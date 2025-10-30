"""
Repository implementations for GAO-Dev.

Provides abstractions for data persistence following the Repository Pattern.
"""

from .file_repository import FileRepository, StateRepository

__all__ = ["FileRepository", "StateRepository"]
