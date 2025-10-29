# Story-Based Benchmark Configuration Guide

## Overview

GAO-Dev supports two workflow modes for benchmarks:

1. **Phase-Based** (Legacy/Waterfall): All planning done upfront, then all implementation, then all testing
2. **Story-Based** (New/Agile): Incremental development - each story is created, implemented, tested, and committed before moving to the next

## Story-Based Format

Story-based benchmarks use `epics` instead of `workflow_phases`:

```yaml
name: "my-project"
description: "Project description"

# Use epics for story-based mode
epics:
  - name: "Epic Name"
    description: "Epic description"
    priority: "P0"  # P0, P1, P2, P3
    stories:
      - name: "Story Name"
        agent: "Amelia"  # Bob, Amelia, Murat
        description: "Story description"
        acceptance_criteria:
          - "Criterion 1"
          - "Criterion 2"
        story_points: 5
        dependencies: ["Other Story Name"]  # Optional
        timeout_seconds: 3600  # Optional, per-story timeout
```

## Story Lifecycle

Each story follows this workflow:

1. **Story Creation** (Bob - Scrum Master)
   - Creates detailed story specification
   - Defines acceptance criteria
   - Identifies dependencies

2. **Story Implementation** (Amelia - Developer)
   - Implements the feature
   - Writes unit tests
   - Documents the code

3. **Story Validation** (Murat - QA)
   - Runs tests
   - Validates acceptance criteria
   - Performs quality checks

4. **Git Commit** (Automated)
   - Automatic commit after validation
   - Conventional commit format
   - Tracks all changes

## Story Configuration Fields

### Required Fields
- `name`: Story name (string)
- `agent`: Responsible agent - "Bob", "Amelia", or "Murat"

### Optional Fields
- `description`: Detailed story description (string)
- `acceptance_criteria`: List of criteria that must be met (array of strings)
- `story_points`: Effort estimation 1-8 (integer, default: 3)
- `dependencies`: Names of stories that must complete first (array of strings)
- `timeout_seconds`: Max time for story (integer, default: 3600)

## Epic Configuration Fields

### Required Fields
- `name`: Epic name (string)
- `description`: Epic description (string)
- `stories`: Array of story configurations

### Optional Fields
- `priority`: Priority level (string: "P0", "P1", "P2", "P3", default: "P1")

## Examples

### Minimal Story-Based Config

```yaml
name: "simple-api"
description: "Simple REST API"

epics:
  - name: "API Development"
    description: "Build REST API"
    stories:
      - name: "Create User Endpoint"
        agent: "Amelia"
        acceptance_criteria:
          - "POST /api/users creates user"
          - "Returns 201 status"
        story_points: 3
```

### Complete Example

See `todo-app-incremental.yaml` for a comprehensive example with:
- Multiple epics
- Story dependencies
- Custom timeouts
- Acceptance criteria
- Story points estimation

## Advantages of Story-Based Workflow

1. **Incremental Progress**: See results after each story
2. **Early Feedback**: Catch issues early in the cycle
3. **Git History**: Clean commit history per story
4. **Fail-Fast**: Stop on first failure, don't waste time
5. **True Agile**: Matches real-world agile development

## Backward Compatibility

Phase-based configs continue to work:

```yaml
name: "legacy-project"
description: "Uses phase-based workflow"

workflow_phases:
  - phase_name: "Planning"
    command: "plan-project"
    timeout_seconds: 3600
```

The system automatically detects which mode to use based on whether `epics` or `workflow_phases` is present.

## Validation Rules

- Config must have **either** `epics` **or** `workflow_phases`, not both
- Each story must have `name` and `agent`
- Each epic must have `name`, `description`, and at least one story
- Story points must be 1-8 if specified
- Dependencies must reference existing story names
- Agent must be one of: "Bob", "Amelia", "Murat"

## Testing Your Config

```bash
# Validate config format
gao-dev validate-config sandbox/benchmarks/my-config.yaml

# Run story-based benchmark
gao-dev run-benchmark sandbox/benchmarks/my-config.yaml
```

## Migration Guide

To convert a phase-based config to story-based:

1. Replace `workflow_phases` with `epics`
2. Group related work into epics
3. Break each phase into granular stories
4. Add acceptance criteria for each story
5. Assign appropriate agent (Bob/Amelia/Murat)
6. Set story points (1-8 scale)
7. Define dependencies between stories

Example:

```yaml
# Phase-Based (OLD)
workflow_phases:
  - phase_name: "Implement Auth"
    command: "implement-auth"

# Story-Based (NEW)
epics:
  - name: "Authentication"
    description: "User authentication system"
    stories:
      - name: "Auth Data Models"
        agent: "Amelia"
        story_points: 3
      - name: "Login Endpoint"
        agent: "Amelia"
        story_points: 5
        dependencies: ["Auth Data Models"]
```

## Best Practices

1. **Keep Stories Small**: 1-5 story points ideal
2. **Clear Acceptance Criteria**: 2-4 specific, testable criteria
3. **Logical Dependencies**: Only add if truly required
4. **Balanced Epics**: 3-7 stories per epic
5. **Appropriate Timeouts**: Give enough time but not excessive
6. **Meaningful Names**: Use action verbs (Create, Implement, Add, Build)

## Getting Help

- See `todo-app-incremental.yaml` for working example
- Run `gao-dev list-workflows` for available workflows
- Check docs at `docs/features/sandbox-system/`
- Report issues at GitHub repository
