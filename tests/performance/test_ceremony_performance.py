"""Performance validation tests for ceremony system.

Validates that ceremony system meets performance requirements:
- Ceremony trigger evaluation <10ms
- Ceremony execution <10 minutes (with timeout)
- Overall workflow overhead <2%
- Database queries <5ms

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.5 - CLI Commands & Testing (AC7)
"""

import pytest
import sqlite3
import sys
import importlib.util
import time
from pathlib import Path
from datetime import datetime

from gao_dev.core.services.ceremony_trigger_engine import (
    CeremonyTriggerEngine,
    TriggerContext
)
from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel


def load_migration_005():
    """Load migration 005 module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent
        / "gao_dev"
        / "lifecycle"
        / "migrations"
        / "005_add_state_tables.py"
    )
    spec = importlib.util.spec_from_file_location("migration_005", migration_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["migration_005"] = module
    spec.loader.exec_module(module)
    return module.Migration005


Migration005 = load_migration_005()


def create_epic_for_test(conn, epic_num: int, total_stories: int = 10):
    """Create a test epic in the database."""
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute(
        """
        INSERT OR IGNORE INTO epic_state (
            epic_num, title, status, total_stories, completed_stories,
            progress_percentage, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (epic_num, f"Test Epic {epic_num}", "in_progress", total_stories, 0, 0.0, now, now)
    )
    conn.commit()


@pytest.fixture
def setup_database(tmp_path):
    """Setup test database with schema."""
    db_path = tmp_path / ".gao-dev" / "documents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT
        )
        """
    )
    conn.commit()
    Migration005.up(conn)

    # Create test epics for all test cases
    for epic_num in range(1, 11):
        create_epic_for_test(conn, epic_num, total_stories=10)

    conn.close()
    return db_path


class TestCeremonyTriggerEvaluationPerformance:
    """Test ceremony trigger evaluation performance (<10ms)."""

    def test_trigger_evaluation_single_epic_cold(self, setup_database):
        """Measure cold trigger evaluation performance (first run)."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Cold run (no warm-up)
        start = time.perf_counter()
        ceremonies = engine.evaluate_all_triggers(context)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 10, f"Cold evaluation took {duration_ms:.2f}ms (target: <10ms)"
        assert isinstance(ceremonies, list)

    def test_trigger_evaluation_single_epic_warm(self, setup_database):
        """Measure warm trigger evaluation performance (cached)."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Warm up
        engine.evaluate_all_triggers(context)

        # Warm run
        start = time.perf_counter()
        _ceremonies = engine.evaluate_all_triggers(context)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 10, f"Warm evaluation took {duration_ms:.2f}ms (target: <10ms)"
        assert duration_ms < 5, f"Expected warm run <5ms, got {duration_ms:.2f}ms"

    def test_trigger_evaluation_with_existing_ceremonies(self, setup_database):
        """Measure evaluation performance with existing ceremony history."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 1

        # Create 5 existing ceremonies
        for i in range(5):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=epic_num,
                story_num=i+1
            )

        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=6,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Warm up
        engine.evaluate_all_triggers(context)

        # Measure with history
        start = time.perf_counter()
        _ceremonies = engine.evaluate_all_triggers(context)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 10, f"Evaluation with history took {duration_ms:.2f}ms (target: <10ms)"

    def test_trigger_evaluation_all_ceremony_types(self, setup_database):
        """Measure evaluation performance for all ceremony types."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        # Context that could trigger all types
        context = TriggerContext(
            epic_num=2,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=8,  # Completion
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Warm up
        engine.evaluate_all_triggers(context)

        # Measure full evaluation
        start = time.perf_counter()
        _ceremonies = engine.evaluate_all_triggers(context)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 10, f"All-type evaluation took {duration_ms:.2f}ms (target: <10ms)"


class TestCeremonyDatabasePerformance:
    """Test ceremony database query performance (<5ms)."""

    def test_ceremony_count_query_performance(self, setup_database):
        """Measure ceremony count query performance."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 3

        # Create 10 ceremonies
        for i in range(10):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=epic_num
            )

        # Warm up
        engine._get_ceremony_count(epic_num)

        # Measure query
        start = time.perf_counter()
        count = engine._get_ceremony_count(epic_num)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 5, f"Count query took {duration_ms:.2f}ms (target: <5ms)"
        assert count == 10

    def test_last_ceremony_time_query_performance(self, setup_database):
        """Measure last ceremony time query performance."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 4

        # Create ceremonies
        for i in range(5):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=epic_num
            )

        # Warm up
        engine._get_last_ceremony_time(epic_num, "standup")

        # Measure query
        start = time.perf_counter()
        last_time = engine._get_last_ceremony_time(epic_num, "standup")
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 5, f"Last time query took {duration_ms:.2f}ms (target: <5ms)"
        assert last_time is not None

    def test_ceremony_existence_check_performance(self, setup_database):
        """Measure ceremony existence check performance."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 5

        # Create planning ceremony
        service.create_summary(
            ceremony_type="planning",
            summary="Planning session",
            participants="team",
            epic_num=epic_num
        )

        # Warm up
        engine._has_ceremony(epic_num, "planning")

        # Measure query
        start = time.perf_counter()
        has_ceremony = engine._has_ceremony(epic_num, "planning")
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 5, f"Existence check took {duration_ms:.2f}ms (target: <5ms)"
        assert has_ceremony is True

    def test_ceremony_service_get_recent_performance(self, setup_database):
        """Measure CeremonyService.get_recent() performance."""
        db_path = setup_database
        service = CeremonyService(db_path=db_path)

        # Create 20 ceremonies across 3 epics
        for epic_num in range(1, 4):
            for i in range(7):
                service.create_summary(
                    ceremony_type="standup",
                    summary=f"Epic {epic_num} standup {i+1}",
                    participants="team",
                    epic_num=epic_num
                )

        # Warm up
        service.get_recent(limit=10)

        # Measure query
        start = time.perf_counter()
        recent = service.get_recent(limit=10)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 5, f"Get recent took {duration_ms:.2f}ms (target: <5ms)"
        assert len(recent) == 10


class TestCeremonyWorkflowOverhead:
    """Test ceremony workflow overhead (<2%)."""

    def test_workflow_overhead_with_ceremonies(self, setup_database):
        """Measure overhead added by ceremony integration to workflows."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        total_stories = 8
        epic_num = 6

        # Simulate workflow with ceremony checks
        workflow_start = time.perf_counter()

        for story_num in range(1, total_stories + 1):
            # Simulate story implementation (100ms per story)
            time.sleep(0.1)

            # Ceremony trigger evaluation
            context = TriggerContext(
                epic_num=epic_num,
                scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
                stories_completed=story_num,
                total_stories=total_stories,
                quality_gates_passed=True,
                failure_count=0,
                project_type='feature'
            )
            _ceremonies = engine.evaluate_all_triggers(context)

        workflow_duration = time.perf_counter() - workflow_start

        # Expected: 8 stories * 100ms = 800ms
        # Target: <2% overhead = <816ms
        expected_base = 0.8  # 800ms
        max_allowed = expected_base * 1.02  # 2% overhead

        assert workflow_duration < max_allowed, \
            f"Workflow took {workflow_duration:.3f}s (target: <{max_allowed:.3f}s, overhead: {((workflow_duration - expected_base) / expected_base) * 100:.1f}%)"


class TestCeremonyPerformanceBenchmarks:
    """Benchmark tests for ceremony system."""

    def test_trigger_evaluation_at_scale(self, setup_database):
        """Benchmark trigger evaluation with multiple epics."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        # Create 10 epics with 5 ceremonies each
        for epic_num in range(1, 11):
            for i in range(5):
                service.create_summary(
                    ceremony_type="standup",
                    summary=f"Epic {epic_num} standup {i+1}",
                    participants="team",
                    epic_num=epic_num
                )

        # Benchmark evaluation for each epic
        durations = []
        for epic_num in range(1, 11):
            context = TriggerContext(
                epic_num=epic_num,
                scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
                stories_completed=6,
                total_stories=10,
                quality_gates_passed=True,
                failure_count=0,
                project_type='feature'
            )

            start = time.perf_counter()
            _ceremonies = engine.evaluate_all_triggers(context)
            duration_ms = (time.perf_counter() - start) * 1000
            durations.append(duration_ms)

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 10, f"Average evaluation: {avg_duration:.2f}ms (target: <10ms)"
        assert max_duration < 15, f"Max evaluation: {max_duration:.2f}ms (target: <15ms)"

    def test_database_query_batching(self, setup_database):
        """Benchmark multiple database queries in sequence."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 10

        # Create test data
        for i in range(10):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=epic_num
            )

        # Benchmark batch of queries
        start = time.perf_counter()
        count = engine._get_ceremony_count(epic_num)
        last_time = engine._get_last_ceremony_time(epic_num, "standup")
        has_planning = engine._has_ceremony(epic_num, "planning")
        duration_ms = (time.perf_counter() - start) * 1000

        # 3 queries should complete in <15ms total
        assert duration_ms < 15, f"Batch queries took {duration_ms:.2f}ms (target: <15ms)"
        assert count == 10
        assert last_time is not None
        assert has_planning is False
