"""
Tests for ProcessExecutor service.

Tests process execution, timeout handling, error capture, and output streaming.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from pathlib import Path

from gao_dev.core.services.process_executor import (
    ProcessExecutor,
    ProcessExecutionError
)


@pytest.fixture
def process_executor(temp_dir):
    """Create ProcessExecutor with temp directory."""
    cli_path = Path("/usr/bin/claude")
    return ProcessExecutor(
        project_root=temp_dir,
        cli_path=cli_path,
        api_key="test-api-key"
    )


@pytest.fixture
def process_executor_no_cli(temp_dir):
    """Create ProcessExecutor without CLI path."""
    return ProcessExecutor(
        project_root=temp_dir,
        cli_path=None,
        api_key="test-api-key"
    )


class TestProcessExecutorInitialization:
    """Test ProcessExecutor initialization."""

    def test_initialization_with_cli_and_api_key(self, temp_dir):
        """Test initialization with all parameters."""
        cli_path = Path("/usr/bin/claude")
        api_key = "test-key"

        executor = ProcessExecutor(
            project_root=temp_dir,
            cli_path=cli_path,
            api_key=api_key
        )

        assert executor.project_root == temp_dir
        assert executor.cli_path == cli_path
        assert executor.api_key == api_key

    def test_initialization_without_cli(self, temp_dir):
        """Test initialization without CLI path."""
        executor = ProcessExecutor(
            project_root=temp_dir,
            cli_path=None,
            api_key="test-key"
        )

        assert executor.project_root == temp_dir
        assert executor.cli_path is None
        assert executor.api_key == "test-key"

    def test_initialization_without_api_key_uses_env(self, temp_dir, monkeypatch):
        """Test initialization uses environment API key if not provided."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")

        executor = ProcessExecutor(
            project_root=temp_dir,
            cli_path=Path("/usr/bin/claude"),
            api_key=None
        )

        assert executor.api_key == "env-key"


class TestProcessExecution:
    """Test process execution functionality."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_success(self, process_executor):
        """Test successful task execution."""
        task = "Test task"
        expected_output = "Test output"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            # Mock process
            mock_process = MagicMock()
            mock_process.communicate.return_value = (expected_output, "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute
            output_lines = []
            async for line in process_executor.execute_agent_task(task):
                output_lines.append(line)

            # Assert
            assert len(output_lines) == 1
            assert output_lines[0] == expected_output

            # Verify subprocess call
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            assert "--print" in args[0]
            assert "--dangerously-skip-permissions" in args[0]
            assert str(process_executor.project_root) in args[0]

            # Verify communicate called with task
            mock_process.communicate.assert_called_once()
            assert mock_process.communicate.call_args[1]["input"] == task

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_stderr(self, process_executor):
        """Test execution with stderr output."""
        task = "Test task"
        stdout_output = "Some output"
        stderr_output = "Some warnings"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (stdout_output, stderr_output)
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute (should not fail on stderr)
            output_lines = []
            async for line in process_executor.execute_agent_task(task):
                output_lines.append(line)

            # Assert stdout was yielded
            assert len(output_lines) == 1
            assert output_lines[0] == stdout_output

    @pytest.mark.asyncio
    async def test_execute_agent_task_no_cli_raises_error(self, process_executor_no_cli):
        """Test execution fails if CLI not found."""
        task = "Test task"

        with pytest.raises(ValueError, match="Claude CLI not found"):
            async for _ in process_executor_no_cli.execute_agent_task(task):
                pass

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_custom_timeout(self, process_executor):
        """Test execution with custom timeout."""
        task = "Test task"
        custom_timeout = 1800

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute with custom timeout
            async for _ in process_executor.execute_agent_task(task, timeout=custom_timeout):
                pass

            # Verify timeout was passed
            assert mock_process.communicate.call_args[1]["timeout"] == custom_timeout

    @pytest.mark.asyncio
    async def test_execute_agent_task_default_timeout(self, process_executor):
        """Test execution uses default timeout."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute without timeout
            async for _ in process_executor.execute_agent_task(task):
                pass

            # Verify default timeout used
            assert mock_process.communicate.call_args[1]["timeout"] == 3600


class TestProcessErrorHandling:
    """Test error handling in process execution."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_non_zero_exit_code(self, process_executor):
        """Test execution fails on non-zero exit code."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "Error message")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            # Execute should raise
            with pytest.raises(ProcessExecutionError) as exc_info:
                async for _ in process_executor.execute_agent_task(task):
                    pass

            assert "exit code 1" in str(exc_info.value)
            assert "Error message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_agent_task_timeout(self, process_executor):
        """Test execution timeout."""
        task = "Long task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 1800)
            mock_process.kill = MagicMock()
            mock_popen.return_value = mock_process

            # Execute should raise TimeoutError
            with pytest.raises(TimeoutError) as exc_info:
                async for _ in process_executor.execute_agent_task(task, timeout=1800):
                    pass

            assert "timed out" in str(exc_info.value)
            assert "1800" in str(exc_info.value)

            # Verify process was killed
            mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_agent_task_subprocess_error(self, process_executor):
        """Test execution with subprocess exception."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = OSError("Failed to start process")

            # Execute should raise ProcessExecutionError
            with pytest.raises(ProcessExecutionError) as exc_info:
                async for _ in process_executor.execute_agent_task(task):
                    pass

            assert "Process execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_agent_task_exit_code_with_no_output(self, process_executor):
        """Test non-zero exit code with no output."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 127
            mock_popen.return_value = mock_process

            with pytest.raises(ProcessExecutionError) as exc_info:
                async for _ in process_executor.execute_agent_task(task):
                    pass

            error_msg = str(exc_info.value)
            assert "exit code 127" in error_msg
            assert "no output" in error_msg or "configured correctly" in error_msg


class TestProcessOutputHandling:
    """Test output handling and streaming."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_yields_output(self, process_executor):
        """Test that output is yielded properly."""
        task = "Test task"
        expected_output = "Line 1\nLine 2\nLine 3"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (expected_output, "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Collect output
            output = []
            async for chunk in process_executor.execute_agent_task(task):
                output.append(chunk)

            # Assert
            assert len(output) == 1
            assert output[0] == expected_output

    @pytest.mark.asyncio
    async def test_execute_agent_task_empty_output_succeeds(self, process_executor):
        """Test execution with empty output still succeeds."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Should not raise
            output = []
            async for chunk in process_executor.execute_agent_task(task):
                output.append(chunk)

            # No output yielded, but no error
            assert len(output) == 0

    @pytest.mark.asyncio
    async def test_execute_agent_task_partial_output_on_error(self, process_executor):
        """Test that partial output is yielded even on error."""
        task = "Test task"
        partial_output = "Some partial output"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = (partial_output, "Error occurred")
            mock_process.returncode = 1
            mock_popen.return_value = mock_process

            # Output should be yielded before error
            output = []
            with pytest.raises(ProcessExecutionError):
                async for chunk in process_executor.execute_agent_task(task):
                    output.append(chunk)

            # Partial output was yielded
            assert len(output) == 1
            assert output[0] == partial_output


class TestProcessEnvironment:
    """Test environment handling."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_sets_api_key_in_env(self, process_executor):
        """Test API key is set in process environment."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute
            async for _ in process_executor.execute_agent_task(task):
                pass

            # Verify env was passed with API key
            call_kwargs = mock_popen.call_args[1]
            assert "env" in call_kwargs
            assert call_kwargs["env"]["ANTHROPIC_API_KEY"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_execute_agent_task_working_directory(self, process_executor):
        """Test process working directory is set to project root."""
        task = "Test task"

        with patch('gao_dev.core.services.process_executor.subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.return_value = ("output", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Execute
            async for _ in process_executor.execute_agent_task(task):
                pass

            # Verify cwd was set
            call_kwargs = mock_popen.call_args[1]
            assert "cwd" in call_kwargs
            assert call_kwargs["cwd"] == str(process_executor.project_root)
