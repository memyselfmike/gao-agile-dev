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
