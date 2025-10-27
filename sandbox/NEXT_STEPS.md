# GAO-Dev Sandbox - Next Steps

## What We Just Accomplished ✅

1. **Initialized Sandbox Project**: Created dedicated workspace at `D:\GAO Agile Dev\sandbox\`
2. **Created Project Brief**: Comprehensive brief with vision, requirements, and success criteria
3. **Generated PRD**: Detailed Product Requirements Document following BMAD workflow
4. **Identified Key Gap**: Discovered that autonomous agent spawning doesn't work from within Claude Code

## Critical Discovery: Agent Spawning Limitation

**Issue**: When running `gao-dev create-prd` from Claude Code, the system hangs trying to spawn John (PM agent).

**Root Cause**: The Claude Agent SDK tries to create new Claude sessions, but we're already in a Claude Code session.

**Impact**: Cannot use autonomous commands (`create-prd`, `create-story`, `implement-story`) within Claude Code.

**Workaround Options**:
1. **Manual Execution**: Use traditional `execute` command and follow workflow instructions
2. **Standalone Mode**: Create CLI that runs outside Claude Code (spawn sessions externally)
3. **Hybrid Mode**: Generate instructions from workflows, user executes in Claude Code
4. **API Key Mode**: Use Anthropic API key instead of logged-in session (requires key)

**Recommendation**: Implement Standalone Mode for benchmarking (option 2)

---

## Required Information from User

### 1. Boilerplate Repository Details

We need the starter template repository for the todo app:

**Required Info:**
- Repository URL (e.g., `https://github.com/user/nextjs-fastapi-template`)
- Branch to use (e.g., `main`)
- Directory structure
- Template variables that need substitution

**Expected Structure:**
```
boilerplate-repo/
├── frontend/              # Next.js app
│   ├── package.json
│   ├── src/
│   └── ...
├── backend/               # FastAPI or Express
│   ├── requirements.txt or package.json
│   ├── src/
│   └── ...
├── docker-compose.yml     # Docker setup
├── .env.example          # Environment variables template
└── README.md
```

**Template Variables Expected:**
- `{{PROJECT_NAME}}` - Name of the project
- `{{AUTHOR}}` - Author name
- `{{DATABASE_NAME}}` - Database name
- Others?

### 2. Tech Stack Preference

**Backend Choice:**
- [ ] Python with FastAPI
- [ ] Node.js with Express
- [ ] Both supported?

### 3. Execution Mode Preference

**How should benchmarks run?**
- [ ] Standalone CLI (runs outside Claude Code)
- [ ] Hybrid mode (generate plans, execute manually)
- [ ] API key mode (use Anthropic API key)

---

## Proposed Next Steps

### Immediate (This Session)

1. **Get Boilerplate Repo Info**
   - User provides repository URL and structure
   - Document template variables

2. **Create Architecture Document**
   - Use Winston (Architect) workflow
   - Design sandbox system architecture
   - Define component interfaces

3. **Create First Epic & Stories**
   - Use Bob (Scrum Master) workflow
   - Epic 1: Sandbox Infrastructure
   - Break down into stories

### Short-term (Next Session)

4. **Implement Sandbox CLI Commands**
   - `gao-dev sandbox init`
   - `gao-dev sandbox clean`
   - `gao-dev sandbox list`

5. **Implement Boilerplate Integration**
   - Clone repository
   - Substitute template variables
   - Initialize project

6. **Create Basic Metric Collection**
   - Time tracking
   - Token counting (if possible)
   - JSON storage

### Medium-term

7. **Implement Benchmark Runner**
   - Load config files
   - Execute full workflow
   - Collect all metrics

8. **Create Reporting System**
   - Generate HTML reports
   - Comparison tools
   - Trend analysis

9. **First End-to-End Benchmark**
   - Run todo app creation
   - Measure all metrics
   - Identify gaps

### Long-term

10. **Iterate & Optimize**
    - Address identified gaps
    - Improve autonomy scores
    - Reduce manual interventions
    - Achieve one-shot success

---

## Questions for User

### Q1: Boilerplate Repository
**What is the URL and structure of your starter template repository?**

Please provide:
- Git URL
- Branch name
- Template variable names
- Any special setup instructions

### Q2: Backend Technology
**Which backend should we focus on first?**
- FastAPI (Python) - Aligns with GAO-Dev being Python
- Express (Node.js) - Aligns with Next.js frontend
- Both - More complex but flexible

### Q3: Execution Mode
**How should we handle the agent spawning limitation?**

Options:
1. **Standalone CLI** - Create `gao-dev-runner` that runs outside IDE
2. **Manual hybrid** - Generate plans, execute manually in Claude Code
3. **API key mode** - Use Anthropic API (requires key)

My recommendation: **Standalone CLI** for benchmarking, keep manual mode for development

### Q4: Scope
**Should we implement all features in the PRD, or start with MVP?**

MVP Scope (Recommended):
- ✅ Sandbox init/clean/list
- ✅ Boilerplate integration
- ✅ Basic metric collection (time, manual interventions)
- ✅ Simple text-based reports
- ✅ One reference app (todo)

Full Scope:
- All metrics (performance, autonomy, quality, workflow)
- HTML dashboards with charts
- Comparison & trend analysis
- Multiple reference apps
- CI/CD integration

---

## Current Project Status

**Repository**: https://github.com/memyselfmike/gao-agile-dev.git
**Branch**: main
**Last Commit**: Initial SDK integration (68 files)

**Sandbox Status**:
- ✅ Project initialized: `D:\GAO Agile Dev\sandbox\`
- ✅ PRD created: `docs/PRD.md`
- ✅ Project brief: `PROJECT_BRIEF.md`
- ⏳ Architecture: Pending
- ⏳ Stories: Pending
- ⏳ Implementation: Pending

---

## Immediate Action Required

**Please provide the boilerplate repository information so we can proceed with:**
1. Creating the architecture document
2. Breaking down into implementable stories
3. Building the sandbox infrastructure

Once we have that, we can use GAO-Dev to build the sandbox system, then use the sandbox to validate and improve GAO-Dev - creating a powerful feedback loop!

---

*This document tracks the sandbox development progress and next steps.*
