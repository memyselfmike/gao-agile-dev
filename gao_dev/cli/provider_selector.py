"""Provider selection orchestrator for interactive REPL startup.

This module provides the ProviderSelector class that coordinates provider
selection through environment variables, saved preferences, or interactive prompts.

Epic 35: Interactive Provider Selection at Startup
Story 35.5: ProviderSelector Implementation
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from rich.console import Console
import structlog

from gao_dev.cli.exceptions import (
    ProviderSelectionCancelled,
    ProviderValidationFailed,
)
from gao_dev.cli.preference_manager import PreferenceManager
from gao_dev.cli.interactive_prompter import InteractivePrompter
from gao_dev.cli.provider_validator import ProviderValidator

logger = structlog.get_logger()

# Available providers
AVAILABLE_PROVIDERS = ["claude-code", "opencode", "direct-api-anthropic"]
PROVIDER_DESCRIPTIONS = {
    "claude-code": "Claude Code CLI (Anthropic)",
    "opencode": "OpenCode CLI (Multi-provider)",
    "direct-api-anthropic": "Direct Anthropic API",
}

# Default models per provider
DEFAULT_MODELS = {
    "claude-code": "sonnet-4.5",
    "opencode": "deepseek-r1",
    "direct-api-anthropic": "claude-3-5-sonnet-20241022",
}

# Available models per provider
AVAILABLE_MODELS = {
    "claude-code": ["sonnet-4.5", "opus-4", "haiku-3.5"],
    "opencode": ["deepseek-r1", "llama2", "codellama"],
    "direct-api-anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ],
}


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
        provider_validator: Optional["ProviderValidator"] = None,
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

        # Create real instances if not provided (dependency injection)
        self._preference_manager = preference_manager or PreferenceManager(
            project_root
        )
        self._interactive_prompter = interactive_prompter or InteractivePrompter(
            console
        )
        self._provider_validator = provider_validator or ProviderValidator(console)

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
        try:
            return self._select_provider_sync()
        except KeyboardInterrupt:
            raise ProviderSelectionCancelled("User cancelled provider selection")

    def _select_provider_sync(self) -> Dict[str, Any]:
        """
        Synchronous implementation of provider selection.

        Skips async validation to avoid event loop conflicts with prompt_toolkit.

        Returns:
            Provider config dict
        """
        self.logger.info("provider_selection_started")

        # Priority 1: Environment variable
        env_config = self.use_environment_variable()
        if env_config:
            self.logger.info(
                "using_env_var",
                provider=env_config["provider"],
            )
            # Skip validation in sync mode to avoid event loop issues
            return env_config

        # Priority 2: Saved preferences
        if self._preference_manager.has_preferences():
            saved_prefs = self._preference_manager.load_preferences()
            if saved_prefs:
                choice = self._interactive_prompter.prompt_use_saved(saved_prefs)

                if choice == "y":
                    # User accepted saved preferences
                    self.logger.info("using_saved_preferences")
                    provider_data = saved_prefs["provider"]
                    config = self._build_config_from_saved(provider_data)
                    return config
                elif choice == "c":
                    # User wants to change specific settings
                    self.logger.info("user_requested_changes")
                    # Fall through to interactive prompts
                else:
                    # User declined saved preferences
                    self.logger.info("user_declined_saved_preferences")
                    # Fall through to interactive prompts

        # Priority 3: Interactive prompts
        self.logger.info("prompting_for_provider_selection")
        config = self._prompt_for_provider_sync()

        # Ask to save preferences
        self._save_if_requested_sync(config)

        self.logger.info("provider_selection_completed", provider=config["provider"])
        return config

    async def _select_provider_async(self) -> Dict[str, Any]:
        """
        Async implementation of provider selection.

        Returns:
            Provider config dict

        Raises:
            ProviderSelectionCancelled: User cancelled selection
            ProviderValidationFailed: Validation failed after max attempts
        """
        self.logger.info("provider_selection_started")

        # Priority 1: Environment variable
        env_config = self.use_environment_variable()
        if env_config:
            self.logger.info(
                "using_env_var",
                provider=env_config["provider"],
            )
            # Validate env var config
            result = await self._provider_validator.validate_configuration(
                env_config["provider"], env_config.get("config", {})
            )
            if result.success:
                self.logger.info("env_var_validation_passed")
                return env_config
            else:
                # Env var invalid, log warning and fall through to saved/interactive
                self.logger.warning(
                    "env_var_validation_failed",
                    provider=env_config["provider"],
                    warnings=result.warnings,
                )
                self._interactive_prompter.show_error(
                    f"Environment variable provider '{env_config['provider']}' "
                    f"validation failed",
                    result.suggestions,
                )

        # Priority 2: Saved preferences
        if self._preference_manager.has_preferences():
            saved_prefs = self._preference_manager.load_preferences()
            if saved_prefs:
                choice = self._interactive_prompter.prompt_use_saved(saved_prefs)

                if choice == "y":
                    # User accepted saved preferences
                    self.logger.info("using_saved_preferences")
                    provider_data = saved_prefs["provider"]
                    config = self._build_config_from_saved(provider_data)

                    # Validate saved config
                    config = await self._validate_and_retry(config, max_attempts=3)
                    return config
                elif choice == "c":
                    # User wants to change specific settings
                    self.logger.info("user_requested_changes")
                    # Fall through to interactive prompts
                else:
                    # User declined saved preferences
                    self.logger.info("user_declined_saved_preferences")
                    # Fall through to interactive prompts

        # Priority 3: Interactive prompts
        self.logger.info("prompting_for_provider_selection")
        config = await self._prompt_for_provider()

        # Validate with retry
        config = await self._validate_and_retry(config, max_attempts=3)

        # Ask to save preferences
        await self._save_if_requested(config)

        self.logger.info("provider_selection_completed", provider=config["provider"])
        return config

    def _build_config_from_saved(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build provider config dict from saved preferences.

        Args:
            provider_data: Provider section from saved preferences

        Returns:
            Provider config dict
        """
        return {
            "provider": provider_data["name"],
            "model": provider_data["model"],
            "config": provider_data.get("config", {}),
        }

    def _prompt_for_provider_sync(self) -> Dict[str, Any]:
        """
        Prompt user for provider selection (synchronous).

        Returns:
            Provider config dict

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C
        """
        try:
            # Prompt for provider
            provider = self._interactive_prompter.prompt_provider(
                AVAILABLE_PROVIDERS, PROVIDER_DESCRIPTIONS
            )

            self.logger.debug("provider_selected", provider=provider)

            # Special handling for OpenCode
            config: Dict[str, Any] = {}
            if provider in ("opencode", "opencode-cli"):
                opencode_config = self._interactive_prompter.prompt_opencode_config()
                config.update(opencode_config)

            # Prompt for model
            available_models = AVAILABLE_MODELS.get(provider, [DEFAULT_MODELS[provider]])
            model = self._interactive_prompter.prompt_model(available_models)

            self.logger.debug("model_selected", model=model)

            return {"provider": provider, "model": model, "config": config}

        except KeyboardInterrupt:
            self.logger.info("user_cancelled_prompt")
            raise

    async def _prompt_for_provider(self) -> Dict[str, Any]:
        """
        Prompt user for provider selection.

        Returns:
            Provider config dict

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C
        """
        try:
            # Prompt for provider
            provider = self._interactive_prompter.prompt_provider(
                AVAILABLE_PROVIDERS, PROVIDER_DESCRIPTIONS
            )

            self.logger.debug("provider_selected", provider=provider)

            # Special handling for OpenCode
            config: Dict[str, Any] = {}
            if provider in ("opencode", "opencode-cli"):
                opencode_config = self._interactive_prompter.prompt_opencode_config()
                config.update(opencode_config)

            # Prompt for model
            available_models = AVAILABLE_MODELS.get(provider, [DEFAULT_MODELS[provider]])
            model = self._interactive_prompter.prompt_model(available_models)

            self.logger.debug("model_selected", model=model)

            return {"provider": provider, "model": model, "config": config}

        except KeyboardInterrupt:
            self.logger.info("user_cancelled_prompt")
            raise

    async def _validate_and_retry(
        self, config: Dict[str, Any], max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Validate provider config with retry logic.

        Args:
            config: Provider config to validate
            max_attempts: Maximum validation attempts

        Returns:
            Validated provider config

        Raises:
            ProviderValidationFailed: After max attempts exceeded
            ProviderSelectionCancelled: User cancelled after failure
        """
        for attempt in range(1, max_attempts + 1):
            self.logger.debug(
                "validating_provider",
                provider=config["provider"],
                attempt=attempt,
                max_attempts=max_attempts,
            )

            result = await self._provider_validator.validate_configuration(
                config["provider"], config.get("config", {})
            )

            if result.success:
                self.logger.info(
                    "validation_passed",
                    provider=config["provider"],
                    attempt=attempt,
                    duration_ms=result.validation_time_ms,
                )
                return config

            # Validation failed
            self.logger.warning(
                "validation_failed",
                provider=config["provider"],
                attempt=attempt,
                warnings=result.warnings,
            )

            # Show error to user
            error_msg = f"Provider validation failed: {', '.join(result.warnings)}"
            self._interactive_prompter.show_error(error_msg, result.suggestions)

            if attempt < max_attempts:
                # Prompt for different provider
                try:
                    self.logger.debug("prompting_for_retry")
                    config = await self._prompt_for_provider()
                except KeyboardInterrupt:
                    raise ProviderSelectionCancelled(
                        "User cancelled after validation failure"
                    )
            else:
                # Max attempts exceeded
                raise ProviderValidationFailed(
                    f"Provider validation failed after {max_attempts} max attempts"
                )

        # Should never reach here
        raise ProviderValidationFailed("Unexpected validation error")

    def _save_if_requested_sync(self, config: Dict[str, Any]) -> None:
        """
        Ask user if they want to save preferences (synchronous).

        Args:
            config: Provider config to save
        """
        try:
            if self._interactive_prompter.prompt_save_preferences():
                self.logger.info("saving_preferences")

                # Build preferences dict
                preferences = {
                    "version": "1.0.0",
                    "provider": {
                        "name": config["provider"],
                        "model": config["model"],
                        "config": config.get("config", {}),
                    },
                    "metadata": {
                        "last_updated": datetime.now().isoformat() + "Z",
                        "cli_version": "1.0.0",
                    },
                }

                self._preference_manager.save_preferences(preferences)
                self.logger.info("preferences_saved")
            else:
                self.logger.info("user_declined_save_preferences")

        except Exception as e:
            self.logger.error("save_preferences_error", error=str(e))
            self.console.print(
                f"[yellow]Warning: Could not save preferences: {e}[/yellow]"
            )

    async def _save_if_requested(self, config: Dict[str, Any]) -> None:
        """
        Ask user if they want to save preferences.

        Args:
            config: Provider config to save
        """
        try:
            if self._interactive_prompter.prompt_save_preferences():
                self.logger.info("saving_preferences")

                # Build preferences dict
                preferences = {
                    "version": "1.0.0",
                    "provider": {
                        "name": config["provider"],
                        "model": config["model"],
                        "config": config.get("config", {}),
                    },
                    "metadata": {
                        "last_updated": datetime.now().isoformat() + "Z",
                        "cli_version": "1.0.0",
                    },
                }

                self._preference_manager.save_preferences(preferences)
                self.logger.info("preferences_saved")
            else:
                self.logger.info("user_declined_save_preferences")

        except Exception as e:
            # Don't fail if save fails - just log warning
            self.logger.warning("failed_to_save_preferences", error=str(e))

    def has_saved_preferences(self) -> bool:
        """
        Check if saved preferences exist and are valid.

        Returns:
            True if valid saved preferences exist, False otherwise
        """
        return self._preference_manager.has_preferences()

    def use_environment_variable(self) -> Optional[Dict[str, Any]]:
        """
        Get provider config from AGENT_PROVIDER environment variable.

        Checks for AGENT_PROVIDER env var and converts to provider config.
        Supports formats:
        - "provider" (e.g., "claude-code")
        - "provider:model" (e.g., "opencode:deepseek-r1")

        Returns:
            Provider config dict if env var set, None otherwise

        Example:
            ```bash
            export AGENT_PROVIDER=claude-code
            ```
            Returns: {'provider': 'claude-code', 'model': 'sonnet-4.5', ...}
        """
        env_var = os.getenv("AGENT_PROVIDER", "").strip()

        if not env_var:
            self.logger.debug("env_var_not_set")
            return None

        self.logger.debug("env_var_found", value=env_var)

        # Parse format: "provider" or "provider:model"
        if ":" in env_var:
            parts = env_var.split(":", 1)
            provider = parts[0].strip()
            model = parts[1].strip()
        else:
            provider = env_var
            model = DEFAULT_MODELS.get(provider, "sonnet-4.5")

        # Build config
        config: Dict[str, Any] = {}
        if provider in ("opencode", "opencode-cli"):
            # Default to local Ollama for opencode
            config = {"ai_provider": "ollama", "use_local": True}

        return {"provider": provider, "model": model, "config": config}
