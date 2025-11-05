"""
Unit tests for ContextResolver.

Tests context resolution functionality including:
- Predefined context keys
- Custom context keys
- Cache integration
- Usage tracking
- Section extraction
- Error handling
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, MagicMock

from gao_dev.core.meta_prompts.resolvers.context_resolver import ContextResolver
from gao_dev.core.context.context_cache import ContextCache
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker


class TestContextResolver:
    """Test suite for ContextResolver."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def temp_db(self, temp_dir):
        """Create temporary database."""
        return temp_dir / "test_usage.db"

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return ContextCache(ttl_seconds=300)

    @pytest.fixture
    def tracker(self, temp_db):
        """Create tracker instance."""
        return ContextUsageTracker(temp_db)

    @pytest.fixture
    def doc_manager(self):
        """Create mock document manager."""
        return Mock()

    @pytest.fixture
    def resolver(self, cache, doc_manager, tracker, temp_dir):
        """Create resolver instance."""
        return ContextResolver(
            context_cache=cache,
            doc_manager=doc_manager,
            context_tracker=tracker,
            project_root=temp_dir
        )

    def test_can_resolve_context(self, resolver):
        """Test can_resolve returns True for 'context'."""
        assert resolver.can_resolve("context") is True
        assert resolver.can_resolve("doc") is False
        assert resolver.can_resolve("query") is False

    def test_resolve_custom_context_key(self, resolver):
        """Test resolving custom context key from context dict."""
        context = {
            'custom_key': 'Custom value here',
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("custom_key", context)
        assert result == 'Custom value here'

    def test_resolve_unknown_context_key(self, resolver):
        """Test resolving unknown context key returns empty string."""
        context = {'workflow_id': 'wf-123'}

        result = resolver.resolve("unknown_key", context)
        assert result == ""

    def test_cache_hit(self, resolver, cache):
        """Test cache hit returns cached value."""
        # Pre-populate cache
        cache_key = "epic_definition:feature=sandbox:epic=3"
        cache.set(cache_key, "Cached epic definition")

        context = {
            'feature': 'sandbox',
            'epic': 3,
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("epic_definition", context)
        assert result == "Cached epic definition"

    def test_cache_miss_loads_from_file(self, resolver, temp_dir):
        """Test cache miss loads from filesystem."""
        # Create test file
        docs_dir = temp_dir / "docs" / "features" / "sandbox"
        docs_dir.mkdir(parents=True)
        epics_file = docs_dir / "epics.md"
        epics_file.write_text("""
# Epic 3

Epic definition here

## Details
Some details
""")

        context = {
            'feature': 'sandbox',
            'epic': 3,
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("epic_definition", context)
        assert "Epic definition here" in result

    def test_cache_population_after_miss(self, resolver, cache, temp_dir):
        """Test cache is populated after cache miss."""
        # Create test file
        docs_dir = temp_dir / "docs" / "features" / "sandbox"
        docs_dir.mkdir(parents=True)
        arch_file = docs_dir / "ARCHITECTURE.md"
        arch_file.write_text("Architecture content")

        context = {
            'feature': 'sandbox',
            'workflow_id': 'wf-123'
        }

        # First call - cache miss
        result1 = resolver.resolve("architecture", context)
        assert result1 == "Architecture content"

        # Second call - should be cached
        cache_key = "architecture:feature=sandbox"
        assert cache.get(cache_key) == "Architecture content"

    def test_usage_tracking_cache_hit(self, resolver, cache, tracker):
        """Test usage tracking records cache hits."""
        # Pre-populate cache
        cache_key = "prd:feature=sandbox"
        cache.set(cache_key, "PRD content")

        context = {
            'feature': 'sandbox',
            'workflow_id': 'wf-123'
        }

        resolver.resolve("prd", context)

        # Check usage was tracked
        history = tracker.get_usage_history(workflow_id="wf-123")
        assert len(history) == 1
        assert history[0]['context_key'] == "prd"
        assert history[0]['cache_hit'] == 1

    def test_usage_tracking_cache_miss(self, resolver, tracker, temp_dir):
        """Test usage tracking records cache misses."""
        # Create test file
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        standards_file = docs_dir / "CODING_STANDARDS.md"
        standards_file.write_text("Coding standards content")

        context = {'workflow_id': 'wf-123'}

        resolver.resolve("coding_standards", context)

        # Check usage was tracked
        history = tracker.get_usage_history(workflow_id="wf-123")
        assert len(history) == 1
        assert history[0]['context_key'] == "coding_standards"
        assert history[0]['cache_hit'] == 0

    def test_content_hash_tracking(self, resolver, tracker, temp_dir):
        """Test content hash is recorded for version tracking."""
        # Create test file
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "CODING_STANDARDS.md"
        file_path.write_text("Content version 1")

        context = {'workflow_id': 'wf-123'}

        resolver.resolve("coding_standards", context)

        history = tracker.get_usage_history(workflow_id="wf-123")
        hash1 = history[0]['content_hash']
        assert hash1  # Should have a hash

        # Update file content
        file_path.write_text("Content version 2")

        # Clear cache to force reload
        resolver.cache.clear()

        resolver.resolve("coding_standards", context)

        history = tracker.get_usage_history(workflow_id="wf-123")
        hash2 = history[0]['content_hash']

        # Hashes should be different
        assert hash2 != hash1

    def test_section_extraction(self, resolver, temp_dir):
        """Test extracting markdown section."""
        # Create story file with sections
        story_dir = temp_dir / "docs" / "features" / "sandbox" / "stories" / "epic-3"
        story_dir.mkdir(parents=True)
        story_file = story_dir / "story-3.1.md"
        story_file.write_text("""
# Story 3.1

Story description

## Acceptance Criteria

- Criterion 1
- Criterion 2
- Criterion 3

## Technical Notes

Some notes
""")

        context = {
            'feature': 'sandbox',
            'epic': 3,
            'story': '3.1',
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("acceptance_criteria", context)

        assert "Criterion 1" in result
        assert "Criterion 2" in result
        assert "Criterion 3" in result
        assert "Technical Notes" not in result

    def test_normalize_heading(self, resolver):
        """Test heading normalization."""
        assert resolver._normalize_heading("Acceptance Criteria") == "acceptance-criteria"
        assert resolver._normalize_heading("User Stories") == "user-stories"
        assert resolver._normalize_heading("Feature #1") == "feature-1"
        assert resolver._normalize_heading("UPPERCASE") == "uppercase"
        assert resolver._normalize_heading("under_score") == "under-score"

    def test_hash_content(self, resolver):
        """Test content hashing."""
        hash1 = resolver._hash_content("content")
        hash2 = resolver._hash_content("content")
        hash3 = resolver._hash_content("different")

        # Same content -> same hash
        assert hash1 == hash2

        # Different content -> different hash
        assert hash1 != hash3

        # Hash should be 16 chars
        assert len(hash1) == 16

    def test_build_cache_key_predefined(self, resolver):
        """Test building cache key for predefined context."""
        context = {'feature': 'sandbox', 'epic': 3, 'story': '3.1'}

        # Epic definition uses feature and epic
        key = resolver._build_cache_key("epic_definition", context)
        assert "epic_definition" in key
        assert "feature=sandbox" in key
        assert "epic=3" in key

        # Architecture uses only feature
        key = resolver._build_cache_key("architecture", context)
        assert "architecture" in key
        assert "feature=sandbox" in key

        # Story definition uses feature, epic, and story
        key = resolver._build_cache_key("story_definition", context)
        assert "story_definition" in key
        assert "feature=sandbox" in key
        assert "epic=3" in key
        assert "story=3.1" in key

    def test_build_cache_key_custom(self, resolver):
        """Test building cache key for custom context."""
        context = {'feature': 'sandbox'}

        key = resolver._build_cache_key("custom_key", context)
        assert key == "custom:custom_key"

    def test_missing_context_variable(self, resolver):
        """Test handling missing context variables for predefined keys."""
        # Epic definition requires 'feature' and 'epic'
        context = {'feature': 'sandbox'}  # Missing 'epic'

        result = resolver.resolve("epic_definition", context)
        assert result == ""

    def test_file_not_found(self, resolver, temp_dir):
        """Test handling file not found."""
        context = {
            'feature': 'nonexistent',
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("architecture", context)
        assert result == ""

    def test_section_not_found(self, resolver, temp_dir):
        """Test handling section not found."""
        # Create file without acceptance criteria section
        story_dir = temp_dir / "docs" / "features" / "sandbox" / "stories" / "epic-3"
        story_dir.mkdir(parents=True)
        story_file = story_dir / "story-3.1.md"
        story_file.write_text("""
# Story 3.1

Story description

## Technical Notes

Some notes
""")

        context = {
            'feature': 'sandbox',
            'epic': 3,
            'story': '3.1',
            'workflow_id': 'wf-123'
        }

        result = resolver.resolve("acceptance_criteria", context)
        assert result == ""

    def test_all_predefined_context_keys(self, resolver):
        """Test all predefined context keys are defined."""
        expected_keys = {
            'epic_definition',
            'architecture',
            'prd',
            'coding_standards',
            'acceptance_criteria',
            'story_definition'
        }

        assert set(resolver.CONTEXT_MAPPINGS.keys()) == expected_keys

    def test_multiple_resolutions_same_workflow(self, resolver, tracker, temp_dir):
        """Test multiple context resolutions in same workflow."""
        # Create test files
        docs_dir = temp_dir / "docs" / "features" / "sandbox"
        docs_dir.mkdir(parents=True)

        arch_file = docs_dir / "ARCHITECTURE.md"
        arch_file.write_text("Architecture")

        prd_file = docs_dir / "PRD.md"
        prd_file.write_text("PRD")

        context = {
            'feature': 'sandbox',
            'workflow_id': 'wf-123'
        }

        resolver.resolve("architecture", context)
        resolver.resolve("prd", context)

        history = tracker.get_usage_history(workflow_id="wf-123")
        assert len(history) == 2

        context_keys = {h['context_key'] for h in history}
        assert context_keys == {'architecture', 'prd'}

    def test_resolve_with_epic_and_story_tracking(self, resolver, tracker, temp_dir):
        """Test epic and story are tracked in usage."""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "CODING_STANDARDS.md"
        file_path.write_text("Standards")

        context = {
            'workflow_id': 'wf-123',
            'epic': 5,
            'story': '5.2'
        }

        resolver.resolve("coding_standards", context)

        history = tracker.get_usage_history(workflow_id="wf-123")
        assert history[0]['epic'] == 5
        assert history[0]['story'] == '5.2'

    def test_empty_file(self, resolver, temp_dir):
        """Test handling empty file."""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "CODING_STANDARDS.md"
        file_path.write_text("")

        context = {}

        result = resolver.resolve("coding_standards", context)
        assert result == ""

    def test_unicode_content(self, resolver, temp_dir):
        """Test handling Unicode content."""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "CODING_STANDARDS.md"
        # Use encoding parameter to handle Unicode on Windows
        file_path.write_text("Content with émojis and spëcial chars 中文", encoding="utf-8")

        context = {}

        result = resolver.resolve("coding_standards", context)
        assert "émojis" in result
        assert "中文" in result

    def test_large_file_caching(self, resolver, cache, temp_dir):
        """Test caching large files."""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "CODING_STANDARDS.md"

        # Create large content
        large_content = "x" * 50000  # 50KB
        file_path.write_text(large_content)

        context = {}

        # First resolve - cache miss
        result1 = resolver.resolve("coding_standards", context)
        assert len(result1) == 50000

        # Second resolve - cache hit
        result2 = resolver.resolve("coding_standards", context)
        assert result2 == result1

        # Verify cache was used
        stats = cache.get_stats()
        assert stats['hits'] == 1
