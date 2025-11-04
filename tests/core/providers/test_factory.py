"""Unit tests for ProviderFactory."""

import pytest
from pathlib import Path

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.models import AgentContext
from gao_dev.core.providers.exceptions import (
    ProviderNotFoundError,
    ProviderCreationError,
    ProviderRegistrationError,
    DuplicateProviderError
)


class MockProvider(IAgentProvider):
    """Mock provider for testing."""

    def __init__(self, config_value: str = "default"):
        self.config_value = config_value
        self._initialized = False

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
        yield "mock result"

    def supports_tool(self, tool_name: str) -> bool:
        return True

    def get_supported_models(self):
        return ["mock-model"]

    def translate_model_name(self, canonical_name: str) -> str:
        return canonical_name

    async def validate_configuration(self) -> bool:
        return True

    def get_configuration_schema(self):
        return {}

    async def initialize(self) -> None:
        self._initialized = True

    async def cleanup(self) -> None:
        self._initialized = False


class InvalidProvider:
    """Invalid provider (doesn't implement IAgentProvider)."""
    pass


class TestProviderFactory:
    """Test ProviderFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ProviderFactory()

    def test_factory_initialization(self):
        """Test factory initializes with built-in providers."""
        providers = self.factory.list_providers()
        assert "claude-code" in providers

    def test_create_claude_code_provider(self):
        """Test creating ClaudeCodeProvider."""
        provider = self.factory.create_provider("claude-code")
        assert provider.name == "claude-code"
        assert provider.version is not None

    def test_create_provider_with_config(self):
        """Test creating provider with configuration."""
        # Register mock provider
        self.factory.register_provider("mock", MockProvider)

        # Create with config
        provider = self.factory.create_provider(
            "mock",
            config={"config_value": "test"}
        )

        assert provider.config_value == "test"

    def test_create_provider_not_found(self):
        """Test creating non-existent provider raises error."""
        with pytest.raises(ProviderNotFoundError) as exc_info:
            self.factory.create_provider("non-existent")

        assert "non-existent" in str(exc_info.value)
        assert "Available providers" in str(exc_info.value)

    def test_register_provider(self):
        """Test registering custom provider."""
        self.factory.register_provider("mock", MockProvider)
        assert "mock" in self.factory.list_providers()

    def test_register_invalid_provider_raises_error(self):
        """Test registering invalid provider raises error."""
        with pytest.raises(ProviderRegistrationError) as exc_info:
            self.factory.register_provider("invalid", InvalidProvider)

        assert "must implement IAgentProvider" in str(exc_info.value)

    def test_register_duplicate_provider_raises_error(self):
        """Test registering duplicate provider raises error."""
        self.factory.register_provider("mock", MockProvider)

        with pytest.raises(DuplicateProviderError):
            self.factory.register_provider("mock", MockProvider)

    def test_register_duplicate_with_override(self):
        """Test registering duplicate with allow_override."""
        self.factory.register_provider("mock", MockProvider)
        # Should not raise
        self.factory.register_provider("mock", MockProvider, allow_override=True)

    def test_list_providers(self):
        """Test listing providers."""
        providers = self.factory.list_providers()
        assert isinstance(providers, list)
        assert "claude-code" in providers
        assert providers == sorted(providers)  # Should be sorted

    def test_provider_exists(self):
        """Test checking provider existence."""
        assert self.factory.provider_exists("claude-code") is True
        assert self.factory.provider_exists("non-existent") is False

    def test_provider_exists_case_insensitive(self):
        """Test provider_exists is case-insensitive."""
        assert self.factory.provider_exists("CLAUDE-CODE") is True
        assert self.factory.provider_exists("Claude-Code") is True

    def test_get_provider_class(self):
        """Test getting provider class."""
        from gao_dev.core.providers.claude_code import ClaudeCodeProvider

        provider_class = self.factory.get_provider_class("claude-code")
        assert provider_class is ClaudeCodeProvider

    def test_get_provider_class_not_found(self):
        """Test getting non-existent provider class raises error."""
        with pytest.raises(ProviderNotFoundError):
            self.factory.get_provider_class("non-existent")

    def test_factory_repr(self):
        """Test factory string representation."""
        repr_str = repr(self.factory)
        assert "ProviderFactory" in repr_str
        assert "claude-code" in repr_str

    def test_create_provider_case_insensitive(self):
        """Test provider creation is case-insensitive."""
        provider1 = self.factory.create_provider("claude-code")
        provider2 = self.factory.create_provider("CLAUDE-CODE")
        provider3 = self.factory.create_provider("Claude-Code")

        assert provider1.name == provider2.name == provider3.name

    def test_register_provider_case_insensitive(self):
        """Test provider registration is case-insensitive."""
        self.factory.register_provider("MOCK", MockProvider)
        assert self.factory.provider_exists("mock")
        assert self.factory.provider_exists("MOCK")
        assert self.factory.provider_exists("Mock")

    def test_create_provider_creation_error(self):
        """Test provider creation error handling."""

        class BrokenProvider(IAgentProvider):
            """Provider that fails to initialize."""

            def __init__(self, required_param):
                """Requires a parameter."""
                self.required_param = required_param

            @property
            def name(self) -> str:
                return "broken"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def execute_task(self, task, context, model, tools, timeout=None, **kwargs):
                yield "result"

            def supports_tool(self, tool_name: str) -> bool:
                return True

            def get_supported_models(self):
                return []

            def translate_model_name(self, canonical_name: str) -> str:
                return canonical_name

            async def validate_configuration(self) -> bool:
                return True

            def get_configuration_schema(self):
                return {}

            async def initialize(self) -> None:
                pass

            async def cleanup(self) -> None:
                pass

        self.factory.register_provider("broken", BrokenProvider)

        # Should raise ProviderCreationError (missing required_param)
        with pytest.raises(ProviderCreationError) as exc_info:
            self.factory.create_provider("broken")

        assert "Failed to create provider" in str(exc_info.value)
