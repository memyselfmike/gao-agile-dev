"""Service for managing project lifecycle operations."""

import re
import shutil
from pathlib import Path
from typing import List, Optional

import structlog

from gao_dev.sandbox.models import ProjectMetadata, ProjectStatus
from gao_dev.sandbox.exceptions import (
    ProjectExistsError,
    ProjectNotFoundError,
    InvalidProjectNameError,
)

logger = structlog.get_logger(__name__)

# Constants
METADATA_FILENAME = ".sandbox.yaml"
PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
MAX_PROJECT_NAME_LENGTH = 50
MIN_PROJECT_NAME_LENGTH = 3


class ProjectLifecycleService:
    """
    Manages project lifecycle operations (CRUD).

    Responsible for creating, reading, deleting projects and checking
    their existence. Works with ProjectStateService for metadata
    persistence and BoilerplateService for boilerplate integration.

    Attributes:
        sandbox_root: Root directory for all sandbox projects
        projects_dir: Directory containing project subdirectories
        state_service: ProjectStateService for metadata operations
        boilerplate_service: Optional BoilerplateService for cloning
    """

    def __init__(
        self,
        sandbox_root: Path,
        state_service: "ProjectStateService",
        boilerplate_service: Optional["BoilerplateService"] = None,
    ):
        """
        Initialize lifecycle service.

        Args:
            sandbox_root: Root directory for sandbox projects
            state_service: Service for state management
            boilerplate_service: Optional service for boilerplate cloning
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.projects_dir = self.sandbox_root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.state_service = state_service
        self.boilerplate_service = boilerplate_service

    def create_project(
        self,
        name: str,
        description: str = "",
        boilerplate_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ProjectMetadata:
        """
        Create a new sandbox project.

        Creates project directory and initializes metadata.
        Project will be created in sandbox_root/projects/<name>/.

        Args:
            name: Project name (must be unique and valid)
            description: Optional project description
            boilerplate_url: Optional boilerplate repository URL
            tags: Optional project tags

        Returns:
            ProjectMetadata object for the new project

        Raises:
            ProjectExistsError: If project already exists
            InvalidProjectNameError: If name doesn't meet requirements
            Exception: If boilerplate cloning fails
        """
        # Validate project name
        self._validate_project_name(name)

        # Check if already exists
        if self.project_exists(name):
            raise ProjectExistsError(name)

        # Create project directory
        project_dir = self.projects_dir / name
        project_dir.mkdir(parents=True, exist_ok=False)

        logger.info("project_created_directory", project=name, path=str(project_dir))

        try:
            # Clone boilerplate if URL provided
            if boilerplate_url and self.boilerplate_service:
                logger.info(
                    "cloning_boilerplate_for_project",
                    project=name,
                    boilerplate_url=boilerplate_url,
                )
                self.boilerplate_service.clone_boilerplate(boilerplate_url, project_dir)

            else:
                # Create standard directory structure
                self._create_project_structure(project_dir)

            # Create and save metadata using state service
            metadata = self.state_service.create_metadata(
                name=name,
                description=description,
                boilerplate_url=boilerplate_url,
                tags=tags or [],
            )

            self.state_service.save_metadata(project_dir, metadata)

            logger.info("project_created_successfully", project=name)

            return metadata

        except Exception as e:
            logger.error("project_creation_failed", project=name, error=str(e))
            if project_dir.exists():
                shutil.rmtree(project_dir)
            raise

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
        logger.info("project_deleted", project=name)

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
                metadata = self.state_service.load_metadata(project_dir)

                # Apply status filter if specified
                if status is None or metadata.status == status:
                    projects.append(metadata)

            except Exception as e:
                # Skip projects with invalid metadata
                logger.warning(
                    "skipping_project_invalid_metadata",
                    project_dir=str(project_dir),
                    error=str(e),
                )
                continue

        # Sort by last_modified descending (newest first)
        projects.sort(key=lambda p: p.last_modified, reverse=True)

        logger.info("listed_projects", count=len(projects))

        return projects

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

    def _validate_project_name(self, name: str) -> None:
        """Validate project name (3-50 chars, alphanumeric + hyphens, no consecutive hyphens)."""
        if len(name) < MIN_PROJECT_NAME_LENGTH:
            raise InvalidProjectNameError(
                name, f"Must be at least {MIN_PROJECT_NAME_LENGTH} characters long"
            )
        if len(name) > MAX_PROJECT_NAME_LENGTH:
            raise InvalidProjectNameError(
                name, f"Must be at most {MAX_PROJECT_NAME_LENGTH} characters long"
            )
        if not PROJECT_NAME_PATTERN.match(name):
            raise InvalidProjectNameError(
                name,
                "Must start/end with alphanumeric, contain only [a-z0-9-]",
            )
        if "--" in name:
            raise InvalidProjectNameError(name, "Cannot contain consecutive hyphens")

    def _create_project_structure(self, project_dir: Path) -> None:
        """Create standard project directory structure (docs, src, tests, benchmarks, .gao-dev)."""
        for dir_name in ["docs", "src", "tests", "benchmarks", ".gao-dev"]:
            (project_dir / dir_name).mkdir(parents=True, exist_ok=True)
        logger.info("project_structure_created", project_dir=str(project_dir))
