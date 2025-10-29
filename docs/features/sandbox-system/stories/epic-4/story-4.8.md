# Story 4.8: Standalone Execution Mode (Programmatic Claude CLI)

**Epic**: Epic 4 - Benchmark Runner
**Status**: In Progress
**Priority**: P1 (High)
**Estimated Effort**: 4 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Updated**: 2025-10-29

---

## User Story

**As a** developer running benchmarks
**I want** to execute benchmarks using programmatic Claude CLI mode
**So that** benchmarks can run non-interactively with full agent-sdk capabilities

---

## Acceptance Criteria

### AC1: Programmatic Claude CLI Configuration
- [ ] ClaudeAgentOptions configured with cli_path
- [ ] Uses Claude CLI in --print mode for non-interactive execution
- [ ] Passes API key via environment to CLI process
- [ ] Permission mode set to "bypassPermissions" for benchmarks
- [ ] Working directory set to sandbox project

### AC2: CLI Path Detection
- [ ] Automatically detects Claude CLI path
- [ ] Supports Windows (claude.bat) and Unix (claude)
- [ ] Fallback paths checked in order
- [ ] Clear error if Claude CLI not found
- [ ] Validates CLI is executable

### AC3: API Key Management
- [ ] API key passed to Claude CLI via env vars
- [ ] Reads from .env file (already working)
- [ ] Reads from ANTHROPIC_API_KEY environment
- [ ] Validates API key before starting
- [ ] Secure key handling (no logging)

### AC4: Benchmark Mode Configuration
- [ ] permission_mode="bypassPermissions" for sandbox safety
- [ ] extra_args configured for --print mode
- [ ] add_dirs includes project_root for file access
- [ ] Keeps full agent-sdk capabilities (agents, MCP, tools)
- [ ] Non-interactive execution

### AC5: Agent Orchestration
- [ ] Agent spawning works in programmatic mode
- [ ] Subagents can be created (Task tool)
- [ ] MCP servers accessible
- [ ] Tool use works correctly
- [ ] Output captured and logged

---

## Technical Details

### Implementation Approach

**Key Insight**: Use agent-sdk's programmatic capabilities instead of replacing with basic API.

**Benefits**:
- Keeps agent orchestration, MCP integration, tool management
- Uses Claude CLI `--print` mode for non-interactive execution
- Leverages `permission_mode="bypassPermissions"` for sandbox safety
- Full agentic harness capabilities maintained

**Updated Module**: `gao_dev/core/cli_detector.py` (New)

```python
"""Detect Claude CLI installation."""

import os
import shutil
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()


def find_claude_cli() -> Optional[Path]:
    """
    Find Claude CLI executable.

    Checks locations in priority order:
    1. 'claude' or 'claude.bat' in PATH
    2. VS Code extension directory
    3. Common installation locations

    Returns:
        Path to Claude CLI or None if not found
    """
    # Try PATH first
    if os.name == 'nt':  # Windows
        claude_cmd = shutil.which('claude.bat') or shutil.which('claude.cmd')
    else:  # Unix
        claude_cmd = shutil.which('claude')

    if claude_cmd:
        logger.debug("found_claude_cli_in_path", path=claude_cmd)
        return Path(claude_cmd)

    # Try VS Code extension directory
    home = Path.home()
    vscode_ext = home / '.vscode' / 'extensions'

    if vscode_ext.exists():
        # Find latest anthropic.claude-code extension
        claude_dirs = sorted(vscode_ext.glob('anthropic.claude-code-*'))
        if claude_dirs:
            cli_js = claude_dirs[-1] / 'resources' / 'claude-code' / 'cli.js'
            if cli_js.exists():
                logger.debug("found_claude_cli_in_vscode", path=str(cli_js))
                return cli_js

    # Try common locations (Windows)
    if os.name == 'nt':
        common_paths = [
            Path(os.environ.get('USERPROFILE', '')) / 'bin' / 'claude.bat',
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'claude' / 'claude.bat',
        ]
        for path in common_paths:
            if path.exists():
                logger.debug("found_claude_cli_common", path=str(path))
                return path

    logger.warning("claude_cli_not_found")
    return None
```

**Updated Module**: `gao_dev/orchestrator/orchestrator.py`

```python
# Key changes to __init__:

def __init__(self, project_root: Path, api_key: Optional[str] = None, mode: str = "cli"):
    """
    Initialize the GAO-Dev orchestrator.

    Args:
        project_root: Root directory of the project
        api_key: Optional Anthropic API key
        mode: Execution mode - "cli", "benchmark", or "api"
    """
    self.project_root = project_root
    self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    self.mode = mode

    # ... existing code ...

    # NEW: Find Claude CLI for programmatic execution
    from ..core.cli_detector import find_claude_cli
    cli_path = find_claude_cli()

    if not cli_path and mode == "benchmark":
        raise ValueError("Claude CLI not found. Cannot run in benchmark mode.")

    # Configure main orchestrator options FOR PROGRAMMATIC EXECUTION
    self.options = ClaudeAgentOptions(
        # Point to Claude CLI executable
        cli_path=cli_path,

        # Set working directory to project
        cwd=self.project_root,

        # Pass API key via environment (secure)
        env={"ANTHROPIC_API_KEY": self.api_key} if self.api_key else {},

        # Model configuration
        model="claude-sonnet-4",

        # Permission mode: bypass for benchmarks (sandbox-safe)
        permission_mode="bypassPermissions" if mode == "benchmark" else "default",

        # Agent definitions (keeps agent orchestration)
        agents=AGENT_DEFINITIONS,

        # MCP servers (keeps MCP integration)
        mcp_servers={"gao_dev": gao_dev_server},

        # Tools (keeps tool management)
        allowed_tools=[...],  # Same as before

        # Grant access to project directory
        add_dirs=[self.project_root],

        # For benchmark mode: configure for non-interactive --print mode
        # (The SDK will use these when spawning Claude CLI)
        max_turns=None,  # Let benchmark determine turns
    )
```

**New Module**: `gao_dev/sandbox/benchmark/standalone.py` (Simplified)

```python
"""Programmatic benchmark execution using Claude CLI."""

class StandaloneRunner:
    """
    Runs benchmarks using programmatic Claude CLI mode.

    Uses agent-sdk with Claude CLI configured for non-interactive
    --print mode execution, maintaining full agentic capabilities.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cli_path: Optional[Path] = None,
        sandbox_root: Path = Path("sandbox")
    ):
        """
        Initialize standalone runner.

        Args:
            api_key: Anthropic API key (optional if in environment)
            cli_path: Path to Claude CLI (auto-detected if not provided)
            sandbox_root: Root directory for sandbox projects

        Raises:
            ValueError: If API key not found or CLI not found
        """
        self.api_key = self._get_api_key(api_key)
        self.cli_path = cli_path or find_claude_cli()

        if not self.cli_path:
            raise ValueError(
                "Claude CLI not found. Install Claude Code or provide --cli-path"
            )

        self.sandbox_root = sandbox_root
        self.logger = logger.bind(component="StandaloneRunner")

    def _get_api_key(self, api_key: Optional[str]) -> str:
        """
        Get API key from various sources.

        Priority:
        1. Explicit api_key parameter
        2. API key file
        3. ANTHROPIC_API_KEY environment variable

        Args:
            api_key: Explicit API key
            api_key_file: Path to API key file

        Returns:
            API key string

        Raises:
            ValueError: If API key not found
        """
        # Try explicit key first
        if api_key:
            return api_key

        # Try API key file
        if api_key_file and api_key_file.exists():
            with open(api_key_file, 'r') as f:
                return f.read().strip()

        # Try environment variable
        env_key = os.getenv("ANTHROPIC_API_KEY")
        if env_key:
            return env_key

        raise ValueError(
            "API key not found. Provide via --api-key, --api-key-file, "
            "or ANTHROPIC_API_KEY environment variable"
        )

    def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """
        Run a benchmark in standalone mode.

        Args:
            config: Benchmark configuration

        Returns:
            BenchmarkResult with all metrics and status
        """
        self.logger.info(
            "standalone_benchmark_started",
            benchmark=config.name,
            mode="standalone"
        )

        # Initialize components
        sandbox_manager = SandboxManager(self.sandbox_root)
        boilerplate_manager = BoilerplateManager()
        metrics_collector = MetricsCollector()

        # Create benchmark runner
        runner = BenchmarkRunner(
            config=config,
            sandbox_manager=sandbox_manager,
            boilerplate_manager=boilerplate_manager,
            metrics_collector=metrics_collector,
            sandbox_root=self.sandbox_root
        )

        # Run benchmark
        result = runner.run()

        # Save results
        self._save_results(result)

        self.logger.info(
            "standalone_benchmark_completed",
            benchmark=config.name,
            status=result.status.value,
            duration=result.duration_seconds
        )

        return result

    def _save_results(self, result: BenchmarkResult) -> None:
        """
        Save benchmark results to file.

        Args:
            result: Benchmark result to save
        """
        output_dir = self.sandbox_root / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{result.run_id}.json"

        import json
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        self.logger.info("results_saved", output_file=str(output_file))

    def validate_api_key(self) -> bool:
        """
        Validate that API key is valid.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try a simple API call to validate key
            # This is a placeholder - actual validation would call Anthropic API
            return len(self.api_key) > 0
        except Exception as e:
            self.logger.error("api_key_validation_failed", error=str(e))
            return False


# CLI Integration
def add_standalone_commands(parent_group):
    """
    Add standalone mode commands to CLI.

    Args:
        parent_group: Click command group to add to
    """
    import click

    @parent_group.command(name="run-standalone")
    @click.argument("config_file", type=click.Path(exists=True))
    @click.option("--api-key", help="Anthropic API key")
    @click.option("--api-key-file", type=click.Path(), help="Path to API key file")
    @click.option("--sandbox-root", type=click.Path(), default="sandbox", help="Sandbox root directory")
    def run_standalone(config_file: str, api_key: str, api_key_file: str, sandbox_root: str):
        """
        Run benchmark in standalone mode using Anthropic API.

        Requires ANTHROPIC_API_KEY environment variable or --api-key option.

        Example:
            gao-dev sandbox run-standalone benchmarks/todo-app.yaml
        """
        import sys
        from .config import BenchmarkConfig

        try:
            # Load config
            config = BenchmarkConfig.from_yaml(Path(config_file))

            # Create standalone runner
            runner = StandaloneRunner(
                api_key=api_key,
                api_key_file=Path(api_key_file) if api_key_file else None,
                sandbox_root=Path(sandbox_root)
            )

            # Validate API key
            if not runner.validate_api_key():
                click.echo("ERROR: Invalid API key", err=True)
                sys.exit(1)

            # Run benchmark
            result = runner.run_benchmark(config)

            # Print summary
            click.echo(result.summary())

            # Exit with appropriate code
            sys.exit(0 if result.status.value == "completed" else 1)

        except Exception as e:
            click.echo(f"ERROR: {e}", err=True)
            sys.exit(1)
```

**CLI Update**: `gao_dev/cli/sandbox_commands.py`

```python
# Add to existing sandbox commands

@sandbox.command(name="run")
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--standalone", is_flag=True, help="Run in standalone mode with API key")
@click.option("--api-key", help="Anthropic API key (for standalone mode)")
@click.option("--api-key-file", type=click.Path(), help="Path to API key file")
def run_benchmark(config_file: str, standalone: bool, api_key: str, api_key_file: str):
    """
    Run a benchmark.

    Without --standalone: Runs in current Claude Code session
    With --standalone: Runs using Anthropic API (requires API key)

    Examples:
        # Interactive mode
        gao-dev sandbox run benchmarks/todo-app.yaml

        # Standalone mode
        gao-dev sandbox run benchmarks/todo-app.yaml --standalone --api-key sk-...
    """
    if standalone:
        # Use standalone runner
        from gao_dev.sandbox.benchmark.standalone import StandaloneRunner
        from gao_dev.sandbox.benchmark.config import BenchmarkConfig

        config = BenchmarkConfig.from_yaml(Path(config_file))
        runner = StandaloneRunner(
            api_key=api_key,
            api_key_file=Path(api_key_file) if api_key_file else None
        )
        result = runner.run_benchmark(config)
        click.echo(result.summary())
    else:
        # Use interactive runner (current session)
        click.echo("Interactive mode not yet implemented")
        click.echo("Use --standalone flag for now")
```

---

## Dependencies

- Story 4.3 (Benchmark Runner Core)
- All Epic 4 stories (4.1-4.7)

---

## Definition of Done

- [ ] StandaloneRunner class implemented
- [ ] API key management implemented
- [ ] CLI command for standalone mode added
- [ ] Can run benchmarks non-interactively
- [ ] Results saved to files
- [ ] API key validation working
- [ ] Secure key handling
- [ ] Clear error messages
- [ ] Type hints for all methods
- [ ] Unit tests written (>80% coverage)
- [ ] Integration test with real API (optional, mocked)
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

---

## Test Strategy

### Unit Tests

**Test File**: `tests/sandbox/benchmark/test_standalone.py`

```python
def test_standalone_runner_creation():
    """Test creating StandaloneRunner."""

def test_get_api_key_from_env():
    """Test getting API key from environment."""

def test_get_api_key_from_file():
    """Test getting API key from file."""

def test_get_api_key_explicit():
    """Test using explicit API key."""

def test_api_key_not_found_raises():
    """Test that missing API key raises error."""

def test_validate_api_key():
    """Test API key validation."""

def test_run_benchmark_standalone():
    """Test running benchmark in standalone mode."""

def test_save_results():
    """Test saving results to file."""
```

### Integration Tests (Optional)

**Test File**: `tests/sandbox/benchmark/test_standalone_integration.py`

```python
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_standalone_benchmark_with_real_api():
    """Test standalone benchmark with real Anthropic API."""
```

---

## Notes

- API key must never be logged or printed
- Standalone mode is critical for CI/CD and scheduled benchmarks
- Consider rate limiting and cost management for API usage
- Future: Add support for other Claude API providers
