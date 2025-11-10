"""Response formatting for interactive Brian chat with Rich visual styling.

This module provides the ResponseFormatter class for formatting conversational
responses with agent-specific colors, indentation hierarchy, and visual symbols.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

from enum import Enum
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import structlog

logger = structlog.get_logger()


class ResponseType(Enum):
    """
    Types of responses for consistent formatting.

    Each type has specific styling and indentation rules.
    """

    INTRO = "intro"
    """Introduction or analysis summary (Brian speaks)"""

    COMMENTARY = "commentary"
    """Brian's ongoing commentary (status updates)"""

    CONCLUSION = "conclusion"
    """Final summary or result"""

    QUESTION = "question"
    """Brian asking user for input"""

    AGENT_START = "agent_start"
    """Agent starting work (e.g., 'John is creating PRD...')"""

    AGENT_PROGRESS = "agent_progress"
    """Agent progress update (indented under agent)"""

    AGENT_OUTPUT = "agent_output"
    """Agent's output/artifact (indented)"""

    AGENT_COMPLETE = "agent_complete"
    """Agent completed work (success indicator)"""

    ERROR = "error"
    """Error message"""

    WARNING = "warning"
    """Warning message"""

    SUCCESS = "success"
    """Success message"""


class ResponseFormatter:
    """
    Format conversational responses with Rich styling.

    Provides consistent colors, indentation, and symbols for
    different response types and agents.

    Agent Color Scheme:
        - Brian: green
        - John: blue
        - Winston: magenta
        - Sally: cyan
        - Bob: yellow
        - Amelia: bright_cyan
        - Murat: bright_yellow
        - Mary: bright_magenta

    Visual Symbols:
        - -> (start)
        - * (progress)
        - v (success/checkmark)
        - x (error/cross)
        - ! (warning)

    Indentation:
        - Brian (left margin): 0 spaces
        - Agent work: 2 spaces
        - Agent details: 4 spaces

    Example:
        ```python
        formatter = ResponseFormatter()

        # Brian speaks
        text = formatter.format_response(
            "I'll coordinate with John to create the PRD.",
            response_type=ResponseType.INTRO
        )

        # Agent starts work
        text = formatter.format_response(
            "John is creating the PRD...",
            response_type=ResponseType.AGENT_START,
            agent="John"
        )

        # Agent progress
        text = formatter.format_response(
            "Analyzing requirements...",
            response_type=ResponseType.AGENT_PROGRESS,
            indent_level=1
        )
        ```
    """

    # Agent color mapping
    AGENT_COLORS: Dict[str, str] = {
        "brian": "green",
        "john": "blue",
        "winston": "magenta",
        "sally": "cyan",
        "bob": "yellow",
        "amelia": "bright_cyan",
        "murat": "bright_yellow",
        "mary": "bright_magenta",
    }

    # Visual symbols (ASCII only for Windows compatibility)
    SYMBOL_START = "->"
    SYMBOL_PROGRESS = "*"
    SYMBOL_SUCCESS = "v"
    SYMBOL_ERROR = "x"
    SYMBOL_WARNING = "!"

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize formatter.

        Args:
            console: Rich Console instance (creates new if not provided)
        """
        self.console = console or Console()
        self.logger = logger.bind(component="response_formatter")

    def format_response(
        self,
        text: str,
        response_type: ResponseType,
        agent: Optional[str] = None,
        indent_level: int = 0
    ) -> Text:
        """
        Format response with appropriate styling.

        Args:
            text: Response text to format
            response_type: Type of response
            agent: Agent name (if agent-related response)
            indent_level: Indentation level (0 = Brian, 1 = agent work, 2 = details)

        Returns:
            Rich Text object with styling applied
        """
        # Create Rich Text object
        styled_text = Text()

        # Calculate indentation
        indent = "  " * indent_level

        # Add symbol based on type
        symbol = self._get_symbol(response_type)
        if symbol:
            styled_text.append(f"{indent}{symbol} ", style=self._get_symbol_style(response_type))
        else:
            styled_text.append(indent)

        # Determine color
        color = self._get_color(response_type, agent)

        # Add text with color
        styled_text.append(text, style=color)

        return styled_text

    def format_panel(
        self,
        text: str,
        title: str = "Brian",
        agent: Optional[str] = None,
        style: str = "green"
    ) -> Panel:
        """
        Format text as Rich Panel (for important messages).

        Args:
            text: Panel content
            title: Panel title
            agent: Agent name (overrides title if provided)
            style: Border style (color)

        Returns:
            Rich Panel object
        """
        # Use agent name as title if provided
        if agent:
            title = agent.capitalize()
            style = self.AGENT_COLORS.get(agent.lower(), style)

        return Panel(
            text,
            title=f"[bold {style}]{title}[/bold {style}]",
            border_style=style
        )

    def _get_symbol(self, response_type: ResponseType) -> Optional[str]:
        """Get symbol for response type."""
        symbol_map = {
            ResponseType.AGENT_START: self.SYMBOL_START,
            ResponseType.AGENT_PROGRESS: self.SYMBOL_PROGRESS,
            ResponseType.AGENT_COMPLETE: self.SYMBOL_SUCCESS,
            ResponseType.ERROR: self.SYMBOL_ERROR,
            ResponseType.WARNING: self.SYMBOL_WARNING,
            ResponseType.SUCCESS: self.SYMBOL_SUCCESS,
        }
        return symbol_map.get(response_type)

    def _get_symbol_style(self, response_type: ResponseType) -> str:
        """Get style for symbol."""
        style_map = {
            ResponseType.AGENT_START: "bright_blue",
            ResponseType.AGENT_PROGRESS: "blue",
            ResponseType.AGENT_COMPLETE: "green",
            ResponseType.ERROR: "red",
            ResponseType.WARNING: "yellow",
            ResponseType.SUCCESS: "green",
        }
        return style_map.get(response_type, "white")

    def _get_color(self, response_type: ResponseType, agent: Optional[str]) -> str:
        """Get color for text based on response type and agent."""
        # Agent-specific responses use agent color
        if agent:
            return self.AGENT_COLORS.get(agent.lower(), "white")

        # Type-specific colors
        color_map = {
            ResponseType.INTRO: "green",
            ResponseType.COMMENTARY: "green",
            ResponseType.CONCLUSION: "green bold",
            ResponseType.QUESTION: "green bold",
            ResponseType.AGENT_START: "bright_blue",
            ResponseType.AGENT_PROGRESS: "blue",
            ResponseType.AGENT_OUTPUT: "white",
            ResponseType.AGENT_COMPLETE: "green",
            ResponseType.ERROR: "red",
            ResponseType.WARNING: "yellow",
            ResponseType.SUCCESS: "green",
        }
        return color_map.get(response_type, "white")

    def print_response(
        self,
        text: str,
        response_type: ResponseType,
        agent: Optional[str] = None,
        indent_level: int = 0
    ) -> None:
        """
        Format and print response to console.

        Args:
            text: Response text
            response_type: Type of response
            agent: Agent name (if agent-related)
            indent_level: Indentation level
        """
        formatted = self.format_response(text, response_type, agent, indent_level)
        self.console.print(formatted)

    def print_panel(
        self,
        text: str,
        title: str = "Brian",
        agent: Optional[str] = None,
        style: str = "green"
    ) -> None:
        """
        Format and print panel to console.

        Args:
            text: Panel content
            title: Panel title
            agent: Agent name
            style: Border style
        """
        panel = self.format_panel(text, title, agent, style)
        self.console.print(panel)
