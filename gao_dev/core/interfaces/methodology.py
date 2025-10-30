"""Methodology interface for development process abstraction.

This module defines the IMethodology interface that all development methodologies
must implement. This abstraction allows GAO-Dev to support multiple methodologies
(BMAD, Scrum, Kanban, custom) interchangeably.

Story 5.1: IMethodology Interface (Epic 5 - Methodology Abstraction)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from gao_dev.core.models.methodology import (
    ComplexityAssessment,
    ValidationResult,
    WorkflowSequence,
)


class IMethodology(ABC):
    """Interface for development methodologies.

    Methodologies define how GAO-Dev analyzes complexity, selects workflows,
    and recommends agents. This abstraction allows supporting BMAD, Scrum,
    Kanban, or custom methodologies without core code changes.

    A methodology implementation provides:
    - Complexity assessment logic (analyze user prompts)
    - Workflow sequence generation (select appropriate workflows)
    - Agent recommendations (which agents for which tasks)
    - Configuration validation (methodology-specific settings)

    Example:
        ```python
        class MyMethodology(IMethodology):
            @property
            def name(self) -> str:
                return "my-methodology"

            @property
            def description(self) -> str:
                return "My custom development methodology"

            @property
            def version(self) -> str:
                return "1.0.0"

            async def assess_complexity(
                self,
                prompt: str,
                context: Optional[Dict[str, Any]] = None
            ) -> ComplexityAssessment:
                # Analyze prompt and return assessment
                return ComplexityAssessment(
                    complexity_level=ComplexityLevel.MEDIUM,
                    reasoning="Detected API project with authentication"
                )

            def build_workflow_sequence(
                self,
                assessment: ComplexityAssessment
            ) -> WorkflowSequence:
                # Return workflows based on complexity
                return WorkflowSequence(
                    workflows=[
                        WorkflowStep("create-prd", "planning"),
                        WorkflowStep("implement", "implementation")
                    ]
                )

            def get_recommended_agents(
                self,
                task: str,
                context: Optional[Dict[str, Any]] = None
            ) -> List[str]:
                # Recommend agents for task
                return ["Developer", "Tester"]

            def validate_config(
                self,
                config: Dict[str, Any]
            ) -> ValidationResult:
                # Validate methodology-specific config
                return ValidationResult(valid=True)
        ```

    Attributes:
        name: Unique methodology identifier (e.g., "bmad", "scrum")
        description: Human-readable description
        version: Methodology version (semantic versioning)
        supports_scale_levels: Whether uses scale levels concept (BMAD-specific)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique methodology identifier.

        Must be lowercase kebab-case (e.g., "bmad", "scrum", "my-methodology").
        Used for configuration and registry lookup.

        Returns:
            Lowercase kebab-case name
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable methodology description.

        Brief description of the methodology's approach and use cases.

        Returns:
            Description string (1-2 sentences)
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Methodology version using semantic versioning.

        Returns:
            Version string (e.g., "1.0.0", "2.1.0-beta")
        """
        pass

    @property
    def supports_scale_levels(self) -> bool:
        """Whether methodology uses scale levels concept.

        BMAD uses scale levels (0-4) for granular complexity classification.
        Other methodologies may use simpler categorization.

        Default: False

        Returns:
            True if methodology uses scale levels, False otherwise
        """
        return False

    @abstractmethod
    async def assess_complexity(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Analyze user prompt to determine project complexity.

        Methodologies analyze the initial prompt to understand project scope,
        complexity, and type. This assessment drives workflow selection.

        Args:
            prompt: User's initial request/prompt
            context: Optional context (project history, files, preferences, etc.)

        Returns:
            ComplexityAssessment with level, type, estimates, reasoning, metadata
        """
        pass

    @abstractmethod
    def build_workflow_sequence(
        self, assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build workflow sequence based on complexity assessment.

        Takes the complexity assessment and generates an ordered sequence
        of workflows to execute.

        Args:
            assessment: ComplexityAssessment from assess_complexity()

        Returns:
            WorkflowSequence with ordered WorkflowSteps
        """
        pass

    @abstractmethod
    def get_recommended_agents(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents for a specific task.

        Methodologies recommend which agents should work on specific tasks
        based on the task type, workflow phase, and context.

        Args:
            task: Task description or workflow name
            context: Optional context (phase, workflow, project_type, etc.)

        Returns:
            List of agent names to assign to task
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate methodology-specific configuration.

        Each methodology can have custom configuration options. This method
        validates those options and returns structured results.

        Args:
            config: Configuration dictionary with methodology-specific settings

        Returns:
            ValidationResult with valid flag, errors, and warnings
        """
        pass


# IMethodologyRegistry moved to Story 5.3
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
