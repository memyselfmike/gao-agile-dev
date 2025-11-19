"""
Configuration migrator for legacy GAO-Dev installations.

This module provides the ConfigMigrator class for detecting and migrating
legacy configuration formats to the new unified format.

Epic 42: Integration Polish
Story 42.1: Existing Installation Migration (5 SP)

Supported legacy formats:
- v1: .gao-dev/gao-dev.yaml
- epic35: .gao-dev/provider_preferences.yaml

Target format:
- Project: .gao-dev/config.yaml
- Global: ~/.gao-dev/config.yaml
"""

import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
import yaml

from gao_dev.core.migration.models import MigrationResult

logger = structlog.get_logger()


class ConfigMigrator:
    """
    Migrate legacy GAO-Dev configurations to new format.

    Detects v1 (gao-dev.yaml) and Epic 35 (provider_preferences.yaml)
    formats and converts them to the new unified config.yaml format.

    Features:
    - Automatic format detection
    - Timestamped backups before migration
    - Global config creation from first project
    - Idempotent operation (safe to run multiple times)
    - Graceful handling of corrupted files

    Example:
        ```python
        migrator = ConfigMigrator()

        # Check for legacy config
        if migrator.detect_legacy_config(project_path):
            result = migrator.migrate(project_path)
            if result.migrated:
                print(f"Migrated from {result.from_version}")
        ```
    """

    # Legacy format file names
    V1_CONFIG_FILE = "gao-dev.yaml"
    EPIC35_CONFIG_FILE = "provider_preferences.yaml"

    # New format file name
    NEW_CONFIG_FILE = "config.yaml"

    # Version identifiers
    VERSION_V1 = "v1"
    VERSION_EPIC35 = "epic35"
    VERSION_NEW = "1.0"

    # Backup directory name pattern
    BACKUP_DIR_PATTERN = "backup_migration_{timestamp}"

    def __init__(self):
        """Initialize ConfigMigrator."""
        self.logger = logger.bind(component="ConfigMigrator")

    def detect_legacy_config(self, project_path: Path) -> Optional[str]:
        """
        Detect legacy configuration format in project.

        Checks for v1 (gao-dev.yaml) or Epic 35 (provider_preferences.yaml)
        configuration files in the .gao-dev directory.

        Args:
            project_path: Path to project directory

        Returns:
            Version string (v1, epic35) if legacy config found, None otherwise
        """
        gao_dev_dir = project_path / ".gao-dev"

        if not gao_dev_dir.exists():
            self.logger.debug(
                "No .gao-dev directory found",
                project_path=str(project_path),
            )
            return None

        # Check for new format first (already migrated)
        new_config = gao_dev_dir / self.NEW_CONFIG_FILE
        if new_config.exists():
            self.logger.debug(
                "New config format already exists",
                project_path=str(project_path),
            )
            return None

        # Check for v1 format
        v1_config = gao_dev_dir / self.V1_CONFIG_FILE
        if v1_config.exists():
            self.logger.info(
                "Detected v1 configuration format",
                project_path=str(project_path),
                config_file=str(v1_config),
            )
            return self.VERSION_V1

        # Check for Epic 35 format
        epic35_config = gao_dev_dir / self.EPIC35_CONFIG_FILE
        if epic35_config.exists():
            self.logger.info(
                "Detected Epic 35 configuration format",
                project_path=str(project_path),
                config_file=str(epic35_config),
            )
            return self.VERSION_EPIC35

        self.logger.debug(
            "No legacy configuration found",
            project_path=str(project_path),
        )
        return None

    def migrate(self, project_path: Path) -> MigrationResult:
        """
        Migrate legacy configuration to new format.

        Performs the following steps:
        1. Detect legacy format
        2. Create timestamped backup
        3. Load legacy configuration
        4. Convert to new format
        5. Write new configuration
        6. Create/update global configuration

        Args:
            project_path: Path to project directory

        Returns:
            MigrationResult with details of the migration
        """
        start_time = time.time()

        # Detect legacy format
        legacy_version = self.detect_legacy_config(project_path)

        if legacy_version is None:
            duration_ms = int((time.time() - start_time) * 1000)
            return MigrationResult(
                migrated=False,
                reason="No legacy configuration found or already migrated",
                duration_ms=duration_ms,
            )

        self.logger.info(
            "Starting migration",
            project_path=str(project_path),
            from_version=legacy_version,
        )

        try:
            # Create backup
            backup_path = self._backup_files(project_path)

            # Load legacy configuration
            if legacy_version == self.VERSION_V1:
                legacy_config = self._load_v1_config(project_path)
            else:  # epic35
                legacy_config = self._load_epic35_config(project_path)

            if legacy_config is None:
                # Corrupted file - use defaults
                self.logger.warning(
                    "Legacy config file corrupted, using defaults",
                    project_path=str(project_path),
                    version=legacy_version,
                )
                legacy_config = {}

            # Convert to new format
            new_config, settings_migrated = self._convert_to_new_format(
                legacy_config, legacy_version
            )

            # Write new configuration
            self._write_new_config(project_path, new_config)

            # Create/update global configuration
            self._ensure_global_config(new_config)

            duration_ms = int((time.time() - start_time) * 1000)

            self.logger.info(
                "Migration completed successfully",
                project_path=str(project_path),
                from_version=legacy_version,
                settings_migrated=settings_migrated,
                duration_ms=duration_ms,
            )

            return MigrationResult(
                migrated=True,
                reason="Migration completed successfully",
                from_version=legacy_version,
                settings_migrated=settings_migrated,
                backup_path=backup_path,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(
                "Migration failed",
                project_path=str(project_path),
                error=str(e),
            )
            return MigrationResult(
                migrated=False,
                reason=f"Migration failed: {e}",
                from_version=legacy_version,
                duration_ms=duration_ms,
            )

    def _backup_files(self, project_path: Path) -> Path:
        """
        Create timestamped backup of configuration files.

        Creates a backup directory with timestamp and copies all
        configuration files that will be affected by migration.

        Args:
            project_path: Path to project directory

        Returns:
            Path to backup directory
        """
        gao_dev_dir = project_path / ".gao-dev"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_dir_name = self.BACKUP_DIR_PATTERN.format(timestamp=timestamp)
        backup_dir = gao_dev_dir / backup_dir_name

        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup all legacy config files
        files_to_backup = [
            self.V1_CONFIG_FILE,
            self.EPIC35_CONFIG_FILE,
            self.NEW_CONFIG_FILE,  # In case of re-migration
        ]

        for filename in files_to_backup:
            source_file = gao_dev_dir / filename
            if source_file.exists():
                dest_file = backup_dir / filename
                shutil.copy2(source_file, dest_file)
                self.logger.debug(
                    "Backed up file",
                    source=str(source_file),
                    dest=str(dest_file),
                )

        self.logger.info(
            "Created backup",
            backup_path=str(backup_dir),
        )

        return backup_dir

    def _load_v1_config(self, project_path: Path) -> Optional[dict]:
        """
        Load v1 format configuration (gao-dev.yaml).

        Args:
            project_path: Path to project directory

        Returns:
            Configuration dictionary or None if corrupted
        """
        config_file = project_path / ".gao-dev" / self.V1_CONFIG_FILE

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self.logger.warning(
                    "v1 config file does not contain dict",
                    file=str(config_file),
                )
                return None

            self.logger.debug(
                "Loaded v1 configuration",
                file=str(config_file),
                keys=list(data.keys()),
            )
            return data

        except yaml.YAMLError as e:
            self.logger.warning(
                "Invalid YAML in v1 config file",
                file=str(config_file),
                error=str(e),
            )
            return None
        except Exception as e:
            self.logger.warning(
                "Error loading v1 config file",
                file=str(config_file),
                error=str(e),
            )
            return None

    def _load_epic35_config(self, project_path: Path) -> Optional[dict]:
        """
        Load Epic 35 format configuration (provider_preferences.yaml).

        Args:
            project_path: Path to project directory

        Returns:
            Configuration dictionary or None if corrupted
        """
        config_file = project_path / ".gao-dev" / self.EPIC35_CONFIG_FILE

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self.logger.warning(
                    "Epic 35 config file does not contain dict",
                    file=str(config_file),
                )
                return None

            self.logger.debug(
                "Loaded Epic 35 configuration",
                file=str(config_file),
                keys=list(data.keys()),
            )
            return data

        except yaml.YAMLError as e:
            self.logger.warning(
                "Invalid YAML in Epic 35 config file",
                file=str(config_file),
                error=str(e),
            )
            return None
        except Exception as e:
            self.logger.warning(
                "Error loading Epic 35 config file",
                file=str(config_file),
                error=str(e),
            )
            return None

    def _convert_to_new_format(
        self, legacy_config: dict, from_version: str
    ) -> tuple[dict, list[str]]:
        """
        Convert legacy configuration to new format.

        Args:
            legacy_config: Legacy configuration dictionary
            from_version: Source version (v1 or epic35)

        Returns:
            Tuple of (new configuration dict, list of migrated settings)
        """
        settings_migrated = []
        now = datetime.now().isoformat() + "Z"

        new_config = {
            "version": self.VERSION_NEW,
            "project": {
                "name": "",
                "type": "brownfield",
                "created_at": now,
            },
            "migrated_from": from_version,
            "migrated_at": now,
            "provider": {
                "default": "claude-code",
                "model": "sonnet-4.5",
            },
            "credentials": {
                "storage": "environment",
            },
        }

        if from_version == self.VERSION_V1:
            # Convert v1 format
            if "project_name" in legacy_config:
                new_config["project"]["name"] = legacy_config["project_name"]
                settings_migrated.append("project_name")

            if "provider" in legacy_config:
                new_config["provider"]["default"] = legacy_config["provider"]
                settings_migrated.append("provider")

            if "model" in legacy_config:
                new_config["provider"]["model"] = legacy_config["model"]
                settings_migrated.append("model")

            if "api_key_source" in legacy_config:
                new_config["credentials"]["storage"] = legacy_config["api_key_source"]
                settings_migrated.append("api_key_source")

            # Preserve any features config
            if "features" in legacy_config:
                new_config["features"] = legacy_config["features"]
                settings_migrated.append("features")

        elif from_version == self.VERSION_EPIC35:
            # Convert Epic 35 format
            if "provider" in legacy_config:
                new_config["provider"]["default"] = legacy_config["provider"]
                settings_migrated.append("provider")

            if "model" in legacy_config:
                new_config["provider"]["model"] = legacy_config["model"]
                settings_migrated.append("model")

            if "saved_at" in legacy_config:
                new_config["project"]["created_at"] = legacy_config["saved_at"]
                settings_migrated.append("saved_at")

            # Handle nested provider structure from newer Epic 35 format
            if "version" in legacy_config:
                settings_migrated.append("version")

            provider_info = legacy_config.get("provider", {})
            if isinstance(provider_info, dict):
                if "name" in provider_info:
                    new_config["provider"]["default"] = provider_info["name"]
                    if "provider" not in settings_migrated:
                        settings_migrated.append("provider")
                if "model" in provider_info:
                    new_config["provider"]["model"] = provider_info["model"]
                    if "model" not in settings_migrated:
                        settings_migrated.append("model")
                if "config" in provider_info:
                    new_config["provider"]["config"] = provider_info["config"]
                    settings_migrated.append("provider_config")

            # Handle metadata
            if "metadata" in legacy_config:
                metadata = legacy_config["metadata"]
                if isinstance(metadata, dict):
                    if "last_updated" in metadata:
                        new_config["project"]["created_at"] = metadata["last_updated"]
                        if "saved_at" not in settings_migrated:
                            settings_migrated.append("last_updated")

        self.logger.debug(
            "Converted configuration",
            from_version=from_version,
            settings_migrated=settings_migrated,
        )

        return new_config, settings_migrated

    def _write_new_config(self, project_path: Path, config: dict) -> None:
        """
        Write new configuration file with atomic operation.

        Uses tempfile + rename for atomic write to prevent corruption.

        Args:
            project_path: Path to project directory
            config: Configuration dictionary to write
        """
        gao_dev_dir = project_path / ".gao-dev"
        config_file = gao_dev_dir / self.NEW_CONFIG_FILE

        # Use atomic write (temp file + rename)
        fd, temp_path = tempfile.mkstemp(
            dir=gao_dev_dir,
            prefix="config_",
            suffix=".yaml.tmp",
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Set file permissions (Unix only)
            if os.name != "nt":
                os.chmod(temp_path, 0o600)

            # Atomic replace
            temp_file = Path(temp_path)
            temp_file.replace(config_file)

            self.logger.info(
                "Wrote new configuration",
                file=str(config_file),
            )

        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _ensure_global_config(self, config: dict) -> None:
        """
        Create or update global configuration at ~/.gao-dev/config.yaml.

        Only creates if it doesn't exist (first project migration).
        Preserves credential references but not sensitive data.

        Args:
            config: Configuration to use as source for global config
        """
        home_dir = Path.home()
        global_gao_dev_dir = home_dir / ".gao-dev"
        global_config_file = global_gao_dev_dir / self.NEW_CONFIG_FILE

        # Skip if global config already exists
        if global_config_file.exists():
            self.logger.debug(
                "Global config already exists, skipping creation",
                file=str(global_config_file),
            )
            return

        # Create global .gao-dev directory
        global_gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Set directory permissions (Unix only)
        if os.name != "nt":
            try:
                os.chmod(global_gao_dev_dir, 0o700)
            except OSError:
                pass

        # Create global config (subset of project config)
        global_config = {
            "version": self.VERSION_NEW,
            "created_at": datetime.now().isoformat() + "Z",
            "provider": config.get("provider", {
                "default": "claude-code",
                "model": "sonnet-4.5",
            }),
            "credentials": config.get("credentials", {
                "storage": "environment",
            }),
        }

        # Use atomic write
        fd, temp_path = tempfile.mkstemp(
            dir=global_gao_dev_dir,
            prefix="config_",
            suffix=".yaml.tmp",
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    global_config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Set file permissions (Unix only)
            if os.name != "nt":
                os.chmod(temp_path, 0o600)

            # Atomic replace
            temp_file = Path(temp_path)
            temp_file.replace(global_config_file)

            self.logger.info(
                "Created global configuration",
                file=str(global_config_file),
            )

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            self.logger.warning(
                "Failed to create global configuration",
                file=str(global_config_file),
                error=str(e),
            )
            # Don't raise - global config is nice to have but not critical

    def should_skip_onboarding(self, project_path: Path) -> bool:
        """
        Check if onboarding should be skipped for migrated users.

        Returns True if:
        - New config exists AND
        - Config contains migrated_from field

        Args:
            project_path: Path to project directory

        Returns:
            True if onboarding should be skipped
        """
        config_file = project_path / ".gao-dev" / self.NEW_CONFIG_FILE

        if not config_file.exists():
            return False

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                return False

            # Skip onboarding if this was a migration
            return "migrated_from" in config

        except Exception:
            return False

    def get_migration_summary(self, result: MigrationResult) -> str:
        """
        Generate a formatted migration summary for display.

        Args:
            result: MigrationResult to summarize

        Returns:
            Formatted summary string
        """
        if not result.migrated:
            return f"Migration not performed: {result.reason}"

        lines = [
            "Configuration Migration Complete",
            "=" * 35,
            f"Migrated from: {result.from_version} format",
            f"Duration: {result.duration_ms}ms",
            "",
            "Settings migrated:",
        ]

        if result.settings_migrated:
            for setting in result.settings_migrated:
                lines.append(f"  - {setting}")
        else:
            lines.append("  (none)")

        if result.backup_path:
            lines.append("")
            lines.append(f"Backup created at:")
            lines.append(f"  {result.backup_path}")

        return "\n".join(lines)
