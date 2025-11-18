"""Settings API endpoints for provider configuration."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import yaml
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from gao_dev.web.events import EventType
from gao_dev.web.provider_validator import WebProviderValidator
from gao_dev.core.providers import ProviderFactory, ClaudeCodeProvider, OpenCodeSDKProvider

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

        # Get available providers and models
        available_providers = _get_available_providers()

        return {
            "current_provider": current_provider,
            "current_model": current_model,
            "available_providers": available_providers,
        }
    except Exception as e:
        logger.exception("failed_to_get_provider_settings", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load provider settings: {str(e)}")


def _get_available_providers() -> List[Dict[str, Any]]:
    """Get list of available providers with their models from ProviderFactory.

    Dynamically discovers providers from the provider abstraction system
    and queries each for available models.

    Returns:
        List of provider configurations
    """
    factory = ProviderFactory()
    providers = []

    # Get Claude Code provider (primary provider)
    try:
        claude_provider = factory.create_provider("claude-code", use_cache=False)
        providers.append({
            "id": "claude-code",
            "name": "Claude Code",
            "description": "Anthropic Claude via Claude Code CLI (requires ANTHROPIC_API_KEY)",
            "icon": "sparkles",
            "models": _get_models_from_provider(claude_provider, "claude-code"),
        })
    except Exception as e:
        logger.warning("failed_to_get_claude_code_provider", error=str(e))

    # Get OpenCode SDK provider (recommended for multi-provider support)
    try:
        opencode_provider = factory.create_provider("opencode-sdk", use_cache=False)
        providers.append({
            "id": "opencode-sdk",
            "name": "OpenCode SDK",
            "description": "Multi-provider AI access (Anthropic, OpenAI, Google, local models)",
            "icon": "globe",
            "models": _get_models_from_opencode_sdk(opencode_provider),
        })
    except Exception as e:
        logger.warning("failed_to_get_opencode_sdk_provider", error=str(e))

    return providers


def _get_models_from_provider(provider: Any, provider_id: str) -> List[Dict[str, str]]:
    """Extract available models from a provider's MODEL_MAPPING.

    Args:
        provider: Provider instance (ClaudeCodeProvider, etc.)
        provider_id: Provider identifier for display

    Returns:
        List of model configurations
    """
    models = []

    # Get MODEL_MAPPING from provider
    model_mapping = getattr(provider, "MODEL_MAPPING", {})

    # Get unique model IDs (values from mapping, excluding canonical short names)
    seen_ids = set()
    for canonical_name, model_id in model_mapping.items():
        # Skip canonical short names like "sonnet-4.5", keep full IDs
        if model_id not in seen_ids and "-" in model_id and "claude-" in model_id:
            seen_ids.add(model_id)

            # Format display name
            display_name = _format_model_name(model_id)

            models.append({
                "id": model_id,
                "name": display_name,
                "description": f"Anthropic Claude model",
            })

    return sorted(models, key=lambda m: m["id"], reverse=True)  # Latest first


def _get_models_from_opencode_sdk(provider: Any) -> List[Dict[str, str]]:
    """Extract available models from OpenCode SDK provider.

    OpenCode SDK supports multiple backends:
    - Anthropic (Claude models)
    - OpenAI (GPT models)
    - Google (Gemini models)
    - Local (Ollama models)

    Args:
        provider: OpenCodeSDKProvider instance

    Returns:
        List of model configurations grouped by backend
    """
    models = []

    # Get MODEL_MAP from OpenCodeSDKProvider
    model_map = getattr(provider, "MODEL_MAP", {})

    # Group by provider type
    anthropic_models = []
    openai_models = []
    google_models = []
    local_models = []

    for model_id, (provider_type, _) in model_map.items():
        # Skip canonical short names, keep full IDs
        if "-" not in model_id:
            continue

        display_name = _format_model_name(model_id)
        model_entry = {
            "id": model_id,
            "name": display_name,
            "description": f"Via OpenCode ({provider_type})",
        }

        if provider_type == "anthropic":
            anthropic_models.append(model_entry)
        elif provider_type == "openai":
            openai_models.append(model_entry)
        elif provider_type == "google":
            google_models.append(model_entry)
        elif provider_type == "ollama" or provider_type == "local":
            local_models.append(model_entry)

    # Combine in priority order: Anthropic, OpenAI, Google, Local
    models.extend(sorted(anthropic_models, key=lambda m: m["id"], reverse=True))
    models.extend(sorted(openai_models, key=lambda m: m["id"], reverse=True))
    models.extend(sorted(google_models, key=lambda m: m["id"], reverse=True))
    models.extend(sorted(local_models, key=lambda m: m["id"], reverse=True))

    return models


def _format_model_name(model_id: str) -> str:
    """Format model ID into display name.

    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4-5-20250929")

    Returns:
        Human-readable name (e.g., "Claude Sonnet 4.5")
    """
    # Special cases
    if "sonnet-4-5" in model_id or "sonnet-4.5" in model_id:
        return "Claude Sonnet 4.5"
    elif "sonnet-3-5" in model_id or "3.5-sonnet" in model_id:
        return "Claude 3.5 Sonnet"
    elif "opus-4" in model_id:
        return "Claude Opus 4"
    elif "opus-3" in model_id:
        return "Claude Opus 3"
    elif "haiku-3" in model_id or "3-haiku" in model_id or "3.5-haiku" in model_id:
        return "Claude 3.5 Haiku"
    elif "gpt-4-turbo" in model_id:
        return "GPT-4 Turbo"
    elif "gpt-4" in model_id:
        return "GPT-4"
    elif "gpt-3.5" in model_id:
        return "GPT-3.5 Turbo"
    elif "gemini-pro" in model_id:
        return "Gemini Pro"
    elif "deepseek-r1:8b" in model_id:
        return "DeepSeek R1 8B (Ollama)"
    elif "deepseek" in model_id:
        return "DeepSeek R1 (Ollama)"
    elif "llama" in model_id:
        return "Llama 2 (Ollama)"
    elif "codellama" in model_id:
        return "CodeLlama (Ollama)"

    # Fallback: Title case with dashes removed
    return model_id.replace("-", " ").replace("_", " ").title()


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
                "message": f"Provider changed to {_format_provider_name(request_data.provider)} - {request_data.model}",
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


def _format_provider_name(provider_id: str) -> str:
    """Format provider ID to display name.

    Args:
        provider_id: Provider ID (claude-code, opencode-sdk, etc.)

    Returns:
        Human-readable provider name
    """
    names = {
        "claude-code": "Claude Code",
        "opencode-sdk": "OpenCode SDK",
        "opencode": "OpenCode",
        "opencode-cli": "OpenCode CLI",
        "direct-api-anthropic": "Direct API (Anthropic)",
        "direct-api-openai": "Direct API (OpenAI)",
        "direct-api-google": "Direct API (Google)",
    }
    return names.get(provider_id, provider_id.replace("-", " ").title())
