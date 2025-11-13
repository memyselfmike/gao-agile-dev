"""Interactive REPL for conversational chat with Brian."""

from typing import Optional
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import asyncio
import structlog

from gao_dev.cli.project_status import ProjectStatusReporter

logger = structlog.get_logger()


class ChatREPL:
    """
    Interactive REPL for conversational chat with Brian.

    Provides infinite while loop for user input, Rich formatting for
    beautiful output, and graceful exit handling.

    Attributes:
        console: Rich Console for formatted output
        prompt_session: Prompt-toolkit session for enhanced input
        history: In-memory history for arrow key navigation
        project_root: Project root path for context
        logger: Structured logger for observability
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize ChatREPL with full orchestration stack.

        Story 30.4: Now includes CommandRouter, HelpSystem, OperationTracker, SubcommandParser.

        Args:
            project_root: Optional project root
        """
        self.project_root = project_root or Path.cwd()
        self.console = Console()
        self.history = InMemoryHistory()
        self.prompt_session: PromptSession[str] = PromptSession(history=self.history)
        self.logger = logger.bind(component="chat_repl")

        # Initialize status reporter
        self.status_reporter = ProjectStatusReporter(self.project_root)

        # Story 30.4: Initialize full stack
        from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
        from gao_dev.orchestrator.conversational_brian import (
            ConversationalBrian,
            ConversationContext,
        )
        from gao_dev.core.workflow_registry import WorkflowRegistry
        from gao_dev.core.services.ai_analysis_service import AIAnalysisService
        from gao_dev.core.config_loader import ConfigLoader
        from gao_dev.core.services.process_executor import ProcessExecutor
        from gao_dev.cli.command_router import CommandRouter
        from gao_dev.cli.help_system import HelpSystem
        from gao_dev.cli.subcommand_parser import SubcommandParser
        from gao_dev.core.state.operation_tracker import OperationTracker
        from gao_dev.core.state.state_tracker import StateTracker

        # Create services
        config_loader = ConfigLoader(self.project_root)
        workflow_registry = WorkflowRegistry(config_loader)

        # Story 35.6: Interactive provider selection
        features = config_loader.get('features', {})
        if features.get('interactive_provider_selection', False):
            try:
                from gao_dev.cli.provider_selector import ProviderSelector
                from gao_dev.cli.exceptions import (
                    ProviderSelectionCancelled,
                    ProviderValidationFailed
                )

                selector = ProviderSelector(self.project_root, self.console)
                provider_config = selector.select_provider()

                # Create ProcessExecutor with selected config
                executor = ProcessExecutor(
                    self.project_root,
                    provider_name=provider_config['provider'],
                    provider_config=provider_config.get('config', {})
                )

            except ProviderSelectionCancelled:
                self.console.print("\n[yellow]Provider selection cancelled. Exiting.[/yellow]")
                import sys
                sys.exit(0)
            except ProviderValidationFailed as e:
                self.console.print(f"\n[red]Error:[/red] {e}")
                import sys
                sys.exit(1)
        else:
            # Use existing default ProcessExecutor creation
            executor = ProcessExecutor(self.project_root)

        analysis_service = AIAnalysisService(executor)

        # Create StateTracker if database exists
        db_path = self.project_root / ".gao-dev" / "documents.db"
        state_tracker = None
        if db_path.exists():
            try:
                state_tracker = StateTracker(db_path)
            except Exception as e:
                self.logger.warning("state_tracker_init_failed", error=str(e))

        # Create operation tracker
        operation_tracker = OperationTracker(state_tracker) if state_tracker else None

        # Create orchestrator using factory method
        from gao_dev.orchestrator.orchestrator import GAODevOrchestrator

        orchestrator = None
        try:
            orchestrator = GAODevOrchestrator.create_default(
                project_root=self.project_root,
                mode="cli"
            )
            self.logger.info("orchestrator_initialized", orchestrator="GAODevOrchestrator")
        except Exception as e:
            self.logger.warning("orchestrator_init_failed", error=str(e))
            # Continue without orchestrator - chat will work but workflows won't execute

        # Create command router
        if operation_tracker and analysis_service:
            self.command_router = CommandRouter(
                orchestrator=orchestrator,
                operation_tracker=operation_tracker,
                analysis_service=analysis_service,
                console=self.console
            )
        else:
            self.command_router = None

        # Create Brian orchestrator
        brian_orchestrator = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service,
            project_root=self.project_root,
        )

        # Create conversational Brian with router
        self.conversational_brian = ConversationalBrian(
            brian_orchestrator,
            command_router=self.command_router
        )

        # Create help system
        self.help_system = HelpSystem(analysis_service, state_tracker)

        # Create subcommand parser
        self.subcommand_parser = SubcommandParser(analysis_service)

        # Story 30.5: Create ChatSession for state management
        from gao_dev.orchestrator.chat_session import ChatSession

        self.session = ChatSession(
            conversational_brian=self.conversational_brian,
            command_router=self.command_router,
            project_root=self.project_root
        )

        # Legacy context (for backward compatibility)
        self.context = ConversationContext(
            project_root=str(self.project_root), session_history=[]
        )

    async def start(self) -> None:
        """
        Start interactive REPL loop.

        Story 30.4: Now checks for interrupted operations on startup.
        Story 30.5: Session state management with optional history load.

        Displays greeting, checks for recovery, enters infinite loop
        accepting user input, handles exit commands and Ctrl+C gracefully.
        """
        self.logger.info("chat_repl_starting")

        # Story 30.5: Optionally load previous session
        await self._maybe_load_previous_session()

        # Story 30.4: Check for interrupted operations
        await self._check_recovery()

        # Display greeting
        await self._show_greeting()

        # Main loop
        while True:
            try:
                # Get user input (async)
                user_input = await self.prompt_session.prompt_async(
                    "You: ", multiline=False
                )

                # Strip whitespace
                user_input = user_input.strip()

                # Check for exit commands
                if self._is_exit_command(user_input):
                    await self._show_farewell()
                    break

                # Handle empty input
                if not user_input:
                    continue

                # Handle input (now with full execution)
                await self._handle_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C pressed - Story 30.5: Cancel via session, don't exit
                self.logger.info("keyboard_interrupt_during_execution")
                self.console.print("\n[yellow]Operation cancelled by user[/yellow]")

                # Cancel current operation via session
                try:
                    await self.session.cancel_current_operation()
                except Exception as e:
                    self.logger.error("cancellation_failed", error=str(e))

                # Reset for next operation
                self.session.reset_cancellation()

                # Continue loop (don't exit)
                continue

            except EOFError:
                # Ctrl+D pressed
                self.logger.info("eof_received")
                await self._show_farewell()
                break

            except Exception as e:
                # Catch all other exceptions (never crash)
                self.logger.exception("repl_error", error=str(e))
                self._display_error(e)

        self.logger.info("chat_repl_stopped")

    async def _show_greeting(self) -> None:
        """Display welcome greeting with project status."""
        # Get project status
        status = self.status_reporter.get_status()

        # Format greeting with status
        greeting_text = f"""
# Welcome to GAO-Dev!

I'm Brian, your AI Engineering Manager.

{self.status_reporter.format_status(status)}

Type your requests in natural language, or type 'help' for available commands.
Type 'exit', 'quit', or 'bye' to end the session.
        """.strip()

        self.console.print()
        self.console.print(
            Panel(
                Markdown(greeting_text),
                title="[bold green]Brian[/bold green]",
                border_style="green",
            )
        )
        self.console.print()

    async def _show_farewell(self) -> None:
        """Display farewell message and save session."""
        # Story 30.5: Save session history
        try:
            save_path = self.session.save_session()
            self.logger.info("session_saved_on_exit", path=str(save_path))

            # Show memory stats
            stats = self.session.get_memory_usage()
            farewell = f"""Goodbye! Great work today. See you next time!

Session Stats:
- Conversation turns: {stats['turn_count']}
- Memory usage: {stats['memory_mb']} MB
- Session saved to: {save_path.name}
"""
        except Exception as e:
            self.logger.error("session_save_failed", error=str(e))
            farewell = "Goodbye! Great work today. See you next time!"

        self.console.print()
        self.console.print(
            Panel(farewell, title="[bold green]Brian[/bold green]", border_style="green")
        )
        self.console.print()

    def _is_exit_command(self, user_input: str) -> bool:
        """
        Check if input is an exit command.

        Args:
            user_input: User's input string

        Returns:
            True if input is an exit command, False otherwise
        """
        return user_input.lower() in ["exit", "quit", "bye", "goodbye"]

    async def _handle_input(self, user_input: str) -> None:
        """
        Handle user input with conversational Brian.

        Story 30.3: Real conversation.
        Story 30.4: Help system integration.
        Story 30.5: Session state management.

        Args:
            user_input: User's input string
        """
        # Story 30.4: Check for help request
        if user_input.lower().startswith("help"):
            try:
                help_text = await self.help_system.get_help(user_input, self.project_root)
                help_panel = self.help_system.format_help_panel(help_text)
                self.console.print(help_panel)
                return
            except Exception as e:
                self.logger.error("help_system_failed", error=str(e))
                # Fall through to normal handling

        # Story 30.5: Handle input via session (tracks history automatically)
        try:
            async for response in self.session.handle_input(user_input):
                self._display_response(response)
        except asyncio.CancelledError:
            # Already handled, just pass through
            pass

    async def _maybe_load_previous_session(self) -> None:
        """
        Optionally load previous session history.

        Story 30.5: Ask user if they want to restore previous session.
        """
        # Check if previous session exists
        gao_dev_dir = self.project_root / ".gao-dev"
        session_file = gao_dev_dir / "last_session_history.json"

        if not session_file.exists():
            return

        # Simple prompt (without rich interaction for now)
        self.console.print("[dim]Found previous session history.[/dim]")
        # Auto-load for now (could add prompt later)
        # For MVP, we'll just note it's available but not load it automatically
        self.logger.info("previous_session_found", file=str(session_file))

    async def _check_recovery(self) -> None:
        """
        Check for interrupted operations on startup.

        Story 30.4: Offer recovery options if operations were interrupted.
        """
        # Note: Would check operation_tracker.get_interrupted_operations()
        # For now, just log
        self.logger.info("checking_for_interrupted_operations")

    def _display_response(self, response: str) -> None:
        """
        Display Brian's response with Rich formatting.

        Args:
            response: Brian's response text
        """
        self.console.print(
            Panel(response, title="[bold green]Brian[/bold green]", border_style="green")
        )

    def _display_error(self, error: Exception) -> None:
        """
        Display error message with helpful suggestion.

        Args:
            error: Exception that occurred
        """
        error_msg = f"[red]Error:[/red] {str(error)}"
        suggestion = "Please try again or type 'help' for assistance."

        self.console.print()
        self.console.print(
            Panel(
                f"{error_msg}\n\n{suggestion}",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        self.console.print()
