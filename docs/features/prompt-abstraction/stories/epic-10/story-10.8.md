# Story 10.8: Migration & Cleanup

**Epic**: 10 - Prompt & Agent Abstraction
**Story Points**: 3
**Priority**: Medium
**Dependencies**: All stories 10.1-10.7

---

## Story

**As a** developer
**I want** all legacy code removed and docs updated
**So that** the codebase is clean and production-ready

---

## Acceptance Criteria

### 1. Legacy Code Removed
- [ ] All hardcoded prompts removed from Python
- [ ] All duplicate agent configs removed
- [ ] Deprecated code paths removed
- [ ] No legacy imports or references

### 2. Documentation Updated
- [ ] Architecture docs reflect new system
- [ ] Plugin development guide updated
- [ ] Agent creation guide written
- [ ] Prompt creation guide written
- [ ] Migration guide for users

### 3. Migration Guide Created
- [ ] How to migrate custom agents to YAML
- [ ] How to extract hardcoded prompts
- [ ] Examples for common scenarios
- [ ] Backwards compatibility notes

### 4. Final Validation
- [ ] All 400+ tests passing
- [ ] Performance benchmarks pass (<5% overhead)
- [ ] Health check validates all configs
- [ ] No regressions in functionality

### 5. Cleanup
- [ ] Remove commented-out code
- [ ] Remove unused imports
- [ ] Format all files (Black)
- [ ] Lint all files (Ruff)

---

## Migration Guide Outline

```markdown
# Migration Guide: Hardcoded to YAML

## For Agent Developers

### Before (Hardcoded)
```python
builtin_agents = {
    "mary": {
        "name": "Mary",
        "tools": ["Read", "Write"]
    }
}
```

### After (YAML)
```yaml
# mary.agent.yaml
agent:
  metadata:
    name: Mary
  tools:
    - Read
    - Write
```

## For Prompt Developers

### Before (Hardcoded)
```python
prompt = f"""You are {agent}...
{50 lines}
"""
```

### After (YAML)
```yaml
# my_prompt.yaml
name: my_prompt
user_prompt: |
  You are {{agent}}...
```

## Breaking Changes

None - backwards compatible for 1 version.

## Deprecations

- Hardcoded agent dicts (removed in v2.0)
- Hardcoded prompts in code (removed in v2.0)
```

---

## Definition of Done

- [ ] All hardcoded code removed
- [ ] All duplicate configs removed
- [ ] Documentation complete
- [ ] Migration guide written
- [ ] All tests passing
- [ ] Performance validated
- [ ] Code formatted and linted
- [ ] Final review
- [ ] Atomic commit
