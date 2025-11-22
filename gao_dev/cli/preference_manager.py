"""Provider preference persistence manager.

This module provides the PreferenceManager class for loading and saving
provider preferences to .gao-dev/provider_preferences.yaml.

Epic 35: Interactive Provider Selection at Startup
Story 35.2: PreferenceManager Implementation

CRAAP Resolution: YAML security measures implemented.
- Uses yaml.safe_dump() instead of yaml.dump()
- Sanitizes all input before saving
- Comprehensive security tests
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
import yaml

from gao_dev.cli.exceptions import PreferenceSaveError

logger = structlog.get_logger()


class PreferenceManager:
    """
    Manages provider preference persistence.

    Loads and saves preferences to .gao-dev/provider_preferences.yaml with
    validation, error handling, and security measures.

    SECURITY NOTE:
    - Uses yaml.safe_dump() to prevent code execution
    - Sanitizes all string input before saving
    - Only allows safe characters (alphanumeric, dash, underscore, dot, etc.)

    Attributes:
        project_root: Project root directory
        preferences_file: Path to preferences YAML file

    Example:
        ```python
        manager = PreferenceManager(project_root)

        # Save preferences
        manager.save_preferences({
            'provider': 'opencode',
            'model': 'deepseek-r1',
            'config': {'ai_provider': 'ollama'}
        })

        # Load preferences
        prefs = manager.load_preferences()
        # Returns dict or None if invalid/missing
        ```
    """

    # CRAAP Security: Whitelist of safe characters for YAML values
    # Only allows: alphanumeric, dash, underscore, dot, space, comma
    # Explicitly removes: /, :, !, &, *, {, }, [, ], |, >, <, `, $, (, ), ', "
    SAFE_CHAR_PATTERN = re.compile(r"[^a-zA-Z0-9\-_.,\s]")

    # Semantic version pattern (X.Y.Z or X.Y.Z-suffix)
    VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9\-_.]+)?$")

    # ISO 8601 timestamp pattern (supports microseconds and timezone)
    TIMESTAMP_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
    )

    def __init__(self, project_root: Path):
        """
        Initialize PreferenceManager with project root.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.gao_dev_dir = project_root / ".gao-dev"
        self.preferences_file = self.gao_dev_dir / "provider_preferences.yaml"
        self.backup_file = self.preferences_file.with_suffix(".yaml.bak")
        self.temp_file = self.preferences_file.with_suffix(".yaml.tmp")
        self.logger = logger.bind(component="preference_manager")

    def load_preferences(self) -> Optional[Dict[str, Any]]:
        """
        Load saved preferences from file.

        Returns None if file doesn't exist or is invalid. Never crashes.

        If main file is corrupt and backup exists, attempts to load from backup.

        Returns:
            Preferences dict, or None if file doesn't exist or is invalid

        Format:
            {
                'version': '1.0.0',
                'provider': {
                    'name': 'opencode',
                    'model': 'deepseek-r1',
                    'config': {...}
                },
                'metadata': {
                    'last_updated': '2025-01-12T10:30:00Z',
                    'cli_version': '1.2.3'
                }
            }
        """
        # Try to load main file
        result = self._load_from_file(self.preferences_file)
        if result is not None:
            return result

        # Main file failed, try backup if it exists
        if self.backup_file.exists():
            self.logger.warning(
                "Main preferences file corrupt, attempting backup",
                main_file=str(self.preferences_file),
                backup_file=str(self.backup_file),
            )
            result = self._load_from_file(self.backup_file)
            if result is not None:
                self.logger.info("Successfully loaded from backup")
                return result

        return None

    def _load_from_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load preferences from specific file.

        Args:
            file_path: Path to YAML file

        Returns:
            Preferences dict or None if invalid
        """
        if not file_path.exists():
            self.logger.debug("Preferences file not found", file=str(file_path))
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                self.logger.warning(
                    "Preferences file does not contain dict", file=str(file_path)
                )
                return None

            self.logger.info("Loaded preferences", file=str(file_path))
            return data

        except yaml.YAMLError as e:
            self.logger.warning(
                "Invalid YAML in preferences file",
                file=str(file_path),
                error=str(e),
            )
            return None
        except Exception as e:
            self.logger.error(
                "Unexpected error loading preferences",
                file=str(file_path),
                error=str(e),
            )
            return None

    def save_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Save preferences to file with security measures.

        SECURITY:
        1. Sanitizes all input before saving
        2. Uses yaml.safe_dump() to prevent code execution
        3. Sets restrictive file permissions (0600)
        4. Creates backup before overwriting
        5. Uses atomic write (tmp file -> replace)

        Args:
            preferences: Preferences dict to save

        Raises:
            PreferenceSaveError: If save fails
        """
        try:
            # Step 1: Create .gao-dev directory if missing
            self._ensure_directory_exists()

            # Step 2: Create backup if file already exists
            if self.preferences_file.exists():
                self._create_backup()

            # Step 3: Sanitize input (CRAAP Critical)
            sanitized = self._sanitize_dict(preferences)

            # Step 4: Write to temporary file first (atomic write)
            with open(self.temp_file, "w", encoding="utf-8") as f:
                # CRAAP Critical: Use safe_dump (not dump) to prevent code execution
                yaml.safe_dump(
                    sanitized,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Step 5: Set file permissions before moving
            self._set_file_permissions(self.temp_file)

            # Step 6: Atomic replace
            self.temp_file.replace(self.preferences_file)

            self.logger.info(
                "Saved preferences",
                file=str(self.preferences_file),
                sanitized=True,
            )

        except (OSError, IOError) as e:
            self.logger.error(
                "Failed to save preferences",
                file=str(self.preferences_file),
                error=str(e),
            )
            # Clean up temp file if it exists
            if self.temp_file.exists():
                try:
                    self.temp_file.unlink()
                except Exception:
                    pass

            raise PreferenceSaveError(
                f"Failed to save preferences: {e}"
            ) from e
        except Exception as e:
            self.logger.error(
                "Unexpected error saving preferences",
                file=str(self.preferences_file),
                error=str(e),
            )
            # Clean up temp file if it exists
            if self.temp_file.exists():
                try:
                    self.temp_file.unlink()
                except Exception:
                    pass

            raise PreferenceSaveError(
                f"Unexpected error saving preferences: {e}"
            ) from e

    def has_preferences(self) -> bool:
        """
        Check if preferences file exists and is valid.

        Returns:
            True if valid preferences file exists, False otherwise
        """
        if not self.preferences_file.exists():
            return False

        # Try to load to verify it's valid
        prefs = self.load_preferences()
        return prefs is not None

    def get_default_preferences(self) -> Dict[str, Any]:
        """
        Get default preferences for fallback.

        Returns:
            Default preferences (claude-code, sonnet-4.5)
        """
        return {
            "version": "1.0.0",
            "provider": {
                "name": "claude-code",
                "model": "sonnet-4.5",
                "config": {
                    "ai_provider": "anthropic",
                    "use_local": False,
                },
            },
            "metadata": {
                "last_updated": datetime.now().isoformat() + "Z",
                "cli_version": "1.0.0",
            },
        }

    def validate_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Validate preference structure.

        Checks:
        - Required keys present: version, provider, metadata
        - Version format is semantic versioning (X.Y.Z)
        - Timestamp format is ISO 8601
        - Provider name is string
        - Structure is correct

        Args:
            preferences: Preferences dict to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required keys
            required_keys = ["version", "provider", "metadata"]
            for key in required_keys:
                if key not in preferences:
                    self.logger.warning(
                        "Validation failed: missing required key",
                        key=key,
                    )
                    return False

            # Validate version format
            version = preferences["version"]
            if not isinstance(version, str):
                self.logger.warning(
                    "Validation failed: version not string",
                    version_type=type(version).__name__,
                )
                return False

            if not self.VERSION_PATTERN.match(version):
                self.logger.warning(
                    "Validation failed: invalid version format",
                    version=version,
                )
                return False

            # Validate provider structure
            provider = preferences["provider"]
            if not isinstance(provider, dict):
                self.logger.warning(
                    "Validation failed: provider not dict",
                    provider_type=type(provider).__name__,
                )
                return False

            # Validate metadata structure
            metadata = preferences["metadata"]
            if not isinstance(metadata, dict):
                self.logger.warning(
                    "Validation failed: metadata not dict",
                    metadata_type=type(metadata).__name__,
                )
                return False

            # Validate timestamp if present
            if "last_updated" in metadata:
                timestamp = metadata["last_updated"]
                if not isinstance(timestamp, str):
                    self.logger.warning(
                        "Validation failed: timestamp not string",
                        timestamp_type=type(timestamp).__name__,
                    )
                    return False

                if not self.TIMESTAMP_PATTERN.match(timestamp):
                    self.logger.warning(
                        "Validation failed: invalid timestamp format",
                        timestamp=timestamp,
                    )
                    return False

            self.logger.debug("Preferences validation passed")
            return True

        except Exception as e:
            self.logger.warning(
                "Validation failed with exception",
                error=str(e),
            )
            return False

    def delete_preferences(self) -> None:
        """
        Delete preferences file (for testing/reset).

        Also deletes backup and temp files if they exist.
        """
        files_to_delete = [
            self.preferences_file,
            self.backup_file,
            self.temp_file,
        ]

        for file_path in files_to_delete:
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.logger.debug("Deleted file", file=str(file_path))
                except Exception as e:
                    self.logger.warning(
                        "Failed to delete file",
                        file=str(file_path),
                        error=str(e),
                    )

    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize string to prevent YAML injection.

        CRAAP Resolution: Security measure against YAML injection attacks.

        Only allows: alphanumeric, dash, underscore, dot, space, comma
        Removes: YAML tags (!), anchors (&), aliases (*), braces, brackets,
                 pipes, backticks, dollar signs, slashes, colons, etc.

        Args:
            value: String to sanitize

        Returns:
            Sanitized string with only safe characters
        """
        if not isinstance(value, str):
            return value

        # Remove all unsafe characters
        sanitized = self.SAFE_CHAR_PATTERN.sub("", value)

        # Log if sanitization changed the value
        if sanitized != value:
            self.logger.debug(
                "Sanitized string value",
                original_length=len(value),
                sanitized_length=len(sanitized),
            )

        return sanitized

    def _sanitize_dict(self, data: Any) -> Any:
        """
        Recursively sanitize all string values in dict.

        CRAAP Resolution: Security measure against YAML injection attacks.

        Handles:
        - Nested dicts
        - Lists
        - String values (sanitized)
        - Other types (preserved as-is)

        Args:
            data: Data to sanitize (dict, list, str, or other)

        Returns:
            Sanitized data with all strings cleaned
        """
        if isinstance(data, dict):
            # Recursively sanitize dict values
            return {key: self._sanitize_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            # Recursively sanitize list items
            return [self._sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            # Sanitize string value
            return self._sanitize_string(data)
        else:
            # Preserve other types (int, bool, float, None, etc.)
            return data

    def _create_backup(self) -> None:
        """
        Create backup of existing preferences file.

        CRAAP Resolution: Backup strategy for preference recovery.

        Creates .yaml.bak file before overwriting. If backup already exists,
        it is overwritten with current file content.
        """
        if not self.preferences_file.exists():
            return

        try:
            shutil.copy2(self.preferences_file, self.backup_file)
            self.logger.debug(
                "Created backup",
                source=str(self.preferences_file),
                backup=str(self.backup_file),
            )
        except Exception as e:
            self.logger.warning(
                "Failed to create backup (continuing anyway)",
                error=str(e),
            )
            # Don't raise - backup is nice to have but not critical

    def _ensure_directory_exists(self) -> None:
        """
        Ensure .gao-dev directory exists with correct permissions.

        Creates directory with 0700 permissions on Unix.
        """
        if self.gao_dev_dir.exists():
            return

        try:
            self.gao_dev_dir.mkdir(parents=True, exist_ok=True)

            # Set directory permissions (Unix only)
            if os.name != "nt":
                os.chmod(self.gao_dev_dir, 0o700)

            self.logger.debug(
                "Created .gao-dev directory",
                path=str(self.gao_dev_dir),
            )
        except Exception as e:
            self.logger.error(
                "Failed to create .gao-dev directory",
                path=str(self.gao_dev_dir),
                error=str(e),
            )
            raise PreferenceSaveError(
                f"Failed to create .gao-dev directory: {e}"
            ) from e

    def _set_file_permissions(self, file_path: Path) -> None:
        """
        Set restrictive file permissions.

        Sets 0600 (user read/write only) on Unix.
        On Windows, uses os.chmod() which has limited effect.

        Args:
            file_path: Path to file to set permissions on
        """
        if os.name == "nt":
            # Windows: chmod has limited effect, but call it anyway
            try:
                os.chmod(file_path, 0o600)
            except Exception:
                pass  # Windows permissions work differently
        else:
            # Unix: Set strict permissions
            try:
                os.chmod(file_path, 0o600)
                self.logger.debug(
                    "Set file permissions to 0600",
                    file=str(file_path),
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to set file permissions",
                    file=str(file_path),
                    error=str(e),
                )
                # Don't raise - permissions are important but not critical
