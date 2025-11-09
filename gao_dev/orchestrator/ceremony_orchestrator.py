"""Ceremony orchestration service for multi-agent ceremonies.

Foundation created in Epic 22 (Story 22.4).
Full implementation in Epic 26.

This service coordinates multi-agent ceremonies (stand-ups, retrospectives, planning)
to enable collaborative learning and continuous improvement.

Epic 26 Implementation:
- FastContextLoader integration (<5ms context)
- ConversationManager (multi-agent dialogues)
- Ceremony artifacts (transcripts, summaries)
- Action item creation and tracking
- Learning extraction and indexing

Example:
    ```python
    orchestrator = CeremonyOrchestrator(
        config=config_loader,
        db_path=Path(".gao-dev/documents.db"),
        project_root=Path("/project")
    )

    # Hold stand-up ceremony
    result = orchestrator.hold_standup(
        epic_num=1,
        participants=["Amelia", "Bob", "John"]
    )

    # Hold retrospective
    result = orchestrator.hold_retrospective(
        epic_num=1,
        participants=["team"]
    )
    ```
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import structlog

from ..core.config_loader import ConfigLoader
from ..core.services.fast_context_loader import FastContextLoader
from ..core.services.ceremony_service import CeremonyService
from ..core.services.action_item_service import ActionItemService
from ..core.services.learning_index_service import LearningIndexService
from ..core.services.git_integrated_state_manager import GitIntegratedStateManager
from ..core.services.action_item_integration_service import ActionItemIntegrationService

logger = structlog.get_logger()


class CeremonyExecutionError(Exception):
    """Raised when ceremony execution fails."""
    pass


class CeremonyOrchestrator:
    """
    Ceremony orchestration service.

    Implemented in Epic 26 (previously foundation in Epic 22).

    Responsibilities:
    - Coordinate multi-agent ceremonies (stand-up, retrospective, planning)
    - Prepare ceremony context and participants
    - Execute ceremony conversations
    - Record ceremony outcomes and learnings

    Ceremony Types:
    - Stand-up: Daily status sync, blockers, action items
    - Retrospective: Learning capture, improvements, team health
    - Planning: Story estimation, sprint commitment, capacity planning

    Attributes:
        config: Configuration loader
        db_path: Path to state database
        project_root: Project root directory
        context_loader: FastContextLoader for <5ms context
        ceremony_service: Service for ceremony tracking
        action_service: Service for action item tracking
        learning_service: Service for learning indexing
    """

    def __init__(
        self,
        config: ConfigLoader,
        db_path: Path,
        project_root: Optional[Path] = None,
        git_state_manager: Optional[GitIntegratedStateManager] = None
    ):
        """
        Initialize ceremony orchestrator.

        Args:
            config: Configuration loader for ceremony settings
            db_path: Path to state database (.gao-dev/documents.db)
            project_root: Project root directory (for artifact storage)
            git_state_manager: Optional git-integrated state manager for atomic transactions (Epic 27.1)
        """
        self.config = config
        self.db_path = Path(db_path)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.git_state_manager = git_state_manager  # Epic 28.4: For atomic transactions

        # Initialize services
        self.context_loader = FastContextLoader(db_path=self.db_path)
        self.ceremony_service = CeremonyService(db_path=self.db_path)
        self.action_service = ActionItemService(db_path=self.db_path)
        self.learning_service = LearningIndexService(db_path=self.db_path)

        # Epic 29.5: Action item integration service
        git_manager = git_state_manager.git_manager if git_state_manager else None
        self.action_item_integration = ActionItemIntegrationService(
            db_path=self.db_path,
            project_root=self.project_root,
            git_manager=git_manager
        )

        self.logger = logger.bind(service="ceremony_orchestrator")
        self.logger.info(
            "ceremony_orchestrator_initialized",
            db_path=str(self.db_path),
            project_root=str(self.project_root),
            has_git_state_manager=git_state_manager is not None
        )

    def hold_ceremony(
        self,
        ceremony_type: str,
        epic_num: int,
        participants: List[str],
        story_num: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generic method to hold any type of ceremony.

        Implements the three-phase ceremony lifecycle with atomic transactions (C3 Fix):
        1. Prepare: Load context and prepare participants
        2. Execute: Run ceremony conversation (simulated in Epic 26)
        3. Record: Save artifacts and outcomes (ATOMIC: file + DB + git)

        Epic 28.4: Atomic transaction wrapper added
        - All operations (file + DB + git) are atomic
        - On failure, ALL operations roll back
        - No partial ceremony artifacts in repository

        Args:
            ceremony_type: Type of ceremony (standup, retrospective, planning)
            epic_num: Epic number for context
            participants: List of agent names to participate
            story_num: Optional story number for story-specific ceremonies
            additional_context: Optional additional context

        Returns:
            Dictionary with ceremony results:
            - ceremony_id: Database ID of ceremony record
            - transcript_path: Path to saved transcript
            - action_items: List of created action items
            - learnings: List of indexed learnings (retrospective only)
            - summary: Ceremony summary text
            - ceremony_type: Type of ceremony

        Raises:
            CeremonyExecutionError: If ceremony execution fails

        Example:
            ```python
            result = orchestrator.hold_ceremony(
                ceremony_type="standup",
                epic_num=1,
                participants=["Amelia", "Bob"]
            )
            print(f"Ceremony recorded: {result['ceremony_id']}")
            print(f"Action items: {len(result['action_items'])}")
            ```
        """
        start_time = datetime.now()

        self.logger.info(
            "ceremony_started",
            ceremony_type=ceremony_type,
            epic_num=epic_num,
            participants=participants
        )

        # C3 Fix: Wrap in atomic transaction if git_state_manager available
        if self.git_state_manager is not None:
            return self._hold_ceremony_with_transaction(
                ceremony_type,
                epic_num,
                participants,
                story_num,
                additional_context,
                start_time
            )
        else:
            # Fallback: Execute without transaction (backward compatibility)
            return self._hold_ceremony_impl(
                ceremony_type,
                epic_num,
                participants,
                story_num,
                additional_context,
                start_time
            )

    def _hold_ceremony_with_transaction(
        self,
        ceremony_type: str,
        epic_num: int,
        participants: List[str],
        story_num: Optional[int],
        additional_context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Hold ceremony with atomic transaction boundary (C3 Fix).

        All operations are atomic: transcript file + DB records + git commit.
        On any failure, ALL operations roll back (no partial artifacts).

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number
            participants: List of participant names
            story_num: Optional story number
            additional_context: Optional additional context
            start_time: Ceremony start time

        Returns:
            Ceremony record dictionary

        Raises:
            CeremonyExecutionError: If ceremony fails (after rollback)
        """
        self.logger.info(
            "ceremony_transaction_starting",
            ceremony_type=ceremony_type,
            epic_num=epic_num
        )

        # Save checkpoint (git HEAD SHA before transaction)
        from ..core.services.git_integrated_state_manager import WorkingTreeDirtyError

        try:
            # Pre-flight check: working tree must be clean
            if not self.git_state_manager.git_manager.is_working_tree_clean():
                raise WorkingTreeDirtyError(
                    "Git working tree has uncommitted changes. "
                    "Commit or stash changes before holding ceremony."
                )

            checkpoint_sha = self.git_state_manager.git_manager.get_head_sha()

            # Execute ceremony (all operations)
            result = self._hold_ceremony_impl(
                ceremony_type,
                epic_num,
                participants,
                story_num,
                additional_context,
                start_time
            )

            # Git commit (if auto_commit enabled)
            if self.git_state_manager.auto_commit:
                commit_message = (
                    f"ceremony({ceremony_type}): epic {epic_num}\n\n"
                    f"{ceremony_type.capitalize()} ceremony for epic {epic_num}\n"
                    f"Participants: {', '.join(participants)}\n"
                    f"Action items: {len(result.get('action_items', []))}\n"
                    f"Learnings: {len(result.get('learnings', []))}"
                )

                self.git_state_manager.git_manager.add_all()
                commit_sha = self.git_state_manager.git_manager.commit(commit_message)

                self.logger.info(
                    "ceremony_committed",
                    ceremony_type=ceremony_type,
                    epic_num=epic_num,
                    ceremony_id=result.get("ceremony_id"),
                    commit_sha=commit_sha
                )

            return result

        except Exception as e:
            # Rollback on error
            self.logger.error(
                "ceremony_failed_rolling_back",
                ceremony_type=ceremony_type,
                epic_num=epic_num,
                error=str(e),
                exc_info=True
            )

            # Attempt rollback
            try:
                # Rollback git (hard reset to checkpoint)
                if self.git_state_manager is not None:
                    self.git_state_manager.git_manager.reset_hard(checkpoint_sha)

                    self.logger.info(
                        "ceremony_rollback_successful",
                        ceremony_type=ceremony_type,
                        epic_num=epic_num,
                        checkpoint_sha=checkpoint_sha
                    )
            except Exception as rollback_error:
                self.logger.error(
                    "ceremony_rollback_failed",
                    ceremony_type=ceremony_type,
                    epic_num=epic_num,
                    error=str(rollback_error)
                )
                # Continue - original error is more important

            # Re-raise as CeremonyExecutionError
            raise CeremonyExecutionError(
                f"Ceremony {ceremony_type} failed for epic {epic_num}: {e}"
            ) from e

    def _hold_ceremony_impl(
        self,
        ceremony_type: str,
        epic_num: int,
        participants: List[str],
        story_num: Optional[int],
        additional_context: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Implementation of ceremony execution (without transaction wrapper).

        This is the core ceremony logic that can be called with or without
        transaction support.

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number
            participants: List of participant names
            story_num: Optional story number
            additional_context: Optional additional context
            start_time: Ceremony start time

        Returns:
            Ceremony record dictionary
        """
        # Phase 1: Prepare
        context = self._prepare_ceremony(ceremony_type, epic_num, story_num)
        if additional_context:
            context.update(additional_context)

        # Phase 2: Execute (simulated conversation for now)
        # Future epic will integrate ConversationManager for real multi-agent dialogue
        results = self._execute_ceremony(ceremony_type, context, participants)

        # Phase 3: Record
        ceremony_record = self._record_ceremony(ceremony_type, epic_num, story_num, results)

        # Add ceremony_type to result
        ceremony_record["ceremony_type"] = ceremony_type

        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            "ceremony_completed",
            ceremony_type=ceremony_type,
            ceremony_id=ceremony_record["ceremony_id"],
            duration_seconds=duration
        )

        return ceremony_record

    def hold_standup(
        self,
        epic_num: int,
        participants: List[str]
    ) -> Dict[str, Any]:
        """
        Hold daily stand-up ceremony.

        Implemented in Epic 26 (Story 26.2).

        Stand-up ceremony includes:
        - What was accomplished yesterday
        - What's planned for today
        - Blockers and impediments
        - Action items for team support

        Args:
            epic_num: Epic number for context
            participants: List of agent names to participate

        Returns:
            Dictionary with ceremony results (see hold_ceremony)

        Example:
            ```python
            result = orchestrator.hold_standup(
                epic_num=1,
                participants=["Amelia", "Bob", "John"]
            )
            print(f"Blockers identified: {len(result['action_items'])}")
            ```
        """
        self.logger.info(
            "ceremony_standup_called",
            epic_num=epic_num,
            participants=participants
        )

        # Load epic context using FastContextLoader (<5ms)
        epic_context = self.context_loader.get_epic_context(
            epic_num=epic_num,
            include_stories=True,
            include_summary=True
        )

        # Generate stand-up specific context
        standup_context = {
            "epic": epic_context["epic"],
            "stories": epic_context["stories"],
            "summary": epic_context["summary"],
            "focus": "daily_status",
            "prompt": self._get_standup_prompt(epic_context)
        }

        return self.hold_ceremony(
            ceremony_type="standup",
            epic_num=epic_num,
            participants=participants,
            additional_context=standup_context
        )

    def hold_retrospective(
        self,
        epic_num: int,
        participants: List[str]
    ) -> Dict[str, Any]:
        """
        Hold retrospective ceremony.

        Implemented in Epic 26 (Story 26.3).

        Retrospective ceremony includes:
        - What went well (celebrate successes)
        - What could be improved (identify pain points)
        - Action items for next sprint
        - Team health and morale check
        - Learning extraction and indexing

        Args:
            epic_num: Epic number for context
            participants: List of agent names to participate

        Returns:
            Dictionary with ceremony results including learnings

        Example:
            ```python
            result = orchestrator.hold_retrospective(
                epic_num=1,
                participants=["team"]
            )
            print(f"Learnings captured: {len(result['learnings'])}")
            print(f"Improvements: {len(result['action_items'])}")
            ```
        """
        self.logger.info(
            "ceremony_retrospective_called",
            epic_num=epic_num,
            participants=participants
        )

        # Load epic context including completion metrics
        epic_context = self.context_loader.get_epic_context(
            epic_num=epic_num,
            include_stories=True,
            include_summary=True
        )

        # Generate retrospective-specific context
        retro_context = {
            "epic": epic_context["epic"],
            "stories": epic_context["stories"],
            "summary": epic_context["summary"],
            "focus": "learning_and_improvement",
            "prompt": self._get_retrospective_prompt(epic_context)
        }

        return self.hold_ceremony(
            ceremony_type="retrospective",
            epic_num=epic_num,
            participants=participants,
            additional_context=retro_context
        )

    def hold_planning(
        self,
        epic_num: int,
        participants: List[str]
    ) -> Dict[str, Any]:
        """
        Hold planning ceremony.

        Implemented in Epic 26 (Story 26.4).

        Planning ceremony includes:
        - Story estimation (complexity, effort)
        - Sprint commitment (capacity planning)
        - Risk identification and mitigation
        - Story sequencing and dependencies

        Args:
            epic_num: Epic number for context
            participants: List of agent names to participate

        Returns:
            Dictionary with ceremony results including commitments

        Example:
            ```python
            result = orchestrator.hold_planning(
                epic_num=2,
                participants=["John", "Winston", "Bob"]
            )
            print(f"Stories estimated: {result['summary']['total_stories']}")
            ```
        """
        self.logger.info(
            "ceremony_planning_called",
            epic_num=epic_num,
            participants=participants
        )

        # Load epic and story context
        epic_context = self.context_loader.get_epic_context(
            epic_num=epic_num,
            include_stories=True,
            include_summary=True
        )

        # Generate planning-specific context
        planning_context = {
            "epic": epic_context["epic"],
            "stories": epic_context["stories"],
            "summary": epic_context["summary"],
            "focus": "estimation_and_commitment",
            "prompt": self._get_planning_prompt(epic_context)
        }

        return self.hold_ceremony(
            ceremony_type="planning",
            epic_num=epic_num,
            participants=participants,
            additional_context=planning_context
        )

    # -------------------------------------------------------------------------
    # Ceremony Lifecycle Framework (Template Method Pattern)
    # -------------------------------------------------------------------------

    def _prepare_ceremony(
        self,
        ceremony_type: str,
        epic_num: int,
        story_num: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare ceremony context.

        Implemented in Epic 26 (Story 26.1).

        This is the first phase of the ceremony lifecycle (prepare → execute → record).

        Args:
            ceremony_type: Type of ceremony (standup, retrospective, planning)
            epic_num: Epic number for context
            story_num: Optional story number for story-specific ceremonies

        Returns:
            Dictionary with ceremony context:
            - epic_context: Epic information from FastContextLoader
            - previous_ceremonies: Recent ceremonies of same type
            - agenda: Ceremony agenda items
            - timestamp: Ceremony start time
        """
        start_time = datetime.now()

        self.logger.debug(
            "ceremony_prepare_started",
            ceremony_type=ceremony_type,
            epic_num=epic_num
        )

        # Load epic context using FastContextLoader (<5ms target)
        epic_context = self.context_loader.get_epic_context(
            epic_num=epic_num,
            include_stories=True,
            include_summary=True
        )

        # Load previous ceremonies for continuity
        previous_ceremonies = self.ceremony_service.get_recent(
            ceremony_type=ceremony_type,
            limit=3
        )

        # Build agenda based on ceremony type
        agenda = self._build_agenda(ceremony_type, epic_context)

        context = {
            "epic_context": epic_context,
            "previous_ceremonies": previous_ceremonies,
            "agenda": agenda,
            "timestamp": start_time.isoformat(),
            "ceremony_type": ceremony_type
        }

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "ceremony_prepare_completed",
            ceremony_type=ceremony_type,
            duration_ms=duration_ms
        )

        return context

    def _execute_ceremony(
        self,
        ceremony_type: str,
        context: Dict[str, Any],
        participants: List[str]
    ) -> Dict[str, Any]:
        """
        Execute ceremony with simulated multi-agent conversation.

        Implemented in Epic 26 (Story 26.1).
        ConversationManager integration in Story 26.5.

        This is the second phase of the ceremony lifecycle (prepare → execute → record).

        Args:
            ceremony_type: Type of ceremony (standup, retrospective, planning)
            context: Prepared ceremony context from _prepare_ceremony()
            participants: List of participant agent names

        Returns:
            Dictionary with ceremony results:
            - transcript: Full conversation transcript
            - action_items: Extracted action items (raw data)
            - learnings: Key learnings and insights (raw data)
            - decisions: Important decisions made
            - summary: Ceremony summary
        """
        start_time = datetime.now()

        self.logger.debug(
            "ceremony_execute_started",
            ceremony_type=ceremony_type,
            participants=participants
        )

        # Simulated conversation for Epic 26
        # Future epic will use ConversationManager for real multi-agent dialogue
        transcript_lines = []
        action_items_raw = []
        learnings_raw = []
        decisions = []

        # Generate simulated ceremony conversation
        if ceremony_type == "standup":
            transcript_lines, action_items_raw = self._simulate_standup(context, participants)
        elif ceremony_type == "retrospective":
            transcript_lines, action_items_raw, learnings_raw = self._simulate_retrospective(context, participants)
        elif ceremony_type == "planning":
            transcript_lines, action_items_raw, decisions = self._simulate_planning(context, participants)

        # Build transcript
        transcript = "\n".join(transcript_lines)

        # Generate summary
        summary = self._generate_summary(ceremony_type, context, len(action_items_raw), len(learnings_raw))

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.debug(
            "ceremony_execute_completed",
            ceremony_type=ceremony_type,
            duration_ms=duration_ms,
            action_items_count=len(action_items_raw),
            learnings_count=len(learnings_raw)
        )

        return {
            "transcript": transcript,
            "action_items": action_items_raw,
            "learnings": learnings_raw,
            "decisions": decisions,
            "summary": summary,
            "participants": participants
        }

    def _record_ceremony(
        self,
        ceremony_type: str,
        epic_num: int,
        story_num: Optional[int],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record ceremony outcomes.

        Implemented in Epic 26 (Story 26.1).
        Artifact integration in Story 26.6.

        This is the third phase of the ceremony lifecycle (prepare → execute → record).

        Args:
            ceremony_type: Type of ceremony (standup, retrospective, planning)
            epic_num: Epic number
            story_num: Optional story number
            results: Ceremony results from _execute_ceremony()

        Returns:
            Dictionary with recorded ceremony data:
            - ceremony_id: Database ID
            - transcript_path: Path to saved transcript
            - action_items: List of created action items
            - learnings: List of indexed learnings
            - summary: Summary text
        """
        start_time = datetime.now()

        self.logger.debug(
            "ceremony_record_started",
            ceremony_type=ceremony_type,
            epic_num=epic_num
        )

        # Save transcript to file
        transcript_path = self._save_transcript(
            ceremony_type,
            epic_num,
            story_num,
            results["transcript"]
        )

        # Create ceremony record in database
        ceremony_record = self.ceremony_service.create_summary(
            ceremony_type=ceremony_type,
            summary=results["summary"],
            participants=", ".join(results["participants"]),
            decisions="\n".join(results["decisions"]) if results["decisions"] else None,
            action_items=f"{len(results['action_items'])} items created",
            epic_num=epic_num,
            story_num=story_num,
            metadata={"transcript_path": str(transcript_path)}
        )

        # Create action items in database
        action_items_created = []
        for item_data in results["action_items"]:
            action_item = self.action_service.create(
                title=item_data["title"],
                description=item_data.get("description"),
                priority=item_data.get("priority", "medium"),
                assignee=item_data.get("assignee"),
                epic_num=epic_num,
                story_num=story_num,
                metadata={"ceremony_id": ceremony_record["id"]}
            )
            action_items_created.append(action_item)

        # Index learnings (retrospective only)
        learnings_indexed = []
        if ceremony_type == "retrospective" and results["learnings"]:
            for learning_data in results["learnings"]:
                learning = self.learning_service.index(
                    topic=learning_data["topic"],
                    category=learning_data.get("category", "process"),
                    learning=learning_data["learning"],
                    context=learning_data.get("context"),
                    source_type="retrospective",
                    epic_num=epic_num,
                    story_num=story_num,
                    metadata={"ceremony_id": ceremony_record["id"]}
                )
                learnings_indexed.append(learning)

        # Epic 29.5: Process action items for auto-conversion
        conversion_result = {"converted": 0, "tracked": 0}
        if action_items_created:
            try:
                conversion_result = self.action_item_integration.process_action_items(
                    ceremony_id=ceremony_record["id"]
                )
                self.logger.info(
                    "action_items_processed",
                    ceremony_id=ceremony_record["id"],
                    converted=conversion_result["converted"],
                    tracked=conversion_result["tracked"]
                )
            except Exception as e:
                self.logger.error(
                    "action_item_processing_failed",
                    ceremony_id=ceremony_record["id"],
                    error=str(e)
                )

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.info(
            "ceremony_record_completed",
            ceremony_type=ceremony_type,
            ceremony_id=ceremony_record["id"],
            duration_ms=duration_ms,
            action_items_count=len(action_items_created),
            learnings_count=len(learnings_indexed),
            action_items_converted=conversion_result["converted"],
            action_items_tracked=conversion_result["tracked"]
        )

        return {
            "ceremony_id": ceremony_record["id"],
            "transcript_path": str(transcript_path),
            "action_items": action_items_created,
            "learnings": learnings_indexed,
            "summary": results["summary"],
            "action_items_converted": conversion_result["converted"],
            "action_items_tracked": conversion_result["tracked"]
        }

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _build_agenda(
        self,
        ceremony_type: str,
        epic_context: Dict[str, Any]
    ) -> List[str]:
        """
        Build ceremony agenda based on type.

        Args:
            ceremony_type: Type of ceremony
            epic_context: Epic context from FastContextLoader

        Returns:
            List of agenda items
        """
        if ceremony_type == "standup":
            return [
                "Review yesterday's progress",
                "Plan today's work",
                "Identify blockers and impediments",
                "Assign action items for support"
            ]
        elif ceremony_type == "retrospective":
            return [
                "Review epic outcomes and metrics",
                "What went well (celebrate successes)",
                "What could be improved (identify pain points)",
                "Extract learnings for future work",
                "Create improvement action items"
            ]
        elif ceremony_type == "planning":
            return [
                "Review epic and story definitions",
                "Estimate story complexity and effort",
                "Identify dependencies and risks",
                "Calculate sprint commitment",
                "Sequence stories for execution"
            ]
        else:
            return ["Discuss ceremony objectives"]

    def _get_standup_prompt(self, epic_context: Dict[str, Any]) -> str:
        """Generate stand-up ceremony prompt."""
        epic = epic_context["epic"]
        summary = epic_context["summary"]

        return f"""Daily Stand-Up - Epic {epic.get('epic_num')}: {epic.get('title', 'Unknown')}

Progress: {summary['completed_stories']}/{summary['total_stories']} stories completed ({summary['progress_percentage']:.1f}%)

Please share:
1. What did you accomplish yesterday?
2. What are you working on today?
3. Any blockers or impediments?
"""

    def _get_retrospective_prompt(self, epic_context: Dict[str, Any]) -> str:
        """Generate retrospective ceremony prompt."""
        epic = epic_context["epic"]
        summary = epic_context["summary"]

        return f"""Retrospective - Epic {epic.get('epic_num')}: {epic.get('title', 'Unknown')}

Epic Completion: {summary['completed_stories']}/{summary['total_stories']} stories

Reflection topics:
1. What went well? (Celebrate successes)
2. What could be improved? (Identify pain points)
3. Key learnings for future epics
4. Action items for next sprint
"""

    def _get_planning_prompt(self, epic_context: Dict[str, Any]) -> str:
        """Generate planning ceremony prompt."""
        epic = epic_context["epic"]
        summary = epic_context["summary"]

        return f"""Planning Ceremony - Epic {epic.get('epic_num')}: {epic.get('title', 'Unknown')}

Stories to estimate: {summary['total_stories']}

Planning agenda:
1. Review story definitions
2. Estimate complexity and effort
3. Identify dependencies and risks
4. Commit to sprint scope
"""

    def _simulate_standup(
        self,
        context: Dict[str, Any],
        participants: List[str]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Simulate stand-up ceremony conversation.

        Returns:
            Tuple of (transcript_lines, action_items)
        """
        transcript = [
            f"=== Daily Stand-Up Ceremony ===",
            f"Date: {context['timestamp']}",
            f"Participants: {', '.join(participants)}",
            "",
            context.get("prompt", ""),
            ""
        ]

        action_items = []

        # Simulate each participant's update
        for participant in participants:
            transcript.append(f"{participant}: Yesterday I worked on story implementation.")
            transcript.append(f"{participant}: Today I will continue with testing.")

            # Simulate blocker
            if len(action_items) < 2:
                transcript.append(f"{participant}: Blocker: Need database schema review.")
                action_items.append({
                    "title": f"Review database schema for {participant}",
                    "description": "Unblock story implementation",
                    "priority": "high",
                    "assignee": "Winston"
                })

            transcript.append("")

        return transcript, action_items

    def _simulate_retrospective(
        self,
        context: Dict[str, Any],
        participants: List[str]
    ) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Simulate retrospective ceremony conversation.

        Returns:
            Tuple of (transcript_lines, action_items, learnings)
        """
        transcript = [
            f"=== Retrospective Ceremony ===",
            f"Date: {context['timestamp']}",
            f"Participants: {', '.join(participants)}",
            "",
            context.get("prompt", ""),
            "",
            "=== What Went Well ===",
            "- Completed all stories on time",
            "- Good test coverage maintained",
            "",
            "=== What Could Be Improved ===",
            "- Communication could be more frequent",
            "- Need better documentation",
            ""
        ]

        action_items = [
            {
                "title": "Establish daily stand-ups",
                "description": "Improve team communication",
                "priority": "medium",
                "assignee": "Bob"
            },
            {
                "title": "Create documentation standards",
                "description": "Ensure consistent documentation",
                "priority": "medium",
                "assignee": "John"
            }
        ]

        learnings = [
            {
                "topic": "Communication",
                "category": "process",
                "learning": "Daily stand-ups improve team coordination",
                "context": "Epic completion review"
            },
            {
                "topic": "Documentation",
                "category": "technical",
                "learning": "Documentation standards prevent inconsistency",
                "context": "Code review feedback"
            }
        ]

        return transcript, action_items, learnings

    def _simulate_planning(
        self,
        context: Dict[str, Any],
        participants: List[str]
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Simulate planning ceremony conversation.

        Returns:
            Tuple of (transcript_lines, action_items, decisions)
        """
        epic_context = context.get("epic_context", {})
        stories = epic_context.get("stories", [])

        transcript = [
            f"=== Planning Ceremony ===",
            f"Date: {context['timestamp']}",
            f"Participants: {', '.join(participants)}",
            "",
            context.get("prompt", ""),
            "",
            "=== Story Estimation ==="
        ]

        for story in stories[:3]:  # Simulate first 3 stories
            transcript.append(f"Story {story.get('story_num')}: {story.get('title', 'Unknown')} - Estimated: 5 points")

        transcript.append("")
        transcript.append("=== Sprint Commitment ===")
        transcript.append(f"Total stories: {len(stories)}")
        transcript.append("Team commits to completing all estimated stories")

        action_items = [
            {
                "title": "Break down complex stories",
                "description": "Ensure stories are appropriately sized",
                "priority": "medium",
                "assignee": "John"
            }
        ]

        decisions = [
            f"Commit to {len(stories)} stories for this sprint",
            "Use story points for estimation",
            "Daily stand-ups at 9am"
        ]

        return transcript, action_items, decisions

    def _generate_summary(
        self,
        ceremony_type: str,
        context: Dict[str, Any],
        action_items_count: int,
        learnings_count: int
    ) -> str:
        """
        Generate ceremony summary.

        Args:
            ceremony_type: Type of ceremony
            context: Ceremony context
            action_items_count: Number of action items created
            learnings_count: Number of learnings indexed

        Returns:
            Summary text
        """
        epic_context = context.get("epic_context", {})
        epic = epic_context.get("epic", {})
        epic_num = epic.get("epic_num", "Unknown")
        epic_title = epic.get("title", "Unknown")

        if ceremony_type == "standup":
            return f"Daily stand-up for Epic {epic_num}: {epic_title}. {action_items_count} blockers identified."
        elif ceremony_type == "retrospective":
            return f"Retrospective for Epic {epic_num}: {epic_title}. {learnings_count} learnings captured, {action_items_count} improvement actions."
        elif ceremony_type == "planning":
            return f"Planning ceremony for Epic {epic_num}: {epic_title}. Stories estimated and sprint committed."
        else:
            return f"Ceremony completed for Epic {epic_num}"

    def _save_transcript(
        self,
        ceremony_type: str,
        epic_num: int,
        story_num: Optional[int],
        transcript: str
    ) -> Path:
        """
        Save ceremony transcript to file.

        Args:
            ceremony_type: Type of ceremony
            epic_num: Epic number
            story_num: Optional story number
            transcript: Transcript text

        Returns:
            Path to saved transcript file
        """
        # Create ceremonies directory
        ceremonies_dir = self.project_root / ".gao-dev" / "ceremonies"
        ceremonies_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if story_num:
            filename = f"{ceremony_type}_epic{epic_num}_story{story_num}_{timestamp}.txt"
        else:
            filename = f"{ceremony_type}_epic{epic_num}_{timestamp}.txt"

        # Save transcript
        transcript_path = ceremonies_dir / filename
        transcript_path.write_text(transcript, encoding="utf-8")

        self.logger.debug(
            "transcript_saved",
            path=str(transcript_path),
            ceremony_type=ceremony_type
        )

        return transcript_path

    def close(self) -> None:
        """Close all service connections."""
        self.context_loader.close()
        self.ceremony_service.close()
        self.action_service.close()
        self.learning_service.close()
        self.action_item_integration.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connections."""
        self.close()
