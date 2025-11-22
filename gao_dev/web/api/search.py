"""Search API endpoints for message search across DMs and channels.

Story 39.36: Message Search Across DMs and Channels

Provides full-text search across all messages with filters for:
- Message type (DMs, channels, or all)
- Agent filter
- Date range filter
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Literal, Optional

import sqlite3

import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


# Response Models
class SearchHighlight(BaseModel):
    """Highlighted search term."""

    term: str


class SearchResult(BaseModel):
    """Single search result."""

    messageId: str
    conversationId: str
    conversationType: Literal["dm", "channel"]
    content: str
    sender: str
    timestamp: str
    highlights: List[str]


class SearchResponse(BaseModel):
    """Search response with results."""

    results: List[SearchResult]
    total: int


def parse_date_range(date_range: str) -> Optional[datetime]:
    """Parse date range string to datetime cutoff.

    Args:
        date_range: Date range string (7d, 30d, all, or custom ISO date)

    Returns:
        Datetime cutoff (messages after this date), or None for all time
    """
    if date_range == "all" or not date_range:
        return None

    if date_range == "7d":
        return datetime.now() - timedelta(days=7)
    elif date_range == "30d":
        return datetime.now() - timedelta(days=30)
    else:
        # Try to parse as ISO date
        try:
            return datetime.fromisoformat(date_range.replace("Z", "+00:00"))
        except ValueError:
            logger.warning("invalid_date_range", date_range=date_range)
            return None


@router.get("/messages")
async def search_messages(
    request: Request,
    q: str = Query(..., description="Search query"),
    type: Literal["all", "dm", "channel"] = Query(
        "all", description="Filter by message type"
    ),
    agent: Optional[str] = Query(None, description="Filter by agent ID"),
    date_range: str = Query("all", description="Date range filter (7d, 30d, all)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
) -> JSONResponse:
    """Search messages across all DMs and channels.

    Uses SQLite FTS5 for full-text search with ranking by relevance.

    Args:
        request: FastAPI request object
        q: Search query string
        type: Filter by message type (all, dm, channel)
        agent: Filter by specific agent ID
        date_range: Date range filter (7d, 30d, all, or ISO date)
        limit: Maximum number of results (1-100)

    Returns:
        JSON response with search results

    Raises:
        HTTPException: If search query is empty or search fails

    Example response:
        {
            "results": [
                {
                    "messageId": "msg-123",
                    "conversationId": "brian",
                    "conversationType": "dm",
                    "content": "Let's create a PRD for user authentication...",
                    "sender": "brian",
                    "timestamp": "2025-01-10T14:30:00Z",
                    "highlights": ["PRD", "authentication"]
                }
            ],
            "total": 15
        }
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        # Get project root from app state
        project_root = getattr(request.app.state, "project_root", Path.cwd())
        db_path = project_root / ".gao-dev" / "documents.db"

        if not db_path.exists():
            logger.warning("database_not_found", db_path=str(db_path))
            return JSONResponse({"results": [], "total": 0})

        # Parse date range
        date_cutoff = parse_date_range(date_range)

        # Build FTS5 search query
        # SQLite FTS5 uses double quotes for exact phrases, OR for alternatives
        # Sanitize query to prevent FTS5 syntax errors
        q.strip().replace('"', '""')  # Escape quotes

        # Build SQL query with filters
        sql_parts = [
            """
            SELECT
                m.id as messageId,
                m.conversation_id as conversationId,
                m.conversation_type as conversationType,
                m.content,
                CASE
                    WHEN m.role = 'agent' THEN m.agent_id
                    ELSE 'user'
                END as sender,
                m.created_at as timestamp
            FROM messages m
            WHERE 1=1
            """
        ]

        params: List[str | int] = []

        # Add full-text search filter
        # Use LIKE for basic search (FTS5 requires virtual table setup)
        sql_parts.append("AND LOWER(m.content) LIKE LOWER(?)")
        params.append(f"%{q}%")

        # Filter by message type
        if type == "dm":
            sql_parts.append("AND m.conversation_type = 'dm'")
        elif type == "channel":
            sql_parts.append("AND m.conversation_type = 'channel'")

        # Filter by agent
        if agent:
            sql_parts.append("AND m.agent_id = ?")
            params.append(agent)

        # Filter by date range
        if date_cutoff:
            sql_parts.append("AND datetime(m.created_at) >= datetime(?)")
            params.append(date_cutoff.isoformat())

        # Order by relevance (most recent first for now)
        # TODO: Implement proper relevance scoring with FTS5
        sql_parts.append("ORDER BY m.created_at DESC")
        sql_parts.append("LIMIT ?")
        params.append(limit)

        query = "\n".join(sql_parts)

        # Execute search
        conn = sqlite3.connect(str(db_path))
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Extract search terms for highlighting
            search_terms = [term.strip() for term in q.lower().split() if term.strip()]

            # Build results
            results: List[SearchResult] = []
            for row in rows:
                # Extract highlights (words from content that match search terms)
                content_words = row[3].split()
                highlights = []
                for word in content_words:
                    word_lower = word.lower().strip(".,!?;:")
                    if any(term in word_lower for term in search_terms):
                        highlights.append(word.strip(".,!?;:"))

                # Deduplicate and limit highlights
                highlights = list(dict.fromkeys(highlights))[:5]

                results.append(
                    SearchResult(
                        messageId=row[0],
                        conversationId=row[1],
                        conversationType=row[2],
                        content=row[3][:200],  # Truncate to 200 chars
                        sender=row[4],
                        timestamp=row[5],
                        highlights=highlights,
                    )
                )

            logger.info(
                "search_completed",
                query=q,
                type=type,
                agent=agent,
                date_range=date_range,
                results_count=len(results),
            )

            return JSONResponse(
                {
                    "results": [r.dict() for r in results],
                    "total": len(results),
                }
            )
        finally:
            conn.close()

    except Exception as e:
        logger.exception("search_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
