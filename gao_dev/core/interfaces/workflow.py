"""
Workflow interfaces for GAO-Dev workflow system.

This module defines the contract for workflows and workflow management.
Workflows represent sequences of steps to accomplish development tasks.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class IWorkflow(ABC):
    """
    Interface for all GAO-Dev workflows (built-in and plugins).

    A workflow represents a defined sequence of steps to accomplish a
    development task (e.g., create PRD, implement story, run tests).

    Example:
        ```python
        class CreateStoryWorkflow(IWorkflow):
            @property
            def identifier(self) -> WorkflowIdentifier:
                return WorkflowIdentifier("create-story", phase=4)

            async def execute(self, context: WorkflowContext):
                # Workflow implementation
                return WorkflowResult(success=True, artifacts=[...])
        ```
    """

    @property
    @abstractmethod
    def identifier(self) -> 'WorkflowIdentifier':  # Forward reference
        """
        Workflow identifier.

        Returns:
            WorkflowIdentifier: Unique identifier for this workflow
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable workflow description.

        Returns:
            str: Description of what this workflow does
        """
        pass

    @property
    @abstractmethod
    def required_tools(self) -> List[str]:
        """
        Tools required by this workflow.

        Returns:
            List of tool names required (e.g., ["Read", "Write", "Bash"])
        """
        pass

    @abstractmethod
    async def execute(
        self,
        context: 'WorkflowContext'  # Forward reference
    ) -> 'WorkflowResult':  # Forward reference
        """
        Execute the workflow.

        This is the primary method that runs the workflow steps and
        produces the expected artifacts.

        Args:
            context: Execution context (project, parameters, etc.)

        Returns:
            WorkflowResult: Execution result with artifacts and status

        Raises:
            WorkflowExecutionError: If workflow execution fails
            ValidationError: If context validation fails
        """
        pass

    @abstractmethod
    def validate_context(self, context: 'WorkflowContext') -> bool:  # Forward reference
        """
        Validate that workflow can execute with given context.

        This method checks prerequisites before execution, allowing
        workflows to fail fast if required inputs are missing.

        Args:
            context: Execution context to validate

        Returns:
            bool: True if context is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_expected_artifacts(self) -> List[str]:
        """
        Get list of artifacts this workflow produces.

        Returns:
            List of artifact paths/identifiers this workflow creates
        """
        pass


class IWorkflowRegistry(ABC):
    """
    Registry interface for workflow discovery and management.

    The registry maintains all available workflows (built-in and plugins)
    and provides methods to discover and retrieve them.

    Example:
        ```python
        registry = DefaultWorkflowRegistry()
        registry.register_workflow(create_story_workflow)

        workflow = registry.get_workflow("create-story")
        phase_2_workflows = registry.list_workflows(phase=2)
        ```
    """

    @abstractmethod
    def register_workflow(self, workflow: IWorkflow) -> None:
        """
        Register a workflow in the registry.

        Args:
            workflow: Workflow instance to register

        Raises:
            RegistrationError: If workflow invalid
            DuplicateRegistrationError: If workflow already registered
        """
        pass

    @abstractmethod
    def get_workflow(self, name: str) -> Optional[IWorkflow]:
        """
        Get a workflow by name.

        Args:
            name: Workflow name (e.g., "create-story", "prd")

        Returns:
            IWorkflow if found, None otherwise
        """
        pass

    @abstractmethod
    def list_workflows(
        self,
        phase: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[IWorkflow]:
        """
        List workflows with optional filtering.

        Args:
            phase: Filter by BMAD phase (0-4), None for all
            tags: Filter by tags, None for all

        Returns:
            List of workflows matching filters
        """
        pass

    @abstractmethod
    def workflow_exists(self, name: str) -> bool:
        """
        Check if a workflow is registered.

        Args:
            name: Workflow name

        Returns:
            bool: True if workflow exists, False otherwise
        """
        pass

    @abstractmethod
    def unregister_workflow(self, name: str) -> None:
        """
        Remove a workflow from the registry.

        Args:
            name: Workflow name to unregister

        Raises:
            WorkflowNotFoundError: If workflow not registered
        """
        pass

    @abstractmethod
    def get_workflow_count(self) -> int:
        """
        Get total number of registered workflows.

        Returns:
            int: Number of workflows in registry
        """
        pass
