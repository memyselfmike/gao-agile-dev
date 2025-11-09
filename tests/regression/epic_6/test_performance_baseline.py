"""
Performance Baseline Tests for Epic 6.

CRITICAL: These tests establish performance baselines BEFORE Epic 6
refactoring. After refactoring, performance must remain within 5%
tolerance to ensure no degradation.

Test Coverage:
- Orchestrator initialization time
- Sandbox manager initialization time
- Project creation time
- Workflow execution time (where possible)
- Memory usage

Usage:
    # Capture baseline before Epic 6:
    pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture

    # Compare after each story:
    pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare

    # Just validate tests pass:
    pytest tests/regression/epic_6/test_performance_baseline.py
"""

import pytest
import time
import tracemalloc
from pathlib import Path

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.sandbox.manager import SandboxManager


# =============================================================================
# A. Initialization Performance Tests
# =============================================================================

class TestInitializationPerformance:
    """Test initialization performance baselines."""

    def test_orchestrator_initialization_time(
        self,
        orchestrator_test_project: Path,
        capture_performance_metric
    ):
        """
        Baseline: Orchestrator initialization time.

        Captures how long it takes to initialize GAODevOrchestrator.
        After refactoring, should remain within 5% tolerance.
        """
        # Measure initialization time
        start_time = time.time()

        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "orchestrator_initialization",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert orchestrator is not None
        assert duration < 10.0  # Should never take more than 10 seconds

    def test_sandbox_initialization_time(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox manager initialization time.

        Captures how long it takes to initialize SandboxManager.
        After refactoring, should remain within 5% tolerance.
        """
        # Measure initialization time
        start_time = time.time()

        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "sandbox_initialization",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert sandbox is not None
        assert duration < 5.0  # Should be very fast


# =============================================================================
# B. Operation Performance Tests
# =============================================================================

class TestOperationPerformance:
    """Test operation performance baselines."""

    def test_sandbox_project_creation_time(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox project creation time.

        Captures how long it takes to create a sandbox project.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Sandbox manager
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Measure project creation time
        start_time = time.time()

        sandbox.create_project(
            name="performance-test",
            description="Performance test project",
            boilerplate_url=None
        )

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "sandbox_project_creation",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert sandbox.project_exists("performance-test")
        assert duration < 5.0  # Should be fast

    def test_sandbox_project_creation_with_boilerplate_time(
        self,
        sandbox_test_root: Path,
        sample_boilerplate: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox project creation with boilerplate time.

        Captures how long it takes to create project with boilerplate.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Sandbox manager
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Measure project creation time with boilerplate
        start_time = time.time()

        sandbox.create_project(
            name="boilerplate-test",
            description="Boilerplate test project",
            boilerplate_url=sample_boilerplate
        )

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "sandbox_project_creation_with_boilerplate",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert sandbox.project_exists("boilerplate-test")
        assert duration < 10.0  # Boilerplate copying takes longer

    def test_sandbox_list_projects_time(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox list projects time.

        Captures how long it takes to list sandbox projects.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Sandbox manager with multiple projects
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Create 10 projects
        for i in range(10):
            sandbox.create_project(name=f"project-{i}", description=f"Project {i}")

        # Measure list time
        start_time = time.time()

        projects = sandbox.list_projects()

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "sandbox_list_projects",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert len(projects) == 10
        assert duration < 2.0  # Should be fast

    def test_sandbox_get_project_time(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox get project time.

        Captures how long it takes to retrieve a project.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Sandbox manager with project
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)
        sandbox.create_project(name="test-project", description="Test")

        # Measure get project time
        start_time = time.time()

        project = sandbox.get_project("test-project")

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "sandbox_get_project",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert project.name == "test-project"
        assert duration < 1.0  # Should be very fast


# =============================================================================
# C. Memory Usage Tests
# =============================================================================

class TestMemoryUsage:
    """Test memory usage baselines."""

    def test_orchestrator_memory_usage(
        self,
        orchestrator_test_project: Path,
        capture_performance_metric
    ):
        """
        Baseline: Orchestrator memory usage.

        Captures memory usage during orchestrator initialization.
        After refactoring, should remain within 10% tolerance.
        """
        # Start memory tracking
        tracemalloc.start()

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=orchestrator_test_project,
            mode="cli"
        )

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        peak_mb = peak / 1024 / 1024

        # Record baseline
        capture_performance_metric(
            "orchestrator_memory_peak",
            peak_mb,
            "MB",
            tolerance=0.10  # 10% tolerance (memory is more variable)
        )

        # Sanity check
        assert orchestrator is not None
        assert peak_mb < 500  # Should not use more than 500MB

    def test_sandbox_memory_usage(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Sandbox manager memory usage.

        Captures memory usage during sandbox operations.
        After refactoring, should remain within 10% tolerance.
        """
        # Start memory tracking
        tracemalloc.start()

        # Create sandbox and multiple projects
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)
        for i in range(5):
            sandbox.create_project(name=f"project-{i}", description=f"Project {i}")

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        peak_mb = peak / 1024 / 1024

        # Record baseline
        capture_performance_metric(
            "sandbox_memory_peak",
            peak_mb,
            "MB",
            tolerance=0.10  # 10% tolerance
        )

        # Sanity check
        assert len(sandbox.list_projects()) == 5
        assert peak_mb < 200  # Should not use more than 200MB


# =============================================================================
# D. Workflow Registry Performance Tests
# =============================================================================

class TestWorkflowRegistryPerformance:
    """Test workflow registry performance baselines."""

    def test_workflow_registry_indexing_time(
        self,
        orchestrator_test_project: Path,
        capture_performance_metric
    ):
        """
        Baseline: Workflow registry indexing time.

        Captures how long it takes to index workflows.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Config loader
        from gao_dev.core.config_loader import ConfigLoader
        from gao_dev.core.workflow_registry import WorkflowRegistry

        config_loader = ConfigLoader(orchestrator_test_project)

        # Measure indexing time
        start_time = time.time()

        registry = WorkflowRegistry(config_loader)
        registry.index_workflows()

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "workflow_registry_indexing",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert registry is not None
        assert duration < 5.0  # Should be fast

    def test_workflow_registry_list_time(
        self,
        orchestrator_test_project: Path,
        capture_performance_metric
    ):
        """
        Baseline: Workflow registry list time.

        Captures how long it takes to list workflows.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Workflow registry
        from gao_dev.core.config_loader import ConfigLoader
        from gao_dev.core.workflow_registry import WorkflowRegistry

        config_loader = ConfigLoader(orchestrator_test_project)
        registry = WorkflowRegistry(config_loader)
        registry.index_workflows()

        # Measure list time
        start_time = time.time()

        workflows = registry.list_workflows()

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "workflow_registry_list",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        assert isinstance(workflows, list)
        assert duration < 1.0  # Should be very fast


# =============================================================================
# E. Stress Tests (Optional)
# =============================================================================

@pytest.mark.slow
class TestStressPerformance:
    """Stress tests for performance baselines (marked slow)."""

    def test_many_projects_creation_time(
        self,
        sandbox_test_root: Path,
        capture_performance_metric
    ):
        """
        Baseline: Time to create many projects.

        Captures how long it takes to create 50 projects.
        After refactoring, should remain within 5% tolerance.
        """
        # Given: Sandbox manager
        sandbox = SandboxManager(sandbox_root=sandbox_test_root)

        # Measure time to create 50 projects
        start_time = time.time()

        for i in range(50):
            sandbox.create_project(name=f"stress-project-{i}", description=f"Project {i}")

        end_time = time.time()
        duration = end_time - start_time

        # Record baseline
        capture_performance_metric(
            "many_projects_creation",
            duration,
            "seconds",
            tolerance=0.05  # 5% tolerance
        )

        # Sanity check
        projects = sandbox.list_projects()
        assert len(projects) == 50
        assert duration < 60.0  # Should complete within 1 minute


# =============================================================================
# Summary
# =============================================================================

"""
These performance tests establish baselines BEFORE Epic 6 refactoring.

Usage:
1. BEFORE Epic 6: Run with --baseline-mode=capture
   pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=capture

2. AFTER each story: Run with --baseline-mode=compare
   pytest tests/regression/epic_6/test_performance_baseline.py --baseline-mode=compare

3. Regular testing: Just run normally
   pytest tests/regression/epic_6/test_performance_baseline.py

Success Criteria:
- All metrics within 5% of baseline (except memory: 10%)
- No test exceeds sanity check thresholds
- Refactored code performs as well as or better than original

If performance regression detected:
1. STOP immediately
2. Profile the code to find bottleneck
3. Optimize or adjust architecture
4. Re-run performance tests
5. Only proceed when performance acceptable
"""
