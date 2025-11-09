# Story 22.2: Extract ArtifactManager

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.2
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Extract artifact detection, registration, and type inference logic from the GAODevOrchestrator into a dedicated ArtifactManager service. This service will handle all artifact-related operations including file snapshots, artifact detection, type inference, and registration with the document lifecycle system.

The ArtifactManager will reduce the orchestrator's responsibility and create a focused service for managing all document artifacts created during workflow execution. This is the largest extraction at ~286 LOC.

---

## Acceptance Criteria

- [ ] Create `ArtifactManager` service (~250 LOC)
- [ ] Move snapshot logic (_snapshot_project_files, ~70 LOC)
- [ ] Move detection logic (_detect_artifacts, ~40 LOC)
- [ ] Move registration logic (_register_artifacts, ~98 LOC)
- [ ] Move type inference logic (_infer_document_type, ~78 LOC)
- [ ] Orchestrator delegates to ArtifactManager
- [ ] All artifact tests pass
- [ ] 15 unit tests for manager
- [ ] Zero breaking changes

---

## Technical Approach

### Implementation Details

The ArtifactManager encapsulates the complete artifact lifecycle: snapshot → detect → infer type → register. It coordinates with DocumentLifecycleManager to register discovered artifacts.

**Key Responsibilities**:
1. Snapshot project files before/after operations
2. Detect newly created or modified artifacts
3. Infer document types from paths and content
4. Register artifacts in document lifecycle
5. Handle metadata extraction

**Design Pattern**: Service pattern with clear separation of concerns

### Files to Modify

- `gao_dev/orchestrator/artifact_manager.py` (+250 LOC / NEW)
  - Add: ArtifactManager class
  - Add: snapshot() method
  - Add: detect() method
  - Add: register() method
  - Add: infer_type() method
  - Add: Helper methods for path analysis

- `gao_dev/orchestrator/orchestrator.py` (-286 LOC / +30 delegation)
  - Remove: _snapshot_project_files() (~70 LOC)
  - Remove: _detect_artifacts() (~40 LOC)
  - Remove: _register_artifacts() (~98 LOC)
  - Remove: _infer_document_type() (~78 LOC)
  - Add: Delegate to artifact_manager
  - Add: artifact_manager initialization

### New Files to Create

- `gao_dev/orchestrator/artifact_manager.py` (~250 LOC)
  - Purpose: Manage artifact detection and registration
  - Key components:
    - ArtifactManager class
    - snapshot(project_path) -> Set[Path]
    - detect(before, after) -> List[Path]
    - infer_type(path, content) -> DocumentType
    - register(artifacts, metadata) -> None
    - Helper: _is_tracked_directory()
    - Helper: _extract_path_metadata()

- `tests/orchestrator/test_artifact_manager.py` (~200 LOC)
  - Purpose: Unit tests for artifact manager
  - Key components:
    - 15 unit tests
    - Mock DocumentLifecycleManager
    - Test snapshot with various directory structures
    - Test detection algorithms
    - Test type inference logic
    - Test registration coordination

---

## Testing Strategy

### Unit Tests (15 tests)

- test_snapshot_empty_project() - Test empty directory snapshot
- test_snapshot_with_files() - Test snapshot with existing files
- test_detect_new_files() - Test detection of newly created files
- test_detect_modified_files() - Test detection of modifications
- test_detect_no_changes() - Test when nothing changes
- test_infer_type_prd() - Test PRD type inference
- test_infer_type_epic() - Test epic type inference
- test_infer_type_story() - Test story type inference
- test_infer_type_architecture() - Test architecture doc inference
- test_infer_type_unknown() - Test fallback to unknown type
- test_register_single_artifact() - Test registering one artifact
- test_register_multiple_artifacts() - Test batch registration
- test_register_with_metadata() - Test metadata extraction
- test_is_tracked_directory() - Test directory filtering
- test_artifact_manager_initialization() - Test constructor

**Total Tests**: 15 tests
**Test File**: `tests/orchestrator/test_artifact_manager.py`

---

## Dependencies

**Upstream**: Story 22.1 (WorkflowExecutionEngine)

**Downstream**:
- Story 22.5 (MetadataExtractor - extracts metadata logic from this)
- Story 22.6 (Orchestrator facade needs this service)

---

## Implementation Notes

### Current Methods to Extract

```python
# From gao_dev/orchestrator/orchestrator.py

def _snapshot_project_files(self, project_path: Path) -> Set[Path]:
    """Snapshot all files in tracked directories."""
    # ~70 LOC
    # Walk directories
    # Filter tracked directories
    # Return set of paths

def _detect_artifacts(
    self,
    before_snapshot: Set[Path],
    after_snapshot: Set[Path]
) -> List[Path]:
    """Detect newly created or modified files."""
    # ~40 LOC
    # Compare snapshots
    # Filter out temporary files
    # Return list of artifacts

def _register_artifacts(
    self,
    artifacts: List[Path],
    context: Dict[str, Any]
) -> None:
    """Register detected artifacts with document lifecycle."""
    # ~98 LOC
    # For each artifact
    # Infer type
    # Extract metadata
    # Register with DocumentLifecycleManager

def _infer_document_type(
    self,
    file_path: Path,
    content: Optional[str] = None
) -> DocumentType:
    """Infer document type from path and content."""
    # ~78 LOC
    # Check path patterns
    # Parse content if needed
    # Return DocumentType
```

### New Service Structure

```python
# gao_dev/orchestrator/artifact_manager.py

class ArtifactManager:
    """Service for artifact detection and registration."""

    def __init__(
        self,
        document_lifecycle: DocumentLifecycleManager,
        tracked_dirs: List[str] = None
    ):
        self.lifecycle = document_lifecycle
        self.tracked_dirs = tracked_dirs or ["docs", "src", "gao_dev"]

    def snapshot(self, project_path: Path) -> Set[Path]:
        """Create snapshot of all tracked files."""
        # Implementation

    def detect(
        self,
        before: Set[Path],
        after: Set[Path]
    ) -> List[Path]:
        """Detect new or modified artifacts."""
        # Implementation

    def infer_type(
        self,
        path: Path,
        content: Optional[str] = None
    ) -> DocumentType:
        """Infer document type from path and content."""
        # Implementation

    def register(
        self,
        artifacts: List[Path],
        context: Dict[str, Any]
    ) -> None:
        """Register artifacts with document lifecycle."""
        # Implementation
```

### Tracked Directories

The ArtifactManager tracks these directories by default:
- `docs/` - Documentation and artifacts
- `src/` - Source code files
- `gao_dev/` - GAO-Dev specific files
- `.gao-dev/` - GAO-Dev metadata

### Type Inference Rules

Document type inference follows these patterns:

**PRD**: `docs/PRD.md`, `docs/*/PRD.md`
**Architecture**: `docs/ARCHITECTURE.md`, `docs/*/ARCHITECTURE.md`
**Epic**: `docs/epics/epic-*.md`, `docs/features/*/epics/epic-*.md`
**Story**: `docs/stories/epic-*/story-*.md`
**Ceremony**: `docs/ceremonies/*.md`
**Learning**: `docs/learnings/*.md`
**Unknown**: Fallback for unrecognized patterns

### Integration with MetadataExtractor (Story 22.5)

Story 22.5 will extract metadata extraction logic from this service into a separate MetadataExtractor utility. This keeps ArtifactManager focused on detection/registration.

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (15/15 unit tests)
- [ ] Code coverage >80% for new service
- [ ] Code review completed
- [ ] Documentation updated (docstrings)
- [ ] No breaking changes (all existing tests pass)
- [ ] Git commit created with proper message
- [ ] Service <300 LOC (target: ~250 LOC)
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
