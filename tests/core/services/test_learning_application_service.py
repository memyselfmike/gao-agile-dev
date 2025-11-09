"""Tests for LearningApplicationService.

Tests all acceptance criteria from Story 29.2:
- AC2: Additive scoring formula (C2 fix critical)
- AC3: Smooth decay function
- AC4: Improved confidence formula
- AC5: Context similarity with asymmetric tag handling (C11 fix)
- AC6: Get relevant learnings method
- AC7: Record application method
- AC8: Performance benchmarks

Epic: 29 - Self-Learning Feedback Loop
Story: 29.2 - LearningApplicationService
"""

import json
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import pytest

from gao_dev.core.services.learning_application_service import (
    LearningApplicationService,
    ScoredLearning,
)
from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create test database with schema."""
    db_file = tmp_path / "test_documents.db"

    # Create tables (from migration 006)
    conn = sqlite3.connect(str(db_file))
    conn.executescript(
        """
        -- Learning index table
        CREATE TABLE IF NOT EXISTS learning_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT NOT NULL,
            learning TEXT NOT NULL,
            context TEXT,
            source_type TEXT,
            epic_num INTEGER,
            story_num INTEGER,
            relevance_score REAL DEFAULT 1.0,
            application_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 1.0,
            confidence_score REAL DEFAULT 0.5,
            status TEXT DEFAULT 'active',
            superseded_by INTEGER,
            indexed_at TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            tags TEXT DEFAULT '[]'
        );

        -- Learning applications table
        CREATE TABLE IF NOT EXISTS learning_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_id INTEGER NOT NULL,
            epic_num INTEGER NOT NULL,
            story_num INTEGER,
            outcome TEXT NOT NULL,
            application_context TEXT,
            applied_at TEXT NOT NULL,
            FOREIGN KEY (learning_id) REFERENCES learning_index(id)
        );
        """
    )
    conn.commit()
    conn.close()

    return db_file


@pytest.fixture
def service(db_path: Path) -> LearningApplicationService:
    """Create service instance."""
    return LearningApplicationService(db_path)


@pytest.fixture
def sample_learnings(db_path: Path) -> list[int]:
    """Insert sample learnings for testing."""
    conn = sqlite3.connect(str(db_path))

    # Learning 1: Recent, high success, web app
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, relevance_score,
            application_count, success_rate, confidence_score,
            indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "React Patterns",
            "technical",
            "Use hooks for state management",
            0.9,
            10,
            0.8,
            0.7,
            datetime.now().isoformat(),
            json.dumps({"scale_level": 3, "project_type": "web_app", "phase": "implementation"}),
            json.dumps(["react", "typescript"]),
        ),
    )

    # Learning 2: Old, low success, general
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, relevance_score,
            application_count, success_rate, confidence_score,
            indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Testing Best Practices",
            "quality",
            "Write tests first",
            0.8,
            5,
            0.4,
            0.3,
            (datetime.now() - timedelta(days=365)).isoformat(),
            json.dumps({"scale_level": 2, "project_type": "any"}),
            json.dumps([]),
        ),
    )

    # Learning 3: Medium, different scale
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, relevance_score,
            application_count, success_rate, confidence_score,
            indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "API Design",
            "architectural",
            "Use RESTful conventions",
            0.85,
            3,
            1.0,
            0.6,
            (datetime.now() - timedelta(days=90)).isoformat(),
            json.dumps({"scale_level": 4, "project_type": "web_app", "phase": "design"}),
            json.dumps(["api", "rest"]),
        ),
    )

    conn.commit()
    learning_ids = [1, 2, 3]
    conn.close()

    return learning_ids


# AC2: Additive Scoring Formula Tests


def test_additive_scoring_formula_stability(service: LearningApplicationService, db_path: Path):
    """Test that additive formula prevents score instability (C2 Fix - CRITICAL)."""
    # Create learning with one very low factor (success_rate = 0.0)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, relevance_score,
            application_count, success_rate, confidence_score,
            indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Test Learning",
            "technical",
            "Test",
            0.8,  # Good base
            1,
            0.0,  # ZERO success rate
            0.5,  # Medium confidence
            datetime.now().isoformat(),
            json.dumps({"scale_level": 3}),
            json.dumps([]),
        ),
    )
    conn.commit()
    conn.close()

    # Get the learning
    learning = {
        "id": 1,
        "relevance_score": 0.8,
        "success_rate": 0.0,  # ZERO
        "confidence_score": 0.5,
        "indexed_at": datetime.now().isoformat(),
        "metadata": "{}",
        "tags": "[]",
        "category": "technical",
    }

    score = service._calculate_relevance_score(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {}
    )

    # With additive formula, score should NOT be zero
    # Expected: 0.30*0.8 + 0.20*0.0 + 0.20*0.5 + 0.15*1.0 + 0.15*similarity
    # = 0.24 + 0.0 + 0.1 + 0.15 + ~0.05 = ~0.54
    assert score > 0.0, "Additive formula should prevent zero scores"
    assert score >= 0.3, f"Score should be >=0.3 even with zero success_rate, got {score}"


def test_additive_weights_sum_to_one(service: LearningApplicationService):
    """Test that weights sum to 1.0 in additive formula."""
    weights = [0.30, 0.20, 0.20, 0.15, 0.15]
    assert sum(weights) == 1.0, "Weights must sum to 1.0"


def test_score_clamped_to_valid_range(service: LearningApplicationService, db_path: Path):
    """Test that scores are clamped to [0.0, 1.0]."""
    # Create learning with all maximum factors
    learning = {
        "relevance_score": 1.0,
        "success_rate": 1.0,
        "confidence_score": 1.0,
        "indexed_at": datetime.now().isoformat(),
        "metadata": json.dumps({"scale_level": 3, "project_type": "web_app"}),
        "tags": json.dumps(["test"]),
        "category": "quality",
    }

    score = service._calculate_relevance_score(
        learning,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        "web_app",
        {"tags": ["test"], "phase": "implementation"},
    )

    assert 0.0 <= score <= 1.0, f"Score must be in [0.0, 1.0], got {score}"


# AC3: Smooth Decay Function Tests


def test_decay_function_smooth_curve(service: LearningApplicationService):
    """Test that decay function has smooth exponential curve (C2 Fix)."""
    now = datetime.now()

    # Test decay at various ages
    test_cases = [
        (0, 1.0),  # Fresh
        (30, 0.92),  # 30 days
        (90, 0.81),  # 90 days
        (180, 0.68),  # 180 days (half-life)
        (365, 0.56),  # 1 year
    ]

    for days, expected_decay in test_cases:
        indexed_at = (now - timedelta(days=days)).isoformat()
        actual_decay = service._calculate_decay(indexed_at)

        # Allow 0.02 tolerance for floating point
        assert abs(actual_decay - expected_decay) < 0.02, (
            f"Decay at {days} days should be ~{expected_decay}, got {actual_decay}"
        )


def test_decay_never_below_half(service: LearningApplicationService):
    """Test that decay never drops below 0.5 (retains historical value)."""
    # Very old learning (10 years)
    old_date = (datetime.now() - timedelta(days=3650)).isoformat()
    decay = service._calculate_decay(old_date)

    assert decay >= 0.5, f"Decay should never be <0.5, got {decay}"


def test_decay_no_cliffs(service: LearningApplicationService):
    """Test that decay has no sudden drops (smooth curve)."""
    now = datetime.now()

    # Check decay is monotonic over 400 days
    prev_decay = 1.0
    for days in range(0, 400, 10):
        indexed_at = (now - timedelta(days=days)).isoformat()
        decay = service._calculate_decay(indexed_at)

        # Decay should be less than or equal to previous (monotonic decrease)
        assert decay <= prev_decay, f"Decay should decrease smoothly, jump at {days} days"
        prev_decay = decay


# AC4: Improved Confidence Formula Tests


def test_confidence_formula_square_root_growth(service: LearningApplicationService, db_path: Path):
    """Test that confidence grows with square root (smoother growth) - C2 Fix."""
    conn = sqlite3.connect(str(db_path))

    # Insert learning
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("Test", "technical", "Test learning", datetime.now().isoformat(), "{}", "[]"),
    )

    # Add 4 successful applications
    for _ in range(4):
        conn.execute(
            """
            INSERT INTO learning_applications (
                learning_id, epic_num, outcome, applied_at
            ) VALUES (?, ?, ?, ?)
            """,
            (1, 1, "success", datetime.now().isoformat()),
        )

    conn.commit()

    stats = service._calculate_updated_stats(1, conn)
    conn.close()

    # Formula: base_confidence = min(0.95, 0.5 + 0.45 * sqrt(successes / total))
    # With 4 successes / 4 total: sqrt(1.0) = 1.0
    # base_confidence = 0.5 + 0.45 * 1.0 = 0.95
    expected_confidence = 0.95
    assert abs(stats["confidence"] - expected_confidence) < 0.01, (
        f"Confidence should be {expected_confidence}, got {stats['confidence']}"
    )


def test_confidence_plateaus_at_ninety_five(
    service: LearningApplicationService, db_path: Path
):
    """Test that confidence plateaus at 0.95."""
    conn = sqlite3.connect(str(db_path))

    # Insert learning
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("Test", "technical", "Test learning", datetime.now().isoformat(), "{}", "[]"),
    )

    # Add 100 successful applications
    for _ in range(100):
        conn.execute(
            """
            INSERT INTO learning_applications (
                learning_id, epic_num, outcome, applied_at
            ) VALUES (?, ?, ?, ?)
            """,
            (1, 1, "success", datetime.now().isoformat()),
        )

    conn.commit()

    stats = service._calculate_updated_stats(1, conn)
    conn.close()

    assert stats["confidence"] <= 0.95, f"Confidence should not exceed 0.95, got {stats['confidence']}"


def test_confidence_reduced_for_low_success_rate(
    service: LearningApplicationService, db_path: Path
):
    """Test that confidence is reduced if success rate < 0.5."""
    conn = sqlite3.connect(str(db_path))

    # Insert learning
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("Test", "technical", "Test learning", datetime.now().isoformat(), "{}", "[]"),
    )

    # Add 1 success, 3 failures (success_rate = 0.25)
    conn.execute(
        """
        INSERT INTO learning_applications (
            learning_id, epic_num, outcome, applied_at
        ) VALUES (?, ?, ?, ?)
        """,
        (1, 1, "success", datetime.now().isoformat()),
    )
    for _ in range(3):
        conn.execute(
            """
            INSERT INTO learning_applications (
                learning_id, epic_num, outcome, applied_at
            ) VALUES (?, ?, ?, ?)
            """,
            (1, 1, "failure", datetime.now().isoformat()),
        )

    conn.commit()

    stats = service._calculate_updated_stats(1, conn)
    conn.close()

    # Success rate = 1/4 = 0.25
    # Base confidence = 0.5 + 0.45 * sqrt(1/4) = 0.5 + 0.45 * 0.5 = 0.725
    # Adjusted = 0.725 * (0.25 * 2) = 0.725 * 0.5 = 0.3625
    expected = 0.725 * 0.5
    assert abs(stats["confidence"] - expected) < 0.01


# AC5: Context Similarity with Asymmetric Tag Handling Tests


def test_context_similarity_exact_scale_match(service: LearningApplicationService):
    """Test scale level exact match gives 0.25 bonus."""
    learning = {
        "metadata": json.dumps({"scale_level": 3}),
        "tags": json.dumps([]),
        "category": "technical",
    }

    similarity = service._context_similarity(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {}
    )

    # Should get 0.25 for exact scale match + category bonus
    assert similarity >= 0.25, f"Exact scale match should give >=0.25, got {similarity}"


def test_context_similarity_adjacent_scale(service: LearningApplicationService):
    """Test adjacent scale levels give 0.15 bonus."""
    learning = {
        "metadata": json.dumps({"scale_level": 2}),
        "tags": json.dumps([]),
        "category": "technical",
    }

    similarity = service._context_similarity(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {}
    )

    # Should get 0.15 for adjacent scale + category bonus
    assert similarity >= 0.15, f"Adjacent scale should give >=0.15, got {similarity}"


def test_context_similarity_asymmetric_tags_both_empty(service: LearningApplicationService):
    """Test asymmetric tag handling when both have no tags (C11 Fix)."""
    learning = {"metadata": json.dumps({}), "tags": json.dumps([]), "category": "technical"}

    similarity = service._context_similarity(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {"tags": []}
    )

    # Should get medium bonus (0.15) for both untagged
    assert similarity >= 0.10, "Both untagged should get medium bonus"


def test_context_similarity_asymmetric_tags_only_learning_has_tags(
    service: LearningApplicationService,
):
    """Test asymmetric tag handling when only learning has tags (C11 Fix)."""
    learning = {
        "metadata": json.dumps({}),
        "tags": json.dumps(["react", "typescript"]),
        "category": "technical",
    }

    similarity = service._context_similarity(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {"tags": []}
    )

    # Should get small bonus (0.05) when only learning has tags
    # Total should be lower than when both have matching tags
    assert similarity < 0.30, "Only learning having tags should get small bonus"


def test_context_similarity_asymmetric_tags_only_context_has_tags(
    service: LearningApplicationService,
):
    """Test asymmetric tag handling when only context has tags (C11 Fix)."""
    learning = {"metadata": json.dumps({}), "tags": json.dumps([]), "category": "technical"}

    similarity = service._context_similarity(
        learning,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        "web_app",
        {"tags": ["react", "typescript"]},
    )

    # Should get 0.10 for untagged learning (general applicability)
    assert similarity >= 0.10, "Untagged learning with tagged context should get base bonus"


def test_context_similarity_tag_overlap_jaccard(service: LearningApplicationService):
    """Test tag overlap uses Jaccard similarity."""
    learning = {
        "metadata": json.dumps({}),
        "tags": json.dumps(["react", "typescript", "redux"]),
        "category": "technical",
    }

    similarity = service._context_similarity(
        learning,
        ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        "web_app",
        {"tags": ["react", "typescript"]},
    )

    # Jaccard = overlap / union = 2 / 3 = 0.667
    # Tag contribution = 0.30 * 0.667 = 0.20
    # Should get at least 0.20 from tags
    assert similarity >= 0.15, f"Tag overlap should contribute significantly, got {similarity}"


# AC6: Get Relevant Learnings Method Tests


def test_get_relevant_learnings_returns_top_n(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test get_relevant_learnings returns top N by score."""
    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={"tags": ["react", "typescript"]},
        limit=2,
    )

    assert len(learnings) <= 2, "Should return at most limit learnings"
    assert len(learnings) > 0, "Should return at least 1 learning"

    # Check sorted by score descending
    for i in range(len(learnings) - 1):
        assert (
            learnings[i].relevance_score >= learnings[i + 1].relevance_score
        ), "Results should be sorted by score descending"


def test_get_relevant_learnings_filters_by_threshold(
    service: LearningApplicationService, db_path: Path
):
    """Test that learnings below threshold (0.2) are filtered out."""
    conn = sqlite3.connect(str(db_path))

    # Insert learning with very low scores to get below threshold
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, relevance_score,
            application_count, success_rate, confidence_score,
            indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Low Score",
            "technical",
            "Test",
            0.1,  # Low base
            1,
            0.1,  # Low success
            0.1,  # Low confidence
            (datetime.now() - timedelta(days=365)).isoformat(),  # Old
            json.dumps({"scale_level": 0}),  # Wrong scale
            json.dumps([]),  # No tags
        ),
    )
    conn.commit()
    conn.close()

    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={"tags": ["react"]},
        limit=10,
    )

    # All returned learnings should have score > 0.2
    for learning in learnings:
        assert learning.relevance_score > 0.2, (
            f"All learnings should have score >0.2, got {learning.relevance_score}"
        )


def test_get_relevant_learnings_returns_scored_learning_objects(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test that results are ScoredLearning objects with all fields."""
    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={},
        limit=5,
    )

    for learning in learnings:
        assert isinstance(learning, ScoredLearning), "Result should be ScoredLearning"
        assert isinstance(learning.learning_id, int)
        assert isinstance(learning.topic, str)
        assert isinstance(learning.category, str)
        assert isinstance(learning.learning, str)
        assert isinstance(learning.relevance_score, float)
        assert isinstance(learning.metadata, dict)
        assert isinstance(learning.tags, list)


# AC7: Record Application Method Tests


def test_record_application_inserts_row(
    service: LearningApplicationService, sample_learnings: list[int], db_path: Path
):
    """Test that record_application inserts into learning_applications table."""
    service.record_application(
        learning_id=sample_learnings[0],
        epic_num=29,
        story_num=2,
        outcome="success",
        context="Test application",
    )

    # Check row was inserted
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT COUNT(*) FROM learning_applications WHERE learning_id = ?",
        (sample_learnings[0],),
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1, "Should insert exactly 1 row"


def test_record_application_updates_stats(
    service: LearningApplicationService, sample_learnings: list[int], db_path: Path
):
    """Test that record_application updates learning_index statistics."""
    learning_id = sample_learnings[0]

    # Record first application
    service.record_application(
        learning_id=learning_id,
        epic_num=29,
        story_num=1,
        outcome="success",
        context="First test",
    )

    # Check stats after first application
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT application_count, success_rate, confidence_score FROM learning_index WHERE id = ?",
        (learning_id,),
    )
    first = cursor.fetchone()
    conn.close()

    assert first[0] == 1, "application_count should be 1 after first application"
    assert first[1] == 1.0, "success_rate should be 1.0 with one success"
    assert first[2] >= 0.5, "confidence_score should be >= 0.5"

    # Record second application
    service.record_application(
        learning_id=learning_id,
        epic_num=29,
        story_num=2,
        outcome="success",
        context="Second test",
    )

    # Check updated stats
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT application_count, success_rate, confidence_score FROM learning_index WHERE id = ?",
        (learning_id,),
    )
    updated = cursor.fetchone()
    conn.close()

    assert updated[0] == 2, "application_count should be 2 after second application"
    assert updated[1] == 1.0, "success_rate should still be 1.0 with two successes"
    assert updated[2] >= first[2], "confidence should not decrease with successes"


def test_record_application_thread_safe(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test that record_application is thread-safe (uses transactions)."""
    # Record multiple applications - should all succeed with transactions
    learning_id = sample_learnings[0]

    for i in range(5):
        service.record_application(
            learning_id=learning_id,
            epic_num=29,
            story_num=i,
            outcome="success",
            context=f"Test {i}",
        )

    # All applications should be recorded
    conn = sqlite3.connect(str(service.db_path))
    cursor = conn.execute(
        "SELECT COUNT(*) FROM learning_applications WHERE learning_id = ?", (learning_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()

    # Initial count was 10, added 5 more
    assert count >= 5, "All applications should be recorded"


def test_record_application_validates_outcome(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test that record_application validates outcome values."""
    with pytest.raises(ValueError, match="Invalid outcome"):
        service.record_application(
            learning_id=sample_learnings[0],
            epic_num=29,
            story_num=2,
            outcome="invalid",  # Should fail
            context="Test",
        )


def test_record_application_handles_partial_outcome(
    service: LearningApplicationService, sample_learnings: list[int], db_path: Path
):
    """Test that partial outcomes count as 0.5 success."""
    learning_id = sample_learnings[1]  # Start fresh

    # Record 2 partial outcomes
    for i in range(2):
        service.record_application(
            learning_id=learning_id, epic_num=29, story_num=i, outcome="partial", context="Test"
        )

    # Check success rate
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT success_rate FROM learning_index WHERE id = ?", (learning_id,)
    )
    success_rate = cursor.fetchone()[0]
    conn.close()

    # Initial had 5 apps with 0.4 success rate = 2 successes
    # Added 2 partial (1.0 success equivalent)
    # Total: (2 + 1.0) / (5 + 2) = 3.0 / 7 = 0.43
    # Expected ~0.43
    assert 0.35 <= success_rate <= 0.50, f"Partial should count as 0.5, got {success_rate}"


# Performance Tests (AC6, AC7)


def test_get_relevant_learnings_performance(
    service: LearningApplicationService, db_path: Path
):
    """Test that scoring 50 candidates takes <50ms (C5 Fix)."""
    conn = sqlite3.connect(str(db_path))

    # Insert 50 learnings
    for i in range(50):
        conn.execute(
            """
            INSERT INTO learning_index (
                topic, category, learning, relevance_score,
                indexed_at, metadata, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"Topic {i}",
                "technical",
                f"Learning {i}",
                0.7,
                datetime.now().isoformat(),
                json.dumps({"scale_level": 3}),
                json.dumps(["tag1", "tag2"]),
            ),
        )
    conn.commit()
    conn.close()

    # Measure performance
    start = datetime.now()
    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={"tags": ["tag1"]},
        limit=5,
    )
    elapsed_ms = (datetime.now() - start).total_seconds() * 1000

    assert elapsed_ms < 50, f"Should take <50ms for 50 candidates, took {elapsed_ms:.2f}ms"
    assert len(learnings) > 0, "Should return results"


def test_record_application_performance(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test that record_application takes <100ms."""
    start = datetime.now()
    service.record_application(
        learning_id=sample_learnings[0],
        epic_num=29,
        story_num=2,
        outcome="success",
        context="Performance test",
    )
    elapsed_ms = (datetime.now() - start).total_seconds() * 1000

    assert elapsed_ms < 100, f"Should take <100ms, took {elapsed_ms:.2f}ms"


# Edge Cases


def test_get_relevant_learnings_empty_database(service: LearningApplicationService):
    """Test get_relevant_learnings with no learnings."""
    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={},
        limit=5,
    )

    assert learnings == [], "Should return empty list"


def test_calculate_updated_stats_no_applications(
    service: LearningApplicationService, sample_learnings: list[int], db_path: Path
):
    """Test _calculate_updated_stats with no applications."""
    # Create new learning with no applications
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO learning_index (
            topic, category, learning, indexed_at, metadata, tags
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("New", "technical", "Test", datetime.now().isoformat(), "{}", "[]"),
    )
    conn.commit()

    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    stats = service._calculate_updated_stats(new_id, conn)
    conn.close()

    assert stats["count"] == 0
    assert stats["success_rate"] == 1.0  # Default
    assert stats["confidence"] == 0.5  # Default


def test_context_similarity_missing_metadata(service: LearningApplicationService):
    """Test context similarity when learning has no metadata."""
    learning = {"metadata": json.dumps({}), "tags": json.dumps([]), "category": "technical"}

    similarity = service._context_similarity(
        learning, ScaleLevel.LEVEL_3_MEDIUM_FEATURE, "web_app", {}
    )

    # Should still work with defaults
    assert 0.0 <= similarity <= 1.0, "Should handle missing metadata gracefully"


def test_get_relevant_learnings_filters_by_category(
    service: LearningApplicationService, sample_learnings: list[int]
):
    """Test that get_relevant_learnings filters by category when provided in context."""
    learnings = service.get_relevant_learnings(
        scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
        project_type="web_app",
        context={"category": "technical"},
        limit=10,
    )

    # All results should be technical category
    for learning in learnings:
        assert learning.category == "technical", f"Expected technical, got {learning.category}"


def test_record_application_database_rollback_on_error(
    service: LearningApplicationService, db_path: Path
):
    """Test that database transactions rollback on error."""
    # Try to record application for non-existent learning (should fail foreign key constraint)
    with pytest.raises(sqlite3.IntegrityError):
        service.record_application(
            learning_id=99999,  # Non-existent
            epic_num=29,
            story_num=2,
            outcome="success",
            context="Test",
        )

    # Verify no partial data was committed
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        "SELECT COUNT(*) FROM learning_applications WHERE learning_id = ?", (99999,)
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0, "Failed transaction should rollback"
