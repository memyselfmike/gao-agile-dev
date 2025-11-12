"""Provider selection orchestrator for interactive REPL startup.

This module provides the ProviderSelector class that coordinates provider
selection through environment variables, saved preferences, or interactive prompts.

Epic 35: Interactive Provider Selection at Startup
Story 35.5: ProviderSelector Implementation
"""

from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console
import structlog

logger = structlog.get_logger()


class ProviderSelector:
    """
    Orchestrates provider selection for REPL startup.

    Coordinates PreferenceManager, InteractivePrompter, and ProviderValidator
    to determine which provider configuration to use based on priority:
    1. Environment variable (AGENT_PROVIDER)
    2. Saved preferences (if exist and user confirms)
    3. Interactive prompts
    4. Hardcoded defaults (last resort)

    Attributes:
        project_root: Project root directory
        console: Rich Console for formatted output
        preference_manager: Manages preference persistence
        interactive_prompter: Handles user interaction
        provider_validator: Validates provider configurations

    Example:
        ```python
        selector = ProviderSelector(project_root, console)
        try:
            provider_config = selector.select_provider()
            # Use provider_config to create ProcessExecutor
        except ProviderSelectionCancelled:
            print("User cancelled selection")
            sys.exit(0)
        ```
    """

    def __init__(
        self,
        project_root: Path,
        console: Console,
        preference_manager: Optional["PreferenceManager"] = None,
        interactive_prompter: Optional["InteractivePrompter"] = None,
        provider_validator: Optional["ProviderValidator"] = None
    ):
        """
        Initialize ProviderSelector with dependencies.

        Args:
            project_root: Project root directory
            console: Rich Console for formatted output
            preference_manager: Optional PreferenceManager (created if None)
            interactive_prompter: Optional InteractivePrompter (created if None)
            provider_validator: Optional ProviderValidator (created if None)
        """
        self.project_root = project_root
        self.console = console
        self.logger = logger.bind(component="provider_selector")

        # Lazy initialization of dependencies (for testing)
        self._preference_manager = preference_manager
        self._interactive_prompter = interactive_prompter
        self._provider_validator = provider_validator

    def select_provider(self) -> Dict[str, Any]:
        """
        Select provider using priority: env var > saved prefs > interactive.

        Priority order:
        1. AGENT_PROVIDER environment variable (bypass all prompts)
        2. Saved preferences (if exist and user confirms)
        3. Interactive prompts (first-time setup)
        4. Hardcoded defaults (last resort)

        Returns:
            Dict with keys: provider, model, config

        Raises:
            ProviderSelectionCancelled: User cancelled selection (Ctrl+C)
            ProviderValidationFailed: Selected provider failed validation

        Example:
            ```python
            config = selector.select_provider()
            # config = {
            #     'provider': 'opencode',
            #     'model': 'deepseek-r1',
            #     'config': {'ai_provider': 'ollama', 'use_local': True}
            # }
            ```
        """
        raise NotImplementedError("Story 35.5 implementation")

    def has_saved_preferences(self) -> bool:
        """
        Check if saved preferences exist and are valid.

        Returns:
            True if valid saved preferences exist, False otherwise
        """
        raise NotImplementedError("Story 35.5 implementation")

    def use_environment_variable(self) -> Optional[Dict[str, Any]]:
        """
        Get provider config from AGENT_PROVIDER environment variable.

        Checks for AGENT_PROVIDER env var and converts to provider config.

        Returns:
            Provider config dict if env var set, None otherwise

        Example:
            ```bash
            export AGENT_PROVIDER=claude-code
            ```
            Returns: {'provider': 'claude-code', 'model': 'sonnet-4.5', ...}
        """
        raise NotImplementedError("Story 35.5 implementation")
