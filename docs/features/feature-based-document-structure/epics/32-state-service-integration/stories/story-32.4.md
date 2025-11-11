---
document:
  type: "story"
  state: "complete"
  created: "2025-11-11"
  completed: "2025-11-11"
  epic: 32
  story: 4
  feature: "feature-based-document-structure"
  points: 3
---

# Story 32.4: Create FeaturePathResolver (3 points)

**Epic:** 32 - State Service Integration
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 3

## User Story

As a **workflow executor**,
I want **a FeaturePathResolver with 6-level priority resolution and WorkflowContext integration**,
So that **feature names can be intelligently auto-detected and all feature-scoped paths can be generated with co-located epic-story structure**.

## Acceptance Criteria

### AC1: FeaturePathResolver Implementation
- [x] Create `gao_dev/core/services/feature_path_resolver.py`
- [x] Implement 6-level priority resolution for feature_name
- [x] Integrate with WorkflowContext.metadata.feature_name
- [x] Generate all path types (PRD, epic, story, QA, etc.) with co-located structure

### AC2: Six-Level Priority Resolution
- [x] **Priority 1**: Explicit parameter (`params["feature_name"]`)
- [x] **Priority 2**: WorkflowContext (`context.metadata.get("feature_name")`)
- [x] **Priority 3**: Current working directory (if in feature folder)
- [x] **Priority 4**: Single feature detection (if only one besides mvp)
- [x] **Priority 5**: MVP detection (if mvp exists and no other features)
- [x] **Priority 6**: Error with helpful message (if ambiguous)

### AC3: Path Generation Methods
- [x] `resolve_feature_name(params, context)` - Returns feature name using 6-level priority
- [x] `generate_feature_path(feature_name, path_type, **kwargs)` - Generates specific path
- [x] Support all path types:
  - Feature-level: prd, architecture, readme, epics_overview
  - Folders: qa_folder, retrospectives_folder
  - Epic-level: epic_folder, epic_location
  - Story-level: story_folder, story_location, context_xml_folder
  - Ceremonies: retrospective_location, standup_location

### AC4: Co-Located Path Templates
- [x] Epic paths: `docs/features/{feature}/epics/{epic}-{epic_name}/`
- [x] Story paths: `docs/features/{feature}/epics/{epic}-{epic_name}/stories/`
- [x] Context XML: `docs/features/{feature}/epics/{epic}-{epic_name}/context/`
- [x] All paths follow co-located structure (epics contain their stories)

### AC5: Error Handling
- [x] Clear error messages when feature_name cannot be resolved
- [x] List available features in error message
- [x] Suggest solutions (use --feature-name or cd to feature directory)
- [x] Validate feature exists in registry before resolving

### AC6: Testing
- [x] 40+ unit test assertions covering:
  - All 6 priority levels
  - WorkflowContext integration
  - All path type generation
  - Error cases (ambiguous, not found)
  - Cross-platform paths

## Technical Notes

### Implementation Approach

**FeaturePathResolver with Context Integration:**

```python
# Location: gao_dev/core/services/feature_path_resolver.py

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from gao_dev.core.state.feature_state_service import FeatureStateService
from gao_dev.core.workflow_executor import WorkflowContext  # Import for type hints

logger = structlog.get_logger(__name__)


class FeaturePathResolver:
    """
    Resolve feature names and generate feature-scoped paths.

    Integrates with WorkflowExecutor to provide feature_name
    variable resolution with intelligent auto-detection.

    Features:
    - 6-level priority resolution
    - WorkflowContext integration (context.metadata.feature_name)
    - Co-located epic-story path generation
    - Comprehensive error messages
    """

    def __init__(
        self,
        project_root: Path,
        feature_service: FeatureStateService
    ):
        """
        Initialize feature path resolver.

        Args:
            project_root: Project root directory
            feature_service: FeatureStateService for querying available features
        """
        self.project_root = project_root
        self.features_dir = project_root / "docs" / "features"
        self.feature_service = feature_service

    def resolve_feature_name(
        self,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None
    ) -> str:
        """
        Resolve feature name from multiple sources.

        Priority (highest to lowest):
        1. Explicit parameter: params["feature_name"]
        2. WorkflowContext: context.metadata.get("feature_name")
        3. Current working directory (if in feature folder)
        4. Single feature detection (if only one besides mvp)
        5. MVP detection (if mvp exists and no other features)
        6. Error (if ambiguous)

        Args:
            params: Workflow parameters
            context: Optional WorkflowContext

        Returns:
            Feature name (e.g., "mvp", "user-auth")

        Raises:
            ValueError: If feature_name cannot be resolved (with helpful message)

        Examples:
            # Priority 1: Explicit parameter
            >>> resolve_feature_name({"feature_name": "user-auth"}, None)
            "user-auth"

            # Priority 2: WorkflowContext
            >>> ctx = WorkflowContext(metadata={"feature_name": "mvp"})
            >>> resolve_feature_name({}, ctx)
            "mvp"

            # Priority 3: CWD in feature folder
            >>> os.chdir("docs/features/user-auth")
            >>> resolve_feature_name({}, None)
            "user-auth"

            # Priority 4: Single feature
            >>> # Only "user-auth" exists (besides mvp)
            >>> resolve_feature_name({}, None)
            "user-auth"

            # Priority 6: Error (multiple features)
            >>> # Both "user-auth" and "payment" exist
            >>> resolve_feature_name({}, None)
            ValueError: Cannot resolve feature_name. Multiple features exist: ...
        """
        # Priority 1: Explicit parameter (highest priority)
        if "feature_name" in params:
            name = params["feature_name"]
            feature = self.feature_service.get_feature(name)
            if not feature:
                available = self._list_feature_names()
                raise ValueError(
                    f"Feature '{name}' does not exist.\n"
                    f"Available features: {', '.join(available)}\n\n"
                    f"Create it with: gao-dev create-feature {name}"
                )
            return name

        # Priority 2: WorkflowContext (NEW!)
        if context and context.metadata.get("feature_name"):
            return context.metadata["feature_name"]

        # Priority 3: Current working directory
        cwd = Path.cwd()
        if cwd.is_relative_to(self.features_dir):
            relative = cwd.relative_to(self.features_dir)
            if relative.parts:
                feature_name = relative.parts[0]
                feature = self.feature_service.get_feature(feature_name)
                if feature:
                    logger.info(
                        "Resolved feature_name from cwd",
                        feature_name=feature_name
                    )
                    return feature_name

        # Priority 4: Single feature detection (exclude MVP)
        features = self._list_feature_names(exclude_mvp=True)
        if len(features) == 1:
            logger.info(
                "Resolved feature_name (single feature)",
                feature_name=features[0]
            )
            return features[0]

        # Priority 5: MVP detection
        mvp_exists = self.feature_service.get_feature("mvp") is not None
        if mvp_exists and len(features) == 0:
            logger.info("Resolved feature_name to mvp (only feature)")
            return "mvp"

        # Priority 6: Error (ambiguous)
        all_features = self._list_feature_names()
        raise ValueError(
            "Cannot resolve feature_name. Multiple features exist:\n"
            f"  {', '.join(all_features)}\n\n"
            "Please specify explicitly:\n"
            f"  --feature-name <name>\n\n"
            "Or run from feature directory:\n"
            f"  cd docs/features/<name> && gao-dev <command>\n\n"
            "Available features:\n" +
            "\n".join(f"  - {name}" for name in all_features)
        )

    def generate_feature_path(
        self,
        feature_name: str,
        path_type: str,
        epic: Optional[str] = None,
        epic_name: Optional[str] = None,
        story: Optional[str] = None
    ) -> Path:
        """
        Generate feature-scoped path using co-located structure.

        Args:
            feature_name: Feature name (e.g., "user-auth", "mvp")
            path_type: Path type identifier
            epic: Epic number (e.g., "1")
            epic_name: Epic name (e.g., "foundation")
            story: Story number (e.g., "2")

        Returns:
            Path relative to project root

        Supported path_types:
            Feature-level documents:
            - prd: docs/features/{feature}/PRD.md
            - architecture: docs/features/{feature}/ARCHITECTURE.md
            - readme: docs/features/{feature}/README.md
            - epics_overview: docs/features/{feature}/EPICS.md

            Feature-level folders:
            - qa_folder: docs/features/{feature}/QA
            - retrospectives_folder: docs/features/{feature}/retrospectives

            Epic-level (co-located with stories!):
            - epic_folder: docs/features/{feature}/epics/{epic}-{epic_name}
            - epic_location: docs/features/{feature}/epics/{epic}-{epic_name}/README.md

            Story-level (inside epic folder!):
            - story_folder: docs/features/{feature}/epics/{epic}-{epic_name}/stories
            - story_location: docs/features/{feature}/epics/{epic}-{epic_name}/stories/story-{epic}.{story}.md
            - context_xml_folder: docs/features/{feature}/epics/{epic}-{epic_name}/context

            Ceremony artifacts:
            - retrospective_location: docs/features/{feature}/retrospectives/epic-{epic}-retro.md
            - standup_location: docs/features/{feature}/standups/standup-{date}.md

        Examples:
            >>> generate_feature_path("user-auth", "prd")
            Path("docs/features/user-auth/PRD.md")

            >>> generate_feature_path("mvp", "epic_location", epic="1", epic_name="foundation")
            Path("docs/features/mvp/epics/1-foundation/README.md")

            >>> generate_feature_path("user-auth", "story_location",
            ...                      epic="2", epic_name="oauth", story="3")
            Path("docs/features/user-auth/epics/2-oauth/stories/story-2.3.md")

        Raises:
            ValueError: If path_type is unknown
        """
        # Co-located path templates (v3.0)
        templates = {
            # Feature-level documents
            "prd": "docs/features/{feature_name}/PRD.md",
            "architecture": "docs/features/{feature_name}/ARCHITECTURE.md",
            "readme": "docs/features/{feature_name}/README.md",
            "epics_overview": "docs/features/{feature_name}/EPICS.md",

            # Feature-level folders
            "qa_folder": "docs/features/{feature_name}/QA",
            "retrospectives_folder": "docs/features/{feature_name}/retrospectives",

            # Epic-level (CO-LOCATED with stories!)
            "epic_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}",
            "epic_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/README.md",

            # Story-level (INSIDE epic folder!)
            "story_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories",
            "story_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories/story-{epic}.{story}.md",
            "context_xml_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/context",

            # Ceremony artifacts
            "retrospective_location": "docs/features/{feature_name}/retrospectives/epic-{epic}-retro.md",
            "standup_location": "docs/features/{feature_name}/standups/standup-{date}.md",

            # Legacy (for backward compatibility)
            "feature_dir": "docs/features/{feature_name}"
        }

        template = templates.get(path_type)
        if not template:
            raise ValueError(
                f"Unknown path_type: '{path_type}'\n\n"
                f"Supported types: {', '.join(templates.keys())}"
            )

        # Generate path from template
        path_str = template.format(
            feature_name=feature_name,
            epic=epic or "",
            epic_name=epic_name or "",
            story=story or "",
            date=datetime.now().strftime("%Y-%m-%d")
        )

        return Path(path_str)

    def _list_feature_names(self, exclude_mvp: bool = False) -> list[str]:
        """List all feature names (helper method)."""
        features = self.feature_service.list_features()
        names = [f.name for f in features]

        if exclude_mvp:
            names = [n for n in names if n != "mvp"]

        return sorted(names)
```

### Code Locations

**New File:**
- `gao_dev/core/services/feature_path_resolver.py` (create new)

**Files That Will Use This:**
- `gao_dev/core/workflow_executor.py` (Story 34.3 integration)
- CLI commands (Story 33.3)

### Dependencies

**Required Before Starting:**
- Story 32.1: FeatureStateService (needs to query features)
- Epic 18: WorkflowContext (already exists)

**Blocks:**
- Story 34.3: WorkflowExecutor integration (uses resolver)
- Story 34.2: defaults.yaml updates (uses path templates)

### Integration Points

1. **WorkflowContext**: Accesses `context.metadata.get("feature_name")`
2. **FeatureStateService**: Queries available features
3. **WorkflowExecutor**: Will call `resolve_feature_name()` in variable resolution

## Testing Requirements

### Unit Tests (40+ assertions)

**Location:** `tests/core/services/test_feature_path_resolver.py`

**Test Coverage:**

1. **resolve_feature_name() - Priority Levels (12 assertions)**
   - Priority 1: Explicit parameter (valid feature)
   - Priority 1: Explicit parameter (invalid feature raises error)
   - Priority 2: WorkflowContext.metadata["feature_name"]
   - Priority 2: Context takes precedence over CWD
   - Priority 3: CWD in feature folder
   - Priority 3: CWD not in feature folder (skips to next priority)
   - Priority 4: Single feature detection
   - Priority 4: Multiple features (skips to error)
   - Priority 5: MVP detection (only feature)
   - Priority 5: MVP + other features (skips to error)
   - Priority 6: Error with helpful message
   - Priority 6: Error lists available features

2. **generate_feature_path() - Feature-Level (8 assertions)**
   - PRD path
   - Architecture path
   - README path
   - EPICS overview path
   - QA folder path
   - Retrospectives folder path
   - Feature directory path
   - Unknown path_type raises error

3. **generate_feature_path() - Epic-Level (6 assertions)**
   - Epic folder path (co-located)
   - Epic location (README.md)
   - Epic with number and name
   - Multiple epics in same feature
   - Context XML folder

4. **generate_feature_path() - Story-Level (6 assertions)**
   - Story folder path (inside epic)
   - Story location (story-X.Y.md)
   - Story with epic number and name
   - Multiple stories in same epic
   - Story numbering (1.1, 1.2, 2.1, etc.)

5. **generate_feature_path() - Ceremonies (4 assertions)**
   - Retrospective location
   - Standup location (with date)
   - Date formatting

6. **Error Handling (4 assertions)**
   - Feature not found
   - Ambiguous resolution (multiple features)
   - Invalid path_type
   - Error messages are helpful

## Definition of Done

- [ ] FeaturePathResolver implemented with all methods
- [ ] 6-level priority resolution working
- [ ] WorkflowContext integration functional
- [ ] All path types supported (15+ types)
- [ ] Co-located epic-story paths generated correctly
- [ ] 40+ unit test assertions passing
- [ ] Clear error messages with solutions
- [ ] Code reviewed and approved
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging for resolution decisions

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 2 - Path Resolution)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Component 4 - FeaturePathResolver)
- **WorkflowContext:** Epic 18 implementation
- **Variable Resolution:** Epic 18 WorkflowExecutor
