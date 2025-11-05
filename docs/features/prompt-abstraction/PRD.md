# Product Requirements Document
## GAO-Dev Prompt & Agent Configuration Abstraction System

**Version:** 1.0.0
**Date:** 2025-11-03
**Status:** Draft
**Author:** Product Strategy (via analysis and architectural review)

---

## Executive Summary

### Vision
Transform GAO-Dev into a truly methodology-agnostic, domain-flexible framework by abstracting all hardcoded prompts, agent definitions, and workflow instructions into declarative configuration files. Enable rapid creation of specialized autonomous teams (gao-ops, gao-research, gao-legal, etc.) without code modifications.

### Goals
1. **Eliminate Hardcoding**: Remove all hardcoded prompts and agent configurations from Python code
2. **Enable Extensibility**: Make it trivial to add new agents, modify prompts, or customize behaviors
3. **Support Multi-Domain**: Allow GAO framework to be used for operations, research, legal, finance, etc.
4. **Improve Maintainability**: Centralize all prompts in version-controlled, testable configuration files
5. **Preserve Quality**: Maintain existing functionality while improving architecture

---

## Problem Statement

### Current State
**Pain Points:**
- **200+ lines of hardcoded prompts** scattered across Python files
  - Brian's complexity analysis: 50 lines in `brian_orchestrator.py`
  - Story orchestrator: 170 lines across 3 phases in `story_orchestrator.py`
  - Task prompts: 5+ prompts in `orchestrator.py`
  - Commit message templates hardcoded in Python
- **Mixed agent definition styles**: Some use markdown, some use Python dictionaries, no consistent schema
- **Duplicate configurations**: Agent tools duplicated in multiple files
- **No validation**: Easy to introduce errors with inconsistent formats
- **Tight coupling**: Prompts mixed with business logic, impossible to modify without code changes
- **Domain-specific assumptions**: Hardcoded for software engineering (Bob, Amelia, etc.)

**Impact:**
- Cannot customize prompts without modifying code
- Difficult to create non-engineering teams (ops, research, legal)
- No A/B testing of prompt variations
- Hard to maintain and improve prompts over time
- Plugin developers can't easily extend with custom agents
- Methodology changes require code modifications

### Target State
**Desired End State:**
- All prompts in YAML/JSON configuration files
- Unified agent definition format (following BMAD agent.yaml pattern)
- Declarative prompt templates with variable substitution
- JSON Schema validation for all configurations
- Plugin-friendly architecture for custom agents/prompts
- No code changes needed to add agents or modify prompts
- Methodology-agnostic foundation

---

## Features

### Core Features

#### 1. **Unified Agent Configuration System**
   - **Description**: Standardize all agent definitions using declarative YAML format
   - **Priority**: High (Foundation for all other features)
   - **Current State**:
     - Agent personas in `.md` files (good)
     - Hardcoded Python dictionaries in `agent_factory.py` (bad)
     - Duplicate tool lists in multiple locations (bad)
   - **Target State**:
     ```yaml
     # gao_dev/agents/amelia.agent.yaml
     agent:
       metadata:
         name: Amelia
         role: Software Developer
         icon: 💻

       persona_file: ./amelia.md  # Keep markdown separate

       tools:
         - Read
         - Write
         - Edit
         - Bash
         - Grep
         - Glob

       capabilities:
         - implementation
         - code_review

       model: claude-sonnet-4-5-20250929

       workflows:
         - dev-story
         - review-story
     ```
   - **Benefits**:
     - Single source of truth for agent config
     - Easy to add new agents (drop in YAML file)
     - No code changes for configuration
     - Consistent with BMAD agent format
   - **Success Criteria**:
     - All 8 GAO-Dev agents in YAML format
     - AgentFactory loads from YAML, not hardcoded dicts
     - Zero duplicate configuration
     - Plugin agents use same format

#### 2. **Centralized Prompt Management**
   - **Description**: Extract all hardcoded prompts to YAML template files
   - **Priority**: High (Biggest pain point)
   - **Prompts to Extract**:

     **Agent Prompts** (`gao_dev/prompts/agents/`):
     - `brian_analysis.yaml` - Complexity assessment prompt (50 lines)

     **Story Phase Prompts** (`gao_dev/prompts/story_phases/`):
     - `story_creation.yaml` - Bob's story creation prompt (50 lines)
     - `story_implementation.yaml` - Amelia's implementation prompt (60 lines)
     - `story_validation.yaml` - Murat's validation prompt (60 lines)

     **Task Prompts** (`gao_dev/prompts/tasks/`):
     - `create_prd.yaml` - John's PRD creation
     - `create_story.yaml` - Bob's story creation
     - `implement_story.yaml` - Full workflow prompt
     - `validate_story.yaml` - Murat's validation
     - `create_architecture.yaml` - Winston's architecture

   - **Prompt Template Format**:
     ```yaml
     name: brian_complexity_analysis
     description: "Analyze project complexity and scale"

     system_prompt: |
       You are Brian Thompson, a Senior Engineering Manager.
       {brian_persona}

     user_prompt: |
       Analyze this request and assess scale level:

       User Request:
       {user_request}

       {scale_level_definitions}

       Return JSON: {json_schema}

     variables:
       scale_level_definitions: "@config:bmad/scale_levels.yaml"
       json_schema: "@file:schemas/analysis_response.json"

     max_tokens: 2048
     temperature: 0.7
     ```

   - **Success Criteria**:
     - Zero hardcoded prompts in Python files
     - All prompts in `gao_dev/prompts/`
     - Variable substitution working
     - Can modify prompts without code changes

#### 3. **Prompt Management Infrastructure**
   - **Description**: Build system for loading, rendering, and validating prompts
   - **Priority**: High (Enables all prompt extraction)
   - **Components**:

     **PromptLoader** (`gao_dev/core/prompt_loader.py`):
     ```python
     class PromptLoader:
         """Load and render prompt templates."""

         def load_prompt(self, prompt_name: str) -> PromptTemplate:
             """Load prompt from YAML."""

         def render_prompt(self, template: PromptTemplate,
                          variables: Dict) -> str:
             """Render prompt with variables."""

         def validate_prompt(self, template: PromptTemplate) -> bool:
             """Validate against JSON schema."""
     ```

     **PromptRegistry** (`gao_dev/core/prompt_registry.py`):
     ```python
     class PromptRegistry:
         """Registry of all prompts."""

         def register_prompt(self, prompt: PromptTemplate)
         def get_prompt(self, name: str) -> PromptTemplate
         def list_prompts(self) -> List[str]
     ```

     **PromptTemplate Model**:
     ```python
     @dataclass
     class PromptTemplate:
         name: str
         description: str
         system_prompt: Optional[str]
         user_prompt: str
         variables: Dict[str, Any]
         schema: Optional[Dict]  # For JSON responses
         max_tokens: int = 4000
         temperature: float = 0.7
     ```

   - **Features**:
     - Variable resolution with `{{mustache}}` syntax
     - Reference files: `@file:path/to/file.md`
     - Reference config: `@config:config_key`
     - JSON schema for structured responses
   - **Success Criteria**:
     - All prompts loadable from YAML
     - Variable substitution working
     - References resolved correctly
     - Caching for performance

#### 4. **JSON Schema Validation**
   - **Description**: Enforce consistent formats with schema validation
   - **Priority**: Medium (Quality assurance)
   - **Schemas**:

     **Agent Schema** (`gao_dev/schemas/agent.schema.json`):
     ```json
     {
       "$schema": "http://json-schema.org/draft-07/schema#",
       "type": "object",
       "required": ["agent"],
       "properties": {
         "agent": {
           "type": "object",
           "required": ["metadata", "tools"],
           "properties": {
             "metadata": {
               "type": "object",
               "required": ["name", "role"],
               "properties": {
                 "name": {"type": "string"},
                 "role": {"type": "string"}
               }
             },
             "tools": {
               "type": "array",
               "items": {"type": "string"}
             }
           }
         }
       }
     }
     ```

     **Prompt Schema** (`gao_dev/schemas/prompt.schema.json`)
     **Workflow Schema** (already exists for benchmarks)

   - **Validation Points**:
     - Agent YAML loaded → validate against agent schema
     - Prompt YAML loaded → validate against prompt schema
     - Startup health check validates all configs
   - **Success Criteria**:
     - All schemas defined
     - Validation integrated into loaders
     - Clear error messages for invalid configs
     - Tests for schema validation

#### 5. **Plugin System Enhancement**
   - **Description**: Enable plugins to register custom agents and prompts
   - **Priority**: Low (Nice to have)
   - **Plugin API Extensions**:
     ```python
     class BaseAgentPlugin:
         def get_agent_definitions(self) -> List[AgentConfig]:
             """Return custom agent configurations."""
             return []

         def get_prompt_templates(self) -> List[PromptTemplate]:
             """Return custom prompts for this agent."""
             return []
     ```

   - **Example Plugin**:
     ```python
     class LegalTeamPlugin(BaseAgentPlugin):
         def get_agent_definitions(self):
             return [load_agent_yaml("legal/laura.agent.yaml")]

         def get_prompt_templates(self):
             return [load_prompt_yaml("legal/contract_review.yaml")]
     ```

   - **Success Criteria**:
     - Plugins can register agents
     - Plugins can register prompts
     - Plugin prompts override defaults
     - Documentation for plugin development

#### 6. **Configuration Migration & Cleanup**
   - **Description**: Remove all legacy hardcoded configurations
   - **Priority**: Medium (Cleanup after migration)
   - **Tasks**:
     - Remove hardcoded prompts from Python
     - Remove duplicate agent configurations
     - Update all tests to use new system
     - Add deprecation warnings for old APIs
     - Update documentation
   - **Backwards Compatibility**:
     - Maintain old API for 1 version
     - Add deprecation warnings
     - Provide migration guide
     - Remove in v2.0
   - **Success Criteria**:
     - No hardcoded prompts in Python (except constants)
     - Zero duplicate configurations
     - All tests passing
     - Documentation updated

---

## Technical Requirements

### File Structure After Abstraction

```
gao-agile-dev/
├── gao_dev/
│   ├── agents/
│   │   ├── amelia.agent.yaml          # Agent config (NEW)
│   │   ├── amelia.md                  # Agent persona (existing)
│   │   ├── bob.agent.yaml
│   │   ├── bob.md
│   │   └── ... (all 8 agents)
│   │
│   ├── prompts/                        # NEW: All prompts here
│   │   ├── agents/                     # Agent-specific prompts
│   │   │   ├── brian_analysis.yaml
│   │   │   └── ...
│   │   ├── story_phases/               # Story workflow prompts
│   │   │   ├── story_creation.yaml
│   │   │   ├── story_implementation.yaml
│   │   │   └── story_validation.yaml
│   │   ├── tasks/                      # Task prompts
│   │   │   ├── create_prd.yaml
│   │   │   ├── create_story.yaml
│   │   │   └── ...
│   │   └── common/                     # Reusable fragments
│   │       ├── responsibilities/
│   │       ├── outputs/
│   │       └── guidelines/
│   │
│   ├── schemas/                        # NEW: JSON schemas
│   │   ├── agent.schema.json
│   │   ├── prompt.schema.json
│   │   └── workflow.schema.json
│   │
│   ├── core/
│   │   ├── prompt_loader.py            # NEW
│   │   ├── prompt_registry.py          # NEW
│   │   └── ...
│   │
│   └── config/
│       ├── defaults.yaml
│       ├── scale_levels.yaml           # NEW: Extract from code
│       └── commit_templates.yaml       # NEW
```

### Performance Requirements
- Prompt loading: <100ms for cold load, <10ms cached
- No more than 5% overhead from abstraction layer
- Schema validation: <50ms per config

### Quality Requirements
- All existing tests must pass
- New tests for prompt loading/rendering
- Schema validation tests
- Integration tests for agent creation
- Performance benchmarks

---

## User Stories & Acceptance Criteria

### Epic 8.1: Agent Configuration Unification (5 points)
**As a** developer
**I want** all agent configurations in YAML format
**So that** I can add/modify agents without touching code

**Acceptance Criteria:**
- [ ] All 8 agents have `.agent.yaml` files
- [ ] AgentFactory loads from YAML
- [ ] Tool lists extracted to config
- [ ] No duplicate configurations
- [ ] All tests passing

### Epic 8.2: Prompt Extraction - Brian (3 points)
**As a** developer
**I want** Brian's analysis prompt in YAML
**So that** I can iterate on complexity assessment without code changes

**Acceptance Criteria:**
- [ ] `prompts/agents/brian_analysis.yaml` created
- [ ] Scale level definitions extracted to config
- [ ] BrianOrchestrator uses PromptLoader
- [ ] Same behavior as before
- [ ] Tests updated

### Epic 8.3: Prompt Extraction - Story Orchestrator (5 points)
**As a** developer
**I want** all story phase prompts in YAML
**So that** I can improve story workflows easily

**Acceptance Criteria:**
- [ ] 3 story phase prompts extracted
- [ ] Reusable fragments created
- [ ] StoryOrchestrator uses PromptLoader
- [ ] Same behavior as before
- [ ] Tests updated

### Epic 8.4: Prompt Extraction - Task Prompts (3 points)
**As a** developer
**I want** task prompts in YAML
**So that** I can customize orchestrator behavior

**Acceptance Criteria:**
- [ ] 5+ task prompts extracted
- [ ] GAODevOrchestrator uses PromptLoader
- [ ] Same behavior as before
- [ ] Tests updated

### Epic 8.5: Prompt Management System (8 points)
**As a** developer
**I want** prompt loading infrastructure
**So that** prompts can be managed declaratively

**Acceptance Criteria:**
- [ ] PromptLoader implemented
- [ ] PromptRegistry implemented
- [ ] Variable substitution working
- [ ] File/config references working
- [ ] Comprehensive tests
- [ ] Performance benchmarks

### Epic 8.6: Schema Validation (5 points)
**As a** developer
**I want** schema validation for configs
**So that** errors are caught early

**Acceptance Criteria:**
- [ ] Agent schema defined
- [ ] Prompt schema defined
- [ ] Validation in loaders
- [ ] Clear error messages
- [ ] Schema validation tests

### Epic 8.7: Plugin System Enhancement (5 points)
**As a** plugin developer
**I want** to register custom agents/prompts
**So that** I can extend GAO-Dev easily

**Acceptance Criteria:**
- [ ] Plugin API for agents
- [ ] Plugin API for prompts
- [ ] Prompt override mechanism
- [ ] Plugin tests
- [ ] Documentation updated

### Epic 8.8: Migration & Cleanup (3 points)
**As a** developer
**I want** all legacy code removed
**So that** the codebase is clean

**Acceptance Criteria:**
- [ ] No hardcoded prompts in Python
- [ ] No duplicate configs
- [ ] All tests updated
- [ ] Documentation updated
- [ ] Migration guide provided

---

## Success Metrics

### Before (Current State)
- Hardcoded prompts: 200+ lines across 5+ files
- Agent definitions: 3 different formats
- Duplicate configurations: 10+ instances
- Code changes required for: Agent modifications, prompt updates, tool changes

### After (Target State)
- Hardcoded prompts: 0 lines
- Agent definitions: 1 format (YAML)
- Duplicate configurations: 0 instances
- Code changes required for: None (all config-driven)

### KPIs
- **Time to add new agent**: <30 minutes (vs. 2+ hours)
- **Prompt iteration speed**: <5 minutes (vs. 20+ minutes)
- **Configuration errors**: 90% reduction (schema validation)
- **Plugin development**: 50% faster (standardized format)

---

## Risks & Mitigations

### Technical Risks

**Risk 1: Performance degradation from abstraction layer**
- **Impact**: Medium
- **Mitigation**: Implement caching, performance benchmarks, lazy loading

**Risk 2: Breaking changes to existing code**
- **Impact**: High
- **Mitigation**: Backwards compatibility layer, comprehensive tests, gradual migration

**Risk 3: Schema validation too strict**
- **Impact**: Low
- **Mitigation**: Flexible schemas, clear error messages, escape hatches

### Organizational Risks

**Risk 1: Learning curve for new format**
- **Impact**: Low
- **Mitigation**: Clear documentation, examples, migration guide

**Risk 2: YAML complexity**
- **Impact**: Low
- **Mitigation**: Simple schemas, validation, good examples

---

## Dependencies

### Internal Dependencies
- Core config loader (exists)
- Workflow registry (exists)
- Plugin system (exists)
- Agent factory (exists, needs refactor)

### External Dependencies
- PyYAML (already installed)
- jsonschema (need to add)
- pydantic (already installed)

---

## Timeline & Milestones

### Phase 1: Foundation (Stories 8.1, 8.5)
**Duration**: 2 sprints
- Agent configuration unification
- Prompt management infrastructure
- **Milestone**: Can load agents and prompts from YAML

### Phase 2: Prompt Migration (Stories 8.2, 8.3, 8.4)
**Duration**: 2 sprints
- Extract Brian's prompts
- Extract story orchestrator prompts
- Extract task prompts
- **Milestone**: All prompts in YAML, same functionality

### Phase 3: Quality & Extensions (Stories 8.6, 8.7)
**Duration**: 2 sprints
- Schema validation
- Plugin system enhancements
- **Milestone**: Robust validation, plugin-ready

### Phase 4: Cleanup (Story 8.8)
**Duration**: 1 sprint
- Remove legacy code
- Update documentation
- **Milestone**: Clean codebase, docs complete

**Total Estimated Duration**: 7 sprints (~14 weeks)

---

## Appendix

### References
- BMAD agent YAML format: `bmad/bmm/agents/*.agent.yaml`
- Current agent implementations: `gao_dev/agents/`
- Hardcoded prompts analysis: (from initial analysis)
- Plugin development guide: `docs/plugin-development-guide.md`

### Glossary
- **Prompt Template**: YAML file containing system/user prompts with variables
- **Agent Configuration**: YAML file defining agent metadata, tools, capabilities
- **Schema Validation**: JSON Schema-based validation of configuration files
- **Variable Substitution**: Replacing `{{variable}}` placeholders in templates

### Version History
- **1.0.0** (2025-11-03): Initial PRD creation
