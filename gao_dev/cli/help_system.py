"""AI-powered context-aware help system for interactive Brian chat.

Provides intelligent help responses based on project state, user query,
and current context using AIAnalysisService.

Epic: 30 - Interactive Brian Chat Interface
Story: 30.4 - Command Routing & Execution
"""

from typing import Dict, Any, Optional
from pathlib import Path
import structlog
from rich.panel import Panel
from rich.markdown import Markdown

from gao_dev.core.services.ai_analysis_service import AIAnalysisService
from gao_dev.core.state.state_tracker import StateTracker

logger = structlog.get_logger()


class HelpSystem:
    """
    AI-powered context-aware help system.

    Analyzes help queries using AI and provides targeted guidance
    based on current project state, NOT generic command lists.

    Features:
    - Understands natural language help queries
    - Gathers project context (epic count, story status, etc.)
    - Generates context-specific guidance
    - Suggests concrete next steps
    - Formatted with Rich Panels

    Example:
        ```python
        help_system = HelpSystem(analysis_service, state_tracker)

        # Greenfield project
        response = await help_system.get_help("help", project_root)
        # -> "Start by creating a PRD..."

        # Active project with epics
        response = await help_system.get_help("help with ceremonies", project_root)
        # -> "You have 3 epics in progress. Consider a planning ceremony..."

        # User stuck
        response = await help_system.get_help("help I'm stuck", project_root)
        # -> "Let's diagnose: You have 2 blocked stories..."
        ```
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService,
        state_tracker: Optional[StateTracker] = None
    ):
        """
        Initialize help system.

        Args:
            analysis_service: AIAnalysisService for intelligent help
            state_tracker: Optional StateTracker for project context
        """
        self.analysis_service = analysis_service
        self.state_tracker = state_tracker
        self.logger = logger.bind(component="help_system")

    async def get_help(
        self,
        query: str,
        project_root: Path
    ) -> str:
        """
        Get context-aware help response.

        Args:
            query: User's help query (e.g., "help", "help with ceremonies")
            project_root: Project root for context gathering

        Returns:
            Formatted help response with guidance
        """
        self.logger.info("help_requested", query=query)

        # Gather project context
        context = self._gather_project_context(project_root)

        # Analyze query with AI
        help_response = await self._analyze_help_query(query, context)

        return help_response

    def _gather_project_context(self, project_root: Path) -> Dict[str, Any]:
        """
        Gather current project context.

        Args:
            project_root: Project root

        Returns:
            Dictionary with project context
        """
        context = {
            "project_root": str(project_root),
            "has_gao_dev": (project_root / ".gao-dev").exists(),
            "epic_count": 0,
            "active_epic_count": 0,
            "story_count": 0,
            "in_progress_story_count": 0,
            "blocked_story_count": 0,
            "project_state": "greenfield"
        }

        # Try to get state from StateTracker
        if self.state_tracker:
            try:
                # Get epics
                active_epics = self.state_tracker.get_active_epics()
                context["epic_count"] = len(active_epics)
                context["active_epic_count"] = len(active_epics)

                # Get stories
                in_progress = self.state_tracker.get_stories_in_progress()
                blocked = self.state_tracker.get_blocked_stories()
                context["in_progress_story_count"] = len(in_progress)
                context["blocked_story_count"] = len(blocked)

                # Determine project state
                if context["epic_count"] == 0:
                    context["project_state"] = "greenfield"
                elif context["in_progress_story_count"] > 0:
                    context["project_state"] = "active_development"
                elif context["blocked_story_count"] > 0:
                    context["project_state"] = "blocked"
                else:
                    context["project_state"] = "planning"

            except Exception as e:
                self.logger.debug("context_gathering_failed", error=str(e))

        return context

    async def _analyze_help_query(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Analyze help query with AI to generate context-aware response.

        Args:
            query: User's help query
            context: Project context dictionary

        Returns:
            Context-aware help response
        """
        # Build prompt with context
        prompt = self._build_help_prompt(query, context)

        try:
            result = await self.analysis_service.analyze(
                prompt=prompt,
                response_format="text",
                max_tokens=800,
                temperature=0.7
            )

            # Format response
            return self._format_help_response(result.response)

        except Exception as e:
            self.logger.error("help_analysis_failed", error=str(e))
            return self._fallback_help_response(context)

    def _build_help_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build help analysis prompt with project context.

        Args:
            query: User's help query
            context: Project context

        Returns:
            Prompt for AI analysis
        """
        # Extract key context
        project_state = context.get("project_state", "unknown")
        epic_count = context.get("epic_count", 0)
        in_progress = context.get("in_progress_story_count", 0)
        blocked = context.get("blocked_story_count", 0)

        prompt = f"""
You are Brian, an AI Engineering Manager helping a developer with GAO-Dev.

User's query: "{query}"

Current project state:
- State: {project_state}
- Epics: {epic_count} total
- Stories in progress: {in_progress}
- Blocked stories: {blocked}

Provide context-aware, actionable help based on the query and project state.

Guidelines:
1. Be specific and actionable (NOT generic command lists)
2. Reference the current project state
3. Suggest concrete next steps
4. Keep response concise (3-5 bullet points)
5. Use encouraging, supportive tone

If project is greenfield:
- Suggest starting with PRD or architecture
- Explain the workflow-driven approach

If project is active:
- Focus on current work
- Suggest ceremonies if needed
- Help with blocking issues

If query is about specific topic (ceremonies, workflows, etc.):
- Provide targeted guidance for that topic
- Show how it applies to current state

Format response as markdown with bullet points.
""".strip()

        return prompt

    def _format_help_response(self, ai_response: str) -> str:
        """
        Format AI-generated help response.

        Args:
            ai_response: Raw AI response

        Returns:
            Formatted help response
        """
        # Add header
        formatted = "**Brian's Help**\n\n"
        formatted += ai_response

        # Add footer
        formatted += "\n\n---\n*Type naturally to request features, or ask specific questions for guidance.*"

        return formatted

    def _fallback_help_response(self, context: Dict[str, Any]) -> str:
        """
        Fallback help response if AI analysis fails.

        Args:
            context: Project context

        Returns:
            Basic help response
        """
        project_state = context.get("project_state", "unknown")

        if project_state == "greenfield":
            return """
**Brian's Help**

You're starting fresh! Here's how to begin:

- Describe what you want to build in natural language
- I'll analyze it and suggest the right workflows
- I coordinate with the team (John, Winston, Bob, Amelia) to execute

Example: "I want to build a todo app with authentication"

---
*Type naturally to request features, or ask specific questions for guidance.*
            """.strip()

        elif project_state == "active_development":
            epic_count = context.get("epic_count", 0)
            in_progress = context.get("in_progress_story_count", 0)

            return f"""
**Brian's Help**

Your project is active:
- {epic_count} epic(s) defined
- {in_progress} story(ies) in progress

You can:
- Continue implementing stories: "implement story X.Y"
- Add new features: "I want to add [feature]"
- Run ceremonies: "hold a retrospective"
- Check status: "what's the status?"

---
*Type naturally to request features, or ask specific questions for guidance.*
            """.strip()

        else:
            return """
**Brian's Help**

I'm here to help you build software! You can:

**Request Features**:
- "I want to add authentication"
- "Build a REST API for users"
- "Fix the login bug"

**Project Management**:
- "What's the status?"
- "Show me blocked stories"
- "Hold a planning ceremony"

**Specific Help**:
- "Help with ceremonies"
- "Explain workflows"
- "What should I work on next?"

Just type naturally and I'll figure out what you need!

---
*Type naturally to request features, or ask specific questions for guidance.*
            """.strip()

    def format_help_panel(self, help_text: str) -> Panel:
        """
        Format help text as Rich Panel.

        Args:
            help_text: Help text (markdown)

        Returns:
            Rich Panel with formatted help
        """
        return Panel(
            Markdown(help_text),
            title="[bold green]Help[/bold green]",
            border_style="green"
        )
