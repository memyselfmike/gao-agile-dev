# Story 5.4: Comparison Report

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 4 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer evaluating improvements
**I want** to compare two benchmark runs side-by-side
**So that** I can see what changed, what improved, and what regressed

---

## Acceptance Criteria

### AC1: Comparison Report Generation
- [ ] `generate_comparison_report(run_id1, run_id2, output_path)` method added to ReportGenerator
- [ ] Loads data for both runs
- [ ] Calculates deltas for all metrics
- [ ] Renders comparison_report.html.j2 template
- [ ] Returns path to generated report
- [ ] Handles missing metrics gracefully

### AC2: Metric Delta Calculation
- [ ] Calculates absolute difference for each metric
- [ ] Calculates percentage change for each metric
- [ ] Identifies improvements (positive changes)
- [ ] Identifies regressions (negative changes)
- [ ] Handles division by zero
- [ ] Handles None/null values

### AC3: Visual Comparison
- [ ] Side-by-side metric display
- [ ] Color coding for improvements (green) and regressions (red)
- [ ] Delta values displayed (e.g., "+5.2%", "-120ms")
- [ ] Arrows or icons for direction of change
- [ ] Highlight significant changes (threshold-based)

### AC4: Comparison Charts
- [ ] Grouped bar charts for metric comparison
- [ ] Waterfall chart for cumulative impact
- [ ] Radar chart comparison for quality metrics
- [ ] Timeline overlay for both runs

### AC5: Summary Section
- [ ] Overall improvement score/percentage
- [ ] Count of improved metrics
- [ ] Count of regressed metrics
- [ ] Count of unchanged metrics
- [ ] Highlight most improved areas
- [ ] Highlight most regressed areas

### AC6: Detailed Breakdown
- [ ] Performance comparison (response time, API calls, tokens)
- [ ] Quality comparison (coverage, errors, test count)
- [ ] Workflow comparison (phase durations, agent handoffs)
- [ ] Resource comparison (CPU, memory, disk)

---

## Technical Details

### Implementation Approach

**Extend ReportGenerator** in `gao_dev/sandbox/reporting/report_generator.py`:

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ChangeDirection(Enum):
    """Direction of metric change."""
    IMPROVED = "improved"
    REGRESSED = "regressed"
    UNCHANGED = "unchanged"


@dataclass
class MetricComparison:
    """Comparison of a single metric between two runs."""

    name: str
    run1_value: float
    run2_value: float
    absolute_delta: float
    percent_delta: float
    direction: ChangeDirection
    is_significant: bool  # Based on threshold


@dataclass
class ComparisonReportData:
    """Data structure for comparison report."""

    run1: BenchmarkRun
    run2: BenchmarkRun
    performance_comparisons: List[MetricComparison]
    quality_comparisons: List[MetricComparison]
    workflow_comparisons: List[MetricComparison]
    summary: Dict[str, Any]
    charts: Dict[str, str]  # Base64-encoded chart images
    generation_time: datetime


class ReportGenerator:
    """Extended with comparison report generation."""

    def generate_comparison_report(
        self,
        run_id1: str,
        run_id2: str,
        output_path: Path,
        significance_threshold: float = 5.0,  # 5% change
        include_charts: bool = True,
        overwrite: bool = True
    ) -> Path:
        """
        Generate comparison report for two benchmark runs.

        Args:
            run_id1: First run identifier (baseline)
            run_id2: Second run identifier (comparison)
            output_path: Where to save HTML report
            significance_threshold: Percentage change threshold for significance
            include_charts: Whether to include charts
            overwrite: Whether to overwrite existing file

        Returns:
            Path to generated report

        Raises:
            RunNotFoundError: If either run doesn't exist
            TemplateNotFoundError: If template missing
            IOError: If can't write file
        """
        logger.info(
            "generating_comparison_report",
            run_id1=run_id1,
            run_id2=run_id2,
            output_path=str(output_path),
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

        # Generate comparison charts
        if include_charts:
            comparison_data.charts = self._generate_comparison_charts(
                run1_data,
                run2_data,
                comparison_data
            )

        # Render template
        try:
            template = self.env.get_template("comparison_report.html.j2")
            html = template.render(
                run1=comparison_data.run1,
                run2=comparison_data.run2,
                performance=comparison_data.performance_comparisons,
                quality=comparison_data.quality_comparisons,
                workflow=comparison_data.workflow_comparisons,
                summary=comparison_data.summary,
                charts=comparison_data.charts,
                generation_time=comparison_data.generation_time,
                version="1.0.0",
            )
        except Exception as e:
            logger.error("template_render_failed", error=str(e))
            raise TemplateNotFoundError(f"Failed to render template: {e}")

        # Write to file
        self._write_report(html, output_path, overwrite)

        logger.info(
            "comparison_report_generated",
            run_id1=run_id1,
            run_id2=run_id2,
            output_path=str(output_path),
        )

        return output_path

    def _calculate_comparisons(
        self,
        run1_data: RunReportData,
        run2_data: RunReportData,
        threshold: float
    ) -> ComparisonReportData:
        """
        Calculate metric comparisons between two runs.

        Args:
            run1_data: First run data
            run2_data: Second run data
            threshold: Significance threshold (percentage)

        Returns:
            ComparisonReportData with all comparisons
        """
        performance_comparisons = self._compare_performance_metrics(
            run1_data.performance,
            run2_data.performance,
            threshold
        )

        quality_comparisons = self._compare_quality_metrics(
            run1_data.quality,
            run2_data.quality,
            threshold
        )

        workflow_comparisons = self._compare_workflow_metrics(
            run1_data.workflow,
            run2_data.workflow,
            threshold
        )

        # Calculate summary
        summary = self._calculate_comparison_summary(
            performance_comparisons,
            quality_comparisons,
            workflow_comparisons
        )

        return ComparisonReportData(
            run1=run1_data.run,
            run2=run2_data.run,
            performance_comparisons=performance_comparisons,
            quality_comparisons=quality_comparisons,
            workflow_comparisons=workflow_comparisons,
            summary=summary,
            charts={},
            generation_time=datetime.now(),
        )

    def _compare_performance_metrics(
        self,
        perf1: PerformanceMetrics,
        perf2: PerformanceMetrics,
        threshold: float
    ) -> List[MetricComparison]:
        """Compare performance metrics."""
        comparisons = []

        # Response time
        comparisons.append(self._create_metric_comparison(
            name="Average Response Time (ms)",
            value1=perf1.avg_response_time_ms,
            value2=perf2.avg_response_time_ms,
            threshold=threshold,
            lower_is_better=True
        ))

        # API calls
        comparisons.append(self._create_metric_comparison(
            name="Total API Calls",
            value1=perf1.total_api_calls,
            value2=perf2.total_api_calls,
            threshold=threshold,
            lower_is_better=True
        ))

        # Token usage
        comparisons.append(self._create_metric_comparison(
            name="Total Tokens",
            value1=perf1.total_tokens_used,
            value2=perf2.total_tokens_used,
            threshold=threshold,
            lower_is_better=True
        ))

        return comparisons

    def _compare_quality_metrics(
        self,
        quality1: QualityMetrics,
        quality2: QualityMetrics,
        threshold: float
    ) -> List[MetricComparison]:
        """Compare quality metrics."""
        comparisons = []

        # Test coverage
        comparisons.append(self._create_metric_comparison(
            name="Test Coverage (%)",
            value1=quality1.test_coverage_percent,
            value2=quality2.test_coverage_percent,
            threshold=threshold,
            lower_is_better=False
        ))

        # Error count
        comparisons.append(self._create_metric_comparison(
            name="Error Count",
            value1=quality1.error_count,
            value2=quality2.error_count,
            threshold=threshold,
            lower_is_better=True
        ))

        # Test count
        comparisons.append(self._create_metric_comparison(
            name="Test Count",
            value1=quality1.test_count,
            value2=quality2.test_count,
            threshold=threshold,
            lower_is_better=False
        ))

        return comparisons

    def _compare_workflow_metrics(
        self,
        workflow1: WorkflowMetrics,
        workflow2: WorkflowMetrics,
        threshold: float
    ) -> List[MetricComparison]:
        """Compare workflow metrics."""
        comparisons = []

        # Total duration (sum of all phases)
        total1 = sum(workflow1.phase_durations.values())
        total2 = sum(workflow2.phase_durations.values())

        comparisons.append(self._create_metric_comparison(
            name="Total Duration (s)",
            value1=total1,
            value2=total2,
            threshold=threshold,
            lower_is_better=True
        ))

        # Agent handoffs
        comparisons.append(self._create_metric_comparison(
            name="Agent Handoffs",
            value1=workflow1.agent_handoffs,
            value2=workflow2.agent_handoffs,
            threshold=threshold,
            lower_is_better=True
        ))

        return comparisons

    def _create_metric_comparison(
        self,
        name: str,
        value1: float,
        value2: float,
        threshold: float,
        lower_is_better: bool
    ) -> MetricComparison:
        """
        Create a metric comparison.

        Args:
            name: Metric name
            value1: Value from first run
            value2: Value from second run
            threshold: Significance threshold (percentage)
            lower_is_better: Whether lower values are improvements

        Returns:
            MetricComparison object
        """
        # Calculate deltas
        absolute_delta = value2 - value1

        if value1 != 0:
            percent_delta = (absolute_delta / value1) * 100
        else:
            percent_delta = 0.0 if value2 == 0 else 100.0

        # Determine direction
        if abs(percent_delta) < 0.1:  # Less than 0.1% change
            direction = ChangeDirection.UNCHANGED
        elif lower_is_better:
            direction = (ChangeDirection.IMPROVED if absolute_delta < 0
                        else ChangeDirection.REGRESSED)
        else:
            direction = (ChangeDirection.IMPROVED if absolute_delta > 0
                        else ChangeDirection.REGRESSED)

        # Check significance
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
        """Calculate summary statistics for comparison."""
        all_comparisons = performance + quality + workflow

        improved = sum(1 for c in all_comparisons
                      if c.direction == ChangeDirection.IMPROVED)
        regressed = sum(1 for c in all_comparisons
                       if c.direction == ChangeDirection.REGRESSED)
        unchanged = sum(1 for c in all_comparisons
                       if c.direction == ChangeDirection.UNCHANGED)

        significant_improved = sum(1 for c in all_comparisons
                                  if c.direction == ChangeDirection.IMPROVED
                                  and c.is_significant)
        significant_regressed = sum(1 for c in all_comparisons
                                   if c.direction == ChangeDirection.REGRESSED
                                   and c.is_significant)

        # Overall score (simple metric)
        total = len(all_comparisons)
        overall_score = (improved / total * 100) if total > 0 else 0

        return {
            "total_metrics": total,
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
            "significant_improved": significant_improved,
            "significant_regressed": significant_regressed,
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

        # Metric comparison bar chart
        metric_names = [c.name for c in comparison_data.performance_comparisons[:3]]
        run1_values = [c.run1_value for c in comparison_data.performance_comparisons[:3]]
        run2_values = [c.run2_value for c in comparison_data.performance_comparisons[:3]]

        charts["performance_comparison"] = chart_gen.generate_comparison_bar_chart(
            metric_names,
            run1_values,
            run2_values,
            run1_label=f"Run {run1_data.run.run_id[:8]}",
            run2_label=f"Run {run2_data.run.run_id[:8]}",
            title="Performance Metrics Comparison"
        )

        # Add more comparison charts as needed...

        return charts
```

---

## Testing Strategy

### Unit Tests
- Metric comparison calculation
- Delta calculations (absolute and percentage)
- Direction determination (improved/regressed)
- Significance threshold logic
- Handles division by zero
- Handles None values
- Summary statistics calculation

### Integration Tests
- Full comparison report generation
- Both runs loaded correctly
- All comparisons calculated
- Template renders correctly
- Charts embedded correctly

### Test Coverage Goal
- 95%+ for comparison logic
- All edge cases tested

---

## Dependencies

### Before This Story
- Story 5.1: Report Templates (comparison template)
- Story 5.2: HTML Report Generator (base generator)
- Story 5.3: Chart Generation (comparison charts)

### Blocks Other Stories
- None

### External Dependencies
- None (uses existing dependencies)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] generate_comparison_report method implemented
- [ ] Metric comparison logic working
- [ ] Comparison template rendering
- [ ] Charts generated correctly
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing (95%+ coverage)
- [ ] Integration tests passing
- [ ] Visual review of comparison reports
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Committed to feature branch

---

## Notes

**Design Decisions:**
- Run 1 is baseline, Run 2 is comparison
- Lower values are better for: response time, API calls, errors
- Higher values are better for: test coverage, test count
- Threshold-based significance (default 5%)
- Simple overall score calculation (can be enhanced later)

**Future Enhancements:**
- Compare more than 2 runs
- Weighted scoring (important metrics weighted higher)
- Statistical significance testing
- Regression alerts (email/slack notifications)
- Export comparison data to CSV

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: ReportGenerator component
