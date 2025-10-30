"""Tests for BoilerplateService."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import tempfile
import shutil

from gao_dev.sandbox.services.boilerplate import BoilerplateService
from gao_dev.sandbox.exceptions import GitCloneError


@pytest.fixture
def mock_git_cloner():
    """Create mock GitCloner."""
    cloner = MagicMock()
    cloner.clone_repository = MagicMock(return_value=True)
    return cloner


@pytest.fixture
def boilerplate_service(mock_git_cloner):
    """Create BoilerplateService instance."""
    return BoilerplateService(git_cloner=mock_git_cloner)


class TestBoilerplateServiceInit:
    """Tests for BoilerplateService initialization."""

    def test_init_with_custom_cloner(self, mock_git_cloner):
        """Test initialization with custom GitCloner."""
        service = BoilerplateService(git_cloner=mock_git_cloner)

        assert service.git_cloner is mock_git_cloner

    @patch("gao_dev.sandbox.services.boilerplate.GitCloner")
    def test_init_without_cloner_creates_default(self, mock_git_cloner_class):
        """Test that default GitCloner is created if not provided."""
        service = BoilerplateService()

        # Should have created a GitCloner instance
        assert service.git_cloner is not None


class TestCloneBoilerplate:
    """Tests for clone_boilerplate method."""

    def test_clone_boilerplate_success(self, boilerplate_service, tmp_path):
        """Test successful boilerplate cloning."""
        # Create a mock boilerplate repo
        mock_repo = tmp_path / "mock_repo"
        mock_repo.mkdir()
        (mock_repo / "file.txt").write_text("Hello")

        # Setup mock git cloner to copy files
        def mock_clone(url, dest):
            # Simulate git clone by copying mock repo
            dest = Path(dest)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(mock_repo, dest, dirs_exist_ok=True)

        boilerplate_service.git_cloner.clone_repository = mock_clone

        # Clone boilerplate
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        boilerplate_service.clone_boilerplate(
            "https://github.com/test/repo.git",
            target_dir,
        )

        # Verify file was merged
        assert (target_dir / "file.txt").exists()
        assert (target_dir / "file.txt").read_text() == "Hello"

    def test_clone_boilerplate_removes_git_directory(self, boilerplate_service, tmp_path):
        """Test that .git directory is removed after cloning."""
        # Create a mock boilerplate repo with .git directory
        mock_repo = tmp_path / "mock_repo"
        mock_repo.mkdir()
        (mock_repo / ".git").mkdir()
        (mock_repo / ".git" / "config").write_text("git config")
        (mock_repo / "file.txt").write_text("Hello")

        # Setup mock git cloner
        def mock_clone(url, dest):
            dest = Path(dest)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(mock_repo, dest, dirs_exist_ok=True)

        boilerplate_service.git_cloner.clone_repository = mock_clone

        # Clone boilerplate
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        boilerplate_service.clone_boilerplate(
            "https://github.com/test/repo.git",
            target_dir,
        )

        # Verify .git directory was removed
        assert not (target_dir / ".git").exists()
        assert (target_dir / "file.txt").exists()

    def test_clone_boilerplate_cleans_temp_directory(self, boilerplate_service, tmp_path):
        """Test that temporary clone directory is cleaned up."""
        # Create a mock boilerplate repo
        mock_repo = tmp_path / "mock_repo"
        mock_repo.mkdir()
        (mock_repo / "file.txt").write_text("Hello")

        # Setup mock git cloner
        def mock_clone(url, dest):
            dest = Path(dest)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(mock_repo, dest, dirs_exist_ok=True)

        boilerplate_service.git_cloner.clone_repository = mock_clone

        # Clone boilerplate
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        boilerplate_service.clone_boilerplate(
            "https://github.com/test/repo.git",
            target_dir,
        )

        # Verify temp directory was removed
        temp_clone_dir = target_dir / ".boilerplate_clone"
        assert not temp_clone_dir.exists()

    def test_clone_boilerplate_merges_directories(self, boilerplate_service, tmp_path):
        """Test that boilerplate directories are properly merged."""
        # Create mock boilerplate with directories
        mock_repo = tmp_path / "mock_repo"
        mock_repo.mkdir()
        (mock_repo / "src").mkdir()
        (mock_repo / "src" / "index.py").write_text("print('hello')")
        (mock_repo / "docs").mkdir()
        (mock_repo / "docs" / "README.md").write_text("# README")

        # Setup mock git cloner
        def mock_clone(url, dest):
            dest = Path(dest)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(mock_repo, dest, dirs_exist_ok=True)

        boilerplate_service.git_cloner.clone_repository = mock_clone

        # Clone boilerplate
        target_dir = tmp_path / "target"
        target_dir.mkdir()

        boilerplate_service.clone_boilerplate(
            "https://github.com/test/repo.git",
            target_dir,
        )

        # Verify directory structure
        assert (target_dir / "src" / "index.py").exists()
        assert (target_dir / "docs" / "README.md").exists()

    def test_clone_boilerplate_handles_clone_failure(self, boilerplate_service, tmp_path):
        """Test error handling when clone fails."""
        boilerplate_service.git_cloner.clone_repository.side_effect = GitCloneError(
            "https://github.com/test/repo.git",
            "Network error",
        )

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        with pytest.raises(GitCloneError):
            boilerplate_service.clone_boilerplate(
                "https://github.com/test/repo.git",
                target_dir,
            )


class TestProcessTemplate:
    """Tests for process_template method."""

    def test_process_template_simple_substitution(self, boilerplate_service, tmp_path):
        """Test simple template variable substitution."""
        # Create project with template
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "config.py").write_text(
            "APP_NAME = '{{ app_name }}'\n"
            "VERSION = '{{ version }}'"
        )

        # Process templates
        variables = {
            "app_name": "MyApp",
            "version": "1.0.0",
        }

        boilerplate_service.process_template(project_dir, variables)

        # Verify substitution
        content = (project_dir / "config.py").read_text()
        assert "APP_NAME = 'MyApp'" in content
        assert "VERSION = '1.0.0'" in content

    def test_process_template_multiple_files(self, boilerplate_service, tmp_path):
        """Test template processing across multiple files."""
        # Create project with multiple files
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "file1.py").write_text("name = '{{ project_name }}'")
        (project_dir / "file2.py").write_text("author = '{{ author }}'")

        # Process templates
        variables = {
            "project_name": "MyProject",
            "author": "Jane Doe",
        }

        boilerplate_service.process_template(project_dir, variables)

        # Verify both files updated
        assert "MyProject" in (project_dir / "file1.py").read_text()
        assert "Jane Doe" in (project_dir / "file2.py").read_text()

    def test_process_template_skips_binary_files(self, boilerplate_service, tmp_path):
        """Test that binary files are skipped."""
        # Create project with binary and text files
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "text.py").write_text("name = '{{ name }}'")
        (project_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03")

        # Process templates
        variables = {"name": "Test"}

        # Should not raise even with binary file
        boilerplate_service.process_template(project_dir, variables)

        # Text file should be updated
        assert "Test" in (project_dir / "text.py").read_text()

    def test_process_template_ignores_hidden_files(self, boilerplate_service, tmp_path):
        """Test that hidden files are ignored."""
        # Create project with hidden file
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".hidden").write_text("name = '{{ name }}'")

        # Process templates
        variables = {"name": "Test"}

        boilerplate_service.process_template(project_dir, variables)

        # Hidden file should not be modified
        assert "{{ name }}" in (project_dir / ".hidden").read_text()

    def test_process_template_nested_directories(self, boilerplate_service, tmp_path):
        """Test template processing in nested directories."""
        # Create nested project structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "src" / "config.py").write_text("app = '{{ app }}'")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "test.py").write_text("test_name = '{{ test }}'")

        # Process templates
        variables = {"app": "MyApp", "test": "TestSuite"}

        boilerplate_service.process_template(project_dir, variables)

        # Verify nested files updated
        assert "MyApp" in (project_dir / "src" / "config.py").read_text()
        assert "TestSuite" in (project_dir / "tests" / "test.py").read_text()

    def test_process_template_empty_variables(self, boilerplate_service, tmp_path):
        """Test template processing with no variables."""
        # Create project
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        original_content = "name = '{{ name }}'"
        (project_dir / "config.py").write_text(original_content)

        # Process with empty variables
        boilerplate_service.process_template(project_dir, {})

        # Content should be unchanged
        assert (project_dir / "config.py").read_text() == original_content

    def test_process_template_unmatched_variables(self, boilerplate_service, tmp_path):
        """Test template with undefined variables."""
        # Create project
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        original_content = "name = '{{ name }}'"
        (project_dir / "config.py").write_text(original_content)

        # Process with different variable
        boilerplate_service.process_template(project_dir, {"other": "value"})

        # Unmatched template should remain
        assert "{{ name }}" in (project_dir / "config.py").read_text()
