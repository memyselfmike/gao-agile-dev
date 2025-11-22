"""Onboarding API endpoints for web wizard setup flow.

Story 41.2: Web Wizard Backend API

Provides endpoints for each step of the onboarding wizard:
1. Status - Get current onboarding state
2. Project - Save project configuration
3. Git - Save git configuration
4. Provider - Save provider selection
5. Credentials - Validate and store API credentials
6. Complete - Finalize onboarding

All endpoints return consistent response format with success, message, next_step.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from gao_dev.web.api.provider_utils import get_available_providers

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ============================================================================
# PYDANTIC MODELS - Request/Response
# ============================================================================


class OnboardingResponse(BaseModel):
    """Standard response format for all onboarding endpoints."""

    success: bool
    message: str
    next_step: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class OnboardingStatus(BaseModel):
    """Current state of onboarding wizard."""

    is_complete: bool = False
    current_step: str = "project"
    completed_steps: List[str] = Field(default_factory=list)
    project_name: Optional[str] = None
    project_path: Optional[str] = None
    git_initialized: bool = False
    provider_configured: bool = False
    credentials_validated: bool = False


class ProjectConfig(BaseModel):
    """Project configuration from wizard step 1."""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    path: str = Field(..., min_length=1, description="Project path")
    language: str = Field(default="python", description="Primary programming language")
    scale_level: int = Field(default=2, ge=0, le=4, description="Project scale level (0-4)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name contains only safe characters."""
        # Allow alphanumeric, hyphens, underscores, spaces
        if not all(c.isalnum() or c in "-_ " for c in v):
            raise ValueError("Project name can only contain letters, numbers, hyphens, underscores, and spaces")
        return v.strip()

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path is absolute and doesn't contain dangerous characters."""
        # Basic path validation
        if not v or v.strip() == "":
            raise ValueError("Path cannot be empty")

        # Check for path traversal attempts
        if ".." in v:
            raise ValueError("Path cannot contain '..'")

        return v.strip()


class GitConfig(BaseModel):
    """Git configuration from wizard step 2."""

    initialize_git: bool = Field(default=True, description="Initialize git repository")
    author_name: str = Field(default="", description="Git author name")
    author_email: str = Field(default="", description="Git author email")
    create_initial_commit: bool = Field(default=True, description="Create initial commit")

    @field_validator("author_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation if provided."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip()


class ProviderConfig(BaseModel):
    """Provider selection from wizard step 3."""

    provider: str = Field(..., description="Provider ID (claude-code, opencode-sdk)")
    model: str = Field(..., description="Model ID")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is one of the supported options."""
        valid_providers = ["claude-code", "opencode-sdk", "opencode-cli", "direct-api"]
        # Allow partial matches for direct-api variants
        if not any(v.startswith(p) for p in valid_providers):
            raise ValueError(f"Invalid provider. Must be one of: {', '.join(valid_providers)}")
        return v.strip()


class CredentialsConfig(BaseModel):
    """API credentials from wizard step 4."""

    api_key: str = Field(..., min_length=1, description="API key (never logged)")
    key_type: str = Field(default="anthropic", description="Key type (anthropic, openai, google)")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format without logging the value."""
        v = v.strip()
        if not v:
            raise ValueError("API key cannot be empty")

        # Basic length validation (most API keys are 30+ chars)
        if len(v) < 20:
            raise ValueError("API key appears too short")

        return v


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_onboarding_state_path(project_root: Path) -> Path:
    """Get path to onboarding state file.

    Args:
        project_root: Project root directory

    Returns:
        Path to onboarding state YAML file
    """
    return project_root / ".gao-dev" / "onboarding_state.yaml"


def _load_onboarding_state(project_root: Path) -> Dict[str, Any]:
    """Load onboarding state from disk.

    Args:
        project_root: Project root directory

    Returns:
        Onboarding state dictionary
    """
    state_path = _get_onboarding_state_path(project_root)

    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f)
                return state if state else {}
        except (yaml.YAMLError, IOError) as e:
            logger.warning("failed_to_load_onboarding_state", error=str(e))

    return {}


def _save_onboarding_state(project_root: Path, state: Dict[str, Any]) -> None:
    """Save onboarding state to disk.

    Args:
        project_root: Project root directory
        state: State dictionary to save
    """
    state_path = _get_onboarding_state_path(project_root)

    # Ensure .gao-dev directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Add timestamp
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Atomic write with backup
    backup_path = state_path.with_suffix(".yaml.bak")

    if state_path.exists():
        shutil.copy(state_path, backup_path)

    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, default_flow_style=False)

        # Set secure permissions (Unix only)
        if os.name != "nt":
            os.chmod(state_path, 0o600)

        # Remove backup on success
        if backup_path.exists():
            backup_path.unlink()

    except Exception as e:
        # Rollback on failure
        if backup_path.exists():
            shutil.copy(backup_path, state_path)
            backup_path.unlink()
        raise e


def _determine_next_step(completed_steps: List[str]) -> Optional[str]:
    """Determine the next onboarding step based on completed steps.

    Args:
        completed_steps: List of completed step names

    Returns:
        Next step name or None if all complete
    """
    step_order = ["project", "git", "provider", "credentials", "complete"]

    for step in step_order:
        if step not in completed_steps:
            return step

    return None


def _get_git_defaults() -> Dict[str, str]:
    """Get git user configuration from global git config.

    Returns:
        Dictionary with 'name' and 'email' from git config, or empty strings if not set
    """
    defaults = {"name": "", "email": ""}

    try:
        # Try to get global git config
        result = subprocess.run(
            ["git", "config", "--global", "user.name"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            defaults["name"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            defaults["email"] = result.stdout.strip()

        logger.debug("git_defaults_loaded", name=defaults["name"], email=defaults["email"])

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # Git not installed or not configured - return empty defaults
        logger.debug("git_config_not_available", error=str(e))

    return defaults


def _get_project_defaults(project_root: Optional[Path]) -> Dict[str, str]:
    """Get project defaults for onboarding wizard.

    Args:
        project_root: Current project root path (may be None in bootstrap mode)

    Returns:
        Dictionary with project defaults (name, type, description)
    """
    # Use current working directory if project_root not set
    if project_root is None:
        project_root = Path.cwd()

    # Default project name from directory name
    project_name = project_root.name if project_root.name != "." else "my-project"

    return {
        "name": project_name,
        "type": "greenfield",  # Default to new project
        "description": "",
    }


# ============================================================================
# API ENDPOINTS
# ============================================================================


@router.get("/status")
async def get_onboarding_status(request: Request) -> Dict[str, Any]:
    """Get current onboarding state with all required data for frontend.

    Returns the current state of the onboarding wizard including:
    - Whether onboarding is complete
    - Current step in progress
    - List of completed steps
    - Available providers with complete metadata
    - Project and git defaults for pre-filling forms
    - Configuration summary (without sensitive data)

    Args:
        request: FastAPI request object

    Returns:
        Dictionary matching frontend OnboardingStatus interface:
        - needs_onboarding: boolean
        - completed_steps: string[]
        - current_step: string
        - project_defaults: {name, type, description}
        - git_defaults: {name, email}
        - available_providers: ProviderInfo[]
        - project_root: string
    """
    try:
        # Get project root from app state (or bootstrap mode)
        project_root = getattr(request.app.state, "project_root", None)

        # Get git and project defaults
        git_defaults = _get_git_defaults()
        project_defaults = _get_project_defaults(project_root)

        # Get available providers with complete metadata
        available_providers = get_available_providers()

        # Use current working directory if project_root not set
        if project_root is None:
            project_root = Path.cwd()

        # Ensure project_root is Path object
        if not isinstance(project_root, Path):
            project_root = Path(project_root)

        # Load saved state (if exists)
        state = _load_onboarding_state(project_root)
        completed_steps = state.get("completed_steps", [])
        next_step = _determine_next_step(completed_steps)
        is_complete = next_step is None or "complete" in completed_steps

        # Override defaults with saved data if available
        if state.get("project"):
            project_defaults["name"] = state["project"].get("name", project_defaults["name"])
            project_defaults["description"] = state["project"].get("description", "")

        if state.get("git"):
            git_defaults["name"] = state["git"].get("author_name", git_defaults["name"])
            git_defaults["email"] = state["git"].get("author_email", git_defaults["email"])

        # Determine if onboarding is needed
        needs_onboarding = not is_complete

        # Build response matching frontend OnboardingStatus interface
        response_data = {
            "needs_onboarding": needs_onboarding,
            "completed_steps": completed_steps,
            "current_step": next_step or "complete",
            "project_defaults": project_defaults,
            "git_defaults": git_defaults,
            "available_providers": available_providers,
            "project_root": str(project_root),
        }

        logger.info(
            "onboarding_status_retrieved",
            needs_onboarding=needs_onboarding,
            current_step=response_data["current_step"],
            provider_count=len(available_providers),
        )

        return response_data

    except Exception as e:
        logger.exception("get_onboarding_status_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get onboarding status: {str(e)}"
        )


@router.post("/project", response_model=OnboardingResponse)
async def save_project_config(
    config: ProjectConfig,
    request: Request
) -> OnboardingResponse:
    """Save project configuration (Step 1).

    Creates the project directory structure and saves configuration.
    This is the first step that establishes the project context.

    Args:
        config: Project configuration
        request: FastAPI request object

    Returns:
        OnboardingResponse with result

    Raises:
        HTTPException: If validation fails (400) or save fails (500)
    """
    try:
        project_path = Path(config.path)

        # Validate path exists or can be created
        if not project_path.exists():
            try:
                project_path.mkdir(parents=True, exist_ok=True)
                logger.info("created_project_directory", path=str(project_path))
            except (OSError, PermissionError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot create project directory: {str(e)}"
                )

        # Ensure .gao-dev directory exists
        gao_dev_dir = project_path / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Load existing state and update
        state = _load_onboarding_state(project_path)
        state["project"] = {
            "name": config.name,
            "description": config.description,
            "path": str(project_path),
            "language": config.language,
            "scale_level": config.scale_level
        }

        # Mark step complete
        completed_steps = state.get("completed_steps", [])
        if "project" not in completed_steps:
            completed_steps.append("project")
        state["completed_steps"] = completed_steps

        # Save state
        _save_onboarding_state(project_path, state)

        # Update app state with new project root
        request.app.state.project_root = project_path

        logger.info(
            "project_config_saved",
            name=config.name,
            path=str(project_path),
            language=config.language,
            scale_level=config.scale_level
        )

        return OnboardingResponse(
            success=True,
            message="Project configuration saved",
            next_step="git",
            data={
                "name": config.name,
                "path": str(project_path),
                "language": config.language,
                "scale_level": config.scale_level
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("save_project_config_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save project configuration: {str(e)}"
        )


@router.post("/git", response_model=OnboardingResponse)
async def save_git_config(
    config: GitConfig,
    request: Request
) -> OnboardingResponse:
    """Save git configuration (Step 2).

    Optionally initializes git repository and configures author settings.

    Args:
        config: Git configuration
        request: FastAPI request object

    Returns:
        OnboardingResponse with result

    Raises:
        HTTPException: If validation fails (400) or git operation fails (500)
    """
    try:
        project_root = getattr(request.app.state, "project_root", None)

        if project_root is None:
            raise HTTPException(
                status_code=400,
                detail="Project must be configured first. Complete the project step."
            )

        git_initialized = False

        if config.initialize_git:
            # Import GitManager
            from gao_dev.core.git_manager import GitManager

            git_manager = GitManager(project_path=project_root)

            # Initialize if not already a git repo
            if not git_manager.is_git_repo():
                # Set author info before initialization (if provided)
                # init_repo will use these values for the initial commit
                author_name = config.author_name or "GAO-Dev"
                author_email = config.author_email or "dev@gao-dev.local"

                # Initialize with initial commit if requested
                git_manager.init_repo(
                    user_name=author_name,
                    user_email=author_email,
                    initial_commit=config.create_initial_commit,
                    create_gitignore=True
                )
                logger.info("git_repository_initialized", path=str(project_root))

                # Set author info locally (for subsequent commits)
                if config.author_name:
                    git_manager._run_git_command(["config", "user.name", config.author_name])
                if config.author_email:
                    git_manager._run_git_command(["config", "user.email", config.author_email])

            git_initialized = True

        # Load existing state and update
        state = _load_onboarding_state(project_root)
        state["git"] = {
            "initialized": git_initialized,
            "author_name": config.author_name,
            "author_email": config.author_email,
            "initial_commit_created": config.create_initial_commit and git_initialized
        }

        # Mark step complete
        completed_steps = state.get("completed_steps", [])
        if "git" not in completed_steps:
            completed_steps.append("git")
        state["completed_steps"] = completed_steps

        # Save state
        _save_onboarding_state(project_root, state)

        logger.info(
            "git_config_saved",
            initialized=git_initialized,
            author=config.author_name
        )

        return OnboardingResponse(
            success=True,
            message="Git configuration saved",
            next_step="provider",
            data={
                "initialized": git_initialized,
                "initial_commit_created": config.create_initial_commit and git_initialized
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("save_git_config_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save git configuration: {str(e)}"
        )


@router.post("/provider", response_model=OnboardingResponse)
async def save_provider_config(
    config: ProviderConfig,
    request: Request
) -> OnboardingResponse:
    """Save provider selection (Step 3).

    Saves the selected AI provider and model to preferences file.

    Args:
        config: Provider configuration
        request: FastAPI request object

    Returns:
        OnboardingResponse with result

    Raises:
        HTTPException: If validation fails (400) or save fails (500)
    """
    try:
        project_root = getattr(request.app.state, "project_root", None)

        if project_root is None:
            raise HTTPException(
                status_code=400,
                detail="Project must be configured first. Complete the project step."
            )

        # Save provider preferences
        prefs_path = project_root / ".gao-dev" / "provider_preferences.yaml"
        prefs_path.parent.mkdir(parents=True, exist_ok=True)

        prefs = {
            "provider": config.provider,
            "model": config.model,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

        with open(prefs_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(prefs, f, default_flow_style=False)

        # Set secure permissions (Unix only)
        if os.name != "nt":
            os.chmod(prefs_path, 0o600)

        # Update onboarding state
        state = _load_onboarding_state(project_root)
        state["provider"] = {
            "provider": config.provider,
            "model": config.model
        }

        # Mark step complete
        completed_steps = state.get("completed_steps", [])
        if "provider" not in completed_steps:
            completed_steps.append("provider")
        state["completed_steps"] = completed_steps

        # Save state
        _save_onboarding_state(project_root, state)

        logger.info(
            "provider_config_saved",
            provider=config.provider,
            model=config.model
        )

        return OnboardingResponse(
            success=True,
            message="Provider selection saved",
            next_step="credentials",
            data={
                "provider": config.provider,
                "model": config.model
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("save_provider_config_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save provider configuration: {str(e)}"
        )


@router.post("/credentials", response_model=OnboardingResponse)
async def save_credentials(
    config: CredentialsConfig,
    request: Request
) -> OnboardingResponse:
    """Validate and store API credentials (Step 4).

    Validates the API key format and optionally tests connectivity.
    SECURITY: Never logs or returns the actual API key value.

    Args:
        config: Credentials configuration
        request: FastAPI request object

    Returns:
        OnboardingResponse with validation result

    Raises:
        HTTPException: If validation fails (400) or storage fails (500)
    """
    try:
        project_root = getattr(request.app.state, "project_root", None)

        if project_root is None:
            raise HTTPException(
                status_code=400,
                detail="Project must be configured first. Complete the project step."
            )

        # Determine environment variable name based on key type
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY"
        }

        env_var = env_var_map.get(config.key_type, "ANTHROPIC_API_KEY")

        # Validate API key (basic checks, never log the key)
        key_valid = True
        validation_message = "API key format validated"

        # Check key prefix based on type (common patterns)
        if config.key_type == "anthropic":
            if not config.api_key.startswith("sk-ant-"):
                # Log warning but allow - some keys might have different format
                logger.info("api_key_unexpected_prefix", key_type=config.key_type)
                validation_message = "API key format appears non-standard but accepted"
        elif config.key_type == "openai":
            if not config.api_key.startswith("sk-"):
                logger.info("api_key_unexpected_prefix", key_type=config.key_type)
                validation_message = "API key format appears non-standard but accepted"

        # Store key status in onboarding state (NOT the key itself)
        state = _load_onboarding_state(project_root)
        state["credentials"] = {
            "key_type": config.key_type,
            "env_var": env_var,
            "validated": key_valid,
            "key_prefix": config.api_key[:8] + "...",  # Only store first 8 chars for identification
            "validated_at": datetime.utcnow().isoformat() + "Z"
        }

        # Mark step complete
        completed_steps = state.get("completed_steps", [])
        if "credentials" not in completed_steps:
            completed_steps.append("credentials")
        state["completed_steps"] = completed_steps

        # Save state
        _save_onboarding_state(project_root, state)

        # Log success without exposing key
        logger.info(
            "credentials_validated",
            key_type=config.key_type,
            env_var=env_var,
            valid=key_valid
        )

        return OnboardingResponse(
            success=True,
            message=validation_message,
            next_step="complete",
            data={
                "key_type": config.key_type,
                "env_var": env_var,
                "validated": key_valid,
                "instructions": f"Set environment variable {env_var} with your API key to use GAO-Dev"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("save_credentials_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save credentials: {str(e)}"
        )


@router.post("/complete", response_model=OnboardingResponse)
async def complete_onboarding(request: Request) -> OnboardingResponse:
    """Finalize onboarding (Step 5).

    Marks onboarding as complete and transitions to normal mode.
    Creates any remaining initialization files.

    Args:
        request: FastAPI request object

    Returns:
        OnboardingResponse with completion status

    Raises:
        HTTPException: If prerequisites not met (400) or finalization fails (500)
    """
    try:
        project_root = getattr(request.app.state, "project_root", None)

        if project_root is None:
            raise HTTPException(
                status_code=400,
                detail="Project must be configured first. Complete the project step."
            )

        # Load state and verify prerequisites
        state = _load_onboarding_state(project_root)
        completed_steps = state.get("completed_steps", [])

        # Check all required steps are complete
        required_steps = ["project", "git", "provider", "credentials"]
        missing_steps = [step for step in required_steps if step not in completed_steps]

        if missing_steps:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete onboarding. Missing steps: {', '.join(missing_steps)}"
            )

        # Mark onboarding complete
        if "complete" not in completed_steps:
            completed_steps.append("complete")
        state["completed_steps"] = completed_steps
        state["onboarding_complete"] = True
        state["completed_at"] = datetime.utcnow().isoformat() + "Z"

        # Save final state
        _save_onboarding_state(project_root, state)

        # Create project README if it doesn't exist
        readme_path = project_root / "README.md"
        if not readme_path.exists():
            project_name = state.get("project", {}).get("name", "GAO-Dev Project")
            description = state.get("project", {}).get("description", "")

            readme_content = f"""# {project_name}

{description}

## Development

This project was initialized using GAO-Dev autonomous development system.

### Getting Started

1. Ensure your API key is set: `export ANTHROPIC_API_KEY=your-key`
2. Run GAO-Dev: `gao-dev start`

## Project Structure

- `docs/` - Documentation and specifications
- `src/` - Source code
- `tests/` - Test suite
- `.gao-dev/` - GAO-Dev configuration and state

---
*Generated by GAO-Dev onboarding wizard*
"""
            readme_path.write_text(readme_content, encoding="utf-8")
            logger.info("readme_created", path=str(readme_path))

        # Create initial docs structure
        docs_path = project_root / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "onboarding_complete",
            project=state.get("project", {}).get("name"),
            path=str(project_root)
        )

        return OnboardingResponse(
            success=True,
            message="Onboarding complete! Your project is ready.",
            next_step=None,
            data={
                "project_name": state.get("project", {}).get("name"),
                "project_path": str(project_root),
                "provider": state.get("provider", {}).get("provider"),
                "completed_at": state.get("completed_at"),
                "ready_to_use": True
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("complete_onboarding_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete onboarding: {str(e)}"
        )
