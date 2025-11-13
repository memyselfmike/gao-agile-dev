"""Custom exceptions for provider selection.

This module defines the exception hierarchy for provider selection operations,
preference management, and validation.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""


class ProviderSelectionError(Exception):
    """Base exception for provider selection operations.

    Raised when any error occurs during provider selection, validation,
    or preference management. All specific provider-related exceptions
    should inherit from this base class.

    Example:
        ```python
        try:
            provider = selector.select_provider()
        except ProviderSelectionError as e:
            logger.error("Provider selection failed", error=str(e))
        ```
    """

    pass


class ProviderSelectionCancelled(ProviderSelectionError):
    """Raised when user cancels provider selection.

    This exception is raised when the user explicitly cancels the provider
    selection process, typically by pressing Ctrl+C or choosing to exit.
    This is not an error condition but a normal exit path.

    Example:
        ```python
        try:
            provider = prompter.prompt_provider(providers, descriptions)
        except KeyboardInterrupt:
            raise ProviderSelectionCancelled("User cancelled selection")
        ```
    """

    pass


class ProviderValidationFailed(ProviderSelectionError):
    """Raised when provider configuration validation fails.

    This exception is raised when a provider fails validation checks such as:
    - CLI not available in PATH
    - API key not set or invalid
    - Model not supported by provider
    - Connectivity test failed

    Attributes:
        provider_name: Name of provider that failed validation
        suggestions: List of actionable suggestions to fix the issue

    Example:
        ```python
        raise ProviderValidationFailed(
            "claude-code validation failed: CLI not found",
            provider_name="claude-code",
            suggestions=[
                "Install Claude Code CLI: https://...",
                "Add to PATH: export PATH=$PATH:/path/to/claude"
            ]
        )
        ```
    """

    def __init__(
        self, message: str, provider_name: str = "", suggestions: list[str] | None = None
    ):
        """Initialize ProviderValidationFailed exception.

        Args:
            message: Error message
            provider_name: Name of provider that failed validation
            suggestions: List of actionable suggestions to fix the issue
        """
        super().__init__(message)
        self.provider_name = provider_name
        self.suggestions = suggestions or []


class PreferenceSaveError(ProviderSelectionError):
    """Raised when saving preferences fails.

    This exception is raised when the system fails to save user preferences
    to the .gao-dev/provider_preferences.yaml file due to:
    - File permission issues
    - Disk full
    - Invalid data structure
    - YAML serialization errors

    Example:
        ```python
        try:
            manager.save_preferences(preferences)
        except PreferenceSaveError as e:
            logger.error("Failed to save preferences", error=str(e))
            # Continue without saving (use in-memory config)
        ```
    """

    pass


class PreferenceLoadError(ProviderSelectionError):
    """Raised when loading preferences fails.

    This exception is raised when the system fails to load saved preferences
    from the .gao-dev/provider_preferences.yaml file due to:
    - File not found (handled gracefully, not usually an error)
    - File corrupted or invalid YAML
    - Invalid data structure
    - Schema validation failure

    Note: If the file simply doesn't exist, PreferenceManager.load_preferences()
    returns None instead of raising this exception. This exception is only
    raised for corrupted or invalid preference files.

    Example:
        ```python
        try:
            prefs = manager.load_preferences()
        except PreferenceLoadError as e:
            logger.warning("Corrupted preferences file", error=str(e))
            # Delete corrupted file and start fresh
            manager.delete_preferences()
        ```
    """

    pass
