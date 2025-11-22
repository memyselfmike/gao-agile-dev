# Story 40.2: Global and Project State Detection

## User Story

As a developer,
I want GAO-Dev to detect my user history (first-time vs returning) and project context (empty, brownfield, existing),
So that it can skip unnecessary onboarding steps and provide a contextually appropriate experience.

## Acceptance Criteria

- [ ] AC1: Detects global state as `FIRST_TIME` when `~/.gao-dev/` directory does not exist
- [ ] AC2: Detects global state as `RETURNING` when `~/.gao-dev/config.yaml` exists and is valid
- [ ] AC3: Detects project state as `EMPTY` when current directory has no files (excluding hidden)
- [ ] AC4: Detects project state as `BROWNFIELD` when directory has code files but no `.gao-dev/`
- [ ] AC5: Detects project state as `GAO_DEV_PROJECT` when `.gao-dev/` directory exists
- [ ] AC6: Brownfield detection recognizes common project indicators: `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `Makefile`
- [ ] AC7: Returns `GlobalState` and `ProjectState` enums with appropriate values
- [ ] AC8: Detection completes in <50ms for typical project sizes (<1000 files)
- [ ] AC9: Handles permission errors gracefully (treats as non-existent)
- [ ] AC10: Works correctly when run from any subdirectory (searches up for `.gao-dev/`)

## Technical Notes

### Implementation Details

Create `gao_dev/core/state_detector.py`:

```python
from enum import Enum
from pathlib import Path
from typing import Tuple

class GlobalState(Enum):
    FIRST_TIME = "first_time"
    RETURNING = "returning"

class ProjectState(Enum):
    EMPTY = "empty"
    BROWNFIELD = "brownfield"
    GAO_DEV_PROJECT = "gao_dev_project"

def detect_global_state() -> GlobalState:
    """Detect user's global GAO-Dev state."""
    pass

def detect_project_state(project_path: Path) -> ProjectState:
    """Detect project context in given directory."""
    pass

def detect_states(project_path: Optional[Path] = None) -> Tuple[GlobalState, ProjectState]:
    """Detect both global and project states."""
    pass
```

### Project Indicator Files

Brownfield detection should check for:
- JavaScript/Node: `package.json`, `yarn.lock`, `package-lock.json`
- Python: `requirements.txt`, `setup.py`, `pyproject.toml`, `Pipfile`
- Rust: `Cargo.toml`
- Go: `go.mod`
- Java: `pom.xml`, `build.gradle`, `build.gradle.kts`
- C#: `*.csproj`, `*.sln`
- Ruby: `Gemfile`
- Generic: `Makefile`, `CMakeLists.txt`, `README.md`

### Global Config Location

- Unix: `~/.gao-dev/config.yaml`
- Windows: `%USERPROFILE%\.gao-dev\config.yaml`

### Performance Considerations

- Use `os.scandir()` instead of `glob` for faster directory scanning
- Stop scanning after finding first indicator file
- Cache results within same process

## Test Scenarios

1. **First-time user**: Given no `~/.gao-dev/` exists, When `detect_global_state()` is called, Then returns `GlobalState.FIRST_TIME`

2. **Returning user**: Given `~/.gao-dev/config.yaml` exists with valid content, When `detect_global_state()` is called, Then returns `GlobalState.RETURNING`

3. **Empty directory**: Given current directory has no files, When `detect_project_state()` is called, Then returns `ProjectState.EMPTY`

4. **Brownfield Node project**: Given directory contains `package.json`, When `detect_project_state()` is called, Then returns `ProjectState.BROWNFIELD`

5. **Brownfield Python project**: Given directory contains `requirements.txt`, When `detect_project_state()` is called, Then returns `ProjectState.BROWNFIELD`

6. **Existing GAO-Dev project**: Given directory contains `.gao-dev/`, When `detect_project_state()` is called, Then returns `ProjectState.GAO_DEV_PROJECT`

7. **Subdirectory detection**: Given `.gao-dev/` exists in parent directory, When `detect_project_state()` is called from subdirectory, Then returns `ProjectState.GAO_DEV_PROJECT`

8. **Permission error handling**: Given directory exists but is not readable, When `detect_project_state()` is called, Then returns `ProjectState.EMPTY` without raising exception

9. **Corrupted config**: Given `~/.gao-dev/config.yaml` exists but is invalid YAML, When `detect_global_state()` is called, Then returns `GlobalState.FIRST_TIME` and logs warning

10. **Combined detection**: Given returning user in brownfield project, When `detect_states()` is called, Then returns `(GlobalState.RETURNING, ProjectState.BROWNFIELD)`

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests with real filesystem
- [ ] Performance benchmarks pass (<50ms)
- [ ] Code reviewed
- [ ] Documentation updated with state matrix
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 40.1: Environment Detection (for EnvironmentType context)

## Notes

- Consider using `platformdirs` library for cross-platform config paths
- Log detected states at DEBUG level for troubleshooting
- Empty directory detection should ignore hidden files like `.git/`
- Handle symlinks appropriately (follow them for file detection)
