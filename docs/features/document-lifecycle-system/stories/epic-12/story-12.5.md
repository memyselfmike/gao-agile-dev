# Story 12.5 (ENHANCED): Document Scanning + 5S Classification

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 5
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** 2

---

## Story Description

Implement document scanning system that automatically discovers and registers existing documents with 5S methodology classification (Sort: permanent, transient, temp). Validates filenames against naming convention and extracts governance metadata from YAML frontmatter.

---

## Business Value

The scanning system provides:
- **Automatic Discovery**: No manual registration needed for existing docs
- **5S Methodology**: Classifies documents for sustained quality (Sort principle)
- **Compliance Checking**: Validates naming convention adherence
- **Governance Extraction**: Auto-populates owner, reviewer, review dates
- **Bulk Registration**: Handles 1000+ documents efficiently

---

## Acceptance Criteria

### Scanning Operations
- [ ] `scan_directory(path)` discovers documents recursively
- [ ] Detects document type from path patterns and frontmatter
- [ ] Extracts metadata from YAML frontmatter (including governance fields)
- [ ] Validates filenames against naming convention
- [ ] Warns on non-standard filenames but still registers
- [ ] Registers unregistered documents automatically
- [ ] Updates metadata for already registered documents
- [ ] Progress reporting for large scans (callback or progress bar)

### 5S Classification (Sort)
- [ ] Classifies documents as:
  - **Permanent**: PRD, Architecture, ADR, Postmortem (keep forever)
  - **Transient**: QA reports, test reports, temp analysis (archive after period)
  - **Temp**: Draft files, .scratch files, WIP docs (can delete)
- [ ] Classification logic:
  - If "draft" in path or frontmatter → temp
  - If path.parent == ".scratch" → temp
  - If doc_type in ["prd", "architecture", "adr", "postmortem"] → permanent
  - If doc_type in ["qa_report", "test_report", "analysis"] → transient
  - Default → permanent (conservative)
- [ ] Classification stored in metadata field

### Exclusion Patterns
- [ ] Respects exclude patterns from configuration:
  - `.git`, `.archive`, `.scratch`, `node_modules`, `__pycache__`
  - `*.pyc`, `*.log`, `.env`, `credentials.json`
- [ ] Configurable exclude patterns
- [ ] Hidden files excluded by default (optional override)

### Naming Convention Validation
- [ ] Validates each filename against standard
- [ ] Logs warnings for non-compliant filenames
- [ ] Suggests correct filename for non-compliant files
- [ ] Tracks naming compliance rate in scan results

### Performance
- [ ] Scan 1000 documents in <10 seconds
- [ ] Batch insert for new documents (not one-by-one)
- [ ] Parallel scanning for large directories (optional)

### Scan Results
- [ ] Returns scan summary:
  - Total files scanned
  - New documents registered
  - Existing documents updated
  - Files skipped (excluded)
  - Naming compliance rate
  - 5S classification breakdown
- [ ] Detailed log of all operations

**Test Coverage:** >80%

---

## Technical Notes

### Implementation

```python
# gao_dev/lifecycle/scanner.py
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import re
from dataclasses import dataclass

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention

@dataclass
class ScanResult:
    """Results from document scan."""
    total_scanned: int
    new_registered: int
    existing_updated: int
    files_skipped: int
    naming_compliance_rate: float
    classification_counts: Dict[str, int]  # permanent, transient, temp
    warnings: List[str]

class DocumentScanner:
    """
    Scan directories for documents and auto-register.

    Applies 5S Sort classification.
    """

    # Default exclude patterns
    DEFAULT_EXCLUDES = [
        '.git', '.archive', '.scratch', 'node_modules', '__pycache__',
        '*.pyc', '*.log', '*.tmp', '.env', 'credentials.json'
    ]

    # 5S Classification rules
    PERMANENT_TYPES = ['prd', 'architecture', 'adr', 'postmortem', 'epic']
    TRANSIENT_TYPES = ['qa_report', 'test_report', 'analysis', 'benchmark']
    TEMP_PATTERNS = [r'.*draft.*', r'.*wip.*', r'.*scratch.*', r'.*temp.*']

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize scanner.

        Args:
            document_manager: Document lifecycle manager
            exclude_patterns: Optional custom exclude patterns
        """
        self.doc_mgr = document_manager
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDES
        self.naming_convention = DocumentNamingConvention()

    def scan_directory(
        self,
        path: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ScanResult:
        """
        Scan directory for documents and register.

        Args:
            path: Directory to scan
            progress_callback: Optional callback for progress updates

        Returns:
            Scan results summary
        """
        total_scanned = 0
        new_registered = 0
        existing_updated = 0
        files_skipped = 0
        warnings = []
        classification_counts = {'permanent': 0, 'transient': 0, 'temp': 0}

        # Find all markdown files
        for file_path in path.rglob('*.md'):
            # Skip excluded paths
            if self._should_exclude(file_path):
                files_skipped += 1
                continue

            total_scanned += 1

            if progress_callback:
                progress_callback(f"Scanning {file_path}")

            try:
                # Check if already registered
                existing_doc = self.doc_mgr.registry.get_document_by_path(str(file_path))

                # Extract metadata
                metadata = self.doc_mgr._extract_metadata(file_path)

                # Validate naming convention
                is_valid, error = self.naming_convention.validate_filename(file_path.name)
                if not is_valid:
                    warnings.append(f"Non-standard filename: {file_path} - {error}")

                # Classify with 5S Sort
                classification = self._classify_document(file_path, metadata)
                metadata['5s_classification'] = classification
                classification_counts[classification] += 1

                # Detect document type
                doc_type = self._detect_doc_type(file_path, metadata)

                if existing_doc:
                    # Update metadata
                    self.doc_mgr.registry.update_document(
                        existing_doc.id,
                        metadata=metadata
                    )
                    existing_updated += 1
                else:
                    # Register new document
                    author = metadata.get('author', 'unknown')
                    self.doc_mgr.register_document(
                        path=file_path,
                        doc_type=doc_type,
                        author=author,
                        metadata=metadata
                    )
                    new_registered += 1

            except Exception as e:
                warnings.append(f"Error scanning {file_path}: {e}")

        # Calculate naming compliance rate
        naming_compliance_rate = (
            (total_scanned - len(warnings)) / total_scanned * 100
            if total_scanned > 0 else 100.0
        )

        return ScanResult(
            total_scanned=total_scanned,
            new_registered=new_registered,
            existing_updated=existing_updated,
            files_skipped=files_skipped,
            naming_compliance_rate=naming_compliance_rate,
            classification_counts=classification_counts,
            warnings=warnings
        )

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)

        for pattern in self.exclude_patterns:
            # Handle glob patterns
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
        metadata: Dict[str, Any]
    ) -> str:
        """
        Classify document using 5S Sort methodology.

        Returns: 'permanent', 'transient', or 'temp'
        """
        path_str = str(path).lower()

        # Check temp patterns first
        for pattern in self.TEMP_PATTERNS:
            if re.search(pattern, path_str):
                return 'temp'

        # Check for .scratch directory
        if '.scratch' in path.parts:
            return 'temp'

        # Check document type from frontmatter
        doc_type = metadata.get('doc_type', '').lower()

        if doc_type in [t.lower() for t in self.PERMANENT_TYPES]:
            return 'permanent'

        if doc_type in [t.lower() for t in self.TRANSIENT_TYPES]:
            return 'transient'

        # Default to permanent (conservative)
        return 'permanent'

    def _detect_doc_type(
        self,
        path: Path,
        metadata: Dict[str, Any]
    ) -> str:
        """Detect document type from path and metadata."""
        # Check frontmatter first
        if 'doc_type' in metadata:
            return metadata['doc_type'].lower()

        # Infer from path
        path_lower = str(path).lower()

        if 'prd' in path_lower:
            return 'prd'
        elif 'architecture' in path_lower or 'arch' in path_lower:
            return 'architecture'
        elif 'story' in path_lower:
            return 'story'
        elif 'epic' in path_lower:
            return 'epic'
        elif 'qa' in path_lower:
            return 'qa_report'
        elif 'test' in path_lower:
            return 'test_report'

        return 'unknown'
```

**Files to Create:**
- `gao_dev/lifecycle/scanner.py`
- `tests/lifecycle/test_scanner.py`
- `tests/lifecycle/test_5s_classification.py`

**Dependencies:**
- Story 12.4 (DocumentLifecycleManager)
- Story 12.1 (DocumentNamingConvention)

---

## Testing Requirements

### Unit Tests
- [ ] Test scan_directory() discovers all files
- [ ] Test exclude patterns work correctly
- [ ] Test 5S classification for each category
- [ ] Test naming convention validation
- [ ] Test metadata extraction
- [ ] Test doc type detection

### Integration Tests
- [ ] Scan real directory structure
- [ ] Verify all documents registered
- [ ] Verify metadata extracted correctly

### Performance Tests
- [ ] Scan 1000 documents in <10 seconds
- [ ] Batch insert performance

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation
- [ ] 5S classification rules documented
- [ ] Exclude patterns documentation
- [ ] Usage examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance targets met
- [ ] 5S classification verified
- [ ] Committed with atomic commit message
