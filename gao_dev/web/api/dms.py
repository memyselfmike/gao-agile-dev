"""DM (Direct Message) API endpoints for agent conversations.

Story 39.31: DMs Section - Agent List and Conversation UI
Story 39.32: DM Conversation View and Message Sending
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/dms", tags=["dms"])


# Request/Response Models
class SendMessageRequest(BaseModel):
    """Request body for sending a message to an agent."""

    content: str


# All 8 GAO-Dev agents
AGENTS = [
    "brian",
    "mary",
    "john",
    "winston",
    "sally",
    "bob",
    "amelia",
    "murat",
]


@router.get("")
async def get_dms(request: Request) -> JSONResponse:
    """Get all DM conversations with last message metadata.

    Returns DM conversation summary for all 8 agents including:
    - Last message content (truncated to 50 chars)
    - Last message timestamp
    - Total message count

    Args:
        request: FastAPI request object

    Returns:
        JSON response with conversations array

    Example response:
        {
            "conversations": [
                {
                    "agent": "brian",
                    "lastMessage": "How can I help you today?",
                    "lastMessageAt": "2025-01-16T10:30:00Z",
                    "messageCount": 12
                },
                ...
            ]
        }
    """
    try:
        # Get ChatSession instances from app state
        # Each agent has its own ChatSession created on-demand
        # For now, we'll read from localStorage-equivalent server storage

        # In Epic 30, chat history is stored in ChatSession instances
        # We need to access BrianWebAdapter to get conversation history

        conversations = []

        # Get brian_adapter from app state
        brian_adapter = getattr(request.app.state, "brian_adapter", None)

        # Always include Brian conversation (even if adapter not initialized)
        if brian_adapter:
            # For Brian, get actual history from ChatSession
            try:
                history = brian_adapter.get_conversation_history(max_turns=50)
                if history:
                    last_msg = history[-1]
                    # Convert timestamp to ISO string if it's an int (milliseconds)
                    timestamp = last_msg.get("timestamp")
                    if isinstance(timestamp, int):
                        timestamp = datetime.fromtimestamp(timestamp / 1000).isoformat()
                    elif not timestamp:
                        timestamp = datetime.now().isoformat()

                    conversations.append(
                        {
                            "agent": "brian",
                            "lastMessage": last_msg.get("content", "")[:50],
                            "lastMessageAt": timestamp,
                            "messageCount": len(history),
                        }
                    )
                else:
                    # No messages yet
                    conversations.append(
                        {
                            "agent": "brian",
                            "lastMessage": "No messages yet",
                            "lastMessageAt": datetime.now().isoformat(),
                            "messageCount": 0,
                        }
                    )
            except Exception as e:
                logger.warning("failed_to_get_brian_history", error=str(e))
                conversations.append(
                    {
                        "agent": "brian",
                        "lastMessage": "No messages yet",
                        "lastMessageAt": datetime.now().isoformat(),
                        "messageCount": 0,
                    }
                )
        else:
            # Brian adapter not initialized yet
            conversations.append(
                {
                    "agent": "brian",
                    "lastMessage": "No messages yet",
                    "lastMessageAt": datetime.now().isoformat(),
                    "messageCount": 0,
                }
            )

        # For other agents, return placeholder data
        # In future stories, these will have their own ChatSession instances
        for agent in AGENTS:
            if agent == "brian":
                continue  # Already handled above

            conversations.append(
                {
                    "agent": agent,
                    "lastMessage": "No messages yet",
                    "lastMessageAt": datetime.now().isoformat(),
                    "messageCount": 0,
                }
            )

        # Note: Sorting disabled to avoid type comparison issues
        # TODO: Fix timestamp type consistency and re-enable sorting

        return JSONResponse({"conversations": conversations})

    except Exception as e:
        logger.exception("get_dms_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get DM conversations: {str(e)}"
        )


@router.get("/{agent_id}/history")
async def get_dm_history(
    agent_id: str, request: Request, max_messages: int = 50
) -> JSONResponse:
    """Get conversation history for a specific agent.

    Args:
        agent_id: Agent identifier (brian, mary, john, etc.)
        request: FastAPI request object
        max_messages: Maximum number of messages to return

    Returns:
        JSON response with message history

    Raises:
        HTTPException: If agent not found or history fetch fails
    """
    if agent_id not in AGENTS:
        raise HTTPException(
            status_code=404, detail=f"Agent {agent_id} not found"
        )

    try:
        # For Brian, use BrianWebAdapter
        if agent_id == "brian":
            brian_adapter = getattr(request.app.state, "brian_adapter", None)
            if brian_adapter:
                history = brian_adapter.get_conversation_history(
                    max_turns=max_messages
                )
                return JSONResponse({"messages": history})

        # For other agents, return empty history for now
        # Future: Implement multi-agent ChatSession support
        return JSONResponse({"messages": []})

    except Exception as e:
        logger.exception("get_dm_history_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}",
        )


@router.get("/{agent_id}/messages")
async def get_dm_messages(
    agent_id: str,
    request: Request,
    offset: int = 0,
    limit: int = 50,
) -> JSONResponse:
    """Get paginated messages for a specific agent conversation.

    Story 39.32: Message pagination support

    Args:
        agent_id: Agent identifier (brian, mary, john, etc.)
        request: FastAPI request object
        offset: Number of messages to skip (for pagination)
        limit: Maximum number of messages to return (max 100)

    Returns:
        JSON response with paginated messages

    Raises:
        HTTPException: If agent not found or fetch fails
    """
    if agent_id not in AGENTS:
        raise HTTPException(
            status_code=404, detail=f"Agent {agent_id} not found"
        )

    # Validate pagination parameters
    if offset < 0:
        raise HTTPException(
            status_code=400, detail="Offset must be non-negative"
        )
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400, detail="Limit must be between 1 and 100"
        )

    try:
        # For Brian, use BrianAdapter
        if agent_id == "brian":
            brian_adapter = getattr(request.app.state, "brian_adapter", None)
            if brian_adapter:
                # Get all history first
                all_messages = brian_adapter.get_conversation_history(
                    max_turns=1000  # Get more for pagination
                )

                # Apply pagination
                total = len(all_messages)
                paginated_messages = all_messages[offset : offset + limit]

                return JSONResponse(
                    {
                        "messages": paginated_messages,
                        "total": total,
                        "offset": offset,
                        "limit": limit,
                        "hasMore": offset + limit < total,
                    }
                )

        # For other agents, return empty for now
        return JSONResponse(
            {
                "messages": [],
                "total": 0,
                "offset": 0,
                "limit": limit,
                "hasMore": False,
            }
        )

    except Exception as e:
        logger.exception("get_dm_messages_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}",
        )


@router.post("/{agent_id}/messages")
async def send_dm_message(
    agent_id: str,
    request: Request,
    message_request: SendMessageRequest,
) -> JSONResponse:
    """Send a message to an agent and get response.

    Story 39.32: Message sending with streaming support

    This endpoint initiates the message send. The actual response
    will stream via WebSocket (dm.message.received events).

    Args:
        agent_id: Agent identifier (brian, mary, john, etc.)
        request: FastAPI request object
        message_request: Message content

    Returns:
        JSON response with success status

    Raises:
        HTTPException: If agent not found or send fails
    """
    if agent_id not in AGENTS:
        raise HTTPException(
            status_code=404, detail=f"Agent {agent_id} not found"
        )

    if not message_request.content.strip():
        raise HTTPException(
            status_code=400, detail="Message content cannot be empty"
        )

    try:
        # For Brian, use BrianAdapter
        if agent_id == "brian":
            brian_adapter = getattr(request.app.state, "brian_adapter", None)
            if not brian_adapter:
                raise HTTPException(
                    status_code=503,
                    detail="Brian adapter not initialized. Please refresh the page.",
                )

            # Get client_id from session if available
            client_id = getattr(request.state, "client_id", None)

            # Send message (response will stream via WebSocket)
            # We consume the async generator to trigger streaming
            response_chunks = []
            async for chunk in brian_adapter.send_message(
                message_request.content, client_id=client_id
            ):
                response_chunks.append(chunk)

            # Return success (frontend will receive response via WebSocket)
            return JSONResponse(
                {
                    "success": True,
                    "messageId": None,  # Could add message ID tracking later
                }
            )

        # For other agents, not yet implemented
        raise HTTPException(
            status_code=501,
            detail=f"Agent {agent_id} messaging not yet implemented",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("send_dm_message_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}",
        )
