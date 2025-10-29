"""Mock repository implementation for testing."""

from typing import Generic, TypeVar, Optional, List, Dict
from gao_dev.core.interfaces.repository import IRepository

T = TypeVar('T')


class MockRepository(IRepository[T], Generic[T]):
    """
    Mock repository for testing.

    Provides in-memory storage for testing repository implementations.
    """

    def __init__(self):
        self._store: Dict[str, T] = {}

    async def find_by_id(self, id: str) -> Optional[T]:
        """Find entity by ID."""
        return self._store.get(id)

    async def find_all(self) -> List[T]:
        """Find all entities."""
        return list(self._store.values())

    async def save(self, entity: T) -> None:
        """Save entity (requires entity to have 'id' attribute)."""
        if hasattr(entity, 'id'):
            self._store[str(entity.id)] = entity
        else:
            raise ValueError("Entity must have 'id' attribute")

    async def delete(self, id: str) -> None:
        """Delete entity by ID."""
        self._store.pop(id, None)

    def clear(self) -> None:
        """Clear all entities (test utility)."""
        self._store.clear()

    def count(self) -> int:
        """Count entities (test utility)."""
        return len(self._store)
