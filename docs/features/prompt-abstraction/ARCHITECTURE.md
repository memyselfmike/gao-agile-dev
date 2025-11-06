---
document:
  type: "architecture"
  state: "archived"
  created: "2025-11-03"
  last_modified: "2025-11-06"
  author: "Winston"
  feature: "prompt-abstraction"
  epic: null
  story: null
  related_documents:
    - "PRD.md"
    - "epics.md"
    - "../../MIGRATION_GUIDE_EPIC_10.md"
  replaces: null
  replaced_by: null
---

# System Architecture
## GAO-Dev Prompt & Agent Configuration Abstraction System

**Version:** 1.0.0
**Date:** 2025-11-03
**Author:** Technical Architecture Team
**Status:** Draft

---

## Table of Contents
1. [System Context](#system-context)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Directory Structure](#directory-structure)
8. [Interface Definitions](#interface-definitions)
9. [Migration Strategy](#migration-strategy)
10. [Performance Considerations](#performance-considerations)

---

## System Context

### Purpose
The Prompt & Agent Abstraction System transforms GAO-Dev from a hardcoded, domain-specific framework into a flexible, methodology-agnostic platform by:
- Extracting all hardcoded prompts to declarative YAML templates
- Unifying agent definitions under a single schema
- Providing infrastructure for prompt loading, validation, and rendering
- Enabling plugin-based extensibility for custom agents and prompts

### Key Stakeholders
- **Core GAO-Dev Developers**: Maintain and improve prompts without code changes
- **Plugin Developers**: Create custom agents and methodologies easily
- **Multi-Domain Teams**: Use GAO framework for ops, research, legal, etc.
- **System Integrators**: Embed GAO-Dev in larger systems with custom configurations

### System Boundaries
**In Scope:**
- Agent configuration unification
- Prompt extraction and templating
- Prompt loading and rendering infrastructure
- JSON Schema validation
- Plugin API extensions
- Migration from hardcoded to declarative

**Out of Scope:**
- Agent execution logic (unchanged)
- Workflow orchestration (unchanged)
- CLI interface (minimal changes)
- Benchmark system (no changes)

---

## Architecture Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Application Layer                            │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Orchestrators  │  │  Agent Factory   │  │  Workflow Mgr   │  │
│  └────────┬───────┘  └────────┬─────────┘  └────────┬────────┘  │
└───────────┼──────────────────┼─────────────────────┼────────────┘
            │                  │                     │
┌───────────▼──────────────────▼─────────────────────▼────────────┐
│                 Abstraction Layer (NEW)                          │
│  ┌────────────────────┐  ┌────────────────────┐                 │
│  │  PromptRegistry    │  │  AgentRegistry     │                 │
│  └─────────┬──────────┘  └─────────┬──────────┘                 │
│            │                       │                             │
│  ┌─────────▼──────────┐  ┌─────────▼──────────┐                 │
│  │  PromptLoader      │  │  AgentLoader       │                 │
│  └─────────┬──────────┘  └─────────┬──────────┘                 │
│            │                       │                             │
│  ┌─────────▼──────────────────────▼──────────┐                  │
│  │       Schema Validator                    │                  │
│  └───────────────────────────────────────────┘                  │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│                 Configuration Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Agents    │  │   Prompts    │  │   Schemas    │           │
│  │   (YAML)    │  │   (YAML)     │  │   (JSON)     │           │
│  └─────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Before vs. After Architecture

#### Before (Current State)

```
┌────────────────────────────────────────┐
│      BrianOrchestrator                 │
│  ┌──────────────────────────────────┐  │
│  │  50-line hardcoded prompt        │  │ <-- PROBLEM
│  │  Scale levels hardcoded          │  │ <-- PROBLEM
│  │  JSON schema in string           │  │ <-- PROBLEM
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│      AgentFactory                      │
│  ┌──────────────────────────────────┐  │
│  │  Hardcoded Python dict           │  │ <-- PROBLEM
│  │  {                               │  │
│  │    "mary": {...},                │  │
│  │    "amelia": {...}               │  │
│  │  }                               │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

#### After (Target State)

```
┌────────────────────────────────────────┐
│      BrianOrchestrator                 │
│  ┌──────────────────────────────────┐  │
│  │  prompt = loader.load_prompt(   │  │ <-- SOLUTION
│  │    "brian_analysis"              │  │
│  │  )                               │  │
│  │  rendered = loader.render(...)   │  │
│  └──────────────────────────────────┘  │
└──────────┬─────────────────────────────┘
           │
           ▼
     gao_dev/prompts/agents/brian_analysis.yaml
```

```
┌────────────────────────────────────────┐
│      AgentFactory                      │
│  ┌──────────────────────────────────┐  │
│  │  config = loader.load_agent(     │  │ <-- SOLUTION
│  │    "amelia"                      │  │
│  │  )                               │  │
│  │  agent = create_from_config(...)│  │
│  └──────────────────────────────────┘  │
└──────────┬─────────────────────────────┘
           │
           ▼
     gao_dev/agents/amelia.agent.yaml
```

---

## Component Design

### 1. PromptLoader

**Purpose**: Load and render prompt templates from YAML files

**Responsibilities**:
- Load YAML prompt templates from disk
- Validate against prompt schema
- Render templates with variable substitution
- Resolve file and config references
- Cache loaded prompts for performance

**Interface**:
```python
class PromptLoader:
    """Load and render prompt templates from YAML files."""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}
        self._validator = SchemaValidator()

    def load_prompt(self, prompt_name: str) -> PromptTemplate:
        """
        Load prompt template by name.

        Args:
            prompt_name: Name of prompt (e.g., "brian_analysis")

        Returns:
            PromptTemplate with all metadata

        Raises:
            FileNotFoundError: If prompt file not found
            ValidationError: If prompt invalid
        """

    def render_prompt(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render prompt template with variables.

        Args:
            template: Prompt template to render
            variables: Variables to substitute

        Returns:
            Fully rendered prompt string

        Supports:
            - {{variable}} - Simple variable substitution
            - @file:path - Include file contents
            - @config:key - Include config value
        """

    def validate_prompt(self, template: PromptTemplate) -> bool:
        """
        Validate prompt against schema.

        Args:
            template: Prompt template to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with details
        """

    def clear_cache(self):
        """Clear prompt cache (for testing)."""
```

**Key Design Decisions**:
- Use caching to avoid repeated file I/O
- Lazy loading (load on demand, not at startup)
- Mustache-style variable syntax (`{{var}}`) for familiarity
- Support `@file:` and `@config:` references for reusability
- Validate on load to fail fast

### 2. PromptRegistry

**Purpose**: Central registry of all available prompts

**Responsibilities**:
- Discover prompts in prompts directory
- Provide prompt lookup by name
- Support prompt categories (agents, tasks, story_phases)
- Enable plugin prompt registration
- Handle prompt overrides

**Interface**:
```python
class PromptRegistry:
    """Registry of all prompts in the system."""

    def __init__(self, loader: PromptLoader):
        self.loader = loader
        self._prompts: Dict[str, PromptTemplate] = {}
        self._categories: Dict[str, List[str]] = {}

    def discover_prompts(self, directory: Path):
        """
        Scan directory for prompt YAML files.

        Args:
            directory: Directory to scan (recursive)

        Populates internal registry with found prompts.
        """

    def register_prompt(
        self,
        prompt: PromptTemplate,
        category: Optional[str] = None
    ):
        """
        Register a prompt manually (for plugins).

        Args:
            prompt: Prompt template to register
            category: Optional category (e.g., "plugin-legal")
        """

    def get_prompt(self, name: str) -> PromptTemplate:
        """
        Get prompt by name.

        Args:
            name: Prompt name

        Returns:
            PromptTemplate

        Raises:
            KeyError: If prompt not found
        """

    def list_prompts(
        self,
        category: Optional[str] = None
    ) -> List[str]:
        """
        List all prompt names, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of prompt names
        """

    def override_prompt(
        self,
        name: str,
        prompt: PromptTemplate
    ):
        """
        Override an existing prompt (for customization).

        Args:
            name: Prompt name to override
            prompt: New prompt template
        """
```

**Key Design Decisions**:
- Discovery-based registration (scan directories)
- Support manual registration for plugins
- Allow prompt overrides for customization
- Category-based organization for clarity

### 3. Agent Configuration Loader

**Purpose**: Load agent definitions from YAML files

**Responsibilities**:
- Load agent YAML files (`.agent.yaml`)
- Load persona markdown files (`.md`)
- Validate against agent schema
- Provide unified AgentConfig model

**Interface**:
```python
class AgentConfigLoader:
    """Load agent configurations from YAML files."""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self._validator = SchemaValidator()

    def load_agent(self, agent_name: str) -> AgentConfig:
        """
        Load agent configuration by name.

        Args:
            agent_name: Name of agent (e.g., "amelia")

        Returns:
            AgentConfig with all metadata

        Process:
            1. Load {agent_name}.agent.yaml
            2. Validate against agent schema
            3. Load persona from {persona_file} if specified
            4. Return AgentConfig model

        Raises:
            FileNotFoundError: If agent file not found
            ValidationError: If agent config invalid
        """

    def discover_agents(self) -> List[str]:
        """
        Discover all agent YAML files in directory.

        Returns:
            List of agent names (without .agent.yaml extension)
        """

    def validate_agent(self, config: AgentConfig) -> bool:
        """
        Validate agent config against schema.

        Args:
            config: Agent configuration to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid with details
        """
```

**Key Design Decisions**:
- Keep persona markdown separate (better for long-form content)
- Reference persona file in YAML (`persona_file: ./amelia.md`)
- Validate on load to catch errors early
- Support both embedded and file-based personas

### 4. Schema Validator

**Purpose**: Validate configurations against JSON schemas

**Responsibilities**:
- Load JSON Schema files
- Validate configurations (agents, prompts, workflows)
- Provide clear error messages
- Support schema versioning

**Interface**:
```python
class SchemaValidator:
    """Validate configurations against JSON schemas."""

    def __init__(self, schemas_dir: Path):
        self.schemas_dir = schemas_dir
        self._schemas: Dict[str, Dict] = {}

    def load_schema(self, schema_name: str) -> Dict:
        """
        Load JSON Schema by name.

        Args:
            schema_name: Name of schema (e.g., "agent")

        Returns:
            JSON Schema as dict

        Caches loaded schemas for performance.
        """

    def validate(
        self,
        data: Dict,
        schema_name: str
    ) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            data: Data to validate (parsed YAML/JSON)
            schema_name: Schema to validate against

        Returns:
            ValidationResult with success status and errors

        Example:
            result = validator.validate(agent_data, "agent")
            if not result.is_valid:
                print(result.errors)
        """

    def get_error_message(
        self,
        validation_error: Exception
    ) -> str:
        """
        Convert jsonschema ValidationError to friendly message.

        Args:
            validation_error: Exception from jsonschema

        Returns:
            Human-readable error message
        """
```

**Key Design Decisions**:
- Use jsonschema library (industry standard)
- Clear, actionable error messages
- Cache schemas to avoid repeated file I/O
- Support custom error formatting

---

## Data Models

### PromptTemplate

```python
@dataclass
class PromptTemplate:
    """Represents a prompt template loaded from YAML."""

    name: str
    """Unique prompt identifier (e.g., "brian_analysis")"""

    description: str
    """Human-readable description of prompt's purpose"""

    system_prompt: Optional[str]
    """System-level instructions (optional)"""

    user_prompt: str
    """Main prompt template with {{variables}}"""

    variables: Dict[str, Any]
    """Variable definitions and default values"""

    schema: Optional[Dict]
    """JSON schema for expected response (if structured output)"""

    max_tokens: int = 4000
    """Maximum tokens for response"""

    temperature: float = 0.7
    """Sampling temperature (0.0-1.0)"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (version, author, etc.)"""

    def render(self, variables: Dict[str, Any]) -> str:
        """Render prompt with provided variables."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PromptTemplate":
        """Load from YAML file."""
```

### AgentConfig

```python
@dataclass
class AgentConfig:
    """Represents an agent configuration loaded from YAML."""

    name: str
    """Agent name (e.g., "Amelia")"""

    role: str
    """Agent role (e.g., "Software Developer")"""

    persona: str
    """Agent persona (loaded from .md file or embedded)"""

    tools: List[str]
    """Available tools (e.g., ["Read", "Write", "Bash"])"""

    capabilities: List[str]
    """High-level capabilities (e.g., ["implementation", "code_review"])"""

    model: str
    """Claude model to use (e.g., "claude-sonnet-4-5-20250929")"""

    workflows: List[str]
    """Associated workflows (e.g., ["dev-story", "review-story"])"""

    icon: Optional[str] = None
    """Visual icon/emoji (optional)"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "AgentConfig":
        """Load from YAML file."""
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    """Result of schema validation."""

    is_valid: bool
    """True if validation passed"""

    errors: List[str] = field(default_factory=list)
    """Validation errors (if any)"""

    warnings: List[str] = field(default_factory=list)
    """Non-fatal warnings"""

    def __str__(self) -> str:
        """Format for display."""
        if self.is_valid:
            return "✓ Validation passed"

        lines = ["✗ Validation failed:"]
        for error in self.errors:
            lines.append(f"  - {error}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
```

---

## Integration Points

### 1. AgentFactory Integration

**Before**:
```python
class AgentFactory:
    def _register_builtin_agents(self):
        # Hardcoded dictionary with all agent configs
        builtin_agents = {
            "mary": {...},
            "amelia": {...},
            # ... 200+ lines
        }
```

**After**:
```python
class AgentFactory:
    def __init__(self, agents_dir: Path):
        self.loader = AgentConfigLoader(agents_dir)
        self.registry = AgentRegistry()

    def _register_builtin_agents(self):
        # Discover and load all .agent.yaml files
        for agent_name in self.loader.discover_agents():
            config = self.loader.load_agent(agent_name)
            self.registry.register(config)
```

### 2. BrianOrchestrator Integration

**Before**:
```python
class BrianOrchestrator:
    def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        # 50-line hardcoded prompt
        analysis_prompt = f"""You are Brian Thompson...
        Scale Levels:
        - Level 0: ...
        - Level 1: ...
        ...
        """
        response = self.anthropic.messages.create(...)
```

**After**:
```python
class BrianOrchestrator:
    def __init__(self, project_root: Path):
        self.prompt_loader = PromptLoader(project_root / "gao_dev/prompts")
        self.prompt_registry = PromptRegistry(self.prompt_loader)

    def _analyze_prompt(self, prompt: str) -> PromptAnalysis:
        # Load prompt template
        template = self.prompt_registry.get_prompt("brian_analysis")

        # Render with variables
        rendered = self.prompt_loader.render_prompt(
            template,
            variables={
                "user_request": prompt,
                "brian_persona": self._load_persona(),
            }
        )

        response = self.anthropic.messages.create(...)
```

### 3. StoryOrchestrator Integration

**Before**:
```python
def _create_story_creation_prompt(self, story, result):
    return f"""You are Bob, the Scrum Master...
    {50+ lines of hardcoded prompt}
    """
```

**After**:
```python
def _create_story_creation_prompt(self, story, result):
    template = self.prompt_registry.get_prompt("story_creation")
    return self.prompt_loader.render_prompt(
        template,
        variables={
            "agent_name": "Bob",
            "story_overview": self._format_story_overview(story),
            "acceptance_criteria": self._format_criteria(story),
        }
    )
```

### 4. Plugin System Integration

```python
class LegalTeamPlugin(BaseAgentPlugin):
    def initialize(self):
        # Register custom agent
        laura_config = AgentConfig.from_yaml(
            Path(__file__).parent / "agents/laura.agent.yaml"
        )
        self.agent_factory.register(laura_config)

        # Register custom prompts
        contract_prompt = PromptTemplate.from_yaml(
            Path(__file__).parent / "prompts/contract_review.yaml"
        )
        self.prompt_registry.register_prompt(contract_prompt, category="legal")
```

---

## Technology Stack

### Core Dependencies

**Required**:
- `PyYAML` (>= 6.0) - YAML parsing (already installed)
- `jsonschema` (>= 4.0) - Schema validation (need to add)
- `pydantic` (>= 2.0) - Data models (already installed)

**Optional**:
- `pystache` or `chevron` - Mustache templating (or custom implementation)
- `jinja2` - Alternative templating engine (if more complex needs)

### File Formats
- **Agent configs**: YAML (`.agent.yaml`)
- **Agent personas**: Markdown (`.md`)
- **Prompts**: YAML (`.yaml`)
- **Schemas**: JSON Schema (`.json`)

### Design Patterns
- **Registry Pattern**: PromptRegistry, AgentRegistry
- **Factory Pattern**: AgentFactory (refactored)
- **Template Method**: PromptTemplate rendering
- **Strategy Pattern**: Different prompt rendering strategies
- **Singleton**: Registry instances (per orchestrator)

---

## Directory Structure

### Final Structure

```
gao-agile-dev/
├── gao_dev/
│   ├── agents/                           # Agent configurations
│   │   ├── amelia.agent.yaml             # Agent metadata & config
│   │   ├── amelia.md                     # Agent persona (unchanged)
│   │   ├── bob.agent.yaml
│   │   ├── bob.md
│   │   ├── brian.agent.yaml
│   │   ├── brian.md
│   │   ├── john.agent.yaml
│   │   ├── john.md
│   │   ├── mary.agent.yaml
│   │   ├── mary.md
│   │   ├── murat.agent.yaml
│   │   ├── murat.md
│   │   ├── sally.agent.yaml
│   │   ├── sally.md
│   │   ├── winston.agent.yaml
│   │   └── winston.md
│   │
│   ├── prompts/                          # Prompt templates (NEW)
│   │   ├── agents/                       # Agent-specific prompts
│   │   │   ├── brian_analysis.yaml       # Brian's complexity analysis
│   │   │   └── README.md                 # Prompt documentation
│   │   │
│   │   ├── story_phases/                 # Story workflow prompts
│   │   │   ├── story_creation.yaml       # Bob creates story spec
│   │   │   ├── story_implementation.yaml # Amelia implements story
│   │   │   ├── story_validation.yaml     # Murat validates story
│   │   │   └── README.md
│   │   │
│   │   ├── tasks/                        # Task orchestration prompts
│   │   │   ├── create_prd.yaml
│   │   │   ├── create_architecture.yaml
│   │   │   ├── create_story.yaml
│   │   │   ├── implement_story.yaml
│   │   │   ├── validate_story.yaml
│   │   │   └── README.md
│   │   │
│   │   └── common/                       # Reusable prompt fragments
│   │       ├── responsibilities/         # Role responsibility descriptions
│   │       │   ├── scrum_master.md
│   │       │   ├── developer.md
│   │       │   └── test_architect.md
│   │       ├── outputs/                  # Output format specifications
│   │       │   ├── story_spec_format.md
│   │       │   ├── test_report_format.md
│   │       │   └── commit_message_template.md
│   │       └── guidelines/               # Common guidelines
│   │           ├── coding_standards.md
│   │           ├── testing_standards.md
│   │           └── git_workflow.md
│   │
│   ├── schemas/                          # JSON Schemas (NEW)
│   │   ├── agent.schema.json             # Agent config validation
│   │   ├── prompt.schema.json            # Prompt template validation
│   │   ├── workflow.schema.json          # Workflow config validation
│   │   └── README.md                     # Schema documentation
│   │
│   ├── core/
│   │   ├── prompt_loader.py              # NEW: Load prompts from YAML
│   │   ├── prompt_registry.py            # NEW: Prompt discovery & lookup
│   │   ├── agent_config_loader.py        # NEW: Load agent configs
│   │   ├── schema_validator.py           # NEW: JSON Schema validation
│   │   └── ...                           # Existing core modules
│   │
│   └── config/
│       ├── defaults.yaml                 # Existing config
│       ├── scale_levels.yaml             # NEW: Extracted from code
│       └── commit_templates.yaml         # NEW: Git commit templates
│
└── docs/
    └── features/
        └── prompt-abstraction/
            ├── PRD.md
            ├── ARCHITECTURE.md          # This document
            ├── epics.md
            ├── stories/
            │   └── epic-8/
            │       ├── story-8.1.md
            │       ├── story-8.2.md
            │       └── ... (8 stories)
            └── examples/                # Example configurations
                ├── custom_agent.yaml
                └── custom_prompt.yaml
```

---

## Interface Definitions

### Agent YAML Format

```yaml
# gao_dev/agents/amelia.agent.yaml

agent:
  metadata:
    name: Amelia
    role: Software Developer
    icon: 💻
    version: 1.0.0

  # Reference to persona markdown file
  persona_file: ./amelia.md

  # Or embed persona directly (alternative)
  # persona: |
  #   You are Amelia, a skilled software developer...

  tools:
    - Read
    - Write
    - Edit
    - MultiEdit
    - Bash
    - Grep
    - Glob
    - TodoWrite

  capabilities:
    - implementation
    - code_review
    - testing
    - debugging

  model: claude-sonnet-4-5-20250929

  workflows:
    - dev-story
    - review-story

  # Optional: Custom configuration
  config:
    max_tokens: 8000
    temperature: 0.7
    preferred_languages:
      - Python
      - TypeScript
      - JavaScript
```

### Prompt YAML Format

```yaml
# gao_dev/prompts/agents/brian_analysis.yaml

name: brian_complexity_analysis
description: "Analyze project complexity and recommend scale level"
version: 1.0.0

system_prompt: |
  You are Brian Thompson, a Senior Engineering Manager with 20 years of experience.

  {brian_persona}

user_prompt: |
  Analyze this software development request and assess its scale level using the BMAD scale-adaptive approach:

  User Request:
  {user_request}

  {scale_level_definitions}

  Assess the following:
  {assessment_criteria}

  Return ONLY a JSON object with these exact keys:
  {json_schema}

  Use your seasoned judgment to right-size the project accurately.

variables:
  # Reference to config file
  scale_level_definitions: "@config:scale_levels.yaml"

  # Reference to markdown file
  assessment_criteria: "@file:common/guidelines/assessment_criteria.md"

  # Reference to JSON schema
  json_schema: "@file:../schemas/analysis_response.json"

  # Agent persona loaded separately
  brian_persona: ""  # Populated by loader

# Response configuration
response:
  max_tokens: 2048
  temperature: 0.7
  format: json  # Expect JSON response

# Metadata
metadata:
  author: "GAO-Dev Team"
  category: "agent-prompts"
  tags:
    - complexity-analysis
    - brian
    - workflow-selection
```

### Schema Format

```json
// gao_dev/schemas/agent.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://gao-dev.com/schemas/agent.schema.json",
  "title": "Agent Configuration",
  "description": "Schema for agent configuration YAML files",
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
            "name": {
              "type": "string",
              "description": "Agent name (e.g., 'Amelia')"
            },
            "role": {
              "type": "string",
              "description": "Agent role (e.g., 'Software Developer')"
            },
            "icon": {
              "type": "string",
              "description": "Optional icon/emoji"
            },
            "version": {
              "type": "string",
              "pattern": "^\\d+\\.\\d+\\.\\d+$",
              "description": "Semantic version (e.g., '1.0.0')"
            }
          }
        },
        "persona_file": {
          "type": "string",
          "description": "Path to persona markdown file"
        },
        "persona": {
          "type": "string",
          "description": "Embedded persona content (alternative to persona_file)"
        },
        "tools": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "minItems": 1,
          "description": "List of available tools"
        },
        "capabilities": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "High-level capabilities"
        },
        "model": {
          "type": "string",
          "description": "Claude model identifier"
        },
        "workflows": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Associated workflow names"
        },
        "config": {
          "type": "object",
          "description": "Additional agent-specific configuration"
        }
      },
      "oneOf": [
        {"required": ["persona_file"]},
        {"required": ["persona"]}
      ]
    }
  }
}
```

---

## Migration Strategy

### Phase 1: Foundation (Stories 8.1, 8.5)
**Goal**: Build infrastructure and prove concept

**Tasks**:
1. Implement PromptLoader and PromptRegistry
2. Implement AgentConfigLoader
3. Implement SchemaValidator
4. Create JSON schemas for agents and prompts
5. Write unit tests for all components
6. Migrate 1 agent (Amelia) as proof of concept
7. Migrate 1 prompt (Brian) as proof of concept

**Success Criteria**:
- All infrastructure components tested and working
- Can load agent from YAML
- Can load and render prompt from YAML
- Validation working
- No regressions in existing functionality

### Phase 2: Agent Migration (Part of Story 8.1)
**Goal**: Migrate all agents to YAML format

**Tasks**:
1. Create `.agent.yaml` for all 8 agents
2. Update AgentFactory to use AgentConfigLoader
3. Remove hardcoded agent dictionaries
4. Update all tests
5. Verify all existing functionality works

**Success Criteria**:
- All 8 agents in YAML format
- Zero hardcoded agent configurations
- All tests passing
- Same functionality as before

### Phase 3: Prompt Migration (Stories 8.2, 8.3, 8.4)
**Goal**: Extract all hardcoded prompts

**Tasks**:
1. Extract Brian's analysis prompt (Story 8.2)
2. Extract Story Orchestrator prompts (Story 8.3)
3. Extract Task prompts (Story 8.4)
4. Create reusable prompt fragments
5. Update orchestrators to use PromptLoader
6. Remove hardcoded prompts
7. Update all tests

**Success Criteria**:
- Zero hardcoded prompts in Python
- All prompts in YAML
- Same behavior as before
- All tests passing

### Phase 4: Quality & Extensions (Stories 8.6, 8.7)
**Goal**: Add validation and plugin support

**Tasks**:
1. Add schema validation to all loaders
2. Enhance plugin API for agents and prompts
3. Add comprehensive error handling
4. Performance optimization (caching)
5. Update documentation

**Success Criteria**:
- Schema validation working
- Plugins can register agents/prompts
- Good error messages
- Performance acceptable (<5% overhead)

### Phase 5: Cleanup (Story 8.8)
**Goal**: Remove legacy code and finalize

**Tasks**:
1. Remove all deprecated code paths
2. Remove hardcoded configurations
3. Update all documentation
4. Write migration guide
5. Final testing

**Success Criteria**:
- Clean codebase
- No legacy code
- Complete documentation
- Migration guide available

---

## Performance Considerations

### Caching Strategy

**Prompt Loading**:
- Cache loaded prompts in memory (Dict[str, PromptTemplate])
- Clear cache only when explicitly requested (testing)
- Lazy loading (load on first request)

**Agent Loading**:
- Cache agent configs in memory
- Reload only if file modification time changes (watch for dev mode)

**Schema Loading**:
- Load schemas once at startup
- Cache in memory (schemas don't change at runtime)

### Performance Targets

**Cold Load** (first time):
- Load agent config: <50ms
- Load prompt template: <50ms
- Validate against schema: <30ms
- Total overhead: <150ms per agent/prompt

**Hot Load** (cached):
- Load agent config: <5ms
- Load prompt template: <5ms
- Render prompt: <10ms
- Total overhead: <20ms per operation

**Acceptable Overhead**:
- <5% overhead compared to hardcoded approach
- For 100 agent creations: <5 seconds total overhead

### Optimization Techniques

1. **Lazy Loading**: Load on demand, not at startup
2. **Caching**: In-memory cache for all loaded configs
3. **Pre-compilation**: Compile Mustache templates on load
4. **Parallel Loading**: Load agents/prompts in parallel during discovery
5. **File Watching**: Reload only changed files in dev mode

---

## Security Considerations

### Configuration Security

**File Access**:
- Only load configs from trusted directories
- Validate file paths (no `../` escapes)
- Sandbox file references (can't access arbitrary system files)

**Variable Injection**:
- Sanitize user-provided variables
- Prevent code injection via template variables
- Validate variable types against schema

**Schema Validation**:
- Enforce strict schemas to prevent malicious configs
- Validate all file references before loading
- Limit file sizes (prevent DOS via huge configs)

### Runtime Security

**Prompt Injection Prevention**:
- Escape special characters in user input
- Separate user content from system prompts
- Use structured formats (JSON) for agent responses

**Resource Limits**:
- Limit max prompt length (prevent DOS)
- Limit max template nesting depth
- Timeout on template rendering

---

## Error Handling

### Error Types

**Configuration Errors**:
- File not found (agent or prompt)
- Invalid YAML syntax
- Schema validation failure
- Missing required fields

**Runtime Errors**:
- Variable not provided for template
- File reference not found
- Config reference not found
- Template rendering failure

### Error Messages

**Good Example**:
```
[ERROR] Agent configuration validation failed: amelia.agent.yaml

Missing required field: agent.tools
Line 12: Expected array, got null

Fix:
  agent:
    tools:  # <- Add tools array
      - Read
      - Write

See: docs/agent-schema.md
```

**Bad Example**:
```
ValidationError: 'tools' is a required property
```

### Recovery Strategies

1. **Fail Fast**: Validate all configs at startup (health check)
2. **Graceful Degradation**: Fall back to defaults if optional fields missing
3. **Clear Guidance**: Provide actionable error messages with fix suggestions
4. **Validation Mode**: CLI command to validate configs without running

---

## Testing Strategy

### Unit Tests

**PromptLoader**:
- Load valid prompt YAML
- Handle invalid YAML
- Variable substitution
- File references
- Config references
- Caching

**AgentConfigLoader**:
- Load valid agent YAML
- Load persona from file
- Handle missing persona
- Schema validation
- Discovery

**SchemaValidator**:
- Validate valid configs
- Detect invalid configs
- Error message formatting
- Schema loading

### Integration Tests

**AgentFactory**:
- Load all 8 agents from YAML
- Create agent instances
- Verify tool assignments
- Verify persona loading

**Orchestrators**:
- BrianOrchestrator with prompt loading
- StoryOrchestrator with prompt loading
- Same behavior as before

### Migration Tests

**Equivalence Tests**:
- Old hardcoded approach vs. new YAML approach
- Same prompts rendered
- Same agent configs loaded
- No functionality regressions

### Performance Tests

**Benchmarks**:
- Load 100 agents (cold)
- Load 100 agents (cached)
- Render 1000 prompts
- Compare to hardcoded baseline

**Target**: <5% overhead

---

## Future Enhancements

### Beyond Epic 8

**Prompt Versioning**:
- Multiple prompt versions in parallel
- A/B testing of prompt variations
- Gradual rollout of new prompts

**Dynamic Prompts**:
- Prompts that adapt based on context
- Conditional prompt sections
- Prompt composition from fragments

**Prompt Analytics**:
- Track which prompts perform best
- Measure token usage per prompt
- Optimize prompts based on data

**Multi-Language Support**:
- Prompts in different languages
- Agent personas in different languages
- Automatic translation

**Visual Prompt Editor**:
- GUI for editing prompts
- Live preview of rendered prompts
- Variable autocomplete

---

## Appendix

### Glossary

- **Prompt Template**: YAML file with system/user prompts and variables
- **Agent Configuration**: YAML file defining agent metadata, tools, capabilities
- **Schema Validation**: Checking configuration against JSON Schema
- **Variable Substitution**: Replacing `{{variable}}` in templates
- **Reference Resolution**: Loading `@file:` and `@config:` references

### References

- **BMAD Agent Format**: `bmad/bmm/agents/*.agent.yaml`
- **JSON Schema Spec**: https://json-schema.org/
- **Mustache Templating**: https://mustache.github.io/
- **PyYAML Docs**: https://pyyaml.org/wiki/PyYAMLDocumentation

### Version History

- **1.0.0** (2025-11-03): Initial architecture document
