"""
Pytest configuration and fixtures for Epic 6 regression tests.

These fixtures provide test data for regression testing of:
- GAODevOrchestrator (before service extraction)
- SandboxManager (before service extraction)
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
from datetime import datetime

# =============================================================================
# Epic 6 Baseline Data
# =============================================================================

@pytest.fixture
def baseline_dir() -> Path:
    """
    Directory for storing baseline data.

    Returns:
        Path: tests/regression/epic_6/baselines/
    """
    baseline_path = Path(__file__).parent / "baselines"
    baseline_path.mkdir(exist_ok=True)
    return baseline_path


@pytest.fixture
def baseline_mode(request) -> str:
    """
    Baseline mode: 'capture', 'compare', or 'validate'.

    Usage:
        pytest --baseline-mode=capture  # Capture baseline
        pytest --baseline-mode=compare  # Compare to baseline
        pytest (default)                # Just validate tests pass

    Returns:
        str: Baseline mode
    """
    return request.config.getoption("--baseline-mode", default="validate")


def pytest_addoption(parser):
    """Add command-line options for baseline testing."""
    parser.addoption(
        "--baseline-mode",
        action="store",
        default="validate",
        choices=["capture", "compare", "validate"],
        help="Baseline testing mode: capture, compare, or validate"
    )


# =============================================================================
# Orchestrator Fixtures
# =============================================================================

@pytest.fixture
def orchestrator_test_project(temp_dir: Path) -> Path:
    """
    Create a realistic test project for orchestrator testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Root of test project
    """
    # Create directory structure
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "features").mkdir()
    (temp_dir / "docs" / "features" / "test-feature").mkdir()
    (temp_dir / "docs" / "features" / "test-feature" / "stories").mkdir()
    (temp_dir / "docs" / "features" / "test-feature" / "stories" / "epic-1").mkdir()
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()
    (temp_dir / "bmad").mkdir()
    (temp_dir / "bmad" / "bmm").mkdir()
    (temp_dir / "bmad" / "bmm" / "workflows").mkdir()
    (temp_dir / "gao_dev").mkdir()
    (temp_dir / "gao_dev" / "agents").mkdir()

    # Create bmad config
    bmad_config = temp_dir / "bmad" / "bmm" / "config.yaml"
    bmad_config.write_text("""
name: "Test Project"
methodology: "BMAD"
scale_level: 3
feature: "Test Feature"
""")

    # Create sample PRD
    prd_content = """# Product Requirements Document

## Project Name
Test Project

## Overview
Test project for regression testing.

## Goals
- Goal 1
- Goal 2

## Success Criteria
- Criteria 1
- Criteria 2
"""
    (temp_dir / "docs" / "features" / "test-feature" / "PRD.md").write_text(prd_content)

    # Create sample story file
    story_content = """# Story 1.1: Test Story

**Status**: backlog
**Points**: 3

## User Story
As a developer
I want to test the system
So that I can verify it works

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
"""
    (temp_dir / "docs" / "features" / "test-feature" / "stories" / "epic-1" / "story-1.1.md").write_text(story_content)

    # Create sample agent persona
    agent_content = """# Mary - Business Analyst

**Role**: Business Analysis, Research, Requirements Gathering

## Personality
Professional and thorough.

## Tools
- Read
- Write
- Grep
- Glob
"""
    (temp_dir / "gao_dev" / "agents" / "mary.md").write_text(agent_content)

    return temp_dir


# =============================================================================
# Sandbox Fixtures
# =============================================================================

@pytest.fixture
def sandbox_test_root(temp_dir: Path) -> Path:
    """
    Create a test sandbox root directory.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Sandbox root directory
    """
    sandbox_root = temp_dir / "sandbox"
    sandbox_root.mkdir()
    return sandbox_root


@pytest.fixture
def sample_boilerplate(temp_dir: Path) -> Path:
    """
    Create a sample boilerplate directory for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Boilerplate directory
    """
    boilerplate_dir = temp_dir / "boilerplate"
    boilerplate_dir.mkdir()

    # Create boilerplate structure
    (boilerplate_dir / "src").mkdir()
    (boilerplate_dir / "tests").mkdir()
    (boilerplate_dir / "docs").mkdir()

    # Create files with template variables
    (boilerplate_dir / "README.md").write_text("""# {{project_name}}

{{project_description}}

## Getting Started
Instructions here.
""")

    (boilerplate_dir / "src" / "main.py").write_text("""'''{{project_name}} - Main module.'''

def main():
    print("Hello from {{project_name}}!")

if __name__ == "__main__":
    main()
""")

    (boilerplate_dir / "package.json").write_text("""{
  "name": "{{project_name}}",
  "version": "0.1.0",
  "description": "{{project_description}}",
  "dependencies": {}
}
""")

    return boilerplate_dir


# =============================================================================
# Performance Baseline Fixtures
# =============================================================================

@pytest.fixture
def performance_baseline_file(baseline_dir: Path) -> Path:
    """
    Path to performance baseline JSON file.

    Args:
        baseline_dir: Baseline directory fixture

    Returns:
        Path: Performance baseline file path
    """
    return baseline_dir / "performance_baseline.json"


def load_performance_baseline(filepath: Path) -> Dict[str, Any]:
    """
    Load performance baseline data.

    Args:
        filepath: Path to baseline JSON file

    Returns:
        Dict: Baseline data
    """
    if not filepath.exists():
        return {}

    with open(filepath, "r") as f:
        return json.load(f)


def save_performance_baseline(filepath: Path, data: Dict[str, Any]) -> None:
    """
    Save performance baseline data.

    Args:
        filepath: Path to baseline JSON file
        data: Baseline data to save
    """
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


@pytest.fixture
def capture_performance_metric(performance_baseline_file: Path, baseline_mode: str):
    """
    Fixture for capturing or comparing performance metrics.

    Usage in test:
        with capture_performance_metric("test_name", duration, "seconds"):
            # Test will compare to baseline or capture baseline
            pass
    """
    def _capture(test_name: str, value: float, unit: str, tolerance: float = 0.05):
        """
        Capture or compare performance metric.

        Args:
            test_name: Name of the test
            value: Measured value
            unit: Unit of measurement
            tolerance: Acceptable variance (default 5%)
        """
        baseline_data = load_performance_baseline(performance_baseline_file)

        if baseline_mode == "capture":
            # Capture baseline
            baseline_data[test_name] = {
                "baseline_value": value,
                "unit": unit,
                "tolerance": tolerance,
                "min_acceptable": value * (1 - tolerance),
                "max_acceptable": value * (1 + tolerance),
                "measured_date": datetime.now().isoformat(),
            }
            save_performance_baseline(performance_baseline_file, baseline_data)
            print(f"\n[BASELINE CAPTURED] {test_name}: {value} {unit}")

        elif baseline_mode == "compare":
            # Compare to baseline
            if test_name not in baseline_data:
                pytest.skip(f"No baseline for {test_name}. Run with --baseline-mode=capture first.")

            baseline = baseline_data[test_name]
            min_val = baseline["min_acceptable"]
            max_val = baseline["max_acceptable"]
            baseline_val = baseline["baseline_value"]

            variance_pct = ((value - baseline_val) / baseline_val) * 100

            print(f"\n[BASELINE COMPARE] {test_name}:")
            print(f"  Baseline: {baseline_val} {unit}")
            print(f"  Current:  {value} {unit}")
            print(f"  Variance: {variance_pct:+.2f}%")
            print(f"  Range:    [{min_val:.4f}, {max_val:.4f}]")

            assert min_val <= value <= max_val, (
                f"Performance regression detected for {test_name}!\n"
                f"  Baseline: {baseline_val} {unit}\n"
                f"  Current:  {value} {unit}\n"
                f"  Variance: {variance_pct:+.2f}%\n"
                f"  Acceptable range: [{min_val:.4f}, {max_val:.4f}]"
            )

        # else: validate mode - just run the test

    return _capture


# =============================================================================
# Workflow Fixtures
# =============================================================================

@pytest.fixture
def sample_workflow_sequence() -> list:
    """
    Sample workflow sequence for testing.

    Returns:
        List of workflow identifiers
    """
    return [
        "analyze-requirements",
        "create-architecture",
        "implement-feature",
    ]


@pytest.fixture
def mock_workflow_output(temp_dir: Path) -> Dict[str, Path]:
    """
    Mock workflow output artifacts.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Dict mapping artifact type to file path
    """
    artifacts = {}

    # Create PRD artifact
    prd_path = temp_dir / "PRD.md"
    prd_path.write_text("# Product Requirements\n\nTest PRD content")
    artifacts["prd"] = prd_path

    # Create architecture artifact
    arch_path = temp_dir / "ARCHITECTURE.md"
    arch_path.write_text("# Architecture\n\nTest architecture content")
    artifacts["architecture"] = arch_path

    # Create story artifact
    story_path = temp_dir / "story-1.1.md"
    story_path.write_text("# Story 1.1\n\nTest story content")
    artifacts["story"] = story_path

    return artifacts
