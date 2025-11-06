"""
Context management and caching for GAO-Dev.

This package provides context caching and usage tracking for the meta-prompt system,
as well as workflow execution context for tracking state across workflow phases,
context persistence to SQLite database, and context lineage tracking for audit trails.
Includes Context API for simplified agent access to context documents.
"""

from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker
from gao_dev.core.context.models import PhaseTransition
from gao_dev.core.context.workflow_context import WorkflowContext
from gao_dev.core.context.context_persistence import ContextPersistence
from gao_dev.core.context.context_lineage import ContextLineageTracker
from gao_dev.core.context.exceptions import PersistenceError, ContextNotFoundError
from gao_dev.core.context.context_api import (
    AgentContextAPI,
    get_workflow_context,
    set_workflow_context,
    clear_workflow_context
)

__all__ = [
    'ContextCache',
    'ContextUsageTracker',
    'PhaseTransition',
    'WorkflowContext',
    'ContextPersistence',
    'ContextLineageTracker',
    'PersistenceError',
    'ContextNotFoundError',
    'AgentContextAPI',
    'get_workflow_context',
    'set_workflow_context',
    'clear_workflow_context',
]
