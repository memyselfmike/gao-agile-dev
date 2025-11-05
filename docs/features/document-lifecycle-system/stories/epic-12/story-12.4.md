# Story 12.4: DocumentLifecycleManager

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** 1

---

## Story Description

Implement the high-level DocumentLifecycleManager that orchestrates all document lifecycle operations. This is the primary API that coordinates DocumentRegistry and StateMachine, handles filesystem operations, and provides a unified interface for all document operations.

---

## Business Value

The DocumentLifecycleManager provides:
- **Unified API**: Single entry point for all document operations
- **Orchestration**: Coordinates registry + state machine + filesystem
- **Convenience**: High-level methods for common tasks
- **Integration Point**: What other components use (not Registry directly)
- **Encapsulation**: Hides implementation details from consumers

---

## Acceptance Criteria

### Core Operations
- [ ] `register_document(path, doc_type, author, metadata)` registers document with metadata extraction
- [ ] `transition_state(doc_id, new_state, reason)` transitions document state with validation
- [ ] `get_current_document(doc_type, feature)` returns active document
- [ ] `get_document_lineage(doc_id)` returns ancestors + descendants
- [ ] `archive_document(doc_id)` moves file to archive directory and updates state
- [ ] `query_documents(**filters)` provides filtered document search
- [ ] All operations use DocumentRegistry and StateMachine internally

### Metadata Extraction
- [ ] Extracts YAML frontmatter from markdown files
- [ ] Extracts feature/epic from file path patterns
- [ ] Calculates content hash for sync detection
- [ ] Validates metadata against schema
- [ ] Populates governance fields from frontmatter

### Filesystem Operations
- [ ] Archive operation moves file to `.archive/` directory
- [ ] Preserves directory structure in archive (e.g., `docs/PRD.md` → `.archive/docs/PRD.md`)
- [ ] Creates archive directories as needed
- [ ] Handles file not found gracefully
- [ ] Atomic file operations (copy then delete)

### Document Relationships
- [ ] Detects relationships from frontmatter (`related_docs` field)
- [ ] Creates relationships automatically on registration
- [ ] Relationship types inferred from document types:
  - PRD → Architecture: "derived_from"
  - Architecture → Story: "derived_from"
  - Story → Code: "implements"
  - Test → Story: "tests"

### Performance
- [ ] Operations complete in <100ms
- [ ] Uses cached connections from Registry
- [ ] Batch operations supported for multiple documents

### Integration Tests
- [ ] Register document with metadata extraction
- [ ] Transition document through lifecycle
- [ ] Archive document and verify file moved
- [ ] Query documents with filters
- [ ] Get document lineage

**Test Coverage:** >80%

---

## Technical Notes

### Implementation

```python
# gao_dev/lifecycle/document_manager.py
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import shutil
import hashlib
import yaml

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.state_machine import DocumentStateMachine
from gao_dev.lifecycle.models import Document, DocumentState

class DocumentLifecycleManager:
    """
    High-level document lifecycle manager.

    Orchestrates DocumentRegistry and StateMachine.
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        archive_dir: Path
    ):
        """
        Initialize lifecycle manager.

        Args:
            registry: Document registry
            archive_dir: Directory for archived documents
        """
        self.registry = registry
        self.archive_dir = archive_dir
        self.state_machine = DocumentStateMachine(registry)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def register_document(
        self,
        path: Path,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Register document with metadata extraction.

        Args:
            path: Path to document file
            doc_type: Document type
            author: Author name
            metadata: Optional metadata (merged with extracted)

        Returns:
            Registered document
        """
        # Extract metadata from file
        extracted_metadata = self._extract_metadata(path)

        # Merge with provided metadata (provided takes precedence)
        merged_metadata = {**extracted_metadata, **(metadata or {})}

        # Extract governance fields
        owner = merged_metadata.get('owner')
        reviewer = merged_metadata.get('reviewer')

        # Register in database
        document = self.registry.register_document(
            path=str(path),
            doc_type=doc_type,
            author=author,
            metadata=merged_metadata,
            owner=owner,
            reviewer=reviewer
        )

        # Create relationships from frontmatter
        if 'related_docs' in merged_metadata:
            self._create_relationships(document, merged_metadata['related_docs'])

        return document

    def transition_state(
        self,
        doc_id: int,
        new_state: DocumentState,
        reason: Optional[str] = None
    ) -> Document:
        """
        Transition document to new state.

        Args:
            doc_id: Document ID
            new_state: Target state
            reason: Reason for transition

        Returns:
            Updated document
        """
        document = self.registry.get_document(doc_id)
        return self.state_machine.transition(document, new_state, reason)

    def get_current_document(
        self,
        doc_type: str,
        feature: Optional[str] = None
    ) -> Optional[Document]:
        """
        Get current active document of specified type.

        Args:
            doc_type: Document type
            feature: Optional feature filter

        Returns:
            Active document or None
        """
        docs = self.registry.query_documents(
            doc_type=doc_type,
            state=DocumentState.ACTIVE,
            feature=feature
        )
        return docs[0] if docs else None

    def get_document_lineage(
        self,
        doc_id: int
    ) -> Tuple[List[Document], List[Document]]:
        """
        Get document lineage (ancestors and descendants).

        Args:
            doc_id: Document ID

        Returns:
            Tuple of (ancestors, descendants)
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

        # Get descendants (recursive)
        def get_descendants_recursive(doc_id, visited):
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

        Args:
            doc_id: Document ID

        Returns:
            Path to archived file

        Raises:
            ValueError: If document not in archivable state
        """
        document = self.registry.get_document(doc_id)

        # Validate state allows archival
        if document.state == DocumentState.ARCHIVED:
            raise ValueError("Document already archived")

        # Move file to archive
        source_path = Path(document.path)
        archive_path = self.archive_dir / source_path

        # Create directory structure
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file (atomic operation)
        if source_path.exists():
            shutil.copy2(source_path, archive_path)
            source_path.unlink()

        # Update state to ARCHIVED
        self.state_machine.transition(
            document,
            DocumentState.ARCHIVED,
            reason="Archived by system"
        )

        # Update path in database
        self.registry.update_document(doc_id, path=str(archive_path))

        return archive_path

    def _extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract metadata from document file."""
        if not path.exists():
            return {}

        try:
            content = path.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    return frontmatter or {}

        except Exception:
            pass

        return {}

    def _create_relationships(
        self,
        document: Document,
        related_docs: List[str]
    ) -> None:
        """Create relationships from related_docs list."""
        for related_path in related_docs:
            related_doc = self.registry.get_document_by_path(related_path)
            if related_doc:
                self.registry.add_relationship(
                    parent_id=related_doc.id,
                    child_id=document.id,
                    rel_type="derived_from"
                )
```

**Files to Create:**
- `gao_dev/lifecycle/document_manager.py`
- `tests/lifecycle/test_document_manager.py`
- `tests/lifecycle/test_metadata_extraction.py`

**Dependencies:**
- Story 12.2 (DocumentRegistry)
- Story 12.3 (DocumentStateMachine)

---

## Testing Requirements

### Unit Tests
- [ ] Test register_document() with frontmatter
- [ ] Test transition_state() delegates to state machine
- [ ] Test get_current_document() returns active doc
- [ ] Test archive_document() moves file correctly
- [ ] Test get_document_lineage() returns ancestors/descendants
- [ ] Test metadata extraction from YAML frontmatter

### Integration Tests
- [ ] End-to-end: register → transition → archive
- [ ] Document lineage with multiple levels
- [ ] Relationship creation from frontmatter

### Performance Tests
- [ ] Operations complete in <100ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation for all public methods
- [ ] Usage examples for common operations
- [ ] Integration guide for other components

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance targets met
- [ ] Committed with atomic commit message
