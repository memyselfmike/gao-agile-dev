"""Adaptive Agile Methodology implementation.

Scale-adaptive agile methodology with 5 levels (0-4).
Extracted from brian_orchestrator.py (Story 5.2).
"""

from typing import Any, Dict, List, Optional

from gao_dev.core.interfaces.methodology import IMethodology
from gao_dev.core.models.methodology import (
    ComplexityAssessment,
    ComplexityLevel,
    ProjectType,
    ValidationResult,
    WorkflowSequence,
)

from .scale_levels import (
    ScaleLevel,
    estimate_epics_from_scale,
    estimate_stories_from_scale,
    map_scale_to_complexity,
)
from .workflow_selector import WorkflowSelector
from .agent_recommender import AgentRecommender


class AdaptiveAgileMethodology(IMethodology):
    """Adaptive agile methodology with 5 scale levels.

    A scale-adaptive approach that adjusts workflow complexity based on
    project scope. Applicable to software engineering, content creation,
    business processes, and operational projects.

    Originally based on BMAD Method principles, generalized for broader use.

    Scale Levels:
        0: Chore (minutes) - Simple task, no planning needed
        1: Bug Fix (hours) - Quick fix with verification
        2: Small Feature (days) - 3-8 stories, basic planning
        3: Medium Feature (weeks) - 12-20 stories, full workflow
        4: Greenfield (months) - 40+ stories, complete lifecycle

    Features:
        - Scale-adaptive workflow selection
        - Complexity-driven agent recommendations
        - 4 phases: Analysis, Planning, Solutioning, Implementation
        - 7 specialized agents for software projects
        - Extensible for non-engineering projects

    Example:
        ```python
        from gao_dev.methodologies.adaptive_agile import AdaptiveAgileMethodology

        methodology = AdaptiveAgileMethodology()

        # Assess complexity
        assessment = await methodology.assess_complexity(
            "Build a todo app with auth and real-time sync"
        )

        # Get workflows
        sequence = methodology.build_workflow_sequence(assessment)

        # Get agents
        agents = methodology.get_recommended_agents(
            "create architecture",
            context={"phase": "solutioning"}
        )
        ```

    Attributes:
        workflow_selector: Selects workflows based on scale level
        agent_recommender: Recommends agents for tasks
    """

    def __init__(self):
        """Initialize Adaptive Agile Methodology."""
        self.workflow_selector = WorkflowSelector()
        self.agent_recommender = AgentRecommender()

    @property
    def name(self) -> str:
        """Methodology identifier.

        Returns:
            "adaptive-agile"
        """
        return "adaptive-agile"

    @property
    def description(self) -> str:
        """Methodology description.

        Returns:
            Brief description of methodology
        """
        return "Adaptive agile methodology with 5 scale levels (0-4)"

    @property
    def version(self) -> str:
        """Methodology version.

        Returns:
            Semantic version string
        """
        return "1.0.0"

    @property
    def supports_scale_levels(self) -> bool:
        """Whether methodology uses scale levels.

        Returns:
            True (Adaptive Agile uses 5 scale levels)
        """
        return True

    async def assess_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """Assess project complexity from user prompt.

        Uses keyword-based analysis to determine scale level (0-4).
        For production use, this can be enhanced with AI analysis
        (Claude API) for more accurate assessments.

        Args:
            prompt: User's project description/request
            context: Optional context (project history, files, etc.)

        Returns:
            ComplexityAssessment with scale level in metadata

        Example:
            ```python
            assessment = await methodology.assess_complexity(
                "Fix login button color"
            )
            # Returns: ScaleLevel.LEVEL_1_BUG_FIX

            assessment = await methodology.assess_complexity(
                "Build complete e-commerce platform"
            )
            # Returns: ScaleLevel.LEVEL_4_GREENFIELD
            ```
        """
        context = context or {}
        prompt_lower = prompt.lower()

        # Analyze prompt for complexity indicators
        scale_level = self._analyze_prompt_keywords(prompt_lower)

        # Detect project type
        project_type = self._detect_project_type(prompt_lower)

        # Map scale to complexity
        complexity_level = map_scale_to_complexity(scale_level)

        # Estimate stories and epics
        estimated_stories = estimate_stories_from_scale(scale_level)
        estimated_epics = estimate_epics_from_scale(scale_level)

        # Build reasoning
        reasoning = self._build_reasoning(
            scale_level,
            prompt_lower,
            complexity_level
        )

        return ComplexityAssessment(
            complexity_level=complexity_level,
            project_type=project_type,
            estimated_stories=estimated_stories,
            estimated_epics=estimated_epics,
            confidence=0.7,  # Keyword-based has moderate confidence
            reasoning=reasoning,
            metadata={
                "methodology": "adaptive-agile",
                "scale_level": scale_level.value,
                "analysis_method": "keyword-based"
            }
        )

    def _analyze_prompt_keywords(self, prompt_lower: str) -> ScaleLevel:
        """Analyze prompt keywords to determine scale level.

        Args:
            prompt_lower: Lowercase prompt text

        Returns:
            Determined scale level
        """
        # Level 4 indicators (Greenfield)
        level_4_keywords = [
            "application", "platform", "system", "full stack",
            "greenfield", "from scratch", "entire", "complete",
            "e-commerce", "marketplace", "social network",
            "cms", "management system"
        ]

        # Level 3 indicators (Medium Feature)
        level_3_keywords = [
            "complex", "feature", "module", "integration",
            "architecture", "refactor", "redesign", "major"
        ]

        # Level 0 indicators (Chore)
        level_0_keywords = [
            "typo", "fix typo", "update", "change color",
            "rename", "config", "setting", "minor change"
        ]

        # Level 1 indicators (Bug Fix)
        level_1_keywords = [
            "fix", "bug", "issue", "error", "broken",
            "doesn't work", "not working", "quick fix"
        ]

        # Check for level 4 (highest priority)
        if any(kw in prompt_lower for kw in level_4_keywords):
            return ScaleLevel.LEVEL_4_GREENFIELD

        # Check for level 0 (specific chores)
        if any(kw in prompt_lower for kw in level_0_keywords):
            return ScaleLevel.LEVEL_0_CHORE

        # Check for level 1 (bug fixes)
        if any(kw in prompt_lower for kw in level_1_keywords):
            return ScaleLevel.LEVEL_1_BUG_FIX

        # Check for level 3 (complex features)
        if any(kw in prompt_lower for kw in level_3_keywords):
            return ScaleLevel.LEVEL_3_MEDIUM_FEATURE

        # Default to level 2 (small feature)
        return ScaleLevel.LEVEL_2_SMALL_FEATURE

    def _detect_project_type(self, prompt_lower: str) -> Optional[ProjectType]:
        """Detect project type from prompt.

        Args:
            prompt_lower: Lowercase prompt text

        Returns:
            Detected ProjectType or None
        """
        type_keywords = {
            ProjectType.WEB_APP: ["web", "website", "webapp", "frontend", "backend"],
            ProjectType.API: ["api", "rest", "graphql", "endpoint"],
            ProjectType.CLI: ["cli", "command line", "terminal", "script"],
            ProjectType.LIBRARY: ["library", "package", "sdk", "framework"],
            ProjectType.MOBILE_APP: ["mobile", "ios", "android", "app"],
            ProjectType.DESKTOP_APP: ["desktop", "electron", "native app"],
            ProjectType.DATA_PIPELINE: ["pipeline", "etl", "data processing"],
            ProjectType.ML_MODEL: ["ml", "machine learning", "model", "ai"],
        }

        for project_type, keywords in type_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return project_type

        return ProjectType.UNKNOWN

    def _build_reasoning(
        self,
        scale_level: ScaleLevel,
        prompt_lower: str,
        complexity_level: ComplexityLevel
    ) -> str:
        """Build reasoning explanation for assessment.

        Args:
            scale_level: Determined scale level
            prompt_lower: Lowercase prompt
            complexity_level: Mapped complexity level

        Returns:
            Human-readable reasoning
        """
        level_descriptions = {
            ScaleLevel.LEVEL_0_CHORE: "Simple chore or config change",
            ScaleLevel.LEVEL_1_BUG_FIX: "Bug fix or quick change",
            ScaleLevel.LEVEL_2_SMALL_FEATURE: "Small feature with basic planning",
            ScaleLevel.LEVEL_3_MEDIUM_FEATURE: "Complex feature requiring architecture",
            ScaleLevel.LEVEL_4_GREENFIELD: "Greenfield application or platform",
        }

        return (
            f"Assessed as {complexity_level.value} complexity "
            f"(Scale Level {scale_level.value}): "
            f"{level_descriptions[scale_level]}"
        )

    def build_workflow_sequence(
        self,
        assessment: ComplexityAssessment
    ) -> WorkflowSequence:
        """Build workflow sequence based on complexity assessment.

        Args:
            assessment: ComplexityAssessment with scale level in metadata

        Returns:
            WorkflowSequence with scale-appropriate workflows

        Example:
            ```python
            assessment = ComplexityAssessment(
                complexity_level=ComplexityLevel.MEDIUM,
                metadata={"scale_level": 2}
            )

            sequence = methodology.build_workflow_sequence(assessment)
            # Returns: Planning + Implementation + Testing workflows
            ```
        """
        # Extract scale level from metadata
        scale_level_value = assessment.metadata.get("scale_level")

        if scale_level_value is None:
            # Fall back to mapping complexity level to scale
            from .scale_levels import map_complexity_to_scale
            scale_level = map_complexity_to_scale(assessment.complexity_level)
        else:
            scale_level = ScaleLevel(scale_level_value)

        # Select workflows using workflow selector
        workflows = self.workflow_selector.select_workflows(scale_level)

        # Count unique phases
        phases = {w.phase for w in workflows}

        return WorkflowSequence(
            workflows=workflows,
            total_phases=len(phases),
            can_parallelize=False,  # Adaptive Agile is sequential
            metadata={
                "methodology": "adaptive-agile",
                "scale_level": scale_level.value
            }
        )

    def get_recommended_agents(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Recommend agents for a task.

        Args:
            task: Task description or workflow name
            context: Optional context (phase, workflow, scale_level)

        Returns:
            List of recommended agent names

        Example:
            ```python
            # Phase-based
            agents = methodology.get_recommended_agents(
                "any task",
                context={"phase": "planning"}
            )
            # Returns: ["John", "Bob"]

            # Keyword-based
            agents = methodology.get_recommended_agents("implement feature")
            # Returns: ["Bob", "Amelia"]
            ```
        """
        return self.agent_recommender.recommend(task, context)

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate Adaptive Agile configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with errors and warnings

        Example:
            ```python
            result = methodology.validate_config({
                "scale_level": 2,
                "use_all_agents": True
            })
            # Returns: ValidationResult(valid=True)
            ```
        """
        errors = []
        warnings = []

        # Validate scale_level if present
        if "scale_level" in config:
            scale_level = config["scale_level"]
            if not isinstance(scale_level, int):
                errors.append(
                    f"scale_level must be integer, got {type(scale_level).__name__}"
                )
            elif not 0 <= scale_level <= 4:
                errors.append(
                    f"Invalid scale_level: {scale_level}. Must be 0-4."
                )

        # Validate project_type if present
        valid_types = [t.value for t in ProjectType]
        if "project_type" in config:
            project_type = config["project_type"]
            if project_type not in valid_types:
                warnings.append(
                    f"Unknown project_type: '{project_type}'. "
                    f"Valid types: {valid_types}"
                )

        # Validate agents if present
        valid_agents = self.agent_recommender.get_all_agents()
        if "agents" in config:
            agents = config["agents"]
            if not isinstance(agents, list):
                errors.append("agents must be a list")
            else:
                for agent in agents:
                    if agent not in valid_agents:
                        warnings.append(
                            f"Unknown agent: '{agent}'. "
                            f"Valid agents: {valid_agents}"
                        )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
