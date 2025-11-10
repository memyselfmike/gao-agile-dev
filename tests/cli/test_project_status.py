"""Tests for ProjectStatusReporter."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil

from gao_dev.cli.project_status import ProjectStatusReporter, ProjectStatus
from gao_dev.core.state.models import Epic, Story


class TestAutoDetection:
    """Tests for project auto-detection."""

    def test_auto_detect_current_directory(self, tmp_path):
        """Test auto-detection in current directory."""
        # Create .gao-dev/ directory
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Change to project directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Auto-detect should find project
            reporter = ProjectStatusReporter()
            assert reporter.project_root == tmp_path
        finally:
            os.chdir(old_cwd)

    def test_auto_detect_parent_directory(self, tmp_path):
        """Test auto-detection in parent directory."""
        # Create .gao-dev/ in tmp_path
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Change to subdirectory
        old_cwd = os.getcwd()
        try:
            os.chdir(subdir)

            # Auto-detect should find project in parent
            reporter = ProjectStatusReporter()
            assert reporter.project_root == tmp_path
        finally:
            os.chdir(old_cwd)

    def test_auto_detect_multiple_levels(self, tmp_path):
        """Test auto-detection 3 levels up."""
        # Create .gao-dev/ in tmp_path
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Create nested subdirectories
        level1 = tmp_path / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()
        level3 = level2 / "level3"
        level3.mkdir()

        # Change to deepest directory
        old_cwd = os.getcwd()
        try:
            os.chdir(level3)

            # Auto-detect should find project 3 levels up
            reporter = ProjectStatusReporter()
            assert reporter.project_root == tmp_path
        finally:
            os.chdir(old_cwd)

    def test_auto_detect_not_found(self, tmp_path):
        """Test auto-detection when no project found."""
        # Don't create .gao-dev/
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Auto-detect should return None
            reporter = ProjectStatusReporter()
            assert reporter.project_root is None
        finally:
            os.chdir(old_cwd)

    def test_explicit_project_root(self, tmp_path):
        """Test explicit project root bypasses auto-detection."""
        # Create .gao-dev/ directory
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        # Provide explicit project root
        reporter = ProjectStatusReporter(project_root=tmp_path)
        assert reporter.project_root == tmp_path


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_greenfield_no_project(self, tmp_path):
        """Test status for greenfield project (no .gao-dev/)."""
        # Change to tmp_path to avoid detecting actual project
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            reporter = ProjectStatusReporter(project_root=None)
            status = reporter.get_status()

            assert status.exists is False
            assert status.is_greenfield is True
            assert status.epic_count == 0
            assert status.story_count == 0
        finally:
            os.chdir(old_cwd)

    def test_get_status_greenfield_no_database(self, tmp_path):
        """Test status when .gao-dev/ exists but no database."""
        # Create .gao-dev/ but no database
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()

        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = reporter.get_status()

        assert status.exists is True
        assert status.is_greenfield is True
        assert status.project_name == tmp_path.name

    @patch("gao_dev.cli.project_status.StateTracker")
    @patch("gao_dev.cli.project_status.GitManager")
    def test_get_status_with_project(self, mock_git_manager_class, mock_state_tracker_class, tmp_path):
        """Test status for existing project with data."""
        # Create .gao-dev/ and database
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()
        db_path = gao_dev_dir / "documents.db"
        db_path.touch()

        # Mock StateTracker
        mock_state_tracker = Mock()
        mock_state_tracker_class.return_value = mock_state_tracker

        # Mock epics
        mock_epic = Mock(spec=Epic)
        mock_epic.epic_num = 30
        mock_epic.title = "Interactive Brian Chat"
        mock_epic.status = "active"
        mock_epic.created_at = "2025-11-10T10:00:00"
        mock_state_tracker.get_active_epics.return_value = [mock_epic]
        mock_state_tracker.get_epic.return_value = mock_epic

        # Mock stories
        mock_story1 = Mock(spec=Story)
        mock_story1.epic = 30
        mock_story1.story_num = 1
        mock_story1.title = "Brian REPL Command"
        mock_story1.status = "done"

        mock_story2 = Mock(spec=Story)
        mock_story2.epic = 30
        mock_story2.story_num = 2
        mock_story2.title = "Project Auto-Detection"
        mock_story2.status = "in_progress"

        mock_state_tracker.get_stories_by_status.side_effect = [
            [],  # pending
            [mock_story2],  # in_progress
            [mock_story1],  # done
            [],  # blocked
            [],  # cancelled
        ]

        # Mock GitManager
        mock_git_manager = Mock()
        mock_git_manager_class.return_value = mock_git_manager
        mock_git_manager.get_commit_info.side_effect = [
            {"message": "feat(epic-30): Story 30.1 - Brian REPL Command"},
            {"message": "Merge Epic 29: Self-Learning Feedback Loop"},
            {"message": "feat(epic-29): Story 29.6 - Learning Decay"},
        ]

        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = reporter.get_status()

        assert status.exists is True
        assert status.is_greenfield is False
        assert status.project_name == tmp_path.name
        assert status.project_root == tmp_path
        assert status.epic_count == 1
        assert status.story_count == 2
        assert len(status.recent_commits) == 3
        assert status.current_epic == "Epic 30: Interactive Brian Chat"

    @patch("gao_dev.cli.project_status.StateTracker")
    @patch("gao_dev.cli.project_status.GitManager")
    def test_get_status_with_error(self, mock_git_manager_class, mock_state_tracker_class, tmp_path):
        """Test status when error occurs during query."""
        # Create .gao-dev/ and database
        gao_dev_dir = tmp_path / ".gao-dev"
        gao_dev_dir.mkdir()
        db_path = gao_dev_dir / "documents.db"
        db_path.touch()

        # Mock StateTracker to raise error
        mock_state_tracker_class.side_effect = Exception("Database error")

        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = reporter.get_status()

        # Should return minimal status on error
        assert status.exists is True
        assert status.project_name == tmp_path.name
        assert status.epic_count == 0
        assert status.story_count == 0


class TestStatusFormatting:
    """Tests for format_status method."""

    @patch("gao_dev.cli.greenfield_initializer.GreenfieldInitializer")
    def test_format_status_greenfield(self, mock_greenfield_init, tmp_path):
        """Test formatting for greenfield project."""
        # Create empty temp directory
        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = ProjectStatus(exists=False, is_greenfield=True)

        # Mock GreenfieldInitializer to return true greenfield
        mock_initializer = Mock()
        mock_initializer.detect_project_type.return_value = "greenfield"
        mock_greenfield_init.return_value = mock_initializer

        formatted = reporter.format_status(status)

        assert "No GAO-Dev project detected" in formatted
        assert "initialize a new project" in formatted
        assert "init" in formatted

    def test_format_status_unable_to_load(self, tmp_path):
        """Test formatting when unable to load status."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = ProjectStatus(exists=False, is_greenfield=False)

        formatted = reporter.format_status(status)

        assert "Unable to load project status" in formatted

    def test_format_status_with_project(self, tmp_path):
        """Test formatting for project with data."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = ProjectStatus(
            exists=True,
            project_name="my-project",
            project_root=tmp_path,
            epic_count=5,
            story_count=25,
            recent_commits=[
                "feat(epic-30): Story 30.1 - Brian REPL",
                "Merge Epic 29: Self-Learning",
                "feat(epic-29): Story 29.6 - Learning Decay",
            ],
            current_epic="Epic 30: Interactive Brian Chat",
            is_greenfield=False,
        )

        formatted = reporter.format_status(status)

        assert "Project: my-project" in formatted or "Project**: my-project" in formatted
        assert "Epics: 5" in formatted or "Epics**: 5" in formatted
        assert "Stories: 25" in formatted or "Stories**: 25" in formatted
        assert "Current Epic: Epic 30" in formatted or "Current Epic**: Epic 30" in formatted
        assert "Recent Activity" in formatted
        assert "feat(epic-30): Story 30.1 - Brian REPL" in formatted

    def test_format_status_minimal_project(self, tmp_path):
        """Test formatting for project with minimal data."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        status = ProjectStatus(
            exists=True,
            project_name="new-project",
            project_root=tmp_path,
            epic_count=0,
            story_count=0,
            recent_commits=[],
            current_epic=None,
            is_greenfield=False,
        )

        formatted = reporter.format_status(status)

        assert "Project: new-project" in formatted or "Project**: new-project" in formatted
        assert "Epics: 0" in formatted or "Epics**: 0" in formatted
        assert "Stories: 0" in formatted or "Stories**: 0" in formatted
        # Should not have current epic or recent activity sections
        assert "Current Epic:" not in formatted
        assert "Recent Activity:" not in formatted


class TestRecentCommits:
    """Tests for _get_recent_commits method."""

    def test_get_recent_commits_success(self, tmp_path):
        """Test getting recent commits successfully."""
        reporter = ProjectStatusReporter(project_root=tmp_path)

        # Mock GitManager
        mock_git_manager = Mock()
        mock_git_manager.get_commit_info.side_effect = [
            {"message": "feat: First commit\n\nDetails here"},
            {"message": "fix: Second commit"},
            {"message": "docs: Third commit"},
        ]

        commits = reporter._get_recent_commits(mock_git_manager, count=3)

        assert len(commits) == 3
        assert commits[0] == "feat: First commit"
        assert commits[1] == "fix: Second commit"
        assert commits[2] == "docs: Third commit"

    def test_get_recent_commits_fewer_available(self, tmp_path):
        """Test getting recent commits when fewer are available."""
        reporter = ProjectStatusReporter(project_root=tmp_path)

        # Mock GitManager - raise exception after 2 commits
        mock_git_manager = Mock()
        mock_git_manager.get_commit_info.side_effect = [
            {"message": "feat: First commit"},
            {"message": "fix: Second commit"},
            Exception("No more commits"),
        ]

        commits = reporter._get_recent_commits(mock_git_manager, count=5)

        assert len(commits) == 2
        assert commits[0] == "feat: First commit"
        assert commits[1] == "fix: Second commit"

    def test_get_recent_commits_error(self, tmp_path):
        """Test getting recent commits with error."""
        reporter = ProjectStatusReporter(project_root=tmp_path)

        # Mock GitManager - immediate error
        mock_git_manager = Mock()
        mock_git_manager.get_commit_info.side_effect = Exception("Git error")

        commits = reporter._get_recent_commits(mock_git_manager, count=5)

        assert commits == []


class TestCurrentEpic:
    """Tests for _determine_current_epic method."""

    def test_determine_current_epic_active(self, tmp_path):
        """Test determining current epic with active epic."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        epics = [
            {"epic_num": 29, "title": "Self-Learning", "status": "completed", "created_at": "2025-11-08"},
            {"epic_num": 30, "title": "Interactive Brian", "status": "active", "created_at": "2025-11-10"},
        ]

        current = reporter._determine_current_epic(epics)

        assert current == "Epic 30: Interactive Brian"

    def test_determine_current_epic_most_recent(self, tmp_path):
        """Test determining current epic when no active epic."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        epics = [
            {"epic_num": 28, "title": "Ceremony Integration", "status": "completed", "created_at": "2025-11-05"},
            {"epic_num": 29, "title": "Self-Learning", "status": "completed", "created_at": "2025-11-08"},
        ]

        current = reporter._determine_current_epic(epics)

        assert current == "Epic 29: Self-Learning"

    def test_determine_current_epic_no_epics(self, tmp_path):
        """Test determining current epic with no epics."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        epics = []

        current = reporter._determine_current_epic(epics)

        assert current is None

    def test_determine_current_epic_missing_created_at(self, tmp_path):
        """Test determining current epic with missing created_at."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        epics = [
            {"epic_num": 30, "title": "Interactive Brian", "status": "planned"},
        ]

        current = reporter._determine_current_epic(epics)

        # Should fall back to first epic
        assert current == "Epic 30: Interactive Brian"


class TestProjectName:
    """Tests for _get_project_name method."""

    def test_get_project_name_with_root(self, tmp_path):
        """Test getting project name with project root."""
        reporter = ProjectStatusReporter(project_root=tmp_path)
        name = reporter._get_project_name()

        assert name == tmp_path.name

    def test_get_project_name_without_root(self, tmp_path):
        """Test getting project name without project root."""
        # Change to tmp_path to avoid detecting actual project
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            reporter = ProjectStatusReporter(project_root=None)
            name = reporter._get_project_name()

            assert name == "Unknown"
        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
