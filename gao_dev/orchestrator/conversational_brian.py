"""Conversational wrapper around BrianOrchestrator."""

from typing import AsyncIterator, Optional, Any
from dataclasses import dataclass
import structlog

from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel
from gao_dev.orchestrator.intent_parser import IntentParser, Intent, IntentType

logger = structlog.get_logger()


@dataclass
class ConversationContext:
    """
    Context for conversation session.

    Attributes:
        project_root: Project root path
        session_history: List of conversation turns
        pending_confirmation: Workflow sequence awaiting confirmation
        current_epic: Current epic number (if any)
        current_story: Current story number (if any)
    """

    project_root: str
    session_history: list[str]
    pending_confirmation: Optional[WorkflowSequence] = None
    current_epic: Optional[int] = None
    current_story: Optional[int] = None


class ConversationalBrian:
    """
    Conversational wrapper around BrianOrchestrator.

    Transforms Brian's analytical capabilities into natural dialogue.
    Handles intent parsing, workflow analysis formatting, and
    confirmation flows.
    """

    def __init__(self, brian_orchestrator: BrianOrchestrator):
        """
        Initialize conversational Brian.

        Args:
            brian_orchestrator: BrianOrchestrator instance
        """
        self.brian = brian_orchestrator
        self.intent_parser = IntentParser()
        self.logger = logger.bind(component="conversational_brian")

    async def handle_input(
        self, user_input: str, context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle user input conversationally.

        Parses intent, routes to appropriate handler, yields
        conversational responses.

        Args:
            user_input: User's message
            context: Conversation context

        Yields:
            Conversational responses
        """
        self.logger.info("handling_input", input_length=len(user_input))

        # Parse intent
        intent = self.intent_parser.parse(user_input)

        # Route based on intent
        if intent.type == IntentType.CONFIRMATION:
            # Handle pending confirmation
            async for response in self._handle_confirmation(intent, context):
                yield response

        elif intent.type == IntentType.FEATURE_REQUEST:
            # Analyze feature request with Brian
            async for response in self._handle_feature_request(user_input, context):
                yield response

        elif intent.type == IntentType.QUESTION:
            # Answer question
            yield self._handle_question(user_input, context)

        elif intent.type == IntentType.HELP:
            # Show help
            yield self._show_help()

        else:
            # Unclear input
            yield self._handle_unclear(user_input)

    async def _handle_feature_request(
        self, user_input: str, context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle feature/project request with Brian.

        Args:
            user_input: User's request
            context: Conversation context

        Yields:
            Conversational responses
        """
        self.logger.info("handling_feature_request")

        # Phase 1: Acknowledge
        yield "Let me analyze that for you..."

        # Phase 2: Analyze with Brian
        try:
            analysis = await self.brian.assess_and_select_workflows(user_input)
        except Exception as e:
            self.logger.exception("analysis_failed", error=str(e))
            yield f"I encountered an error analyzing your request: {str(e)}"
            yield "Could you rephrase your request or provide more details?"
            return

        # Phase 3: Present analysis conversationally
        yield self._format_analysis(analysis)

        # Phase 4: Store pending confirmation
        context.pending_confirmation = analysis

        # Phase 5: Ask for confirmation
        yield "\nShall I proceed with this plan? (yes/no)"

    def _format_analysis(self, analysis: WorkflowSequence) -> str:
        """
        Format Brian's analysis as conversational message.

        Args:
            analysis: WorkflowSequence from Brian

        Returns:
            Formatted analysis message
        """
        # Format scale level
        scale_desc = self._describe_scale_level(analysis.scale_level)

        # Format workflows
        workflows_desc = self._format_workflows(analysis.workflows)

        # Estimate duration
        duration_desc = self._estimate_duration(analysis)

        # Get project type
        project_type = (
            analysis.project_type.value if hasattr(analysis, "project_type") else "Unknown"
        )

        return f"""
I've analyzed your request. Here's what I found:

**Scale Level**: {scale_desc}
**Project Type**: {project_type}

**Reasoning**: {analysis.routing_rationale}

**Recommended Workflows**:
{workflows_desc}

**Estimated Duration**: {duration_desc}
        """.strip()

    def _describe_scale_level(self, scale_level: ScaleLevel) -> str:
        """Describe scale level in natural language."""
        descriptions = {
            0: "Level 0 - Quick chore (< 1 hour, no planning needed)",
            1: "Level 1 - Bug fix (1-4 hours, minimal planning)",
            2: "Level 2 - Small feature (1-2 weeks, light planning)",
            3: "Level 3 - Medium feature (1-2 months, full planning)",
            4: "Level 4 - Greenfield app (2-6 months, comprehensive)",
        }
        level_num: int = scale_level.value
        return descriptions.get(level_num, f"Level {level_num}")

    def _format_workflows(self, workflows: list[Any]) -> str:
        """Format workflow list as bullet points."""
        if not workflows:
            return "  - Direct implementation (no formal workflows)"

        lines = []
        for i, workflow in enumerate(workflows, 1):
            workflow_name = workflow.name if hasattr(workflow, "name") else str(workflow)
            lines.append(f"  {i}. {workflow_name}")

        return "\n".join(lines)

    def _estimate_duration(self, analysis: WorkflowSequence) -> str:
        """Estimate duration from workflow sequence."""
        # Simple heuristic based on workflow count
        workflow_count = len(analysis.workflows) if analysis.workflows else 1

        if workflow_count <= 2:
            return "Less than 1 hour"
        elif workflow_count <= 4:
            return "A few hours"
        elif workflow_count <= 8:
            return "1-2 days"
        else:
            return "Several days to weeks"

    async def _handle_confirmation(
        self, intent: Intent, context: ConversationContext
    ) -> AsyncIterator[str]:
        """
        Handle confirmation response.

        Args:
            intent: Parsed confirmation intent
            context: Conversation context

        Yields:
            Conversational responses
        """
        if not context.pending_confirmation:
            yield "I'm not sure what you're confirming. What would you like to do?"
            return

        if intent.is_positive:
            # User confirmed - execution will happen in Story 30.4
            yield "Great! I'll coordinate with the team to get started..."
            # NOTE: Actual execution will be handled by CommandRouter in Story 30.4
            # For now, just acknowledge
            yield "(Execution will be implemented in Story 30.4)"

            # Clear pending confirmation
            context.pending_confirmation = None

        else:
            # User declined
            yield "No problem! Let me know if you'd like to try a different approach."
            context.pending_confirmation = None

    def _handle_question(self, user_input: str, context: ConversationContext) -> str:
        """
        Handle user question.

        Args:
            user_input: User's question
            context: Conversation context

        Returns:
            Answer or guidance
        """
        # Simple keyword-based Q&A
        # Future: Could use RAG or semantic search

        user_lower = user_input.lower()

        if "status" in user_lower or "progress" in user_lower:
            return "To see project status, I check at startup. Type 'refresh' to reload."

        elif "workflow" in user_lower:
            return "I can select workflows based on your request. Just describe what you want to build!"

        elif "help" in user_lower or "what can" in user_lower:
            return self._show_help()

        else:
            return "I'm not sure about that. Could you ask in a different way, or type 'help' for guidance?"

    def _show_help(self) -> str:
        """Show help message."""
        return """
I'm here to help you build software! Here's what I can do:

**Feature Requests**: Just describe what you want to build
  - "I want to add authentication"
  - "Build a todo app with a REST API"
  - "Fix the bug in the login flow"

**Project Information**:
  - "What's the status?" - Current project state
  - "What should I work on next?" - Suggestions

**Commands**:
  - 'help' - Show this message
  - 'exit', 'quit', 'bye' - End session

Just type naturally and I'll figure out what you need!
        """.strip()

    def _handle_unclear(self, user_input: str) -> str:
        """
        Handle unclear input.

        Args:
            user_input: User's unclear message

        Returns:
            Helpful clarification request
        """
        return f"""
I'm not quite sure what you mean by "{user_input[:50]}...".

Could you rephrase that? For example:
  - "I want to build [feature]"
  - "Help me fix [bug]"
  - "What's the status?"

Or type 'help' for more guidance.
        """.strip()
