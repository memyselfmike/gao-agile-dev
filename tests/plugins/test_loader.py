"""Tests for PluginLoader class."""

import pytest
from pathlib import Path

from gao_dev.plugins import (
    PluginLoader,
    PluginMetadata,
    PluginType,
    PluginLoadError,
    PluginNotFoundError,
    DuplicatePluginError,
)


@pytest.fixture
def loader():
    """Create a PluginLoader instance."""
    return PluginLoader()


@pytest.fixture
def lifecycle_plugin_metadata(tmp_path):
    """Create metadata for lifecycle test plugin."""
    plugin_path = Path(__file__).parent / "fixtures" / "lifecycle_plugin"
    return PluginMetadata(
        name="lifecycle-test-plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="lifecycle_plugin.plugin.LifecycleTestPlugin",
        plugin_path=plugin_path,
        description="A test plugin with lifecycle hooks",
        author="GAO-Dev Test Suite",
        enabled=True,
    )


@pytest.fixture
def failing_init_plugin_metadata(tmp_path):
    """Create metadata for failing init test plugin."""
    plugin_path = Path(__file__).parent / "fixtures" / "failing_init_plugin"
    return PluginMetadata(
        name="failing-init-plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="failing_init_plugin.plugin.FailingInitPlugin",
        plugin_path=plugin_path,
        description="A test plugin that fails initialization",
        author="GAO-Dev Test Suite",
        enabled=True,
    )


@pytest.fixture
def disabled_plugin_metadata(tmp_path):
    """Create metadata for disabled plugin."""
    plugin_path = Path(__file__).parent / "fixtures" / "lifecycle_plugin"
    return PluginMetadata(
        name="disabled-plugin",
        version="1.0.0",
        type=PluginType.TOOL,
        entry_point="lifecycle_plugin.plugin.LifecycleTestPlugin",
        plugin_path=plugin_path,
        enabled=False,
    )


class TestPluginLoaderBasics:
    """Test basic PluginLoader functionality."""

    def test_loader_initialization(self, loader):
        """Test PluginLoader initializes with empty registries."""
        assert len(loader.list_loaded_plugins()) == 0
        assert not loader.is_loaded("any-plugin")

    def test_is_loaded_false_for_unknown_plugin(self, loader):
        """Test is_loaded returns False for unknown plugin."""
        assert not loader.is_loaded("unknown-plugin")
        assert not loader.is_loaded("UNKNOWN-PLUGIN")  # case-insensitive

    def test_list_loaded_plugins_empty(self, loader):
        """Test list_loaded_plugins returns empty list initially."""
        assert loader.list_loaded_plugins() == []


class TestPluginLoading:
    """Test plugin loading functionality."""

    def test_load_plugin_success(self, loader, lifecycle_plugin_metadata):
        """Test successful plugin loading."""
        loader.load_plugin(lifecycle_plugin_metadata)

        assert loader.is_loaded("lifecycle-test-plugin")
        assert "lifecycle-test-plugin" in loader.list_loaded_plugins()

    def test_load_plugin_calls_initialize_hook(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test that initialize() hook is called during loading."""
        loader.load_plugin(lifecycle_plugin_metadata)

        plugin = loader.get_loaded_plugin("lifecycle-test-plugin")
        assert plugin.initialized is True
        assert plugin.init_count == 1

    def test_load_plugin_with_failing_initialize(
        self, loader, failing_init_plugin_metadata
    ):
        """Test that plugin loading fails if initialize() returns False."""
        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_plugin(failing_init_plugin_metadata)

        assert "initialization returned False" in str(exc_info.value)
        assert not loader.is_loaded("failing-init-plugin")

    def test_load_plugin_already_loaded(self, loader, lifecycle_plugin_metadata):
        """Test that loading same plugin twice raises DuplicatePluginError."""
        loader.load_plugin(lifecycle_plugin_metadata)

        with pytest.raises(DuplicatePluginError) as exc_info:
            loader.load_plugin(lifecycle_plugin_metadata)

        assert "already loaded" in str(exc_info.value)

    def test_load_plugin_case_insensitive(self, loader, lifecycle_plugin_metadata):
        """Test that plugin names are case-insensitive."""
        loader.load_plugin(lifecycle_plugin_metadata)

        assert loader.is_loaded("lifecycle-test-plugin")
        assert loader.is_loaded("LIFECYCLE-TEST-PLUGIN")
        assert loader.is_loaded("Lifecycle-Test-Plugin")

    def test_load_plugin_with_invalid_entry_point(self, loader):
        """Test loading plugin with invalid entry point format."""
        from gao_dev.plugins.exceptions import PluginValidationError

        # PluginMetadata validation catches invalid entry point
        with pytest.raises(PluginValidationError) as exc_info:
            metadata = PluginMetadata(
                name="invalid-entry",
                version="1.0.0",
                type=PluginType.TOOL,
                entry_point="invalid",  # No dot separator
                plugin_path=Path("."),
                enabled=True,
            )

        assert "Invalid entry_point" in str(exc_info.value)

    def test_load_plugin_with_missing_module(self, loader):
        """Test loading plugin with non-existent module."""
        metadata = PluginMetadata(
            name="missing-module",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="nonexistent.module.Class",
            plugin_path=Path("."),
            enabled=True,
        )

        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_plugin(metadata)

        assert "Failed to import" in str(exc_info.value)

    def test_load_plugin_with_missing_class(self, loader):
        """Test loading plugin with missing class in module."""
        plugin_path = Path(__file__).parent / "fixtures" / "lifecycle_plugin"
        metadata = PluginMetadata(
            name="missing-class",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="lifecycle_plugin.plugin.NonExistentClass",
            plugin_path=plugin_path,
            enabled=True,
        )

        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_plugin(metadata)

        assert "has no class" in str(exc_info.value)


class TestPluginUnloading:
    """Test plugin unloading functionality."""

    def test_unload_plugin_success(self, loader, lifecycle_plugin_metadata):
        """Test successful plugin unloading."""
        loader.load_plugin(lifecycle_plugin_metadata)
        assert loader.is_loaded("lifecycle-test-plugin")

        loader.unload_plugin("lifecycle-test-plugin")

        assert not loader.is_loaded("lifecycle-test-plugin")
        assert "lifecycle-test-plugin" not in loader.list_loaded_plugins()

    def test_unload_plugin_calls_cleanup_hook(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test that cleanup() hook is called during unloading."""
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin = loader.get_loaded_plugin("lifecycle-test-plugin")

        assert plugin.cleaned_up is False

        loader.unload_plugin("lifecycle-test-plugin")

        assert plugin.cleaned_up is True
        assert plugin.cleanup_count == 1

    def test_unload_plugin_not_loaded(self, loader):
        """Test unloading non-existent plugin raises PluginNotFoundError."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            loader.unload_plugin("non-existent")

        assert "is not loaded" in str(exc_info.value)
        assert "Loaded plugins:" in str(exc_info.value)

    def test_unload_plugin_case_insensitive(self, loader, lifecycle_plugin_metadata):
        """Test that unload is case-insensitive."""
        loader.load_plugin(lifecycle_plugin_metadata)

        loader.unload_plugin("LIFECYCLE-TEST-PLUGIN")

        assert not loader.is_loaded("lifecycle-test-plugin")

    def test_unload_all_plugins(self, loader, lifecycle_plugin_metadata):
        """Test unloading all plugins."""
        # Load multiple plugins
        loader.load_plugin(lifecycle_plugin_metadata)

        # Create another plugin instance with different name
        metadata2 = PluginMetadata(
            name="lifecycle-test-plugin-2",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="lifecycle_plugin.plugin.LifecycleTestPlugin",
            plugin_path=lifecycle_plugin_metadata.plugin_path,
            enabled=True,
        )
        loader.load_plugin(metadata2)

        assert len(loader.list_loaded_plugins()) == 2

        loader.unload_all()

        assert len(loader.list_loaded_plugins()) == 0


class TestPluginReloading:
    """Test plugin reloading functionality."""

    def test_reload_plugin_success(self, loader, lifecycle_plugin_metadata):
        """Test successful plugin reloading."""
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin_before = loader.get_loaded_plugin("lifecycle-test-plugin")

        loader.reload_plugin("lifecycle-test-plugin")

        assert loader.is_loaded("lifecycle-test-plugin")
        plugin_after = loader.get_loaded_plugin("lifecycle-test-plugin")

        # Should be a new instance
        assert plugin_before is not plugin_after

    def test_reload_plugin_not_loaded(self, loader):
        """Test reloading non-existent plugin raises PluginNotFoundError."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            loader.reload_plugin("non-existent")

        assert "is not loaded" in str(exc_info.value)

    def test_reload_plugin_calls_lifecycle_hooks(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test that reload calls cleanup and initialize."""
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin_before = loader.get_loaded_plugin("lifecycle-test-plugin")

        assert plugin_before.init_count == 1
        assert plugin_before.cleanup_count == 0

        loader.reload_plugin("lifecycle-test-plugin")

        # Old plugin should have been cleaned up
        assert plugin_before.cleanup_count == 1

        # New plugin should be initialized
        plugin_after = loader.get_loaded_plugin("lifecycle-test-plugin")
        assert plugin_after.init_count == 1
        assert plugin_after.cleanup_count == 0


class TestPluginAccess:
    """Test plugin access functionality."""

    def test_get_loaded_plugin_success(self, loader, lifecycle_plugin_metadata):
        """Test getting a loaded plugin instance."""
        loader.load_plugin(lifecycle_plugin_metadata)

        plugin = loader.get_loaded_plugin("lifecycle-test-plugin")

        assert plugin is not None
        assert hasattr(plugin, "do_something")
        assert plugin.do_something() == "lifecycle plugin working"

    def test_get_loaded_plugin_not_found(self, loader):
        """Test getting non-existent plugin raises PluginNotFoundError."""
        with pytest.raises(PluginNotFoundError) as exc_info:
            loader.get_loaded_plugin("non-existent")

        assert "is not loaded" in str(exc_info.value)

    def test_get_loaded_plugin_case_insensitive(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test that get_loaded_plugin is case-insensitive."""
        loader.load_plugin(lifecycle_plugin_metadata)

        plugin1 = loader.get_loaded_plugin("lifecycle-test-plugin")
        plugin2 = loader.get_loaded_plugin("LIFECYCLE-TEST-PLUGIN")

        assert plugin1 is plugin2

    def test_get_plugin_metadata(self, loader, lifecycle_plugin_metadata):
        """Test getting plugin metadata for loaded plugin."""
        loader.load_plugin(lifecycle_plugin_metadata)

        metadata = loader.get_plugin_metadata("lifecycle-test-plugin")

        assert metadata.name == "lifecycle-test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.type == PluginType.TOOL

    def test_get_plugin_metadata_not_found(self, loader):
        """Test getting metadata for non-existent plugin."""
        with pytest.raises(PluginNotFoundError):
            loader.get_plugin_metadata("non-existent")

    def test_list_loaded_plugins(self, loader, lifecycle_plugin_metadata):
        """Test listing loaded plugins."""
        assert loader.list_loaded_plugins() == []

        loader.load_plugin(lifecycle_plugin_metadata)

        plugins = loader.list_loaded_plugins()
        assert len(plugins) == 1
        assert "lifecycle-test-plugin" in plugins

    def test_list_loaded_plugins_sorted(self, loader, lifecycle_plugin_metadata):
        """Test that list_loaded_plugins returns sorted list."""
        # Load multiple plugins
        loader.load_plugin(lifecycle_plugin_metadata)

        metadata2 = PluginMetadata(
            name="a-plugin",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="lifecycle_plugin.plugin.LifecycleTestPlugin",
            plugin_path=lifecycle_plugin_metadata.plugin_path,
            enabled=True,
        )
        loader.load_plugin(metadata2)

        plugins = loader.list_loaded_plugins()

        assert plugins == ["a-plugin", "lifecycle-test-plugin"]  # Sorted


class TestBatchLoading:
    """Test batch plugin loading functionality."""

    def test_load_all_enabled_empty_list(self, loader):
        """Test load_all_enabled with empty list."""
        results = loader.load_all_enabled([])

        assert results == {}
        assert len(loader.list_loaded_plugins()) == 0

    def test_load_all_enabled_single_plugin(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test load_all_enabled with single enabled plugin."""
        results = loader.load_all_enabled([lifecycle_plugin_metadata])

        assert results["lifecycle-test-plugin"] == "loaded"
        assert loader.is_loaded("lifecycle-test-plugin")

    def test_load_all_enabled_skips_disabled(
        self, loader, disabled_plugin_metadata
    ):
        """Test load_all_enabled skips disabled plugins."""
        results = loader.load_all_enabled([disabled_plugin_metadata])

        assert "disabled-plugin" in results
        assert results["disabled-plugin"] == "skipped (disabled)"
        assert not loader.is_loaded("disabled-plugin")

    def test_load_all_enabled_mixed_plugins(
        self,
        loader,
        lifecycle_plugin_metadata,
        disabled_plugin_metadata,
        failing_init_plugin_metadata,
    ):
        """Test load_all_enabled with mix of enabled, disabled, and failing plugins."""
        plugins = [
            lifecycle_plugin_metadata,
            disabled_plugin_metadata,
            failing_init_plugin_metadata,
        ]

        results = loader.load_all_enabled(plugins)

        assert results["lifecycle-test-plugin"] == "loaded"
        assert results["disabled-plugin"] == "skipped (disabled)"
        assert results["failing-init-plugin"].startswith("failed:")

        assert loader.is_loaded("lifecycle-test-plugin")
        assert not loader.is_loaded("disabled-plugin")
        assert not loader.is_loaded("failing-init-plugin")

    def test_load_all_enabled_continues_on_failure(
        self, loader, lifecycle_plugin_metadata, failing_init_plugin_metadata
    ):
        """Test that load_all_enabled continues loading after failure."""
        plugins = [failing_init_plugin_metadata, lifecycle_plugin_metadata]

        results = loader.load_all_enabled(plugins)

        # First plugin should fail but not stop the process
        assert results["failing-init-plugin"].startswith("failed:")
        assert results["lifecycle-test-plugin"] == "loaded"

        # Second plugin should still load
        assert loader.is_loaded("lifecycle-test-plugin")


class TestIntegration:
    """Integration tests for PluginLoader."""

    def test_full_lifecycle(self, loader, lifecycle_plugin_metadata):
        """Test complete plugin lifecycle: load -> use -> unload."""
        # Load
        loader.load_plugin(lifecycle_plugin_metadata)
        assert loader.is_loaded("lifecycle-test-plugin")

        # Use
        plugin = loader.get_loaded_plugin("lifecycle-test-plugin")
        assert plugin.initialized is True
        result = plugin.do_something()
        assert result == "lifecycle plugin working"

        # Unload
        loader.unload_plugin("lifecycle-test-plugin")
        assert not loader.is_loaded("lifecycle-test-plugin")
        assert plugin.cleaned_up is True

    def test_load_unload_reload_cycle(self, loader, lifecycle_plugin_metadata):
        """Test loading, unloading, and reloading a plugin."""
        # First load
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin1 = loader.get_loaded_plugin("lifecycle-test-plugin")

        # Unload
        loader.unload_plugin("lifecycle-test-plugin")

        # Reload
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin2 = loader.get_loaded_plugin("lifecycle-test-plugin")

        # Should be different instances
        assert plugin1 is not plugin2
        assert plugin1.cleaned_up is True
        assert plugin2.initialized is True

    def test_multiple_plugins_independent(self, loader, lifecycle_plugin_metadata):
        """Test that multiple plugin instances are independent."""
        # Load same plugin code with different names
        loader.load_plugin(lifecycle_plugin_metadata)

        metadata2 = PluginMetadata(
            name="lifecycle-test-plugin-copy",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="lifecycle_plugin.plugin.LifecycleTestPlugin",
            plugin_path=lifecycle_plugin_metadata.plugin_path,
            enabled=True,
        )
        loader.load_plugin(metadata2)

        plugin1 = loader.get_loaded_plugin("lifecycle-test-plugin")
        plugin2 = loader.get_loaded_plugin("lifecycle-test-plugin-copy")

        assert plugin1 is not plugin2
        assert plugin1.init_count == 1
        assert plugin2.init_count == 1


class TestErrorHandling:
    """Test error handling in PluginLoader."""

    def test_entry_point_parsing(self, loader):
        """Test entry point parsing edge cases."""
        # Valid entry points should not raise during parsing
        valid_metadata = PluginMetadata(
            name="valid",
            version="1.0.0",
            type=PluginType.TOOL,
            entry_point="module.submodule.ClassName",
            plugin_path=Path("."),
            enabled=True,
        )

        # This will fail at import time, but parsing should work
        with pytest.raises(PluginLoadError) as exc_info:
            loader.load_plugin(valid_metadata)

        assert "Failed to import" in str(exc_info.value)

    def test_cleanup_failure_does_not_prevent_unload(
        self, loader, lifecycle_plugin_metadata
    ):
        """Test that cleanup failure doesn't prevent plugin unload."""
        loader.load_plugin(lifecycle_plugin_metadata)
        plugin = loader.get_loaded_plugin("lifecycle-test-plugin")

        # Make cleanup fail
        def failing_cleanup():
            raise RuntimeError("Cleanup failed")

        plugin.cleanup = failing_cleanup

        # Should not raise, just log warning
        loader.unload_plugin("lifecycle-test-plugin")

        # Plugin should still be unloaded
        assert not loader.is_loaded("lifecycle-test-plugin")
