"""
Document Scanner Implementation.

This module provides the DocumentScanner class for discovering and registering
documents from the filesystem. It implements:
- Recursive directory scanning
- 5S methodology classification (Sort: permanent, transient, temp)
- Filename validation against naming convention
- Metadata extraction from YAML frontmatter
- Batch registration for performance
- Progress reporting for large scans
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention


@dataclass
class ScanResult:
    """
    Results from document scan operation.

    Provides comprehensive summary of scan operation including discovery,
    registration, validation, and classification statistics.
    """

    total_scanned: int
    new_registered: int
    existing_updated: int
    files_skipped: int
    naming_compliance_rate: float
    classification_counts: Dict[str, int]  # permanent, transient, temp
    warnings: List[str]


class DocumentScanner:
    """
    Scan directories for documents and auto-register with 5S classification.

    This class implements the 5S Sort methodology for document classification:
    - Permanent: Keep forever (PRD, Architecture, ADR, Postmortem, Epic)
    - Transient: Archive after period (QA reports, test reports, analysis)
    - Temp: Can delete (drafts, scratch files, WIP docs)

    Features:
    - Recursive directory scanning
    - Smart exclusion patterns (.git, node_modules, etc.)
    - Filename validation with warnings for non-compliance
    - Batch registration for performance
    - Progress reporting for large scans
    - Metadata extraction from YAML frontmatter

    Example:
        >>> scanner = DocumentScanner(doc_manager)
        >>> result = scanner.scan_directory(Path("docs"))
        >>> print(f"Scanned: {result.total_scanned}, Registered: {result.new_registered}")
    """

    # Default exclude patterns
    DEFAULT_EXCLUDES = [
        '.git', '.archive', '.scratch', 'node_modules', '__pycache__',
        '*.pyc', '*.log', '*.tmp', '.env', 'credentials.json'
    ]

    # 5S Classification rules - Permanent types (keep forever)
    PERMANENT_TYPES = ['prd', 'architecture', 'adr', 'postmortem', 'epic']

    # 5S Classification rules - Transient types (archive after period)
    TRANSIENT_TYPES = ['qa_report', 'test_report', 'analysis', 'benchmark']

    # 5S Classification rules - Temp patterns (can delete)
    # Note: Use word boundaries and specific patterns to avoid matching system paths
    # These patterns are applied to filenames only, not full paths
    TEMP_PATTERNS = [
        r'^draft[-_.]', r'[-_]draft[-_.]', r'\bdraft\b',  # draft at start or with separators
        r'^wip[-_.]', r'[-_]wip[-_.]', r'\bwip\b',  # wip
        r'^scratch[-_.]', r'[-_]scratch[-_.]', r'\bscratch\b',  # scratch
        r'^temp[-_.]', r'[-_]temp[-_.]',  # temp at start or with separators
    ]

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        exclude_patterns: Optional[List[str]] = None,
        exclude_hidden: bool = True,
    ):
        """
        Initialize document scanner.

        Args:
            document_manager: Document lifecycle manager for registration
            exclude_patterns: Optional custom exclude patterns (extends defaults)
            exclude_hidden: Whether to exclude hidden files (default: True)
        """
        self.doc_mgr = document_manager
        self.naming_convention = DocumentNamingConvention()
        self.exclude_hidden = exclude_hidden

        # Combine default and custom exclude patterns
        self.exclude_patterns = list(self.DEFAULT_EXCLUDES)
        if exclude_patterns:
            self.exclude_patterns.extend(exclude_patterns)

    def scan_directory(
        self,
        path: Path,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ScanResult:
        """
        Scan directory for documents and register them.

        This method:
        1. Recursively discovers all .md files
        2. Applies exclusion patterns
        3. Validates filenames against naming convention
        4. Extracts metadata from YAML frontmatter
        5. Classifies documents using 5S Sort methodology
        6. Registers new documents or updates existing ones
        7. Reports progress for large scans

        Args:
            path: Directory to scan (absolute or relative)
            progress_callback: Optional callback for progress updates
                              Called with status message for each file

        Returns:
            ScanResult with comprehensive statistics

        Example:
            >>> def progress(msg):
            ...     print(f"Progress: {msg}")
            >>> result = scanner.scan_directory(Path("docs"), progress)
            >>> print(f"Compliance: {result.naming_compliance_rate:.1f}%")
        """
        path = Path(path).resolve()

        # Initialize counters
        total_scanned = 0
        new_registered = 0
        existing_updated = 0
        files_skipped = 0
        warnings = []
        naming_violations = 0
        classification_counts = {'permanent': 0, 'transient': 0, 'temp': 0}

        # Collect documents to register in batch
        documents_to_register = []

        # Find all markdown files recursively
        for file_path in path.rglob('*.md'):
            # Skip excluded paths
            if self._should_exclude(file_path):
                files_skipped += 1
                continue

            total_scanned += 1

            # Progress reporting
            if progress_callback:
                progress_callback(f"Scanning {file_path.name}")

            try:
                # Check if already registered
                existing_doc = self.doc_mgr.registry.get_document_by_path(str(file_path))

                # Extract metadata from file
                metadata = self.doc_mgr._extract_metadata(file_path)

                # Validate naming convention
                is_valid, error = self.naming_convention.validate_filename(file_path.name)
                if not is_valid:
                    naming_violations += 1
                    # Suggest correct filename
                    doc_type = self._detect_doc_type(file_path, metadata)
                    subject = metadata.get('subject', file_path.stem)
                    suggested = self.naming_convention.suggest_filename(
                        file_path.name, doc_type, subject
                    )
                    warnings.append(
                        f"Non-standard filename: {file_path.name} "
                        f"(suggest: {suggested})"
                    )

                # Classify with 5S Sort methodology
                classification = self._classify_document(file_path, metadata)
                metadata['5s_classification'] = classification
                classification_counts[classification] += 1

                # Detect document type
                doc_type = self._detect_doc_type(file_path, metadata)

                # Get author from metadata or default
                author = metadata.get('author', 'unknown')

                if existing_doc:
                    # Update existing document metadata and governance fields
                    update_kwargs = {'metadata': metadata}

                    # Extract governance fields if present
                    if 'owner' in metadata:
                        update_kwargs['owner'] = metadata['owner']
                    if 'reviewer' in metadata:
                        update_kwargs['reviewer'] = metadata['reviewer']
                    if 'feature' in metadata:
                        update_kwargs['feature'] = metadata['feature']
                    if 'epic' in metadata:
                        update_kwargs['epic'] = metadata['epic']
                    if 'story' in metadata:
                        update_kwargs['story'] = metadata['story']

                    self.doc_mgr.registry.update_document(
                        existing_doc.id,
                        **update_kwargs,
                    )
                    existing_updated += 1
                else:
                    # Collect for batch registration
                    documents_to_register.append({
                        'path': file_path,
                        'doc_type': doc_type,
                        'author': author,
                        'metadata': metadata,
                    })

            except Exception as e:
                warnings.append(f"Error scanning {file_path.name}: {str(e)}")

        # Batch register new documents
        for doc_data in documents_to_register:
            try:
                self.doc_mgr.register_document(**doc_data)
                new_registered += 1
            except Exception as e:
                warnings.append(f"Error registering {doc_data['path'].name}: {str(e)}")

        # Calculate naming compliance rate
        naming_compliance_rate = (
            ((total_scanned - naming_violations) / total_scanned * 100)
            if total_scanned > 0 else 100.0
        )

        return ScanResult(
            total_scanned=total_scanned,
            new_registered=new_registered,
            existing_updated=existing_updated,
            files_skipped=files_skipped,
            naming_compliance_rate=naming_compliance_rate,
            classification_counts=classification_counts,
            warnings=warnings,
        )

    def _should_exclude(self, path: Path) -> bool:
        """
        Check if path should be excluded from scanning.

        Args:
            path: Path to check

        Returns:
            True if should be excluded, False otherwise
        """
        # Exclude hidden files if configured
        if self.exclude_hidden:
            for part in path.parts:
                if part.startswith('.') and part not in ['.', '..']:
                    return True

        str(path)

        for pattern in self.exclude_patterns:
            # Handle glob patterns (e.g., *.pyc)
            if '*' in pattern:
                if path.match(pattern):
                    return True
            # Handle directory names
            else:
                if pattern in path.parts:
                    return True

        return False

    def _classify_document(
        self,
        path: Path,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Classify document using 5S Sort methodology.

        Classification Rules:
        1. Temp (can delete):
           - "draft", "wip", "scratch", "temp" in path (as directory names or in filename)
           - .scratch directory
           - "draft" in frontmatter

        2. Permanent (keep forever):
           - doc_type: prd, architecture, adr, postmortem, epic
           - Default for unknown types (conservative)

        3. Transient (archive after period):
           - doc_type: qa_report, test_report, analysis, benchmark

        Args:
            path: Document file path
            metadata: Extracted metadata

        Returns:
            Classification: 'permanent', 'transient', or 'temp'
        """
        # Check for .scratch directory first
        if '.scratch' in path.parts:
            return 'temp'

        # Check frontmatter for draft status
        if metadata.get('status', '').lower() == 'draft':
            return 'temp'

        if 'draft' in metadata.get('tags', []):
            return 'temp'

        # Check path parts (directory names) for temp indicators
        # Skip system directories - only check the last 5 parts (project-relative)
        # This avoids matching system paths like /tmp/, /var/temp/, AppData\Local\Temp\
        relevant_parts = path.parts[-5:]  # Last 5 parts should cover most project structures
        path_parts_lower = [p.lower() for p in relevant_parts]
        temp_dir_names = ['draft', 'drafts', 'wip', 'scratch']  # Removed 'temp' to avoid system paths

        for part in path_parts_lower:
            if part in temp_dir_names:
                return 'temp'

        # Check filename for temp indicators (e.g., draft-notes.md, wip-doc.md)
        filename_lower = path.name.lower()
        for pattern in self.TEMP_PATTERNS:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return 'temp'

        # Check document type from frontmatter
        doc_type = metadata.get('doc_type', '').lower()

        # Permanent types
        if doc_type in [t.lower() for t in self.PERMANENT_TYPES]:
            return 'permanent'

        # Transient types
        if doc_type in [t.lower() for t in self.TRANSIENT_TYPES]:
            return 'transient'

        # Default to permanent (conservative approach)
        return 'permanent'

    def _detect_doc_type(
        self,
        path: Path,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Detect document type from path and metadata.

        Priority:
        1. doc_type from YAML frontmatter
        2. Infer from path patterns
        3. Default to 'story' (most generic document type)

        Args:
            path: Document file path
            metadata: Extracted metadata

        Returns:
            Document type string (always a valid DocumentType)
        """
        # Check frontmatter first (highest priority)
        if 'doc_type' in metadata:
            doc_type = metadata['doc_type'].lower()
            # Validate it's a known type
            valid_types = ['prd', 'architecture', 'epic', 'story', 'adr',
                          'postmortem', 'runbook', 'qa_report', 'test_report']
            if doc_type in valid_types:
                return doc_type

        # Infer from path
        path_lower = str(path).lower()

        # Check filename and path for common patterns
        if 'prd' in path_lower:
            return 'prd'
        elif 'architecture' in path_lower or 'arch' in path_lower:
            return 'architecture'
        elif 'epic' in path_lower:
            return 'epic'
        elif 'adr' in path_lower:
            return 'adr'
        elif 'postmortem' in path_lower:
            return 'postmortem'
        elif 'runbook' in path_lower:
            return 'runbook'
        elif 'qa' in path_lower:
            return 'qa_report'
        elif 'test' in path_lower:
            return 'test_report'
        elif 'story' in path_lower:
            return 'story'

        # Default to 'story' (most generic document type that makes sense)
        return 'story'
