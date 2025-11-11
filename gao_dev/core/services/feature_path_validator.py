"""
Stateless validator for feature-based paths.

This module provides pure functions for validating feature paths without requiring
database queries or service dependencies. The stateless design breaks circular
dependencies between FeatureRegistry and DocumentLifecycleManager.

All validation methods are static - no instance state required.
"""

from pathlib import Path
from typing import Optional, List
import structlog

logger = structlog.get_logger(__name__)


class FeaturePathValidator:
    """
    Stateless validator for feature paths.

    Uses pure functions (no database queries, no dependencies).
    Breaks circular dependency between FeatureRegistry and DocumentLifecycleManager.

    All methods are static - no instance state required.
    """

    @staticmethod
    def validate_feature_path(path: Path, feature_name: str) -> bool:
        """
        Validate path matches feature pattern.

        Args:
            path: Path to validate (e.g., docs/features/user-auth/PRD.md)
            feature_name: Expected feature name (e.g., "user-auth")

        Returns:
            True if path matches docs/features/{feature_name}/... pattern

        Examples:
            >>> FeaturePathValidator.validate_feature_path(
            ...     Path("docs/features/user-auth/PRD.md"), "user-auth"
            ... )
            True

            >>> FeaturePathValidator.validate_feature_path(
            ...     Path("docs/PRD.md"), "user-auth"
            ... )
            False

            >>> FeaturePathValidator.validate_feature_path(
            ...     Path("docs/features/mvp/epics/1-foundation/README.md"), "mvp"
            ... )
            True
        """
        # Normalize path (cross-platform)
        normalized = str(path).replace("\\", "/")

        # Check if path starts with docs/features/{feature_name}/
        expected_prefix = f"docs/features/{feature_name}/"
        return normalized.startswith(expected_prefix)

    @staticmethod
    def extract_feature_from_path(path: Path) -> Optional[str]:
        """
        Extract feature name from path.

        Args:
            path: Path to extract from

        Returns:
            Feature name or None if not feature-scoped

        Examples:
            >>> FeaturePathValidator.extract_feature_from_path(
            ...     Path("docs/features/user-auth/PRD.md")
            ... )
            'user-auth'

            >>> FeaturePathValidator.extract_feature_from_path(
            ...     Path("docs/features/mvp/epics/1-foundation/README.md")
            ... )
            'mvp'

            >>> FeaturePathValidator.extract_feature_from_path(Path("docs/PRD.md"))
            >>> # Returns None

            >>> FeaturePathValidator.extract_feature_from_path(Path("src/main.py"))
            >>> # Returns None
        """
        parts = path.parts

        # Check if path follows docs/features/{name}/... pattern
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "features":
            return parts[2]

        return None

    @staticmethod
    def validate_structure(feature_path: Path) -> List[str]:
        """
        Validate feature folder structure.

        Args:
            feature_path: Path to feature folder (e.g., docs/features/user-auth)

        Returns:
            List of violation messages (empty list if compliant)

        Checks:
        - Required files exist: PRD.md, ARCHITECTURE.md, README.md
        - Required folders exist: epics/, QA/
        - epics/ is a folder (not epics.md file)
        - No old patterns (epics.md, stories/ at root)

        Examples:
            >>> FeaturePathValidator.validate_structure(
            ...     Path("docs/features/user-auth")
            ... )
            []  # Compliant

            >>> FeaturePathValidator.validate_structure(
            ...     Path("docs/features/incomplete")
            ... )
            ['Missing required file: README.md', 'Missing required folder: QA/']
        """
        violations = []

        # Check feature path exists
        if not feature_path.exists():
            return [f"Feature path does not exist: {feature_path}"]

        if not feature_path.is_dir():
            return [f"Feature path is not a directory: {feature_path}"]

        # Check required files
        required_files = ["PRD.md", "ARCHITECTURE.md", "README.md"]
        for required_file in required_files:
            file_path = feature_path / required_file
            if not file_path.exists():
                violations.append(f"Missing required file: {required_file}")

        # Check required folders
        required_folders = ["epics", "QA"]
        for required_folder in required_folders:
            folder_path = feature_path / required_folder
            if not folder_path.exists():
                violations.append(f"Missing required folder: {required_folder}/")
            elif not folder_path.is_dir():
                violations.append(
                    f"{required_folder} is a file, should be a folder"
                )

        # Check for old patterns
        if (feature_path / "epics.md").exists():
            violations.append(
                "Using old epics.md format (should be epics/ folder with co-located stories)"
            )

        if (feature_path / "stories").exists() and (feature_path / "stories").is_dir():
            violations.append(
                "Using old stories/ folder at root (stories should be co-located inside epics/{epic-name}/stories/)"
            )

        return violations

    @staticmethod
    def validate_epic_structure(epic_path: Path) -> List[str]:
        """
        Validate epic folder structure (co-located pattern).

        Args:
            epic_path: Path to epic folder (e.g., docs/features/mvp/epics/1-foundation)

        Returns:
            List of violation messages (empty if compliant)

        Checks:
        - Epic folder follows {number}-{name} pattern
        - README.md exists (epic definition)
        - stories/ folder exists
        - context/ folder exists (optional but recommended)

        Examples:
            >>> FeaturePathValidator.validate_epic_structure(
            ...     Path("docs/features/mvp/epics/1-foundation")
            ... )
            []  # Compliant
        """
        violations = []

        # Check epic path exists
        if not epic_path.exists():
            return [f"Epic path does not exist: {epic_path}"]

        if not epic_path.is_dir():
            return [f"Epic path is not a directory: {epic_path}"]

        # Check epic folder naming (should be {number}-{name})
        epic_folder_name = epic_path.name
        if not epic_folder_name[0].isdigit():
            violations.append(
                f"Epic folder should start with number: {epic_folder_name} "
                "(expected format: 1-epic-name)"
            )

        # Check required files
        if not (epic_path / "README.md").exists():
            violations.append("Missing epic definition: README.md")

        # Check required folders
        if not (epic_path / "stories").exists():
            violations.append("Missing stories/ folder")
        elif not (epic_path / "stories").is_dir():
            violations.append("stories is a file, should be a folder")

        # Optional but recommended
        if not (epic_path / "context").exists():
            logger.warning(
                "No context/ folder (optional but recommended for context XML files)",
                epic_path=str(epic_path)
            )

        return violations
