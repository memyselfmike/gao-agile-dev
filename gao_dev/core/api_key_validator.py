"""API Key Validator for GAO-Dev.

Epic 41: Streamlined Onboarding
Story 41.6: API Key Validation

Validates API keys with various providers using async HTTP requests.
Includes rate limiting, caching, and actionable fix suggestions.
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Optional, Tuple

import httpx
import structlog

logger = structlog.get_logger(__name__)


class ValidationResult(Enum):
    """Result of API key validation."""

    VALID = "valid"
    INVALID = "invalid"
    NETWORK_ERROR = "network_error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    OFFLINE = "offline"
    SKIPPED = "skipped"


class APIKeyValidator:
    """Validate API keys with various providers.

    Features:
    - Async validation with configurable timeout
    - Rate limiting (max 3 attempts per minute per provider)
    - Session caching for successful validations
    - Actionable fix suggestions for common errors
    - Never logs or exposes actual API keys
    """

    TIMEOUT_SECONDS = 5.0
    MAX_ATTEMPTS_PER_MINUTE = 3

    # Provider endpoint configurations
    PROVIDER_ENDPOINTS = {
        "anthropic": "https://api.anthropic.com/v1/models",
        "openai": "https://api.openai.com/v1/models",
        "google": "https://generativelanguage.googleapis.com/v1/models",
        "ollama": "http://localhost:11434/api/tags",
    }

    def __init__(self) -> None:
        """Initialize the API key validator."""
        # Session cache: provider -> validation result
        self._validation_cache: Dict[str, Tuple[ValidationResult, str]] = {}
        # Rate limiting: provider -> list of timestamps
        self._attempt_timestamps: Dict[str, list] = {}

    async def validate(
        self, provider: str, api_key: str
    ) -> Tuple[ValidationResult, str]:
        """Validate API key and return result with message.

        Args:
            provider: Provider name (anthropic, openai, google, ollama)
            api_key: API key to validate (not logged)

        Returns:
            Tuple of (ValidationResult, message)
        """
        # Check cache first
        cache_key = f"{provider}:{hash(api_key)}"
        if cache_key in self._validation_cache:
            cached_result, cached_message = self._validation_cache[cache_key]
            if cached_result == ValidationResult.VALID:
                logger.debug(
                    "api_key_validation_cache_hit",
                    provider=provider,
                )
                return cached_result, cached_message

        # Check rate limiting
        if self._is_rate_limited(provider):
            logger.warning(
                "api_key_validation_rate_limited",
                provider=provider,
            )
            return (
                ValidationResult.RATE_LIMITED,
                "Too many validation attempts. Please wait a minute and try again.",
            )

        # Record attempt
        self._record_attempt(provider)

        # Route to provider-specific validator
        logger.info(
            "api_key_validation_started",
            provider=provider,
        )

        try:
            if provider == "anthropic":
                result, message = await self._validate_anthropic(api_key)
            elif provider == "openai":
                result, message = await self._validate_openai(api_key)
            elif provider == "google":
                result, message = await self._validate_google(api_key)
            elif provider == "ollama":
                result, message = await self._validate_ollama(api_key)
            else:
                result = ValidationResult.INVALID
                message = f"Unknown provider: {provider}"

            # Cache successful validations
            if result == ValidationResult.VALID:
                self._validation_cache[cache_key] = (result, message)
                logger.info(
                    "api_key_validation_success",
                    provider=provider,
                )
            else:
                logger.warning(
                    "api_key_validation_failed",
                    provider=provider,
                    result=result.value,
                )

            return result, message

        except Exception as e:
            # Never log the actual error if it might contain the key
            logger.error(
                "api_key_validation_error",
                provider=provider,
                error_type=type(e).__name__,
            )
            return (
                ValidationResult.NETWORK_ERROR,
                "An unexpected error occurred during validation.",
            )

    async def _validate_anthropic(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate Anthropic API key.

        Args:
            api_key: Anthropic API key

        Returns:
            Tuple of (ValidationResult, message)
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(
                    self.PROVIDER_ENDPOINTS["anthropic"],
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )

                if response.status_code == 200:
                    return ValidationResult.VALID, "API key validated successfully"
                elif response.status_code == 401:
                    return ValidationResult.INVALID, "Invalid API key"
                elif response.status_code == 429:
                    return (
                        ValidationResult.RATE_LIMITED,
                        "Rate limited by provider",
                    )
                else:
                    return (
                        ValidationResult.INVALID,
                        f"Validation failed with status {response.status_code}",
                    )

        except httpx.TimeoutException:
            return ValidationResult.TIMEOUT, "Validation timed out"
        except httpx.ConnectError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Could not connect to Anthropic API",
            )
        except httpx.NetworkError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Network error during validation",
            )

    async def _validate_openai(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate OpenAI API key.

        Args:
            api_key: OpenAI API key

        Returns:
            Tuple of (ValidationResult, message)
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(
                    self.PROVIDER_ENDPOINTS["openai"],
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 200:
                    return ValidationResult.VALID, "API key validated successfully"
                elif response.status_code == 401:
                    return ValidationResult.INVALID, "Invalid API key"
                elif response.status_code == 429:
                    return (
                        ValidationResult.RATE_LIMITED,
                        "Rate limited by provider",
                    )
                else:
                    return (
                        ValidationResult.INVALID,
                        f"Validation failed with status {response.status_code}",
                    )

        except httpx.TimeoutException:
            return ValidationResult.TIMEOUT, "Validation timed out"
        except httpx.ConnectError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Could not connect to OpenAI API",
            )
        except httpx.NetworkError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Network error during validation",
            )

    async def _validate_google(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate Google AI API key.

        Args:
            api_key: Google AI API key

        Returns:
            Tuple of (ValidationResult, message)
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(
                    self.PROVIDER_ENDPOINTS["google"],
                    params={"key": api_key},
                )

                if response.status_code == 200:
                    return ValidationResult.VALID, "API key validated successfully"
                elif response.status_code == 400:
                    # Google returns 400 for invalid API key
                    return ValidationResult.INVALID, "Invalid API key"
                elif response.status_code == 403:
                    # Google returns 403 for permission denied
                    return ValidationResult.INVALID, "API key lacks required permissions"
                elif response.status_code == 429:
                    return (
                        ValidationResult.RATE_LIMITED,
                        "Rate limited by provider",
                    )
                else:
                    return (
                        ValidationResult.INVALID,
                        f"Validation failed with status {response.status_code}",
                    )

        except httpx.TimeoutException:
            return ValidationResult.TIMEOUT, "Validation timed out"
        except httpx.ConnectError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Could not connect to Google AI API",
            )
        except httpx.NetworkError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Network error during validation",
            )

    async def _validate_ollama(self, api_key: str) -> Tuple[ValidationResult, str]:
        """Validate Ollama is running locally.

        Args:
            api_key: Not used for Ollama, but kept for consistent interface

        Returns:
            Tuple of (ValidationResult, message)
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(self.PROVIDER_ENDPOINTS["ollama"])

                if response.status_code == 200:
                    return ValidationResult.VALID, "Ollama server is running"
                else:
                    return (
                        ValidationResult.INVALID,
                        "Ollama server not responding correctly",
                    )

        except httpx.ConnectError:
            return (
                ValidationResult.OFFLINE,
                "Ollama server not running at localhost:11434",
            )
        except httpx.TimeoutException:
            return ValidationResult.TIMEOUT, "Ollama server timed out"
        except httpx.NetworkError:
            return (
                ValidationResult.NETWORK_ERROR,
                "Network error connecting to Ollama",
            )

    def get_fix_suggestion(self, result: ValidationResult, provider: str) -> str:
        """Get actionable fix suggestion for validation failure.

        Args:
            result: The validation result
            provider: The provider name

        Returns:
            Actionable fix suggestion string
        """
        suggestions = {
            ValidationResult.INVALID: {
                "anthropic": (
                    "Get a valid key from https://console.anthropic.com/. "
                    "Check for extra spaces or missing characters."
                ),
                "openai": (
                    "Get a valid key from https://platform.openai.com/api-keys. "
                    "Check for extra spaces or missing characters."
                ),
                "google": (
                    "Get a valid key from https://aistudio.google.com/apikey. "
                    "Check for extra spaces or missing characters."
                ),
                "ollama": (
                    "Ensure Ollama is properly installed and configured. "
                    "Try reinstalling with 'curl -fsSL https://ollama.com/install.sh | sh'"
                ),
            },
            ValidationResult.RATE_LIMITED: {
                "anthropic": (
                    "Wait a few minutes and try again, or use a different API key."
                ),
                "openai": (
                    "Wait a few minutes and try again, or use a different API key."
                ),
                "google": (
                    "Wait a few minutes and try again, or use a different API key."
                ),
                "ollama": "Wait a few minutes and try again.",
            },
            ValidationResult.NETWORK_ERROR: {
                "anthropic": (
                    "Check your internet connection and firewall settings. "
                    "Ensure api.anthropic.com is accessible."
                ),
                "openai": (
                    "Check your internet connection and firewall settings. "
                    "Ensure api.openai.com is accessible."
                ),
                "google": (
                    "Check your internet connection and firewall settings. "
                    "Ensure generativelanguage.googleapis.com is accessible."
                ),
                "ollama": (
                    "Check if Ollama is running with 'ollama serve'. "
                    "Ensure localhost:11434 is not blocked."
                ),
            },
            ValidationResult.TIMEOUT: {
                "anthropic": (
                    "The Anthropic API may be experiencing issues. "
                    "Try again later or skip validation."
                ),
                "openai": (
                    "The OpenAI API may be experiencing issues. "
                    "Try again later or skip validation."
                ),
                "google": (
                    "The Google AI API may be experiencing issues. "
                    "Try again later or skip validation."
                ),
                "ollama": (
                    "Ollama server is slow to respond. "
                    "Try restarting with 'ollama serve'."
                ),
            },
            ValidationResult.OFFLINE: {
                "anthropic": (
                    "You appear to be offline. "
                    "Connect to the internet to validate cloud API keys."
                ),
                "openai": (
                    "You appear to be offline. "
                    "Connect to the internet to validate cloud API keys."
                ),
                "google": (
                    "You appear to be offline. "
                    "Connect to the internet to validate cloud API keys."
                ),
                "ollama": (
                    "Ollama server is not running. "
                    "Start it with 'ollama serve' in a terminal."
                ),
            },
        }

        # Get suggestion for result type and provider
        result_suggestions = suggestions.get(result, {})
        suggestion = result_suggestions.get(
            provider, "Check your configuration and try again."
        )

        return suggestion

    def skip_validation(self, provider: str) -> Tuple[ValidationResult, str]:
        """Mark validation as skipped with appropriate warning.

        Args:
            provider: The provider being skipped

        Returns:
            Tuple of (SKIPPED result, warning message)
        """
        message = (
            "Validation skipped. You may encounter errors if the key is invalid. "
            "The credential will be marked as unvalidated."
        )
        logger.warning(
            "api_key_validation_skipped",
            provider=provider,
        )
        return ValidationResult.SKIPPED, message

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._validation_cache.clear()
        logger.debug("api_key_validation_cache_cleared")

    def clear_rate_limit(self, provider: str) -> None:
        """Clear rate limit history for a provider.

        Args:
            provider: Provider to clear rate limit for
        """
        if provider in self._attempt_timestamps:
            del self._attempt_timestamps[provider]

    def _is_rate_limited(self, provider: str) -> bool:
        """Check if provider is rate limited.

        Args:
            provider: Provider to check

        Returns:
            True if rate limited, False otherwise
        """
        if provider not in self._attempt_timestamps:
            return False

        # Clean up old timestamps (older than 1 minute)
        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute
        self._attempt_timestamps[provider] = [
            ts
            for ts in self._attempt_timestamps[provider]
            if ts > cutoff_time
        ]

        # Check if we've exceeded max attempts
        return len(self._attempt_timestamps[provider]) >= self.MAX_ATTEMPTS_PER_MINUTE

    def _record_attempt(self, provider: str) -> None:
        """Record a validation attempt for rate limiting.

        Args:
            provider: Provider being validated
        """
        if provider not in self._attempt_timestamps:
            self._attempt_timestamps[provider] = []
        self._attempt_timestamps[provider].append(time.time())


async def validate_api_key(
    provider: str, api_key: str
) -> Tuple[ValidationResult, str]:
    """Convenience function for one-off validation.

    Args:
        provider: Provider name
        api_key: API key to validate

    Returns:
        Tuple of (ValidationResult, message)
    """
    validator = APIKeyValidator()
    return await validator.validate(provider, api_key)
