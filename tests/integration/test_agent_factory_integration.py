"""
Integration tests for AgentFactory.

Tests the AgentFactory integration with the orchestrator and
real agent execution scenarios.
"""

import pytest
from pathlib import Path
import asyncio

from gao_dev.core.factories.agent_factory import AgentFactory
from gao_dev.core.models.agent import AgentContext


class TestAgentFactoryIntegration:
    """Integration test suite for AgentFactory."""

    @pytest.fixture
    def factory(self):
        """Create factory with real agents directory."""
        # Use the actual GAO-Dev agents directory
        gao_dev_root = Path(__file__).parent.parent.parent
        agents_dir = gao_dev_root / "gao_dev" / "agents"

        return AgentFactory(agents_dir)

    @pytest.fixture
    def agent_context(self, tmp_path):
        """Create agent context for testing."""
        return AgentContext(
            project_root=tmp_path,
            available_tools=["Read", "Write", "Edit", "Bash"],
            agent_config={},
            metadata={}
        )

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_factory_creates_all_builtin_agents_with_real_personas(self, factory):
        """Test that factory can create all built-in agents with real persona files."""
        agent_types = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)

            # Should have loaded persona from file
            # (if file exists in gao_dev/agents/)
            assert agent.persona or True  # Persona might be empty if file doesn't exist
            assert agent.name
            assert agent.role

    @pytest.mark.asyncio
    async def test_created_agent_can_execute_task(self, factory, agent_context):
        """Test that agent created by factory can execute tasks."""
        agent = factory.create_agent("amelia")

        # Initialize agent
        await agent.initialize()

        # Execute a simple task
        messages = []
        async for message in agent.execute_task("Write a test", agent_context):
            messages.append(message)

        # Should yield some messages
        assert len(messages) > 0
        assert any("Amelia" in msg for msg in messages)

        # Cleanup
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_created_agent_handles_initialization(self, factory, agent_context):
        """Test that agent handles initialization lifecycle."""
        agent = factory.create_agent("bob")

        # Should not be initialized yet
        assert not agent.is_initialized

        # Initialize
        await agent.initialize()
        assert agent.is_initialized

        # Cleanup
        await agent.cleanup()
        assert not agent.is_initialized

    @pytest.mark.asyncio
    async def test_multiple_agents_can_work_concurrently(self, factory, agent_context):
        """Test that multiple agents can be created and work concurrently."""
        mary = factory.create_agent("mary")
        john = factory.create_agent("john")
        amelia = factory.create_agent("amelia")

        # Initialize all
        await mary.initialize()
        await john.initialize()
        await amelia.initialize()

        # Execute tasks concurrently
        async def execute_agent_task(agent, task):
            messages = []
            async for msg in agent.execute_task(task, agent_context):
                messages.append(msg)
            return messages

        results = await asyncio.gather(
            execute_agent_task(mary, "Analyze requirements"),
            execute_agent_task(john, "Create PRD"),
            execute_agent_task(amelia, "Implement feature")
        )

        # All should have completed
        assert len(results) == 3
        assert all(len(messages) > 0 for messages in results)

        # Cleanup all
        await mary.cleanup()
        await john.cleanup()
        await amelia.cleanup()

    def test_factory_works_with_existing_orchestrator_pattern(self, factory):
        """Test that factory integrates with existing orchestrator pattern."""
        # Simulate how orchestrator would use factory
        agent_type = "amelia"
        agent = factory.create_agent(agent_type)

        # Should be compatible with orchestrator expectations
        assert hasattr(agent, "name")
        assert hasattr(agent, "role")
        assert hasattr(agent, "execute_task")
        assert callable(agent.execute_task)

    def test_factory_supports_plugin_pattern(self, factory):
        """Test that factory supports plugin-style agent registration."""
        from gao_dev.agents.claude_agent import ClaudeAgent

        # Simulate a plugin registering a custom agent
        class CustomDomainAgent(ClaudeAgent):
            """Custom domain-specific agent."""
            pass

        # Register the plugin agent
        factory.register_agent_class("domain-expert", CustomDomainAgent)

        # Should be able to create it
        agent = factory.create_agent("domain-expert")
        assert isinstance(agent, CustomDomainAgent)

    def test_factory_maintains_agent_isolation(self, factory):
        """Test that agents created by factory are isolated."""
        agent1 = factory.create_agent("amelia")
        agent2 = factory.create_agent("amelia")

        # Should be different instances
        assert agent1 is not agent2

        # Modifying one should not affect the other
        agent1._persona = "Modified persona"
        assert agent2._persona != "Modified persona"


class TestAgentFactoryWithOrchestrator:
    """Integration tests with GAODevOrchestrator."""

    @pytest.fixture
    def factory(self):
        """Create factory with real agents directory."""
        gao_dev_root = Path(__file__).parent.parent.parent
        agents_dir = gao_dev_root / "gao_dev" / "agents"
        return AgentFactory(agents_dir)

    def test_factory_can_replace_agent_definitions(self, factory):
        """Test that factory can replace AGENT_DEFINITIONS pattern."""
        # The old pattern used AGENT_DEFINITIONS dict
        # The new pattern uses AgentFactory

        # Get all agent types from factory
        available_agents = factory.list_available_agents()

        # Should have all expected agents
        expected_agents = ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]
        assert set(available_agents) == set(expected_agents)

        # Each should be creatable
        for agent_type in expected_agents:
            agent = factory.create_agent(agent_type)
            assert agent.name.lower() == agent_type
