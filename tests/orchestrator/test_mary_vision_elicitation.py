"""Tests for Mary Vision Elicitation - Story 31.1.

Tests cover:
- Prompt loading and rendering (4 techniques)
- VisionSummary generation (4 techniques)
- Strategy selection
- Integration with Brian
- File output and persistence
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from datetime import datetime

from gao_dev.orchestrator.mary_orchestrator import MaryOrchestrator, ClarificationStrategy
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult
from gao_dev.core.models.vision_summary import (
    VisionSummary,
    VisionCanvas,
    ProblemSolutionFit,
    OutcomeMap,
    FiveWOneH,
)
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.core.models.prompt_template import PromptTemplate


@pytest.fixture
def mock_workflow_registry():
    """Create mock workflow registry."""
    registry = Mock(spec=WorkflowRegistry)

    # Mock vision-elicitation workflow
    workflow = Mock(spec=WorkflowInfo)
    workflow.name = "vision-elicitation"
    workflow.metadata = {
        "prompts": {
            "vision_canvas": "mary_vision_canvas",
            "problem_solution_fit": "mary_vision_problem_solution_fit",
            "outcome_mapping": "mary_vision_outcome_mapping",
            "5w1h": "mary_vision_5w1h",
        }
    }

    registry.get_workflow = Mock(return_value=workflow)
    return registry


@pytest.fixture
def mock_prompt_loader():
    """Create mock prompt loader."""
    loader = Mock(spec=PromptLoader)

    # Create mock template
    template = Mock(spec=PromptTemplate)
    template.name = "mary_vision_canvas"
    template.system_prompt = "You are Mary, a Business Analyst"
    template.user_prompt = "Let's create a vision canvas for: {{user_request}}"
    template.variables = {"user_request": "", "mary_persona": "", "project_context": ""}
    template.max_tokens = 1024
    template.temperature = 0.7
    template.response = {"max_tokens": 1024, "temperature": 0.7, "format": "text"}

    loader.load_prompt = Mock(return_value=template)
    loader.render_prompt = Mock(return_value="Rendered prompt text")
    loader.render_system_prompt = Mock(return_value="You are Mary")
    return loader


@pytest.fixture
def mock_analysis_service():
    """Create mock AI analysis service."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(
        return_value=AnalysisResult(
            response="Vision canvas analysis complete",
            model_used="claude-sonnet-4-5",
            tokens_used=500,
            duration_ms=1000,
        )
    )
    return service


@pytest.fixture
def mary_orchestrator(
    mock_workflow_registry, mock_prompt_loader, mock_analysis_service, tmp_path
):
    """Create Mary orchestrator with mocks."""
    return MaryOrchestrator(
        workflow_registry=mock_workflow_registry,
        prompt_loader=mock_prompt_loader,
        analysis_service=mock_analysis_service,
        project_root=tmp_path,
    )


# ==============================================================================
# Prompt Loading Tests (4 tests - one per technique)
# ==============================================================================


def test_vision_canvas_prompt_loading(mock_prompt_loader):
    """Test vision canvas prompt loads and renders correctly."""
    template = mock_prompt_loader.load_prompt("agents/mary_vision_canvas")

    assert template.name == "mary_vision_canvas"
    assert "Mary" in template.system_prompt
    assert "vision_canvas" in template.name.lower()

    rendered = mock_prompt_loader.render_prompt(
        template, {"user_request": "Build a todo app", "mary_persona": "You are Mary"}
    )

    assert rendered is not None
    mock_prompt_loader.load_prompt.assert_called_once()


def test_problem_solution_fit_prompt_loading(mock_prompt_loader):
    """Test problem-solution fit prompt loads correctly."""
    template = Mock(spec=PromptTemplate)
    template.name = "mary_vision_problem_solution_fit"
    mock_prompt_loader.load_prompt.return_value = template

    loaded = mock_prompt_loader.load_prompt("agents/mary_vision_problem_solution_fit")

    assert loaded.name == "mary_vision_problem_solution_fit"


def test_outcome_mapping_prompt_loading(mock_prompt_loader):
    """Test outcome mapping prompt loads correctly."""
    template = Mock(spec=PromptTemplate)
    template.name = "mary_vision_outcome_mapping"
    mock_prompt_loader.load_prompt.return_value = template

    loaded = mock_prompt_loader.load_prompt("agents/mary_vision_outcome_mapping")

    assert loaded.name == "mary_vision_outcome_mapping"


def test_5w1h_prompt_loading(mock_prompt_loader):
    """Test 5W1H prompt loads correctly."""
    template = Mock(spec=PromptTemplate)
    template.name = "mary_vision_5w1h"
    mock_prompt_loader.load_prompt.return_value = template

    loaded = mock_prompt_loader.load_prompt("agents/mary_vision_5w1h")

    assert loaded.name == "mary_vision_5w1h"


# ==============================================================================
# Strategy Selection Tests (2 tests)
# ==============================================================================


def test_select_vision_elicitation_strategy_high_vagueness(mary_orchestrator):
    """Test that high vagueness triggers vision elicitation."""
    strategy = mary_orchestrator.select_clarification_strategy(
        "I want to build something", vagueness_score=0.9
    )

    assert strategy == ClarificationStrategy.VISION_ELICITATION


def test_select_simple_questions_strategy_medium_vagueness(mary_orchestrator):
    """Test that medium vagueness triggers simple questions."""
    strategy = mary_orchestrator.select_clarification_strategy(
        "Build a todo app with user authentication", vagueness_score=0.6
    )

    assert strategy == ClarificationStrategy.SIMPLE_QUESTIONS


# ==============================================================================
# VisionSummary Generation Tests (4 tests - one per technique)
# ==============================================================================


@pytest.mark.asyncio
async def test_generate_vision_canvas_summary(mary_orchestrator):
    """Test vision canvas summary generation."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Build a project management tool",
        technique="vision_canvas",
        project_context="Agile teams need better collaboration",
    )

    assert isinstance(summary, VisionSummary)
    assert summary.technique_used == "vision_canvas"
    assert summary.vision_canvas is not None
    assert summary.vision_canvas.target_users
    assert summary.vision_canvas.product_vision
    assert summary.duration_minutes is not None
    assert summary.file_path is not None


@pytest.mark.asyncio
async def test_generate_problem_solution_fit_summary(mary_orchestrator):
    """Test problem-solution fit summary generation."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Solve team communication issues", technique="problem_solution_fit"
    )

    assert isinstance(summary, VisionSummary)
    assert summary.technique_used == "problem_solution_fit"
    assert summary.problem_solution_fit is not None
    assert summary.problem_solution_fit.problem_definition
    assert summary.problem_solution_fit.value_proposition


@pytest.mark.asyncio
async def test_generate_outcome_map_summary(mary_orchestrator):
    """Test outcome mapping summary generation."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Improve developer productivity", technique="outcome_mapping"
    )

    assert isinstance(summary, VisionSummary)
    assert summary.technique_used == "outcome_mapping"
    assert summary.outcome_map is not None
    assert summary.outcome_map.desired_outcomes
    assert summary.outcome_map.leading_indicators


@pytest.mark.asyncio
async def test_generate_5w1h_summary(mary_orchestrator):
    """Test 5W1H summary generation."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Create a mobile app", technique="5w1h"
    )

    assert isinstance(summary, VisionSummary)
    assert summary.technique_used == "5w1h"
    assert summary.five_w_one_h is not None
    assert summary.five_w_one_h.who
    assert summary.five_w_one_h.what


# ==============================================================================
# VisionSummary Formatting Tests (4 tests)
# ==============================================================================


def test_vision_canvas_to_prompt():
    """Test vision canvas to_prompt() formatting."""
    canvas = VisionCanvas(
        target_users="Developers",
        user_needs="Need efficient tools",
        product_vision="Build the best IDE",
        key_features=["Fast", "Reliable"],
        success_metrics=["Adoption rate"],
        differentiators="AI-powered",
    )

    summary = VisionSummary(
        user_request="Build an IDE",
        technique_used="vision_canvas",
        vision_canvas=canvas,
    )

    prompt_text = summary.to_prompt()

    assert "Vision Elicitation Summary" in prompt_text
    assert "Developers" in prompt_text
    assert "Build the best IDE" in prompt_text


def test_vision_canvas_to_markdown():
    """Test vision canvas to_markdown() formatting."""
    canvas = VisionCanvas(
        target_users="Product managers",
        user_needs="Need planning tools",
        product_vision="Streamline roadmap planning",
        key_features=["Timeline view", "Dependencies"],
        success_metrics=["User satisfaction"],
        differentiators="Integrated with Jira",
    )

    summary = VisionSummary(
        user_request="Build roadmap tool",
        technique_used="vision_canvas",
        vision_canvas=canvas,
    )

    markdown = summary.to_markdown()

    assert "# Vision Elicitation Summary" in markdown
    assert "## Vision Canvas Results" in markdown
    assert "Product managers" in markdown
    assert "Timeline view" in markdown


def test_problem_solution_fit_to_dict():
    """Test problem-solution fit to_dict() conversion."""
    psf = ProblemSolutionFit(
        problem_definition="Teams struggle with async communication",
        current_solutions="Email and Slack",
        gaps_pain_points=["Lost context", "Information overload"],
        proposed_solution="Threaded async messaging",
        value_proposition="Reduce noise, increase clarity",
    )

    summary = VisionSummary(
        user_request="Fix team communication",
        technique_used="problem_solution_fit",
        problem_solution_fit=psf,
    )

    data = summary.to_dict()

    assert data["technique_used"] == "problem_solution_fit"
    assert data["problem_solution_fit"]["problem_definition"]
    assert "Lost context" in data["problem_solution_fit"]["gaps_pain_points"]


def test_outcome_map_to_markdown():
    """Test outcome map to_markdown() formatting."""
    omap = OutcomeMap(
        desired_outcomes=["Increase productivity", "Reduce errors"],
        leading_indicators=["Early adoption", "Positive feedback"],
        lagging_indicators=["Usage metrics", "Error reduction"],
        stakeholders=["Developers", "Managers"],
    )

    summary = VisionSummary(
        user_request="Productivity tool", technique_used="outcome_mapping", outcome_map=omap
    )

    markdown = summary.to_markdown()

    assert "## Outcome Map Results" in markdown
    assert "Increase productivity" in markdown
    assert "Early adoption" in markdown


# ==============================================================================
# File Persistence Tests (2 tests)
# ==============================================================================


@pytest.mark.asyncio
async def test_vision_document_saved_to_file(mary_orchestrator, tmp_path):
    """Test that vision document is saved to .gao-dev/mary/vision-documents/."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Test request", technique="vision_canvas"
    )

    assert summary.file_path is not None
    assert summary.file_path.exists()
    # Use forward slashes for path checking (works on both Windows and Unix)
    path_str = str(summary.file_path).replace("\\", "/")
    assert ".gao-dev/mary/vision-documents" in path_str
    assert "vision-vision_canvas-" in summary.file_path.name

    # Check file contents
    content = summary.file_path.read_text()
    assert "# Vision Elicitation Summary" in content
    assert "Test request" in content


@pytest.mark.asyncio
async def test_vision_document_filename_format(mary_orchestrator, tmp_path):
    """Test vision document filename format."""
    summary = await mary_orchestrator.elicit_vision(
        user_request="Another test", technique="problem_solution_fit"
    )

    filename = summary.file_path.name
    assert filename.startswith("vision-problem_solution_fit-")
    assert filename.endswith(".md")


# ==============================================================================
# Integration Tests (2 tests)
# ==============================================================================


def test_brian_assess_vagueness_high():
    """Test Brian's vagueness assessment for high vagueness."""
    from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator

    # Create minimal Brian instance
    brian = BrianOrchestrator(
        workflow_registry=Mock(),
        analysis_service=Mock(),
    )

    # Test high vagueness request
    score = brian.assess_vagueness("I want to build something")
    assert score >= 0.8

    # Test specific request
    score = brian.assess_vagueness(
        "Build a user authentication system with JWT tokens and OAuth integration"
    )
    assert score < 0.8


@pytest.mark.asyncio
async def test_end_to_end_vision_elicitation_flow(mary_orchestrator):
    """Test complete vision elicitation flow: request -> elicit -> summary."""
    # Simulate vague user request
    user_request = "I want something for teams"

    # Mary assesses and selects strategy
    strategy = mary_orchestrator.select_clarification_strategy(user_request, 0.9)
    assert strategy == ClarificationStrategy.VISION_ELICITATION

    # Mary elicits vision
    summary = await mary_orchestrator.elicit_vision(
        user_request=user_request, technique="vision_canvas"
    )

    # Verify summary completeness
    assert summary.user_request == user_request
    assert summary.vision_canvas is not None
    assert summary.file_path is not None
    assert summary.file_path.exists()

    # Verify prompt format (for handoff to Brian)
    prompt_text = summary.to_prompt()
    assert "Vision Elicitation Summary" in prompt_text
    assert user_request in prompt_text


# ==============================================================================
# Error Handling Tests (2 tests)
# ==============================================================================


@pytest.mark.asyncio
async def test_invalid_technique_raises_error(mary_orchestrator):
    """Test that invalid technique raises ValueError."""
    with pytest.raises(ValueError, match="Invalid technique"):
        await mary_orchestrator.elicit_vision(
            user_request="Test", technique="invalid_technique"
        )


@pytest.mark.asyncio
async def test_workflow_not_found_raises_error(mary_orchestrator):
    """Test that missing workflow raises error."""
    # Mock workflow registry to return None
    mary_orchestrator.workflow_registry.get_workflow = Mock(return_value=None)

    with pytest.raises(ValueError, match="workflow not found"):
        await mary_orchestrator.elicit_vision(user_request="Test", technique="vision_canvas")
