"""Tests for SubcommandParser.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from gao_dev.cli.subcommand_parser import SubcommandParser
from gao_dev.core.services.ai_analysis_service import AIAnalysisService


@pytest.fixture
def mock_analysis_service():
    """Create mock AI analysis service."""
    service = MagicMock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def subcommand_parser(mock_analysis_service):
    """Create SubcommandParser instance."""
    return SubcommandParser(mock_analysis_service)


class TestSubcommandParser:
    """Test suite for SubcommandParser."""

    @pytest.mark.asyncio
    async def test_parse_ceremony_list(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing 'list ceremonies for epic 1'."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "ceremony",
            "subcommand": "list",
            "args": {"epic_num": 1}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("list ceremonies for epic 1")

        assert result is not None
        command, subcommand, args = result
        assert command == "ceremony"
        assert subcommand == "list"
        assert args["epic_num"] == 1

    @pytest.mark.asyncio
    async def test_parse_story_show(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing 'show story 30.4'."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "story",
            "subcommand": "show",
            "args": {"epic_num": 30, "story_num": 4}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("show story 30.4")

        assert result is not None
        command, subcommand, args = result
        assert command == "story"
        assert subcommand == "show"
        assert args["epic_num"] == 30
        assert args["story_num"] == 4

    @pytest.mark.asyncio
    async def test_parse_ceremony_run(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing 'run a retrospective'."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "ceremony",
            "subcommand": "run",
            "args": {"type": "retrospective"}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("run a retrospective")

        assert result is not None
        command, subcommand, args = result
        assert command == "ceremony"
        assert subcommand == "run"
        assert args["type"] == "retrospective"

    @pytest.mark.asyncio
    async def test_parse_state_show(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing 'what's the status?'."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "state",
            "subcommand": "show",
            "args": {}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("what's the status?")

        assert result is not None
        command, subcommand, args = result
        assert command == "state"
        assert subcommand == "show"

    @pytest.mark.asyncio
    async def test_parse_invalid_command(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing returns None for invalid command."""
        # Mock AI response with null command
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": None,
            "subcommand": None,
            "args": {}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("something unclear")

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_malformed_json(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing handles malformed JSON gracefully."""
        # Mock AI response with invalid JSON
        mock_result = MagicMock()
        mock_result.response = "Not valid JSON {{"
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("some input")

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_unsupported_command(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing rejects unsupported commands."""
        # Mock AI response with unsupported command
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "unsupported",
            "subcommand": "action",
            "args": {}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("unsupported command")

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_unsupported_subcommand(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing rejects unsupported subcommands."""
        # Mock AI response with invalid subcommand for ceremony
        mock_result = MagicMock()
        mock_result.response = json.dumps({
            "command": "ceremony",
            "subcommand": "invalid_action",
            "args": {}
        })
        mock_analysis_service.analyze.return_value = mock_result

        # Parse
        result = await subcommand_parser.parse("ceremony invalid_action")

        assert result is None

    @pytest.mark.asyncio
    async def test_parse_ai_service_failure(
        self, subcommand_parser, mock_analysis_service
    ):
        """Test parsing handles AI service failure gracefully."""
        # Mock AI service failure
        mock_analysis_service.analyze.side_effect = Exception("AI failed")

        # Parse
        result = await subcommand_parser.parse("some command")

        assert result is None

    def test_validate_command_valid(self, subcommand_parser):
        """Test command validation for valid commands."""
        assert subcommand_parser._validate_command("ceremony", "list") is True
        assert subcommand_parser._validate_command("learning", "show") is True
        assert subcommand_parser._validate_command("state", "show") is True

    def test_validate_command_invalid(self, subcommand_parser):
        """Test command validation for invalid commands."""
        assert subcommand_parser._validate_command("invalid", "list") is False
        assert subcommand_parser._validate_command("ceremony", "invalid") is False
        assert subcommand_parser._validate_command(None, "list") is False
        assert subcommand_parser._validate_command("ceremony", None) is False

    def test_get_supported_commands(self, subcommand_parser):
        """Test retrieving supported commands."""
        commands = subcommand_parser.get_supported_commands()

        assert "ceremony" in commands
        assert "learning" in commands
        assert "state" in commands
        assert isinstance(commands["ceremony"], list)
        assert "list" in commands["ceremony"]

    def test_format_command_help(self, subcommand_parser):
        """Test formatting command help."""
        help_text = subcommand_parser.format_command_help()

        assert "ceremony" in help_text.lower()
        assert "learning" in help_text.lower()
        assert "Examples" in help_text
        assert len(help_text) > 100

    def test_build_parsing_prompt(self, subcommand_parser):
        """Test parsing prompt construction."""
        prompt = subcommand_parser._build_parsing_prompt("list ceremonies")

        assert "list ceremonies" in prompt
        assert "ceremony" in prompt.lower()
        assert "JSON" in prompt
        assert len(prompt) > 200  # Should be substantial
