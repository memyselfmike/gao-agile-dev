"""
Unit tests for Context Lineage Tracking.

Tests the ContextLineageTracker class for recording and querying context usage,
lineage tracking, stale context detection, and report generation.
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from gao_dev.core.context.context_lineage import ContextLineageTracker


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_lineage.db"
        yield db_path


@pytest.fixture
def tracker(temp_db):
    """Create ContextLineageTracker instance for testing."""
    return ContextLineageTracker(temp_db)


class TestContextLineageTracker:
    """Test ContextLineageTracker class."""

    def test_initialization(self, tracker, temp_db):
        """Test tracker initialization creates database and schema."""
        assert temp_db.exists()
        assert tracker.db_path == temp_db

        # Verify table exists
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='context_usage'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_record_usage_basic(self, tracker):
        """Test recording basic context usage."""
        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="abc123def456",
            document_id=42,
            document_path="docs/features/auth/ARCHITECTURE.md",
            document_type="architecture",
            workflow_id="wf-story-3.1",
            workflow_name="implement_story",
            epic=3,
            story="3.1",
        )

        assert usage_id > 0

    def test_record_usage_minimal(self, tracker):
        """Test recording usage with minimal required fields."""
        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="xyz789",
        )

        assert usage_id > 0

    def test_record_usage_invalid_artifact_type(self, tracker):
        """Test recording usage with invalid artifact type raises error."""
        with pytest.raises(ValueError, match="Invalid artifact_type"):
            tracker.record_usage(
                artifact_type="invalid_type",
                artifact_id="3.1",
                document_version="abc123",
            )

    def test_record_usage_all_artifact_types(self, tracker):
        """Test recording usage for all valid artifact types."""
        valid_types = ['epic', 'story', 'task', 'code', 'test', 'doc', 'other']

        for artifact_type in valid_types:
            usage_id = tracker.record_usage(
                artifact_type=artifact_type,
                artifact_id=f"{artifact_type}-1",
                document_version="hash123",
            )
            assert usage_id > 0

    def test_get_artifact_context_empty(self, tracker):
        """Test getting context for non-existent artifact returns empty list."""
        context = tracker.get_artifact_context("story", "999.999")
        assert context == []

    def test_get_artifact_context_single(self, tracker):
        """Test getting context for artifact with single document."""
        # Record usage
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="abc123",
            document_id=42,
            document_path="docs/arch.md",
            document_type="architecture",
            epic=3,
            story="3.1",
        )

        # Get context
        context = tracker.get_artifact_context("story", "3.1")

        assert len(context) == 1
        assert context[0]["artifact_type"] == "story"
        assert context[0]["artifact_id"] == "3.1"
        assert context[0]["document_version"] == "abc123"
        assert context[0]["document_id"] == 42
        assert context[0]["document_type"] == "architecture"

    def test_get_artifact_context_multiple(self, tracker):
        """Test getting context for artifact with multiple documents."""
        # Record multiple usages
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="prd_v1",
            document_id=40,
            document_type="prd",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="arch_v2",
            document_id=41,
            document_type="architecture",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="epic_v1",
            document_id=42,
            document_type="epic",
        )

        # Get context
        context = tracker.get_artifact_context("story", "3.1")

        assert len(context) == 3
        doc_types = {c["document_type"] for c in context}
        assert doc_types == {"prd", "architecture", "epic"}

    def test_get_artifact_context_ordered_by_accessed_at(self, tracker):
        """Test artifact context is ordered by accessed_at descending."""
        import time

        # Record usages with small delays
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v1",
            document_type="prd",
        )
        time.sleep(0.01)

        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v2",
            document_type="architecture",
        )

        # Get context
        context = tracker.get_artifact_context("story", "3.1")

        # Most recent should be first
        assert len(context) == 2
        assert context[0]["document_type"] == "architecture"  # Most recent
        assert context[1]["document_type"] == "prd"  # Older

    def test_get_workflow_context_empty(self, tracker):
        """Test getting context for non-existent workflow returns empty list."""
        context = tracker.get_workflow_context("wf-nonexistent")
        assert context == []

    def test_get_workflow_context_single(self, tracker):
        """Test getting context for workflow execution."""
        # Record usages for workflow
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v1",
            workflow_id="wf-123",
            workflow_name="implement_story",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v2",
            workflow_id="wf-123",
            workflow_name="implement_story",
        )

        # Get workflow context
        context = tracker.get_workflow_context("wf-123")

        assert len(context) == 2
        for c in context:
            assert c["workflow_id"] == "wf-123"
            assert c["workflow_name"] == "implement_story"

    def test_get_workflow_context_ordered_by_accessed_at_asc(self, tracker):
        """Test workflow context is ordered by accessed_at ascending."""
        import time

        # Record usages with delays
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v1",
            workflow_id="wf-123",
        )
        time.sleep(0.01)

        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="v2",
            workflow_id="wf-123",
        )

        # Get workflow context
        context = tracker.get_workflow_context("wf-123")

        # Oldest should be first (chronological order)
        assert len(context) == 2
        assert context[0]["document_version"] == "v1"  # First
        assert context[1]["document_version"] == "v2"  # Second

    def test_detect_stale_usage_no_stale(self, tracker):
        """Test detecting stale usage when all versions are current."""
        # Record usage
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="current_hash",
            document_id=42,
        )

        # Check for stale (version matches)
        current_versions = {42: "current_hash"}
        stale = tracker.detect_stale_usage(current_versions)

        assert stale == []

    def test_detect_stale_usage_with_stale(self, tracker):
        """Test detecting stale usage when document version has changed."""
        # Record usage with old version
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="old_hash",
            document_id=42,
            document_type="architecture",
        )

        # Check for stale (version changed)
        current_versions = {42: "new_hash"}
        stale = tracker.detect_stale_usage(current_versions)

        assert len(stale) == 1
        assert stale[0]["artifact_id"] == "3.1"
        assert stale[0]["recorded_version"] == "old_hash"
        assert stale[0]["current_version"] == "new_hash"
        assert stale[0]["document_id"] == 42

    def test_detect_stale_usage_multiple(self, tracker):
        """Test detecting multiple stale usages."""
        # Record usages with old versions
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="old_prd",
            document_id=40,
            document_type="prd",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.2",
            document_version="old_arch",
            document_id=41,
            document_type="architecture",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.3",
            document_version="current_epic",
            document_id=42,
            document_type="epic",
        )

        # Check for stale
        current_versions = {
            40: "new_prd",  # Changed
            41: "new_arch",  # Changed
            42: "current_epic",  # Same
        }
        stale = tracker.detect_stale_usage(current_versions)

        assert len(stale) == 2
        stale_artifact_ids = {s["artifact_id"] for s in stale}
        assert stale_artifact_ids == {"3.1", "3.2"}

    def test_detect_stale_usage_ignores_unknown_documents(self, tracker):
        """Test stale detection ignores documents not in current_versions."""
        # Record usage for document not in current_versions
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="some_hash",
            document_id=999,  # Not in current_versions
        )

        # Check for stale
        current_versions = {42: "hash"}  # Different document
        stale = tracker.detect_stale_usage(current_versions)

        assert stale == []

    def test_generate_lineage_report_markdown(self, tracker):
        """Test generating lineage report in markdown format."""
        # Record usage for epic 3
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="prd_hash",
            document_path="docs/PRD.md",
            document_type="prd",
            epic=3,
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="arch_hash",
            document_path="docs/ARCHITECTURE.md",
            document_type="architecture",
            epic=3,
        )

        # Generate report
        report = tracker.generate_lineage_report(epic=3, output_format="markdown")

        # Verify report structure
        assert isinstance(report, str)
        assert "# Context Lineage Report - Epic 3" in report
        assert "## Document Flow" in report
        assert "## Artifacts" in report
        assert "PRD.md" in report
        assert "ARCHITECTURE.md" in report

    def test_generate_lineage_report_json(self, tracker):
        """Test generating lineage report in JSON format."""
        # Record usage
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash",
            epic=3,
        )

        # Generate report
        report = tracker.generate_lineage_report(epic=3, output_format="json")

        # Verify JSON structure
        data = json.loads(report)
        assert data["epic"] == 3
        assert "usage_records" in data
        assert len(data["usage_records"]) == 1

    def test_generate_lineage_report_empty_epic(self, tracker):
        """Test generating report for epic with no usage."""
        report = tracker.generate_lineage_report(epic=999, output_format="markdown")

        assert "# Context Lineage Report - Epic 999" in report
        # Should not crash, just show empty sections

    def test_get_context_lineage_empty(self, tracker):
        """Test getting lineage for non-existent artifact."""
        lineage = tracker.get_context_lineage("story", "999.999")
        assert lineage == []

    def test_get_context_lineage_single_document(self, tracker):
        """Test getting lineage with single document."""
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="arch_hash",
            document_type="architecture",
        )

        lineage = tracker.get_context_lineage("story", "3.1")

        assert len(lineage) >= 1
        # Should include the architecture document
        assert any(d["document_type"] == "architecture" for d in lineage)

    def test_get_context_lineage_sorted_by_hierarchy(self, tracker):
        """Test lineage is sorted by document hierarchy (PRD -> Arch -> Epic -> Story)."""
        # Record in random order
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="story_hash",
            document_type="story",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="prd_hash",
            document_type="prd",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="arch_hash",
            document_type="architecture",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="epic_hash",
            document_type="epic",
        )

        lineage = tracker.get_context_lineage("story", "3.1")

        # Extract document types in order
        doc_types = [d["document_type"] for d in lineage]

        # Verify hierarchical order (PRD before Architecture before Epic before Story)
        prd_idx = doc_types.index("prd")
        arch_idx = doc_types.index("architecture")
        epic_idx = doc_types.index("epic")
        story_idx = doc_types.index("story")

        assert prd_idx < arch_idx < epic_idx < story_idx

    def test_performance_record_usage(self, tracker):
        """Test record_usage performance is <50ms."""
        import time

        start = time.time()
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash",
            document_id=42,
            document_path="docs/test.md",
            document_type="architecture",
            workflow_id="wf-123",
            epic=3,
            story="3.1",
        )
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 50, f"record_usage took {duration:.2f}ms (target: <50ms)"

    def test_performance_query_lineage(self, tracker):
        """Test query lineage performance is <100ms."""
        import time

        # Populate with some data
        for i in range(10):
            tracker.record_usage(
                artifact_type="story",
                artifact_id="3.1",
                document_version=f"hash_{i}",
                document_type="architecture",
            )

        # Measure query time
        start = time.time()
        tracker.get_context_lineage("story", "3.1")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 100, f"get_context_lineage took {duration:.2f}ms (target: <100ms)"

    def test_database_indexes_exist(self, temp_db, tracker):
        """Test that database indexes are created for performance."""
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_context_usage%'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Verify key indexes exist
        expected_indexes = [
            "idx_context_usage_artifact",
            "idx_context_usage_document_id",
            "idx_context_usage_workflow_id",
            "idx_context_usage_epic_story",
        ]

        for idx_name in expected_indexes:
            assert idx_name in indexes, f"Missing index: {idx_name}"

    def test_concurrent_usage_recording(self, tracker):
        """Test concurrent usage recording doesn't corrupt data."""
        import threading

        def record_usages(thread_id):
            for i in range(5):
                tracker.record_usage(
                    artifact_type="story",
                    artifact_id=f"thread-{thread_id}.{i}",
                    document_version=f"hash_{thread_id}_{i}",
                )

        threads = [threading.Thread(target=record_usages, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all records were created (3 threads * 5 records = 15)
        conn = sqlite3.connect(str(tracker.db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM context_usage")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 15

    def test_context_usage_with_null_values(self, tracker):
        """Test recording and querying usage with NULL optional fields."""
        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash",
            document_id=None,  # NULL
            document_path=None,  # NULL
            workflow_id=None,  # NULL
        )

        # Should still work
        assert usage_id > 0

        context = tracker.get_artifact_context("story", "3.1")
        assert len(context) == 1
        assert context[0]["document_id"] is None
        assert context[0]["workflow_id"] is None

    def test_epic_story_filtering(self, tracker):
        """Test filtering by epic and story numbers."""
        # Record usage for different epics/stories
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash1",
            epic=3,
            story="3.1",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.2",
            document_version="hash2",
            epic=3,
            story="3.2",
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="4.1",
            document_version="hash3",
            epic=4,
            story="4.1",
        )

        # Query by artifact
        story_3_1 = tracker.get_artifact_context("story", "3.1")
        story_3_2 = tracker.get_artifact_context("story", "3.2")
        story_4_1 = tracker.get_artifact_context("story", "4.1")

        assert len(story_3_1) == 1
        assert len(story_3_2) == 1
        assert len(story_4_1) == 1

        assert story_3_1[0]["epic"] == 3
        assert story_3_1[0]["story"] == "3.1"

    def test_lineage_report_groups_by_artifact(self, tracker):
        """Test lineage report groups artifacts correctly."""
        # Record multiple artifacts
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash1",
            document_type="architecture",
            epic=3,
        )
        tracker.record_usage(
            artifact_type="story",
            artifact_id="3.2",
            document_version="hash2",
            document_type="architecture",
            epic=3,
        )
        tracker.record_usage(
            artifact_type="epic",
            artifact_id="3",
            document_version="hash3",
            document_type="prd",
            epic=3,
        )

        report = tracker.generate_lineage_report(epic=3, output_format="markdown")

        # Should contain both stories
        assert "Story 3.1" in report or "story 3.1" in report
        assert "Story 3.2" in report or "story 3.2" in report
        assert "Epic 3" in report or "epic 3" in report


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_database(self, tracker):
        """Test operations on empty database."""
        assert tracker.get_artifact_context("story", "1.1") == []
        assert tracker.get_workflow_context("wf-123") == []
        assert tracker.detect_stale_usage({}) == []
        assert tracker.get_context_lineage("story", "1.1") == []

    def test_special_characters_in_ids(self, tracker):
        """Test handling of special characters in artifact/document IDs."""
        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="epic-3/story-3.1",
            document_version="hash",
            document_path="docs/features/my-feature/PRD.md",
        )

        assert usage_id > 0

        context = tracker.get_artifact_context("story", "epic-3/story-3.1")
        assert len(context) == 1

    def test_very_long_version_hash(self, tracker):
        """Test handling of very long content hashes."""
        long_hash = "a" * 1000  # Very long hash

        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version=long_hash,
        )

        assert usage_id > 0

        context = tracker.get_artifact_context("story", "3.1")
        assert context[0]["document_version"] == long_hash

    def test_unicode_in_paths(self, tracker):
        """Test handling of Unicode characters in paths."""
        usage_id = tracker.record_usage(
            artifact_type="story",
            artifact_id="3.1",
            document_version="hash",
            document_path="docs/features/事例/PRD.md",  # Japanese characters
        )

        assert usage_id > 0

        context = tracker.get_artifact_context("story", "3.1")
        assert "事例" in context[0]["document_path"]
