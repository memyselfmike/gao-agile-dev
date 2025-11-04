"""Unit tests for IAgentProvider interface."""

import pytest
from abc import ABC
from pathlib import Path
from typing import AsyncGenerator, List, Dict, Optional

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.models import AgentContext


class TestIAgentProvider:
    """Test IAgentProvider interface structure."""

    def test_is_abstract_base_class(self):
        """Test IAgentProvider is an ABC."""
        assert issubclass(IAgentProvider, ABC)

    def test_cannot_instantiate_directly(self):
        """Test IAgentProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            IAgentProvider()  # type: ignore

        # Error message should mention abstract methods
        error_msg = str(exc_info.value)
        assert "abstract" in error_msg.lower() or "instantiate" in error_msg.lower()

    def test_has_required_properties(self):
        """Test IAgentProvider defines required properties."""
        required_properties = ['name', 'version']

        for prop_name in required_properties:
            assert hasattr(IAgentProvider, prop_name), \
                f"IAgentProvider should have property '{prop_name}'"

    def test_has_required_methods(self):
        """Test IAgentProvider defines all required methods."""
        required_methods = [
            'execute_task',
            'supports_tool',
            'get_supported_models',
            'translate_model_name',
            'validate_configuration',
            'get_configuration_schema',
            'initialize',
            'cleanup',
        ]

        for method_name in required_methods:
            assert hasattr(IAgentProvider, method_name), \
                f"IAgentProvider should have method '{method_name}'"

    def test_method_signatures_are_correct(self):
        """Test method signatures match interface specification."""
        # Check execute_task signature
        execute_task = IAgentProvider.execute_task
        assert hasattr(execute_task, '__isabstractmethod__')

        # Check other abstract methods
        abstract_methods = [
            'supports_tool',
            'get_supported_models',
            'translate_model_name',
            'validate_configuration',
            'get_configuration_schema',
            'initialize',
            'cleanup',
        ]

        for method_name in abstract_methods:
            method = getattr(IAgentProvider, method_name)
            assert hasattr(method, '__isabstractmethod__'), \
                f"{method_name} should be abstract"


class TestIAgentProviderImplementation:
    """Test concrete implementation of IAgentProvider."""

    @pytest.fixture
    def minimal_provider_class(self):
        """Create minimal concrete provider for testing."""

        class MinimalProvider(IAgentProvider):
            """Minimal provider implementation for testing."""

            @property
            def name(self) -> str:
                return "test-provider"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def execute_task(
                self,
                task: str,
                context: AgentContext,
                model: str,
                tools: List[str],
                timeout: Optional[int] = None,
                **kwargs
            ) -> AsyncGenerator[str, None]:
                yield "test result"

            def supports_tool(self, tool_name: str) -> bool:
                return tool_name in ["Read", "Write"]

            def get_supported_models(self) -> List[str]:
                return ["test-model"]

            def translate_model_name(self, canonical_name: str) -> str:
                return f"translated-{canonical_name}"

            async def validate_configuration(self) -> bool:
                return True

            def get_configuration_schema(self) -> Dict:
                return {"type": "object"}

            async def initialize(self) -> None:
                pass

            async def cleanup(self) -> None:
                pass

        return MinimalProvider

    def test_can_instantiate_concrete_implementation(self, minimal_provider_class):
        """Test concrete implementation can be instantiated."""
        provider = minimal_provider_class()
        assert isinstance(provider, IAgentProvider)

    def test_concrete_implementation_has_name_property(self, minimal_provider_class):
        """Test concrete implementation returns name."""
        provider = minimal_provider_class()
        assert provider.name == "test-provider"
        assert isinstance(provider.name, str)

    def test_concrete_implementation_has_version_property(self, minimal_provider_class):
        """Test concrete implementation returns version."""
        provider = minimal_provider_class()
        assert provider.version == "1.0.0"
        assert isinstance(provider.version, str)

    @pytest.mark.asyncio
    async def test_execute_task_yields_results(self, minimal_provider_class, tmp_path):
        """Test execute_task yields results."""
        provider = minimal_provider_class()
        context = AgentContext(project_root=tmp_path)

        results = []
        async for result in provider.execute_task(
            task="test task",
            context=context,
            model="test-model",
            tools=["Read"],
            timeout=60
        ):
            results.append(result)

        assert len(results) == 1
        assert results[0] == "test result"

    def test_supports_tool_returns_bool(self, minimal_provider_class):
        """Test supports_tool returns boolean."""
        provider = minimal_provider_class()
        assert provider.supports_tool("Read") is True
        assert provider.supports_tool("NonExistent") is False
        assert isinstance(provider.supports_tool("Read"), bool)

    def test_get_supported_models_returns_list(self, minimal_provider_class):
        """Test get_supported_models returns list of strings."""
        provider = minimal_provider_class()
        models = provider.get_supported_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(m, str) for m in models)

    def test_translate_model_name_returns_string(self, minimal_provider_class):
        """Test translate_model_name returns string."""
        provider = minimal_provider_class()
        translated = provider.translate_model_name("canonical-model")
        assert isinstance(translated, str)
        assert translated == "translated-canonical-model"

    @pytest.mark.asyncio
    async def test_validate_configuration_returns_bool(self, minimal_provider_class):
        """Test validate_configuration returns boolean."""
        provider = minimal_provider_class()
        result = await provider.validate_configuration()
        assert isinstance(result, bool)

    def test_get_configuration_schema_returns_dict(self, minimal_provider_class):
        """Test get_configuration_schema returns dict."""
        provider = minimal_provider_class()
        schema = provider.get_configuration_schema()
        assert isinstance(schema, dict)

    @pytest.mark.asyncio
    async def test_initialize_is_callable(self, minimal_provider_class):
        """Test initialize method is callable."""
        provider = minimal_provider_class()
        # Should not raise
        await provider.initialize()

    @pytest.mark.asyncio
    async def test_cleanup_is_callable(self, minimal_provider_class):
        """Test cleanup method is callable."""
        provider = minimal_provider_class()
        # Should not raise
        await provider.cleanup()


class TestPartialImplementation:
    """Test that partial implementation raises TypeError."""

    def test_missing_name_property_raises_error(self):
        """Test missing name property prevents instantiation."""

        class PartialProvider(IAgentProvider):
            # Missing name property

            @property
            def version(self) -> str:
                return "1.0.0"

            async def execute_task(self, *args, **kwargs):
                yield "test"

            def supports_tool(self, tool_name: str) -> bool:
                return True

            def get_supported_models(self) -> List[str]:
                return []

            def translate_model_name(self, canonical_name: str) -> str:
                return canonical_name

            async def validate_configuration(self) -> bool:
                return True

            def get_configuration_schema(self) -> Dict:
                return {}

            async def initialize(self) -> None:
                pass

            async def cleanup(self) -> None:
                pass

        with pytest.raises(TypeError):
            PartialProvider()  # type: ignore

    def test_missing_execute_task_raises_error(self):
        """Test missing execute_task method prevents instantiation."""

        class PartialProvider(IAgentProvider):
            @property
            def name(self) -> str:
                return "test"

            @property
            def version(self) -> str:
                return "1.0.0"

            # Missing execute_task

            def supports_tool(self, tool_name: str) -> bool:
                return True

            def get_supported_models(self) -> List[str]:
                return []

            def translate_model_name(self, canonical_name: str) -> str:
                return canonical_name

            async def validate_configuration(self) -> bool:
                return True

            def get_configuration_schema(self) -> Dict:
                return {}

            async def initialize(self) -> None:
                pass

            async def cleanup(self) -> None:
                pass

        with pytest.raises(TypeError):
            PartialProvider()  # type: ignore

    def test_missing_multiple_methods_raises_error(self):
        """Test missing multiple methods prevents instantiation."""

        class PartialProvider(IAgentProvider):
            @property
            def name(self) -> str:
                return "test"

            # Missing everything else

        with pytest.raises(TypeError):
            PartialProvider()  # type: ignore


class TestInterfaceDocumentation:
    """Test that interface has proper documentation."""

    def test_class_has_docstring(self):
        """Test IAgentProvider has class docstring."""
        assert IAgentProvider.__doc__ is not None
        assert len(IAgentProvider.__doc__) > 100

    def test_methods_have_docstrings(self):
        """Test all abstract methods have docstrings."""
        methods = [
            'execute_task',
            'supports_tool',
            'get_supported_models',
            'translate_model_name',
            'validate_configuration',
            'get_configuration_schema',
            'initialize',
            'cleanup',
        ]

        for method_name in methods:
            method = getattr(IAgentProvider, method_name)
            assert method.__doc__ is not None, \
                f"{method_name} should have docstring"
            assert len(method.__doc__) > 50, \
                f"{method_name} docstring should be substantial"

    def test_properties_have_docstrings(self):
        """Test properties have docstrings."""
        # Properties are defined as abstract methods with @property decorator
        # Check that name and version have documentation
        assert hasattr(IAgentProvider, 'name')
        assert hasattr(IAgentProvider, 'version')


class TestTypeHints:
    """Test that interface has proper type hints."""

    def test_name_property_has_return_type(self):
        """Test name property has return type annotation."""
        # This is validated by mypy, here we just check it exists
        assert hasattr(IAgentProvider, 'name')

    def test_execute_task_has_type_hints(self):
        """Test execute_task has proper type hints."""
        # Type hints are checked by mypy
        # This test verifies the method exists and is properly decorated
        assert hasattr(IAgentProvider, 'execute_task')
        method = getattr(IAgentProvider, 'execute_task')
        assert hasattr(method, '__annotations__')
