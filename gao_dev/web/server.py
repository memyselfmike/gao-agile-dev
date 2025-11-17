"""FastAPI web server for GAO-Dev interface."""

import asyncio
import signal
import sys
import webbrowser
from pathlib import Path
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .auth import SessionTokenManager
from .config import WebConfig
from .event_bus import WebEventBus
from .middleware import ReadOnlyMiddleware
from .websocket_manager import WebSocketManager
from .file_tree_builder import build_file_tree
from .file_watcher import FileSystemWatcher
from ..core.session_lock import SessionLock

logger = structlog.get_logger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str
    agent: Optional[str] = "Brian"


class FileSaveRequest(BaseModel):
    """Request model for file save endpoint."""

    path: str
    content: str
    commit_message: str


def _detect_language(file_path: Path) -> str:
    """Detect language/mode for Monaco editor based on file extension.

    Args:
        file_path: Path to file

    Returns:
        Language identifier for Monaco editor
    """
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".html": "html",
        ".css": "css",
        ".sh": "shell",
        ".xml": "xml",
        ".sql": "sql",
        ".txt": "plaintext",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix, "plaintext")


def create_app(config: Optional[WebConfig] = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config: Web server configuration (uses defaults if None)

    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = WebConfig()

    app = FastAPI(
        title="GAO-Dev Web Interface",
        version="1.0.0",
        description="Browser-based interface for GAO-Dev autonomous development system",
    )

    # CORS middleware - restricted to localhost only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Read-only middleware - enforce lock-based access control
    app.add_middleware(ReadOnlyMiddleware)

    # Store config in app state
    app.state.config = config

    # Initialize WebSocket infrastructure
    session_token_manager = SessionTokenManager()
    event_bus = WebEventBus()
    websocket_manager = WebSocketManager(event_bus)

    # Initialize session lock (read mode by default for web observability)
    # frontend_dist_path = "gao_dev/web/frontend/dist" (relative path)
    # Need to resolve to absolute path first, then go up to project root
    # dist → frontend → web → gao_dev → project_root (4 levels up)
    project_root = Path(config.frontend_dist_path).resolve().parent.parent.parent.parent
    session_lock = SessionLock(project_root)

    # Acquire read lock on startup (observability mode)
    if session_lock.acquire("web", mode="read"):
        logger.info("web_session_lock_acquired", mode="read")
    else:
        logger.warning("web_session_lock_acquisition_failed")

    # Store in app state for access by other components
    app.state.session_token_manager = session_token_manager
    app.state.event_bus = event_bus
    app.state.websocket_manager = websocket_manager
    app.state.session_lock = session_lock
    app.state.project_root = project_root

    # Initialize BrianWebAdapter (Story 39.7)
    # NOTE: This will be properly initialized with real ChatSession in future
    # For now, we store None and will create on-demand in chat endpoint
    app.state.brian_adapter = None

    # Initialize FileSystemWatcher (Story 39.13)
    file_watcher = FileSystemWatcher(project_root, event_bus)
    file_watcher.start()
    app.state.file_watcher = file_watcher

    logger.info(
        "websocket_infrastructure_initialized",
        session_token=session_token_manager.get_token()[:8] + "...",
        file_watcher_running=file_watcher.is_running()
    )

    # Health check endpoint
    @app.get("/api/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with status and version
        """
        return JSONResponse({"status": "healthy", "version": "1.0.0"})

    # Session token endpoint
    @app.get("/api/session/token")
    async def get_session_token() -> JSONResponse:
        """Get session token for WebSocket authentication.

        Returns:
            JSON response with session token
        """
        return JSONResponse({"token": session_token_manager.get_token()})

    # Agents endpoint (Story 39.8)
    @app.get("/api/agents")
    async def get_agents() -> JSONResponse:
        """Get list of all available agents with metadata.

        Returns:
            JSON response with array of agent configurations
        """
        agents = [
            {
                "id": "brian",
                "name": "Brian",
                "role": "Workflow Coordinator",
                "description": "Analyzes requests, selects workflows, and coordinates other agents",
                "icon": "workflow",
            },
            {
                "id": "mary",
                "name": "Mary",
                "role": "Business Analyst",
                "description": "Elicits vision, facilitates brainstorming, analyzes requirements",
                "icon": "lightbulb",
            },
            {
                "id": "john",
                "name": "John",
                "role": "Product Manager",
                "description": "Creates PRDs, defines features, prioritizes work",
                "icon": "clipboard-list",
            },
            {
                "id": "winston",
                "name": "Winston",
                "role": "Technical Architect",
                "description": "Designs system architecture and technical specifications",
                "icon": "layers",
            },
            {
                "id": "sally",
                "name": "Sally",
                "role": "UX Designer",
                "description": "Creates user experience designs and wireframes",
                "icon": "palette",
            },
            {
                "id": "bob",
                "name": "Bob",
                "role": "Scrum Master",
                "description": "Manages stories, coordinates sprints, tracks progress",
                "icon": "kanban",
            },
            {
                "id": "amelia",
                "name": "Amelia",
                "role": "Software Developer",
                "description": "Implements features, writes tests, reviews code",
                "icon": "code",
            },
            {
                "id": "murat",
                "name": "Murat",
                "role": "Test Architect",
                "description": "Designs test strategies and quality assurance processes",
                "icon": "check-circle",
            },
        ]
        return JSONResponse({"agents": agents})

    # Session lock state endpoint
    @app.get("/api/session/lock-state")
    async def get_lock_state() -> JSONResponse:
        """Get current session lock state.

        Returns:
            JSON response with lock mode, read-only status, and holder
        """
        lock_state = app.state.session_lock.get_lock_state()

        # Determine if we're in read-only mode
        is_read_only = lock_state["mode"] == "read" and lock_state["holder"] is not None

        return JSONResponse(
            {
                "mode": lock_state["mode"],
                "isReadOnly": is_read_only,
                "holder": lock_state["holder"],
                "timestamp": lock_state["timestamp"],
            }
        )

    # Chat endpoints (Story 39.7)
    @app.post("/api/chat")
    async def send_chat_message(request: ChatRequest) -> JSONResponse:
        """Send message to Brian via chat.

        This endpoint triggers the BrianWebAdapter which streams responses
        via WebSocket events (chat.streaming_chunk, chat.message_received).

        Args:
            request: Chat request with message and agent

        Returns:
            JSON response with message acknowledgement

        Raises:
            HTTPException: If message is empty or adapter fails
        """
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Validate agent (currently only Brian supported)
        if request.agent and request.agent != "Brian":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported agent: {request.agent}. Only 'Brian' is supported."
            )

        try:
            # Get or create BrianWebAdapter
            if app.state.brian_adapter is None:
                # Initialize Brian adapter on first use
                from gao_dev.orchestrator.chat_session import ChatSession
                from gao_dev.orchestrator.conversational_brian import ConversationalBrian
                from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
                from gao_dev.cli.command_router import CommandRouter
                from gao_dev.web.adapters import BrianWebAdapter
                from gao_dev.core.workflow_registry import WorkflowRegistry
                from gao_dev.core.services.ai_analysis_service import AIAnalysisService
                from gao_dev.core.config_loader import ConfigLoader
                from gao_dev.core.services.process_executor import ProcessExecutor

                # Create services (matching ChatREPL initialization)
                config_loader = ConfigLoader(project_root)
                workflow_registry = WorkflowRegistry(config_loader)
                executor = ProcessExecutor(project_root)
                analysis_service = AIAnalysisService(executor)

                # Create StateTracker and OperationTracker (needed for CommandRouter)
                from gao_dev.core.state.state_tracker import StateTracker
                from gao_dev.core.state.operation_tracker import OperationTracker
                from gao_dev.orchestrator.orchestrator import GAODevOrchestrator

                db_path = project_root / ".gao-dev" / "documents.db"
                state_tracker = StateTracker(db_path) if db_path.exists() else None
                operation_tracker = OperationTracker(state_tracker) if state_tracker else None

                # Create orchestrator
                orchestrator = GAODevOrchestrator.create_default(
                    project_root=project_root,
                    mode="web"
                )

                # Create Brian infrastructure (reusing Epic 30 components)
                brian_orchestrator = BrianOrchestrator(
                    workflow_registry=workflow_registry,
                    analysis_service=analysis_service,
                    project_root=project_root
                )

                # Create command router with all required dependencies
                command_router = CommandRouter(
                    orchestrator=orchestrator,
                    operation_tracker=operation_tracker,
                    analysis_service=analysis_service
                ) if operation_tracker else None

                conversational_brian = ConversationalBrian(
                    brian_orchestrator=brian_orchestrator,
                    command_router=command_router
                )

                chat_session = ChatSession(
                    conversational_brian=conversational_brian,
                    command_router=command_router,
                    project_root=project_root
                )

                # Create adapter
                app.state.brian_adapter = BrianWebAdapter(
                    chat_session=chat_session,
                    event_bus=event_bus
                )

                logger.info("brian_adapter_initialized")

            # Send message (responses stream via WebSocket)
            # We collect chunks here but don't return them (WebSocket does that)
            chunks = []
            async for chunk in app.state.brian_adapter.send_message(request.message):
                chunks.append(chunk)

            return JSONResponse({
                "status": "success",
                "message": "Message sent to Brian",
                "agent": request.agent or "Brian",
                "chunks_sent": len(chunks)
            })

        except Exception as e:
            logger.exception("chat_message_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send message: {str(e)}"
            )

    @app.get("/api/chat/history")
    async def get_chat_history(max_turns: int = 50) -> JSONResponse:
        """Get conversation history.

        Args:
            max_turns: Maximum number of turns to return (default: 50)

        Returns:
            JSON response with conversation history
        """
        if app.state.brian_adapter is None:
            return JSONResponse({"messages": []})

        try:
            history = app.state.brian_adapter.get_conversation_history(max_turns)
            return JSONResponse({"messages": history})
        except Exception as e:
            logger.exception("get_history_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get history: {str(e)}"
            )

    @app.get("/api/chat/context")
    async def get_chat_context() -> JSONResponse:
        """Get current session context.

        Returns:
            JSON response with session context
        """
        if app.state.brian_adapter is None:
            return JSONResponse({
                "projectRoot": str(project_root),
                "currentEpic": None,
                "currentStory": None,
                "pendingConfirmation": False,
                "contextSummary": "No active session"
            })

        try:
            context = app.state.brian_adapter.get_session_context()
            return JSONResponse(context)
        except Exception as e:
            logger.exception("get_context_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get context: {str(e)}"
            )

    # File endpoints (Story 39.11, 39.12, 39.14)
    @app.get("/api/files/tree")
    async def get_file_tree() -> JSONResponse:
        """Get project file tree structure.

        Returns hierarchical file tree with only tracked directories.
        Respects .gitignore and highlights recently changed files.

        Returns:
            JSON response with file tree
        """
        try:
            tree = build_file_tree(project_root)
            return JSONResponse({"tree": tree})
        except Exception as e:
            logger.exception("get_file_tree_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get file tree: {str(e)}"
            )

    @app.get("/api/files/content")
    async def get_file_content(path: str) -> JSONResponse:
        """Get file content for given path.

        Args:
            path: Relative path to file from project root

        Returns:
            JSON response with file content

        Raises:
            HTTPException: If file not found or cannot be read
        """
        try:
            file_path = project_root / path

            # Security: Ensure path is within project root
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(project_root.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")

            # Check if file exists
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return JSONResponse({
                "path": path,
                "content": content,
                "size": len(content),
                "language": _detect_language(file_path)
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("get_file_content_failed", path=path, error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read file: {str(e)}"
            )

    @app.post("/api/files/save")
    async def save_file(request: FileSaveRequest) -> JSONResponse:
        """Save file with commit message.

        Atomic operation: file write + DB update + git commit.
        Requires write lock (enforced by middleware).

        Args:
            request: File save request with path, content, and commit message

        Returns:
            JSON response with success status

        Raises:
            HTTPException: If save fails or validation fails
        """
        # Validate commit message format
        if not request.commit_message or not request.commit_message.strip():
            raise HTTPException(
                status_code=400,
                detail="Commit message is required"
            )

        # Basic commit message format validation
        import re
        commit_pattern = r'^(feat|fix|docs|refactor|test|chore|style|perf)\([^)]+\):.+'
        if not re.match(commit_pattern, request.commit_message):
            raise HTTPException(
                status_code=400,
                detail="Commit message must follow format: <type>(<scope>): <description>"
            )

        try:
            file_path = project_root / request.path

            # Security: Ensure path is within project root
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(project_root.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)

            # Git commit (atomic)
            from gao_dev.core.git_manager import GitManager
            git_manager = GitManager(project_path=project_root)

            # Add file
            git_manager.add_files([file_path])

            # Commit
            commit_hash = git_manager.commit(
                message=request.commit_message,
                author_name="Web User",
                author_email="web@gao-dev.local"
            )

            # Publish file.modified event
            event_bus.publish({
                "type": "file.modified",
                "payload": {
                    "path": request.path,
                    "commitHash": commit_hash,
                    "commitMessage": request.commit_message,
                    "agent": "web",
                    "timestamp": asyncio.get_event_loop().time()
                }
            })

            logger.info(
                "file_saved_and_committed",
                path=request.path,
                commit_hash=commit_hash[:8]
            )

            return JSONResponse({
                "status": "success",
                "path": request.path,
                "commitHash": commit_hash,
                "message": "File saved and committed"
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("save_file_failed", path=request.path, error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )

    @app.get("/api/files/diff")
    async def get_file_diff(path: str) -> JSONResponse:
        """Get diff of file vs last commit.

        Args:
            path: Relative path to file from project root

        Returns:
            JSON response with diff

        Raises:
            HTTPException: If diff cannot be generated
        """
        try:
            from gao_dev.core.git_manager import GitManager
            git_manager = GitManager(project_path=project_root)

            # Get diff vs HEAD
            diff = git_manager.get_file_diff(path)

            return JSONResponse({
                "path": path,
                "diff": diff
            })

        except Exception as e:
            logger.exception("get_file_diff_failed", path=path, error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get diff: {str(e)}"
            )

    # Workflow visualization endpoints (Story 39.20)
    @app.get("/api/workflows/timeline")
    async def get_workflow_timeline(
        request: Request,
        workflow_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> JSONResponse:
        """Get workflow execution timeline with optional filters.

        Returns timeline data for workflow visualization with filtering by:
        - workflow_type: Specific workflow name
        - start_date: ISO 8601 timestamp (filter started_at >= this)
        - end_date: ISO 8601 timestamp (filter started_at <= this)
        - status: Comma-separated list of statuses

        Args:
            request: FastAPI request object
            workflow_type: Optional workflow name filter
            start_date: Optional start date filter (ISO 8601)
            end_date: Optional end date filter (ISO 8601)
            status: Optional comma-separated status filter

        Returns:
            JSON response with workflows array, total count, and filter metadata
        """
        try:
            from gao_dev.core.state.state_tracker import StateTracker
            from gao_dev.core.state.exceptions import StateTrackerError
            import sqlite3
            from datetime import datetime

            # Get project root from app state
            project_root_path = request.app.state.project_root

            # Check if database exists
            db_path = project_root_path / ".gao-dev" / "documents.db"
            if not db_path.exists():
                # Return empty timeline if no database yet
                return JSONResponse({
                    "workflows": [],
                    "total": 0,
                    "filters": {
                        "workflow_types": [],
                        "date_range": {"min": None, "max": None},
                        "statuses": ["pending", "running", "completed", "failed", "cancelled"]
                    }
                })

            # Parse status filter (comma-separated)
            status_list = None
            if status:
                status_list = [s.strip() for s in status.split(",")]

            # Query workflows with filters
            try:
                state_tracker = StateTracker(db_path)
                workflows = state_tracker.query_workflows(
                    workflow_type=workflow_type,
                    start_date=start_date,
                    end_date=end_date,
                    status=status_list
                )

                # Get filter metadata
                workflow_types = state_tracker.get_workflow_types()
                date_range = state_tracker.get_workflow_date_range()

            except (sqlite3.OperationalError, StateTrackerError) as e:
                # Handle unmigrated database
                error_msg = str(e)
                if "no such table" in error_msg:
                    logger.warning(
                        "workflow_timeline_schema_not_initialized",
                        error=error_msg,
                        hint="Run 'gao-dev migrate' to initialize database schema"
                    )
                    return JSONResponse({
                        "workflows": [],
                        "total": 0,
                        "filters": {
                            "workflow_types": [],
                            "date_range": {"min": None, "max": None},
                            "statuses": ["pending", "running", "completed", "failed", "cancelled"]
                        }
                    })
                raise

            # Build response with workflow data
            workflow_data = []
            for wf in workflows:
                # Calculate duration if completed
                duration = None
                if wf.completed_at and wf.started_at:
                    try:
                        started = datetime.fromisoformat(wf.started_at.replace("Z", "+00:00"))
                        completed = datetime.fromisoformat(wf.completed_at.replace("Z", "+00:00"))
                        duration = int((completed - started).total_seconds())
                    except (ValueError, AttributeError):
                        duration = None

                workflow_data.append({
                    "id": wf.id,
                    "workflow_id": wf.workflow_id,
                    "workflow_name": wf.workflow_name,
                    "status": wf.status,
                    "started_at": wf.started_at,
                    "completed_at": wf.completed_at,
                    "duration": duration,
                    "agent": wf.workflow_id,  # executor is the agent identifier
                    "epic": wf.epic,
                    "story_num": wf.story_num
                })

            return JSONResponse({
                "workflows": workflow_data,
                "total": len(workflow_data),
                "filters": {
                    "workflow_types": workflow_types,
                    "date_range": date_range,
                    "statuses": ["pending", "running", "completed", "failed", "cancelled"]
                }
            })

        except Exception as e:
            logger.exception("get_workflow_timeline_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get workflow timeline: {str(e)}"
            )

    # Kanban endpoints (Story 39.15)
    @app.get("/api/kanban/board")
    async def get_kanban_board(request: Request) -> JSONResponse:
        """Get all epics and stories grouped by state.

        Returns Kanban board data with epics and stories organized into 5 columns:
        - backlog: Stories with status 'pending'
        - ready: Stories that are ready to be worked on
        - in_progress: Stories currently being worked on
        - in_review: Stories under review
        - done: Completed stories

        Args:
            request: FastAPI request object (for accessing app.state)

        Returns:
            JSON response with columns containing epics and stories

        Raises:
            HTTPException: If database query fails
        """
        try:
            # Import StateTracker
            from gao_dev.core.state.state_tracker import StateTracker
            from gao_dev.core.state.exceptions import StateTrackerError
            import sqlite3

            # Get project root from app state (can be overridden in tests)
            project_root_path = request.app.state.project_root

            # Check if database exists
            db_path = project_root_path / ".gao-dev" / "documents.db"
            if not db_path.exists():
                # Return empty board if no database yet
                return JSONResponse({
                    "columns": {
                        "backlog": [],
                        "ready": [],
                        "in_progress": [],
                        "in_review": [],
                        "done": []
                    }
                })

            # Query database
            try:
                state_tracker = StateTracker(db_path)
                # Get all active epics
                epics = state_tracker.get_active_epics()
            except (sqlite3.OperationalError, StateTrackerError) as e:
                # Handle unmigrated database (schema not initialized)
                error_msg = str(e)
                if "no such table" in error_msg:
                    logger.warning(
                        "kanban_board_schema_not_initialized",
                        error=error_msg,
                        hint="Run 'gao-dev migrate migrate' to initialize database schema"
                    )
                    # Return empty board
                    return JSONResponse({
                        "columns": {
                            "backlog": [],
                            "ready": [],
                            "in_progress": [],
                            "in_review": [],
                            "done": []
                        }
                    })
                # Re-raise other errors
                raise

            # Build map of stories by status
            # Note: The database uses 'pending', 'in_progress', 'done', 'blocked', 'cancelled'
            # We'll map these to Kanban columns
            columns = {
                "backlog": [],
                "ready": [],
                "in_progress": [],
                "in_review": [],
                "done": []
            }

            # Process each epic
            for epic in epics:
                # Get stories for this epic
                stories = state_tracker.get_stories_by_epic(epic.epic_num)

                # Group stories by status
                for story in stories:
                    # Map database status to Kanban column
                    # Database statuses: pending, in_progress, done, blocked, cancelled
                    # Kanban columns: backlog, ready, in_progress, in_review, done
                    status = story.status.lower()

                    # Default mapping
                    column = "backlog"
                    if status == "pending":
                        column = "backlog"
                    elif status == "ready":
                        column = "ready"
                    elif status == "in_progress":
                        column = "in_progress"
                    elif status == "in_review":
                        column = "in_review"
                    elif status == "done":
                        column = "done"
                    elif status == "blocked":
                        # Blocked stories stay in their original column but marked
                        column = "backlog"
                    elif status == "cancelled":
                        # Skip cancelled stories
                        continue

                    # Add story card to appropriate column
                    columns[column].append({
                        "id": f"story-{story.epic}.{story.story_num}",
                        "type": "story",
                        "number": f"{story.epic}.{story.story_num}",
                        "epicNumber": story.epic,
                        "storyNumber": story.story_num,
                        "title": story.title,
                        "status": story.status,
                        "owner": story.owner,
                        "points": story.points,
                        "priority": story.priority
                    })

                # Add epic card showing summary
                # Place epic in column based on overall progress
                epic_column = "backlog"
                if epic.progress >= 100.0:
                    epic_column = "done"
                elif epic.progress > 0:
                    epic_column = "in_progress"

                # Count stories by status for epic card
                story_counts = {
                    "total": len(stories),
                    "done": len([s for s in stories if s.status == "done"]),
                    "in_progress": len([s for s in stories if s.status == "in_progress"]),
                    "backlog": len([s for s in stories if s.status == "pending"])
                }

                # Add epic card to appropriate column
                columns[epic_column].append({
                    "id": f"epic-{epic.epic_num}",
                    "type": "epic",
                    "number": str(epic.epic_num),
                    "title": epic.title,
                    "status": epic.status,
                    "progress": epic.progress,
                    "totalPoints": epic.total_points,
                    "completedPoints": epic.completed_points,
                    "storyCounts": story_counts
                })

            return JSONResponse({"columns": columns})

        except Exception as e:
            logger.exception("get_kanban_board_failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get kanban board: {str(e)}"
            )

    # Story 39.17: Drag-and-drop card move endpoint
    class MoveCardRequest(BaseModel):
        """Request model for moving a card to a new status."""
        fromStatus: str
        toStatus: str

    @app.patch("/api/kanban/cards/{card_id}/move")
    async def move_kanban_card(
        card_id: str,
        request: Request,
        body: MoveCardRequest
    ) -> JSONResponse:
        """Move a kanban card to a new status (drag-and-drop transition).

        Performs atomic state transition:
        1. Parse card_id (epic-N or story-N.M)
        2. Update status in database via StateTracker
        3. Emit WebSocket event for real-time updates
        4. Return updated card data

        Args:
            card_id: Card identifier (e.g., "story-1.1" or "epic-1")
            request: FastAPI request object
            body: Request body with fromStatus and toStatus

        Returns:
            JSON response with success status and updated card

        Raises:
            HTTPException: If card not found, invalid transition, or update fails
        """
        try:
            from gao_dev.core.state.state_tracker import StateTracker
            from gao_dev.core.state.exceptions import StateTrackerError
            import sqlite3
            from datetime import datetime

            # Get project root from app state
            project_root_path = request.app.state.project_root

            # Check if database exists
            db_path = project_root_path / ".gao-dev" / "documents.db"
            if not db_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Project database not found. Initialize project first."
                )

            # Parse card ID
            if card_id.startswith("epic-"):
                # Epic card: epic-N
                epic_num = int(card_id.split("-")[1])
                story_num = None
                card_type = "epic"
            elif card_id.startswith("story-"):
                # Story card: story-N.M
                parts = card_id.split("-")[1].split(".")
                epic_num = int(parts[0])
                story_num = int(parts[1])
                card_type = "story"
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid card ID format: {card_id}"
                )

            # Validate status values
            valid_statuses = ["backlog", "ready", "in_progress", "in_review", "done"]
            if body.toStatus not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {body.toStatus}. Must be one of {valid_statuses}"
                )

            # Update status in database
            state_tracker = StateTracker(db_path)

            if card_type == "story":
                # Update story status
                # Note: StateTracker uses different status names (pending, in_progress, done)
                # Map from Kanban column names to DB status names
                status_map = {
                    "backlog": "pending",
                    "ready": "ready",
                    "in_progress": "in_progress",
                    "in_review": "in_review",
                    "done": "done"
                }

                db_status = status_map.get(body.toStatus, body.toStatus)

                # Update story status
                state_tracker.update_story_status(
                    epic_num=epic_num,
                    story_num=story_num,
                    new_status=db_status
                )

                # Get updated story
                story = state_tracker.get_story(epic_num, story_num)
                if not story:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Story {epic_num}.{story_num} not found"
                    )

                updated_card = {
                    "id": card_id,
                    "type": "story",
                    "number": f"{story.epic}.{story.story_num}",
                    "epicNumber": story.epic,
                    "storyNumber": story.story_num,
                    "title": story.title,
                    "status": body.toStatus,
                    "owner": story.owner,
                    "points": story.points,
                    "priority": story.priority
                }

            else:  # epic
                # Update epic status
                # Note: Epics don't have explicit status in StateTracker
                # This is a simplified implementation - epics derive status from stories
                # For now, we'll just return success without updating
                logger.warning(
                    "epic_move_not_implemented",
                    epic_num=epic_num,
                    message="Epic drag-and-drop not fully implemented (status derived from stories)"
                )

                epic = state_tracker.get_epic(epic_num)
                if not epic:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Epic {epic_num} not found"
                    )

                # Get stories for epic to calculate progress
                stories = state_tracker.get_stories_by_epic(epic_num)
                story_counts = {
                    "total": len(stories),
                    "done": len([s for s in stories if s.status == "done"]),
                    "in_progress": len([s for s in stories if s.status == "in_progress"]),
                    "backlog": len([s for s in stories if s.status == "pending"])
                }

                updated_card = {
                    "id": card_id,
                    "type": "epic",
                    "number": str(epic.epic_num),
                    "title": epic.title,
                    "status": body.toStatus,
                    "progress": epic.progress,
                    "totalPoints": epic.total_points,
                    "completedPoints": epic.completed_points,
                    "storyCounts": story_counts
                }

            # Emit WebSocket event for real-time updates
            try:
                from gao_dev.web.event_bus import WebEvent

                await request.app.state.event_bus.publish(WebEvent(
                    type="kanban.card.moved",
                    data={
                        "cardId": card_id,
                        "cardType": card_type,
                        "fromStatus": body.fromStatus,
                        "toStatus": body.toStatus,
                        "card": updated_card,
                        "timestamp": datetime.now().isoformat()
                    }
                ))

                logger.info(
                    "kanban_card_moved",
                    card_id=card_id,
                    card_type=card_type,
                    from_status=body.fromStatus,
                    to_status=body.toStatus
                )
            except Exception as ws_error:
                # Non-fatal: WebSocket broadcast failed
                logger.warning(
                    "websocket_broadcast_failed",
                    error=str(ws_error),
                    card_id=card_id
                )

            return JSONResponse({
                "success": True,
                "card": updated_card
            })

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except (sqlite3.OperationalError, StateTrackerError) as e:
            logger.exception("move_kanban_card_db_error", error=str(e), card_id=card_id)
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            logger.exception("move_kanban_card_failed", error=str(e), card_id=card_id)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to move card: {str(e)}"
            )

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time communication.

        Requires X-Session-Token header for authentication.
        Supports reconnection with event replay via X-Client-Id and X-Last-Sequence headers.

        Args:
            websocket: WebSocket connection
        """
        # Extract authentication token
        token = websocket.headers.get("X-Session-Token") or websocket.query_params.get(
            "token"
        )

        if not session_token_manager.validate(token):
            logger.warning(
                "websocket_auth_failed",
                headers_present="X-Session-Token" in websocket.headers,
            )
            await websocket.close(code=1008, reason="Unauthorized")
            return

        # Extract reconnection parameters
        client_id = websocket.headers.get("X-Client-Id")
        last_sequence_str = websocket.headers.get("X-Last-Sequence")
        last_sequence = int(last_sequence_str) if last_sequence_str else None

        # Connect client
        try:
            assigned_client_id = await websocket_manager.connect(
                websocket, client_id, last_sequence
            )

            logger.info(
                "websocket_connection_established",
                client_id=assigned_client_id,
                reconnection=client_id is not None,
            )

            # Keep connection alive until disconnect
            # The WebSocketManager handles event streaming
            while True:
                # Receive messages from client (for future bidirectional communication)
                try:
                    data = await websocket.receive_json()
                    # Future: Handle client commands (subscribe, unsubscribe, etc.)
                    logger.debug("websocket_message_received", client_id=assigned_client_id)
                except Exception:
                    break

        except ValueError as e:
            # Connection limit exceeded
            logger.error("websocket_connection_failed", error=str(e))
            await websocket.close(code=1008, reason=str(e))
        except WebSocketDisconnect:
            logger.info("websocket_disconnected", client_id=client_id)
        finally:
            if client_id:
                await websocket_manager.disconnect(client_id)

    # Static file serving (frontend build)
    frontend_dist = Path(config.frontend_dist_path)
    index_path = frontend_dist / "index.html"

    # Check if frontend build is actually ready (both directory and index.html exist)
    if frontend_dist.exists() and index_path.exists():
        # Mount static assets if they exist
        assets_path = frontend_dist / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

        # Serve index.html for root route
        @app.get("/")
        async def serve_index() -> FileResponse:
            """Serve the frontend index.html."""
            return FileResponse(str(index_path))

    else:
        # Frontend not built yet - serve placeholder
        @app.get("/")
        async def serve_placeholder() -> JSONResponse:
            """Serve placeholder when frontend is not built."""
            return JSONResponse(
                {
                    "message": "GAO-Dev Web Interface",
                    "status": "Frontend not built",
                    "instructions": "Frontend will be built in Story 39.4",
                },
                status_code=200,
            )

    return app


class ServerManager:
    """Manages the web server lifecycle with graceful shutdown."""

    def __init__(self, config: Optional[WebConfig] = None):
        """Initialize server manager.

        Args:
            config: Web server configuration
        """
        self.config = config or WebConfig()
        self.server: Optional[uvicorn.Server] = None
        self.shutdown_event = asyncio.Event()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame: Optional[object]) -> None:
            """Handle shutdown signals."""
            logger.info("shutting_down_web_server", signal=signum)
            self.shutdown_event.set()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def start_async(self) -> None:
        """Start the server asynchronously."""
        self._setup_signal_handlers()

        # Create FastAPI app
        app = create_app(self.config)

        # Auto-open browser
        if self.config.auto_open:
            url = self.config.get_url()
            logger.info("auto_opening_browser", url=url)
            webbrowser.open(url)

        # Configure uvicorn
        config_uvicorn = uvicorn.Config(
            app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
            access_log=True,
        )
        self.server = uvicorn.Server(config_uvicorn)

        # Log startup
        logger.info(
            "starting_web_server",
            host=self.config.host,
            port=self.config.port,
            url=self.config.get_url(),
        )

        # Start server
        try:
            await self.server.serve()
        except OSError as e:
            if "Address already in use" in str(e) or "Only one usage" in str(e):
                logger.error("port_already_in_use", port=self.config.port, error=str(e))
                raise OSError(
                    f"Port {self.config.port} already in use. Try `--port {self.config.port + 1}`"
                ) from e
            raise

    def stop(self) -> None:
        """Stop the server gracefully and release lock."""
        if self.server:
            logger.info("stopping_web_server")

            # Stop file watcher if running
            if hasattr(self.server, "config") and hasattr(self.server.config, "app"):
                if hasattr(self.server.config.app.state, "file_watcher"):
                    self.server.config.app.state.file_watcher.stop()
                    logger.info("file_watcher_stopped")

                # Release session lock if acquired
                if hasattr(self.server.config.app.state, "session_lock"):
                    self.server.config.app.state.session_lock.release()
                    logger.info("web_session_lock_released")

            self.server.should_exit = True


def start_server(
    host: str = "127.0.0.1",
    port: int = 3000,
    auto_open: bool = True,
    config: Optional[WebConfig] = None,
) -> None:
    """Start the FastAPI web server.

    Args:
        host: Server host (default: 127.0.0.1)
        port: Server port (default: 3000)
        auto_open: Auto-open browser (default: True)
        config: Web configuration (overrides other params if provided)

    Raises:
        OSError: If port is already in use
    """
    if config is None:
        config = WebConfig(host=host, port=port, auto_open=auto_open)

    manager = ServerManager(config)

    # Log startup message
    url = config.get_url()
    print(f"Web interface available at {url}")

    try:
        asyncio.run(manager.start_async())
    except KeyboardInterrupt:
        logger.info("shutting_down_web_server", reason="keyboard_interrupt")
    except OSError as e:
        # Re-raise with helpful message
        raise
    finally:
        manager.stop()
        logger.info("web_server_stopped")
