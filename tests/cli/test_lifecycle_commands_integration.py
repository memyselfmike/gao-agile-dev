"""Integration tests for lifecycle CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner
import tempfile
import shutil
import time
import sys

from gao_dev.cli.lifecycle_commands import lifecycle
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


def safe_rmtree(path, max_retries=5, delay=0.2):
    """
    Safely remove directory tree with retries for Windows file locking.

    On Windows, SQLite database files can remain locked briefly after
    connections are closed. This function retries with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt == max_retries - 1:
                # Last attempt failed - log but don't raise
                # This is acceptable for test cleanup
                print(f"Warning: Could not remove {path} after {max_retries} attempts")
                return
            time.sleep(delay * (2 ** attempt))


class TestLifecycleCommands:
    """Test suite for lifecycle CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def test_project(self):
        """Create test project with initialized lifecycle."""
        temp_dir = Path(tempfile.mkdtemp())
        project_dir = temp_dir / "test-app"
        project_dir.mkdir()

        # Initialize document lifecycle
        lifecycle = ProjectDocumentLifecycle.initialize(project_dir)

        # Create test document
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "TEST.md").write_text("# Test Document")

        yield project_dir

        # Close database connections before cleanup (Windows compatibility)
        if hasattr(lifecycle, 'registry') and hasattr(lifecycle.registry, 'close'):
            lifecycle.registry.close()

        # Use safe cleanup with retries for Windows file locking
        safe_rmtree(temp_dir)

    def test_lifecycle_health_detects_project(self, runner, test_project, monkeypatch):
        """Test that health command detects project root."""
        # Change to project directory
        monkeypatch.chdir(test_project)

        # Run health command with action-items-only to reduce output
        result = runner.invoke(lifecycle, ['health', '--action-items-only'])

        # Should show project name
        assert test_project.name in result.output
        # Should show project location
        assert "Location:" in result.output

    def test_lifecycle_with_project_option(self, runner, test_project):
        """Test explicit project targeting with --project option."""
        result = runner.invoke(lifecycle, ['health', '--action-items-only', '--project', str(test_project)])

        assert test_project.name in result.output
        assert "Project:" in result.output

    def test_lifecycle_from_subdirectory(self, runner, test_project, monkeypatch):
        """Test commands work from project subdirectories."""
        # Change to subdirectory
        subdir = test_project / "docs"
        monkeypatch.chdir(subdir)

        # Run health command
        result = runner.invoke(lifecycle, ['health', '--action-items-only'])

        assert test_project.name in result.output

    def test_lifecycle_uninitialized_project(self, runner, tmp_path, monkeypatch):
        """Test error handling for uninitialized projects."""
        # Change to directory without .gao-dev/
        monkeypatch.chdir(tmp_path)

        # Run health command
        result = runner.invoke(lifecycle, ['health'])

        assert result.exit_code != 0
        assert "not initialized" in result.output.lower()
        assert "gao-dev sandbox init" in result.output.lower()

    def test_lifecycle_invalid_project_path(self, runner):
        """Test error handling for invalid project path."""
        result = runner.invoke(lifecycle, [
            'health',
            '--project', '/nonexistent/path'
        ])

        assert result.exit_code != 0
        # CLI should show error about missing initialization or path not existing
        assert ("does not exist" in result.output.lower() or
                "not initialized" in result.output.lower())

    def test_lifecycle_project_context_displayed(self, runner, test_project):
        """Test that project context is displayed in output."""
        result = runner.invoke(lifecycle, [
            'health',
            '--action-items-only',
            '--project', str(test_project)
        ])

        assert "Project:" in result.output
        assert test_project.name in result.output
        assert "Location:" in result.output
        assert str(test_project) in result.output

    def test_lifecycle_archive_command(self, runner, test_project):
        """Test archive command with project detection."""
        result = runner.invoke(lifecycle, [
            'archive',
            '--dry-run',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_cleanup_command(self, runner, test_project):
        """Test cleanup command with project detection."""
        result = runner.invoke(lifecycle, [
            'cleanup',
            '--dry-run',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_retention_report_command(self, runner, test_project):
        """Test retention-report command with project detection."""
        result = runner.invoke(lifecycle, [
            'retention-report',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_show_policy_command(self, runner, test_project):
        """Test show-policy command with project detection."""
        result = runner.invoke(lifecycle, [
            'show-policy',
            'prd',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_list_policies_command(self, runner, test_project):
        """Test list-policies command with project detection."""
        result = runner.invoke(lifecycle, [
            'list-policies',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_review_due_command(self, runner, test_project):
        """Test review-due command with project detection."""
        result = runner.invoke(lifecycle, [
            'review-due',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_governance_report_command(self, runner, test_project):
        """Test governance-report command with project detection."""
        result = runner.invoke(lifecycle, [
            'governance-report',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_create_command(self, runner, test_project):
        """Test create command with project detection."""
        result = runner.invoke(lifecycle, [
            'create',
            'prd',
            '--subject', 'test-feature',
            '--author', 'Test Author',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_list_templates_command(self, runner, test_project):
        """Test list-templates command with project detection."""
        result = runner.invoke(lifecycle, [
            'list-templates',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_search_command(self, runner, test_project):
        """Test search command with project detection."""
        result = runner.invoke(lifecycle, [
            'search',
            'test query',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_search_tags_command(self, runner, test_project):
        """Test search-tags command with project detection."""
        result = runner.invoke(lifecycle, [
            'search-tags',
            '--tags', 'test-tag',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_lifecycle_health_command(self, runner, test_project):
        """Test health command with project detection."""
        result = runner.invoke(lifecycle, [
            'health',
            '--action-items-only',
            '--project', str(test_project)
        ])

        # Should show project context
        assert "Project:" in result.output
        assert test_project.name in result.output

    def test_multiple_projects_different_context(self, runner):
        """Test that different projects show different context."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create two projects
            project1 = temp_dir / "project1"
            project2 = temp_dir / "project2"

            project1.mkdir()
            project2.mkdir()

            # Initialize both
            ProjectDocumentLifecycle.initialize(project1)
            ProjectDocumentLifecycle.initialize(project2)

            # Run health on project1
            result1 = runner.invoke(lifecycle, [
                'health',
                '--action-items-only',
                '--project', str(project1)
            ])

            # Run health on project2
            result2 = runner.invoke(lifecycle, [
                'health',
                '--action-items-only',
                '--project', str(project2)
            ])

            # Each should show its own project name
            assert project1.name in result1.output
            assert project2.name in result2.output

            # Project1 output should not contain project2 name
            assert project2.name not in result1.output
            # Project2 output should not contain project1 name
            assert project1.name not in result2.output

        finally:
            # Clean up
            import time
            time.sleep(0.5)  # Give databases time to close
            try:
                shutil.rmtree(temp_dir)
            except PermissionError:
                pass  # Ignore cleanup errors on Windows
