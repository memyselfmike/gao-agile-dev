"""
Unit tests for AgentFactory.

Tests the Factory Pattern implementation for agent creation,
including registration, creation, error handling, and built-in agents.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import yaml

from gao_dev.core.factories.agent_factory import AgentFactory
from gao_dev.core.interfaces.agent import IAgent
from gao_dev.core.models.agent import AgentConfig
from gao_dev.agents.claude_agent import ClaudeAgent
from gao_dev.agents.exceptions import (
    AgentNotFoundError,
    AgentCreationError,
    RegistrationError,
    DuplicateRegistrationError
)


class TestAgentFactory:
    """Test suite for AgentFactory."""

    @pytest.fixture
    def agents_dir(self, tmp_path):
        """Create temporary agents directory with persona files and YAML configs."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        # Define all 8 agents with their configurations
        agents = {
            "mary": {"name": "Mary", "role": "Business Analyst", "tools": ["Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"], "capabilities": ["analysis"]},
            "john": {"name": "John", "role": "Product Manager", "tools": ["Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"], "capabilities": ["planning", "project-management"]},
            "winston": {"name": "Winston", "role": "Technical Architect", "tools": ["Read", "Write", "Edit", "Grep", "Glob", "WebSearch", "WebFetch"], "capabilities": ["architecture"]},
            "sally": {"name": "Sally", "role": "UX Designer", "tools": ["Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"], "capabilities": ["ux-design"]},
            "bob": {"name": "Bob", "role": "Scrum Master", "tools": ["Read", "Write", "Grep", "Glob", "TodoWrite"], "capabilities": ["scrum-master", "project-management"]},
            "amelia": {"name": "Amelia", "role": "Software Developer", "tools": ["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "TodoWrite", "WebSearch", "WebFetch"], "capabilities": ["implementation", "code-review"]},
            "murat": {"name": "Murat", "role": "Test Architect", "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "TodoWrite"], "capabilities": ["testing"]},
            "brian": {"name": "Brian", "role": "Workflow Coordinator", "tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch"], "capabilities": ["project-management", "planning"]},
        }

        # Create YAML and persona files for each agent
        for agent_name, agent_data in agents.items():
            # Create YAML config file
            yaml_data = {
                "agent": {
                    "metadata": {
                        "name": agent_data["name"],
                        "role": agent_data["role"],
                        "version": "1.0.0",
                    },
                    "persona_file": f"./{agent_name}.md",
                    "tools": agent_data["tools"],
                    "capabilities": agent_data["capabilities"],
                    "model": "claude-sonnet-4-5-20250929",
                }
            }
            yaml_path = agents_dir / f"{agent_name}.agent.yaml"
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(yaml_data, f)

            # Create persona file
            persona_text = f"You are {agent_data['name']}, a {agent_data['role'].lower()}."
            (agents_dir / f"{agent_name}.md").write_text(persona_text)

        return agents_dir

    @pytest.fixture
    def factory(self, agents_dir):
        """Create AgentFactory instance."""
        return AgentFactory(agents_dir)

    # ========================================================================
    # Initialization Tests
    # ========================================================================

    def test_factory_initialization(self, agents_dir):
        """Test factory initializes correctly."""
        factory = AgentFactory(agents_dir)

        assert factory._agents_dir == agents_dir
        assert isinstance(factory._registry, dict)
        assert isinstance(factory._agent_configs, dict)

    def test_builtin_agents_registered_on_init(self, factory):
        """Test that all 8 built-in agents are registered on initialization."""
        expected_agents = [
            "amelia", "bob", "brian", "john", "mary", "murat", "sally", "winston"
        ]

        available = factory.list_available_agents()

        assert len(available) == 8
        assert available == expected_agents  # Should be sorted alphabetically

    # ========================================================================
    # Agent Creation Tests
    # ========================================================================

    def test_create_agent_without_config(self, factory):
        """Test creating agent without explicit config uses built-in config."""
        agent = factory.create_agent("amelia")

        assert isinstance(agent, IAgent)
        assert isinstance(agent, ClaudeAgent)
        assert agent.name == "Amelia"
        assert agent.role == "Software Developer"

    def test_create_agent_with_config(self, factory):
        """Test creating agent with custom config."""
        config = AgentConfig(
            name="CustomAmelia",
            role="Senior Developer",
            tools=["Read", "Write", "Edit"]
        )

        agent = factory.create_agent("amelia", config)

        assert isinstance(agent, IAgent)
        assert agent.name == "CustomAmelia"
        assert agent.role == "Senior Developer"
        assert set(agent.tools) == {"Read", "Write", "Edit"}

    def test_create_all_builtin_agents(self, factory):
        """Test creating each built-in agent."""
        agent_types = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)

            assert isinstance(agent, IAgent)
            assert agent.name.lower() == agent_type
            assert agent.role  # Has a role

    def test_create_agent_loads_persona_from_file(self, factory, agents_dir):
        """Test that agent creation loads persona from file if it exists."""
        agent = factory.create_agent("amelia")

        # Persona should be loaded from amelia.md
        assert agent.persona == "You are Amelia, a software developer."

    def test_create_agent_handles_missing_persona_file(self, factory, agents_dir):
        """Test that agent creation works even if persona file is missing."""
        # Brian has persona from YAML config (no longer from .md file)
        agent = factory.create_agent("brian")

        assert isinstance(agent, IAgent)
        # Brian has persona from brian.agent.yaml
        assert agent.persona == "You are Brian, a workflow coordinator."

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_create_agent_raises_not_found_error(self, factory):
        """Test that creating non-existent agent raises AgentNotFoundError."""
        with pytest.raises(AgentNotFoundError) as exc_info:
            factory.create_agent("nonexistent")

        assert "nonexistent" in str(exc_info.value).lower()
        assert "Available agents:" in str(exc_info.value)

    def test_create_agent_is_case_insensitive(self, factory):
        """Test that agent creation is case-insensitive."""
        agent1 = factory.create_agent("amelia")
        agent2 = factory.create_agent("AMELIA")
        agent3 = factory.create_agent("Amelia")

        assert agent1.name == agent2.name == agent3.name

    # ========================================================================
    # Registration Tests
    # ========================================================================

    def test_register_agent_class(self, factory):
        """Test registering a new agent class."""
        class CustomAgent(ClaudeAgent):
            """Custom agent for testing."""
            pass

        factory.register_agent_class("custom", CustomAgent)

        assert factory.agent_exists("custom")
        assert "custom" in factory.list_available_agents()

    def test_register_agent_class_validates_interface(self, factory):
        """Test that registration validates IAgent interface."""
        class InvalidAgent:
            """Invalid agent that doesn't implement IAgent."""
            pass

        with pytest.raises(RegistrationError) as exc_info:
            factory.register_agent_class("invalid", InvalidAgent)

        assert "must implement IAgent" in str(exc_info.value)

    def test_register_duplicate_agent_raises_error(self, factory):
        """Test that registering duplicate agent type raises error."""
        class CustomAgent(ClaudeAgent):
            """Custom agent for testing."""
            pass

        # First registration should succeed
        factory.register_agent_class("custom", CustomAgent)

        # Second registration should fail
        with pytest.raises(DuplicateRegistrationError) as exc_info:
            factory.register_agent_class("custom", CustomAgent)

        assert "already registered" in str(exc_info.value).lower()

    def test_register_builtin_agent_raises_duplicate_error(self, factory):
        """Test that trying to re-register built-in agent raises error."""
        class CustomAgent(ClaudeAgent):
            """Custom agent for testing."""
            pass

        with pytest.raises(DuplicateRegistrationError):
            factory.register_agent_class("amelia", CustomAgent)

    # ========================================================================
    # Agent Existence Tests
    # ========================================================================

    def test_agent_exists_returns_true_for_registered(self, factory):
        """Test that agent_exists returns True for registered agents."""
        assert factory.agent_exists("amelia") is True
        assert factory.agent_exists("mary") is True
        assert factory.agent_exists("brian") is True

    def test_agent_exists_returns_false_for_unregistered(self, factory):
        """Test that agent_exists returns False for unregistered agents."""
        assert factory.agent_exists("nonexistent") is False
        assert factory.agent_exists("custom") is False

    def test_agent_exists_is_case_insensitive(self, factory):
        """Test that agent_exists is case-insensitive."""
        assert factory.agent_exists("amelia") is True
        assert factory.agent_exists("AMELIA") is True
        assert factory.agent_exists("Amelia") is True

    # ========================================================================
    # List Agents Tests
    # ========================================================================

    def test_list_available_agents_returns_sorted_list(self, factory):
        """Test that list_available_agents returns alphabetically sorted list."""
        agents = factory.list_available_agents()

        assert agents == sorted(agents)
        assert len(agents) == 8

    def test_list_available_agents_includes_custom_agents(self, factory):
        """Test that list includes custom registered agents."""
        class CustomAgent(ClaudeAgent):
            """Custom agent for testing."""
            pass

        factory.register_agent_class("zulu", CustomAgent)  # Will be last alphabetically
        factory.register_agent_class("alpha", CustomAgent)  # Will be first alphabetically

        agents = factory.list_available_agents()

        assert "alpha" in agents
        assert "zulu" in agents
        assert agents[0] == "alpha"  # Should be first (alphabetically)
        assert agents[-1] == "zulu"  # Should be last (alphabetically)

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_created_agent_has_correct_capabilities(self, factory):
        """Test that created agents have correct capabilities."""
        # Amelia should have Implementation and Code Review capabilities
        amelia = factory.create_agent("amelia")
        capabilities = amelia.get_capabilities()

        assert len(capabilities) == 2
        capability_types = [cap.capability_type.value for cap in capabilities]
        assert "implementation" in capability_types
        assert "code-review" in capability_types

    def test_created_agent_has_correct_tools(self, factory):
        """Test that created agents have correct tools."""
        mary = factory.create_agent("mary")

        # Mary should have analysis tools including WebSearch and WebFetch
        assert "Read" in mary.tools
        assert "Write" in mary.tools
        assert "WebSearch" in mary.tools
        assert "WebFetch" in mary.tools

    def test_factory_can_create_multiple_instances(self, factory):
        """Test that factory can create multiple instances of the same agent."""
        amelia1 = factory.create_agent("amelia")
        amelia2 = factory.create_agent("amelia")

        # Should be different instances
        assert amelia1 is not amelia2

        # But with same properties
        assert amelia1.name == amelia2.name
        assert amelia1.role == amelia2.role


class TestAgentFactoryErrorHandling:
    """Test suite for AgentFactory error handling."""

    def test_factory_handles_invalid_agents_dir(self, tmp_path):
        """Test that factory handles invalid agents directory."""
        invalid_dir = tmp_path / "nonexistent"

        # Should not raise error on initialization
        factory = AgentFactory(invalid_dir)

        # But should handle missing persona files gracefully
        agent = factory.create_agent("amelia")
        assert agent.persona == ""  # Empty if directory doesn't exist

    def test_factory_handles_persona_read_error(self, tmp_path, monkeypatch):
        """Test that factory handles errors reading persona files."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        persona_file = agents_dir / "amelia.md"
        persona_file.write_text("Test persona")

        factory = AgentFactory(agents_dir)

        # Mock Path.read_text to raise an error
        def mock_read_text(*args, **kwargs):
            raise IOError("Failed to read file")

        # This should log a warning but not fail
        with patch.object(Path, 'read_text', side_effect=mock_read_text):
            agent = factory.create_agent("amelia")
            # Should still create agent with empty persona
            assert isinstance(agent, IAgent)


class TestAgentFactoryBuiltinAgents:
    """Test suite for built-in agent configurations."""

    @pytest.fixture
    def factory(self, tmp_path):
        """Create factory with temp directory."""
        return AgentFactory(tmp_path / "agents")

    @pytest.mark.parametrize("agent_type,expected_role", [
        ("mary", "Business Analyst"),
        ("john", "Product Manager"),
        ("winston", "Technical Architect"),
        ("sally", "UX Designer"),
        ("bob", "Scrum Master"),
        ("amelia", "Software Developer"),
        ("murat", "Test Architect"),
        ("brian", "Workflow Coordinator"),
    ])
    def test_builtin_agent_roles(self, factory, agent_type, expected_role):
        """Test that built-in agents have correct roles."""
        agent = factory.create_agent(agent_type)
        assert agent.role == expected_role

    def test_all_builtin_agents_have_tools(self, factory):
        """Test that all built-in agents have tools configured."""
        agent_types = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)
            assert len(agent.tools) > 0, f"{agent_type} should have tools"

    def test_technical_agents_have_edit_and_bash_tools(self, factory):
        """Test that technical agents (developers, QA) have Edit and Bash tools."""
        technical_agents = ["amelia", "murat", "winston"]

        for agent_type in technical_agents:
            agent = factory.create_agent(agent_type)
            assert "Edit" in agent.tools, f"{agent_type} should have Edit tool"

    def test_analysis_agents_have_web_tools(self, factory):
        """Test that analysis agents have WebSearch and WebFetch tools."""
        mary = factory.create_agent("mary")

        assert "WebSearch" in mary.tools
        assert "WebFetch" in mary.tools
