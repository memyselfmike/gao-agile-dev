"""Provider exception hierarchy with standardized error taxonomy.

This module implements Winston's R2 recommendation for a standardized
error taxonomy across all providers, enabling intelligent error handling,
retry logic, and provider fallback strategies.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ProviderErrorType(Enum):
    """
    Standardized error types for provider operations.

    This taxonomy enables:
    - Intelligent error handling and fallback strategies
    - Consistent error messages across providers
    - Error analytics and monitoring
    - Provider-specific error translation

    Example:
        ```python
        # Provider translates native error to standard taxonomy
        if "rate limit" in error_msg:
            raise RateLimitError(
                provider_name="claude-code",
                retry_after=60,
                message="API rate limit exceeded"
            )
        ```
    """

    # Authentication & Authorization
    AUTHENTICATION_ERROR = "authentication_error"
    """API key invalid, expired, or missing."""

    AUTHORIZATION_ERROR = "authorization_error"
    """Insufficient permissions for requested operation."""

    # Rate Limiting & Quotas
    RATE_LIMIT_ERROR = "rate_limit_error"
    """API rate limit exceeded, retry after delay."""

    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    """Monthly/daily quota exceeded, cannot retry."""

    # Model & Request Errors
    MODEL_NOT_FOUND_ERROR = "model_not_found_error"
    """Requested model not available on this provider."""

    INVALID_REQUEST_ERROR = "invalid_request_error"
    """Malformed request (e.g., invalid parameters)."""

    CONTENT_POLICY_ERROR = "content_policy_error"
    """Request violates provider's content policy."""

    # Network & Infrastructure
    TIMEOUT_ERROR = "timeout_error"
    """Request timed out (client-side or server-side)."""

    NETWORK_ERROR = "network_error"
    """Network connectivity issues."""

    # Provider Availability
    PROVIDER_UNAVAILABLE_ERROR = "provider_unavailable_error"
    """Provider service is down or unreachable."""

    CLI_NOT_FOUND_ERROR = "cli_not_found_error"
    """CLI executable not found (for CLI-based providers)."""

    # Configuration
    CONFIGURATION_ERROR = "configuration_error"
    """Provider misconfigured (e.g., invalid base URL)."""

    # Unknown
    UNKNOWN_ERROR = "unknown_error"
    """Unclassified error (should be rare)."""


class ProviderError(Exception):
    """
    Base exception for all provider errors.

    Attributes:
        error_type: Standardized error type from taxonomy
        message: Human-readable error message
        provider_name: Name of provider that raised error
        original_error: Original exception from provider (if any)
        retry_after: Seconds to wait before retry (for rate limits)
        context: Additional context for debugging

    Example:
        ```python
        raise ProviderError(
            error_type=ProviderErrorType.TIMEOUT_ERROR,
            message="Request timed out after 60 seconds",
            provider_name="claude-code",
            context={"timeout": 60}
        )
        ```
    """

    def __init__(
        self,
        error_type: ProviderErrorType,
        message: str,
        provider_name: str,
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider error.

        Args:
            error_type: Standardized error type from taxonomy
            message: Human-readable error message
            provider_name: Name of provider that raised error
            original_error: Original exception (if any)
            retry_after: Seconds to wait before retry (for rate limits)
            context: Additional debugging context
        """
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.provider_name = provider_name
        self.original_error = original_error
        self.retry_after = retry_after
        self.context = context or {}

    def is_retryable(self) -> bool:
        """
        Check if error is retryable.

        Retryable errors are transient and may succeed on retry:
        - Rate limit errors (after waiting)
        - Timeout errors
        - Network errors
        - Provider unavailable (temporary outage)

        Returns:
            True if operation should be retried

        Example:
            ```python
            try:
                await provider.execute_task(...)
            except ProviderError as e:
                if e.is_retryable():
                    await asyncio.sleep(e.retry_after or 5)
                    # Retry operation
                else:
                    # Fatal error, don't retry
                    raise
            ```
        """
        retryable_types = {
            ProviderErrorType.RATE_LIMIT_ERROR,
            ProviderErrorType.TIMEOUT_ERROR,
            ProviderErrorType.NETWORK_ERROR,
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
        }
        return self.error_type in retryable_types

    def should_fallback(self) -> bool:
        """
        Check if error should trigger provider fallback.

        Fallback-eligible errors indicate provider-specific issues
        where switching to a different provider might succeed:
        - Provider unavailable
        - CLI not found
        - Authentication error (wrong API key)
        - Model not found (provider doesn't support model)
        - Quota exceeded (try different provider)

        Returns:
            True if should try different provider

        Example:
            ```python
            providers = ["claude-code", "opencode", "direct-api"]
            for provider_name in providers:
                try:
                    provider = factory.create_provider(provider_name)
                    result = await provider.execute_task(...)
                    break
                except ProviderError as e:
                    if e.should_fallback():
                        continue  # Try next provider
                    else:
                        raise  # Fatal error, don't fallback
            ```
        """
        fallback_types = {
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            ProviderErrorType.CLI_NOT_FOUND_ERROR,
            ProviderErrorType.AUTHENTICATION_ERROR,
            ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            ProviderErrorType.QUOTA_EXCEEDED_ERROR,
        }
        return self.error_type in fallback_types

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"error_type={self.error_type.value}, "
            f"provider_name={self.provider_name}, "
            f"message={self.message!r})"
        )


class AuthenticationError(ProviderError):
    """
    Authentication failed (invalid API key).

    Raised when API key is invalid, expired, or missing.

    Example:
        ```python
        raise AuthenticationError(
            provider_name="claude-code",
            message="Invalid Anthropic API key. Set ANTHROPIC_API_KEY environment variable.",
            context={"env_var": "ANTHROPIC_API_KEY"}
        )
        ```
    """

    def __init__(
        self,
        provider_name: str,
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication error.

        Args:
            provider_name: Name of provider
            message: Error message
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.AUTHENTICATION_ERROR,
            message=message,
            provider_name=provider_name,
            original_error=original_error,
            context=context
        )


class RateLimitError(ProviderError):
    """
    Rate limit exceeded.

    Raised when API rate limit is exceeded. Operation should be
    retried after waiting for retry_after seconds.

    Example:
        ```python
        raise RateLimitError(
            provider_name="opencode",
            retry_after=60,
            message="Anthropic API rate limit exceeded. Retry after 60 seconds."
        )
        ```
    """

    def __init__(
        self,
        provider_name: str,
        retry_after: int,
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.

        Args:
            provider_name: Name of provider
            retry_after: Seconds to wait before retry
            message: Error message
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.RATE_LIMIT_ERROR,
            message=message,
            provider_name=provider_name,
            original_error=original_error,
            retry_after=retry_after,
            context=context
        )


class ModelNotFoundError(ProviderError):
    """
    Requested model not available.

    Raised when provider doesn't support the requested model.

    Example:
        ```python
        raise ModelNotFoundError(
            provider_name="claude-code",
            model_name="gpt-4",
            context={"supported_models": ["sonnet-4.5", "opus-3"]}
        )
        ```
    """

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize model not found error.

        Args:
            provider_name: Name of provider
            model_name: Model that was not found
            original_error: Original exception (if any)
            context: Additional context (e.g., supported models)
        """
        message = f"Model '{model_name}' not found on provider '{provider_name}'"
        super().__init__(
            error_type=ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            message=message,
            provider_name=provider_name,
            original_error=original_error,
            context=context or {"model_name": model_name}
        )
        self.model_name = model_name


class ProviderUnavailableError(ProviderError):
    """
    Provider service unavailable.

    Raised when provider service is down, unreachable, or experiencing
    an outage. This is typically a transient error.

    Example:
        ```python
        raise ProviderUnavailableError(
            provider_name="direct-api",
            message="Anthropic API is currently unavailable (503 Service Unavailable)"
        )
        ```
    """

    def __init__(
        self,
        provider_name: str,
        message: str,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider unavailable error.

        Args:
            provider_name: Name of provider
            message: Error message
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            message=message,
            provider_name=provider_name,
            original_error=original_error,
            context=context
        )


# Legacy exception aliases for backward compatibility
# These map to the new standardized error taxonomy


class ProviderNotFoundError(ProviderError):
    """
    Raised when requested provider not registered.

    Legacy alias that maps to PROVIDER_UNAVAILABLE_ERROR.

    Example:
        ```python
        raise ProviderNotFoundError(
            provider_name="unknown-provider",
            message="Provider 'unknown-provider' not found in registry"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: str = "unknown",
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider not found error.

        Args:
            message: Error message
            provider_name: Name of provider
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            message=message,
            provider_name=provider_name,
            original_error=original_error,
            context=context
        )


class ProviderExecutionError(ProviderError):
    """
    Raised when provider execution fails.

    Legacy alias that maps to UNKNOWN_ERROR.

    Example:
        ```python
        raise ProviderExecutionError(
            message="CLI execution failed with exit code 1",
            provider_name="claude-code"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider execution error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class ProviderTimeoutError(ProviderError):
    """
    Raised when provider execution times out.

    Legacy alias that maps to TIMEOUT_ERROR.

    Example:
        ```python
        raise ProviderTimeoutError(
            message="Execution timed out after 3600 seconds",
            provider_name="opencode",
            context={"timeout": 3600}
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider timeout error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.TIMEOUT_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class ProviderConfigurationError(ProviderError):
    """
    Raised when provider configuration is invalid.

    Legacy alias that maps to CONFIGURATION_ERROR.

    Example:
        ```python
        raise ProviderConfigurationError(
            message="Invalid base URL: must be a valid HTTPS endpoint",
            provider_name="direct-api"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider configuration error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.CONFIGURATION_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class ProviderInitializationError(ProviderError):
    """
    Raised when provider initialization fails.

    Maps to CONFIGURATION_ERROR as initialization failures are
    typically due to configuration issues.

    Example:
        ```python
        raise ProviderInitializationError(
            message="Failed to initialize HTTP client: connection refused",
            provider_name="direct-api"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider initialization error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.CONFIGURATION_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class ProviderRegistrationError(ProviderError):
    """
    Raised when provider registration fails.

    Maps to CONFIGURATION_ERROR as registration failures are
    typically due to invalid provider definitions.

    Example:
        ```python
        raise ProviderRegistrationError(
            message="Provider class must implement IAgentProvider",
            provider_name="custom-provider"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider registration error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.CONFIGURATION_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class DuplicateProviderError(ProviderRegistrationError):
    """
    Raised when attempting to register duplicate provider.

    Subclass of ProviderRegistrationError.

    Example:
        ```python
        raise DuplicateProviderError(
            message="Provider 'claude-code' already registered",
            provider_name="claude-code"
        )
        ```
    """

    pass


class ProviderCreationError(ProviderError):
    """
    Raised when provider instantiation fails.

    Maps to CONFIGURATION_ERROR as creation failures are typically
    due to configuration issues or missing dependencies.

    Example:
        ```python
        raise ProviderCreationError(
            message="Failed to create provider: missing required dependency",
            provider_name="custom-provider"
        )
        ```
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider creation error.

        Args:
            message: Error message
            provider_name: Name of provider (if known)
            original_error: Original exception (if any)
            context: Additional context
        """
        super().__init__(
            error_type=ProviderErrorType.CONFIGURATION_ERROR,
            message=message,
            provider_name=provider_name or "unknown",
            original_error=original_error,
            context=context
        )


class ModelNotSupportedError(ModelNotFoundError):
    """
    Raised when model not supported by provider.

    Legacy alias for ModelNotFoundError (backward compatibility).

    Example:
        ```python
        raise ModelNotSupportedError(
            provider_name="claude-code",
            model_name="gpt-4"
        )
        ```
    """

    pass
