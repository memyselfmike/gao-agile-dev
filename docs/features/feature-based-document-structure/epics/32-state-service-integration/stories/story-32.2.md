---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 32
  story: 2
  feature: "feature-based-document-structure"
  points: 2
---

# Story 32.2: Extend StateCoordinator (2 points)

**Epic:** 32 - State Service Integration
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **developer using state management**,
I want **FeatureStateService integrated into StateCoordinator as the 6th service facade**,
So that **I can access feature operations through the same consistent interface as epics, stories, and other entities**.

## Acceptance Criteria

### AC1: Add FeatureStateService to StateCoordinator
- [ ] Import FeatureStateService in `gao_dev/core/state/state_coordinator.py`
- [ ] Add `feature_service: FeatureStateService` to `__init__()` parameters
- [ ] Initialize feature_service alongside existing 5 services
- [ ] Follow exact pattern from Epic 24-27 (consistent initialization)

### AC2: Add Facade Methods
- [ ] `create_feature(name, scope, scale_level, description, owner)` - Wraps feature_service.create_feature()
- [ ] `get_feature(name)` - Wraps feature_service.get_feature()
- [ ] `list_features(scope, status)` - Wraps feature_service.list_features()
- [ ] `update_feature_status(name, status)` - Wraps feature_service.update_status()
- [ ] All methods delegate to feature_service (thin facade pattern)

### AC3: Add Comprehensive Query Method
- [ ] `get_feature_state(name)` - Returns complete feature state including:
  - Feature metadata (from features table)
  - All epics for this feature (from epics table using epics.feature column)
  - Epic summaries (epic number, title, status, story count)
  - Total story count across all epics
  - Feature completion percentage

### AC4: Maintain Consistency
- [ ] All facade methods follow same error handling as existing methods
- [ ] Structlog logging for all operations
- [ ] Type hints throughout
- [ ] Docstrings matching existing pattern

### AC5: Testing
- [ ] 15+ unit test assertions covering:
  - All facade methods delegate correctly
  - get_feature_state() returns complete data
  - Error handling (feature not found, etc.)
  - Integration with existing services (epics relationship)

## Technical Notes

### Implementation Approach

**Extend StateCoordinator (gao_dev/core/state/state_coordinator.py):**

```python
# Location: gao_dev/core/state/state_coordinator.py (lines ~50-200)

from gao_dev.core.state.feature_state_service import FeatureStateService, Feature, FeatureScope, FeatureStatus

class StateCoordinator:
    """
    Facade for all state services.

    Provides unified interface to:
    - EpicStateService (existing)
    - StoryStateService (existing)
    - ActionItemService (existing)
    - CeremonyService (existing)
    - LearningIndexService (existing)
    - FeatureStateService (NEW - 6th service)
    """

    def __init__(
        self,
        project_root: Path,
        epic_service: EpicStateService,
        story_service: StoryStateService,
        action_item_service: ActionItemService,
        ceremony_service: CeremonyService,
        learning_service: LearningIndexService,
        feature_service: FeatureStateService  # NEW
    ):
        self.project_root = project_root
        self.epic_service = epic_service
        self.story_service = story_service
        self.action_item_service = action_item_service
        self.ceremony_service = ceremony_service
        self.learning_service = learning_service
        self.feature_service = feature_service  # NEW

    # NEW: Feature facade methods

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Feature:
        """
        Create feature (facade to FeatureStateService).

        Args:
            name: Feature name (e.g., "user-auth", "mvp")
            scope: MVP or FEATURE
            scale_level: 0-4
            description: Optional description
            owner: Optional owner

        Returns:
            Feature object

        Raises:
            ValueError: If feature already exists
        """
        logger.info("Creating feature", name=name, scope=scope.value, scale_level=scale_level)
        return self.feature_service.create_feature(
            name=name,
            scope=scope,
            scale_level=scale_level,
            description=description,
            owner=owner
        )

    def get_feature(self, name: str) -> Optional[Feature]:
        """Get feature by name (facade)."""
        return self.feature_service.get_feature(name)

    def list_features(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[FeatureStatus] = None
    ) -> List[Feature]:
        """List features with optional filters (facade)."""
        return self.feature_service.list_features(scope=scope, status=status)

    def update_feature_status(self, name: str, status: FeatureStatus) -> bool:
        """Update feature status (facade)."""
        logger.info("Updating feature status", name=name, status=status.value)
        return self.feature_service.update_status(name=name, status=status)

    def get_feature_state(self, name: str) -> dict:
        """
        Get comprehensive feature state.

        Returns complete feature data including:
        - Feature metadata
        - All epics for this feature
        - Story counts
        - Completion metrics

        Args:
            name: Feature name

        Returns:
            Dictionary with:
                - feature: Feature object
                - epics: List of Epic objects for this feature
                - epic_summaries: List of {epic_num, title, status, story_count}
                - total_stories: Total story count across all epics
                - completion_pct: Percentage of stories complete

        Raises:
            ValueError: If feature not found
        """
        # Get feature metadata
        feature = self.feature_service.get_feature(name)
        if not feature:
            raise ValueError(f"Feature '{name}' not found")

        # Get all epics for this feature (using epics.feature column)
        # Note: epic_service.list_epics() should support feature_name filter
        # This may require minor enhancement to EpicStateService
        epics = self.epic_service.list_epics()  # Get all epics
        feature_epics = [e for e in epics if getattr(e, 'feature', None) == name]

        # Build epic summaries
        epic_summaries = []
        total_stories = 0
        completed_stories = 0

        for epic in feature_epics:
            stories = self.story_service.list_stories(epic_num=epic.epic_num)
            story_count = len(stories)
            completed_count = len([s for s in stories if s.status == "done"])

            epic_summaries.append({
                "epic_num": epic.epic_num,
                "title": epic.title,
                "status": epic.status,
                "story_count": story_count,
                "completed_count": completed_count
            })

            total_stories += story_count
            completed_stories += completed_count

        completion_pct = (completed_stories / total_stories * 100) if total_stories > 0 else 0

        return {
            "feature": feature,
            "epics": feature_epics,
            "epic_summaries": epic_summaries,
            "total_stories": total_stories,
            "completed_stories": completed_stories,
            "completion_pct": completion_pct
        }
```

### Code Locations

**File to Modify:**
- `gao_dev/core/state/state_coordinator.py` (lines ~50-200)
  - Add feature_service parameter to __init__()
  - Add 5 facade methods
  - Add get_feature_state() comprehensive query

**Files to Update (Initialization):**
- `gao_dev/core/services/git_integrated_state_manager.py` (lines ~40-60)
  - Instantiate FeatureStateService and pass to StateCoordinator
  - Follow pattern from Epic 25

**Reference:**
- `gao_dev/core/state/state_coordinator.py` (existing) - Follow facade pattern

### Dependencies

**Required Before Starting:**
- Story 32.1: FeatureStateService implementation (MUST BE COMPLETE)

**Blocks:**
- Story 33.2: GitIntegratedStateManager.create_feature() (needs StateCoordinator.create_feature())
- Story 33.3: CLI commands (needs StateCoordinator facade)

### Integration Points

1. **EpicStateService**: Query epics by feature (use epics.feature column)
2. **StoryStateService**: Count stories per epic for feature state
3. **GitIntegratedStateManager**: Will use StateCoordinator to create features atomically

### Minor Enhancement Needed

**EpicStateService.list_epics()** may need optional `feature_name` parameter:

```python
# In epic_state_service.py
def list_epics(self, feature_name: Optional[str] = None) -> List[Epic]:
    """List epics with optional feature filter."""
    query = "SELECT * FROM epics WHERE 1=1"
    params = []

    if feature_name:
        query += " AND feature = ?"
        params.append(feature_name)

    # ... execute query ...
```

This is a tiny addition (5 lines) and can be done in this story or Story 32.1.

## Testing Requirements

### Unit Tests (15+ assertions)

**Location:** `tests/core/state/test_state_coordinator.py` (extend existing)

**Test Coverage:**

1. **Facade Delegation (5 assertions)**
   - create_feature() calls feature_service.create_feature()
   - get_feature() calls feature_service.get_feature()
   - list_features() calls feature_service.list_features()
   - update_feature_status() calls feature_service.update_status()
   - All methods pass parameters correctly

2. **get_feature_state() Comprehensive Query (6 assertions)**
   - Returns feature metadata
   - Returns all epics for feature
   - Returns epic summaries with story counts
   - Calculates total_stories correctly
   - Calculates completion_pct correctly
   - Raises ValueError if feature not found

3. **Error Handling (4 assertions)**
   - get_feature() returns None for non-existent
   - update_feature_status() returns False for non-existent
   - get_feature_state() raises ValueError for non-existent
   - Logging occurs for all operations

## Definition of Done

- [ ] StateCoordinator has feature_service as 6th service
- [ ] All 5 facade methods implemented
- [ ] get_feature_state() returns comprehensive data
- [ ] 15+ unit test assertions passing
- [ ] GitIntegratedStateManager instantiates FeatureStateService
- [ ] Code reviewed and approved
- [ ] No regressions in existing StateCoordinator functionality
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging added

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 1)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: High-Level Architecture)
- **Pattern Reference:** Epic 24-27 StateCoordinator implementation
- **Database Schema:** `gao_dev/core/state/schema.sql` (line 13: epics.feature column)
