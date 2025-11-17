"""Tests for settings API endpoints.

Story 39.28: Provider Selection Settings Panel
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from fastapi.testclient import TestClient

from gao_dev.web.server import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Create test client with temporary .gao-dev directory.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Configured test client
    """
    # Create .gao-dev directory
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)

    # Change to temp directory for test
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    app = create_app()
    client = TestClient(app)

    yield client

    # Restore original directory
    os.chdir(original_cwd)


@pytest.fixture
def preferences_file(tmp_path: Path) -> Path:
    """Create provider preferences file.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to preferences file
    """
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)
    prefs_file = gao_dev_dir / "provider_preferences.yaml"
    return prefs_file


def test_get_provider_settings_defaults(client: TestClient) -> None:
    """Test GET /api/settings/provider returns defaults when no preferences exist.

    AC5: Provider dropdown displays three options
    AC6: Model dropdown filtered by provider
    """
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "current_provider" in data
    assert "current_model" in data
    assert "available_providers" in data

    # Check defaults
    assert data["current_provider"] == "claude_code"
    assert data["current_model"] == "claude-sonnet-4-5-20250929"

    # Check available providers (AC5)
    providers = data["available_providers"]
    assert len(providers) == 3

    provider_ids = [p["id"] for p in providers]
    assert "claude_code" in provider_ids
    assert "opencode" in provider_ids
    assert "ollama" in provider_ids

    # Check Claude Code provider (AC6)
    claude_provider = next(p for p in providers if p["id"] == "claude_code")
    assert claude_provider["name"] == "Claude Code"
    assert "description" in claude_provider
    assert "models" in claude_provider
    assert len(claude_provider["models"]) == 3

    # Check model structure
    first_model = claude_provider["models"][0]
    assert "id" in first_model
    assert "name" in first_model
    assert "description" in first_model


def test_get_provider_settings_with_preferences(
    client: TestClient, preferences_file: Path
) -> None:
    """Test GET /api/settings/provider returns saved preferences.

    AC7: Current provider and model shown at top of panel
    """
    # Create preferences file
    prefs = {
        "provider": "ollama",
        "model": "deepseek-r1",
    }
    with open(preferences_file, "w", encoding="utf-8") as f:
        yaml.dump(prefs, f)

    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    # Check saved preferences are returned (AC7)
    assert data["current_provider"] == "ollama"
    assert data["current_model"] == "deepseek-r1"


def test_get_provider_settings_invalid_yaml(
    client: TestClient, preferences_file: Path
) -> None:
    """Test GET /api/settings/provider handles invalid YAML gracefully."""
    # Write invalid YAML
    with open(preferences_file, "w", encoding="utf-8") as f:
        f.write("invalid: yaml: content: {{broken")

    response = client.get("/api/settings/provider")

    # Should still return 200 with defaults (graceful degradation)
    assert response.status_code == 200
    data = response.json()

    # Should fall back to defaults
    assert data["current_provider"] == "claude_code"
    assert data["current_model"] == "claude-sonnet-4-5-20250929"


def test_provider_has_icon(client: TestClient) -> None:
    """Test providers include icon identifiers.

    AC13: Provider dropdown shows provider logos/icons
    """
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    providers = data["available_providers"]

    # Check each provider has an icon
    for provider in providers:
        assert "icon" in provider
        assert provider["icon"] in ["sparkles", "globe", "server"]


def test_model_has_description(client: TestClient) -> None:
    """Test models include descriptions for tooltips.

    AC14: Model dropdown shows model descriptions (tooltips)
    """
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    # Check Claude Code models have descriptions
    claude_provider = next(
        p for p in data["available_providers"] if p["id"] == "claude_code"
    )

    for model in claude_provider["models"]:
        assert "description" in model
        assert len(model["description"]) > 0


def test_openrouter_models_returned(client: TestClient) -> None:
    """Test OpenRouter provider returns models.

    AC6: Model dropdown filtered by provider (OpenCode models)
    """
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    opencode_provider = next(
        p for p in data["available_providers"] if p["id"] == "opencode"
    )

    # Should have at least some models
    assert len(opencode_provider["models"]) > 0

    # Check model structure
    for model in opencode_provider["models"]:
        assert "id" in model
        assert "name" in model
        assert "description" in model


def test_ollama_models_returned(client: TestClient) -> None:
    """Test Ollama provider returns models.

    AC6: Model dropdown filtered by provider (Ollama models)
    """
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    ollama_provider = next(
        p for p in data["available_providers"] if p["id"] == "ollama"
    )

    # Should have at least some models (fallback list)
    assert len(ollama_provider["models"]) > 0

    # Check for common models (may have tags like :8b)
    model_ids = [m["id"] for m in ollama_provider["models"]]
    has_deepseek = any("deepseek-r1" in mid for mid in model_ids)
    has_llama = any("llama2" in mid for mid in model_ids)
    assert has_deepseek or has_llama, f"Expected deepseek-r1 or llama2 in {model_ids}"


def test_response_json_structure(client: TestClient) -> None:
    """Test response follows expected JSON structure."""
    response = client.get("/api/settings/provider")

    assert response.status_code == 200
    data = response.json()

    # Validate complete structure
    assert isinstance(data["current_provider"], str)
    assert isinstance(data["current_model"], str)
    assert isinstance(data["available_providers"], list)

    for provider in data["available_providers"]:
        assert isinstance(provider["id"], str)
        assert isinstance(provider["name"], str)
        assert isinstance(provider["description"], str)
        assert isinstance(provider["models"], list)

        for model in provider["models"]:
            assert isinstance(model["id"], str)
            assert isinstance(model["name"], str)
