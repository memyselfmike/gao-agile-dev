"""Settings API endpoints for provider configuration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import yaml
from fastapi import APIRouter, HTTPException

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


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
        current_provider = "claude_code"
        current_model = "claude-sonnet-4-5-20250929"

        if prefs_file.exists():
            try:
                with open(prefs_file, "r", encoding="utf-8") as f:
                    prefs = yaml.safe_load(f)
                    if prefs:
                        current_provider = prefs.get("provider", "claude_code")
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
    """Get list of available providers with their models.

    Returns:
        List of provider configurations
    """
    providers = [
        {
            "id": "claude_code",
            "name": "Claude Code",
            "description": "Anthropic Claude API (requires ANTHROPIC_API_KEY)",
            "icon": "sparkles",
            "models": [
                {
                    "id": "claude-sonnet-4-5-20250929",
                    "name": "Claude Sonnet 4.5",
                    "description": "Latest and most capable model (Jan 2025)",
                },
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "name": "Claude 3.5 Sonnet",
                    "description": "Previous generation Sonnet (Oct 2024)",
                },
                {
                    "id": "claude-3-5-haiku-20241022",
                    "name": "Claude 3.5 Haiku",
                    "description": "Faster, more cost-effective option",
                },
            ],
        },
        {
            "id": "opencode",
            "name": "OpenCode",
            "description": "OpenRouter API (requires OPENROUTER_API_KEY)",
            "icon": "globe",
            "models": _get_openrouter_models(),
        },
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "description": "Run models locally with Ollama",
            "icon": "server",
            "models": _get_ollama_models(),
        },
    ]

    return providers


def _get_openrouter_models() -> List[Dict[str, str]]:
    """Fetch available models from OpenRouter API.

    For Story 39.28, we return hardcoded list.
    Future story can implement actual API fetch.

    Returns:
        List of model configurations
    """
    # Hardcoded OpenRouter models
    # Future: Implement actual API call to OpenRouter
    return [
        {
            "id": "anthropic/claude-3.5-sonnet",
            "name": "Claude 3.5 Sonnet (OpenRouter)",
            "description": "Via OpenRouter proxy",
        },
        {
            "id": "anthropic/claude-3.5-haiku",
            "name": "Claude 3.5 Haiku (OpenRouter)",
            "description": "Via OpenRouter proxy",
        },
        {
            "id": "openai/gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "description": "OpenAI's most capable model",
        },
        {"id": "openai/gpt-4", "name": "GPT-4", "description": "OpenAI GPT-4 base model"},
    ]


def _get_ollama_models() -> List[Dict[str, str]]:
    """Fetch available models from local Ollama.

    Attempts to detect running Ollama instance and query available models.
    Falls back to common models if Ollama not available.

    Returns:
        List of model configurations
    """
    try:
        import httpx

        # Try to connect to Ollama API
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])

            # Convert Ollama response to our format
            return [
                {
                    "id": model["name"],
                    "name": model["name"].replace(":", " ").title(),
                    "description": f"Local Ollama model ({model.get('size', 'Unknown size')})",
                }
                for model in models
            ]
    except Exception as e:
        logger.debug("ollama_detection_failed", error=str(e))
        # Fall through to defaults

    # Return common Ollama models as fallback
    return [
        {"id": "deepseek-r1", "name": "DeepSeek R1", "description": "Reasoning-focused open model"},
        {"id": "llama2", "name": "Llama 2", "description": "Meta's open source LLM"},
        {"id": "codellama", "name": "CodeLlama", "description": "Specialized for code generation"},
    ]
