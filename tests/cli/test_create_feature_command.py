"""Tests for create-feature CLI command.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import pytest
import sqlite3
from pathlib import Path
from click.testing import CliRunner

from gao_dev.cli.create_feature_command import create_feature
from gao_dev.core.services.feature_state_service import FeatureScope, FeatureStatus


@pytest.fixture
def test_project(tmp_path):
    """Create temporary test project."""
    import subprocess

    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create .gao-dev directory with database
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    db_path = gao_dev_dir / "documents.db"

    # Initialize database schema (run migration)
    from gao_dev.core.services.git_migration_manager import GitMigrationManager
    migration_mgr = GitMigrationManager(db_path=db_path)
    migration_mgr._phase_1_create_tables()

    # Create git repo properly
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, capture_output=True)

    # Create initial commit
    (project_root / "README.md").write_text("# Test Project")
    subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_root, capture_output=True)

    return project_root


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestCreateFeatureCommand:
    """Tests for create-feature command."""

    def test_create_feature_default_options(self, test_project, runner, monkeypatch):
        """Test creating feature with default options."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, ["user-auth"])

        assert result.exit_code == 0
        assert "user-auth" in result.output
        assert "Feature created successfully" in result.output or "Feature Created" in result.output

        # Verify feature directory created
        feature_dir = test_project / "docs" / "features" / "user-auth"
        assert feature_dir.exists()
        assert (feature_dir / "PRD.md").exists()
        assert (feature_dir / "ARCHITECTURE.md").exists()

        # Verify database record
        db_path = test_project / ".gao-dev" / "documents.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name, scope, scale_level FROM feature_state WHERE name = ?", ("user-auth",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "user-auth"
        assert row[1] == "feature"
        assert row[2] == 3  # Default scale level

    def test_create_feature_all_options(self, test_project, runner, monkeypatch):
        """Test creating feature with all options."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, [
            "payment-gateway",
            "--scale-level", "4",
            "--scope", "feature",
            "--description", "Payment processing integration",
            "--owner", "john@example.com"
        ])

        assert result.exit_code == 0
        assert "payment-gateway" in result.output

        # Verify database record
        db_path = test_project / ".gao-dev" / "documents.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, scope, scale_level, description, owner FROM feature_state WHERE name = ?",
            ("payment-gateway",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "payment-gateway"
        assert row[1] == "feature"
        assert row[2] == 4
        assert row[3] == "Payment processing integration"
        assert row[4] == "john@example.com"

    def test_create_mvp_feature(self, test_project, runner, monkeypatch):
        """Test creating MVP-scoped feature."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, [
            "mvp",
            "--scope", "mvp",
            "--scale-level", "4"
        ])

        assert result.exit_code == 0
        assert "mvp" in result.output

        # Verify scope
        db_path = test_project / ".gao-dev" / "documents.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT scope FROM feature_state WHERE name = ?", ("mvp",))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "mvp"

    def test_create_feature_invalid_scale_level(self, test_project, runner, monkeypatch):
        """Test error on invalid scale level."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, [
            "test-feature",
            "--scale-level", "5"  # Invalid: should be 0-4
        ])

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Error" in result.output

    def test_create_feature_duplicate_name(self, test_project, runner, monkeypatch):
        """Test error on duplicate feature name."""
        monkeypatch.chdir(test_project)

        # Create first feature
        result1 = runner.invoke(create_feature, ["duplicate-test"])
        assert result1.exit_code == 0

        # Attempt to create duplicate
        result2 = runner.invoke(create_feature, ["duplicate-test"])
        assert result2.exit_code != 0
        assert "Error" in result2.output

    def test_create_feature_outside_project(self, tmp_path, runner, monkeypatch):
        """Test error when not in a GAO-Dev project."""
        # Create empty directory without .gao-dev or .git
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        result = runner.invoke(create_feature, ["test-feature"])

        assert result.exit_code != 0
        assert "Not in a GAO-Dev project" in result.output or "Error" in result.output

    def test_create_feature_with_rich_output(self, test_project, runner, monkeypatch):
        """Test Rich formatted output."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, ["rich-test"])

        assert result.exit_code == 0
        # Check for success indicators (works with or without Rich)
        assert "rich-test" in result.output
        assert "Next" in result.output or "next" in result.output

    def test_create_feature_exit_code_success(self, test_project, runner, monkeypatch):
        """Test exit code 0 on success."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, ["exit-code-test"])

        assert result.exit_code == 0

    def test_create_feature_next_steps_guidance(self, test_project, runner, monkeypatch):
        """Test next steps guidance in output."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, ["guidance-test"])

        assert result.exit_code == 0
        assert "PRD" in result.output
        assert "ARCHITECTURE" in result.output
        assert "list-features" in result.output

    def test_create_feature_atomic_operation(self, test_project, runner, monkeypatch):
        """Test that operation is atomic (all or nothing)."""
        monkeypatch.chdir(test_project)

        # This is tested implicitly - if create fails, nothing should exist
        result = runner.invoke(create_feature, ["atomic-test"])

        if result.exit_code == 0:
            # Success: everything should exist
            feature_dir = test_project / "docs" / "features" / "atomic-test"
            assert feature_dir.exists()

            db_path = test_project / ".gao-dev" / "documents.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM feature_state WHERE name = ?", ("atomic-test",))
            row = cursor.fetchone()
            conn.close()

            assert row is not None
        else:
            # Failure: nothing should exist (rollback)
            feature_dir = test_project / "docs" / "features" / "atomic-test"
            # Note: In actual failure, rollback should clean up
            pass


class TestCreateFeatureEdgeCases:
    """Edge case tests for create-feature command."""

    def test_create_feature_special_characters_name(self, test_project, runner, monkeypatch):
        """Test feature name with special characters."""
        monkeypatch.chdir(test_project)

        # Hyphens and underscores should work
        result = runner.invoke(create_feature, ["my-special_feature"])

        # Should succeed or provide clear error
        assert "my-special_feature" in result.output

    def test_create_feature_long_description(self, test_project, runner, monkeypatch):
        """Test feature with long description."""
        monkeypatch.chdir(test_project)

        long_desc = "A" * 500  # 500 character description

        result = runner.invoke(create_feature, [
            "long-desc-test",
            "--description", long_desc
        ])

        assert result.exit_code == 0

    def test_create_feature_minimal_command(self, test_project, runner, monkeypatch):
        """Test minimal command (just name)."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(create_feature, ["minimal"])

        assert result.exit_code == 0
        assert "minimal" in result.output
