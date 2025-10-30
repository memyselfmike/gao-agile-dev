# Story 6.8: Migrate from Legacy Models

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Remove `legacy_models.py` and migrate all 8 files that import from it to use the new models in `core/models/`.

---

## User Story

**As a** GAO-Dev architect
**I want** all legacy model duplicates removed
**So that** there's one source of truth for models

---

## Acceptance Criteria

1. **Health Models Migrated**
   - [ ] Move `HealthStatus`, `CheckResult`, `HealthCheckResult` into `health_check.py`
   - [ ] Update `core/health_check.py` to use local models
   - [ ] Remove from `legacy_models.py`

2. **WorkflowInfo Migration**
   - [ ] Verify `core/models/workflow.py::WorkflowInfo` has all features
   - [ ] Update 5 files to import from `core/models/workflow`:
     - `orchestrator/models.py`
     - `orchestrator/brian_orchestrator.py`
     - `core/workflow_registry.py`
     - `core/workflow_executor.py`
     - `core/strategies/workflow_strategies.py`
   - [ ] Remove `WorkflowInfo` from `legacy_models.py`

3. **StoryStatus Migration**
   - [ ] Verify `core/models/story.py::StoryStatus` matches legacy
   - [ ] Update `core/state_manager.py` import
   - [ ] Remove `StoryStatus` from `legacy_models.py`

4. **AgentInfo Migration**
   - [ ] Verify `core/models/agent.py::AgentInfo` matches legacy
   - [ ] Find all usages (if any)
   - [ ] Update imports
   - [ ] Remove `AgentInfo` from `legacy_models.py`

5. **Delete Legacy File**
   - [ ] Verify `legacy_models.py` is empty
   - [ ] Delete `gao_dev/core/legacy_models.py`
   - [ ] Remove from `core/__init__.py` exports
   - [ ] Remove from git

6. **Testing**
   - [ ] All imports resolve correctly
   - [ ] All tests pass
   - [ ] No references to legacy_models remain
   - [ ] Type checking passes (mypy)

---

## Technical Details

### Files to Update

1. **orchestrator/models.py**
   ```python
   # BEFORE
   from ..core.legacy_models import WorkflowInfo

   # AFTER
   from ..core.models.workflow import WorkflowInfo
   ```

2. **orchestrator/brian_orchestrator.py**
   ```python
   # BEFORE
   from ..core.legacy_models import WorkflowInfo

   # AFTER
   from ..core.models.workflow import WorkflowInfo
   ```

3. **core/state_manager.py**
   ```python
   # BEFORE
   from .legacy_models import StoryStatus

   # AFTER
   from .models.story import StoryStatus
   ```

4. **core/health_check.py**
   ```python
   # BEFORE
   from .legacy_models import HealthStatus, CheckResult, HealthCheckResult

   # AFTER
   # Define these enums/classes locally in health_check.py
   # OR keep in models/health.py if that makes sense
   ```

5. **core/workflow_registry.py**
   ```python
   # BEFORE
   from .legacy_models import WorkflowInfo

   # AFTER
   from .models.workflow import WorkflowInfo
   ```

6. **core/workflow_executor.py**
   ```python
   # BEFORE
   from .legacy_models import WorkflowInfo

   # AFTER
   from .models.workflow import WorkflowInfo
   ```

7. **core/strategies/workflow_strategies.py**
   ```python
   # BEFORE
   from ..legacy_models import WorkflowInfo

   # AFTER
   from ..models.workflow import WorkflowInfo
   ```

8. **core/__init__.py**
   ```python
   # BEFORE
   from .legacy_models import (
       StoryStatus as LegacyStoryStatus,
       ...
   )

   # AFTER
   # Remove all legacy imports and exports
   ```

### Verification Commands

```bash
# Find any remaining references
grep -r "from.*legacy_models" gao_dev/
grep -r "import.*legacy_models" gao_dev/

# Should return no results
```

---

## Implementation Steps

1. **Move Health Models**
   - Copy models to `health_check.py` or create `models/health.py`
   - Update import in `health_check.py`
   - Test health check functionality

2. **Update WorkflowInfo Imports** (5 files)
   - Change import statements one file at a time
   - Run tests after each change
   - Verify no breakage

3. **Update StoryStatus Import** (1 file)
   - Change import in `state_manager.py`
   - Run tests

4. **Update AgentInfo Import** (if used)
   - Search for usages
   - Update imports
   - Run tests

5. **Clean up core/__init__.py**
   - Remove legacy exports
   - Update tests if any rely on these exports

6. **Delete Legacy File**
   - Verify file is empty or unused
   - `git rm gao_dev/core/legacy_models.py`
   - Commit with message

7. **Final Verification**
   - Run full test suite
   - Run type checker (mypy)
   - Search for any missed references

---

## Definition of Done

- [ ] All 8 files updated with new imports
- [ ] `legacy_models.py` deleted
- [ ] All tests pass
- [ ] Type checking passes
- [ ] No grep results for "legacy_models"
- [ ] Git commit: "refactor: remove legacy_models.py, migrate to core/models"
- [ ] Code reviewed

---

## Risks & Mitigation

**Risk**: Missing a reference causes runtime error
**Mitigation**:
- Search thoroughly before deleting
- Update one file at a time
- Run tests after each change
- Use IDE "Find All References" feature

**Risk**: Models not fully compatible
**Mitigation**:
- Compare old and new models field-by-field
- Add any missing fields to new models
- Write tests for model serialization

---

**Related Stories**: All previous stories (services use these models)
**Estimated Time**: 1 day
**Critical**: Removes technical debt and confusion
