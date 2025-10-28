"""Environment configuration loader for GAO-Dev.

Loads configuration from .env file and environment variables.
Priority: CLI arguments > .env file > environment variables
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import structlog


logger = structlog.get_logger()


class EnvConfig:
    """
    Manages environment configuration for GAO-Dev.

    Loads from .env file in project root and provides access to
    configuration values with proper fallback chain.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize environment config.

        Args:
            project_root: Path to project root (default: auto-detect)
        """
        self.project_root = project_root or self._find_project_root()
        self.env_file = self.project_root / ".env"
        self._loaded = False
        self.logger = logger.bind(component="EnvConfig")

    def _find_project_root(self) -> Path:
        """
        Find project root by looking for pyproject.toml.

        Returns:
            Path to project root
        """
        current = Path(__file__).resolve()

        # Walk up directory tree looking for pyproject.toml
        for parent in [current] + list(current.parents):
            if (parent / "pyproject.toml").exists():
                return parent

        # Fallback to current directory
        return Path.cwd()

    def load(self) -> None:
        """
        Load environment variables from .env file.

        Only loads once, subsequent calls are no-ops.
        """
        if self._loaded:
            return

        if self.env_file.exists():
            load_dotenv(self.env_file)
            self.logger.info("env_config_loaded", env_file=str(self.env_file))
        else:
            self.logger.debug(
                "no_env_file_found",
                env_file=str(self.env_file),
                note="Using environment variables only"
            )

        self._loaded = True

    def get_anthropic_api_key(self, cli_arg: Optional[str] = None) -> Optional[str]:
        """
        Get Anthropic API key with fallback chain.

        Priority:
        1. CLI argument (if provided)
        2. .env file ANTHROPIC_API_KEY
        3. Environment variable ANTHROPIC_API_KEY

        Args:
            cli_arg: API key from CLI argument (highest priority)

        Returns:
            API key string or None if not found
        """
        self.load()

        # Priority 1: CLI argument
        if cli_arg:
            self.logger.debug("using_api_key_from_cli_arg")
            return cli_arg

        # Priority 2 & 3: .env file or environment variable
        # (load_dotenv doesn't override existing env vars, so this covers both)
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if api_key:
            source = "env_file" if self.env_file.exists() else "environment"
            self.logger.debug("using_api_key_from", source=source)
            return api_key

        self.logger.warning("no_api_key_found")
        return None

    def get_sandbox_root(self, cli_arg: Optional[str] = None) -> Path:
        """
        Get sandbox root directory.

        Args:
            cli_arg: Sandbox root from CLI argument

        Returns:
            Path to sandbox root
        """
        self.load()

        if cli_arg:
            return Path(cli_arg)

        sandbox_root = os.getenv("SANDBOX_ROOT")
        if sandbox_root:
            return Path(sandbox_root)

        # Default to ./sandbox relative to project root
        return self.project_root / "sandbox"

    def get_metrics_output_dir(self, cli_arg: Optional[str] = None) -> Path:
        """
        Get metrics output directory.

        Args:
            cli_arg: Metrics dir from CLI argument

        Returns:
            Path to metrics output directory
        """
        self.load()

        if cli_arg:
            return Path(cli_arg)

        metrics_dir = os.getenv("METRICS_OUTPUT_DIR")
        if metrics_dir:
            return Path(metrics_dir)

        # Default to sandbox/metrics
        return self.get_sandbox_root() / "metrics"

    def get_benchmark_timeout(self, cli_arg: Optional[int] = None) -> int:
        """
        Get default benchmark timeout in seconds.

        Args:
            cli_arg: Timeout from CLI argument

        Returns:
            Timeout in seconds
        """
        self.load()

        if cli_arg is not None:
            return cli_arg

        timeout = os.getenv("BENCHMARK_TIMEOUT_SECONDS")
        if timeout:
            try:
                return int(timeout)
            except ValueError:
                self.logger.warning(
                    "invalid_benchmark_timeout",
                    value=timeout,
                    using_default=14400
                )

        # Default: 4 hours
        return 14400

    def is_debug_enabled(self) -> bool:
        """
        Check if debug logging is enabled.

        Returns:
            True if debug logging enabled
        """
        self.load()

        debug = os.getenv("GAO_DEV_DEBUG", "false").lower()
        return debug in ("true", "1", "yes", "on")


# Singleton instance
_env_config: Optional[EnvConfig] = None


def get_env_config(project_root: Optional[Path] = None) -> EnvConfig:
    """
    Get singleton EnvConfig instance.

    Args:
        project_root: Path to project root (only used on first call)

    Returns:
        EnvConfig instance
    """
    global _env_config

    if _env_config is None:
        _env_config = EnvConfig(project_root)

    return _env_config
