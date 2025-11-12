"""Interactive prompts for provider selection using Rich and prompt_toolkit.

This module provides the InteractivePrompter class for beautiful formatted
prompts with tables and clear user interaction.

Epic 35: Interactive Provider Selection at Startup
Story 35.4: InteractivePrompter Implementation

CRAAP Resolution: Lazy import pattern for CI/CD compatibility.
All prompt_toolkit and rich.prompt imports happen inside methods, not at module level.
"""

from typing import Any, Dict, List, Optional
from rich.console import Console
import structlog

logger = structlog.get_logger()


class InteractivePrompter:
    """
    Handles interactive prompts for provider selection.

    Uses Rich for formatted output and prompt_toolkit for input.
    Falls back to simple input() if Rich/prompt_toolkit unavailable (CI/CD).

    SECURITY NOTE: All user input is validated before use.

    Attributes:
        console: Rich Console for formatted output

    Example:
        ```python
        prompter = InteractivePrompter(console)

        provider = prompter.prompt_provider(
            available_providers=['claude-code', 'opencode'],
            descriptions={'claude-code': 'Claude Code CLI', ...}
        )
        # User sees formatted table, selects provider
        ```
    """

    def __init__(self, console: Console):
        """
        Initialize InteractivePrompter with Rich console.

        Args:
            console: Rich Console for formatted output
        """
        self.console = console
        self.logger = logger.bind(component="interactive_prompter")

    def prompt_provider(
        self,
        available_providers: List[str],
        descriptions: Dict[str, str]
    ) -> str:
        """
        Prompt user to select a provider.

        Shows formatted table of providers with descriptions, then prompts
        for selection. Falls back to simple text if Rich unavailable.

        CRAAP Resolution: Uses lazy imports for CI/CD compatibility.

        Args:
            available_providers: List of provider names
            descriptions: Provider name -> description mapping

        Returns:
            Selected provider name

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C

        Example:
            ```python
            provider = prompter.prompt_provider(
                ['claude-code', 'opencode', 'direct-api-anthropic'],
                {
                    'claude-code': 'Claude Code CLI (Anthropic)',
                    'opencode': 'OpenCode CLI (Multi-provider)',
                    'direct-api-anthropic': 'Direct Anthropic API'
                }
            )
            # Returns: 'opencode'
            ```
        """
        raise NotImplementedError("Story 35.4 implementation")

    def prompt_opencode_config(self) -> Dict[str, Any]:
        """
        Prompt for OpenCode-specific configuration.

        Asks:
        - Local model (Ollama) vs cloud?
        - If cloud: which provider (anthropic/openai/google)?

        Returns:
            Dict with OpenCode-specific config

        Example:
            ```python
            config = prompter.prompt_opencode_config()
            # Returns: {'ai_provider': 'ollama', 'use_local': True}
            # or: {'ai_provider': 'anthropic', 'use_local': False}
            ```
        """
        raise NotImplementedError("Story 35.4 implementation")

    def prompt_model(
        self,
        available_models: List[str],
        descriptions: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Prompt user to select a model.

        Shows formatted table of models with optional descriptions.

        Args:
            available_models: List of model names
            descriptions: Optional model name -> description mapping

        Returns:
            Selected model name

        Example:
            ```python
            model = prompter.prompt_model(
                ['deepseek-r1', 'llama2', 'codellama'],
                {
                    'deepseek-r1': '7B (recommended for coding)',
                    'llama2': '7B',
                    'codellama': '13B'
                }
            )
            # Returns: 'deepseek-r1'
            ```
        """
        raise NotImplementedError("Story 35.4 implementation")

    def prompt_save_preferences(self) -> bool:
        """
        Ask if user wants to save preferences.

        Returns:
            True if user wants to save, False otherwise
        """
        raise NotImplementedError("Story 35.4 implementation")

    def prompt_use_saved(self, saved_config: Dict[str, Any]) -> str:
        """
        Ask if user wants to use saved configuration.

        Args:
            saved_config: Previously saved configuration

        Returns:
            'y' (yes), 'n' (no), or 'c' (change specific settings)
        """
        raise NotImplementedError("Story 35.4 implementation")

    def show_error(self, message: str, suggestions: Optional[List[str]] = None):
        """
        Display error message with optional suggestions.

        Args:
            message: Error message
            suggestions: Optional list of suggestion strings
        """
        raise NotImplementedError("Story 35.4 implementation")

    def show_success(self, message: str):
        """
        Display success message.

        Args:
            message: Success message
        """
        raise NotImplementedError("Story 35.4 implementation")
