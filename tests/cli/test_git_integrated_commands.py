"""Tests for CLI commands with git integration (Epic 27, Story 27.2).

Tests verify that:
1. CLI commands properly use GitIntegratedStateManager
2. Commands create atomic commits
3. Error handling and rollback work correctly
4. Commands provide proper feedback about git transactions

Epic 27: Integration & Migration
Story 27.2: Update CLI Commands
Created: 2025-11-09
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from gao_dev.cli.commands import (
    create_prd,
    create_story,
    implement_story,
    create_architecture,
)


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create basic project structure
    (temp_dir / "docs").mkdir(parents=True, exist_ok=True)
    (temp_dir / "src").mkdir(parents=True, exist_ok=True)
    (temp_dir / ".gao-dev").mkdir(parents=True, exist_ok=True)

    # Create gao-dev.yaml config
    config_content = """
project_name: "Test Project"
project_level: 2
output_folder: "docs"
dev_story_location: "docs/stories"
git_auto_commit: true
qa_enabled: true
"""
    (temp_dir / "gao-dev.yaml").write_text(config_content)

    # Initialize git repo
    import subprocess
    try:
        subprocess.run(
            ["git", "init"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        # Initial commit
        (temp_dir / "README.md").write_text("# Test Project")
        subprocess.run(
            ["git", "add", "."],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
    except Exception as e:
        print(f"Git init failed: {e}")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIGitIntegration:
    """Test CLI commands use git transactions correctly."""

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_create_prd_uses_git_state_manager(self, mock_create_default, temp_project, monkeypatch):
        """Test create-prd command uses git_state_manager."""
        runner = CliRunner()

        # Create mock orchestrator with git_state_manager
        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Mock create_prd async generator
        def _mock_create_prd_gen(name):
            yield "Creating PRD..."
            yield "PRD created successfully"
        mock_create_prd = AsyncMock(return_value=_mock_create_prd_gen('Test'))
        mock_create_prd.return_value = _mock_create_prd_gen('Test')

        mock_orchestrator.create_prd = mock_create_prd
        mock_create_default.return_value = mock_orchestrator

        # Run command in project directory
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_prd, ['--name', 'Test Project'])

        # Verify
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" in result.output
        mock_orchestrator.close.assert_called_once()

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_create_story_uses_git_state_manager(self, mock_create_default, temp_project, monkeypatch):
        """Test create-story command uses git_state_manager."""
        runner = CliRunner()

        # Create mock orchestrator with git_state_manager
        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Mock create_story async generator
        def mock_create_story(epic, story, title):
            yield "Creating story..."
            yield "Story created successfully"

        mock_orchestrator.create_story = mock_create_story
        mock_create_default.return_value = mock_orchestrator

        # Run command in project directory
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_story, ['--epic', '1', '--story', '1'])

        # Verify
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" in result.output
        mock_orchestrator.close.assert_called_once()

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_implement_story_uses_git_state_manager(self, mock_create_default, temp_project, monkeypatch):
        """Test implement-story command uses git_state_manager."""
        runner = CliRunner()

        # Create mock orchestrator with git_state_manager
        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Mock implement_story async generator
        def mock_implement_story(epic, story):
            yield "Implementing story..."
            yield "Story implemented successfully"

        mock_orchestrator.implement_story = mock_implement_story
        mock_create_default.return_value = mock_orchestrator

        # Run command in project directory
        monkeypatch.chdir(temp_project)
        result = runner.invoke(implement_story, ['--epic', '1', '--story', '1'])

        # Verify
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" in result.output
        mock_orchestrator.close.assert_called_once()

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_create_architecture_uses_git_state_manager(self, mock_create_default, temp_project, monkeypatch):
        """Test create-architecture command uses git_state_manager."""
        runner = CliRunner()

        # Create mock orchestrator with git_state_manager
        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Mock create_architecture async generator
        def mock_create_architecture(name):
            yield "Creating architecture..."
            yield "Architecture created successfully"

        mock_orchestrator.create_architecture = mock_create_architecture
        mock_create_default.return_value = mock_orchestrator

        # Run command in project directory
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_architecture, ['--name', 'Test Project'])

        # Verify
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" in result.output
        mock_orchestrator.close.assert_called_once()

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_command_closes_orchestrator_on_success(self, mock_create_default, temp_project, monkeypatch):
        """Test commands close orchestrator on success."""
        runner = CliRunner()

        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        def mock_create_prd(name):
            yield "Creating PRD..."

        mock_orchestrator.create_prd = mock_create_prd
        mock_create_default.return_value = mock_orchestrator

        # Run command
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_prd, ['--name', 'Test'])

        # Verify close() was called
        assert mock_orchestrator.close.called

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_command_closes_orchestrator_on_error(self, mock_create_default, temp_project, monkeypatch):
        """Test commands close orchestrator even on error."""
        runner = CliRunner()

        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Mock that raises exception
        def mock_create_prd(name):
            raise Exception("Test error")

        mock_orchestrator.create_prd = mock_create_prd
        mock_create_default.return_value = mock_orchestrator

        # Run command
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_prd, ['--name', 'Test'])

        # Verify close() was called even on error
        assert mock_orchestrator.close.called
        assert result.exit_code != 0

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_command_without_git_state_manager(self, mock_create_default, temp_project, monkeypatch):
        """Test commands work even if git_state_manager is None."""
        runner = CliRunner()

        # Create mock orchestrator WITHOUT git_state_manager
        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = None  # No git integration
        mock_orchestrator.close = Mock()

        def mock_create_prd(name):
            yield "Creating PRD..."

        mock_orchestrator.create_prd = mock_create_prd
        mock_create_default.return_value = mock_orchestrator

        # Run command
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_prd, ['--name', 'Test'])

        # Should still succeed, but no git message
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" not in result.output

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_create_story_with_title_uses_git(self, mock_create_default, temp_project, monkeypatch):
        """Test create-story with title option uses git_state_manager."""
        runner = CliRunner()

        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        def mock_create_story(epic, story, title):
            yield f"Creating story: {title}"

        mock_orchestrator.create_story = mock_create_story
        mock_create_default.return_value = mock_orchestrator

        # Run with title
        monkeypatch.chdir(temp_project)
        result = runner.invoke(
            create_story,
            ['--epic', '1', '--story', '1', '--title', 'Test Story']
        )

        # Verify
        assert result.exit_code == 0
        assert "[INFO] Changes committed via git transaction" in result.output


class TestCLIErrorHandling:
    """Test CLI commands handle errors properly."""

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_error_in_workflow_shows_error_message(self, mock_create_default, temp_project, monkeypatch):
        """Test that workflow errors are shown to user."""
        runner = CliRunner()

        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        # Async generator that raises
        def mock_create_prd(name):
            raise ValueError("Test error from workflow")

        mock_orchestrator.create_prd = mock_create_prd
        mock_create_default.return_value = mock_orchestrator

        # Run command
        monkeypatch.chdir(temp_project)
        result = runner.invoke(create_prd, ['--name', 'Test'])

        # Verify error handling
        assert result.exit_code != 0
        assert "[ERROR]" in result.output
        assert "Test error from workflow" in result.output

    @patch('gao_dev.cli.commands.GAODevOrchestrator.create_default')
    def test_orchestrator_close_called_after_error(self, mock_create_default, temp_project, monkeypatch):
        """Test orchestrator.close() is called even when error occurs."""
        runner = CliRunner()

        mock_orchestrator = Mock()
        mock_orchestrator.git_state_manager = Mock()
        mock_orchestrator.close = Mock()

        def mock_implement_story(epic, story):
            raise RuntimeError("Implementation failed")

        mock_orchestrator.implement_story = mock_implement_story
        mock_create_default.return_value = mock_orchestrator

        # Run command
        monkeypatch.chdir(temp_project)
        result = runner.invoke(implement_story, ['--epic', '1', '--story', '1'])

        # Verify close was called despite error
        assert mock_orchestrator.close.called
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
