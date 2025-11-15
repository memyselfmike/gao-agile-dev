"""Tests for E2E test provider configuration.

Epic 36: Test Infrastructure
Story 36.1: Cost-Free Test Execution

This module tests the provider configuration system for E2E tests,
ensuring cost-free defaults and proper precedence handling.
"""

import os
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from _pytest.monkeypatch import MonkeyPatch
from _pytest.capture import CaptureFixture

from tests.e2e.conftest import get_e2e_test_provider, validate_ollama_available


class TestProviderPrecedence:
    """Test three-tier provider precedence system."""

    def test_default_provider_is_cost_free(self, monkeypatch: MonkeyPatch) -> None:
        """Test that default provider is opencode/ollama/deepseek-r1 (AC1)."""
        # Clear all provider env vars
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.delenv("AGENT_PROVIDER", raising=False)
        monkeypatch.delenv("E2E_AI_PROVIDER", raising=False)
        monkeypatch.delenv("E2E_MODEL", raising=False)

        provider_name, provider_config = get_e2e_test_provider()

        # Verify cost-free defaults
        assert provider_name == "opencode"
        assert provider_config["ai_provider"] == "ollama"
        assert provider_config["use_local"] is True
        assert provider_config["model"] == "deepseek-r1"

    def test_e2e_test_provider_override_claude(self, monkeypatch: MonkeyPatch) -> None:
        """Test E2E_TEST_PROVIDER takes highest precedence (AC2)."""
        # Set all providers to different values
        monkeypatch.setenv("E2E_TEST_PROVIDER", "claude-code")
        monkeypatch.setenv("AGENT_PROVIDER", "opencode")

        provider_name, provider_config = get_e2e_test_provider()

        # E2E_TEST_PROVIDER should win
        assert provider_name == "claude-code"
        assert provider_config == {}

    def test_e2e_test_provider_override_opencode(self, monkeypatch: MonkeyPatch) -> None:
        """Test E2E_TEST_PROVIDER opencode with custom config (AC2)."""
        monkeypatch.setenv("E2E_TEST_PROVIDER", "opencode")
        monkeypatch.setenv("E2E_AI_PROVIDER", "anthropic")
        monkeypatch.setenv("E2E_MODEL", "llama2")

        provider_name, provider_config = get_e2e_test_provider()

        # Custom opencode config
        assert provider_name == "opencode"
        assert provider_config["ai_provider"] == "anthropic"
        assert provider_config["use_local"] is True
        assert provider_config["model"] == "llama2"

    def test_agent_provider_fallback_still_cost_free(self, monkeypatch: MonkeyPatch) -> None:
        """Test AGENT_PROVIDER is overridden to remain cost-free (AC3)."""
        # Clear E2E_TEST_PROVIDER, set AGENT_PROVIDER to expensive option
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        provider_name, provider_config = get_e2e_test_provider()

        # Should still use local model despite AGENT_PROVIDER=claude-code
        assert provider_name == "opencode"
        assert provider_config["ai_provider"] == "ollama"
        assert provider_config["use_local"] is True
        assert provider_config["model"] == "deepseek-r1"

    def test_agent_provider_opencode_respects_env_vars(self, monkeypatch: MonkeyPatch) -> None:
        """Test AGENT_PROVIDER=opencode respects AI_PROVIDER and MODEL env vars (AC3)."""
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.setenv("AGENT_PROVIDER", "opencode")
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        monkeypatch.setenv("MODEL", "codellama")

        provider_name, provider_config = get_e2e_test_provider()

        assert provider_name == "opencode"
        assert provider_config["ai_provider"] == "ollama"
        assert provider_config["model"] == "codellama"

    def test_precedence_documented_correctly(self) -> None:
        """Test provider precedence is documented: E2E_TEST_PROVIDER > AGENT_PROVIDER > Default (AC4)."""
        # This test validates documentation matches implementation
        from tests.e2e.conftest import get_e2e_test_provider

        # Check docstring contains precedence information
        docstring = get_e2e_test_provider.__doc__
        assert docstring is not None
        assert "E2E_TEST_PROVIDER" in docstring
        assert "AGENT_PROVIDER" in docstring
        assert "Default" in docstring
        assert "cost-free" in docstring.lower()


class TestOllamaValidation:
    """Test ollama availability validation."""

    def test_ollama_running_model_available(self) -> None:
        """Test validation succeeds when ollama is running and model exists (AC5)."""
        # This test requires actual ollama to be running
        # Mock for unit test, but can run integration test separately
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="deepseek-r1    latest    abc123    1.2 GB"
            )

            result = validate_ollama_available("deepseek-r1")

            assert result is True
            mock_run.assert_called_once_with(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
            )

    def test_ollama_not_installed(self, capsys: CaptureFixture[str]) -> None:
        """Test validation fails gracefully if ollama not installed (AC6)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = validate_ollama_available()

            assert result is False

            # Check error message is clear and actionable
            captured = capsys.readouterr()
            assert "ERROR: ollama not installed" in captured.out
            assert "https://ollama.ai/" in captured.out
            assert "E2E_TEST_PROVIDER=claude-code" in captured.out
            assert "$0.003/1K tokens" in captured.out  # Cost warning

    def test_ollama_not_running(self, capsys: CaptureFixture[str]) -> None:
        """Test validation fails if ollama service not running (AC6)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            result = validate_ollama_available()

            assert result is False

            # Check error message
            captured = capsys.readouterr()
            assert "ERROR: ollama is not running" in captured.out
            assert "Start ollama service" in captured.out
            assert "ollama pull deepseek-r1" in captured.out

    def test_ollama_timeout(self, capsys: CaptureFixture[str]) -> None:
        """Test validation handles timeout gracefully (AC6)."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ollama", 5)

            result = validate_ollama_available()

            assert result is False

            # Check error message
            captured = capsys.readouterr()
            assert "ERROR: ollama command timed out" in captured.out
            assert "Restart ollama service" in captured.out

    def test_model_not_available(self, capsys: CaptureFixture[str]) -> None:
        """Test validation fails if requested model not installed (AC6)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="llama2    latest    xyz789    3.8 GB"
            )

            result = validate_ollama_available("deepseek-r1")

            assert result is False

            # Check error message
            captured = capsys.readouterr()
            assert "ERROR: deepseek-r1 model not installed" in captured.out
            assert "ollama pull deepseek-r1" in captured.out
            assert "E2E_MODEL=llama2" in captured.out  # Alternative model suggestion

    def test_custom_model_validation(self) -> None:
        """Test validation works with custom model names."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="codellama    latest    def456    2.1 GB"
            )

            result = validate_ollama_available("codellama")

            assert result is True


class TestProviderConfigurationHelper:
    """Test get_e2e_test_provider helper function (AC7)."""

    def test_function_returns_tuple(self, monkeypatch: MonkeyPatch) -> None:
        """Test helper function returns (provider_name, config) tuple."""
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.delenv("AGENT_PROVIDER", raising=False)

        result = get_e2e_test_provider()

        assert isinstance(result, tuple)
        assert len(result) == 2
        provider_name, provider_config = result
        assert isinstance(provider_name, str)
        assert isinstance(provider_config, dict)

    def test_config_contains_required_fields(self, monkeypatch: MonkeyPatch) -> None:
        """Test provider config contains required fields for opencode."""
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.delenv("AGENT_PROVIDER", raising=False)

        provider_name, provider_config = get_e2e_test_provider()

        # Opencode requires these fields
        assert "ai_provider" in provider_config
        assert "use_local" in provider_config
        assert "model" in provider_config

    def test_claude_code_config_empty(self, monkeypatch: MonkeyPatch) -> None:
        """Test claude-code provider config is empty (no additional config needed)."""
        monkeypatch.setenv("E2E_TEST_PROVIDER", "claude-code")

        provider_name, provider_config = get_e2e_test_provider()

        assert provider_name == "claude-code"
        assert provider_config == {}


class TestZeroCostConfirmation:
    """Test zero API costs for default execution (AC8)."""

    def test_default_provider_no_api_calls(self, monkeypatch: MonkeyPatch) -> None:
        """Test default configuration makes no external API calls."""
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.delenv("AGENT_PROVIDER", raising=False)

        provider_name, provider_config = get_e2e_test_provider()

        # Verify local-only configuration
        assert provider_config["use_local"] is True
        assert provider_config["ai_provider"] == "ollama"  # Local service
        # No API keys required
        assert "api_key" not in provider_config
        assert "anthropic_api_key" not in provider_config

    def test_agent_provider_override_prevents_costs(self, monkeypatch: MonkeyPatch) -> None:
        """Test AGENT_PROVIDER=claude-code is overridden to prevent costs."""
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        provider_name, provider_config = get_e2e_test_provider()

        # Should be overridden to cost-free
        assert provider_name == "opencode"
        assert provider_config["use_local"] is True
        assert provider_config["ai_provider"] == "ollama"

    def test_explicit_override_allows_costs(self, monkeypatch: MonkeyPatch) -> None:
        """Test explicit E2E_TEST_PROVIDER override allows paid API (user choice)."""
        # User explicitly wants to use Claude despite costs
        monkeypatch.setenv("E2E_TEST_PROVIDER", "claude-code")

        provider_name, provider_config = get_e2e_test_provider()

        # User explicitly requested paid API
        assert provider_name == "claude-code"
        # This is intentional and requires explicit opt-in


class TestEnvironmentVariableSupport:
    """Test all supported environment variables."""

    def test_e2e_test_provider_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test E2E_TEST_PROVIDER environment variable."""
        monkeypatch.setenv("E2E_TEST_PROVIDER", "opencode")

        provider_name, _ = get_e2e_test_provider()
        assert provider_name == "opencode"

    def test_e2e_ai_provider_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test E2E_AI_PROVIDER environment variable."""
        monkeypatch.setenv("E2E_TEST_PROVIDER", "opencode")
        monkeypatch.setenv("E2E_AI_PROVIDER", "anthropic")

        _, provider_config = get_e2e_test_provider()
        assert provider_config["ai_provider"] == "anthropic"

    def test_e2e_model_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test E2E_MODEL environment variable."""
        monkeypatch.setenv("E2E_TEST_PROVIDER", "opencode")
        monkeypatch.setenv("E2E_MODEL", "llama2")

        _, provider_config = get_e2e_test_provider()
        assert provider_config["model"] == "llama2"

    def test_agent_provider_support(self, monkeypatch: MonkeyPatch) -> None:
        """Test AGENT_PROVIDER environment variable."""
        monkeypatch.delenv("E2E_TEST_PROVIDER", raising=False)
        monkeypatch.setenv("AGENT_PROVIDER", "opencode")
        monkeypatch.setenv("MODEL", "codellama")

        _, provider_config = get_e2e_test_provider()
        assert provider_config["model"] == "codellama"


# Integration test marker for tests that require actual ollama
integration_test = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "1",
    reason="Integration tests skipped (set SKIP_INTEGRATION_TESTS=0 to run)",
)


@integration_test
class TestOllamaIntegration:
    """Integration tests requiring actual ollama installation."""

    def test_real_ollama_validation(self) -> None:
        """Test validation with real ollama service (requires ollama running)."""
        # This test will only run if ollama is actually installed and running
        result = validate_ollama_available("deepseek-r1")

        if result:
            # If ollama is running, verify it
            provider_name, provider_config = get_e2e_test_provider()
            assert provider_name == "opencode"
            assert provider_config["ai_provider"] == "ollama"
        else:
            # If ollama not running, test should still pass (graceful handling)
            pytest.skip("Ollama not available - skipping integration test")
