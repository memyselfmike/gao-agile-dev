# GAO-Dev Documentation

This directory contains all documentation for the GAO-Dev project.

## Structure

```
docs/
├── README.md                           # This file
├── SETUP.md                            # Setup guide (API keys, config)
├── sandbox-autonomous-benchmark-guide.md # Complete benchmarking guide
├── features/                           # Feature development documentation
│   └── sandbox-system/                 # Sandbox & Benchmarking System
│       ├── PRD.md                      # Product Requirements
│       ├── ARCHITECTURE.md             # Technical architecture
│       ├── BOILERPLATE_INFO.md         # Boilerplate analysis
│       ├── PROJECT_BRIEF.md            # Initial brief
│       ├── NEXT_STEPS.md               # Action items
│       ├── epics.md                    # Epic breakdown
│       └── stories/                    # User stories
│           └── epic-1/
│               └── story-1.1.md
└── (future: project-level docs like original PRD, roadmap, etc.)
```

## Organization Principles

### 1. Feature Documentation (`features/`)

Each major feature gets its own directory with:
- **PRD.md**: Product requirements
- **ARCHITECTURE.md**: Technical design
- **epics.md**: Epic breakdown
- **stories/**: User stories organized by epic

**Example**: `features/sandbox-system/` contains all planning docs for the sandbox feature.

### 2. Sandbox Workspace (`../sandbox/`)

**Important**: The `sandbox/` directory is NOT for documentation!

It's a workspace where test projects are created autonomously by agents.

**For sandbox system documentation**, see `features/sandbox-system/`
**For sandbox test projects**, see `../sandbox/projects/`

### 3. Project-Level Docs (Future)

As the project grows, we'll add:
- Main project PRD
- Overall roadmap
- Contribution guidelines
- Architecture overview
- Agent personas guide

## Documentation Workflow

When developing a new feature:

1. **Planning Phase**:
   - Create `docs/features/<feature-name>/`
   - Add PRD.md, ARCHITECTURE.md
   - Define epics and stories

2. **Implementation Phase**:
   - Reference docs while coding
   - Update docs as design evolves
   - Mark stories as completed

3. **Completion Phase**:
   - Ensure docs match implementation
   - Add to main project docs if needed
   - Archive or maintain feature docs

## Current Features

### Sandbox & Benchmarking System
**Status**: Planning complete, ready for implementation
**Location**: `features/sandbox-system/`
**Purpose**: Test and measure GAO-Dev's autonomous capabilities

**Key Documents**:
- [PRD](features/sandbox-system/PRD.md)
- [Architecture](features/sandbox-system/ARCHITECTURE.md)
- [Epics](features/sandbox-system/epics.md)
- [Story 1.1](features/sandbox-system/stories/epic-1/story-1.1.md)

## Finding Information

**Looking for...** | **Check...**
--- | ---
**Getting Started** |
Setup & API key config | [SETUP.md](SETUP.md)
Autonomous benchmark guide | [sandbox-autonomous-benchmark-guide.md](sandbox-autonomous-benchmark-guide.md)
**Sandbox System** |
Sandbox system requirements | `features/sandbox-system/PRD.md`
Sandbox architecture | `features/sandbox-system/ARCHITECTURE.md`
Sandbox stories | `features/sandbox-system/stories/`
**Workspace & Projects** |
Sandbox test projects | `../sandbox/projects/`
Benchmark configs | `../sandbox/benchmarks/`
How to use sandbox | `../sandbox/README.md`

## Contributing to Docs

When adding documentation:

1. **Feature docs**: Place in `features/<feature-name>/`
2. **User guides**: Place in root docs or appropriate subdirectory
3. **Code docs**: Keep with code (docstrings, inline comments)
4. **API docs**: Generate from code (future)

## Conventions

- Use Markdown for all docs
- Include table of contents for long docs
- Link between related docs
- Keep docs updated with code changes
- Use consistent formatting

---

**For main project information**, see: `../README.md`
**For sandbox workspace**, see: `../sandbox/README.md`
**For source code**, see: `../gao_dev/`
