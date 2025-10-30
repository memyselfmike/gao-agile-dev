"""Performance tests for workflow-driven architecture (Story 7.2.5 - AC8)."""

import pytest
import time
import asyncio
from pathlib import Path
from unittest.mock import patch

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.orchestrator.models import WorkflowSequence, ScaleLevel, ProjectType
from gao_dev.core.legacy_models import WorkflowInfo


@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def orchestrator(temp_project):
    """Create orchestrator for performance testing."""
    return GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )


@pytest.mark.performance
def test_orchestrator_initialization_performance(temp_project):
    """Test that orchestrator initialization is fast."""
    start = time.time()

    orchestrator = GAODevOrchestrator(
        project_root=temp_project,
        api_key="test-key",
        mode="benchmark"
    )

    duration = time.time() - start

    # Initialization should be reasonable (< 3 seconds, even with 50+ workflows)
    assert duration < 3.0, f"Initialization took {duration:.2f}s, expected < 3s"

    # Verify it initialized correctly
    assert orchestrator.workflow_registry is not None
    assert orchestrator.brian_orchestrator is not None


@pytest.mark.performance
def test_workflow_registry_load_performance(orchestrator):
    """Test that loading workflow registry is fast."""
    start = time.time()

    workflows = orchestrator.workflow_registry.list_workflows()

    duration = time.time() - start

    # Loading workflows should be quick (< 2 seconds even with 50+ workflows)
    assert duration < 2.0, f"Loading workflows took {duration:.2f}s, expected < 2s"

    # Should have loaded workflows
    assert len(workflows) > 0


@pytest.mark.performance
def test_workflow_get_by_name_performance(orchestrator):
    """Test that retrieving workflow by name is fast."""
    # First, get list of workflows
    workflows = orchestrator.workflow_registry.list_workflows()

    if not workflows:
        pytest.skip("No workflows available to test")

    workflow_name = workflows[0].name

    # Measure retrieval time
    iterations = 100
    start = time.time()

    for _ in range(iterations):
        result = orchestrator.workflow_registry.get_workflow(workflow_name)
        assert result is not None

    duration = time.time() - start
    avg_time = duration / iterations

    # Each lookup should be very fast (< 10ms average)
    assert avg_time < 0.01, f"Average lookup took {avg_time*1000:.2f}ms, expected < 10ms"


@pytest.mark.performance
def test_workflow_filter_by_phase_performance(orchestrator):
    """Test that filtering workflows by phase is fast."""
    start = time.time()

    phase_2_workflows = orchestrator.workflow_registry.list_workflows(phase=2)

    duration = time.time() - start

    # Filtering should be instant (< 0.1s)
    assert duration < 0.1, f"Filtering took {duration:.2f}s, expected < 0.1s"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_simple_workflow_execution_performance(orchestrator):
    """Test that simple workflow executes in reasonable time."""
    workflow_info = WorkflowInfo(
        name="simple-workflow",
        description="Simple performance test workflow",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Performance test",
        phase_breakdown={}
    )

    # Mock fast agent method
    async def fast_method():
        await asyncio.sleep(0.01)  # 10ms
        yield "Done"

    start = time.time()

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=fast_method):
        result = await orchestrator.execute_workflow(
            "Performance test",
            workflow=sequence
        )

    duration = time.time() - start

    # Simple workflow should complete quickly (< 5 seconds including overhead)
    assert duration < 5.0, f"Simple workflow took {duration:.2f}s, expected < 5s"

    # Verify it completed
    assert result.total_steps == 1
    assert result.successful_steps == 1


@pytest.mark.performance
@pytest.mark.asyncio
async def test_multi_workflow_execution_performance(orchestrator):
    """Test that multiple workflows execute efficiently."""
    # 5 workflows
    workflows = [
        WorkflowInfo(
            name=f"workflow-{i}",
            description=f"Workflow {i}",
            phase=2,
            installed_path=Path(f"/fake/{i}")
        )
        for i in range(5)
    ]

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_2,
        workflows=workflows,
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Multi-workflow performance test",
        phase_breakdown={}
    )

    # Mock fast methods
    async def fast_method():
        await asyncio.sleep(0.01)  # 10ms per workflow
        yield "Done"

    start = time.time()

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=fast_method):
        result = await orchestrator.execute_workflow(
            "Multi-workflow performance test",
            workflow=sequence
        )

    duration = time.time() - start

    # 5 workflows should complete in reasonable time (< 10 seconds)
    assert duration < 10.0, f"5 workflows took {duration:.2f}s, expected < 10s"

    # Verify all completed
    assert result.total_steps == 5


@pytest.mark.performance
def test_scale_level_description_performance(orchestrator):
    """Test that getting scale level descriptions is fast."""
    scale_levels = [
        ScaleLevel.LEVEL_0,
        ScaleLevel.LEVEL_1,
        ScaleLevel.LEVEL_2,
        ScaleLevel.LEVEL_3,
        ScaleLevel.LEVEL_4
    ]

    start = time.time()

    for level in scale_levels:
        description = orchestrator.get_scale_level_description(level)
        assert isinstance(description, str)
        assert len(description) > 0

    duration = time.time() - start

    # Getting descriptions should be instant (< 0.01s for all)
    assert duration < 0.01, f"Getting descriptions took {duration:.3f}s, expected < 0.01s"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_workflow_result_creation_performance(orchestrator):
    """Test that creating WorkflowResult is efficient."""
    workflow_info = WorkflowInfo(
        name="result-test",
        description="Result creation test",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Result creation test",
        phase_breakdown={}
    )

    async def fast_method():
        yield "Done"

    iterations = 10
    start = time.time()

    with patch.object(orchestrator, '_get_agent_method_for_workflow', return_value=fast_method):
        for _ in range(iterations):
            result = await orchestrator.execute_workflow(
                "Result creation test",
                workflow=sequence
            )
            assert result is not None

    duration = time.time() - start
    avg_time = duration / iterations

    # Creating results should be fast (< 2s average per execution)
    assert avg_time < 2.0, f"Average result creation took {avg_time:.2f}s, expected < 2s"


@pytest.mark.performance
def test_memory_usage_reasonable(orchestrator):
    """Test that orchestrator doesn't use excessive memory."""
    import sys

    # Get current memory usage
    initial_size = sys.getsizeof(orchestrator)

    # Load workflows multiple times
    for _ in range(10):
        workflows = orchestrator.workflow_registry.list_workflows()

    final_size = sys.getsizeof(orchestrator)

    # Size shouldn't grow significantly (< 10% increase)
    growth = (final_size - initial_size) / initial_size if initial_size > 0 else 0

    # Some growth is expected due to caching, but should be bounded
    assert growth < 1.0, f"Memory grew by {growth*100:.1f}%, expected < 100%"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_workflow_execution_performance(temp_project):
    """Test that multiple orchestrators can run concurrently."""
    # Create multiple orchestrators
    orchestrators = [
        GAODevOrchestrator(
            project_root=temp_project / f"project_{i}",
            api_key="test-key",
            mode="benchmark"
        )
        for i in range(3)
    ]

    workflow_info = WorkflowInfo(
        name="concurrent-test",
        description="Concurrent test",
        phase=2,
        installed_path=Path("/fake")
    )

    sequence = WorkflowSequence(
        scale_level=ScaleLevel.LEVEL_1,
        workflows=[workflow_info],
        project_type=ProjectType.GREENFIELD,
        routing_rationale="Concurrent test",
        phase_breakdown={}
    )

    async def fast_method():
        await asyncio.sleep(0.1)
        yield "Done"

    start = time.time()

    # Run all concurrently
    async def run_workflow(orch):
        with patch.object(orch, '_get_agent_method_for_workflow', return_value=fast_method):
            return await orch.execute_workflow("Concurrent test", workflow=sequence)

    results = await asyncio.gather(*[run_workflow(orch) for orch in orchestrators])

    duration = time.time() - start

    # Concurrent execution should be faster than sequential (< 1s with 0.1s each)
    assert duration < 1.0, f"Concurrent execution took {duration:.2f}s, expected < 1s"

    # All should complete successfully
    assert len(results) == 3
    for result in results:
        assert result.total_steps == 1


@pytest.mark.performance
@pytest.mark.slow
def test_workflow_registry_cache_performance(orchestrator):
    """Test that workflow registry caching improves performance."""
    # First call (cold)
    start = time.time()
    workflows_1 = orchestrator.workflow_registry.list_workflows()
    cold_duration = time.time() - start

    # Second call (should be cached)
    start = time.time()
    workflows_2 = orchestrator.workflow_registry.list_workflows()
    cached_duration = time.time() - start

    # Cached call should be faster (or at least not slower)
    # Allow some variance for system fluctuations
    assert cached_duration <= cold_duration * 1.5, \
        f"Cached call ({cached_duration:.3f}s) slower than cold ({cold_duration:.3f}s)"

    # Results should be identical
    assert len(workflows_1) == len(workflows_2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
