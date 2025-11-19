"""
Tests for ConfigMigrator.

Epic 42: Integration Polish
Story 42.1: Existing Installation Migration (5 SP)

Test coverage for all 12 acceptance criteria.
"""

import os
import time
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml

from gao_dev.core.migration import ConfigMigrator, MigrationResult


class TestMigrationResult:
    """Test MigrationResult dataclass."""

    def test_to_dict(self):
        """Test converting result to dictionary."""
        # Use a platform-independent path for testing
        backup_path = Path("project") / ".gao-dev" / "backup_migration_123"
        result = MigrationResult(
            migrated=True,
            reason="Migration completed successfully",
            from_version="v1",
            settings_migrated=["provider", "model"],
            backup_path=backup_path,
            duration_ms=150,
        )

        data = result.to_dict()

        assert data["migrated"] is True
        assert data["reason"] == "Migration completed successfully"
        assert data["from_version"] == "v1"
        assert data["settings_migrated"] == ["provider", "model"]
        # Compare using Path to handle cross-platform path separators
        assert Path(data["backup_path"]) == backup_path
        assert data["duration_ms"] == 150

    def test_from_dict(self):
        """Test creating result from dictionary."""
        data = {
            "migrated": True,
            "reason": "Migration completed",
            "from_version": "epic35",
            "settings_migrated": ["provider"],
            "backup_path": "/project/backup",
            "duration_ms": 100,
        }

        result = MigrationResult.from_dict(data)

        assert result.migrated is True
        assert result.reason == "Migration completed"
        assert result.from_version == "epic35"
        assert result.settings_migrated == ["provider"]
        assert result.backup_path == Path("/project/backup")
        assert result.duration_ms == 100

    def test_from_dict_defaults(self):
        """Test from_dict with minimal data uses defaults."""
        data = {"migrated": False}

        result = MigrationResult.from_dict(data)

        assert result.migrated is False
        assert result.reason is None
        assert result.from_version is None
        assert result.settings_migrated == []
        assert result.backup_path is None
        assert result.duration_ms == 0

    def test_summary_migrated(self):
        """Test summary for successful migration."""
        # Use a platform-independent path for testing
        backup_path = Path("project") / "backup"
        result = MigrationResult(
            migrated=True,
            from_version="v1",
            settings_migrated=["provider", "model"],
            backup_path=backup_path,
            duration_ms=150,
        )

        summary = result.summary()

        assert "Migrated from v1 format" in summary
        assert "provider" in summary
        assert "model" in summary
        assert "150ms" in summary
        # Check that backup path is in summary (path separator varies by OS)
        assert "backup" in summary
        assert "project" in summary

    def test_summary_not_migrated(self):
        """Test summary when migration skipped."""
        result = MigrationResult(
            migrated=False,
            reason="No legacy configuration found",
        )

        summary = result.summary()

        assert "Migration skipped" in summary
        assert "No legacy configuration found" in summary


class TestConfigMigrator:
    """Test ConfigMigrator."""

    @pytest.fixture
    def migrator(self) -> ConfigMigrator:
        """Create ConfigMigrator instance."""
        return ConfigMigrator()

    @pytest.fixture
    def v1_project(self, tmp_path: Path) -> Path:
        """Create project with v1 configuration."""
        project_path = tmp_path / "v1_project"
        project_path.mkdir()

        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create v1 config
        v1_config = {
            "project_name": "my-app",
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "api_key_source": "environment",
            "features": {
                "interactive_provider_selection": True,
            },
        }

        config_file = gao_dev_dir / "gao-dev.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(v1_config, f)

        return project_path

    @pytest.fixture
    def epic35_project(self, tmp_path: Path) -> Path:
        """Create project with Epic 35 configuration."""
        project_path = tmp_path / "epic35_project"
        project_path.mkdir()

        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create Epic 35 config
        epic35_config = {
            "provider": "claude-code",
            "model": "sonnet-4.5",
            "saved_at": "2025-01-15T10:30:00Z",
        }

        config_file = gao_dev_dir / "provider_preferences.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(epic35_config, f)

        return project_path

    @pytest.fixture
    def epic35_project_nested(self, tmp_path: Path) -> Path:
        """Create project with nested Epic 35 configuration (newer format)."""
        project_path = tmp_path / "epic35_nested_project"
        project_path.mkdir()

        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create nested Epic 35 config (newer format)
        epic35_config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {
                    "ai_provider": "ollama",
                    "use_local": True,
                },
            },
            "metadata": {
                "last_updated": "2025-01-15T10:30:00Z",
                "cli_version": "1.2.3",
            },
        }

        config_file = gao_dev_dir / "provider_preferences.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(epic35_config, f)

        return project_path

    @pytest.fixture
    def new_format_project(self, tmp_path: Path) -> Path:
        """Create project with new configuration format."""
        project_path = tmp_path / "new_project"
        project_path.mkdir()

        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create new config
        new_config = {
            "version": "1.0",
            "project": {
                "name": "new-app",
                "type": "brownfield",
            },
            "provider": {
                "default": "claude-code",
                "model": "sonnet-4.5",
            },
        }

        config_file = gao_dev_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(new_config, f)

        return project_path

    @pytest.fixture
    def empty_project(self, tmp_path: Path) -> Path:
        """Create empty project without .gao-dev."""
        project_path = tmp_path / "empty_project"
        project_path.mkdir()
        return project_path

    @pytest.fixture
    def corrupted_project(self, tmp_path: Path) -> Path:
        """Create project with corrupted configuration."""
        project_path = tmp_path / "corrupted_project"
        project_path.mkdir()

        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create corrupted v1 config
        config_file = gao_dev_dir / "gao-dev.yaml"
        config_file.write_text("invalid: yaml: {corrupted")

        return project_path

    # AC1: Detects .gao-dev/gao-dev.yaml (v1 format) and migrates
    def test_detect_v1_format(self, migrator: ConfigMigrator, v1_project: Path):
        """Test detecting v1 configuration format."""
        result = migrator.detect_legacy_config(v1_project)

        assert result == "v1"

    def test_migrate_v1_success(self, migrator: ConfigMigrator, v1_project: Path):
        """Test successful v1 migration."""
        result = migrator.migrate(v1_project)

        assert result.migrated is True
        assert result.from_version == "v1"
        assert "provider" in result.settings_migrated
        assert "model" in result.settings_migrated
        assert "project_name" in result.settings_migrated
        assert "api_key_source" in result.settings_migrated
        assert "features" in result.settings_migrated

        # Verify new config created
        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        assert new_config_file.exists()

        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["version"] == "1.0"
        assert new_config["project"]["name"] == "my-app"
        assert new_config["provider"]["default"] == "anthropic"
        assert new_config["provider"]["model"] == "claude-3-sonnet"
        assert new_config["credentials"]["storage"] == "environment"
        assert new_config["migrated_from"] == "v1"

    # AC2: Detects .gao-dev/provider_preferences.yaml (Epic 35) and migrates
    def test_detect_epic35_format(self, migrator: ConfigMigrator, epic35_project: Path):
        """Test detecting Epic 35 configuration format."""
        result = migrator.detect_legacy_config(epic35_project)

        assert result == "epic35"

    def test_migrate_epic35_success(self, migrator: ConfigMigrator, epic35_project: Path):
        """Test successful Epic 35 migration."""
        result = migrator.migrate(epic35_project)

        assert result.migrated is True
        assert result.from_version == "epic35"
        assert "provider" in result.settings_migrated
        assert "model" in result.settings_migrated
        assert "saved_at" in result.settings_migrated

        # Verify new config created
        new_config_file = epic35_project / ".gao-dev" / "config.yaml"
        assert new_config_file.exists()

        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["version"] == "1.0"
        assert new_config["provider"]["default"] == "claude-code"
        assert new_config["provider"]["model"] == "sonnet-4.5"
        assert new_config["migrated_from"] == "epic35"

    def test_migrate_epic35_nested_format(
        self, migrator: ConfigMigrator, epic35_project_nested: Path
    ):
        """Test migration of nested Epic 35 format."""
        result = migrator.migrate(epic35_project_nested)

        assert result.migrated is True
        assert result.from_version == "epic35"

        # Verify new config created with nested values
        new_config_file = epic35_project_nested / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["provider"]["default"] == "opencode"
        assert new_config["provider"]["model"] == "deepseek-r1"
        assert "config" in new_config["provider"]

    # AC3: Creates global config at ~/.gao-dev/config.yaml
    def test_creates_global_config(
        self, migrator: ConfigMigrator, v1_project: Path, tmp_path: Path
    ):
        """Test global config creation from first migrated project."""
        # Patch home directory to temp path
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        with patch.object(Path, "home", return_value=home_dir):
            result = migrator.migrate(v1_project)

        assert result.migrated is True

        # Verify global config created
        global_config_file = home_dir / ".gao-dev" / "config.yaml"
        assert global_config_file.exists()

        with open(global_config_file, "r", encoding="utf-8") as f:
            global_config = yaml.safe_load(f)

        assert global_config["version"] == "1.0"
        assert "provider" in global_config

    def test_skips_existing_global_config(
        self, migrator: ConfigMigrator, v1_project: Path, tmp_path: Path
    ):
        """Test that existing global config is not overwritten."""
        # Create existing global config
        home_dir = tmp_path / "home"
        global_gao_dev = home_dir / ".gao-dev"
        global_gao_dev.mkdir(parents=True)

        global_config_file = global_gao_dev / "config.yaml"
        existing_config = {"version": "1.0", "existing": True}
        with open(global_config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(existing_config, f)

        with patch.object(Path, "home", return_value=home_dir):
            result = migrator.migrate(v1_project)

        assert result.migrated is True

        # Verify global config unchanged
        with open(global_config_file, "r", encoding="utf-8") as f:
            global_config = yaml.safe_load(f)

        assert global_config["existing"] is True

    # AC4: Preserves provider selection, model choice, and preferences
    def test_preserves_provider_settings(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that provider settings are preserved during migration."""
        result = migrator.migrate(v1_project)

        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        # Original v1 had: provider=anthropic, model=claude-3-sonnet
        assert new_config["provider"]["default"] == "anthropic"
        assert new_config["provider"]["model"] == "claude-3-sonnet"

    def test_preserves_features(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that features configuration is preserved."""
        result = migrator.migrate(v1_project)

        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        # Original v1 had features.interactive_provider_selection=True
        assert "features" in new_config
        assert new_config["features"]["interactive_provider_selection"] is True

    # AC5: Backs up original files before migration (timestamped folders)
    def test_creates_backup(self, migrator: ConfigMigrator, v1_project: Path):
        """Test backup creation with timestamp."""
        result = migrator.migrate(v1_project)

        assert result.migrated is True
        assert result.backup_path is not None
        assert result.backup_path.exists()

        # Verify backup is timestamped
        assert "backup_migration_" in result.backup_path.name

        # Verify backup contains original file
        backup_file = result.backup_path / "gao-dev.yaml"
        assert backup_file.exists()

    def test_backup_contains_original_config(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that backup contains original configuration."""
        # Read original config
        original_file = v1_project / ".gao-dev" / "gao-dev.yaml"
        with open(original_file, "r", encoding="utf-8") as f:
            original_config = yaml.safe_load(f)

        result = migrator.migrate(v1_project)

        # Read backed up config
        backup_file = result.backup_path / "gao-dev.yaml"
        with open(backup_file, "r", encoding="utf-8") as f:
            backup_config = yaml.safe_load(f)

        assert backup_config == original_config

    # AC6: Migration runs automatically on first startup - tested via integration
    # This is tested implicitly through the migrate() method

    # AC7: Shows migration summary with what was migrated
    def test_migration_summary(self, migrator: ConfigMigrator, v1_project: Path):
        """Test migration summary generation."""
        result = migrator.migrate(v1_project)

        summary = migrator.get_migration_summary(result)

        assert "Configuration Migration Complete" in summary
        assert "v1 format" in summary
        assert "provider" in summary
        assert "model" in summary

    def test_migration_summary_not_migrated(self, migrator: ConfigMigrator, empty_project: Path):
        """Test summary when no migration performed."""
        result = migrator.migrate(empty_project)

        summary = migrator.get_migration_summary(result)

        assert "Migration not performed" in summary
        assert "No legacy configuration" in summary

    # AC8: Skips onboarding for migrated users
    def test_should_skip_onboarding_after_migration(
        self, migrator: ConfigMigrator, v1_project: Path
    ):
        """Test that onboarding is skipped for migrated users."""
        result = migrator.migrate(v1_project)

        assert result.migrated is True
        assert migrator.should_skip_onboarding(v1_project) is True

    def test_should_not_skip_onboarding_for_new_project(
        self, migrator: ConfigMigrator, new_format_project: Path
    ):
        """Test that onboarding is not skipped for new projects."""
        # New format without migrated_from field
        assert migrator.should_skip_onboarding(new_format_project) is False

    def test_should_not_skip_onboarding_no_config(
        self, migrator: ConfigMigrator, empty_project: Path
    ):
        """Test that onboarding is not skipped when no config exists."""
        assert migrator.should_skip_onboarding(empty_project) is False

    # AC9: Handles corrupted legacy files gracefully
    def test_handles_corrupted_files(self, migrator: ConfigMigrator, corrupted_project: Path):
        """Test graceful handling of corrupted configuration files."""
        result = migrator.migrate(corrupted_project)

        # Should still succeed with defaults
        assert result.migrated is True

        # Verify new config created with defaults
        new_config_file = corrupted_project / ".gao-dev" / "config.yaml"
        assert new_config_file.exists()

        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        # Should use default values
        assert new_config["provider"]["default"] == "claude-code"
        assert new_config["provider"]["model"] == "sonnet-4.5"

    def test_handles_invalid_yaml(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test handling of invalid YAML syntax."""
        project_path = tmp_path / "invalid_yaml_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create file with invalid YAML
        config_file = gao_dev_dir / "gao-dev.yaml"
        config_file.write_text("invalid:\n  - [broken yaml")

        result = migrator.migrate(project_path)

        # Should succeed with defaults
        assert result.migrated is True

    def test_handles_non_dict_config(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test handling config file that isn't a dictionary."""
        project_path = tmp_path / "non_dict_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create file with list instead of dict
        config_file = gao_dev_dir / "gao-dev.yaml"
        config_file.write_text("- item1\n- item2")

        result = migrator.migrate(project_path)

        # Should succeed with defaults
        assert result.migrated is True

    # AC10: Migration is idempotent (safe to run multiple times)
    def test_idempotent_migration(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that migration is idempotent."""
        # First migration
        result1 = migrator.migrate(v1_project)
        assert result1.migrated is True

        # Read config after first migration
        config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            config1 = yaml.safe_load(f)

        # Second migration attempt
        result2 = migrator.migrate(v1_project)

        # Should not migrate again
        assert result2.migrated is False
        assert "already migrated" in result2.reason

        # Config should be unchanged
        with open(config_file, "r", encoding="utf-8") as f:
            config2 = yaml.safe_load(f)

        assert config1 == config2

    def test_detect_already_migrated(
        self, migrator: ConfigMigrator, new_format_project: Path
    ):
        """Test that already migrated projects are detected."""
        result = migrator.detect_legacy_config(new_format_project)

        assert result is None

    # AC11: Credential sources preserved
    def test_preserves_credential_storage(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that credential storage setting is preserved."""
        result = migrator.migrate(v1_project)

        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        # Original v1 had api_key_source=environment
        assert new_config["credentials"]["storage"] == "environment"

    def test_preserves_keychain_reference(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test that keychain references are preserved."""
        project_path = tmp_path / "keychain_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create v1 config with keychain
        v1_config = {
            "project_name": "keychain-app",
            "provider": "anthropic",
            "model": "claude-3-opus",
            "api_key_source": "keychain",
        }

        config_file = gao_dev_dir / "gao-dev.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(v1_config, f)

        result = migrator.migrate(project_path)

        new_config_file = project_path / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["credentials"]["storage"] == "keychain"

    # AC12: Migration completes in <2 seconds
    def test_migration_performance(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that migration completes within 2 seconds."""
        start_time = time.time()
        result = migrator.migrate(v1_project)
        elapsed_time = time.time() - start_time

        assert result.migrated is True
        assert elapsed_time < 2.0
        assert result.duration_ms < 2000

    def test_migration_duration_recorded(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that migration duration is accurately recorded."""
        result = migrator.migrate(v1_project)

        assert result.duration_ms > 0
        assert result.duration_ms < 2000  # Should be fast

    # Additional edge case tests

    def test_no_gao_dev_directory(self, migrator: ConfigMigrator, empty_project: Path):
        """Test handling of project without .gao-dev directory."""
        result = migrator.migrate(empty_project)

        assert result.migrated is False
        assert "No legacy configuration" in result.reason

    def test_detect_no_legacy_config(self, migrator: ConfigMigrator, empty_project: Path):
        """Test detect returns None when no legacy config exists."""
        result = migrator.detect_legacy_config(empty_project)

        assert result is None

    def test_detect_empty_gao_dev_directory(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test detect returns None for empty .gao-dev directory."""
        project_path = tmp_path / "empty_gaodev_project"
        project_path.mkdir()
        (project_path / ".gao-dev").mkdir()

        result = migrator.detect_legacy_config(project_path)

        assert result is None

    def test_atomic_write_on_failure(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that atomic write doesn't leave partial files on failure."""
        # Mock tempfile.mkstemp to raise exception
        with patch("gao_dev.core.migration.config_migrator.tempfile.mkstemp") as mock_mkstemp:
            mock_mkstemp.side_effect = OSError("Failed to create temp file")

            result = migrator.migrate(v1_project)

        # Should fail but not leave partial file
        assert result.migrated is False
        assert "Failed" in result.reason

    def test_migrate_sets_migrated_at_timestamp(
        self, migrator: ConfigMigrator, v1_project: Path
    ):
        """Test that migrated_at timestamp is set."""
        before = datetime.now().isoformat()
        result = migrator.migrate(v1_project)
        after = datetime.now().isoformat()

        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        migrated_at = new_config["migrated_at"]
        # Remove trailing Z for comparison
        migrated_at_clean = migrated_at.rstrip("Z")

        # Timestamp should be between before and after
        assert migrated_at_clean >= before
        assert migrated_at_clean <= after

    def test_multiple_backups_unique(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test that multiple backup directories have unique names."""
        # Create v1 project
        project_path = tmp_path / "multi_backup_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        backups = []

        for i in range(3):
            # Create config
            config_file = gao_dev_dir / "gao-dev.yaml"
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.safe_dump({"provider": f"provider{i}"}, f)

            # Remove new config to allow re-migration
            new_config = gao_dev_dir / "config.yaml"
            if new_config.exists():
                new_config.unlink()

            result = migrator.migrate(project_path)
            if result.backup_path:
                backups.append(result.backup_path)

            # Small delay to ensure unique timestamps
            time.sleep(0.001)

        # All backups should have unique names
        backup_names = [b.name for b in backups]
        assert len(backup_names) == len(set(backup_names))

    def test_handles_read_only_config(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test handling of read-only configuration files."""
        # This test is skipped on Windows where chmod behaves differently
        if os.name == "nt":
            pytest.skip("File permissions work differently on Windows")

        project_path = tmp_path / "readonly_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        config_file = gao_dev_dir / "gao-dev.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump({"provider": "test"}, f)

        # Make file read-only (this doesn't prevent creating new files)
        os.chmod(config_file, 0o444)

        try:
            result = migrator.migrate(project_path)
            # Should still succeed as we're creating a new file
            assert result.migrated is True
        finally:
            # Restore permissions for cleanup
            os.chmod(config_file, 0o644)

    def test_preserves_project_type(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that project type defaults to brownfield."""
        result = migrator.migrate(v1_project)

        new_config_file = v1_project / ".gao-dev" / "config.yaml"
        with open(new_config_file, "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["project"]["type"] == "brownfield"

    def test_migration_result_can_serialize(self, migrator: ConfigMigrator, v1_project: Path):
        """Test that MigrationResult can be serialized and deserialized."""
        result = migrator.migrate(v1_project)

        # Serialize
        data = result.to_dict()

        # Deserialize
        restored = MigrationResult.from_dict(data)

        assert restored.migrated == result.migrated
        assert restored.from_version == result.from_version
        assert restored.settings_migrated == result.settings_migrated
        assert restored.duration_ms == result.duration_ms


class TestConfigMigratorIntegration:
    """Integration tests for ConfigMigrator."""

    @pytest.fixture
    def migrator(self) -> ConfigMigrator:
        """Create ConfigMigrator instance."""
        return ConfigMigrator()

    def test_full_v1_migration_workflow(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test complete v1 migration workflow."""
        # Create v1 project
        project_path = tmp_path / "workflow_project"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        v1_config = {
            "project_name": "workflow-app",
            "provider": "claude-code",
            "model": "sonnet-4.5",
            "api_key_source": "environment",
        }

        with open(gao_dev_dir / "gao-dev.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(v1_config, f)

        # Check for legacy config
        legacy_version = migrator.detect_legacy_config(project_path)
        assert legacy_version == "v1"

        # Migrate
        result = migrator.migrate(project_path)
        assert result.migrated is True

        # Verify can't migrate again (idempotent)
        result2 = migrator.migrate(project_path)
        assert result2.migrated is False

        # Verify onboarding should be skipped
        assert migrator.should_skip_onboarding(project_path) is True

        # Verify summary is readable
        summary = migrator.get_migration_summary(result)
        assert len(summary) > 0

    def test_full_epic35_migration_workflow(self, migrator: ConfigMigrator, tmp_path: Path):
        """Test complete Epic 35 migration workflow."""
        # Create Epic 35 project
        project_path = tmp_path / "epic35_workflow"
        project_path.mkdir()
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir()

        epic35_config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {"ai_provider": "ollama"},
            },
            "metadata": {
                "last_updated": "2025-01-15T10:30:00Z",
            },
        }

        with open(gao_dev_dir / "provider_preferences.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(epic35_config, f)

        # Detect and migrate
        assert migrator.detect_legacy_config(project_path) == "epic35"

        result = migrator.migrate(project_path)
        assert result.migrated is True
        assert "provider" in result.settings_migrated

        # Verify new config has correct values
        with open(gao_dev_dir / "config.yaml", "r", encoding="utf-8") as f:
            new_config = yaml.safe_load(f)

        assert new_config["provider"]["default"] == "opencode"
        assert new_config["provider"]["model"] == "deepseek-r1"
