# Story 3.8: Metrics Storage & Retrieval

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer managing metrics
**I want** to save metrics to database and query historical data
**So that** I can analyze trends and compare benchmark runs

---

## Acceptance Criteria

### AC1: Metrics Persistence
- [ ] Save complete metrics to SQLite database
- [ ] Save all metric categories (performance, autonomy, quality, workflow)
- [ ] Transactional saves (all or nothing)
- [ ] Validate metrics before saving

### AC2: Metrics Retrieval
- [ ] Query single run by run_id
- [ ] Query runs by project name
- [ ] Query runs by benchmark name
- [ ] Query runs by date range
- [ ] Sort results by timestamp

### AC3: Aggregation Queries
- [ ] Get latest N runs
- [ ] Get runs between dates
- [ ] Get average metrics across runs
- [ ] Get metric trends over time

### AC4: Integration
- [ ] Works with MetricsCollector
- [ ] Works with all tracker classes
- [ ] Automatic saving at end of run
- [ ] Error handling for DB issues

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/storage.py`

```python
"""Metrics storage and retrieval."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .database import MetricsDatabase
from .models import BenchmarkMetrics
from .collector import MetricsCollector


class MetricsStorage:
    """
    Handles storage and retrieval of benchmark metrics.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize metrics storage."""
        self.db = MetricsDatabase(db_path)

    def save_metrics(self, metrics: BenchmarkMetrics) -> bool:
        """
        Save benchmark metrics to database.

        Args:
            metrics: BenchmarkMetrics object to save

        Returns:
            True if successful, False otherwise
        """
        if not metrics.validate():
            raise ValueError("Invalid metrics data")

        with self.db.connection() as conn:
            cursor = conn.cursor()

            try:
                # Save benchmark run
                cursor.execute("""
                    INSERT INTO benchmark_runs
                    (run_id, timestamp, project_name, benchmark_name, version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metrics.run_id,
                    metrics.timestamp,
                    metrics.project_name,
                    metrics.benchmark_name,
                    metrics.version,
                    json.dumps(metrics.metadata)
                ))

                # Save performance metrics
                perf = metrics.performance
                cursor.execute("""
                    INSERT INTO performance_metrics
                    (run_id, total_time_seconds, phase_times, token_usage_total,
                     token_usage_by_agent, api_calls_count, api_calls_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.run_id,
                    perf.total_time_seconds,
                    json.dumps(perf.phase_times),
                    perf.token_usage_total,
                    json.dumps(perf.token_usage_by_agent),
                    perf.api_calls_count,
                    perf.api_calls_cost
                ))

                # Save autonomy metrics
                auto = metrics.autonomy
                cursor.execute("""
                    INSERT INTO autonomy_metrics
                    (run_id, manual_interventions_count, manual_interventions_types,
                     prompts_needed_initial, prompts_needed_followup,
                     one_shot_success_rate, error_recovery_rate,
                     agent_handoffs_successful, agent_handoffs_failed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.run_id,
                    auto.manual_interventions_count,
                    json.dumps(auto.manual_interventions_types),
                    auto.prompts_needed_initial,
                    auto.prompts_needed_followup,
                    auto.one_shot_success_rate,
                    auto.error_recovery_rate,
                    auto.agent_handoffs_successful,
                    auto.agent_handoffs_failed
                ))

                # Save quality metrics
                qual = metrics.quality
                cursor.execute("""
                    INSERT INTO quality_metrics
                    (run_id, tests_written, tests_passing, code_coverage_percentage,
                     linting_errors_count, linting_errors_by_severity,
                     type_errors_count, security_vulnerabilities_count,
                     security_vulnerabilities_by_severity, functional_completeness_percentage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.run_id,
                    qual.tests_written,
                    qual.tests_passing,
                    qual.code_coverage_percentage,
                    qual.linting_errors_count,
                    json.dumps(qual.linting_errors_by_severity),
                    qual.type_errors_count,
                    qual.security_vulnerabilities_count,
                    json.dumps(qual.security_vulnerabilities_by_severity),
                    qual.functional_completeness_percentage
                ))

                # Save workflow metrics
                work = metrics.workflow
                cursor.execute("""
                    INSERT INTO workflow_metrics
                    (run_id, stories_created, stories_completed, avg_cycle_time_seconds,
                     phase_distribution, rework_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metrics.run_id,
                    work.stories_created,
                    work.stories_completed,
                    work.avg_cycle_time_seconds,
                    json.dumps(work.phase_distribution),
                    work.rework_count
                ))

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"Failed to save metrics: {e}")

    def get_metrics(self, run_id: str) -> Optional[BenchmarkMetrics]:
        """Get metrics for a specific run."""
        with self.db.connection() as conn:
            cursor = conn.cursor()

            # Get benchmark run
            cursor.execute("SELECT * FROM benchmark_runs WHERE run_id = ?", (run_id,))
            run_row = cursor.fetchone()
            if not run_row:
                return None

            # Get all metric categories
            cursor.execute("SELECT * FROM performance_metrics WHERE run_id = ?", (run_id,))
            perf_row = cursor.fetchone()

            cursor.execute("SELECT * FROM autonomy_metrics WHERE run_id = ?", (run_id,))
            auto_row = cursor.fetchone()

            cursor.execute("SELECT * FROM quality_metrics WHERE run_id = ?", (run_id,))
            qual_row = cursor.fetchone()

            cursor.execute("SELECT * FROM workflow_metrics WHERE run_id = ?", (run_id,))
            work_row = cursor.fetchone()

            # Reconstruct BenchmarkMetrics
            # Implementation to convert rows to BenchmarkMetrics object
            # ...

    def list_runs(
        self,
        project_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List recent benchmark runs."""
        with self.db.connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM benchmark_runs"
            conditions = []
            params = []

            if project_name:
                conditions.append("project_name = ?")
                params.append(project_name)

            if benchmark_name:
                conditions.append("benchmark_name = ?")
                params.append(benchmark_name)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def delete_metrics(self, run_id: str) -> bool:
        """Delete metrics for a specific run."""
        with self.db.connection() as conn:
            cursor = conn.cursor()
            try:
                # Delete from all tables (cascade)
                cursor.execute("DELETE FROM performance_metrics WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM autonomy_metrics WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM quality_metrics WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM workflow_metrics WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM benchmark_runs WHERE run_id = ?", (run_id,))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False
```

### Usage Example

```python
storage = MetricsStorage()

# Save metrics
collector = MetricsCollector()
metrics = collector.get_current_metrics()
storage.save_metrics(metrics)

# Retrieve metrics
retrieved = storage.get_metrics(metrics.run_id)

# List runs
runs = storage.list_runs(project_name="todo-app", limit=10)

# Delete metrics
storage.delete_metrics(run_id)
```

---

## Testing Requirements

### Unit Tests

```python
def test_save_metrics():
    """Test saving complete metrics."""
    pass

def test_get_metrics():
    """Test retrieving metrics."""
    pass

def test_list_runs():
    """Test listing runs with filters."""
    pass

def test_delete_metrics():
    """Test deleting metrics."""
    pass

def test_invalid_metrics_rejected():
    """Test validation."""
    pass

def test_transaction_rollback():
    """Test rollback on error."""
    pass
```

---

## Definition of Done

- [ ] MetricsStorage implemented
- [ ] All CRUD operations working
- [ ] Transactional saves working
- [ ] Query methods working
- [ ] Unit tests passing (>90% coverage)
- [ ] Documentation complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.1 (models), Story 3.2 (database), Story 3.3 (collector)
- **Blocks**: Story 3.9 (export)

---

*Created as part of Epic 3: Metrics Collection System*
