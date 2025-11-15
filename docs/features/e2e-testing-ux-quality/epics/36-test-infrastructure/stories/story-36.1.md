# Story 36.1: Cost-Free Test Execution

**Story ID**: 1.1
**Epic**: 1 - Test Infrastructure
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 3
**Priority**: Critical

---

## User Story

**As a** developer
**I want** ALL E2E tests to use opencode/ollama/deepseek-r1 by default
**So that** I can run comprehensive test suites without incurring API costs

---

## Business Value

API costs ($0.003/1K tokens input, $0.015/1K tokens output) create a financial barrier that prevents:
- Frequent test execution during development
- Comprehensive test coverage
- Running tests in CI/CD pipelines

By defaulting to local models, we enable:
- Unlimited test execution with zero cost
- Faster developer iteration (no cost concerns)
- Cost savings: $40-200/month per developer

---

## Acceptance Criteria

- [ ] **AC1**: E2E test framework defaults to opencode provider with ollama/deepseek-r1 model
- [ ] **AC2**: `E2E_TEST_PROVIDER` environment variable overrides default provider
- [ ] **AC3**: `AGENT_PROVIDER` environment variable is respected as second-tier precedence
- [ ] **AC4**: Provider precedence documented: E2E_TEST_PROVIDER > AGENT_PROVIDER > Default
- [ ] **AC5**: Test setup validates ollama is running before execution
- [ ] **AC6**: Clear error message if ollama not available with setup instructions
- [ ] **AC7**: Test configuration helper function `get_e2e_test_provider()` implemented
- [ ] **AC8**: Zero API costs confirmed for default test execution

---

## Technical Context

### Architecture References

From Architecture document section "Integration Points":

**Provider Override Precedence** (Three-tier hierarchy):
1. `E2E_TEST_PROVIDER` environment variable (highest precedence)
2. `AGENT_PROVIDER` environment variable (global preference from Epic 385)
3. Default: opencode/ollama/deepseek-r1 (cost-free)

### Implementation Details

**Provider Configuration Function**:
```python
# tests/e2e/conftest.py

import os
from typing import Tuple, Dict

def get_e2e_test_provider() -> Tuple[str, Dict]:
    """Get provider configuration for E2E tests with precedence resolution."""

    # Tier 1: E2E_TEST_PROVIDER (highest precedence)
    if e2e_provider := os.getenv("E2E_TEST_PROVIDER"):
        if e2e_provider == "claude-code":
            return ("claude-code", {})
        elif e2e_provider == "opencode":
            return ("opencode", {
                "ai_provider": os.getenv("E2E_AI_PROVIDER", "ollama"),
                "use_local": True,
                "model": os.getenv("E2E_MODEL", "deepseek-r1")
            })

    # Tier 2: AGENT_PROVIDER (global preference from Epic 385)
    if agent_provider := os.getenv("AGENT_PROVIDER"):
        if agent_provider == "claude-code":
            # Override with cost-free default
            return ("opencode", {
                "ai_provider": "ollama",
                "use_local": True,
                "model": "deepseek-r1"
            })
        elif agent_provider == "opencode":
            return ("opencode", {
                "ai_provider": os.getenv("AI_PROVIDER", "ollama"),
                "use_local": True,
                "model": os.getenv("MODEL", "deepseek-r1")
            })

    # Tier 3: Default (cost-free)
    return ("opencode", {
        "ai_provider": "ollama",
        "use_local": True,
        "model": "deepseek-r1"
    })
```

**Ollama Validation**:
```python
import subprocess
import sys

def validate_ollama_available() -> bool:
    """Check if ollama is running and model is available."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print("ERROR: ollama is not running")
            print("Setup instructions: https://ollama.ai/")
            return False

        if "deepseek-r1" not in result.stdout:
            print("ERROR: deepseek-r1 model not installed")
            print("Run: ollama pull deepseek-r1")
            return False

        return True

    except FileNotFoundError:
        print("ERROR: ollama not installed")
        print("Install from: https://ollama.ai/")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR: ollama command timed out")
        return False
```

### Dependencies

- Epic 3871: Provider abstraction (ProcessExecutor, ProviderFactory)
- Epic 385: AGENT_PROVIDER environment variable support
- ollama installed locally
- deepseek-r1 model downloaded

---

## Test Scenarios

### Test 1: Default Provider Configuration
```python
def test_default_provider_is_cost_free():
    """Test that default provider is opencode/ollama/deepseek-r1."""
    provider_name, provider_config = get_e2e_test_provider()

    assert provider_name == "opencode"
    assert provider_config["ai_provider"] == "ollama"
    assert provider_config["use_local"] is True
    assert provider_config["model"] == "deepseek-r1"
```

### Test 2: E2E_TEST_PROVIDER Override
```python
def test_e2e_test_provider_override(monkeypatch):
    """Test E2E_TEST_PROVIDER takes highest precedence."""
    monkeypatch.setenv("E2E_TEST_PROVIDER", "claude-code")
    monkeypatch.setenv("AGENT_PROVIDER", "opencode")

    provider_name, provider_config = get_e2e_test_provider()

    assert provider_name == "claude-code"  # E2E wins
```

### Test 3: AGENT_PROVIDER Fallback
```python
def test_agent_provider_fallback_still_cost_free(monkeypatch):
    """Test AGENT_PROVIDER is overridden to remain cost-free."""
    monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

    provider_name, provider_config = get_e2e_test_provider()

    # Should still use local model despite AGENT_PROVIDER
    assert provider_name == "opencode"
    assert provider_config["ai_provider"] == "ollama"
```

### Test 4: Ollama Validation
```python
def test_ollama_validation_detects_missing_service():
    """Test validation fails gracefully if ollama not running."""
    # This test requires ollama to be stopped
    # Mock subprocess for unit test
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()

        result = validate_ollama_available()

        assert result is False
```

---

## Definition of Done

- [ ] Provider configuration function implemented and tested
- [ ] Ollama validation function implemented and tested
- [ ] Environment variable precedence working as documented
- [ ] Unit tests passing (4+ tests)
- [ ] Error messages clear and actionable
- [ ] Documentation updated with setup instructions
- [ ] Code reviewed and approved
- [ ] Zero API costs confirmed in test runs

---

## Implementation Notes

### Files to Create/Modify

**New Files**:
- `tests/e2e/conftest.py` - Pytest fixtures and provider config
- `tests/e2e/test_provider_config.py` - Tests for provider configuration

**Modified Files**:
- None (new infrastructure)

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `E2E_TEST_PROVIDER` | Override test provider (highest precedence) | `claude-code`, `opencode` |
| `E2E_AI_PROVIDER` | AI backend for opencode | `ollama`, `anthropic` |
| `E2E_MODEL` | Model to use | `deepseek-r1`, `llama2` |
| `AGENT_PROVIDER` | Global agent provider (from Epic 385) | `claude-code`, `opencode` |

### Error Messages

```
ERROR: ollama is not running
Ollama must be installed and running to execute E2E tests.

Setup Instructions:
1. Install ollama: https://ollama.ai/
2. Start ollama service
3. Pull deepseek-r1 model: ollama pull deepseek-r1

Alternative: Override provider with environment variable:
  export E2E_TEST_PROVIDER=claude-code

Note: Using Claude API will incur costs ($0.003/1K tokens input, $0.015/1K tokens output)
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Ollama not installed on developer machine | Medium | High | Clear setup docs, validation with helpful errors |
| Developer doesn't understand provider precedence | Medium | Medium | Document precedence clearly, add examples |
| AGENT_PROVIDER conflicts with E2E_TEST_PROVIDER | Low | Medium | Explicit precedence rules, unit tests |
| Costs accidentally incurred with wrong config | Low | High | Default to cost-free, require explicit override |

---

## Related Stories

- **Depends On**: None (foundation story)
- **Blocks**: Story 36.2, 1.3, 1.4 (all need provider configuration)
- **Related**: Epic 385 stories (provider selection system)

---

## References

- PRD Section: FR1 (Provider Configuration)
- Architecture Section: Integration Points - Provider System
- CRAAP Review: Priority Issue #5 (Clarify Provider Override Behavior)
