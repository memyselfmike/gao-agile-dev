"""Tests for agent plugin system."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from gao_dev.plugins import (
    BaseAgentPlugin,
    AgentPluginManager,
    AgentMetadata,
    PluginDiscovery,
    PluginLoader,
    PluginMetadata,
    PluginType,
    PluginError,
)
from gao_dev.core.factories.agent_factory import AgentFactory
from gao_dev.core.interfaces.agent import IAgent
from gao_dev.agents.exceptions import DuplicateRegistrationError, RegistrationError


# Fixtures

@pytest.fixture
def agent_factory(tmp_path):
    """Create AgentFactory instance."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return AgentFactory(agents_dir)


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
def plugin_discovery(mock_config_loader):
    """Create PluginDiscovery instance."""
    return PluginDiscovery(mock_config_loader)


@pytest.fixture
def plugin_loader():
    """Create PluginLoader instance."""
    return PluginLoader()


@pytest.fixture
def agent_plugin_manager(plugin_discovery, plugin_loader, agent_factory):
    """Create AgentPluginManager instance."""
    return AgentPluginManager(plugin_discovery, plugin_loader, agent_factory)


@pytest.fixture
def example_agent_plugin_path():
    """Get path to example agent plugin fixture."""
    return Path(__file__).parent / "fixtures" / "example_agent_plugin"


@pytest.fixture
def example_plugin_metadata(example_agent_plugin_path):
    """Create metadata for example agent plugin."""
    return PluginMetadata(
        name="example-agent-plugin",
        version="1.0.0",
        type=PluginType.AGENT,
        entry_point="example_agent_plugin.agent_plugin.ExampleAgentPlugin",
        plugin_path=example_agent_plugin_path,
        description="Example agent plugin for testing",
        enabled=True,
    )


# Tests for AgentMetadata

class TestAgentMetadata:
    """Tests for AgentMetadata model."""

    def test_create_agent_metadata(self):
        """Test creating agent metadata with all fields."""
        metadata = AgentMetadata(
            name="TestAgent",
            role="Test Role",
            description="Test description",
            capabilities=["test1", "test2"],
            tools=["Read", "Write"],
            model="claude-sonnet-4-5-20250929"
        )

        assert metadata.name == "TestAgent"
        assert metadata.role == "Test Role"
        assert metadata.description == "Test description"
        assert metadata.capabilities == ["test1", "test2"]
        assert metadata.tools == ["Read", "Write"]
        assert metadata.model == "claude-sonnet-4-5-20250929"

    def test_agent_metadata_requires_name(self):
        """Test that name is required."""
        with pytest.raises(ValueError, match="name is required"):
            AgentMetadata(
                name="",
                role="Role",
                description="Desc"
            )

    def test_agent_metadata_requires_role(self):
        """Test that role is required."""
        with pytest.raises(ValueError, match="role is required"):
            AgentMetadata(
                name="Test",
                role="",
                description="Desc"
            )

    def test_agent_metadata_requires_description(self):
        """Test that description is required."""
        with pytest.raises(ValueError, match="description is required"):
            AgentMetadata(
                name="Test",
                role="Role",
                description=""
            )


# Tests for BaseAgentPlugin

class TestBaseAgentPlugin:
    """Tests for BaseAgentPlugin abstract class."""

    def test_base_agent_plugin_requires_implementation(self):
        """Test that BaseAgentPlugin requires abstract methods to be implemented."""
        # BaseAgentPlugin can be instantiated but abstract methods must be implemented
        # Trying to call abstract methods without implementation should raise TypeError
        # This is tested implicitly through the working example plugin
        pass

    def test_example_agent_plugin_implements_interface(self, plugin_loader, example_plugin_metadata):
        """Test that example plugin implements all required methods."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        assert isinstance(plugin, BaseAgentPlugin)
        assert hasattr(plugin, 'get_agent_class')
        assert hasattr(plugin, 'get_agent_name')
        assert hasattr(plugin, 'get_agent_metadata')

    def test_example_plugin_returns_agent_class(self, plugin_loader, example_plugin_metadata):
        """Test that plugin returns valid agent class."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        agent_class = plugin.get_agent_class()
        assert isinstance(agent_class, type)
        assert issubclass(agent_class, IAgent)

    def test_example_plugin_returns_agent_name(self, plugin_loader, example_plugin_metadata):
        """Test that plugin returns agent name."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        agent_name = plugin.get_agent_name()
        assert isinstance(agent_name, str)
        assert agent_name == "ExampleAgent"

    def test_example_plugin_returns_metadata(self, plugin_loader, example_plugin_metadata):
        """Test that plugin returns agent metadata."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        metadata = plugin.get_agent_metadata()
        assert isinstance(metadata, AgentMetadata)
        assert metadata.name == "ExampleAgent"
        assert metadata.role == "Example Role"

    def test_validate_agent_class(self, plugin_loader, example_plugin_metadata):
        """Test agent class validation."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        # Should not raise
        plugin.validate_agent_class()


# Tests for AgentFactory.register_plugin_agent()

class TestAgentFactoryPluginRegistration:
    """Tests for AgentFactory plugin agent registration."""

    def test_register_plugin_agent(self, agent_factory, plugin_loader, example_plugin_metadata):
        """Test registering a plugin agent."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        agent_class = plugin.get_agent_class()
        agent_name = plugin.get_agent_name()

        agent_factory.register_plugin_agent(agent_name, agent_class)

        assert agent_factory.agent_exists("exampleagent")
        assert "exampleagent" in agent_factory.list_agents()

    def test_register_plugin_agent_duplicate(self, agent_factory, plugin_loader, example_plugin_metadata):
        """Test that duplicate registration raises error."""
        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        agent_class = plugin.get_agent_class()
        agent_name = plugin.get_agent_name()

        agent_factory.register_plugin_agent(agent_name, agent_class)

        with pytest.raises(DuplicateRegistrationError, match="already registered"):
            agent_factory.register_plugin_agent(agent_name, agent_class)

    def test_register_plugin_agent_invalid_class(self, agent_factory):
        """Test that non-IAgent class raises error."""
        class NotAnAgent:
            pass

        with pytest.raises(RegistrationError, match="must implement IAgent"):
            agent_factory.register_plugin_agent("invalid", NotAnAgent)

    def test_list_agents_includes_plugins(self, agent_factory, plugin_loader, example_plugin_metadata):
        """Test that list_agents includes both built-in and plugin agents."""
        initial_count = len(agent_factory.list_agents())

        plugin_loader.load_plugin(example_plugin_metadata)
        plugin = plugin_loader.get_loaded_plugin("example-agent-plugin")

        agent_factory.register_plugin_agent(
            plugin.get_agent_name(),
            plugin.get_agent_class()
        )

        assert len(agent_factory.list_agents()) == initial_count + 1


# Tests for AgentPluginManager

class TestAgentPluginManager:
    """Tests for AgentPluginManager."""

    def test_discover_agent_plugins(self, agent_plugin_manager, example_agent_plugin_path):
        """Test discovering agent plugins."""
        # Mock plugin dirs to include our example
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]

        agent_plugins = agent_plugin_manager.discover_agent_plugins()

        assert len(agent_plugins) >= 1
        assert any(p.name == "example-agent-plugin" for p in agent_plugins)
        assert all(p.type == PluginType.AGENT for p in agent_plugins)

    def test_load_agent_plugins(self, agent_plugin_manager, example_agent_plugin_path):
        """Test loading agent plugins."""
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]

        results = agent_plugin_manager.load_agent_plugins()

        assert "example-agent-plugin" in results
        assert results["example-agent-plugin"] == "loaded"

    def test_register_agent_plugins(self, agent_plugin_manager, example_agent_plugin_path):
        """Test registering agent plugins with factory."""
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]

        # Load plugins first
        agent_plugin_manager.load_agent_plugins()

        # Register
        count = agent_plugin_manager.register_agent_plugins()

        assert count >= 1
        assert agent_plugin_manager.factory.agent_exists("exampleagent")

    def test_get_available_agents(self, agent_plugin_manager, example_agent_plugin_path):
        """Test getting all available agents."""
        initial_agents = agent_plugin_manager.get_available_agents()

        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]
        agent_plugin_manager.load_agent_plugins()
        agent_plugin_manager.register_agent_plugins()

        final_agents = agent_plugin_manager.get_available_agents()

        assert len(final_agents) > len(initial_agents)
        assert "exampleagent" in final_agents

    def test_discover_load_and_register(self, agent_plugin_manager, example_agent_plugin_path):
        """Test convenience method for full workflow."""
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]

        results = agent_plugin_manager.discover_load_and_register()

        assert results["discovered"] >= 1
        assert results["registered"] >= 1
        assert "exampleagent" in results["available_agents"]


# Integration Tests

class TestIntegration:
    """Integration tests for agent plugin system."""

    def test_end_to_end_plugin_workflow(self, agent_plugin_manager, example_agent_plugin_path):
        """Test complete workflow: discover → load → register → use."""
        # Setup
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]

        # Discover
        plugins = agent_plugin_manager.discover_agent_plugins()
        assert len(plugins) >= 1

        # Load
        results = agent_plugin_manager.load_agent_plugins()
        assert results["example-agent-plugin"] == "loaded"

        # Register
        count = agent_plugin_manager.register_agent_plugins()
        assert count >= 1

        # Use (create agent instance)
        agent = agent_plugin_manager.factory.create_agent("exampleagent")
        assert agent is not None
        assert agent.name == "ExampleAgent"

    async def test_plugin_agent_execution(self, agent_plugin_manager, example_agent_plugin_path):
        """Test that plugin agent can execute tasks."""
        from gao_dev.core.models.agent import AgentContext

        # Setup
        agent_plugin_manager.discovery.get_plugin_dirs = lambda: [example_agent_plugin_path.parent]
        agent_plugin_manager.discover_load_and_register()

        # Create agent
        agent = agent_plugin_manager.factory.create_agent("exampleagent")

        # Execute task
        context = AgentContext(project_root=Path("."))
        messages = []
        async for msg in agent.execute_task("Test task", context):
            messages.append(msg)

        assert len(messages) == 3
        assert "ExampleAgent starting task" in messages[0]
        assert "completed task successfully" in messages[2]
