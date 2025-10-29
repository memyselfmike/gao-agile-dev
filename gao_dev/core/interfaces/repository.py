"""
Repository interfaces for data access layer.

This module defines the repository pattern interfaces for GAO-Dev,
enabling separation of business logic from data persistence concerns.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any

# Generic type for repository entities
T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Generic repository interface for data access.

    This interface defines the contract for all repositories in GAO-Dev.
    Repositories abstract data access and persistence, allowing business
    logic to remain independent of storage implementation.

    Type Parameters:
        T: The entity type this repository manages

    Example:
        ```python
        class StoryRepository(IRepository[Story]):
            async def find_by_id(self, id: str) -> Optional[Story]:
                # Implementation
                pass
        ```
    """

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find an entity by its unique identifier.

        Args:
            id: Unique identifier for the entity

        Returns:
            The entity if found, None otherwise

        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """
        Retrieve all entities.

        Returns:
            List of all entities (may be empty)

        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def save(self, entity: T) -> None:
        """
        Save an entity (create or update).

        Args:
            entity: Entity to save

        Raises:
            RepositoryError: If save operation fails
            ValidationError: If entity validation fails
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        """
        Delete an entity by its identifier.

        Args:
            id: Unique identifier of entity to delete

        Raises:
            RepositoryError: If delete operation fails
            EntityNotFoundError: If entity doesn't exist
        """
        pass


class IStoryRepository(IRepository['Story']):  # type: ignore
    """
    Repository interface for user story data access.

    Extends the generic repository with story-specific query methods.

    Example:
        ```python
        story_repo = FileSystemStoryRepository(project_root)
        stories = await story_repo.find_by_epic(1)
        backlog = await story_repo.find_by_status(StoryStatus.BACKLOG)
        ```
    """

    @abstractmethod
    async def find_by_epic(self, epic: int) -> List['Story']:  # type: ignore
        """
        Find all stories in a specific epic.

        Args:
            epic: Epic number (e.g., 1, 2, 3)

        Returns:
            List of stories in the epic (may be empty)

        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: 'StoryStatus') -> List['Story']:  # type: ignore
        """
        Find all stories with a specific status.

        Args:
            status: Story status to filter by

        Returns:
            List of stories with the status (may be empty)

        Raises:
            RepositoryError: If data access fails
        """
        pass


class IProjectRepository(IRepository['Project']):  # type: ignore
    """
    Repository interface for sandbox project data access.

    Extends the generic repository with project-specific query methods.

    Example:
        ```python
        project_repo = FileSystemProjectRepository(sandbox_root)
        active = await project_repo.find_active()
        tagged = await project_repo.find_by_tags(["benchmark", "todo"])
        ```
    """

    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List['Project']:  # type: ignore
        """
        Find all projects matching any of the given tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of projects with at least one matching tag

        Raises:
            RepositoryError: If data access fails
        """
        pass

    @abstractmethod
    async def find_active(self) -> List['Project']:  # type: ignore
        """
        Find all active (not deleted/archived) projects.

        Returns:
            List of active projects

        Raises:
            RepositoryError: If data access fails
        """
        pass
