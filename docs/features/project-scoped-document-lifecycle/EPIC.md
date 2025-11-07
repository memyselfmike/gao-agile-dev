---
document:
  type: "epic"
  state: "active"
  created: "2025-11-06"
  last_modified: "2025-11-06"
  author: "Bob"
  feature: "project-scoped-document-lifecycle"
  epic: 20
  story: null
  related_documents:
    - "DOCUMENT_LIFECYCLE_ARCHITECTURE_FIX.md"
  replaces: null
  replaced_by: null
---

# Epic 20: Project-Scoped Document Lifecycle

**Project**: GAO-Dev Project-Scoped Document Lifecycle
**Version**: 1.0.0
**Epic Number**: 20
**Status**: Active
**Priority**: P0 (Critical)
**Owner**: Amelia (Developer)
**Estimated Duration**: 1.5-2 weeks
**Created**: 2025-11-06

---

## Executive Summary

The document lifecycle system was incorrectly implemented as a GAO-Dev-global system, storing all documentation metadata in a centralized database at `.gao-dev/documents.db` in the GAO-Dev project directory. This epic refactors the system to be project-scoped, where each project managed BY GAO-Dev has its own `.gao-dev/` directory containing project-specific documentation, context, and metadata that persists across sessions.

**Problem**: Currently, the document lifecycle system operates on GAO-Dev itself instead of the projects being managed, causing context isolation issues and preventing proper multi-project support.

**Solution**: Refactor to project-scoped architecture where each sandbox project (and eventually all projects) has its own `.gao-dev/` directory with isolated documentation tracking.

---

## Description

This epic addresses a fundamental architectural flaw in the document lifecycle system. Currently:

1. **Wrong Scope**: All document tracking happens in `<gao-dev-repo>/.gao-dev/documents.db`
2. **Hard-coded Paths**: CLI commands use `Path.cwd()` which points to GAO-Dev, not target projects
3. **No Integration**: SandboxManager and Orchestrator don't initialize project-scoped document lifecycle
4. **Poor Portability**: Project documentation context is not portable with the project

After this epic, each project will have:
- Its own `.gao-dev/` directory with `documents.db`
- Isolated documentation context
- Portable documentation that moves with the project
- Proper integration with SandboxManager and Orchestrator

---

## Goals and Objectives

### Primary Goals

1. **Project Isolation**: Each project has its own `.gao-dev/` directory with complete isolation
2. **Correct Integration**: SandboxManager and Orchestrator properly initialize project-scoped lifecycle
3. **CLI Project Awareness**: All lifecycle commands detect and operate on correct project
4. **Portability**: Documentation context persists and can be moved with projects

### Secondary Goals

1. **Consistency**: Same structure for all projects (greenfield, brownfield, sandbox)
2. **Backward Compatibility**: Minimal disruption to existing functionality
3. **Clear Documentation**: Updated guides and migration path

---

## Success Criteria

### Must Have

- ✅ Each sandbox project has its own `.gao-dev/documents.db`
- ✅ SandboxManager initializes `.gao-dev/` structure on project creation
- ✅ Orchestrator uses project-scoped document lifecycle
- ✅ CLI commands detect project root and operate on correct database
- ✅ Multiple projects can exist simultaneously without interference
- ✅ All existing tests pass with new architecture

### Should Have

- ✅ Project directories are portable (can be moved/copied)
- ✅ Clear migration documentation
- ✅ Updated CLAUDE.md with project-scoped architecture
- ✅ CLI `--project` option for explicit targeting

### Nice to Have

- ✅ Migration script for any existing centralized data
- ✅ Enhanced error messages for project detection
- ✅ Metrics tracking per-project document lifecycle operations

---

## Story Breakdown

### Phase 1: Core Refactoring (High Priority)

**Goal**: Make document lifecycle system project-aware

#### Story 20.1: Create ProjectDocumentLifecycle Factory Class
- **Effort**: 3 story points
- **Description**: Create factory class for initializing project-scoped document lifecycle components
- **Key Deliverables**:
  - `ProjectDocumentLifecycle` factory class
  - Project context added to core components
  - Unit tests for isolated registries

#### Story 20.2: Update SandboxManager Integration
- **Effort**: 3 story points
- **Description**: Initialize `.gao-dev/` structure when creating sandbox projects
- **Key Deliverables**:
  - `SandboxManager.create_project()` initializes document lifecycle
  - `ProjectLifecycleService` integration
  - Integration tests for project creation

#### Story 20.3: Update Orchestrator Integration
- **Effort**: 3 story points
- **Description**: Initialize project-scoped document lifecycle in orchestrator
- **Key Deliverables**:
  - `GAODevOrchestrator` uses `ProjectDocumentLifecycle`
  - Document manager passed to workflow coordinator
  - Benchmark tests with document tracking

### Phase 2: CLI Updates (Medium Priority)

**Goal**: Update CLI commands to be project-aware

#### Story 20.4: Add Project Root Detection
- **Effort**: 2 story points
- **Description**: Create utility to detect project root from any directory
- **Key Deliverables**:
  - `detect_project_root()` utility function
  - Looks for `.gao-dev/` or `.sandbox.yaml`
  - Tests for detection from various directories

#### Story 20.5: Update Lifecycle CLI Commands
- **Effort**: 3 story points
- **Description**: Replace `Path.cwd()` with project detection in all lifecycle commands
- **Key Deliverables**:
  - All lifecycle commands use `detect_project_root()`
  - Add `--project` option for explicit targeting
  - Updated help text explaining project scope

### Phase 3: Documentation and Migration (Low Priority)

**Goal**: Clean up and document new architecture

#### Story 20.6: Documentation and Migration
- **Effort**: 2 story points
- **Description**: Update documentation and provide migration path
- **Key Deliverables**:
  - Updated CLAUDE.md with project-scoped architecture
  - Updated plugin development guide
  - Migration script if needed
  - Updated benchmark documentation

---

## Timeline Estimate

| Phase | Stories | Estimated Duration | Dependencies |
|-------|---------|-------------------|--------------|
| Phase 1: Core Refactoring | 3 stories (9 pts) | 4-6 hours | None |
| Phase 2: CLI Updates | 2 stories (5 pts) | 2-3 hours | Phase 1 complete |
| Phase 3: Documentation | 1 story (2 pts) | 1-2 hours | Phase 1-2 complete |
| **Testing & Validation** | - | 2-3 hours | All phases |
| **Total** | **6 stories (16 pts)** | **9-14 hours** | - |

**Expected Completion**: 1.5-2 weeks with parallel development

---

## Dependencies

### Requires (Prerequisites)

- Epic 19: OpenCode SDK Integration (Story 19.4 completed)
- Existing document lifecycle system (`gao_dev/lifecycle/`)
- Sandbox infrastructure (`gao_dev/sandbox/`)
- Orchestrator system (`gao_dev/orchestrator/`)

### Blocks (What depends on this)

- Future multi-project management features
- Brownfield project support
- Project context persistence across sessions
- Proper session state management per-project

### Related Epics

- Epic 1-7: Sandbox & Benchmarking System
- Epic 19: OpenCode SDK Integration
- Future: Multi-project workspace management

---

## Technical Architecture

### Current (Incorrect) Structure

```
gao-agile-dev/                     # GAO-Dev repo
├── .gao-dev/
│   └── documents.db               # WRONG: All projects share this
└── sandbox/projects/
    └── my-todo-app/
        ├── docs/                  # Documents here
        └── src/                   # But tracked in GAO-Dev's .gao-dev/
```

### New (Correct) Structure

```
sandbox/projects/my-todo-app/      # Project root
├── .gao-dev/                      # Project-specific GAO-Dev data
│   ├── documents.db               # Document lifecycle (PROJECT-SCOPED)
│   ├── context.json               # Execution context snapshots
│   ├── session-state.db           # Session state tracking
│   └── metrics/                   # Project-specific metrics
├── .archive/                      # Project-specific archived docs
├── docs/                          # Live documentation
│   ├── PRD.md
│   └── ARCHITECTURE.md
├── src/                           # Application code
└── tests/
```

### Integration Points

**1. SandboxManager**: Initialize `.gao-dev/` on project creation
**2. Orchestrator**: Use project-scoped document lifecycle
**3. CLI Commands**: Detect project root, operate on correct database
**4. Agents**: Automatically track documents in project's `.gao-dev/`

---

## Technical Notes

### Design Principles

1. **Project Isolation**: No cross-contamination between projects
2. **Portability**: `.gao-dev/` directory moves with project
3. **Persistence**: Context survives across sessions
4. **Consistency**: Same structure for all project types

### Key Components

**ProjectDocumentLifecycle Factory**:
```python
class ProjectDocumentLifecycle:
    """Factory for creating project-scoped document lifecycle components."""

    @classmethod
    def initialize(cls, project_root: Path) -> DocumentLifecycleManager:
        """Initialize document lifecycle for a project."""
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        db_path = gao_dev_dir / "documents.db"
        archive_dir = project_root / ".archive"

        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir, project_root)

        return manager
```

**Project Root Detection**:
```python
def detect_project_root() -> Path:
    """Detect project root by looking for .gao-dev/ or .sandbox.yaml."""
    current = Path.cwd()

    for parent in [current, *current.parents]:
        if (parent / ".gao-dev").exists() or (parent / ".sandbox.yaml").exists():
            return parent

    return current  # Default to current directory
```

---

## Impact Analysis

### Breaking Changes

**Medium Impact**:
- Existing `.gao-dev/documents.db` in GAO-Dev repo will be orphaned
- Any code assuming centralized document lifecycle will break
- CLI commands will operate on different database locations

**Mitigation**:
- Document lifecycle is a new feature (Epic 19.4 just completed)
- Minimal production usage so far
- Breaking changes acceptable at this stage of development
- Clear migration documentation provided

### Benefits

**High Value**:
- Correct architecture for multi-project management
- Better isolation and context persistence
- Portable project directories
- Enables brownfield project support
- Consistent with sandbox architecture
- Foundation for future workspace features

---

## Testing Strategy

### Unit Tests

1. **Test**: `DocumentRegistry` with different project paths
2. **Test**: `ProjectDocumentLifecycle.initialize()` creates correct structure
3. **Test**: Isolated registries don't interfere with each other

### Integration Tests

1. **Test**: Create two sandbox projects, verify isolated `.gao-dev/`
2. **Test**: Run benchmark, verify documents in project directory
3. **Test**: Orchestrator with project_root creates project-scoped lifecycle
4. **Test**: CLI commands detect and use correct project

### End-to-End Tests

1. **Test**: Full benchmark run creates project-scoped documentation
2. **Test**: Return to existing project, context loads correctly
3. **Test**: Multiple concurrent benchmarks don't interfere
4. **Test**: Move project directory, documentation still accessible

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing workflows | Medium | Medium | Comprehensive testing, clear migration docs |
| Performance impact | Low | Low | Minimal overhead from multiple databases |
| Migration complexity | Low | Low | Feature is new, minimal data to migrate |
| Detection logic failures | Medium | Medium | Fallback to current directory, clear errors |
| Multi-project race conditions | Low | Medium | Isolated databases prevent interference |

---

## Acceptance Testing Checklist

After implementation, verify:

- [ ] Create sandbox project: `.gao-dev/documents.db` exists in project root
- [ ] Run benchmark: Documents tracked in project's `.gao-dev/`
- [ ] CLI from project directory: Commands operate on correct database
- [ ] CLI with `--project` flag: Can target specific project
- [ ] Multiple projects: No interference between project databases
- [ ] Move project directory: Documentation still accessible
- [ ] Return to project: Full context restored from `.gao-dev/`
- [ ] All existing tests pass
- [ ] Documentation updated

---

## Future Considerations

### Post-Epic Enhancements

1. **Workspace Management**: Support for multi-project workspaces
2. **Cloud Sync**: Sync `.gao-dev/` to cloud storage
3. **Team Collaboration**: Shared project context across team
4. **Analytics**: Cross-project analytics and reporting
5. **Brownfield Support**: Initialize `.gao-dev/` for existing projects

### Related Future Work

- Epic 21: Multi-Project Workspace Management
- Epic 22: Brownfield Project Onboarding
- Epic 23: Team Collaboration Features

---

## References

### Related Documents

- `DOCUMENT_LIFECYCLE_ARCHITECTURE_FIX.md` - Detailed analysis
- Epic 19: OpenCode SDK Integration
- Story 19.4: Integration Testing and Validation
- `gao_dev/lifecycle/` - Document lifecycle implementation
- `gao_dev/sandbox/` - Sandbox manager
- `gao_dev/orchestrator/` - Orchestrator
- CLAUDE.md - Project guide

### Key Files

- `gao_dev/lifecycle/registry.py` - Document registry
- `gao_dev/lifecycle/manager.py` - Document lifecycle manager
- `gao_dev/sandbox/manager.py` - Sandbox manager
- `gao_dev/orchestrator/orchestrator.py` - Orchestrator
- `gao_dev/cli/lifecycle_commands.py` - CLI commands

---

## Stakeholders

- **Primary**: Development team building projects with GAO-Dev
- **Secondary**: Plugin developers extending GAO-Dev
- **Tertiary**: Users managing multiple projects

---

## Definition of Done

- [ ] All 6 stories completed and tested
- [ ] All acceptance criteria met
- [ ] All tests passing (unit, integration, E2E)
- [ ] Documentation updated (CLAUDE.md, plugin guide)
- [ ] Code review completed
- [ ] Migration path documented
- [ ] Epic retrospective completed

---

**Created by**: Bob (Scrum Master)
**Approved by**: [Pending]
**Implementation Start**: 2025-11-06

---

*This epic is part of the GAO-Dev continuous improvement initiative to ensure correct architectural foundations for multi-project management.*
