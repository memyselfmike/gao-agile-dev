"""Synchronous provider validator for web API.

This module provides synchronous validation for web API endpoints.
Differs from cli.provider_validator which is async and CLI-focused.

Story 39.29: Provider Validation and Persistence
"""

import os
from dataclasses import dataclass
from typing import List, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WebValidationResult:
    """Result of provider validation for web API.

    Attributes:
        valid: Whether validation passed
        api_key_status: Status of API key ("valid", "invalid", "missing")
        model_available: Whether model is available
        error: Error message if validation failed
        fix_suggestion: Suggestion for fixing the error
        warnings: List of warning messages
    """

    valid: bool
    api_key_status: str = "unknown"  # "valid", "invalid", "missing"
    model_available: bool = True
    error: Optional[str] = None
    fix_suggestion: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self) -> None:
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []


class WebProviderValidator:
    """Synchronous provider validator for web API.

    Validates provider configurations without async operations.
    Designed for FastAPI endpoints.
    """

    # Valid Claude models
    CLAUDE_MODELS = [
        "claude-sonnet-4-5-20250929",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]

    def validate(self, provider: str, model: str) -> WebValidationResult:
        """Validate provider and model combination.

        Args:
            provider: Provider ID (claude_code, opencode, ollama)
            model: Model ID

        Returns:
            WebValidationResult with validation status
        """
        if provider == "claude_code":
            return self._validate_claude_code(model)
        elif provider == "opencode":
            return self._validate_opencode(model)
        elif provider == "ollama":
            return self._validate_ollama(model)
        else:
            return WebValidationResult(
                valid=False,
                error=f"Unknown provider: {provider}",
                fix_suggestion="Select Claude Code, OpenCode, or Ollama",
                api_key_status="unknown",
            )

    def _validate_claude_code(self, model: str) -> WebValidationResult:
        """Validate Claude Code configuration.

        Args:
            model: Model ID to validate

        Returns:
            Validation result
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")

        # Check API key exists
        if not api_key:
            return WebValidationResult(
                valid=False,
                api_key_status="missing",
                error="API key missing",
                fix_suggestion="Set environment variable ANTHROPIC_API_KEY",
            )

        # Validate API key format
        if not api_key.startswith("sk-ant-"):
            return WebValidationResult(
                valid=False,
                api_key_status="invalid",
                error="Invalid API key format",
                fix_suggestion="Anthropic API keys start with 'sk-ant-'",
            )

        # Validate model
        if model not in self.CLAUDE_MODELS:
            return WebValidationResult(
                valid=False,
                api_key_status="valid",
                model_available=False,
                error="Invalid model",
                fix_suggestion=f"Valid models: {', '.join(self.CLAUDE_MODELS)}",
            )

        return WebValidationResult(valid=True, api_key_status="valid")

    def _validate_opencode(self, model: str) -> WebValidationResult:
        """Validate OpenCode configuration.

        Args:
            model: Model ID to validate

        Returns:
            Validation result
        """
        api_key = os.getenv("OPENROUTER_API_KEY")

        # Check API key exists
        if not api_key:
            return WebValidationResult(
                valid=False,
                api_key_status="missing",
                error="API key missing",
                fix_suggestion="Set environment variable OPENROUTER_API_KEY",
            )

        # Validate API key via OpenRouter API
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )

                if response.status_code == 401:
                    return WebValidationResult(
                        valid=False,
                        api_key_status="invalid",
                        error="Invalid API key",
                        fix_suggestion="Check environment variable OPENROUTER_API_KEY",
                    )

                response.raise_for_status()
                return WebValidationResult(valid=True, api_key_status="valid")

        except httpx.TimeoutException:
            logger.warning("openrouter_api_timeout")
            return WebValidationResult(
                valid=False,
                api_key_status="unknown",
                error="OpenRouter API timeout",
                fix_suggestion="Check network connection and try again",
            )
        except Exception as e:
            logger.warning("openrouter_validation_failed", error=str(e))
            return WebValidationResult(
                valid=False,
                api_key_status="unknown",
                error="OpenRouter API unavailable",
                fix_suggestion="Check network connection and API key",
            )

    def _validate_ollama(self, model: str) -> WebValidationResult:
        """Validate Ollama configuration.

        Args:
            model: Model ID to validate

        Returns:
            Validation result
        """
        try:
            # Check if Ollama is running
            with httpx.Client(timeout=2.0) as client:
                response = client.get("http://localhost:11434/api/tags")
                response.raise_for_status()

                # Check if model is available
                data = response.json()
                available_models = [m["name"] for m in data.get("models", [])]

                if model not in available_models:
                    return WebValidationResult(
                        valid=False,
                        api_key_status="valid",
                        model_available=False,
                        error="Model not available",
                        fix_suggestion=f"Pull model with: ollama pull {model}",
                    )

                return WebValidationResult(valid=True, api_key_status="valid")

        except httpx.ConnectError:
            return WebValidationResult(
                valid=False,
                api_key_status="missing",
                error="Ollama not running",
                fix_suggestion="Start Ollama with: ollama serve",
            )
        except httpx.TimeoutException:
            logger.warning("ollama_timeout")
            return WebValidationResult(
                valid=False,
                api_key_status="unknown",
                error="Ollama timeout",
                fix_suggestion="Check if Ollama is running and try again",
            )
        except Exception as e:
            logger.warning("ollama_validation_failed", error=str(e))
            return WebValidationResult(
                valid=False,
                api_key_status="unknown",
                error="Ollama validation failed",
                fix_suggestion=str(e),
            )
