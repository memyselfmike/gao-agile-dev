"""Tests for BrianOrchestrator - Scale-Adaptive Workflow Selection.

Story 5.4: Updated to use orchestrator.models for enums.
Story 21.2: Updated to mock AIAnalysisService instead of Anthropic client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.orchestrator.models import (
    ScaleLevel,
    ProjectType,
    PromptAnalysis,
    WorkflowSequence,
)
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult
from gao_dev.core.providers.exceptions import AnalysisError


@pytest.fixture
def mock_workflow_registry():
    """Create mock workflow registry with test workflows."""
    registry = Mock(spec=WorkflowRegistry)

    # Create mock workflows
    workflows = {
        "tech-spec": WorkflowInfo(
            name="tech-spec",
            description="Technical specification",
            phase=2,
            installed_path=Path("/fake/path/tech-spec")
        ),
        "prd": WorkflowInfo(
            name="prd",
            description="Product Requirements Document",
            phase=2,
            installed_path=Path("/fake/path/prd")
        ),
        "architecture": WorkflowInfo(
            name="architecture",
            description="System Architecture",
            phase=3,
            installed_path=Path("/fake/path/architecture")
        ),
        "create-story": WorkflowInfo(
            name="create-story",
            description="Create user story",
            phase=4,
            installed_path=Path("/fake/path/create-story")
        ),
        "dev-story": WorkflowInfo(
            name="dev-story",
            description="Develop story",
            phase=4,
            installed_path=Path("/fake/path/dev-story")
        ),
        "story-done": WorkflowInfo(
            name="story-done",
            description="Complete story",
            phase=4,
            installed_path=Path("/fake/path/story-done")
        ),
        "game-brief": WorkflowInfo(
            name="game-brief",
            description="Game brief",
            phase=1,
            installed_path=Path("/fake/path/game-brief")
        ),
        "gdd": WorkflowInfo(
            name="gdd",
            description="Game Design Document",
            phase=2,
            installed_path=Path("/fake/path/gdd")
        ),
        "document-project": WorkflowInfo(
            name="document-project",
            description="Document existing project",
            phase=1,
            installed_path=Path("/fake/path/document-project")
        ),
    }

    registry.get_workflow = lambda name: workflows.get(name)
    return registry


@pytest.fixture
def mock_analysis_service():
    """Create mock AIAnalysisService for testing."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def brian_orchestrator(mock_workflow_registry, mock_analysis_service):
    """Create BrianOrchestrator instance for testing."""
    return BrianOrchestrator(
        workflow_registry=mock_workflow_registry,
        analysis_service=mock_analysis_service,
        brian_persona_path=None
    )


class TestScaleLevelAssessment:
    """Test scale level assessment for various prompts."""

    @pytest.mark.asyncio
    async def test_level_0_bug_fix(self, brian_orchestrator, mock_analysis_service):
        """Test Level 0 assessment for simple bug fix."""
        prompt = "Fix the login bug where users can't sign in"

        # Mock the analysis service response
        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 0, "project_type": "bug_fix", "is_greenfield": false, "is_brownfield": true, "is_game_project": false, "estimated_stories": 1, "estimated_epics": 1, "technical_complexity": "low", "domain_complexity": "low", "timeline_hint": "hours", "confidence": 0.9, "reasoning": "Single bug fix requiring 1 story", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=150,
            duration_ms=1200
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_0
        assert len(workflow_sequence.workflows) > 0
        assert "tech-spec" in [w.name for w in workflow_sequence.workflows if w]

    @pytest.mark.asyncio
    async def test_level_1_small_feature(self, brian_orchestrator, mock_analysis_service):
        """Test Level 1 assessment for small feature."""
        prompt = "Add a user profile page with avatar upload"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 1, "project_type": "enhancement", "is_greenfield": false, "is_brownfield": true, "is_game_project": false, "estimated_stories": 3, "estimated_epics": 1, "technical_complexity": "low", "domain_complexity": "low", "timeline_hint": "days", "confidence": 0.85, "reasoning": "Small feature requiring 2-3 stories", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=150,
            duration_ms=1200
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_1
        assert "tech-spec" in [w.name for w in workflow_sequence.workflows if w]

    @pytest.mark.asyncio
    async def test_level_2_medium_project(self, brian_orchestrator, mock_analysis_service):
        """Test Level 2 assessment for medium project."""
        prompt = "Build a todo application with task management, categories, and persistence"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 2, "project_type": "greenfield", "is_greenfield": true, "is_brownfield": false, "is_game_project": false, "estimated_stories": 8, "estimated_epics": 2, "technical_complexity": "medium", "domain_complexity": "low", "timeline_hint": "weeks", "confidence": 0.8, "reasoning": "Medium project requiring PRD and 8 stories across 2 epics", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=200,
            duration_ms=1500
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_2
        assert "prd" in [w.name for w in workflow_sequence.workflows if w]
        assert "tech-spec" in [w.name for w in workflow_sequence.workflows if w]

    @pytest.mark.asyncio
    async def test_level_3_large_project(self, brian_orchestrator, mock_analysis_service):
        """Test Level 3 assessment for large project."""
        prompt = "Create a CRM system with sales tracking, customer management, and reporting modules"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 3, "project_type": "greenfield", "is_greenfield": true, "is_brownfield": false, "is_game_project": false, "estimated_stories": 25, "estimated_epics": 3, "technical_complexity": "high", "domain_complexity": "medium", "timeline_hint": "months", "confidence": 0.85, "reasoning": "Large project requiring architecture and 25 stories across 3 epics", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=250,
            duration_ms=1800
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_3
        assert "prd" in [w.name for w in workflow_sequence.workflows if w]
        assert "architecture" in [w.name for w in workflow_sequence.workflows if w]
        assert workflow_sequence.jit_tech_specs is True

    @pytest.mark.asyncio
    async def test_level_4_enterprise(self, brian_orchestrator, mock_analysis_service):
        """Test Level 4 assessment for enterprise system."""
        prompt = "Build an enterprise ERP system with inventory, HR, finance, sales, and procurement modules"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 4, "project_type": "greenfield", "is_greenfield": true, "is_brownfield": false, "is_game_project": false, "estimated_stories": 60, "estimated_epics": 6, "technical_complexity": "high", "domain_complexity": "high", "timeline_hint": "months", "confidence": 0.75, "reasoning": "Enterprise system requiring architecture and 60+ stories across 6 epics", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=300,
            duration_ms=2000
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_4
        assert "prd" in [w.name for w in workflow_sequence.workflows if w]
        assert "architecture" in [w.name for w in workflow_sequence.workflows if w]
        assert workflow_sequence.jit_tech_specs is True


class TestProjectTypeRouting:
    """Test routing based on project type."""

    @pytest.mark.asyncio
    async def test_greenfield_routing(self, brian_orchestrator, mock_analysis_service):
        """Test greenfield project routing."""
        prompt = "Build a new todo app from scratch"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 2, "project_type": "greenfield", "is_greenfield": true, "is_brownfield": false, "is_game_project": false, "estimated_stories": 8, "estimated_epics": 2, "technical_complexity": "medium", "domain_complexity": "low", "timeline_hint": "weeks", "confidence": 0.85, "reasoning": "New greenfield project", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=180,
            duration_ms=1400
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.project_type == ProjectType.GREENFIELD
        # Should NOT include document-project workflow
        assert "document-project" not in [w.name for w in workflow_sequence.workflows if w]

    @pytest.mark.asyncio
    async def test_brownfield_routing(self, brian_orchestrator, mock_analysis_service):
        """Test brownfield project routing (should start with document-project)."""
        prompt = "Add authentication to our existing application"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 1, "project_type": "brownfield", "is_greenfield": false, "is_brownfield": true, "is_game_project": false, "estimated_stories": 3, "estimated_epics": 1, "technical_complexity": "medium", "domain_complexity": "medium", "timeline_hint": "days", "confidence": 0.9, "reasoning": "Enhancement to existing codebase", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=160,
            duration_ms=1300
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.project_type == ProjectType.BROWNFIELD
        # Should include document-project workflow first
        workflow_names = [w.name for w in workflow_sequence.workflows if w]
        assert "document-project" in workflow_names
        assert workflow_names.index("document-project") == 0  # First workflow

    @pytest.mark.asyncio
    async def test_game_project_routing(self, brian_orchestrator, mock_analysis_service):
        """Test game project routing."""
        prompt = "Create a 2D platformer game with collectibles and power-ups"

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 2, "project_type": "game", "is_greenfield": true, "is_brownfield": false, "is_game_project": true, "estimated_stories": 12, "estimated_epics": 2, "technical_complexity": "medium", "domain_complexity": "medium", "timeline_hint": "weeks", "confidence": 0.8, "reasoning": "Game development project", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=190,
            duration_ms=1450
        )

        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        assert workflow_sequence.project_type == ProjectType.GAME
        workflow_names = [w.name for w in workflow_sequence.workflows if w]
        # Game projects should use game-specific workflows
        assert "game-brief" in workflow_names or "gdd" in workflow_names


class TestClarificationQuestions:
    """Test clarification question handling."""

    @pytest.mark.asyncio
    async def test_ambiguous_prompt_returns_questions(self, brian_orchestrator, mock_analysis_service):
        """Test that ambiguous prompts return clarifying questions."""
        prompt = "Fix it"

        # Mock _analyze_prompt to return ambiguous analysis
        analysis = PromptAnalysis(
            scale_level=ScaleLevel.LEVEL_0,
            project_type=ProjectType.BUG_FIX,
            is_greenfield=False,
            is_brownfield=True,
            is_game_project=False,
            estimated_stories=1,
            estimated_epics=1,
            technical_complexity="low",
            domain_complexity="low",
            timeline_hint=None,
            confidence=0.3,
            reasoning="Prompt too ambiguous to assess",
            needs_clarification=True,
            clarifying_questions=[
                "What specific issue needs to be fixed?",
                "Is this a bug fix or a feature enhancement?"
            ]
        )

        with patch.object(brian_orchestrator, '_analyze_prompt', return_value=analysis):
            workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        # When clarification needed, workflow list should be empty
        assert len(workflow_sequence.workflows) == 0
        assert "Clarification needed" in workflow_sequence.routing_rationale


class TestFallbackHandling:
    """Test fallback behavior when AI analysis fails."""

    @pytest.mark.asyncio
    async def test_ai_failure_fallback(self, brian_orchestrator, mock_analysis_service):
        """Test that AI failure results in conservative fallback."""
        prompt = "Build a todo app"

        # Simulate AI failure
        mock_analysis_service.analyze.side_effect = AnalysisError("API Error")
        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(prompt)

        # Should fallback to conservative Level 2
        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_2 or len(workflow_sequence.workflows) == 0


class TestScaleLevelDescription:
    """Test scale level description utility."""

    def test_get_scale_level_descriptions(self, brian_orchestrator):
        """Test that all scale levels have descriptions."""
        for level in ScaleLevel:
            description = brian_orchestrator.get_scale_level_description(level)
            assert isinstance(description, str)
            assert len(description) > 0
            assert "story" in description.lower() or "stories" in description.lower()


class TestForceScaleLevel:
    """Test forcing scale level override."""

    @pytest.mark.asyncio
    async def test_force_scale_level_override(self, brian_orchestrator, mock_analysis_service):
        """Test that force_scale_level overrides AI assessment."""
        prompt = "Fix a bug"  # Would normally be Level 0

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response='{"scale_level": 0, "project_type": "bug_fix", "is_greenfield": false, "is_brownfield": true, "is_game_project": false, "estimated_stories": 1, "estimated_epics": 1, "technical_complexity": "low", "domain_complexity": "low", "timeline_hint": "hours", "confidence": 0.9, "reasoning": "Bug fix", "needs_clarification": false, "clarifying_questions": []}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=140,
            duration_ms=1100
        )

        # Force Level 3 even though AI would choose Level 0
        workflow_sequence = await brian_orchestrator.assess_and_select_workflows(
            prompt,
            force_scale_level=ScaleLevel.LEVEL_3
        )

        assert workflow_sequence.scale_level == ScaleLevel.LEVEL_3
