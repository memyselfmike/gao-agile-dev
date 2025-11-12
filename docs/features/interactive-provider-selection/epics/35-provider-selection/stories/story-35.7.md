# Story 35.7: Comprehensive Testing & Regression Validation

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.7
**Story Points**: 8
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.6
**Priority**: P0
**Status**: Todo

---

## Description

Create comprehensive test suite including E2E tests, regression tests, security tests, and CI/CD headless environment tests to ensure >90% coverage for new code and zero regressions in existing functionality.

**Note**: This story focuses on **additional** E2E, regression, security, and headless tests. Unit and integration tests for each component were already created in Stories 35.2-35.6 (TDD approach as per CRAAP resolution).

This story focuses on:
- End-to-end test scenarios (complete flows)
- Regression testing (existing functionality unchanged)
- Security testing (YAML injection, input sanitization)
- CI/CD headless environment testing (Docker, no TTY)
- Cross-platform validation (Windows, macOS, Linux)
- Performance testing (startup time, validation time)

---

## Acceptance Criteria

- [ ] Test coverage targets met:
  - [ ] Overall project coverage: no decrease from baseline
  - [ ] New code coverage: >90%
  - [ ] PreferenceManager: >95% (from Story 35.2)
  - [ ] ProviderValidator: >90% (from Story 35.3)
  - [ ] InteractivePrompter: >85% (from Story 35.4)
  - [ ] ProviderSelector: >90% (from Story 35.5)
  - [ ] ChatREPL integration: >80% (from Story 35.6)
- [ ] Regression test suite created:
  - [ ] File: `tests/regression/test_epic35_no_regressions.py`
  - [ ] 20+ regression tests covering:
    - [ ] Environment variables still work (AGENT_PROVIDER)
    - [ ] ProcessExecutor backward compatible
    - [ ] All existing CLI commands work (create-prd, implement-story, etc.)
    - [ ] Config files still work (defaults.yaml, local.yaml)
    - [ ] All agent workflows unchanged
    - [ ] Brian orchestrator unchanged
    - [ ] ConversationalBrian unchanged
    - [ ] CommandRouter unchanged
    - [ ] Session state unchanged
    - [ ] Existing workflows work
- [ ] End-to-end test scenarios:
  - [ ] File: `tests/e2e/test_provider_selection_e2e.py`
  - [ ] First-time startup flow (no prefs, interactive)
  - [ ] Returning user flow (saved prefs accepted)
  - [ ] Environment variable bypass (no prompts)
  - [ ] Validation failure recovery (retry flow)
  - [ ] Preference save/load round-trip
  - [ ] Feature flag disabled (old behavior)
- [ ] Cross-platform testing:
  - [ ] Tests pass on Windows (local or CI)
  - [ ] Tests pass on macOS (if available)
  - [ ] Tests pass on Linux (via GitHub Actions)
  - [ ] Platform-specific tests for CLI detection
  - [ ] Windows-specific: CMD, PowerShell, Git Bash
- [ ] Performance testing:
  - [ ] File: `tests/performance/test_provider_selection_performance.py`
  - [ ] Preference loading <100ms
  - [ ] Provider validation <2s
  - [ ] Full selection flow <30s (mocked user input)
  - [ ] No regression in REPL startup time (with env var)
- [ ] Error scenario testing:
  - [ ] Corrupt preference files
  - [ ] Missing CLIs
  - [ ] Invalid configurations
  - [ ] Network failures (for validation)
  - [ ] Permission errors
  - [ ] Timeout scenarios
- [ ] **Security testing** (CRAAP Critical Resolution):
  - [ ] File: `tests/security/test_provider_selection_security.py`
  - [ ] Test YAML injection attempts with malicious input
  - [ ] Verify `yaml.safe_dump()` prevents code execution
  - [ ] Test input sanitization rejects dangerous characters
  - [ ] Test with special characters, newlines, YAML tags, anchors
  - [ ] Test with realistic attack payloads:
    - [ ] `!!python/object/apply:os.system ['rm -rf /']`
    - [ ] `!!python/eval "import os; os.system('whoami')"`
    - [ ] YAML anchors and aliases (`&exploit`, `*exploit`)
- [ ] **CI/CD headless environment testing** (CRAAP Critical Resolution):
  - [ ] File: `tests/ci/test_headless_environment.py`
  - [ ] Test in Docker container without TTY
  - [ ] Verify lazy import fallback works (prompt_toolkit unavailable)
  - [ ] Ensure env var bypass works in headless mode
  - [ ] Test with `stdin` closed or redirected
  - [ ] Add GitHub Actions job for headless testing:
    - [ ] `.github/workflows/test-headless.yml`
- [ ] CI/CD integration:
  - [ ] All tests run in GitHub Actions
  - [ ] Coverage report generated and uploaded
  - [ ] No test failures allowed in CI
  - [ ] Headless environment test job passes
  - [ ] Windows test job passes (if available)
- [ ] Test documentation:
  - [ ] README in `tests/cli/` explaining test structure
  - [ ] Comments in all test files
  - [ ] Instructions for running tests locally
  - [ ] Instructions for running headless tests (Docker)

---

## Tasks

- [ ] Write regression test suite (20+ tests)
  - [ ] Test env vars still work
  - [ ] Test existing CLI commands
  - [ ] Test existing workflows
  - [ ] Test backward compatibility
- [ ] Write end-to-end tests (5+ scenarios)
  - [ ] First-time startup
  - [ ] Returning user
  - [ ] Env var bypass
  - [ ] Validation recovery
  - [ ] Round-trip save/load
- [ ] Cross-platform testing
  - [ ] Run tests on Windows
  - [ ] Run tests on macOS (if available)
  - [ ] Run tests on Linux (CI)
  - [ ] Add platform-specific tests
- [ ] Performance testing
  - [ ] Write performance tests
  - [ ] Establish baselines
  - [ ] Verify targets met
- [ ] Error scenario testing
  - [ ] Test all error paths
  - [ ] Test edge cases
  - [ ] Test timeouts
- [ ] **Write security tests** (CRAAP Critical)
  - [ ] YAML injection attempts
  - [ ] Input sanitization validation
  - [ ] Code execution prevention
  - [ ] Test with realistic attack payloads
- [ ] **Write CI/CD headless tests** (CRAAP Critical)
  - [ ] Docker test setup
  - [ ] No TTY simulation
  - [ ] Lazy import fallback validation
  - [ ] GitHub Actions job
- [ ] Run full test suite and fix failures
  - [ ] `pytest tests/ -v --cov=gao_dev`
  - [ ] Fix any failures
  - [ ] Address coverage gaps
- [ ] Generate coverage report
  - [ ] `pytest --cov=gao_dev --cov-report=html`
  - [ ] Review report
  - [ ] Ensure >90% for new code
- [ ] Document test structure
  - [ ] Write tests/cli/README.md
  - [ ] Document running tests
  - [ ] Document headless testing

---

## Test Suites

### Regression Tests (`tests/regression/test_epic35_no_regressions.py`)

```python
class TestEpic35NoRegressions:
    """Ensure Epic 35 doesn't break existing functionality."""

    def test_env_var_still_works(self):
        """AGENT_PROVIDER env var still bypasses prompts."""
        # Set AGENT_PROVIDER=claude-code
        # Run gao-dev start
        # Assert no prompts shown
        # Assert claude-code used

    def test_chatrepl_backward_compatible(self):
        """ChatREPL API unchanged."""
        # Create ChatREPL instance (old way)
        # Assert works identically

    def test_processexecutor_unchanged(self):
        """ProcessExecutor API unchanged."""
        # Create ProcessExecutor directly
        # Assert works identically

    def test_all_cli_commands_work(self):
        """All CLI commands still work."""
        # Test: gao-dev create-prd
        # Test: gao-dev create-architecture
        # Test: gao-dev implement-story
        # Assert all work unchanged

    def test_existing_configs_work(self):
        """Existing config files still work."""
        # Load defaults.yaml
        # Load local.yaml (if exists)
        # Assert all settings respected

    def test_brian_orchestrator_unchanged(self):
        """Brian orchestrator unchanged."""
        # Create Brian orchestrator
        # Run analysis
        # Assert works identically

    def test_conversational_brian_unchanged(self):
        """ConversationalBrian unchanged."""
        # Create ConversationalBrian
        # Send message
        # Assert works identically

    def test_command_router_unchanged(self):
        """CommandRouter unchanged."""
        # Create CommandRouter
        # Route command
        # Assert works identically

    def test_session_state_unchanged(self):
        """Session state management unchanged."""
        # Create session
        # Save state
        # Load state
        # Assert works identically

    def test_existing_workflows_work(self):
        """Existing workflows still work."""
        # Load workflow
        # Execute workflow
        # Assert works identically

    # ... 10+ more regression tests
```

### End-to-End Tests (`tests/e2e/test_provider_selection_e2e.py`)

```python
class TestProviderSelectionE2E:
    """End-to-end test scenarios."""

    async def test_first_time_startup_flow(self, tmp_path):
        """Full first-time startup flow."""
        # No env var, no saved prefs
        # Mock all prompts:
        #   - Select provider: 2 (opencode)
        #   - Use local: y
        #   - Select model: 1 (deepseek-r1)
        #   - Save prefs: y
        # Start ChatREPL
        # Assert provider selected
        # Assert preferences saved
        # Assert validation passed
        # Assert REPL started

    async def test_returning_user_flow(self, tmp_path):
        """Full returning user flow."""
        # Create saved preferences
        # Mock prompt: Use saved? y
        # Start ChatREPL
        # Assert saved config used
        # Assert validation passed
        # Assert REPL started

    async def test_env_var_bypass_flow(self, tmp_path):
        """Environment variable bypass flow."""
        # Set AGENT_PROVIDER=claude-code
        # Start ChatREPL
        # Assert no prompts shown
        # Assert env var used
        # Assert REPL started

    async def test_validation_failure_recovery(self, tmp_path):
        """Validation failure and recovery flow."""
        # Mock prompts:
        #   - Select provider: 2 (opencode)
        #   - Mock validation failure (CLI not found)
        #   - Try again: y
        #   - Select provider: 1 (claude-code)
        #   - Mock validation success
        # Start ChatREPL
        # Assert retry worked
        # Assert second provider used

    async def test_preference_save_load_round_trip(self, tmp_path):
        """Preference save and load round-trip."""
        # First run: select provider, save prefs
        # Second run: load prefs, use saved
        # Assert loaded config matches saved
```

### Security Tests (`tests/security/test_provider_selection_security.py`)

```python
class TestProviderSelectionSecurity:
    """Security tests for YAML injection and input sanitization."""

    def test_yaml_injection_prevented(self, tmp_path):
        """YAML injection attempts are prevented."""
        malicious_config = {
            'provider': 'opencode',
            'model': "!!python/object/apply:os.system ['echo HACKED']"
        }
        manager = PreferenceManager(tmp_path)
        manager.save_preferences(malicious_config)

        # Read file raw
        content = (tmp_path / '.gao-dev' / 'provider_preferences.yaml').read_text()

        # Assert malicious code not present
        assert '!!python' not in content
        assert 'os.system' not in content

    def test_input_sanitization_removes_dangerous_chars(self):
        """Input sanitization removes dangerous characters."""
        manager = PreferenceManager(Path('/tmp'))

        # Test dangerous strings
        dangerous_strings = [
            "model!!python/eval",
            "model&exploit",
            "model*exploit",
            "model{code}",
            "model|command",
            "model`whoami`",
            "model$(whoami)",
        ]

        for dangerous in dangerous_strings:
            sanitized = manager._sanitize_string(dangerous)
            # Assert dangerous characters removed
            assert '!!' not in sanitized
            assert '&' not in sanitized
            assert '*' not in sanitized
            assert '{' not in sanitized
            assert '|' not in sanitized
            assert '`' not in sanitized
            assert '$(' not in sanitized

    def test_yaml_safe_dump_used(self, tmp_path):
        """Verify yaml.safe_dump() is used, not yaml.dump()."""
        # This is a code review item
        # Check PreferenceManager.save_preferences() uses yaml.safe_dump
        import inspect
        from gao_dev.cli.preference_manager import PreferenceManager

        source = inspect.getsource(PreferenceManager.save_preferences)
        assert 'yaml.safe_dump' in source
        assert 'yaml.dump(' not in source  # Ensure unsafe dump not used
```

### Headless Environment Tests (`tests/ci/test_headless_environment.py`)

```python
class TestHeadlessEnvironment:
    """Tests for CI/CD headless environments (no TTY)."""

    def test_lazy_import_fallback_on_import_error(self, monkeypatch):
        """Lazy import falls back to input() when prompt_toolkit unavailable."""
        # Mock ImportError when importing prompt_toolkit
        def mock_import(name, *args):
            if 'prompt_toolkit' in name:
                raise ImportError("No module named 'prompt_toolkit'")
            return __import__(name, *args)

        monkeypatch.setattr('builtins.__import__', mock_import)

        # Mock input() to return valid choice
        monkeypatch.setattr('builtins.input', lambda prompt: '1')

        prompter = InteractivePrompter()
        provider = prompter.prompt_provider()

        # Assert fallback worked
        assert provider == 'claude-code'

    def test_no_tty_environment(self, monkeypatch):
        """Test in environment without TTY (stdin closed)."""
        # Mock OSError when creating PromptSession (no TTY)
        from unittest.mock import Mock, patch

        with patch('gao_dev.cli.interactive_prompter.PromptSession',
                   side_effect=OSError("No TTY available")):
            monkeypatch.setattr('builtins.input', lambda prompt: '2')

            prompter = InteractivePrompter()
            provider = prompter.prompt_provider()

            assert provider == 'opencode'

    def test_env_var_bypass_in_headless(self, tmp_path, monkeypatch):
        """Environment variable bypass works in headless mode."""
        monkeypatch.setenv('AGENT_PROVIDER', 'claude-code')

        selector = ProviderSelector(tmp_path)
        config = selector.select_provider()

        # Assert env var used, no prompts needed
        assert config['provider'] == 'claude-code'

    def test_docker_without_tty(self):
        """Test in Docker container without TTY."""
        # This test runs in GitHub Actions with Docker
        # See .github/workflows/test-headless.yml
        # Ensures system works in real headless environment
        pass
```

### GitHub Actions Job (`.github/workflows/test-headless.yml`)

```yaml
name: Headless Environment Tests

on: [push, pull_request]

jobs:
  test-headless:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-cov

      - name: Run headless tests (no TTY)
        run: |
          # Run tests without TTY
          python -c "import sys; sys.stdin.close()"
          export AGENT_PROVIDER=claude-code
          pytest tests/ci/test_headless_environment.py -v

      - name: Run full test suite in headless mode
        run: |
          export AGENT_PROVIDER=claude-code
          pytest tests/ -v --cov=gao_dev
```

---

## Definition of Done

- [ ] 100+ total tests passing (including existing tests from stories 35.2-35.6)
- [ ] >90% coverage for new code (verified with coverage report)
- [ ] 0 regressions detected (all existing tests pass)
- [ ] Cross-platform validation complete (Windows, Linux, macOS if available)
- [ ] Performance targets met (<100ms prefs, <2s validation, <30s flow)
- [ ] Security tests pass (YAML injection prevented)
- [ ] Headless tests pass (CI/CD compatible)
- [ ] GitHub Actions passing (all jobs green)
- [ ] Test documentation complete (README, comments)
- [ ] Coverage report generated and reviewed
- [ ] Commit message: `feat(epic-35): Story 35.7 - Comprehensive Testing & Regression Validation (8 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Security Testing (CRAAP Critical - Issue #3)**:
- **Risk**: YAML injection vulnerabilities
- **Tests**: Malicious input attempts, code execution prevention
- **Validation**: Verify `yaml.safe_dump()` usage, sanitization effectiveness

**CI/CD Headless Testing (CRAAP Critical - Issue #1)**:
- **Risk**: prompt_toolkit breaks in headless Docker containers
- **Tests**: No TTY simulation, lazy import fallback validation
- **Validation**: GitHub Actions job with Docker container

**Testing Estimates (CRAAP Critical - Issue #1)**:
- **Original**: 120+ tests in Story 35.7 only
- **Revised**: Tests distributed across stories (TDD):
  - Stories 35.2-35.6: ~90 unit and integration tests
  - Story 35.7: ~20-30 E2E, regression, security tests
- **Total**: 110-120 tests (realistic for 8 story points)

### Test Distribution Summary

**By Story** (Cumulative):
- Story 35.2: 20+ PreferenceManager tests
- Story 35.3: 15+ ProviderValidator tests
- Story 35.4: 25+ InteractivePrompter tests
- Story 35.5: 20+ ProviderSelector tests
- Story 35.6: 10+ ChatREPL integration tests
- **Story 35.7: 20-30 E2E, regression, security, headless tests**

**Total**: 110-140 tests

**By Category**:
- Unit tests: ~70 (Stories 35.2-35.5)
- Integration tests: ~20 (Stories 35.5-35.6)
- E2E tests: ~10 (Story 35.7)
- Regression tests: ~20 (Story 35.7)
- Security tests: ~5 (Story 35.7)
- Headless tests: ~5 (Story 35.7)

### Performance Testing Baselines

**Targets** (Success Criteria):
- Preference loading: <100ms
- Provider validation: <2s
- Full selection flow: <30s (mocked user input)
- REPL startup (with env var): No regression from baseline

**Measurement**:
```python
import time

def test_preference_loading_performance(tmp_path):
    """Preference loading is fast (<100ms)."""
    manager = PreferenceManager(tmp_path)
    # Save preferences first
    manager.save_preferences({...})

    # Measure load time
    start = time.time()
    prefs = manager.load_preferences()
    elapsed_ms = (time.time() - start) * 1000

    assert elapsed_ms < 100, f"Loading took {elapsed_ms}ms (target <100ms)"
```

### Cross-Platform Testing Strategy

**Windows**:
- Run locally if available
- GitHub Actions Windows runner (optional)
- Test: CMD, PowerShell, Git Bash

**macOS**:
- Run locally if available
- GitHub Actions macOS runner (optional)

**Linux**:
- GitHub Actions Ubuntu runner (primary CI)
- Docker containers for headless testing

**Platform-Specific Tests**:
- CLI detection differences (`where` vs `which`)
- File permissions (Unix vs Windows)
- Rich output (ANSI codes in CMD)

### Security Testing Details

**Attack Payloads** (Should All Be Prevented):
```python
malicious_payloads = [
    # Python code execution
    "!!python/object/apply:os.system ['rm -rf /']",
    "!!python/eval 'import os; os.system(\"whoami\")'",

    # YAML anchors (can cause DoS)
    "model: &exploit\n*exploit",

    # Command injection
    "model: `whoami`",
    "model: $(whoami)",

    # Path traversal
    "model: ../../etc/passwd",
]
```

**Expected Behavior**: All sanitized or rejected before saving.

### Headless Testing Details

**Environments to Test**:
1. Docker container without TTY
2. GitHub Actions (stdin closed)
3. SSH session without TTY allocation
4. Automated scripts (no interactive input)

**Expected Behavior**:
- If `AGENT_PROVIDER` set: Use env var, no prompts
- If lazy import fails: Fall back to `input()`, still works
- If no TTY: Use fallback, not crash

### Dependencies for Next Stories

After this story completes:
- Story 35.8 (Documentation) can begin
- All implementation and testing complete

---

**Story Status**: Todo
**Next Action**: Begin testing after Story 35.6 completes
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
