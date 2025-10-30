"""Example workflow plugin for testing."""

from typing import Type
from gao_dev.plugins import BaseWorkflowPlugin, WorkflowMetadata
from gao_dev.core.interfaces.workflow import IWorkflow
from gao_dev.core.models.workflow import WorkflowIdentifier
from .workflow import ExampleWorkflow


class ExampleWorkflowPlugin(BaseWorkflowPlugin):
    """Example workflow plugin demonstrating the plugin API.

    This plugin shows how to:
    - Extend BaseWorkflowPlugin
    - Provide workflow class, identifier, and metadata
    - Integrate with GAO-Dev's workflow system
    """

    def get_workflow_class(self) -> Type[IWorkflow]:
        """Return the ExampleWorkflow class."""
        return ExampleWorkflow

    def get_workflow_identifier(self) -> WorkflowIdentifier:
        """Return the unique workflow identifier."""
        return WorkflowIdentifier("example-workflow", phase=1)

    def get_workflow_metadata(self) -> WorkflowMetadata:
        """Return workflow metadata."""
        return WorkflowMetadata(
            name="example-workflow",
            description="Example workflow for testing plugin system",
            phase=1,
            tags=["example", "testing"],
            required_tools=["Read", "Write"]
        )
