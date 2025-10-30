"""Tests for MethodologyRegistry.

Story 5.3: Test methodology registry implementation.
"""

import pytest
import threading
from unittest.mock import Mock

from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.core.models.methodology import (
    ComplexityAssessment,
    ComplexityLevel,
    ValidationResult,
    WorkflowSequence,
)
from gao_dev.methodologies import (
    MethodologyRegistry,
    MethodologyAlreadyRegisteredError,
    MethodologyNotFoundError,
    InvalidMethodologyError,
)
from gao_dev.methodologies.adaptive_agile import AdaptiveAgileMethodology


class MockMethodology(IMethodology):
    """Mock methodology for testing."""

    def __init__(self, name: str = "mock", version: str = "1.0.0"):
        self._name = name
        self._version = version

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock methodology: {self._name}"

    @property
    def version(self) -> str:
        return self._version

    async def assess_complexity(self, prompt: str, context=None) -> ComplexityAssessment:
        return ComplexityAssessment(complexity_level=ComplexityLevel.MEDIUM)

    def build_workflow_sequence(self, assessment: ComplexityAssessment) -> WorkflowSequence:
        return WorkflowSequence(workflows=[], total_phases=1)

    def get_recommended_agents(self, task: str, context=None):
        return ["agent1"]

    def validate_config(self, config):
        return ValidationResult(valid=True, errors=[], warnings=[])


class TestMethodologyRegistry:
    """Test MethodologyRegistry class."""

    def setup_method(self):
        """Reset singleton before each test."""
        MethodologyRegistry.reset_instance()

    def test_get_instance_returns_singleton(self):
        """Test get_instance returns same instance."""
        registry1 = MethodologyRegistry.get_instance()
        registry2 = MethodologyRegistry.get_instance()

        assert registry1 is registry2

    def test_auto_registers_adaptive_agile(self):
        """Test AdaptiveAgile auto-registered on init."""
        registry = MethodologyRegistry.get_instance()

        assert registry.has_methodology("adaptive-agile")

        methodology = registry.get_methodology("adaptive-agile")
        assert isinstance(methodology, AdaptiveAgileMethodology)

    def test_adaptive_agile_is_default(self):
        """Test AdaptiveAgile is default methodology."""
        registry = MethodologyRegistry.get_instance()

        default = registry.get_default()
        assert default.name == "adaptive-agile"

    def test_register_methodology(self):
        """Test registering new methodology."""
        registry = MethodologyRegistry.get_instance()
        mock = MockMethodology("custom")

        registry.register_methodology(mock)

        assert registry.has_methodology("custom")
        retrieved = registry.get_methodology("custom")
        assert retrieved is mock

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate name raises error."""
        registry = MethodologyRegistry.get_instance()
        mock1 = MockMethodology("custom")
        mock2 = MockMethodology("custom")

        registry.register_methodology(mock1)

        with pytest.raises(MethodologyAlreadyRegisteredError) as exc:
            registry.register_methodology(mock2)

        assert "already registered" in str(exc.value)

    def test_register_invalid_methodology_raises_error(self):
        """Test registering non-IMethodology raises error."""
        registry = MethodologyRegistry.get_instance()

        class NotAMethodology:
            pass

        with pytest.raises(InvalidMethodologyError) as exc:
            registry.register_methodology(NotAMethodology())

        assert "must implement IMethodology" in str(exc.value)

    def test_get_methodology_case_insensitive(self):
        """Test get_methodology is case-insensitive."""
        registry = MethodologyRegistry.get_instance()

        # All should return same methodology
        m1 = registry.get_methodology("adaptive-agile")
        m2 = registry.get_methodology("ADAPTIVE-AGILE")
        m3 = registry.get_methodology("Adaptive-Agile")

        assert m1 is m2 is m3

    def test_get_nonexistent_methodology_raises_error(self):
        """Test getting nonexistent methodology raises error."""
        registry = MethodologyRegistry.get_instance()

        with pytest.raises(MethodologyNotFoundError) as exc:
            registry.get_methodology("nonexistent")

        assert "not registered" in str(exc.value)
        assert "Available methodologies" in str(exc.value)

    def test_list_methodologies_sorted(self):
        """Test list_methodologies returns sorted names."""
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(MockMethodology("zebra"))
        registry.register_methodology(MockMethodology("aardvark"))

        methodologies = registry.list_methodologies()

        assert methodologies == ["aardvark", "adaptive-agile", "zebra"]

    def test_list_methodologies_empty_after_reset(self):
        """Test list after reset shows only auto-registered."""
        MethodologyRegistry.reset_instance()
        registry = MethodologyRegistry.get_instance()

        methodologies = registry.list_methodologies()

        # Only AdaptiveAgile auto-registered
        assert methodologies == ["adaptive-agile"]

    def test_has_methodology_true_for_registered(self):
        """Test has_methodology returns True for registered."""
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(MockMethodology("custom"))

        assert registry.has_methodology("custom") is True

    def test_has_methodology_false_for_unregistered(self):
        """Test has_methodology returns False for unregistered."""
        registry = MethodologyRegistry.get_instance()

        assert registry.has_methodology("nonexistent") is False

    def test_has_methodology_case_insensitive(self):
        """Test has_methodology is case-insensitive."""
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(MockMethodology("MyMethodology"))

        assert registry.has_methodology("mymethodology") is True
        assert registry.has_methodology("MYMETHODOLOGY") is True

    def test_get_default_never_raises(self):
        """Test get_default always works (adaptive-agile auto-registered)."""
        registry = MethodologyRegistry.get_instance()

        default = registry.get_default()

        assert default is not None
        assert default.name == "adaptive-agile"

    def test_set_default_changes_default(self):
        """Test set_default changes default methodology."""
        registry = MethodologyRegistry.get_instance()
        custom = MockMethodology("custom")
        registry.register_methodology(custom)

        registry.set_default("custom")
        default = registry.get_default()

        assert default is custom

    def test_set_default_nonexistent_raises_error(self):
        """Test set_default with nonexistent methodology raises error."""
        registry = MethodologyRegistry.get_instance()

        with pytest.raises(MethodologyNotFoundError):
            registry.set_default("nonexistent")

    def test_set_default_case_insensitive(self):
        """Test set_default is case-insensitive."""
        registry = MethodologyRegistry.get_instance()
        custom = MockMethodology("MyMethodology")
        registry.register_methodology(custom)

        registry.set_default("MYMETHODOLOGY")
        default = registry.get_default()

        assert default is custom

    def test_thread_safety_registration(self):
        """Test concurrent registration is thread-safe."""
        registry = MethodologyRegistry.get_instance()
        errors = []

        def register_methodology(name):
            try:
                methodology = MockMethodology(name)
                registry.register_methodology(methodology)
            except Exception as e:
                errors.append(e)

        # Create 10 threads registering different methodologies
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_methodology, args=(f"method-{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # No errors should occur
        assert len(errors) == 0

        # All methodologies should be registered
        methodologies = registry.list_methodologies()
        assert len(methodologies) == 11  # 10 + adaptive-agile

    def test_thread_safety_retrieval(self):
        """Test concurrent retrieval is thread-safe."""
        registry = MethodologyRegistry.get_instance()
        results = []

        def get_methodology():
            try:
                methodology = registry.get_methodology("adaptive-agile")
                results.append(methodology)
            except Exception as e:
                results.append(e)

        # Create 20 threads getting the same methodology
        threads = []
        for i in range(20):
            thread = threading.Thread(target=get_methodology)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should succeed and return same instance
        assert len(results) == 20
        assert all(isinstance(r, AdaptiveAgileMethodology) for r in results)
        assert all(r is results[0] for r in results)

    def test_singleton_thread_safety(self):
        """Test singleton instantiation is thread-safe."""
        MethodologyRegistry.reset_instance()
        instances = []

        def get_instance():
            instance = MethodologyRegistry.get_instance()
            instances.append(instance)

        # Create 20 threads getting instance
        threads = []
        for i in range(20):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should get same instance
        assert len(instances) == 20
        assert all(inst is instances[0] for inst in instances)

    def test_register_stores_lowercase_name(self):
        """Test registry stores methodology names in lowercase."""
        registry = MethodologyRegistry.get_instance()
        methodology = MockMethodology("MyMethodology")

        registry.register_methodology(methodology)

        # Should be stored as lowercase
        assert "mymethodology" in registry.list_methodologies()
        assert "MyMethodology" not in registry.list_methodologies()

    def test_multiple_methodologies(self):
        """Test registering multiple methodologies."""
        registry = MethodologyRegistry.get_instance()

        methodologies = [
            MockMethodology("method1"),
            MockMethodology("method2"),
            MockMethodology("method3"),
        ]

        for m in methodologies:
            registry.register_methodology(m)

        names = registry.list_methodologies()
        assert "method1" in names
        assert "method2" in names
        assert "method3" in names
        assert len(names) == 4  # 3 + adaptive-agile
