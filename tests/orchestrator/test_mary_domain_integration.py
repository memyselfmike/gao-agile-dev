"""Tests for Mary's domain-specific clarification integration.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.4 - Domain-Specific Question Libraries (Integration Tests)
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from gao_dev.orchestrator.mary_orchestrator import MaryOrchestrator
from gao_dev.orchestrator.domain_question_library import DomainType
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.prompt_loader import PromptLoader
from gao_dev.core.services.ai_analysis_service import AIAnalysisService


@pytest.fixture
def mock_workflow_registry():
    """Create mock workflow registry."""
    registry = MagicMock(spec=WorkflowRegistry)
    return registry


@pytest.fixture
def mock_prompt_loader():
    """Create mock prompt loader."""
    loader = MagicMock(spec=PromptLoader)
    return loader


@pytest.fixture
def mock_analysis_service():
    """Create mock analysis service."""
    service = MagicMock(spec=AIAnalysisService)
    return service


@pytest.fixture
def mary_orchestrator(mock_workflow_registry, mock_prompt_loader, mock_analysis_service):
    """Create Mary orchestrator with mocks."""
    return MaryOrchestrator(
        workflow_registry=mock_workflow_registry,
        prompt_loader=mock_prompt_loader,
        analysis_service=mock_analysis_service,
        conversation_manager=None,
        project_root=Path.cwd(),
    )


class TestMaryDomainIntegration:
    """Test Mary's integration with domain question library."""

    @pytest.mark.asyncio
    async def test_get_clarification_questions_web_app(self, mary_orchestrator):
        """Test getting clarification questions for web app."""
        user_request = "I want to build a web application for managing tasks"

        result = await mary_orchestrator.get_clarification_questions(user_request)

        assert "domain" in result
        assert "confidence" in result
        assert "questions" in result
        assert "focus_areas" in result

        assert result["domain"] == "web_app"
        assert result["confidence"] > 0.7
        assert len(result["questions"]) > 0
        assert len(result["focus_areas"]) > 0

    @pytest.mark.asyncio
    async def test_get_clarification_questions_mobile_app(self, mary_orchestrator):
        """Test getting clarification questions for mobile app."""
        user_request = "Need to create an iOS app for fitness tracking"

        result = await mary_orchestrator.get_clarification_questions(user_request)

        assert result["domain"] == "mobile_app"
        assert result["confidence"] > 0.7
        assert len(result["questions"]) > 0

        # Should contain mobile-specific questions
        questions_text = " ".join(result["questions"]).lower()
        assert any(
            keyword in questions_text
            for keyword in ["ios", "android", "mobile", "app store"]
        )

    @pytest.mark.asyncio
    async def test_get_clarification_questions_with_focus(self, mary_orchestrator):
        """Test getting questions with specific focus area."""
        user_request = "Build a web app with user authentication"

        result = await mary_orchestrator.get_clarification_questions(
            user_request, focus_area="authentication"
        )

        assert result["domain"] == "web_app"
        assert len(result["questions"]) > 0

        # Questions should be authentication-focused
        questions_text = " ".join(result["questions"]).lower()
        assert any(
            keyword in questions_text
            for keyword in ["auth", "login", "password", "token"]
        )

    @pytest.mark.asyncio
    async def test_get_clarification_questions_with_context(self, mary_orchestrator):
        """Test getting questions with project context."""
        user_request = "Build something for users"
        project_context = {
            "existing_tech": "Python Django",
            "team_size": 3,
        }

        result = await mary_orchestrator.get_clarification_questions(
            user_request, project_context=project_context
        )

        assert "domain" in result
        assert "questions" in result
        # Context should help with domain detection

    @pytest.mark.asyncio
    async def test_domain_library_initialized(self, mary_orchestrator):
        """Test that domain library is initialized in Mary."""
        assert hasattr(mary_orchestrator, "domain_library")
        assert mary_orchestrator.domain_library is not None

        # Should have libraries loaded
        assert len(mary_orchestrator.domain_library.libraries) > 0

    @pytest.mark.asyncio
    async def test_focus_areas_available(self, mary_orchestrator):
        """Test that focus areas are returned for exploration."""
        user_request = "Build a REST API service"

        result = await mary_orchestrator.get_clarification_questions(user_request)

        assert result["domain"] == "api_service"
        assert len(result["focus_areas"]) > 0

        # Focus areas should not include special sections
        assert "general" not in result["focus_areas"]
        assert "focus_discovery" not in result["focus_areas"]
