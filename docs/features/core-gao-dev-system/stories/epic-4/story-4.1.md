# Story 4.1: Implement Plugin Discovery System

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Done

---

## User Story

**As a** core developer
**I want** an automated plugin discovery system
**So that** plugins can be found and registered dynamically without manual configuration

---

## Description

Implement a plugin discovery system that scans configured directories, identifies valid plugins, loads their metadata, and prepares them for loading. This is the foundation of the plugin architecture.

**Current State**: No plugin system exists. All agents and workflows are hard-coded into the system.

**Target State**: New `PluginDiscovery` class in `gao_dev/plugins/discovery.py` that scans plugin directories, validates plugin structure, and returns discovered plugin metadata.

---

## Acceptance Criteria

### PluginDiscovery Implementation

- [ ] **Class created**: `gao_dev/plugins/discovery.py`
- [ ] **Implements**: `IPluginDiscovery` interface completely
- [ ] **Size**: < 250 lines
- [ ] **Single responsibility**: Discover and validate plugins

### Core Methods

- [ ] **discover_plugins(plugin_dirs)** -> List[PluginMetadata]
  - Scan each directory in plugin_dirs
  - Identify valid plugin packages (contain __init__.py and plugin.yaml)
  - Load and validate plugin.yaml metadata
  - Return list of PluginMetadata objects
  - Skip invalid plugins with warning logs
  - Handle directory read errors gracefully

- [ ] **is_valid_plugin(plugin_path)** -> bool
  - Check if directory contains required files
  - Validate plugin.yaml structure
  - Verify plugin name follows naming convention
  - Return true if valid, false otherwise

- [ ] **load_plugin_metadata(plugin_path)** -> PluginMetadata
  - Read plugin.yaml file
  - Parse YAML into PluginMetadata dataclass
  - Validate required fields (name, version, type, entry_point)
  - Raise PluginValidationError if invalid
  - Support optional fields (description, author, dependencies)

- [ ] **get_plugin_dirs(config)** -> List[Path]
  - Read plugin directories from config
  - Support multiple plugin directories
  - Create directories if they don't exist
  - Return list of absolute paths

### Plugin Metadata Model

- [ ] **PluginMetadata dataclass** created:
  - name: str (unique plugin identifier)
  - version: str (semantic version)
  - type: PluginType (agent, workflow, methodology, tool)
  - entry_point: str (module path to plugin class)
  - description: Optional[str]
  - author: Optional[str]
  - dependencies: Optional[List[str]]
  - enabled: bool = True

- [ ] **PluginType enum** created:
  - AGENT = "agent"
  - WORKFLOW = "workflow"
  - METHODOLOGY = "methodology"
  - TOOL = "tool"

### Plugin Directory Structure

- [ ] **Standard plugin structure** defined and validated:
  ```
  plugins/
    my_custom_agent/
      __init__.py          # Plugin package marker
      plugin.yaml          # Plugin metadata (REQUIRED)
      agent.py             # Plugin implementation
      README.md            # Documentation (optional)
      requirements.txt     # Dependencies (optional)
  ```

### Plugin Metadata Format

- [ ] **plugin.yaml schema** defined:
  ```yaml
  name: my-custom-agent
  version: 1.0.0
  type: agent
  entry_point: my_custom_agent.agent.MyCustomAgent
  description: "A custom agent for domain-specific tasks"
  author: "John Doe"
  dependencies:
    - numpy>=1.24.0
    - pandas>=2.0.0
  enabled: true
  ```

### Configuration

- [ ] **Plugin config** added to `gao_dev/config/defaults.yaml`:
  ```yaml
  plugins:
    enabled: true
    directories:
      - ./plugins
      - ~/.gao-dev/plugins
    auto_discover: true
  ```

### Testing

- [ ] Unit tests for PluginDiscovery (85%+ coverage)
- [ ] Test valid plugin discovery
- [ ] Test invalid plugin handling
- [ ] Test missing plugin.yaml
- [ ] Test malformed plugin.yaml
- [ ] Test multiple plugin directories
- [ ] Integration tests with sample plugins
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create PluginMetadata model**:
   ```python
   from dataclasses import dataclass, field
   from enum import Enum
   from typing import Optional, List
   from pathlib import Path

   class PluginType(Enum):
       """Types of plugins supported by GAO-Dev."""
       AGENT = "agent"
       WORKFLOW = "workflow"
       METHODOLOGY = "methodology"
       TOOL = "tool"

   @dataclass
   class PluginMetadata:
       """Metadata describing a plugin."""
       name: str
       version: str
       type: PluginType
       entry_point: str
       plugin_path: Path
       description: Optional[str] = None
       author: Optional[str] = None
       dependencies: List[str] = field(default_factory=list)
       enabled: bool = True

       def __post_init__(self):
           """Validate metadata after initialization."""
           if not self.name:
               raise PluginValidationError("Plugin name is required")
           if not self.version:
               raise PluginValidationError("Plugin version is required")
           if not self.entry_point:
               raise PluginValidationError("Plugin entry_point is required")

           # Validate semantic version
           if not self._is_valid_semver(self.version):
               raise PluginValidationError(
                   f"Invalid version '{self.version}'. Must be semantic version (e.g., 1.0.0)"
               )

       @staticmethod
       def _is_valid_semver(version: str) -> bool:
           """Check if version follows semantic versioning."""
           import re
           pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$'
           return bool(re.match(pattern, version))
   ```

2. **Create IPluginDiscovery interface**:
   ```python
   from abc import ABC, abstractmethod
   from typing import List
   from pathlib import Path
   from .models import PluginMetadata

   class IPluginDiscovery(ABC):
       """Interface for plugin discovery."""

       @abstractmethod
       def discover_plugins(self, plugin_dirs: List[Path]) -> List[PluginMetadata]:
           """Discover all valid plugins in given directories."""
           pass

       @abstractmethod
       def is_valid_plugin(self, plugin_path: Path) -> bool:
           """Check if path contains a valid plugin."""
           pass

       @abstractmethod
       def load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
           """Load metadata from plugin directory."""
           pass
   ```

3. **Create PluginDiscovery implementation**:
   ```python
   import yaml
   from pathlib import Path
   from typing import List
   import structlog

   logger = structlog.get_logger(__name__)

   class PluginDiscovery(IPluginDiscovery):
       """
       Discovers plugins from configured directories.

       Scans plugin directories, validates plugin structure, loads metadata,
       and returns list of discovered plugins ready for loading.
       """

       def __init__(self, config_loader):
           """Initialize with config loader."""
           self.config_loader = config_loader

       def discover_plugins(self, plugin_dirs: List[Path]) -> List[PluginMetadata]:
           """Discover all valid plugins in given directories."""
           discovered = []

           for plugin_dir in plugin_dirs:
               if not plugin_dir.exists():
                   logger.warning(
                       "plugin_dir_not_found",
                       plugin_dir=str(plugin_dir)
                   )
                   continue

               # Scan for subdirectories (each is potential plugin)
               for item in plugin_dir.iterdir():
                   if not item.is_dir():
                       continue

                   # Skip hidden directories and __pycache__
                   if item.name.startswith('.') or item.name == '__pycache__':
                       continue

                   # Check if valid plugin
                   if self.is_valid_plugin(item):
                       try:
                           metadata = self.load_plugin_metadata(item)
                           discovered.append(metadata)
                           logger.info(
                               "plugin_discovered",
                               plugin_name=metadata.name,
                               plugin_type=metadata.type.value,
                               plugin_version=metadata.version
                           )
                       except PluginValidationError as e:
                           logger.warning(
                               "plugin_validation_failed",
                               plugin_path=str(item),
                               error=str(e)
                           )
                   else:
                       logger.debug(
                           "invalid_plugin_structure",
                           plugin_path=str(item)
                       )

           logger.info(
               "plugin_discovery_complete",
               plugins_found=len(discovered)
           )

           return discovered

       def is_valid_plugin(self, plugin_path: Path) -> bool:
           """Check if path contains a valid plugin."""
           # Must be a directory
           if not plugin_path.is_dir():
               return False

           # Must have __init__.py (Python package)
           init_file = plugin_path / "__init__.py"
           if not init_file.exists():
               return False

           # Must have plugin.yaml (metadata)
           metadata_file = plugin_path / "plugin.yaml"
           if not metadata_file.exists():
               return False

           return True

       def load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
           """Load metadata from plugin directory."""
           metadata_file = plugin_path / "plugin.yaml"

           try:
               with open(metadata_file, 'r', encoding='utf-8') as f:
                   data = yaml.safe_load(f)

               if not isinstance(data, dict):
                   raise PluginValidationError(
                       f"plugin.yaml must contain a YAML dictionary"
                   )

               # Parse plugin type
               plugin_type_str = data.get('type', '').lower()
               try:
                   plugin_type = PluginType(plugin_type_str)
               except ValueError:
                   raise PluginValidationError(
                       f"Invalid plugin type '{plugin_type_str}'. "
                       f"Must be one of: {[t.value for t in PluginType]}"
                   )

               # Create metadata object (validation in __post_init__)
               metadata = PluginMetadata(
                   name=data.get('name', ''),
                   version=data.get('version', ''),
                   type=plugin_type,
                   entry_point=data.get('entry_point', ''),
                   plugin_path=plugin_path,
                   description=data.get('description'),
                   author=data.get('author'),
                   dependencies=data.get('dependencies', []),
                   enabled=data.get('enabled', True)
               )

               return metadata

           except yaml.YAMLError as e:
               raise PluginValidationError(
                   f"Invalid YAML in plugin.yaml: {e}"
               ) from e
           except OSError as e:
               raise PluginValidationError(
                   f"Failed to read plugin.yaml: {e}"
               ) from e

       def get_plugin_dirs(self) -> List[Path]:
           """Get plugin directories from config."""
           config = self.config_loader.load_config()
           plugin_config = config.get('plugins', {})

           if not plugin_config.get('enabled', True):
               logger.info("plugins_disabled")
               return []

           directories = plugin_config.get('directories', ['./plugins'])

           # Convert to absolute paths and create if needed
           plugin_dirs = []
           for dir_str in directories:
               plugin_dir = Path(dir_str).expanduser().resolve()

               # Create directory if it doesn't exist
               if not plugin_dir.exists():
                   try:
                       plugin_dir.mkdir(parents=True, exist_ok=True)
                       logger.info(
                           "plugin_dir_created",
                           plugin_dir=str(plugin_dir)
                       )
                   except OSError as e:
                       logger.warning(
                           "plugin_dir_creation_failed",
                           plugin_dir=str(plugin_dir),
                           error=str(e)
                       )
                       continue

               plugin_dirs.append(plugin_dir)

           return plugin_dirs
   ```

4. **Create exception classes**:
   ```python
   class PluginError(Exception):
       """Base exception for plugin system."""
       pass

   class PluginValidationError(PluginError):
       """Raised when plugin validation fails."""
       pass

   class PluginNotFoundError(PluginError):
       """Raised when plugin not found."""
       pass

   class PluginLoadError(PluginError):
       """Raised when plugin fails to load."""
       pass
   ```

5. **Update config/defaults.yaml**:
   ```yaml
   plugins:
     enabled: true
     directories:
       - ./plugins
       - ~/.gao-dev/plugins
     auto_discover: true
     security:
       sandboxing: true
       allowed_modules: []
   ```

---

## Dependencies

- **Depends On**:
  - Epic 1 complete (base interfaces)
  - Epic 2 complete (clean architecture)
  - Epic 3 complete (Factory pattern for registration)

- **Blocks**:
  - Story 4.2 (Plugin loading needs discovery)
  - Story 4.3 (Agent plugins need discovery)
  - Story 4.4 (Workflow plugins need discovery)

---

## Definition of Done

- [ ] PluginDiscovery class < 250 lines
- [ ] PluginMetadata model with validation
- [ ] IPluginDiscovery interface defined
- [ ] Plugin directory structure documented
- [ ] plugin.yaml schema defined and validated
- [ ] 85%+ test coverage for discovery
- [ ] All existing tests pass (100%)
- [ ] Integration test discovers sample plugins
- [ ] Configuration added for plugin directories
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/plugins/__init__.py`
2. `gao_dev/plugins/models.py` (PluginMetadata, PluginType)
3. `gao_dev/plugins/discovery.py` (PluginDiscovery class)
4. `gao_dev/plugins/exceptions.py` (Plugin exceptions)
5. `gao_dev/core/interfaces/plugin.py` (IPluginDiscovery)
6. `tests/plugins/__init__.py`
7. `tests/plugins/test_discovery.py`
8. `tests/plugins/fixtures/` (sample plugins for testing)
9. `tests/plugins/fixtures/valid_agent_plugin/`
10. `tests/plugins/fixtures/invalid_plugin/`

---

## Files to Modify

1. `gao_dev/config/defaults.yaml` - Add plugins configuration
2. `README.md` - Add plugin system overview

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Next Story**: Story 4.2 - Implement Plugin Loading and Lifecycle
- **Interface**: `gao_dev/core/interfaces/plugin.py` (IPluginDiscovery)
- **Pattern**: Registry pattern from Epic 3

---

## Test Plan

### Unit Tests

1. **Test valid plugin discovery**:
   - Create sample valid plugin
   - Run discover_plugins()
   - Assert plugin found with correct metadata

2. **Test invalid plugin handling**:
   - Missing __init__.py
   - Missing plugin.yaml
   - Malformed YAML
   - Invalid plugin type
   - Invalid version format

3. **Test multiple directories**:
   - Create plugins in different directories
   - Discover from multiple paths
   - Assert all plugins found

4. **Test disabled plugins**:
   - Set enabled: false in plugin.yaml
   - Assert plugin skipped

### Integration Tests

1. **End-to-end discovery**:
   - Set up test plugin directory
   - Create multiple valid plugins
   - Run full discovery flow
   - Assert correct plugins found

---

## Security Considerations

- Validate all user input (plugin paths, metadata)
- Prevent directory traversal attacks
- Validate semantic versioning format
- Log security-relevant events
- Don't execute plugin code during discovery (only metadata)

---

## Notes

- Discovery is read-only - no plugin code execution
- Plugin loading happens in Story 4.2
- Security/sandboxing happens in Story 4.6
- Focus on metadata extraction and validation
