"""Agent implementation for MY_PLUGIN.

Replace MY_PLUGIN, MyAgent with your names.
"""

from typing import Dict, Any, Optional, List
import structlog

from gao_dev.core.interfaces.agent import IAgent

logger = structlog.get_logger()


class MyAgent(IAgent):
    """Example agent implementation.

    This is a template showing the basic structure of a GAO-Dev agent.
    Customize this to implement your agent's specific behavior.
    """

    def __init__(
        self,
        name: str = "MyAgent",  # Replace with your agent name
        role: str = "My Role",  # Replace with agent role
        tools: Optional[List[str]] = None,
        model: str = "claude-sonnet-4-5-20250929",
        **kwargs
    ):
        """Initialize the agent.

        Args:
            name: Agent name (should be unique)
            role: Agent role/responsibility
            tools: List of tool names this agent can use
            model: Claude model to use
            **kwargs: Additional configuration
        """
        self._name = name
        self._role = role
        self._tools = tools or ["Read", "Write", "Grep"]  # Customize tools
        self._model = model
        self._config = kwargs

        logger.info(
            "agent_initialized",
            agent=name,
            role=role,
            tools=self._tools,
            model=model,
        )

    @property
    def name(self) -> str:
        """Return agent name."""
        return self._name

    @property
    def role(self) -> str:
        """Return agent role."""
        return self._role

    @property
    def tools(self) -> List[str]:
        """Return list of tools this agent uses."""
        return self._tools

    @property
    def model(self) -> str:
        """Return Claude model name."""
        return self._model

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute a task.

        This is the main method where your agent's logic goes.
        Implement your agent's specific behavior here.

        Args:
            task: Task description or instruction
            context: Optional context data (workflow state, files, etc.)

        Returns:
            str: Result message or output

        Raises:
            Exception: If task execution fails
        """
        context = context or {}

        logger.info(
            "agent_execute_start",
            agent=self._name,
            task=task[:100],  # Log first 100 chars
            context_keys=list(context.keys()),
        )

        try:
            # REPLACE THIS with your agent's actual logic
            # Examples:
            # - Call Claude API with specific prompt
            # - Process files using tools
            # - Generate artifacts
            # - Update workflow state

            result = f"Agent {self._name} executed task: {task}"

            # Example: Access context data
            if "workflow_state" in context:
                workflow_state = context["workflow_state"]
                result += f" (Workflow: {workflow_state.get('name', 'unknown')})"

            logger.info(
                "agent_execute_complete",
                agent=self._name,
                task=task[:100],
                result_length=len(result),
            )

            return result

        except Exception as e:
            logger.error(
                "agent_execute_error",
                agent=self._name,
                task=task[:100],
                error=str(e),
                exc_info=True,
            )
            raise

    def validate_task(self, task: str) -> bool:
        """Validate if this agent can handle the task.

        Optional: Override to add validation logic.

        Args:
            task: Task description

        Returns:
            bool: True if agent can handle the task
        """
        # Add your validation logic here
        # Examples:
        # - Check if task matches agent's capabilities
        # - Verify required context is available
        # - Validate task format

        if not task or not isinstance(task, str):
            return False

        return True

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities.

        Optional: Override to declare specific capabilities.

        Returns:
            List[str]: List of capability descriptions
        """
        return [
            "capability1",  # Replace with actual capabilities
            "capability2",
            "capability3",
        ]

    def configure(self, config: Dict[str, Any]) -> None:
        """Update agent configuration.

        Optional: Override to support runtime configuration changes.

        Args:
            config: Configuration dictionary
        """
        self._config.update(config)
        logger.info(
            "agent_configured",
            agent=self._name,
            config_keys=list(config.keys()),
        )

    def get_config(self) -> Dict[str, Any]:
        """Return current configuration.

        Returns:
            Dict[str, Any]: Current configuration
        """
        return {
            "name": self._name,
            "role": self._role,
            "tools": self._tools,
            "model": self._model,
            **self._config,
        }
