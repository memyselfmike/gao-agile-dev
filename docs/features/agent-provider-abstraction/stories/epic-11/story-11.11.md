# Story 11.11: Provider Selection Strategy

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P2 (Medium)
**Estimated Effort**: 8 story points
**Owner**: Winston (Architect) + Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.2 (ClaudeCodeProvider), Story 11.7 (OpenCodeProvider), Story 11.10 (DirectAPIProvider)

---

## User Story

**As a** GAO-Dev developer
**I want** the system to automatically select the best available provider
**So that** GAO-Dev works out-of-the-box and optimizes for performance, cost, and availability

---

## Acceptance Criteria

### AC1: Provider Selection Strategy Interface
- ✅ `IProviderSelectionStrategy` interface created
- ✅ Located in `gao_dev/core/providers/selection.py`
- ✅ Strategy pattern implementation
- ✅ Extensible for custom selection logic
- ✅ Type-safe

### AC2: Auto-Detection Strategy
- ✅ `AutoDetectStrategy` class implemented
- ✅ Detects available providers by checking:
  - CLI installation (claude-code, opencode)
  - API keys (direct-api)
  - Package installation
- ✅ Fallback chain support
- ✅ Caches detection results
- ✅ Logs detection decisions

### AC3: Performance-Based Strategy
- ✅ `PerformanceBasedStrategy` class implemented
- ✅ Selects provider based on historical performance
- ✅ Tracks average execution time per provider
- ✅ Prefers faster providers
- ✅ Falls back if preferred provider unavailable

### AC4: Cost-Based Strategy
- ✅ `CostBasedStrategy` class implemented
- ✅ Selects cheapest provider for given model
- ✅ Considers token pricing
- ✅ Configurable cost thresholds
- ✅ Falls back to next cheapest

### AC5: Availability-Based Strategy
- ✅ `AvailabilityBasedStrategy` class implemented
- ✅ Health checks for each provider
- ✅ Skips unhealthy providers
- ✅ Periodic re-checking
- ✅ Circuit breaker pattern

### AC6: Composite Strategy
- ✅ `CompositeStrategy` class implemented
- ✅ Combines multiple strategies
- ✅ Weighted decision making
- ✅ Example: 60% performance, 30% cost, 10% availability
- ✅ Configurable weights

### AC7: Provider Selector Service
- ✅ `ProviderSelector` service created
- ✅ Uses configured strategy
- ✅ Returns best provider instance
- ✅ Logs selection decision and reasoning
- ✅ Handles fallback chain

### AC8: Configuration Support
- ✅ Selection strategy configurable in `defaults.yaml`
- ✅ Per-agent strategy override
- ✅ Fallback chain configurable
- ✅ Strategy parameters configurable

### AC9: ProcessExecutor Integration
- ✅ `ProcessExecutor` uses `ProviderSelector`
- ✅ Auto-selection if no provider specified
- ✅ Backward compatible (explicit provider still works)
- ✅ Logs which provider was selected

### AC10: Testing
- ✅ Unit tests for each strategy
- ✅ Integration tests for selector
- ✅ Mock provider availability scenarios
- ✅ Test fallback behavior
- ✅ All tests pass

### AC11: Documentation
- ✅ Strategy pattern documented
- ✅ Configuration examples
- ✅ How to implement custom strategies
- ✅ Troubleshooting guide

---

## Technical Details

### File Structure
```
gao_dev/core/providers/
├── __init__.py                     # MODIFIED: Export selection classes
├── selection.py                    # NEW: Selection strategies
├── selector.py                     # NEW: Provider selector service
├── health_check.py                 # NEW: Provider health checking
└── performance_tracker.py          # NEW: Provider performance tracking

gao_dev/config/
└── defaults.yaml                   # MODIFIED: Add selection config

tests/core/providers/
├── test_selection_strategies.py    # NEW: Strategy tests
├── test_provider_selector.py       # NEW: Selector tests
└── test_health_check.py            # NEW: Health check tests
```

### Implementation Approach

#### Step 1: Create Strategy Interface

**File**: `gao_dev/core/providers/selection.py`

```python
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

        # Create mapping of name -> provider
        provider_map = {p.name: p for p in available_providers}

        # Try each provider in fallback chain
        for provider_name in self.fallback_chain:
            # Check if provider available
            matching_providers = [
                p for p in available_providers
                if p.name.startswith(provider_name)
            ]

            if matching_providers:
                selected = matching_providers[0]
                logger.info(
                    "auto_detect_selected_provider",
                    provider=selected.name,
                    reason="first_available_in_chain",
                )
                return selected

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
            # Get base provider name (without suffix)
            base_name = provider.name.split("-")[0]
            if base_name not in self.PRICING:
                continue

            model_pricing = self.PRICING[base_name].get(model)
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
```

#### Step 2: Create Provider Selector Service

**File**: `gao_dev/core/providers/selector.py`

```python
"""Provider selector service.

Main service for selecting providers based on configured strategy.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import structlog

from gao_dev.core.providers.base import IAgentProvider
from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.selection import (
    IProviderSelectionStrategy,
    AutoDetectStrategy,
    ProviderSelectionError,
)

logger = structlog.get_logger(__name__)


class ProviderSelector:
    """
    Service for selecting the best provider.

    Uses a configurable selection strategy to choose from available providers.
    """

    def __init__(
        self,
        factory: ProviderFactory,
        strategy: Optional[IProviderSelectionStrategy] = None,
    ):
        """
        Initialize provider selector.

        Args:
            factory: Provider factory for creating providers
            strategy: Selection strategy (defaults to AutoDetect)
        """
        self.factory = factory
        self.strategy = strategy or AutoDetectStrategy()

    def select_provider(
        self,
        model: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IAgentProvider:
        """
        Select the best provider for the given model.

        Args:
            model: Canonical model name
            context: Additional context for selection

        Returns:
            Selected provider instance

        Raises:
            ProviderSelectionError: If no suitable provider found
        """
        logger.info(
            "provider_selector_starting",
            model=model,
            strategy=self.strategy.__class__.__name__,
        )

        # Get all available providers
        available_providers = self._get_available_providers()

        if not available_providers:
            raise ProviderSelectionError(
                "No providers available. Install Claude Code, OpenCode, "
                "or set API keys for direct API access."
            )

        # Use strategy to select
        selected = self.strategy.select_provider(
            available_providers, model, context
        )

        if not selected:
            raise ProviderSelectionError(
                f"Strategy {self.strategy.__class__.__name__} "
                f"could not select a provider for model '{model}'"
            )

        logger.info(
            "provider_selector_selected",
            provider=selected.name,
            model=model,
            strategy=self.strategy.__class__.__name__,
        )

        return selected

    def _get_available_providers(self) -> List[IAgentProvider]:
        """
        Get list of available providers.

        Returns:
            List of available provider instances
        """
        available = []
        provider_names = self.factory.list_providers()

        for name in provider_names:
            try:
                # Try to create provider
                provider = self.factory.create_provider(name)

                # TODO: Could add validation here
                available.append(provider)

            except Exception as e:
                logger.debug(
                    "provider_not_available",
                    provider=name,
                    error=str(e),
                )

        return available
```

#### Step 3: Create Helper Services

**File**: `gao_dev/core/providers/performance_tracker.py`

```python
"""Provider performance tracking."""

from typing import Dict
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)


class ProviderPerformanceTracker:
    """Tracks performance metrics for each provider."""

    def __init__(self):
        """Initialize tracker."""
        # provider_name -> model -> list of execution times
        self._execution_times: Dict[str, Dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def record_execution_time(
        self, provider_name: str, model: str, execution_time: float
    ):
        """
        Record execution time for provider/model.

        Args:
            provider_name: Name of provider
            model: Model name
            execution_time: Execution time in seconds
        """
        self._execution_times[provider_name][model].append(execution_time)

        logger.debug(
            "performance_recorded",
            provider=provider_name,
            model=model,
            execution_time=execution_time,
        )

    def get_avg_execution_time(
        self, provider_name: str, model: str
    ) -> float:
        """
        Get average execution time for provider/model.

        Args:
            provider_name: Name of provider
            model: Model name

        Returns:
            Average execution time, or infinity if no data
        """
        times = self._execution_times.get(provider_name, {}).get(model, [])

        if not times:
            return float("inf")

        return sum(times) / len(times)
```

**File**: `gao_dev/core/providers/health_check.py`

```python
"""Provider health checking."""

import asyncio
from typing import Dict
from datetime import datetime, timedelta
import structlog

from gao_dev.core.providers.base import IAgentProvider

logger = structlog.get_logger(__name__)


class ProviderHealthChecker:
    """Checks and caches provider health status."""

    def __init__(self, cache_duration: int = 300):
        """
        Initialize health checker.

        Args:
            cache_duration: Cache duration in seconds (default 5 minutes)
        """
        self.cache_duration = cache_duration
        self._health_cache: Dict[str, tuple[bool, datetime]] = {}

    def is_healthy(self, provider_name: str) -> bool:
        """
        Check if provider is healthy.

        Args:
            provider_name: Name of provider

        Returns:
            True if healthy, False otherwise
        """
        # Check cache
        if provider_name in self._health_cache:
            is_healthy, checked_at = self._health_cache[provider_name]
            age = (datetime.now() - checked_at).total_seconds()

            if age < self.cache_duration:
                logger.debug(
                    "health_check_cache_hit",
                    provider=provider_name,
                    is_healthy=is_healthy,
                )
                return is_healthy

        # Cache miss or expired - always return True for now
        # TODO: Implement actual health check
        logger.debug(
            "health_check_cache_miss",
            provider=provider_name,
        )

        # Update cache
        self._health_cache[provider_name] = (True, datetime.now())
        return True

    async def check_provider_health(
        self, provider: IAgentProvider
    ) -> bool:
        """
        Perform actual health check on provider.

        Args:
            provider: Provider instance

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Use provider's validate method
            is_healthy = await provider.validate()

            # Update cache
            self._health_cache[provider.name] = (is_healthy, datetime.now())

            logger.info(
                "health_check_completed",
                provider=provider.name,
                is_healthy=is_healthy,
            )

            return is_healthy

        except Exception as e:
            logger.error(
                "health_check_failed",
                provider=provider.name,
                error=str(e),
            )

            # Update cache as unhealthy
            self._health_cache[provider.name] = (False, datetime.now())
            return False
```

#### Step 4: Update Configuration

**File**: `gao_dev/config/defaults.yaml` (MODIFIED)

```yaml
# Provider Configuration
providers:
  # Selection strategy
  selection:
    # Strategy type: "auto", "performance", "cost", "availability", "composite"
    strategy: "auto"

    # Fallback chain for auto strategy
    fallback_chain:
      - "claude-code"
      - "opencode"
      - "direct-api"

    # Composite strategy weights (if strategy: "composite")
    composite_weights:
      performance: 0.6
      cost: 0.3
      availability: 0.1

    # Performance tracker settings
    performance:
      enabled: true
      cache_duration: 3600  # 1 hour

    # Health check settings
    health:
      enabled: true
      cache_duration: 300  # 5 minutes
      check_interval: 60   # Check every minute

  # ... rest of provider configuration ...
```

#### Step 5: Update ProcessExecutor

**File**: `gao_dev/core/process_executor.py` (MODIFIED)

```python
from gao_dev.core.providers.selector import ProviderSelector

class ProcessExecutor:
    """Execute tasks using configured provider."""

    def __init__(
        self,
        project_root: Path,
        provider: Optional[IAgentProvider] = None,
        provider_name: Optional[str] = None,
        provider_config: Optional[Dict] = None,
        # ... legacy params ...
    ):
        """Initialize executor."""
        self.project_root = project_root

        # If provider explicitly provided, use it
        if provider is not None:
            self.provider = provider
            logger.info("using_explicit_provider", provider=provider.name)

        # If provider name specified, create it
        elif provider_name is not None:
            factory = ProviderFactory()
            self.provider = factory.create_provider(
                provider_name, provider_config
            )
            logger.info("created_provider_by_name", provider=provider_name)

        # AUTO-SELECT PROVIDER (NEW!)
        else:
            logger.info("auto_selecting_provider")
            factory = ProviderFactory()
            selector = ProviderSelector(factory)

            # Select based on default model
            self.provider = selector.select_provider(
                model="sonnet-4.5",  # Default model
                context={"project_root": str(project_root)},
            )
            logger.info(
                "auto_selected_provider",
                provider=self.provider.name,
            )
```

---

## Testing Strategy

### Unit Tests
- Each strategy tested independently
- Mock provider availability
- Test fallback behavior
- Test weight calculations (composite)

### Integration Tests
- End-to-end provider selection
- ProcessExecutor auto-selection
- Configuration loading
- Strategy switching

### Performance Tests
- Selection overhead measurement
- Cache effectiveness
- Health check performance

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Strategy interface created
- [ ] All strategies implemented
- [ ] Provider selector service created
- [ ] Performance tracker working
- [ ] Health checker working
- [ ] Configuration support added
- [ ] ProcessExecutor integration complete
- [ ] Unit tests passing (100% coverage)
- [ ] Integration tests passing
- [ ] Type checking passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.2 (ClaudeCodeProvider) - MUST be complete
- Story 11.7 (OpenCodeProvider) - MUST be complete
- Story 11.10 (DirectAPIProvider) - MUST be complete

**Downstream**:
- Story 11.14 (Comprehensive Testing) - tests selection strategies

---

## Notes

- **Default Strategy**: Auto-detect (most user-friendly)
- **Custom Strategies**: Users can implement custom selection logic
- **Performance Tracking**: Optional, can be disabled
- **Health Checking**: Prevents using broken providers
- **Backward Compatible**: Explicit provider selection still works
- **Extensible**: Easy to add new strategies
- **Configuration**: All strategies configurable via YAML
- **Logging**: All decisions logged for troubleshooting

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.2: `story-11.2.md` (ClaudeCodeProvider)
- Story 11.7: `story-11.7.md` (OpenCodeProvider)
- Story 11.10: `story-11.10.md` (DirectAPIProvider)
