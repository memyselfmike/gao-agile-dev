"""Unit tests for CeremonyTriggerEngine.

Epic: 28 - Ceremony-Driven Workflow Integration
Story: 28.3 - CeremonyTriggerEngine

Test coverage:
- Trigger evaluation for each ceremony type and scale level
- Safety mechanism enforcement (limits, cooldowns, circuit breaker)
- Edge cases (0 stories, 100%, 50%, quality failures, repeated failures)
- Configuration loading
- TriggerContext validation
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gao_dev.core.services.ceremony_trigger_engine import (
    CeremonyTriggerEngine,
    TriggerContext,
    TriggerType,
    CeremonyType,
)
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel


# Fixtures

@pytest.fixture
def temp_db():
    """Create temporary database with ceremony_summaries table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    # Initialize schema
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE ceremony_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ceremony_type TEXT NOT NULL,
                epic_num INTEGER,
                story_num INTEGER,
                summary TEXT,
                participants TEXT,
                decisions TEXT,
                action_items TEXT,
                held_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE epic_state (
                epic_num INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                total_stories INTEGER DEFAULT 0,
                completed_stories INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE story_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_num INTEGER NOT NULL,
                story_num INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                assignee TEXT,
                priority TEXT DEFAULT 'P2',
                estimate_hours REAL,
                actual_hours REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT,
                UNIQUE(epic_num, story_num),
                FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num)
            )
        """)

    yield db_path

    # Cleanup - Windows requires retry logic for locked files
    import time
    for _ in range(5):
        try:
            db_path.unlink()
            break
        except PermissionError:
            time.sleep(0.1)


@pytest.fixture
def engine(temp_db):
    """Create CeremonyTriggerEngine instance."""
    engine = CeremonyTriggerEngine(db_path=temp_db)
    yield engine
    # Close all connections before cleanup
    engine.close()


@pytest.fixture
def context_level_3():
    """Create TriggerContext for Level 3 Medium Feature."""
    return TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=5,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )


# TriggerContext Tests

def test_trigger_context_creation():
    """Test TriggerContext creation with valid fields."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=3,
        total_stories=5,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert context.epic_num == 1
    assert context.scale_level == ScaleLevel.LEVEL_2_SMALL_FEATURE
    assert context.stories_completed == 3
    assert context.total_stories == 5
    assert context.quality_gates_passed is True
    assert context.failure_count == 0
    assert context.project_type == "feature"
    assert context.story_num is None
    assert context.last_standup is None


def test_trigger_context_validation_negative_stories():
    """Test TriggerContext validation for negative stories_completed."""
    with pytest.raises(ValueError, match="stories_completed must be >= 0"):
        TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=-1,
            total_stories=5,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )


def test_trigger_context_validation_negative_total():
    """Test TriggerContext validation for negative total_stories."""
    with pytest.raises(ValueError, match="total_stories must be >= 0"):
        TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=0,
            total_stories=-1,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )


def test_trigger_context_progress_percentage():
    """Test progress percentage calculation."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=5,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert context.progress_percentage == 0.5


def test_trigger_context_progress_percentage_zero_total():
    """Test progress percentage with 0 total stories."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_0_CHORE,
        stories_completed=0,
        total_stories=0,
        quality_gates_passed=True,
        failure_count=0,
        project_type="chore"
    )

    assert context.progress_percentage == 0.0


# Planning Ceremony Trigger Tests

def test_planning_trigger_level_0_never(engine):
    """Test planning never triggers for Level 0."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_0_CHORE,
        stories_completed=0,
        total_stories=0,
        quality_gates_passed=True,
        failure_count=0,
        project_type="chore"
    )

    assert engine.should_trigger_planning(context) is False


def test_planning_trigger_level_1_never(engine):
    """Test planning never triggers for Level 1."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_1_BUG_FIX,
        stories_completed=0,
        total_stories=1,
        quality_gates_passed=True,
        failure_count=0,
        project_type="bugfix"
    )

    assert engine.should_trigger_planning(context) is False


def test_planning_trigger_level_2_optional(engine):
    """Test planning is optional for Level 2."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=0,
        total_stories=5,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should return False (optional, not automatic)
    assert engine.should_trigger_planning(context) is False


def test_planning_trigger_level_3_required_at_start(engine):
    """Test planning required at epic start for Level 3."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=0,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should trigger (no planning held yet)
    assert engine.should_trigger_planning(context) is True


def test_planning_trigger_level_3_not_if_already_held(engine, temp_db):
    """Test planning doesn't retrigger if already held."""
    # Create planning ceremony record
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            INSERT INTO ceremony_summaries (
                ceremony_type, epic_num, summary, held_at, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("planning", 1, "Epic planning", datetime.now().isoformat(), datetime.now().isoformat())
        )

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=0,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should NOT trigger (planning already held)
    assert engine.should_trigger_planning(context) is False


# Standup Ceremony Trigger Tests

def test_standup_trigger_level_0_never(engine):
    """Test standup never triggers for Level 0."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_0_CHORE,
        stories_completed=0,
        total_stories=0,
        quality_gates_passed=True,
        failure_count=0,
        project_type="chore"
    )

    assert engine.should_trigger_standup(context) is False


def test_standup_trigger_level_1_never(engine):
    """Test standup never triggers for Level 1."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_1_BUG_FIX,
        stories_completed=1,
        total_stories=1,
        quality_gates_passed=True,
        failure_count=0,
        project_type="bugfix"
    )

    assert engine.should_trigger_standup(context) is False


def test_standup_trigger_level_2_every_3_stories(engine):
    """Test standup triggers every 3 stories for Level 2."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=3,
        total_stories=5,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_standup(context) is True


def test_standup_trigger_level_2_not_if_few_stories(engine):
    """Test standup doesn't trigger for Level 2 with <=3 total stories."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=3,
        total_stories=3,  # Only 3 total
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_standup(context) is False


def test_standup_trigger_level_3_every_2_stories(engine):
    """Test standup triggers every 2 stories for Level 3."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=2,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_standup(context) is True


def test_standup_trigger_level_4_every_story(engine):
    """Test standup triggers every story for Level 4."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_4_GREENFIELD,
        stories_completed=1,
        total_stories=50,
        quality_gates_passed=True,
        failure_count=0,
        project_type="greenfield"
    )

    assert engine.should_trigger_standup(context) is True


def test_standup_trigger_level_4_daily(engine):
    """Test standup triggers daily for Level 4."""
    last_standup = datetime.now() - timedelta(hours=25)  # 25 hours ago

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_4_GREENFIELD,
        stories_completed=1,  # Same story count
        total_stories=50,
        quality_gates_passed=True,
        failure_count=0,
        project_type="greenfield",
        last_standup=last_standup
    )

    assert engine.should_trigger_standup(context) is True


def test_standup_trigger_quality_gate_failure(engine):
    """Test standup triggers on quality gate failure."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=1,  # Not at interval
        total_stories=5,
        quality_gates_passed=False,  # Failed
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_standup(context) is True


# Retrospective Ceremony Trigger Tests

def test_retrospective_trigger_level_0_never(engine):
    """Test retrospective never triggers for Level 0."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_0_CHORE,
        stories_completed=0,
        total_stories=0,
        quality_gates_passed=True,
        failure_count=0,
        project_type="chore"
    )

    assert engine.should_trigger_retrospective(context) is False


def test_retrospective_trigger_level_1_repeated_failure(engine):
    """Test retrospective triggers on repeated failure for Level 1."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_1_BUG_FIX,
        stories_completed=0,
        total_stories=1,
        quality_gates_passed=False,
        failure_count=2,  # Failed 2 times
        project_type="bugfix"
    )

    assert engine.should_trigger_retrospective(context) is True


def test_retrospective_trigger_level_1_not_if_single_failure(engine):
    """Test retrospective doesn't trigger on single failure for Level 1."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_1_BUG_FIX,
        stories_completed=0,
        total_stories=1,
        quality_gates_passed=False,
        failure_count=1,  # Only 1 failure
        project_type="bugfix"
    )

    assert engine.should_trigger_retrospective(context) is False


def test_retrospective_trigger_level_2_epic_completion(engine):
    """Test retrospective triggers at epic completion for Level 2."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=5,
        total_stories=5,  # 100% complete
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_retrospective(context) is True


def test_retrospective_trigger_level_3_mid_epic(engine):
    """Test retrospective triggers at 50% for Level 3."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=5,
        total_stories=10,  # 50% complete
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_retrospective(context) is True


def test_retrospective_trigger_level_3_not_if_mid_retro_held(engine, temp_db):
    """Test retrospective doesn't retrigger at 50% if already held."""
    # Create mid-epic retrospective record
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            INSERT INTO ceremony_summaries (
                ceremony_type, epic_num, summary, held_at, created_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "retrospective",
                1,
                "Mid-epic retrospective",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                '{"checkpoint": "mid"}'
            )
        )

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=5,
        total_stories=10,  # 50% complete
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should NOT trigger (mid-epic retro already held)
    assert engine.should_trigger_retrospective(context) is False


# Safety Mechanism Tests

def test_safety_limit_enforcement(engine, temp_db):
    """Test max ceremonies per epic limit enforcement."""
    # Create 10 ceremonies (hit limit)
    with sqlite3.connect(temp_db) as conn:
        for i in range(10):
            conn.execute(
                """
                INSERT INTO ceremony_summaries (
                    ceremony_type, epic_num, summary, held_at, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                ("standup", 1, f"Standup {i}", datetime.now().isoformat(), datetime.now().isoformat())
            )

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=2,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should return empty list (hit safety limit)
    ceremonies = engine.evaluate_all_triggers(context)
    assert ceremonies == []


def test_cooldown_enforcement(engine, temp_db):
    """Test cooldown period enforcement."""
    # Create standup ceremony 5 hours ago (within 12h cooldown)
    recent_time = datetime.now() - timedelta(hours=5)

    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            INSERT INTO ceremony_summaries (
                ceremony_type, epic_num, summary, held_at, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("standup", 1, "Recent standup", recent_time.isoformat(), recent_time.isoformat())
        )

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=2,  # Triggers standup
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Should return empty (cooldown active)
    ceremonies = engine.evaluate_all_triggers(context)
    assert CeremonyType.STANDUP not in ceremonies


def test_circuit_breaker_activation(engine):
    """Test circuit breaker opens after 3 consecutive failures."""
    # Record 3 consecutive failures
    for _ in range(3):
        engine.record_ceremony_execution(
            epic_num=1,
            ceremony_type="standup",
            success=False
        )

    # Circuit should be open
    assert engine._is_circuit_open(1, "standup") is True


def test_circuit_breaker_reset_on_success(engine):
    """Test circuit breaker resets on success."""
    # Record 2 failures
    engine.record_ceremony_execution(epic_num=1, ceremony_type="standup", success=False)
    engine.record_ceremony_execution(epic_num=1, ceremony_type="standup", success=False)

    # Then success
    engine.record_ceremony_execution(epic_num=1, ceremony_type="standup", success=True)

    # Circuit should NOT be open (reset)
    assert engine._is_circuit_open(1, "standup") is False


def test_ceremony_execution_recording(engine):
    """Test ceremony execution recording updates counts."""
    engine.record_ceremony_execution(epic_num=1, ceremony_type="planning", success=True)

    assert engine.ceremony_counts.get(1) == 1
    assert (1, "planning") in engine.last_ceremony_times


# Edge Case Tests

def test_zero_stories_completed(engine):
    """Test trigger evaluation with 0 stories completed."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=0,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    # Planning should trigger (epic start)
    ceremonies = engine.evaluate_all_triggers(context)
    assert CeremonyType.PLANNING in ceremonies

    # Standup should NOT trigger (0 stories)
    assert CeremonyType.STANDUP not in ceremonies

    # Retrospective should NOT trigger (0% progress)
    assert CeremonyType.RETROSPECTIVE not in ceremonies


def test_exactly_50_percent_progress(engine):
    """Test retrospective triggers at exactly 50%."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=10,
        total_stories=20,  # Exactly 50%
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_retrospective(context) is True


def test_100_percent_progress(engine):
    """Test retrospective triggers at 100%."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
        stories_completed=5,
        total_stories=5,  # 100% complete
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    assert engine.should_trigger_retrospective(context) is True


# Configuration Tests

def test_config_loading_default(engine):
    """Test default configuration is used when file not found."""
    assert engine.config["max_per_epic"] == 10
    assert engine.config["cooldown_hours"]["planning"] == 24
    assert engine.config["cooldown_hours"]["standup"] == 12
    assert engine.config["timeout_minutes"] == 10
    assert engine.config["circuit_breaker_threshold"] == 3


def test_config_loading_from_file(temp_db):
    """Test configuration loaded from YAML file."""
    # Create custom config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
max_per_epic: 5
cooldown_hours:
  planning: 12
  standup: 6
  retrospective: 12
timeout_minutes: 5
circuit_breaker_threshold: 2
""")
        config_path = Path(f.name)

    try:
        engine = CeremonyTriggerEngine(db_path=temp_db, config_path=config_path)

        assert engine.config["max_per_epic"] == 5
        assert engine.config["cooldown_hours"]["planning"] == 12
        assert engine.config["cooldown_hours"]["standup"] == 6
        assert engine.config["timeout_minutes"] == 5
        assert engine.config["circuit_breaker_threshold"] == 2
    finally:
        config_path.unlink()


# Integration Tests

def test_evaluate_all_triggers_level_3_epic_start(engine):
    """Test evaluate_all_triggers at epic start for Level 3."""
    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=0,
        total_stories=10,
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    ceremonies = engine.evaluate_all_triggers(context)

    # Should trigger planning (epic start)
    assert CeremonyType.PLANNING in ceremonies

    # Should NOT trigger standup (0 stories)
    assert CeremonyType.STANDUP not in ceremonies

    # Should NOT trigger retrospective (0% progress)
    assert CeremonyType.RETROSPECTIVE not in ceremonies


def test_evaluate_all_triggers_level_3_mid_epic(engine, temp_db):
    """Test evaluate_all_triggers at mid-epic for Level 3."""
    # Planning already held
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            INSERT INTO ceremony_summaries (
                ceremony_type, epic_num, summary, held_at, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("planning", 1, "Planning", datetime.now().isoformat(), datetime.now().isoformat())
        )

    context = TriggerContext(
        epic_num=1,
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        stories_completed=5,
        total_stories=10,  # 50%
        quality_gates_passed=True,
        failure_count=0,
        project_type="feature"
    )

    ceremonies = engine.evaluate_all_triggers(context)

    # Should NOT trigger planning (already held)
    assert CeremonyType.PLANNING not in ceremonies

    # Should NOT trigger standup (5 is odd, interval is 2)
    assert CeremonyType.STANDUP not in ceremonies

    # Should trigger retrospective (50% mid-epic)
    assert CeremonyType.RETROSPECTIVE in ceremonies


def test_context_manager_usage(temp_db):
    """Test CeremonyTriggerEngine used as context manager."""
    with CeremonyTriggerEngine(db_path=temp_db) as engine:
        context = TriggerContext(
            epic_num=1,
            scale_level=ScaleLevel.LEVEL_2_SMALL_FEATURE,
            stories_completed=3,
            total_stories=5,
            quality_gates_passed=True,
            failure_count=0,
            project_type="feature"
        )

        ceremonies = engine.evaluate_all_triggers(context)
        assert isinstance(ceremonies, list)

    # Services should be closed after context exit
    # (No explicit assertion, just verify no errors)
