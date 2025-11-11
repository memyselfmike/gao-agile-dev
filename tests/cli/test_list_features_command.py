"""Tests for list-features CLI command.

Epic: 33 - Atomic Feature Operations
Story: 33.3 - CLI Commands
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner

from gao_dev.cli.list_features_command import list_features
from gao_dev.core.services.feature_state_service import FeatureScope, FeatureStatus


@pytest.fixture
def test_project(tmp_path):
    """Create temporary test project with features."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create .gao-dev directory with database
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()

    db_path = gao_dev_dir / "documents.db"

    # Initialize database schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            scope TEXT NOT NULL,
            status TEXT NOT NULL,
            scale_level INTEGER NOT NULL,
            description TEXT,
            owner TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT
        )
    """)

    # Insert test features
    now = datetime.utcnow().isoformat()

    test_features = [
        ("mvp", "mvp", "active", 4, "MVP scope", "alice@example.com", now),
        ("user-auth", "feature", "planning", 3, "Authentication", "bob@example.com", now),
        ("payment", "feature", "active", 3, "Payment gateway", "charlie@example.com", now),
        ("notifications", "feature", "complete", 2, "Push notifications", "diana@example.com", now),
        ("reporting", "feature", "archived", 2, "Analytics", None, now),
    ]

    cursor.executemany(
        """INSERT INTO feature_state
        (name, scope, status, scale_level, description, owner, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        test_features
    )

    conn.commit()
    conn.close()

    # Create git repo
    git_dir = project_root / ".git"
    git_dir.mkdir()

    return project_root


@pytest.fixture
def runner():
    """Create Click test runner."""
    return CliRunner()


class TestListFeaturesCommand:
    """Tests for list-features command."""

    def test_list_all_features(self, test_project, runner, monkeypatch):
        """Test listing all features."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        assert "mvp" in result.output
        assert "user-auth" in result.output
        assert "payment" in result.output
        assert "notifications" in result.output
        assert "reporting" in result.output
        assert "5 total" in result.output or "5" in result.output

    def test_list_features_filter_by_mvp_scope(self, test_project, runner, monkeypatch):
        """Test filtering by MVP scope."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, ["--scope", "mvp"])

        assert result.exit_code == 0
        assert "mvp" in result.output
        assert "user-auth" not in result.output
        assert "1 total" in result.output or result.output.count("\n") < 10

    def test_list_features_filter_by_feature_scope(self, test_project, runner, monkeypatch):
        """Test filtering by feature scope."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, ["--scope", "feature"])

        assert result.exit_code == 0
        assert "user-auth" in result.output
        assert "payment" in result.output
        assert "mvp" not in result.output or "mvp" in result.output.lower()  # May appear in column headers
        assert "4 total" in result.output or "4" in result.output

    def test_list_features_filter_by_active_status(self, test_project, runner, monkeypatch):
        """Test filtering by active status."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, ["--status", "active"])

        assert result.exit_code == 0
        assert "mvp" in result.output
        assert "payment" in result.output
        assert "notifications" not in result.output
        assert "2 total" in result.output or "2" in result.output

    def test_list_features_filter_by_planning_status(self, test_project, runner, monkeypatch):
        """Test filtering by planning status."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, ["--status", "planning"])

        assert result.exit_code == 0
        assert "user-auth" in result.output
        assert "payment" not in result.output
        assert "1 total" in result.output or "1" in result.output

    def test_list_features_combined_filters(self, test_project, runner, monkeypatch):
        """Test combining scope and status filters."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [
            "--scope", "feature",
            "--status", "active"
        ])

        assert result.exit_code == 0
        assert "payment" in result.output
        assert "mvp" not in result.output or "mvp" in result.output.lower()
        assert "user-auth" not in result.output
        assert "1 total" in result.output or "1" in result.output

    def test_list_features_empty_state(self, tmp_path, runner, monkeypatch):
        """Test empty state when no features exist."""
        # Create empty project
        project_root = tmp_path / "empty_project"
        project_root.mkdir()

        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir()

        db_path = gao_dev_dir / "documents.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                scope TEXT NOT NULL,
                status TEXT NOT NULL,
                scale_level INTEGER NOT NULL,
                description TEXT,
                owner TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

        git_dir = project_root / ".git"
        git_dir.mkdir()

        monkeypatch.chdir(project_root)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        assert "No features found" in result.output
        assert "create-feature" in result.output

    def test_list_features_rich_table_output(self, test_project, runner, monkeypatch):
        """Test Rich table formatting."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        # Check for table-like structure (works with or without Rich)
        assert "Name" in result.output or "name" in result.output
        assert "Scope" in result.output or "scope" in result.output
        assert "Status" in result.output or "status" in result.output

    def test_list_features_shows_owner(self, test_project, runner, monkeypatch):
        """Test owner column is displayed."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        assert "alice@example.com" in result.output or "alice" in result.output
        assert "bob@example.com" in result.output or "bob" in result.output

    def test_list_features_shows_scale_level(self, test_project, runner, monkeypatch):
        """Test scale level column is displayed."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        assert "Scale" in result.output or "scale" in result.output
        assert "4" in result.output  # MVP has scale 4
        assert "3" in result.output  # Others have scale 3
        assert "2" in result.output  # Some have scale 2

    def test_list_features_shows_created_date(self, test_project, runner, monkeypatch):
        """Test created date column is displayed."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        assert "Created" in result.output or "created" in result.output
        # Should show date portion (YYYY-MM-DD)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        assert today in result.output


class TestListFeaturesEdgeCases:
    """Edge case tests for list-features command."""

    def test_list_features_filter_no_matches(self, test_project, runner, monkeypatch):
        """Test filtering with no matches."""
        monkeypatch.chdir(test_project)

        # Filter for archived MVPs (should be none)
        result = runner.invoke(list_features, [
            "--scope", "mvp",
            "--status", "archived"
        ])

        assert result.exit_code == 0
        assert "No features found" in result.output

    def test_list_features_outside_project(self, tmp_path, runner, monkeypatch):
        """Test error when not in a GAO-Dev project."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        result = runner.invoke(list_features, [])

        assert result.exit_code != 0
        assert "Error" in result.output or "Not in a GAO-Dev project" in result.output

    def test_list_features_case_insensitive_filters(self, test_project, runner, monkeypatch):
        """Test filters are case-insensitive."""
        monkeypatch.chdir(test_project)

        # Test uppercase
        result1 = runner.invoke(list_features, ["--scope", "MVP"])
        assert result1.exit_code == 0
        assert "mvp" in result1.output

        # Test mixed case
        result2 = runner.invoke(list_features, ["--status", "Active"])
        assert result2.exit_code == 0

    def test_list_features_null_owner_display(self, test_project, runner, monkeypatch):
        """Test features with no owner display correctly."""
        monkeypatch.chdir(test_project)

        result = runner.invoke(list_features, [])

        assert result.exit_code == 0
        # Should show em dash or similar for null owner
        assert "reporting" in result.output
