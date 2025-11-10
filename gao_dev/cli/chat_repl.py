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
        Initialize ChatREPL.

        Args:
            project_root: Optional project root (for future session integration)
        """
        self.project_root = project_root or Path.cwd()
        self.console = Console()
        self.history = InMemoryHistory()
        self.prompt_session: PromptSession[str] = PromptSession(history=self.history)
        self.logger = logger.bind(component="chat_repl")

        # Initialize status reporter
        self.status_reporter = ProjectStatusReporter(self.project_root)

        # Initialize Conversational Brian (Story 30.3)
        from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
        from gao_dev.orchestrator.conversational_brian import (
            ConversationalBrian,
            ConversationContext,
        )
        from gao_dev.core.workflow_registry import WorkflowRegistry
        from gao_dev.core.services.ai_analysis_service import AIAnalysisService
        from gao_dev.core.config_loader import ConfigLoader
        from gao_dev.core.services.process_executor import ProcessExecutor

        # Create Brian orchestrator
        config_loader = ConfigLoader(self.project_root)
        workflow_registry = WorkflowRegistry(config_loader)
        executor = ProcessExecutor(self.project_root)
        analysis_service = AIAnalysisService(executor)
        brian_orchestrator = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service,
            project_root=self.project_root,
        )
        self.conversational_brian = ConversationalBrian(brian_orchestrator)

        # Conversation context
        self.context = ConversationContext(
            project_root=str(self.project_root), session_history=[]
        )

    async def start(self) -> None:
        """
        Start interactive REPL loop.

        Displays greeting, enters infinite loop accepting user input,
        handles exit commands and Ctrl+C gracefully.
        """
        self.logger.info("chat_repl_starting")

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

                # Echo input (for now - will be replaced by actual handling in Story 30.3)
                await self._handle_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C pressed
                self.logger.info("keyboard_interrupt")
                await self._show_farewell()
                break

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
        """Display farewell message."""
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

        Story 30.3: Replaces simple echo with real conversation.

        Args:
            user_input: User's input string
        """
        # Add to session history
        self.context.session_history.append(f"User: {user_input}")

        # Get responses from conversational Brian
        async for response in self.conversational_brian.handle_input(user_input, self.context):
            self._display_response(response)

            # Add to session history
            self.context.session_history.append(f"Brian: {response}")

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
