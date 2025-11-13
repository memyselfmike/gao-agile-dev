# Interactive Provider Selection - Testing Guide

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Running Tests

### All Provider Selection Tests

```bash
# Run all provider selection tests
pytest tests/cli/test_*provider*.py -v

# With coverage
pytest tests/cli/test_*provider*.py --cov=gao_dev.cli --cov-report=html

# Specific test file
pytest tests/cli/test_provider_selector.py -v
```

### Unit Tests

```bash
# PreferenceManager tests
pytest tests/cli/test_preference_manager.py -v

# ProviderValidator tests
pytest tests/cli/test_provider_validator.py -v

# InteractivePrompter tests
pytest tests/cli/test_interactive_prompter.py -v

# ProviderSelector tests
pytest tests/cli/test_provider_selector.py -v
```

### Integration Tests

```bash
# Full integration tests
pytest tests/integration/test_provider_selection_integration.py -v

# ChatREPL integration
pytest tests/cli/test_chat_repl.py -k provider -v
```

### End-to-End Tests

```bash
# E2E tests (requires mock providers)
pytest tests/e2e/test_provider_selection_e2e.py -v

# Headless environment tests
pytest tests/e2e/test_headless_environment.py -v
```

### Performance Tests

```bash
# Performance benchmarks
pytest tests/performance/test_provider_selection_performance.py -v
```

---

## Coverage Requirements

**Target**: >90% coverage for all new code

```bash
# Generate coverage report
pytest tests/cli/test_*provider*.py --cov=gao_dev.cli --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Coverage Breakdown** (Target):
- PreferenceManager: >95%
- ProviderValidator: >90%
- InteractivePrompter: >85%
- ProviderSelector: >90%
- ChatREPL Integration: >80%

---

## Adding New Tests

### Test Structure

```python
import pytest
from pathlib import Path
from rich.console import Console
from gao_dev.cli.provider_selector import ProviderSelector

class TestProviderSelector:
    """Tests for ProviderSelector class."""

    @pytest.fixture
    def console(self):
        """Fixture for Rich Console."""
        return Console()

    @pytest.fixture
    def project_root(self, tmp_path):
        """Fixture for temporary project root."""
        gao_dev = tmp_path / ".gao-dev"
        gao_dev.mkdir()
        return tmp_path

    def test_select_provider_with_env_var(self, project_root, console, monkeypatch):
        """Test provider selection using environment variable."""
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        selector = ProviderSelector(project_root, console)
        config = selector.select_provider()

        assert config["provider"] == "claude-code"
        assert "model" in config
```

### Mocking User Input

```python
from unittest.mock import patch, Mock

def test_interactive_prompt(project_root, console):
    """Test interactive provider prompt."""
    with patch('builtins.input', return_value='1'):
        prompter = InteractivePrompter(console)
        provider = prompter.prompt_provider(
            ['claude-code', 'opencode'],
            {'claude-code': 'Claude Code CLI'}
        )
        assert provider == 'claude-code'
```

### Async Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_validation_async():
    """Test async validation."""
    validator = ProviderValidator(Console())
    result = await validator.validate_configuration('claude-code', {})
    assert isinstance(result, ValidationResult)
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Test Provider Selection

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .[test]

      - name: Run tests
        run: |
          pytest tests/cli/test_*provider*.py -v --cov=gao_dev.cli

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Fixtures

### Common Fixtures

Located in `tests/conftest.py`:

```python
@pytest.fixture
def mock_console():
    """Mock Rich Console."""
    return Mock(spec=Console)

@pytest.fixture
def temp_project_root(tmp_path):
    """Temporary project root with .gao-dev/ directory."""
    gao_dev = tmp_path / ".gao-dev"
    gao_dev.mkdir()
    return tmp_path

@pytest.fixture
def sample_preferences():
    """Sample valid preferences dict."""
    return {
        'version': '1.0.0',
        'provider': {
            'name': 'opencode',
            'model': 'deepseek-r1',
            'config': {'ai_provider': 'ollama', 'use_local': True}
        },
        'metadata': {'last_updated': '2025-01-12T10:30:00Z'}
    }
```

---

## Security Testing

### YAML Injection Tests

```python
def test_yaml_injection_prevention():
    """Test that YAML injection is prevented."""
    manager = PreferenceManager(tmp_path)

    malicious_prefs = {
        'provider': '!!python/object/apply:os.system ["rm -rf /"]',
        'model': 'sonnet-4.5'
    }

    manager.save_preferences(malicious_prefs)
    loaded = manager.load_preferences()

    # Verify dangerous tags removed
    assert '!!' not in loaded['provider']
    assert 'rm -rf' not in loaded['provider']
```

---

## Related Documentation

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

---

**Version**: 1.0
**Last Updated**: 2025-01-12
