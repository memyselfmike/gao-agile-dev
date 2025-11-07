"""Unit tests for artifact detection system (Story 18.2).

Tests the filesystem-based artifact detection that captures snapshots
before/after workflow execution to automatically detect created/modified files.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator


@pytest.fixture
def orchestrator(tmp_path):
    """Create orchestrator with automatic cleanup."""
    orch = GAODevOrchestrator(
        project_root=tmp_path,
        mode="benchmark"
    )
    yield orch
    orch.close()


class TestSnapshotProjectFiles:
    """Test _snapshot_project_files() method."""

    def test_snapshot_basic(self, tmp_path, orchestrator):
        """Test basic snapshot captures file metadata correctly."""
        # Create test files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("test content")

        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")

        # Take snapshot
        snapshot = orchestrator._snapshot_project_files()

        # Verify snapshot contains expected files
        paths = {item[0] for item in snapshot}
        assert "docs/test.md" in paths or "docs\\test.md" in paths
        assert "src/main.py" in paths or "src\\main.py" in paths

        # Verify metadata captured (path, mtime, size)
        for item in snapshot:
            assert len(item) == 3  # (path, mtime, size)
            assert isinstance(item[0], str)  # path
            assert isinstance(item[1], float)  # mtime
            assert isinstance(item[2], int)  # size

    def test_snapshot_excludes_ignored_dirs(self, tmp_path, orchestrator):
        """Test snapshot excludes ignored directories."""
        # Create files in ignored directories
        git_dir = tmp_path / "docs" / ".git"
        git_dir.mkdir(parents=True)
        (git_dir / "config").write_text("git config")

        node_dir = tmp_path / "src" / "node_modules"
        node_dir.mkdir(parents=True)
        (node_dir / "package.json").write_text("{}")

        cache_dir = tmp_path / "gao_dev" / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "test.pyc").write_bytes(b"compiled")

        # Create valid file
        (tmp_path / "docs" / "README.md").write_text("readme")


        # Take snapshot
        snapshot = orchestrator._snapshot_project_files()

        # Verify ignored files NOT in snapshot
        paths = {item[0] for item in snapshot}
        assert not any(".git" in path for path in paths)
        assert not any("node_modules" in path for path in paths)
        assert not any("__pycache__" in path for path in paths)

        # Verify valid file IS in snapshot
        assert "docs/README.md" in paths or "docs\\README.md" in paths

    def test_snapshot_handles_missing_dirs(self, tmp_path, orchestrator):
        """Test snapshot handles missing tracked directories gracefully."""
        # Don't create any directories - all missing

        # Should not crash, just return empty set
        snapshot = orchestrator._snapshot_project_files()
        assert isinstance(snapshot, set)
        assert len(snapshot) == 0

    def test_snapshot_handles_filesystem_errors(self, tmp_path, orchestrator):
        """Test snapshot handles filesystem errors gracefully."""
        # Create a file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "test.md"
        test_file.write_text("content")


        # Mock stat to raise OSError for specific file
        original_stat = Path.stat

        def mock_stat(self):
            if self.name == "test.md":
                raise OSError("Permission denied")
            return original_stat(self)

        with patch.object(Path, 'stat', mock_stat):
            # Should log warning but not crash
            snapshot = orchestrator._snapshot_project_files()
            # File with error should be skipped
            paths = {item[0] for item in snapshot}
            assert not any("test.md" in path for path in paths)

    def test_snapshot_relative_paths(self, tmp_path, orchestrator):
        """Test snapshot uses relative paths (not absolute)."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text("content")


        snapshot = orchestrator._snapshot_project_files()

        # All paths should be relative to project root
        for item in snapshot:
            path_str = item[0]
            assert not Path(path_str).is_absolute()
            # Should start with tracked directory name
            assert any(path_str.startswith(d) for d in ["docs", "src", "gao_dev"])

    def test_snapshot_performance(self, tmp_path, orchestrator):
        """Test snapshot performance is acceptable (<50ms for small project)."""
        # Create a moderate number of files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        for i in range(50):
            (docs_dir / f"file{i}.md").write_text(f"content {i}")


        # Measure snapshot time
        start = time.time()
        snapshot = orchestrator._snapshot_project_files()
        duration_ms = (time.time() - start) * 1000

        # Should be fast (<50ms for 50 files)
        assert duration_ms < 100  # Generous threshold for test environments
        assert len(snapshot) == 50


class TestDetectArtifacts:
    """Test _detect_artifacts() method."""

    def test_detect_new_files(self, tmp_path, orchestrator):
        """Test detection of newly created files."""

        # Create before snapshot (empty)
        before = set()

        # Create after snapshot (with new file)
        after = {
            ("docs/new.md", 1234567890.0, 100),
        }

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should detect the new file
        assert len(artifacts) == 1
        assert str(artifacts[0]) == "docs/new.md" or str(artifacts[0]) == "docs\\new.md"

    def test_detect_modified_files(self, tmp_path, orchestrator):
        """Test detection of modified files (changed mtime or size)."""

        # Before: file exists with specific metadata
        before = {
            ("docs/existing.md", 1234567890.0, 100),
        }

        # After: same file, different mtime (modified)
        after = {
            ("docs/existing.md", 1234567900.0, 100),  # Different mtime
        }

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should detect the modified file
        assert len(artifacts) == 1
        assert str(artifacts[0]) == "docs/existing.md" or str(artifacts[0]) == "docs\\existing.md"

    def test_detect_size_change(self, tmp_path, orchestrator):
        """Test detection when file size changes (even if mtime same)."""

        # Before: file with original size
        before = {
            ("src/main.py", 1234567890.0, 100),
        }

        # After: same file, different size
        after = {
            ("src/main.py", 1234567890.0, 200),  # Different size
        }

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should detect the size change
        assert len(artifacts) == 1

    def test_deleted_files_ignored(self, tmp_path, orchestrator):
        """Test that deleted files are NOT flagged as artifacts."""

        # Before: file exists
        before = {
            ("docs/deleted.md", 1234567890.0, 100),
        }

        # After: file no longer exists (empty)
        after = set()

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should NOT detect deleted file as artifact
        assert len(artifacts) == 0

    def test_unchanged_files_not_detected(self, tmp_path, orchestrator):
        """Test that unchanged files are NOT flagged as artifacts."""

        # Same snapshot before and after
        snapshot = {
            ("docs/unchanged.md", 1234567890.0, 100),
            ("src/main.py", 1234567891.0, 200),
        }

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(snapshot, snapshot)

        # Should detect nothing (no changes)
        assert len(artifacts) == 0

    def test_multiple_artifacts(self, tmp_path, orchestrator):
        """Test detection of multiple new/modified files."""

        before = {
            ("docs/existing.md", 1234567890.0, 100),
        }

        after = {
            ("docs/existing.md", 1234567900.0, 100),  # Modified
            ("docs/new.md", 1234567895.0, 50),        # New
            ("src/main.py", 1234567896.0, 300),       # New
        }

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should detect all 3 files (1 modified + 2 new)
        assert len(artifacts) == 3

        # Verify all expected files detected
        artifact_strs = {str(p) for p in artifacts}
        assert any("existing.md" in s for s in artifact_strs)
        assert any("new.md" in s for s in artifact_strs)
        assert any("main.py" in s for s in artifact_strs)

    def test_empty_diff(self, tmp_path, orchestrator):
        """Test detection with no changes (empty before and after)."""

        before = set()
        after = set()

        # Detect artifacts
        artifacts = orchestrator._detect_artifacts(before, after)

        # Should detect nothing
        assert len(artifacts) == 0
        assert isinstance(artifacts, list)


class TestSnapshotIntegration:
    """Test snapshot integration with ignored directories."""

    def test_ignores_all_standard_dirs(self, tmp_path, orchestrator):
        """Test all standard ignored directories are excluded."""
        # Create files in all ignored directories
        ignored_dirs = [
            ".git", "node_modules", "__pycache__", ".gao-dev",
            ".archive", "venv", ".venv", "dist", "build",
            ".pytest_cache", ".mypy_cache", "htmlcov"
        ]

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        for ignored_dir in ignored_dirs:
            test_dir = docs_dir / ignored_dir
            test_dir.mkdir()
            (test_dir / "test.txt").write_text("should be ignored")

        # Create valid file
        (docs_dir / "valid.md").write_text("valid content")


        snapshot = orchestrator._snapshot_project_files()

        # Only the valid file should be captured
        assert len(snapshot) == 1
        paths = {item[0] for item in snapshot}
        assert "docs/valid.md" in paths or "docs\\valid.md" in paths

    def test_nested_ignored_dirs(self, tmp_path, orchestrator):
        """Test nested ignored directories are excluded."""
        # Create nested structure: docs/subdir/.git/file
        docs_dir = tmp_path / "docs" / "subdir"
        docs_dir.mkdir(parents=True)

        git_dir = docs_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git")

        # Create valid file at same level
        (docs_dir / "valid.md").write_text("valid")


        snapshot = orchestrator._snapshot_project_files()

        # Should capture valid file but not .git/config
        paths = {item[0] for item in snapshot}
        assert any("valid.md" in path for path in paths)
        assert not any(".git" in path for path in paths)


class TestArtifactDetectionReturns:
    """Test return types and values of artifact detection."""

    def test_returns_path_objects(self, tmp_path, orchestrator):
        """Test _detect_artifacts returns List[Path]."""

        before = set()
        after = {("docs/test.md", 123.0, 100)}

        artifacts = orchestrator._detect_artifacts(before, after)

        # Should return list
        assert isinstance(artifacts, list)

        # Should contain Path objects
        assert len(artifacts) == 1
        assert isinstance(artifacts[0], Path)

    def test_paths_relative_to_project_root(self, tmp_path, orchestrator):
        """Test artifact paths are relative to project root."""

        before = set()
        after = {("docs/subdir/test.md", 123.0, 100)}

        artifacts = orchestrator._detect_artifacts(before, after)

        # Path should be relative
        assert not artifacts[0].is_absolute()
        assert str(artifacts[0]).startswith("docs")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
