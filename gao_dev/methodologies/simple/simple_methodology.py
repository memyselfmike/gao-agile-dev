"""Simple alternative methodology.

Story 5.5: Minimal 3-level methodology demonstrating IMethodology implementation.
"""

from typing import Dict, List, Optional, Any

from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.core.models.methodology import (
    ComplexityAssessment,
    ComplexityLevel,
    ProjectType,
    ValidationResult,
    WorkflowSequence,
    WorkflowStep,
)


class SimpleMethodology(IMethodology):
    """Simple alternative methodology.

    Demonstrates IMethodology implementation with minimal complexity.
    Uses 3 levels (SMALL, MEDIUM, LARGE), keyword-based analysis, linear workflows.

    Complexity Levels:
        SMALL: Hours - Quick task or bug fix
        MEDIUM: Days - Feature with planning
        LARGE: Weeks - Project with design

    Example:
        ```python
        from gao_dev.methodologies.simple import SimpleMethodology
        from gao_dev.methodologies.registry import MethodologyRegistry

        # Register SimpleMethodology
        registry = MethodologyRegistry.get_instance()
        registry.register_methodology(SimpleMethodology())

        # Use it
        simple = registry.get_methodology("simple")
        assessment = await simple.assess_complexity("Fix login bug")
        # Returns SMALL complexity
        ```
    """

    @property
    def name(self) -> str:
        """Methodology identifier."""
        return "simple"

    @property
    def description(self) -> str:
        """Methodology description."""
        return "Simple 3-level methodology for straightforward projects"

    @property
    def version(self) -> str:
        """Methodology version."""
        return "1.0.0"

    @property
    def supports_scale_levels(self) -> bool:
        """SimpleMethodology doesn't use scale levels."""
        return False

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Assess complexity using keyword analysis.

        Uses simple keyword matching to determine SMALL, MEDIUM, or LARGE complexity.
        No AI analysis - fast and deterministic.

        Args:
            prompt: User's project description
            context: Optional context (ignored by SimpleMethodology)

        Returns:
            ComplexityAssessment with SMALL, MEDIUM, or LARGE level
        """
        prompt_lower = prompt.lower()

        # LARGE indicators
        large_keywords = [
            "application", "system", "platform", "full stack",
            "greenfield", "from scratch", "entire", "complete"
        ]

        # SMALL indicators
        small_keywords = [
            "fix", "bug", "typo", "update", "change", "quick",
            "simple", "minor", "small"
        ]

        # Check for LARGE
        if any(kw in prompt_lower for kw in large_keywords):
            complexity = ComplexityLevel.XLARGE
            reasoning = "Detected large project keywords"
        # Check for SMALL
        elif any(kw in prompt_lower for kw in small_keywords):
            complexity = ComplexityLevel.TRIVIAL
            reasoning = "Detected small task keywords"
        # Default to MEDIUM
        else:
            complexity = ComplexityLevel.MEDIUM
            reasoning = "Default medium complexity (feature-sized)"

        return ComplexityAssessment(
            complexity_level=complexity,
            project_type=self._detect_project_type(prompt),
            confidence=0.6,  # Lower confidence (no AI analysis)
            reasoning=reasoning,
            metadata={"methodology": "simple"}
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build simple workflow sequence.

        Maps complexity to simple linear workflows:
        - TRIVIAL/SMALL: Direct implementation
        - MEDIUM: Plan → Implement → Test
        - LARGE/XLARGE: Design → Plan → Implement → Test

        Args:
            assessment: Complexity assessment result

        Returns:
            WorkflowSequence with appropriate workflows
        """
        # Map complexity to workflow
        if assessment.complexity_level in (ComplexityLevel.TRIVIAL, ComplexityLevel.SMALL):
            # SMALL: Direct implementation
            workflows = [
                WorkflowStep("implement", "implementation", required=True)
            ]
        elif assessment.complexity_level == ComplexityLevel.MEDIUM:
            # MEDIUM: Plan → Implement → Test
            workflows = [
                WorkflowStep("plan", "planning", required=True),
                WorkflowStep("implement", "implementation", required=True),
                WorkflowStep("test", "testing", required=True)
            ]
        else:  # LARGE/XLARGE
            # LARGE: Design → Plan → Implement → Test
            workflows = [
                WorkflowStep("design", "design", required=True),
                WorkflowStep("plan", "planning", required=True),
                WorkflowStep("implement", "implementation", required=True),
                WorkflowStep("test", "testing", required=True)
            ]

        return WorkflowSequence(
            workflows=workflows,
            total_phases=len({w.phase for w in workflows}),
            can_parallelize=False,
            metadata={"methodology": "simple"}
        )

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents based on phase.

        Simple phase-based agent recommendations (not BMAD-specific).

        Args:
            task: Task description
            context: Optional context with 'phase' key

        Returns:
            List of recommended agent names
        """
        context = context or {}
        phase = context.get("phase", "").lower()

        # Simple phase-based recommendations
        if "design" in phase:
            return ["Architect"]
        elif "plan" in phase:
            return ["Planner"]
        elif "implement" in phase:
            return ["Developer"]
        elif "test" in phase:
            return ["Tester"]
        else:
            return ["Developer"]  # Default

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Minimal validation.

        SimpleMethodology has no complex config requirements.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult (always valid for SimpleMethodology)
        """
        # SimpleMethodology has no complex config requirements
        return ValidationResult(valid=True, errors=[], warnings=[])

    def _detect_project_type(self, prompt: str) -> Optional[ProjectType]:
        """Simple project type detection.

        Args:
            prompt: User's project description

        Returns:
            Detected ProjectType or UNKNOWN
        """
        prompt_lower = prompt.lower()

        if "web" in prompt_lower or "website" in prompt_lower:
            return ProjectType.WEB_APP
        elif "api" in prompt_lower:
            return ProjectType.API
        elif "cli" in prompt_lower or "command" in prompt_lower:
            return ProjectType.CLI
        else:
            return ProjectType.UNKNOWN
