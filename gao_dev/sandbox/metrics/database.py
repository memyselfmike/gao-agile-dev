"""Database schema and management for metrics storage.

This module provides SQLite database management for storing benchmark metrics.
It handles schema creation, migrations, and connection management.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class MetricsDatabase:
    """
    SQLite database for storing benchmark metrics.

    Manages database schema, connections, and provides helper methods
    for common database operations.

    Attributes:
        db_path: Path to SQLite database file
        SCHEMA_VERSION: Current database schema version
        DEFAULT_DB_PATH: Default location for database file
    """

    SCHEMA_VERSION = 1
    DEFAULT_DB_PATH = Path.home() / ".gao-dev" / "metrics.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metrics database.

        Args:
            db_path: Path to SQLite database file (default: ~/.gao-dev/metrics.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """
        Create database schema if it doesn't exist.

        Creates all tables, indexes, and foreign key relationships
        required for metrics storage.
        """
        with self.connection() as conn:
            cursor = conn.cursor()

            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")

            # benchmark_runs table - main run information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    benchmark_name TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # performance_metrics table - performance data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    total_time_seconds REAL NOT NULL,
                    phase_times TEXT,
                    token_usage_total INTEGER NOT NULL,
                    token_usage_by_agent TEXT,
                    api_calls_count INTEGER NOT NULL,
                    api_calls_cost REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id) ON DELETE CASCADE
                )
            """)

            # autonomy_metrics table - autonomy data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS autonomy_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    manual_interventions_count INTEGER NOT NULL,
                    manual_interventions_types TEXT,
                    prompts_needed_initial INTEGER NOT NULL,
                    prompts_needed_followup INTEGER NOT NULL,
                    one_shot_success_rate REAL NOT NULL,
                    error_recovery_rate REAL NOT NULL,
                    agent_handoffs_successful INTEGER NOT NULL,
                    agent_handoffs_failed INTEGER NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id) ON DELETE CASCADE
                )
            """)

            # quality_metrics table - quality data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    tests_written INTEGER NOT NULL,
                    tests_passing INTEGER NOT NULL,
                    code_coverage_percentage REAL NOT NULL,
                    linting_errors_count INTEGER NOT NULL,
                    linting_errors_by_severity TEXT,
                    type_errors_count INTEGER NOT NULL,
                    security_vulnerabilities_count INTEGER NOT NULL,
                    security_vulnerabilities_by_severity TEXT,
                    functional_completeness_percentage REAL NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id) ON DELETE CASCADE
                )
            """)

            # workflow_metrics table - workflow data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    stories_created INTEGER NOT NULL,
                    stories_completed INTEGER NOT NULL,
                    avg_cycle_time_seconds REAL NOT NULL,
                    phase_distribution TEXT,
                    rework_count INTEGER NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id) ON DELETE CASCADE
                )
            """)

            # Create indexes for frequently queried columns
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON benchmark_runs(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_runs_project ON benchmark_runs(project_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON benchmark_runs(benchmark_name)"
            )

            # Create indexes on foreign keys for better join performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_performance_run_id ON performance_metrics(run_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_autonomy_run_id ON autonomy_metrics(run_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_quality_run_id ON quality_metrics(run_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_run_id ON workflow_metrics(run_id)"
            )

            conn.commit()

    @contextmanager
    def connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM benchmark_runs")
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints for this connection
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def get_schema_version(self) -> int:
        """
        Get current schema version.

        Returns:
            Current schema version number
        """
        return self.SCHEMA_VERSION

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None

    def get_table_names(self) -> list[str]:
        """
        Get list of all table names in the database.

        Returns:
            List of table names
        """
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            return [row[0] for row in cursor.fetchall()]

    def vacuum(self) -> None:
        """
        Vacuum the database to reclaim unused space and optimize performance.
        """
        with self.connection() as conn:
            conn.execute("VACUUM")

    def get_database_size(self) -> int:
        """
        Get database file size in bytes.

        Returns:
            Size of database file in bytes
        """
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0
