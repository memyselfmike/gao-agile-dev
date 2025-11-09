"""Unit tests for ArtifactManager service.

Tests cover:
- Snapshot creation with various directory structures
- Artifact detection algorithms
- Document type inference logic
- Artifact registration coordination with DocumentLifecycleManager
- Edge cases and error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from gao_dev.orchestrator.artifact_manager import ArtifactManager


@pytest.fixture
def mock_doc_lifecycle():
    """Create a mock DocumentLifecycleManager."""
    mock = Mock()
    mock_doc = Mock()
    mock_doc.id = "test-doc-123"
    mock.register_document.return_value = mock_doc
    return mock


@pytest.fixture
def artifact_manager(tmp_path, mock_doc_lifecycle):
    """Create an ArtifactManager instance with a temporary project root."""
    return ArtifactManager(
        project_root=tmp_path,
        document_lifecycle=mock_doc_lifecycle,
        tracked_dirs=["docs", "src", "gao_dev"],
    )


class TestArtifactManagerInitialization:
    """Test ArtifactManager initialization."""

    def test_artifact_manager_initialization(self, tmp_path, mock_doc_lifecycle):
        """Test that ArtifactManager initializes correctly."""
        manager = ArtifactManager(
            project_root=tmp_path,
            document_lifecycle=mock_doc_lifecycle,
            tracked_dirs=["docs", "src"],
        )

        assert manager.project_root == tmp_path
        assert manager.doc_lifecycle == mock_doc_lifecycle
        assert manager.tracked_dirs == ["docs", "src"]
        assert len(manager.ignored_dirs) > 0
        assert ".git" in manager.ignored_dirs

    def test_initialization_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        manager = ArtifactManager(project_root=tmp_path)

        assert manager.project_root == tmp_path
        assert manager.doc_lifecycle is None
        assert manager.tracked_dirs == ["docs", "src", "gao_dev"]


class TestSnapshot:
    """Test filesystem snapshot functionality."""

    def test_snapshot_empty_project(self, artifact_manager):
        """Test snapshot with no files in tracked directories."""
        snapshot = artifact_manager.snapshot()

        assert isinstance(snapshot, set)
        assert len(snapshot) == 0

    def test_snapshot_with_files(self, artifact_manager, tmp_path):
        """Test snapshot captures files correctly."""
        # Create test files in tracked directories
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")
        (docs_dir / "epic-1.md").write_text("# Epic 1")

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")

        snapshot = artifact_manager.snapshot()

        assert len(snapshot) == 3
        # Verify snapshot contains tuples of (path, mtime, size)
        paths = {item[0] for item in snapshot}
        assert "docs/PRD.md" in paths or "docs\\PRD.md" in paths
        assert "docs/epic-1.md" in paths or "docs\\epic-1.md" in paths
        assert "src/main.py" in paths or "src\\main.py" in paths

    def test_snapshot_ignores_excluded_directories(self, artifact_manager, tmp_path):
        """Test that snapshot ignores excluded directories."""
        # Create files in tracked directory
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # Create files in ignored directory
        git_dir = docs_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        cache_dir = docs_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.pyc").write_text("bytecode")

        snapshot = artifact_manager.snapshot()

        # Only PRD.md should be captured
        assert len(snapshot) == 1
        paths = {item[0] for item in snapshot}
        assert any("PRD.md" in path for path in paths)
        assert not any(".git" in path for path in paths)
        assert not any("__pycache__" in path for path in paths)


class TestDetect:
    """Test artifact detection functionality."""

    def test_detect_new_files(self, artifact_manager, tmp_path):
        """Test detection of newly created files."""
        # Initial snapshot (empty)
        before = artifact_manager.snapshot()

        # Create new files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # Second snapshot
        after = artifact_manager.snapshot()

        # Detect artifacts
        artifacts = artifact_manager.detect(before, after)

        assert len(artifacts) == 1
        assert artifacts[0].name == "PRD.md"

    def test_detect_modified_files(self, artifact_manager, tmp_path):
        """Test detection of modified files."""
        # Create initial file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        prd_file = docs_dir / "PRD.md"
        prd_file.write_text("# PRD v1")

        # Initial snapshot
        before = artifact_manager.snapshot()

        # Modify file
        import time
        time.sleep(0.01)  # Ensure mtime changes
        prd_file.write_text("# PRD v2 - updated")

        # Second snapshot
        after = artifact_manager.snapshot()

        # Detect artifacts
        artifacts = artifact_manager.detect(before, after)

        assert len(artifacts) == 1
        assert artifacts[0].name == "PRD.md"

    def test_detect_no_changes(self, artifact_manager, tmp_path):
        """Test detection when nothing changes."""
        # Create files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # Two identical snapshots
        before = artifact_manager.snapshot()
        after = artifact_manager.snapshot()

        # Detect artifacts
        artifacts = artifact_manager.detect(before, after)

        assert len(artifacts) == 0


class TestInferType:
    """Test document type inference functionality."""

    def test_infer_type_prd(self, artifact_manager):
        """Test PRD type inference from workflow name."""
        doc_type = artifact_manager.infer_type(Path("docs/PRD.md"), "prd")
        assert doc_type == "prd"

    def test_infer_type_epic(self, artifact_manager):
        """Test epic type inference."""
        doc_type = artifact_manager.infer_type(Path("docs/epic-1.md"), "epic")
        assert doc_type == "epic"

    def test_infer_type_story(self, artifact_manager):
        """Test story type inference from workflow name."""
        doc_type = artifact_manager.infer_type(Path("docs/story-1.1.md"), "create-story")
        assert doc_type == "story"

    def test_infer_type_architecture(self, artifact_manager):
        """Test architecture document type inference."""
        doc_type = artifact_manager.infer_type(Path("docs/ARCHITECTURE.md"), "architecture")
        assert doc_type == "architecture"

    def test_infer_type_unknown(self, artifact_manager):
        """Test fallback to 'story' for unknown types."""
        doc_type = artifact_manager.infer_type(Path("docs/unknown.md"), "custom-workflow")
        assert doc_type == "story"  # Default fallback

    def test_infer_type_from_path_fallback(self, artifact_manager):
        """Test type inference from path when workflow doesn't match."""
        # Workflow name doesn't match, but path contains 'epic'
        doc_type = artifact_manager.infer_type(Path("docs/epic-1.md"), "custom-workflow")
        assert doc_type == "epic"


class TestRegister:
    """Test artifact registration functionality."""

    def test_register_single_artifact(self, artifact_manager, mock_doc_lifecycle, tmp_path):
        """Test registering a single artifact."""
        # Create artifact file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        prd_file = docs_dir / "PRD.md"
        prd_file.write_text("# PRD")

        # Register artifact
        artifacts = [Path("docs/PRD.md")]
        artifact_manager.register(
            artifacts=artifacts,
            workflow_name="prd",
            epic=1,
            story=1,
            agent="john",
            phase="planning",
            variables={"project_name": "TestApp"},
        )

        # Verify registration was called
        assert mock_doc_lifecycle.register_document.call_count == 1
        call_args = mock_doc_lifecycle.register_document.call_args

        assert call_args.kwargs["doc_type"] == "prd"
        assert call_args.kwargs["author"] == "john"
        assert call_args.kwargs["metadata"]["workflow"] == "prd"
        assert call_args.kwargs["metadata"]["epic"] == 1
        assert call_args.kwargs["metadata"]["story"] == 1

    def test_register_multiple_artifacts(self, artifact_manager, mock_doc_lifecycle, tmp_path):
        """Test registering multiple artifacts in one call."""
        # Create artifact files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")
        (docs_dir / "epic-1.md").write_text("# Epic 1")
        (docs_dir / "story-1.1.md").write_text("# Story 1.1")

        # Register artifacts
        artifacts = [
            Path("docs/PRD.md"),
            Path("docs/epic-1.md"),
            Path("docs/story-1.1.md"),
        ]
        artifact_manager.register(
            artifacts=artifacts,
            workflow_name="prd",
            epic=1,
            story=1,
            agent="john",
            phase="planning",
            variables={},
        )

        # Verify all artifacts were registered
        assert mock_doc_lifecycle.register_document.call_count == 3

    def test_register_with_metadata(self, artifact_manager, mock_doc_lifecycle, tmp_path):
        """Test that metadata is correctly passed during registration."""
        # Create artifact file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # Register with comprehensive metadata
        variables = {
            "project_name": "TestApp",
            "prd_location": "docs/PRD.md",
            "epic_num": 1,
        }

        artifact_manager.register(
            artifacts=[Path("docs/PRD.md")],
            workflow_name="prd",
            epic=1,
            story=1,
            agent="john",
            phase="planning",
            variables=variables,
        )

        # Verify metadata structure
        call_args = mock_doc_lifecycle.register_document.call_args
        metadata = call_args.kwargs["metadata"]

        assert metadata["workflow"] == "prd"
        assert metadata["epic"] == 1
        assert metadata["story"] == 1
        assert metadata["phase"] == "planning"
        assert metadata["created_by_workflow"] is True
        assert metadata["variables"] == variables
        assert metadata["workflow_phase"] == "planning"

    def test_register_without_lifecycle_manager(self, tmp_path):
        """Test that registration gracefully handles missing lifecycle manager."""
        # Create manager without lifecycle
        manager = ArtifactManager(
            project_root=tmp_path, document_lifecycle=None, tracked_dirs=["docs"]
        )

        # Create artifact
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # This should not raise an exception
        manager.register(
            artifacts=[Path("docs/PRD.md")],
            workflow_name="prd",
            epic=1,
            story=1,
            agent="john",
            phase="planning",
            variables={},
        )

    def test_register_handles_registration_failure(
        self, artifact_manager, mock_doc_lifecycle, tmp_path
    ):
        """Test that registration failures are handled gracefully."""
        # Make registration fail
        mock_doc_lifecycle.register_document.side_effect = Exception("Registration failed")

        # Create artifact
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")

        # This should not raise an exception (failures are logged as warnings)
        artifact_manager.register(
            artifacts=[Path("docs/PRD.md")],
            workflow_name="prd",
            epic=1,
            story=1,
            agent="john",
            phase="planning",
            variables={},
        )

        # Verify registration was attempted
        assert mock_doc_lifecycle.register_document.call_count == 1


class TestIsTrackedDirectory:
    """Test directory filtering logic."""

    def test_is_tracked_directory(self, artifact_manager, tmp_path):
        """Test that tracked directories are correctly identified in snapshot."""
        # Create tracked directory
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("test")

        # Create non-tracked directory
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        (other_dir / "test.txt").write_text("test")

        snapshot = artifact_manager.snapshot()

        # Only docs/test.md should be in snapshot
        paths = {item[0] for item in snapshot}
        assert any("docs" in path for path in paths)
        assert not any("other" in path for path in paths)
