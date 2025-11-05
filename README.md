# GAO-Dev

**Software Engineering Team for Generative Autonomous Organisation**

GAO-Dev is an autonomous AI development orchestration system that manages the complete software development lifecycle using specialized Claude agents. Transform "simple prompt → production-ready app" into reality through intelligent workflow selection, scale-adaptive routing, and autonomous agent orchestration.

## Features

- **Autonomous Development**: 7 specialized Claude agents (Brian, John, Winston, Sally, Bob, Amelia, Murat)
- **Scale-Adaptive Routing**: Automatically adjusts approach based on project size (Levels 0-4)
- **Workflow Intelligence**: Brian agent for intelligent workflow selection and orchestration
- **Multi-Workflow Sequencing**: Coordinate complex development sequences autonomously
- **Artifact Creation**: Real project files with atomic git commits
- **Sandbox & Benchmarking**: Test and measure autonomous development capabilities
- **Comprehensive Metrics**: Track performance, autonomy, quality, and workflow metrics
- **HTML Reporting**: Professional dashboards with charts, comparisons, and trend analysis
- **Plugin Architecture**: Extensible system for custom agents, workflows, and methodologies
- **Methodology Abstraction**: Support for multiple development methodologies (Adaptive Agile, Simple)
- **Configuration Abstraction**: All agents and prompts in YAML templates (zero hardcoded prompts)
- **55+ Embedded Workflows**: Complete SDLC coverage from analysis to deployment
- **Quality Enforcement**: Built-in quality standards, testing requirements, and phase gates
- **Git Integration**: GitFlow workflows with conventional commits

## Installation

### Quick Setup with uv (Recommended)

**Windows:**
```bash
setup.bat
```

**Unix/Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### From Source (Manual)

```bash
# Clone the repository
cd gao-agile-dev

# Install with uv (recommended)
uv sync
uv pip install -e .

# Or install with pip
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
python -m gao_dev.cli.commands --version
python -m gao_dev.cli.commands --help
```

**See [QUICKSTART.md](QUICKSTART.md) for a detailed getting started guide.**

**See [docs/SETUP.md](docs/SETUP.md) for API key configuration and autonomous benchmark setup.**

## Quick Start

### 1. Initialize a Project

```bash
cd your-project
python -m gao_dev.cli.commands init --name "My Awesome Project"
```

This creates:
- Project structure (`docs/`, `docs/stories/`)
- Configuration file (`gao-dev.yaml`)
- Git repository (if not already initialized)

### 2. Create a PRD (Autonomous)

```bash
python -m gao_dev.cli.commands create-prd --name "My Awesome Project"
```

This spawns **John (Product Manager)** to autonomously create a comprehensive PRD.

### 3. Create System Architecture (Autonomous)

```bash
python -m gao_dev.cli.commands create-architecture --name "My Awesome Project"
```

This spawns **Winston (Technical Architect)** to design the system architecture.

### 4. Create a User Story (Autonomous)

```bash
python -m gao_dev.cli.commands create-story --epic 1 --story 1 --title "User authentication"
```

This spawns **Bob (Scrum Master)** to create a well-defined user story.

### 5. Implement a Story (Autonomous Multi-Agent)

```bash
python -m gao_dev.cli.commands implement-story --epic 1 --story 1
```

This coordinates **Bob** and **Amelia (Developer)** through the full implementation workflow:
- Story verification
- Feature branch creation
- Implementation with tests
- Code review
- Merge and completion

### 6. Run Benchmarks (Test Autonomous Capabilities)

```bash
# Set API key
export ANTHROPIC_API_KEY=your_key_here  # Linux/Mac
set ANTHROPIC_API_KEY=your_key_here     # Windows

# Run a benchmark
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml

# View results
python -m gao_dev.cli.commands metrics report list
python -m gao_dev.cli.commands metrics report open <report-id>
```

### 7. Utility Commands

```bash
# Check system health
python -m gao_dev.cli.commands health

# List available workflows (55+)
python -m gao_dev.cli.commands list-workflows

# List available agents
python -m gao_dev.cli.commands list-agents

# Sandbox management
python -m gao_dev.cli.commands sandbox list
python -m gao_dev.cli.commands sandbox status
```

## Available Commands

### Core Commands

```bash
python -m gao_dev.cli.commands --version                    # Show version
python -m gao_dev.cli.commands --help                       # Show help
python -m gao_dev.cli.commands init --name "Project"        # Initialize project
python -m gao_dev.cli.commands health                       # Run health check
python -m gao_dev.cli.commands list-workflows               # List all workflows (55+)
python -m gao_dev.cli.commands list-agents                  # List all agents
python -m gao_dev.cli.commands version                      # Show detailed version info
```

### Autonomous Development Commands

```bash
python -m gao_dev.cli.commands create-prd --name "Project"            # John creates PRD
python -m gao_dev.cli.commands create-architecture --name "Project"   # Winston creates architecture
python -m gao_dev.cli.commands create-story --epic 1 --story 1        # Bob creates story
python -m gao_dev.cli.commands implement-story --epic 1 --story 1     # Bob + Amelia implement
python -m gao_dev.cli.commands execute <workflow-name>                # Execute any workflow
```

### Sandbox & Benchmarking Commands

```bash
python -m gao_dev.cli.commands sandbox init <project-name>            # Create sandbox project
python -m gao_dev.cli.commands sandbox list                           # List all projects
python -m gao_dev.cli.commands sandbox clean <project-name>           # Clean/reset project
python -m gao_dev.cli.commands sandbox delete <project-name>          # Delete project
python -m gao_dev.cli.commands sandbox status                         # System status
python -m gao_dev.cli.commands sandbox run <benchmark.yaml>           # Run benchmark
```

### Metrics & Reporting Commands

```bash
python -m gao_dev.cli.commands metrics export <run-id> --format csv   # Export metrics
python -m gao_dev.cli.commands metrics report run <run-id>            # Generate HTML report
python -m gao_dev.cli.commands metrics report compare <id1> <id2>     # Compare two runs
python -m gao_dev.cli.commands metrics report trend <config>          # Trend analysis
python -m gao_dev.cli.commands metrics report list                    # List all reports
python -m gao_dev.cli.commands metrics report open <report-id>        # Open in browser
```

## Project Structure

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

## Configuration

Edit `gao-dev.yaml` in your project root:

```yaml
# Project Configuration
project_name: "My Project"
project_level: 2
output_folder: "docs"
dev_story_location: "docs/stories"

# Methodology
methodology: "adaptive_agile"  # or "simple"

# Git Settings
git_auto_commit: true
git_branch_prefix: "feature/epic"

# Quality Settings
qa_enabled: true
test_coverage_threshold: 80
```

## The 7 Specialized Agents

### 1. Brian - Workflow Coordinator (NEW!)
**Role**: Intelligent workflow selection and orchestration
**Capability**: Scale-adaptive routing (Levels 0-4), clarification dialogs, multi-workflow sequencing
**Use For**: Initial project analysis, workflow selection, coordinating complex sequences

### 2. John - Product Manager
**Role**: PRDs, feature definition, prioritization
**Use For**: Creating PRDs, defining epics, prioritizing work

### 3. Winston - Technical Architect
**Role**: System architecture, technical specifications
**Use For**: Architecture design, technical decisions

### 4. Sally - UX Designer
**Role**: User experience, wireframes, design
**Use For**: UX design, user flows, interface design

### 5. Bob - Scrum Master
**Role**: Story creation and management, team coordination
**Use For**: Creating stories, managing sprint, status tracking

### 6. Amelia - Software Developer
**Role**: Implementation, code reviews, testing
**Use For**: Implementing features, writing code, code reviews

### 7. Murat - Test Architect
**Role**: Test strategies, quality assurance
**Use For**: Test strategies, test plans, quality standards

## Scale-Adaptive Routing

GAO-Dev intelligently adapts its approach based on project scale:

**Level 0: Chore** (<1 hour) - Direct execution, no formal planning
**Level 1: Bug Fix** (1-4 hours) - Minimal planning, direct fix
**Level 2: Small Feature** (1-2 weeks) - PRD → Architecture → Stories → Implementation
**Level 3: Medium Feature** (1-2 months) - Full workflow with analysis
**Level 4: Greenfield Application** (2-6 months) - Comprehensive methodology

## Available Workflows (55+)

### Phase 1: Analysis
- Product brief
- Research & discovery
- Brainstorming sessions

### Phase 2: Planning
- Product Requirements Document (PRD)
- Game Design Document (GDD)
- Technical Specifications
- Epic definitions

### Phase 3: Solutioning
- System architecture
- API design
- Data models
- Technical design

### Phase 4: Implementation
- Story creation
- Story development
- Code review
- Testing & QA
- Deployment

## Architecture

GAO-Dev uses a clean, layered architecture:

### 1. CLI Layer
User interface for all commands (`gao_dev/cli/`)

### 2. Orchestrator Layer
Coordinates agent execution and workflow sequencing (`gao_dev/orchestrator/`)
- GAODevOrchestrator: Main orchestration engine
- Agent definitions and configurations
- Workflow result handling

### 3. Methodology Layer
Supports multiple development methodologies (`gao_dev/methodologies/`)
- **Adaptive Agile**: Scale-adaptive routing with intelligent workflow selection
- **Simple**: Lightweight methodology for quick projects
- **Plugin Support**: Custom methodologies via plugin system

### 4. Core Services Layer
Business logic and infrastructure (`gao_dev/core/`)
- **Workflow Management**: Registry, executor, strategies
- **State Management**: Project state, story tracking
- **Git Management**: Branch creation, commits, merges
- **Event System**: Event bus for cross-component communication
- **Repositories**: File-based storage
- **Services**: Quality gates, story lifecycle
- **Factories**: Agent instantiation

### 5. Plugin System
Extensibility layer (`gao_dev/plugins/`)
- Agent plugins
- Workflow plugins
- Methodology plugins
- Permission management
- Resource monitoring

### 6. Sandbox & Benchmarking System
Testing and validation layer (`gao_dev/sandbox/`)
- **Sandbox Manager**: Isolated project environments
- **Benchmark Runner**: Automated testing with orchestration
- **Metrics Collection**: Performance, autonomy, quality tracking
- **Reporting**: HTML dashboards with charts and trends
- **Git Integration**: Commit management, artifact parsing

### 7. Agent Layer
Specialized Claude agents (`gao_dev/agents/`)
- Base agent implementations
- Agent personas (Brian, John, Winston, Sally, Bob, Amelia, Murat)

### 8. Embedded Assets
Zero external dependencies
- 55+ workflows across all SDLC phases
- Agent persona definitions
- Quality checklists
- Default configurations

## Sandbox & Benchmarking

The sandbox system enables comprehensive testing of autonomous capabilities:

### Features

**Isolated Environments**: Each project runs in its own sandbox
**Benchmark Configurations**: YAML/JSON configs define test scenarios
**Multi-Phase Orchestration**: Coordinates complex workflow sequences
**Comprehensive Metrics**: Tracks performance, autonomy, quality, workflow
**HTML Reporting**: Professional dashboards with charts and trends
**Success Validation**: Automated checking against criteria
**Real Artifacts**: Creates actual project files with git history

### Running Benchmarks

```bash
# 1. Set API key
export ANTHROPIC_API_KEY=your_key_here

# 2. Run a benchmark
python -m gao_dev.cli.commands sandbox run sandbox/benchmarks/workflow-driven-todo.yaml

# 3. View results
python -m gao_dev.cli.commands metrics report list
python -m gao_dev.cli.commands metrics report open <report-id>

# 4. Inspect artifacts
cd sandbox/projects/<project-name>/
git log --oneline
```

### Example Benchmark Config

```yaml
# sandbox/benchmarks/workflow-driven-todo.yaml
name: "Workflow-Driven Todo App"
description: "Build complete todo app autonomously"

initial_prompt: |
  Build a todo application with:
  - User authentication
  - CRUD operations for tasks
  - Task filtering and search
  - API + Frontend
  - Tests with >80% coverage

success_criteria:
  - Application runs successfully
  - All tests pass
  - Test coverage >80%
  - Clean git history
  - Documentation complete

scale_level: 2  # Small feature (3-8 stories)
```

## Metrics & Reporting

### Metrics Collected

**Performance Metrics**:
- Duration (total, per phase, per story)
- Token usage (input, output, total)
- Cost tracking
- Resource utilization

**Autonomy Metrics**:
- User intervention count
- Error recovery rate
- Autonomous decision rate
- Clarification requests

**Quality Metrics**:
- Test coverage percentage
- Type safety score
- Code quality score
- Documentation completeness

**Workflow Metrics**:
- Story completion rate
- Rework percentage
- Phase transition times
- Success rate

### Report Types

**Run Report**: Detailed analysis of single benchmark run
**Comparison Report**: Side-by-side comparison of two runs
**Trend Report**: Multi-run analysis with statistical trends

All reports include:
- Interactive charts (timeline, bar, gauge, radar)
- Statistical analysis
- Recommendations
- Export capabilities

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gao_dev --cov-report=html

# Run specific test category
pytest -m integration
pytest -m "not slow"
```

Current: **400+ tests passing** across all modules

### Code Quality

```bash
# Format code
black gao_dev tests

# Lint code
ruff check gao_dev tests

# Type check
mypy gao_dev
```

### Building Package

```bash
python -m build
pip install dist/gao_dev-*.whl
```

## Plugin Development

GAO-Dev supports extensibility through plugins:

### Plugin Types

- **Agent Plugins**: Add new agents or extend existing ones
- **Workflow Plugins**: Add custom workflows or modify behavior
- **Methodology Plugins**: Add custom development methodologies

See [docs/plugin-development-guide.md](docs/plugin-development-guide.md) for complete guide.

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: Comprehensive guide for Claude Code sessions
- **[QUICKSTART.md](QUICKSTART.md)**: Detailed getting started guide
- **[docs/SETUP.md](docs/SETUP.md)**: API key configuration and setup
- **[docs/BENCHMARK_STANDARDS.md](docs/BENCHMARK_STANDARDS.md)**: Benchmark standards and best practices
- **[docs/plugin-development-guide.md](docs/plugin-development-guide.md)**: Plugin development guide
- **[docs/bmm-workflow-status.md](docs/bmm-workflow-status.md)**: Current development status
- **[docs/features/](docs/features/)**: Feature-specific documentation

## About GAO

**GAO (Generative Autonomous Organisation)** is a parent organization exploring autonomous operations through AI agents across multiple domains.

**GAO-Dev** is the software engineering team within GAO. The `gao-dev` command prefix distinguishes development team commands from higher-level GAO organizational commands.

Future GAO teams may include:
- `gao init` - Initialize a new GAO organization
- `gao-dev` - Development team (this project)
- `gao-ops` - Operations team
- `gao-research` - Research team

## Current Status

**Version**: 1.0.0
**Status**: Production-ready, core architecture complete

**Recent Achievements**:
- Epic 10: Prompt & Agent Configuration Abstraction (COMPLETE)
- Epic 7.2: Workflow-Driven Core Architecture (COMPLETE)
- Epic 6: Legacy Cleanup & God Class Refactoring (COMPLETE)
- Epics 1-5: Sandbox & Benchmarking System (COMPLETE)

**Latest Achievement - Epic 10**:
- All 8 agents defined in structured YAML configuration files
- Zero hardcoded prompts (200+ lines extracted to YAML templates)
- PromptLoader with @file: and @config: reference support
- Enhanced plugin system for custom agents and prompts
- 100% backwards compatible with existing workflows
- Foundation for domain-specific teams (gao-ops, gao-legal, gao-research)

**Next Steps**:
- Real-world testing with workflow-driven benchmarks
- Continuous improvement based on benchmark learnings
- Create domain-specific agent teams using new abstraction

## Acknowledgments

Built on proven patterns from BMAD Method while evolving the approach for modern autonomous AI orchestration within the GAO framework.

## License

MIT License - see LICENSE file for details

## Contributing

This is a proof-of-concept implementation. Contributions and feedback are welcome!

## Support

For issues and feature requests, please create an issue in the repository.

---

**Built with GAO-Dev - Autonomous AI Development Orchestration**

*Transform "simple prompt → production-ready app" into reality*
