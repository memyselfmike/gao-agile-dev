"""Configuration for GAO-Dev web server."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


def _get_default_frontend_dist_path() -> str:
    """Get the default frontend dist path relative to package installation.

    Returns:
        Absolute path to the frontend dist directory
    """
    # Get the directory containing this config.py file
    # config.py is in gao_dev/web/, so frontend/dist is at gao_dev/web/frontend/dist
    web_dir = Path(__file__).parent
    frontend_dist = web_dir / "frontend" / "dist"
    return str(frontend_dist)


def _get_cors_origins() -> List[str]:
    """Get CORS origins with support for dynamic frontend ports.

    Allows Vite dev server on ports 5173-5180 (common fallback range).
    Backend port can also vary, so we include a range.

    Returns:
        List of allowed CORS origins
    """
    origins = []

    # Backend ports (3000-3010)
    for port in range(3000, 3011):
        origins.extend([
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ])

    # Frontend ports (5173-5180) - Vite's fallback range
    for port in range(5173, 5181):
        origins.extend([
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ])

    return origins


@dataclass
class WebConfig:
    """Configuration for the GAO-Dev web server.

    Attributes:
        host: Server host (default: 127.0.0.1 for localhost only)
        port: Server port (default: 3000)
        auto_open: Auto-open browser on startup (default: True)
        cors_origins: Allowed CORS origins (default: localhost with port ranges)
        frontend_dist_path: Path to frontend build directory

    Environment Variables:
        WEB_HOST: Override server host (default: 127.0.0.1)
        WEB_PORT: Override server port (default: 3000)
        WEB_AUTO_OPEN_BROWSER: Auto-open browser (default: true)
    """

    host: str = field(default_factory=lambda: os.getenv("WEB_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("WEB_PORT", "3000")))
    auto_open: bool = field(
        default_factory=lambda: os.getenv("WEB_AUTO_OPEN_BROWSER", "true").lower() == "true"
    )
    cors_origins: List[str] = field(default_factory=_get_cors_origins)
    frontend_dist_path: str = field(default_factory=_get_default_frontend_dist_path)

    def get_url(self) -> str:
        """Get the full server URL."""
        return f"http://{self.host}:{self.port}"
