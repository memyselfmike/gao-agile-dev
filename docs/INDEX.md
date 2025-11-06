# GAO-Dev Documentation Index

**Last Updated**: 2025-11-06

This is the master navigation hub for all GAO-Dev documentation.

## Core Documentation

### Getting Started
- [README.md](../README.md) - Project overview and quick start
- [QUICKSTART.md](../QUICKSTART.md) - Detailed getting started guide
- [CLAUDE.md](../CLAUDE.md) - Guide for Claude Code sessions
- [SETUP.md](SETUP.md) - API key configuration and setup

### Standards & Guidelines
- [BENCHMARK_STANDARDS.md](BENCHMARK_STANDARDS.md) - Benchmarking standards and best practices
- [QA_STANDARDS.md](QA_STANDARDS.md) - Quality assurance standards and testing requirements
- [BMAD_METHODOLOGY.md](BMAD_METHODOLOGY.md) - BMAD methodology reference

### Status & Planning
- [bmm-workflow-status.md](bmm-workflow-status.md) - Current workflow status (ACTIVE)
- [sprint-status.yaml](sprint-status.yaml) - Sprint tracking and story status

## Feature Documentation

### Active Features

**[Document Lifecycle System](features/document-lifecycle-system/)** (Epics 12-17)
- [PRD](features/document-lifecycle-system/PRD.md) | [Architecture](features/document-lifecycle-system/ARCHITECTURE.md) | [Epics](features/document-lifecycle-system/epics.md)
- Status: COMPLETE & ACTIVE (using it now!)
- Deliverables:
  - Epic 12: Document Lifecycle Management (state tracking, metadata, relationships)
  - Epic 13: Meta-Prompt System (@doc:, @query:, @context:, @checklist: references)
  - Epic 14: Checklist Plugin System (21 core checklists, YAML-based)
  - Epic 15: State Tracking Database (SQLite schema, bidirectional markdown sync)
  - Epic 16: Context Persistence Layer (ContextCache, WorkflowContext, lineage tracking)
  - Epic 17: Context System Integration (full integration, database unification, agent API)

### Planned Features

**[Agent Provider Abstraction](features/agent-provider-abstraction/)** (Epic 11)
- [PRD](features/agent-provider-abstraction/PRD.md) | [Architecture](features/agent-provider-abstraction/ARCHITECTURE.md) | [Epics](features/agent-provider-abstraction/epics.md)
- Status: DOCUMENTED (not yet implemented)
- Goal: Multi-provider support (Claude Code, OpenCode, DirectAPI, custom providers)
- Timeline: 4 weeks (94 story points across 16 stories)

### Archived Features (Completed)

**[Sandbox System](features/sandbox-system/)** (Epics 1-5, 7-7.2)
- [PRD](features/sandbox-system/PRD.md) | [Architecture](features/sandbox-system/ARCHITECTURE.md) | [Epics](features/sandbox-system/epics.md)
- Status: COMPLETE (2025-10-29)
- Deliverables:
  - Epic 1: Sandbox Infrastructure (CLI commands, project management)
  - Epic 2: Boilerplate Integration (template system)
  - Epic 3: Metrics Collection System (performance, autonomy, quality tracking)
  - Epic 4: Benchmark Runner (orchestration, progress tracking, validation)
  - Epic 5: Reporting & Visualization (HTML dashboards, charts, trends)
  - Epic 7: Autonomous Artifact Creation (real project files, git integration)
  - Epic 7.2: Workflow-Driven Core Architecture (Brian agent, scale-adaptive routing)

**[Prompt Abstraction](features/prompt-abstraction/)** (Epic 10)
- [PRD](features/prompt-abstraction/PRD.md) | [Architecture](features/prompt-abstraction/ARCHITECTURE.md) | [Epics](features/prompt-abstraction/epics.md)
- Status: COMPLETE (2025-11-03)
- Deliverables:
  - All 8 agents in YAML format
  - Zero hardcoded prompts (200+ lines extracted)
  - PromptLoader with @file: and @config: references
  - JSON Schema validation
  - Enhanced plugin system
  - 100% backwards compatibility

**[Core System Refactor](features/core-gao-dev-system-refactor/)** (Epic 6)
- [PRD](features/core-gao-dev-system-refactor/PRD.md) | [Architecture](features/core-gao-dev-system-refactor/ARCHITECTURE.md) | [Epics](features/core-gao-dev-system-refactor/epics.md)
- Status: COMPLETE (2025-10-28)
- Deliverables:
  - Clean architecture with service layer
  - Facade pattern for managers
  - Model-driven design
  - All services <200 LOC
  - SOLID principles throughout

## Reference Materials

### BMAD Method
- [BMAD Method Reference](../bmad/) - Reference implementation (external)
- Workflow templates and patterns
- Agile methodology guidelines

### Examples & Guides
- [Plugin Development Guide](plugin-development-guide.md) - Create custom agents, workflows, and methodologies
- [Benchmark Examples](../sandbox/benchmarks/) - Example benchmark configurations
- [Example Plugins](examples/) - Sample plugin implementations

## Archived Documentation

### Session Notes
- [archive/session-notes/](archive/session-notes/) - Historical session summaries
- Development progress and decisions
- Useful for understanding project history

### Historical Analysis
- [archive/historical-analysis/](archive/historical-analysis/) - Obsolete analysis documents
- Previous architectural explorations
- Preserved for reference only

## Quick Navigation

### I want to...

**Get started with GAO-Dev**
- Start with [QUICKSTART.md](../QUICKSTART.md)
- Then read [SETUP.md](SETUP.md) for API key configuration

**Understand the current status**
- Check [bmm-workflow-status.md](bmm-workflow-status.md)
- Review [sprint-status.yaml](sprint-status.yaml)

**Learn about a specific feature**
- Navigate to [features/](features/) directory
- Read the feature's README.md for overview
- Then PRD.md and ARCHITECTURE.md for details

**Develop a plugin**
- Read [plugin-development-guide.md](plugin-development-guide.md)
- Review example plugins in [examples/](examples/)
- Check agent YAML schema in feature documentation

**Run benchmarks**
- Read [BENCHMARK_STANDARDS.md](BENCHMARK_STANDARDS.md)
- Check [SETUP.md](SETUP.md) for API key setup
- See examples in [sandbox/benchmarks/](../sandbox/benchmarks/)

**Work on a story**
- Check [bmm-workflow-status.md](bmm-workflow-status.md) for current epic
- Navigate to feature directory for story details
- Follow story acceptance criteria and definition of done

**Understand the architecture**
- Read main [README.md](../README.md) for overview
- Review [CLAUDE.md](../CLAUDE.md) for detailed system guide
- Check feature ARCHITECTURE.md for component details

## Documentation Standards

### File Organization
- **Features**: Each feature has its own directory under `features/`
- **Structure**: Each feature follows PRD → Architecture → Epics → Stories
- **Status**: README.md in each feature indicates current status
- **Archive**: Completed features remain for reference

### Naming Conventions
- **Feature Directories**: lowercase-with-hyphens (e.g., `document-lifecycle-system`)
- **Documentation Files**: UPPERCASE.md for major docs (e.g., `PRD.md`, `ARCHITECTURE.md`)
- **Story Files**: lowercase with epic and story numbers (e.g., `story-12.1.md`)

### Status Indicators
- ACTIVE: Currently being used in the system
- COMPLETE: Finished and validated
- DOCUMENTED: Planning complete, ready to implement
- DRAFT: Work in progress
- ARCHIVED: Complete and preserved for reference

## Contributing to Documentation

### When to Update
- Update [bmm-workflow-status.md](bmm-workflow-status.md) after completing epics/stories
- Update feature README.md when status changes
- Update this INDEX.md when adding new features or major sections
- Keep dates current in "Last Updated" sections

### Documentation Checklist
- [ ] Feature has README.md with status and links
- [ ] PRD.md exists and is complete
- [ ] ARCHITECTURE.md exists and is complete
- [ ] All stories documented in stories/ directory
- [ ] Feature linked from this INDEX.md
- [ ] Status accurate in bmm-workflow-status.md

## Support & Help

### Getting Help
- Check this INDEX.md for relevant documentation
- Read feature-specific README.md files
- Review CLAUDE.md for comprehensive system guide
- Create GitHub issue for specific questions

### Reporting Issues
- Documentation gaps: Create issue with "documentation" label
- Broken links: Create issue with "bug" label
- Unclear content: Create issue with "enhancement" label

---

**Navigation Tips**:
- Start with [QUICKSTART.md](../QUICKSTART.md) if new to GAO-Dev
- Check [bmm-workflow-status.md](bmm-workflow-status.md) for current development status
- Feature docs follow standard structure: README → PRD → Architecture → Epics → Stories
- Archived features are complete but documentation is preserved for reference
- Use Ctrl+F to search for specific topics in this index

---

*Last Updated: 2025-11-06*
*Maintained by GAO-Dev Team*
