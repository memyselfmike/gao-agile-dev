"""Tests for chart generation."""

import pytest
from datetime import datetime
from pathlib import Path

from gao_dev.sandbox.reporting.chart_generator import (
    ChartGenerator,
    ChartGeneratorError,
)


class TestChartGenerator:
    """Test chart generation functionality."""

    def test_initialization(self):
        """Test chart generator initialization."""
        generator = ChartGenerator()
        assert generator.dpi == 300
        assert generator.figsize == (10, 6)

    def test_initialization_custom_params(self):
        """Test chart generator with custom parameters."""
        generator = ChartGenerator(dpi=150, figsize=(8, 4))
        assert generator.dpi == 150
        assert generator.figsize == (8, 4)

    def test_generate_performance_timeline(self):
        """Test performance timeline chart generation."""
        generator = ChartGenerator()

        timestamps = [
            datetime(2025, 1, 1, 10, 0, i)
            for i in range(5)
        ]
        response_times = [100.0, 120.5, 95.2, 110.8, 105.3]

        result = generator.generate_performance_timeline(
            timestamps,
            response_times,
            "Test Timeline"
        )

        assert result.startswith("data:image/png;base64,")
        assert len(result) > 100  # Should have substantial data

    def test_generate_api_calls_bar_chart(self):
        """Test API calls bar chart generation."""
        generator = ChartGenerator()

        phase_names = ["Init", "Planning", "Implementation"]
        api_calls = [10, 25, 40]

        result = generator.generate_api_calls_bar_chart(
            phase_names,
            api_calls,
            "API Calls Test"
        )

        assert result.startswith("data:image/png;base64,")

    def test_generate_test_coverage_gauge(self):
        """Test coverage gauge chart generation."""
        generator = ChartGenerator()

        result = generator.generate_test_coverage_gauge(85.5)

        assert result.startswith("data:image/png;base64,")

    def test_generate_quality_radar(self):
        """Test quality radar chart generation."""
        generator = ChartGenerator()

        metrics = {
            "Coverage": 85.0,
            "Complexity": 70.0,
            "Maintainability": 90.0,
            "Documentation": 80.0,
        }

        result = generator.generate_quality_radar(metrics)

        assert result.startswith("data:image/png;base64,")

    def test_generate_phase_duration_chart(self):
        """Test phase duration chart generation."""
        generator = ChartGenerator()

        phase_names = ["Analysis", "Design", "Implementation", "Testing"]
        durations = [300.0, 600.0, 1800.0, 900.0]

        result = generator.generate_phase_duration_chart(
            phase_names,
            durations
        )

        assert result.startswith("data:image/png;base64,")

    def test_generate_comparison_bar_chart(self):
        """Test comparison bar chart generation."""
        generator = ChartGenerator()

        metric_names = ["Response Time", "API Calls", "Tokens"]
        run1_values = [100.0, 25.0, 5000.0]
        run2_values = [95.0, 20.0, 4500.0]

        result = generator.generate_comparison_bar_chart(
            metric_names,
            run1_values,
            run2_values,
            "Run 1",
            "Run 2"
        )

        assert result.startswith("data:image/png;base64,")

    def test_format_duration(self):
        """Test duration formatting."""
        assert ChartGenerator._format_duration(30.5) == "30.5s"
        assert ChartGenerator._format_duration(90.0) == "1.5m"
        assert ChartGenerator._format_duration(3600.0) == "1.0h"

    def test_get_coverage_color(self):
        """Test coverage color selection."""
        from gao_dev.sandbox.reporting.chart_generator import COLORS

        assert ChartGenerator._get_coverage_color(85.0) == COLORS["success"]
        assert ChartGenerator._get_coverage_color(65.0) == COLORS["warning"]
        assert ChartGenerator._get_coverage_color(45.0) == COLORS["error"]

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        generator = ChartGenerator()

        # Should handle gracefully or raise appropriate error
        try:
            result = generator.generate_api_calls_bar_chart([], [])
            # If it succeeds, it should still return valid base64
            assert result.startswith("data:image/png;base64,")
        except (ChartGeneratorError, ValueError):
            # Or it should raise a clear error
            pass
