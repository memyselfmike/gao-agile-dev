"""Unit tests for web configuration."""

import os
import pytest
from gao_dev.web.config import WebConfig


class TestWebConfig:
    """Tests for WebConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = WebConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 3000
        assert config.auto_open is True
        assert config.cors_origins == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        assert config.frontend_dist_path == "gao_dev/frontend/dist"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = WebConfig(
            host="0.0.0.0",
            port=8080,
            auto_open=False,
            cors_origins=["http://example.com"],
            frontend_dist_path="/custom/path",
        )

        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.auto_open is False
        assert config.cors_origins == ["http://example.com"]
        assert config.frontend_dist_path == "/custom/path"

    def test_environment_variables(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("WEB_HOST", "192.168.1.1")
        monkeypatch.setenv("WEB_PORT", "5000")
        monkeypatch.setenv("WEB_AUTO_OPEN_BROWSER", "false")

        config = WebConfig()

        assert config.host == "192.168.1.1"
        assert config.port == 5000
        assert config.auto_open is False

    def test_get_url(self):
        """Test get_url method."""
        config = WebConfig(host="127.0.0.1", port=3000)
        assert config.get_url() == "http://127.0.0.1:3000"

        config2 = WebConfig(host="localhost", port=8080)
        assert config2.get_url() == "http://localhost:8080"

    def test_environment_variables_override_defaults(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("WEB_PORT", "9000")

        config = WebConfig()
        assert config.port == 9000
        assert config.host == "127.0.0.1"  # Default remains

    def test_auto_open_browser_true_values(self, monkeypatch):
        """Test various true values for WEB_AUTO_OPEN_BROWSER."""
        for value in ["true", "True", "TRUE", "1", "yes"]:
            monkeypatch.setenv("WEB_AUTO_OPEN_BROWSER", value)
            config = WebConfig()
            # Only "true" (lowercase) should be True based on implementation
            assert config.auto_open == (value.lower() == "true")

    def test_auto_open_browser_false_values(self, monkeypatch):
        """Test various false values for WEB_AUTO_OPEN_BROWSER."""
        for value in ["false", "False", "FALSE", "0", "no"]:
            monkeypatch.setenv("WEB_AUTO_OPEN_BROWSER", value)
            config = WebConfig()
            assert config.auto_open is False
