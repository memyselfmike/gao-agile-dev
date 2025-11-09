# GAO-Dev Project Guide - For Claude

This document helps you (Claude) quickly understand the GAO-Dev project, its structure, current status, and best practices.

---

## What is GAO-Dev?

**GAO-Dev** (Generative Autonomous Organisation - Development Team) is an autonomous AI development orchestration system that manages the complete software development lifecycle using specialized Claude agents.

**Goal**: Transform "simple prompt → production-ready app" into reality through intelligent workflow selection, scale-adaptive routing, and autonomous agent orchestration.

**Parent Project**: GAO (Generative Autonomous Organisation)
**This Project**: Development team within GAO
**Future**: gao-ops (Operations), gao-research (Research), etc.

---

## Core Principles

1. **Workflow-Driven Development**: All work follows defined workflows with intelligent selection
2. **Agent Specialization**: 7 specialized agents (Brian, John, Winston, Sally, Bob, Amelia, Murat)
3. **Scale-Adaptive**: Automatically adjusts approach based on project size (Levels 0-4)
4. **Autonomous Execution**: Agents work autonomously to build complete applications
5. **Quality Focus**: Comprehensive testing, type safety, clean architecture
6. **Observability**: Full visibility into agent activities, metrics, and benchmarking
7. **Git-Integrated Hybrid Architecture**: Files + database with atomic git transactions (NEW!)

---

## Current Status (As of 2025-11-09)

### Latest Achievements

✅ **EPIC 27: Git-Integrated Hybrid Wisdom - Integration & Migration** - COMPLETE
  - Complete orchestrator integration with all services
  - CLI commands updated (migrate, consistency-check, consistency-repair)
  - Migration tools for existing projects
  - 15 E2E workflow tests covering complete user journeys
  - 10 performance benchmarks validating system-level targets
  - Comprehensive documentation (Migration Guide, API Reference, Troubleshooting)
  - **THIS COMPLETES THE GIT-INTEGRATED-HYBRID-WISDOM FEATURE (100%)!**

✅ **Epics 22-26: Git-Integrated Hybrid Architecture** - COMPLETE
  - GitIntegratedStateManager for atomic file+DB operations
  - FastContextLoader with caching for <5ms load times
  - CeremonyOrchestrator for multi-agent coordination
  - ConversationManager for natural dialogue flow
  - GitMigrationManager for safe migration with rollback
  - GitAwareConsistencyChecker for file-DB sync validation
  - All services integrated and tested

✅ **Epic 18: Workflow Variable Resolution and Artifact Tracking** - COMPLETE
  - Workflow variables properly resolved before sending to LLM
  - Files created at correct locations (e.g., docs/PRD.md not root)
  - Automatic artifact detection and registration
  - Document lifecycle integration with metadata
  - WorkflowExecutor integration into orchestrator
  - Comprehensive logging for observability
  - Migration guide and documentation

✅ **Epic 20: Project-Scoped Document Lifecycle** - COMPLETE
  - Project-scoped `.gao-dev/` directories for isolated tracking
  - ProjectDocumentLifecycle factory for multi-project support
  - Auto-detection of project roots in CLI commands
  - Orchestrator and SandboxManager integration
  - Migration guide for existing projects
  - Full backward compatibility

✅ **Epic 10: Prompt & Agent Configuration Abstraction** - COMPLETE
  - All prompts externalized to YAML templates
  - Agent configurations in structured YAML files
  - PromptLoader with reference resolution (@file:, @config:)
  - Enhanced plugin system for custom agents and prompts
  - 5 task prompt templates created
  - Example legal team plugin demonstrating extensibility
  - Migration guide for upgrading

✅ **Epic 7.2: Workflow-Driven Core Architecture** - COMPLETE
  - Brian agent for intelligent workflow selection
  - Scale-adaptive routing (Levels 0-4)
  - Multi-workflow sequencing
  - 41 integration tests passing
  - 55+ workflows loaded

✅ **Epic 6: Legacy Cleanup & God Class Refactoring** - COMPLETE
  - Clean architecture with service layer
  - Facade pattern for managers
  - Model-driven design
  - All services <200 LOC

✅ **Sandbox & Benchmarking System** - COMPLETE (Epics 1-5)
  - Full sandbox infrastructure
  - Boilerplate integration
  - Comprehensive metrics collection (performance, autonomy, quality)
  - Benchmark runner with orchestration
  - HTML reporting with charts and trends

### System Capabilities

**The system NOW can**:
- Accept a simple prompt
- Intelligently select appropriate workflows based on scale and context
- Execute multi-workflow sequences
- Resolve workflow variables before sending instructions to LLM
- Create real project artifacts at correct locations with atomic git commits
- Automatically detect and register all workflow artifacts
- Track document lifecycle per-project with isolated `.gao-dev/` directories
- Auto-detect project context for CLI commands
- Track comprehensive metrics with structured logging
- Generate detailed HTML reports
- Validate results against success criteria
- Load prompts and agent configs from YAML files
- Support custom agents and prompts via plugins
- Resolve references to files and configuration values

### What's Next

1. **Real-world testing** - Run workflow-driven benchmarks to build complete applications
2. **Domain-specific teams** - Create gao-ops, gao-legal, gao-research using new abstraction
3. **Prompt optimization** - A/B test prompt variations using YAML templates
4. **Epic 9: Continuous Improvement** - Optimize based on benchmark learnings
5. **Production deployment** - Core architecture is complete and tested

---

## The 7 Specialized Agents

### 1. Brian - Workflow Coordinator (NEW!)
**Role**: Intelligent workflow selection and orchestration
**Capability**: Scale-adaptive routing, clarification dialogs, multi-workflow sequencing
**Use For**: Initial project analysis, workflow selection, coordinating complex sequences

### 2. John - Product Manager
**Role**: PRDs, feature definition, prioritization
**Tools**: Read, Write, Grep, Glob, workflows, sprint status, research
**Use For**: Creating PRDs, defining epics, prioritizing work

### 3. Winston - Technical Architect
**Role**: System architecture, technical specifications
**Tools**: Read, Write, Edit, Grep, Glob, workflows, research
**Use For**: Architecture design, technical decisions

### 4. Sally - UX Designer
**Role**: User experience, wireframes, design
**Tools**: Read, Write, Grep, Glob, workflows, story status, research
**Use For**: UX design, user flows, interface design

### 5. Bob - Scrum Master
**Role**: Story creation and management, team coordination
**Tools**: Read, Write, Grep, Glob, workflows, story management, git, TodoWrite
**Use For**: Creating stories, managing sprint, status tracking

### 6. Amelia - Software Developer
**Role**: Implementation, code reviews, testing
**Tools**: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, workflows, story management, git, TodoWrite, research
**Use For**: Implementing features, writing code, code reviews

### 7. Murat - Test Architect
**Role**: Test strategies, quality assurance
**Tools**: Read, Write, Edit, Grep, Glob, Bash, workflows, story status, git, TodoWrite
**Use For**: Test strategies, test plans, quality standards

---

## Project Structure

```
gao-agile-dev/
├── .claude/
│   └── settings.local.json       # Claude settings
│
├── gao_dev/                       # Source code (MAIN FOCUS)
│   ├── agents/                    # Agent implementations
│   │   ├── base.py, claude_agent.py, exceptions.py
│   │   ├── mary.md, john.md, winston.md, sally.md
│   │   ├── bob.md, amelia.md, murat.md, brian.md
│   │
│   ├── cli/                       # CLI commands
│   │   ├── commands.py            # Main commands
│   │   ├── sandbox_commands.py    # Sandbox commands
│   │   └── report_commands.py     # Reporting commands
│   │
│   ├── core/                      # Core services & infrastructure
│   │   ├── config_loader.py
│   │   ├── workflow_registry.py, workflow_executor.py
│   │   ├── state_manager.py, git_manager.py
│   │   ├── health_check.py, hook_manager.py
│   │   ├── events/                # Event bus
│   │   ├── factories/             # Agent factory
│   │   ├── interfaces/            # Core interfaces
│   │   ├── models/                # Domain models
│   │   ├── repositories/          # File repository
│   │   ├── services/              # Business services
│   │   │   ├── quality_gate.py
│   │   │   └── story_lifecycle.py
│   │   └── strategies/            # Workflow strategies
│   │
│   ├── orchestrator/              # Agent orchestration
│   │   ├── orchestrator.py        # GAODevOrchestrator (main)
│   │   ├── agent_definitions.py   # Agent configs
│   │   └── workflow_results.py    # Result handling
│   │
│   ├── methodologies/             # Methodology abstraction
│   │   ├── adaptive_agile/        # Adaptive methodology
│   │   │   ├── methodology.py
│   │   │   ├── scale_levels.py    # Levels 0-4
│   │   │   ├── workflow_selector.py
│   │   │   └── agent_recommender.py
│   │   ├── simple/                # Simple methodology
│   │   │   └── simple_methodology.py
│   │   └── registry.py            # Methodology registry
│   │
│   ├── plugins/                   # Plugin system
│   │   ├── base_plugin.py, loader.py, discovery.py
│   │   ├── agent_plugin.py, agent_plugin_manager.py
│   │   ├── workflow_plugin.py, workflow_plugin_manager.py
│   │   ├── permission_manager.py, resource_monitor.py
│   │   └── sandbox.py
│   │
│   ├── sandbox/                   # Sandbox & Benchmarking (MAJOR SYSTEM)
│   │   ├── manager.py             # SandboxManager
│   │   ├── git_cloner.py, git_commit_manager.py
│   │   ├── boilerplate_validator.py, dependency_installer.py
│   │   ├── artifact_parser.py, artifact_verifier.py
│   │   ├── benchmark_loader.py
│   │   │
│   │   ├── benchmark/             # Benchmark system
│   │   │   ├── config.py, validator.py, models.py
│   │   │   ├── orchestrator.py    # Main benchmark orchestrator
│   │   │   ├── story_orchestrator.py
│   │   │   ├── interactive_runner.py, checker.py
│   │   │   ├── progress.py, timeout.py
│   │   │   └── metrics_aggregator.py
│   │   │
│   │   ├── metrics/               # Metrics collection
│   │   │   ├── models.py, database.py
│   │   │   ├── collector.py, export.py
│   │   │   ├── performance_tracker.py
│   │   │   ├── autonomy_tracker.py
│   │   │   └── quality_tracker.py
│   │   │
│   │   └── reporting/             # HTML reporting
│   │       ├── templates/         # Jinja2 templates
│   │       └── assets/            # CSS, JS
│   │
│   ├── workflows/                 # Embedded workflows (55+)
│   │   ├── 1-analysis/
│   │   ├── 2-plan/
│   │   ├── 3-solutioning/
│   │   └── 4-implementation/
│   │
│   ├── checklists/                # Quality checklists
│   │
│   └── config/                    # Configuration (ENHANCED in Epic 10)
│       ├── agents/                # Agent YAML configurations
│       │   ├── amelia.yaml, bob.yaml, john.yaml
│       │   ├── winston.yaml, sally.yaml, murat.yaml
│       │   ├── brian.yaml, mary.yaml
│       │
│       ├── prompts/               # Prompt templates
│       │   ├── brian/             # Brian's prompts
│       │   ├── story_orchestrator/ # Story phase prompts
│       │   └── tasks/             # Task prompts
│       │
│       ├── schemas/               # JSON Schema validation
│       │   ├── agent_schema.json
│       │   └── prompt_schema.json
│       │
│       └── defaults.yaml          # Default settings
│
├── sandbox/                       # Sandbox WORKSPACE
│   ├── benchmarks/                # Benchmark configs
│   │   └── workflow-driven-todo.yaml
│   └── projects/                  # Test projects (created by agents)
│
├── docs/                          # Documentation
│   ├── README.md
│   ├── bmm-workflow-status.md     # Current epic/story status
│   ├── sprint-status.yaml         # Sprint tracking
│   ├── SETUP.md                   # API key setup
│   ├── BENCHMARK_STANDARDS.md
│   ├── plugin-development-guide.md
│   └── features/                  # Feature development docs
│       ├── sandbox-system/        # Sandbox feature (Epics 1-7.2)
│       ├── prompt-abstraction/    # Prompt abstraction (Epic 10)
│       └── core-gao-dev-system-refactor/  # Refactoring (Epic 6)
│
├── bmad/                          # BMAD Method reference
│   └── (reference implementations)
│
├── tests/                         # Test suite
├── pyproject.toml                 # Package configuration
├── README.md                      # Main project README
└── CLAUDE.md                      # This file
```

### Project-Scoped Architecture

Each project managed by GAO-Dev has its own `.gao-dev/` directory for isolated document lifecycle tracking:

```
sandbox/projects/my-app/          # Project root
├── .gao-dev/                     # Project-specific GAO-Dev data
│   ├── documents.db              # Document lifecycle tracking
│   ├── context.json              # Execution context
│   └── metrics/                  # Project metrics
├── .archive/                     # Archived documents
├── docs/                         # Live documentation
├── src/                          # Application code
└── tests/                        # Test suite
```

**Key Points**:
- Each project is isolated with its own document tracking
- Documentation context persists across sessions
- `.gao-dev/` can be moved with the project
- Same structure for all project types (sandbox, benchmarks, production)
- Automatic initialization on project creation

---

## Scale-Adaptive Routing

GAO-Dev intelligently adapts its approach based on project scale (via Brian agent):

**Level 0: Chore** (Quick task, <1 hour)
- Direct execution, no formal planning
- Examples: Fix typo, update docs, small config change

**Level 1: Bug Fix** (Single file, 1-4 hours)
- Minimal planning, direct fix
- Examples: Fix failing test, resolve small bug

**Level 2: Small Feature** (3-8 stories, 1-2 weeks)
- PRD → Architecture → Epic → Stories → Implementation
- Examples: Add authentication, new UI component

**Level 3: Medium Feature** (12-40 stories, 1-2 months)
- Full BMAD workflow with analysis phase
- Examples: Complete module, integration system

**Level 4: Greenfield Application** (40+ stories, 2-6 months)
- Comprehensive methodology with discovery
- Examples: New product, complete rewrite

---

## Git-Integrated Hybrid Architecture (NEW!)

GAO-Dev now uses a **hybrid file + database architecture** with **git transaction safety** for managing all project state. This provides the best of both worlds: human-readable files for collaboration + structured database for fast queries, all wrapped in atomic git commits.

### Architecture Overview

```
                    ┌─────────────────────────────────┐
                    │   GAODevOrchestrator            │
                    │  (Main Entry Point)             │
                    └──────────┬──────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
    ┌───────────▼──────────┐   │   ┌─────────▼────────────┐
    │ GitIntegrated        │   │   │ FastContextLoader    │
    │ StateManager         │   │   │ (5ms context loads)  │
    │ (Atomic File+DB+Git) │   │   │ + Caching           │
    └──────────┬───────────┘   │   └─────────┬────────────┘
               │               │             │
    ┌──────────▼───────────┐   │   ┌─────────▼────────────┐
    │ StateCoordinator     │   │   │ CeremonyOrchestrator │
    │ (SQLite DB)          │   │   │ (Multi-agent coord)  │
    └──────────────────────┘   │   └──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ConversationManager │
                    │ (Natural dialogue)  │
                    └─────────────────────┘
```

### Core Services

**1. GitIntegratedStateManager** - Central state management service
- Atomic operations: File write + DB insert + Git commit (all or nothing)
- Auto-rollback on any step failure
- Epic and story lifecycle management
- State transition validation with FSM

**2. FastContextLoader** - High-performance context loading
- <5ms context load times (LRU cache with TTL)
- Loads epic, story, dependencies, architecture
- Cache hit rates >80% in production
- Async streaming for large contexts

**3. CeremonyOrchestrator** - Multi-agent coordination
- Executes ceremonies (planning, daily standup, retrospective)
- Loads shared context for all agents
- Tracks ceremony outcomes and decisions
- Git commits after each ceremony

**4. ConversationManager** - Natural dialogue flow
- Maintains conversation history
- Context-aware responses
- Supports clarification loops
- Integrates with FastContextLoader

**5. GitMigrationManager** - Safe migration with rollback
- 4-phase migration: tables → epics → stories → validate
- Git checkpoint after each phase
- Automatic rollback on failure
- Migration branch isolation

**6. GitAwareConsistencyChecker** - File-DB sync validation
- Detects orphaned DB records
- Finds unregistered files
- Identifies state mismatches
- Repairs issues automatically

### Key Features

**Atomic Transactions**:
```python
# All or nothing - if any step fails, everything rolls back
manager.create_epic(
    epic_num=1,
    title="Feature X",
    file_path=Path("docs/epics/epic-1.md"),
    content="# Epic 1: Feature X"
)
# Result: File written + DB record + Git commit (atomic)
```

**Fast Context Loading**:
```python
# <5ms with caching
context = await loader.load_story_context(epic_num=1, story_num=1)
# Includes: epic, story, dependencies, architecture, previous context
```

**Safe Migration**:
```python
# Migrate existing project with rollback safety
result = migration_mgr.migrate_to_hybrid_architecture()
if result.success:
    print(f"Migrated {result.epics_count} epics, {result.stories_count} stories")
else:
    print(f"Migration failed, automatic rollback performed")
```

**Consistency Checking**:
```python
# Detect and repair issues
report = checker.check_consistency()
if report.has_issues:
    checker.repair(report)  # Files are source of truth
```

### Performance Characteristics

- **Epic creation**: <1 second (file + DB + git commit)
- **Story creation**: <200ms (file + DB + git commit)
- **Context loading**: <5ms (with cache), <50ms (cold)
- **Orchestrator init**: <500ms (all services initialized)
- **Migration**: ~100ms per file (includes git operations)
- **Consistency check**: <5 seconds for 1000 files
- **Memory growth**: <100MB for 1000 operations
- **DB size growth**: <1KB per operation

### Using the Architecture

**Initialize Orchestrator**:
```python
from gao_dev.orchestrator import GAODevOrchestrator

# Uses GitIntegratedStateManager automatically
orchestrator = GAODevOrchestrator.create_default(project_root)

# All services available
orchestrator.git_state_manager      # GitIntegratedStateManager
orchestrator.fast_context_loader    # FastContextLoader
orchestrator.ceremony_orchestrator  # CeremonyOrchestrator
orchestrator.conversation_manager   # ConversationManager
```

**CLI Commands**:
```bash
# Migration commands
gao-dev migrate                    # Migrate to hybrid architecture
gao-dev migrate --dry-run          # Preview migration
gao-dev consistency-check          # Check file-DB consistency
gao-dev consistency-repair         # Repair inconsistencies

# State commands (use hybrid architecture)
gao-dev state list-epics           # Query database
gao-dev state show-story 1 1       # Fast DB lookup
gao-dev state transition 1 1 ready # Atomic state transition
```

### Migration Guide

For existing projects, see: [Migration Guide](docs/features/git-integrated-hybrid-wisdom/MIGRATION_GUIDE.md)

Key steps:
1. Run `gao-dev migrate` to migrate existing files to database
2. Verify with `gao-dev consistency-check`
3. Continue normal development (automatic hybrid mode)

### Troubleshooting

For common issues, see: [Troubleshooting Guide](docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md)

Common issues:
- **Working tree dirty**: Commit or stash changes before operations
- **Orphaned records**: Run `gao-dev consistency-repair`
- **Slow context loads**: Cache warming or increase cache size
- **Migration failures**: Automatic rollback, check logs for details

### API Reference

For complete API documentation, see: [API Reference](docs/features/git-integrated-hybrid-wisdom/API.md)

---

## Prompt & Configuration System (Epic 10)

GAO-Dev uses a YAML-based abstraction system for all prompts and agent configurations:

### Prompt Templates

All prompts are externalized to YAML files with variable substitution:

**Location**: `gao_dev/config/prompts/`
- `tasks/` - Task prompts (create_prd, implement_story, etc.)
- `brian/` - Brian's prompts (complexity analysis)
- `story_orchestrator/` - Story lifecycle prompts
- (More can be added via plugins)

**Example Prompt Template**:
```yaml
name: create_prd
description: "Task prompt for PRD creation by John"
version: 1.0.0

user_prompt: |
  Use the John agent to create a Product Requirements Document for '{{project_name}}'.

  John should:
  1. Use the 'prd' workflow to understand the structure
  2. Create a comprehensive PRD.md file
  ...

variables:
  project_name: ""
  agent: "John"

response:
  max_tokens: 8000
  temperature: 0.7
```

**Loading and Rendering Prompts**:
```python
from gao_dev.core.prompt_loader import PromptLoader

loader = PromptLoader(prompts_dir=Path("gao_dev/config/prompts"))
template = loader.load_prompt("tasks/create_prd")
rendered = loader.render_prompt(template, {"project_name": "MyApp"})
```

### Reference Resolution

The PromptLoader supports dynamic references:

**File References** - Load content from files:
```yaml
variables:
  responsibilities: "@file:common/responsibilities/developer.md"
```

**Config References** - Load from configuration:
```yaml
variables:
  model: "@config:claude_model"
```

### Agent Configurations

All agent definitions are in YAML format:

**Location**: `gao_dev/config/agents/*.yaml`

All 8 agents now configured in YAML:
- `amelia.yaml`, `bob.yaml`, `john.yaml`
- `winston.yaml`, `sally.yaml`, `murat.yaml`
- `brian.yaml`, `mary.yaml`

**Example Agent Config**:
```yaml
agent:
  metadata:
    name: Mary
    role: Engineering Manager
    version: 1.0.0

  persona:
    background: |
      You are Mary, an Engineering Manager...

    responsibilities:
      - Coordinate development teams
      - Review technical decisions

  tools:
    - Read
    - Write
    - Grep

  configuration:
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 4000
    temperature: 0.7
```

### Plugin System Extensions

Plugins can provide custom agents and prompts:

```python
from gao_dev.plugins.agent_plugin import BaseAgentPlugin

class MyPlugin(BaseAgentPlugin):
    def get_agent_definitions(self) -> List[AgentConfig]:
        """Return custom agent definitions from YAML."""
        return [AgentConfig.from_yaml(Path("agents/custom.agent.yaml"))]

    def get_prompt_templates(self) -> List[PromptTemplate]:
        """Return custom prompt templates from YAML."""
        return [PromptTemplate.from_yaml(Path("prompts/custom.yaml"))]
```

**Benefits**:
- No code changes needed to update prompts
- Easy customization and versioning
- Plugin ecosystem for domain-specific extensions
- Separation of concerns (logic vs. content)

**See Also**:
- [Migration Guide - Epic 10 (Prompt Abstraction)](docs/MIGRATION_GUIDE_EPIC_10.md)
- [Migration Guide - Epic 20 (Project-Scoped Lifecycle)](docs/MIGRATION_GUIDE_EPIC_20.md)
- [Plugin Example](docs/examples/legal-team-plugin/)

---

## Available Commands

### Core Commands
```bash
gao-dev --version                    # Show version
gao-dev --help                       # Show help
gao-dev init --name "Project"        # Initialize project
gao-dev health                       # Run health check
gao-dev list-workflows               # List all workflows
gao-dev list-agents                  # List all agents
```

### Autonomous Commands
```bash
gao-dev create-prd --name "Project"            # John creates PRD
gao-dev create-architecture --name "Project"   # Winston creates architecture
gao-dev create-story --epic 1 --story 1        # Bob creates story
gao-dev implement-story --epic 1 --story 1     # Bob + Amelia implement
```

### Sandbox Commands
```bash
gao-dev sandbox init <project-name>            # Create sandbox project
gao-dev sandbox list                           # List all projects
gao-dev sandbox clean <project-name>           # Clean/reset project
gao-dev sandbox delete <project-name>          # Delete project
gao-dev sandbox status                         # System status
gao-dev sandbox run <benchmark.yaml>           # Run benchmark
```

### Metrics & Reporting
```bash
gao-dev metrics export <run-id> --format csv   # Export metrics
gao-dev metrics report run <run-id>            # Generate HTML report
gao-dev metrics report compare <id1> <id2>     # Compare two runs
gao-dev metrics report trend <config>          # Trend analysis
gao-dev metrics report list                    # List all reports
gao-dev metrics report open <report-id>        # Open report in browser
```

### Document Lifecycle Commands
```bash
gao-dev lifecycle list                         # List documents (auto-detects project)
gao-dev lifecycle list --project <path>        # List for specific project
gao-dev lifecycle register <path> <type>       # Register document
gao-dev lifecycle update <path>                # Update document
gao-dev lifecycle archive <path>               # Archive document
gao-dev lifecycle restore <path>               # Restore document
```

**Note**: Commands auto-detect project root by searching for `.gao-dev/` or `.sandbox.yaml`.
You can override with `--project` option to target a specific project.

---

## Methodologies

GAO-Dev supports multiple methodologies through abstraction:

### Adaptive Agile (Default)
- Scale-adaptive routing (Levels 0-4)
- Intelligent workflow selection
- Agent recommendations based on context
- Located in: `gao_dev/methodologies/adaptive_agile/`

### Simple Methodology
- Lightweight, minimal process
- For quick prototypes and experiments
- Located in: `gao_dev/methodologies/simple/`

### Future: Custom Methodologies
- Plugin system supports custom methodologies
- Implement `IMethodology` interface
- Register via plugin system

---

## Workflow-Driven Architecture

### How It Works

1. **User provides prompt** → "Build a todo application with user auth"
2. **Brian agent analyzes** → Determines scale level, project type, requirements
3. **Workflow selection** → Chooses appropriate workflow sequence
4. **Variable resolution** → WorkflowExecutor resolves variables from workflow.yaml, config, and params
5. **Template rendering** → Instructions rendered with resolved variables ({{prd_location}} → docs/PRD.md)
6. **Orchestration** → Coordinates agent execution with resolved instructions (John → Winston → Bob → Amelia)
7. **Artifact creation** → Real files created at correct locations with atomic git commits
8. **Artifact detection** → Filesystem snapshots detect all created/modified files
9. **Document registration** → All artifacts registered with DocumentLifecycleManager
10. **Metrics tracking** → Performance, autonomy, quality metrics collected
11. **Validation** → Results checked against success criteria

### Variable Resolution Flow

All workflow variables are now properly resolved before execution:

```
[workflow.yaml: variables + defaults]
         ↓
[WorkflowExecutor.resolve_variables()]  ← Resolve from workflow.yaml, params, config
         ↓
[WorkflowExecutor.render_template()]  ← Render {{variable}} → actual values
         ↓
[Orchestrator sends RESOLVED instructions to LLM]  ← All variables replaced
         ↓
[LLM creates files at correct locations]
         ↓
[Post-execution artifact detector]  ← Detect created/modified files
         ↓
[DocumentLifecycleManager.register_document()]  ← Track all artifacts
```

**Variable Priority Order** (highest to lowest):
1. Runtime parameters (passed at execution)
2. Workflow YAML defaults (defined in workflow.yaml)
3. Config defaults (from config/defaults.yaml)
4. Common variables (auto-generated: date, timestamp, project_name, etc.)

### Available Workflows (55+)

**Phase 1: Analysis**
- Product brief, research, brainstorming

**Phase 2: Planning**
- PRD, Game Design Doc, Tech Specs, Epics

**Phase 3: Solutioning**
- System architecture, API design, data models

**Phase 4: Implementation**
- Story creation, story development, code review, testing

### Workflow Variable Conventions

All workflows support variable resolution using Mustache-style syntax (`{{variable}}`):

**Common Variables** (automatically available):
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{timestamp}}` - Current timestamp (ISO 8601)
- `{{project_name}}` - Project directory name
- `{{project_root}}` - Absolute path to project root
- `{{epic}}` / `{{epic_num}}` - Epic number
- `{{story}}` / `{{story_num}}` - Story number
- `{{agent}}` - Current agent name
- `{{workflow}}` - Workflow name

**Defining Variables** in workflow.yaml:
```yaml
variables:
  prd_location:
    description: "Location for PRD file"
    default: "docs/PRD.md"
    required: false
```

**Variable Naming Conventions**:
- Location variables: `{type}_location` (e.g., `prd_location`, `story_location`)
- Folder variables: `{type}_folder` (e.g., `output_folder`, `test_folder`)
- Path variables: `{type}_path` (e.g., `template_path`, `config_path`)
- Always use `snake_case`

**See Also**: [Variable Resolution Guide](docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md)

---

## Git Workflow

### Branch Strategy

**Branch Naming**:
- `main` - Production-ready code (protected)
- `feature/epic-<N>-<epic-name>` - Epic-level feature branches
- `feature/story-<N>.<M>-<story-name>` - Story-level branches

**Workflow Process**:
```bash
# 1. Start new feature
git checkout main
git pull origin main
git checkout -b feature/epic-N-name

# 2. Work on story, commit atomically
git add -A
git commit -m "feat(scope): implement Story N.M - Story Name"

# 3. After epic complete
git checkout main
git pull origin main
git merge feature/epic-N-name --no-ff
git push origin main
```

### Atomic Commits - REQUIRED

**One Commit Per Story**:
- ✅ Each story gets exactly ONE commit
- ✅ Commit immediately after story completion
- ✅ Never batch multiple stories into one commit
- ✅ Never leave uncommitted work

**Commit Message Format**:
```
<type>(<scope>): <description>

<optional body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

---

## Quality Standards

### Code Quality
- ✅ **DRY Principle**: No code duplication
- ✅ **SOLID Principles**: Single responsibility, Open/closed, etc.
- ✅ **Clean Architecture**: Clear separation of concerns
- ✅ **Type Safety**: Type hints throughout, no `Any` types
- ✅ **Error Handling**: Comprehensive try/catch, clear messages
- ✅ **Logging**: structlog for observability

### Testing
- ✅ **Unit Tests**: 80%+ coverage
- ✅ **Integration Tests**: Key workflows tested
- ✅ **Type Checking**: MyPy passes strict mode
- ✅ **Current**: 400+ tests passing across all modules

### Code Style
- ✅ **ASCII Only**: No emojis or Unicode (Windows compatibility)
- ✅ **Formatting**: Black, line length 100
- ✅ **Linting**: Ruff for code quality

---

## Sandbox & Benchmarking System

### Purpose

The sandbox system enables:
1. **Testing autonomous capabilities** - Validate GAO-Dev can build complete apps
2. **Measuring performance** - Track improvements over time
3. **Quality assurance** - Ensure code quality, test coverage, architecture

### Components

**Sandbox Manager**:
- Creates isolated project environments
- Manages project lifecycle (init, clean, delete, list)
- Tracks project metadata and state

**Benchmark Runner**:
- YAML/JSON configuration
- Multi-phase workflow orchestration
- Success criteria validation
- Real-time progress tracking
- Timeout management

**Metrics Collection**:
- Performance: Duration, token usage, cost
- Autonomy: User interventions, error recovery
- Quality: Test coverage, type safety, code quality
- Workflow: Story completion rate, rework percentage

**Reporting System**:
- HTML dashboards with charts
- Run comparison reports
- Trend analysis with statistics
- Professional templates (Jinja2)

### Example Benchmark

```yaml
# sandbox/benchmarks/workflow-driven-todo.yaml
name: "Workflow-Driven Todo App"
description: "Build complete todo app autonomously"

initial_prompt: |
  Build a todo application with:
  - User authentication
  - CRUD operations for tasks
  - Task filtering and search
  - API + Frontend
  - Tests with >80% coverage

success_criteria:
  - Application runs successfully
  - All tests pass
  - Test coverage >80%
  - Clean git history
  - Documentation complete

scale_level: 2  # Small feature
```

---

## Execution Best Practices

### 1. Use TodoWrite for Progress Tracking
```python
TodoWrite([
    {"content": "Task 1", "status": "in_progress", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "pending", "activeForm": "Doing task 2"},
])
```

**Rules**:
- Exactly ONE task in_progress at a time
- Mark completed immediately after finishing
- Clear todo list when done

### 2. Provide Full Visibility
- Tell user what you're about to do
- Explain results as you get them
- Show progress for long operations
- Allow user to interrupt or redirect

### 3. Parallel Tool Calls When Appropriate
- If multiple independent reads needed, call in parallel
- User sees all calls at once (more efficient)

### 4. Read Before Write/Edit
- Always use Read tool before Edit or Write
- Understand existing code before modifying
- Preserve indentation and style

---

## Common Workflows

### Starting a New Project
1. Check `docs/bmm-workflow-status.md` for current status
2. Read relevant PRD and architecture docs
3. Create feature branch
4. Plan work with TodoWrite
5. Implement with atomic commits

### Implementing a Story
1. Read story file (e.g., `docs/features/sandbox-system/stories/epic-N/story-N.M.md`)
2. Check acceptance criteria
3. Write tests first (TDD)
4. Implement functionality
5. Run tests and validate
6. Commit atomically
7. Update story status

### Running Benchmarks
1. Set ANTHROPIC_API_KEY environment variable
2. Create or use existing benchmark config
3. Run: `gao-dev sandbox run sandbox/benchmarks/<config>.yaml`
4. Monitor progress in real-time
5. Review generated report
6. Inspect artifacts in `sandbox/projects/<project-name>/`

---

## Key Files to Read When Starting

### Priority 1: Current Status
1. **`docs/bmm-workflow-status.md`** - Current epic, story, what's done, what's next
2. **`docs/sprint-status.yaml`** - All stories and their status
3. **Latest git commits** - `git log --oneline -10`

### Priority 2: Feature Context
1. **Feature PRD** - `docs/features/<feature-name>/PRD.md`
2. **Feature Architecture** - `docs/features/<feature-name>/ARCHITECTURE.md`
3. **Current story** - Detailed requirements and acceptance criteria

### Priority 3: Codebase Understanding
1. **`README.md`** - Project overview
2. **`pyproject.toml`** - Dependencies and configuration
3. **Relevant source** - Existing implementations for patterns

---

## Plugin System

GAO-Dev supports extensibility through plugins:

### Plugin Types

**Agent Plugins**:
- Add new agents with custom capabilities
- Extend existing agents

**Workflow Plugins**:
- Add custom workflows
- Modify workflow behavior

**Methodology Plugins**:
- Add custom methodologies
- Customize development process

### Creating Plugins

See `docs/plugin-development-guide.md` for complete guide.

Basic structure:
```python
from gao_dev.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def initialize(self, config):
        # Plugin setup
        pass

    def on_workflow_start(self, workflow_name):
        # Hook into workflow lifecycle
        pass
```

---

## Troubleshooting

### Common Issues

**Import Errors**:
- Ensure package installed: `pip install -e .`
- Check Python version: `python --version` (requires 3.11+)

**CLI Not Found**:
- Reinstall: `pip install -e .`
- Check PATH includes Python scripts directory

**Variable Not Resolved**:
- Symptom: `{{variable}}` appears in LLM instructions, files created at wrong location
- Solution: Add variable to workflow.yaml or config/defaults.yaml
- Check logs: `gao-dev <command> 2>&1 | jq 'select(.event == "workflow_variables_resolved")'`
- See: [Variable Resolution Guide](docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md#troubleshooting-guide)

**File Created at Wrong Location**:
- Symptom: PRD.md created in root instead of docs/
- Cause: Variable not resolved or LLM ignored instruction
- Solution: Check variable definitions, make instructions more explicit
- See: [Troubleshooting Guide](docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md#issue-2-file-created-at-wrong-location)

**Artifact Not Detected**:
- Symptom: File created but not registered in .gao-dev/documents.db
- Cause: File outside tracked directories (docs/, src/, gao_dev/)
- Solution: Ensure file in tracked directory, check artifact detection logs
- Manual registration: `gao-dev lifecycle register <path> <type>`

**Benchmark Fails**:
- Check ANTHROPIC_API_KEY set
- Verify benchmark config valid: `gao-dev sandbox validate <config>`
- Review logs in `sandbox/projects/<project>/logs/`

**Tests Failing**:
- Run tests: `pytest`
- Check coverage: `pytest --cov=gao_dev`
- Run specific test: `pytest tests/test_specific.py`

---

## Quick Reference

| Need to... | Look at... |
|-----------|-----------|
| **Check what to do next** | **docs/bmm-workflow-status.md** ← START HERE! |
| See current story status | docs/sprint-status.yaml |
| Understand overall system | README.md, this file |
| Workflow variable resolution | docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md |
| Migrate to Epic 18 | docs/MIGRATION_GUIDE_EPIC_18.md |
| Run benchmarks | docs/SETUP.md, sandbox/benchmarks/ |
| Understand scale routing | gao_dev/methodologies/adaptive_agile/scale_levels.py |
| Find agent implementations | gao_dev/agents/ |
| See CLI commands | gao_dev/cli/commands.py, sandbox_commands.py |
| Check code patterns | Existing implementations in gao_dev/ |
| Plugin development | docs/plugin-development-guide.md |
| Metrics & reporting | gao_dev/sandbox/metrics/, gao_dev/sandbox/reporting/ |
| Document lifecycle | docs/features/document-lifecycle-system/ |

---

## Success Criteria

You'll know you're doing well when:
- ✅ User can see your progress (TodoWrite)
- ✅ Code follows quality standards (DRY, SOLID, typed)
- ✅ Atomic commits with clear messages
- ✅ Documentation updated alongside code
- ✅ Tests passing (>80% coverage)
- ✅ User is informed and can interrupt/redirect

---

**Remember**: GAO-Dev is now a complete, production-ready autonomous development orchestration system. The core architecture is finished. Focus is on real-world validation through benchmarks and continuous improvement.

**Start every session by reading `docs/bmm-workflow-status.md`!**
