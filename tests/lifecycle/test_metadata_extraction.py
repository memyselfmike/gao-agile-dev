"""
Tests for metadata extraction functionality.

This module tests the DocumentLifecycleManager's metadata extraction capabilities:
- YAML frontmatter parsing
- Path-based metadata extraction
- Content hash calculation
- Metadata merging strategies
"""

import tempfile
from pathlib import Path

import pytest

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.registry import DocumentRegistry


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def db_path(temp_dir):
    """Create temporary database path."""
    return temp_dir / "test_metadata.db"


@pytest.fixture
def archive_dir(temp_dir):
    """Create archive directory."""
    archive = temp_dir / ".archive"
    archive.mkdir(parents=True, exist_ok=True)
    return archive


@pytest.fixture
def registry(db_path):
    """Create DocumentRegistry instance."""
    reg = DocumentRegistry(db_path)
    yield reg
    reg.close()


@pytest.fixture
def manager(registry, archive_dir):
    """Create DocumentLifecycleManager instance."""
    return DocumentLifecycleManager(registry, archive_dir)


class TestYAMLFrontmatterExtraction:
    """Tests for YAML frontmatter extraction."""

    def test_extract_simple_frontmatter(self, manager, temp_dir):
        """Test extracting simple YAML frontmatter."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: john
reviewer: winston
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        # Extract metadata
        metadata = manager._extract_metadata(doc_path)

        assert metadata["owner"] == "john"
        assert metadata["reviewer"] == "winston"

    def test_extract_complex_frontmatter(self, manager, temp_dir):
        """Test extracting complex YAML frontmatter with nested structures."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: john
reviewer: winston
feature: authentication
epic: 5
tags:
  - security
  - auth
  - critical
metadata:
  version: 1.0
  priority: high
related_docs:
  - docs/PRD.md
  - docs/Architecture.md
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert metadata["owner"] == "john"
        assert metadata["feature"] == "authentication"
        assert metadata["epic"] == 5
        assert len(metadata["tags"]) == 3
        assert "security" in metadata["tags"]
        assert metadata["metadata"]["version"] == 1.0  # YAML parses as number
        assert len(metadata["related_docs"]) == 2

    def test_extract_no_frontmatter(self, manager, temp_dir):
        """Test document with no frontmatter."""
        doc_path = temp_dir / "doc.md"
        doc_path.write_text("# Document\n\nNo frontmatter here.", encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert metadata == {}

    def test_extract_invalid_frontmatter(self, manager, temp_dir):
        """Test document with invalid YAML frontmatter."""
        doc_path = temp_dir / "doc.md"
        content = """---
invalid: yaml: structure:
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        # Should return empty dict on parse error
        metadata = manager._extract_metadata(doc_path)

        assert metadata == {}

    def test_extract_incomplete_frontmatter(self, manager, temp_dir):
        """Test document with incomplete frontmatter (missing closing ---)."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: john

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        # Should return empty dict if frontmatter incomplete
        metadata = manager._extract_metadata(doc_path)

        assert metadata == {}

    def test_extract_empty_frontmatter(self, manager, temp_dir):
        """Test document with empty frontmatter."""
        doc_path = temp_dir / "doc.md"
        content = """---
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert metadata == {}

    def test_extract_frontmatter_with_special_characters(self, manager, temp_dir):
        """Test frontmatter with special characters in values."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: john@company.com
description: Document with special chars
file_path: C:\\\\Users\\\\Documents\\\\file.md
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert metadata["owner"] == "john@company.com"
        assert "special chars" in metadata["description"]
        assert "Users" in metadata["file_path"]

    def test_extract_nonexistent_file(self, manager, temp_dir):
        """Test extracting from nonexistent file."""
        doc_path = temp_dir / "nonexistent.md"

        metadata = manager._extract_metadata(doc_path)

        assert metadata == {}


class TestPathMetadataExtraction:
    """Tests for path-based metadata extraction."""

    def test_extract_feature_from_path(self, manager, temp_dir):
        """Test extracting feature name from path."""
        doc_path = temp_dir / "docs" / "features" / "user-authentication" / "PRD.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# PRD", encoding="utf-8")

        metadata = manager._extract_path_metadata(doc_path)

        assert metadata["feature"] == "user-authentication"

    def test_extract_epic_from_path(self, manager, temp_dir):
        """Test extracting epic number from path."""
        # Test with hyphen
        doc_path1 = temp_dir / "docs" / "epic-5" / "story.md"
        metadata1 = manager._extract_path_metadata(doc_path1)
        assert metadata1["epic"] == 5

        # Test with underscore
        doc_path2 = temp_dir / "docs" / "epic_12" / "story.md"
        metadata2 = manager._extract_path_metadata(doc_path2)
        assert metadata2["epic"] == 12

    def test_extract_story_from_path(self, manager, temp_dir):
        """Test extracting story identifier from path."""
        # Test with hyphen and dot
        doc_path1 = temp_dir / "docs" / "story-5.2.md"
        metadata1 = manager._extract_path_metadata(doc_path1)
        assert metadata1["story"] == "5.2"

        # Test with underscore
        doc_path2 = temp_dir / "docs" / "story_12_3.md"
        metadata2 = manager._extract_path_metadata(doc_path2)
        assert metadata2["story"] == "12.3"

    def test_extract_all_from_path(self, manager, temp_dir):
        """Test extracting feature, epic, and story from path."""
        doc_path = (
            temp_dir / "docs" / "features" / "auth-system" / "stories" / "epic-5" / "story-5.2.md"
        )
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text("# Story", encoding="utf-8")

        metadata = manager._extract_path_metadata(doc_path)

        assert metadata["feature"] == "auth-system"
        assert metadata["epic"] == 5
        assert metadata["story"] == "5.2"

    def test_extract_no_metadata_from_path(self, manager, temp_dir):
        """Test path with no extractable metadata."""
        doc_path = temp_dir / "docs" / "README.md"

        metadata = manager._extract_path_metadata(doc_path)

        assert "feature" not in metadata
        assert "epic" not in metadata
        assert "story" not in metadata

    def test_extract_feature_with_special_chars(self, manager, temp_dir):
        """Test extracting feature with special characters."""
        doc_path = temp_dir / "docs" / "features" / "oauth2-integration" / "PRD.md"

        metadata = manager._extract_path_metadata(doc_path)

        assert metadata["feature"] == "oauth2-integration"

    def test_extract_with_windows_paths(self, manager):
        """Test path extraction works with Windows-style paths."""
        doc_path = Path("C:\\Projects\\docs\\features\\auth\\epic-5\\story-5.1.md")

        metadata = manager._extract_path_metadata(doc_path)

        assert metadata["feature"] == "auth"
        assert metadata["epic"] == 5
        assert metadata["story"] == "5.1"

    def test_extract_case_insensitive(self, manager, temp_dir):
        """Test that extraction is case-insensitive."""
        doc_path = temp_dir / "docs" / "EPIC-5" / "STORY-5.2.md"

        metadata = manager._extract_path_metadata(doc_path)

        assert metadata["epic"] == 5
        assert metadata["story"] == "5.2"


class TestContentHashCalculation:
    """Tests for content hash calculation."""

    def test_calculate_hash_existing_file(self, manager, temp_dir):
        """Test calculating hash for existing file."""
        doc_path = temp_dir / "doc.md"
        doc_path.write_text("# Document\n\nContent here.", encoding="utf-8")

        content_hash = manager._calculate_content_hash(doc_path)

        assert content_hash is not None
        assert len(content_hash) == 64  # SHA256 hex digest

    def test_calculate_hash_consistency(self, manager, temp_dir):
        """Test that same content produces same hash."""
        doc_path = temp_dir / "doc.md"
        content = "# Document\n\nSame content."
        doc_path.write_text(content, encoding="utf-8")

        hash1 = manager._calculate_content_hash(doc_path)

        # Write again
        doc_path.write_text(content, encoding="utf-8")
        hash2 = manager._calculate_content_hash(doc_path)

        assert hash1 == hash2

    def test_calculate_hash_different_content(self, manager, temp_dir):
        """Test that different content produces different hash."""
        doc_path = temp_dir / "doc.md"

        doc_path.write_text("# Document 1", encoding="utf-8")
        hash1 = manager._calculate_content_hash(doc_path)

        doc_path.write_text("# Document 2", encoding="utf-8")
        hash2 = manager._calculate_content_hash(doc_path)

        assert hash1 != hash2

    def test_calculate_hash_nonexistent_file(self, manager, temp_dir):
        """Test calculating hash for nonexistent file."""
        doc_path = temp_dir / "nonexistent.md"

        content_hash = manager._calculate_content_hash(doc_path)

        assert content_hash is None

    def test_calculate_hash_large_file(self, manager, temp_dir):
        """Test calculating hash for large file (tests chunking)."""
        doc_path = temp_dir / "large.md"

        # Create large content (> 4KB to test chunking)
        large_content = "x" * 10000
        doc_path.write_text(large_content, encoding="utf-8")

        content_hash = manager._calculate_content_hash(doc_path)

        assert content_hash is not None
        assert len(content_hash) == 64

    def test_calculate_hash_binary_file(self, manager, temp_dir):
        """Test calculating hash for binary file."""
        doc_path = temp_dir / "binary.bin"
        doc_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        content_hash = manager._calculate_content_hash(doc_path)

        assert content_hash is not None
        assert len(content_hash) == 64


class TestMetadataMerging:
    """Tests for metadata merging strategies."""

    def test_merge_provided_overrides_extracted(self, manager, temp_dir):
        """Test that provided metadata overrides extracted metadata."""
        doc_path = temp_dir / "docs" / "features" / "auth" / "PRD.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        content = """---
owner: john
feature: authentication
---

# PRD
"""
        doc_path.write_text(content, encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="jane",
            metadata={
                "owner": "jane",  # Override frontmatter
                "feature": "overridden",  # Override both frontmatter and path
            },
        )

        assert doc.owner == "jane"
        assert doc.feature == "overridden"

    def test_merge_extracted_overrides_path(self, manager, temp_dir):
        """Test that extracted (frontmatter) overrides path metadata."""
        doc_path = temp_dir / "docs" / "features" / "path-feature" / "PRD.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        content = """---
feature: frontmatter-feature
---

# PRD
"""
        doc_path.write_text(content, encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="john",
        )

        # Frontmatter should override path
        assert doc.feature == "frontmatter-feature"

    def test_merge_all_sources(self, manager, temp_dir):
        """Test merging metadata from all sources."""
        doc_path = temp_dir / "docs" / "features" / "auth" / "epic-5" / "story-5.2.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        content = """---
owner: john
tags:
  - security
---

# Story
"""
        doc_path.write_text(content, encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="story",
            author="bob",
            metadata={"priority": "high"},
        )

        # Verify all sources merged correctly
        assert doc.feature == "auth"  # From path
        assert doc.epic == 5  # From path
        assert doc.story == "5.2"  # From path
        assert doc.owner == "john"  # From frontmatter
        assert "security" in doc.metadata["tags"]  # From frontmatter
        assert doc.metadata["priority"] == "high"  # From provided

    def test_merge_with_none_values(self, manager, temp_dir):
        """Test merging handles None values correctly."""
        doc_path = temp_dir / "doc.md"
        doc_path.write_text("# Document", encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="john",
            metadata=None,  # Explicitly None
        )

        # Should not crash
        assert doc.id is not None

    def test_merge_empty_metadata(self, manager, temp_dir):
        """Test merging with empty metadata dict."""
        doc_path = temp_dir / "doc.md"
        doc_path.write_text("# Document", encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="john",
            metadata={},
        )

        # Should not crash
        assert doc.id is not None

    def test_merge_preserves_all_fields(self, manager, temp_dir):
        """Test that merging preserves all metadata fields."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: john
reviewer: winston
tags:
  - tag1
  - tag2
custom_field: custom_value
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        doc = manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="john",
            metadata={"additional": "field"},
        )

        # All fields should be present
        assert doc.owner == "john"
        assert doc.reviewer == "winston"
        assert "tag1" in doc.metadata["tags"]
        assert doc.metadata["custom_field"] == "custom_value"
        assert doc.metadata["additional"] == "field"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_extract_with_unicode(self, manager, temp_dir):
        """Test extracting metadata with Unicode characters."""
        doc_path = temp_dir / "doc.md"
        content = """---
owner: "José García"
description: "Документ на русском"
emoji: "🚀 🎉"
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert metadata["owner"] == "José García"
        assert "Документ" in metadata["description"]
        assert "🚀" in metadata["emoji"]

    def test_extract_with_multiline_values(self, manager, temp_dir):
        """Test extracting multiline YAML values."""
        doc_path = temp_dir / "doc.md"
        content = """---
description: |
  This is a multiline
  description that spans
  multiple lines.
---

# Document
"""
        doc_path.write_text(content, encoding="utf-8")

        metadata = manager._extract_metadata(doc_path)

        assert "multiline" in metadata["description"]
        assert "multiple lines" in metadata["description"]

    def test_path_with_multiple_features_dirs(self, manager, temp_dir):
        """Test path with nested 'features' directories."""
        doc_path = temp_dir / "docs" / "features" / "auth" / "features" / "nested" / "doc.md"

        metadata = manager._extract_path_metadata(doc_path)

        # Should extract first match
        assert metadata["feature"] == "auth"

    def test_path_with_multiple_epic_numbers(self, manager, temp_dir):
        """Test path with multiple epic numbers."""
        doc_path = temp_dir / "epic-5" / "epic-10" / "story.md"

        metadata = manager._extract_path_metadata(doc_path)

        # Should extract first match
        assert metadata["epic"] == 5

    def test_hash_empty_file(self, manager, temp_dir):
        """Test calculating hash for empty file."""
        doc_path = temp_dir / "empty.md"
        doc_path.write_text("", encoding="utf-8")

        content_hash = manager._calculate_content_hash(doc_path)

        assert content_hash is not None
        assert len(content_hash) == 64

    def test_extract_from_symlink(self, manager, temp_dir):
        """Test extracting metadata from symlinked file."""
        # Create actual file
        actual_file = temp_dir / "actual.md"
        content = """---
owner: john
---

# Document
"""
        actual_file.write_text(content, encoding="utf-8")

        # Create symlink (skip if not supported)
        try:
            symlink = temp_dir / "symlink.md"
            symlink.symlink_to(actual_file)

            metadata = manager._extract_metadata(symlink)

            assert metadata["owner"] == "john"
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform
            pytest.skip("Symlinks not supported")
