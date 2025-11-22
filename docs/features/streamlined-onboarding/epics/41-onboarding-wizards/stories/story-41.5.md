# Story 41.5: Onboarding State Persistence and Recovery

## User Story

As a developer who was interrupted during onboarding,
I want to resume from where I left off,
So that I don't have to re-enter information I already provided.

## Acceptance Criteria

- [ ] AC1: Onboarding state saved to `~/.gao-dev/onboarding_state.yaml` after each step
- [ ] AC2: State includes: completed steps, step data, timestamp, project path
- [ ] AC3: On startup, detects incomplete onboarding and offers to resume
- [ ] AC4: Resume prompt shows which steps are complete and what's next
- [ ] AC5: User can choose to resume, start fresh, or cancel
- [ ] AC6: Resume loads all previous step data correctly
- [ ] AC7: State file is cleaned up after successful completion
- [ ] AC8: State file older than 24 hours prompts "expired" warning
- [ ] AC9: Handles corrupted state file gracefully (offers start fresh)
- [ ] AC10: Project path in state must match current directory to offer resume
- [ ] AC11: Atomic file writes prevent partial state corruption
- [ ] AC12: State file has user-only permissions (600)

## Technical Notes

### Implementation Details

Create `gao_dev/core/onboarding_state.py`:

```python
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import yaml

class OnboardingStateManager:
    """Persist onboarding progress for recovery."""

    STATE_FILE = "onboarding_state.yaml"
    EXPIRY_HOURS = 24

    def __init__(self, config_path: Path):
        self.state_file = config_path / self.STATE_FILE

    def save_step(self, step: str, data: Dict[str, Any]) -> None:
        """Save progress after completing a step."""
        state = self._load_state()
        state['steps_completed'].append(step)
        state['step_data'][step] = data
        state['last_updated'] = datetime.utcnow().isoformat()
        self._save_state(state)

    def can_resume(self, project_path: Path) -> bool:
        """Check if there's valid incomplete onboarding to resume."""
        if not self.state_file.exists():
            return False

        state = self._load_state()

        # Check not completed
        if state.get('completed', False):
            return False

        # Check same project
        if state.get('project_path') != str(project_path):
            return False

        # Check not expired
        last_updated = datetime.fromisoformat(state['last_updated'])
        if datetime.utcnow() - last_updated > timedelta(hours=self.EXPIRY_HOURS):
            return False

        return True

    def is_expired(self) -> bool:
        """Check if state is older than expiry threshold."""
        pass

    def resume(self) -> Tuple[str, Dict[str, Any]]:
        """Get the next step and accumulated data."""
        pass

    def clear(self) -> None:
        """Remove state file after completion."""
        pass
```

### State File Format

```yaml
version: "1.0"
completed: false
project_path: "/Users/alex/my-app"
steps_completed:
  - project
  - git
step_data:
  project:
    name: "my-app"
    type: "greenfield"
    description: "My new app"
  git:
    name: "Alex Developer"
    email: "alex@example.com"
    init_repository: true
started_at: "2025-01-15T10:30:00Z"
last_updated: "2025-01-15T10:35:00Z"
```

### Atomic File Writes

Use write-to-temp-then-rename pattern:

```python
def _save_state(self, state: dict) -> None:
    temp_file = self.state_file.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        yaml.safe_dump(state, f)
    temp_file.rename(self.state_file)
    self.state_file.chmod(0o600)
```

### Resume Prompt

TUI:
```
Incomplete onboarding detected from 10 minutes ago.

Steps completed: Project, Git
Next step: Provider Selection

[R]esume  [S]tart fresh  [C]ancel
```

Web:
```
Modal dialog with same information and buttons
```

## Test Scenarios

1. **Save step**: Given onboarding in progress, When step completed, Then state saved to file

2. **Load on startup**: Given incomplete state exists, When startup runs, Then offers resume option

3. **Resume flow**: Given user chooses resume, When wizard starts, Then starts at next incomplete step

4. **Data preservation**: Given project and git steps complete, When resumed, Then data for those steps loaded

5. **Expired state**: Given state older than 24 hours, When can_resume checked, Then returns False with warning

6. **Wrong directory**: Given state for different project path, When startup in new directory, Then resume not offered

7. **Corrupted state**: Given invalid YAML in state file, When loading, Then handles gracefully and offers start fresh

8. **Cleanup on completion**: Given onboarding completes, When cleanup runs, Then state file deleted

9. **Atomic write**: Given save in progress, When process killed, Then file is either old or new (not partial)

10. **File permissions**: Given state file created, When permissions checked, Then is 600 (user-only)

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests for resume flow
- [ ] Tested with process interruption scenarios
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Type hints complete (no `Any`)

## Story Points: 5

## Dependencies

- Story 40.2: Global and Project State Detection
- Stories 41.1-41.3: Wizards (for integration)

## Notes

- Consider compression for large step data
- Log resume/start-fresh choices for analytics
- Handle timezone issues in expiry calculation (use UTC)
- Test file locking on Windows
- Consider backup of state file before clearing
- State should not contain sensitive data (credentials stored separately)
