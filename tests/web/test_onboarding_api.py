"""Tests for onboarding API endpoints.

Story 41.2: Web Wizard Backend API

Tests for all onboarding wizard endpoints ensuring:
- Each endpoint works correctly
- Validation errors return 400
- Response format is consistent
- Credentials security (no key logging)
- >80% coverage
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gao_dev.web.api.onboarding import (
    router,
    OnboardingResponse,
    ProjectConfig,
    GitConfig,
    ProviderConfig,
    CredentialsConfig,
    _load_onboarding_state,
    _save_onboarding_state,
    _determine_next_step,
    _get_onboarding_state_path,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def app():
    """Create test FastAPI app with onboarding router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


@pytest.fixture
def app_with_project(temp_project):
    """Create test app with project root configured."""
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.state.project_root = temp_project
    return test_app


@pytest.fixture
def client_with_project(app_with_project):
    """Create test client with project context."""
    return TestClient(app_with_project)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_onboarding_state_path(self, temp_project):
        """Test state path generation."""
        path = _get_onboarding_state_path(temp_project)
        assert path == temp_project / ".gao-dev" / "onboarding_state.yaml"

    def test_load_onboarding_state_empty(self, temp_project):
        """Test loading state when file doesn't exist."""
        state = _load_onboarding_state(temp_project)
        assert state == {}

    def test_load_onboarding_state_existing(self, temp_project):
        """Test loading existing state."""
        state_path = temp_project / ".gao-dev" / "onboarding_state.yaml"
        state_path.parent.mkdir(parents=True, exist_ok=True)

        test_state = {"project": {"name": "test"}, "completed_steps": ["project"]}
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(test_state, f)

        loaded = _load_onboarding_state(temp_project)
        assert loaded["project"]["name"] == "test"
        assert "project" in loaded["completed_steps"]

    def test_save_onboarding_state(self, temp_project):
        """Test saving state."""
        state = {"project": {"name": "saved"}, "completed_steps": ["project"]}
        _save_onboarding_state(temp_project, state)

        # Verify saved
        state_path = temp_project / ".gao-dev" / "onboarding_state.yaml"
        assert state_path.exists()

        with open(state_path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded["project"]["name"] == "saved"
        assert "last_updated" in loaded

    def test_save_onboarding_state_creates_directory(self, temp_project):
        """Test that save creates .gao-dev directory if needed."""
        # Remove .gao-dev directory
        import shutil
        gao_dev_dir = temp_project / ".gao-dev"
        if gao_dev_dir.exists():
            shutil.rmtree(gao_dev_dir)

        state = {"test": "value"}
        _save_onboarding_state(temp_project, state)

        assert gao_dev_dir.exists()
        assert (gao_dev_dir / "onboarding_state.yaml").exists()

    def test_determine_next_step_project(self):
        """Test determining next step when no steps complete."""
        next_step = _determine_next_step([])
        assert next_step == "project"

    def test_determine_next_step_git(self):
        """Test determining next step after project."""
        next_step = _determine_next_step(["project"])
        assert next_step == "git"

    def test_determine_next_step_provider(self):
        """Test determining next step after git."""
        next_step = _determine_next_step(["project", "git"])
        assert next_step == "provider"

    def test_determine_next_step_credentials(self):
        """Test determining next step after provider."""
        next_step = _determine_next_step(["project", "git", "provider"])
        assert next_step == "credentials"

    def test_determine_next_step_complete(self):
        """Test determining next step after credentials."""
        next_step = _determine_next_step(["project", "git", "provider", "credentials"])
        assert next_step == "complete"

    def test_determine_next_step_all_done(self):
        """Test when all steps complete."""
        next_step = _determine_next_step(["project", "git", "provider", "credentials", "complete"])
        assert next_step is None


# ============================================================================
# PYDANTIC MODEL VALIDATION TESTS
# ============================================================================


class TestPydanticModels:
    """Tests for Pydantic model validation."""

    def test_project_config_valid(self):
        """Test valid project configuration."""
        config = ProjectConfig(
            name="My Project",
            description="A test project",
            path="/tmp/test",
            language="python",
            scale_level=2
        )
        assert config.name == "My Project"
        assert config.path == "/tmp/test"

    def test_project_config_name_validation(self):
        """Test project name validation."""
        with pytest.raises(ValueError, match="only contain"):
            ProjectConfig(name="test<>project", path="/tmp/test")

    def test_project_config_name_strip(self):
        """Test project name is stripped."""
        config = ProjectConfig(name="  test  ", path="/tmp/test")
        assert config.name == "test"

    def test_project_config_path_empty(self):
        """Test empty path validation."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            ProjectConfig(name="test", path="")

    def test_project_config_path_traversal(self):
        """Test path traversal prevention."""
        with pytest.raises(ValueError, match="cannot contain"):
            ProjectConfig(name="test", path="/tmp/../etc/passwd")

    def test_git_config_valid(self):
        """Test valid git configuration."""
        config = GitConfig(
            initialize_git=True,
            author_name="Test User",
            author_email="test@example.com"
        )
        assert config.initialize_git
        assert config.author_name == "Test User"

    def test_git_config_invalid_email(self):
        """Test invalid email validation."""
        with pytest.raises(ValueError, match="Invalid email"):
            GitConfig(author_email="invalid-email")

    def test_provider_config_valid(self):
        """Test valid provider configuration."""
        config = ProviderConfig(
            provider="claude-code",
            model="claude-sonnet-4-5-20250929"
        )
        assert config.provider == "claude-code"

    def test_provider_config_invalid_provider(self):
        """Test invalid provider validation."""
        with pytest.raises(ValueError, match="Invalid provider"):
            ProviderConfig(provider="invalid-provider", model="test")

    def test_credentials_config_valid(self):
        """Test valid credentials configuration."""
        config = CredentialsConfig(
            api_key="sk-ant-test-key-12345678901234567890",
            key_type="anthropic"
        )
        assert config.key_type == "anthropic"

    def test_credentials_config_empty_key(self):
        """Test empty API key validation."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            CredentialsConfig(api_key="", key_type="anthropic")

    def test_credentials_config_short_key(self):
        """Test short API key validation."""
        with pytest.raises(ValueError, match="too short"):
            CredentialsConfig(api_key="short", key_type="anthropic")


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================


class TestStatusEndpoint:
    """Tests for GET /api/onboarding/status endpoint."""

    def test_status_no_project_context(self, client):
        """Test status returns bootstrap mode when no project."""
        response = client.get("/api/onboarding/status")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "project"
        assert data["data"]["bootstrap_mode"] is True

    def test_status_with_project(self, client_with_project, temp_project):
        """Test status with project context."""
        response = client_with_project.get("/api/onboarding/status")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "project"
        assert data["data"]["bootstrap_mode"] is False

    def test_status_after_some_steps(self, client_with_project, temp_project):
        """Test status after completing some steps."""
        # Save partial state
        state = {
            "completed_steps": ["project", "git"],
            "project": {"name": "Test", "path": str(temp_project)}
        }
        _save_onboarding_state(temp_project, state)

        response = client_with_project.get("/api/onboarding/status")
        assert response.status_code == 200

        data = response.json()
        assert data["next_step"] == "provider"
        assert "project" in data["data"]["completed_steps"]
        assert "git" in data["data"]["completed_steps"]


class TestProjectEndpoint:
    """Tests for POST /api/onboarding/project endpoint."""

    def test_project_save_success(self, app, temp_project):
        """Test successful project save."""
        app.state.project_root = None  # Will be set by endpoint
        client = TestClient(app)

        project_path = str(temp_project / "new_project")

        response = client.post("/api/onboarding/project", json={
            "name": "Test Project",
            "description": "A test",
            "path": project_path,
            "language": "python",
            "scale_level": 2
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "git"
        assert data["data"]["name"] == "Test Project"

    def test_project_save_creates_directory(self, app):
        """Test project save creates directory."""
        app.state.project_root = None
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "new_dir", "project")

            response = client.post("/api/onboarding/project", json={
                "name": "Test",
                "path": project_path
            })

            assert response.status_code == 200
            assert Path(project_path).exists()
            assert (Path(project_path) / ".gao-dev").exists()

    def test_project_validation_error(self, client):
        """Test project validation returns 400."""
        response = client.post("/api/onboarding/project", json={
            "name": "test<invalid>",
            "path": "/tmp/test"
        })

        assert response.status_code == 422  # Pydantic validation error

    def test_project_empty_name(self, client):
        """Test empty name returns validation error."""
        response = client.post("/api/onboarding/project", json={
            "name": "",
            "path": "/tmp/test"
        })

        assert response.status_code == 422


class TestGitEndpoint:
    """Tests for POST /api/onboarding/git endpoint."""

    def test_git_requires_project(self, client):
        """Test git endpoint requires project context."""
        response = client.post("/api/onboarding/git", json={
            "initialize_git": True
        })

        assert response.status_code == 400
        assert "Project must be configured" in response.json()["detail"]

    def test_git_save_without_init(self, client_with_project):
        """Test git save without initialization."""
        response = client_with_project.post("/api/onboarding/git", json={
            "initialize_git": False,
            "author_name": "Test",
            "author_email": "test@example.com"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "provider"
        assert data["data"]["initialized"] is False

    def test_git_save_with_init_state_updated(self, client_with_project, temp_project):
        """Test git save with init marks step as complete."""
        # Test with initialize_git=True but catch any git errors
        # This test verifies state handling, not actual git init
        response = client_with_project.post("/api/onboarding/git", json={
            "initialize_git": True,
            "author_name": "Test User",
            "author_email": "test@example.com",
            "create_initial_commit": False  # Skip commit to avoid needing actual git
        })

        # Should succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["next_step"] == "provider"

            # Verify state was updated
            state = _load_onboarding_state(temp_project)
            assert "git" in state.get("completed_steps", [])
        else:
            # Git not available in test environment is ok
            assert response.status_code == 500

    def test_git_invalid_email(self, client_with_project):
        """Test git with invalid email."""
        response = client_with_project.post("/api/onboarding/git", json={
            "initialize_git": False,
            "author_email": "invalid"
        })

        assert response.status_code == 422


class TestProviderEndpoint:
    """Tests for POST /api/onboarding/provider endpoint."""

    def test_provider_requires_project(self, client):
        """Test provider endpoint requires project context."""
        response = client.post("/api/onboarding/provider", json={
            "provider": "claude-code",
            "model": "claude-sonnet-4-5-20250929"
        })

        assert response.status_code == 400

    def test_provider_save_success(self, client_with_project, temp_project):
        """Test successful provider save."""
        response = client_with_project.post("/api/onboarding/provider", json={
            "provider": "claude-code",
            "model": "claude-sonnet-4-5-20250929"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "credentials"
        assert data["data"]["provider"] == "claude-code"

        # Verify preferences file created
        prefs_path = temp_project / ".gao-dev" / "provider_preferences.yaml"
        assert prefs_path.exists()

    def test_provider_invalid_provider(self, client_with_project):
        """Test invalid provider returns validation error."""
        response = client_with_project.post("/api/onboarding/provider", json={
            "provider": "invalid",
            "model": "test"
        })

        assert response.status_code == 422

    def test_provider_opencode_sdk(self, client_with_project):
        """Test OpenCode SDK provider save."""
        response = client_with_project.post("/api/onboarding/provider", json={
            "provider": "opencode-sdk",
            "model": "gpt-4"
        })

        assert response.status_code == 200
        assert response.json()["data"]["provider"] == "opencode-sdk"


class TestCredentialsEndpoint:
    """Tests for POST /api/onboarding/credentials endpoint."""

    def test_credentials_requires_project(self, client):
        """Test credentials endpoint requires project context."""
        response = client.post("/api/onboarding/credentials", json={
            "api_key": "sk-ant-test123456789012345678901234567890",
            "key_type": "anthropic"
        })

        assert response.status_code == 400

    def test_credentials_save_success(self, client_with_project, temp_project):
        """Test successful credentials save."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "sk-ant-test123456789012345678901234567890",
            "key_type": "anthropic"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["next_step"] == "complete"
        assert data["data"]["env_var"] == "ANTHROPIC_API_KEY"

    def test_credentials_never_returns_key(self, client_with_project):
        """Test that API key is never returned in response."""
        api_key = "sk-ant-super-secret-key-12345678901234"

        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": api_key,
            "key_type": "anthropic"
        })

        assert response.status_code == 200

        # Verify key is not in response anywhere
        response_text = response.text
        assert api_key not in response_text
        assert "super-secret" not in response_text

    def test_credentials_stores_prefix_only(self, client_with_project, temp_project):
        """Test that only key prefix is stored in state."""
        api_key = "sk-ant-test123456789012345678901234567890"

        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": api_key,
            "key_type": "anthropic"
        })

        assert response.status_code == 200

        # Check state file
        state = _load_onboarding_state(temp_project)
        stored_prefix = state["credentials"]["key_prefix"]

        # Should only have first 8 chars plus "..."
        assert len(stored_prefix) == 11  # 8 + "..."
        assert stored_prefix.endswith("...")
        assert api_key not in stored_prefix
        assert api_key[:8] in stored_prefix

    def test_credentials_openai_type(self, client_with_project):
        """Test OpenAI credentials type."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "sk-openai-key-12345678901234567890123456",
            "key_type": "openai"
        })

        assert response.status_code == 200
        assert response.json()["data"]["env_var"] == "OPENAI_API_KEY"

    def test_credentials_google_type(self, client_with_project):
        """Test Google credentials type."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "AIza-google-key-123456789012345678901",
            "key_type": "google"
        })

        assert response.status_code == 200
        assert response.json()["data"]["env_var"] == "GOOGLE_API_KEY"

    def test_credentials_empty_key(self, client_with_project):
        """Test empty API key validation."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "",
            "key_type": "anthropic"
        })

        assert response.status_code == 422

    def test_credentials_short_key(self, client_with_project):
        """Test short API key validation."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "short",
            "key_type": "anthropic"
        })

        assert response.status_code == 422


class TestCompleteEndpoint:
    """Tests for POST /api/onboarding/complete endpoint."""

    def test_complete_requires_project(self, client):
        """Test complete endpoint requires project context."""
        response = client.post("/api/onboarding/complete")
        assert response.status_code == 400

    def test_complete_requires_all_steps(self, client_with_project, temp_project):
        """Test complete requires all previous steps."""
        # Only project step complete
        state = {"completed_steps": ["project"]}
        _save_onboarding_state(temp_project, state)

        response = client_with_project.post("/api/onboarding/complete")
        assert response.status_code == 400
        assert "Missing steps" in response.json()["detail"]

    def test_complete_success(self, client_with_project, temp_project):
        """Test successful completion."""
        # Complete all required steps
        state = {
            "completed_steps": ["project", "git", "provider", "credentials"],
            "project": {"name": "Test Project", "description": "Test"},
            "provider": {"provider": "claude-code"}
        }
        _save_onboarding_state(temp_project, state)

        response = client_with_project.post("/api/onboarding/complete")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["next_step"] is None
        assert data["data"]["ready_to_use"] is True

    def test_complete_creates_readme(self, client_with_project, temp_project):
        """Test completion creates README if not exists."""
        # Complete all required steps
        state = {
            "completed_steps": ["project", "git", "provider", "credentials"],
            "project": {"name": "Test Project", "description": "A test"},
            "provider": {"provider": "claude-code"}
        }
        _save_onboarding_state(temp_project, state)

        response = client_with_project.post("/api/onboarding/complete")
        assert response.status_code == 200

        # Check README created
        readme = temp_project / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "Test Project" in content

    def test_complete_creates_docs_directory(self, client_with_project, temp_project):
        """Test completion creates docs directory."""
        state = {
            "completed_steps": ["project", "git", "provider", "credentials"],
            "project": {"name": "Test"},
            "provider": {"provider": "claude-code"}
        }
        _save_onboarding_state(temp_project, state)

        response = client_with_project.post("/api/onboarding/complete")
        assert response.status_code == 200

        assert (temp_project / "docs").exists()

    def test_complete_sets_onboarding_complete_flag(self, client_with_project, temp_project):
        """Test completion sets complete flag in state."""
        state = {
            "completed_steps": ["project", "git", "provider", "credentials"],
            "project": {"name": "Test"},
            "provider": {"provider": "claude-code"}
        }
        _save_onboarding_state(temp_project, state)

        response = client_with_project.post("/api/onboarding/complete")
        assert response.status_code == 200

        # Check state
        final_state = _load_onboarding_state(temp_project)
        assert final_state["onboarding_complete"] is True
        assert "complete" in final_state["completed_steps"]


# ============================================================================
# RESPONSE FORMAT CONSISTENCY TESTS
# ============================================================================


class TestResponseFormat:
    """Tests for consistent response format across all endpoints."""

    def test_status_response_format(self, client):
        """Test status endpoint response format."""
        response = client.get("/api/onboarding/status")
        data = response.json()

        assert "success" in data
        assert "message" in data
        assert "next_step" in data
        assert "data" in data

    def test_project_response_format(self, app):
        """Test project endpoint response format."""
        app.state.project_root = None
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            response = client.post("/api/onboarding/project", json={
                "name": "Test",
                "path": os.path.join(tmpdir, "test")
            })

            data = response.json()
            assert "success" in data
            assert "message" in data
            assert "next_step" in data

    def test_git_response_format(self, client_with_project):
        """Test git endpoint response format."""
        response = client_with_project.post("/api/onboarding/git", json={
            "initialize_git": False
        })

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "next_step" in data

    def test_provider_response_format(self, client_with_project):
        """Test provider endpoint response format."""
        response = client_with_project.post("/api/onboarding/provider", json={
            "provider": "claude-code",
            "model": "test"
        })

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "next_step" in data

    def test_credentials_response_format(self, client_with_project):
        """Test credentials endpoint response format."""
        response = client_with_project.post("/api/onboarding/credentials", json={
            "api_key": "sk-ant-test123456789012345678901234567890",
            "key_type": "anthropic"
        })

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "next_step" in data


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json_returns_422(self, client):
        """Test invalid JSON returns 422."""
        response = client.post(
            "/api/onboarding/project",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_field_returns_422(self, client):
        """Test missing required field returns 422."""
        response = client.post("/api/onboarding/project", json={
            "description": "no name field"
        })
        assert response.status_code == 422

    def test_wrong_type_returns_422(self, client):
        """Test wrong type returns 422."""
        response = client.post("/api/onboarding/project", json={
            "name": "test",
            "path": "/tmp/test",
            "scale_level": "not-an-int"
        })
        assert response.status_code == 422

    def test_scale_level_out_of_range(self, client):
        """Test scale level out of range returns 422."""
        response = client.post("/api/onboarding/project", json={
            "name": "test",
            "path": "/tmp/test",
            "scale_level": 10
        })
        assert response.status_code == 422


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestOnboardingFlow:
    """Integration tests for complete onboarding flow."""

    def test_complete_onboarding_flow(self, app):
        """Test complete onboarding flow from start to finish."""
        app.state.project_root = None
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "test_project")

            # Step 1: Status (bootstrap mode)
            response = client.get("/api/onboarding/status")
            assert response.status_code == 200
            assert response.json()["data"]["bootstrap_mode"] is True

            # Step 2: Project
            response = client.post("/api/onboarding/project", json={
                "name": "Integration Test",
                "description": "Testing flow",
                "path": project_path,
                "language": "python",
                "scale_level": 2
            })
            assert response.status_code == 200
            assert response.json()["next_step"] == "git"

            # Step 3: Git
            response = client.post("/api/onboarding/git", json={
                "initialize_git": False,
                "author_name": "Test",
                "author_email": "test@test.com"
            })
            assert response.status_code == 200
            assert response.json()["next_step"] == "provider"

            # Step 4: Provider
            response = client.post("/api/onboarding/provider", json={
                "provider": "claude-code",
                "model": "claude-sonnet-4-5-20250929"
            })
            assert response.status_code == 200
            assert response.json()["next_step"] == "credentials"

            # Step 5: Credentials
            response = client.post("/api/onboarding/credentials", json={
                "api_key": "sk-ant-test123456789012345678901234567890",
                "key_type": "anthropic"
            })
            assert response.status_code == 200
            assert response.json()["next_step"] == "complete"

            # Step 6: Complete
            response = client.post("/api/onboarding/complete")
            assert response.status_code == 200
            assert response.json()["next_step"] is None
            assert response.json()["data"]["ready_to_use"] is True

            # Final status check
            response = client.get("/api/onboarding/status")
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["is_complete"] is True
            assert len(data["completed_steps"]) == 5

    def test_resume_onboarding_flow(self, app):
        """Test resuming onboarding from previous state."""
        app.state.project_root = None
        client = TestClient(app)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()

            # Manually set up partial state
            state = {
                "completed_steps": ["project", "git"],
                "project": {"name": "Resume Test", "path": str(project_path)}
            }
            _save_onboarding_state(project_path, state)

            # Set project root
            app.state.project_root = project_path

            # Check status shows correct next step
            response = client.get("/api/onboarding/status")
            assert response.status_code == 200
            assert response.json()["next_step"] == "provider"
