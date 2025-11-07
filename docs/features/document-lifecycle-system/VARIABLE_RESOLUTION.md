# Workflow Variable Resolution System

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Status:** Production Ready

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Variable Resolution Flow](#variable-resolution-flow)
- [Defining Variables](#defining-variables)
- [Using Variables in Templates](#using-variables-in-templates)
- [Common Variables](#common-variables)
- [Artifact Detection System](#artifact-detection-system)
- [Document Lifecycle Integration](#document-lifecycle-integration)
- [Logging and Observability](#logging-and-observability)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Best Practices](#best-practices)

---

## Overview

The **Workflow Variable Resolution System** is a core component of GAO-Dev that ensures workflow variables defined in `workflow.yaml` files are properly resolved and used when rendering instructions for the LLM. This system solves the critical problem where variables like `{{prd_location}}` were being sent raw to the LLM, causing files to be created in incorrect locations.

### The Problem (Before Epic 18)

```
[workflow.yaml defines: prd_location="docs/PRD.md"]
         ↓
[Orchestrator loads instructions.md RAW]  ← BYPASSES WorkflowExecutor
         ↓
[Sends "Path: {{prd_location}}" to LLM]  ← Variable NOT resolved!
         ↓
[LLM ignores variable, creates PRD.md in root]  ← Wrong location
         ↓
[No artifact detection or document registration]  ← Lost tracking
```

### The Solution (After Epic 18)

```
[workflow.yaml: variables + defaults]
         ↓
[WorkflowExecutor.resolve_variables()]  ← Resolve from workflow.yaml, params, config
         ↓
[WorkflowExecutor.render_template()]  ← Render {{variable}} → actual values
         ↓
[Orchestrator sends RESOLVED instructions to LLM]  ← All variables replaced
         ↓
[LLM creates files at correct locations]
         ↓
[Post-execution artifact detector]  ← Detect created/modified files
         ↓
[DocumentLifecycleManager.register_document()]  ← Track all artifacts
```

**Key Benefits:**
- ✅ Variables are resolved before sending to LLM
- ✅ Files are created at correct locations
- ✅ All artifacts are automatically tracked
- ✅ Document lifecycle is properly maintained
- ✅ Project conventions are enforced

---

## Architecture

### System Components

The variable resolution system consists of four main components:

1. **Variable Definition** - Variables defined in workflow.yaml files
2. **Variable Resolution** - WorkflowExecutor resolves variables from multiple sources
3. **Template Rendering** - Mustache-style templates rendered with resolved values
4. **Artifact Detection** - Post-execution detection and registration of created files

### Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                      GAODevOrchestrator                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 1. Load workflow.yaml                                  │   │
│  │    - Variables section                                 │   │
│  │    - Instructions template                             │   │
│  └────────────────────────────────────────────────────────┘   │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 2. WorkflowExecutor.resolve_variables()                │   │
│  │    - Check parameters (highest priority)               │   │
│  │    - Check workflow.yaml defaults                      │   │
│  │    - Check config/defaults.yaml                        │   │
│  │    - Add common variables (date, timestamp, etc.)      │   │
│  └────────────────────────────────────────────────────────┘   │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 3. WorkflowExecutor.render_template()                  │   │
│  │    - Replace {{variable}} with actual values           │   │
│  │    - Generate final instructions for LLM               │   │
│  └────────────────────────────────────────────────────────┘   │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 4. Execute workflow with agent                         │   │
│  │    - Snapshot filesystem (before)                      │   │
│  │    - Send resolved instructions to LLM                 │   │
│  │    - LLM creates files at correct locations            │   │
│  │    - Snapshot filesystem (after)                       │   │
│  └────────────────────────────────────────────────────────┘   │
│                          ↓                                      │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 5. Artifact Detection & Registration                   │   │
│  │    - Compare before/after snapshots                    │   │
│  │    - Detect created/modified files                     │   │
│  │    - Register with DocumentLifecycleManager            │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Variable Resolution Flow

### Priority Order

Variables are resolved from multiple sources with the following priority (highest to lowest):

1. **Runtime Parameters** (highest priority)
   - Values passed at execution time
   - Example: `--project-name "MyApp"`

2. **Workflow YAML Defaults**
   - Defaults defined in `workflow.yaml` files
   - Example: `prd_location: "docs/PRD.md"`

3. **Config Defaults**
   - Defaults from `gao_dev/config/defaults.yaml`
   - Example: Global workflow defaults

4. **Common Variables** (lowest priority)
   - Auto-generated variables
   - Examples: `date`, `timestamp`, `project_name`

### Resolution Algorithm

```python
def resolve_variables(workflow, params):
    """
    Resolve variables from multiple sources.

    Priority: params > workflow.yaml > config > common
    """
    resolved = {}

    # 1. Start with common variables (lowest priority)
    resolved.update({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "project_name": get_project_name(),
        "project_root": get_project_root()
    })

    # 2. Add config defaults
    resolved.update(config.get("workflow_defaults", {}))

    # 3. Add workflow.yaml defaults
    for var_name, var_def in workflow.variables.items():
        if "default" in var_def:
            resolved[var_name] = var_def["default"]

    # 4. Override with runtime parameters (highest priority)
    resolved.update(params)

    return resolved
```

### Example Resolution

**workflow.yaml:**
```yaml
name: prd
variables:
  prd_location:
    default: "docs/PRD.md"
  output_folder:
    default: "docs"
```

**config/defaults.yaml:**
```yaml
workflow_defaults:
  prd_location: "documentation/PRD.md"  # Will be overridden
```

**Runtime parameters:**
```python
params = {
    "project_name": "TodoApp"
}
```

**Resolved variables:**
```python
{
    "date": "2025-11-07",
    "timestamp": "2025-11-07T10:30:00",
    "project_name": "TodoApp",          # From params (highest priority)
    "project_root": "/path/to/project",
    "prd_location": "docs/PRD.md",      # From workflow.yaml (overrides config)
    "output_folder": "docs"             # From workflow.yaml
}
```

---

## Defining Variables

### In workflow.yaml Files

Variables are defined in the `variables` section of `workflow.yaml` files:

```yaml
name: prd
description: "Create Product Requirements Document"
phase: planning
agent: john

variables:
  # Required variable (must be provided)
  prd_location:
    description: "Location for PRD file"
    default: "docs/PRD.md"
    required: true

  # Optional variable (has default)
  output_folder:
    description: "Output folder for documentation"
    default: "docs"
    required: false

  # Optional variable (no default)
  template_path:
    description: "Path to PRD template"
    required: false
```

**Variable Definition Schema:**

```yaml
variable_name:
  description: "Human-readable description"  # Required
  default: "default_value"                   # Optional
  required: true|false                       # Optional (default: false)
```

### In Configuration Files

Global defaults can be defined in `gao_dev/config/defaults.yaml`:

```yaml
workflow_defaults:
  # Common file locations
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  epic_location: "docs/epics"
  dev_story_location: "docs/features/{feature_name}/stories"

  # Common folders
  output_folder: "docs"
  test_folder: "tests"
  src_folder: "src"

  # Common settings
  date_format: "%Y-%m-%d"
  author: "GAO-Dev"
```

### Variable Naming Conventions

Follow these conventions for consistency:

- **Location variables**: `{type}_location` (e.g., `prd_location`, `story_location`)
- **Folder variables**: `{type}_folder` (e.g., `output_folder`, `test_folder`)
- **Path variables**: `{type}_path` (e.g., `template_path`, `config_path`)
- **Name variables**: `{type}_name` (e.g., `project_name`, `feature_name`)
- **ID variables**: `{type}_id` (e.g., `epic_id`, `story_id`)

Use `snake_case` for all variable names.

---

## Using Variables in Templates

### Template Syntax

Variables use **Mustache-style syntax**: `{{variable_name}}`

**Example instructions.md:**

```markdown
# Create Product Requirements Document

You are {{agent}} agent working on the {{project_name}} project.

## Task

Create a comprehensive Product Requirements Document (PRD) at the following location:

**Path:** {{prd_location}}

The PRD should be saved in the **{{output_folder}}** folder.

## Requirements

1. Document creation date: {{date}}
2. Project root: {{project_root}}
3. Epic number: {{epic}}
4. Story number: {{story}}

## Output

Save the PRD to: `{{prd_location}}`
```

**After variable resolution:**

```markdown
# Create Product Requirements Document

You are John agent working on the TodoApp project.

## Task

Create a comprehensive Product Requirements Document (PRD) at the following location:

**Path:** docs/PRD.md

The PRD should be saved in the **docs** folder.

## Requirements

1. Document creation date: 2025-11-07
2. Project root: /home/user/projects/TodoApp
3. Epic number: 1
4. Story number: 1

## Output

Save the PRD to: `docs/PRD.md`
```

### Conditional Rendering

For advanced use cases, you can use conditional blocks (if Mustache library supports):

```markdown
{{#has_epic}}
This story is part of Epic {{epic}}.
{{/has_epic}}

{{^has_epic}}
This is a standalone task.
{{/has_epic}}
```

### Nested Variables

Variables can reference other configuration values:

```yaml
variables:
  feature_folder:
    default: "docs/features/{{feature_name}}"
  story_location:
    default: "{{feature_folder}}/stories/epic-{{epic}}"
```

---

## Common Variables

The following variables are automatically available in all workflows:

### Timestamp Variables

```yaml
date: "2025-11-07"                    # Current date (YYYY-MM-DD)
timestamp: "2025-11-07T10:30:00Z"     # Current timestamp (ISO 8601)
year: "2025"                          # Current year
month: "11"                           # Current month
day: "07"                             # Current day
```

### Project Variables

```yaml
project_name: "TodoApp"                        # Project directory name
project_root: "/home/user/projects/TodoApp"    # Absolute path to project root
```

### Epic/Story Variables

```yaml
epic: "1"                             # Epic number (if executing story)
story: "2"                            # Story number (if executing story)
epic_num: "1"                         # Alias for epic
story_num: "2"                        # Alias for story
feature_name: "user-authentication"   # Feature name (from epic)
```

### Agent Variables

```yaml
agent: "John"                         # Current agent name
agent_role: "Product Manager"         # Agent's role
```

### Workflow Variables

```yaml
workflow: "prd"                       # Workflow name
workflow_phase: "planning"            # Workflow phase (analysis, planning, etc.)
workflow_description: "Create PRD"    # Workflow description
```

---

## Artifact Detection System

### Overview

The artifact detection system automatically identifies files created or modified during workflow execution and registers them with the DocumentLifecycleManager.

### How It Works

1. **Before Execution**: Create filesystem snapshot
   - Walk tracked directories (`docs/`, `src/`, `gao_dev/`)
   - Record: path, mtime, size for each file
   - Ignore: `.git/`, `node_modules/`, `__pycache__/`, `.gao-dev/`, `.archive/`

2. **Execute Workflow**: LLM creates/modifies files
   - WorkflowExecutor sends resolved instructions to LLM
   - LLM executes task and creates artifacts

3. **After Execution**: Create filesystem snapshot again
   - Same process as before

4. **Detect Changes**: Compare snapshots
   - **New files**: Files in after but not in before
   - **Modified files**: Files with different mtime or size

5. **Register Artifacts**: Register with DocumentLifecycleManager
   - Infer document type from workflow and path
   - Add metadata (workflow, epic, story, phase)
   - Track in `.gao-dev/documents.db`

### Tracked Directories

By default, the following directories are tracked:

```python
TRACKED_DIRS = [
    "docs/",           # Documentation
    "src/",            # Source code
    "gao_dev/",        # Internal files
    "tests/",          # Test files
    "config/",         # Configuration files
]
```

### Ignored Directories

The following directories are ignored for performance and correctness:

```python
IGNORED_DIRS = [
    ".git/",           # Git metadata
    "node_modules/",   # Node.js dependencies
    "__pycache__/",    # Python cache
    ".pytest_cache/",  # Pytest cache
    ".gao-dev/",       # Lifecycle database
    ".archive/",       # Archived files
    "venv/",           # Virtual environment
    ".venv/",          # Virtual environment
    "dist/",           # Distribution files
    "build/",          # Build artifacts
]
```

### Filesystem Snapshot Structure

```python
{
    "docs/PRD.md": {
        "path": "docs/PRD.md",
        "mtime": 1699372800.0,
        "size": 4096
    },
    "docs/ARCHITECTURE.md": {
        "path": "docs/ARCHITECTURE.md",
        "mtime": 1699372900.0,
        "size": 8192
    }
}
```

### Detection Algorithm

```python
def detect_artifacts(before_snapshot, after_snapshot):
    """
    Detect created and modified files.

    Returns:
        List of artifact paths
    """
    artifacts = []

    # Find new files
    for path in after_snapshot:
        if path not in before_snapshot:
            artifacts.append({
                "path": path,
                "change_type": "created"
            })

    # Find modified files
    for path in after_snapshot:
        if path in before_snapshot:
            before = before_snapshot[path]
            after = after_snapshot[path]

            # Check if modified (mtime or size changed)
            if before["mtime"] != after["mtime"] or before["size"] != after["size"]:
                artifacts.append({
                    "path": path,
                    "change_type": "modified"
                })

    return artifacts
```

### Performance Characteristics

- **Snapshot Time**: O(n) where n = number of tracked files
- **Detection Time**: O(m) where m = number of files in after snapshot
- **Overhead**: < 5% for typical projects (< 10,000 files)
- **Optimization**: Only walks tracked directories, ignores large dependency folders

---

## Document Lifecycle Integration

### Document Type Inference

Document types are inferred using the following logic:

1. **From Workflow Name** (primary):
   ```python
   WORKFLOW_TO_DOCTYPE = {
       "prd": "product-requirements",
       "architecture": "architecture",
       "epic": "epic",
       "dev-story": "story",
       "test-plan": "test-plan",
       "tech-spec": "technical-specification"
   }
   ```

2. **From File Path** (fallback):
   ```python
   PATH_TO_DOCTYPE = {
       "PRD.md": "product-requirements",
       "ARCHITECTURE.md": "architecture",
       "TEST_PLAN.md": "test-plan",
       "SPEC.md": "technical-specification"
   }
   ```

3. **Default**: `"document"`

### Author Determination

The author is determined as follows:

1. **From Workflow Metadata**: `workflow.agent` (e.g., "John")
2. **From Config**: `config.default_author` (e.g., "GAO-Dev")
3. **Default**: `"system"`

### Metadata Structure

Registered documents include rich metadata:

```python
{
    # Core metadata
    "document_type": "product-requirements",
    "author": "John",
    "created_at": "2025-11-07T10:30:00Z",

    # Workflow context
    "workflow": "prd",
    "epic": 1,
    "story": 1,
    "phase": "planning",
    "created_by_workflow": True,

    # Variable context
    "variables": {
        "prd_location": "docs/PRD.md",
        "output_folder": "docs",
        "project_name": "TodoApp"
    },

    # Change tracking
    "change_type": "created",  # or "modified"
    "previous_version": None   # For modified files
}
```

### Registration Process

```python
def register_artifact(path, workflow, resolved_vars):
    """
    Register an artifact with DocumentLifecycleManager.
    """
    # 1. Infer document type
    doc_type = infer_document_type(workflow.name, path)

    # 2. Determine author
    author = workflow.agent or config.default_author

    # 3. Build metadata
    metadata = {
        "workflow": workflow.name,
        "epic": resolved_vars.get("epic"),
        "story": resolved_vars.get("story"),
        "phase": workflow.phase,
        "created_by_workflow": True,
        "variables": resolved_vars
    }

    # 4. Register document
    doc_lifecycle.register_document(
        path=path,
        document_type=doc_type,
        author=author,
        metadata=metadata
    )
```

### Error Handling

If artifact registration fails:

1. **Log Error**: `artifact_registration_failed` event
2. **Continue Execution**: Don't fail workflow
3. **Notify User**: Warning in workflow results
4. **Retry**: Can manually register later using CLI

---

## Logging and Observability

### Log Events

The variable resolution system emits the following structured log events:

#### 1. workflow_variables_resolved

Emitted when variables are successfully resolved.

```json
{
  "event": "workflow_variables_resolved",
  "workflow": "prd",
  "variables": {
    "prd_location": "docs/PRD.md",
    "output_folder": "docs",
    "project_name": "TodoApp",
    "date": "2025-11-07"
  },
  "timestamp": "2025-11-07T10:30:00Z"
}
```

#### 2. workflow_instructions_rendered

Emitted when instructions template is rendered.

```json
{
  "event": "workflow_instructions_rendered",
  "workflow": "prd",
  "template_length": 1024,
  "rendered_length": 1156,
  "variables_used": ["prd_location", "output_folder", "project_name"],
  "timestamp": "2025-11-07T10:30:01Z"
}
```

#### 3. filesystem_snapshot_created

Emitted when filesystem snapshot is created.

```json
{
  "event": "filesystem_snapshot_created",
  "phase": "before",
  "file_count": 42,
  "tracked_dirs": ["docs/", "src/", "gao_dev/"],
  "timestamp": "2025-11-07T10:30:02Z"
}
```

#### 4. workflow_artifacts_detected

Emitted when artifacts are detected after execution.

```json
{
  "event": "workflow_artifacts_detected",
  "workflow": "prd",
  "artifacts": [
    {
      "path": "docs/PRD.md",
      "change_type": "created",
      "size": 4096
    }
  ],
  "timestamp": "2025-11-07T10:35:00Z"
}
```

#### 5. artifact_registered

Emitted when an artifact is successfully registered.

```json
{
  "event": "artifact_registered",
  "path": "docs/PRD.md",
  "document_type": "product-requirements",
  "author": "John",
  "workflow": "prd",
  "timestamp": "2025-11-07T10:35:01Z"
}
```

#### 6. artifact_registration_failed

Emitted when artifact registration fails.

```json
{
  "event": "artifact_registration_failed",
  "path": "docs/PRD.md",
  "error": "Document already exists",
  "workflow": "prd",
  "timestamp": "2025-11-07T10:35:01Z"
}
```

### Viewing Logs

Logs are emitted using structlog and can be viewed in multiple formats:

**Console (JSON):**
```bash
gao-dev create-prd --name "TodoApp" 2>&1 | jq 'select(.event == "workflow_variables_resolved")'
```

**Log File:**
```bash
tail -f .gao-dev/logs/workflow.log | grep "workflow_variables_resolved"
```

---

## Troubleshooting Guide

### Issue 1: Variable Not Resolved

**Symptom:**
```
LLM instructions contain: "Save to {{prd_location}}"
File created at wrong location: PRD.md (root) instead of docs/PRD.md
```

**Cause:**
Variable `prd_location` is not defined in workflow.yaml, config, or parameters.

**Solution:**

1. **Check workflow.yaml**:
   ```yaml
   variables:
     prd_location:
       default: "docs/PRD.md"
   ```

2. **Check config/defaults.yaml**:
   ```yaml
   workflow_defaults:
     prd_location: "docs/PRD.md"
   ```

3. **Pass as parameter**:
   ```bash
   gao-dev create-prd --prd-location "docs/PRD.md"
   ```

4. **Verify in logs**:
   ```bash
   gao-dev create-prd 2>&1 | jq 'select(.event == "workflow_variables_resolved")'
   ```

### Issue 2: File Created at Wrong Location

**Symptom:**
```
Expected: docs/PRD.md
Actual: PRD.md (in project root)
```

**Cause:**
- Variable resolved correctly, but LLM ignored instruction
- OR variable contains wrong value

**Solution:**

1. **Check resolved variables in logs**:
   ```json
   {
     "event": "workflow_variables_resolved",
     "variables": {
       "prd_location": "docs/PRD.md"  // Correct
     }
   }
   ```

2. **Check rendered instructions**:
   ```json
   {
     "event": "workflow_instructions_rendered",
     "rendered_length": 1156
   }
   ```

3. **Update instructions.md** to be more explicit:
   ```markdown
   **CRITICAL**: You MUST create the PRD file at this EXACT path:

   Path: {{prd_location}}

   DO NOT create it anywhere else.
   ```

### Issue 3: Artifact Not Detected

**Symptom:**
```
File created by LLM but not registered in .gao-dev/documents.db
No artifact_registered event in logs
```

**Cause:**
- File created outside tracked directories
- File created before snapshot (timing issue)
- File creation failed silently

**Solution:**

1. **Check if file exists**:
   ```bash
   ls -la docs/PRD.md
   ```

2. **Check tracked directories**:
   ```python
   TRACKED_DIRS = ["docs/", "src/", "gao_dev/"]
   # Is your file in one of these?
   ```

3. **Check artifact detection logs**:
   ```json
   {
     "event": "workflow_artifacts_detected",
     "artifacts": []  // Empty = nothing detected
   }
   ```

4. **Manual registration** (if needed):
   ```bash
   gao-dev lifecycle register docs/PRD.md product-requirements
   ```

### Issue 4: Required Variable Missing

**Symptom:**
```
Error: Required variable 'prd_location' not provided
Workflow execution failed
```

**Cause:**
Variable marked as `required: true` but not provided.

**Solution:**

1. **Provide via parameter**:
   ```bash
   gao-dev create-prd --prd-location "docs/PRD.md"
   ```

2. **Add default to workflow.yaml**:
   ```yaml
   variables:
     prd_location:
       default: "docs/PRD.md"
       required: true  # Now has default, won't fail
   ```

3. **Make optional** (if appropriate):
   ```yaml
   variables:
     prd_location:
       default: "docs/PRD.md"
       required: false
   ```

### Issue 5: Performance Degradation

**Symptom:**
```
Workflow execution slow (>10 seconds overhead)
High CPU during filesystem snapshot
```

**Cause:**
- Too many files in tracked directories
- Tracking directories with dependencies (node_modules/, venv/)

**Solution:**

1. **Check file count**:
   ```json
   {
     "event": "filesystem_snapshot_created",
     "file_count": 50000  // Too high!
   }
   ```

2. **Add to ignored directories**:
   ```python
   IGNORED_DIRS = [
       ".git/", "node_modules/", "__pycache__/",
       ".gao-dev/", ".archive/",
       "venv/", ".venv/", "dist/", "build/",
       "your_large_folder/"  // Add this
   ]
   ```

3. **Reduce tracked directories** (if appropriate):
   ```python
   TRACKED_DIRS = [
       "docs/",  # Only track docs
   ]
   ```

### Issue 6: Document Type Incorrect

**Symptom:**
```
Expected: document_type = "product-requirements"
Actual: document_type = "document"
```

**Cause:**
Document type inference failed.

**Solution:**

1. **Check workflow name mapping**:
   ```python
   WORKFLOW_TO_DOCTYPE = {
       "prd": "product-requirements",
       # Is your workflow in this mapping?
   }
   ```

2. **Update mapping** (if needed):
   ```python
   # In orchestrator or config
   WORKFLOW_TO_DOCTYPE["your-workflow"] = "your-document-type"
   ```

3. **Manual update** (if needed):
   ```bash
   # Update document type in database
   sqlite3 .gao-dev/documents.db
   UPDATE documents SET document_type = 'product-requirements' WHERE path = 'docs/PRD.md';
   ```

---

## Best Practices

### 1. Variable Naming

✅ **Good:**
```yaml
variables:
  prd_location: "docs/PRD.md"
  output_folder: "docs"
  test_folder: "tests"
```

❌ **Bad:**
```yaml
variables:
  PRDLocation: "docs/PRD.md"    # Use snake_case, not PascalCase
  output: "docs"                # Be specific: output_folder
  tests: "tests"                # Be specific: test_folder
```

### 2. Variable Defaults

✅ **Good:**
```yaml
variables:
  prd_location:
    description: "Location for PRD file"
    default: "docs/PRD.md"      # Sensible default
    required: false              # Allow override
```

❌ **Bad:**
```yaml
variables:
  prd_location:
    required: true               # No default, always required
```

### 3. Instruction Templates

✅ **Good:**
```markdown
Create a PRD at the following location:

**Path:** {{prd_location}}

IMPORTANT: You MUST create the file at this exact path.
```

❌ **Bad:**
```markdown
Create a PRD somewhere, maybe at {{prd_location}} or wherever.
```

### 4. Variable Organization

✅ **Good:**
```yaml
# Group related variables
variables:
  # File locations
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"

  # Folders
  output_folder: "docs"
  test_folder: "tests"

  # Settings
  author: "John"
  version: "1.0.0"
```

❌ **Bad:**
```yaml
variables:
  prd_location: "docs/PRD.md"
  author: "John"
  test_folder: "tests"
  architecture_location: "docs/ARCHITECTURE.md"
  # Random order, no grouping
```

### 5. Required vs. Optional

**Use `required: true` when:**
- Variable MUST be provided for workflow to work
- No sensible default exists
- Example: `project_name` for project creation

**Use `required: false` with default when:**
- Variable has a sensible default
- Most users will use the default
- Example: `prd_location` with default `"docs/PRD.md"`

**Use `required: false` without default when:**
- Variable is truly optional
- Workflow works without it
- Example: `template_path` for custom templates

### 6. Documentation

Always document your variables:

```yaml
variables:
  prd_location:
    description: "Location for PRD file. Must be in docs/ folder."
    default: "docs/PRD.md"
    required: false
```

### 7. Testing

Test variable resolution before deploying:

```bash
# Test with defaults
gao-dev create-prd --name "TestApp"

# Test with custom values
gao-dev create-prd --name "TestApp" --prd-location "documentation/PRD.md"

# Check logs
gao-dev create-prd --name "TestApp" 2>&1 | jq 'select(.event == "workflow_variables_resolved")'
```

---

## Related Documentation

- [Migration Guide - Epic 18](../../MIGRATION_GUIDE_EPIC_18.md)
- [Workflow Authoring Guide](./workflow-authoring-guide.md)
- [Document Lifecycle System](./README.md)
- [Epic 18: Workflow Variable Resolution](./epic-18-workflow-variable-resolution.md)

---

## Version History

- **1.0.0** (2025-11-07): Initial release with Epic 18
  - Variable resolution system
  - Artifact detection system
  - Document lifecycle integration

---

**Questions or issues?** Check the [Troubleshooting Guide](#troubleshooting-guide) or consult the [Migration Guide](../../MIGRATION_GUIDE_EPIC_18.md).
