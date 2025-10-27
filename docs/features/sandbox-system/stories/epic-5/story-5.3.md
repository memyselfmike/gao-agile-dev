# Story 5.3: Chart Generation

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 5 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer reviewing benchmark results
**I want** visual charts and graphs embedded in reports
**So that** I can quickly understand trends, patterns, and comparisons visually

---

## Acceptance Criteria

### AC1: ChartGenerator Class
- [ ] `ChartGenerator` class implemented
- [ ] Generates chart images (PNG format)
- [ ] Returns base64-encoded images for HTML embedding
- [ ] Type hints for all methods
- [ ] Error handling for chart generation failures
- [ ] Logging for debugging

### AC2: Performance Charts
- [ ] Time-series chart for response times (line chart)
- [ ] API calls per phase (bar chart)
- [ ] Token usage over time (area chart)
- [ ] CPU and memory usage (dual-axis line chart)
- [ ] Handles missing data points gracefully

### AC3: Quality Charts
- [ ] Test coverage visualization (gauge chart)
- [ ] Error count by category (pie chart)
- [ ] Code quality metrics (radar chart)
- [ ] Test pass/fail breakdown (stacked bar chart)

### AC4: Workflow Charts
- [ ] Phase duration comparison (horizontal bar chart)
- [ ] Agent activity timeline (Gantt-style chart)
- [ ] Workflow progression (sankey/flow diagram)
- [ ] Handoff frequency heatmap

### AC5: Comparison Charts
- [ ] Side-by-side metric comparisons (grouped bar chart)
- [ ] Improvement/regression indicators (waterfall chart)
- [ ] Metric delta visualization (bullet chart)

### AC6: Chart Styling
- [ ] Consistent color scheme across all charts
- [ ] Professional, clean design
- [ ] Readable fonts and labels
- [ ] Proper legends and axis labels
- [ ] Responsive sizing (works in reports)
- [ ] High-resolution output (300 DPI)

### AC7: Integration with Templates
- [ ] Charts embedded as base64 images in HTML
- [ ] Chart generation integrated with ReportGenerator
- [ ] Fallback when chart generation fails (text summary)
- [ ] Lazy loading for large numbers of charts

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/reporting/chart_generator.py`

```python
"""Chart generation for benchmark reports."""

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import base64

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import structlog

from gao_dev.sandbox.metrics.models import (
    PerformanceMetrics,
    QualityMetrics,
    WorkflowMetrics,
)


logger = structlog.get_logger(__name__)


# Color scheme for consistency
COLORS = {
    "primary": "#2563eb",      # Blue
    "secondary": "#7c3aed",    # Purple
    "success": "#10b981",      # Green
    "warning": "#f59e0b",      # Orange
    "error": "#ef4444",        # Red
    "gray": "#6b7280",         # Gray
}


class ChartGeneratorError(Exception):
    """Base exception for chart generation errors."""
    pass


@dataclass
class ChartData:
    """Data structure for chart generation."""

    labels: List[str]
    values: List[float]
    title: str
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    colors: Optional[List[str]] = None


class ChartGenerator:
    """Generates charts for benchmark reports."""

    def __init__(
        self,
        dpi: int = 300,
        figsize: Tuple[int, int] = (10, 6)
    ) -> None:
        """
        Initialize chart generator.

        Args:
            dpi: Resolution for chart images
            figsize: Default figure size (width, height) in inches
        """
        self.dpi = dpi
        self.figsize = figsize

        # Set default matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')

        logger.info(
            "chart_generator_initialized",
            dpi=dpi,
            figsize=figsize,
        )

    def generate_performance_timeline(
        self,
        timestamps: List[datetime],
        response_times: List[float],
        title: str = "Response Time Over Time"
    ) -> str:
        """
        Generate line chart for response times.

        Args:
            timestamps: List of timestamps
            response_times: List of response times (ms)
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        ax.plot(
            timestamps,
            response_times,
            color=COLORS["primary"],
            linewidth=2,
            marker='o',
            markersize=4,
        )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Time", fontsize=11)
        ax.set_ylabel("Response Time (ms)", fontsize=11)
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()

        return self._figure_to_base64(fig)

    def generate_api_calls_bar_chart(
        self,
        phase_names: List[str],
        api_calls: List[int],
        title: str = "API Calls by Phase"
    ) -> str:
        """
        Generate bar chart for API calls per phase.

        Args:
            phase_names: List of phase names
            api_calls: List of API call counts
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        bars = ax.bar(
            phase_names,
            api_calls,
            color=COLORS["secondary"],
            alpha=0.8,
        )

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{int(height)}',
                ha='center',
                va='bottom',
                fontsize=10,
            )

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("Phase", fontsize=11)
        ax.set_ylabel("API Calls", fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')

        # Rotate labels if many phases
        if len(phase_names) > 5:
            plt.xticks(rotation=45, ha='right')

        plt.tight_layout()
        return self._figure_to_base64(fig)

    def generate_test_coverage_gauge(
        self,
        coverage_percent: float,
        title: str = "Test Coverage"
    ) -> str:
        """
        Generate gauge chart for test coverage.

        Args:
            coverage_percent: Coverage percentage (0-100)
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})

        # Create gauge
        theta = (coverage_percent / 100) * 180  # 0-180 degrees

        # Background arc
        ax.barh(1, 180, left=0, height=0.3, color='lightgray', alpha=0.3)

        # Value arc
        color = self._get_coverage_color(coverage_percent)
        ax.barh(1, theta, left=0, height=0.3, color=color, alpha=0.8)

        # Center text
        ax.text(
            0, 0, f'{coverage_percent:.1f}%',
            ha='center', va='center',
            fontsize=24, fontweight='bold'
        )

        ax.set_ylim(0, 2)
        ax.set_xlim(0, 180)
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('W')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['polar'].set_visible(False)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        return self._figure_to_base64(fig)

    def generate_quality_radar(
        self,
        metrics: Dict[str, float],
        title: str = "Code Quality Metrics"
    ) -> str:
        """
        Generate radar chart for quality metrics.

        Args:
            metrics: Dictionary of metric names and values (0-100)
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

        categories = list(metrics.keys())
        values = list(metrics.values())

        # Number of variables
        N = len(categories)

        # Compute angle for each axis
        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        values += values[:1]  # Complete the circle
        angles += angles[:1]

        # Plot
        ax.plot(angles, values, 'o-', linewidth=2, color=COLORS["primary"])
        ax.fill(angles, values, alpha=0.25, color=COLORS["primary"])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        ax.grid(True)

        return self._figure_to_base64(fig)

    def generate_phase_duration_chart(
        self,
        phase_names: List[str],
        durations: List[float],
        title: str = "Phase Durations"
    ) -> str:
        """
        Generate horizontal bar chart for phase durations.

        Args:
            phase_names: List of phase names
            durations: List of durations in seconds
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        y_pos = range(len(phase_names))
        colors = [COLORS["primary"] if i % 2 == 0 else COLORS["secondary"]
                  for i in range(len(phase_names))]

        bars = ax.barh(y_pos, durations, color=colors, alpha=0.8)

        # Add value labels
        for i, (bar, duration) in enumerate(zip(bars, durations)):
            width = bar.get_width()
            label = self._format_duration(duration)
            ax.text(
                width,
                i,
                f' {label}',
                va='center',
                fontsize=10,
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(phase_names)
        ax.set_xlabel("Duration", fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        return self._figure_to_base64(fig)

    def generate_comparison_bar_chart(
        self,
        metric_names: List[str],
        run1_values: List[float],
        run2_values: List[float],
        run1_label: str = "Run 1",
        run2_label: str = "Run 2",
        title: str = "Metric Comparison"
    ) -> str:
        """
        Generate grouped bar chart for comparing two runs.

        Args:
            metric_names: List of metric names
            run1_values: Values for first run
            run2_values: Values for second run
            run1_label: Label for first run
            run2_label: Label for second run
            title: Chart title

        Returns:
            Base64-encoded PNG image
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        x = range(len(metric_names))
        width = 0.35

        bars1 = ax.bar(
            [i - width/2 for i in x],
            run1_values,
            width,
            label=run1_label,
            color=COLORS["primary"],
            alpha=0.8,
        )
        bars2 = ax.bar(
            [i + width/2 for i in x],
            run2_values,
            width,
            label=run2_label,
            color=COLORS["secondary"],
            alpha=0.8,
        )

        ax.set_xlabel("Metrics", fontsize=11)
        ax.set_ylabel("Values", fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(metric_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        return self._figure_to_base64(fig)

    def _figure_to_base64(self, fig: Figure) -> str:
        """
        Convert matplotlib figure to base64-encoded PNG.

        Args:
            fig: Matplotlib figure

        Returns:
            Base64-encoded image string
        """
        buffer = BytesIO()
        try:
            fig.savefig(
                buffer,
                format='png',
                dpi=self.dpi,
                bbox_inches='tight',
                facecolor='white',
            )
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
        finally:
            plt.close(fig)
            buffer.close()

    @staticmethod
    def _get_coverage_color(coverage: float) -> str:
        """Get color based on coverage percentage."""
        if coverage >= 80:
            return COLORS["success"]
        elif coverage >= 60:
            return COLORS["warning"]
        else:
            return COLORS["error"]

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
```

**Integration with ReportGenerator:**

Update `report_generator.py` to include chart generation:

```python
def generate_run_report(
    self,
    run_id: str,
    output_path: Path,
    include_charts: bool = True,
    overwrite: bool = True
) -> Path:
    """Generate HTML report with optional charts."""

    # Load run data
    run_data = self._load_run_data(run_id)

    # Generate charts if requested
    charts = {}
    if include_charts:
        chart_gen = ChartGenerator()

        # Performance charts
        if run_data.performance:
            charts["response_time"] = chart_gen.generate_performance_timeline(...)
            charts["api_calls"] = chart_gen.generate_api_calls_bar_chart(...)

        # Quality charts
        if run_data.quality:
            charts["test_coverage"] = chart_gen.generate_test_coverage_gauge(...)
            charts["quality_radar"] = chart_gen.generate_quality_radar(...)

        # Workflow charts
        if run_data.workflow:
            charts["phase_durations"] = chart_gen.generate_phase_duration_chart(...)

    # Render template with charts
    template = self.env.get_template("run_report.html.j2")
    html = template.render(
        run=run_data.run,
        performance=run_data.performance,
        quality=run_data.quality,
        workflow=run_data.workflow,
        charts=charts,  # Pass charts to template
        ...
    )

    # Write to file
    self._write_report(html, output_path, overwrite)
    return output_path
```

---

## Testing Strategy

### Unit Tests
- Each chart generation method tested
- Base64 encoding works correctly
- Color schemes consistent
- Chart styling applies correctly
- Error handling for invalid data
- Handles empty/missing data

### Integration Tests
- Charts embedded in HTML reports
- Charts display correctly in browser
- Charts are high-resolution
- Multiple charts in same report work
- Chart generation doesn't slow report generation significantly

### Visual Tests
- Manual review of all chart types
- Verify colors and styling
- Check readability and clarity
- Test with different data ranges

### Performance Tests
- Chart generation time < 1 second per chart
- Memory usage reasonable for multiple charts
- No memory leaks

### Test Coverage Goal
- 90%+ for ChartGenerator class
- All chart types tested
- All error paths tested

---

## Dependencies

### Before This Story
- Story 5.1: Report Templates (chart placeholders in templates)
- Story 5.2: HTML Report Generator (integration point)

### Blocks Other Stories
- Story 5.4: Comparison Report (uses comparison charts)
- Story 5.5: Trend Analysis (uses timeline charts)

### External Dependencies
- matplotlib (add to dependencies)
- numpy (matplotlib dependency)

**Update `pyproject.toml`:**
```toml
dependencies = [
    ...
    "matplotlib>=3.7.0",
    "numpy>=1.24.0",
]
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] ChartGenerator class implemented
- [ ] All chart types working
- [ ] Charts embedded in HTML reports
- [ ] Error handling comprehensive
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing (90%+ coverage)
- [ ] Integration tests passing
- [ ] Visual review completed
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Committed to feature branch

---

## Notes

**Design Decisions:**
- Use matplotlib (widely used, flexible, no external dependencies)
- Generate PNG images (best compatibility)
- Embed as base64 (single-file HTML reports)
- Non-interactive charts (static reports)
- Consistent color scheme across all charts

**Performance Considerations:**
- Use 'Agg' backend (non-interactive, faster)
- Close figures after generation (prevent memory leaks)
- Cache chart images if regenerating same report
- Consider lazy loading for many charts

**Accessibility:**
- High contrast colors
- Large, readable fonts
- Alt text in HTML templates
- Text fallbacks when charts fail

**Future Enhancements:**
- Interactive charts (using Plotly)
- More chart types (sunburst, treemap, etc.)
- Custom color themes
- Animation for time-series data
- Export charts separately (SVG, PDF)

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: ReportGenerator component
- Matplotlib Documentation: https://matplotlib.org/
- Chart.js (alternative): https://www.chartjs.org/
