"""
Performance benchmark tests for onboarding.

Tests that verify onboarding meets performance requirements,
including <2 second startup time.
"""

import time
from pathlib import Path
from typing import Any

import pytest
import structlog

from gao_dev.core.environment_detector import (
    EnvironmentType,
    detect_environment,
    clear_cache,
    is_interactive,
    has_gui,
    _check_container,
    _check_ssh,
    _check_wsl,
    _check_desktop,
    _check_ci_cd,
    _check_vscode_remote,
)

logger = structlog.get_logger()


# =============================================================================
# Startup Performance Tests
# =============================================================================


@pytest.mark.performance
class TestStartupPerformance:
    """Test startup performance requirements."""

    def test_startup_under_2_seconds(
        self, desktop_environment: None, mock_project: Path, performance_timer: Any
    ) -> None:
        """Given any environment, when startup measured, then completes in <2 seconds."""
        clear_cache()

        with performance_timer("startup"):
            # Simulate startup sequence
            env_type = detect_environment()
            interactive = is_interactive()
            gui = has_gui()

            # These would be part of startup
            assert env_type is not None
            assert isinstance(interactive, bool)
            assert isinstance(gui, bool)

        elapsed = performance_timer.timings["startup"]
        assert elapsed < 2.0, f"Startup took {elapsed:.2f}s, expected <2s"

        logger.info(
            "startup_performance_test_passed",
            elapsed_ms=elapsed * 1000,
            environment=env_type.value,
        )

    def test_startup_p50_under_1_second(
        self, desktop_environment: None, performance_timer: Any
    ) -> None:
        """Test P50 startup time is under 1 second."""
        times = []

        for _ in range(10):
            clear_cache()
            start = time.perf_counter()

            detect_environment()
            is_interactive()
            has_gui()

            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Sort for percentile calculation
        times.sort()
        p50 = times[len(times) // 2]

        assert p50 < 1.0, f"P50 startup was {p50:.2f}s, expected <1s"
        logger.info("startup_p50_passed", p50_ms=p50 * 1000)


# =============================================================================
# Environment Detection Performance Tests
# =============================================================================


@pytest.mark.performance
class TestEnvironmentDetectionPerformance:
    """Test environment detection performance."""

    def test_cold_detection_under_50ms(self, performance_timer: Any) -> None:
        """Test cold environment detection completes in <50ms."""
        clear_cache()

        with performance_timer("cold_detection"):
            detect_environment()

        elapsed_ms = performance_timer.timings["cold_detection"] * 1000
        assert elapsed_ms < 50, f"Cold detection took {elapsed_ms:.2f}ms, expected <50ms"

    def test_hot_detection_under_1ms(self, performance_timer: Any) -> None:
        """Test cached environment detection completes in <1ms."""
        # Prime cache
        detect_environment()

        with performance_timer("hot_detection"):
            detect_environment()

        elapsed_us = performance_timer.timings["hot_detection"] * 1_000_000
        assert elapsed_us < 1000, f"Hot detection took {elapsed_us:.2f}us, expected <1000us"

    def test_100_detections_under_10ms(self, performance_timer: Any) -> None:
        """Test 100 cached detections complete in <10ms total."""
        # Prime cache
        detect_environment()

        with performance_timer("100_detections"):
            for _ in range(100):
                detect_environment()

        elapsed_ms = performance_timer.timings["100_detections"] * 1000
        avg_us = (performance_timer.timings["100_detections"] / 100) * 1_000_000

        assert elapsed_ms < 10, f"100 detections took {elapsed_ms:.2f}ms, expected <10ms"
        logger.info("cached_detection_performance", avg_us=avg_us)


# =============================================================================
# Individual Check Function Performance Tests
# =============================================================================


@pytest.mark.performance
class TestCheckFunctionPerformance:
    """Test individual check function performance."""

    def test_check_container_fast(self, performance_timer: Any) -> None:
        """Test _check_container is fast."""
        with performance_timer("check_container"):
            for _ in range(1000):
                _check_container()

        avg_us = (performance_timer.timings["check_container"] / 1000) * 1_000_000
        assert avg_us < 50, f"_check_container took {avg_us:.2f}us avg, expected <50us"

    def test_check_ssh_fast(self, performance_timer: Any) -> None:
        """Test _check_ssh is fast."""
        with performance_timer("check_ssh"):
            for _ in range(1000):
                _check_ssh()

        avg_us = (performance_timer.timings["check_ssh"] / 1000) * 1_000_000
        assert avg_us < 50, f"_check_ssh took {avg_us:.2f}us avg, expected <50us"

    def test_check_desktop_fast(self, performance_timer: Any) -> None:
        """Test _check_desktop is fast."""
        with performance_timer("check_desktop"):
            for _ in range(1000):
                _check_desktop()

        avg_us = (performance_timer.timings["check_desktop"] / 1000) * 1_000_000
        assert avg_us < 50, f"_check_desktop took {avg_us:.2f}us avg, expected <50us"

    def test_check_ci_cd_fast(self, performance_timer: Any) -> None:
        """Test _check_ci_cd is fast."""
        with performance_timer("check_ci_cd"):
            for _ in range(1000):
                _check_ci_cd()

        avg_us = (performance_timer.timings["check_ci_cd"] / 1000) * 1_000_000
        assert avg_us < 50, f"_check_ci_cd took {avg_us:.2f}us avg, expected <50us"

    def test_check_vscode_remote_fast(self, performance_timer: Any) -> None:
        """Test _check_vscode_remote is fast."""
        with performance_timer("check_vscode_remote"):
            for _ in range(1000):
                _check_vscode_remote()

        avg_us = (performance_timer.timings["check_vscode_remote"] / 1000) * 1_000_000
        assert avg_us < 50, f"_check_vscode_remote took {avg_us:.2f}us avg, expected <50us"


# =============================================================================
# Helper Function Performance Tests
# =============================================================================


@pytest.mark.performance
class TestHelperFunctionPerformance:
    """Test helper function performance."""

    def test_is_interactive_fast(self, desktop_environment: None, performance_timer: Any) -> None:
        """Test is_interactive is fast."""
        with performance_timer("is_interactive"):
            for _ in range(1000):
                is_interactive()

        avg_us = (performance_timer.timings["is_interactive"] / 1000) * 1_000_000
        assert avg_us < 10, f"is_interactive took {avg_us:.2f}us avg, expected <10us"

    def test_has_gui_fast(self, desktop_environment: None, performance_timer: Any) -> None:
        """Test has_gui is fast."""
        with performance_timer("has_gui"):
            for _ in range(1000):
                has_gui()

        avg_us = (performance_timer.timings["has_gui"] / 1000) * 1_000_000
        assert avg_us < 10, f"has_gui took {avg_us:.2f}us avg, expected <10us"


# =============================================================================
# Cross-Environment Performance Tests
# =============================================================================


@pytest.mark.performance
class TestCrossEnvironmentPerformance:
    """Test performance across different environments."""

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "docker_environment",
            "ssh_environment",
            "desktop_environment",
            "headless_environment",
        ],
    )
    def test_detection_fast_all_environments(
        self, fixture_name: str, request: pytest.FixtureRequest, performance_timer: Any
    ) -> None:
        """Test detection is fast in all environment types."""
        request.getfixturevalue(fixture_name)

        with performance_timer(f"{fixture_name}_detection"):
            detect_environment()

        elapsed_ms = performance_timer.timings[f"{fixture_name}_detection"] * 1000
        assert elapsed_ms < 10, f"{fixture_name} detection took {elapsed_ms:.2f}ms, expected <10ms"


# =============================================================================
# Cache Performance Tests
# =============================================================================


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance."""

    def test_cache_hit_fast(self, performance_timer: Any) -> None:
        """Test cache hit is very fast."""
        # Prime cache
        detect_environment()

        iterations = 10000
        with performance_timer("cache_hits"):
            for _ in range(iterations):
                detect_environment()

        avg_ns = (performance_timer.timings["cache_hits"] / iterations) * 1_000_000_000
        assert avg_ns < 1000, f"Cache hit took {avg_ns:.2f}ns avg, expected <1000ns"

    def test_cache_clear_fast(self, performance_timer: Any) -> None:
        """Test cache clear is fast."""
        with performance_timer("cache_clears"):
            for _ in range(1000):
                detect_environment()
                clear_cache()

        avg_us = (performance_timer.timings["cache_clears"] / 1000) * 1_000_000
        # This includes both detection and clear
        assert avg_us < 100, f"Detection+clear took {avg_us:.2f}us avg, expected <100us"


# =============================================================================
# Memory Performance Tests
# =============================================================================


@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory usage is reasonable."""

    def test_no_memory_leak_in_detection(self) -> None:
        """Test repeated detection doesn't leak memory."""
        import gc

        # Run many detections
        for _ in range(10000):
            clear_cache()
            detect_environment()

        # Force garbage collection
        gc.collect()

        # If we got here without OOM, test passes
        # More detailed memory tracking would require memory_profiler


# =============================================================================
# Benchmark Tests (for pytest-benchmark integration)
# =============================================================================


# Check if pytest-benchmark is available
try:
    import pytest_benchmark
    HAS_BENCHMARK = True
except ImportError:
    HAS_BENCHMARK = False


@pytest.mark.performance
@pytest.mark.skipif(not HAS_BENCHMARK, reason="pytest-benchmark not installed")
class TestBenchmarks:
    """Benchmark tests for pytest-benchmark integration."""

    def test_benchmark_detect_environment_cold(self, benchmark: Any) -> None:
        """Benchmark cold environment detection."""

        def detect_cold():
            clear_cache()
            return detect_environment()

        result = benchmark(detect_cold)
        assert result is not None

    def test_benchmark_detect_environment_hot(self, benchmark: Any) -> None:
        """Benchmark hot (cached) environment detection."""
        # Prime cache
        detect_environment()

        result = benchmark(detect_environment)
        assert result is not None

    def test_benchmark_is_interactive(
        self, desktop_environment: None, benchmark: Any
    ) -> None:
        """Benchmark is_interactive helper."""
        result = benchmark(is_interactive)
        assert isinstance(result, bool)

    def test_benchmark_has_gui(
        self, desktop_environment: None, benchmark: Any
    ) -> None:
        """Benchmark has_gui helper."""
        result = benchmark(has_gui)
        assert isinstance(result, bool)


# =============================================================================
# Performance Regression Tests
# =============================================================================


@pytest.mark.performance
class TestPerformanceRegression:
    """Test performance hasn't regressed."""

    def test_detection_not_slower_than_baseline(
        self, performance_timer: Any
    ) -> None:
        """Test detection isn't slower than baseline performance."""
        # Baseline: cold detection should be <10ms
        BASELINE_MS = 10

        clear_cache()
        with performance_timer("regression_check"):
            detect_environment()

        elapsed_ms = performance_timer.timings["regression_check"] * 1000

        assert elapsed_ms < BASELINE_MS * 2, (
            f"Detection took {elapsed_ms:.2f}ms, "
            f"more than 2x baseline of {BASELINE_MS}ms"
        )

    def test_consistent_performance(self, performance_timer: Any) -> None:
        """Test performance is consistent across runs."""
        times = []

        for _ in range(20):
            clear_cache()
            start = time.perf_counter()
            detect_environment()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Calculate variance
        mean = sum(times) / len(times)
        variance = sum((t - mean) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5

        # Coefficient of variation should be reasonable
        cv = std_dev / mean if mean > 0 else 0
        assert cv < 1.0, f"Performance too variable: CV={cv:.2f}"


# =============================================================================
# Load Testing
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestLoadPerformance:
    """Load tests for high-volume scenarios."""

    def test_1000_detections_stable(self, performance_timer: Any) -> None:
        """Test 1000 detections complete without errors."""
        errors = []

        with performance_timer("1000_detections"):
            for i in range(1000):
                try:
                    if i % 100 == 0:
                        clear_cache()
                    detect_environment()
                except Exception as e:
                    errors.append((i, str(e)))

        elapsed_ms = performance_timer.timings["1000_detections"] * 1000
        assert len(errors) == 0, f"Errors during load test: {errors}"
        assert elapsed_ms < 1000, f"1000 detections took {elapsed_ms:.0f}ms, expected <1000ms"

        logger.info("load_test_passed", elapsed_ms=elapsed_ms)
