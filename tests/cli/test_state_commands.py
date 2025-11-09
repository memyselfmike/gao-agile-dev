"""Tests for state CLI commands."""

import pytest
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner

from gao_dev.cli.state_commands import (
    state,
    get_state_tracker,
)
from gao_dev.core.state.state_tracker import StateTracker


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Create temporary database with schema."""
    db_file = tmp_path / "gao_dev.db"

    # Set database path via environment variable
    monkeypatch.setenv("GAO_DEV_DB_PATH", str(db_file))

    # Reset the singleton to pick up new environment variable
    from gao_dev.core.config import DatabaseConfig
    DatabaseConfig.reset_default()

    # Create schema
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            feature TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            total_points INTEGER DEFAULT 0,
            completed_points INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            owner TEXT,
            points INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'P1',
            content_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (epic_num) REFERENCES epics(epic_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE sprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE story_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_num INTEGER NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(epic_num, story_num),
            FOREIGN KEY (sprint_num) REFERENCES sprints(sprint_num),
            FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_name TEXT NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            status TEXT NOT NULL,
            executor TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            duration_ms INTEGER,
            output TEXT
        )
    """)

    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def tracker(db_path):
    """Create StateTracker with test database."""
    return StateTracker(db_path)


@pytest.fixture
def sample_data(tracker):
    """Create sample data for testing."""
    # Create epics
    tracker.create_epic(15, "State Tracking Database", "document-lifecycle-system", 20)
    tracker.create_epic(16, "Document Templates", "document-lifecycle-system", 15)

    # Create sprint
    tracker.create_sprint(5, "2025-11-01", "2025-11-15")

    # Create stories for epic 15
    tracker.create_story(15, 1, "Schema Design", status="done", points=3, sprint=5)
    tracker.create_story(15, 2, "StateTracker Implementation", status="done", points=5, sprint=5)
    tracker.create_story(15, 3, "Markdown Syncer", status="in_progress", points=5, owner="Amelia")
    tracker.create_story(15, 4, "Query Builder", status="pending", points=4)

    # Update epic points
    tracker.update_epic_points(15, 20, 8)

    return tracker


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestStoryCommand:
    """Test 'state story' command."""

    def test_story_table_format(self, runner, db_path, sample_data, monkeypatch):
        """Test story command with table format."""
        # Change to temp directory
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["story", "15", "1", "--format", "table"])
        assert result.exit_code == 0
        assert "Schema Design" in result.output
        assert "done" in result.output

    def test_story_json_format(self, runner, db_path, sample_data, monkeypatch):
        """Test story command with JSON format."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["story", "15", "1", "--format", "json"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["epic"] == 15
        assert data["story_num"] == 1
        assert data["title"] == "Schema Design"
        assert data["status"] == "done"

    def test_story_csv_format(self, runner, db_path, sample_data, monkeypatch):
        """Test story command with CSV format."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["story", "15", "1", "--format", "csv"])
        assert result.exit_code == 0
        assert "Schema Design" in result.output
        assert "done" in result.output

    def test_story_not_found(self, runner, db_path, sample_data, monkeypatch):
        """Test story command with non-existent story."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["story", "999", "1"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestEpicCommand:
    """Test 'state epic' command."""

    def test_epic_table_format(self, runner, db_path, sample_data, monkeypatch):
        """Test epic command with table format."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["epic", "15", "--format", "table"])
        assert result.exit_code == 0
        assert "State Tracking Database" in result.output

    def test_epic_json_format(self, runner, db_path, sample_data, monkeypatch):
        """Test epic command with JSON format."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["epic", "15", "--format", "json"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["epic_num"] == 15
        assert data["title"] == "State Tracking Database"
        assert data["total_points"] == 20
        assert data["completed_points"] == 8

    def test_epic_not_found(self, runner, db_path, sample_data, monkeypatch):
        """Test epic command with non-existent epic."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["epic", "999"])
        assert result.exit_code != 0


class TestSprintCommand:
    """Test 'state sprint' command."""

    def test_sprint_specific_number(self, runner, db_path, sample_data, monkeypatch):
        """Test sprint command with specific sprint number."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["sprint", "5", "--format", "table"])
        assert result.exit_code == 0
        assert "Sprint 5" in result.output

    def test_sprint_json_format(self, runner, db_path, sample_data, monkeypatch):
        """Test sprint command with JSON format."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["sprint", "5", "--format", "json"])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["sprint_num"] == 5
        assert data["sprint_name"] == "Sprint 5"
        assert "velocity" in data

    def test_sprint_current(self, runner, db_path, sample_data, monkeypatch):
        """Test sprint command without number (current sprint)."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["sprint"])
        assert result.exit_code == 0
        assert "Sprint 5" in result.output


class TestQueryCommand:
    """Test 'state query' command."""

    def test_query_select(self, runner, db_path, sample_data, monkeypatch):
        """Test query command with SELECT."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(
            state, ["query", "SELECT epic_num, story_num, title FROM stories LIMIT 2"]
        )
        assert result.exit_code == 0
        assert "Schema Design" in result.output

    def test_query_rejects_write_operations(self, runner, db_path, sample_data, monkeypatch):
        """Test query command rejects write operations."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["query", "DELETE FROM stories"])
        assert result.exit_code != 0
        assert "SELECT queries" in result.output

        result = runner.invoke(state, ["query", "UPDATE stories SET status='done'"])
        assert result.exit_code != 0

        result = runner.invoke(state, ["query", "INSERT INTO stories VALUES (1,1,1,'test','done',NULL,0,'P1',NULL,'','')"])
        assert result.exit_code != 0


class TestInitCommand:
    """Test 'state init' command."""

    def test_init_creates_database(self, runner, tmp_path, monkeypatch):
        """Test init command creates database."""
        monkeypatch.chdir(tmp_path)

        # Reset config to pick up current directory
        from gao_dev.core.config import DatabaseConfig
        DatabaseConfig.reset_default()

        result = runner.invoke(state, ["init"])
        assert result.exit_code == 0

        db_path = tmp_path / "gao_dev.db"
        assert db_path.exists()

    def test_init_with_existing_database(self, runner, db_path, monkeypatch):
        """Test init command with existing database."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["init"])
        assert result.exit_code == 0
        assert "already exists" in result.output.lower()

    def test_init_force_overwrite(self, runner, db_path, monkeypatch):
        """Test init command with --force flag."""
        monkeypatch.chdir(db_path.parent)

        # Config is already set by db_path fixture, so force should work
        result = runner.invoke(state, ["init", "--force"])
        assert result.exit_code == 0


class TestSyncCommand:
    """Test 'state sync' command."""

    def test_sync_with_default_directory(self, runner, db_path, sample_data, tmp_path, monkeypatch):
        """Test sync command with default directory."""
        monkeypatch.chdir(db_path.parent)

        # Create a story file
        stories_dir = db_path.parent / "docs" / "features" / "test" / "stories" / "epic-15"
        stories_dir.mkdir(parents=True)

        story_file = stories_dir / "story-15.5.md"
        story_file.write_text(
            """---
epic: 15
story_num: 5
title: Test Story
status: pending
points: 3
---

## Description
Test story for sync.
"""
        )

        result = runner.invoke(state, ["sync"])
        assert result.exit_code == 0
        assert "Created" in result.output or "Skipped" in result.output


class TestDashboardCommand:
    """Test 'state dashboard' command."""

    def test_dashboard_shows_active_work(self, runner, db_path, sample_data, monkeypatch):
        """Test dashboard command shows active work."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["dashboard"])
        # May fail if rich not available, check for either success or error message
        assert result.exit_code == 0 or "Rich library not installed" in result.output


class TestErrorHandling:
    """Test error handling."""

    def test_commands_require_database(self, runner, tmp_path, monkeypatch):
        """Test commands fail gracefully without database."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(state, ["story", "1", "1"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "init" in result.output.lower()

    def test_invalid_format_option(self, runner, db_path, sample_data, monkeypatch):
        """Test invalid format option."""
        monkeypatch.chdir(db_path.parent)

        result = runner.invoke(state, ["story", "15", "1", "--format", "invalid"])
        assert result.exit_code != 0
