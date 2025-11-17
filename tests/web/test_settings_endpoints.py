"""Tests for settings API endpoints.

Story 39.28: Provider Selection Settings Panel
Story 39.29: Provider Validation and Persistence
"""

import json
import os
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

from gao_dev.web.server import create_app
from gao_dev.web.provider_validator import WebValidationResult


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


# Story 39.29: Provider Validation and Persistence Tests


def test_validate_provider_endpoint_success(client: TestClient, monkeypatch) -> None:
    """Test GET /api/settings/provider/validate with valid provider.

    AC3: Real-time validation during typing (debounced 500ms)
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

    response = client.get(
        "/api/settings/provider/validate",
        params={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check validation result structure
    assert "valid" in data
    assert "api_key_status" in data
    assert "model_available" in data
    assert "warnings" in data

    # Should be valid
    assert data["valid"] is True
    assert data["api_key_status"] == "valid"


def test_validate_provider_endpoint_missing_api_key(
    client: TestClient, monkeypatch
) -> None:
    """Test validate endpoint with missing API key.

    AC2: API key validation displays status indicator
    AC5: Validation errors show specific fix suggestions
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.get(
        "/api/settings/provider/validate",
        params={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should fail validation
    assert data["valid"] is False
    assert data["api_key_status"] == "missing"
    assert data["error"] == "API key missing"
    assert "ANTHROPIC_API_KEY" in data["fix_suggestion"]


def test_save_provider_success(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    """Test POST /api/settings/provider saves successfully.

    AC6: Save writes to `.gao-dev/provider_preferences.yaml` atomically
    AC7: YAML structure matches Epic 35 format
    AC11: Success toast notification
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

    response = client.post(
        "/api/settings/provider",
        json={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check success response
    assert data["success"] is True
    assert data["provider"] == "claude_code"
    assert data["model"] == "claude-sonnet-4-5-20250929"
    assert "Provider changed to" in data["message"]

    # Check file was created (AC6)
    prefs_file = tmp_path / ".gao-dev" / "provider_preferences.yaml"
    assert prefs_file.exists()

    # Check YAML structure (AC7)
    with open(prefs_file, "r", encoding="utf-8") as f:
        saved_prefs = yaml.safe_load(f)

    assert saved_prefs["provider"] == "claude_code"
    assert saved_prefs["model"] == "claude-sonnet-4-5-20250929"
    assert "last_updated" in saved_prefs


def test_save_provider_validation_failure(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """Test save fails if validation fails.

    AC1: Provider + model combination validated before save
    AC12: Error toast notification with actionable message
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.post(
        "/api/settings/provider",
        json={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should fail
    assert data["success"] is False
    assert data["error"] == "API key missing"
    assert "ANTHROPIC_API_KEY" in data["fix_suggestion"]

    # Check validation details (AC1)
    assert "validation_details" in data
    assert data["validation_details"]["api_key_status"] == "missing"

    # File should NOT be created
    prefs_file = tmp_path / ".gao-dev" / "provider_preferences.yaml"
    assert not prefs_file.exists()


def test_save_provider_atomic_with_backup(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """Test atomic save creates backup before overwriting.

    AC6: Save writes atomically with backup
    AC9: Rollback on save failure
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

    # Create existing preferences file
    gao_dev_dir = tmp_path / ".gao-dev"
    gao_dev_dir.mkdir(parents=True, exist_ok=True)
    prefs_file = gao_dev_dir / "provider_preferences.yaml"

    original_prefs = {
        "provider": "ollama",
        "model": "llama2",
        "last_updated": "2025-01-01T00:00:00Z",
    }
    with open(prefs_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(original_prefs, f)

    # Save new preferences
    response = client.post(
        "/api/settings/provider",
        json={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    # Check new preferences saved
    with open(prefs_file, "r", encoding="utf-8") as f:
        saved_prefs = yaml.safe_load(f)

    assert saved_prefs["provider"] == "claude_code"
    assert saved_prefs["model"] == "claude-sonnet-4-5-20250929"

    # Backup should be deleted after successful save
    backup_file = gao_dev_dir / "provider_preferences.yaml.bak"
    assert not backup_file.exists()


def test_save_provider_invalid_model(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """Test save fails with invalid model.

    AC1: Provider + model combination validated before save
    AC4: Save button disabled if validation fails
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

    response = client.post(
        "/api/settings/provider",
        json={"provider": "claude_code", "model": "invalid-model"},
    )

    assert response.status_code == 200
    data = response.json()

    # Should fail
    assert data["success"] is False
    assert data["error"] == "Invalid model"
    assert data["validation_details"]["model_available"] is False

    # File should NOT be created
    prefs_file = tmp_path / ".gao-dev" / "provider_preferences.yaml"
    assert not prefs_file.exists()


def test_file_permissions_unix_only(
    client: TestClient, tmp_path: Path, monkeypatch
) -> None:
    """Test file permissions set to 0600 on Unix.

    AC8: File permissions set to 0600 (read/write owner only) for security
    """
    # Skip on Windows
    if os.name == "nt":
        pytest.skip("File permissions test skipped on Windows")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-valid-key")

    response = client.post(
        "/api/settings/provider",
        json={"provider": "claude_code", "model": "claude-sonnet-4-5-20250929"},
    )

    assert response.status_code == 200

    # Check file permissions
    prefs_file = tmp_path / ".gao-dev" / "provider_preferences.yaml"
    assert prefs_file.exists()

    # Check permissions are 0600
    stat_info = prefs_file.stat()
    permissions = oct(stat_info.st_mode)[-3:]
    assert permissions == "600"
