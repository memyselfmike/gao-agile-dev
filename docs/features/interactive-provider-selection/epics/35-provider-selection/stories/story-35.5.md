# Story 35.5: ProviderSelector Implementation

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Story ID**: 35.5
**Story Points**: 5
**Owner**: Amelia (Software Developer)
**Dependencies**: Stories 35.2, 35.3, 35.4
**Priority**: P0
**Status**: Done

---

## Description

Implement `ProviderSelector` orchestrator class that coordinates all components (PreferenceManager, InteractivePrompter, ProviderValidator) to determine which provider configuration to use based on priority order: environment variables → saved preferences → interactive prompts → defaults.

This story focuses on:
- Orchestrating the complete provider selection flow
- Implementing priority-based decision logic
- Integrating validation with user feedback
- Dependency injection for testability
- Comprehensive test coverage (>90%)

---

## Acceptance Criteria

- [ ] `ProviderSelector` class fully implemented in `gao_dev/cli/provider_selector.py`:
  - [ ] `__init__()` - accepts optional dependencies (for testing)
  - [ ] `select_provider()` - main orchestration method (synchronous)
  - [ ] `_select_provider_async()` - async implementation (internal)
  - [ ] `has_saved_preferences()` - check for saved prefs
  - [ ] `use_environment_variable()` - check AGENT_PROVIDER env var
  - [ ] `_validate_and_retry()` - validation loop with retry
  - [ ] `_save_if_requested()` - save preferences if user agrees
- [ ] Priority order enforced correctly:
  1. **Environment variable** (`AGENT_PROVIDER`) - highest priority
  2. **Saved preferences** (if exist and user confirms)
  3. **Interactive prompts** (if no saved prefs or user declines)
  4. **Hardcoded defaults** (`claude-code`) - last resort
- [ ] Validation integrated:
  - [ ] Validate selected provider before returning
  - [ ] Show error panel if validation fails
  - [ ] Prompt user to select different provider or fix issue
  - [ ] Allow retry (max 3 attempts)
  - [ ] Allow cancel (Ctrl+C) at any point
- [ ] Dependency injection support:
  - [ ] Constructor accepts optional `PreferenceManager` instance
  - [ ] Constructor accepts optional `InteractivePrompter` instance
  - [ ] Constructor accepts optional `ProviderValidator` instance
  - [ ] Creates real instances if not provided (production use)
  - [ ] Enables easy mocking for tests
- [ ] Error handling:
  - [ ] `ProviderSelectionCancelled` on Ctrl+C
  - [ ] `ProviderValidationFailed` if no valid provider found after 3 attempts
  - [ ] Clear error messages at each step
  - [ ] Propagate KeyboardInterrupt (don't catch)
- [ ] Logging with structlog:
  - [ ] Info: provider selection source (env/saved/interactive/default)
  - [ ] Info: validation started/completed
  - [ ] Warning: validation failures
  - [ ] Debug: each step in decision tree
  - [ ] Debug: timing for performance monitoring
- [ ] Synchronous wrapper for async operations:
  - [ ] `select_provider()` is synchronous (for ChatREPL.__init__)
  - [ ] Uses `asyncio.run()` internally to call `_select_provider_async()`
  - [ ] Handles event loop creation properly
- [ ] Comprehensive test coverage (>90%):
  - [ ] Unit tests with mocked dependencies
  - [ ] Integration tests with real dependencies
  - [ ] All decision paths tested (env var, saved, interactive, default)
  - [ ] Error scenarios tested (validation fails, cancel, timeouts)
  - [ ] Retry logic tested
- [ ] Type hints throughout, MyPy passes strict mode

---

## Tasks

- [ ] Implement decision tree logic
  - [ ] Check environment variable first
  - [ ] Check saved preferences second
  - [ ] Prompt interactively third
  - [ ] Use defaults last
- [ ] Integrate all three components
  - [ ] Use PreferenceManager for load/save
  - [ ] Use InteractivePrompter for user interaction
  - [ ] Use ProviderValidator for validation
- [ ] Add validation loop
  - [ ] Validate provider config
  - [ ] If validation fails, show error
  - [ ] Prompt user to retry or select different provider
  - [ ] Allow max 3 attempts
- [ ] Implement synchronous wrapper
  - [ ] `select_provider()` calls `asyncio.run(_select_provider_async())`
  - [ ] Handle case where event loop already running
  - [ ] Proper error propagation
- [ ] Add error handling
  - [ ] Catch KeyboardInterrupt, convert to ProviderSelectionCancelled
  - [ ] Clear error messages
  - [ ] Proper exception hierarchy
- [ ] Write 10+ unit tests
  - [ ] Mock all dependencies
  - [ ] Test each decision path
  - [ ] Test error scenarios
- [ ] Write 10+ integration tests
  - [ ] Use real dependencies
  - [ ] Test full flow end-to-end
  - [ ] Test validation failures
- [ ] Add structlog logging
  - [ ] Log all decisions
  - [ ] Log validation results
  - [ ] Log timing information
- [ ] Run MyPy and fix issues
  - [ ] `mypy gao_dev/cli/provider_selector.py --strict`

---

## Test Cases

```python
# Environment variable path
def test_select_provider_env_var():
    """Environment variable bypasses prompts."""
    # Set AGENT_PROVIDER=opencode
    # Call select_provider()
    # Assert returns opencode config
    # Assert no prompts shown
    # Assert logged "Using provider from env var"

def test_select_provider_env_var_invalid():
    """Invalid env var falls back to prompts."""
    # Set AGENT_PROVIDER=invalid-provider
    # Mock prompter to return valid choice
    # Call select_provider()
    # Assert prompts shown
    # Assert warning logged

# Saved preferences path
def test_select_provider_saved_accepted():
    """Saved preferences used when accepted."""
    # Mock PreferenceManager.load_preferences() to return valid prefs
    # Mock InteractivePrompter.prompt_use_saved() to return 'y'
    # Call select_provider()
    # Assert returns saved config
    # Assert logged "Using saved preferences"

def test_select_provider_saved_rejected():
    """Interactive prompts when saved rejected."""
    # Mock PreferenceManager.load_preferences() to return valid prefs
    # Mock InteractivePrompter.prompt_use_saved() to return 'n'
    # Mock InteractivePrompter.prompt_provider() to return new choice
    # Call select_provider()
    # Assert prompts for new provider
    # Assert logged "User declined saved preferences"

# Interactive path
def test_select_provider_no_saved():
    """Interactive prompts when no saved prefs."""
    # Mock PreferenceManager.has_preferences() to return False
    # Mock InteractivePrompter.prompt_provider() to return choice
    # Call select_provider()
    # Assert prompts shown
    # Assert logged "No saved preferences, prompting user"

# Validation
def test_select_provider_validation_fails():
    """Prompt for different provider on validation failure."""
    # Mock InteractivePrompter to return provider choice
    # Mock ProviderValidator to fail validation
    # Mock InteractivePrompter to return different choice
    # Call select_provider()
    # Assert prompted twice
    # Assert second provider validated
    # Assert logged "Validation failed, retrying"

def test_select_provider_validation_max_attempts():
    """Raise error after 3 validation failures."""
    # Mock InteractivePrompter to return choices
    # Mock ProviderValidator to always fail
    # Call select_provider()
    # Assert ProviderValidationFailed raised
    # Assert error message includes "exceeded max attempts"

# Cancellation
def test_select_provider_cancelled():
    """Ctrl+C raises ProviderSelectionCancelled."""
    # Mock InteractivePrompter to raise KeyboardInterrupt
    # Call select_provider()
    # Assert ProviderSelectionCancelled raised
    # Assert logged "User cancelled provider selection"

# Preference saving
def test_select_provider_saves_preferences():
    """Preferences saved when user agrees."""
    # Mock InteractivePrompter.prompt_save_preferences() to return True
    # Mock PreferenceManager.save_preferences()
    # Call select_provider()
    # Assert save_preferences() called with correct config
    # Assert logged "Preferences saved"

def test_select_provider_no_save():
    """Preferences not saved when user declines."""
    # Mock InteractivePrompter.prompt_save_preferences() to return False
    # Mock PreferenceManager.save_preferences()
    # Call select_provider()
    # Assert save_preferences() NOT called
    # Assert logged "User declined to save preferences"

# Dependency injection
def test_has_saved_preferences():
    """Correctly detects saved preferences."""
    # Mock PreferenceManager.has_preferences() to return True
    # Call has_saved_preferences()
    # Assert returns True

def test_use_environment_variable():
    """Correctly extracts config from env var."""
    # Set AGENT_PROVIDER=claude-code
    # Call use_environment_variable()
    # Assert returns {'provider': 'claude-code'}

# Integration tests
async def test_full_flow_first_time():
    """Full flow for first-time user."""
    # No env var, no saved prefs
    # Mock all interactive prompts
    # Call select_provider()
    # Assert provider selected
    # Assert preferences saved
    # Assert validation passed

async def test_full_flow_returning_user():
    """Full flow for returning user."""
    # Saved prefs exist
    # Mock user accepts saved prefs
    # Call select_provider()
    # Assert saved config used
    # Assert validation passed
    # Assert no new preferences saved

async def test_full_flow_validation_recovery():
    """Full flow with validation failure and recovery."""
    # Mock provider choice
    # Mock validation fails first time
    # Mock different provider choice
    # Mock validation succeeds second time
    # Call select_provider()
    # Assert second provider returned
    # Assert preferences saved
```

---

## Definition of Done

- [ ] All methods implemented and working
- [ ] Synchronous wrapper for async operations implemented
- [ ] 20+ tests passing (10 unit, 10 integration), >90% coverage
- [ ] Integration tests with real components pass
- [ ] MyPy passes strict mode
- [ ] Documentation complete (docstrings)
- [ ] Code reviewed
- [ ] Commit message: `feat(epic-35): Story 35.5 - ProviderSelector Implementation (5 pts)`

---

## Notes

### CRAAP Resolutions Incorporated

**Async/Sync Handling (CRAAP Moderate - Issue #9)**:
- **Challenge**: ChatREPL.__init__ is synchronous, can't `await`
- **Solution**: Synchronous wrapper pattern
  ```python
  def select_provider(self) -> Dict[str, Any]:
      """Synchronous wrapper for async provider selection."""
      return asyncio.run(self._select_provider_async())

  async def _select_provider_async(self) -> Dict[str, Any]:
      """Async implementation of provider selection."""
      # All async operations here...
  ```
- **Benefit**: ChatREPL can call synchronously, internals use async for performance

### Decision Tree Flow

```
1. Check AGENT_PROVIDER env var
   ├─ If set and valid → Use it (validate)
   └─ If not set or invalid → Continue

2. Check saved preferences
   ├─ If exist → Prompt "Use saved?"
   │   ├─ If yes → Use saved (validate)
   │   └─ If no → Continue to prompts
   └─ If not exist → Continue to prompts

3. Interactive prompts
   ├─ Prompt for provider
   ├─ If OpenCode → Prompt for local/cloud
   ├─ Prompt for model
   └─ Validate

4. If validation fails
   ├─ Show error + suggestions
   ├─ Prompt "Try again?"
   │   ├─ If yes → Return to step 3
   │   └─ If no → Raise ProviderSelectionCancelled
   └─ If exceeded 3 attempts → Raise ProviderValidationFailed

5. Ask "Save preferences?"
   ├─ If yes → Save to .gao-dev/provider_preferences.yaml
   └─ If no → Don't save

6. Return provider config dict
```

### Priority Order Implementation

```python
async def _select_provider_async(self) -> Dict[str, Any]:
    logger.info("Starting provider selection")

    # Priority 1: Environment variable
    if env_config := self._check_env_var():
        logger.info("Using provider from environment variable")
        return await self._validate_and_return(env_config)

    # Priority 2: Saved preferences
    if self.preference_manager.has_preferences():
        if self.prompter.prompt_use_saved():
            saved_config = self.preference_manager.load_preferences()
            logger.info("Using saved preferences")
            return await self._validate_and_return(saved_config)

    # Priority 3: Interactive prompts
    logger.info("No saved preferences or user declined, prompting...")
    config = await self._prompt_for_provider()

    # Validate with retry logic
    config = await self._validate_and_retry(config, max_attempts=3)

    # Ask to save
    if self.prompter.prompt_save_preferences():
        self.preference_manager.save_preferences(config)
        logger.info("Preferences saved")

    return config
```

### Validation Loop with Retry

```python
async def _validate_and_retry(
    self, config: Dict[str, Any], max_attempts: int = 3
) -> Dict[str, Any]:
    """Validate provider config, retry on failure."""
    for attempt in range(1, max_attempts + 1):
        result = await self.validator.validate_configuration(config)

        if result.success:
            logger.info(f"Validation passed on attempt {attempt}")
            return config

        # Validation failed
        logger.warning(f"Validation failed (attempt {attempt}/{max_attempts})")
        self.prompter.show_error(
            f"Provider validation failed: {result.messages}",
            result.suggestions
        )

        if attempt < max_attempts:
            retry = self.prompter.prompt_retry()
            if retry:
                config = await self._prompt_for_provider()
            else:
                raise ProviderSelectionCancelled("User cancelled after validation failure")
        else:
            raise ProviderValidationFailed(
                f"Validation failed after {max_attempts} attempts"
            )

    # Should never reach here
    raise ProviderValidationFailed("Unexpected validation error")
```

### Dependency Injection Pattern

```python
class ProviderSelector:
    """Orchestrates provider selection flow."""

    def __init__(
        self,
        project_root: Path,
        preference_manager: Optional[PreferenceManager] = None,
        prompter: Optional[InteractivePrompter] = None,
        validator: Optional[ProviderValidator] = None,
    ):
        self.project_root = project_root

        # Use provided dependencies or create defaults
        self.preference_manager = preference_manager or PreferenceManager(project_root)
        self.prompter = prompter or InteractivePrompter()
        self.validator = validator or ProviderValidator()

        self.logger = structlog.get_logger(__name__)
```

### Performance Targets

- Environment variable check: <1ms
- Saved preferences check: <100ms (load from file)
- Interactive prompts: User-dependent (typically 10-30 seconds)
- Validation: <3 seconds (includes CLI checks)
- Total flow: <30 seconds (success criteria)

### Dependencies for Next Stories

After this story completes:
- Story 35.6 (ChatREPL Integration) can begin
- All three component stories (35.2, 35.3, 35.4) must be complete

---

**Story Status**: Todo
**Next Action**: Begin implementation after Stories 35.2, 35.3, 35.4 complete
**Created**: 2025-01-12
**Last Updated**: 2025-01-12
