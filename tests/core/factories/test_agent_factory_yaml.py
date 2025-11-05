"""
Integration tests for AgentFactory with YAML-based agent loading.

Tests that AgentFactory correctly loads agents from YAML files
and maintains backwards compatibility with the existing API.
"""

import pytest
from pathlib import Path

from gao_dev.core.factories.agent_factory import AgentFactory
from gao_dev.agents.exceptions import AgentNotFoundError


@pytest.fixture
def agents_dir():
    """Get the real agents directory."""
    return Path(__file__).parent.parent.parent.parent / "gao_dev" / "agents"


@pytest.fixture
def agent_factory(agents_dir):
    """Create an AgentFactory instance."""
    return AgentFactory(agents_dir)


class TestAgentFactoryYAMLLoading:
    """Tests for YAML-based agent loading."""

    def test_factory_initializes_with_yaml(self, agent_factory):
        """Test that factory initializes and loads agents from YAML."""
        # Factory should have loaded all 8 agents
        available = agent_factory.list_available_agents()

        assert len(available) == 8
        expected_agents = ["amelia", "bob", "brian", "john", "mary", "murat", "sally", "winston"]
        assert sorted(available) == expected_agents

    def test_create_agent_from_yaml(self, agent_factory):
        """Test creating an agent loaded from YAML."""
        amelia = agent_factory.create_agent("amelia")

        assert amelia is not None
        assert amelia.name == "Amelia"
        assert amelia.role == "Software Developer"
        assert "Read" in amelia.tools
        assert "Write" in amelia.tools
        assert "Edit" in amelia.tools
        assert amelia.persona  # Non-empty persona

    def test_create_all_agents_from_yaml(self, agent_factory):
        """Test creating all agents from YAML."""
        agent_names = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_name in agent_names:
            agent = agent_factory.create_agent(agent_name)
            assert agent is not None
            assert agent.name  # Has a name
            assert agent.role  # Has a role
            assert agent.tools  # Has tools
            assert agent.persona  # Has persona

    def test_agent_has_correct_tools_from_yaml(self, agent_factory):
        """Test that agents have correct tools loaded from YAML."""
        # Amelia should have implementation tools
        amelia = agent_factory.create_agent("amelia")
        assert "Read" in amelia.tools
        assert "Write" in amelia.tools
        assert "Edit" in amelia.tools
        assert "Bash" in amelia.tools

        # John should have planning tools
        john = agent_factory.create_agent("john")
        assert "Read" in john.tools
        assert "Write" in john.tools
        assert "Grep" in john.tools
        assert "Glob" in john.tools

        # Brian should have read-only tools
        brian = agent_factory.create_agent("brian")
        assert "Read" in brian.tools
        assert "Grep" in brian.tools
        assert "Glob" in brian.tools

    def test_agent_has_correct_capabilities(self, agent_factory):
        """Test that agents have correct capabilities from YAML."""
        # Amelia should have implementation and code review
        amelia = agent_factory.create_agent("amelia")
        capabilities = amelia.get_capabilities()
        assert capabilities is not None
        assert len(capabilities) >= 2

        # Mary should have analysis
        mary = agent_factory.create_agent("mary")
        capabilities = mary.get_capabilities()
        assert capabilities is not None
        assert len(capabilities) >= 1

    def test_agent_persona_loaded_from_file(self, agent_factory):
        """Test that agent persona is loaded from .md file."""
        amelia = agent_factory.create_agent("amelia")

        # Persona should contain agent name and role
        assert "Amelia" in amelia.persona or "amelia" in amelia.persona.lower()
        assert amelia.persona  # Non-empty
        assert len(amelia.persona) > 100  # Substantial content


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with existing API."""

    def test_list_available_agents(self, agent_factory):
        """Test list_available_agents works as before."""
        agents = agent_factory.list_available_agents()

        assert isinstance(agents, list)
        assert len(agents) == 8
        assert all(isinstance(name, str) for name in agents)

    def test_list_agents_alias(self, agent_factory):
        """Test list_agents alias works."""
        agents = agent_factory.list_agents()

        assert isinstance(agents, list)
        assert len(agents) == 8

    def test_agent_exists(self, agent_factory):
        """Test agent_exists works as before."""
        assert agent_factory.agent_exists("amelia") is True
        assert agent_factory.agent_exists("john") is True
        assert agent_factory.agent_exists("nonexistent") is False

    def test_agent_not_found_error(self, agent_factory):
        """Test that AgentNotFoundError is raised for unknown agents."""
        with pytest.raises(AgentNotFoundError) as exc_info:
            agent_factory.create_agent("nonexistent")

        assert "nonexistent" in str(exc_info.value).lower()
        assert "Available agents:" in str(exc_info.value)

    def test_case_insensitive_agent_names(self, agent_factory):
        """Test that agent names are case-insensitive."""
        amelia_lower = agent_factory.create_agent("amelia")
        amelia_upper = agent_factory.create_agent("AMELIA")
        amelia_mixed = agent_factory.create_agent("Amelia")

        assert amelia_lower.name == amelia_upper.name == amelia_mixed.name


class TestAgentFactoryWithCustomConfig:
    """Tests for custom agent configuration."""

    def test_create_agent_with_custom_config(self, agent_factory):
        """Test creating agent with custom config overrides YAML."""
        from gao_dev.core.models.agent import AgentConfig

        custom_config = AgentConfig(
            name="CustomAmelia",
            role="Custom Developer",
            tools=["Read", "Write"],
        )

        agent = agent_factory.create_agent("amelia", custom_config)

        assert agent.name == "CustomAmelia"
        assert agent.role == "Custom Developer"
        assert agent.tools == ["Read", "Write"]


class TestAgentModel:
    """Tests for agent model configuration."""

    def test_agent_has_correct_model(self, agent_factory):
        """Test that agents have the correct Claude model."""
        amelia = agent_factory.create_agent("amelia")

        assert amelia.model == "claude-sonnet-4-5-20250929"


class TestZeroRegressions:
    """Tests to ensure no regressions from YAML migration."""

    def test_all_agents_can_be_created(self, agent_factory):
        """Test that all agents can be created successfully."""
        agent_names = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_name in agent_names:
            agent = agent_factory.create_agent(agent_name)
            assert agent is not None, f"Failed to create {agent_name}"

    def test_agents_have_required_attributes(self, agent_factory):
        """Test that all agents have required attributes."""
        agent_names = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_name in agent_names:
            agent = agent_factory.create_agent(agent_name)

            # Check required attributes
            assert hasattr(agent, "name"), f"{agent_name} missing name"
            assert hasattr(agent, "role"), f"{agent_name} missing role"
            assert hasattr(agent, "persona"), f"{agent_name} missing persona"
            assert hasattr(agent, "tools"), f"{agent_name} missing tools"
            assert hasattr(agent, "model"), f"{agent_name} missing model"

            # Check non-empty
            assert agent.name, f"{agent_name} has empty name"
            assert agent.role, f"{agent_name} has empty role"
            assert agent.persona, f"{agent_name} has empty persona"
            assert agent.tools, f"{agent_name} has empty tools list"
            assert agent.model, f"{agent_name} has empty model"

    def test_agents_match_expected_roles(self, agent_factory):
        """Test that agents have their expected roles."""
        expected_roles = {
            "mary": "Business Analyst",
            "john": "Product Manager",
            "winston": "Technical Architect",
            "sally": "UX Designer",
            "bob": "Scrum Master",
            "amelia": "Software Developer",
            "murat": "Test Architect",
            "brian": "Workflow Coordinator",
        }

        for agent_name, expected_role in expected_roles.items():
            agent = agent_factory.create_agent(agent_name)
            assert agent.role == expected_role, f"{agent_name} has wrong role: {agent.role}"

    def test_tool_counts_reasonable(self, agent_factory):
        """Test that agents have a reasonable number of tools."""
        agent_names = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_name in agent_names:
            agent = agent_factory.create_agent(agent_name)

            # All agents should have at least 3 tools
            assert len(agent.tools) >= 3, f"{agent_name} has too few tools: {agent.tools}"

            # No agent should have more than 15 tools
            assert len(agent.tools) <= 15, f"{agent_name} has too many tools: {agent.tools}"


class TestAgentFactoryPluginSupport:
    """Tests for plugin agent registration."""

    def test_register_plugin_agent(self, agent_factory):
        """Test registering a plugin agent alongside YAML agents."""
        from gao_dev.agents.claude_agent import ClaudeAgent

        # Should be able to register new agents
        agent_factory.register_plugin_agent("custom", ClaudeAgent)

        assert agent_factory.agent_exists("custom")
        assert "custom" in agent_factory.list_available_agents()

    def test_register_plugin_agent_does_not_conflict(self, agent_factory):
        """Test that plugin agents don't conflict with YAML agents."""
        from gao_dev.agents.claude_agent import ClaudeAgent
        from gao_dev.agents.exceptions import DuplicateRegistrationError

        # Try to register an agent with same name as YAML agent
        with pytest.raises(DuplicateRegistrationError):
            agent_factory.register_plugin_agent("amelia", ClaudeAgent)
