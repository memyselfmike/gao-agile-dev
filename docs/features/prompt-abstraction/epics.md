# Epic Breakdown
## Prompt & Agent Configuration Abstraction System

**Feature**: Prompt & Agent Abstraction
**Epic 10**: Complete Abstraction System
**Total Story Points**: 37
**Estimated Duration**: 7 sprints (~14 weeks)

---

## Overview

Epic 10 transforms GAO-Dev from a hardcoded, domain-specific framework into a flexible, methodology-agnostic platform by:
1. Extracting 200+ lines of hardcoded prompts to YAML templates
2. Unifying all agent definitions under a single declarative schema
3. Building infrastructure for prompt loading, validation, and rendering
4. Enabling plugin-based extensibility for custom agents and methodologies

---

## Story Summary

| Story | Name | Points | Priority | Dependencies |
|-------|------|--------|----------|--------------|
| 10.1 | Agent Configuration Unification | 5 | High | None |
| 10.2 | Prompt Extraction - Brian | 3 | High | 10.5 |
| 10.3 | Prompt Extraction - Story Orchestrator | 5 | High | 10.5 |
| 10.4 | Prompt Extraction - Task Prompts | 3 | Medium | 10.5 |
| 10.5 | Prompt Management System | 8 | High | None |
| 10.6 | Schema Validation | 5 | Medium | 10.1, 10.5 |
| 10.7 | Plugin System Enhancement | 5 | Low | 10.1, 10.5, 10.6 |
| 10.8 | Migration & Cleanup | 3 | Medium | 10.1-10.7 |

**Total**: 37 story points

---

## Epic Phases

### Phase 1: Foundation (2 sprints)
**Stories**: 10.1, 10.5
**Goal**: Build core infrastructure

**Deliverables**:
- All 8 agents in YAML format (`.agent.yaml`)
- PromptLoader and PromptRegistry implemented
- AgentConfigLoader implemented
- Basic schema validation

**Success Criteria**:
- Can load agents from YAML
- Can load and render prompts from YAML
- All existing tests passing
- Zero regressions

### Phase 2: Prompt Migration (2 sprints)
**Stories**: 10.2, 10.3, 10.4
**Goal**: Extract all hardcoded prompts

**Deliverables**:
- Brian's 50-line analysis prompt in YAML
- Story Orchestrator's 170 lines of prompts in YAML
- Task prompts (5+) in YAML
- Reusable prompt fragments

**Success Criteria**:
- Zero hardcoded prompts in Python
- All orchestrators using PromptLoader
- Same functionality as before
- All tests updated and passing

### Phase 3: Quality & Extensions (2 sprints)
**Stories**: 10.6, 10.7
**Goal**: Add robustness and extensibility

**Deliverables**:
- JSON Schema validation for all configs
- Plugin API for custom agents
- Plugin API for custom prompts
- Comprehensive error handling
- Performance optimization

**Success Criteria**:
- Schema validation catching errors
- Plugins can register agents/prompts
- Clear error messages
- <5% performance overhead

### Phase 4: Cleanup (1 sprint)
**Stories**: 10.8
**Goal**: Remove legacy code and finalize

**Deliverables**:
- All hardcoded configs removed
- All duplicate code removed
- Migration guide
- Updated documentation
- Clean, production-ready codebase

**Success Criteria**:
- No legacy code remaining
- All docs updated
- Migration guide complete
- All tests passing

---

## Story Details

### Story 10.1: Agent Configuration Unification
**Points**: 5 | **Priority**: High | **Dependencies**: None

**Description**:
Migrate all 8 GAO-Dev agents from hardcoded Python dictionaries to declarative YAML format following the BMAD agent schema pattern.

**What Changes**:
- Create `.agent.yaml` for: mary, john, winston, sally, bob, amelia, murat, brian
- Extract tool lists from hardcoded dicts
- Update AgentFactory to use AgentConfigLoader
- Remove duplicate agent configurations

**Value**:
- Foundation for all other abstraction work
- Single source of truth for agent configs
- Easy to add new agents (drop in YAML file)
- Consistent format across all agents

**Technical Approach**:
- Implement AgentConfigLoader
- Create JSON schema for agent validation
- Migrate agents one-by-one (start with Amelia as proof of concept)
- Update tests to verify same functionality

**File**: `stories/epic-10/story-10.1.md`

---

### Story 10.2: Prompt Extraction - Brian
**Points**: 3 | **Priority**: High | **Dependencies**: 10.5

**Description**:
Extract Brian's 50-line complexity analysis prompt from `brian_orchestrator.py` to YAML template file.

**What Changes**:
- Create `prompts/agents/brian_analysis.yaml`
- Extract scale level definitions to `config/scale_levels.yaml`
- Extract assessment criteria to separate file
- Update BrianOrchestrator to use PromptLoader

**Value**:
- Can iterate on complexity analysis without code changes
- A/B test different analysis approaches
- Easier to improve workflow selection logic

**Technical Approach**:
- Create prompt template with variables
- Use `@config:` and `@file:` references
- Verify same JSON schema response format
- Update integration tests

**File**: `stories/epic-10/story-10.2.md`

---

### Story 10.3: Prompt Extraction - Story Orchestrator
**Points**: 5 | **Priority**: High | **Dependencies**: 10.5

**Description**:
Extract 170 lines of hardcoded prompts from `story_orchestrator.py` (story creation, implementation, validation) to YAML templates.

**What Changes**:
- Create `prompts/story_phases/story_creation.yaml`
- Create `prompts/story_phases/story_implementation.yaml`
- Create `prompts/story_phases/story_validation.yaml`
- Create reusable fragments in `prompts/common/`
- Update StoryOrchestrator to use PromptLoader

**Value**:
- Biggest single prompt extraction (170 lines)
- Easy to improve story workflows
- Reusable fragments for consistency
- Can customize per methodology

**Technical Approach**:
- Identify reusable fragments (responsibilities, output formats)
- Create fragment files in `prompts/common/`
- Use `@file:` references in main prompts
- Verify story workflow still works end-to-end

**File**: `stories/epic-10/story-10.3.md`

---

### Story 10.4: Prompt Extraction - Task Prompts
**Points**: 3 | **Priority**: Medium | **Dependencies**: 10.5

**Description**:
Extract 5+ task prompts from `orchestrator.py` (PRD creation, story creation, implementation, validation, architecture) to YAML templates.

**What Changes**:
- Create `prompts/tasks/create_prd.yaml`
- Create `prompts/tasks/create_story.yaml`
- Create `prompts/tasks/implement_story.yaml`
- Create `prompts/tasks/validate_story.yaml`
- Create `prompts/tasks/create_architecture.yaml`
- Update GAODevOrchestrator to use PromptLoader

**Value**:
- Complete prompt extraction (no more hardcoded prompts)
- Easy to customize orchestrator behavior
- Methodology-agnostic task definitions

**Technical Approach**:
- Extract task prompts to YAML
- Add agent recommendations as variables
- Update orchestrator methods
- Verify autonomous workflow selection works

**File**: `stories/epic-10/story-10.4.md`

---

### Story 10.5: Prompt Management System
**Points**: 8 | **Priority**: High | **Dependencies**: None

**Description**:
Build core infrastructure for loading, rendering, and managing prompts: PromptLoader, PromptRegistry, and template rendering with variable substitution.

**What Changes**:
- Implement `gao_dev/core/prompt_loader.py`
- Implement `gao_dev/core/prompt_registry.py`
- Implement PromptTemplate data model
- Add variable substitution (`{{var}}` syntax)
- Add reference resolution (`@file:`, `@config:`)
- Add caching for performance

**Value**:
- Foundation for all prompt extraction
- Reusable infrastructure
- Performance optimization (caching)
- Clean separation of concerns

**Technical Approach**:
- Use Mustache-style `{{variable}}` syntax
- Support `@file:path` for file references
- Support `@config:key` for config references
- Implement caching with lazy loading
- Comprehensive unit tests

**File**: `stories/epic-10/story-10.5.md`

---

### Story 10.6: Schema Validation
**Points**: 5 | **Priority**: Medium | **Dependencies**: 10.1, 10.5

**Description**:
Add JSON Schema validation for agent configurations and prompt templates to catch errors early and provide clear error messages.

**What Changes**:
- Create `schemas/agent.schema.json`
- Create `schemas/prompt.schema.json`
- Implement SchemaValidator
- Add validation to AgentConfigLoader
- Add validation to PromptLoader
- Add validation to health check

**Value**:
- Catch configuration errors early (at load time)
- Clear, actionable error messages
- Prevent invalid configs from causing runtime errors
- Documentation via schemas

**Technical Approach**:
- Use `jsonschema` library
- Define strict JSON schemas
- Validate on load
- Format error messages for clarity
- Add schema validation tests

**File**: `stories/epic-10/story-10.6.md`

---

### Story 10.7: Plugin System Enhancement
**Points**: 5 | **Priority**: Low | **Dependencies**: 10.1, 10.5, 10.6

**Description**:
Extend plugin system to support registering custom agents and prompts, enabling easy creation of domain-specific teams (legal, ops, research, etc.).

**What Changes**:
- Add `get_agent_definitions()` to BaseAgentPlugin
- Add `get_prompt_templates()` to BaseAgentPlugin
- Add prompt override mechanism to PromptRegistry
- Update PluginManager to load agent configs
- Update PluginManager to register prompts
- Create example plugin (e.g., legal team)

**Value**:
- Easy to create custom teams (gao-legal, gao-ops)
- Plugins can extend without modifying core
- Enable multi-domain use cases
- Demonstrate flexibility of abstraction

**Technical Approach**:
- Extend plugin API
- Add registration methods to registries
- Support prompt overrides (plugins override defaults)
- Create documentation and examples

**File**: `stories/epic-10/story-10.7.md`

---

### Story 10.8: Migration & Cleanup
**Points**: 3 | **Priority**: Medium | **Dependencies**: 10.1-10.7

**Description**:
Remove all legacy hardcoded configurations, update documentation, provide migration guide, and ensure clean, production-ready codebase.

**What Changes**:
- Remove hardcoded prompts from Python files
- Remove duplicate agent configurations
- Remove deprecated code paths
- Update all documentation
- Create migration guide for plugin developers
- Final testing and validation

**Value**:
- Clean, maintainable codebase
- No technical debt
- Clear documentation
- Smooth migration path for users

**Technical Approach**:
- Search for remaining hardcoded prompts/configs
- Remove deprecated code
- Update all docs to reflect new architecture
- Write migration guide with examples
- Final comprehensive testing

**File**: `stories/epic-10/story-10.8.md`

---

## Dependencies Graph

```
┌─────────┐     ┌─────────┐
│  10.1   │     │  10.5   │
│ Agents  │     │ Prompts │
└────┬────┘     └────┬────┘
     │               │
     │    ┌──────────┤
     │    │          │
     ▼    ▼          ▼
  ┌──────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │  10.6    │  │  10.2   │  │  10.3   │  │  10.4   │
  │ Schemas  │  │ Brian   │  │ Story   │  │ Tasks   │
  └────┬─────┘  └─────────┘  └─────────┘  └─────────┘
       │
       ▼
  ┌─────────┐
  │  10.7   │
  │ Plugins │
  └────┬────┘
       │
       ▼
  ┌─────────┐
  │  10.8   │
  │ Cleanup │
  └─────────┘
```

**Critical Path**: 10.5 (Prompt Management) is required for all prompt extraction stories

**Parallel Work**:
- 10.1 (Agents) can be done in parallel with 10.5 (Prompts)
- 10.2, 10.3, 10.4 can be done in parallel after 10.5 completes
- 10.6 and 10.7 can overlap once 10.1 and 10.5 are done

---

## Timeline

### Sprint 1-2: Foundation
- **Week 1-2**: Story 10.5 (Prompt Management System) - 8 points
- **Week 3-4**: Story 10.1 (Agent Configuration) - 5 points

**Milestone 1**: Infrastructure complete, can load agents/prompts from YAML

### Sprint 3-4: Prompt Migration
- **Week 5**: Story 10.2 (Brian prompts) - 3 points
- **Week 6**: Story 10.3 (Story Orchestrator prompts) - 5 points
- **Week 7-8**: Story 10.4 (Task prompts) - 3 points

**Milestone 2**: All prompts in YAML, zero hardcoded prompts

### Sprint 5-6: Quality & Extensions
- **Week 9-10**: Story 10.6 (Schema Validation) - 5 points
- **Week 11-12**: Story 10.7 (Plugin Enhancement) - 5 points

**Milestone 3**: Robust validation, plugin-ready

### Sprint 7: Cleanup
- **Week 13-14**: Story 10.8 (Migration & Cleanup) - 3 points

**Milestone 4**: Production-ready, clean codebase

---

## Success Metrics

### Before (Baseline)
- **Hardcoded prompts**: 200+ lines across 5+ files
- **Agent definition formats**: 3 different formats
- **Duplicate configurations**: 10+ instances
- **Time to add new agent**: 2+ hours (requires code changes)
- **Time to modify prompt**: 20+ minutes (code + testing)
- **Configuration errors**: High (no validation)

### After (Target)
- **Hardcoded prompts**: 0 lines
- **Agent definition formats**: 1 (YAML)
- **Duplicate configurations**: 0 instances
- **Time to add new agent**: <30 minutes (just YAML files)
- **Time to modify prompt**: <5 minutes (edit YAML, reload)
- **Configuration errors**: 90% reduction (schema validation)

### Key Performance Indicators
- **Prompt iteration speed**: 4x faster
- **Agent creation speed**: 4x faster
- **Plugin development**: 50% faster
- **Configuration errors**: 90% reduction
- **Performance overhead**: <5%

---

## Risks & Mitigations

### Risk 1: Performance Degradation
**Impact**: Medium
**Probability**: Low
**Mitigation**:
- Implement caching strategy (in-memory)
- Performance benchmarks after each story
- Target <5% overhead vs. hardcoded
- Optimize hot paths (agent creation, prompt rendering)

### Risk 2: Breaking Changes
**Impact**: High
**Probability**: Low
**Mitigation**:
- Comprehensive test coverage
- Backwards compatibility layer (v1.x)
- Gradual migration (one component at a time)
- Deprecation warnings for old APIs

### Risk 3: Schema Too Strict
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Flexible schemas (required vs. optional)
- Clear error messages with fix suggestions
- Escape hatches for advanced use cases
- Community feedback before finalizing schemas

### Risk 4: Migration Complexity
**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Clear migration guide
- Automated migration tools (future)
- Examples for common scenarios
- Support for questions during migration

---

## Out of Scope (Future Work)

### Prompt Versioning
- Multiple versions of same prompt in parallel
- A/B testing of prompt variations
- Gradual rollout of new prompts

### Prompt Analytics
- Track which prompts perform best
- Measure token usage per prompt
- Optimize prompts based on data

### Visual Prompt Editor
- GUI for editing prompts
- Live preview of rendered prompts
- Variable autocomplete

### Multi-Language Support
- Prompts in different languages
- Automatic translation

### Dynamic Prompts
- Prompts that adapt based on context
- Conditional prompt sections
- Prompt composition from fragments

---

## Related Documentation

- **PRD**: `PRD.md` - Product requirements and user stories
- **Architecture**: `ARCHITECTURE.md` - Technical design and components
- **Stories**: `stories/epic-10/story-10.{1-8}.md` - Detailed story specifications
- **BMAD Reference**: `bmad/bmm/agents/` - Example YAML agent format
- **Plugin Guide**: `docs/plugin-development-guide.md` - Plugin API documentation

---

## Approval & Sign-off

**Product Manager**: [ ] Approved
**Technical Architect**: [ ] Approved
**Scrum Master**: [ ] Approved
**Development Team**: [ ] Committed

**Date**: 2025-11-03
**Epic Start Date**: TBD
**Epic Target Completion**: TBD + 14 weeks
