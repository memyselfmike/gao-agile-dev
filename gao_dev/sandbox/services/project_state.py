"""Service for managing project state and metadata persistence."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import structlog
import yaml

from gao_dev.sandbox.models import ProjectMetadata, ProjectStatus
from gao_dev.sandbox.exceptions import (
    ProjectNotFoundError,
    ProjectStateError,
)

logger = structlog.get_logger(__name__)

METADATA_FILENAME = ".sandbox.yaml"


class ProjectStateService:
    """
    Manages project state and metadata persistence.

    Responsible for:
    - Loading and saving project metadata
    - Managing project status transitions

    Attributes:
        sandbox_root: Root directory for all sandbox projects
    """

    def __init__(self, sandbox_root: Path):
        """
        Initialize state service.

        Args:
            sandbox_root: Root directory for sandbox projects
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.projects_dir = self.sandbox_root / "projects"

    def get_project(self, name: str, lifecycle_service: "ProjectLifecycleService") -> ProjectMetadata:
        """
        Get project metadata.

        Args:
            name: Project name
            lifecycle_service: Service to check project existence

        Returns:
            ProjectMetadata object

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        if not lifecycle_service.project_exists(name):
            raise ProjectNotFoundError(name)

        project_dir = lifecycle_service.get_project_path(name)
        return self.load_metadata(project_dir)

    def update_status(
        self,
        project_name: str,
        new_status: ProjectStatus,
        reason: Optional[str] = None,
        lifecycle_service: Optional["ProjectLifecycleService"] = None,
    ) -> ProjectMetadata:
        """
        Update project status with validation.

        Validates state transitions before applying changes.

        Args:
            project_name: Name of project to update
            new_status: New status to set
            reason: Optional reason for status change
            lifecycle_service: Service to get project path

        Returns:
            Updated ProjectMetadata

        Raises:
            ProjectNotFoundError: If project doesn't exist
            ProjectStateError: If transition is invalid
        """
        if lifecycle_service is None:
            raise ValueError("lifecycle_service is required")

        metadata = self.get_project(project_name, lifecycle_service)
        if not self._is_valid_transition(metadata.status, new_status):
            raise ProjectStateError(
                project_name, metadata.status.value, new_status.value
            )
        old_status = metadata.status.value
        metadata.status = new_status
        metadata.last_modified = datetime.now()
        project_dir = lifecycle_service.get_project_path(project_name)
        self.save_metadata(project_dir, metadata)
        logger.info(
            "project_status_updated", project=project_name, old_status=old_status,
            new_status=new_status.value, reason=reason
        )
        return metadata

    def update_project(
        self,
        project_name: str,
        metadata: ProjectMetadata,
        lifecycle_service: Optional["ProjectLifecycleService"] = None,
    ) -> None:
        """
        Update project metadata.

        Args:
            project_name: Project name
            metadata: Updated metadata object
            lifecycle_service: Service to get project path

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        if lifecycle_service is None:
            raise ValueError("lifecycle_service is required")

        if not lifecycle_service.project_exists(project_name):
            raise ProjectNotFoundError(project_name)

        project_dir = lifecycle_service.get_project_path(project_name)
        metadata.last_modified = datetime.now()
        self.save_metadata(project_dir, metadata)
        logger.info("project_metadata_updated", project=project_name)

    def load_metadata(self, project_dir: Path) -> ProjectMetadata:
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

    def save_metadata(self, project_dir: Path, metadata: ProjectMetadata) -> None:
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

        logger.debug("metadata_saved", project_dir=str(project_dir))

    def create_metadata(
        self,
        name: str,
        description: str = "",
        boilerplate_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> ProjectMetadata:
        """
        Create new project metadata.

        Args:
            name: Project name
            description: Project description
            boilerplate_url: Optional boilerplate URL
            tags: Optional project tags

        Returns:
            ProjectMetadata object
        """
        metadata = ProjectMetadata(
            name=name,
            created_at=datetime.now(),
            status=ProjectStatus.ACTIVE,
            boilerplate_url=boilerplate_url,
            tags=tags or [],
            description=description,
        )

        logger.info("metadata_created", project=name)
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
        if current_status == new_status:
            return True

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
