"""Provider configuration validator.

This module provides the ProviderValidator class for validating provider
configurations, checking CLI availability, and providing actionable error
messages.

Epic 35: Interactive Provider Selection at Startup
Story 35.3: ProviderValidator Implementation
"""

from typing import Dict, Any, List
from rich.console import Console
import structlog

from gao_dev.cli.models import ValidationResult

logger = structlog.get_logger()


class ProviderValidator:
    """
    Validates provider configuration.

    Checks CLI availability, API keys, connectivity, and provides
    actionable error messages with fix suggestions.

    Attributes:
        console: Rich Console for output

    Example:
        ```python
        validator = ProviderValidator(console)

        result = await validator.validate_configuration(
            'claude-code',
            {'api_key_env': 'ANTHROPIC_API_KEY'}
        )

        if not result.success:
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        ```
    """

    def __init__(self, console: Console):
        """
        Initialize ProviderValidator with console.

        Args:
            console: Rich Console for output
        """
        self.console = console
        self.logger = logger.bind(component="provider_validator")

    async def validate_configuration(
        self,
        provider_name: str,
        config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate provider configuration.

        Checks:
        - Provider exists in ProviderFactory registry
        - CLI available (if CLI-based provider)
        - API key set (if direct API provider)
        - Model supported by provider
        - Basic connectivity test (optional)

        Args:
            provider_name: Provider identifier
            config: Provider configuration dict

        Returns:
            ValidationResult with success/failure and messages
        """
        raise NotImplementedError("Story 35.3 implementation")

    async def check_cli_available(self, cli_name: str) -> bool:
        """
        Check if CLI tool is in PATH.

        Cross-platform: uses shutil.which() on Unix, where on Windows.

        Args:
            cli_name: Name of CLI (e.g., 'claude', 'opencode', 'ollama')

        Returns:
            True if CLI available, False otherwise
        """
        raise NotImplementedError("Story 35.3 implementation")

    async def check_ollama_models(self) -> List[str]:
        """
        Get list of available Ollama models.

        Runs `ollama list` command and parses output.
        Returns empty list if Ollama unavailable.

        Returns:
            List of model names, or empty list if Ollama unavailable
        """
        raise NotImplementedError("Story 35.3 implementation")

    def suggest_fixes(self, provider_name: str) -> List[str]:
        """
        Provide installation/fix suggestions for provider.

        Args:
            provider_name: Provider that failed validation

        Returns:
            List of suggestion strings

        Example:
            For 'claude-code':
            [
                "Install Claude Code: Follow instructions at https://...",
                "Ensure ANTHROPIC_API_KEY is set: export ANTHROPIC_API_KEY=sk-...",
                "Check PATH: echo $PATH"
            ]
        """
        raise NotImplementedError("Story 35.3 implementation")
