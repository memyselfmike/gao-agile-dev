# GAO-Dev Project Guide - For Claude

**Last Updated**: 2025-01-12
**Version**: 2.3 (Epic 35 Complete - Interactive Provider Selection)

This document helps you (Claude) quickly understand GAO-Dev's structure, current status, and development patterns.

---

## What is GAO-Dev?

**GAO-Dev** (Generative Autonomous Organisation - Development Team) is an autonomous AI development orchestration system managing the complete software development lifecycle using specialized Claude agents.

**Goal**: Transform "simple prompt → production-ready app" through intelligent workflow selection, scale-adaptive routing, and autonomous agent orchestration.

**Status**: Production-ready core architecture. Now adding ceremony integration and self-learning capabilities.

---

## Core Principles

1. **Workflow-Driven**: All work follows defined workflows with intelligent selection
2. **Agent Specialization**: 8 specialized agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary)
3. **Scale-Adaptive**: Auto-adjusts approach based on project size (Levels 0-4)
4. **Autonomous**: Agents work autonomously to build complete applications
5. **Quality-Focused**: Comprehensive testing, type safety, clean architecture
6. **Observable**: Full visibility into agent activities, metrics, benchmarking
7. **Git-Integrated**: Hybrid file+DB architecture with atomic git transactions
8. **Self-Learning**: System learns from retrospectives and improves over time (NEW!)

---

## Current Status (2025-11-10)

### Latest Achievements

✅ **EPIC 35: Interactive Provider Selection at Startup** - COMPLETE (100%)
  - Interactive prompts with Rich-formatted tables for provider selection
  - Preference persistence to `.gao-dev/provider_preferences.yaml`
  - Cross-platform CLI detection (Windows, macOS, Linux)
  - Ollama local model support (deepseek-r1, llama2, codellama)
  - Validation with actionable error messages and fix suggestions
  - Environment variable bypass for CI/CD (`AGENT_PROVIDER`)
  - Security: YAML injection prevention, input sanitization, file permissions
  - **39 story points, 8 stories - ALL COMPLETE**
  - **120+ tests, 3,000+ lines of comprehensive documentation**
  - **Production-ready: Choose AI provider interactively at startup**

✅ **EPIC 31: Full Mary (Business Analyst) Integration** - COMPLETE (100%)
  - Vision elicitation with 4 techniques (Vision Canvas, Problem-Solution Fit, Outcome Mapping, 5W1H)
  - Brainstorming facilitation with 35 BMAD techniques (SCAMPER, Mind Mapping, etc.)
  - Advanced requirements analysis (MoSCoW, Kano, Dependency, Risk, Constraint)
  - Domain-specific question libraries (5 domains, 300+ questions)
  - All 8 GAO-Dev agents now operational
  - **114+ tests, 2,500+ lines of documentation**
  - **Production-ready: Users can start with vague ideas, Mary clarifies into clear visions**

✅ **EPIC 30: Interactive Brian Chat Interface** - COMPLETE (100%)
  - ChatREPL with Rich formatting and infinite loop
  - Project auto-detection with status display
  - Conversational Brian with natural language understanding
  - Command routing with AI-powered failure analysis
  - Session state management with bounded history
  - Greenfield & brownfield initialization (9 languages)
  - **177+ tests, comprehensive documentation**
  - **Production-ready: Users can now run `gao-dev start`!**

✅ **EPIC 27: Git-Integrated Hybrid Wisdom** - COMPLETE (100%)
  - GitIntegratedStateManager: Atomic file+DB+git operations
  - FastContextLoader: <5ms context loads with caching
  - CeremonyOrchestrator: Multi-agent coordination
  - ConversationManager: Natural dialogue flow
  - Migration tools, E2E tests, performance benchmarks
  - **Complete orchestrator integration**

✅ **EPICS 22-26: Foundation Services** - COMPLETE
  - Epic 22: Orchestrator decomposition (thin facade pattern)
  - Epic 23: GitManager enhancement (14 new methods)
  - Epic 24: State tables & tracker (5 specialized services)
  - Epic 25: Git-integrated state manager
  - Epic 26: Multi-agent ceremonies architecture

✅ **EPICS 18-20: Workflow & Document Systems** - COMPLETE
  - Epic 18: Workflow variable resolution & artifact tracking
  - Epic 20: Project-scoped document lifecycle (.gao-dev/ per project)

✅ **EPIC 10: Prompt & Agent Configuration Abstraction** - COMPLETE
  - All prompts externalized to YAML templates
  - Agent configurations in YAML files
  - Plugin system for custom agents/prompts

✅ **EPIC 7.2: Workflow-Driven Core** - COMPLETE
  - Brian agent for workflow selection
  - Scale-adaptive routing (Levels 0-4)
  - 55+ workflows loaded

✅ **EPICS 1-6: Sandbox & Benchmarking** - COMPLETE
  - Full sandbox infrastructure
  - Comprehensive metrics collection
  - HTML reporting with charts
  - 400+ tests passing

### Recently Completed (Continued)

✅ **EPIC 28: Ceremony-Driven Workflow Integration** - COMPLETE (100%)
  - Automatic ceremony triggers in workflows
  - CeremonyTriggerEngine with intelligent triggering
  - DocumentStructureManager for consistent project structure
  - Multi-agent ceremony coordination
  - 35 story points, 6 stories - ALL COMPLETE
  - **Production-ready: Ceremonies auto-trigger at workflow milestones**

✅ **EPIC 29: Self-Learning Feedback Loop** - COMPLETE (100%)
  - LearningApplicationService with relevance scoring
  - Brian context augmentation with learnings
  - Workflow adjustment engine based on past failures
  - Action items flow into next sprint planning
  - 51 story points, 7 stories - ALL COMPLETE
  - **Production-ready: System learns from retrospectives and improves over time**

### System Capabilities

**The system CAN**:
- Accept simple prompts and intelligently select workflows
- **Interactively select AI providers at startup (Claude Code, OpenCode, local Ollama models)**
- Execute multi-workflow sequences with scale-adaptive routing
- Resolve workflow variables and create artifacts at correct locations
- Track document lifecycle per-project with isolated `.gao-dev/` directories
- Perform atomic file+DB+git operations with auto-rollback
- Load context in <5ms with caching
- Generate comprehensive metrics and HTML reports
- Load prompts and agent configs from YAML
- Support custom agents/prompts via plugins
- **Persist provider preferences and bypass prompts via `AGENT_PROVIDER` env var**

**System NOW CAN (Epics 28-29 Complete)**:
- Auto-trigger ceremonies at workflow milestones
- Learn from retrospectives and improve workflow selection
- Adjust workflows based on past learnings
- Convert action items to stories automatically

---

## The 8 Specialized Agents

| Agent | Role | Primary Use |
|-------|------|-------------|
| **Brian** | Workflow Coordinator | Initial analysis, workflow selection, scale routing |
| **John** | Product Manager | PRDs, feature definition, prioritization |
| **Winston** | Technical Architect | System architecture, technical specifications |
| **Sally** | UX Designer | User experience, wireframes, design |
| **Bob** | Scrum Master | Story creation/management, sprint coordination |
| **Amelia** | Software Developer | Implementation, code reviews, testing |
| **Murat** | Test Architect | Test strategies, quality assurance |
| **Mary** | Business Analyst | Vision elicitation, brainstorming, requirements analysis |

**All agents** configured in `gao_dev/config/agents/*.yaml` with YAML-based prompts.

---

## Project Structure (Essential Paths)

```
gao-agile-dev/
├── gao_dev/                       # Source code
│   ├── agents/                    # Agent implementations
│   ├── cli/                       # CLI commands
│   ├── core/                      # Core services & infrastructure
│   │   ├── services/              # Business services
│   │   ├── models/                # Domain models
│   │   ├── workflow_executor.py   # Workflow execution
│   │   └── state_manager.py       # Git-integrated state manager
│   ├── orchestrator/              # GAODevOrchestrator (main)
│   ├── methodologies/             # Adaptive agile, simple
│   ├── plugins/                   # Plugin system
│   ├── sandbox/                   # Sandbox & benchmarking
│   │   ├── benchmark/             # Benchmark orchestration
│   │   ├── metrics/               # Metrics collection
│   │   └── reporting/             # HTML reporting
│   ├── workflows/                 # 55+ embedded workflows
│   └── config/                    # YAML configurations
│       ├── agents/                # Agent configs
│       ├── prompts/               # Prompt templates
│       └── defaults.yaml          # Default settings
│
├── sandbox/                       # Sandbox workspace
│   ├── benchmarks/                # Benchmark configs
│   └── projects/                  # Test projects
│
├── docs/                          # Documentation
│   ├── bmm-workflow-status.md     # ⭐ START HERE - Current status
│   ├── sprint-status.yaml         # All story statuses
│   └── features/                  # Feature docs (PRDs, architecture)
│
└── tests/                         # 400+ tests
```

### Project-Scoped Architecture

Each project has its own `.gao-dev/` directory:

```
sandbox/projects/my-app/
├── .gao-dev/                     # Project-specific tracking
│   ├── documents.db              # Document lifecycle
│   ├── context.json              # Execution context
│   └── metrics/                  # Project metrics
├── docs/                         # Live documentation
├── src/                          # Application code
└── tests/                        # Test suite
```

### Feature-Based Document Structure (Epics 32-34 - NEW!)

Projects now organize documentation by feature with co-located epic-story structure:

```
docs/features/
├── mvp/                              # Greenfield initial scope
│   ├── PRD.md                        # Product requirements
│   ├── ARCHITECTURE.md               # System architecture
│   ├── README.md                     # Feature overview
│   ├── CHANGELOG.md                  # Version history
│   ├── MIGRATION_GUIDE.md            # Migration docs (Level 4)
│   │
│   ├── epics/                        # Co-located epic-story structure
│   │   ├── 1-foundation/            # Epic 1 (number-name format)
│   │   │   ├── README.md            # Epic definition
│   │   │   ├── stories/             # Stories for Epic 1
│   │   │   │   ├── story-1.1.md
│   │   │   │   └── story-1.2.md
│   │   │   └── context/             # Context XML files
│   │   │       └── story-1.1.xml
│   │   │
│   │   └── 2-advanced/              # Epic 2
│   │       ├── README.md
│   │       └── stories/
│   │           └── story-2.1.md
│   │
│   ├── QA/                          # Quality artifacts
│   ├── retrospectives/              # Retrospectives
│   └── ceremonies/                  # Level 4 only
│
└── user-auth/                       # Subsequent feature
    ├── PRD.md
    ├── ARCHITECTURE.md
    ├── README.md
    ├── CHANGELOG.md
    ├── epics/
    │   └── 1-oauth/
    │       ├── README.md
    │       └── stories/
    ├── QA/
    └── retrospectives/
```

**Key Benefits:**
- **Co-located stories**: Stories live with their epic, not in separate folder
- **Feature isolation**: Each feature is self-contained
- **Scalable**: Supports MVP → multiple features
- **Validated**: Built-in structure compliance checking

**See also:** `docs/features/feature-based-document-structure/MIGRATION_GUIDE.md`

---

## Scale-Adaptive Routing (Levels 0-4)

Brian agent selects workflows based on project scale:

| Level | Type | Stories | Duration | Workflows | Ceremonies |
|-------|------|---------|----------|-----------|------------|
| **0** | Chore | 0 | <1 hour | Direct execution | None |
| **1** | Bug Fix | 0-1 | 1-4 hours | Minimal planning | Retro on failure |
| **2** | Small Feature | 3-8 | 1-2 weeks | PRD → Arch → Stories | Optional |
| **3** | Medium Feature | 12-40 | 1-2 months | Full BMAD | Planning + Retros |
| **4** | Greenfield App | 40+ | 2-6 months | Comprehensive | Full ceremonies |

**Key**: Level determines workflow complexity, not quality. All levels maintain high standards.

---

## Git-Integrated Hybrid Architecture

GAO-Dev uses **hybrid file + database** with **git transaction safety**:

### Core Services

1. **GitIntegratedStateManager** - Atomic file+DB+git operations with auto-rollback
2. **FastContextLoader** - <5ms context loads (LRU cache, >80% hit rate)
3. **CeremonyOrchestrator** - Multi-agent ceremony coordination
4. **ConversationManager** - Natural dialogue with context awareness
5. **GitMigrationManager** - Safe migration with 4-phase rollback
6. **GitAwareConsistencyChecker** - File-DB sync validation and repair

### Key Features

**Atomic Operations**: File write + DB insert + Git commit (all or nothing)
```python
# Example: All 3 operations succeed or all roll back
manager.create_epic(epic_num=1, title="Feature X",
                   file_path=Path("docs/epics/epic-1.md"),
                   content="# Epic 1")
```

**Fast Context Loading**: <5ms with cache, <50ms cold
**Performance**: Epic creation <1s, Story creation <200ms, Context load <5ms

### CLI Commands

```bash
# Migration
gao-dev migrate                    # Migrate to hybrid architecture
gao-dev consistency-check          # Validate file-DB sync
gao-dev consistency-repair         # Fix inconsistencies

# State management (uses hybrid architecture)
gao-dev state list-epics           # Query database
gao-dev state show-story 1 1       # Fast DB lookup
gao-dev state transition 1 1 ready # Atomic state transition
```

**Docs**: See `docs/features/git-integrated-hybrid-wisdom/` for migration guide, API reference, troubleshooting.

---

## Workflow-Driven Architecture

### Execution Flow

1. User provides prompt → "Build a todo app with auth"
2. Brian analyzes → Scale level, requirements, project type
3. Workflow selection → Choose sequence (e.g., PRD → Architecture → Stories → Implementation)
4. Variable resolution → `{{prd_location}}` → `docs/PRD.md`
5. Template rendering → Instructions with resolved variables
6. Orchestration → Coordinate agents (John → Winston → Bob → Amelia)
7. Artifact creation → Files at correct locations with atomic git commits
8. Artifact detection → Snapshot detects all created/modified files
9. Document registration → Track in `.gao-dev/documents.db`
10. Metrics & validation → Collect metrics, check success criteria

### Variable Resolution

**Priority Order** (highest to lowest):
1. Runtime parameters (execution-time values)
2. Workflow YAML defaults (`workflow.yaml`)
3. Config defaults (`config/defaults.yaml`)
4. Common variables (auto-generated: date, project_name, etc.)

**Common Variables**:
- `{{date}}`, `{{timestamp}}`, `{{project_name}}`, `{{project_root}}`
- `{{epic}}`, `{{story}}`, `{{agent}}`, `{{workflow}}`

**Naming Conventions**:
- Locations: `{type}_location` (e.g., `prd_location`)
- Folders: `{type}_folder` (e.g., `output_folder`)
- Paths: `{type}_path` (e.g., `template_path`)
- Use `snake_case`

**Available Workflows**: 55+ across 4 phases (analysis, planning, solutioning, implementation)

---

## Essential Commands

### Core
```bash
gao-dev --help                     # Show help
gao-dev health                     # System health check
gao-dev list-workflows             # List all workflows
gao-dev list-agents                # List all agents
```

### Autonomous
```bash
gao-dev create-prd --name "Project"            # John creates PRD
gao-dev create-architecture --name "Project"   # Winston creates architecture
gao-dev implement-story --epic 1 --story 1     # Bob + Amelia implement
```

### Sandbox
```bash
gao-dev sandbox init <name>        # Create project
gao-dev sandbox run <config.yaml>  # Run benchmark
gao-dev sandbox status             # System status
```

### Metrics & Reporting
```bash
gao-dev metrics report run <id>    # Generate HTML report
gao-dev metrics report compare <id1> <id2>  # Compare runs
```

### Feature Management (Epics 32-34 - NEW!)
```bash
# Create feature
gao-dev create-feature <name> --scale-level 3          # Create new feature
gao-dev create-feature mvp --scope mvp --scale-level 4  # Create MVP

# List features
gao-dev list-features                                   # List all features
gao-dev list-features --scope mvp                       # Filter by scope
gao-dev list-features --status active                   # Filter by status

# Validate structure
gao-dev validate-structure --feature user-auth          # Validate specific feature
gao-dev validate-structure --all                        # Validate all features
cd docs/features/user-auth && gao-dev validate-structure # Auto-detect from pwd

# Database migration
gao-dev migrate                                         # Apply migrations
gao-dev migrate --rollback                              # Rollback migration
```

**Note**: Commands auto-detect project root by searching for `.gao-dev/` or `.sandbox.yaml`.

---

## Development Environment Setup

### Installation Modes

GAO-Dev has **two distinct installation modes** - **CRITICAL: Never mix them**:

**1. Beta Testing Mode** - For using GAO-Dev
```bash
pip install git+https://github.com/memyselfmike/gao-agile-dev.git@main
```

**2. Development Mode** - For contributing to GAO-Dev (YOU ARE HERE)
```bash
git clone https://github.com/memyselfmike/gao-agile-dev.git
cd gao-agile-dev
pip install -e ".[dev]"
python verify_install.py  # MUST SHOW ALL [PASS]
```

**⚠️ Mixing Modes = Stale Installation Issue**

If you previously installed for beta testing, you MUST clean up first:
```bash
# Windows
reinstall_dev.bat

# macOS/Linux
./reinstall_dev.sh
```

**Symptoms of Stale Installation:**
- Code changes don't take effect
- Web server uses wrong project_root
- Logs show `C:\Python314\Lib\site-packages` instead of project directory

**Fix:**
```bash
python verify_install.py  # Check current state
reinstall_dev.bat  # Clean and reinstall (Windows)
./reinstall_dev.sh  # Clean and reinstall (macOS/Linux)
```

**See Also:**
- [INSTALLATION.md](INSTALLATION.md) - Complete installation guide
- [DEV_TROUBLESHOOTING.md](DEV_TROUBLESHOOTING.md) - Detailed troubleshooting

---

## Development Patterns & Best Practices

### 1. Starting a Session

**ALWAYS START HERE**:
1. **Verify installation**: `python verify_install.py` (should show all [PASS])
2. Read `docs/bmm-workflow-status.md` - Current epic, story, what's next
3. Read relevant PRD/Architecture (`docs/features/<feature-name>/`)
4. Check latest commits: `git log --oneline -10`
5. Read current story file for acceptance criteria

### 2. Working on Stories

**Pattern**:
1. Create feature branch: `git checkout -b feature/epic-N-name`
2. Plan with TodoWrite (ONE task in_progress at a time)
3. Write tests first (TDD)
4. Implement functionality
5. Run tests and validate
6. **Atomic commit** (ONE per story): `git commit -m "feat(scope): Story N.M - Description"`
7. Update story status

**Commit Format**:
```
<type>(<scope>): <description>

<optional body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

### 3. Progress Tracking

**Use TodoWrite religiously**:
```python
TodoWrite([
    {"content": "Task 1", "status": "in_progress", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "pending", "activeForm": "Doing task 2"},
])
```

**Rules**:
- Exactly ONE task `in_progress` at a time
- Mark completed IMMEDIATELY after finishing
- Clear todo list when done
- NEVER batch multiple completions

### 4. Code Quality Standards

**Required**:
- ✅ DRY Principle (no duplication)
- ✅ SOLID Principles
- ✅ Type hints throughout (no `Any`)
- ✅ Comprehensive error handling
- ✅ structlog for observability
- ✅ 80%+ test coverage
- ✅ ASCII only (no emojis - Windows compatibility)
- ✅ Black formatting (line length 100)

**Testing**:
- Unit tests for all new code
- Integration tests for workflows
- MyPy passes strict mode
- Current: 400+ tests passing

### 5. Tool Usage

**Read before Write/Edit**:
- ALWAYS use Read tool before Edit or Write
- Understand existing code before modifying
- Preserve indentation and style

**Parallel Tool Calls**:
- If multiple independent reads needed, call in parallel
- User sees all calls at once (more efficient)

**Provide Full Visibility**:
- Tell user what you're about to do
- Explain results as you get them
- Show progress for long operations
- Allow user to interrupt or redirect

### 6. Common Pitfalls to Avoid

❌ **DON'T**:
- Batch multiple story commits
- Leave uncommitted work
- Create files without reading existing code
- Use `Any` type hints
- Skip tests
- Forget to update TodoWrite
- Create unnecessary new files (prefer editing existing)

✅ **DO**:
- One commit per story
- Read before write
- Type everything
- Test everything
- Update progress frequently
- Edit existing files when possible

---

## Prompt & Configuration System

All prompts and agent configs are YAML-based:

**Prompts**: `gao_dev/config/prompts/`
- `tasks/` - Task prompts (create_prd, implement_story, etc.)
- `brian/` - Brian's prompts
- `story_orchestrator/` - Story lifecycle prompts

**Agents**: `gao_dev/config/agents/*.yaml`
- All 8 agents configured in YAML
- Supports reference resolution: `@file:`, `@config:`

**Benefits**:
- No code changes to update prompts
- Easy versioning and customization
- Plugin ecosystem for domain-specific extensions

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| **Changes not taking effect** | `python verify_install.py` → `reinstall_dev.bat` if [FAIL] |
| **Wrong project_root in logs** | Run `reinstall_dev.bat` to clean stale site-packages |
| **Import errors** | `pip install -e .` and verify with `python verify_install.py` |
| **CLI not found** | Reinstall: `pip install -e .` |
| **Stale gao_dev in site-packages** | Run `reinstall_dev.bat` to clean and reinstall |
| **Variable not resolved** | Check workflow.yaml or config/defaults.yaml |
| **File at wrong location** | Check variable definitions, verify resolution |
| **Artifact not detected** | Ensure file in tracked directory (docs/, src/, gao_dev/) |
| **Benchmark fails** | Check ANTHROPIC_API_KEY, validate config |
| **Tests failing** | `pytest --cov=gao_dev` |
| **Orphaned DB records** | `gao-dev consistency-repair` |
| **Slow context loads** | Check cache hit rates, increase cache size |

**Full docs**: See `docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md`

---

## Quick Reference Table

| Need to... | Look at... |
|-----------|-----------|
| **Check what to do next** | **docs/bmm-workflow-status.md** ← START HERE! |
| Current story status | docs/sprint-status.yaml |
| Feature PRD/Architecture | docs/features/<feature-name>/ |
| **Provider selection** | **Set `AGENT_PROVIDER` env var or use interactive prompts** |
| **Create new feature** | **gao-dev create-feature <name> --scale-level 3** |
| **List all features** | **gao-dev list-features** |
| **Validate feature structure** | **gao-dev validate-structure --feature <name>** |
| **Migrate to feature-based** | **docs/features/feature-based-document-structure/MIGRATION_GUIDE.md** |
| Workflow variables | docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md |
| Git-integrated architecture | docs/features/git-integrated-hybrid-wisdom/ |
| Migration guides | docs/MIGRATION_GUIDE_EPIC_*.md |
| Run benchmarks | docs/SETUP.md, sandbox/benchmarks/ |
| Scale routing logic | gao_dev/methodologies/adaptive_agile/scale_levels.py |
| Agent implementations | gao_dev/agents/, gao_dev/config/agents/ |
| CLI commands | gao_dev/cli/ |
| Plugin development | docs/plugin-development-guide.md |
| Metrics & reporting | gao_dev/sandbox/metrics/, gao_dev/sandbox/reporting/ |

---

## Success Criteria

**You're doing well when**:
- ✅ User can see your progress (TodoWrite)
- ✅ Code follows quality standards (DRY, SOLID, typed)
- ✅ Atomic commits with clear messages
- ✅ Documentation updated alongside code
- ✅ Tests passing (>80% coverage)
- ✅ User is informed and can interrupt/redirect

---

## Remember

1. **GAO-Dev is production-ready** - Core architecture complete, now enhancing with ceremonies and self-learning
2. **Start every session with `docs/bmm-workflow-status.md`** - Always know where you are
3. **One commit per story** - Atomic, clear, traceable
4. **TodoWrite is your friend** - Track progress, show user what's happening
5. **Read before write** - Understand before modifying
6. **Quality matters** - Tests, types, clean code - always

**Current Focus**: Epics 28-29 complete. Ready for next epic (Feature-Based Document Structure) or other priorities as directed.

---

**Version**: 2.0 (Streamlined for context efficiency)
**Last Updated**: 2025-11-09
**Changes**: Consolidated verbose sections, updated status with Epics 28-29, added Development Patterns section
