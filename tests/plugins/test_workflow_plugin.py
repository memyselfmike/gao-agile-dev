"""Tests for workflow plugin system."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from gao_dev.plugins import (
    BaseWorkflowPlugin,
    WorkflowPluginManager,
    WorkflowMetadata,
    PluginDiscovery,
    PluginLoader,
    PluginMetadata,
    PluginType,
    PluginError,
)
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.interfaces.workflow import IWorkflow
from gao_dev.core.models.workflow import WorkflowIdentifier


# Fixtures

@pytest.fixture
def mock_config_loader():
    """Create mock config loader."""
    mock_loader = Mock()
    mock_loader.load_config.return_value = {
        'plugins': {
            'enabled': True,
            'directories': []
        }
    }
    return mock_loader


@pytest.fixture
def workflow_registry(mock_config_loader):
    """Create WorkflowRegistry instance."""
    return WorkflowRegistry(mock_config_loader)


@pytest.fixture
def plugin_discovery(mock_config_loader):
    """Create PluginDiscovery instance."""
    return PluginDiscovery(mock_config_loader)


@pytest.fixture
def plugin_loader():
    """Create PluginLoader instance."""
    return PluginLoader()


@pytest.fixture
def workflow_plugin_manager(plugin_discovery, plugin_loader, workflow_registry):
    """Create WorkflowPluginManager instance."""
    return WorkflowPluginManager(plugin_discovery, plugin_loader, workflow_registry)


@pytest.fixture
def example_workflow_plugin_path():
    """Get path to example workflow plugin fixture."""
    return Path(__file__).parent / "fixtures" / "example_workflow_plugin"


@pytest.fixture
def example_plugin_metadata(example_workflow_plugin_path):
    """Create metadata for example workflow plugin."""
    return PluginMetadata(
        name="example-workflow-plugin",
        version="1.0.0",
        type=PluginType.WORKFLOW,
        entry_point="example_workflow_plugin.workflow_plugin.ExampleWorkflowPlugin",
        plugin_path=example_workflow_plugin_path,
        description="Example workflow plugin for testing",
        enabled=True,
    )


# Tests for WorkflowMetadata

class TestWorkflowMetadata:
    """Tests for WorkflowMetadata model."""

    def test_create_workflow_metadata(self):
        """Test creating workflow metadata with all fields."""
        metadata = WorkflowMetadata(
            name="test-workflow",
            description="Test description",
            phase=1,
            tags=["test", "example"],
            required_tools=["Read", "Write"]
        )

        assert metadata.name == "test-workflow"
        assert metadata.description == "Test description"
        assert metadata.phase == 1
        assert metadata.tags == ["test", "example"]
        assert metadata.required_tools == ["Read", "Write"]

    def test_workflow_metadata_requires_name(self):
        """Test that name is required."""
        with pytest.raises(ValueError, match="name is required"):
            WorkflowMetadata(name="", description="Desc")

    def test_workflow_metadata_requires_description(self):
        """Test that description is required."""
        with pytest.raises(ValueError, match="description is required"):
            WorkflowMetadata(name="Test", description="")

    def test_workflow_metadata_validates_phase(self):
        """Test that phase is validated."""
        with pytest.raises(ValueError, match="Phase must be -1 to 4"):
            WorkflowMetadata(name="Test", description="Desc", phase=5)


# Tests for BaseWorkflowPlugin

class TestBaseWorkflowPlugin:
    """Tests for BaseWorkflowPlugin abstract class."""

    def test_example_workflow_plugin_implements_interface(
        self, plugin_loader, example_plugin_metadata
    ):
        """Test that example plugin implements all required methods."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-workflow-plugin")

        assert isinstance(plugin, BaseWorkflowPlugin)
        assert hasattr(plugin, 'get_workflow_class')
        assert hasattr(plugin, 'get_workflow_identifier')
        assert hasattr(plugin, 'get_workflow_metadata')

    def test_example_plugin_returns_workflow_class(
        self, plugin_loader, example_plugin_metadata
    ):
        """Test that plugin returns valid workflow class."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-workflow-plugin")

        workflow_class = plugin.get_workflow_class()
        assert isinstance(workflow_class, type)
        assert issubclass(workflow_class, IWorkflow)

    def test_example_plugin_returns_identifier(
        self, plugin_loader, example_plugin_metadata
    ):
        """Test that plugin returns workflow identifier."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-workflow-plugin")

        identifier = plugin.get_workflow_identifier()
        assert isinstance(identifier, WorkflowIdentifier)
        assert identifier.name == "example-workflow"
        assert identifier.phase == 1

    def test_example_plugin_returns_metadata(
        self, plugin_loader, example_plugin_metadata
    ):
        """Test that plugin returns workflow metadata."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-workflow-plugin")

        metadata = plugin.get_workflow_metadata()
        assert isinstance(metadata, WorkflowMetadata)
        assert metadata.name == "example-workflow"
        assert metadata.description
        assert metadata.phase == 1

    def test_validate_workflow_class(
        self, plugin_loader, example_plugin_metadata
    ):
        """Test workflow class validation."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-workflow-plugin")

        # Should not raise
        plugin.validate_workflow_class()


# Tests for WorkflowPluginManager

class TestWorkflowPluginManager:
    """Tests for WorkflowPluginManager."""

    def test_discover_workflow_plugins(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test discovering workflow plugins."""
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]

        workflow_plugins = workflow_plugin_manager.discover_workflow_plugins()

        assert len(workflow_plugins) >= 1
        assert any(p.name == "example-workflow-plugin" for p in workflow_plugins)
        assert all(p.type == PluginType.WORKFLOW for p in workflow_plugins)

    def test_load_workflow_plugins(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test loading workflow plugins."""
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]

        results = workflow_plugin_manager.load_workflow_plugins()

        assert "example-workflow-plugin" in results
        assert results["example-workflow-plugin"] == "loaded"

    def test_register_workflow_plugins(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test registering workflow plugins."""
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]

        # Load plugins first
        workflow_plugin_manager.load_workflow_plugins()

        # Register
        count = workflow_plugin_manager.register_workflow_plugins()

        assert count >= 1

    def test_discover_load_and_register(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test convenience method for full workflow."""
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]

        results = workflow_plugin_manager.discover_load_and_register()

        assert results["discovered"] >= 1
        assert results["registered"] >= 1


# Integration Tests

class TestIntegration:
    """Integration tests for workflow plugin system."""

    def test_end_to_end_plugin_workflow(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test complete workflow: discover → load → register."""
        # Setup
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]

        # Discover
        plugins = workflow_plugin_manager.discover_workflow_plugins()
        assert len(plugins) >= 1

        # Load
        results = workflow_plugin_manager.load_workflow_plugins()
        assert results["example-workflow-plugin"] == "loaded"

        # Register
        count = workflow_plugin_manager.register_workflow_plugins()
        assert count >= 1

    async def test_plugin_workflow_execution(
        self, workflow_plugin_manager, example_workflow_plugin_path
    ):
        """Test that plugin workflow can be instantiated and executed."""
        from gao_dev.core.models.workflow import WorkflowContext

        # Setup
        workflow_plugin_manager.discovery.get_plugin_dirs = lambda: [
            example_workflow_plugin_path.parent
        ]
        workflow_plugin_manager.load_workflow_plugins()

        # Get plugin and workflow class
        plugin = workflow_plugin_manager.loader.get_loaded_plugin("example-workflow-plugin")
        workflow_class = plugin.get_workflow_class()

        # Create workflow instance
        workflow = workflow_class()

        # Validate
        assert workflow.identifier.name == "example-workflow"
        assert workflow.description
        assert isinstance(workflow.required_tools, list)

        # Execute (basic check)
        context = WorkflowContext(
            project_root=Path("."),
            parameters={}
        )
        assert workflow.validate_context(context)

        result = await workflow.execute(context)
        assert result.success is True
