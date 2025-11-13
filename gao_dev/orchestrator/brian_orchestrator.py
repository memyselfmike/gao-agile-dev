"""Brian - Scale-Adaptive Workflow Orchestrator.

This module implements Brian, the Senior Engineering Manager agent who:
- Analyzes project complexity using AI
- Assesses scale level (Level 0-4)
- Selects appropriate workflow sequences based on scale
- Routes based on project type and context

Story 5.4: Updated to use shared models from models.py.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import structlog
import json
import hashlib
import time
from datetime import datetime, timedelta

from ..core.workflow_registry import WorkflowRegistry
from ..core.models.workflow import WorkflowInfo
from ..core.prompt_loader import PromptLoader
from ..core.config_loader import ConfigLoader
from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.services.learning_application_service import LearningApplicationService
from ..core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError,
)
from ..lifecycle.exceptions import WorkflowDependencyCycleError
from ..methodologies.adaptive_agile.workflow_adjuster import WorkflowAdjuster
from .models import (
    ScaleLevel,
    ProjectType,
    PromptAnalysis,
    WorkflowSequence
)


logger = structlog.get_logger()


class BrianOrchestrator:
    """
    Brian - Senior Engineering Manager and Workflow Orchestrator.

    Implements scale-adaptive workflow selection based on BMAD Method principles.
    Analyzes prompts, assesses complexity, and builds appropriate workflow sequences.
    """

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        analysis_service: AIAnalysisService,
        brian_persona_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
        model: Optional[str] = None,
        learning_service: Optional[LearningApplicationService] = None,
        workflow_adjuster: Optional[WorkflowAdjuster] = None
    ):
        """
        Initialize Brian Orchestrator.

        Args:
            workflow_registry: Registry of available workflows
            analysis_service: AI analysis service for prompt analysis
            brian_persona_path: Path to Brian's agent definition
            project_root: Project root for PromptLoader (defaults to gao_dev parent)
            model: Model to use for analysis (defaults to deepseek-r1 from YAML or env)
            learning_service: Optional LearningApplicationService for context enrichment
            workflow_adjuster: Optional WorkflowAdjuster for adjusting workflows based on learnings
        """
        self.workflow_registry = workflow_registry
        self.analysis_service = analysis_service
        self.brian_persona_path = brian_persona_path
        self.learning_service = learning_service
        self.workflow_adjuster = workflow_adjuster
        self.logger = logger.bind(component="brian_orchestrator", agent="Brian")

        # Initialize PromptLoader
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root

        # Setup config and prompt loaders
        self.config_loader = ConfigLoader(project_root)
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt_loader = PromptLoader(
            prompts_dir=prompts_dir,
            config_loader=self.config_loader
        )

        # Learning context cache (TTL: 1 hour)
        self._learning_cache: Dict[str, tuple[str, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)

        # Load model from YAML config if not provided
        import os
        if model is None:
            # Try environment variable first
            model = os.getenv("GAO_DEV_MODEL")
            if model is None:
                # Try to load from Brian's YAML config
                try:
                    from ..core.agent_config_loader import AgentConfigLoader
                    agents_dir = Path(__file__).parent.parent / "agents"
                    agent_loader = AgentConfigLoader(agents_dir)
                    brian_config = agent_loader.load_agent_config("brian")
                    model = brian_config.model if brian_config else "deepseek-r1"
                except Exception:
                    model = "deepseek-r1"  # Default to deepseek-r1

        self.model = model
        self.logger.info("brian_model_configured", model=self.model)

    def assess_vagueness(self, user_request: str) -> float:
        """
        Assess vagueness of user request using simple heuristics.

        This is a lightweight check to determine if Mary should be consulted
        for vision elicitation before Brian selects workflows.

        Args:
            user_request: User's initial request

        Returns:
            Vagueness score (0.0 = very specific, 1.0 = very vague)
        """
        request_lower = user_request.lower().strip()
        length = len(request_lower.split())

        # Very short requests are often vague
        if length < 5:
            return 0.9

        # Check for vague words
        vague_words = [
            "something", "anything", "stuff", "thing", "idea",
            "maybe", "kinda", "sorta", "probably", "possibly"
        ]
        vague_count = sum(1 for word in vague_words if word in request_lower)

        # Check for lack of specifics
        specific_indicators = [
            "user", "feature", "button", "page", "api", "database",
            "authentication", "dashboard", "report", "form"
        ]
        specific_count = sum(1 for word in specific_indicators if word in request_lower)

        # Calculate score
        vagueness = 0.5  # baseline

        if vague_count > 0:
            vagueness += 0.2 * min(vague_count, 2)

        if specific_count == 0:
            vagueness += 0.2

        if length < 10:
            vagueness += 0.1

        return min(1.0, vagueness)

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
                jit_tech_specs=False,
                estimated_stories=analysis.estimated_stories,
                estimated_epics=analysis.estimated_epics
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

    async def select_workflows_with_learning(
        self,
        user_prompt: str,
        force_scale_level: Optional[ScaleLevel] = None,
        epic_num: Optional[int] = None
    ) -> WorkflowSequence:
        """
        Select workflows with learning-enriched context (Epic 29 integration).

        This method extends the standard workflow selection by:
        1. Analyzing complexity (existing)
        2. Building enriched context with learnings (Story 29.3)
        3. Selecting base workflows (existing)
        4. Adjusting workflows based on learnings (Story 29.4 - NEW)

        Args:
            user_prompt: User's initial request
            force_scale_level: Optional override for scale level
            epic_num: Optional epic number for tracking adjustments

        Returns:
            WorkflowSequence with selected and adjusted workflows
        """
        self.logger.info(
            "select_workflows_with_learning_started",
            prompt_preview=user_prompt[:100]
        )

        # Phase 1: Analyze the prompt (existing)
        analysis = await self._analyze_prompt(user_prompt)

        # Override scale level if forced (for testing/debugging)
        if force_scale_level:
            analysis.scale_level = force_scale_level

        # Phase 2: Build enriched context with learnings (Story 29.3)
        learning_context = self._build_context_with_learnings(
            scale_level=analysis.scale_level,
            project_type=analysis.project_type.value,
            user_prompt=user_prompt
        )

        # Get relevant learnings for workflow adjustment
        learnings = []
        if self.learning_service:
            context = self._extract_context_from_prompt(user_prompt)
            learnings = self.learning_service.get_relevant_learnings(
                scale_level=analysis.scale_level,
                project_type=analysis.project_type.value,
                context=context,
                limit=5
            )

        # Log learning context status
        if learning_context:
            self.logger.info(
                "learning_context_added",
                context_length=len(learning_context),
                learnings_count=len(learnings),
                scale_level=analysis.scale_level.value
            )
        else:
            self.logger.info(
                "no_learning_context_added",
                scale_level=analysis.scale_level.value
            )

        # Phase 3: Build base workflow sequence (existing logic)
        workflow_sequence = self._build_workflow_sequence(analysis)

        # Phase 4: Adjust workflows based on learnings (Story 29.4 - NEW)
        if learnings and self.workflow_adjuster:
            try:
                from ..methodologies.adaptive_agile.workflow_adjuster import WorkflowStep

                # Convert WorkflowInfo to WorkflowStep for adjustment
                workflow_steps = [
                    WorkflowStep(
                        workflow_name=wf.name,
                        phase=self._get_phase_name(wf.phase),
                        depends_on=[],  # Dependencies not tracked in WorkflowInfo
                        metadata=wf.metadata
                    )
                    for wf in workflow_sequence.workflows
                ]

                # Adjust workflows
                adjusted_steps = self.workflow_adjuster.adjust_workflows(
                    workflows=workflow_steps,
                    learnings=learnings,
                    scale_level=analysis.scale_level,
                    epic_num=epic_num
                )

                # Log adjustments
                if len(adjusted_steps) > len(workflow_steps):
                    self.logger.info(
                        "workflows_adjusted",
                        original_count=len(workflow_steps),
                        adjusted_count=len(adjusted_steps),
                        workflows_added=len(adjusted_steps) - len(workflow_steps)
                    )

            except WorkflowDependencyCycleError as e:
                self.logger.error(
                    "workflow_adjustment_cycle_detected",
                    error=str(e),
                    cycles=getattr(e, "cycles", [])
                )
                # Fallback to original workflows on cycle detection
            except Exception as e:
                self.logger.error(
                    "workflow_adjustment_failed",
                    error=str(e),
                    exc_info=True
                )
                # Fallback to original workflows on any error

        self.logger.info(
            "select_workflows_with_learning_completed",
            scale_level=analysis.scale_level.value,
            total_workflows=len(workflow_sequence.workflows),
            learning_context_length=len(learning_context)
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

        Raises:
            AnalysisError: If analysis fails
        """
        # Load Brian's persona if available
        brian_context = ""
        if self.brian_persona_path and self.brian_persona_path.exists():
            brian_context = self.brian_persona_path.read_text(encoding="utf-8")

        # Load and render prompt template
        try:
            template = self.prompt_loader.load_prompt("agents/brian_analysis")

            # Render the prompt with variables
            analysis_prompt = self.prompt_loader.render_prompt(
                template,
                variables={
                    "user_request": prompt,
                    "brian_persona": brian_context[:500] if brian_context else "",
                }
            )
        except Exception as e:
            self.logger.error("failed_to_load_prompt_template", error=str(e))
            # Fallback to inline prompt if template loading fails
            analysis_prompt = self._get_fallback_prompt(prompt, brian_context)

        # Call analysis service
        try:
            self.logger.info("brian_calling_analysis_service", model=self.model)

            # Call analysis service (NOT Anthropic directly)
            result = await self.analysis_service.analyze(
                prompt=analysis_prompt,
                model=self.model,
                response_format="json",
                max_tokens=2048
            )

            # Extract JSON from response
            response_text = result.response

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

            self.logger.info(
                "brian_analysis_complete",
                scale_level=analysis_data.get("scale_level"),
                model=result.model_used,
                tokens=result.tokens_used,
                duration_ms=result.duration_ms
            )

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

        except (AnalysisError, AnalysisTimeoutError, InvalidModelError) as e:
            self.logger.error(
                "brian_analysis_failed",
                error=str(e),
                error_type=type(e).__name__,
                model=self.model
            )
            # Fallback to conservative default
            # Proceed with sensible defaults instead of blocking on clarification
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
                reasoning=f"Analysis failed, using conservative default (Level 2: small feature, ~10 stories). Error: {str(e)}",
                needs_clarification=False,  # Don't block on clarification when analysis fails
                clarifying_questions=[]
            )
        except json.JSONDecodeError as e:
            self.logger.error(
                "brian_response_parse_failed",
                error=str(e),
                response=response_text[:200] if 'response_text' in locals() else "N/A"
            )
            raise AnalysisError(f"Failed to parse analysis response: {e}") from e
        except Exception as e:
            self.logger.error(
                "brian_analysis_unexpected_error",
                error=str(e),
                error_type=type(e).__name__,
                model=self.model
            )
            # Fallback to conservative default for unexpected errors
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
        - Level 0-1: tech-spec -> story -> implementation
        - Level 2: PRD -> tech-spec -> implementation
        - Level 3-4: PRD -> architecture -> JIT tech-specs -> implementation

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
            # tech-spec -> create-story -> dev-story -> story-done
            workflows.extend(self._get_workflows_by_names([
                "tech-spec",
                "create-story",
                "dev-story",
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = "Level 0 (atomic change): Fast path with tech-spec -> single story -> implementation"

        elif analysis.scale_level == ScaleLevel.LEVEL_1:
            # Level 1: Small feature (2-10 stories)
            # tech-spec -> multiple stories
            workflows.extend(self._get_workflows_by_names([
                "tech-spec",
                "create-story",  # Will be called multiple times
                "dev-story",     # Will be called per story
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = f"Level 1 (small feature): Tech-spec -> {analysis.estimated_stories} stories -> implementation"

        elif analysis.scale_level == ScaleLevel.LEVEL_2:
            # Level 2: Medium project (5-15 stories, 1-2 epics)
            # PRD -> epics -> tech-spec -> implementation
            workflows.extend(self._get_workflows_by_names([
                "prd",
                "tech-spec",
                "create-story",
                "dev-story",
                "story-done"
            ]))
            phase_breakdown["Phase 2: Planning"] = ["prd", "tech-spec"]
            phase_breakdown["Phase 4: Implementation"] = ["create-story", "dev-story", "story-done"]
            routing_rationale = f"Level 2 (medium project): PRD -> epics -> tech-spec -> {analysis.estimated_epics} epics, {analysis.estimated_stories} stories"

        else:  # Level 3-4: Large/Enterprise
            # Level 3-4: Large project or enterprise
            # PRD -> epics -> architecture -> JIT tech-specs (per epic) -> implementation
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
            routing_rationale = f"Level {analysis.scale_level.value} ({'large' if analysis.scale_level == ScaleLevel.LEVEL_3 else 'enterprise'}): PRD -> architecture -> JIT tech-specs (per epic) -> {analysis.estimated_epics} epics, {analysis.estimated_stories} stories"

        return WorkflowSequence(
            scale_level=analysis.scale_level,
            workflows=[w for w in workflows if w is not None],  # Filter out missing workflows
            project_type=analysis.project_type,
            routing_rationale=routing_rationale,
            phase_breakdown=phase_breakdown,
            jit_tech_specs=jit_tech_specs,
            estimated_stories=analysis.estimated_stories,
            estimated_epics=analysis.estimated_epics
        )

    def _build_game_workflow_sequence(self, analysis: PromptAnalysis) -> WorkflowSequence:
        """
        Build workflow sequence for game projects.

        Game projects follow different workflow:
        - game-brief (optional) -> gdd -> solutioning (if complex) -> implementation

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

        routing_rationale = f"Game Project (Level {analysis.scale_level.value}): game-brief -> gdd -> {'architecture -> ' if analysis.scale_level.value >= 3 else ''}implementation"

        return WorkflowSequence(
            scale_level=analysis.scale_level,
            workflows=[w for w in workflows if w is not None],
            project_type=ProjectType.GAME,
            routing_rationale=routing_rationale,
            phase_breakdown=phase_breakdown,
            jit_tech_specs=False,
            estimated_stories=analysis.estimated_stories,
            estimated_epics=analysis.estimated_epics
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

    def _get_phase_name(self, phase: int) -> str:
        """
        Convert phase number to phase name.

        Args:
            phase: Phase number (0-4)

        Returns:
            Phase name string
        """
        phase_names = {
            0: "analysis",
            1: "planning",
            2: "planning",
            3: "solutioning",
            4: "implementation",
            5: "ceremonies"
        }
        return phase_names.get(phase, "implementation")

    def _extract_context_from_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Extract context clues from user prompt using keyword matching.

        This method identifies relevant tags, requirements, technologies, and project phase
        from the user's prompt to help find relevant learnings.

        Args:
            user_prompt: Original user request

        Returns:
            Dict with keys: tags, requirements, technologies, phase
        """
        context: Dict[str, Any] = {
            "tags": [],
            "requirements": [],
            "technologies": [],
            "phase": "unknown"
        }

        prompt_lower = user_prompt.lower()

        # Extract feature tags
        feature_keywords = [
            "authentication", "auth", "login", "api", "rest", "graphql",
            "database", "db", "storage", "cache", "search", "testing",
            "ui", "frontend", "backend", "admin", "user", "payment",
            "notification", "email", "messaging", "analytics", "reporting"
        ]
        context["tags"] = [kw for kw in feature_keywords if kw in prompt_lower]

        # Extract requirements
        requirement_keywords = {
            "security": ["security", "secure", "auth", "encryption", "ssl", "tls"],
            "performance": ["performance", "fast", "optimize", "cache", "speed"],
            "scalability": ["scalability", "scale", "distributed", "cluster", "load"]
        }
        for req, keywords in requirement_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                context["requirements"].append(req)

        # Extract technologies
        tech_keywords = [
            "python", "javascript", "typescript", "react", "vue", "angular",
            "django", "flask", "fastapi", "postgres", "mysql", "mongodb",
            "redis", "elasticsearch", "jwt", "oauth", "docker", "kubernetes"
        ]
        context["technologies"] = [tech for tech in tech_keywords if tech in prompt_lower]

        # Detect phase
        if any(word in prompt_lower for word in ["build", "create", "new", "from scratch"]):
            context["phase"] = "greenfield"
        elif any(word in prompt_lower for word in ["add", "enhance", "extend", "improve"]):
            context["phase"] = "enhancement"
        elif any(word in prompt_lower for word in ["fix", "bug", "issue", "error"]):
            context["phase"] = "bugfix"

        self.logger.debug(
            "context_extracted_from_prompt",
            tags=context["tags"],
            requirements=context["requirements"],
            technologies=context["technologies"],
            phase=context["phase"]
        )

        return context

    def _build_context_with_learnings(
        self,
        scale_level: ScaleLevel,
        project_type: str,
        user_prompt: str
    ) -> str:
        """
        Build Brian's analysis context enriched with relevant past learnings.

        This method:
        1. Extracts context from user prompt
        2. Checks cache for existing learning context
        3. Queries LearningApplicationService for relevant learnings
        4. Renders learning context using Mustache template
        5. Caches result for future use
        6. Returns enriched context

        Args:
            scale_level: Detected scale level
            project_type: Project type (greenfield, enhancement, bugfix, etc.)
            user_prompt: Original user request

        Returns:
            Enriched context string for Brian's analysis (empty string if no learnings or error)
        """
        # Early return if no learning service configured
        if not self.learning_service:
            self.logger.debug("no_learning_service_configured")
            return ""

        start_time = time.time()

        try:
            # Extract context from prompt
            context = self._extract_context_from_prompt(user_prompt)

            # Build cache key
            context_hash = hashlib.md5(
                json.dumps(context, sort_keys=True).encode()
            ).hexdigest()[:8]
            cache_key = f"learning_context_{scale_level.value}_{project_type}_{context_hash}"

            # Check cache
            if cache_key in self._learning_cache:
                cached_context, cached_at = self._learning_cache[cache_key]
                if datetime.now() - cached_at < self._cache_ttl:
                    elapsed_ms = (time.time() - start_time) * 1000
                    self.logger.info(
                        "learning_context_cache_hit",
                        cache_key=cache_key,
                        elapsed_ms=round(elapsed_ms, 2)
                    )
                    return cached_context

            # Query for relevant learnings
            learnings = self.learning_service.get_relevant_learnings(
                scale_level=scale_level,
                project_type=project_type,
                context=context,
                limit=5
            )

            # If no learnings found, return empty (graceful degradation)
            if not learnings:
                self.logger.info("no_relevant_learnings_found", scale_level=scale_level.value)
                return ""

            # Format learnings for template
            formatted_learnings = []
            for idx, learning in enumerate(learnings, start=1):
                formatted_learnings.append({
                    "rank": idx,
                    "category": learning.category.title(),
                    "confidence": f"{learning.confidence_score:.2f}",
                    "success_rate": f"{learning.success_rate:.2f}",
                    "success_rate_percent": f"{learning.success_rate * 100:.0f}",
                    "content": learning.learning,
                    "context": learning.metadata.get("context", "General application"),
                    "application_count": learning.application_count,
                    "recommendation": learning.metadata.get(
                        "recommendation",
                        "Consider applying this learning to current context"
                    )
                })

            # Render template using prompt loader (Mustache template)
            try:
                template = self.prompt_loader.load_prompt("agents/brian_context_with_learnings")
                learning_context = self.prompt_loader.render_prompt(
                    template,
                    variables={
                        "learnings": formatted_learnings,
                        "has_learnings": len(formatted_learnings) > 0
                    }
                )
            except Exception as e:
                self.logger.warning(
                    "failed_to_load_learning_template",
                    error=str(e),
                    exc_info=True
                )
                # Fallback to simple formatting
                learning_context = self._format_learnings_fallback(formatted_learnings)

            # Cache the result
            self._learning_cache[cache_key] = (learning_context, datetime.now())

            # Log performance
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.info(
                "learning_context_built",
                learnings_count=len(learnings),
                elapsed_ms=round(elapsed_ms, 2),
                cache_key=cache_key,
                scale_level=scale_level.value,
                project_type=project_type
            )

            return learning_context

        except Exception as e:
            # Graceful fallback on any error
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.warning(
                "failed_to_build_learning_context",
                error=str(e),
                elapsed_ms=round(elapsed_ms, 2),
                exc_info=True
            )
            return ""

    def _format_learnings_fallback(self, formatted_learnings: List[Dict[str, Any]]) -> str:
        """
        Fallback formatting for learnings when template loading fails.

        Args:
            formatted_learnings: List of formatted learning dicts

        Returns:
            Simple text-formatted learning context
        """
        if not formatted_learnings:
            return ""

        lines = ["## Relevant Past Learnings\n"]
        lines.append("Based on analysis of past projects, here are key learnings:\n")

        for learning in formatted_learnings:
            lines.append(
                f"\n### Learning {learning['rank']}: {learning['category']} "
                f"(Confidence: {learning['confidence']}, Success Rate: {learning['success_rate']})\n"
            )
            lines.append(f"**Content**: {learning['content']}\n")
            lines.append(f"**Context**: {learning['context']}\n")
            lines.append(
                f"**Applications**: Applied {learning['application_count']} times "
                f"with {learning['success_rate_percent']}% success\n"
            )
            lines.append(f"**Recommendation**: {learning['recommendation']}\n")
            lines.append("---\n")

        lines.append("\nPlease consider these learnings when selecting workflows.\n")

        return "".join(lines)

    def _get_fallback_prompt(self, prompt: str, brian_context: str) -> str:
        """
        Get fallback prompt if template loading fails.

        Args:
            prompt: User request
            brian_context: Brian's persona context

        Returns:
            Fallback analysis prompt
        """
        return f"""You are Brian Thompson, a Senior Engineering Manager with 20 years of battle-tested experience analyzing software projects.

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
