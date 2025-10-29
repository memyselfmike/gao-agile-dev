"""
Methodology interfaces for development process abstraction.

This module defines the interface for development methodologies,
enabling GAO-Dev to support multiple development processes
(BMAD, Scrum, Kanban, custom methodologies).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class IMethodology(ABC):
    """
    Interface for development methodologies.

    A methodology defines how to assess project complexity and
    build appropriate workflow sequences. This abstraction allows
    GAO-Dev to support multiple development processes beyond BMAD.

    Example:
        ```python
        class BMADMethodology(IMethodology):
            @property
            def name(self) -> str:
                return "BMAD Method"

            async def assess_complexity(self, prompt: str):
                # Analyze prompt using Claude
                return ComplexityAssessment(level=3, ...)

            def build_workflow_sequence(self, assessment):
                # Build workflow based on scale level
                return WorkflowSequence([...])
        ```
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Methodology name.

        Returns:
            str: Human-readable methodology name (e.g., "BMAD Method", "Scrum")
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Methodology version.

        Returns:
            str: Version string (e.g., "6.0", "1.0")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Methodology description.

        Returns:
            str: Brief description of the methodology
        """
        pass

    @abstractmethod
    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> 'ComplexityAssessment':  # Forward reference
        """
        Assess project complexity from user prompt.

        Different methodologies may use different complexity models:
        - BMAD: Scale levels 0-4
        - Simple: Small/Medium/Large
        - Custom: Domain-specific complexity metrics

        Args:
            prompt: User's project description/request
            context: Optional additional context

        Returns:
            ComplexityAssessment: Assessment result with complexity level

        Raises:
            AssessmentError: If complexity assessment fails
        """
        pass

    @abstractmethod
    def build_workflow_sequence(
        self,
        assessment: 'ComplexityAssessment'  # Forward reference
    ) -> 'WorkflowSequence':  # Forward reference
        """
        Build workflow sequence based on complexity assessment.

        The methodology determines which workflows to run and in what order
        based on the project's assessed complexity.

        Args:
            assessment: Complexity assessment result

        Returns:
            WorkflowSequence: Ordered sequence of workflows to execute

        Raises:
            WorkflowBuildError: If workflow sequence cannot be built
        """
        pass

    @abstractmethod
    def get_recommended_agents(
        self,
        assessment: 'ComplexityAssessment'  # Forward reference
    ) -> List[str]:
        """
        Get recommended agent types for the project.

        Different complexity levels may require different agent combinations:
        - Simple projects: Just developer + QA
        - Complex projects: Full team (PM, Architect, Dev, QA, etc.)

        Args:
            assessment: Complexity assessment result

        Returns:
            List of recommended agent type identifiers
        """
        pass

    @abstractmethod
    def get_phases(self) -> List['MethodologyPhase']:  # Forward reference
        """
        Get methodology phases.

        Phases represent major stages in the methodology:
        - BMAD: Analysis, Planning, Solutioning, Implementation
        - Scrum: Sprint Planning, Daily Scrum, Review, Retrospective
        - Custom: Methodology-specific phases

        Returns:
            List of methodology phases
        """
        pass

    @abstractmethod
    def validate_workflow_sequence(
        self,
        sequence: 'WorkflowSequence'  # Forward reference
    ) -> bool:
        """
        Validate that a workflow sequence is valid for this methodology.

        Ensures workflow order follows methodology rules:
        - Required workflows present
        - Dependencies satisfied
        - Phase ordering correct

        Args:
            sequence: Workflow sequence to validate

        Returns:
            bool: True if sequence is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_quality_gates(
        self,
        assessment: 'ComplexityAssessment'  # Forward reference
    ) -> List['QualityGate']:  # Forward reference
        """
        Get quality gates for the project based on complexity.

        Quality gates are checkpoints that must pass before proceeding:
        - Simple: Basic tests passing
        - Complex: Architecture review, security scan, performance tests

        Args:
            assessment: Complexity assessment result

        Returns:
            List of quality gates to enforce
        """
        pass


class IMethodologyRegistry(ABC):
    """
    Registry interface for methodology discovery and management.

    Allows multiple methodologies to be registered and selected
    per project.

    Example:
        ```python
        registry = MethodologyRegistry()
        registry.register(BMADMethodology())
        registry.register(ScrumMethodology())

        methodology = registry.get_methodology("BMAD")
        ```
    """

    @abstractmethod
    def register_methodology(self, methodology: IMethodology) -> None:
        """
        Register a methodology.

        Args:
            methodology: Methodology to register

        Raises:
            RegistrationError: If methodology invalid
            DuplicateRegistrationError: If name already registered
        """
        pass

    @abstractmethod
    def get_methodology(self, name: str) -> Optional[IMethodology]:
        """
        Get a methodology by name.

        Args:
            name: Methodology name

        Returns:
            IMethodology if found, None otherwise
        """
        pass

    @abstractmethod
    def list_methodologies(self) -> List[str]:
        """
        List all registered methodology names.

        Returns:
            List of methodology names
        """
        pass

    @abstractmethod
    def get_default_methodology(self) -> IMethodology:
        """
        Get the default methodology.

        Returns:
            IMethodology: Default methodology (typically BMAD)

        Raises:
            NoDefaultMethodologyError: If no default set
        """
        pass

    @abstractmethod
    def set_default_methodology(self, name: str) -> None:
        """
        Set the default methodology.

        Args:
            name: Methodology name to set as default

        Raises:
            MethodologyNotFoundError: If methodology not registered
        """
        pass
