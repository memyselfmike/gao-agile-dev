"""Provider abstraction module for multi-provider agent execution.

This module provides the core abstractions for GAO-Dev's provider system,
enabling support for multiple AI agent execution backends (Claude Code CLI,
OpenCode CLI, direct APIs, custom providers) through a unified interface.

Key Components:
- IAgentProvider: Abstract interface all providers must implement
- ProviderError hierarchy: Standardized error taxonomy with intelligent methods
- AgentContext: Execution context model passed to providers

Example:
    ```python
    from gao_dev.core.providers import (
        IAgentProvider,
        AgentContext,
        ProviderError,
        AuthenticationError,
        RateLimitError
    )

    # Create context
    context = AgentContext(project_root=Path("/project"))

    # Execute task with error handling
    try:
        async for message in provider.execute_task(
            task="Implement feature",
            context=context,
            model="sonnet-4.5",
            tools=["Read", "Write"]
        ):
            print(message)
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s")
    except ProviderError as e:
        if e.should_fallback():
            # Try different provider
            pass
        elif e.is_retryable():
            # Retry after delay
            pass
        else:
            # Fatal error
            raise
    ```
"""

from .base import IAgentProvider
from .exceptions import (
    # Error taxonomy enum
    ProviderErrorType,

    # Base exception
    ProviderError,

    # Specific exceptions (new taxonomy)
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    ProviderUnavailableError,

    # Legacy exception aliases (backward compatibility)
    ProviderNotFoundError,
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ProviderInitializationError,
    ProviderRegistrationError,
    ProviderCreationError,
    DuplicateProviderError,
    ModelNotSupportedError,
)
from .models import AgentContext
from .factory import ProviderFactory
from .direct_api import DirectAPIProvider
from .claude_code import ClaudeCodeProvider
from .opencode import OpenCodeProvider
from .selection import (
    IProviderSelectionStrategy,
    AutoDetectStrategy,
    PerformanceBasedStrategy,
    CostBasedStrategy,
    AvailabilityBasedStrategy,
    CompositeStrategy,
    ProviderSelectionError,
)
from .selector import ProviderSelector
from .performance_tracker import ProviderPerformanceTracker
from .health_check import ProviderHealthChecker
from .cache import ProviderCache, hash_config

__all__ = [
    # Core interface
    "IAgentProvider",

    # Factory
    "ProviderFactory",

    # Built-in providers
    "DirectAPIProvider",
    "ClaudeCodeProvider",
    "OpenCodeProvider",

    # Selection strategies
    "IProviderSelectionStrategy",
    "AutoDetectStrategy",
    "PerformanceBasedStrategy",
    "CostBasedStrategy",
    "AvailabilityBasedStrategy",
    "CompositeStrategy",
    "ProviderSelectionError",

    # Provider selection
    "ProviderSelector",
    "ProviderPerformanceTracker",
    "ProviderHealthChecker",

    # Performance optimization
    "ProviderCache",
    "hash_config",

    # Models
    "AgentContext",

    # Error taxonomy
    "ProviderErrorType",

    # Base exception
    "ProviderError",

    # Specific exceptions (new standardized taxonomy)
    "AuthenticationError",
    "RateLimitError",
    "ModelNotFoundError",
    "ProviderUnavailableError",

    # Legacy exceptions (backward compatibility)
    "ProviderNotFoundError",
    "ProviderExecutionError",
    "ProviderTimeoutError",
    "ProviderConfigurationError",
    "ProviderInitializationError",
    "ProviderRegistrationError",
    "ProviderCreationError",
    "DuplicateProviderError",
    "ModelNotSupportedError",
]

# Version information
__version__ = "1.0.0"
