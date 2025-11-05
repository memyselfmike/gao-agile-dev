"""Google Generative AI client for DirectAPIProvider.

Epic: 11 - Agent Provider Abstraction
Story: 11.10 - Implement Direct API Provider
"""

import asyncio
from typing import AsyncGenerator, Optional
import structlog

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore

from .exceptions import ProviderExecutionError, ProviderConfigurationError

logger = structlog.get_logger()


class GoogleClient:
    """Google Generative AI client with streaming support."""

    def __init__(
        self,
        api_key: str,
        timeout: int = 3600,
    ):
        """
        Initialize Google client.

        Args:
            api_key: Google API key
            timeout: Request timeout in seconds

        Raises:
            ProviderConfigurationError: If google-generativeai package not installed
        """
        if genai is None:
            raise ProviderConfigurationError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self.timeout = timeout

        logger.debug("google_client_initialized")

    async def execute_task(
        self,
        prompt: str,
        model: str,
        timeout: int,
    ) -> AsyncGenerator[str, None]:
        """
        Execute task via Google Generative AI API.

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
                "google_streaming_request",
                model=model,
                prompt_length=len(prompt)
            )

            # Create model
            model_instance = genai.GenerativeModel(model)

            # Generate content with streaming
            response = await model_instance.generate_content_async(
                prompt,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

            logger.debug("google_streaming_complete", model=model)

        except Exception as e:
            logger.error(
                "google_api_error",
                error=str(e),
                model=model
            )
            raise ProviderExecutionError(f"Google API error: {e}") from e

    async def validate(self) -> bool:
        """
        Validate API key by making a test request.

        Returns:
            True if valid, False otherwise
        """
        try:
            logger.debug("google_validating_api_key")

            # Make minimal request to validate key
            model = genai.GenerativeModel("gemini-pro")
            response = await model.generate_content_async("test")

            logger.debug("google_validation_success")
            return True

        except Exception as e:
            logger.warning("google_validation_error", error=str(e))
            return False

    async def cleanup(self) -> None:
        """Clean up client resources."""
        # Google client doesn't need cleanup
        logger.debug("google_client_cleaned_up")
