---
document:
  type: "story"
  state: "complete"
  created: "2025-11-11"
  completed: "2025-11-11"
  epic: 32
  story: 3
  feature: "feature-based-document-structure"
  points: 2
---

# Story 32.3: Create FeaturePathValidator (2 points)

**Epic:** 32 - State Service Integration
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **system component needing path validation**,
I want **a stateless FeaturePathValidator using pure functions**,
So that **I can validate feature paths without creating circular dependencies with FeatureRegistry or DocumentLifecycleManager**.

## Acceptance Criteria

### AC1: Stateless Validator Implementation
- [x] Create `gao_dev/core/services/feature_path_validator.py` as stateless validator
- [x] All methods are static or class methods (no instance state)
- [x] No database queries (pure functions only)
- [x] No dependencies on FeatureRegistry or DocumentLifecycleManager
- [x] Breaks circular dependency chain

### AC2: Path Validation Methods
- [x] `validate_feature_path(path: Path, feature_name: str) -> bool`
  - Returns True if path matches `docs/features/{feature_name}/...` pattern
  - Cross-platform (handles Windows and Unix paths)
- [x] `extract_feature_from_path(path: Path) -> Optional[str]`
  - Extracts feature name from path
  - Returns None if not feature-scoped
- [x] `validate_structure(feature_path: Path) -> List[str]`
  - Validates complete feature folder structure
  - Returns list of violation messages (empty if compliant)

### AC3: Structure Validation Rules
- [x] Check required files exist: PRD.md, ARCHITECTURE.md, README.md
- [x] Check required folders exist: epics/, QA/
- [x] Validate epics/ is a folder (not epics.md file)
- [x] Detect old patterns (epics.md, stories/ at root level)
- [x] Provide actionable violation messages

### AC4: Cross-Platform Compatibility
- [x] Handle Windows paths (backslashes)
- [x] Handle Unix paths (forward slashes)
- [x] Normalize paths before validation
- [x] Test on both platforms

### AC5: Testing
- [x] 25+ unit test assertions covering:
  - Path validation (valid and invalid patterns)
  - Feature extraction (various path formats)
  - Structure validation (compliant and non-compliant)
  - Cross-platform paths
  - Edge cases (empty paths, root paths, etc.)

## Technical Notes

### Implementation Approach

**Pure Functions Pattern:**

```python
# Location: gao_dev/core/services/feature_path_validator.py

from pathlib import Path
from typing import Optional, List
import structlog

logger = structlog.get_logger(__name__)


class FeaturePathValidator:
    """
    Stateless validator for feature paths.

    Uses pure functions (no database queries, no dependencies).
    Breaks circular dependency between FeatureRegistry and DocumentLifecycleManager.

    All methods are static - no instance state required.
    """

    @staticmethod
    def validate_feature_path(path: Path, feature_name: str) -> bool:
        """
        Validate path matches feature pattern.

        Args:
            path: Path to validate (e.g., docs/features/user-auth/PRD.md)
            feature_name: Expected feature name (e.g., "user-auth")

        Returns:
            True if path matches docs/features/{feature_name}/... pattern

        Examples:
            >>> validate_feature_path(Path("docs/features/user-auth/PRD.md"), "user-auth")
            True

            >>> validate_feature_path(Path("docs/PRD.md"), "user-auth")
            False

            >>> validate_feature_path(Path("docs/features/mvp/epics/1-foundation/README.md"), "mvp")
            True
        """
        # Normalize path (cross-platform)
        normalized = str(path).replace("\\", "/")

        # Check if path starts with docs/features/{feature_name}/
        expected_prefix = f"docs/features/{feature_name}/"
        return normalized.startswith(expected_prefix)

    @staticmethod
    def extract_feature_from_path(path: Path) -> Optional[str]:
        """
        Extract feature name from path.

        Args:
            path: Path to extract from

        Returns:
            Feature name or None if not feature-scoped

        Examples:
            >>> extract_feature_from_path(Path("docs/features/user-auth/PRD.md"))
            "user-auth"

            >>> extract_feature_from_path(Path("docs/features/mvp/epics/1-foundation/README.md"))
            "mvp"

            >>> extract_feature_from_path(Path("docs/PRD.md"))
            None

            >>> extract_feature_from_path(Path("src/main.py"))
            None
        """
        parts = path.parts

        # Check if path follows docs/features/{name}/... pattern
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "features":
            return parts[2]

        return None

    @staticmethod
    def validate_structure(feature_path: Path) -> List[str]:
        """
        Validate feature folder structure.

        Args:
            feature_path: Path to feature folder (e.g., docs/features/user-auth)

        Returns:
            List of violation messages (empty list if compliant)

        Checks:
        - Required files exist: PRD.md, ARCHITECTURE.md, README.md
        - Required folders exist: epics/, QA/
        - epics/ is a folder (not epics.md file)
        - No old patterns (epics.md, stories/ at root)

        Examples:
            >>> validate_structure(Path("docs/features/user-auth"))
            []  # Compliant

            >>> validate_structure(Path("docs/features/incomplete"))
            ["Missing required file: README.md", "Missing required folder: QA/"]
        """
        violations = []

        # Check feature path exists
        if not feature_path.exists():
            return [f"Feature path does not exist: {feature_path}"]

        if not feature_path.is_dir():
            return [f"Feature path is not a directory: {feature_path}"]

        # Check required files
        required_files = ["PRD.md", "ARCHITECTURE.md", "README.md"]
        for required_file in required_files:
            file_path = feature_path / required_file
            if not file_path.exists():
                violations.append(f"Missing required file: {required_file}")

        # Check required folders
        required_folders = ["epics", "QA"]
        for required_folder in required_folders:
            folder_path = feature_path / required_folder
            if not folder_path.exists():
                violations.append(f"Missing required folder: {required_folder}/")
            elif not folder_path.is_dir():
                violations.append(
                    f"{required_folder} is a file, should be a folder"
                )

        # Check for old patterns
        if (feature_path / "epics.md").exists():
            violations.append(
                "Using old epics.md format (should be epics/ folder with co-located stories)"
            )

        if (feature_path / "stories").exists() and (feature_path / "stories").is_dir():
            violations.append(
                "Using old stories/ folder at root (stories should be co-located inside epics/{epic-name}/stories/)"
            )

        return violations

    @staticmethod
    def validate_epic_structure(epic_path: Path) -> List[str]:
        """
        Validate epic folder structure (co-located pattern).

        Args:
            epic_path: Path to epic folder (e.g., docs/features/mvp/epics/1-foundation)

        Returns:
            List of violation messages (empty if compliant)

        Checks:
        - Epic folder follows {number}-{name} pattern
        - README.md exists (epic definition)
        - stories/ folder exists
        - context/ folder exists (optional but recommended)
        """
        violations = []

        # Check epic path exists
        if not epic_path.exists():
            return [f"Epic path does not exist: {epic_path}"]

        if not epic_path.is_dir():
            return [f"Epic path is not a directory: {epic_path}"]

        # Check epic folder naming (should be {number}-{name})
        epic_folder_name = epic_path.name
        if not epic_folder_name[0].isdigit():
            violations.append(
                f"Epic folder should start with number: {epic_folder_name} "
                "(expected format: 1-epic-name)"
            )

        # Check required files
        if not (epic_path / "README.md").exists():
            violations.append("Missing epic definition: README.md")

        # Check required folders
        if not (epic_path / "stories").exists():
            violations.append("Missing stories/ folder")
        elif not (epic_path / "stories").is_dir():
            violations.append("stories is a file, should be a folder")

        # Optional but recommended
        if not (epic_path / "context").exists():
            logger.warning(
                "No context/ folder (optional but recommended for context XML files)",
                epic_path=str(epic_path)
            )

        return violations
```

### Code Locations

**New File:**
- `gao_dev/core/services/feature_path_validator.py` (create new)

**Files That Will Use This:**
- `gao_dev/core/services/document_lifecycle_manager.py` (Story 33.1 integration)
- CLI validate-structure command (Story 33.3)

### Dependencies

**Required Before Starting:**
- None (stateless, no dependencies)

**Blocks:**
- Story 33.1: DocumentStructureManager enhancement (needs validator for structure checks)
- Story 33.3: CLI validate-structure command (uses validator)

### Integration Points

1. **DocumentLifecycleManager**: Will use `extract_feature_from_path()` to auto-tag documents
2. **CLI Commands**: Will use `validate_structure()` for compliance checking
3. **No Circular Dependencies**: Stateless design breaks dependency chain

## Testing Requirements

### Unit Tests (25+ assertions)

**Location:** `tests/core/services/test_feature_path_validator.py`

**Test Coverage:**

1. **validate_feature_path() - 8 assertions**
   - Valid feature path (docs/features/user-auth/PRD.md)
   - Valid MVP path (docs/features/mvp/epics/1-foundation/README.md)
   - Invalid path (docs/PRD.md)
   - Invalid path (src/main.py)
   - Windows path (docs\features\user-auth\PRD.md)
   - Unix path (docs/features/user-auth/PRD.md)
   - Wrong feature name (path for "mvp" but checking "user-auth")
   - Edge case (empty path, root path)

2. **extract_feature_from_path() - 8 assertions**
   - Extract from PRD.md path
   - Extract from nested epic path
   - Extract from story path
   - Extract "mvp" correctly
   - Return None for non-feature path (docs/PRD.md)
   - Return None for src/ path
   - Windows path extraction
   - Unix path extraction

3. **validate_structure() - 7 assertions**
   - Compliant structure (all files and folders present)
   - Missing PRD.md
   - Missing README.md
   - Missing QA/ folder
   - epics is a file (should be folder)
   - Old pattern detected (epics.md exists)
   - Old pattern detected (stories/ at root)

4. **validate_epic_structure() - 2 assertions**
   - Compliant epic structure
   - Missing README.md or stories/

## Definition of Done

- [x] FeaturePathValidator implemented with all static methods
- [x] No instance state (stateless)
- [x] No database queries (pure functions)
- [x] All 4 validation methods working
- [x] 25+ unit test assertions passing (41 assertions, 37 tests)
- [x] Cross-platform compatibility verified
- [x] Code reviewed and approved
- [x] Type hints throughout (mypy passes)
- [x] Structlog logging for warnings (not errors in pure functions)

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 2)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Component 3 - FeaturePathValidator)
- **Design Decision:** Stateless validator breaks circular dependencies
