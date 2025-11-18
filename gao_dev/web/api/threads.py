"""Threads API endpoints for message threading.

Story 39.34: Message Threading Infrastructure

Provides endpoints for creating threads, fetching thread messages,
and posting replies in threads.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/threads", tags=["threads"])


# Request/Response Models
class CreateThreadRequest(BaseModel):
    """Request body for creating a thread."""

    parentMessageId: str
    conversationId: str
    conversationType: str  # "dm" | "channel"


class ThreadReplyRequest(BaseModel):
    """Request body for replying in a thread."""

    content: str


# Helper functions
def _get_db_connection(project_root: Path) -> sqlite3.Connection:
    """Get database connection.

    Args:
        project_root: Project root directory

    Returns:
        SQLite connection

    Raises:
        HTTPException: If database not found
    """
    db_path = project_root / ".gao-dev" / "documents.db"
    if not db_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Project not initialized."
        )

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_or_create_message(conn: sqlite3.Connection, message_id: str) -> Optional[dict]:
    """Get message or create placeholder if not exists.

    Args:
        conn: Database connection
        message_id: Message ID

    Returns:
        Message dict or None if creation failed
    """
    cursor = conn.execute(
        "SELECT * FROM messages WHERE id = ?",
        (message_id,)
    )
    row = cursor.fetchone()

    if row:
        return dict(row)

    # Message doesn't exist yet - this is OK for now
    # The frontend will sync the message later
    logger.warning(
        "message_not_found_creating_placeholder",
        message_id=message_id
    )
    return None


# API Endpoints
@router.post("")
async def create_thread(
    request: Request,
    body: CreateThreadRequest
) -> JSONResponse:
    """Create a new thread from a parent message.

    Args:
        request: FastAPI request object
        body: Request body with parent message ID and conversation info

    Returns:
        JSON response with thread ID

    Raises:
        HTTPException: If thread creation fails or parent message not found

    Example request:
        POST /api/threads
        {
            "parentMessageId": "msg-123",
            "conversationId": "brian",
            "conversationType": "dm"
        }

    Example response:
        {
            "threadId": "thread-456",
            "parentMessageId": "msg-123",
            "conversationId": "brian",
            "conversationType": "dm",
            "createdAt": "2025-01-17T10:30:00Z"
        }
    """
    # Validate conversation type
    if body.conversationType not in ["dm", "channel"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid conversation type: {body.conversationType}. Must be 'dm' or 'channel'."
        )

    try:
        project_root = request.app.state.project_root
        conn = _get_db_connection(project_root)

        try:
            # Check if thread already exists for this parent message
            cursor = conn.execute(
                "SELECT id, created_at FROM threads WHERE parent_message_id = ?",
                (body.parentMessageId,)
            )
            existing_thread = cursor.fetchone()

            if existing_thread:
                # Thread already exists, return it WITHOUT publishing event
                logger.info(
                    "thread_already_exists",
                    thread_id=existing_thread["id"],
                    parent_message_id=body.parentMessageId
                )
                return JSONResponse({
                    "threadId": existing_thread["id"],
                    "parentMessageId": body.parentMessageId,
                    "conversationId": body.conversationId,
                    "conversationType": body.conversationType,
                    "createdAt": existing_thread["created_at"]
                })

            # Create new thread
            cursor = conn.execute(
                """
                INSERT INTO threads (parent_message_id, conversation_id, conversation_type)
                VALUES (?, ?, ?)
                """,
                (body.parentMessageId, body.conversationId, body.conversationType)
            )
            thread_id = cursor.lastrowid

            # Get created thread
            cursor = conn.execute(
                "SELECT id, created_at FROM threads WHERE id = ?",
                (thread_id,)
            )
            thread = cursor.fetchone()

            conn.commit()

            logger.info(
                "thread_created",
                thread_id=thread_id,
                parent_message_id=body.parentMessageId,
                conversation_id=body.conversationId
            )

            # Publish WebSocket event
            try:
                await request.app.state.event_bus.publish({
                    "type": "thread.created",
                    "payload": {
                        "threadId": thread_id,
                        "parentMessageId": body.parentMessageId,
                        "conversationId": body.conversationId,
                        "conversationType": body.conversationType,
                        "timestamp": datetime.now().isoformat()
                    }
                })
            except Exception as ws_error:
                # Non-fatal: WebSocket broadcast failed
                logger.warning(
                    "websocket_broadcast_failed",
                    error=str(ws_error),
                    thread_id=thread_id
                )

            return JSONResponse({
                "threadId": thread_id,
                "parentMessageId": body.parentMessageId,
                "conversationId": body.conversationId,
                "conversationType": body.conversationType,
                "createdAt": thread["created_at"]
            })

        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create_thread_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create thread: {str(e)}"
        )


@router.get("/{thread_id}")
async def get_thread(
    thread_id: int,
    request: Request
) -> JSONResponse:
    """Get thread with parent message and replies.

    Args:
        thread_id: Thread ID
        request: FastAPI request object

    Returns:
        JSON response with parent message and replies

    Raises:
        HTTPException: If thread not found or fetch fails

    Example response:
        {
            "threadId": 456,
            "parentMessage": {
                "id": "msg-123",
                "content": "Parent message",
                "role": "agent",
                "agentName": "Brian",
                "createdAt": "2025-01-17T10:00:00Z",
                "threadCount": 5
            },
            "replies": [
                {
                    "id": "msg-124",
                    "content": "Reply 1",
                    "role": "user",
                    "createdAt": "2025-01-17T10:05:00Z"
                },
                {
                    "id": "msg-125",
                    "content": "Reply 2",
                    "role": "agent",
                    "agentName": "Brian",
                    "createdAt": "2025-01-17T10:10:00Z"
                }
            ],
            "conversationId": "brian",
            "conversationType": "dm",
            "replyCount": 2
        }
    """
    try:
        project_root = request.app.state.project_root
        conn = _get_db_connection(project_root)

        try:
            # Get thread
            cursor = conn.execute(
                """
                SELECT id, parent_message_id, conversation_id, conversation_type,
                       reply_count, created_at, updated_at
                FROM threads
                WHERE id = ?
                """,
                (thread_id,)
            )
            thread = cursor.fetchone()

            if not thread:
                raise HTTPException(
                    status_code=404,
                    detail=f"Thread {thread_id} not found"
                )

            # Get parent message
            cursor = conn.execute(
                """
                SELECT id, conversation_id, conversation_type, content, role,
                       agent_id, agent_name, thread_count, created_at, updated_at
                FROM messages
                WHERE id = ?
                """,
                (thread["parent_message_id"],)
            )
            parent_message_row = cursor.fetchone()

            parent_message = None
            if parent_message_row:
                parent_message = {
                    "id": parent_message_row["id"],
                    "conversationId": parent_message_row["conversation_id"],
                    "conversationType": parent_message_row["conversation_type"],
                    "content": parent_message_row["content"],
                    "role": parent_message_row["role"],
                    "agentId": parent_message_row["agent_id"],
                    "agentName": parent_message_row["agent_name"],
                    "threadCount": parent_message_row["thread_count"],
                    "createdAt": parent_message_row["created_at"],
                    "timestamp": int(datetime.fromisoformat(parent_message_row["created_at"].replace("Z", "+00:00")).timestamp() * 1000)
                }

            # Get replies (sorted by created_at)
            cursor = conn.execute(
                """
                SELECT id, conversation_id, conversation_type, content, role,
                       agent_id, agent_name, created_at, updated_at
                FROM messages
                WHERE thread_id = ?
                ORDER BY created_at ASC
                """,
                (thread_id,)
            )
            replies_rows = cursor.fetchall()

            replies = []
            for row in replies_rows:
                replies.append({
                    "id": row["id"],
                    "conversationId": row["conversation_id"],
                    "conversationType": row["conversation_type"],
                    "content": row["content"],
                    "role": row["role"],
                    "agentId": row["agent_id"],
                    "agentName": row["agent_name"],
                    "createdAt": row["created_at"],
                    "timestamp": int(datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")).timestamp() * 1000)
                })

            return JSONResponse({
                "threadId": thread["id"],
                "parentMessage": parent_message,
                "replies": replies,
                "conversationId": thread["conversation_id"],
                "conversationType": thread["conversation_type"],
                "replyCount": thread["reply_count"]
            })

        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_thread_failed", thread_id=thread_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get thread: {str(e)}"
        )


@router.post("/{thread_id}/messages")
async def post_thread_reply(
    thread_id: int,
    request: Request,
    body: ThreadReplyRequest
) -> JSONResponse:
    """Post a reply in a thread.

    Args:
        thread_id: Thread ID
        request: FastAPI request object
        body: Request body with message content

    Returns:
        JSON response with created message

    Raises:
        HTTPException: If thread not found or post fails

    Example request:
        POST /api/threads/456/messages
        {
            "content": "This is a reply in the thread"
        }

    Example response:
        {
            "messageId": "msg-789",
            "threadId": 456,
            "content": "This is a reply in the thread",
            "role": "user",
            "createdAt": "2025-01-17T10:15:00Z",
            "parentMessageId": "msg-123"
        }
    """
    # Validate content
    if not body.content or not body.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Message content cannot be empty"
        )

    try:
        project_root = request.app.state.project_root
        conn = _get_db_connection(project_root)

        try:
            # Verify thread exists
            cursor = conn.execute(
                """
                SELECT id, parent_message_id, conversation_id, conversation_type
                FROM threads
                WHERE id = ?
                """,
                (thread_id,)
            )
            thread = cursor.fetchone()

            if not thread:
                raise HTTPException(
                    status_code=404,
                    detail=f"Thread {thread_id} not found"
                )

            # Create message ID
            message_id = f"msg-{uuid.uuid4().hex[:12]}"

            # Insert message
            cursor = conn.execute(
                """
                INSERT INTO messages (
                    id, conversation_id, conversation_type, content, role,
                    thread_id, reply_to_message_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    thread["conversation_id"],
                    thread["conversation_type"],
                    body.content,
                    "user",  # User is always the poster (agent replies not yet supported)
                    thread_id,
                    thread["parent_message_id"]
                )
            )

            # Get created message
            cursor = conn.execute(
                "SELECT id, content, role, created_at FROM messages WHERE id = ?",
                (message_id,)
            )
            message = cursor.fetchone()

            conn.commit()

            logger.info(
                "thread_reply_created",
                message_id=message_id,
                thread_id=thread_id,
                parent_message_id=thread["parent_message_id"]
            )

            # Publish WebSocket events
            try:
                # Event 1: thread.reply
                await request.app.state.event_bus.publish({
                    "type": "thread.reply",
                    "payload": {
                        "messageId": message_id,
                        "threadId": thread_id,
                        "parentMessageId": thread["parent_message_id"],
                        "conversationId": thread["conversation_id"],
                        "conversationType": thread["conversation_type"],
                        "content": body.content,
                        "role": "user",
                        "createdAt": message["created_at"],
                        "timestamp": datetime.now().isoformat()
                    }
                })

                # Event 2: thread.updated (parent message thread count changed)
                # Get updated parent message thread count
                cursor = conn.execute(
                    "SELECT thread_count FROM messages WHERE id = ?",
                    (thread["parent_message_id"],)
                )
                parent_msg = cursor.fetchone()
                thread_count = parent_msg["thread_count"] if parent_msg else 0

                await request.app.state.event_bus.publish({
                    "type": "thread.updated",
                    "payload": {
                        "threadId": thread_id,
                        "parentMessageId": thread["parent_message_id"],
                        "threadCount": thread_count,
                        "timestamp": datetime.now().isoformat()
                    }
                })

            except Exception as ws_error:
                # Non-fatal: WebSocket broadcast failed
                logger.warning(
                    "websocket_broadcast_failed",
                    error=str(ws_error),
                    message_id=message_id
                )

            return JSONResponse({
                "messageId": message_id,
                "threadId": thread_id,
                "content": body.content,
                "role": "user",
                "createdAt": message["created_at"],
                "parentMessageId": thread["parent_message_id"]
            })

        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "post_thread_reply_failed",
            thread_id=thread_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to post thread reply: {str(e)}"
        )
