"""Tests for scripts/bump_version.py."""

import subprocess
import sys
from pathlib import Path

import pytest


# Get the project root and scripts path
PROJECT_ROOT = Path(__file__).parent.parent.parent
BUMP_VERSION_SCRIPT = PROJECT_ROOT / "scripts" / "bump_version.py"


class TestBumpVersionScript:
    """Test suite for bump_version.py script."""

    def test_bump_minor_version(self) -> None:
        """Test bumping minor version."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0", "minor"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0.2.0"

    def test_bump_patch_version(self) -> None:
        """Test bumping patch version."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0", "patch"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0.1.1"

    def test_bump_major_version(self) -> None:
        """Test bumping major version."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0", "major"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "1.0.0"

    def test_bump_version_with_v_prefix(self) -> None:
        """Test bumping version with 'v' prefix."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "v0.1.0", "minor"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0.2.0"

    def test_bump_version_with_prerelease(self) -> None:
        """Test bumping version with prerelease suffix."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0-beta.1", "patch"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0.1.1"

    def test_bump_version_invalid_type(self) -> None:
        """Test error handling for invalid bump type."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0", "invalid"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "Invalid bump type" in result.stderr

    def test_bump_version_missing_args(self) -> None:
        """Test error handling for missing arguments."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_bump_version_invalid_format(self) -> None:
        """Test error handling for invalid version format."""
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "1.0", "minor"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "Invalid version format" in result.stderr

    def test_bump_multiple_times(self) -> None:
        """Test multiple sequential bumps."""
        # Start with 0.1.0
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.1.0", "patch"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        version = result.stdout.strip()
        assert version == "0.1.1"

        # Bump again
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), version, "minor"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        version = result.stdout.strip()
        assert version == "0.2.0"

        # Bump major
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), version, "major"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "1.0.0"

    def test_bump_edge_cases(self) -> None:
        """Test edge cases like 0.0.0 and high numbers."""
        # From 0.0.0
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "0.0.0", "patch"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0.0.1"

        # High version numbers
        result = subprocess.run(
            [sys.executable, str(BUMP_VERSION_SCRIPT), "99.99.99", "major"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "100.0.0"
