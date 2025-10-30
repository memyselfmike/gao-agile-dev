"""
Strategy implementations for GAO-Dev.

This package contains strategy pattern implementations for workflow selection,
agent routing, and other pluggable behaviors.
"""

from .workflow_strategies import (
    ScaleLevelStrategy,
    ProjectTypeStrategy,
    CustomWorkflowStrategy,
    WorkflowStrategyRegistry
)

__all__ = [
    "ScaleLevelStrategy",
    "ProjectTypeStrategy",
    "CustomWorkflowStrategy",
    "WorkflowStrategyRegistry"
]
