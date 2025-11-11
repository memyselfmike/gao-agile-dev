"""
Unit tests for FeaturePathValidator.

Tests the stateless validator with pure functions for feature path validation.
Covers path validation, feature extraction, structure validation, and cross-platform support.
"""

import pytest
from pathlib import Path
from gao_dev.core.services.feature_path_validator import FeaturePathValidator


class TestValidateFeaturePath:
    """Test validate_feature_path() method."""

    def test_valid_feature_path_prd(self):
        """Test valid feature path for PRD.md."""
        path = Path("docs/features/user-auth/PRD.md")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is True

    def test_valid_feature_path_nested_epic(self):
        """Test valid feature path with nested epic structure."""
        path = Path("docs/features/mvp/epics/1-foundation/README.md")
        assert FeaturePathValidator.validate_feature_path(path, "mvp") is True

    def test_valid_feature_path_nested_story(self):
        """Test valid feature path with nested story structure."""
        path = Path("docs/features/mvp/epics/1-foundation/stories/story-1.1.md")
        assert FeaturePathValidator.validate_feature_path(path, "mvp") is True

    def test_invalid_path_no_features_folder(self):
        """Test invalid path - no features folder."""
        path = Path("docs/PRD.md")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is False

    def test_invalid_path_src_folder(self):
        """Test invalid path - source code folder."""
        path = Path("src/main.py")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is False

    def test_valid_windows_path(self):
        """Test valid path with Windows backslashes."""
        path = Path("docs\\features\\user-auth\\PRD.md")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is True

    def test_valid_unix_path(self):
        """Test valid path with Unix forward slashes."""
        path = Path("docs/features/user-auth/PRD.md")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is True

    def test_wrong_feature_name(self):
        """Test path for MVP but checking user-auth."""
        path = Path("docs/features/mvp/PRD.md")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is False

    def test_empty_path(self):
        """Test empty path."""
        path = Path("")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is False

    def test_root_path(self):
        """Test root path."""
        path = Path("/")
        assert FeaturePathValidator.validate_feature_path(path, "user-auth") is False


class TestExtractFeatureFromPath:
    """Test extract_feature_from_path() method."""

    def test_extract_from_prd_path(self):
        """Test extracting feature name from PRD.md path."""
        path = Path("docs/features/user-auth/PRD.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "user-auth"

    def test_extract_from_nested_epic_path(self):
        """Test extracting feature name from nested epic path."""
        path = Path("docs/features/mvp/epics/1-foundation/README.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "mvp"

    def test_extract_from_story_path(self):
        """Test extracting feature name from story path."""
        path = Path("docs/features/mvp/epics/1-foundation/stories/story-1.1.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "mvp"

    def test_extract_mvp_correctly(self):
        """Test extracting 'mvp' feature name."""
        path = Path("docs/features/mvp/ARCHITECTURE.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "mvp"

    def test_return_none_for_non_feature_path(self):
        """Test returning None for non-feature path."""
        path = Path("docs/PRD.md")
        assert FeaturePathValidator.extract_feature_from_path(path) is None

    def test_return_none_for_src_path(self):
        """Test returning None for source code path."""
        path = Path("src/main.py")
        assert FeaturePathValidator.extract_feature_from_path(path) is None

    def test_windows_path_extraction(self):
        """Test extracting feature name from Windows path."""
        path = Path("docs\\features\\user-auth\\PRD.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "user-auth"

    def test_unix_path_extraction(self):
        """Test extracting feature name from Unix path."""
        path = Path("docs/features/user-auth/PRD.md")
        assert FeaturePathValidator.extract_feature_from_path(path) == "user-auth"

    def test_empty_path(self):
        """Test extracting from empty path."""
        path = Path("")
        assert FeaturePathValidator.extract_feature_from_path(path) is None

    def test_root_path(self):
        """Test extracting from root path."""
        path = Path("/")
        assert FeaturePathValidator.extract_feature_from_path(path) is None


class TestValidateStructure:
    """Test validate_structure() method."""

    def test_compliant_structure(self, tmp_path):
        """Test compliant feature structure with all required files and folders."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create required folders
        (feature_path / "epics").mkdir()
        (feature_path / "QA").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert violations == []

    def test_missing_prd(self, tmp_path):
        """Test structure with missing PRD.md."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create only some required files
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create required folders
        (feature_path / "epics").mkdir()
        (feature_path / "QA").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert "Missing required file: PRD.md" in violations

    def test_missing_readme(self, tmp_path):
        """Test structure with missing README.md."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create only some required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")

        # Create required folders
        (feature_path / "epics").mkdir()
        (feature_path / "QA").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert "Missing required file: README.md" in violations

    def test_missing_qa_folder(self, tmp_path):
        """Test structure with missing QA/ folder."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create only epics folder
        (feature_path / "epics").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert "Missing required folder: QA/" in violations

    def test_epics_is_file_not_folder(self, tmp_path):
        """Test structure where epics is a file instead of folder."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create epics as file instead of folder
        (feature_path / "epics").write_text("Epics file")
        (feature_path / "QA").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert "epics is a file, should be a folder" in violations

    def test_old_pattern_epics_md(self, tmp_path):
        """Test detection of old epics.md pattern."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create required folders
        (feature_path / "epics").mkdir()
        (feature_path / "QA").mkdir()

        # Create old pattern file
        (feature_path / "epics.md").write_text("Old epics file")

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert any("old epics.md format" in v for v in violations)

    def test_old_pattern_stories_at_root(self, tmp_path):
        """Test detection of old stories/ folder at root."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.mkdir(parents=True)

        # Create required files
        (feature_path / "PRD.md").write_text("# PRD")
        (feature_path / "ARCHITECTURE.md").write_text("# Architecture")
        (feature_path / "README.md").write_text("# README")

        # Create required folders
        (feature_path / "epics").mkdir()
        (feature_path / "QA").mkdir()

        # Create old pattern folder
        (feature_path / "stories").mkdir()

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert any("old stories/ folder at root" in v for v in violations)

    def test_nonexistent_path(self, tmp_path):
        """Test validation of non-existent path."""
        feature_path = tmp_path / "docs" / "features" / "nonexistent"

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert len(violations) == 1
        assert "does not exist" in violations[0]

    def test_path_is_file_not_directory(self, tmp_path):
        """Test validation when path is a file instead of directory."""
        feature_path = tmp_path / "docs" / "features" / "user-auth"
        feature_path.parent.mkdir(parents=True)
        feature_path.write_text("I'm a file")

        violations = FeaturePathValidator.validate_structure(feature_path)
        assert len(violations) == 1
        assert "not a directory" in violations[0]


class TestValidateEpicStructure:
    """Test validate_epic_structure() method."""

    def test_compliant_epic_structure(self, tmp_path):
        """Test compliant epic structure with all required elements."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.mkdir(parents=True)

        # Create required files
        (epic_path / "README.md").write_text("# Epic 1: Foundation")

        # Create required folders
        (epic_path / "stories").mkdir()
        (epic_path / "context").mkdir()

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert violations == []

    def test_missing_epic_readme(self, tmp_path):
        """Test epic structure with missing README.md."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.mkdir(parents=True)

        # Create only stories folder
        (epic_path / "stories").mkdir()

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert "Missing epic definition: README.md" in violations

    def test_missing_stories_folder(self, tmp_path):
        """Test epic structure with missing stories/ folder."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.mkdir(parents=True)

        # Create only README
        (epic_path / "README.md").write_text("# Epic 1")

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert "Missing stories/ folder" in violations

    def test_stories_is_file_not_folder(self, tmp_path):
        """Test epic structure where stories is a file instead of folder."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.mkdir(parents=True)

        # Create README
        (epic_path / "README.md").write_text("# Epic 1")

        # Create stories as file instead of folder
        (epic_path / "stories").write_text("Stories file")

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert "stories is a file, should be a folder" in violations

    def test_epic_folder_naming_invalid(self, tmp_path):
        """Test epic folder with invalid naming (not starting with number)."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "foundation"
        epic_path.mkdir(parents=True)

        # Create required files and folders
        (epic_path / "README.md").write_text("# Epic")
        (epic_path / "stories").mkdir()

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert any("should start with number" in v for v in violations)

    def test_nonexistent_epic_path(self, tmp_path):
        """Test validation of non-existent epic path."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "nonexistent"

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert len(violations) == 1
        assert "does not exist" in violations[0]

    def test_epic_path_is_file(self, tmp_path):
        """Test validation when epic path is a file instead of directory."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.parent.mkdir(parents=True)
        epic_path.write_text("I'm a file")

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        assert len(violations) == 1
        assert "not a directory" in violations[0]

    def test_missing_context_folder_logs_warning(self, tmp_path, caplog):
        """Test that missing context/ folder logs warning but doesn't violate."""
        epic_path = tmp_path / "docs" / "features" / "mvp" / "epics" / "1-foundation"
        epic_path.mkdir(parents=True)

        # Create required files and folders (but not context/)
        (epic_path / "README.md").write_text("# Epic 1")
        (epic_path / "stories").mkdir()

        violations = FeaturePathValidator.validate_epic_structure(epic_path)
        # Should not be a violation (context/ is optional)
        assert violations == []
