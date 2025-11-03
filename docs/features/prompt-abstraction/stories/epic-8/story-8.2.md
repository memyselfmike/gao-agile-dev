# Story 8.2: Prompt Extraction - Brian's Complexity Analysis

**Epic**: 8 - Prompt & Agent Abstraction
**Story Points**: 3
**Priority**: High
**Status**: Pending
**Dependencies**: Story 8.5 (Prompt Management System)

---

## Story

**As a** developer
**I want** Brian's complexity analysis prompt in YAML template
**So that** I can iterate on workflow selection without code changes

---

## Description

Extract Brian's 50-line hardcoded complexity analysis prompt from `brian_orchestrator.py` to a YAML template file with variable substitution.

**Current**: 50 lines hardcoded in `gao_dev/orchestrator/brian_orchestrator.py:149-200`
**Target**: YAML template in `gao_dev/prompts/agents/brian_analysis.yaml`

---

## Acceptance Criteria

### 1. Prompt Template Created
- [ ] `gao_dev/prompts/agents/brian_analysis.yaml` created
- [ ] System prompt with Brian persona reference
- [ ] User prompt with variable placeholders
- [ ] All variables defined

### 2. Supporting Files Extracted
- [ ] `gao_dev/config/scale_levels.yaml` - Scale level definitions (Levels 0-4)
- [ ] `gao_dev/schemas/analysis_response.json` - JSON schema for response

### 3. BrianOrchestrator Updated
- [ ] Uses PromptLoader to load template
- [ ] Renders prompt with variables
- [ ] Same JSON response format
- [ ] No hardcoded prompt in code

### 4. Tests Passing
- [ ] All existing Brian tests pass
- [ ] Prompt rendering tested
- [ ] Same analysis results as before

---

## Technical Details

### Prompt Template Structure

**File**: `gao_dev/prompts/agents/brian_analysis.yaml`
```yaml
name: brian_complexity_analysis
description: "Analyze project complexity and recommend scale level"
version: 1.0.0

system_prompt: |
  You are Brian Thompson, a Senior Engineering Manager with 20 years of battle-tested experience.

  {brian_persona}

user_prompt: |
  Analyze this software development request and assess its scale level:

  User Request:
  {user_request}

  {scale_level_definitions}

  Assess: scale_level (0-4), project_type, estimated_stories, complexity, confidence

  Return JSON: {json_schema}

variables:
  scale_level_definitions: "@config:scale_levels.yaml"
  json_schema: "@file:../schemas/analysis_response.json"
  brian_persona: ""

response:
  max_tokens: 2048
  temperature: 0.7
  format: json
```

### Scale Levels Configuration

**File**: `gao_dev/config/scale_levels.yaml`
```yaml
scale_levels:
  0:
    name: "Chore"
    stories: "1 story"
    duration: "<1 hour"
    examples:
      - "Fix typo"
      - "Update docs"

  1:
    name: "Bug Fix"
    stories: "1-2 stories"
    duration: "1-4 hours"
    examples:
      - "Fix failing test"
      - "Resolve small bug"

  2:
    name: "Small Feature"
    stories: "3-10 stories, 1 epic"
    duration: "1-2 weeks"
    examples:
      - "Add authentication"
      - "New UI component"

  3:
    name: "Medium Feature"
    stories: "12-40 stories, 2-5 epics"
    duration: "1-2 months"
    examples:
      - "Complete module"
      - "Integration system"

  4:
    name: "Greenfield Application"
    stories: "40+ stories, 5+ epics"
    duration: "2-6 months"
    examples:
      - "New product"
      - "Complete rewrite"
```

### BrianOrchestrator Integration

**Before**:
```python
def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
    analysis_prompt = f"""You are Brian Thompson...
    {50 lines of hardcoded prompt}
    """
    response = self.anthropic.messages.create(...)
```

**After**:
```python
def __init__(self, project_root: Path, api_key: str):
    self.prompt_loader = PromptLoader(project_root / "gao_dev/prompts")
    self.prompt_registry = PromptRegistry(self.prompt_loader)

def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
    template = self.prompt_registry.get_prompt("brian_analysis")
    rendered = self.prompt_loader.render_prompt(
        template,
        variables={
            "user_request": prompt,
            "brian_persona": self._load_brian_persona(),
        }
    )
    response = self.anthropic.messages.create(
        messages=[{"role": "user", "content": rendered}],
        max_tokens=template.response.max_tokens
    )
```

---

## Testing

```python
def test_brian_prompt_loads():
    """Test Brian prompt loads from YAML."""
    loader = PromptLoader(Path("gao_dev/prompts"))
    template = loader.load_prompt("brian_analysis")

    assert template.name == "brian_complexity_analysis"
    assert "{{user_request}}" in template.user_prompt

def test_brian_prompt_renders():
    """Test prompt renders with variables."""
    loader = PromptLoader(Path("gao_dev/prompts"))
    template = loader.load_prompt("brian_analysis")

    rendered = loader.render_prompt(template, {
        "user_request": "Build a todo app",
        "brian_persona": "You are Brian...",
    })

    assert "Build a todo app" in rendered
    assert "{{" not in rendered  # No unresolved variables

def test_brian_analysis_same_results():
    """Verify same analysis results as hardcoded version."""
    orchestrator = BrianOrchestrator(project_root, api_key)
    result = orchestrator._analyze_prompt("Build a todo application")

    assert result.scale_level in [0, 1, 2, 3, 4]
    assert result.project_type in ["greenfield", "brownfield", ...]
```

---

## Definition of Done

- [ ] Prompt template YAML created
- [ ] Scale levels config created
- [ ] JSON schema created
- [ ] BrianOrchestrator updated
- [ ] Hardcoded prompt removed
- [ ] All tests passing
- [ ] Same functionality verified
- [ ] Code reviewed
- [ ] Atomic commit

---

## References

- **Current Code**: `gao_dev/orchestrator/brian_orchestrator.py:149-200`
- **PromptLoader**: Story 8.5
- **Architecture**: `docs/features/prompt-abstraction/ARCHITECTURE.md#promptloader`
