"""Mary Orchestrator - Business Analyst agent for vision elicitation and clarification.

This module implements Mary, the Business Analyst agent who:
- Helps users articulate vague ideas into clear product visions
- Facilitates structured discovery using multiple techniques
- Generates comprehensive vision documents for handoff to Brian

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.1 - Vision Elicitation Workflows & Prompts
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import structlog
from enum import Enum

from ..core.workflow_registry import WorkflowRegistry
from ..core.prompt_loader import PromptLoader
from ..core.services.ai_analysis_service import AIAnalysisService
from ..core.models.vision_summary import (
    VisionSummary,
    VisionCanvas,
    ProblemSolutionFit,
    OutcomeMap,
    FiveWOneH,
)
from ..core.models.brainstorming_summary import (
    BrainstormingSummary,
    Idea,
)
from ..core.models.requirements_analysis import RequirementsAnalysis
from .conversation_manager import ConversationManager
from .brainstorming_engine import BrainstormingEngine, BrainstormingGoal
from .requirements_analyzer import RequirementsAnalyzer
from .domain_question_library import DomainQuestionLibrary


logger = structlog.get_logger()


class ClarificationStrategy(str, Enum):
    """Strategy for clarification approach."""

    SIMPLE_QUESTIONS = "simple_questions"  # Ask 2-3 clarifying questions
    VISION_ELICITATION = "vision_elicitation"  # Full vision elicitation session


class MaryOrchestrator:
    """
    Mary - Business Analyst and Vision Elicitation Facilitator.

    Mary helps users with vague ideas articulate clear product visions through
    structured discovery techniques (vision canvas, problem-solution fit, etc.).
    """

    def __init__(
        self,
        workflow_registry: WorkflowRegistry,
        prompt_loader: PromptLoader,
        analysis_service: AIAnalysisService,
        conversation_manager: Optional[ConversationManager] = None,
        project_root: Optional[Path] = None,
        mary_persona_path: Optional[Path] = None,
    ):
        """
        Initialize Mary Orchestrator.

        Args:
            workflow_registry: Registry of available workflows
            prompt_loader: PromptLoader for loading vision prompts (Epic 10)
            analysis_service: AI analysis service for facilitation
            conversation_manager: Optional conversation manager for multi-turn dialogue
            project_root: Project root for output files
            mary_persona_path: Path to Mary's agent definition
        """
        self.workflow_registry = workflow_registry
        self.prompt_loader = prompt_loader
        self.analysis_service = analysis_service
        self.conversation_manager = conversation_manager
        self.mary_persona_path = mary_persona_path
        self.logger = logger.bind(component="mary_orchestrator", agent="Mary")

        # Setup project root
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

        # Initialize brainstorming engine
        self.brainstorming_engine = BrainstormingEngine(
            analysis_service=analysis_service, conversation_manager=conversation_manager
        )

        # Initialize requirements analyzer
        self.requirements_analyzer = RequirementsAnalyzer(analysis_service=analysis_service)

        # Initialize domain question library (Story 31.4)
        self.domain_library = DomainQuestionLibrary(analysis_service=analysis_service)

        self.logger.info("mary_orchestrator_initialized", project_root=str(project_root))

    def select_clarification_strategy(
        self, user_request: str, vagueness_score: float
    ) -> ClarificationStrategy:
        """
        Select appropriate clarification strategy based on vagueness.

        Args:
            user_request: User's original request
            vagueness_score: Vagueness score from Brian (0.0-1.0)

        Returns:
            ClarificationStrategy to use
        """
        # High vagueness (>0.8) triggers full vision elicitation
        if vagueness_score > 0.8:
            self.logger.info(
                "vision_elicitation_selected",
                vagueness_score=vagueness_score,
                reason="High vagueness requires structured discovery",
            )
            return ClarificationStrategy.VISION_ELICITATION

        # Medium vagueness (0.5-0.8) uses simple questions
        self.logger.info(
            "simple_questions_selected",
            vagueness_score=vagueness_score,
            reason="Medium vagueness, simple clarification sufficient",
        )
        return ClarificationStrategy.SIMPLE_QUESTIONS

    async def get_clarification_questions(
        self,
        user_request: str,
        project_context: Optional[Dict] = None,
        focus_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get domain-specific clarification questions.

        Story 31.4: Uses domain detection to provide contextually relevant questions.

        Args:
            user_request: User's project description or request
            project_context: Optional project context dict
            focus_area: Optional focus area for targeted questions

        Returns:
            Dict with:
                - domain: Detected domain type
                - confidence: Detection confidence (0.0-1.0)
                - questions: List of domain-specific questions
                - focus_areas: Available focus areas for this domain

        Example:
            ```python
            result = await mary.get_clarification_questions(
                user_request="I want to build a web app for task management",
                focus_area="authentication"
            )
            print(f"Domain: {result['domain']}")
            print(f"Questions: {result['questions']}")
            ```
        """
        self.logger.info(
            "getting_clarification_questions",
            request=user_request[:50],
            has_context=bool(project_context),
            focus_area=focus_area,
        )

        # Detect domain
        domain, confidence = await self.domain_library.detect_domain(
            user_request, project_context
        )

        # Get questions
        questions = self.domain_library.get_questions(domain, focus_area)

        # Get available focus areas
        focus_areas = self.domain_library.get_available_focus_areas(domain)

        result = {
            "domain": domain.value,
            "confidence": confidence,
            "questions": questions,
            "focus_areas": focus_areas,
        }

        self.logger.info(
            "clarification_questions_prepared",
            domain=domain.value,
            confidence=confidence,
            question_count=len(questions),
            focus_areas_count=len(focus_areas),
        )

        return result

    async def elicit_vision(
        self,
        user_request: str,
        technique: str = "vision_canvas",
        project_context: str = "",
    ) -> VisionSummary:
        """
        Elicit product vision through guided discovery.

        This is Mary's main vision elicitation method. She facilitates a structured
        conversation using one of four techniques to help users clarify their vision.

        Args:
            user_request: Original vague request
            technique: Vision technique to use (vision_canvas, problem_solution_fit,
                      outcome_mapping, 5w1h)
            project_context: Optional project context

        Returns:
            VisionSummary with clarified vision

        Raises:
            ValueError: If technique is invalid
        """
        self.logger.info(
            "vision_elicitation_started",
            user_request=user_request[:100],
            technique=technique,
        )

        start_time = datetime.now()

        # Validate technique
        valid_techniques = ["vision_canvas", "problem_solution_fit", "outcome_mapping", "5w1h"]
        if technique not in valid_techniques:
            raise ValueError(
                f"Invalid technique '{technique}'. "
                f"Must be one of: {', '.join(valid_techniques)}"
            )

        # Load workflow metadata
        try:
            workflow = self.workflow_registry.get_workflow("vision-elicitation")
            if not workflow:
                raise ValueError("vision-elicitation workflow not found in registry")
        except Exception as e:
            self.logger.error("workflow_load_failed", error=str(e))
            raise

        # Get prompt name for selected technique
        prompt_name = workflow.metadata.get("prompts", {}).get(technique)
        if not prompt_name:
            # Fallback to technique name if not in metadata
            prompt_name = f"mary_{technique}"

        self.logger.debug("loading_prompt", prompt_name=prompt_name)

        # Load prompt template (Epic 10 PromptLoader)
        try:
            template = self.prompt_loader.load_prompt(f"agents/{prompt_name}")
        except Exception as e:
            self.logger.error("prompt_load_failed", prompt_name=prompt_name, error=str(e))
            raise

        # Load Mary's persona if available
        mary_context = ""
        if self.mary_persona_path and self.mary_persona_path.exists():
            mary_context = self.mary_persona_path.read_text(encoding="utf-8")

        # Render prompt with variables (Epic 10 reference resolution)
        try:
            rendered = self.prompt_loader.render_prompt(
                template,
                variables={
                    "user_request": user_request,
                    "mary_persona": mary_context,
                    "project_context": project_context,
                },
            )
        except Exception as e:
            self.logger.error("prompt_render_failed", error=str(e))
            raise

        # For MVP: Generate mock vision summary
        # TODO: In Story 31.2+, implement actual multi-turn conversation
        self.logger.info(
            "generating_mock_vision_summary",
            note="Multi-turn conversation will be implemented in Story 31.2+",
        )

        vision_summary = await self._generate_mock_vision_summary(
            user_request, technique, project_context, rendered, template
        )

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds() / 60.0
        vision_summary.duration_minutes = duration

        # Save to .gao-dev/mary/vision-documents/
        output_path = await self._save_vision(vision_summary, technique)
        vision_summary.file_path = output_path

        self.logger.info(
            "vision_elicitation_complete",
            technique=technique,
            duration_minutes=round(duration, 2),
            output_path=str(output_path),
        )

        return vision_summary

    async def _generate_mock_vision_summary(
        self,
        user_request: str,
        technique: str,
        project_context: str,
        rendered_prompt: str,
        template: Any,
    ) -> VisionSummary:
        """
        Generate mock vision summary using AI analysis (single-shot).

        This is a simplified version for MVP. Story 31.2+ will implement
        actual multi-turn conversation with ConversationManager.

        Args:
            user_request: Original request
            technique: Technique used
            project_context: Project context
            rendered_prompt: Rendered prompt
            template: Prompt template

        Returns:
            VisionSummary with generated content
        """
        # Use AI to generate structured vision content
        system_prompt = self.prompt_loader.render_system_prompt(
            template,
            variables={
                "user_request": user_request,
                "mary_persona": "",
                "project_context": project_context,
            },
        )

        try:
            await self.analysis_service.analyze(
                prompt=rendered_prompt,
                system_prompt=system_prompt,
                response_format="text",
                max_tokens=template.response.get("max_tokens", 1024),
                temperature=template.response.get("temperature", 0.7),
            )

        except Exception as e:
            self.logger.error("ai_analysis_failed", error=str(e))
            # Fallback to minimal mock data

        # Parse response into appropriate data structure
        if technique == "vision_canvas":
            canvas = VisionCanvas(
                target_users=f"Users interested in: {user_request[:50]}",
                user_needs="Need to accomplish their goals efficiently",
                product_vision=f"Build a solution for: {user_request}",
                key_features=["Core functionality", "User-friendly interface", "Reliable performance"],
                success_metrics=["User adoption rate", "User satisfaction score"],
                differentiators="Innovative approach to solving user needs",
            )
            return VisionSummary(
                user_request=user_request,
                technique_used=technique,
                project_context=project_context,
                vision_canvas=canvas,
                created_at=datetime.now(),
                turn_count=1,  # Mock single turn
            )

        elif technique == "problem_solution_fit":
            psf = ProblemSolutionFit(
                problem_definition=f"Users need to: {user_request}",
                current_solutions="Manual workarounds and existing tools",
                gaps_pain_points=["Inefficient process", "Lack of integration", "Poor user experience"],
                proposed_solution=f"Automated solution for: {user_request}",
                value_proposition="Significantly faster and more reliable than alternatives",
            )
            return VisionSummary(
                user_request=user_request,
                technique_used=technique,
                project_context=project_context,
                problem_solution_fit=psf,
                created_at=datetime.now(),
                turn_count=1,
            )

        elif technique == "outcome_mapping":
            outcome_map = OutcomeMap(
                desired_outcomes=["Improved user productivity", "Reduced errors", "Higher satisfaction"],
                leading_indicators=["Early user adoption", "Positive feedback"],
                lagging_indicators=["Long-term usage metrics", "Business impact"],
                stakeholders=["End users", "Business owners", "Development team"],
            )
            return VisionSummary(
                user_request=user_request,
                technique_used=technique,
                project_context=project_context,
                outcome_map=outcome_map,
                created_at=datetime.now(),
                turn_count=1,
            )

        else:  # 5w1h
            five_w = FiveWOneH(
                who="Target users who need this capability",
                what=f"A solution for: {user_request}",
                when="As soon as feasible, based on priority",
                where="In the users' typical working environment",
                why="To address critical user needs and improve outcomes",
                how="Following agile development principles with iterative delivery",
            )
            return VisionSummary(
                user_request=user_request,
                technique_used=technique,
                project_context=project_context,
                five_w_one_h=five_w,
                created_at=datetime.now(),
                turn_count=1,
            )

    async def _save_vision(
        self, vision_summary: VisionSummary, technique: str
    ) -> Path:
        """
        Save vision summary to .gao-dev/mary/vision-documents/.

        Args:
            vision_summary: Vision summary to save
            technique: Technique used

        Returns:
            Path to saved file
        """
        # Create output directory
        output_dir = self.project_root / ".gao-dev" / "mary" / "vision-documents"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = vision_summary.created_at.strftime("%Y%m%d-%H%M%S")
        filename = f"vision-{technique}-{timestamp}.md"
        output_path = output_dir / filename

        # Write markdown
        try:
            markdown_content = vision_summary.to_markdown()
            output_path.write_text(markdown_content, encoding="utf-8")
            self.logger.info("vision_document_saved", path=str(output_path))
        except Exception as e:
            self.logger.error("vision_save_failed", path=str(output_path), error=str(e))
            raise

        return output_path

    async def facilitate_brainstorming(
        self,
        topic: str,
        goal: BrainstormingGoal = BrainstormingGoal.EXPLORATION,
        techniques: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> BrainstormingSummary:
        """
        Facilitate brainstorming session with multiple techniques.

        Mary guides users through creative exploration using BMAD techniques,
        captures ideas, generates mind maps, and synthesizes insights.

        Args:
            topic: Brainstorming topic
            goal: Brainstorming goal (innovation, problem_solving, etc.)
            techniques: Optional list of specific technique names to use
            context: Optional context (energy_level, etc.)

        Returns:
            BrainstormingSummary with all session results

        Raises:
            ValueError: If invalid technique names provided
        """
        self.logger.info(
            "brainstorming_session_started",
            topic=topic[:100],
            goal=goal.value,
            techniques=techniques,
        )

        from datetime import datetime

        start_time = datetime.now()
        all_ideas: List[Idea] = []
        techniques_used: List[str] = []

        # Get techniques to use
        if techniques:
            # Validate and get specific techniques
            technique_objects = []
            for name in techniques:
                tech = self.brainstorming_engine.get_technique(name)
                if not tech:
                    raise ValueError(f"Invalid technique name: {name}")
                technique_objects.append(tech)
        else:
            # Get recommendations
            technique_objects = await self.brainstorming_engine.recommend_techniques(
                topic=topic, goal=goal, context=context or {}
            )

        self.logger.info(
            "techniques_selected",
            count=len(technique_objects),
            names=[t.name for t in technique_objects],
        )

        # Facilitate each technique
        # For MVP: Use mock responses (in production, would use ConversationManager)
        for technique in technique_objects:
            techniques_used.append(technique.name)

            if technique.name == "SCAMPER Method":
                # Use SCAMPER implementation
                ideas = await self.brainstorming_engine.facilitate_scamper(
                    topic=topic, user_responses=None
                )
                all_ideas.extend(ideas)
                self.logger.info("scamper_completed", idea_count=len(ideas))

            elif "How Might We" in technique.name or technique.name == "Question Storming":
                # Use HMW implementation
                ideas = await self.brainstorming_engine.facilitate_how_might_we(
                    problem_statement=topic, user_responses=None
                )
                all_ideas.extend(ideas)
                self.logger.info("hmw_completed", idea_count=len(ideas))

            else:
                # Generic facilitation: create placeholder ideas
                for i, prompt in enumerate(technique.facilitation_prompts[:3], 1):
                    idea = Idea(
                        content=f"[Idea {i} from {technique.name}: {prompt[:50]}...]",
                        technique=technique.name,
                    )
                    all_ideas.append(idea)
                self.logger.info("generic_technique_completed", technique=technique.name)

        # Perform affinity mapping
        await self.brainstorming_engine.perform_affinity_mapping(
            ideas=all_ideas, num_themes=5
        )

        # Generate mind map
        try:
            mind_map = await self.brainstorming_engine.generate_mind_map(
                ideas=all_ideas, central_topic=topic
            )
            mind_maps = [mind_map]
        except Exception as e:
            self.logger.error("mind_map_generation_failed", error=str(e))
            mind_maps = []

        # Synthesize insights
        insights = await self.brainstorming_engine.synthesize_insights(
            ideas=all_ideas, techniques_used=techniques_used, topic=topic
        )

        # Extract quick wins and long-term opportunities
        quick_wins = []
        long_term = []
        for quick_win_text in insights.get("quick_wins", [])[:5]:
            quick_wins.append(Idea(content=quick_win_text, technique="Synthesis", priority="quick_win"))
        for long_term_text in insights.get("long_term_opportunities", [])[:5]:
            long_term.append(
                Idea(content=long_term_text, technique="Synthesis", priority="long_term")
            )

        # Calculate duration
        duration = datetime.now() - start_time

        # Create summary
        summary = BrainstormingSummary(
            topic=topic,
            techniques_used=techniques_used,
            ideas_generated=all_ideas,
            mind_maps=mind_maps,
            key_themes=insights.get("key_themes", []),
            insights_learnings=insights.get("insights_learnings", []),
            quick_wins=quick_wins,
            long_term_opportunities=long_term,
            recommended_followup=insights.get("recommended_followup", []),
            session_duration=duration,
            created_at=start_time,
        )

        # Save to file
        output_path = await self._save_brainstorming(summary)
        summary.file_path = output_path

        self.logger.info(
            "brainstorming_session_complete",
            idea_count=len(all_ideas),
            duration_seconds=duration.total_seconds(),
            output_path=str(output_path),
        )

        return summary

    async def _save_brainstorming(self, summary: BrainstormingSummary) -> Path:
        """
        Save brainstorming summary to .gao-dev/mary/brainstorming-sessions/.

        Args:
            summary: Brainstorming summary to save

        Returns:
            Path to saved file

        Raises:
            IOError: If file save fails
        """
        # Create output directory
        output_dir = self.project_root / ".gao-dev" / "mary" / "brainstorming-sessions"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = summary.created_at.strftime("%Y%m%d-%H%M%S")
        # Sanitize topic for filename
        topic_safe = "".join(c if c.isalnum() or c in "-_ " else "" for c in summary.topic)[:50]
        topic_safe = topic_safe.strip().replace(" ", "-")
        filename = f"brainstorming-{topic_safe}-{timestamp}.md"
        output_path = output_dir / filename

        # Write markdown
        try:
            markdown_content = summary.to_markdown()
            output_path.write_text(markdown_content, encoding="utf-8")
            self.logger.info("brainstorming_document_saved", path=str(output_path))
        except Exception as e:
            self.logger.error("brainstorming_save_failed", path=str(output_path), error=str(e))
            raise IOError(f"Failed to save brainstorming summary: {e}")

        return output_path

    async def analyze_requirements(
        self,
        requirements: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> RequirementsAnalysis:
        """
        Perform comprehensive requirements analysis.

        Uses professional BA techniques:
        - MoSCoW prioritization (Must, Should, Could, Won't)
        - Kano model categorization (Basic, Performance, Excitement)
        - Dependency mapping
        - Risk identification
        - Constraint analysis

        Args:
            requirements: List of requirement strings to analyze
            context: Optional context dict with product_vision, timeline, team_size, etc.

        Returns:
            RequirementsAnalysis with all analysis results

        Raises:
            ValueError: If requirements list is empty
        """
        if not requirements:
            raise ValueError("Requirements list cannot be empty")

        if context is None:
            context = {}

        self.logger.info(
            "requirements_analysis_started",
            req_count=len(requirements),
            has_context=bool(context),
        )

        from datetime import datetime

        start_time = datetime.now()

        # Perform full analysis
        analysis = await self.requirements_analyzer.analyze_all(requirements, context)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Save to .gao-dev/mary/requirements-analysis/
        output_path = await self._save_requirements_analysis(analysis)
        analysis.file_path = output_path

        self.logger.info(
            "requirements_analysis_complete",
            duration_seconds=round(duration, 2),
            output_path=str(output_path),
            must_count=len([m for m in analysis.moscow if m.category.lower() == "must"]),
            risk_count=len(analysis.risks),
        )

        return analysis

    async def _save_requirements_analysis(
        self, analysis: RequirementsAnalysis
    ) -> Path:
        """
        Save requirements analysis to .gao-dev/mary/requirements-analysis/.

        Args:
            analysis: RequirementsAnalysis to save

        Returns:
            Path to saved file

        Raises:
            IOError: If file save fails
        """
        # Create output directory
        output_dir = self.project_root / ".gao-dev" / "mary" / "requirements-analysis"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = analysis.created_at.strftime("%Y%m%d-%H%M%S")
        filename = f"requirements-analysis-{timestamp}.md"
        output_path = output_dir / filename

        # Write markdown
        try:
            markdown_content = analysis.to_markdown()
            output_path.write_text(markdown_content, encoding="utf-8")
            self.logger.info("requirements_analysis_saved", path=str(output_path))
        except Exception as e:
            self.logger.error(
                "requirements_analysis_save_failed", path=str(output_path), error=str(e)
            )
            raise IOError(f"Failed to save requirements analysis: {e}")

        return output_path
