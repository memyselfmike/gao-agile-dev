"""
Agent-related exceptions.

This module defines exceptions for agent execution and lifecycle errors.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass


class AgentExecutionError(AgentError):
    """
    Exception raised when agent task execution fails.

    This includes failures during task execution, invalid inputs,
    or execution timeouts.
    """

    def __init__(self, message: str, agent_name: str = None, task: str = None):
        """
        Initialize execution error.

        Args:
            message: Error message
            agent_name: Name of agent that failed
            task: Task that failed
        """
        self.agent_name = agent_name
        self.task = task
        super().__init__(message)

    def __str__(self) -> str:
        """String representation."""
        parts = [super().__str__()]
        if self.agent_name:
            parts.append(f"Agent: {self.agent_name}")
        if self.task:
            parts.append(f"Task: {self.task}")
        return " | ".join(parts)


class AgentInitializationError(AgentError):
    """Exception raised when agent initialization fails."""
    pass


class AgentNotFoundError(AgentError):
    """Exception raised when requested agent does not exist."""
    pass


class AgentCreationError(AgentError):
    """Exception raised when agent creation fails."""
    pass


class AgentValidationError(AgentError):
    """Exception raised when agent validation fails."""
    pass


class RegistrationError(AgentError):
    """Exception raised when agent registration fails."""
    pass


class DuplicateRegistrationError(AgentError):
    """Exception raised when attempting to register duplicate agent type."""
    pass
