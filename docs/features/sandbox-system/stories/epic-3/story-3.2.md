# Story 3.2: SQLite Database Schema

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer building the metrics system
**I want** a well-designed SQLite database schema
**So that** metrics can be efficiently stored and queried

---

## Acceptance Criteria

### AC1: Database Schema Design
- [ ] `benchmark_runs` table created
- [ ] `performance_metrics` table created
- [ ] `autonomy_metrics` table created
- [ ] `quality_metrics` table created
- [ ] `workflow_metrics` table created
- [ ] Proper foreign key relationships
- [ ] Indexes on frequently queried columns

### AC2: Schema Migration System
- [ ] Initial schema creation script
- [ ] Migration versioning support
- [ ] Safe upgrade/downgrade capabilities
- [ ] Schema validation on startup

### AC3: Database Initialization
- [ ] Database auto-created if missing
- [ ] Default path: `.gao-dev/metrics.db`
- [ ] Can specify custom database path
- [ ] Connection pooling configured

### AC4: Query Helpers
- [ ] Helper methods for common queries
- [ ] Transaction support
- [ ] Proper error handling
- [ ] Connection lifecycle management

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/database.py`

```python
"""Database schema and management for metrics storage."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class MetricsDatabase:
    """
    SQLite database for storing benchmark metrics.
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
        """Create database schema if it doesn't exist."""
        with self.connection() as conn:
            cursor = conn.cursor()

            # benchmark_runs table
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

            # performance_metrics table
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
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
                )
            """)

            # autonomy_metrics table
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
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
                )
            """)

            # quality_metrics table
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
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
                )
            """)

            # workflow_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    stories_created INTEGER NOT NULL,
                    stories_completed INTEGER NOT NULL,
                    avg_cycle_time_seconds REAL NOT NULL,
                    phase_distribution TEXT,
                    rework_count INTEGER NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs(run_id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON benchmark_runs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_project ON benchmark_runs(project_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_benchmark ON benchmark_runs(benchmark_name)")

            conn.commit()

    @contextmanager
    def connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_schema_version(self) -> int:
        """Get current schema version."""
        return self.SCHEMA_VERSION
```

### Database Schema

**Tables**:

1. **benchmark_runs**: Main run information
   - `run_id` (TEXT, PK): Unique run identifier
   - `timestamp` (TEXT): ISO timestamp
   - `project_name` (TEXT): Project being benchmarked
   - `benchmark_name` (TEXT): Benchmark configuration name
   - `version` (TEXT): Schema version
   - `metadata` (TEXT): JSON metadata
   - `created_at` (TEXT): Record creation timestamp

2. **performance_metrics**: Performance data
   - `id` (INTEGER, PK): Auto-increment ID
   - `run_id` (TEXT, FK): Foreign key to benchmark_runs
   - All PerformanceMetrics fields (JSON for dicts/lists)

3. **autonomy_metrics**: Autonomy data
   - `id` (INTEGER, PK): Auto-increment ID
   - `run_id` (TEXT, FK): Foreign key to benchmark_runs
   - All AutonomyMetrics fields (JSON for dicts/lists)

4. **quality_metrics**: Quality data
   - `id` (INTEGER, PK): Auto-increment ID
   - `run_id` (TEXT, FK): Foreign key to benchmark_runs
   - All QualityMetrics fields (JSON for dicts/lists)

5. **workflow_metrics**: Workflow data
   - `id` (INTEGER, PK): Auto-increment ID
   - `run_id` (TEXT, FK): Foreign key to benchmark_runs
   - All WorkflowMetrics fields (JSON for dicts/lists)

**Indexes**:
- `idx_runs_timestamp`: Query by timestamp
- `idx_runs_project`: Query by project
- `idx_runs_benchmark`: Query by benchmark

---

## Testing Requirements

### Unit Tests

**File**: `tests/sandbox/metrics/test_database.py`

```python
def test_database_creation():
    """Test database file created automatically."""
    pass


def test_schema_initialization():
    """Test all tables and indexes created."""
    pass


def test_connection_context_manager():
    """Test connection lifecycle."""
    pass


def test_custom_database_path():
    """Test specifying custom database path."""
    pass


def test_schema_version():
    """Test schema version tracking."""
    pass


def test_foreign_key_constraints():
    """Test referential integrity."""
    pass
```

### Integration Tests

- Test with real SQLite database
- Test concurrent access
- Test large datasets

---

## Definition of Done

- [ ] MetricsDatabase class implemented
- [ ] All tables created correctly
- [ ] Indexes created
- [ ] Foreign keys working
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] No type errors (MyPy strict)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.1 (data models exist)
- **Blocks**: Story 3.8 (storage & retrieval)

---

## Notes

- Use JSON for complex fields (dicts, lists)
- SQLite is file-based, no server needed
- Consider PostgreSQL for production
- Add migration system in future if needed

---

*Created as part of Epic 3: Metrics Collection System*
