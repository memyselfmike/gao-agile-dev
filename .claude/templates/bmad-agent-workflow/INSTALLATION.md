# Installation Guide - B-MAD Agent-Based Workflow

## Quick Installation for Teammates

### Option 1: Direct Copy (Recommended)

```bash
# Navigate to your project
cd /path/to/your/project

# Create .claude folder if it doesn't exist
mkdir -p .claude

# Copy the template
cp -r /path/to/bmad-agent-workflow .claude/
```

### Option 2: From Zip File

```bash
# Navigate to your project
cd /path/to/your/project

# Create .claude folder if it doesn't exist
mkdir -p .claude

# Extract the zip
unzip bmad-agent-workflow.zip -d .claude/
```

### Option 3: From Git Repository

```bash
# Navigate to your project
cd /path/to/your/project

# Create .claude folder if it doesn't exist
mkdir -p .claude

# Clone the standards repo
cd .claude
git clone https://github.com/yourorg/bmad-standards bmad-agent-workflow
```

---

## Verify Installation

Check that files are in place:

```bash
ls .claude/bmad-agent-workflow/
# Should show: CLAUDE.md, README.md, INSTALLATION.md, commands/

ls .claude/bmad-agent-workflow/commands/
# Should show: create-prd.md, create-architecture.md, create-epic.md,
#             create-stories.md, implement-story.md, status.md, commit.md
```

---

## Set Up Your Project

### Step 1: Create docs/ Structure

```bash
mkdir -p docs/features
touch docs/bmm-workflow-status.md
touch docs/sprint-status.yaml
```

### Step 2: Initialize bmm-workflow-status.md

```markdown
---
last_updated: 2025-11-05
phase: 4-implementation
scale_level: 2
project_type: software
project_name: Your Project Name
---

# BMM Workflow Status

## Current State

**Phase**: 2 - Planning
**Scale Level**: 2 (Small Feature)
**Project Type**: Software
**Current Epic**: None (starting project)
**Status**: PLANNING

## Project Overview

**Goal**: [Your project goal]

**Key Documents**:
- PRD: `docs/features/<feature>/PRD.md` (to be created)
- Architecture: `docs/features/<feature>/ARCHITECTURE.md` (to be created)
- Epics: `docs/features/<feature>/epics.md` (to be created)

## Next Actions

1. Create PRD using `/create-prd`
2. Create Architecture using `/create-architecture`
3. Create Epic breakdown using `/create-epic`
4. Create story files using `/create-stories`
```

### Step 3: Initialize sprint-status.yaml

```yaml
sprint_name: "Sprint 1"
start_date: "2025-11-05"
phase: 2-planning
scale_level: 2

epics:
  # Epics will be added as you create them
```

---

## First Time Usage

### Step 1: Check Status

```bash
# In Claude Code, use the command:
/status
```

This will read your bmm-workflow-status.md and show you where to start.

### Step 2: Create Your First Feature

```bash
# 1. Create PRD
/create-prd "Your Feature Name"
# → Spawns John agent
# → Creates docs/features/your-feature-name/PRD.md

# 2. Create Architecture
/create-architecture "Your Feature Name"
# → Spawns Winston agent
# → Creates docs/features/your-feature-name/ARCHITECTURE.md

# 3. Create Epic Breakdown
/create-epic "Your Feature Name"
# → Spawns John/Bob
# → Creates docs/features/your-feature-name/epics.md

# 4. Create Story Files
/create-stories --epic 1
# → Spawns Bob agent
# → Creates story files in docs/features/your-feature-name/stories/epic-1/
# → Updates sprint-status.yaml

# 5. Implement First Story
/implement-story --epic 1 --story 1
# → Spawns Amelia agent
# → Implements with TDD
# → Creates atomic commit
# → Updates sprint-status.yaml
```

---

## Using in Existing Projects

### If You Already Have Features

1. **Organize existing docs** into the B-MAD structure:
```bash
mkdir -p docs/features/<existing-feature>
mv <existing-prd> docs/features/<existing-feature>/PRD.md
mv <existing-architecture> docs/features/<existing-feature>/ARCHITECTURE.md
```

2. **Create missing docs** (PRD, Architecture, Epics) using slash commands

3. **Update tracking files**:
   - bmm-workflow-status.md (current status)
   - sprint-status.yaml (story tracking)

### Migration Strategy

**Option 1: Fresh Start**
- Use B-MAD for all NEW features
- Keep existing features as-is
- Gradually migrate existing features over time

**Option 2: Full Migration**
- Create PRDs for existing features
- Create Architectures for existing code
- Break down into epics and stories
- Track retrospectively in sprint-status.yaml

---

## Team Rollout

### Phase 1: Pilot (Week 1)
- 1-2 developers install and test
- Create one small feature end-to-end
- Gather feedback
- Adjust prompts/commands if needed

### Phase 2: Team Training (Week 2)
- Share CLAUDE.md with team
- Demo the workflow with agents
- Explain key concepts:
  - B-MAD scale levels
  - The 7 specialized agents
  - Task tool usage
  - Atomic commits per story
  - Sprint tracking

### Phase 3: Full Rollout (Week 3)
- All team members install
- All new features use B-MAD workflow
- Update team documentation
- Include in onboarding

### Phase 4: Continuous Improvement (Ongoing)
- Review sprint retrospectives
- Update methodology based on learnings
- Share improvements with team
- Iterate on agent prompts

---

## What You Get

### Complete Methodology
- **CLAUDE.md**: 20KB guide covering entire B-MAD workflow
- **Slash Commands**: 7 ready-to-use commands for agent-based development
- **Proven Patterns**: Based on real-world project (GAO-Dev)

### Agent-Based Automation
- **John** (PM): Creates PRDs, defines requirements
- **Winston** (Architect): Designs system architecture
- **Sally** (UX): Creates user experience designs
- **Bob** (Scrum Master): Creates and manages stories
- **Amelia** (Developer): Implements features with TDD
- **Murat** (QA): Creates test strategies
- **Brian** (Coordinator): Selects workflows, analyzes scale

### Quality Assurance
- TDD approach (tests first)
- 80%+ coverage requirement
- Type safety (MyPy strict)
- SOLID principles
- Linting (Ruff)
- Atomic commits

---

## Configuration

### Customizing for Your Project

**Edit CLAUDE.md**:
```bash
code .claude/bmad-agent-workflow/CLAUDE.md
```

Update:
- Project-specific context
- Quality thresholds (coverage, etc.)
- Technology stack specifics
- Team conventions

**Edit Slash Commands**:
```bash
code .claude/bmad-agent-workflow/commands/create-prd.md
```

Customize:
- Agent prompts
- File paths
- Workflow steps
- Team-specific requirements

---

## Troubleshooting

### Slash Commands Not Working?

Check file locations:
```
your-project/
  .claude/
    bmad-agent-workflow/
      commands/
        create-prd.md
        create-architecture.md
        ...
```

### Task Tool Not Spawning Agents?

Ensure Claude Code has access to:
- Task tool
- Agents (John, Winston, Bob, Amelia, etc.)
- Workflows

### Documentation Not Being Created?

Check:
- docs/features/ directory exists
- Permissions allow file creation
- Agent prompts include correct paths

### Sprint Tracking Not Updating?

Verify:
- sprint-status.yaml exists in docs/
- Format is valid YAML
- Agents have permission to edit

---

## Support

### Common Questions

**Q: Do I need all 7 agents?**
A: No, use what you need. Most projects use John (PRD), Winston (Architecture), Bob (Stories), and Amelia (Implementation).

**Q: Can I customize the agents?**
A: Yes! Edit the slash command prompts to customize agent behavior.

**Q: What if I don't want to use sprint-status.yaml?**
A: You can track stories however you want, but sprint-status.yaml provides automated tracking.

**Q: Can I use this with GitHub Issues?**
A: Yes! Sprint-status.yaml can mirror your GitHub Issues, or you can use GitHub Issues directly.

**Q: Do I need to follow TDD strictly?**
A: TDD is a core principle of quality. Tests-first ensures high coverage and prevents bugs.

### Getting Help

- **Read CLAUDE.md** - Most questions answered there
- **Check command files** - See exact agent prompts
- **Review examples** - See workflow in action
- **Ask your team** - Share learnings

---

## Next Steps

After installation:

1. **Read CLAUDE.md** (15 minutes) - Understand methodology
2. **Run /status** - See current project state
3. **Try /create-prd** - Create your first PRD
4. **Follow workflow** - PRD → Architecture → Epics → Stories → Implementation
5. **Share template** - Help teammates achieve same excellence

---

## Maintenance

### Keep Template Updated

As your team learns:

1. **Update agent prompts** based on what works
2. **Add new commands** for common workflows
3. **Refine quality standards** based on learnings
4. **Version control** your customizations
5. **Share updates** with team

### Regular Reviews

Review quarterly:
- Are agents producing quality outputs?
- Do commands need adjustment?
- Are quality standards appropriate?
- What can be improved?

---

**Welcome to B-MAD Agent-Based Development!**

You now have a proven methodology for autonomous, high-quality software delivery through intelligent agent collaboration.

**Questions?** Review CLAUDE.md and command files for detailed guidance.
