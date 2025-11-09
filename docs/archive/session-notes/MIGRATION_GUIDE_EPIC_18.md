# Migration Guide - Epic 18: Variable Resolution and Artifact Tracking

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Status:** Production Ready

---

## Table of Contents

- [Overview](#overview)
- [What Changed](#what-changed)
- [Breaking Changes](#breaking-changes)
- [Migration Steps](#migration-steps)
- [Common Migration Scenarios](#common-migration-scenarios)
- [Backward Compatibility](#backward-compatibility)
- [Verification](#verification)
- [Rollback Plan](#rollback-plan)
- [FAQ](#faq)
- [Support](#support)

---

## Overview

Epic 18 introduces a **critical architectural change** to how workflows are executed in GAO-Dev. This change fixes a fundamental bug where workflow variables defined in `workflow.yaml` files were not being resolved before sending instructions to the LLM, causing files to be created at incorrect locations and losing artifact tracking.

### Why This Migration Matters

Before Epic 18, the orchestrator bypassed the `WorkflowExecutor`, which meant:
- Variables like `{{prd_location}}` were sent raw to the LLM
- LLMs ignored these variables and created files in arbitrary locations
- No tracking of created artifacts
- No integration with DocumentLifecycleManager
- Project conventions were not enforced

After Epic 18, these issues are fixed, but existing workflows may need updates to be compatible.

---

## What Changed

### Before Epic 18

The old execution flow had critical flaws:

```
[workflow.yaml defines: prd_location="docs/PRD.md"]
         ↓
[Orchestrator loads instructions.md RAW]  ← BYPASSES WorkflowExecutor
         ↓
[Only replaces hardcoded: {epic}, {story}, {{epic_num}}, {{story_num}}]
         ↓
[Sends "Path: {{prd_location}}" to LLM]  ← Variable NOT resolved!
         ↓
[LLM ignores variable, creates PRD.md in root]  ← Wrong location
         ↓
[No artifact detection or document registration]  ← Lost tracking
```

**Problems:**
- ❌ Variables sent raw to LLM: `{{prd_location}}`
- ❌ Files created at wrong locations (PRD.md in root instead of docs/)
- ❌ No artifact tracking or document registration
- ❌ LLMs frequently ignored unresolved variable placeholders
- ❌ Project structure conventions not enforced
- ❌ No metadata captured for created documents

### After Epic 18

The new execution flow properly resolves variables:

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

**Benefits:**
- ✅ Variables resolved before sending to LLM: `{{prd_location}}` → `docs/PRD.md`
- ✅ Files created at correct locations
- ✅ All artifacts tracked in `.gao-dev/documents.db`
- ✅ Document lifecycle properly maintained
- ✅ Project conventions enforced
- ✅ Rich metadata captured for all documents

---

## Breaking Changes

### 1. Variables Are Now Enforced

**Before:** Variables like `{{prd_location}}` were sent to LLM as-is, and the LLM would either ignore them or create files in arbitrary locations.

**After:** Variables MUST be defined in one of these locations:
- `workflow.yaml` (recommended)
- `config/defaults.yaml`
- Runtime parameters

**Impact:** If a workflow uses `{{variable}}` but doesn't define it, execution will fail with a clear error message.

**Migration Required:** ✅ Yes

### 2. File Locations Must Match Variables

**Before:** LLMs could create files anywhere, regardless of variables.

**After:** Files should be created at locations specified by resolved variables. The artifact detection system validates this.

**Impact:** Workflows that rely on LLMs creating files at arbitrary locations may fail.

**Migration Required:** ✅ Yes

### 3. Artifact Detection Is Automatic

**Before:** No automatic artifact detection or registration.

**After:** All files created/modified during workflow execution are automatically detected and registered.

**Impact:**
- All artifacts now tracked in `.gao-dev/documents.db`
- Document lifecycle events triggered automatically
- May discover files that were previously untracked

**Migration Required:** ⚠️ Maybe (review tracked files)

### 4. WorkflowExecutor Integration

**Before:** Orchestrator directly loaded and sent instructions.

**After:** Orchestrator uses `WorkflowExecutor` for variable resolution and template rendering.

**Impact:** Minimal for users, but affects custom orchestrator implementations.

**Migration Required:** ✅ Yes (for custom orchestrators)

### 5. Logging Changes

**Before:** Basic workflow execution logging.

**After:** Comprehensive structured logging with new events:
- `workflow_variables_resolved`
- `workflow_instructions_rendered`
- `filesystem_snapshot_created`
- `workflow_artifacts_detected`
- `artifact_registered`
- `artifact_registration_failed`

**Impact:** Log files will contain more events. Log parsing tools may need updates.

**Migration Required:** ⚠️ Maybe (if you parse logs)

---

## Migration Steps

### Step 1: Review Workflow Variables

First, identify all variables used in your workflows:

```bash
# Search for all {{variable}} usage in workflow files
grep -r "{{" gao_dev/workflows/ --include="*.md"

# Example output:
# gao_dev/workflows/2-plan/prd/instructions.md:Path: {{prd_location}}
# gao_dev/workflows/2-plan/architecture/instructions.md:Save to: {{architecture_location}}
```

### Step 2: Define Missing Variables

For each variable found, ensure it's defined in one of these locations:

#### Option A: In workflow.yaml (Recommended)

```yaml
# gao_dev/workflows/2-plan/prd/workflow.yaml
name: prd
description: "Create Product Requirements Document"
phase: planning
agent: john

variables:
  prd_location:
    description: "Location for PRD file"
    default: "docs/PRD.md"
    required: false

  output_folder:
    description: "Output folder for documentation"
    default: "docs"
    required: false
```

#### Option B: In config/defaults.yaml (For Global Defaults)

```yaml
# gao_dev/config/defaults.yaml
workflow_defaults:
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  epic_location: "docs/epics"
  dev_story_location: "docs/features/{feature_name}/stories"
  output_folder: "docs"
  test_folder: "tests"
  src_folder: "src"
```

### Step 3: Update Configuration

Add global defaults to `config/defaults.yaml`:

```bash
# Edit config/defaults.yaml
vim gao_dev/config/defaults.yaml
```

Add workflow defaults:

```yaml
workflow_defaults:
  # Common locations
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  epic_location: "docs/epics"
  dev_story_location: "docs/features/{feature_name}/stories/epic-{epic}"

  # Common folders
  output_folder: "docs"
  test_folder: "tests"
  src_folder: "src"
  config_folder: "config"

  # Common settings
  author: "GAO-Dev"
  version: "1.0.0"
```

### Step 4: Test Workflows

Test each workflow to verify variables are resolved correctly:

```bash
# Test PRD workflow
gao-dev create-prd --name "TestProject"

# Check logs for variable resolution
gao-dev create-prd --name "TestProject" 2>&1 | jq 'select(.event == "workflow_variables_resolved")'

# Expected output:
# {
#   "event": "workflow_variables_resolved",
#   "workflow": "prd",
#   "variables": {
#     "prd_location": "docs/PRD.md",
#     "output_folder": "docs",
#     "project_name": "TestProject",
#     "date": "2025-11-07"
#   }
# }
```

### Step 5: Verify Artifact Detection

Verify that artifacts are being detected and registered:

```bash
# Run workflow
gao-dev create-prd --name "TestProject"

# Check for artifact detection logs
gao-dev create-prd --name "TestProject" 2>&1 | jq 'select(.event == "workflow_artifacts_detected")'

# Expected output:
# {
#   "event": "workflow_artifacts_detected",
#   "workflow": "prd",
#   "artifacts": [
#     {
#       "path": "docs/PRD.md",
#       "change_type": "created",
#       "size": 4096
#     }
#   ]
# }

# Verify in database
gao-dev lifecycle list

# Expected output:
# ID  Path          Type                    Author  Created
# 1   docs/PRD.md   product-requirements    John    2025-11-07 10:30:00
```

### Step 6: Update Custom Code

If you have custom orchestrators or workflow executors:

**Before:**
```python
# Custom orchestrator (old way)
instructions = workflow_registry.load_instructions(workflow_name)
instructions = instructions.replace("{{epic}}", str(epic))
result = agent.execute(instructions)
```

**After:**
```python
# Custom orchestrator (new way)
from gao_dev.core.workflow_executor import WorkflowExecutor

workflow_executor = WorkflowExecutor(workflow_registry, config)

# Resolve variables
params = {"epic": epic, "story": story, "project_name": project_name}
resolved_vars = workflow_executor.resolve_variables(workflow_name, params)

# Render template
instructions = workflow_executor.render_template(workflow_name, resolved_vars)

# Execute
result = agent.execute(instructions)
```

---

## Common Migration Scenarios

### Scenario 1: PRD Workflow

**Before Epic 18:**

```yaml
# workflow.yaml (old)
name: prd
description: "Create Product Requirements Document"
phase: planning
agent: john
# No variables section
```

```markdown
<!-- instructions.md (old) -->
Create a PRD at {{prd_location}}
```

**Problem:** `prd_location` not defined, sent raw to LLM, PRD created at wrong location.

**After Epic 18:**

```yaml
# workflow.yaml (new)
name: prd
description: "Create Product Requirements Document"
phase: planning
agent: john

variables:
  prd_location:
    description: "Location for PRD file"
    default: "docs/PRD.md"
    required: false
```

**Result:** `{{prd_location}}` → `docs/PRD.md`, PRD created at correct location.

---

### Scenario 2: Story Creation Workflow

**Before Epic 18:**

```yaml
# workflow.yaml (old)
name: dev-story
description: "Create development story"
phase: implementation
agent: bob
# No variables section
```

**Problem:** Stories created at arbitrary locations, no tracking.

**After Epic 18:**

```yaml
# workflow.yaml (new)
name: dev-story
description: "Create development story"
phase: implementation
agent: bob

variables:
  dev_story_location:
    description: "Base location for story files"
    default: "docs/features/{feature_name}/stories/epic-{epic}"
    required: false

  story_template:
    description: "Template for story file"
    default: "story-{epic}.{story}.md"
    required: false
```

**Result:** Stories created at consistent locations, automatically tracked.

---

### Scenario 3: Architecture Workflow

**Before Epic 18:**

```yaml
# workflow.yaml (old)
name: architecture
description: "Create system architecture"
phase: solutioning
agent: winston
# No variables section
```

**After Epic 18:**

```yaml
# workflow.yaml (new)
name: architecture
description: "Create system architecture"
phase: solutioning
agent: winston

variables:
  architecture_location:
    description: "Location for architecture document"
    default: "docs/ARCHITECTURE.md"
    required: false

  diagram_folder:
    description: "Folder for architecture diagrams"
    default: "docs/diagrams"
    required: false
```

**Result:** Architecture docs created at correct location, diagrams in dedicated folder.

---

### Scenario 4: Custom Workflow with Required Variables

**Use Case:** Workflow that MUST have certain variables provided.

```yaml
# workflow.yaml
name: custom-deploy
description: "Deploy to custom environment"
phase: implementation
agent: amelia

variables:
  deploy_target:
    description: "Deployment target environment"
    required: true  # No default, MUST be provided

  deploy_config:
    description: "Path to deployment config"
    default: "config/deploy.yaml"
    required: false
```

**Usage:**

```bash
# This will FAIL (missing required variable)
gao-dev run-workflow custom-deploy

# Error: Required variable 'deploy_target' not provided

# This will SUCCEED
gao-dev run-workflow custom-deploy --deploy-target "production"
```

---

## Backward Compatibility

### Compatibility Options

Epic 18 maintains backward compatibility through several mechanisms:

#### 1. Config Defaults (Recommended)

Add all common variables to `config/defaults.yaml` to maintain existing behavior:

```yaml
# config/defaults.yaml
workflow_defaults:
  # Add defaults for all commonly used variables
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  epic_location: "docs/epics"
  dev_story_location: "docs/features/{feature_name}/stories"
  # ... etc
```

**Pros:**
- ✅ Minimal changes to workflow.yaml files
- ✅ Consistent defaults across all workflows
- ✅ Easy to update globally

**Cons:**
- ⚠️ Less explicit (defaults hidden in config)
- ⚠️ Workflow-specific overrides require workflow.yaml updates

#### 2. Update Workflows (Best Practice)

Update each workflow.yaml file to explicitly define variables:

```yaml
# Each workflow.yaml
variables:
  prd_location:
    default: "docs/PRD.md"
```

**Pros:**
- ✅ Explicit and self-documenting
- ✅ Workflow-specific defaults
- ✅ Easier to understand and maintain

**Cons:**
- ⚠️ More work to update all workflows
- ⚠️ Duplication if same defaults used everywhere

#### 3. Hybrid Approach (Balanced)

Use config for common defaults, override in workflow.yaml when needed:

```yaml
# config/defaults.yaml (common defaults)
workflow_defaults:
  output_folder: "docs"
  test_folder: "tests"

# workflow.yaml (workflow-specific overrides)
variables:
  prd_location:
    default: "docs/PRD.md"  # Specific to PRD workflow
```

**Pros:**
- ✅ Balance between DRY and explicitness
- ✅ Common defaults centralized
- ✅ Workflow-specific customization

**Cons:**
- ⚠️ Need to check both locations to understand defaults

### Legacy Variable Handling

For variables not defined anywhere, the system will:

1. **Log a warning**: `variable_not_resolved` event
2. **Use empty string**: `{{undefined_var}}` → `""`
3. **Continue execution**: Don't fail workflow (for now)

**Future versions may require all variables to be defined.**

---

## Verification

After migration, verify the following:

### Checklist

- [ ] ✅ All workflows execute successfully
- [ ] ✅ Files created at expected locations
- [ ] ✅ Variables resolved in logs (`workflow_variables_resolved` events)
- [ ] ✅ Artifacts detected in logs (`workflow_artifacts_detected` events)
- [ ] ✅ Artifacts registered in database (check `gao-dev lifecycle list`)
- [ ] ✅ No errors in workflow execution
- [ ] ✅ Document types correctly inferred
- [ ] ✅ Metadata captured for all documents
- [ ] ✅ Performance acceptable (<5% overhead)

### Verification Commands

```bash
# 1. Test PRD workflow
gao-dev create-prd --name "VerificationTest"

# 2. Check variable resolution
gao-dev create-prd --name "VerificationTest" 2>&1 | jq 'select(.event == "workflow_variables_resolved")'

# 3. Check artifact detection
gao-dev create-prd --name "VerificationTest" 2>&1 | jq 'select(.event == "workflow_artifacts_detected")'

# 4. List tracked documents
gao-dev lifecycle list

# 5. Verify file at correct location
ls -la docs/PRD.md

# 6. Check document metadata in database
sqlite3 .gao-dev/documents.db "SELECT * FROM documents WHERE path = 'docs/PRD.md';"
```

### Expected Results

**Variable Resolution:**
```json
{
  "event": "workflow_variables_resolved",
  "workflow": "prd",
  "variables": {
    "prd_location": "docs/PRD.md",
    "output_folder": "docs",
    "project_name": "VerificationTest",
    "date": "2025-11-07"
  }
}
```

**Artifact Detection:**
```json
{
  "event": "workflow_artifacts_detected",
  "workflow": "prd",
  "artifacts": [
    {
      "path": "docs/PRD.md",
      "change_type": "created"
    }
  ]
}
```

**Lifecycle List:**
```
ID  Path          Type                    Author  Created
1   docs/PRD.md   product-requirements    John    2025-11-07 10:30:00
```

---

## Rollback Plan

If you encounter issues after migration, follow this rollback procedure:

### Step 1: Identify the Issue

```bash
# Check recent logs
tail -100 .gao-dev/logs/workflow.log

# Look for errors
grep ERROR .gao-dev/logs/workflow.log

# Check specific events
grep "workflow_variables_resolved" .gao-dev/logs/workflow.log
```

### Step 2: Determine Scope

**Minor issues** (single workflow):
- Fix variable definitions in workflow.yaml
- Retest workflow
- No rollback needed

**Major issues** (system-wide):
- Consider rollback to pre-Epic 18 version
- File bug report with logs
- Use workaround until fixed

### Step 3: Rollback Procedure

```bash
# 1. Check git history
git log --oneline | head -20

# 2. Find commit before Epic 18
# Look for: "feat(epic-18): ..." commits

# 3. Create rollback branch
git checkout -b rollback-epic-18

# 4. Revert to pre-Epic 18 commit
git revert <commit-hash-of-epic-18>

# 5. Test system
gao-dev create-prd --name "RollbackTest"

# 6. If working, merge rollback
git checkout main
git merge rollback-epic-18
```

### Step 4: Report Issue

When reporting issues, include:

1. **Error message**: Full error output
2. **Logs**: Relevant log events
3. **Workflow config**: workflow.yaml content
4. **Variables**: Variable definitions
5. **Expected vs. Actual**: What you expected vs. what happened
6. **Steps to reproduce**: Minimal reproduction case

### Step 5: Investigate Root Cause

Common root causes:

1. **Missing variable definition**: Add to workflow.yaml or config
2. **Typo in variable name**: `{{prd_location}}` vs. `{{prd_loc}}`
3. **Incorrect default value**: Check default makes sense
4. **Path issues**: Check paths are valid for your OS
5. **Performance issues**: Check file count in tracked directories

---

## FAQ

### Q1: Do I need to update all workflows at once?

**A:** No. You can migrate workflows incrementally. Workflows without variable definitions will use config defaults or log warnings.

### Q2: What happens if a variable is not defined?

**A:** Currently, the system logs a warning and uses an empty string. Future versions may enforce variable definitions.

### Q3: Can I disable artifact detection?

**A:** Not currently. Artifact detection is a core feature of Epic 18. If you have performance concerns, see [Troubleshooting: Performance](features/document-lifecycle-system/VARIABLE_RESOLUTION.md#issue-5-performance-degradation).

### Q4: How do I debug variable resolution issues?

**A:** Check logs for `workflow_variables_resolved` events. These show exactly which variables were resolved and their values.

### Q5: Can I use nested variables?

**A:** Yes, in some cases. Example: `feature_folder: "docs/features/{{feature_name}}"`. However, deep nesting is not recommended.

### Q6: What if my workflow uses dynamic paths?

**A:** Use variables with parameters. Example:
```yaml
variables:
  story_location:
    default: "docs/features/{feature_name}/stories/epic-{epic}/story-{story}.md"
```

### Q7: How do I override a config default?

**A:** Define the variable in workflow.yaml or pass as runtime parameter. Both override config defaults.

### Q8: Are there performance implications?

**A:** Minimal (<5% overhead). Artifact detection uses efficient filesystem snapshots. See [Performance](features/document-lifecycle-system/VARIABLE_RESOLUTION.md#performance-characteristics).

### Q9: Can I customize tracked directories?

**A:** Not currently configurable via workflow.yaml, but you can modify `TRACKED_DIRS` in the codebase if needed.

### Q10: What about Windows vs. Unix paths?

**A:** Use forward slashes (`/`) in all paths. Python's `Path` class handles OS-specific conversion automatically.

---

## Support

### Resources

- **Variable Resolution Guide**: [VARIABLE_RESOLUTION.md](features/document-lifecycle-system/VARIABLE_RESOLUTION.md)
- **Epic 18 Documentation**: [epic-18-workflow-variable-resolution.md](features/document-lifecycle-system/epic-18-workflow-variable-resolution.md)
- **Troubleshooting**: [VARIABLE_RESOLUTION.md#troubleshooting-guide](features/document-lifecycle-system/VARIABLE_RESOLUTION.md#troubleshooting-guide)
- **Test Report**: [TEST_REPORT_EPIC_18.md](features/document-lifecycle-system/TEST_REPORT_EPIC_18.md)

### Getting Help

1. **Check Logs**: Review structured logs for variable resolution events
2. **Check Documentation**: Read [VARIABLE_RESOLUTION.md](features/document-lifecycle-system/VARIABLE_RESOLUTION.md)
3. **Check Examples**: See [Common Migration Scenarios](#common-migration-scenarios)
4. **File Issue**: If you find a bug, file an issue with logs and reproduction steps

### Reporting Issues

When reporting issues, include:

```bash
# Capture full output
gao-dev create-prd --name "ReproTest" 2>&1 | tee issue-report.log

# Include system info
gao-dev --version
python --version
uname -a  # or "ver" on Windows
```

Attach `issue-report.log` to your issue report.

---

## Version History

- **1.0.0** (2025-11-07): Initial release with Epic 18
  - Variable resolution system migration
  - Artifact detection migration
  - Breaking changes documentation

---

**Questions?** Consult the [Variable Resolution Guide](features/document-lifecycle-system/VARIABLE_RESOLUTION.md) or [FAQ](#faq).

**Ready to migrate?** Follow the [Migration Steps](#migration-steps).

**Need help?** Check [Support](#support) resources.
