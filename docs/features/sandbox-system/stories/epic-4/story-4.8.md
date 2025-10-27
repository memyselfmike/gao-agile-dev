# Story 4.8: Standalone Execution Mode

**Epic**: Epic 4 - Benchmark Runner
**Status**: Ready
**Priority**: P1 (High)
**Estimated Effort**: 4 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer running benchmarks
**I want** to execute benchmarks in standalone mode with API key
**So that** benchmarks can run without interactive Claude Code sessions

---

## Acceptance Criteria

### AC1: Standalone Runner
- [ ] StandaloneRunner class implemented
- [ ] Uses Anthropic API key for agent spawning
- [ ] Runs completely non-interactively
- [ ] No dependency on Claude Code session
- [ ] Can be scheduled or run in CI/CD

### AC2: API Key Management
- [ ] Reads API key from environment variable
- [ ] Reads API key from config file
- [ ] Validates API key before starting
- [ ] Secure key handling (no logging)
- [ ] Clear error if key missing/invalid

### AC3: CLI Integration
- [ ] `gao-dev sandbox run --standalone` flag
- [ ] `--api-key` option for explicit key
- [ ] `--api-key-file` option for key file
- [ ] Works with all benchmark configs
- [ ] Exit codes indicate success/failure

### AC4: Agent Spawning
- [ ] Can spawn GAO-Dev agents using SDK
- [ ] Passes tools to agents correctly
- [ ] Captures agent outputs
- [ ] Handles agent errors
- [ ] Logs all agent interactions

### AC5: Headless Operation
- [ ] No interactive prompts
- [ ] All progress to structured logs
- [ ] Results saved to files
- [ ] Can run unattended
- [ ] Provides run summary at end

---

## Technical Details

### Implementation Approach

**New Module**: `gao_dev/sandbox/benchmark/standalone.py`

```python
"""Standalone benchmark execution using Anthropic API."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import structlog

from anthropic import Anthropic
from .runner import BenchmarkRunner, BenchmarkResult
from .config import BenchmarkConfig
from ..sandbox_manager import SandboxManager
from ..boilerplate.manager import BoilerplateManager
from ..metrics.collector import MetricsCollector


logger = structlog.get_logger()


class StandaloneRunner:
    """
    Runs benchmarks in standalone mode using Anthropic API.

    This mode allows benchmarks to run non-interactively without
    a Claude Code session, using an API key for agent spawning.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_file: Optional[Path] = None,
        sandbox_root: Path = Path("sandbox")
    ):
        """
        Initialize standalone runner.

        Args:
            api_key: Anthropic API key (optional if in environment)
            api_key_file: Path to file containing API key
            sandbox_root: Root directory for sandbox projects

        Raises:
            ValueError: If API key not found
        """
        self.api_key = self._get_api_key(api_key, api_key_file)
        self.sandbox_root = sandbox_root
        self.client = Anthropic(api_key=self.api_key)
        self.logger = logger.bind(component="StandaloneRunner")

    def _get_api_key(
        self,
        api_key: Optional[str],
        api_key_file: Optional[Path]
    ) -> str:
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
