"""
Example tests demonstrating test infrastructure usage.

This module shows how to use mocks, fixtures, and testing utilities.
"""

import pytest
from pathlib import Path

from gao_dev.core.models.story import StoryIdentifier, Story, StoryStatus
from gao_dev.core.models.workflow import WorkflowContext

from tests.mocks import (
    MockAgent,
    MockWorkflow,
    MockRepository,
    MockEventBus,
    MockEventHandler,
)


# =============================================================================
# Mock Agent Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_agent(mock_agent, sample_agent_context):
    """Test that mock agent works correctly."""
    # Execute task
    messages = []
    async for msg in mock_agent.execute_task("Test task", sample_agent_context):
        messages.append(msg)

    # Verify
    assert len(messages) > 0
    assert "Test task" in mock_agent.tasks_executed


@pytest.mark.unit
def test_mock_agent_capabilities(mock_agent):
    """Test mock agent capabilities."""
    capabilities = mock_agent.get_capabilities()
    assert isinstance(capabilities, list)


# =============================================================================
# Mock Workflow Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_workflow(mock_workflow, sample_workflow_context):
    """Test that mock workflow executes correctly."""
    result = await mock_workflow.execute(sample_workflow_context)

    assert result.success is True
    assert len(result.artifacts) > 0
    assert len(mock_workflow.executions) == 1


@pytest.mark.unit
def test_mock_workflow_registry(mock_workflow_registry, mock_workflow):
    """Test mock workflow registry."""
    # Register workflow
    mock_workflow_registry.register_workflow(mock_workflow)

    # Verify
    assert mock_workflow_registry.workflow_exists(mock_workflow.identifier.name)
    assert mock_workflow_registry.get_workflow_count() == 1

    # Retrieve
    retrieved = mock_workflow_registry.get_workflow(mock_workflow.identifier.name)
    assert retrieved is mock_workflow


# =============================================================================
# Mock Repository Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_repository(mock_repository, sample_story):
    """Test mock repository CRUD operations."""
    # Save
    await mock_repository.save(sample_story)
    assert mock_repository.count() == 1

    # Find by ID
    found = await mock_repository.find_by_id(str(sample_story.id))
    assert found is sample_story

    # Find all
    all_stories = await mock_repository.find_all()
    assert len(all_stories) == 1

    # Delete
    await mock_repository.delete(str(sample_story.id))
    assert mock_repository.count() == 0


# =============================================================================
# Mock Event Bus Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_event_bus(mock_event_bus):
    """Test mock event bus pub/sub."""
    # Create handler
    handler = MockEventHandler()

    # Subscribe
    event_type = str
    mock_event_bus.subscribe(event_type, handler)

    # Publish
    await mock_event_bus.publish("Test event")

    # Verify
    assert len(handler.events_handled) == 1
    assert handler.events_handled[0] == "Test event"

    # Check history
    history = mock_event_bus.get_event_history()
    assert len(history) == 1


# =============================================================================
# Fixture Tests
# =============================================================================

@pytest.mark.unit
def test_temp_dir_fixture(temp_dir):
    """Test that temp_dir fixture works."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()

    # Can write to it
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()


@pytest.mark.unit
def test_sample_project_fixture(sample_project_dir):
    """Test that sample_project_dir fixture creates structure."""
    assert sample_project_dir.exists()
    assert (sample_project_dir / "docs").exists()
    assert (sample_project_dir / "docs" / "PRD.md").exists()
    assert (sample_project_dir / "src").exists()


@pytest.mark.unit
def test_sample_story_identifier_fixture(sample_story_identifier):
    """Test sample story identifier fixture."""
    assert sample_story_identifier.epic == 1
    assert sample_story_identifier.story == 1
    assert sample_story_identifier.to_string() == "1.1"


@pytest.mark.unit
def test_sample_story_fixture(sample_story):
    """Test sample story fixture."""
    assert sample_story.id.epic == 1
    assert sample_story.title == "Sample Story"
    assert sample_story.status == StoryStatus.BACKLOG


# =============================================================================
# Integration Example
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_with_event_bus(
    mock_workflow,
    mock_event_bus,
    sample_workflow_context
):
    """Integration test: workflow execution with events."""
    # Create handler
    handler = MockEventHandler()

    # Subscribe to workflow completion events
    mock_event_bus.subscribe(str, handler)

    # Execute workflow
    result = await mock_workflow.execute(sample_workflow_context)

    # Publish completion event
    await mock_event_bus.publish(f"Workflow {result.workflow_name} completed")

    # Verify event was handled
    assert len(handler.events_handled) == 1
