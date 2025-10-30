# Story 4.2: Implement Plugin Loading and Lifecycle

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** a plugin loader that manages plugin lifecycle
**So that** plugins can be loaded, initialized, used, and cleaned up properly

---

## Description

Implement a plugin loading and lifecycle management system that takes discovered plugin metadata, dynamically loads the plugin code, manages the plugin instance lifecycle (init → active → cleanup), and provides access to loaded plugins.

**Current State**: Plugins can be discovered (Story 4.1) but cannot be loaded or used.

**Target State**: New `PluginLoader` class in `gao_dev/plugins/loader.py` that handles dynamic plugin loading with proper lifecycle management.

---

## Acceptance Criteria

### PluginLoader Implementation

- [ ] **Class created**: `gao_dev/plugins/loader.py`
- [ ] **Implements**: `IPluginLoader` interface completely
- [ ] **Size**: < 300 lines
- [ ] **Single responsibility**: Load and manage plugin instances

### Core Methods

- [ ] **load_plugin(metadata)** -> None
  - Dynamically import plugin module using entry_point
  - Instantiate plugin class
  - Call plugin.initialize() if method exists
  - Store plugin instance in registry
  - Raise PluginLoadError if loading fails
  - Raise DuplicatePluginError if already loaded

- [ ] **unload_plugin(plugin_name)** -> None
  - Call plugin.cleanup() if method exists
  - Remove plugin from registry
  - Cleanup imported modules
  - Raise PluginNotFoundError if not loaded

- [ ] **reload_plugin(plugin_name)** -> None
  - Unload existing plugin
  - Re-discover plugin metadata
  - Load plugin with new metadata
  - Preserves configuration

- [ ] **get_loaded_plugin(plugin_name)** -> Any
  - Return loaded plugin instance
  - Raise PluginNotFoundError if not loaded

- [ ] **is_loaded(plugin_name)** -> bool
  - Check if plugin currently loaded
  - Case-insensitive lookup

- [ ] **list_loaded_plugins()** -> List[str]
  - Return names of all loaded plugins
  - Sorted alphabetically

### Plugin Lifecycle Hooks

- [ ] **initialize()**: Optional plugin method called after loading
  - Plugin can set up resources
  - Return True for success, False for failure
  - Plugin not registered if initialization fails

- [ ] **cleanup()**: Optional plugin method called before unloading
  - Plugin can clean up resources
  - Release file handles, connections, etc.
  - Always called, even if errors occur

### Dynamic Import Handling

- [ ] **Module import**:
  - Use importlib to dynamically import plugin module
  - Add plugin directory to sys.path temporarily
  - Handle import errors gracefully
  - Support nested module structures

- [ ] **Class instantiation**:
  - Get class from module using getattr
  - Verify class implements required interface
  - Call constructor with no arguments (default)
  - Handle instantiation errors

### Error Handling

- [ ] **Import errors**: PluginLoadError with clear message
- [ ] **Missing class**: PluginLoadError with class name
- [ ] **Invalid interface**: PluginValidationError
- [ ] **Initialization failure**: PluginLoadError with details
- [ ] **Already loaded**: DuplicatePluginError
- [ ] **Not found**: PluginNotFoundError

### Integration with Discovery

- [ ] **Auto-load workflow**:
  - Discover plugins using PluginDiscovery
  - Load each enabled plugin
  - Skip disabled plugins
  - Log successes and failures

- [ ] **Configuration-driven loading**:
  - Respect enabled flag in plugin.yaml
  - Support auto_discover config option
  - Allow manual plugin loading via API

### Testing

- [ ] Unit tests for PluginLoader (85%+ coverage)
- [ ] Test successful plugin loading
- [ ] Test plugin unloading and cleanup
- [ ] Test plugin reload
- [ ] Test lifecycle hooks (initialize, cleanup)
- [ ] Test error handling (import failures, invalid plugins)
- [ ] Integration tests with real plugin
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create PluginLoader class**:
   ```python
   import importlib
   import sys
   from pathlib import Path
   from typing import Dict, Any, List
   import structlog

   logger = structlog.get_logger(__name__)

   class PluginLoader(IPluginLoader):
       """
       Loads and manages plugin instances with lifecycle management.

       Handles dynamic module import, class instantiation, lifecycle hooks,
       and plugin registry management.
       """

       def __init__(self):
           """Initialize plugin loader."""
           self._loaded_plugins: Dict[str, Any] = {}
           self._plugin_metadata: Dict[str, PluginMetadata] = {}

       def load_plugin(self, metadata: PluginMetadata) -> None:
           """Load a plugin from its metadata."""
           plugin_name = metadata.name.lower()

           # Check if already loaded
           if plugin_name in self._loaded_plugins:
               raise DuplicatePluginError(
                   f"Plugin '{metadata.name}' is already loaded"
               )

           try:
               # Add plugin directory to sys.path temporarily
               plugin_dir = str(metadata.plugin_path)
               if plugin_dir not in sys.path:
                   sys.path.insert(0, plugin_dir)

               # Import module
               module_path = metadata.get_module_path()
               module = importlib.import_module(module_path)

               # Get class
               class_name = metadata.get_class_name()
               if not hasattr(module, class_name):
                   raise PluginLoadError(
                       f"Module '{module_path}' has no class '{class_name}'"
                   )

               plugin_class = getattr(module, class_name)

               # Instantiate plugin
               plugin_instance = plugin_class()

               # Call initialize hook if exists
               if hasattr(plugin_instance, 'initialize'):
                   try:
                       success = plugin_instance.initialize()
                       if success is False:
                           raise PluginLoadError(
                               f"Plugin initialization returned False"
                           )
                   except Exception as e:
                       raise PluginLoadError(
                           f"Plugin initialization failed: {e}"
                       ) from e

               # Store plugin
               self._loaded_plugins[plugin_name] = plugin_instance
               self._plugin_metadata[plugin_name] = metadata

               logger.info(
                   "plugin_loaded",
                   plugin_name=metadata.name,
                   plugin_type=metadata.type.value,
                   plugin_version=metadata.version
               )

           except ImportError as e:
               raise PluginLoadError(
                   f"Failed to import plugin module '{metadata.entry_point}': {e}"
               ) from e
           except Exception as e:
               raise PluginLoadError(
                   f"Failed to load plugin '{metadata.name}': {e}"
               ) from e
           finally:
               # Remove plugin directory from sys.path
               if plugin_dir in sys.path:
                   sys.path.remove(plugin_dir)

       def unload_plugin(self, plugin_name: str) -> None:
           """Unload a plugin by name."""
           plugin_name_lower = plugin_name.lower()

           if plugin_name_lower not in self._loaded_plugins:
               raise PluginNotFoundError(
                   f"Plugin '{plugin_name}' is not loaded"
               )

           plugin_instance = self._loaded_plugins[plugin_name_lower]

           # Call cleanup hook if exists
           if hasattr(plugin_instance, 'cleanup'):
               try:
                   plugin_instance.cleanup()
               except Exception as e:
                   logger.warning(
                       "plugin_cleanup_failed",
                       plugin_name=plugin_name,
                       error=str(e)
                   )

           # Remove from registry
           del self._loaded_plugins[plugin_name_lower]
           del self._plugin_metadata[plugin_name_lower]

           logger.info(
               "plugin_unloaded",
               plugin_name=plugin_name
           )

       def reload_plugin(self, plugin_name: str) -> None:
           """Reload a plugin by name."""
           plugin_name_lower = plugin_name.lower()

           if plugin_name_lower not in self._plugin_metadata:
               raise PluginNotFoundError(
                   f"Plugin '{plugin_name}' is not loaded"
               )

           # Get current metadata
           metadata = self._plugin_metadata[plugin_name_lower]

           # Unload
           self.unload_plugin(plugin_name)

           # Reload metadata (in case plugin.yaml changed)
           # This requires access to PluginDiscovery
           # For now, use existing metadata

           # Load again
           self.load_plugin(metadata)

           logger.info(
               "plugin_reloaded",
               plugin_name=plugin_name
           )

       def get_loaded_plugin(self, plugin_name: str) -> Any:
           """Get a loaded plugin instance."""
           plugin_name_lower = plugin_name.lower()

           if plugin_name_lower not in self._loaded_plugins:
               raise PluginNotFoundError(
                   f"Plugin '{plugin_name}' is not loaded. "
                   f"Loaded plugins: {list(self._loaded_plugins.keys())}"
               )

           return self._loaded_plugins[plugin_name_lower]

       def is_loaded(self, plugin_name: str) -> bool:
           """Check if plugin is loaded."""
           return plugin_name.lower() in self._loaded_plugins

       def list_loaded_plugins(self) -> List[str]:
           """List all loaded plugins."""
           return sorted(self._loaded_plugins.keys())

       def load_all_enabled(
           self,
           discovered_plugins: List[PluginMetadata]
       ) -> Dict[str, str]:
           """Load all enabled plugins from discovered list.

           Returns dict mapping plugin_name to status:
           - "loaded": Successfully loaded
           - "skipped": Disabled in metadata
           - "failed": Load error (with message)
           """
           results = {}

           for metadata in discovered_plugins:
               if not metadata.enabled:
                   results[metadata.name] = "skipped (disabled)"
                   continue

               try:
                   self.load_plugin(metadata)
                   results[metadata.name] = "loaded"
               except Exception as e:
                   results[metadata.name] = f"failed: {e}"
                   logger.error(
                       "plugin_load_failed",
                       plugin_name=metadata.name,
                       error=str(e),
                       exc_info=True
                   )

           return results

       def unload_all(self) -> None:
           """Unload all loaded plugins."""
           # Get list of plugin names (copy to avoid modification during iteration)
           plugin_names = list(self._loaded_plugins.keys())

           for plugin_name in plugin_names:
               try:
                   self.unload_plugin(plugin_name)
               except Exception as e:
                   logger.error(
                       "plugin_unload_failed",
                       plugin_name=plugin_name,
                       error=str(e)
                   )
   ```

2. **Plugin interface contract**:
   ```python
   # Optional methods that plugins can implement

   class BasePlugin:
       """Base class for plugins (optional but recommended)."""

       def initialize(self) -> bool:
           """Initialize plugin after loading.

           Called immediately after plugin instantiation.
           Return True for success, False to abort loading.

           Returns:
               True if initialization successful, False otherwise
           """
           return True

       def cleanup(self) -> None:
           """Cleanup plugin before unloading.

           Called before plugin is removed from registry.
           Should release resources, close connections, etc.
           """
           pass
   ```

3. **Integration with PluginManager** (created later):
   ```python
   class PluginManager:
       """High-level plugin management."""

       def __init__(self, config_loader):
           self.discovery = PluginDiscovery(config_loader)
           self.loader = PluginLoader()

       def discover_and_load_all(self) -> Dict[str, str]:
           """Discover and load all plugins."""
           plugin_dirs = self.discovery.get_plugin_dirs()
           discovered = self.discovery.discover_plugins(plugin_dirs)
           results = self.loader.load_all_enabled(discovered)
           return results
   ```

---

## Dependencies

- **Depends On**:
  - Story 4.1 complete (PluginDiscovery and PluginMetadata)

- **Blocks**:
  - Story 4.3 (Agent plugins need loader)
  - Story 4.4 (Workflow plugins need loader)
  - Story 4.5 (Extension points need loaded plugins)

---

## Definition of Done

- [ ] PluginLoader class < 300 lines
- [ ] All IPluginLoader methods implemented
- [ ] Plugin lifecycle hooks functional (initialize, cleanup)
- [ ] Dynamic import working for nested modules
- [ ] 85%+ test coverage for loader
- [ ] All existing tests pass (100%)
- [ ] Integration test loads and unloads real plugin
- [ ] Error handling comprehensive
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/plugins/loader.py`
2. `gao_dev/plugins/base_plugin.py` (optional base class)
3. `tests/plugins/test_loader.py`
4. `tests/plugins/fixtures/lifecycle_plugin/` (test plugin with hooks)

---

## Files to Modify

1. `gao_dev/plugins/__init__.py` - Export PluginLoader
2. `tests/plugins/fixtures/valid_agent_plugin/agent.py` - Add lifecycle hooks

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.1 - Plugin Discovery System
- **Next Story**: Story 4.3 - Create Plugin API for Agents
- **Interface**: `gao_dev/core/interfaces/plugin.py` (IPluginLoader)
- **Dependencies**: Story 4.1 (PluginMetadata, PluginDiscovery)

---

## Test Plan

### Unit Tests

1. **Test successful plugin loading**:
   - Load valid plugin
   - Verify instance stored
   - Verify is_loaded returns True

2. **Test plugin with initialize hook**:
   - Plugin with initialize() that returns True
   - Plugin with initialize() that returns False
   - Plugin with initialize() that raises exception

3. **Test plugin unloading**:
   - Unload loaded plugin
   - Verify cleanup() called
   - Verify is_loaded returns False

4. **Test plugin reload**:
   - Load, modify, reload plugin
   - Verify new version loaded

5. **Test error handling**:
   - Import error (missing module)
   - Missing class in module
   - Invalid plugin (doesn't implement interface)
   - Already loaded (DuplicatePluginError)
   - Not loaded (PluginNotFoundError)

### Integration Tests

1. **End-to-end loading**:
   - Discover plugins
   - Load all enabled
   - Get plugin instance
   - Use plugin
   - Unload plugin

---

## Security Considerations

- Validate plugin implements expected interface before use
- Handle malicious plugins gracefully (exceptions, errors)
- Log all plugin operations for audit trail
- Don't expose sys.path modifications beyond load operation
- Cleanup resources even if errors occur

---

## Notes

- Plugin loading is synchronous (async in future if needed)
- Plugins must be thread-safe (not enforced yet)
- Plugin sandboxing handled in Story 4.6
- Plugin dependencies handled in Story 4.6
