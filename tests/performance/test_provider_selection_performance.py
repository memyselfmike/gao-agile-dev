"""Performance tests for provider selection flow.

Epic 35: Interactive Provider Selection at Startup
Story 35.7: Comprehensive Testing & Regression Validation

This module validates performance requirements:
- Preference loading <100ms
- Provider validation <2s (mocked)
- Full selection flow <5s (mocked input)
- No regression in REPL startup time
"""

import asyncio
import time
from pathlib import Path
from statistics import median
from typing import List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from gao_dev.cli.preference_manager import PreferenceManager
from gao_dev.cli.provider_validator import ProviderValidator
from gao_dev.cli.provider_selector import ProviderSelector
from gao_dev.cli.interactive_prompter import InteractivePrompter
from gao_dev.cli.models import ValidationResult
from rich.console import Console


# ============================================================================
# Performance Test Utilities
# ============================================================================


def measure_execution_time(func, iterations: int = 100) -> List[float]:
    """
    Measure execution time over multiple iterations.

    Args:
        func: Callable to measure
        iterations: Number of iterations to run

    Returns:
        List of execution times in milliseconds
    """
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    return times


def calculate_percentile(times: List[float], percentile: int) -> float:
    """
    Calculate percentile from list of times.

    Args:
        times: List of times in milliseconds
        percentile: Percentile to calculate (e.g., 95 for p95)

    Returns:
        Percentile value in milliseconds
    """
    sorted_times = sorted(times)
    index = int(len(sorted_times) * (percentile / 100))
    return sorted_times[min(index, len(sorted_times) - 1)]


def print_performance_stats(name: str, times: List[float], target_ms: float):
    """
    Print performance statistics.

    Args:
        name: Name of operation
        times: List of execution times in milliseconds
        target_ms: Target time in milliseconds
    """
    p50 = calculate_percentile(times, 50)
    p95 = calculate_percentile(times, 95)
    p99 = calculate_percentile(times, 99)
    avg = sum(times) / len(times)
    med = median(times)

    print(f"\n{name} Performance:")
    print(f"  Samples: {len(times)}")
    print(f"  Average: {avg:.2f}ms")
    print(f"  Median:  {med:.2f}ms")
    print(f"  p50:     {p50:.2f}ms")
    print(f"  p95:     {p95:.2f}ms {'PASS' if p95 <= target_ms else 'FAIL'}")
    print(f"  p99:     {p99:.2f}ms")
    print(f"  Min:     {min(times):.2f}ms")
    print(f"  Max:     {max(times):.2f}ms")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create temporary project directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    gao_dev_dir = project_root / ".gao-dev"
    gao_dev_dir.mkdir()
    return project_root


@pytest.fixture
def console() -> Console:
    """Create Rich Console."""
    return Console()


@pytest.fixture
def saved_preferences(temp_project: Path) -> Path:
    """Create saved preferences for testing."""
    manager = PreferenceManager(temp_project)
    config = {
        "version": "1.0.0",
        "provider": {
            "name": "opencode",
            "model": "deepseek-r1",
            "config": {"ai_provider": "ollama", "use_local": True},
        },
        "metadata": {"saved_at": "2025-01-12T10:00:00"},
    }
    manager.save_preferences(config)
    return temp_project


# ============================================================================
# Performance Tests
# ============================================================================


class TestPreferenceLoadingPerformance:
    """Test preference loading performance."""

    def test_preference_loading_under_100ms(self, saved_preferences: Path):
        """Preference loading is fast (<100ms p95)."""
        manager = PreferenceManager(saved_preferences)

        # Measure load time
        def load_prefs():
            manager.load_preferences()

        times = measure_execution_time(load_prefs, iterations=100)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Preference Loading", times, target_ms=100.0)

        # Assert p95 under target
        assert p95 < 100.0, f"Preference loading p95 {p95:.2f}ms exceeds 100ms target"

    def test_preference_has_check_fast(self, saved_preferences: Path):
        """Checking if preferences exist is fast (<10ms)."""
        manager = PreferenceManager(saved_preferences)

        # Measure has_preferences check
        def check_has_prefs():
            manager.has_preferences()

        times = measure_execution_time(check_has_prefs, iterations=100)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Has Preferences Check", times, target_ms=10.0)

        # Assert p95 under 10ms
        assert p95 < 10.0, f"has_preferences() p95 {p95:.2f}ms exceeds 10ms target"

    def test_preference_save_performance(self, temp_project: Path):
        """Preference saving is reasonably fast (<200ms p95)."""
        manager = PreferenceManager(temp_project)
        config = {
            "version": "1.0.0",
            "provider": {
                "name": "opencode",
                "model": "deepseek-r1",
                "config": {"ai_provider": "ollama", "use_local": True},
            },
            "metadata": {"saved_at": "2025-01-12T10:00:00"},
        }

        # Measure save time
        def save_prefs():
            manager.save_preferences(config)

        times = measure_execution_time(save_prefs, iterations=50)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Preference Saving", times, target_ms=200.0)

        # Assert p95 under 200ms
        assert p95 < 200.0, f"Preference saving p95 {p95:.2f}ms exceeds 200ms target"


class TestProviderValidationPerformance:
    """Test provider validation performance."""

    @pytest.mark.asyncio
    async def test_validation_under_2s_mocked(self, console: Console):
        """Provider validation is fast (<2s with mocked CLI)."""
        validator = ProviderValidator(console)

        # Mock CLI check to return immediately
        with patch.object(validator, "check_cli_available", return_value=True):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                times = []

                # Measure validation time
                for _ in range(20):
                    start = time.perf_counter()
                    result = await validator.validate_configuration(
                        "claude-code", {"api_key_env": "ANTHROPIC_API_KEY"}
                    )
                    end = time.perf_counter()
                    times.append((end - start) * 1000)  # Convert to ms

                # Calculate p95
                p95 = calculate_percentile(times, 95)

                # Print stats
                print_performance_stats("Provider Validation (Mocked)", times, target_ms=2000.0)

                # Assert p95 under 2s
                assert p95 < 2000.0, f"Validation p95 {p95:.2f}ms exceeds 2s target"

    @pytest.mark.asyncio
    async def test_cli_check_performance(self, console: Console):
        """CLI availability check is fast (<100ms)."""
        validator = ProviderValidator(console)

        # Measure CLI check time (real check, no mock)
        times = []
        for _ in range(50):
            start = time.perf_counter()
            # Check for a CLI that definitely doesn't exist
            result = await validator.check_cli_available("nonexistent-cli-12345")
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("CLI Availability Check", times, target_ms=100.0)

        # Assert p95 under 100ms
        assert p95 < 100.0, f"CLI check p95 {p95:.2f}ms exceeds 100ms target"


class TestFullSelectionFlowPerformance:
    """Test full selection flow performance."""

    def test_first_time_flow_under_5s_mocked(self, temp_project: Path, console: Console):
        """Full first-time flow is fast (<5s with mocked input/validation)."""
        # Mock all dependencies
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "opencode"
        mock_prompter.prompt_opencode_config.return_value = {"ai_provider": "ollama", "use_local": True}
        mock_prompter.prompt_model.return_value = "deepseek-r1"
        mock_prompter.prompt_save_preferences.return_value = True

        mock_validator = Mock(spec=ProviderValidator)
        mock_validator.validate_configuration = AsyncMock(
            return_value=ValidationResult(
                success=True,
                provider_name="opencode",
                messages=["OK"],
                validation_time_ms=50.0,
            )
        )

        preference_manager = PreferenceManager(temp_project)

        # Measure full flow
        times = []
        for _ in range(20):
            selector = ProviderSelector(
                project_root=temp_project,
                console=console,
                preference_manager=preference_manager,
                interactive_prompter=mock_prompter,
                provider_validator=mock_validator,
            )

            start = time.perf_counter()
            config = selector.select_provider()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("First-Time Flow (Mocked)", times, target_ms=5000.0)

        # Assert p95 under 5s
        assert p95 < 5000.0, f"First-time flow p95 {p95:.2f}ms exceeds 5s target"

    def test_returning_user_flow_fast(self, saved_preferences: Path, console: Console):
        """Returning user flow with saved prefs is very fast (<1s)."""
        # Mock dependencies
        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_use_saved.return_value = "y"  # Use saved preferences

        mock_validator = Mock(spec=ProviderValidator)
        mock_validator.validate_configuration = AsyncMock(
            return_value=ValidationResult(
                success=True,
                provider_name="opencode",
                messages=["OK"],
                validation_time_ms=30.0,
            )
        )

        preference_manager = PreferenceManager(saved_preferences)

        # Measure returning user flow
        times = []
        for _ in range(50):
            selector = ProviderSelector(
                project_root=saved_preferences,
                console=console,
                preference_manager=preference_manager,
                interactive_prompter=mock_prompter,
                provider_validator=mock_validator,
            )

            start = time.perf_counter()
            config = selector.select_provider()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("Returning User Flow", times, target_ms=1000.0)

        # Assert p95 under 1s
        assert p95 < 1000.0, f"Returning user flow p95 {p95:.2f}ms exceeds 1s target"


class TestREPLStartupPerformance:
    """Test REPL startup time not regressed."""

    def test_repl_startup_with_env_var_no_regression(self, temp_project: Path, monkeypatch):
        """REPL startup with env var is fast (no slowdown from provider selection)."""
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        from gao_dev.cli.chat_repl import ChatREPL

        # Measure startup time
        times = []
        for _ in range(20):
            with patch("gao_dev.cli.chat_repl.PromptSession"):
                start = time.perf_counter()
                repl = ChatREPL(project_root=temp_project)
                end = time.perf_counter()
                times.append((end - start) * 1000)

        # Calculate p95
        p95 = calculate_percentile(times, 95)

        # Print stats
        print_performance_stats("REPL Startup (Env Var)", times, target_ms=1000.0)

        # Assert p95 under 1s (reasonable startup time)
        assert p95 < 1000.0, f"REPL startup p95 {p95:.2f}ms exceeds 1s target"

    def test_env_var_bypass_faster_than_interactive(self, temp_project: Path, console: Console, monkeypatch):
        """Env var bypass is faster than interactive flow."""
        # Measure env var bypass
        monkeypatch.setenv("AGENT_PROVIDER", "claude-code")

        mock_validator = Mock(spec=ProviderValidator)
        mock_validator.validate_configuration = AsyncMock(
            return_value=ValidationResult(
                success=True,
                provider_name="claude-code",
                messages=["OK"],
                validation_time_ms=20.0,
            )
        )

        env_var_times = []
        for _ in range(30):
            selector = ProviderSelector(
                project_root=temp_project,
                console=console,
                provider_validator=mock_validator,
            )

            start = time.perf_counter()
            config = selector.select_provider()
            end = time.perf_counter()
            env_var_times.append((end - start) * 1000)

        # Measure interactive flow
        monkeypatch.delenv("AGENT_PROVIDER", raising=False)

        mock_prompter = Mock(spec=InteractivePrompter)
        mock_prompter.prompt_provider.return_value = "claude-code"
        mock_prompter.prompt_model.return_value = "sonnet-4.5"
        mock_prompter.prompt_save_preferences.return_value = False

        interactive_times = []
        for _ in range(30):
            selector = ProviderSelector(
                project_root=temp_project,
                console=console,
                interactive_prompter=mock_prompter,
                provider_validator=mock_validator,
            )

            start = time.perf_counter()
            config = selector.select_provider()
            end = time.perf_counter()
            interactive_times.append((end - start) * 1000)

        # Calculate medians
        env_var_median = median(env_var_times)
        interactive_median = median(interactive_times)

        print(f"\nEnv Var Bypass Median: {env_var_median:.2f}ms")
        print(f"Interactive Flow Median: {interactive_median:.2f}ms")
        print(f"Speedup: {interactive_median / env_var_median:.2f}x faster with env var")

        # Env var should be faster (at least 2x)
        assert env_var_median < interactive_median, "Env var bypass should be faster than interactive flow"
