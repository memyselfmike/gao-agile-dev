# Story 19.3: Server Lifecycle Management

**Epic**: Epic 19 - OpenCode SDK Integration
**Status**: Draft
**Priority**: P1 (High)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev system
**I want** automatic OpenCode server lifecycle management
**So that** the server starts when needed, runs reliably, and shuts down gracefully

---

## Acceptance Criteria

### AC1: Auto-Start on Initialization
- Server starts automatically when provider initializes
- Server startup verified before returning from `initialize()`
- Startup happens in background (non-blocking after health check)
- Server process tracked for monitoring

### AC2: Health Check Implementation
- Health check confirms server is ready before task execution
- Uses SDK or HTTP request to verify server health
- Timeout for health check (default: 10 seconds)
- Retries health check on failure (max 3 attempts)
- Clear error message if health check fails

### AC3: Graceful Shutdown
- Server stops gracefully on `cleanup()` call
- All active sessions closed before shutdown
- Server process terminated cleanly
- Resources released (ports, file handles)

### AC4: Startup Failure Handling
- Retry server startup on failure (max 3 attempts)
- Clear error messages for different failure types
- Fallback to CLI provider documented (manual intervention)
- Port conflict detection and handling

### AC5: Configurable Port Support
- Port configurable via constructor parameter
- Default port: 4096
- Port validation (range: 1024-65535)
- Port conflict handling (try next available port)

### AC6: Process Management
- Server process tracked throughout lifecycle
- Process cleanup on Python exit (atexit handler)
- Zombie process prevention
- Process status monitoring

### AC7: Timeout Handling
- Startup timeout: 30 seconds default
- Health check timeout: 10 seconds default
- Shutdown timeout: 15 seconds default
- Configurable timeouts via constructor

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── opencode_sdk.py          # MODIFIED: Add server lifecycle management
└── exceptions.py            # MODIFIED: Add server-specific exceptions
```

### Implementation Approach

**Step 1: Add Server Management to OpenCodeSDKProvider**
```python
"""OpenCode SDK-based agent provider with server lifecycle management."""

import atexit
import subprocess
import time
import requests
from typing import Optional, Any
import structlog

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider

logger = structlog.get_logger(__name__)


class OpenCodeSDKProvider(IAgentProvider):
    """OpenCode SDK provider with automatic server management."""

    def __init__(
        self,
        server_url: str = "http://localhost:4096",
        port: int = 4096,
        auto_start_server: bool = True,
        startup_timeout: int = 30,
        health_check_timeout: int = 10,
        shutdown_timeout: int = 15,
        **kwargs: Any
    ) -> None:
        """
        Initialize provider with server lifecycle management.

        Args:
            server_url: URL of OpenCode server
            port: Port for OpenCode server
            auto_start_server: Whether to auto-start server on init
            startup_timeout: Max seconds to wait for server startup
            health_check_timeout: Max seconds for health check
            shutdown_timeout: Max seconds for graceful shutdown
        """
        self.server_url = server_url
        self.port = port
        self.auto_start_server = auto_start_server
        self.startup_timeout = startup_timeout
        self.health_check_timeout = health_check_timeout
        self.shutdown_timeout = shutdown_timeout

        self.server_process: Optional[subprocess.Popen] = None
        self.sdk_client: Optional[Opencode] = None
        self.session: Optional[Any] = None

        # Register cleanup on exit
        atexit.register(self.cleanup)

        logger.info(
            "opencode_sdk_provider_init",
            server_url=server_url,
            port=port,
            auto_start=auto_start_server,
        )

    def initialize(self) -> None:
        """Initialize provider and start server if needed."""
        try:
            logger.info("opencode_sdk_provider_initialize_start")

            # Start server if auto-start enabled
            if self.auto_start_server:
                self._start_server()

            # Verify server health
            self._health_check()

            # Create SDK client
            self.sdk_client = Opencode(base_url=self.server_url)

            logger.info("opencode_sdk_provider_initialize_complete")

        except Exception as e:
            logger.error(
                "opencode_sdk_provider_initialize_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Cleanup on failure
            self._stop_server()
            raise ProviderInitializationError(
                f"Failed to initialize OpenCode SDK provider: {e}"
            ) from e

    def _start_server(self) -> None:
        """
        Start OpenCode server process.

        Raises:
            ProviderInitializationError: If server startup fails
        """
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "opencode_server_start_attempt",
                    attempt=attempt,
                    max_retries=max_retries,
                    port=self.port,
                )

                # Check if port is available
                if self._is_port_in_use(self.port):
                    logger.warning(
                        "opencode_server_port_in_use",
                        port=self.port,
                    )
                    # Try to connect to existing server
                    if self._is_server_healthy():
                        logger.info("opencode_server_already_running")
                        return
                    else:
                        raise ProviderInitializationError(
                            f"Port {self.port} in use but server not responding"
                        )

                # Start server process
                self.server_process = subprocess.Popen(
                    ["opencode", "serve", "--port", str(self.port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                logger.info(
                    "opencode_server_process_started",
                    pid=self.server_process.pid,
                )

                # Wait for server to be ready
                if self._wait_for_server_ready():
                    logger.info("opencode_server_start_success")
                    return

                # Server didn't become ready
                self._stop_server()
                raise ProviderInitializationError(
                    f"Server failed to become ready within {self.startup_timeout}s"
                )

            except subprocess.SubprocessError as e:
                logger.warning(
                    "opencode_server_start_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise ProviderInitializationError(
                        f"Failed to start OpenCode server after {max_retries} attempts: {e}"
                    ) from e

    def _wait_for_server_ready(self) -> bool:
        """
        Wait for server to be ready with timeout.

        Returns:
            True if server is ready, False if timeout
        """
        start_time = time.time()
        check_interval = 0.5  # seconds

        while time.time() - start_time < self.startup_timeout:
            if self._is_server_healthy():
                return True

            time.sleep(check_interval)

            # Check if process crashed
            if self.server_process and self.server_process.poll() is not None:
                logger.error(
                    "opencode_server_process_crashed",
                    returncode=self.server_process.returncode,
                )
                return False

        return False

    def _health_check(self) -> None:
        """
        Perform health check on OpenCode server.

        Raises:
            ProviderInitializationError: If health check fails
        """
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(
                    "opencode_health_check_attempt",
                    attempt=attempt,
                )

                if self._is_server_healthy():
                    logger.info("opencode_health_check_success")
                    return

            except Exception as e:
                logger.warning(
                    "opencode_health_check_attempt_failed",
                    attempt=attempt,
                    error=str(e),
                )

                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise ProviderInitializationError(
                        f"Health check failed after {max_retries} attempts: {e}"
                    ) from e

    def _is_server_healthy(self) -> bool:
        """
        Check if OpenCode server is healthy.

        Returns:
            True if server responds to health check
        """
        try:
            # Try health endpoint (adjust URL based on actual API)
            health_url = f"{self.server_url}/health"
            response = requests.get(
                health_url,
                timeout=self.health_check_timeout,
            )
            return response.status_code == 200

        except requests.RequestException:
            return False

    def _is_port_in_use(self, port: int) -> bool:
        """
        Check if port is already in use.

        Args:
            port: Port number to check

        Returns:
            True if port is in use
        """
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def _stop_server(self) -> None:
        """Stop OpenCode server gracefully."""
        if not self.server_process:
            return

        try:
            logger.info(
                "opencode_server_stop_start",
                pid=self.server_process.pid,
            )

            # Try graceful shutdown first
            self.server_process.terminate()

            # Wait for graceful shutdown
            try:
                self.server_process.wait(timeout=self.shutdown_timeout)
                logger.info("opencode_server_stopped_gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("opencode_server_force_kill")
                self.server_process.kill()
                self.server_process.wait()

            self.server_process = None

        except Exception as e:
            logger.error(
                "opencode_server_stop_error",
                error=str(e),
            )

    def cleanup(self) -> None:
        """Clean up SDK resources and stop server."""
        try:
            logger.info("opencode_sdk_provider_cleanup_start")

            # Close session
            if self.session:
                self.session = None

            # Close SDK client
            if self.sdk_client:
                self.sdk_client = None

            # Stop server
            if self.auto_start_server:
                self._stop_server()

            logger.info("opencode_sdk_provider_cleanup_complete")

        except Exception as e:
            logger.warning(
                "opencode_sdk_provider_cleanup_error",
                error=str(e),
            )
```

**Step 2: Add Server-Specific Exceptions**
```python
# gao_dev/core/providers/exceptions.py

class ServerStartupError(ProviderError):
    """Raised when OpenCode server fails to start."""
    pass


class ServerHealthCheckError(ProviderError):
    """Raised when OpenCode server health check fails."""
    pass
```

---

## Testing Approach

### Unit Tests
```python
# tests/core/providers/test_opencode_sdk_lifecycle.py
"""Unit tests for OpenCode SDK server lifecycle management."""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call

from gao_dev.core.providers.opencode_sdk import OpenCodeSDKProvider
from gao_dev.core.providers.exceptions import ProviderInitializationError


class TestServerLifecycle:
    """Test server lifecycle management."""

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    @patch('gao_dev.core.providers.opencode_sdk.requests.get')
    def test_start_server_success(self, mock_requests, mock_popen):
        """Test successful server startup."""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        # Initialize provider
        provider = OpenCodeSDKProvider(auto_start_server=True)
        provider.initialize()

        # Verify server started
        mock_popen.assert_called_once()
        assert provider.server_process is not None

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    def test_start_server_failure(self, mock_popen):
        """Test server startup failure handling."""
        mock_popen.side_effect = subprocess.SubprocessError("Failed to start")

        provider = OpenCodeSDKProvider(auto_start_server=True)

        with pytest.raises(ProviderInitializationError) as exc_info:
            provider.initialize()

        assert "failed to start" in str(exc_info.value).lower()

    @patch('gao_dev.core.providers.opencode_sdk.requests.get')
    def test_health_check_success(self, mock_requests):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        provider = OpenCodeSDKProvider(auto_start_server=False)
        provider._health_check()

        mock_requests.assert_called()

    @patch('gao_dev.core.providers.opencode_sdk.requests.get')
    def test_health_check_failure(self, mock_requests):
        """Test health check failure handling."""
        mock_requests.side_effect = requests.RequestException("Connection failed")

        provider = OpenCodeSDKProvider(auto_start_server=False)

        with pytest.raises(ProviderInitializationError):
            provider._health_check()

    def test_is_port_in_use(self):
        """Test port availability checking."""
        provider = OpenCodeSDKProvider()

        # Port 80 likely in use or restricted
        # Port 65530 likely available
        # This is a basic test, may need adjustment

        assert isinstance(provider._is_port_in_use(4096), bool)

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    def test_stop_server_graceful(self, mock_popen):
        """Test graceful server shutdown."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        provider = OpenCodeSDKProvider()
        provider.server_process = mock_process
        provider._stop_server()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called()
        assert provider.server_process is None

    @patch('gao_dev.core.providers.opencode_sdk.subprocess.Popen')
    def test_stop_server_force_kill(self, mock_popen):
        """Test force kill when graceful shutdown fails."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.wait.side_effect = [subprocess.TimeoutExpired("opencode", 15), None]
        mock_popen.return_value = mock_process

        provider = OpenCodeSDKProvider()
        provider.server_process = mock_process
        provider._stop_server()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    def test_cleanup_stops_server(self):
        """Test cleanup stops server if auto-started."""
        provider = OpenCodeSDKProvider(auto_start_server=True)
        provider.server_process = MagicMock()

        provider.cleanup()

        # Server should be stopped
        assert provider.server_process is None

    @patch('gao_dev.core.providers.opencode_sdk.requests.get')
    def test_port_already_in_use_with_healthy_server(self, mock_requests):
        """Test handling when port in use with healthy server."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        provider = OpenCodeSDKProvider()

        # Mock port in use
        with patch.object(provider, '_is_port_in_use', return_value=True):
            provider._start_server()  # Should not raise, uses existing server
```

### Integration Tests (Story 19.4)
Full integration tests with real server in Story 19.4.

---

## Dependencies

### Required Packages
- opencode-ai ^0.1.0a36 (from Story 19.1)
- requests (existing)
- subprocess (standard library)

### Code Dependencies
- Story 19.1 (SDK dependency)
- Story 19.2 (Core provider implementation)

### External Dependencies
- OpenCode CLI installed and in PATH
- Available port for server (default: 4096)

---

## Definition of Done

- [x] Server auto-starts on provider initialization
- [x] Health check verifies server readiness
- [x] Server stops gracefully on cleanup
- [x] Retry logic for startup failures (max 3 attempts)
- [x] Configurable port support
- [x] Process management with atexit cleanup
- [x] Timeout handling for all operations
- [x] Unit tests for all lifecycle methods
- [x] Type checking passes (mypy strict mode)
- [x] All existing tests still pass
- [x] Code follows existing style (ASCII-only, type hints)
- [x] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 19.1 (Add OpenCode SDK Dependency)
- Story 19.2 (Implement OpenCodeSDKProvider Core)

**Blocks**:
- Story 19.4 (Integration Testing and Validation)
- Story 19.5 (Provider Registration and Documentation)

---

## Notes

### Key Design Decisions

1. **Auto-Start Default**: Server auto-starts by default for better UX
2. **Health Check Strategy**: HTTP request to `/health` endpoint with retries
3. **Graceful Shutdown**: Try terminate first, force kill if needed
4. **Port Conflict**: Reuse existing healthy server if port in use
5. **Cleanup Registration**: Use atexit to ensure cleanup on Python exit

### Server Startup Flow
1. Check if port is available
2. If port in use, check if server is healthy
3. If healthy server exists, reuse it
4. Otherwise, start new server process
5. Wait for server to be ready (health check)
6. Create SDK client

### Error Scenarios
- Port unavailable → Try to use existing server or fail
- Server crashes during startup → Retry up to 3 times
- Health check fails → Retry up to 3 times
- Startup timeout → Stop server and raise error

---

## Acceptance Testing

### Test Case 1: Auto-Start Server
```python
provider = OpenCodeSDKProvider(auto_start_server=True)
provider.initialize()
assert provider.server_process is not None
assert provider._is_server_healthy() is True
```
**Expected**: Server starts automatically and is healthy

### Test Case 2: Health Check
```python
provider = OpenCodeSDKProvider(auto_start_server=False)
# Assume server already running
provider._health_check()
# No exception raised
```
**Expected**: Health check passes for running server

### Test Case 3: Graceful Shutdown
```python
provider = OpenCodeSDKProvider()
provider.initialize()
pid = provider.server_process.pid
provider.cleanup()
# Check process no longer exists
```
**Expected**: Server stops gracefully, process terminated

### Test Case 4: Port Conflict
```python
# Start first provider
provider1 = OpenCodeSDKProvider(port=4096)
provider1.initialize()

# Start second provider on same port
provider2 = OpenCodeSDKProvider(port=4096)
provider2.initialize()  # Should reuse existing server

assert provider2._is_server_healthy() is True
```
**Expected**: Second provider reuses existing healthy server

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Server fails to start | High | Medium | Retry logic, clear error messages, fallback docs |
| Port conflicts | Medium | Medium | Detect and reuse existing server |
| Process cleanup fails | Medium | Low | Force kill after timeout, atexit handler |
| Health check false negatives | Low | Low | Multiple retries with delay |

---

## Implementation Checklist

- [ ] Add server lifecycle methods to `OpenCodeSDKProvider`
- [ ] Implement `_start_server()` method
- [ ] Implement `_wait_for_server_ready()` method
- [ ] Implement `_health_check()` method
- [ ] Implement `_is_server_healthy()` method
- [ ] Implement `_is_port_in_use()` method
- [ ] Implement `_stop_server()` method
- [ ] Update `initialize()` to start server
- [ ] Update `cleanup()` to stop server
- [ ] Add atexit handler registration
- [ ] Add server-specific exceptions
- [ ] Write comprehensive unit tests
- [ ] Run mypy type checking
- [ ] Run full test suite
- [ ] Create git commit with conventional message

---

**Created by**: Bob (Scrum Master) via BMAD workflow
**Ready for Implementation**: Yes (after Story 19.2)
**Estimated Completion**: 1 day

---

*This story is part of the GAO-Dev OpenCode SDK Integration project.*
