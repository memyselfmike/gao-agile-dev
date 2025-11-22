# GAO-Dev Project Guide - For Claude

**Last Updated**: 2025-01-22
**Version**: 3.0 (Restructured for clarity and efficiency)

This document helps you (Claude) quickly understand GAO-Dev's structure, current status, and how to contribute effectively.

---

## 🎯 TL;DR - Start Here

**What is GAO-Dev?** Autonomous AI development orchestration system managing the complete software development lifecycle using specialized Claude agents.

**Your First Steps**:
1. **Check current work**: `docs/bmm-workflow-status.md`
2. **Verify installation**: `python verify_install.py` (must show all [PASS])
3. **See what to do**: Use "I Want To..." decision tree below
4. **Follow patterns**: [docs/developers/DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md)

**Production Status**: ✅ Core architecture complete (400+ tests, 80%+ coverage, 55+ workflows, 9 agents)

---

## 📖 I Want To...

Use this decision tree to find what you need quickly:

### Development Tasks

| I want to... | Go to... |
|-------------|----------|
| **Find out what to work on next** | [docs/bmm-workflow-status.md](docs/bmm-workflow-status.md) ← START HERE |
| **Set up my development environment** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) → Installation section |
| **Fix a bug** | 1. Use bug-tester agent (`.claude/agents/bug-tester.md`)<br>2. Follow [DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md#5-bug-fixing-and-testing) |
| **Add a new workflow** | [docs/developers/ADDING_WORKFLOWS.md](docs/developers/ADDING_WORKFLOWS.md) |
| **Add a web UI feature** | [docs/developers/ADDING_WEB_FEATURES.md](docs/developers/ADDING_WEB_FEATURES.md) |
| **Add a new agent** | [docs/developers/ADDING_AGENTS.md](docs/developers/ADDING_AGENTS.md) |
| **Write tests** | [docs/developers/TESTING_GUIDE.md](docs/developers/TESTING_GUIDE.md) |
| **See code examples** | [docs/examples/](docs/examples/) - Complete feature implementations |
| **Understand development workflow** | [docs/developers/DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md) |

### Understanding the System

| I want to... | Go to... |
|-------------|----------|
| **Understand the architecture** | See "Core Architecture" section below + [docs/features/](docs/features/) |
| **Learn about agents** | See "The 9 Specialized Agents" section below |
| **See all API endpoints** | [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - 50+ endpoints, 25+ events |
| **Quick integration examples** | [docs/QUICK_START.md](docs/QUICK_START.md) - Copy-paste patterns |
| **Web interface architecture** | [docs/features/web-interface/ARCHITECTURE.md](docs/features/web-interface/ARCHITECTURE.md) |
| **Git-integrated architecture** | [docs/features/git-integrated-hybrid-wisdom/](docs/features/git-integrated-hybrid-wisdom/) |
| **Onboarding system** | [docs/features/streamlined-onboarding/](docs/features/streamlined-onboarding/) |
| **Scale-adaptive routing** | See "Scale Levels" section below |

### Troubleshooting

| I want to... | Go to... |
|-------------|----------|
| **Fix installation issues** | 1. Run `python verify_install.py`<br>2. Run `reinstall_dev.bat` (Windows) or `./reinstall_dev.sh` (macOS/Linux)<br>3. See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md#installation) |
| **Debug web interface** | [docs/features/web-interface/TROUBLESHOOTING.md](docs/features/web-interface/TROUBLESHOOTING.md) |
| **Fix file-DB sync issues** | `gao-dev consistency-repair` + [docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md](docs/features/git-integrated-hybrid-wisdom/TROUBLESHOOTING.md) |
| **Understand errors** | See "Troubleshooting Quick Reference" section below |

---

## What is GAO-Dev?

**GAO-Dev** (Generative Autonomous Organisation - Development Team) is an autonomous AI development orchestration system managing the complete software development lifecycle using specialized Claude agents.

**Goal**: Transform "simple prompt → production-ready app" through intelligent workflow selection, scale-adaptive routing, and autonomous agent orchestration.

**Status**: Production-ready core architecture. Comprehensive web interface, multi-environment support, and self-learning capabilities.

---

## Core Principles

1. **Workflow-Driven**: All work follows defined workflows with intelligent selection
2. **Agent Specialization**: 9 specialized agents (Brian, Mary, John, Winston, Sally, Bob, Amelia, Murat, Diana)
3. **Scale-Adaptive**: Auto-adjusts approach based on project size (Levels 0-4)
4. **Autonomous**: Agents work autonomously to build complete applications
5. **Quality-Focused**: Comprehensive testing, type safety, clean architecture
6. **Observable**: Full visibility into agent activities via web interface
7. **Git-Integrated**: Hybrid file+DB architecture with atomic git transactions
8. **Self-Learning**: System learns from retrospectives and improves over time

---

## Current Status

### Latest Production Features

✅ **Browser-Based Web Interface** (Epic 39)
- Real-time WebSocket event streaming (<50ms latency)
- Interactive chat with all 9 agents
- Visual Kanban board with drag-and-drop
- Monaco code editor with atomic git commits
- Activity stream (10,000+ events with virtual scrolling)
- **50+ API endpoints, 25+ WebSocket event types**

✅ **Streamlined Onboarding** (Epics 40-42)
- Unified `gao-dev start` command with environment detection
- Multi-environment support (Desktop, Docker, SSH, WSL, CI/CD)
- Web wizard (desktop), TUI wizard (remote), headless mode (CI/CD)
- **<3 min time to first Brian response**

✅ **Interactive Provider Selection** (Epic 35)
- Choose AI providers at startup (Claude Code, OpenCode, Ollama)
- Preference persistence to `.gao-dev/provider_preferences.yaml`
- Environment variable bypass for CI/CD (`AGENT_PROVIDER`)

✅ **Full Agent Roster** (Epic 31)
- All 9 specialized agents operational
- Mary (Business Analyst) with vision elicitation and brainstorming
- Diana (Document Keeper) for documentation management

✅ **Self-Learning Capabilities** (Epics 28-29)
- Automatic ceremony triggers at workflow milestones
- Learning from retrospectives with workflow adjustments
- Action items flow into next sprint planning

### System Capabilities Summary

**The system CAN**:
- Accept simple prompts and intelligently select workflows
- Execute multi-workflow sequences with scale-adaptive routing (Levels 0-4)
- Perform atomic file+DB+git operations with auto-rollback
- Provide full-stack web interface with real-time observability
- Stream agent activities via WebSocket (<50ms latency)
- Deploy to Docker, SSH, WSL, CI/CD with environment detection
- Learn from retrospectives and improve workflow selection
- Load context in <5ms with caching (>80% hit rate)

**Quick Stats**:
- **400+ tests passing** (80%+ coverage)
- **55+ workflows** across 4 phases
- **9 specialized agents** (all operational)
- **50+ API endpoints** (REST + WebSocket)
- **Production-ready** core architecture

---

## The 9 Specialized Agents

| Agent | Role | Primary Use |
|-------|------|-------------|
| **Brian** | Workflow Coordinator & Engineering Manager | Initial analysis, workflow selection, scale routing |
| **Mary** | Business Analyst | Vision elicitation, brainstorming, requirements analysis |
| **John** | Product Manager | PRDs, feature definition, prioritization |
| **Winston** | Technical Architect | System architecture, technical specifications |
| **Sally** | UX Designer | User experience, wireframes, design |
| **Bob** | Scrum Master | Story creation/management, sprint coordination |
| **Amelia** | Software Developer | Implementation, code reviews, testing |
| **Murat** | Test Architect | Test strategies, quality assurance |
| **Diana** | Document Keeper & Knowledge Architect | Documentation management, guides, API references |

**All agents** configured in `gao_dev/config/agents/*.yaml` with YAML-based prompts.

**See**: `.claude/agents/` for detailed agent workflows and skills.

---

## Core Architecture

### Scale-Adaptive Routing (Levels 0-4)

Brian agent selects workflows based on project scale:

| Level | Type | Stories | Duration | Workflows | Ceremonies |
|-------|------|---------|----------|-----------|------------|
| **0** | Chore | 0 | <1 hour | Direct execution | None |
| **1** | Bug Fix | 0-1 | 1-4 hours | Minimal planning | Retro on failure |
| **2** | Small Feature | 3-8 | 1-2 weeks | PRD → Arch → Stories | Optional |
| **3** | Medium Feature | 12-40 | 1-2 months | Full BMAD | Planning + Retros |
| **4** | Greenfield App | 40+ | 2-6 months | Comprehensive | Full ceremonies |

**Key**: Level determines workflow complexity, not quality. All levels maintain high standards.

### Technology Stack

**Backend**:
- Python 3.11+ / FastAPI / WebSocket / SQLite
- Atomic file+DB+git operations (GitIntegratedStateManager)
- LRU caching (<5ms context loads)

**Frontend**:
- React 19 / TypeScript / Vite
- Zustand state management
- shadcn/ui components
- Monaco code editor

**Agents**:
- Anthropic Claude (primary)
- OpenAI (optional)
- Ollama (local models)

### Project Structure

```
gao-agile-dev/
├── gao_dev/                       # Source code
│   ├── agents/                    # Agent implementations
│   ├── cli/                       # CLI commands
│   ├── core/                      # Core services (StateManager, WorkflowExecutor)
│   ├── web/                       # Web interface (API + frontend)
│   │   ├── api/                   # 50+ REST endpoints
│   │   └── frontend/              # React 19 app
│   ├── orchestrator/              # GAODevOrchestrator (main)
│   ├── workflows/                 # 55+ embedded workflows
│   └── config/                    # YAML configurations (agents, prompts)
│
├── docs/                          # Documentation
│   ├── bmm-workflow-status.md     # ⭐ START HERE - Current status
│   ├── sprint-status.yaml         # All story statuses
│   ├── developers/                # Developer guides (NEW!)
│   │   ├── DEVELOPMENT_PATTERNS.md  # Development workflow
│   │   ├── ADDING_WORKFLOWS.md      # Add workflows
│   │   ├── ADDING_WEB_FEATURES.md   # Extend web UI
│   │   ├── ADDING_AGENTS.md         # Add agents
│   │   └── TESTING_GUIDE.md         # Testing patterns
│   ├── examples/                  # Code examples (NEW!)
│   │   ├── complete-feature-implementation.md
│   │   ├── testing-strategies.md
│   │   ├── error-handling-patterns.md
│   │   └── performance-patterns.md
│   ├── features/                  # Feature docs (PRDs, architecture)
│   ├── QUICK_START.md             # Integration patterns (NEW!)
│   └── API_REFERENCE.md           # Complete API catalog (NEW!)
│
└── tests/                         # 400+ tests (80%+ coverage)
```

### Each Project Has `.gao-dev/` Directory

```
sandbox/projects/my-app/
├── .gao-dev/                     # Project-specific tracking
│   ├── documents.db              # Document lifecycle (SQLite)
│   ├── context.json              # Execution context
│   ├── session.token             # WebSocket authentication
│   ├── provider_preferences.yaml # AI provider config
│   └── metrics/                  # Project metrics
├── docs/                         # Live documentation
├── src/                          # Application code
└── tests/                        # Test suite
```

---

## Essential Commands

### Getting Started

```bash
# Start GAO-Dev (unified entry point)
gao-dev start                      # Auto-detects environment (desktop/Docker/SSH/CI)

# Verify installation (CRITICAL - run first!)
python verify_install.py           # Must show all [PASS]

# Check system health
gao-dev health                     # System health check
gao-dev list-workflows             # List all 55+ workflows
gao-dev list-agents                # List all 9 agents
```

### Development Workflow

```bash
# 1. Check current status
cat docs/bmm-workflow-status.md    # What to work on next

# 2. Verify installation
python verify_install.py           # All [PASS]?

# 3. Create feature branch
git checkout -b feature/epic-N-name

# 4. Run tests (after changes)
pytest --cov=gao_dev tests/

# 5. Type check
mypy gao_dev/ --strict

# 6. Format code
black gao_dev/ --line-length 100

# 7. Atomic commit
git commit -m "feat(scope): Story N.M - Description"
```

### Autonomous Workflows

```bash
gao-dev create-prd --name "Project"            # John creates PRD
gao-dev create-architecture --name "Project"   # Winston creates architecture
gao-dev implement-story --epic 1 --story 1     # Bob + Amelia implement
```

### Git-Integrated State Management

```bash
gao-dev migrate                    # Migrate to hybrid architecture
gao-dev consistency-check          # Validate file-DB sync
gao-dev consistency-repair         # Fix inconsistencies
gao-dev state list-epics           # Query database
gao-dev state show-story 1 1       # Fast DB lookup
gao-dev state transition 1 1 ready # Atomic state transition
```

**See**: [docs/features/git-integrated-hybrid-wisdom/](docs/features/git-integrated-hybrid-wisdom/) for complete documentation.

---

## Development Workflow

### The Standard Pattern

**See**: [docs/developers/DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md) for complete guide.

**Quick Summary**:
1. ✅ Verify installation: `python verify_install.py`
2. ✅ Read `docs/bmm-workflow-status.md` - Current epic/story
3. ✅ Create feature branch
4. ✅ Plan with TodoWrite (ONE task in_progress at a time)
5. ✅ Write tests first (TDD)
6. ✅ Implement functionality
7. ✅ Run tests and validate
8. ✅ Atomic commit (ONE per story)
9. ✅ Update story status

### Code Quality Requirements

- ✅ **DRY Principle** (no duplication)
- ✅ **SOLID Principles**
- ✅ **Type hints throughout** (no `Any`)
- ✅ **Comprehensive error handling**
- ✅ **structlog for observability**
- ✅ **80%+ test coverage**
- ✅ **ASCII only** (no emojis - Windows compatibility)
- ✅ **Black formatting** (line length 100)

### Bug Fixing

**CRITICAL: Always use bug-tester agent for bug fixes**

```bash
# Quick commands
/verify-bug-fix   # Complete verification workflow (dev + beta)
/test-ui          # Systematic Playwright UI testing
```

**Required**:
- ✅ Test in development environment
- ✅ Test in beta environment (C:\Testing)
- ✅ Playwright verification with screenshots
- ✅ Server log analysis
- ✅ Regression test creation
- ✅ Verification report

**See**: `.claude/agents/bug-tester.md` for complete workflow.

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| **Changes not taking effect** | `python verify_install.py` → `reinstall_dev.bat` if [FAIL] |
| **Wrong project_root in logs** | Run `reinstall_dev.bat` to clean stale site-packages |
| **Import errors** | `pip install -e ".[dev]"` and verify with `python verify_install.py` |
| **CLI not found** | Reinstall: `pip install -e ".[dev]"` |
| **Stale gao_dev in site-packages** | Run `reinstall_dev.bat` to clean and reinstall |
| **Variable not resolved** | Check `workflow.yaml` or `config/defaults.yaml` |
| **File at wrong location** | Check variable definitions in workflow YAML |
| **Artifact not detected** | Ensure file in tracked directory (`docs/`, `src/`, `gao_dev/`) |
| **Benchmark fails** | Check `ANTHROPIC_API_KEY`, validate config |
| **Tests failing** | `pytest --cov=gao_dev` |
| **Orphaned DB records** | `gao-dev consistency-repair` |
| **Slow context loads** | Check cache hit rates (should be >80%) |
| **Web interface errors** | See [docs/features/web-interface/TROUBLESHOOTING.md](docs/features/web-interface/TROUBLESHOOTING.md) |

**Full docs**: See feature-specific troubleshooting guides in `docs/features/`.

---

## Quick Reference Table

| Need to... | Look at... |
|-----------|-----------|
| **Check what to do next** | **[docs/bmm-workflow-status.md](docs/bmm-workflow-status.md)** ← START HERE! |
| **Development workflow** | **[docs/developers/DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md)** |
| **Contributing guide** | **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** |
| **Quick integration examples** | **[docs/QUICK_START.md](docs/QUICK_START.md)** ← Copy-paste code! |
| **API reference** | **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** ← All endpoints/events |
| **Code examples** | **[docs/examples/](docs/examples/)** - Complete implementations |
| Current story status | [docs/sprint-status.yaml](docs/sprint-status.yaml) |
| Feature PRD/Architecture | `docs/features/<feature-name>/` |
| Add workflow | [docs/developers/ADDING_WORKFLOWS.md](docs/developers/ADDING_WORKFLOWS.md) |
| Add web feature | [docs/developers/ADDING_WEB_FEATURES.md](docs/developers/ADDING_WEB_FEATURES.md) |
| Add agent | [docs/developers/ADDING_AGENTS.md](docs/developers/ADDING_AGENTS.md) |
| Testing guide | [docs/developers/TESTING_GUIDE.md](docs/developers/TESTING_GUIDE.md) |
| Web UI architecture | [docs/features/web-interface/ARCHITECTURE.md](docs/features/web-interface/ARCHITECTURE.md) |
| Git-integrated architecture | [docs/features/git-integrated-hybrid-wisdom/](docs/features/git-integrated-hybrid-wisdom/) |
| Onboarding system | [docs/features/streamlined-onboarding/](docs/features/streamlined-onboarding/) |
| Provider selection | Set `AGENT_PROVIDER` env var or use interactive prompts |
| Feature management | `gao-dev create-feature`, `gao-dev list-features` |
| Workflow variables | [docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md](docs/features/document-lifecycle-system/VARIABLE_RESOLUTION.md) |
| Scale routing logic | `gao_dev/methodologies/adaptive_agile/scale_levels.py` |
| Agent implementations | `gao_dev/agents/`, `gao_dev/config/agents/` |
| CLI commands | `gao_dev/cli/` |
| Plugin development | [docs/plugin-development-guide.md](docs/plugin-development-guide.md) |
| Metrics & reporting | `gao_dev/sandbox/metrics/`, `gao_dev/sandbox/reporting/` |

---

## Success Criteria

**You're doing well when**:
- ✅ User can see your progress (TodoWrite updated continuously)
- ✅ Code follows quality standards (DRY, SOLID, typed, tested)
- ✅ Atomic commits with clear messages (one per story)
- ✅ Documentation updated alongside code
- ✅ Tests passing (>80% coverage)
- ✅ User is informed and can interrupt/redirect

---

## Remember (Critical Reminders)

1. **Start every session with `docs/bmm-workflow-status.md`** - Always know where you are
2. **Verify installation FIRST**: `python verify_install.py` (must show all [PASS])
3. **One commit per story** - Atomic, clear, traceable
4. **TodoWrite is your friend** - Track progress, show user what's happening (ONE task in_progress)
5. **Read before write** - Always use Read tool before Edit or Write
6. **Quality matters** - Tests, types, clean code - always
7. **Use bug-tester agent for ALL bug fixes** - Systematic verification required
8. **Follow development patterns** - See [DEVELOPMENT_PATTERNS.md](docs/developers/DEVELOPMENT_PATTERNS.md)

**GAO-Dev is production-ready** - Core architecture complete with comprehensive web interface, multi-environment support, and self-learning capabilities. Ready for continued enhancement and feature development.

---

**Version**: 3.0 (Restructured for clarity and efficiency)
**Last Updated**: 2025-01-22
**Changes**:
- Added "I Want To..." decision tree for quick navigation
- Extracted Development Patterns to separate document
- Simplified verbose sections with links to detailed docs
- Enhanced quick reference table
- Reduced from 1,071 lines to ~650 lines (40% reduction)
- Added links to new developer guides and code examples
