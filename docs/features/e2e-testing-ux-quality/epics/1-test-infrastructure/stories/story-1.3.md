# Story 1.3: ChatHarness Implementation

**Story ID**: 1.3
**Epic**: 1 - Test Infrastructure
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 8
**Priority**: Critical

---

## User Story

**As a** test developer
**I want** a ChatHarness class that spawns `gao-dev start` as subprocess and allows programmatic interaction
**So that** I can write E2E tests that validate real terminal execution of Brian

---

## Business Value

Current tests mock ProcessExecutor and ConversationalBrian, missing critical bugs that only appear in:
- Real subprocess execution
- Rich formatting and ANSI codes
- prompt-toolkit terminal interaction
- Cross-platform (Windows/macOS/Linux) differences

ChatHarness enables:
- True E2E testing from user perspective
- Detection of subprocess-specific bugs
- Cross-platform compatibility validation
- Foundation for all three testing modes

**Estimated bug prevention**: 30-50% reduction in user-reported terminal interaction issues

---

## Acceptance Criteria

- [ ] **AC1**: ChatHarness spawns `gao-dev start` subprocess using pexpect (Unix) or wexpect (Windows)
- [ ] **AC2**: ChatHarness.start() method waits for Brian greeting before returning
- [ ] **AC3**: ChatHarness.send(text) method sends input to Brian via stdin
- [ ] **AC4**: ChatHarness.expect(patterns) method waits for output matching regex patterns
- [ ] **AC5**: ChatHarness.read_until_prompt() method reads output until Brian prompt appears
- [ ] **AC6**: ChatHarness strips ANSI codes for clean pattern matching
- [ ] **AC7**: ChatHarness handles timeouts gracefully (default 30s, configurable)
- [ ] **AC8**: ChatHarness.close() method terminates subprocess cleanly
- [ ] **AC9**: ChatHarness works on Windows 10+ (wexpect), macOS (pexpect), Linux (pexpect)
- [ ] **AC10**: Resource cleanup happens even if tests fail (via context manager or pytest fixtures)

---

## Technical Context

### Architecture References

From Architecture document section 2.1 (ChatHarness):

**Purpose**: Spawn and interact with `gao-dev start` subprocess

**Key Responsibilities**:
- Cross-platform subprocess spawning (pexpect/wexpect)
- Send user input via stdin
- Capture output from stdout/stderr
- Handle timeouts and errors
- Clean subprocess termination

**Platform-Specific Notes**:
- **Unix/macOS**: Use `pexpect`
- **Windows**: Use `wexpect` (pexpect port for Windows)
- Both have similar APIs, abstracted in ChatHarness

### Implementation Details

**ChatHarness Class** (`tests/e2e/harness/chat_harness.py`):
```python
import re
import time
import platform
from pathlib import Path
from typing import List, Optional

class ChatHarness:
    """Spawn and interact with gao-dev start subprocess."""

    def __init__(
        self,
        test_mode: bool = False,
        capture_mode: bool = False,
        fixture_path: Optional[Path] = None,
        timeout: int = 30
    ):
        self.test_mode = test_mode
        self.capture_mode = capture_mode
        self.fixture_path = fixture_path
        self.timeout = timeout
        self.process = None
        self._platform = self._detect_platform()
        self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def start(self) -> None:
        """Spawn gao-dev start subprocess."""
        cmd = self._build_command()

        if self._platform == "windows":
            import wexpect
            self.process = wexpect.spawn(cmd, timeout=self.timeout)
        else:
            import pexpect
            self.process = pexpect.spawn(cmd, timeout=self.timeout, encoding='utf-8')

        # Wait for greeting (Brian's initial prompt)
        self.expect([r"Welcome to GAO-Dev|Brian:"])

    def send(self, text: str) -> None:
        """Send input to chat."""
        if not self.process:
            raise RuntimeError("Process not started. Call start() first.")
        self.process.sendline(text)

    def expect(
        self,
        patterns: List[str],
        timeout: Optional[int] = None
    ) -> str:
        """
        Wait for output matching patterns.

        Args:
            patterns: List of regex patterns to match
            timeout: Override default timeout

        Returns:
            Clean output (ANSI stripped)

        Raises:
            AssertionError: If patterns not found within timeout
        """
        output = self.read_until_prompt(timeout or self.timeout)
        clean_output = self._strip_ansi(output)

        for pattern in patterns:
            if not re.search(pattern, clean_output, re.DOTALL | re.MULTILINE):
                raise AssertionError(
                    f"Expected pattern not found: {pattern}\n"
                    f"Actual output:\n{clean_output}"
                )

        return clean_output

    def read_until_prompt(self, timeout: int) -> str:
        """Read output until Brian prompt appears."""
        output = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self.process.read_nonblocking(size=1024, timeout=0.1)
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8', errors='ignore')
                output += chunk

                # Check for Brian prompt
                if self._has_prompt(output):
                    break
            except Exception:
                # Timeout or read error - continue trying
                time.sleep(0.1)

        if not self._has_prompt(output):
            raise TimeoutError(f"Prompt not found within {timeout}s")

        return output

    def close(self) -> None:
        """Terminate subprocess cleanly."""
        if self.process:
            try:
                self.process.sendline("exit")
                self.process.expect(pexpect.EOF, timeout=5)
            except:
                pass
            finally:
                self.process.terminate(force=True)

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes."""
        return self._ansi_escape.sub('', text)

    def _build_command(self) -> str:
        """Build gao-dev start command with flags."""
        cmd = "gao-dev start"

        if self.test_mode:
            cmd += " --test-mode"
        if self.capture_mode:
            cmd += " --capture-mode"
        if self.fixture_path:
            cmd += f" --fixture {self.fixture_path}"

        return cmd

    def _detect_platform(self) -> str:
        """Detect OS platform."""
        system = platform.system().lower()
        return "windows" if system == "windows" else "unix"

    def _has_prompt(self, output: str) -> bool:
        """Check if output contains Brian prompt."""
        # Look for common prompt patterns
        prompt_patterns = [
            r"You:",
            r"Brian:",
            r">",
            r"\$",
        ]
        return any(re.search(p, output) for p in prompt_patterns)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
```

### Dependencies

- **Depends On**: Story 1.2 (test mode flags in ChatREPL)
- **External**: pexpect (Unix), wexpect (Windows), pytest
- Python 3.10+ (for match statement support)

---

## Test Scenarios

### Test 1: Cross-Platform Subprocess Spawn
```python
import pytest
import platform

def test_chat_harness_spawns_subprocess():
    """Test ChatHarness spawns gao-dev start on current platform."""
    harness = ChatHarness()

    # Should detect platform correctly
    if platform.system().lower() == "windows":
        assert harness._platform == "windows"
    else:
        assert harness._platform == "unix"

    # Start subprocess
    harness.start()

    # Should have process
    assert harness.process is not None

    # Cleanup
    harness.close()
```

### Test 2: Send and Expect
```python
def test_chat_harness_send_and_expect():
    """Test sending input and expecting output."""
    with ChatHarness(capture_mode=True) as harness:
        # Send a simple command
        harness.send("help")

        # Expect help output
        output = harness.expect(["commands", "available"])

        assert "help" in output.lower() or "commands" in output.lower()
```

### Test 3: ANSI Stripping
```python
def test_ansi_stripping():
    """Test ANSI escape code removal."""
    harness = ChatHarness()

    # Sample ANSI-formatted text
    ansi_text = "\x1b[32mGreen text\x1b[0m and normal text"

    clean_text = harness._strip_ansi(ansi_text)

    assert clean_text == "Green text and normal text"
    assert "\x1b" not in clean_text
```

### Test 4: Timeout Handling
```python
def test_timeout_handling():
    """Test timeout raises TimeoutError."""
    with ChatHarness(timeout=2) as harness:
        # Try to expect something that won't appear
        with pytest.raises(TimeoutError):
            harness.expect(["IMPOSSIBLE_PATTERN_XYZ123"], timeout=1)
```

### Test 5: Context Manager Cleanup
```python
def test_context_manager_cleanup():
    """Test context manager ensures subprocess cleanup."""
    harness = None

    try:
        with ChatHarness() as h:
            harness = h
            assert harness.process is not None

            # Simulate error
            raise RuntimeError("Simulated error")
    except RuntimeError:
        pass

    # Process should be terminated despite error
    assert harness.process.isalive() is False
```

### Test 6: Cross-Platform Path Handling
```python
def test_cross_platform_fixture_path(tmp_path):
    """Test fixture path works on all platforms."""
    fixture_path = tmp_path / "test.yaml"
    fixture_path.write_text("name: test\nscenario: []")

    harness = ChatHarness(test_mode=True, fixture_path=fixture_path)

    cmd = harness._build_command()

    # Path should be in command
    assert str(fixture_path) in cmd or fixture_path.name in cmd
```

---

## Definition of Done

- [ ] ChatHarness class implemented with all methods
- [ ] Cross-platform support (Windows/macOS/Linux) implemented
- [ ] ANSI stripping working correctly
- [ ] Timeout handling implemented
- [ ] Context manager implemented for resource cleanup
- [ ] Unit tests passing (6+ tests)
- [ ] Integration test with real `gao-dev start` passing
- [ ] Cross-platform testing completed (Windows, macOS, or Linux)
- [ ] Code reviewed and approved
- [ ] Documentation updated (docstrings, README)

---

## Implementation Notes

### Files to Create

**New Files**:
- `tests/e2e/harness/__init__.py`
- `tests/e2e/harness/chat_harness.py` - Main implementation
- `tests/e2e/test_chat_harness.py` - Unit tests

### Dependencies to Add

Update `pyproject.toml` or `requirements-dev.txt`:
```toml
[tool.poetry.group.dev.dependencies]
pexpect = "^4.9.0"  # Unix/macOS
wexpect = "^4.0.0"  # Windows
```

Or in `requirements-dev.txt`:
```
pexpect>=4.9.0; sys_platform != 'win32'
wexpect>=4.0.0; sys_platform == 'win32'
```

### Platform-Specific Gotchas

**Windows**:
- Use `wexpect` instead of `pexpect`
- Line endings may be `\r\n` instead of `\n`
- Path separators are backslashes
- Some ANSI codes may not render

**macOS/Linux**:
- Use `pexpect`
- Line endings are `\n`
- ANSI codes render properly
- Terminal encoding is UTF-8

**Cross-Platform Normalization**:
```python
def _normalize_output(self, text: str) -> str:
    """Normalize line endings and encoding for cross-platform."""
    # Convert all line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Ensure UTF-8 encoding
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')

    return text
```

### Pytest Fixture for Harness

Add to `tests/e2e/conftest.py`:
```python
import pytest
from tests.e2e.harness.chat_harness import ChatHarness

@pytest.fixture
def chat_harness():
    """Provide ChatHarness with automatic cleanup."""
    harness = ChatHarness(capture_mode=True)
    harness.start()
    yield harness
    harness.close()
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| pexpect/wexpect API differences break tests | High | High | Abstract differences in ChatHarness, comprehensive tests |
| Subprocess timing flakiness | High | Medium | Generous timeouts, retry logic, heartbeat detection |
| Terminal encoding issues | Medium | Medium | UTF-8 enforcement, error='ignore' decoding |
| Hung subprocesses on test failure | Medium | High | Context manager cleanup, pytest fixtures, timeout enforcement |
| ANSI code variations across terminals | Medium | Low | Robust ANSI regex, test on multiple terminals |
| Windows path handling issues | Medium | Medium | Path normalization, cross-platform testing |

---

## Related Stories

- **Depends On**: Story 1.2 (test mode flags)
- **Blocks**: Epic 2 stories (quality analysis needs ChatHarness)
- **Blocks**: Epic 3 stories (interactive tools need ChatHarness)
- **Related**: Story 1.4 (fixture system works with ChatHarness)

---

## References

- PRD Section: FR3 (Interactive Testing)
- Architecture Section: 2.1 ChatHarness
- pexpect documentation: https://pexpect.readthedocs.io/
- wexpect: https://pypi.org/project/wexpect/
- CRAAP Review: Risk "pexpect/wexpect Platform Inconsistencies"
