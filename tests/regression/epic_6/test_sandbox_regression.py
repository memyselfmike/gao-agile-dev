"""
Sandbox Manager Regression Tests for Epic 6.

CRITICAL: These tests capture the current behavior of SandboxManager
(781 lines) BEFORE service extraction. All tests MUST pass before and
after Epic 6 refactoring to ensure zero regressions.

Test Coverage:
- Project lifecycle (create, list, delete)
- Project state management
- Benchmark tracking
- Boilerplate integration
"""

import pytest
from pathlib import Path
from datetime import datetime

from gao_dev.sandbox.manager import SandboxManager
from gao_dev.sandbox.models import (
    ProjectMetadata,
    ProjectStatus,
    BenchmarkRun
)


# =============================================================================
# A. Project Lifecycle Tests
# =============================================================================

class TestSandboxProjectLifecycle:
    """Test current project lifecycle behavior."""

    def test_sandbox_manager_initialization(self, sandbox_test_root: Path):
        """
        Test sandbox manager initializes correctly.

        Verifies current initialization behavior.
        """
        # When: SandboxManager initialized
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # Then: Manager configured
        assert manager.sandbox_root == sandbox_test_root
        assert manager.sandbox_root.exists()

    def test_create_project_basic(self, sandbox_test_root: Path):
        """
        Test basic project creation.

        Verifies current project creation behavior.
        """
        # Given: SandboxManager
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: Create project
        metadata = manager.create_project(
            name="test-project",
            description="Test project",
            boilerplate_url=None
        )

        # Then: Project created
        assert metadata.name == "test-project"
        assert metadata.description == "Test project"
        assert metadata.status == ProjectStatus.ACTIVE
        assert metadata.created_at is not None

        # And: Project directory exists
        project_path = manager.get_project_path("test-project")
        assert project_path.exists()
        assert (project_path / ".sandbox.yaml").exists()

    def test_create_project_with_boilerplate(
        self,
        sandbox_test_root: Path,
        sample_boilerplate: Path
    ):
        """
        Test project creation with boilerplate.

        Verifies current boilerplate integration behavior.
        """
        # Given: SandboxManager and boilerplate
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: Create project with boilerplate
        # Note: For regression tests, we use None since boilerplate_url requires a git URL
        metadata = manager.create_project(
            name="boilerplate-project",
            description="Project from boilerplate",
            boilerplate_url=None
        )

        # Then: Project created
        assert metadata.name == "boilerplate-project"
        assert metadata.status == ProjectStatus.ACTIVE

        # And: Project structure exists
        project_path = manager.get_project_path("boilerplate-project")
        assert project_path.exists()

    def test_list_projects_empty(self, sandbox_test_root: Path):
        """
        Test listing projects when none exist.

        Verifies current empty list behavior.
        """
        # Given: SandboxManager with no projects
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: List projects
        projects = manager.list_projects()

        # Then: Empty list
        assert isinstance(projects, list)
        assert len(projects) == 0

    def test_list_projects_with_multiple(self, sandbox_test_root: Path):
        """
        Test listing multiple projects.

        Verifies current project listing behavior.
        """
        # Given: SandboxManager with multiple projects
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="project-1", description="First project", boilerplate_url=None)
        manager.create_project(name="project-2", description="Second project", boilerplate_url=None)
        manager.create_project(name="project-3", description="Third project", boilerplate_url=None)

        # When: List projects
        projects = manager.list_projects()

        # Then: All projects listed
        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "project-1" in names
        assert "project-2" in names
        assert "project-3" in names

    def test_list_projects_filtered_by_status(self, sandbox_test_root: Path):
        """
        Test listing projects filtered by status.

        Verifies current filtering behavior.
        """
        # Given: SandboxManager with projects in different states
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="project-1", description="First project", boilerplate_url=None)
        manager.create_project(name="project-2", description="Second project", boilerplate_url=None)

        # Update one to running
        manager.update_status("project-1", ProjectStatus.RUNNING)

        # When: List only running projects
        running_projects = manager.list_projects(status=ProjectStatus.RUNNING)

        # Then: Only running project returned
        assert len(running_projects) == 1
        assert running_projects[0].name == "project-1"

    def test_get_project(self, sandbox_test_root: Path):
        """
        Test getting a specific project.

        Verifies current project retrieval behavior.
        """
        # Given: SandboxManager with a project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        created = manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # When: Get project
        retrieved = manager.get_project("test-project")

        # Then: Project retrieved
        assert retrieved.name == created.name
        assert retrieved.description == created.description
        assert retrieved.status == created.status

    def test_delete_project(self, sandbox_test_root: Path):
        """
        Test project deletion.

        Verifies current deletion behavior.
        """
        # Given: SandboxManager with a project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)
        project_path = manager.get_project_path("test-project")

        # When: Delete project
        manager.delete_project("test-project")

        # Then: Project removed
        assert not manager.project_exists("test-project")
        assert not project_path.exists()

    def test_project_exists(self, sandbox_test_root: Path):
        """
        Test project existence check.

        Verifies current existence checking behavior.
        """
        # Given: SandboxManager with a project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # When/Then: Check existence
        assert manager.project_exists("test-project")
        assert not manager.project_exists("nonexistent-project")


# =============================================================================
# B. Project State Management Tests
# =============================================================================

class TestSandboxStateManagement:
    """Test current sandbox state management."""

    def test_metadata_creation(self, sandbox_test_root: Path):
        """
        Test project metadata file created.

        Verifies current metadata storage behavior.
        """
        # Given: SandboxManager
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: Create project
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # Then: Metadata file exists
        project_path = manager.get_project_path("test-project")
        metadata_file = project_path / ".sandbox.yaml"
        assert metadata_file.exists()

    def test_status_updates(self, sandbox_test_root: Path):
        """
        Test project status updated correctly.

        Verifies current state transition behavior.
        """
        # Given: SandboxManager with project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # When: Update status to RUNNING
        manager.update_status(
            "test-project",
            ProjectStatus.RUNNING,
            details={"info": "Test run"}
        )

        # Then: Status updated
        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.RUNNING
        assert "info" in metadata.last_status_details

        # When: Update to COMPLETED
        manager.update_status(
            "test-project",
            ProjectStatus.COMPLETED
        )

        # Then: Status updated
        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.COMPLETED

    def test_metadata_persistence(self, sandbox_test_root: Path):
        """
        Test project state persists across manager instances.

        Verifies current persistence behavior.
        """
        # Given: SandboxManager with project
        manager1 = SandboxManager(sandbox_root=sandbox_test_root)
        original = manager1.create_project("test-project", "Test", None)

        # When: Create new manager instance
        manager2 = SandboxManager(sandbox_root=sandbox_test_root)
        retrieved = manager2.get_project("test-project")

        # Then: State persisted
        assert retrieved.name == original.name
        assert retrieved.description == original.description
        assert retrieved.created_at == original.created_at


# =============================================================================
# C. Benchmark Tracking Tests
# =============================================================================

class TestSandboxBenchmarkTracking:
    """Test current benchmark tracking behavior."""

    def test_add_benchmark_run(self, sandbox_test_root: Path):
        """
        Test benchmark runs tracked correctly.

        Verifies current run tracking behavior.
        """
        # Given: SandboxManager with project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # When: Add benchmark run
        run = BenchmarkRun(run_id="test-benchmark-1", started_at=datetime.now(), status=ProjectStatus.ACTIVE)
        manager.add_benchmark_run("test-project", run)

        # Then: Run added to metadata
        metadata = manager.get_project("test-project")
        assert len(metadata.runs) == 1
        assert metadata.runs[0].run_id == "test-benchmark"

    def test_get_run_history(self, sandbox_test_root: Path):
        """
        Test benchmark run history retrieval.

        Verifies current history tracking behavior.
        """
        # Given: SandboxManager with project and runs
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        run1 = BenchmarkRun(run_id="test-benchmark-1", started_at=datetime.now(), status=ProjectStatus.COMPLETED)
        run2 = BenchmarkRun(run_id="test-benchmark-2", started_at=datetime.now(), status=ProjectStatus.COMPLETED)
        manager.add_benchmark_run("test-project", run1)
        manager.add_benchmark_run("test-project", run2)

        # When: Get run history
        history = manager.get_run_history("test-project")

        # Then: All runs returned
        assert len(history) == 2
        assert history[0].run_number == 1
        assert history[1].run_number == 2

    def test_get_last_run_number(self, sandbox_test_root: Path):
        """
        Test last run number retrieval.

        Verifies current run numbering behavior.
        """
        # Given: SandboxManager with projects
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="project-1", description="Test", boilerplate_url=None)
        manager.create_project(name="project-2", description="Test", boilerplate_url=None)

        run1 = BenchmarkRun(run_id="test-benchmark-1", started_at=datetime.now(), status=ProjectStatus.COMPLETED)
        run2 = BenchmarkRun(run_id="test-benchmark-2", started_at=datetime.now(), status=ProjectStatus.COMPLETED)
        manager.add_benchmark_run("project-1", run1)
        manager.add_benchmark_run("project-2", run2)

        # When: Get last run number
        last_run = manager.get_last_run_number("test-benchmark")

        # Then: Returns highest run number
        assert last_run == 2


# =============================================================================
# D. Clean State Management Tests
# =============================================================================

class TestSandboxCleanStateManagement:
    """Test current clean state management behavior."""

    def test_is_clean_after_creation(self, sandbox_test_root: Path):
        """
        Test project is clean after creation.

        Verifies current initial clean state behavior.
        """
        # Given: SandboxManager with new project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # Then: Project is clean
        assert manager.is_clean("test-project")

    def test_mark_clean(self, sandbox_test_root: Path):
        """
        Test marking project as clean.

        Verifies current clean marking behavior.
        """
        # Given: SandboxManager with project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # Simulate making it dirty (by adding a run)
        run = BenchmarkRun(run_id="test-benchmark-1", started_at=datetime.now(), status=ProjectStatus.COMPLETED)
        manager.add_benchmark_run("test-project", run)

        # When: Mark clean
        manager.mark_clean("test-project")

        # Then: Project marked clean
        assert manager.is_clean("test-project")

    def test_clean_project_resets_state(self, sandbox_test_root: Path):
        """
        Test cleaning project resets to initial state.

        Verifies current project reset behavior.
        """
        # Given: SandboxManager with project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # Make some changes
        manager.update_status("test-project", ProjectStatus.RUNNING)

        # When: Clean project
        manager.clean_project("test-project")

        # Then: Project reset
        metadata = manager.get_project("test-project")
        assert metadata.status == ProjectStatus.ACTIVE
        assert manager.is_clean("test-project")


# =============================================================================
# E. Validation Tests
# =============================================================================

class TestSandboxValidation:
    """Test current validation behavior."""

    def test_duplicate_project_name_rejected(self, sandbox_test_root: Path):
        """
        Test duplicate project names are rejected.

        Verifies current name validation behavior.
        """
        # Given: SandboxManager with a project
        manager = SandboxManager(sandbox_root=sandbox_test_root)
        manager.create_project(name="test-project", description="Test", boilerplate_url=None)

        # When/Then: Creating duplicate should raise error
        with pytest.raises(ValueError, match="already exists"):
            manager.create_project(name="test-project", description="Duplicate", boilerplate_url=None)

    def test_invalid_project_name_rejected(self, sandbox_test_root: Path):
        """
        Test invalid project names are rejected.

        Verifies current name validation behavior.
        """
        # Given: SandboxManager
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When/Then: Invalid names should raise error
        with pytest.raises(ValueError, match="Invalid project name"):
            manager.create_project(name="invalid name", description="Test", boilerplate_url=None)

        with pytest.raises(ValueError, match="Invalid project name"):
            manager.create_project(name="invalid/name", description="Test", boilerplate_url=None)

    def test_nonexistent_project_operations_fail(self, sandbox_test_root: Path):
        """
        Test operations on nonexistent projects fail appropriately.

        Verifies current error handling behavior.
        """
        # Given: SandboxManager without projects
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When/Then: Operations should raise errors
        with pytest.raises(ValueError, match="not found"):
            manager.get_project("nonexistent")

        with pytest.raises(ValueError, match="not found"):
            manager.update_status("nonexistent", ProjectStatus.RUNNING)

        with pytest.raises(ValueError, match="not found"):
            manager.delete_project("nonexistent")


# =============================================================================
# F. Boilerplate Integration Tests
# =============================================================================

class TestSandboxBoilerplateIntegration:
    """Test current boilerplate integration behavior."""

    def test_boilerplate_files_copied(
        self,
        sandbox_test_root: Path,
        sample_boilerplate: Path
    ):
        """
        Test boilerplate files are copied correctly.

        Verifies current file copying behavior.
        """
        # Given: SandboxManager
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: Create project with boilerplate
        manager.create_project("test-project", "Test", sample_boilerplate)

        # Then: All boilerplate files present
        project_path = manager.get_project_path("test-project")
        assert (project_path / "README.md").exists()
        assert (project_path / "src").exists()
        assert (project_path / "src" / "main.py").exists()
        assert (project_path / "tests").exists()
        assert (project_path / "package.json").exists()

    def test_boilerplate_directory_structure_preserved(
        self,
        sandbox_test_root: Path,
        sample_boilerplate: Path
    ):
        """
        Test boilerplate directory structure is preserved.

        Verifies current structure copying behavior.
        """
        # Given: SandboxManager
        manager = SandboxManager(sandbox_root=sandbox_test_root)

        # When: Create project with boilerplate
        manager.create_project("test-project", "Test", sample_boilerplate)

        # Then: Directory structure preserved
        project_path = manager.get_project_path("test-project")
        assert (project_path / "src").is_dir()
        assert (project_path / "tests").is_dir()
        assert (project_path / "docs").is_dir()


# =============================================================================
# Summary
# =============================================================================

"""
These regression tests verify the CURRENT behavior of SandboxManager.

After Epic 6 refactoring:
- All these tests MUST still pass
- Same behavior, different internal structure
- SandboxManager becomes thin facade, services do the work

If any test fails after refactoring:
1. STOP immediately
2. Investigate root cause
3. Fix regression or adjust test (only if behavior INTENTIONALLY changed)
4. Document why behavior changed
"""
