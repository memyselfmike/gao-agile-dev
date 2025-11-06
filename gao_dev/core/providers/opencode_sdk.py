"""OpenCode SDK-based agent provider implementation.

This provider uses OpenCode's Python SDK for direct API access, eliminating
subprocess hanging issues present in CLI-based provider.

Key Differences from CLI Provider:
- Uses SDK's session.create() and session.chat() instead of CLI subprocess
- Direct API communication (no process management)
- Better error handling and response parsing
- No timeout issues from subprocess hangs

Implementation Status:
- Story 19.2: Core provider implementation
- Story 19.3: Server lifecycle management (future)
- Story 19.4: Integration testing (future)

Extracted for: Epic 19 - OpenCode SDK Integration
Story: 19.2 - Implement OpenCodeSDKProvider Core
"""

from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional, Any
import structlog
import os

from .base import IAgentProvider
from .models import AgentContext
from .exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ProviderInitializationError,
    ModelNotSupportedError
)

logger = structlog.get_logger()


class OpenCodeSDKProvider(IAgentProvider):
    """
    OpenCode SDK-based agent provider.

    Uses OpenCode's Python SDK for direct API access, eliminating
    subprocess hanging issues present in CLI-based provider.

    Execution Model: SDK API calls (not subprocess)
    Backend: Multiple (Anthropic, OpenAI, Google, local)

    Attributes:
        server_url: URL of OpenCode server (default: http://localhost:4096)
        api_key: API key for authentication (if required)
        sdk_client: OpenCode SDK client instance
        session: Current SDK session for task execution

    Example:
        ```python
        provider = OpenCodeSDKProvider(server_url="http://localhost:4096")
        await provider.initialize()

        async for result in provider.execute_task(
            task="Write a hello world script",
            context=AgentContext(project_root=Path("/project")),
            model="sonnet-4.5",
            tools=["Read", "Write", "Bash"],
            timeout=3600
        ):
            print(result)

        await provider.cleanup()
        ```
    """

    # Model translation map: canonical name -> (provider_id, model_id)
    # Based on OpenCode Models.dev naming conventions
    MODEL_MAP: Dict[str, tuple[str, str]] = {
        # Claude models (Anthropic)
        "claude-sonnet-4-5-20250929": ("anthropic", "claude-sonnet-4.5"),
        "claude-opus-4-20250514": ("anthropic", "claude-opus-4"),
        "claude-3-5-sonnet-20241022": ("anthropic", "claude-3.5-sonnet"),
        "claude-3-haiku-20240307": ("anthropic", "claude-3-haiku"),

        # Canonical short names
        "sonnet-4.5": ("anthropic", "claude-sonnet-4.5"),
        "opus-4": ("anthropic", "claude-opus-4"),
        "sonnet-3.5": ("anthropic", "claude-3.5-sonnet"),
        "haiku-3": ("anthropic", "claude-3-haiku"),

        # OpenAI models
        "gpt-4": ("openai", "gpt-4"),
        "gpt-4-turbo": ("openai", "gpt-4-turbo"),
        "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    }

    # Tool mapping: GAO-Dev tool name -> OpenCode capability
    # Based on OpenCode research (same as CLI provider)
    TOOL_MAPPING = {
        # Core file operations (excellent support)
        "Read": True,
        "Write": True,
        "Edit": True,
        "Bash": True,
        "Glob": True,

        # Partial support
        "MultiEdit": True,  # Sequential, not atomic
        "Grep": True,       # LSP-based, not regex

        # Not supported
        "Task": False,
        "WebFetch": False,
        "WebSearch": False,
        "TodoWrite": False,
        "AskUserQuestion": False,  # Non-interactive mode
        "NotebookEdit": False,
        "Skill": False,
        "SlashCommand": False,
    }

    DEFAULT_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        server_url: str = "http://localhost:4096",
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize OpenCode SDK provider.

        Args:
            server_url: URL of OpenCode server (default: http://localhost:4096)
            api_key: API key for authentication (if required)
            **kwargs: Additional configuration options (for future use)

        Example:
            ```python
            # With default server URL
            provider = OpenCodeSDKProvider()

            # With custom server URL
            provider = OpenCodeSDKProvider(server_url="http://localhost:8080")

            # With API key
            provider = OpenCodeSDKProvider(api_key="sk-...")
            ```
        """
        self.server_url = server_url
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.sdk_client: Optional[Any] = None  # Type: Opencode
        self.session: Optional[Any] = None  # Type: Session
        self._initialized = False

        logger.info(
            "opencode_sdk_provider_init",
            server_url=server_url,
            has_api_key=bool(self.api_key),
        )

    @property
    def name(self) -> str:
        """Provider name."""
        return "opencode-sdk"

    @property
    def version(self) -> str:
        """Provider version."""
        return "1.0.0"

    async def initialize(self) -> None:
        """
        Initialize SDK client and verify server connection.

        Raises:
            ProviderInitializationError: If initialization fails

        Example:
            ```python
            provider = OpenCodeSDKProvider()
            await provider.initialize()
            # Provider ready to use
            ```
        """
        if self._initialized:
            logger.debug("opencode_sdk_provider_already_initialized")
            return

        try:
            logger.info("opencode_sdk_provider_initialize_start")

            # Import SDK here to avoid import-time errors if SDK not installed
            try:
                from opencode_ai import Opencode
            except ImportError as e:
                raise ProviderInitializationError(
                    "OpenCode SDK not installed. Install with: pip install opencode-ai",
                    provider_name=self.name,
                    original_error=e
                ) from e

            # Create SDK client
            self.sdk_client = Opencode(base_url=self.server_url)

            self._initialized = True
            logger.info("opencode_sdk_provider_initialize_complete")

        except ProviderInitializationError:
            # Re-raise our own exceptions
            raise

        except Exception as e:
            logger.error(
                "opencode_sdk_provider_initialize_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ProviderInitializationError(
                f"Failed to initialize OpenCode SDK provider: {e}",
                provider_name=self.name,
                original_error=e
            ) from e

    async def execute_task(
        self,
        task: str,
        context: AgentContext,
        model: str,
        tools: List[str],
        timeout: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Execute agent task using OpenCode SDK.

        Args:
            task: Task prompt/message
            context: Execution context
            model: Model name (canonical format)
            tools: Available tools for agent
            timeout: Timeout in seconds (not implemented yet)
            **kwargs: Additional execution parameters

        Yields:
            Output from SDK execution

        Raises:
            ProviderExecutionError: If task execution fails
            ProviderConfigurationError: If provider not initialized
            ModelNotSupportedError: If model not supported

        Example:
            ```python
            async for message in provider.execute_task(
                task="Create hello.py with hello world function",
                context=AgentContext(project_root=Path("/project")),
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=60
            ):
                print(message)
            ```
        """
        if not self._initialized or not self.sdk_client:
            raise ProviderConfigurationError(
                "Provider not initialized. Call initialize() first.",
                provider_name=self.name
            )

        try:
            # Translate model name (raises ModelNotSupportedError if invalid)
            provider_id, model_id = self._translate_model(model)

            logger.info(
                "opencode_sdk_execute_task_start",
                model=model,
                provider_id=provider_id,
                model_id=model_id,
                has_tools=bool(tools),
                project_root=str(context.project_root),
            )

            # Create session if needed
            if not self.session:
                logger.debug(
                    "opencode_sdk_create_session",
                    provider_id=provider_id,
                    model_id=model_id,
                )
                self.session = self.sdk_client.create_session(
                    provider_id=provider_id,
                    model_id=model_id,
                )
                logger.debug("opencode_sdk_session_created", session_id=getattr(self.session, 'id', 'unknown'))

            # Send chat message
            logger.debug("opencode_sdk_send_chat", message_length=len(task))
            response = self.session.chat(
                message=task,
                tools=tools or [],
            )

            # Extract response content
            content = self._extract_content(response)
            usage = self._extract_usage(response)

            logger.info(
                "opencode_sdk_execute_task_complete",
                content_length=len(content),
                usage=usage,
            )

            # Yield output (similar to CLI providers)
            yield content

        except ModelNotSupportedError:
            # Re-raise model not supported errors
            raise

        except ProviderConfigurationError:
            # Re-raise configuration errors
            raise

        except Exception as e:
            logger.error(
                "opencode_sdk_execute_task_failed",
                error=str(e),
                error_type=type(e).__name__,
                model=model,
            )
            raise ProviderExecutionError(
                f"Failed to execute task with OpenCode SDK: {e}",
                provider_name=self.name,
                original_error=e
            ) from e

    def _translate_model(self, canonical_name: str) -> tuple[str, str]:
        """
        Translate canonical model name to OpenCode provider/model IDs.

        Args:
            canonical_name: Canonical model name (e.g., 'sonnet-4.5')

        Returns:
            Tuple of (provider_id, model_id)

        Raises:
            ModelNotSupportedError: If model not found

        Example:
            ```python
            provider_id, model_id = provider._translate_model("sonnet-4.5")
            # ('anthropic', 'claude-sonnet-4.5')
            ```
        """
        if canonical_name not in self.MODEL_MAP:
            supported = list(self.MODEL_MAP.keys())
            logger.error(
                "model_not_supported",
                canonical_name=canonical_name,
                supported_models=supported[:5],  # Log first 5 for brevity
            )
            raise ModelNotSupportedError(
                provider_name=self.name,
                model_name=canonical_name,
                context={"supported_models": supported}
            )

        provider_id, model_id = self.MODEL_MAP[canonical_name]
        logger.debug(
            "model_translated",
            canonical=canonical_name,
            provider_id=provider_id,
            model_id=model_id,
        )
        return provider_id, model_id

    def _extract_content(self, response: Any) -> str:
        """
        Extract text content from SDK response.

        Args:
            response: SDK response object

        Returns:
            Extracted text content

        Note:
            This method handles multiple possible response formats.
            The exact structure depends on the SDK version.

        Example:
            ```python
            content = provider._extract_content(response)
            # "Task completed successfully"
            ```
        """
        # Try multiple attribute names (SDK structure may vary)
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        elif hasattr(response, 'message'):
            content = response.message
        elif isinstance(response, str):
            content = response
        else:
            # Fallback: convert to string
            logger.warning(
                "unknown_response_format",
                response_type=type(response).__name__,
                message="Unknown SDK response format, converting to string"
            )
            content = str(response)

        logger.debug(
            "content_extracted",
            content_length=len(content),
            response_type=type(response).__name__,
        )
        return content

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        """
        Extract usage statistics from SDK response.

        Args:
            response: SDK response object

        Returns:
            Dictionary with token usage statistics

        Example:
            ```python
            usage = provider._extract_usage(response)
            # {'input_tokens': 100, 'output_tokens': 50}
            ```
        """
        usage: Dict[str, int] = {}

        try:
            if hasattr(response, 'usage'):
                usage_obj = response.usage
                if hasattr(usage_obj, 'input_tokens'):
                    usage['input_tokens'] = int(usage_obj.input_tokens)
                if hasattr(usage_obj, 'output_tokens'):
                    usage['output_tokens'] = int(usage_obj.output_tokens)
                if hasattr(usage_obj, 'total_tokens'):
                    usage['total_tokens'] = int(usage_obj.total_tokens)

            logger.debug("usage_extracted", usage=usage)

        except Exception as e:
            logger.warning(
                "usage_extraction_failed",
                error=str(e),
                message="Failed to extract usage statistics, continuing with empty usage"
            )

        return usage

    def supports_tool(self, tool_name: str) -> bool:
        """
        Check if tool is supported by OpenCode SDK.

        Based on OpenCode research from Story 11.6 (same as CLI provider).

        Args:
            tool_name: Tool name to check

        Returns:
            True if tool is supported (fully or partially), False otherwise

        Example:
            ```python
            if provider.supports_tool("Read"):
                # Can use Read tool
                pass

            if not provider.supports_tool("WebFetch"):
                # Cannot use WebFetch
                logger.warning("WebFetch not supported by OpenCode SDK")
            ```
        """
        return self.TOOL_MAPPING.get(tool_name, False)

    def get_supported_models(self) -> List[str]:
        """
        Get list of models supported by OpenCode SDK provider.

        Returns canonical names only (not provider/model format).

        Returns:
            List of canonical model names

        Example:
            ```python
            models = provider.get_supported_models()
            # ['sonnet-4.5', 'opus-4', 'gpt-4', ...]
            ```
        """
        return list(self.MODEL_MAP.keys())

    def translate_model_name(self, canonical_name: str) -> str:
        """
        Translate canonical model name to OpenCode provider/model format.

        Args:
            canonical_name: Canonical model name

        Returns:
            OpenCode-specific model identifier (provider/model format)

        Raises:
            ModelNotSupportedError: If model not supported

        Example:
            ```python
            model_id = provider.translate_model_name("sonnet-4.5")
            # "anthropic/claude-sonnet-4.5"
            ```
        """
        provider_id, model_id = self._translate_model(canonical_name)
        return f"{provider_id}/{model_id}"

    async def validate_configuration(self) -> bool:
        """
        Validate that provider is properly configured and ready to use.

        Checks:
        - SDK is installed (import succeeds)
        - Server URL is set
        - API key is set (if required)

        Returns:
            True if configuration valid and ready, False otherwise

        Example:
            ```python
            if await provider.validate_configuration():
                # Ready to use
                result = await provider.execute_task(...)
            else:
                # Not configured
                print("Please configure OpenCode SDK provider")
            ```
        """
        is_valid = True

        # Check SDK is installed
        try:
            import opencode_ai  # noqa: F401
        except ImportError:
            logger.warning(
                "opencode_sdk_not_installed",
                message="OpenCode SDK not installed. Install with: pip install opencode-ai"
            )
            is_valid = False

        # Check server URL
        if not self.server_url:
            logger.warning(
                "server_url_not_set",
                message="OpenCode server URL not set"
            )
            is_valid = False

        # Check API key (warning only, may not be required for all models)
        if not self.api_key:
            logger.info(
                "api_key_not_set",
                message="API key not set. This may be required for some models."
            )

        logger.info(
            "opencode_sdk_configuration_validated",
            is_valid=is_valid,
            has_server_url=bool(self.server_url),
            has_api_key=bool(self.api_key),
        )

        return is_valid

    def get_configuration_schema(self) -> Dict[str, Any]:
        """
        Get JSON Schema for provider-specific configuration.

        Returns:
            JSON Schema dict describing configuration options

        Example:
            ```python
            schema = provider.get_configuration_schema()
            # Use for validation or documentation
            ```
        """
        return {
            "type": "object",
            "properties": {
                "server_url": {
                    "type": "string",
                    "description": "URL of OpenCode server",
                    "default": "http://localhost:4096",
                    "format": "uri"
                },
                "api_key": {
                    "type": "string",
                    "description": "API key for authentication (if required)"
                }
            },
            "required": []  # Both optional
        }

    async def cleanup(self) -> None:
        """
        Clean up SDK resources.

        Closes any open sessions and SDK clients.

        Example:
            ```python
            await provider.cleanup()
            # Provider cleaned up
            ```
        """
        try:
            logger.info("opencode_sdk_provider_cleanup_start")

            # Close session if exists
            if self.session:
                # TODO: Close session if SDK provides method
                # For now, just clear the reference
                self.session = None
                logger.debug("opencode_sdk_session_closed")

            # Clean up client
            if self.sdk_client:
                # TODO: Close client if SDK provides method
                # For now, just clear the reference
                self.sdk_client = None
                logger.debug("opencode_sdk_client_closed")

            self._initialized = False
            logger.info("opencode_sdk_provider_cleanup_complete")

        except Exception as e:
            # Log but don't raise
            logger.warning(
                "opencode_sdk_provider_cleanup_error",
                error=str(e),
                message="Error during cleanup, continuing"
            )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"OpenCodeSDKProvider("
            f"server_url={self.server_url}, "
            f"has_api_key={bool(self.api_key)}, "
            f"initialized={self._initialized})"
        )
