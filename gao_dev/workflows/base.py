"""
Base workflow classes for GAO-Dev.

This module provides the base implementation for all workflows,
using the Template Method pattern for consistent workflow execution.
"""

from abc import abstractmethod
from typing import List, Optional

from ..core.interfaces.workflow import IWorkflow
from ..core.models.workflow import (
    WorkflowIdentifier,
    WorkflowContext,
    WorkflowResult,
)
from .exceptions import (
    WorkflowExecutionError,
    WorkflowValidationError,
)


class BaseWorkflow(IWorkflow):
    """
    Base implementation for all GAO-Dev workflows.

    Provides common workflow functionality and enforces consistent
    behavior using the Template Method pattern. All workflows follow
    the same execution pattern: validate → pre-execute → execute → post-execute.

    Attributes:
        identifier: Workflow identifier (name, phase)
        description: Human-readable description
        required_tools: Tools required by this workflow
        output_file: Optional output file path

    Example:
        ```python
        class MyWorkflow(BaseWorkflow):
            def __init__(self):
                super().__init__(
                    identifier=WorkflowIdentifier("my-workflow", phase=4),
                    description="My custom workflow",
                    required_tools=["Read", "Write"]
                )

            async def _execute_impl(self, context: WorkflowContext):
                # Workflow implementation
                return ["artifact1.md", "artifact2.md"]

        # Execute workflow
        workflow = MyWorkflow()
        context = WorkflowContext(project_root=Path.cwd())
        result = await workflow.execute(context)
        ```
    """

    def __init__(
        self,
        identifier: WorkflowIdentifier,
        description: str,
        required_tools: List[str],
        output_file: Optional[str] = None
    ):
        """
        Initialize base workflow.

        Args:
            identifier: Workflow identifier
            description: Human-readable description
            required_tools: List of required tool names
            output_file: Optional output file name
        """
        self._identifier = identifier
        self._description = description
        self._required_tools = required_tools
        self._output_file = output_file

    @property
    def identifier(self) -> WorkflowIdentifier:
        """Workflow identifier."""
        return self._identifier

    @property
    def description(self) -> str:
        """Human-readable workflow description."""
        return self._description

    @property
    def required_tools(self) -> List[str]:
        """Tools required by this workflow."""
        return self._required_tools.copy()  # Return copy to prevent modification

    @property
    def output_file(self) -> Optional[str]:
        """Optional output file name."""
        return self._output_file

    async def execute(self, context: WorkflowContext) -> WorkflowResult:
        """
        Execute the workflow (Template Method).

        This is the main execution method that follows a consistent pattern:
        1. Validate context
        2. Pre-execution hook
        3. Execute workflow implementation
        4. Post-execution hook
        5. Return result

        Args:
            context: Workflow execution context

        Returns:
            WorkflowResult: Execution result with artifacts

        Raises:
            WorkflowValidationError: If context validation fails
            WorkflowExecutionError: If execution fails
        """
        try:
            # Step 1: Validate context
            if not self.validate_context(context):
                raise WorkflowValidationError(
                    f"Context validation failed for workflow '{self.identifier.name}'"
                )

            # Step 2: Pre-execution hook
            await self._pre_execute(context)

            # Step 3: Execute workflow implementation
            artifacts = await self._execute_impl(context)

            # Step 4: Post-execution hook
            await self._post_execute(context, artifacts)

            # Step 5: Return result
            return WorkflowResult(
                success=True,
                workflow_name=self.identifier.name,
                artifacts=artifacts,
                metadata={"phase": self.identifier.phase}
            )

        except WorkflowValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in WorkflowExecutionError
            raise WorkflowExecutionError(
                f"Workflow execution failed: {e}",
                workflow_name=self.identifier.name
            ) from e

    def validate_context(self, context: WorkflowContext) -> bool:
        """
        Validate that workflow can execute with given context.

        Default implementation checks:
        - Project root exists
        - Required parameters present

        Override in subclasses for custom validation.

        Args:
            context: Workflow context to validate

        Returns:
            bool: True if context is valid, False otherwise
        """
        # Check project root exists
        if not context.project_root.exists():
            return False

        # Subclasses can add more validation
        return self._validate_context_impl(context)

    def _validate_context_impl(self, context: WorkflowContext) -> bool:
        """
        Custom context validation (override in subclasses).

        Args:
            context: Workflow context

        Returns:
            bool: True if valid
        """
        return True

    async def _pre_execute(self, context: WorkflowContext) -> None:
        """
        Pre-execution hook (override in subclasses).

        Called before workflow execution. Use for setup tasks:
        - Create directories
        - Load configuration
        - Validate prerequisites

        Args:
            context: Workflow context
        """
        pass  # Default: no-op

    @abstractmethod
    async def _execute_impl(self, context: WorkflowContext) -> List[str]:
        """
        Workflow implementation (subclasses must implement).

        This is the core workflow logic that subclasses must provide.

        Args:
            context: Workflow execution context

        Returns:
            List[str]: List of artifact paths created by workflow

        Raises:
            WorkflowExecutionError: If execution fails
        """
        pass

    async def _post_execute(
        self,
        context: WorkflowContext,
        artifacts: List[str]
    ) -> None:
        """
        Post-execution hook (override in subclasses).

        Called after successful workflow execution. Use for cleanup tasks:
        - Validate artifacts
        - Update metadata
        - Trigger notifications

        Args:
            context: Workflow context
            artifacts: List of created artifacts
        """
        pass  # Default: no-op

    def get_expected_artifacts(self) -> List[str]:
        """
        Get list of artifacts this workflow produces.

        Override in subclasses to specify expected artifacts.

        Returns:
            List of artifact identifiers
        """
        if self.output_file:
            return [self.output_file]
        return []

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"{self.__class__.__name__}("
            f"identifier={self.identifier.name}, "
            f"phase={self.identifier.phase})"
        )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.identifier.name} (phase {self.identifier.phase})"
