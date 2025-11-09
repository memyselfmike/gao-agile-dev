"""Metadata extraction utilities for GAO-Dev.

This utility service provides methods for extracting metadata from file paths,
content, and workflow context. It uses regex patterns and path analysis to
extract structured metadata like feature names, epic/story numbers, and titles.

Design Pattern: Utility service with static/class methods
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import structlog

logger = structlog.get_logger()


class MetadataExtractor:
    """
    Utility for extracting metadata from paths and content.

    Provides static/class methods for parsing metadata without maintaining state.
    This utility is used by both Orchestrator and ArtifactManager for consistent
    metadata extraction across the system.

    Examples:
        >>> # Extract feature name from path
        >>> MetadataExtractor.extract_feature_name(Path("docs/features/sandbox-system/PRD.md"))
        "sandbox-system"

        >>> # Extract epic number
        >>> MetadataExtractor.extract_epic_number(Path("docs/epics/epic-22.md"))
        22

        >>> # Extract story number (returns tuple)
        >>> MetadataExtractor.extract_story_number(Path("docs/stories/epic-5/story-5.3.md"))
        (5, 3)

        >>> # Extract title from markdown
        >>> content = "# Epic 22: Orchestrator Decomposition\\n\\nContent here..."
        >>> MetadataExtractor.extract_title(content)
        "Epic 22: Orchestrator Decomposition"
    """

    # Regex patterns for metadata extraction
    FEATURE_PATTERN = re.compile(r'/features/([^/]+)/')
    EPIC_PATTERN = re.compile(r'epic-(\d+)')
    STORY_PATTERN = re.compile(r'story-(\d+)\.(\d+)')
    TITLE_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)

    @classmethod
    def extract_feature_name(cls, path: Path) -> Optional[str]:
        """
        Extract feature name from file path.

        Searches for the pattern "/features/{feature-name}/" in the path and
        extracts the feature name segment. This works for both absolute and
        relative paths.

        Args:
            path: File path to extract feature name from

        Returns:
            Feature name or None if not found

        Examples:
            >>> MetadataExtractor.extract_feature_name(Path("docs/features/sandbox-system/PRD.md"))
            "sandbox-system"

            >>> MetadataExtractor.extract_feature_name(Path("docs/features/git-wisdom/epics/epic-1.md"))
            "git-wisdom"

            >>> MetadataExtractor.extract_feature_name(Path("docs/PRD.md"))
            None
        """
        # Convert to string with forward slashes for consistent pattern matching
        path_str = str(path).replace('\\', '/')

        match = cls.FEATURE_PATTERN.search(path_str)
        if match:
            feature_name = match.group(1)
            logger.debug(
                "feature_name_extracted",
                path=str(path),
                feature_name=feature_name
            )
            return feature_name

        logger.debug(
            "feature_name_not_found",
            path=str(path)
        )
        return None

    @classmethod
    def extract_epic_number(cls, path: Path) -> Optional[int]:
        """
        Extract epic number from file path.

        Searches for the pattern "epic-{number}" in the path and extracts
        the numeric epic identifier. This works anywhere in the path.

        Args:
            path: File path to extract epic number from

        Returns:
            Epic number or None if not found

        Examples:
            >>> MetadataExtractor.extract_epic_number(Path("docs/epics/epic-5.md"))
            5

            >>> MetadataExtractor.extract_epic_number(Path("docs/features/x/epics/epic-22.md"))
            22

            >>> MetadataExtractor.extract_epic_number(Path("docs/PRD.md"))
            None
        """
        # Convert to string with forward slashes for consistent pattern matching
        path_str = str(path).replace('\\', '/')

        match = cls.EPIC_PATTERN.search(path_str)
        if match:
            epic_num = int(match.group(1))
            logger.debug(
                "epic_number_extracted",
                path=str(path),
                epic_number=epic_num
            )
            return epic_num

        logger.debug(
            "epic_number_not_found",
            path=str(path)
        )
        return None

    @classmethod
    def extract_story_number(cls, path: Path) -> Optional[Tuple[int, int]]:
        """
        Extract story number (epic, story) from file path.

        Searches for the pattern "story-{epic}.{story}" in the path and extracts
        both the epic and story numbers as a tuple.

        Args:
            path: File path to extract story number from

        Returns:
            (epic_num, story_num) tuple or None if not found

        Examples:
            >>> MetadataExtractor.extract_story_number(Path("docs/stories/epic-5/story-5.3.md"))
            (5, 3)

            >>> MetadataExtractor.extract_story_number(Path("docs/features/x/stories/epic-22/story-22.1.md"))
            (22, 1)

            >>> MetadataExtractor.extract_story_number(Path("docs/epics/epic-1.md"))
            None
        """
        # Convert to string with forward slashes for consistent pattern matching
        path_str = str(path).replace('\\', '/')

        match = cls.STORY_PATTERN.search(path_str)
        if match:
            epic_num = int(match.group(1))
            story_num = int(match.group(2))
            logger.debug(
                "story_number_extracted",
                path=str(path),
                epic_number=epic_num,
                story_number=story_num
            )
            return (epic_num, story_num)

        logger.debug(
            "story_number_not_found",
            path=str(path)
        )
        return None

    @classmethod
    def extract_title(cls, content: str) -> Optional[str]:
        """
        Extract document title from markdown content.

        Searches for the first H1 heading (# Title) in the content and
        extracts the title text. This is useful for parsing PRDs, epics,
        stories, and other markdown documents.

        Args:
            content: Markdown content to extract title from

        Returns:
            Title string or None if not found

        Examples:
            >>> content = "# Epic 22: Orchestrator Decomposition\\n\\nContent..."
            >>> MetadataExtractor.extract_title(content)
            "Epic 22: Orchestrator Decomposition"

            >>> content = "## Subtitle\\n\\nNo H1 heading here"
            >>> MetadataExtractor.extract_title(content)
            None

            >>> content = ""
            >>> MetadataExtractor.extract_title(content)
            None
        """
        if not content:
            return None

        match = cls.TITLE_PATTERN.search(content)
        if match:
            title = match.group(1).strip()
            logger.debug(
                "title_extracted",
                title=title,
                content_length=len(content)
            )
            return title

        logger.debug(
            "title_not_found",
            content_length=len(content)
        )
        return None
