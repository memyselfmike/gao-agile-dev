# GAO-Dev Project Guide - For Claude

This document helps you (Claude) quickly understand the GAO-Dev project, its structure, current status, and best practices.

---

## What is GAO-Dev?

**GAO-Dev** (Generative Autonomous Organisation - Development Team) is an autonomous AI development orchestration system that manages the complete software development lifecycle using specialized Claude agents.

**Parent Project**: GAO (Generative Autonomous Organisation)
**This Project**: Development team within GAO
**Future**: gao-ops (Operations), gao-research (Research), etc.

---

## Core Principles

1. **Workflow-Driven Development**: All work follows defined workflows
2. **Agent Specialization**: 7 specialized agents with specific responsibilities
3. **Documentation First**: All artifacts created in correct folders using templates
4. **Autonomous Execution**: Agents work autonomously to build complete applications
5. **Quality Focus**: Comprehensive testing, type safety, clean architecture
6. **Observability**: Full visibility into agent activities and metrics

---

## The 7 Specialized Agents

### 1. Mary - Business Analyst
**Role**: Analysis, research, requirements gathering
**Tools**: Read, Write, Grep, Glob, workflows, research tools
**Use For**: Business analysis, research, product briefs

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
│   └── CLAUDE.md                  # This file
│
├── docs/                           # Documentation
│   ├── README.md                   # Docs organization guide
│   └── features/                   # Feature development docs
│       └── sandbox-system/         # Current: Sandbox & Benchmarking
│           ├── PRD.md
│           ├── ARCHITECTURE.md
│           ├── epics.md
│           └── stories/
│
├── sandbox/                        # Sandbox WORKSPACE (not docs!)
│   ├── README.md                   # Explains workspace purpose
│   ├── benchmarks/                 # Benchmark configs
│   │   └── todo-baseline.yaml
│   └── projects/                   # Test projects (created by agents)
│
├── gao_dev/                        # Source code
│   ├── agents/                     # Agent persona files
│   │   ├── mary.md, john.md, winston.md
│   │   ├── sally.md, bob.md, amelia.md, murat.md
│   ├── cli/                        # CLI commands
│   │   ├── commands.py             # Main commands
│   │   └── sandbox_commands.py     # Sandbox commands (TBD)
│   ├── core/                       # Core services
│   │   ├── config_loader.py
│   │   ├── workflow_registry.py
│   │   ├── workflow_executor.py
│   │   ├── state_manager.py
│   │   ├── git_manager.py
│   │   └── health_check.py
│   ├── orchestrator/               # Agent orchestration
│   │   ├── orchestrator.py         # Main orchestrator
│   │   └── agent_definitions.py    # Agent configs
│   ├── tools/                      # Custom GAO-Dev tools
│   │   └── gao_tools.py            # MCP tools
│   ├── sandbox/                    # Sandbox system (TBD)
│   │   └── (to be implemented)
│   ├── workflows/                  # Embedded workflows
│   │   ├── 2-plan/prd/
│   │   ├── 4-implementation/create-story/
│   │   └── 4-implementation/dev-story/
│   └── config/
│       └── defaults.yaml
│
├── pyproject.toml                  # Package configuration
├── README.md                       # Main project README
└── SESSION_SUMMARY.md              # Latest session summary
```

---

## Current Status (As of 2025-10-27)

### Completed
✅ Phase 1-5 of Agent SDK Integration
  - Custom tool layer (11 tools)
  - Agent definitions (7 agents)
  - GAODevOrchestrator
  - CLI integration (autonomous commands)
  - Environment setup (uv support)

✅ Sandbox Planning Complete
  - PRD, Architecture, Epics defined
  - Story 1.1 ready for implementation
  - Boilerplate identified (Next.js starter)

### Current Focus
🔄 **Epic 1: Sandbox Infrastructure** (Ready to implement)
  - Story 1.1: Sandbox CLI Command Structure ← **START HERE**

### Next Steps
1. Implement Story 1.1 (Sandbox CLI)
2. Continue Epic 1 implementation
3. Build complete sandbox & benchmarking system

---

## Documentation Standards

### Feature Development Docs
**Location**: `docs/features/<feature-name>/`

**Required Files**:
- `PRD.md` - Product Requirements Document
- `ARCHITECTURE.md` - Technical architecture
- `epics.md` - Epic breakdown
- `PROJECT_BRIEF.md` - Initial vision (optional)
- `stories/epic-N/story-N.M.md` - User stories

**Example**: Sandbox system docs in `docs/features/sandbox-system/`

### Sandbox Workspace
**Location**: `sandbox/`

**Purpose**: Where agents create test projects autonomously

**Structure**:
```
sandbox/
├── benchmarks/          # Benchmark configs
└── projects/            # Test projects (created during runs)
    └── todo-app-001/    # Example autonomous project
        ├── docs/        # Created by agents
        ├── src/         # Created by agents
        └── tests/       # Created by agents
```

**Important**: Do NOT put feature development docs in sandbox!

---

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `feature/<feature-name>` - Feature branches

### Commit Message Format
```
<type>(<scope>): <description>

<body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

**Examples**:
- `feat(sandbox): add sandbox init command`
- `docs(architecture): create sandbox architecture document`
- `refactor(cli): reorganize sandbox commands`

---

## Quality Standards

### Code Quality
- ✅ **DRY Principle**: No code duplication
- ✅ **SOLID Principles**: Single responsibility, Open/closed, etc.
- ✅ **Clean Architecture**: Clear separation of concerns
- ✅ **Type Safety**: Type hints throughout, no `Any` types
- ✅ **Error Handling**: Comprehensive try/catch, clear messages
- ✅ **Logging**: structlog for observability

### Documentation
- ✅ **Docstrings**: All public methods documented
- ✅ **Type Hints**: All function signatures typed
- ✅ **README files**: Each major directory has README
- ✅ **Inline Comments**: Complex logic explained

### Testing
- ✅ **Unit Tests**: 80%+ coverage
- ✅ **Integration Tests**: Key workflows tested
- ✅ **Type Checking**: MyPy passes strict mode

### Code Style
- ✅ **ASCII Only**: No emojis or Unicode (Windows compatibility)
- ✅ **Formatting**: Black, line length 100
- ✅ **Linting**: Ruff for code quality

---

## Execution Best Practices

### 1. Use TodoWrite for Progress Tracking
```python
# Start of task
TodoWrite([
    {"content": "Task 1", "status": "in_progress", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "pending", "activeForm": "Doing task 2"},
])

# After completing task 1
TodoWrite([
    {"content": "Task 1", "status": "completed", "activeForm": "Doing task 1"},
    {"content": "Task 2", "status": "in_progress", "activeForm": "Doing task 2"},
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
- Explain what you're gathering first

### 4. Read Before Write/Edit
- Always use Read tool before Edit or Write
- Understand existing code before modifying
- Preserve indentation and style

---

## Avoid Common Pitfalls

### ❌ Don't Mix Documentation Types
- Feature development docs → `docs/features/`
- Test project outputs → `sandbox/projects/`
- Don't put planning docs in sandbox!

### ❌ Don't Skip Planning
- Read PRD and Architecture before implementing
- Understand the full context
- Follow the defined approach

### ❌ Don't Nest Agents from Claude Code
- Can't spawn GAO-Dev agents from within Claude Code session
- Use standalone mode with API key for benchmarks
- Or generate instructions for manual execution

### ❌ Don't Create Files Without Reading Project Structure
- Understand where files should go
- Follow existing patterns
- Read docs/README.md if unsure

### ❌ Don't Use Emojis
- Windows console compatibility issue
- Use ASCII: `>>`, `[OK]`, `[WARN]`, `[FAIL]`

---

## Getting Started on a Task

1. **Read Current Status**
   - Check `SESSION_SUMMARY.md` for latest progress
   - Check todo list if session interrupted
   - Read relevant feature docs

2. **Understand Context**
   - Read PRD for requirements
   - Read ARCHITECTURE for design
   - Read current story for specifics

3. **Plan Your Work**
   - Create todo list with TodoWrite
   - Identify files you'll need to read/modify
   - Consider dependencies

4. **Execute Incrementally**
   - Work through todos one at a time
   - Mark progress as you go
   - Commit logically sized changes

5. **Validate**
   - Test your changes
   - Check against acceptance criteria
   - Ensure quality standards met

---

## MCP Tools Available

### GAO-Dev Custom Tools
- `mcp__gao_dev__list_workflows` - List workflows
- `mcp__gao_dev__get_workflow` - Get workflow details
- `mcp__gao_dev__execute_workflow` - Execute workflow
- `mcp__gao_dev__get_story_status` - Get story status
- `mcp__gao_dev__set_story_status` - Update story status
- `mcp__gao_dev__ensure_story_directory` - Create story directory
- `mcp__gao_dev__get_sprint_status` - Get sprint status
- `mcp__gao_dev__git_create_branch` - Create git branch
- `mcp__gao_dev__git_commit` - Create git commit
- `mcp__gao_dev__git_merge_branch` - Merge branch
- `mcp__gao_dev__health_check` - Run health check

### Usage
Currently, these tools work in standalone mode only (can't spawn agents from Claude Code).

For development work, use the traditional workflow:
1. Read workflow with `gao-dev list-workflows`
2. Execute workflow with `gao-dev execute <workflow>`
3. Follow workflow instructions manually

---

## Common Commands

```bash
# List available commands
gao-dev --help

# List workflows
gao-dev list-workflows

# List agents
gao-dev list-agents

# Run health check
gao-dev health

# Initialize project
gao-dev init --name "Project Name"

# Autonomous commands (when available)
gao-dev create-prd --name "Project"
gao-dev create-story --epic 1 --story 1
gao-dev implement-story --epic 1 --story 1
```

---

## Key Files to Read When Starting

1. **For Project Overview**:
   - `README.md` - Main project README
   - `SESSION_SUMMARY.md` - Latest session summary
   - `.claude/CLAUDE.md` - This file

2. **For Current Work**:
   - `docs/features/sandbox-system/PRD.md` - Requirements
   - `docs/features/sandbox-system/ARCHITECTURE.md` - Design
   - `docs/features/sandbox-system/epics.md` - Epic breakdown
   - Current story in `docs/features/sandbox-system/stories/`

3. **For Implementation**:
   - Relevant files in `gao_dev/`
   - Existing similar implementations
   - Test files for patterns

---

## Quick Reference

| Need to... | Look at... |
|-----------|-----------|
| Understand project goals | README.md, PRD.md |
| See current progress | SESSION_SUMMARY.md |
| Know what to build | Current story in docs/features/ |
| Understand architecture | ARCHITECTURE.md |
| Find agent definitions | gao_dev/agents/*.md |
| See CLI commands | gao_dev/cli/commands.py |
| Understand workflows | gao_dev/workflows/ |
| Check code patterns | Existing implementations in gao_dev/ |

---

## When in Doubt

1. **Ask the user** - They have context you may not
2. **Read the docs** - Especially PRD and ARCHITECTURE
3. **Follow existing patterns** - Match the codebase style
4. **Use TodoWrite** - Keep user informed of progress
5. **Test incrementally** - Verify as you go

---

## Success Criteria

You'll know you're doing well when:
- ✅ User can see your progress (TodoWrite)
- ✅ Code follows quality standards (DRY, SOLID, typed)
- ✅ Commits have clear messages
- ✅ Documentation updated alongside code
- ✅ Tests passing
- ✅ User is informed and can interrupt/redirect

---

**Remember**: GAO-Dev is about building a system that can autonomously build applications. Everything we do should move us closer to that goal of "simple prompt → production-ready app."

**Good luck! 🚀**
