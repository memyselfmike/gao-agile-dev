# Story 40.1: Environment Detection

## User Story

As a developer,
I want GAO-Dev to automatically detect my runtime environment (Docker, SSH, WSL, Desktop, CI/CD),
So that it can provide the appropriate onboarding experience without manual configuration.

## Acceptance Criteria

- [ ] AC1: Detects Docker environment via `/.dockerenv` file or `$GAO_DEV_DOCKER` environment variable
- [ ] AC2: Detects SSH session via `$SSH_CLIENT` or `$SSH_TTY` environment variables
- [ ] AC3: Detects WSL via `/proc/version` containing "Microsoft" or "WSL"
- [ ] AC4: Detects VS Code Remote via `$VSCODE_IPC_HOOK_CLI` environment variable
- [ ] AC5: Detects desktop GUI via `$DISPLAY` (Linux/macOS) or Windows platform
- [ ] AC6: Detects CI/CD via `$CI`, `$GITHUB_ACTIONS`, `$GITLAB_CI`, or `$GAO_DEV_HEADLESS`
- [ ] AC7: Returns `EnvironmentType` enum with values: `DESKTOP`, `SSH`, `CONTAINER`, `WSL`, `REMOTE_DEV`, `HEADLESS`
- [ ] AC8: Explicit overrides via `$GAO_DEV_HEADLESS` or `$GAO_DEV_GUI` take precedence over detection
- [ ] AC9: Detection completes in <50ms
- [ ] AC10: Falls back to `HEADLESS` when no environment can be determined (safe default)

## Technical Notes

### Implementation Details

Create `gao_dev/core/environment_detector.py`:

```python
from enum import Enum
from pathlib import Path
import os
import sys

class EnvironmentType(Enum):
    DESKTOP = "desktop"
    SSH = "ssh"
    CONTAINER = "container"
    WSL = "wsl"
    REMOTE_DEV = "remote_dev"
    HEADLESS = "headless"

def detect_environment() -> EnvironmentType:
    """Detect runtime environment with priority-based checks."""
    # Implementation per Architecture doc
```

### Detection Priority Order

1. Explicit overrides (`$GAO_DEV_HEADLESS`, `$GAO_DEV_GUI`)
2. CI/CD environment variables
3. Container markers (`.dockerenv`)
4. Remote development (SSH, VS Code Remote)
5. WSL detection
6. Desktop detection
7. Default to HEADLESS

### Platform-Specific Considerations

- **Windows**: Always has GUI capability, check for `$DISPLAY` only on Unix
- **Linux**: Check both `$DISPLAY` and `$WAYLAND_DISPLAY`
- **macOS**: Check `$DISPLAY` for X11 forwarding scenarios

### Dependencies

- No external dependencies (uses standard library only)
- `pathlib.Path` for file checks
- `os.getenv` for environment variables
- `sys.platform` for platform detection

## Test Scenarios

1. **Docker detection**: Given `/.dockerenv` exists, When `detect_environment()` is called, Then returns `EnvironmentType.CONTAINER`

2. **SSH detection**: Given `$SSH_CLIENT` is set, When `detect_environment()` is called, Then returns `EnvironmentType.SSH`

3. **WSL detection**: Given `/proc/version` contains "Microsoft", When `detect_environment()` is called, Then returns `EnvironmentType.WSL`

4. **Desktop detection (Windows)**: Given platform is `win32`, When `detect_environment()` is called, Then returns `EnvironmentType.DESKTOP`

5. **Desktop detection (Linux)**: Given `$DISPLAY` is set, When `detect_environment()` is called, Then returns `EnvironmentType.DESKTOP`

6. **CI/CD detection**: Given `$CI=true`, When `detect_environment()` is called, Then returns `EnvironmentType.HEADLESS`

7. **Explicit override**: Given `$GAO_DEV_HEADLESS=1`, When `detect_environment()` is called, Then returns `EnvironmentType.HEADLESS` regardless of other signals

8. **Priority test**: Given both `$SSH_CLIENT` and `$GAO_DEV_GUI=1` are set, When `detect_environment()` is called, Then returns `EnvironmentType.DESKTOP` (override wins)

9. **Performance test**: Given any environment, When `detect_environment()` is called 1000 times, Then average time is <1ms per call

10. **Unknown environment**: Given no environment signals present, When `detect_environment()` is called, Then returns `EnvironmentType.HEADLESS`

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for each environment type
- [ ] Performance benchmarks pass (<50ms)
- [ ] Code reviewed
- [ ] Documentation updated with detection matrix
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- None (this is a foundational story)

## Notes

- Use `structlog` for logging detection results
- Consider caching detection result since environment doesn't change during process lifetime
- Document all environment variables in README for users to understand override options
