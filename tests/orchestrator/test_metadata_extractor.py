"""Unit tests for MetadataExtractor utility.

Tests the metadata extraction utilities for feature names, epic numbers,
story numbers, and document titles from file paths and content.

Story: 22.5 - Extract MetadataExtractor Utility
"""

import pytest
from pathlib import Path

from gao_dev.orchestrator.metadata_extractor import MetadataExtractor


class TestExtractFeatureName:
    """Test feature name extraction from file paths."""

    def test_extract_feature_name_from_path(self):
        """Extract feature name from typical feature path."""
        path = Path("docs/features/sandbox-system/PRD.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result == "sandbox-system"

    def test_extract_feature_name_nested_path(self):
        """Extract feature name from nested feature path."""
        path = Path("docs/features/git-integrated-hybrid-wisdom/epics/epic-22.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result == "git-integrated-hybrid-wisdom"

    def test_extract_feature_name_missing(self):
        """Handle paths without feature directory."""
        path = Path("docs/PRD.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result is None

    def test_extract_feature_name_absolute_path(self):
        """Extract feature name from absolute path."""
        path = Path("/home/user/project/docs/features/my-feature/README.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result == "my-feature"

    def test_extract_feature_name_windows_path(self):
        """Extract feature name from Windows-style path."""
        path = Path(r"C:\Projects\gao-dev\docs\features\test-feature\epic-1.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result == "test-feature"


class TestExtractEpicNumber:
    """Test epic number extraction from file paths."""

    def test_extract_epic_number_from_path(self):
        """Extract epic number from typical epic path."""
        path = Path("docs/epics/epic-5.md")
        result = MetadataExtractor.extract_epic_number(path)
        assert result == 5

    def test_extract_epic_number_feature_path(self):
        """Extract epic number from feature epic path."""
        path = Path("docs/features/sandbox-system/epics/epic-22.md")
        result = MetadataExtractor.extract_epic_number(path)
        assert result == 22

    def test_extract_epic_number_missing(self):
        """Handle paths without epic number."""
        path = Path("docs/PRD.md")
        result = MetadataExtractor.extract_epic_number(path)
        assert result is None

    def test_extract_epic_number_large_number(self):
        """Extract large epic numbers correctly."""
        path = Path("docs/epics/epic-999.md")
        result = MetadataExtractor.extract_epic_number(path)
        assert result == 999

    def test_extract_epic_number_nested_story(self):
        """Extract epic number from story path."""
        path = Path("docs/features/x/stories/epic-18/story-18.1.md")
        result = MetadataExtractor.extract_epic_number(path)
        assert result == 18


class TestExtractStoryNumber:
    """Test story number extraction from file paths."""

    def test_extract_story_number_from_path(self):
        """Extract story number from typical story path."""
        path = Path("docs/stories/epic-5/story-5.3.md")
        result = MetadataExtractor.extract_story_number(path)
        assert result == (5, 3)

    def test_extract_story_number_feature_path(self):
        """Extract story number from feature story path."""
        path = Path("docs/features/git-wisdom/stories/epic-22/story-22.1.md")
        result = MetadataExtractor.extract_story_number(path)
        assert result == (22, 1)

    def test_extract_story_number_missing(self):
        """Handle paths without story number."""
        path = Path("docs/epics/epic-1.md")
        result = MetadataExtractor.extract_story_number(path)
        assert result is None

    def test_extract_story_number_large_numbers(self):
        """Extract large story numbers correctly."""
        path = Path("docs/stories/epic-99/story-99.42.md")
        result = MetadataExtractor.extract_story_number(path)
        assert result == (99, 42)

    def test_extract_story_number_single_digit(self):
        """Extract single-digit story numbers."""
        path = Path("docs/stories/epic-1/story-1.1.md")
        result = MetadataExtractor.extract_story_number(path)
        assert result == (1, 1)


class TestExtractTitle:
    """Test title extraction from markdown content."""

    def test_extract_title_from_markdown(self):
        """Extract title from markdown with H1 heading."""
        content = "# Epic 22: Orchestrator Decomposition\n\nContent here..."
        result = MetadataExtractor.extract_title(content)
        assert result == "Epic 22: Orchestrator Decomposition"

    def test_extract_title_missing(self):
        """Handle content without H1 heading."""
        content = "## Subtitle\n\nNo H1 heading here"
        result = MetadataExtractor.extract_title(content)
        assert result is None

    def test_extract_title_empty_content(self):
        """Handle empty content."""
        content = ""
        result = MetadataExtractor.extract_title(content)
        assert result is None

    def test_extract_title_with_leading_whitespace(self):
        """Extract title with leading/trailing whitespace."""
        content = "#   Story 5.3: Test Implementation   \n\nContent..."
        result = MetadataExtractor.extract_title(content)
        assert result == "Story 5.3: Test Implementation"

    def test_extract_title_multiple_h1(self):
        """Extract first H1 when multiple present."""
        content = "# First Title\n\nContent...\n\n# Second Title\n\nMore content..."
        result = MetadataExtractor.extract_title(content)
        assert result == "First Title"

    def test_extract_title_with_special_characters(self):
        """Extract title containing special characters."""
        content = "# PRD: My App (v2.0) - Phase 1 [DRAFT]\n\nContent..."
        result = MetadataExtractor.extract_title(content)
        assert result == "PRD: My App (v2.0) - Phase 1 [DRAFT]"


class TestMetadataExtractorEdgeCases:
    """Test edge cases and error handling."""

    def test_metadata_extractor_none_path(self):
        """Handle None as path input gracefully."""
        # Since Path(None) raises TypeError, we test with empty Path
        path = Path(".")
        result = MetadataExtractor.extract_feature_name(path)
        assert result is None

    def test_metadata_extractor_relative_path(self):
        """Handle relative paths correctly."""
        # Relative path needs /features/ pattern (not just features/)
        path = Path("docs/features/my-feature/doc.md")
        result = MetadataExtractor.extract_feature_name(path)
        assert result == "my-feature"

    def test_epic_and_story_in_same_path(self):
        """Extract both epic from path and story from path when both present."""
        path = Path("docs/features/x/stories/epic-22/story-22.5.md")

        epic = MetadataExtractor.extract_epic_number(path)
        story = MetadataExtractor.extract_story_number(path)

        assert epic == 22
        assert story == (22, 5)

    def test_feature_epic_story_all_present(self):
        """Extract all metadata when feature, epic, and story all present."""
        path = Path("docs/features/git-wisdom/stories/epic-22/story-22.5.md")

        feature = MetadataExtractor.extract_feature_name(path)
        epic = MetadataExtractor.extract_epic_number(path)
        story = MetadataExtractor.extract_story_number(path)

        assert feature == "git-wisdom"
        assert epic == 22
        assert story == (22, 5)


class TestMetadataPatterns:
    """Test regex pattern accuracy and reliability."""

    def test_feature_pattern_matches_kebab_case(self):
        """Feature pattern matches kebab-case names."""
        test_cases = [
            ("docs/features/my-feature/doc.md", "my-feature"),
            ("docs/features/feature-with-many-words/doc.md", "feature-with-many-words"),
            ("docs/features/f1/doc.md", "f1"),
        ]

        for path_str, expected in test_cases:
            result = MetadataExtractor.extract_feature_name(Path(path_str))
            assert result == expected, f"Failed for {path_str}"

    def test_epic_pattern_matches_numbers_only(self):
        """Epic pattern matches only numeric epic identifiers."""
        test_cases = [
            ("docs/epics/epic-1.md", 1),
            ("docs/epics/epic-99.md", 99),
            ("docs/epics/epic-1234.md", 1234),
        ]

        for path_str, expected in test_cases:
            result = MetadataExtractor.extract_epic_number(Path(path_str))
            assert result == expected, f"Failed for {path_str}"

    def test_story_pattern_matches_dotted_format(self):
        """Story pattern matches epic.story dotted format."""
        test_cases = [
            ("docs/stories/epic-1/story-1.1.md", (1, 1)),
            ("docs/stories/epic-22/story-22.5.md", (22, 5)),
            ("docs/stories/epic-99/story-99.99.md", (99, 99)),
        ]

        for path_str, expected in test_cases:
            result = MetadataExtractor.extract_story_number(Path(path_str))
            assert result == expected, f"Failed for {path_str}"

    def test_title_pattern_requires_h1(self):
        """Title pattern only matches H1 headings (single #)."""
        test_cases = [
            ("# H1 Title", "H1 Title"),
            ("## H2 Title", None),  # Should not match H2
            ("### H3 Title", None),  # Should not match H3
            ("#### H4 Title", None),  # Should not match H4
        ]

        for content, expected in test_cases:
            result = MetadataExtractor.extract_title(content)
            assert result == expected, f"Failed for {content}"
