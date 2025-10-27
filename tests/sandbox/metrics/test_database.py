"""Tests for metrics database.

Tests database schema creation, connection management, and helper methods.
"""

import pytest
import tempfile
from pathlib import Path
import sqlite3

from gao_dev.sandbox.metrics.database import MetricsDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metrics.db"
        yield db_path


class TestMetricsDatabase:
    """Tests for MetricsDatabase class."""

    def test_database_creation(self, temp_db):
        """Test database file created automatically."""
        assert not temp_db.exists()
        db = MetricsDatabase(temp_db)
        assert temp_db.exists()

    def test_schema_initialization(self, temp_db):
        """Test all tables and indexes created."""
        db = MetricsDatabase(temp_db)

        with db.connection() as conn:
            cursor = conn.cursor()

            # Check that all tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "autonomy_metrics",
                "benchmark_runs",
                "performance_metrics",
                "quality_metrics",
                "workflow_metrics",
            ]

            assert sorted(tables) == sorted(expected_tables)

            # Check that indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            assert "idx_runs_timestamp" in indexes
            assert "idx_runs_project" in indexes
            assert "idx_runs_benchmark" in indexes
            assert "idx_performance_run_id" in indexes
            assert "idx_autonomy_run_id" in indexes
            assert "idx_quality_run_id" in indexes
            assert "idx_workflow_run_id" in indexes

    def test_connection_context_manager(self, temp_db):
        """Test connection lifecycle with context manager."""
        db = MetricsDatabase(temp_db)

        # Test that connection works and is closed properly
        with db.connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

        # Connection should be closed now
        # Verify by trying to use it (should raise)
        with pytest.raises(sqlite3.ProgrammingError):
            cursor.execute("SELECT 1")

    def test_custom_database_path(self, temp_db):
        """Test specifying custom database path."""
        custom_path = temp_db.parent / "custom_metrics.db"
        db = MetricsDatabase(custom_path)

        assert db.db_path == custom_path
        assert custom_path.exists()

    def test_default_database_path(self):
        """Test default database path."""
        db = MetricsDatabase()
        expected_path = Path.home() / ".gao-dev" / "metrics.db"
        assert db.db_path == expected_path

    def test_schema_version(self, temp_db):
        """Test schema version tracking."""
        db = MetricsDatabase(temp_db)
        assert db.get_schema_version() == 1

    def test_foreign_key_constraints(self, temp_db):
        """Test referential integrity with foreign keys."""
        db = MetricsDatabase(temp_db)

        with db.connection() as conn:
            cursor = conn.cursor()

            # Try to insert metrics without corresponding run (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute("""
                    INSERT INTO performance_metrics
                    (run_id, total_time_seconds, token_usage_total, api_calls_count, api_calls_cost)
                    VALUES ('nonexistent-run', 100.0, 1000, 10, 1.0)
                """)

            # Insert a run first
            cursor.execute("""
                INSERT INTO benchmark_runs
                (run_id, timestamp, project_name, benchmark_name)
                VALUES ('test-run', '2025-10-27T10:00:00Z', 'test', 'test')
            """)

            # Now metrics insert should succeed
            cursor.execute("""
                INSERT INTO performance_metrics
                (run_id, total_time_seconds, token_usage_total, api_calls_count, api_calls_cost)
                VALUES ('test-run', 100.0, 1000, 10, 1.0)
            """)

            conn.commit()

            # Verify it was inserted
            cursor.execute("SELECT * FROM performance_metrics WHERE run_id = ?", ("test-run",))
            assert cursor.fetchone() is not None

    def test_cascade_delete(self, temp_db):
        """Test cascade delete removes related metrics."""
        db = MetricsDatabase(temp_db)

        with db.connection() as conn:
            cursor = conn.cursor()

            # Insert a run and its metrics
            cursor.execute("""
                INSERT INTO benchmark_runs
                (run_id, timestamp, project_name, benchmark_name)
                VALUES ('cascade-test', '2025-10-27T10:00:00Z', 'test', 'test')
            """)

            cursor.execute("""
                INSERT INTO performance_metrics
                (run_id, total_time_seconds, token_usage_total, api_calls_count, api_calls_cost)
                VALUES ('cascade-test', 100.0, 1000, 10, 1.0)
            """)

            cursor.execute("""
                INSERT INTO autonomy_metrics
                (run_id, manual_interventions_count, prompts_needed_initial,
                 prompts_needed_followup, one_shot_success_rate, error_recovery_rate,
                 agent_handoffs_successful, agent_handoffs_failed)
                VALUES ('cascade-test', 0, 1, 0, 1.0, 1.0, 5, 0)
            """)

            conn.commit()

            # Verify metrics exist
            cursor.execute("SELECT COUNT(*) FROM performance_metrics WHERE run_id = ?", ("cascade-test",))
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM autonomy_metrics WHERE run_id = ?", ("cascade-test",))
            assert cursor.fetchone()[0] == 1

            # Delete the run
            cursor.execute("DELETE FROM benchmark_runs WHERE run_id = ?", ("cascade-test",))
            conn.commit()

            # Verify metrics were deleted via cascade
            cursor.execute("SELECT COUNT(*) FROM performance_metrics WHERE run_id = ?", ("cascade-test",))
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT COUNT(*) FROM autonomy_metrics WHERE run_id = ?", ("cascade-test",))
            assert cursor.fetchone()[0] == 0

    def test_table_exists(self, temp_db):
        """Test table_exists helper method."""
        db = MetricsDatabase(temp_db)

        assert db.table_exists("benchmark_runs") is True
        assert db.table_exists("performance_metrics") is True
        assert db.table_exists("nonexistent_table") is False

    def test_get_table_names(self, temp_db):
        """Test get_table_names helper method."""
        db = MetricsDatabase(temp_db)

        tables = db.get_table_names()
        expected_tables = [
            "autonomy_metrics",
            "benchmark_runs",
            "performance_metrics",
            "quality_metrics",
            "workflow_metrics",
        ]

        assert sorted(tables) == sorted(expected_tables)

    def test_vacuum(self, temp_db):
        """Test vacuum operation."""
        db = MetricsDatabase(temp_db)

        # Insert and delete some data to create fragmentation
        with db.connection() as conn:
            cursor = conn.cursor()

            for i in range(100):
                cursor.execute("""
                    INSERT INTO benchmark_runs
                    (run_id, timestamp, project_name, benchmark_name)
                    VALUES (?, ?, ?, ?)
                """, (f"run-{i}", "2025-10-27T10:00:00Z", "test", "test"))

            conn.commit()

            cursor.execute("DELETE FROM benchmark_runs")
            conn.commit()

        # Get size before vacuum
        size_before = db.get_database_size()

        # Vacuum
        db.vacuum()

        # Size after should be smaller or same
        size_after = db.get_database_size()
        assert size_after <= size_before

    def test_get_database_size(self, temp_db):
        """Test get_database_size method."""
        db = MetricsDatabase(temp_db)

        size = db.get_database_size()
        assert size > 0  # Database file exists and has content

        # Insert some data
        with db.connection() as conn:
            cursor = conn.cursor()
            for i in range(100):  # Insert more rows to guarantee size increase
                cursor.execute("""
                    INSERT INTO benchmark_runs
                    (run_id, timestamp, project_name, benchmark_name)
                    VALUES (?, ?, ?, ?)
                """, (f"run-{i}", "2025-10-27T10:00:00Z", "test", "test"))
            conn.commit()

        # Size should have increased or stayed same (due to page allocation)
        new_size = db.get_database_size()
        assert new_size >= size

    def test_row_factory(self, temp_db):
        """Test that row factory enables dict-like access."""
        db = MetricsDatabase(temp_db)

        with db.connection() as conn:
            cursor = conn.cursor()

            # Insert a run
            cursor.execute("""
                INSERT INTO benchmark_runs
                (run_id, timestamp, project_name, benchmark_name)
                VALUES ('dict-test', '2025-10-27T10:00:00Z', 'test', 'test')
            """)
            conn.commit()

            # Query and verify dict-like access works
            cursor.execute("SELECT * FROM benchmark_runs WHERE run_id = ?", ("dict-test",))
            row = cursor.fetchone()

            assert row is not None
            assert row["run_id"] == "dict-test"
            assert row["project_name"] == "test"
            assert row["benchmark_name"] == "test"

    def test_multiple_connections(self, temp_db):
        """Test multiple concurrent connections."""
        db = MetricsDatabase(temp_db)

        # Open two connections simultaneously
        with db.connection() as conn1:
            with db.connection() as conn2:
                cursor1 = conn1.cursor()
                cursor2 = conn2.cursor()

                cursor1.execute("SELECT COUNT(*) FROM benchmark_runs")
                cursor2.execute("SELECT COUNT(*) FROM benchmark_runs")

                assert cursor1.fetchone()[0] == 0
                assert cursor2.fetchone()[0] == 0

    def test_database_persistence(self, temp_db):
        """Test that data persists across database instances."""
        # Create first instance and insert data
        db1 = MetricsDatabase(temp_db)
        with db1.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO benchmark_runs
                (run_id, timestamp, project_name, benchmark_name)
                VALUES ('persist-test', '2025-10-27T10:00:00Z', 'test', 'test')
            """)
            conn.commit()

        # Create second instance and verify data exists
        db2 = MetricsDatabase(temp_db)
        with db2.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmark_runs WHERE run_id = ?", ("persist-test",))
            row = cursor.fetchone()

            assert row is not None
            assert row["run_id"] == "persist-test"
