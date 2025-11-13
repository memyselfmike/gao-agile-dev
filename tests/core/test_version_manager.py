"""
Tests for gao_dev/core/version_manager.py

Story 36.7: VersionManager for Compatibility Checking
"""

from pathlib import Path
from typing import Callable

import pytest

from gao_dev.core.version_manager import VersionManager, CompatibilityResult


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def version_manager() -> VersionManager:
    """Create a VersionManager instance."""
    return VersionManager()


class TestVersionManager:
    """Test VersionManager functionality."""

    def test_new_project_initialization(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test detection of new project (no .gao-dev directory)."""
        result = version_manager.check_compatibility(temp_project)

        assert result.status == "compatible"
        assert result.action == "initialize"
        assert "New project" in result.message

    def test_project_without_version_file(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test legacy project without version.txt file."""
        # Create .gao-dev directory but no version file
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "needs_migration"
        assert result.action == "migrate"
        assert "Legacy project" in result.message

    def test_compatible_exact_version(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test project with exact version match."""
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text(version_manager.CURRENT_VERSION)

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "compatible"
        assert result.action == "continue"

    def test_compatible_same_major_minor(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test project with same MAJOR.MINOR but different PATCH."""
        # If current version is 1.0.0, set project to 1.0.5
        current_parts = version_manager.CURRENT_VERSION.split('.')
        project_version = f"{current_parts[0]}.{current_parts[1]}.5"

        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text(project_version)

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "compatible"
        assert result.action == "continue"

    def test_needs_migration(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test project that needs migration."""
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text("0.9.0")  # Older but compatible version

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "needs_migration"
        assert result.action == "migrate"
        assert result.from_version == "0.9.0"
        assert result.to_version == version_manager.CURRENT_VERSION

    def test_incompatible_version(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test project with incompatible version (too old)."""
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text("0.5.0")  # Too old

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "incompatible"
        assert result.action == "error"
        assert "incompatible" in result.message.lower()

    def test_get_project_version(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test getting project version."""
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text("1.2.3")

        version = version_manager.get_project_version(temp_project)

        assert version == "1.2.3"

    def test_get_project_version_no_file(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test getting version when file doesn't exist."""
        version = version_manager.get_project_version(temp_project)

        assert version is None

    def test_set_project_version(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test setting project version."""
        version_manager.set_project_version(temp_project, "1.2.3")

        version_file = temp_project / ".gao-dev" / "version.txt"
        assert version_file.exists()
        assert version_file.read_text() == "1.2.3"

    def test_set_project_version_default(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """Test setting project version with default (current version)."""
        version_manager.set_project_version(temp_project)

        version_file = temp_project / ".gao-dev" / "version.txt"
        assert version_file.exists()
        assert version_file.read_text() == version_manager.CURRENT_VERSION


class TestVersionParsing:
    """Test version parsing logic."""

    def test_parse_simple_version(self, version_manager: VersionManager) -> None:
        """Test parsing simple version."""
        major, minor, patch = version_manager._parse_version("1.2.3")

        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_version_with_v_prefix(self, version_manager: VersionManager) -> None:
        """Test parsing version with 'v' prefix."""
        major, minor, patch = version_manager._parse_version("v1.2.3")

        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_version_with_prerelease(self, version_manager: VersionManager) -> None:
        """Test parsing version with prerelease suffix."""
        major, minor, patch = version_manager._parse_version("1.2.3-beta.1")

        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_invalid_version(self, version_manager: VersionManager) -> None:
        """Test parsing invalid version format."""
        with pytest.raises(ValueError, match="Invalid version format"):
            version_manager._parse_version("1.2")

    def test_parse_invalid_numbers(self, version_manager: VersionManager) -> None:
        """Test parsing version with invalid numbers."""
        with pytest.raises(ValueError, match="Invalid version numbers"):
            version_manager._parse_version("1.2.abc")


class TestCompatibilityChecks:
    """Test version compatibility checking logic."""

    def test_is_compatible_exact_match(self, version_manager: VersionManager) -> None:
        """Test compatibility with exact version match."""
        assert version_manager._is_compatible("1.2.3", "1.2.3")

    def test_is_compatible_same_major_minor(self, version_manager: VersionManager) -> None:
        """Test compatibility with same MAJOR.MINOR."""
        assert version_manager._is_compatible("1.2.3", "1.2.5")

    def test_is_not_compatible_different_minor(self, version_manager: VersionManager) -> None:
        """Test incompatibility with different MINOR version."""
        assert not version_manager._is_compatible("1.2.3", "1.3.0")

    def test_is_not_compatible_different_major(self, version_manager: VersionManager) -> None:
        """Test incompatibility with different MAJOR version."""
        assert not version_manager._is_compatible("1.2.3", "2.0.0")

    def test_needs_migration_older_version(self, version_manager: VersionManager) -> None:
        """Test migration needed for older version."""
        assert version_manager._needs_migration("0.9.0", "1.0.0")

    def test_needs_migration_not_needed_same_version(
        self,
        version_manager: VersionManager
    ) -> None:
        """Test migration not needed for same version."""
        assert not version_manager._needs_migration("1.0.0", "1.0.0")

    def test_needs_migration_not_needed_too_old(
        self,
        version_manager: VersionManager
    ) -> None:
        """Test migration not possible for too old version."""
        assert not version_manager._needs_migration("0.1.0", "1.0.0")


class TestMigrations:
    """Test migration detection."""

    def test_get_required_migrations_0_x_to_1_0(
        self,
        version_manager: VersionManager
    ) -> None:
        """Test migrations from 0.x to 1.0."""
        migrations = version_manager._get_required_migrations("0.9.0", "1.0.0")

        assert "migration_0_x_to_1_0" in migrations

    def test_get_required_migrations_multiple(
        self,
        version_manager: VersionManager
    ) -> None:
        """Test multiple migrations needed."""
        migrations = version_manager._get_required_migrations("0.9.0", "1.1.0")

        # Should include migrations for 0.x→1.0 and 1.0→1.1
        assert len(migrations) >= 1
        assert "migration_0_x_to_1_0" in migrations

    def test_get_required_migrations_none_needed(
        self,
        version_manager: VersionManager
    ) -> None:
        """Test no migrations needed for same version."""
        migrations = version_manager._get_required_migrations("1.0.0", "1.0.0")

        assert len(migrations) == 0


class TestAcceptanceCriteria:
    """Test acceptance criteria from Story 36.7."""

    def test_ac1_version_manager_class_exists(self) -> None:
        """AC1: `VersionManager` class with `check_compatibility()` method."""
        vm = VersionManager()
        assert hasattr(vm, 'check_compatibility')
        assert callable(vm.check_compatibility)

    def test_ac2_stores_version_in_version_txt(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """AC2: Stores version in `.gao-dev/version.txt`."""
        version_manager.set_project_version(temp_project, "1.2.3")

        version_file = temp_project / ".gao-dev" / "version.txt"
        assert version_file.exists()
        assert version_file.read_text() == "1.2.3"

    def test_ac3_returns_compatibility_result(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """AC3: Returns CompatibilityResult with status."""
        result = version_manager.check_compatibility(temp_project)

        assert isinstance(result, CompatibilityResult)
        assert result.status in ["compatible", "needs_migration", "incompatible"]
        assert result.action in ["continue", "migrate", "initialize", "error"]

    def test_ac4_new_project_initialize(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """AC4: Test: New project → initialize."""
        result = version_manager.check_compatibility(temp_project)

        assert result.status == "compatible"
        assert result.action == "initialize"

    def test_ac5_old_compatible_version_needs_migration(
        self,
        version_manager: VersionManager,
        temp_project: Path
    ) -> None:
        """AC5: Test: Old compatible version → needs_migration."""
        gaodev_dir = temp_project / ".gao-dev"
        gaodev_dir.mkdir()
        version_file = gaodev_dir / "version.txt"
        version_file.write_text("0.9.0")

        result = version_manager.check_compatibility(temp_project)

        assert result.status == "needs_migration"
        assert result.action == "migrate"
