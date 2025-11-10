"""Tests for BrainstormingEngine.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.2 - Brainstorming & Mind Mapping
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from gao_dev.orchestrator.brainstorming_engine import (
    BrainstormingEngine,
    BrainstormingGoal,
)
from gao_dev.core.models.brainstorming_summary import (
    BrainstormingTechnique,
    Idea,
)
from gao_dev.core.services.ai_analysis_service import AIAnalysisService


@pytest.fixture
def mock_analysis_service():
    """Create mock AIAnalysisService."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def brainstorming_engine(mock_analysis_service):
    """Create BrainstormingEngine with mocked dependencies."""
    engine = BrainstormingEngine(analysis_service=mock_analysis_service)
    return engine


class TestTechniqueLoading:
    """Tests for technique loading from CSV."""

    def test_load_techniques_from_csv(self, brainstorming_engine):
        """Test that 35+ techniques are loaded from CSV."""
        techniques = brainstorming_engine.techniques

        # CSV has 35 techniques (34 data rows + 1 header = 35 lines)
        assert len(techniques) >= 35
        assert "SCAMPER Method" in techniques
        assert "Mind Mapping" in techniques
        assert "Five Whys" in techniques

    def test_technique_structure(self, brainstorming_engine):
        """Test that technique objects have correct structure."""
        scamper = brainstorming_engine.get_technique("SCAMPER Method")

        assert scamper is not None
        assert scamper.name == "SCAMPER Method"
        assert scamper.category == "structured"
        assert len(scamper.facilitation_prompts) == 7  # S, C, A, M, P, E, R

        # Note: Some techniques in CSV have incomplete metadata (None values)
        # This is acceptable - they can still be used for brainstorming

    def test_technique_categories(self, brainstorming_engine):
        """Test that all expected categories are present."""
        categories = set(t.category for t in brainstorming_engine.techniques.values())

        expected_categories = {
            "structured",
            "creative",
            "collaborative",
            "deep",
            "theatrical",
            "wild",
            "introspective_delight",
        }
        assert categories == expected_categories

    def test_list_techniques_all(self, brainstorming_engine):
        """Test listing all techniques."""
        techniques = brainstorming_engine.list_techniques()

        assert len(techniques) >= 35  # CSV has 35 techniques

    def test_list_techniques_by_category(self, brainstorming_engine):
        """Test filtering techniques by category."""
        creative_techniques = brainstorming_engine.list_techniques(category="creative")

        assert len(creative_techniques) > 0
        assert all(t.category == "creative" for t in creative_techniques)


class TestTechniqueRecommendation:
    """Tests for technique recommendation algorithm."""

    @pytest.mark.asyncio
    async def test_recommend_for_innovation(self, brainstorming_engine):
        """Test recommendation for innovation goal."""
        recommendations = await brainstorming_engine.recommend_techniques(
            topic="New product features", goal=BrainstormingGoal.INNOVATION
        )

        assert len(recommendations) == 3
        # Should recommend creative/wild/theatrical techniques
        categories = [t.category for t in recommendations]
        assert any(cat in ["creative", "wild", "theatrical"] for cat in categories)

    @pytest.mark.asyncio
    async def test_recommend_for_problem_solving(self, brainstorming_engine):
        """Test recommendation for problem solving goal."""
        recommendations = await brainstorming_engine.recommend_techniques(
            topic="Reduce error rate", goal=BrainstormingGoal.PROBLEM_SOLVING
        )

        assert len(recommendations) == 3
        # Should recommend deep/structured techniques
        categories = [t.category for t in recommendations]
        assert any(cat in ["deep", "structured"] for cat in categories)

    @pytest.mark.asyncio
    async def test_recommend_for_strategic_planning(self, brainstorming_engine):
        """Test recommendation for strategic planning goal."""
        recommendations = await brainstorming_engine.recommend_techniques(
            topic="2024 roadmap", goal=BrainstormingGoal.STRATEGIC_PLANNING
        )

        assert len(recommendations) == 3
        categories = [t.category for t in recommendations]
        assert any(cat in ["structured", "deep", "collaborative"] for cat in categories)

    @pytest.mark.asyncio
    async def test_recommend_diverse_techniques(self, brainstorming_engine):
        """Test that recommendations are diverse (different categories)."""
        recommendations = await brainstorming_engine.recommend_techniques(
            topic="General exploration", goal=BrainstormingGoal.EXPLORATION
        )

        assert len(recommendations) == 3
        categories = [t.category for t in recommendations]
        # Should have at least 2 different categories for diversity
        assert len(set(categories)) >= 2

    @pytest.mark.asyncio
    async def test_recommend_with_energy_filter(self, brainstorming_engine):
        """Test recommendation with energy level preference."""
        context = {"energy_level": "high"}

        recommendations = await brainstorming_engine.recommend_techniques(
            topic="Innovation workshop", goal=BrainstormingGoal.INNOVATION, context=context
        )

        # If high energy techniques available, should prefer them
        # (fallback to all if not enough)
        assert len(recommendations) > 0


class TestSCAMPERFacilitation:
    """Tests for SCAMPER technique implementation."""

    @pytest.mark.asyncio
    async def test_scamper_generates_seven_prompts(self, brainstorming_engine):
        """Test that SCAMPER generates 7 ideas (one per lens)."""
        ideas = await brainstorming_engine.facilitate_scamper(
            topic="Authentication system", user_responses=None
        )

        assert len(ideas) == 7
        assert all(idea.technique == "SCAMPER Method" for idea in ideas)

    @pytest.mark.asyncio
    async def test_scamper_lenses(self, brainstorming_engine):
        """Test that all SCAMPER lenses are covered."""
        ideas = await brainstorming_engine.facilitate_scamper(
            topic="Shopping cart", user_responses=None
        )

        lenses = [idea.content.split(":")[0] for idea in ideas]
        expected_lenses = [
            "Substitute",
            "Combine",
            "Adapt",
            "Modify",
            "Put to other uses",
            "Eliminate",
            "Reverse",
        ]

        assert lenses == expected_lenses

    @pytest.mark.asyncio
    async def test_scamper_with_user_responses(self, brainstorming_engine):
        """Test SCAMPER with provided user responses."""
        user_responses = [
            "Use biometric instead of password",
            "Combine email and SMS verification",
            "Adapt OAuth2 from social login",
            "Modify timeout to 30 minutes",
            "Use for API authentication too",
            "Eliminate security questions",
            "Reverse: ask for email instead of username",
        ]

        ideas = await brainstorming_engine.facilitate_scamper(
            topic="Authentication", user_responses=user_responses
        )

        assert len(ideas) == 7
        assert "biometric" in ideas[0].content.lower()
        assert "combine" in ideas[1].content.lower()


class TestHowMightWe:
    """Tests for How Might We framing."""

    @pytest.mark.asyncio
    async def test_how_might_we_generation(self, brainstorming_engine, mock_analysis_service):
        """Test HMW question generation."""
        # Mock AI response
        mock_analysis_service.analyze.return_value = Mock(
            response="""How might we simplify authentication?
How might we make login more secure?
How might we reduce password fatigue?
How might we support passwordless authentication?
How might we improve user trust?"""
        )

        ideas = await brainstorming_engine.facilitate_how_might_we(
            problem_statement="Users forget passwords", user_responses=None
        )

        assert len(ideas) == 5
        assert all(idea.technique == "How Might We" for idea in ideas)
        mock_analysis_service.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_how_might_we_with_responses(self, brainstorming_engine, mock_analysis_service):
        """Test HMW with user responses."""
        mock_analysis_service.analyze.return_value = Mock(
            response="""How might we simplify login?
How might we remove passwords?"""
        )

        user_responses = ["Use biometrics", "Implement magic links"]

        ideas = await brainstorming_engine.facilitate_how_might_we(
            problem_statement="Complex login", user_responses=user_responses
        )

        assert len(ideas) == 2
        assert "biometrics" in ideas[0].content.lower()
        assert "magic links" in ideas[1].content.lower()


class TestAffinityMapping:
    """Tests for affinity mapping and idea grouping."""

    @pytest.mark.asyncio
    async def test_affinity_mapping(self, brainstorming_engine, mock_analysis_service):
        """Test ideas grouped by theme."""
        ideas = [
            Idea(content="Biometric authentication", technique="SCAMPER"),
            Idea(content="Fingerprint scanner", technique="SCAMPER"),
            Idea(content="Password manager integration", technique="HMW"),
            Idea(content="Social login", technique="HMW"),
            Idea(content="Face recognition", technique="SCAMPER"),
        ]

        # Mock AI clustering response
        mock_analysis_service.analyze.return_value = Mock(
            response='{"themes": [{"name": "Biometric Security", "idea_indices": [1, 2, 5]}, {"name": "Password Alternatives", "idea_indices": [3, 4]}]}'
        )

        theme_groups = await brainstorming_engine.perform_affinity_mapping(ideas, num_themes=2)

        assert len(theme_groups) == 2
        assert "Biometric Security" in theme_groups
        assert "Password Alternatives" in theme_groups

        # Check ideas are assigned to themes
        for idea in theme_groups["Biometric Security"]:
            assert idea.theme == "Biometric Security"

    @pytest.mark.asyncio
    async def test_affinity_mapping_empty_ideas(self, brainstorming_engine):
        """Test affinity mapping with no ideas."""
        theme_groups = await brainstorming_engine.perform_affinity_mapping([], num_themes=3)

        assert theme_groups == {}


class TestMindMapGeneration:
    """Tests for mind map generation in mermaid syntax."""

    @pytest.mark.asyncio
    async def test_mind_map_generation(self, brainstorming_engine, mock_analysis_service):
        """Test mind map generation with valid mermaid syntax."""
        ideas = [
            Idea(content="Biometric auth", technique="SCAMPER"),
            Idea(content="Password manager", technique="HMW"),
            Idea(content="2FA", technique="SCAMPER"),
        ]

        # Mock AI clustering
        mock_analysis_service.analyze.return_value = Mock(
            response='{"themes": [{"name": "Security", "ideas": ["Biometric auth", "2FA"]}, {"name": "Convenience", "ideas": ["Password manager"]}]}'
        )

        mind_map = await brainstorming_engine.generate_mind_map(ideas, "Authentication")

        assert mind_map.startswith("graph TD")
        assert "Authentication" in mind_map
        assert "Security" in mind_map or "Convenience" in mind_map
        # Check for mermaid node syntax
        assert 'A["' in mind_map or 'B["' in mind_map or 'A -->' in mind_map

    @pytest.mark.asyncio
    async def test_mind_map_no_ideas_raises_error(self, brainstorming_engine):
        """Test that mind map generation fails with no ideas."""
        with pytest.raises(ValueError, match="Cannot generate mind map with no ideas"):
            await brainstorming_engine.generate_mind_map([], "Topic")


class TestInsightsSynthesis:
    """Tests for insights synthesis."""

    @pytest.mark.asyncio
    async def test_synthesize_insights(self, brainstorming_engine, mock_analysis_service):
        """Test insights synthesis extracts themes and opportunities."""
        ideas = [
            Idea(content="Biometric login", technique="SCAMPER"),
            Idea(content="Password manager", technique="HMW"),
            Idea(content="2FA via SMS", technique="SCAMPER"),
        ]

        # Mock AI synthesis
        mock_analysis_service.analyze.return_value = Mock(
            response="""
{
  "key_themes": ["Security Enhancement", "User Experience"],
  "insights_learnings": ["Biometrics reduce friction", "Multiple auth methods needed"],
  "quick_wins": ["Enable 2FA", "Add password manager"],
  "long_term_opportunities": ["Full biometric system", "AI-based fraud detection"],
  "recommended_followup": ["Mind Mapping", "Prototype Testing"]
}
"""
        )

        insights = await brainstorming_engine.synthesize_insights(
            ideas=ideas, techniques_used=["SCAMPER", "HMW"], topic="Authentication"
        )

        assert "key_themes" in insights
        assert "insights_learnings" in insights
        assert "quick_wins" in insights
        assert "long_term_opportunities" in insights
        assert "recommended_followup" in insights

        assert len(insights["key_themes"]) == 2
        assert len(insights["quick_wins"]) == 2
        assert len(insights["long_term_opportunities"]) == 2

    @pytest.mark.asyncio
    async def test_synthesize_empty_ideas(self, brainstorming_engine):
        """Test insights synthesis with no ideas returns empty structure."""
        insights = await brainstorming_engine.synthesize_insights(
            ideas=[], techniques_used=[], topic="Test"
        )

        assert insights["key_themes"] == []
        assert insights["insights_learnings"] == []
        assert insights["quick_wins"] == []
        assert insights["long_term_opportunities"] == []
        assert insights["recommended_followup"] == []


class TestBrainstormingSummaryModel:
    """Tests for BrainstormingSummary data model."""

    def test_summary_to_markdown(self):
        """Test BrainstormingSummary generates valid markdown."""
        from datetime import timedelta
        from gao_dev.core.models.brainstorming_summary import BrainstormingSummary

        ideas = [
            Idea(content="Biometric auth", technique="SCAMPER"),
            Idea(content="Password manager", technique="HMW"),
        ]

        summary = BrainstormingSummary(
            topic="Authentication",
            techniques_used=["SCAMPER", "HMW"],
            ideas_generated=ideas,
            mind_maps=['graph TD\n    A["Auth"]'],
            key_themes=["Security", "UX"],
            insights_learnings=["Multiple methods needed"],
            quick_wins=[Idea(content="Enable 2FA", technique="Synthesis", priority="quick_win")],
            long_term_opportunities=[
                Idea(content="Full biometric", technique="Synthesis", priority="long_term")
            ],
            recommended_followup=["Mind Mapping"],
            session_duration=timedelta(minutes=20),
        )

        markdown = summary.to_markdown()

        assert "# Brainstorming Session: Authentication" in markdown
        assert "SCAMPER" in markdown
        assert "HMW" in markdown
        assert "## Key Themes" in markdown
        assert "## Quick Wins" in markdown
        assert "## Mind Maps" in markdown
        assert "```mermaid" in markdown

    def test_summary_empty_ideas(self):
        """Test BrainstormingSummary with no ideas."""
        from gao_dev.core.models.brainstorming_summary import BrainstormingSummary

        summary = BrainstormingSummary(
            topic="Test", techniques_used=[], ideas_generated=[], session_duration=None
        )

        markdown = summary.to_markdown()

        assert "# Brainstorming Session: Test" in markdown
        assert "*No ideas generated*" in markdown
        assert "*No themes identified*" in markdown


class TestMaryOrchestrator:
    """Tests for Mary's brainstorming facilitation."""

    @pytest.mark.asyncio
    async def test_mary_facilitate_brainstorming(self, tmp_path):
        """Test Mary orchestrates full brainstorming session."""
        from gao_dev.orchestrator.mary_orchestrator import MaryOrchestrator
        from gao_dev.core.workflow_registry import WorkflowRegistry
        from gao_dev.core.prompt_loader import PromptLoader

        # Setup mocks
        workflow_registry = Mock(spec=WorkflowRegistry)
        prompt_loader = Mock(spec=PromptLoader)
        mock_analysis_service = Mock(spec=AIAnalysisService)
        mock_analysis_service.analyze = AsyncMock()

        # Mock AI responses for synthesis
        mock_analysis_service.analyze.return_value = Mock(
            response='{"themes": [{"name": "Security", "ideas": ["Auth"]}], "key_themes": ["Security"], "insights_learnings": ["Insight"], "quick_wins": ["2FA"], "long_term_opportunities": ["Biometric"], "recommended_followup": ["Mind Mapping"]}'
        )

        mary = MaryOrchestrator(
            workflow_registry=workflow_registry,
            prompt_loader=prompt_loader,
            analysis_service=mock_analysis_service,
            project_root=tmp_path,
        )

        # Facilitate brainstorming
        summary = await mary.facilitate_brainstorming(
            topic="Authentication",
            goal=BrainstormingGoal.INNOVATION,
            techniques=["SCAMPER Method"],
        )

        assert summary.topic == "Authentication"
        assert "SCAMPER Method" in summary.techniques_used
        assert len(summary.ideas_generated) == 7  # SCAMPER has 7 lenses
        assert summary.file_path is not None
        assert summary.file_path.exists()

    @pytest.mark.asyncio
    async def test_mary_brainstorming_invalid_technique(self, tmp_path):
        """Test Mary raises error for invalid technique."""
        from gao_dev.orchestrator.mary_orchestrator import MaryOrchestrator
        from gao_dev.core.workflow_registry import WorkflowRegistry
        from gao_dev.core.prompt_loader import PromptLoader

        workflow_registry = Mock(spec=WorkflowRegistry)
        prompt_loader = Mock(spec=PromptLoader)
        mock_analysis_service = Mock(spec=AIAnalysisService)

        mary = MaryOrchestrator(
            workflow_registry=workflow_registry,
            prompt_loader=prompt_loader,
            analysis_service=mock_analysis_service,
            project_root=tmp_path,
        )

        with pytest.raises(ValueError, match="Invalid technique name"):
            await mary.facilitate_brainstorming(
                topic="Test", techniques=["Invalid Technique Name"]
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
