"""Tests for OperationTracker.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from gao_dev.core.state.operation_tracker import OperationTracker, OperationRecord
from gao_dev.core.state.state_tracker import StateTracker


@pytest.fixture
def mock_state_tracker():
    """Create mock state tracker."""
    tracker = MagicMock(spec=StateTracker)
    return tracker


@pytest.fixture
def operation_tracker(mock_state_tracker):
    """Create OperationTracker instance."""
    return OperationTracker(mock_state_tracker)


class TestOperationTracker:
    """Test suite for OperationTracker."""

    def test_init(self, operation_tracker, mock_state_tracker):
        """Test initialization."""
        assert operation_tracker.state_tracker is mock_state_tracker

    def test_start_operation(self, operation_tracker, mock_state_tracker):
        """Test starting new operation."""
        op_id = operation_tracker.start_operation(
            operation_type="workflow_sequence",
            description="Test operation"
        )

        # Should return UUID string
        assert isinstance(op_id, str)
        assert len(op_id) > 0

        # Should have called StateTracker
        mock_state_tracker.track_workflow_execution.assert_called_once()

    def test_start_operation_with_metadata(
        self, operation_tracker, mock_state_tracker
    ):
        """Test starting operation with metadata."""
        metadata = {"key": "value"}

        op_id = operation_tracker.start_operation(
            operation_type="command",
            description="Test command",
            epic_num=30,
            story_num=4,
            metadata=metadata
        )

        assert len(op_id) > 0
        mock_state_tracker.track_workflow_execution.assert_called_once()

    def test_update_progress(self, operation_tracker):
        """Test updating operation progress."""
        op_id = "test-op-id"

        # Should not raise
        operation_tracker.update_progress(op_id, 50, "Step 1")
        operation_tracker.update_progress(op_id, 100, "Complete")

    def test_mark_complete(self, operation_tracker, mock_state_tracker):
        """Test marking operation as complete."""
        op_id = "test-op-id"
        artifacts = ["file1.py", "file2.py"]

        operation_tracker.mark_complete(op_id, artifacts=artifacts)

        # Should have updated workflow status
        mock_state_tracker.update_workflow_status.assert_called_once()
        call_args = mock_state_tracker.update_workflow_status.call_args
        assert call_args[1]["workflow_id"] == op_id
        assert call_args[1]["status"] == "completed"

    def test_mark_failed(self, operation_tracker, mock_state_tracker):
        """Test marking operation as failed."""
        op_id = "test-op-id"
        error_msg = "Operation failed due to X"

        operation_tracker.mark_failed(op_id, error_msg)

        # Should have updated workflow status
        mock_state_tracker.update_workflow_status.assert_called_once()
        call_args = mock_state_tracker.update_workflow_status.call_args
        assert call_args[1]["workflow_id"] == op_id
        assert call_args[1]["status"] == "failed"

    def test_mark_cancelled(self, operation_tracker, mock_state_tracker):
        """Test marking operation as cancelled."""
        op_id = "test-op-id"

        operation_tracker.mark_cancelled(op_id)

        # Should have updated workflow status
        mock_state_tracker.update_workflow_status.assert_called_once()
        call_args = mock_state_tracker.update_workflow_status.call_args
        assert call_args[1]["workflow_id"] == op_id
        assert call_args[1]["status"] == "cancelled"

    def test_get_interrupted_operations(self, operation_tracker):
        """Test retrieving interrupted operations."""
        # Should return empty list (not implemented yet)
        interrupted = operation_tracker.get_interrupted_operations()

        assert isinstance(interrupted, list)

    def test_get_operation(self, operation_tracker, mock_state_tracker):
        """Test retrieving single operation."""
        # Mock workflow execution
        mock_workflow = MagicMock()
        mock_workflow.workflow_id = "test-id"
        mock_workflow.workflow_name = "Test Workflow"
        mock_workflow.status = "completed"
        mock_workflow.started_at = "2025-01-01T00:00:00"
        mock_workflow.completed_at = "2025-01-01T01:00:00"

        mock_state_tracker.get_workflow_execution.return_value = mock_workflow

        # Get operation
        op = operation_tracker.get_operation("test-id")

        assert op is not None
        assert isinstance(op, OperationRecord)
        assert op.operation_id == "test-id"
        assert op.status == "completed"

    def test_get_operation_not_found(
        self, operation_tracker, mock_state_tracker
    ):
        """Test retrieving non-existent operation."""
        mock_state_tracker.get_workflow_execution.side_effect = Exception("Not found")

        op = operation_tracker.get_operation("nonexistent")

        assert op is None

    def test_get_recent_operations(self, operation_tracker):
        """Test retrieving recent operations."""
        # Should return empty list (not implemented yet)
        recent = operation_tracker.get_recent_operations(limit=10)

        assert isinstance(recent, list)

    def test_cleanup_old_operations(self, operation_tracker):
        """Test cleaning up old operations."""
        # Should return 0 (not implemented yet)
        count = operation_tracker.cleanup_old_operations(days=7)

        assert count == 0

    def test_start_operation_state_tracker_failure(
        self, operation_tracker, mock_state_tracker
    ):
        """Test start_operation handles StateTracker failure gracefully."""
        mock_state_tracker.track_workflow_execution.side_effect = Exception("DB error")

        # Should not raise
        op_id = operation_tracker.start_operation(
            operation_type="test",
            description="Test"
        )

        # Should still return ID
        assert len(op_id) > 0

    def test_mark_complete_state_tracker_failure(
        self, operation_tracker, mock_state_tracker
    ):
        """Test mark_complete handles StateTracker failure gracefully."""
        mock_state_tracker.update_workflow_status.side_effect = Exception("DB error")

        # Should not raise
        operation_tracker.mark_complete("test-id")

    def test_mark_failed_with_context(
        self, operation_tracker, mock_state_tracker
    ):
        """Test marking failed with additional context."""
        context = {"attempt": 2, "last_error": "Connection timeout"}

        operation_tracker.mark_failed(
            "test-id",
            "Failed after retries",
            context=context
        )

        # Should have called update with context
        mock_state_tracker.update_workflow_status.assert_called_once()
