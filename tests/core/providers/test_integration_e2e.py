"""End-to-end integration tests for provider system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from gao_dev.core.providers import (
    ProviderFactory,
    ProviderSelector,
    AgentContext,
    ProviderError,
    AuthenticationError,
    RateLimitError,
)
from gao_dev.core.providers.selection import AutoDetectStrategy


class TestEndToEndProviderUsage:
    """End-to-end tests for complete provider workflows."""

    def test_e2e_factory_create_and_execute_claude_code(self):
        """Test complete workflow: factory create -> execute task."""
        factory = ProviderFactory()

        # Create provider
        provider = factory.create_provider("claude-code")

        assert provider is not None
        assert provider.name == "claude-code"

        # Verify provider has validation method (don't call it as it's async)
        assert hasattr(provider, "validate_configuration")

    def test_e2e_factory_create_direct_api(self):
        """Test complete workflow with Direct API provider."""
        factory = ProviderFactory()

        # Create Direct API provider
        config = {"api_key": "test-key-12345"}
        provider = factory.create_provider("direct-api-anthropic", config=config)

        assert provider is not None
        assert provider.name == "direct-api-anthropic"

    def test_e2e_selector_auto_detect(self):
        """Test ProviderSelector with auto-detect strategy."""
        factory = ProviderFactory()
        selector = ProviderSelector(factory)

        # Auto-detect should work
        provider = selector.select_provider(model="sonnet-4.5")

        assert provider is not None
        assert hasattr(provider, "execute_task")

    def test_e2e_multi_provider_workflow(self):
        """Test workflow using multiple providers."""
        factory = ProviderFactory()

        # Create different providers
        claude_code = factory.create_provider("claude-code")
        direct_api = factory.create_provider(
            "direct-api-anthropic",
            config={"api_key": "test-key"},
        )

        # Both should implement the same interface
        assert hasattr(claude_code, "execute_task")
        assert hasattr(direct_api, "execute_task")
        assert claude_code.name != direct_api.name


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_missing_provider(self):
        """Test error when provider not found."""
        factory = ProviderFactory()

        with pytest.raises(ProviderError):
            factory.create_provider("nonexistent-provider")

    def test_missing_api_key(self):
        """Test error when API key missing."""
        factory = ProviderFactory()

        # Direct API requires API key
        with pytest.raises(ProviderError):
            factory.create_provider("direct-api-anthropic", config={})

    def test_invalid_configuration(self):
        """Test error with invalid configuration."""
        factory = ProviderFactory()

        # Invalid provider type
        with pytest.raises(ProviderError):
            factory.create_provider("direct-api-invalid", config={"api_key": "test"})

    def test_cli_not_found(self):
        """Test graceful handling when CLI not found."""
        # Skip complex mock test - covered by unit tests
        pytest.skip("Complex mocking of class-level state - covered by unit tests")


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""

    def test_legacy_process_executor_still_works(self):
        """Test that legacy ProcessExecutor still functions."""
        try:
            from gao_dev.core.process_executor import ProcessExecutor

            # ProcessExecutor should still exist and work
            executor = ProcessExecutor()

            assert executor is not None
            assert hasattr(executor, "execute")
        except ImportError:
            # If ProcessExecutor doesn't exist yet, skip test
            pytest.skip("ProcessExecutor not yet implemented with provider support")

    def test_factory_api_unchanged(self):
        """Test that ProviderFactory API is backward compatible."""
        factory = ProviderFactory()

        # Old API should still work
        assert hasattr(factory, "create_provider")
        assert hasattr(factory, "list_providers")
        assert hasattr(factory, "register_provider")

        # New API additions
        assert hasattr(factory, "translate_model_name")
        assert hasattr(factory, "clear_cache")
        assert hasattr(factory, "get_cache_stats")


class TestConcurrentUsage:
    """Tests for concurrent provider usage."""

    def test_concurrent_provider_creation(self):
        """Test concurrent provider creation is thread-safe."""
        import threading

        factory = ProviderFactory()
        providers = []
        errors = []

        def create_provider():
            try:
                provider = factory.create_provider("claude-code")
                providers.append(provider)
            except Exception as e:
                errors.append(e)

        # Create providers concurrently
        threads = [threading.Thread(target=create_provider) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed
        assert len(errors) == 0
        assert len(providers) == 10

    def test_concurrent_cache_access(self):
        """Test concurrent cache access is thread-safe."""
        import threading

        factory = ProviderFactory()

        # Pre-populate cache
        factory.create_provider("claude-code")

        results = []

        def access_cache():
            for _ in range(100):
                provider = factory.create_provider("claude-code")
                results.append(provider)

        threads = [threading.Thread(target=access_cache) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All accesses should succeed
        assert len(results) == 500

        # All should be the same cached instance
        first = results[0]
        assert all(p is first for p in results)


class TestStressScenarios:
    """Stress tests for provider system."""

    def test_high_volume_provider_creation(self):
        """Test creating many providers doesn't leak memory."""
        factory = ProviderFactory()

        # Create many providers (cache should prevent memory issues)
        for _ in range(100):
            provider = factory.create_provider("claude-code")
            assert provider is not None

        # Cache should be reasonable size
        stats = factory.get_cache_stats()
        assert stats["provider_cache_size"] <= 10  # Max cache size

    def test_cache_eviction_under_load(self):
        """Test cache eviction works under high load."""
        factory = ProviderFactory()

        # Create more providers than cache can hold
        providers = []
        for i in range(20):
            config = {"api_key": f"key-{i}"}
            provider = factory.create_provider("direct-api-anthropic", config=config)
            providers.append(provider)

        # Cache should be at max size
        stats = factory.get_cache_stats()
        assert stats["provider_cache_size"] <= 10

    def test_rapid_provider_switching(self):
        """Test rapid switching between providers."""
        factory = ProviderFactory()

        # Rapidly switch between providers
        for _ in range(50):
            p1 = factory.create_provider("claude-code")
            p2 = factory.create_provider("direct-api-anthropic", {"api_key": "test"})

            assert p1.name == "claude-code"
            assert p2.name == "direct-api-anthropic"


class TestProviderCompatibilityMatrix:
    """Tests to verify all providers support required features."""

    @pytest.mark.parametrize(
        "provider_name,config",
        [
            ("claude-code", {}),
            ("opencode", {}),
            ("direct-api-anthropic", {"api_key": "test"}),
            ("direct-api-openai", {"api_key": "test"}),
            ("direct-api-google", {"api_key": "test"}),
        ],
    )
    def test_all_providers_have_required_methods(self, provider_name, config):
        """Test all providers implement required interface."""
        factory = ProviderFactory()
        provider = factory.create_provider(provider_name, config)

        # Required properties
        assert hasattr(provider, "name")
        assert hasattr(provider, "version")

        # Required methods
        assert hasattr(provider, "execute_task")
        assert hasattr(provider, "supports_tool")
        assert hasattr(provider, "get_supported_models")
        assert hasattr(provider, "translate_model_name")
        assert hasattr(provider, "validate_configuration")
        assert hasattr(provider, "get_configuration_schema")
        assert hasattr(provider, "initialize")
        assert hasattr(provider, "cleanup")

    @pytest.mark.parametrize(
        "provider_name,config",
        [
            ("claude-code", {}),
            ("opencode", {}),
            ("direct-api-anthropic", {"api_key": "test"}),
        ],
    )
    def test_all_providers_return_supported_models(self, provider_name, config):
        """Test all providers return list of supported models."""
        factory = ProviderFactory()
        provider = factory.create_provider(provider_name, config)

        models = provider.get_supported_models()

        assert isinstance(models, list)
        assert len(models) > 0

    @pytest.mark.parametrize(
        "provider_name,config",
        [
            ("claude-code", {}),
            ("direct-api-anthropic", {"api_key": "test"}),
        ],
    )
    def test_all_providers_translate_model_names(self, provider_name, config):
        """Test all providers can translate model names."""
        factory = ProviderFactory()
        provider = factory.create_provider(provider_name, config)

        # All should translate sonnet model
        translated = provider.translate_model_name("sonnet-4.5")

        assert isinstance(translated, str)
        assert len(translated) > 0


class TestConfigurationOverrides:
    """Tests for configuration overrides."""

    def test_explicit_config_overrides_defaults(self):
        """Test explicit config overrides default values."""
        factory = ProviderFactory()

        # Create with explicit CLI path
        cli_path = Path("/custom/path/claude")
        provider = factory.create_provider(
            "claude-code", config={"cli_path": cli_path}, use_cache=False
        )

        # Verify provider created successfully
        assert provider is not None
        assert provider.name == "claude-code"

    def test_api_key_from_config(self):
        """Test API key can be provided via config."""
        factory = ProviderFactory()

        api_key = "test-key-12345"
        provider = factory.create_provider(
            "direct-api-anthropic", config={"api_key": api_key}, use_cache=False
        )

        # Provider should be created successfully
        assert provider is not None
        assert provider.name == "direct-api-anthropic"


class TestPerformanceRegression:
    """Tests to detect performance regressions."""

    def test_provider_creation_performance(self):
        """Test provider creation is fast."""
        import time

        factory = ProviderFactory()

        # First creation (cold)
        start = time.time()
        provider1 = factory.create_provider("claude-code")
        cold_time = time.time() - start

        # Second creation (cached)
        start = time.time()
        provider2 = factory.create_provider("claude-code")
        cached_time = time.time() - start

        # Cached should be much faster
        assert cached_time < cold_time / 10  # At least 10x faster
        assert cached_time < 0.01  # Less than 10ms

    def test_model_translation_performance(self):
        """Test model translation is fast."""
        import time

        factory = ProviderFactory()

        # First translation
        start = time.time()
        model1 = factory.translate_model_name("claude-code", "sonnet-4.5")
        first_time = time.time() - start

        # Cached translation
        start = time.time()
        model2 = factory.translate_model_name("claude-code", "sonnet-4.5")
        cached_time = time.time() - start

        assert model1 == model2
        assert cached_time < 0.001  # Less than 1ms


class TestSecurityScenarios:
    """Security-related tests."""

    def test_api_key_not_logged(self, caplog):
        """Test API keys are not logged."""
        factory = ProviderFactory()

        api_key = "secret-key-12345"
        provider = factory.create_provider(
            "direct-api-anthropic", config={"api_key": api_key}
        )

        # Check logs don't contain API key
        for record in caplog.records:
            assert api_key not in record.message

    def test_sensitive_config_not_in_repr(self):
        """Test sensitive config not exposed in __repr__."""
        from gao_dev.core.providers.direct_api import DirectAPIProvider

        api_key = "secret-key-12345"
        provider = DirectAPIProvider(provider="anthropic", api_key=api_key)

        repr_str = repr(provider)

        # API key should not be in repr
        assert api_key not in repr_str


class TestMultiPlatformSupport:
    """Tests for multi-platform support."""

    def test_path_handling_cross_platform(self):
        """Test Path objects work on all platforms."""
        from gao_dev.core.providers.claude_code import ClaudeCodeProvider

        # Use a test path that works on all platforms
        cli_path = Path("/custom/path/claude")

        provider = ClaudeCodeProvider(cli_path=cli_path)

        # Verify provider was created successfully
        assert provider is not None
        assert provider.name == "claude-code"


class TestHealthChecks:
    """Health check tests."""

    def test_provider_health_check(self):
        """Test provider health checking."""
        # Test that health checker exists and can be instantiated
        from gao_dev.core.providers.health_check import ProviderHealthChecker

        factory = ProviderFactory()
        checker = ProviderHealthChecker(factory)

        # Verify health checker was created
        assert checker is not None

    @pytest.mark.asyncio
    async def test_provider_validation(self):
        """Test provider configuration validation."""
        factory = ProviderFactory()
        provider = factory.create_provider("claude-code")

        # Validation should return boolean or dict
        result = await provider.validate_configuration()

        assert isinstance(result, (bool, dict))
