# Story 16.5: Context API for Agents

**Epic:** 16 - Context Persistence Layer
**Story Points:** 3 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Create simple API for agents to access context without manual document loading. This provides convenience methods that abstract away the complexity of context management.

---

## Acceptance Criteria

### Context Access Methods
- [ ] `get_workflow_context()` returns current WorkflowContext
- [ ] `context.get_epic_definition()` lazy-loads epic definition
- [ ] `context.get_architecture()` lazy-loads architecture
- [ ] `context.get_coding_standards()` lazy-loads standards
- [ ] `context.get_acceptance_criteria()` lazy-loads criteria

### Automatic Features
- [ ] Integrates with ContextCache (transparent caching)
- [ ] Fallback to document loading if not cached
- [ ] Usage tracking integrated (automatic lineage recording)
- [ ] Thread-local or explicit context passing

### Integration
- [ ] Works with MetaPromptEngine (Epic 13)
- [ ] Works with workflow orchestrators
- [ ] Context passed through workflow steps
- [ ] Context stored in WorkflowContext object

### Examples & Documentation
- [ ] Example: Using context in agent prompts
- [ ] Example: Accessing context in workflow steps
- [ ] Example: Custom context keys
- [ ] API documentation complete

**Files to Create:**
- `gao_dev/core/context/context_api.py`
- `docs/examples/context-api-examples.md`
- `tests/core/context/test_context_api.py`

**Dependencies:** Story 16.1 (ContextCache), Story 16.2 (WorkflowContext)

---

## Technical Notes

```python
# Example usage in agent prompt

from gao_dev.core.context import get_workflow_context

# In workflow
context = get_workflow_context()

# Lazy-loaded, cached, tracked
epic_def = context.get_epic_definition()
architecture = context.get_architecture()
standards = context.get_coding_standards()

# Used in prompt
prompt = f"""
Epic Definition:
{epic_def}

Architecture Guidelines:
{architecture}

Coding Standards:
{standards}
"""
```

---

## Definition of Done

- [ ] All methods implemented
- [ ] Caching working
- [ ] Tracking working
- [ ] Examples complete
- [ ] Tests passing
- [ ] Committed with atomic commit
