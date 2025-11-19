"""Configuration data models for TUI wizard.

This module provides dataclasses for storing wizard configuration
collected during the onboarding process.

Epic 41: Streamlined Onboarding
Story 41.1: TUI Wizard Implementation
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderInfo:
    """Information about an AI provider.

    Attributes:
        name: Provider identifier (e.g., 'claude-code', 'opencode-sdk')
        description: Human-readable description
        requires_api_key: Whether this provider requires an API key
        api_key_env: Environment variable name for API key

    Example:
        ```python
        provider = ProviderInfo(
            name='claude-code',
            description='Anthropic Claude via Claude Code CLI',
            requires_api_key=True,
            api_key_env='ANTHROPIC_API_KEY'
        )
        ```
    """

    name: str
    description: str
    requires_api_key: bool
    api_key_env: str = ""


@dataclass
class GitConfig:
    """Git configuration for the project.

    Attributes:
        user_name: Git user.name
        user_email: Git user.email
        init_git: Whether to initialize a git repository

    Example:
        ```python
        git_config = GitConfig(
            user_name='John Doe',
            user_email='john@example.com',
            init_git=True
        )
        ```
    """

    user_name: str = ""
    user_email: str = ""
    init_git: bool = True


@dataclass
class ProjectConfig:
    """Project configuration collected in wizard.

    Attributes:
        name: Project name (default: folder name)
        project_type: Detected or selected project type
        description: Project description

    Example:
        ```python
        project_config = ProjectConfig(
            name='my-app',
            project_type='python',
            description='A sample Python application'
        )
        ```
    """

    name: str = ""
    project_type: str = ""
    description: str = ""


@dataclass
class WizardConfig:
    """Complete configuration collected by TUI wizard.

    Contains all data gathered during the 4-step onboarding wizard:
    1. Project configuration
    2. Git configuration
    3. Provider selection
    4. Credentials

    Attributes:
        project: Project configuration
        git: Git configuration
        provider_name: Selected provider name
        model: Selected model name
        api_key: API key (if entered)
        provider_config: Additional provider-specific config

    Example:
        ```python
        config = WizardConfig(
            project=ProjectConfig(name='my-app', project_type='python'),
            git=GitConfig(user_name='John', user_email='john@example.com'),
            provider_name='claude-code',
            model='sonnet-4.5',
            api_key='sk-ant-...',
            provider_config={'ai_provider': 'anthropic'}
        )
        ```
    """

    project: ProjectConfig = field(default_factory=ProjectConfig)
    git: GitConfig = field(default_factory=GitConfig)
    provider_name: str = ""
    model: str = ""
    api_key: str = ""
    provider_config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the config
        """
        return {
            "project": {
                "name": self.project.name,
                "type": self.project.project_type,
                "description": self.project.description,
            },
            "git": {
                "user_name": self.git.user_name,
                "user_email": self.git.user_email,
                "init_git": self.git.init_git,
            },
            "provider": {
                "name": self.provider_name,
                "model": self.model,
                "config": self.provider_config,
            },
        }


# Provider definitions
PROVIDERS = [
    ProviderInfo(
        name="claude-code",
        description="Anthropic Claude via Claude Code CLI",
        requires_api_key=True,
        api_key_env="ANTHROPIC_API_KEY",
    ),
    ProviderInfo(
        name="opencode-sdk",
        description="OpenCode with cloud or local models",
        requires_api_key=False,  # Depends on model choice
        api_key_env="",
    ),
    ProviderInfo(
        name="direct-api",
        description="Direct Anthropic/OpenAI/Google API",
        requires_api_key=True,
        api_key_env="ANTHROPIC_API_KEY",
    ),
    ProviderInfo(
        name="ollama",
        description="Free local models (llama2, deepseek)",
        requires_api_key=False,
        api_key_env="",
    ),
]

# Provider name to ProviderInfo mapping
PROVIDER_MAP = {p.name: p for p in PROVIDERS}

# Default models per provider
DEFAULT_MODELS = {
    "claude-code": "sonnet-4.5",
    "opencode-sdk": "deepseek-r1",
    "direct-api": "claude-3-5-sonnet-20241022",
    "ollama": "deepseek-r1",
}

# Available models per provider
AVAILABLE_MODELS = {
    "claude-code": ["sonnet-4.5", "opus-4", "haiku-3.5"],
    "opencode-sdk": ["deepseek-r1", "llama2", "codellama"],
    "direct-api": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "gpt-4-turbo",
        "gemini-pro",
    ],
    "ollama": ["deepseek-r1", "llama2", "codellama", "mistral"],
}
