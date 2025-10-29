"""Mock workflow implementations for testing."""

from typing import List, Optional, Dict
from gao_dev.core.interfaces.workflow import IWorkflow, IWorkflowRegistry
from gao_dev.core.models.workflow import (
    WorkflowIdentifier,
    WorkflowContext,
    WorkflowResult,
)


class MockWorkflow(IWorkflow):
    """Mock workflow for testing."""

    def __init__(
        self,
        identifier: WorkflowIdentifier,
        description: str = "Mock workflow",
        required_tools: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        should_succeed: bool = True
    ):
        self._identifier = identifier
        self._description = description
        self._required_tools = required_tools or []
        self._artifacts = artifacts or []
        self._should_succeed = should_succeed
        self.executions: List[WorkflowContext] = []

    @property
    def identifier(self) -> WorkflowIdentifier:
        return self._identifier

    @property
    def description(self) -> str:
        return self._description

    @property
    def required_tools(self) -> List[str]:
        return self._required_tools.copy()

    async def execute(self, context: WorkflowContext) -> WorkflowResult:
        """Execute workflow and return predefined result."""
        self.executions.append(context)
        return WorkflowResult(
            success=self._should_succeed,
            workflow_name=self.identifier.name,
            artifacts=self._artifacts.copy()
        )

    def validate_context(self, context: WorkflowContext) -> bool:
        """Always returns True by default."""
        return True

    def get_expected_artifacts(self) -> List[str]:
        """Return predefined artifacts."""
        return self._artifacts.copy()


class MockWorkflowRegistry(IWorkflowRegistry):
    """Mock workflow registry for testing."""

    def __init__(self):
        self._workflows: Dict[str, IWorkflow] = {}

    def register_workflow(self, workflow: IWorkflow) -> None:
        """Register a workflow."""
        self._workflows[workflow.identifier.name] = workflow

    def get_workflow(self, name: str) -> Optional[IWorkflow]:
        """Get workflow by name."""
        return self._workflows.get(name)

    def list_workflows(
        self,
        phase: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[IWorkflow]:
        """List all workflows (ignoring filters for simplicity)."""
        return list(self._workflows.values())

    def workflow_exists(self, name: str) -> bool:
        """Check if workflow exists."""
        return name in self._workflows

    def unregister_workflow(self, name: str) -> None:
        """Unregister a workflow."""
        self._workflows.pop(name, None)

    def get_workflow_count(self) -> int:
        """Get count of registered workflows."""
        return len(self._workflows)
