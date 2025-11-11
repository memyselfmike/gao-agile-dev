# Variable Naming Guide

**Feature:** Feature-Based Document Structure
**Epic:** 34 - Integration & Variables
**Story:** 34.2 - Update defaults.yaml
**Version:** 3.0
**Updated:** 2025-11-11

## Overview

This guide documents the naming convention and template variables used in GAO-Dev's feature-based document structure. All path variables follow consistent naming patterns for clarity and predictability.

## Naming Convention

### Suffixes

All path variables use clear suffixes to indicate their type:

| Suffix | Meaning | Example | Resolves To |
|--------|---------|---------|-------------|
| `_location` | Specific file path | `prd_location` | `docs/features/mvp/PRD.md` |
| `_folder` | Directory path | `qa_folder` | `docs/features/mvp/QA` |
| `_overview` | Master/index file | `epics_overview` | `docs/features/mvp/EPICS.md` |

### Naming Rules

1. **Use snake_case**: All variables use lowercase with underscores
2. **Be specific**: `prd_location` not `prd_path` or `prd_file`
3. **No ambiguity**: Name should clearly indicate what it points to
4. **Consistent structure**: `{type}_{suffix}` pattern

## Template Variables

### Feature-Level Variables

Variables that identify the feature and epic:

| Variable | Description | Example Values |
|----------|-------------|----------------|
| `{{feature_name}}` | Feature identifier | `"mvp"`, `"user-auth"`, `"payment-system"` |
| `{{epic}}` | Epic number | `"1"`, `"2"`, `"34"` |
| `{{epic_name}}` | Epic identifier | `"foundation"`, `"oauth-integration"` |
| `{{story}}` | Story number | `"1"`, `"2"`, `"5"` |

### Auto-Generated Variables

Variables automatically populated by WorkflowExecutor:

| Variable | Description | Example Values |
|----------|-------------|----------------|
| `{{date}}` | Current date | `"2025-11-11"` |
| `{{timestamp}}` | ISO 8601 timestamp | `"2025-11-11T14:30:00Z"` |
| `{{project_name}}` | Project name | `"gao-agile-dev"` |
| `{{project_root}}` | Project root path | `"/path/to/project"` |
| `{{agent}}` | Executing agent | `"john"`, `"winston"`, `"amelia"` |
| `{{workflow}}` | Workflow name | `"create-prd"`, `"implement-story"` |

## Path Structure

### Feature-Level Documents

Primary documents at the feature root:

```yaml
# Feature directory
feature_dir: "docs/features/{{feature_name}}"

# Primary documents
prd_location: "docs/features/{{feature_name}}/PRD.md"
architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
readme_location: "docs/features/{{feature_name}}/README.md"
epics_overview: "docs/features/{{feature_name}}/EPICS.md"
```

**Example Resolution** (feature_name="user-auth"):
- `feature_dir` → `docs/features/user-auth`
- `prd_location` → `docs/features/user-auth/PRD.md`
- `architecture_location` → `docs/features/user-auth/ARCHITECTURE.md`
- `readme_location` → `docs/features/user-auth/README.md`
- `epics_overview` → `docs/features/user-auth/EPICS.md`

### Feature-Level Folders

Organizational folders at feature root:

```yaml
qa_folder: "docs/features/{{feature_name}}/QA"
retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"
ceremonies_folder: "docs/features/{{feature_name}}/ceremonies"
standups_folder: "docs/features/{{feature_name}}/standups"
```

**Example Resolution** (feature_name="user-auth"):
- `qa_folder` → `docs/features/user-auth/QA`
- `retrospectives_folder` → `docs/features/user-auth/retrospectives`
- `ceremonies_folder` → `docs/features/user-auth/ceremonies`
- `standups_folder` → `docs/features/user-auth/standups`

### Epic-Level Paths (Co-Located Structure)

Epics contain their stories for intuitive navigation:

```yaml
# Epic folder (contains README.md, stories/, context/)
epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"

# Epic definition file
epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"
```

**Example Resolution** (feature_name="user-auth", epic="1", epic_name="oauth-integration"):
- `epic_folder` → `docs/features/user-auth/epics/1-oauth-integration`
- `epic_location` → `docs/features/user-auth/epics/1-oauth-integration/README.md`

**Epic Folder Structure:**
```
docs/features/user-auth/epics/1-oauth-integration/
├── README.md           # Epic definition
├── stories/            # All stories for this epic
│   ├── story-1.1.md
│   ├── story-1.2.md
│   └── story-1.3.md
└── context/            # Context XML files
    ├── story-1.1.xml
    ├── story-1.2.xml
    └── story-1.3.xml
```

### Story-Level Paths (Inside Epic Folder)

Stories are co-located with their epic:

```yaml
# Story folder (inside epic folder)
story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"

# Individual story file
story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"

# Context XML folder
context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"

# Context XML file
context_xml_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context/story-{{epic}}.{{story}}.xml"
```

**Example Resolution** (feature_name="user-auth", epic="1", epic_name="oauth-integration", story="2"):
- `story_folder` → `docs/features/user-auth/epics/1-oauth-integration/stories`
- `story_location` → `docs/features/user-auth/epics/1-oauth-integration/stories/story-1.2.md`
- `context_xml_folder` → `docs/features/user-auth/epics/1-oauth-integration/context`
- `context_xml_location` → `docs/features/user-auth/epics/1-oauth-integration/context/story-1.2.xml`

### Ceremony Artifact Paths

Ceremony outputs stored at feature level:

```yaml
retrospective_location: "docs/features/{{feature_name}}/retrospectives/epic-{{epic}}-retro.md"
standup_location: "docs/features/{{feature_name}}/standups/standup-{{date}}.md"
planning_session_location: "docs/features/{{feature_name}}/ceremonies/planning-{{date}}.md"
```

**Example Resolution** (feature_name="user-auth", epic="1", date="2025-11-11"):
- `retrospective_location` → `docs/features/user-auth/retrospectives/epic-1-retro.md`
- `standup_location` → `docs/features/user-auth/standups/standup-2025-11-11.md`
- `planning_session_location` → `docs/features/user-auth/ceremonies/planning-2025-11-11.md`

### QA Artifact Paths

Quality assurance documents in QA folder:

```yaml
qa_validation_location: "docs/features/{{feature_name}}/QA/QA_VALIDATION_EPIC_{{epic}}.md"
test_report_location: "docs/features/{{feature_name}}/QA/TEST_REPORT_EPIC_{{epic}}.md"
final_qa_report_location: "docs/features/{{feature_name}}/QA/FINAL_QA_REPORT_{{feature_name}}.md"
```

**Example Resolution** (feature_name="user-auth", epic="1"):
- `qa_validation_location` → `docs/features/user-auth/QA/QA_VALIDATION_EPIC_1.md`
- `test_report_location` → `docs/features/user-auth/QA/TEST_REPORT_EPIC_1.md`
- `final_qa_report_location` → `docs/features/user-auth/QA/FINAL_QA_REPORT_user-auth.md`

## Complete Example: User Auth Feature

### Scenario

Building a User Authentication feature with OAuth integration:

- **Feature:** `user-auth`
- **Epic 1:** `oauth-integration` (3 stories)
- **Epic 2:** `session-management` (2 stories)

### Resolved Paths

```
docs/features/user-auth/
├── PRD.md                                    # prd_location
├── ARCHITECTURE.md                           # architecture_location
├── README.md                                 # readme_location
├── EPICS.md                                  # epics_overview
│
├── epics/
│   ├── 1-oauth-integration/                  # epic_folder (epic=1)
│   │   ├── README.md                         # epic_location
│   │   ├── stories/                          # story_folder
│   │   │   ├── story-1.1.md                  # story_location (story=1)
│   │   │   ├── story-1.2.md                  # story_location (story=2)
│   │   │   └── story-1.3.md                  # story_location (story=3)
│   │   └── context/                          # context_xml_folder
│   │       ├── story-1.1.xml                 # context_xml_location (story=1)
│   │       ├── story-1.2.xml                 # context_xml_location (story=2)
│   │       └── story-1.3.xml                 # context_xml_location (story=3)
│   │
│   └── 2-session-management/                 # epic_folder (epic=2)
│       ├── README.md                         # epic_location
│       ├── stories/                          # story_folder
│       │   ├── story-2.1.md                  # story_location (story=1)
│       │   └── story-2.2.md                  # story_location (story=2)
│       └── context/                          # context_xml_folder
│           ├── story-2.1.xml                 # context_xml_location (story=1)
│           └── story-2.2.xml                 # context_xml_location (story=2)
│
├── QA/                                       # qa_folder
│   ├── QA_VALIDATION_EPIC_1.md              # qa_validation_location (epic=1)
│   ├── TEST_REPORT_EPIC_1.md                # test_report_location (epic=1)
│   ├── QA_VALIDATION_EPIC_2.md              # qa_validation_location (epic=2)
│   ├── TEST_REPORT_EPIC_2.md                # test_report_location (epic=2)
│   └── FINAL_QA_REPORT_user-auth.md         # final_qa_report_location
│
├── retrospectives/                           # retrospectives_folder
│   ├── epic-1-retro.md                       # retrospective_location (epic=1)
│   └── epic-2-retro.md                       # retrospective_location (epic=2)
│
├── ceremonies/                               # ceremonies_folder
│   ├── planning-2025-11-01.md               # planning_session_location
│   └── planning-2025-11-15.md               # planning_session_location
│
└── standups/                                 # standups_folder
    ├── standup-2025-11-05.md                # standup_location
    ├── standup-2025-11-06.md                # standup_location
    └── standup-2025-11-07.md                # standup_location
```

## MVP (Greenfield) Example

For greenfield projects, use `mvp` as the feature name:

### Scenario

Building a new Todo App from scratch:

- **Feature:** `mvp`
- **Epic 1:** `foundation` (core entities, basic CRUD)
- **Epic 2:** `ui-enhancement` (styling, responsiveness)

### Resolved Paths

```
docs/features/mvp/
├── PRD.md                                    # prd_location
├── ARCHITECTURE.md                           # architecture_location
├── README.md                                 # readme_location
├── EPICS.md                                  # epics_overview
│
├── epics/
│   ├── 1-foundation/                         # epic_folder
│   │   ├── README.md                         # epic_location
│   │   ├── stories/                          # story_folder
│   │   │   ├── story-1.1.md                  # story_location
│   │   │   ├── story-1.2.md
│   │   │   └── story-1.3.md
│   │   └── context/                          # context_xml_folder
│   │       ├── story-1.1.xml                 # context_xml_location
│   │       ├── story-1.2.xml
│   │       └── story-1.3.xml
│   │
│   └── 2-ui-enhancement/                     # epic_folder
│       ├── README.md
│       ├── stories/
│       │   ├── story-2.1.md
│       │   └── story-2.2.md
│       └── context/
│           ├── story-2.1.xml
│           └── story-2.2.xml
│
├── QA/                                       # qa_folder
│   ├── QA_VALIDATION_EPIC_1.md
│   ├── TEST_REPORT_EPIC_1.md
│   └── FINAL_QA_REPORT_mvp.md               # final_qa_report_location
│
└── retrospectives/                           # retrospectives_folder
    ├── epic-1-retro.md
    └── epic-2-retro.md
```

## Legacy Paths (Deprecated)

For backward compatibility, legacy paths are still supported but marked DEPRECATED:

```yaml
legacy_prd_location: "docs/PRD.md"
legacy_architecture_location: "docs/ARCHITECTURE.md"
legacy_tech_spec_location: "docs/TECHNICAL_SPEC.md"
legacy_epic_location: "docs/epics.md"
legacy_story_folder: "docs/stories"
legacy_context_xml_folder: "docs/stories/{epic}/context"
legacy_output_folder: "docs"
legacy_sprint_status_location: "docs/sprint-status.yaml"
legacy_workflow_status_location: "docs/bmm-workflow-status.md"
```

**Migration Note:** These will be removed in a future version. New workflows should use feature-scoped paths.

## Usage in Workflows

### In workflow.yaml

```yaml
workflow:
  name: "create-epic"
  variables:
    # Epic-specific variables
    epic: "1"
    epic_name: "foundation"

    # Uses defaults.yaml for paths:
    # - epic_folder: docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}
    # - epic_location: docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md
```

### In workflow execution

```python
# WorkflowExecutor resolves variables in priority order:
# 1. Parameters (highest)
# 2. workflow.yaml
# 3. defaults.yaml
# 4. Auto-generated (date, timestamp, etc.)

result = executor.execute(
    workflow_name="create-epic",
    parameters={
        "feature_name": "user-auth",  # Priority 1
        "epic": "1",                  # Priority 1
        "epic_name": "oauth-integration"  # Priority 1
    }
)

# Variables resolve to:
# - epic_folder: docs/features/user-auth/epics/1-oauth-integration
# - epic_location: docs/features/user-auth/epics/1-oauth-integration/README.md
```

## Best Practices

### 1. Always Use Feature Names

Never hardcode paths. Always use `{{feature_name}}`:

**Good:**
```yaml
prd_location: "docs/features/{{feature_name}}/PRD.md"
```

**Bad:**
```yaml
prd_location: "docs/features/mvp/PRD.md"  # Hardcoded!
```

### 2. Follow Naming Convention

Use the correct suffix for clarity:

**Good:**
```yaml
epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"
epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
```

**Bad:**
```yaml
epic_path: "..."      # Ambiguous - file or folder?
epic_file: "..."      # Use _location
epic_dir: "..."       # Use _folder
```

### 3. Co-Locate Related Files

Keep stories inside their epic folders:

**Good (Co-Located):**
```
docs/features/user-auth/epics/1-oauth-integration/
├── README.md
├── stories/
│   ├── story-1.1.md
│   └── story-1.2.md
└── context/
    ├── story-1.1.xml
    └── story-1.2.xml
```

**Bad (Separated):**
```
docs/features/user-auth/
├── epics/
│   └── 1-oauth-integration.md
└── stories/
    ├── story-1.1.md
    └── story-1.2.md
```

### 4. Use Descriptive Epic Names

Epic names should be clear identifiers:

**Good:**
```yaml
epic_name: "oauth-integration"
epic_name: "session-management"
epic_name: "password-reset"
```

**Bad:**
```yaml
epic_name: "part1"           # Vague
epic_name: "epic-1"          # Redundant with epic number
epic_name: "stuff"           # Non-descriptive
```

## See Also

- **defaults.yaml:** `gao_dev/config/defaults.yaml` - Complete variable definitions
- **FeaturePathResolver:** `gao_dev/core/services/feature_path_resolver.py` - Path generation service
- **WorkflowExecutor:** Variable resolution in `gao_dev/core/workflow_executor.py`
- **PRD:** `docs/features/feature-based-document-structure/PRD.md` - Feature requirements
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` - System design

---

**Questions?** Refer to the PRD or Architecture docs for detailed explanations.
