"""Tests for API Key Validator.

Epic 41: Streamlined Onboarding
Story 41.6: API Key Validation

Tests cover:
- Each provider validation (Anthropic, OpenAI, Google, Ollama)
- Rate limiting
- Session caching
- Error handling
- Fix suggestions
- Skip option
- Retry option
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from gao_dev.core.api_key_validator import (
    APIKeyValidator,
    ValidationResult,
    validate_api_key,
)


class TestValidationResult:
    """Tests for ValidationResult enum."""

    def test_enum_values(self):
        """Test all expected enum values exist."""
        assert ValidationResult.VALID.value == "valid"
        assert ValidationResult.INVALID.value == "invalid"
        assert ValidationResult.NETWORK_ERROR.value == "network_error"
        assert ValidationResult.RATE_LIMITED.value == "rate_limited"
        assert ValidationResult.TIMEOUT.value == "timeout"
        assert ValidationResult.OFFLINE.value == "offline"
        assert ValidationResult.SKIPPED.value == "skipped"


class TestAPIKeyValidatorBasics:
    """Tests for APIKeyValidator basic functionality."""

    def test_initialization(self):
        """Test validator initializes correctly."""
        validator = APIKeyValidator()
        assert validator.TIMEOUT_SECONDS == 5.0
        assert validator.MAX_ATTEMPTS_PER_MINUTE == 3
        assert len(validator._validation_cache) == 0
        assert len(validator._attempt_timestamps) == 0

    def test_provider_endpoints_configured(self):
        """Test all provider endpoints are configured."""
        validator = APIKeyValidator()
        assert "anthropic" in validator.PROVIDER_ENDPOINTS
        assert "openai" in validator.PROVIDER_ENDPOINTS
        assert "google" in validator.PROVIDER_ENDPOINTS
        assert "ollama" in validator.PROVIDER_ENDPOINTS

    def test_clear_cache(self):
        """Test cache clearing works."""
        validator = APIKeyValidator()
        validator._validation_cache["test"] = (ValidationResult.VALID, "message")
        validator.clear_cache()
        assert len(validator._validation_cache) == 0

    def test_clear_rate_limit(self):
        """Test rate limit clearing works."""
        validator = APIKeyValidator()
        validator._attempt_timestamps["anthropic"] = [time.time()]
        validator.clear_rate_limit("anthropic")
        assert "anthropic" not in validator._attempt_timestamps

    def test_clear_rate_limit_nonexistent(self):
        """Test clearing nonexistent rate limit is safe."""
        validator = APIKeyValidator()
        validator.clear_rate_limit("nonexistent")  # Should not raise


class TestAnthropicValidation:
    """Tests for Anthropic API key validation."""

    @pytest.mark.asyncio
    async def test_valid_key(self):
        """Test validation with valid Anthropic key."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "sk-ant-test-key")

            assert result == ValidationResult.VALID
            assert message == "API key validated successfully"

    @pytest.mark.asyncio
    async def test_invalid_key_401(self):
        """Test validation with invalid Anthropic key (401)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "invalid-key")

            assert result == ValidationResult.INVALID
            assert message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_rate_limited_429(self):
        """Test validation when rate limited by Anthropic (429)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.RATE_LIMITED
            assert "Rate limited" in message

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test validation timeout for Anthropic."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.TIMEOUT
            assert "timed out" in message.lower()

    @pytest.mark.asyncio
    async def test_connect_error(self):
        """Test validation connect error for Anthropic."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.NETWORK_ERROR
            assert "Could not connect" in message

    @pytest.mark.asyncio
    async def test_network_error(self):
        """Test validation network error for Anthropic."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.NetworkError("Network error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.NETWORK_ERROR
            assert "Network error" in message

    @pytest.mark.asyncio
    async def test_unexpected_status_code(self):
        """Test validation with unexpected status code."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.INVALID
            assert "500" in message


class TestOpenAIValidation:
    """Tests for OpenAI API key validation."""

    @pytest.mark.asyncio
    async def test_valid_key(self):
        """Test validation with valid OpenAI key."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("openai", "sk-test-key")

            assert result == ValidationResult.VALID
            assert message == "API key validated successfully"

    @pytest.mark.asyncio
    async def test_invalid_key_401(self):
        """Test validation with invalid OpenAI key (401)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("openai", "invalid-key")

            assert result == ValidationResult.INVALID
            assert message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_rate_limited_429(self):
        """Test validation when rate limited by OpenAI (429)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("openai", "test-key")

            assert result == ValidationResult.RATE_LIMITED
            assert "Rate limited" in message

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test validation timeout for OpenAI."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("openai", "test-key")

            assert result == ValidationResult.TIMEOUT
            assert "timed out" in message.lower()

    @pytest.mark.asyncio
    async def test_bearer_token_format(self):
        """Test that OpenAI validation uses Bearer token format."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await validator.validate("openai", "sk-test-key")

            # Verify the Authorization header format
            call_args = mock_client.get.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer sk-test-key"


class TestGoogleValidation:
    """Tests for Google AI API key validation."""

    @pytest.mark.asyncio
    async def test_valid_key(self):
        """Test validation with valid Google key."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "AIzaSy-test-key")

            assert result == ValidationResult.VALID
            assert message == "API key validated successfully"

    @pytest.mark.asyncio
    async def test_invalid_key_400(self):
        """Test validation with invalid Google key (400)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "invalid-key")

            assert result == ValidationResult.INVALID
            assert message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_permission_denied_403(self):
        """Test validation with permission denied (403)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "test-key")

            assert result == ValidationResult.INVALID
            assert "lacks required permissions" in message

    @pytest.mark.asyncio
    async def test_rate_limited_429(self):
        """Test validation when rate limited by Google (429)."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "test-key")

            assert result == ValidationResult.RATE_LIMITED
            assert "Rate limited" in message

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test validation timeout for Google."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "test-key")

            assert result == ValidationResult.TIMEOUT
            assert "timed out" in message.lower()

    @pytest.mark.asyncio
    async def test_connect_error(self):
        """Test validation connect error for Google."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("google", "test-key")

            assert result == ValidationResult.NETWORK_ERROR
            assert "Could not connect" in message

    @pytest.mark.asyncio
    async def test_api_key_param_format(self):
        """Test that Google validation uses query param format."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await validator.validate("google", "AIzaSy-test-key")

            # Verify the params include the key
            call_args = mock_client.get.call_args
            params = call_args.kwargs.get("params", {})
            assert "key" in params
            assert params["key"] == "AIzaSy-test-key"


class TestOllamaValidation:
    """Tests for Ollama validation."""

    @pytest.mark.asyncio
    async def test_server_running(self):
        """Test validation when Ollama server is running."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("ollama", "")

            assert result == ValidationResult.VALID
            assert "running" in message.lower()

    @pytest.mark.asyncio
    async def test_server_not_running(self):
        """Test validation when Ollama server is not running."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("ollama", "")

            assert result == ValidationResult.OFFLINE
            assert "not running" in message.lower()

    @pytest.mark.asyncio
    async def test_server_bad_response(self):
        """Test validation when Ollama returns bad response."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("ollama", "")

            assert result == ValidationResult.INVALID
            assert "not responding correctly" in message

    @pytest.mark.asyncio
    async def test_server_timeout(self):
        """Test validation when Ollama server times out."""
        validator = APIKeyValidator()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validator.validate("ollama", "")

            assert result == ValidationResult.TIMEOUT
            assert "timed out" in message.lower()


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_after_max_attempts(self):
        """Test rate limiting after max attempts."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 401  # Invalid to avoid caching

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Make max attempts
            for _ in range(validator.MAX_ATTEMPTS_PER_MINUTE):
                await validator.validate("anthropic", "test-key")

            # Next attempt should be rate limited
            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.RATE_LIMITED
            assert "wait" in message.lower()

    @pytest.mark.asyncio
    async def test_rate_limit_per_provider(self):
        """Test rate limiting is per provider."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Max out anthropic
            for _ in range(validator.MAX_ATTEMPTS_PER_MINUTE):
                await validator.validate("anthropic", "test-key")

            # OpenAI should still work
            result, message = await validator.validate("openai", "test-key")
            assert result != ValidationResult.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_rate_limit_expires(self):
        """Test rate limit expires after 1 minute."""
        validator = APIKeyValidator()

        # Manually set old timestamps
        old_time = time.time() - 61  # 61 seconds ago
        validator._attempt_timestamps["anthropic"] = [old_time] * 3

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should not be rate limited
            result, message = await validator.validate("anthropic", "test-key")
            assert result == ValidationResult.VALID


class TestCaching:
    """Tests for session caching functionality."""

    @pytest.mark.asyncio
    async def test_successful_validation_cached(self):
        """Test successful validations are cached."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call
            await validator.validate("anthropic", "test-key")
            # Second call should use cache
            result, message = await validator.validate("anthropic", "test-key")

            assert result == ValidationResult.VALID
            # Should only be called once
            assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_failed_validation_not_cached(self):
        """Test failed validations are not cached."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call
            await validator.validate("anthropic", "test-key")
            # Second call should not use cache
            await validator.validate("anthropic", "test-key")

            # Should be called twice
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_different_keys_different_cache(self):
        """Test different keys have separate cache entries."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Two different keys
            await validator.validate("anthropic", "key-1")
            await validator.validate("anthropic", "key-2")

            # Both should make actual calls
            assert mock_client.get.call_count == 2


class TestFixSuggestions:
    """Tests for fix suggestion functionality."""

    def test_invalid_key_anthropic(self):
        """Test fix suggestion for invalid Anthropic key."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.INVALID, "anthropic")
        assert "console.anthropic.com" in suggestion
        assert "spaces" in suggestion.lower()

    def test_invalid_key_openai(self):
        """Test fix suggestion for invalid OpenAI key."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.INVALID, "openai")
        assert "platform.openai.com" in suggestion

    def test_invalid_key_google(self):
        """Test fix suggestion for invalid Google key."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.INVALID, "google")
        assert "aistudio.google.com" in suggestion
        assert "spaces" in suggestion.lower()

    def test_network_error_google(self):
        """Test fix suggestion for Google network error."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(
            ValidationResult.NETWORK_ERROR, "google"
        )
        assert "generativelanguage.googleapis.com" in suggestion

    def test_invalid_key_ollama(self):
        """Test fix suggestion for invalid Ollama."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.INVALID, "ollama")
        assert "install" in suggestion.lower()

    def test_rate_limited(self):
        """Test fix suggestion for rate limited."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(
            ValidationResult.RATE_LIMITED, "anthropic"
        )
        assert "wait" in suggestion.lower()

    def test_network_error_anthropic(self):
        """Test fix suggestion for network error."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(
            ValidationResult.NETWORK_ERROR, "anthropic"
        )
        assert "internet" in suggestion.lower() or "connection" in suggestion.lower()

    def test_network_error_ollama(self):
        """Test fix suggestion for Ollama network error."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(
            ValidationResult.NETWORK_ERROR, "ollama"
        )
        assert "ollama serve" in suggestion

    def test_timeout(self):
        """Test fix suggestion for timeout."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.TIMEOUT, "anthropic")
        assert "issues" in suggestion.lower() or "try again" in suggestion.lower()

    def test_offline_cloud(self):
        """Test fix suggestion for offline cloud provider."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.OFFLINE, "anthropic")
        assert "offline" in suggestion.lower()

    def test_offline_ollama(self):
        """Test fix suggestion for offline Ollama."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.OFFLINE, "ollama")
        assert "ollama serve" in suggestion

    def test_unknown_result_type(self):
        """Test fix suggestion for unknown result type."""
        validator = APIKeyValidator()
        # VALID doesn't need a fix, but should return default
        suggestion = validator.get_fix_suggestion(ValidationResult.VALID, "anthropic")
        assert "try again" in suggestion.lower()

    def test_unknown_provider(self):
        """Test fix suggestion for unknown provider."""
        validator = APIKeyValidator()
        suggestion = validator.get_fix_suggestion(ValidationResult.INVALID, "unknown")
        assert "try again" in suggestion.lower()


class TestSkipValidation:
    """Tests for skip validation functionality."""

    def test_skip_returns_skipped_result(self):
        """Test skip validation returns SKIPPED result."""
        validator = APIKeyValidator()
        result, message = validator.skip_validation("anthropic")
        assert result == ValidationResult.SKIPPED

    def test_skip_returns_warning_message(self):
        """Test skip validation returns warning message."""
        validator = APIKeyValidator()
        result, message = validator.skip_validation("anthropic")
        assert "skipped" in message.lower()
        assert "warning" in message.lower() or "error" in message.lower()
        assert "unvalidated" in message.lower()


class TestUnknownProvider:
    """Tests for unknown provider handling."""

    @pytest.mark.asyncio
    async def test_unknown_provider(self):
        """Test validation with unknown provider."""
        validator = APIKeyValidator()
        result, message = await validator.validate("unknown-provider", "test-key")
        assert result == ValidationResult.INVALID
        assert "unknown-provider" in message.lower()


class TestConvenienceFunction:
    """Tests for the validate_api_key convenience function."""

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience function works."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result, message = await validate_api_key("anthropic", "test-key")
            assert result == ValidationResult.VALID


class TestSecurityLogging:
    """Tests to ensure API keys are never logged."""

    @pytest.mark.asyncio
    async def test_key_not_in_logs_on_success(self):
        """Test API key is not logged on success."""
        validator = APIKeyValidator()
        test_key = "super-secret-key-12345"

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("gao_dev.core.api_key_validator.logger") as mock_logger:
                await validator.validate("anthropic", test_key)

                # Check no log call contains the key
                for call in mock_logger.method_calls:
                    args_str = str(call)
                    assert test_key not in args_str

    @pytest.mark.asyncio
    async def test_key_not_in_logs_on_error(self):
        """Test API key is not logged on error."""
        validator = APIKeyValidator()
        test_key = "super-secret-key-67890"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Error with key " + test_key)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("gao_dev.core.api_key_validator.logger") as mock_logger:
                await validator.validate("anthropic", test_key)

                # Check no log call contains the key
                for call in mock_logger.method_calls:
                    args_str = str(call)
                    assert test_key not in args_str


class TestTimeoutConfiguration:
    """Tests for timeout configuration."""

    @pytest.mark.asyncio
    async def test_timeout_is_five_seconds(self):
        """Test timeout is configured to 5 seconds per AC7."""
        validator = APIKeyValidator()
        assert validator.TIMEOUT_SECONDS == 5.0

    @pytest.mark.asyncio
    async def test_httpx_client_uses_timeout(self):
        """Test httpx client is created with timeout."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await validator.validate("anthropic", "test-key")

            # Verify AsyncClient was called with timeout
            mock_client_class.assert_called_with(timeout=5.0)


class TestAnthropicHeaderFormat:
    """Tests for Anthropic API header format."""

    @pytest.mark.asyncio
    async def test_anthropic_uses_x_api_key_header(self):
        """Test Anthropic validation uses x-api-key header."""
        validator = APIKeyValidator()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await validator.validate("anthropic", "test-key")

            # Verify the header format
            call_args = mock_client.get.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "x-api-key" in headers
            assert headers["x-api-key"] == "test-key"
            assert "anthropic-version" in headers


class TestRetryScenario:
    """Tests for retry scenario (AC7)."""

    @pytest.mark.asyncio
    async def test_retry_after_failure(self):
        """Test retry works after initial failure."""
        validator = APIKeyValidator()

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 401

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # First call fails, second succeeds
            mock_client.get.side_effect = [mock_response_fail, mock_response_success]
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First attempt fails
            result1, _ = await validator.validate("anthropic", "test-key")
            assert result1 == ValidationResult.INVALID

            # Retry succeeds
            result2, _ = await validator.validate("anthropic", "test-key")
            assert result2 == ValidationResult.VALID
