# Story 14.5: Checklist Plugin Support

**Epic:** 14 - Checklist Plugin System
**Story Points:** 3 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Extend plugin system to support custom checklist loading from plugins. This enables domain-specific plugins (legal, ops, research) to provide their own checklists that integrate seamlessly with the core system. This story is critical for making GAO-Dev truly domain-agnostic and extensible across different organizational teams.

---

## Business Value

This story enables the plugin ecosystem that makes GAO-Dev adaptable to any domain:

- **Domain Customization**: Legal, ops, research teams can define their own quality standards
- **Reusability**: Share checklist plugins across teams and organizations
- **Extensibility**: Add new domains without modifying core system
- **Override Capability**: Customize core checklists for specific organizational needs
- **Separation of Concerns**: Domain-specific quality standards separate from core infrastructure
- **Plugin Marketplace**: Prepares for future plugin sharing and distribution

---

## Acceptance Criteria

### Plugin Interface
- [ ] `ChecklistPlugin` base class defined in `gao_dev/plugins/checklist_plugin.py`
  - Inherits from `BasePlugin` (Epic 10 plugin system)
  - Abstract method `get_checklist_directories()` returns list of paths
  - Abstract method `get_checklist_metadata()` returns plugin info
  - Optional method `validate_checklist()` for custom validation
- [ ] Plugin lifecycle hooks:
  - `on_checklist_loaded()` - Called after checklist loaded
  - `on_checklist_executed()` - Called after execution
  - `on_checklist_failed()` - Called on execution failure
- [ ] Plugin checklists discovered on startup via discovery mechanism
- [ ] Plugin priority system for override order
- [ ] Unit tests for ChecklistPlugin base class

### Integration with ChecklistLoader
- [ ] `ChecklistLoader` extended to search plugin directories
  - Core checklists loaded first (baseline)
  - Plugin checklists loaded second (override/extend)
  - Clear precedence rules documented
- [ ] Plugin checklist directories searched in priority order
  - Higher priority plugins override lower priority
  - Same-name checklists: last loaded wins
- [ ] Validation identical for core and plugin checklists
  - Schema validation enforced
  - Invalid plugin checklists logged but don't break system
- [ ] `list_checklists()` shows source (core vs plugin name)
- [ ] `get_checklist_source(name)` returns which plugin provided it
- [ ] Unit tests for plugin integration

### Discovery & Registration
- [ ] `ChecklistPluginManager` class manages plugin lifecycle
  - Auto-discovery of plugins in plugins/ directory
  - Manual registration via API
  - Plugin enable/disable capability
- [ ] Plugin metadata validation:
  - Required fields: name, version, author, checklist_directories
  - Optional fields: description, dependencies, priority
- [ ] Dependency resolution between plugins
  - Plugin can declare dependencies on other plugins
  - Load order respects dependencies
- [ ] Unit tests for discovery and registration

### Example Legal Team Plugin
- [ ] Complete working example in `docs/examples/legal-team-plugin/`
- [ ] Legal checklists created:
  - `contract-review.yaml` - Contract review checklist
  - `compliance-check.yaml` - Regulatory compliance
  - `legal-review.yaml` - Legal document review
  - `data-privacy.yaml` - GDPR/privacy compliance
- [ ] Plugin structure demonstrates best practices:
  - Clear directory structure
  - Comprehensive metadata
  - Example usage documentation
  - Unit tests for plugin
- [ ] Example plugin tested end-to-end with real workflow
- [ ] Example shows override of core checklist

### Override Behavior
- [ ] Override rules clearly defined and documented:
  - Plugin checklists can override core checklists by name
  - Plugin checklists can extend core checklists (inheritance)
  - Multiple plugins can provide same checklist (priority wins)
- [ ] `extends` keyword in plugin checklist references core checklist
- [ ] Merge strategy for extended checklists:
  - Plugin items appended to core items
  - Plugin items can override core items by ID
  - Categories merged intelligently
- [ ] Override warnings logged for visibility
- [ ] Unit tests for all override scenarios

### Performance
- [ ] Plugin discovery <500ms on startup
- [ ] Checklist loading from plugins <10ms per checklist (cached)
- [ ] No performance degradation with 10+ plugins loaded

---

## Technical Notes

### ChecklistPlugin Base Class

```python
# gao_dev/plugins/checklist_plugin.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional
from gao_dev.plugins.base_plugin import BasePlugin

class ChecklistPlugin(BasePlugin, ABC):
    """
    Base class for checklist plugins.

    Checklist plugins provide domain-specific checklists that extend
    or override core checklists.

    Example:
        class LegalTeamPlugin(ChecklistPlugin):
            def get_checklist_directories(self) -> List[Path]:
                return [Path(__file__).parent / "checklists"]

            def get_checklist_metadata(self) -> Dict:
                return {
                    "name": "legal-team",
                    "version": "1.0.0",
                    "author": "Legal Team",
                    "description": "Legal compliance checklists",
                    "priority": 100  # Higher priority overrides lower
                }
    """

    @abstractmethod
    def get_checklist_directories(self) -> List[Path]:
        """
        Return list of directories containing checklist YAML files.

        Returns:
            List of Path objects to directories with checklists

        Example:
            return [
                Path(__file__).parent / "checklists" / "legal",
                Path(__file__).parent / "checklists" / "compliance"
            ]
        """
        pass

    @abstractmethod
    def get_checklist_metadata(self) -> Dict:
        """
        Return metadata about this plugin.

        Required fields:
            - name: Plugin name (unique identifier)
            - version: Semantic version (e.g., "1.0.0")
            - author: Plugin author

        Optional fields:
            - description: Plugin description
            - dependencies: List of plugin names this depends on
            - priority: Override priority (default: 0, higher wins)
            - checklist_prefix: Prefix for all checklists (e.g., "legal-")

        Returns:
            Dictionary with metadata
        """
        pass

    def validate_checklist(self, checklist: Dict) -> bool:
        """
        Optional: Custom validation for plugin checklists.

        Override to add domain-specific validation beyond schema.

        Args:
            checklist: Parsed checklist dictionary

        Returns:
            True if valid, False otherwise
        """
        return True

    def on_checklist_loaded(self, checklist_name: str, checklist: Dict):
        """Hook called after checklist loaded from this plugin."""
        pass

    def on_checklist_executed(self, checklist_name: str, execution_id: int, status: str):
        """Hook called after checklist execution completes."""
        pass

    def on_checklist_failed(self, checklist_name: str, execution_id: int, errors: List[str]):
        """Hook called when checklist execution fails."""
        pass
```

### ChecklistPluginManager

```python
# gao_dev/core/checklists/plugin_manager.py
from pathlib import Path
from typing import List, Dict, Optional
import structlog
from gao_dev.plugins.checklist_plugin import ChecklistPlugin
from gao_dev.plugins.discovery import discover_plugins

logger = structlog.get_logger()

class ChecklistPluginManager:
    """Manages checklist plugin lifecycle."""

    def __init__(self, plugins_dir: Path):
        """
        Initialize plugin manager.

        Args:
            plugins_dir: Directory to search for plugins
        """
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, ChecklistPlugin] = {}
        self._plugin_priority: Dict[str, int] = {}

    def discover_plugins(self) -> List[ChecklistPlugin]:
        """
        Discover all checklist plugins in plugins directory.

        Returns:
            List of discovered ChecklistPlugin instances
        """
        discovered = discover_plugins(
            self.plugins_dir,
            plugin_type=ChecklistPlugin
        )

        for plugin in discovered:
            metadata = plugin.get_checklist_metadata()
            name = metadata.get("name")
            priority = metadata.get("priority", 0)

            self.plugins[name] = plugin
            self._plugin_priority[name] = priority

            logger.info(
                "checklist_plugin_discovered",
                plugin_name=name,
                version=metadata.get("version"),
                priority=priority
            )

        return discovered

    def get_plugin(self, name: str) -> Optional[ChecklistPlugin]:
        """Get plugin by name."""
        return self.plugins.get(name)

    def get_all_checklist_directories(self) -> List[tuple[Path, str, int]]:
        """
        Get all checklist directories from all plugins.

        Returns:
            List of tuples: (directory_path, plugin_name, priority)
            Sorted by priority (highest first)
        """
        directories = []
        for name, plugin in self.plugins.items():
            priority = self._plugin_priority[name]
            for directory in plugin.get_checklist_directories():
                directories.append((directory, name, priority))

        # Sort by priority descending (highest priority first)
        directories.sort(key=lambda x: x[2], reverse=True)
        return directories

    def validate_dependencies(self) -> bool:
        """
        Validate all plugin dependencies are met.

        Returns:
            True if all dependencies satisfied
        """
        for name, plugin in self.plugins.items():
            metadata = plugin.get_checklist_metadata()
            dependencies = metadata.get("dependencies", [])

            for dep in dependencies:
                if dep not in self.plugins:
                    logger.error(
                        "plugin_dependency_missing",
                        plugin=name,
                        missing_dependency=dep
                    )
                    return False

        return True
```

### Enhanced ChecklistLoader Integration

```python
# Extend existing ChecklistLoader from Story 14.2
from gao_dev.core.checklists.plugin_manager import ChecklistPluginManager

class ChecklistLoader:
    """Loads and validates checklists from YAML files (ENHANCED with plugins)."""

    def __init__(
        self,
        core_dir: Path,
        schema_path: Path,
        plugin_manager: Optional[ChecklistPluginManager] = None
    ):
        """
        Initialize loader.

        Args:
            core_dir: Directory with core checklists
            schema_path: Path to JSON schema
            plugin_manager: Optional plugin manager for plugin checklists
        """
        self.core_dir = core_dir
        self.schema_path = schema_path
        self.plugin_manager = plugin_manager
        self._cache: Dict[str, Dict] = {}
        self._source_map: Dict[str, str] = {}  # checklist_name -> source (core/plugin_name)

    def load_checklist(self, name: str) -> Dict:
        """
        Load checklist by name.

        Search order:
        1. Plugin checklists (by priority)
        2. Core checklists

        Args:
            name: Checklist name (without .yaml extension)

        Returns:
            Loaded and validated checklist dictionary
        """
        if name in self._cache:
            return self._cache[name]

        # Search plugin directories first (by priority)
        if self.plugin_manager:
            for directory, plugin_name, priority in self.plugin_manager.get_all_checklist_directories():
                checklist_path = directory / f"{name}.yaml"
                if checklist_path.exists():
                    logger.info(
                        "loading_plugin_checklist",
                        name=name,
                        plugin=plugin_name,
                        priority=priority
                    )
                    checklist = self._load_and_validate(checklist_path)
                    self._cache[name] = checklist
                    self._source_map[name] = plugin_name

                    # Call plugin hook
                    plugin = self.plugin_manager.get_plugin(plugin_name)
                    if plugin:
                        plugin.on_checklist_loaded(name, checklist)

                    return checklist

        # Fall back to core checklist
        core_path = self.core_dir / f"{name}.yaml"
        if core_path.exists():
            logger.info("loading_core_checklist", name=name)
            checklist = self._load_and_validate(core_path)
            self._cache[name] = checklist
            self._source_map[name] = "core"
            return checklist

        raise ValueError(f"Checklist '{name}' not found in core or plugins")

    def get_checklist_source(self, name: str) -> str:
        """
        Get source of checklist (core or plugin name).

        Args:
            name: Checklist name

        Returns:
            "core" or plugin name
        """
        return self._source_map.get(name, "unknown")

    def list_checklists(self) -> List[tuple[str, str]]:
        """
        List all available checklists.

        Returns:
            List of tuples: (checklist_name, source)
        """
        checklists = []

        # Core checklists
        for path in self.core_dir.glob("*.yaml"):
            name = path.stem
            checklists.append((name, "core"))

        # Plugin checklists
        if self.plugin_manager:
            for directory, plugin_name, _ in self.plugin_manager.get_all_checklist_directories():
                for path in directory.glob("*.yaml"):
                    name = path.stem
                    # Only add if not already from higher priority source
                    if name not in [c[0] for c in checklists]:
                        checklists.append((name, plugin_name))

        return checklists
```

### Example Legal Team Plugin

```yaml
# docs/examples/legal-team-plugin/checklists/legal/contract-review.yaml
name: contract-review
category: legal
version: 1.0.0
description: Checklist for reviewing contracts and legal agreements

metadata:
  owner: Legal Team
  review_cadence: quarterly
  compliance_tags:
    - legal
    - compliance
    - gdpr

items:
  - id: contract-parties
    text: Verify all parties are correctly identified with full legal names
    severity: high
    category: parties
    help_text: Check company names, addresses, and registration numbers

  - id: contract-terms
    text: Review and approve all contractual terms and conditions
    severity: high
    category: terms
    help_text: Ensure terms align with company policy and legal requirements

  - id: contract-liability
    text: Verify liability clauses and limitation of liability
    severity: high
    category: liability
    help_text: Check indemnification, warranties, and liability caps

  - id: contract-termination
    text: Review termination clauses and exit procedures
    severity: medium
    category: termination
    help_text: Ensure clear termination rights and procedures

  - id: contract-ip
    text: Verify intellectual property rights and ownership
    severity: high
    category: ip
    help_text: Check IP ownership, licensing, and confidentiality

  - id: contract-compliance
    text: Ensure compliance with applicable laws and regulations
    severity: high
    category: compliance
    help_text: Verify GDPR, data protection, and industry-specific regulations

  - id: contract-signatures
    text: Verify all required signatures and authorities
    severity: high
    category: execution
    help_text: Check signing authority and execution formalities
```

```python
# docs/examples/legal-team-plugin/legal_plugin.py
from pathlib import Path
from typing import List, Dict
from gao_dev.plugins.checklist_plugin import ChecklistPlugin

class LegalTeamPlugin(ChecklistPlugin):
    """Legal team checklist plugin."""

    def get_checklist_directories(self) -> List[Path]:
        """Return legal checklist directories."""
        base = Path(__file__).parent
        return [
            base / "checklists" / "legal",
            base / "checklists" / "compliance"
        ]

    def get_checklist_metadata(self) -> Dict:
        """Return plugin metadata."""
        return {
            "name": "legal-team",
            "version": "1.0.0",
            "author": "GAO Legal Team",
            "description": "Legal and compliance checklists for contract review, GDPR, etc.",
            "priority": 100,  # Override core if needed
            "checklist_prefix": "legal-",
            "dependencies": []
        }

    def on_checklist_executed(self, checklist_name: str, execution_id: int, status: str):
        """Log legal checklist executions for audit."""
        if status == "fail":
            # Could send notification to legal team
            logger.warning(
                "legal_checklist_failed",
                checklist=checklist_name,
                execution_id=execution_id
            )
```

**Files to Create:**
- `gao_dev/plugins/checklist_plugin.py`
- `gao_dev/core/checklists/plugin_manager.py`
- `docs/examples/legal-team-plugin/legal_plugin.py`
- `docs/examples/legal-team-plugin/checklists/legal/contract-review.yaml`
- `docs/examples/legal-team-plugin/checklists/legal/compliance-check.yaml`
- `docs/examples/legal-team-plugin/checklists/legal/legal-review.yaml`
- `docs/examples/legal-team-plugin/checklists/legal/data-privacy.yaml`
- `docs/examples/legal-team-plugin/README.md`
- `tests/plugins/test_checklist_plugin.py`
- `tests/plugins/test_checklist_plugin_manager.py`
- `tests/examples/test_legal_team_plugin.py`

**Dependencies:**
- Story 14.2 (ChecklistLoader) - For integration
- Epic 10 (Plugin System) - For BasePlugin infrastructure

---

## Testing Requirements

### Unit Tests

**ChecklistPlugin Tests:**
- [ ] Test base class methods (abstract enforcement)
- [ ] Test plugin metadata validation
- [ ] Test lifecycle hooks called correctly
- [ ] Test custom validation override

**ChecklistPluginManager Tests:**
- [ ] Test plugin discovery finds all plugins
- [ ] Test plugin registration and retrieval
- [ ] Test priority ordering works correctly
- [ ] Test dependency validation detects missing deps
- [ ] Test get_all_checklist_directories returns correct order

**ChecklistLoader Integration Tests:**
- [ ] Test plugin checklists loaded before core
- [ ] Test same-name checklist override by priority
- [ ] Test source tracking works (core vs plugin)
- [ ] Test list_checklists shows all sources
- [ ] Test cache works correctly with plugins
- [ ] Test invalid plugin checklist doesn't break system

**Legal Team Plugin Tests:**
- [ ] Test plugin loads successfully
- [ ] Test all legal checklists valid
- [ ] Test plugin metadata correct
- [ ] Test legal checklists executable end-to-end

### Integration Tests
- [ ] Load core and plugin checklists together
- [ ] Execute plugin checklist through full workflow
- [ ] Test multiple plugins with priority ordering
- [ ] Test plugin with dependencies
- [ ] Test plugin override of core checklist

### Performance Tests
- [ ] Plugin discovery completes in <500ms
- [ ] Loading 20 plugin checklists <200ms (cached)
- [ ] No performance degradation with 10 plugins

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all classes and methods
- [ ] Plugin developer guide with complete example
- [ ] Checklist discovery mechanism documented
- [ ] Override behavior clearly explained with examples
- [ ] Legal team plugin documented as reference
- [ ] Migration guide for existing custom checklists

---

## Implementation Details

### Development Approach

1. **Phase 1: Plugin Base Class** (Day 1)
   - Create ChecklistPlugin base class
   - Define abstract methods and hooks
   - Write base class tests

2. **Phase 2: Plugin Manager** (Day 1-2)
   - Implement ChecklistPluginManager
   - Add discovery mechanism
   - Implement priority and dependency resolution
   - Write manager tests

3. **Phase 3: ChecklistLoader Integration** (Day 2)
   - Extend ChecklistLoader for plugin support
   - Implement search order and override logic
   - Add source tracking
   - Write integration tests

4. **Phase 4: Example Legal Plugin** (Day 3)
   - Create complete legal team plugin
   - Write 4 legal checklists
   - Document plugin as example
   - Test end-to-end

### Quality Gates
- All unit tests passing before integration
- Legal team plugin working end-to-end before completion
- Documentation reviewed and approved
- No performance regression

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Legal team plugin working end-to-end
- [ ] Plugin developer guide complete
- [ ] Performance benchmarks met
- [ ] Committed with atomic commit message:
  ```
  feat(epic-14): implement Story 14.5 - Checklist Plugin Support

  - Create ChecklistPlugin base class with lifecycle hooks
  - Implement ChecklistPluginManager with discovery and priority
  - Extend ChecklistLoader to load plugin checklists
  - Add override mechanism with priority-based resolution
  - Create complete legal team plugin example with 4 checklists
  - Add comprehensive unit and integration tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
