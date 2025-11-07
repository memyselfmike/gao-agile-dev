# Story 20.3: Update Orchestrator Integration

**Epic**: Epic 20 - Project-Scoped Document Lifecycle
**Status**: Ready
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-06

---

## User Story

**As a** GAO-Dev developer
**I want** the orchestrator to use project-scoped document lifecycle
**So that** agents automatically track documents in the correct project's `.gao-dev/` directory

---

## Acceptance Criteria

### AC1: Orchestrator Initializes Project-Scoped Lifecycle

- ✅ `GAODevOrchestrator.__init__()` calls `ProjectDocumentLifecycle.initialize()`
- ✅ Uses `project_root` parameter to determine correct `.gao-dev/` location
- ✅ Document manager instance stored for workflow use
- ✅ Initialization logged with project context

### AC2: Document Manager Passed to Workflows

- ✅ `WorkflowCoordinator` receives `doc_manager` parameter
- ✅ Workflow execution context includes document manager
- ✅ Agents can access document manager from context
- ✅ Document operations automatically use project-scoped paths

### AC3: Backward Compatibility

- ✅ If `project_root` not provided, uses current directory
- ✅ Existing orchestrator usage doesn't break
- ✅ Graceful degradation if lifecycle initialization fails
- ✅ Clear error messages for misconfiguration

### AC4: Benchmark Integration

- ✅ Benchmark orchestrator passes project directory
- ✅ Documents created during benchmark tracked in project `.gao-dev/`
- ✅ Metrics include document lifecycle operations
- ✅ Benchmark reports show document tracking status

### AC5: Integration Tests

- ✅ Test: `test_orchestrator_initializes_lifecycle()` - Verifies initialization
- ✅ Test: `test_workflow_has_doc_manager_access()` - Context includes manager
- ✅ Test: `test_benchmark_uses_project_scoped()` - Benchmark integration
- ✅ Test: `test_multiple_orchestrators_isolated()` - Multiple instances isolated
- ✅ All tests pass

---

## Technical Details

### File Structure

```
gao_dev/orchestrator/
├── orchestrator.py          # UPDATE: GAODevOrchestrator
├── workflow_coordinator.py  # UPDATE: WorkflowCoordinator
└── context.py               # UPDATE: Execution context
```

### Implementation Approach

**Step 1: Update GAODevOrchestrator**

Initialize project-scoped document lifecycle:

```python
# In gao_dev/orchestrator/orchestrator.py

from pathlib import Path
from typing import Optional
import structlog

from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.lifecycle.manager import DocumentLifecycleManager
from gao_dev.orchestrator.workflow_coordinator import WorkflowCoordinator

logger = structlog.get_logger(__name__)


class GAODevOrchestrator:
    """
    Main orchestrator for GAO-Dev autonomous development system.

    Coordinates agents, workflows, and system components to build
    complete applications autonomously.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        methodology: Optional[str] = None,
        workflow_coordinator: Optional[WorkflowCoordinator] = None,
        state_manager: Optional[StateManager] = None,
        git_manager: Optional[GitManager] = None,
        quality_gate: Optional[QualityGate] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            project_root: Root directory of the project (defaults to current directory)
            methodology: Methodology to use (defaults to 'adaptive-agile')
            workflow_coordinator: Optional workflow coordinator instance
            state_manager: Optional state manager instance
            git_manager: Optional git manager instance
            quality_gate: Optional quality gate instance
        """
        # Set project root
        self.project_root = project_root or Path.cwd()
        logger.info("Initializing orchestrator", project_root=str(self.project_root))

        # Initialize project-scoped document lifecycle (NEW)
        try:
            self.doc_lifecycle = ProjectDocumentLifecycle.initialize(self.project_root)
            logger.info(
                "Document lifecycle initialized",
                project_root=str(self.project_root),
                db_path=str(ProjectDocumentLifecycle.get_db_path(self.project_root))
            )
        except Exception as e:
            logger.warning(
                "Failed to initialize document lifecycle",
                project_root=str(self.project_root),
                error=str(e)
            )
            self.doc_lifecycle = None

        # Initialize other components
        self.methodology = self._load_methodology(methodology)
        self.state_manager = state_manager or StateManager(self.project_root)
        self.git_manager = git_manager or GitManager(self.project_root)
        self.quality_gate = quality_gate or QualityGate()

        # Initialize workflow coordinator with document manager (UPDATED)
        self.workflow_coordinator = workflow_coordinator or WorkflowCoordinator(
            project_root=self.project_root,
            methodology=self.methodology,
            state_manager=self.state_manager,
            doc_manager=self.doc_lifecycle,  # NEW parameter
        )

        logger.info("Orchestrator initialized successfully")

    def execute_workflow(
        self,
        workflow_name: str,
        prompt: str,
        context: Optional[dict] = None,
    ) -> WorkflowResult:
        """
        Execute a workflow with the given prompt.

        Args:
            workflow_name: Name of the workflow to execute
            prompt: User prompt/requirement
            context: Optional additional context

        Returns:
            WorkflowResult with execution details
        """
        logger.info(
            "Executing workflow",
            workflow=workflow_name,
            project_root=str(self.project_root)
        )

        # Build execution context
        execution_context = {
            "project_root": self.project_root,
            "doc_manager": self.doc_lifecycle,  # Include document manager
            "state_manager": self.state_manager,
            "git_manager": self.git_manager,
            "quality_gate": self.quality_gate,
            **(context or {}),
        }

        # Execute workflow
        result = self.workflow_coordinator.execute(
            workflow_name=workflow_name,
            prompt=prompt,
            context=execution_context,
        )

        logger.info(
            "Workflow execution completed",
            workflow=workflow_name,
            success=result.success
        )

        return result

    def get_document_manager(self) -> Optional[DocumentLifecycleManager]:
        """
        Get the project-scoped document lifecycle manager.

        Returns:
            DocumentLifecycleManager instance or None if not initialized
        """
        return self.doc_lifecycle
```

**Step 2: Update WorkflowCoordinator**

Accept and use document manager:

```python
# In gao_dev/orchestrator/workflow_coordinator.py

from pathlib import Path
from typing import Optional
import structlog

from gao_dev.lifecycle.manager import DocumentLifecycleManager

logger = structlog.get_logger(__name__)


class WorkflowCoordinator:
    """
    Coordinates workflow execution and agent interactions.
    """

    def __init__(
        self,
        project_root: Path,
        methodology: Methodology,
        state_manager: StateManager,
        doc_manager: Optional[DocumentLifecycleManager] = None,  # NEW parameter
    ):
        """
        Initialize the workflow coordinator.

        Args:
            project_root: Project root directory
            methodology: Methodology instance
            state_manager: State manager instance
            doc_manager: Optional document lifecycle manager
        """
        self.project_root = project_root
        self.methodology = methodology
        self.state_manager = state_manager
        self.doc_manager = doc_manager  # Store for workflow use

        logger.info(
            "Workflow coordinator initialized",
            project_root=str(project_root),
            has_doc_manager=doc_manager is not None
        )

    def execute(
        self,
        workflow_name: str,
        prompt: str,
        context: dict,
    ) -> WorkflowResult:
        """
        Execute a workflow.

        Args:
            workflow_name: Name of workflow to execute
            prompt: User prompt
            context: Execution context (includes doc_manager)

        Returns:
            WorkflowResult with execution details
        """
        logger.info("Executing workflow", workflow=workflow_name)

        # Ensure doc_manager in context
        if "doc_manager" not in context and self.doc_manager:
            context["doc_manager"] = self.doc_manager

        # Load workflow
        workflow = self._load_workflow(workflow_name)

        # Execute workflow with context
        result = workflow.execute(prompt, context)

        # Track documents created during workflow (if doc_manager available)
        if self.doc_manager and result.artifacts:
            self._register_workflow_artifacts(workflow_name, result.artifacts)

        return result

    def _register_workflow_artifacts(
        self,
        workflow_name: str,
        artifacts: list[Path]
    ) -> None:
        """
        Register artifacts created during workflow execution.

        Args:
            workflow_name: Name of workflow that created artifacts
            artifacts: List of artifact paths
        """
        if not self.doc_manager:
            return

        logger.debug(
            "Registering workflow artifacts",
            workflow=workflow_name,
            artifact_count=len(artifacts)
        )

        for artifact in artifacts:
            try:
                # Determine document type from path
                doc_type = self._infer_document_type(artifact)

                # Register with document lifecycle
                self.doc_manager.registry.register_document(
                    path=str(artifact.relative_to(self.project_root)),
                    doc_type=doc_type,
                    metadata={
                        "workflow": workflow_name,
                        "created_by": "orchestrator",
                    }
                )

                logger.debug(
                    "Artifact registered",
                    artifact=str(artifact),
                    doc_type=doc_type
                )

            except Exception as e:
                logger.warning(
                    "Failed to register artifact",
                    artifact=str(artifact),
                    error=str(e)
                )

    def _infer_document_type(self, path: Path) -> str:
        """Infer document type from file path."""
        if "PRD" in path.name.upper():
            return "product-requirements"
        elif "ARCHITECTURE" in path.name.upper():
            return "architecture"
        elif path.name.startswith("story-"):
            return "story"
        elif path.name.startswith("epic-"):
            return "epic"
        else:
            return "documentation"
```

**Step 3: Update Execution Context**

Ensure context properly includes document manager:

```python
# In gao_dev/orchestrator/context.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gao_dev.lifecycle.manager import DocumentLifecycleManager
from gao_dev.core.state_manager import StateManager
from gao_dev.core.git_manager import GitManager


@dataclass
class ExecutionContext:
    """
    Context for workflow execution.

    Contains all necessary components and state for executing
    workflows and coordinating agents.
    """

    project_root: Path
    state_manager: StateManager
    git_manager: GitManager
    doc_manager: Optional[DocumentLifecycleManager] = None  # NEW field

    # Existing fields...
    methodology: str = "adaptive-agile"
    metadata: dict = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for agent context."""
        return {
            "project_root": str(self.project_root),
            "has_doc_manager": self.doc_manager is not None,
            "methodology": self.methodology,
            "metadata": self.metadata,
        }
```

**Step 4: Update Benchmark Orchestrator**

Ensure benchmarks use project-scoped lifecycle:

```python
# In gao_dev/sandbox/benchmark/orchestrator.py

class BenchmarkOrchestrator:
    """Orchestrates benchmark execution."""

    def __init__(self, config: BenchmarkConfig, sandbox_manager: SandboxManager):
        """Initialize the benchmark orchestrator."""
        self.config = config
        self.sandbox_manager = sandbox_manager

    def run(self) -> BenchmarkResult:
        """Run the benchmark."""
        # Get project directory
        project_dir = self.sandbox_manager.projects_dir / self.config.project_name

        # Initialize orchestrator with project root (IMPORTANT)
        orchestrator = GAODevOrchestrator(
            project_root=project_dir,  # Use project directory, not sandbox root
            methodology=self.config.methodology,
        )

        # Execute workflows
        for workflow in self.config.workflows:
            result = orchestrator.execute_workflow(
                workflow_name=workflow.name,
                prompt=workflow.prompt,
            )

        # Documents are now tracked in project_dir/.gao-dev/
        return BenchmarkResult(...)
```

---

## Testing Approach

### Integration Tests

Create `tests/orchestrator/test_orchestrator_lifecycle.py`:

```python
"""Integration tests for Orchestrator document lifecycle."""

import pytest
from pathlib import Path
import tempfile
import shutil

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestOrchestratorLifecycle:
    """Test suite for Orchestrator document lifecycle integration."""

    @pytest.fixture
    def project_dir(self):
        """Create temporary project directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_orchestrator_initializes_lifecycle(self, project_dir):
        """Test that orchestrator initializes document lifecycle."""
        # Create orchestrator
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        # Verify document lifecycle initialized
        assert orchestrator.doc_lifecycle is not None
        assert (project_dir / ".gao-dev" / "documents.db").exists()

    def test_workflow_has_doc_manager_access(self, project_dir):
        """Test that workflows can access document manager from context."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        # Execute workflow with context
        result = orchestrator.execute_workflow(
            workflow_name="test_workflow",
            prompt="test prompt",
            context={},
        )

        # Verify doc_manager was in context
        # (This would be tested by workflow implementation)
        assert orchestrator.doc_lifecycle is not None

    def test_get_document_manager(self, project_dir):
        """Test get_document_manager method."""
        orchestrator = GAODevOrchestrator(project_root=project_dir)

        doc_manager = orchestrator.get_document_manager()
        assert doc_manager is not None
        assert doc_manager.project_root == project_dir

    def test_multiple_orchestrators_isolated(self, tmp_path):
        """Test that multiple orchestrators have isolated lifecycles."""
        project1 = tmp_path / "project1"
        project2 = tmp_path / "project2"

        # Create two orchestrators
        orch1 = GAODevOrchestrator(project_root=project1)
        orch2 = GAODevOrchestrator(project_root=project2)

        # Verify isolated
        assert orch1.doc_lifecycle is not None
        assert orch2.doc_lifecycle is not None
        assert orch1.project_root != orch2.project_root

        # Register document in project1
        orch1.doc_lifecycle.registry.register_document("test.md", "test", {})

        # Verify project2 unaffected
        docs = orch2.doc_lifecycle.registry.list_documents()
        assert len(docs) == 0

    def test_orchestrator_without_project_root(self):
        """Test orchestrator with default project root."""
        # Should use current directory
        orchestrator = GAODevOrchestrator()

        assert orchestrator.project_root == Path.cwd()

    def test_orchestrator_lifecycle_failure_graceful(self, tmp_path):
        """Test that lifecycle initialization failure doesn't crash orchestrator."""
        # Use read-only directory to cause failure
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        try:
            # Should not crash, but doc_lifecycle will be None
            orchestrator = GAODevOrchestrator(project_root=readonly_dir)
            assert orchestrator.doc_lifecycle is None  # Failed to initialize

        finally:
            # Clean up
            readonly_dir.chmod(0o755)

    def test_benchmark_uses_project_scoped(self, project_dir):
        """Test that benchmark orchestrator uses project-scoped lifecycle."""
        # This would be an E2E test with actual benchmark
        # For now, verify the pattern

        orchestrator = GAODevOrchestrator(project_root=project_dir)

        # Verify correct paths
        db_path = ProjectDocumentLifecycle.get_db_path(project_dir)
        assert db_path == project_dir / ".gao-dev" / "documents.db"
```

Run tests:
```bash
pytest tests/orchestrator/test_orchestrator_lifecycle.py -v
```

---

## Dependencies

### Required Packages
- ✅ structlog (already installed)
- ✅ pytest (already installed)

### Code Dependencies
- Story 20.1: ProjectDocumentLifecycle factory class
- Story 20.2: SandboxManager integration
- `gao_dev.orchestrator.orchestrator.GAODevOrchestrator`
- `gao_dev.orchestrator.workflow_coordinator.WorkflowCoordinator`

---

## Definition of Done

- [ ] `GAODevOrchestrator.__init__()` initializes project-scoped lifecycle
- [ ] `WorkflowCoordinator` accepts and uses `doc_manager` parameter
- [ ] Execution context includes document manager
- [ ] Workflow artifacts automatically registered
- [ ] Benchmark orchestrator passes project directory
- [ ] Integration tests created and passing
- [ ] Graceful degradation if initialization fails
- [ ] Logging comprehensive and clear
- [ ] Code review completed
- [ ] Committed to git with conventional commit message

---

## Related Stories

**Depends On**:
- Story 20.1: Create ProjectDocumentLifecycle Factory Class
- Story 20.2: Update SandboxManager Integration

**Blocks**:
- Story 20.6: Documentation and Migration

---

## Notes

### Key Design Decisions

1. **Non-Fatal Initialization**: Lifecycle init failure doesn't prevent orchestrator creation
2. **Context Propagation**: Document manager passed through execution context
3. **Automatic Registration**: Workflow artifacts automatically registered
4. **Type Inference**: Document types inferred from file paths
5. **Backward Compatible**: Existing code without project_root still works

### Benefits

- Agents automatically track documents in correct location
- No manual registration needed for workflow artifacts
- Complete audit trail of document creation
- Multi-project support enabled

---

## Acceptance Testing

### Test Case 1: Orchestrator Initializes Lifecycle

```python
from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from pathlib import Path

project_dir = Path("sandbox/projects/test-app")
orchestrator = GAODevOrchestrator(project_root=project_dir)

# Verify
assert (project_dir / ".gao-dev" / "documents.db").exists()
assert orchestrator.doc_lifecycle is not None
```

**Expected**: Document lifecycle initialized for project

### Test Case 2: Workflows Access Document Manager

```python
# Execute workflow
result = orchestrator.execute_workflow(
    workflow_name="prd",
    prompt="Create PRD for todo app"
)

# Verify document tracked
docs = orchestrator.doc_lifecycle.registry.list_documents()
assert len(docs) > 0
```

**Expected**: Created documents automatically tracked

### Test Case 3: Multiple Orchestrators Isolated

```python
orch1 = GAODevOrchestrator(project_root=Path("sandbox/projects/app1"))
orch2 = GAODevOrchestrator(project_root=Path("sandbox/projects/app2"))

# Register in app1
orch1.doc_lifecycle.registry.register_document("test.md", "test", {})

# Verify app2 unaffected
assert len(orch2.doc_lifecycle.registry.list_documents()) == 0
```

**Expected**: Projects have isolated document tracking

---

**Created by**: Bob (Scrum Master)
**Ready for Implementation**: Yes
**Estimated Completion**: 1-2 days

---

*This story is part of Epic 20: Project-Scoped Document Lifecycle.*
