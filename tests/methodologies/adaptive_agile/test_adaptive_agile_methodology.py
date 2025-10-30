"""Tests for AdaptiveAgileMethodology.

Story 5.2: Test complete methodology implementation.
"""

import pytest

from gao_dev.core.models.methodology import (
    ComplexityLevel,
    ProjectType,
    ValidationResult,
)
from gao_dev.methodologies.adaptive_agile import (
    AdaptiveAgileMethodology,
    ScaleLevel,
)


class TestAdaptiveAgileMethodology:
    """Test AdaptiveAgileMethodology class."""

    @pytest.fixture
    def methodology(self):
        """Create methodology instance."""
        return AdaptiveAgileMethodology()

    def test_name_is_adaptive_agile(self, methodology):
        """Test methodology name."""
        assert methodology.name == "adaptive-agile"

    def test_description_exists(self, methodology):
        """Test description exists."""
        assert len(methodology.description) > 0
        assert "scale" in methodology.description.lower()

    def test_version_is_semantic(self, methodology):
        """Test version follows semantic versioning."""
        assert methodology.version == "1.0.0"

    def test_supports_scale_levels(self, methodology):
        """Test methodology supports scale levels."""
        assert methodology.supports_scale_levels is True

    @pytest.mark.asyncio
    async def test_assess_complexity_bug_fix(self, methodology):
        """Test assessing bug fix complexity."""
        assessment = await methodology.assess_complexity("Fix login bug")

        assert assessment.complexity_level == ComplexityLevel.SMALL
        assert assessment.metadata["scale_level"] == ScaleLevel.LEVEL_1_BUG_FIX
        assert assessment.estimated_stories == 1

    @pytest.mark.asyncio
    async def test_assess_complexity_small_feature(self, methodology):
        """Test assessing small feature complexity."""
        assessment = await methodology.assess_complexity("Add user profile page")

        assert assessment.complexity_level == ComplexityLevel.MEDIUM
        assert assessment.metadata["scale_level"] == ScaleLevel.LEVEL_2_SMALL_FEATURE

    @pytest.mark.asyncio
    async def test_assess_complexity_greenfield(self, methodology):
        """Test assessing greenfield complexity."""
        assessment = await methodology.assess_complexity(
            "Build complete e-commerce platform from scratch"
        )

        assert assessment.complexity_level == ComplexityLevel.XLARGE
        assert assessment.metadata["scale_level"] == ScaleLevel.LEVEL_4_GREENFIELD
        assert assessment.estimated_stories == 50
        assert assessment.estimated_epics == 8

    @pytest.mark.asyncio
    async def test_assess_complexity_detects_web_app(self, methodology):
        """Test project type detection for web app."""
        assessment = await methodology.assess_complexity("Build a web application")

        assert assessment.project_type == ProjectType.WEB_APP

    @pytest.mark.asyncio
    async def test_assess_complexity_detects_api(self, methodology):
        """Test project type detection for API."""
        assessment = await methodology.assess_complexity("Create a REST API")

        assert assessment.project_type == ProjectType.API

    def test_build_workflow_sequence_level_0(self, methodology):
        """Test workflow sequence for level 0."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.TRIVIAL,
            metadata={"scale_level": 0}
        )

        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 1
        assert sequence.workflows[0].workflow_name == "direct-implementation"

    def test_build_workflow_sequence_level_2(self, methodology):
        """Test workflow sequence for level 2."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.MEDIUM,
            metadata={"scale_level": 2}
        )

        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) == 4
        workflow_names = [w.workflow_name for w in sequence.workflows]
        assert "create-prd" in workflow_names
        assert "create-stories" in workflow_names
        assert "implement-stories" in workflow_names

    def test_build_workflow_sequence_level_4(self, methodology):
        """Test workflow sequence for level 4 (comprehensive)."""
        from gao_dev.core.models.methodology import ComplexityAssessment

        assessment = ComplexityAssessment(
            complexity_level=ComplexityLevel.XLARGE,
            metadata={"scale_level": 4}
        )

        sequence = methodology.build_workflow_sequence(assessment)

        assert len(sequence.workflows) > 10  # Comprehensive workflows
        assert sequence.total_phases >= 4  # All phases present

    def test_get_recommended_agents_for_planning(self, methodology):
        """Test agent recommendations for planning phase."""
        agents = methodology.get_recommended_agents(
            "any task",
            context={"phase": "planning"}
        )

        assert "John" in agents or "Bob" in agents

    def test_get_recommended_agents_for_implementation(self, methodology):
        """Test agent recommendations for implementation phase."""
        agents = methodology.get_recommended_agents(
            "implement feature",
            context={"phase": "implementation"}
        )

        assert "Amelia" in agents

    def test_get_recommended_agents_for_architecture(self, methodology):
        """Test agent recommendations for architecture tasks."""
        agents = methodology.get_recommended_agents("create architecture")

        assert "Winston" in agents

    def test_validate_config_valid_scale_level(self, methodology):
        """Test validating valid scale level."""
        result = methodology.validate_config({"scale_level": 2})

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_config_invalid_scale_level(self, methodology):
        """Test validating invalid scale level."""
        result = methodology.validate_config({"scale_level": 5})

        assert result.valid is False
        assert len(result.errors) > 0
        assert "0-4" in result.errors[0]

    def test_validate_config_unknown_project_type_warning(self, methodology):
        """Test unknown project type generates warning."""
        result = methodology.validate_config({"project_type": "invalid_type"})

        assert result.valid is True  # Warning, not error
        assert len(result.warnings) > 0
        assert "invalid_type" in result.warnings[0]

    def test_validate_config_invalid_scale_level_type(self, methodology):
        """Test non-integer scale level is invalid."""
        result = methodology.validate_config({"scale_level": "two"})

        assert result.valid is False
        assert "integer" in result.errors[0].lower()


class TestWorkflowSelector:
    """Test workflow selection logic."""

    @pytest.fixture
    def methodology(self):
        return AdaptiveAgileMethodology()

    def test_level_1_has_bug_fix_workflows(self, methodology):
        """Test level 1 has bug fix specific workflows."""
        workflows = methodology.workflow_selector.select_workflows(
            ScaleLevel.LEVEL_1_BUG_FIX
        )

        workflow_names = [w.workflow_name for w in workflows]
        assert "analyze-bug" in workflow_names
        assert "implement-fix" in workflow_names
        assert "verify-fix" in workflow_names

    def test_level_3_has_solutioning_phase(self, methodology):
        """Test level 3 includes solutioning phase."""
        workflows = methodology.workflow_selector.select_workflows(
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE
        )

        phases = {w.phase for w in workflows}
        assert "solutioning" in phases
        assert "planning" in phases
        assert "implementation" in phases

    def test_level_4_has_research_phase(self, methodology):
        """Test level 4 includes optional research."""
        workflows = methodology.workflow_selector.select_workflows(
            ScaleLevel.LEVEL_4_GREENFIELD
        )

        workflow_names = [w.workflow_name for w in workflows]
        assert "research" in workflow_names
        assert "product-brief" in workflow_names


class TestAgentRecommender:
    """Test agent recommendation logic."""

    @pytest.fixture
    def methodology(self):
        return AdaptiveAgileMethodology()

    def test_recommends_mary_for_analysis(self, methodology):
        """Test Mary recommended for analysis."""
        agents = methodology.agent_recommender.recommend("research")

        assert "Mary" in agents

    def test_recommends_john_for_prd(self, methodology):
        """Test John recommended for PRD."""
        agents = methodology.agent_recommender.recommend("create PRD")

        assert "John" in agents

    def test_recommends_winston_for_architecture(self, methodology):
        """Test Winston recommended for architecture."""
        agents = methodology.agent_recommender.recommend("design architecture")

        assert "Winston" in agents

    def test_recommends_amelia_for_implementation(self, methodology):
        """Test Amelia recommended for implementation."""
        agents = methodology.agent_recommender.recommend("implement code")

        assert "Amelia" in agents

    def test_recommends_murat_for_testing(self, methodology):
        """Test Murat recommended for testing."""
        agents = methodology.agent_recommender.recommend("test feature")

        assert "Murat" in agents

    def test_get_all_agents_returns_7_agents(self, methodology):
        """Test all 7 agents returned."""
        agents = methodology.agent_recommender.get_all_agents()

        assert len(agents) == 7
        assert "Mary" in agents
        assert "Murat" in agents
