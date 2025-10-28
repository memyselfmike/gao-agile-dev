# Story 7.1.1 Debug Notes - ConfigLoader Error

**Error**: `argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'ConfigLoader'`

**When**: Phase-based benchmark (greenfield-simple.yaml) fails immediately after "phase_based_workflow_started" log

**Location**: Somewhere in WorkflowOrchestrator initialization or early execution

## Investigation Done

1. Checked runner.py line 465: `project_path = self.sandbox_root / "projects" / project.name` - Looks correct
2. Checked runner.py line 487: Passes `project_path` to WorkflowOrchestrator - Looks correct
3. Checked orchestrator.py line 119: `self.project_path = Path(project_path)` - Should convert to Path

## Likely Issue

The error "ConfigLoader" suggests somewhere a config object is being passed where a Path is expected.

Possibilities:
1. **self.config vs project_path confusion** - Somewhere passing self.config instead of a path
2. **Config loading issue** - ConfigLoader not being converted to actual config object
3. **Hidden parameter** - Some method receiving config when it expects path

## Next Steps to Debug

1. **Add detailed logging** before WorkflowOrchestrator init:
```python
# In runner.py before line 487
self.logger.debug("project_path_type", type=type(project_path), value=str(project_path))
self.logger.debug("config_type", type=type(self.config))
```

2. **Check ConfigLoader usage** - Search for where ConfigLoader is instantiated and how it's used

3. **Add try/except with traceback**:
```python
try:
    orchestrator = WorkflowOrchestrator(...)
except Exception as e:
    import traceback
    self.logger.error("orchestrator_init_failed", error=str(e), traceback=traceback.format_exc())
    raise
```

4. **Check if config.phases returns ConfigLoader** - Maybe self.config.phases is a ConfigLoader not a list?

## Quick Test

Run with verbose logging to get full traceback:
```bash
python -c "
import traceback
import sys
try:
    from pathlib import Path
    # Try to recreate the error
    from gao_dev.core.config_loader import ConfigLoader
    loader = ConfigLoader()
    Path(loader)  # This should trigger the error
except Exception as e:
    traceback.print_exc()
"
```

## Most Likely Fix

Somewhere in the code, we're passing `self.config` or `config` object where we should be passing `project_path`. Search for any place where:
- WorkflowOrchestrator is initialized
- GAODevOrchestrator is initialized
- ArtifactParser is initialized
- GitCommitManager is initialized
- Any Path() constructor is called with a config parameter

And verify they're receiving Path objects, not config objects.

## Time Estimate

Once we have the full traceback: 15-30 minutes to fix

---

## RESOLUTION (2025-10-28)

### Root Cause Found

**File**: `gao_dev/sandbox/git_commit_manager.py:36`
**Error**: Passing `ConfigLoader` object as positional argument to `GitManager`

Full traceback:
```
File "gao_dev/sandbox/benchmark/runner.py", line 504
  orchestrator = WorkflowOrchestrator(...)
File "gao_dev/sandbox/benchmark/orchestrator.py", line 139
  self.git_commit_manager = GitCommitManager(project_root=self.project_path, run_id=self.run_id)
File "gao_dev/sandbox/git_commit_manager.py", line 36
  self.git_manager = GitManager(config)  # <-- BUG HERE
File "gao_dev/core/git_manager.py", line 59
  self.project_path = Path(project_path).resolve()
TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'ConfigLoader'
```

### The Bug

In `git_commit_manager.py`:
```python
# WRONG:
from ..core import ConfigLoader
config = ConfigLoader(self.project_root)
self.git_manager = GitManager(config)  # Passes ConfigLoader as first positional arg (project_path)
```

`GitManager.__init__` signature:
```python
def __init__(self, project_path: Optional[Path] = None, config_loader: Optional[Any] = None):
```

By passing `config` as a positional argument, it was being interpreted as `project_path` instead of `config_loader`.

### The Fix

Changed to pass `project_root` directly (sandbox/agent mode doesn't need ConfigLoader):

```python
# CORRECT:
self.git_manager = GitManager(project_path=self.project_root)
```

### Test Results

After fix:
```
2025-10-28 20:09:16 [debug] workflow_orchestrator_created
2025-10-28 20:09:16 [debug] executing_workflow phases_count=4
2025-10-28 20:09:16 [info] phase_execution_started phase_name='Product Requirements'
2025-10-28 20:09:16 [info] executing_phase_with_gao_orchestrator agent=John
```

Phase-based workflow now initializes successfully and begins execution.

### Status

**FIXED** - Story 7.1.1 complete
