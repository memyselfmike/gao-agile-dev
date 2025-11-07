"""Unit tests for document registration system (Story 18.3).

Tests the automatic artifact registration with DocumentLifecycleManager,
including document type inference, author determination, and metadata construction.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.core.models.workflow import WorkflowInfo


@pytest.fixture
def mock_workflow_info():
    """Create a mock WorkflowInfo object for testing."""
    return WorkflowInfo(
        name="prd",
        description="Create PRD",
        phase=2,  # Planning phase
        installed_path=Path("/fake/path"),
        variables={}
    )


class TestInferDocumentType:
    """Test _infer_document_type() method."""

    def test_infer_from_workflow_name_prd(self, tmp_path, mock_workflow_info):
        """Test document type inferred from PRD workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "prd"
        doc_type = orchestrator._infer_document_type(
            Path("docs/PRD.md"),
            mock_workflow_info
        )

        assert doc_type == "prd"

    def test_infer_from_workflow_name_architecture(self, tmp_path, mock_workflow_info):
        """Test document type inferred from architecture workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "architecture"
        doc_type = orchestrator._infer_document_type(
            Path("docs/ARCHITECTURE.md"),
            mock_workflow_info
        )

        assert doc_type == "architecture"

    def test_infer_from_workflow_name_story(self, tmp_path, mock_workflow_info):
        """Test document type inferred from story workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "create-story"
        doc_type = orchestrator._infer_document_type(
            Path("docs/epic-1/story-1.md"),
            mock_workflow_info
        )

        assert doc_type == "story"

    def test_infer_from_workflow_name_epic(self, tmp_path, mock_workflow_info):
        """Test document type inferred from epic workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "epic"
        doc_type = orchestrator._infer_document_type(
            Path("docs/epic-1.md"),
            mock_workflow_info
        )

        assert doc_type == "epic"

    def test_infer_from_workflow_name_test(self, tmp_path, mock_workflow_info):
        """Test document type inferred from test workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "test"
        doc_type = orchestrator._infer_document_type(
            Path("docs/test-plan.md"),
            mock_workflow_info
        )

        assert doc_type == "test_report"

    def test_infer_from_workflow_name_design(self, tmp_path, mock_workflow_info):
        """Test document type inferred from design workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "ux-design"
        doc_type = orchestrator._infer_document_type(
            Path("docs/design.md"),
            mock_workflow_info
        )

        assert doc_type == "adr"

    def test_infer_from_workflow_name_tech_spec(self, tmp_path, mock_workflow_info):
        """Test document type inferred from tech-spec workflow name."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "tech-spec"
        doc_type = orchestrator._infer_document_type(
            Path("docs/spec.md"),
            mock_workflow_info
        )

        assert doc_type == "architecture"

    def test_infer_from_path_when_workflow_unknown(self, tmp_path, mock_workflow_info):
        """Test document type inferred from path when workflow name is unknown."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "unknown-workflow"
        doc_type = orchestrator._infer_document_type(
            Path("docs/features/auth/story-1.md"),
            mock_workflow_info
        )

        # Should fall back to path-based detection
        assert doc_type == "story"

    def test_infer_from_path_prd(self, tmp_path, mock_workflow_info):
        """Test document type inferred from path containing 'prd'."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "custom-workflow"
        doc_type = orchestrator._infer_document_type(
            Path("docs/prd/product-requirements.md"),
            mock_workflow_info
        )

        assert doc_type == "prd"

    def test_infer_from_path_epic(self, tmp_path, mock_workflow_info):
        """Test document type inferred from path containing 'epic'."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "custom-workflow"
        doc_type = orchestrator._infer_document_type(
            Path("docs/epics/epic-1.md"),
            mock_workflow_info
        )

        assert doc_type == "epic"

    def test_infer_default_for_unknown(self, tmp_path, mock_workflow_info):
        """Test default document type when no pattern matches."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "custom-workflow"
        doc_type = orchestrator._infer_document_type(
            Path("docs/notes/random.md"),
            mock_workflow_info
        )

        assert doc_type == "story"

    def test_workflow_name_takes_precedence_over_path(self, tmp_path, mock_workflow_info):
        """Test workflow name takes precedence over path patterns."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Workflow says "prd" but path says "story"
        mock_workflow_info.name = "prd"
        doc_type = orchestrator._infer_document_type(
            Path("docs/epic-1/story-1.md"),  # Path has "story"
            mock_workflow_info
        )

        # Workflow name should win
        assert doc_type == "prd"

    def test_case_insensitive_matching(self, tmp_path, mock_workflow_info):
        """Test document type inference is case-insensitive."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "PRD"  # Uppercase
        doc_type = orchestrator._infer_document_type(
            Path("DOCS/PRD.MD"),  # Uppercase path
            mock_workflow_info
        )

        assert doc_type == "prd"


class TestGetAgentForWorkflow:
    """Test _get_agent_for_workflow() method (used for author determination)."""

    def test_prd_workflow_returns_john(self, tmp_path, mock_workflow_info):
        """Test PRD workflow maps to John agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "prd"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "John"

    def test_architecture_workflow_returns_winston(self, tmp_path, mock_workflow_info):
        """Test architecture workflow maps to Winston agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "architecture"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Winston"

    def test_story_workflow_returns_bob(self, tmp_path, mock_workflow_info):
        """Test story creation workflow maps to Bob agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "create-story"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Bob"

    def test_implementation_workflow_returns_amelia(self, tmp_path, mock_workflow_info):
        """Test implementation workflow maps to Amelia agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "implement-story"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Amelia"

    def test_test_workflow_returns_murat(self, tmp_path, mock_workflow_info):
        """Test test workflow maps to Murat agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "test"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Murat"

    def test_ux_workflow_returns_sally(self, tmp_path, mock_workflow_info):
        """Test UX workflow maps to Sally agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "ux-design"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Sally"

    def test_research_workflow_returns_mary(self, tmp_path, mock_workflow_info):
        """Test research workflow maps to Mary agent."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "brief"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Mary"

    def test_unknown_workflow_returns_orchestrator(self, tmp_path, mock_workflow_info):
        """Test unknown workflow returns Orchestrator as default."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        mock_workflow_info.name = "unknown-workflow"
        agent = orchestrator._get_agent_for_workflow(mock_workflow_info)

        assert agent == "Orchestrator"


class TestRegisterArtifacts:
    """Test _register_artifacts() method."""

    def test_register_artifacts_success(self, tmp_path, mock_workflow_info):
        """Test successful artifact registration."""
        # Create test file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "PRD.md"
        test_file.write_text("# PRD Content")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager
        mock_doc_manager = MagicMock()
        mock_doc = Mock()
        mock_doc.id = "doc-123"
        mock_doc_manager.register_document.return_value = mock_doc
        orchestrator.doc_lifecycle = mock_doc_manager

        # Register artifacts
        mock_workflow_info.name = "prd"
        artifacts = [Path("docs/PRD.md")]
        variables = {"project_name": "TestProject"}

        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=1,
            story=1,
            variables=variables
        )

        # Verify registration was called
        mock_doc_manager.register_document.assert_called_once()
        call_args = mock_doc_manager.register_document.call_args

        # Verify arguments
        assert call_args.kwargs["path"] == tmp_path / "docs/PRD.md"
        assert call_args.kwargs["doc_type"] == "prd"
        assert call_args.kwargs["author"] == "john"
        assert call_args.kwargs["metadata"]["workflow"] == "prd"
        assert call_args.kwargs["metadata"]["epic"] == 1
        assert call_args.kwargs["metadata"]["story"] == 1
        assert call_args.kwargs["metadata"]["created_by_workflow"] is True
        assert call_args.kwargs["metadata"]["variables"] == variables

    def test_register_multiple_artifacts(self, tmp_path, mock_workflow_info):
        """Test registration of multiple artifacts."""
        # Create test files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# PRD")
        (docs_dir / "Architecture.md").write_text("# Architecture")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager
        mock_doc_manager = MagicMock()
        mock_doc = Mock()
        mock_doc.id = "doc-123"
        mock_doc_manager.register_document.return_value = mock_doc
        orchestrator.doc_lifecycle = mock_doc_manager

        # Register artifacts
        mock_workflow_info.name = "prd"
        artifacts = [Path("docs/PRD.md"), Path("docs/Architecture.md")]
        variables = {"project_name": "TestProject"}

        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=1,
            story=1,
            variables=variables
        )

        # Verify registration was called twice
        assert mock_doc_manager.register_document.call_count == 2

    def test_register_artifacts_no_doc_lifecycle(self, tmp_path, mock_workflow_info):
        """Test registration skipped when DocumentLifecycleManager not available."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Ensure doc_lifecycle is None
        orchestrator.doc_lifecycle = None

        # Register artifacts (should not crash)
        mock_workflow_info.name = "prd"
        artifacts = [Path("docs/PRD.md")]
        variables = {}

        # Should log warning and return without error
        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=1,
            story=1,
            variables=variables
        )

        # No exception should be raised

    def test_register_artifacts_handles_failures_gracefully(self, tmp_path, mock_workflow_info):
        """Test registration continues after failures."""
        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager to raise exception
        mock_doc_manager = MagicMock()
        mock_doc_manager.register_document.side_effect = [
            Exception("Database error"),  # First call fails
            Mock(id="doc-456")            # Second call succeeds
        ]
        orchestrator.doc_lifecycle = mock_doc_manager

        # Register multiple artifacts
        mock_workflow_info.name = "prd"
        artifacts = [Path("docs/PRD.md"), Path("docs/Architecture.md")]
        variables = {}

        # Should not raise exception
        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=1,
            story=1,
            variables=variables
        )

        # Verify both registration attempts were made
        assert mock_doc_manager.register_document.call_count == 2

    def test_metadata_construction(self, tmp_path, mock_workflow_info):
        """Test metadata is constructed correctly."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "PRD.md"
        test_file.write_text("# PRD")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager
        mock_doc_manager = MagicMock()
        mock_doc = Mock()
        mock_doc.id = "doc-123"
        mock_doc_manager.register_document.return_value = mock_doc
        orchestrator.doc_lifecycle = mock_doc_manager

        # Register with specific metadata
        mock_workflow_info.name = "prd"
        mock_workflow_info.phase = "planning"
        artifacts = [Path("docs/PRD.md")]
        variables = {
            "project_name": "TestProject",
            "version": "1.0",
            "custom_field": "custom_value"
        }

        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=5,
            story=3,
            variables=variables
        )

        # Verify metadata structure
        call_args = mock_doc_manager.register_document.call_args
        metadata = call_args.kwargs["metadata"]

        assert metadata["workflow"] == "prd"
        assert metadata["epic"] == 5
        assert metadata["story"] == 3
        assert metadata["phase"] == "planning"
        assert metadata["workflow_phase"] == "planning"
        assert metadata["created_by_workflow"] is True
        assert metadata["variables"] == variables
        assert metadata["variables"]["project_name"] == "TestProject"
        assert metadata["variables"]["version"] == "1.0"
        assert metadata["variables"]["custom_field"] == "custom_value"

    def test_author_determined_correctly(self, tmp_path, mock_workflow_info):
        """Test author is determined from workflow agent."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "story.md"
        test_file.write_text("# Story")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager
        mock_doc_manager = MagicMock()
        mock_doc = Mock()
        mock_doc.id = "doc-123"
        mock_doc_manager.register_document.return_value = mock_doc
        orchestrator.doc_lifecycle = mock_doc_manager

        # Test different workflows and expected authors
        test_cases = [
            ("prd", "john"),
            ("architecture", "winston"),
            ("create-story", "bob"),
            ("implement-story", "amelia"),
            ("test", "murat"),
            ("ux-design", "sally"),
            ("brief", "mary"),
        ]

        for workflow_name, expected_author in test_cases:
            mock_workflow_info.name = workflow_name
            artifacts = [Path("docs/story.md")]

            orchestrator._register_artifacts(
                artifacts=artifacts,
                workflow_info=mock_workflow_info,
                epic=1,
                story=1,
                variables={}
            )

            # Verify author was set correctly
            call_args = mock_doc_manager.register_document.call_args
            assert call_args.kwargs["author"] == expected_author

            # Reset mock for next iteration
            mock_doc_manager.reset_mock()

    def test_relative_path_converted_to_absolute(self, tmp_path, mock_workflow_info):
        """Test relative artifact paths are converted to absolute paths."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "PRD.md"
        test_file.write_text("# PRD")

        orchestrator = GAODevOrchestrator(
            project_root=tmp_path,
            mode="benchmark"
        )

        # Mock the document lifecycle manager
        mock_doc_manager = MagicMock()
        mock_doc = Mock()
        mock_doc.id = "doc-123"
        mock_doc_manager.register_document.return_value = mock_doc
        orchestrator.doc_lifecycle = mock_doc_manager

        # Register with relative path
        mock_workflow_info.name = "prd"
        artifacts = [Path("docs/PRD.md")]  # Relative path

        orchestrator._register_artifacts(
            artifacts=artifacts,
            workflow_info=mock_workflow_info,
            epic=1,
            story=1,
            variables={}
        )

        # Verify absolute path was used
        call_args = mock_doc_manager.register_document.call_args
        registered_path = call_args.kwargs["path"]

        # Should be absolute path
        assert registered_path == tmp_path / "docs/PRD.md"
        assert registered_path.is_absolute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
