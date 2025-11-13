"""OpenCode SDK-based agent provider implementation.

This provider uses OpenCode's Python SDK for direct API access, eliminating
subprocess hanging issues present in CLI-based provider.

Key Differences from CLI Provider:
- Uses SDK's session.create() and session.chat() instead of CLI subprocess
- Direct API communication (no process management)
- Better error handling and response parsing
- No timeout issues from subprocess hangs
- Automatic server lifecycle management (auto-start, health check, shutdown)

Implementation Status:
- Story 19.2: Core provider implementation - COMPLETE
- Story 19.3: Server lifecycle management - COMPLETE
- Story 19.4: Integration testing (future)

Extracted for: Epic 19 - OpenCode SDK Integration
Story: 19.3 - Server Lifecycle Management
"""

from typing import AsyncGenerator, List, Dict, Optional, Any
import structlog
import os
import atexit
import subprocess
import time
import socket

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from .base import IAgentProvider
from .models import AgentContext
from .exceptions import (
    ProviderExecutionError,
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
        "claude-sonnet-4-5-20250929": ("anthropic", "claude-sonnet-4-5"),
        "claude-opus-4-20250514": ("anthropic", "claude-opus-4"),
        "claude-3-5-sonnet-20241022": ("anthropic", "claude-3.5-sonnet"),
        "claude-3-haiku-20240307": ("anthropic", "claude-3-haiku"),

        # Canonical short names
        "sonnet-4.5": ("anthropic", "claude-sonnet-4-5"),
        "opus-4": ("anthropic", "claude-opus-4"),
        "sonnet-3.5": ("anthropic", "claude-3.5-sonnet"),
        "haiku-3": ("anthropic", "claude-3-haiku"),

        # OpenAI models
        "gpt-4": ("openai", "gpt-4"),
        "gpt-4-turbo": ("openai", "gpt-4-turbo"),
        "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),

        # Ollama models (local)
        # OpenCode uses "ollama" as provider ID and model names as they appear in Ollama
        # BaseURL: http://localhost:11434/v1
        "deepseek-r1:8b": ("ollama", "deepseek-r1:8b"),
        "deepseek-r1": ("ollama", "deepseek-r1:8b"),  # Alias for convenience
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
        server_url: str = "http://localhost:54321",
        port: int = 54321,
        api_key: Optional[str] = None,
        auto_start_server: bool = True,
        startup_timeout: int = 30,
        health_check_timeout: int = 10,
        shutdown_timeout: int = 15,
        **kwargs: Any
    ) -> None:
        """
        Initialize OpenCode SDK provider with server lifecycle management.

        Args:
            server_url: URL of OpenCode server (default: http://localhost:54321)
            port: Port for OpenCode server (default: 54321)
            api_key: API key for authentication (if required)
            auto_start_server: Whether to auto-start server on init (default: True)
            startup_timeout: Max seconds to wait for server startup (default: 30)
            health_check_timeout: Max seconds for health check (default: 10)
            shutdown_timeout: Max seconds for graceful shutdown (default: 15)
            **kwargs: Additional configuration options (for future use)

        Example:
            ```python
            # With default settings (auto-start server)
            provider = OpenCodeSDKProvider()

            # With custom configuration
            provider = OpenCodeSDKProvider(
                port=8080,
                auto_start_server=True,
                startup_timeout=60
            )

            # Disable auto-start (assume server already running)
            provider = OpenCodeSDKProvider(auto_start_server=False)
            ```
        """
        # Validate port
        if not (1024 <= port <= 65535):
            raise ProviderConfigurationError(
                f"Invalid port {port}. Must be between 1024 and 65535.",
                provider_name="opencode-sdk"
            )

        self.server_url = server_url
        self.port = port
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.auto_start_server = auto_start_server
        self.startup_timeout = startup_timeout
        self.health_check_timeout = health_check_timeout
        self.shutdown_timeout = shutdown_timeout

        self.sdk_client: Optional[Any] = None  # Type: Opencode
        self.session: Optional[Any] = None  # Type: Session (deprecated, kept for compatibility)
        self.session_id: Optional[str] = None  # Active session ID
        self.last_project_root: Optional[Path] = None  # Track project root for session invalidation
        self.server_process: Optional[subprocess.Popen] = None
        self._initialized = False

        # Auto-detect OpenCode CLI path for server startup
        self.cli_path = self._detect_opencode_cli()

        # Register cleanup on exit
        atexit.register(self.cleanup_sync)

        logger.info(
            "opencode_sdk_provider_init",
            server_url=server_url,
            port=port,
            has_api_key=bool(self.api_key),
            auto_start=auto_start_server,
            has_cli_path=bool(self.cli_path),
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
        Initialize SDK client and start server if needed.

        This method:
        1. Starts OpenCode server if auto_start_server is True
        2. Verifies server health with retries
        3. Creates SDK client

        Raises:
            ProviderInitializationError: If initialization fails

        Example:
            ```python
            provider = OpenCodeSDKProvider()
            await provider.initialize()
            # Provider ready to use, server started automatically
            ```
        """
        if self._initialized:
            logger.debug("opencode_sdk_provider_already_initialized")
            return

        try:
            logger.info("opencode_sdk_provider_initialize_start")

            # Start server if auto-start enabled
            if self.auto_start_server:
                self._start_server()

            # Verify server health
            self._health_check()

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
            # Cleanup on failure
            self._stop_server()
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
            # IMPORTANT: If project root changes, we must destroy and recreate the session
            # because OpenCode sessions lock the working directory at creation time
            project_root_changed = (
                self.last_project_root is not None and
                self.last_project_root != context.project_root
            )

            if project_root_changed and self.session_id:
                logger.info(
                    "opencode_sdk_session_invalidated",
                    old_project_root=str(self.last_project_root),
                    new_project_root=str(context.project_root),
                    session_id=self.session_id
                )
                # Delete old session since project root changed
                try:
                    self.sdk_client.session.delete(id=self.session_id)
                    logger.debug("opencode_sdk_session_deleted", session_id=self.session_id)
                except Exception as e:
                    logger.warning(
                        "opencode_sdk_session_delete_failed",
                        session_id=self.session_id,
                        error=str(e)
                    )
                # Clear session to force recreation
                self.session = None
                self.session_id = None

            if not self.session:
                logger.debug(
                    "opencode_sdk_create_session",
                    project_root=str(context.project_root)
                )
                # Session creation with working directory set to project root
                # This is CRITICAL - without cwd, tools won't know where to create files!
                session_response = self.sdk_client.session.create(
                    extra_body={"cwd": str(context.project_root)}
                )
                # Store session for reuse and track project root
                self.session = session_response
                self.session_id = getattr(session_response, 'id', session_response.get('id') if isinstance(session_response, dict) else None)
                self.last_project_root = context.project_root  # Track current project root
                session_dir = getattr(session_response, 'directory', None)
                logger.debug(
                    "opencode_sdk_session_created",
                    session_id=self.session_id,
                    directory=session_dir
                )

            # Convert tools list to dictionary format expected by SDK
            # Tools should be Dict[str, bool] where True enables the tool
            # OpenCode expects lowercase tool names: read, write, edit, bash, etc.
            # Map GAO-Dev tool names (capitalized) to OpenCode tool names (lowercase)
            tool_mapping = {
                "Read": "read",
                "Write": "write",
                "Edit": "edit",
                "MultiEdit": "edit",  # OpenCode doesn't have multiedit, use edit
                "Bash": "bash",
                "Grep": "grep",
                "Glob": "glob",
                "TodoWrite": "todowrite",
                "WebFetch": "webfetch",
                "List": "list",
            }
            tools_dict = {
                tool_mapping.get(tool_name, tool_name.lower()): True
                for tool_name in tools
            } if tools else {}

            # Send chat message using session resource
            # NOTE: SDK version mismatch - SDK uses snake_case, server expects camelCase nested structure
            # Using extra_body to override SDK's format with server's expected format
            # Prepend working directory context to task
            # OpenCode sessions don't support changing cwd, so we MUST use absolute paths
            task_with_context = f"""CRITICAL: You MUST use ABSOLUTE file paths for ALL file operations AND follow the correct project structure.

Your project directory is: {context.project_root}

REQUIRED PROJECT STRUCTURE:
- Documentation (PRD, Architecture, Epics, Stories): {context.project_root}\\docs\\
- Source code: {context.project_root}\\src\\
- Tests: {context.project_root}\\tests\\
- Configuration: {context.project_root}\\config\\ (optional)
- Do NOT put documentation files in the root directory!

ABSOLUTE PATH EXAMPLES:
- PRD: {context.project_root}\\docs\\PRD.md
- Architecture: {context.project_root}\\docs\\ARCHITECTURE.md
- Tech Spec: {context.project_root}\\docs\\TECH_SPEC.md
- Source: {context.project_root}\\src\\main.py
- Tests: {context.project_root}\\tests\\test_main.py

WRONG PATHS (DO NOT USE):
- PRD.md (missing docs/ folder)
- {context.project_root}\\PRD.md (should be in docs/)
- ./src/main.py (relative path)

DOCUMENT METADATA (for PRDs, Architecture, etc.):
Start documentation with metadata block:
```
# Document Title

**Version**: 1.0.0
**Date**: YYYY-MM-DD (use current date)
**Status**: Draft
**Author**: [Your Name]

---

## Content starts here...
```

{task}"""

            logger.debug(
                "opencode_sdk_send_chat",
                message_length=len(task_with_context),
                session_id=self.session_id,
                tools_enabled=list(tools_dict.keys()) if tools_dict else None,
                working_directory=str(context.project_root)
            )
            response = self.sdk_client.session.chat(
                id=self.session_id,
                provider_id=provider_id,
                model_id=model_id,
                parts=[{"type": "text", "text": task_with_context}],
                tools=tools_dict if tools_dict else {},  # Enable tools
                # NOTE: Working directory is set at session creation time and cannot be changed per-chat
                # If the project root changes, the session is automatically deleted and recreated (see above)
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
            OpenCode SDK returns response with 'parts' array containing:
            - type: 'text' parts with actual content
            - type: 'step-start', 'step-finish' for metadata

        Example:
            ```python
            content = provider._extract_content(response)
            # "Task completed successfully"
            ```
        """
        content_parts = []

        # Extract from parts array (OpenCode SDK v0.1.0a36+)
        if hasattr(response, 'parts') and isinstance(response.parts, list):
            for part in response.parts:
                # Handle dict format
                if isinstance(part, dict) and part.get('type') == 'text':
                    text = part.get('text', '')
                    if text:
                        content_parts.append(text)
                # Handle object format (pydantic models)
                elif hasattr(part, 'type') and getattr(part, 'type') == 'text':
                    text = getattr(part, 'text', '')
                    if text:
                        content_parts.append(text)

        # Fallback: try legacy attributes
        if not content_parts:
            if hasattr(response, 'content'):
                content_parts.append(response.content)
            elif hasattr(response, 'text'):
                content_parts.append(response.text)
            elif hasattr(response, 'message'):
                content_parts.append(response.message)
            elif isinstance(response, str):
                content_parts.append(response)
            else:
                # Final fallback: convert to string
                logger.warning(
                    "unknown_response_format",
                    response_type=type(response).__name__,
                    message="Unknown SDK response format, converting to string"
                )
                content_parts.append(str(response))

        content = '\n'.join(content_parts)
        logger.debug(
            "content_extracted",
            content_length=len(content),
            num_parts=len(content_parts),
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

        Note:
            OpenCode SDK returns usage in 'step-finish' parts with:
            - tokens: {input, output, reasoning, cache}
            - cost: total cost in dollars

        Example:
            ```python
            usage = provider._extract_usage(response)
            # {'input_tokens': 100, 'output_tokens': 50, 'cost': 0.001}
            ```
        """
        usage: Dict[str, int] = {}

        try:
            # Extract from parts array (OpenCode SDK v0.1.0a36+)
            if hasattr(response, 'parts') and isinstance(response.parts, list):
                for part in response.parts:
                    if isinstance(part, dict) and part.get('type') == 'step-finish':
                        # Extract token usage
                        tokens = part.get('tokens', {})
                        if isinstance(tokens, dict):
                            if 'input' in tokens:
                                usage['input_tokens'] = int(tokens['input'])
                            if 'output' in tokens:
                                usage['output_tokens'] = int(tokens['output'])
                            if 'reasoning' in tokens:
                                usage['reasoning_tokens'] = int(tokens['reasoning'])

                            # Calculate total
                            total = tokens.get('input', 0) + tokens.get('output', 0) + tokens.get('reasoning', 0)
                            if total > 0:
                                usage['total_tokens'] = total

                        # Extract cost
                        if 'cost' in part:
                            usage['cost'] = float(part['cost'])

            # Fallback: try legacy attributes
            if not usage and hasattr(response, 'usage'):
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

    def _start_server(self) -> None:
        """
        Start OpenCode server process with retry logic.

        Raises:
            ProviderInitializationError: If server startup fails after all retries
        """
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "opencode_server_start_attempt",
                    attempt=attempt,
                    max_retries=max_retries,
                    port=self.port,
                )

                # Check if port is available
                if self._is_port_in_use(self.port):
                    logger.warning(
                        "opencode_server_port_in_use",
                        port=self.port,
                    )
                    # Try to connect to existing server
                    if self._is_server_healthy():
                        logger.info("opencode_server_already_running")
                        return
                    else:
                        # Port in use but server not responding - try to clean up
                        logger.warning(
                            "opencode_server_port_stuck",
                            port=self.port,
                            message="Attempting to kill stuck process and restart"
                        )
                        if self._kill_process_on_port(self.port):
                            logger.info("opencode_stuck_process_killed", port=self.port)
                            # Wait a moment for port to be released
                            import time
                            time.sleep(1)
                            # Continue to try starting server
                        else:
                            raise ProviderInitializationError(
                                f"Port {self.port} in use by another process that couldn't be killed. "
                                f"Please manually stop the process or use a different port.",
                                provider_name=self.name
                            )

                # Start server process
                if not self.cli_path:
                    raise ProviderInitializationError(
                        "OpenCode CLI not found. Install: npm install -g opencode-ai@latest",
                        provider_name=self.name
                    )

                self.server_process = subprocess.Popen(
                    [str(self.cli_path), "serve", "--port", str(self.port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                logger.info(
                    "opencode_server_process_started",
                    pid=self.server_process.pid,
                )

                # Wait for server to be ready
                if self._wait_for_server_ready():
                    logger.info("opencode_server_start_success")
                    return

                # Server didn't become ready
                self._stop_server()
                raise ProviderInitializationError(
                    f"Server failed to become ready within {self.startup_timeout}s",
                    provider_name=self.name
                )

            except subprocess.SubprocessError as e:
                logger.warning(
                    "opencode_server_start_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise ProviderInitializationError(
                        f"Failed to start OpenCode server after {max_retries} attempts: {e}",
                        provider_name=self.name,
                        original_error=e
                    ) from e

    def _wait_for_server_ready(self) -> bool:
        """
        Wait for server to be ready with timeout.

        Returns:
            True if server is ready, False if timeout
        """
        start_time = time.time()
        check_interval = 0.5  # seconds

        while time.time() - start_time < self.startup_timeout:
            if self._is_server_healthy():
                return True

            time.sleep(check_interval)

            # Check if process crashed
            if self.server_process and self.server_process.poll() is not None:
                logger.error(
                    "opencode_server_process_crashed",
                    returncode=self.server_process.returncode,
                )
                return False

        return False

    def _health_check(self) -> None:
        """
        Perform health check on OpenCode server with retries.

        Raises:
            ProviderInitializationError: If health check fails after all retries
        """
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    "opencode_health_check_attempt",
                    attempt=attempt,
                )

                if self._is_server_healthy():
                    logger.info("opencode_health_check_success")
                    return

            except Exception as e:
                logger.warning(
                    "opencode_health_check_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise ProviderInitializationError(
                        f"Health check failed after {max_retries} attempts: {e}",
                        provider_name=self.name,
                        original_error=e
                    ) from e

        # If we get here without exception, health check never succeeded
        raise ProviderInitializationError(
            f"Health check failed after {max_retries} attempts",
            provider_name=self.name
        )

    def _is_server_healthy(self) -> bool:
        """
        Check if OpenCode server is healthy using HTTP health check.

        Returns:
            True if server responds to health check
        """
        try:
            if requests is None:
                logger.warning("requests module not available, cannot check server health")
                return False

            # Try health endpoint
            health_url = f"{self.server_url}/health"
            response = requests.get(
                health_url,
                timeout=self.health_check_timeout,
            )
            return response.status_code == 200

        except Exception:
            return False

    def _is_port_in_use(self, port: int) -> bool:
        """
        Check if port is already in use.

        Args:
            port: Port number to check

        Returns:
            True if port is in use
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def _kill_process_on_port(self, port: int) -> bool:
        """
        Intelligently kill process using the specified port.

        Only kills processes that appear to be OpenCode servers.
        Cross-platform: Works on Windows, Linux, and macOS.

        Args:
            port: Port number

        Returns:
            True if process was killed, False if couldn't kill or not safe to kill
        """
        import platform
        import subprocess

        try:
            system = platform.system()

            if system == "Windows":
                # Find PID using netstat
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                for line in result.stdout.split('\n'):
                    if f":{port}" in line and "LISTENING" in line:
                        # Extract PID (last column)
                        parts = line.split()
                        if parts:
                            try:
                                pid = int(parts[-1])
                                logger.info("found_process_on_port", port=port, pid=pid)

                                # Try to get process name to verify it's safe to kill
                                name_result = subprocess.run(
                                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )

                                # Check if it's node/python (OpenCode likely processes)
                                process_name = name_result.stdout.lower()
                                if any(name in process_name for name in ["node", "python", "opencode"]):
                                    logger.info("killing_stuck_process", pid=pid, process=process_name)
                                    subprocess.run(
                                        ["taskkill", "/PID", str(pid), "/F"],
                                        capture_output=True,
                                        timeout=5
                                    )
                                    return True
                                else:
                                    logger.warning(
                                        "process_not_safe_to_kill",
                                        pid=pid,
                                        process=process_name
                                    )
                                    return False
                            except (ValueError, IndexError):
                                continue

            else:  # Linux/macOS
                # Find PID using lsof
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    pid = int(result.stdout.strip())
                    logger.info("found_process_on_port", port=port, pid=pid)

                    # Get process name
                    name_result = subprocess.run(
                        ["ps", "-p", str(pid), "-o", "comm="],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    process_name = name_result.stdout.strip().lower()
                    if any(name in process_name for name in ["node", "python", "opencode"]):
                        logger.info("killing_stuck_process", pid=pid, process=process_name)
                        subprocess.run(["kill", "-9", str(pid)], timeout=5)
                        return True
                    else:
                        logger.warning(
                            "process_not_safe_to_kill",
                            pid=pid,
                            process=process_name
                        )
                        return False

        except Exception as e:
            logger.error("kill_process_failed", error=str(e), port=port)
            return False

        return False

    def _stop_server(self) -> None:
        """Stop OpenCode server gracefully."""
        if not self.server_process:
            return

        try:
            logger.info(
                "opencode_server_stop_start",
                pid=self.server_process.pid,
            )

            # Try graceful shutdown first
            self.server_process.terminate()

            # Wait for graceful shutdown
            try:
                self.server_process.wait(timeout=self.shutdown_timeout)
                logger.info("opencode_server_stopped_gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("opencode_server_force_kill")
                self.server_process.kill()
                self.server_process.wait()

            self.server_process = None

        except Exception as e:
            logger.error(
                "opencode_server_stop_error",
                error=str(e),
            )

    def _detect_opencode_cli(self) -> Optional[Any]:
        """
        Auto-detect OpenCode CLI installation.

        Searches common installation paths for opencode executable.

        Returns:
            Path to OpenCode CLI if found, None otherwise

        Example:
            ```python
            cli_path = provider._detect_opencode_cli()
            if cli_path:
                print(f"Found OpenCode at: {cli_path}")
            else:
                print("OpenCode not found. Please install.")
            ```
        """
        from pathlib import Path

        # Common installation paths
        search_paths = [
            Path.home() / ".opencode" / "bin" / "opencode",
            Path.home() / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/usr/bin/opencode"),
        ]

        # Windows paths
        if os.name == 'nt':
            search_paths.extend([
                Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "bin" / "opencode.exe",
                Path.home() / ".opencode" / "bin" / "opencode.exe",
                Path("C:/Program Files/opencode/opencode.exe"),
            ])

        for path in search_paths:
            if path.exists() and path.is_file():
                logger.info("opencode_cli_detected", path=str(path))
                return path

        logger.warning(
            "opencode_cli_not_detected",
            searched_paths=[str(p) for p in search_paths],
            message="OpenCode CLI not found. Install: npm install -g opencode-ai@latest"
        )
        return None

    async def cleanup(self) -> None:
        """
        Clean up SDK resources and stop server if auto-started.

        Closes any open sessions, SDK clients, and gracefully stops
        the OpenCode server if it was started by this provider.

        Example:
            ```python
            await provider.cleanup()
            # Provider cleaned up, server stopped
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

            # Stop server if we started it
            if self.auto_start_server:
                self._stop_server()

            self._initialized = False
            logger.info("opencode_sdk_provider_cleanup_complete")

        except Exception as e:
            # Log but don't raise
            logger.warning(
                "opencode_sdk_provider_cleanup_error",
                error=str(e),
                message="Error during cleanup, continuing"
            )

    def cleanup_sync(self) -> None:
        """
        Synchronous cleanup method for atexit handler.

        This is called automatically on Python exit to ensure
        server is stopped properly.
        """
        try:
            # Only stop server, don't cleanup other resources
            # (those may already be garbage collected)
            if self.auto_start_server:
                self._stop_server()
        except Exception as e:
            # Silently fail - we're exiting anyway
            logger.warning(
                "opencode_sdk_provider_atexit_cleanup_error",
                error=str(e),
            )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"OpenCodeSDKProvider("
            f"server_url={self.server_url}, "
            f"has_api_key={bool(self.api_key)}, "
            f"initialized={self._initialized})"
        )
