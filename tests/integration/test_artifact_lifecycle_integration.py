"""Integration tests for artifact lifecycle integration (Story 18.3).

Tests the end-to-end integration between workflow execution, artifact detection,
and document lifecycle management.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle


class TestArtifactLifecycleIntegration:
    """Test integration between orchestrator and document lifecycle."""

    @pytest.mark.asyncio
    async def test_prd_registered_as_product_requirements(self, tmp_path):
        """Test PRD workflow registers artifact as 'product-requirements' type."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize document lifecycle for this project
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator with document lifecycle
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Ensure doc_lifecycle is set
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor to avoid actual Claude CLI calls
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Simulate creating a PRD file during execution
            prd_file = docs_dir / "PRD.md"
            prd_file.write_text("# Product Requirements Document\n\nTest PRD content")
            yield "Creating PRD..."
            yield "PRD created successfully"

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Create workflow info for PRD
        workflow_info = WorkflowInfo(
            name="prd",
            description="Create PRD",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/prd",
            variables={}
        )

        # Execute workflow (this will trigger artifact detection and registration)
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=1,
            story=1
        ):
            outputs.append(output)

        # Verify artifact was registered
        documents = doc_lifecycle.registry.list_documents()
        assert len(documents) > 0

        # Find PRD document
        prd_docs = [doc for doc in documents if doc.doc_type == "prd"]
        assert len(prd_docs) == 1

        prd_doc = prd_docs[0]
        assert prd_doc.author == "john"
        assert prd_doc.metadata["workflow"] == "prd"
        assert prd_doc.metadata["created_by_workflow"] is True

    @pytest.mark.asyncio
    async def test_story_registered_with_epic_story_metadata(self, tmp_path):
        """Test story workflow registers artifact with epic and story numbers."""
        # Create test project structure
        docs_dir = tmp_path / "docs" / "features" / "auth"
        docs_dir.mkdir(parents=True)

        # Initialize document lifecycle
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Simulate creating a story file
            story_file = docs_dir / "story-1.1.md"
            story_file.write_text("# Story 1.1: User Login\n\nTest story content")
            yield "Creating story..."
            yield "Story created successfully"

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Create workflow info for story
        workflow_info = WorkflowInfo(
            name="create-story",
            description="Create user story",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/create-story",
            variables={}
        )

        # Execute workflow with specific epic/story numbers
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=3,
            story=5
        ):
            outputs.append(output)

        # Verify artifact was registered with correct metadata
        documents = doc_lifecycle.registry.list_documents()
        story_docs = [doc for doc in documents if doc.doc_type == "story"]
        assert len(story_docs) == 1

        story_doc = story_docs[0]
        assert story_doc.author == "bob"
        assert story_doc.metadata["workflow"] == "create-story"
        assert story_doc.metadata["epic"] == 3
        assert story_doc.metadata["story"] == 5
        assert story_doc.metadata["created_by_workflow"] is True

    @pytest.mark.asyncio
    async def test_artifacts_queryable_via_document_lifecycle(self, tmp_path):
        """Test registered artifacts can be queried via DocumentLifecycleManager."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize document lifecycle
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Simulate creating multiple files
            (docs_dir / "PRD.md").write_text("# PRD")
            (docs_dir / "Architecture.md").write_text("# Architecture")
            yield "Creating documents..."
            yield "Documents created"

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Create workflow info
        workflow_info = WorkflowInfo(
            name="prd",
            description="Create PRD",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/prd",
            variables={},
        )

        # Execute workflow
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=1,
            story=1
        ):
            outputs.append(output)

        # Query documents by type
        all_docs = doc_lifecycle.registry.list_documents()
        assert len(all_docs) >= 2

        # Query by author
        john_docs = [doc for doc in all_docs if doc.author == "john"]
        assert len(john_docs) >= 2

        # Query by metadata
        workflow_docs = [
            doc for doc in all_docs
            if doc.metadata.get("workflow") == "prd"
        ]
        assert len(workflow_docs) >= 2

    @pytest.mark.asyncio
    async def test_registration_failure_does_not_break_workflow(self, tmp_path):
        """Test workflow continues even if document registration fails."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize orchestrator WITHOUT document lifecycle (simulate failure)
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock doc_lifecycle to raise exception
        mock_doc_lifecycle = MagicMock()
        mock_doc_lifecycle.register_document.side_effect = Exception("Database error")
        orchestrator.doc_lifecycle = mock_doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Simulate creating a file
            (docs_dir / "PRD.md").write_text("# PRD")
            yield "Creating PRD..."
            yield "PRD created"

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Create workflow info
        workflow_info = WorkflowInfo(
            name="prd",
            description="Create PRD",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/prd",
            variables={},
        )

        # Execute workflow - should NOT raise exception despite registration failure
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=1,
            story=1
        ):
            outputs.append(output)

        # Workflow should complete successfully
        assert len(outputs) == 2
        assert "PRD created" in outputs[1]

    @pytest.mark.asyncio
    async def test_variables_included_in_metadata(self, tmp_path):
        """Test resolved workflow variables are included in artifact metadata."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize document lifecycle
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Simulate creating a file
            (docs_dir / "PRD.md").write_text("# PRD")
            yield "Creating PRD..."

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Mock WorkflowExecutor to return specific variables
        mock_workflow_executor = MagicMock()
        mock_workflow_executor.resolve_variables.return_value = {
            "project_name": "MyApp",
            "version": "1.0.0",
            "author": "TestTeam",
            "custom_var": "custom_value"
        }
        orchestrator.workflow_executor = mock_workflow_executor

        # Create workflow info
        workflow_info = WorkflowInfo(
            name="prd",
            description="Create PRD",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/prd",
            variables={},
        )

        # Execute workflow
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=1,
            story=1
        ):
            outputs.append(output)

        # Verify variables were included in metadata
        documents = doc_lifecycle.registry.list_documents()
        assert len(documents) > 0

        doc = documents[0]
        assert "variables" in doc.metadata
        assert doc.metadata["variables"]["project_name"] == "MyApp"
        assert doc.metadata["variables"]["version"] == "1.0.0"
        assert doc.metadata["variables"]["author"] == "TestTeam"
        assert doc.metadata["variables"]["custom_var"] == "custom_value"

    @pytest.mark.asyncio
    async def test_multiple_workflow_types_register_correctly(self, tmp_path):
        """Test different workflow types register with correct document types."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize document lifecycle
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        orchestrator.process_executor = mock_executor

        # Test cases: (workflow_name, file_name, expected_doc_type, expected_author)
        test_cases = [
            ("prd", "PRD.md", "prd", "john"),
            ("architecture", "ARCHITECTURE.md", "architecture", "winston"),
            ("create-story", "story-1.md", "story", "bob"),
            ("test", "test-plan.md", "test_report", "murat"),
            ("ux-design", "design.md", "adr", "sally"),
        ]

        for workflow_name, file_name, expected_doc_type, expected_author in test_cases:
            # Mock execution to create file
            async def mock_execution(*args, **kwargs):
                file_path = docs_dir / file_name
                file_path.write_text(f"# {file_name}")
                yield f"Creating {file_name}..."

            mock_executor.execute_agent_task = AsyncMock(side_effect=mock_execution)

            # Create workflow info
            workflow_info = WorkflowInfo(
                name=workflow_name,
                description=f"Test {workflow_name}",
                phase=2,  # Planning phase
                installed_path=tmp_path / "workflows" / workflow_name,
                variables={},
            )

            # Execute workflow
            outputs = []
            async for output in orchestrator._execute_agent_task_static(
                workflow_info=workflow_info,
                epic=1,
                story=1
            ):
                outputs.append(output)

        # Verify all documents were registered with correct types and authors
        documents = doc_lifecycle.registry.list_documents()
        assert len(documents) == len(test_cases)

        # Check each document type
        for workflow_name, file_name, expected_doc_type, expected_author in test_cases:
            matching_docs = [
                doc for doc in documents
                if doc.doc_type == expected_doc_type
                and doc.author == expected_author
            ]
            assert len(matching_docs) >= 1, f"Expected document type {expected_doc_type} not found"

    @pytest.mark.asyncio
    async def test_artifacts_in_database(self, tmp_path):
        """Test registered artifacts persist in .gao-dev/documents.db."""
        # Create test project structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Initialize document lifecycle (creates .gao-dev/documents.db)
        doc_lifecycle = ProjectDocumentLifecycle.initialize(tmp_path)

        # Create orchestrator
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )
        orchestrator.doc_lifecycle = doc_lifecycle

        # Mock ProcessExecutor
        mock_executor = MagicMock()
        mock_executor.execute_agent_task = AsyncMock()

        async def mock_execution(*args, **kwargs):
            # Create test file
            (docs_dir / "PRD.md").write_text("# PRD Content")
            yield "Creating PRD..."

        mock_executor.execute_agent_task.side_effect = mock_execution
        orchestrator.process_executor = mock_executor

        # Create workflow info
        workflow_info = WorkflowInfo(
            name="prd",
            description="Create PRD",
            phase=2,  # Planning phase
            installed_path=tmp_path / "workflows/prd",
            variables={},
        )

        # Execute workflow
        outputs = []
        async for output in orchestrator._execute_agent_task_static(
            workflow_info=workflow_info,
            epic=1,
            story=1
        ):
            outputs.append(output)

        # Verify database file exists
        db_path = tmp_path / ".gao-dev" / "documents.db"
        assert db_path.exists()

        # Verify database contains the document
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
