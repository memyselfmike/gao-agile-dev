"""Shared provider utilities for web API endpoints.

This module provides common functions for working with AI providers across
the web API, including provider discovery, model listing, and status checking.

Used by:
- onboarding.py (wizard provider selection)
- settings.py (provider settings management)
"""

import os
from typing import Any, Dict, List

import structlog

from gao_dev.core.providers import ProviderFactory

logger = structlog.get_logger(__name__)


def get_available_providers() -> List[Dict[str, Any]]:
    """Get list of available providers with complete information.

    Returns provider data suitable for both onboarding wizard and settings panel.
    Includes all fields needed by frontend:
    - id, name, description, icon
    - models (list of available models)
    - requires_api_key, api_key_env_var, has_api_key

    Returns:
        List of provider configurations with complete metadata
    """
    factory = ProviderFactory()
    providers = []

    # Claude Code provider (primary)
    try:
        claude_provider = factory.create_provider("claude-code", use_cache=False)
        providers.append({
            "id": "claude-code",
            "name": "Claude Code",
            "description": "Anthropic Claude via Claude Code CLI (requires ANTHROPIC_API_KEY)",
            "icon": "sparkles",
            "models": _get_models_from_provider(claude_provider, "claude-code"),
            "requires_api_key": True,
            "api_key_env_var": "ANTHROPIC_API_KEY",
            "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        })
    except Exception as e:
        logger.warning("failed_to_get_claude_code_provider", error=str(e))

    # OpenCode SDK provider (multi-provider support)
    try:
        opencode_provider = factory.create_provider("opencode-sdk", use_cache=False)
        # Check for any OpenCode-compatible API keys
        has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
        has_openai = bool(os.environ.get("OPENAI_API_KEY"))
        has_google = bool(os.environ.get("GOOGLE_API_KEY"))
        has_any_key = has_anthropic or has_openai or has_google

        providers.append({
            "id": "opencode-sdk",
            "name": "OpenCode SDK",
            "description": "Multi-provider AI access (Anthropic, OpenAI, Google, local models)",
            "icon": "globe",
            "models": _get_models_from_opencode_sdk(opencode_provider),
            "requires_api_key": True,  # Requires at least one API key
            "api_key_env_var": "ANTHROPIC_API_KEY or OPENAI_API_KEY or GOOGLE_API_KEY",
            "has_api_key": has_any_key,
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
        List of model configurations with id, name, description
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
            display_name = format_model_name(model_id)

            models.append({
                "id": model_id,
                "name": display_name,
                "description": "Anthropic Claude model",
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

        display_name = format_model_name(model_id)
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


def format_model_name(model_id: str) -> str:
    """Format model ID into human-readable display name.

    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4-5-20250929")

    Returns:
        Human-readable name (e.g., "Claude Sonnet 4.5")
    """
    # Special cases for common models
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


def format_provider_name(provider_id: str) -> str:
    """Format provider ID to human-readable display name.

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
