"""Workflow orchestration for benchmark execution."""

import subprocess
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog

from .config import WorkflowPhaseConfig
from ...orchestrator import GAODevOrchestrator
from ..artifact_parser import ArtifactParser
from ..git_commit_manager import GitCommitManager
from ..artifact_verifier import ArtifactVerifier


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
        api_key: Optional[str] = None,
        metrics_aggregator: Optional[Any] = None,
        run_id: Optional[str] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            project_path: Path to project directory
            execution_mode: How to execute phases (subprocess, agent, dry-run)
            api_key: Anthropic API key (required for agent mode - currently unused)
            metrics_aggregator: MetricsAggregator for comprehensive logging (optional)
            run_id: Benchmark run ID for git commit tracking
        """
        self.project_path = Path(project_path)
        self.execution_mode = execution_mode
        self.api_key = api_key
        self.metrics_aggregator = metrics_aggregator
        self.run_id = run_id or "benchmark"
        self.context: Dict[str, Any] = {}
        self.logger = logger.bind(
            component="WorkflowOrchestrator",
            project_path=str(project_path),
            execution_mode=execution_mode,
        )

        # Initialize GAODevOrchestrator, ArtifactParser, GitCommitManager, and ArtifactVerifier for agent mode
        self.gao_orchestrator = None
        self.artifact_parser = None
        self.git_commit_manager = None
        self.artifact_verifier = None
        if execution_mode == "agent":
            self.gao_orchestrator = GAODevOrchestrator(project_root=self.project_path)
            self.artifact_parser = ArtifactParser(project_root=self.project_path)
            self.git_commit_manager = GitCommitManager(
                project_root=self.project_path,
                run_id=self.run_id,
            )
            self.artifact_verifier = ArtifactVerifier(project_root=self.project_path)

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

        elif self.execution_mode == "agent":
            # Agent mode: spawn GAO-Dev agent via Task tool
            # This mode is used when running in Claude Code with Cloud Max
            return self._execute_phase_with_agent(phase_config, start_time)

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

    def _execute_phase_with_agent(
        self, phase_config: WorkflowPhaseConfig, start_time: datetime
    ) -> PhaseResult:
        """
        Execute phase using GAODevOrchestrator.

        Maps the phase configuration to the appropriate GAODevOrchestrator method
        and executes it to create artifacts autonomously.

        Args:
            phase_config: Configuration for the phase to execute
            start_time: When phase execution started

        Returns:
            PhaseResult with orchestrator execution status
        """
        # Extract agent name from phase config
        agent_name = phase_config.agent or phase_config.quality_gates.get("agent", "Unknown")

        self.logger.info(
            "executing_phase_with_gao_orchestrator",
            phase=phase_config.phase_name,
            agent=agent_name,
        )

        if not self.gao_orchestrator:
            # Fallback if orchestrator not initialized
            self.logger.error("gao_orchestrator_not_initialized")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            return PhaseResult(
                phase_name=phase_config.phase_name,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                command=phase_config.phase_name,
                stdout="",
                stderr="GAODevOrchestrator not initialized",
                exit_code=1,
            )

        try:
            # Map phase to orchestrator method and execute
            output = self._execute_orchestrator_method(
                phase_name=phase_config.phase_name,
                agent_name=agent_name,
                timeout_seconds=phase_config.timeout_seconds,
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Parse output for artifacts
            artifacts_created = []
            commit_sha = None
            if self.artifact_parser:
                parsed_artifacts = self.artifact_parser.parse_output(
                    output=output,
                    phase=phase_config.phase_name,
                )

                # Write artifacts to disk
                write_results = self.artifact_parser.write_artifacts(parsed_artifacts)

                # Track which artifacts were created
                artifacts_created = [
                    path for path, success in write_results.items() if success
                ]

                self.logger.info(
                    "artifacts_created",
                    phase=phase_config.phase_name,
                    artifact_count=len(artifacts_created),
                    artifacts=artifacts_created,
                )

                # Create atomic commit for artifacts
                if self.git_commit_manager and artifacts_created:
                    commit_sha = self.git_commit_manager.commit_artifacts(
                        phase=phase_config.phase_name,
                        artifact_paths=artifacts_created,
                        agent_name=agent_name,
                    )

                    if commit_sha:
                        self.logger.info(
                            "artifacts_committed",
                            phase=phase_config.phase_name,
                            commit_sha=commit_sha[:8],
                        )

                # Verify artifacts were created correctly
                verification_result = None
                if self.artifact_verifier and artifacts_created:
                    verification_result = self.artifact_verifier.verify_artifacts(
                        artifact_paths=artifacts_created,
                        phase=phase_config.phase_name,
                    )

                    if not verification_result.success:
                        self.logger.warning(
                            "artifact_verification_warnings",
                            phase=phase_config.phase_name,
                            expected=verification_result.expected_count,
                            found=verification_result.found_count,
                            valid=verification_result.valid_count,
                        )

            self.logger.info(
                "phase_execution_completed",
                phase=phase_config.phase_name,
                agent=agent_name,
                duration_seconds=duration,
                output_length=len(output),
                artifacts_created=len(artifacts_created),
            )

            # Record metrics if aggregator available
            if self.metrics_aggregator:
                self.metrics_aggregator.record_phase_result(
                    phase_name=phase_config.phase_name,
                    agent_name=agent_name,
                    success=True,
                    duration_seconds=duration,
                    details={
                        "output_length": len(output),
                        "orchestration_mode": "gao-dev",
                        "artifacts_created": artifacts_created,
                        "artifact_count": len(artifacts_created),
                        "commit_sha": commit_sha,
                        "git_committed": commit_sha is not None,
                    },
                )

            return PhaseResult(
                phase_name=phase_config.phase_name,
                status="success",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                command=phase_config.phase_name,
                stdout=output,
                stderr="",
                exit_code=0,
                artifacts={
                    "agent": agent_name,
                    "orchestration_mode": "gao-dev",
                    "files_created": artifacts_created,
                    "commit_sha": commit_sha,
                },
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(
                "orchestrator_execution_exception",
                phase=phase_config.phase_name,
                agent=agent_name,
                error=str(e),
            )

            return PhaseResult(
                phase_name=phase_config.phase_name,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                command=phase_config.phase_name,
                stdout="",
                stderr=f"Orchestrator execution error: {str(e)}",
                exit_code=1,
            )

    def _execute_orchestrator_method(
        self, phase_name: str, agent_name: str, timeout_seconds: int
    ) -> str:
        """
        Map phase/agent to appropriate GAODevOrchestrator method and execute.

        Args:
            phase_name: Name of the phase being executed
            agent_name: Name of the agent (John, Winston, Bob, Amelia, etc.)
            timeout_seconds: Timeout for execution

        Returns:
            Collected output from orchestrator

        Raises:
            ValueError: If phase/agent cannot be mapped to a method
        """
        # Determine project name from context or path
        project_name = self.context.get("project_name", self.project_path.name)

        # Map phase_name or agent_name to orchestrator method
        phase_lower = phase_name.lower()
        agent_lower = agent_name.lower()

        async def run_orchestrator():
            """Run the appropriate orchestrator method."""
            output_parts = []

            # Map to orchestrator methods based on phase name or agent
            if "product requirements" in phase_lower or agent_lower == "john":
                async for message in self.gao_orchestrator.create_prd(project_name):
                    output_parts.append(message)

            elif "system architecture" in phase_lower or "architecture" in phase_lower or agent_lower == "winston":
                async for message in self.gao_orchestrator.create_architecture(project_name):
                    output_parts.append(message)

            elif "story creation" in phase_lower or agent_lower == "bob":
                # For now, create story 1.1
                # TODO: Make this configurable from phase config
                async for message in self.gao_orchestrator.create_story(epic=1, story=1):
                    output_parts.append(message)

            elif "implementation" in phase_lower or agent_lower == "amelia":
                # For now, implement story 1.1
                # TODO: Make this configurable from phase config
                async for message in self.gao_orchestrator.implement_story(epic=1, story=1):
                    output_parts.append(message)

            else:
                raise ValueError(
                    f"Cannot map phase '{phase_name}' with agent '{agent_name}' to orchestrator method"
                )

            return "".join(output_parts)

        # Run the async orchestrator method synchronously
        return asyncio.run(run_orchestrator())

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
