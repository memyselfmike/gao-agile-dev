"""Anthropic API client for DirectAPIProvider.

Epic: 11 - Agent Provider Abstraction
Story: 11.10 - Implement Direct API Provider
"""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore

from .exceptions import ProviderExecutionError, ProviderConfigurationError

logger = structlog.get_logger()


class AnthropicClient:
    """Anthropic API client with streaming support."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
    ):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            base_url: Base URL override (for proxies)
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds

        Raises:
            ProviderConfigurationError: If anthropic package not installed
        """
        if anthropic is None:
            raise ProviderConfigurationError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )

        logger.debug(
            "anthropic_client_initialized",
            has_base_url=base_url is not None,
            max_retries=max_retries
        )

    async def execute_task(
        self,
        prompt: str,
        model: str,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via Anthropic API.

        Args:
            prompt: Task prompt
            model: Model ID (provider-specific)
            timeout: Timeout in seconds

        Yields:
            Response chunks

        Raises:
            ProviderExecutionError: If API call fails
        """
        try:
            logger.debug(
                "anthropic_streaming_request",
                model=model,
                prompt_length=len(prompt)
            )

            # Create streaming message
            async with self.client.messages.stream(
                model=model,
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.debug("anthropic_streaming_complete", model=model)

        except anthropic.APIError as e:
            logger.error(
                "anthropic_api_error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
                model=model
            )
            raise ProviderExecutionError(f"Anthropic API error: {e}") from e

        except Exception as e:
            logger.error(
                "anthropic_unexpected_error",
                error=str(e),
                model=model
            )
            raise ProviderExecutionError(f"Unexpected error: {e}") from e

    async def validate(self) -> bool:
        """
        Validate API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        try:
            logger.debug("anthropic_validating_api_key")

            # Make minimal request to validate key
            response = await self.client.messages.create(
                model="claude-haiku-3-20250219",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )

            logger.debug("anthropic_validation_success")
            return True

        except anthropic.AuthenticationError as e:
            logger.warning("anthropic_authentication_failed", error=str(e))
            return False

        except anthropic.APIError as e:
            # Other API errors might still mean valid auth
            logger.debug("anthropic_validation_api_error", error=str(e))
            return False

        except Exception as e:
            logger.warning("anthropic_validation_error", error=str(e))
            return False

    async def cleanup(self) -> None:
        """Clean up client resources."""
        try:
            # Close client if needed
            if hasattr(self.client, 'close'):
                await self.client.close()

            logger.debug("anthropic_client_cleaned_up")

        except Exception as e:
            logger.warning("anthropic_cleanup_error", error=str(e))
