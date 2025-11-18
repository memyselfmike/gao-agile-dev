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
            provider: Provider ID (claude-code, opencode-sdk, etc.)
            model: Model ID

        Returns:
            WebValidationResult with validation status
        """
        if provider == "claude-code":
            return self._validate_claude_code(model)
        elif provider == "opencode-sdk":
            return self._validate_opencode_sdk(model)
        elif provider == "opencode":
            # Legacy opencode (CLI-based)
            return self._validate_opencode(model)
        else:
            return WebValidationResult(
                valid=False,
                error=f"Unknown provider: {provider}",
                fix_suggestion="Select Claude Code or OpenCode SDK",
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

    def _validate_opencode_sdk(self, model: str) -> WebValidationResult:
        """Validate OpenCode SDK configuration.

        OpenCode SDK supports multiple backends (Anthropic, OpenAI, Google, local).
        Validation depends on which backend the model uses.

        Args:
            model: Model ID to validate

        Returns:
            Validation result
        """
        # Determine backend from model ID
        if "claude" in model or "anthropic" in model:
            # Anthropic backend - requires ANTHROPIC_API_KEY
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return WebValidationResult(
                    valid=False,
                    api_key_status="missing",
                    error="API key missing for Claude models",
                    fix_suggestion="Set environment variable ANTHROPIC_API_KEY",
                )
            return WebValidationResult(valid=True, api_key_status="valid")

        elif "gpt" in model or "openai" in model:
            # OpenAI backend - requires OPENAI_API_KEY
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return WebValidationResult(
                    valid=False,
                    api_key_status="missing",
                    error="API key missing for OpenAI models",
                    fix_suggestion="Set environment variable OPENAI_API_KEY",
                )
            return WebValidationResult(valid=True, api_key_status="valid")

        elif "gemini" in model or "google" in model:
            # Google backend - requires GOOGLE_API_KEY
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return WebValidationResult(
                    valid=False,
                    api_key_status="missing",
                    error="API key missing for Google models",
                    fix_suggestion="Set environment variable GOOGLE_API_KEY",
                )
            return WebValidationResult(valid=True, api_key_status="valid")

        elif "deepseek" in model or "llama" in model or "codellama" in model:
            # Local models - no API key needed, just check OpenCode server
            # For now, assume valid (OpenCode SDK manages local models)
            return WebValidationResult(
                valid=True,
                api_key_status="valid",
                warnings=["Local models require OpenCode server running"],
            )

        else:
            # Unknown model type
            return WebValidationResult(
                valid=False,
                api_key_status="unknown",
                error="Unknown model type",
                fix_suggestion="Select a valid model from the list",
            )
