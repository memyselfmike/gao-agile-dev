# Interactive Provider Selection - API Reference

**Epic**: Epic 35 - Interactive Provider Selection at Startup
**Version**: 1.0
**Last Updated**: 2025-01-12

---

## Table of Contents

- [ProviderSelector](#providerselector)
- [PreferenceManager](#preferencemanager)
- [ProviderValidator](#providervalidator)
- [InteractivePrompter](#interactiveprompter)
- [Data Models](#data-models)
- [Exceptions](#exceptions)

---

## ProviderSelector

**File**: `gao_dev/cli/provider_selector.py`

Orchestrates provider selection flow by coordinating preferences, prompts, and validation.

### Class: `ProviderSelector`

```python
class ProviderSelector:
    """
    Orchestrates provider selection for REPL startup.

    Priority order:
    1. AGENT_PROVIDER environment variable
    2. Saved preferences (if exist and user confirms)
    3. Interactive prompts
    4. Hardcoded defaults
    """
```

#### Constructor

```python
def __init__(
    self,
    project_root: Path,
    console: Console,
    preference_manager: Optional[PreferenceManager] = None,
    interactive_prompter: Optional[InteractivePrompter] = None,
    provider_validator: Optional[ProviderValidator] = None,
) -> None:
    """
    Initialize ProviderSelector with dependencies.

    Args:
        project_root: Project root directory
        console: Rich Console for formatted output
        preference_manager: Optional PreferenceManager (created if None)
        interactive_prompter: Optional InteractivePrompter (created if None)
        provider_validator: Optional ProviderValidator (created if None)
    """
```

#### Methods

##### `select_provider()`

```python
def select_provider(self) -> Dict[str, Any]:
    """
    Select provider using priority: env var > saved prefs > interactive.

    Returns:
        Dict with keys: provider, model, config

    Raises:
        ProviderSelectionCancelled: User cancelled selection (Ctrl+C)
        ProviderValidationFailed: Selected provider failed validation

    Example:
        >>> config = selector.select_provider()
        >>> print(config)
        {
            'provider': 'opencode',
            'model': 'deepseek-r1',
            'config': {'ai_provider': 'ollama', 'use_local': True}
        }
    """
```

##### `has_saved_preferences()`

```python
def has_saved_preferences(self) -> bool:
    """
    Check if saved preferences exist and are valid.

    Returns:
        True if valid saved preferences exist, False otherwise
    """
```

##### `use_environment_variable()`

```python
def use_environment_variable(self) -> Optional[Dict[str, Any]]:
    """
    Get provider config from AGENT_PROVIDER environment variable.

    Supports formats:
    - "provider" (e.g., "claude-code")
    - "provider:model" (e.g., "opencode:deepseek-r1")

    Returns:
        Provider config dict if env var set, None otherwise

    Example:
        >>> os.environ['AGENT_PROVIDER'] = 'claude-code'
        >>> config = selector.use_environment_variable()
        >>> print(config['provider'])
        'claude-code'
    """
```

---

## PreferenceManager

**File**: `gao_dev/cli/preference_manager.py`

Manages provider preference persistence with security measures.

### Class: `PreferenceManager`

```python
class PreferenceManager:
    """
    Manages provider preference persistence.

    SECURITY NOTE:
    - Uses yaml.safe_dump() to prevent code execution
    - Sanitizes all string input before saving
    - Only allows safe characters (alphanumeric, dash, underscore, dot, etc.)
    """
```

#### Constructor

```python
def __init__(self, project_root: Path) -> None:
    """
    Initialize PreferenceManager with project root.

    Args:
        project_root: Project root directory
    """
```

#### Methods

##### `load_preferences()`

```python
def load_preferences(self) -> Optional[Dict[str, Any]]:
    """
    Load saved preferences from file.

    Returns None if file doesn't exist or is invalid. Never crashes.
    If main file corrupt and backup exists, attempts to load from backup.

    Returns:
        Preferences dict, or None if file doesn't exist or is invalid

    Format:
        {
            'version': '1.0.0',
            'provider': {
                'name': 'opencode',
                'model': 'deepseek-r1',
                'config': {...}
            },
            'metadata': {
                'last_updated': '2025-01-12T10:30:00Z',
                'cli_version': '1.2.3'
            }
        }
    """
```

##### `save_preferences()`

```python
def save_preferences(self, preferences: Dict[str, Any]) -> None:
    """
    Save preferences to file with security measures.

    SECURITY:
    1. Sanitizes all input before saving
    2. Uses yaml.safe_dump() to prevent code execution
    3. Sets restrictive file permissions (0600)
    4. Creates backup before overwriting
    5. Uses atomic write (tmp file -> replace)

    Args:
        preferences: Preferences dict to save

    Raises:
        PreferenceSaveError: If save fails
    """
```

##### `has_preferences()`

```python
def has_preferences(self) -> bool:
    """
    Check if preferences file exists and is valid.

    Returns:
        True if valid preferences file exists, False otherwise
    """
```

##### `validate_preferences()`

```python
def validate_preferences(self, preferences: Dict[str, Any]) -> bool:
    """
    Validate preference structure.

    Checks:
    - Required keys present: version, provider, metadata
    - Version format is semantic versioning (X.Y.Z)
    - Timestamp format is ISO 8601
    - Provider name is string
    - Structure is correct

    Args:
        preferences: Preferences dict to validate

    Returns:
        True if valid, False otherwise
    """
```

##### `delete_preferences()`

```python
def delete_preferences(self) -> None:
    """
    Delete preferences file (for testing/reset).

    Also deletes backup and temp files if they exist.
    """
```

##### `get_default_preferences()`

```python
def get_default_preferences(self) -> Dict[str, Any]:
    """
    Get default preferences for fallback.

    Returns:
        Default preferences (claude-code, sonnet-4.5)
    """
```

---

## ProviderValidator

**File**: `gao_dev/cli/provider_validator.py`

Validates provider configurations with actionable error messages.

### Class: `ProviderValidator`

```python
class ProviderValidator:
    """
    Validates provider configuration.

    Checks CLI availability, API keys, connectivity, and provides
    actionable error messages with fix suggestions.
    """
```

#### Constructor

```python
def __init__(self, console: Console) -> None:
    """
    Initialize ProviderValidator with console.

    Args:
        console: Rich Console for output
    """
```

#### Methods

##### `validate_configuration()`

```python
async def validate_configuration(
    self, provider_name: str, config: Dict[str, Any]
) -> ValidationResult:
    """
    Validate provider configuration.

    Checks:
    - Provider exists in ProviderFactory registry
    - CLI available (if CLI-based provider)
    - API key set (if direct API provider)
    - Model supported by provider
    - Basic connectivity test (optional)

    Args:
        provider_name: Provider identifier
        config: Provider configuration dict

    Returns:
        ValidationResult with success/failure and messages

    Example:
        >>> result = await validator.validate_configuration(
        ...     'claude-code',
        ...     {'api_key_env': 'ANTHROPIC_API_KEY'}
        ... )
        >>> if not result.success:
        ...     for suggestion in result.suggestions:
        ...         print(f"  - {suggestion}")
    """
```

##### `check_cli_available()`

```python
async def check_cli_available(self, cli_name: str) -> bool:
    """
    Check if CLI tool is in PATH.

    Cross-platform: uses shutil.which() on Unix, where on Windows.

    Args:
        cli_name: Name of CLI (e.g., 'claude', 'opencode', 'ollama')

    Returns:
        True if CLI available, False otherwise
    """
```

##### `check_ollama_models()`

```python
async def check_ollama_models(self) -> List[str]:
    """
    Get list of available Ollama models.

    Runs `ollama list` command and parses output.
    Returns empty list if Ollama unavailable.

    Returns:
        List of model names, or empty list if Ollama unavailable

    Example:
        >>> models = await validator.check_ollama_models()
        >>> print(models)
        ['deepseek-r1', 'llama2', 'codellama']
    """
```

##### `suggest_fixes()`

```python
def suggest_fixes(self, provider_name: str) -> List[str]:
    """
    Provide installation/fix suggestions for provider.

    Args:
        provider_name: Provider that failed validation

    Returns:
        List of suggestion strings

    Example:
        >>> suggestions = validator.suggest_fixes('claude-code')
        >>> for s in suggestions:
        ...     print(s)
        'Install Claude Code CLI: npm install -g @anthropic/claude-code'
        'Set API key: export ANTHROPIC_API_KEY=sk-ant-...'
        'Verify installation: claude --version'
    """
```

---

## InteractivePrompter

**File**: `gao_dev/cli/interactive_prompter.py`

Handles interactive prompts with Rich formatting.

### Class: `InteractivePrompter`

```python
class InteractivePrompter:
    """
    Handles interactive prompts for provider selection.

    Uses Rich for formatted output and prompt_toolkit for input.
    Falls back to simple input() if Rich/prompt_toolkit unavailable (CI/CD).
    """
```

#### Constructor

```python
def __init__(self, console: Console) -> None:
    """
    Initialize InteractivePrompter with Rich console.

    Args:
        console: Rich Console for formatted output
    """
```

#### Methods

##### `prompt_provider()`

```python
def prompt_provider(
    self,
    available_providers: List[str],
    descriptions: Dict[str, str]
) -> str:
    """
    Prompt user to select a provider.

    Shows formatted table of providers with descriptions, then prompts
    for selection. Falls back to simple text if Rich unavailable.

    Args:
        available_providers: List of provider names
        descriptions: Provider name -> description mapping

    Returns:
        Selected provider name

    Raises:
        KeyboardInterrupt: User pressed Ctrl+C

    Example:
        >>> provider = prompter.prompt_provider(
        ...     ['claude-code', 'opencode'],
        ...     {'claude-code': 'Claude Code CLI (Anthropic)'}
        ... )
        >>> print(provider)
        'claude-code'
    """
```

##### `prompt_opencode_config()`

```python
def prompt_opencode_config(self) -> Dict[str, Any]:
    """
    Prompt for OpenCode-specific configuration.

    Asks:
    - Local model (Ollama) vs cloud?
    - If cloud: which provider (anthropic/openai/google)?

    Returns:
        Dict with OpenCode-specific config

    Example:
        >>> config = prompter.prompt_opencode_config()
        >>> print(config)
        {'ai_provider': 'ollama', 'use_local': True}
    """
```

##### `prompt_model()`

```python
def prompt_model(
    self,
    available_models: List[str],
    descriptions: Optional[Dict[str, str]] = None
) -> str:
    """
    Prompt user to select a model.

    Shows formatted table of models with optional descriptions.

    Args:
        available_models: List of model names
        descriptions: Optional model name -> description mapping

    Returns:
        Selected model name
    """
```

##### `prompt_save_preferences()`

```python
def prompt_save_preferences(self) -> bool:
    """
    Ask if user wants to save preferences.

    Returns:
        True if user wants to save, False otherwise
    """
```

##### `prompt_use_saved()`

```python
def prompt_use_saved(self, saved_config: Dict[str, Any]) -> str:
    """
    Ask if user wants to use saved configuration.

    Args:
        saved_config: Previously saved configuration

    Returns:
        'y' (yes), 'n' (no), or 'c' (change specific settings)
    """
```

##### `show_error()`

```python
def show_error(self, message: str, suggestions: Optional[List[str]] = None) -> None:
    """
    Display error message with optional suggestions.

    Args:
        message: Error message
        suggestions: Optional list of suggestion strings
    """
```

##### `show_success()`

```python
def show_success(self, message: str) -> None:
    """
    Display success message.

    Args:
        message: Success message
    """
```

---

## Data Models

**File**: `gao_dev/cli/models.py`

### `ProviderConfig`

```python
@dataclass
class ProviderConfig:
    """
    Provider configuration returned by ProviderSelector.

    Attributes:
        provider_name: Provider identifier (e.g., 'claude-code')
        model: Model name (e.g., 'sonnet-4.5')
        config: Provider-specific configuration dict
        validated: Whether provider has been validated
        validation_timestamp: When provider was last validated
    """
    provider_name: str
    model: str
    config: Dict[str, Any] = field(default_factory=dict)
    validated: bool = False
    validation_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for ProcessExecutor."""
```

### `ProviderPreferences`

```python
@dataclass
class ProviderPreferences:
    """
    Saved provider preferences.

    Attributes:
        version: Preferences file format version
        last_updated: When preferences were last updated
        provider: ProviderConfig for selected provider
        metadata: Additional metadata
    """
    version: str
    last_updated: datetime
    provider: ProviderConfig
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-serializable dict."""

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'ProviderPreferences':
        """Create from loaded YAML dict."""
```

### `ValidationResult`

```python
@dataclass
class ValidationResult:
    """
    Result of provider validation.

    Attributes:
        success: True if validation passed, False otherwise
        provider_name: Name of provider validated
        messages: List of informational messages
        warnings: List of warning messages
        suggestions: List of suggestion strings for fixing issues
        validation_time_ms: Time taken for validation in milliseconds
    """
    success: bool
    provider_name: str
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validation_time_ms: float = 0.0

    def add_message(self, message: str) -> None:
        """Add informational message."""

    def add_warning(self, warning: str) -> None:
        """Add warning message."""

    def add_suggestion(self, suggestion: str) -> None:
        """Add actionable suggestion."""
```

---

## Exceptions

**File**: `gao_dev/cli/exceptions.py`

### Exception Hierarchy

```python
class ProviderSelectionError(Exception):
    """Base exception for provider selection operations."""

class ProviderSelectionCancelled(ProviderSelectionError):
    """Raised when user cancels provider selection (Ctrl+C)."""

class ProviderValidationFailed(ProviderSelectionError):
    """Raised when provider configuration validation fails."""

    def __init__(
        self,
        message: str,
        provider_name: str = "",
        suggestions: List[str] | None = None
    ):
        super().__init__(message)
        self.provider_name = provider_name
        self.suggestions = suggestions or []

class PreferenceSaveError(ProviderSelectionError):
    """Raised when saving preferences fails."""

class PreferenceLoadError(ProviderSelectionError):
    """Raised when loading preferences fails."""
```

### Usage Examples

```python
# Catching specific exceptions
try:
    provider = selector.select_provider()
except ProviderSelectionCancelled:
    print("User cancelled selection")
    sys.exit(0)
except ProviderValidationFailed as e:
    print(f"Validation failed: {e}")
    for suggestion in e.suggestions:
        print(f"  - {suggestion}")
except ProviderSelectionError as e:
    print(f"Selection error: {e}")
```

---

## Constants

**File**: `gao_dev/cli/provider_selector.py`

```python
# Available providers
AVAILABLE_PROVIDERS = ["claude-code", "opencode", "direct-api-anthropic"]

# Provider descriptions
PROVIDER_DESCRIPTIONS = {
    "claude-code": "Claude Code CLI (Anthropic)",
    "opencode": "OpenCode CLI (Multi-provider)",
    "direct-api-anthropic": "Direct Anthropic API",
}

# Default models per provider
DEFAULT_MODELS = {
    "claude-code": "sonnet-4.5",
    "opencode": "deepseek-r1",
    "direct-api-anthropic": "claude-3-5-sonnet-20241022",
}

# Available models per provider
AVAILABLE_MODELS = {
    "claude-code": ["sonnet-4.5", "opus-4", "haiku-3.5"],
    "opencode": ["deepseek-r1", "llama2", "codellama"],
    "direct-api-anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307",
    ],
}
```

---

## Usage Examples

### Complete Provider Selection

```python
from pathlib import Path
from rich.console import Console
from gao_dev.cli.provider_selector import ProviderSelector
from gao_dev.cli.exceptions import ProviderSelectionCancelled

console = Console()
project_root = Path.cwd()

selector = ProviderSelector(project_root, console)

try:
    provider_config = selector.select_provider()

    print(f"Selected provider: {provider_config['provider']}")
    print(f"Model: {provider_config['model']}")
    print(f"Config: {provider_config['config']}")

    # Use config to create ProcessExecutor
    # executor = ProcessExecutor(project_root, **provider_config)

except ProviderSelectionCancelled:
    print("User cancelled provider selection")
    sys.exit(0)
except Exception as e:
    print(f"Provider selection failed: {e}")
    sys.exit(1)
```

### Manual Preference Management

```python
from pathlib import Path
from gao_dev.cli.preference_manager import PreferenceManager

manager = PreferenceManager(Path.cwd())

# Load preferences
prefs = manager.load_preferences()
if prefs:
    print(f"Provider: {prefs['provider']['name']}")
else:
    print("No saved preferences")

# Save new preferences
new_prefs = {
    'version': '1.0.0',
    'provider': {
        'name': 'opencode',
        'model': 'deepseek-r1',
        'config': {'ai_provider': 'ollama', 'use_local': True}
    },
    'metadata': {
        'last_updated': '2025-01-12T10:30:00Z',
        'cli_version': '1.0.0'
    }
}

manager.save_preferences(new_prefs)
```

### Provider Validation

```python
import asyncio
from rich.console import Console
from gao_dev.cli.provider_validator import ProviderValidator

console = Console()
validator = ProviderValidator(console)

async def validate():
    result = await validator.validate_configuration(
        'claude-code',
        {'api_key_env': 'ANTHROPIC_API_KEY'}
    )

    if result.success:
        print(f"✓ Validation passed in {result.validation_time_ms:.1f}ms")
    else:
        print("✗ Validation failed:")
        for warning in result.warnings:
            print(f"  - {warning}")
        print("\nSuggestions:")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")

asyncio.run(validate())
```

---

## Related Documentation

- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md) for end-user instructions
- **Testing Guide**: [TESTING.md](TESTING.md) for testing the API
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for custom providers
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) for system design

---

**Version**: 1.0
**Last Updated**: 2025-01-12
**Epic**: 35 - Interactive Provider Selection at Startup
