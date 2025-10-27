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
    ):
        """
        Initialize benchmark runner.

        Args:
            config: Benchmark configuration
            sandbox_manager: Sandbox project manager
            metrics_collector: Metrics collection service
            sandbox_root: Root directory for sandbox projects
        """
        self.config = config
        self.sandbox_manager = sandbox_manager
        self.metrics_collector = metrics_collector
        self.sandbox_root = sandbox_root
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
            self.metrics_collector.start_collection(run_id)

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
        Initialize sandbox project.

        Args:
            result: Benchmark result to update

        Returns:
            Initialized sandbox project

        Raises:
            Exception: If initialization fails
        """
        project_name = self.config.project_name or self.config.name

        self.logger.info("initializing_sandbox", project_name=project_name)

        project = self.sandbox_manager.init_project(
            name=project_name,
            config={
                "benchmark_run_id": result.run_id,
                "benchmark_name": self.config.name,
            },
        )

        self.logger.info("sandbox_initialized", project_name=project_name)
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
            cloner.clone(
                url=self.config.boilerplate_url, target_dir=project.project_path
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
        Execute workflow phases.

        This is a placeholder that will be implemented in Story 4.4.

        Args:
            project: Sandbox project
            result: Benchmark result to update
        """
        self.logger.info("workflow_execution_placeholder")
        # TODO: Implement in Story 4.4
        pass

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
                storage.save_benchmark_metrics(result.run_id, result.metrics)
            except Exception as e:
                self.logger.error("failed_to_save_metrics", error=str(e))

        # TODO: Additional cleanup tasks
        # - Archive project if needed
        # - Generate reports
        # - Notify observers

        self.logger.info("cleanup_completed", run_id=result.run_id)
