"""AI Analysis Service - Provider-abstracted analysis-only AI calls.

This service provides a lightweight interface for components that need AI for
decision-making without full agent overhead. It uses ProcessExecutor for provider
abstraction to enable Claude Code, OpenCode, local models (Ollama), etc.

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
Story: 21.1 - Create AI Analysis Service

Design Pattern: Service Layer
Dependencies: ProcessExecutor, structlog
"""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
import structlog
import time
import os
import json

if TYPE_CHECKING:
    from ..services.process_executor import ProcessExecutor

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

    This service uses ProcessExecutor for provider abstraction, enabling
    use of any AI provider (Claude Code, OpenCode, local Ollama models, etc.).

    Example:
        ```python
        from gao_dev.core.services.process_executor import ProcessExecutor

        executor = ProcessExecutor(project_root=Path("/project"))
        service = AIAnalysisService(
            executor=executor,
            default_model="deepseek-r1:8b"
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
        GAO_DEV_MODEL: Default model name (if not provided)
        AGENT_PROVIDER: Provider to use (claude-code, opencode-sdk, etc.)
    """

    def __init__(
        self,
        executor: "ProcessExecutor",
        default_model: Optional[str] = None,
    ):
        """
        Initialize analysis service.

        Args:
            executor: ProcessExecutor instance for provider abstraction
            default_model: Default model if not specified per-call
                          (defaults to GAO_DEV_MODEL env var or claude-sonnet-4-5-20250929)
        """
        self.executor = executor

        # Get default model from parameter or environment
        env_model = os.getenv("GAO_DEV_MODEL")
        self.default_model = default_model or env_model or "claude-sonnet-4-5-20250929"

        self.logger = logger.bind(service="ai_analysis")
        self.logger.info(
            "ai_analysis_service_initialized",
            default_model=self.default_model,
            provider=self.executor.provider.name if hasattr(self.executor, 'provider') else 'unknown',
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
            # Build task prompt
            task_prompt = prompt
            if system_prompt:
                task_prompt = f"{system_prompt}\n\n{prompt}"

            # Execute via ProcessExecutor (provider abstraction)
            self.logger.debug(
                "calling_provider_via_executor",
                model=model_to_use,
                provider=self.executor.provider.name if hasattr(self.executor, 'provider') else 'unknown'
            )

            # Collect all streamed output
            response_chunks = []
            async for chunk in self.executor.execute_agent_task(
                task=task_prompt,
                model=model_to_use,
                tools=[],  # No tools for analysis
                timeout=None
            ):
                response_chunks.append(chunk)

            # Join all chunks
            response_text = "".join(response_chunks)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Estimate tokens (rough estimate: ~4 chars per token)
            tokens_used = (len(task_prompt) + len(response_text)) // 4

            # Log success
            self.logger.info(
                "analysis_completed",
                model=model_to_use,
                tokens_used=tokens_used,
                duration_ms=duration_ms,
                response_length=len(response_text),
            )

            # Clean response (strip markdown code blocks if present)
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                # Extract JSON from markdown code blocks
                json_start = cleaned_response.index("```json") + 7
                json_end = cleaned_response.index("```", json_start)
                cleaned_response = cleaned_response[json_start:json_end].strip()
            elif cleaned_response.startswith("```"):
                # Handle generic code blocks
                json_start = cleaned_response.index("```") + 3
                json_end = cleaned_response.index("```", json_start)
                cleaned_response = cleaned_response[json_start:json_end].strip()

            # Create result
            result = AnalysisResult(
                response=cleaned_response,
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

        except TimeoutError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "analysis_timeout",
                model=model_to_use,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise AnalysisTimeoutError(f"Analysis timed out: {e}") from e

        except ValueError as e:
            # Model not found or invalid
            duration_ms = (time.time() - start_time) * 1000
            if "model" in str(e).lower() or "not found" in str(e).lower():
                self.logger.error(
                    "invalid_model",
                    model=model_to_use,
                    duration_ms=duration_ms,
                    error=str(e),
                )
                raise InvalidModelError(
                    f"Model '{model_to_use}' not found or not available: {e}"
                ) from e
            # Re-raise other ValueErrors
            self.logger.error(
                "analysis_failed",
                model=model_to_use,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration_ms,
            )
            raise AnalysisError(f"Analysis failed: {e}") from e

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
