"""Workflow plugin API for GAO-Dev.

This module provides the plugin API for creating custom workflow plugins.
"""

from abc import abstractmethod
from typing import Type
import structlog

from .base_plugin import BasePlugin
from .models import WorkflowMetadata
from ..core.interfaces.workflow import IWorkflow
from ..core.models.workflow import WorkflowIdentifier
from .exceptions import PluginError

logger = structlog.get_logger(__name__)


class BaseWorkflowPlugin(BasePlugin):
    """Base class for workflow plugins.

    Workflow plugins provide custom workflows that integrate with GAO-Dev's
    workflow system. Plugin workflows have access to the same context and
    tools as built-in workflows.

    Subclasses must implement:
    - get_workflow_class(): Return workflow class implementing IWorkflow
    - get_workflow_identifier(): Return unique workflow identifier
    - get_workflow_metadata(): Return workflow metadata

    Example:
        ```python
        from gao_dev.plugins import BaseWorkflowPlugin, WorkflowMetadata
        from gao_dev.core.interfaces.workflow import IWorkflow
        from gao_dev.core.models.workflow import WorkflowIdentifier

        class DomainAnalysisWorkflow(IWorkflow):
            @property
            def identifier(self):
                return WorkflowIdentifier("domain-analysis", phase=1)

            @property
            def description(self):
                return "Analyze domain-specific requirements"

            @property
            def required_tools(self):
                return ["Read", "Grep", "WebFetch"]

            async def execute(self, context):
                # Implementation
                pass

            def validate_context(self, context):
                return True

        class DomainAnalysisPlugin(BaseWorkflowPlugin):
            def get_workflow_class(self):
                return DomainAnalysisWorkflow

            def get_workflow_identifier(self):
                return WorkflowIdentifier("domain-analysis", phase=1)

            def get_workflow_metadata(self):
                return WorkflowMetadata(
                    name="domain-analysis",
                    description="Analyze domain-specific requirements",
                    phase=1,
                    tags=["analysis", "domain"],
                    required_tools=["Read", "Grep", "WebFetch"]
                )
        ```
    """

    @abstractmethod
    def get_workflow_class(self) -> Type[IWorkflow]:
        """Get the workflow class to register.

        Returns:
            Workflow class implementing IWorkflow interface

        Raises:
            PluginError: If workflow class doesn't implement IWorkflow
        """
        pass

    @abstractmethod
    def get_workflow_identifier(self) -> WorkflowIdentifier:
        """Get unique workflow identifier.

        This identifier will be used to register the workflow.
        Must be unique across all workflows (built-in and plugins).

        Returns:
            WorkflowIdentifier (name and optional phase)
        """
        pass

    @abstractmethod
    def get_workflow_metadata(self) -> WorkflowMetadata:
        """Get workflow metadata.

        Returns:
            WorkflowMetadata with workflow details (description, phase, tags, tools)
        """
        pass

    def validate_workflow_class(self) -> None:
        """Validate that workflow class implements IWorkflow interface.

        Raises:
            PluginError: If workflow class doesn't implement IWorkflow
        """
        workflow_class = self.get_workflow_class()

        if not isinstance(workflow_class, type):
            raise PluginError(
                f"get_workflow_class() must return a class, got {type(workflow_class)}"
            )

        if not issubclass(workflow_class, IWorkflow):
            raise PluginError(
                f"Workflow class '{workflow_class.__name__}' must implement IWorkflow interface"
            )

        logger.debug(
            "workflow_class_validated",
            workflow_class=workflow_class.__name__,
            workflow_name=self.get_workflow_identifier().name
        )
