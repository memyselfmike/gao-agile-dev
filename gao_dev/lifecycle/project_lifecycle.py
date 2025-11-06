"""
Project-scoped document lifecycle initialization.

This module provides factory methods for creating document lifecycle
components that are scoped to a specific project, ensuring proper
isolation and context management.
"""

from pathlib import Path
from typing import Optional
import structlog

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager

logger = structlog.get_logger(__name__)


class ProjectDocumentLifecycle:
    """
    Factory for creating project-scoped document lifecycle components.

    This class provides a centralized way to initialize the document
    lifecycle system for a specific project, ensuring all components
    are properly configured and isolated.
    """

    @classmethod
    def initialize(
        cls,
        project_root: Path,
        create_dirs: bool = True
    ) -> DocumentLifecycleManager:
        """
        Initialize document lifecycle for a project.

        Creates the necessary directory structure and initializes all
        document lifecycle components with project-specific paths.

        Args:
            project_root: Root directory of the project
            create_dirs: Whether to create directories if they don't exist

        Returns:
            Fully initialized DocumentLifecycleManager

        Raises:
            ValueError: If project_root doesn't exist and create_dirs is False
            OSError: If directory creation fails

        Example:
            >>> project_root = Path("sandbox/projects/my-app")
            >>> doc_lifecycle = ProjectDocumentLifecycle.initialize(project_root)
            >>> doc_lifecycle.register_document("PRD.md", "product-requirements")
        """
        logger.info(
            "Initializing project-scoped document lifecycle",
            project_root=str(project_root)
        )

        # Validate project root
        if not project_root.exists():
            if create_dirs:
                logger.debug("Creating project root directory")
                project_root.mkdir(parents=True, exist_ok=True)
            else:
                raise ValueError(f"Project root does not exist: {project_root}")

        # Create .gao-dev directory
        gao_dev_dir = project_root / ".gao-dev"
        if create_dirs:
            gao_dev_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(".gao-dev directory ready", path=str(gao_dev_dir))

        # Set up paths
        db_path = gao_dev_dir / "documents.db"
        archive_dir = project_root / ".archive"

        logger.debug(
            "Project paths configured",
            db_path=str(db_path),
            archive_dir=str(archive_dir)
        )

        # Initialize components
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(
            registry=registry,
            archive_dir=archive_dir,
            project_root=project_root
        )

        logger.info(
            "Document lifecycle initialized successfully",
            project_root=str(project_root)
        )

        return manager

    @classmethod
    def get_gao_dev_dir(cls, project_root: Path) -> Path:
        """
        Get the .gao-dev directory path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to .gao-dev directory
        """
        return project_root / ".gao-dev"

    @classmethod
    def get_db_path(cls, project_root: Path) -> Path:
        """
        Get the documents.db path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to documents.db file
        """
        return cls.get_gao_dev_dir(project_root) / "documents.db"

    @classmethod
    def get_archive_dir(cls, project_root: Path) -> Path:
        """
        Get the archive directory path for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            Path to archive directory
        """
        return project_root / ".archive"

    @classmethod
    def is_initialized(cls, project_root: Path) -> bool:
        """
        Check if document lifecycle is initialized for a project.

        Args:
            project_root: Root directory of the project

        Returns:
            True if .gao-dev directory and documents.db exist
        """
        gao_dev_dir = cls.get_gao_dev_dir(project_root)
        db_path = cls.get_db_path(project_root)

        return gao_dev_dir.exists() and db_path.exists()
