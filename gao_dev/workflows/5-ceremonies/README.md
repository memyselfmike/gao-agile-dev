# Ceremony Workflows

This directory contains ceremony workflow definitions for GAO-Dev's multi-agent coordination system.

## Overview

**Ceremony workflows** are special workflows that coordinate multi-agent ceremonies using the `CeremonyOrchestrator`. Unlike regular workflows where a single agent executes a task, ceremony workflows bring multiple agents together for collaborative activities like planning, standups, and retrospectives.

## Available Ceremonies

### 1. Planning Ceremony (`planning-ceremony.yaml`)

**Purpose**: Kickoff epic with team alignment on goals, architecture, and story breakdown

**Participants**:
- John (Product Manager)
- Winston (Technical Architect)
- Bob (Scrum Master)

**Trigger**:
- `epic_start`
- Required for Scale Level 3+ projects

**Duration**: 15-30 minutes

**Outcomes**:
- Planning transcript saved to `docs/features/{feature_name}/ceremonies/planning-{epic_num}.md`
- Action items for epic kickoff
- Team aligned on epic goals, architecture, and risks

### 2. Standup Ceremony (`standup-ceremony.yaml`)

**Purpose**: Daily sync on progress, blockers, and action items

**Participants**:
- Bob (Scrum Master)
- Amelia (Developer)
- Murat (Test Architect)

**Trigger**:
- `story_interval` (varies by scale level)
  - Level 2: Every 3 stories
  - Level 3: Every 2 stories
  - Level 4: Every 1 story
- `quality_gate_failure`

**Duration**: 5-10 minutes

**Outcomes**:
- Standup transcript saved to `docs/features/{feature_name}/ceremonies/standup-{epic_num}-{date}.md`
- Blockers identified and tracked
- Action items for high-priority issues

### 3. Retrospective Ceremony (`retrospective-ceremony.yaml`)

**Purpose**: Capture learnings and improvements after epic completion or at mid-epic checkpoints

**Participants**:
- All team members (John, Winston, Sally, Bob, Amelia, Murat)

**Trigger**:
- `epic_completion`
- `mid_epic_checkpoint`
- Required for Scale Level 2+ projects

**Duration**: 20-45 minutes

**Outcomes**:
- Retrospective transcript saved to `docs/features/{feature_name}/retrospectives/retro-{epic_num}.md`
- 3-10 learnings extracted and indexed
- Action items for improvements
- Learning relevance scores assigned

## How Ceremony Workflows Differ from Regular Workflows

| Aspect | Regular Workflow | Ceremony Workflow |
|--------|------------------|-------------------|
| **Agent** | Single agent executes task | Multiple agents collaborate |
| **Execution** | Direct task execution | CeremonyOrchestrator coordination |
| **Outcomes** | Artifacts (code, docs) | Transcript + Action Items + Learnings |
| **Trigger** | Workflow sequence | Event-driven (epic milestones, intervals) |
| **Duration** | Variable | Time-boxed (5-45 minutes) |
| **Category** | analysis/planning/solutioning/implementation | ceremonies |
| **Phase** | 0-4 | 5 |

## Ceremony Workflow Structure

All ceremony workflows follow this structure:

```yaml
name: ceremony-name
description: Brief description
category: ceremonies           # Always "ceremonies"
phase: 5                       # Always phase 5
agent: Bob                     # Usually Bob (facilitator)
non_interactive: false
autonomous: true
iterative: false
web_bundle: false

# Ceremony-specific metadata
metadata:
  ceremony_type: planning | standup | retrospective
  participants:
    - Agent1
    - Agent2
  trigger: epic_start | story_interval | epic_completion
  required_for_levels:
    - 2
    - 3
    - 4
  duration_estimate: "X-Y minutes"
  success_criteria:
    - Criterion 1
    - Criterion 2

variables:
  epic_num:
    description: Epic number
    type: integer
    required: true
  # ... other variables

required_tools:
  - read_file
  - write_file
  - ceremony_orchestrator

output_file: "{{ceremony_output_folder}}/ceremony-{{epic_num}}.md"

templates:
  main: |
    # Ceremony instructions for facilitator
    # Step-by-step guide for executing ceremony
    # Expected outcomes and success criteria
```

## Variable Substitution

Ceremony workflows support standard GAO-Dev variable substitution:

- `{{epic_num}}` - Epic number
- `{{feature_name}}` - Feature name
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{ceremony_output_folder}}` - Output folder for ceremony artifacts
- `{{stories_completed}}` - Number of stories completed
- `{{total_stories}}` - Total stories in epic

All variables follow the same resolution priority as regular workflows:
1. Runtime parameters (execution-time values)
2. Workflow YAML defaults
3. Config defaults (`config/defaults.yaml`)
4. Common variables (auto-generated)

## Integration with CeremonyOrchestrator

Ceremony workflows invoke `CeremonyOrchestrator` to coordinate multi-agent conversations:

```python
from gao_dev.orchestrator.ceremony_orchestrator import CeremonyOrchestrator

result = ceremony_orchestrator.hold_ceremony(
    ceremony_type="planning",
    epic_num=1,
    participants=["John", "Winston", "Bob"],
    additional_context={
        "feature_name": "user-authentication",
        "prd_path": "docs/features/user-authentication/PRD.md"
    }
)
```

The orchestrator handles:
1. **Preparation**: Load context and prepare participants
2. **Execution**: Run ceremony conversation
3. **Recording**: Save artifacts (transcript, action items, learnings)

## Trigger Evaluation

The `CeremonyTriggerEngine` (Story 28.3) evaluates when ceremonies should trigger:

**Epic Lifecycle Triggers**:
- `epic_start` - At the beginning of an epic (planning)
- `epic_completion` - At the end of an epic (retrospective)
- `mid_epic_checkpoint` - At 50% epic completion (retrospective)

**Interval Triggers**:
- `story_interval` - Every N stories (standup, varies by scale level)
- `story_count_threshold` - After X stories completed

**Quality Gate Triggers**:
- `quality_gate_failure` - When tests fail or linting errors (standup)
- `repeated_failure` - When same test fails multiple times

## WorkflowRegistry Integration

Ceremony workflows are loaded by `WorkflowRegistry` just like regular workflows:

```python
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.config_loader import ConfigLoader

config = ConfigLoader()
registry = WorkflowRegistry(config)
registry.index_workflows()

# Get ceremony workflow
planning = registry.get_workflow("planning-ceremony")
print(planning.metadata['ceremony_type'])  # "planning"
print(planning.metadata['participants'])    # ["John", "Winston", "Bob"]

# List all ceremonies
ceremonies = registry.list_workflows(phase=5)
```

The registry validates ceremony-specific metadata:
- `ceremony_type` field is present and valid
- `participants` field is a list of agent names
- `trigger` field is a valid TriggerType

## CLI Commands

List all ceremony workflows:

```bash
gao-dev list-workflows --phase 5
gao-dev list-workflows --category ceremonies
```

Get ceremony workflow details:

```bash
gao-dev workflow-info planning-ceremony
gao-dev workflow-info standup-ceremony
gao-dev workflow-info retrospective-ceremony
```

## Testing

Ceremony workflows have comprehensive unit tests in `tests/core/test_workflow_registry_ceremonies.py`:

- Ceremony workflows load successfully
- Metadata validation works
- Category "ceremonies" recognized
- Workflow instructions are valid
- Variable placeholders present

Run tests:

```bash
pytest tests/core/test_workflow_registry_ceremonies.py -v
```

## Self-Learning Integration

Ceremony workflows are key to GAO-Dev's self-learning system (Epic 29):

1. **Retrospectives extract learnings** that are indexed in the database
2. **Learnings feed back into Brian's workflow selection** (Story 29.3)
3. **Workflow adjustments based on learnings** (Story 29.4)
4. **Action items flow into next sprint** (Story 29.5)

This creates a closed-loop learning system where the system improves with every project.

## Best Practices

1. **Keep ceremonies time-boxed**: Follow duration estimates to maintain efficiency
2. **Focus on outcomes**: Ensure every ceremony produces actionable artifacts
3. **Clear facilitation**: Bob (facilitator) should guide discussion efficiently
4. **Document learnings**: Retrospectives should extract 3-10 actionable learnings
5. **Follow up on action items**: Ensure action items are tracked and completed

## Related Documentation

- **PRD**: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- **Architecture**: `docs/features/ceremony-integration-and-self-learning/ARCHITECTURE.md`
- **Epic 28**: `docs/features/ceremony-integration-and-self-learning/epics/epic-28-ceremony-workflow-integration.md`
- **CeremonyOrchestrator**: `gao_dev/orchestrator/ceremony_orchestrator.py`
- **WorkflowRegistry**: `gao_dev/core/workflow_registry.py`
