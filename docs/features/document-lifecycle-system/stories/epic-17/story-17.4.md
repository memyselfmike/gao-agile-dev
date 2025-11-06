# Story 17.4: Agent Prompt Integration

**Epic:** 17 - Context System Integration
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Update agent prompts and configurations to use AgentContextAPI for accessing project context. This makes agents context-aware by providing them with explicit instructions and code examples for accessing PRDs, architecture documents, epic definitions, and coding standards through the WorkflowContext API. The story orchestrator sets the context before agent execution, and context usage is automatically tracked for lineage.

---

## Business Value

This story makes agents intelligent by giving them access to full project context:

- **Agent Intelligence**: Agents can access full project context (PRDs, architecture)
- **Consistency**: All agents use same context access pattern
- **Autonomous Execution**: Agents work independently with complete information
- **Quality Improvement**: Agents reference coding standards and architecture
- **Reduced Rework**: Agents avoid mistakes by checking context first
- **Lineage Tracking**: Automatic tracking of what documents agents accessed
- **Developer Experience**: Clear examples in agent YAML configs
- **Debugging**: Context usage history shows what agents looked at
- **Observability**: Track which documents agents find most useful
- **Foundation for Analytics**: Context usage enables agent behavior analysis

---

## Acceptance Criteria

### Story Orchestrator Integration
- [ ] Story orchestrator sets WorkflowContext before agent execution
- [ ] Context includes feature, epic, story information
- [ ] Context persisted before agent call
- [ ] Thread-local context available during agent execution

### Agent Context Access
- [ ] Agents can call `get_workflow_context()` in prompt code
- [ ] Agents can access `context.get_epic_definition()` successfully
- [ ] Agents can access `context.get_architecture()` successfully
- [ ] Agents can access `context.get_coding_standards()` successfully
- [ ] Agents can access `context.get_prd()` successfully
- [ ] Context access returns actual document content (not None)

### Usage Tracking
- [ ] Context usage automatically tracked for lineage
- [ ] Usage records include agent name and document type
- [ ] Usage records include timestamp
- [ ] Multiple document accesses tracked separately

### Configuration Updates
- [ ] Agent YAML configs include context API import examples
- [ ] Agent prompts include instructions for context access
- [ ] Examples show how to use context in agent code
- [ ] All agent configs updated (Amelia, Bob, John, Winston, Sally, Murat)

### Testing
- [ ] Integration tests verify agents can access context
- [ ] Test agent accesses PRD via context
- [ ] Test agent accesses architecture via context
- [ ] Test agent accesses epic definition via context
- [ ] Test context usage tracked correctly

### Documentation
- [ ] Documentation shows complete agent usage examples
- [ ] Updated prompts work with real workflow executions
- [ ] Troubleshooting guide for context access issues

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/config/prompts/tasks/implement_story.yaml`

Update story implementation prompt to use context:

```yaml
name: implement_story
description: "Task prompt for story implementation by Amelia"
version: 1.0.0

user_prompt: |
  Use the Amelia agent to implement Story {{epic_number}}.{{story_number}}.

  IMPORTANT: Access project context before starting implementation:

  ```python
  from gao_dev.core.context import get_workflow_context

  # Get workflow context (automatically set by orchestrator)
  context = get_workflow_context()

  if context:
      # Get epic definition
      epic_def = context.get_epic_definition()
      if epic_def:
          print(f"Epic Definition:\\n{epic_def[:500]}...")

      # Get architecture guidelines
      architecture = context.get_architecture()
      if architecture:
          print(f"Architecture:\\n{architecture[:500]}...")

      # Get coding standards
      standards = context.get_coding_standards()
      if standards:
          print(f"Coding Standards:\\n{standards[:500]}...")
  ```

  Implementation Steps:
  1. Read story file: docs/features/{{feature_name}}/stories/epic-{{epic_number}}/story-{{epic_number}}.{{story_number}}.md
  2. Access context documents (PRD, architecture, epic)
  3. Understand acceptance criteria
  4. Write tests first (TDD)
  5. Implement functionality
  6. Run tests and validate
  7. Commit atomically

  Context Usage:
  - `context.get_prd()` - Product Requirements Document
  - `context.get_architecture()` - System architecture
  - `context.get_epic_definition()` - Current epic details
  - `context.get_story_definition()` - Current story details
  - `context.get_coding_standards()` - Coding guidelines

  All context access is automatically tracked for lineage.

variables:
  epic_number: ""
  story_number: ""
  feature_name: ""
  agent: "Amelia"

response:
  max_tokens: 8000
  temperature: 0.7
```

**File:** `gao_dev/config/prompts/story_orchestrator/implementation_phase.yaml`

Update story orchestrator to set context:

```yaml
name: story_implementation
description: "Story orchestrator implementation phase prompt"
version: 1.0.0

system_prompt: |
  You are the Story Orchestrator managing story implementation.

  CONTEXT MANAGEMENT:
  Before calling agents, you must set the WorkflowContext:

  ```python
  from gao_dev.core.context import WorkflowContext, set_workflow_context, ContextPersistence

  # Create workflow context
  context = WorkflowContext(
      workflow_id=workflow_id,
      feature_name="{{feature_name}}",
      epic_number={{epic_number}},
      story_number={{story_number}},
      phase="implementation",
      status="in_progress"
  )

  # Persist context
  persistence = ContextPersistence()
  persistence.save_context(context)

  # Set for agents to access
  set_workflow_context(context)
  ```

  Agents will automatically access context during execution.
  Context usage is tracked for lineage.

user_prompt: |
  Implement Story {{epic_number}}.{{story_number}} - {{story_title}}.

  1. Set WorkflowContext before calling agents
  2. Call Amelia agent to implement story
  3. Amelia will access context for PRD, architecture, epic
  4. Verify implementation meets acceptance criteria
  5. Ensure atomic commit

  Context will be automatically tracked.

variables:
  workflow_id: ""
  feature_name: ""
  epic_number: ""
  story_number: ""
  story_title: ""
```

**File:** `gao_dev/config/agents/amelia.yaml`

Update Amelia's configuration with context examples:

```yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    version: 2.0.0  # Updated for context integration

  persona:
    background: |
      You are Amelia, a Senior Software Developer who implements stories.

      You have access to full project context via WorkflowContext API:
      - PRDs (Product Requirements Documents)
      - System architecture
      - Epic definitions
      - Coding standards

      ALWAYS access context before starting implementation to understand:
      - Overall project goals (PRD)
      - System design (architecture)
      - Epic scope (epic definition)
      - Code quality standards (coding standards)

    responsibilities:
      - Access project context before implementation
      - Implement stories following architecture
      - Write tests first (TDD)
      - Follow coding standards from context
      - Commit atomically

    context_usage: |
      Use the AgentContextAPI to access documents:

      ```python
      from gao_dev.core.context import get_workflow_context

      context = get_workflow_context()
      if context:
          prd = context.get_prd()
          architecture = context.get_architecture()
          epic = context.get_epic_definition()
          standards = context.get_coding_standards()
      ```

  tools:
    - Read
    - Write
    - Edit
    - MultiEdit
    - Grep
    - Glob
    - Bash

  configuration:
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 8000
    temperature: 0.7
```

**Files to Modify:**
- `gao_dev/config/prompts/tasks/implement_story.yaml` - Add context access
- `gao_dev/config/prompts/tasks/validate_story.yaml` - Add context access
- `gao_dev/config/prompts/story_orchestrator/implementation_phase.yaml` - Set context
- `gao_dev/config/agents/amelia.yaml` - Add context examples
- `gao_dev/config/agents/bob.yaml` - Add context examples
- `gao_dev/config/agents/john.yaml` - Add context examples (for PRD creation)
- `gao_dev/config/agents/winston.yaml` - Add context examples (for architecture)

**Files to Create:**
- `tests/config/test_agent_context_integration.py` - Integration tests
- `docs/agent-context-usage-guide.md` - Developer guide

**Dependencies:**
- Story 17.3 (Orchestrator Integration)
- Story 16.5 (AgentContextAPI)

---

## Testing Requirements

### Integration Tests

**Agent Context Access:**
- [ ] Test agent can call get_workflow_context()
- [ ] Test agent can access PRD content
- [ ] Test agent can access architecture content
- [ ] Test agent can access epic definition
- [ ] Test agent can access coding standards
- [ ] Test context access returns actual content (not None)

**Usage Tracking:**
- [ ] Test context usage recorded in database
- [ ] Test usage includes agent name (e.g., "Amelia")
- [ ] Test usage includes document type (e.g., "architecture")
- [ ] Test usage includes timestamp
- [ ] Test multiple accesses tracked separately

**Story Orchestrator:**
- [ ] Test orchestrator sets context before agent call
- [ ] Test context persisted before agent execution
- [ ] Test agent can access context during execution

**End-to-End:**
- [ ] Test full story implementation with context access
- [ ] Test Amelia accesses architecture during implementation
- [ ] Test context lineage shows document flow
- [ ] Test multiple workflows have isolated contexts

### Unit Tests
- [ ] Test get_workflow_context() returns context from thread-local
- [ ] Test context access with no context set returns None
- [ ] Test prompt rendering includes context instructions
- [ ] Test agent YAML config parsing includes context_usage

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Update agent documentation with context access patterns
- [ ] Create agent-context-usage-guide.md with examples
- [ ] Document context API methods (get_prd, get_architecture, etc.)
- [ ] Add troubleshooting guide for context access issues
- [ ] Update story orchestrator documentation
- [ ] Document context usage tracking and lineage
- [ ] Add examples of real agent workflows with context
- [ ] Create video/screencast showing context in action (optional)

---

## Implementation Details

### Development Approach

**Phase 1: Prompt Updates**
1. Update task prompts (implement_story.yaml, validate_story.yaml)
2. Add context access instructions and code examples
3. Update story orchestrator prompts to set context

**Phase 2: Agent Config Updates**
1. Update all agent YAML configs (Amelia, Bob, John, Winston, Sally, Murat)
2. Add context_usage section with examples
3. Update agent personas to mention context access

**Phase 3: Testing**
1. Write integration tests for agent context access
2. Test usage tracking
3. Test end-to-end story implementation
4. Verify context lineage

**Phase 4: Documentation**
1. Create agent-context-usage-guide.md
2. Update all agent documentation
3. Add examples and troubleshooting
4. Create sequence diagrams

### Quality Gates
- [ ] All integration tests pass
- [ ] Agents can access context in real workflows
- [ ] Usage tracking working correctly
- [ ] All agent configs updated
- [ ] Documentation complete with examples
- [ ] No regression in existing agent functionality

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Story orchestrator sets WorkflowContext before agent execution
- [ ] Agents can call get_workflow_context() successfully
- [ ] Agents can access PRD, architecture, epic, standards
- [ ] Context usage automatically tracked for lineage
- [ ] All agent YAML configs updated with context examples
- [ ] Task prompts updated with context access instructions
- [ ] Integration tests pass (>80% coverage)
- [ ] Documentation complete with usage guide
- [ ] Real workflow executions use context
- [ ] Code reviewed and approved
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.4 - Agent Prompt Integration

  - Update task prompts to use AgentContextAPI
  - Add context access instructions to implement_story.yaml
  - Update story orchestrator to set WorkflowContext
  - Add context examples to all agent YAML configs
  - Document context_usage section in agent personas
  - Implement automatic usage tracking for lineage
  - Add integration tests for agent context access
  - Create agent-context-usage-guide.md
  - Update all agent documentation with examples

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
