# Story 11.8: Provider Comparison Test Suite

**Epic**: Epic 11 - Agent Provider Abstraction
**Status**: Not Started
**Priority**: P2 (Medium)
**Estimated Effort**: 8 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-04
**Dependencies**: Story 11.2 (ClaudeCodeProvider), Story 11.7 (OpenCodeProvider)

---

## User Story

**As a** GAO-Dev developer
**I want** automated tests that compare provider outputs and behavior
**So that** I can verify provider equivalence and document any differences

---

## Acceptance Criteria

### AC1: Comparison Test Framework Created
- ✅ Test framework supports running same test across multiple providers
- ✅ `@pytest.mark.parametrize` used for provider iteration
- ✅ Test fixtures for provider setup
- ✅ Easy to add new providers to comparison

### AC2: Functional Equivalence Tests
- ✅ Simple task tests (e.g., "Create hello world file")
- ✅ Multi-step task tests
- ✅ File operation tests (read, write, edit)
- ✅ Code generation tests
- ✅ All tests run against ClaudeCode and OpenCode
- ✅ Results compared programmatically where possible

### AC3: Output Comparison
- ✅ Output format compared
- ✅ Content similarity measured
- ✅ Differences documented
- ✅ Known differences whitelisted

### AC4: Performance Comparison
- ✅ Execution time measured per provider
- ✅ Memory usage measured
- ✅ Token usage compared (if available)
- ✅ Performance report generated

### AC5: Compatibility Matrix Created
- ✅ Tool compatibility table generated
- ✅ Model compatibility table generated
- ✅ Feature support matrix
- ✅ Known limitations documented

### AC6: CI Integration
- ✅ Tests added to CI pipeline
- ✅ Run nightly (not on every commit)
- ✅ Results archived
- ✅ Failures reported clearly

### AC7: Report Generation
- ✅ Comparison report script created
- ✅ HTML report with charts
- ✅ Markdown summary for quick review
- ✅ Historical comparison tracking

### AC8: Documentation
- ✅ Comparison test guide created
- ✅ How to add new comparison tests
- ✅ How to interpret results
- ✅ Known differences documented

---

## Technical Details

### File Structure
```
tests/comparison/
├── __init__.py
├── test_provider_comparison.py      # Main comparison tests
├── test_provider_parity.py          # Parity validation tests
├── fixtures/
│   ├── comparison_tasks.yaml        # Test tasks
│   └── expected_behaviors.yaml      # Expected results
└── conftest.py                      # Shared fixtures

scripts/
└── generate_comparison_report.py    # Report generator

docs/
└── provider-comparison-results.md   # Latest results
```

### Implementation Approach

#### Step 1: Create Comparison Test Framework

**File**: `tests/comparison/conftest.py`

```python
"""Shared fixtures for provider comparison tests."""

import pytest
from pathlib import Path
from typing import List

from gao_dev.core.providers.factory import ProviderFactory
from gao_dev.core.providers.base import IAgentProvider


@pytest.fixture
def provider_factory():
    """Provide a provider factory instance."""
    return ProviderFactory()


@pytest.fixture(params=["claude-code", "opencode"])
def provider_name(request):
    """Parametrize tests across all providers."""
    return request.param


@pytest.fixture
def provider(provider_factory, provider_name):
    """Create provider instance for testing."""
    return provider_factory.create_provider(provider_name)


@pytest.fixture
def providers(provider_factory) -> List[IAgentProvider]:
    """Create all providers for comparison."""
    provider_names = provider_factory.list_providers()
    return [
        provider_factory.create_provider(name)
        for name in provider_names
    ]


@pytest.fixture
def comparison_workspace(tmp_path):
    """Create a temporary workspace for comparison tests."""
    workspace = tmp_path / "comparison_workspace"
    workspace.mkdir()
    return workspace
```

#### Step 2: Create Comparison Tests

**File**: `tests/comparison/test_provider_comparison.py`

```python
"""Provider comparison tests."""

import pytest
import time
from pathlib import Path

from gao_dev.core.providers.models import AgentContext


@pytest.mark.comparison
@pytest.mark.asyncio
class TestProviderComparison:
    """Compare providers for identical tasks."""

    async def test_simple_file_creation(self, provider, comparison_workspace):
        """Test simple file creation across all providers."""
        task = "Create a file named 'hello.txt' with content 'Hello, World!'"

        context = AgentContext(project_root=comparison_workspace)

        # Execute task
        start_time = time.time()
        results = []
        async for result in provider.execute_task(
            task=task,
            context=context,
            model="sonnet-4.5",
            tools=["Write"],
            timeout=60
        ):
            results.append(result)
        duration = time.time() - start_time

        # Verify file created
        hello_file = comparison_workspace / "hello.txt"
        assert hello_file.exists(), f"{provider.name} did not create file"

        content = hello_file.read_text()
        assert "Hello, World!" in content, f"{provider.name} wrong content"

        # Log performance
        print(f"\n{provider.name}: {duration:.2f}s")

    async def test_code_generation(self, provider, comparison_workspace):
        """Test code generation across all providers."""
        task = """
        Create a Python file 'fibonacci.py' with a function that calculates
        the nth Fibonacci number using recursion.
        """

        context = AgentContext(project_root=comparison_workspace)

        # Execute task
        results = []
        async for result in provider.execute_task(
            task=task,
            context=context,
            model="sonnet-4.5",
            tools=["Write"],
            timeout=120
        ):
            results.append(result)

        # Verify file created
        fib_file = comparison_workspace / "fibonacci.py"
        assert fib_file.exists(), f"{provider.name} did not create file"

        # Verify content has expected elements
        content = fib_file.read_text()
        assert "def" in content, f"{provider.name} missing function definition"
        assert "fibonacci" in content.lower(), f"{provider.name} wrong function name"

    async def test_multi_file_task(self, provider, comparison_workspace):
        """Test multi-file creation across providers."""
        task = """
        Create a simple Python project:
        1. main.py with a hello world function
        2. utils.py with a helper function
        3. README.md with project description
        """

        context = AgentContext(project_root=comparison_workspace)

        # Execute task
        async for _ in provider.execute_task(
            task=task,
            context=context,
            model="sonnet-4.5",
            tools=["Write"],
            timeout=180
        ):
            pass

        # Verify all files created
        assert (comparison_workspace / "main.py").exists()
        assert (comparison_workspace / "utils.py").exists()
        assert (comparison_workspace / "README.md").exists()


@pytest.mark.comparison
@pytest.mark.asyncio
class TestProviderPerformance:
    """Compare provider performance."""

    async def test_performance_simple_task(self, providers, comparison_workspace):
        """Compare performance for simple task."""
        task = "Create a file 'test.txt' with content 'test'"

        results = {}

        for provider in providers:
            context = AgentContext(project_root=comparison_workspace / provider.name)
            context.project_root.mkdir(exist_ok=True)

            start_time = time.time()
            async for _ in provider.execute_task(
                task=task,
                context=context,
                model="sonnet-4.5",
                tools=["Write"],
                timeout=60
            ):
                pass
            duration = time.time() - start_time

            results[provider.name] = duration

        # Print comparison
        print("\nPerformance Comparison (simple task):")
        for name, duration in sorted(results.items(), key=lambda x: x[1]):
            print(f"  {name}: {duration:.2f}s")

        # Assert all completed successfully
        assert len(results) == len(providers)

    async def test_performance_complex_task(self, providers, comparison_workspace):
        """Compare performance for complex task."""
        task = """
        Create a complete REST API in Python using FastAPI:
        - main.py with FastAPI app
        - models.py with Pydantic models
        - routes.py with API endpoints
        - requirements.txt with dependencies
        """

        results = {}

        for provider in providers:
            context = AgentContext(project_root=comparison_workspace / provider.name)
            context.project_root.mkdir(exist_ok=True)

            start_time = time.time()
            try:
                async for _ in provider.execute_task(
                    task=task,
                    context=context,
                    model="sonnet-4.5",
                    tools=["Write"],
                    timeout=300
                ):
                    pass
                duration = time.time() - start_time
                results[provider.name] = {"duration": duration, "success": True}
            except Exception as e:
                duration = time.time() - start_time
                results[provider.name] = {"duration": duration, "success": False, "error": str(e)}

        # Print comparison
        print("\nPerformance Comparison (complex task):")
        for name, result in sorted(results.items(), key=lambda x: x[1]["duration"]):
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {name}: {result['duration']:.2f}s")


@pytest.mark.comparison
class TestProviderParity:
    """Test provider parity and compatibility."""

    def test_tool_support_parity(self, providers):
        """Compare tool support across providers."""
        tools_to_test = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]

        support_matrix = {}
        for provider in providers:
            support_matrix[provider.name] = {
                tool: provider.supports_tool(tool)
                for tool in tools_to_test
            }

        # Print matrix
        print("\nTool Support Matrix:")
        print(f"{'Tool':<15} " + " ".join(f"{p.name:<12}" for p in providers))
        print("-" * (15 + 13 * len(providers)))

        for tool in tools_to_test:
            row = f"{tool:<15} "
            for provider in providers:
                supported = support_matrix[provider.name][tool]
                symbol = "✓" if supported else "✗"
                row += f"{symbol:<12} "
            print(row)

    def test_model_support_parity(self, providers):
        """Compare model support across providers."""
        # Test common model names
        models_to_test = ["sonnet-4.5", "sonnet-3.5", "opus-3", "gpt-4"]

        support_matrix = {}
        for provider in providers:
            supported_models = provider.get_supported_models()
            support_matrix[provider.name] = {
                model: model in supported_models
                for model in models_to_test
            }

        # Print matrix
        print("\nModel Support Matrix:")
        print(f"{'Model':<15} " + " ".join(f"{p.name:<12}" for p in providers))
        print("-" * (15 + 13 * len(providers)))

        for model in models_to_test:
            row = f"{model:<15} "
            for provider in providers:
                supported = support_matrix[provider.name][model]
                symbol = "✓" if supported else "✗"
                row += f"{symbol:<12} "
            print(row)
```

#### Step 3: Create Report Generator

**File**: `scripts/generate_comparison_report.py`

```python
#!/usr/bin/env python3
"""Generate provider comparison report from test results."""

import json
import sys
from pathlib import Path
from datetime import datetime


def generate_report(test_results_file: Path, output_file: Path):
    """
    Generate HTML comparison report.

    Args:
        test_results_file: Path to pytest JSON results
        output_file: Path to output HTML file
    """
    # Load test results
    with open(test_results_file) as f:
        results = json.load(f)

    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Provider Comparison Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .pass {{ color: green; }}
            .fail {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Provider Comparison Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Summary</h2>
        <table>
            <tr>
                <th>Provider</th>
                <th>Tests Passed</th>
                <th>Tests Failed</th>
                <th>Avg Duration</th>
            </tr>
            <!-- Results will be inserted here -->
        </table>

        <h2>Detailed Results</h2>
        <!-- Detailed results will be inserted here -->
    </body>
    </html>
    """

    # Write report
    output_file.write_text(html)
    print(f"Report generated: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_comparison_report.py <test_results.json> <output.html>")
        sys.exit(1)

    generate_report(Path(sys.argv[1]), Path(sys.argv[2]))
```

#### Step 4: Create Comparison Task Definitions

**File**: `tests/comparison/fixtures/comparison_tasks.yaml`

```yaml
# Standard comparison tasks for provider testing

tasks:
  - id: simple_file
    description: "Create a simple text file"
    task: "Create a file named 'hello.txt' with content 'Hello, World!'"
    expected_files:
      - hello.txt
    timeout: 60

  - id: python_function
    description: "Generate a Python function"
    task: "Create a Python file 'math_utils.py' with a function to calculate factorial"
    expected_files:
      - math_utils.py
    expected_content:
      - "def"
      - "factorial"
    timeout: 120

  - id: multi_file_project
    description: "Create a multi-file project"
    task: |
      Create a simple Python project:
      1. main.py with a main function
      2. utils.py with helper functions
      3. README.md with project description
      4. requirements.txt (can be empty)
    expected_files:
      - main.py
      - utils.py
      - README.md
      - requirements.txt
    timeout: 180
```

---

## Testing Strategy

### Comparison Tests
- Functional equivalence (same task, different providers)
- Performance comparison (time, memory)
- Output comparison (format, content)

### Compatibility Tests
- Tool support matrix
- Model support matrix
- Feature parity

### Report Generation
- Automated HTML reports
- Historical tracking
- Trend analysis

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Comparison test framework created
- [ ] Functional equivalence tests passing
- [ ] Performance comparison tests complete
- [ ] Compatibility matrix generated
- [ ] CI integration complete
- [ ] Report generator working
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Changes committed

---

## Dependencies

**Upstream**:
- Story 11.2 (ClaudeCodeProvider) - MUST be complete
- Story 11.7 (OpenCodeProvider) - MUST be complete

**Downstream**:
- Informs provider optimization decisions
- Validates provider abstraction quality

---

## Notes

- Tests should be non-blocking (failures don't block development)
- Focus on functional equivalence, not identical output
- Document known differences clearly
- Performance comparison informative, not prescriptive
- Add new providers to comparison as they're implemented

---

## Related Documents

- PRD: `docs/features/agent-provider-abstraction/PRD.md`
- Architecture: `docs/features/agent-provider-abstraction/ARCHITECTURE.md`
- Story 11.2: `story-11.2.md` (ClaudeCodeProvider)
- Story 11.7: `story-11.7.md` (OpenCodeProvider)
