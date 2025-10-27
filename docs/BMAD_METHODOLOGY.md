# BMAD Methodology - GAO-Dev

**Version**: 1.0.0
**Last Updated**: 2025-10-27
**Status**: Active

---

## Table of Contents

1. [Overview](#overview)
2. [What is BMAD?](#what-is-bmad)
3. [The 7 Specialized Agents](#the-7-specialized-agents)
4. [The BMAD Workflow](#the-bmad-workflow)
5. [When to Use BMAD](#when-to-use-bmad)
6. [Agent Handoff Protocol](#agent-handoff-protocol)
7. [Integration with Sandbox System](#integration-with-sandbox-system)
8. [BMAD in Practice](#bmad-in-practice)
9. [Benefits](#benefits)
10. [Common Patterns](#common-patterns)

---

## Overview

BMAD (Business Analysis → Methodology → Architecture → Development) is GAO-Dev's autonomous software development workflow that orchestrates 7 specialized AI agents to deliver complete, production-ready applications from simple prompts.

**Core Philosophy**: Each agent is a specialist with specific tools, responsibilities, and expertise, working together through a structured handoff process to produce high-quality software.

---

## What is BMAD?

BMAD represents the four critical phases of software development:

### B - Business Analysis
**Agent**: Mary (Business Analyst)
**Focus**: Understanding the problem, researching requirements, analyzing business context

### M - Methodology
**Agent**: John (Product Manager)
**Focus**: Defining what to build, creating specifications, prioritizing features

### A - Architecture
**Agents**: Winston (Technical Architect) + Sally (UX Designer)
**Focus**: Designing how to build it, technical decisions, user experience

### D - Development
**Agents**: Bob (Scrum Master) + Amelia (Developer) + Murat (Test Architect)
**Focus**: Building, testing, and delivering the solution

---

## The 7 Specialized Agents

### 1. Mary - Business Analyst

**Persona**: Analytical, detail-oriented, research-focused
**Role**: Analysis and requirements gathering
**Primary Tools**:
- Read, Write, Grep, Glob (file operations)
- Research tools (WebFetch, WebSearch)
- Workflows (can execute research workflows)

**Responsibilities**:
- Conduct business analysis
- Research market/competition
- Gather stakeholder requirements
- Create PROJECT_BRIEF documents
- Identify constraints and opportunities
- Provide context for downstream agents

**When to Use Mary**:
- New project inception
- Market research needed
- Requirements unclear
- Stakeholder analysis required

---

### 2. John - Product Manager

**Persona**: Strategic, prioritization-focused, customer-centric
**Role**: Product definition and feature prioritization
**Primary Tools**:
- Read, Write, Grep, Glob
- Workflows (PRD workflows)
- Sprint status tools
- Research tools

**Responsibilities**:
- Create Product Requirements Documents (PRDs)
- Define features and user stories
- Prioritize backlog
- Define success metrics
- Create epic breakdowns
- Maintain product vision

**When to Use John**:
- After business analysis (Mary's output)
- When creating PRDs
- Feature prioritization needed
- Sprint planning required

---

### 3. Winston - Technical Architect

**Persona**: System-thinking, design-focused, quality-conscious
**Role**: Technical architecture and system design
**Primary Tools**:
- Read, Write, Edit, Grep, Glob
- Workflows (architecture workflows)
- Research tools

**Responsibilities**:
- Design system architecture
- Make technical decisions (tech stack, patterns, tools)
- Create ARCHITECTURE documents
- Define component interfaces
- Plan data models
- Establish technical standards

**When to Use Winston**:
- After PRD created (John's output)
- Technical decisions needed
- System design required
- Architecture review needed

---

### 4. Sally - UX Designer

**Persona**: User-focused, design-thinking, empathetic
**Role**: User experience and interface design
**Primary Tools**:
- Read, Write, Grep, Glob
- Workflows (UX design workflows)
- Story status tools
- Research tools

**Responsibilities**:
- Design user flows
- Create wireframes (text-based descriptions)
- Define UI/UX specifications
- Ensure accessibility standards
- Design interaction patterns
- Create design system guidelines

**When to Use Sally**:
- After PRD/Architecture (parallel with Winston)
- UI/UX design needed
- User flows undefined
- Accessibility review required

---

### 5. Bob - Scrum Master

**Persona**: Organized, process-focused, team coordinator
**Role**: Story management and team coordination
**Primary Tools**:
- Read, Write, Grep, Glob
- Workflows (story creation workflows)
- Story management tools (create, update, query stories)
- Git tools (branch, commit, merge)
- TodoWrite (progress tracking)

**Responsibilities**:
- Create user stories from epics
- Manage sprint backlog
- Track story status
- Coordinate agent handoffs
- Create feature branches
- Manage git workflow

**When to Use Bob**:
- After architecture/design (Winston + Sally's output)
- Story creation needed
- Sprint management required
- Git workflow coordination

---

### 6. Amelia - Software Developer

**Persona**: Implementation-focused, code-quality-driven, pragmatic
**Role**: Software implementation and code delivery
**Primary Tools**:
- Read, Write, Edit, MultiEdit (code editing)
- Grep, Glob (code navigation)
- Bash (running tests, builds, scripts)
- Workflows (development workflows)
- Story management tools
- Git tools (branch, commit, merge)
- TodoWrite (progress tracking)
- Research tools (documentation lookup)

**Responsibilities**:
- Implement features from stories
- Write clean, tested code
- Follow architecture and design specs
- Conduct code reviews
- Fix bugs and refactor
- Write unit and integration tests
- Document code

**When to Use Amelia**:
- After stories created (Bob's output)
- Implementation work needed
- Code reviews required
- Bug fixes needed

---

### 7. Murat - Test Architect

**Persona**: Quality-focused, thorough, risk-aware
**Role**: Test strategy and quality assurance
**Primary Tools**:
- Read, Write, Edit, Grep, Glob
- Bash (running tests, quality checks)
- Workflows (test strategy workflows)
- Story status tools
- Git tools
- TodoWrite

**Responsibilities**:
- Define test strategies
- Create test plans
- Establish quality standards
- Run quality checks (type checking, linting, coverage)
- Validate acceptance criteria
- Security and performance testing
- Final quality gate before production

**When to Use Murat**:
- After implementation (Amelia's output)
- Test strategy needed
- Quality validation required
- Pre-production review

---

## The BMAD Workflow

### Standard Flow (Full Project)

```
User Prompt
    |
    v
[Mary: Business Analysis]
    |
    v
PROJECT_BRIEF.md
    |
    v
[John: Product Requirements]
    |
    v
PRD.md + epics.md
    |
    v
[Winston: Technical Architecture] <---> [Sally: UX Design]
    |                                           |
    v                                           v
ARCHITECTURE.md                         UX_DESIGN.md
    |                                           |
    +-------------------------------------------+
                        |
                        v
            [Bob: Story Creation]
                        |
                        v
            stories/epic-N/story-N.M.md
                        |
                        v
            [Amelia: Implementation]
                        |
                        v
                Working Code + Tests
                        |
                        v
            [Murat: Quality Validation]
                        |
                        v
            Production-Ready Application
```

### Workflow Variations

**Quick Feature** (Skip Mary):
```
User Prompt → John (PRD) → Winston/Sally → Bob → Amelia → Murat
```

**Bug Fix** (Skip to Amelia):
```
Bug Report → Amelia (Fix) → Murat (Validate)
```

**Architecture Review** (Winston only):
```
Existing Code → Winston (Review) → Recommendations
```

**Story Creation** (Start at Bob):
```
Epic Definition → Bob (Stories) → Ready for Development
```

---

## Agent Handoff Protocol

Each agent follows this handoff pattern:

### 1. Receive Context
- Read previous agent's output documents
- Understand requirements and constraints
- Clarify any ambiguities (via AskUserQuestion)

### 2. Execute Work
- Use specialized tools for their domain
- Follow established patterns and standards
- Track progress with TodoWrite
- Create required artifacts

### 3. Validate Output
- Ensure acceptance criteria met
- Check against quality standards
- Verify all required artifacts created

### 4. Handoff to Next Agent
- Document decisions made
- Highlight key points for next agent
- Note any open questions or risks
- Commit artifacts to git (if applicable)

### Handoff Artifacts

| From → To | Artifact | Purpose |
|-----------|----------|---------|
| Mary → John | PROJECT_BRIEF.md | Business context for PRD |
| John → Winston | PRD.md, epics.md | Requirements for architecture |
| John → Sally | PRD.md | Requirements for UX design |
| Winston → Bob | ARCHITECTURE.md | Technical design for stories |
| Sally → Bob | UX_DESIGN.md | UI/UX specs for stories |
| Bob → Amelia | stories/*.md | Implementation tasks |
| Amelia → Murat | Working code | Code to validate |

---

## When to Use BMAD

### Use BMAD (Full Workflow) When:

✅ Building new applications from scratch
✅ Adding major features (3+ epics)
✅ Unclear requirements (need analysis)
✅ Complex system design needed
✅ Production-ready quality required
✅ Full documentation needed

### Use Partial BMAD When:

⚡ Small features (1-2 stories) - Start at Bob
⚡ Bug fixes - Start at Amelia
⚡ Code refactoring - Amelia + Murat
⚡ Architecture review - Winston only
⚡ Test strategy - Murat only

### Don't Use BMAD When:

❌ Simple script/utility (manual coding faster)
❌ Prototype/spike (too much process)
❌ Documentation-only changes
❌ Configuration changes

---

## Integration with Sandbox System

The sandbox system validates that BMAD produces production-ready code autonomously.

### Benchmark Flow

```
1. Initialize Sandbox
   gao-dev sandbox init todo-app-001

2. Run BMAD Workflow (Autonomous)
   gao-dev sandbox run benchmarks/todo-baseline.yaml

   Internally executes:
   Mary → John → Winston → Sally → Bob → Amelia → Murat

3. Collect Metrics
   - Time per agent
   - Manual interventions
   - Quality metrics
   - Success criteria validation

4. Generate Report
   gao-dev sandbox report <run-id>

5. Analyze & Improve
   - Identify gaps
   - Create improvement stories (Epic 7+)
   - Enhance agent capabilities
   - Re-run benchmark
```

### Success Criteria

**Phase 1** (Current): BMAD with manual intervention
**Phase 2** (Goal): BMAD 70%+ autonomous
**Phase 3** (Vision): BMAD 95%+ autonomous (one-shot success)

---

## BMAD in Practice

### Example 1: Building Todo App

**User Prompt**: "Build a todo application with authentication"

**Execution**:

1. **Mary** researches todo app patterns, authentication methods, creates PROJECT_BRIEF.md
2. **John** creates PRD.md with features, epics, success metrics
3. **Winston** designs system architecture (Next.js, PostgreSQL, Prisma)
4. **Sally** designs user flows, UI components, accessibility
5. **Bob** creates 15 stories across 4 epics
6. **Amelia** implements stories sequentially, writing tests
7. **Murat** validates quality, runs final checks, approves for production

**Result**: Production-ready todo app with auth, tests, docs, deployment config

---

### Example 2: Adding Feature to Existing App

**User Prompt**: "Add email notifications to the todo app"

**Execution** (Partial BMAD):

1. **John** creates mini-PRD for email feature
2. **Winston** designs email service integration
3. **Bob** creates 3 stories
4. **Amelia** implements email service + integration
5. **Murat** validates, checks security, approves

**Result**: Email notifications integrated cleanly

---

### Example 3: Bug Fix

**User Prompt**: "Fix the login button not working on mobile"

**Execution** (Skip to Development):

1. **Amelia** investigates issue, finds CSS bug, fixes it, adds test
2. **Murat** validates fix on multiple devices, approves

**Result**: Bug fixed, test added, validated

---

## Benefits

### 1. Specialization
Each agent is expert in their domain, producing higher quality output than generalists

### 2. Consistency
Structured workflow ensures nothing is skipped (requirements → design → implementation → testing)

### 3. Quality
Multiple validation points catch issues early

### 4. Documentation
Artifacts created at each phase provide complete project documentation

### 5. Traceability
Clear lineage from business need → requirements → design → code → tests

### 6. Scalability
Can run multiple BMAD workflows in parallel for different features

### 7. Measurability
Sandbox system tracks metrics at each phase to drive improvement

---

## Common Patterns

### Pattern 1: Feature Development

```
John → Winston → Bob → Amelia → Murat
```
Use when adding features to existing apps (skip business analysis)

### Pattern 2: Full Project

```
Mary → John → Winston → Sally → Bob → Amelia → Murat
```
Use for new projects or major initiatives

### Pattern 3: Story-Driven Development

```
Bob → Amelia → Murat (repeat for each story)
```
Use when epics/architecture already exist

### Pattern 4: Quality Gate

```
Amelia → Murat → (back to Amelia if issues) → Murat → Done
```
Use for final validation before release

### Pattern 5: Architecture Evolution

```
Winston → Bob (update stories) → Amelia (refactor)
```
Use when evolving system architecture

---

## Troubleshooting

### Issue: Agent Doesn't Have Context

**Solution**: Ensure previous agent's artifacts are committed and readable

### Issue: Agent Asks Too Many Questions

**Solution**: Improve handoff artifacts with more detail

### Issue: Quality Issues Not Caught

**Solution**: Strengthen Murat's test strategy, add more checks

### Issue: Workflow Too Slow

**Solution**: Use partial BMAD, skip unnecessary agents for simple tasks

### Issue: Agents Duplicate Work

**Solution**: Clearer role boundaries, better handoff documentation

---

## Evolution & Improvement

BMAD is not static. The sandbox system helps us:

1. **Measure**: Track time, quality, autonomy per agent
2. **Analyze**: Identify bottlenecks and gaps
3. **Improve**: Enhance agent prompts, tools, workflows
4. **Validate**: Re-run benchmarks to confirm improvement

**Improvement Loop**:
```
Run BMAD → Collect Metrics → Analyze Gaps →
Create Improvement Stories → Implement → Re-run BMAD
```

This continuous improvement is captured in **Epic 7: Iterative Improvement & Gap Remediation**

---

## Getting Started with BMAD

### For New Projects:

1. Start with `gao-dev create-prd --name "Project Name"` (triggers John)
2. Follow the workflow sequentially
3. Use TodoWrite to track progress
4. Commit artifacts at each phase

### For Existing Projects:

1. Determine entry point (which agent?)
2. Ensure that agent has required context
3. Execute from that point forward
4. Validate with Murat before merging

### For Learning:

1. Read agent persona files (`gao_dev/agents/*.md`)
2. Review example workflows (`gao_dev/workflows/`)
3. Try the sandbox system to see BMAD in action
4. Study the metrics to understand effectiveness

---

## Measuring BMAD Success

Key metrics tracked by sandbox system:

**Autonomy Metrics**:
- One-shot success rate (% tasks completed first try)
- Manual interventions per agent
- Error recovery rate

**Quality Metrics**:
- Test coverage
- Type safety (zero `Any` types)
- Code quality score
- Documentation completeness

**Efficiency Metrics**:
- Time per agent/phase
- Token usage per agent
- Stories completed per day

**Goal**: 95%+ autonomous completion with zero manual interventions

---

## Conclusion

BMAD is GAO-Dev's path to autonomous software development. By orchestrating 7 specialized agents through a structured workflow, we can transform simple prompts into production-ready applications.

The sandbox & benchmarking system validates this vision, providing data-driven insights to continuously improve until we achieve true one-shot autonomy.

**Remember**: BMAD is a framework, not a rigid process. Adapt it to your needs while maintaining the core principles of specialization, structured handoffs, and quality focus.

---

## References

- [Agent Persona Files](../gao_dev/agents/) - Detailed agent definitions
- [Workflow Templates](../gao_dev/workflows/) - Reusable workflow implementations
- [Sandbox System PRD](features/sandbox-system/PRD.md) - How sandbox validates BMAD
- [Quality Standards](QA_STANDARDS.md) - Quality criteria for all code
- [CLAUDE.md](../.claude/CLAUDE.md) - Quick reference guide for Claude

---

**Version History**:
- 1.0.0 (2025-10-27): Initial BMAD methodology documentation

---

*This methodology document captures the essence of GAO-Dev's autonomous development approach and will evolve as we learn from sandbox benchmarking.*
