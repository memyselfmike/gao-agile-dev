"""Workflow orchestration for benchmark runs."""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from .config import WorkflowPhaseConfig


logger = structlog.get_logger()


@dataclass
class PhaseResult:
    """Result of executing a single phase."""

    phase_name: str
    status: str  # "success", "failed", "skipped", "timeout"
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    artifacts_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecutionResult:
    """Result of complete workflow execution."""

    phases: List[PhaseResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    success: bool = False

    @property
    def completed_phases(self) -> int:
        """Count of successfully completed phases."""
        return sum(1 for p in self.phases if p.status == "success")

    @property
    def failed_phases(self) -> int:
        """Count of failed phases."""
        return sum(1 for p in self.phases if p.status == "failed")


class WorkflowOrchestrator:
    """
    Orchestrates GAO-Dev workflow execution.

    Executes workflow phases, manages context, validates artifacts,
    and enforces quality gates.
    """

    def __init__(self, project_path: Path, execution_mode: str = "subprocess"):
        """
        Initialize workflow orchestrator.

        Args:
            project_path: Path to sandbox project
            execution_mode: How to execute commands ("subprocess", "api", "dry-run")
        """
        self.project_path = project_path
        self.execution_mode = execution_mode
        self.logger = logger.bind(component="WorkflowOrchestrator")
        self.context: Dict[str, Any] = {}

    def execute_workflow(
        self, phases: List[WorkflowPhaseConfig], timeout_seconds: Optional[int] = None
    ) -> WorkflowExecutionResult:
        """
        Execute complete workflow.

        Args:
            phases: List of workflow phases to execute
            timeout_seconds: Overall timeout for workflow

        Returns:
            WorkflowExecutionResult with all phase results
        """
        result = WorkflowExecutionResult()
        start_time = datetime.now()

        self.logger.info("workflow_execution_started", num_phases=len(phases))

        for phase in phases:
            # Check if we should skip this phase
            if self._should_skip_phase(phase, result):
                self.logger.info("phase_skipped", phase=phase.phase_name)
                continue

            # Execute the phase
            phase_result = self._execute_phase(phase)
            result.phases.append(phase_result)

            # Update context with results
            self._update_context(phase_result)

            # Check if we exceeded overall timeout
            if timeout_seconds:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    self.logger.warning("workflow_timeout_exceeded", elapsed=elapsed)
                    break

        # Calculate results
        end_time = datetime.now()
        result.total_duration_seconds = (end_time - start_time).total_seconds()
        result.success = result.failed_phases == 0

        self.logger.info(
            "workflow_execution_completed",
            success=result.success,
            completed=result.completed_phases,
            failed=result.failed_phases,
        )

        return result

    def _should_skip_phase(
        self, phase: WorkflowPhaseConfig, result: WorkflowExecutionResult
    ) -> bool:
        """Check if phase should be skipped based on skip_if_failed."""
        if not phase.skip_if_failed:
            return False
        return result.failed_phases > 0

    def _execute_phase(self, phase: WorkflowPhaseConfig) -> PhaseResult:
        """
        Execute a single workflow phase.

        Args:
            phase: Phase configuration

        Returns:
            PhaseResult with execution details
        """
        self.logger.info("phase_execution_started", phase=phase.phase_name)
        start_time = datetime.now()

        # Build command based on phase
        command = self._build_command(phase)

        # Execute command
        if self.execution_mode == "dry-run":
            stdout, stderr, exit_code = self._dry_run_command(command)
        elif self.execution_mode == "api":
            stdout, stderr, exit_code = self._execute_via_api(phase)
        else:  # subprocess mode (default)
            stdout, stderr, exit_code = self._execute_via_subprocess(
                command, phase.timeout_seconds
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Create result
        status = "success" if exit_code == 0 else "failed"
        result = PhaseResult(
            phase_name=phase.phase_name,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

        # Validate expected artifacts
        self._validate_artifacts(phase, result)

        # Check quality gates
        self._check_quality_gates(phase, result)

        self.logger.info(
            "phase_execution_completed",
            phase=phase.phase_name,
            status=status,
            duration=duration,
        )

        return result

    def _build_command(self, phase: WorkflowPhaseConfig) -> str:
        """Build gao-dev command for phase."""
        # Simplified command - actual implementation would be more sophisticated
        return f"gao-dev execute {phase.phase_name}"

    def _execute_via_subprocess(
        self, command: str, timeout: int
    ) -> tuple[str, str, int]:
        """Execute command via subprocess."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 124
        except Exception as e:
            return "", str(e), 1

    def _execute_via_api(self, phase: WorkflowPhaseConfig) -> tuple[str, str, int]:
        """Execute phase via GAO-Dev API (if available)."""
        # Placeholder for API mode
        # In Story 4.8, this would use the standalone execution mode
        return "API mode not yet implemented", "", 0

    def _dry_run_command(self, command: str) -> tuple[str, str, int]:
        """Simulate command execution for testing."""
        return f"[DRY RUN] Would execute: {command}", "", 0

    def _validate_artifacts(
        self, phase: WorkflowPhaseConfig, result: PhaseResult
    ) -> None:
        """Validate that expected artifacts were created."""
        for artifact in phase.expected_artifacts:
            artifact_path = self.project_path / artifact
            if artifact_path.exists():
                result.artifacts_created.append(artifact)
            else:
                result.errors.append(f"Expected artifact not found: {artifact}")
                result.status = "failed"

    def _check_quality_gates(
        self, phase: WorkflowPhaseConfig, result: PhaseResult
    ) -> None:
        """Check quality gates for phase."""
        # Placeholder for quality gate checks
        # Would validate things like test coverage, linting, etc.
        pass

    def _update_context(self, phase_result: PhaseResult) -> None:
        """Update execution context with phase results."""
        self.context[phase_result.phase_name] = {
            "status": phase_result.status,
            "artifacts": phase_result.artifacts_created,
            "duration": phase_result.duration_seconds,
        }
