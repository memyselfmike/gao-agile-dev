"""Metrics storage and retrieval.

This module provides the MetricsStorage class for persisting and querying
benchmark metrics. It integrates MetricsDatabase and BenchmarkMetrics to
provide high-level storage operations with transaction safety.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from .database import MetricsDatabase
from .models import (
    BenchmarkMetrics,
    PerformanceMetrics,
    AutonomyMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


class MetricsStorage:
    """
    Handles storage and retrieval of benchmark metrics.

    Provides high-level API for:
    - Saving complete metrics (transactional)
    - Retrieving metrics by run_id
    - Querying runs with filters
    - Deleting metrics

    Uses JSON serialization for complex fields (dicts, lists) when storing
    in SQLite. Validates metrics before saving and handles database errors
    gracefully with rollback.

    Attributes:
        db: MetricsDatabase instance for database operations
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metrics storage.

        Args:
            db_path: Path to SQLite database file (default: ~/.gao-dev/metrics.db)
        """
        self.db = MetricsDatabase(db_path)

    def save_metrics(self, metrics: BenchmarkMetrics) -> bool:
        """
        Save benchmark metrics to database.

        All inserts are transactional - either all succeed or all are rolled back.
        Validates metrics before saving.

        Args:
            metrics: BenchmarkMetrics object to save

        Returns:
            True if successful

        Raises:
            ValueError: If metrics validation fails
            RuntimeError: If database operation fails
        """
        if not metrics.validate():
            raise ValueError("Invalid metrics data")

        with self.db.connection() as conn:
            cursor = conn.cursor()

            try:
                # Save benchmark run
                cursor.execute(
                    """
                    INSERT INTO benchmark_runs
                    (run_id, timestamp, project_name, benchmark_name, version, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.run_id,
                        metrics.timestamp,
                        metrics.project_name,
                        metrics.benchmark_name,
                        metrics.version,
                        json.dumps(metrics.metadata),
                    ),
                )

                # Save performance metrics
                perf = metrics.performance
                cursor.execute(
                    """
                    INSERT INTO performance_metrics
                    (run_id, total_time_seconds, phase_times, token_usage_total,
                     token_usage_by_agent, api_calls_count, api_calls_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.run_id,
                        perf.total_time_seconds,
                        json.dumps(perf.phase_times),
                        perf.token_usage_total,
                        json.dumps(perf.token_usage_by_agent),
                        perf.api_calls_count,
                        perf.api_calls_cost,
                    ),
                )

                # Save autonomy metrics
                auto = metrics.autonomy
                cursor.execute(
                    """
                    INSERT INTO autonomy_metrics
                    (run_id, manual_interventions_count, manual_interventions_types,
                     prompts_needed_initial, prompts_needed_followup,
                     one_shot_success_rate, error_recovery_rate,
                     agent_handoffs_successful, agent_handoffs_failed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.run_id,
                        auto.manual_interventions_count,
                        json.dumps(auto.manual_interventions_types),
                        auto.prompts_needed_initial,
                        auto.prompts_needed_followup,
                        auto.one_shot_success_rate,
                        auto.error_recovery_rate,
                        auto.agent_handoffs_successful,
                        auto.agent_handoffs_failed,
                    ),
                )

                # Save quality metrics
                qual = metrics.quality
                cursor.execute(
                    """
                    INSERT INTO quality_metrics
                    (run_id, tests_written, tests_passing, code_coverage_percentage,
                     linting_errors_count, linting_errors_by_severity,
                     type_errors_count, security_vulnerabilities_count,
                     security_vulnerabilities_by_severity, functional_completeness_percentage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.run_id,
                        qual.tests_written,
                        qual.tests_passing,
                        qual.code_coverage_percentage,
                        qual.linting_errors_count,
                        json.dumps(qual.linting_errors_by_severity),
                        qual.type_errors_count,
                        qual.security_vulnerabilities_count,
                        json.dumps(qual.security_vulnerabilities_by_severity),
                        qual.functional_completeness_percentage,
                    ),
                )

                # Save workflow metrics
                work = metrics.workflow
                cursor.execute(
                    """
                    INSERT INTO workflow_metrics
                    (run_id, stories_created, stories_completed, avg_cycle_time_seconds,
                     phase_distribution, rework_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.run_id,
                        work.stories_created,
                        work.stories_completed,
                        work.avg_cycle_time_seconds,
                        json.dumps(work.phase_distribution),
                        work.rework_count,
                    ),
                )

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"Failed to save metrics: {e}") from e

    def get_metrics(self, run_id: str) -> Optional[BenchmarkMetrics]:
        """
        Get metrics for a specific run.

        Retrieves all metric categories and reconstructs a complete
        BenchmarkMetrics object.

        Args:
            run_id: Unique identifier for the benchmark run

        Returns:
            BenchmarkMetrics object if found, None otherwise
        """
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
            return BenchmarkMetrics(
                run_id=run_row["run_id"],
                timestamp=run_row["timestamp"],
                project_name=run_row["project_name"],
                benchmark_name=run_row["benchmark_name"],
                version=run_row["version"],
                performance=PerformanceMetrics(
                    total_time_seconds=perf_row["total_time_seconds"],
                    phase_times=json.loads(perf_row["phase_times"]),
                    token_usage_total=perf_row["token_usage_total"],
                    token_usage_by_agent=json.loads(perf_row["token_usage_by_agent"]),
                    api_calls_count=perf_row["api_calls_count"],
                    api_calls_cost=perf_row["api_calls_cost"],
                )
                if perf_row
                else PerformanceMetrics(),
                autonomy=AutonomyMetrics(
                    manual_interventions_count=auto_row["manual_interventions_count"],
                    manual_interventions_types=json.loads(auto_row["manual_interventions_types"]),
                    prompts_needed_initial=auto_row["prompts_needed_initial"],
                    prompts_needed_followup=auto_row["prompts_needed_followup"],
                    one_shot_success_rate=auto_row["one_shot_success_rate"],
                    error_recovery_rate=auto_row["error_recovery_rate"],
                    agent_handoffs_successful=auto_row["agent_handoffs_successful"],
                    agent_handoffs_failed=auto_row["agent_handoffs_failed"],
                )
                if auto_row
                else AutonomyMetrics(),
                quality=QualityMetrics(
                    tests_written=qual_row["tests_written"],
                    tests_passing=qual_row["tests_passing"],
                    code_coverage_percentage=qual_row["code_coverage_percentage"],
                    linting_errors_count=qual_row["linting_errors_count"],
                    linting_errors_by_severity=json.loads(
                        qual_row["linting_errors_by_severity"]
                    ),
                    type_errors_count=qual_row["type_errors_count"],
                    security_vulnerabilities_count=qual_row["security_vulnerabilities_count"],
                    security_vulnerabilities_by_severity=json.loads(
                        qual_row["security_vulnerabilities_by_severity"]
                    ),
                    functional_completeness_percentage=qual_row[
                        "functional_completeness_percentage"
                    ],
                )
                if qual_row
                else QualityMetrics(),
                workflow=WorkflowMetrics(
                    stories_created=work_row["stories_created"],
                    stories_completed=work_row["stories_completed"],
                    avg_cycle_time_seconds=work_row["avg_cycle_time_seconds"],
                    phase_distribution=json.loads(work_row["phase_distribution"]),
                    rework_count=work_row["rework_count"],
                )
                if work_row
                else WorkflowMetrics(),
                metadata=json.loads(run_row["metadata"]),
            )

    def list_runs(
        self,
        project_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List recent benchmark runs with optional filters.

        Results are sorted by timestamp in descending order (newest first).

        Args:
            project_name: Filter by project name
            benchmark_name: Filter by benchmark name
            start_date: Filter runs after this date (ISO format)
            end_date: Filter runs before this date (ISO format)
            limit: Maximum number of results (default: 50)

        Returns:
            List of dictionaries containing run information
        """
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

            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

    def delete_metrics(self, run_id: str) -> bool:
        """
        Delete metrics for a specific run.

        Deletes from all tables in a transaction. Thanks to CASCADE constraints,
        deleting from benchmark_runs automatically deletes related metrics.

        Args:
            run_id: Unique identifier for the benchmark run

        Returns:
            True if successful, False otherwise
        """
        with self.db.connection() as conn:
            cursor = conn.cursor()
            try:
                # Check if run exists
                cursor.execute("SELECT run_id FROM benchmark_runs WHERE run_id = ?", (run_id,))
                if not cursor.fetchone():
                    return False

                # Delete from benchmark_runs (cascade will handle related tables)
                cursor.execute("DELETE FROM benchmark_runs WHERE run_id = ?", (run_id,))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                return False

    def get_latest_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the N most recent runs.

        Args:
            limit: Number of runs to retrieve (default: 10)

        Returns:
            List of dictionaries containing run information
        """
        return self.list_runs(limit=limit)

    def get_runs_between_dates(
        self, start_date: str, end_date: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get runs between two dates.

        Args:
            start_date: Start date in ISO format (inclusive)
            end_date: End date in ISO format (inclusive)
            limit: Maximum number of results (default: 100)

        Returns:
            List of dictionaries containing run information
        """
        return self.list_runs(start_date=start_date, end_date=end_date, limit=limit)

    def get_average_metrics(
        self,
        project_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, float]:
        """
        Get average metrics across recent runs.

        Calculates averages for key numeric metrics across the most recent runs
        matching the filter criteria.

        Args:
            project_name: Filter by project name
            benchmark_name: Filter by benchmark name
            limit: Number of recent runs to include in average (default: 10)

        Returns:
            Dictionary containing average values for key metrics
        """
        runs = self.list_runs(
            project_name=project_name, benchmark_name=benchmark_name, limit=limit
        )

        if not runs:
            return {}

        # Collect metrics for averaging
        metrics_list = []
        for run in runs:
            metrics = self.get_metrics(run["run_id"])
            if metrics:
                metrics_list.append(metrics)

        if not metrics_list:
            return {}

        # Calculate averages
        total = len(metrics_list)
        return {
            "total_time_seconds": sum(m.performance.total_time_seconds for m in metrics_list)
            / total,
            "token_usage_total": sum(m.performance.token_usage_total for m in metrics_list)
            / total,
            "api_calls_count": sum(m.performance.api_calls_count for m in metrics_list) / total,
            "api_calls_cost": sum(m.performance.api_calls_cost for m in metrics_list) / total,
            "manual_interventions_count": sum(
                m.autonomy.manual_interventions_count for m in metrics_list
            )
            / total,
            "one_shot_success_rate": sum(
                m.autonomy.one_shot_success_rate for m in metrics_list
            )
            / total,
            "error_recovery_rate": sum(m.autonomy.error_recovery_rate for m in metrics_list)
            / total,
            "tests_written": sum(m.quality.tests_written for m in metrics_list) / total,
            "tests_passing": sum(m.quality.tests_passing for m in metrics_list) / total,
            "code_coverage_percentage": sum(
                m.quality.code_coverage_percentage for m in metrics_list
            )
            / total,
            "stories_created": sum(m.workflow.stories_created for m in metrics_list) / total,
            "stories_completed": sum(m.workflow.stories_completed for m in metrics_list) / total,
            "avg_cycle_time_seconds": sum(
                m.workflow.avg_cycle_time_seconds for m in metrics_list
            )
            / total,
        }

    def get_metric_trends(
        self,
        metric_name: str,
        project_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get trend data for a specific metric over time.

        Returns time series data showing how a metric has changed across runs.

        Args:
            metric_name: Name of the metric to track (e.g., 'total_time_seconds')
            project_name: Filter by project name
            benchmark_name: Filter by benchmark name
            limit: Number of recent runs to include (default: 20)

        Returns:
            List of dictionaries with timestamp and metric value
        """
        runs = self.list_runs(
            project_name=project_name, benchmark_name=benchmark_name, limit=limit
        )

        trends = []
        for run in runs:
            metrics = self.get_metrics(run["run_id"])
            if not metrics:
                continue

            # Extract metric value by name
            value = None
            if hasattr(metrics.performance, metric_name):
                value = getattr(metrics.performance, metric_name)
            elif hasattr(metrics.autonomy, metric_name):
                value = getattr(metrics.autonomy, metric_name)
            elif hasattr(metrics.quality, metric_name):
                value = getattr(metrics.quality, metric_name)
            elif hasattr(metrics.workflow, metric_name):
                value = getattr(metrics.workflow, metric_name)

            if value is not None:
                trends.append(
                    {"timestamp": metrics.timestamp, "run_id": metrics.run_id, "value": value}
                )

        # Sort by timestamp ascending (oldest first for trend visualization)
        trends.sort(key=lambda x: x["timestamp"])
        return trends
