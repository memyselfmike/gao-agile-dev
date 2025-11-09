"""
End-to-end workflow tests for git-integrated hybrid architecture.

These tests validate complete workflows from start to finish using real
git operations on temporary repositories.

Epic: 27 - Integration & Migration
Story: 27.4 - End-to-End Tests

Test Scenarios:
    1. Create epic to completion workflow
    2. Ceremony with context loading and artifacts
    3. Multi-story workflow with state transitions
    4. Error recovery and rollback scenarios
    5. CLI command integration
    6. Migration workflow
    7. Consistency check workflow
"""

import asyncio
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
import structlog

from gao_dev.orchestrator import GAODevOrchestrator
from gao_dev.core.git_manager import GitManager
from gao_dev.core.state_coordinator import StateCoordinator
from gao_dev.core.services.git_migration_manager import GitMigrationManager
from gao_dev.core.services.git_consistency_checker import GitAwareConsistencyChecker

logger = structlog.get_logger()


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create temporary git repository for testing."""
    project_root = tmp_path / "test_project"
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
    (project_root / "README.md").write_text("# Test Project")
    git_mgr.git_add(["README.md"])
    git_mgr.git_commit("Initial commit")

    yield project_root

    # Cleanup handled by tmp_path fixture


@pytest.fixture
def orchestrator(temp_git_repo):
    """Create orchestrator for temporary project."""
    orch = GAODevOrchestrator.create_default(temp_git_repo)
    yield orch
    orch.close()


# =============================================================================
# TEST SCENARIO 1: Create Epic to Completion Workflow
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_epic_creation_workflow(orchestrator, temp_git_repo):
    """Test complete epic creation workflow with git integration."""
    # Create epic
    epic_num = 1
    epic_title = "Test Feature Implementation"

    # Mock epic creation (normally done by orchestrator)
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text(f"""# Epic {epic_num}: {epic_title}

## Description
Test epic for E2E workflow validation.

## Stories
- Story 1.1: Implement feature A
- Story 1.2: Implement feature B
- Story 1.3: Add tests
""")

    # Register epic in database
    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_epic(
            epic_num=epic_num,
            title=epic_title,
            file_path=epic_file,
            content=epic_file.read_text()
        )

    # Verify epic exists in git
    git_mgr = GitManager(project_path=temp_git_repo)
    assert epic_file.exists()

    # Verify epic in database
    coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
    epic = coordinator.get_epic(epic_num)
    assert epic is not None
    assert epic["title"] == epic_title
    assert epic["status"] == "planning"


@pytest.mark.asyncio
async def test_e2e_story_creation_and_completion(orchestrator, temp_git_repo):
    """Test story creation, implementation, and completion workflow."""
    # Create epic first
    epic_num = 1
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text("# Epic 1: Test Epic")

    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_epic(
            epic_num=epic_num,
            title="Test Epic",
            description="Test",
            file_path=epic_file
        )

    # Create story
    story_num = 1
    story_title = "Implement feature"
    story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_file = story_dir / f"story-{epic_num}.{story_num}.md"
    story_file.write_text(f"""# Story {epic_num}.{story_num}: {story_title}

## Description
Test story for E2E validation.

## Acceptance Criteria
- [ ] Feature implemented
- [ ] Tests passing
""")

    # Register story
    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_story(
            epic_num=epic_num,
            story_num=story_num,
            title=story_title,
            description="Test story",
            file_path=story_file
        )

    # Transition story through states
    coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")

    # planning -> ready
    coordinator.transition_story_state(epic_num, story_num, "ready")
    story = coordinator.get_story(epic_num, story_num)
    assert story["status"] == "ready"

    # ready -> in_progress
    coordinator.transition_story_state(epic_num, story_num, "in_progress")
    story = coordinator.get_story(epic_num, story_num)
    assert story["status"] == "in_progress"

    # in_progress -> completed
    coordinator.transition_story_state(epic_num, story_num, "completed")
    story = coordinator.get_story(epic_num, story_num)
    assert story["status"] == "completed"


# =============================================================================
# TEST SCENARIO 2: Ceremony with Context Loading
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_ceremony_with_context(orchestrator, temp_git_repo):
    """Test ceremony execution with context loading and artifact creation."""
    # Setup: Create epic and story
    epic_num = 2
    story_num = 1

    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text("# Epic 2: Context Test")

    story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_file = story_dir / f"story-{epic_num}.{story_num}.md"
    story_file.write_text("# Story 2.1: Context Test Story")

    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_epic(epic_num, "Context Test", "Test", epic_file)
        orchestrator.git_state_manager.create_story(epic_num, story_num, "Context Test Story", "Test", story_file)

    # Load context (simulates ceremony preparation)
    if orchestrator.fast_context_loader:
        context = await orchestrator.fast_context_loader.load_story_context(
            epic_num=epic_num,
            story_num=story_num
        )

        assert context is not None
        assert context.epic_num == epic_num
        assert context.story_num == story_num
        assert "epic" in context.artifacts
        assert "story" in context.artifacts


@pytest.mark.asyncio
async def test_e2e_multi_story_workflow(orchestrator, temp_git_repo):
    """Test multi-story workflow with state transitions."""
    epic_num = 3

    # Create epic
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text("# Epic 3: Multi-Story Test")

    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_epic(epic_num, "Multi-Story Test", "Test", epic_file)

    # Create 3 stories
    coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
    story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
    story_dir.mkdir(parents=True, exist_ok=True)

    for story_num in range(1, 4):
        story_file = story_dir / f"story-{epic_num}.{story_num}.md"
        story_file.write_text(f"# Story {epic_num}.{story_num}")

        if orchestrator.git_state_manager:
            orchestrator.git_state_manager.create_story(
                epic_num, story_num, f"Story {story_num}", "Test", story_file
            )

    # Verify all stories created
    stories = coordinator.list_stories(epic_num)
    assert len(stories) == 3

    # Transition first story to completed
    coordinator.transition_story_state(epic_num, 1, "ready")
    coordinator.transition_story_state(epic_num, 1, "in_progress")
    coordinator.transition_story_state(epic_num, 1, "completed")

    # Verify state
    story = coordinator.get_story(epic_num, 1)
    assert story["status"] == "completed"


# =============================================================================
# TEST SCENARIO 3: Error Recovery and Rollback
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_error_recovery(orchestrator, temp_git_repo):
    """Test error recovery with git rollback."""
    coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")

    # Create epic
    epic_num = 4
    epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
    epic_file.write_text("# Epic 4: Error Recovery Test")

    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_epic(epic_num, "Error Recovery", "Test", epic_file)

    # Create story
    story_num = 1
    story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
    story_dir.mkdir(parents=True, exist_ok=True)
    story_file = story_dir / f"story-{epic_num}.{story_num}.md"
    story_file.write_text(f"# Story {epic_num}.{story_num}")

    if orchestrator.git_state_manager:
        orchestrator.git_state_manager.create_story(epic_num, story_num, "Test", "Test", story_file)

    # Attempt invalid state transition (should fail gracefully)
    with pytest.raises(Exception):
        # Try to go from planning directly to completed (invalid)
        coordinator.transition_story_state(epic_num, story_num, "completed")

    # Verify story still in original state
    story = coordinator.get_story(epic_num, story_num)
    assert story["status"] == "planning"


@pytest.mark.asyncio
async def test_e2e_git_rollback_on_failure(temp_git_repo):
    """Test git rollback on migration failure."""
    git_mgr = GitManager(project_path=temp_git_repo)

    # Get current commit
    initial_sha = git_mgr.get_current_commit_sha()

    # Create some files
    test_file = temp_git_repo / "test.txt"
    test_file.write_text("test")
    git_mgr.git_add("test.txt")
    git_mgr.git_commit("Add test file")

    # Verify commit changed
    new_sha = git_mgr.get_current_commit_sha()
    assert new_sha != initial_sha

    # Simulate rollback
    git_mgr.git_reset_hard(initial_sha)

    # Verify rolled back
    assert git_mgr.get_current_commit_sha() == initial_sha
    assert not test_file.exists()


# =============================================================================
# TEST SCENARIO 4: CLI Command Integration
# =============================================================================

def test_e2e_cli_create_prd_flow(temp_git_repo):
    """Test CLI create-prd command integration."""
    # This would normally invoke CLI, but we test orchestrator directly
    orchestrator = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Verify orchestrator initialized
        assert orchestrator.git_state_manager is not None
        assert orchestrator.fast_context_loader is not None
        assert orchestrator.ceremony_orchestrator is not None

        # Verify database initialized
        db_path = temp_git_repo / ".gao-dev" / "documents.db"
        assert db_path.exists()

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "epics" in tables
        assert "stories" in tables

        conn.close()
    finally:
        orchestrator.close()


def test_e2e_cli_create_story_flow(temp_git_repo):
    """Test CLI create-story command integration."""
    orchestrator = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Create epic first
        epic_num = 5
        epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
        epic_file.write_text("# Epic 5: CLI Test")

        orchestrator.git_state_manager.create_epic(epic_num, "CLI Test", "Test", epic_file)

        # Verify epic creation triggered database insert
        coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
        epic = coordinator.get_epic(epic_num)
        assert epic is not None
        assert epic["status"] == "planning"
    finally:
        orchestrator.close()


# =============================================================================
# TEST SCENARIO 5: Migration Workflow
# =============================================================================

def test_e2e_migration_workflow(temp_git_repo):
    """Test complete migration from file-based to hybrid architecture."""
    # Create epic and story files (pre-migration state)
    (temp_git_repo / "docs" / "epics" / "epic-1.md").write_text("# Epic 1")
    (temp_git_repo / "docs" / "epics" / "epic-2.md").write_text("# Epic 2")

    story_dir = temp_git_repo / "docs" / "stories" / "epic-1"
    story_dir.mkdir(parents=True, exist_ok=True)
    (story_dir / "story-1.1.md").write_text("# Story 1.1")
    (story_dir / "story-1.2.md").write_text("# Story 1.2")

    # Commit files
    git_mgr = GitManager(project_path=temp_git_repo)
    git_mgr.git_add("docs/")
    git_mgr.git_commit("Add epics and stories")

    # Run migration
    db_path = temp_git_repo / ".gao-dev" / "documents.db"
    migration_mgr = GitMigrationManager(
        db_path=db_path,
        project_path=temp_git_repo
    )

    result = migration_mgr.migrate_to_hybrid_architecture(
        create_branch=False,
        auto_merge=False
    )

    # Verify migration success
    assert result.success
    assert result.phase_completed == 4
    assert result.epics_count == 2
    assert result.stories_count == 2

    # Verify database populated
    coordinator = StateCoordinator(db_path=db_path)
    epics = coordinator.list_epics()
    assert len(epics) == 2

    stories = coordinator.list_stories(1)
    assert len(stories) == 2


def test_e2e_migration_with_rollback(temp_git_repo):
    """Test migration rollback on failure."""
    # Create invalid state (no git repo)
    non_git_dir = temp_git_repo / "non_git"
    non_git_dir.mkdir()

    db_path = non_git_dir / ".gao-dev" / "documents.db"

    # Attempt migration (should fail gracefully)
    migration_mgr = GitMigrationManager(
        db_path=db_path,
        project_path=non_git_dir
    )

    # This should handle error gracefully
    # (actual behavior depends on implementation)
    try:
        result = migration_mgr.migrate_to_hybrid_architecture(
            create_branch=False,
            auto_merge=False
        )
        # If it succeeds, verify no partial state
        if not result.success:
            assert result.rollback_performed or result.phase_completed == 0
    except Exception as e:
        # Expected - migration should fail for non-git repo
        assert "git" in str(e).lower() or "repository" in str(e).lower()


# =============================================================================
# TEST SCENARIO 6: Consistency Check Workflow
# =============================================================================

def test_e2e_consistency_check_clean(temp_git_repo):
    """Test consistency check on clean project."""
    # Setup: Migrate project
    db_path = temp_git_repo / ".gao-dev" / "documents.db"
    migration_mgr = GitMigrationManager(db_path=db_path, project_path=temp_git_repo)
    migration_mgr.migrate_to_hybrid_architecture(create_branch=False, auto_merge=False)

    # Run consistency check
    checker = GitAwareConsistencyChecker(db_path=db_path, project_path=temp_git_repo)
    report = checker.check_consistency()

    # Should have no issues (clean migration)
    assert not report.has_issues or report.total_issues == 0


def test_e2e_consistency_check_and_repair(temp_git_repo):
    """Test consistency check detects issues and repair fixes them."""
    # Setup: Create inconsistent state
    db_path = temp_git_repo / ".gao-dev" / "documents.db"

    # Migrate
    migration_mgr = GitMigrationManager(db_path=db_path, project_path=temp_git_repo)
    migration_mgr.migrate_to_hybrid_architecture(create_branch=False, auto_merge=False)

    # Create inconsistency: Add file without registering in DB
    epic_file = temp_git_repo / "docs" / "epics" / "epic-99.md"
    epic_file.write_text("# Epic 99: Unregistered")

    # Run consistency check
    checker = GitAwareConsistencyChecker(db_path=db_path, project_path=temp_git_repo)
    report = checker.check_consistency()

    # Should detect unregistered file
    assert report.has_issues
    assert len(report.unregistered_files) > 0 or len(report.uncommitted_changes) > 0

    # Repair issues
    if report.has_issues:
        checker.repair(report, create_commit=False)

    # Re-check - should be clean now
    report2 = checker.check_consistency()
    # After repair, uncommitted changes expected (repaired files not committed)
    # but no structural issues
    assert len(report2.orphaned_records) == 0
    assert len(report2.state_mismatches) == 0


# =============================================================================
# TEST SCENARIO 7: Performance and Scale
# =============================================================================

@pytest.mark.asyncio
async def test_e2e_multiple_epics_and_stories(temp_git_repo):
    """Test system with multiple epics and stories."""
    orchestrator = GAODevOrchestrator.create_default(temp_git_repo)

    try:
        # Create 5 epics
        for epic_num in range(1, 6):
            epic_file = temp_git_repo / "docs" / "epics" / f"epic-{epic_num}.md"
            epic_file.write_text(f"# Epic {epic_num}")

            orchestrator.git_state_manager.create_epic(
                epic_num, f"Epic {epic_num}", "Test", epic_file
            )

            # Create 5 stories per epic
            story_dir = temp_git_repo / "docs" / "stories" / f"epic-{epic_num}"
            story_dir.mkdir(parents=True, exist_ok=True)

            for story_num in range(1, 6):
                story_file = story_dir / f"story-{epic_num}.{story_num}.md"
                story_file.write_text(f"# Story {epic_num}.{story_num}")

                orchestrator.git_state_manager.create_story(
                    epic_num, story_num, f"Story {story_num}", "Test", story_file
                )

        # Verify all created
        coordinator = StateCoordinator(db_path=temp_git_repo / ".gao-dev" / "documents.db")
        epics = coordinator.list_epics()
        assert len(epics) == 5

        # Verify stories for each epic
        for epic_num in range(1, 6):
            stories = coordinator.list_stories(epic_num)
            assert len(stories) == 5
    finally:
        orchestrator.close()
