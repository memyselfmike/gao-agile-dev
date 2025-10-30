"""Tests for SimpleMethodology.

Story 5.5: Test simple 3-level methodology implementation.
"""

import pytest

from gao_dev.core.models.methodology import (
    ComplexityLevel,
    ProjectType,
)
from gao_dev.methodologies.simple import SimpleMethodology


class TestSimpleMethodology:
    """Test SimpleMethodology class."""

    @pytest.fixture
    def methodology(self):
        """Create methodology instance."""
        return SimpleMethodology()

    def test_name(self, methodology):
        """Test methodology name."""
        assert methodology.name == "simple"

    def test_description(self, methodology):
        """Test description exists."""
        assert len(methodology.description) > 0
        assert "simple" in methodology.description.lower()

    def test_version(self, methodology):
        """Test version follows semantic versioning."""
        assert methodology.version == "1.0.0"

    def test_supports_scale_levels_is_false(self, methodology):
        """Test SimpleMethodology doesn't support scale levels."""
        assert methodology.supports_scale_levels is False

    @pytest.mark.asyncio
    async def test_assess_complexity_small_keywords(self, methodology):
        """Test assessing small task with keywords."""
        assessment = await methodology.assess_complexity("Fix login bug")

        assert assessment.complexity_level == ComplexityLevel.TRIVIAL
        assert assessment.confidence == 0.6
        assert "small task keywords" in assessment.reasoning.lower()
        assert assessment.metadata["methodology"] == "simple"

    @pytest.mark.asyncio
    async def test_assess_complexity_large_keywords(self, methodology):
        """Test assessing large project with keywords."""
        assessment = await methodology.assess_complexity(
            "Build complete e-commerce platform from scratch"
        )

        assert assessment.complexity_level == ComplexityLevel.XLARGE
        assert assessment.confidence == 0.6
        assert "large project keywords" in assessment.reasoning.lower()

    @pytest.mark.asyncio
    async def test_assess_complexity_medium_default(self, methodology):
        """Test default medium complexity."""
        assessment = await methodology.assess_complexity("Add user profile page")

        assert assessment.complexity_level == ComplexityLevel.MEDIUM
        assert "default medium" in assessment.reasoning.lower()

    @pytest.mark.asyncio
    async def test_detect_web_app_type(self, methodology):
        """Test project type detection for web app."""
        assessment = await methodology.assess_complexity("Build a website")

        assert assessment.project_type == ProjectType.WEB_APP

    @pytest.mark.asyncio
    async def test_detect_api_type(self, methodology):
        """Test project type detection for API."""
        assessment = await methodology.assess_complexity("Create REST API")

        assert assessment.project_type == ProjectType.API

    @pytest.mark.asyncio
    async def test_detect_cli_type(self, methodology):
        """Test project type detection for CLI."""
        assessment = await methodology.assess_complexity("Build CLI tool")

        assert assessment.project_type == ProjectType.CLI

    @pytest.mark.asyncio
    async def test_detect_unknown_type(self, methodology):
        """Test unknown project type."""
        assessment = await methodology.assess_complexity("Some project")

        assert assessment.project_type == ProjectType.UNKNOWN

    def test_build_workflow_trivial(self, methodology):
        """Test workflow for TRIVIAL complexity."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(complexity_level=ComplexityLevel.TRIVIAL)
        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 1
        assert sequence.workflows[0].workflow_name == "implement"
        assert sequence.workflows[0].phase == "implementation"
        assert sequence.total_phases == 1
        assert sequence.can_parallelize is False

    def test_build_workflow_medium(self, methodology):
        """Test workflow for MEDIUM complexity."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(complexity_level=ComplexityLevel.MEDIUM)
        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 3
        workflow_names = [w.workflow_name for w in sequence.workflows]
        assert workflow_names == ["plan", "implement", "test"]
        assert sequence.total_phases == 3

    def test_build_workflow_large(self, methodology):
        """Test workflow for LARGE complexity."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(complexity_level=ComplexityLevel.LARGE)
        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 4
        workflow_names = [w.workflow_name for w in sequence.workflows]
        assert workflow_names == ["design", "plan", "implement", "test"]
        assert sequence.total_phases == 4

    def test_build_workflow_xlarge(self, methodology):
        """Test workflow for XLARGE complexity (same as LARGE)."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(complexity_level=ComplexityLevel.XLARGE)
        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 4
        workflow_names = [w.workflow_name for w in sequence.workflows]
        assert workflow_names == ["design", "plan", "implement", "test"]

    def test_get_recommended_agents_design_phase(self, methodology):
        """Test agent recommendation for design phase."""
        agents = methodology.get_recommended_agents(
            "design system",
            context={"phase": "design"}
        )

        assert agents == ["Architect"]

    def test_get_recommended_agents_planning_phase(self, methodology):
        """Test agent recommendation for planning phase."""
        agents = methodology.get_recommended_agents(
            "plan feature",
            context={"phase": "planning"}
        )

        assert agents == ["Planner"]

    def test_get_recommended_agents_implementation_phase(self, methodology):
        """Test agent recommendation for implementation phase."""
        agents = methodology.get_recommended_agents(
            "implement code",
            context={"phase": "implementation"}
        )

        assert agents == ["Developer"]

    def test_get_recommended_agents_testing_phase(self, methodology):
        """Test agent recommendation for testing phase."""
        agents = methodology.get_recommended_agents(
            "test feature",
            context={"phase": "testing"}
        )

        assert agents == ["Tester"]

    def test_get_recommended_agents_default(self, methodology):
        """Test default agent recommendation."""
        agents = methodology.get_recommended_agents("some task")

        assert agents == ["Developer"]

    def test_get_recommended_agents_no_context(self, methodology):
        """Test agent recommendation without context."""
        agents = methodology.get_recommended_agents("task", context=None)

        assert agents == ["Developer"]

    def test_validate_config_always_valid(self, methodology):
        """Test config validation always returns valid."""
        result = methodology.validate_config({})

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_config_with_data(self, methodology):
        """Test config validation with data (still valid)."""
        result = methodology.validate_config({"some_key": "some_value"})

        assert result.valid is True

    @pytest.mark.asyncio
    async def test_multiple_keywords_large_priority(self, methodology):
        """Test that large keywords have priority over small keywords."""
        # Has both "fix" (small) and "application" (large)
        # Large keywords are checked first, so should match XLARGE
        assessment = await methodology.assess_complexity("Fix the application bug")

        # "application" is a large keyword, so it takes priority
        assert assessment.complexity_level == ComplexityLevel.XLARGE

    @pytest.mark.asyncio
    async def test_case_insensitive_keywords(self, methodology):
        """Test keyword matching is case-insensitive."""
        assessment1 = await methodology.assess_complexity("FIX BUG")
        assessment2 = await methodology.assess_complexity("fix bug")

        assert assessment1.complexity_level == assessment2.complexity_level
        assert assessment1.complexity_level == ComplexityLevel.TRIVIAL


class TestSimpleMethodologyIntegration:
    """Integration tests for SimpleMethodology."""

    @pytest.mark.asyncio
    async def test_end_to_end_small_task(self):
        """Test complete flow for small task."""
        methodology = SimpleMethodology()

        # Assess
        assessment = await methodology.assess_complexity("Quick bug fix")

        # Build workflow
        sequence = methodology.build_workflow_sequence(assessment)

        # Get agents
        agents = methodology.get_recommended_agents(
            "implement",
            context={"phase": "implementation"}
        )

        assert assessment.complexity_level == ComplexityLevel.TRIVIAL
        assert len(sequence.workflows) == 1
        assert agents == ["Developer"]

    @pytest.mark.asyncio
    async def test_end_to_end_medium_feature(self):
        """Test complete flow for medium feature."""
        methodology = SimpleMethodology()

        # Assess
        assessment = await methodology.assess_complexity("Add authentication")

        # Build workflow
        sequence = methodology.build_workflow_sequence(assessment)

        assert assessment.complexity_level == ComplexityLevel.MEDIUM
        assert len(sequence.workflows) == 3
        assert sequence.workflows[0].workflow_name == "plan"
        assert sequence.workflows[1].workflow_name == "implement"
        assert sequence.workflows[2].workflow_name == "test"

    @pytest.mark.asyncio
    async def test_end_to_end_large_project(self):
        """Test complete flow for large project."""
        methodology = SimpleMethodology()

        # Assess
        assessment = await methodology.assess_complexity(
            "Build complete system from scratch"
        )

        # Build workflow
        sequence = methodology.build_workflow_sequence(assessment)

        # Verify all phases
        phases = [w.phase for w in sequence.workflows]

        assert assessment.complexity_level == ComplexityLevel.XLARGE
        assert len(sequence.workflows) == 4
        assert "design" in phases
        assert "planning" in phases
        assert "implementation" in phases
        assert "testing" in phases

    def test_can_be_registered(self):
        """Test SimpleMethodology can be registered."""
        from gao_dev.methodologies.registry import MethodologyRegistry

        # Reset registry
        MethodologyRegistry.reset_instance()
        registry = MethodologyRegistry.get_instance()

        # Register SimpleMethodology
        simple = SimpleMethodology()
        registry.register_methodology(simple)

        # Verify registration
        assert registry.has_methodology("simple")
        retrieved = registry.get_methodology("simple")
        assert retrieved.name == "simple"
