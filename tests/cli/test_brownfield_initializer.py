"""Tests for BrownfieldInitializer."""

import pytest
from pathlib import Path
import json
import subprocess

from gao_dev.cli.brownfield_initializer import BrownfieldInitializer


class TestProjectTypeDetection:
    """Tests for project type detection."""

    def test_detect_node_project(self, tmp_path):
        """Test detection of Node.js project."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test-project"}')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "node"

    def test_detect_python_project_requirements(self, tmp_path):
        """Test detection of Python project with requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("flask==2.0.0\nrequests>=2.25.0")

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "python"

    def test_detect_python_project_pyproject(self, tmp_path):
        """Test detection of Python project with pyproject.toml."""
        # Create pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test-project"')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "python"

    def test_detect_rust_project(self, tmp_path):
        """Test detection of Rust project."""
        # Create Cargo.toml
        cargo = tmp_path / "Cargo.toml"
        cargo.write_text('[package]\nname = "test-project"')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "rust"

    def test_detect_go_project(self, tmp_path):
        """Test detection of Go project."""
        # Create go.mod
        go_mod = tmp_path / "go.mod"
        go_mod.write_text('module test-project')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "go"

    def test_detect_java_maven_project(self, tmp_path):
        """Test detection of Java Maven project."""
        # Create pom.xml
        pom = tmp_path / "pom.xml"
        pom.write_text('<project></project>')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "java"

    def test_detect_java_gradle_project(self, tmp_path):
        """Test detection of Java Gradle project."""
        # Create build.gradle
        build_gradle = tmp_path / "build.gradle"
        build_gradle.write_text('plugins { id "java" }')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "java"

    def test_detect_ruby_project(self, tmp_path):
        """Test detection of Ruby project."""
        # Create Gemfile
        gemfile = tmp_path / "Gemfile"
        gemfile.write_text('source "https://rubygems.org"')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "ruby"

    def test_detect_php_project(self, tmp_path):
        """Test detection of PHP project."""
        # Create composer.json
        composer = tmp_path / "composer.json"
        composer.write_text('{"name": "test/project"}')

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "php"

    def test_detect_unknown_project(self, tmp_path):
        """Test detection of unknown project type."""
        # Create some files but no recognizable project files
        readme = tmp_path / "README.md"
        readme.write_text("# Test Project")

        initializer = BrownfieldInitializer(tmp_path)
        project_type = initializer.detect_project_type()

        assert project_type == "unknown"


class TestCodebaseAnalysis:
    """Tests for codebase analysis."""

    def test_analyze_empty_project(self, tmp_path):
        """Test analysis of empty project."""
        initializer = BrownfieldInitializer(tmp_path)

        analysis = initializer._analyze_existing_codebase()

        assert analysis["type"] == "unknown"
        assert analysis["file_count"] == 0
        assert analysis["directory_count"] == 0
        assert analysis["has_tests"] is False
        assert analysis["has_docs"] is False

    def test_analyze_node_project(self, tmp_path):
        """Test analysis of Node.js project."""
        # Create package.json with dependencies
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "dependencies": {
                "express": "^4.17.1",
                "lodash": "^4.17.21"
            }
        }))

        # Create src directory with files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text("console.log('Hello');")
        (src_dir / "app.js").write_text("const express = require('express');")

        # Create tests directory
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test.js").write_text("// test")

        initializer = BrownfieldInitializer(tmp_path)
        analysis = initializer._analyze_existing_codebase()

        assert analysis["type"] == "node"
        assert analysis["file_count"] >= 3  # package.json + 2 src files + 1 test
        assert analysis["has_tests"] is True
        assert "express" in analysis["dependencies"]

    def test_analyze_python_project(self, tmp_path):
        """Test analysis of Python project."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("flask==2.0.0\nrequests>=2.25.0\npytest>=6.0.0")

        # Create src directory with files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('Hello')")
        (src_dir / "app.py").write_text("from flask import Flask")

        # Create docs directory
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "README.md").write_text("# Documentation")

        initializer = BrownfieldInitializer(tmp_path)
        analysis = initializer._analyze_existing_codebase()

        assert analysis["type"] == "python"
        assert analysis["file_count"] >= 3
        assert analysis["has_docs"] is True
        assert "flask" in analysis["dependencies"]

    def test_analyze_excludes_ignored_directories(self, tmp_path):
        """Test that analysis excludes common ignored directories."""
        # Create node_modules
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        for i in range(100):
            (node_modules / f"file{i}.js").write_text("// file")

        # Create __pycache__
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        for i in range(50):
            (pycache / f"file{i}.pyc").write_text("bytecode")

        # Create actual source files
        (tmp_path / "main.py").write_text("print('Hello')")

        initializer = BrownfieldInitializer(tmp_path)
        analysis = initializer._analyze_existing_codebase()

        # Should only count main.py, not files in ignored directories
        assert analysis["file_count"] < 10  # Much less than 150


class TestBrownfieldInitialization:
    """Tests for brownfield initialization flow."""

    @pytest.mark.asyncio
    async def test_initialize_preserves_existing_readme(self, tmp_path):
        """Test that initialization preserves existing README.md."""
        # Create existing README
        readme = tmp_path / "README.md"
        original_content = "# My Existing Project\n\nThis is my original README."
        readme.write_text(original_content)

        # Create package.json to trigger brownfield
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Assert backup created
        backup = tmp_path / "README.md.bak"
        assert backup.exists()
        assert backup.read_text() == original_content

        # Assert new README exists
        assert readme.exists()
        new_content = readme.read_text()
        assert "GAO-Dev" in new_content
        assert "README.md.bak" in new_content

    @pytest.mark.asyncio
    async def test_initialize_creates_project_status(self, tmp_path):
        """Test that initialization creates PROJECT_STATUS.md."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert PROJECT_STATUS.md created
        status_file = tmp_path / "docs" / "PROJECT_STATUS.md"
        assert status_file.exists()

        content = status_file.read_text()
        assert "Onboarded" in content
        assert "node" in content
        assert "Current State" in content

    @pytest.mark.asyncio
    async def test_initialize_creates_retrospective(self, tmp_path):
        """Test that initialization creates initial retrospective."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert retrospective created
        retro_file = tmp_path / "docs" / "retrospectives" / "initial-state.md"
        assert retro_file.exists()

        content = retro_file.read_text()
        assert "Initial Project State Retrospective" in content
        assert "Brownfield Onboarding" in content
        assert "Action Items" in content

    @pytest.mark.asyncio
    async def test_initialize_creates_gao_dev_structure(self, tmp_path):
        """Test that initialization creates .gao-dev/ structure."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert .gao-dev/ structure
        assert (tmp_path / ".gao-dev").exists()
        assert (tmp_path / ".gao-dev" / "documents.db").exists()
        assert (tmp_path / ".gao-dev" / "metrics").exists()
        assert (tmp_path / ".gao-dev" / "metrics" / ".gitkeep").exists()

    @pytest.mark.asyncio
    async def test_initialize_creates_git_if_needed(self, tmp_path):
        """Test that initialization creates git if not present."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        async for message in initializer.initialize(interactive=False):
            pass

        # Assert git initialized
        assert (tmp_path / ".git").exists()

    @pytest.mark.asyncio
    async def test_initialize_skips_git_if_exists(self, tmp_path):
        """Test that initialization skips git if already present."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        # Initialize git manually
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Should skip git initialization
        assert any("already exists" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_creates_commit(self, tmp_path):
        """Test that initialization creates git commit."""
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

        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Verify commit exists (or at least attempted)
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False
        )

        # Commit should either exist or we should have a warning
        if result.returncode == 0:
            assert "Add GAO-Dev tracking" in result.stdout
        else:
            # Git config issue - should have warning
            assert any("WARN" in msg for msg in messages) or any("commit" in msg.lower() for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_yields_progress_messages(self, tmp_path):
        """Test that initialization yields informative progress messages."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Check for key messages
        assert any("existing project" in msg for msg in messages)
        assert any("Scanning your codebase" in msg for msg in messages)
        assert any("node project" in msg for msg in messages)
        assert any(".gao-dev/ created" in msg for msg in messages)
        assert any("README.md generated" in msg for msg in messages)
        assert any("PROJECT_STATUS.md created" in msg for msg in messages)
        assert any("retrospective" in msg for msg in messages)
        assert any("Done!" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_reports_project_statistics(self, tmp_path):
        """Test that initialization reports file and directory counts."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        # Create some files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "file1.js").write_text("// code")
        (src_dir / "file2.js").write_text("// code")

        initializer = BrownfieldInitializer(tmp_path)

        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Should report file count
        assert any("files" in msg for msg in messages)
        assert any("directories" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_handles_readme_without_backup_needed(self, tmp_path):
        """Test initialization when no existing README."""
        # Create package.json but no README
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Initialize
        messages = []
        async for message in initializer.initialize(interactive=False):
            messages.append(message)

        # Should not create backup
        assert not (tmp_path / "README.md.bak").exists()

        # Should create new README
        assert (tmp_path / "README.md").exists()


class TestDependencyExtraction:
    """Tests for dependency extraction."""

    def test_extract_node_dependencies(self, tmp_path):
        """Test extraction of Node.js dependencies."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "express": "^4.17.1",
                "lodash": "^4.17.21",
                "axios": "^0.21.1"
            }
        }))

        initializer = BrownfieldInitializer(tmp_path)
        deps = initializer._extract_dependencies("node")

        assert "express" in deps
        assert "lodash" in deps
        assert len(deps) <= 5  # Top 5 only

    def test_extract_python_dependencies(self, tmp_path):
        """Test extraction of Python dependencies."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("""
flask==2.0.0
requests>=2.25.0
pytest>=6.0.0
# This is a comment
sqlalchemy==1.4.0
""".strip())

        initializer = BrownfieldInitializer(tmp_path)
        deps = initializer._extract_dependencies("python")

        assert "flask" in deps
        assert "requests" in deps
        assert "pytest" in deps
        assert len(deps) <= 5  # Top 5 only

    def test_extract_dependencies_handles_missing_file(self, tmp_path):
        """Test dependency extraction handles missing files gracefully."""
        initializer = BrownfieldInitializer(tmp_path)

        # Should return empty list, not raise error
        deps = initializer._extract_dependencies("node")
        assert deps == []

    def test_extract_dependencies_unknown_type(self, tmp_path):
        """Test dependency extraction for unknown project type."""
        initializer = BrownfieldInitializer(tmp_path)

        deps = initializer._extract_dependencies("unknown")
        assert deps == []


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_initialize_handles_directory_creation_failure(self, tmp_path):
        """Test handling of directory creation failure."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Mock mkdir to fail
        from unittest.mock import patch
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            messages = []
            async for message in initializer.initialize(interactive=False):
                messages.append(message)

            # Should fail gracefully
            assert any("FAILED" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_initialize_handles_git_failure_gracefully(self, tmp_path):
        """Test that initialization handles git failure gracefully."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"name": "test"}')

        initializer = BrownfieldInitializer(tmp_path)

        # Mock git to fail
        from unittest.mock import patch
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                if "git" in args[0]:
                    raise subprocess.CalledProcessError(1, "git", stderr=b"Git failed")
                # Let other calls pass through (for StateTracker, etc.)
                return subprocess.CompletedProcess(args[0], 0, b"", b"")

            mock_run.side_effect = side_effect

            messages = []
            async for message in initializer.initialize(interactive=False):
                messages.append(message)

            # Should warn about git failure but continue
            assert any("WARN" in msg for msg in messages)
