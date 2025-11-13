# Architecture Document: Interactive Provider Selection

**Feature**: Interactive Provider Selection for Brian REPL
**Epic**: Epic 35
**Version**: 1.0
**Status**: Planning
**Created**: 2025-01-12

---

## 1. Overview

This document describes the technical architecture for adding interactive provider selection to the GAO-Dev REPL startup flow. The system allows users to interactively choose their AI provider, configure provider-specific settings, and persist preferences for future sessions.

### 1.1 Design Goals

1. **Zero Regressions**: Existing functionality must work identically
2. **Clean Separation**: New code isolated in new modules
3. **Testability**: All components fully unit-testable
4. **Extensibility**: Easy to add new provider types
5. **User-Friendly**: Clear prompts, good defaults, skip options
6. **Performance**: Preference loading <100ms, validation <2s

### 1.2 Key Principles

- **Dependency Injection**: Components receive dependencies via constructor
- **Interface Segregation**: Small, focused interfaces
- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Open for extension (new providers), closed for modification
- **Fail-Safe**: Graceful degradation if preferences corrupt or providers unavailable

---

## 2. System Architecture

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ChatREPL                                 │
│  (Existing, Minor Modifications)                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ select_provider()
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ProviderSelector                              │
│  (NEW - Story 35.5)                                             │
│                                                                  │
│  + select_provider() -> Dict                                    │
│  + has_saved_preferences() -> bool                              │
│  + use_environment_variable() -> Optional[Dict]                 │
└──┬────────────────────┬──────────────────────┬──────────────────┘
   │                    │                      │
   │ prompt()           │ save/load            │ validate()
   ▼                    ▼                      ▼
┌──────────────┐ ┌────────────────┐ ┌─────────────────────┐
│Interactive   │ │Preference      │ │Provider            │
│Prompter      │ │Manager         │ │Validator           │
│(NEW 35.4)    │ │(NEW 35.2)      │ │(NEW 35.3)          │
│              │ │                │ │                    │
│+ prompt_     │ │+ load_prefs()  │ │+ validate_config() │
│  provider()  │ │+ save_prefs()  │ │+ check_cli()       │
│+ prompt_     │ │+ get_defaults()│ │+ test_connection() │
│  model()     │ │                │ │                    │
│+ prompt_     │ │                │ │                    │
│  opencode()  │ │                │ │                    │
└──────────────┘ └────────────────┘ └─────────────────────┘
                       │
                       │ uses
                       ▼
              ┌────────────────┐
              │    PyYAML      │
              │  (Existing)    │
              └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Existing Components (No Changes)                   │
├─────────────────────────────────────────────────────────────────┤
│  ProcessExecutor  │  ProviderFactory  │  ConversationalBrian    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Sequence Diagram: First-Time Startup

```
User           ChatREPL      ProviderSelector   InteractivePrompter   PreferenceManager   ProviderValidator
 │                │                │                     │                   │                   │
 │  gao-dev start │                │                     │                   │                   │
 ├───────────────>│                │                     │                   │                   │
 │                │ __init__()     │                     │                   │                   │
 │                ├───────────────>│                     │                   │                   │
 │                │                │ check_env_var()     │                   │                   │
 │                │                ├─────────────────────┼───────────────────┼──────────────────>│
 │                │                │ None                │                   │                   │
 │                │                │<────────────────────┼───────────────────┼───────────────────┤
 │                │                │                     │                   │                   │
 │                │                │ has_saved_prefs?    │                   │                   │
 │                │                ├─────────────────────┼───────────────────>│                   │
 │                │                │ False               │                   │                   │
 │                │                │<────────────────────┼───────────────────┤                   │
 │                │                │                     │                   │                   │
 │                │                │ prompt_provider()   │                   │                   │
 │                │                ├────────────────────>│                   │                   │
 │  [Show Table]  │                │                     │                   │                   │
 │<───────────────┼────────────────┼─────────────────────┤                   │                   │
 │  Select: 2     │                │                     │                   │                   │
 │───────────────>│                │                     │                   │                   │
 │                │                │ "opencode"          │                   │                   │
 │                │                │<────────────────────┤                   │                   │
 │                │                │                     │                   │                   │
 │                │                │ prompt_opencode()   │                   │                   │
 │                │                ├────────────────────>│                   │                   │
 │  Local? y      │                │                     │                   │                   │
 │<───────────────┼────────────────┼─────────────────────┤                   │                   │
 │                │                │ use_local=True      │                   │                   │
 │                │                │<────────────────────┤                   │                   │
 │                │                │                     │                   │                   │
 │                │                │ prompt_model()      │                   │                   │
 │                │                ├────────────────────>│                   │                   │
 │  Model: 1      │                │                     │                   │                   │
 │<───────────────┼────────────────┼─────────────────────┤                   │                   │
 │                │                │ "deepseek-r1"       │                   │                   │
 │                │                │<────────────────────┤                   │                   │
 │                │                │                     │                   │                   │
 │                │                │ validate_config()   │                   │                   │
 │                │                ├─────────────────────┼───────────────────┼──────────────────>│
 │                │                │ Valid=True          │                   │                   │
 │                │                │<────────────────────┼───────────────────┼───────────────────┤
 │                │                │                     │                   │                   │
 │  Save? y       │                │                     │                   │                   │
 │<───────────────┼────────────────┼─────────────────────┤                   │                   │
 │                │                │ save_preferences()  │                   │                   │
 │                │                ├─────────────────────┼───────────────────>│                   │
 │                │                │ Saved               │                   │                   │
 │                │                │<────────────────────┼───────────────────┤                   │
 │                │                │                     │                   │                   │
 │                │ provider_config│                     │                   │                   │
 │                │<───────────────┤                     │                   │                   │
 │                │                │                     │                   │                   │
 │                │ Create ProcessExecutor(config)       │                   │                   │
 │                │                │                     │                   │                   │
 │                │ start() REPL   │                     │                   │                   │
 │<───────────────┤                │                     │                   │                   │
```

### 2.3 Sequence Diagram: Returning User

```
User           ChatREPL      ProviderSelector   PreferenceManager
 │                │                │                   │
 │  gao-dev start │                │                   │
 ├───────────────>│                │                   │
 │                │ __init__()     │                   │
 │                ├───────────────>│                   │
 │                │                │ load_prefs()      │
 │                │                ├──────────────────>│
 │                │                │ prefs_dict        │
 │                │                │<──────────────────┤
 │                │                │                   │
 │  Use saved?    │                │                   │
 │<───────────────┼────────────────┤                   │
 │  Y (Enter)     │                │                   │
 │───────────────>│                │                   │
 │                │ provider_config│                   │
 │                │<───────────────┤                   │
 │                │                │                   │
 │                │ Create ProcessExecutor(config)     │
 │                │                │                   │
 │                │ start() REPL   │                   │
 │<───────────────┤                │                   │
```

---

## 3. Component Specifications

### 3.1 ProviderSelector

**File**: `gao_dev/cli/provider_selector.py`

**Purpose**: Orchestrates provider selection flow by coordinating prompts, preferences, and validation.

**Responsibilities**:
- Check environment variables first
- Load saved preferences if available
- Coordinate interactive prompts if needed
- Validate final configuration
- Return provider config dict

**Interface**:
```python
class ProviderSelector:
    """
    Orchestrates interactive provider selection for REPL startup.

    Coordinates PreferenceManager, InteractivePrompter, and ProviderValidator
    to determine which provider configuration to use.
    """

    def __init__(
        self,
        project_root: Path,
        console: Console,
        preference_manager: Optional[PreferenceManager] = None,
        interactive_prompter: Optional[InteractivePrompter] = None,
        provider_validator: Optional[ProviderValidator] = None
    ):
        """Initialize with dependencies (supports dependency injection)."""

    def select_provider(self) -> Dict[str, Any]:
        """
        Select provider using priority: env var > saved prefs > interactive.

        Returns:
            Dict with keys: provider, model, config

        Raises:
            ProviderSelectionCancelled: User cancelled selection
            ProviderValidationFailed: Selected provider failed validation
        """

    def has_saved_preferences(self) -> bool:
        """Check if saved preferences exist."""

    def use_environment_variable(self) -> Optional[Dict[str, Any]]:
        """Get provider config from AGENT_PROVIDER env var if set."""
```

**Dependencies**:
- `PreferenceManager` (for loading/saving)
- `InteractivePrompter` (for user interaction)
- `ProviderValidator` (for validation)
- `ProviderFactory` (for listing providers)

**Testing Strategy**:
- Unit tests: Mock all dependencies
- Integration tests: Real dependencies, mock user input
- E2E tests: Full flow with mocked providers

---

### 3.2 InteractivePrompter

**File**: `gao_dev/cli/interactive_prompter.py`

**Purpose**: Handles all user interaction using Rich and prompt_toolkit.

**Responsibilities**:
- Display provider selection table
- Prompt for provider choice
- Handle OpenCode-specific prompts (local vs cloud)
- Display model selection table
- Prompt for model choice
- Ask about saving preferences

**Interface**:
```python
class InteractivePrompter:
    """
    Handles interactive prompts for provider selection.

    Uses Rich for formatted output and prompt_toolkit for input.
    """

    def __init__(self, console: Console):
        """Initialize with Rich console."""

    def prompt_provider(
        self,
        available_providers: List[str],
        descriptions: Dict[str, str]
    ) -> str:
        """
        Prompt user to select a provider.

        Args:
            available_providers: List of provider names
            descriptions: Provider name -> description mapping

        Returns:
            Selected provider name

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C
        """

    def prompt_opencode_config(self) -> Dict[str, Any]:
        """
        Prompt for OpenCode-specific configuration.

        Asks:
        - Local model (Ollama) vs cloud?
        - If cloud: which provider (anthropic/openai/google)?

        Returns:
            Dict with opencode-specific config
        """

    def prompt_model(
        self,
        available_models: List[str],
        descriptions: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Prompt user to select a model.

        Args:
            available_models: List of model names
            descriptions: Optional model descriptions

        Returns:
            Selected model name
        """

    def prompt_save_preferences(self) -> bool:
        """
        Ask if user wants to save preferences.

        Returns:
            True if user wants to save, False otherwise
        """

    def prompt_use_saved(self, saved_config: Dict[str, Any]) -> str:
        """
        Ask if user wants to use saved configuration.

        Args:
            saved_config: Previously saved configuration

        Returns:
            'y' (yes), 'n' (no), or 'c' (change specific settings)
        """

    def show_error(self, message: str, suggestions: Optional[List[str]] = None):
        """
        Display error message with optional suggestions.

        Args:
            message: Error message
            suggestions: Optional list of suggestion strings
        """

    def show_success(self, message: str):
        """Display success message."""
```

**Dependencies**:
- `rich.console.Console`
- `rich.prompt.Prompt`
- `rich.prompt.Confirm`
- `rich.table.Table`
- `rich.panel.Panel`

**Testing Strategy**:
- Unit tests: Mock Rich/prompt_toolkit
- Integration tests: Capture output, inject input
- E2E tests: Full interaction flows

---

### 3.3 PreferenceManager

**File**: `gao_dev/cli/preference_manager.py`

**Purpose**: Manages loading and saving of provider preferences.

**Responsibilities**:
- Load preferences from `.gao-dev/provider_preferences.yaml`
- Save preferences to file
- Validate preference file format
- Provide sensible defaults
- Handle corrupt/missing files gracefully

**Interface**:
```python
class PreferenceManager:
    """
    Manages provider preference persistence.

    Loads and saves preferences to .gao-dev/provider_preferences.yaml.
    """

    def __init__(self, project_root: Path):
        """Initialize with project root."""

    def load_preferences(self) -> Optional[Dict[str, Any]]:
        """
        Load saved preferences from file.

        Returns:
            Preferences dict, or None if file doesn't exist or is invalid

        Format:
            {
                'provider': 'opencode',
                'model': 'deepseek-r1',
                'config': {...},
                'metadata': {
                    'last_updated': '2025-01-12T10:30:00Z',
                    'version': '1.0'
                }
            }
        """

    def save_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Save preferences to file.

        Args:
            preferences: Preferences dict to save

        Raises:
            PreferenceSaveError: If save fails
        """

    def has_preferences(self) -> bool:
        """Check if preferences file exists and is valid."""

    def get_default_preferences(self) -> Dict[str, Any]:
        """
        Get default preferences for fallback.

        Returns:
            Default preferences (claude-code, sonnet-4.5)
        """

    def validate_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Validate preference structure.

        Checks required keys, types, values.

        Args:
            preferences: Preferences dict to validate

        Returns:
            True if valid, False otherwise
        """

    def delete_preferences(self) -> None:
        """Delete preferences file (for testing/reset)."""
```

**File Format** (`.gao-dev/provider_preferences.yaml`):
```yaml
version: "1.0"
last_updated: "2025-01-12T10:30:00Z"

provider:
  name: "opencode"
  model: "deepseek-r1"

  config:
    ai_provider: "ollama"
    use_local: true
    timeout: 3600

metadata:
  cli_version: "1.2.3"
  last_validated: "2025-01-12T10:30:00Z"
  validation_status: "healthy"
```

**Dependencies**:
- `pyyaml`
- `pathlib`
- `datetime`

**Testing Strategy**:
- Unit tests: Test all methods with mock filesystem
- Integration tests: Real file I/O with temp directories
- Edge cases: Corrupt files, missing fields, old versions

---

### 3.4 ProviderValidator

**File**: `gao_dev/cli/provider_validator.py`

**Purpose**: Validates provider configuration before use.

**Responsibilities**:
- Check if CLI tools are installed (claude, opencode)
- Validate API keys (if using direct API)
- Test basic connectivity
- Check for required dependencies
- Provide actionable error messages

**Interface**:
```python
class ProviderValidator:
    """
    Validates provider configuration.

    Checks CLI availability, API keys, connectivity.
    """

    def __init__(self, console: Console):
        """Initialize with console for output."""

    async def validate_configuration(
        self,
        provider_name: str,
        config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate provider configuration.

        Args:
            provider_name: Provider identifier
            config: Provider configuration dict

        Returns:
            ValidationResult with success/failure and messages
        """

    async def check_cli_available(self, cli_name: str) -> bool:
        """
        Check if CLI tool is in PATH.

        Args:
            cli_name: Name of CLI (e.g., 'claude', 'opencode', 'ollama')

        Returns:
            True if available, False otherwise
        """

    async def check_ollama_models(self) -> List[str]:
        """
        Get list of available Ollama models.

        Returns:
            List of model names, or empty list if Ollama unavailable
        """

    def suggest_fixes(self, provider_name: str) -> List[str]:
        """
        Provide installation/fix suggestions for provider.

        Args:
            provider_name: Provider that failed validation

        Returns:
            List of suggestion strings
        """

@dataclass
class ValidationResult:
    """Result of provider validation."""
    success: bool
    provider_name: str
    messages: List[str]
    warnings: List[str]
    suggestions: List[str]
```

**Dependencies**:
- `asyncio` (for async validation)
- `subprocess` (for checking CLI availability)
- `ProviderFactory` (for creating test instances)

**Testing Strategy**:
- Unit tests: Mock subprocess calls
- Integration tests: Real CLI checks (where available)
- Edge cases: Missing CLIs, invalid configs, network failures

---

## 4. Data Models

### 4.1 ProviderConfig

```python
@dataclass
class ProviderConfig:
    """Provider configuration returned by ProviderSelector."""
    provider_name: str
    model: str
    config: Dict[str, Any]
    validated: bool
    validation_timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for ProcessExecutor."""
        return {
            'provider': self.provider_name,
            'model': self.model,
            'config': self.config
        }
```

### 4.2 ProviderPreferences

```python
@dataclass
class ProviderPreferences:
    """Saved provider preferences."""
    version: str
    last_updated: datetime
    provider: ProviderConfig
    metadata: Dict[str, Any]

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dict."""

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'ProviderPreferences':
        """Create from loaded YAML dict."""
```

---

## 5. Integration Points

### 5.1 ChatREPL Modification

**File**: `gao_dev/cli/chat_repl.py`

**Changes**:
```python
# BEFORE (lines 68-72)
executor = ProcessExecutor(self.project_root)
analysis_service = AIAnalysisService(executor)

# AFTER
from gao_dev.cli.provider_selector import ProviderSelector

# Select provider interactively
provider_selector = ProviderSelector(self.project_root, self.console)
try:
    provider_config = provider_selector.select_provider()
except (KeyboardInterrupt, ProviderSelectionCancelled):
    self.console.print("[yellow]Provider selection cancelled. Exiting.[/yellow]")
    sys.exit(0)

# Create executor with selected provider
executor = ProcessExecutor(
    self.project_root,
    provider_name=provider_config['provider'],
    provider_config=provider_config['config']
)
analysis_service = AIAnalysisService(executor)
```

**Impact**: Minimal. Just add provider selection before ProcessExecutor creation.

---

### 5.2 ProcessExecutor (No Changes)

The existing `ProcessExecutor` already supports:
- `provider_name` parameter ✅
- `provider_config` parameter ✅
- Environment variable override (`AGENT_PROVIDER`) ✅

No changes needed! The new components just provide the parameters.

---

### 5.3 Environment Variable Precedence

**Priority Order** (highest to lowest):
1. `AGENT_PROVIDER` environment variable (bypasses all prompts)
2. Saved preferences in `.gao-dev/provider_preferences.yaml`
3. Interactive prompts (first-time setup)
4. Hardcoded defaults (claude-code, sonnet-4.5)

**Example**:
```bash
# Bypass all prompts
export AGENT_PROVIDER=opencode
gao-dev start  # Uses opencode without prompting

# Use saved preferences
gao-dev start  # Prompts "Use saved config?" if preferences exist

# First-time setup
gao-dev start  # Full interactive prompts
```

---

## 6. Error Handling

### 6.1 Error Taxonomy

```python
class ProviderSelectionError(Exception):
    """Base exception for provider selection errors."""
    pass

class ProviderSelectionCancelled(ProviderSelectionError):
    """User cancelled provider selection (Ctrl+C)."""
    pass

class ProviderValidationFailed(ProviderSelectionError):
    """Provider validation failed."""
    pass

class PreferenceSaveError(ProviderSelectionError):
    """Failed to save preferences."""
    pass

class PreferenceLoadError(ProviderSelectionError):
    """Failed to load preferences."""
    pass
```

### 6.2 Error Handling Strategy

| Error | Handling |
|-------|----------|
| User presses Ctrl+C | Catch KeyboardInterrupt, exit gracefully with message |
| Invalid preference file | Log warning, prompt user (don't crash) |
| Provider validation fails | Show error + suggestions, prompt for different provider |
| CLI not found | Show error + installation instructions, offer alternatives |
| Save preferences fails | Log warning, continue anyway (non-critical) |
| Ollama not found | Hide "local model" option, only show cloud providers |

### 6.3 Fallback Chain

```
1. Try user's selection
   ├─ Valid? → Use it
   └─ Invalid? → Show error
       ├─ User chooses different provider → Retry
       └─ User presses Ctrl+C → Exit

2. Environment variable set?
   ├─ Valid? → Use it
   └─ Invalid? → Warn user, proceed to saved preferences

3. Saved preferences exist?
   ├─ Valid? → Prompt user
   │   ├─ Accept? → Use it
   │   └─ Reject? → Interactive prompts
   └─ Invalid? → Interactive prompts

4. Interactive prompts
   ├─ Success? → Use selection
   └─ Cancelled? → Exit gracefully

5. Last resort: Hardcoded defaults
   └─ Use claude-code + sonnet-4.5
```

---

## 7. Performance Considerations

### 7.1 Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Load preferences | <100ms | Time to read YAML |
| Save preferences | <200ms | Time to write YAML |
| Provider validation | <2s | CLI check + basic test |
| Ollama model detection | <3s | `ollama list` command |
| Interactive prompts | <30s | Total user time |
| ChatREPL startup (with selection) | <5s | End-to-end |

### 7.2 Optimization Strategies

1. **Lazy validation**: Only validate when needed, not on every startup
2. **Cache CLI checks**: Remember which CLIs are available
3. **Async operations**: Run validations concurrently where possible
4. **Skip prompts**: Environment variable bypasses everything
5. **Fast defaults**: Saved preferences skip prompts

### 7.3 Memory Usage

Estimated additional memory usage: **<2 MB**
- YAML parsing: ~100 KB
- Rich components: ~500 KB
- Provider instances: ~1 MB
- Cached data: ~100 KB

---

## 8. Security Considerations

### 8.1 API Key Handling

- **NEVER store API keys in preferences file**
- Always read from environment variables
- Reference environment variable names in config:
  ```yaml
  config:
    api_key_env: "ANTHROPIC_API_KEY"  # Reference, not value
  ```

### 8.2 File Permissions

- Preferences file: `0600` (user read/write only)
- `.gao-dev/` directory: `0700` (user only)

### 8.3 Input Validation

- Validate all user input before using
- Sanitize file paths (no directory traversal)
- Validate YAML structure before loading
- Timeout on validation operations (prevent hanging)

---

## 9. Testing Architecture

### 9.1 Test Structure

```
tests/cli/
├── test_provider_selector.py          (Unit + Integration)
├── test_interactive_prompter.py       (Unit + Integration)
├── test_preference_manager.py         (Unit + Integration)
├── test_provider_validator.py         (Unit + Integration)
└── test_provider_selection_e2e.py     (End-to-End)
```

### 9.2 Test Fixtures

```python
# conftest.py
@pytest.fixture
def mock_console():
    """Mock Rich Console."""
    return Mock(spec=Console)

@pytest.fixture
def temp_project_root(tmp_path):
    """Temporary project root with .gao-dev/ directory."""
    gao_dev = tmp_path / ".gao-dev"
    gao_dev.mkdir()
    return tmp_path

@pytest.fixture
def sample_preferences():
    """Sample valid preferences dict."""
    return {
        'provider': 'opencode',
        'model': 'deepseek-r1',
        'config': {'ai_provider': 'ollama'},
        'metadata': {'version': '1.0'}
    }

@pytest.fixture
def mock_prompter():
    """Mock InteractivePrompter with pre-configured responses."""
    prompter = Mock(spec=InteractivePrompter)
    prompter.prompt_provider.return_value = "opencode"
    prompter.prompt_model.return_value = "deepseek-r1"
    prompter.prompt_save_preferences.return_value = True
    return prompter
```

### 9.3 Regression Test Suite

**File**: `tests/regression/test_epic35_no_regressions.py`

```python
class TestEpic35NoRegressions:
    """Ensure Epic 35 doesn't break existing functionality."""

    def test_existing_env_var_still_works(self):
        """AGENT_PROVIDER env var still overrides everything."""

    def test_chatrepl_with_env_var_skips_prompts(self):
        """ChatREPL doesn't prompt when env var set."""

    def test_processexecutor_backward_compatible(self):
        """ProcessExecutor still works with old constructor."""

    def test_all_existing_tests_pass(self):
        """Run full test suite to ensure no breaks."""

    def test_existing_config_files_still_work(self):
        """Old config files (defaults.yaml) still work."""
```

---

## 10. Documentation Requirements

### 10.1 User Documentation

1. **User Guide**: `docs/features/interactive-provider-selection/USER_GUIDE.md`
   - How to use interactive setup
   - How to change preferences
   - How to skip prompts
   - Troubleshooting common issues

2. **FAQ**: `docs/features/interactive-provider-selection/FAQ.md`
   - What if I want to change my provider?
   - How do I use local models?
   - What if validation fails?
   - How do I bypass prompts in CI/CD?

### 10.2 Developer Documentation

1. **Architecture** (this document)
2. **API Reference**: `docs/features/interactive-provider-selection/API_REFERENCE.md`
   - All public classes and methods
   - Usage examples
   - Integration patterns

3. **Testing Guide**: `docs/features/interactive-provider-selection/TESTING.md`
   - How to run tests
   - How to add new tests
   - Mock patterns

---

## 11. Migration Strategy

### 11.1 Backward Compatibility

**Existing users will see NO changes unless**:
- They have `AGENT_PROVIDER` set → No prompts, uses env var
- They run ChatREPL → New interactive prompts appear

**All existing functionality preserved**:
- ✅ Environment variables still work
- ✅ Config files (defaults.yaml) still work
- ✅ ProcessExecutor constructor unchanged
- ✅ All existing tests pass

### 11.2 Rollout Plan

**Phase 1: Opt-In (Week 1)**
- Feature released but disabled by default
- Users enable via feature flag: `ENABLE_INTERACTIVE_PROVIDER_SELECTION=1`

**Phase 2: Opt-Out (Week 2)**
- Feature enabled by default
- Users can disable via env var: `SKIP_PROVIDER_SELECTION=1`

**Phase 3: Full Rollout (Week 3)**
- Feature always enabled
- Environment variables still bypass prompts

---

## 12. Future Enhancements

### 12.1 Potential Extensions

1. **Global preferences**: `~/.gao-dev/global_preferences.yaml`
2. **Provider benchmarking**: Test speed and recommend fastest
3. **Cost estimation**: Show estimated cost before starting
4. **A/B testing mode**: Automatically try different providers
5. **Provider health dashboard**: `gao-dev providers dashboard`
6. **Automatic fallback**: If provider fails, auto-switch to backup
7. **Usage analytics**: Track which providers are most used

### 12.2 Plugin System Integration

Allow plugins to register custom providers:
```yaml
# ~/.gao-dev/plugins/my-custom-provider/config.yaml
provider:
  name: "my-custom-provider"
  description: "My custom AI provider"
  class: "MyCustomProvider"
```

---

## 13. Glossary

| Term | Definition |
|------|------------|
| **Provider** | AI execution backend (Claude Code, OpenCode, direct API) |
| **Model** | Specific AI model (sonnet-4.5, deepseek-r1, etc.) |
| **Preferences** | Saved provider configuration in YAML file |
| **Validation** | Checking if provider is available and properly configured |
| **Interactive Prompt** | User input request using Rich/prompt_toolkit |
| **Fallback** | Alternative provider used if primary fails |
| **Bypass** | Skip prompts using environment variable |

---

## 8. Security Considerations

### 8.1 YAML Injection Prevention (CRAAP Resolution)

**Risk**: User-provided input saved to YAML could execute arbitrary code if not properly sanitized.

**Mitigations Implemented**:

**1. Use `yaml.safe_dump()` Instead of `yaml.dump()`**:
```python
# PreferenceManager.save_preferences()

# UNSAFE - Can execute arbitrary code
yaml.dump(preferences, file)

# SAFE - Only dumps basic Python types
yaml.safe_dump(preferences, file, default_flow_style=False)
```

**Rationale**: `yaml.safe_dump()` only serializes basic Python types (dict, list, str, int, etc.) and prevents YAML tags like `!!python/object/apply` which can execute code.

**2. Input Sanitization Before Saving**:
```python
# PreferenceManager._sanitize_string()

def _sanitize_string(self, value: str) -> str:
    """
    Sanitize string to prevent YAML injection.

    Only allows: alphanumeric, dash, underscore, dot, slash, colon, space
    Removes: YAML tags (!), anchors (&), aliases (*), quotes, newlines
    """
    import string
    allowed_chars = set(string.ascii_letters + string.digits + '-_./: ')
    return ''.join(c for c in value if c in allowed_chars)

def _sanitize_dict(self, data: Dict) -> Dict:
    """Recursively sanitize all string values in dict."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = self._sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = self._sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                self._sanitize_string(v) if isinstance(v, str) else v
                for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized

def save_preferences(self, preferences: Dict) -> None:
    """Save preferences with sanitization."""
    # Step 1: Sanitize all input
    sanitized = self._sanitize_dict(preferences)

    # Step 2: Use safe_dump
    yaml_str = yaml.safe_dump(sanitized, default_flow_style=False)

    # Step 3: Atomic write
    self.preferences_file.write_text(yaml_str)
```

**3. Security Tests with Malicious Input**:
```python
# tests/cli/test_preference_manager.py

def test_yaml_tag_injection_prevented():
    """Test that YAML tag injection is prevented."""
    manager = PreferenceManager(tmp_path)

    malicious_prefs = {
        'provider': '!!python/object/apply:os.system ["rm -rf /"]',
        'model': 'sonnet-4.5'
    }

    manager.save_preferences(malicious_prefs)
    loaded = manager.load_preferences()

    # Verify dangerous tags removed
    assert '!!' not in loaded['provider']
    assert 'rm -rf' not in loaded['provider']
    assert 'os.system' not in loaded['provider']

def test_yaml_anchor_injection_prevented():
    """Test that YAML anchors/aliases are prevented."""
    manager = PreferenceManager(tmp_path)

    malicious_prefs = {
        'provider': '&anchor claude-code',
        'model': '*anchor'
    }

    manager.save_preferences(malicious_prefs)
    loaded = manager.load_preferences()

    # Verify anchors/aliases removed
    assert '&' not in loaded['provider']
    assert '*' not in loaded['model']

def test_special_characters_sanitized():
    """Test that special characters are sanitized."""
    manager = PreferenceManager(tmp_path)

    malicious_prefs = {
        'provider': 'claude-code\n---\nevil: payload',
        'model': 'sonnet"4.5\'injection'
    }

    manager.save_preferences(malicious_prefs)
    loaded = manager.load_preferences()

    # Verify special chars removed
    assert '\n' not in loaded['provider']
    assert '---' not in loaded['provider']
    assert '"' not in loaded['model']
    assert "'" not in loaded['model']
```

### 8.2 API Key Handling

**Best Practices**:

1. **NEVER store API keys in preferences file**
   ```yaml
   # WRONG
   config:
     api_key: "sk-ant-api03-..."

   # RIGHT
   config:
     api_key_env: "ANTHROPIC_API_KEY"  # Reference only
   ```

2. **Always read from environment variables**
   ```python
   api_key = os.getenv(config['api_key_env'])
   if not api_key:
       raise ValueError(f"{config['api_key_env']} not set")
   ```

3. **Validate key format (optional)**
   ```python
   def validate_anthropic_key(self, key: str) -> bool:
       """Quick format check for Anthropic API key."""
       return key.startswith('sk-ant-api03-')
   ```

### 8.3 File Permissions

**Preferences File Security**:

```python
# PreferenceManager.save_preferences()

import os

# Set restrictive permissions (user read/write only)
if os.name == 'posix':  # Unix/macOS/Linux
    os.chmod(self.preferences_file, 0o600)  # -rw-------
elif os.name == 'nt':  # Windows
    # Use Windows ACLs (requires pywin32)
    import win32security
    import win32con

    user = win32security.GetTokenInformation(
        win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_QUERY
        ),
        win32security.TokenUser
    )[0]

    sd = win32security.SECURITY_DESCRIPTOR()
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(
        win32con.FILE_ALL_ACCESS,
        user
    )
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        str(self.preferences_file),
        win32security.DACL_SECURITY_INFORMATION,
        sd
    )
```

### 8.4 Input Validation

**All user input validated before use**:

```python
class InteractivePrompter:
    def prompt_provider(self, available_providers: List[str]) -> str:
        """Prompt with strict validation."""
        valid_choices = [str(i) for i in range(1, len(available_providers) + 1)]

        while True:
            choice = input(f"Select provider [{'/'.join(valid_choices)}]: ")

            # Validate input
            if choice not in valid_choices:
                print(f"Invalid choice. Must be one of: {', '.join(valid_choices)}")
                continue

            # Map choice to provider
            provider_index = int(choice) - 1
            return available_providers[provider_index]
```

---

## 9. CI/CD Compatibility (CRAAP Resolution)

### 9.1 Lazy Import Pattern

**Problem**: `prompt_toolkit` fails in headless CI environments without TTY, breaking even when `AGENT_PROVIDER` env var is set.

**Solution**: Lazy imports with fallback to `input()`.

**Implementation**:

```python
# InteractivePrompter class

class InteractivePrompter:
    """Interactive prompts with CI/CD compatibility."""

    def __init__(self, console: Console):
        """Initialize with Rich console (always safe)."""
        self.console = console

    def prompt_provider(
        self,
        available_providers: List[str],
        descriptions: Dict[str, str]
    ) -> str:
        """
        Prompt user to select provider (CI/CD compatible).

        Tries prompt_toolkit first, falls back to input() if unavailable.
        """
        # Try Rich interactive prompt
        try:
            from rich.prompt import Prompt

            # Show table
            self._show_provider_table(available_providers, descriptions)

            # Get choice
            choice = Prompt.ask(
                "Select provider",
                choices=[str(i) for i in range(1, len(available_providers) + 1)],
                default="1"
            )

            return available_providers[int(choice) - 1]

        except (ImportError, OSError) as e:
            # Fallback to simple input()
            logger.warning(
                "interactive_prompt_unavailable",
                error=str(e),
                fallback="input()"
            )

            # Simple text-based prompt
            print("\nAvailable Providers:")
            for i, provider in enumerate(available_providers, 1):
                desc = descriptions.get(provider, "")
                print(f"  [{i}] {provider} - {desc}")

            while True:
                choice = input(f"\nSelect provider [1-{len(available_providers)}]: ")
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_providers):
                        return available_providers[idx]
                    print(f"Invalid choice. Must be 1-{len(available_providers)}")
                except ValueError:
                    print("Invalid input. Enter a number.")

    def _show_provider_table(self, providers: List[str], descriptions: Dict[str, str]):
        """Show provider table (only if Rich available)."""
        try:
            from rich.table import Table

            table = Table(title="Available Providers")
            table.add_column("Option", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Description")

            for i, provider in enumerate(providers, 1):
                desc = descriptions.get(provider, "")
                table.add_row(str(i), provider, desc)

            self.console.print(table)

        except (ImportError, OSError):
            # Skip table, will use text output in prompt method
            pass
```

**Key Points**:
1. **Always import inside methods**, not at module level
2. **Catch both `ImportError` and `OSError`** (OSError = no TTY)
3. **Provide simple text fallback** for headless environments
4. **Log the fallback** for debugging

### 9.2 Headless Testing

**Dockerfile for Headless Environment**:
```dockerfile
# tests/docker/headless/Dockerfile

FROM python:3.11-slim

# Don't allocate TTY
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Run tests
CMD ["pytest", "tests/cli/test_interactive_prompter.py", "-v"]
```

**GitHub Actions Job**:
```yaml
# .github/workflows/test.yml

jobs:
  test-headless:
    name: Test Headless Environment
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Build headless Docker image
        run: docker build -t gao-dev-headless -f tests/docker/headless/Dockerfile .

      - name: Run headless tests
        run: docker run --rm gao-dev-headless

      - name: Test env var bypass
        run: |
          docker run --rm \
            -e AGENT_PROVIDER=claude-code \
            -e ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }} \
            gao-dev-headless \
            python -c "from gao_dev.cli.chat_repl import ChatREPL; print('SUCCESS')"
```

**Test Cases**:
```python
# tests/cli/test_interactive_prompter.py

def test_lazy_import_fallback(monkeypatch):
    """Test that lazy import fallback works when prompt_toolkit unavailable."""
    # Simulate ImportError
    import sys
    monkeypatch.setitem(sys.modules, 'prompt_toolkit', None)

    prompter = InteractivePrompter(Console())

    # Should fall back to input() without crashing
    with patch('builtins.input', return_value='1'):
        provider = prompter.prompt_provider(
            ['claude-code', 'opencode'],
            {'claude-code': 'Claude Code CLI'}
        )

    assert provider == 'claude-code'

def test_lazy_import_oserror(monkeypatch):
    """Test that OSError (no TTY) is handled."""
    # Simulate OSError
    def mock_import(*args, **kwargs):
        raise OSError("No TTY available")

    monkeypatch.setattr('builtins.__import__', mock_import)

    prompter = InteractivePrompter(Console())

    # Should fall back to input() without crashing
    with patch('builtins.input', return_value='2'):
        provider = prompter.prompt_provider(
            ['claude-code', 'opencode'],
            {'opencode': 'OpenCode CLI'}
        )

    assert provider == 'opencode'
```

### 9.3 Environment Variable Bypass

**Always check env vars before prompting**:

```python
# ProviderSelector.select_provider()

def select_provider(self) -> Dict[str, Any]:
    """Select provider with env var precedence."""
    # Priority 1: Environment variable
    env_config = self.use_environment_variable()
    if env_config:
        logger.info("using_env_var_provider", provider=env_config['provider'])
        return env_config

    # Priority 2: Saved preferences
    if self.has_saved_preferences():
        # ... prompt to use saved

    # Priority 3: Interactive prompts (only if no env var!)
    return self._interactive_selection()
```

---

## Appendices

### Appendix A: Configuration Examples

**Example 1: Claude Code (Cloud)**
```yaml
version: "1.0"
provider:
  name: "claude-code"
  model: "sonnet-4.5"
  config:
    api_key_env: "ANTHROPIC_API_KEY"
    timeout: 3600
```

**Example 2: OpenCode (Local Ollama)**
```yaml
version: "1.0"
provider:
  name: "opencode"
  model: "deepseek-r1"
  config:
    ai_provider: "ollama"
    use_local: true
    timeout: 3600
```

**Example 3: OpenCode (Cloud Anthropic)**
```yaml
version: "1.0"
provider:
  name: "opencode"
  model: "sonnet-4.5"
  config:
    ai_provider: "anthropic"
    use_local: false
    api_key_env: "ANTHROPIC_API_KEY"
    timeout: 3600
```

**Example 4: Direct API**
```yaml
version: "1.0"
provider:
  name: "direct-api-anthropic"
  model: "sonnet-4.5"
  config:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: null
    timeout: 3600
    max_retries: 3
```

### Appendix B: CLI Check Commands

```bash
# Check if Claude Code installed
which claude  # Unix/Mac
where claude  # Windows

# Check if OpenCode installed
which opencode
where opencode

# Check if Ollama installed
which ollama
where ollama

# List Ollama models
ollama list

# Test provider
gao-dev providers validate claude-code
```

### Appendix C: Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AGENT_PROVIDER` | Override provider selection | `export AGENT_PROVIDER=opencode` |
| `SKIP_PROVIDER_SELECTION` | Skip prompts, use defaults | `export SKIP_PROVIDER_SELECTION=1` |
| `ANTHROPIC_API_KEY` | API key for Anthropic | `export ANTHROPIC_API_KEY=sk-ant-...` |
| `OPENAI_API_KEY` | API key for OpenAI | `export OPENAI_API_KEY=sk-...` |

---

**Document Version**: 1.0
**Last Updated**: 2025-01-12
**Next Review**: After implementation completion
