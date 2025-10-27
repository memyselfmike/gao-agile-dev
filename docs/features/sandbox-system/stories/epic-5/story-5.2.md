# Story 5.2: HTML Report Generator

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer reviewing benchmark results
**I want** an automated HTML report generator
**So that** I can quickly create comprehensive, professional reports from benchmark data

---

## Acceptance Criteria

### AC1: ReportGenerator Class
- [ ] `ReportGenerator` class implemented
- [ ] Initializes with metrics database path
- [ ] Loads Jinja2 templates correctly
- [ ] Type hints for all methods
- [ ] Comprehensive error handling
- [ ] Logging for debugging

### AC2: Generate Run Report
- [ ] `generate_run_report(run_id, output_path)` method implemented
- [ ] Loads run data from metrics database
- [ ] Loads all associated metrics (performance, quality, workflow)
- [ ] Renders run_report.html.j2 template
- [ ] Writes HTML file to output path
- [ ] Returns Path to generated report
- [ ] Handles missing data gracefully

### AC3: Data Preparation
- [ ] Formats metrics for template consumption
- [ ] Calculates summary statistics
- [ ] Formats timestamps for display
- [ ] Formats durations (seconds to human-readable)
- [ ] Rounds numeric values appropriately
- [ ] Handles None/null values
- [ ] Provides default values for missing fields

### AC4: Template Rendering
- [ ] Template environment configured correctly
- [ ] Template loader finds all templates
- [ ] Template filters registered (format_duration, format_timestamp, etc.)
- [ ] Template inheritance works correctly
- [ ] All template variables resolved
- [ ] No rendering errors with valid data

### AC5: Output Management
- [ ] Creates output directory if doesn't exist
- [ ] Overwrites existing reports with confirmation
- [ ] Sets appropriate file permissions
- [ ] Returns path to generated report
- [ ] Validates output path before writing

### AC6: Error Handling
- [ ] RunNotFoundError if run doesn't exist
- [ ] TemplateNotFoundError if template missing
- [ ] IOError if can't write output file
- [ ] Clear error messages for all failures
- [ ] Logs errors with context

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/reporting/report_generator.py`

```python
"""HTML report generation from benchmark metrics."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
import structlog

from gao_dev.sandbox.metrics.storage import MetricsStorage
from gao_dev.sandbox.metrics.models import (
    BenchmarkRun,
    PerformanceMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


logger = structlog.get_logger(__name__)


class ReportGeneratorError(Exception):
    """Base exception for report generation errors."""
    pass


class RunNotFoundError(ReportGeneratorError):
    """Raised when benchmark run not found."""
    pass


class TemplateNotFoundError(ReportGeneratorError):
    """Raised when template file not found."""
    pass


@dataclass
class RunReportData:
    """Data structure for run report template."""

    run: BenchmarkRun
    performance: PerformanceMetrics
    quality: QualityMetrics
    workflow: WorkflowMetrics
    summary: Dict[str, Any]
    generation_time: datetime
    version: str


class ReportGenerator:
    """Generates HTML reports from benchmark data."""

    def __init__(
        self,
        metrics_db_path: Path,
        template_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize report generator.

        Args:
            metrics_db_path: Path to metrics database
            template_dir: Path to templates directory (default: built-in)
        """
        self.storage = MetricsStorage(metrics_db_path)

        # Set up Jinja2 environment
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

        logger.info(
            "report_generator_initialized",
            metrics_db=str(metrics_db_path),
            template_dir=str(template_dir),
        )

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["format_duration"] = self._format_duration
        self.env.filters["format_timestamp"] = self._format_timestamp
        self.env.filters["format_percent"] = self._format_percent
        self.env.filters["format_number"] = self._format_number
        self.env.filters["status_class"] = self._status_class

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_percent(value: float) -> str:
        """Format percentage value."""
        return f"{value:.1f}%"

    @staticmethod
    def _format_number(value: float) -> str:
        """Format number with appropriate precision."""
        if abs(value) < 10:
            return f"{value:.2f}"
        else:
            return f"{value:.0f}"

    @staticmethod
    def _status_class(status: str) -> str:
        """Get CSS class for status."""
        status_map = {
            "completed": "status-success",
            "failed": "status-error",
            "timeout": "status-warning",
            "running": "status-info",
        }
        return status_map.get(status.lower(), "status-default")

    def generate_run_report(
        self,
        run_id: str,
        output_path: Path,
        overwrite: bool = True
    ) -> Path:
        """
        Generate HTML report for benchmark run.

        Args:
            run_id: Benchmark run identifier
            output_path: Where to save HTML report
            overwrite: Whether to overwrite existing file

        Returns:
            Path to generated report

        Raises:
            RunNotFoundError: If run doesn't exist
            TemplateNotFoundError: If template missing
            IOError: If can't write file
        """
        logger.info(
            "generating_run_report",
            run_id=run_id,
            output_path=str(output_path),
        )

        # Load run data
        run_data = self._load_run_data(run_id)

        # Render template
        try:
            template = self.env.get_template("run_report.html.j2")
            html = template.render(
                run=run_data.run,
                performance=run_data.performance,
                quality=run_data.quality,
                workflow=run_data.workflow,
                summary=run_data.summary,
                generation_time=run_data.generation_time,
                version=run_data.version,
            )
        except Exception as e:
            logger.error("template_render_failed", error=str(e))
            raise TemplateNotFoundError(f"Failed to render template: {e}")

        # Write to file
        self._write_report(html, output_path, overwrite)

        logger.info(
            "run_report_generated",
            run_id=run_id,
            output_path=str(output_path),
        )

        return output_path

    def _load_run_data(self, run_id: str) -> RunReportData:
        """
        Load all data needed for run report.

        Args:
            run_id: Benchmark run identifier

        Returns:
            RunReportData with all metrics

        Raises:
            RunNotFoundError: If run doesn't exist
        """
        # Load run
        run = self.storage.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")

        # Load metrics
        performance = self.storage.get_performance_metrics(run_id)
        quality = self.storage.get_quality_metrics(run_id)
        workflow = self.storage.get_workflow_metrics(run_id)

        # Calculate summary statistics
        summary = self._calculate_summary(
            run, performance, quality, workflow
        )

        return RunReportData(
            run=run,
            performance=performance or PerformanceMetrics(),
            quality=quality or QualityMetrics(),
            workflow=workflow or WorkflowMetrics(),
            summary=summary,
            generation_time=datetime.now(),
            version="1.0.0",
        )

    def _calculate_summary(
        self,
        run: BenchmarkRun,
        performance: Optional[PerformanceMetrics],
        quality: Optional[QualityMetrics],
        workflow: Optional[WorkflowMetrics],
    ) -> Dict[str, Any]:
        """Calculate summary statistics for report."""
        summary = {
            "total_duration": run.end_time - run.start_time if run.end_time else None,
            "status": run.status,
            "success": run.status == "completed",
        }

        if performance:
            summary["avg_response_time"] = performance.avg_response_time_ms
            summary["total_api_calls"] = performance.total_api_calls

        if quality:
            summary["test_coverage"] = quality.test_coverage_percent
            summary["total_errors"] = quality.error_count

        if workflow:
            summary["total_phases"] = len(workflow.phase_durations)

        return summary

    def _write_report(
        self,
        html: str,
        output_path: Path,
        overwrite: bool
    ) -> None:
        """
        Write HTML report to file.

        Args:
            html: Rendered HTML content
            output_path: Where to save file
            overwrite: Whether to overwrite existing file

        Raises:
            IOError: If can't write file
        """
        # Check if file exists
        if output_path.exists() and not overwrite:
            raise IOError(f"File already exists: {output_path}")

        # Create parent directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            output_path.write_text(html, encoding="utf-8")
        except Exception as e:
            logger.error("report_write_failed", error=str(e))
            raise IOError(f"Failed to write report: {e}")
```

---

## Testing Strategy

### Unit Tests
- Template rendering with sample data
- Custom filters work correctly
- Error handling for missing runs
- Error handling for template errors
- Data preparation and formatting
- Summary calculations

### Integration Tests
- Full report generation from database
- All metrics loaded correctly
- Template inheritance works
- Output file written correctly
- Directory creation works

### Test Coverage Goal
- 95%+ for ReportGenerator class
- All error paths tested
- All filters tested

---

## Dependencies

### Before This Story
- Story 5.1: Report Templates (needs templates to render)
- Epic 3: Metrics Collection (needs metrics database)

### Blocks Other Stories
- Story 5.4: Comparison Report (uses same generator)
- Story 5.5: Trend Analysis (uses same generator)

### External Dependencies
- Jinja2 (already in dependencies)
- Metrics database from Epic 3

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] ReportGenerator class implemented
- [ ] generate_run_report method working
- [ ] All filters and formatting functions working
- [ ] Error handling comprehensive
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing (95%+ coverage)
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Committed to feature branch

---

## Notes

**Design Decisions:**
- Use dataclasses for template data structures
- Provide sensible defaults for missing data
- Log all operations for debugging
- Keep template rendering separate from data loading

**Performance Considerations:**
- Cache templates in Jinja2 environment
- Only load needed metrics (don't load all runs)
- Stream large reports if needed (future)

**Future Enhancements:**
- PDF generation (using weasyprint or similar)
- Custom report templates (user-provided)
- Report caching for faster regeneration
- Async report generation for large datasets

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: ReportGenerator component
- Jinja2 Documentation: https://jinja.palletsprojects.com/
