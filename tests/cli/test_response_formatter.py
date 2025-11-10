"""Tests for ResponseFormatter.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

import pytest
from rich.text import Text
from rich.panel import Panel

from gao_dev.cli.response_formatter import ResponseFormatter, ResponseType


class TestResponseFormatter:
    """Test suite for ResponseFormatter."""

    def test_init_default(self):
        """Test initialization with default console."""
        formatter = ResponseFormatter()
        assert formatter.console is not None

    def test_format_response_intro(self):
        """Test formatting intro response."""
        formatter = ResponseFormatter()
        text = formatter.format_response(
            "Let me analyze that...",
            ResponseType.INTRO
        )

        assert isinstance(text, Text)
        assert "Let me analyze" in str(text)

    def test_format_response_agent_start(self):
        """Test formatting agent start message."""
        formatter = ResponseFormatter()
        text = formatter.format_response(
            "John is creating PRD...",
            ResponseType.AGENT_START,
            agent="John"
        )

        assert isinstance(text, Text)
        assert "John" in str(text)
        # Should have start symbol
        assert formatter.SYMBOL_START in str(text)

    def test_format_response_agent_progress(self):
        """Test formatting agent progress message."""
        formatter = ResponseFormatter()
        text = formatter.format_response(
            "Analyzing requirements...",
            ResponseType.AGENT_PROGRESS,
            indent_level=1
        )

        assert isinstance(text, Text)
        # Should be indented
        assert str(text).startswith("  ")

    def test_format_response_error(self):
        """Test formatting error message."""
        formatter = ResponseFormatter()
        text = formatter.format_response(
            "Operation failed",
            ResponseType.ERROR
        )

        assert isinstance(text, Text)
        # Should have error symbol
        assert formatter.SYMBOL_ERROR in str(text)

    def test_format_response_success(self):
        """Test formatting success message."""
        formatter = ResponseFormatter()
        text = formatter.format_response(
            "Completed successfully",
            ResponseType.SUCCESS
        )

        assert isinstance(text, Text)
        # Should have success symbol
        assert formatter.SYMBOL_SUCCESS in str(text)

    def test_format_response_with_indentation(self):
        """Test indentation levels."""
        formatter = ResponseFormatter()

        # Level 0 (Brian)
        text0 = formatter.format_response("Text", ResponseType.INTRO, indent_level=0)
        assert not str(text0).startswith(" ")

        # Level 1 (agent work)
        text1 = formatter.format_response("Text", ResponseType.AGENT_PROGRESS, indent_level=1)
        assert str(text1).startswith("  ")

        # Level 2 (details)
        text2 = formatter.format_response("Text", ResponseType.AGENT_OUTPUT, indent_level=2)
        assert str(text2).startswith("    ")

    def test_agent_colors(self):
        """Test all agent colors are defined."""
        formatter = ResponseFormatter()

        agents = ["brian", "john", "winston", "sally", "bob", "amelia", "murat", "mary"]
        for agent in agents:
            assert agent in formatter.AGENT_COLORS
            assert isinstance(formatter.AGENT_COLORS[agent], str)

    def test_format_panel_default(self):
        """Test formatting panel with defaults."""
        formatter = ResponseFormatter()
        panel = formatter.format_panel("Test content")

        assert isinstance(panel, Panel)

    def test_format_panel_with_agent(self):
        """Test formatting panel with agent."""
        formatter = ResponseFormatter()
        panel = formatter.format_panel(
            "John's output",
            agent="John"
        )

        assert isinstance(panel, Panel)

    def test_symbols_are_ascii(self):
        """Test that all symbols are ASCII (Windows compatible)."""
        formatter = ResponseFormatter()

        # Check all symbols are ASCII (no emojis)
        assert formatter.SYMBOL_START.isascii()
        assert formatter.SYMBOL_PROGRESS.isascii()
        assert formatter.SYMBOL_SUCCESS.isascii()
        assert formatter.SYMBOL_ERROR.isascii()
        assert formatter.SYMBOL_WARNING.isascii()

    def test_get_symbol_for_types(self):
        """Test symbol retrieval for different types."""
        formatter = ResponseFormatter()

        # Types with symbols
        assert formatter._get_symbol(ResponseType.AGENT_START) == formatter.SYMBOL_START
        assert formatter._get_symbol(ResponseType.ERROR) == formatter.SYMBOL_ERROR
        assert formatter._get_symbol(ResponseType.SUCCESS) == formatter.SYMBOL_SUCCESS

        # Types without symbols
        assert formatter._get_symbol(ResponseType.INTRO) is None
        assert formatter._get_symbol(ResponseType.COMMENTARY) is None

    def test_get_color_for_agent(self):
        """Test color retrieval for agents."""
        formatter = ResponseFormatter()

        # Agent-specific colors
        assert formatter._get_color(ResponseType.AGENT_START, "John") == "blue"
        assert formatter._get_color(ResponseType.AGENT_PROGRESS, "Winston") == "magenta"

    def test_get_color_for_type(self):
        """Test color retrieval for response types."""
        formatter = ResponseFormatter()

        # Type-specific colors
        assert "green" in formatter._get_color(ResponseType.INTRO, None)
        assert "red" in formatter._get_color(ResponseType.ERROR, None)
        assert "yellow" in formatter._get_color(ResponseType.WARNING, None)

    def test_print_response_no_error(self):
        """Test print_response doesn't raise errors."""
        formatter = ResponseFormatter()

        # Should not raise
        formatter.print_response("Test", ResponseType.INTRO)

    def test_print_panel_no_error(self):
        """Test print_panel doesn't raise errors."""
        formatter = ResponseFormatter()

        # Should not raise
        formatter.print_panel("Test content")
