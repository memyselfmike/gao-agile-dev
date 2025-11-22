"""Settings API endpoints for provider configuration."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import structlog
import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from gao_dev.web.events import EventType
from gao_dev.web.provider_validator import WebProviderValidator
from gao_dev.web.api.provider_utils import (
    get_available_providers,
    format_provider_name,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class ProviderChangeRequest(BaseModel):
    """Request body for changing provider settings."""

    provider: str
    model: str


@router.get("/provider")
async def get_provider_settings() -> Dict[str, Any]:
    """Get current provider settings and available options.

    Reads current provider configuration from .gao-dev/provider_preferences.yaml
    and returns available providers with their models.

    Returns:
        Dict containing:
            - current_provider: Currently selected provider ID
            - current_model: Currently selected model ID
            - available_providers: List of provider configurations with models

    Raises:
        HTTPException: If failed to load provider settings
    """
    try:
        # Read current provider from preferences
        prefs_file = Path(".gao-dev/provider_preferences.yaml")
        current_provider = "claude-code"  # Default to claude-code
        current_model = "claude-sonnet-4-5-20250929"

        if prefs_file.exists():
            try:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    prefs = yaml.safe_load(f)
                    if prefs:
                        # Provider names use hyphens in the system
                        current_provider = prefs.get("provider", "claude-code")
                        current_model = prefs.get("model", "claude-sonnet-4-5-20250929")
            except (yaml.YAMLError, IOError) as e:
                logger.warning("failed_to_read_preferences", error=str(e), file=str(prefs_file))
                # Continue with defaults

        # Get available providers and models (using shared utility)
        available_providers = get_available_providers()

        return {
            "current_provider": current_provider,
            "current_model": current_model,
            "available_providers": available_providers,
        }
    except Exception as e:
        logger.exception("failed_to_get_provider_settings", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load provider settings: {str(e)}")


@router.post("/provider")
async def update_provider(request_data: ProviderChangeRequest, req: Request) -> Dict[str, Any]:
    """Save provider settings with validation and atomic persistence.

    Story 39.29: Provider Validation and Persistence

    Args:
        request_data: Provider and model to save
        req: FastAPI request (for event bus access)

    Returns:
        Response dict with success status and message
    """
    try:
        # Validate provider + model combination
        validator = WebProviderValidator()
        validation_result = validator.validate(
            provider=request_data.provider,
            model=request_data.model,
        )

        if not validation_result.valid:
            logger.warning(
                "provider_validation_failed",
                provider=request_data.provider,
                model=request_data.model,
                error=validation_result.error,
            )
            return {
                "success": False,
                "error": validation_result.error,
                "fix_suggestion": validation_result.fix_suggestion,
                "validation_details": {
                    "api_key_status": validation_result.api_key_status,
                    "model_available": validation_result.model_available,
                },
            }

        # Atomic save with rollback
        prefs_file = Path(".gao-dev/provider_preferences.yaml")
        backup_file = Path(".gao-dev/provider_preferences.yaml.bak")

        # Ensure .gao-dev directory exists
        prefs_file.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if prefs_file.exists():
            shutil.copy(prefs_file, backup_file)

        try:
            # Write new preferences
            new_prefs = {
                "provider": request_data.provider,
                "model": request_data.model,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

            with open(prefs_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(new_prefs, f, default_flow_style=False)

            # Set secure file permissions (0600) - Unix only
            if os.name != "nt":
                os.chmod(prefs_file, 0o600)

            # Delete backup on success
            if backup_file.exists():
                backup_file.unlink()

            # Broadcast WebSocket event
            if hasattr(req.app.state, "event_bus"):
                await req.app.state.event_bus.publish(
                    EventType.PROVIDER_CHANGED,
                    {
                        "provider": request_data.provider,
                        "model": request_data.model,
                    },
                )

            logger.info(
                "provider_settings_updated",
                provider=request_data.provider,
                model=request_data.model,
            )

            return {
                "success": True,
                "provider": request_data.provider,
                "model": request_data.model,
                "message": f"Provider changed to {format_provider_name(request_data.provider)} - {request_data.model}",
            }

        except Exception as e:
            # Rollback on failure
            logger.error("failed_to_write_preferences", error=str(e))
            if backup_file.exists():
                shutil.copy(backup_file, prefs_file)
                backup_file.unlink()
            raise e

    except Exception as e:
        logger.exception("failed_to_update_provider", error=str(e))
        return {
            "success": False,
            "error": "Failed to save settings",
            "fix_suggestion": f"Error: {str(e)}. Please try again.",
        }


@router.get("/provider/validate")
async def validate_provider(provider: str, model: str) -> Dict[str, Any]:
    """Validate provider and model combination (real-time validation).

    Story 39.29: Provider Validation and Persistence

    Args:
        provider: Provider ID to validate
        model: Model ID to validate

    Returns:
        Validation result dict

    Raises:
        HTTPException: If validation fails unexpectedly
    """
    try:
        validator = WebProviderValidator()
        result = validator.validate(provider=provider, model=model)

        return {
            "valid": result.valid,
            "api_key_status": result.api_key_status,
            "model_available": result.model_available,
            "warnings": result.warnings,
            "error": result.error,
            "fix_suggestion": result.fix_suggestion,
        }
    except Exception as e:
        logger.exception("failed_to_validate_provider", error=str(e))
        raise HTTPException(status_code=500, detail="Validation failed")
