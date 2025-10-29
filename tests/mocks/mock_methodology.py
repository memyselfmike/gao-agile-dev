"""Mock methodology implementation for testing."""

from typing import List, Dict, Any, Optional
from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.core.models.workflow import ComplexityLevel, WorkflowSequence, WorkflowIdentifier


class MockMethodology(IMethodology):
    """Mock methodology for testing."""

    def __init__(
        self,
        name: str = "MockMethodology",
        version: str = "1.0",
        complexity_level: int = 1,
        workflows: Optional[List[str]] = None
    ):
        self._name = name
        self._version = version
        self._complexity_level = complexity_level
        self._workflows = workflows or ["test-workflow"]
        self.assessments_made: List[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return f"Mock methodology for testing"

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityLevel:
        """Return predefined complexity level."""
        self.assessments_made.append(prompt)
        return ComplexityLevel.from_scale_level(self._complexity_level)

    def build_workflow_sequence(
        self,
        assessment: ComplexityLevel
    ) -> WorkflowSequence:
        """Return predefined workflow sequence."""
        identifiers = [
            WorkflowIdentifier(name, phase=-1)
            for name in self._workflows
        ]
        return WorkflowSequence(identifiers)

    def get_recommended_agents(
        self,
        assessment: ComplexityLevel
    ) -> List[str]:
        """Return predefined agent list."""
        return ["MockAgent"]

    def get_phases(self) -> List[Any]:
        """Return empty phases list."""
        return []

    def validate_workflow_sequence(
        self,
        sequence: WorkflowSequence
    ) -> bool:
        """Always returns True."""
        return True

    def get_quality_gates(
        self,
        assessment: ComplexityLevel
    ) -> List[Any]:
        """Return empty quality gates list."""
        return []
