"""Permission management for plugins.

This module provides permission management functionality to control what
operations plugins can perform.
"""

from typing import Dict, List, Set
import structlog

from .models import PluginPermission
from .exceptions import PermissionDeniedError

logger = structlog.get_logger(__name__)


class PermissionManager:
    """Manages plugin permissions and access control.

    The PermissionManager tracks which permissions have been granted to
    each plugin and provides methods to check permissions at runtime.

    Plugins must declare required permissions in plugin.yaml:
        permissions:
          - file:read
          - file:write
          - hook:register

    Example:
        ```python
        manager = PermissionManager()

        # Grant permissions from plugin metadata
        manager.grant_permissions("my-plugin", ["file:read", "file:write"])

        # Check permission before operation
        if manager.has_permission("my-plugin", PluginPermission.FILE_READ):
            # Perform file read
            pass

        # Or enforce permission (raises if denied)
        manager.enforce_permission("my-plugin", PluginPermission.FILE_WRITE)
        ```

    Attributes:
        _permissions: Dictionary mapping plugin names to sets of permissions
    """

    def __init__(self):
        """Initialize permission manager with empty permissions."""
        self._permissions: Dict[str, Set[PluginPermission]] = {}

        logger.info("permission_manager_initialized")

    def grant_permissions(
        self,
        plugin_name: str,
        permissions: List[str],
    ) -> None:
        """Grant permissions to a plugin.

        Converts permission strings to PluginPermission enums and stores
        them for the specified plugin. Invalid permissions are logged as
        warnings but don't cause failure.

        Args:
            plugin_name: Name of plugin to grant permissions to
            permissions: List of permission strings (e.g., ["file:read"])

        Example:
            ```python
            manager.grant_permissions(
                "my-plugin",
                ["file:read", "file:write", "hook:register"]
            )
            ```
        """
        if plugin_name not in self._permissions:
            self._permissions[plugin_name] = set()

        granted_count = 0
        for perm_str in permissions:
            try:
                perm = PluginPermission(perm_str)
                self._permissions[plugin_name].add(perm)
                granted_count += 1
            except ValueError:
                logger.warning(
                    "invalid_permission",
                    plugin=plugin_name,
                    permission=perm_str,
                )

        logger.info(
            "permissions_granted",
            plugin=plugin_name,
            count=granted_count,
            permissions=[p.value for p in self._permissions[plugin_name]],
        )

    def has_permission(
        self,
        plugin_name: str,
        operation: PluginPermission,
    ) -> bool:
        """Check if plugin has permission for operation.

        Args:
            plugin_name: Name of plugin to check
            operation: Permission being checked

        Returns:
            True if plugin has permission, False otherwise

        Example:
            ```python
            if manager.has_permission("my-plugin", PluginPermission.FILE_READ):
                print("Plugin can read files")
            ```
        """
        return operation in self._permissions.get(plugin_name, set())

    def enforce_permission(
        self,
        plugin_name: str,
        operation: PluginPermission,
    ) -> None:
        """Enforce that plugin has permission for operation.

        Raises PermissionDeniedError if plugin doesn't have permission.

        Args:
            plugin_name: Name of plugin to check
            operation: Permission being enforced

        Raises:
            PermissionDeniedError: If plugin doesn't have permission

        Example:
            ```python
            # Will raise if permission not granted
            manager.enforce_permission(
                "my-plugin",
                PluginPermission.FILE_WRITE
            )
            ```
        """
        if not self.has_permission(plugin_name, operation):
            logger.error(
                "permission_denied",
                plugin=plugin_name,
                operation=operation.value,
            )
            raise PermissionDeniedError(
                f"Plugin '{plugin_name}' does not have permission '{operation.value}'"
            )

    def get_permissions(self, plugin_name: str) -> List[PluginPermission]:
        """Get list of permissions granted to plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            List of PluginPermission enums granted to plugin

        Example:
            ```python
            perms = manager.get_permissions("my-plugin")
            print(f"Plugin has {len(perms)} permissions")
            ```
        """
        return list(self._permissions.get(plugin_name, set()))

    def revoke_permission(
        self,
        plugin_name: str,
        operation: PluginPermission,
    ) -> bool:
        """Revoke a specific permission from plugin.

        Args:
            plugin_name: Name of plugin
            operation: Permission to revoke

        Returns:
            True if permission was revoked, False if not granted

        Example:
            ```python
            revoked = manager.revoke_permission(
                "my-plugin",
                PluginPermission.FILE_WRITE
            )
            ```
        """
        if plugin_name not in self._permissions:
            return False

        if operation in self._permissions[plugin_name]:
            self._permissions[plugin_name].remove(operation)
            logger.info(
                "permission_revoked",
                plugin=plugin_name,
                permission=operation.value,
            )
            return True

        return False

    def revoke_all_permissions(self, plugin_name: str) -> int:
        """Revoke all permissions from plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Number of permissions revoked

        Example:
            ```python
            count = manager.revoke_all_permissions("my-plugin")
            print(f"Revoked {count} permissions")
            ```
        """
        if plugin_name not in self._permissions:
            return 0

        count = len(self._permissions[plugin_name])
        del self._permissions[plugin_name]

        logger.info(
            "all_permissions_revoked",
            plugin=plugin_name,
            count=count,
        )

        return count

    def list_plugins_with_permission(
        self, operation: PluginPermission
    ) -> List[str]:
        """List all plugins that have a specific permission.

        Args:
            operation: Permission to check for

        Returns:
            List of plugin names with this permission

        Example:
            ```python
            plugins = manager.list_plugins_with_permission(
                PluginPermission.FILE_WRITE
            )
            print(f"{len(plugins)} plugins can write files")
            ```
        """
        return [
            plugin_name
            for plugin_name, perms in self._permissions.items()
            if operation in perms
        ]
