"""Tests for TemplateScanner functionality."""

from pathlib import Path

import pytest

from gao_dev.sandbox import TemplateScanner, TemplateVariable


class TestTemplateScanner:
    """Tests for TemplateScanner class."""

    @pytest.fixture
    def scanner(self):
        """Create TemplateScanner instance."""
        return TemplateScanner()

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project directory."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project

    def test_init_scanner(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert len(scanner.text_extensions) > 0
        assert len(scanner.ignore_dirs) > 0

    def test_detect_double_brace_variables(self, scanner, temp_project):
        """Test detection of {{VAR}} format."""
        # Create file with double brace variables
        readme = temp_project / "README.md"
        readme.write_text(
            "# {{PROJECT_NAME}}\n\n"
            "Description: {{project_description}}\n"
            "Author: {{AUTHOR}}\n"
        )

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "project_description" in var_names
        assert "AUTHOR" in var_names

        # All should be double_brace format
        assert all(v.format == "double_brace" for v in variables)

    def test_detect_double_underscore_variables(self, scanner, temp_project):
        """Test detection of __VAR__ format."""
        # Create file with double underscore variables
        config = temp_project / "config.py"
        config.write_text(
            "PROJECT_NAME = '__PROJECT_NAME__'\n"
            "AUTHOR = '__AUTHOR__'\n"
            "VERSION = '__VERSION__'\n"
        )

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "AUTHOR" in var_names
        assert "VERSION" in var_names

        # All should be double_underscore format
        assert all(v.format == "double_underscore" for v in variables)

    def test_detect_mixed_formats(self, scanner, temp_project):
        """Test detection of both variable formats."""
        # Create file with both formats
        file1 = temp_project / "file1.md"
        file1.write_text("# {{PROJECT_NAME}}\nAuthor: __AUTHOR__\n")

        variables = scanner.scan_project(temp_project)

        # Should find both variables
        assert len(variables) == 2

        # Check formats
        var_dict = {v.name: v.format for v in variables}
        assert var_dict["PROJECT_NAME"] == "double_brace"
        assert var_dict["AUTHOR"] == "double_underscore"

    def test_scan_multiple_files(self, scanner, temp_project):
        """Test scanning multiple files."""
        # Create multiple files with variables
        (temp_project / "README.md").write_text("# {{PROJECT_NAME}}")
        (temp_project / "package.json").write_text('{"name": "{{project_name}}"}')
        (temp_project / "config.yaml").write_text("author: {{AUTHOR}}")

        variables = scanner.scan_project(temp_project)

        # Check PROJECT_NAME appears in README.md
        project_name_var = next(v for v in variables if v.name == "PROJECT_NAME")
        assert "README.md" in project_name_var.locations

        # Check project_name appears in package.json
        project_name_lower = next(v for v in variables if v.name == "project_name")
        assert "package.json" in project_name_lower.locations

    def test_deduplicate_variables(self, scanner, temp_project):
        """Test that same variable in multiple files is deduplicated."""
        # Create multiple files with same variable
        (temp_project / "file1.md").write_text("{{PROJECT_NAME}}")
        (temp_project / "file2.md").write_text("{{PROJECT_NAME}}")
        (temp_project / "file3.md").write_text("{{PROJECT_NAME}}")

        variables = scanner.scan_project(temp_project)

        # Should have only one TemplateVariable for PROJECT_NAME
        project_vars = [v for v in variables if v.name == "PROJECT_NAME"]
        assert len(project_vars) == 1

        # But should track all locations
        assert len(project_vars[0].locations) == 3
        assert "file1.md" in project_vars[0].locations
        assert "file2.md" in project_vars[0].locations
        assert "file3.md" in project_vars[0].locations

    def test_ignore_binary_files(self, scanner, temp_project):
        """Test that binary files are skipped."""
        # Create a binary file (or file with non-text extension)
        binary_file = temp_project / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n{{PROJECT_NAME}}")

        variables = scanner.scan_project(temp_project)

        # Should not find any variables
        assert len(variables) == 0

    def test_ignore_node_modules(self, scanner, temp_project):
        """Test that node_modules directory is skipped."""
        # Create node_modules directory with variables
        node_modules = temp_project / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.json").write_text('{"name": "{{SHOULD_IGNORE}}"}')

        # Create file outside node_modules
        (temp_project / "README.md").write_text("{{PROJECT_NAME}}")

        variables = scanner.scan_project(temp_project)

        # Should only find PROJECT_NAME, not SHOULD_IGNORE
        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "SHOULD_IGNORE" not in var_names

    def test_ignore_git_directory(self, scanner, temp_project):
        """Test that .git directory is skipped."""
        # Create .git directory with variables
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("{{SHOULD_IGNORE}}")

        # Create file outside .git
        (temp_project / "README.md").write_text("{{PROJECT_NAME}}")

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "SHOULD_IGNORE" not in var_names

    def test_ignore_pycache(self, scanner, temp_project):
        """Test that __pycache__ is skipped."""
        # Create __pycache__ directory
        pycache = temp_project / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("{{SHOULD_IGNORE}}")

        # Create normal file
        (temp_project / "main.py").write_text("name = '{{PROJECT_NAME}}'")

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "SHOULD_IGNORE" not in var_names

    def test_scan_text_extensions(self, scanner, temp_project):
        """Test scanning various text file extensions."""
        # Create files with different extensions
        extensions = [".md", ".txt", ".json", ".yaml", ".py", ".js", ".ts", ".tsx"]

        for ext in extensions:
            file = temp_project / f"test{ext}"
            file.write_text("{{TEST_VAR}}")

        variables = scanner.scan_project(temp_project)

        # Should find TEST_VAR in all files
        test_var = next(v for v in variables if v.name == "TEST_VAR")
        assert len(test_var.locations) == len(extensions)

    def test_is_text_file(self, scanner, temp_project):
        """Test text file detection."""
        # Create text files
        (temp_project / "test.md").write_text("test")
        (temp_project / "test.py").write_text("test")
        (temp_project / "test.json").write_text("test")

        # Create binary/non-text files
        (temp_project / "image.png").write_bytes(b"test")
        (temp_project / "data.bin").write_bytes(b"test")
        (temp_project / "archive.zip").write_bytes(b"test")

        # Text files should pass
        assert scanner.is_text_file(temp_project / "test.md")
        assert scanner.is_text_file(temp_project / "test.py")
        assert scanner.is_text_file(temp_project / "test.json")

        # Non-text files (by extension) should fail
        assert not scanner.is_text_file(temp_project / "image.png")
        assert not scanner.is_text_file(temp_project / "data.bin")
        assert not scanner.is_text_file(temp_project / "archive.zip")

    def test_scan_file_double_brace(self, scanner, temp_project):
        """Test scanning single file for double brace variables."""
        file = temp_project / "test.md"
        file.write_text("# {{VAR1}}\n{{VAR2}}\n{{VAR1}}")

        variables = scanner.scan_file(file)

        # Should return set of (name, format) tuples
        var_names = {name for name, fmt in variables}
        assert "VAR1" in var_names
        assert "VAR2" in var_names
        assert len(variables) == 2  # Deduplicated

    def test_scan_file_double_underscore(self, scanner, temp_project):
        """Test scanning single file for double underscore variables."""
        file = temp_project / "test.py"
        file.write_text("NAME = '__VAR1__'\nOTHER = '__VAR2__'")

        variables = scanner.scan_file(file)

        var_names = {name for name, fmt in variables}
        assert "VAR1" in var_names
        assert "VAR2" in var_names

    def test_scan_empty_file(self, scanner, temp_project):
        """Test scanning empty file."""
        file = temp_project / "empty.md"
        file.write_text("")

        variables = scanner.scan_file(file)

        assert len(variables) == 0

    def test_scan_file_no_variables(self, scanner, temp_project):
        """Test scanning file without variables."""
        file = temp_project / "normal.md"
        file.write_text("# Normal File\n\nNo variables here!")

        variables = scanner.scan_file(file)

        assert len(variables) == 0

    def test_ignore_invalid_variable_names(self, scanner, temp_project):
        """Test that invalid variable names are not detected."""
        file = temp_project / "test.md"
        file.write_text(
            "{{123invalid}}\n"  # Starts with number
            "{{-invalid}}\n"  # Starts with hyphen
            "{{in-valid}}\n"  # Contains hyphen
            "{{valid_name}}\n"  # Valid
        )

        variables = scanner.scan_file(file)

        var_names = {name for name, fmt in variables}
        # Only valid_name should be found
        assert "valid_name" in var_names
        assert len(var_names) == 1

    def test_get_variables_by_format(self, scanner):
        """Test filtering variables by format."""
        variables = [
            TemplateVariable("VAR1", "double_brace", []),
            TemplateVariable("VAR2", "double_underscore", []),
            TemplateVariable("VAR3", "double_brace", []),
        ]

        brace_vars = scanner.get_variables_by_format(variables, "double_brace")
        assert len(brace_vars) == 2

        underscore_vars = scanner.get_variables_by_format(variables, "double_underscore")
        assert len(underscore_vars) == 1

    def test_get_common_variables(self, scanner):
        """Test identifying common variables."""
        variables = [
            TemplateVariable("PROJECT_NAME", "double_brace", []),
            TemplateVariable("AUTHOR", "double_brace", []),
            TemplateVariable("CUSTOM_VAR", "double_brace", []),
            TemplateVariable("LICENSE", "double_brace", []),
        ]

        common = scanner.get_common_variables(variables)

        assert "PROJECT_NAME" in common
        assert "AUTHOR" in common
        assert "LICENSE" in common
        assert "CUSTOM_VAR" not in common

    def test_scan_nonexistent_project(self, scanner, tmp_path):
        """Test scanning nonexistent project."""
        nonexistent = tmp_path / "does_not_exist"

        variables = scanner.scan_project(nonexistent)

        # Should return empty list
        assert len(variables) == 0

    def test_ignore_env_files(self, scanner, temp_project):
        """Test that .env files are ignored."""
        env_file = temp_project / ".env"
        env_file.write_text("SECRET={{SHOULD_IGNORE}}")

        # Create normal file
        (temp_project / "README.md").write_text("{{PROJECT_NAME}}")

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "SHOULD_IGNORE" not in var_names

    def test_ignore_lockfiles(self, scanner, temp_project):
        """Test that package lock files are ignored."""
        # Create lockfiles
        (temp_project / "package-lock.json").write_text('{"name": "{{IGNORE}}"}')
        (temp_project / "yarn.lock").write_text("{{IGNORE}}")
        (temp_project / "pnpm-lock.yaml").write_text("name: {{IGNORE}}")

        # Create normal file
        (temp_project / "package.json").write_text('{"name": "{{PROJECT_NAME}}"}')

        variables = scanner.scan_project(temp_project)

        var_names = [v.name for v in variables]
        assert "PROJECT_NAME" in var_names
        assert "IGNORE" not in var_names

    def test_variable_locations_relative_paths(self, scanner, temp_project):
        """Test that variable locations use relative paths."""
        # Create nested structure
        subdir = temp_project / "src" / "components"
        subdir.mkdir(parents=True)
        (subdir / "Component.tsx").write_text("const name = '{{PROJECT_NAME}}';")

        variables = scanner.scan_project(temp_project)

        project_var = next(v for v in variables if v.name == "PROJECT_NAME")
        # Should use forward slashes and be relative
        assert "src" in project_var.locations[0]
        assert "components" in project_var.locations[0]
        assert "Component.tsx" in project_var.locations[0]

    def test_performance_many_files(self, scanner, temp_project):
        """Test performance with many files."""
        import time

        # Create 100 files with variables
        for i in range(100):
            file = temp_project / f"file_{i}.md"
            file.write_text(f"# {{{{VAR_{i}}}}}\n{{{{COMMON_VAR}}}}")

        start = time.time()
        variables = scanner.scan_project(temp_project)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 2 seconds for 100 files)
        assert elapsed < 2.0

        # Should find all variables (100 unique + 1 common)
        assert len(variables) == 101


class TestTemplateVariable:
    """Tests for TemplateVariable dataclass."""

    def test_create_variable(self):
        """Test creating TemplateVariable."""
        var = TemplateVariable(
            name="TEST_VAR",
            format="double_brace",
            locations=["file1.md", "file2.md"],
        )

        assert var.name == "TEST_VAR"
        assert var.format == "double_brace"
        assert len(var.locations) == 2
        assert var.required is True

    def test_default_values(self):
        """Test default values."""
        var = TemplateVariable(name="TEST", format="double_brace")

        assert var.locations == []
        assert var.required is True

    def test_post_init_converts_to_list(self):
        """Test that post_init ensures locations is a list."""
        var = TemplateVariable(
            name="TEST",
            format="double_brace",
            locations=("file1.md", "file2.md"),
        )

        assert isinstance(var.locations, list)
        assert len(var.locations) == 2
