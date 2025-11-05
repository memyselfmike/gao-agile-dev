# B-MAD Agent-Based Development Guide - For Claude Code

This guide helps Claude Code work effectively using the B-MAD (Business Model Adaptive Development) methodology with specialized AI agents for autonomous software development.

---

## What is B-MAD + Agent-Based Development?

**B-MAD Methodology**: A business-model-driven agile approach that adapts scale and process based on project complexity (Levels 0-4: Chore → Bug Fix → Small Feature → Medium Feature → Greenfield App).

**Agent-Based Development**: Use specialized AI agents (John, Winston, Sally, Bob, Amelia, Murat, Brian) to autonomously handle different aspects of the development lifecycle.

**Result**: High-quality, production-ready software delivered incrementally through autonomous agent collaboration.

---

## Core Principles

1. **Agent Specialization**: Use the right agent for each task (PM, Architect, Designer, Developer, QA, Scrum Master)
2. **Story-Based Development**: Work in small, atomic stories (ONE story at a time)
3. **Atomic Commits**: ONE commit per story, immediately after completion
4. **Documentation-Driven**: PRD → Architecture → Epics → Stories → Implementation
5. **Quality Gates**: TDD, 80%+ coverage, type safety, SOLID principles
6. **Workflow-Driven**: Intelligent workflow selection based on scale and context

---

## The 7 Specialized Agents

### 1. Brian - Workflow Coordinator (NEW!)
**Role**: Intelligent workflow selection and orchestration
**Use For**: Initial project analysis, workflow selection, scale-adaptive routing, multi-workflow sequencing

**When to Use**:
- Starting a new project
- Need to determine appropriate scale level
- Require workflow recommendations
- Need clarification on requirements

**Invoke with Task tool**:
```
Use the Task tool with subagent_type="Plan" to spawn Brian for workflow selection and project analysis.
```

### 2. John - Product Manager
**Role**: PRDs, feature definition, prioritization, requirements
**Tools**: Read, Write, Grep, Glob, workflows, sprint status, research

**Use For**:
- Creating Product Requirements Documents (PRDs)
- Defining features and requirements
- Breaking down features into epics
- Prioritizing work

**Typical Workflow**:
1. Spawn John to analyze requirements
2. John creates comprehensive PRD
3. PRD saved to `docs/features/<feature-name>/PRD.md`

### 3. Winston - Technical Architect
**Role**: System architecture, technical specifications, design decisions
**Tools**: Read, Write, Edit, Grep, Glob, workflows, research

**Use For**:
- Designing system architecture
- Creating technical specifications
- Making technology stack decisions
- Defining component interfaces

**Typical Workflow**:
1. Spawn Winston after PRD complete
2. Winston designs architecture
3. Architecture saved to `docs/features/<feature-name>/ARCHITECTURE.md`

### 4. Sally - UX Designer
**Role**: User experience, wireframes, design specifications
**Tools**: Read, Write, Grep, Glob, workflows, story status, research

**Use For**:
- Designing user interfaces
- Creating user flows
- UX/UI specifications
- Accessibility considerations

### 5. Bob - Scrum Master
**Role**: Story creation and management, sprint coordination, team facilitation
**Tools**: Read, Write, Grep, Glob, workflows, story management, git, TodoWrite

**Use For**:
- Creating story files from epics
- Managing sprint status
- Coordinating between agents
- Tracking progress

**Typical Workflow**:
1. Spawn Bob to create stories from epic
2. Bob creates story files in `docs/features/<feature>/stories/epic-N/story-N.M.md`
3. Bob updates sprint-status.yaml

### 6. Amelia - Software Developer
**Role**: Implementation, code reviews, testing, refactoring
**Tools**: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, workflows, story management, git, TodoWrite, research

**Use For**:
- Implementing features
- Writing tests (TDD)
- Code reviews
- Refactoring
- Bug fixes

**Typical Workflow**:
1. Spawn Amelia to implement story
2. Amelia reads story acceptance criteria
3. Amelia writes tests first (TDD)
4. Amelia implements functionality
5. Amelia creates atomic commit

### 7. Murat - Test Architect
**Role**: Test strategies, quality assurance, test planning
**Tools**: Read, Write, Edit, Grep, Glob, Bash, workflows, story status, git, TodoWrite

**Use For**:
- Creating test strategies
- Defining test plans
- Quality standards
- Test coverage analysis

---

## Project Structure - CRITICAL

### Feature-Based Organization

```
docs/
├── features/
│   ├── <feature-name>/
│   │   ├── PRD.md                   # Product Requirements (John creates)
│   │   ├── ARCHITECTURE.md          # Technical Architecture (Winston creates)
│   │   ├── epics.md                 # Epic breakdown (John + Bob create)
│   │   └── stories/
│   │       ├── epic-1/
│   │       │   ├── story-1.1.md     # Story files (Bob creates)
│   │       │   ├── story-1.2.md
│   │       │   └── ...
│   │       ├── epic-2/
│   │       │   └── ...
│   │       └── ...
│   │
│   ├── <another-feature>/
│   │   └── ...
│   │
├── bmm-workflow-status.md           # Current sprint status (UPDATE THIS!)
└── sprint-status.yaml               # Detailed story tracking
```

### ALWAYS Start Here

**Before ANY work**: Read `docs/bmm-workflow-status.md`
- Shows current epic and story
- Shows what's done and what's next
- Shows overall project status

---

## B-MAD Development Workflow

### Scale Levels (Adaptive Approach)

**Level 0: Chore** (<1 hour)
- Direct execution, no formal planning
- Examples: Fix typo, update docs, small config change

**Level 1: Bug Fix** (1-4 hours)
- Minimal planning, direct fix
- Examples: Fix failing test, resolve small bug

**Level 2: Small Feature** (1-2 weeks, 3-8 stories)
- PRD → Architecture → Epic → Stories → Implementation
- Examples: Add authentication, new UI component

**Level 3: Medium Feature** (1-2 months, 12-40 stories)
- Full B-MAD workflow with analysis phase
- Examples: Complete module, integration system

**Level 4: Greenfield Application** (2-6 months, 40+ stories)
- Comprehensive methodology with discovery
- Examples: New product, complete rewrite

### The B-MAD Phases

**Phase 1: Analysis** (Levels 3-4)
- Product brief
- Market research
- User research
- Problem definition

**Phase 2: Planning**
- PRD (John creates)
- Feature breakdown
- Epic definition
- Success criteria

**Phase 3: Solutioning**
- System architecture (Winston creates)
- Technical specifications
- API design
- Data models

**Phase 4: Implementation**
- Story creation (Bob creates)
- Story development (Amelia implements)
- Testing (Murat validates)
- Deployment

---

## Story-Based Development Workflow

### Creating a New Feature

**Step 1: Create PRD** (Use John)
```
Use the Task tool to spawn John to create a Product Requirements Document.

John should:
1. Read existing documentation for context
2. Analyze requirements
3. Create comprehensive PRD.md
4. Save to docs/features/<feature-name>/PRD.md
```

**Step 2: Create Architecture** (Use Winston)
```
Use the Task tool to spawn Winston to create system architecture.

Winston should:
1. Read the PRD
2. Design system architecture
3. Define component interfaces
4. Create ARCHITECTURE.md
5. Save to docs/features/<feature-name>/ARCHITECTURE.md
```

**Step 3: Create Epic Breakdown** (Use John + Bob)
```
Use the Task tool to spawn John/Bob to break down into epics.

Output:
1. docs/features/<feature-name>/epics.md
2. Defines 2-6 epics with story estimates
3. Success criteria for each epic
```

**Step 4: Create Stories** (Use Bob)
```
Use the Task tool to spawn Bob to create story files.

Bob creates:
- docs/features/<feature>/stories/epic-N/story-N.M.md (for each story)
- Updates sprint-status.yaml

Each story includes:
- User story
- Acceptance criteria
- Technical details
- Dependencies
- Testing strategy
```

**Step 5: Implement Stories** (Use Amelia)
```
Use the Task tool to spawn Amelia to implement ONE story at a time.

Amelia follows TDD:
1. Read story file completely
2. Write failing tests first
3. Implement to pass tests
4. Refactor
5. Create atomic commit
6. Update story status

ONE STORY = ONE COMMIT (atomic)
```

---

## Using the Task Tool for Agents

### Task Tool Basics

The Task tool spawns specialized agents autonomously:

```python
# Example: Spawn John to create PRD
Task(
    subagent_type="general-purpose",  # or "Explore" for codebase exploration
    description="Create PRD for user authentication",
    prompt="""
    Use the John agent to create a Product Requirements Document for 'User Authentication Feature'.

    John should:
    1. Use the 'prd' workflow to understand structure
    2. Research authentication best practices
    3. Create comprehensive PRD.md
    4. Save to docs/features/user-authentication/PRD.md

    The PRD must include:
    - Executive summary
    - Problem statement
    - Requirements (functional & non-functional)
    - Success criteria
    - Risks and dependencies
    """
)
```

### When to Use Task Tool vs Direct Work

**Use Task Tool When**:
- ✅ Need specialized agent (John, Winston, Sally, Bob, Amelia, Murat)
- ✅ Complex multi-step work (PRD, Architecture, Story implementation)
- ✅ Require autonomous execution
- ✅ Need agent-specific tools and workflows

**Work Directly When**:
- ❌ Simple file reads or edits
- ❌ Quick status updates
- ❌ Trivial changes (typos, formatting)
- ❌ Already working on a story yourself

---

## Git Workflow - ATOMIC COMMITS

### Branch Strategy

```bash
main                                    # Production-ready
feature/epic-<N>-<name>                # Epic-level branches
feature/story-<N>.<M>-<name>           # Story-level (if needed)
```

### Atomic Commits - ONE STORY = ONE COMMIT

**CRITICAL RULE**: Each story gets exactly ONE commit, created immediately after story completion.

**Commit Message Format**:
```
<type>(<scope>): implement Story N.M - Brief Description

Detailed explanation of what changed and why.

Acceptance Criteria Met:
- [x] Criterion 1
- [x] Criterion 2
- [x] Criterion 3

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**:
- `feat`: New feature (most stories)
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Test additions
- `chore`: Maintenance

**Example**:
```bash
git add -A
git commit -m "feat(auth): implement Story 3.1 - JWT Token Validation

Implement JWT token validation middleware with comprehensive tests.
Validates token signature, expiration, and required claims.
Returns 401 for invalid/expired tokens.

Acceptance Criteria Met:
- [x] Token signature validation
- [x] Expiration checking
- [x] Required claims validation
- [x] Error handling for invalid tokens
- [x] Unit tests with 95% coverage

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Quality Standards - NON-NEGOTIABLE

### Code Quality (SOLID + DRY)

**SOLID Principles**:
- ✅ Single Responsibility
- ✅ Open/Closed
- ✅ Liskov Substitution
- ✅ Interface Segregation
- ✅ Dependency Inversion

**DRY**: No code duplication
**Clean Code**: Functions <50 lines, classes <200 lines
**Type Safety**: Type hints on ALL functions, no `Any` types

### Testing (TDD Required)

**Process**:
1. **RED**: Write failing test
2. **GREEN**: Write code to pass test
3. **REFACTOR**: Clean up while tests pass

**Requirements**:
- ✅ 80%+ test coverage (measured)
- ✅ Unit tests for all business logic
- ✅ Integration tests for key workflows
- ✅ All tests pass before commit

### Code Standards

**Type Checking**: MyPy strict mode must pass
**Linting**: No Ruff errors
**Formatting**: Black (line length 100)
**Logging**: Structured logging (structlog), no print statements

---

## Sprint Tracking

### bmm-workflow-status.md - ALWAYS READ FIRST

This file shows:
- Current phase and scale level
- Current epic and status
- What's done and what's next
- Overall project progress

**Update After**:
- Epic completion
- Major milestone
- Phase transition

### sprint-status.yaml - Story Tracking

Tracks all stories with:
```yaml
epics:
  - epic_number: 1
    name: "Feature Name"
    status: in_progress  # or completed
    stories:
      - number: 1
        status: done  # or in_progress, blocked, not_started
        name: "Story Name"
        file: "docs/features/.../story-1.1.md"
```

**Update After Each Story**:
```yaml
- number: 1
  status: done  # ← Update this
  name: "Story Name"
```

---

## Story Implementation Checklist

When implementing a story (as Amelia or directly):

### Before Starting
- [ ] Read story file completely
- [ ] Understand all acceptance criteria
- [ ] Check dependencies (blocked stories)
- [ ] Read related PRD and Architecture docs
- [ ] Create TodoWrite plan

### During Implementation (TDD)
- [ ] Write failing tests first (RED)
- [ ] Implement minimum code to pass (GREEN)
- [ ] Refactor while keeping tests green (REFACTOR)
- [ ] Follow SOLID principles
- [ ] No code duplication (DRY)
- [ ] Type hints on all functions
- [ ] Comprehensive error handling
- [ ] Structured logging (no print())

### Before Committing
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] MyPy passes (strict mode)
- [ ] Ruff passes (no linting errors)
- [ ] Code reviewed (self-review checklist)
- [ ] Documentation updated (docstrings, README)

### Commit
- [ ] Create atomic commit (ONE story = ONE commit)
- [ ] Follow conventional commit format
- [ ] Include acceptance criteria checklist in message
- [ ] Include "🤖 Generated with Claude Code" footer

### After Commit
- [ ] Update story status in sprint-status.yaml
- [ ] Update bmm-workflow-status.md (if epic/phase complete)
- [ ] Clear TodoWrite
- [ ] Inform user of completion

---

## Common Workflows (Use Slash Commands)

### /create-prd
Creates PRD using John agent

### /create-architecture
Creates architecture using Winston agent

### /create-epic
Breaks down feature into epics using John/Bob

### /create-stories
Creates story files using Bob agent

### /implement-story
Implements ONE story using Amelia agent (TDD approach)

### /commit
Creates atomic commit following standards

### /status
Shows current sprint status and next story

---

## Example: Complete Feature Development

```bash
# 1. Check current status
Read docs/bmm-workflow-status.md

# 2. Create PRD (spawn John)
/create-prd "User Authentication Feature"
# → Creates docs/features/user-authentication/PRD.md

# 3. Create Architecture (spawn Winston)
/create-architecture "User Authentication Feature"
# → Creates docs/features/user-authentication/ARCHITECTURE.md

# 4. Create Epic Breakdown (spawn John/Bob)
/create-epic "User Authentication"
# → Creates docs/features/user-authentication/epics.md

# 5. Create Story Files (spawn Bob)
/create-stories --epic 1
# → Creates docs/features/user-authentication/stories/epic-1/story-1.*.md
# → Updates sprint-status.yaml

# 6. Implement Story 1.1 (spawn Amelia)
/implement-story --epic 1 --story 1
# → Amelia reads story-1.1.md
# → Amelia writes tests (TDD)
# → Amelia implements feature
# → Amelia creates atomic commit
# → Updates sprint-status.yaml

# 7. Continue with remaining stories
/implement-story --epic 1 --story 2
/implement-story --epic 1 --story 3
# ... until epic complete

# 8. Update status
Edit bmm-workflow-status.md (mark epic complete)
```

---

## Communication & Visibility

### Keep User Informed

**Before Acting**:
"I'm going to spawn John to create the PRD for the authentication feature."

**During Work** (use TodoWrite):
```python
TodoWrite([
    {"content": "Spawn John to create PRD", "status": "in_progress", "activeForm": "Spawning John for PRD creation"},
    {"content": "Review PRD for completeness", "status": "pending", "activeForm": "Reviewing PRD"},
    {"content": "Update bmm-workflow-status.md", "status": "pending", "activeForm": "Updating workflow status"}
])
```

**After Completion**:
"John has created a comprehensive PRD at docs/features/user-authentication/PRD.md. The PRD includes 15 functional requirements and 8 non-functional requirements. Ready to proceed with architecture design."

### Allow User to Redirect

- ✅ Give user chance to review before proceeding
- ✅ Ask for clarification when uncertain
- ✅ Offer options when multiple approaches exist
- ❌ Don't make major decisions silently

---

## Success Criteria

You're doing well when:

- ✅ Always read bmm-workflow-status.md first
- ✅ Use correct agent for each task (Task tool)
- ✅ ONE story implemented at a time
- ✅ ONE atomic commit per story
- ✅ All tests pass (80%+ coverage)
- ✅ Type checking passes
- ✅ sprint-status.yaml kept up to date
- ✅ User can see progress (TodoWrite)
- ✅ Documentation created alongside code

---

## Troubleshooting

### "Where do I start?"
→ Read `docs/bmm-workflow-status.md` - it tells you current epic and next story

### "Should I implement this myself or spawn an agent?"
→ Complex work (stories, PRDs, architecture) = Spawn agent
→ Simple edits or status updates = Do directly

### "How do I track multiple stories?"
→ ONE story at a time. Complete current story (commit) before starting next.

### "Tests are failing"
→ Don't commit. Fix tests first. TDD = tests pass before commit.

### "Should I batch multiple stories into one commit?"
→ NO. ONE story = ONE commit. Atomic commits are non-negotiable.

---

## Quick Reference Checklist

### Starting New Feature
- [ ] Read bmm-workflow-status.md
- [ ] Spawn John for PRD
- [ ] Spawn Winston for Architecture
- [ ] Spawn Bob for Epic + Stories
- [ ] Update sprint-status.yaml

### Implementing Story
- [ ] Read story file completely
- [ ] Use TodoWrite to plan
- [ ] Write tests first (TDD)
- [ ] Implement to pass tests
- [ ] Ensure 80%+ coverage
- [ ] Create atomic commit
- [ ] Update sprint-status.yaml

### Before Every Commit
- [ ] All tests pass
- [ ] Coverage >80%
- [ ] MyPy passes
- [ ] Ruff passes
- [ ] One story only
- [ ] Conventional commit message

---

## Resources

### Key Files to Reference
- `CLAUDE.md` (project root) - Project-specific information
- `docs/bmm-workflow-status.md` - Current status
- `docs/sprint-status.yaml` - Story tracking
- `docs/features/<feature>/PRD.md` - Requirements
- `docs/features/<feature>/ARCHITECTURE.md` - Technical design
- `docs/features/<feature>/stories/epic-N/story-N.M.md` - Story details

### Commands Available
See `.claude/commands/` directory for slash commands

---

**Remember**: B-MAD + Agent-Based Development combines adaptive methodology with autonomous agent collaboration to deliver high-quality software incrementally. Quality is non-negotiable. Atomic commits are sacred. ONE story at a time.
