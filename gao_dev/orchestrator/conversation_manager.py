"""Conversation Manager - Multi-agent dialogue coordination.

This service manages turn-based conversations between multiple agents,
handling context injection, history tracking, and conversation flow.

Epic: 26 - Multi-Agent Ceremonies Architecture
Story: 26.5 - Implement ConversationManager

Design Pattern: State Machine + Observer
Dependencies: FastContextLoader, structlog

Example:
    ```python
    manager = ConversationManager(
        context_loader=FastContextLoader(db_path),
        max_turns=10
    )

    # Start conversation
    manager.start_conversation(
        participants=["Amelia", "Bob", "John"],
        topic="Epic 1 Planning",
        context={"epic_num": 1}
    )

    # Add turn
    manager.add_turn(
        agent="Amelia",
        message="I can handle stories 1.1 and 1.2"
    )

    # Get conversation history
    history = manager.get_history()
    ```
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import structlog

from ..core.services.fast_context_loader import FastContextLoader

logger = structlog.get_logger()


@dataclass
class ConversationTurn:
    """
    Represents a single turn in a conversation.

    Attributes:
        turn_num: Sequential turn number
        agent: Agent name
        message: Message content
        timestamp: When turn was added
        metadata: Additional turn metadata
    """
    turn_num: int
    agent: str
    message: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ConversationManager:
    """
    Manages multi-agent conversations.

    Provides turn-based conversation flow with context injection,
    history tracking, and agent participation management.

    Attributes:
        context_loader: FastContextLoader for agent context
        max_turns: Maximum number of turns allowed
        conversation_id: Unique conversation identifier
        participants: List of participant agent names
        turns: List of conversation turns
        topic: Conversation topic
        context: Conversation context
        is_active: Whether conversation is active
    """

    def __init__(
        self,
        context_loader: FastContextLoader,
        max_turns: int = 50
    ):
        """
        Initialize conversation manager.

        Args:
            context_loader: FastContextLoader for context injection
            max_turns: Maximum conversation turns (default: 50)
        """
        self.context_loader = context_loader
        self.max_turns = max_turns

        # Conversation state
        self.conversation_id: Optional[str] = None
        self.participants: List[str] = []
        self.turns: List[ConversationTurn] = []
        self.topic: str = ""
        self.context: Dict[str, Any] = {}
        self.is_active: bool = False

        self.logger = logger.bind(service="conversation_manager")

    def start_conversation(
        self,
        participants: List[str],
        topic: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start new conversation.

        Args:
            participants: List of agent names to participate
            topic: Conversation topic
            context: Optional initial context

        Returns:
            Conversation ID

        Raises:
            RuntimeError: If conversation already active

        Example:
            ```python
            conv_id = manager.start_conversation(
                participants=["Amelia", "Bob"],
                topic="Sprint Planning",
                context={"epic_num": 1}
            )
            ```
        """
        if self.is_active:
            raise RuntimeError("Conversation already active. End current conversation first.")

        # Generate conversation ID
        self.conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.participants = participants
        self.topic = topic
        self.context = context or {}
        self.turns = []
        self.is_active = True

        self.logger.info(
            "conversation_started",
            conversation_id=self.conversation_id,
            participants=participants,
            topic=topic
        )

        return self.conversation_id

    def add_turn(
        self,
        agent: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """
        Add turn to conversation.

        Args:
            agent: Agent name
            message: Message content
            metadata: Optional turn metadata

        Returns:
            Created ConversationTurn

        Raises:
            RuntimeError: If conversation not active
            ValueError: If agent not in participants
            RuntimeError: If max turns exceeded

        Example:
            ```python
            turn = manager.add_turn(
                agent="Amelia",
                message="I'll work on story 1.1",
                metadata={"story_num": 1}
            )
            ```
        """
        if not self.is_active:
            raise RuntimeError("No active conversation. Call start_conversation() first.")

        if agent not in self.participants:
            raise ValueError(f"Agent '{agent}' not in participants: {self.participants}")

        if len(self.turns) >= self.max_turns:
            raise RuntimeError(f"Maximum turns ({self.max_turns}) exceeded")

        # Create turn
        turn = ConversationTurn(
            turn_num=len(self.turns) + 1,
            agent=agent,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )

        self.turns.append(turn)

        self.logger.debug(
            "turn_added",
            conversation_id=self.conversation_id,
            turn_num=turn.turn_num,
            agent=agent
        )

        return turn

    def end_conversation(self) -> Dict[str, Any]:
        """
        End active conversation.

        Returns:
            Dictionary with conversation summary:
            - conversation_id: Conversation ID
            - topic: Topic
            - participants: List of participants
            - turn_count: Number of turns
            - started_at: First turn timestamp
            - ended_at: Last turn timestamp
            - duration_seconds: Conversation duration

        Raises:
            RuntimeError: If no active conversation

        Example:
            ```python
            summary = manager.end_conversation()
            print(f"Conversation had {summary['turn_count']} turns")
            ```
        """
        if not self.is_active:
            raise RuntimeError("No active conversation to end")

        # Calculate duration
        if self.turns:
            started_at = self.turns[0].timestamp
            ended_at = self.turns[-1].timestamp
            start_time = datetime.fromisoformat(started_at)
            end_time = datetime.fromisoformat(ended_at)
            duration = (end_time - start_time).total_seconds()
        else:
            started_at = None
            ended_at = None
            duration = 0.0

        summary = {
            "conversation_id": self.conversation_id,
            "topic": self.topic,
            "participants": self.participants,
            "turn_count": len(self.turns),
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_seconds": duration
        }

        self.logger.info(
            "conversation_ended",
            conversation_id=self.conversation_id,
            turn_count=len(self.turns),
            duration_seconds=duration
        )

        # Reset state
        self.is_active = False

        return summary

    def get_history(
        self,
        agent: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ConversationTurn]:
        """
        Get conversation history.

        Args:
            agent: Optional filter by agent
            limit: Optional limit number of turns

        Returns:
            List of ConversationTurn objects

        Example:
            ```python
            # Get all turns
            all_turns = manager.get_history()

            # Get Amelia's turns only
            amelia_turns = manager.get_history(agent="Amelia")

            # Get last 5 turns
            recent = manager.get_history(limit=5)
            ```
        """
        turns = self.turns

        # Filter by agent
        if agent:
            turns = [t for t in turns if t.agent == agent]

        # Apply limit
        if limit:
            turns = turns[-limit:]

        return turns

    def get_context_for_agent(
        self,
        agent: str,
        epic_num: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get context tailored for specific agent.

        Combines conversation context with agent-specific context
        from FastContextLoader.

        Args:
            agent: Agent name
            epic_num: Optional epic number for context loading

        Returns:
            Dictionary with agent context:
            - conversation: Conversation metadata
            - history: Recent conversation turns
            - agent_context: Agent-specific context from FastContextLoader
            - epic_context: Epic context (if epic_num provided)

        Example:
            ```python
            context = manager.get_context_for_agent(
                agent="Amelia",
                epic_num=1
            )
            print(f"Agent role: {context['agent_context']['agent_role']}")
            ```
        """
        # Build conversation context
        conv_context = {
            "conversation_id": self.conversation_id,
            "topic": self.topic,
            "participants": self.participants,
            "turn_count": len(self.turns)
        }

        # Get recent history (last 5 turns)
        recent_history = [t.to_dict() for t in self.get_history(limit=5)]

        # Build result
        result = {
            "conversation": conv_context,
            "history": recent_history,
            "context": self.context
        }

        # Add agent-specific context from FastContextLoader
        if epic_num:
            try:
                # Infer agent role from name
                agent_role = self._infer_agent_role(agent)

                # Get agent context
                agent_context = self.context_loader.get_agent_context(
                    agent_role=agent_role,
                    epic_num=epic_num
                )

                result["agent_context"] = agent_context

                # Also get epic context
                epic_context = self.context_loader.get_epic_context(
                    epic_num=epic_num,
                    include_stories=True,
                    include_summary=True
                )

                result["epic_context"] = epic_context

            except Exception as e:
                self.logger.warning(
                    "failed_to_load_agent_context",
                    agent=agent,
                    error=str(e)
                )

        return result

    def refresh_context(self, epic_num: int) -> None:
        """
        Refresh conversation context with latest epic data.

        Uses FastContextLoader to reload epic context during conversation.

        Args:
            epic_num: Epic number to refresh context for

        Example:
            ```python
            # Start conversation
            manager.start_conversation(...)

            # After some turns, refresh context
            manager.refresh_context(epic_num=1)
            ```
        """
        if not self.is_active:
            raise RuntimeError("No active conversation. Call start_conversation() first.")

        # Load fresh epic context
        epic_context = self.context_loader.get_epic_context(
            epic_num=epic_num,
            include_stories=True,
            include_summary=True
        )

        # Update conversation context
        self.context["epic_context"] = epic_context
        self.context["last_refreshed"] = datetime.now().isoformat()

        self.logger.debug(
            "context_refreshed",
            conversation_id=self.conversation_id,
            epic_num=epic_num
        )

    def export_transcript(self) -> str:
        """
        Export conversation as formatted transcript.

        Returns:
            Formatted transcript string

        Example:
            ```python
            transcript = manager.export_transcript()
            print(transcript)
            ```
        """
        lines = [
            f"=== Conversation Transcript ===",
            f"ID: {self.conversation_id}",
            f"Topic: {self.topic}",
            f"Participants: {', '.join(self.participants)}",
            f"Turns: {len(self.turns)}",
            "",
            "=== Conversation ==="
        ]

        for turn in self.turns:
            lines.append(f"\n[Turn {turn.turn_num}] {turn.agent} ({turn.timestamp}):")
            lines.append(turn.message)

        return "\n".join(lines)

    def save_transcript(self, file_path: Path) -> None:
        """
        Save conversation transcript to file.

        Args:
            file_path: Path to save transcript

        Example:
            ```python
            manager.save_transcript(Path("transcripts/conv_001.txt"))
            ```
        """
        transcript = self.export_transcript()

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write transcript
        file_path.write_text(transcript, encoding="utf-8")

        self.logger.info(
            "transcript_saved",
            conversation_id=self.conversation_id,
            path=str(file_path)
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _infer_agent_role(self, agent: str) -> str:
        """
        Infer agent role from agent name.

        Args:
            agent: Agent name

        Returns:
            Agent role string
        """
        # Simple name-to-role mapping
        role_map = {
            "amelia": "developer",
            "bob": "scrum_master",
            "john": "product_manager",
            "winston": "architect",
            "sally": "ux_designer",
            "murat": "test_engineer",
            "mary": "engineering_manager",
            "brian": "workflow_coordinator"
        }

        agent_lower = agent.lower()
        return role_map.get(agent_lower, "developer")

    def __repr__(self) -> str:
        """String representation."""
        if self.is_active:
            return f"<ConversationManager active={self.is_active} id={self.conversation_id} turns={len(self.turns)}>"
        else:
            return f"<ConversationManager active={self.is_active}>"
