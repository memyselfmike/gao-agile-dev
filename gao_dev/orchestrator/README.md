# GAO-Dev Orchestrator Architecture

**Package**: `gao_dev.orchestrator`
**Version**: 3.0 (Post-Epic 22 Refactoring)
**Status**: Production
**Last Updated**: 2025-11-09

---

## Overview

The GAO-Dev orchestrator is a **facade pattern** that coordinates autonomous AI development through specialized services. After Epic 22 refactoring, the orchestrator is a thin 469 LOC facade that delegates to 5 focused services.

### Architecture Pattern: Facade

```
┌────────────────────────────────────────────────────────────┐
│            GAODevOrchestrator (FACADE)                     │
│                     469 LOC                                │
│                                                            │
│  - Provides simple high-level API                          │
│  - Delegates to specialized services                       │
│  - Manages service lifecycle                               │
└────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼──────────────┬─────────────┐
         ↓               ↓              ↓             ↓
┌─────────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐
│ WorkflowExec    │ │Artifact  │ │Agent     │ │Ceremony     │
│ Engine          │ │Manager   │ │Coordinator│ │Orchestrator │
│ ~325 LOC        │ │~414 LOC  │ │~218 LOC  │ │~297 LOC     │
└─────────────────┘ └──────────┘ └──────────┘ └─────────────┘
         │               │
         └───────────────┘
                  │
           ┌──────────────┐
           │Metadata      │
           │Extractor     │
           │~228 LOC      │
           └──────────────┘
```

**Key Metrics (Post-Epic 22)**:
- Facade LOC: 469 (down from 1,477)
- Services: 5 specialized services (~200-400 LOC each)
- Test Coverage: 162 tests (147 existing + 15 validation)
- Pass Rate: 100%
- Backward Compatibility: 100%

---

## Services

### 1. WorkflowExecutionEngine

**File**: `workflow_execution_engine.py`
**LOC**: ~325
**Purpose**: Execute workflows and tasks with variable resolution

**Responsibilities**:
- Execute workflows via WorkflowExecutor
- Execute tasks via task prompts (e.g., create_prd)
- Coordinate with WorkflowRegistry
- Handle workflow errors and retries

**Key Methods**:
```python
async def execute_task(task_name: str, params: dict) -> TaskResult:
    """Execute a task via task prompt template."""

async def execute(workflow_name: str, params: dict) -> WorkflowResult:
    """Execute a workflow with parameter resolution."""
```

**Example**:
```python
# Execute task
result = await orchestrator.workflow_execution_engine.execute_task(
    "create_prd",
    {"project_name": "MyApp"}
)

# Execute workflow
result = await orchestrator.workflow_execution_engine.execute(
    "prd",
    {"project_name": "MyApp"}
)
```

---

### 2. ArtifactManager

**File**: `artifact_manager.py`
**LOC**: ~414
**Purpose**: Detect and register workflow artifacts

**Responsibilities**:
- Snapshot project files before/after operations
- Detect newly created or modified artifacts
- Infer document types from paths/content
- Register artifacts with document lifecycle
- Use MetadataExtractor for path parsing

**Key Methods**:
```python
def snapshot() -> Set[Tuple[str, float, int]]:
    """Snapshot current project files."""

def detect(before: Set, after: Set) -> List[Path]:
    """Detect artifacts created/modified between snapshots."""

def infer_type(path: Path, content: str) -> DocumentType:
    """Infer document type from path and content."""

def register(artifacts: List[Path], context: dict) -> None:
    """Register artifacts with document lifecycle."""
```

**Example**:
```python
# Take snapshot before operation
before = orchestrator.artifact_manager.snapshot()

# ... perform workflow operation ...

# Detect and register artifacts
after = orchestrator.artifact_manager.snapshot()
artifacts = orchestrator.artifact_manager.detect(before, after)
orchestrator.artifact_manager.register(artifacts, {"epic": 1})
```

---

### 3. AgentCoordinator

**File**: `agent_coordinator.py`
**LOC**: ~218
**Purpose**: Coordinate agent operations and lifecycle

**Responsibilities**:
- Execute tasks via appropriate agents
- Map workflows to correct agents (PRD → John, Architecture → Winston)
- Manage agent lifecycle and caching
- Coordinate agent-specific context
- Delegate to ProcessExecutor for Claude CLI execution

**Key Methods**:
```python
async def execute_task(
    agent_name: str,
    instructions: str,
    context: dict,
    tools: Optional[List[str]] = None
) -> AsyncGenerator[str, None]:
    """Execute task via specified agent."""

def get_agent(workflow_name: str) -> str:
    """Get agent name for workflow."""
```

**Example**:
```python
# Execute task via specific agent
async for chunk in orchestrator.agent_coordinator.execute_task(
    agent_name="John",
    instructions="Create a PRD for MyApp",
    context={"project_name": "MyApp"}
):
    print(chunk)

# Get agent for workflow
agent = orchestrator.agent_coordinator.get_agent("prd")  # Returns: "John"
```

---

### 4. CeremonyOrchestrator

**File**: `ceremony_orchestrator.py`
**LOC**: ~297
**Purpose**: Coordinate multi-agent ceremonies (stand-ups, retros, planning)

**Status**: Foundation created in Epic 22, full implementation in Epic 26

**Responsibilities** (Epic 26):
- Coordinate multi-agent stand-ups
- Coordinate retrospectives
- Coordinate planning sessions
- Track ceremony artifacts

**Example** (Epic 26):
```python
# Hold stand-up
await orchestrator.ceremony_orchestrator.hold_standup(
    epic_num=1,
    participants=["John", "Winston", "Amelia", "Bob"]
)
```

---

### 5. MetadataExtractor

**File**: `metadata_extractor.py`
**LOC**: ~228
**Purpose**: Extract metadata from paths and content

**Responsibilities**:
- Extract feature names from paths
- Extract epic/story numbers from paths
- Parse document titles from content
- Provide metadata parsing utilities

**Key Methods**:
```python
def extract_feature_name(path: Path) -> Optional[str]:
    """Extract feature name from path."""

def extract_epic_number(path: Path) -> Optional[int]:
    """Extract epic number from path."""

def extract_story_number(path: Path) -> Optional[Tuple[int, int]]:
    """Extract (epic, story) from path."""

def extract_title(content: str) -> Optional[str]:
    """Extract title from markdown content."""
```

**Example**:
```python
extractor = orchestrator.artifact_manager.metadata_extractor

feature = extractor.extract_feature_name(
    Path("docs/features/sandbox-system/PRD.md")
)
# Returns: "sandbox-system"

story_num = extractor.extract_story_number(
    Path("docs/features/f/stories/epic-5/story-5.3.md")
)
# Returns: (5, 3)
```

---

## Usage

### Basic Usage (Factory Method)

```python
from pathlib import Path
from gao_dev.orchestrator.orchestrator import GAODevOrchestrator

# Create orchestrator via factory (recommended)
orchestrator = GAODevOrchestrator.create_default(
    project_root=Path("/project"),
    api_key="sk-...",
    mode="cli"
)

# Use high-level API
async for chunk in orchestrator.create_prd(project_name="MyApp"):
    print(chunk)

# Close when done
await orchestrator.close()
```

### Advanced Usage (Custom Services)

```python
# Inject custom services (for testing or custom behavior)
orchestrator = GAODevOrchestrator(
    project_root=Path("/project"),
    workflow_execution_engine=MyCustomEngine(...),
    artifact_manager=MyCustomManager(...),
    # ... other required services
)
```

### Service Access

```python
# Access services directly
workflow_engine = orchestrator.workflow_execution_engine
artifact_manager = orchestrator.artifact_manager
agent_coordinator = orchestrator.agent_coordinator

# Use services
result = await workflow_engine.execute_task("create_prd", {"project_name": "MyApp"})
snapshot = artifact_manager.snapshot()
agent = agent_coordinator.get_agent("prd")
```

---

## Testing

### Unit Tests (Per Service)

Each service has focused unit tests:
- `test_workflow_execution_engine.py` (20+ tests)
- `test_artifact_manager.py` (35+ tests)
- `test_agent_coordinator.py` (15+ tests)
- `test_ceremony_orchestrator.py` (10+ tests)
- `test_metadata_extractor.py` (20+ tests)

### Validation Tests (Epic 22)

Refactoring validation tests:
- `test_refactoring_validation.py` (15 tests)
  - Contract tests (5) - Public API unchanged
  - Regression tests (5) - Behavior unchanged
  - Performance tests (3) - No degradation
  - Dependency tests (2) - No new deps

### Running Tests

```bash
# Run all orchestrator tests
pytest tests/orchestrator/ -v

# Run validation tests
pytest tests/orchestrator/test_refactoring_validation.py -v
```

---

## Migration from Epic 21 to Epic 22

See [EPIC-22-MIGRATION.md](../../docs/features/git-integrated-hybrid-wisdom/EPIC-22-MIGRATION.md) for detailed migration guide.

**Summary**:
- ✅ **Public API unchanged** (100% backward compatible)
- ✅ **Factory method unchanged** (use `create_default()`)
- ✅ **Services accessible** (via public attributes)
- ✅ **Performance unchanged** (validated by tests)

**Breaking Changes**: None

---

## Performance

### Orchestrator Initialization
- **Time**: <1 second (typical: 100-200ms)
- **Validated by**: `test_orchestrator_initialization_performance`

### Artifact Detection
- **Time**: <1 second for small projects (typical: 50-100ms)
- **Validated by**: `test_artifact_detection_performance`

### Service Access Overhead
- **Overhead**: <0.1ms per service access
- **Validated by**: `test_service_delegation_overhead`

---

## Version History

| Version | Date | Epic | Notes |
|---------|------|------|-------|
| 3.0 | 2025-11-09 | Epic 22 | Service decomposition (1,477 → 469 LOC) |
| 2.0 | 2025-10-30 | Epic 6 | Service-based architecture |
| 1.0 | 2025-10-29 | - | Monolithic god class |

---

## Resources

- **Migration Guide**: `docs/features/git-integrated-hybrid-wisdom/EPIC-22-MIGRATION.md`
- **Architecture**: `docs/features/git-integrated-hybrid-wisdom/ARCHITECTURE.md`
- **Services**: `gao_dev/orchestrator/*.py`
- **Tests**: `tests/orchestrator/`

---

**Version**: 3.0 (Post-Epic 22)
**Last Updated**: 2025-11-09
**Status**: Production
