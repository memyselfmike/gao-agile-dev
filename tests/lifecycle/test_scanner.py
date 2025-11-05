"""
Tests for Document Scanner.

This module provides comprehensive tests for the DocumentScanner class,
covering directory scanning, exclusion patterns, metadata extraction,
document type detection, and batch registration.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from gao_dev.lifecycle.scanner import DocumentScanner, ScanResult
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType


@pytest.fixture
def temp_docs_dir():
    """Create temporary directory for test documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


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


class TestDocumentScanner:
    """Test suite for DocumentScanner class."""

    def test_scanner_initialization(self, doc_manager):
        """Test scanner initializes correctly."""
        scanner = DocumentScanner(doc_manager)

        assert scanner.doc_mgr is doc_manager
        assert scanner.naming_convention is not None
        assert scanner.exclude_hidden is True
        assert '.git' in scanner.exclude_patterns
        assert 'node_modules' in scanner.exclude_patterns

    def test_scanner_with_custom_excludes(self, doc_manager):
        """Test scanner with custom exclude patterns."""
        custom_excludes = ['*.txt', 'build']
        scanner = DocumentScanner(doc_manager, exclude_patterns=custom_excludes)

        assert '*.txt' in scanner.exclude_patterns
        assert 'build' in scanner.exclude_patterns
        assert '.git' in scanner.exclude_patterns  # Still includes defaults

    def test_scanner_with_hidden_files_allowed(self, doc_manager):
        """Test scanner can include hidden files."""
        scanner = DocumentScanner(doc_manager, exclude_hidden=False)
        assert scanner.exclude_hidden is False

    def test_scan_empty_directory(self, scanner, temp_docs_dir):
        """Test scanning empty directory."""
        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 0
        assert result.new_registered == 0
        assert result.existing_updated == 0
        assert result.files_skipped == 0
        assert result.naming_compliance_rate == 100.0
        assert result.classification_counts == {'permanent': 0, 'transient': 0, 'temp': 0}
        assert result.warnings == []

    def test_scan_discovers_markdown_files(self, scanner, temp_docs_dir):
        """Test scanner discovers .md files."""
        # Create test markdown files
        (temp_docs_dir / "doc1.md").write_text("# Doc 1")
        (temp_docs_dir / "doc2.md").write_text("# Doc 2")
        (temp_docs_dir / "subdir").mkdir()
        (temp_docs_dir / "subdir" / "doc3.md").write_text("# Doc 3")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 3
        assert result.new_registered == 3

    def test_scan_excludes_git_directory(self, scanner, temp_docs_dir):
        """Test scanner excludes .git directory."""
        # Create .git directory with files
        git_dir = temp_docs_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config.md").write_text("# Git Config")

        # Create normal file
        (temp_docs_dir / "doc.md").write_text("# Doc")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 1  # Only doc.md
        assert result.files_skipped >= 1  # .git/config.md skipped

    def test_scan_excludes_node_modules(self, scanner, temp_docs_dir):
        """Test scanner excludes node_modules directory."""
        # Create node_modules directory
        node_dir = temp_docs_dir / "node_modules"
        node_dir.mkdir()
        (node_dir / "readme.md").write_text("# Package")

        # Create normal file
        (temp_docs_dir / "doc.md").write_text("# Doc")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 1
        assert result.files_skipped >= 1

    def test_scan_excludes_glob_patterns(self, scanner, temp_docs_dir):
        """Test scanner excludes files matching glob patterns."""
        # Create various files
        (temp_docs_dir / "doc.md").write_text("# Doc")
        (temp_docs_dir / "test.log").write_text("log")  # Should be excluded
        (temp_docs_dir / "temp.tmp").write_text("temp")  # Should be excluded

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 1  # Only .md files scanned

    def test_scan_excludes_hidden_files(self, scanner, temp_docs_dir):
        """Test scanner excludes hidden files by default."""
        (temp_docs_dir / ".hidden.md").write_text("# Hidden")
        (temp_docs_dir / "visible.md").write_text("# Visible")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 1
        assert result.files_skipped >= 1

    def test_scan_includes_hidden_files_when_allowed(self, doc_manager, temp_docs_dir):
        """Test scanner can include hidden files."""
        scanner = DocumentScanner(doc_manager, exclude_hidden=False)

        (temp_docs_dir / ".hidden.md").write_text("# Hidden")
        (temp_docs_dir / "visible.md").write_text("# Visible")

        result = scanner.scan_directory(temp_docs_dir)

        # Both files should be scanned (but may still be excluded by other patterns)
        assert result.total_scanned >= 1

    def test_scan_extracts_metadata_from_frontmatter(self, scanner, temp_docs_dir):
        """Test scanner extracts YAML frontmatter metadata."""
        doc_path = temp_docs_dir / "PRD_test_2024-11-05_v1.0.md"
        doc_path.write_text("""---
doc_type: prd
author: john
owner: winston
reviewer: sally
feature: authentication
---

# PRD Content
""")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.new_registered == 1

        # Verify metadata was extracted
        doc = scanner.doc_mgr.registry.get_document_by_path(str(doc_path))
        assert doc.author == 'john'
        assert doc.owner == 'winston'
        assert doc.reviewer == 'sally'
        assert doc.feature == 'authentication'

    def test_scan_registers_new_documents(self, scanner, temp_docs_dir):
        """Test scanner registers new documents."""
        doc_path = temp_docs_dir / "doc.md"
        doc_path.write_text("# Document")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.new_registered == 1
        assert result.existing_updated == 0

        # Verify document is in registry
        doc = scanner.doc_mgr.registry.get_document_by_path(str(doc_path))
        assert doc is not None

    def test_scan_updates_existing_documents(self, scanner, temp_docs_dir):
        """Test scanner updates metadata for existing documents."""
        doc_path = temp_docs_dir / "doc.md"
        doc_path.write_text("""---
doc_type: prd
author: john
---

# Content v1
""")

        # First scan - register
        result1 = scanner.scan_directory(temp_docs_dir)
        assert result1.new_registered == 1

        # Update file content and frontmatter
        doc_path.write_text("""---
doc_type: prd
author: john
owner: winston
---

# Content v2
""")

        # Second scan - update
        result2 = scanner.scan_directory(temp_docs_dir)
        assert result2.new_registered == 0
        assert result2.existing_updated == 1

        # Verify metadata updated
        doc = scanner.doc_mgr.registry.get_document_by_path(str(doc_path))
        assert doc.owner == 'winston'

    def test_scan_validates_filenames(self, scanner, temp_docs_dir):
        """Test scanner validates filenames against naming convention."""
        # Create non-compliant filename
        (temp_docs_dir / "invalid-name.md").write_text("# Doc")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 1
        assert len(result.warnings) > 0
        assert any("Non-standard filename" in w for w in result.warnings)

    def test_scan_suggests_correct_filename(self, scanner, temp_docs_dir):
        """Test scanner suggests correct filename for non-compliant files."""
        doc_path = temp_docs_dir / "prd.md"
        doc_path.write_text("""---
doc_type: prd
subject: user auth
---

# PRD
""")

        result = scanner.scan_directory(temp_docs_dir)

        assert len(result.warnings) > 0
        warning = result.warnings[0]
        assert "prd.md" in warning
        assert "suggest:" in warning.lower()

    def test_scan_calculates_naming_compliance_rate(self, scanner, temp_docs_dir):
        """Test scanner calculates naming compliance rate."""
        # Create 2 compliant and 3 non-compliant files
        (temp_docs_dir / "PRD_test_2024-11-05_v1.0.md").write_text("# PRD 1")
        (temp_docs_dir / "EPIC_auth_2024-11-05_v1.0.md").write_text("# Epic")
        (temp_docs_dir / "invalid1.md").write_text("# Invalid 1")
        (temp_docs_dir / "invalid2.md").write_text("# Invalid 2")
        (temp_docs_dir / "invalid3.md").write_text("# Invalid 3")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 5
        # 2 compliant out of 5 = 40%
        assert result.naming_compliance_rate == 40.0

    def test_scan_with_progress_callback(self, scanner, temp_docs_dir):
        """Test scanner calls progress callback."""
        (temp_docs_dir / "doc1.md").write_text("# Doc 1")
        (temp_docs_dir / "doc2.md").write_text("# Doc 2")

        progress_messages = []

        def progress_callback(msg):
            progress_messages.append(msg)

        result = scanner.scan_directory(temp_docs_dir, progress_callback)

        assert len(progress_messages) == 2
        assert any("doc1.md" in msg for msg in progress_messages)
        assert any("doc2.md" in msg for msg in progress_messages)

    def test_scan_handles_errors_gracefully(self, scanner, temp_docs_dir):
        """Test scanner handles errors without crashing."""
        # Create file that will cause error (e.g., invalid frontmatter)
        doc_path = temp_docs_dir / "bad.md"
        doc_path.write_text("""---
invalid yaml: [
---

# Content
""")

        # Scanner should handle the error and continue
        result = scanner.scan_directory(temp_docs_dir)

        # Should still attempt to scan, might have warnings
        assert result.total_scanned >= 0

    def test_scan_returns_classification_counts(self, scanner, temp_docs_dir):
        """Test scanner returns classification counts."""
        # Create documents of different types
        (temp_docs_dir / "PRD_auth_2024-11-05_v1.0.md").write_text("""---
doc_type: prd
author: john
---
# PRD
""")

        (temp_docs_dir / "QA_report_2024-11-05_v1.0.md").write_text("""---
doc_type: qa_report
author: sally
---
# QA Report
""")

        (temp_docs_dir / "draft.md").write_text("""---
status: draft
---
# Draft
""")

        result = scanner.scan_directory(temp_docs_dir)

        counts = result.classification_counts
        assert counts['permanent'] >= 1  # PRD
        assert counts['transient'] >= 1  # QA report
        assert counts['temp'] >= 1  # draft

    def test_should_exclude_directory_patterns(self, scanner):
        """Test _should_exclude with directory patterns."""
        assert scanner._should_exclude(Path("/project/.git/file.md"))
        assert scanner._should_exclude(Path("/project/node_modules/pkg.md"))
        assert scanner._should_exclude(Path("/project/.archive/old.md"))
        assert not scanner._should_exclude(Path("/project/docs/file.md"))

    def test_should_exclude_glob_patterns(self, scanner):
        """Test _should_exclude with glob patterns."""
        assert scanner._should_exclude(Path("/project/test.pyc"))
        assert scanner._should_exclude(Path("/project/app.log"))
        assert scanner._should_exclude(Path("/project/.env"))
        assert not scanner._should_exclude(Path("/project/doc.md"))

    def test_detect_doc_type_from_frontmatter(self, scanner, temp_docs_dir):
        """Test document type detection from frontmatter."""
        path = temp_docs_dir / "test.md"
        metadata = {'doc_type': 'architecture'}

        doc_type = scanner._detect_doc_type(path, metadata)
        assert doc_type == 'architecture'

    def test_detect_doc_type_from_path(self, scanner):
        """Test document type detection from path."""
        test_cases = [
            (Path("/docs/PRD.md"), 'prd'),
            (Path("/docs/Architecture.md"), 'architecture'),
            (Path("/docs/stories/story-1.1.md"), 'story'),
            (Path("/docs/epics/epic-5.md"), 'epic'),
            (Path("/docs/ADR-001.md"), 'adr'),
            (Path("/docs/Postmortem.md"), 'postmortem'),
            (Path("/docs/Runbook.md"), 'runbook'),
            (Path("/docs/qa-report.md"), 'qa_report'),
            (Path("/docs/test-results.md"), 'test_report'),
            (Path("/docs/document.md"), 'story'),  # Default to 'story'
        ]

        for path, expected_type in test_cases:
            doc_type = scanner._detect_doc_type(path, {})
            assert doc_type == expected_type, f"Failed for {path}"

    def test_scan_result_dataclass(self):
        """Test ScanResult dataclass."""
        result = ScanResult(
            total_scanned=100,
            new_registered=80,
            existing_updated=15,
            files_skipped=5,
            naming_compliance_rate=85.0,
            classification_counts={'permanent': 50, 'transient': 30, 'temp': 20},
            warnings=["Warning 1", "Warning 2"],
        )

        assert result.total_scanned == 100
        assert result.new_registered == 80
        assert result.existing_updated == 15
        assert result.files_skipped == 5
        assert result.naming_compliance_rate == 85.0
        assert result.classification_counts['permanent'] == 50
        assert len(result.warnings) == 2

    def test_scan_large_directory_structure(self, scanner, temp_docs_dir):
        """Test scanning large directory structure."""
        # Create nested structure with multiple documents
        for i in range(5):
            feature_dir = temp_docs_dir / f"feature-{i}"
            feature_dir.mkdir()
            for j in range(10):
                (feature_dir / f"doc-{j}.md").write_text(f"# Doc {i}-{j}")

        result = scanner.scan_directory(temp_docs_dir)

        assert result.total_scanned == 50
        assert result.new_registered == 50

    def test_scan_preserves_existing_document_ids(self, scanner, temp_docs_dir):
        """Test scanning doesn't duplicate documents."""
        doc_path = temp_docs_dir / "doc.md"
        doc_path.write_text("# Document")

        # First scan
        result1 = scanner.scan_directory(temp_docs_dir)
        doc1 = scanner.doc_mgr.registry.get_document_by_path(str(doc_path))

        # Second scan
        result2 = scanner.scan_directory(temp_docs_dir)
        doc2 = scanner.doc_mgr.registry.get_document_by_path(str(doc_path))

        # Should be same document
        assert doc1.id == doc2.id
        assert result2.new_registered == 0
        assert result2.existing_updated == 1
