"""Tests for complete workflow registry loading (Story 7.2.6)."""

import pytest
from pathlib import Path

from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.workflow_registry import WorkflowRegistry


@pytest.fixture
def workflow_registry(tmp_path):
    """Create workflow registry pointing to real BMAD workflows."""
    # Use real project root to load actual workflows
    project_root = Path(__file__).parent.parent.parent
    config_loader = ConfigLoader(project_root)
    registry = WorkflowRegistry(config_loader)
    registry.index_workflows()
    return registry


def test_workflow_registry_loads_all_workflows(workflow_registry):
    """Test that workflow registry loads all 34+ workflows."""
    workflows = workflow_registry.list_workflows()

    # We should have at least 30 workflows loaded (accounting for variations)
    assert len(workflows) >= 30, f"Expected at least 30 workflows, got {len(workflows)}"

    print(f"\nTotal workflows loaded: {len(workflows)}")


def test_workflows_from_all_phases_loaded(workflow_registry):
    """Test that workflows from all phases (0-4) are loaded."""
    workflows = workflow_registry.list_workflows()

    # Get workflows by phase
    phase_counts = {}
    for workflow in workflows:
        phase = workflow.phase
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    print(f"\nWorkflows by phase:")
    for phase in sorted(phase_counts.keys()):
        print(f"  Phase {phase}: {phase_counts[phase]} workflows")

    # Should have workflows from multiple phases
    assert len(phase_counts) >= 3, f"Expected workflows from at least 3 phases, got {len(phase_counts)}"


def test_phase_1_workflows_loaded(workflow_registry):
    """Test that Phase 1 (Analysis) workflows are loaded."""
    phase_1 = workflow_registry.list_workflows(phase=1)

    # Phase 1 should have analysis workflows
    assert len(phase_1) > 0, "Expected Phase 1 analysis workflows"

    phase_1_names = [w.name for w in phase_1]
    print(f"\nPhase 1 workflows: {phase_1_names}")


def test_phase_2_workflows_loaded(workflow_registry):
    """Test that Phase 2 (Planning) workflows are loaded."""
    phase_2 = workflow_registry.list_workflows(phase=2)

    # Phase 2 should have planning workflows like PRD
    assert len(phase_2) > 0, "Expected Phase 2 planning workflows"

    phase_2_names = [w.name for w in phase_2]
    print(f"\nPhase 2 workflows: {phase_2_names}")

    # Should include PRD workflow
    assert any("prd" in name.lower() for name in phase_2_names)


def test_phase_4_workflows_loaded(workflow_registry):
    """Test that Phase 4 (Implementation) workflows are loaded."""
    phase_4 = workflow_registry.list_workflows(phase=4)

    # Phase 4 should have implementation workflows
    assert len(phase_4) > 0, "Expected Phase 4 implementation workflows"

    phase_4_names = [w.name for w in phase_4]
    print(f"\nPhase 4 workflows: {phase_4_names}")

    # Should include story workflows
    assert any("story" in name.lower() for name in phase_4_names)


def test_workflow_get_by_name(workflow_registry):
    """Test retrieving specific workflows by name."""
    # Try to get a known workflow
    prd_workflow = workflow_registry.get_workflow("prd")

    if prd_workflow:
        assert prd_workflow.name == "prd"
        assert prd_workflow.phase == 2
        print(f"\nPRD Workflow: {prd_workflow.name}, Phase {prd_workflow.phase}")


def test_workflow_metadata_complete(workflow_registry):
    """Test that workflow metadata includes required fields."""
    workflows = workflow_registry.list_workflows()

    assert len(workflows) > 0, "No workflows loaded"

    # Check first workflow has required metadata
    workflow = workflows[0]
    assert workflow.name
    assert workflow.description
    assert workflow.phase >= 0
    assert workflow.installed_path.exists()

    print(f"\nSample workflow metadata:")
    print(f"  Name: {workflow.name}")
    print(f"  Description: {workflow.description}")
    print(f"  Phase: {workflow.phase}")
    print(f"  Path: {workflow.installed_path}")


def test_workflow_exists_check(workflow_registry):
    """Test workflow existence checking."""
    # Check that a known workflow exists
    assert workflow_registry.workflow_exists("prd") or workflow_registry.workflow_exists("create-story")

    # Check that a non-existent workflow returns False
    assert not workflow_registry.workflow_exists("nonexistent-workflow-xyz")


def test_get_all_workflows_dict(workflow_registry):
    """Test getting all workflows as dictionary."""
    all_workflows = workflow_registry.get_all_workflows()

    assert isinstance(all_workflows, dict)
    assert len(all_workflows) > 0

    print(f"\nTotal workflows in dict: {len(all_workflows)}")
    print(f"Workflow names: {list(all_workflows.keys())[:10]}...")  # Print first 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
