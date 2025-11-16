"""Configuration for GAO-Dev web server."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class WebConfig:
    """Configuration for the GAO-Dev web server.

    Attributes:
        host: Server host (default: 127.0.0.1 for localhost only)
        port: Server port (default: 3000)
        auto_open: Auto-open browser on startup (default: True)
        cors_origins: Allowed CORS origins (default: localhost only)
        frontend_dist_path: Path to frontend build directory
    """

    host: str = field(default_factory=lambda: os.getenv("WEB_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("WEB_PORT", "3000")))
    auto_open: bool = field(
        default_factory=lambda: os.getenv("WEB_AUTO_OPEN_BROWSER", "true").lower() == "true"
    )
    cors_origins: List[str] = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    frontend_dist_path: str = "gao_dev/frontend/dist"

    def get_url(self) -> str:
        """Get the full server URL."""
        return f"http://{self.host}:{self.port}"
