# Story 10.4: Prompt Extraction - Task Prompts

**Epic**: 10 - Prompt & Agent Abstraction
**Story Points**: 3
**Priority**: Medium
**Dependencies**: Story 10.5

---

## Story

**As a** developer
**I want** task orchestration prompts in YAML
**So that** I can customize GAO-Dev task behavior without code changes

---

## Acceptance Criteria

- [ ] `gao_dev/prompts/tasks/create_prd.yaml` created
- [ ] `gao_dev/prompts/tasks/create_architecture.yaml` created
- [ ] `gao_dev/prompts/tasks/create_story.yaml` created
- [ ] `gao_dev/prompts/tasks/implement_story.yaml` created
- [ ] `gao_dev/prompts/tasks/validate_story.yaml` created
- [ ] GAODevOrchestrator uses PromptLoader for all tasks
- [ ] No hardcoded task prompts in `orchestrator.py`
- [ ] All tests passing

---

## Technical Details

**Current**: 5+ hardcoded prompts in `gao_dev/orchestrator/orchestrator.py`
**Target**: 5 YAML templates in `gao_dev/prompts/tasks/`

**Template Example**:
```yaml
name: create_prd
description: "Task prompt for PRD creation by John"

user_prompt: |
  Use the John agent to create a Product Requirements Document for '{project_name}'.

  Follow the PRD workflow:
  1. Gather requirements
  2. Define features
  3. Document acceptance criteria
  4. Create PRD document

variables:
  project_name: ""
  agent: "John"
```

---

## Definition of Done

- [ ] 5 task prompts created
- [ ] GAODevOrchestrator updated
- [ ] All hardcoded task prompts removed
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Atomic commit
