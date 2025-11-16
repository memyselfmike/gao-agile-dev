"""FastAPI web server for GAO-Dev interface."""

import asyncio
import signal
import sys
import webbrowser
from pathlib import Path
from typing import Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .auth import SessionTokenManager
from .config import WebConfig
from .event_bus import WebEventBus
from .middleware import ReadOnlyMiddleware
from .websocket_manager import WebSocketManager
from ..core.session_lock import SessionLock

logger = structlog.get_logger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str
    agent: Optional[str] = "Brian"


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
    project_root = Path(config.frontend_dist_path).parent.parent
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

    # Initialize BrianWebAdapter (Story 39.7)
    # NOTE: This will be properly initialized with real ChatSession in future
    # For now, we store None and will create on-demand in chat endpoint
    app.state.brian_adapter = None

    logger.info(
        "websocket_infrastructure_initialized",
        session_token=session_token_manager.get_token()[:8] + "...",
    )

    # Health check endpoint
    @app.get("/api/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with status and version
        """
        return JSONResponse({"status": "healthy", "version": "1.0.0"})

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
                from gao_dev.orchestrator.command_router import CommandRouter
                from gao_dev.web.adapters import BrianWebAdapter

                # Create Brian infrastructure (reusing Epic 30 components)
                brian_orchestrator = BrianOrchestrator(project_root)
                command_router = CommandRouter(project_root)
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

            # Release session lock if acquired
            if hasattr(self.server, "config") and hasattr(self.server.config, "app"):
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
