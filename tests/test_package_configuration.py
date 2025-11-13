"""
Tests for package configuration.

Story 36.11: Update pyproject.toml Package Configuration
"""

import pytest
import tomllib
from pathlib import Path


class TestPackageConfiguration:
    """Test package configuration in pyproject.toml."""

    @pytest.fixture
    def pyproject_config(self) -> dict:
        """Load pyproject.toml configuration."""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            return tomllib.load(f)

    def test_package_data_includes_workflows(self, pyproject_config: dict):
        """Test package-data includes workflows."""
        package_data = pyproject_config["tool"]["setuptools"]["package-data"]["gao_dev"]

        assert "workflows/**/*" in package_data

    def test_package_data_includes_config(self, pyproject_config: dict):
        """Test package-data includes config files."""
        package_data = pyproject_config["tool"]["setuptools"]["package-data"]["gao_dev"]

        assert "config/**/*" in package_data

    def test_package_data_includes_templates(self, pyproject_config: dict):
        """Test package-data includes templates."""
        package_data = pyproject_config["tool"]["setuptools"]["package-data"]["gao_dev"]

        assert "templates/**/*" in package_data

    def test_package_data_includes_migrations(self, pyproject_config: dict):
        """Test package-data includes migrations."""
        package_data = pyproject_config["tool"]["setuptools"]["package-data"]["gao_dev"]

        assert "migrations/**/*" in package_data

    def test_package_data_includes_gaodev_source(self, pyproject_config: dict):
        """Test package-data includes .gaodev-source marker."""
        package_data = pyproject_config["tool"]["setuptools"]["package-data"]["gao_dev"]

        assert "../.gaodev-source" in package_data

    def test_exclude_package_data_excludes_tests(self, pyproject_config: dict):
        """Test exclude-package-data excludes tests."""
        exclude_data = pyproject_config["tool"]["setuptools"]["exclude-package-data"]["*"]

        assert "tests" in exclude_data

    def test_exclude_package_data_excludes_docs(self, pyproject_config: dict):
        """Test exclude-package-data excludes docs."""
        exclude_data = pyproject_config["tool"]["setuptools"]["exclude-package-data"]["*"]

        assert "docs" in exclude_data

    def test_exclude_package_data_excludes_sandbox_projects(self, pyproject_config: dict):
        """Test exclude-package-data excludes sandbox projects."""
        exclude_data = pyproject_config["tool"]["setuptools"]["exclude-package-data"]["*"]

        assert "sandbox/projects" in exclude_data

    def test_development_status_is_beta(self, pyproject_config: dict):
        """Test classifiers include Beta status."""
        classifiers = pyproject_config["project"]["classifiers"]

        assert "Development Status :: 4 - Beta" in classifiers

    def test_development_status_not_alpha(self, pyproject_config: dict):
        """Test classifiers no longer include Alpha status."""
        classifiers = pyproject_config["project"]["classifiers"]

        assert "Development Status :: 3 - Alpha" not in classifiers

    def test_dynamic_versioning_enabled(self, pyproject_config: dict):
        """Test dynamic versioning is enabled."""
        assert "version" in pyproject_config["project"]["dynamic"]

    def test_setuptools_scm_configured(self, pyproject_config: dict):
        """Test setuptools-scm is configured."""
        assert "tool" in pyproject_config
        assert "setuptools_scm" in pyproject_config["tool"]

        scm_config = pyproject_config["tool"]["setuptools_scm"]
        assert scm_config["version_scheme"] == "no-guess-dev"
        assert scm_config["local_scheme"] == "no-local-version"

    def test_gaodev_source_marker_exists(self):
        """Test .gaodev-source marker file exists."""
        marker_path = Path(__file__).parent.parent / ".gaodev-source"
        assert marker_path.exists(), ".gaodev-source marker file should exist"

    def test_gaodev_source_marker_content(self):
        """Test .gaodev-source marker has correct content."""
        marker_path = Path(__file__).parent.parent / ".gaodev-source"

        if marker_path.exists():
            content = marker_path.read_text().strip()
            # Should contain repository URL or identifier
            assert len(content) > 0, ".gaodev-source should not be empty"
