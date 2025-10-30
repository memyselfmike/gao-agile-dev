"""Brian - Scale-Adaptive Workflow Orchestrator.

This module implements Brian, the Senior Engineering Manager agent who:
- Analyzes project complexity using AI
- Assesses scale level (Level 0-4)
- Selects appropriate workflow sequences based on scale
- Routes based on project type and context
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog
import json

from anthropic import Anthropic

from ..core.workflow_registry import WorkflowRegistry
from ..core.legacy_models import WorkflowInfo


logger = structlog.get_logger()


class ScaleLevel(Enum):
    """Scale levels for project complexity (BMAD scale-adaptive approach)."""

    LEVEL_0 = 0  # Single atomic change (1 story)
    LEVEL_1 = 1  # Small feature (2-10 stories, 1 epic)
    LEVEL_2 = 2  # Medium project (5-15 stories, 1-2 epics)
    LEVEL_3 = 3  # Large project (12-40 stories, 2-5 epics)
    LEVEL_4 = 4  # Enterprise system (40+ stories, 5+ epics)


class ProjectType(Enum):
    """Project type classification."""

    GREENFIELD = "greenfield"  # New project from scratch
    BROWNFIELD = "brownfield"  # Enhancing existing codebase
    GAME = "game"  # Game development project
    SOFTWARE = "software"  # Standard software project
    BUG_FIX = "bug_fix"  # Bug fix only
    ENHANCEMENT = "enhancement"  # Feature enhancement


@dataclass
class PromptAnalysis:
    """Analysis results from initial prompt assessment."""

    scale_level: ScaleLevel
    project_type: ProjectType
    is_greenfield: bool
    is_brownfield: bool
    is_game_project: bool
    estimated_stories: int
    estimated_epics: int
    technical_complexity: str  # low, medium, high
    domain_complexity: str  # low, medium, high
    timeline_hint: Optional[str]  # hours, days, weeks, months
    confidence: float  # 0.0-1.0
    reasoning: str
    needs_clarification: bool = False
    clarifying_questions: List[str] = field(default_factory=list)


@dataclass
class WorkflowSequence:
    """Sequence of workflows to execute for a project."""

    scale_level: ScaleLevel
    workflows: List[WorkflowInfo]
    project_type: ProjectType
    routing_rationale: str
    phase_breakdown: Dict[str, List[str]]  # Phase name -> workflow names
    jit_tech_specs: bool = False  # Just-in-time tech specs (Level 3-4)


class BrianOrchestrator:
    """
    Brian - Senior Engineering Manager and Workflow Orchestrator.

    Implements scale-adaptive workflow selection based on BMAD Method principles.
    Analyzes prompts, assesses complexity, and builds appropriate workflow sequences.
    """

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        api_key: Optional[str] = None,
        brian_persona_path: Optional[Path] = None
    ):
        """
        Initialize Brian Orchestrator.

        Args:
            workflow_registry: Registry of available workflows
            api_key: Anthropic API key (uses env var if not provided)
            brian_persona_path: Path to Brian's agent definition
        """
        self.workflow_registry = workflow_registry
        self.anthropic = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.brian_persona_path = brian_persona_path
        self.logger = logger.bind(component="brian_orchestrator", agent="Brian")

    async def assess_and_select_workflows(
        self,
        initial_prompt: str,
        force_scale_level: Optional[ScaleLevel] = None
    ) -> WorkflowSequence:
        """
        Assess prompt complexity and select appropriate workflow sequence.

        This is Brian's main decision-making method. He analyzes the prompt using
        his 20 years of experience (via AI) and selects the optimal workflow path.

        Args:
            initial_prompt: User's initial request
            force_scale_level: Optional override for scale level

        Returns:
            WorkflowSequence with selected workflows and routing rationale
        """
        self.logger.info(
            "brian_analyzing_prompt",
            prompt_preview=initial_prompt[:100]
        )

        # Phase 1: Analyze the prompt
        analysis = await self._analyze_prompt(initial_prompt)

        # Override scale level if forced (for testing/debugging)
        if force_scale_level:
            analysis.scale_level = force_scale_level

        self.logger.info(
            "brian_assessment_complete",
            scale_level=analysis.scale_level.value,
            project_type=analysis.project_type.value,
            estimated_stories=analysis.estimated_stories,
            confidence=analysis.confidence
        )

        # If clarification needed, return early with questions
        if analysis.needs_clarification:
            self.logger.info(
                "brian_needs_clarification",
                questions=analysis.clarifying_questions
            )
            # Return empty sequence with clarification questions
            return WorkflowSequence(
                scale_level=analysis.scale_level,
                workflows=[],
                project_type=analysis.project_type,
                routing_rationale=f"Clarification needed: {analysis.reasoning}",
                phase_breakdown={},
                jit_tech_specs=False
            )

        # Phase 2: Build workflow sequence based on scale
        workflow_sequence = self._build_workflow_sequence(analysis)

        self.logger.info(
            "brian_workflow_sequence_built",
            scale_level=analysis.scale_level.value,
            total_workflows=len(workflow_sequence.workflows),
            phases=list(workflow_sequence.phase_breakdown.keys())
        )

        return workflow_sequence

    async def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """
        Use AI with Brian's persona to analyze the prompt.

        Brian applies his 20 years of experience to assess:
        - Scale level (0-4)
        - Project type
        - Technical and domain complexity
        - Timeline hints

        Args:
            prompt: User's initial request

        Returns:
            PromptAnalysis with scale assessment
        """
        # Load Brian's persona if available
        brian_context = ""
        if self.brian_persona_path and self.brian_persona_path.exists():
            brian_context = self.brian_persona_path.read_text(encoding="utf-8")

        # Create analysis prompt for Claude
        analysis_prompt = f"""You are Brian Thompson, a Senior Engineering Manager with 20 years of battle-tested experience analyzing software projects.

{brian_context[:500] if brian_context else ""}

Analyze this software development request and assess its scale level using the BMAD scale-adaptive approach:

User Request:
{prompt}

Scale Levels (BMAD Method):
- Level 0: Single atomic change (1 story) - bug fix, small tweak
- Level 1: Small feature (2-10 stories, 1 epic) - single focused feature
- Level 2: Medium project (5-15 stories, 1-2 epics) - feature set, small app
- Level 3: Large project (12-40 stories, 2-5 epics) - complex app, system
- Level 4: Enterprise system (40+ stories, 5+ epics) - enterprise platform

Assess the following:
1. Scale Level (0-4): Based on estimated story count
2. Project Type: greenfield, brownfield, game, software, bug_fix, enhancement
3. Is Greenfield: Building from scratch?
4. Is Brownfield: Enhancing existing code?
5. Is Game Project: Game development?
6. Estimated Stories: How many stories would this take?
7. Estimated Epics: How many epics?
8. Technical Complexity: low, medium, high
9. Domain Complexity: low, medium, high
10. Timeline Hint: hours, days, weeks, months (or null)
11. Confidence: 0.0-1.0 (how confident are you?)
12. Reasoning: Your expert assessment (1-2 sentences)
13. Needs Clarification: true/false - Is the scope too ambiguous?
14. Clarifying Questions: If ambiguous, what should we ask? (list)

Return ONLY a JSON object with these exact keys:
{{
    "scale_level": 0-4,
    "project_type": "greenfield|brownfield|game|software|bug_fix|enhancement",
    "is_greenfield": true|false,
    "is_brownfield": true|false,
    "is_game_project": true|false,
    "estimated_stories": number,
    "estimated_epics": number,
    "technical_complexity": "low|medium|high",
    "domain_complexity": "low|medium|high",
    "timeline_hint": "hours|days|weeks|months" or null,
    "confidence": 0.85,
    "reasoning": "Your expert assessment...",
    "needs_clarification": true|false,
    "clarifying_questions": ["Question 1?", "Question 2?"]
}}

Use your seasoned judgment to right-size the project accurately.
"""

        # Call Claude for analysis
        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            # Extract JSON from response
            response_text = response.content[0].text

            # Try to parse JSON (handle cases where Claude adds explanation)
            try:
                # Try direct JSON parse first
                analysis_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Look for JSON in code blocks
                if "```json" in response_text:
                    json_start = response_text.index("```json") + 7
                    json_end = response_text.index("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                    analysis_data = json.loads(json_str)
                elif "{" in response_text:
                    # Extract JSON object from text
                    json_start = response_text.index("{")
                    json_end = response_text.rindex("}") + 1
                    json_str = response_text[json_start:json_end]
                    analysis_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")

            # Convert to PromptAnalysis
            return PromptAnalysis(
                scale_level=ScaleLevel(analysis_data["scale_level"]),
                project_type=ProjectType(analysis_data["project_type"]),
                is_greenfield=analysis_data["is_greenfield"],
                is_brownfield=analysis_data["is_brownfield"],
                is_game_project=analysis_data["is_game_project"],
                estimated_stories=analysis_data["estimated_stories"],
                estimated_epics=analysis_data["estimated_epics"],
                technical_complexity=analysis_data["technical_complexity"],
                domain_complexity=analysis_data["domain_complexity"],
                timeline_hint=analysis_data.get("timeline_hint"),
                confidence=analysis_data["confidence"],
                reasoning=analysis_data["reasoning"],
                needs_clarification=analysis_data.get("needs_clarification", False),
                clarifying_questions=analysis_data.get("clarifying_questions", [])
            )

        except Exception as e:
            self.logger.error("brian_analysis_failed", error=str(e))
            # Fallback to conservative default
            return PromptAnalysis(
                scale_level=ScaleLevel.LEVEL_2,
                project_type=ProjectType.SOFTWARE,
                is_greenfield=True,
                is_brownfield=False,
                is_game_project=False,
                estimated_stories=10,
                estimated_epics=2,
                technical_complexity="medium",
                domain_complexity="medium",
                timeline_hint=None,
                confidence=0.5,
                reasoning=f"Analysis failed, using conservative default. Error: {str(e)}",
                needs_clarification=True,
                clarifying_questions=[
                    "What is the approximate scope? (small feature, medium project, large system)",
                    "Is this a new project or enhancing existing code?",
                    "What is the estimated timeline?"
                ]
            )

    def _build_workflow_sequence(self, analysis: PromptAnalysis) -> WorkflowSequence:
        """
        Build workflow sequence based on scale-adaptive routing.

        This implements BMAD Method's scale-adaptive principles:
        - Level 0-1: tech-spec → story → implementation
        - Level 2: PRD → tech-spec → implementation
        - Level 3-4: PRD → architecture → JIT tech-specs → implementation

        Args:
            analysis: Prompt analysis results

        Returns:
            WorkflowSequence with ordered workflows
        """
        workflows: List[WorkflowInfo] = []
        phase_breakdown: Dict[str, List[str]] = {}
        jit_tech_specs = False

        # Special routing for brownfield projects
        if analysis.is_brownfield:
            # Brownfield ALWAYS starts with document-project
            doc_workflow = self.workflow_registry.get_workflow("document-project")
            if doc_workflow:
                workflows.append(doc_workflow)
                phase_breakdown["Phase 1: Analysis"] = ["document-project"]

        # Special routing for game projects
        if analysis.is_game_project:
            return self._build_game_workflow_sequence(analysis)

        # Scale-adaptive routing for software projects
        if analysis.scale_level == ScaleLevel.LEVEL_0:
            # Level 0: Single atomic change
            # tech-spec → create-story → dev-story → story-done
            workflows.extend(self._get_workflows_by_names([
                "tech-spec",
                "create-story",
                "dev-story",
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = "Level 0 (atomic change): Fast path with tech-spec → single story → implementation"

        elif analysis.scale_level == ScaleLevel.LEVEL_1:
            # Level 1: Small feature (2-10 stories)
            # tech-spec → multiple stories
            workflows.extend(self._get_workflows_by_names([
                "tech-spec",
                "create-story",  # Will be called multiple times
                "dev-story",     # Will be called per story
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = f"Level 1 (small feature): Tech-spec → {analysis.estimated_stories} stories → implementation"

        elif analysis.scale_level == ScaleLevel.LEVEL_2:
            # Level 2: Medium project (5-15 stories, 1-2 epics)
            # PRD → epics → tech-spec → implementation
            workflows.extend(self._get_workflows_by_names([
                "prd",
                "tech-spec",
                "create-story",
                "dev-story",
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["prd", "tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = f"Level 2 (medium project): PRD → epics → tech-spec → {analysis.estimated_epics} epics, {analysis.estimated_stories} stories"

        else:  # Level 3-4: Large/Enterprise
            # Level 3-4: Large project or enterprise
            # PRD → epics → architecture → JIT tech-specs (per epic) → implementation
            workflows.extend(self._get_workflows_by_names([
                "prd",
                "architecture",
                "tech-spec",     # JIT per epic
                "create-story",
                "dev-story",
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["prd"]
            phase_breakdown["Phase 3: Solutioning"] = ["architecture"]
            phase_breakdown["Phase 4: Implementation"] = ["tech-spec (JIT per epic)", "create-story", "dev-story", "story-done"]
            jit_tech_specs = True
            routing_rationale = f"Level {analysis.scale_level.value} ({'large' if analysis.scale_level == ScaleLevel.LEVEL_3 else 'enterprise'}): PRD → architecture → JIT tech-specs (per epic) → {analysis.estimated_epics} epics, {analysis.estimated_stories} stories"

        return WorkflowSequence(
            scale_level=analysis.scale_level,
            workflows=[w for w in workflows if w is not None],  # Filter out missing workflows
            project_type=analysis.project_type,
            routing_rationale=routing_rationale,
            phase_breakdown=phase_breakdown,
            jit_tech_specs=jit_tech_specs
        )

    def _build_game_workflow_sequence(self, analysis: PromptAnalysis) -> WorkflowSequence:
        """
        Build workflow sequence for game projects.

        Game projects follow different workflow:
        - game-brief (optional) → gdd → solutioning (if complex) → implementation

        Args:
            analysis: Prompt analysis results

        Returns:
            WorkflowSequence for game project
        """
        workflows: List[WorkflowInfo] = []
        phase_breakdown: Dict[str, List[str]] = {}

        # Game workflow
        game_workflows = ["game-brief", "gdd"]

        # Add solutioning if complex (Level 3-4)
        if analysis.scale_level.value >= 3:
            game_workflows.append("architecture")

        game_workflows.extend(["create-story", "dev-story", "story-done"])

        workflows = self._get_workflows_by_names(game_workflows)

        phase_breakdown["Phase 1: Analysis"] = ["game-brief"]
        phase_breakdown["Phase 2: Planning"] = ["gdd"]
        if analysis.scale_level.value >= 3:
            phase_breakdown["Phase 3: Solutioning"] = ["architecture"]
        phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]

        routing_rationale = f"Game Project (Level {analysis.scale_level.value}): game-brief → gdd → {'architecture → ' if analysis.scale_level.value >= 3 else ''}implementation"

        return WorkflowSequence(
            scale_level=analysis.scale_level,
            workflows=[w for w in workflows if w is not None],
            project_type=ProjectType.GAME,
            routing_rationale=routing_rationale,
            phase_breakdown=phase_breakdown,
            jit_tech_specs=False
        )

    def _get_workflows_by_names(self, workflow_names: List[str]) -> List[Optional[WorkflowInfo]]:
        """
        Get workflows by name from registry.

        Args:
            workflow_names: List of workflow names to retrieve

        Returns:
            List of WorkflowInfo objects (None if not found)
        """
        workflows = []
        for name in workflow_names:
            workflow = self.workflow_registry.get_workflow(name)
            if workflow:
                workflows.append(workflow)
            else:
                self.logger.warning("workflow_not_found", workflow_name=name)
                workflows.append(None)
        return workflows

    def get_scale_level_description(self, scale_level: ScaleLevel) -> str:
        """
        Get human-readable description of scale level.

        Args:
            scale_level: Scale level to describe

        Returns:
            Description string
        """
        descriptions = {
            ScaleLevel.LEVEL_0: "Single atomic change (1 story) - quick fix or small tweak",
            ScaleLevel.LEVEL_1: "Small feature (2-10 stories, 1 epic) - focused feature addition",
            ScaleLevel.LEVEL_2: "Medium project (5-15 stories, 1-2 epics) - feature set or small application",
            ScaleLevel.LEVEL_3: "Large project (12-40 stories, 2-5 epics) - complex application or system",
            ScaleLevel.LEVEL_4: "Enterprise system (40+ stories, 5+ epics) - enterprise platform or large system"
        }
        return descriptions.get(scale_level, "Unknown scale level")
