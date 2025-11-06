# GAO-Dev Quick Reference

**Last Updated**: 2025-11-06

Quick reference for the most commonly used commands, agents, and documentation.

## Essential Commands

### Core Commands
```bash
# Version and help
gao-dev --version                    # Show version
gao-dev --help                       # Show help
gao-dev health                       # Run health check

# Discovery
gao-dev list-workflows               # List all workflows (55+)
gao-dev list-agents                  # List all agents (8)
gao-dev version                      # Show detailed version info
```

### Development Commands
```bash
# Initialize project
gao-dev init --name "Project"        # Initialize GAO-Dev project

# Autonomous workflows
gao-dev create-prd --name "Project"            # John creates PRD
gao-dev create-architecture --name "Project"   # Winston creates architecture
gao-dev create-story --epic 1 --story 1        # Bob creates story
gao-dev implement-story --epic 1 --story 1     # Bob + Amelia implement

# Execute any workflow
gao-dev execute <workflow-name>                # Execute specific workflow
```

### Sandbox & Benchmarking
```bash
# Sandbox management
gao-dev sandbox init <project-name>            # Create sandbox project
gao-dev sandbox list                           # List all projects
gao-dev sandbox clean <project-name>           # Clean/reset project
gao-dev sandbox delete <project-name>          # Delete project
gao-dev sandbox status                         # System status

# Run benchmarks
gao-dev sandbox run <benchmark.yaml>           # Run benchmark
```

### Metrics & Reporting
```bash
# Export metrics
gao-dev metrics export <run-id> --format csv   # Export to CSV

# Generate reports
gao-dev metrics report run <run-id>            # Generate HTML report
gao-dev metrics report compare <id1> <id2>     # Compare two runs
gao-dev metrics report trend <config>          # Trend analysis
gao-dev metrics report list                    # List all reports
gao-dev metrics report open <report-id>        # Open in browser
```

## The 8 Specialized Agents

### 1. Mary - Engineering Manager
**Role**: Team coordination, technical oversight, resource management
**Use For**: Coordinating development teams, reviewing technical decisions
**Tools**: Read, Write, Grep, Glob

### 2. Brian - Workflow Coordinator
**Role**: Intelligent workflow selection and orchestration
**Capability**: Scale-adaptive routing (Levels 0-4), clarification dialogs, multi-workflow sequencing
**Use For**: Initial project analysis, workflow selection, coordinating complex sequences
**Tools**: Read, Write, Grep, Glob, workflows, research

### 3. John - Product Manager
**Role**: PRDs, feature definition, prioritization
**Use For**: Creating PRDs, defining epics, prioritizing work
**Tools**: Read, Write, Grep, Glob, workflows, sprint status, research

### 4. Winston - Technical Architect
**Role**: System architecture, technical specifications
**Use For**: Architecture design, technical decisions, system design
**Tools**: Read, Write, Edit, Grep, Glob, workflows, research

### 5. Sally - UX Designer
**Role**: User experience, wireframes, design
**Use For**: UX design, user flows, interface design
**Tools**: Read, Write, Grep, Glob, workflows, story status, research

### 6. Bob - Scrum Master
**Role**: Story creation and management, team coordination
**Use For**: Creating stories, managing sprint, status tracking
**Tools**: Read, Write, Grep, Glob, workflows, story management, git, TodoWrite

### 7. Amelia - Software Developer
**Role**: Implementation, code reviews, testing
**Use For**: Implementing features, writing code, code reviews, testing
**Tools**: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, workflows, story management, git, TodoWrite, research

### 8. Murat - Test Architect
**Role**: Test strategies, quality assurance
**Use For**: Test strategies, test plans, quality standards, QA processes
**Tools**: Read, Write, Edit, Grep, Glob, Bash, workflows, story status, git, TodoWrite

## Scale-Adaptive Routing

GAO-Dev intelligently adapts its approach based on project scale:

| Level | Name | Duration | Description | Example |
|-------|------|----------|-------------|---------|
| **0** | Chore | <1 hour | Direct execution, no formal planning | Fix typo, update docs |
| **1** | Bug Fix | 1-4 hours | Minimal planning, direct fix | Fix failing test, resolve small bug |
| **2** | Small Feature | 1-2 weeks | PRD → Architecture → Stories → Implementation | Add authentication, new UI component |
| **3** | Medium Feature | 1-2 months | Full BMAD workflow with analysis | Complete module, integration system |
| **4** | Greenfield Application | 2-6 months | Comprehensive methodology with discovery | New product, complete rewrite |

## Essential Documentation

### Getting Started
- [QUICKSTART.md](../QUICKSTART.md) - Get started in 5 minutes
- [INDEX.md](INDEX.md) - Full documentation hub
- [SETUP.md](SETUP.md) - API key and configuration
- [README.md](../README.md) - Project overview

### Current Status
- [bmm-workflow-status.md](bmm-workflow-status.md) - Current epic and story status
- [sprint-status.yaml](sprint-status.yaml) - Sprint tracking

### Feature Documentation
- [Sandbox System](features/sandbox-system/) - Sandbox & benchmarking (Epics 1-5, 7-7.2)
- [Prompt Abstraction](features/prompt-abstraction/) - YAML-based prompts (Epic 10)
- [Document Lifecycle](features/document-lifecycle-system/) - Document tracking & context (Epics 12-17)
- [Agent Provider Abstraction](features/agent-provider-abstraction/) - Multi-provider support (Epic 11 - planned)

### Guides
- [CLAUDE.md](../CLAUDE.md) - Comprehensive guide for Claude Code sessions
- [plugin-development-guide.md](plugin-development-guide.md) - Plugin development
- [BENCHMARK_STANDARDS.md](BENCHMARK_STANDARDS.md) - Benchmarking standards

## Features Status

### Active & Complete
- Document Lifecycle System (Epics 12-17) - ACTIVE
- Sandbox System (Epics 1-5, 7-7.2) - COMPLETE
- Prompt Abstraction (Epic 10) - COMPLETE
- Core Refactor (Epic 6) - COMPLETE

### Planned
- Agent Provider Abstraction (Epic 11) - DOCUMENTED (ready to implement)

## Common Workflows

### Starting a New Project
```bash
# 1. Initialize
gao-dev init --name "My Project"

# 2. Create PRD (autonomous)
gao-dev create-prd --name "My Project"

# 3. Create architecture (autonomous)
gao-dev create-architecture --name "My Project"

# 4. Create stories (autonomous)
gao-dev create-story --epic 1 --story 1 --title "User authentication"

# 5. Implement stories (autonomous)
gao-dev implement-story --epic 1 --story 1
```

### Running Benchmarks
```bash
# 1. Set API key
export ANTHROPIC_API_KEY=your_key_here  # Linux/Mac
set ANTHROPIC_API_KEY=your_key_here     # Windows

# 2. Run benchmark
gao-dev sandbox run sandbox/benchmarks/workflow-driven-todo.yaml

# 3. View results
gao-dev metrics report list
gao-dev metrics report open <report-id>

# 4. Inspect artifacts
cd sandbox/projects/<project-name>/
git log --oneline
```

### Plugin Development
```bash
# 1. Create plugin structure
mkdir -p plugins/my-plugin/agents
mkdir -p plugins/my-plugin/prompts

# 2. Create agent YAML
# Edit plugins/my-plugin/agents/my-agent.yaml

# 3. Create prompt templates
# Edit plugins/my-plugin/prompts/my-prompt.yaml

# 4. Register plugin
# Add to plugin configuration

# 5. Test
gao-dev list-agents  # Should show your agent
```

## Configuration Files

### Project Configuration
- `gao-dev.yaml` - Project settings, methodology, git settings
- `.claude/settings.local.json` - Claude Code settings

### Agent Configurations
- `gao_dev/config/agents/*.yaml` - 8 agent YAML files
- `gao_dev/config/prompts/*.yaml` - Prompt templates

### Benchmark Configurations
- `sandbox/benchmarks/*.yaml` - Benchmark test scenarios

## Quick Troubleshooting

### Command Not Found
```bash
# If gao-dev command not found, use:
python -m gao_dev.cli.commands --help

# Or reinstall:
pip install -e .
```

### API Key Issues
```bash
# Set API key for benchmarks
export ANTHROPIC_API_KEY=your_key_here  # Linux/Mac
set ANTHROPIC_API_KEY=your_key_here     # Windows

# Verify it's set
echo $ANTHROPIC_API_KEY  # Linux/Mac
echo %ANTHROPIC_API_KEY%  # Windows
```

### Health Check
```bash
# Run health check to verify system
gao-dev health

# Expected output:
# - System health OK
# - Workflows loaded
# - Agents configured
# - Database accessible
```

## Metrics Tracked

### Performance Metrics
- Duration (total, per phase, per story)
- Token usage (input, output, total)
- Cost tracking
- Resource utilization

### Autonomy Metrics
- User intervention count
- Error recovery rate
- Autonomous decision rate
- Clarification requests

### Quality Metrics
- Test coverage percentage
- Type safety score
- Code quality score
- Documentation completeness

### Workflow Metrics
- Story completion rate
- Rework percentage
- Phase transition times
- Success rate

## Project Structure (User Projects)

```
your-project/
├── gao-dev.yaml          # Project configuration
├── docs/                 # Documentation and artifacts
│   ├── PRD.md           # Product Requirements
│   ├── epics.md         # Epic definitions
│   ├── architecture.md  # System architecture
│   └── stories/         # User stories
│       └── epic-1/
│           ├── story-1.1.md
│           └── story-1.2.md
└── src/                  # Your source code
```

## Git Workflow

### Branch Strategy
- `main` - Production-ready code
- `feature/epic-N-name` - Epic-level branches
- `feature/story-N.M-name` - Story-level branches

### Commit Format
```
<type>(<scope>): <description>

<optional body>

Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, refactor, test, chore

## Environment Setup

### Required
- Python 3.11+
- Git
- API key (for autonomous benchmarks)

### Optional
- uv (recommended package manager)
- pytest (for running tests)
- black, ruff, mypy (for code quality)

## Support

### Getting Help
1. Check [INDEX.md](INDEX.md) for documentation hub
2. Read feature-specific README.md files
3. Review [CLAUDE.md](../CLAUDE.md) for comprehensive guide
4. Create GitHub issue for specific questions

### Useful Links
- Documentation Hub: [docs/INDEX.md](INDEX.md)
- Quick Start: [QUICKSTART.md](../QUICKSTART.md)
- Main README: [README.md](../README.md)
- Current Status: [bmm-workflow-status.md](bmm-workflow-status.md)

---

**Pro Tips**:
- Use `gao-dev list-workflows` to see all 55+ available workflows
- Use `gao-dev list-agents` to see all 8 specialized agents
- Check `bmm-workflow-status.md` before starting new work
- Run `gao-dev health` if something seems wrong
- Use benchmarks to test autonomous capabilities end-to-end

---

*Last Updated: 2025-11-06*
*For detailed information, see [INDEX.md](INDEX.md)*
