# Story 28.6: DocumentStructureManager

**Epic**: Epic 28 - Ceremony-Driven Workflow Integration
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: None (can run in parallel with Stories 28.1-28.5)

---

## User Story

**As a** workflow orchestrator
**I want** automatic document structure initialization based on work type and scale level
**So that** the correct folder structure and templates are created consistently without manual intervention

---

## Context

This story addresses **C4 Critical Fix** from CRITICAL_FIXES.md. The DocumentStructureManager was missing from the original Epic 28 plan but is required by Epic 29.5 (Action Item Integration) for systematic document organization.

**Problem Identified**:
- Epic 29.5 depends on DocumentStructureManager for organizing action items, learnings, and ceremony outputs
- No component existed to systematically create and maintain document structure
- Manual document creation is error-prone and inconsistent across scale levels
- Global docs (PRD.md, CHANGELOG.md) needed automated updates

**Solution**:
Create DocumentStructureManager service to:
1. Initialize feature folders with scale-appropriate structure
2. Manage document templates (PRD, ARCHITECTURE, CHANGELOG)
3. Update global documentation automatically
4. Integrate with DocumentLifecycleManager for tracking
5. Commit folder initialization to git atomically

**Why Critical**:
- Without this, Epic 29.5 cannot organize action items and learnings systematically
- Ensures consistent documentation structure across all scale levels
- Prevents manual errors in folder structure creation
- Required for Epic 28 to total 35 points (not 30)

---

## Acceptance Criteria

### AC1: DocumentStructureManager Class Created
- [ ] Create `gao_dev/core/services/document_structure_manager.py` (~300 LOC)
- [ ] Class `DocumentStructureManager` implemented with:
  - `__init__(project_root, doc_lifecycle, git_manager)` constructor
  - Dependency injection for DocumentLifecycleManager and GitManager
  - Project root validation on initialization
- [ ] Clean class structure with clear separation of concerns:
  - Public methods for external API
  - Private methods for internal implementation
  - Helper methods for file creation and template rendering
- [ ] Comprehensive docstrings for all public methods
- [ ] Type hints for all parameters and return values
- [ ] Structured logging using `structlog`

### AC2: initialize_feature_folder() Method - Scale Level 0
- [ ] Method signature: `initialize_feature_folder(feature_name: str, scale_level: ScaleLevel) -> Optional[Path]`
- [ ] Level 0 (Chore) behavior:
  - Returns `None` (no folder created)
  - Logs decision: "Level 0 chore, skipping folder initialization"
  - No git commit triggered
- [ ] Validation:
  - Raises `ValueError` if feature_name is empty
  - Raises `ValueError` if scale_level is invalid
- [ ] Unit test: `test_initialize_level_0_returns_none()`

### AC3: initialize_feature_folder() Method - Scale Level 1
- [ ] Level 1 (Bug Fix) behavior:
  - Creates `docs/bugs/` directory if not exists
  - Does NOT create individual bug file (optional, created on-demand)
  - Returns path to bugs directory
  - Git commit: "docs(bugs): initialize bugs directory"
- [ ] Directory creation idempotent (mkdir with exist_ok=True)
- [ ] No template files created at Level 1
- [ ] Unit test: `test_initialize_level_1_creates_bugs_dir()`

### AC4: initialize_feature_folder() Method - Scale Level 2
- [ ] Level 2 (Small Feature) behavior:
  - Creates `docs/features/<feature_name>/` directory
  - Creates subdirectories:
    - `stories/` - For story files
  - Creates template files:
    - `PRD.md` - Lightweight PRD template
    - `CHANGELOG.md` - Changelog template
  - Returns path to feature folder
  - Git commit: "docs(<feature_name>): initialize feature folder (Level 2)"
- [ ] All created documents registered with DocumentLifecycleManager
- [ ] Metadata includes: `feature`, `scale_level`
- [ ] Unit test: `test_initialize_level_2_small_feature()`

### AC5: initialize_feature_folder() Method - Scale Level 3
- [ ] Level 3 (Medium Feature) behavior:
  - All Level 2 structure PLUS:
  - Creates additional subdirectories:
    - `epics/` - For epic files
    - `retrospectives/` - For retrospective transcripts
  - Creates additional template files:
    - `ARCHITECTURE.md` - Full architecture template
  - PRD uses FULL template (not lightweight)
  - Returns path to feature folder
  - Git commit: "docs(<feature_name>): initialize feature folder (Level 3)"
- [ ] Architecture template includes system design sections
- [ ] Unit test: `test_initialize_level_3_medium_feature()`

### AC6: initialize_feature_folder() Method - Scale Level 4
- [ ] Level 4 (Greenfield) behavior:
  - All Level 3 structure PLUS:
  - Creates additional subdirectories:
    - `ceremonies/` - For planning, standup, retro transcripts
  - Creates additional files:
    - `MIGRATION_GUIDE.md` - Migration guide template
  - Updates root-level `docs/PRD.md` and `docs/ARCHITECTURE.md`
  - Returns path to feature folder
  - Git commit: "docs(<feature_name>): initialize feature folder (Level 4)"
- [ ] Root docs include link to feature folder
- [ ] Unit test: `test_initialize_level_4_greenfield()`

### AC7: update_global_docs() Method Implementation
- [ ] Method signature: `update_global_docs(feature_name: str, epic_num: int, update_type: str) -> None`
- [ ] Three update types supported:
  - `planned` - Updates `docs/PRD.md` with "Planned" status
  - `architected` - Updates `docs/ARCHITECTURE.md` with feature section
  - `completed` - Updates PRD to "Completed", updates CHANGELOG
- [ ] Update types validated (raises ValueError if invalid)
- [ ] Git commit after each update: "docs(global): update {update_type} for {feature_name}"
- [ ] Delegates to private methods:
  - `_update_global_prd()` for PRD updates
  - `_update_global_architecture()` for architecture updates
  - `_update_changelog()` for changelog updates
- [ ] Unit tests:
  - `test_update_global_docs_planned()`
  - `test_update_global_docs_completed()`

### AC8: Template System Implementation
- [ ] Private method `_prd_template(feature_name: str, template_type: str) -> str`
- [ ] Two template types:
  - `lightweight` - For Level 2 (basic PRD structure)
  - `full` - For Level 3+ (comprehensive PRD with analysis)
- [ ] Lightweight template includes (50-100 lines):
  - Feature name and summary
  - User stories section
  - Acceptance criteria section
  - Success metrics placeholder
- [ ] Full template includes (150-250 lines):
  - All lightweight sections PLUS:
  - Problem statement
  - Solution approach
  - Technical requirements
  - Dependencies
  - Timeline
  - Risk assessment
- [ ] Private method `_architecture_template(feature_name: str) -> str`
- [ ] Architecture template includes (100-150 lines):
  - System overview
  - Component diagram placeholder
  - Data models
  - API design
  - Integration points
  - Performance considerations
- [ ] Templates use consistent markdown structure
- [ ] Unit test: `test_template_rendering()`

### AC9: Helper Methods Implementation
- [ ] Private method `_create_file(path: Path, content: str) -> None`:
  - Creates parent directories if needed
  - Writes content to file
  - Logs file creation
  - Registers with DocumentLifecycleManager
- [ ] Private method `_update_global_prd(feature_name: str, epic_num: int, status: str) -> None`:
  - Loads existing PRD.md
  - Finds or creates feature section
  - Updates status (Planned/In Progress/Completed)
  - Writes updated PRD
  - Logs update
- [ ] Private method `_update_global_architecture(feature_name: str, epic_num: int) -> None`:
  - Loads existing ARCHITECTURE.md
  - Adds feature architecture section
  - Links to feature folder ARCHITECTURE.md
  - Writes updated file
- [ ] Private method `_update_changelog(feature_name: str, epic_num: int) -> None`:
  - Loads CHANGELOG.md
  - Adds entry to "Unreleased" section
  - Format: "- Epic {epic_num}: {feature_name} completed"
  - Writes updated changelog

### AC10: Git Integration
- [ ] Git commit after folder initialization:
  - Message format: "docs({feature_name}): initialize feature folder (Level {level})"
  - Includes all created files and directories
- [ ] Git commit after global doc updates:
  - Message format: "docs(global): update {update_type} for {feature_name}"
- [ ] Atomic operations: folder creation + registration + commit
- [ ] Rollback on failure (remove created files if commit fails)
- [ ] Integration with GitManager service

### AC11: DocumentLifecycleManager Integration
- [ ] All created documents registered with DocumentLifecycleManager
- [ ] Registration includes metadata:
  - `feature`: Feature name
  - `scale_level`: Scale level value
  - `epic_num`: Epic number (if applicable)
  - `doc_type`: DocumentType enum (PRD, ARCHITECTURE, CHANGELOG, etc.)
- [ ] Registration happens immediately after file creation
- [ ] Registration failure triggers cleanup (remove created files)

### AC12: Error Handling and Validation
- [ ] Validation:
  - `feature_name` must not be empty
  - `scale_level` must be valid ScaleLevel enum
  - `update_type` must be one of: planned, architected, completed
  - `project_root` must exist and be writable
- [ ] Error handling:
  - IO errors during file creation logged and re-raised
  - Git commit failures trigger rollback
  - DocumentLifecycle registration failures trigger cleanup
- [ ] Clear error messages for all failure scenarios
- [ ] Structured logging for debugging

### AC13: Unit Tests (8 tests minimum)
- [ ] `test_initialize_level_0_returns_none()` - Level 0 behavior
- [ ] `test_initialize_level_1_creates_bugs_dir()` - Level 1 bugs directory
- [ ] `test_initialize_level_2_small_feature()` - Level 2 structure
- [ ] `test_initialize_level_3_medium_feature()` - Level 3 structure
- [ ] `test_initialize_level_4_greenfield()` - Level 4 structure
- [ ] `test_update_global_docs_planned()` - Global PRD update (planned)
- [ ] `test_update_global_docs_completed()` - Global PRD + CHANGELOG update
- [ ] `test_template_rendering()` - Template generation
- [ ] Test coverage >90%
- [ ] All tests use mocks for git operations
- [ ] Tests verify DocumentLifecycleManager registration calls

---

## Technical Details

### File Structure
```
gao_dev/core/services/
   document_structure_manager.py  # New file (~300 LOC)

tests/core/services/
   test_document_structure_manager.py  # New file (~200 LOC)
```

### Implementation Approach

**1. Class Structure** (~300 LOC total):
```python
from pathlib import Path
from typing import Optional
import structlog
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel
from gao_dev.core.services.document_lifecycle_manager import (
    DocumentLifecycleManager,
    DocumentType
)
from gao_dev.core.git_manager import GitManager

logger = structlog.get_logger()

class DocumentStructureManager:
    """
    Manages document structure based on work type and scale level.

    Responsibilities:
    - Initialize feature folders with correct structure for each scale level
    - Create document templates (PRD, ARCHITECTURE, CHANGELOG)
    - Update global docs (PRD.md, CHANGELOG.md, ARCHITECTURE.md)
    - Enforce structure consistency across features
    - Integrate with DocumentLifecycleManager for tracking

    Scale Level Structures:
    - Level 0 (Chore): No folder created
    - Level 1 (Bug): docs/bugs/ directory
    - Level 2 (Small Feature): docs/features/<name>/ + PRD + stories/
    - Level 3 (Medium Feature): + ARCHITECTURE + epics/ + retrospectives/
    - Level 4 (Greenfield): + ceremonies/ + MIGRATION_GUIDE + root docs
    """

    def __init__(
        self,
        project_root: Path,
        doc_lifecycle: DocumentLifecycleManager,
        git_manager: GitManager
    ):
        """
        Initialize DocumentStructureManager.

        Args:
            project_root: Root directory of the project
            doc_lifecycle: DocumentLifecycleManager for tracking documents
            git_manager: GitManager for committing changes

        Raises:
            ValueError: If project_root doesn't exist or isn't writable
        """
        if not project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        self.project_root = project_root
        self.doc_lifecycle = doc_lifecycle
        self.git = git_manager

        logger.info(
            "document_structure_manager_initialized",
            project_root=str(project_root)
        )

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel
    ) -> Optional[Path]:
        """
        Initialize feature folder based on scale level.

        Creates appropriate folder structure and template files for the
        given scale level. All created documents are registered with
        DocumentLifecycleManager and committed to git.

        Args:
            feature_name: Name of the feature (kebab-case recommended)
            scale_level: Scale level determining folder structure

        Returns:
            Path to created folder, or None for Level 0

        Raises:
            ValueError: If feature_name is empty or scale_level invalid
        """
        if not feature_name:
            raise ValueError("feature_name cannot be empty")

        logger.info(
            "initializing_feature_folder",
            feature_name=feature_name,
            scale_level=scale_level.name
        )

        # Level 0: No folder created
        if scale_level == ScaleLevel.LEVEL_0_CHORE:
            logger.info(
                "level_0_chore_skip_folder",
                feature_name=feature_name
            )
            return None

        # Level 1: Optional bug report directory
        if scale_level == ScaleLevel.LEVEL_1_BUG_FIX:
            bug_path = self.project_root / "docs" / "bugs"
            bug_path.mkdir(parents=True, exist_ok=True)

            self.git.add_all()
            self.git.commit("docs(bugs): initialize bugs directory")

            logger.info("bugs_directory_created", path=str(bug_path))
            return bug_path

        # Level 2+: Feature folder
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=True)

        # Create structure based on level
        if scale_level >= ScaleLevel.LEVEL_2_SMALL_FEATURE:
            # Stories directory
            (feature_path / "stories").mkdir(exist_ok=True)

            # Lightweight PRD for Level 2
            prd_content = self._prd_template(feature_name, "lightweight")
            self._create_file(feature_path / "PRD.md", prd_content)

            # CHANGELOG
            changelog_content = "# Changelog\n\n## Unreleased\n\n"
            self._create_file(feature_path / "CHANGELOG.md", changelog_content)

        if scale_level >= ScaleLevel.LEVEL_3_MEDIUM_FEATURE:
            # Additional directories
            (feature_path / "epics").mkdir(exist_ok=True)
            (feature_path / "retrospectives").mkdir(exist_ok=True)

            # Full architecture document
            arch_content = self._architecture_template(feature_name)
            self._create_file(feature_path / "ARCHITECTURE.md", arch_content)

            # Upgrade PRD to full template
            prd_content = self._prd_template(feature_name, "full")
            self._create_file(feature_path / "PRD.md", prd_content)

        if scale_level == ScaleLevel.LEVEL_4_GREENFIELD:
            # Greenfield-specific additions
            (feature_path / "ceremonies").mkdir(exist_ok=True)

            migration_content = "# Migration Guide\n\nTBD\n"
            self._create_file(
                feature_path / "MIGRATION_GUIDE.md",
                migration_content
            )

        # Register with document lifecycle
        self.doc_lifecycle.register_document(
            path=feature_path / "PRD.md",
            doc_type=DocumentType.PRD,
            metadata={
                "feature": feature_name,
                "scale_level": scale_level.value
            }
        )

        # Git commit
        self.git.add_all()
        self.git.commit(
            f"docs({feature_name}): initialize feature folder (Level {scale_level.value})"
        )

        logger.info(
            "feature_folder_initialized",
            feature_name=feature_name,
            scale_level=scale_level.name,
            path=str(feature_path)
        )

        return feature_path

    def update_global_docs(
        self,
        feature_name: str,
        epic_num: int,
        update_type: str  # 'planned', 'architected', 'completed'
    ) -> None:
        """
        Update global PRD and ARCHITECTURE docs.

        Args:
            feature_name: Name of the feature
            epic_num: Epic number for the feature
            update_type: Type of update (planned/architected/completed)

        Raises:
            ValueError: If update_type is invalid
        """
        valid_types = ['planned', 'architected', 'completed']
        if update_type not in valid_types:
            raise ValueError(
                f"Invalid update_type: {update_type}. "
                f"Must be one of: {valid_types}"
            )

        logger.info(
            "updating_global_docs",
            feature_name=feature_name,
            epic_num=epic_num,
            update_type=update_type
        )

        if update_type == 'planned':
            self._update_global_prd(feature_name, epic_num, status="Planned")
        elif update_type == 'architected':
            self._update_global_architecture(feature_name, epic_num)
        elif update_type == 'completed':
            self._update_global_prd(feature_name, epic_num, status="Completed")
            self._update_changelog(feature_name, epic_num)

        # Git commit
        self.git.add_all()
        self.git.commit(
            f"docs(global): update {update_type} for {feature_name}"
        )

    # Private helper methods (~150 LOC)

    def _create_file(self, path: Path, content: str) -> None:
        """Create file with content and log creation."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        logger.debug("file_created", path=str(path))

    def _prd_template(self, feature_name: str, template_type: str) -> str:
        """Generate PRD template (lightweight or full)."""
        if template_type == "lightweight":
            return f"""# {feature_name} - Product Requirements Document

## Summary
TBD

## User Stories
- As a user, I want...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Success Metrics
TBD
"""
        else:  # full
            return f"""# {feature_name} - Product Requirements Document

## Summary
TBD

## Problem Statement
TBD

## Solution Approach
TBD

## User Stories
- As a user, I want...

## Technical Requirements
TBD

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Dependencies
TBD

## Timeline
TBD

## Risk Assessment
TBD

## Success Metrics
TBD
"""

    def _architecture_template(self, feature_name: str) -> str:
        """Generate architecture template."""
        return f"""# {feature_name} - Architecture

## System Overview
TBD

## Component Diagram
```
[Diagram placeholder]
```

## Data Models
TBD

## API Design
TBD

## Integration Points
TBD

## Performance Considerations
TBD
"""

    def _update_global_prd(
        self,
        feature_name: str,
        epic_num: int,
        status: str
    ) -> None:
        """Update global PRD with feature status."""
        prd_path = self.project_root / "docs" / "PRD.md"

        if not prd_path.exists():
            content = "# Product Requirements\n\n"
        else:
            content = prd_path.read_text(encoding='utf-8')

        # Add/update feature entry
        feature_line = f"- Epic {epic_num}: {feature_name} - {status}\n"

        if f"Epic {epic_num}:" in content:
            # Update existing
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if f"Epic {epic_num}:" in line:
                    lines[i] = feature_line.rstrip()
                    break
            content = '\n'.join(lines)
        else:
            # Add new
            content += feature_line

        prd_path.write_text(content, encoding='utf-8')
        logger.debug("global_prd_updated", feature_name=feature_name, status=status)

    def _update_global_architecture(
        self,
        feature_name: str,
        epic_num: int
    ) -> None:
        """Update global ARCHITECTURE with feature section."""
        arch_path = self.project_root / "docs" / "ARCHITECTURE.md"

        if not arch_path.exists():
            content = "# Architecture\n\n"
        else:
            content = arch_path.read_text(encoding='utf-8')

        # Add feature section
        section = f"""
## Epic {epic_num}: {feature_name}

See [Feature Architecture](features/{feature_name}/ARCHITECTURE.md) for details.

"""
        content += section
        arch_path.write_text(content, encoding='utf-8')
        logger.debug("global_architecture_updated", feature_name=feature_name)

    def _update_changelog(
        self,
        feature_name: str,
        epic_num: int
    ) -> None:
        """Update CHANGELOG with epic completion."""
        changelog_path = self.project_root / "docs" / "CHANGELOG.md"

        if not changelog_path.exists():
            content = "# Changelog\n\n## Unreleased\n\n"
        else:
            content = changelog_path.read_text(encoding='utf-8')

        # Add entry under Unreleased
        entry = f"- Epic {epic_num}: {feature_name} completed\n"

        if "## Unreleased" in content:
            content = content.replace(
                "## Unreleased\n",
                f"## Unreleased\n{entry}"
            )
        else:
            content += f"\n## Unreleased\n{entry}"

        changelog_path.write_text(content, encoding='utf-8')
        logger.debug("changelog_updated", feature_name=feature_name)
```

**2. Unit Tests** (~200 LOC):
```python
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from gao_dev.core.services.document_structure_manager import DocumentStructureManager
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project root."""
    return tmp_path

@pytest.fixture
def mock_doc_lifecycle():
    """Mock DocumentLifecycleManager."""
    return Mock()

@pytest.fixture
def mock_git():
    """Mock GitManager."""
    return Mock()

@pytest.fixture
def manager(temp_project, mock_doc_lifecycle, mock_git):
    """Create DocumentStructureManager instance."""
    return DocumentStructureManager(
        project_root=temp_project,
        doc_lifecycle=mock_doc_lifecycle,
        git_manager=mock_git
    )

def test_initialize_level_0_returns_none(manager):
    """Level 0 should return None without creating folders."""
    result = manager.initialize_feature_folder(
        "quick-fix",
        ScaleLevel.LEVEL_0_CHORE
    )
    assert result is None
    # No git commit
    manager.git.commit.assert_not_called()

def test_initialize_level_1_creates_bugs_dir(manager, temp_project):
    """Level 1 should create bugs directory."""
    result = manager.initialize_feature_folder(
        "bug-123",
        ScaleLevel.LEVEL_1_BUG_FIX
    )

    bugs_dir = temp_project / "docs" / "bugs"
    assert bugs_dir.exists()
    assert result == bugs_dir
    manager.git.commit.assert_called_once()

def test_initialize_level_2_small_feature(manager, temp_project, mock_doc_lifecycle):
    """Level 2 should create feature folder with PRD and stories."""
    result = manager.initialize_feature_folder(
        "my-feature",
        ScaleLevel.LEVEL_2_SMALL_FEATURE
    )

    feature_path = temp_project / "docs" / "features" / "my-feature"
    assert feature_path.exists()
    assert (feature_path / "PRD.md").exists()
    assert (feature_path / "CHANGELOG.md").exists()
    assert (feature_path / "stories").exists()

    # Verify registration
    mock_doc_lifecycle.register_document.assert_called_once()

    # Verify git commit
    manager.git.commit.assert_called_once()

# More tests...
```

---

## Testing Strategy

### Unit Tests (8 tests minimum)
1. **test_initialize_level_0_returns_none**: Verify Level 0 returns None, no folders created
2. **test_initialize_level_1_creates_bugs_dir**: Verify bugs directory created
3. **test_initialize_level_2_small_feature**: Verify Level 2 structure (PRD, stories, CHANGELOG)
4. **test_initialize_level_3_medium_feature**: Verify Level 3 adds ARCHITECTURE, epics, retrospectives
5. **test_initialize_level_4_greenfield**: Verify Level 4 adds ceremonies, MIGRATION_GUIDE
6. **test_update_global_docs_planned**: Verify global PRD updated with "Planned" status
7. **test_update_global_docs_completed**: Verify global PRD updated to "Completed" and CHANGELOG updated
8. **test_template_rendering**: Verify lightweight vs full PRD templates

### Integration Tests
- Test with real DocumentLifecycleManager and GitManager
- Verify end-to-end folder initialization and git commits
- Test rollback on failure scenarios

### Manual Testing
```bash
# Test via Python console
from pathlib import Path
from gao_dev.core.services.document_structure_manager import DocumentStructureManager
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel

# Initialize manager (requires orchestrator setup)
manager = DocumentStructureManager(...)

# Test Level 2 initialization
path = manager.initialize_feature_folder("test-feature", ScaleLevel.LEVEL_2_SMALL_FEATURE)
print(f"Created: {path}")

# Verify structure
assert (path / "PRD.md").exists()
assert (path / "stories").exists()
```

---

## Definition of Done

- [ ] All acceptance criteria met (AC1-AC13)
- [ ] DocumentStructureManager class created (~300 LOC)
- [ ] All 5 scale levels implemented correctly
- [ ] Template system working (lightweight, full, architecture)
- [ ] Global docs update methods implemented
- [ ] DocumentLifecycleManager integration complete
- [ ] Git commits working atomically
- [ ] Unit tests passing (>90% coverage, 8+ tests)
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation complete (docstrings, comments)
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message:
  - `feat(epic-28): implement Story 28.6 - DocumentStructureManager`
- [ ] Story marked as complete in sprint-status.yaml

---

## Dependencies

**Upstream** (Can run in parallel):
- Epic 20 (DocumentLifecycleManager) - COMPLETE
- Epic 23 (GitManager) - COMPLETE
- Adaptive Agile ScaleLevel enum - COMPLETE

**Downstream** (Depends on this story):
- Story 29.5 (Action Item Integration) - Needs DocumentStructureManager to organize action items
- Epic 29 ceremonies - Need structured folders for ceremony outputs

**Parallel Work** (No dependencies):
- Stories 28.1-28.5 can be developed in parallel with this story
- This story is independent of ceremony workflow definitions

---

## Notes

**Why This Was Missing**:
- Original Epic 28 planning focused on ceremony integration
- Document structure management was assumed to exist
- Epic 29.5 planning revealed the missing dependency
- Added as C4 critical fix to bring Epic 28 to 35 points

**Design Decisions**:
1. **Scale-Adaptive Structure**: Each scale level builds on previous level (Level 3 includes all Level 2 structure)
2. **Template System**: Separate lightweight vs full templates to avoid overwhelming small features
3. **Git Integration**: Atomic commits ensure folder initialization is all-or-nothing
4. **DocumentLifecycle Integration**: Automatic registration ensures all documents are tracked
5. **Global Docs Updates**: Centralized PRD and CHANGELOG provide project-wide visibility

**Integration Points**:
- DocumentLifecycleManager: Registers all created documents
- GitManager: Commits folder initialization atomically
- ScaleLevel enum: Determines folder structure
- Epic 29.5: Uses this for organizing action items and learnings

**Future Enhancements** (Not in this story):
- Custom template support via configuration
- Template validation (linting markdown)
- Folder structure migration for existing features
- Multi-project support (different structures per project type)

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `docs/features/ceremony-integration-and-self-learning/ARCHITECTURE.md`
- Epic 28: `docs/features/ceremony-integration-and-self-learning/epics/epic-28-ceremony-workflow-integration.md`
- Critical Fixes: `docs/features/ceremony-integration-and-self-learning/CRITICAL_FIXES.md` (C4 fix, lines 514-553)
- DocumentLifecycleManager: `gao_dev/core/services/document_lifecycle_manager.py`
- GitManager: `gao_dev/core/git_manager.py`
- ScaleLevel: `gao_dev/methodologies/adaptive_agile/scale_levels.py`
