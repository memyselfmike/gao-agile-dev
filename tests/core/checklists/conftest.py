"""Shared fixtures and utilities for checklist tests."""

import gc
import tempfile
import time
from pathlib import Path

import pytest


def safe_cleanup_db(db_path: Path, max_retries: int = 3):
    """Safely cleanup a database file, handling Windows file locking.

    Args:
        db_path: Path to database file to delete
        max_retries: Maximum number of retry attempts
    """
    gc.collect()  # Force garbage collection to close any lingering connections

    if not db_path.exists():
        return

    for i in range(max_retries):
        try:
            db_path.unlink()
            return
        except PermissionError:
            if i < max_retries - 1:
                # On Windows, wait progressively longer and try again
                time.sleep(0.2 * (i + 1))  # Progressive backoff: 0.2s, 0.4s, 0.6s
                gc.collect()
            else:
                # Last resort: ignore the error and let OS clean up temp files
                # This is acceptable for test teardown
                pass


@pytest.fixture
def tmp_path():
    """Provide a temporary directory for test databases with safe cleanup."""
    tmpdir = tempfile.mkdtemp()
    tmp_path = Path(tmpdir)

    yield tmp_path

    # Safe cleanup of any database files
    for db_file in tmp_path.glob("*.db"):
        safe_cleanup_db(db_file)

    # Clean up the temp directory
    try:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        # Ignore cleanup errors - OS will handle it
        pass
