"""Tests for GreenfieldInitializer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

from gao_dev.cli.greenfield_initializer import GreenfieldInitializer


class TestProjectTypeDetection:
    """Tests for project type detection."""

    def test_detect_greenfield_empty_directory(self, tmp_path):
        """Test detection of greenfield project in empty directory."""
        initializer = GreenfieldInitializer(tmp_path)

        project_type = initializer.detect_project_type()

        assert project_type == "greenfield"

    def test_detect_brownfield_with_package_json(self, tmp_path):
        """Test detection of brownfield project with package.json."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test-project"}')

        initializer = GreenfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "brownfield"

    def test_detect_brownfield_with_requirements_txt(self, tmp_path):
        """Test detection of brownfield project with requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("flask==2.0.0")

        initializer = GreenfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "brownfield"

    def test_detect_brownfield_with_src_directory(self, tmp_path):
        """Test detection of brownfield project with src/ directory."""
        # Create src/ directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        initializer = GreenfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "brownfield"

    def test_detect_greenfield_with_only_readme(self, tmp_path):
        """Test detection of greenfield when only README exists."""
        # Create README (shouldn't trigger brownfield detection)
        readme = tmp_path / "README.md"
        readme.write_text("# Test Project")

        initializer = GreenfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "greenfield"


class TestGreenfieldInitialization:
    """Tests for greenfield initialization flow."""

    @pytest.mark.asyncio
    async def test_initialize_creates_directories(self, tmp_path):
        """Test that initialization creates required directories."""
        initializer = GreenfieldInitializer(tmp_path)

        # Initialize (non-interactive)
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Assert directories created
        assert (tmp_path / ".gao-dev").exists()
        assert (tmp_path / ".gao-dev" / "documents.db").exists()
        assert (tmp_path / ".gao-dev" / "metrics").exists()
        assert (tmp_path / "docs").exists()
        assert (tmp_path / "src").exists()
        assert (tmp_path / "tests").exists()

        # Assert success message
        assert any("initialized successfully" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_creates_documents(self, tmp_path):
        """Test that initialization creates README.md and .gitignore."""
        initializer = GreenfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert documents created
        assert (tmp_path / "README.md").exists()
        assert (tmp_path / ".gitignore").exists()

        # Verify README content
        readme_content = (tmp_path / "README.md").read_text()
        assert tmp_path.name in readme_content
        assert "GAO-Dev" in readme_content

        # Verify .gitignore content
        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert "__pycache__" in gitignore_content
        assert ".gao-dev/metrics" in gitignore_content

    @pytest.mark.asyncio
    async def test_initialize_creates_git_repository(self, tmp_path):
        """Test that initialization creates git repository."""
        initializer = GreenfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert git initialized
        assert (tmp_path / ".git").exists()

        # Verify git repo is valid
        result = subprocess.run(
            ["git", "status"],
            cwd=tmp_path,
            capture_output=True,
            check=False
        )
        assert result.returncode == 0

    @pytest.mark.asyncio
    async def test_initialize_creates_initial_commit(self, tmp_path):
        """Test that initialization creates initial commit."""
        # Set git config for this test
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=tmp_path,
            capture_output=True,
            check=False
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False
        )

        initializer = GreenfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # If commit was created, verify it
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False
        )

        # Commit should either exist or we should have a warning about git config
        if result.returncode == 0:
            assert "Initialize GAO-Dev project" in result.stdout
        else:
            # Git config issue - should have warning
            assert any("WARN" in msg for msg in messages) or any("commit" in msg.lower() for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_skips_git_if_already_initialized(self, tmp_path):
        """Test that initialization skips git if already initialized."""
        # Initialize git manually
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        initializer = GreenfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Should skip git initialization
        assert any("already initialized" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_handles_git_failure_gracefully(self, tmp_path):
        """Test that initialization handles git failure gracefully."""
        initializer = GreenfieldInitializer(tmp_path)

        # Mock git to fail
        with patch("subprocess.run") as mock_run:
            # First call (git init) fails
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "git init", stderr=b"Git failed"),
                # Subsequent calls succeed (for other operations)
            ]

            messages = []
            async for message in initializer.initialize(interactive=False):
                messages.append(message)

            # Should warn about git failure but continue
            assert any("WARN" in msg and "Git" in msg for msg in messages)
            assert any("manually later" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_interactive_mode(self, tmp_path):
        """Test initialization in interactive mode."""
        initializer = GreenfieldInitializer(tmp_path)

        # Initialize in interactive mode (uses defaults for now)
        messages = []
        async for message in initializer.initialize(interactive=True):
            messages.append(message)

        # Should still create all structures
        assert (tmp_path / ".gao-dev").exists()
        assert (tmp_path / "README.md").exists()
        assert any("initialized successfully" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_yields_progress_messages(self, tmp_path):
        """Test that initialization yields informative progress messages."""
        initializer = GreenfieldInitializer(tmp_path)

        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Check for key messages
        assert any("Welcome" in msg for msg in messages)
        assert any("Creating project structure" in msg for msg in messages)
        assert any("directories created" in msg for msg in messages)
        assert any("README.md created" in msg for msg in messages)
        assert any("initialized successfully" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_creates_metrics_gitkeep(self, tmp_path):
        """Test that initialization creates .gitkeep in metrics directory."""
        initializer = GreenfieldInitializer(tmp_path)

        async for message in initializer.initialize(interactive=False):
            pass

        # Assert .gitkeep exists
        assert (tmp_path / ".gao-dev" / "metrics" / ".gitkeep").exists()


class TestHelperMethods:
    """Tests for helper methods."""

    def test_is_git_initialized_true(self, tmp_path):
        """Test _is_git_initialized returns True when .git exists."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        initializer = GreenfieldInitializer(tmp_path)
        assert initializer._is_git_initialized() is True

    def test_is_git_initialized_false(self, tmp_path):
        """Test _is_git_initialized returns False when .git doesn't exist."""
        initializer = GreenfieldInitializer(tmp_path)
        assert initializer._is_git_initialized() is False

    def test_get_default_project_info(self, tmp_path):
        """Test _get_default_project_info returns correct structure."""
        initializer = GreenfieldInitializer(tmp_path)

        info = initializer._get_default_project_info()

        assert "name" in info
        assert "type" in info
        assert "description" in info
        assert info["name"] == tmp_path.name
        assert info["type"] == "application"

    def test_generate_readme(self, tmp_path):
        """Test _generate_readme creates valid content."""
        initializer = GreenfieldInitializer(tmp_path)

        project_info = {
            "name": "test-project",
            "type": "application",
            "description": "A test project"
        }

        readme = initializer._generate_readme(project_info)

        assert "# test-project" in readme
        assert "A test project" in readme
        assert "GAO-Dev" in readme
        assert "gao-dev start" in readme
        assert "Brian" in readme

    def test_generate_gitignore(self, tmp_path):
        """Test _generate_gitignore creates valid content."""
        initializer = GreenfieldInitializer(tmp_path)

        gitignore = initializer._generate_gitignore()

        # Check for common patterns
        assert "__pycache__" in gitignore
        assert ".vscode" in gitignore
        assert ".DS_Store" in gitignore
        assert ".gao-dev/metrics" in gitignore
        assert "!.gao-dev/metrics/.gitkeep" in gitignore


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_initialize_handles_directory_creation_failure(self, tmp_path):
        """Test handling of directory creation failure."""
        initializer = GreenfieldInitializer(tmp_path)

        # Mock mkdir to fail
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            messages = []
            async for message in initializer.initialize(interactive=False):
                messages.append(message)

            # Should fail gracefully
            assert any("FAILED" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_handles_document_creation_failure(self, tmp_path):
        """Test handling of document creation failure."""
        initializer = GreenfieldInitializer(tmp_path)

        # Create directories manually
        (tmp_path / ".gao-dev").mkdir()

        # Mock write_text to fail
        with patch.object(Path, "write_text", side_effect=OSError("Write failed")):
            messages = []
            async for message in initializer.initialize(interactive=False):
                messages.append(message)

            # Should fail when creating documents
            assert any("FAILED" in msg and "documents" in msg for msg in messages)
