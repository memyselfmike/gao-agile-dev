"""Sandbox manager for project lifecycle operations."""

import re
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import yaml

from .models import ProjectMetadata, ProjectStatus, BenchmarkRun
from .exceptions import (
    ProjectExistsError,
    ProjectNotFoundError,
    InvalidProjectNameError,
    ProjectStateError,
)

# Constants
METADATA_FILENAME = ".sandbox.yaml"
PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
MAX_PROJECT_NAME_LENGTH = 50
MIN_PROJECT_NAME_LENGTH = 3


class SandboxManager:
    """
    Manages sandbox project lifecycle and operations.

    Responsible for creating, reading, updating, and deleting
    sandbox projects, as well as managing their metadata.

    Attributes:
        sandbox_root: Root directory for all sandbox projects
        projects_dir: Directory containing project subdirectories
    """

    def __init__(self, sandbox_root: Path):
        """
        Initialize sandbox manager.

        Args:
            sandbox_root: Root directory for sandbox projects
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.projects_dir = self.sandbox_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

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
        # Validate project name
        self._validate_project_name(name)

        # Check if already exists
        if self.project_exists(name):
            raise ProjectExistsError(name)

        # Create project directory
        project_dir = self.projects_dir / name
        project_dir.mkdir(parents=True, exist_ok=False)

        # Create metadata
        metadata = ProjectMetadata(
            name=name,
            created_at=datetime.now(),
            status=ProjectStatus.ACTIVE,
            boilerplate_url=boilerplate_url,
            tags=tags or [],
            description=description,
        )

        # Create directory structure
        self._create_project_structure(project_dir)

        # Save metadata
        self._save_metadata(project_dir, metadata)

        return metadata

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
        if not self.project_exists(name):
            raise ProjectNotFoundError(name)

        project_dir = self.get_project_path(name)
        return self._load_metadata(project_dir)

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
        projects: List[ProjectMetadata] = []

        # Iterate through project directories
        if not self.projects_dir.exists():
            return projects

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Skip if no metadata file
            metadata_file = project_dir / METADATA_FILENAME
            if not metadata_file.exists():
                continue

            try:
                metadata = self._load_metadata(project_dir)

                # Apply status filter if specified
                if status is None or metadata.status == status:
                    projects.append(metadata)

            except Exception:
                # Skip projects with invalid metadata
                continue

        # Sort by last_modified descending (newest first)
        projects.sort(key=lambda p: p.last_modified, reverse=True)

        return projects

    def update_project(self, name: str, metadata: ProjectMetadata) -> None:
        """
        Update project metadata.

        Args:
            name: Project name
            metadata: Updated metadata object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        if not self.project_exists(name):
            raise ProjectNotFoundError(name)

        project_dir = self.get_project_path(name)
        metadata.last_modified = datetime.now()
        self._save_metadata(project_dir, metadata)

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
        if not self.project_exists(name):
            raise ProjectNotFoundError(name)

        project_dir = self.get_project_path(name)
        shutil.rmtree(project_dir)

    def project_exists(self, name: str) -> bool:
        """
        Check if project exists.

        Args:
            name: Project name

        Returns:
            True if project exists, False otherwise
        """
        project_dir = self.projects_dir / name
        metadata_file = project_dir / METADATA_FILENAME
        return project_dir.exists() and metadata_file.exists()

    def get_project_path(self, name: str) -> Path:
        """
        Get absolute path to project directory.

        Args:
            name: Project name

        Returns:
            Absolute Path to project directory
        """
        return (self.projects_dir / name).resolve()

    def _create_project_structure(self, project_dir: Path) -> None:
        """
        Create standard project directory structure.

        Creates subdirectories for organizing project files.

        Args:
            project_dir: Project root directory
        """
        # Standard directories
        directories = [
            "docs",
            "src",
            "tests",
            "benchmarks",
            ".gao-dev",  # For GAO-Dev metadata
        ]

        for dir_name in directories:
            (project_dir / dir_name).mkdir(parents=True, exist_ok=True)

    def _load_metadata(self, project_dir: Path) -> ProjectMetadata:
        """
        Load project metadata from .sandbox.yaml file.

        Args:
            project_dir: Project directory containing metadata file

        Returns:
            ProjectMetadata object

        Raises:
            FileNotFoundError: If metadata file doesn't exist
            ValueError: If metadata is invalid
        """
        metadata_file = project_dir / METADATA_FILENAME

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        with open(metadata_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty or invalid metadata file: {metadata_file}")

        return ProjectMetadata.from_dict(data)

    def _save_metadata(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """
        Save project metadata to .sandbox.yaml file.

        Args:
            project_dir: Project directory to save metadata in
            metadata: ProjectMetadata object to save
        """
        metadata_file = project_dir / METADATA_FILENAME

        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                metadata.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def _validate_project_name(self, name: str) -> None:
        """
        Validate project name meets requirements.

        Project names must:
        - Be 3-50 characters long
        - Start and end with alphanumeric character
        - Contain only lowercase letters, numbers, and hyphens
        - Not contain consecutive hyphens

        Args:
            name: Project name to validate

        Raises:
            InvalidProjectNameError: If name doesn't meet requirements
        """
        # Check length
        if len(name) < MIN_PROJECT_NAME_LENGTH:
            raise InvalidProjectNameError(
                name, f"Must be at least {MIN_PROJECT_NAME_LENGTH} characters long"
            )

        if len(name) > MAX_PROJECT_NAME_LENGTH:
            raise InvalidProjectNameError(
                name, f"Must be at most {MAX_PROJECT_NAME_LENGTH} characters long"
            )

        # Check pattern (lowercase alphanumeric and hyphens only)
        if not PROJECT_NAME_PATTERN.match(name):
            raise InvalidProjectNameError(
                name,
                "Must start and end with alphanumeric character, "
                "and contain only lowercase letters, numbers, and hyphens",
            )

        # Check for consecutive hyphens
        if "--" in name:
            raise InvalidProjectNameError(name, "Cannot contain consecutive hyphens")

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
        metadata = self.get_project(project_name)

        # Validate state transition
        if not self._is_valid_transition(metadata.status, new_status):
            raise ProjectStateError(
                project_name, metadata.status.value, new_status.value
            )

        metadata.status = new_status
        metadata.last_modified = datetime.now()
        self.update_project(project_name, metadata)

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
        metadata = self.get_project(project_name)

        run = BenchmarkRun(
            run_id=run_id,
            started_at=datetime.now(),
            config_file=config_file,
        )

        metadata.add_run(run)
        self.update_project(project_name, metadata)

        return run

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
        metadata = self.get_project(project_name)
        runs = sorted(metadata.runs, key=lambda r: r.started_at, reverse=True)
        return runs

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
        pattern = f"{benchmark_name}-run-"
        all_projects = self.list_projects()
        return [p for p in all_projects if p.name.startswith(pattern)]

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
        projects = self.get_projects_for_benchmark(benchmark_name)

        if not projects:
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

        return max_num

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
        benchmark_name = benchmark_config.name
        benchmark_version = benchmark_config.version

        # Get next run number
        last_run = self.get_last_run_number(benchmark_name)
        next_run = last_run + 1

        # Generate run ID with zero-padding (3 digits)
        run_id = f"{benchmark_name}-run-{next_run:03d}"

        # Create project with generated name
        metadata = self.create_project(
            name=run_id,
            tags=["benchmark", benchmark_name, f"version:{benchmark_version}"],
            description=f"Benchmark run {next_run} for {benchmark_name} v{benchmark_version}",
        )

        # Add benchmark info to metadata
        metadata.benchmark_info = {
            "benchmark_name": benchmark_name,
            "benchmark_version": benchmark_version,
            "benchmark_file": str(benchmark_file),
            "prompt_hash": benchmark_config.prompt_hash,
            "run_number": next_run,
            "complexity_level": benchmark_config.complexity_level,
            "estimated_duration_minutes": benchmark_config.estimated_duration_minutes,
        }

        # Update metadata with benchmark info
        self.update_project(run_id, metadata)

        return metadata

    def _is_valid_transition(
        self, current_status: ProjectStatus, new_status: ProjectStatus
    ) -> bool:
        """
        Check if status transition is valid.

        Valid transitions:
        - ACTIVE -> COMPLETED, FAILED, ARCHIVED
        - COMPLETED -> ACTIVE, ARCHIVED
        - FAILED -> ACTIVE, ARCHIVED
        - ARCHIVED -> ACTIVE
        - Any status -> Same status (no-op)

        Args:
            current_status: Current project status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        # Same status is always valid (no-op)
        if current_status == new_status:
            return True

        # Define valid transitions
        valid_transitions = {
            ProjectStatus.ACTIVE: {
                ProjectStatus.COMPLETED,
                ProjectStatus.FAILED,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.COMPLETED: {ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED},
            ProjectStatus.FAILED: {ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED},
            ProjectStatus.ARCHIVED: {ProjectStatus.ACTIVE},
        }

        return new_status in valid_transitions.get(current_status, set())

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
