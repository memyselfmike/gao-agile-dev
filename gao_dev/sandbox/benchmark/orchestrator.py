"""Workflow orchestration for benchmark execution."""

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
    """Result of executing a single workflow phase."""

    phase_name: str
    status: str  # "success", "failed", "skipped", "timeout"
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    artifacts: Dict[str, Any] = field(default_factory=dict)
    quality_gates: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "phase_name": self.phase_name,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "artifacts": self.artifacts,
            "quality_gates": self.quality_gates,
        }


@dataclass
class WorkflowExecutionResult:
    """Result of executing complete workflow."""

    phases: List[PhaseResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """Check if workflow succeeded."""
        if not self.phases:
            return False
        return all(p.status in ("success", "skipped") for p in self.phases)

    @property
    def completed_phases(self) -> int:
        """Count of successfully completed phases."""
        return sum(1 for p in self.phases if p.status == "success")

    @property
    def failed_phases(self) -> int:
        """Count of failed phases."""
        return sum(1 for p in self.phases if p.status == "failed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "phases": [p.to_dict() for p in self.phases],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": self.total_duration_seconds,
            "success": self.success,
            "completed_phases": self.completed_phases,
            "failed_phases": self.failed_phases,
        }


class WorkflowOrchestrator:
    """
    Orchestrates multi-phase workflow execution.

    Manages phase dependencies, execution modes (subprocess/API/dry-run),
    artifact validation, and quality gates.
    """

    def __init__(
        self,
        project_path: Path,
        execution_mode: str = "subprocess",
    ):
        """
        Initialize orchestrator.

        Args:
            project_path: Path to project directory
            execution_mode: How to execute phases (subprocess, api, dry-run)
        """
        self.project_path = Path(project_path)
        self.execution_mode = execution_mode
        self.context: Dict[str, Any] = {}
        self.logger = logger.bind(
            component="WorkflowOrchestrator",
            project_path=str(project_path),
            execution_mode=execution_mode,
        )

    def execute_workflow(
        self,
        phases: List[WorkflowPhaseConfig],
        timeout_seconds: Optional[int] = None,
    ) -> WorkflowExecutionResult:
        """
        Execute workflow phases sequentially.

        Args:
            phases: List of workflow phase configurations
            timeout_seconds: Optional overall timeout for workflow

        Returns:
            WorkflowExecutionResult with all phase results
        """
        result = WorkflowExecutionResult(start_time=datetime.now())

        self.logger.info(
            "workflow_execution_started",
            phase_count=len(phases),
            timeout_seconds=timeout_seconds,
        )

        for phase_config in phases:
            # Check if phase should be skipped
            if self._should_skip_phase(phase_config, result):
                self.logger.info("phase_skipped", phase_name=phase_config.phase_name)
                phase_result = self._create_skipped_phase_result(phase_config)
                result.phases.append(phase_result)
                self._update_context(phase_config.phase_name, phase_result)
                continue

            # Execute phase
            phase_result = self._execute_phase(phase_config)
            result.phases.append(phase_result)
            self._update_context(phase_config.phase_name, phase_result)

            # Check if we should stop on failure
            if phase_result.status == "failed" and not phase_config.continue_on_failure:
                self.logger.warning(
                    "workflow_stopped_on_failure",
                    phase_name=phase_config.phase_name,
                )
                break

        result.end_time = datetime.now()
        result.total_duration_seconds = (
            result.end_time - result.start_time
        ).total_seconds()

        self.logger.info(
            "workflow_execution_completed",
            success=result.success,
            completed_phases=result.completed_phases,
            failed_phases=result.failed_phases,
            total_duration=result.total_duration_seconds,
        )

        return result

    def _execute_phase(self, phase_config: WorkflowPhaseConfig) -> PhaseResult:
        """Execute a single workflow phase."""
        start_time = datetime.now()
        command = phase_config.command or f"echo 'Phase: {phase_config.phase_name}'"

        self.logger.info(
            "phase_execution_started",
            phase_name=phase_config.phase_name,
            command=command,
        )

        if self.execution_mode == "dry-run":
            # Dry-run mode: simulate execution
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            return PhaseResult(
                phase_name=phase_config.phase_name,
                status="success",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                command=command,
                stdout=f"[DRY RUN] Would execute: {command}",
                stderr="",
                exit_code=0,
            )

        elif self.execution_mode == "subprocess":
            # Subprocess mode: execute command
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=phase_config.timeout_seconds,
                )

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                status = "success" if result.returncode == 0 else "failed"

                return PhaseResult(
                    phase_name=phase_config.phase_name,
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                )

            except subprocess.TimeoutExpired:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                return PhaseResult(
                    phase_name=phase_config.phase_name,
                    status="timeout",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    command=command,
                    stdout="",
                    stderr=f"Phase timed out after {phase_config.timeout_seconds}s",
                    exit_code=-1,
                )

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                return PhaseResult(
                    phase_name=phase_config.phase_name,
                    status="failed",
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=duration,
                    command=command,
                    stdout="",
                    stderr=f"Error executing phase: {str(e)}",
                    exit_code=-1,
                )

        else:
            # Unknown execution mode
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            return PhaseResult(
                phase_name=phase_config.phase_name,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                command=command,
                stdout="",
                stderr=f"Unknown execution mode: {self.execution_mode}",
                exit_code=-1,
            )

    def _should_skip_phase(
        self,
        phase_config: WorkflowPhaseConfig,
        result: WorkflowExecutionResult,
    ) -> bool:
        """Check if phase should be skipped based on previous failures."""
        if not phase_config.skip_if_failed:
            return False

        # Check if any previous phase failed
        for phase_result in result.phases:
            if phase_result.status == "failed":
                return True

        return False

    def _create_skipped_phase_result(
        self, phase_config: WorkflowPhaseConfig
    ) -> PhaseResult:
        """Create a result for a skipped phase."""
        now = datetime.now()
        return PhaseResult(
            phase_name=phase_config.phase_name,
            status="skipped",
            start_time=now,
            end_time=now,
            duration_seconds=0.0,
            command=phase_config.command or "",
            stdout="Phase skipped due to previous failure",
            stderr="",
            exit_code=0,
        )

    def _update_context(self, phase_name: str, phase_result: PhaseResult) -> None:
        """Update orchestrator context with phase result."""
        self.context[phase_name] = {
            "status": phase_result.status,
            "duration_seconds": phase_result.duration_seconds,
            "exit_code": phase_result.exit_code,
            "artifacts": phase_result.artifacts,
            "quality_gates": phase_result.quality_gates,
        }
