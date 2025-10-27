# System Architecture
## GAO-Dev Sandbox & Benchmarking System

**Version:** 1.0.0
**Date:** 2025-10-27
**Author:** Winston (Technical Architect) - Manual Creation
**Status:** Draft

---

## Table of Contents
1. [System Context](#system-context)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Directory Structure](#directory-structure)
8. [Interface Definitions](#interface-definitions)
9. [Security Considerations](#security-considerations)
10. [Deployment Architecture](#deployment-architecture)

---

## System Context

### Purpose
The Sandbox & Benchmarking System enables deterministic testing and measurement of GAO-Dev's autonomous capabilities by providing:
- Isolated project environments
- Automated metric collection
- Performance benchmarking
- Trend analysis and reporting

### Key Stakeholders
- **Developers**: Use sandbox to test GAO-Dev improvements
- **Product Team**: Track progress toward full autonomy
- **GAO-Dev System**: Subject of testing and measurement

### System Boundaries
**In Scope:**
- Sandbox project management
- Boilerplate integration
- Benchmark execution
- Metric collection and storage
- Report generation

**Out of Scope:**
- GAO-Dev core functionality (separate system)
- CI/CD infrastructure (future enhancement)
- Cloud deployment automation (future enhancement)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User/CLI                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  Sandbox CLI Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  init    │ │  clean   │ │   run    │ │  report  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              Core Services Layer                             │
│  ┌─────────────────┐  ┌──────────────────┐                 │
│  │ Sandbox Manager │  │ Benchmark Runner │                 │
│  └────────┬────────┘  └────────┬─────────┘                 │
│           │                     │                            │
│  ┌────────▼────────┐  ┌────────▼─────────┐                 │
│  │ Boilerplate Mgr │  │ Metrics Collector│                 │
│  └─────────────────┘  └──────────────────┘                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│               Data Layer                                     │
│  ┌────────────────┐  ┌──────────────────┐                  │
│  │ Metrics Store  │  │ Config Store     │                  │
│  │   (SQLite)     │  │   (YAML/JSON)    │                  │
│  └────────────────┘  └──────────────────┘                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│             External Systems                                 │
│  ┌────────────┐ ┌─────────────┐ ┌──────────────┐          │
│  │ Git Repos  │ │  GAO-Dev    │ │ File System  │          │
│  └────────────┘ └─────────────┘ └──────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Separation of Concerns**: CLI, business logic, data access clearly separated
2. **Single Responsibility**: Each component has one well-defined purpose
3. **Dependency Injection**: Components receive dependencies rather than creating them
4. **Fail-Safe Defaults**: System defaults to safe, predictable behavior
5. **Observable**: Comprehensive logging and metric collection
6. **Testable**: All components designed for unit testing

---

## Component Design

### 1. Sandbox CLI Layer

**Responsibility**: User interface for sandbox operations

**Commands:**

#### `gao-dev sandbox init <project-name>`
```python
# Purpose: Initialize new sandbox project
# Input: project_name (str)
# Output: Created project directory, config files
# Success: Exit 0, message "Sandbox initialized"
# Failure: Exit 1, error message
```

#### `gao-dev sandbox clean [project-name]`
```python
# Purpose: Reset sandbox to clean state
# Input: project_name (str, optional - defaults to current)
# Output: Removed generated files, reset state
# Success: Exit 0, message "Sandbox cleaned"
# Failure: Exit 1, error message
```

#### `gao-dev sandbox list`
```python
# Purpose: List all sandbox projects
# Input: None
# Output: Table of projects with status
# Success: Exit 0, formatted table
# Failure: Exit 1, error message
```

#### `gao-dev sandbox run <benchmark-config>`
```python
# Purpose: Execute benchmark with metrics collection
# Input: benchmark_config (file path)
# Output: Run ID, real-time progress, final metrics
# Success: Exit 0, run summary
# Failure: Exit 1, error message
```

#### `gao-dev sandbox report <run-id>`
```python
# Purpose: Generate HTML report for benchmark run
# Input: run_id (str)
# Output: HTML file path
# Success: Exit 0, report generated
# Failure: Exit 1, error message
```

#### `gao-dev sandbox compare <run1> <run2>`
```python
# Purpose: Compare two benchmark runs
# Input: run_id_1, run_id_2 (str)
# Output: Comparison report
# Success: Exit 0, comparison shown
# Failure: Exit 1, error message
```

**Implementation:**
- Location: `gao_dev/cli/sandbox_commands.py`
- Uses Click for command parsing
- Delegates to SandboxManager for business logic

---

### 2. Sandbox Manager

**Responsibility**: Orchestrate sandbox lifecycle and operations

**Interface:**
```python
class SandboxManager:
    """Manages sandbox project lifecycle."""

    def __init__(self, sandbox_root: Path):
        """Initialize with sandbox root directory."""
        self.sandbox_root = sandbox_root
        self.config_loader = ConfigLoader()
        self.boilerplate_mgr = BoilerplateManager()

    def init_project(self, name: str, config: Dict[str, Any]) -> SandboxProject:
        """
        Initialize new sandbox project.

        Args:
            name: Project name
            config: Initial configuration

        Returns:
            SandboxProject instance

        Raises:
            SandboxExistsError: If project already exists
            ValidationError: If config invalid
        """

    def clean_project(self, name: str) -> None:
        """
        Reset project to clean state.

        Args:
            name: Project name

        Raises:
            SandboxNotFoundError: If project doesn't exist
        """

    def list_projects(self) -> List[SandboxProject]:
        """
        List all sandbox projects.

        Returns:
            List of SandboxProject instances
        """

    def get_project(self, name: str) -> SandboxProject:
        """
        Get project by name.

        Args:
            name: Project name

        Returns:
            SandboxProject instance

        Raises:
            SandboxNotFoundError: If project doesn't exist
        """
```

**Implementation Details:**
- Stores projects in `sandbox_root/projects/<project-name>/`
- Each project has `.sandbox.yaml` with metadata
- Tracks project state (initialized, running, completed, failed)
- Manages project isolation (separate git repos, dependencies)

---

### 3. Boilerplate Manager

**Responsibility**: Clone and configure boilerplate repositories

**Interface:**
```python
class BoilerplateManager:
    """Manages boilerplate repository integration."""

    def clone_repository(
        self,
        repo_url: str,
        destination: Path,
        branch: str = "main"
    ) -> None:
        """
        Clone boilerplate repository.

        Args:
            repo_url: Git repository URL
            destination: Target directory
            branch: Git branch to clone

        Raises:
            CloneError: If git clone fails
        """

    def substitute_variables(
        self,
        project_dir: Path,
        substitutions: Dict[str, str]
    ) -> List[Path]:
        """
        Substitute template variables in files.

        Args:
            project_dir: Project directory
            substitutions: Variable -> value mapping

        Returns:
            List of modified file paths

        Raises:
            SubstitutionError: If substitution fails
        """

    def install_dependencies(
        self,
        project_dir: Path,
        package_manager: str = "pnpm"
    ) -> None:
        """
        Install project dependencies.

        Args:
            project_dir: Project directory
            package_manager: npm, pnpm, or yarn

        Raises:
            InstallError: If installation fails
        """

    def get_template_variables(self, project_dir: Path) -> List[str]:
        """
        Extract template variables from files.

        Args:
            project_dir: Project directory

        Returns:
            List of variable names found (e.g., ["PROJECT_NAME", "AUTHOR"])
        """
```

**Template Variable Detection:**
- Scans files for patterns: `{{VARIABLE_NAME}}`
- Common files: `package.json`, `README.md`, `src/app/layout.tsx`
- Returns list of required substitutions

**Substitution Rules:**
- Case-sensitive replacement
- Recursive through all text files
- Skips binary files, node_modules, .git
- Creates backup before substitution (optional)

---

### 4. Benchmark Runner

**Responsibility**: Execute benchmarks and coordinate workflow

**Interface:**
```python
class BenchmarkRunner:
    """Executes benchmark runs with metric collection."""

    def __init__(
        self,
        sandbox_manager: SandboxManager,
        metrics_collector: MetricsCollector
    ):
        """Initialize with required dependencies."""
        self.sandbox_manager = sandbox_manager
        self.metrics_collector = metrics_collector

    async def run_benchmark(
        self,
        config: BenchmarkConfig,
        callback: Optional[ProgressCallback] = None
    ) -> BenchmarkRun:
        """
        Execute benchmark from configuration.

        Args:
            config: Benchmark configuration
            callback: Optional progress callback

        Returns:
            BenchmarkRun with complete results

        Raises:
            TimeoutError: If benchmark exceeds timeout
            BenchmarkError: If benchmark fails
        """

    def stop_benchmark(self, run_id: str) -> None:
        """
        Stop running benchmark.

        Args:
            run_id: Run identifier

        Raises:
            RunNotFoundError: If run doesn't exist
        """
```

**Execution Flow:**
```
1. Load benchmark config
2. Validate configuration
3. Initialize sandbox project
4. Clone boilerplate
5. Substitute variables
6. Start metrics collection
7. Execute workflow steps:
   a. Analysis phase (if configured)
   b. Planning phase
   c. Solutioning phase
   d. Implementation phase
8. Stop metrics collection
9. Run success criteria checks
10. Generate run report
11. Store results
```

**Timeout Handling:**
- Global timeout from config (default: 1 hour)
- Per-phase timeouts (optional)
- Graceful shutdown on timeout
- Partial results saved

---

### 5. Metrics Collector

**Responsibility**: Collect, aggregate, and store metrics

**Interface:**
```python
class MetricsCollector:
    """Collects and stores benchmark metrics."""

    def start_collection(self, run_id: str) -> None:
        """Start collecting metrics for a run."""

    def stop_collection(self, run_id: str) -> MetricsSnapshot:
        """Stop collecting and return snapshot."""

    def record_event(
        self,
        run_id: str,
        event_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Record a discrete event."""

    def record_metric(
        self,
        run_id: str,
        metric_name: str,
        value: Union[int, float, str],
        category: str = "custom"
    ) -> None:
        """Record a metric value."""

    def get_metrics(self, run_id: str) -> Metrics:
        """Retrieve all metrics for a run."""
```

**Metric Categories:**

#### Performance Metrics
```python
@dataclass
class PerformanceMetrics:
    total_time_seconds: float
    phase_times: Dict[str, float]  # phase_name -> seconds
    token_usage: int
    token_usage_by_agent: Dict[str, int]
    api_calls: int
    api_cost_usd: float
```

#### Autonomy Metrics
```python
@dataclass
class AutonomyMetrics:
    manual_interventions: int
    intervention_types: Dict[str, int]  # type -> count
    prompts_required: int
    one_shot_success_rate: float
    error_recovery_rate: float
    agent_handoffs: int
    failed_handoffs: int
```

#### Quality Metrics
```python
@dataclass
class QualityMetrics:
    tests_written: int
    tests_passing: int
    test_pass_rate: float
    code_coverage_percent: float
    linting_errors: int
    type_errors: int
    security_vulnerabilities: int
    vulnerability_severity: Dict[str, int]
    acceptance_criteria_met: int
    acceptance_criteria_total: int
    functional_completeness_percent: float
```

#### Workflow Metrics
```python
@dataclass
class WorkflowMetrics:
    stories_created: int
    stories_completed: int
    average_story_cycle_time_seconds: float
    phase_distribution: Dict[str, float]  # phase -> % of time
    rework_count: int
```

**Storage:**
- SQLite database for structured metrics
- JSON files for raw event logs
- Schema versioning for compatibility

---

### 6. Report Generator

**Responsibility**: Generate reports from metrics data

**Interface:**
```python
class ReportGenerator:
    """Generates reports from benchmark data."""

    def generate_run_report(
        self,
        run_id: str,
        output_path: Path,
        format: str = "html"
    ) -> Path:
        """
        Generate report for single run.

        Args:
            run_id: Run identifier
            output_path: Where to save report
            format: html, json, or markdown

        Returns:
            Path to generated report
        """

    def generate_comparison_report(
        self,
        run_ids: List[str],
        output_path: Path
    ) -> Path:
        """Generate comparison report for multiple runs."""

    def generate_trend_report(
        self,
        run_ids: List[str],
        output_path: Path
    ) -> Path:
        """Generate trend analysis report."""
```

**Report Templates:**
- Jinja2 templates for HTML reports
- Bootstrap CSS for styling
- Chart.js for visualizations
- Responsive design

**Report Sections:**
1. Executive Summary (KPIs)
2. Performance Details
3. Autonomy Analysis
4. Quality Metrics
5. Workflow Timeline
6. Error Log
7. Artifacts Generated
8. Success Criteria Results

---

## Data Models

### BenchmarkConfig

```python
@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""

    name: str
    description: str
    version: str
    initial_prompt: str

    tech_stack: TechStack
    boilerplate: BoilerplateConfig
    success_criteria: List[SuccessCriterion]
    metrics_enabled: MetricsConfig
    timeout_seconds: int = 3600

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchmarkConfig":
        """Load from YAML file."""

    def to_yaml(self, path: Path) -> None:
        """Save to YAML file."""

    def validate(self) -> List[str]:
        """Validate configuration, return list of errors."""
```

### SandboxProject

```python
@dataclass
class SandboxProject:
    """Represents a sandbox project."""

    name: str
    path: Path
    created_at: datetime
    status: ProjectStatus  # initialized, running, completed, failed
    config: Dict[str, Any]
    benchmark_runs: List[str]  # List of run IDs

    def get_metadata(self) -> Dict[str, Any]:
        """Get project metadata."""

    def update_status(self, status: ProjectStatus) -> None:
        """Update project status."""
```

### BenchmarkRun

```python
@dataclass
class BenchmarkRun:
    """Results from a benchmark run."""

    run_id: str
    benchmark_name: str
    project_name: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: RunStatus  # running, completed, failed, timeout
    config: BenchmarkConfig
    metrics: Metrics
    success_criteria_results: Dict[str, bool]
    artifacts: List[Path]
    error_log: List[ErrorEntry]

    def is_successful(self) -> bool:
        """Check if all success criteria met."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkRun":
        """Load from dictionary."""
```

### Metrics

```python
@dataclass
class Metrics:
    """Complete metrics for a benchmark run."""

    performance: PerformanceMetrics
    autonomy: AutonomyMetrics
    quality: QualityMetrics
    workflow: WorkflowMetrics
    custom: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""

    def calculate_score(self) -> float:
        """
        Calculate overall score (0-100).

        Weighted average:
        - Autonomy: 40%
        - Quality: 30%
        - Performance: 20%
        - Workflow: 10%
        """
```

---

## Integration Points

### 1. GAO-Dev Core Integration

**Current Limitation:**
- Cannot spawn GAO-Dev agents from within Claude Code session
- Agent sessions require standalone execution

**Solutions:**

#### Option A: Standalone Runner (Recommended)
```python
# Create standalone script that runs outside IDE
# sandbox/runner.py

import anthropic
from gao_dev.orchestrator import GAODevOrchestrator

async def run_autonomous_workflow(
    project_path: Path,
    initial_prompt: str,
    api_key: str
) -> BenchmarkRun:
    """Run GAO-Dev workflow standalone."""
    orchestrator = GAODevOrchestrator(project_path)

    # Execute with real API key
    result = await orchestrator.execute_task(initial_prompt)

    return result
```

Usage:
```bash
python -m gao_dev.sandbox.runner \
    --project todo-app \
    --prompt "Build a todo application" \
    --api-key $ANTHROPIC_API_KEY
```

#### Option B: Manual Hybrid Mode
```python
# Generate step-by-step plan, user executes in Claude Code
def generate_execution_plan(config: BenchmarkConfig) -> List[Step]:
    """Generate manual execution steps."""
    return [
        Step("Initialize project", "gao-dev init --name ..."),
        Step("Create PRD", "Provide PRD prompt to Claude Code"),
        Step("Create architecture", "Provide architecture prompt"),
        # etc.
    ]
```

**Recommended**: Use Option A with API key for true autonomous benchmarking.

### 2. Git Integration

**Requirements:**
- Clone boilerplate repos
- Initialize git for new projects
- Commit artifacts during workflow
- Track git history as metrics

**Implementation:**
```python
from gao_dev.core import GitManager

git_mgr = GitManager(config)
git_mgr.clone_repository(url, destination)
git_mgr.git_init()
git_mgr.git_commit(files, message)
```

### 3. File System Integration

**Sandbox Structure:**
```
sandbox/
├── projects/                 # Sandbox projects
│   ├── todo-app-run-001/
│   │   ├── .sandbox.yaml    # Project metadata
│   │   ├── src/             # Cloned boilerplate
│   │   └── .git/
│   └── todo-app-run-002/
├── benchmarks/              # Benchmark configs
│   ├── todo-baseline.yaml
│   └── todo-advanced.yaml
├── metrics/                 # Metrics database
│   ├── metrics.db          # SQLite
│   └── events/             # JSON logs
│       ├── run-001.json
│       └── run-002.json
└── reports/                 # Generated reports
    ├── run-001.html
    └── comparison-001-002.html
```

---

## Technology Stack

### Core Technologies
- **Python 3.11+**: Main language
- **Click**: CLI framework
- **SQLite**: Metrics storage
- **Jinja2**: Report templates
- **PyYAML**: Configuration files

### Additional Dependencies
```toml
[project.dependencies]
# Existing GAO-Dev dependencies
"pyyaml>=6.0"
"gitpython>=3.1.0"
"click>=8.1.0"
"anthropic>=0.34.0"
"claude-agent-sdk>=0.1.0"
"structlog>=24.1.0"

# New sandbox dependencies
"jinja2>=3.1.0"          # Report templates
"matplotlib>=3.7.0"       # Charts (optional)
"requests>=2.31.0"        # HTTP requests
"python-dateutil>=2.8.0"  # Date handling
```

### Frontend Boilerplate (Target Application)
- **Next.js 15**: React framework
- **TypeScript**: Type safety
- **pnpm**: Package manager
- **Biome**: Linter/formatter
- **Prisma**: Database ORM (to be added)

---

## Directory Structure

```
gao_dev/
├── sandbox/                           # NEW: Sandbox module
│   ├── __init__.py
│   ├── models.py                      # Data models
│   ├── sandbox_manager.py             # Sandbox lifecycle
│   ├── boilerplate_manager.py         # Boilerplate integration
│   ├── benchmark_runner.py            # Benchmark execution
│   ├── metrics_collector.py           # Metrics collection
│   ├── report_generator.py            # Report generation
│   ├── templates/                     # Report templates
│   │   ├── run_report.html.j2
│   │   ├── comparison_report.html.j2
│   │   └── styles.css
│   └── schemas/                       # JSON schemas
│       ├── benchmark_config.schema.json
│       └── metrics.schema.json
│
├── cli/
│   ├── commands.py                    # Existing commands
│   └── sandbox_commands.py            # NEW: Sandbox CLI
│
└── ... (existing structure)
```

---

## Interface Definitions

### CLI Interface

```bash
# Sandbox management
gao-dev sandbox init <project-name> [--config <file>]
gao-dev sandbox clean [<project-name>]
gao-dev sandbox list [--status <status>]
gao-dev sandbox delete <project-name>

# Benchmark execution
gao-dev sandbox run <benchmark-config> [--mode <standalone|hybrid>]
gao-dev sandbox stop <run-id>
gao-dev sandbox status <run-id>

# Reporting
gao-dev sandbox report <run-id> [--output <path>] [--format <html|json|md>]
gao-dev sandbox compare <run1> <run2> [--output <path>]
gao-dev sandbox trends --last <n> [--metric <metric-name>]
gao-dev sandbox export <run-id> --format <csv|json> [--output <path>]
```

### Python API

```python
from gao_dev.sandbox import (
    SandboxManager,
    BenchmarkRunner,
    BenchmarkConfig,
    MetricsCollector
)

# Initialize
manager = SandboxManager(Path("./sandbox"))
project = manager.init_project("my-app", config={})

# Run benchmark
config = BenchmarkConfig.from_yaml("benchmarks/todo.yaml")
runner = BenchmarkRunner(manager, MetricsCollector())

async with runner.run_benchmark(config) as run:
    # Monitor progress
    async for event in run.events():
        print(f"Progress: {event}")

# Generate report
from gao_dev.sandbox import ReportGenerator

generator = ReportGenerator()
report_path = generator.generate_run_report(
    run.run_id,
    Path("reports/latest.html")
)
```

---

## Security Considerations

### 1. Code Execution Safety
**Risk**: Executing untrusted code from benchmarks
**Mitigation**:
- Sandboxed execution (containers recommended)
- Timeout enforcement
- Resource limits (CPU, memory)
- No elevated privileges

### 2. Repository Cloning
**Risk**: Cloning malicious repositories
**Mitigation**:
- Validate repository URLs (whitelist domains)
- Shallow clones only
- Scan for suspicious files
- User confirmation for external repos

### 3. File System Access
**Risk**: Overwriting system files
**Mitigation**:
- All operations within sandbox directory
- Path validation (no .. traversal)
- Explicit project isolation

### 4. Metrics Storage
**Risk**: Sensitive data in metrics
**Mitigation**:
- No credentials stored
- Sanitize file paths in logs
- Option to redact sensitive fields

### 5. API Keys
**Risk**: API key exposure
**Mitigation**:
- Environment variables only
- Never log API keys
- Prompt before using API keys

---

## Deployment Architecture

### Local Development
```
Developer Machine
├── GAO-Dev (installed via pip)
├── Sandbox directory (local filesystem)
├── SQLite database (local)
└── Claude Code (IDE integration)
```

### Standalone Benchmarking
```
Dedicated Machine/Container
├── GAO-Dev (installed)
├── Anthropic API key (env variable)
├── Sandbox directory (isolated)
└── Cron job / GitHub Actions (scheduled runs)
```

### Future: CI/CD Integration
```
GitHub Actions
├── Trigger: On PR / Nightly
├── Runner: Ubuntu latest
├── Steps:
│   1. Install GAO-Dev
│   2. Run benchmark
│   3. Upload artifacts
│   4. Post results to PR
└── Artifacts: Reports, metrics
```

---

## Performance Considerations

### 1. Metrics Collection Overhead
**Target**: <5% overhead
**Strategy**:
- Async collection
- Batch writes
- In-memory aggregation

### 2. Report Generation
**Target**: <10 seconds
**Strategy**:
- Template caching
- Lazy chart rendering
- Incremental updates

### 3. Database Size
**Concern**: Metrics database growth
**Strategy**:
- Periodic archival (>30 days)
- Compression for old data
- Cleanup commands

### 4. Git Operations
**Concern**: Large repository clones
**Strategy**:
- Shallow clones (`--depth 1`)
- Sparse checkout
- Caching cloned repos

---

## Testing Strategy

### Unit Tests
- All components independently testable
- Mock external dependencies (Git, API)
- 80%+ code coverage

### Integration Tests
- End-to-end benchmark runs
- Boilerplate integration
- Metrics collection accuracy

### Performance Tests
- Benchmark overhead measurement
- Large project handling
- Concurrent run support

---

## Migration Path

### Phase 1: MVP (Weeks 1-2)
- Sandbox CLI (init, clean, list)
- Basic boilerplate integration
- Manual execution tracking

### Phase 2: Metrics (Weeks 3-4)
- Automated metrics collection
- SQLite storage
- Simple text reports

### Phase 3: Automation (Weeks 5-6)
- Standalone benchmark runner
- HTML reports
- Comparison tools

### Phase 4: Polish (Weeks 7-8)
- Trend analysis
- Performance optimization
- Documentation

---

## Open Technical Questions

1. **API Key Management**: How to securely provide Anthropic API key for standalone mode?
2. **Concurrent Runs**: Should we support multiple benchmarks running simultaneously?
3. **Resource Limits**: What CPU/memory limits for safety?
4. **Metric Sampling**: Should we sample metrics to reduce overhead?
5. **Report Storage**: Local files or database storage?

---

## Appendix A: Benchmark Config Example

```yaml
benchmark:
  name: "todo-app-baseline"
  description: "Full-stack todo app with authentication"
  version: "1.0.0"

  initial_prompt: |
    Build a todo application with the following features:
    - User authentication (register, login, logout)
    - Create, read, update, delete todos
    - Organize todos with categories
    - Set due dates and priorities
    - Responsive UI with accessibility support

  tech_stack:
    frontend: "nextjs"
    backend: "nextjs-api-routes"  # or "fastapi"
    database: "postgresql"
    orm: "prisma"

  boilerplate:
    repo_url: "https://github.com/webventurer/simple-nextjs-starter"
    branch: "main"
    substitutions:
      PROJECT_NAME: "todo-app"
      AUTHOR: "GAO-Dev Team"
      DESCRIPTION: "Full-stack todo application"

  success_criteria:
    - name: "All tests passing"
      type: "test_results"
      threshold: 100

    - name: "Code coverage"
      type: "coverage"
      threshold: 80

    - name: "Zero type errors"
      type: "type_check"
      threshold: 0

    - name: "Authentication working"
      type: "functional"
      validator: "test_auth_flow"

    - name: "CRUD operations working"
      type: "functional"
      validator: "test_todo_crud"

  metrics_enabled:
    performance: true
    autonomy: true
    quality: true
    workflow: true

  timeout: 3600  # 1 hour
```

---

**Architecture Review Status:**
- [ ] Technical review complete
- [ ] Security review complete
- [ ] Approved for implementation

---

*This architecture document defines the technical design for the GAO-Dev Sandbox & Benchmarking System, following clean architecture and SOLID principles.*
