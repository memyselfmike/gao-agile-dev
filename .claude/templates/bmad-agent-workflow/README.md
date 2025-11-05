# B-MAD Agent-Based Workflow Template

This template provides a comprehensive framework for autonomous software development using the B-MAD (Business Model Adaptive Development) methodology with specialized AI agents.

---

## What's Included

### 📘 CLAUDE.md - Complete Methodology Guide
Comprehensive guide covering:
- **B-MAD Methodology**: Adaptive development approach (Scale Levels 0-4)
- **The 7 Specialized Agents**: John, Winston, Sally, Bob, Amelia, Murat, Brian
- **Project Structure**: docs/features/ organization with PRD, Architecture, Epics, Stories
- **Agent-Based Development**: When and how to use Task tool to spawn agents
- **Story-Based Workflow**: ONE story at a time, atomic commits
- **Quality Standards**: TDD, SOLID, 80%+ coverage, type safety
- **Sprint Tracking**: bmm-workflow-status.md and sprint-status.yaml
- **Git Workflow**: Atomic commits (ONE story = ONE commit)

### 🛠️ 7 Slash Commands
Ready-to-use commands for agent-based workflows:

1. **/create-prd** - Spawn John to create Product Requirements Document
2. **/create-architecture** - Spawn Winston to create system architecture
3. **/create-epic** - Spawn John/Bob to break down into epics and stories
4. **/create-stories** - Spawn Bob to create detailed story files
5. **/implement-story** - Spawn Amelia to implement ONE story (TDD approach)
6. **/status** - Check current sprint status and next story
7. **/commit** - Create atomic commit following B-MAD standards

---

## Quick Start

### For Your Teammates

**Option 1: Copy to Project**
```bash
# Navigate to their project
cd /path/to/their/project

# Copy the template
cp -r /path/to/bmad-agent-workflow .claude/
```

**Option 2: From Zip**
```bash
# Create shareable zip
cd .claude/templates
zip -r bmad-agent-workflow.zip bmad-agent-workflow/

# They extract it
unzip bmad-agent-workflow.zip -d /their/project/.claude/
```

**Option 3: Git Repository**
```bash
# Create standards repo
git init claude-bmad-standards
cp -r .claude/templates/bmad-agent-workflow/* claude-bmad-standards/

# Teammates clone
cd /their/project/.claude
git clone <your-repo-url> bmad-agent-workflow
```

---

## What Makes This Powerful

### 1. B-MAD Methodology
**Adaptive approach** that scales from chores to greenfield apps:
- **Level 0**: Chore (<1 hour) - Direct execution
- **Level 1**: Bug Fix (1-4 hours) - Minimal planning
- **Level 2**: Small Feature (1-2 weeks) - PRD → Architecture → Stories
- **Level 3**: Medium Feature (1-2 months) - Full B-MAD workflow
- **Level 4**: Greenfield App (2-6 months) - Comprehensive methodology

### 2. Specialized Agents
**The right agent for each task**:
- **Brian**: Workflow selection, scale analysis
- **John**: Product requirements, feature definition
- **Winston**: System architecture, technical design
- **Sally**: UX design, user flows
- **Bob**: Story management, sprint coordination
- **Amelia**: Implementation, testing, refactoring
- **Murat**: Test strategies, quality assurance

### 3. Documentation-Driven
**Clear structure, easy tracking**:
```
docs/features/<feature-name>/
  ├── PRD.md              # Requirements (John creates)
  ├── ARCHITECTURE.md     # Design (Winston creates)
  ├── epics.md            # Epic breakdown (Bob creates)
  └── stories/
      └── epic-N/
          └── story-N.M.md  # Story details (Bob creates)
```

### 4. Story-Based Development
**ONE story at a time, ONE atomic commit**:
1. Read story file (acceptance criteria)
2. Write tests first (TDD - RED)
3. Implement to pass tests (GREEN)
4. Refactor (REFACTOR)
5. Create atomic commit
6. Update sprint tracking
7. Move to next story

### 5. Quality Gates (Non-Negotiable)
- ✅ TDD: Tests written FIRST
- ✅ 80%+ test coverage (measured)
- ✅ Type hints on ALL functions
- ✅ No `Any` types
- ✅ SOLID principles
- ✅ DRY (no duplication)
- ✅ MyPy strict mode passes
- ✅ Linting passes (Ruff)

---

## Complete Workflow Example

```bash
# 1. Check current status
/status
# → Shows current epic, completed stories, next action

# 2. Start new feature - Create PRD
/create-prd "User Authentication"
# → Spawns John agent
# → Creates docs/features/user-authentication/PRD.md

# 3. Create Architecture
/create-architecture "User Authentication"
# → Spawns Winston agent
# → Creates docs/features/user-authentication/ARCHITECTURE.md

# 4. Break down into Epics
/create-epic "User Authentication"
# → Spawns John/Bob
# → Creates docs/features/user-authentication/epics.md
# → Defines 4 epics with 22 stories

# 5. Create Story Files for Epic 1
/create-stories --epic 1
# → Spawns Bob agent
# → Creates docs/features/user-authentication/stories/epic-1/story-1.*.md
# → Updates sprint-status.yaml

# 6. Implement Story 1.1
/implement-story --epic 1 --story 1
# → Spawns Amelia agent
# → Amelia reads story-1.1.md
# → Amelia writes tests first (TDD)
# → Amelia implements feature
# → Amelia creates atomic commit
# → Updates sprint-status.yaml (status: done)

# 7. Continue with remaining stories
/implement-story --epic 1 --story 2
/implement-story --epic 1 --story 3
# ... ONE story at a time

# 8. Check progress
/status
# → Shows Epic 1: 3/5 complete (60%)
```

---

## Key Concepts

### Task Tool for Agent Spawning
Use the Task tool to spawn specialized agents:
```python
Task(
    subagent_type="general-purpose",
    description="Create PRD",
    prompt="Use John agent to create PRD for feature X..."
)
```

### Atomic Commits
**ONE story = ONE commit** (sacred rule):
```bash
git commit -m "feat(auth): implement Story 1.1 - User Registration

Implement registration with validation...

Acceptance Criteria Met:
- [x] Form validation
- [x] Email verification
- [x] Password strength check

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Sprint Tracking
**Always read first**: `docs/bmm-workflow-status.md`
- Shows current epic
- Shows progress
- Shows what's next

**Update after each story**: `docs/sprint-status.yaml`
```yaml
stories:
  - number: 1
    status: done  # ← Update this
```

---

## File Structure

```
.claude/bmad-agent-workflow/
├── README.md              # This file
├── INSTALLATION.md        # Setup instructions
├── CLAUDE.md              # Complete methodology guide (20KB)
└── commands/              # Slash commands
    ├── create-prd.md
    ├── create-architecture.md
    ├── create-epic.md
    ├── create-stories.md
    ├── implement-story.md
    ├── status.md
    └── commit.md
```

---

## Benefits for Teams

### Consistency
Everyone follows the same agent-based workflow, making collaboration seamless.

### Quality
Non-negotiable quality gates (TDD, 80% coverage, type safety) ensure production-ready code.

### Visibility
Sprint tracking (bmm-workflow-status.md, sprint-status.yaml) provides full transparency.

### Autonomy
Specialized agents handle complex tasks autonomously, freeing humans for high-level decisions.

### Documentation
Documentation-driven approach ensures requirements, architecture, and stories are always up-to-date.

### Velocity
Clear workflow and agent specialization reduce decision fatigue and context switching.

---

## Success Metrics

You'll know it's working when:

- ✅ Always start by reading bmm-workflow-status.md
- ✅ Use Task tool to spawn appropriate agent
- ✅ ONE story implemented at a time
- ✅ ONE atomic commit per story
- ✅ All tests pass (80%+ coverage)
- ✅ sprint-status.yaml always up to date
- ✅ Documentation created alongside code
- ✅ Features delivered incrementally
- ✅ Team velocity is consistent and predictable

---

## Customization

### For Your Project

1. **Edit CLAUDE.md**:
   - Add project-specific context
   - Customize quality thresholds
   - Add domain-specific patterns

2. **Edit slash commands**:
   - Adjust prompts for your agents
   - Add project-specific workflows
   - Include team conventions

3. **Add new commands**:
   - Create new .md files in commands/
   - Follow existing format
   - Use Task tool for agent spawning

---

## Real-World Example

This template is based on the **GAO-Dev** project, which uses this exact methodology:

**Stats**:
- 11 epics completed
- 90+ stories implemented
- 400+ tests (93%+ coverage)
- Atomic commits per story
- Documentation-driven throughout
- Specialized agents for all work

**Result**: Production-ready autonomous development orchestration system delivered incrementally with high quality.

---

## Next Steps

1. **Read CLAUDE.md** (15 minutes) - Understand the methodology
2. **Try /status command** - See current project state
3. **Try /create-prd** - Create a PRD for a feature
4. **Follow the workflow** - PRD → Architecture → Epics → Stories → Implementation
5. **Share with team** - Help teammates achieve the same excellence

---

## Support

### Questions?
- **Methodology**: Read CLAUDE.md thoroughly
- **Agents**: See "The 7 Specialized Agents" section
- **Workflow**: Check slash command files in commands/
- **Examples**: See workflow examples in CLAUDE.md

### Common Issues
- **"Where do I start?"** → Read bmm-workflow-status.md first
- **"Which agent to use?"** → See "The 7 Specialized Agents" section
- **"How to track stories?"** → Update sprint-status.yaml after each story
- **"Tests failing?"** → Don't commit. Fix tests first (TDD)

---

**Welcome to B-MAD Agent-Based Development!**

This methodology enables autonomous, high-quality software delivery through intelligent agent collaboration and adaptive process scaling.

**Quality + Autonomy + Velocity = B-MAD Success**
