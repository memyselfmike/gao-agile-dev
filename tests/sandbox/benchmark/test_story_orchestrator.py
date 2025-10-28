"""Tests for story-based workflow orchestration."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import pytest

from gao_dev.sandbox.benchmark.story_orchestrator import (
    StoryOrchestrator,
    StoryResult,
    EpicResult,
    StoryStatus,
)
from gao_dev.sandbox.benchmark.config import StoryConfig, EpicConfig


class TestStoryOrchestrator:
    """Tests for StoryOrchestrator class."""

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temporary project path."""
        return tmp_path / "test_project"

    @pytest.fixture
    def mock_git_manager(self):
        """Create mock GitManager."""
        manager = Mock()
        manager.create_commit.return_value = {
            "hash": "abc1234",
            "files_changed": ["file1.py", "file2.py"],
        }
        return manager

    @pytest.fixture
    def orchestrator(self, temp_project_path, mock_git_manager):
        """Create StoryOrchestrator instance."""
        return StoryOrchestrator(
            project_path=temp_project_path,
            git_manager=mock_git_manager,
        )

    @pytest.fixture
    def sample_story(self):
        """Create sample story config."""
        return StoryConfig(
            name="Test Story",
            agent="Amelia",
            description="Test story description",
            acceptance_criteria=["Criteria 1", "Criteria 2"],
            story_points=3,
        )

    @pytest.fixture
    def sample_epic(self, sample_story):
        """Create sample epic config."""
        return EpicConfig(
            name="Test Epic",
            description="Test epic description",
            stories=[sample_story],
        )

    def test_init_creates_orchestrator(self, temp_project_path):
        """Test orchestrator initialization."""
        orchestrator = StoryOrchestrator(project_path=temp_project_path)

        assert orchestrator.project_path == temp_project_path
        assert orchestrator.logger is not None

    def test_execute_story_success(self, orchestrator, sample_story):
        """Test successful story execution."""
        result = orchestrator.execute_story(sample_story, "Test Epic")

        assert result.story_name == "Test Story"
        assert result.epic_name == "Test Epic"
        assert result.agent == "Amelia"
        assert result.status == StoryStatus.COMPLETED
        assert result.duration_seconds > 0
        assert len(result.acceptance_criteria_met) > 0

    def test_execute_story_creates_commit(
        self, orchestrator, sample_story, mock_git_manager
    ):
        """Test that story execution creates git commit."""
        result = orchestrator.execute_story(sample_story, "Test Epic")

        # Verify commit was created
        mock_git_manager.create_commit.assert_called_once()
        call_args = mock_git_manager.create_commit.call_args
        assert "feat(test-epic)" in call_args[1]["message"]
        assert result.commit_hash == "abc1234"

    def test_execute_epic_success(self, orchestrator, sample_epic):
        """Test successful epic execution."""
        result = orchestrator.execute_epic(sample_epic)

        assert result.epic_name == "Test Epic"
        assert result.total_stories == 1
        assert result.completed_stories == 1
        assert result.failed_stories == 0
        assert result.success is True

    def test_execute_epic_with_multiple_stories(self, orchestrator):
        """Test epic with multiple stories."""
        epic = EpicConfig(
            name="Multi-Story Epic",
            description="Epic with multiple stories",
            stories=[
                StoryConfig(name="Story 1", agent="Amelia", story_points=3),
                StoryConfig(name="Story 2", agent="Bob", story_points=5),
                StoryConfig(name="Story 3", agent="Murat", story_points=2),
            ],
        )

        result = orchestrator.execute_epic(epic)

        assert result.total_stories == 3
        assert result.completed_stories == 3
        assert len(result.story_results) == 3

    def test_execute_epics_multiple(self, orchestrator):
        """Test executing multiple epics."""
        epics = [
            EpicConfig(
                name="Epic 1",
                description="First epic",
                stories=[StoryConfig(name="Story 1.1", agent="Amelia")],
            ),
            EpicConfig(
                name="Epic 2",
                description="Second epic",
                stories=[StoryConfig(name="Story 2.1", agent="Bob")],
            ),
        ]

        results = orchestrator.execute_epics(epics)

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_story_result_to_dict(self):
        """Test StoryResult serialization."""
        result = StoryResult(
            story_name="Test",
            epic_name="Epic",
            agent="Amelia",
            status=StoryStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        result_dict = result.to_dict()

        assert result_dict["story_name"] == "Test"
        assert result_dict["status"] == "completed"
        assert "start_time" in result_dict
        assert "end_time" in result_dict

    def test_epic_result_to_dict(self, sample_story):
        """Test EpicResult serialization."""
        story_result = StoryResult(
            story_name="Test",
            epic_name="Epic",
            agent="Amelia",
            status=StoryStatus.COMPLETED,
            start_time=datetime.now(),
        )

        epic_result = EpicResult(
            epic_name="Test Epic",
            story_results=[story_result],
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        epic_dict = epic_result.to_dict()

        assert epic_dict["epic_name"] == "Test Epic"
        assert len(epic_dict["story_results"]) == 1
        assert epic_dict["completed_stories"] == 1
        assert epic_dict["success"] is True

    def test_commit_message_generation(self, orchestrator, sample_story):
        """Test conventional commit message generation."""
        result = StoryResult(
            story_name="Test Story",
            epic_name="User Auth",
            agent="Amelia",
            status=StoryStatus.COMPLETED,
            start_time=datetime.now(),
        )

        message = orchestrator._generate_commit_message(sample_story, result)

        assert "feat(user-auth)" in message
        assert "Test Story" in message
        assert "Story Points: 3" in message
        assert "🤖 Generated with GAO-Dev" in message

    def test_story_phases_executed_in_order(self, orchestrator, sample_story):
        """Test that story phases execute in correct order."""
        with patch.object(
            orchestrator, "_execute_story_creation"
        ) as mock_create, patch.object(
            orchestrator, "_execute_story_implementation"
        ) as mock_implement, patch.object(
            orchestrator, "_execute_story_validation"
        ) as mock_validate, patch.object(
            orchestrator, "_execute_story_commit"
        ) as mock_commit:

            orchestrator.execute_story(sample_story, "Test Epic")

            # Verify all phases were called
            mock_create.assert_called_once()
            mock_implement.assert_called_once()
            mock_validate.assert_called_once()
            mock_commit.assert_called_once()

    def test_epic_stops_on_first_failure(self, orchestrator):
        """Test that epic stops on first story failure."""
        # Create epic with multiple stories
        epic = EpicConfig(
            name="Test Epic",
            description="Test",
            stories=[
                StoryConfig(name="Story 1", agent="Amelia"),
                StoryConfig(name="Story 2", agent="Bob"),
                StoryConfig(name="Story 3", agent="Murat"),
            ],
        )

        # Mock the execute_story to fail on second story
        original_execute = orchestrator.execute_story

        def mock_execute_story(story, epic_name, timeout=None):
            result = original_execute(story, epic_name, timeout)
            if story.name == "Story 2":
                result.status = StoryStatus.FAILED
                result.error_message = "Test failure"
            return result

        with patch.object(
            orchestrator, "execute_story", side_effect=mock_execute_story
        ):
            epic_result = orchestrator.execute_epic(epic)

            # Should have 3 results (1 completed, 1 failed, 1 skipped)
            assert epic_result.total_stories == 3
            assert epic_result.completed_stories == 1
            assert epic_result.failed_stories == 1
            # Story 3 should be skipped
            assert epic_result.story_results[2].status == StoryStatus.SKIPPED

    def test_orchestrator_without_git_manager(self, temp_project_path, sample_story):
        """Test orchestrator works without git manager."""
        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            git_manager=None,  # No git manager
        )

        result = orchestrator.execute_story(sample_story, "Test Epic")

        # Should still complete successfully
        assert result.status == StoryStatus.COMPLETED
        # But no commit hash
        assert result.commit_hash is None


class TestStoryStatus:
    """Tests for StoryStatus enum."""

    def test_status_values(self):
        """Test story status values."""
        assert StoryStatus.PENDING.value == "pending"
        assert StoryStatus.IN_PROGRESS.value == "in_progress"
        assert StoryStatus.COMPLETED.value == "completed"
        assert StoryStatus.FAILED.value == "failed"
        assert StoryStatus.SKIPPED.value == "skipped"


class TestIntegration:
    """Integration tests for story orchestration."""

    @pytest.fixture
    def real_project_path(self, tmp_path):
        """Create real project directory."""
        project_path = tmp_path / "integration_test"
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def test_full_story_workflow(self, real_project_path):
        """Test complete story workflow from start to finish."""
        from gao_dev.core.git_manager import GitManager

        # Initialize git repo
        git_manager = GitManager(real_project_path)
        git_manager.init_repo(initial_commit=True)

        # Create a test file to commit
        test_file = real_project_path / "test_feature.py"
        test_file.write_text("# New feature implementation\nprint('hello')\n")

        # Create orchestrator
        orchestrator = StoryOrchestrator(
            project_path=real_project_path,
            git_manager=git_manager,
        )

        # Create story
        story = StoryConfig(
            name="Implement feature X",
            agent="Amelia",
            description="Add new feature",
            acceptance_criteria=["Feature works", "Tests pass"],
            story_points=5,
        )

        # Execute story
        result = orchestrator.execute_story(story, "Feature Epic")

        # Verify result
        assert result.status == StoryStatus.COMPLETED
        assert result.commit_hash is not None  # Should have commit hash
        assert result.duration_seconds > 0
        assert len(result.artifacts_created) > 0  # Should have committed files

        # Verify git commit was created
        status = git_manager.get_status()
        assert status["has_commits"] is True
        assert status["clean"] is True  # All committed


class TestCommitAutomation:
    """Tests for incremental commit automation (Story 6.4)."""

    @pytest.fixture
    def temp_project_path(self, tmp_path):
        """Create temp project path."""
        return tmp_path / "commit_test"

    @pytest.fixture
    def git_manager(self, temp_project_path):
        """Create real GitManager."""
        from gao_dev.core.git_manager import GitManager

        temp_project_path.mkdir(parents=True, exist_ok=True)
        manager = GitManager(temp_project_path)
        manager.init_repo(initial_commit=True)
        return manager

    def test_auto_commit_after_story_completion(self, temp_project_path, git_manager):
        """Test that story automatically commits after completion."""
        # Create test file
        test_file = temp_project_path / "feature.py"
        test_file.write_text("# Feature code\n")

        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            git_manager=git_manager,
        )

        story = StoryConfig(name="Add feature", agent="Amelia", story_points=3)
        result = orchestrator.execute_story(story, "Test Epic")

        # Verify auto-commit occurred
        assert result.status == StoryStatus.COMPLETED
        assert result.commit_hash is not None
        assert len(result.artifacts_created) > 0

    def test_conventional_commit_format(self, temp_project_path):
        """Test that commit follows conventional format."""
        orchestrator = StoryOrchestrator(project_path=temp_project_path)

        story = StoryConfig(
            name="User Login",
            agent="Amelia",
            description="Implement user auth",
            story_points=5,
        )

        result = StoryResult(
            story_name="User Login",
            epic_name="Authentication System",
            agent="Amelia",
            status=StoryStatus.COMPLETED,
            start_time=datetime.now(),
        )

        message = orchestrator._generate_commit_message(story, result)

        # Verify conventional format
        assert message.startswith("feat(authentication-system)")
        assert "User Login" in message
        assert "Story Points: 5" in message
        assert "🤖 Generated with GAO-Dev" in message
        assert "Co-Authored-By: Claude" in message

    def test_commit_metadata_tracked(self, temp_project_path, git_manager):
        """Test that commit metadata is properly tracked."""
        test_file = temp_project_path / "test.py"
        test_file.write_text("print('test')\n")

        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            git_manager=git_manager,
        )

        story = StoryConfig(name="Test Story", agent="Amelia")
        result = orchestrator.execute_story(story, "Epic")

        # Verify metadata
        assert result.commit_hash is not None
        assert isinstance(result.commit_hash, str)
        assert len(result.commit_hash) > 0
        assert "test.py" in result.artifacts_created
        assert result.duration_seconds > 0

    def test_robust_error_handling_on_commit_failure(self, temp_project_path):
        """Test that commit failures don't break story execution."""
        # Mock git manager that fails
        mock_git = Mock()
        mock_git.create_commit.side_effect = Exception("Git error")

        orchestrator = StoryOrchestrator(
            project_path=temp_project_path,
            git_manager=mock_git,
        )

        story = StoryConfig(name="Test", agent="Amelia")
        result = orchestrator.execute_story(story, "Epic")

        # Story should still complete
        assert result.status == StoryStatus.COMPLETED
        # But no commit hash
        assert result.commit_hash is None
        # Warning logged in metadata
        assert "commit_warning" in result.metadata
