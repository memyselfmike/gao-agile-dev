"""Service for managing benchmark run tracking."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

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
        """Get highest run number for benchmark (format: benchmark-name-run-NNN)."""
        projects = self._get_projects_for_benchmark(benchmark_name, lifecycle_service)
        if not projects:
            logger.debug("no_benchmark_runs_found", benchmark_name=benchmark_name)
            return 0
        pattern = f"{benchmark_name}-run-"
        max_num = 0
        for project in projects:
            if project.name.startswith(pattern):
                try:
                    run_num = int(project.name[len(pattern):])
                    max_num = max(max_num, run_num)
                except ValueError:
                    continue
        logger.info("last_run_number_retrieved", benchmark_name=benchmark_name, last_run=max_num)
        return max_num

    def get_projects_for_benchmark(
        self,
        benchmark_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> List[ProjectMetadata]:
        """Get all projects for benchmark (matching benchmark-name-run-* pattern)."""
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
        """Create project with auto-generated run ID (format: benchmark-name-run-NNN)."""
        last_run = self.get_last_run_number(benchmark_name, lifecycle_service)
        next_run = last_run + 1
        run_id = f"{benchmark_name}-run-{next_run:03d}"
        logger.info("creating_run_project", run_id=run_id, run_number=next_run)
        metadata = lifecycle_service.create_project(
            name=run_id,
            tags=["benchmark", benchmark_name, f"version:{benchmark_version}"],
            description=f"Benchmark run {next_run} for {benchmark_name} v{benchmark_version}",
        )
        metadata.benchmark_info = {
            "benchmark_name": benchmark_name,
            "benchmark_version": benchmark_version,
            "benchmark_file": str(benchmark_file),
            "prompt_hash": prompt_hash,
            "run_number": next_run,
            "complexity_level": complexity_level,
            "estimated_duration_minutes": estimated_duration_minutes,
        }
        self.state_service.update_project(run_id, metadata, lifecycle_service)
        logger.info("run_project_created", run_id=run_id, run_number=next_run)
        return metadata

    def _get_projects_for_benchmark(
        self,
        benchmark_name: str,
        lifecycle_service: "ProjectLifecycleService",
    ) -> List[ProjectMetadata]:
        """Get projects matching benchmark name pattern."""
        pattern = f"{benchmark_name}-run-"
        return [p for p in lifecycle_service.list_projects() if p.name.startswith(pattern)]
