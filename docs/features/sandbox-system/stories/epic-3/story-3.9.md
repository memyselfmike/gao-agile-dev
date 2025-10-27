# Story 3.9: Metrics Export Functionality

**Epic**: Epic 3 - Metrics Collection System
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 2 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer analyzing metrics
**I want** to export metrics to CSV and JSON formats
**So that** I can use external tools for analysis and reporting

---

## Acceptance Criteria

### AC1: JSON Export
- [ ] Export single run to JSON file
- [ ] Export multiple runs to JSON array
- [ ] Pretty-printed JSON output
- [ ] Include all metric categories

### AC2: CSV Export
- [ ] Export metrics to CSV format
- [ ] Separate CSV files for each metric category
- [ ] Headers with descriptive column names
- [ ] Support for multiple runs in single CSV

### AC3: Export Options
- [ ] Export by run_id
- [ ] Export by date range
- [ ] Export by project name
- [ ] Export all runs

### AC4: CLI Integration
- [ ] `gao-dev metrics export` command
- [ ] Format option (--format json|csv)
- [ ] Output path option (--output)
- [ ] Filter options (--project, --run-id, --since)

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/metrics/export.py`

```python
"""Metrics export functionality."""

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
    """

    def __init__(self, storage: Optional[MetricsStorage] = None):
        """Initialize metrics exporter."""
        self.storage = storage or MetricsStorage()

    def export_to_json(
        self,
        run_ids: List[str],
        output_path: Path,
        pretty: bool = True
    ) -> None:
        """
        Export metrics to JSON file.

        Args:
            run_ids: List of run IDs to export
            output_path: Path to output JSON file
            pretty: Whether to pretty-print JSON
        """
        metrics_list = []
        for run_id in run_ids:
            metrics = self.storage.get_metrics(run_id)
            if metrics:
                metrics_list.append(metrics.to_dict())

        with open(output_path, 'w') as f:
            if pretty:
                json.dump(metrics_list, f, indent=2)
            else:
                json.dump(metrics_list, f)

    def export_to_csv(
        self,
        run_ids: List[str],
        output_dir: Path
    ) -> None:
        """
        Export metrics to CSV files (one per category).

        Args:
            run_ids: List of run IDs to export
            output_dir: Directory for output CSV files
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

        # Export benchmark runs summary
        self._export_runs_csv(metrics_list, output_dir / "runs.csv")

        # Export performance metrics
        self._export_performance_csv(metrics_list, output_dir / "performance.csv")

        # Export autonomy metrics
        self._export_autonomy_csv(metrics_list, output_dir / "autonomy.csv")

        # Export quality metrics
        self._export_quality_csv(metrics_list, output_dir / "quality.csv")

        # Export workflow metrics
        self._export_workflow_csv(metrics_list, output_dir / "workflow.csv")

    def _export_runs_csv(self, metrics_list: List[BenchmarkMetrics], output_path: Path) -> None:
        """Export runs summary to CSV."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'run_id', 'timestamp', 'project_name', 'benchmark_name', 'version'
            ])

            for metrics in metrics_list:
                writer.writerow([
                    metrics.run_id,
                    metrics.timestamp,
                    metrics.project_name,
                    metrics.benchmark_name,
                    metrics.version
                ])

    def _export_performance_csv(self, metrics_list: List[BenchmarkMetrics], output_path: Path) -> None:
        """Export performance metrics to CSV."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'run_id', 'total_time_seconds', 'token_usage_total',
                'api_calls_count', 'api_calls_cost'
            ])

            for metrics in metrics_list:
                perf = metrics.performance
                writer.writerow([
                    metrics.run_id,
                    perf.total_time_seconds,
                    perf.token_usage_total,
                    perf.api_calls_count,
                    perf.api_calls_cost
                ])

    def _export_autonomy_csv(self, metrics_list: List[BenchmarkMetrics], output_path: Path) -> None:
        """Export autonomy metrics to CSV."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'run_id', 'manual_interventions_count', 'prompts_needed_initial',
                'prompts_needed_followup', 'one_shot_success_rate',
                'error_recovery_rate', 'agent_handoffs_successful',
                'agent_handoffs_failed'
            ])

            for metrics in metrics_list:
                auto = metrics.autonomy
                writer.writerow([
                    metrics.run_id,
                    auto.manual_interventions_count,
                    auto.prompts_needed_initial,
                    auto.prompts_needed_followup,
                    auto.one_shot_success_rate,
                    auto.error_recovery_rate,
                    auto.agent_handoffs_successful,
                    auto.agent_handoffs_failed
                ])

    def _export_quality_csv(self, metrics_list: List[BenchmarkMetrics], output_path: Path) -> None:
        """Export quality metrics to CSV."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'run_id', 'tests_written', 'tests_passing', 'code_coverage_percentage',
                'linting_errors_count', 'type_errors_count',
                'security_vulnerabilities_count', 'functional_completeness_percentage'
            ])

            for metrics in metrics_list:
                qual = metrics.quality
                writer.writerow([
                    metrics.run_id,
                    qual.tests_written,
                    qual.tests_passing,
                    qual.code_coverage_percentage,
                    qual.linting_errors_count,
                    qual.type_errors_count,
                    qual.security_vulnerabilities_count,
                    qual.functional_completeness_percentage
                ])

    def _export_workflow_csv(self, metrics_list: List[BenchmarkMetrics], output_path: Path) -> None:
        """Export workflow metrics to CSV."""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'run_id', 'stories_created', 'stories_completed',
                'avg_cycle_time_seconds', 'rework_count'
            ])

            for metrics in metrics_list:
                work = metrics.workflow
                writer.writerow([
                    metrics.run_id,
                    work.stories_created,
                    work.stories_completed,
                    work.avg_cycle_time_seconds,
                    work.rework_count
                ])

    def export_run(
        self,
        run_id: str,
        output_path: Path,
        format: str = "json"
    ) -> None:
        """
        Export single run to file.

        Args:
            run_id: Run ID to export
            output_path: Output file path
            format: Export format (json or csv)
        """
        if format == "json":
            self.export_to_json([run_id], output_path, pretty=True)
        elif format == "csv":
            self.export_to_csv([run_id], output_path.parent)
        else:
            raise ValueError(f"Unknown format: {format}")
```

**CLI Command**: Add to `gao_dev/cli/commands.py`

```python
@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]), default="json")
@click.option("--output", type=click.Path(), required=True)
@click.option("--run-id", help="Specific run ID to export")
@click.option("--project", help="Export all runs for project")
@click.option("--since", help="Export runs since date (YYYY-MM-DD)")
def metrics_export(format, output, run_id, project, since):
    """Export metrics to JSON or CSV format."""
    from gao_dev.sandbox.metrics.export import MetricsExporter
    from gao_dev.sandbox.metrics.storage import MetricsStorage

    storage = MetricsStorage()
    exporter = MetricsExporter(storage)

    # Determine which runs to export
    if run_id:
        run_ids = [run_id]
    else:
        runs = storage.list_runs(project_name=project)
        run_ids = [run["run_id"] for run in runs]

    output_path = Path(output)

    if format == "json":
        exporter.export_to_json(run_ids, output_path)
        click.echo(f"Exported {len(run_ids)} runs to {output_path}")
    elif format == "csv":
        exporter.export_to_csv(run_ids, output_path)
        click.echo(f"Exported {len(run_ids)} runs to {output_path}/")
```

### Usage Example

```bash
# Export single run to JSON
gao-dev metrics export --format json --run-id abc123 --output metrics.json

# Export all runs for project to CSV
gao-dev metrics export --format csv --project todo-app --output ./exports

# Export recent runs
gao-dev metrics export --format json --since 2025-10-01 --output recent.json
```

---

## Testing Requirements

### Unit Tests

```python
def test_export_to_json():
    """Test JSON export."""
    pass

def test_export_to_csv():
    """Test CSV export."""
    pass

def test_export_single_run():
    """Test exporting single run."""
    pass

def test_export_multiple_runs():
    """Test exporting multiple runs."""
    pass

def test_csv_file_structure():
    """Test CSV files have correct structure."""
    pass

def test_cli_command():
    """Test CLI command integration."""
    pass
```

---

## Definition of Done

- [ ] MetricsExporter implemented
- [ ] JSON export working
- [ ] CSV export working (all 5 files)
- [ ] CLI command added
- [ ] Unit tests passing (>85% coverage)
- [ ] Documentation complete
- [ ] Committed with proper message

---

## Dependencies

- **Requires**: Story 3.1 (models), Story 3.8 (storage)
- **Blocks**: None

---

## Notes

- CSV format good for Excel/Google Sheets
- JSON format good for external tools
- Consider adding more formats later (Excel, Parquet)

---

*Created as part of Epic 3: Metrics Collection System*
