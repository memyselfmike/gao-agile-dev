"""AI Analysis Service - Provider-abstracted analysis-only AI calls.

This service provides a lightweight interface for components that need AI for
decision-making without full agent overhead. It uses provider abstraction via
Anthropic client (or other providers) to enable local models, OpenCode, etc.

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
Story: 21.1 - Create AI Analysis Service

Design Pattern: Service Layer
Dependencies: Anthropic client, structlog
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import structlog
import time
import os
import json

# Import anthropic at module level for mockability
try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

logger = structlog.get_logger()


@dataclass
class AnalysisResult:
    """
    Result from AI analysis.

    Attributes:
        response: AI response text (string or JSON)
        model_used: Model that processed the request
        tokens_used: Token count (prompt + completion)
        duration_ms: Processing time in milliseconds
    """

    response: str
    model_used: str
    tokens_used: int
    duration_ms: float


class AIAnalysisService:
    """
    Provider-abstracted AI analysis service.

    Provides simple interface for components that need AI analysis
    without full agent capabilities (tools, artifacts, etc.).

    This service uses the Anthropic client directly for lightweight
    analysis tasks. Future versions can add support for other providers
    via provider abstraction.

    Example:
        ```python
        service = AIAnalysisService(
            api_key="sk-ant-...",
            default_model="claude-sonnet-4-5-20250929"
        )

        result = await service.analyze(
            prompt="Analyze this project complexity",
            response_format="json"
        )

        print(result.response)
        print(f"Tokens used: {result.tokens_used}")
        print(f"Duration: {result.duration_ms}ms")
        ```

    Environment Variables:
        ANTHROPIC_API_KEY: API key for Anthropic (if not provided)
        GAO_DEV_MODEL: Default model name (if not provided)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        """
        Initialize analysis service.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            default_model: Default model if not specified per-call
                          (defaults to GAO_DEV_MODEL env var or claude-sonnet-4-5-20250929)

        Raises:
            ValueError: If API key not provided and not in environment
        """
        # Check anthropic is available
        if anthropic is None:
            raise ImportError(
                "anthropic package required for AIAnalysisService. "
                "Install with: pip install anthropic"
            )

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Provide api_key parameter or set "
                "ANTHROPIC_API_KEY environment variable."
            )

        # Get default model from parameter or environment
        env_model = os.getenv("GAO_DEV_MODEL")
        self.default_model = default_model or env_model or "claude-sonnet-4-5-20250929"

        # Create Anthropic client
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

        self.logger = logger.bind(service="ai_analysis")
        self.logger.info(
            "ai_analysis_service_initialized",
            default_model=self.default_model,
            has_api_key=bool(self.api_key),
        )

    async def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        response_format: str = "json",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> AnalysisResult:
        """
        Send analysis prompt to AI provider.

        Args:
            prompt: User prompt for analysis
            model: Model to use (defaults to configured model)
            system_prompt: Optional system instructions
            response_format: Expected format ("json" or "text")
            max_tokens: Maximum response length
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            AnalysisResult with response and metadata

        Raises:
            AnalysisError: If analysis fails
            AnalysisTimeoutError: If analysis times out
            InvalidModelError: If model is invalid

        Example:
            ```python
            # JSON response
            result = await service.analyze(
                prompt="Rate complexity 1-10: {code}",
                response_format="json"
            )
            data = json.loads(result.response)

            # Text response
            result = await service.analyze(
                prompt="Explain this code",
                response_format="text",
                system_prompt="You are a code reviewer"
            )
            print(result.response)
            ```
        """
        from ..providers.exceptions import (
            AnalysisError,
            AnalysisTimeoutError,
            InvalidModelError,
        )

        model_to_use = model or self.default_model
        start_time = time.time()

        self.logger.info(
            "analysis_started",
            model=model_to_use,
            prompt_length=len(prompt),
            response_format=response_format,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        try:
            # Build messages
            messages: list[Dict[str, Any]] = [{"role": "user", "content": prompt}]

            # Build API call parameters
            api_params: Dict[str, Any] = {
                "model": model_to_use,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            # Add system prompt if provided
            if system_prompt:
                api_params["system"] = system_prompt

            # Execute via Anthropic API
            self.logger.debug("calling_anthropic_api", model=model_to_use)
            response = await self.client.messages.create(**api_params)

            # Extract response content
            response_text = ""
            if response.content:
                # Handle list of content blocks
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Calculate total tokens
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Log success
            self.logger.info(
                "analysis_completed",
                model=model_to_use,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
                response_length=len(response_text),
            )

            # Create result
            result = AnalysisResult(
                response=response_text.strip(),
                model_used=model_to_use,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
            )

            # Validate JSON format if requested
            if response_format == "json":
                try:
                    json.loads(result.response)
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        "json_validation_failed",
                        error=str(e),
                        response_preview=result.response[:100],
                    )
                    # Don't fail, just warn - let caller handle

            return result

        except anthropic.APITimeoutError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "analysis_timeout",
                model=model_to_use,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise AnalysisTimeoutError(f"Analysis timed out: {e}") from e

        except anthropic.NotFoundError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "invalid_model",
                model=model_to_use,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise InvalidModelError(
                f"Model '{model_to_use}' not found or not available: {e}"
            ) from e

        except anthropic.APIError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "analysis_api_error",
                model=model_to_use,
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise AnalysisError(f"Anthropic API error: {e}") from e

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "analysis_failed",
                model=model_to_use,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms,
                exc_info=True,
            )
            raise AnalysisError(f"Analysis failed: {e}") from e

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AIAnalysisService("
            f"default_model={self.default_model}, "
            f"has_api_key={bool(self.api_key)})"
        )
