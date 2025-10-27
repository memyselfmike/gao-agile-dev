"""Tests for workflow orchestrator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from gao_dev.sandbox.benchmark.orchestrator import (
    WorkflowOrchestrator,
    PhaseResult,
    WorkflowExecutionResult,
)
from gao_dev.sandbox.benchmark.config import WorkflowPhaseConfig


@pytest.fixture
def test_phases():
    """Create test workflow phases."""
    return [
        WorkflowPhaseConfig(phase_name="planning", timeout_seconds=300),
        WorkflowPhaseConfig(phase_name="implementation", timeout_seconds=600),
    ]


class TestPhaseResult:
    """Tests for PhaseResult."""

    def test_creation(self):
        """Test creating phase result."""
        result = PhaseResult(
            phase_name="test",
            status="success",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=10.0,
            command="test command",
        )
        assert result.phase_name == "test"
        assert result.status == "success"
        assert result.exit_code == 0


class TestWorkflowExecutionResult:
    """Tests for WorkflowExecutionResult."""

    def test_completed_phases_count(self):
        """Test counting completed phases."""
        result = WorkflowExecutionResult(
            phases=[
                PhaseResult("p1", "success", datetime.now(), datetime.now(), 1, "cmd"),
                PhaseResult("p2", "success", datetime.now(), datetime.now(), 1, "cmd"),
                PhaseResult("p3", "failed", datetime.now(), datetime.now(), 1, "cmd"),
            ]
        )
        assert result.completed_phases == 2

    def test_failed_phases_count(self):
        """Test counting failed phases."""
        result = WorkflowExecutionResult(
            phases=[
                PhaseResult("p1", "success", datetime.now(), datetime.now(), 1, "cmd"),
                PhaseResult("p2", "failed", datetime.now(), datetime.now(), 1, "cmd"),
                PhaseResult("p3", "failed", datetime.now(), datetime.now(), 1, "cmd"),
            ]
        )
        assert result.failed_phases == 2


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        orchestrator = WorkflowOrchestrator(Path("/tmp/test"))
        assert orchestrator.project_path == Path("/tmp/test")
        assert orchestrator.execution_mode == "subprocess"

    def test_dry_run_mode(self, test_phases):
        """Test dry-run execution mode."""
        orchestrator = WorkflowOrchestrator(Path("/tmp/test"), execution_mode="dry-run")
        result = orchestrator.execute_workflow(test_phases)

        assert result.success is True
        assert len(result.phases) == 2
        assert all("[DRY RUN]" in p.stdout for p in result.phases)

    @patch("subprocess.run")
    def test_subprocess_execution(self, mock_run, test_phases):
        """Test subprocess execution."""
        mock_result = Mock()
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        orchestrator = WorkflowOrchestrator(Path("/tmp/test"))
        result = orchestrator.execute_workflow(test_phases)

        assert result.success is True
        assert mock_run.call_count == 2

    def test_skip_phase_if_failed(self):
        """Test skipping phases when skip_if_failed is true."""
        phases = [
            WorkflowPhaseConfig(phase_name="p1", skip_if_failed=False),
            WorkflowPhaseConfig(phase_name="p2", skip_if_failed=True),
        ]

        orchestrator = WorkflowOrchestrator(Path("/tmp/test"), execution_mode="dry-run")

        # Manually create a result with one failed phase
        exec_result = WorkflowExecutionResult()
        exec_result.phases.append(
            PhaseResult("p1", "failed", datetime.now(), datetime.now(), 1, "cmd")
        )

        should_skip = orchestrator._should_skip_phase(phases[1], exec_result)
        assert should_skip is True

    def test_context_updates(self, test_phases):
        """Test that context is updated after each phase."""
        orchestrator = WorkflowOrchestrator(Path("/tmp/test"), execution_mode="dry-run")
        orchestrator.execute_workflow(test_phases)

        assert "planning" in orchestrator.context
        assert "implementation" in orchestrator.context
        assert orchestrator.context["planning"]["status"] == "success"
