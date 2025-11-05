# Story 13.6: Update Core Prompts to Use Meta-Prompts

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 4
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Update 10 core prompt templates to use meta-prompt references instead of hardcoded context. This demonstrates the value of the meta-prompt system and ensures backward compatibility while improving maintainability.

---

## Business Value

This story validates the meta-prompt system and provides immediate benefits:

- **Reduced Prompt Size**: Remove 50%+ of hardcoded context
- **Maintainability**: Context changes automatically reflected in prompts
- **Consistency**: Same references used across prompts
- **Validation**: Proves meta-prompt system works end-to-end
- **Examples**: Real-world examples for prompt engineers

---

## Acceptance Criteria

### Prompts to Update
- [ ] `tasks/create_prd.yaml` - Use @context: for project context
- [ ] `tasks/create_architecture.yaml` - Use @doc: for PRD, @context: for standards
- [ ] `tasks/create_story.yaml` - Use @context: for epic definition
- [ ] `tasks/implement_story.yaml` - Use @doc: for story + acceptance criteria
- [ ] `tasks/validate_story.yaml` - Use @checklist: for QA standards
- [ ] `brian/complexity_analysis.yaml` - Use @config: for scale levels
- [ ] `story_orchestrator/planning.yaml` - Use @query: for related stories
- [ ] `story_orchestrator/implementation.yaml` - Use @context: for architecture
- [ ] `story_orchestrator/testing.yaml` - Use @checklist: for test standards
- [ ] `story_orchestrator/validation.yaml` - Use @checklist: for validation

### Quality Requirements
- [ ] All updated prompts tested with workflows
- [ ] Backward compatibility maintained (can still render without meta-prompts)
- [ ] Prompt size reduced by 30%+ for each updated prompt
- [ ] No loss of context quality
- [ ] All variables properly substituted

### Documentation
- [ ] Before/after comparison for each prompt
- [ ] Migration guide for custom prompts
- [ ] Best practices for using meta-prompts
- [ ] Examples section in documentation

---

## Technical Notes

### Example Transformations

#### Before: create_story.yaml (Epic 10 version)

```yaml
name: create_story
description: "Task prompt for story creation by Bob"
version: 1.0.0

user_prompt: |
  Use the Bob agent to create a story file for Epic {{epic_num}}, Story {{story_num}}.

  Epic Context:
  {{epic_definition}}

  Related PRD:
  {{prd_content}}

  Bob should:
  1. Read the epic definition carefully
  2. Create detailed story file following template
  3. Include acceptance criteria
  4. Estimate story points

variables:
  epic_num: ""
  story_num: ""
  epic_definition: ""  # Must be passed in
  prd_content: ""      # Must be passed in
```

#### After: create_story.yaml (with meta-prompts)

```yaml
name: create_story
description: "Task prompt for story creation by Bob"
version: 2.0.0

user_prompt: |
  Use the Bob agent to create a story file for Epic {{epic_num}}, Story {{story_num}}.

  Epic Context:
  @context:epic_definition

  Related PRD:
  @context:prd

  Existing Stories (for context):
  @query:stories.where(epic={{epic_num}}, status!='cancelled').format('list')

  Bob should:
  1. Read the epic definition carefully
  2. Create detailed story file following template
  3. Include acceptance criteria
  4. Estimate story points

variables:
  epic_num: ""
  story_num: ""
  feature: ""  # For context resolution

meta_prompts:
  enabled: true
```

**Changes:**
- Removed `epic_definition` and `prd_content` variables (now auto-injected)
- Added `@context:` references for epic and PRD
- Added `@query:` for related stories list
- Enabled meta_prompts flag
- Reduced prompt size by ~40%

#### Before: implement_story.yaml

```yaml
user_prompt: |
  Implement Story {{epic}}.{{story}}.

  Story Requirements:
  {{story_content}}

  Acceptance Criteria:
  {{acceptance_criteria}}

  Epic Context:
  {{epic_definition}}

  Architecture Guidelines:
  {{architecture}}

  Coding Standards:
  {{coding_standards}}

  Quality Checklist:
  {{qa_checklist}}

variables:
  epic: ""
  story: ""
  story_content: ""
  acceptance_criteria: ""
  epic_definition: ""
  architecture: ""
  coding_standards: ""
  qa_checklist: ""
```

#### After: implement_story.yaml

```yaml
user_prompt: |
  Implement Story {{epic}}.{{story}}.

  Story Requirements:
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

  Acceptance Criteria:
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md#acceptance-criteria

  Epic Context:
  @context:epic_definition

  Architecture Guidelines:
  @context:architecture

  Coding Standards:
  @context:coding_standards

  Quality Checklists:
  @checklist:testing/unit-test-standards
  @checklist:code-quality/solid-principles

variables:
  epic: ""
  story: ""
  feature: ""

meta_prompts:
  enabled: true
```

**Changes:**
- Removed 6 content variables (story_content, acceptance_criteria, epic_definition, architecture, coding_standards, qa_checklist)
- Added @doc:, @context:, @checklist: references
- Reduced from 8 variables to 3
- Reduced prompt size by ~60%

### Testing Strategy

For each updated prompt:

1. **Unit Test**: Render with MetaPromptEngine, verify references resolved
2. **Integration Test**: Run through workflow, verify functionality unchanged
3. **Performance Test**: Measure rendering time (<200ms)
4. **Regression Test**: Ensure existing functionality works

**Files to Update:**
- `gao_dev/config/prompts/tasks/create_prd.yaml`
- `gao_dev/config/prompts/tasks/create_architecture.yaml`
- `gao_dev/config/prompts/tasks/create_story.yaml`
- `gao_dev/config/prompts/tasks/implement_story.yaml`
- `gao_dev/config/prompts/tasks/validate_story.yaml`
- `gao_dev/config/prompts/brian/complexity_analysis.yaml`
- `gao_dev/config/prompts/story_orchestrator/planning.yaml`
- `gao_dev/config/prompts/story_orchestrator/implementation.yaml`
- `gao_dev/config/prompts/story_orchestrator/testing.yaml`
- `gao_dev/config/prompts/story_orchestrator/validation.yaml`

**Files to Create:**
- `docs/MIGRATION_GUIDE_EPIC_13.md` - Migration guide for meta-prompts
- `docs/examples/meta-prompt-examples.md` - Examples and best practices

**Dependencies:**
- Story 13.5 (MetaPromptEngine)
- All resolvers (13.1-13.4)

---

## Testing Requirements

### Unit Tests

**Per Prompt:**
- [ ] Test rendering with MetaPromptEngine
- [ ] Test all references resolve correctly
- [ ] Test variables substituted properly
- [ ] Test missing variables handled
- [ ] Test backward compatibility (can render without meta-prompts)

**Integration Tests:**
- [ ] Test create_prd workflow end-to-end
- [ ] Test create_architecture workflow end-to-end
- [ ] Test create_story workflow end-to-end
- [ ] Test implement_story workflow end-to-end
- [ ] Test validate_story workflow end-to-end

### Regression Tests
- [ ] All existing workflows still work
- [ ] No loss of context quality
- [ ] Prompt rendering performance not degraded
- [ ] All automated tests pass

### Performance Tests
- [ ] Each prompt renders in <200ms
- [ ] No significant slowdown vs Epic 10 version
- [ ] Cache hit rate >70% for repeated prompts

**Test Coverage:** 100% of updated prompts tested

---

## Documentation Requirements

- [ ] Migration guide for custom prompts
- [ ] Before/after examples for all 10 prompts
- [ ] Best practices for using meta-prompts
- [ ] Reference syntax quick reference
- [ ] Troubleshooting guide
- [ ] Performance optimization tips

---

## Definition of Done

- [ ] All 10 core prompts updated
- [ ] All tests passing (no regressions)
- [ ] Documentation complete
- [ ] Migration guide published
- [ ] Backward compatibility verified
- [ ] Performance benchmarks met
- [ ] Examples provided
- [ ] Code reviewed and approved
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.6 - Update Core Prompts to Use Meta-Prompts

  - Update 10 core prompt templates with meta-prompt references
  - Replace hardcoded context with @doc:, @context:, @checklist:, @query: references
  - Reduce prompt size by 30-60% while maintaining functionality
  - Add meta_prompts.enabled flag to all updated prompts
  - Create migration guide and examples
  - Verify backward compatibility and performance

  Prompts updated:
  - tasks: create_prd, create_architecture, create_story, implement_story, validate_story
  - brian: complexity_analysis
  - story_orchestrator: planning, implementation, testing, validation

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
