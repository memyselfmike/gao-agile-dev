"""Tests for web provider validator.

Story 39.29: Provider Validation and Persistence
"""

import os
from unittest.mock import Mock, patch

import httpx
import pytest

from gao_dev.web.provider_validator import WebProviderValidator, WebValidationResult


class TestWebProviderValidator:
    """Test WebProviderValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = WebProviderValidator()

    def test_validate_claude_code_missing_api_key(self, monkeypatch):
        """Test Claude Code validation with missing API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = self.validator.validate("claude_code", "claude-sonnet-4-5-20250929")

        assert result.valid is False
        assert result.api_key_status == "missing"
        assert result.error == "API key missing"
        assert "ANTHROPIC_API_KEY" in result.fix_suggestion

    def test_validate_claude_code_invalid_api_key_format(self, monkeypatch):
        """Test Claude Code validation with invalid API key format."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid-key")

        result = self.validator.validate("claude_code", "claude-sonnet-4-5-20250929")

        assert result.valid is False
        assert result.api_key_status == "invalid"
        assert result.error == "Invalid API key format"
        assert "sk-ant-" in result.fix_suggestion

    def test_validate_claude_code_invalid_model(self, monkeypatch):
        """Test Claude Code validation with invalid model."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

        result = self.validator.validate("claude_code", "invalid-model")

        assert result.valid is False
        assert result.api_key_status == "valid"
        assert result.model_available is False
        assert result.error == "Invalid model"

    def test_validate_claude_code_success(self, monkeypatch):
        """Test Claude Code validation success."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

        result = self.validator.validate("claude_code", "claude-sonnet-4-5-20250929")

        assert result.valid is True
        assert result.api_key_status == "valid"
        assert result.model_available is True

    def test_validate_opencode_missing_api_key(self, monkeypatch):
        """Test OpenCode validation with missing API key."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        result = self.validator.validate("opencode", "some-model")

        assert result.valid is False
        assert result.api_key_status == "missing"
        assert result.error == "API key missing"
        assert "OPENROUTER_API_KEY" in result.fix_suggestion

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_opencode_invalid_api_key(self, mock_client_class, monkeypatch):
        """Test OpenCode validation with invalid API key."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-key")

        # Mock httpx.Client context manager
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("opencode", "some-model")

        assert result.valid is False
        assert result.api_key_status == "invalid"
        assert result.error == "Invalid API key"

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_opencode_success(self, mock_client_class, monkeypatch):
        """Test OpenCode validation success."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "valid-key")

        # Mock httpx.Client context manager
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("opencode", "some-model")

        assert result.valid is True
        assert result.api_key_status == "valid"

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_opencode_timeout(self, mock_client_class, monkeypatch):
        """Test OpenCode validation timeout."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "valid-key")

        # Mock httpx.Client to raise TimeoutException
        mock_client = Mock()
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("opencode", "some-model")

        assert result.valid is False
        assert result.api_key_status == "unknown"
        assert "timeout" in result.error.lower()

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_ollama_not_running(self, mock_client_class):
        """Test Ollama validation when service not running."""
        # Mock httpx.Client to raise ConnectError
        mock_client = Mock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("ollama", "llama2")

        assert result.valid is False
        assert result.api_key_status == "missing"
        assert result.error == "Ollama not running"
        assert "ollama serve" in result.fix_suggestion

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_ollama_model_not_available(self, mock_client_class):
        """Test Ollama validation with unavailable model."""
        # Mock httpx.Client to return models list without target model
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "deepseek-r1"},
                {"name": "codellama"},
            ]
        }
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("ollama", "llama2")

        assert result.valid is False
        assert result.api_key_status == "valid"
        assert result.model_available is False
        assert result.error == "Model not available"
        assert "ollama pull" in result.fix_suggestion

    @patch("gao_dev.web.provider_validator.httpx.Client")
    def test_validate_ollama_success(self, mock_client_class):
        """Test Ollama validation success."""
        # Mock httpx.Client to return models list with target model
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "deepseek-r1"},
            ]
        }
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result = self.validator.validate("ollama", "llama2")

        assert result.valid is True
        assert result.api_key_status == "valid"
        assert result.model_available is True

    def test_validate_unknown_provider(self):
        """Test validation with unknown provider."""
        result = self.validator.validate("unknown-provider", "some-model")

        assert result.valid is False
        assert "Unknown provider" in result.error
        assert result.fix_suggestion is not None
