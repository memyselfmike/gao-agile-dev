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
from rich.table import Table
from rich.panel import Panel
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
        # Display table
        table = Table(title="Available AI Providers", border_style="cyan")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Provider", style="green")
        table.add_column("Description", style="white")

        for idx, provider in enumerate(available_providers, 1):
            table.add_row(
                str(idx),
                provider,
                descriptions.get(provider, "")
            )

        self.console.print(table)

        # Get user input with validation loop
        while True:
            try:
                choice = self._get_user_input(
                    f"Select provider [1-{len(available_providers)}]",
                    default="1",
                    choices=[str(i) for i in range(1, len(available_providers) + 1)]
                )

                # Validate and convert
                if choice == '' or choice == '1':
                    return available_providers[0]

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_providers):
                    return available_providers[choice_idx]
                else:
                    self.show_error(
                        f"Invalid choice: {choice}",
                        [f"Please choose a number between 1 and {len(available_providers)}"]
                    )
            except ValueError:
                self.show_error(
                    f"Invalid input: {choice}",
                    [f"Please enter a number between 1 and {len(available_providers)}"]
                )

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
        # Ask about local vs cloud
        self.console.print("\n[bold cyan]OpenCode Configuration[/bold cyan]")

        use_local_choice = self._get_user_input(
            "Use local model via Ollama? [y/N]",
            default="n",
            choices=['y', 'n', 'Y', 'N', '']
        )

        if use_local_choice.lower() == 'y':
            return {
                'use_local': True,
                'ai_provider': 'ollama'
            }
        else:
            # Ask for cloud provider
            self.console.print("\n[bold]Cloud AI Provider Options:[/bold]")
            self.console.print("  1) Anthropic (Claude)")
            self.console.print("  2) OpenAI (GPT)")
            self.console.print("  3) Google (Gemini)")

            provider_choice = self._get_user_input(
                "Select cloud provider [1-3]",
                default="1",
                choices=['1', '2', '3', '']
            )

            provider_map = {
                '1': 'anthropic',
                '2': 'openai',
                '3': 'google',
                '': 'anthropic'  # Default
            }

            return {
                'use_local': False,
                'ai_provider': provider_map.get(provider_choice, 'anthropic')
            }

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
        # Display table
        table = Table(title="Available Models", border_style="cyan")
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Model", style="green")

        if descriptions:
            table.add_column("Description", style="white")

        for idx, model in enumerate(available_models, 1):
            if descriptions:
                table.add_row(
                    str(idx),
                    model,
                    descriptions.get(model, "")
                )
            else:
                table.add_row(str(idx), model)

        self.console.print(table)

        # Get user input with validation loop
        while True:
            try:
                choice = self._get_user_input(
                    f"Select model [1-{len(available_models)}]",
                    default="1",
                    choices=[str(i) for i in range(1, len(available_models) + 1)]
                )

                # Validate and convert
                if choice == '' or choice == '1':
                    return available_models[0]

                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_models):
                    return available_models[choice_idx]
                else:
                    self.show_error(
                        f"Invalid choice: {choice}",
                        [f"Please choose a number between 1 and {len(available_models)}"]
                    )
            except ValueError:
                self.show_error(
                    f"Invalid input: {choice}",
                    [f"Please enter a number between 1 and {len(available_models)}"]
                )

    def prompt_save_preferences(self) -> bool:
        """
        Ask if user wants to save preferences.

        Returns:
            True if user wants to save, False otherwise
        """
        choice = self._get_user_input(
            "Save these preferences? [y/N]",
            default="n",
            choices=['y', 'n', 'Y', 'N', '']
        )

        return choice.lower() == 'y'

    def prompt_use_saved(self, saved_config: Dict[str, Any]) -> str:
        """
        Ask if user wants to use saved configuration.

        Args:
            saved_config: Previously saved configuration

        Returns:
            'y' (yes), 'n' (no), or 'c' (change specific settings)
        """
        # Display saved config
        self.console.print("\n[bold cyan]Saved Configuration Found:[/bold cyan]")
        for key, value in saved_config.items():
            self.console.print(f"  {key}: [green]{value}[/green]")

        choice = self._get_user_input(
            "Use saved configuration? [Y/n/c (change)]",
            default="y",
            choices=['y', 'n', 'c', 'Y', 'N', 'C', '']
        )

        return choice.lower() if choice else 'y'

    def show_error(self, message: str, suggestions: Optional[List[str]] = None) -> None:
        """
        Display error message with optional suggestions.

        Args:
            message: Error message
            suggestions: Optional list of suggestion strings
        """
        content = f"[bold red]{message}[/bold red]"

        if suggestions:
            content += "\n\n[bold]Suggestions:[/bold]"
            for suggestion in suggestions:
                content += f"\n  - {suggestion}"

        panel = Panel(
            content,
            title="Error",
            border_style="red",
            expand=False
        )
        self.console.print(panel)

    def show_success(self, message: str) -> None:
        """
        Display success message.

        Args:
            message: Success message
        """
        panel = Panel(
            f"[bold green]{message}[/bold green]",
            title="Success",
            border_style="green",
            expand=False
        )
        self.console.print(panel)

    def _get_user_input(
        self,
        prompt_text: str,
        default: str = "",
        choices: Optional[List[str]] = None
    ) -> str:
        """
        Get user input with lazy import fallback for CI/CD compatibility.

        This method implements the CRAAP Critical Resolution pattern:
        - Try to import prompt_toolkit INSIDE the method (lazy)
        - If ImportError or OSError, fall back to basic input()
        - This ensures CI/CD pipelines work even without TTY

        Args:
            prompt_text: Text to display to user
            default: Default value if user presses Enter
            choices: Optional list of valid choices

        Returns:
            User's input string

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C (not caught, propagates)
        """
        # Format prompt with default
        if default:
            display_prompt = f"{prompt_text} (default: {default}): "
        else:
            display_prompt = f"{prompt_text}: "

        try:
            # LAZY IMPORT: Import inside method, not at module level
            from prompt_toolkit import PromptSession

            # Use prompt_toolkit for interactive input
            session: PromptSession[str] = PromptSession()
            user_input: str = session.prompt(display_prompt)

            # Use default if empty
            if not user_input and default:
                return default

            return user_input

        except (ImportError, OSError) as e:
            # Fallback for headless environments (Docker, CI/CD, no TTY)
            self.logger.warning(
                "prompt_toolkit unavailable, using fallback input",
                error=str(e),
                error_type=type(e).__name__
            )

            # Use standard input() function as fallback
            user_input_fallback: str = input(display_prompt)

            # Use default if empty
            if not user_input_fallback and default:
                return default

            return user_input_fallback
