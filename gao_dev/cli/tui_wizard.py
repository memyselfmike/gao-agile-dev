"""Terminal-based onboarding wizard using Rich.

This module provides the TUIWizard class for Docker, SSH, and WSL environments.
It guides users through a 4-step onboarding process with Rich-formatted output.

Epic 41: Streamlined Onboarding
Story 41.1: TUI Wizard Implementation
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from gao_dev.cli.wizard_config import (
    WizardConfig,
    ProjectConfig,
    GitConfig,
    ProviderInfo,
    PROVIDERS,
    PROVIDER_MAP,
    DEFAULT_MODELS,
    AVAILABLE_MODELS,
)
from gao_dev.cli.provider_validator import ProviderValidator

logger = structlog.get_logger()


class TUIWizard:
    """Terminal-based onboarding wizard using Rich.

    Guides users through a 4-step onboarding process:
    1. Project Configuration
    2. Git Configuration
    3. Provider Selection
    4. Credentials

    Uses Rich for formatted terminal output with panels, tables, and prompts.
    Supports back navigation, keyboard interrupt handling, and validation spinners.

    Attributes:
        project_root: Project root directory
        console: Rich Console for formatted output
        config: Collected wizard configuration

    Example:
        ```python
        wizard = TUIWizard(project_root, console)
        config = await wizard.run()
        # config contains all collected data
        ```
    """

    def __init__(self, project_root: Path, console: Optional[Console] = None):
        """Initialize TUIWizard with project root.

        Args:
            project_root: Project root directory
            console: Optional Rich Console (created if None)
        """
        self.project_root = project_root
        self.console = console or Console()
        self.config = WizardConfig()
        self.logger = logger.bind(component="tui_wizard")
        self._cancelled = False
        self._validator: Optional[ProviderValidator] = None
        self._current_step = 1
        self._total_steps = 4

    async def run(self) -> WizardConfig:
        """Run the TUI wizard and collect configuration.

        Main entry point for the wizard. Guides user through all 4 steps
        with support for back navigation and graceful cancellation.

        Returns:
            WizardConfig with all collected data

        Raises:
            KeyboardInterrupt: User cancelled with Ctrl+C
        """
        self.logger.info("wizard_started")

        try:
            # Show welcome panel
            self._show_welcome()

            # Run through steps with back navigation support
            steps = [
                self._step_project,
                self._step_git,
                self._step_provider,
                self._step_credentials,
            ]

            step_idx = 0
            while step_idx < len(steps):
                self._current_step = step_idx + 1
                result = await steps[step_idx]()

                if result == "back":
                    if step_idx > 0:
                        step_idx -= 1
                        self.console.print("[dim]Going back...[/dim]\n")
                    else:
                        self.console.print(
                            "[yellow]Already at first step[/yellow]\n"
                        )
                elif result == "cancel":
                    raise KeyboardInterrupt("User cancelled wizard")
                else:
                    step_idx += 1

            # Show completion panel
            self._show_completion()

            self.logger.info("wizard_completed")
            return self.config

        except KeyboardInterrupt:
            self.logger.info("wizard_cancelled")
            if self._confirm_cancel():
                raise
            # User chose not to cancel, restart from current step
            return await self.run()

    def _show_welcome(self) -> None:
        """Display welcome panel with GAO-Dev branding and setup context."""
        welcome_text = """[bold cyan]GAO-Dev[/bold cyan] - Generative Autonomous Organisation

[dim]This wizard will help you set up your development environment.[/dim]

[bold]Setup Steps:[/bold]
  1. Project Configuration
  2. Git Configuration
  3. AI Provider Selection
  4. Credentials Setup

[dim]Press Ctrl+C at any time to cancel.[/dim]
[dim]Type 'back' to return to previous step.[/dim]"""

        panel = Panel(
            welcome_text,
            title="[bold green]Welcome to GAO-Dev Setup[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            expand=False,
        )
        self.console.print(panel)
        self.console.print()

    def _show_completion(self) -> None:
        """Display success panel with configuration summary."""
        # Build summary text
        summary_lines = [
            "[bold]Configuration Summary:[/bold]",
            "",
            f"[cyan]Project:[/cyan] {self.config.project.name}",
            f"  Type: {self.config.project.project_type}",
            f"  Description: {self.config.project.description or '(none)'}",
            "",
            f"[cyan]Git:[/cyan]",
            f"  User: {self.config.git.user_name}",
            f"  Email: {self.config.git.user_email}",
            f"  Initialize: {'Yes' if self.config.git.init_git else 'No'}",
            "",
            f"[cyan]Provider:[/cyan] {self.config.provider_name}",
            f"  Model: {self.config.model}",
        ]

        if self.config.api_key:
            # Show masked API key
            masked = self.config.api_key[:8] + "..." + self.config.api_key[-4:]
            summary_lines.append(f"  API Key: {masked}")

        summary_text = "\n".join(summary_lines)

        panel = Panel(
            summary_text,
            title="[bold green]Setup Complete![/bold green]",
            border_style="green",
            box=box.ROUNDED,
            expand=False,
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()
        self.console.print(
            "[bold]Run [cyan]gao-dev start[/cyan] to begin working![/bold]"
        )

    def _show_progress(self, step_name: str) -> None:
        """Display progress indicator for current step.

        Args:
            step_name: Name of current step
        """
        self.console.print(
            f"[bold cyan]Step {self._current_step} of {self._total_steps}: "
            f"{step_name}[/bold cyan]\n"
        )

    def _confirm_cancel(self) -> bool:
        """Confirm wizard cancellation with user.

        Returns:
            True if user confirms cancellation
        """
        self.console.print()
        return Confirm.ask(
            "[yellow]Are you sure you want to cancel setup?[/yellow]",
            default=False,
            console=self.console,
        )

    async def _step_project(self) -> str:
        """Step 1: Project Configuration.

        Collects project name, type, and description.

        Returns:
            'next', 'back', or 'cancel'
        """
        self._show_progress("Project Configuration")

        # Defaults
        default_name = self.project_root.name
        default_type = self._detect_project_type()

        # Project name
        name = Prompt.ask(
            "Project name",
            default=default_name,
            console=self.console,
        )
        if name.lower() == "back":
            return "back"

        # Project type
        type_prompt = f"Project type (detected: {default_type})"
        project_type = Prompt.ask(
            type_prompt,
            default=default_type,
            console=self.console,
        )
        if project_type.lower() == "back":
            return "back"

        # Description
        description = Prompt.ask(
            "Project description",
            default="",
            console=self.console,
        )
        if description.lower() == "back":
            return "back"

        # Store config
        self.config.project = ProjectConfig(
            name=name,
            project_type=project_type,
            description=description,
        )

        self.console.print()
        return "next"

    async def _step_git(self) -> str:
        """Step 2: Git Configuration.

        Collects git user.name, user.email, and init preference.

        Returns:
            'next', 'back', or 'cancel'
        """
        self._show_progress("Git Configuration")

        # Get defaults from global git config
        default_name = self._get_git_config("user.name") or ""
        default_email = self._get_git_config("user.email") or ""

        # Git user name
        user_name = Prompt.ask(
            "Git user name",
            default=default_name,
            console=self.console,
        )
        if user_name.lower() == "back":
            return "back"

        # Git email
        user_email = Prompt.ask(
            "Git user email",
            default=default_email,
            console=self.console,
        )
        if user_email.lower() == "back":
            return "back"

        # Init git repo
        # Check if .git already exists
        git_exists = (self.project_root / ".git").exists()
        if git_exists:
            init_git = False
            self.console.print(
                "[dim]Git repository already initialized[/dim]"
            )
        else:
            init_git = Confirm.ask(
                "Initialize git repository?",
                default=True,
                console=self.console,
            )

        # Store config
        self.config.git = GitConfig(
            user_name=user_name,
            user_email=user_email,
            init_git=init_git,
        )

        self.console.print()
        return "next"

    async def _step_provider(self) -> str:
        """Step 3: Provider Selection.

        Displays table of providers and collects selection.

        Returns:
            'next', 'back', or 'cancel'
        """
        self._show_progress("AI Provider Selection")

        # Display provider table
        table = Table(
            title="Available AI Providers",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Provider", style="green")
        table.add_column("Description", style="white")
        table.add_column("API Key", style="yellow", justify="center")

        for idx, provider in enumerate(PROVIDERS, 1):
            api_key_text = "Yes" if provider.requires_api_key else "No"
            table.add_row(
                str(idx),
                provider.name,
                provider.description,
                api_key_text,
            )

        self.console.print(table)
        self.console.print()

        # Get selection
        while True:
            choice = Prompt.ask(
                f"Select provider [1-{len(PROVIDERS)}]",
                default="1",
                console=self.console,
            )

            if choice.lower() == "back":
                return "back"

            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(PROVIDERS):
                    selected_provider = PROVIDERS[choice_idx]
                    break
                else:
                    self._show_inline_error(
                        f"Invalid choice. Please enter 1-{len(PROVIDERS)}"
                    )
            except ValueError:
                self._show_inline_error(
                    f"Invalid input. Please enter a number 1-{len(PROVIDERS)}"
                )

        # Store provider
        self.config.provider_name = selected_provider.name

        # Select model
        models = AVAILABLE_MODELS.get(
            selected_provider.name,
            [DEFAULT_MODELS.get(selected_provider.name, "default")],
        )
        default_model = DEFAULT_MODELS.get(selected_provider.name, models[0])

        self.console.print()
        self.console.print("[bold]Available models:[/bold]")
        for idx, model in enumerate(models, 1):
            marker = " (default)" if model == default_model else ""
            self.console.print(f"  {idx}. {model}{marker}")
        self.console.print()

        while True:
            model_choice = Prompt.ask(
                f"Select model [1-{len(models)}]",
                default="1",
                console=self.console,
            )

            if model_choice.lower() == "back":
                return "back"

            try:
                model_idx = int(model_choice) - 1
                if 0 <= model_idx < len(models):
                    self.config.model = models[model_idx]
                    break
                else:
                    self._show_inline_error(
                        f"Invalid choice. Please enter 1-{len(models)}"
                    )
            except ValueError:
                self._show_inline_error(
                    f"Invalid input. Please enter a number 1-{len(models)}"
                )

        self.console.print()
        return "next"

    async def _step_credentials(self) -> str:
        """Step 4: Credentials Setup.

        Handles API key entry with environment variable check and validation.

        Returns:
            'next', 'back', or 'cancel'
        """
        self._show_progress("Credentials Setup")

        provider_info = PROVIDER_MAP.get(self.config.provider_name)

        if not provider_info or not provider_info.requires_api_key:
            self.console.print(
                "[green]No API key required for this provider.[/green]"
            )
            self.config.api_key = ""
            self.console.print()
            return "next"

        # Check environment variable first
        env_var = provider_info.api_key_env
        env_value = os.getenv(env_var, "")

        if env_value:
            masked = env_value[:8] + "..." + env_value[-4:] if len(env_value) > 12 else "***"
            self.console.print(
                f"[green]Found {env_var} in environment: {masked}[/green]"
            )

            use_env = Confirm.ask(
                "Use existing API key from environment?",
                default=True,
                console=self.console,
            )

            if use_env:
                self.config.api_key = env_value
                # Validate the key
                await self._validate_credentials()
                self.console.print()
                return "next"

        # Prompt for API key with password masking
        self.console.print(
            f"[dim]Required environment variable: {env_var}[/dim]"
        )

        api_key = Prompt.ask(
            "Enter API key",
            password=True,
            console=self.console,
        )

        if api_key.lower() == "back":
            return "back"

        if not api_key:
            self._show_inline_error("API key is required")
            return await self._step_credentials()

        self.config.api_key = api_key

        # Offer to reveal for verification
        reveal = Confirm.ask(
            "Reveal API key for verification?",
            default=False,
            console=self.console,
        )
        if reveal:
            self.console.print(f"[dim]API Key: {api_key}[/dim]")

        # Validate the credentials
        await self._validate_credentials()

        self.console.print()
        return "next"

    async def _validate_credentials(self) -> None:
        """Validate API key with spinner feedback."""
        from rich.status import Status

        with Status(
            "[bold cyan]Validating API key...[/bold cyan]",
            console=self.console,
            spinner="dots",
        ) as status:
            # Initialize validator if needed
            if self._validator is None:
                self._validator = ProviderValidator(self.console)

            # Build config for validation
            config = {
                "api_key_env": PROVIDER_MAP.get(
                    self.config.provider_name, PROVIDERS[0]
                ).api_key_env,
            }

            # Run validation
            result = await self._validator.validate_configuration(
                self.config.provider_name, config
            )

            if result.success:
                status.stop()
                self.console.print(
                    "[green]API key validated successfully[/green]"
                )
            else:
                status.stop()
                self._show_inline_error(
                    "Validation failed: " + ", ".join(result.warnings)
                )
                if result.suggestions:
                    self.console.print("[dim]Suggestions:[/dim]")
                    for suggestion in result.suggestions:
                        self.console.print(f"  [dim]- {suggestion}[/dim]")

    def _show_inline_error(self, message: str) -> None:
        """Display inline error message with red styling.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def _detect_project_type(self) -> str:
        """Detect project type from files in project root.

        Returns:
            Detected project type string
        """
        # Check for common project files
        if (self.project_root / "package.json").exists():
            return "javascript"
        elif (self.project_root / "pyproject.toml").exists():
            return "python"
        elif (self.project_root / "requirements.txt").exists():
            return "python"
        elif (self.project_root / "Cargo.toml").exists():
            return "rust"
        elif (self.project_root / "go.mod").exists():
            return "go"
        elif (self.project_root / "pom.xml").exists():
            return "java"
        elif (self.project_root / "build.gradle").exists():
            return "java"
        elif (self.project_root / "Gemfile").exists():
            return "ruby"
        elif (self.project_root / "composer.json").exists():
            return "php"
        elif (self.project_root / "*.csproj").exists():
            return "csharp"
        else:
            return "unknown"

    def _get_git_config(self, key: str) -> str:
        """Get value from global git config.

        Args:
            key: Git config key (e.g., 'user.name')

        Returns:
            Config value or empty string if not found
        """
        try:
            result = subprocess.run(
                ["git", "config", "--global", "--get", key],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug("git_config_error", key=key, error=str(e))

        return ""


async def run_wizard(project_root: Path, console: Optional[Console] = None) -> WizardConfig:
    """Convenience function to run the TUI wizard.

    Args:
        project_root: Project root directory
        console: Optional Rich Console

    Returns:
        WizardConfig with collected data
    """
    wizard = TUIWizard(project_root, console)
    return await wizard.run()
