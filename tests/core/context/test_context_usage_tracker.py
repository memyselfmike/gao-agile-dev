"""
Unit tests for ContextUsageTracker.

Tests usage tracking functionality including:
- Recording usage
- Querying usage history
- Filtering by workflow/context/epic/story
- Cache hit rate calculation
- Version tracking
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from gao_dev.core.context.context_usage_tracker import ContextUsageTracker


class TestContextUsageTracker:
    """Test suite for ContextUsageTracker."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_context_usage.db"
            yield db_path

    @pytest.fixture
    def tracker(self, temp_db):
        """Create tracker instance with temp database."""
        return ContextUsageTracker(temp_db)

    def test_init_creates_database(self, temp_db):
        """Test tracker initialization creates database and schema."""
        tracker = ContextUsageTracker(temp_db)

        # Database file should exist
        assert temp_db.exists()

        # Should be able to query (no errors)
        history = tracker.get_usage_history()
        assert history == []

    def test_record_usage_basic(self, tracker):
        """Test recording basic usage."""
        tracker.record_usage(
            context_key="epic_definition",
            content_hash="abc123",
            cache_hit=True,
            workflow_id="wf-123"
        )

        # Should be in history
        history = tracker.get_usage_history(workflow_id="wf-123")
        assert len(history) == 1
        assert history[0]['context_key'] == "epic_definition"
        assert history[0]['content_hash'] == "abc123"
        assert history[0]['cache_hit'] == 1  # SQLite stores boolean as int

    def test_record_usage_with_epic_story(self, tracker):
        """Test recording usage with epic and story."""
        tracker.record_usage(
            context_key="acceptance_criteria",
            content_hash="def456",
            cache_hit=False,
            workflow_id="wf-123",
            epic=3,
            story="3.1"
        )

        history = tracker.get_usage_history(workflow_id="wf-123")
        assert len(history) == 1
        assert history[0]['epic'] == 3
        assert history[0]['story'] == "3.1"

    def test_multiple_records(self, tracker):
        """Test recording multiple usage entries."""
        tracker.record_usage("key1", "hash1", True, "wf-1", 1, "1.1")
        tracker.record_usage("key2", "hash2", False, "wf-1", 1, "1.2")
        tracker.record_usage("key3", "hash3", True, "wf-2", 2, "2.1")

        history = tracker.get_usage_history()
        assert len(history) == 3

    def test_get_usage_history_filter_by_workflow(self, tracker):
        """Test filtering usage history by workflow ID."""
        tracker.record_usage("key1", "hash1", True, "wf-1")
        tracker.record_usage("key2", "hash2", True, "wf-1")
        tracker.record_usage("key3", "hash3", True, "wf-2")

        history = tracker.get_usage_history(workflow_id="wf-1")
        assert len(history) == 2
        assert all(h['workflow_id'] == "wf-1" for h in history)

    def test_get_usage_history_filter_by_context_key(self, tracker):
        """Test filtering usage history by context key."""
        tracker.record_usage("epic_definition", "hash1", True, "wf-1")
        tracker.record_usage("architecture", "hash2", True, "wf-1")
        tracker.record_usage("epic_definition", "hash3", False, "wf-2")

        history = tracker.get_usage_history(context_key="epic_definition")
        assert len(history) == 2
        assert all(h['context_key'] == "epic_definition" for h in history)

    def test_get_usage_history_filter_by_epic(self, tracker):
        """Test filtering usage history by epic."""
        tracker.record_usage("key1", "hash1", True, "wf-1", epic=3)
        tracker.record_usage("key2", "hash2", True, "wf-1", epic=3)
        tracker.record_usage("key3", "hash3", True, "wf-2", epic=4)

        history = tracker.get_usage_history(epic=3)
        assert len(history) == 2
        assert all(h['epic'] == 3 for h in history)

    def test_get_usage_history_filter_by_story(self, tracker):
        """Test filtering usage history by story."""
        tracker.record_usage("key1", "hash1", True, "wf-1", epic=3, story="3.1")
        tracker.record_usage("key2", "hash2", True, "wf-1", epic=3, story="3.2")
        tracker.record_usage("key3", "hash3", True, "wf-2", epic=3, story="3.1")

        history = tracker.get_usage_history(story="3.1")
        assert len(history) == 2
        assert all(h['story'] == "3.1" for h in history)

    def test_get_usage_history_multiple_filters(self, tracker):
        """Test filtering with multiple criteria."""
        tracker.record_usage("key1", "hash1", True, "wf-1", epic=3, story="3.1")
        tracker.record_usage("key2", "hash2", True, "wf-1", epic=3, story="3.2")
        tracker.record_usage("key1", "hash3", True, "wf-2", epic=3, story="3.1")

        history = tracker.get_usage_history(
            workflow_id="wf-1",
            context_key="key1",
            epic=3,
            story="3.1"
        )
        assert len(history) == 1
        assert history[0]['workflow_id'] == "wf-1"
        assert history[0]['context_key'] == "key1"
        assert history[0]['epic'] == 3
        assert history[0]['story'] == "3.1"

    def test_get_usage_history_limit(self, tracker):
        """Test limiting usage history results."""
        for i in range(10):
            tracker.record_usage(f"key{i}", f"hash{i}", True, "wf-1")

        history = tracker.get_usage_history(limit=5)
        assert len(history) == 5

    def test_get_usage_history_ordered_by_time(self, tracker):
        """Test usage history is ordered by accessed_at DESC."""
        import time

        tracker.record_usage("key1", "hash1", True, "wf-1")
        time.sleep(0.01)  # Small delay
        tracker.record_usage("key2", "hash2", True, "wf-1")
        time.sleep(0.01)
        tracker.record_usage("key3", "hash3", True, "wf-1")

        history = tracker.get_usage_history()

        # Most recent first
        assert history[0]['context_key'] == "key3"
        assert history[1]['context_key'] == "key2"
        assert history[2]['context_key'] == "key1"

    def test_get_context_versions(self, tracker):
        """Test getting version history for a context key."""
        import time

        # Record same key with different content hashes
        tracker.record_usage("epic_definition", "hash_v1", True, "wf-1")
        time.sleep(0.01)
        tracker.record_usage("epic_definition", "hash_v1", True, "wf-2")
        time.sleep(0.01)
        tracker.record_usage("epic_definition", "hash_v2", False, "wf-3")

        versions = tracker.get_context_versions("epic_definition")

        # Should have 2 distinct versions
        assert len(versions) == 2

        # Most recent first
        assert versions[0]['content_hash'] == "hash_v2"
        assert versions[0]['access_count'] == 1

        assert versions[1]['content_hash'] == "hash_v1"
        assert versions[1]['access_count'] == 2

    def test_get_context_versions_limit(self, tracker):
        """Test limiting version history results."""
        for i in range(10):
            tracker.record_usage("key1", f"hash{i}", True, "wf-1")

        versions = tracker.get_context_versions("key1", limit=5)
        assert len(versions) <= 5

    def test_get_cache_hit_rate_all(self, tracker):
        """Test calculating overall cache hit rate."""
        tracker.record_usage("key1", "hash1", True, "wf-1")  # hit
        tracker.record_usage("key2", "hash2", True, "wf-1")  # hit
        tracker.record_usage("key3", "hash3", False, "wf-1")  # miss
        tracker.record_usage("key4", "hash4", True, "wf-1")  # hit

        stats = tracker.get_cache_hit_rate()

        assert stats['total'] == 4
        assert stats['hits'] == 3
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.75

    def test_get_cache_hit_rate_by_workflow(self, tracker):
        """Test cache hit rate for specific workflow."""
        tracker.record_usage("key1", "hash1", True, "wf-1")
        tracker.record_usage("key2", "hash2", False, "wf-1")
        tracker.record_usage("key3", "hash3", True, "wf-2")

        stats = tracker.get_cache_hit_rate(workflow_id="wf-1")

        assert stats['total'] == 2
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5

    def test_get_cache_hit_rate_by_context_key(self, tracker):
        """Test cache hit rate for specific context key."""
        tracker.record_usage("epic_definition", "hash1", True, "wf-1")
        tracker.record_usage("epic_definition", "hash2", True, "wf-1")
        tracker.record_usage("architecture", "hash3", False, "wf-1")

        stats = tracker.get_cache_hit_rate(context_key="epic_definition")

        assert stats['total'] == 2
        assert stats['hits'] == 2
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 1.0

    def test_get_cache_hit_rate_empty(self, tracker):
        """Test cache hit rate with no data."""
        stats = tracker.get_cache_hit_rate()

        assert stats['total'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0

    def test_clear_history_all(self, tracker):
        """Test clearing all history."""
        tracker.record_usage("key1", "hash1", True, "wf-1")
        tracker.record_usage("key2", "hash2", True, "wf-1")

        deleted = tracker.clear_history()
        assert deleted == 2

        history = tracker.get_usage_history()
        assert len(history) == 0

    def test_clear_history_older_than(self, tracker):
        """Test clearing history older than N days."""
        from datetime import datetime, timedelta

        tracker.record_usage("key1", "hash1", True, "wf-1")

        # Manually update timestamp to be older
        with tracker._get_connection() as conn:
            old_date = (datetime.now() - timedelta(days=10)).isoformat()
            conn.execute(
                "UPDATE context_usage SET accessed_at = ?",
                (old_date,)
            )
            conn.commit()

        # Add recent entry
        tracker.record_usage("key2", "hash2", True, "wf-1")

        # Clear entries older than 5 days
        deleted = tracker.clear_history(older_than_days=5)
        assert deleted == 1

        # Only recent entry should remain
        history = tracker.get_usage_history()
        assert len(history) == 1
        assert history[0]['context_key'] == "key2"

    def test_record_without_optional_fields(self, tracker):
        """Test recording usage without workflow/epic/story."""
        tracker.record_usage(
            context_key="coding_standards",
            content_hash="xyz789",
            cache_hit=True
        )

        history = tracker.get_usage_history()
        assert len(history) == 1
        assert history[0]['context_key'] == "coding_standards"
        assert history[0]['workflow_id'] is None
        assert history[0]['epic'] is None
        assert history[0]['story'] is None

    def test_accessed_at_timestamp(self, tracker):
        """Test accessed_at timestamp is recorded."""
        tracker.record_usage("key1", "hash1", True, "wf-1")

        history = tracker.get_usage_history()
        assert 'accessed_at' in history[0]
        assert history[0]['accessed_at']  # Not None or empty

        # Should be ISO format
        from datetime import datetime
        datetime.fromisoformat(history[0]['accessed_at'])  # Should not raise
