"""Learning Application Service - Relevance scoring and learning application tracking.

This service calculates relevance scores for learnings using an additive weighted formula
(C2 fix) and tracks learning applications to update statistics.

Epic: 29 - Self-Learning Feedback Loop
Story: 29.2 - LearningApplicationService

Design Pattern: Service Layer
Dependencies: LearningIndexService, sqlite3, structlog
"""

import math
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, NamedTuple

import structlog

from gao_dev.methodologies.adaptive_agile.scale_levels import ScaleLevel

logger = structlog.get_logger()


class ScoredLearning(NamedTuple):
    """A learning with its calculated relevance score."""

    learning_id: int
    topic: str
    category: str
    learning: str
    relevance_score: float
    success_rate: float
    confidence_score: float
    application_count: int
    indexed_at: str
    metadata: Dict[str, Any]
    tags: List[str]


class LearningApplicationService:
    """
    Service for learning relevance scoring and application tracking.

    This service uses an ADDITIVE weighted scoring formula (C2 fix) to prevent
    score instability where a single low factor zeros out the entire score.

    Scoring formula:
        score = 0.30 * base_relevance +
                0.20 * success_rate +
                0.20 * confidence_score +
                0.15 * decay_factor +
                0.15 * context_similarity

    Example:
        ```python
        service = LearningApplicationService(db_path=Path(".gao-dev/documents.db"))

        # Get relevant learnings
        learnings = service.get_relevant_learnings(
            scale_level=ScaleLevel.LEVEL_3_MEDIUM_FEATURE,
            project_type="web_app",
            context={"tags": ["react", "typescript"], "phase": "implementation"},
            limit=5
        )

        # Record application
        service.record_application(
            learning_id=1,
            epic_num=29,
            story_num=2,
            outcome="success",
            context="Applied in story 29.2 implementation"
        )
        ```
    """

    def __init__(self, db_path: Path):
        """Initialize learning application service."""
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="learning_application")

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection with transaction handling."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()

    def get_relevant_learnings(
        self,
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict[str, Any],
        limit: int = 5,
    ) -> List[ScoredLearning]:
        """
        Get relevant learnings with calculated relevance scores.

        Query candidates (up to 50), score each using additive formula,
        filter by threshold (>0.2), sort by score, return top N.

        Args:
            scale_level: Current project scale level
            project_type: Project type (e.g., "web_app", "cli", "library")
            context: Execution context with tags, phase, etc.
            limit: Maximum number of learnings to return (default: 5)

        Returns:
            List of ScoredLearning objects sorted by relevance score (descending)
        """
        start_time = datetime.now()

        # Query candidate learnings (active only, limit 50 for performance)
        category = context.get("category")
        with self._get_connection() as conn:
            query = """
                SELECT
                    id, topic, category, learning, relevance_score,
                    success_rate, confidence_score, application_count,
                    indexed_at, metadata, tags
                FROM learning_index
                WHERE status = 'active'
            """
            params: List[Any] = []

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " LIMIT 50"

            cursor = conn.execute(query, params)
            candidates = [dict(row) for row in cursor.fetchall()]

        # Score each candidate
        scored_learnings: List[tuple[float, ScoredLearning]] = []
        for learning_dict in candidates:
            # Parse JSON fields
            import json

            metadata = json.loads(learning_dict.get("metadata", "{}"))
            tags = json.loads(learning_dict.get("tags", "[]"))

            # Calculate relevance score
            score = self._calculate_relevance_score(
                learning_dict, scale_level, project_type, context
            )

            # Filter by threshold (lowered to 0.2 from 0.3)
            if score > 0.2:
                scored_learning = ScoredLearning(
                    learning_id=learning_dict["id"],
                    topic=learning_dict["topic"],
                    category=learning_dict["category"],
                    learning=learning_dict["learning"],
                    relevance_score=score,
                    success_rate=learning_dict["success_rate"],
                    confidence_score=learning_dict["confidence_score"],
                    application_count=learning_dict["application_count"],
                    indexed_at=learning_dict["indexed_at"],
                    metadata=metadata,
                    tags=tags,
                )
                scored_learnings.append((score, scored_learning))

        # Sort by score descending and return top N
        scored_learnings.sort(key=lambda x: x[0], reverse=True)
        results = [sl for _, sl in scored_learnings[:limit]]

        # Log performance
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.info(
            "get_relevant_learnings_completed",
            candidates_evaluated=len(candidates),
            results_returned=len(results),
            elapsed_ms=round(elapsed_ms, 2),
            scale_level=scale_level.value,
            project_type=project_type,
        )

        return results

    def _calculate_relevance_score(
        self,
        learning: Dict[str, Any],
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Calculate relevance score using ADDITIVE weighted formula (C2 Fix).

        Formula:
            score = 0.30 * base_relevance +
                    0.20 * success_rate +
                    0.20 * confidence_score +
                    0.15 * decay_factor +
                    0.15 * context_similarity

        Each factor is independently weighted, preventing any single low factor
        from zeroing out the entire score. All factors normalized to [0.0, 1.0].

        Args:
            learning: Learning dictionary from database
            scale_level: Current project scale level
            project_type: Project type
            context: Execution context

        Returns:
            Relevance score in range [0.0, 1.0]
        """
        # Individual factors (each normalized to 0.0-1.0)
        base_relevance = learning.get("relevance_score", 0.5)
        success_rate = learning.get("success_rate", 1.0)
        confidence = learning.get("confidence_score", 0.5)
        decay = self._calculate_decay(learning["indexed_at"])
        similarity = self._context_similarity(learning, scale_level, project_type, context)

        # Weighted additive formula (C2 Fix - NOT multiplicative)
        score = (
            0.30 * base_relevance
            + 0.20 * success_rate
            + 0.20 * confidence
            + 0.15 * decay
            + 0.15 * similarity
        )

        # Clamp to [0, 1] (should be automatic with correct inputs, but safe)
        return max(0.0, min(1.0, score))

    def _calculate_decay(self, indexed_at: str) -> float:
        """
        Calculate recency decay factor using smooth exponential decay (C2 Fix).

        Formula: decay = 0.5 + 0.5 * exp(-days/180)

        This provides smooth exponential decay with no cliffs:
        - 0 days: 1.0 (full strength)
        - 30 days: 0.92
        - 90 days: 0.81
        - 180 days: 0.68
        - 365 days: 0.56
        - Never drops below 0.5 (retains historical value)

        Args:
            indexed_at: ISO format datetime string when learning was indexed

        Returns:
            Decay factor in range [0.5, 1.0]
        """
        indexed = datetime.fromisoformat(indexed_at)
        days_old = (datetime.now() - indexed).days

        # Smooth exponential decay (C2 Fix)
        decay = 0.5 + 0.5 * math.exp(-days_old / 180)

        return decay

    def _context_similarity(
        self,
        learning: Dict[str, Any],
        scale_level: ScaleLevel,
        project_type: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Calculate context similarity score (C11 Fix - Asymmetric Tag Handling).

        Compares:
        - Scale level match (25%): exact/adjacent/near scoring
        - Project type match (20%): exact match or general
        - Tag overlap (30%): Jaccard similarity with asymmetric handling
        - Category relevance (15%): quality/architectural highest
        - Temporal context (10%): same phase bonus

        C11 Fix: Handles asymmetric tag cases where only one side has tags.

        Args:
            learning: Learning dictionary from database
            scale_level: Current project scale level
            project_type: Project type
            context: Execution context with tags, phase, etc.

        Returns:
            Context similarity score in range [0.0, 1.0]
        """
        score = 0.0
        import json

        # Parse metadata and tags
        metadata = json.loads(learning.get("metadata", "{}"))
        learning_tags_raw = learning.get("tags", "[]")
        if isinstance(learning_tags_raw, str):
            learning_tags = set(json.loads(learning_tags_raw))
        else:
            learning_tags = set(learning_tags_raw)

        # Scale level match (25% weight) - C11 Fix
        learning_scale = metadata.get("scale_level")
        if learning_scale is not None:
            if learning_scale == scale_level.value:
                score += 0.25  # Exact match
            elif abs(learning_scale - scale_level.value) == 1:
                score += 0.15  # Adjacent levels
            elif abs(learning_scale - scale_level.value) == 2:
                score += 0.05  # Near levels
        else:
            score += 0.10  # Unknown scale gets base score

        # Project type match (20% weight) - C11 Fix
        learning_type = metadata.get("project_type")
        if learning_type == project_type:
            score += 0.20  # Exact match
        elif learning_type in ["any", "general"]:
            score += 0.15  # General learnings apply broadly

        # Tag overlap (30% weight) - Jaccard similarity with asymmetric handling (C11 Fix)
        context_tags = set(context.get("tags", []))
        if learning_tags and context_tags:
            # Both have tags: use Jaccard index
            overlap = len(learning_tags & context_tags)
            total = len(learning_tags | context_tags)
            score += 0.30 * (overlap / total)
        elif not learning_tags and not context_tags:
            # Neither has tags: neutral
            score += 0.15  # Medium bonus (both untagged)
        elif not learning_tags:
            # Only context has tags: learning is general (C11 Fix - asymmetric)
            score += 0.10  # Small bonus for untagged learnings
        else:
            # Only learning has tags: penalize slightly (less relevant)
            score += 0.05  # Minimal bonus

        # Category relevance (15% weight) - Smart scoring
        learning_category = learning.get("category")
        category_scores = {
            "quality": 0.15,  # Always relevant
            "architectural": 0.15,
            "process": 0.12,
            "technical": 0.10,
            "communication": 0.08,
            "tooling": 0.05,
        }
        score += category_scores.get(learning_category, 0.05)

        # Temporal context (10% weight) - Similar phases
        learning_phase = metadata.get("phase")
        context_phase = context.get("phase")
        if learning_phase and context_phase:
            if learning_phase == context_phase:
                score += 0.10
            elif learning_phase in ["any", "all_phases"]:
                score += 0.05

        return min(score, 1.0)

    def record_application(
        self,
        learning_id: int,
        epic_num: int,
        story_num: Optional[int],
        outcome: str,
        context: str,
    ) -> None:
        """
        Record a learning application and update statistics.

        This method is thread-safe using database transactions.

        Updates:
        - Insert into learning_applications table
        - Increment application_count
        - Recalculate success_rate
        - Adjust confidence_score using improved formula (C2 Fix)

        Args:
            learning_id: Learning ID from learning_index table
            epic_num: Epic number where learning was applied
            story_num: Optional story number
            outcome: Outcome ('success', 'failure', 'partial')
            context: Context description of application

        Raises:
            ValueError: If outcome is not valid
        """
        if outcome not in ["success", "failure", "partial"]:
            raise ValueError(f"Invalid outcome: {outcome}. Must be success, failure, or partial")

        start_time = datetime.now()

        with self._get_connection() as conn:
            # Record application
            conn.execute(
                """
                INSERT INTO learning_applications (
                    learning_id, epic_num, story_num,
                    outcome, application_context, applied_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (learning_id, epic_num, story_num, outcome, context, datetime.now().isoformat()),
            )

            # Calculate updated statistics
            stats = self._calculate_updated_stats(learning_id, conn)

            # Update learning index
            conn.execute(
                """
                UPDATE learning_index
                SET application_count = ?,
                    success_rate = ?,
                    confidence_score = ?
                WHERE id = ?
                """,
                (stats["count"], stats["success_rate"], stats["confidence"], learning_id),
            )

        # Log performance
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.info(
            "record_application_completed",
            learning_id=learning_id,
            epic_num=epic_num,
            story_num=story_num,
            outcome=outcome,
            new_count=stats["count"],
            new_success_rate=round(stats["success_rate"], 3),
            new_confidence=round(stats["confidence"], 3),
            elapsed_ms=round(elapsed_ms, 2),
        )

    def _calculate_updated_stats(
        self, learning_id: int, conn: sqlite3.Connection
    ) -> Dict[str, float]:
        """
        Calculate updated statistics for a learning (C2 Fix - Improved Confidence Formula).

        Formula:
            base_confidence = min(0.95, 0.5 + 0.45 * sqrt(successes / total))

            Then adjust for success rate:
            if success_rate < 0.5:
                confidence *= success_rate * 2  # Reduce if poor performance

        This provides smoother growth and never decreases on success.

        Args:
            learning_id: Learning ID
            conn: Database connection (for transaction safety)

        Returns:
            Dict with count, success_rate, confidence
        """
        cursor = conn.execute(
            """
            SELECT outcome
            FROM learning_applications
            WHERE learning_id = ?
            """,
            (learning_id,),
        )
        applications = [row[0] for row in cursor.fetchall()]

        count = len(applications)
        if count == 0:
            return {"count": 0, "success_rate": 1.0, "confidence": 0.5}

        # Calculate success rate
        successes = applications.count("success")
        partials = applications.count("partial")
        success_rate = (successes + 0.5 * partials) / count

        # Calculate base confidence using sqrt (smoother growth) - C2 Fix
        if successes > 0:
            base_confidence = min(0.95, 0.5 + 0.45 * math.sqrt(successes / count))
        else:
            base_confidence = 0.5

        # Adjust for poor success rate - C2 Fix
        if success_rate < 0.5:
            confidence = base_confidence * (success_rate * 2)
        else:
            confidence = base_confidence

        return {"count": count, "success_rate": success_rate, "confidence": confidence}
