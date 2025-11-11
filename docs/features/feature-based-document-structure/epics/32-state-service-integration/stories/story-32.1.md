---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 32
  story: 1
  feature: "feature-based-document-structure"
  points: 3
---

# Story 32.1: Create FeatureStateService (3 points)

**Epic:** 32 - State Service Integration
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 3

## User Story

As a **system architect**,
I want **a FeatureStateService following the Epic 24-27 state service pattern**,
So that **feature metadata can be managed with thread-safe, <5ms CRUD operations integrated with StateCoordinator**.

## Acceptance Criteria

### AC1: FeatureStateService Implementation
- [ ] Create `gao_dev/core/state/feature_state_service.py` following Epic 24 pattern
- [ ] Implement thread-safe database connections (one per method call)
- [ ] All queries complete in <5ms (SQLite with indexes)
- [ ] Follow exact same pattern as EpicStateService, StoryStateService, etc.

### AC2: CRUD Operations
- [ ] `create_feature(name, scope, scale_level, description, owner)` - Insert feature record
- [ ] `get_feature(name)` - Retrieve feature by name
- [ ] `list_features(scope=None, status=None)` - Query with optional filters
- [ ] `update_status(name, status)` - Update feature status
- [ ] `delete_feature(name)` - Delete feature record (soft delete preferred)

### AC3: Data Model
- [ ] Create `FeatureScope` enum (MVP, FEATURE)
- [ ] Create `FeatureStatus` enum (PLANNING, ACTIVE, COMPLETE, ARCHIVED)
- [ ] Create `Feature` dataclass with all required fields
- [ ] Support metadata JSON field for extensibility

### AC4: Database Integration
- [ ] Use per-project database: `{project_root}/.gao-dev/documents.db`
- [ ] Create features table on first access (if not exists)
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Proper error handling with structlog logging

### AC5: Testing
- [ ] 30+ unit test assertions covering:
  - Thread safety (concurrent access)
  - CRUD operations (create, read, update, delete)
  - Query filtering (by scope, by status)
  - Error cases (duplicate name, not found, invalid status)
  - Performance (<5ms queries)

## Technical Notes

### Implementation Approach

**Follow Epic 24 Service Pattern:**

```python
# Location: gao_dev/core/state/feature_state_service.py

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class FeatureScope(Enum):
    """Feature scope: MVP or subsequent feature."""
    MVP = "mvp"
    FEATURE = "feature"


class FeatureStatus(Enum):
    """Feature lifecycle status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


@dataclass
class Feature:
    """Feature metadata model."""
    name: str
    scope: FeatureScope
    status: FeatureStatus
    scale_level: int  # 0-4
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    id: Optional[int] = None


class FeatureStateService:
    """
    Service for managing feature state in per-project database.

    Follows Epic 24-27 state service pattern:
    - Thread-safe (one connection per method call)
    - <5ms queries (indexed lookups)
    - Per-project isolation (.gao-dev/documents.db)
    - Consistent with other state services
    """

    def __init__(self, project_root: Path):
        """
        Initialize feature state service.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.db_path = project_root / ".gao-dev" / "documents.db"
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create features table if not exists."""
        # Note: Migration script (Story 34.1) will handle this properly
        # This is just for safety during development
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
                    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
                    scale_level INTEGER NOT NULL,
                    description TEXT,
                    owner TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    metadata JSON
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scope ON features(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_status ON features(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scale_level ON features(scale_level)")

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Feature:
        """
        Create feature record.

        Args:
            name: Feature name (e.g., "user-auth", "mvp")
            scope: MVP or FEATURE
            scale_level: 0-4
            description: Optional description
            owner: Optional owner

        Returns:
            Feature object with assigned ID

        Raises:
            ValueError: If feature already exists or invalid parameters
        """
        # Implementation here...

    def get_feature(self, name: str) -> Optional[Feature]:
        """Get feature by name."""
        # Implementation here...

    def list_features(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[FeatureStatus] = None
    ) -> List[Feature]:
        """List features with optional filters."""
        # Implementation here...

    def update_status(self, name: str, status: FeatureStatus) -> bool:
        """Update feature status."""
        # Implementation here...

    def delete_feature(self, name: str) -> bool:
        """Delete feature (soft delete if possible)."""
        # Implementation here...
```

### Code Locations

**New File:**
- `gao_dev/core/state/feature_state_service.py` (create new)

**Reference Implementations:**
- `gao_dev/core/state/epic_state_service.py` (lines 1-250) - Follow this pattern exactly
- `gao_dev/core/state/story_state_service.py` (lines 1-300) - Similar CRUD operations
- `gao_dev/core/state/schema.sql` (line 13) - Note `epics.feature` column already exists

### Dependencies

**Required Before Starting:**
- Epic 24-27: State management system (COMPLETE)
- Database schema with epics.feature column (COMPLETE)

**Blocks:**
- Story 32.2: StateCoordinator extension (needs FeatureStateService)
- Story 33.2: GitIntegratedStateManager extension (needs service via StateCoordinator)

### Integration Points

1. **Database Schema**: Features table in per-project `.gao-dev/documents.db`
2. **Epics Table**: Will link via `epics.feature = features.name` foreign key relationship
3. **StateCoordinator**: Will be added as 6th service in Story 32.2

## Testing Requirements

### Unit Tests (30+ assertions)

**Location:** `tests/core/state/test_feature_state_service.py`

**Test Coverage:**

1. **Basic CRUD (10 assertions)**
   - Create feature with valid data
   - Get feature by name
   - List all features
   - Update feature status
   - Delete feature

2. **Query Filtering (8 assertions)**
   - List features by scope (MVP only)
   - List features by scope (FEATURE only)
   - List features by status (PLANNING)
   - List features by status (ACTIVE)
   - List features by combined scope + status
   - List all features (no filter)

3. **Error Cases (8 assertions)**
   - Create duplicate feature (should fail)
   - Get non-existent feature (returns None)
   - Update non-existent feature (returns False)
   - Delete non-existent feature (returns False)
   - Invalid scope value (should reject)
   - Invalid status value (should reject)
   - Invalid scale_level (negative or >4)

4. **Performance (2 assertions)**
   - Create feature <5ms
   - Query feature <5ms

5. **Thread Safety (2 assertions)**
   - Concurrent creates (different names)
   - Concurrent updates (same feature)

## Definition of Done

- [ ] FeatureStateService implemented following Epic 24 pattern
- [ ] All 5 CRUD methods working
- [ ] 30+ unit test assertions passing
- [ ] Performance targets met (<5ms queries)
- [ ] Thread-safe implementation verified
- [ ] Code reviewed and approved
- [ ] No regressions in existing state services
- [ ] Structlog logging added for all operations
- [ ] Type hints throughout (mypy passes)

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic Breakdown - Epic 1)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Component 1 - FeatureStateService)
- **Pattern Reference:** Epic 24 State Service Implementation
- **Database Schema:** `gao_dev/core/state/schema.sql`
