"""Detect Claude CLI installation for programmatic execution."""

import os
import shutil
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()


def find_claude_cli() -> Optional[Path]:
    """
    Find Claude CLI executable.

    Checks locations in priority order:
    1. 'claude' or 'claude.bat' in PATH
    2. VS Code extension directory
    3. Common installation locations

    Returns:
        Path to Claude CLI or None if not found
    """
    # Try PATH first
    if os.name == 'nt':  # Windows
        claude_cmd = shutil.which('claude.bat') or shutil.which('claude.cmd')
    else:  # Unix
        claude_cmd = shutil.which('claude')

    if claude_cmd:
        logger.debug("found_claude_cli_in_path", path=claude_cmd)
        return Path(claude_cmd)

    # Try VS Code extension directory
    home = Path.home()
    vscode_ext = home / '.vscode' / 'extensions'

    if vscode_ext.exists():
        # Find latest anthropic.claude-code extension
        claude_dirs = sorted(vscode_ext.glob('anthropic.claude-code-*'))
        if claude_dirs:
            cli_js = claude_dirs[-1] / 'resources' / 'claude-code' / 'cli.js'
            if cli_js.exists():
                logger.debug("found_claude_cli_in_vscode", path=str(cli_js))
                return cli_js

    # Try common locations (Windows)
    if os.name == 'nt':
        common_paths = [
            Path(os.environ.get('USERPROFILE', '')) / 'bin' / 'claude.bat',
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'claude' / 'claude.bat',
        ]
        for path in common_paths:
            if path.exists():
                logger.debug("found_claude_cli_common", path=str(path))
                return path

    logger.warning("claude_cli_not_found")
    return None


def validate_claude_cli(cli_path: Path) -> bool:
    """
    Validate that Claude CLI path is executable.

    Args:
        cli_path: Path to Claude CLI

    Returns:
        True if CLI is valid and executable
    """
    if not cli_path.exists():
        logger.error("claude_cli_not_exists", path=str(cli_path))
        return False

    # For .js files, check if they exist (will be run via node)
    if cli_path.suffix == '.js':
        return True

    # For .bat/.cmd files on Windows, check existence
    if os.name == 'nt' and cli_path.suffix in ['.bat', '.cmd']:
        return True

    # For Unix executables, check if executable
    if os.name != 'nt':
        if not os.access(cli_path, os.X_OK):
            logger.error("claude_cli_not_executable", path=str(cli_path))
            return False

    return True
