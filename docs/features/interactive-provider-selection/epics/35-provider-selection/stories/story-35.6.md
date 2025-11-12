# Story 35.6: ChatREPL Integration

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.6
**Story Points**: 3
**Owner**: Amelia (Software Developer)
**Dependencies**: Story 35.5
**Priority**: P0
**Status**: Todo

---

## Description

Integrate `ProviderSelector` into `ChatREPL.__init__()` to enable interactive provider selection at startup while maintaining backward compatibility with existing configurations, environment variables, and feature flag control for rollback.

This story focuses on:
- Minimal changes to ChatREPL (10-15 lines)
- Feature flag integration for rollback capability
- Backward compatibility with existing flows
- Graceful error handling
- Comprehensive integration testing

---

## Acceptance Criteria

- [ ] `ChatREPL.__init__()` modified to use `ProviderSelector`:
  - [ ] Check feature flag: `config.features.interactive_provider_selection`
  - [ ] If flag is True: Create `ProviderSelector` instance
  - [ ] Call `select_provider()` to get config dict
  - [ ] Pass config to `ProcessExecutor` constructor
  - [ ] Handle `ProviderSelectionCancelled` gracefully (exit with message)
  - [ ] Handle `ProviderValidationFailed` gracefully (exit with error)
  - [ ] If flag is False: Use existing default behavior
- [ ] Backward compatibility maintained:
  - [ ] Existing env vars still work (`AGENT_PROVIDER`)
  - [ ] Existing ProcessExecutor constructor calls unchanged
  - [ ] No breaking changes to ChatREPL API
  - [ ] No changes to other ChatREPL methods
  - [ ] Feature can be disabled via feature flag
- [ ] Error handling:
  - [ ] Ctrl+C during selection → exit gracefully with clear message
  - [ ] Validation failures → show error, exit gracefully
  - [ ] No crashes under any circumstance
  - [ ] All exceptions logged properly
- [ ] User experience:
  - [ ] Selection happens **before** greeting message
  - [ ] Clear message if using env var: "Using provider from AGENT_PROVIDER: claude-code"
  - [ ] Clear message if using saved prefs: "Using saved provider: opencode (deepseek-r1)"
  - [ ] Smooth transition to normal REPL after selection
  - [ ] No duplicate or confusing messages
- [ ] Minimal code changes:
  - [ ] ~10-15 lines added to `__init__`
  - [ ] No changes to existing methods (run, handle_command, etc.)
  - [ ] No changes to ConversationalBrian
  - [ ] No changes to CommandRouter
  - [ ] No changes to other files (except tests)
- [ ] All existing tests still pass:
  - [ ] ChatREPL unit tests
  - [ ] ChatREPL integration tests
  - [ ] End-to-end REPL tests
  - [ ] Brian orchestrator tests
  - [ ] Session state tests
  - [ ] 0 regressions
- [ ] New integration tests added:
  - [ ] Test with env var set
  - [ ] Test with saved preferences
  - [ ] Test first-time startup
  - [ ] Test cancellation handling
  - [ ] Test feature flag disabled

---

## Tasks

- [ ] Read existing ChatREPL code
  - [ ] Understand `__init__` flow
  - [ ] Identify ProcessExecutor creation point
  - [ ] Identify config loading logic
- [ ] Add ProviderSelector import
  - [ ] `from gao_dev.cli.provider_selector import ProviderSelector`
  - [ ] `from gao_dev.cli.exceptions import ProviderSelectionCancelled, ProviderValidationFailed`
- [ ] Modify `__init__` to call select_provider()
  - [ ] Check feature flag first
  - [ ] If enabled, create ProviderSelector
  - [ ] Call select_provider()
  - [ ] Pass result to ProcessExecutor
  - [ ] If disabled, use existing logic
- [ ] Add error handling for cancellation
  - [ ] Catch ProviderSelectionCancelled
  - [ ] Print clear message: "Provider selection cancelled. Exiting."
  - [ ] Exit gracefully (sys.exit(0) or return)
- [ ] Add error handling for validation failures
  - [ ] Catch ProviderValidationFailed
  - [ ] Print error message with details
  - [ ] Exit gracefully (sys.exit(1))
- [ ] Test with existing test suite
  - [ ] Run: `pytest tests/cli/test_chatrepl.py -v`
  - [ ] Verify 0 regressions
  - [ ] Fix any broken tests
- [ ] Write 5+ integration tests
  - [ ] Test env var bypass
  - [ ] Test saved preferences
  - [ ] Test first-time flow
  - [ ] Test cancellation
  - [ ] Test feature flag disabled
- [ ] Update ChatREPL documentation
  - [ ] Add section on provider selection
  - [ ] Document feature flag
  - [ ] Document environment variable behavior
- [ ] Manual testing of full flow
  - [ ] First-time startup (no prefs)
  - [ ] Returning user (with prefs)
  - [ ] Env var set (bypass)
  - [ ] Ctrl+C handling
  - [ ] Feature flag disabled
- [ ] Verify feature flag exists in defaults.yaml
  - [ ] Ensure Story 35.1 added the flag
  - [ ] Default should be `true`

---

## Test Cases

```python
# Integration tests for ChatREPL
def test_chatrepl_with_env_var(tmp_path):
    """ChatREPL uses env var without prompts."""
    # Set AGENT_PROVIDER=claude-code
    # Create ChatREPL instance
    # Assert no prompts shown
    # Assert ProcessExecutor created with claude-code config
    # Assert logged "Using provider from env var"

def test_chatrepl_with_saved_prefs(tmp_path):
    """ChatREPL prompts to use saved prefs."""
    # Create saved preferences file
    # Mock InteractivePrompter.prompt_use_saved() to return 'y'
    # Create ChatREPL instance
    # Assert saved prefs used
    # Assert logged "Using saved preferences"

def test_chatrepl_first_time(tmp_path):
    """ChatREPL shows interactive prompts on first startup."""
    # No env var, no saved prefs
    # Mock all interactive prompts
    # Create ChatREPL instance
    # Assert prompts shown
    # Assert provider selected
    # Assert ProcessExecutor created

def test_chatrepl_cancellation(tmp_path):
    """Ctrl+C during selection exits gracefully."""
    # Mock InteractivePrompter to raise KeyboardInterrupt
    # Create ChatREPL instance
    # Assert ProviderSelectionCancelled caught
    # Assert exits with clear message
    # Assert no crash

def test_chatrepl_validation_failure(tmp_path):
    """Validation failure exits gracefully."""
    # Mock ProviderValidator to always fail
    # Mock user retries 3 times
    # Create ChatREPL instance
    # Assert ProviderValidationFailed caught
    # Assert exits with error message

def test_chatrepl_feature_flag_disabled(tmp_path):
    """Feature flag disabled uses old behavior."""
    # Set features.interactive_provider_selection = false
    # Create ChatREPL instance
    # Assert ProviderSelector NOT called
    # Assert default provider used
    # Assert no prompts shown

# Regression tests
def test_chatrepl_existing_functionality_unchanged(tmp_path):
    """All existing ChatREPL functionality still works."""
    # Test existing commands
    # Test Brian orchestrator
    # Test session state
    # Test command routing
    # Assert 0 regressions

def test_chatrepl_backward_compatible(tmp_path):
    """Backward compatibility maintained."""
    # Test with existing configs
    # Test with legacy CLI args
    # Test with existing .gao-dev/documents.db
    # Assert all work unchanged
```

---

## Implementation Example

```python
# In gao_dev/cli/chatrepl.py

class ChatREPL:
    def __init__(self, project_root: Path, config: Config):
        self.project_root = project_root
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Check feature flag for interactive provider selection
        if config.features.get('interactive_provider_selection', True):
            try:
                # New: Interactive provider selection
                from gao_dev.cli.provider_selector import ProviderSelector
                from gao_dev.cli.exceptions import (
                    ProviderSelectionCancelled,
                    ProviderValidationFailed,
                )

                selector = ProviderSelector(project_root)
                provider_config = selector.select_provider()
                self.logger.info("Provider selected", provider=provider_config['provider'])

            except ProviderSelectionCancelled:
                console.print("[yellow]Provider selection cancelled. Exiting.[/yellow]")
                sys.exit(0)

            except ProviderValidationFailed as e:
                console.print(f"[red]Provider validation failed: {e}[/red]")
                sys.exit(1)

        else:
            # Old: Use environment variable or default
            provider_config = self._get_default_provider_config()
            self.logger.info("Using default provider", provider=provider_config['provider'])

        # Create ProcessExecutor (existing code)
        self.executor = ProcessExecutor(
            provider=provider_config['provider'],
            model=provider_config.get('model'),
            config=provider_config,
        )

        # Rest of __init__ remains unchanged...
```

---

## Definition of Done

- [ ] ChatREPL modified and working
- [ ] Feature flag integration complete
- [ ] All existing tests pass (0 regressions)
- [ ] 5+ new integration tests passing
- [ ] Manual testing complete (all scenarios)
- [ ] Documentation updated (ChatREPL docs)
- [ ] Code reviewed
- [ ] Commit message: `feat(epic-35): Story 35.6 - ChatREPL Integration (3 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Feature Flag for Rollback (CRAAP Critical - Issue #8)**:
- **Purpose**: Enable production rollback if Epic 35 causes issues
- **Implementation**: Check `config.features.interactive_provider_selection` before using ProviderSelector
- **Benefit**: Can disable feature without code changes
- **Usage**:
  ```yaml
  # In gao_dev/config/defaults.yaml
  features:
    interactive_provider_selection: true  # Set to false to disable
  ```

**Session State Initialization (CRAAP Moderate - Issue #9)**:
- **Question**: Does provider selection interfere with session restoration?
- **Answer**: No, provider selection happens **before** session creation
- **Flow**:
  1. Provider selection (new)
  2. ProcessExecutor creation (existing)
  3. Session creation (existing)
  4. REPL greeting (existing)
- **Testing**: Verify session restoration still works

### Integration Points

**Before** (Existing):
```python
def __init__(self, project_root, config):
    # ... initialization ...
    self.executor = ProcessExecutor(provider='claude-code')  # Hardcoded
```

**After** (New):
```python
def __init__(self, project_root, config):
    # ... initialization ...

    # Check feature flag
    if config.features.get('interactive_provider_selection', True):
        selector = ProviderSelector(project_root)
        provider_config = selector.select_provider()  # Interactive or env var
    else:
        provider_config = self._get_default_provider_config()  # Old behavior

    self.executor = ProcessExecutor(**provider_config)
```

### Error Handling Strategy

**Graceful Exit on Cancellation**:
- User presses Ctrl+C → ProviderSelectionCancelled
- Print: "Provider selection cancelled. Exiting."
- Exit with code 0 (not an error, user choice)

**Graceful Exit on Validation Failure**:
- Validation fails 3 times → ProviderValidationFailed
- Print: "Provider validation failed: <reason>. Please fix and try again."
- Exit with code 1 (error)

**No Crashes**:
- All exceptions caught and handled
- User never sees traceback
- Always exit gracefully

### Timing and User Experience

**Selection Timing**:
- Provider selection happens **first** (before greeting)
- Reason: User needs to know which provider before seeing prompt
- Flow: Select → Validate → Create executor → Show greeting

**Messages**:
- Env var: "[dim]Using provider from AGENT_PROVIDER: claude-code[/dim]"
- Saved: "[dim]Using saved provider: opencode (deepseek-r1)[/dim]"
- First time: [Interactive prompts shown]
- After selection: [Normal greeting]

### Performance Impact

**When Feature Enabled**:
- Env var set: +1ms (env var check only)
- Saved prefs: +100ms (load from file)
- First time: +10-30s (user interaction)

**When Feature Disabled**:
- No performance impact (old code path)

### Backward Compatibility

**Still Works**:
- `AGENT_PROVIDER=opencode gao-dev start` (env var)
- Existing `.gao-dev/` directories
- Existing CLI arguments
- Existing commands: `/help`, `/brian`, etc.

**Doesn't Break**:
- Other CLI commands (create-prd, create-architecture)
- Sandbox/benchmark runner
- Existing test suite
- Existing workflows

### Dependencies for Next Stories

After this story completes:
- Story 35.7 (Testing & Regression) can begin
- Full integration is complete at this point

---

**Story Status**: Todo
**Next Action**: Begin implementation after Story 35.5 completes
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
