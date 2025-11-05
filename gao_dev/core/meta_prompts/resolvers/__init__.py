"""
Reference resolvers for meta-prompt system.

This package contains specialized resolvers for different reference types:
- DocResolver: @doc: references for document content
- ChecklistResolver: @checklist: references for checklists
"""

from .doc_resolver import DocResolver

__all__ = ["DocResolver"]
