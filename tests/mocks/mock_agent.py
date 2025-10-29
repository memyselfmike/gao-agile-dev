"""Mock agent implementations for testing."""

from typing import List, AsyncGenerator, Optional, Dict
from gao_dev.core.interfaces.agent import IAgent, IAgentFactory
from gao_dev.core.models.agent import AgentCapability, AgentContext


class MockAgent(IAgent):
    """
    Mock agent for testing.

    Provides a simple agent implementation that yields predefined messages.
    """

    def __init__(
        self,
        name: str = "MockAgent",
        role: str = "Mock Role",
        capabilities: Optional[List[AgentCapability]] = None,
        messages: Optional[List[str]] = None
    ):
        self._name = name
        self._role = role
        self._capabilities = capabilities or []
        self._messages = messages or ["Mock message"]
        self.tasks_executed: List[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self._role

    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """Execute task and yield predefined messages."""
        self.tasks_executed.append(task)
        for message in self._messages:
            yield message

    def get_capabilities(self) -> List[AgentCapability]:
        """Return predefined capabilities."""
        return self._capabilities.copy()

    def can_handle_task(self, task: str) -> bool:
        """Always returns True by default."""
        return True


class MockAgentFactory(IAgentFactory):
    """
    Mock agent factory for testing.

    Provides a simple factory that creates MockAgent instances.
    """

    def __init__(self):
        self._agents: Dict[str, type] = {}
        self._created_agents: List[IAgent] = []

    def create_agent(
        self,
        agent_type: str,
        config: Optional[dict] = None
    ) -> IAgent:
        """Create a mock agent."""
        agent_class = self._agents.get(agent_type, MockAgent)
        agent = agent_class(name=agent_type)
        self._created_agents.append(agent)
        return agent

    def register_agent_class(
        self,
        agent_type: str,
        agent_class: type
    ) -> None:
        """Register an agent class."""
        self._agents[agent_type] = agent_class

    def list_available_agents(self) -> List[str]:
        """List registered agent types."""
        return list(self._agents.keys())

    def agent_exists(self, agent_type: str) -> bool:
        """Check if agent type is registered."""
        return agent_type in self._agents
