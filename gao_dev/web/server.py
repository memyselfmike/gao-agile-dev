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

from .auth import SessionTokenManager
from .config import WebConfig
from .event_bus import WebEventBus
from .websocket_manager import WebSocketManager

logger = structlog.get_logger(__name__)


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

    # Store config in app state
    app.state.config = config

    # Initialize WebSocket infrastructure
    session_token_manager = SessionTokenManager()
    event_bus = WebEventBus()
    websocket_manager = WebSocketManager(event_bus)

    # Store in app state for access by other components
    app.state.session_token_manager = session_token_manager
    app.state.event_bus = event_bus
    app.state.websocket_manager = websocket_manager

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
        """Stop the server gracefully."""
        if self.server:
            logger.info("stopping_web_server")
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
