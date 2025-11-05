"""
Meta-prompt system for automatic context injection.

This module provides a framework for resolving different reference types
in prompts (@doc:, @checklist:, @query:, @context:) with caching,
nested resolution, and error handling.
"""

from .reference_resolver import ReferenceResolver
from .resolver_registry import ReferenceResolverRegistry
from .resolver_cache import ResolverCache
from .meta_prompt_engine import MetaPromptEngine
from .exceptions import (
    ReferenceResolutionError,
    InvalidReferenceError,
    ResolverNotFoundError,
    CircularReferenceError,
    MaxDepthExceededError,
)

__all__ = [
    "ReferenceResolver",
    "ReferenceResolverRegistry",
    "ResolverCache",
    "MetaPromptEngine",
    "ReferenceResolutionError",
    "InvalidReferenceError",
    "ResolverNotFoundError",
    "CircularReferenceError",
    "MaxDepthExceededError",
]
