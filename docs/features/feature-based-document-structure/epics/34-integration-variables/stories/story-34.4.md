---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 34
  story: 4
  feature: "feature-based-document-structure"
  points: 1
---

# Story 34.4: Testing & Documentation (1 point)

**Epic:** 34 - Integration & Variables
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 1

## User Story

As a **GAO-Dev user and maintainer**,
I want **comprehensive end-to-end tests and updated documentation**,
So that **the feature-based document structure works reliably and users understand how to use it**.

## Acceptance Criteria

### AC1: End-to-End Tests
- [ ] Test greenfield project initialization (create mvp feature)
- [ ] Test feature creation → epic creation → story creation flow
- [ ] Test structure validation (compliant and non-compliant)
- [ ] Test concurrent operations (multiple features, thread safety)
- [ ] Test error recovery (rollback scenarios)
- [ ] All tests automated and reproducible

### AC2: Update CLAUDE.md
- [ ] Add feature-based structure section to CLAUDE.md
- [ ] Document new CLI commands (create-feature, list-features, validate-structure)
- [ ] Update quick reference table with feature commands
- [ ] Add examples of feature-scoped workflows
- [ ] Update directory structure diagrams

### AC3: Migration Guide
- [ ] Create `docs/features/feature-based-document-structure/MIGRATION_GUIDE.md`
- [ ] Document how to migrate existing projects
- [ ] Provide migration checklist
- [ ] Include before/after examples
- [ ] Address common migration issues

### AC4: CLI Help Text
- [ ] Update `gao-dev --help` output with new commands
- [ ] Ensure create-feature help is comprehensive
- [ ] Ensure list-features help includes filter examples
- [ ] Ensure validate-structure help explains exit codes
- [ ] Add examples to all command help text

### AC5: Integration Verification
- [ ] Run full integration test suite (all 11 stories)
- [ ] Verify no regressions in existing functionality
- [ ] Performance benchmarks (feature creation <1s, validation <2s)
- [ ] Cross-platform testing (Windows and Unix paths)

## Technical Notes

### Implementation Approach

**End-to-End Test Suite:**

```python
# Location: tests/integration/test_feature_based_structure_e2e.py

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.core.services.git_integrated_state_manager import GitIntegratedStateManager
from gao_dev.core.state.feature_state_service import FeatureScope, FeatureStatus
from gao_dev.core.services.feature_path_validator import FeaturePathValidator


class TestFeatureBasedStructureE2E:
    """
    End-to-end tests for feature-based document structure.

    Tests complete workflows from feature creation to validation.
    """

    def setup_method(self):
        """Create temporary project for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        # Initialize git, .gao-dev/, etc.
        self._setup_project()

    def teardown_method(self):
        """Clean up temporary project."""
        shutil.rmtree(self.temp_dir)

    def test_greenfield_mvp_creation(self):
        """
        Test complete greenfield flow: create mvp → validate structure.

        Steps:
        1. Create MVP feature
        2. Verify folder structure created
        3. Verify database record exists
        4. Verify git commit exists
        5. Validate structure compliance
        """
        # Create MVP
        manager = self._init_state_manager()
        feature = manager.create_feature(
            name="mvp",
            scope=FeatureScope.MVP,
            scale_level=4,
            description="Initial greenfield MVP"
        )

        # Verify folder structure
        mvp_path = self.project_root / "docs" / "features" / "mvp"
        assert mvp_path.exists()
        assert (mvp_path / "PRD.md").exists()
        assert (mvp_path / "ARCHITECTURE.md").exists()
        assert (mvp_path / "README.md").exists()
        assert (mvp_path / "QA").is_dir()
        assert (mvp_path / "epics").is_dir()
        assert (mvp_path / "retrospectives").is_dir()

        # Verify database record
        assert feature.id is not None
        assert feature.name == "mvp"
        assert feature.scope == FeatureScope.MVP

        # Verify git commit
        git_log = self._get_git_log()
        assert "feat(mvp): create feature" in git_log

        # Validate structure
        validator = FeaturePathValidator()
        violations = validator.validate_structure(mvp_path)
        assert len(violations) == 0, f"Structure violations: {violations}"

    def test_feature_epic_story_flow(self):
        """
        Test complete flow: create feature → create epic → create story.

        Verifies co-located epic-story structure.
        """
        manager = self._init_state_manager()

        # Step 1: Create feature
        feature = manager.create_feature(
            name="user-auth",
            scope=FeatureScope.FEATURE,
            scale_level=3,
            description="User authentication with OAuth"
        )

        # Step 2: Create epic
        epic = manager.create_epic(
            epic_num=1,
            title="OAuth Integration",
            feature_name="user-auth"  # Link to feature
        )

        # Step 3: Create story
        story = manager.create_story(
            epic_num=1,
            story_num=1,
            title="Google OAuth provider",
            feature_name="user-auth"
        )

        # Verify co-located structure
        epic_folder = self.project_root / "docs" / "features" / "user-auth" / "epics" / "1-oauth-integration"
        assert epic_folder.exists()
        assert (epic_folder / "README.md").exists()
        assert (epic_folder / "stories").is_dir()
        assert (epic_folder / "stories" / "story-1.1.md").exists()

        # Verify database relationships
        coordinator = manager.state
        feature_state = coordinator.get_feature_state("user-auth")
        assert len(feature_state["epics"]) == 1
        assert feature_state["total_stories"] == 1

    def test_validation_compliant_and_non_compliant(self):
        """
        Test structure validation on compliant and non-compliant features.
        """
        validator = FeaturePathValidator()

        # Create compliant feature
        manager = self._init_state_manager()
        manager.create_feature("compliant", FeatureScope.FEATURE, 3)

        compliant_path = self.project_root / "docs" / "features" / "compliant"
        violations = validator.validate_structure(compliant_path)
        assert len(violations) == 0

        # Create non-compliant feature (missing README.md)
        non_compliant_path = self.project_root / "docs" / "features" / "non-compliant"
        non_compliant_path.mkdir(parents=True)
        (non_compliant_path / "PRD.md").write_text("# PRD")
        (non_compliant_path / "ARCHITECTURE.md").write_text("# Architecture")
        (non_compliant_path / "epics").mkdir()
        (non_compliant_path / "QA").mkdir()
        # Missing README.md

        violations = validator.validate_structure(non_compliant_path)
        assert len(violations) == 1
        assert "Missing required file: README.md" in violations[0]

    def test_concurrent_feature_creation(self):
        """
        Test concurrent feature creation (thread safety).
        """
        import concurrent.futures

        def create_feature(name: str):
            manager = self._init_state_manager()
            return manager.create_feature(name, FeatureScope.FEATURE, 2)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(create_feature, "feature-a"),
                executor.submit(create_feature, "feature-b"),
                executor.submit(create_feature, "feature-c")
            ]

            results = [f.result() for f in futures]

        # Verify all created successfully
        assert len(results) == 3
        assert all(f.id is not None for f in results)

        # Verify all folders exist
        for name in ["feature-a", "feature-b", "feature-c"]:
            assert (self.project_root / "docs" / "features" / name).exists()

    def test_error_recovery_rollback(self):
        """
        Test error recovery and rollback on failure.
        """
        manager = self._init_state_manager()

        # Attempt to create feature with invalid name (should fail pre-flight checks)
        with pytest.raises(ValueError, match="Invalid feature name"):
            manager.create_feature("Invalid_Name", FeatureScope.FEATURE, 3)

        # Verify no partial state
        invalid_path = self.project_root / "docs" / "features" / "Invalid_Name"
        assert not invalid_path.exists()

        coordinator = manager.state
        assert coordinator.get_feature("Invalid_Name") is None

        # Verify git clean
        assert manager.git.is_clean()
```

**CLAUDE.md Updates:**

```markdown
# Add to CLAUDE.md (Section: Essential Commands)

### Feature Management (New!)

```bash
# Create feature
gao-dev create-feature <name> --scale-level 3          # Create new feature
gao-dev create-feature mvp --scope mvp --scale-level 4  # Create MVP

# List features
gao-dev list-features                                   # List all features
gao-dev list-features --scope mvp                       # Filter by scope
gao-dev list-features --status active                   # Filter by status

# Validate structure
gao-dev validate-structure --feature user-auth          # Validate specific feature
gao-dev validate-structure --all                        # Validate all features
cd docs/features/user-auth && gao-dev validate-structure # Auto-detect

# Database migration
gao-dev migrate                                         # Apply migrations
gao-dev migrate --rollback                              # Rollback migration
```

# Add to CLAUDE.md (Section: Directory Structure)

### Feature-Based Structure (Post-Epic 32-34)

```
docs/features/
  ├── mvp/                              # Greenfield initial scope
  │   ├── PRD.md
  │   ├── ARCHITECTURE.md
  │   ├── README.md                     # Feature overview
  │   ├── EPICS.md                      # Master epic list
  │   │
  │   ├── epics/                        # Co-located epic-story structure
  │   │   ├── 1-foundation/            # Epic 1 (number + name)
  │   │   │   ├── README.md            # Epic definition
  │   │   │   ├── stories/             # Stories for Epic 1
  │   │   │   │   ├── story-1.1.md
  │   │   │   │   └── story-1.2.md
  │   │   │   └── context/             # Context XML
  │   │   │       └── story-1.1.xml
  │   │   │
  │   │   └── 2-advanced/              # Epic 2
  │   │       ├── README.md
  │   │       └── stories/
  │   │
  │   ├── QA/                          # Quality artifacts
  │   └── retrospectives/              # Retrospectives
  │
  └── user-auth/                       # Subsequent feature
      ├── PRD.md
      ├── ARCHITECTURE.md
      ├── README.md
      ├── epics/
      │   └── 1-oauth/
      │       ├── README.md
      │       └── stories/
      ├── QA/
      └── retrospectives/
```
```

**Migration Guide:**

```markdown
# Location: docs/features/feature-based-document-structure/MIGRATION_GUIDE.md

# Migration Guide: Feature-Based Document Structure

## Overview

This guide helps you migrate existing GAO-Dev projects to the new feature-based document structure (Epics 32-34).

## When to Migrate

**New Projects:** Use feature-based structure from the start (`gao-dev create-feature mvp`)

**Existing Projects:** Migration is optional. Existing structure continues working (backward compatible).

## Migration Steps

### Step 1: Run Database Migration

```bash
# Apply features table migration
gao-dev migrate

# Verify migration applied
gao-dev list-features  # Should return empty list (no features yet)
```

### Step 2: Create Features for Existing Work

If you have existing documentation in `docs/`:

```bash
# Create feature for existing work
gao-dev create-feature mvp --scope mvp --scale-level 4

# Or for specific features
gao-dev create-feature user-auth --scale-level 3
```

### Step 3: Migrate Documents

**Option A: Manual Migration (Recommended for small projects)**

```bash
# Move existing docs to feature folder
mv docs/PRD.md docs/features/mvp/PRD.md
mv docs/ARCHITECTURE.md docs/features/mvp/ARCHITECTURE.md

# Create README.md (will be auto-generated in future)
touch docs/features/mvp/README.md
```

**Option B: Automated Migration (Future)**

```bash
# Not yet implemented (Epic 35)
gao-dev migrate-feature --from docs/ --to docs/features/mvp/
```

### Step 4: Validate Structure

```bash
# Check compliance
gao-dev validate-structure --feature mvp

# Fix any violations reported
```

## Before and After

**Before (Legacy Structure):**
```
docs/
├── PRD.md
├── ARCHITECTURE.md
├── epics.md
└── stories/
    └── story-1.1.md
```

**After (Feature-Based Structure):**
```
docs/features/mvp/
├── PRD.md
├── ARCHITECTURE.md
├── README.md
├── EPICS.md
├── epics/
│   └── 1-foundation/
│       ├── README.md
│       └── stories/
│           └── story-1.1.md
├── QA/
└── retrospectives/
```

## Common Issues

### Issue 1: "Feature already exists"

**Cause:** Feature folder or DB record already exists

**Fix:**
```bash
# Check existing features
gao-dev list-features

# Remove if orphaned
rm -rf docs/features/mvp/
gao-dev migrate --rollback  # Remove DB record
gao-dev migrate              # Re-apply
gao-dev create-feature mvp
```

### Issue 2: Structure validation fails

**Cause:** Missing required files or folders

**Fix:**
```bash
# Check violations
gao-dev validate-structure --feature mvp

# Add missing files/folders as reported
```

## Rollback

If you need to rollback migration:

```bash
# Rollback database migration
gao-dev migrate --rollback

# Remove feature folders (if desired)
rm -rf docs/features/

# Continue using legacy structure
```

## Support

For issues or questions:
1. Check validation output: `gao-dev validate-structure --all`
2. Review CLAUDE.md for updated commands
3. Check feature documentation: `docs/features/feature-based-document-structure/`
```

### Code Locations

**New Files:**
- `tests/integration/test_feature_based_structure_e2e.py` (E2E tests)
- `docs/features/feature-based-document-structure/MIGRATION_GUIDE.md`
- `docs/features/feature-based-document-structure/USER_GUIDE.md`

**Files to Update:**
- `CLAUDE.md` (add feature commands, update structure diagrams)
- `README.md` (mention feature-based structure)
- `gao_dev/cli/cli.py` (update --help text)

### Dependencies

**Required Before Starting:**
- All Stories 32.1-34.3 (COMPLETE)

**Blocks:**
- None (final story in Epic 34)

### Integration Points

1. **All Previous Stories**: E2E tests verify integration of all 11 stories
2. **CLAUDE.md**: Primary documentation for developers
3. **CLI Help**: User-facing help text

## Testing Requirements

### End-to-End Tests

**Location:** `tests/integration/test_feature_based_structure_e2e.py`

**Test Coverage (comprehensive scenarios):**

1. **Greenfield Project (test_greenfield_mvp_creation)**
   - Create MVP feature
   - Verify structure created
   - Verify database record
   - Verify git commit
   - Validate compliance

2. **Feature → Epic → Story Flow (test_feature_epic_story_flow)**
   - Create feature
   - Create epic (linked to feature)
   - Create story (co-located in epic)
   - Verify relationships in database

3. **Validation (test_validation_compliant_and_non_compliant)**
   - Test compliant feature (no violations)
   - Test non-compliant feature (violations reported)

4. **Concurrency (test_concurrent_feature_creation)**
   - Create 3 features concurrently
   - Verify thread safety
   - Verify all features created correctly

5. **Error Recovery (test_error_recovery_rollback)**
   - Trigger error (invalid feature name)
   - Verify rollback (no partial state)
   - Verify git clean

## Definition of Done

- [ ] End-to-end test suite implemented (5+ test scenarios)
- [ ] All E2E tests passing
- [ ] CLAUDE.md updated with feature commands
- [ ] Migration guide created and comprehensive
- [ ] CLI help text updated for all commands
- [ ] User guide created
- [ ] Cross-platform testing complete (Windows + Unix)
- [ ] Performance benchmarks met (create <1s, validate <2s)
- [ ] No regressions in existing functionality
- [ ] Documentation reviewed and approved
- [ ] All 11 stories verified working together

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Success Criteria)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Complete system)
- **All Previous Stories:** Stories 32.1 through 34.3
