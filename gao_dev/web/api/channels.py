"""Channel API endpoints for ceremony channels.

Story 39.33: Channels Section - Ceremony Channels UI

Provides endpoints for listing ceremony channels, fetching channel messages,
and sending messages to ceremony channels.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])


# Request/Response Models
class SendChannelMessageRequest(BaseModel):
    """Request body for sending a message to a channel."""

    content: str


# TODO (Epic 28 Integration): Replace mock data with CeremonyOrchestrator integration
# For MVP, we'll use mock data to demonstrate the UI
MOCK_CHANNELS = [
    {
        "id": "sprint-planning-epic-5",
        "name": "#sprint-planning-epic-5",
        "ceremonyType": "sprint-planning",
        "status": "active",
        "participants": ["brian", "bob", "john", "winston"],
        "lastMessageAt": "2025-01-16T10:45:00Z",
        "lastMessage": "Let's start planning Sprint 5...",
        "messageCount": 12,
    },
    {
        "id": "retrospective-epic-4",
        "name": "#retrospective-epic-4",
        "ceremonyType": "retrospective",
        "status": "active",
        "participants": ["brian", "bob", "amelia", "murat"],
        "lastMessageAt": "2025-01-16T09:30:00Z",
        "lastMessage": "What went well in Epic 4?",
        "messageCount": 8,
    },
    {
        "id": "daily-standup-2025-01-16",
        "name": "#daily-standup-2025-01-16",
        "ceremonyType": "daily-standup",
        "status": "active",
        "participants": ["brian", "bob", "amelia", "john", "winston"],
        "lastMessageAt": "2025-01-16T09:00:00Z",
        "lastMessage": "Good morning team! What's on your plate today?",
        "messageCount": 15,
    },
    {
        "id": "sprint-planning-epic-3",
        "name": "#sprint-planning-epic-3",
        "ceremonyType": "sprint-planning",
        "status": "archived",
        "participants": ["brian", "bob", "john"],
        "lastMessageAt": "2025-01-10T14:00:00Z",
        "lastMessage": "Sprint planning completed for Epic 3",
        "messageCount": 18,
    },
]

MOCK_MESSAGES = {
    "sprint-planning-epic-5": [
        {
            "id": "msg-1",
            "role": "agent",
            "agentName": "Brian",
            "agentId": "brian",
            "content": "Let's start planning Sprint 5. We have 3 stories ready to implement.",
            "timestamp": datetime(2025, 1, 16, 10, 30).timestamp() * 1000,
        },
        {
            "id": "msg-2",
            "role": "agent",
            "agentName": "Bob",
            "agentId": "bob",
            "content": "I've reviewed the backlog. Story 5.1, 5.2, and 5.3 are ready. Total: 13 story points.",
            "timestamp": datetime(2025, 1, 16, 10, 32).timestamp() * 1000,
        },
        {
            "id": "msg-3",
            "role": "agent",
            "agentName": "John",
            "agentId": "john",
            "content": "Story 5.1 is critical for the MVP. We should prioritize that.",
            "timestamp": datetime(2025, 1, 16, 10, 35).timestamp() * 1000,
        },
        {
            "id": "msg-4",
            "role": "agent",
            "agentName": "Winston",
            "agentId": "winston",
            "content": "Agreed. Story 5.1 requires database migration, so I'll prepare the schema changes.",
            "timestamp": datetime(2025, 1, 16, 10, 40).timestamp() * 1000,
        },
        {
            "id": "msg-5",
            "role": "agent",
            "agentName": "Brian",
            "agentId": "brian",
            "content": "Perfect. Let's commit to Story 5.1 and 5.2 for this sprint. Amelia, can you handle implementation?",
            "timestamp": datetime(2025, 1, 16, 10, 45).timestamp() * 1000,
        },
    ],
    "retrospective-epic-4": [
        {
            "id": "msg-1",
            "role": "agent",
            "agentName": "Brian",
            "agentId": "brian",
            "content": "Time for our Epic 4 retrospective. What went well?",
            "timestamp": datetime(2025, 1, 16, 9, 30).timestamp() * 1000,
        },
        {
            "id": "msg-2",
            "role": "agent",
            "agentName": "Bob",
            "agentId": "bob",
            "content": "Great collaboration between Winston and Amelia on the architecture implementation.",
            "timestamp": datetime(2025, 1, 16, 9, 32).timestamp() * 1000,
        },
        {
            "id": "msg-3",
            "role": "agent",
            "agentName": "Amelia",
            "agentId": "amelia",
            "content": "Test coverage was excellent thanks to Murat's early involvement.",
            "timestamp": datetime(2025, 1, 16, 9, 35).timestamp() * 1000,
        },
        {
            "id": "msg-4",
            "role": "agent",
            "agentName": "Murat",
            "agentId": "murat",
            "content": "We should continue TDD approach. It caught 5 bugs before code review.",
            "timestamp": datetime(2025, 1, 16, 9, 37).timestamp() * 1000,
        },
    ],
    "daily-standup-2025-01-16": [
        {
            "id": "msg-1",
            "role": "agent",
            "agentName": "Brian",
            "agentId": "brian",
            "content": "Good morning team! What's on your plate today?",
            "timestamp": datetime(2025, 1, 16, 9, 0).timestamp() * 1000,
        },
        {
            "id": "msg-2",
            "role": "agent",
            "agentName": "Amelia",
            "agentId": "amelia",
            "content": "Working on Story 4.5 implementation. Should be done by EOD.",
            "timestamp": datetime(2025, 1, 16, 9, 1).timestamp() * 1000,
        },
        {
            "id": "msg-3",
            "role": "agent",
            "agentName": "Winston",
            "agentId": "winston",
            "content": "Finishing architecture doc for Epic 5. Will share for review this morning.",
            "timestamp": datetime(2025, 1, 16, 9, 2).timestamp() * 1000,
        },
        {
            "id": "msg-4",
            "role": "agent",
            "agentName": "John",
            "agentId": "john",
            "content": "Reviewing Epic 6 PRD with Mary. Need clarification on requirements.",
            "timestamp": datetime(2025, 1, 16, 9, 3).timestamp() * 1000,
        },
        {
            "id": "msg-5",
            "role": "agent",
            "agentName": "Bob",
            "agentId": "bob",
            "content": "Updating sprint board. Story 4.3 moved to done.",
            "timestamp": datetime(2025, 1, 16, 9, 4).timestamp() * 1000,
        },
    ],
}


@router.get("")
async def get_channels(request: Request) -> JSONResponse:
    """Get all ceremony channels.

    Returns list of all ceremony channels with metadata including:
    - Channel ID, name, ceremony type
    - Status (active or archived)
    - Participant agents
    - Last message metadata

    Args:
        request: FastAPI request object

    Returns:
        JSON response with channels array

    Example response:
        {
            "channels": [
                {
                    "id": "sprint-planning-epic-5",
                    "name": "#sprint-planning-epic-5",
                    "ceremonyType": "sprint-planning",
                    "status": "active",
                    "participants": ["brian", "bob", "john", "winston"],
                    "lastMessageAt": "2025-01-16T10:45:00Z",
                    "lastMessage": "Let's start planning...",
                    "messageCount": 12
                }
            ]
        }
    """
    try:
        # TODO (Epic 28 Integration): Query CeremonyOrchestrator for real channels
        # For now, return mock data
        logger.info("get_channels_called")

        # Sort channels: active first, then by last message timestamp
        sorted_channels = sorted(
            MOCK_CHANNELS,
            key=lambda c: (
                c["status"] != "active",  # Active channels first
                -datetime.fromisoformat(c["lastMessageAt"].replace("Z", "+00:00")).timestamp(),
            ),
        )

        return JSONResponse({"channels": sorted_channels})

    except Exception as e:
        logger.exception("get_channels_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get channels: {str(e)}")


@router.get("/{channel_id}/messages")
async def get_channel_messages(
    channel_id: str,
    request: Request,
    offset: int = 0,
    limit: int = 50,
) -> JSONResponse:
    """Get messages for a specific ceremony channel.

    Supports pagination for loading message history.

    Args:
        channel_id: Channel identifier (e.g., "sprint-planning-epic-5")
        request: FastAPI request object
        offset: Number of messages to skip (for pagination)
        limit: Maximum number of messages to return (max 100)

    Returns:
        JSON response with paginated messages

    Raises:
        HTTPException: If channel not found or fetch fails

    Example response:
        {
            "messages": [
                {
                    "id": "msg-1",
                    "role": "agent",
                    "agentName": "Brian",
                    "agentId": "brian",
                    "content": "Let's start planning...",
                    "timestamp": 1705401000000
                }
            ],
            "total": 12,
            "offset": 0,
            "limit": 50,
            "hasMore": false
        }
    """
    # Validate channel exists
    channel = next((c for c in MOCK_CHANNELS if c["id"] == channel_id), None)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    # Validate pagination parameters
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    try:
        # TODO (Epic 28 Integration): Query CeremonyOrchestrator for real messages
        # For now, return mock data
        logger.info("get_channel_messages_called", channel_id=channel_id, offset=offset, limit=limit)

        messages = MOCK_MESSAGES.get(channel_id, [])
        total = len(messages)

        # Apply pagination
        paginated_messages = messages[offset : offset + limit]

        return JSONResponse(
            {
                "messages": paginated_messages,
                "total": total,
                "offset": offset,
                "limit": limit,
                "hasMore": offset + limit < total,
            }
        )

    except Exception as e:
        logger.exception("get_channel_messages_failed", channel_id=channel_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/{channel_id}/archive")
async def archive_channel(
    channel_id: str,
    request: Request,
) -> JSONResponse:
    """Archive a ceremony channel (admin only).

    Marks channel as read-only. No new messages can be sent after archiving.

    Args:
        channel_id: Channel identifier
        request: FastAPI request object

    Returns:
        JSON response with success status

    Raises:
        HTTPException: If channel not found, already archived, or archive fails

    Example response:
        {
            "success": true,
            "channelId": "sprint-planning-epic-5",
            "status": "archived",
            "timestamp": "2025-01-16T15:00:00Z"
        }
    """
    # Validate channel exists
    channel = next((c for c in MOCK_CHANNELS if c["id"] == channel_id), None)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    # Check if already archived
    if channel["status"] == "archived":
        raise HTTPException(
            status_code=400, detail="Channel is already archived"
        )

    try:
        # TODO (Epic 28 Integration): Archive via CeremonyOrchestrator
        # For now, update mock data
        logger.info("archive_channel_called", channel_id=channel_id)

        # Update channel status in mock data
        channel["status"] = "archived"
        timestamp = datetime.now().isoformat()

        # TODO: Publish WebSocket event for real-time updates
        # event_bus.publish({
        #     "type": "channel.archived",
        #     "payload": {
        #         "channelId": channel_id,
        #         "status": "archived",
        #         "timestamp": timestamp
        #     }
        # })

        return JSONResponse(
            {
                "success": True,
                "channelId": channel_id,
                "status": "archived",
                "timestamp": timestamp,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("archive_channel_failed", channel_id=channel_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to archive channel: {str(e)}")


@router.get("/{channel_id}/export")
async def export_channel_transcript(
    channel_id: str,
    request: Request,
) -> str:
    """Export channel transcript to Markdown file.

    Generates downloadable Markdown file with channel messages formatted as:
    # {ceremony-type} - Epic {epic_num}
    **Date**: {date}
    **Participants**: {agents}

    ---

    **AgentName** (HH:MM AM/PM):
    Message content

    Args:
        channel_id: Channel identifier
        request: FastAPI request object

    Returns:
        Markdown content with Content-Disposition header for download

    Raises:
        HTTPException: If channel not found or export fails

    Example filename: sprint-planning-epic-5-2025-01-16.md
    """
    from fastapi.responses import PlainTextResponse

    # Validate channel exists
    channel = next((c for c in MOCK_CHANNELS if c["id"] == channel_id), None)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    try:
        # TODO (Epic 28 Integration): Query CeremonyOrchestrator for real messages
        # For now, use mock data
        logger.info("export_channel_transcript_called", channel_id=channel_id)

        messages = MOCK_MESSAGES.get(channel_id, [])

        # Extract ceremony info
        ceremony_type = channel["ceremonyType"].replace("-", " ").title()
        channel_name = channel["name"].replace("#", "")

        # Extract epic number from channel name (e.g., "sprint-planning-epic-5")
        epic_num = "N/A"
        if "epic-" in channel_name:
            epic_num = channel_name.split("epic-")[1].split("-")[0]

        # Get date from last message
        last_message_date = datetime.fromisoformat(
            channel["lastMessageAt"].replace("Z", "+00:00")
        )
        date_str = last_message_date.strftime("%Y-%m-%d")

        # Get participants
        participants = ", ".join([p.title() for p in channel["participants"]])

        # Build Markdown content
        markdown_lines = [
            f"# {ceremony_type} - Epic {epic_num}",
            f"**Date**: {date_str}",
            f"**Participants**: {participants}",
            "",
            "---",
            "",
        ]

        # Add messages
        for message in messages:
            msg_timestamp = datetime.fromtimestamp(message["timestamp"] / 1000)
            # Use %I:%M %p format (works on all platforms, including Windows)
            time_str = msg_timestamp.strftime("%I:%M %p")

            agent_name = message.get("agentName", "System")

            markdown_lines.append(f"**{agent_name}** ({time_str}):")
            markdown_lines.append(message["content"])
            markdown_lines.append("")

        markdown_content = "\n".join(markdown_lines)

        # Generate filename
        filename = f"{channel['ceremonyType']}-epic-{epic_num}-{date_str}.md"

        # Return as downloadable file
        return PlainTextResponse(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("export_channel_transcript_failed", channel_id=channel_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export transcript: {str(e)}")


@router.post("/{channel_id}/messages")
async def send_channel_message(
    channel_id: str,
    request: Request,
    message_request: SendChannelMessageRequest,
) -> JSONResponse:
    """Send a message to a ceremony channel.

    Allows user to participate in ceremony by sending messages to the channel.
    All participants receive the message via WebSocket.

    Args:
        channel_id: Channel identifier
        request: FastAPI request object
        message_request: Message content

    Returns:
        JSON response with success status

    Raises:
        HTTPException: If channel not found, archived, or send fails

    Example response:
        {
            "success": true,
            "messageId": "msg-123",
            "timestamp": "2025-01-16T10:50:00Z"
        }
    """
    # Validate channel exists
    channel = next((c for c in MOCK_CHANNELS if c["id"] == channel_id), None)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    # Check if channel is archived (read-only)
    if channel["status"] == "archived":
        raise HTTPException(
            status_code=403, detail="Cannot send message to archived channel. Channel is read-only."
        )

    # Validate message content
    if not message_request.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    try:
        # TODO (Epic 28 Integration): Send message via CeremonyOrchestrator
        # For now, just log and return success
        logger.info(
            "send_channel_message_called",
            channel_id=channel_id,
            message_length=len(message_request.content),
        )

        # Generate message ID and timestamp
        message_id = f"msg-{datetime.now().timestamp()}"
        timestamp = datetime.now().isoformat()

        # TODO: Publish WebSocket event for real-time updates
        # event_bus.publish({
        #     "type": "channel.message",
        #     "payload": {
        #         "channelId": channel_id,
        #         "messageId": message_id,
        #         "role": "user",
        #         "content": message_request.content,
        #         "timestamp": timestamp
        #     }
        # })

        return JSONResponse(
            {"success": True, "messageId": message_id, "timestamp": timestamp}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("send_channel_message_failed", channel_id=channel_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
