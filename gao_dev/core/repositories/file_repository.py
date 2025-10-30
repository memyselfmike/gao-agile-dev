"""
File-based repository implementations.

Provides Repository Pattern abstractions over file I/O operations.
"""

from pathlib import Path
from typing import Optional, List, Any, Dict
import yaml
import json
import structlog

from ..interfaces.repository import IRepository

logger = structlog.get_logger()


class FileRepository(IRepository):
    """
    Base repository for file-based persistence.

    Provides common file I/O operations following Repository Pattern.
    Subclasses specify file format and validation logic.
    """

    def __init__(self, base_path: Path, file_extension: str = ".yaml"):
        """
        Initialize file repository.

        Args:
            base_path: Base directory for file storage
            file_extension: File extension (.yaml, .json, .md)
        """
        self.base_path = Path(base_path)
        self.file_extension = file_extension
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, entity_id: str, data: Any) -> None:
        """Save entity to file."""
        file_path = self._get_file_path(entity_id)

        try:
            if self.file_extension == ".yaml":
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False)
            elif self.file_extension == ".json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            else:
                # Plain text
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))

            logger.info("entity_saved", entity_id=entity_id, path=str(file_path))

        except Exception as e:
            logger.error("save_failed", entity_id=entity_id, error=str(e))
            raise

    def get(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID."""
        file_path = self._get_file_path(entity_id)

        if not file_path.exists():
            return None

        try:
            if self.file_extension == ".yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            elif self.file_extension == ".json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

        except Exception as e:
            logger.error("get_failed", entity_id=entity_id, error=str(e))
            return None

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        file_path = self._get_file_path(entity_id)

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            logger.info("entity_deleted", entity_id=entity_id)
            return True
        except Exception as e:
            logger.error("delete_failed", entity_id=entity_id, error=str(e))
            return False

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return self._get_file_path(entity_id).exists()

    def list_all(self) -> List[str]:
        """List all entity IDs."""
        if not self.base_path.exists():
            return []

        files = self.base_path.glob(f"*{self.file_extension}")
        return [f.stem for f in files]

    def update(self, entity_id: str, data: Any) -> bool:
        """Update existing entity."""
        if not self.exists(entity_id):
            return False

        self.save(entity_id, data)
        return True

    def find_by_id(self, entity_id: str) -> Optional[Any]:
        """Find entity by ID (alias for get)."""
        return self.get(entity_id)

    def find_all(self) -> List[Any]:
        """Find all entities."""
        entity_ids = self.list_all()
        entities = []
        for entity_id in entity_ids:
            entity = self.get(entity_id)
            if entity:
                entities.append(entity)
        return entities

    def _get_file_path(self, entity_id: str) -> Path:
        """Get file path for entity ID."""
        return self.base_path / f"{entity_id}{self.file_extension}"


class StateRepository(FileRepository):
    """
    Repository for project state files.

    Manages .gao-state.yaml files for project state persistence.
    """

    def __init__(self, base_path: Path):
        """
        Initialize state repository.

        Args:
            base_path: Base directory (usually project root or sandbox)
        """
        super().__init__(base_path, file_extension=".yaml")

    def get_project_state(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project state."""
        return self.get(f"{project_name}.gao-state")

    def save_project_state(self, project_name: str, state: Dict[str, Any]) -> None:
        """Save project state."""
        self.save(f"{project_name}.gao-state", state)

    def update_project_status(self, project_name: str, status: str) -> bool:
        """Update project status field."""
        state = self.get_project_state(project_name)
        if state is None:
            return False

        state["status"] = status
        self.save_project_state(project_name, state)
        return True
