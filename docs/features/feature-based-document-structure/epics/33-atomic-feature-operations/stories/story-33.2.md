---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 33
  story: 2
  feature: "feature-based-document-structure"
  points: 4
---

# Story 33.2: Extend GitIntegratedStateManager (4 points)

**Epic:** 33 - Atomic Feature Operations
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 4

## User Story

As a **developer creating features**,
I want **GitIntegratedStateManager.create_feature() method following the atomic pattern**,
So that **feature creation is guaranteed atomic (file + DB + git together) with automatic rollback on errors**.

## Acceptance Criteria

### AC1: Implement create_feature() Method
- [ ] Add `create_feature()` to GitIntegratedStateManager
- [ ] Follow exact same atomic pattern as create_epic(), create_story()
- [ ] Integrate DocumentStructureManager (helper, auto_commit=false)
- [ ] Integrate StateCoordinator.create_feature() (DB insert)
- [ ] Single git commit at the end (atomic operation)

### AC2: Atomic Operation Pattern
- [ ] **Pre-flight checks**: Verify git working tree is clean
- [ ] **Create checkpoint**: Git stash or note current HEAD
- [ ] **File operations**: Call DocumentStructureManager with auto_commit=false
- [ ] **Database insert**: Call StateCoordinator.create_feature()
- [ ] **Git commit**: Single atomic commit with conventional format
- [ ] **Rollback on error**: Git reset + DB rollback if any step fails

### AC3: Pre-Flight Validation
- [ ] Check git working tree is clean (no uncommitted changes)
- [ ] Check feature name doesn't already exist (DB check)
- [ ] Check feature folder doesn't already exist (filesystem check)
- [ ] Validate feature name format (kebab-case)
- [ ] Clear error messages for validation failures

### AC4: Rollback Logic
- [ ] If file creation fails: No DB changes, no git commit
- [ ] If DB insert fails: Delete created files, no git commit
- [ ] If git commit fails: Rollback DB, delete files
- [ ] All-or-nothing guarantee (atomic)
- [ ] Log rollback actions with structlog

### AC5: Testing
- [ ] 50+ unit test assertions covering:
  - Successful atomic creation
  - Pre-flight check failures
  - File creation failures
  - DB insert failures
  - Git commit failures
  - Rollback verification (files deleted, DB clean)
- [ ] 15+ integration test scenarios:
  - End-to-end feature creation
  - Concurrent feature creation (different names)
  - Error recovery scenarios
  - Performance (<1s for feature creation)

## Technical Notes

### Implementation Approach

**Extend GitIntegratedStateManager (gao_dev/core/services/git_integrated_state_manager.py):**

```python
# Location: gao_dev/core/services/git_integrated_state_manager.py (lines ~100-400)

from gao_dev.core.services.document_structure_manager import DocumentStructureManager
from gao_dev.core.state.state_coordinator import StateCoordinator
from gao_dev.core.state.feature_state_service import FeatureScope, FeatureStatus

class GitIntegratedStateManager:
    """
    Atomic state manager integrating file + DB + git operations.

    EXISTING METHODS (Epic 25-27):
    - create_epic() - Atomic epic creation
    - create_story() - Atomic story creation
    - transition_story() - Atomic state transitions

    NEW METHOD (Story 33.2):
    - create_feature() - Atomic feature creation

    All operations follow pattern:
    1. Pre-flight checks
    2. Create checkpoint
    3. File operations
    4. Database operations
    5. Git commit
    6. Rollback on any failure
    """

    def __init__(
        self,
        project_root: Path,
        git_manager: GitManager,
        state_coordinator: StateCoordinator,
        document_structure_manager: DocumentStructureManager,  # NEW dependency
        lifecycle_manager: DocumentLifecycleManager
    ):
        self.project_root = project_root
        self.git = git_manager
        self.state = state_coordinator
        self.doc_structure = document_structure_manager  # NEW
        self.lifecycle = lifecycle_manager

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Feature:
        """
        Create feature atomically (file + DB + git).

        This is the PRIMARY method for feature creation. It guarantees:
        - All operations succeed together OR
        - All operations roll back (no partial state)

        Args:
            name: Feature name (kebab-case, e.g., "user-auth", "mvp")
            scope: MVP or FEATURE
            scale_level: 0-4 (project scale)
            description: Optional feature description
            owner: Optional owner

        Returns:
            Feature object with metadata

        Raises:
            ValueError: If pre-flight checks fail (feature exists, invalid name, etc.)
            RuntimeError: If operation fails and rollback succeeds
            Exception: If operation AND rollback both fail (critical error)

        Example:
            >>> manager = GitIntegratedStateManager(...)
            >>> feature = manager.create_feature(
            ...     name="user-auth",
            ...     scope=FeatureScope.FEATURE,
            ...     scale_level=3,
            ...     description="User authentication with OAuth"
            ... )
            >>> feature.name
            "user-auth"
        """
        logger.info(
            "Creating feature atomically",
            name=name,
            scope=scope.value,
            scale_level=scale_level
        )

        # STEP 1: Pre-flight checks
        self._pre_flight_checks_feature(name, scope, scale_level)

        # STEP 2: Create checkpoint (note current git HEAD)
        checkpoint = self.git.get_current_commit_hash()

        feature_path = None
        feature = None

        try:
            # STEP 3: File operations (DocumentStructureManager - NO COMMIT!)
            logger.info("Creating feature folder structure", name=name)
            feature_path = self.doc_structure.initialize_feature_folder(
                feature_name=name,
                scale_level=ScaleLevel(scale_level),
                description=description,
                auto_commit=False  # CRITICAL: No git commit yet!
            )

            # STEP 4: Database insert (StateCoordinator)
            logger.info("Inserting feature into database", name=name)
            feature = self.state.create_feature(
                name=name,
                scope=scope,
                scale_level=scale_level,
                description=description,
                owner=owner
            )

            # STEP 5: Single atomic git commit
            logger.info("Committing feature to git", name=name)
            self.git.add_all()
            self.git.commit(
                f"feat({name}): create feature\n\n"
                f"Scope: {scope.value}\n"
                f"Scale Level: {scale_level}\n"
                f"Description: {description or 'N/A'}\n\n"
                f"Created with GitIntegratedStateManager (atomic operation).\n\n"
                f"🤖 Generated with GAO-Dev\n"
                f"Co-Authored-By: Claude <noreply@anthropic.com>"
            )

            logger.info(
                "Feature created successfully (atomic)",
                name=name,
                feature_id=feature.id
            )

            return feature

        except Exception as e:
            logger.error(
                "Feature creation failed - initiating rollback",
                name=name,
                error=str(e),
                exc_info=True
            )

            # STEP 6: Rollback on error
            self._rollback_feature_creation(
                name=name,
                feature_path=feature_path,
                feature=feature,
                checkpoint=checkpoint
            )

            raise RuntimeError(
                f"Feature creation failed and rolled back: {str(e)}"
            ) from e

    def _pre_flight_checks_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int
    ) -> None:
        """
        Pre-flight checks before feature creation.

        Raises:
            ValueError: If any check fails
        """
        # Check 1: Git working tree is clean
        if not self.git.is_clean():
            raise ValueError(
                "Git working tree has uncommitted changes. "
                "Commit or stash changes before creating feature."
            )

        # Check 2: Feature name format (kebab-case)
        import re
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', name):
            raise ValueError(
                f"Invalid feature name: '{name}'\n"
                "Feature names must be kebab-case (lowercase, hyphens only).\n"
                "Examples: user-auth, payment-processing, analytics-dashboard"
            )

        # Check 3: Feature doesn't exist in DB
        existing_feature = self.state.get_feature(name)
        if existing_feature:
            raise ValueError(
                f"Feature '{name}' already exists in database.\n"
                f"Use 'gao-dev list-features' to see all features."
            )

        # Check 4: Feature folder doesn't exist on filesystem
        feature_path = self.project_root / "docs" / "features" / name
        if feature_path.exists():
            raise ValueError(
                f"Feature folder already exists: {feature_path}\n"
                "Delete it manually or choose a different name."
            )

        # Check 5: Valid scale level
        if not 0 <= scale_level <= 4:
            raise ValueError(
                f"Invalid scale_level: {scale_level}\n"
                "Must be 0-4 (0=chore, 1=bug, 2=small, 3=medium, 4=large)"
            )

        logger.info(
            "Pre-flight checks passed",
            name=name,
            scope=scope.value,
            scale_level=scale_level
        )

    def _rollback_feature_creation(
        self,
        name: str,
        feature_path: Optional[Path],
        feature: Optional[Feature],
        checkpoint: str
    ) -> None:
        """
        Rollback feature creation on error.

        Restores system to state before create_feature() was called.

        Args:
            name: Feature name
            feature_path: Path to created feature folder (if created)
            feature: Feature object (if inserted into DB)
            checkpoint: Git commit hash before operation
        """
        logger.warning("Rolling back feature creation", name=name)

        # Rollback 1: Delete feature folder (if created)
        if feature_path and feature_path.exists():
            logger.info("Deleting feature folder", path=str(feature_path))
            import shutil
            shutil.rmtree(feature_path)

        # Rollback 2: Delete from database (if inserted)
        if feature:
            logger.info("Deleting feature from database", name=name)
            self.state.feature_service.delete_feature(name)

        # Rollback 3: Reset git to checkpoint
        logger.info("Resetting git to checkpoint", checkpoint=checkpoint)
        self.git.reset_hard(checkpoint)

        logger.info("Rollback complete", name=name)
```

### Code Locations

**File to Modify:**
- `gao_dev/core/services/git_integrated_state_manager.py` (lines ~100-400)
  - Add create_feature() method
  - Add _pre_flight_checks_feature() helper
  - Add _rollback_feature_creation() helper
  - Update __init__() to accept DocumentStructureManager

**Files to Update (Initialization):**
- Anywhere GitIntegratedStateManager is instantiated (add doc_structure_manager parameter)

**Reference:**
- Epic 25: GitIntegratedStateManager.create_epic() (follow same pattern exactly)

### Dependencies

**Required Before Starting:**
- Story 32.1: FeatureStateService (COMPLETE)
- Story 32.2: StateCoordinator.create_feature() (COMPLETE)
- Story 33.1: DocumentStructureManager with auto_commit parameter (COMPLETE)

**Blocks:**
- Story 33.3: CLI create-feature command (uses this method)

### Integration Points

1. **DocumentStructureManager**: Called with auto_commit=false
2. **StateCoordinator**: create_feature() for DB insert
3. **GitManager**: Single commit at end, rollback on error
4. **DocumentLifecycleManager**: Already integrated via DocumentStructureManager

## Testing Requirements

### Unit Tests (50+ assertions)

**Location:** `tests/core/services/test_git_integrated_state_manager.py` (extend existing)

**Test Coverage:**

1. **Successful Creation (10 assertions)**
   - Feature folder created
   - Feature in database
   - Git commit exists
   - All files present (PRD, Architecture, README, QA/)
   - Feature metadata correct (name, scope, scale_level)
   - Feature path returned
   - Git history has single commit
   - Commit message follows conventional format
   - Working tree clean after creation

2. **Pre-Flight Check Failures (8 assertions)**
   - Dirty git tree raises ValueError
   - Invalid feature name (uppercase) raises ValueError
   - Invalid feature name (underscores) raises ValueError
   - Existing feature (DB) raises ValueError
   - Existing folder raises ValueError
   - Invalid scale_level (-1) raises ValueError
   - Invalid scale_level (5) raises ValueError
   - Error messages are helpful

3. **File Creation Failure (8 assertions)**
   - DocumentStructureManager error triggers rollback
   - Feature folder deleted
   - No DB record
   - No git commit
   - Working tree clean after rollback
   - RuntimeError raised
   - Structlog logged rollback

4. **DB Insert Failure (8 assertions)**
   - StateCoordinator error triggers rollback
   - Feature folder deleted
   - No DB record
   - No git commit
   - Working tree clean after rollback
   - RuntimeError raised

5. **Git Commit Failure (8 assertions)**
   - Git error triggers rollback
   - Feature folder deleted
   - DB record deleted
   - Git reset to checkpoint
   - Working tree clean after rollback
   - RuntimeError raised

6. **Rollback Verification (8 assertions)**
   - All rollback steps executed
   - System state restored
   - No orphaned files
   - No orphaned DB records
   - Git history unchanged
   - Structlog logged all rollback actions

### Integration Tests (15+ scenarios)

**Location:** `tests/integration/test_feature_creation_e2e.py`

**Test Scenarios:**

1. **End-to-End Feature Creation (5 scenarios)**
   - Create MVP feature
   - Create regular feature
   - Create feature with all optional parameters
   - Verify all files exist
   - Verify git history

2. **Concurrent Operations (3 scenarios)**
   - Create two features concurrently (different names)
   - Attempt duplicate creation (should fail)
   - Thread safety verification

3. **Error Recovery (4 scenarios)**
   - Disk full simulation (file creation fails)
   - DB constraint violation (DB insert fails)
   - Git failure simulation (commit fails)
   - All rollbacks successful

4. **Performance (3 scenarios)**
   - Feature creation <1s
   - Multiple features in sequence
   - Benchmark 10 feature creations

## Definition of Done

- [ ] create_feature() method implemented
- [ ] Atomic pattern followed (all-or-nothing)
- [ ] Pre-flight checks comprehensive
- [ ] Rollback logic verified
- [ ] 50+ unit test assertions passing
- [ ] 15+ integration test scenarios passing
- [ ] Performance target met (<1s)
- [ ] Code reviewed and approved
- [ ] No regressions in existing atomic operations
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging comprehensive

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 2 - Atomic Operations)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: GitIntegratedStateManager Extension)
- **Pattern Reference:** Epic 25 GitIntegratedStateManager.create_epic()
- **Atomic Pattern:** Epics 24-27 state management system
