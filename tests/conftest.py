"""
Pytest configuration and fixtures for GAO-Dev tests.

This module provides reusable fixtures for testing.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from gao_dev.core.models.project import ProjectPath, Project, ProjectStatus
from gao_dev.core.models.story import StoryIdentifier, Story, StoryStatus
from gao_dev.core.models.workflow import (
    WorkflowIdentifier,
    WorkflowContext,
    ComplexityLevel,
)
from gao_dev.core.models.agent import AgentContext

from tests.mocks import (
    MockAgent,
    MockAgentFactory,
    MockWorkflow,
    MockWorkflowRegistry,
    MockRepository,
    MockEventBus,
    MockMethodology,
)


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Temporary directory fixture.

    Creates a temporary directory for test use and cleans it up after.

    Yields:
        Path: Temporary directory path
    """
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_project_dir(temp_dir: Path) -> Path:
    """
    Sample project directory structure.

    Creates a realistic project directory structure for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Root of sample project
    """
    # Create directory structure
    (temp_dir / "docs").mkdir()
    (temp_dir / "docs" / "stories").mkdir()
    (temp_dir / "docs" / "stories" / "epic-1").mkdir()
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()

    # Create sample files
    (temp_dir / "docs" / "PRD.md").write_text("# Product Requirements")
    (temp_dir / "docs" / "ARCHITECTURE.md").write_text("# Architecture")

    return temp_dir


# =============================================================================
# Value Object Fixtures
# =============================================================================

@pytest.fixture
def sample_story_identifier() -> StoryIdentifier:
    """Sample story identifier (1.1)."""
    return StoryIdentifier(epic=1, story=1)


@pytest.fixture
def sample_story(sample_story_identifier: StoryIdentifier, temp_dir: Path) -> Story:
    """Sample story object."""
    return Story(
        id=sample_story_identifier,
        title="Sample Story",
        status=StoryStatus.BACKLOG,
        file_path=temp_dir / "story-1.1.md",
        story_points=3
    )


@pytest.fixture
def sample_project_path(sample_project_dir: Path) -> ProjectPath:
    """Sample project path."""
    return ProjectPath(root=sample_project_dir)


@pytest.fixture
def sample_project(sample_project_path: ProjectPath) -> Project:
    """Sample project object."""
    return Project(
        id="test-001",
        name="Test Project",
        path=sample_project_path,
        status=ProjectStatus.ACTIVE,
        methodology="BMAD"
    )


@pytest.fixture
def sample_workflow_identifier() -> WorkflowIdentifier:
    """Sample workflow identifier."""
    return WorkflowIdentifier("test-workflow", phase=4)


@pytest.fixture
def sample_workflow_context(sample_project_dir: Path) -> WorkflowContext:
    """Sample workflow context."""
    return WorkflowContext(project_root=sample_project_dir)


@pytest.fixture
def sample_agent_context(sample_project_dir: Path) -> AgentContext:
    """Sample agent context."""
    return AgentContext(
        project_root=sample_project_dir,
        available_tools=["Read", "Write", "Edit", "Bash"]
    )


@pytest.fixture
def sample_complexity_level() -> ComplexityLevel:
    """Sample complexity level (level 3)."""
    return ComplexityLevel.from_scale_level(3)


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_agent() -> MockAgent:
    """Mock agent instance."""
    return MockAgent(name="TestAgent", role="Tester")


@pytest.fixture
def mock_agent_factory() -> MockAgentFactory:
    """Mock agent factory instance."""
    factory = MockAgentFactory()
    factory.register_agent_class("test", MockAgent)
    return factory


@pytest.fixture
def mock_workflow(sample_workflow_identifier: WorkflowIdentifier) -> MockWorkflow:
    """Mock workflow instance."""
    return MockWorkflow(
        identifier=sample_workflow_identifier,
        artifacts=["output.md"]
    )


@pytest.fixture
def mock_workflow_registry() -> MockWorkflowRegistry:
    """Mock workflow registry instance."""
    return MockWorkflowRegistry()


@pytest.fixture
def mock_repository() -> MockRepository:
    """Mock repository instance."""
    return MockRepository()


@pytest.fixture
def mock_event_bus() -> MockEventBus:
    """Mock event bus instance."""
    return MockEventBus()


@pytest.fixture
def mock_methodology() -> MockMethodology:
    """Mock methodology instance."""
    return MockMethodology()


# =============================================================================
# Async Utilities
# =============================================================================

@pytest.fixture
def event_loop_policy():
    """Set event loop policy for Windows."""
    import asyncio
    import sys

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
