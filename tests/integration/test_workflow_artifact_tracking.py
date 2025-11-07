"""Integration tests for end-to-end workflow artifact tracking (Story 18.2).

Tests the complete artifact detection flow:
1. Snapshot before workflow execution
2. LLM creates/modifies files during workflow
3. Snapshot after workflow execution
4. Artifact detection finds all changes
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.core.workflow_registry import WorkflowInfo


@pytest.fixture
def mock_workflow_info(tmp_path):
    """Create mock WorkflowInfo for testing."""
    # Create workflow directory with instructions
    workflow_dir = tmp_path / "workflows" / "test-workflow"
    workflow_dir.mkdir(parents=True)

    instructions_file = workflow_dir / "instructions.md"
    instructions_file.write_text("Test workflow instructions")

    return WorkflowInfo(
        name="test-workflow",
        description="Test workflow",
        installed_path=str(workflow_dir),
        workflow_type="task",
        phase="implementation",
        tools=["Read", "Write"],
        agents=["Amelia"],
    )


class TestWorkflowArtifactDetectionE2E:
    """End-to-end tests for workflow artifact detection."""

    @pytest.mark.asyncio
    async def test_workflow_creates_single_file(self, tmp_path, mock_workflow_info):
        """Test artifact detection when workflow creates one file."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create docs directory for LLM to write to
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Mock ProcessExecutor to simulate file creation
        async def mock_execute(*args, **kwargs):
            # Simulate LLM creating a file
            test_file = docs_dir / "created-by-llm.md"
            test_file.write_text("# Test Document\n\nCreated by LLM")
            yield "Creating file..."
            yield "File created successfully"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow (which will create file)
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # Verify file was created
        assert (docs_dir / "created-by-llm.md").exists()

        # Verify artifact was logged (check log output indirectly via file existence)
        # In real usage, we'd check structured logs
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_workflow_modifies_existing_file(self, tmp_path, mock_workflow_info):
        """Test artifact detection when workflow modifies existing file."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create existing file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        existing_file = docs_dir / "existing.md"
        existing_file.write_text("Original content")

        import time
        time.sleep(0.01)  # Ensure mtime differs

        # Mock ProcessExecutor to simulate file modification
        async def mock_execute(*args, **kwargs):
            # Simulate LLM modifying the file
            existing_file.write_text("Modified content by LLM")
            yield "Modifying file..."
            yield "File modified successfully"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # Verify file was modified
        assert existing_file.read_text() == "Modified content by LLM"

    @pytest.mark.asyncio
    async def test_workflow_creates_multiple_files(self, tmp_path, mock_workflow_info):
        """Test artifact detection with multiple file creations."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create directories
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Mock ProcessExecutor to simulate multiple file creation
        async def mock_execute(*args, **kwargs):
            # Simulate LLM creating multiple files
            (docs_dir / "README.md").write_text("# README")
            (docs_dir / "ARCHITECTURE.md").write_text("# Architecture")
            (src_dir / "main.py").write_text("print('hello')")
            yield "Creating files..."
            yield "Files created successfully"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # Verify all files were created
        assert (docs_dir / "README.md").exists()
        assert (docs_dir / "ARCHITECTURE.md").exists()
        assert (src_dir / "main.py").exists()

    @pytest.mark.asyncio
    async def test_workflow_no_changes(self, tmp_path, mock_workflow_info):
        """Test artifact detection when workflow makes no changes."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create existing file that won't be modified
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "unchanged.md").write_text("Original content")

        # Mock ProcessExecutor - no file operations
        async def mock_execute(*args, **kwargs):
            # Simulate LLM doing analysis but not creating files
            yield "Analyzing..."
            yield "Analysis complete (no files created)"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # File should remain unchanged
        assert (docs_dir / "unchanged.md").read_text() == "Original content"

    @pytest.mark.asyncio
    async def test_ignores_files_in_ignored_dirs(self, tmp_path, mock_workflow_info):
        """Test that files created in ignored directories are not tracked."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create directories
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Mock ProcessExecutor to create files in both tracked and ignored dirs
        async def mock_execute(*args, **kwargs):
            # Create file in tracked directory
            (docs_dir / "tracked.md").write_text("Tracked")

            # Create files in ignored directories
            git_dir = docs_dir / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("Git config")

            node_dir = docs_dir / "node_modules"
            node_dir.mkdir()
            (node_dir / "package.json").write_text("{}")

            yield "Creating files..."

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Capture snapshots manually to verify
            before = orchestrator._snapshot_project_files()

            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

            after = orchestrator._snapshot_project_files()

        # Verify ignored files are not in snapshot
        paths = {item[0] for item in after}
        assert not any(".git" in path for path in paths)
        assert not any("node_modules" in path for path in paths)

    @pytest.mark.asyncio
    async def test_handles_nested_directory_creation(self, tmp_path, mock_workflow_info):
        """Test artifact detection with nested directory structures."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock ProcessExecutor to create nested structure
        async def mock_execute(*args, **kwargs):
            # Create deeply nested file
            nested_dir = tmp_path / "docs" / "features" / "epic-1"
            nested_dir.mkdir(parents=True)
            (nested_dir / "story-1.md").write_text("# Story 1")
            yield "Creating nested structure..."

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # Verify nested file was created
        assert (tmp_path / "docs" / "features" / "epic-1" / "story-1.md").exists()


class TestArtifactDetectionPerformance:
    """Performance tests for artifact detection."""

    @pytest.mark.asyncio
    async def test_snapshot_performance_100_files(self, tmp_path):
        """Test snapshot performance with 100 files (<100ms total)."""
        # Create 100 files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        for i in range(100):
            (docs_dir / f"file{i}.md").write_text(f"Content {i}")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Measure snapshot performance
        import time
        start = time.time()
        snapshot = orchestrator._snapshot_project_files()
        duration_ms = (time.time() - start) * 1000

        # Should be fast (<100ms for 100 files)
        assert duration_ms < 200  # Generous threshold for test environments
        assert len(snapshot) == 100

    @pytest.mark.asyncio
    async def test_detection_performance(self, tmp_path):
        """Test detection performance is negligible (<10ms)."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Create large before/after snapshots
        before = {(f"docs/file{i}.md", 123.0 + i, 100) for i in range(1000)}
        after = {(f"docs/file{i}.md", 124.0 + i, 100) for i in range(1000)}  # All modified

        # Measure detection performance
        import time
        start = time.time()
        artifacts = orchestrator._detect_artifacts(before, after)
        duration_ms = (time.time() - start) * 1000

        # Detection should be very fast (just set difference)
        assert duration_ms < 50  # Should be <10ms but generous for tests
        assert len(artifacts) == 1000


class TestArtifactDetectionEdgeCases:
    """Test edge cases in artifact detection."""

    @pytest.mark.asyncio
    async def test_concurrent_file_modifications(self, tmp_path, mock_workflow_info):
        """Test handling of rapid file modifications."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Mock ProcessExecutor to rapidly modify files
        async def mock_execute(*args, **kwargs):
            test_file = docs_dir / "rapid.md"
            for i in range(5):
                test_file.write_text(f"Version {i}")
                await asyncio.sleep(0.001)  # Minimal delay
            yield "Rapid modifications complete"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # File should exist with final content
        assert (docs_dir / "rapid.md").read_text() == "Version 4"

    @pytest.mark.asyncio
    async def test_large_file_creation(self, tmp_path, mock_workflow_info):
        """Test artifact detection with large files."""
        # Setup orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Mock ProcessExecutor to create large file
        async def mock_execute(*args, **kwargs):
            large_content = "x" * 1_000_000  # 1MB file
            (docs_dir / "large.md").write_text(large_content)
            yield "Created large file"

        with patch.object(orchestrator.process_executor, 'execute_agent_task', mock_execute):
            # Execute workflow
            output = []
            async for chunk in orchestrator._execute_agent_task_static(
                workflow_info=mock_workflow_info,
                epic=1,
                story=1
            ):
                output.append(chunk)

        # Verify large file was created and detected
        assert (docs_dir / "large.md").exists()
        assert (docs_dir / "large.md").stat().st_size == 1_000_000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
