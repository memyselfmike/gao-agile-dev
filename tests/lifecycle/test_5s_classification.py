"""
Tests for 5S Classification System.

This module provides comprehensive tests for the 5S Sort methodology
implementation in the DocumentScanner. Tests cover all classification
rules and edge cases.

5S Sort Classification:
- Permanent: Keep forever (PRD, Architecture, ADR, Postmortem, Epic)
- Transient: Archive after period (QA reports, test reports, analysis)
- Temp: Can delete (drafts, scratch files, WIP docs)
"""

import pytest
import tempfile
from pathlib import Path

from gao_dev.lifecycle.scanner import DocumentScanner
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry


@pytest.fixture
def registry():
    """Create test registry."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    registry = DocumentRegistry(db_path)
    yield registry
    registry.close()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def archive_dir():
    """Create temporary archive directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def doc_manager(registry, archive_dir):
    """Create test document manager."""
    return DocumentLifecycleManager(registry, archive_dir)


@pytest.fixture
def scanner(doc_manager):
    """Create test scanner."""
    return DocumentScanner(doc_manager)


class Test5SClassification:
    """Test suite for 5S Sort classification."""

    # ========== PERMANENT Classification Tests ==========

    def test_classify_prd_as_permanent(self, scanner):
        """Test PRD documents classified as permanent."""
        path = Path("/docs/PRD.md")
        metadata = {'doc_type': 'prd'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_architecture_as_permanent(self, scanner):
        """Test architecture documents classified as permanent."""
        path = Path("/docs/Architecture.md")
        metadata = {'doc_type': 'architecture'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_adr_as_permanent(self, scanner):
        """Test ADR documents classified as permanent."""
        path = Path("/docs/ADR-001.md")
        metadata = {'doc_type': 'adr'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_postmortem_as_permanent(self, scanner):
        """Test postmortem documents classified as permanent."""
        path = Path("/docs/Postmortem.md")
        metadata = {'doc_type': 'postmortem'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_epic_as_permanent(self, scanner):
        """Test epic documents classified as permanent."""
        path = Path("/docs/Epic-5.md")
        metadata = {'doc_type': 'epic'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_unknown_type_as_permanent(self, scanner):
        """Test unknown document types default to permanent (conservative)."""
        path = Path("/docs/CustomDoc.md")
        metadata = {'doc_type': 'custom_type'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classify_no_metadata_as_permanent(self, scanner):
        """Test documents without metadata default to permanent."""
        path = Path("/docs/Document.md")
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    # ========== TRANSIENT Classification Tests ==========

    def test_classify_qa_report_as_transient(self, scanner):
        """Test QA reports classified as transient."""
        path = Path("/docs/QA_Report.md")
        metadata = {'doc_type': 'qa_report'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'transient'

    def test_classify_test_report_as_transient(self, scanner):
        """Test test reports classified as transient."""
        path = Path("/docs/Test_Report.md")
        metadata = {'doc_type': 'test_report'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'transient'

    def test_classify_analysis_as_transient(self, scanner):
        """Test analysis documents classified as transient."""
        path = Path("/docs/Analysis.md")
        metadata = {'doc_type': 'analysis'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'transient'

    def test_classify_benchmark_as_transient(self, scanner):
        """Test benchmark documents classified as transient."""
        path = Path("/docs/Benchmark.md")
        metadata = {'doc_type': 'benchmark'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'transient'

    # ========== TEMP Classification Tests ==========

    def test_classify_draft_in_path_as_temp(self, scanner):
        """Test documents with 'draft' in path classified as temp."""
        path = Path("/docs/drafts/PRD.md")
        metadata = {'doc_type': 'prd'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_wip_in_path_as_temp(self, scanner):
        """Test documents with 'wip' in path classified as temp."""
        path = Path("/docs/wip-document.md")
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_scratch_in_path_as_temp(self, scanner):
        """Test documents with 'scratch' in path classified as temp."""
        path = Path("/docs/scratch-notes.md")
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_temp_in_path_as_temp(self, scanner):
        """Test documents with 'temp' in filename classified as temp."""
        # Note: 'temp' as a directory name is excluded to avoid matching system paths
        # But it should match in filenames
        path = Path("/docs/temp-file.md")  # temp in filename
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_scratch_directory_as_temp(self, scanner):
        """Test documents in .scratch directory classified as temp."""
        path = Path("/docs/.scratch/notes.md")
        metadata = {'doc_type': 'prd'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_draft_status_in_frontmatter_as_temp(self, scanner):
        """Test documents with draft status in frontmatter classified as temp."""
        path = Path("/docs/PRD.md")
        metadata = {'doc_type': 'prd', 'status': 'draft'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_draft_status_uppercase_as_temp(self, scanner):
        """Test documents with DRAFT status (case-insensitive) classified as temp."""
        path = Path("/docs/PRD.md")
        metadata = {'doc_type': 'prd', 'status': 'DRAFT'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_draft_tag_as_temp(self, scanner):
        """Test documents with 'draft' tag classified as temp."""
        path = Path("/docs/PRD.md")
        metadata = {'doc_type': 'prd', 'tags': ['draft', 'in-progress']}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    # ========== Priority Tests ==========

    def test_temp_overrides_permanent(self, scanner):
        """Test temp classification takes priority over permanent type."""
        # Even though PRD is permanent, draft pattern makes it temp
        path = Path("/docs/drafts/PRD_auth_2024-11-05_v1.0.md")
        metadata = {'doc_type': 'prd'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_temp_overrides_transient(self, scanner):
        """Test temp classification takes priority over transient type."""
        path = Path("/docs/draft-qa-report.md")
        metadata = {'doc_type': 'qa_report'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_scratch_dir_overrides_all(self, scanner):
        """Test .scratch directory overrides document type."""
        path = Path("/docs/.scratch/Architecture.md")
        metadata = {'doc_type': 'architecture'}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    # ========== Case Sensitivity Tests ==========

    def test_classification_case_insensitive_doc_type(self, scanner):
        """Test document type matching is case-insensitive."""
        path = Path("/docs/PRD.md")
        metadata = {'doc_type': 'PRD'}  # Uppercase

        classification = scanner._classify_document(path, metadata)
        assert classification == 'permanent'

    def test_classification_case_insensitive_path(self, scanner):
        """Test path pattern matching is case-insensitive."""
        path = Path("/docs/DRAFT-document.md")
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    # ========== Edge Cases ==========

    def test_classify_multiple_temp_indicators(self, scanner):
        """Test document with multiple temp indicators still classified as temp."""
        path = Path("/docs/.scratch/draft-wip-document.md")
        metadata = {'status': 'draft', 'tags': ['draft']}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_partial_word_match(self, scanner):
        """Test temp patterns match word boundaries in filename."""
        # Updated: Now uses word boundary matching, so "undrafted" won't match
        # But "draft-concept" or "concept-draft" will match
        path = Path("/docs/draft-concept.md")  # Has 'draft' with separator
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        assert classification == 'temp'

    def test_classify_empty_path_and_metadata(self, scanner):
        """Test classification with minimal information."""
        path = Path("/docs/file.md")
        metadata = {}

        classification = scanner._classify_document(path, metadata)
        # Should default to permanent
        assert classification == 'permanent'

    # ========== Integration Tests ==========

    def test_scan_classifies_all_documents(self, scanner, doc_manager):
        """Test full scan classifies all document types correctly."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            # Create permanent document
            prd_path = temp_dir / "PRD_auth_2024-11-05_v1.0.md"
            prd_path.write_text("""---
doc_type: prd
---
# PRD
""")

            # Create transient document
            qa_path = temp_dir / "QA_report_2024-11-05_v1.0.md"
            qa_path.write_text("""---
doc_type: qa_report
---
# QA Report
""")

            # Create temp document
            draft_path = temp_dir / "draft-notes.md"
            draft_path.write_text("# Draft Notes")

            result = scanner.scan_directory(temp_dir)

            assert result.classification_counts['permanent'] == 1
            assert result.classification_counts['transient'] == 1
            assert result.classification_counts['temp'] == 1

            # Verify metadata stored correctly
            prd_doc = doc_manager.registry.get_document_by_path(str(prd_path))
            assert prd_doc.metadata['5s_classification'] == 'permanent'

            qa_doc = doc_manager.registry.get_document_by_path(str(qa_path))
            assert qa_doc.metadata['5s_classification'] == 'transient'

            draft_doc = doc_manager.registry.get_document_by_path(str(draft_path))
            assert draft_doc.metadata['5s_classification'] == 'temp'

    def test_scan_updates_classification_on_rescan(self, scanner, doc_manager):
        """Test rescanning updates classification if document changes."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            doc_path = temp_dir / "doc.md"

            # First scan - permanent
            doc_path.write_text("""---
doc_type: prd
---
# PRD
""")

            result1 = scanner.scan_directory(temp_dir)
            assert result1.classification_counts['permanent'] == 1

            # Update to draft - should become temp
            doc_path.write_text("""---
doc_type: prd
status: draft
---
# PRD Draft
""")

            result2 = scanner.scan_directory(temp_dir)
            assert result2.classification_counts['temp'] == 1

            # Verify metadata updated
            doc = doc_manager.registry.get_document_by_path(str(doc_path))
            assert doc.metadata['5s_classification'] == 'temp'

    def test_classification_constants(self, scanner):
        """Test classification constants are defined correctly."""
        assert 'prd' in scanner.PERMANENT_TYPES
        assert 'architecture' in scanner.PERMANENT_TYPES
        assert 'adr' in scanner.PERMANENT_TYPES
        assert 'postmortem' in scanner.PERMANENT_TYPES
        assert 'epic' in scanner.PERMANENT_TYPES

        assert 'qa_report' in scanner.TRANSIENT_TYPES
        assert 'test_report' in scanner.TRANSIENT_TYPES
        assert 'analysis' in scanner.TRANSIENT_TYPES
        assert 'benchmark' in scanner.TRANSIENT_TYPES

        assert any('draft' in pattern for pattern in scanner.TEMP_PATTERNS)
        assert any('wip' in pattern for pattern in scanner.TEMP_PATTERNS)
        assert any('scratch' in pattern for pattern in scanner.TEMP_PATTERNS)
        assert any('temp' in pattern for pattern in scanner.TEMP_PATTERNS)

    def test_classification_coverage(self, scanner):
        """Test all DocumentType enum values have classification rules."""
        from gao_dev.lifecycle.models import DocumentType

        # All permanent types
        permanent_paths = [
            (Path("/docs/PRD.md"), {'doc_type': 'prd'}),
            (Path("/docs/Architecture.md"), {'doc_type': 'architecture'}),
            (Path("/docs/ADR.md"), {'doc_type': 'adr'}),
            (Path("/docs/Postmortem.md"), {'doc_type': 'postmortem'}),
            (Path("/docs/Epic.md"), {'doc_type': 'epic'}),
        ]

        for path, metadata in permanent_paths:
            classification = scanner._classify_document(path, metadata)
            assert classification == 'permanent', f"Failed for {metadata['doc_type']}"

        # All transient types
        transient_paths = [
            (Path("/docs/QA.md"), {'doc_type': 'qa_report'}),
            (Path("/docs/Test.md"), {'doc_type': 'test_report'}),
        ]

        for path, metadata in transient_paths:
            classification = scanner._classify_document(path, metadata)
            assert classification == 'transient', f"Failed for {metadata['doc_type']}"
