"""
Workflow-related exceptions.

This module defines exceptions for workflow execution and validation errors.
"""


class WorkflowError(Exception):
    """Base exception for all workflow-related errors."""
    pass


class WorkflowExecutionError(WorkflowError):
    """
    Exception raised when workflow execution fails.

    This includes failures during workflow execution, step failures,
    or workflow timeouts.
    """

    def __init__(self, message: str, workflow_name: str = None, step: str = None):
        """
        Initialize execution error.

        Args:
            message: Error message
            workflow_name: Name of workflow that failed
            step: Workflow step that failed
        """
        self.workflow_name = workflow_name
        self.step = step
        super().__init__(message)

    def __str__(self) -> str:
        """String representation."""
        parts = [super().__str__()]
        if self.workflow_name:
            parts.append(f"Workflow: {self.workflow_name}")
        if self.step:
            parts.append(f"Step: {self.step}")
        return " | ".join(parts)


class WorkflowValidationError(WorkflowError):
    """Exception raised when workflow validation fails."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Exception raised when requested workflow does not exist."""
    pass


class WorkflowContextError(WorkflowError):
    """Exception raised when workflow context is invalid."""
    pass
