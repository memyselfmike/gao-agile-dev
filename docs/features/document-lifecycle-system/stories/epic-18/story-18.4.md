# Story 18.4: Configuration Defaults

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 3
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Add default workflow variable values to the configuration system to provide sensible defaults that match GAO-Dev project conventions. These defaults should be configurable but provide good out-of-the-box behavior for common workflow variables like document locations, output folders, and file paths. The system should load these defaults from a YAML configuration file and make them available to WorkflowExecutor for variable resolution.

---

## Business Value

This story provides sensible defaults for the variable resolution system:

- **Zero Configuration**: Workflows work out-of-the-box without requiring parameter overrides
- **Convention Enforcement**: Default paths follow GAO-Dev project structure conventions
- **Customization**: Users can override defaults via config without editing workflows
- **Maintainability**: Change default paths in one place, not scattered across workflows
- **Documentation**: Config file documents expected variable values
- **Consistency**: All workflows use same default paths for consistency
- **Flexibility**: Different projects can customize defaults via local config
- **Discoverability**: Users can see all available variables and defaults
- **Migration Support**: Provides backward compatibility defaults for existing workflows
- **Production Ready**: Professional configuration management

---

## Acceptance Criteria

### Configuration File
- [ ] `defaults.yaml` exists with `workflow_defaults` section
- [ ] All common workflow variables defined with sensible defaults
- [ ] Defaults match GAO-Dev project conventions (docs/ folder structure)
- [ ] YAML file has clear comments explaining each default
- [ ] Variables include: prd_location, architecture_location, tech_spec_location
- [ ] Variables include: dev_story_location, epic_location, output_folder
- [ ] File organized logically (document locations, output paths, etc.)

### ConfigLoader Integration
- [ ] ConfigLoader loads workflow_defaults section from YAML
- [ ] ConfigLoader provides `get_workflow_defaults()` method
- [ ] Method returns dict of variable name → default value
- [ ] Handles missing workflow_defaults section gracefully (return empty dict)
- [ ] Validates that all defaults are strings (path values)
- [ ] Logs warning if defaults section malformed

### WorkflowExecutor Integration
- [ ] WorkflowExecutor uses config defaults when resolving variables
- [ ] Config defaults used when variable not in params or workflow.yaml
- [ ] Priority order: params > workflow.yaml > config defaults
- [ ] All default paths tested with actual workflow execution

### Testing
- [ ] Unit tests verify config loading from defaults.yaml
- [ ] Unit tests verify get_workflow_defaults() returns correct dict
- [ ] Unit tests verify defaults used when variable not in params
- [ ] Unit tests verify parameter override of defaults
- [ ] Integration test: Workflow uses config default when no param provided
- [ ] Integration test: PRD workflow creates file at default location

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/config/defaults.yaml` (create or update)

**Add workflow_defaults section:**

```yaml
# Default values for workflow variables
# These provide sensible defaults for common workflow variables
# Projects can override these in their local config files

workflow_defaults:
  # Document locations follow GAO-Dev project structure

  # Product Requirements Document location
  prd_location: "docs/PRD.md"

  # System architecture documentation location
  architecture_location: "docs/ARCHITECTURE.md"

  # Technical specification document location
  tech_spec_location: "docs/TECHNICAL_SPEC.md"

  # Directory for development stories
  dev_story_location: "docs/stories"

  # Epic tracking document location
  epic_location: "docs/epics.md"

  # Default output folder for all documentation
  output_folder: "docs"

  # Sprint status tracking file
  sprint_status_location: "docs/sprint-status.yaml"

  # Workflow status tracking file
  workflow_status_location: "docs/bmm-workflow-status.md"

# Document lifecycle configuration
document_lifecycle:
  # Directory for archived documents
  archive_dir: ".archive"

  # Automatically register workflow artifacts
  auto_register: true

  # Directory for document lifecycle database
  lifecycle_dir: ".gao-dev"
```

**File:** `gao_dev/core/config_loader.py`

**Add method to load workflow defaults:**

```python
def get_workflow_defaults(self) -> Dict[str, Any]:
    """
    Get default values for workflow variables.

    Returns:
        Dict mapping variable names to default values
    """
    try:
        if not hasattr(self, '_workflow_defaults'):
            # Load from defaults.yaml on first access
            defaults_path = self.config_dir / "defaults.yaml"

            if not defaults_path.exists():
                logger.warning(
                    "defaults_yaml_not_found",
                    path=str(defaults_path),
                    message="No defaults.yaml found - using empty defaults"
                )
                self._workflow_defaults = {}
                return self._workflow_defaults

            with open(defaults_path, 'r', encoding='utf-8') as f:
                defaults_data = yaml.safe_load(f)

            # Extract workflow_defaults section
            workflow_defaults = defaults_data.get('workflow_defaults', {})

            # Validate all defaults are strings (path values)
            for key, value in workflow_defaults.items():
                if not isinstance(value, str):
                    logger.warning(
                        "workflow_default_invalid_type",
                        variable=key,
                        value_type=type(value).__name__,
                        message="Workflow default must be string - skipping"
                    )
                    continue

            self._workflow_defaults = {
                k: v for k, v in workflow_defaults.items()
                if isinstance(v, str)
            }

            logger.debug(
                "workflow_defaults_loaded",
                defaults_count=len(self._workflow_defaults),
                defaults=list(self._workflow_defaults.keys())
            )

        return self._workflow_defaults.copy()

    except Exception as e:
        logger.error(
            "workflow_defaults_load_error",
            error=str(e),
            error_type=type(e).__name__,
            message="Failed to load workflow defaults - using empty dict"
        )
        return {}
```

**File:** `gao_dev/core/workflow_executor.py`

**Update `_resolve_variables()` to use config defaults:**

```python
def _resolve_variables(
    self, workflow: WorkflowInfo, params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Resolve workflow variables from multiple sources.

    Priority order:
    1. Parameters (passed to execute method)
    2. Workflow.yaml variables section
    3. Config defaults (from defaults.yaml)
    4. Common variables (date, timestamp)
    """
    variables = {}

    # Layer 1: Config defaults (lowest priority)
    config_defaults = self.config_loader.get_workflow_defaults()
    variables.update(config_defaults)

    logger.debug(
        "variables_from_config_defaults",
        variables_count=len(config_defaults),
        variables=list(config_defaults.keys())
    )

    # Layer 2: Workflow.yaml defaults
    if workflow.variables:
        workflow_defaults = {
            k: v.get('default')
            for k, v in workflow.variables.items()
            if 'default' in v
        }
        variables.update(workflow_defaults)

        logger.debug(
            "variables_from_workflow_yaml",
            variables_count=len(workflow_defaults),
            variables=list(workflow_defaults.keys())
        )

    # Layer 3: Parameters (highest priority)
    variables.update(params)

    logger.debug(
        "variables_from_params",
        variables_count=len(params),
        variables=list(params.keys())
    )

    # Layer 4: Add common variables
    common_vars = self._add_common_variables()
    variables.update(common_vars)

    # Validate required variables
    self._validate_required_variables(workflow, variables)

    return variables
```

---

## Dependencies

- ConfigLoader infrastructure exists
- YAML parsing support (PyYAML)
- WorkflowExecutor variable resolution (Story 18.1)

---

## Tasks

### Implementation Tasks
- [ ] Create or update gao_dev/config/defaults.yaml
- [ ] Add workflow_defaults section with all common variables
- [ ] Add clear comments documenting each default variable
- [ ] Organize variables logically (document locations, paths, etc.)
- [ ] Add get_workflow_defaults() method to ConfigLoader
- [ ] Implement YAML loading and parsing
- [ ] Add validation for default values (must be strings)
- [ ] Handle missing defaults.yaml gracefully
- [ ] Update WorkflowExecutor._resolve_variables() to use config defaults
- [ ] Ensure proper priority order (params > workflow > config)
- [ ] Add comprehensive logging for default loading

### Testing Tasks
- [ ] Write unit test: test_load_workflow_defaults_from_yaml()
- [ ] Write unit test: test_workflow_defaults_all_strings()
- [ ] Write unit test: test_workflow_defaults_missing_file()
- [ ] Write unit test: test_workflow_defaults_malformed_yaml()
- [ ] Write unit test: test_resolve_variables_uses_config_defaults()
- [ ] Write unit test: test_resolve_variables_priority_order()
- [ ] Write unit test: test_param_overrides_config_default()
- [ ] Write integration test: test_workflow_uses_config_defaults()
- [ ] Write integration test: test_prd_workflow_default_location()

### Documentation Tasks
- [ ] Add comments to defaults.yaml explaining each variable
- [ ] Document how to override defaults in project config
- [ ] Add example of custom defaults in project
- [ ] Document variable naming conventions
- [ ] Update VARIABLE_RESOLUTION.md with config defaults section

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] defaults.yaml created with all common variables
- [ ] ConfigLoader loads and exposes workflow defaults
- [ ] WorkflowExecutor uses config defaults correctly
- [ ] Unit tests pass (>80% coverage)
- [ ] Integration tests pass
- [ ] Code review approved
- [ ] Documentation updated with examples
- [ ] Manual testing with workflows successful
- [ ] Merged to feature branch

---

## Files to Modify

1. `gao_dev/config/defaults.yaml` (create or update, ~40 LOC)
   - Add workflow_defaults section
   - Document all common variables
   - Add clear comments

2. `gao_dev/core/config_loader.py` (~30 LOC additions)
   - Add get_workflow_defaults() method
   - Implement YAML loading
   - Add validation logic
   - Add error handling

3. `gao_dev/core/workflow_executor.py` (~15 LOC changes)
   - Update _resolve_variables() to use config defaults
   - Ensure proper priority order
   - Add logging for defaults

4. `tests/core/test_config_loader_defaults.py` (new file, ~100 LOC)
   - Unit tests for defaults loading
   - Unit tests for validation
   - Unit tests for error handling

5. `tests/core/test_workflow_executor_variables.py` (update, ~50 LOC additions)
   - Unit tests for config defaults usage
   - Unit tests for priority order
   - Integration tests

---

## Success Metrics

- **Defaults Coverage**: All common workflow variables have defaults
- **Convention Compliance**: 100% of defaults follow GAO-Dev conventions
- **Validation**: 100% of defaults are valid strings
- **Test Coverage**: >80% coverage for config loading code
- **Usability**: Workflows work without parameter overrides
- **Documentation**: All defaults clearly documented

---

## Risk Assessment

**Risks:**
- Defaults might not match all project structures
- Breaking changes if defaults change
- YAML parsing errors
- Missing defaults.yaml file

**Mitigations:**
- Use GAO-Dev standard conventions
- Version defaults.yaml (breaking changes documented)
- Comprehensive error handling and logging
- Gracefully handle missing file (return empty dict)
- Allow project-specific overrides
- Document customization process

---

## Notes

- Defaults should match GAO-Dev project conventions exactly
- All path defaults should use forward slashes (cross-platform)
- Consider adding validation schema for defaults.yaml
- Future enhancement: support environment variable substitution in defaults
- Consider adding default categories (paths, locations, flags, etc.)
- Keep defaults minimal - only common variables used across multiple workflows
- Document how to add project-specific defaults

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
