"""Data models for provider selection.

Epic 35: Interactive Provider Selection at Startup
Story 35.1: Project Setup & Architecture
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


@dataclass
class ProviderConfig:
    """
    Provider configuration returned by ProviderSelector.

    Attributes:
        provider_name: Provider identifier (e.g., 'claude-code', 'opencode')
        model: Model name (e.g., 'sonnet-4.5', 'deepseek-r1')
        config: Provider-specific configuration dict
        validated: Whether provider has been validated
        validation_timestamp: When provider was last validated

    Example:
        ```python
        config = ProviderConfig(
            provider_name='opencode',
            model='deepseek-r1',
            config={'ai_provider': 'ollama', 'use_local': True},
            validated=True,
            validation_timestamp=datetime.now()
        )
        ```
    """

    provider_name: str
    model: str
    config: Dict[str, Any] = field(default_factory=dict)
    validated: bool = False
    validation_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dict for ProcessExecutor.

        Returns:
            Dict with provider, model, config keys
        """
        return {
            'provider': self.provider_name,
            'model': self.model,
            'config': self.config
        }


@dataclass
class ProviderPreferences:
    """
    Saved provider preferences.

    Represents the structure of .gao-dev/provider_preferences.yaml.

    Attributes:
        version: Preferences file format version
        last_updated: When preferences were last updated
        provider: ProviderConfig for selected provider
        metadata: Additional metadata (CLI version, validation status, etc.)

    Example:
        ```python
        prefs = ProviderPreferences(
            version='1.0',
            last_updated=datetime.now(),
            provider=ProviderConfig(...),
            metadata={'cli_version': '1.2.3'}
        )
        ```
    """

    version: str
    last_updated: datetime
    provider: ProviderConfig
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Convert to YAML-serializable dict.

        Returns:
            Dict suitable for yaml.safe_dump()
        """
        return {
            'version': self.version,
            'last_updated': self.last_updated.isoformat(),
            'provider': {
                'name': self.provider.provider_name,
                'model': self.provider.model,
                'config': self.provider.config,
            },
            'metadata': self.metadata
        }

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'ProviderPreferences':
        """
        Create from loaded YAML dict.

        Args:
            data: Dict loaded from YAML file

        Returns:
            ProviderPreferences instance

        Raises:
            KeyError: If required keys missing
            ValueError: If data format invalid
        """
        provider_data = data['provider']
        provider = ProviderConfig(
            provider_name=provider_data['name'],
            model=provider_data['model'],
            config=provider_data.get('config', {}),
            validated=False,  # Re-validate on load
            validation_timestamp=datetime.now()
        )

        return cls(
            version=data['version'],
            last_updated=datetime.fromisoformat(data['last_updated']),
            provider=provider,
            metadata=data.get('metadata', {})
        )


@dataclass
class ValidationResult:
    """Result of provider validation.

    Represents the outcome of validating a provider configuration, including
    success status, messages, warnings, and actionable suggestions.

    Attributes:
        success: True if validation passed, False otherwise
        provider_name: Name of provider validated
        messages: List of informational messages
        warnings: List of warning messages
        suggestions: List of suggestion strings for fixing issues

    Example:
        ```python
        result = ValidationResult(
            success=False,
            provider_name='claude-code',
            messages=['Checking CLI availability...'],
            warnings=['ANTHROPIC_API_KEY not set'],
            suggestions=[
                'Install Claude Code: https://...',
                'Set API key: export ANTHROPIC_API_KEY=sk-...'
            ]
        )
        ```
    """

    success: bool
    provider_name: str
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def add_message(self, message: str) -> None:
        """Add informational message.

        Args:
            message: Informational message
        """
        self.messages.append(message)

    def add_warning(self, warning: str) -> None:
        """Add warning message.

        Args:
            warning: Warning message
        """
        self.warnings.append(warning)

    def add_suggestion(self, suggestion: str) -> None:
        """Add actionable suggestion.

        Args:
            suggestion: Suggestion string
        """
        self.suggestions.append(suggestion)
