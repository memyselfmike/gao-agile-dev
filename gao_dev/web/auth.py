"""Session token authentication for WebSocket connections."""

import secrets
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class SessionTokenManager:
    """Manages session token authentication for WebSocket connections.

    The session token is generated on server startup and stored in
    .gao-dev/session.token for CLI access. This provides simple
    authentication for localhost-only deployments.

    Attributes:
        token: The current session token
        token_file: Path to token storage file
    """

    def __init__(self, token_file: Optional[Path] = None):
        """Initialize session token manager.

        Args:
            token_file: Path to store token (default: .gao-dev/session.token)
        """
        self.token_file = token_file or Path.cwd() / ".gao-dev" / "session.token"
        self.token: str = ""

        # Generate or load token
        self._initialize_token()

    def _initialize_token(self) -> None:
        """Initialize or load session token."""
        # Try to load existing token
        if self.token_file.exists():
            try:
                self.token = self.token_file.read_text().strip()
                logger.info("session_token_loaded", token_file=str(self.token_file))
                return
            except Exception as e:
                logger.warning(
                    "failed_to_load_session_token",
                    token_file=str(self.token_file),
                    error=str(e),
                )

        # Generate new token (in memory only)
        self.token = secrets.token_urlsafe(32)
        logger.info("session_token_generated", token_length=len(self.token))

        # Only store token if .gao-dev directory already exists
        # This prevents creating .gao-dev prematurely during module imports
        if self.token_file.parent.exists():
            try:
                self.token_file.write_text(self.token)
                logger.info("session_token_stored", token_file=str(self.token_file))
            except Exception as e:
                logger.warning(
                    "failed_to_store_session_token",
                    token_file=str(self.token_file),
                    error=str(e),
                )
        else:
            logger.debug(
                "session_token_not_stored",
                reason="gao_dev_directory_not_exists",
                token_file=str(self.token_file),
            )

    def ensure_persisted(self) -> None:
        """Ensure token is persisted to disk.

        Call this when the server is actually starting to make sure
        the token file is created (e.g., during initialization phase).
        """
        if not self.token_file.exists() and self.token:
            try:
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                self.token_file.write_text(self.token)
                logger.info("session_token_persisted", token_file=str(self.token_file))
            except Exception as e:
                logger.warning(
                    "failed_to_persist_session_token",
                    token_file=str(self.token_file),
                    error=str(e),
                )

    def validate(self, token: Optional[str]) -> bool:
        """Validate a session token.

        Args:
            token: Token to validate

        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            logger.debug("token_validation_failed", reason="missing_token")
            return False

        is_valid = secrets.compare_digest(token, self.token)

        if not is_valid:
            logger.debug("token_validation_failed", reason="token_mismatch")

        return is_valid

    def regenerate(self) -> str:
        """Regenerate the session token.

        This invalidates all existing connections.

        Returns:
            The new session token
        """
        old_token_prefix = self.token[:8] if self.token else "none"
        self.token = secrets.token_urlsafe(32)

        # Store new token
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            self.token_file.write_text(self.token)
            logger.info(
                "session_token_regenerated",
                old_token_prefix=old_token_prefix,
                token_file=str(self.token_file),
            )
        except Exception as e:
            logger.error(
                "failed_to_store_regenerated_token",
                token_file=str(self.token_file),
                error=str(e),
            )

        return self.token

    def get_token(self) -> str:
        """Get the current session token.

        Returns:
            Current session token
        """
        return self.token
