"""
ChecklistLoader for GAO-Dev.

Loads, validates, and resolves checklist inheritance from YAML files,
providing the core infrastructure for the checklist system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import structlog
import yaml

from gao_dev.core.checklists.exceptions import (
    ChecklistInheritanceError,
    ChecklistNotFoundError,
    ChecklistValidationError,
)
from gao_dev.core.checklists.models import Checklist, ChecklistItem
from gao_dev.core.checklists.schema_validator import ChecklistSchemaValidator

logger = structlog.get_logger(__name__)


class ChecklistLoader:
    """
    Load and validate checklists from YAML files.

    Supports:
    - Loading from multiple directories (plugins, project, core)
    - Schema validation using JSON Schema
    - Inheritance resolution via 'extends' mechanism
    - Circular dependency detection
    - Performance-optimized caching
    - Plugin integration for custom checklists
    """

    def __init__(
        self,
        checklist_dirs: List[Path],
        schema_path: Path,
        plugin_manager: Optional["ChecklistPluginManager"] = None,
    ):
        """
        Initialize the checklist loader.

        Args:
            checklist_dirs: List of directories to search for core checklists
                           (searched in order: first match wins)
            schema_path: Path to JSON Schema file for validation
            plugin_manager: Optional plugin manager for loading plugin checklists

        Example:
            >>> from pathlib import Path
            >>> from gao_dev.core.checklists.plugin_manager import ChecklistPluginManager
            >>> dirs = [Path("gao_dev/config/checklists")]
            >>> schema = Path("gao_dev/config/schemas/checklist_schema.json")
            >>> plugin_mgr = ChecklistPluginManager(Path("plugins"))
            >>> loader = ChecklistLoader(dirs, schema, plugin_mgr)
        """
        self.checklist_dirs = checklist_dirs
        self.validator = ChecklistSchemaValidator(schema_path)
        self.plugin_manager = plugin_manager
        self._cache: Dict[str, Checklist] = {}
        self._source_map: Dict[str, str] = {}  # checklist_name -> source

    def load_checklist(self, name: str) -> Checklist:
        """
        Load checklist by name (e.g., 'testing/unit-test-standards').

        Search order:
        1. Plugin checklists (by priority - highest first)
        2. Core checklists

        Args:
            name: Checklist name (relative path without .yaml extension)

        Returns:
            Loaded and validated Checklist instance

        Raises:
            ChecklistNotFoundError: If checklist file cannot be found
            ChecklistValidationError: If checklist fails schema validation
            ChecklistInheritanceError: If circular inheritance detected

        Example:
            >>> loader = ChecklistLoader(dirs, schema)
            >>> checklist = loader.load_checklist("testing/unit-test-standards")
            >>> print(f"Loaded: {checklist.name} with {len(checklist.items)} items")
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Search plugin directories first (by priority)
        if self.plugin_manager:
            for directory, plugin_name, priority in (
                self.plugin_manager.get_all_checklist_directories()
            ):
                # Skip disabled plugins
                if not self.plugin_manager.is_plugin_enabled(plugin_name):
                    continue

                checklist_path = directory / f"{name}.yaml"
                if checklist_path.exists():
                    logger.info(
                        "loading_plugin_checklist",
                        name=name,
                        plugin=plugin_name,
                        priority=priority,
                    )

                    # Load and validate
                    with open(checklist_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    is_valid, errors = self.validator.validate(data)
                    if not is_valid:
                        error_msg = "\n".join(errors)
                        logger.warning(
                            "plugin_checklist_validation_failed",
                            name=name,
                            plugin=plugin_name,
                            errors=error_msg,
                        )
                        continue

                    # Resolve inheritance
                    checklist = self._resolve_inheritance(data, name, set())

                    # Cache and track source
                    self._cache[name] = checklist
                    self._source_map[name] = plugin_name

                    # Call plugin hook
                    plugin = self.plugin_manager.get_plugin(plugin_name)
                    if plugin:
                        try:
                            plugin.on_checklist_loaded(
                                name, {"checklist": data["checklist"]}
                            )
                        except Exception as e:
                            logger.error(
                                "plugin_hook_error",
                                plugin=plugin_name,
                                hook="on_checklist_loaded",
                                error=str(e),
                            )

                    return checklist

        # Fall back to core checklists
        checklist_path = self._find_checklist(name)
        if not checklist_path:
            raise ChecklistNotFoundError(f"Checklist not found: {name}")

        logger.info("loading_core_checklist", name=name)

        # Load YAML
        with open(checklist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Validate against schema
        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise ChecklistValidationError(
                f"Checklist validation failed for {name}:\n{error_msg}"
            )

        # Resolve inheritance (with circular dependency tracking)
        checklist = self._resolve_inheritance(data, name, set())

        # Cache and track source
        self._cache[name] = checklist
        self._source_map[name] = "core"
        return checklist

    def _find_checklist(self, name: str) -> Path:
        """
        Find checklist file in search directories.

        Searches directories in order and returns first match.

        Args:
            name: Checklist name (e.g., 'testing/unit-test-standards')

        Returns:
            Path to checklist file, or None if not found
        """
        for directory in self.checklist_dirs:
            checklist_path = directory / f"{name}.yaml"
            if checklist_path.exists():
                return checklist_path
        return None

    def _resolve_inheritance(
        self, data: dict, name: str, inheritance_chain: Set[str]
    ) -> Checklist:
        """
        Resolve checklist inheritance recursively.

        Args:
            data: Parsed YAML data
            name: Current checklist name (for error messages)
            inheritance_chain: Set of checklist names in the current inheritance chain
                             (used for circular dependency detection)

        Returns:
            Resolved Checklist instance with merged items and metadata

        Raises:
            ChecklistInheritanceError: If circular inheritance detected
        """
        checklist_data = data["checklist"]

        # Circular dependency detection
        if name in inheritance_chain:
            chain_str = " -> ".join(inheritance_chain) + f" -> {name}"
            raise ChecklistInheritanceError(
                f"Circular inheritance detected: {chain_str}"
            )

        # Base case: no inheritance
        if "extends" not in checklist_data:
            return self._parse_checklist(checklist_data)

        # Load parent (recursively)
        parent_name = checklist_data["extends"]
        new_chain = inheritance_chain | {name}
        parent = self._load_parent(parent_name, new_chain)

        # Merge items: parent items + child items (child overrides same ID)
        child_items_data = checklist_data.get("items", [])
        merged_items = self._merge_items(parent.items, child_items_data)

        # Merge metadata (child overrides parent)
        merged_metadata = {**parent.metadata, **checklist_data.get("metadata", {})}

        # Return merged checklist
        return Checklist(
            name=checklist_data["name"],
            category=checklist_data["category"],
            version=checklist_data["version"],
            description=checklist_data.get("description", parent.description),
            items=merged_items,
            metadata=merged_metadata,
        )

    def _load_parent(self, parent_name: str, inheritance_chain: Set[str]) -> Checklist:
        """
        Load parent checklist with inheritance tracking.

        Args:
            parent_name: Name of parent checklist
            inheritance_chain: Current inheritance chain for circular detection

        Returns:
            Loaded parent Checklist

        Raises:
            ChecklistNotFoundError: If parent checklist not found
            ChecklistInheritanceError: If circular inheritance detected
        """
        # Check cache first
        if parent_name in self._cache:
            return self._cache[parent_name]

        # Find and load parent
        parent_path = self._find_checklist(parent_name)
        if not parent_path:
            raise ChecklistNotFoundError(
                f"Parent checklist not found: {parent_name}"
            )

        with open(parent_path, "r", encoding="utf-8") as f:
            parent_data = yaml.safe_load(f)

        # Validate parent
        is_valid, errors = self.validator.validate(parent_data)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise ChecklistValidationError(
                f"Parent checklist validation failed for {parent_name}:\n{error_msg}"
            )

        # Resolve parent's inheritance recursively
        parent = self._resolve_inheritance(parent_data, parent_name, inheritance_chain)

        # Cache parent
        self._cache[parent_name] = parent
        return parent

    def _merge_items(
        self, parent_items: List[ChecklistItem], child_items_data: List[dict]
    ) -> List[ChecklistItem]:
        """
        Merge parent and child checklist items.

        Child items with the same ID as parent items override the parent item.
        Child items with new IDs are appended.

        Args:
            parent_items: List of ChecklistItem from parent
            child_items_data: List of item dictionaries from child

        Returns:
            Merged list of ChecklistItem instances
        """
        # Parse child items
        child_items = [self._parse_item(item_data) for item_data in child_items_data]

        # Create merged items dict (ID -> item)
        merged_dict: Dict[str, ChecklistItem] = {}

        # Add parent items
        for item in parent_items:
            merged_dict[item.id] = item

        # Add/override with child items
        for item in child_items:
            merged_dict[item.id] = item

        # Return as list (preserving order: parent items first, then new child items)
        result = []
        parent_ids = {item.id for item in parent_items}
        {item.id for item in child_items}

        # Add parent items (potentially overridden by child)
        for parent_item in parent_items:
            result.append(merged_dict[parent_item.id])

        # Add new child items (not in parent)
        for child_item in child_items:
            if child_item.id not in parent_ids:
                result.append(child_item)

        return result

    def _parse_checklist(self, checklist_data: dict) -> Checklist:
        """
        Parse checklist data into Checklist instance.

        Args:
            checklist_data: Dictionary from YAML

        Returns:
            Checklist instance
        """
        items = [self._parse_item(item_data) for item_data in checklist_data["items"]]

        return Checklist(
            name=checklist_data["name"],
            category=checklist_data["category"],
            version=checklist_data["version"],
            description=checklist_data.get("description"),
            items=items,
            metadata=checklist_data.get("metadata", {}),
        )

    def _parse_item(self, item_data: dict) -> ChecklistItem:
        """
        Parse item data into ChecklistItem instance.

        Args:
            item_data: Dictionary from YAML

        Returns:
            ChecklistItem instance
        """
        return ChecklistItem(
            id=item_data["id"],
            text=item_data["text"],
            severity=item_data["severity"],
            category=item_data.get("category"),
            help_text=item_data.get("help_text"),
            references=item_data.get("references", []),
        )

    def render_checklist(self, checklist: Checklist) -> str:
        """
        Render checklist as markdown format.

        Args:
            checklist: Checklist instance to render

        Returns:
            Markdown-formatted checklist string

        Example:
            >>> loader = ChecklistLoader(dirs, schema)
            >>> checklist = loader.load_checklist("testing/unit-test-standards")
            >>> markdown = loader.render_checklist(checklist)
            >>> print(markdown)
        """
        lines = [f"# {checklist.name}\n"]

        if checklist.description:
            lines.append(f"{checklist.description}\n")

        for item in checklist.items:
            lines.append(f"- [ ] **[{item.severity.upper()}]** {item.text}")
            if item.help_text:
                lines.append(f"  - {item.help_text}")

        return "\n".join(lines)

    def get_checklist_source(self, name: str) -> str:
        """
        Get source of checklist (core or plugin name).

        Args:
            name: Checklist name

        Returns:
            "core" or plugin name, or "unknown" if not loaded

        Example:
            >>> loader = ChecklistLoader(dirs, schema, plugin_mgr)
            >>> checklist = loader.load_checklist("contract-review")
            >>> source = loader.get_checklist_source("contract-review")
            >>> print(f"Loaded from: {source}")
        """
        return self._source_map.get(name, "unknown")

    def list_checklists(self) -> List[Tuple[str, str]]:
        """
        Discover all available checklists with their sources.

        Recursively searches all checklist directories (core and plugins) for .yaml files.

        Returns:
            List of tuples: (checklist_name, source)
            where source is "core" or plugin name

        Example:
            >>> loader = ChecklistLoader(dirs, schema, plugin_mgr)
            >>> for name, source in loader.list_checklists():
            ...     print(f"{name} (from {source})")
        """
        checklists_dict: Dict[str, str] = {}

        # Core checklists first (lowest priority)
        for directory in self.checklist_dirs:
            if not directory.exists():
                continue
            for yaml_file in directory.rglob("*.yaml"):
                rel_path = yaml_file.relative_to(directory)
                # Convert to forward slashes and remove .yaml extension
                name = str(rel_path.with_suffix("")).replace("\\", "/")
                checklists_dict[name] = "core"

        # Plugin checklists (can override core)
        if self.plugin_manager:
            # Process in reverse priority order (lowest to highest)
            # so highest priority wins
            directories = self.plugin_manager.get_all_checklist_directories()
            for directory, plugin_name, priority in reversed(directories):
                # Skip disabled plugins
                if not self.plugin_manager.is_plugin_enabled(plugin_name):
                    continue

                if not directory.exists():
                    continue

                for yaml_file in directory.rglob("*.yaml"):
                    rel_path = yaml_file.relative_to(directory)
                    name = str(rel_path.with_suffix("")).replace("\\", "/")
                    # Override if already exists (higher priority)
                    checklists_dict[name] = plugin_name

        # Convert to sorted list of tuples
        return sorted(checklists_dict.items(), key=lambda x: x[0])
