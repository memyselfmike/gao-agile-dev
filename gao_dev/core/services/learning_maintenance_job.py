"""Learning Maintenance Job - Automated learning hygiene and decay management.

This service performs automated maintenance on learning index to keep it relevant
and performant through decay updates, low confidence deactivation, supersession,
and old data pruning.

Epic: 29 - Self-Learning Feedback Loop
Story: 29.6 - Learning Decay & Confidence

Design Pattern: Batch Job Service
Dependencies: LearningIndexService, LearningApplicationService, sqlite3, structlog
"""

import math
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple, Optional, List, Dict, Any

import structlog

logger = structlog.get_logger()


class MaintenanceReport(NamedTuple):
    """Report from maintenance job execution."""

    decay_updates: int
    deactivated_count: int
    superseded_count: int
    pruned_applications: int
    execution_time_ms: float
    timestamp: str


class LearningMaintenanceJob:
    """
    Automated maintenance job for learning index.

    Performs:
    - Decay factor updates (smooth exponential, C10 fix)
    - Low confidence deactivation (confidence < 0.2, success_rate < 0.3, apps >= 5)
    - Supersede outdated learnings (same category, newer > old + 0.2)
    - Prune old applications (>1 year)

    Performance target: <5 seconds for 1000 learnings

    Example:
        ```python
        job = LearningMaintenanceJob(db_path=Path(".gao-dev/documents.db"))

        # Run full maintenance
        report = job.run_maintenance()
        print(f"Updated {report.decay_updates} decay factors")

        # Dry run to preview changes
        report = job.run_maintenance(dry_run=True)
        ```
    """

    def __init__(self, db_path: Path):
        """Initialize learning maintenance job."""
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="learning_maintenance")

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

    def run_maintenance(
        self, dry_run: bool = False, verbose: bool = False
    ) -> MaintenanceReport:
        """
        Run full maintenance cycle.

        Args:
            dry_run: If True, preview changes without committing
            verbose: If True, log detailed information

        Returns:
            MaintenanceReport with execution statistics
        """
        start_time = datetime.now()

        self.logger.info(
            "maintenance_started",
            dry_run=dry_run,
            verbose=verbose,
            timestamp=start_time.isoformat(),
        )

        if dry_run:
            # Use separate connection for dry run (read-only queries)
            with self._get_connection() as conn:
                # Preview changes without committing
                decay_updates = self._count_decay_updates(conn)
                deactivated = self._count_low_confidence_learnings(conn)
                superseded = self._count_supersede_candidates(conn)
                pruned = self._count_old_applications(conn)

                elapsed = (datetime.now() - start_time).total_seconds() * 1000

                report = MaintenanceReport(
                    decay_updates=decay_updates,
                    deactivated_count=deactivated,
                    superseded_count=superseded,
                    pruned_applications=pruned,
                    execution_time_ms=elapsed,
                    timestamp=start_time.isoformat(),
                )

                if verbose:
                    self._log_report(report, dry_run=True)

                return report

        # Run actual maintenance
        with self._get_connection() as conn:
            decay_updates = self._update_decay_factors(conn, verbose)
            deactivated = self._deactivate_low_confidence_learnings(conn, verbose)
            superseded = self._supersede_outdated_learnings(conn, verbose)
            pruned = self._prune_old_applications(conn, verbose)

        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        report = MaintenanceReport(
            decay_updates=decay_updates,
            deactivated_count=deactivated,
            superseded_count=superseded,
            pruned_applications=pruned,
            execution_time_ms=elapsed,
            timestamp=start_time.isoformat(),
        )

        self.logger.info(
            "maintenance_completed",
            decay_updates=decay_updates,
            deactivated_count=deactivated,
            superseded_count=superseded,
            pruned_applications=pruned,
            execution_time_ms=round(elapsed, 2),
        )

        if verbose:
            self._log_report(report, dry_run=False)

        return report

    def _update_decay_factors(self, conn: sqlite3.Connection, verbose: bool) -> int:
        """
        Update decay factors for all active learnings (C10 Fix).

        Uses smooth exponential decay: decay = 0.5 + 0.5 * exp(-days/180)
        Results: 0d=1.0, 30d=0.92, 90d=0.81, 180d=0.68, 365d=0.56

        Args:
            conn: Database connection
            verbose: If True, log detailed information

        Returns:
            Number of decay factors updated
        """
        cursor = conn.cursor()

        # Get all active learnings
        cursor.execute(
            """
            SELECT id, indexed_at
            FROM learning_index
            WHERE status = 'active'
            """
        )
        learnings = cursor.fetchall()

        updated_count = 0
        for row in learnings:
            learning_id = row["id"]
            indexed_at = row["indexed_at"]

            # Calculate decay factor
            decay = self._calculate_decay(indexed_at)

            # Update decay factor
            cursor.execute(
                """
                UPDATE learning_index
                SET decay_factor = ?
                WHERE id = ?
                """,
                (decay, learning_id),
            )

            updated_count += 1

            if verbose and updated_count <= 5:
                self.logger.debug(
                    "decay_updated",
                    learning_id=learning_id,
                    decay_factor=round(decay, 3),
                    indexed_at=indexed_at,
                )

        return updated_count

    def _calculate_decay(self, indexed_at: str) -> float:
        """
        Calculate smooth exponential decay factor (C2, C10 Fix).

        Formula: decay = 0.5 + 0.5 * exp(-days / 180)

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

        # Smooth exponential decay (C2, C10 Fix)
        decay = 0.5 + 0.5 * math.exp(-days_old / 180)

        return max(decay, 0.5)  # Floor at 0.5

    def _deactivate_low_confidence_learnings(
        self, conn: sqlite3.Connection, verbose: bool
    ) -> int:
        """
        Deactivate learnings with low confidence after sufficient applications.

        Criteria:
        - confidence_score < 0.2
        - success_rate < 0.3
        - application_count >= 5

        Args:
            conn: Database connection
            verbose: If True, log detailed information

        Returns:
            Number of learnings deactivated
        """
        cursor = conn.cursor()

        # Find learnings matching criteria
        cursor.execute(
            """
            SELECT id, topic, confidence_score, success_rate, application_count
            FROM learning_index
            WHERE status = 'active'
              AND confidence_score < 0.2
              AND success_rate < 0.3
              AND application_count >= 5
            """
        )
        learnings = cursor.fetchall()

        deactivated_count = 0
        for row in learnings:
            learning_id = row["id"]

            # Get current metadata or create new
            import json

            cursor.execute("SELECT metadata FROM learning_index WHERE id = ?", (learning_id,))
            current_metadata = cursor.fetchone()["metadata"]

            if current_metadata:
                metadata_dict = json.loads(current_metadata)
            else:
                metadata_dict = {}

            # Add deactivation info
            metadata_dict["deactivated_reason"] = "Low confidence after 5+ applications"
            metadata_dict["deactivated_at"] = datetime.now().isoformat()

            # Deactivate learning
            cursor.execute(
                """
                UPDATE learning_index
                SET status = 'inactive',
                    metadata = ?
                WHERE id = ?
                """,
                (json.dumps(metadata_dict), learning_id),
            )

            deactivated_count += 1

            if verbose:
                self.logger.info(
                    "learning_deactivated",
                    learning_id=learning_id,
                    topic=row["topic"],
                    confidence=round(row["confidence_score"], 3),
                    success_rate=round(row["success_rate"], 3),
                    applications=row["application_count"],
                )

        return deactivated_count

    def _supersede_outdated_learnings(
        self, conn: sqlite3.Connection, verbose: bool
    ) -> int:
        """
        Mark older learnings superseded by newer ones.

        Criteria:
        - Same category
        - Newer has confidence > old + 0.2

        Args:
            conn: Database connection
            verbose: If True, log detailed information

        Returns:
            Number of learnings superseded
        """
        cursor = conn.cursor()

        superseded_count = 0

        # Get all categories
        categories = ["quality", "process", "architectural", "technical", "team", "communication"]

        for category in categories:
            # Get learnings in this category, ordered by indexed_at DESC
            cursor.execute(
                """
                SELECT id, topic, confidence_score, indexed_at
                FROM learning_index
                WHERE category = ?
                  AND status = 'active'
                  AND superseded_by IS NULL
                ORDER BY indexed_at DESC
                """,
                (category,),
            )
            learnings = cursor.fetchall()

            # Compare newer learnings with older ones
            for i, newer in enumerate(learnings):
                for older in learnings[i + 1 :]:
                    # Check if newer clearly outperforms older
                    confidence_delta = newer["confidence_score"] - older["confidence_score"]
                    if confidence_delta > 0.2:
                        # Supersede older learning
                        cursor.execute(
                            """
                            UPDATE learning_index
                            SET superseded_by = ?,
                                status = 'superseded'
                            WHERE id = ?
                            """,
                            (newer["id"], older["id"]),
                        )

                        superseded_count += 1

                        if verbose:
                            self.logger.info(
                                "learning_superseded",
                                old_id=older["id"],
                                old_topic=older["topic"],
                                old_confidence=round(older["confidence_score"], 3),
                                new_id=newer["id"],
                                new_topic=newer["topic"],
                                new_confidence=round(newer["confidence_score"], 3),
                                confidence_delta=round(confidence_delta, 3),
                            )

        return superseded_count

    def _prune_old_applications(self, conn: sqlite3.Connection, verbose: bool) -> int:
        """
        Delete learning_applications older than 1 year.

        Args:
            conn: Database connection
            verbose: If True, log detailed information

        Returns:
            Number of applications pruned
        """
        cursor = conn.cursor()

        # Calculate cutoff date (1 year ago)
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()

        # Count applications to be deleted
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM learning_applications
            WHERE applied_at < ?
            """,
            (cutoff_date,),
        )
        count = cursor.fetchone()["count"]

        # Delete old applications
        cursor.execute(
            """
            DELETE FROM learning_applications
            WHERE applied_at < ?
            """,
            (cutoff_date,),
        )

        if verbose and count > 0:
            self.logger.info(
                "applications_pruned",
                count=count,
                cutoff_date=cutoff_date,
            )

        return count

    # Dry-run preview methods

    def _count_decay_updates(self, conn: sqlite3.Connection) -> int:
        """Count active learnings that would have decay updated."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM learning_index
            WHERE status = 'active'
            """
        )
        return cursor.fetchone()["count"]

    def _count_low_confidence_learnings(self, conn: sqlite3.Connection) -> int:
        """Count learnings that would be deactivated."""
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM learning_index
            WHERE status = 'active'
              AND confidence_score < 0.2
              AND success_rate < 0.3
              AND application_count >= 5
            """
        )
        return cursor.fetchone()["count"]

    def _count_supersede_candidates(self, conn: sqlite3.Connection) -> int:
        """Count learnings that would be superseded (approximate)."""
        # This is an approximation since actual count requires complex logic
        # For dry-run purposes, we'll count potentially supersedable learnings
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT category, COUNT(*) as count
            FROM learning_index
            WHERE status = 'active'
              AND superseded_by IS NULL
            GROUP BY category
            HAVING count > 1
            """
        )
        # Estimate ~10% might be superseded
        total = sum(row["count"] for row in cursor.fetchall())
        return int(total * 0.1)

    def _count_old_applications(self, conn: sqlite3.Connection) -> int:
        """Count applications older than 1 year."""
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM learning_applications
            WHERE applied_at < ?
            """,
            (cutoff_date,),
        )
        return cursor.fetchone()["count"]

    def _log_report(self, report: MaintenanceReport, dry_run: bool) -> None:
        """Log detailed report information."""
        mode = "DRY RUN" if dry_run else "COMPLETED"
        self.logger.info(
            f"maintenance_report_{mode.lower().replace(' ', '_')}",
            mode=mode,
            decay_updates=report.decay_updates,
            deactivated_count=report.deactivated_count,
            superseded_count=report.superseded_count,
            pruned_applications=report.pruned_applications,
            execution_time_ms=round(report.execution_time_ms, 2),
            timestamp=report.timestamp,
        )

    def close(self) -> None:
        """Close database connection for current thread."""
        if hasattr(self._local, "conn"):
            try:
                self._local.conn.close()
            except Exception:
                pass
            delattr(self._local, "conn")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connections."""
        self.close()
