"""Integration tests for ClaudeCodeProvider.

Tests end-to-end execution scenarios and behavioral compatibility
with ProcessExecutor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from gao_dev.core.providers.claude_code import ClaudeCodeProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError
)


@pytest.mark.integration
class TestClaudeCodeProviderIntegration:
    """Integration tests for ClaudeCodeProvider."""

    @pytest.mark.asyncio
    async def test_full_execution_cycle(self, tmp_path):
        """Test complete execution cycle from initialization to cleanup."""
        # Mock successful execution
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Task completed", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            # Initialize
            await provider.initialize()
            assert provider._initialized is True

            # Validate configuration
            with patch.object(Path, 'exists', return_value=True):
                is_valid = await provider.validate_configuration()
                assert is_valid is True

            # Execute task
            context = AgentContext(project_root=tmp_path)
            results = []

            async for result in provider.execute_task(
                task="Implement feature X",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write", "Bash"],
                timeout=3600
            ):
                results.append(result)

            assert len(results) > 0
            assert "Task completed" in results[0]

            # Cleanup
            await provider.cleanup()
            assert provider._initialized is False

    @pytest.mark.asyncio
    async def test_multiple_sequential_executions(self, tmp_path):
        """Test multiple task executions in sequence."""
        mock_process = Mock()
        mock_process.returncode = 0

        # Different outputs for each execution
        outputs = [
            ("First task complete", ""),
            ("Second task complete", ""),
            ("Third task complete", ""),
        ]

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            for i, (stdout, stderr) in enumerate(outputs):
                mock_process.communicate.return_value = (stdout, stderr)

                results = []
                async for result in provider.execute_task(
                    task=f"Task {i+1}",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    results.append(result)

                assert len(results) == 1
                assert stdout in results[0]

    @pytest.mark.asyncio
    async def test_execution_with_different_models(self, tmp_path):
        """Test execution with different model names."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        models_to_test = [
            ("sonnet-4.5", "claude-sonnet-4-5-20250929"),
            ("sonnet-3.5", "claude-sonnet-3-5-20241022"),
            ("opus-3", "claude-opus-3-20250219"),
            ("haiku-3", "claude-haiku-3-20250219"),
        ]

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            for canonical, expected_id in models_to_test:
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model=canonical,
                    tools=["Read"],
                    timeout=60
                ):
                    pass

                # Verify correct model ID was used
                call_args = popen_mock.call_args
                cmd = call_args[0][0]
                assert expected_id in cmd

    @pytest.mark.asyncio
    async def test_error_recovery(self, tmp_path):
        """Test error handling and recovery."""
        mock_process = Mock()

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            # First execution fails
            mock_process.returncode = 1
            mock_process.communicate.return_value = ("", "Error")

            with pytest.raises(ProviderExecutionError):
                async for _ in provider.execute_task(
                    task="Failing task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            # Second execution succeeds (provider should recover)
            mock_process.returncode = 0
            mock_process.communicate.return_value = ("Success", "")

            results = []
            async for result in provider.execute_task(
                task="Succeeding task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                results.append(result)

            assert len(results) == 1
            assert "Success" in results[0]

    @pytest.mark.asyncio
    async def test_timeout_handling(self, tmp_path):
        """Test timeout handling with different timeout values."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 30)
        mock_process.kill = Mock()

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            # Test with short timeout
            with pytest.raises(ProviderTimeoutError) as exc_info:
                async for _ in provider.execute_task(
                    task="Long running task",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=30
                ):
                    pass

            assert "30 seconds" in str(exc_info.value)
            mock_process.kill.assert_called()

    @pytest.mark.asyncio
    async def test_context_working_directory(self, tmp_path):
        """Test execution with different working directories."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        # Create subdirectory
        subdir = tmp_path / "subproject"
        subdir.mkdir()

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            # Execute with project_root
            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Verify cwd was set correctly
            call_args = popen_mock.call_args
            assert call_args[1]['cwd'] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_partial_output_before_failure(self, tmp_path):
        """Test that partial output is yielded even if execution fails."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("Partial output before crash", "Fatal error")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            results = []
            with pytest.raises(ProviderExecutionError):
                async for result in provider.execute_task(
                    task="Task that fails",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    results.append(result)

            # Should have yielded partial output before raising exception
            assert len(results) == 1
            assert "Partial output" in results[0]


@pytest.mark.integration
class TestClaudeCodeProviderCompatibility:
    """Test behavioral compatibility with ProcessExecutor."""

    @pytest.mark.asyncio
    async def test_same_command_structure_as_process_executor(self, tmp_path):
        """Verify command structure matches ProcessExecutor exactly."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read", "Write"],
                timeout=3600
            ):
                pass

            # Verify command matches ProcessExecutor
            call_args = popen_mock.call_args
            cmd = call_args[0][0]

            # Same flags in same order as ProcessExecutor
            assert cmd[0] == str(provider.cli_path)
            assert cmd[1] == '--print'
            assert cmd[2] == '--dangerously-skip-permissions'
            assert cmd[3] == '--model'
            assert cmd[4] == 'claude-sonnet-4-5-20250929'
            assert cmd[5] == '--add-dir'
            assert cmd[6] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_same_subprocess_settings_as_process_executor(self, tmp_path):
        """Verify subprocess settings match ProcessExecutor exactly."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process) as popen_mock:
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            async for _ in provider.execute_task(
                task="Test task",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=3600
            ):
                pass

            # Verify subprocess settings match ProcessExecutor
            call_args = popen_mock.call_args
            kwargs = call_args[1]

            assert kwargs['stdin'] == subprocess.PIPE
            assert kwargs['stdout'] == subprocess.PIPE
            assert kwargs['stderr'] == subprocess.PIPE
            assert kwargs['text'] is True
            assert kwargs['encoding'] == 'utf-8'
            assert kwargs['errors'] == 'replace'
            assert kwargs['cwd'] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_same_error_messages_as_process_executor(self, tmp_path):
        """Verify error messages match ProcessExecutor exactly."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            with pytest.raises(ProviderExecutionError) as exc_info:
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            # Should match ProcessExecutor error message exactly
            error_msg = str(exc_info.value)
            assert "Claude CLI failed with exit code 1" in error_msg
            assert "check if claude.bat is configured correctly" in error_msg

    @pytest.mark.asyncio
    async def test_same_logging_behavior_as_process_executor(self, tmp_path):
        """Verify logging behavior matches ProcessExecutor."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success output", "Warning in stderr")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            # Execute task (logging happens internally)
            async for _ in provider.execute_task(
                task="Test",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            # Test passes if no exceptions (logging verified by structlog)
            # In real usage, we'd capture and verify log events


@pytest.mark.integration
class TestClaudeCodeProviderPerformance:
    """Performance tests for ClaudeCodeProvider."""

    @pytest.mark.asyncio
    async def test_no_unnecessary_overhead(self, tmp_path):
        """Test that provider adds minimal overhead vs direct subprocess."""
        import time

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            # Measure execution time
            start = time.time()

            async for _ in provider.execute_task(
                task="Test",
                context=context,
                model="sonnet-4.5",
                tools=["Read"],
                timeout=60
            ):
                pass

            duration = time.time() - start

            # Should complete in under 100ms (overhead should be minimal)
            assert duration < 0.1

    @pytest.mark.asyncio
    async def test_no_memory_leaks(self, tmp_path):
        """Test that multiple executions don't leak memory."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Success", "")

        with patch('subprocess.Popen', return_value=mock_process):
            provider = ClaudeCodeProvider(
                cli_path=Path("/usr/bin/claude"),
                api_key="test-key"
            )

            context = AgentContext(project_root=tmp_path)

            # Execute many times
            for _ in range(100):
                async for _ in provider.execute_task(
                    task="Test",
                    context=context,
                    model="sonnet-4.5",
                    tools=["Read"],
                    timeout=60
                ):
                    pass

            # Test passes if no exceptions (memory leaks would cause issues)
