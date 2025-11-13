"""
Version Manager for GAO-Dev

Manages version compatibility between GAO-Dev installation and user projects.

Story 36.7: VersionManager for Compatibility Checking
"""

import structlog
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from gao_dev.__version__ import __version__ as CURRENT_VERSION


logger = structlog.get_logger(__name__)


@dataclass
class CompatibilityResult:
    """
    Result of compatibility check.

    Attributes:
        status: "compatible", "needs_migration", or "incompatible"
        action: Recommended action ("continue", "migrate", "initialize", "error")
        message: Human-readable message
        from_version: Version being upgraded from (if applicable)
        to_version: Version being upgraded to (if applicable)
        migrations: List of migration names required (if any)
    """

    status: str
    action: str
    message: str = ""
    from_version: Optional[str] = None
    to_version: Optional[str] = None
    migrations: List[str] = None

    def __post_init__(self):
        if self.migrations is None:
            self.migrations = []


class VersionManager:
    """
    Manage version compatibility and migrations for GAO-Dev projects.

    Responsibilities:
    - Check if project version is compatible with current GAO-Dev version
    - Determine if migration is needed
    - Store and read project version from .gao-dev/version.txt
    """

    # Semantic version of GAO-Dev
    CURRENT_VERSION: str = CURRENT_VERSION

    # Minimum compatible version (older versions need migration)
    MIN_COMPATIBLE_VERSION: str = "0.9.0"

    def __init__(self):
        """Initialize version manager."""
        self.logger = logger.bind(
            component="VersionManager",
            current_version=self.CURRENT_VERSION,
        )

    def check_compatibility(self, project_path: Path) -> CompatibilityResult:
        """
        Check if project is compatible with current GAO-Dev version.

        Args:
            project_path: Path to user project directory

        Returns:
            CompatibilityResult with status and recommended action

        Status values:
        - "compatible": Project version matches or is compatible
        - "needs_migration": Project needs to be migrated to current version
        - "incompatible": Project version is too old or too new
        """
        gaodev_dir = project_path / ".gao-dev"

        # Check if project has been initialized
        if not gaodev_dir.exists():
            self.logger.info("project_not_initialized", path=str(project_path))
            return CompatibilityResult(
                status="compatible",
                action="initialize",
                message="New project - will initialize .gao-dev directory",
            )

        # Check for version file
        version_file = gaodev_dir / "version.txt"
        if not version_file.exists():
            # Legacy project without version file - assume needs migration
            self.logger.warning(
                "no_version_file",
                path=str(project_path),
                action="creating_version_file",
            )
            return CompatibilityResult(
                status="needs_migration",
                action="migrate",
                message="Legacy project detected - migration required",
                from_version="0.0.0",
                to_version=self.CURRENT_VERSION,
                migrations=self._get_required_migrations("0.0.0", self.CURRENT_VERSION),
            )

        # Read project version
        project_version = version_file.read_text().strip()
        self.logger.info(
            "checking_compatibility",
            project_version=project_version,
            current_version=self.CURRENT_VERSION,
        )

        # Check if project version is compatible
        if self._is_compatible(project_version, self.CURRENT_VERSION):
            self.logger.info("versions_compatible")
            return CompatibilityResult(
                status="compatible",
                action="continue",
                message=f"Project version {project_version} is compatible",
            )

        # Check if migration is possible
        if self._needs_migration(project_version, self.CURRENT_VERSION):
            migrations = self._get_required_migrations(project_version, self.CURRENT_VERSION)
            self.logger.info(
                "migration_required",
                migrations_count=len(migrations),
                migrations=migrations,
            )
            return CompatibilityResult(
                status="needs_migration",
                action="migrate",
                message=(
                    f"Project created with GAO-Dev {project_version}. "
                    f"Migration to {self.CURRENT_VERSION} is required."
                ),
                from_version=project_version,
                to_version=self.CURRENT_VERSION,
                migrations=migrations,
            )

        # Version is incompatible (too old or too new)
        self.logger.error(
            "version_incompatible",
            project_version=project_version,
            min_compatible=self.MIN_COMPATIBLE_VERSION,
        )
        return CompatibilityResult(
            status="incompatible",
            action="error",
            message=(
                f"Project created with GAO-Dev {project_version} which is incompatible "
                f"with current version {self.CURRENT_VERSION}.\n\n"
                f"Minimum compatible version: {self.MIN_COMPATIBLE_VERSION}\n\n"
                "Please either:\n"
                "  1. Update project manually\n"
                "  2. Use GAO-Dev version {project_version}\n"
                "  3. Create a new project"
            ),
        )

    def get_project_version(self, project_path: Path) -> Optional[str]:
        """
        Get version of GAO-Dev that created this project.

        Args:
            project_path: Path to user project

        Returns:
            Version string or None if not found
        """
        version_file = project_path / ".gao-dev" / "version.txt"
        if not version_file.exists():
            return None

        return version_file.read_text().strip()

    def set_project_version(self, project_path: Path, version: Optional[str] = None) -> None:
        """
        Set version of GAO-Dev for this project.

        Args:
            project_path: Path to user project
            version: Version string (defaults to current GAO-Dev version)
        """
        version = version or self.CURRENT_VERSION
        version_file = project_path / ".gao-dev" / "version.txt"

        # Ensure .gao-dev directory exists
        version_file.parent.mkdir(parents=True, exist_ok=True)

        version_file.write_text(version)
        self.logger.info("version_set", path=str(version_file), version=version)

    def _is_compatible(self, project_version: str, current_version: str) -> bool:
        """
        Check if project version is compatible with current version.

        Compatible means:
        - Exact version match, OR
        - Same MAJOR.MINOR version (PATCH can differ)

        Args:
            project_version: Version from project
            current_version: Current GAO-Dev version

        Returns:
            True if compatible
        """
        proj_major, proj_minor, proj_patch = self._parse_version(project_version)
        curr_major, curr_minor, curr_patch = self._parse_version(current_version)

        # Exact match
        if (proj_major, proj_minor, proj_patch) == (curr_major, curr_minor, curr_patch):
            return True

        # Same MAJOR.MINOR (different PATCH is OK)
        if (proj_major, proj_minor) == (curr_major, curr_minor):
            return True

        return False

    def _needs_migration(self, project_version: str, current_version: str) -> bool:
        """
        Check if project needs migration.

        Migration is needed if:
        - Project version is older than current version, AND
        - Project version is >= MIN_COMPATIBLE_VERSION

        Args:
            project_version: Version from project
            current_version: Current GAO-Dev version

        Returns:
            True if migration is needed
        """
        proj_major, proj_minor, proj_patch = self._parse_version(project_version)
        curr_major, curr_minor, curr_patch = self._parse_version(current_version)
        min_major, min_minor, min_patch = self._parse_version(self.MIN_COMPATIBLE_VERSION)

        # Check if project version >= MIN_COMPATIBLE_VERSION
        proj_tuple = (proj_major, proj_minor, proj_patch)
        min_tuple = (min_major, min_minor, min_patch)
        if proj_tuple < min_tuple:
            # Too old to migrate
            return False

        # Check if project version < current version
        curr_tuple = (curr_major, curr_minor, curr_patch)
        if proj_tuple < curr_tuple:
            # Migration needed
            return True

        return False

    def _get_required_migrations(self, from_version: str, to_version: str) -> List[str]:
        """
        Get list of migrations needed to upgrade from one version to another.

        Args:
            from_version: Starting version
            to_version: Target version

        Returns:
            List of migration names (e.g., ["migration_0_9_to_1_0", "migration_1_0_to_1_1"])
        """
        from_major, from_minor, from_patch = self._parse_version(from_version)
        to_major, to_minor, to_patch = self._parse_version(to_version)

        migrations = []

        # Example migration logic - can be expanded based on actual migrations
        if (from_major, from_minor) < (1, 0) and (to_major, to_minor) >= (1, 0):
            migrations.append("migration_0_x_to_1_0")

        if (from_major, from_minor) < (1, 1) and (to_major, to_minor) >= (1, 1):
            migrations.append("migration_1_0_to_1_1")

        return migrations

    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """
        Parse semantic version string into (major, minor, patch).

        Args:
            version: Version string (e.g., "1.2.3" or "v1.2.3-beta.1")

        Returns:
            Tuple of (major, minor, patch)

        Raises:
            ValueError: If version format is invalid
        """
        # Remove 'v' prefix if present
        clean_version = version.lstrip('v')

        # Split on '-' to remove suffix (e.g., -beta.1)
        base_version = clean_version.split('-')[0]

        # Parse major.minor.patch
        parts = base_version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")

        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
            return (major, minor, patch)
        except ValueError as e:
            raise ValueError(f"Invalid version numbers in {version}: {e}")
