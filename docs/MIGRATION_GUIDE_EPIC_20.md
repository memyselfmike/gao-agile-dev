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

If you had documents tracked in the old global database, you can re-register them:

```python
from pathlib import Path
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle

project_dir = Path("sandbox/projects/my-app")
doc_manager = ProjectDocumentLifecycle.initialize(project_dir)

# Re-register documents
doc_manager.registry.register_document("docs/PRD.md", "product-requirements")
doc_manager.registry.register_document("docs/ARCHITECTURE.md", "architecture")
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
