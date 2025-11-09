"""
System-level performance validation tests.

These tests validate performance targets for the complete git-integrated
hybrid architecture system using pytest-benchmark.

Epic: 27 - Integration & Migration
Story: 27.5 - Performance Validation

Performance Targets:
    1. Complete epic creation workflow: < 1 second
    2. Complete story creation workflow: < 200ms
    3. CLI command performance (create-prd, create-story)
    4. Orchestrator initialization: < 500ms
    5. Database size growth (after 100 operations)
    6. Context loading under load (50 simultaneous requests)
    7. Migration performance (100 files)
    8. Full consistency check (1000 files)
    9. Memory usage tracking
    10. End-to-end workflow (create epic -> 10 stories -> complete)
"""

import asyncio
import sqlite3
import tempfile
import time
from pathlib import Path
import pytest

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.core.git_manager import GitManager
from gao_dev.core.state_coordinator import StateCoordinator
from gao_dev.core.services.git_migration_manager import GitMigrationManager
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyChecker


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create temporary git repository for testing."""
    project_root = tmp_path / "perf_test_project"
    project_root.mkdir()

    # Initialize git
    git_mgr = GitManager(project_path=project_root)
    git_mgr.git_init()

    # Create basic structure
    (project_root / "docs").mkdir()
    (project_root / "docs" / "epics").mkdir()
    (project_root / "docs" / "stories").mkdir()
    (project_root / ".gao-dev").mkdir()

    # Initial commit
    (project_root / "README.md").write_text("# Performance Test Project")
    git_mgr.git_add("README.md")
    git_mgr.git_commit("Initial commit")

    yield project_root


@pytest.fixture
def orchestrator(temp_git_repo):
    """Create orchestrator for performance testing."""
    orch = GAODevOrchestrator.create_default(temp_git_repo)
    yield orch
    orch.close()


# =============================================================================
# BENCHMARK 1: Complete Epic Creation Workflow
# Target: < 1 second
# =============================================================================

def test_perf_epic_creation_workflow(benchmark, temp_git_repo):
    """Benchmark complete epic creation workflow."""

    def create_epic():
        orch = GAODevOrchestrator.create_default(temp_git_repo)
        try:
            epic_num = 1
            epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
            epic_file.write_text(f"# Epic {epic_num}: Performance Test")

            orch.git_state_manager.create_epic(
                epic_num=epic_num,
                title="Performance Test Epic",
                description="Test epic for performance validation",
                file_path=epic_file
            )

            # Verify created
            coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
            epic = coordinator.get_epic(epic_num)
            assert epic is not None

            # Cleanup for next iteration
            epic_file.unlink(missing_ok=True)
            coordinator.db.execute("DELETE FROM epics WHERE epic_num = ?", (epic_num,))
            coordinator.db.commit()
        finally:
            orch.close()

    # Run benchmark
    result = benchmark(create_epic)
    print(f"\nEpic creation time: {result:.4f}s")
    assert result < 1.0, f"Epic creation took {result:.4f}s, target is < 1.0s"


# =============================================================================
# BENCHMARK 2: Complete Story Creation Workflow
# Target: < 200ms
# =============================================================================

def test_perf_story_creation_workflow(benchmark, temp_git_repo):
    """Benchmark complete story creation workflow."""
    # Setup: Create epic first
    orch = GAODevOrchestrator.create_default(temp_git_repo)
    epic_num = 1
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text(f"# Epic {epic_num}")
    orch.git_state_manager.create_epic(epic_num, "Test Epic", "Test", epic_file)
    orch.close()

    def create_story():
        orch = GAODevOrchestrator.create_default(temp_git_repo)
        try:
            story_num = 1
            story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
            story_dir.mkdir(parents=True, exist_ok=True)
            story_file = story_dir / f"story-{epic_num}.{story_num}.md"
            story_file.write_text(f"# Story {epic_num}.{story_num}")

            orch.git_state_manager.create_story(
                epic_num=epic_num,
                story_num=story_num,
                title="Performance Test Story",
                description="Test story",
                file_path=story_file
            )

            # Verify created
            coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
            story = coordinator.get_story(epic_num, story_num)
            assert story is not None

            # Cleanup
            story_file.unlink(missing_ok=True)
            coordinator.db.execute(
                "DELETE FROM stories WHERE epic_num = ? AND story_num = ?",
                (epic_num, story_num)
            )
            coordinator.db.commit()
        finally:
            orch.close()

    # Run benchmark
    result = benchmark(create_story)
    print(f"\nStory creation time: {result:.4f}s")
    assert result < 0.2, f"Story creation took {result:.4f}s, target is < 0.2s"


# =============================================================================
# BENCHMARK 3: CLI Command Performance
# =============================================================================

def test_perf_cli_create_prd_init(benchmark, temp_git_repo):
    """Benchmark create-prd command initialization."""

    def initialize_orchestrator():
        orch = GAODevOrchestrator.create_default(temp_git_repo)
        orch.close()

    # Run benchmark
    result = benchmark(initialize_orchestrator)
    print(f"\nCLI init time: {result:.4f}s")


def test_perf_cli_create_story_operation(benchmark, temp_git_repo):
    """Benchmark create-story command operation."""
    # Setup epic
    orch = GAODevOrchestrator.create_default(temp_git_repo)
    epic_num = 2
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text(f"# Epic {epic_num}")
    orch.git_state_manager.create_epic(epic_num, "Test", "Test", epic_file)
    orch.close()

    def create_story_via_orchestrator():
        orch = GAODevOrchestrator.create_default(temp_git_repo)
        try:
            story_num = 1
            story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
            story_dir.mkdir(parents=True, exist_ok=True)
            story_file = story_dir / f"story-{epic_num}.{story_num}.md"
            story_file.write_text(f"# Story {epic_num}.{story_num}")

            orch.git_state_manager.create_story(
                epic_num, story_num, "Test Story", "Test", story_file
            )

            # Cleanup
            coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
            story_file.unlink(missing_ok=True)
            coordinator.db.execute(
                "DELETE FROM stories WHERE epic_num = ? AND story_num = ?",
                (epic_num, story_num)
            )
            coordinator.db.commit()
        finally:
            orch.close()

    result = benchmark(create_story_via_orchestrator)
    print(f"\nCreate story operation time: {result:.4f}s")


# =============================================================================
# BENCHMARK 4: Orchestrator Initialization
# Target: < 500ms
# =============================================================================

def test_perf_orchestrator_initialization(benchmark, temp_git_repo):
    """Benchmark orchestrator initialization time."""

    def init_orchestrator():
        orch = GAODevOrchestrator.create_default(temp_git_repo)
        # Verify all services initialized
        assert orch.git_state_manager is not None
        assert orch.fast_context_loader is not None
        assert orch.ceremony_orchestrator is not None
        orch.close()

    # Run benchmark
    result = benchmark(init_orchestrator)
    print(f"\nOrchestrator init time: {result:.4f}s")
    assert result < 0.5, f"Orchestrator init took {result:.4f}s, target is < 0.5s"


# =============================================================================
# BENCHMARK 5: Database Size Growth
# =============================================================================

def test_perf_database_size_growth(temp_git_repo):
    """Measure database size growth after 100 operations."""
    db_path = temp_git_repo / ".gao-dev" / "documents.db"

    orch = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Measure initial size
        initial_size = db_path.stat().st_size if db_path.exists() else 0
        print(f"\nInitial DB size: {initial_size} bytes")

        # Perform 100 operations (10 epics x 10 stories)
        for epic_num in range(1, 11):
            epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
            epic_file.write_text(f"# Epic {epic_num}")
            orch.git_state_manager.create_epic(epic_num, f"Epic {epic_num}", "Test", epic_file)

            story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
            story_dir.mkdir(parents=True, exist_ok=True)

            for story_num in range(1, 11):
                story_file = story_dir / f"story-{epic_num}.{story_num}.md"
                story_file.write_text(f"# Story {epic_num}.{story_num}")
                orch.git_state_manager.create_story(
                    epic_num, story_num, f"Story {story_num}", "Test", story_file
                )

        # Measure final size
        final_size = db_path.stat().st_size
        growth = final_size - initial_size
        growth_per_op = growth / 100

        print(f"Final DB size: {final_size} bytes")
        print(f"Growth: {growth} bytes ({growth / 1024:.2f} KB)")
        print(f"Growth per operation: {growth_per_op:.2f} bytes")

        # Reasonable growth: < 1KB per operation
        assert growth_per_op < 1024, f"DB growth per operation ({growth_per_op:.2f} bytes) exceeds 1KB"
    finally:
        orch.close()


# =============================================================================
# BENCHMARK 6: Context Loading Under Load
# =============================================================================

@pytest.mark.asyncio
async def test_perf_context_loading_under_load(temp_git_repo):
    """Benchmark context loading with 50 simultaneous requests."""
    orch = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Setup: Create epic and story
        epic_num = 1
        story_num = 1

        epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
        epic_file.write_text("# Epic 1: Load Test")
        orch.git_state_manager.create_epic(epic_num, "Load Test", "Test", epic_file)

        story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
        story_dir.mkdir(parents=True, exist_ok=True)
        story_file = story_dir / f"story-{epic_num}.{story_num}.md"
        story_file.write_text(f"# Story {epic_num}.{story_num}")
        orch.git_state_manager.create_story(epic_num, story_num, "Load Test", "Test", story_file)

        # Load context 50 times simultaneously
        start_time = time.time()

        async def load_context():
            return await orch.fast_context_loader.load_story_context(epic_num, story_num)

        tasks = [load_context() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time

        # Verify all succeeded
        assert all(r is not None for r in results)

        print(f"\n50 context loads in {elapsed:.4f}s")
        print(f"Average per load: {(elapsed / 50) * 1000:.2f}ms")

        # Target: < 5 seconds for 50 loads (100ms average per load)
        assert elapsed < 5.0, f"50 context loads took {elapsed:.4f}s, target is < 5.0s"
    finally:
        orch.close()


# =============================================================================
# BENCHMARK 7: Migration Performance (100 Files)
# =============================================================================

def test_perf_migration_100_files(temp_git_repo):
    """Benchmark migration performance with 100 files."""
    # Create 100 files (10 epics x 10 stories)
    for epic_num in range(1, 11):
        epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
        epic_file.write_text(f"# Epic {epic_num}")

        story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
        story_dir.mkdir(parents=True, exist_ok=True)

        for story_num in range(1, 11):
            story_file = story_dir / f"story-{epic_num}.{story_num}.md"
            story_file.write_text(f"# Story {epic_num}.{story_num}")

    # Commit files
    git_mgr = GitManager(project_path=temp_git_repo)
    git_mgr.git_add("docs/")
    git_mgr.git_commit("Add 100 files for migration test")

    # Benchmark migration
    db_path = temp_git_repo / ".gao-dev" / "documents.db"
    migration_mgr = GitMigrationManager(db_path=db_path, project_path=temp_git_repo)

    start_time = time.time()
    result = migration_mgr.migrate_to_hybrid_architecture(create_branch=False, auto_merge=False)
    elapsed = time.time() - start_time

    assert result.success
    print(f"\nMigration of 100 files: {elapsed:.4f}s")
    print(f"Epics migrated: {result.epics_count}")
    print(f"Stories migrated: {result.stories_count}")

    # Target: < 10 seconds for 100 files
    assert elapsed < 10.0, f"Migration took {elapsed:.4f}s, target is < 10.0s"


# =============================================================================
# BENCHMARK 8: Full Consistency Check (1000 Files)
# =============================================================================

def test_perf_consistency_check_1000_files(temp_git_repo):
    """Benchmark consistency check performance with 1000 files."""
    # Create 1000 files (100 epics x 10 stories)
    for epic_num in range(1, 101):
        epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
        epic_file.write_text(f"# Epic {epic_num}")

        story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
        story_dir.mkdir(parents=True, exist_ok=True)

        for story_num in range(1, 11):
            story_file = story_dir / f"story-{epic_num}.{story_num}.md"
            story_file.write_text(f"# Story {epic_num}.{story_num}")

    # Commit files
    git_mgr = GitManager(project_path=temp_git_repo)
    git_mgr.git_add("docs/")
    git_mgr.git_commit("Add 1000 files")

    # Migrate
    db_path = temp_git_repo / ".gao-dev" / "documents.db"
    migration_mgr = GitMigrationManager(db_path=db_path, project_path=temp_git_repo)
    result = migration_mgr.migrate_to_hybrid_architecture(create_branch=False, auto_merge=False)
    assert result.success

    # Benchmark consistency check
    checker = GitAwareConsistencyChecker(db_path=db_path, project_path=temp_git_repo)

    start_time = time.time()
    report = checker.check_consistency()
    elapsed = time.time() - start_time

    print(f"\nConsistency check of 1000 files: {elapsed:.4f}s")
    print(f"Issues found: {report.total_issues}")

    # Target: < 5 seconds for 1000 files
    assert elapsed < 5.0, f"Consistency check took {elapsed:.4f}s, target is < 5.0s"


# =============================================================================
# BENCHMARK 9: Memory Usage Tracking
# =============================================================================

def test_perf_memory_usage(temp_git_repo):
    """Track memory usage over 1000 operations."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    orch = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Perform 1000 operations (100 epics x 10 stories)
        for epic_num in range(1, 101):
            epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
            epic_file.write_text(f"# Epic {epic_num}")
            orch.git_state_manager.create_epic(epic_num, f"Epic {epic_num}", "Test", epic_file)

            story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
            story_dir.mkdir(parents=True, exist_ok=True)

            for story_num in range(1, 11):
                story_file = story_dir / f"story-{epic_num}.{story_num}.md"
                story_file.write_text(f"# Story {epic_num}.{story_num}")
                orch.git_state_manager.create_story(
                    epic_num, story_num, f"Story {story_num}", "Test", story_file
                )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        print(f"\nInitial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory growth: {memory_growth:.2f} MB")
        print(f"Memory per operation: {memory_growth / 1000:.4f} MB")

        # Target: < 100MB growth for 1000 operations
        assert memory_growth < 100, f"Memory growth ({memory_growth:.2f} MB) exceeds 100MB"
    finally:
        orch.close()


# =============================================================================
# BENCHMARK 10: End-to-End Workflow (Epic + 10 Stories + Complete)
# =============================================================================

def test_perf_e2e_workflow(temp_git_repo):
    """Benchmark complete workflow: create epic -> 10 stories -> complete all."""
    orch = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        start_time = time.time()

        # Create epic
        epic_num = 1
        epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
        epic_file.write_text(f"# Epic {epic_num}: E2E Test")
        orch.git_state_manager.create_epic(epic_num, "E2E Test", "Test", epic_file)

        # Create 10 stories
        story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
        story_dir.mkdir(parents=True, exist_ok=True)

        for story_num in range(1, 11):
            story_file = story_dir / f"story-{epic_num}.{story_num}.md"
            story_file.write_text(f"# Story {epic_num}.{story_num}")
            orch.git_state_manager.create_story(
                epic_num, story_num, f"Story {story_num}", "Test", story_file
            )

        # Complete all stories
        coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
        for story_num in range(1, 11):
            coordinator.transition_story_state(epic_num, story_num, "ready")
            coordinator.transition_story_state(epic_num, story_num, "in_progress")
            coordinator.transition_story_state(epic_num, story_num, "completed")

        elapsed = time.time() - start_time

        print(f"\nE2E workflow (1 epic + 10 stories + complete): {elapsed:.4f}s")

        # Target: < 5 seconds
        assert elapsed < 5.0, f"E2E workflow took {elapsed:.4f}s, target is < 5.0s"
    finally:
        orch.close()
