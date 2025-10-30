"""Tests for plugin security system."""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from gao_dev.plugins import (
    PluginPermission,
    ValidationResult,
    ResourceUsage,
    PermissionManager,
    ResourceMonitor,
    PluginSandbox,
    PluginMetadata,
    PluginType,
    PermissionDeniedError,
    PluginTimeoutError,
    ResourceLimitError,
)


# Test PluginPermission Enum

class TestPluginPermission:
    """Tests for PluginPermission enum."""

    def test_permission_enum_values(self):
        """Test that all expected permissions exist."""
        assert PluginPermission.FILE_READ.value == "file:read"
        assert PluginPermission.FILE_WRITE.value == "file:write"
        assert PluginPermission.FILE_DELETE.value == "file:delete"
        assert PluginPermission.NETWORK_REQUEST.value == "network:request"
        assert PluginPermission.SUBPROCESS_EXECUTE.value == "subprocess:execute"
        assert PluginPermission.HOOK_REGISTER.value == "hook:register"
        assert PluginPermission.CONFIG_READ.value == "config:read"
        assert PluginPermission.CONFIG_WRITE.value == "config:write"
        assert PluginPermission.DATABASE_READ.value == "database:read"
        assert PluginPermission.DATABASE_WRITE.value == "database:write"

    def test_permission_from_string(self):
        """Test creating permission from string."""
        perm = PluginPermission("file:read")
        assert perm == PluginPermission.FILE_READ


# Test Models

class TestModels:
    """Tests for security models."""

    def test_validation_result_valid(self):
        """Test ValidationResult for valid plugin."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        result = ValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
        )
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_resource_usage_defaults(self):
        """Test ResourceUsage default values."""
        usage = ResourceUsage()
        assert usage.cpu_percent == 0.0
        assert usage.memory_mb == 0.0
        assert usage.start_time == 0.0


# Test PermissionManager

class TestPermissionManager:
    """Tests for PermissionManager."""

    @pytest.fixture
    def manager(self):
        """Create PermissionManager instance."""
        return PermissionManager()

    def test_grant_permissions(self, manager):
        """Test granting permissions to plugin."""
        manager.grant_permissions("test-plugin", ["file:read", "file:write"])

        assert manager.has_permission("test-plugin", PluginPermission.FILE_READ)
        assert manager.has_permission("test-plugin", PluginPermission.FILE_WRITE)

    def test_has_permission_not_granted(self, manager):
        """Test checking permission that wasn't granted."""
        assert not manager.has_permission("test-plugin", PluginPermission.FILE_READ)

    def test_enforce_permission_granted(self, manager):
        """Test enforcing granted permission."""
        manager.grant_permissions("test-plugin", ["file:read"])
        # Should not raise
        manager.enforce_permission("test-plugin", PluginPermission.FILE_READ)

    def test_enforce_permission_denied(self, manager):
        """Test enforcing permission not granted."""
        with pytest.raises(PermissionDeniedError):
            manager.enforce_permission("test-plugin", PluginPermission.FILE_WRITE)

    def test_get_permissions(self, manager):
        """Test getting list of permissions."""
        manager.grant_permissions("test-plugin", ["file:read", "file:write"])
        perms = manager.get_permissions("test-plugin")
        assert len(perms) == 2
        assert PluginPermission.FILE_READ in perms
        assert PluginPermission.FILE_WRITE in perms

    def test_revoke_permission(self, manager):
        """Test revoking specific permission."""
        manager.grant_permissions("test-plugin", ["file:read", "file:write"])

        revoked = manager.revoke_permission("test-plugin", PluginPermission.FILE_READ)
        assert revoked is True
        assert not manager.has_permission("test-plugin", PluginPermission.FILE_READ)
        assert manager.has_permission("test-plugin", PluginPermission.FILE_WRITE)

    def test_revoke_all_permissions(self, manager):
        """Test revoking all permissions."""
        manager.grant_permissions("test-plugin", ["file:read", "file:write"])

        count = manager.revoke_all_permissions("test-plugin")
        assert count == 2
        assert not manager.has_permission("test-plugin", PluginPermission.FILE_READ)
        assert not manager.has_permission("test-plugin", PluginPermission.FILE_WRITE)

    def test_list_plugins_with_permission(self, manager):
        """Test listing plugins with specific permission."""
        manager.grant_permissions("plugin1", ["file:read"])
        manager.grant_permissions("plugin2", ["file:read", "file:write"])
        manager.grant_permissions("plugin3", ["file:write"])

        plugins_with_read = manager.list_plugins_with_permission(PluginPermission.FILE_READ)
        assert len(plugins_with_read) == 2
        assert "plugin1" in plugins_with_read
        assert "plugin2" in plugins_with_read


# Test ResourceMonitor

class TestResourceMonitor:
    """Tests for ResourceMonitor."""

    @pytest.fixture
    def monitor(self):
        """Create ResourceMonitor instance."""
        return ResourceMonitor()

    def test_start_monitoring(self, monitor):
        """Test starting resource monitoring."""
        monitor.start_monitoring("test-plugin")
        usage = monitor.get_usage("test-plugin")
        assert usage is not None
        assert usage.cpu_percent == 0.0
        assert usage.memory_mb == 0.0

    def test_stop_monitoring(self, monitor):
        """Test stopping resource monitoring."""
        monitor.start_monitoring("test-plugin")
        usage = monitor.stop_monitoring("test-plugin")

        assert usage is not None
        assert monitor.get_usage("test-plugin") is None

    def test_update_usage(self, monitor):
        """Test updating resource usage."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", cpu_percent=45.0, memory_mb=128.5)

        usage = monitor.get_usage("test-plugin")
        assert usage.cpu_percent == 45.0
        assert usage.memory_mb == 128.5

    def test_check_limits_within(self, monitor):
        """Test checking limits when within bounds."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", cpu_percent=50.0, memory_mb=250.0)

        within_limits = monitor.check_limits("test-plugin", max_memory_mb=500, max_cpu_percent=80)
        assert within_limits is True

    def test_check_limits_memory_exceeded(self, monitor):
        """Test checking limits when memory exceeded."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", memory_mb=600.0)

        within_limits = monitor.check_limits("test-plugin", max_memory_mb=500)
        assert within_limits is False

    def test_check_limits_cpu_exceeded(self, monitor):
        """Test checking limits when CPU exceeded."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", cpu_percent=90.0)

        within_limits = monitor.check_limits("test-plugin", max_cpu_percent=80)
        assert within_limits is False

    def test_enforce_limits_within(self, monitor):
        """Test enforcing limits when within bounds."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", cpu_percent=50.0, memory_mb=250.0)

        # Should not raise
        monitor.enforce_limits("test-plugin", max_memory_mb=500, max_cpu_percent=80)

    def test_enforce_limits_memory_exceeded(self, monitor):
        """Test enforcing limits when memory exceeded."""
        monitor.start_monitoring("test-plugin")
        monitor.update_usage("test-plugin", memory_mb=600.0)

        with pytest.raises(ResourceLimitError):
            monitor.enforce_limits("test-plugin", max_memory_mb=500)

    def test_get_all_usage(self, monitor):
        """Test getting all usage metrics."""
        monitor.start_monitoring("plugin1")
        monitor.start_monitoring("plugin2")
        monitor.update_usage("plugin1", memory_mb=100.0)
        monitor.update_usage("plugin2", memory_mb=200.0)

        all_usage = monitor.get_all_usage()
        assert len(all_usage) == 2
        assert "plugin1" in all_usage
        assert "plugin2" in all_usage


# Test PluginSandbox

class TestPluginSandbox:
    """Tests for PluginSandbox."""

    @pytest.fixture
    def sandbox(self):
        """Create PluginSandbox instance."""
        return PluginSandbox()

    @pytest.fixture
    def sample_metadata(self, tmp_path):
        """Create sample plugin metadata."""
        return PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            type=PluginType.AGENT,
            entry_point="test_plugin.agent.TestAgent",
            plugin_path=tmp_path,
            permissions=["file:read", "hook:register"],
        )

    def test_validate_plugin_valid(self, sandbox, sample_metadata):
        """Test validating valid plugin."""
        result = sandbox.validate_plugin(sample_metadata)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_plugin_invalid_entry_point(self, sandbox, tmp_path):
        """Test validating plugin with invalid entry point."""
        # PluginMetadata validates entry point in __post_init__
        # So invalid entry point will raise during creation
        from gao_dev.plugins import PluginValidationError

        with pytest.raises(PluginValidationError):
            metadata = PluginMetadata(
                name="test-plugin",
                version="1.0.0",
                type=PluginType.AGENT,
                entry_point="InvalidFormat",  # Missing dot
                plugin_path=tmp_path,
            )

    def test_validate_plugin_invalid_permission(self, sandbox, tmp_path):
        """Test validating plugin with invalid permission."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            type=PluginType.AGENT,
            entry_point="test.Agent",
            plugin_path=tmp_path,
            permissions=["invalid:permission"],
        )
        result = sandbox.validate_plugin(metadata)
        assert result.valid is False
        assert any("invalid:permission" in err for err in result.errors)

    def test_check_permission(self, sandbox):
        """Test checking permissions."""
        sandbox.grant_permissions("test-plugin", ["file:read"])
        assert sandbox.check_permission("test-plugin", PluginPermission.FILE_READ)
        assert not sandbox.check_permission("test-plugin", PluginPermission.FILE_WRITE)

    def test_enforce_permission(self, sandbox):
        """Test enforcing permissions."""
        sandbox.grant_permissions("test-plugin", ["file:read"])
        sandbox.enforce_permission("test-plugin", PluginPermission.FILE_READ)

        with pytest.raises(PermissionDeniedError):
            sandbox.enforce_permission("test-plugin", PluginPermission.FILE_WRITE)

    @pytest.mark.asyncio
    async def test_execute_with_timeout_sync(self, sandbox):
        """Test executing sync function with timeout."""
        def sync_func():
            return "result"

        result = await sandbox.execute_with_timeout(sync_func, 1.0)
        assert result == "result"

    @pytest.mark.asyncio
    async def test_execute_with_timeout_async(self, sandbox):
        """Test executing async function with timeout."""
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"

        result = await sandbox.execute_with_timeout(async_func, 1.0)
        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_execute_with_timeout_exceeded(self, sandbox):
        """Test timeout enforcement."""
        async def slow_func():
            await asyncio.sleep(10)
            return "should_not_reach"

        with pytest.raises(PluginTimeoutError):
            await sandbox.execute_with_timeout(slow_func, 0.1)

    def test_resource_monitoring_integration(self, sandbox):
        """Test resource monitoring integration."""
        sandbox.start_monitoring("test-plugin")
        sandbox._resource_monitor.update_usage("test-plugin", memory_mb=100.0)

        within_limits = sandbox.check_resource_limits("test-plugin", max_memory_mb=500)
        assert within_limits is True

        sandbox.stop_monitoring("test-plugin")


# Integration Tests

class TestSecurityIntegration:
    """Integration tests for security system."""

    def test_full_security_workflow(self):
        """Test complete security workflow."""
        sandbox = PluginSandbox()

        # Grant permissions
        sandbox.grant_permissions("my-plugin", ["file:read", "hook:register"])

        # Start monitoring
        sandbox.start_monitoring("my-plugin")

        # Check permissions
        assert sandbox.check_permission("my-plugin", PluginPermission.FILE_READ)
        assert sandbox.check_permission("my-plugin", PluginPermission.HOOK_REGISTER)

        # Update resource usage
        sandbox._resource_monitor.update_usage("my-plugin", memory_mb=100.0, cpu_percent=30.0)

        # Check resource limits
        assert sandbox.check_resource_limits("my-plugin")

        # Cleanup
        sandbox.stop_monitoring("my-plugin")
        sandbox.revoke_all_permissions("my-plugin")
