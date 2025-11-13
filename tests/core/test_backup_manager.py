"""
Tests for BackupManager.

Story 36.8: BackupManager for Pre-Update Safety
"""

import json
import shutil
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from gao_dev.core.backup_manager import BackupManager, BackupMetadata


class TestBackupMetadata:
    """Test BackupMetadata dataclass."""

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = BackupMetadata(
            timestamp="2025-01-15T10:30:00",
            gaodev_version="0.1.0-beta.1",
            reason="pre_update_backup",
            file_count=10,
            files=["documents.db", "config.yaml"],
            backup_path="/project/.gao-dev-backups/backup_20250115_103000",
        )

        result = metadata.to_dict()

        assert result["timestamp"] == "2025-01-15T10:30:00"
        assert result["gaodev_version"] == "0.1.0-beta.1"
        assert result["reason"] == "pre_update_backup"
        assert result["file_count"] == 10
        assert result["files"] == ["documents.db", "config.yaml"]

    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "timestamp": "2025-01-15T10:30:00",
            "gaodev_version": "0.1.0-beta.1",
            "reason": "pre_update_backup",
            "file_count": 10,
            "files": ["documents.db", "config.yaml"],
            "backup_path": "/project/.gao-dev-backups/backup_20250115_103000",
        }

        metadata = BackupMetadata.from_dict(data)

        assert metadata.timestamp == "2025-01-15T10:30:00"
        assert metadata.gaodev_version == "0.1.0-beta.1"
        assert metadata.reason == "pre_update_backup"
        assert metadata.file_count == 10
        assert metadata.files == ["documents.db", "config.yaml"]


class TestBackupManager:
    """Test BackupManager."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project directory with .gao-dev."""
        project_path = tmp_path / "test_project"
        project_path.mkdir()

        gaodev_dir = project_path / ".gao-dev"
        gaodev_dir.mkdir()

        # Create some test files
        (gaodev_dir / "documents.db").write_text("fake db content")
        (gaodev_dir / "config.yaml").write_text("fake config")

        subdir = gaodev_dir / "metrics"
        subdir.mkdir()
        (subdir / "metrics.json").write_text('{"test": true}')

        return project_path

    @pytest.fixture
    def manager(self) -> BackupManager:
        """Create BackupManager instance."""
        return BackupManager()

    def test_initialization(self, manager: BackupManager):
        """Test BackupManager initializes correctly."""
        assert manager.MAX_BACKUPS == 5
        assert manager.logger is not None

    def test_create_backup_success(self, manager: BackupManager, temp_project: Path):
        """Test creating backup successfully."""
        backup_path = manager.create_backup(temp_project, reason="test_backup")

        # Verify backup directory created
        assert backup_path.exists()
        assert backup_path.is_dir()

        # Verify backup is in correct location
        assert backup_path.parent == temp_project / ".gao-dev-backups"

        # Verify backup name format
        assert backup_path.name.startswith("backup_")

        # Verify metadata file exists
        metadata_file = backup_path / "backup_metadata.json"
        assert metadata_file.exists()

        # Verify metadata content
        metadata_dict = json.loads(metadata_file.read_text())
        assert metadata_dict["reason"] == "test_backup"
        assert metadata_dict["file_count"] == 3  # 3 files in .gao-dev
        assert "documents.db" in metadata_dict["files"]
        assert "config.yaml" in metadata_dict["files"]
        # Normalize path separators for cross-platform
        files_normalized = [f.replace("\\", "/") for f in metadata_dict["files"]]
        assert "metrics/metrics.json" in files_normalized

        # Verify files were copied
        assert (backup_path / "documents.db").exists()
        assert (backup_path / "config.yaml").exists()
        assert (backup_path / "metrics" / "metrics.json").exists()

    def test_create_backup_missing_gaodev(self, manager: BackupManager, tmp_path: Path):
        """Test create_backup raises FileNotFoundError when .gao-dev missing."""
        project_path = tmp_path / "no_gaodev"
        project_path.mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            manager.create_backup(project_path)

        assert ".gao-dev directory not found" in str(exc_info.value)

    def test_create_backup_default_reason(self, manager: BackupManager, temp_project: Path):
        """Test create_backup uses default reason."""
        backup_path = manager.create_backup(temp_project)

        metadata_file = backup_path / "backup_metadata.json"
        metadata_dict = json.loads(metadata_file.read_text())

        assert metadata_dict["reason"] == "pre_update_backup"

    def test_restore_backup_success(self, manager: BackupManager, temp_project: Path):
        """Test restoring backup successfully."""
        # Create backup
        backup_path = manager.create_backup(temp_project, reason="test_backup")

        # Modify .gao-dev
        gaodev_dir = temp_project / ".gao-dev"
        (gaodev_dir / "documents.db").write_text("MODIFIED CONTENT")
        (gaodev_dir / "new_file.txt").write_text("NEW FILE")

        # Restore backup
        manager.restore_backup(temp_project, backup_path)

        # Verify original state restored
        assert (gaodev_dir / "documents.db").read_text() == "fake db content"
        assert (gaodev_dir / "config.yaml").read_text() == "fake config"
        assert (gaodev_dir / "metrics" / "metrics.json").read_text() == '{"test": true}'

        # Verify new file is gone
        assert not (gaodev_dir / "new_file.txt").exists()

    def test_restore_backup_missing_backup(self, manager: BackupManager, temp_project: Path):
        """Test restore_backup raises FileNotFoundError when backup missing."""
        fake_backup = temp_project / ".gao-dev-backups" / "backup_20250101_000000"

        with pytest.raises(FileNotFoundError) as exc_info:
            manager.restore_backup(temp_project, fake_backup)

        assert "Backup not found" in str(exc_info.value)

    def test_restore_backup_creates_gaodev_if_missing(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test restore_backup creates .gao-dev if it doesn't exist."""
        # Create backup
        backup_path = manager.create_backup(temp_project)

        # Remove .gao-dev
        gaodev_dir = temp_project / ".gao-dev"
        shutil.rmtree(gaodev_dir)

        # Restore backup
        manager.restore_backup(temp_project, backup_path)

        # Verify .gao-dev restored
        assert gaodev_dir.exists()
        assert (gaodev_dir / "documents.db").exists()

    def test_list_backups_empty(self, manager: BackupManager, temp_project: Path):
        """Test list_backups returns empty list when no backups exist."""
        backups = manager.list_backups(temp_project)

        assert backups == []

    def test_list_backups_success(self, manager: BackupManager, temp_project: Path):
        """Test list_backups returns all backups sorted by timestamp."""
        # Create multiple backups (microseconds ensure unique timestamps)
        backup1 = manager.create_backup(temp_project, reason="backup_1")
        backup2 = manager.create_backup(temp_project, reason="backup_2")
        backup3 = manager.create_backup(temp_project, reason="backup_3")

        backups = manager.list_backups(temp_project)

        # Should return 3 backups, newest first
        assert len(backups) == 3
        assert backups[0].reason == "backup_3"  # Newest
        assert backups[1].reason == "backup_2"
        assert backups[2].reason == "backup_1"  # Oldest

    def test_list_backups_skips_invalid_metadata(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test list_backups skips backups with invalid metadata."""
        # Create valid backup
        manager.create_backup(temp_project, reason="valid_backup")

        # Create backup with invalid metadata
        backup_root = temp_project / ".gao-dev-backups"
        invalid_backup = backup_root / "backup_invalid"
        invalid_backup.mkdir()
        (invalid_backup / "backup_metadata.json").write_text("INVALID JSON{")

        backups = manager.list_backups(temp_project)

        # Should only return valid backup
        assert len(backups) == 1
        assert backups[0].reason == "valid_backup"

    def test_list_backups_skips_directories_without_metadata(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test list_backups skips directories without metadata."""
        # Create valid backup
        manager.create_backup(temp_project, reason="valid_backup")

        # Create directory without metadata
        backup_root = temp_project / ".gao-dev-backups"
        legacy_backup = backup_root / "backup_legacy"
        legacy_backup.mkdir()

        backups = manager.list_backups(temp_project)

        # Should only return valid backup
        assert len(backups) == 1

    def test_get_latest_backup_none(self, manager: BackupManager, temp_project: Path):
        """Test get_latest_backup returns None when no backups exist."""
        latest = manager.get_latest_backup(temp_project)

        assert latest is None

    def test_get_latest_backup_success(self, manager: BackupManager, temp_project: Path):
        """Test get_latest_backup returns most recent backup."""
        manager.create_backup(temp_project, reason="backup_1")
        manager.create_backup(temp_project, reason="backup_2")
        manager.create_backup(temp_project, reason="backup_3")

        latest = manager.get_latest_backup(temp_project)

        assert latest is not None
        assert latest.reason == "backup_3"

    def test_delete_backup_success(self, manager: BackupManager, temp_project: Path):
        """Test deleting backup successfully."""
        backup_path = manager.create_backup(temp_project)

        assert backup_path.exists()

        manager.delete_backup(backup_path)

        assert not backup_path.exists()

    def test_delete_backup_missing(self, manager: BackupManager, temp_project: Path):
        """Test delete_backup raises FileNotFoundError when backup missing."""
        fake_backup = temp_project / ".gao-dev-backups" / "backup_20250101_000000"

        with pytest.raises(FileNotFoundError) as exc_info:
            manager.delete_backup(fake_backup)

        assert "Backup not found" in str(exc_info.value)

    def test_cleanup_old_backups(self, manager: BackupManager, temp_project: Path):
        """Test cleanup_old_backups keeps only MAX_BACKUPS."""
        # Create 7 backups (more than MAX_BACKUPS=5)
        backups = []
        for i in range(7):
            backup = manager.create_backup(temp_project, reason=f"backup_{i}")
            backups.append(backup)

        # List backups in directory
        backup_root = temp_project / ".gao-dev-backups"
        remaining = [d for d in backup_root.iterdir() if d.is_dir()]

        # Should only have 5 backups
        assert len(remaining) == 5

        # Oldest 2 should be deleted
        assert not backups[0].exists()
        assert not backups[1].exists()

        # Newest 5 should remain
        assert backups[2].exists()
        assert backups[3].exists()
        assert backups[4].exists()
        assert backups[5].exists()
        assert backups[6].exists()

    def test_backup_metadata_includes_version(self, manager: BackupManager, temp_project: Path):
        """Test backup metadata includes GAO-Dev version."""
        backup_path = manager.create_backup(temp_project)

        metadata_file = backup_path / "backup_metadata.json"
        metadata_dict = json.loads(metadata_file.read_text())

        assert "gaodev_version" in metadata_dict
        assert metadata_dict["gaodev_version"]  # Non-empty

    def test_backup_metadata_includes_timestamp(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test backup metadata includes ISO format timestamp."""
        backup_path = manager.create_backup(temp_project)

        metadata_file = backup_path / "backup_metadata.json"
        metadata_dict = json.loads(metadata_file.read_text())

        assert "timestamp" in metadata_dict

        # Verify timestamp is valid ISO format
        timestamp = datetime.fromisoformat(metadata_dict["timestamp"])
        assert isinstance(timestamp, datetime)

    def test_backup_preserves_directory_structure(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test backup preserves directory structure."""
        # Create nested structure
        gaodev_dir = temp_project / ".gao-dev"
        nested = gaodev_dir / "a" / "b" / "c"
        nested.mkdir(parents=True)
        (nested / "deep_file.txt").write_text("deep content")

        backup_path = manager.create_backup(temp_project)

        # Verify structure preserved
        assert (backup_path / "a" / "b" / "c" / "deep_file.txt").exists()
        assert (backup_path / "a" / "b" / "c" / "deep_file.txt").read_text() == "deep content"

    def test_create_backup_handles_copy_failure(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test create_backup handles copy failures gracefully."""
        # Mock shutil.copytree to raise exception
        with patch("gao_dev.core.backup_manager.shutil.copytree") as mock_copy:
            mock_copy.side_effect = OSError("Copy failed")

            with pytest.raises(OSError) as exc_info:
                manager.create_backup(temp_project)

            assert "Failed to create backup" in str(exc_info.value)

            # Verify partial backup cleaned up
            backup_root = temp_project / ".gao-dev-backups"
            backups = [d for d in backup_root.iterdir() if d.is_dir()]
            assert len(backups) == 0

    def test_restore_backup_handles_restore_failure(
        self, manager: BackupManager, temp_project: Path
    ):
        """Test restore_backup handles restore failures gracefully."""
        backup_path = manager.create_backup(temp_project)

        # Mock shutil.copytree to raise exception
        with patch("gao_dev.core.backup_manager.shutil.copytree") as mock_copy:
            mock_copy.side_effect = OSError("Restore failed")

            with pytest.raises(OSError) as exc_info:
                manager.restore_backup(temp_project, backup_path)

            assert "Failed to restore backup" in str(exc_info.value)

    def test_backup_path_format(self, manager: BackupManager, temp_project: Path):
        """Test backup directory follows naming convention."""
        backup_path = manager.create_backup(temp_project)

        # Verify format: backup_YYYYMMDD_HHMMSS_ffffff
        assert backup_path.name.startswith("backup_")

        # Extract timestamp part
        timestamp_str = backup_path.name.replace("backup_", "")

        # Verify format (should be YYYYMMDD_HHMMSS_ffffff - at least 22 chars)
        assert len(timestamp_str) >= 22
        assert timestamp_str[8] == "_"  # First underscore after YYYYMMDD
        assert timestamp_str[15] == "_"  # Second underscore after HHMMSS

    def test_multiple_backups_unique_names(self, manager: BackupManager, temp_project: Path):
        """Test multiple backups get unique names."""
        backup1 = manager.create_backup(temp_project)
        backup2 = manager.create_backup(temp_project)
        backup3 = manager.create_backup(temp_project)

        # All should have different names
        assert backup1.name != backup2.name
        assert backup2.name != backup3.name
        assert backup1.name != backup3.name
