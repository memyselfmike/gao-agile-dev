# Story 20.6: Documentation and Migration

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev developer or user
**I want** updated documentation explaining the project-scoped architecture
**So that** I understand how document lifecycle works and can migrate existing projects

---

## Acceptance Criteria

### AC1: CLAUDE.md Updated

- ✅ Project structure section shows `.gao-dev/` in project directories
- ✅ Document lifecycle section explains project-scoped architecture
- ✅ Commands section shows project detection behavior
- ✅ Examples use project-scoped paths
- ✅ Quick reference updated

### AC2: Plugin Development Guide Updated

- ✅ Plugin examples show project-scoped usage
- ✅ Document lifecycle integration explained
- ✅ Project root parameter usage documented
- ✅ Best practices for multi-project support

### AC3: Migration Guide Created

- ✅ New file: `docs/MIGRATION_GUIDE_EPIC_20.md`
- ✅ Explains changes from centralized to project-scoped
- ✅ Step-by-step migration instructions
- ✅ Handling existing `.gao-dev/` directory
- ✅ FAQ section for common issues

### AC4: Benchmark Documentation Updated

- ✅ Benchmark guide explains project-scoped tracking
- ✅ Examples show `.gao-dev/` in project output
- ✅ Metrics section includes document lifecycle operations
- ✅ Success criteria include document tracking

### AC5: README Updates

- ✅ Main README.md mentions project-scoped architecture
- ✅ Feature highlights include document lifecycle
- ✅ Quick start shows `.gao-dev/` initialization
- ✅ Links to detailed documentation

---

## Technical Details

### Files to Update

```
gao-agile-dev/
├── CLAUDE.md                              # UPDATE: Project guide
├── README.md                              # UPDATE: Main readme
├── docs/
│   ├── MIGRATION_GUIDE_EPIC_20.md         # NEW: Migration guide
│   ├── plugin-development-guide.md        # UPDATE: Plugin guide
│   └── features/
│       └── sandbox-system/
│           └── sandbox-autonomous-benchmark-guide.md  # UPDATE: Benchmark guide
```

### Implementation Approach

**Step 1: Create Migration Guide**

Create `docs/MIGRATION_GUIDE_EPIC_20.md`:

```markdown
# Migration Guide: Epic 20 - Project-Scoped Document Lifecycle

**Version**: 1.0.0
**Date**: 2025-11-06
**Epic**: Epic 20 - Project-Scoped Document Lifecycle

---

## Overview

Epic 20 refactors the document lifecycle system from a GAO-Dev-global
system to a project-scoped system. This guide explains the changes and
how to migrate existing projects.

---

## What Changed

### Before Epic 20 (Incorrect)

```
gao-agile-dev/                     # GAO-Dev repo
├── .gao-dev/
│   └── documents.db               # WRONG: All projects shared this
└── sandbox/projects/
    └── my-app/
        └── docs/                  # Documents here, tracked globally
```

**Problem**: All projects shared one database in the GAO-Dev repo.

### After Epic 20 (Correct)

```
sandbox/projects/my-app/           # Project root
├── .gao-dev/                      # Project-specific GAO-Dev data
│   └── documents.db               # Document lifecycle (PROJECT-SCOPED)
├── .archive/                      # Project-specific archived docs
└── docs/                          # Live documentation
    ├── PRD.md
    └── ARCHITECTURE.md
```

**Benefit**: Each project has its own isolated document tracking.

---

## Who Needs to Migrate

### Scenario 1: New Projects (No Action Needed)

If you're creating new projects after Epic 20:
- ✅ `gao-dev sandbox init` automatically creates `.gao-dev/`
- ✅ Document lifecycle is project-scoped by default
- ✅ No migration needed

### Scenario 2: Existing Sandbox Projects (Recommended)

If you have existing sandbox projects created before Epic 20:
- Projects may not have `.gao-dev/` directory
- Document tracking was in GAO-Dev's global database
- **Action**: Re-initialize document lifecycle (see below)

### Scenario 3: GAO-Dev Development (Optional)

If you were using document lifecycle for GAO-Dev itself:
- Old `.gao-dev/documents.db` in GAO-Dev repo is orphaned
- **Action**: Can be safely deleted or ignored

---

## Migration Steps

### Step 1: Identify Projects to Migrate

List all sandbox projects:

```bash
gao-dev sandbox list
```

### Step 2: Initialize Document Lifecycle

For each project, initialize project-scoped lifecycle:

```bash
# Option A: Using Python API
from pathlib import Path
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle

project_dir = Path("sandbox/projects/my-app")
doc_manager = ProjectDocumentLifecycle.initialize(project_dir)
```

```bash
# Option B: Using CLI (if supported)
gao-dev sandbox init my-app  # Re-runs initialization
```

### Step 3: Verify Initialization

Check that `.gao-dev/` was created:

```bash
ls -la sandbox/projects/my-app/.gao-dev/
# Should show: documents.db
```

### Step 4: Re-register Documents (If Needed)

If you had documents tracked in the old global database:

```bash
cd sandbox/projects/my-app
gao-dev lifecycle register docs/PRD.md product-requirements
gao-dev lifecycle register docs/ARCHITECTURE.md architecture
# ... register other documents
```

### Step 5: Test Commands

Verify lifecycle commands work:

```bash
cd sandbox/projects/my-app
gao-dev lifecycle list
# Should show project-specific documents
```

---

## Breaking Changes

### Change 1: Database Location

**Before**:
```python
db_path = Path.cwd() / ".gao-dev" / "documents.db"  # GAO-Dev repo
```

**After**:
```python
db_path = project_root / ".gao-dev" / "documents.db"  # Project directory
```

**Impact**: CLI commands now operate on project-specific databases.

### Change 2: CLI Behavior

**Before**:
```bash
# Always used GAO-Dev's .gao-dev/
gao-dev lifecycle list  # Showed all projects' documents
```

**After**:
```bash
# Auto-detects current project
cd sandbox/projects/my-app
gao-dev lifecycle list  # Shows only my-app's documents

# Or explicit targeting
gao-dev lifecycle list --project sandbox/projects/other-app
```

**Impact**: Commands are project-aware and must be run from within
a project or with `--project` option.

### Change 3: Orchestrator Integration

**Before**:
```python
orchestrator = GAODevOrchestrator()  # Used global lifecycle
```

**After**:
```python
orchestrator = GAODevOrchestrator(project_root=Path("sandbox/projects/my-app"))
# Uses project-scoped lifecycle
```

**Impact**: Must provide `project_root` to orchestrator for correct
document tracking.

---

## Common Issues

### Issue 1: "Document lifecycle not initialized"

**Symptom**:
```
Error: Document lifecycle not initialized for project: my-app
```

**Solution**:
```python
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
ProjectDocumentLifecycle.initialize(Path("sandbox/projects/my-app"))
```

### Issue 2: Commands operating on wrong project

**Symptom**: Lifecycle commands show wrong project's documents

**Solution**: Ensure you're in the correct directory or use `--project`:
```bash
cd sandbox/projects/my-app  # Change to project
# OR
gao-dev lifecycle list --project sandbox/projects/my-app
```

### Issue 3: Old `.gao-dev/` in GAO-Dev repo

**Symptom**: Leftover `.gao-dev/documents.db` in GAO-Dev root

**Solution**: Safe to delete:
```bash
rm -rf .gao-dev/  # In GAO-Dev repo root (NOT in projects!)
```

---

## FAQ

**Q: Do I need to migrate existing projects?**

A: Only if you want to use document lifecycle features. New features
like benchmarking will automatically initialize `.gao-dev/`.

**Q: What happens to old document tracking data?**

A: It remains in GAO-Dev's old `.gao-dev/documents.db` but is not
used. You can safely delete it or export data if needed.

**Q: Can I have projects without `.gao-dev/`?**

A: Yes, but document lifecycle commands will fail. Initialize when
you need document tracking.

**Q: How do I know if a project is initialized?**

A: Check for `.gao-dev/documents.db`:
```bash
ls sandbox/projects/my-app/.gao-dev/documents.db
```

**Q: Will this affect my existing projects' code?**

A: No, this only affects document tracking metadata. Your project
code is not touched.

---

## Testing Migration

### Test 1: Create New Project

```bash
gao-dev sandbox init test-migration
ls -la sandbox/projects/test-migration/.gao-dev/
# Should see: documents.db
```

### Test 2: Register Document

```bash
cd sandbox/projects/test-migration
echo "# Test" > docs/TEST.md
gao-dev lifecycle register docs/TEST.md test-doc
gao-dev lifecycle list
# Should show: TEST.md
```

### Test 3: Multiple Projects Isolated

```bash
# Create two projects
gao-dev sandbox init project-a
gao-dev sandbox init project-b

# Register in project-a
cd sandbox/projects/project-a
gao-dev lifecycle register docs/A.md test

# Verify project-b unaffected
cd ../project-b
gao-dev lifecycle list
# Should show: No documents found
```

---

## Rollback (If Needed)

If you encounter issues and need to rollback:

1. **Revert Code**:
   ```bash
   git checkout <commit-before-epic-20>
   ```

2. **Restore Old Database**:
   ```bash
   # If you backed it up
   cp .gao-dev/documents.db.backup .gao-dev/documents.db
   ```

3. **Contact Maintainers**: Report issues for investigation

---

## Support

For questions or issues:
- Check this guide's FAQ section
- Review Epic 20 documentation
- Contact: [Your support channel]

---

**Last Updated**: 2025-11-06
**Epic**: 20 - Project-Scoped Document Lifecycle
```

**Step 2: Update CLAUDE.md**

Add to "Project Structure" section:

```markdown
### Project-Scoped Architecture

Each project managed by GAO-Dev has its own `.gao-dev/` directory:

```
sandbox/projects/my-app/          # Project root
├── .gao-dev/                     # Project-specific GAO-Dev data
│   ├── documents.db              # Document lifecycle tracking
│   ├── context.json              # Execution context
│   └── metrics/                  # Project metrics
├── .archive/                     # Archived documents
├── docs/                         # Live documentation
├── src/                          # Application code
└── tests/                        # Test suite
```

**Key Points**:
- Each project is isolated
- Documentation context persists across sessions
- `.gao-dev/` can be moved with the project
- Same structure for all project types
```

Add to "Available Commands" section:

```markdown
### Document Lifecycle Commands

```bash
gao-dev lifecycle list                    # List documents (auto-detects project)
gao-dev lifecycle list --project <path>   # List for specific project
gao-dev lifecycle register <path> <type>  # Register document
gao-dev lifecycle update <path>           # Update document
gao-dev lifecycle archive <path>          # Archive document
gao-dev lifecycle restore <path>          # Restore document
```

**Note**: Commands auto-detect project root by searching for `.gao-dev/`
or `.sandbox.yaml`. You can override with `--project` option.
```

**Step 3: Update Plugin Development Guide**

Add section on project-scoped usage:

```markdown
## Working with Project-Scoped Document Lifecycle

### Overview

The document lifecycle system is project-scoped. Each project has its
own `.gao-dev/documents.db` for tracking documentation.

### Using in Plugins

```python
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle

class MyPlugin(BasePlugin):
    def on_project_created(self, project_root: Path):
        """Initialize document lifecycle for new project."""
        doc_manager = ProjectDocumentLifecycle.initialize(project_root)

        # Register plugin-specific documents
        doc_manager.registry.register_document(
            path="docs/PLUGIN_CONFIG.md",
            doc_type="plugin-config",
            metadata={"plugin": "my-plugin"}
        )
```

### Best Practices

1. **Always Use Project Root**: Pass `project_root` to all operations
2. **Check Initialization**: Use `is_initialized()` before operations
3. **Handle Failures**: Lifecycle init can fail, handle gracefully
4. **Project Isolation**: Never mix data between projects
```

**Step 4: Update Benchmark Guide**

Add section explaining document tracking in benchmarks:

```markdown
## Document Lifecycle Tracking in Benchmarks

### Overview

Benchmarks automatically track all documentation created during runs
in the project's `.gao-dev/documents.db`.

### What Gets Tracked

- PRD.md (product requirements)
- ARCHITECTURE.md (system architecture)
- Story files (story-X.Y.md)
- Any documents created by agents

### Viewing Tracked Documents

After a benchmark run:

```bash
cd sandbox/projects/workflow-driven-todo
gao-dev lifecycle list

# Output:
# Project: workflow-driven-todo
# Found 15 document(s):
#   docs/PRD.md (product-requirements)
#   docs/ARCHITECTURE.md (architecture)
#   docs/features/stories/story-1.1.md (story)
#   ...
```

### Metrics

Document lifecycle operations are tracked in metrics:
- Number of documents created
- Document types distribution
- Registration/update/archive operations
```

**Step 5: Update Main README.md**

Add to features section:

```markdown
### Project-Scoped Document Lifecycle

- Each project has isolated `.gao-dev/` directory
- Documentation tracked throughout lifecycle
- Context persists across sessions
- Automatic registration during workflows
- CLI commands for document management
```

---

## Testing Approach

### Documentation Review Checklist

- [ ] CLAUDE.md: Reviewed and updated
- [ ] README.md: Features section updated
- [ ] Migration guide: Created and comprehensive
- [ ] Plugin guide: Updated with examples
- [ ] Benchmark guide: Document tracking explained
- [ ] All links working
- [ ] Code examples tested
- [ ] No broken references

### Manual Testing

1. **Follow Migration Guide**: Step through guide as a user
2. **Test Examples**: Run all code examples in documentation
3. **Check Links**: Verify all cross-references work
4. **Review Clarity**: Ensure explanations are clear

---

## Dependencies

### Required Packages
- None (documentation only)

### Code Dependencies
- All stories in Epic 20 (documentation reflects implemented features)

---

## Definition of Done

- [ ] CLAUDE.md updated with project-scoped architecture
- [ ] README.md features section updated
- [ ] Migration guide created (`docs/MIGRATION_GUIDE_EPIC_20.md`)
- [ ] Plugin development guide updated
- [ ] Benchmark guide updated
- [ ] All code examples tested
- [ ] Documentation review completed
- [ ] Links and cross-references verified
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 20.1: Create ProjectDocumentLifecycle Factory Class
- Story 20.2: Update SandboxManager Integration
- Story 20.3: Update Orchestrator Integration
- Story 20.4: Add Project Root Detection
- Story 20.5: Update Lifecycle CLI Commands

**Blocks**: None (final story in epic)

---

## Notes

### Documentation Priorities

1. **High Priority**: CLAUDE.md, Migration Guide
2. **Medium Priority**: Plugin Guide, Benchmark Guide
3. **Low Priority**: README.md

### Key Messages

- Each project is isolated
- Context persists across sessions
- CLI commands auto-detect project
- Migration is straightforward
- New projects work automatically

### Writing Style

- Clear and concise
- Examples for every concept
- Step-by-step instructions
- Visual diagrams where helpful
- FAQ for common issues

---

## Acceptance Testing

### Test Case 1: Follow Migration Guide

**Action**: Step through migration guide as new user

**Expected**: Can successfully migrate a project without errors

### Test Case 2: Test Code Examples

**Action**: Copy/paste all code examples from docs

**Expected**: All examples execute without errors

### Test Case 3: Verify Cross-References

**Action**: Click all links in documentation

**Expected**: All links resolve correctly

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1 day

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*
