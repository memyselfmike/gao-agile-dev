"""
Backup Manager for GAO-Dev

Manages backups of user project state before updates and migrations.

Story 36.8: BackupManager for Pre-Update Safety
"""

import json
import shutil
import structlog
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from gao_dev.__version__ import __version__ as CURRENT_VERSION


logger = structlog.get_logger(__name__)


@dataclass
class BackupMetadata:
    """
    Metadata about a backup.

    Attributes:
        timestamp: ISO format timestamp of backup creation
        gaodev_version: Version of GAO-Dev at time of backup
        reason: Why backup was created (e.g., "pre_update_backup", "pre_migration")
        file_count: Number of files in backup
        files: List of relative file paths in backup
        backup_path: Path to backup directory
    """

    timestamp: str
    gaodev_version: str
    reason: str
    file_count: int
    files: List[str]
    backup_path: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(**data)


class BackupManager:
    """
    Manage backups of user project state.

    Responsibilities:
    - Create backups of .gao-dev directory before updates/migrations
    - Restore from backups on failure
    - Clean up old backups (keep last N)
    - Store metadata about backups
    """

    # Maximum number of backups to keep
    MAX_BACKUPS: int = 5

    def __init__(self):
        """Initialize backup manager."""
        self.logger = logger.bind(component="BackupManager")

    def create_backup(
        self,
        project_path: Path,
        reason: str = "pre_update_backup"
    ) -> Path:
        """
        Create backup of .gao-dev directory.

        Args:
            project_path: Path to user project directory
            reason: Reason for backup (e.g., "pre_update_backup", "pre_migration")

        Returns:
            Path to backup directory

        Raises:
            FileNotFoundError: If .gao-dev directory doesn't exist
            OSError: If backup creation fails
        """
        gaodev_dir = project_path / ".gao-dev"

        if not gaodev_dir.exists():
            raise FileNotFoundError(f".gao-dev directory not found at {project_path}")

        # Create backup directory structure
        backup_root = project_path / ".gao-dev-backups"
        backup_root.mkdir(exist_ok=True)

        # Generate timestamp-based backup name (include microseconds for uniqueness)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_dir = backup_root / f"backup_{timestamp}"

        self.logger.info(
            "creating_backup",
            project_path=str(project_path),
            backup_path=str(backup_dir),
            reason=reason,
        )

        try:
            # Copy entire .gao-dev directory
            shutil.copytree(gaodev_dir, backup_dir)

            # Collect file list
            files = [
                str(p.relative_to(backup_dir))
                for p in backup_dir.rglob("*")
                if p.is_file()
            ]

            # Store metadata
            metadata = BackupMetadata(
                timestamp=datetime.now().isoformat(),
                gaodev_version=CURRENT_VERSION,
                reason=reason,
                file_count=len(files),
                files=files,
                backup_path=str(backup_dir),
            )

            metadata_file = backup_dir / "backup_metadata.json"
            metadata_file.write_text(json.dumps(metadata.to_dict(), indent=2))

            self.logger.info(
                "backup_created",
                backup_path=str(backup_dir),
                file_count=len(files),
            )

            # Clean up old backups
            self._cleanup_old_backups(backup_root)

            return backup_dir

        except Exception as e:
            self.logger.error(
                "backup_failed",
                error=str(e),
                backup_path=str(backup_dir),
            )
            # Clean up partial backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            raise OSError(f"Failed to create backup: {e}")

    def restore_backup(self, project_path: Path, backup_path: Path) -> None:
        """
        Restore from backup (rollback failed update).

        Args:
            project_path: Path to user project directory
            backup_path: Path to backup directory to restore from

        Raises:
            FileNotFoundError: If backup doesn't exist
            OSError: If restore fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found at {backup_path}")

        gaodev_dir = project_path / ".gao-dev"

        self.logger.info(
            "restoring_backup",
            project_path=str(project_path),
            backup_path=str(backup_path),
        )

        try:
            # Remove current .gao-dev directory if it exists
            if gaodev_dir.exists():
                shutil.rmtree(gaodev_dir)

            # Restore from backup
            shutil.copytree(backup_path, gaodev_dir)

            self.logger.info(
                "backup_restored",
                project_path=str(project_path),
                backup_path=str(backup_path),
            )

        except Exception as e:
            self.logger.error(
                "restore_failed",
                error=str(e),
                backup_path=str(backup_path),
            )
            raise OSError(f"Failed to restore backup: {e}")

    def list_backups(self, project_path: Path) -> List[BackupMetadata]:
        """
        List all backups for a project.

        Args:
            project_path: Path to user project directory

        Returns:
            List of BackupMetadata objects, sorted by timestamp (newest first)
        """
        backup_root = project_path / ".gao-dev-backups"

        if not backup_root.exists():
            return []

        backups = []

        for backup_dir in backup_root.iterdir():
            if not backup_dir.is_dir():
                continue

            metadata_file = backup_dir / "backup_metadata.json"
            if not metadata_file.exists():
                # Legacy backup without metadata
                continue

            try:
                metadata_dict = json.loads(metadata_file.read_text())
                metadata = BackupMetadata.from_dict(metadata_dict)
                backups.append(metadata)
            except Exception as e:
                self.logger.warning(
                    "invalid_backup_metadata",
                    backup_path=str(backup_dir),
                    error=str(e),
                )
                continue

        # Sort by timestamp (newest first)
        backups.sort(key=lambda b: b.timestamp, reverse=True)

        return backups

    def get_latest_backup(self, project_path: Path) -> Optional[BackupMetadata]:
        """
        Get the latest backup for a project.

        Args:
            project_path: Path to user project directory

        Returns:
            BackupMetadata of latest backup, or None if no backups exist
        """
        backups = self.list_backups(project_path)
        return backups[0] if backups else None

    def delete_backup(self, backup_path: Path) -> None:
        """
        Delete a specific backup.

        Args:
            backup_path: Path to backup directory to delete

        Raises:
            FileNotFoundError: If backup doesn't exist
            OSError: If deletion fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found at {backup_path}")

        self.logger.info("deleting_backup", backup_path=str(backup_path))

        try:
            shutil.rmtree(backup_path)
            self.logger.info("backup_deleted", backup_path=str(backup_path))

        except Exception as e:
            self.logger.error(
                "delete_failed",
                error=str(e),
                backup_path=str(backup_path),
            )
            raise OSError(f"Failed to delete backup: {e}")

    def _cleanup_old_backups(self, backup_root: Path) -> None:
        """
        Clean up old backups, keeping only the last MAX_BACKUPS.

        Args:
            backup_root: Path to backups directory (.gao-dev-backups)
        """
        # Get all backup directories sorted by name (which includes timestamp)
        backups = sorted(
            [d for d in backup_root.iterdir() if d.is_dir()],
            key=lambda d: d.name,
            reverse=True,  # Newest first
        )

        # Delete old backups beyond MAX_BACKUPS
        if len(backups) > self.MAX_BACKUPS:
            old_backups = backups[self.MAX_BACKUPS:]
            self.logger.info(
                "cleaning_old_backups",
                count=len(old_backups),
                max_backups=self.MAX_BACKUPS,
            )

            for backup_dir in old_backups:
                try:
                    shutil.rmtree(backup_dir)
                    self.logger.debug("old_backup_deleted", backup_path=str(backup_dir))
                except Exception as e:
                    self.logger.warning(
                        "cleanup_failed",
                        backup_path=str(backup_dir),
                        error=str(e),
                    )
