"""Tests for web CLI commands."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gao_dev.cli.web_commands import web, start_web
from gao_dev.web.config import WebConfig


class TestWebCLI:
    """Tests for web CLI commands."""

    def test_web_group_exists(self):
        """Test web command group exists."""
        runner = CliRunner()
        result = runner.invoke(web, ["--help"])

        assert result.exit_code == 0
        assert "Web interface commands" in result.output

    def test_start_command_exists(self):
        """Test start command exists in web group."""
        runner = CliRunner()
        result = runner.invoke(web, ["start", "--help"])

        assert result.exit_code == 0
        assert "Start GAO-Dev web interface" in result.output
        assert "--port" in result.output
        assert "--host" in result.output
        assert "--no-browser" in result.output

    @patch("gao_dev.cli.web_commands.start_server")
    def test_start_with_defaults(self, mock_start_server):
        """Test start command with default options."""
        runner = CliRunner()

        # Mock to avoid actually starting server
        mock_start_server.return_value = None

        result = runner.invoke(web, ["start"])

        # Should attempt to start server
        mock_start_server.assert_called_once()
        call_args = mock_start_server.call_args

        # Check config
        config = call_args.kwargs["config"]
        assert config.host == "127.0.0.1"
        assert config.port == 3000
        assert config.auto_open is True

    @patch("gao_dev.cli.web_commands.start_server")
    def test_start_with_custom_port(self, mock_start_server):
        """Test start command with custom port."""
        runner = CliRunner()
        mock_start_server.return_value = None

        result = runner.invoke(web, ["start", "--port", "8080"])

        mock_start_server.assert_called_once()
        config = mock_start_server.call_args.kwargs["config"]
        assert config.port == 8080

    @patch("gao_dev.cli.web_commands.start_server")
    def test_start_with_custom_host(self, mock_start_server):
        """Test start command with custom host."""
        runner = CliRunner()
        mock_start_server.return_value = None

        result = runner.invoke(web, ["start", "--host", "0.0.0.0"])

        mock_start_server.assert_called_once()
        config = mock_start_server.call_args.kwargs["config"]
        assert config.host == "0.0.0.0"

    @patch("gao_dev.cli.web_commands.start_server")
    def test_start_with_no_browser(self, mock_start_server):
        """Test start command with --no-browser flag."""
        runner = CliRunner()
        mock_start_server.return_value = None

        result = runner.invoke(web, ["start", "--no-browser"])

        mock_start_server.assert_called_once()
        config = mock_start_server.call_args.kwargs["config"]
        assert config.auto_open is False

    @patch("gao_dev.cli.web_commands.start_server")
    def test_start_with_all_options(self, mock_start_server):
        """Test start command with all options."""
        runner = CliRunner()
        mock_start_server.return_value = None

        result = runner.invoke(
            web, ["start", "--port", "9000", "--host", "localhost", "--no-browser"]
        )

        mock_start_server.assert_called_once()
        config = mock_start_server.call_args.kwargs["config"]
        assert config.host == "localhost"
        assert config.port == 9000
        assert config.auto_open is False

    @patch("gao_dev.cli.web_commands.start_server")
    def test_port_conflict_error_handling(self, mock_start_server):
        """Test error handling when port is already in use."""
        runner = CliRunner()

        # Simulate port conflict
        mock_start_server.side_effect = OSError("Port 3000 already in use. Try `--port 3001`")

        result = runner.invoke(web, ["start"])

        assert result.exit_code == 1
        assert "Port 3000 already in use" in result.output

    @patch("gao_dev.cli.web_commands.start_server")
    def test_keyboard_interrupt_handling(self, mock_start_server):
        """Test graceful handling of KeyboardInterrupt."""
        runner = CliRunner()

        # Simulate Ctrl+C
        mock_start_server.side_effect = KeyboardInterrupt()

        result = runner.invoke(web, ["start"])

        assert result.exit_code == 0
        assert "Shutting down" in result.output

    @patch("gao_dev.cli.web_commands.start_server")
    def test_general_exception_handling(self, mock_start_server):
        """Test handling of unexpected exceptions."""
        runner = CliRunner()

        # Simulate unexpected error
        mock_start_server.side_effect = Exception("Unexpected error")

        result = runner.invoke(web, ["start"])

        assert result.exit_code == 1
        assert "Error: Failed to start web server" in result.output


@pytest.mark.integration
class TestWebCLIIntegration:
    """Integration tests for web CLI."""

    def test_web_command_in_main_cli(self):
        """Test web command is registered in main CLI."""
        from gao_dev.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "web" in result.output

    def test_web_start_help_from_main_cli(self):
        """Test web start help from main CLI."""
        from gao_dev.cli.commands import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["web", "start", "--help"])

        assert result.exit_code == 0
        assert "Start GAO-Dev web interface" in result.output
