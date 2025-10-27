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

## BMAD Method - Our Development Process

**IMPORTANT**: GAO-Dev itself is being developed using the **BMAD Method** (Business, Market, Architecture, Development).

### What is BMAD Method?

BMAD Method is a proven agile development framework with specialized agents and workflows. We use it to build GAO-Dev before GAO-Dev can build other projects.

### BMAD Four-Phase Methodology

```
Phase 1: Analysis (Optional) → Research, brainstorming, product brief
Phase 2: Planning (Required) → PRD, epics, stories
Phase 3: Solutioning (Level 3-4) → Architecture, technical specs
Phase 4: Implementation (Current) → Story development, reviews, retrospectives
```

### Key BMAD Files

**Always Read These First**:
1. **`docs/bmm-workflow-status.md`** - Current phase, epic, story status
2. **`docs/sprint-status.yaml`** - Sprint progress and story tracking
3. **`bmad/bmm/workflows/README.md`** - Complete workflow guide

### BMAD Workflows Location

All BMAD workflows are in `bmad/bmm/workflows/`:
- `1-analysis/` - Research and discovery workflows
- `2-plan-workflows/` - PRD, GDD, tech-spec workflows
- `3-solutioning/` - Architecture workflows
- `4-implementation/` - Story creation, dev-story, reviews

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
├── bmad/                           # BMAD Method (our dev process)
│   ├── bmm/                        # BMAD Method Module
│   │   ├── config.yaml             # BMAD configuration
│   │   ├── workflows/              # All BMAD workflows
│   │   │   ├── 1-analysis/
│   │   │   ├── 2-plan-workflows/
│   │   │   ├── 3-solutioning/
│   │   │   └── 4-implementation/
│   │   └── agents/                 # BMAD agent definitions
│   └── core/                       # BMAD core files
│
├── docs/                           # Documentation
│   ├── README.md                   # Docs organization guide
│   ├── bmm-workflow-status.md      # BMAD workflow status (CHECK FIRST!)
│   ├── sprint-status.yaml          # Sprint and story tracking
│   └── features/                   # Feature development docs
│       └── sandbox-system/         # Current: Sandbox & Benchmarking
│           ├── PRD.md
│           ├── ARCHITECTURE.md
│           ├── epics.md
│           └── stories/
│               ├── epic-1/         # Complete
│               └── epic-2/         # Ready to implement
│
├── sandbox/                        # Sandbox WORKSPACE (not docs!)
│   ├── README.md                   # Explains workspace purpose
│   ├── benchmarks/                 # Benchmark configs
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

### BMAD Workflow Status
**Phase**: 4 - Implementation
**Scale Level**: 3 (12-40 stories, 2-5 epics)
**Current Epic**: Epic 2 - Boilerplate Integration
**Status**: Ready to begin Epic 2 implementation

### Completed Work
✅ **Epic 1: Sandbox Infrastructure** (Stories 1.1-1.6)
  - Sandbox CLI command structure
  - SandboxManager implementation
  - Project state management
  - init, clean, list, run commands
  - All tests passing

✅ **BMAD Method Installed**
  - BMAD v6-alpha configured for GAO-Dev
  - Workflow status tracking initialized
  - Sprint status file created

✅ **Epic 2 Stories Created** (Stories 2.1-2.5)
  - All 5 stories documented and ready
  - 21 story points total

### Current Focus
🔄 **Epic 2: Boilerplate Integration** (Ready to implement)
  - Story 2.1: Git Repository Cloning ← **START HERE**
  - Story 2.2: Template Variable Detection
  - Story 2.3: Variable Substitution Engine
  - Story 2.4: Dependency Installation
  - Story 2.5: Boilerplate Validation

### Next Steps
1. **Check BMAD workflow status** (`docs/bmm-workflow-status.md`)
2. **Implement Story 2.1** using BMAD dev-story workflow
3. Continue through Epic 2 stories sequentially
4. Move to Epic 3 (Metrics Collection)

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

**IMPORTANT**: Always use feature branches and atomic commits!

**Branch Naming**:
- `main` - Production-ready code (protected)
- `feature/epic-<N>-<epic-name>` - Epic-level feature branches
- `feature/story-<N>.<M>-<story-name>` - Story-level branches (optional, for complex stories)

**Workflow Process**:
1. **Before Starting Work**: Always create a feature branch
   ```bash
   git checkout main
   git pull origin main  # ALWAYS pull latest first!
   git checkout -b feature/epic-3-metrics-collection
   ```

2. **During Development**: Commit atomically after each story
   ```bash
   # After completing Story 3.1
   git add -A
   git commit -m "feat(metrics): implement Story 3.1 - Metrics Data Models"

   # Immediately after Story 3.2
   git add -A
   git commit -m "feat(metrics): implement Story 3.2 - SQLite Database Schema"
   ```

3. **After Epic Complete**: Merge to main and push
   ```bash
   git checkout main
   git pull origin main  # Pull again before merge!
   git merge feature/epic-3-metrics-collection
   git push origin main
   git branch -d feature/epic-3-metrics-collection
   ```

### Atomic Commits - REQUIRED

**One Commit Per Story**:
- ✅ Each story gets exactly ONE commit
- ✅ Commit immediately after story completion
- ✅ Never batch multiple stories into one commit
- ✅ Never leave uncommitted work at end of session

**Why Atomic Commits**:
- Easy to track progress
- Clean git history
- Easy to revert specific stories if needed
- Clear mapping: 1 story = 1 commit
- Better collaboration and code review

**Atomic Commit Checklist**:
- [ ] All story acceptance criteria met
- [ ] All tests passing for this story
- [ ] Story documentation updated (status: Done)
- [ ] Clean commit message following format
- [ ] Commit pushed to feature branch (or ready to push)

### Commit Message Format

```
<type>(<scope>): <description>

<optional body with details>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

**Examples**:
- `feat(metrics): implement Story 3.1 - Metrics Data Models`
- `feat(sandbox): implement Story 2.3 - Variable Substitution Engine`
- `docs(epic-3): update sprint status for Epic 3 completion`
- `fix(metrics): correct foreign key constraints in database schema`
- `refactor(cli): reorganize sandbox commands`

### Git Best Practices

**Always Pull Before Starting**:
```bash
git checkout main
git pull origin main  # Get latest changes
git checkout -b feature/epic-N-name
```

**Commit After Each Story** (Atomic):
```bash
# Story complete? Commit immediately!
git add -A
git commit -m "feat(scope): implement Story N.M - Story Name"
```

**Push Regularly**:
```bash
# After each story or at end of session
git push origin feature/epic-N-name
```

**Clean Merges**:
```bash
# Before merging to main
git checkout main
git pull origin main  # Critical: pull latest!
git merge feature/epic-N-name --no-ff  # Preserve branch history
git push origin main
```

**Never**:
- ❌ Don't commit to main directly
- ❌ Don't batch multiple stories into one commit
- ❌ Don't leave work uncommitted
- ❌ Don't forget to pull before merge
- ❌ Don't push broken tests to shared branches

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

**IMPORTANT**: Always follow the BMAD Method workflow!

### 1. Check BMAD Workflow Status (REQUIRED)

**Read these files FIRST**:
```bash
1. docs/bmm-workflow-status.md    # Current phase, epic, story
2. docs/sprint-status.yaml         # Story status and progress
3. Current story file              # Detailed requirements
```

### 2. Understand Context

**For Current Epic/Story**:
- Read the current story file (e.g., `docs/features/sandbox-system/stories/epic-2/story-2.1.md`)
- Check acceptance criteria and technical details
- Review dependencies on other stories

**For Overall Feature**:
- Read PRD (`docs/features/sandbox-system/PRD.md`)
- Read ARCHITECTURE (`docs/features/sandbox-system/ARCHITECTURE.md`)
- Read epics breakdown (`docs/features/sandbox-system/epics.md`)

**For BMAD Process**:
- Read BMAD workflows guide (`bmad/bmm/workflows/README.md`)
- Understand which phase you're in
- Know what comes next

### 3. Create Feature Branch

**ALWAYS create a feature branch before starting work**:

```bash
# For Epic-level work
git checkout main
git pull origin main  # Always pull first!
git checkout -b feature/epic-N-epic-name

# For Story-level work (if needed)
git checkout -b feature/story-N.M-story-name
```

### 4. Plan Your Work

- Create todo list with TodoWrite
- Break story into implementation steps
- Identify files to read/modify
- Consider testing requirements
- Plan atomic commit for this story

### 5. Implement Using BMAD Workflow

**For Story Implementation**:
1. Follow story acceptance criteria
2. Write tests first (TDD approach)
3. Implement functionality
4. Run tests and validate
5. Update documentation

**BMAD dev-story Workflow** (optional but recommended):
- Creates feature branch
- Provides implementation guidance
- Handles git operations
- Ensures quality standards

### 6. Validate & Complete

- ✅ All acceptance criteria met
- ✅ Tests passing (>80% coverage)
- ✅ Type hints complete
- ✅ Documentation updated
- ✅ Code reviewed (quality standards)
- ✅ Story file updated to "Done" status

### 7. Commit Atomically (REQUIRED)

**Immediately after completing each story**:

```bash
# Add all changes
git add -A

# Create atomic commit for this story
git commit -m "feat(scope): implement Story N.M - Story Name

<detailed description of what was implemented>

Test Results: X/X tests passed, Y% coverage

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to feature branch
git push origin feature/epic-N-name
```

**Commit Checklist**:
- [ ] One commit per story (atomic)
- [ ] Commit message follows format
- [ ] All tests passing
- [ ] Story status updated to "Done"
- [ ] Committed immediately after story completion

### 8. Update BMAD Status

After completing story:
- Update story status in `docs/sprint-status.yaml`
- Update `docs/bmm-workflow-status.md` with progress
- Commit status updates (separate commit is OK)

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

### Priority 1: BMAD Workflow Status (ALWAYS READ FIRST!)

1. **`docs/bmm-workflow-status.md`** - Current phase, epic, story, next actions
2. **`docs/sprint-status.yaml`** - All stories and their status
3. **Current story file** - The specific story you'll be working on

### Priority 2: Feature Context

1. **`docs/features/sandbox-system/PRD.md`** - Requirements and success criteria
2. **`docs/features/sandbox-system/ARCHITECTURE.md`** - System design
3. **`docs/features/sandbox-system/epics.md`** - Epic breakdown and timeline

### Priority 3: BMAD Method Understanding

1. **`bmad/bmm/workflows/README.md`** - Complete BMAD workflow guide
2. **`bmad/bmm/config.yaml`** - BMAD configuration for this project
3. **`bmad/bmm/workflows/4-implementation/`** - Implementation workflows

### Priority 4: Implementation Reference

1. **Existing implementations in `gao_dev/`** - Code patterns and style
2. **Test files** - Testing patterns and structure
3. **Similar completed stories** - Reference implementations

### Priority 5: General Context

1. **`README.md`** - Main project overview
2. **`.claude/CLAUDE.md`** - This file
3. **`SESSION_SUMMARY.md`** - Latest session notes (if exists)

---

## Quick Reference

| Need to... | Look at... |
|-----------|-----------|
| **Check what to do next** | **docs/bmm-workflow-status.md** ← START HERE! |
| See current story status | docs/sprint-status.yaml |
| Understand BMAD workflows | bmad/bmm/workflows/README.md |
| Know what to build | Current story in docs/features/sandbox-system/stories/ |
| Understand project goals | docs/features/sandbox-system/PRD.md |
| Understand architecture | docs/features/sandbox-system/ARCHITECTURE.md |
| See epic breakdown | docs/features/sandbox-system/epics.md |
| Find GAO-Dev agents | gao_dev/agents/*.md (these are different from BMAD!) |
| Find BMAD agents | bmad/bmm/agents/*.agent.yaml |
| See CLI commands | gao_dev/cli/commands.py |
| Check code patterns | Existing implementations in gao_dev/ |

---

## When in Doubt

1. **Check BMAD workflow status** - `docs/bmm-workflow-status.md` always knows where you are
2. **Ask the user** - They have context you may not have
3. **Read the docs** - Especially PRD, ARCHITECTURE, and current story
4. **Follow existing patterns** - Match the codebase style
5. **Use TodoWrite** - Keep user informed of progress
6. **Test incrementally** - Verify as you go
7. **Follow BMAD workflows** - They guide you through the process

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

---

## Important Notes

### GAO-Dev vs BMAD Method

**GAO-Dev**: The system we're building - will autonomously orchestrate development
**BMAD Method**: The process we're using to BUILD GAO-Dev itself

Once GAO-Dev is complete, it will use its own agents and workflows. But until then, we use BMAD Method to develop GAO-Dev with proper agile practices.

### Two Sets of Agents

**BMAD Agents** (in `bmad/bmm/agents/`):
- analyst, pm, architect, dev, sm, ux-designer, tea
- Used for developing GAO-Dev itself
- Defined in BMAD Method workflow files

**GAO-Dev Agents** (in `gao_dev/agents/`):
- Mary, John, Winston, Sally, Bob, Amelia, Murat
- Will be used BY GAO-Dev for autonomous development
- The product we're building

### Workflow Priority

1. **Always use BMAD workflows** for developing GAO-Dev
2. **Check workflow status first** before starting any work
3. **Follow story acceptance criteria** exactly
4. **Update status files** after completing work
5. **Commit with proper messages** following BMAD conventions

---

**Remember**:
- **For GAO-Dev development**: Use BMAD Method workflows
- **For GAO-Dev goal**: Build autonomous development orchestration
- **End goal**: "simple prompt → production-ready app"

**Start every session by reading `docs/bmm-workflow-status.md`!**
