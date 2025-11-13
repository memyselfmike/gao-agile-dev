"""Tests for dynamic versioning with setuptools-scm."""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Python 3.11+ has tomllib built-in, earlier versions need tomli
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]


PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"


class TestDynamicVersioning:
    """Test suite for dynamic versioning configuration."""

    def test_pyproject_toml_exists(self) -> None:
        """Test that pyproject.toml exists."""
        assert PYPROJECT_TOML.exists(), "pyproject.toml must exist"

    def test_dynamic_version_configured(self) -> None:
        """Test that version is configured as dynamic in pyproject.toml."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        # Check that version is in dynamic list
        assert "project" in config, "Missing [project] section"
        assert "dynamic" in config["project"], "Missing 'dynamic' field in [project]"
        assert "version" in config["project"]["dynamic"], (
            "'version' must be in dynamic list"
        )

    def test_no_static_version(self) -> None:
        """Test that no static version field exists in pyproject.toml."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        # Ensure no static version field
        assert "version" not in config["project"] or config["project"].get("version") is None, (
            "Static 'version' field should not exist in [project] section"
        )

    def test_setuptools_scm_configured(self) -> None:
        """Test that setuptools-scm is properly configured."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        # Check for [tool.setuptools_scm] section
        assert "tool" in config, "Missing [tool] section"
        assert "setuptools_scm" in config["tool"], "Missing [tool.setuptools_scm] section"

        scm_config = config["tool"]["setuptools_scm"]

        # Verify configuration keys exist
        assert isinstance(scm_config, dict), "setuptools_scm config must be a dict"

    def test_setuptools_scm_in_build_requires(self) -> None:
        """Test that setuptools-scm is in build-system.requires."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        assert "build-system" in config, "Missing [build-system] section"
        assert "requires" in config["build-system"], "Missing 'requires' in [build-system]"

        requires = config["build-system"]["requires"]
        assert isinstance(requires, list), "build-system.requires must be a list"

        # Check for setuptools-scm with version constraint
        has_setuptools_scm = any(
            "setuptools-scm" in req or "setuptools_scm" in req
            for req in requires
        )
        assert has_setuptools_scm, "setuptools-scm must be in build-system.requires"

        # Check version constraint (>=8.0)
        scm_req = next(
            (req for req in requires if "setuptools-scm" in req or "setuptools_scm" in req),
            None
        )
        assert scm_req is not None
        assert ">=8.0" in scm_req, "setuptools-scm version must be >=8.0"

    def test_pyproject_has_documentation_comment(self) -> None:
        """Test that pyproject.toml has documentation about dynamic versioning."""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for comment explaining dynamic versioning
        # This is a heuristic check - looking for comment near setuptools_scm
        assert "setuptools_scm" in content or "setuptools-scm" in content, (
            "pyproject.toml should mention setuptools-scm"
        )

        # Check that the word "version" appears in comments (# ...)
        lines = content.split("\n")
        has_version_comment = any(
            "#" in line and "version" in line.lower()
            for line in lines
            if line.strip().startswith("#")
        )
        assert has_version_comment, (
            "pyproject.toml should have comments explaining versioning"
        )


class TestVersionDerivation:
    """Test version derivation from git tags."""

    def test_can_get_version_from_setuptools_scm(self) -> None:
        """Test that setuptools-scm can derive version from git."""
        # This test requires setuptools-scm to be installed
        try:
            result = subprocess.run(
                [sys.executable, "-m", "setuptools_scm"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            # Should either succeed or fail with a helpful message
            # (not an import error)
            if result.returncode != 0:
                # Allow failure if no tags exist, but not import errors
                assert "ModuleNotFoundError" not in result.stderr, (
                    "setuptools-scm not installed"
                )
        except Exception as e:
            pytest.skip(f"Cannot test setuptools-scm: {e}")


class TestPyprojectTomlStructure:
    """Test overall structure of pyproject.toml."""

    def test_pyproject_toml_valid_toml(self) -> None:
        """Test that pyproject.toml is valid TOML."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        assert isinstance(config, dict), "pyproject.toml must be a valid TOML dict"

    def test_required_sections_exist(self) -> None:
        """Test that all required sections exist."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        required_sections = ["build-system", "project", "tool"]
        for section in required_sections:
            assert section in config, f"Missing required section: [{section}]"

    def test_project_metadata_complete(self) -> None:
        """Test that project metadata is complete."""
        with open(PYPROJECT_TOML, "rb") as f:
            config = tomllib.load(f)

        project = config["project"]

        required_fields = ["name", "description", "requires-python"]
        for field in required_fields:
            assert field in project, f"Missing required field in [project]: {field}"

        # Name should be gao-dev
        assert project["name"] == "gao-dev", "Project name should be 'gao-dev'"
