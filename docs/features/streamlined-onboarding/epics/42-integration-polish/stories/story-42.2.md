# Story 42.2: Cross-Platform Testing

## User Story

As a GAO-Dev developer,
I want comprehensive automated tests across Docker, SSH, WSL, and desktop environments,
So that I can confidently release knowing the onboarding works in all supported contexts.

## Acceptance Criteria

- [ ] AC1: CI pipeline includes test matrix for all supported environments
- [ ] AC2: Docker tests run in official Python 3.11 slim container
- [ ] AC3: SSH tests simulate SSH session with environment variables
- [ ] AC4: WSL tests run on Windows CI runner with WSL2
- [ ] AC5: Desktop tests run on Windows, macOS, and Linux with display
- [ ] AC6: Each environment verifies correct detection (EnvironmentType)
- [ ] AC7: Each environment runs through complete onboarding flow
- [ ] AC8: Tests verify correct wizard selection (TUI vs Web)
- [ ] AC9: Credential storage tests verify correct backend selection
- [ ] AC10: Performance benchmarks pass on all platforms (<2s startup)
- [ ] AC11: Test failures produce clear diagnostic output
- [ ] AC12: Test coverage report generated across all environments

## Technical Notes

### Test Matrix Configuration

```yaml
# .github/workflows/onboarding-test.yml
name: Cross-Platform Onboarding Tests

on: [push, pull_request]

jobs:
  test-docker:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim
    steps:
      - uses: actions/checkout@v4
      - name: Install GAO-Dev
        run: pip install -e .
      - name: Run Docker environment tests
        run: pytest tests/onboarding/test_docker_environment.py -v
        env:
          GAO_DEV_DOCKER: "1"

  test-ssh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
      - name: Install GAO-Dev
        run: pip install -e .
      - name: Run SSH environment tests
        run: pytest tests/onboarding/test_ssh_environment.py -v
        env:
          SSH_CLIENT: "192.168.1.1 54321 22"
          SSH_TTY: "/dev/pts/0"

  test-wsl:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup WSL
        uses: Vampire/setup-wsl@v2
      - name: Run WSL environment tests
        shell: wsl-bash {0}
        run: |
          pip install -e .
          pytest tests/onboarding/test_wsl_environment.py -v

  test-desktop-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
      - name: Install GAO-Dev
        run: pip install -e .
      - name: Run Windows desktop tests
        run: pytest tests/onboarding/test_desktop_environment.py -v

  test-desktop-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
      - name: Install GAO-Dev
        run: pip install -e .
      - name: Run macOS desktop tests
        run: pytest tests/onboarding/test_desktop_environment.py -v

  test-desktop-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
      - name: Install GAO-Dev
        run: pip install -e .
      - name: Run Linux desktop tests
        run: pytest tests/onboarding/test_desktop_environment.py -v
        env:
          DISPLAY: ":0"
```

### Test Structure

```
tests/onboarding/
  conftest.py                    # Shared fixtures
  test_environment_detection.py  # Unit tests for detection
  test_docker_environment.py     # Docker-specific integration
  test_ssh_environment.py        # SSH-specific integration
  test_wsl_environment.py        # WSL-specific integration
  test_desktop_environment.py    # Desktop-specific integration
  test_wizard_selection.py       # Wizard type selection
  test_credential_backends.py    # Credential storage per env
  test_full_onboarding_flow.py   # End-to-end flows
```

### Test Fixtures

```python
@pytest.fixture
def docker_environment(monkeypatch, tmp_path):
    """Simulate Docker container environment."""
    dockerenv = tmp_path / ".dockerenv"
    dockerenv.touch()
    monkeypatch.setenv("GAO_DEV_DOCKER", "1")
    monkeypatch.delenv("DISPLAY", raising=False)
    yield
    dockerenv.unlink()

@pytest.fixture
def ssh_environment(monkeypatch):
    """Simulate SSH session environment."""
    monkeypatch.setenv("SSH_CLIENT", "192.168.1.1 54321 22")
    monkeypatch.setenv("SSH_TTY", "/dev/pts/0")
    monkeypatch.delenv("DISPLAY", raising=False)
    yield
```

### Performance Benchmarks

```python
@pytest.mark.benchmark
def test_startup_performance(benchmark):
    """Startup should complete in <2 seconds."""
    result = benchmark(lambda: startup_orchestrator.start())
    assert benchmark.stats['mean'] < 2.0
```

## Test Scenarios

1. **Docker detection accuracy**: Given Docker container, When environment detected, Then returns `CONTAINER`

2. **SSH detection accuracy**: Given SSH session, When environment detected, Then returns `SSH`

3. **WSL detection accuracy**: Given WSL environment, When environment detected, Then returns `WSL`

4. **Desktop detection accuracy**: Given desktop with DISPLAY, When environment detected, Then returns `DESKTOP`

5. **TUI wizard for Docker**: Given Docker environment, When wizard selected, Then TUI wizard runs

6. **Web wizard for desktop**: Given desktop environment, When wizard selected, Then Web wizard runs

7. **Env var credentials in container**: Given container environment, When credential backend selected, Then environment variables primary

8. **Keychain on desktop**: Given desktop environment, When credential backend selected, Then keychain available

9. **Complete flow in Docker**: Given Docker environment, When full onboarding runs, Then completes successfully

10. **Startup performance**: Given any environment, When startup measured, Then completes in <2 seconds

## Definition of Done

- [ ] All acceptance criteria met
- [ ] CI pipeline configured and passing
- [ ] All test matrix combinations pass
- [ ] Performance benchmarks documented
- [ ] Test coverage >80% for onboarding code
- [ ] Flaky tests identified and fixed
- [ ] Code reviewed
- [ ] Test documentation updated

## Story Points: 8

## Dependencies

- Epic 40: All stories (environment detection)
- Epic 41: All stories (wizard implementations)

## Notes

- Use GitHub Actions caching for faster CI runs
- Consider parallel test execution where possible
- Document known environment-specific quirks
- Set up test result badges for README
- Consider adding manual test checklist for edge cases
- Ensure CI secrets are properly configured for API validation tests
