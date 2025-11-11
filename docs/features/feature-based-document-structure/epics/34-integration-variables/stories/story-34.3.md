---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 34
  story: 3
  feature: "feature-based-document-structure"
  points: 2
---

# Story 34.3: WorkflowExecutor Integration (2 points)

**Epic:** 34 - Integration & Variables
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **WorkflowExecutor (Epic 18 component)**,
I want **to use FeaturePathResolver for feature_name resolution and pass WorkflowContext to all resolvers**,
So that **feature names auto-detect intelligently and all workflows create files in correct feature-scoped locations**.

## Acceptance Criteria

### AC1: Extend resolve_variables() Method
- [ ] Add FeaturePathResolver to WorkflowExecutor dependencies
- [ ] Integrate resolver into resolve_variables() method
- [ ] Pass WorkflowContext to resolver (enables context.metadata.feature_name)
- [ ] Resolve feature_name using 6-level priority
- [ ] Use resolved feature_name for all path variables

### AC2: Feature Name Resolution
- [ ] Check if feature_name already in resolved variables (explicit param)
- [ ] If not, call FeaturePathResolver.resolve_feature_name(params, context)
- [ ] Add resolved feature_name to variables dict
- [ ] Use feature_name for all feature-scoped path resolution

### AC3: Fallback to Legacy Paths
- [ ] If feature_name resolution fails AND workflow doesn't require it: use legacy paths
- [ ] If feature_name resolution fails AND workflow requires it: raise ValueError
- [ ] Determine workflow requirement by checking if workflow uses {{feature_name}} variable
- [ ] Log warning when falling back to legacy paths

### AC4: WorkflowContext Integration
- [ ] Accept optional `context: WorkflowContext` parameter in resolve_variables()
- [ ] Pass context to FeaturePathResolver
- [ ] Ensure context.metadata.feature_name persists across workflow steps
- [ ] Update all workflow execution calls to pass context

### AC5: Testing
- [ ] 15+ integration test cases covering:
  - Feature name resolution (all 6 priority levels)
  - WorkflowContext persistence
  - Fallback to legacy paths
  - Error cases (required feature_name but can't resolve)
  - Path generation with resolved feature_name

## Technical Notes

### Implementation Approach

**Extend WorkflowExecutor (gao_dev/core/workflow_executor.py):**

```python
# Location: gao_dev/core/workflow_executor.py (lines ~100-300)

from gao_dev.core.services.feature_path_resolver import FeaturePathResolver
from gao_dev.core.state.feature_state_service import FeatureStateService

class WorkflowExecutor:
    """
    Execute workflows with variable resolution and template rendering.

    EXISTING FUNCTIONALITY (Epic 18):
    - Load workflows from YAML
    - Resolve variables with priority: params → workflow → config → common
    - Render templates with resolved variables
    - Track workflow execution

    NEW ENHANCEMENTS (Story 34.3):
    - Integrate FeaturePathResolver for feature_name resolution
    - Pass WorkflowContext to resolvers
    - Support feature-scoped paths
    - Fallback to legacy paths when needed
    """

    def __init__(
        self,
        project_root: Path,
        config_manager: ConfigManager,
        feature_service: FeatureStateService  # NEW dependency
    ):
        self.project_root = project_root
        self.config = config_manager
        self.workflows = self._load_workflows()

        # NEW: Initialize FeaturePathResolver
        self.feature_resolver = FeaturePathResolver(
            project_root=project_root,
            feature_service=feature_service
        )

    def resolve_variables(
        self,
        workflow: Workflow,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None  # NEW parameter
    ) -> Dict[str, Any]:
        """
        Resolve variables with feature_name auto-detection.

        EXISTING PRIORITY (Epic 18):
        1. Explicit params (runtime parameters)
        2. Workflow defaults (workflow.variables)
        3. Config defaults (defaults.yaml)
        4. Common variables (auto-generated: date, timestamp, etc.)

        NEW ENHANCEMENT (Story 34.3):
        5. Feature name resolution (FeaturePathResolver with 6-level priority)
        6. Feature-scoped path generation (using resolved feature_name)

        Args:
            workflow: Workflow definition
            params: Runtime parameters
            context: Optional WorkflowContext (for feature_name persistence)

        Returns:
            Dict with all resolved variables

        Raises:
            ValueError: If required feature_name cannot be resolved
        """
        resolved = {}

        # Priority 1-3: Existing resolution logic (Epic 18)
        resolved.update(self._resolve_from_params(params))
        resolved.update(self._resolve_from_workflow(workflow))
        resolved.update(self._resolve_from_config())

        # Priority 4: Common variables (Epic 18)
        resolved.update(self._generate_common_variables())

        # NEW: Priority 5 - Feature name resolution
        if "feature_name" not in resolved:
            try:
                feature_name = self.feature_resolver.resolve_feature_name(
                    params=resolved,
                    context=context  # Pass context for priority 2!
                )
                resolved["feature_name"] = feature_name

                logger.info(
                    "Resolved feature_name",
                    feature_name=feature_name,
                    source="FeaturePathResolver"
                )

            except ValueError as e:
                # Feature name required but can't resolve
                if self._workflow_requires_feature_name(workflow):
                    raise ValueError(
                        f"Workflow '{workflow.name}' requires feature_name but cannot resolve.\n"
                        f"{str(e)}\n\n"
                        f"Specify feature_name explicitly:\n"
                        f"  --feature-name <name>\n"
                        f"Or run from feature directory:\n"
                        f"  cd docs/features/<name> && gao-dev {workflow.name}"
                    ) from e

                # Otherwise, use legacy paths (backward compatibility)
                logger.warning(
                    "feature_name not resolved, using legacy paths",
                    workflow=workflow.name,
                    reason=str(e)
                )
                # Don't add feature_name to resolved (will use legacy paths)

        # NEW: Priority 6 - Feature-scoped path generation
        if "feature_name" in resolved:
            resolved.update(self._generate_feature_scoped_paths(resolved))

        return resolved

    def _workflow_requires_feature_name(self, workflow: Workflow) -> bool:
        """
        Check if workflow requires feature_name.

        A workflow requires feature_name if:
        - It uses {{feature_name}} in any template
        - It has output paths that are feature-scoped
        - It's a feature-related workflow (prd, architecture, etc.)

        Args:
            workflow: Workflow definition

        Returns:
            True if workflow requires feature_name
        """
        # Check if workflow template uses {{feature_name}} variable
        template_content = workflow.template or ""
        if "{{feature_name}}" in template_content:
            return True

        # Check if workflow has feature-scoped output paths
        output_location = workflow.variables.get("output_location", "")
        if "{{feature_name}}" in str(output_location):
            return True

        # Check if workflow is feature-related by name
        feature_workflows = [
            "create_prd", "create_architecture", "create_epic",
            "create_story", "implement_story", "qa_validation"
        ]
        if workflow.name in feature_workflows:
            return True

        return False

    def _generate_feature_scoped_paths(self, resolved: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate feature-scoped paths using FeaturePathResolver.

        Uses resolved feature_name, epic, epic_name, story to generate
        all feature-scoped paths (PRD, epic location, story location, etc.)

        Args:
            resolved: Already resolved variables (must contain feature_name)

        Returns:
            Dict with generated paths
        """
        paths = {}
        feature_name = resolved["feature_name"]

        # Generate all path types
        path_types = [
            "prd", "architecture", "readme", "epics_overview",
            "qa_folder", "retrospectives_folder",
            "epic_folder", "epic_location",
            "story_folder", "story_location", "context_xml_folder",
            "retrospective_location"
        ]

        for path_type in path_types:
            try:
                path = self.feature_resolver.generate_feature_path(
                    feature_name=feature_name,
                    path_type=path_type,
                    epic=resolved.get("epic"),
                    epic_name=resolved.get("epic_name"),
                    story=resolved.get("story")
                )
                # Convert path_type to variable name (e.g., "prd" → "prd_location")
                var_name = f"{path_type}_location" if not path_type.endswith(("_folder", "_location", "_overview")) else path_type
                paths[var_name] = str(path)

            except ValueError:
                # Path type may require epic/story that aren't available
                # (e.g., story_location requires epic and story)
                pass

        return paths

    # EXISTING METHODS (Epic 18 - unchanged)
    def _resolve_from_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve variables from explicit parameters (Priority 1)."""
        return params.copy()

    def _resolve_from_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Resolve variables from workflow defaults (Priority 2)."""
        return workflow.variables.copy()

    def _resolve_from_config(self) -> Dict[str, Any]:
        """Resolve variables from config defaults (Priority 3)."""
        return self.config.get("workflow_defaults", {}).copy()

    def _generate_common_variables(self) -> Dict[str, Any]:
        """Generate common variables (Priority 4)."""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "project_name": self.project_root.name,
            "project_root": str(self.project_root)
        }
```

**Update Workflow Execution Calls:**

```python
# In various orchestrators and agents, update to pass context:

# Before (Epic 18):
variables = workflow_executor.resolve_variables(workflow, params)

# After (Story 34.3):
variables = workflow_executor.resolve_variables(workflow, params, context=context)
```

### Code Locations

**File to Modify:**
- `gao_dev/core/workflow_executor.py` (lines ~100-300)
  - Add feature_service to __init__()
  - Add feature_resolver initialization
  - Extend resolve_variables() with context parameter
  - Add _workflow_requires_feature_name() helper
  - Add _generate_feature_scoped_paths() helper

**Files to Update (Pass Context):**
- `gao_dev/orchestrator/gao_dev_orchestrator.py` (pass context to executor)
- Agent implementations that call workflow_executor (pass context)

### Dependencies

**Required Before Starting:**
- Story 32.4: FeaturePathResolver (COMPLETE)
- Story 34.2: Updated defaults.yaml (COMPLETE)
- Epic 18: WorkflowExecutor and WorkflowContext (COMPLETE)

**Blocks:**
- Story 34.4: Testing & Documentation (needs integration working)

### Integration Points

1. **FeaturePathResolver**: Called for feature_name resolution and path generation
2. **WorkflowContext**: Passed to resolver for context.metadata.feature_name access
3. **defaults.yaml**: Fallback path templates when feature_name not available
4. **All Workflows**: Will use feature-scoped paths when feature_name resolved

## Testing Requirements

### Integration Tests (15+ cases)

**Location:** `tests/core/test_workflow_executor_integration.py`

**Test Coverage:**

1. **Feature Name Resolution - All Priorities (6 cases)**
   - Priority 1: Explicit parameter resolves correctly
   - Priority 2: WorkflowContext.metadata["feature_name"] resolves
   - Priority 3: CWD in feature folder resolves
   - Priority 4: Single feature auto-detects
   - Priority 5: MVP auto-detects
   - Priority 6: Ambiguous raises error with helpful message

2. **WorkflowContext Persistence (3 cases)**
   - Set feature_name in context once
   - Execute multiple workflows
   - feature_name persists across all executions (no need to re-specify)

3. **Path Generation (3 cases)**
   - Resolved feature_name generates PRD path
   - Resolved feature_name generates epic path (with epic, epic_name)
   - Resolved feature_name generates story path (with epic, epic_name, story)

4. **Fallback to Legacy Paths (2 cases)**
   - Workflow doesn't require feature_name → uses legacy paths
   - Workflow requires feature_name but can't resolve → raises ValueError

5. **Error Handling (1 case)**
   - Required feature_name but multiple features → error lists all features

## Definition of Done

- [ ] WorkflowExecutor.resolve_variables() extended with context parameter
- [ ] FeaturePathResolver integrated
- [ ] 6-level feature_name resolution working
- [ ] WorkflowContext passed to resolver
- [ ] Feature-scoped paths generated for all path types
- [ ] Fallback to legacy paths implemented
- [ ] 15+ integration test cases passing
- [ ] All workflow execution calls updated (pass context)
- [ ] Code reviewed and approved
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging for resolution decisions

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Integration - WorkflowExecutor)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Integration 2 - WorkflowExecutor)
- **Epic 18:** WorkflowExecutor original implementation
- **Story 32.4:** FeaturePathResolver (6-level priority)
