"""Sandbox manager for project lifecycle operations - thin facade pattern."""

import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import structlog

from .models import ProjectMetadata, ProjectStatus, BenchmarkRun
from .exceptions import ProjectNotFoundError
from .git_cloner import GitCloner
from .services.project_lifecycle import ProjectLifecycleService
from .services.project_state import ProjectStateService
from .services.boilerplate import BoilerplateService
from .services.benchmark_tracking import BenchmarkTrackingService

logger = structlog.get_logger(__name__)

# Constants
METADATA_FILENAME = ".sandbox.yaml"


class SandboxManager:
    """
    Manages sandbox project lifecycle and operations.

    This is a facade that delegates operations to specialized services:
    - ProjectLifecycleService: Project CRUD operations
    - ProjectStateService: State management and persistence
    - BoilerplateService: Boilerplate cloning and template processing
    - BenchmarkTrackingService: Benchmark run tracking

    Maintains backward compatibility with the previous API while using
    the refactored services internally.

    Attributes:
        sandbox_root: Root directory for all sandbox projects
        projects_dir: Directory containing project subdirectories
        lifecycle_service: Service for project lifecycle operations
        state_service: Service for state management
        boilerplate_service: Service for boilerplate operations
        benchmark_service: Service for benchmark tracking
    """

    def __init__(
        self,
        sandbox_root: Path,
        git_cloner: Optional[GitCloner] = None,
        state_service: Optional[ProjectStateService] = None,
        boilerplate_service: Optional[BoilerplateService] = None,
        lifecycle_service: Optional[ProjectLifecycleService] = None,
        benchmark_service: Optional[BenchmarkTrackingService] = None,
    ):
        """
        Initialize sandbox manager.

        Args:
            sandbox_root: Root directory for sandbox projects
            git_cloner: Optional GitCloner instance (creates default if not provided)
            state_service: Optional ProjectStateService (creates default if not provided)
            boilerplate_service: Optional BoilerplateService (creates default if not provided)
            lifecycle_service: Optional ProjectLifecycleService (creates default if not provided)
            benchmark_service: Optional BenchmarkTrackingService (creates default if not provided)
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.projects_dir = self.sandbox_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or use injected services
        self._git_cloner = git_cloner or GitCloner()

        self.state_service = state_service or ProjectStateService(
            sandbox_root=self.sandbox_root
        )
        self.boilerplate_service = boilerplate_service or BoilerplateService(
            git_cloner=self._git_cloner
        )
        self.lifecycle_service = lifecycle_service or ProjectLifecycleService(
            sandbox_root=self.sandbox_root,
            state_service=self.state_service,
            boilerplate_service=self.boilerplate_service,
        )
        self.benchmark_service = benchmark_service or BenchmarkTrackingService(
            state_service=self.state_service
        )

    @property
    def git_cloner(self) -> GitCloner:
        """Get the current GitCloner instance."""
        return self._git_cloner

    @git_cloner.setter
    def git_cloner(self, cloner: GitCloner) -> None:
        """Set a new GitCloner instance and update services."""
        self._git_cloner = cloner
        self.boilerplate_service.set_git_cloner(cloner)

    def create_project(
        self,
        name: str,
        boilerplate_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> ProjectMetadata:
        """
        Create a new sandbox project.

        Creates project directory structure and initializes metadata.
        Project will be created in sandbox_root/projects/<name>/.

        Args:
            name: Project name (must be unique and valid)
            boilerplate_url: Optional boilerplate repository URL
            tags: Optional project tags
            description: Optional project description

        Returns:
            ProjectMetadata object for the new project

        Raises:
            ProjectExistsError: If project already exists
            InvalidProjectNameError: If name doesn't meet requirements
        """
        # Delegate to lifecycle service
        return self.lifecycle_service.create_project(
            name=name,
            description=description,
            boilerplate_url=boilerplate_url,
            tags=tags,
        )

    def get_project(self, name: str) -> ProjectMetadata:
        """
        Get project metadata.

        Args:
            name: Project name

        Returns:
            ProjectMetadata object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Delegate to state service
        return self.state_service.get_project(name, self.lifecycle_service)

    def list_projects(
        self, status: Optional[ProjectStatus] = None
    ) -> List[ProjectMetadata]:
        """
        List all sandbox projects.

        Args:
            status: Optional status filter (only return projects with this status)

        Returns:
            List of ProjectMetadata objects, sorted by last_modified descending
        """
        # Delegate to lifecycle service
        return self.lifecycle_service.list_projects(status=status)

    def update_project(self, name: str, metadata: ProjectMetadata) -> None:
        """
        Update project metadata.

        Args:
            name: Project name
            metadata: Updated metadata object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Delegate to state service
        self.state_service.update_project(
            name, metadata, lifecycle_service=self.lifecycle_service
        )

    def delete_project(self, name: str) -> None:
        """
        Delete a sandbox project.

        Permanently removes project directory and all contents.
        This operation cannot be undone.

        Args:
            name: Project name

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Delegate to lifecycle service
        self.lifecycle_service.delete_project(name)

    def project_exists(self, name: str) -> bool:
        """
        Check if project exists.

        Args:
            name: Project name

        Returns:
            True if project exists, False otherwise
        """
        # Delegate to lifecycle service
        return self.lifecycle_service.project_exists(name)

    def get_project_path(self, name: str) -> Path:
        """
        Get absolute path to project directory.

        Args:
            name: Project name

        Returns:
            Absolute Path to project directory
        """
        # Delegate to lifecycle service
        return self.lifecycle_service.get_project_path(name)

    def initialize_document_lifecycle(
        self,
        project_name: str,
        force: bool = False
    ) -> bool:
        """
        Initialize document lifecycle for existing project.

        Args:
            project_name: Name of the project
            force: Force re-initialization

        Returns:
            True if successful
        """
        # Delegate to lifecycle service
        return self.lifecycle_service.initialize_document_lifecycle(
            project_name,
            force
        )

    def update_status(
        self,
        project_name: str,
        new_status: ProjectStatus,
        reason: Optional[str] = None,
    ) -> None:
        """
        Update project status with validation.

        Validates state transitions before applying changes.

        Args:
            project_name: Name of project to update
            new_status: New status to set
            reason: Optional reason for status change

        Raises:
            ProjectNotFoundError: If project doesn't exist
            ProjectStateError: If transition is invalid
        """
        # Delegate to state service
        self.state_service.update_status(
            project_name, new_status, reason, lifecycle_service=self.lifecycle_service
        )

    def add_benchmark_run(
        self,
        project_name: str,
        run_id: str,
        config_file: str,
    ) -> BenchmarkRun:
        """
        Add new benchmark run to project.

        Args:
            project_name: Name of project
            run_id: Unique identifier for this run
            config_file: Path to benchmark configuration file

        Returns:
            BenchmarkRun object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Delegate to benchmark service
        return self.benchmark_service.add_benchmark_run(
            project_name, run_id, config_file, self.lifecycle_service
        )

    def get_run_history(self, project_name: str) -> List[BenchmarkRun]:
        """
        Get all benchmark runs for project.

        Args:
            project_name: Name of project

        Returns:
            List of BenchmarkRun objects, sorted by started_at descending

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Delegate to benchmark service
        return self.benchmark_service.get_run_history(project_name, self.lifecycle_service)

    def is_clean(self, project_name: str) -> bool:
        """
        Check if project is in clean state.

        A project is considered clean if:
        - Status is ACTIVE
        - No failed runs
        - Latest run (if any) is completed

        Args:
            project_name: Name of project

        Returns:
            True if project is clean, False otherwise

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        metadata = self.get_project(project_name)

        # Must be ACTIVE status
        if metadata.status != ProjectStatus.ACTIVE:
            return False

        # Check latest run
        latest_run = metadata.get_latest_run()
        if latest_run:
            # Latest run must be completed (not active or failed)
            if latest_run.status in (ProjectStatus.ACTIVE, ProjectStatus.FAILED):
                return False

        return True

    def mark_clean(self, project_name: str) -> None:
        """
        Mark project as clean and ready for new run.

        Resets project to ACTIVE status (if not already).
        Does not delete files or runs, just updates status.

        Args:
            project_name: Name of project

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        metadata = self.get_project(project_name)

        # Set to ACTIVE status
        if metadata.status != ProjectStatus.ACTIVE:
            metadata.status = ProjectStatus.ACTIVE

        metadata.last_modified = datetime.now()
        self.update_project(project_name, metadata)

    def get_projects_for_benchmark(self, benchmark_name: str) -> List[ProjectMetadata]:
        """
        Get all projects associated with a specific benchmark.

        Finds projects whose names start with the benchmark name pattern
        (e.g., 'todo-app-baseline-run-001', 'todo-app-baseline-run-002').

        Args:
            benchmark_name: Name of the benchmark (e.g., 'todo-app-baseline')

        Returns:
            List of ProjectMetadata objects for matching projects
        """
        # Delegate to benchmark service
        return self.benchmark_service.get_projects_for_benchmark(
            benchmark_name, self.lifecycle_service
        )

    def get_last_run_number(self, benchmark_name: str) -> int:
        """
        Get the highest run number for a benchmark.

        Scans all projects matching the benchmark name pattern
        and returns the highest run number found. Returns 0 if
        no runs exist yet.

        Args:
            benchmark_name: Name of the benchmark (e.g., 'todo-app-baseline')

        Returns:
            Highest run number (0 if no runs exist)
        """
        # Delegate to benchmark service
        return self.benchmark_service.get_last_run_number(
            benchmark_name, self.lifecycle_service
        )

    def create_run_project(
        self, benchmark_file: Path, benchmark_config: "BenchmarkConfig"
    ) -> ProjectMetadata:
        """
        Create a new project with auto-generated run ID.

        Automatically generates the next run ID in sequence for the
        specified benchmark, following the format: benchmark-name-run-NNN

        Example: If last run was 'todo-app-baseline-run-003',
        creates 'todo-app-baseline-run-004'.

        Args:
            benchmark_file: Path to the benchmark YAML file
            benchmark_config: Parsed benchmark configuration

        Returns:
            ProjectMetadata for the created project

        Raises:
            InvalidProjectNameError: If generated name is invalid
            ProjectExistsError: If project somehow already exists
        """
        # Extract benchmark name - handle case where benchmark_config.name is dict
        if isinstance(benchmark_config.name, dict):
            # Config was created incorrectly - extract from nested structure
            benchmark_name = benchmark_config.name.get("benchmark", {}).get("name", "benchmark")
            benchmark_version = benchmark_config.name.get("benchmark", {}).get("version", "1.0.0")
            complexity_level = benchmark_config.name.get("benchmark", {}).get("complexity_level", 2)
            estimated_duration = benchmark_config.name.get("benchmark", {}).get("estimated_duration_minutes", 120)
            prompt_hash = benchmark_config.prompt_hash or ""
        else:
            # Config was created correctly
            benchmark_name = benchmark_config.name
            benchmark_version = benchmark_config.version
            complexity_level = benchmark_config.complexity_level
            estimated_duration = benchmark_config.estimated_duration_minutes
            prompt_hash = benchmark_config.prompt_hash

        # Delegate to benchmark service
        return self.benchmark_service.create_run_project(
            benchmark_name=benchmark_name,
            benchmark_version=benchmark_version,
            benchmark_file=benchmark_file,
            complexity_level=complexity_level,
            estimated_duration_minutes=estimated_duration,
            prompt_hash=prompt_hash,
            lifecycle_service=self.lifecycle_service,
        )


    def clean_project(
        self,
        project_name: str,
        full: bool = False,
        output_only: bool = False,
        runs_only: bool = False,
    ) -> dict:
        """
        Clean project to fresh state.

        Args:
            project_name: Project to clean
            full: If True, remove all files except metadata
            output_only: If True, only remove generated output files
            runs_only: If True, only clear run history

        Returns:
            Dictionary with cleanup statistics

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        if not self.project_exists(project_name):
            raise ProjectNotFoundError(project_name)

        project_dir = self.get_project_path(project_name)
        stats = {
            "files_deleted": 0,
            "dirs_deleted": 0,
            "runs_cleared": 0,
        }

        if runs_only:
            # Only clear run history
            metadata = self.get_project(project_name)
            stats["runs_cleared"] = len(metadata.runs)
            metadata.runs = []
            metadata.last_modified = datetime.now()
            self.update_project(project_name, metadata)
            return stats

        # Define directories to clean
        clean_dirs = []

        if full:
            # Full clean: remove everything except metadata
            for item in project_dir.iterdir():
                if item.name not in [METADATA_FILENAME, ".gao-dev"]:
                    if item.is_dir():
                        shutil.rmtree(item)
                        stats["dirs_deleted"] += 1
                    else:
                        item.unlink()
                        stats["files_deleted"] += 1

        elif output_only:
            # Output only: clean generated files
            output_patterns = [
                "src/**/*.pyc",
                "src/**/__pycache__",
                "dist",
                "build",
                ".next",
                "node_modules",
                "*.log",
            ]

            for pattern in output_patterns:
                for item in project_dir.glob(pattern):
                    if item.is_dir():
                        shutil.rmtree(item)
                        stats["dirs_deleted"] += 1
                    elif item.is_file():
                        item.unlink()
                        stats["files_deleted"] += 1

        else:
            # Standard clean: remove src, docs, tests contents but keep structure
            for subdir in ["src", "docs", "tests"]:
                subdir_path = project_dir / subdir
                if subdir_path.exists():
                    for item in subdir_path.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                            stats["dirs_deleted"] += 1
                        else:
                            item.unlink()
                            stats["files_deleted"] += 1

        # Reset project to clean state
        self.mark_clean(project_name)

        return stats
