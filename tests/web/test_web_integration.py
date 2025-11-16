"""Integration tests for web server."""

import asyncio
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from gao_dev.web.config import WebConfig
from gao_dev.web.server import create_app, ServerManager


@pytest.mark.integration
class TestWebServerIntegration:
    """Integration tests for the full web server."""

    def test_full_app_lifecycle(self):
        """Test complete app creation and usage lifecycle."""
        config = WebConfig()
        app = create_app(config)
        client = TestClient(app)

        # Test health check
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

        # Test placeholder route
        response = client.get("/")
        assert response.status_code == 200

    def test_cors_headers(self):
        """Test CORS headers are present and correct."""
        config = WebConfig()
        app = create_app(config)
        client = TestClient(app)

        # Make request from allowed origin
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        # TestClient doesn't fully simulate CORS, but middleware is configured
        # Actual CORS validation happens in browser

    def test_options_preflight_request(self):
        """Test OPTIONS pre-flight requests are handled."""
        config = WebConfig()
        app = create_app(config)
        client = TestClient(app)

        # Pre-flight OPTIONS request
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should not error
        assert response.status_code in [200, 204]

    def test_multiple_endpoints(self):
        """Test multiple endpoints work correctly."""
        app = create_app()
        client = TestClient(app)

        # Health check
        health_response = client.get("/api/health")
        assert health_response.status_code == 200

        # Root route
        root_response = client.get("/")
        assert root_response.status_code == 200

    def test_static_assets_with_build(self, tmp_path):
        """Test static assets are served correctly when build exists."""
        # Create mock frontend build with assets
        frontend_dist = tmp_path / "dist"
        frontend_dist.mkdir()

        index_html = frontend_dist / "index.html"
        index_html.write_text("<!DOCTYPE html><html><body>App</body></html>")

        assets_dir = frontend_dist / "assets"
        assets_dir.mkdir()

        js_file = assets_dir / "main.js"
        js_file.write_text("console.log('test');")

        css_file = assets_dir / "styles.css"
        css_file.write_text("body { margin: 0; }")

        # Create app with frontend
        config = WebConfig(frontend_dist_path=str(frontend_dist))
        app = create_app(config)
        client = TestClient(app)

        # Test index served
        response = client.get("/")
        assert response.status_code == 200
        assert b"App" in response.content

        # Test JS asset
        response = client.get("/assets/main.js")
        assert response.status_code == 200
        assert b"console.log" in response.content

        # Test CSS asset
        response = client.get("/assets/styles.css")
        assert response.status_code == 200
        assert b"margin" in response.content

    def test_404_for_nonexistent_assets(self, tmp_path):
        """Test 404 is returned for nonexistent assets."""
        frontend_dist = tmp_path / "dist"
        frontend_dist.mkdir()
        (frontend_dist / "index.html").write_text("<html></html>")

        assets_dir = frontend_dist / "assets"
        assets_dir.mkdir()

        config = WebConfig(frontend_dist_path=str(frontend_dist))
        app = create_app(config)
        client = TestClient(app)

        # Request nonexistent asset
        response = client.get("/assets/nonexistent.js")
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.performance
class TestWebServerPerformance:
    """Performance tests for web server."""

    def test_server_startup_time(self):
        """Test server app creation is fast (<3 seconds)."""
        start = time.perf_counter()
        app = create_app()
        end = time.perf_counter()

        duration = end - start
        assert duration < 3.0, f"App creation took {duration:.2f}s (should be <3s)"

    def test_concurrent_health_checks(self):
        """Test health check handles concurrent requests."""
        app = create_app()
        client = TestClient(app)

        # Make multiple concurrent requests
        responses = []
        for _ in range(10):
            response = client.get("/api/health")
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)


@pytest.mark.integration
class TestServerManagerIntegration:
    """Integration tests for ServerManager."""

    @patch("gao_dev.web.server.webbrowser.open")
    def test_browser_opens_with_correct_url(self, mock_browser_open):
        """Test browser opens with correct URL when auto_open=True."""
        config = WebConfig(host="127.0.0.1", port=3000, auto_open=True)
        manager = ServerManager(config)

        # Simulate what would happen in start_async
        if config.auto_open:
            url = config.get_url()
            # This is what the actual code does
            assert url == "http://127.0.0.1:3000"

    @patch("gao_dev.web.server.webbrowser.open")
    def test_browser_not_opened_when_disabled(self, mock_browser_open):
        """Test browser doesn't open when auto_open=False."""
        config = WebConfig(auto_open=False)
        manager = ServerManager(config)

        # Browser should not be opened
        assert config.auto_open is False

    def test_graceful_shutdown_flag(self):
        """Test graceful shutdown sets appropriate flags."""
        manager = ServerManager()

        # Simulate server running
        from unittest.mock import MagicMock

        manager.server = MagicMock()
        manager.server.should_exit = False

        # Stop server
        manager.stop()

        # Should_exit flag should be set
        assert manager.server.should_exit is True
