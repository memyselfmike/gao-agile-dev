# Epic 35: Interactive Provider Selection at Startup

**Status**: Planning
**Owner**: Amelia (Software Developer)
**Created**: 2025-01-12
**Target Duration**: 1 week (40-50 hours)

---

## Epic Goal

Add interactive provider selection to the Brian REPL startup flow, enabling users to choose their AI provider (Claude Code, OpenCode, local models) through clear prompts with preference persistence and zero regressions.

---

## Success Criteria

- ✅ Interactive prompts work on first-time startup
- ✅ Saved preferences reused on subsequent startups
- ✅ All existing tests pass (no regressions)
- ✅ >90% test coverage for new code
- ✅ Works on Windows, macOS, Linux
- ✅ Selection flow completes in <30 seconds
- ✅ Clear error messages with actionable suggestions

---

## Stories Breakdown

### Phase 1: Foundation (Stories 35.1-35.3)

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| 35.1 | Project Setup & Architecture | 2 | None |
| 35.2 | PreferenceManager Implementation | 5 | 35.1 |
| 35.3 | ProviderValidator Implementation | 5 | 35.1 |

**Phase 1 Total**: 12 points (~12-16 hours)

### Phase 2: UI & Integration (Stories 35.4-35.5)

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| 35.4 | InteractivePrompter Implementation | 8 | 35.1 |
| 35.5 | ProviderSelector Implementation | 5 | 35.2, 35.3, 35.4 |
| 35.6 | ChatREPL Integration | 3 | 35.5 |

**Phase 2 Total**: 16 points (~16-20 hours)

### Phase 3: Testing & Polish (Stories 35.7-35.8)

| Story | Title | Points | Dependencies |
|-------|-------|--------|--------------|
| 35.7 | Comprehensive Testing & Regression Validation | 8 | 35.6 |
| 35.8 | Documentation & Examples | 3 | 35.7 |

**Phase 3 Total**: 11 points (~11-14 hours)

---

## Epic Total: 39 Story Points (~40-50 hours)

---

## Story Details

---

## Story 35.1: Project Setup & Architecture

**Title**: Project Setup & Architecture
**Points**: 2
**Owner**: Amelia
**Dependencies**: None
**Priority**: P0

### Description

Create foundational structure for Epic 35 including directory structure, base classes, exceptions, and data models. This establishes the architecture for all subsequent stories.

### Acceptance Criteria

1. ✅ Feature directory created: `docs/features/interactive-provider-selection/`
2. ✅ PRD, ARCHITECTURE, and epic breakdown documents created
3. ✅ New module structure created:
   - `gao_dev/cli/provider_selector.py` (stub)
   - `gao_dev/cli/interactive_prompter.py` (stub)
   - `gao_dev/cli/preference_manager.py` (stub)
   - `gao_dev/cli/provider_validator.py` (stub)
4. ✅ Exception classes defined in `gao_dev/cli/exceptions.py`:
   - `ProviderSelectionError`
   - `ProviderSelectionCancelled`
   - `ProviderValidationFailed`
   - `PreferenceSaveError`
   - `PreferenceLoadError`
5. ✅ Data models defined in `gao_dev/cli/models.py`:
   - `ProviderConfig`
   - `ProviderPreferences`
   - `ValidationResult`
6. ✅ Test structure created:
   - `tests/cli/test_provider_selector.py` (stub)
   - `tests/cli/test_interactive_prompter.py` (stub)
   - `tests/cli/test_preference_manager.py` (stub)
   - `tests/cli/test_provider_validator.py` (stub)
7. ✅ All stubs have docstrings and type hints
8. ✅ Import structure validated (no circular dependencies)

### Tasks

- [ ] Create feature directory and documentation
- [ ] Create module stubs with class definitions
- [ ] Define exception hierarchy
- [ ] Define data models with dataclasses
- [ ] Create test file stubs
- [ ] Validate imports and type hints
- [ ] Run mypy to ensure type safety

### Definition of Done

- [ ] All files created and committed
- [ ] Mypy passes with no errors
- [ ] Documentation reviewed and approved
- [ ] Test stubs created

---

## Story 35.2: PreferenceManager Implementation

**Title**: PreferenceManager Implementation
**Points**: 5
**Owner**: Amelia
**Dependencies**: 35.1
**Priority**: P0

### Description

Implement `PreferenceManager` class for loading and saving provider preferences to `.gao-dev/provider_preferences.yaml` with validation, error handling, and sensible defaults.

### Acceptance Criteria

1. ✅ `PreferenceManager` class fully implemented with all methods:
   - `load_preferences()` - loads from YAML, returns None if invalid
   - `save_preferences()` - saves to YAML with proper formatting
   - `has_preferences()` - checks if valid file exists
   - `get_default_preferences()` - returns claude-code defaults
   - `validate_preferences()` - validates structure and values
   - `delete_preferences()` - removes file (for testing)
2. ✅ YAML format validated against schema:
   - Required keys: version, provider, metadata
   - Version format validation (semantic versioning)
   - Timestamp format validation (ISO 8601)
3. ✅ File permissions set correctly:
   - Preferences file: 0600 (user read/write only)
   - `.gao-dev/` directory: 0700 (user only)
4. ✅ Error handling for all edge cases:
   - Missing file → returns None, doesn't crash
   - Corrupt YAML → logs warning, returns None
   - Missing fields → logs warning, returns None
   - Permission denied → raises PreferenceSaveError with clear message
5. ✅ **SECURITY: YAML injection prevention** (CRAAP Resolution):
   - Use `yaml.safe_dump()` instead of `yaml.dump()` for all saves
   - Implement input sanitization for all string values before saving
   - Only allow alphanumeric, dash, underscore, dot, slash, colon, space characters
   - Sanitization method: `_sanitize_string()` and `_sanitize_dict()`
6. ✅ Comprehensive test coverage (>95%):
   - Unit tests with temp directories
   - Valid preferences load/save round-trip
   - Invalid YAML handling
   - Missing fields handling
   - Corrupt file handling
   - Permission error handling
   - Default preferences test
   - **Security tests with malicious input** (YAML injection attempts)
7. ✅ Logging with structlog:
   - Info level: successful load/save
   - Warning level: invalid preferences, using defaults
   - Error level: save failures
8. ✅ Type hints throughout, mypy passes strict mode

### Tasks

- [ ] Implement `load_preferences()` with YAML parsing
- [ ] Implement `save_preferences()` with atomic write
- [ ] Implement validation logic
- [ ] Add proper error handling
- [ ] Set file permissions correctly
- [ ] Write 20+ unit tests
- [ ] Add structlog logging
- [ ] Run mypy and fix any issues

### Test Cases

```python
def test_load_valid_preferences():
    """Load valid preferences from file."""

def test_load_missing_file():
    """Missing file returns None, doesn't crash."""

def test_load_corrupt_yaml():
    """Corrupt YAML returns None, logs warning."""

def test_save_preferences():
    """Save preferences to file with correct format."""

def test_save_creates_directory():
    """.gao-dev/ directory created if missing."""

def test_save_permission_error():
    """Permission error raises PreferenceSaveError."""

def test_validate_valid_preferences():
    """Valid preferences pass validation."""

def test_validate_missing_fields():
    """Missing required fields fail validation."""

def test_validate_invalid_types():
    """Invalid field types fail validation."""

def test_default_preferences():
    """Default preferences are valid."""

def test_round_trip():
    """Save then load produces identical dict."""
```

### Definition of Done

- [ ] All methods implemented and working
- [ ] 20+ tests passing, >95% coverage
- [ ] Mypy passes strict mode
- [ ] Documentation complete
- [ ] Code reviewed

---

## Story 35.3: ProviderValidator Implementation

**Title**: ProviderValidator Implementation
**Points**: 5
**Owner**: Amelia
**Dependencies**: 35.1
**Priority**: P0

### Description

Implement `ProviderValidator` class for validating provider configurations, checking CLI availability, and providing actionable error messages and fix suggestions.

### Acceptance Criteria

1. ✅ `ProviderValidator` class fully implemented:
   - `validate_configuration()` - validates full provider config
   - `check_cli_available()` - checks if CLI in PATH
   - `check_ollama_models()` - lists available Ollama models
   - `suggest_fixes()` - provides installation/fix suggestions
2. ✅ CLI detection works cross-platform:
   - Uses `shutil.which()` for Unix/macOS
   - Uses `where` command for Windows
   - Handles missing CLIs gracefully
3. ✅ Ollama model detection:
   - Runs `ollama list` command
   - Parses output to extract model names
   - Returns empty list if Ollama not available
   - Timeout after 3 seconds
4. ✅ Validation checks:
   - Provider exists in ProviderFactory registry
   - CLI available (if CLI-based provider)
   - API key set (if direct API provider)
   - Model supported by provider
   - Basic connectivity test (optional, can be slow)
5. ✅ Actionable error messages:
   - "Claude Code CLI not found. Install: <command>"
   - "ANTHROPIC_API_KEY not set. Export: export ANTHROPIC_API_KEY=sk-..."
   - "Model 'xyz' not supported. Available: [list]"
6. ✅ `ValidationResult` dataclass with:
   - `success: bool`
   - `provider_name: str`
   - `messages: List[str]`
   - `warnings: List[str]`
   - `suggestions: List[str]`
7. ✅ Async implementation for performance
8. ✅ Comprehensive test coverage (>90%):
   - Mock subprocess calls
   - All provider types tested
   - CLI available/unavailable scenarios
   - Ollama detection tests
   - Suggestion tests
9. ✅ Type hints throughout, mypy passes

### Tasks

- [ ] Implement CLI detection (cross-platform)
- [ ] Implement Ollama model detection
- [ ] Implement validation logic
- [ ] Create suggestion messages
- [ ] Write 15+ unit tests
- [ ] Add integration tests
- [ ] Add structlog logging
- [ ] Run mypy and fix issues

### Test Cases

```python
async def test_validate_claude_code_available():
    """Claude Code validation passes when CLI available."""

async def test_validate_claude_code_missing():
    """Claude Code validation fails when CLI missing."""

async def test_validate_opencode_available():
    """OpenCode validation passes when CLI available."""

async def test_validate_direct_api_with_key():
    """Direct API validation passes with API key."""

async def test_validate_direct_api_no_key():
    """Direct API validation fails without API key."""

async def test_check_cli_available():
    """CLI detection works cross-platform."""

async def test_check_ollama_models():
    """Ollama model detection parses output correctly."""

async def test_check_ollama_not_available():
    """Ollama unavailable returns empty list."""

def test_suggest_fixes_claude_code():
    """Suggestions provided for Claude Code installation."""

def test_suggest_fixes_opencode():
    """Suggestions provided for OpenCode installation."""
```

### Definition of Done

- [ ] All methods implemented and working
- [ ] 15+ tests passing, >90% coverage
- [ ] Mypy passes strict mode
- [ ] Cross-platform testing (Windows + Unix)
- [ ] Documentation complete
- [ ] Code reviewed

---

## Story 35.4: InteractivePrompter Implementation

**Title**: InteractivePrompter Implementation
**Points**: 8
**Owner**: Amelia
**Dependencies**: 35.1
**Priority**: P0

### Description

Implement `InteractivePrompter` class for user interaction using Rich and prompt_toolkit, providing beautiful formatted tables and clear prompts for provider and model selection.

### Acceptance Criteria

1. ✅ `InteractivePrompter` class fully implemented:
   - `prompt_provider()` - shows provider table, gets selection
   - `prompt_opencode_config()` - OpenCode-specific prompts
   - `prompt_model()` - shows model table, gets selection
   - `prompt_save_preferences()` - asks about saving
   - `prompt_use_saved()` - asks about using saved config
   - `show_error()` - displays error panel with suggestions
   - `show_success()` - displays success message
2. ✅ **CI/CD Compatibility: Lazy import pattern** (CRAAP Resolution):
   - Import `prompt_toolkit` and `rich.prompt` lazily inside methods, not at module level
   - Catch `ImportError` and `OSError` (no TTY) and fall back to `input()`
   - Ensures headless CI/CD environments don't break
   - Example pattern:
     ```python
     def prompt_provider(self):
         try:
             from prompt_toolkit import PromptSession
             # Use PromptSession
         except (ImportError, OSError):
             # Fallback to input()
             return input("Select provider [1/2/3]: ")
     ```
3. ✅ Rich formatting:
   - Tables with styled columns (cyan headers, green data)
   - Panels for errors/success with appropriate colors
   - Clear descriptions for each option
4. ✅ Input validation:
   - Only accept valid choices (1/2/3 for providers)
   - Handle invalid input gracefully (re-prompt)
   - Default values provided (press Enter for default)
5. ✅ Keyboard shortcuts:
   - Enter → accept default
   - Ctrl+C → cancel (raises KeyboardInterrupt)
   - Arrow keys → navigate history
6. ✅ OpenCode-specific flow:
   - "Use local model (Ollama)?" [y/N]
   - If no: "Cloud AI provider?" [anthropic/openai/google]
   - If yes: Continue to Ollama model selection
7. ✅ Model selection enhancements:
   - Show model descriptions/sizes if available
   - Highlight recommended models
   - Group models by provider if multiple
8. ✅ Error display with suggestions:
   - Error panel in red
   - Bullet-pointed suggestions
   - "Try again?" prompt
9. ✅ Comprehensive test coverage (>85%):
   - Mock Rich components
   - Mock user input
   - Test all prompt paths
   - Test error handling
   - **Test lazy import fallback** (simulate headless environment)
10. ✅ Type hints throughout, mypy passes

### Tasks

- [ ] Implement provider prompt with table
- [ ] Implement model prompt with table
- [ ] Implement OpenCode-specific prompts
- [ ] Implement error/success displays
- [ ] Add input validation
- [ ] Write 25+ unit tests
- [ ] Add integration tests with mocked input
- [ ] Test keyboard shortcuts
- [ ] Run mypy and fix issues

### Test Cases

```python
def test_prompt_provider_valid_choice():
    """Valid provider choice returns provider name."""

def test_prompt_provider_invalid_then_valid():
    """Invalid choice re-prompts, then accepts valid."""

def test_prompt_provider_default():
    """Empty input uses default (1)."""

def test_prompt_provider_ctrl_c():
    """Ctrl+C raises KeyboardInterrupt."""

def test_prompt_opencode_local():
    """OpenCode local model config returned."""

def test_prompt_opencode_cloud():
    """OpenCode cloud config returned."""

def test_prompt_model_valid():
    """Valid model choice returns model name."""

def test_prompt_save_yes():
    """'y' returns True."""

def test_prompt_save_no():
    """'n' returns False."""

def test_prompt_use_saved_yes():
    """'y' returns 'y'."""

def test_prompt_use_saved_change():
    """'c' returns 'c'."""

def test_show_error():
    """Error panel displayed with suggestions."""

def test_show_success():
    """Success message displayed."""
```

### Definition of Done

- [ ] All methods implemented and working
- [ ] 25+ tests passing, >85% coverage
- [ ] Manual testing of UI (screenshots)
- [ ] Mypy passes strict mode
- [ ] Documentation complete
- [ ] Code reviewed

---

## Story 35.5: ProviderSelector Implementation

**Title**: ProviderSelector Implementation
**Points**: 5
**Owner**: Amelia
**Dependencies**: 35.2, 35.3, 35.4
**Priority**: P0

### Description

Implement `ProviderSelector` orchestrator class that coordinates all components (PreferenceManager, InteractivePrompter, ProviderValidator) to determine which provider configuration to use based on environment variables, saved preferences, or interactive prompts.

### Acceptance Criteria

1. ✅ `ProviderSelector` class fully implemented:
   - `select_provider()` - main orchestration method
   - `has_saved_preferences()` - check for saved prefs
   - `use_environment_variable()` - check AGENT_PROVIDER env var
2. ✅ Priority order enforced:
   1. Environment variable (AGENT_PROVIDER)
   2. Saved preferences (if exist and user confirms)
   3. Interactive prompts
   4. Hardcoded defaults (last resort)
3. ✅ Validation integrated:
   - Validate selected provider before returning
   - Show error if validation fails
   - Prompt for different provider on failure
   - Allow retry or cancel
4. ✅ Dependency injection support:
   - Constructor accepts optional dependencies for testing
   - Creates real instances if not provided
5. ✅ Error handling:
   - `ProviderSelectionCancelled` on Ctrl+C
   - `ProviderValidationFailed` if no valid provider found
   - Clear error messages at each step
6. ✅ Logging with structlog:
   - Info: provider selection source (env/saved/interactive)
   - Warning: validation failures
   - Debug: each step in decision tree
7. ✅ Comprehensive test coverage (>90%):
   - Unit tests with mocked dependencies
   - Integration tests with real dependencies
   - All decision paths tested
   - Error scenarios tested
8. ✅ Type hints throughout, mypy passes

### Tasks

- [ ] Implement decision tree logic
- [ ] Integrate all three components
- [ ] Add validation loop
- [ ] Add error handling
- [ ] Write 10+ unit tests
- [ ] Write 10+ integration tests
- [ ] Add structlog logging
- [ ] Run mypy and fix issues

### Test Cases

```python
def test_select_provider_env_var():
    """Environment variable bypasses prompts."""

def test_select_provider_saved_accepted():
    """Saved preferences used when accepted."""

def test_select_provider_saved_rejected():
    """Interactive prompts when saved rejected."""

def test_select_provider_no_saved():
    """Interactive prompts when no saved prefs."""

def test_select_provider_validation_fails():
    """Prompt for different provider on validation failure."""

def test_select_provider_cancelled():
    """Ctrl+C raises ProviderSelectionCancelled."""

def test_has_saved_preferences():
    """Correctly detects saved preferences."""

def test_use_environment_variable():
    """Correctly extracts config from env var."""

def test_select_provider_saves_preferences():
    """Preferences saved when user agrees."""

def test_select_provider_no_save():
    """Preferences not saved when user declines."""
```

### Definition of Done

- [ ] All methods implemented and working
- [ ] 20+ tests passing, >90% coverage
- [ ] Integration tests with real components
- [ ] Mypy passes strict mode
- [ ] Documentation complete
- [ ] Code reviewed

---

## Story 35.6: ChatREPL Integration

**Title**: ChatREPL Integration
**Points**: 3
**Owner**: Amelia
**Dependencies**: 35.5
**Priority**: P0

### Description

Integrate `ProviderSelector` into `ChatREPL.__init__()` to enable interactive provider selection at startup while maintaining backward compatibility with existing configurations and environment variables.

### Acceptance Criteria

1. ✅ `ChatREPL.__init__()` modified to use `ProviderSelector`:
   - Create `ProviderSelector` instance
   - Call `select_provider()` to get config
   - Pass config to `ProcessExecutor`
   - Handle `ProviderSelectionCancelled` gracefully
2. ✅ Backward compatibility maintained:
   - Existing env vars still work (AGENT_PROVIDER)
   - Existing ProcessExecutor calls unchanged
   - No breaking changes to API
3. ✅ Error handling:
   - Ctrl+C during selection → exit gracefully with message
   - Validation failures → clear error, exit gracefully
   - No crashes under any circumstance
4. ✅ User experience:
   - Selection happens before greeting
   - Clear message if using env var
   - Clear message if using saved prefs
   - Smooth transition to normal REPL
5. ✅ Minimal code changes:
   - ~10-15 lines added to `__init__`
   - No changes to existing methods
   - No changes to other files
6. ✅ All existing tests still pass:
   - ChatREPL unit tests
   - ChatREPL integration tests
   - End-to-end REPL tests
7. ✅ New integration tests added:
   - Test with env var set
   - Test with saved preferences
   - Test first-time startup
   - Test cancellation

### Tasks

- [ ] Add ProviderSelector to ChatREPL imports
- [ ] Modify `__init__` to call select_provider()
- [ ] Add error handling for cancellation
- [ ] Test with existing test suite
- [ ] Write 5+ integration tests
- [ ] Update ChatREPL documentation
- [ ] Manual testing of full flow

### Test Cases

```python
def test_chatrepl_with_env_var():
    """ChatREPL uses env var without prompts."""

def test_chatrepl_with_saved_prefs():
    """ChatREPL prompts to use saved prefs."""

def test_chatrepl_first_time():
    """ChatREPL shows interactive prompts."""

def test_chatrepl_cancellation():
    """Ctrl+C during selection exits gracefully."""

def test_chatrepl_validation_failure():
    """Validation failure exits gracefully."""
```

### Definition of Done

- [ ] ChatREPL modified and working
- [ ] All existing tests pass (0 regressions)
- [ ] 5+ new integration tests passing
- [ ] Manual testing complete
- [ ] Documentation updated
- [ ] Code reviewed

---

## Story 35.7: Comprehensive Testing & Regression Validation

**Title**: Comprehensive Testing & Regression Validation
**Points**: 8
**Owner**: Amelia
**Dependencies**: 35.6
**Priority**: P0

### Description

Create comprehensive test suite including unit, integration, end-to-end, and regression tests to ensure >90% coverage for new code and zero regressions in existing functionality.

### Acceptance Criteria

1. ✅ Test coverage targets met:
   - Overall project coverage: no decrease
   - New code coverage: >90%
   - PreferenceManager: >95%
   - ProviderValidator: >90%
   - InteractivePrompter: >85%
   - ProviderSelector: >90%
   - ChatREPL integration: >80%
2. ✅ Regression test suite created:
   - File: `tests/regression/test_epic35_no_regressions.py`
   - 20+ regression tests covering:
     - Environment variables still work
     - ProcessExecutor backward compatible
     - All existing CLI commands work
     - Config files still work
     - All agent workflows unchanged
3. ✅ End-to-end test scenarios:
   - First-time startup flow
   - Returning user flow
   - Environment variable bypass
   - Validation failure recovery
   - Preference save/load round-trip
4. ✅ Cross-platform testing:
   - Tests pass on Windows
   - Tests pass on macOS (if available)
   - Tests pass on Linux (via CI)
5. ✅ Performance testing:
   - Preference loading <100ms
   - Provider validation <2s
   - Full selection flow <30s (simulated)
6. ✅ Error scenario testing:
   - Corrupt preference files
   - Missing CLIs
   - Invalid configurations
   - Network failures (for validation)
   - Permission errors
7. ✅ **Security testing** (CRAAP Resolution):
   - Test YAML injection attempts with malicious input
   - Verify `yaml.safe_dump()` prevents code execution
   - Test input sanitization rejects dangerous characters
   - Test with special characters, newlines, YAML tags, anchors
8. ✅ **CI/CD headless environment testing** (CRAAP Resolution):
   - Test in Docker container without TTY
   - Verify lazy import fallback works (prompt_toolkit unavailable)
   - Ensure env var bypass works in headless mode
   - Add GitHub Actions job for headless testing
9. ✅ CI/CD integration:
   - All tests run in GitHub Actions
   - Coverage report generated
   - No test failures allowed
   - Headless environment test job included
10. ✅ Test documentation:
   - README in tests/cli/ explaining structure
   - Comments in all test files
   - Instructions for running tests

### Tasks

- [ ] Write regression test suite (20+ tests)
- [ ] Write end-to-end tests (5+ scenarios)
- [ ] Cross-platform testing
- [ ] Performance testing
- [ ] Error scenario testing
- [ ] **Write security tests** (YAML injection, input sanitization)
- [ ] **Write CI/CD headless tests** (Docker, no TTY, lazy import fallback)
- [ ] Run full test suite and fix failures
- [ ] Generate coverage report
- [ ] Document test structure

### Test Suites

**Regression Tests** (`tests/regression/test_epic35_no_regressions.py`):
```python
class TestEpic35NoRegressions:
    def test_env_var_still_works()
    def test_chatrepl_backward_compatible()
    def test_processexecutor_unchanged()
    def test_all_cli_commands_work()
    def test_existing_configs_work()
    def test_brian_orchestrator_unchanged()
    def test_conversational_brian_unchanged()
    def test_command_router_unchanged()
    def test_session_state_unchanged()
    def test_existing_workflows_work()
    # ... 10+ more
```

**End-to-End Tests** (`tests/e2e/test_provider_selection_e2e.py`):
```python
class TestProviderSelectionE2E:
    async def test_first_time_startup_flow()
    async def test_returning_user_flow()
    async def test_env_var_bypass_flow()
    async def test_validation_failure_recovery()
    async def test_preference_save_load_round_trip()
```

**Performance Tests** (`tests/performance/test_provider_selection_performance.py`):
```python
class TestProviderSelectionPerformance:
    def test_preference_loading_fast()
    def test_validation_fast()
    def test_selection_flow_fast()
```

### Definition of Done

- [ ] 100+ total tests passing
- [ ] >90% coverage for new code
- [ ] 0 regressions detected
- [ ] Cross-platform validation
- [ ] Performance targets met
- [ ] CI/CD passing
- [ ] Test documentation complete

---

## Story 35.8: Documentation & Examples

**Title**: Documentation & Examples
**Points**: 3
**Owner**: Amelia
**Dependencies**: 35.7
**Priority**: P0

### Description

Create comprehensive user and developer documentation including user guide, API reference, FAQ, testing guide, and examples demonstrating all features and common use cases.

### Acceptance Criteria

1. ✅ User documentation created:
   - **USER_GUIDE.md**: Step-by-step guide with screenshots
   - **FAQ.md**: 15+ common questions answered
   - **TROUBLESHOOTING.md**: Common issues and solutions
2. ✅ Developer documentation created:
   - **API_REFERENCE.md**: All classes, methods, parameters
   - **TESTING.md**: How to run/add tests
   - **INTEGRATION_GUIDE.md**: How to integrate new provider types
3. ✅ Examples created:
   - `examples/provider-selection/first-time-setup.md`
   - `examples/provider-selection/change-provider.md`
   - `examples/provider-selection/local-models.md`
   - `examples/provider-selection/ci-cd-usage.md`
4. ✅ README.md updated:
   - Feature overview section added
   - Link to full documentation
   - Quick start example
5. ✅ CLAUDE.md updated:
   - Epic 35 marked complete
   - Provider selection mentioned in workflow
6. ✅ Changelog entry added:
   - `docs/CHANGELOG.md` updated with Epic 35
7. ✅ All documentation reviewed:
   - No typos or formatting issues
   - All links work
   - Code examples are correct
8. ✅ Screenshots/recordings:
   - GIF showing first-time flow
   - GIF showing returning user flow
   - Screenshots of error messages

### Tasks

- [ ] Write USER_GUIDE.md
- [ ] Write FAQ.md
- [ ] Write API_REFERENCE.md
- [ ] Write TESTING.md
- [ ] Create examples
- [ ] Update README.md
- [ ] Update CLAUDE.md
- [ ] Create screenshots/GIFs
- [ ] Review all documentation

### Documentation Structure

```
docs/features/interactive-provider-selection/
├── PRD.md                    (Already created)
├── ARCHITECTURE.md           (Already created)
├── EPIC-35.md               (This file)
├── USER_GUIDE.md            (NEW)
├── FAQ.md                   (NEW)
├── API_REFERENCE.md         (NEW)
├── TESTING.md               (NEW)
├── TROUBLESHOOTING.md       (NEW)
├── INTEGRATION_GUIDE.md     (NEW)
├── README.md                (NEW - feature overview)
└── examples/
    ├── first-time-setup.md
    ├── change-provider.md
    ├── local-models.md
    └── ci-cd-usage.md
```

### Definition of Done

- [ ] All documentation files created
- [ ] All examples working and tested
- [ ] Screenshots/GIFs created
- [ ] README and CLAUDE.md updated
- [ ] Documentation reviewed and approved
- [ ] No broken links or formatting issues

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaks existing configs | **High** | Low | Extensive regression testing (Story 35.7) |
| User confusion | Medium | Medium | Clear prompts, good defaults, FAQ |
| Cross-platform issues | Medium | Low | Test on all platforms (Story 35.7) |
| Performance issues | Low | Low | Performance testing, caching |
| Test complexity | Medium | Medium | Mock everything, clear test structure |

---

## Dependencies

### Internal Dependencies
- ✅ Epic 30 (Interactive Brian Chat) - Complete
- ✅ Epic 21 (AI Analysis Service) - Complete
- ✅ Provider abstraction system - Complete

### External Dependencies
- ✅ `rich` library - Already installed
- ✅ `prompt_toolkit` - Already installed
- ✅ `pyyaml` - Already installed

---

## Timeline

**Week 1 (40-50 hours)**:
- **Days 1-2**: Stories 35.1-35.3 (Foundation)
- **Days 3-4**: Stories 35.4-35.6 (UI & Integration)
- **Day 5**: Stories 35.7-35.8 (Testing & Documentation)

---

## Success Metrics

- ✅ 100+ tests passing
- ✅ >90% coverage for new code
- ✅ 0 regressions
- ✅ <30s selection flow
- ✅ <100ms preference loading
- ✅ Works on all platforms
- ✅ Clear documentation

---

## Rollout Plan

**Phase 1**: Feature complete, full testing
**Phase 2**: Deploy to staging, dogfooding
**Phase 3**: Production release, monitor feedback

---

## Future Enhancements

After Epic 35 complete, consider:
- Global preferences (`~/.gao-dev/global_preferences.yaml`)
- Provider benchmarking and recommendations
- Automatic fallback on provider failure
- Usage analytics and reporting
- `gao-dev configure` standalone command

---

**Epic Status**: Planning
**Next Action**: Begin Story 35.1 (Project Setup & Architecture)
