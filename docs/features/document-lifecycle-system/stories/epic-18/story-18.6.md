# Story 18.6: Documentation and Migration

**Epic:** 18 - Workflow Variable Resolution and Artifact Tracking
**Story Points:** 3
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Create comprehensive documentation for the variable resolution and artifact tracking system, including architecture guides, migration instructions, and troubleshooting guides. This documentation is critical for users, contributors, and maintainers to understand how the system works, how to use it, and how to migrate existing workflows to take advantage of the new functionality.

---

## Business Value

This story enables adoption and maintenance:

- **User Enablement**: Clear documentation helps users leverage the new system
- **Migration Support**: Migration guide reduces friction for existing users
- **Troubleshooting**: Troubleshooting guide reduces support burden
- **Onboarding**: New contributors can understand architecture quickly
- **Knowledge Transfer**: Architecture documented for long-term maintenance
- **Best Practices**: Documentation codifies recommended patterns
- **Discoverability**: Examples show how to use features effectively
- **Compliance**: Documentation required for production deployment
- **Communication**: Explains what changed and why
- **Confidence**: Good documentation increases user confidence

---

## Acceptance Criteria

### Variable Resolution Documentation
- [ ] VARIABLE_RESOLUTION.md explains complete variable resolution flow
- [ ] Documentation includes architecture diagram showing new flow
- [ ] Examples show workflow.yaml variable definitions
- [ ] Template syntax clearly documented ({{mustache}} style)
- [ ] Variable priority order documented (params > workflow > config)
- [ ] Common variables documented (date, timestamp, project_name)
- [ ] Required vs. optional variables explained
- [ ] Default values and configuration documented

### Artifact Detection Documentation
- [ ] Artifact detection system explained with examples
- [ ] Tracked vs. ignored directories documented
- [ ] Snapshot mechanism explained
- [ ] Performance characteristics documented
- [ ] Logging examples provided

### Document Lifecycle Integration Documentation
- [ ] Document type inference rules documented
- [ ] Author determination logic explained
- [ ] Metadata structure documented
- [ ] Registration process explained
- [ ] Error handling behavior documented

### Migration Guide
- [ ] MIGRATION_GUIDE_EPIC_18.md lists all breaking changes
- [ ] Breaking changes explained clearly (variables now enforced)
- [ ] Migration guide provides step-by-step migration instructions
- [ ] Before/after examples show impact of changes
- [ ] Common migration scenarios covered
- [ ] Backward compatibility options explained

### Troubleshooting Guide
- [ ] Troubleshooting section covers common issues
- [ ] Variable resolution errors explained
- [ ] Artifact detection issues covered
- [ ] Document registration failures explained
- [ ] Log examples provided for debugging
- [ ] Solutions provided for each issue

### CLAUDE.md Updates
- [ ] CLAUDE.md updated with new architecture
- [ ] Architecture section shows variable resolution flow
- [ ] Orchestrator description includes artifact tracking
- [ ] Workflow variable conventions documented
- [ ] Troubleshooting section updated

### Code Examples
- [ ] All documentation has working code examples
- [ ] Examples tested and verified
- [ ] Examples follow best practices
- [ ] Examples cover common use cases

---

## Technical Notes

### Documentation Structure

**File:** `docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md` (new, ~400 LOC)

```markdown
# Workflow Variable Resolution System

## Overview

The workflow variable resolution system enables workflows to define variables in `workflow.yaml` files that are automatically resolved and used when rendering instructions for the LLM.

## Architecture

### Variable Resolution Flow

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

### Variable Sources and Priority

Variables are resolved from multiple sources with the following priority:

1. **Parameters** (highest priority) - Values passed to workflow execution
2. **Workflow YAML** - Defaults defined in workflow.yaml
3. **Config Defaults** - Defaults from `gao_dev/config/defaults.yaml`
4. **Common Variables** (lowest priority) - Auto-generated (date, timestamp, etc.)

## Defining Variables

### In workflow.yaml

```yaml
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
    required: true
```

### In Configuration

`gao_dev/config/defaults.yaml`:

```yaml
workflow_defaults:
  prd_location: "docs/PRD.md"
  architecture_location: "docs/ARCHITECTURE.md"
  output_folder: "docs"
```

## Using Variables in Templates

### Template Syntax

Variables use Mustache-style syntax: `{{variable_name}}`

**Example instructions.md:**

```markdown
# Create Product Requirements Document

Create a comprehensive PRD at the following location:

**Path:** {{prd_location}}

The PRD should be saved in the {{output_folder}} folder.
```

**After resolution:**

```markdown
# Create Product Requirements Document

Create a comprehensive PRD at the following location:

**Path:** docs/PRD.md

The PRD should be saved in the docs folder.
```

## Common Variables

These variables are automatically added to all workflows:

- `{{date}}` - Current date (YYYY-MM-DD)
- `{{timestamp}}` - Current timestamp (ISO 8601)
- `{{project_name}}` - Project directory name
- `{{project_root}}` - Absolute path to project root
- `{{epic}}` - Epic number
- `{{story}}` - Story number

## Artifact Detection

### How It Works

1. **Before Execution**: Snapshot filesystem (path, mtime, size) for all tracked files
2. **Execute Workflow**: LLM creates/modifies files
3. **After Execution**: Snapshot filesystem again
4. **Detect Changes**: Compare snapshots to find new/modified files
5. **Register Artifacts**: Register all detected artifacts with DocumentLifecycleManager

### Tracked Directories

- `docs/` - Documentation
- `src/` - Source code
- `gao_dev/` - Internal files

### Ignored Directories

- `.git/` - Git metadata
- `node_modules/` - Dependencies
- `__pycache__/` - Python cache
- `.gao-dev/` - Lifecycle database
- `.archive/` - Archived files

## Document Registration

### Document Type Inference

Document types are inferred from:

1. **Workflow name** (primary): `prd` → `product-requirements`
2. **File path** (fallback): `docs/PRD.md` → `product-requirements`
3. **Default**: `document`

### Metadata

Registered documents include:

```python
{
    "workflow": "prd",
    "epic": 1,
    "story": 1,
    "phase": "planning",
    "created_by_workflow": True,
    "variables": {
        "prd_location": "docs/PRD.md",
        "output_folder": "docs"
    }
}
```

## Troubleshooting

### Variable Not Resolved

**Symptom**: `{{variable}}` appears in LLM instructions

**Cause**: Variable not defined in workflow.yaml, config, or params

**Solution**: Add variable to one of these sources

### File Created at Wrong Location

**Symptom**: File created at root instead of docs/

**Cause**: Variable not resolved or LLM ignored instruction

**Solution**: Check logs for `workflow_variables_resolved` event

### Artifact Not Detected

**Symptom**: File created but not registered

**Cause**: File outside tracked directories or created before snapshot

**Solution**: Ensure file in tracked directory, check timing

## Logging

### Log Events

- `workflow_variables_resolved` - Variables resolved successfully
- `workflow_instructions_rendered` - Template rendered
- `workflow_artifacts_detected` - Artifacts detected
- `artifact_registered` - Artifact registered successfully
- `artifact_registration_failed` - Registration failed

### Example Logs

```json
{
  "event": "workflow_variables_resolved",
  "workflow": "prd",
  "variables": {
    "prd_location": "docs/PRD.md",
    "output_folder": "docs"
  }
}
```
```

**File:** `docs/MIGRATION_GUIDE_EPIC_18.md` (new, ~300 LOC)

```markdown
# Migration Guide - Epic 18: Variable Resolution and Artifact Tracking

## Overview

Epic 18 introduces a significant architectural change to how workflows execute. Variables defined in workflow.yaml files are now properly resolved before sending instructions to the LLM, and all workflow artifacts are automatically tracked.

## What Changed

### Before Epic 18

❌ Variables sent raw to LLM: `{{prd_location}}`
❌ Files created at wrong locations (PRD.md in root)
❌ No artifact tracking or document registration

### After Epic 18

✅ Variables resolved: `{{prd_location}}` → `docs/PRD.md`
✅ Files created at correct locations
✅ All artifacts tracked in `.gao-dev/documents.db`

## Breaking Changes

### 1. Variables Are Now Enforced

**Before**: Variables like `{{prd_location}}` were sent to LLM as-is
**After**: Variables MUST be defined or workflow will fail

**Migration**: Add all used variables to workflow.yaml or config

### 2. File Locations Must Match Variables

**Before**: LLM could create files anywhere
**After**: Files should be created at resolved variable locations

**Migration**: Ensure workflow instructions use resolved variables

## Migration Steps

### Step 1: Review Workflow Variables

Check your workflow.yaml files for variable usage:

```bash
grep -r "{{" gao_dev/workflows/
```

### Step 2: Define Missing Variables

Add variables to workflow.yaml:

```yaml
variables:
  prd_location:
    default: "docs/PRD.md"
  output_folder:
    default: "docs"
```

### Step 3: Update Configuration

Add common defaults to `gao_dev/config/defaults.yaml`.

### Step 4: Test Workflows

Run workflows and verify:
- Variables resolved correctly
- Files created at correct locations
- Artifacts registered in database

## Common Migration Scenarios

### Scenario 1: PRD Workflow

**Before**:
```markdown
Create a PRD at {{prd_location}}
```

**Issue**: `prd_location` not defined

**Solution**:
```yaml
# workflow.yaml
variables:
  prd_location:
    default: "docs/PRD.md"
```

### Scenario 2: Story Workflow

**Before**: Stories created at arbitrary locations

**After**: Stories created at `dev_story_location`

**Solution**:
```yaml
# defaults.yaml
workflow_defaults:
  dev_story_location: "docs/stories"
```

## Backward Compatibility

### Option 1: Use Config Defaults

Add all common variables to `defaults.yaml` to maintain existing behavior.

### Option 2: Update Workflows

Update workflow.yaml files to explicitly define variables.

### Option 3: Feature Flag (if implemented)

Disable variable enforcement (not recommended for production).

## Verification

After migration, verify:

1. ✅ All workflows execute successfully
2. ✅ Files created at expected locations
3. ✅ Variables resolved in logs
4. ✅ Artifacts registered in database
5. ✅ No errors in execution

## Rollback Plan

If issues occur:

1. Revert to pre-Epic 18 commit
2. Review errors in logs
3. Fix variable definitions
4. Retry migration

## Support

For issues, check:

- [VARIABLE_RESOLUTION.md](features/document-lifecycle-system/VARIABLE_RESOLUTION.md)
- [Troubleshooting Guide](features/document-lifecycle-system/VARIABLE_RESOLUTION.md#troubleshooting)
- Logs: `workflow_variables_resolved`, `artifact_registered`
```

---

## Dependencies

- Stories 18.1, 18.2, 18.3 must be complete
- Architecture finalized
- All functionality working

---

## Tasks

### Implementation Tasks
- [ ] Create VARIABLE_RESOLUTION.md with complete guide
- [ ] Add architecture diagram to documentation
- [ ] Create code examples for all use cases
- [ ] Create MIGRATION_GUIDE_EPIC_18.md
- [ ] Document all breaking changes
- [ ] Provide step-by-step migration instructions
- [ ] Create before/after examples
- [ ] Update CLAUDE.md architecture section
- [ ] Update CLAUDE.md orchestrator description
- [ ] Add workflow variable conventions to CLAUDE.md
- [ ] Update troubleshooting section
- [ ] Add new log events to logging guide
- [ ] Create troubleshooting examples

### Documentation Tasks
- [ ] Review all documentation for accuracy
- [ ] Ensure all code examples work
- [ ] Verify all links are correct
- [ ] Check formatting and style
- [ ] Add table of contents where appropriate
- [ ] Add cross-references between documents

### Validation Tasks
- [ ] Have users review documentation
- [ ] Test migration guide with real workflows
- [ ] Verify troubleshooting guide solves common issues
- [ ] Ensure documentation matches implementation
- [ ] Get documentation approved

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] All tasks completed
- [ ] VARIABLE_RESOLUTION.md created and comprehensive
- [ ] MIGRATION_GUIDE_EPIC_18.md created with clear instructions
- [ ] CLAUDE.md updated with new architecture
- [ ] All code examples tested and working
- [ ] Documentation reviewed and approved
- [ ] No broken links or formatting issues
- [ ] Migration guide validated with real workflows
- [ ] Troubleshooting guide tested
- [ ] Merged to feature branch

---

## Files to Create

1. `docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md` (new, ~400 LOC)
   - Architecture overview
   - Variable resolution flow
   - Usage examples
   - Artifact detection explanation
   - Document registration explanation
   - Troubleshooting guide

2. `docs/MIGRATION_GUIDE_EPIC_18.md` (new, ~300 LOC)
   - What changed and why
   - Breaking changes list
   - Migration steps
   - Common scenarios
   - Backward compatibility
   - Verification steps

---

## Files to Modify

1. `CLAUDE.md` (~50 LOC changes)
   - Update architecture section with variable resolution flow
   - Update orchestrator description with artifact tracking
   - Add workflow variable conventions section
   - Update troubleshooting with new issues
   - Add links to new documentation

2. `docs/workflow-authoring-guide.md` (if exists, ~30 LOC additions)
   - Add variables section
   - Document variable naming conventions
   - Explain required vs. optional variables
   - Show examples of variable definitions

---

## Success Metrics

- **Completeness**: All aspects of system documented
- **Clarity**: Users can understand and use system from docs alone
- **Accuracy**: Documentation matches implementation 100%
- **Examples**: All examples work as shown
- **Usability**: Migration guide successfully used by users
- **Discoverability**: Users can find answers to common questions

---

## Risk Assessment

**Risks:**
- Documentation might become outdated as code changes
- Examples might not work due to code changes
- Migration guide might miss edge cases
- Users might not read documentation

**Mitigations:**
- Link documentation to code version
- Test all examples as part of CI/CD
- Gather user feedback on migration guide
- Keep documentation concise and scannable
- Use clear headings and table of contents
- Provide quick start guide for impatient users

---

## Notes

- Documentation is as important as code for this epic
- Keep documentation concise but comprehensive
- Use diagrams where they add clarity
- Provide working examples for all major features
- Migration guide critical for smooth rollout
- Consider adding video walkthrough for complex topics
- Keep troubleshooting guide up-to-date with real issues
- Cross-reference related documentation
- Use consistent terminology throughout
- Consider adding FAQ section

---

**Created:** 2025-11-07
**Last Updated:** 2025-11-07
**Author:** Bob (Scrum Master)
