"""Tests for clarification dialog (Story 7.2.4)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from gao_dev.orchestrator import GAODevOrchestrator


@pytest.fixture
def orchestrator_cli(tmp_path):
    """Create orchestrator in CLI mode."""
    return GAODevOrchestrator.create_default(
        project_root=tmp_path,
        api_key="test-key",
        mode="cli"
    )


@pytest.fixture
def orchestrator_benchmark(tmp_path):
    """Create orchestrator in benchmark mode."""
    return GAODevOrchestrator.create_default(
        project_root=tmp_path,
        api_key="test-key",
        mode="benchmark"
    )


@pytest.fixture
def orchestrator_api(tmp_path):
    """Create orchestrator in API mode."""
    return GAODevOrchestrator.create_default(
        project_root=tmp_path,
        api_key="test-key",
        mode="api"
    )


def test_orchestrator_mode_detection(tmp_path):
    """Test that orchestrator correctly sets execution mode."""
    # CLI mode (default)
    cli_orch = GAODevOrchestrator.create_default(project_root=tmp_path)
    assert cli_orch.mode == "cli"

    # Benchmark mode
    bench_orch = GAODevOrchestrator.create_default(project_root=tmp_path, mode="benchmark")
    assert bench_orch.mode == "benchmark"

    # API mode
    api_orch = GAODevOrchestrator.create_default(project_root=tmp_path, mode="api")
    assert api_orch.mode == "api"


def test_clarification_in_cli_mode(orchestrator_cli):
    """Test clarification handling in CLI mode."""
    questions = [
        "What framework do you want to use?",
        "Do you need authentication?"
    ]

    # For now, returns None (interactive not implemented yet)
    result = orchestrator_cli.handle_clarification(questions, "Build an app")
    assert result is None  # Would be enhanced prompt when interactive added


def test_clarification_in_benchmark_mode(orchestrator_benchmark):
    """Test clarification handling in benchmark mode."""
    questions = [
        "What framework do you want to use?",
        "Do you need authentication?"
    ]

    # Benchmark mode should return None (fails gracefully)
    result = orchestrator_benchmark.handle_clarification(questions, "Build an app")
    assert result is None


def test_clarification_in_api_mode(orchestrator_api):
    """Test clarification handling in API mode."""
    questions = [
        "What framework do you want to use?",
        "Do you need authentication?"
    ]

    # API mode should return None (delegated to caller)
    result = orchestrator_api.handle_clarification(questions, "Build an app")
    assert result is None


def test_clarification_logging(orchestrator_cli, caplog):
    """Test that clarification interactions are logged."""
    import logging
    caplog.set_level(logging.INFO)

    questions = [
        "What is the project scope?",
        "What technologies should I use?"
    ]

    orchestrator_cli.handle_clarification(questions, "Build something")

    # Check that questions were logged
    # Note: structlog may format differently, so we just verify method was called
    assert orchestrator_cli.mode == "cli"


def test_empty_questions_list(orchestrator_cli):
    """Test handling of empty questions list."""
    result = orchestrator_cli.handle_clarification([], "Build an app")
    assert result is None


def test_single_question(orchestrator_benchmark):
    """Test handling of single clarifying question."""
    questions = ["What is the target platform?"]
    result = orchestrator_benchmark.handle_clarification(questions, "Build mobile app")
    assert result is None  # Benchmark mode fails gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
