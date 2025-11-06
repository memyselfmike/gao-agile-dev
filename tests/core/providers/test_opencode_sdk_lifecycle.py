"""Unit tests for OpenCode SDK server lifecycle management.

Tests the server auto-start, health check, and shutdown functionality
added in Story 19.3.

Story: 19.3 - Server Lifecycle Management
"""

import pytest
import subprocess
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.exceptions import (
    ProviderInitializationError,
    ProviderConfigurationError,
)


class TestServerLifecycleInit:
    """Test server lifecycle configuration in __init__."""

    def test_init_with_default_lifecycle_config(self):
        """Test initialization with default lifecycle configuration."""
        provider = OpenCodeSDKProvider()

        assert provider.port == 4096
        assert provider.auto_start_server is True
        assert provider.startup_timeout == 30
        assert provider.health_check_timeout == 10
        assert provider.shutdown_timeout == 15
        assert provider.server_process is None

    def test_init_with_custom_lifecycle_config(self):
        """Test initialization with custom lifecycle configuration."""
        provider = OpenCodeSDKProvider(
            port=8080,
            auto_start_server=False,
            startup_timeout=60,
            health_check_timeout=20,
            shutdown_timeout=30,
        )

        assert provider.port == 8080
        assert provider.auto_start_server is False
        assert provider.startup_timeout == 60
        assert provider.health_check_timeout == 20
        assert provider.shutdown_timeout == 30

    def test_init_with_invalid_port_too_low(self):
        """Test initialization fails with port too low."""
        with pytest.raises(ProviderConfigurationError) as exc_info:
            OpenCodeSDKProvider(port=1023)

        assert "invalid port" in str(exc_info.value).lower()

    def test_init_with_invalid_port_too_high(self):
        """Test initialization fails with port too high."""
        with pytest.raises(ProviderConfigurationError) as exc_info:
            OpenCodeSDKProvider(port=65536)

        assert "invalid port" in str(exc_info.value).lower()

    def test_init_registers_atexit_handler(self):
        """Test that atexit handler is registered."""
        with patch('atexit.register') as mock_atexit:
            provider = OpenCodeSDKProvider()

            mock_atexit.assert_called_once_with(provider.cleanup_sync)


class TestServerStartup:
    """Test server startup functionality."""

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch.object(OpenCodeSDKProvider, '_wait_for_server_ready')
    def test_start_server_success(
        self,
        mock_wait_ready,
        mock_is_healthy,
        mock_is_port_in_use,
        mock_popen
    ):
        """Test successful server startup."""
        # Mock successful startup
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        mock_is_port_in_use.return_value = False
        mock_wait_ready.return_value = True

        provider = OpenCodeSDKProvider()
        provider._start_server()

        # Verify server process started
        mock_popen.assert_called_once_with(
            ["opencode", "serve", "--port", "4096"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert provider.server_process is not None
        assert provider.server_process.pid == 12345

    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    def test_start_server_port_in_use_with_healthy_server(
        self,
        mock_is_healthy,
        mock_is_port_in_use
    ):
        """Test startup when port in use with healthy server (reuse existing)."""
        mock_is_port_in_use.return_value = True
        mock_is_healthy.return_value = True

        provider = OpenCodeSDKProvider()
        provider._start_server()  # Should not raise

        # Server should not be started (reusing existing)
        assert provider.server_process is None

    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    def test_start_server_port_in_use_with_unhealthy_server(
        self,
        mock_is_healthy,
        mock_is_port_in_use
    ):
        """Test startup fails when port in use but server unhealthy."""
        mock_is_port_in_use.return_value = True
        mock_is_healthy.return_value = False

        provider = OpenCodeSDKProvider()

        with pytest.raises(ProviderInitializationError) as exc_info:
            provider._start_server()

        assert "port" in str(exc_info.value).lower()
        assert "not responding" in str(exc_info.value).lower()

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch.object(OpenCodeSDKProvider, '_wait_for_server_ready')
    @patch.object(OpenCodeSDKProvider, '_stop_server')
    def test_start_server_timeout_waiting_for_ready(
        self,
        mock_stop_server,
        mock_wait_ready,
        mock_is_port_in_use,
        mock_popen
    ):
        """Test startup fails when server doesn't become ready."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_is_port_in_use.return_value = False
        mock_wait_ready.return_value = False  # Timeout

        provider = OpenCodeSDKProvider()

        with pytest.raises(ProviderInitializationError) as exc_info:
            provider._start_server()

        assert "failed to become ready" in str(exc_info.value).lower()
        mock_stop_server.assert_called_once()

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_start_server_retry_on_subprocess_error(
        self,
        mock_sleep,
        mock_is_port_in_use,
        mock_popen
    ):
        """Test server startup retries on subprocess error."""
        mock_is_port_in_use.return_value = False
        mock_popen.side_effect = subprocess.SubprocessError("Failed to start")

        provider = OpenCodeSDKProvider()

        with pytest.raises(ProviderInitializationError) as exc_info:
            provider._start_server()

        # Should retry 3 times
        assert mock_popen.call_count == 3
        assert "after 3 attempts" in str(exc_info.value).lower()


class TestServerReadyWait:
    """Test waiting for server to be ready."""

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_server_ready_success(
        self,
        mock_time,
        mock_sleep,
        mock_is_healthy
    ):
        """Test waiting for server ready succeeds."""
        # First call returns False, second returns True
        mock_is_healthy.side_effect = [False, True]
        mock_time.side_effect = [0, 0.5, 1.0]  # Simulate time passing

        provider = OpenCodeSDKProvider()
        result = provider._wait_for_server_ready()

        assert result is True
        assert mock_is_healthy.call_count == 2

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_server_ready_timeout(
        self,
        mock_time,
        mock_sleep,
        mock_is_healthy
    ):
        """Test waiting for server ready times out."""
        provider = OpenCodeSDKProvider()  # Create provider first
        mock_is_healthy.return_value = False
        # Simulate timeout
        mock_time.side_effect = [0] + [provider.startup_timeout + 1] * 100

        result = provider._wait_for_server_ready()

        assert result is False

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_server_ready_process_crashes(
        self,
        mock_time,
        mock_sleep,
        mock_is_healthy
    ):
        """Test waiting detects when process crashes."""
        mock_is_healthy.return_value = False
        mock_time.side_effect = [0, 0.5]

        provider = OpenCodeSDKProvider()
        provider.server_process = MagicMock()
        provider.server_process.poll.return_value = 1  # Process exited

        result = provider._wait_for_server_ready()

        assert result is False


class TestHealthCheck:
    """Test health check functionality."""

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    def test_health_check_success(self, mock_is_healthy):
        """Test successful health check."""
        mock_is_healthy.return_value = True

        provider = OpenCodeSDKProvider()
        provider._health_check()  # Should not raise

        mock_is_healthy.assert_called_once()

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    def test_health_check_retry_and_success(self, mock_sleep, mock_is_healthy):
        """Test health check retries and eventually succeeds."""
        # Fail first 2 attempts, succeed on 3rd
        mock_is_healthy.side_effect = [False, False, True]

        provider = OpenCodeSDKProvider()
        provider._health_check()  # Should not raise

        assert mock_is_healthy.call_count == 3

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    def test_health_check_failure_after_retries(self, mock_sleep, mock_is_healthy):
        """Test health check fails after all retries."""
        mock_is_healthy.return_value = False

        provider = OpenCodeSDKProvider()

        with pytest.raises(ProviderInitializationError) as exc_info:
            provider._health_check()

        assert "health check failed" in str(exc_info.value).lower()
        assert mock_is_healthy.call_count == 3

    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    def test_health_check_exception_and_retry(self, mock_sleep, mock_is_healthy):
        """Test health check handles exceptions and retries."""
        # First call raises exception, second succeeds
        mock_is_healthy.side_effect = [Exception("Connection refused"), True]

        provider = OpenCodeSDKProvider()
        provider._health_check()  # Should not raise

        assert mock_is_healthy.call_count == 2


class TestServerHealthy:
    """Test server healthy check via HTTP."""

    def test_is_server_healthy_when_requests_not_available(self):
        """Test server health check returns False when requests module not available."""
        provider = OpenCodeSDKProvider()

        # When requests is None (not installed), should return False
        with patch('gao_dev.core.providers.opencode_sdk.requests', None):
            result = provider._is_server_healthy()
            assert result is False


class TestPortInUse:
    """Test port availability checking."""

    @patch('socket.socket')
    def test_is_port_in_use_available(self, mock_socket_class):
        """Test port availability check returns False for available port."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1  # Non-zero = not in use
        mock_socket_class.return_value.__enter__.return_value = mock_socket

        provider = OpenCodeSDKProvider()
        result = provider._is_port_in_use(4096)

        assert result is False
        mock_socket.connect_ex.assert_called_once_with(('localhost', 4096))

    @patch('socket.socket')
    def test_is_port_in_use_taken(self, mock_socket_class):
        """Test port availability check returns True for port in use."""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # 0 = in use
        mock_socket_class.return_value.__enter__.return_value = mock_socket

        provider = OpenCodeSDKProvider()
        result = provider._is_port_in_use(4096)

        assert result is True


class TestServerShutdown:
    """Test server shutdown functionality."""

    def test_stop_server_no_process(self):
        """Test stopping server when no process exists."""
        provider = OpenCodeSDKProvider()
        provider.server_process = None

        # Should not raise
        provider._stop_server()

        assert provider.server_process is None

    def test_stop_server_graceful_shutdown(self):
        """Test graceful server shutdown."""
        provider = OpenCodeSDKProvider()
        mock_process = MagicMock()
        mock_process.pid = 12345
        provider.server_process = mock_process

        provider._stop_server()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=15)
        assert provider.server_process is None

    def test_stop_server_force_kill_on_timeout(self):
        """Test force kill when graceful shutdown times out."""
        provider = OpenCodeSDKProvider()
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired("opencode", 15),
            None  # Second call (after kill) succeeds
        ]
        provider.server_process = mock_process

        provider._stop_server()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert mock_process.wait.call_count == 2
        assert provider.server_process is None

    def test_stop_server_handles_exceptions(self):
        """Test server stop handles exceptions gracefully."""
        provider = OpenCodeSDKProvider()
        mock_process = MagicMock()
        mock_process.terminate.side_effect = Exception("Process error")
        provider.server_process = mock_process

        # Should not raise
        provider._stop_server()


class TestInitializeWithServerLifecycle:
    """Test initialize() with server lifecycle management."""

    @pytest.mark.asyncio
    @patch.object(OpenCodeSDKProvider, '_start_server')
    @patch.object(OpenCodeSDKProvider, '_health_check')
    async def test_initialize_starts_server_when_auto_start_enabled(
        self,
        mock_health_check,
        mock_start_server
    ):
        """Test initialize calls _start_server when auto_start_server is True."""
        provider = OpenCodeSDKProvider(auto_start_server=True)

        # Mock the SDK import to avoid import error
        with patch.dict('sys.modules', {'opencode_ai': MagicMock()}):
            from unittest.mock import MagicMock as MockOpencode
            with patch('gao_dev.core.providers.opencode_sdk.Opencode', MockOpencode):
                await provider.initialize()

        mock_start_server.assert_called_once()
        mock_health_check.assert_called_once()
        assert provider._initialized is True

    @pytest.mark.asyncio
    @patch.object(OpenCodeSDKProvider, '_start_server')
    @patch.object(OpenCodeSDKProvider, '_health_check')
    async def test_initialize_skips_server_start_when_disabled(
        self,
        mock_health_check,
        mock_start_server
    ):
        """Test initialize skips _start_server when auto_start_server is False."""
        provider = OpenCodeSDKProvider(auto_start_server=False)

        # Mock the SDK import to avoid import error
        with patch.dict('sys.modules', {'opencode_ai': MagicMock()}):
            from unittest.mock import MagicMock as MockOpencode
            with patch('gao_dev.core.providers.opencode_sdk.Opencode', MockOpencode):
                await provider.initialize()

        mock_start_server.assert_not_called()
        mock_health_check.assert_called_once()
        assert provider._initialized is True

    @pytest.mark.asyncio
    @patch.object(OpenCodeSDKProvider, '_start_server')
    @patch.object(OpenCodeSDKProvider, '_stop_server')
    async def test_initialize_stops_server_on_failure(
        self,
        mock_stop_server,
        mock_start_server
    ):
        """Test initialize stops server on failure."""
        mock_start_server.side_effect = Exception("Server start failed")

        provider = OpenCodeSDKProvider(auto_start_server=True)

        with pytest.raises(ProviderInitializationError):
            await provider.initialize()

        mock_stop_server.assert_called_once()


class TestCleanupWithServerLifecycle:
    """Test cleanup() with server lifecycle management."""

    @pytest.mark.asyncio
    @patch.object(OpenCodeSDKProvider, '_stop_server')
    async def test_cleanup_stops_server_when_auto_started(self, mock_stop_server):
        """Test cleanup stops server when auto_start_server is True."""
        provider = OpenCodeSDKProvider(auto_start_server=True)
        provider._initialized = True

        await provider.cleanup()

        mock_stop_server.assert_called_once()
        assert provider._initialized is False

    @pytest.mark.asyncio
    @patch.object(OpenCodeSDKProvider, '_stop_server')
    async def test_cleanup_skips_stop_when_not_auto_started(self, mock_stop_server):
        """Test cleanup skips stop when auto_start_server is False."""
        provider = OpenCodeSDKProvider(auto_start_server=False)
        provider._initialized = True

        await provider.cleanup()

        mock_stop_server.assert_not_called()
        assert provider._initialized is False


class TestCleanupSync:
    """Test synchronous cleanup for atexit handler."""

    @patch.object(OpenCodeSDKProvider, '_stop_server')
    def test_cleanup_sync_stops_server_when_auto_started(self, mock_stop_server):
        """Test cleanup_sync stops server when auto_start_server is True."""
        provider = OpenCodeSDKProvider(auto_start_server=True)

        provider.cleanup_sync()

        mock_stop_server.assert_called_once()

    @patch.object(OpenCodeSDKProvider, '_stop_server')
    def test_cleanup_sync_skips_stop_when_not_auto_started(self, mock_stop_server):
        """Test cleanup_sync skips stop when auto_start_server is False."""
        provider = OpenCodeSDKProvider(auto_start_server=False)

        provider.cleanup_sync()

        mock_stop_server.assert_not_called()

    @patch.object(OpenCodeSDKProvider, '_stop_server')
    def test_cleanup_sync_handles_exceptions_silently(self, mock_stop_server):
        """Test cleanup_sync handles exceptions silently (for atexit)."""
        mock_stop_server.side_effect = Exception("Cleanup error")

        provider = OpenCodeSDKProvider(auto_start_server=True)

        # Should not raise
        provider.cleanup_sync()


class TestEndToEndServerLifecycle:
    """Test end-to-end server lifecycle scenarios."""

    @pytest.mark.asyncio
    @patch('opencode_ai.Opencode')
    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch.object(OpenCodeSDKProvider, '_is_port_in_use')
    @patch.object(OpenCodeSDKProvider, '_is_server_healthy')
    @patch('time.sleep')
    async def test_full_lifecycle_auto_start_and_cleanup(
        self,
        mock_sleep,
        mock_is_healthy,
        mock_is_port_in_use,
        mock_popen,
        mock_opencode
    ):
        """Test full lifecycle: init, start server, use, cleanup."""
        # Setup mocks
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        mock_is_port_in_use.return_value = False
        mock_is_healthy.return_value = True

        mock_client = MagicMock()
        mock_opencode.return_value = mock_client

        # Create provider with auto-start
        provider = OpenCodeSDKProvider(auto_start_server=True)

        # Initialize (should start server)
        await provider.initialize()

        assert provider._initialized is True
        assert provider.server_process is not None
        mock_popen.assert_called_once()

        # Cleanup (should stop server)
        await provider.cleanup()

        assert provider._initialized is False
        assert provider.server_process is None
        mock_process.terminate.assert_called_once()
