# GAO-Dev Agents & Skills for Claude Code

This directory contains specialized agents and skills extracted from the BMAD methodology and adapted for Claude Code's Task tool system.

## Overview

**Sub-Agents** are specialized AI assistants that Claude Code can delegate tasks to. Each agent has expertise in a specific domain and operates with its own context window.

**Skills** are modular capabilities that extend Claude's functionality. They're invoked automatically by Claude when the task matches the skill's description.

## Available Sub-Agents

All agents are stored in `.claude/agents/` and can be invoked using the Task tool.

### 1. Scrum Master (Bob) - `scrum-master.md`

**Description**: Technical Scrum Master specializing in user story creation, sprint planning, and agile ceremonies.

**Use When**:
- Creating user stories from requirements
- Planning sprints or breaking down epics
- Conducting retrospectives
- Preparing development-ready specifications
- Refining backlog items

**Core Capabilities**:
- User story creation with clear acceptance criteria
- Sprint planning and story sequencing
- Story refinement and clarification
- Retrospective facilitation
- Story context assembly

**Example Usage**:
```
Create a user story for the password reset feature described in the PRD, including acceptance criteria and test scenarios.
```

---

### 2. Developer (Amelia) - `developer.md`

**Description**: Senior Implementation Engineer specializing in code implementation, testing, and story completion.

**Use When**:
- Implementing user stories
- Writing tests (TDD approach)
- Fixing bugs
- Completing development tasks
- Code implementation with strict AC adherence

**Core Capabilities**:
- Story implementation with TDD
- Comprehensive test coverage
- Code quality assurance
- Bug fixing with regression tests
- Self-code review

**Example Usage**:
```
Implement Story 1.3 (User Password Reset) following all acceptance criteria and using TDD approach. Ensure 100% test coverage.
```

---

### 3. Architect (Winston) - `architect.md`

**Description**: System Architect and Technical Design Leader specializing in distributed systems and scalable architecture patterns.

**Use When**:
- Designing system architecture
- Making technology choices
- Evaluating technical approaches
- Planning migrations
- Creating architectural documentation

**Core Capabilities**:
- System architecture design
- Technology selection and evaluation
- API design and data architecture
- Security architecture
- Migration strategy planning

**Example Usage**:
```
Design a scalable architecture for a real-time todo application that supports 10,000 concurrent users, including database selection, API design, and deployment strategy.
```

---

### 4. Business Analyst (Mary) - `business-analyst.md`

**Description**: Strategic Business Analyst and Requirements Expert specializing in market research and requirements elicitation.

**Use When**:
- Gathering requirements from stakeholders
- Conducting market or competitive research
- Facilitating brainstorming sessions
- Translating business needs into specifications
- Documenting existing projects

**Core Capabilities**:
- Requirements elicitation
- Market and competitive research
- Brainstorming facilitation
- Product brief creation
- Existing project documentation

**Example Usage**:
```
Conduct a competitive analysis of todo applications focusing on collaboration features, pricing models, and key differentiators. Present findings in a structured format.
```

---

### 5. Product Manager (John) - `product-manager.md`

**Description**: Investigative Product Strategist specializing in PRD creation, feature prioritization, and product roadmaps.

**Use When**:
- Creating Product Requirements Documents
- Prioritizing features
- Defining product strategy
- Planning product releases
- Making product decisions

**Core Capabilities**:
- PRD creation and documentation
- Feature prioritization (RICE, MoSCoW)
- Product roadmap planning
- Technical specification writing
- Go-to-market strategy

**Example Usage**:
```
Create a comprehensive PRD for a collaborative todo application targeting small teams, including user personas, functional requirements, success metrics, and competitive positioning.
```

---

### 6. Test Architect (Murat) - `test-architect.md`

**Description**: Master Test Architect specializing in test strategy, automation frameworks, and CI/CD integration.

**Use When**:
- Designing test strategies
- Setting up test frameworks
- Implementing test automation
- Advising on quality assurance
- Planning CI/CD quality gates

**Core Capabilities**:
- Test strategy design
- Test framework setup
- ATDD (Acceptance Test-Driven Development)
- Test automation
- CI/CD quality pipeline design
- Requirements traceability

**Example Usage**:
```
Design a comprehensive test strategy for a todo application including unit, integration, and E2E tests. Set up pytest framework with CI/CD integration.
```

---

## Available Skills

Skills are stored in `.claude/skills/` and are automatically invoked by Claude when appropriate.

### 1. Story Writing - `story-writing/SKILL.md`

**Description**: Create well-structured user stories with clear acceptance criteria and test scenarios.

**Auto-Invoked When**: Creating user stories, refining backlog items, or breaking down epics.

**Key Features**:
- INVEST criteria validation
- Clear acceptance criteria templates
- Test scenario guidelines
- Definition of Done checklist

---

### 2. PRD Creation - `prd-creation/SKILL.md`

**Description**: Create comprehensive Product Requirements Documents that align stakeholders.

**Auto-Invoked When**: Planning new features, products, or major initiatives.

**Key Features**:
- Complete PRD structure with all sections
- Quality checklist
- Prioritization frameworks
- Research and discovery process

---

### 3. Architecture Design - `architecture-design/SKILL.md`

**Description**: Design system architectures with focus on scalability and maintainability.

**Auto-Invoked When**: Designing systems, making technology choices, or planning migrations.

**Key Features**:
- Comprehensive architecture document structure
- Technology evaluation framework
- Security and scalability checklists
- Common patterns and anti-patterns

---

### 4. Code Review - `code-review/SKILL.md`

**Description**: Perform comprehensive code reviews focusing on quality and security.

**Auto-Invoked When**: Reviewing code changes before merging.

**Key Features**:
- Multi-faceted review checklist (security, performance, maintainability)
- Feedback categorization (critical, important, suggestion)
- Example good/poor feedback
- Review process guidance

---

## How to Use

### Using Sub-Agents

Claude Code will automatically invoke the appropriate agent based on your request. You can also explicitly request an agent:

**Automatic Invocation**:
```
I need to create a PRD for a new todo app feature.
```
→ Claude may invoke the `product-manager` agent

**Explicit Invocation**:
```
Use the architect agent to design a system architecture for this application.
```

**Parallel Agent Use**:
```
I need both a PRD and system architecture. Use the product-manager and architect agents in parallel to create both.
```

### Using Skills

Skills are automatically invoked by Claude based on the task context. You don't need to explicitly call them, but you can reference them:

```
Help me write a user story following the story-writing skill guidelines.
```

Skills can also restrict tool usage. For example, the `code-review` skill only has read access (no Write or Edit), ensuring safe review operations.

---

## Agent Selection Guide

Use this guide to choose the right agent:

| Task Type | Agent | Example |
|-----------|-------|---------|
| Define product vision | Product Manager | "Create a PRD for feature X" |
| Gather requirements | Business Analyst | "Research competitors and gather requirements" |
| Design architecture | Architect | "Design a scalable system for Y" |
| Plan sprint work | Scrum Master | "Create user stories from epic Z" |
| Implement features | Developer | "Implement story 1.3 with full tests" |
| Design testing approach | Test Architect | "Create test strategy for the application" |

---

## Agent Coordination

Agents can work together in sequence:

1. **Business Analyst** → Gather requirements and competitive research
2. **Product Manager** → Create PRD from requirements
3. **Architect** → Design system architecture based on PRD
4. **Scrum Master** → Break down architecture into user stories
5. **Test Architect** → Design test strategy
6. **Developer** → Implement stories with tests

---

## Customization

### Modifying Agents

Edit agent files in `.claude/agents/` to customize:
- **name**: Agent identifier (lowercase, hyphens)
- **description**: When Claude should use this agent (critical for auto-selection)
- **tools**: Which tools the agent can access
- **model**: sonnet (default), opus (more capable), haiku (faster)

### Modifying Skills

Edit skill files in `.claude/skills/skill-name/SKILL.md` to customize:
- **name**: Skill identifier
- **description**: When Claude should invoke this skill
- **allowed-tools**: Restrict tools for safety (e.g., read-only reviews)

### Adding Supporting Files

Skills can include supporting files:
```
.claude/skills/my-skill/
├── SKILL.md
├── examples.md
├── templates/
│   └── story-template.md
└── scripts/
    └── helper.py
```

Reference them in SKILL.md, and Claude will load them as needed.

---

## Best Practices

### For Agent Use

1. **Be Specific**: Clearly describe what you need
2. **Provide Context**: Share relevant files, requirements, or constraints
3. **Use Parallel Execution**: When tasks are independent, ask for parallel agent execution
4. **Review Agent Output**: Agents are experts but review their work
5. **Iterate**: Agents can refine their output based on feedback

### For Skill Use

1. **Trust Auto-Invocation**: Claude will invoke skills when appropriate
2. **Reference Explicitly**: If unsure, reference the skill by name
3. **Check Tool Restrictions**: Some skills have read-only access by design
4. **Customize for Your Workflow**: Adapt skills to your team's standards

---

## Troubleshooting

### Agent Not Being Invoked

**Problem**: Claude isn't using the agent you expect

**Solutions**:
- Make the `description` field more specific with trigger keywords
- Explicitly request the agent by name
- Check that the agent file is in `.claude/agents/`

### Skill Not Being Invoked

**Problem**: Skill isn't being used automatically

**Solutions**:
- Check YAML frontmatter syntax (no tabs, proper `---` delimiters)
- Make description more specific with trigger terms
- Verify file location: `.claude/skills/skill-name/SKILL.md`
- Try explicitly mentioning the skill name

### Agent Has Wrong Tools

**Problem**: Agent can't access a tool it needs

**Solution**:
- Edit the agent file's `tools:` field
- Add the required tool (Read, Write, Edit, Grep, Glob, Bash, WebFetch, WebSearch)

---

## Project Standards & Conventions

Before working on GAO-Dev, agents should review these key directives:

- **Folder Structure & Naming**: `.claude/FOLDER_STRUCTURE_AND_NAMING_DIRECTIVE.md` - Complete conventions for folders, files, variables, and commits
- **Project Guide**: `CLAUDE.md` - Overview of GAO-Dev architecture, status, and development patterns
- **Variable Naming Guide**: `docs/features/feature-based-document-structure/VARIABLE_NAMING_GUIDE.md` - Detailed variable resolution guide

## References

- **Sub-Agents Documentation**: https://code.claude.com/docs/en/sub-agents
- **Skills Documentation**: https://code.claude.com/docs/en/skills
- **BMAD Source**: `C:\Projects\gao-agile-dev\bmad\bmm\agents\`
- **GAO-Dev Standards**: `.claude/FOLDER_STRUCTURE_AND_NAMING_DIRECTIVE.md`

---

## Version History

- **v1.0** (2025-11-11): Initial extraction from BMAD methodology
  - 6 specialized agents (Scrum Master, Developer, Architect, Business Analyst, Product Manager, Test Architect)
  - 4 core skills (Story Writing, PRD Creation, Architecture Design, Code Review)
  - Compatible with Claude Code Task tool system

---

**Remember**: These agents and skills work best when you provide clear context and specific requests. They're designed to be your specialized team members, each bringing deep expertise to their domain.
