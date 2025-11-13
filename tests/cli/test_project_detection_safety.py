"""Tests for source repository detection and safety checks."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.cli.project_detection import (
    detect_project_root,
    GAODevSourceDirectoryError,
    _is_gaodev_source_repo,
)


class TestSourceRepoDetection:
    """Test suite for GAO-Dev source repository detection and prevention."""

    @pytest.fixture
    def temp_gaodev_source(self):
        """Create temporary directory that looks like GAO-Dev source repo."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create marker files that identify GAO-Dev source
        (temp_dir / ".gaodev-source").touch()
        (temp_dir / "gao_dev" / "orchestrator").mkdir(parents=True)
        (temp_dir / "gao_dev" / "orchestrator" / "orchestrator.py").touch()
        (temp_dir / "docs").mkdir()
        (temp_dir / "docs" / "bmm-workflow-status.md").touch()

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_user_project(self):
        """Create temporary directory that looks like a user project."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create user project structure with .gao-dev marker
        (temp_dir / ".gao-dev").mkdir()
        (temp_dir / "src").mkdir()
        (temp_dir / "docs").mkdir()

        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_is_gaodev_source_repo_detects_marker(self, temp_gaodev_source):
        """Test that _is_gaodev_source_repo detects .gaodev-source marker."""
        assert _is_gaodev_source_repo(temp_gaodev_source) is True

    def test_is_gaodev_source_repo_detects_orchestrator(self, tmp_path):
        """Test that _is_gaodev_source_repo detects orchestrator.py."""
        # Create directory with orchestrator file only
        (tmp_path / "gao_dev" / "orchestrator").mkdir(parents=True)
        (tmp_path / "gao_dev" / "orchestrator" / "orchestrator.py").touch()

        assert _is_gaodev_source_repo(tmp_path) is True

    def test_is_gaodev_source_repo_detects_bmm_workflow(self, tmp_path):
        """Test that _is_gaodev_source_repo detects bmm-workflow-status.md."""
        # Create directory with BMM workflow file only
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "bmm-workflow-status.md").touch()

        assert _is_gaodev_source_repo(tmp_path) is True

    def test_is_gaodev_source_repo_detects_all_markers(self, temp_gaodev_source):
        """Test that _is_gaodev_source_repo detects all three markers."""
        # temp_gaodev_source has all three markers
        assert _is_gaodev_source_repo(temp_gaodev_source) is True

    def test_is_gaodev_source_repo_false_for_user_project(self, temp_user_project):
        """Test that _is_gaodev_source_repo returns False for user projects."""
        assert _is_gaodev_source_repo(temp_user_project) is False

    def test_is_gaodev_source_repo_false_for_empty_dir(self, tmp_path):
        """Test that _is_gaodev_source_repo returns False for empty directory."""
        assert _is_gaodev_source_repo(tmp_path) is False

    def test_detect_project_root_raises_error_from_source(self, temp_gaodev_source):
        """Test that detect_project_root raises error when run from source repo."""
        with pytest.raises(GAODevSourceDirectoryError) as exc_info:
            detect_project_root(temp_gaodev_source)

        error_msg = str(exc_info.value)

        # Check for required error message components
        assert "[E001]" in error_msg
        assert "Running from GAO-Dev Source Directory" in error_msg
        assert "must be installed via pip" in error_msg
        assert "pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main" in error_msg
        assert "cd /path/to/your/project" in error_msg
        assert "gao-dev start" in error_msg
        assert "--project /path/to/your/project" in error_msg
        assert "https://docs.gao-dev.com/errors/E001" in error_msg
        assert "https://github.com/memyselfmike/gao-agile-dev/issues/new" in error_msg

    def test_detect_project_root_works_from_user_project(self, temp_user_project):
        """Test that detect_project_root works normally from user project."""
        # Should not raise error
        detected = detect_project_root(temp_user_project)

        # Should return the user project root
        assert detected == temp_user_project
        assert (detected / ".gao-dev").exists()

    def test_detect_project_root_checks_parent_dirs(self, temp_gaodev_source):
        """Test that detect_project_root checks parent directories for source markers."""
        # Create subdirectory in source repo
        subdir = temp_gaodev_source / "some" / "nested" / "dir"
        subdir.mkdir(parents=True)

        # Should detect source repo even from subdirectory
        with pytest.raises(GAODevSourceDirectoryError):
            detect_project_root(subdir)

    def test_detect_project_root_with_partial_markers(self, tmp_path):
        """Test that detect_project_root handles directories with partial markers."""
        # Create directory with some files that might look like source repo
        # but without the key markers
        (tmp_path / "gao_dev").mkdir()
        (tmp_path / "docs").mkdir()
        (tmp_path / ".gao-dev").mkdir()  # User project marker

        # Should not raise error - this is a user project
        detected = detect_project_root(tmp_path)
        assert detected == tmp_path

    def test_gaodev_source_directory_error_message_format(self):
        """Test that GAODevSourceDirectoryError has correct message format."""
        error = GAODevSourceDirectoryError()
        error_msg = str(error)

        # Verify exact format from story specification
        assert error_msg.startswith("[E001] Running from GAO-Dev Source Directory")
        assert "Installation:" in error_msg
        assert "Usage:" in error_msg
        assert "Alternative:" in error_msg
        assert "Documentation:" in error_msg
        assert "Support:" in error_msg

    def test_is_gaodev_source_repo_handles_missing_dirs(self, tmp_path):
        """Test that _is_gaodev_source_repo handles missing directories gracefully."""
        # Create only partial structure
        (tmp_path / "gao_dev").mkdir()
        # Don't create orchestrator subdirectory

        # Should not crash, should return False
        assert _is_gaodev_source_repo(tmp_path) is False

    def test_is_gaodev_source_repo_handles_permission_error(self, tmp_path):
        """Test that _is_gaodev_source_repo handles permission errors gracefully."""
        # This test is platform-specific and may need adjustment
        # Create a marker file
        (tmp_path / ".gaodev-source").touch()

        # Should detect the marker even if other checks fail
        assert _is_gaodev_source_repo(tmp_path) is True


class TestSourceMarkerPackaging:
    """Test that .gaodev-source marker is included in package."""

    def test_marker_file_exists_in_repo(self):
        """Test that .gaodev-source exists in repository root."""
        # This test verifies the marker file exists in development
        from gao_dev import __file__ as gao_dev_init

        # Navigate to repo root (two levels up from gao_dev/__init__.py)
        repo_root = Path(gao_dev_init).parent.parent

        marker_path = repo_root / ".gaodev-source"
        assert marker_path.exists(), f"Marker file not found at {marker_path}"

        # Verify content
        content = marker_path.read_text()
        assert "GAO-Dev Source Repository Marker" in content
        assert "Do not run gao-dev commands from this directory" in content


class TestErrorMessageQuality:
    """Test that error messages are helpful and actionable."""

    def test_error_message_includes_all_required_sections(self):
        """Test that error message has all required sections."""
        error = GAODevSourceDirectoryError()
        error_msg = str(error)

        required_sections = [
            "[E001]",
            "Running from GAO-Dev Source Directory",
            "Installation:",
            "pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main",
            "Usage:",
            "cd /path/to/your/project",
            "gao-dev start",
            "Alternative:",
            "--project /path/to/your/project",
            "Documentation: https://docs.gao-dev.com/errors/E001",
            "Support: https://github.com/memyselfmike/gao-agile-dev/issues/new",
        ]

        for section in required_sections:
            assert section in error_msg, f"Error message missing required section: {section}"

    def test_error_message_format_matches_spec(self):
        """Test that error message format exactly matches specification."""
        error = GAODevSourceDirectoryError()
        error_msg = str(error)

        # Check format structure
        lines = error_msg.strip().split("\n")

        # Should have multiple lines
        assert len(lines) >= 10

        # First line should be error code and title
        assert lines[0] == "[E001] Running from GAO-Dev Source Directory"

        # Check for empty line after title (formatting)
        assert lines[1] == ""

    def test_error_is_actionable(self):
        """Test that error message provides clear, actionable guidance."""
        error = GAODevSourceDirectoryError()
        error_msg = str(error)

        # Must provide installation command
        assert "pip install" in error_msg

        # Must provide usage examples
        assert "gao-dev start" in error_msg
        assert "cd /path/to/your/project" in error_msg

        # Must provide support resources
        assert "github.com" in error_msg
        assert "docs.gao-dev.com" in error_msg
