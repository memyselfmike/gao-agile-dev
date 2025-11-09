"""Action Item Integration Service - Convert action items to stories.

This service manages the conversion of CRITICAL action items from ceremonies
into stories, with strict limits to prevent noise (C8 fix).

Epic: 29 - Self-Learning Feedback Loop
Story: 29.5 - Action Item Integration

Design Pattern: Service Layer
Dependencies: ActionItemService, StoryStateService, GitIntegratedStateManager
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import json

import structlog

from .action_item_service import ActionItemService
from .story_state_service import StoryStateService
from ..git_manager import GitManager
from ...lifecycle.exceptions import MaxConversionsExceededError

logger = structlog.get_logger()


class ActionItemPriority(Enum):
    """
    Action item priority levels with conversion rules (C8 fix).

    Only CRITICAL priority auto-converts to stories.
    Maximum 1 conversion per epic to prevent noise.
    """
    CRITICAL = "critical"  # ONLY this auto-converts
    HIGH = "high"          # Manual review required
    MEDIUM = "medium"      # Track only
    LOW = "low"            # Auto-complete after 30 days


class ActionItemIntegrationService:
    """
    Service for converting action items to stories with strict limits.

    Implements C8 fix: Only CRITICAL priority items auto-convert,
    with maximum 1 conversion per epic to prevent noise.

    Example:
        ```python
        service = ActionItemIntegrationService(
            db_path=Path(".gao-dev/documents.db"),
            project_root=Path("/project")
        )

        # Process action items after ceremony
        result = service.process_action_items(ceremony_id=1)
        print(f"Converted: {result['converted']}, Tracked: {result['tracked']}")

        # Manual promotion of HIGH priority item
        story_num = service.convert_to_story(action_item_id=5, epic_num=2)
        ```

    Attributes:
        db_path: Path to state database
        project_root: Project root directory
        action_service: Service for action item CRUD
        story_service: Service for story state management
        git_manager: Git manager for commits
    """

    def __init__(
        self,
        db_path: Path,
        project_root: Path,
        git_manager: Optional[GitManager] = None
    ):
        """
        Initialize action item integration service.

        Args:
            db_path: Path to state database
            project_root: Project root directory
            git_manager: Optional git manager (creates new if not provided)
        """
        self.db_path = Path(db_path)
        self.project_root = Path(project_root)
        self._local = threading.local()

        # Initialize services
        self.action_service = ActionItemService(db_path=self.db_path)
        self.story_service = StoryStateService(db_path=self.db_path)
        self.git_manager = git_manager or GitManager(repo_path=self.project_root)

        self.logger = logger.bind(service="action_item_integration")
        self.logger.info(
            "action_item_integration_service_initialized",
            db_path=str(self.db_path),
            project_root=str(self.project_root)
        )

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

    def process_action_items(self, ceremony_id: int) -> Dict[str, int]:
        """
        Process action items from ceremony with strict conversion rules.

        Rules (C8 Fix):
        - Only CRITICAL priority converts automatically
        - Maximum 1 conversion per epic
        - All others tracked for manual review

        Args:
            ceremony_id: Ceremony ID to process action items from

        Returns:
            Dict with counts: {"converted": N, "tracked": M}

        Example:
            ```python
            result = service.process_action_items(ceremony_id=1)
            print(f"Auto-converted: {result['converted']}")
            print(f"Tracked for review: {result['tracked']}")
            ```
        """
        self.logger.info(
            "processing_action_items",
            ceremony_id=ceremony_id
        )

        # Get all action items for ceremony
        action_items = self._get_action_items_by_ceremony(ceremony_id)

        if not action_items:
            self.logger.info("no_action_items_found", ceremony_id=ceremony_id)
            return {"converted": 0, "tracked": 0}

        converted = 0
        tracked = 0

        # Get epic number from ceremony
        epic_num = self._get_epic_num_from_ceremony(ceremony_id)

        # Check if epic already has a converted action item (C8 limit)
        if self._has_converted_action_item(epic_num):
            self.logger.warning(
                "epic_conversion_limit_reached",
                epic_num=epic_num,
                message=f"Epic {epic_num} already has 1 converted action item (C8 limit)"
            )
            # Track all items, convert none
            for item in action_items:
                self._mark_for_manual_review(item["id"])
                tracked += 1
            return {"converted": 0, "tracked": tracked}

        # Process items by priority
        for item in action_items:
            priority_str = item.get("priority", "low").lower()

            if priority_str == ActionItemPriority.CRITICAL.value:
                # Auto-convert first CRITICAL item only
                if converted == 0:
                    try:
                        story_num = self.convert_to_story(item["id"], epic_num)
                        converted += 1
                        self.logger.info(
                            "action_item_converted",
                            action_item_id=item["id"],
                            epic_num=epic_num,
                            story_num=story_num
                        )
                    except Exception as e:
                        self.logger.error(
                            "conversion_failed",
                            action_item_id=item["id"],
                            error=str(e)
                        )
                        self._mark_for_manual_review(item["id"])
                        tracked += 1
                else:
                    # Additional CRITICAL items marked for manual review
                    self._mark_for_manual_review(item["id"])
                    tracked += 1
            else:
                # HIGH/MEDIUM/LOW tracked only
                tracked += 1

        self.logger.info(
            "action_items_processed",
            ceremony_id=ceremony_id,
            epic_num=epic_num,
            converted=converted,
            tracked=tracked
        )

        return {"converted": converted, "tracked": tracked}

    def convert_to_story(
        self,
        action_item_id: int,
        epic_num: int,
        manual_override: bool = False
    ) -> int:
        """
        Convert CRITICAL action item to story.

        Args:
            action_item_id: Action item to convert
            epic_num: Epic to add story to
            manual_override: If True, bypass C8 limit check (for manual promotion)

        Returns:
            Story number created

        Raises:
            MaxConversionsExceededError: If epic already has 1 converted item (unless manual_override)
            ValueError: If action item not found

        Example:
            ```python
            # Auto-conversion (checks C8 limit)
            story_num = service.convert_to_story(action_item_id=1, epic_num=1)

            # Manual promotion (bypasses C8 limit)
            story_num = service.convert_to_story(
                action_item_id=5,
                epic_num=1,
                manual_override=True
            )
            ```
        """
        self.logger.info(
            "converting_action_item_to_story",
            action_item_id=action_item_id,
            epic_num=epic_num,
            manual_override=manual_override
        )

        # Check limit (C8 fix) unless manual override
        if not manual_override and self._has_converted_action_item(epic_num):
            raise MaxConversionsExceededError(
                f"Epic {epic_num} already has 1 converted action item. "
                f"Use manual_override=True to bypass limit.",
                epic_num=epic_num,
                adjustment_count=1
            )

        # Get action item
        action_item = self.action_service.get(action_item_id)

        # Get next story number
        story_num = self._get_next_story_num(epic_num)

        # Generate story content
        story_content = self._generate_story_content(action_item, epic_num, story_num)

        # Create story file
        story_path = self._get_story_path(epic_num, story_num)
        story_path.parent.mkdir(parents=True, exist_ok=True)
        story_path.write_text(story_content, encoding="utf-8")

        # Parse metadata if it's a string
        action_metadata = action_item.get("metadata")
        if isinstance(action_metadata, str):
            action_metadata = json.loads(action_metadata) if action_metadata else {}
        elif action_metadata is None:
            action_metadata = {}

        # Register in database
        self.story_service.create(
            epic_num=epic_num,
            story_num=story_num,
            title=action_item["title"],
            status="pending",
            priority="P0",  # CRITICAL action items = P0
            metadata={
                "source": "action_item",
                "action_item_id": action_item_id,
                "ceremony_id": action_metadata.get("ceremony_id"),
                "priority": action_item.get("priority"),
                "converted_at": datetime.now().isoformat(),
                "manual_override": manual_override
            }
        )

        # Record conversion in tracking table
        self._record_conversion(epic_num, action_item_id, story_num)

        # Mark action item as converted
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE action_items
                SET status = 'converted',
                    completed_at = ?,
                    updated_at = ?,
                    metadata = json_set(COALESCE(metadata, '{}'), '$.converted_to_story', ?)
                WHERE id = ?
                """,
                (datetime.now().isoformat(), datetime.now().isoformat(), story_num, action_item_id)
            )

        # Git commit
        try:
            self.git_manager.add(str(story_path))
            self.git_manager.commit(
                f"feat(epic-{epic_num}): add Story {epic_num}.{story_num} from action item\n\n"
                f"Converted action item: {action_item['title']}\n"
                f"Priority: {action_item.get('priority', 'unknown')}\n"
                f"Manual override: {manual_override}"
            )
        except Exception as e:
            self.logger.warning(
                "git_commit_failed",
                error=str(e),
                story_path=str(story_path)
            )

        self.logger.info(
            "story_created_from_action_item",
            epic_num=epic_num,
            story_num=story_num,
            action_item_id=action_item_id,
            story_path=str(story_path)
        )

        return story_num

    def get_pending_action_items(
        self,
        epic_num: Optional[int] = None,
        priority: Optional[ActionItemPriority] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending action items (not converted, not completed).

        Args:
            epic_num: Optional filter by epic number
            priority: Optional filter by priority

        Returns:
            List of pending action items

        Example:
            ```python
            # Get all pending items
            items = service.get_pending_action_items()

            # Get pending CRITICAL items for epic 1
            critical_items = service.get_pending_action_items(
                epic_num=1,
                priority=ActionItemPriority.CRITICAL
            )
            ```
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM action_items
                WHERE status IN ('pending', 'in_progress')
            """
            params = []

            if epic_num is not None:
                query += " AND epic_num = ?"
                params.append(epic_num)

            if priority is not None:
                query += " AND priority = ?"
                params.append(priority.value)

            query += " ORDER BY priority DESC, created_at ASC"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def mark_action_item_complete(
        self,
        action_item_id: int,
        completed_by: str = "user",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark action item as completed without converting to story.

        Args:
            action_item_id: Action item ID to complete
            completed_by: Who completed it (default: "user")
            reason: Optional completion reason

        Returns:
            Updated action item record

        Example:
            ```python
            service.mark_action_item_complete(
                action_item_id=5,
                completed_by="Bob",
                reason="Fixed during other story"
            )
            ```
        """
        self.logger.info(
            "marking_action_item_complete",
            action_item_id=action_item_id,
            completed_by=completed_by,
            reason=reason
        )

        # Update metadata with completion reason
        metadata = {"completed_by": completed_by}
        if reason:
            metadata["completion_reason"] = reason

        # Use action_service to mark complete
        return self.action_service.complete(action_item_id)

    def auto_complete_stale_items(self, days_old: int = 30) -> int:
        """
        Auto-complete LOW priority items older than N days.

        Args:
            days_old: Age threshold in days (default: 30)

        Returns:
            Number of items auto-completed

        Example:
            ```python
            # Auto-complete LOW items older than 30 days
            completed = service.auto_complete_stale_items(days_old=30)
            print(f"Auto-completed {completed} stale items")
            ```
        """
        self.logger.info(
            "auto_completing_stale_items",
            days_old=days_old
        )

        cutoff_date = datetime.now() - timedelta(days=days_old)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Find stale LOW priority items
            cursor.execute(
                """
                SELECT id, title FROM action_items
                WHERE status IN ('pending', 'in_progress')
                  AND priority = ?
                  AND created_at < ?
                """,
                (ActionItemPriority.LOW.value, cutoff_date.isoformat())
            )

            stale_items = cursor.fetchall()

            # Mark each as complete
            for item in stale_items:
                self.mark_action_item_complete(
                    action_item_id=item["id"],
                    completed_by="system",
                    reason=f"Auto-completed after {days_old} days (low priority)"
                )

        count = len(stale_items)
        self.logger.info(
            "stale_items_auto_completed",
            count=count,
            days_old=days_old
        )

        return count

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_action_items_by_ceremony(self, ceremony_id: int) -> List[Dict[str, Any]]:
        """Get all action items for a ceremony."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM action_items
                WHERE json_extract(metadata, '$.ceremony_id') = ?
                  AND status = 'pending'
                """,
                (ceremony_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def _get_epic_num_from_ceremony(self, ceremony_id: int) -> int:
        """Get epic number from ceremony ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT epic_num FROM ceremony_summaries WHERE id = ?",
                (ceremony_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Ceremony {ceremony_id} not found")
            return row["epic_num"]

    def _has_converted_action_item(self, epic_num: int) -> bool:
        """Check if epic already has a converted action item (C8 fix)."""
        # Ensure conversion tracking table exists
        self._ensure_conversion_table()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM action_item_conversions WHERE epic_num = ?",
                (epic_num,)
            )
            count = cursor.fetchone()["count"]
            return count >= 1  # Max 1 per epic

    def _ensure_conversion_table(self) -> None:
        """Ensure action_item_conversions table exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS action_item_conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    epic_num INTEGER NOT NULL,
                    action_item_id INTEGER NOT NULL,
                    story_num INTEGER NOT NULL,
                    converted_at TEXT NOT NULL,
                    FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num),
                    FOREIGN KEY (action_item_id) REFERENCES action_items(id)
                )
                """
            )

    def _record_conversion(self, epic_num: int, action_item_id: int, story_num: int) -> None:
        """Record action item conversion in tracking table."""
        self._ensure_conversion_table()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO action_item_conversions (epic_num, action_item_id, story_num, converted_at)
                VALUES (?, ?, ?, ?)
                """,
                (epic_num, action_item_id, story_num, datetime.now().isoformat())
            )

    def _mark_for_manual_review(self, action_item_id: int) -> None:
        """Mark action item for manual review."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE action_items
                SET metadata = json_set(COALESCE(metadata, '{}'), '$.manual_review_required', 1),
                    updated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), action_item_id)
            )

    def _get_next_story_num(self, epic_num: int) -> int:
        """Get next available story number for epic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(story_num) as max_num FROM story_state WHERE epic_num = ?",
                (epic_num,)
            )
            row = cursor.fetchone()
            max_num = row["max_num"] if row and row["max_num"] is not None else 0
            return max_num + 1

    def _get_story_path(self, epic_num: int, story_num: int) -> Path:
        """Get file path for story."""
        # Standard story location
        return (
            self.project_root
            / "docs"
            / "features"
            / "ceremony-integration-and-self-learning"
            / "stories"
            / f"epic-{epic_num}"
            / f"story-{epic_num}.{story_num}.md"
        )

    def _generate_story_content(
        self,
        action_item: Dict[str, Any],
        epic_num: int,
        story_num: int
    ) -> str:
        """
        Generate story content from action item using template.

        Args:
            action_item: Action item data
            epic_num: Epic number
            story_num: Story number

        Returns:
            Markdown content for story file
        """
        # Extract metadata
        metadata = action_item.get("metadata")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        elif metadata is None:
            metadata = {}

        ceremony_id = metadata.get("ceremony_id", "Unknown")

        # Get ceremony type and date
        ceremony_type = "Unknown"
        ceremony_date = datetime.now().strftime("%Y-%m-%d")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT ceremony_type, created_at FROM ceremony_summaries WHERE id = ?",
                    (ceremony_id,)
                )
                row = cursor.fetchone()
                if row:
                    ceremony_type = row["ceremony_type"]
                    ceremony_date = row["created_at"][:10]  # Extract date part
        except Exception:
            pass

        # Generate content from template
        title = action_item["title"]
        description = action_item.get("description", "")
        priority = action_item.get("priority", "critical").upper()
        created_at = datetime.now().strftime("%Y-%m-%d")

        content = f"""# Story {epic_num}.{story_num}: {title}

**Epic**: Epic {epic_num}
**Status**: Not Started
**Priority**: P0 (from CRITICAL action item)
**Estimated Effort**: 3 story points
**Owner**: TBD
**Created**: {created_at}
**Source**: Action Item from {ceremony_type} ceremony

---

## User Story

**As a** team member
**I want** {description or title}
**So that** we can improve our development process and address critical issues

---

## Context

This story was created from a CRITICAL action item identified during
{ceremony_type} ceremony on {ceremony_date}.

**Original Action Item**: {title}

**Description**: {description}

**Why Critical**: This item was marked as CRITICAL priority during the ceremony,
indicating it requires immediate attention to unblock progress or address a
significant issue.

---

## Acceptance Criteria

### AC1: Action Item Requirements Met

- [ ] {description or title}
- [ ] All acceptance criteria from original action item satisfied
- [ ] Related blockers or issues resolved

### AC2: Quality Standards

- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

### AC3: Verification

- [ ] Verified with action item creator
- [ ] Stakeholders notified of resolution

---

## Definition of Done

- [ ] Action item requirements met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Committed to git
- [ ] Action item marked as resolved

---

## Related Action Item

- **Action Item ID**: {action_item["id"]}
- **Created**: {action_item.get("created_at", "Unknown")}
- **Priority**: {priority}
- **Ceremony**: {ceremony_type} (ID: {ceremony_id})
"""

        return content

    def close(self) -> None:
        """Close all service connections."""
        self.action_service.close()
        self.story_service.close()
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
