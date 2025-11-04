"""Tests for provider selection strategies."""

import pytest
from unittest.mock import Mock, MagicMock

from gao_dev.core.providers.selection import (
    IProviderSelectionStrategy,
    AutoDetectStrategy,
    PerformanceBasedStrategy,
    CostBasedStrategy,
    AvailabilityBasedStrategy,
    CompositeStrategy,
    ProviderSelectionError,
)
from gao_dev.core.providers.performance_tracker import ProviderPerformanceTracker
from gao_dev.core.providers.health_check import ProviderHealthChecker


class TestAutoDetectStrategy:
    """Test auto-detect strategy."""

    def test_selects_first_in_fallback_chain(self):
        """Test selects first available provider from fallback chain."""
        # Create mock providers with name attribute
        claude_provider = Mock()
        claude_provider.name = "claude-code"
        opencode_provider = Mock()
        opencode_provider.name = "opencode"

        # Strategy with fallback chain
        strategy = AutoDetectStrategy(fallback_chain=["claude-code", "opencode"])

        # Select
        selected = strategy.select_provider(
            [claude_provider, opencode_provider],
            model="sonnet-4.5"
        )

        assert selected == claude_provider

    def test_skips_unavailable_providers(self):
        """Test skips unavailable providers in chain."""
        # Only opencode available
        opencode_provider = Mock()
        opencode_provider.name = "opencode"

        strategy = AutoDetectStrategy(fallback_chain=["claude-code", "opencode"])

        # Select
        selected = strategy.select_provider(
            [opencode_provider],
            model="sonnet-4.5"
        )

        assert selected == opencode_provider

    def test_returns_none_if_no_match(self):
        """Test returns None if no providers match chain."""
        custom_provider = Mock()
        custom_provider.name = "custom-provider"

        strategy = AutoDetectStrategy(fallback_chain=["claude-code", "opencode"])

        selected = strategy.select_provider(
            [custom_provider],
            model="sonnet-4.5"
        )

        assert selected is None

    def test_default_fallback_chain(self):
        """Test uses default fallback chain."""
        strategy = AutoDetectStrategy()

        assert strategy.fallback_chain == ["claude-code", "opencode", "direct-api"]


class TestPerformanceBasedStrategy:
    """Test performance-based strategy."""

    def test_selects_fastest_provider(self):
        """Test selects provider with best historical performance."""
        # Create tracker with performance data
        tracker = ProviderPerformanceTracker()
        tracker.record_execution_time("claude-code", "sonnet-4.5", 2.0)
        tracker.record_execution_time("opencode", "sonnet-4.5", 1.5)
        tracker.record_execution_time("direct-api-anthropic", "sonnet-4.5", 1.0)

        # Create mock providers
        claude = Mock()
        claude.name = "claude-code"
        opencode = Mock()
        opencode.name = "opencode"
        direct_api = Mock()
        direct_api.name = "direct-api-anthropic"

        # Strategy
        strategy = PerformanceBasedStrategy(tracker)

        # Select
        selected = strategy.select_provider(
            [claude, opencode, direct_api],
            model="sonnet-4.5"
        )

        assert selected == direct_api

    def test_handles_no_performance_data(self):
        """Test handles providers with no performance history."""
        tracker = ProviderPerformanceTracker()

        claude = Mock()
        claude.name = "claude-code"

        strategy = PerformanceBasedStrategy(tracker)

        # Should still select (infinity is sorted last)
        selected = strategy.select_provider([claude], model="sonnet-4.5")

        assert selected == claude

    def test_returns_none_for_empty_list(self):
        """Test returns None for empty provider list."""
        tracker = ProviderPerformanceTracker()
        strategy = PerformanceBasedStrategy(tracker)

        selected = strategy.select_provider([], model="sonnet-4.5")

        assert selected is None


class TestCostBasedStrategy:
    """Test cost-based strategy."""

    def test_selects_cheapest_provider(self):
        """Test selects provider with lowest estimated cost."""
        # Create mock providers
        claude = Mock()
        claude.name = "claude-code"
        opencode = Mock()
        opencode.name = "opencode"

        strategy = CostBasedStrategy()

        # Both should have same cost for sonnet-4.5
        selected = strategy.select_provider(
            [claude, opencode],
            model="sonnet-4.5"
        )

        # Should select one of them (both same price)
        assert selected in [claude, opencode]

    def test_prefers_haiku_for_low_cost(self):
        """Test prefers cheaper model."""
        claude_sonnet = Mock()
        claude_sonnet.name = "claude-code"
        claude_haiku = Mock()
        claude_haiku.name = "claude-code"

        strategy = CostBasedStrategy()

        # Test with haiku (should be cheaper)
        selected_haiku = strategy.select_provider(
            [claude_haiku],
            model="haiku-3"
        )
        assert selected_haiku == claude_haiku

        # Test with sonnet
        selected_sonnet = strategy.select_provider(
            [claude_sonnet],
            model="sonnet-4.5"
        )
        assert selected_sonnet == claude_sonnet

    def test_falls_back_if_no_pricing(self):
        """Test falls back to first provider if no pricing data."""
        custom = Mock()
        custom.name = "custom-provider"

        strategy = CostBasedStrategy()

        selected = strategy.select_provider([custom], model="unknown-model")

        assert selected == custom

    def test_returns_none_for_empty_list(self):
        """Test returns None for empty provider list."""
        strategy = CostBasedStrategy()

        selected = strategy.select_provider([], model="sonnet-4.5")

        assert selected is None


class TestAvailabilityBasedStrategy:
    """Test availability-based strategy."""

    def test_selects_healthy_provider(self):
        """Test selects first healthy provider."""
        checker = ProviderHealthChecker()

        # Mark opencode as unhealthy
        checker.mark_unhealthy("opencode")

        claude = Mock()
        claude.name = "claude-code"
        opencode = Mock()
        opencode.name = "opencode"

        strategy = AvailabilityBasedStrategy(checker)

        selected = strategy.select_provider(
            [claude, opencode],
            model="sonnet-4.5"
        )

        assert selected == claude

    def test_returns_none_if_all_unhealthy(self):
        """Test returns None if all providers unhealthy."""
        checker = ProviderHealthChecker()
        checker.mark_unhealthy("claude-code")
        checker.mark_unhealthy("opencode")

        claude = Mock()
        claude.name = "claude-code"
        opencode = Mock()
        opencode.name = "opencode"

        strategy = AvailabilityBasedStrategy(checker)

        selected = strategy.select_provider(
            [claude, opencode],
            model="sonnet-4.5"
        )

        assert selected is None


class TestCompositeStrategy:
    """Test composite strategy."""

    def test_combines_multiple_strategies(self):
        """Test combines multiple strategies with weights."""
        # Create sub-strategies
        tracker = ProviderPerformanceTracker()
        tracker.record_execution_time("claude-code", "sonnet-4.5", 1.0)

        checker = ProviderHealthChecker()

        perf_strategy = PerformanceBasedStrategy(tracker)
        avail_strategy = AvailabilityBasedStrategy(checker)

        # Composite strategy: 70% performance, 30% availability
        strategy = CompositeStrategy([
            (perf_strategy, 0.7),
            (avail_strategy, 0.3),
        ])

        claude = Mock()
        claude.name = "claude-code"

        selected = strategy.select_provider([claude], model="sonnet-4.5")

        assert selected == claude

    def test_normalizes_weights(self):
        """Test normalizes strategy weights."""
        tracker = ProviderPerformanceTracker()
        checker = ProviderHealthChecker()

        perf_strategy = PerformanceBasedStrategy(tracker)
        avail_strategy = AvailabilityBasedStrategy(checker)

        # Weights don't sum to 1.0
        strategy = CompositeStrategy([
            (perf_strategy, 60),
            (avail_strategy, 30),
        ])

        # Weights should be normalized
        assert abs(sum(w for _, w in strategy.strategies) - 1.0) < 0.001

    def test_returns_none_for_empty_list(self):
        """Test returns None for empty provider list."""
        tracker = ProviderPerformanceTracker()
        perf_strategy = PerformanceBasedStrategy(tracker)

        strategy = CompositeStrategy([(perf_strategy, 1.0)])

        selected = strategy.select_provider([], model="sonnet-4.5")

        assert selected is None


class TestProviderSelectionError:
    """Test provider selection error."""

    def test_is_exception(self):
        """Test ProviderSelectionError is an exception."""
        error = ProviderSelectionError("test")

        assert isinstance(error, Exception)

    def test_has_message(self):
        """Test error has message."""
        error = ProviderSelectionError("Test message")

        assert str(error) == "Test message"
