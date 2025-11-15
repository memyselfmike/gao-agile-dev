"""ChatHarness for spawning and interacting with gao-dev start subprocess.

Story: 36.3 - ChatHarness Implementation
Epic: 36 - Test Infrastructure

This module provides ChatHarness - a cross-platform subprocess wrapper that enables
true E2E testing by spawning `gao-dev start` and allowing programmatic interaction.

Key Features:
- Cross-platform support: pexpect (Unix/macOS) and wexpect (Windows)
- ANSI code stripping for clean pattern matching
- Configurable timeouts with graceful handling
- Context manager support for automatic cleanup
- Test mode and capture mode flags support
"""

import re
import time
import platform
from pathlib import Path
from typing import List, Optional, Union
import structlog

logger = structlog.get_logger()


class ChatHarness:
    """
    Spawn and interact with gao-dev start subprocess.

    Provides cross-platform subprocess spawning and interaction for E2E testing.
    Supports both pexpect (Unix/macOS) and wexpect (Windows) with automatic
    platform detection.

    Attributes:
        test_mode: Enable test mode with fixture responses
        capture_mode: Enable conversation capture logging
        fixture_path: Path to fixture file for test mode
        timeout: Default timeout in seconds for expect operations
        process: Underlying pexpect/wexpect process
        _platform: Detected platform ('windows' or 'unix')
        _ansi_escape: Compiled regex for ANSI code removal
        _pexpect_module: Dynamically loaded pexpect/wexpect module

    Example:
        >>> with ChatHarness(capture_mode=True) as harness:
        ...     harness.send("create a todo app")
        ...     output = harness.expect(["workflow", "selected"])
        ...     assert "workflow" in output
    """

    def __init__(
        self,
        test_mode: bool = False,
        capture_mode: bool = False,
        fixture_path: Optional[Path] = None,
        timeout: int = 30,
    ):
        """
        Initialize ChatHarness with configuration.

        Args:
            test_mode: Enable test mode with fixture responses
            capture_mode: Enable conversation capture logging
            fixture_path: Path to fixture file for test mode
            timeout: Default timeout in seconds (default: 30)

        Raises:
            ImportError: If pexpect/wexpect not installed for platform
        """
        self.test_mode = test_mode
        self.capture_mode = capture_mode
        self.fixture_path = fixture_path
        self.timeout = timeout
        self.process: Optional[Union[object, object]] = None
        self._platform = self._detect_platform()
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        self._pexpect_module: Optional[object] = None

        logger.info(
            "chat_harness_initialized",
            platform=self._platform,
            test_mode=test_mode,
            capture_mode=capture_mode,
            timeout=timeout,
        )

    def start(self) -> None:
        """
        Spawn gao-dev start subprocess.

        Waits for Brian greeting before returning to ensure subprocess
        is ready for interaction.

        Raises:
            ImportError: If pexpect/wexpect not available
            RuntimeError: If subprocess fails to start
            TimeoutError: If greeting not received within timeout

        Example:
            >>> harness = ChatHarness()
            >>> harness.start()
            >>> # Subprocess is now ready for interaction
        """
        logger.info("spawning_subprocess")

        # Build command with flags
        cmd = self._build_command()

        try:
            # Import platform-specific module
            if self._platform == "windows":
                import wexpect

                self._pexpect_module = wexpect
                # Windows: spawn with command string, no encoding parameter
                self.process = wexpect.spawn(cmd, timeout=self.timeout)
                logger.info("subprocess_spawned", platform="windows", cmd=cmd)

            else:
                import pexpect

                self._pexpect_module = pexpect
                # Unix/macOS: spawn with command string, UTF-8 encoding
                self.process = pexpect.spawn(
                    cmd, timeout=self.timeout, encoding='utf-8', codec_errors='ignore'
                )
                logger.info("subprocess_spawned", platform="unix", cmd=cmd)

        except ImportError as e:
            logger.error("pexpect_import_failed", platform=self._platform, error=str(e))
            if self._platform == "windows":
                raise ImportError(
                    "wexpect not installed. Install with: pip install wexpect"
                ) from e
            else:
                raise ImportError(
                    "pexpect not installed. Install with: pip install pexpect"
                ) from e

        except Exception as e:
            logger.error("subprocess_spawn_failed", error=str(e))
            raise RuntimeError(f"Failed to spawn subprocess: {e}") from e

        # Wait for Brian greeting (AC2)
        try:
            self._wait_for_greeting()
            logger.info("greeting_received", message="ChatHarness ready for interaction")
        except Exception as e:
            logger.error("greeting_timeout", error=str(e))
            self.close()
            raise

    def send(self, text: str) -> None:
        """
        Send input to chat via stdin.

        Args:
            text: Text to send to Brian

        Raises:
            RuntimeError: If process not started

        Example:
            >>> harness.send("help")
        """
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")

        logger.debug("sending_input", text=text)
        self.process.sendline(text)

    def expect(
        self, patterns: List[str], timeout: Optional[int] = None
    ) -> str:
        """
        Wait for output matching patterns.

        Reads output until Brian prompt appears, then checks if any pattern
        matches the output. ANSI codes are stripped for clean matching.

        Args:
            patterns: List of regex patterns to match
            timeout: Override default timeout (seconds)

        Returns:
            Clean output (ANSI stripped)

        Raises:
            RuntimeError: If process not started
            AssertionError: If patterns not found within timeout
            TimeoutError: If prompt not found within timeout

        Example:
            >>> output = harness.expect(["workflow", "selected"], timeout=10)
            >>> assert "workflow" in output
        """
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")

        # Read until prompt
        output = self.read_until_prompt(timeout or self.timeout)

        # Strip ANSI codes for clean matching
        clean_output = self._strip_ansi(output)

        # Check patterns
        for pattern in patterns:
            if not re.search(pattern, clean_output, re.DOTALL | re.MULTILINE):
                logger.error(
                    "pattern_not_found",
                    pattern=pattern,
                    output_preview=clean_output[:200],
                )
                raise AssertionError(
                    f"Expected pattern not found: {pattern}\n"
                    f"Actual output (first 500 chars):\n{clean_output[:500]}"
                )

        logger.debug("patterns_matched", patterns=patterns)
        return clean_output

    def read_until_prompt(self, timeout: int) -> str:
        """
        Read output until Brian prompt appears.

        Continuously reads from subprocess until a prompt pattern is detected
        or timeout is reached. Handles both bytes and str output, normalizes
        line endings.

        Args:
            timeout: Timeout in seconds

        Returns:
            Accumulated output (may include ANSI codes)

        Raises:
            RuntimeError: If process not started
            TimeoutError: If prompt not found within timeout

        Example:
            >>> output = harness.read_until_prompt(10)
        """
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")

        output = ""
        start_time = time.time()

        logger.debug("reading_until_prompt", timeout=timeout)

        while time.time() - start_time < timeout:
            try:
                # Read chunk with short timeout
                chunk = self.process.read_nonblocking(size=1024, timeout=0.1)

                # Convert bytes to str if needed
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')

                # Normalize line endings (Windows \r\n -> \n)
                chunk = chunk.replace('\r\n', '\n').replace('\r', '\n')

                output += chunk

                # Check for Brian prompt
                if self._has_prompt(output):
                    logger.debug(
                        "prompt_detected",
                        elapsed=time.time() - start_time,
                        output_length=len(output),
                    )
                    break

            except Exception:
                # Timeout on read or EOF - continue trying until overall timeout
                time.sleep(0.1)
                continue

        if not self._has_prompt(output):
            logger.error("prompt_timeout", timeout=timeout, output_preview=output[:200])
            raise TimeoutError(
                f"Prompt not found within {timeout}s\n"
                f"Output (first 500 chars):\n{output[:500]}"
            )

        return output

    def close(self) -> None:
        """
        Terminate subprocess cleanly.

        Attempts graceful exit by sending "exit" command, then forcefully
        terminates if needed. Safe to call multiple times.

        Example:
            >>> harness.close()
        """
        if not self.process:
            return

        logger.info("closing_subprocess")

        try:
            # Try graceful exit
            self.process.sendline("exit")

            # Wait for EOF
            if self._pexpect_module:
                self.process.expect(self._pexpect_module.EOF, timeout=5)

            logger.info("subprocess_closed_gracefully")

        except Exception as e:
            logger.warning("graceful_close_failed", error=str(e))

        finally:
            # Force terminate
            try:
                if hasattr(self.process, 'terminate'):
                    self.process.terminate(force=True)
                elif hasattr(self.process, 'kill'):
                    self.process.kill(9)

                logger.info("subprocess_terminated")

            except Exception as e:
                logger.warning("force_terminate_failed", error=str(e))

            self.process = None

    def _strip_ansi(self, text: str) -> str:
        """
        Remove ANSI escape codes from text.

        Uses regex pattern that matches all ANSI escape sequences including
        colors, cursor movement, and formatting codes.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Clean text without ANSI codes

        Example:
            >>> harness._strip_ansi("\\x1b[32mGreen\\x1b[0m text")
            'Green text'
        """
        return self._ansi_escape.sub('', text)

    def _build_command(self) -> str:
        """
        Build gao-dev start command with flags.

        Constructs command string with optional test mode, capture mode,
        and fixture path flags.

        Returns:
            Command string ready for subprocess spawn

        Example:
            >>> cmd = harness._build_command()
            >>> assert "gao-dev start" in cmd
        """
        cmd = "gao-dev start"

        if self.test_mode:
            cmd += " --test-mode"

        if self.capture_mode:
            cmd += " --capture-mode"

        if self.fixture_path:
            # Quote path if it contains spaces (cross-platform)
            path_str = str(self.fixture_path)
            if ' ' in path_str:
                cmd += f' --fixture "{path_str}"'
            else:
                cmd += f" --fixture {path_str}"

        logger.debug("command_built", cmd=cmd)
        return cmd

    def _detect_platform(self) -> str:
        """
        Detect OS platform.

        Returns:
            'windows' or 'unix'

        Example:
            >>> platform = harness._detect_platform()
            >>> assert platform in ['windows', 'unix']
        """
        system = platform.system().lower()
        detected = "windows" if system == "windows" else "unix"
        logger.debug("platform_detected", system=system, normalized=detected)
        return detected

    def _has_prompt(self, output: str) -> bool:
        """
        Check if output contains Brian prompt.

        Looks for common prompt patterns that indicate Brian is ready
        for input. Checks both clean output and ANSI-stripped output.

        Args:
            output: Output text to check

        Returns:
            True if prompt detected, False otherwise

        Example:
            >>> harness._has_prompt("You: ")
            True
        """
        # Strip ANSI first for reliable detection
        clean = self._strip_ansi(output)

        # Common prompt patterns
        prompt_patterns = [
            r"You:\s*$",  # Standard prompt
            r"Brian:\s*",  # Brian's responses end with his name
            r">\s*$",  # Generic prompt
            r"\$\s*$",  # Shell-style prompt
        ]

        for pattern in prompt_patterns:
            if re.search(pattern, clean, re.MULTILINE):
                return True

        return False

    def _wait_for_greeting(self) -> None:
        """
        Wait for Brian greeting after subprocess start.

        Reads output until greeting patterns are detected. This ensures
        subprocess is fully initialized before returning from start().

        Raises:
            TimeoutError: If greeting not received within timeout

        Example:
            >>> harness._wait_for_greeting()
        """
        logger.debug("waiting_for_greeting")

        greeting_patterns = [
            r"Welcome to GAO-Dev",
            r"Brian",
            r"Type.*help",
            r"You:",
        ]

        output = ""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                chunk = self.process.read_nonblocking(size=1024, timeout=0.5)

                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')

                chunk = chunk.replace('\r\n', '\n').replace('\r', '\n')
                output += chunk

                # Check for greeting patterns
                clean_output = self._strip_ansi(output)
                for pattern in greeting_patterns:
                    if re.search(pattern, clean_output, re.DOTALL | re.IGNORECASE):
                        logger.debug("greeting_found", pattern=pattern)
                        return

            except Exception:
                # Continue trying
                time.sleep(0.1)
                continue

        # Timeout - log output for debugging
        logger.error(
            "greeting_timeout",
            timeout=self.timeout,
            output_preview=output[:500],
        )
        raise TimeoutError(
            f"Brian greeting not received within {self.timeout}s\n"
            f"Output (first 500 chars):\n{output[:500]}"
        )

    def __enter__(self) -> "ChatHarness":
        """
        Context manager entry - starts subprocess.

        Returns:
            self for context manager usage

        Example:
            >>> with ChatHarness() as harness:
            ...     harness.send("help")
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit - ensures cleanup.

        Closes subprocess even if exception occurred during usage.
        This ensures no orphaned processes.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)

        Example:
            >>> with ChatHarness() as harness:
            ...     raise RuntimeError("Error")
            ... # Subprocess is still cleaned up
        """
        self.close()
