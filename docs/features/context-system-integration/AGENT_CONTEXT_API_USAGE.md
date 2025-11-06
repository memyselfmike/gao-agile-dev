# Agent Context API Usage Guide

## Overview

The AgentContextAPI provides a high-level interface for agents (Bob, Amelia, Murat, etc.) to access project context without manual document loading. All document access is automatically cached, tracked for lineage, and logged for audit trails.

## Key Features

- **Lazy Loading**: Documents loaded only when accessed
- **Transparent Caching**: Automatic cache usage with fallback to file loading
- **Usage Tracking**: Every access recorded for audit trail and lineage
- **Thread-Safe**: Supports concurrent agent workflows
- **Custom Loaders**: Support for custom document loading logic

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Prompt                              │
│  (Bob, Amelia, Murat use AgentContextAPI in their prompts)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WorkflowContext                               │
│  - workflow_id, epic_num, story_num, feature                    │
│  - Set via set_workflow_context() (thread-local)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AgentContextAPI                               │
│  - get_epic_definition()                                         │
│  - get_architecture()                                            │
│  - get_prd()                                                     │
│  - get_story_definition()                                        │
│  - get_coding_standards()                                        │
│  - get_acceptance_criteria()                                     │
└───────────┬────────────────┬────────────────┬────────────────────┘
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
    │ ContextCache │ │  Document    │ │ ContextUsage     │
    │              │ │  Loader      │ │ Tracker          │
    │ (LRU, TTL)   │ │ (Filesystem) │ │ (SQLite DB)      │
    └──────────────┘ └──────────────┘ └──────────────────┘
```

## Basic Usage

### 1. Setting Up WorkflowContext

Before agents can access context, the WorkflowContext must be set. This is typically done by the story orchestrator or task coordinator:

```python
from gao_dev.core.context.context_api import set_workflow_context
from gao_dev.core.context.workflow_context import WorkflowContext
import uuid

# Create WorkflowContext
context = WorkflowContext(
    workflow_id=str(uuid.uuid4()),
    epic_num=17,
    story_num=4,
    feature="context-system-integration",
    workflow_name="implement_story"
)

# Set as current context (thread-local)
set_workflow_context(context)
```

### 2. Accessing Context in Agent Prompts

Agents can then retrieve the context and access documents:

```python
from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

# Get current workflow context
workflow_context = get_workflow_context()

# Initialize AgentContextAPI
api = AgentContextAPI(workflow_context)

# Access documents (lazy-loaded, cached, tracked)
epic_def = api.get_epic_definition()
architecture = api.get_architecture()
prd = api.get_prd()
story_def = api.get_story_definition()
coding_standards = api.get_coding_standards()
acceptance_criteria = api.get_acceptance_criteria()
```

### 3. Clearing Context After Workflow

```python
from gao_dev.core.context.context_api import clear_workflow_context

# Clear context after workflow completes
clear_workflow_context()
```

## Agent-Specific Usage Patterns

### Bob (Scrum Master) - Story Creation

Bob needs epic context when creating story specifications:

```python
# In Bob's story creation prompt
from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

context = get_workflow_context()
api = AgentContextAPI(context)

# Bob accesses:
epic_def = api.get_epic_definition()      # Epic requirements and scope
architecture = api.get_architecture()     # System architecture for planning
prd = api.get_prd()                       # Product requirements

# Use context to create comprehensive story specification
```

### Amelia (Developer) - Story Implementation

Amelia needs comprehensive context for implementation:

```python
# In Amelia's implementation prompt
from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

context = get_workflow_context()
api = AgentContextAPI(context)

# Amelia accesses:
epic_def = api.get_epic_definition()           # Epic context
architecture = api.get_architecture()          # Architecture patterns
story_def = api.get_story_definition()         # Story requirements
coding_standards = api.get_coding_standards()  # Code quality standards
acceptance_criteria = api.get_acceptance_criteria()  # What to implement

# Implement story following all guidelines
```

### Murat (Test Architect) - Story Validation

Murat needs context for comprehensive validation:

```python
# In Murat's validation prompt
from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

context = get_workflow_context()
api = AgentContextAPI(context)

# Murat accesses:
story_def = api.get_story_definition()         # Story to validate
acceptance_criteria = api.get_acceptance_criteria()  # Validation criteria
coding_standards = api.get_coding_standards()  # Quality standards
architecture = api.get_architecture()          # Architecture compliance

# Validate implementation against all criteria
```

## Advanced Features

### Custom Context Values

AgentContextAPI supports custom key-value storage:

```python
api = AgentContextAPI(context)

# Set custom values
api.set_custom("project_name", "GAO-Dev")
api.set_custom("version", "2.0.0")
api.set_custom("test_framework", "pytest")

# Get custom values
project_name = api.get_custom("project_name")
version = api.get_custom("version", default="1.0.0")
```

### Cache Statistics

Monitor cache performance:

```python
api = AgentContextAPI(context)

# Access some documents
epic_def = api.get_epic_definition()
architecture = api.get_architecture()

# Get cache statistics
stats = api.get_cache_statistics()
print(f"Cache hits: {stats['hits']}")
print(f"Cache misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['size']}")
```

### Usage History and Lineage

Track document access for audit and lineage:

```python
api = AgentContextAPI(context)

# Access documents
epic_def = api.get_epic_definition()
architecture = api.get_architecture()

# Get usage history
history = api.get_usage_history()
for record in history:
    print(f"Context Key: {record['context_key']}")
    print(f"Cache Hit: {record['cache_hit']}")
    print(f"Accessed At: {record['accessed_at']}")

# Get usage for specific document
epic_history = api.get_usage_history(context_key="epic_definition")
```

### Manual Cache Management

Clear cache when needed:

```python
api = AgentContextAPI(context)

# Clear all cached documents
api.clear_cache()
```

## Prompt Template Integration

### Story Orchestrator Prompts

Story orchestrator prompts set up the WorkflowContext:

```yaml
# gao_dev/prompts/story_phases/story_implementation.yaml

user_prompt: |
  ### Accessing Context via AgentContextAPI

  You have access to the AgentContextAPI for retrieving project context.
  Use the following API to access documents:

  ```python
  from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

  # Get current workflow context
  workflow_context = get_workflow_context()

  # Initialize AgentContextAPI
  api = AgentContextAPI(workflow_context)

  # Access documents (lazy-loaded, cached, tracked)
  epic_def = api.get_epic_definition()
  architecture = api.get_architecture()
  story_def = api.get_story_definition()
  coding_standards = api.get_coding_standards()
  ```

  All document accesses are automatically:
  - Cached for performance
  - Tracked for lineage
  - Logged for audit trail
```

### Task Prompts

Task prompts initialize WorkflowContext before agent coordination:

```yaml
# gao_dev/prompts/tasks/implement_story.yaml

user_prompt: |
  ### Accessing Context via AgentContextAPI

  Before coordinating agents, set up the WorkflowContext and AgentContextAPI:

  ```python
  from gao_dev.core.context.context_api import set_workflow_context, AgentContextAPI
  from gao_dev.core.context.workflow_context import WorkflowContext
  import uuid

  # Create and set WorkflowContext
  context = WorkflowContext(
      workflow_id=str(uuid.uuid4()),
      epic_num={{epic}},
      story_num={{story}},
      feature="{{feature}}",
      workflow_name="implement_story"
  )
  set_workflow_context(context)

  # Initialize AgentContextAPI
  api = AgentContextAPI(context)

  # Access documents
  epic_def = api.get_epic_definition()
  architecture = api.get_architecture()
  story_def = api.get_story_definition()
  ```
```

## Agent YAML Configuration

Agent YAML configs include context API references:

```yaml
# gao_dev/agents/amelia.agent.yaml

agent:
  metadata:
    name: Amelia
    role: Software Developer

  context_api:
    enabled: true
    description: "Access project context via AgentContextAPI"
    available_documents:
      - epic_definition: "Epic definition for current story"
      - architecture: "System architecture guidelines"
      - prd: "Product Requirements Document"
      - story_definition: "Current story definition"
      - acceptance_criteria: "Story acceptance criteria"
      - coding_standards: "Project coding standards"
    usage: |
      # Accessing Context in Amelia's prompts:
      from gao_dev.core.context.context_api import get_workflow_context, AgentContextAPI

      context = get_workflow_context()
      api = AgentContextAPI(context)

      # Get documents for implementation
      epic_def = api.get_epic_definition()
      architecture = api.get_architecture()
      story_def = api.get_story_definition()
      coding_standards = api.get_coding_standards()
```

## Benefits

### For Agents
- **No Manual File Loading**: Agents don't need to know file paths or directory structure
- **Automatic Caching**: Repeated access is fast and efficient
- **Consistent Interface**: All agents use the same API
- **Type Safety**: Clear method names with documentation

### For System
- **Usage Tracking**: Know which documents agents access most
- **Lineage Tracking**: Trace which documents influenced which artifacts
- **Performance Monitoring**: Cache hit rates and access patterns
- **Audit Trail**: Complete history of document access

### For Development
- **Easy Testing**: Mock document loader for unit tests
- **Custom Loaders**: Support different document sources
- **Extensible**: Add new document types easily
- **Observable**: Full visibility into context usage

## Document Loading Hierarchy

The AgentContextAPI follows this document loading strategy:

1. **Cache Check**: Check ContextCache first (LRU with TTL)
2. **DocumentLifecycleManager**: Try loading from document registry (Epic 12)
3. **Filesystem Fallback**: Load directly from docs/features/ structure
4. **Return None**: If document not found

This ensures maximum compatibility while leveraging advanced features when available.

## Thread Safety

WorkflowContext is stored in thread-local storage, ensuring:

- **Isolated Contexts**: Each thread has its own context
- **Concurrent Execution**: Multiple agents can run in parallel
- **No Race Conditions**: Context access is thread-safe

```python
import threading

def agent_workflow(epic_num, story_num):
    # Each thread gets its own context
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=epic_num,
        story_num=story_num,
        feature="test-feature",
        workflow_name="implement_story"
    )
    set_workflow_context(context)

    # Use context (isolated to this thread)
    api = AgentContextAPI(context)
    epic_def = api.get_epic_definition()

# Run multiple agents concurrently
threads = [
    threading.Thread(target=agent_workflow, args=(17, 1)),
    threading.Thread(target=agent_workflow, args=(17, 2)),
]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Error Handling

The AgentContextAPI handles errors gracefully:

```python
api = AgentContextAPI(context)

# Returns None if document not found
epic_def = api.get_epic_definition()
if epic_def is None:
    # Handle missing document
    print("Epic definition not found")

# Returns None if story_num is None
story_def = api.get_story_definition()
if story_def is None:
    # This is normal for epic-level workflows
    print("No story context (epic-level workflow)")
```

## Testing

Integration tests verify agent context access:

```python
# tests/integration/test_agent_context_access.py

def test_amelia_agent_workflow(temp_project_dir, monkeypatch):
    """Test Amelia accessing context for implementation."""
    monkeypatch.chdir(temp_project_dir)

    # Simulate Amelia's workflow
    context = WorkflowContext(
        workflow_id=str(uuid.uuid4()),
        epic_num=1,
        story_num=1,
        feature="test-feature",
        workflow_name="implement_story"
    )

    set_workflow_context(context)
    api = AgentContextAPI(context)

    # Amelia accesses multiple documents
    epic_def = api.get_epic_definition()
    architecture = api.get_architecture()
    story_def = api.get_story_definition()
    coding_standards = api.get_coding_standards()

    assert all([
        epic_def is not None,
        architecture is not None,
        story_def is not None,
        coding_standards is not None,
    ])

    # Verify usage tracked
    history = api.get_usage_history()
    assert len(history) >= 4
```

## Future Enhancements

Potential future improvements to the Context API:

1. **Remote Document Sources**: Load documents from APIs or databases
2. **Document Versioning**: Access specific versions of documents
3. **Smart Prefetching**: Preload documents based on workflow type
4. **Compression**: Compress large documents in cache
5. **Distributed Cache**: Share cache across multiple instances
6. **Analytics**: Machine learning insights on document usage patterns

## Summary

The AgentContextAPI provides a clean, efficient, and observable way for agents to access project context. By abstracting document loading, caching, and tracking, it allows agents to focus on their core responsibilities while the system maintains full visibility into context usage.

Key takeaways:
- Set WorkflowContext before agent execution
- Use AgentContextAPI methods to access documents
- All access is cached, tracked, and logged
- Thread-safe for concurrent agent workflows
- Easy to test and extend
