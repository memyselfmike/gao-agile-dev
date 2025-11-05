"""
Tests for ChecklistTracker.

Tests database schema creation, tracking operations, query interface,
batch operations, and performance requirements.
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gao_dev.core.checklists.checklist_tracker import ChecklistTracker
from gao_dev.core.checklists.models import ExecutionResult, ItemResult


class TestSchemaCreation:
    """Test database schema creation and validation."""

    def test_schema_creates_tables(self, tmp_path):
        """Test that schema creates all required tables."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('checklist_executions', 'checklist_results')
            """
            )
            tables = {row[0] for row in cursor.fetchall()}
            assert "checklist_executions" in tables
            assert "checklist_results" in tables

    def test_schema_creates_indexes(self, tmp_path):
        """Test that all indexes are created."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check indexes exist
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_%'
            """
            )
            indexes = {row[0] for row in cursor.fetchall()}

            expected_indexes = {
                "idx_executions_checklist",
                "idx_executions_artifact",
                "idx_executions_story",
                "idx_executions_status",
                "idx_executions_date",
                "idx_results_execution",
                "idx_results_status",
            }
            assert expected_indexes.issubset(indexes)

    def test_foreign_key_constraints_enabled(self, tmp_path):
        """Test that foreign key constraints are enforced."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Try to insert result without execution (should fail)
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO checklist_results
                    (execution_id, item_id, status, checked_at)
                    VALUES (99999, 'test', 'pass', ?)
                """,
                    (datetime.now().isoformat(),),
                )

    def test_check_constraints_artifact_type(self, tmp_path):
        """Test CHECK constraint on artifact_type."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Valid artifact type should work
        tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Invalid artifact type should fail
        with pytest.raises(ValueError):
            tracker.track_execution(
                checklist_name="test",
                checklist_version="1.0",
                artifact_type="invalid",
                artifact_id="1.1",
                executed_by="test",
            )

    def test_check_constraints_status(self, tmp_path):
        """Test CHECK constraint on status values."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Valid status should work
        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )

        # Invalid status should fail
        with pytest.raises(ValueError):
            tracker.record_item_result(
                execution_id=execution_id, item_id="test-2", status="invalid"
            )

    def test_cascade_delete(self, tmp_path):
        """Test CASCADE delete removes item results when execution deleted."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Delete execution
            cursor.execute(
                "DELETE FROM checklist_executions WHERE execution_id = ?",
                (execution_id,),
            )

            # Check item results were also deleted
            cursor.execute(
                "SELECT COUNT(*) FROM checklist_results WHERE execution_id = ?",
                (execution_id,),
            )
            count = cursor.fetchone()[0]
            assert count == 0


class TestTrackingOperations:
    """Test core tracking operations."""

    def test_track_execution_creates_record(self, tmp_path):
        """Test track_execution creates execution record."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="qa-comprehensive",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            epic_num=12,
            story_num=1,
        )

        assert execution_id > 0

        # Verify record created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT checklist_name, overall_status FROM checklist_executions WHERE execution_id = ?",
                (execution_id,),
            )
            row = cursor.fetchone()
            assert row[0] == "qa-comprehensive"
            assert row[1] == "in_progress"

    def test_track_execution_with_metadata(self, tmp_path):
        """Test track_execution stores metadata."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        metadata = {"environment": "test", "branch": "main"}
        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
            metadata=metadata,
        )

        result = tracker.get_execution_results(execution_id)
        assert result.metadata == metadata

    def test_record_item_result_validates_status(self, tmp_path):
        """Test record_item_result validates status values."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Valid statuses should work
        for status in ["pass", "fail", "skip", "na"]:
            notes = "test notes" if status in ["fail", "skip"] else None
            tracker.record_item_result(
                execution_id=execution_id,
                item_id=f"test-{status}",
                status=status,
                notes=notes,
            )

        # Invalid status should fail
        with pytest.raises(ValueError, match="Invalid status"):
            tracker.record_item_result(
                execution_id=execution_id, item_id="test-invalid", status="invalid"
            )

    def test_record_item_result_requires_notes_for_fail(self, tmp_path):
        """Test record_item_result requires notes for fail status."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Fail without notes should fail
        with pytest.raises(ValueError, match="Notes required"):
            tracker.record_item_result(
                execution_id=execution_id, item_id="test-1", status="fail"
            )

        # Fail with notes should work
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-1",
            status="fail",
            notes="Missing tests",
        )

    def test_record_item_result_requires_notes_for_skip(self, tmp_path):
        """Test record_item_result requires notes for skip status."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Skip without notes should fail
        with pytest.raises(ValueError, match="Notes required"):
            tracker.record_item_result(
                execution_id=execution_id, item_id="test-1", status="skip"
            )

        # Skip with notes should work
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-1",
            status="skip",
            notes="Not applicable",
        )

    def test_complete_execution_calculates_status_fail(self, tmp_path):
        """Test complete_execution calculates 'fail' when any item fails."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-2",
            status="fail",
            notes="Failed",
        )

        overall_status = tracker.complete_execution(execution_id)
        assert overall_status == "fail"

    def test_complete_execution_calculates_status_pass(self, tmp_path):
        """Test complete_execution calculates 'pass' when all items pass."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )
        tracker.record_item_result(
            execution_id=execution_id, item_id="test-2", status="pass"
        )

        overall_status = tracker.complete_execution(execution_id)
        assert overall_status == "pass"

    def test_complete_execution_calculates_status_partial(self, tmp_path):
        """Test complete_execution calculates 'partial' for skip/na mix."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-2",
            status="skip",
            notes="Skipped",
        )

        overall_status = tracker.complete_execution(execution_id)
        assert overall_status == "pass"  # skip is ignored, so still pass

    def test_complete_execution_calculates_status_partial_na_only(self, tmp_path):
        """Test complete_execution calculates 'partial' when only skip/na."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-1",
            status="skip",
            notes="Skipped",
        )
        tracker.record_item_result(
            execution_id=execution_id, item_id="test-2", status="na"
        )

        overall_status = tracker.complete_execution(execution_id)
        assert overall_status == "partial"

    def test_complete_execution_calculates_duration(self, tmp_path):
        """Test complete_execution calculates duration correctly."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )

        overall_status = tracker.complete_execution(execution_id)

        result = tracker.get_execution_results(execution_id)
        assert result.duration_ms is not None
        assert result.duration_ms > 0

    def test_complete_execution_raises_if_no_items(self, tmp_path):
        """Test complete_execution raises error if no items recorded."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        with pytest.raises(ValueError, match="No item results found"):
            tracker.complete_execution(execution_id)


class TestQueryInterface:
    """Test query methods."""

    def test_get_execution_results_returns_complete_data(self, tmp_path):
        """Test get_execution_results returns complete execution data."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="qa-comprehensive",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            epic_num=12,
            story_num=1,
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="qa-1", status="pass"
        )
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="qa-2",
            status="fail",
            notes="Missing tests",
        )

        tracker.complete_execution(execution_id, notes="Completed with failures")

        result = tracker.get_execution_results(execution_id)

        assert isinstance(result, ExecutionResult)
        assert result.execution_id == execution_id
        assert result.checklist_name == "qa-comprehensive"
        assert result.overall_status == "fail"
        assert len(result.item_results) == 2
        assert result.notes == "Completed with failures"

    def test_get_execution_results_raises_if_not_found(self, tmp_path):
        """Test get_execution_results raises error if execution not found."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        with pytest.raises(ValueError, match="not found"):
            tracker.get_execution_results(99999)

    def test_get_story_checklists_filters_by_story(self, tmp_path):
        """Test get_story_checklists returns only checklists for specific story."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Create executions for different stories
        exec1 = tracker.track_execution(
            checklist_name="qa",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            epic_num=12,
            story_num=1,
        )
        tracker.record_item_result(execution_id=exec1, item_id="qa-1", status="pass")
        tracker.complete_execution(exec1)

        exec2 = tracker.track_execution(
            checklist_name="security",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            epic_num=12,
            story_num=1,
        )
        tracker.record_item_result(execution_id=exec2, item_id="sec-1", status="pass")
        tracker.complete_execution(exec2)

        exec3 = tracker.track_execution(
            checklist_name="qa",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.2",
            executed_by="Amelia",
            epic_num=12,
            story_num=2,
        )
        tracker.record_item_result(execution_id=exec3, item_id="qa-1", status="pass")
        tracker.complete_execution(exec3)

        # Get checklists for story 12.1
        results = tracker.get_story_checklists(epic_num=12, story_num=1)

        assert len(results) == 2
        assert all(r.epic_num == 12 and r.story_num == 1 for r in results)

    def test_get_story_checklists_sorted_by_date(self, tmp_path):
        """Test get_story_checklists returns results sorted by date (newest first)."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Create multiple executions
        for i in range(3):
            exec_id = tracker.track_execution(
                checklist_name=f"checklist-{i}",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                epic_num=12,
                story_num=1,
            )
            tracker.record_item_result(
                execution_id=exec_id, item_id="test-1", status="pass"
            )
            tracker.complete_execution(exec_id)

        results = tracker.get_story_checklists(epic_num=12, story_num=1)

        # Should be sorted newest first
        assert results[0].checklist_name == "checklist-2"
        assert results[1].checklist_name == "checklist-1"
        assert results[2].checklist_name == "checklist-0"

    def test_get_failed_items_returns_only_failures(self, tmp_path):
        """Test get_failed_items returns only failed items."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-2",
            status="fail",
            notes="Missing tests",
        )
        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-3",
            status="fail",
            notes="Coverage too low",
        )

        failed = tracker.get_failed_items(execution_id)

        assert len(failed) == 2
        assert all(item.status == "fail" for item in failed)
        assert failed[0].item_id == "test-2"
        assert failed[1].item_id == "test-3"

    def test_get_checklist_history_returns_executions_and_stats(self, tmp_path):
        """Test get_checklist_history returns executions and statistics."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Create multiple executions of same checklist
        for i in range(5):
            exec_id = tracker.track_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id=f"12.{i}",
                executed_by="Amelia",
            )
            tracker.record_item_result(
                execution_id=exec_id, item_id="qa-1", status="pass"
            )
            if i < 3:
                tracker.record_item_result(
                    execution_id=exec_id, item_id="qa-2", status="pass"
                )
            else:
                tracker.record_item_result(
                    execution_id=exec_id,
                    item_id="qa-2",
                    status="fail",
                    notes="Failed",
                )
            tracker.complete_execution(exec_id)

        executions, stats = tracker.get_checklist_history("qa-comprehensive")

        assert len(executions) == 5
        assert stats["total_executions"] == 5
        assert stats["pass_rate"] == 0.6  # 3 passed out of 5
        assert stats["avg_duration_ms"] > 0
        assert len(stats["most_failed_items"]) > 0

    def test_get_checklist_history_empty(self, tmp_path):
        """Test get_checklist_history with no executions."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        executions, stats = tracker.get_checklist_history("nonexistent")

        assert len(executions) == 0
        assert stats["total_executions"] == 0
        assert stats["pass_rate"] == 0.0

    def test_get_compliance_report_generates_metrics(self, tmp_path):
        """Test get_compliance_report generates aggregate metrics."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Create executions for different checklists
        for checklist in ["qa", "security", "performance"]:
            for i in range(3):
                exec_id = tracker.track_execution(
                    checklist_name=checklist,
                    checklist_version="1.0",
                    artifact_type="story",
                    artifact_id=f"{i}.1",
                    executed_by="Amelia",
                )
                tracker.record_item_result(
                    execution_id=exec_id, item_id="test-1", status="pass"
                )
                tracker.complete_execution(exec_id)

        report = tracker.get_compliance_report()

        assert report["total_executions"] == 9
        assert report["overall_pass_rate"] == 1.0
        assert len(report["pass_rate_by_checklist"]) == 3

    def test_get_compliance_report_filtered_by_artifact_type(self, tmp_path):
        """Test get_compliance_report filters by artifact type."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Create story executions
        exec1 = tracker.track_execution(
            checklist_name="qa",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="Amelia",
        )
        tracker.record_item_result(execution_id=exec1, item_id="qa-1", status="pass")
        tracker.complete_execution(exec1)

        # Create epic execution
        exec2 = tracker.track_execution(
            checklist_name="qa",
            checklist_version="1.0",
            artifact_type="epic",
            artifact_id="1",
            executed_by="John",
        )
        tracker.record_item_result(execution_id=exec2, item_id="qa-1", status="pass")
        tracker.complete_execution(exec2)

        report = tracker.get_compliance_report(artifact_type="story")

        assert report["total_executions"] == 1

    def test_get_pending_checklists(self, tmp_path):
        """Test get_pending_checklists returns missing checklists."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Execute only one checklist
        exec_id = tracker.track_execution(
            checklist_name="qa-comprehensive",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            epic_num=12,
            story_num=1,
        )
        tracker.record_item_result(execution_id=exec_id, item_id="qa-1", status="pass")
        tracker.complete_execution(exec_id)

        required = ["qa-comprehensive", "security-checklist", "performance-checklist"]
        pending = tracker.get_pending_checklists(
            epic_num=12, story_num=1, required_checklists=required
        )

        assert len(pending) == 2
        assert "security-checklist" in pending
        assert "performance-checklist" in pending


class TestBatchOperations:
    """Test batch operation methods."""

    def test_track_batch_execution_atomic(self, tmp_path):
        """Test track_batch_execution is atomic."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        item_results = [
            {"item_id": "qa-1", "status": "pass"},
            {"item_id": "qa-2", "status": "fail", "notes": "Missing tests"},
            {"item_id": "qa-3", "status": "skip", "notes": "Not applicable"},
        ]

        execution_id = tracker.track_batch_execution(
            checklist_name="qa-comprehensive",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
            item_results=item_results,
            epic_num=12,
            story_num=1,
        )

        assert execution_id > 0

        # Verify all items recorded and execution completed
        result = tracker.get_execution_results(execution_id)
        assert len(result.item_results) == 3
        assert result.overall_status == "fail"
        assert result.completed_at is not None

    def test_track_batch_execution_rollback_on_error(self, tmp_path):
        """Test track_batch_execution rolls back on validation error."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Invalid status should cause rollback
        item_results = [
            {"item_id": "qa-1", "status": "pass"},
            {"item_id": "qa-2", "status": "invalid"},  # Invalid status
        ]

        with pytest.raises(ValueError):
            tracker.track_batch_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                item_results=item_results,
            )

        # Verify no records created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM checklist_executions")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_import_execution_results_validates_data(self, tmp_path):
        """Test import_execution_results validates required fields."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Missing required fields should fail
        data = {
            "checklist_name": "qa-comprehensive",
            "checklist_version": "1.0",
            # Missing other required fields
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            tracker.import_execution_results(data)

    def test_import_execution_results_successful(self, tmp_path):
        """Test import_execution_results imports complete execution."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        data = {
            "checklist_name": "qa-comprehensive",
            "checklist_version": "1.0",
            "artifact_type": "story",
            "artifact_id": "12.1",
            "executed_by": "Amelia",
            "epic_num": 12,
            "story_num": 1,
            "item_results": [
                {"item_id": "qa-1", "status": "pass"},
                {"item_id": "qa-2", "status": "fail", "notes": "Missing tests"},
            ],
            "notes": "Imported from CLI",
        }

        execution_id = tracker.import_execution_results(data)

        result = tracker.get_execution_results(execution_id)
        assert result.checklist_name == "qa-comprehensive"
        assert len(result.item_results) == 2
        assert result.notes == "Imported from CLI"


class TestPerformance:
    """Test performance requirements."""

    def test_track_execution_performance(self, tmp_path):
        """Test track_execution completes in <50ms."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        start = datetime.now()
        tracker.track_execution(
            checklist_name="qa-comprehensive",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="12.1",
            executed_by="Amelia",
        )
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        assert duration_ms < 50

    def test_record_item_result_performance(self, tmp_path):
        """Test record_item_result completes in <10ms."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        start = datetime.now()
        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        assert duration_ms < 10

    def test_query_execution_results_performance(self, tmp_path):
        """Test get_execution_results completes in <50ms."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        for i in range(10):
            tracker.record_item_result(
                execution_id=execution_id, item_id=f"test-{i}", status="pass"
            )

        tracker.complete_execution(execution_id)

        start = datetime.now()
        result = tracker.get_execution_results(execution_id)
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        assert duration_ms < 50

    def test_batch_insert_performance(self, tmp_path):
        """Test batch insert of 100 items completes in <500ms."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        item_results = [{"item_id": f"test-{i}", "status": "pass"} for i in range(100)]

        start = datetime.now()
        tracker.track_batch_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
            item_results=item_results,
        )
        duration_ms = (datetime.now() - start).total_seconds() * 1000

        assert duration_ms < 500


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_multiple_executions_same_checklist(self, tmp_path):
        """Test multiple executions of same checklist on same artifact."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        # Execute same checklist twice
        for i in range(2):
            exec_id = tracker.track_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                epic_num=12,
                story_num=1,
            )
            tracker.record_item_result(
                execution_id=exec_id, item_id="qa-1", status="pass"
            )
            tracker.complete_execution(exec_id)

        # Both should be recorded
        results = tracker.get_story_checklists(epic_num=12, story_num=1)
        assert len(results) == 2

    def test_empty_notes_allowed_for_pass(self, tmp_path):
        """Test notes not required for pass status."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        # Pass without notes should work
        tracker.record_item_result(
            execution_id=execution_id, item_id="test-1", status="pass"
        )

    def test_evidence_path_stored(self, tmp_path):
        """Test evidence_path is stored and retrieved."""
        db_path = tmp_path / "test.db"
        tracker = ChecklistTracker(db_path)

        execution_id = tracker.track_execution(
            checklist_name="test",
            checklist_version="1.0",
            artifact_type="story",
            artifact_id="1.1",
            executed_by="test",
        )

        tracker.record_item_result(
            execution_id=execution_id,
            item_id="test-1",
            status="pass",
            evidence_path="/path/to/screenshot.png",
            evidence_metadata={"size": 12345, "format": "png"},
        )

        tracker.complete_execution(execution_id)
        result = tracker.get_execution_results(execution_id)

        assert result.item_results[0].evidence_path == "/path/to/screenshot.png"
        assert result.item_results[0].evidence_metadata == {
            "size": 12345,
            "format": "png",
        }


@pytest.fixture
def tmp_path():
    """Provide a temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
