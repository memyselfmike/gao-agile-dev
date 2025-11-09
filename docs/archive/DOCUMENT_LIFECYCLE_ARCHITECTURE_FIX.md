# Document Lifecycle System - Architecture Fix Analysis

**Date**: 2025-11-06
**Issue**: Document lifecycle system is GAO-Dev-centric instead of project-centric
**Status**: Analysis Complete - Ready for Implementation

---

## Executive Summary

The document lifecycle system was incorrectly implemented as a GAO-Dev-global system, storing all documentation metadata in a centralized database at `.gao-dev/documents.db` in the GAO-Dev project directory. This is fundamentally wrong.

**Correct Behavior**: Each project managed BY GAO-Dev should have its own `.gao-dev/` directory containing project-specific documentation, context, and metadata that persists across sessions.

---

## The Problem - Where We Went Wrong

### 1. Misunderstood Scope

**What we built**:
- A centralized document lifecycle system for the GAO-Dev project itself
- Database location: `<gao-dev-repo>/.gao-dev/documents.db`
- All projects share the same documentation registry

**What we should have built**:
- A project-scoped document lifecycle system for projects managed BY GAO-Dev
- Database location: `<project-root>/.gao-dev/documents.db`
- Each project has isolated documentation context

### 2. Architectural Issues

#### Issue 2.1: Hard-coded `Path.cwd()` in CLI Commands

**Location**: `gao_dev/cli/lifecycle_commands.py:35-36`

```python
project_root = Path.cwd()
db_path = project_root / ".gao-dev" / "documents.db"
```

**Problem**: This uses the current working directory, which when running GAO-Dev commands is typically the GAO-Dev development directory, NOT the target project directory.

**Impact**: All document lifecycle operations are performed on GAO-Dev itself, not on the project being managed.

#### Issue 2.2: Missing Project Context Awareness

**Current State**: The document lifecycle components have no awareness of which project they're operating on.

**Components affected**:
- `DocumentRegistry` - No project context parameter
- `DocumentLifecycleManager` - No project root tracking
- `ArchivalManager` - Archives to global `.archive/` directory
- CLI commands - Use current working directory

#### Issue 2.3: No Integration with Orchestrator/Sandbox

**Current State**:
- The `GAODevOrchestrator` has a `project_root` parameter
- The `SandboxManager` creates project directories in `sandbox/projects/<name>/`
- But the document lifecycle system doesn't integrate with either

**Missing**:
- Document lifecycle initialization when sandbox project is created
- Orchestrator passing project context to document operations
- Project-scoped `.gao-dev/` directory creation in sandbox projects

### 3. Use Case Mismatch

**Scenario**: User wants to build a todo application

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

## The Solution - Project-Scoped Architecture

### Design Principles

1. **Project Isolation**: Each project has its own `.gao-dev/` directory with complete isolation
2. **Portability**: The `.gao-dev/` directory can be copied/moved with the project
3. **Persistence**: Documentation context persists across sessions, greenfield/brownfield transitions
4. **Consistency**: Same structure for all projects (greenfield, brownfield, sandbox, production)

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

### Integration Points

#### 1. Sandbox Manager

**When**: Project creation (`gao-dev sandbox init <name>`)

**Action**: Initialize `.gao-dev/` directory structure

```python
def create_project(self, name: str, boilerplate_url: Optional[str] = None):
    # Create project directory
    project_dir = self.projects_dir / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize .gao-dev structure
    gao_dev_dir = project_dir / ".gao-dev"
    gao_dev_dir.mkdir(exist_ok=True)

    # Initialize document lifecycle for this project
    db_path = gao_dev_dir / "documents.db"
    registry = DocumentRegistry(db_path)
    # ... initialize components
```

#### 2. Orchestrator

**When**: Any workflow execution

**Action**: Pass project_root to all components that need document access

```python
class GAODevOrchestrator:
    def __init__(self, project_root: Path, ...):
        self.project_root = project_root

        # Initialize project-scoped document lifecycle
        gao_dev_dir = project_root / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        db_path = gao_dev_dir / "documents.db"
        archive_dir = project_root / ".archive"

        self.doc_registry = DocumentRegistry(db_path)
        self.doc_manager = DocumentLifecycleManager(self.doc_registry, archive_dir)
```

#### 3. CLI Commands

**When**: User runs document lifecycle commands

**Action**: Detect project root or require `--project` flag

```python
@click.option('--project', type=click.Path(exists=True),
              help='Project directory (defaults to current directory)')
def lifecycle_command(project: Optional[str] = None):
    # Detect project root
    if project:
        project_root = Path(project)
    else:
        project_root = _detect_project_root()  # Look for .gao-dev/ or .sandbox.yaml

    # Use project-scoped paths
    db_path = project_root / ".gao-dev" / "documents.db"
    archive_dir = project_root / ".archive"
```

#### 4. Agents (via Orchestrator)

**When**: Agents create/update documentation

**Action**: Documents are automatically tracked in project's `.gao-dev/`

```python
# In workflow execution
def execute_workflow(self, workflow_name: str, prompt: str):
    # Context includes project-scoped document manager
    context = {
        "doc_manager": self.doc_manager,  # Project-scoped
        "project_root": self.project_root,
    }

    # Agent creates PRD.md in project
    # Automatically registered in project's .gao-dev/documents.db
```

---

## Implementation Plan

### Phase 1: Core Refactoring (High Priority)

**Goal**: Make document lifecycle system project-aware

#### Story 1.1: Add Project Context to Core Components

**Changes**:
1. `DocumentRegistry.__init__()` - Already takes `db_path`, no change needed
2. `DocumentLifecycleManager.__init__()` - Add optional `project_root` parameter for logging
3. Create `ProjectDocumentLifecycle` factory class:
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

**Testing**:
- Create multiple projects in sandbox
- Verify isolated `.gao-dev/` directories
- Verify no cross-contamination

#### Story 1.2: Update Sandbox Manager Integration

**Changes**:
1. `SandboxManager.create_project()` - Initialize `.gao-dev/` structure
2. `ProjectLifecycleService` - Add document lifecycle initialization
3. `ProjectMetadata` - Track document lifecycle version

**Code**:
```python
# In sandbox/services/project_lifecycle.py
def create_project(self, name: str, ...) -> ProjectMetadata:
    # ... existing project creation ...

    # Initialize document lifecycle
    from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
    ProjectDocumentLifecycle.initialize(project_dir)

    # ... rest of setup ...
```

**Testing**:
- `gao-dev sandbox init test-project`
- Verify `.gao-dev/` created
- Verify `documents.db` exists and is empty

#### Story 1.3: Update Orchestrator Integration

**Changes**:
1. `GAODevOrchestrator.__init__()` - Initialize project-scoped document lifecycle
2. Pass `doc_manager` to workflow coordinator
3. Update context API to include document manager

**Code**:
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

**Testing**:
- Run benchmark with document creation
- Verify documents tracked in project's `.gao-dev/`
- Verify multiple concurrent projects don't interfere

### Phase 2: CLI Updates (Medium Priority)

**Goal**: Update CLI commands to be project-aware

#### Story 2.1: Add Project Root Detection

**Changes**:
1. Create `gao_dev/cli/project_detection.py`:
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

2. Update all lifecycle CLI commands to use detection

**Testing**:
- Run from various directories
- Verify correct project detection
- Test with `--project` override

#### Story 2.2: Update Lifecycle Commands

**Changes**:
1. `lifecycle_commands.py` - Replace `Path.cwd()` with `detect_project_root()`
2. Add `--project` option to all commands
3. Update help text to explain project scope

**Testing**:
- Run lifecycle commands from different directories
- Verify correct project targeting
- Test multi-project scenarios

### Phase 3: Migration & Cleanup (Low Priority)

**Goal**: Clean up existing GAO-Dev-level `.gao-dev/` and provide migration path

#### Story 3.1: Migration Script

**Create**: `scripts/migrate_to_project_scoped.py`

**Purpose**: Migrate any existing centralized data to project-scoped structure

**Note**: May not be needed if we simply start fresh with correct architecture

#### Story 3.2: Documentation Updates

**Changes**:
1. Update CLAUDE.md with project-scoped architecture
2. Update plugin development guide
3. Add migration guide if needed
4. Update benchmark documentation

---

## Testing Strategy

### Unit Tests

1. **Test**: `DocumentRegistry` with different project paths
2. **Test**: `ProjectDocumentLifecycle.initialize()` creates correct structure
3. **Test**: Isolated registries don't interfere

### Integration Tests

1. **Test**: Create two sandbox projects, verify isolated `.gao-dev/`
2. **Test**: Run benchmark, verify documents in project directory
3. **Test**: Orchestrator with project_root creates project-scoped lifecycle
4. **Test**: CLI commands detect and use correct project

### E2E Tests

1. **Test**: Full benchmark run creates project-scoped documentation
2. **Test**: Come back to existing project, context is loaded correctly
3. **Test**: Multiple concurrent benchmarks don't interfere

---

## Success Criteria

After implementation, the following should be true:

1. Each sandbox project has its own `.gao-dev/documents.db`
2. Running benchmarks creates documents in project's `.gao-dev/`
3. CLI commands operate on the correct project's documentation
4. Multiple projects can exist simultaneously without interference
5. Project directories are portable (can be moved/copied)
6. Coming back to a project loads its full documentation context
7. Greenfield and brownfield projects use same structure

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

### Benefits

**High Value**:
- Correct architecture for multi-project management
- Better isolation and context persistence
- Portable project directories
- Enables brownfield project support
- Consistent with sandbox architecture

---

## Timeline Estimate

- **Phase 1**: 4-6 hours (3 stories)
- **Phase 2**: 2-3 hours (2 stories)
- **Phase 3**: 1-2 hours (documentation)
- **Testing**: 2-3 hours
- **Total**: 9-14 hours

---

## Recommended Approach

### Option A: Fix Now (Recommended)

**Pros**:
- Correct architecture before more features depend on it
- Minimal disruption (feature just completed)
- Prevents compounding technical debt

**Cons**:
- Delays Epic 19 completion slightly

### Option B: Fix Later

**Pros**:
- Can complete Epic 19 first
- More time to consider design

**Cons**:
- Risk of building more features on wrong foundation
- Harder to fix later with more dependencies
- May forget the details of this analysis

**Recommendation**: Fix now (Option A). This is a fundamental architectural issue that will cause problems if left unfixed.

---

## Next Steps

1. Review this analysis with user
2. Get approval for recommended approach
3. Create Epic/Stories in workflow system
4. Implement Phase 1 (core refactoring)
5. Implement Phase 2 (CLI updates)
6. Update documentation (Phase 3)
7. Run comprehensive tests
8. Update Epic 19 documentation to reflect corrected architecture

---

## References

- Epic 19: OpenCode SDK Integration
- Story 19.4: Integration Testing and Validation
- `gao_dev/lifecycle/` - Document lifecycle implementation
- `gao_dev/sandbox/` - Sandbox manager
- `gao_dev/orchestrator/` - Orchestrator
- CLAUDE.md - Project guide
