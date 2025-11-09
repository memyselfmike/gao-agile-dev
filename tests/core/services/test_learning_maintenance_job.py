"""Tests for Learning Maintenance Job.

Tests for Story 29.6: Learning Decay & Confidence
"""

import math
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gao_dev.core.services.learning_maintenance_job import (
    LearningMaintenanceJob,
    MaintenanceReport,
)


@pytest.fixture
def test_db(tmp_path):
    """Create test database with learning tables."""
    db_path = tmp_path / "test_learning.db"
    conn = sqlite3.connect(str(db_path))

    # Create learning_index table
    conn.execute(
        """
        CREATE TABLE learning_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT NOT NULL,
            learning TEXT NOT NULL,
            context TEXT,
            source_type TEXT,
            epic_num INTEGER,
            story_num INTEGER,
            relevance_score REAL DEFAULT 1.0,
            success_rate REAL DEFAULT 1.0,
            confidence_score REAL DEFAULT 0.5,
            application_count INTEGER DEFAULT 0,
            decay_factor REAL DEFAULT 1.0,
            status TEXT DEFAULT 'active',
            superseded_by INTEGER,
            indexed_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT,
            tags TEXT
        )
        """
    )

    # Create learning_applications table
    conn.execute(
        """
        CREATE TABLE learning_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_id INTEGER NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER,
            outcome TEXT NOT NULL,
            application_context TEXT,
            applied_at TEXT NOT NULL,
            FOREIGN KEY (learning_id) REFERENCES learning_index (id)
        )
        """
    )

    conn.commit()
    conn.close()

    return db_path


# ============================================================================
# Decay Calculation Tests (AC2 - C10 Fix)
# ============================================================================


def test_decay_calculation_smooth_curve(test_db):
    """Test smooth exponential decay calculation (C2, C10 fix)."""
    job = LearningMaintenanceJob(db_path=test_db)

    # Test various ages
    now = datetime.now()

    # 0 days: 1.0
    decay = job._calculate_decay(now.isoformat())
    assert decay == pytest.approx(1.0, abs=0.01)

    # 30 days: ~0.92
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    decay = job._calculate_decay(thirty_days_ago)
    assert decay == pytest.approx(0.92, abs=0.01)

    # 90 days: ~0.81
    ninety_days_ago = (now - timedelta(days=90)).isoformat()
    decay = job._calculate_decay(ninety_days_ago)
    assert decay == pytest.approx(0.81, abs=0.02)

    # 180 days: ~0.68
    half_year_ago = (now - timedelta(days=180)).isoformat()
    decay = job._calculate_decay(half_year_ago)
    assert decay == pytest.approx(0.68, abs=0.02)

    # 365 days: ~0.56
    one_year_ago = (now - timedelta(days=365)).isoformat()
    decay = job._calculate_decay(one_year_ago)
    assert decay == pytest.approx(0.56, abs=0.02)

    # Very old: should floor at 0.5
    very_old = (now - timedelta(days=3650)).isoformat()
    decay = job._calculate_decay(very_old)
    assert decay >= 0.5
    assert decay == pytest.approx(0.5, abs=0.01)


def test_update_decay_factors(test_db):
    """Test decay factor updates for all active learnings."""
    # Insert test learnings with various ages
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    learnings = [
        (now - timedelta(days=0), "active"),
        (now - timedelta(days=30), "active"),
        (now - timedelta(days=90), "active"),
        (now - timedelta(days=180), "active"),
        (now - timedelta(days=365), "active"),
        (now - timedelta(days=30), "inactive"),  # Should not update
    ]

    for indexed_at, status in learnings:
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, indexed_at, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Test Learning",
                "technical",
                "Test content",
                indexed_at.isoformat(),
                now.isoformat(),
                status,
            ),
        )

    conn.commit()
    conn.close()

    # Run decay update
    job = LearningMaintenanceJob(db_path=test_db)
    with job._get_connection() as conn:
        updated = job._update_decay_factors(conn, verbose=False)

    # Should update 5 active learnings (not the inactive one)
    assert updated == 5

    # Verify decay factors
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute(
        """
        SELECT decay_factor, indexed_at
        FROM learning_index
        WHERE status = 'active'
        ORDER BY indexed_at DESC
        """
    )

    rows = cursor.fetchall()
    assert len(rows) == 5

    # Check decay values match expected ranges
    assert rows[0][0] == pytest.approx(1.0, abs=0.01)  # 0 days
    assert rows[1][0] == pytest.approx(0.92, abs=0.02)  # 30 days
    assert rows[2][0] == pytest.approx(0.81, abs=0.02)  # 90 days
    assert rows[3][0] == pytest.approx(0.68, abs=0.02)  # 180 days
    assert rows[4][0] == pytest.approx(0.56, abs=0.02)  # 365 days

    conn.close()


# ============================================================================
# Low Confidence Deactivation Tests (AC3)
# ============================================================================


def test_deactivate_low_confidence_learnings(test_db):
    """Test deactivation of low confidence learnings."""
    # Insert test learnings
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    test_cases = [
        # (confidence, success_rate, app_count, should_deactivate)
        (0.15, 0.2, 5, True),  # Low confidence, low success, enough apps
        (0.15, 0.2, 3, False),  # Low confidence, low success, not enough apps
        (0.3, 0.2, 5, False),  # Confidence too high
        (0.15, 0.5, 5, False),  # Success rate too high
        (0.1, 0.1, 10, True),  # Very low metrics, many apps
    ]

    for i, (confidence, success_rate, app_count, should_deactivate) in enumerate(test_cases):
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, confidence_score, success_rate,
                application_count, indexed_at, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"Test Learning {i}",
                "technical",
                "Test content",
                confidence,
                success_rate,
                app_count,
                now.isoformat(),
                now.isoformat(),
                "active",
            ),
        )

    conn.commit()
    conn.close()

    # Run deactivation
    job = LearningMaintenanceJob(db_path=test_db)
    with job._get_connection() as conn:
        deactivated = job._deactivate_low_confidence_learnings(conn, verbose=False)

    # Should deactivate 2 learnings
    assert deactivated == 2

    # Verify deactivation
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM learning_index
        WHERE status = 'inactive'
        """
    )
    assert cursor.fetchone()[0] == 2

    # Verify metadata was updated
    cursor = conn.execute(
        """
        SELECT metadata
        FROM learning_index
        WHERE status = 'inactive'
        LIMIT 1
        """
    )
    metadata = cursor.fetchone()[0]
    assert "deactivated_reason" in metadata
    assert "Low confidence" in metadata

    conn.close()


# ============================================================================
# Supersede Outdated Learnings Tests (AC4)
# ============================================================================


def test_supersede_outdated_learnings(test_db):
    """Test superseding outdated learnings in same category."""
    # Insert test learnings
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    # Create learnings in same category with different confidence scores
    test_cases = [
        # (indexed_at, confidence, category)
        (now - timedelta(days=30), 0.9, "quality"),  # Newer, higher confidence
        (now - timedelta(days=60), 0.6, "quality"),  # Older, lower (delta > 0.2)
        (now - timedelta(days=90), 0.85, "quality"),  # Old but high confidence
        (now - timedelta(days=10), 0.7, "process"),  # Different category
        (now - timedelta(days=20), 0.4, "process"),  # Same category
    ]

    for indexed_at, confidence, category in test_cases:
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, confidence_score,
                indexed_at, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"Test Learning",
                category,
                "Test content",
                confidence,
                indexed_at.isoformat(),
                now.isoformat(),
                "active",
            ),
        )

    conn.commit()
    conn.close()

    # Run supersession
    job = LearningMaintenanceJob(db_path=test_db)
    with job._get_connection() as conn:
        superseded = job._supersede_outdated_learnings(conn, verbose=False)

    # Should supersede at least 1 learning (older with lower confidence)
    assert superseded >= 1

    # Verify supersession
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM learning_index
        WHERE status = 'superseded'
        """
    )
    assert cursor.fetchone()[0] >= 1

    # Verify superseded_by is set
    cursor = conn.execute(
        """
        SELECT superseded_by
        FROM learning_index
        WHERE status = 'superseded'
        LIMIT 1
        """
    )
    superseded_by = cursor.fetchone()[0]
    assert superseded_by is not None

    conn.close()


# ============================================================================
# Prune Old Applications Tests (AC5)
# ============================================================================


def test_prune_old_applications(test_db):
    """Test pruning of applications older than 1 year."""
    # Insert test applications
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    # First insert a learning
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Test Learning",
            "technical",
            "Test content",
            now.isoformat(),
            now.isoformat(),
            "active",
        ),
    )
    learning_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert applications with various ages
    test_cases = [
        (now - timedelta(days=10), False),  # Recent - keep
        (now - timedelta(days=100), False),  # 3 months - keep
        (now - timedelta(days=364), False),  # Just under 1 year - keep
        (now - timedelta(days=366), True),  # Just over 1 year - prune
        (now - timedelta(days=500), True),  # Old - prune
        (now - timedelta(days=1000), True),  # Very old - prune
    ]

    for applied_at, should_prune in test_cases:
        conn.execute(
            """
            INSERT INTO learning_applications (
                learning_id, epic_num, outcome, applied_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (learning_id, 1, "success", applied_at.isoformat()),
        )

    conn.commit()
    conn.close()

    # Run pruning
    job = LearningMaintenanceJob(db_path=test_db)
    with job._get_connection() as conn:
        pruned = job._prune_old_applications(conn, verbose=False)

    # Should prune 3 old applications
    assert pruned == 3

    # Verify pruning
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM learning_applications
        """
    )
    # Should have 3 remaining (recent ones)
    assert cursor.fetchone()[0] == 3

    conn.close()


# ============================================================================
# Full Maintenance Run Tests
# ============================================================================


def test_run_maintenance_full(test_db):
    """Test full maintenance run."""
    # Insert comprehensive test data
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    # Insert learnings with various characteristics
    for i in range(10):
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, confidence_score, success_rate,
                application_count, indexed_at, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"Learning {i}",
                "technical",
                f"Content {i}",
                0.5,
                0.5,
                0,
                (now - timedelta(days=i * 30)).isoformat(),
                now.isoformat(),
                "active",
            ),
        )

    conn.commit()
    conn.close()

    # Run full maintenance
    job = LearningMaintenanceJob(db_path=test_db)
    report = job.run_maintenance(dry_run=False, verbose=False)

    # Verify report structure
    assert isinstance(report, MaintenanceReport)
    assert report.decay_updates == 10
    assert report.execution_time_ms > 0
    assert report.timestamp


def test_run_maintenance_dry_run(test_db):
    """Test dry run mode (preview without changes)."""
    # Insert test data
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    # Insert a learning that would be deactivated
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, confidence_score, success_rate,
            application_count, indexed_at, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Low Confidence Learning",
            "technical",
            "Test content",
            0.15,
            0.2,
            5,
            now.isoformat(),
            now.isoformat(),
            "active",
        ),
    )

    conn.commit()
    conn.close()

    # Run dry run
    job = LearningMaintenanceJob(db_path=test_db)
    report = job.run_maintenance(dry_run=True, verbose=False)

    # Verify report shows what would happen
    assert isinstance(report, MaintenanceReport)
    assert report.deactivated_count == 1  # Would deactivate 1 learning

    # Verify no actual changes were made
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute(
        """
        SELECT status
        FROM learning_index
        """
    )
    status = cursor.fetchone()[0]
    assert status == "active"  # Should still be active

    conn.close()


# ============================================================================
# Performance Tests (AC1)
# ============================================================================


def test_performance_1000_learnings(test_db):
    """Test maintenance performance with 1000 learnings (target: <5s)."""
    # Insert 1000 learnings
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    learnings = []
    for i in range(1000):
        learnings.append(
            (
                f"Learning {i}",
                "technical",
                f"Content {i}",
                (now - timedelta(days=i % 365)).isoformat(),
                now.isoformat(),
            )
        )

    conn.executemany(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, 'active')
        """,
        learnings,
    )

    conn.commit()
    conn.close()

    # Run maintenance and measure time
    job = LearningMaintenanceJob(db_path=test_db)
    start = time.time()
    report = job.run_maintenance(dry_run=False, verbose=False)
    elapsed = time.time() - start

    # Verify performance (should be <5 seconds)
    assert elapsed < 5.0, f"Maintenance took {elapsed:.2f}s (target: <5s)"
    assert report.execution_time_ms < 5000, f"Report shows {report.execution_time_ms}ms (target: <5000ms)"

    # Verify all learnings were processed
    assert report.decay_updates == 1000


# ============================================================================
# Edge Cases Tests
# ============================================================================


def test_no_learnings(test_db):
    """Test maintenance with no learnings."""
    job = LearningMaintenanceJob(db_path=test_db)
    report = job.run_maintenance(dry_run=False, verbose=False)

    assert report.decay_updates == 0
    assert report.deactivated_count == 0
    assert report.superseded_count == 0
    assert report.pruned_applications == 0


def test_all_recent_learnings(test_db):
    """Test with all learnings being recent."""
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    # Insert recent learnings
    for i in range(5):
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, indexed_at, created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"Recent Learning {i}",
                "technical",
                f"Content {i}",
                now.isoformat(),
                now.isoformat(),
                "active",
            ),
        )

    conn.commit()
    conn.close()

    # Run maintenance
    job = LearningMaintenanceJob(db_path=test_db)
    report = job.run_maintenance(dry_run=False, verbose=False)

    # Verify decay factors are all ~1.0
    conn = sqlite3.connect(str(test_db))
    cursor = conn.execute("SELECT decay_factor FROM learning_index")
    for row in cursor.fetchall():
        assert row[0] == pytest.approx(1.0, abs=0.01)

    conn.close()


def test_verbose_mode(test_db):
    """Test verbose logging mode."""
    # Insert test data
    conn = sqlite3.connect(str(test_db))
    now = datetime.now()

    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, created_at, status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Test Learning",
            "technical",
            "Test content",
            (now - timedelta(days=30)).isoformat(),
            now.isoformat(),
            "active",
        ),
    )

    conn.commit()
    conn.close()

    # Run with verbose mode (should not raise errors)
    job = LearningMaintenanceJob(db_path=test_db)
    report = job.run_maintenance(dry_run=False, verbose=True)

    assert report.decay_updates == 1


# ============================================================================
# Context Manager Tests
# ============================================================================


def test_context_manager(test_db):
    """Test context manager usage."""
    with LearningMaintenanceJob(db_path=test_db) as job:
        # Should work without errors
        decay = job._calculate_decay(datetime.now().isoformat())
        assert decay == pytest.approx(1.0, abs=0.01)
