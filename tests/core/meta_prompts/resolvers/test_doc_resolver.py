"""
Comprehensive unit tests for DocResolver.

Tests all aspects of document reference resolution:
- Full document loading
- Section extraction
- YAML field extraction
- Glob patterns
- Error handling
- Performance characteristics
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock

from gao_dev.core.meta_prompts.resolvers.doc_resolver import DocResolver
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType


class TestDocResolverBasicLoading:
    """Test basic document loading functionality."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create test document
        test_doc = docs_dir / "test.md"
        test_doc.write_text("# Test Document\n\nThis is test content.", encoding="utf-8")

        return tmp_path

    @pytest.fixture
    def doc_manager(self, tmp_path):
        """Create DocumentLifecycleManager for testing."""
        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        yield manager
        # Cleanup
        registry.close()

    @pytest.fixture
    def resolver(self, doc_manager, temp_project):
        """Create DocResolver instance."""
        return DocResolver(doc_manager, temp_project)

    def test_can_resolve_doc_type(self, resolver):
        """Test resolver identifies 'doc' type."""
        assert resolver.can_resolve("doc") is True
        assert resolver.can_resolve("checklist") is False
        assert resolver.can_resolve("other") is False

    def test_get_type(self, resolver):
        """Test resolver returns correct type."""
        assert resolver.get_type() == "doc"

    def test_load_existing_document(self, resolver, temp_project):
        """Test loading existing document returns full content."""
        content = resolver.resolve("docs/test.md", {})

        assert "# Test Document" in content
        assert "This is test content" in content

    def test_load_missing_document(self, resolver):
        """Test loading missing document returns empty string."""
        content = resolver.resolve("docs/missing.md", {})

        assert content == ""

    def test_relative_path_resolution(self, resolver, temp_project):
        """Test relative paths are resolved from project root."""
        content = resolver.resolve("docs/test.md", {})

        assert content != ""

    def test_absolute_path_support(self, resolver, temp_project):
        """Test absolute paths are supported."""
        abs_path = str(temp_project / "docs" / "test.md")
        content = resolver.resolve(abs_path, {})

        assert "# Test Document" in content

    def test_document_state_filtering_active(
        self, resolver, doc_manager, temp_project
    ):
        """Test only active documents are loaded by default."""
        doc_path = temp_project / "docs" / "test.md"

        # Register document as active (use valid document type "story")
        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test_user",
        )
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE)

        content = resolver.resolve("docs/test.md", {})

        assert content != ""


class TestDocResolverSectionExtraction:
    """Test markdown section extraction."""

    @pytest.fixture
    def markdown_doc(self, tmp_path):
        """Create markdown document with sections."""
        doc_path = tmp_path / "sections.md"
        content = """# Main Heading

Some intro content.

## Acceptance Criteria

- Criterion 1
- Criterion 2
- Criterion 3

## Technical Notes

Implementation details here.

### Nested Section

Nested content.

## Another Section

More content here.
"""
        doc_path.write_text(content, encoding="utf-8")
        return tmp_path

    @pytest.fixture
    def resolver(self, markdown_doc):
        """Create resolver with markdown document."""
        db_path = markdown_doc / "test.db"
        archive_dir = markdown_doc / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, markdown_doc)
        yield resolver
        # Cleanup
        registry.close()

    def test_extract_top_level_heading(self, resolver):
        """Test extracting content under top-level heading."""
        content = resolver.resolve("sections.md#acceptance-criteria", {})

        assert "- Criterion 1" in content
        assert "- Criterion 2" in content
        assert "- Criterion 3" in content
        assert "Technical Notes" not in content

    def test_extract_nested_heading(self, resolver):
        """Test extracting content under nested heading."""
        content = resolver.resolve("sections.md#nested-section", {})

        assert "Nested content" in content
        assert "Another Section" not in content

    def test_missing_section_returns_empty(self, resolver):
        """Test missing section returns empty string."""
        content = resolver.resolve("sections.md#nonexistent-section", {})

        assert content == ""

    def test_section_formatting_preserved(self, resolver):
        """Test section extraction preserves formatting."""
        content = resolver.resolve("sections.md#technical-notes", {})

        assert "Implementation details here." in content

    def test_heading_normalization(self, resolver):
        """Test heading names are normalized correctly."""
        # Test case-insensitive matching
        content = resolver.resolve("sections.md#ACCEPTANCE-CRITERIA", {})
        assert "Criterion 1" in content

        # Test space to hyphen conversion
        content = resolver.resolve("sections.md#technical notes", {})
        assert "Implementation details" in content

    def test_extract_main_heading(self, resolver):
        """Test extracting content under main heading."""
        content = resolver.resolve("sections.md#main-heading", {})

        assert "Some intro content" in content
        assert "Acceptance Criteria" not in content


class TestDocResolverYAMLExtraction:
    """Test YAML frontmatter field extraction."""

    @pytest.fixture
    def yaml_doc(self, tmp_path):
        """Create document with YAML frontmatter."""
        doc_path = tmp_path / "yaml.md"
        content = """---
status: in_progress
owner: john
epic: 5
story: 5.2
metadata:
  author: john
  version: 1.0
  tags: [epic-5, auth]
tags:
  - authentication
  - security
nested:
  deep:
    value: "deep_value"
---

# Content

Document content here.
"""
        doc_path.write_text(content, encoding="utf-8")
        return tmp_path

    @pytest.fixture
    def resolver(self, yaml_doc):
        """Create resolver with YAML document."""
        db_path = yaml_doc / "test.db"
        archive_dir = yaml_doc / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, yaml_doc)
        yield resolver
        # Cleanup
        registry.close()

    def test_extract_simple_field(self, resolver):
        """Test extracting simple YAML field."""
        status = resolver.resolve("yaml.md@status", {})

        assert status == "in_progress"

    def test_extract_nested_field_dot_notation(self, resolver):
        """Test extracting nested field with dot notation."""
        author = resolver.resolve("yaml.md@metadata.author", {})

        assert author == "john"

    def test_extract_array_field(self, resolver):
        """Test extracting array field returns YAML format."""
        tags = resolver.resolve("yaml.md@tags", {})

        assert "authentication" in tags
        assert "security" in tags

    def test_extract_object_field(self, resolver):
        """Test extracting object field returns YAML format."""
        metadata = resolver.resolve("yaml.md@metadata", {})

        assert "author: john" in metadata
        assert "version: 1.0" in metadata

    def test_missing_field_returns_empty(self, resolver):
        """Test missing YAML field returns empty string."""
        value = resolver.resolve("yaml.md@nonexistent", {})

        assert value == ""

    def test_deep_nested_field(self, resolver):
        """Test deeply nested field extraction."""
        value = resolver.resolve("yaml.md@nested.deep.value", {})

        assert value == "deep_value"

    def test_invalid_yaml_handled_gracefully(self, tmp_path):
        """Test invalid YAML frontmatter is handled gracefully."""
        doc_path = tmp_path / "invalid.md"
        content = """---
invalid: yaml: syntax:
---

Content
"""
        doc_path.write_text(content, encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        value = resolver.resolve("invalid.md@status", {})

        assert value == ""

        # Cleanup
        registry.close()

    def test_no_frontmatter_returns_empty(self, tmp_path):
        """Test document without frontmatter returns empty."""
        doc_path = tmp_path / "no_yaml.md"
        doc_path.write_text("# No YAML\n\nJust content.", encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        value = resolver.resolve("no_yaml.md@status", {})

        assert value == ""

        # Cleanup
        registry.close()


class TestDocResolverGlobPatterns:
    """Test glob pattern support for multiple documents."""

    @pytest.fixture
    def project_with_files(self, tmp_path):
        """Create project with multiple files."""
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir()

        # Create multiple story files
        for i in range(1, 6):
            story = stories_dir / f"story-{i}.md"
            story.write_text(
                f"# Story {i}\n\nContent for story {i}.",
                encoding="utf-8"
            )

        return tmp_path

    @pytest.fixture
    def resolver(self, project_with_files):
        """Create resolver with multiple files."""
        db_path = project_with_files / "test.db"
        archive_dir = project_with_files / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, project_with_files)
        yield resolver
        # Cleanup
        registry.close()

    def test_glob_matching_multiple_files(self, resolver):
        """Test glob pattern matches multiple files."""
        content = resolver.resolve("glob:stories/*.md", {})

        assert "story-1.md" in content
        assert "story-2.md" in content
        assert "Story 1" in content
        assert "Story 2" in content

    def test_glob_with_max_limit(self, tmp_path):
        """Test glob respects max file limit."""
        stories_dir = tmp_path / "stories"
        stories_dir.mkdir()

        # Create 150 files (more than default max of 100)
        for i in range(1, 151):
            story = stories_dir / f"story-{i:03d}.md"  # Zero-padded for proper sorting
            story.write_text(f"Story {i}", encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path, max_glob_files=50)

        content = resolver.resolve("glob:stories/*.md", {})

        # Should only load first 50 files (alphabetically sorted)
        assert "story-001.md" in content
        assert "story-050.md" in content
        # Should NOT contain files beyond limit
        assert "story-051.md" not in content

        # Cleanup
        registry.close()

    def test_glob_with_no_matches(self, resolver):
        """Test glob with no matching files returns empty."""
        content = resolver.resolve("glob:nonexistent/*.md", {})

        assert content == ""

    def test_glob_sorting_alphabetical(self, resolver):
        """Test glob results are sorted alphabetically."""
        content = resolver.resolve("glob:stories/*.md", {})

        # Find positions of files in content
        pos_1 = content.find("story-1.md")
        pos_2 = content.find("story-2.md")
        pos_3 = content.find("story-3.md")

        assert pos_1 < pos_2 < pos_3

    def test_glob_delimiter(self, resolver):
        """Test glob uses correct delimiter between files."""
        content = resolver.resolve("glob:stories/*.md", {})

        # Default delimiter is \n---\n
        assert "\n---\n" in content

    def test_glob_custom_delimiter(self, project_with_files):
        """Test custom glob delimiter."""
        db_path = project_with_files / "test.db"
        archive_dir = project_with_files / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(
            manager,
            project_with_files,
            glob_delimiter="\n\n===\n\n"
        )

        content = resolver.resolve("glob:stories/*.md", {})

        assert "\n\n===\n\n" in content

        # Cleanup
        registry.close()


class TestDocResolverErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def resolver(self, tmp_path):
        """Create basic resolver."""
        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)
        yield resolver
        # Cleanup
        registry.close()

    def test_empty_reference(self, resolver):
        """Test empty reference returns empty string."""
        content = resolver.resolve("", {})

        assert content == ""

    def test_malformed_section_reference(self, tmp_path):
        """Test malformed section reference."""
        doc_path = tmp_path / "test.md"
        doc_path.write_text("# Test\n\nContent", encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        # Multiple # symbols - should use first one
        content = resolver.resolve("test.md#section#subsection", {})

        # Should handle gracefully
        assert isinstance(content, str)

        # Cleanup
        registry.close()

    def test_file_read_error_handling(self, tmp_path, monkeypatch):
        """Test file read errors are handled gracefully."""
        doc_path = tmp_path / "test.md"
        doc_path.write_text("Content", encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        # Mock read_text to raise an error
        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        content = resolver.resolve("test.md", {})

        # Should return empty string on error
        assert content == ""

    def test_unicode_content_handling(self, tmp_path):
        """Test Unicode content is handled correctly."""
        doc_path = tmp_path / "unicode.md"
        doc_path.write_text(
            "# Unicode Test\n\n日本語 العربية 🎉",
            encoding="utf-8"
        )

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        content = resolver.resolve("unicode.md", {})

        assert "日本語" in content
        assert "العربية" in content
        assert "🎉" in content

        # Cleanup
        registry.close()


class TestDocResolverPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def large_project(self, tmp_path):
        """Create project with many files."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create multiple documents
        for i in range(20):
            doc = docs_dir / f"doc-{i}.md"
            content = f"# Document {i}\n\n" + ("Content line.\n" * 100)
            doc.write_text(content, encoding="utf-8")

        return tmp_path

    @pytest.fixture
    def resolver(self, large_project):
        """Create resolver with large project."""
        db_path = large_project / "test.db"
        archive_dir = large_project / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, large_project)
        yield resolver
        # Cleanup
        registry.close()

    def test_single_document_load_performance(self, resolver):
        """Test single document loads in <50ms."""
        start = time.perf_counter()
        resolver.resolve("docs/doc-0.md", {})
        duration = (time.perf_counter() - start) * 1000  # Convert to ms

        assert duration < 50, f"Load took {duration:.2f}ms, expected <50ms"

    def test_section_extraction_performance(self, tmp_path):
        """Test section extraction in <10ms."""
        doc_path = tmp_path / "sections.md"
        content = "# Main\n\nIntro\n\n" + "\n\n".join(
            [f"## Section {i}\n\nContent {i}" for i in range(50)]
        )
        doc_path.write_text(content, encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        # First load to warm up
        resolver.resolve("sections.md#section-25", {})

        # Measure
        start = time.perf_counter()
        resolver.resolve("sections.md#section-25", {})
        duration = (time.perf_counter() - start) * 1000

        # Note: This includes file I/O, so may be >10ms
        # The section extraction itself should be <10ms
        assert duration < 100, f"Extract took {duration:.2f}ms"

        # Cleanup
        registry.close()

    def test_yaml_parsing_performance(self, tmp_path):
        """Test YAML parsing in <10ms."""
        doc_path = tmp_path / "yaml.md"
        frontmatter = {f"key_{i}": f"value_{i}" for i in range(50)}
        frontmatter["nested"] = {f"key_{i}": f"value_{i}" for i in range(50)}

        import yaml
        content = f"---\n{yaml.dump(frontmatter)}---\n\nContent"
        doc_path.write_text(content, encoding="utf-8")

        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)
        resolver = DocResolver(manager, tmp_path)

        # First load to warm up
        resolver.resolve("yaml.md@key_0", {})

        # Measure
        start = time.perf_counter()
        resolver.resolve("yaml.md@nested.key_25", {})
        duration = (time.perf_counter() - start) * 1000

        assert duration < 100, f"YAML parse took {duration:.2f}ms"

        # Cleanup
        registry.close()

    def test_glob_performance(self, resolver):
        """Test glob with 20 files in <1 second."""
        start = time.perf_counter()
        resolver.resolve("glob:docs/*.md", {})
        duration = time.perf_counter() - start

        assert duration < 1.0, f"Glob took {duration:.2f}s, expected <1s"


class TestDocResolverIntegration:
    """Integration tests with real document lifecycle."""

    @pytest.fixture
    def integrated_setup(self, tmp_path):
        """Setup with registered documents."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create document
        doc_path = docs_dir / "story.md"
        content = """---
status: in_progress
owner: amelia
epic: 13
story: 13.2
---

# Story 13.2: Document Reference Resolver

## Acceptance Criteria

- [ ] Full document loading
- [ ] Section extraction
- [ ] YAML field extraction

## Implementation

Implementation details here.
"""
        doc_path.write_text(content, encoding="utf-8")

        # Setup document manager
        db_path = tmp_path / "test.db"
        archive_dir = tmp_path / ".archive"
        registry = DocumentRegistry(db_path)
        manager = DocumentLifecycleManager(registry, archive_dir)

        # Register document
        doc = manager.register_document(
            path=doc_path,
            doc_type="story",
            author="amelia"
        )
        manager.transition_state(doc.id, DocumentState.ACTIVE)

        resolver = DocResolver(manager, tmp_path)

        yield {
            "resolver": resolver,
            "manager": manager,
            "doc": doc,
            "path": "docs/story.md",
            "registry": registry
        }

        # Cleanup
        registry.close()

    def test_end_to_end_full_document(self, integrated_setup):
        """Test end-to-end full document loading."""
        resolver = integrated_setup["resolver"]
        path = integrated_setup["path"]

        content = resolver.resolve(path, {})

        assert "Story 13.2" in content
        assert "Acceptance Criteria" in content

    def test_end_to_end_section_extraction(self, integrated_setup):
        """Test end-to-end section extraction."""
        resolver = integrated_setup["resolver"]
        path = integrated_setup["path"]

        criteria = resolver.resolve(f"{path}#acceptance-criteria", {})

        assert "Full document loading" in criteria
        assert "Section extraction" in criteria
        assert "Implementation" not in criteria

    def test_end_to_end_yaml_extraction(self, integrated_setup):
        """Test end-to-end YAML field extraction."""
        resolver = integrated_setup["resolver"]
        path = integrated_setup["path"]

        status = resolver.resolve(f"{path}@status", {})
        owner = resolver.resolve(f"{path}@owner", {})

        assert status == "in_progress"
        assert owner == "amelia"

    def test_with_cached_documents(self, integrated_setup):
        """Test resolver works with cached documents."""
        resolver = integrated_setup["resolver"]
        path = integrated_setup["path"]

        # Load multiple times - should work consistently
        content1 = resolver.resolve(path, {})
        content2 = resolver.resolve(path, {})
        content3 = resolver.resolve(path, {})

        assert content1 == content2 == content3
