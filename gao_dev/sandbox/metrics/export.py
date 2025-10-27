"""Metrics export functionality.

This module provides the MetricsExporter class for exporting benchmark metrics
to various formats (JSON, CSV) with filtering capabilities.
"""

import csv
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .storage import MetricsStorage
from .models import BenchmarkMetrics


class MetricsExporter:
    """
    Exports metrics to various formats (JSON, CSV).

    Provides functionality to export benchmark metrics to JSON files (single
    or multiple runs) and CSV files (one per metric category). Supports
    filtering by run_id, project_name, benchmark_name, and date range.

    Attributes:
        storage: MetricsStorage instance for retrieving metrics
    """

    def __init__(self, storage: Optional[MetricsStorage] = None):
        """
        Initialize metrics exporter.

        Args:
            storage: MetricsStorage instance (default: creates new instance)
        """
        self.storage = storage or MetricsStorage()

    def export_to_json(
        self, run_ids: List[str], output_path: Path, pretty: bool = True
    ) -> None:
        """
        Export metrics to JSON file.

        Exports one or more benchmark runs to a JSON file. If multiple runs
        are provided, exports as a JSON array. Pretty-prints by default.

        Args:
            run_ids: List of run IDs to export
            output_path: Path to output JSON file
            pretty: Whether to pretty-print JSON (default: True)

        Raises:
            IOError: If file cannot be written
        """
        metrics_list = []
        for run_id in run_ids:
            metrics = self.storage.get_metrics(run_id)
            if metrics:
                metrics_list.append(metrics.to_dict())

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            if pretty:
                json.dump(metrics_list, f, indent=2)
            else:
                json.dump(metrics_list, f)

    def export_to_csv(self, run_ids: List[str], output_dir: Path) -> None:
        """
        Export metrics to CSV files (one per category).

        Creates 5 CSV files in the output directory:
        - runs.csv: Basic run information
        - performance.csv: Performance metrics
        - autonomy.csv: Autonomy metrics
        - quality.csv: Quality metrics
        - workflow.csv: Workflow metrics

        Args:
            run_ids: List of run IDs to export
            output_dir: Directory for output CSV files

        Raises:
            IOError: If files cannot be written
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Fetch all metrics
        metrics_list = []
        for run_id in run_ids:
            metrics = self.storage.get_metrics(run_id)
            if metrics:
                metrics_list.append(metrics)

        if not metrics_list:
            return

        # Export each category to separate CSV
        self._export_runs_csv(metrics_list, output_dir / "runs.csv")
        self._export_performance_csv(metrics_list, output_dir / "performance.csv")
        self._export_autonomy_csv(metrics_list, output_dir / "autonomy.csv")
        self._export_quality_csv(metrics_list, output_dir / "quality.csv")
        self._export_workflow_csv(metrics_list, output_dir / "workflow.csv")

    def _export_runs_csv(
        self, metrics_list: List[BenchmarkMetrics], output_path: Path
    ) -> None:
        """
        Export runs summary to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics to export
            output_path: Path to output CSV file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["run_id", "timestamp", "project_name", "benchmark_name", "version"]
            )

            for metrics in metrics_list:
                writer.writerow(
                    [
                        metrics.run_id,
                        metrics.timestamp,
                        metrics.project_name,
                        metrics.benchmark_name,
                        metrics.version,
                    ]
                )

    def _export_performance_csv(
        self, metrics_list: List[BenchmarkMetrics], output_path: Path
    ) -> None:
        """
        Export performance metrics to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics to export
            output_path: Path to output CSV file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "run_id",
                    "total_time_seconds",
                    "token_usage_total",
                    "api_calls_count",
                    "api_calls_cost",
                ]
            )

            for metrics in metrics_list:
                perf = metrics.performance
                writer.writerow(
                    [
                        metrics.run_id,
                        perf.total_time_seconds,
                        perf.token_usage_total,
                        perf.api_calls_count,
                        perf.api_calls_cost,
                    ]
                )

    def _export_autonomy_csv(
        self, metrics_list: List[BenchmarkMetrics], output_path: Path
    ) -> None:
        """
        Export autonomy metrics to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics to export
            output_path: Path to output CSV file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "run_id",
                    "manual_interventions_count",
                    "prompts_needed_initial",
                    "prompts_needed_followup",
                    "one_shot_success_rate",
                    "error_recovery_rate",
                    "agent_handoffs_successful",
                    "agent_handoffs_failed",
                ]
            )

            for metrics in metrics_list:
                auto = metrics.autonomy
                writer.writerow(
                    [
                        metrics.run_id,
                        auto.manual_interventions_count,
                        auto.prompts_needed_initial,
                        auto.prompts_needed_followup,
                        auto.one_shot_success_rate,
                        auto.error_recovery_rate,
                        auto.agent_handoffs_successful,
                        auto.agent_handoffs_failed,
                    ]
                )

    def _export_quality_csv(
        self, metrics_list: List[BenchmarkMetrics], output_path: Path
    ) -> None:
        """
        Export quality metrics to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics to export
            output_path: Path to output CSV file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "run_id",
                    "tests_written",
                    "tests_passing",
                    "code_coverage_percentage",
                    "linting_errors_count",
                    "type_errors_count",
                    "security_vulnerabilities_count",
                    "functional_completeness_percentage",
                ]
            )

            for metrics in metrics_list:
                qual = metrics.quality
                writer.writerow(
                    [
                        metrics.run_id,
                        qual.tests_written,
                        qual.tests_passing,
                        qual.code_coverage_percentage,
                        qual.linting_errors_count,
                        qual.type_errors_count,
                        qual.security_vulnerabilities_count,
                        qual.functional_completeness_percentage,
                    ]
                )

    def _export_workflow_csv(
        self, metrics_list: List[BenchmarkMetrics], output_path: Path
    ) -> None:
        """
        Export workflow metrics to CSV.

        Args:
            metrics_list: List of BenchmarkMetrics to export
            output_path: Path to output CSV file
        """
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "run_id",
                    "stories_created",
                    "stories_completed",
                    "avg_cycle_time_seconds",
                    "rework_count",
                ]
            )

            for metrics in metrics_list:
                work = metrics.workflow
                writer.writerow(
                    [
                        metrics.run_id,
                        work.stories_created,
                        work.stories_completed,
                        work.avg_cycle_time_seconds,
                        work.rework_count,
                    ]
                )

    def export_run(
        self, run_id: str, output_path: Path, format: str = "json"
    ) -> None:
        """
        Export single run to file.

        Convenience method for exporting a single run. For CSV format,
        creates files in the parent directory of output_path.

        Args:
            run_id: Run ID to export
            output_path: Output file path (for JSON) or base path (for CSV)
            format: Export format ('json' or 'csv')

        Raises:
            ValueError: If format is not 'json' or 'csv'
        """
        if format == "json":
            self.export_to_json([run_id], output_path, pretty=True)
        elif format == "csv":
            self.export_to_csv([run_id], output_path.parent)
        else:
            raise ValueError(f"Unknown format: {format}")

    def export_filtered(
        self,
        output_path: Path,
        format: str = "json",
        project_name: Optional[str] = None,
        benchmark_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> int:
        """
        Export metrics with filters applied.

        Queries storage for runs matching the filter criteria and exports them.

        Args:
            output_path: Output file path (JSON) or directory (CSV)
            format: Export format ('json' or 'csv')
            project_name: Filter by project name
            benchmark_name: Filter by benchmark name
            start_date: Filter runs after this date (ISO format)
            end_date: Filter runs before this date (ISO format)
            limit: Maximum number of runs to export (default: 100)

        Returns:
            Number of runs exported

        Raises:
            ValueError: If format is not 'json' or 'csv'
        """
        # Validate format first
        if format not in ("json", "csv"):
            raise ValueError(f"Unknown format: {format}")

        # Get filtered runs
        runs = self.storage.list_runs(
            project_name=project_name,
            benchmark_name=benchmark_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        run_ids = [run["run_id"] for run in runs]

        if not run_ids:
            return 0

        # Export based on format
        if format == "json":
            self.export_to_json(run_ids, output_path, pretty=True)
        else:  # format == "csv"
            self.export_to_csv(run_ids, output_path)

        return len(run_ids)
