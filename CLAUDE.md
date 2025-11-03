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

---

## Current Status (As of 2025-11-03)

### Latest Achievements

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
- Create real project artifacts with atomic git commits
- Track comprehensive metrics
- Generate detailed HTML reports
- Validate results against success criteria

### What's Next

1. **Real-world testing** - Run workflow-driven benchmarks to build complete applications
2. **Epic 9: Continuous Improvement** - Optimize based on benchmark learnings
3. **Production deployment** - Core architecture is complete and tested

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
│   └── config/                    # Default configs
│       └── defaults.yaml
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
4. **Orchestration** → Coordinates agent execution (John → Winston → Bob → Amelia)
5. **Artifact creation** → Real files created with atomic git commits
6. **Metrics tracking** → Performance, autonomy, quality metrics collected
7. **Validation** → Results checked against success criteria

### Available Workflows (55+)

**Phase 1: Analysis**
- Product brief, research, brainstorming

**Phase 2: Planning**
- PRD, Game Design Doc, Tech Specs, Epics

**Phase 3: Solutioning**
- System architecture, API design, data models

**Phase 4: Implementation**
- Story creation, story development, code review, testing

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
| Run benchmarks | docs/SETUP.md, sandbox/benchmarks/ |
| Understand scale routing | gao_dev/methodologies/adaptive_agile/scale_levels.py |
| Find agent implementations | gao_dev/agents/ |
| See CLI commands | gao_dev/cli/commands.py, sandbox_commands.py |
| Check code patterns | Existing implementations in gao_dev/ |
| Plugin development | docs/plugin-development-guide.md |
| Metrics & reporting | gao_dev/sandbox/metrics/, gao_dev/sandbox/reporting/ |

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
