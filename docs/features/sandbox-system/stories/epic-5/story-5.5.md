# Story 5.5: Trend Analysis

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer tracking long-term improvements
**I want** to analyze trends across multiple benchmark runs over time
**So that** I can see patterns, identify improvements, and track GAO-Dev's evolution

---

## Acceptance Criteria

### AC1: Trend Report Generation
- [ ] `generate_trend_report(run_ids, output_path)` method added to ReportGenerator
- [ ] Accepts list of run IDs (chronologically ordered)
- [ ] Loads data for all runs
- [ ] Calculates trend statistics
- [ ] Renders trend_report.html.j2 template
- [ ] Returns path to generated report

### AC2: Time-Series Analysis
- [ ] Response time trend over time
- [ ] API call trend over time
- [ ] Token usage trend over time
- [ ] Test coverage trend over time
- [ ] Error rate trend over time
- [ ] Duration trend over time

### AC3: Statistical Calculations
- [ ] Mean, median, std deviation for each metric
- [ ] Min/max values with timestamps
- [ ] Trend direction (improving, stable, degrading)
- [ ] Rate of change calculation
- [ ] Outlier detection
- [ ] Moving averages (7-run, 30-run)

### AC4: Trend Visualization
- [ ] Line charts for time-series metrics
- [ ] Trend lines (linear regression)
- [ ] Confidence intervals (standard deviation bands)
- [ ] Annotate significant events
- [ ] Highlight best/worst runs
- [ ] Show moving averages

### AC5: Comparative Analysis
- [ ] First vs. latest run comparison
- [ ] Best vs. worst run comparison
- [ ] Recent trend (last 5 runs)
- [ ] Overall trend (all runs)
- [ ] Improvement velocity (% improvement per week)

### AC6: Insights & Recommendations
- [ ] Identify metrics with most improvement
- [ ] Identify metrics with most regression
- [ ] Identify metrics with high variability
- [ ] Suggest areas for focus
- [ ] Stability assessment

---

## Technical Details

### Implementation Approach

**Extend ReportGenerator** in `gao_dev/sandbox/reporting/report_generator.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import numpy as np
from scipy import stats  # For linear regression


@dataclass
class TrendStatistics:
    """Statistical summary for a metric trend."""

    metric_name: str
    values: List[float]
    timestamps: List[datetime]

    # Basic statistics
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float

    # Trend analysis
    trend_direction: str  # "improving", "stable", "degrading"
    slope: float  # From linear regression
    r_squared: float  # Goodness of fit
    percent_change: float  # First to last

    # Moving averages
    ma_7: Optional[List[float]]  # 7-run moving average
    ma_30: Optional[List[float]]  # 30-run moving average

    # Outliers
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
    """Extended with trend analysis."""

    def generate_trend_report(
        self,
        run_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_path: Path = None,
        include_charts: bool = True,
        overwrite: bool = True
    ) -> Path:
        """
        Generate trend analysis report for multiple benchmark runs.

        Args:
            run_ids: List of run IDs (if None, use date range)
            start_date: Start date for runs (if run_ids not provided)
            end_date: End date for runs (if run_ids not provided)
            output_path: Where to save HTML report
            include_charts: Whether to include charts
            overwrite: Whether to overwrite existing file

        Returns:
            Path to generated report

        Raises:
            ValueError: If no runs found or invalid parameters
            TemplateNotFoundError: If template missing
            IOError: If can't write file
        """
        logger.info(
            "generating_trend_report",
            run_count=len(run_ids) if run_ids else None,
            start_date=start_date,
            end_date=end_date,
        )

        # Load runs
        if run_ids:
            runs = [self.storage.get_run(rid) for rid in run_ids]
            runs = [r for r in runs if r is not None]
        else:
            runs = self._get_runs_by_date_range(start_date, end_date)

        if len(runs) < 2:
            raise ValueError("Need at least 2 runs for trend analysis")

        # Sort by timestamp
        runs.sort(key=lambda r: r.start_time)

        # Calculate trends
        trend_data = self._calculate_trends(runs)

        # Generate insights
        trend_data.insights = self._generate_insights(trend_data)

        # Generate charts
        if include_charts:
            trend_data.charts = self._generate_trend_charts(trend_data)

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

        # Write to file
        self._write_report(html, output_path, overwrite)

        logger.info(
            "trend_report_generated",
            run_count=len(runs),
            output_path=str(output_path),
        )

        return output_path

    def _get_runs_by_date_range(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[BenchmarkRun]:
        """Get all runs within date range."""
        all_runs = self.storage.get_all_runs()

        if start_date:
            all_runs = [r for r in all_runs if r.start_time >= start_date]

        if end_date:
            all_runs = [r for r in all_runs if r.start_time <= end_date]

        return all_runs

    def _calculate_trends(
        self,
        runs: List[BenchmarkRun]
    ) -> TrendReportData:
        """Calculate trend statistics for all metrics."""

        # Load all metrics for all runs
        performance_metrics = [
            self.storage.get_performance_metrics(r.run_id) for r in runs
        ]
        quality_metrics = [
            self.storage.get_quality_metrics(r.run_id) for r in runs
        ]
        workflow_metrics = [
            self.storage.get_workflow_metrics(r.run_id) for r in runs
        ]

        timestamps = [r.start_time for r in runs]

        # Calculate performance trends
        performance_trends = [
            self._calculate_metric_trend(
                "Average Response Time (ms)",
                [p.avg_response_time_ms for p in performance_metrics if p],
                timestamps,
                lower_is_better=True
            ),
            self._calculate_metric_trend(
                "Total API Calls",
                [p.total_api_calls for p in performance_metrics if p],
                timestamps,
                lower_is_better=True
            ),
            self._calculate_metric_trend(
                "Total Tokens",
                [p.total_tokens_used for p in performance_metrics if p],
                timestamps,
                lower_is_better=True
            ),
        ]

        # Calculate quality trends
        quality_trends = [
            self._calculate_metric_trend(
                "Test Coverage (%)",
                [q.test_coverage_percent for q in quality_metrics if q],
                timestamps,
                lower_is_better=False
            ),
            self._calculate_metric_trend(
                "Error Count",
                [q.error_count for q in quality_metrics if q],
                timestamps,
                lower_is_better=True
            ),
        ]

        # Calculate workflow trends
        workflow_trends = [
            self._calculate_metric_trend(
                "Total Duration (s)",
                [sum(w.phase_durations.values()) for w in workflow_metrics if w],
                timestamps,
                lower_is_better=True
            ),
        ]

        # Calculate summary
        summary = self._calculate_trend_summary(
            runs,
            performance_trends,
            quality_trends,
            workflow_trends
        )

        return TrendReportData(
            runs=runs,
            performance_trends=performance_trends,
            quality_trends=quality_trends,
            workflow_trends=workflow_trends,
            summary=summary,
            insights=[],
            charts={},
            generation_time=datetime.now(),
        )

    def _calculate_metric_trend(
        self,
        metric_name: str,
        values: List[float],
        timestamps: List[datetime],
        lower_is_better: bool
    ) -> TrendStatistics:
        """
        Calculate trend statistics for a single metric.

        Args:
            metric_name: Name of the metric
            values: List of metric values
            timestamps: List of timestamps
            lower_is_better: Whether lower values are improvements

        Returns:
            TrendStatistics object
        """
        values_array = np.array(values)

        # Basic statistics
        mean = float(np.mean(values_array))
        median = float(np.median(values_array))
        std_dev = float(np.std(values_array))
        min_value = float(np.min(values_array))
        max_value = float(np.max(values_array))

        # Linear regression for trend
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        r_squared = r_value ** 2

        # Determine trend direction
        if abs(slope) < std_dev * 0.1:  # Slope less than 10% of std dev
            trend_direction = "stable"
        elif (slope < 0 and lower_is_better) or (slope > 0 and not lower_is_better):
            trend_direction = "improving"
        else:
            trend_direction = "degrading"

        # Percent change from first to last
        if values[0] != 0:
            percent_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            percent_change = 0.0

        # Moving averages
        ma_7 = self._calculate_moving_average(values, window=7)
        ma_30 = self._calculate_moving_average(values, window=30)

        # Outlier detection (using IQR method)
        outlier_indices = self._detect_outliers(values_array)

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
            ma_7=ma_7,
            ma_30=ma_30,
            outlier_indices=outlier_indices,
        )

    @staticmethod
    def _calculate_moving_average(
        values: List[float],
        window: int
    ) -> Optional[List[float]]:
        """Calculate moving average."""
        if len(values) < window:
            return None

        ma = []
        for i in range(len(values)):
            if i < window - 1:
                ma.append(None)
            else:
                window_values = values[i - window + 1:i + 1]
                ma.append(np.mean(window_values))

        return ma

    @staticmethod
    def _detect_outliers(values: np.ndarray) -> List[int]:
        """Detect outliers using IQR method."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)

        return outliers

    def _calculate_trend_summary(
        self,
        runs: List[BenchmarkRun],
        performance_trends: List[TrendStatistics],
        quality_trends: List[TrendStatistics],
        workflow_trends: List[TrendStatistics]
    ) -> Dict[str, Any]:
        """Calculate summary for trend report."""
        all_trends = performance_trends + quality_trends + workflow_trends

        improving = sum(1 for t in all_trends if t.trend_direction == "improving")
        degrading = sum(1 for t in all_trends if t.trend_direction == "degrading")
        stable = sum(1 for t in all_trends if t.trend_direction == "stable")

        # Time span
        time_span = runs[-1].start_time - runs[0].start_time

        return {
            "total_runs": len(runs),
            "time_span_days": time_span.days,
            "first_run_date": runs[0].start_time,
            "last_run_date": runs[-1].start_time,
            "metrics_improving": improving,
            "metrics_degrading": degrading,
            "metrics_stable": stable,
        }

    def _generate_insights(
        self,
        trend_data: TrendReportData
    ) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []

        all_trends = (
            trend_data.performance_trends +
            trend_data.quality_trends +
            trend_data.workflow_trends
        )

        # Most improved metric
        most_improved = max(
            [t for t in all_trends if t.trend_direction == "improving"],
            key=lambda t: abs(t.percent_change),
            default=None
        )
        if most_improved:
            insights.append(
                f"Most improved: {most_improved.metric_name} "
                f"({most_improved.percent_change:+.1f}%)"
            )

        # Most degraded metric
        most_degraded = max(
            [t for t in all_trends if t.trend_direction == "degrading"],
            key=lambda t: abs(t.percent_change),
            default=None
        )
        if most_degraded:
            insights.append(
                f"Needs attention: {most_degraded.metric_name} "
                f"({most_degraded.percent_change:+.1f}%)"
            )

        # High variability metrics
        high_variance = [t for t in all_trends
                        if t.std_dev / t.mean > 0.2 if t.mean != 0]
        if high_variance:
            insights.append(
                f"High variability: {', '.join([t.metric_name for t in high_variance[:2]])}"
            )

        # Overall trend
        improving_count = trend_data.summary["metrics_improving"]
        total_count = len(all_trends)
        if improving_count / total_count > 0.6:
            insights.append("Overall trend: Strong improvement across most metrics")
        elif improving_count / total_count > 0.4:
            insights.append("Overall trend: Moderate improvement")
        else:
            insights.append("Overall trend: Mixed results, focus needed")

        return insights

    def _generate_trend_charts(
        self,
        trend_data: TrendReportData
    ) -> Dict[str, str]:
        """Generate charts for trend report."""
        chart_gen = ChartGenerator()
        charts = {}

        # Performance trend chart
        for trend in trend_data.performance_trends:
            chart_name = trend.metric_name.lower().replace(" ", "_")
            charts[chart_name] = chart_gen.generate_performance_timeline(
                trend.timestamps,
                trend.values,
                title=trend.metric_name
            )

        # Quality trend chart
        for trend in trend_data.quality_trends:
            chart_name = trend.metric_name.lower().replace(" ", "_")
            charts[chart_name] = chart_gen.generate_performance_timeline(
                trend.timestamps,
                trend.values,
                title=trend.metric_name
            )

        return charts
```

---

## Testing Strategy

### Unit Tests
- Statistical calculations (mean, median, std dev)
- Linear regression trend calculation
- Moving average calculation
- Outlier detection
- Trend direction determination
- Handles edge cases (2 runs, identical values)

### Integration Tests
- Full trend report generation
- Multiple runs loaded correctly
- All trends calculated
- Insights generated
- Template renders correctly
- Charts embedded correctly

### Test Coverage Goal
- 95%+ for trend calculation logic
- All statistical methods tested

---

## Dependencies

### Before This Story
- Story 5.1: Report Templates (trend template)
- Story 5.2: HTML Report Generator (base generator)
- Story 5.3: Chart Generation (timeline charts)

### Blocks Other Stories
- None

### External Dependencies
- numpy (add to dependencies)
- scipy (for linear regression)

**Update `pyproject.toml`:**
```toml
dependencies = [
    ...
    "numpy>=1.24.0",
    "scipy>=1.10.0",
]
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] generate_trend_report method implemented
- [ ] Statistical calculations working
- [ ] Trend direction determination correct
- [ ] Insights generation working
- [ ] Charts generated correctly
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing (95%+ coverage)
- [ ] Integration tests passing
- [ ] Visual review of trend reports
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Committed to feature branch

---

## Notes

**Design Decisions:**
- Use linear regression for trend lines
- IQR method for outlier detection
- Moving averages for smoothing
- Insights based on statistical analysis
- Support both run IDs and date ranges

**Statistical Methods:**
- Linear regression: scipy.stats.linregress
- Moving average: simple moving average
- Outlier detection: 1.5 * IQR method
- Trend direction: slope + standard deviation threshold

**Future Enhancements:**
- Seasonal decomposition (detect patterns)
- Forecasting (predict future performance)
- Anomaly detection (detect unusual runs)
- Correlation analysis (which metrics move together)
- Multi-variate regression

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: ReportGenerator component
- NumPy Documentation: https://numpy.org/
- SciPy Stats: https://docs.scipy.org/doc/scipy/reference/stats.html
