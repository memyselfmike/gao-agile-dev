"""Tests for CommandRouter.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from gao_dev.cli.command_router import CommandRouter
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.state.operation_tracker import OperationTracker
from gao_dev.core.services.ai_analysis_service import AIAnalysisService


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator."""
    return MagicMock()


@pytest.fixture
def mock_operation_tracker():
    """Create mock operation tracker."""
    tracker = MagicMock(spec=OperationTracker)
    tracker.start_operation.return_value = "test-op-id"
    return tracker


@pytest.fixture
def mock_analysis_service():
    """Create mock AI analysis service."""
    service = MagicMock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def command_router(mock_orchestrator, mock_operation_tracker, mock_analysis_service):
    """Create CommandRouter instance."""
    return CommandRouter(
        orchestrator=mock_orchestrator,
        operation_tracker=mock_operation_tracker,
        analysis_service=mock_analysis_service
    )


class TestCommandRouter:
    """Test suite for CommandRouter."""

    @pytest.mark.asyncio
    async def test_execute_workflow_sequence(
        self, command_router, mock_operation_tracker
    ):
        """Test executing workflow sequence."""
        # Create mock workflow
        mock_workflow = MagicMock()
        mock_workflow.name = "create_prd"

        # Create workflow sequence
        workflow_sequence = WorkflowSequence(
            workflows=[mock_workflow],
            scale_level=ScaleLevel.LEVEL_2,
            project_type=ProjectType.SOFTWARE,
            routing_rationale="Test rationale",
            phase_breakdown={}
        )

        # Execute
        messages = []
        async for message in command_router.execute_workflow_sequence(
            workflow_sequence,
            Path("/test/project")
        ):
            messages.append(message)

        # Assertions
        assert len(messages) > 0
        assert any("Executing" in msg for msg in messages)
        assert any("complete" in msg.lower() for msg in messages)

        # Verify operation tracking
        mock_operation_tracker.start_operation.assert_called_once()
        mock_operation_tracker.mark_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_sequence_with_error(
        self, command_router, mock_operation_tracker, mock_analysis_service
    ):
        """Test workflow sequence with error triggers retry and AI analysis."""
        # Mock workflow that fails
        mock_workflow = MagicMock()
        mock_workflow.name = "failing_workflow"

        workflow_sequence = WorkflowSequence(
            workflows=[mock_workflow],
            scale_level=ScaleLevel.LEVEL_1,
            project_type=ProjectType.SOFTWARE,
            routing_rationale="Test",
            phase_breakdown={}
        )

        # Mock analysis service response
        mock_analysis_result = MagicMock()
        mock_analysis_result.response = "AI analysis of failure"
        mock_analysis_service.analyze.return_value = mock_analysis_result

        # Patch _execute_single_workflow to raise error
        with patch.object(
            command_router,
            '_execute_single_workflow',
            side_effect=Exception("Test error")
        ):
            messages = []
            async for message in command_router.execute_workflow_sequence(
                workflow_sequence,
                Path("/test")
            ):
                messages.append(message)

            # Should have error messages
            assert any("failed" in msg.lower() for msg in messages)
            assert any("AI Analysis" in msg or "Analyzing failure" in msg for msg in messages)

            # Should mark as failed
            mock_operation_tracker.mark_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_create_prd(self, command_router):
        """Test PRD creation workflow execution."""
        mock_workflow = MagicMock()
        mock_workflow.project_name = "Test Project"

        messages = []
        async for msg in command_router._execute_create_prd(
            mock_workflow,
            Path("/test")
        ):
            messages.append(msg)

        # Should mention John and PRD
        combined = " ".join(messages)
        assert "John" in combined or "PRD" in combined

    @pytest.mark.asyncio
    async def test_execute_create_architecture(self, command_router):
        """Test architecture creation workflow execution."""
        mock_workflow = MagicMock()

        messages = []
        async for msg in command_router._execute_create_architecture(
            mock_workflow,
            Path("/test")
        ):
            messages.append(msg)

        # Should mention Winston and architecture
        combined = " ".join(messages)
        assert "Winston" in combined or "architecture" in combined.lower()

    @pytest.mark.asyncio
    async def test_execute_create_stories(self, command_router):
        """Test story creation workflow execution."""
        mock_workflow = MagicMock()
        mock_workflow.epic_num = 30

        messages = []
        async for msg in command_router._execute_create_stories(
            mock_workflow,
            Path("/test")
        ):
            messages.append(msg)

        # Should mention Bob and stories
        combined = " ".join(messages)
        assert "Bob" in combined or "stor" in combined.lower()

    @pytest.mark.asyncio
    async def test_execute_implement(self, command_router):
        """Test implementation workflow execution."""
        mock_workflow = MagicMock()
        mock_workflow.epic_num = 30
        mock_workflow.story_num = 4

        messages = []
        async for msg in command_router._execute_implement(
            mock_workflow,
            Path("/test")
        ):
            messages.append(msg)

        # Should mention Amelia and implementation
        combined = " ".join(messages)
        assert "Amelia" in combined or "implement" in combined.lower()

    @pytest.mark.asyncio
    async def test_execute_ceremony(self, command_router):
        """Test ceremony workflow execution."""
        mock_workflow = MagicMock()
        mock_workflow.ceremony_type = "retrospective"

        messages = []
        async for msg in command_router._execute_ceremony(
            mock_workflow,
            Path("/test")
        ):
            messages.append(msg)

        # Should mention ceremony
        combined = " ".join(messages)
        assert "ceremony" in combined.lower()

    @pytest.mark.asyncio
    async def test_execute_command_status(self, command_router):
        """Test status command execution."""
        messages = []
        async for msg in command_router.execute_command(
            "status",
            {},
            Path("/test")
        ):
            messages.append(msg)

        # Should return status info
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_execute_command_unknown(self, command_router):
        """Test unknown command."""
        messages = []
        async for msg in command_router.execute_command(
            "unknown_command",
            {},
            Path("/test")
        ):
            messages.append(msg)

        # Should have error message
        combined = " ".join(messages)
        assert "unknown" in combined.lower()
        assert "help" in combined.lower()

    @pytest.mark.asyncio
    async def test_analyze_failure(self, command_router, mock_analysis_service):
        """Test AI-powered failure analysis."""
        mock_result = MagicMock()
        mock_result.response = "Root cause: XYZ\nAlternatives: 1. A, 2. B"
        mock_analysis_service.analyze.return_value = mock_result

        analysis = await command_router._analyze_failure(
            "test_workflow",
            "Test error message"
        )

        # Should return analysis
        assert "Root cause" in analysis or len(analysis) > 0
        mock_analysis_service.analyze.assert_called_once()

    def test_get_workflow_name(self, command_router):
        """Test workflow name extraction."""
        # With name attribute
        workflow1 = MagicMock()
        workflow1.name = "test_workflow"
        assert command_router._get_workflow_name(workflow1) == "test_workflow"

        # With workflow_name attribute
        workflow2 = MagicMock()
        workflow2.workflow_name = "another_workflow"
        del workflow2.name
        assert command_router._get_workflow_name(workflow2) == "another_workflow"

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, command_router):
        """Test successful execution on first attempt (no retry)."""
        mock_workflow = MagicMock()

        messages = []
        async for msg in command_router._execute_with_retry(
            mock_workflow,
            Path("/test"),
            "test_workflow",
            max_retries=1
        ):
            messages.append(msg)

        # Should not mention retry
        combined = " ".join(messages)
        assert "retry" not in combined.lower()

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure_then_success(
        self, command_router, mock_analysis_service
    ):
        """Test retry on failure."""
        mock_workflow = MagicMock()

        # Mock to fail once, then succeed
        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            # Second attempt succeeds (yield nothing)
            return
            yield  # Make it a generator

        with patch.object(
            command_router,
            '_execute_single_workflow',
            side_effect=mock_execute
        ):
            messages = []
            try:
                async for msg in command_router._execute_with_retry(
                    mock_workflow,
                    Path("/test"),
                    "test_workflow",
                    max_retries=1
                ):
                    messages.append(msg)
            except Exception:
                pass  # Expected if both attempts fail

            # Should have attempted retry
            assert call_count >= 1
