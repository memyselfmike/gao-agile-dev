# GAO-Dev Project Context

**Last Updated**: 2025-10-27
**Status**: Active Development
**Current Phase**: Sandbox & Benchmarking System Implementation

---

## Quick Start

**New to this project?** Read in this order:
1. This file (PROJECT_CONTEXT.md) ← You are here
2. README.md (project overview)
3. `.claude/CLAUDE.md` (for Claude - development guide)
4. `docs/features/sandbox-system/PRD.md` (current feature requirements)

**Ready to work?** Start with:
- Current story: `docs/features/sandbox-system/stories/epic-1/story-1.1.md`
- Or check: `SESSION_SUMMARY.md` for latest progress

---

## What is GAO-Dev?

**GAO-Dev** is an autonomous AI development orchestration system that manages the complete software development lifecycle using specialized Claude agents.

### The Vision

**From**: Manual prompting and intervention
**To**: `gao-dev build "todo app with auth"` → Complete, production-ready application

### How It Works

1. **7 Specialized Agents** work together:
   - Mary (Business Analyst)
   - John (Product Manager)
   - Winston (Architect)
   - Sally (UX Designer)
   - Bob (Scrum Master)
   - Amelia (Developer)
   - Murat (Test Architect)

2. **Workflow-Driven Development**:
   - Each phase has defined workflows
   - Agents follow workflows autonomously
   - Artifacts created in correct locations

3. **Complete SDLC**:
   - Analysis → Planning → Solutioning → Implementation
   - PRD → Architecture → Stories → Code → Tests

---

## Current Status

### ✅ What's Complete

**Phase 1-5: Agent SDK Integration** (Initial system)
- Custom MCP tool layer (11 tools)
- Agent definitions (7 specialized agents)
- GAODevOrchestrator class
- CLI integration (autonomous commands)
- Environment setup (uv support)
- All committed & pushed to main

**Phase 6: Sandbox Planning** (Current feature documentation)
- PRD: Complete specification
- Architecture: Full system design
- Epics: 6 epics defined with breakdown
- Stories: Story 1.1 ready for implementation

### 🔄 What's In Progress

**Epic 1: Sandbox Infrastructure** (2 weeks estimated)
- **Next**: Story 1.1 - Sandbox CLI Command Structure
- **Goal**: Working sandbox project management
- **Stories**: 6 stories total

### 📋 What's Next

1. **Short-term** (Weeks 1-2): Epic 1 - Sandbox Infrastructure
2. **Medium-term** (Weeks 3-4): Epic 2 - Boilerplate Integration
3. **Long-term** (Weeks 5-10): Epics 3-6 - Full benchmarking system

---

## Repository Structure

```
gao-agile-dev/
│
├── 📄 Core Documentation
│   ├── README.md                    # Main project README
│   ├── PROJECT_CONTEXT.md           # This file
│   ├── SESSION_SUMMARY.md           # Latest session summary
│   ├── pyproject.toml               # Package configuration
│   └── .claude/
│       └── CLAUDE.md                # Guide for Claude
│
├── 📚 Documentation
│   ├── docs/
│   │   ├── README.md                # Doc organization
│   │   ├── QA_STANDARDS.md          # Quality standards
│   │   └── features/
│   │       └── sandbox-system/      # Current feature
│   │           ├── PRD.md
│   │           ├── ARCHITECTURE.md
│   │           ├── epics.md
│   │           └── stories/
│   │
│   └── sandbox/                     # Sandbox WORKSPACE
│       ├── README.md
│       ├── benchmarks/              # Benchmark configs
│       └── projects/                # Test projects (created by agents)
│
└── 💻 Source Code
    └── gao_dev/
        ├── agents/                  # Agent personas
        ├── cli/                     # CLI commands
        ├── core/                    # Core services
        ├── orchestrator/            # Agent orchestration
        ├── tools/                   # MCP tools
        ├── workflows/               # Embedded workflows
        └── sandbox/                 # Sandbox system (TBD)
```

---

## The 7 Agents

| Agent | Role | Primary Use |
|-------|------|-------------|
| **Mary** | Business Analyst | Research, analysis, requirements |
| **John** | Product Manager | PRDs, features, prioritization |
| **Winston** | Technical Architect | System design, technical specs |
| **Sally** | UX Designer | User experience, wireframes |
| **Bob** | Scrum Master | Stories, sprint management |
| **Amelia** | Developer | Implementation, code reviews |
| **Murat** | Test Architect | Test strategies, QA |

**Personas**: Defined in `gao_dev/agents/*.md`
**Configs**: Defined in `gao_dev/orchestrator/agent_definitions.py`

---

## Current Feature: Sandbox & Benchmarking System

### Purpose

Build a system to:
1. **Test** GAO-Dev's autonomous capabilities
2. **Measure** performance (time, tokens, quality)
3. **Validate** end-to-end workflows
4. **Benchmark** improvements over time

### How It Will Work

```bash
# Define what to build
cat > benchmarks/todo-app.yaml << EOF
benchmark:
  name: "todo-app-baseline"
  initial_prompt: "Build a todo app with auth..."
EOF

# Run benchmark
gao-dev sandbox run benchmarks/todo-app.yaml

# Agents work autonomously:
# Mary → John → Winston → Sally → Bob → Amelia → Murat
# Create: docs/, src/, tests/, docker-compose.yml

# Review results
gao-dev sandbox report <run-id>
# Shows: time taken, tokens used, quality metrics, etc.
```

### Reference Application

**Todo App** (Next.js + FastAPI + PostgreSQL)
- Boilerplate: https://github.com/webventurer/simple-nextjs-starter
- Features: Auth, CRUD, categories, responsive UI
- Tests: >80% coverage
- Deployment: Docker

### Metrics Tracked

- **Performance**: Time, tokens, API cost
- **Autonomy**: Interventions, one-shot success rate
- **Quality**: Test coverage, type errors, vulnerabilities
- **Workflow**: Story cycle time, phase distribution

---

## Technology Stack

### Production Code
- **Language**: Python 3.11+
- **CLI**: Click
- **Logging**: structlog
- **Type Checking**: MyPy (strict mode)
- **Linting**: Ruff
- **Formatting**: Black (line length 100)
- **Testing**: pytest with coverage

### Agent System
- **Framework**: Claude Agent SDK
- **MCP Server**: Custom GAO-Dev tools
- **Execution**: Standalone mode (for benchmarks)

### Target Applications (what agents will build)
- **Frontend**: Next.js 15, TypeScript, React
- **Backend**: FastAPI (Python) or Node.js
- **Database**: PostgreSQL with Prisma ORM
- **Deployment**: Docker + docker-compose

---

## Development Workflow

### 1. Planning Phase (You Are Here)
**Location**: `docs/features/<feature-name>/`
- Create PRD (requirements)
- Create ARCHITECTURE (design)
- Define epics and stories

### 2. Implementation Phase (Next)
**Location**: `gao_dev/<module-name>/`
- Implement story-by-story
- Follow quality standards
- Write tests alongside code

### 3. Testing Phase
- Unit tests (pytest)
- Integration tests
- Type checking (mypy)
- Coverage (>80%)

### 4. Documentation Phase
- Update READMEs
- Add docstrings
- Update architecture if needed

### 5. Release Phase
- Commit with conventional message
- Push to main
- Tag version (if release)

---

## Quality Standards

**All code must meet**: 14/14 QA criteria (see `docs/QA_STANDARDS.md`)

### Critical Requirements
- ✅ No code duplication (DRY)
- ✅ No magic numbers (extract to constants)
- ✅ No `Any` types (use specific types)
- ✅ Type hints on all functions
- ✅ Docstrings on public API
- ✅ 80%+ test coverage
- ✅ SOLID principles
- ✅ Clean architecture

### Code Review Checklist
- [ ] QA standards met (14/14)
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Commit message follows convention
- [ ] No regressions

---

## Git Workflow

### Branches
- `main` - Production-ready code (protected)
- `feature/<name>` - Feature branches

### Commit Format
```
<type>(<scope>): <description>

<body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

### Current Branch
`main` (all work currently on main - no feature branches yet)

---

## CLI Commands

### Current (Available Now)
```bash
# Setup
gao-dev init --name "Project Name"
gao-dev health

# Information
gao-dev list-workflows
gao-dev list-agents
gao-dev version

# Traditional workflow execution
gao-dev execute <workflow> -p key=value
```

### Autonomous (Not Yet Working from Claude Code)
```bash
# These spawn agents - require standalone mode
gao-dev create-prd --name "Project"
gao-dev create-story --epic 1 --story 1
gao-dev implement-story --epic 1 --story 1
gao-dev create-architecture --name "Project"
```

### Sandbox (To Be Implemented)
```bash
gao-dev sandbox init <project>
gao-dev sandbox run <benchmark-config>
gao-dev sandbox report <run-id>
gao-dev sandbox compare <run1> <run2>
```

---

## Key Files Reference

### Documentation
- `README.md` - Project overview
- `PROJECT_CONTEXT.md` - This file
- `.claude/CLAUDE.md` - Development guide
- `docs/QA_STANDARDS.md` - Quality standards
- `SESSION_SUMMARY.md` - Latest progress

### Current Feature
- `docs/features/sandbox-system/PRD.md` - Requirements
- `docs/features/sandbox-system/ARCHITECTURE.md` - Design
- `docs/features/sandbox-system/epics.md` - Epic breakdown
- `docs/features/sandbox-system/stories/epic-1/story-1.1.md` - Next story

### Source Code
- `gao_dev/__init__.py` - Package root
- `gao_dev/cli/commands.py` - CLI implementation
- `gao_dev/orchestrator/orchestrator.py` - Main orchestrator
- `gao_dev/tools/gao_tools.py` - MCP tools
- `gao_dev/agents/*.md` - Agent personas

### Configuration
- `pyproject.toml` - Package config, dependencies
- `gao_dev/config/defaults.yaml` - Default settings

---

## Common Questions

### Q: Where should I put documentation for a new feature?
**A**: `docs/features/<feature-name>/` with PRD.md, ARCHITECTURE.md, etc.

### Q: Where does the sandbox workspace go?
**A**: `sandbox/` is for test projects created during benchmark runs, NOT documentation

### Q: Can I spawn agents from Claude Code?
**A**: Not yet - agent spawning requires standalone mode with API key

### Q: What's the difference between docs/features and sandbox/?
**A**:
- `docs/features/` = Documentation ABOUT building features
- `sandbox/` = Workspace WHERE agents create test projects

### Q: What should I work on next?
**A**: Check `SESSION_SUMMARY.md` for latest, or Story 1.1 in `docs/features/sandbox-system/stories/`

### Q: How do I know if my code is good enough?
**A**: Run QA validation - must score 12/14 or higher (see `docs/QA_STANDARDS.md`)

---

## Critical Limitations

### Agent Spawning from Claude Code
**Problem**: Can't spawn GAO-Dev agents from within Claude Code session (session nesting)

**Workarounds**:
1. **Standalone mode**: Run with API key outside IDE
2. **Manual execution**: Follow workflow instructions manually
3. **Hybrid mode**: Generate plans, execute manually

**Future**: Epic 4 Story 4.8 will implement standalone execution mode

### Windows Console Compatibility
**Problem**: Windows console can't display Unicode/emojis

**Solution**: Use ASCII only (`>>`, `[OK]`, `[WARN]`, `[FAIL]`)

---

## Success Metrics

We'll know GAO-Dev is successful when:
- ✅ Simple prompt → Working application (end-to-end)
- ✅ >80% autonomous (minimal manual intervention)
- ✅ >80% test coverage
- ✅ Production-ready quality
- ✅ <1 hour total time (for todo app)
- ✅ <$5 API cost per run

**Current baseline**: To be established with first benchmark run

---

## Contributing

### For Humans
1. Read this file
2. Read `.claude/CLAUDE.md`
3. Check current story in `docs/features/sandbox-system/stories/`
4. Follow quality standards
5. Submit PR

### For Claude
1. Read `.claude/CLAUDE.md`
2. Check `SESSION_SUMMARY.md` for latest progress
3. Read current story
4. Use TodoWrite to track progress
5. Follow quality standards
6. Commit with conventional messages

---

## Resources

- **Repository**: https://github.com/memyselfmike/gao-agile-dev
- **BMAD Method** (inspiration): Original methodology
- **Claude Agent SDK**: Framework used
- **Next.js Starter**: https://github.com/webventurer/simple-nextjs-starter

---

## Contact & Support

- **Issues**: GitHub Issues
- **Questions**: Check docs first, then ask
- **Latest Progress**: Always in `SESSION_SUMMARY.md`

---

**Last Commit**: `9a89931` (Documentation reorganization)
**Next Milestone**: Epic 1 Complete (Sandbox Infrastructure)
**Target Date**: 2 weeks from start

---

*This document provides complete context for anyone (human or AI) joining the project.*
