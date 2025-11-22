"""Brian Web Adapter - Translates ChatSession events to WebSocket events.

Integrates Epic 30 ChatSession/ConversationalBrian with web interface.
NO duplication - this is a thin translation layer only.

Epic: 39.3 - Core Observability
Story: 39.7 - Brian Chat Component
"""

from typing import AsyncIterator, Optional, Any, Dict
import structlog

from gao_dev.orchestrator.chat_session import ChatSession
from gao_dev.web.events import EventType
from gao_dev.web.event_bus import WebEventBus

logger = structlog.get_logger(__name__)


class BrianWebAdapter:
    """
    Adapter between ChatSession and WebSocket event bus.

    Translates ChatSession conversation events into WebSocket events:
    - chat.message_sent: User sent message
    - chat.message_received: Brian responded
    - chat.thinking_started: Claude is reasoning
    - chat.thinking_finished: Reasoning complete
    - chat.streaming_chunk: Partial response (streaming)

    This is a thin wrapper that reuses Epic 30 infrastructure.
    """

    def __init__(
        self,
        chat_session: ChatSession,
        event_bus: WebEventBus
    ):
        """
        Initialize Brian web adapter.

        Args:
            chat_session: Epic 30 ChatSession instance
            event_bus: WebSocket event bus for publishing events
        """
        self.chat_session = chat_session
        self.event_bus = event_bus
        self.logger = logger.bind(component="brian_web_adapter")

    async def send_message(
        self,
        message: str,
        client_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Send message to Brian and stream response.

        Publishes events:
        - chat.message_sent: When user message is added
        - chat.streaming_chunk: For each response chunk
        - chat.message_received: When response is complete

        Args:
            message: User message
            client_id: Optional WebSocket client ID

        Yields:
            Response chunks from Brian
        """
        self.logger.info(
            "sending_message_to_brian",
            message_length=len(message),
            client_id=client_id
        )

        # Publish user message event
        await self.event_bus.publish(
            EventType.CHAT_MESSAGE_SENT,
            data={
                "role": "user",
                "content": message,
                "agentName": None
            },
            metadata={"client_id": client_id} if client_id else None
        )

        # Stream response from ChatSession
        response_chunks: list[str] = []

        try:
            async for chunk in self.chat_session.handle_input(message):
                response_chunks.append(chunk)

                # Publish streaming chunk event
                await self.event_bus.publish(
                    EventType.CHAT_STREAMING_CHUNK,
                    data={
                        "chunk": chunk,
                        "role": "agent",
                        "agentName": "Brian"
                    },
                    metadata={"client_id": client_id} if client_id else None
                )

                yield chunk

            # Publish complete message event
            complete_response = "".join(response_chunks)
            await self.event_bus.publish(
                EventType.CHAT_MESSAGE_RECEIVED,
                data={
                    "role": "agent",
                    "content": complete_response,
                    "agentName": "Brian"
                },
                metadata={"client_id": client_id} if client_id else None
            )

            self.logger.info(
                "message_response_complete",
                response_length=len(complete_response),
                chunks=len(response_chunks)
            )

        except Exception as e:
            self.logger.exception("message_handling_failed", error=str(e))

            # Publish error event
            await self.event_bus.publish(
                EventType.SYSTEM_ERROR,
                data={
                    "error": str(e),
                    "context": "brian_chat"
                },
                metadata={"client_id": client_id} if client_id else None
            )

            raise

    def get_conversation_history(self, max_turns: int = 50) -> list[Dict[str, Any]]:
        """
        Get recent conversation history.

        Args:
            max_turns: Maximum number of turns to return

        Returns:
            List of conversation turns as dictionaries
        """
        recent_turns = self.chat_session.get_recent_history(max_turns)

        return [
            {
                "id": str(id(turn)),  # Generate unique ID
                "role": turn.role,
                "content": turn.content,
                "timestamp": int(turn.timestamp.timestamp() * 1000),  # Convert to milliseconds
                "agentName": "Brian" if turn.role == "brian" else None
            }
            for turn in recent_turns
        ]

    def get_session_context(self) -> Dict[str, Any]:
        """
        Get current session context.

        Returns:
            Dictionary with session state (epic, story, etc.)
        """
        context = self.chat_session.context

        return {
            "projectRoot": str(context.project_root),
            "currentEpic": context.current_epic,
            "currentStory": context.current_story,
            "pendingConfirmation": context.pending_confirmation is not None,
            "contextSummary": self.chat_session.get_context_summary()
        }
