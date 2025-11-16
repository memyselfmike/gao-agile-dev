"""Unit tests for ReadOnlyMiddleware."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gao_dev.core.session_lock import SessionLock
from gao_dev.web.middleware import ReadOnlyMiddleware


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir()
    return tmp_path


@pytest.fixture
def app(temp_project):
    """Create test FastAPI app with middleware."""
    app = FastAPI()

    # Add middleware
    app.add_middleware(ReadOnlyMiddleware)

    # Create session lock
    session_lock = SessionLock(temp_project)
    app.state.session_lock = session_lock

    # Test endpoints
    @app.get("/api/test")
    async def get_test():
        return {"message": "GET success"}

    @app.post("/api/test")
    async def post_test():
        return {"message": "POST success"}

    @app.put("/api/test")
    async def put_test():
        return {"message": "PUT success"}

    @app.patch("/api/test")
    async def patch_test():
        return {"message": "PATCH success"}

    @app.delete("/api/test")
    async def delete_test():
        return {"message": "DELETE success"}

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestReadOnlyMiddleware:
    """Test ReadOnlyMiddleware behavior."""

    def test_get_request_always_allowed(self, client):
        """Test GET requests always allowed."""
        response = client.get("/api/test")
        assert response.status_code == 200
        assert response.json() == {"message": "GET success"}

    def test_head_request_always_allowed(self, client):
        """Test HEAD requests always allowed (even if endpoint doesn't support HEAD)."""
        response = client.head("/api/test")
        # HEAD is allowed by middleware, but endpoint might not support it (405)
        # The key is middleware doesn't block it with 423
        assert response.status_code in [200, 405]

    def test_options_request_always_allowed(self, client):
        """Test OPTIONS requests always allowed."""
        response = client.options("/api/test")
        # OPTIONS returns 200 or 405 depending on endpoint definition
        assert response.status_code in [200, 405]

    def test_post_allowed_when_no_lock(self, client, app):
        """Test POST allowed when no write lock exists."""
        # No lock held
        response = client.post("/api/test")
        assert response.status_code == 200
        assert response.json() == {"message": "POST success"}

    def test_post_allowed_when_we_hold_lock(self, client, app):
        """Test POST allowed when we hold write lock."""
        # Acquire write lock
        app.state.session_lock.acquire("web", mode="write")

        response = client.post("/api/test")
        assert response.status_code == 200
        assert response.json() == {"message": "POST success"}

    def test_post_rejected_when_other_holds_lock(self, client, app):
        """Test POST rejected when another process holds write lock."""
        # Create lock file with different PID
        import json
        import os

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,  # Different PID
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = client.post("/api/test")
            assert response.status_code == 423  # Locked
            data = response.json()
            assert "Session locked by CLI" in data["error"]
            assert data["mode"] == "read-only"
            assert "Exit CLI session" in data["message"]

    def test_put_rejected_when_locked(self, client, app):
        """Test PUT rejected when locked."""
        import json

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = client.put("/api/test")
            assert response.status_code == 423

    def test_patch_rejected_when_locked(self, client, app):
        """Test PATCH rejected when locked."""
        import json

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = client.patch("/api/test")
            assert response.status_code == 423

    def test_delete_rejected_when_locked(self, client, app):
        """Test DELETE rejected when locked."""
        import json

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = client.delete("/api/test")
            assert response.status_code == 423

    def test_graceful_degradation_when_lock_not_initialized(self):
        """Test middleware gracefully degrades when lock not initialized."""
        app = FastAPI()
        app.add_middleware(ReadOnlyMiddleware)

        @app.post("/api/test")
        async def post_test():
            return {"message": "POST success"}

        # Don't initialize session_lock in app.state
        client = TestClient(app)

        # Should allow request (graceful degradation)
        response = client.post("/api/test")
        assert response.status_code == 200

    def test_error_response_format(self, client, app):
        """Test error response has correct format."""
        import json

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=True):
            response = client.post("/api/test")
            data = response.json()

            # Verify all required fields
            assert "error" in data
            assert "mode" in data
            assert "message" in data
            assert data["mode"] == "read-only"

    def test_stale_lock_allows_write(self, client, app):
        """Test write operations allowed when lock is stale."""
        import json

        lock_data = {
            "interface": "cli",
            "mode": "write",
            "pid": 99999,  # Dead process
            "timestamp": "2025-01-01T00:00:00",
        }
        app.state.session_lock.lock_file.write_text(json.dumps(lock_data))

        with patch("psutil.pid_exists", return_value=False):
            # Stale lock should not block
            response = client.post("/api/test")
            assert response.status_code == 200
            assert response.json() == {"message": "POST success"}
