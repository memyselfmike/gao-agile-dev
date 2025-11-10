"""Tests for HelpSystem.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from gao_dev.cli.help_system import HelpSystem
from gao_dev.core.services.ai_analysis_service import AIAnalysisService
from gao_dev.core.state.state_tracker import StateTracker


@pytest.fixture
def mock_analysis_service():
    """Create mock AI analysis service."""
    service = MagicMock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def mock_state_tracker():
    """Create mock state tracker."""
    tracker = MagicMock(spec=StateTracker)
    tracker.get_active_epics.return_value = []
    tracker.get_stories_in_progress.return_value = []
    tracker.get_blocked_stories.return_value = []
    return tracker


@pytest.fixture
def help_system(mock_analysis_service, mock_state_tracker):
    """Create HelpSystem instance."""
    return HelpSystem(mock_analysis_service, mock_state_tracker)


class TestHelpSystem:
    """Test suite for HelpSystem."""

    @pytest.mark.asyncio
    async def test_get_help_greenfield(
        self, help_system, mock_analysis_service
    ):
        """Test help for greenfield project."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = "Start by creating a PRD..."
        mock_analysis_service.analyze.return_value = mock_result

        # Get help
        response = await help_system.get_help("help", Path("/test"))

        # Should return formatted help
        assert "Brian's Help" in response
        assert len(response) > 0

        # Should have called AI
        mock_analysis_service.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_help_active_project(
        self, help_system, mock_analysis_service, mock_state_tracker
    ):
        """Test help for active project."""
        # Mock active project state
        mock_epic = MagicMock()
        mock_state_tracker.get_active_epics.return_value = [mock_epic]

        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = "You have 1 epic in progress..."
        mock_analysis_service.analyze.return_value = mock_result

        # Get help
        response = await help_system.get_help("help", Path("/test"))

        # Should include context
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_get_help_specific_query(
        self, help_system, mock_analysis_service
    ):
        """Test help with specific query."""
        # Mock AI response
        mock_result = MagicMock()
        mock_result.response = "Ceremonies are collaborative meetings..."
        mock_analysis_service.analyze.return_value = mock_result

        # Get help about ceremonies
        response = await help_system.get_help("help with ceremonies", Path("/test"))

        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_get_help_ai_failure_fallback(
        self, help_system, mock_analysis_service
    ):
        """Test fallback help when AI fails."""
        # Mock AI failure
        mock_analysis_service.analyze.side_effect = Exception("AI failed")

        # Get help
        response = await help_system.get_help("help", Path("/test"))

        # Should return fallback help
        assert "Brian's Help" in response
        assert len(response) > 0

    def test_gather_project_context_greenfield(self, help_system):
        """Test context gathering for greenfield project."""
        context = help_system._gather_project_context(Path("/test"))

        assert context["project_state"] == "greenfield"
        assert context["epic_count"] == 0

    def test_gather_project_context_active(
        self, help_system, mock_state_tracker
    ):
        """Test context gathering for active project."""
        # Mock active epics
        mock_epic = MagicMock()
        mock_state_tracker.get_active_epics.return_value = [mock_epic]

        # Mock in-progress stories
        mock_story = MagicMock()
        mock_state_tracker.get_stories_in_progress.return_value = [mock_story]

        context = help_system._gather_project_context(Path("/test"))

        assert context["epic_count"] == 1
        assert context["in_progress_story_count"] == 1
        assert context["project_state"] == "active_development"

    def test_gather_project_context_blocked(
        self, help_system, mock_state_tracker
    ):
        """Test context gathering for blocked project."""
        # Mock blocked stories
        mock_story = MagicMock()
        mock_state_tracker.get_blocked_stories.return_value = [mock_story]

        context = help_system._gather_project_context(Path("/test"))

        assert context["blocked_story_count"] == 1
        # Note: state may be 'planning' or 'blocked' depending on logic

    def test_build_help_prompt(self, help_system):
        """Test help prompt construction."""
        context = {
            "project_state": "greenfield",
            "epic_count": 0,
            "in_progress_story_count": 0,
            "blocked_story_count": 0
        }

        prompt = help_system._build_help_prompt("help", context)

        assert "greenfield" in prompt
        assert "Brian" in prompt
        assert len(prompt) > 100  # Should be substantial

    def test_format_help_response(self, help_system):
        """Test help response formatting."""
        ai_response = "Here's some guidance..."
        formatted = help_system._format_help_response(ai_response)

        assert "Brian's Help" in formatted
        assert "Here's some guidance" in formatted
        assert "Type naturally" in formatted  # Footer

    def test_fallback_help_response_greenfield(self, help_system):
        """Test fallback help for greenfield."""
        context = {"project_state": "greenfield"}
        response = help_system._fallback_help_response(context)

        assert "starting fresh" in response.lower() or "greenfield" in response.lower()
        assert len(response) > 50

    def test_fallback_help_response_active(self, help_system):
        """Test fallback help for active project."""
        context = {
            "project_state": "active_development",
            "epic_count": 2,
            "in_progress_story_count": 3
        }
        response = help_system._fallback_help_response(context)

        assert "2" in response  # Should mention epic count
        assert "3" in response  # Should mention story count

    def test_format_help_panel(self, help_system):
        """Test help panel formatting."""
        from rich.panel import Panel

        panel = help_system.format_help_panel("Test help text")

        assert isinstance(panel, Panel)
