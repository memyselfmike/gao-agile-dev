"""
Document Lifecycle Manager Implementation.

This module provides the high-level DocumentLifecycleManager class that orchestrates
all document lifecycle operations. It coordinates the DocumentRegistry and
DocumentStateMachine, handles filesystem operations, and provides a unified API
for document management.
"""

import hashlib
import re
import shutil
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.state_machine import DocumentStateMachine
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType, RelationshipType


class DocumentLifecycleManager:
    """
    High-level document lifecycle manager.

    This class provides a unified API for all document lifecycle operations,
    orchestrating the DocumentRegistry and DocumentStateMachine. It handles:
    - Document registration with metadata extraction
    - State transitions with validation
    - Filesystem operations (archiving)
    - Document relationships
    - Query operations

    The manager extracts metadata from YAML frontmatter, detects feature/epic
    from file paths, and manages document relationships automatically.

    Example:
        >>> manager = DocumentLifecycleManager(registry, archive_dir)
        >>> doc = manager.register_document(
        ...     path=Path("docs/PRD.md"),
        ...     doc_type="prd",
        ...     author="john",
        ...     metadata={"version": "1.0"}
        ... )
        >>> manager.transition_state(doc.id, DocumentState.ACTIVE, "Approved")
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        archive_dir: Path,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize lifecycle manager.

        Args:
            registry: Document registry for data access
            archive_dir: Directory for archived documents
            project_root: Optional project root for logging context
        """
        self.registry = registry
        self.archive_dir = Path(archive_dir)
        self.project_root = project_root
        self.state_machine = DocumentStateMachine(registry)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def register_document(
        self,
        path: Path,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Register document with metadata extraction.

        This method:
        1. Extracts metadata from file (YAML frontmatter)
        2. Extracts feature/epic from file path
        3. Calculates content hash
        4. Merges provided metadata with extracted metadata
        5. Registers in database
        6. Creates relationships from frontmatter

        Args:
            path: Path to document file
            doc_type: Document type (prd, architecture, epic, story, etc.)
            author: Document author
            metadata: Optional metadata (merged with extracted, takes precedence)

        Returns:
            Registered Document object

        Raises:
            ValidationError: If document type or metadata is invalid
            DocumentAlreadyExistsError: If document already registered

        Example:
            >>> doc = manager.register_document(
            ...     path=Path("docs/features/auth/PRD.md"),
            ...     doc_type="prd",
            ...     author="john",
            ...     metadata={"version": "1.0"}
            ... )
        """
        # Extract metadata from file
        extracted_metadata = self._extract_metadata(path)

        # Extract feature/epic from path
        path_metadata = self._extract_path_metadata(path)

        # Merge all metadata (priority: provided > extracted > path)
        merged_metadata = {
            **path_metadata,
            **extracted_metadata,
            **(metadata or {}),
        }

        # Calculate content hash
        content_hash = self._calculate_content_hash(path)
        if content_hash:
            merged_metadata["content_hash"] = content_hash

        # Extract governance fields
        owner = merged_metadata.get("owner")
        reviewer = merged_metadata.get("reviewer")
        feature = merged_metadata.get("feature")
        epic = merged_metadata.get("epic")
        story = merged_metadata.get("story")

        # Register in database
        document = self.registry.register_document(
            path=str(path),
            doc_type=doc_type,
            author=author,
            metadata=merged_metadata,
            owner=owner,
            reviewer=reviewer,
            feature=feature,
            epic=epic,
            story=story,
        )

        # Create relationships from frontmatter
        if "related_docs" in merged_metadata:
            self._create_relationships(document, merged_metadata["related_docs"])

        return document

    def transition_state(
        self,
        doc_id: int,
        new_state: DocumentState,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> Document:
        """
        Transition document to new state.

        Delegates to DocumentStateMachine for validation and business rules.

        Args:
            doc_id: Document ID
            new_state: Target state
            reason: Reason for transition (required for OBSOLETE/ARCHIVED)
            changed_by: Who initiated the change (defaults to "system")

        Returns:
            Updated Document object

        Raises:
            InvalidStateTransition: If transition not allowed
            ValueError: If reason required but not provided
            DocumentNotFoundError: If document not found

        Example:
            >>> doc = manager.transition_state(
            ...     doc_id=1,
            ...     new_state=DocumentState.ACTIVE,
            ...     reason="Approved by team",
            ...     changed_by="john"
            ... )
        """
        document = self.registry.get_document(doc_id)
        return self.state_machine.transition(document, new_state, reason, changed_by)

    def get_current_document(
        self,
        doc_type: str,
        feature: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Get current active document of specified type.

        Returns the first active document matching the type and optional feature.

        Args:
            doc_type: Document type
            feature: Optional feature filter

        Returns:
            Active document or None if not found

        Example:
            >>> doc = manager.get_current_document("prd", feature="authentication")
        """
        docs = self.registry.query_documents(
            doc_type=doc_type,
            state=DocumentState.ACTIVE,
            feature=feature,
        )
        return docs[0] if docs else None

    def get_document_lineage(
        self,
        doc_id: int,
    ) -> Tuple[List[Document], List[Document]]:
        """
        Get document lineage (ancestors and descendants).

        Recursively traverses relationships to build complete lineage tree.

        Args:
            doc_id: Document ID

        Returns:
            Tuple of (ancestors, descendants)
            - ancestors: List of parent documents (ordered from immediate parent to root)
            - descendants: List of child documents (depth-first traversal)

        Example:
            >>> ancestors, descendants = manager.get_document_lineage(doc_id=5)
            >>> print(f"Parents: {[d.path for d in ancestors]}")
            >>> print(f"Children: {[d.path for d in descendants]}")
        """
        ancestors = []
        descendants = []

        # Get ancestors (recursive)
        current_id = doc_id
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            parents = self.registry.get_parent_documents(current_id)
            if parents:
                ancestors.extend(parents)
                current_id = parents[0].id
            else:
                break

        # Get descendants (recursive depth-first)
        def get_descendants_recursive(doc_id: int, visited: set) -> List[Document]:
            if doc_id in visited:
                return []
            visited.add(doc_id)

            children = self.registry.get_child_documents(doc_id)
            all_descendants = list(children)

            for child in children:
                all_descendants.extend(get_descendants_recursive(child.id, visited))

            return all_descendants

        descendants = get_descendants_recursive(doc_id, set())

        return (ancestors, descendants)

    def archive_document(self, doc_id: int) -> Path:
        """
        Archive document to archive directory.

        This method:
        1. Validates document can be archived
        2. Moves file to .archive/ directory (preserving structure)
        3. Transitions document to ARCHIVED state
        4. Updates path in database

        Args:
            doc_id: Document ID

        Returns:
            Path to archived file

        Raises:
            ValueError: If document already archived
            DocumentNotFoundError: If document not found

        Example:
            >>> archive_path = manager.archive_document(doc_id=3)
            >>> print(f"Archived to: {archive_path}")
        """
        document = self.registry.get_document(doc_id)

        # Validate state allows archival
        if document.state == DocumentState.ARCHIVED:
            raise ValueError("Document already archived")

        # Move file to archive
        source_path = Path(document.path)

        # Determine archive path
        # Try to preserve directory structure relative to a known base
        if source_path.is_absolute():
            # For absolute paths, just use the name to avoid complex path handling
            archive_path = self.archive_dir / source_path.name
        else:
            # For relative paths, preserve structure
            archive_path = self.archive_dir / source_path

        # Create directory structure
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file if it exists, then delete source
        if source_path.exists():
            try:
                # Use shutil.move which handles cross-filesystem moves better
                shutil.move(str(source_path), str(archive_path))
            except (PermissionError, OSError):
                # If move fails, try copy+delete with retry
                shutil.copy2(str(source_path), str(archive_path))
                # Small delay to release file handles
                import time
                time.sleep(0.1)
                try:
                    source_path.unlink()
                except (PermissionError, OSError):
                    # If we can't delete, at least we have the copy
                    pass

        # Update state to ARCHIVED
        self.state_machine.transition(
            document,
            DocumentState.ARCHIVED,
            reason="Archived by system",
        )

        # Update path in database if different
        if str(archive_path) != document.path:
            self.registry.update_document(doc_id, path=str(archive_path))

        return archive_path

    def query_documents(self, **filters) -> List[Document]:
        """
        Query documents with filters.

        Delegates to DocumentRegistry.query_documents().

        Args:
            **filters: Query filters (doc_type, state, feature, epic, owner, tags)

        Returns:
            List of matching documents

        Example:
            >>> docs = manager.query_documents(
            ...     doc_type="story",
            ...     state=DocumentState.ACTIVE,
            ...     feature="authentication"
            ... )
        """
        return self.registry.query_documents(**filters)

    # Private helper methods

    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """
        Extract metadata from document file.

        Parses YAML frontmatter from markdown files.

        Args:
            path: Path to document file

        Returns:
            Dictionary of extracted metadata

        Example frontmatter:
            ---
            owner: john
            reviewer: winston
            feature: authentication
            epic: 5
            related_docs:
              - docs/Architecture.md
            ---
        """
        if not path.exists():
            return {}

        try:
            content = path.read_text(encoding="utf-8")

            # Extract YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    return frontmatter or {}

        except Exception:
            # Silently fail - return empty dict
            pass

        return {}

    def _extract_path_metadata(self, path: Path) -> Dict[str, Any]:
        """
        Extract metadata from file path patterns.

        Detects:
        - Feature name: docs/features/<feature-name>/...
        - Epic number: epic-<N> or epic_<N>
        - Story identifier: story-<N>.<M> or story_<N>_<M>

        Args:
            path: File path

        Returns:
            Dictionary with extracted metadata

        Example:
            >>> path = Path("docs/features/auth-system/stories/epic-5/story-5.2.md")
            >>> metadata = _extract_path_metadata(path)
            >>> # Returns: {"feature": "auth-system", "epic": 5, "story": "5.2"}
        """
        metadata = {}
        path_str = str(path)

        # Extract feature: docs/features/<feature-name>/
        feature_match = re.search(r"features[/\\]([^/\\]+)", path_str)
        if feature_match:
            metadata["feature"] = feature_match.group(1)

        # Extract epic: epic-5 or epic_5
        epic_match = re.search(r"epic[-_](\d+)", path_str, re.IGNORECASE)
        if epic_match:
            metadata["epic"] = int(epic_match.group(1))

        # Extract story: story-5.2 or story_5_2
        story_match = re.search(r"story[-_](\d+[._]\d+)", path_str, re.IGNORECASE)
        if story_match:
            story_id = story_match.group(1).replace("_", ".")
            metadata["story"] = story_id

        return metadata

    def _calculate_content_hash(self, path: Path) -> Optional[str]:
        """
        Calculate SHA256 hash of file content.

        Args:
            path: File path

        Returns:
            SHA256 hash string, or None if file doesn't exist
        """
        if not path.exists():
            return None

        try:
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def _create_relationships(
        self,
        document: Document,
        related_docs: List[str],
    ) -> None:
        """
        Create relationships from related_docs list.

        Infers relationship types based on document types:
        - PRD -> Architecture: DERIVED_FROM
        - Architecture -> Story: DERIVED_FROM
        - Story -> Code: IMPLEMENTS
        - Test -> Story: TESTS

        Args:
            document: Child document
            related_docs: List of related document paths
        """
        for related_path in related_docs:
            related_doc = self.registry.get_document_by_path(related_path)
            if related_doc:
                # Infer relationship type
                rel_type = self._infer_relationship_type(
                    parent_type=related_doc.type,
                    child_type=document.type,
                )

                try:
                    self.registry.add_relationship(
                        parent_id=related_doc.id,
                        child_id=document.id,
                        rel_type=rel_type,
                    )
                except Exception:
                    # Silently skip if relationship already exists or other errors
                    pass

    def _infer_relationship_type(
        self,
        parent_type: DocumentType,
        child_type: DocumentType,
    ) -> RelationshipType:
        """
        Infer relationship type based on document types.

        Args:
            parent_type: Parent document type
            child_type: Child document type

        Returns:
            Inferred relationship type

        Inference rules:
        - PRD -> Architecture: DERIVED_FROM
        - Architecture -> Story: DERIVED_FROM
        - Architecture -> Epic: DERIVED_FROM
        - Epic -> Story: IMPLEMENTS
        - Story -> Code: IMPLEMENTS
        - Test Report -> Story: TESTS
        - Default: REFERENCES
        """
        # Map of (parent_type, child_type) -> relationship_type
        inference_map = {
            (DocumentType.PRD, DocumentType.ARCHITECTURE): RelationshipType.DERIVED_FROM,
            (DocumentType.ARCHITECTURE, DocumentType.EPIC): RelationshipType.DERIVED_FROM,
            (DocumentType.ARCHITECTURE, DocumentType.STORY): RelationshipType.DERIVED_FROM,
            (DocumentType.EPIC, DocumentType.STORY): RelationshipType.IMPLEMENTS,
            (DocumentType.STORY, DocumentType.RUNBOOK): RelationshipType.IMPLEMENTS,
            (DocumentType.TEST_REPORT, DocumentType.STORY): RelationshipType.TESTS,
            (DocumentType.QA_REPORT, DocumentType.STORY): RelationshipType.TESTS,
        }

        return inference_map.get(
            (parent_type, child_type),
            RelationshipType.REFERENCES,
        )
