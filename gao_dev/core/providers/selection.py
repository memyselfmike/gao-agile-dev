"""Provider selection strategies.

Strategies for automatically selecting the best provider based on
availability, performance, cost, or custom criteria.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import structlog

from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class IProviderSelectionStrategy(ABC):
    """
    Interface for provider selection strategies.

    Implementations decide which provider to use based on
    various criteria (availability, performance, cost, etc.).
    """

    @abstractmethod
    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """
        Select the best provider from available options.

        Args:
            available_providers: List of available providers
            model: Canonical model name
            context: Additional context for decision

        Returns:
            Selected provider, or None if none suitable

        Raises:
            ProviderSelectionError: If selection fails
        """
        pass


class ProviderSelectionError(Exception):
    """Raised when provider selection fails."""
    pass


class AutoDetectStrategy(IProviderSelectionStrategy):
    """
    Auto-detect strategy: Try providers in order until one works.

    Order:
    1. Claude Code CLI (if installed)
    2. OpenCode CLI (if installed)
    3. Direct API (if API key available)
    """

    def __init__(self, fallback_chain: Optional[List[str]] = None):
        """
        Initialize auto-detect strategy.

        Args:
            fallback_chain: Provider names in order of preference
        """
        self.fallback_chain = fallback_chain or [
            "claude-code",
            "opencode",
            "direct-api",
        ]

    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """Select first available provider from fallback chain."""
        logger.info(
            "auto_detect_selecting_provider",
            num_available=len(available_providers),
            fallback_chain=self.fallback_chain,
        )

        # Try each provider in fallback chain
        for provider_name in self.fallback_chain:
            # Check if provider available (match name or prefix)
            for provider in available_providers:
                # Try exact match or prefix match
                if provider.name == provider_name or provider.name.startswith(provider_name + "-"):
                    logger.info(
                        "auto_detect_selected_provider",
                        provider=provider.name,
                        reason="first_available_in_chain",
                    )
                    return provider

        logger.warning(
            "auto_detect_no_provider_found",
            fallback_chain=self.fallback_chain,
        )
        return None


class PerformanceBasedStrategy(IProviderSelectionStrategy):
    """
    Select provider based on historical performance.

    Tracks average execution time per provider and prefers faster ones.
    """

    def __init__(self, performance_tracker):
        """
        Initialize performance-based strategy.

        Args:
            performance_tracker: ProviderPerformanceTracker instance
        """
        self.performance_tracker = performance_tracker

    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """Select fastest provider based on historical data."""
        if not available_providers:
            return None

        # Get performance stats for each provider
        provider_scores = []
        for provider in available_providers:
            avg_time = self.performance_tracker.get_avg_execution_time(
                provider.name, model
            )
            provider_scores.append((provider, avg_time))

        # Sort by execution time (ascending)
        provider_scores.sort(key=lambda x: x[1])

        # Select fastest
        selected = provider_scores[0][0]
        avg_time = provider_scores[0][1]

        logger.info(
            "performance_based_selected_provider",
            provider=selected.name,
            avg_execution_time=avg_time,
            reason="fastest_historical_performance",
        )

        return selected


class CostBasedStrategy(IProviderSelectionStrategy):
    """
    Select provider based on cost.

    Prefers cheapest provider for given model.
    """

    # Token pricing (per 1M tokens)
    PRICING = {
        "claude-code": {
            "sonnet-4.5": {"input": 3.0, "output": 15.0},
            "opus-3": {"input": 15.0, "output": 75.0},
            "haiku-3": {"input": 0.25, "output": 1.25},
        },
        "opencode": {
            "sonnet-4.5": {"input": 3.0, "output": 15.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
        },
        "direct-api": {
            "sonnet-4.5": {"input": 3.0, "output": 15.0},
            "gpt-4": {"input": 30.0, "output": 60.0},
        },
    }

    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """Select cheapest provider for model."""
        if not available_providers:
            return None

        # Calculate cost for each provider
        provider_costs = []
        for provider in available_providers:
            # Get base provider name (handle both "claude-code" and "direct-api-anthropic")
            name_parts = provider.name.split("-")
            base_name = name_parts[0]

            # For direct-api providers, look at second part
            if base_name == "direct" and len(name_parts) > 2:
                base_name = "direct-api"

            if base_name not in self.PRICING:
                continue

            provider_pricing = self.PRICING.get(base_name, {})
            model_pricing = provider_pricing.get(model)
            if not model_pricing:
                continue

            # Estimate cost (assume 1000 input + 1000 output tokens)
            estimated_cost = (
                model_pricing["input"] * 0.001 +
                model_pricing["output"] * 0.001
            )
            provider_costs.append((provider, estimated_cost))

        if not provider_costs:
            # No pricing data, fall back to first
            return available_providers[0]

        # Sort by cost (ascending)
        provider_costs.sort(key=lambda x: x[1])

        # Select cheapest
        selected = provider_costs[0][0]
        cost = provider_costs[0][1]

        logger.info(
            "cost_based_selected_provider",
            provider=selected.name,
            estimated_cost=cost,
            reason="lowest_estimated_cost",
        )

        return selected


class AvailabilityBasedStrategy(IProviderSelectionStrategy):
    """
    Select provider based on availability/health.

    Checks provider health and skips unhealthy ones.
    """

    def __init__(self, health_checker):
        """
        Initialize availability-based strategy.

        Args:
            health_checker: ProviderHealthChecker instance
        """
        self.health_checker = health_checker

    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """Select first healthy provider."""
        for provider in available_providers:
            if self.health_checker.is_healthy(provider.name):
                logger.info(
                    "availability_based_selected_provider",
                    provider=provider.name,
                    reason="provider_healthy",
                )
                return provider

        logger.warning(
            "availability_based_no_healthy_provider",
            num_checked=len(available_providers),
        )
        return None


class CompositeStrategy(IProviderSelectionStrategy):
    """
    Composite strategy: Combines multiple strategies with weights.

    Example: 60% performance, 30% cost, 10% availability
    """

    def __init__(
        self,
        strategies: List[tuple[IProviderSelectionStrategy, float]]
    ):
        """
        Initialize composite strategy.

        Args:
            strategies: List of (strategy, weight) tuples
        """
        self.strategies = strategies

        # Normalize weights
        total_weight = sum(w for _, w in strategies)
        self.strategies = [
            (s, w / total_weight) for s, w in strategies
        ]

    def select_provider(
        self,
        available_providers: List[IAgentProvider],
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IAgentProvider]:
        """Select provider based on weighted strategy scores."""
        if not available_providers:
            return None

        # Score each provider
        provider_scores: Dict[str, float] = {}

        for provider in available_providers:
            provider_scores[provider.name] = 0.0

        # Apply each strategy
        for strategy, weight in self.strategies:
            selected = strategy.select_provider(
                available_providers, model, context
            )
            if selected:
                provider_scores[selected.name] += weight

        # Select provider with highest score
        best_provider_name = max(provider_scores, key=provider_scores.get)  # type: ignore
        best_provider = next(
            p for p in available_providers
            if p.name == best_provider_name
        )

        logger.info(
            "composite_selected_provider",
            provider=best_provider.name,
            score=provider_scores[best_provider_name],
            all_scores=provider_scores,
            reason="highest_weighted_score",
        )

        return best_provider
