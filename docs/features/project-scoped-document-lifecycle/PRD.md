# Product Requirements Document: Project-Scoped Document Lifecycle

**Version**: 1.0.0
**Date**: 2025-11-06
**Status**: Draft
**Epic**: TBD
**Owner**: GAO-Dev Team

---

## Executive Summary

### Problem
The document lifecycle system was incorrectly implemented as a GAO-Dev-centric system, storing all documentation metadata in a centralized database at `.gao-dev/documents.db` in the GAO-Dev project directory. This architectural misalignment prevents proper context persistence across sessions, breaks multi-project isolation, and makes project directories non-portable.

### Solution
Refactor the document lifecycle system to be project-scoped, where each project managed BY GAO-Dev has its own `.gao-dev/` directory containing project-specific documentation, context, and metadata that persists across sessions.

### Business Value
- **Multi-Project Support**: Enables GAO-Dev to manage multiple projects simultaneously without interference
- **Context Persistence**: Documentation context persists across sessions, supporting long-running projects
- **Portability**: Project directories become self-contained and can be moved/copied
- **Brownfield Support**: Critical foundation for supporting existing codebases
- **Correct Architecture**: Aligns with sandbox infrastructure and autonomous orchestration patterns

---

## Background

### Current State (GAO-Dev-Centric)
- Single centralized database: `<gao-dev-repo>/.gao-dev/documents.db`
- All projects share the same documentation registry
- CLI commands use `Path.cwd()` which resolves to GAO-Dev development directory
- No integration with `SandboxManager` or `GAODevOrchestrator` project roots
- Archives stored in global `.archive/` directory

### Architectural Misalignment
**What we built**: A centralized document tracking system for GAO-Dev project itself

**What we should have**: A project-scoped document tracking system for projects managed BY GAO-Dev

### Real-World Impact
**Current (Wrong) Behavior**:
```
1. User: "gao-dev sandbox run todo-app.yaml"
2. GAO-Dev creates: sandbox/projects/workflow-driven-todo/
3. Agents create PRD, architecture, stories in: sandbox/projects/workflow-driven-todo/docs/
4. Document lifecycle tracks in: <gao-dev-repo>/.gao-dev/documents.db
5. User comes back later: "gao-dev implement-story --project todo-app --story 2.1"
6. Context is NOT available because it's not in the project directory
```

**Correct Behavior**:
```
1. User: "gao-dev sandbox run todo-app.yaml"
2. GAO-Dev creates: sandbox/projects/workflow-driven-todo/.gao-dev/
3. Agents create PRD, architecture, stories in: sandbox/projects/workflow-driven-todo/docs/
4. Document lifecycle tracks in: sandbox/projects/workflow-driven-todo/.gao-dev/documents.db
5. User comes back later: "gao-dev implement-story --project todo-app --story 2.1"
6. GAO-Dev loads context from: sandbox/projects/workflow-driven-todo/.gao-dev/
7. All documentation, state, and context is available
```

---

## Goals and Objectives

### Primary Goals
1. **Project Isolation**: Each project has completely isolated `.gao-dev/` directory
2. **Context Persistence**: Documentation context persists across sessions
3. **Portability**: Projects can be moved/copied with full context intact
4. **Consistency**: Same structure for all projects (greenfield, brownfield, sandbox, production)
5. **Integration**: Seamless integration with sandbox and orchestrator systems

### Success Metrics
- Each sandbox project has its own `.gao-dev/documents.db`
- Multiple projects can exist simultaneously without interference
- Project directories are portable (can be moved/copied)
- Coming back to a project loads its full documentation context
- 100% of lifecycle operations use project-scoped paths
- Zero cross-project data contamination

---

## Stakeholders

### Primary
- **Development Team**: Needs proper multi-project context management
- **Autonomous Agents**: Rely on persistent documentation context
- **Sandbox System**: Foundation for isolated project environments
- **Users**: Benefit from reliable context across sessions

### Secondary
- **Plugin Developers**: Reference architecture for custom lifecycle systems
- **Future GAO Teams**: Pattern for gao-ops, gao-legal, gao-research

---

## Requirements

### Functional Requirements

#### FR1: Project-Scoped Directory Structure
- **FR1.1**: Each project has `.gao-dev/` directory with isolated database
- **FR1.2**: Project structure includes: documents.db, context.json, session-state.db, metrics/
- **FR1.3**: Archives stored in project-specific `.archive/` directory
- **FR1.4**: Structure consistent across greenfield/brownfield/sandbox projects

#### FR2: Core Component Refactoring
- **FR2.1**: Create `ProjectDocumentLifecycle` factory class for initialization
- **FR2.2**: `DocumentRegistry` uses project-specific database path
- **FR2.3**: `DocumentLifecycleManager` tracks project root context
- **FR2.4**: `ArchivalManager` uses project-specific archive directory

#### FR3: Sandbox Manager Integration
- **FR3.1**: Initialize `.gao-dev/` structure on project creation
- **FR3.2**: `ProjectLifecycleService` includes document lifecycle setup
- **FR3.3**: `ProjectMetadata` tracks document lifecycle version
- **FR3.4**: Project deletion removes `.gao-dev/` directory

#### FR4: Orchestrator Integration
- **FR4.1**: `GAODevOrchestrator` initializes project-scoped document lifecycle
- **FR4.2**: Pass document manager to workflow coordinator
- **FR4.3**: Update context API to include project-scoped document manager
- **FR4.4**: Agents automatically use project-scoped documentation

#### FR5: CLI Project Detection
- **FR5.1**: Implement project root detection (look for `.gao-dev/` or `.sandbox.yaml`)
- **FR5.2**: All lifecycle commands support `--project` flag
- **FR5.3**: Default to detected project root if not specified
- **FR5.4**: Clear error messages when project cannot be detected

#### FR6: Migration Path
- **FR6.1**: Provide migration script for existing centralized data
- **FR6.2**: Support both old and new structure during transition period
- **FR6.3**: Clear documentation for migration process

### Non-Functional Requirements

#### NFR1: Reliability
- Zero cross-project data contamination
- Automatic directory creation on initialization
- Graceful handling of missing `.gao-dev/` directories

#### NFR2: Performance
- Directory initialization: <100ms
- No performance impact on document operations
- Efficient project root detection

#### NFR3: Maintainability
- Clean factory pattern for lifecycle initialization
- Comprehensive logging for debugging
- Type hints throughout (mypy strict mode)
- >85% test coverage for new components

#### NFR4: Compatibility
- Works with existing document lifecycle APIs
- Compatible with all workflow types
- No breaking changes to agent interfaces
- Backward compatible during transition period

---

## Technical Specifications

### Correct Directory Structure
```
sandbox/projects/my-todo-app/          # Project root
├── .gao-dev/                          # Project-specific GAO-Dev data
│   ├── documents.db                   # Document lifecycle database (PROJECT-SCOPED)
│   ├── context.json                   # Execution context snapshots
│   ├── session-state.db               # Session state tracking
│   └── metrics/                       # Project-specific metrics
│       └── runs.db
├── .archive/                          # Project-specific archived docs
│   └── deprecated/
├── docs/                              # Live documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── features/
├── src/                               # Application code
└── tests/
```

### ProjectDocumentLifecycle Factory
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

### Project Root Detection
```python
def detect_project_root() -> Path:
    """Detect project root by looking for .gao-dev/ or .sandbox.yaml."""
    current = Path.cwd()

    # Look for .gao-dev/ or .sandbox.yaml
    for parent in [current, *current.parents]:
        if (parent / ".gao-dev").exists() or (parent / ".sandbox.yaml").exists():
            return parent

    # Default to current directory
    return current
```

### Sandbox Manager Integration
```python
# In sandbox/services/project_lifecycle.py
def create_project(self, name: str, ...) -> ProjectMetadata:
    # ... existing project creation ...

    # Initialize document lifecycle
    from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
    ProjectDocumentLifecycle.initialize(project_dir)

    # ... rest of setup ...
```

### Orchestrator Integration
```python
# In orchestrator/orchestrator.py
def __init__(self, project_root: Path, ...):
    self.project_root = project_root

    # Initialize project-scoped document lifecycle
    self.doc_lifecycle = ProjectDocumentLifecycle.initialize(project_root)

    # Pass to workflow coordinator
    self.workflow_coordinator = workflow_coordinator or WorkflowCoordinator(
        ...,
        doc_manager=self.doc_lifecycle,
    )
```

---

## User Stories

### Story 1.1: Add Project Context to Core Components
**As a** developer
**I want** document lifecycle components to be project-aware
**So that** each project has isolated documentation tracking

**Acceptance Criteria**:
- `ProjectDocumentLifecycle` factory class created
- Factory creates proper directory structure
- `DocumentLifecycleManager` accepts project_root parameter
- Unit tests verify isolation between projects
- Type checking passes

### Story 1.2: Update Sandbox Manager Integration
**As a** sandbox system
**I want** to automatically initialize `.gao-dev/` on project creation
**So that** projects are ready for document lifecycle tracking

**Acceptance Criteria**:
- `SandboxManager.create_project()` initializes `.gao-dev/`
- `ProjectLifecycleService` includes document lifecycle setup
- `ProjectMetadata` tracks document lifecycle version
- Integration tests verify structure creation
- Project deletion removes `.gao-dev/`

### Story 1.3: Update Orchestrator Integration
**As a** orchestrator
**I want** to use project-scoped document lifecycle
**So that** agents work with correct project context

**Acceptance Criteria**:
- `GAODevOrchestrator` initializes project-scoped lifecycle
- Document manager passed to workflow coordinator
- Context API includes project-scoped manager
- Integration tests verify correct usage
- Multiple concurrent projects don't interfere

### Story 2.1: Add Project Root Detection
**As a** CLI system
**I want** to automatically detect the correct project root
**So that** users don't need to specify it every time

**Acceptance Criteria**:
- `detect_project_root()` function created
- Looks for `.gao-dev/` or `.sandbox.yaml` markers
- Walks up directory tree to find root
- Returns current directory if no markers found
- Unit tests cover all detection scenarios

### Story 2.2: Update Lifecycle Commands
**As a** user
**I want** lifecycle CLI commands to work on the correct project
**So that** I can manage documentation from any directory

**Acceptance Criteria**:
- All lifecycle commands use `detect_project_root()`
- `--project` flag supported for override
- Help text explains project scope
- Clear error messages when project not detected
- Integration tests verify correct project targeting

### Story 3.1: Documentation Updates
**As a** developer
**I want** comprehensive documentation for project-scoped architecture
**So that** I understand how to use the system correctly

**Acceptance Criteria**:
- CLAUDE.md updated with project-scoped architecture
- Plugin development guide updated
- Migration guide created (if needed)
- Benchmark documentation updated
- Examples provided for common use cases

---

## Success Criteria

### Must Have
- Each sandbox project has its own `.gao-dev/documents.db`
- Running benchmarks creates documents in project's `.gao-dev/`
- CLI commands operate on the correct project's documentation
- Multiple projects can exist simultaneously without interference
- Project directories are portable (can be moved/copied)
- Coming back to a project loads its full documentation context
- All tests pass (400+ existing + new tests)

### Should Have
- Automatic project root detection works reliably
- Clear error messages for misconfiguration
- Graceful handling of legacy centralized data
- Performance impact negligible

### Nice to Have
- Migration script for existing data
- Visual indicator in CLI showing current project
- Project validation command

---

## Design Principles

1. **Project Isolation**: Each project has complete isolation from others
2. **Portability**: The `.gao-dev/` directory can be copied/moved with the project
3. **Persistence**: Documentation context persists across sessions, greenfield/brownfield transitions
4. **Consistency**: Same structure for all projects (greenfield, brownfield, sandbox, production)

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing workflows | High | Medium | Transition period with backward compatibility |
| Orphaned centralized data | Low | High | Migration script, clear documentation |
| Project detection failures | Medium | Low | Fallback to current directory, `--project` flag |
| Performance degradation | Low | Low | Efficient initialization, caching |

---

## Timeline

**Epic Duration**: 9-14 hours (3 phases)

**Phase 1** (4-6 hours): Core Refactoring
- Story 1.1: Add Project Context to Core Components
- Story 1.2: Update Sandbox Manager Integration
- Story 1.3: Update Orchestrator Integration

**Phase 2** (2-3 hours): CLI Updates
- Story 2.1: Add Project Root Detection
- Story 2.2: Update Lifecycle Commands

**Phase 3** (1-2 hours): Documentation
- Story 3.1: Documentation Updates

**Testing** (2-3 hours): Comprehensive validation across all phases

---

## Out of Scope

The following are explicitly NOT included in this epic:

- **UI/Visual Project Indicator**: Command-line indicator showing current project
- **Multi-Project Workspace**: Managing multiple projects in single command
- **Cloud Sync**: Syncing `.gao-dev/` to cloud storage
- **Project Templates**: Pre-configured `.gao-dev/` templates
- **Advanced Migration**: Automatic detection and migration of old data

These may be considered for future enhancements.

---

## Dependencies

### Internal Dependencies
- **Sandbox System**: Foundation for project creation and management
- **Orchestrator**: Uses document lifecycle for workflow execution
- **CLI Commands**: Interface for document lifecycle operations
- **Document Lifecycle**: Core system being refactored

### External Dependencies
- None (internal refactoring only)

---

## Impact Analysis

### Breaking Changes
**Medium Impact**:
- Existing `.gao-dev/documents.db` in GAO-Dev repo will be orphaned
- Any code assuming centralized document lifecycle will break
- CLI commands will operate on different database locations

**Mitigation**:
- This is a new feature (Epic 19.4 just completed)
- Minimal production usage so far
- Breaking changes acceptable at this stage
- Migration path provided if needed

### Benefits
**High Value**:
- Correct architecture for multi-project management
- Better isolation and context persistence
- Portable project directories
- Enables brownfield project support
- Consistent with sandbox architecture
- Foundation for future multi-project features

---

## Testing Strategy

### Unit Tests
1. `DocumentRegistry` with different project paths
2. `ProjectDocumentLifecycle.initialize()` creates correct structure
3. Isolated registries don't interfere
4. Project root detection with various directory structures

### Integration Tests
1. Create two sandbox projects, verify isolated `.gao-dev/`
2. Run benchmark, verify documents in project directory
3. Orchestrator with project_root creates project-scoped lifecycle
4. CLI commands detect and use correct project
5. Project deletion removes all project-scoped data

### End-to-End Tests
1. Full benchmark run creates project-scoped documentation
2. Come back to existing project, context loads correctly
3. Multiple concurrent benchmarks don't interfere
4. Project moved to different directory, context still works

---

## Appendix

### References
- **Analysis Document**: `DOCUMENT_LIFECYCLE_ARCHITECTURE_FIX.md`
- **Document Lifecycle**: `gao_dev/lifecycle/`
- **Sandbox Manager**: `gao_dev/sandbox/manager.py`
- **Orchestrator**: `gao_dev/orchestrator/orchestrator.py`
- **Epic 19**: OpenCode SDK Integration (recently completed)

### Related Features
- Epic 1-5: Sandbox and Benchmarking System
- Epic 12: Document Lifecycle System
- Epic 19: OpenCode SDK Integration

### Terminology
- **GAO-Dev-Centric**: Database stored in GAO-Dev project directory (incorrect)
- **Project-Centric**: Database stored in each managed project directory (correct)
- **Project Root**: The root directory of a project managed BY GAO-Dev
- **`.gao-dev/`**: Project-specific directory for GAO-Dev metadata and context
- **Greenfield**: New project created from scratch
- **Brownfield**: Existing codebase being enhanced

---

## Recommended Approach

### Option A: Fix Now (Recommended)
**Pros**:
- Correct architecture before more features depend on it
- Minimal disruption (feature just completed)
- Prevents compounding technical debt
- Foundation for brownfield support

**Cons**:
- Requires immediate refactoring effort
- May delay other feature work slightly

### Option B: Fix Later
**Pros**:
- Can complete other features first
- More time to consider design

**Cons**:
- Risk of building more features on wrong foundation
- Harder to fix later with more dependencies
- May forget the details of this analysis
- Blocks brownfield project support

**Recommendation**: Fix now (Option A). This is a fundamental architectural issue that will cause problems if left unfixed. The document lifecycle feature was just completed, making this the ideal time to correct the architecture before more features depend on it.

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-06 | John (Product Manager) | Initial PRD creation |
