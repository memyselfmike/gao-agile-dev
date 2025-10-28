"""Core benchmark runner implementation."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog

from .config import BenchmarkConfig
from .validator import ConfigValidator
from ...sandbox.manager import SandboxManager
from ...sandbox.metrics.collector import MetricsCollector
from ...sandbox.metrics.models import BenchmarkMetrics


logger = structlog.get_logger()


class BenchmarkStatus(Enum):
    """Benchmark run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    run_id: str
    config: BenchmarkConfig
    status: BenchmarkStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    metrics: Optional[BenchmarkMetrics] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        """Generate a quick summary of the run."""
        lines = [
            f"Benchmark Run: {self.run_id}",
            f"Status: {self.status.value}",
            f"Duration: {self.duration_seconds:.2f}s",
        ]
        if self.metrics:
            lines.append(
                f"Total Time: {self.metrics.performance.total_time_seconds:.2f}s"
            )
            lines.append(
                f"Manual Interventions: {self.metrics.autonomy.manual_interventions_count}"
            )
            lines.append(
                f"Test Coverage: {self.metrics.quality.code_coverage_percentage:.1f}%"
            )
        if self.errors:
            lines.append(f"Errors: {len(self.errors)}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        from dataclasses import asdict

        data = asdict(self)
        # Convert enums and datetime to strings
        data["status"] = self.status.value
        data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        # Convert config to dict
        data["config"] = self.config.to_dict()
        return data


class BenchmarkRunner:
    """
    Core benchmark runner.

    Orchestrates the complete benchmark execution including:
    - Configuration validation
    - Sandbox initialization
    - Boilerplate setup
    - Workflow execution
    - Metrics collection
    - Cleanup
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        sandbox_manager: SandboxManager,
        metrics_collector: MetricsCollector,
        sandbox_root: Path,
        api_key: Optional[str] = None,
        project_name: Optional[str] = None,
    ):
        """
        Initialize benchmark runner.

        Args:
            config: Benchmark configuration
            sandbox_manager: Sandbox project manager
            metrics_collector: Metrics collection service
            sandbox_root: Root directory for sandbox projects
            api_key: Anthropic API key for agent spawning (if None, uses env var)
            project_name: Pre-created project name (if None, creates new one)
        """
        self.config = config
        self.sandbox_manager = sandbox_manager
        self.metrics_collector = metrics_collector
        self.sandbox_root = sandbox_root
        self.api_key = api_key
        self.project_name = project_name
        self.validator = ConfigValidator()
        self.logger = logger.bind(component="BenchmarkRunner")

    def run(self) -> BenchmarkResult:
        """
        Execute the complete benchmark.

        Returns:
            BenchmarkResult with all metrics and status

        Raises:
            ValueError: If configuration is invalid
        """
        # Generate unique run ID
        run_id = self._generate_run_id()
        self.logger.info(
            "benchmark_run_started", run_id=run_id, config=self.config.name
        )

        # Initialize result
        result = BenchmarkResult(
            run_id=run_id,
            config=self.config,
            status=BenchmarkStatus.PENDING,
            start_time=datetime.now(),
        )

        try:
            # Validate configuration
            self._validate_configuration(result)

            # Initialize sandbox project
            result.status = BenchmarkStatus.RUNNING
            project = self._initialize_sandbox(result)

            # Setup boilerplate
            self._setup_boilerplate(project, result)

            # Start metrics collection
            self.metrics_collector.start_collection(project.name, self.config.name)

            # Execute workflow (placeholder - will be implemented in Story 4.4)
            self._execute_workflow(project, result)

            # Stop metrics collection
            metrics = self.metrics_collector.stop_collection()
            result.metrics = metrics

            # Mark as completed
            result.status = BenchmarkStatus.COMPLETED
            self.logger.info("benchmark_run_completed", run_id=run_id)

        except Exception as e:
            result.status = BenchmarkStatus.FAILED
            result.errors.append(str(e))
            self.logger.error("benchmark_run_failed", run_id=run_id, error=str(e))

        finally:
            # Always set end time and duration
            result.end_time = datetime.now()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

            # Cleanup
            self._cleanup(result)

        return result

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{self.config.name}-{timestamp}-{short_uuid}"

    def _validate_configuration(self, result: BenchmarkResult) -> None:
        """
        Validate benchmark configuration.

        Args:
            result: Benchmark result to update with validation errors

        Raises:
            ValueError: If configuration is invalid
        """
        validation_result = self.validator.validate_config(self.config)

        if not validation_result.is_valid:
            error_msg = str(validation_result)
            result.errors.append(error_msg)
            raise ValueError(f"Invalid benchmark configuration:\n{error_msg}")

        # Add warnings to result
        for warning in validation_result.warnings:
            result.warnings.append(str(warning))

        self.logger.info(
            "configuration_validated", warnings=len(validation_result.warnings)
        )

    def _initialize_sandbox(self, result: BenchmarkResult) -> Any:
        """
        Initialize sandbox project with git repository.

        If project_name was provided in __init__, uses the existing project.
        Otherwise, creates a new project.

        Args:
            result: Benchmark result to update

        Returns:
            Initialized sandbox project

        Raises:
            Exception: If initialization fails
        """
        # Use pre-created project if provided, otherwise create new one
        if self.project_name:
            project_name = self.project_name
            self.logger.info("using_existing_sandbox", project_name=project_name)
            project = self.sandbox_manager.get_project(project_name)
        else:
            project_name = self.config.project_name or self.config.name
            self.logger.info("creating_new_sandbox", project_name=project_name)
            project = self.sandbox_manager.create_project(
                name=project_name,
                boilerplate_url=self.config.boilerplate_url,
                tags=[f"benchmark:{self.config.name}", f"run:{result.run_id}"],
                description=f"Benchmark: {self.config.description}",
            )

        # Initialize git repository for incremental story-based workflow
        project_path = self.sandbox_root / "projects" / project.name
        self._initialize_git_repository(project_path, result)

        self.logger.info("sandbox_initialized", project_name=project.name)
        return project

    def _setup_boilerplate(self, project: Any, result: BenchmarkResult) -> None:
        """
        Setup boilerplate in sandbox project.

        Args:
            project: Sandbox project
            result: Benchmark result to update

        Raises:
            Exception: If boilerplate setup fails
        """
        from ...sandbox.git_cloner import GitCloner

        if self.config.boilerplate_url:
            self.logger.info("cloning_boilerplate", url=self.config.boilerplate_url)
            cloner = GitCloner()
            cloner.clone_repository(
                repo_url=self.config.boilerplate_url, destination=project.project_path
            )
        elif self.config.boilerplate_path:
            self.logger.info("copying_boilerplate", path=self.config.boilerplate_path)
            # Copy local template
            import shutil

            shutil.copytree(
                self.config.boilerplate_path,
                project.project_path,
                dirs_exist_ok=True,
            )

        self.logger.info("boilerplate_setup_complete")

    def _execute_workflow(self, project: Any, result: BenchmarkResult) -> None:
        """
        Execute workflow - either phase-based or story-based.

        Detects mode from config and delegates to appropriate orchestrator:
        - Phase-based: Uses WorkflowOrchestrator (legacy waterfall mode)
        - Story-based: Uses StoryOrchestrator (incremental agile mode)

        Args:
            project: Sandbox project
            result: Benchmark result to update
        """
        self.logger.info("workflow_execution_started", run_id=result.run_id)

        # Check if config is story-based
        if self.config.is_story_based():
            self._execute_story_based_workflow(project, result)
        else:
            self._execute_phase_based_workflow(project, result)

    def _execute_story_based_workflow(
        self, project: Any, result: BenchmarkResult
    ) -> None:
        """
        Execute story-based incremental workflow.

        Uses StoryOrchestrator to iterate through epics and stories,
        with each story following: create → implement → test → commit.

        Args:
            project: Sandbox project
            result: Benchmark result to update
        """
        from .story_orchestrator import StoryOrchestrator
        from .progress import ProgressTracker, ConsoleProgressObserver
        from .metrics_aggregator import MetricsAggregator
        from ...core.git_manager import GitManager

        self.logger.info(
            "story_based_workflow_started",
            run_id=result.run_id,
            total_epics=len(self.config.epics),
            total_stories=self.config.total_stories(),
        )

        # Get project path
        project_path = self.sandbox_root / "projects" / project.name

        # Initialize git manager for commits
        git_manager = GitManager(project_path)

        # Initialize metrics aggregator
        output_dir = self.sandbox_root / "metrics"
        metrics_aggregator = MetricsAggregator(
            run_id=result.run_id,
            benchmark_name=self.config.name,
            output_dir=output_dir,
        )

        # Initialize progress tracker
        progress_tracker = ProgressTracker()
        progress_tracker.add_observer(ConsoleProgressObserver())

        # Log benchmark start
        metrics_aggregator.log_event(
            "story_based_benchmark_started",
            f"Starting story-based benchmark: {self.config.name}",
            {
                "epics": len(self.config.epics),
                "stories": total_stories,
                "project_path": str(project_path),
                "story_points": self.config.total_story_points(),
            },
        )

        # Create story orchestrator
        orchestrator = StoryOrchestrator(
            project_path=project_path,
            api_key=self.api_key,
            git_manager=git_manager,
            metrics_aggregator=metrics_aggregator,
        )

        try:
            # Execute all epics
            total_stories = self.config.total_stories()
            progress_tracker.benchmark_started(self.config.name, total_stories)
            epic_results = orchestrator.execute_epics(
                epics=self.config.epics,
                timeout_seconds=self.config.timeout_seconds,
            )
            progress_tracker.benchmark_completed(True)

            # Store results
            result.metadata["story_based_workflow"] = True
            result.metadata["epic_results"] = [
                epic_result.to_dict() for epic_result in epic_results
            ]
            result.metadata["total_epics"] = len(epic_results)
            result.metadata["completed_stories"] = sum(
                epic.completed_stories for epic in epic_results
            )
            result.metadata["failed_stories"] = sum(
                epic.failed_stories for epic in epic_results
            )
            result.metadata["total_stories"] = total_stories

            # Check if all epics succeeded
            all_succeeded = all(epic.success for epic in epic_results)
            if not all_succeeded:
                error_msg = "Some stories failed in story-based workflow"
                result.errors.append(error_msg)
                self.logger.error("story_based_workflow_partial_failure")

            self.logger.info(
                "story_based_workflow_completed",
                total_epics=len(epic_results),
                completed_stories=result.metadata["completed_stories"],
                failed_stories=result.metadata["failed_stories"],
            )

            # Generate metrics report
            metrics_report = metrics_aggregator.generate_report()
            result.metadata["metrics_report"] = metrics_report
            metrics_aggregator.print_summary()

        except Exception as e:
            error_msg = f"Story-based workflow error: {str(e)}"
            result.errors.append(error_msg)
            progress_tracker.benchmark_completed(False)
            self.logger.error("story_based_workflow_exception", error=str(e))

            # Log error to metrics
            metrics_aggregator.log_event(
                "story_based_workflow_failed",
                f"Workflow failed: {str(e)}",
                {"error": str(e)},
            )

    def _execute_phase_based_workflow(
        self, project: Any, result: BenchmarkResult
    ) -> None:
        """
        Execute phase-based workflow (legacy waterfall mode).

        Uses WorkflowOrchestrator to execute workflow phases sequentially.

        Args:
            project: Sandbox project
            result: Benchmark result to update
        """
        from .orchestrator import WorkflowOrchestrator
        from .progress import ProgressTracker, ConsoleProgressObserver
        from .metrics_aggregator import MetricsAggregator

        self.logger.info("phase_based_workflow_started", run_id=result.run_id)

        # Create workflow phases from benchmark config
        workflow_phases = self._create_workflow_phases()

        if not workflow_phases:
            self.logger.warning("no_workflow_phases_configured")
            result.warnings.append("No workflow phases configured in benchmark")
            return

        # Initialize progress tracking
        progress_tracker = ProgressTracker()
        progress_tracker.add_observer(ConsoleProgressObserver())

        # Get project path
        project_path = self.sandbox_root / "projects" / project.name

        # Initialize metrics aggregator for comprehensive logging
        output_dir = self.sandbox_root / "metrics"
        metrics_aggregator = MetricsAggregator(
            run_id=result.run_id,
            benchmark_name=self.config.name,
            output_dir=output_dir,
        )

        # Log benchmark start
        metrics_aggregator.log_event(
            "benchmark_started",
            f"Starting benchmark: {self.config.name}",
            {
                "phases": len(workflow_phases),
                "project_path": str(project_path),
                "timeout_seconds": self.config.timeout_seconds,
            },
        )

        # Create orchestrator (use 'agent' mode for autonomous execution)
        orchestrator = WorkflowOrchestrator(
            project_path=project_path,
            execution_mode="agent",  # Use agent mode for autonomous execution
            api_key=self.api_key,  # Pass API key for agent spawning
            metrics_aggregator=metrics_aggregator,  # Pass metrics aggregator
        )

        try:
            # Execute workflow
            progress_tracker.benchmark_started(self.config.name, len(workflow_phases))
            workflow_result = orchestrator.execute_workflow(
                phases=workflow_phases,
                timeout_seconds=self.config.timeout_seconds,
            )
            progress_tracker.benchmark_completed(True)

            # Store workflow results in benchmark result
            result.metadata["workflow_result"] = workflow_result.to_dict()
            result.metadata["completed_phases"] = workflow_result.completed_phases
            result.metadata["failed_phases"] = workflow_result.failed_phases

            # Check if workflow succeeded
            if not workflow_result.success:
                error_msg = (
                    f"Workflow failed: {workflow_result.failed_phases} phase(s) failed"
                )
                result.errors.append(error_msg)
                self.logger.error("workflow_execution_failed", error=error_msg)

            self.logger.info(
                "workflow_execution_completed",
                success=workflow_result.success,
                completed=workflow_result.completed_phases,
                failed=workflow_result.failed_phases,
            )

            # Generate comprehensive metrics report
            metrics_report = metrics_aggregator.generate_report()
            result.metadata["metrics_report"] = metrics_report

            # Print summary to console
            metrics_aggregator.print_summary()

        except Exception as e:
            error_msg = f"Workflow execution error: {str(e)}"
            result.errors.append(error_msg)
            progress_tracker.benchmark_completed(False)
            self.logger.error("workflow_execution_exception", error=str(e))

            # Log error to metrics
            metrics_aggregator.log_event(
                "benchmark_failed",
                f"Benchmark failed with error: {str(e)}",
                {"error": str(e)},
            )

    def _create_workflow_phases(self) -> List:
        """
        Create workflow phase configurations from benchmark config.

        Returns:
            List[WorkflowPhaseConfig]: List of workflow phases to execute
        """
        from .config import WorkflowPhaseConfig

        phases = []

        # Check if using new-style config with workflow_phases
        if hasattr(self.config, 'workflow_phases') and self.config.workflow_phases:
            return self.config.workflow_phases

        # Handle simple BenchmarkConfig from sandbox/benchmark.py
        # This has a 'phases' attribute extracted from YAML
        if hasattr(self.config, 'phases') and self.config.phases:
            for phase_def in self.config.phases:
                # Extract phase information
                phase_name = phase_def.get('name', 'Unknown')
                agent_name = phase_def.get('agent', 'Amelia')
                duration_minutes = phase_def.get('expected_duration_minutes', 60)

                # Create prompt for the agent
                # The agent will receive the initial prompt from the benchmark
                # CRITICAL: Agents must complete ALL work, not just foundation
                prompt = f"""You are {agent_name}, working on phase: {phase_name}

IMPORTANT: This is a COMPLETE END-TO-END BENCHMARK. You must finish ALL work for this phase, not just setup or foundation.

Initial Benchmark Prompt:
{self.config.initial_prompt}

Your task is to FULLY COMPLETE the {phase_name} phase according to your role and responsibilities.

Time allocation: {duration_minutes} minutes

COMPLETION CRITERIA:
- For implementation phases: Complete ALL stories in the epic, with tests
- For planning phases: Create COMPLETE and DETAILED documentation
- For quality phases: Run ALL tests and audits, fix ALL issues

DO NOT stop at "foundation" or "setup" - you must deliver a COMPLETE, PRODUCTION-READY result.

Work autonomously to FULLY complete this phase."""

                phase = WorkflowPhaseConfig(
                    phase_name=phase_name,
                    command=prompt,  # Store prompt as command for agent execution
                    timeout_seconds=duration_minutes * 60,
                    quality_gates={"agent": agent_name, "prompt": prompt},
                )
                phases.append(phase)

        return phases

    def _initialize_git_repository(
        self, project_path: Path, result: BenchmarkResult
    ) -> None:
        """
        Initialize git repository in sandbox project.

        Creates git repo, configures user info, and makes initial commit
        with project structure (README, .gitignore, package.json if present).

        Args:
            project_path: Path to project directory
            result: Benchmark result to update with git info

        Raises:
            Exception: If git initialization fails
        """
        from ...core.git_manager import GitManager

        self.logger.info("initializing_git_repository", project_path=str(project_path))

        try:
            # Create GitManager instance
            git_manager = GitManager(project_path)

            # Initialize repository with initial commit
            init_result = git_manager.init_repo(
                user_name="GAO-Dev Benchmark",
                user_email="benchmark@gao-dev.local",
                initial_commit=True,
            )

            # Store git initialization info in result metadata
            result.metadata["git_initialized"] = True
            result.metadata["git_init_timestamp"] = init_result["timestamp"].isoformat()
            result.metadata["git_initial_commit"] = init_result.get("commit_hash")

            # Get and log git status
            status = git_manager.get_status()
            self.logger.info(
                "git_repository_initialized",
                project_path=str(project_path),
                commit_hash=init_result.get("commit_hash"),
                branch=status.get("branch"),
            )

        except Exception as e:
            error_msg = f"Failed to initialize git repository: {str(e)}"
            result.warnings.append(error_msg)
            self.logger.warning("git_initialization_failed", error=error_msg)
            # Don't fail the entire benchmark if git init fails
            # This allows the benchmark to continue without git integration

    def _cleanup(self, result: BenchmarkResult) -> None:
        """
        Cleanup after benchmark run.

        Args:
            result: Benchmark result
        """
        self.logger.info("cleanup_started", run_id=result.run_id)

        # Save metrics to database
        if result.metrics:
            try:
                from ...sandbox.metrics.storage import MetricsStorage

                storage = MetricsStorage()
                storage.save_metrics(result.metrics)
            except Exception as e:
                self.logger.error("failed_to_save_metrics", error=str(e))

        # TODO: Additional cleanup tasks
        # - Archive project if needed
        # - Generate reports
        # - Notify observers

        self.logger.info("cleanup_completed", run_id=result.run_id)
