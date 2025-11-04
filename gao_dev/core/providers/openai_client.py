"""OpenAI API client for DirectAPIProvider.

Epic: 11 - Agent Provider Abstraction
Story: 11.10 - Implement Direct API Provider
"""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import openai
except ImportError:
    openai = None  # type: ignore

from .exceptions import ProviderExecutionError, ProviderConfigurationError

logger = structlog.get_logger()


class OpenAIClient:
    """OpenAI API client with streaming support."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 3600,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            base_url: Base URL override (for proxies)
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds

        Raises:
            ProviderConfigurationError: If openai package not installed
        """
        if openai is None:
            raise ProviderConfigurationError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
        )

        logger.debug(
            "openai_client_initialized",
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
        Execute task via OpenAI API.

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
                "openai_streaming_request",
                model=model,
                prompt_length=len(prompt)
            )

            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.debug("openai_streaming_complete", model=model)

        except openai.APIError as e:
            logger.error(
                "openai_api_error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
                model=model
            )
            raise ProviderExecutionError(f"OpenAI API error: {e}") from e

        except Exception as e:
            logger.error(
                "openai_unexpected_error",
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
            logger.debug("openai_validating_api_key")

            # Make minimal request to validate key
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )

            logger.debug("openai_validation_success")
            return True

        except openai.AuthenticationError as e:
            logger.warning("openai_authentication_failed", error=str(e))
            return False

        except openai.APIError as e:
            logger.debug("openai_validation_api_error", error=str(e))
            return False

        except Exception as e:
            logger.warning("openai_validation_error", error=str(e))
            return False

    async def cleanup(self) -> None:
        """Clean up client resources."""
        try:
            # Close client if needed
            if hasattr(self.client, 'close'):
                await self.client.close()

            logger.debug("openai_client_cleaned_up")

        except Exception as e:
            logger.warning("openai_cleanup_error", error=str(e))
