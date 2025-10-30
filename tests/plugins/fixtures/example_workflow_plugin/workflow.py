"""Example workflow implementation for testing."""

from typing import List
from gao_dev.core.interfaces.workflow import IWorkflow
from gao_dev.core.models.workflow import WorkflowIdentifier


class ExampleWorkflow(IWorkflow):
    """Example workflow for plugin system testing.

    This workflow demonstrates how to create a custom workflow that
    can be registered via the plugin system.
    """

    @property
    def identifier(self) -> WorkflowIdentifier:
        """Return workflow identifier."""
        return WorkflowIdentifier("example-workflow", phase=1)

    @property
    def description(self) -> str:
        """Return workflow description."""
        return "Example workflow for testing the plugin system"

    @property
    def required_tools(self) -> List[str]:
        """Return required tools."""
        return ["Read", "Write"]

    async def execute(self, context):
        """Execute the workflow.

        Args:
            context: Workflow context

        Returns:
            WorkflowResult with success status
        """
        # Simple implementation for testing
        from gao_dev.core.models.workflow import WorkflowResult

        return WorkflowResult(
            success=True,
            artifacts=[],
            message="Example workflow executed successfully"
        )

    def validate_context(self, context) -> bool:
        """Validate workflow context.

        Args:
            context: Workflow context

        Returns:
            True if context is valid
        """
        return True
