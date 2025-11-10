"""Tests for ConversationalBrian - Intent parsing and conversational flow.

Story 30.3: Comprehensive tests for conversational Brian integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from gao_dev.orchestrator.conversational_brian import (
    ConversationalBrian,
    ConversationContext,
)
from gao_dev.orchestrator.intent_parser import IntentParser, IntentType, Intent
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.models.workflow import WorkflowInfo


# ==================== Fixtures ====================


@pytest.fixture
def mock_brian_orchestrator():
    """Create mock BrianOrchestrator."""
    brian = MagicMock()
    brian.assess_and_select_workflows = AsyncMock()
    return brian


@pytest.fixture
def conversational_brian(mock_brian_orchestrator):
    """Create ConversationalBrian instance."""
    return ConversationalBrian(mock_brian_orchestrator)


@pytest.fixture
def conversation_context():
    """Create ConversationContext for testing."""
    return ConversationContext(project_root="/test/project", session_history=[])


@pytest.fixture
def sample_workflow_sequence():
    """Create sample WorkflowSequence for testing."""
    workflows = [
        WorkflowInfo(
            name="prd", description="Product Requirements", phase=2, installed_path=Path("/fake/prd")
        ),
        WorkflowInfo(
            name="tech-spec",
            description="Technical Spec",
            phase=2,
            installed_path=Path("/fake/tech-spec"),
        ),
    ]

    return WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=workflows,
        project_type=ProjectType.SOFTWARE,
        routing_rationale="Small feature requiring PRD and tech spec",
        phase_breakdown={"Phase 2: Planning": ["prd", "tech-spec"]},
        jit_tech_specs=False,
        estimated_stories=8,
        estimated_epics=1,
    )


# ==================== IntentParser Tests ====================


def test_intent_parser_feature_request():
    """Test intent parsing for feature requests."""
    parser = IntentParser()

    # Test various feature request phrasings
    assert parser.parse("I want to build a todo app").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Add authentication to my app").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Fix the login bug").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Create a new API endpoint").type == IntentType.FEATURE_REQUEST
    assert parser.parse("Implement user registration").type == IntentType.FEATURE_REQUEST


def test_intent_parser_confirmation_positive():
    """Test intent parsing for positive confirmations."""
    parser = IntentParser()

    positive_inputs = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed", "go ahead"]

    for input_text in positive_inputs:
        intent = parser.parse(input_text)
        assert intent.type == IntentType.CONFIRMATION
        assert intent.is_positive is True


def test_intent_parser_confirmation_negative():
    """Test intent parsing for negative confirmations."""
    parser = IntentParser()

    negative_inputs = ["no", "nope", "nah", "cancel", "abort", "stop"]

    for input_text in negative_inputs:
        intent = parser.parse(input_text)
        assert intent.type == IntentType.CONFIRMATION
        assert intent.is_positive is False


def test_intent_parser_question():
    """Test intent parsing for questions."""
    parser = IntentParser()

    assert parser.parse("What's the status?").type == IntentType.QUESTION
    assert parser.parse("How do I do this?").type == IntentType.QUESTION
    assert parser.parse("Why is this happening?").type == IntentType.QUESTION
    assert parser.parse("When will it be done?").type == IntentType.QUESTION
    assert parser.parse("What is the current progress?").type == IntentType.QUESTION


def test_intent_parser_help():
    """Test intent parsing for help requests."""
    parser = IntentParser()

    assert parser.parse("help").type == IntentType.HELP
    assert parser.parse("?").type == IntentType.HELP
    assert parser.parse("what can you do").type == IntentType.HELP


def test_intent_parser_unclear():
    """Test intent parsing for unclear input."""
    parser = IntentParser()

    assert parser.parse("asdf qwerty zxcv").type == IntentType.UNCLEAR
    assert parser.parse("gibberish").type == IntentType.UNCLEAR
    assert parser.parse("123 456").type == IntentType.UNCLEAR


# ==================== ConversationalBrian Tests ====================


@pytest.mark.asyncio
async def test_feature_request_analysis(
    conversational_brian, conversation_context, sample_workflow_sequence, mock_brian_orchestrator
):
    """Test feature request analysis flow."""
    # Mock Brian's assessment
    mock_brian_orchestrator.assess_and_select_workflows.return_value = sample_workflow_sequence

    # Handle feature request
    responses = []
    async for response in conversational_brian.handle_input(
        "I want to add authentication", conversation_context
    ):
        responses.append(response)

    # Assert we got multiple responses
    assert len(responses) >= 3

    # Assert acknowledgment
    assert "analyze" in responses[0].lower()

    # Assert analysis formatting
    analysis_text = responses[1]
    assert "Level 2" in analysis_text or "Small feature" in analysis_text
    assert "prd" in analysis_text.lower()
    assert "tech-spec" in analysis_text.lower()

    # Assert confirmation request
    assert "Shall I proceed" in responses[-1] or "yes/no" in responses[-1]

    # Assert pending confirmation stored
    assert conversation_context.pending_confirmation is not None

    # Assert Brian was called correctly
    mock_brian_orchestrator.assess_and_select_workflows.assert_called_once_with(
        "I want to add authentication"
    )


@pytest.mark.asyncio
async def test_feature_request_error_handling(conversational_brian, conversation_context):
    """Test error handling during feature request analysis."""
    # Mock Brian to raise an error
    conversational_brian.brian.assess_and_select_workflows = AsyncMock(
        side_effect=Exception("Analysis failed")
    )

    # Handle feature request
    responses = []
    async for response in conversational_brian.handle_input(
        "Build something", conversation_context
    ):
        responses.append(response)

    # Assert error handling
    assert any("error" in r.lower() for r in responses)
    assert any("rephrase" in r.lower() or "details" in r.lower() for r in responses)

    # Assert no pending confirmation
    assert conversation_context.pending_confirmation is None


@pytest.mark.asyncio
async def test_confirmation_positive(conversational_brian, conversation_context, sample_workflow_sequence):
    """Test positive confirmation flow."""
    # Set pending confirmation
    conversation_context.pending_confirmation = sample_workflow_sequence

    # Handle positive confirmation
    responses = []
    async for response in conversational_brian.handle_input("yes", conversation_context):
        responses.append(response)

    # Assert positive acknowledgment
    assert any("great" in r.lower() or "coordinate" in r.lower() for r in responses)

    # Assert pending confirmation cleared
    assert conversation_context.pending_confirmation is None


@pytest.mark.asyncio
async def test_confirmation_negative(conversational_brian, conversation_context, sample_workflow_sequence):
    """Test negative confirmation flow."""
    # Set pending confirmation
    conversation_context.pending_confirmation = sample_workflow_sequence

    # Handle negative confirmation
    responses = []
    async for response in conversational_brian.handle_input("no", conversation_context):
        responses.append(response)

    # Assert negative acknowledgment
    assert any("no problem" in r.lower() or "different approach" in r.lower() for r in responses)

    # Assert pending confirmation cleared
    assert conversation_context.pending_confirmation is None


@pytest.mark.asyncio
async def test_confirmation_without_pending(conversational_brian, conversation_context):
    """Test confirmation without pending confirmation."""
    # No pending confirmation
    conversation_context.pending_confirmation = None

    # Handle confirmation
    responses = []
    async for response in conversational_brian.handle_input("yes", conversation_context):
        responses.append(response)

    # Assert helpful message
    assert len(responses) == 1
    assert "not sure" in responses[0].lower() or "confirming" in responses[0].lower()


@pytest.mark.asyncio
async def test_question_handling(conversational_brian, conversation_context):
    """Test question handling."""
    # Handle status question
    responses = []
    async for response in conversational_brian.handle_input("What's the status?", conversation_context):
        responses.append(response)

    assert len(responses) == 1
    assert "status" in responses[0].lower()

    # Handle workflow question
    responses = []
    async for response in conversational_brian.handle_input("What workflows?", conversation_context):
        responses.append(response)

    assert len(responses) == 1
    assert "workflow" in responses[0].lower()


@pytest.mark.asyncio
async def test_help_request(conversational_brian, conversation_context):
    """Test help request."""
    # Handle help
    responses = []
    async for response in conversational_brian.handle_input("help", conversation_context):
        responses.append(response)

    assert len(responses) == 1
    help_text = responses[0]

    # Assert help includes key information
    assert "feature" in help_text.lower() or "build" in help_text.lower()
    assert "exit" in help_text.lower() or "quit" in help_text.lower()


@pytest.mark.asyncio
async def test_unclear_input_handling(conversational_brian, conversation_context):
    """Test unclear input handling."""
    # Handle gibberish
    responses = []
    async for response in conversational_brian.handle_input("asdf qwerty", conversation_context):
        responses.append(response)

    assert len(responses) == 1
    unclear_text = responses[0]

    # Assert clarification request
    assert "not" in unclear_text.lower() and ("sure" in unclear_text.lower() or "mean" in unclear_text.lower())
    assert "help" in unclear_text.lower() or "rephrase" in unclear_text.lower()


# ==================== Formatting Tests ====================


def test_format_analysis(conversational_brian, sample_workflow_sequence):
    """Test analysis formatting."""
    formatted = conversational_brian._format_analysis(sample_workflow_sequence)

    # Assert key sections present
    assert "Level 2" in formatted
    assert "software" in formatted.lower()
    assert "prd" in formatted.lower()
    assert "tech-spec" in formatted.lower()
    assert "Small feature" in formatted


def test_describe_scale_level(conversational_brian):
    """Test scale level descriptions."""
    assert "Level 0" in conversational_brian._describe_scale_level(ScaleLevel.LEVEL_0)
    assert "Level 1" in conversational_brian._describe_scale_level(ScaleLevel.LEVEL_1)
    assert "Level 2" in conversational_brian._describe_scale_level(ScaleLevel.LEVEL_2)
    assert "Level 3" in conversational_brian._describe_scale_level(ScaleLevel.LEVEL_3)
    assert "Level 4" in conversational_brian._describe_scale_level(ScaleLevel.LEVEL_4)


def test_format_workflows_empty(conversational_brian):
    """Test workflow formatting with empty list."""
    formatted = conversational_brian._format_workflows([])
    assert "Direct implementation" in formatted or "no formal workflows" in formatted


def test_format_workflows(conversational_brian):
    """Test workflow formatting."""
    workflows = [
        WorkflowInfo(
            name="prd", description="PRD", phase=2, installed_path=Path("/fake/prd")
        ),
        WorkflowInfo(
            name="tech-spec", description="Spec", phase=2, installed_path=Path("/fake/spec")
        ),
    ]

    formatted = conversational_brian._format_workflows(workflows)
    assert "1. prd" in formatted
    assert "2. tech-spec" in formatted


def test_estimate_duration(conversational_brian, sample_workflow_sequence):
    """Test duration estimation."""
    # Small workflow count
    sample_workflow_sequence.workflows = [
        WorkflowInfo(name="test", description="Test", phase=1, installed_path=Path("/fake"))
    ]
    duration = conversational_brian._estimate_duration(sample_workflow_sequence)
    assert "hour" in duration.lower()

    # Medium workflow count
    sample_workflow_sequence.workflows = [
        WorkflowInfo(name=f"test{i}", description="Test", phase=1, installed_path=Path("/fake"))
        for i in range(4)
    ]
    duration = conversational_brian._estimate_duration(sample_workflow_sequence)
    assert "hours" in duration.lower() or "hour" in duration.lower()
