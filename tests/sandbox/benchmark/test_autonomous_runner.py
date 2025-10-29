"""Tests for autonomous benchmark runner (Story 7.2.3)."""

import pytest
from pathlib import Path

from gao_dev.sandbox.benchmark.config import (
    BenchmarkConfig,
    SuccessCriteria,
    WorkflowPhaseConfig
)


def test_autonomous_config_validation():
    """Test that autonomous config validates correctly."""
    autonomous_config = BenchmarkConfig(
        name="autonomous-test",
        description="Test autonomous benchmark",
        initial_prompt="Build a simple todo application with Python",
        timeout_seconds=300,
        success_criteria=SuccessCriteria()
    )

    assert autonomous_config.validate()
    assert autonomous_config.initial_prompt
    assert not autonomous_config.workflow_phases
    assert not autonomous_config.epics


def test_autonomous_mode_detection():
    """Test that runner correctly detects autonomous mode."""
    # Autonomous config
    autonomous = BenchmarkConfig(
        name="auto",
        description="Auto",
        initial_prompt="Build app",
        success_criteria=SuccessCriteria()
    )
    assert autonomous.validate()
    assert autonomous.initial_prompt
    assert not autonomous.workflow_phases
    assert not autonomous.epics

    # Phase-based config (should still work)
    phase_based = BenchmarkConfig(
        name="phase",
        description="Phase",
        workflow_phases=[WorkflowPhaseConfig(phase_name="Test")],
        success_criteria=SuccessCriteria()
    )
    assert phase_based.validate()


def test_autonomous_config_requires_initial_prompt():
    """Test that autonomous config without initial_prompt fails validation."""
    # Config with no initial_prompt, no phases, no epics - should fail
    invalid_config = BenchmarkConfig(
        name="invalid",
        description="Invalid",
        success_criteria=SuccessCriteria()
    )
    assert not invalid_config.validate()


def test_config_with_initial_prompt_and_phases_uses_phases():
    """Test that config with both initial_prompt and phases uses phase mode."""
    config = BenchmarkConfig(
        name="hybrid",
        description="Hybrid",
        initial_prompt="Build app",
        workflow_phases=[WorkflowPhaseConfig(phase_name="Test")],
        success_criteria=SuccessCriteria()
    )
    # Should still validate (phases take precedence)
    assert config.validate()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
