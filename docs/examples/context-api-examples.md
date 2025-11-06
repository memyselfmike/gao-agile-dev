# Context API Usage Examples

This document demonstrates how to use the Context API for agents to access project context without manual document loading.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Accessing Different Document Types](#accessing-different-document-types)
3. [Using in Agent Prompts](#using-in-agent-prompts)
4. [Using in Workflow Steps](#using-in-workflow-steps)
5. [Custom Context Keys](#custom-context-keys)
6. [Cache and Usage Statistics](#cache-and-usage-statistics)
7. [Thread-Local Context](#thread-local-context)
8. [Custom Document Loaders](#custom-document-loaders)
9. [Integration with Workflows](#integration-with-workflows)

---

## Basic Usage

The simplest way to use the Context API is to create an `AgentContextAPI` instance with a `WorkflowContext`:

```python
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI

# Create workflow context
context = WorkflowContext(
    workflow_id="wf-12345",
    epic_num=16,
    story_num=5,
    feature="document-lifecycle",
    workflow_name="implement_story"
)

# Create API instance
api = AgentContextAPI(workflow_context=context)

# Access documents (lazy-loaded, cached, tracked)
epic_def = api.get_epic_definition()
architecture = api.get_architecture()
prd = api.get_prd()

print(f"Epic Definition: {epic_def[:100]}...")
print(f"Architecture: {architecture[:100]}...")
```

**Key Features:**
- Documents are loaded only when accessed (lazy loading)
- Results are cached automatically (transparent caching)
- Every access is tracked for audit (usage tracking)

---

## Accessing Different Document Types

The API provides convenience methods for all common document types:

```python
from gao_dev.core.context.context_api import AgentContextAPI

# Access different document types
epic_def = api.get_epic_definition()          # Epic definition
architecture = api.get_architecture()          # Architecture document
prd = api.get_prd()                           # Product Requirements Doc
story_def = api.get_story_definition()        # Story definition
standards = api.get_coding_standards()        # Coding standards
criteria = api.get_acceptance_criteria()      # Acceptance criteria

# Handle None gracefully (document may not exist)
if epic_def:
    print(f"Epic: {epic_def}")
else:
    print("Epic definition not found")
```

**Available Methods:**
- `get_epic_definition()` - Epic definition document
- `get_architecture()` - System architecture document
- `get_prd()` - Product Requirements Document
- `get_story_definition()` - Story definition (None if story_num is None)
- `get_coding_standards()` - Coding standards document
- `get_acceptance_criteria()` - Acceptance criteria document

---

## Using in Agent Prompts

The Context API is designed to make it easy to include context in agent prompts:

```python
from gao_dev.core.context.context_api import AgentContextAPI

# Create API
api = AgentContextAPI(workflow_context=context)

# Load context for prompt
epic_def = api.get_epic_definition()
architecture = api.get_architecture()
standards = api.get_coding_standards()
story_def = api.get_story_definition()

# Build prompt with context
prompt = f"""
You are implementing Story {api.workflow_context.story_id}.

## Epic Definition
{epic_def}

## Architecture Guidelines
{architecture}

## Coding Standards
{standards}

## Story Requirements
{story_def}

## Your Task
Implement the functionality described in the story above, following the
architecture guidelines and coding standards. Ensure all acceptance criteria
are met.
"""

# Send prompt to agent
response = agent.run(prompt)
```

---

## Using in Workflow Steps

The Context API integrates seamlessly with workflow orchestrators:

```python
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI, set_workflow_context

def workflow_step_1(workflow_context: WorkflowContext):
    """First workflow step."""
    # Set thread-local context
    set_workflow_context(workflow_context)

    # Create API
    api = AgentContextAPI(workflow_context)

    # Access context
    epic_def = api.get_epic_definition()

    # Use in workflow logic
    print(f"Working on: {epic_def[:100]}")

    return {"status": "completed"}


def workflow_step_2(workflow_context: WorkflowContext):
    """Second workflow step."""
    # Create API (can use thread-local context)
    api = AgentContextAPI(workflow_context)

    # Access different context
    architecture = api.get_architecture()
    standards = api.get_coding_standards()

    # Use in workflow logic
    validate_against_architecture(architecture)
    validate_against_standards(standards)

    return {"status": "completed"}


# Run workflow
workflow_context = WorkflowContext(
    workflow_id="wf-123",
    epic_num=16,
    story_num=5,
    feature="document-lifecycle",
    workflow_name="implement_story"
)

result_1 = workflow_step_1(workflow_context)
result_2 = workflow_step_2(workflow_context)
```

---

## Custom Context Keys

The API supports custom context keys for application-specific data:

```python
from gao_dev.core.context.context_api import AgentContextAPI

api = AgentContextAPI(workflow_context=context)

# Set custom context
api.set_custom("project_name", "MyApp")
api.set_custom("tech_stack", ["Python", "FastAPI", "SQLite"])
api.set_custom("team_size", 5)
api.set_custom("config", {"debug": True, "timeout": 30})

# Get custom context
project_name = api.get_custom("project_name")
tech_stack = api.get_custom("tech_stack")
team_size = api.get_custom("team_size")
config = api.get_custom("config")

print(f"Project: {project_name}")
print(f"Tech Stack: {tech_stack}")
print(f"Team Size: {team_size}")
print(f"Config: {config}")

# Get with default value
timeout = api.get_custom("timeout", default=60)
debug_mode = api.get_custom("debug_mode", default=False)
```

**Use Cases:**
- Store configuration values
- Pass data between workflow steps
- Store computed results for reuse
- Application-specific metadata

---

## Cache and Usage Statistics

The API provides visibility into caching and usage patterns:

```python
from gao_dev.core.context.context_api import AgentContextAPI

api = AgentContextAPI(workflow_context=context)

# Access some documents
api.get_epic_definition()
api.get_architecture()
api.get_epic_definition()  # Cache hit

# Get cache statistics
stats = api.get_cache_statistics()
print(f"Cache Size: {stats['size']}")
print(f"Cache Hits: {stats['hits']}")
print(f"Cache Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hit_rate']:.2%}")
print(f"Memory Usage: {stats['memory_usage']} bytes")

# Get usage history
history = api.get_usage_history()
print(f"\nUsage History ({len(history)} records):")
for record in history:
    print(f"  - {record['context_key']}: cache_hit={record['cache_hit']}")

# Get usage for specific context key
epic_history = api.get_usage_history(context_key="epic_definition")
print(f"\nEpic Definition accessed {len(epic_history)} times")

# Clear cache if needed
api.clear_cache()
print("Cache cleared")
```

**Available Metrics:**
- `hits` - Number of cache hits
- `misses` - Number of cache misses
- `size` - Current cache size
- `hit_rate` - Cache hit rate (0.0 - 1.0)
- `memory_usage` - Estimated memory usage in bytes

---

## Thread-Local Context

Use thread-local context for simplified access across functions:

```python
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import (
    set_workflow_context,
    get_workflow_context,
    clear_workflow_context,
    AgentContextAPI
)

# Set thread-local context
context = WorkflowContext(
    workflow_id="wf-123",
    epic_num=16,
    story_num=5,
    feature="document-lifecycle",
    workflow_name="implement_story"
)
set_workflow_context(context)

# Access from anywhere in the thread
def helper_function():
    """Helper that needs context."""
    ctx = get_workflow_context()
    if ctx:
        api = AgentContextAPI(ctx)
        epic = api.get_epic_definition()
        print(f"Epic: {epic[:50]}")

helper_function()  # Works!

# Clean up when done
clear_workflow_context()
```

**Benefits:**
- No need to pass context through all function calls
- Simplified API access in nested functions
- Thread-safe (each thread has its own context)

**When to Use:**
- Long-running workflow executions
- Deep call stacks where passing context is cumbersome
- Integration with existing code that doesn't expect context parameter

---

## Custom Document Loaders

Provide custom document loading logic for special use cases:

```python
from typing import Optional
from pathlib import Path
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI

def custom_document_loader(doc_type: str, workflow_context: WorkflowContext) -> Optional[str]:
    """
    Custom document loader that loads from a different location.

    Example: Load from a database instead of file system.
    """
    if doc_type == "prd":
        # Load from database
        return database.get_document("prd", workflow_context.feature)

    elif doc_type == "architecture":
        # Load from API
        return api_client.fetch_architecture(workflow_context.epic_num)

    elif doc_type == "epic_definition":
        # Load from custom location
        path = Path(f"/custom/location/epic-{workflow_context.epic_num}.md")
        if path.exists():
            return path.read_text()

    # Return None if document not found
    return None


# Use custom loader
api = AgentContextAPI(
    workflow_context=context,
    document_loader=custom_document_loader
)

# API works the same, but uses custom loader
epic = api.get_epic_definition()  # Uses custom loader
arch = api.get_architecture()     # Uses custom loader
```

**Use Cases:**
- Load documents from database
- Load documents from API
- Load documents from custom file structure
- Transform documents on-the-fly
- Add access control logic

---

## Integration with Workflows

Complete example showing integration with workflow orchestration:

```python
from typing import Dict, Any
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI, set_workflow_context

class StoryImplementationWorkflow:
    """Workflow for implementing a story."""

    def __init__(self, workflow_context: WorkflowContext):
        self.context = workflow_context
        self.api = AgentContextAPI(workflow_context)
        set_workflow_context(workflow_context)

    def run(self) -> Dict[str, Any]:
        """Execute workflow steps."""
        # Step 1: Analyze requirements
        requirements = self.analyze_requirements()

        # Step 2: Design solution
        design = self.design_solution(requirements)

        # Step 3: Implement
        artifacts = self.implement(design)

        # Step 4: Validate
        validation = self.validate(artifacts)

        return {
            "status": "completed",
            "artifacts": artifacts,
            "validation": validation
        }

    def analyze_requirements(self) -> Dict[str, Any]:
        """Analyze requirements from context."""
        # Load context documents
        story = self.api.get_story_definition()
        epic = self.api.get_epic_definition()
        prd = self.api.get_prd()

        # Parse requirements
        requirements = parse_requirements(story, epic, prd)

        # Store in custom context
        self.api.set_custom("requirements", requirements)

        return requirements

    def design_solution(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design solution based on architecture."""
        # Load architecture context
        architecture = self.api.get_architecture()
        standards = self.api.get_coding_standards()

        # Design solution
        design = create_design(requirements, architecture, standards)

        # Store in custom context
        self.api.set_custom("design", design)

        return design

    def implement(self, design: Dict[str, Any]) -> list:
        """Implement the design."""
        # Get previous context
        requirements = self.api.get_custom("requirements")

        # Implement
        artifacts = generate_code(design, requirements)

        return artifacts

    def validate(self, artifacts: list) -> Dict[str, Any]:
        """Validate implementation."""
        # Get acceptance criteria
        criteria = self.api.get_acceptance_criteria()

        # Validate
        results = validate_artifacts(artifacts, criteria)

        # Log usage statistics
        stats = self.api.get_cache_statistics()
        results["cache_stats"] = stats

        return results


# Run workflow
workflow_context = WorkflowContext(
    workflow_id="wf-123",
    epic_num=16,
    story_num=5,
    feature="document-lifecycle",
    workflow_name="implement_story"
)

workflow = StoryImplementationWorkflow(workflow_context)
result = workflow.run()

print(f"Workflow Result: {result}")
```

---

## Best Practices

### 1. Reuse API Instances

Create one API instance per workflow execution and reuse it:

```python
# Good: Reuse API
api = AgentContextAPI(workflow_context)
epic = api.get_epic_definition()
arch = api.get_architecture()

# Bad: Create multiple APIs
api1 = AgentContextAPI(workflow_context)
epic = api1.get_epic_definition()
api2 = AgentContextAPI(workflow_context)
arch = api2.get_architecture()
```

### 2. Handle Missing Documents

Always check for None when accessing documents:

```python
# Good: Check for None
epic = api.get_epic_definition()
if epic:
    process_epic(epic)
else:
    logger.warning("Epic definition not found")

# Bad: Assume document exists
epic = api.get_epic_definition()
process_epic(epic)  # May fail if epic is None
```

### 3. Use Custom Context for Workflow State

Store intermediate results in custom context:

```python
# Good: Store state
api.set_custom("parsed_requirements", requirements)
api.set_custom("validation_results", results)

# Later...
requirements = api.get_custom("parsed_requirements")
```

### 4. Monitor Cache Performance

Check cache statistics to optimize performance:

```python
stats = api.get_cache_statistics()
if stats['hit_rate'] < 0.5:
    logger.warning(f"Low cache hit rate: {stats['hit_rate']:.2%}")
```

### 5. Clear Cache When Context Changes

If documents are updated, clear cache:

```python
# Document updated externally
update_epic_definition(new_content)

# Clear cache to force reload
api.clear_cache()

# Next access will load fresh content
epic = api.get_epic_definition()
```

---

## Complete Example: Agent Prompt Builder

```python
from gao_dev.core.context import WorkflowContext
from gao_dev.core.context.context_api import AgentContextAPI

class AgentPromptBuilder:
    """Build agent prompts with relevant context."""

    def __init__(self, workflow_context: WorkflowContext):
        self.api = AgentContextAPI(workflow_context)

    def build_implementation_prompt(self) -> str:
        """Build prompt for story implementation."""
        # Load all relevant context
        story = self.api.get_story_definition()
        epic = self.api.get_epic_definition()
        architecture = self.api.get_architecture()
        standards = self.api.get_coding_standards()

        # Build prompt
        prompt = f"""
# Story Implementation Task

## Story Definition
{story}

## Epic Context
{epic}

## Architecture Guidelines
{architecture}

## Coding Standards
{standards}

## Instructions
Implement the functionality described in the story above. Follow these steps:
1. Review the story requirements and acceptance criteria
2. Design the solution following architecture guidelines
3. Implement the code following coding standards
4. Write tests for all new functionality
5. Validate against acceptance criteria

Provide:
1. List of files to create/modify
2. Implementation plan
3. Test strategy
"""

        # Log cache statistics
        stats = self.api.get_cache_statistics()
        print(f"Cache Stats: {stats['hit_rate']:.2%} hit rate")

        return prompt

    def build_review_prompt(self, code: str) -> str:
        """Build prompt for code review."""
        # Load review context
        standards = self.api.get_coding_standards()
        architecture = self.api.get_architecture()

        # Build prompt
        prompt = f"""
# Code Review Task

## Code to Review
```python
{code}
```

## Coding Standards
{standards}

## Architecture Guidelines
{architecture}

## Instructions
Review the code above for:
1. Adherence to coding standards
2. Alignment with architecture
3. Code quality and maintainability
4. Test coverage
5. Documentation completeness

Provide detailed feedback and recommendations.
"""

        return prompt


# Use the prompt builder
workflow_context = WorkflowContext(
    workflow_id="wf-123",
    epic_num=16,
    story_num=5,
    feature="document-lifecycle",
    workflow_name="implement_story"
)

builder = AgentPromptBuilder(workflow_context)

# Build implementation prompt
impl_prompt = builder.build_implementation_prompt()
implementation = agent.run(impl_prompt)

# Build review prompt
review_prompt = builder.build_review_prompt(implementation)
review_result = agent.run(review_prompt)
```

---

## Summary

The Context API provides a simple, powerful way for agents to access project context:

**Key Features:**
- Lazy loading (load only what you need)
- Transparent caching (automatic performance optimization)
- Usage tracking (complete audit trail)
- Custom context (store workflow state)
- Thread-local context (simplified access)
- Custom loaders (flexible loading logic)

**Benefits:**
- Reduced boilerplate code
- Improved performance through caching
- Better observability through tracking
- Simplified agent implementation
- Consistent access patterns

**Use It When:**
- Building agent prompts with context
- Implementing workflow steps
- Accessing project documents
- Tracking context usage
- Optimizing document loading

For more information, see:
- API Documentation: `gao_dev/core/context/context_api.py`
- Tests: `tests/core/context/test_context_api.py`
- Context System: Epic 16 documentation
