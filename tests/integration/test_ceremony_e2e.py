"""End-to-end integration tests for ceremony workflows.

Tests complete workflow execution with ceremony integration including:
- Level 2 workflow with ceremonies
- Level 3 workflow with ceremonies
- Safety limits enforcement
- Cooldown enforcement
- Circuit breaker activation

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.5 - CLI Commands & Testing (AC6)
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
    TriggerContext,
    CeremonyType
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


def create_epic_for_test(conn, epic_num: int, total_stories: int = 8):
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
    for epic_num in range(1, 9):
        create_epic_for_test(conn, epic_num, total_stories=10)

    conn.close()
    return db_path


class TestLevel2WorkflowWithCeremonies:
    """Test complete Level 2 workflow with ceremony integration (AC6.1)."""

    def test_level_2_workflow_5_stories_with_retrospective(self, setup_database):
        """
        Level 2 workflow: 5 stories
        - No planning (optional for Level 2)
        - No standups (need >3 stories for standup at every 3 stories)
        - Retrospective at epic completion
        """
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        # Simulate Level 2 workflow: 5 stories
        total_stories = 5
        epic_num = 1

        # Story 1 completed
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=1,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert ceremonies == []  # No ceremonies yet

        # Story 3 completed
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=3,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.STANDUP in ceremonies  # Standup at story 3

        # Record standup
        service.create_summary(
            ceremony_type="standup",
            summary="Progress check at story 3",
            participants="team",
            epic_num=epic_num,
            story_num=3
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Epic completion (5/5 stories)
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=5,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.RETROSPECTIVE in ceremonies  # Retro at completion

        # Record retrospective
        service.create_summary(
            ceremony_type="retrospective",
            summary="Epic 1 completed successfully",
            participants="team",
            decisions="Continue with current approach",
            action_items="Document learnings for next epic",
            epic_num=epic_num
        )
        engine.record_ceremony_execution(epic_num, "retrospective", success=True)

        # Verify ceremony counts
        total_count = engine._get_ceremony_count(epic_num)
        assert total_count == 2  # 1 standup + 1 retrospective
        assert total_count < engine.MAX_CEREMONIES_PER_EPIC  # Within limits


class TestLevel3WorkflowWithCeremonies:
    """Test complete Level 3 workflow with ceremony integration (AC6.2)."""

    def test_level_3_workflow_8_stories_with_all_ceremonies(self, setup_database):
        """
        Level 3 workflow: 8 stories
        - Planning at epic start (required)
        - Standup every 2 stories
        - Mid-epic retrospective at 50% (4 stories)
        - Final retrospective at completion
        """
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        total_stories = 8
        epic_num = 2

        # Epic start - Planning required
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=0,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.PLANNING in ceremonies  # Planning required

        # Record planning
        service.create_summary(
            ceremony_type="planning",
            summary="Epic 2 planning session",
            participants="team",
            decisions="Prioritize stories 1-4 first",
            action_items="Create detailed story descriptions",
            epic_num=epic_num
        )
        engine.record_ceremony_execution(epic_num, "planning", success=True)

        # Story 2 completed - First standup
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=2,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.STANDUP in ceremonies  # Standup every 2 stories

        # Record standup
        service.create_summary(
            ceremony_type="standup",
            summary="Progress check at story 2",
            participants="team",
            epic_num=epic_num,
            story_num=2
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Story 4 completed - Mid-epic checkpoint (50%)
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        # Both standup and retrospective should trigger
        assert CeremonyType.STANDUP in ceremonies  # Every 2 stories
        assert CeremonyType.RETROSPECTIVE in ceremonies  # Mid-epic at 50%

        # Record standup
        service.create_summary(
            ceremony_type="standup",
            summary="Progress check at story 4",
            participants="team",
            epic_num=epic_num,
            story_num=4
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Record mid-epic retrospective
        service.create_summary(
            ceremony_type="retrospective",
            summary="Mid-epic retrospective at 50%",
            participants="team",
            decisions="Adjust approach for remaining stories",
            action_items="Improve test coverage",
            epic_num=epic_num,
            metadata={"checkpoint": "mid"}
        )
        engine.record_ceremony_execution(epic_num, "retrospective", success=True)

        # Story 6 completed - Another standup
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=6,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.STANDUP in ceremonies

        # Record standup
        service.create_summary(
            ceremony_type="standup",
            summary="Progress check at story 6",
            participants="team",
            epic_num=epic_num,
            story_num=6
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Story 8 completed - Epic completion
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=8,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        # Both standup and retrospective should trigger
        assert CeremonyType.STANDUP in ceremonies  # Every 2 stories
        assert CeremonyType.RETROSPECTIVE in ceremonies  # Epic completion

        # Record standup
        service.create_summary(
            ceremony_type="standup",
            summary="Final progress check",
            participants="team",
            epic_num=epic_num,
            story_num=8
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Record final retrospective
        service.create_summary(
            ceremony_type="retrospective",
            summary="Epic 2 completion retrospective",
            participants="team",
            decisions="Apply learnings to next epic",
            action_items="Document patterns and anti-patterns",
            epic_num=epic_num
        )
        engine.record_ceremony_execution(epic_num, "retrospective", success=True)

        # Verify ceremony counts
        total_count = engine._get_ceremony_count(epic_num)
        # 1 planning + 4 standups + 2 retrospectives = 7 ceremonies
        assert total_count == 7
        assert total_count < engine.MAX_CEREMONIES_PER_EPIC  # Within limits


class TestCeremonySafetyLimits:
    """Test ceremony safety mechanisms (AC6.3)."""

    def test_max_ceremonies_limit_enforced(self, setup_database):
        """Verify max 10 ceremonies per epic limit is enforced."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 3
        total_stories = 20

        # Hold 10 ceremonies (max limit)
        for i in range(10):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Ceremony {i+1}",
                participants="team",
                epic_num=epic_num,
                story_num=i+1
            )
            engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Verify count
        count = engine._get_ceremony_count(epic_num)
        assert count == 10

        # Attempt to trigger another ceremony
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=12,
            total_stories=total_stories,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )
        ceremonies = engine.evaluate_all_triggers(context)
        assert ceremonies == []  # No ceremonies trigger (limit reached)

    def test_cooldown_prevents_rapid_retrigger(self, setup_database):
        """Verify cooldown period prevents rapid re-triggering."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 4

        # Hold standup
        service.create_summary(
            ceremony_type="standup",
            summary="First standup",
            participants="team",
            epic_num=epic_num,
            story_num=2
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Immediately try to trigger another standup
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Should trigger based on story count, but cooldown should block it
        should_trigger = engine.should_trigger_standup(context)
        assert should_trigger is True  # Logic says yes

        # But cooldown check should prevent it
        can_trigger = engine._check_cooldown(epic_num, "standup")
        assert can_trigger is False  # Cooldown active (12 hours)

        # Full evaluation should respect cooldown
        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.STANDUP not in ceremonies  # Blocked by cooldown

    def test_circuit_breaker_activates_after_failures(self, setup_database):
        """Verify circuit breaker opens after 3 consecutive failures."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 5

        # Record 3 consecutive failures
        for i in range(3):
            service.create_summary(
                ceremony_type="planning",
                summary=f"Failed planning attempt {i+1}",
                participants="team",
                epic_num=epic_num
            )
            engine.record_ceremony_execution(epic_num, "planning", success=False)

        # Verify circuit breaker is open
        is_open = engine._is_circuit_open(epic_num, "planning")
        assert is_open is True  # Circuit breaker activated

        # Attempt to trigger planning
        context = TriggerContext(
            epic_num=epic_num,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=0,
            total_stories=10,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        ceremonies = engine.evaluate_all_triggers(context)
        assert CeremonyType.PLANNING not in ceremonies  # Blocked by circuit breaker

    def test_circuit_breaker_resets_on_success(self, setup_database):
        """Verify circuit breaker resets after successful execution."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 6

        # Record 2 failures
        for i in range(2):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Failed standup {i+1}",
                participants="team",
                epic_num=epic_num
            )
            engine.record_ceremony_execution(epic_num, "standup", success=False)

        # Verify failures tracked
        key = (epic_num, "standup")
        assert engine.consecutive_failures.get(key, 0) == 2

        # Successful execution
        service.create_summary(
            ceremony_type="standup",
            summary="Successful standup",
            participants="team",
            epic_num=epic_num
        )
        engine.record_ceremony_execution(epic_num, "standup", success=True)

        # Verify failure count reset
        assert key not in engine.consecutive_failures
        is_open = engine._is_circuit_open(epic_num, "standup")
        assert is_open is False  # Circuit breaker closed


class TestCeremonyE2EPerformance:
    """Test ceremony system performance (AC7 baseline)."""

    def test_trigger_evaluation_performance(self, setup_database):
        """Verify trigger evaluation completes in <10ms."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)

        context = TriggerContext(
            epic_num=7,
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            stories_completed=4,
            total_stories=8,
            quality_gates_passed=True,
            failure_count=0,
            project_type='feature'
        )

        # Warm up
        engine.evaluate_all_triggers(context)

        # Measure performance
        start = time.perf_counter()
        ceremonies = engine.evaluate_all_triggers(context)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 10  # <10ms target
        assert isinstance(ceremonies, list)  # Valid result

    def test_ceremony_database_queries_optimized(self, setup_database):
        """Verify database queries complete in <5ms."""
        db_path = setup_database
        engine = CeremonyTriggerEngine(db_path=db_path)
        service = CeremonyService(db_path=db_path)

        epic_num = 8

        # Create some test data
        for i in range(5):
            service.create_summary(
                ceremony_type="standup",
                summary=f"Standup {i+1}",
                participants="team",
                epic_num=epic_num
            )

        # Measure query performance
        start = time.perf_counter()
        count = engine._get_ceremony_count(epic_num)
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 5  # <5ms target
        assert count == 5  # Correct result
