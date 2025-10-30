"""Plugin discovery implementation."""

import yaml
from pathlib import Path
from typing import List
import structlog

from ..core.interfaces.plugin import IPluginDiscovery
from .models import PluginMetadata, PluginType
from .exceptions import PluginValidationError

logger = structlog.get_logger(__name__)


class PluginDiscovery(IPluginDiscovery):
    """Discovers plugins from configured directories.

    Scans plugin directories, validates plugin structure, loads metadata,
    and returns list of discovered plugins ready for loading.

    This class only handles discovery and metadata extraction - it does NOT
    execute any plugin code. Plugin loading is handled separately in Story 4.2.

    Attributes:
        config_loader: Configuration loader for accessing plugin settings
    """

    def __init__(self, config_loader):
        """Initialize with config loader.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader

    def discover_plugins(self, plugin_dirs: List[Path]) -> List[PluginMetadata]:
        """Discover all valid plugins in given directories.

        Scans each directory for subdirectories that contain valid plugins
        (have __init__.py and plugin.yaml). Loads and validates metadata
        for each valid plugin.

        Args:
            plugin_dirs: List of directories to scan for plugins

        Returns:
            List of discovered plugin metadata

        Note:
            Invalid plugins are logged and skipped, not raised as errors
        """
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
                            plugin_version=metadata.version,
                            plugin_path=str(item)
                        )
                    except PluginValidationError as e:
                        logger.warning(
                            "plugin_validation_failed",
                            plugin_path=str(item),
                            error=str(e)
                        )
                    except Exception as e:
                        logger.error(
                            "plugin_discovery_error",
                            plugin_path=str(item),
                            error=str(e),
                            exc_info=True
                        )
                else:
                    logger.debug(
                        "invalid_plugin_structure",
                        plugin_path=str(item)
                    )

        logger.info(
            "plugin_discovery_complete",
            plugins_found=len(discovered),
            plugin_names=[p.name for p in discovered]
        )

        return discovered

    def is_valid_plugin(self, plugin_path: Path) -> bool:
        """Check if path contains a valid plugin.

        A valid plugin must:
        1. Be a directory
        2. Contain __init__.py (Python package)
        3. Contain plugin.yaml (metadata file)

        Args:
            plugin_path: Path to potential plugin directory

        Returns:
            True if valid plugin structure, False otherwise
        """
        # Must be a directory
        if not plugin_path.is_dir():
            return False

        # Must have __init__.py (Python package)
        init_file = plugin_path / "__init__.py"
        if not init_file.exists():
            logger.debug(
                "plugin_missing_init",
                plugin_path=str(plugin_path)
            )
            return False

        # Must have plugin.yaml (metadata)
        metadata_file = plugin_path / "plugin.yaml"
        if not metadata_file.exists():
            logger.debug(
                "plugin_missing_metadata",
                plugin_path=str(plugin_path)
            )
            return False

        return True

    def load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Load metadata from plugin directory.

        Reads plugin.yaml, parses it, and creates PluginMetadata object
        with validation.

        Args:
            plugin_path: Path to plugin directory

        Returns:
            Plugin metadata object

        Raises:
            PluginValidationError: If metadata is invalid or cannot be parsed
        """
        metadata_file = plugin_path / "plugin.yaml"

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise PluginValidationError(
                    f"plugin.yaml must contain a YAML dictionary, got {type(data)}"
                )

            # Parse plugin type
            plugin_type_str = data.get('type', '').lower()
            try:
                plugin_type = PluginType(plugin_type_str)
            except ValueError:
                valid_types = [t.value for t in PluginType]
                raise PluginValidationError(
                    f"Invalid plugin type '{plugin_type_str}'. "
                    f"Must be one of: {valid_types}"
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
                f"Invalid YAML in {metadata_file}: {e}"
            ) from e
        except OSError as e:
            raise PluginValidationError(
                f"Failed to read {metadata_file}: {e}"
            ) from e

    def get_plugin_dirs(self) -> List[Path]:
        """Get plugin directories from configuration.

        Reads plugin directories from config and ensures they exist.
        Creates directories if they don't exist.

        Returns:
            List of absolute paths to plugin directories
        """
        config = self.config_loader.load_config()
        plugin_config = config.get('plugins', {})

        if not plugin_config.get('enabled', True):
            logger.info("plugins_disabled_in_config")
            return []

        directories = plugin_config.get('directories', ['./plugins'])

        # Convert to absolute paths and create if needed
        plugin_dirs = []
        for dir_str in directories:
            # Expand user home directory and resolve to absolute path
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
