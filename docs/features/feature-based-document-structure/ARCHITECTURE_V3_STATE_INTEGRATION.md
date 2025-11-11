# ARCHITECTURE v3.0 - State Management Integration

**Date:** 2025-11-11
**Status:** Post-State Management Integration Review
**Relates to:** ARCHITECTURE.md v2.0

---

## Executive Summary

After reviewing the existing state management system (Epics 24-27), we discovered that:

1. **The schema ALREADY has `epics.feature TEXT` column** (line 13 of `gao_dev/core/state/schema.sql`)
2. **GitIntegratedStateManager pattern exists** and provides atomic file + DB + git operations
3. **5 state services already exist** following a proven pattern

**Decision:** Instead of creating a standalone FeatureRegistry, we should create **FeatureStateService as the 6th state service** and use **GitIntegratedStateManager for atomic operations**.

---

## Key Changes from v2.0 to v3.0

| Aspect | v2.0 (SUPERSEDED) | v3.0 (APPROVED) |
|--------|-------------------|-----------------|
| **Feature metadata** | FeatureRegistry (standalone) | FeatureStateService (6th service) |
| **Atomicity** | DocumentStructureManager + FeatureRegistry (non-atomic) | GitIntegratedStateManager.create_feature() (atomic) |
| **Pattern** | New standalone pattern | Follows Epic 24-27 service pattern |
| **StateCoordinator** | Not integrated | Add feature_service facade |
| **DocumentStructureManager** | Standalone with git commit | Helper with auto_commit parameter |
| **Epic numbering** | Epic 1-3 | Epic 32-34 (after Epic 31) |

---

## v3.0 Architecture Overview

```
CLI Commands
    ↓
GitIntegratedStateManager.create_feature()  ← NEW METHOD (atomic)
    ├─ Pre-check: git clean
    ├─ DocumentStructureManager.initialize_feature_folder(auto_commit=false)  ← HELPER
    ├─ StateCoordinator.create_feature()  ← Uses FeatureStateService
    ├─ Git commit
    └─ Rollback on error (file + DB + git)
```

---

## Component Updates

### 1. FeatureStateService (NEW - 6th Service)

**Location:** `gao_dev/core/services/feature_state_service.py`

**Follows EXACT pattern of:**
- `epic_state_service.py`
- `story_state_service.py`
- `action_item_service.py`
- `ceremony_service.py`
- `learning_index_service.py`

**Interface:**
```python
class FeatureStateService:
    """
    Service for feature state management.

    Follows Epic 24 service pattern: thread-safe, <5ms queries, DB CRUD only.
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._local = threading.local()

    @contextmanager
    def _get_connection(self):
        """Get thread-local connection (Epic 24 pattern)."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(...)
            self._local.conn.row_factory = sqlite3.Row
        yield self._local.conn

    def create(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        status: str = "planning",
        description: Optional[str] = None,
        owner: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create feature record in database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO features (name, scope, scale_level, status,
                                    description, owner, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, scope.value, scale_level, status,
                 description, owner, datetime.now().isoformat(),
                 json.dumps(metadata or {}))
            )
            return self.get(name)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get feature by name (fast lookup, <5ms)."""

    def list(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List features with optional filters."""

    def update_status(self, name: str, status: str) -> bool:
        """Update feature status."""

    def delete(self, name: str) -> bool:
        """Delete feature (soft delete - set status to archived)."""
```

**Why this is right:**
- ✅ Consistent with all other services
- ✅ Thread-safe (thread-local connections)
- ✅ Fast queries (<5ms with indexes)
- ✅ Database CRUD only (single responsibility)

---

### 2. StateCoordinator Extension (MODIFY)

**Location:** `gao_dev/core/state_coordinator.py`

**Add:**
```python
class StateCoordinator:
    def __init__(self, db_path: Path):
        # Existing 5 services
        self.epic_service = EpicStateService(db_path)
        self.story_service = StoryStateService(db_path)
        self.action_service = ActionItemService(db_path)
        self.ceremony_service = CeremonyService(db_path)
        self.learning_service = LearningIndexService(db_path)

        # NEW: 6th service
        self.feature_service = FeatureStateService(db_path)

    # NEW: Feature facade methods
    def create_feature(self, ...):
        return self.feature_service.create(...)

    def get_feature(self, name: str):
        return self.feature_service.get(name)

    def list_features(self, scope=None, status=None):
        return self.feature_service.list(scope, status)

    def update_feature_status(self, name, status):
        return self.feature_service.update_status(name, status)

    # NEW: Comprehensive feature state query
    def get_feature_state(self, feature_name: str) -> Dict[str, Any]:
        """
        Get feature + all epics + all stories for this feature.

        Returns:
            {
                "feature": {...},
                "epics": [{...}, {...}],
                "stories": [{...}, {...}]
            }
        """
        feature = self.feature_service.get(feature_name)
        epics = self.epic_service.list_by_feature(feature_name)  # NEW query
        stories = []
        for epic in epics:
            stories.extend(self.story_service.list_by_epic(epic["epic_num"]))

        return {
            "feature": feature,
            "epics": epics,
            "stories": stories
        }
```

**Why this is right:**
- ✅ StateCoordinator becomes complete facade (6 services)
- ✅ Follows existing pattern exactly
- ✅ Provides comprehensive state queries

---

### 3. GitIntegratedStateManager Extension (MODIFY)

**Location:** `gao_dev/core/services/git_integrated_state_manager.py`

**Add:**
```python
class GitIntegratedStateManager:
    def __init__(self, db_path: Path, project_path: Path):
        self.coordinator = StateCoordinator(db_path)
        self.git_manager = GitManager(project_path)

        # NEW: DocumentStructureManager as helper
        self.doc_structure_manager = DocumentStructureManager(
            project_root=project_path,
            git_manager=self.git_manager,
            lifecycle_manager=DocumentLifecycleManager(...)
        )

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create feature with ATOMIC file + DB + git operation.

        This operation is ATOMIC:
        1. Pre-check: git working tree must be clean
        2. Create folder structure (via DocumentStructureManager)
        3. Insert feature record (via StateCoordinator)
        4. Git add + commit
        5. On error: rollback DB + git reset --hard

        Args:
            name: Feature name (kebab-case, e.g., "user-auth", "mvp")
            scope: FeatureScope.MVP or FeatureScope.FEATURE
            scale_level: 0-4 (determines folder complexity)
            description: Optional description
            owner: Optional owner
            commit_message: Custom git commit message (optional)

        Returns:
            Created feature record from database

        Raises:
            WorkingTreeDirtyError: If git working tree has uncommitted changes
            GitIntegratedStateManagerError: If operation fails

        Example:
            ```python
            feature = manager.create_feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                scale_level=3,
                description="User authentication system",
                owner="John"
            )
            # Result:
            # - docs/features/user-auth/ created with full structure
            # - features table row inserted
            # - Git commit: "feat(user-auth): initialize feature feature"
            ```
        """
        self.logger.info(
            "creating_feature",
            name=name,
            scope=scope.value,
            scale_level=scale_level
        )

        # Pre-flight check: working tree must be clean
        if not self.git_manager.is_working_tree_clean():
            raise WorkingTreeDirtyError(
                "Git working tree has uncommitted changes. "
                "Commit or stash changes before creating feature."
            )

        # Save checkpoint (current HEAD SHA)
        checkpoint_sha = self.git_manager.get_head_sha()

        try:
            # Step 1: Create folder structure (delegate to helper)
            # IMPORTANT: auto_commit=False (we commit at the end)
            feature_path = self.doc_structure_manager.initialize_feature_folder(
                feature_name=name,
                scale_level=ScaleLevel(scale_level),
                description=description,
                auto_commit=False  # ← CRITICAL! Don't commit yet
            )

            self.logger.debug(
                "feature_folders_created",
                path=str(feature_path)
            )

            # Step 2: Insert into database
            feature = self.coordinator.create_feature(
                name=name,
                scope=scope,
                scale_level=scale_level,
                status="planning",
                description=description,
                owner=owner,
                metadata={
                    "folder_path": str(feature_path)
                }
            )

            self.logger.debug(
                "feature_database_record_created",
                feature_id=feature["id"]
            )

            # Step 3: Atomic git commit (if auto-commit enabled)
            if self.auto_commit:
                message = commit_message or (
                    f"feat({name}): initialize {scope.value} feature\n\n"
                    f"Scale level: {scale_level}\n"
                    f"Structure: PRD, ARCHITECTURE, README, epics/, stories/, QA/\n\n"
                    f"🤖 Generated with [GAO-Dev](https://github.com/gao-dev)"
                )

                self.git_manager.add_all()
                commit_sha = self.git_manager.commit(message)

                self.logger.info(
                    "feature_created_with_commit",
                    name=name,
                    commit_sha=commit_sha,
                    feature_id=feature["id"]
                )

            return feature

        except Exception as e:
            # Atomic rollback: DB + git
            self.logger.error(
                "feature_creation_failed",
                name=name,
                error=str(e)
            )

            # Rollback git (hard reset to checkpoint)
            self.git_manager.reset_hard(checkpoint_sha)

            # Rollback database
            self.coordinator.rollback()

            raise GitIntegratedStateManagerError(
                f"Feature creation failed: {e}. "
                f"All changes rolled back (files + DB + git)."
            ) from e
```

**Why this is right:**
- ✅ Follows EXACT same pattern as create_epic(), create_story()
- ✅ Atomic operations (file + DB + git)
- ✅ Auto-rollback on errors
- ✅ DocumentStructureManager becomes helper (called with auto_commit=false)

---

### 4. DocumentStructureManager Extension (MODIFY)

**Location:** `gao_dev/core/services/document_structure_manager.py`

**Modify:**
```python
class DocumentStructureManager:
    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel,
        description: Optional[str] = None,
        auto_commit: bool = True  # ← NEW PARAMETER
    ) -> Path:
        """
        Create feature folder structure.

        Args:
            feature_name: Feature name (e.g., "user-auth", "mvp")
            scale_level: ScaleLevel enum (0-4)
            description: Optional description
            auto_commit: Whether to git commit after creation (default: True)
                        Set to False when called by GitIntegratedStateManager

        Returns:
            Path to created feature folder
        """
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=False)

        # Create existing files
        self._create_file(feature_path / "PRD.md", self._prd_template(...))
        self._create_file(feature_path / "ARCHITECTURE.md", self._arch_template(...))
        (feature_path / "stories").mkdir()
        (feature_path / "epics").mkdir()

        # NEW: QA/ folder (always create)
        (feature_path / "QA").mkdir()

        # NEW: README.md (generate from template)
        readme_content = self._readme_template(feature_name, description)
        self._create_file(feature_path / "README.md", readme_content)

        # Scale-level folders
        if scale_level >= ScaleLevel.LEVEL_3:
            (feature_path / "retrospectives").mkdir()

        if scale_level == ScaleLevel.LEVEL_4:
            (feature_path / "ceremonies").mkdir()

        # Register with lifecycle manager
        self.lifecycle.register_document(...)

        # Git commit (CONDITIONAL - NEW!)
        if auto_commit:
            self.git.add_all()
            self.git.commit(f"docs({feature_name}): initialize feature folder")
        # else: Caller will handle commit (e.g., GitIntegratedStateManager)

        return feature_path
```

**Why this is right:**
- ✅ Minimal changes (add QA/, README, auto_commit parameter)
- ✅ Backward compatible (auto_commit=True by default)
- ✅ Becomes helper when auto_commit=False

---

## Database Schema Updates

**Location:** `gao_dev/core/state/schema.sql`

**Add after existing tables:**

```sql
-- Features table (NEW - per-project!)
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
    scale_level INTEGER NOT NULL CHECK(scale_level >= 0 AND scale_level <= 4),
    description TEXT,
    owner TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata JSON
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_features_scope ON features(scope);
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_features_scale_level ON features(scale_level);
CREATE INDEX IF NOT EXISTS idx_features_name ON features(name);

-- Trigger for updating features timestamp
CREATE TRIGGER IF NOT EXISTS update_feature_timestamp
AFTER UPDATE ON features
FOR EACH ROW
BEGIN
    UPDATE features SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger for logging feature status changes (audit trail)
CREATE TRIGGER IF NOT EXISTS log_feature_status_change
AFTER UPDATE OF status ON features
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('features', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;

-- FUTURE: Foreign key constraint on epics.feature
-- The epics.feature column ALREADY EXISTS (line 13)!
-- After full migration, add constraint:
-- ALTER TABLE epics ADD CONSTRAINT fk_epics_feature
--   FOREIGN KEY (feature) REFERENCES features(name)
--   ON DELETE SET NULL
--   ON UPDATE CASCADE;
```

---

## Revised Epic Breakdown (Epic 32-34)

**Total: 3 epics, 11 stories, 25 points, 2 weeks**

### Epic 32: State Service Integration (Week 1) - 10 points

**Story 32.1: Create FeatureStateService (3 pts)**
- Implement FeatureStateService following Epic 24 pattern
- Thread-safe connections, <5ms queries
- CRUD operations: create, get, list, update_status, delete
- Unit tests (30+ assertions)

**Story 32.2: Extend StateCoordinator (2 pts)**
- Add feature_service to StateCoordinator.__init__()
- Add facade methods: create_feature, get_feature, list_features
- Add get_feature_state() comprehensive query
- Unit tests (15+ assertions)

**Story 32.3: Create FeaturePathValidator (2 pts)**
- Implement stateless validator (pure functions)
- validate_feature_path(), extract_feature_from_path(), validate_structure()
- Unit tests (25+ assertions)

**Story 32.4: Create FeaturePathResolver (3 pts)**
- Implement resolver with 6-level priority
- WorkflowContext integration (metadata.feature_name)
- Co-located path generation
- Unit tests (40+ assertions)

### Epic 33: Atomic Feature Operations (Week 1.5) - 8 points

**Story 33.1: Extend DocumentStructureManager (2 pts)**
- Add QA/ folder creation
- Add README.md generation with template
- Add auto_commit parameter (default: true, backward compatible)
- Unit tests (20+ assertions)

**Story 33.2: Extend GitIntegratedStateManager (4 pts)**
- Add create_feature() method following atomic pattern
- Pre-flight checks, checkpoint, rollback logic
- Integrate DocumentStructureManager (auto_commit=false) + StateCoordinator
- Unit tests (50+ assertions)
- Integration tests (15+ scenarios)

**Story 33.3: CLI Commands (2 pts)**
- create-feature command (wraps GitIntegratedStateManager)
- list-features command (wraps StateCoordinator)
- validate-structure command (wraps FeaturePathValidator)
- CLI tests (20+ scenarios)

### Epic 34: Integration & Variables (Week 2) - 7 points

**Story 34.1: Schema Migration (2 pts)**
- Create migration script for features table
- Add triggers for timestamps and audit trail
- Migration tests (validate existing DB schemas)
- Documentation

**Story 34.2: Update defaults.yaml (2 pts)**
- Replace all paths with co-located structure
- Update variable defaults (feature_name, epic_folder, story_location, etc.)
- Validation tests

**Story 34.3: WorkflowExecutor Integration (2 pts)**
- Extend resolve_variables() to use FeaturePathResolver
- Pass WorkflowContext to resolver
- Fallback logic for legacy paths
- Integration tests (15+ cases)

**Story 34.4: Testing & Documentation (1 pt)**
- End-to-end tests (greenfield, feature creation, validation)
- Update CLAUDE.md with new commands
- Migration guide for existing features
- CLI help text updates

---

## Summary: v2.0 → v3.0 Changes

**Architectural Shift:**
- v2.0: Standalone FeatureRegistry + DocumentStructureManager
- v3.0: FeatureStateService (6th service) + GitIntegratedStateManager (atomic)

**Key Benefits:**
1. ✅ **Consistency**: Follows proven Epic 24-27 patterns
2. ✅ **Atomicity**: File + DB + git guaranteed atomic or rollback
3. ✅ **Integration**: Leverages existing infrastructure (StateCoordinator, GitIntegratedStateManager)
4. ✅ **Performance**: <5ms queries, thread-safe, indexed
5. ✅ **Single Responsibility**: Each component has clear, focused responsibility

**Migration from v2.0:**
- All v2.0 concepts remain valid (co-located structure, stateless validator, WorkflowContext integration)
- Implementation shifts to use state service pattern
- Epic numbering updated to 32-34 (after Epic 31 - Mary Integration)

---

*End of v3.0 State Integration Summary*
