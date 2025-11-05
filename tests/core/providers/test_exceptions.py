"""Unit tests for provider exception hierarchy."""

import pytest
from gao_dev.core.providers.exceptions import (
    ProviderErrorType,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    ProviderUnavailableError,
    ProviderNotFoundError,
    ProviderExecutionError,
    ProviderTimeoutError,
    ProviderConfigurationError,
    ProviderInitializationError,
    ProviderRegistrationError,
    DuplicateProviderError,
    ModelNotSupportedError,
)


class TestProviderErrorType:
    """Test ProviderErrorType enum."""

    def test_enum_values_exist(self):
        """Test all required error types are defined."""
        required_types = [
            "AUTHENTICATION_ERROR",
            "AUTHORIZATION_ERROR",
            "RATE_LIMIT_ERROR",
            "QUOTA_EXCEEDED_ERROR",
            "MODEL_NOT_FOUND_ERROR",
            "INVALID_REQUEST_ERROR",
            "CONTENT_POLICY_ERROR",
            "TIMEOUT_ERROR",
            "NETWORK_ERROR",
            "PROVIDER_UNAVAILABLE_ERROR",
            "CLI_NOT_FOUND_ERROR",
            "CONFIGURATION_ERROR",
            "UNKNOWN_ERROR",
        ]

        for error_type in required_types:
            assert hasattr(ProviderErrorType, error_type)

    def test_enum_value_format(self):
        """Test enum values are lowercase with underscores."""
        for error_type in ProviderErrorType:
            assert error_type.value.islower()
            assert "_" in error_type.value or error_type.value == "error"


class TestProviderError:
    """Test ProviderError base exception."""

    def test_provider_error_initialization(self):
        """Test ProviderError can be initialized with all attributes."""
        error = ProviderError(
            error_type=ProviderErrorType.TIMEOUT_ERROR,
            message="Request timed out",
            provider_name="test-provider",
            original_error=ValueError("original"),
            retry_after=30,
            context={"timeout": 60}
        )

        assert error.error_type == ProviderErrorType.TIMEOUT_ERROR
        assert error.message == "Request timed out"
        assert error.provider_name == "test-provider"
        assert isinstance(error.original_error, ValueError)
        assert error.retry_after == 30
        assert error.context == {"timeout": 60}

    def test_provider_error_is_exception(self):
        """Test ProviderError is subclass of Exception."""
        assert issubclass(ProviderError, Exception)

    def test_provider_error_str(self):
        """Test ProviderError string representation."""
        error = ProviderError(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message="Something went wrong",
            provider_name="test"
        )

        error_str = str(error)
        assert "Something went wrong" in error_str

    def test_provider_error_repr(self):
        """Test ProviderError repr includes key attributes."""
        error = ProviderError(
            error_type=ProviderErrorType.AUTHENTICATION_ERROR,
            message="Auth failed",
            provider_name="claude-code"
        )

        repr_str = repr(error)
        assert "ProviderError" in repr_str
        assert "authentication_error" in repr_str
        assert "claude-code" in repr_str
        assert "Auth failed" in repr_str

    def test_is_retryable_for_retryable_errors(self):
        """Test is_retryable returns True for retryable error types."""
        retryable_types = [
            ProviderErrorType.RATE_LIMIT_ERROR,
            ProviderErrorType.TIMEOUT_ERROR,
            ProviderErrorType.NETWORK_ERROR,
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
        ]

        for error_type in retryable_types:
            error = ProviderError(
                error_type=error_type,
                message="test",
                provider_name="test"
            )
            assert error.is_retryable(), f"{error_type} should be retryable"

    def test_is_retryable_for_non_retryable_errors(self):
        """Test is_retryable returns False for non-retryable error types."""
        non_retryable_types = [
            ProviderErrorType.AUTHENTICATION_ERROR,
            ProviderErrorType.AUTHORIZATION_ERROR,
            ProviderErrorType.QUOTA_EXCEEDED_ERROR,
            ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            ProviderErrorType.INVALID_REQUEST_ERROR,
            ProviderErrorType.CONTENT_POLICY_ERROR,
            ProviderErrorType.CLI_NOT_FOUND_ERROR,
            ProviderErrorType.CONFIGURATION_ERROR,
            ProviderErrorType.UNKNOWN_ERROR,
        ]

        for error_type in non_retryable_types:
            error = ProviderError(
                error_type=error_type,
                message="test",
                provider_name="test"
            )
            assert not error.is_retryable(), f"{error_type} should not be retryable"

    def test_should_fallback_for_fallback_errors(self):
        """Test should_fallback returns True for fallback-eligible error types."""
        fallback_types = [
            ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR,
            ProviderErrorType.CLI_NOT_FOUND_ERROR,
            ProviderErrorType.AUTHENTICATION_ERROR,
            ProviderErrorType.MODEL_NOT_FOUND_ERROR,
            ProviderErrorType.QUOTA_EXCEEDED_ERROR,
        ]

        for error_type in fallback_types:
            error = ProviderError(
                error_type=error_type,
                message="test",
                provider_name="test"
            )
            assert error.should_fallback(), f"{error_type} should trigger fallback"

    def test_should_fallback_for_non_fallback_errors(self):
        """Test should_fallback returns False for non-fallback error types."""
        non_fallback_types = [
            ProviderErrorType.RATE_LIMIT_ERROR,
            ProviderErrorType.TIMEOUT_ERROR,
            ProviderErrorType.NETWORK_ERROR,
            ProviderErrorType.INVALID_REQUEST_ERROR,
            ProviderErrorType.CONTENT_POLICY_ERROR,
            ProviderErrorType.CONFIGURATION_ERROR,
            ProviderErrorType.UNKNOWN_ERROR,
        ]

        for error_type in non_fallback_types:
            error = ProviderError(
                error_type=error_type,
                message="test",
                provider_name="test"
            )
            assert not error.should_fallback(), f"{error_type} should not trigger fallback"


class TestAuthenticationError:
    """Test AuthenticationError exception."""

    def test_authentication_error_initialization(self):
        """Test AuthenticationError sets correct error_type."""
        error = AuthenticationError(
            provider_name="claude-code",
            message="Invalid API key"
        )

        assert error.error_type == ProviderErrorType.AUTHENTICATION_ERROR
        assert error.message == "Invalid API key"
        assert error.provider_name == "claude-code"

    def test_authentication_error_with_context(self):
        """Test AuthenticationError with context."""
        error = AuthenticationError(
            provider_name="opencode",
            message="API key not found",
            context={"env_var": "ANTHROPIC_API_KEY"}
        )

        assert error.context["env_var"] == "ANTHROPIC_API_KEY"

    def test_authentication_error_should_fallback(self):
        """Test AuthenticationError triggers fallback."""
        error = AuthenticationError(
            provider_name="test",
            message="test"
        )
        assert error.should_fallback()


class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_rate_limit_error_initialization(self):
        """Test RateLimitError sets correct error_type and retry_after."""
        error = RateLimitError(
            provider_name="direct-api",
            retry_after=60,
            message="Rate limit exceeded"
        )

        assert error.error_type == ProviderErrorType.RATE_LIMIT_ERROR
        assert error.retry_after == 60
        assert error.message == "Rate limit exceeded"

    def test_rate_limit_error_is_retryable(self):
        """Test RateLimitError is retryable."""
        error = RateLimitError(
            provider_name="test",
            retry_after=30,
            message="test"
        )
        assert error.is_retryable()

    def test_rate_limit_error_not_fallback(self):
        """Test RateLimitError does not trigger fallback."""
        error = RateLimitError(
            provider_name="test",
            retry_after=30,
            message="test"
        )
        assert not error.should_fallback()


class TestModelNotFoundError:
    """Test ModelNotFoundError exception."""

    def test_model_not_found_error_initialization(self):
        """Test ModelNotFoundError sets correct attributes."""
        error = ModelNotFoundError(
            provider_name="claude-code",
            model_name="gpt-4"
        )

        assert error.error_type == ProviderErrorType.MODEL_NOT_FOUND_ERROR
        assert error.model_name == "gpt-4"
        assert "gpt-4" in error.message
        assert "claude-code" in error.message

    def test_model_not_found_error_should_fallback(self):
        """Test ModelNotFoundError triggers fallback."""
        error = ModelNotFoundError(
            provider_name="test",
            model_name="test-model"
        )
        assert error.should_fallback()


class TestProviderUnavailableError:
    """Test ProviderUnavailableError exception."""

    def test_provider_unavailable_error_initialization(self):
        """Test ProviderUnavailableError sets correct error_type."""
        error = ProviderUnavailableError(
            provider_name="opencode",
            message="Service unavailable"
        )

        assert error.error_type == ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR
        assert error.message == "Service unavailable"

    def test_provider_unavailable_error_is_retryable(self):
        """Test ProviderUnavailableError is retryable."""
        error = ProviderUnavailableError(
            provider_name="test",
            message="test"
        )
        assert error.is_retryable()

    def test_provider_unavailable_error_should_fallback(self):
        """Test ProviderUnavailableError triggers fallback."""
        error = ProviderUnavailableError(
            provider_name="test",
            message="test"
        )
        assert error.should_fallback()


class TestLegacyExceptions:
    """Test legacy exception aliases for backward compatibility."""

    def test_provider_not_found_error_maps_to_unavailable(self):
        """Test ProviderNotFoundError maps to PROVIDER_UNAVAILABLE_ERROR."""
        error = ProviderNotFoundError(
            message="Provider not found",
            provider_name="unknown"
        )
        assert error.error_type == ProviderErrorType.PROVIDER_UNAVAILABLE_ERROR

    def test_provider_execution_error_maps_to_unknown(self):
        """Test ProviderExecutionError maps to UNKNOWN_ERROR."""
        error = ProviderExecutionError(
            message="Execution failed",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.UNKNOWN_ERROR

    def test_provider_timeout_error_maps_to_timeout(self):
        """Test ProviderTimeoutError maps to TIMEOUT_ERROR."""
        error = ProviderTimeoutError(
            message="Timeout",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.TIMEOUT_ERROR
        assert error.is_retryable()

    def test_provider_configuration_error_maps_to_configuration(self):
        """Test ProviderConfigurationError maps to CONFIGURATION_ERROR."""
        error = ProviderConfigurationError(
            message="Config invalid",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.CONFIGURATION_ERROR

    def test_provider_initialization_error_maps_to_configuration(self):
        """Test ProviderInitializationError maps to CONFIGURATION_ERROR."""
        error = ProviderInitializationError(
            message="Init failed",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.CONFIGURATION_ERROR

    def test_provider_registration_error_maps_to_configuration(self):
        """Test ProviderRegistrationError maps to CONFIGURATION_ERROR."""
        error = ProviderRegistrationError(
            message="Registration failed",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.CONFIGURATION_ERROR

    def test_duplicate_provider_error_is_registration_error(self):
        """Test DuplicateProviderError is subclass of ProviderRegistrationError."""
        assert issubclass(DuplicateProviderError, ProviderRegistrationError)

        error = DuplicateProviderError(
            message="Duplicate",
            provider_name="test"
        )
        assert error.error_type == ProviderErrorType.CONFIGURATION_ERROR

    def test_model_not_supported_error_is_model_not_found(self):
        """Test ModelNotSupportedError is alias for ModelNotFoundError."""
        assert issubclass(ModelNotSupportedError, ModelNotFoundError)

        error = ModelNotSupportedError(
            provider_name="test",
            model_name="test-model"
        )
        assert error.error_type == ProviderErrorType.MODEL_NOT_FOUND_ERROR


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_provider_error(self):
        """Test all provider exceptions inherit from ProviderError."""
        exception_classes = [
            AuthenticationError,
            RateLimitError,
            ModelNotFoundError,
            ProviderUnavailableError,
            ProviderNotFoundError,
            ProviderExecutionError,
            ProviderTimeoutError,
            ProviderConfigurationError,
            ProviderInitializationError,
            ProviderRegistrationError,
            DuplicateProviderError,
            ModelNotSupportedError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, ProviderError), \
                f"{exc_class.__name__} should inherit from ProviderError"

    def test_all_exceptions_inherit_from_exception(self):
        """Test all provider exceptions are Python exceptions."""
        exception_classes = [
            ProviderError,
            AuthenticationError,
            RateLimitError,
            ModelNotFoundError,
            ProviderUnavailableError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, Exception), \
                f"{exc_class.__name__} should inherit from Exception"


class TestExceptionContext:
    """Test exception context handling."""

    def test_exception_with_original_error(self):
        """Test exception can store original error."""
        original = ValueError("original error")
        error = ProviderError(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message="Wrapped error",
            provider_name="test",
            original_error=original
        )

        assert error.original_error is original
        assert isinstance(error.original_error, ValueError)

    def test_exception_with_empty_context(self):
        """Test exception with no context defaults to empty dict."""
        error = ProviderError(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message="test",
            provider_name="test"
        )

        assert error.context == {}
        assert isinstance(error.context, dict)

    def test_exception_context_is_mutable(self):
        """Test exception context can be modified after creation."""
        error = ProviderError(
            error_type=ProviderErrorType.UNKNOWN_ERROR,
            message="test",
            provider_name="test",
            context={"key": "value"}
        )

        error.context["new_key"] = "new_value"
        assert error.context["new_key"] == "new_value"
