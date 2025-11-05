"""
Reference resolvers for meta-prompt system.

This package contains specialized resolvers for different reference types:
- DocResolver: @doc: references for document content
- QueryResolver: @query: references for database queries
- ContextResolver: @context: references for cached context
"""

from .doc_resolver import DocResolver
from .query_resolver import QueryResolver
from .context_resolver import ContextResolver

__all__ = ["DocResolver", "QueryResolver", "ContextResolver"]
