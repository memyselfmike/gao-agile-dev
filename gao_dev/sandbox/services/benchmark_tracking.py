"""Service for managing benchmark run tracking."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import structlog

from gao_dev.sandbox.models import BenchmarkRun, ProjectMetadata

logger = structlog.get_logger(__name__)


class BenchmarkTrackingService:
    """
    Manages benchmark run tracking and history.

    Responsible for:
    - Adding benchmark runs to projects
    - Retrieving run history
    - Getting last run numbers for benchmarks

    Attributes:
        state_service: ProjectStateService for metadata operations
    """

    def __init__(self, state_service: "ProjectStateService"):
        """
        Initialize benchmark tracking service.

        Args:
            state_service: ProjectStateService for state management
        """
        self.state_service = state_service

    def add_benchmark_run(
        self,
        project_name: str,
        run_id: str,
        config_file: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> BenchmarkRun:
        """
        Add new benchmark run to project.

        Args:
            project_name: Name of project
            run_id: Unique identifier for this run
            config_file: Path to benchmark configuration file
            lifecycle_service: Service to get project metadata

        Returns:
            BenchmarkRun object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        metadata = self.state_service.get_project(project_name, lifecycle_service)

        run = BenchmarkRun(
            run_id=run_id,
            started_at=datetime.now(),
            config_file=config_file,
        )

        metadata.add_run(run)
        self.state_service.update_project(project_name, metadata, lifecycle_service)

        logger.info(
            "benchmark_run_added",
            project=project_name,
            run_id=run_id,
        )

        return run

    def get_run_history(
        self,
        project_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> List[BenchmarkRun]:
        """
        Get all benchmark runs for project.

        Args:
            project_name: Name of project
            lifecycle_service: Service to get project metadata

        Returns:
            List of BenchmarkRun objects, sorted by started_at descending

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        metadata = self.state_service.get_project(project_name, lifecycle_service)
        runs = sorted(metadata.runs, key=lambda r: r.started_at, reverse=True)

        logger.info(
            "run_history_retrieved",
            project=project_name,
            run_count=len(runs),
        )

        return runs

    def get_last_run_number(
        self,
        benchmark_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> int:
        """
        Get the highest run number for a benchmark.

        Scans all projects matching the benchmark name pattern
        (e.g., 'todo-app-baseline-run-001', 'todo-app-baseline-run-002')
        and returns the highest run number found. Returns 0 if
        no runs exist yet.

        Args:
            benchmark_name: Name of the benchmark (e.g., 'todo-app-baseline')
            lifecycle_service: Service for listing projects

        Returns:
            Highest run number (0 if no runs exist)
        """
        projects = self._get_projects_for_benchmark(
            benchmark_name, lifecycle_service
        )

        if not projects:
            logger.debug("no_benchmark_runs_found", benchmark_name=benchmark_name)
            return 0

        # Extract run numbers from project names
        # Format: benchmark-name-run-NNN
        pattern = f"{benchmark_name}-run-"
        max_num = 0

        for project in projects:
            if project.name.startswith(pattern):
                # Extract the number part
                suffix = project.name[len(pattern) :]
                try:
                    run_num = int(suffix)
                    max_num = max(max_num, run_num)
                except ValueError:
                    # Not a valid run number, skip
                    continue

        logger.info(
            "last_run_number_retrieved",
            benchmark_name=benchmark_name,
            last_run=max_num,
        )

        return max_num

    def get_projects_for_benchmark(
        self,
        benchmark_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> List[ProjectMetadata]:
        """
        Get all projects associated with a specific benchmark.

        Finds projects whose names start with the benchmark name pattern
        (e.g., 'todo-app-baseline-run-001', 'todo-app-baseline-run-002').

        Args:
            benchmark_name: Name of the benchmark (e.g., 'todo-app-baseline')
            lifecycle_service: Service for listing projects

        Returns:
            List of ProjectMetadata objects for matching projects
        """
        return self._get_projects_for_benchmark(benchmark_name, lifecycle_service)

    def create_run_project(
        self,
        benchmark_name: str,
        benchmark_version: str,
        benchmark_file: Path,
        complexity_level: int,
        estimated_duration_minutes: int,
        prompt_hash: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> ProjectMetadata:
        """
        Create a new project with auto-generated run ID.

        Automatically generates the next run ID in sequence for the
        specified benchmark, following the format: benchmark-name-run-NNN

        Example: If last run was 'todo-app-baseline-run-003',
        creates 'todo-app-baseline-run-004'.

        Args:
            benchmark_name: Name of benchmark
            benchmark_version: Version of benchmark
            benchmark_file: Path to benchmark YAML file
            complexity_level: Complexity level of benchmark
            estimated_duration_minutes: Estimated duration
            prompt_hash: Hash of benchmark prompt
            lifecycle_service: Service for creating projects

        Returns:
            ProjectMetadata for the created project

        Raises:
            InvalidProjectNameError: If generated name is invalid
            ProjectExistsError: If project somehow already exists
        """
        # Get next run number
        last_run = self.get_last_run_number(benchmark_name, lifecycle_service)
        next_run = last_run + 1

        # Generate run ID with zero-padding (3 digits)
        run_id = f"{benchmark_name}-run-{next_run:03d}"

        logger.info(
            "creating_run_project",
            run_id=run_id,
            benchmark_name=benchmark_name,
            run_number=next_run,
        )

        # Create project with generated name
        metadata = lifecycle_service.create_project(
            name=run_id,
            tags=["benchmark", benchmark_name, f"version:{benchmark_version}"],
            description=f"Benchmark run {next_run} for {benchmark_name} v{benchmark_version}",
        )

        # Add benchmark info to metadata
        metadata.benchmark_info = {
            "benchmark_name": benchmark_name,
            "benchmark_version": benchmark_version,
            "benchmark_file": str(benchmark_file),
            "prompt_hash": prompt_hash,
            "run_number": next_run,
            "complexity_level": complexity_level,
            "estimated_duration_minutes": estimated_duration_minutes,
        }

        # Update metadata with benchmark info
        self.state_service.update_project(run_id, metadata, lifecycle_service)

        logger.info(
            "run_project_created",
            run_id=run_id,
            run_number=next_run,
        )

        return metadata

    def _get_projects_for_benchmark(
        self,
        benchmark_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> List[ProjectMetadata]:
        """
        Get all projects for a specific benchmark.

        Args:
            benchmark_name: Name of benchmark
            lifecycle_service: Service for listing projects

        Returns:
            List of matching ProjectMetadata objects
        """
        pattern = f"{benchmark_name}-run-"
        all_projects = lifecycle_service.list_projects()
        return [p for p in all_projects if p.name.startswith(pattern)]
