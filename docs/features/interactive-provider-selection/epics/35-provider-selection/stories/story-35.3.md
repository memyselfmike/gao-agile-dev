# Story 35.3: ProviderValidator Implementation

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.3
**Story Points**: 5
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.1
**Priority**: P0
**Status**: Todo

---

## Description

Implement `ProviderValidator` class for validating provider configurations, checking CLI availability cross-platform, detecting Ollama models, and providing actionable error messages with fix suggestions.

This story focuses on:
- Cross-platform CLI detection (Windows, macOS, Linux)
- Ollama model detection with increased timeout
- Comprehensive validation with clear error messages
- Async implementation for performance
- Extensive test coverage (>90%)

---

## Acceptance Criteria

- [ ] `ProviderValidator` class fully implemented in `gao_dev/cli/provider_validator.py`:
  - [ ] `validate_configuration()` - validates full provider config
  - [ ] `check_cli_available()` - checks if CLI in PATH (async)
  - [ ] `check_ollama_models()` - lists available Ollama models (async)
  - [ ] `suggest_fixes()` - provides installation/fix suggestions
  - [ ] `_check_cli_windows()` - Windows-specific CLI detection
  - [ ] `_check_cli_unix()` - Unix/macOS CLI detection
  - [ ] `_parse_ollama_output()` - parses `ollama list` output
- [ ] CLI detection works cross-platform:
  - [ ] Unix/macOS: Uses `shutil.which()` or `which` command
  - [ ] Windows: Uses `where` command with `shell=True`
  - [ ] Handles missing CLIs gracefully (returns False, not crash)
  - [ ] Timeout for CLI checks: 5 seconds
- [ ] Ollama model detection (CRAAP Moderate Resolution):
  - [ ] Runs `ollama list` command asynchronously
  - [ ] Parses output to extract model names and sizes
  - [ ] Returns empty list if Ollama not available (not error)
  - [ ] **Timeout increased to 10 seconds** (was 3s in original)
  - [ ] Shows user feedback: "[dim]Detecting Ollama models (may take a moment)...[/dim]"
  - [ ] Handles slow disks (HDD, NAS) gracefully
  - [ ] Handles first-time Ollama daemon startup
- [ ] Validation checks:
  - [ ] Provider exists in ProviderFactory registry
  - [ ] CLI available (if CLI-based provider: claude-code, opencode)
  - [ ] API key set (if direct API provider: anthropic, openai, google)
  - [ ] Model supported by provider (validate against known models)
  - [ ] Basic connectivity test (optional, can be slow - make skippable)
- [ ] Actionable error messages:
  - [ ] "Claude Code CLI not found. Install: `npm install -g @anthropic/claude-code`"
  - [ ] "OpenCode CLI not found. Install: `npm install -g opencode`"
  - [ ] "ANTHROPIC_API_KEY not set. Export: `export ANTHROPIC_API_KEY=sk-ant-...`"
  - [ ] "Model 'xyz' not supported. Available models: [list]"
  - [ ] "Ollama not found. Install: https://ollama.ai"
- [ ] `ValidationResult` dataclass with:
  - [ ] `success: bool` - overall validation result
  - [ ] `provider_name: str` - provider being validated
  - [ ] `messages: List[str]` - informational messages
  - [ ] `warnings: List[str]` - non-critical warnings
  - [ ] `suggestions: List[str]` - actionable fix suggestions
  - [ ] `validation_time_ms: float` - how long validation took
- [ ] Async implementation for performance:
  - [ ] All CLI checks are async (use `asyncio.create_subprocess_exec`)
  - [ ] All file I/O is async where possible
  - [ ] Timeouts on all async operations (prevent hanging)
- [ ] Comprehensive test coverage (>90%):
  - [ ] Mock subprocess calls (no real CLI execution)
  - [ ] All provider types tested (claude-code, opencode, direct-api)
  - [ ] CLI available/unavailable scenarios
  - [ ] Ollama detection tests (available, unavailable, timeout)
  - [ ] Suggestion tests (all error scenarios)
  - [ ] Cross-platform tests (Windows, Unix)
- [ ] Type hints throughout, MyPy passes strict mode

---

## Tasks

- [ ] Implement CLI detection (cross-platform)
  - [ ] `_check_cli_unix()` using `shutil.which()`
  - [ ] `_check_cli_windows()` using `where` command
  - [ ] Handle platform differences gracefully
  - [ ] Add 5-second timeout
- [ ] Implement Ollama model detection
  - [ ] Run `ollama list` asynchronously
  - [ ] Parse output (format: "NAME    SIZE    MODIFIED")
  - [ ] Extract model names
  - [ ] Handle case where Ollama not installed
  - [ ] **Set timeout to 10 seconds** (CRAAP resolution)
  - [ ] Log detection start/end with timing
- [ ] Implement validation logic
  - [ ] Check provider exists in ProviderFactory
  - [ ] Dispatch to appropriate validator (CLI vs API)
  - [ ] Collect all validation errors
  - [ ] Generate suggestions based on errors
- [ ] Create suggestion messages
  - [ ] Map error types to actionable suggestions
  - [ ] Include installation commands
  - [ ] Include documentation links
- [ ] Write 15+ unit tests
  - [ ] Mock all subprocess calls
  - [ ] Test all provider types
  - [ ] Test all error scenarios
  - [ ] Test suggestion generation
- [ ] Add integration tests
  - [ ] Real CLI detection (optional, can be slow)
  - [ ] Real Ollama detection (if available)
- [ ] Add structlog logging
  - [ ] Info: validation started/completed
  - [ ] Warning: validation failures
  - [ ] Debug: CLI detection details
- [ ] Run MyPy and fix issues
  - [ ] `mypy gao_dev/cli/provider_validator.py --strict`

---

## Test Cases

```python
# CLI detection
async def test_validate_claude_code_available():
    """Claude Code validation passes when CLI available."""
    # Mock shutil.which() to return path
    # Call validate_configuration()
    # Assert success=True

async def test_validate_claude_code_missing():
    """Claude Code validation fails when CLI missing."""
    # Mock shutil.which() to return None
    # Call validate_configuration()
    # Assert success=False
    # Assert suggestion includes installation command

async def test_validate_opencode_available():
    """OpenCode validation passes when CLI available."""
    # Mock subprocess to return success
    # Call validate_configuration()
    # Assert success=True

# Direct API validation
async def test_validate_direct_api_with_key():
    """Direct API validation passes with API key."""
    # Mock os.environ to include ANTHROPIC_API_KEY
    # Call validate_configuration()
    # Assert success=True

async def test_validate_direct_api_no_key():
    """Direct API validation fails without API key."""
    # Mock os.environ to not include key
    # Call validate_configuration()
    # Assert success=False
    # Assert suggestion includes export command

# CLI detection
async def test_check_cli_available():
    """CLI detection works cross-platform."""
    # Mock subprocess for current platform
    # Call check_cli_available('opencode')
    # Assert returns True

async def test_check_cli_timeout():
    """CLI check times out after 5 seconds."""
    # Mock subprocess to hang
    # Call check_cli_available()
    # Assert returns False after 5s
    # Assert timeout warning logged

# Ollama detection (CRAAP Resolution)
async def test_check_ollama_models():
    """Ollama model detection parses output correctly."""
    # Mock subprocess to return sample output
    # Call check_ollama_models()
    # Assert model names extracted correctly

async def test_check_ollama_not_available():
    """Ollama unavailable returns empty list."""
    # Mock subprocess to raise FileNotFoundError
    # Call check_ollama_models()
    # Assert returns []

async def test_check_ollama_timeout_10s():
    """Ollama detection times out after 10 seconds."""
    # Mock subprocess to hang
    # Call check_ollama_models()
    # Assert returns [] after 10s
    # Assert timeout warning logged

async def test_check_ollama_slow_disk():
    """Ollama detection handles slow disks gracefully."""
    # Mock subprocess with 8-second delay
    # Call check_ollama_models()
    # Assert completes successfully (within 10s timeout)

# Suggestions
def test_suggest_fixes_claude_code():
    """Suggestions provided for Claude Code installation."""
    # Create ValidationResult with CLI not found error
    # Call suggest_fixes()
    # Assert suggestions include npm install command

def test_suggest_fixes_opencode():
    """Suggestions provided for OpenCode installation."""
    # Create ValidationResult with CLI not found error
    # Call suggest_fixes()
    # Assert suggestions include installation link

def test_suggest_fixes_api_key():
    """Suggestions provided for missing API key."""
    # Create ValidationResult with missing key error
    # Call suggest_fixes()
    # Assert suggestions include export command

# Cross-platform
async def test_cli_detection_windows():
    """CLI detection works on Windows."""
    # Mock platform.system() to return 'Windows'
    # Mock subprocess 'where' command
    # Call check_cli_available()
    # Assert uses 'where' command with shell=True

async def test_cli_detection_unix():
    """CLI detection works on Unix/macOS."""
    # Mock platform.system() to return 'Linux'
    # Mock shutil.which()
    # Call check_cli_available()
    # Assert uses shutil.which()
```

---

## Definition of Done

- [ ] All methods implemented and working
- [ ] Ollama timeout increased to 10 seconds (CRAAP resolution)
- [ ] 15+ tests passing, >90% coverage
- [ ] Cross-platform validation (Windows + Unix)
- [ ] MyPy passes strict mode
- [ ] Documentation complete (docstrings)
- [ ] Code reviewed
- [ ] Commit message: `feat(epic-35): Story 35.3 - ProviderValidator Implementation (5 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Ollama Timeout Increased (CRAAP Moderate - Issue #3)**:
- **Risk**: 3-second timeout too short for:
  - Large model collections (20+ models)
  - Slow disks (HDD, NAS)
  - First-time Ollama daemon startup
- **Mitigation**:
  - Timeout increased from 3s to 10s
  - User feedback: "Detecting Ollama models (may take a moment)..."
  - Graceful handling if timeout still exceeded (return empty list)
- **Testing**: Test with slow subprocess mock (8s delay)

**Windows-Specific Challenges (CRAAP Moderate - Issue #2)**:
- **Risk**: CLI detection differs on Windows
- **Mitigation**:
  - Separate `_check_cli_windows()` and `_check_cli_unix()` methods
  - Windows uses `where` command with `shell=True`
  - Unix uses `shutil.which()` (more reliable)
  - Handle path separators (`\` vs `/`)
- **Testing**: Mock platform detection, test both paths

### CLI Detection Implementation

**Unix/macOS**:
```python
import shutil

def _check_cli_unix(self, cli_name: str) -> bool:
    return shutil.which(cli_name) is not None
```

**Windows**:
```python
import subprocess

async def _check_cli_windows(self, cli_name: str) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            'where', cli_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True  # Required on Windows
        )
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        return proc.returncode == 0
    except (asyncio.TimeoutError, Exception):
        return False
```

### Ollama Output Parsing

**Example `ollama list` output**:
```
NAME                    ID              SIZE      MODIFIED
deepseek-r1:latest      abc123          3.8 GB    2 days ago
llama2:latest           def456          3.8 GB    1 week ago
codellama:13b           ghi789          6.7 GB    2 weeks ago
```

**Parsing Logic**:
- Skip header line
- Split by whitespace
- Extract first column (NAME)
- Remove `:latest` suffix if present
- Return list of model names

### Validation Flow

1. Check if provider exists in ProviderFactory registry
2. If CLI-based (claude-code, opencode):
   - Check CLI available with platform-specific method
   - If not available, add error + suggestion
3. If Direct API (anthropic, openai, google):
   - Check API key environment variable
   - If not set, add error + suggestion
4. If OpenCode + local:
   - Check Ollama available
   - If available, list models with 10s timeout
   - If not available, add error + suggestion
5. Collect all errors, warnings, suggestions
6. Return ValidationResult

### Performance Targets

- CLI check: <2 seconds (with 5s timeout)
- Ollama check: <5 seconds typical, <10s worst case
- Full validation: <3 seconds typical
- Log validation timing for monitoring

### Dependencies for Next Stories

After this story completes:
- Story 35.5 (ProviderSelector) can integrate ProviderValidator
- Can be developed in parallel with Story 35.2 (PreferenceManager)

---

**Story Status**: Todo
**Next Action**: Begin implementation after Story 35.1 completes (can be parallel with 35.2)
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
