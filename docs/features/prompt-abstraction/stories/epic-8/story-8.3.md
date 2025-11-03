# Story 8.3: Prompt Extraction - Story Orchestrator

**Epic**: 8 - Prompt & Agent Abstraction
**Story Points**: 5
**Priority**: High
**Status**: Pending
**Dependencies**: Story 8.5 (Prompt Management System)

---

## Story

**As a** developer
**I want** all story phase prompts extracted to YAML templates
**So that** I can improve story workflows without code changes

---

## Description

Extract 170 lines of hardcoded prompts from `story_orchestrator.py` to YAML templates:
- Story creation prompt (50 lines)
- Story implementation prompt (60 lines)
- Story validation prompt (60 lines)

**Current**: Hardcoded in `gao_dev/sandbox/benchmark/story_orchestrator.py:578-757`
**Target**: 3 YAML templates in `gao_dev/prompts/story_phases/`

---

## Acceptance Criteria

### 1. Prompt Templates Created
- [ ] `gao_dev/prompts/story_phases/story_creation.yaml` - Bob creates story spec
- [ ] `gao_dev/prompts/story_phases/story_implementation.yaml` - Amelia implements
- [ ] `gao_dev/prompts/story_phases/story_validation.yaml` - Murat validates

### 2. Reusable Fragments Created
- [ ] `gao_dev/prompts/common/responsibilities/scrum_master_story_creation.md`
- [ ] `gao_dev/prompts/common/responsibilities/developer_implementation.md`
- [ ] `gao_dev/prompts/common/responsibilities/test_architect_validation.md`
- [ ] `gao_dev/prompts/common/outputs/story_specification_format.md`
- [ ] `gao_dev/prompts/common/outputs/test_report_format.md`

### 3. StoryOrchestrator Updated
- [ ] `_create_story_creation_prompt()` uses PromptLoader
- [ ] `_create_story_implementation_prompt()` uses PromptLoader
- [ ] `_create_story_validation_prompt()` uses PromptLoader
- [ ] No hardcoded prompts in code

### 4. Tests Passing
- [ ] All story orchestrator tests pass
- [ ] Story workflow end-to-end tested
- [ ] Same story results as before

---

## Technical Details

### Story Creation Prompt

**File**: `gao_dev/prompts/story_phases/story_creation.yaml`
```yaml
name: story_creation
description: "Bob creates story specification"
version: 1.0.0

system_prompt: |
  You are {agent_name}, the Scrum Master for GAO-Dev.

user_prompt: |
  ## YOUR TASK: Create Specification for ONE Story

  **IMPORTANT**: Focus ONLY on this ONE story.

  ### Story Overview
  {story_overview}

  ### Predefined Acceptance Criteria
  {acceptance_criteria}

  ### Your Responsibilities
  {responsibilities}

  ### Output Required
  {output_format}

variables:
  agent_name: "Bob"
  story_overview: ""
  acceptance_criteria: ""
  responsibilities: "@file:../common/responsibilities/scrum_master_story_creation.md"
  output_format: "@file:../common/outputs/story_specification_format.md"

response:
  max_tokens: 4000
  temperature: 0.7
```

### Reusable Fragment Example

**File**: `gao_dev/prompts/common/responsibilities/scrum_master_story_creation.md`
```markdown
## Scrum Master Responsibilities for Story Creation

1. **Review the Story**: Understand what needs to be built for THIS ONE story
2. **Enhance Acceptance Criteria**: Add technical acceptance criteria if needed
3. **Identify Dependencies**: List any files or components this story depends on
4. **Define Technical Requirements**: Specify implementation details
5. **Create Story Document**: Document this ONE story for the developer

Remember:
- Focus on ONE story at a time
- Be specific and actionable
- Include clear acceptance criteria
- Identify all dependencies upfront
```

### StoryOrchestrator Integration

**Before**:
```python
def _create_story_creation_prompt(self, story: StoryConfig, result: StoryResult) -> str:
    return f"""You are Bob, the Scrum Master for GAO-Dev.
    {50+ lines of hardcoded prompt}
    """
```

**After**:
```python
def _create_story_creation_prompt(self, story: StoryConfig, result: StoryResult) -> str:
    template = self.prompt_registry.get_prompt("story_creation")
    return self.prompt_loader.render_prompt(
        template,
        variables={
            "story_overview": self._format_story_overview(story, result),
            "acceptance_criteria": self._format_criteria(story),
        }
    )
```

---

## Testing

```python
def test_story_prompts_load():
    """Test all 3 story prompts load."""
    loader = PromptLoader(Path("gao_dev/prompts"))

    creation = loader.load_prompt("story_creation")
    implementation = loader.load_prompt("story_implementation")
    validation = loader.load_prompt("story_validation")

    assert all([creation, implementation, validation])

def test_story_workflow_end_to_end():
    """Test complete story workflow."""
    orchestrator = StoryOrchestrator(...)

    result = orchestrator.execute_story(test_story)

    assert result.created
    assert result.implemented
    assert result.validated
    assert result.committed
```

---

## Definition of Done

- [ ] 3 prompt templates created
- [ ] 5+ reusable fragments created
- [ ] StoryOrchestrator updated
- [ ] 170 lines of hardcoded prompts removed
- [ ] All tests passing
- [ ] Same story workflow behavior
- [ ] Code reviewed
- [ ] Atomic commit

---

## References

- **Current Code**: `gao_dev/sandbox/benchmark/story_orchestrator.py:578-757`
- **Story**: Story 8.5 (PromptLoader)
