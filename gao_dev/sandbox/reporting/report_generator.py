"""HTML report generation from benchmark metrics."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
import numpy as np
from scipy import stats
import structlog

from gao_dev.sandbox.metrics.storage import MetricsStorage
from gao_dev.sandbox.metrics.models import (
    PerformanceMetrics,
    QualityMetrics,
    WorkflowMetrics,
)
from gao_dev.sandbox.models import BenchmarkRun
from gao_dev.sandbox.reporting.chart_generator import ChartGenerator


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


class ChangeDirection(Enum):
    """Direction of metric change."""
    IMPROVED = "improved"
    REGRESSED = "regressed"
    UNCHANGED = "unchanged"


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
    status: str  # For template compatibility


@dataclass
class MetricComparison:
    """Comparison of a single metric between two runs."""

    name: str
    run1_value: float
    run2_value: float
    absolute_delta: float
    percent_delta: float
    direction: ChangeDirection
    is_significant: bool


@dataclass
class ComparisonReportData:
    """Data structure for comparison report."""

    run1: BenchmarkRun
    run2: BenchmarkRun
    performance: List[MetricComparison]
    quality: List[MetricComparison]
    workflow: List[MetricComparison]
    summary: Dict[str, Any]
    charts: Dict[str, str]
    generation_time: datetime


@dataclass
class TrendStatistics:
    """Statistical summary for a metric trend."""

    metric_name: str
    values: List[float]
    timestamps: List[datetime]
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    trend_direction: str
    slope: float
    r_squared: float
    percent_change: float
    ma_7: Optional[List[float]]
    ma_30: Optional[List[float]]
    outlier_indices: List[int]


@dataclass
class TrendReportData:
    """Data structure for trend report."""

    runs: List[BenchmarkRun]
    performance_trends: List[TrendStatistics]
    quality_trends: List[TrendStatistics]
    workflow_trends: List[TrendStatistics]
    summary: Dict[str, Any]
    insights: List[str]
    charts: Dict[str, str]
    generation_time: datetime


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
        if seconds is None:
            return "N/A"
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
        if dt is None:
            return "N/A"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_percent(value: float) -> str:
        """Format percentage value."""
        if value is None:
            return "N/A"
        return f"{value:.1f}%"

    @staticmethod
    def _format_number(value: float) -> str:
        """Format number with appropriate precision."""
        if value is None:
            return "N/A"
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
        include_charts: bool = True,
        overwrite: bool = True
    ) -> Path:
        """
        Generate HTML report for benchmark run.

        Args:
            run_id: Benchmark run identifier
            output_path: Where to save HTML report
            include_charts: Whether to include charts
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

        # Generate charts if requested
        charts = {}
        if include_charts:
            try:
                charts = self._generate_run_charts(run_data)
            except Exception as e:
                logger.warning("chart_generation_failed", error=str(e))
                # Continue without charts

        # Render template
        try:
            template = self.env.get_template("run_report.html.j2")
            html = template.render(
                run=run_data.run,
                performance=run_data.performance,
                quality=run_data.quality,
                workflow=run_data.workflow,
                summary=run_data.summary,
                charts=charts,
                generation_time=run_data.generation_time,
                version=run_data.version,
                status=run_data.status,
            )
        except TemplateNotFound as e:
            logger.error("template_not_found", template=str(e))
            raise TemplateNotFoundError(f"Template not found: {e}")
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
        """Load all data needed for run report."""
        # Load run
        run = self.storage.get_run(run_id)
        if run is None:
            raise RunNotFoundError(f"Run not found: {run_id}")

        # Load metrics
        performance = self.storage.get_performance_metrics(run_id)
        quality = self.storage.get_quality_metrics(run_id)
        workflow = self.storage.get_workflow_metrics(run_id)

        # Calculate summary statistics
        summary = self._calculate_summary(run, performance, quality, workflow)

        return RunReportData(
            run=run,
            performance=performance or PerformanceMetrics(),
            quality=quality or QualityMetrics(),
            workflow=workflow or WorkflowMetrics(),
            summary=summary,
            generation_time=datetime.now(),
            version="1.0.0",
            status=run.status,
        )

    def _calculate_summary(
        self,
        run: BenchmarkRun,
        performance: Optional[PerformanceMetrics],
        quality: Optional[QualityMetrics],
        workflow: Optional[WorkflowMetrics],
    ) -> Dict[str, Any]:
        """Calculate summary statistics for report."""
        summary: Dict[str, Any] = {
            "total_duration": (run.end_time - run.start_time) if run.end_time else None,
            "status": run.status,
            "success": run.status == "completed",
        }

        if performance:
            summary["avg_response_time"] = performance.avg_response_time_ms
            summary["total_api_calls"] = performance.total_api_calls

        if quality:
            summary["test_coverage"] = quality.test_coverage_percent
            summary["total_errors"] = quality.error_count

        if workflow and workflow.phase_durations:
            summary["total_phases"] = len(workflow.phase_durations)

        return summary

    def _generate_run_charts(self, run_data: RunReportData) -> Dict[str, str]:
        """Generate charts for run report."""
        chart_gen = ChartGenerator()
        charts = {}

        # Phase duration chart
        if run_data.workflow and run_data.workflow.phase_durations:
            try:
                phase_names = list(run_data.workflow.phase_durations.keys())
                durations = list(run_data.workflow.phase_durations.values())
                charts["phase_durations"] = chart_gen.generate_phase_duration_chart(
                    phase_names, durations
                )
            except Exception as e:
                logger.warning("phase_duration_chart_failed", error=str(e))

        # Test coverage gauge
        if run_data.quality and run_data.quality.test_coverage_percent is not None:
            try:
                charts["test_coverage"] = chart_gen.generate_test_coverage_gauge(
                    run_data.quality.test_coverage_percent
                )
            except Exception as e:
                logger.warning("coverage_chart_failed", error=str(e))

        return charts

    def _write_report(
        self,
        html: str,
        output_path: Path,
        overwrite: bool
    ) -> None:
        """Write HTML report to file."""
        if output_path.exists() and not overwrite:
            raise IOError(f"File already exists: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            output_path.write_text(html, encoding="utf-8")
        except Exception as e:
            logger.error("report_write_failed", error=str(e))
            raise IOError(f"Failed to write report: {e}")

    # Comparison Report Methods

    def generate_comparison_report(
        self,
        run_id1: str,
        run_id2: str,
        output_path: Path,
        significance_threshold: float = 5.0,
        include_charts: bool = True,
        overwrite: bool = True
    ) -> Path:
        """Generate comparison report for two benchmark runs."""
        logger.info(
            "generating_comparison_report",
            run_id1=run_id1,
            run_id2=run_id2,
        )

        # Load both runs
        run1_data = self._load_run_data(run_id1)
        run2_data = self._load_run_data(run_id2)

        # Calculate comparisons
        comparison_data = self._calculate_comparisons(
            run1_data,
            run2_data,
            significance_threshold
        )

        # Generate charts
        if include_charts:
            try:
                comparison_data.charts = self._generate_comparison_charts(
                    run1_data, run2_data, comparison_data
                )
            except Exception as e:
                logger.warning("comparison_charts_failed", error=str(e))

        # Render template
        try:
            template = self.env.get_template("comparison_report.html.j2")
            html = template.render(
                run1=comparison_data.run1,
                run2=comparison_data.run2,
                performance=comparison_data.performance,
                quality=comparison_data.quality,
                workflow=comparison_data.workflow,
                summary=comparison_data.summary,
                charts=comparison_data.charts,
                generation_time=comparison_data.generation_time,
                version="1.0.0",
            )
        except Exception as e:
            logger.error("template_render_failed", error=str(e))
            raise TemplateNotFoundError(f"Failed to render template: {e}")

        self._write_report(html, output_path, overwrite)

        logger.info("comparison_report_generated", output_path=str(output_path))
        return output_path

    def _calculate_comparisons(
        self,
        run1_data: RunReportData,
        run2_data: RunReportData,
        threshold: float
    ) -> ComparisonReportData:
        """Calculate metric comparisons between two runs."""
        performance = self._compare_performance(
            run1_data.performance, run2_data.performance, threshold
        )
        quality = self._compare_quality(
            run1_data.quality, run2_data.quality, threshold
        )
        workflow = self._compare_workflow(
            run1_data.workflow, run2_data.workflow, threshold
        )

        summary = self._calculate_comparison_summary(performance, quality, workflow)

        return ComparisonReportData(
            run1=run1_data.run,
            run2=run2_data.run,
            performance=performance,
            quality=quality,
            workflow=workflow,
            summary=summary,
            charts={},
            generation_time=datetime.now(),
        )

    def _compare_performance(
        self, perf1: PerformanceMetrics, perf2: PerformanceMetrics, threshold: float
    ) -> List[MetricComparison]:
        """Compare performance metrics."""
        return [
            self._create_metric_comparison(
                "Average Response Time (ms)",
                perf1.avg_response_time_ms or 0,
                perf2.avg_response_time_ms or 0,
                threshold,
                lower_is_better=True
            ),
            self._create_metric_comparison(
                "Total API Calls",
                perf1.total_api_calls or 0,
                perf2.total_api_calls or 0,
                threshold,
                lower_is_better=True
            ),
            self._create_metric_comparison(
                "Total Tokens",
                perf1.total_tokens_used or 0,
                perf2.total_tokens_used or 0,
                threshold,
                lower_is_better=True
            ),
        ]

    def _compare_quality(
        self, quality1: QualityMetrics, quality2: QualityMetrics, threshold: float
    ) -> List[MetricComparison]:
        """Compare quality metrics."""
        return [
            self._create_metric_comparison(
                "Test Coverage (%)",
                quality1.test_coverage_percent or 0,
                quality2.test_coverage_percent or 0,
                threshold,
                lower_is_better=False
            ),
            self._create_metric_comparison(
                "Error Count",
                quality1.error_count or 0,
                quality2.error_count or 0,
                threshold,
                lower_is_better=True
            ),
        ]

    def _compare_workflow(
        self, workflow1: WorkflowMetrics, workflow2: WorkflowMetrics, threshold: float
    ) -> List[MetricComparison]:
        """Compare workflow metrics."""
        total1 = sum(workflow1.phase_durations.values()) if workflow1.phase_durations else 0
        total2 = sum(workflow2.phase_durations.values()) if workflow2.phase_durations else 0

        return [
            self._create_metric_comparison(
                "Total Duration (s)",
                total1,
                total2,
                threshold,
                lower_is_better=True
            ),
        ]

    def _create_metric_comparison(
        self,
        name: str,
        value1: float,
        value2: float,
        threshold: float,
        lower_is_better: bool
    ) -> MetricComparison:
        """Create a metric comparison."""
        absolute_delta = value2 - value1

        if value1 != 0:
            percent_delta = (absolute_delta / value1) * 100
        else:
            percent_delta = 0.0 if value2 == 0 else 100.0

        if abs(percent_delta) < 0.1:
            direction = ChangeDirection.UNCHANGED
        elif lower_is_better:
            direction = (ChangeDirection.IMPROVED if absolute_delta < 0
                        else ChangeDirection.REGRESSED)
        else:
            direction = (ChangeDirection.IMPROVED if absolute_delta > 0
                        else ChangeDirection.REGRESSED)

        is_significant = abs(percent_delta) >= threshold

        return MetricComparison(
            name=name,
            run1_value=value1,
            run2_value=value2,
            absolute_delta=absolute_delta,
            percent_delta=percent_delta,
            direction=direction,
            is_significant=is_significant,
        )

    def _calculate_comparison_summary(
        self,
        performance: List[MetricComparison],
        quality: List[MetricComparison],
        workflow: List[MetricComparison]
    ) -> Dict[str, Any]:
        """Calculate summary for comparison."""
        all_comparisons = performance + quality + workflow

        improved = sum(1 for c in all_comparisons if c.direction == ChangeDirection.IMPROVED)
        regressed = sum(1 for c in all_comparisons if c.direction == ChangeDirection.REGRESSED)
        unchanged = sum(1 for c in all_comparisons if c.direction == ChangeDirection.UNCHANGED)

        total = len(all_comparisons)
        overall_score = (improved / total * 100) if total > 0 else 0

        return {
            "total_metrics": total,
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
            "overall_score": overall_score,
        }

    def _generate_comparison_charts(
        self,
        run1_data: RunReportData,
        run2_data: RunReportData,
        comparison_data: ComparisonReportData
    ) -> Dict[str, str]:
        """Generate charts for comparison report."""
        chart_gen = ChartGenerator()
        charts = {}

        try:
            metric_names = [c.name for c in comparison_data.performance[:3]]
            run1_values = [c.run1_value for c in comparison_data.performance[:3]]
            run2_values = [c.run2_value for c in comparison_data.performance[:3]]

            charts["performance_comparison"] = chart_gen.generate_comparison_bar_chart(
                metric_names,
                run1_values,
                run2_values,
                f"Run {run1_data.run.run_id[:8]}",
                f"Run {run2_data.run.run_id[:8]}",
                "Performance Metrics Comparison"
            )
        except Exception as e:
            logger.warning("comparison_chart_failed", error=str(e))

        return charts

    # Trend Analysis Methods

    def generate_trend_report(
        self,
        run_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_path: Path = None,
        include_charts: bool = True,
        overwrite: bool = True
    ) -> Path:
        """Generate trend analysis report."""
        logger.info("generating_trend_report")

        # Load runs
        if run_ids:
            runs = [self.storage.get_run(rid) for rid in run_ids]
            runs = [r for r in runs if r is not None]
        else:
            runs = self._get_runs_by_date_range(start_date, end_date)

        if len(runs) < 2:
            raise ValueError("Need at least 2 runs for trend analysis")

        runs.sort(key=lambda r: r.start_time)

        # Calculate trends
        trend_data = self._calculate_trends(runs)
        trend_data.insights = self._generate_insights(trend_data)

        # Generate charts
        if include_charts:
            try:
                trend_data.charts = self._generate_trend_charts(trend_data)
            except Exception as e:
                logger.warning("trend_charts_failed", error=str(e))

        # Render template
        try:
            template = self.env.get_template("trend_report.html.j2")
            html = template.render(
                runs=trend_data.runs,
                performance_trends=trend_data.performance_trends,
                quality_trends=trend_data.quality_trends,
                workflow_trends=trend_data.workflow_trends,
                summary=trend_data.summary,
                insights=trend_data.insights,
                charts=trend_data.charts,
                generation_time=trend_data.generation_time,
                version="1.0.0",
            )
        except Exception as e:
            logger.error("template_render_failed", error=str(e))
            raise TemplateNotFoundError(f"Failed to render template: {e}")

        self._write_report(html, output_path, overwrite)

        logger.info("trend_report_generated", output_path=str(output_path))
        return output_path

    def _get_runs_by_date_range(
        self, start_date: Optional[datetime], end_date: Optional[datetime]
    ) -> List[BenchmarkRun]:
        """Get all runs within date range."""
        all_runs = self.storage.get_all_runs()

        if start_date:
            all_runs = [r for r in all_runs if r.start_time >= start_date]
        if end_date:
            all_runs = [r for r in all_runs if r.start_time <= end_date]

        return all_runs

    def _calculate_trends(self, runs: List[BenchmarkRun]) -> TrendReportData:
        """Calculate trend statistics."""
        timestamps = [r.start_time for r in runs]

        # Load all metrics
        performance_metrics = [self.storage.get_performance_metrics(r.run_id) for r in runs]
        quality_metrics = [self.storage.get_quality_metrics(r.run_id) for r in runs]

        # Calculate trends
        performance_trends = [
            self._calculate_metric_trend(
                "Average Response Time (ms)",
                [p.avg_response_time_ms for p in performance_metrics if p],
                timestamps,
                lower_is_better=True
            ),
        ]

        quality_trends = [
            self._calculate_metric_trend(
                "Test Coverage (%)",
                [q.test_coverage_percent for q in quality_metrics if q],
                timestamps,
                lower_is_better=False
            ),
        ]

        time_span = runs[-1].start_time - runs[0].start_time

        summary = {
            "total_runs": len(runs),
            "time_span_days": time_span.days,
            "first_run_date": runs[0].start_time,
            "last_run_date": runs[-1].start_time,
            "metrics_improving": sum(1 for t in performance_trends + quality_trends
                                    if t.trend_direction == "improving"),
            "metrics_degrading": sum(1 for t in performance_trends + quality_trends
                                    if t.trend_direction == "degrading"),
            "metrics_stable": sum(1 for t in performance_trends + quality_trends
                                 if t.trend_direction == "stable"),
        }

        return TrendReportData(
            runs=runs,
            performance_trends=performance_trends,
            quality_trends=quality_trends,
            workflow_trends=[],
            summary=summary,
            insights=[],
            charts={},
            generation_time=datetime.now(),
        )

    def _calculate_metric_trend(
        self, metric_name: str, values: List[float], timestamps: List[datetime],
        lower_is_better: bool
    ) -> TrendStatistics:
        """Calculate trend statistics for a single metric."""
        values_array = np.array(values)

        mean = float(np.mean(values_array))
        median = float(np.median(values_array))
        std_dev = float(np.std(values_array))
        min_value = float(np.min(values_array))
        max_value = float(np.max(values_array))

        # Linear regression
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        r_squared = r_value ** 2

        # Trend direction
        if abs(slope) < std_dev * 0.1:
            trend_direction = "stable"
        elif (slope < 0 and lower_is_better) or (slope > 0 and not lower_is_better):
            trend_direction = "improving"
        else:
            trend_direction = "degrading"

        # Percent change
        if values[0] != 0:
            percent_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            percent_change = 0.0

        return TrendStatistics(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            trend_direction=trend_direction,
            slope=float(slope),
            r_squared=float(r_squared),
            percent_change=percent_change,
            ma_7=None,
            ma_30=None,
            outlier_indices=[],
        )

    def _generate_insights(self, trend_data: TrendReportData) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []

        all_trends = trend_data.performance_trends + trend_data.quality_trends

        improving = [t for t in all_trends if t.trend_direction == "improving"]
        if improving:
            most_improved = max(improving, key=lambda t: abs(t.percent_change))
            insights.append(
                f"Most improved: {most_improved.metric_name} "
                f"({most_improved.percent_change:+.1f}%)"
            )

        degrading = [t for t in all_trends if t.trend_direction == "degrading"]
        if degrading:
            most_degraded = max(degrading, key=lambda t: abs(t.percent_change))
            insights.append(
                f"Needs attention: {most_degraded.metric_name} "
                f"({most_degraded.percent_change:+.1f}%)"
            )

        return insights

    def _generate_trend_charts(self, trend_data: TrendReportData) -> Dict[str, str]:
        """Generate charts for trend report."""
        chart_gen = ChartGenerator()
        charts = {}

        for trend in trend_data.performance_trends + trend_data.quality_trends:
            try:
                chart_name = trend.metric_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
                charts[chart_name] = chart_gen.generate_performance_timeline(
                    trend.timestamps,
                    trend.values,
                    title=trend.metric_name
                )
            except Exception as e:
                logger.warning("trend_chart_failed", metric=trend.metric_name, error=str(e))

        return charts
