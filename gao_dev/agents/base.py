"""
Base agent classes for GAO-Dev.

This module provides the base implementation for all agents,
including common functionality, lifecycle management, and
specialized bases for different agent types.
"""

from abc import abstractmethod
from typing import List, AsyncGenerator, Optional
from pathlib import Path

from ..core.interfaces.agent import IAgent
from ..core.models.agent import AgentCapability, AgentContext
from .exceptions import AgentInitializationError


class BaseAgent(IAgent):
    """
    Base implementation for all GAO-Dev agents.

    Provides common functionality and enforces consistent behavior
    across all agent implementations (built-in and plugins).

    Attributes:
        name: Agent's unique name
        role: Agent's role/specialty
        persona: Agent's persona/instructions
        tools: List of available tools
        model: Claude model to use

    Example:
        ```python
        class MyAgent(BaseAgent):
            async def execute_task(self, task: str, context: AgentContext):
                # Implementation
                yield "Starting task..."
                # Do work
                yield "Task complete"

        async with MyAgent("test", "Tester", "...", ["Read"]) as agent:
            async for msg in agent.execute_task("Test something", context):
                print(msg)
        ```
    """

    def __init__(
        self,
        name: str,
        role: str,
        persona: str,
        tools: List[str],
        model: str = "claude-sonnet-4-5-20250929",
        persona_file: Optional[Path] = None
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name (e.g., "Amelia", "Mary")
            role: Agent role (e.g., "Developer", "Business Analyst")
            persona: Agent persona/instructions
            tools: List of available tools
            model: Claude model identifier
            persona_file: Optional path to persona markdown file
        """
        self._name = name
        self._role = role
        self._persona = persona
        self._tools = tools
        self._model = model
        self._persona_file = persona_file
        self._initialized = False

    @property
    def name(self) -> str:
        """Agent's unique name."""
        return self._name

    @property
    def role(self) -> str:
        """Agent's role/specialty."""
        return self._role

    @property
    def persona(self) -> str:
        """Agent's persona/instructions."""
        return self._persona

    @property
    def tools(self) -> List[str]:
        """List of available tools."""
        return self._tools.copy()  # Return copy to prevent modification

    @property
    def model(self) -> str:
        """Claude model identifier."""
        return self._model

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """
        Initialize agent resources.

        Called before agent execution. Subclasses can override to
        add custom initialization (load files, setup connections, etc.).

        Raises:
            AgentInitializationError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Load persona from file if provided
            if self._persona_file and self._persona_file.exists():
                self._persona = self._persona_file.read_text(encoding="utf-8")

            # Mark as initialized
            self._initialized = True
        except Exception as e:
            raise AgentInitializationError(
                f"Failed to initialize agent '{self.name}': {e}"
            ) from e

    async def cleanup(self) -> None:
        """
        Clean up agent resources.

        Called after agent execution. Subclasses can override to
        add custom cleanup (close connections, save state, etc.).
        """
        # Subclasses can override for custom cleanup
        self._initialized = False

    async def __aenter__(self) -> 'BaseAgent':
        """
        Async context manager entry.

        Automatically initializes agent when entering context.

        Returns:
            Self for use in async with statement
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Async context manager exit.

        Automatically cleans up agent when exiting context.

        Returns:
            False to propagate exceptions
        """
        await self.cleanup()
        return False

    @abstractmethod
    async def execute_task(
        self,
        task: str,
        context: AgentContext
    ) -> AsyncGenerator[str, None]:
        """
        Execute a task and yield progress messages.

        This is the primary method for agent execution. Subclasses
        must implement this method with their specific behavior.

        Args:
            task: Task description in natural language
            context: Execution context (project, tools, etc.)

        Yields:
            str: Progress messages during execution

        Raises:
            AgentExecutionError: If task execution fails
        """
        pass

    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get list of agent capabilities.

        Override in subclasses to define agent capabilities.

        Returns:
            List of agent capabilities
        """
        return []

    def can_handle_task(self, task: str) -> bool:
        """
        Check if agent can handle given task.

        Override in subclasses for intelligent task routing.
        Default implementation returns True (can handle any task).

        Args:
            task: Task description

        Returns:
            bool: True if agent can handle this task
        """
        return True

    def __repr__(self) -> str:
        """Developer representation."""
        return f"{self.__class__.__name__}(name='{self.name}', role='{self.role}')"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.role})"


class PlanningAgent(BaseAgent):
    """
    Base class for planning-focused agents.

    Used for agents that focus on analysis, planning, architecture,
    and design work (Mary, John, Winston, Sally).

    These agents typically work with documentation, requirements,
    and high-level design artifacts.

    Example:
        ```python
        class MaryAgent(PlanningAgent):
            async def execute_task(self, task: str, context: AgentContext):
                # Business analysis implementation
                yield "Analyzing requirements..."
        ```
    """

    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get planning agent capabilities.

        Override to add agent-specific capabilities.

        Returns:
            List of capabilities (empty by default)
        """
        return []

    def can_handle_task(self, task: str) -> bool:
        """
        Check if this planning agent can handle the task.

        Looks for planning-related keywords in the task description.

        Args:
            task: Task description

        Returns:
            bool: True if task appears to be planning-related
        """
        planning_keywords = [
            "analyze", "plan", "design", "architect", "requirement",
            "specification", "prd", "architecture", "ux", "wireframe"
        ]

        task_lower = task.lower()
        return any(keyword in task_lower for keyword in planning_keywords)


class ImplementationAgent(BaseAgent):
    """
    Base class for implementation-focused agents.

    Used for agents that focus on implementation, testing, and
    execution work (Amelia, Murat, Bob).

    These agents typically work with code, tests, and execution
    of development workflows.

    Example:
        ```python
        class AmeliaAgent(ImplementationAgent):
            async def execute_task(self, task: str, context: AgentContext):
                # Implementation work
                yield "Implementing feature..."
        ```
    """

    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get implementation agent capabilities.

        Override to add agent-specific capabilities.

        Returns:
            List of capabilities (empty by default)
        """
        return []

    def can_handle_task(self, task: str) -> bool:
        """
        Check if this implementation agent can handle the task.

        Looks for implementation-related keywords in the task description.

        Args:
            task: Task description

        Returns:
            bool: True if task appears to be implementation-related
        """
        implementation_keywords = [
            "implement", "code", "develop", "test", "fix", "debug",
            "refactor", "build", "create", "story", "feature"
        ]

        task_lower = task.lower()
        return any(keyword in task_lower for keyword in implementation_keywords)
