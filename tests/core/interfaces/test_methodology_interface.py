"""Tests for IMethodology interface.

Story 5.1: Test IMethodology interface with mock implementation.
"""

import pytest
from typing import Any, Dict, List, Optional

from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.core.models.methodology import (
    ComplexityLevel,
    ProjectType,
    ComplexityAssessment,
    WorkflowStep,
    WorkflowSequence,
    ValidationResult,
)


class MockMethodology(IMethodology):
    """Mock methodology implementation for testing."""

    def __init__(self):
        """Initialize mock methodology."""
        self._name = "mock-methodology"
        self._description = "Mock methodology for testing"
        self._version = "1.0.0"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def version(self) -> str:
        return self._version

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        # Simple mock: return MEDIUM complexity
        return ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            project_type=ProjectType.WEB_APP,
            confidence=0.7,
            reasoning="Mock assessment"
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        # Simple mock: return basic sequence
        workflows = [
            WorkflowStep("plan", "planning"),
            WorkflowStep("implement", "implementation")
        ]
        return WorkflowSequence(
            workflows=workflows,
            total_phases=2
        )

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        # Simple mock: return fixed agents
        return ["Developer", "Tester"]

    def validate_config(
        self,
        config: Dict[str, Any]
    ) -> ValidationResult:
        # Simple mock: always valid
        return ValidationResult(valid=True)


class TestIMethodologyInterface:
    """Test IMethodology interface."""

    @pytest.fixture
    def methodology(self):
        """Create mock methodology instance."""
        return MockMethodology()

    def test_name_property(self, methodology):
        """Test name property returns string."""
        assert isinstance(methodology.name, str)
        assert methodology.name == "mock-methodology"

    def test_description_property(self, methodology):
        """Test description property returns string."""
        assert isinstance(methodology.description, str)
        assert len(methodology.description) > 0

    def test_version_property(self, methodology):
        """Test version property returns string."""
        assert isinstance(methodology.version, str)
        assert "." in methodology.version  # Semantic versioning

    def test_supports_scale_levels_default(self, methodology):
        """Test supports_scale_levels default is False."""
        assert methodology.supports_scale_levels is False

    @pytest.mark.asyncio
    async def test_assess_complexity_returns_assessment(self, methodology):
        """Test assess_complexity returns ComplexityAssessment."""
        prompt = "Build a todo application"

        assessment = await methodology.assess_complexity(prompt)

        assert isinstance(assessment, ComplexityAssessment)
        assert isinstance(assessment.complexity_level, ComplexityLevel)

    @pytest.mark.asyncio
    async def test_assess_complexity_with_context(self, methodology):
        """Test assess_complexity accepts context."""
        prompt = "Fix login bug"
        context = {"project_type": "web_app"}

        assessment = await methodology.assess_complexity(prompt, context)

        assert isinstance(assessment, ComplexityAssessment)

    def test_build_workflow_sequence_returns_sequence(self, methodology):
        """Test build_workflow_sequence returns WorkflowSequence."""
        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM
        )

        sequence = methodology.build_workflow_sequence(assessment)

        assert isinstance(sequence, WorkflowSequence)
        assert isinstance(sequence.workflows, list)

    def test_get_recommended_agents_returns_list(self, methodology):
        """Test get_recommended_agents returns list of agent names."""
        agents = methodology.get_recommended_agents("implement feature")

        assert isinstance(agents, list)
        assert all(isinstance(agent, str) for agent in agents)
        assert len(agents) > 0

    def test_get_recommended_agents_with_context(self, methodology):
        """Test get_recommended_agents accepts context."""
        agents = methodology.get_recommended_agents(
            "create architecture",
            context={"phase": "solutioning"}
        )

        assert isinstance(agents, list)

    def test_validate_config_returns_validation_result(self, methodology):
        """Test validate_config returns ValidationResult."""
        config = {"some_setting": "value"}

        result = methodology.validate_config(config)

        assert isinstance(result, ValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


class TestMethodologyWithScaleLevels(IMethodology):
    """Test methodology that supports scale levels."""

    @property
    def name(self) -> str:
        return "scale-methodology"

    @property
    def description(self) -> str:
        return "Methodology with scale levels"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supports_scale_levels(self) -> bool:
        # Override to return True
        return True

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        return ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            metadata={"scale_level": 2}
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        return WorkflowSequence()

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        return []

    def validate_config(
        self,
        config: Dict[str, Any]
    ) -> ValidationResult:
        return ValidationResult(valid=True)


class TestSupportsScaleLevels:
    """Test supports_scale_levels property."""

    def test_supports_scale_levels_can_be_overridden(self):
        """Test methodology can override supports_scale_levels."""
        methodology = TestMethodologyWithScaleLevels()

        assert methodology.supports_scale_levels is True

    def test_default_supports_scale_levels_is_false(self):
        """Test default supports_scale_levels is False."""
        methodology = MockMethodology()

        assert methodology.supports_scale_levels is False


class TestInterfaceRequirements:
    """Test interface implementation requirements."""

    def test_cannot_instantiate_interface(self):
        """Test cannot instantiate IMethodology directly."""
        with pytest.raises(TypeError):
            IMethodology()  # type: ignore

    def test_must_implement_all_abstract_methods(self):
        """Test implementation must provide all abstract methods."""
        # This class is missing required methods
        with pytest.raises(TypeError):
            class IncompleteMethodology(IMethodology):
                @property
                def name(self) -> str:
                    return "incomplete"
                # Missing other required methods

            IncompleteMethodology()  # type: ignore
