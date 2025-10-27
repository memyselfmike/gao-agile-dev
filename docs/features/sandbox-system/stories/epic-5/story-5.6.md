# Story 5.6: Report CLI Commands

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer using GAO-Dev
**I want** convenient CLI commands to generate reports
**So that** I can quickly create, view, and share benchmark reports

---

## Acceptance Criteria

### AC1: report run Command
- [ ] `gao-dev sandbox report run <run-id>` command implemented
- [ ] Generates HTML report for specified run
- [ ] Optional `--output` flag for custom output path
- [ ] Optional `--no-charts` flag to skip chart generation
- [ ] Optional `--open` flag to open in browser
- [ ] Displays success message with report path
- [ ] Error handling for invalid run IDs

### AC2: report compare Command
- [ ] `gao-dev sandbox report compare <run-id1> <run-id2>` command implemented
- [ ] Generates comparison report for two runs
- [ ] Optional `--output` flag for custom output path
- [ ] Optional `--threshold` flag for significance threshold
- [ ] Optional `--no-charts` flag to skip chart generation
- [ ] Optional `--open` flag to open in browser
- [ ] Displays summary of improvements/regressions
- [ ] Error handling for invalid run IDs

### AC3: report trend Command
- [ ] `gao-dev sandbox report trend` command implemented
- [ ] Generates trend analysis for all runs
- [ ] Optional `--run-ids` flag to specify specific runs
- [ ] Optional `--start-date` and `--end-date` flags for date range
- [ ] Optional `--last-n` flag to analyze last N runs
- [ ] Optional `--output` flag for custom output path
- [ ] Optional `--no-charts` flag to skip chart generation
- [ ] Optional `--open` flag to open in browser
- [ ] Displays trend summary
- [ ] Error handling for insufficient runs

### AC4: report list Command
- [ ] `gao-dev sandbox report list` command implemented
- [ ] Lists all available benchmark runs
- [ ] Shows run ID, date, status, duration
- [ ] Optional `--format` flag (table, json)
- [ ] Sorted by date (newest first)
- [ ] Color-coded status (success=green, failed=red)

### AC5: report open Command
- [ ] `gao-dev sandbox report open <report-path>` command implemented
- [ ] Opens HTML report in default browser
- [ ] Validates report file exists
- [ ] Cross-platform support (Windows, macOS, Linux)
- [ ] Error handling for missing files

### AC6: Default Output Paths
- [ ] Reports saved to `sandbox/reports/` by default
- [ ] Naming convention: `run_<run-id>_<timestamp>.html`
- [ ] Comparison reports: `comparison_<id1>_<id2>_<timestamp>.html`
- [ ] Trend reports: `trend_<start>_<end>_<timestamp>.html`
- [ ] Creates directory if doesn't exist

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/cli/report_commands.py`

```python
"""CLI commands for report generation."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import webbrowser

import click
import structlog
from rich.console import Console
from rich.table import Table

from gao_dev.sandbox.reporting.report_generator import (
    ReportGenerator,
    RunNotFoundError,
)
from gao_dev.sandbox.metrics.storage import MetricsStorage


logger = structlog.get_logger(__name__)
console = Console()


@click.group(name="report")
def report_group():
    """Generate and manage benchmark reports."""
    pass


@report_group.command(name="run")
@click.argument("run_id", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output path for HTML report",
)
@click.option(
    "--no-charts",
    is_flag=True,
    help="Skip chart generation (faster)",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open report in browser after generation",
)
def report_run(
    run_id: str,
    output: Optional[str],
    no_charts: bool,
    open_browser: bool
) -> None:
    """
    Generate HTML report for a benchmark run.

    Example:
        gao-dev sandbox report run abc123 --open
    """
    try:
        # Set up output path
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"sandbox/reports/run_{run_id[:8]}_{timestamp}.html"

        output_path = Path(output)

        # Initialize report generator
        metrics_db = Path("sandbox/.gao/metrics.db")
        generator = ReportGenerator(metrics_db)

        console.print(f"[cyan]Generating report for run: {run_id}[/cyan]")

        # Generate report
        report_path = generator.generate_run_report(
            run_id=run_id,
            output_path=output_path,
            include_charts=not no_charts,
        )

        console.print(f"[green]Report generated: {report_path}[/green]")

        # Open in browser if requested
        if open_browser:
            console.print("[cyan]Opening report in browser...[/cyan]")
            webbrowser.open(f"file://{report_path.absolute()}")

    except RunNotFoundError:
        console.print(f"[red]Error: Run not found: {run_id}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        logger.error("report_generation_failed", error=str(e))
        raise click.Abort()


@report_group.command(name="compare")
@click.argument("run_id1", type=str)
@click.argument("run_id2", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output path for HTML report",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=5.0,
    help="Significance threshold (percentage)",
)
@click.option(
    "--no-charts",
    is_flag=True,
    help="Skip chart generation (faster)",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open report in browser after generation",
)
def report_compare(
    run_id1: str,
    run_id2: str,
    output: Optional[str],
    threshold: float,
    no_charts: bool,
    open_browser: bool
) -> None:
    """
    Generate comparison report for two benchmark runs.

    RUN_ID1 is the baseline run.
    RUN_ID2 is the comparison run.

    Example:
        gao-dev sandbox report compare abc123 def456 --open
    """
    try:
        # Set up output path
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"sandbox/reports/comparison_{run_id1[:8]}_{run_id2[:8]}_{timestamp}.html"

        output_path = Path(output)

        # Initialize report generator
        metrics_db = Path("sandbox/.gao/metrics.db")
        generator = ReportGenerator(metrics_db)

        console.print(
            f"[cyan]Comparing runs:[/cyan]\n"
            f"  Baseline:   {run_id1}\n"
            f"  Comparison: {run_id2}"
        )

        # Generate report
        report_path = generator.generate_comparison_report(
            run_id1=run_id1,
            run_id2=run_id2,
            output_path=output_path,
            significance_threshold=threshold,
            include_charts=not no_charts,
        )

        console.print(f"[green]Comparison report generated: {report_path}[/green]")

        # Open in browser if requested
        if open_browser:
            console.print("[cyan]Opening report in browser...[/cyan]")
            webbrowser.open(f"file://{report_path.absolute()}")

    except RunNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error generating comparison report: {e}[/red]")
        logger.error("comparison_report_failed", error=str(e))
        raise click.Abort()


@report_group.command(name="trend")
@click.option(
    "--run-ids",
    type=str,
    default=None,
    help="Comma-separated list of run IDs",
)
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--last-n",
    type=int,
    default=None,
    help="Analyze last N runs",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output path for HTML report",
)
@click.option(
    "--no-charts",
    is_flag=True,
    help="Skip chart generation (faster)",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open report in browser after generation",
)
def report_trend(
    run_ids: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    last_n: Optional[int],
    output: Optional[str],
    no_charts: bool,
    open_browser: bool
) -> None:
    """
    Generate trend analysis report across multiple runs.

    Examples:
        gao-dev sandbox report trend --last-n 10 --open
        gao-dev sandbox report trend --start-date 2025-01-01 --end-date 2025-01-31
        gao-dev sandbox report trend --run-ids abc123,def456,ghi789
    """
    try:
        # Parse run IDs if provided
        run_id_list = None
        if run_ids:
            run_id_list = [rid.strip() for rid in run_ids.split(",")]
        elif last_n:
            # Get last N runs
            metrics_db = Path("sandbox/.gao/metrics.db")
            storage = MetricsStorage(metrics_db)
            all_runs = storage.get_all_runs()
            all_runs.sort(key=lambda r: r.start_time, reverse=True)
            run_id_list = [r.run_id for r in all_runs[:last_n]]

        # Set up output path
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if start_date and end_date:
                start_str = start_date.strftime("%Y%m%d")
                end_str = end_date.strftime("%Y%m%d")
                output = f"sandbox/reports/trend_{start_str}_{end_str}_{timestamp}.html"
            else:
                output = f"sandbox/reports/trend_{timestamp}.html"

        output_path = Path(output)

        # Initialize report generator
        metrics_db = Path("sandbox/.gao/metrics.db")
        generator = ReportGenerator(metrics_db)

        console.print("[cyan]Generating trend analysis report...[/cyan]")

        # Generate report
        report_path = generator.generate_trend_report(
            run_ids=run_id_list,
            start_date=start_date,
            end_date=end_date,
            output_path=output_path,
            include_charts=not no_charts,
        )

        console.print(f"[green]Trend report generated: {report_path}[/green]")

        # Open in browser if requested
        if open_browser:
            console.print("[cyan]Opening report in browser...[/cyan]")
            webbrowser.open(f"file://{report_path.absolute()}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error generating trend report: {e}[/red]")
        logger.error("trend_report_failed", error=str(e))
        raise click.Abort()


@report_group.command(name="list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format",
)
def report_list(output_format: str) -> None:
    """
    List all available benchmark runs.

    Example:
        gao-dev sandbox report list
        gao-dev sandbox report list --format json
    """
    try:
        metrics_db = Path("sandbox/.gao/metrics.db")
        storage = MetricsStorage(metrics_db)

        # Get all runs
        runs = storage.get_all_runs()
        runs.sort(key=lambda r: r.start_time, reverse=True)

        if output_format == "json":
            import json
            runs_data = [
                {
                    "run_id": r.run_id,
                    "name": r.benchmark_name,
                    "status": r.status,
                    "start_time": r.start_time.isoformat(),
                    "duration_seconds": (r.end_time - r.start_time).total_seconds()
                    if r.end_time else None,
                }
                for r in runs
            ]
            console.print(json.dumps(runs_data, indent=2))
        else:
            # Table format
            table = Table(title="Benchmark Runs")
            table.add_column("Run ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Status", style="white")
            table.add_column("Date", style="white")
            table.add_column("Duration", style="white")

            for run in runs:
                # Status color
                if run.status == "completed":
                    status_style = "[green]"
                elif run.status == "failed":
                    status_style = "[red]"
                else:
                    status_style = "[yellow]"

                # Duration
                if run.end_time:
                    duration = (run.end_time - run.start_time).total_seconds()
                    duration_str = f"{duration:.1f}s"
                else:
                    duration_str = "N/A"

                table.add_row(
                    run.run_id[:12],
                    run.benchmark_name,
                    f"{status_style}{run.status}[/]",
                    run.start_time.strftime("%Y-%m-%d %H:%M"),
                    duration_str,
                )

            console.print(table)
            console.print(f"\n[cyan]Total runs: {len(runs)}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error listing runs: {e}[/red]")
        logger.error("list_runs_failed", error=str(e))
        raise click.Abort()


@report_group.command(name="open")
@click.argument("report_path", type=click.Path(exists=True))
def report_open(report_path: str) -> None:
    """
    Open an HTML report in the default browser.

    Example:
        gao-dev sandbox report open sandbox/reports/run_abc123.html
    """
    try:
        path = Path(report_path).absolute()
        console.print(f"[cyan]Opening report: {path}[/cyan]")
        webbrowser.open(f"file://{path}")
        console.print("[green]Report opened in browser[/green]")

    except Exception as e:
        console.print(f"[red]Error opening report: {e}[/red]")
        logger.error("open_report_failed", error=str(e))
        raise click.Abort()
```

**Update `gao_dev/cli/commands.py`** to register report commands:

```python
from gao_dev.cli.report_commands import report_group

# Add to sandbox group
@click.group(name="sandbox")
def sandbox_group():
    """Sandbox management and benchmarking commands."""
    pass

# Register report commands
sandbox_group.add_command(report_group)
```

---

## Testing Strategy

### Unit Tests
- Command parsing and validation
- Default output path generation
- Run ID validation
- Date parsing
- Error handling for missing runs
- Error handling for invalid paths

### Integration Tests
- Full report generation via CLI
- All report types (run, compare, trend)
- All flags and options work
- Browser opening (mocked)
- Output to custom paths
- List command output

### Manual Tests
- Test on Windows, macOS, Linux
- Verify browser opening works
- Test with various run IDs
- Test date range filtering
- Test output formatting

### Test Coverage Goal
- 90%+ for CLI command logic
- All error paths tested

---

## Dependencies

### Before This Story
- Story 5.1: Report Templates
- Story 5.2: HTML Report Generator
- Story 5.3: Chart Generation
- Story 5.4: Comparison Report
- Story 5.5: Trend Analysis

### Blocks Other Stories
- None (final story in epic)

### External Dependencies
- click (already in dependencies)
- rich (add for better CLI output)

**Update `pyproject.toml`:**
```toml
dependencies = [
    ...
    "rich>=13.0.0",
]
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 5 report commands implemented
- [ ] All flags and options working
- [ ] Default paths working correctly
- [ ] Browser opening working (cross-platform)
- [ ] Error handling comprehensive
- [ ] Rich output for better UX
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing (90%+ coverage)
- [ ] Integration tests passing
- [ ] Manual testing on multiple platforms
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Committed to feature branch

---

## Usage Examples

```bash
# Generate report for a single run
gao-dev sandbox report run abc123 --open

# Compare two runs
gao-dev sandbox report compare abc123 def456 --threshold 10

# Trend analysis for last 10 runs
gao-dev sandbox report trend --last-n 10 --open

# Trend analysis for date range
gao-dev sandbox report trend --start-date 2025-01-01 --end-date 2025-01-31

# List all runs
gao-dev sandbox report list

# Open existing report
gao-dev sandbox report open sandbox/reports/run_abc123.html

# Generate report without charts (faster)
gao-dev sandbox report run abc123 --no-charts

# Custom output path
gao-dev sandbox report run abc123 --output reports/my_report.html
```

---

## Notes

**Design Decisions:**
- Use `rich` library for better CLI output (tables, colors)
- Default report directory: `sandbox/reports/`
- Timestamp in filenames to avoid collisions
- `--open` flag for convenience
- `--no-charts` flag for faster generation when needed
- Cross-platform browser opening with `webbrowser` module

**User Experience:**
- Clear, colorful output
- Progress messages during generation
- Success/error messages
- Helpful examples in help text
- Consistent flag naming across commands

**Future Enhancements:**
- `report watch` - Auto-generate reports on new runs
- `report serve` - Start web server to view reports
- `report export` - Export to PDF
- `report email` - Email reports to stakeholders
- `report slack` - Post reports to Slack

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: CLI component
- Click Documentation: https://click.palletsprojects.com/
- Rich Documentation: https://rich.readthedocs.io/
