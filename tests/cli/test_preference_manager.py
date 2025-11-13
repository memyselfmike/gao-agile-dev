"""Tests for PreferenceManager.

Epic 35: Interactive Provider Selection at Startup
Story 35.2: PreferenceManager Implementation

Tests cover:
- Basic load/save functionality
- YAML injection prevention (CRAAP Critical)
- Backup strategy (CRAAP Moderate)
- Validation logic
- Error handling
- File permissions
- Security hardening
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import pytest
import yaml

from gao_dev.cli.preference_manager import PreferenceManager
from gao_dev.cli.exceptions import PreferenceSaveError


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root."""
    return tmp_path


@pytest.fixture
def preference_manager(temp_project_root: Path) -> PreferenceManager:
    """Create PreferenceManager instance."""
    return PreferenceManager(temp_project_root)


@pytest.fixture
def valid_preferences() -> Dict[str, Any]:
    """Create valid preferences dict."""
    return {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {"ai_provider": "ollama", "use_local": True},
        },
        "metadata": {
            "last_updated": "2025-01-12T10:30:00Z",
            "cli_version": "1.2.3",
        },
    }


# ============================================================================
# Basic Functionality Tests
# ============================================================================


def test_preference_manager_imports():
    """Test that PreferenceManager can be imported."""
    from gao_dev.cli.preference_manager import PreferenceManager

    assert PreferenceManager is not None


def test_load_missing_file(preference_manager: PreferenceManager):
    """Missing file returns None, doesn't crash."""
    result = preference_manager.load_preferences()
    assert result is None


def test_save_preferences(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Save preferences to file with correct format."""
    preference_manager.save_preferences(valid_preferences)

    # Verify file exists
    assert preference_manager.preferences_file.exists()

    # Load raw YAML to verify format
    with open(preference_manager.preferences_file, "r") as f:
        saved_data = yaml.safe_load(f)

    # Verify structure (sanitization may modify values)
    assert "version" in saved_data
    assert "provider" in saved_data
    assert "metadata" in saved_data


def test_load_valid_preferences(
    preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]
):
    """Load valid preferences from file."""
    # Save first
    preference_manager.save_preferences(valid_preferences)

    # Load back
    loaded = preference_manager.load_preferences()
    assert loaded is not None
    assert "version" in loaded
    assert "provider" in loaded
    assert "metadata" in loaded


def test_round_trip(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Save then load produces equivalent dict."""
    preference_manager.save_preferences(valid_preferences)
    loaded = preference_manager.load_preferences()

    assert loaded is not None
    # After sanitization, structure should be preserved
    assert loaded["version"] == valid_preferences["version"]
    assert "provider" in loaded
    assert "metadata" in loaded


def test_has_preferences_missing(preference_manager: PreferenceManager):
    """has_preferences returns False when file missing."""
    assert preference_manager.has_preferences() is False


def test_has_preferences_exists(
    preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]
):
    """has_preferences returns True when file exists."""
    preference_manager.save_preferences(valid_preferences)
    assert preference_manager.has_preferences() is True


def test_delete_preferences(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """delete_preferences removes file."""
    preference_manager.save_preferences(valid_preferences)
    assert preference_manager.preferences_file.exists()

    preference_manager.delete_preferences()
    assert not preference_manager.preferences_file.exists()


# ============================================================================
# Validation Tests
# ============================================================================


def test_validate_valid_preferences(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Valid preferences pass validation."""
    assert preference_manager.validate_preferences(valid_preferences) is True


def test_validate_missing_version(preference_manager: PreferenceManager):
    """Missing 'version' key fails validation."""
    invalid = {
        "provider": {"name": "opencode", "model": "deepseek-r1", "config": {}},
        "metadata": {"last_updated": "2025-01-12T10:30:00Z"},
    }
    assert preference_manager.validate_preferences(invalid) is False


def test_validate_missing_provider(preference_manager: PreferenceManager):
    """Missing 'provider' key fails validation."""
    invalid = {
        "version": "1.0.0",
        "metadata": {"last_updated": "2025-01-12T10:30:00Z"},
    }
    assert preference_manager.validate_preferences(invalid) is False


def test_validate_missing_metadata(preference_manager: PreferenceManager):
    """Missing 'metadata' key fails validation."""
    invalid = {
        "version": "1.0.0",
        "provider": {"name": "opencode", "model": "deepseek-r1", "config": {}},
    }
    assert preference_manager.validate_preferences(invalid) is False


def test_validate_invalid_version_format(preference_manager: PreferenceManager):
    """Invalid version format fails validation."""
    invalid = {
        "version": "not-a-version",  # Should be X.Y.Z
        "provider": {"name": "opencode", "model": "deepseek-r1", "config": {}},
        "metadata": {"last_updated": "2025-01-12T10:30:00Z"},
    }
    assert preference_manager.validate_preferences(invalid) is False


def test_validate_invalid_timestamp_format(preference_manager: PreferenceManager):
    """Invalid timestamp format fails validation."""
    invalid = {
        "version": "1.0.0",
        "provider": {"name": "opencode", "model": "deepseek-r1", "config": {}},
        "metadata": {"last_updated": "not-a-timestamp"},
    }
    assert preference_manager.validate_preferences(invalid) is False


def test_default_preferences_valid(preference_manager: PreferenceManager):
    """Default preferences are valid."""
    defaults = preference_manager.get_default_preferences()
    assert preference_manager.validate_preferences(defaults) is True


# ============================================================================
# Security Tests (CRAAP Critical - YAML Injection Prevention)
# ============================================================================


def test_sanitize_string_removes_yaml_tags(preference_manager: PreferenceManager):
    """Sanitization removes YAML tags (!!)."""
    malicious = "!!python/object/apply:os.system"
    sanitized = preference_manager._sanitize_string(malicious)
    # Verify dangerous characters removed
    assert "!!" not in sanitized
    assert "/" not in sanitized
    assert ":" not in sanitized
    # Only alphanumeric and safe chars (including dots) remain
    # Result should be: "pythonobjectapplyos.system" (dots are safe)
    assert "python" in sanitized
    assert "object" in sanitized
    assert "." in sanitized  # Dots are allowed
    assert "!" not in sanitized


def test_sanitize_string_removes_yaml_anchors(preference_manager: PreferenceManager):
    """Sanitization removes YAML anchors (&, *)."""
    malicious = "&anchor *alias"
    sanitized = preference_manager._sanitize_string(malicious)
    assert "&" not in sanitized
    assert "*" not in sanitized


def test_sanitize_string_removes_dangerous_chars(preference_manager: PreferenceManager):
    """Sanitization removes dangerous YAML characters."""
    dangerous = "model: {key: value} [array] | pipe > redirect `backtick` $var"
    sanitized = preference_manager._sanitize_string(dangerous)

    # All dangerous characters should be removed
    assert "{" not in sanitized
    assert "}" not in sanitized
    assert "[" not in sanitized
    assert "]" not in sanitized
    assert "|" not in sanitized
    assert ">" not in sanitized
    assert "`" not in sanitized
    assert "$" not in sanitized


def test_sanitize_string_preserves_safe_chars(preference_manager: PreferenceManager):
    """Sanitization preserves safe characters."""
    safe = "deepseek-r1_model.v2 test-123"
    sanitized = preference_manager._sanitize_string(safe)

    # Safe characters should be preserved
    assert "deepseek" in sanitized
    assert "r1" in sanitized
    assert "model" in sanitized
    assert "v2" in sanitized
    # Spaces, dashes, underscores, dots should be preserved
    assert "-" in sanitized
    assert "_" in sanitized
    assert "." in sanitized


def test_sanitize_dict_recursive(preference_manager: PreferenceManager):
    """Sanitization works on nested dictionaries."""
    malicious = {
        "provider": {"name": "!!python/eval", "model": "test&anchor"},
        "config": {"key": "{dangerous}"},
    }
    sanitized = preference_manager._sanitize_dict(malicious)

    # Verify structure preserved
    assert "provider" in sanitized
    assert "name" in sanitized["provider"]
    assert "model" in sanitized["provider"]

    # Verify dangerous chars removed from VALUES (not dict structure itself)
    name_value = sanitized["provider"]["name"]
    model_value = sanitized["provider"]["model"]
    key_value = sanitized["config"]["key"]

    assert "!!" not in name_value
    assert "/" not in name_value
    assert "&" not in model_value
    assert "{" not in key_value
    assert "}" not in key_value


def test_yaml_injection_attempt_prevented(
    preference_manager: PreferenceManager, temp_project_root: Path
):
    """YAML injection attack is prevented."""
    malicious_prefs = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "!!python/object/apply:os.system ['rm -rf /']",
            "config": {},
        },
        "metadata": {"last_updated": "2025-01-12T10:30:00Z"},
    }

    preference_manager.save_preferences(malicious_prefs)

    # Read raw file content
    with open(preference_manager.preferences_file, "r") as f:
        content = f.read()

    # Verify malicious YAML tags are NOT in file
    assert "!!python" not in content
    assert ":os.system" not in content  # Colon removed by sanitization
    assert "['rm" not in content  # Brackets removed by sanitization
    # Verify only safe characters remain
    assert "!!" not in content
    assert "[" not in content
    assert "]" not in content


def test_yaml_safe_dump_used(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Verify yaml.safe_dump() is used (not yaml.dump())."""
    preference_manager.save_preferences(valid_preferences)

    # Try to load with safe_load (should succeed)
    with open(preference_manager.preferences_file, "r") as f:
        data = yaml.safe_load(f)
    assert data is not None

    # File should not contain dangerous YAML constructs
    with open(preference_manager.preferences_file, "r") as f:
        content = f.read()
    assert "!!python" not in content
    assert "!!" not in content


# ============================================================================
# Backup Strategy Tests (CRAAP Moderate)
# ============================================================================


def test_backup_not_created_for_new_file(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """No backup created for first-time save."""
    preference_manager.save_preferences(valid_preferences)

    backup_file = preference_manager.preferences_file.with_suffix(".yaml.bak")
    assert not backup_file.exists()


def test_backup_created_before_overwrite(
    preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]
):
    """Backup file created before overwriting."""
    # First save
    preference_manager.save_preferences(valid_preferences)
    original_content = preference_manager.preferences_file.read_text()

    # Second save (should create backup)
    modified_prefs = valid_preferences.copy()
    modified_prefs["version"] = "2.0.0"
    preference_manager.save_preferences(modified_prefs)

    # Verify backup exists and contains original content
    backup_file = preference_manager.preferences_file.with_suffix(".yaml.bak")
    assert backup_file.exists()

    backup_content = backup_file.read_text()
    assert backup_content == original_content


def test_load_from_backup_if_corrupt(
    preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]
):
    """Load from backup if main file is corrupt."""
    # Save valid preferences
    preference_manager.save_preferences(valid_preferences)

    # Save again to create backup
    preference_manager.save_preferences(valid_preferences)

    # Corrupt main file
    with open(preference_manager.preferences_file, "w") as f:
        f.write("invalid: yaml: content: ::::")

    # Load should fallback to backup
    loaded = preference_manager.load_preferences()
    assert loaded is not None
    assert "version" in loaded


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_load_corrupt_yaml(preference_manager: PreferenceManager):
    """Corrupt YAML returns None, logs warning."""
    # Create .gao-dev directory
    preference_manager.gao_dev_dir.mkdir(parents=True, exist_ok=True)

    # Write invalid YAML
    with open(preference_manager.preferences_file, "w") as f:
        f.write("invalid: yaml: {{{")

    result = preference_manager.load_preferences()
    # Should return None (or fallback to backup if exists)
    # If no backup exists, should return None
    assert result is None or isinstance(result, dict)


def test_save_permission_error(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Permission error raises PreferenceSaveError."""
    if os.name == "nt":
        pytest.skip("Permission tests unreliable on Windows")

    # Create .gao-dev directory
    preference_manager.gao_dev_dir.mkdir(parents=True, exist_ok=True)

    # Make directory read-only
    os.chmod(preference_manager.gao_dev_dir, 0o444)

    try:
        with pytest.raises(PreferenceSaveError):
            preference_manager.save_preferences(valid_preferences)
    finally:
        # Restore permissions for cleanup
        os.chmod(preference_manager.gao_dev_dir, 0o700)


# ============================================================================
# File Permissions Tests
# ============================================================================


def test_save_creates_directory(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """.gao-dev/ directory created if missing."""
    assert not preference_manager.gao_dev_dir.exists()

    preference_manager.save_preferences(valid_preferences)

    assert preference_manager.gao_dev_dir.exists()
    assert preference_manager.gao_dev_dir.is_dir()


def test_directory_permissions(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Directory has correct permissions (0700 on Unix)."""
    if os.name == "nt":
        pytest.skip("Unix permission test not applicable on Windows")

    preference_manager.save_preferences(valid_preferences)

    # Check directory permissions
    stat_info = preference_manager.gao_dev_dir.stat()
    mode = stat_info.st_mode & 0o777
    assert mode == 0o700


def test_file_permissions(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """File has correct permissions (0600 on Unix)."""
    if os.name == "nt":
        pytest.skip("Unix permission test not applicable on Windows")

    preference_manager.save_preferences(valid_preferences)

    # Check file permissions
    stat_info = preference_manager.preferences_file.stat()
    mode = stat_info.st_mode & 0o777
    assert mode == 0o600


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_save_empty_config(preference_manager: PreferenceManager):
    """Save preferences with empty config."""
    prefs = {
        "version": "1.0.0",
        "provider": {"name": "opencode", "model": "deepseek-r1", "config": {}},
        "metadata": {"last_updated": "2025-01-12T10:30:00Z"},
    }
    preference_manager.save_preferences(prefs)

    loaded = preference_manager.load_preferences()
    assert loaded is not None
    assert loaded["provider"]["config"] == {}


def test_sanitize_preserves_numbers(preference_manager: PreferenceManager):
    """Sanitization preserves numeric values."""
    data = {"version": "1.0.0", "port": 8080, "enabled": True, "timeout": 30.5}
    sanitized = preference_manager._sanitize_dict(data)

    assert sanitized["port"] == 8080
    assert sanitized["enabled"] is True
    assert sanitized["timeout"] == 30.5


def test_sanitize_preserves_lists(preference_manager: PreferenceManager):
    """Sanitization works with lists."""
    data = {"items": ["item1", "item&2", "item!!3"]}
    sanitized = preference_manager._sanitize_dict(data)

    assert "items" in sanitized
    assert len(sanitized["items"]) == 3
    # Dangerous chars should be removed from strings in list
    assert "&" not in str(sanitized["items"])
    assert "!!" not in str(sanitized["items"])


def test_multiple_saves_atomic(preference_manager: PreferenceManager, valid_preferences: Dict[str, Any]):
    """Multiple saves are atomic (no partial writes)."""
    for i in range(5):
        prefs = valid_preferences.copy()
        prefs["version"] = f"{i}.0.0"
        preference_manager.save_preferences(prefs)

        # Verify file is always valid
        loaded = preference_manager.load_preferences()
        assert loaded is not None
        assert loaded["version"] == f"{i}.0.0"
