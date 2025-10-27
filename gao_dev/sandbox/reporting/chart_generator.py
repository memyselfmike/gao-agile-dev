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
import numpy as np
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
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except OSError:
            # Fallback if seaborn style not available
            plt.style.use('default')

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
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

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="timeline", error=str(e))
            raise ChartGeneratorError(f"Failed to generate timeline chart: {e}")

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
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

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="bar", error=str(e))
            raise ChartGeneratorError(f"Failed to generate bar chart: {e}")

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
            fig, ax = plt.subplots(figsize=(8, 4))

            # Create simple bar representation instead of polar
            color = self._get_coverage_color(coverage_percent)

            ax.barh(0, coverage_percent, height=0.5, color=color, alpha=0.8)
            ax.barh(0, 100 - coverage_percent, left=coverage_percent,
                   height=0.5, color='lightgray', alpha=0.3)

            # Center text
            ax.text(
                50, 0, f'{coverage_percent:.1f}%',
                ha='center', va='center',
                fontsize=24, fontweight='bold'
            )

            ax.set_xlim(0, 100)
            ax.set_ylim(-1, 1)
            ax.set_xticks([0, 25, 50, 75, 100])
            ax.set_yticks([])
            ax.set_xlabel("Coverage (%)", fontsize=11)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)

            plt.tight_layout()
            return self._figure_to_base64(fig)

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="gauge", error=str(e))
            raise ChartGeneratorError(f"Failed to generate gauge chart: {e}")

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

            categories = list(metrics.keys())
            values = list(metrics.values())

            # Number of variables
            N = len(categories)

            # Compute angle for each axis
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            values_plot = values + values[:1]  # Complete the circle
            angles_plot = angles + angles[:1]

            # Plot
            ax.plot(angles_plot, values_plot, 'o-', linewidth=2, color=COLORS["primary"])
            ax.fill(angles_plot, values_plot, alpha=0.25, color=COLORS["primary"])

            ax.set_xticks(angles)
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

            ax.grid(True)

            plt.tight_layout()
            return self._figure_to_base64(fig)

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="radar", error=str(e))
            raise ChartGeneratorError(f"Failed to generate radar chart: {e}")

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
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

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="horizontal_bar", error=str(e))
            raise ChartGeneratorError(f"Failed to generate phase duration chart: {e}")

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

        Raises:
            ChartGeneratorError: If chart generation fails
        """
        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            x = np.arange(len(metric_names))
            width = 0.35

            bars1 = ax.bar(
                x - width/2,
                run1_values,
                width,
                label=run1_label,
                color=COLORS["primary"],
                alpha=0.8,
            )
            bars2 = ax.bar(
                x + width/2,
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

        except Exception as e:
            logger.error("chart_generation_failed", chart_type="comparison", error=str(e))
            raise ChartGeneratorError(f"Failed to generate comparison chart: {e}")

    def _figure_to_base64(self, fig: Figure) -> str:
        """
        Convert matplotlib figure to base64-encoded PNG.

        Args:
            fig: Matplotlib figure

        Returns:
            Base64-encoded image string

        Raises:
            ChartGeneratorError: If conversion fails
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
        except Exception as e:
            logger.error("base64_conversion_failed", error=str(e))
            raise ChartGeneratorError(f"Failed to convert chart to base64: {e}")
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
