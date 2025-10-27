# GAO-Dev Quickstart Guide

This guide will help you get GAO-Dev up and running in minutes.

## Prerequisites

- **Python 3.11+**: Required for GAO-Dev
- **uv**: Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git**: For version control
- **Claude Max Account**: Logged in session (no API key required)

## Installation

### Option 1: Using uv (Recommended)

**Windows:**
```bash
# Install uv (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Run setup script
setup.bat
```

**Unix/Linux/Mac:**
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Option 2: Using pip

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# Unix/Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e .
```

## Quick Start

### 1. Initialize a New Project

```bash
# Navigate to your project directory
cd /path/to/your/project

# Initialize GAO-Dev
gao-dev init --name "My Awesome Project"
```

This creates:
- `docs/` folder structure
- `gao-dev.yaml` configuration file
- Git repository (if not already initialized)

### 2. Create a Product Requirements Document

```bash
gao-dev create-prd --name "My Awesome Project"
```

This delegates to **John (Product Manager)** who will:
- Use the PRD workflow
- Create a comprehensive PRD.md
- Include executive summary, features, success metrics
- Save to `docs/PRD.md`
- Commit the file

### 3. Create System Architecture

```bash
gao-dev create-architecture --name "My Awesome Project"
```

This delegates to **Winston (Technical Architect)** who will:
- Read the PRD
- Use the architecture workflow
- Create system design documentation
- Save to `docs/architecture.md`
- Commit the file

### 4. Create a User Story

```bash
gao-dev create-story --epic 1 --story 1 --title "User authentication"
```

This delegates to **Bob (Scrum Master)** who will:
- Read the epic definition
- Use the create-story workflow
- Create story file with acceptance criteria
- Save to `docs/stories/epic-1/story-1.1.md`
- Set status to 'Draft'
- Commit the file

### 5. Implement a Story

```bash
gao-dev implement-story --epic 1 --story 1
```

This coordinates the full workflow:
1. **Bob** verifies story is ready
2. **Amelia (Developer)** implements the story:
   - Creates feature branch
   - Implements all acceptance criteria
   - Writes tests
   - Commits code
3. **Amelia** performs code review
4. **Bob** verifies completion and merges

## Available Commands

```bash
# View all commands
gao-dev --help

# List available workflows
gao-dev list-workflows

# List available agents
gao-dev list-agents

# Run health check
gao-dev health

# View version
gao-dev version
```

## Autonomous Commands

These commands use the GAO-Dev orchestrator to spawn specialized agents:

- `gao-dev create-prd --name "<project>"` - Create PRD (uses John)
- `gao-dev create-architecture --name "<project>"` - Create architecture (uses Winston)
- `gao-dev create-story --epic N --story M` - Create user story (uses Bob)
- `gao-dev implement-story --epic N --story M` - Full implementation workflow (uses Bob + Amelia)
- `gao-dev run-health-check` - Autonomous system check

## Agent Team

GAO-Dev includes 7 specialized AI agents:

1. **Mary** (Business Analyst) - Analysis, research, requirements
2. **John** (Product Manager) - PRDs, features, prioritization
3. **Winston** (Technical Architect) - System design, tech specs
4. **Sally** (UX Designer) - User experience, wireframes
5. **Bob** (Scrum Master) - Story management, coordination
6. **Amelia** (Software Developer) - Implementation, code reviews
7. **Murat** (Test Architect) - Test strategy, quality assurance

## Configuration

Edit `gao-dev.yaml` in your project root:

```yaml
project_name: "My Awesome Project"
project_level: 2
output_folder: "docs"
dev_story_location: "docs/stories"
git_auto_commit: true
git_branch_prefix: "feature/epic"
qa_enabled: true
```

## Workflow Phases

GAO-Dev organizes work into 5 phases:

- **Phase 0**: Meta (project setup, planning)
- **Phase 1**: Analysis (business analysis, research)
- **Phase 2**: Planning (PRDs, epics, roadmaps)
- **Phase 3**: Solutioning (architecture, design, UX)
- **Phase 4**: Implementation (stories, development, testing)

## Example: Complete Project Setup

```bash
# 1. Initialize project
gao-dev init --name "E-commerce Platform"

# 2. Create PRD
gao-dev create-prd --name "E-commerce Platform"

# 3. Create architecture
gao-dev create-architecture --name "E-commerce Platform"

# 4. Create first story
gao-dev create-story --epic 1 --story 1 --title "User registration"

# 5. Implement story
gao-dev implement-story --epic 1 --story 1

# 6. Check health
gao-dev health
```

## Troubleshooting

### Command not found: gao-dev

Make sure you've activated your virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Unix/Linux/Mac
source .venv/bin/activate
```

### Import errors

Reinstall in development mode:
```bash
pip install -e .
# or with uv:
uv pip install -e .
```

### Git errors

Ensure Git is installed and configured:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Next Steps

1. Explore the [full documentation](README.md)
2. Review [agent personas](gao_dev/agents/)
3. Check out [workflow templates](gao_dev/workflows/)
4. Join the community (coming soon)

## Support

- Documentation: [README.md](README.md)
- Issues: https://github.com/gao-org/gao-dev/issues
- Discussions: https://github.com/gao-org/gao-dev/discussions

---

**Built with Claude Agent SDK** | Part of the **GAO** (Generative Autonomous Organisation) ecosystem
