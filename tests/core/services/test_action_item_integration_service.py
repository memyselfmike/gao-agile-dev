"""Tests for ActionItemIntegrationService - Action item to story conversion.

Epic: 29 - Self-Learning Feedback Loop
Story: 29.5 - Action Item Integration

Test Coverage:
- Process action items with various priorities (C8 fix)
- C8 fix: Only CRITICAL converts automatically
- C8 fix: Max 1 conversion per epic enforced
- Story creation from action item
- Story content template rendering
- Stale item cleanup (30 days)
- Manual promotion of HIGH priority items
- Integration with CeremonyOrchestrator
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

from gao_dev.core.services.action_item_integration_service import (
    ActionItemIntegrationService,
    ActionItemPriority
)
from gao_dev.core.services.action_item_service import ActionItemService
from gao_dev.core.services.story_state_service import StoryStateService
from gao_dev.core.services.ceremony_service import CeremonyService
from gao_dev.lifecycle.exceptions import MaxConversionsExceededError


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary test database with schema."""
    db_path = tmp_path / "test_documents.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create necessary tables
    cursor.execute("""
        CREATE TABLE action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            assignee TEXT,
            epic_num INTEGER,
            story_num INTEGER,
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE story_state (
            epic_num INTEGER NOT NULL,
            story_num INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            assignee TEXT,
            priority TEXT DEFAULT 'P2',
            estimate_hours REAL,
            actual_hours REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT,
            PRIMARY KEY (epic_num, story_num)
        )
    """)

    cursor.execute("""
        CREATE TABLE epic_state (
            epic_num INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE ceremony_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ceremony_type TEXT NOT NULL,
            epic_num INTEGER,
            story_num INTEGER,
            summary TEXT NOT NULL,
            participants TEXT,
            decisions TEXT,
            action_items TEXT,
            held_at TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT
        )
    """)

    # Insert test epic
    cursor.execute(
        "INSERT INTO epic_state (epic_num, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (1, "Test Epic", datetime.now().isoformat(), datetime.now().isoformat())
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def service(temp_db, tmp_path):
    """Create ActionItemIntegrationService instance."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Mock GitManager
    git_manager = Mock()
    git_manager.add = Mock()
    git_manager.commit = Mock()

    service = ActionItemIntegrationService(
        db_path=temp_db,
        project_root=project_root,
        git_manager=git_manager
    )

    yield service

    service.close()


def test_process_action_items_critical_converts(service, temp_db):
    """Test CRITICAL priority action item converts to story (C8 fix)."""
    # Create ceremony
    ceremony_service = CeremonyService(db_path=temp_db)
    ceremony = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro",
        participants="team",
        epic_num=1
    )

    # Create CRITICAL action item
    action_service = ActionItemService(db_path=temp_db)
    action_item = action_service.create(
        title="Fix critical bug",
        description="Security vulnerability found",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    # Process action items
    result = service.process_action_items(ceremony_id=ceremony["id"])

    # Verify conversion
    assert result["converted"] == 1
    assert result["tracked"] == 0

    # Verify story created
    story_service = StoryStateService(db_path=temp_db)
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM story_state WHERE epic_num = 1")
        stories = cursor.fetchall()
        assert len(stories) == 1

    ceremony_service.close()
    action_service.close()


def test_c8_fix_max_one_conversion_per_epic(service, temp_db):
    """Test max 1 action item converts per epic (C8 fix)."""
    # Create ceremony
    ceremony_service = CeremonyService(db_path=temp_db)
    ceremony1 = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro 1",
        participants="team",
        epic_num=1
    )

    # Create first CRITICAL action item
    action_service = ActionItemService(db_path=temp_db)
    action1 = action_service.create(
        title="Critical issue 1",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony1["id"]}
    )

    # Process first ceremony - should convert 1
    result1 = service.process_action_items(ceremony_id=ceremony1["id"])
    assert result1["converted"] == 1
    assert result1["tracked"] == 0

    # Create second ceremony
    ceremony2 = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro 2",
        participants="team",
        epic_num=1
    )

    # Create second CRITICAL action item
    action2 = action_service.create(
        title="Critical issue 2",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony2["id"]}
    )

    # Process second ceremony - should convert 0 (limit hit)
    result2 = service.process_action_items(ceremony_id=ceremony2["id"])
    assert result2["converted"] == 0
    assert result2["tracked"] == 1  # Tracked for manual review

    # Verify only 1 story created
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM story_state WHERE epic_num = 1")
        count = cursor.fetchone()[0]
        assert count == 1

    ceremony_service.close()
    action_service.close()


def test_c8_fix_non_critical_items_do_not_auto_convert(service, temp_db):
    """Test HIGH/MEDIUM/LOW priority items don't auto-convert (C8 fix)."""
    # Create ceremony
    ceremony_service = CeremonyService(db_path=temp_db)
    ceremony = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro",
        participants="team",
        epic_num=1
    )

    # Create action items with various priorities
    action_service = ActionItemService(db_path=temp_db)

    action_service.create(
        title="High priority item",
        priority=ActionItemPriority.HIGH.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    action_service.create(
        title="Medium priority item",
        priority=ActionItemPriority.MEDIUM.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    action_service.create(
        title="Low priority item",
        priority=ActionItemPriority.LOW.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    # Process action items
    result = service.process_action_items(ceremony_id=ceremony["id"])

    # None should convert
    assert result["converted"] == 0
    assert result["tracked"] == 3

    # Verify no stories created
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM story_state WHERE epic_num = 1")
        count = cursor.fetchone()[0]
        assert count == 0

    ceremony_service.close()
    action_service.close()


def test_convert_to_story_creates_file_and_db_record(service, temp_db, tmp_path):
    """Test converting action item to story creates file and DB record."""
    # Create action item
    action_service = ActionItemService(db_path=temp_db)
    action_item = action_service.create(
        title="Implement new feature",
        description="Add user authentication",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": 1}
    )

    # Convert to story
    story_num = service.convert_to_story(
        action_item_id=action_item["id"],
        epic_num=1
    )

    # Verify story number
    assert story_num == 1

    # Verify DB record
    story_service = StoryStateService(db_path=temp_db)
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM story_state WHERE epic_num = 1 AND story_num = ?", (story_num,))
        story = cursor.fetchone()
        assert story is not None

    # Verify file created
    story_path = (
        tmp_path / "project" / "docs" / "features" / "ceremony-integration-and-self-learning"
        / "stories" / "epic-1" / f"story-1.{story_num}.md"
    )
    assert story_path.exists()

    # Verify content
    content = story_path.read_text()
    assert "Implement new feature" in content
    assert "Add user authentication" in content
    assert "CRITICAL" in content
    assert "P0" in content

    action_service.close()


def test_story_content_template_rendering(service, temp_db, tmp_path):
    """Test story content template renders correctly."""
    # Create ceremony
    ceremony_service = CeremonyService(db_path=temp_db)
    ceremony = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro",
        participants="team",
        epic_num=1
    )

    # Create action item
    action_service = ActionItemService(db_path=temp_db)
    action_item = action_service.create(
        title="Fix security vulnerability",
        description="SQL injection in login endpoint",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    # Convert to story
    story_num = service.convert_to_story(
        action_item_id=action_item["id"],
        epic_num=1
    )

    # Read story file
    story_path = (
        tmp_path / "project" / "docs" / "features" / "ceremony-integration-and-self-learning"
        / "stories" / "epic-1" / f"story-1.{story_num}.md"
    )
    content = story_path.read_text()

    # Verify template elements
    assert f"# Story 1.{story_num}: Fix security vulnerability" in content
    assert "**Epic**: Epic 1" in content
    assert "**Status**: Not Started" in content
    assert "**Priority**: P0 (from CRITICAL action item)" in content
    assert "**Source**: Action Item from retrospective ceremony" in content
    assert "SQL injection in login endpoint" in content
    assert "**Original Action Item**: Fix security vulnerability" in content
    assert "## Acceptance Criteria" in content
    assert "## Definition of Done" in content

    ceremony_service.close()
    action_service.close()


def test_stale_low_priority_items_auto_complete(service, temp_db):
    """Test LOW priority items auto-complete after 30 days."""
    # Create old LOW priority items (35 days old)
    action_service = ActionItemService(db_path=temp_db)
    old_date = (datetime.now() - timedelta(days=35)).isoformat()

    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()

        for i in range(3):
            cursor.execute(
                """
                INSERT INTO action_items (title, priority, status, created_at, updated_at, epic_num)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"Old low priority item {i}", ActionItemPriority.LOW.value, "pending", old_date, old_date, 1)
            )

        conn.commit()

    # Auto-complete stale items
    completed = service.auto_complete_stale_items(days_old=30)

    # Verify count
    assert completed == 3

    # Verify items marked complete
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM action_items WHERE priority = ? AND status = 'completed'",
            (ActionItemPriority.LOW.value,)
        )
        count = cursor.fetchone()[0]
        assert count == 3

    action_service.close()


def test_stale_cleanup_only_affects_low_priority(service, temp_db):
    """Test stale cleanup only affects LOW priority, not MEDIUM/HIGH."""
    # Create old items with various priorities (35 days old)
    old_date = (datetime.now() - timedelta(days=35)).isoformat()

    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()

        # LOW priority (should be completed)
        cursor.execute(
            """
            INSERT INTO action_items (title, priority, status, created_at, updated_at, epic_num)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Old low", ActionItemPriority.LOW.value, "pending", old_date, old_date, 1)
        )

        # MEDIUM priority (should NOT be completed)
        cursor.execute(
            """
            INSERT INTO action_items (title, priority, status, created_at, updated_at, epic_num)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Old medium", ActionItemPriority.MEDIUM.value, "pending", old_date, old_date, 1)
        )

        # HIGH priority (should NOT be completed)
        cursor.execute(
            """
            INSERT INTO action_items (title, priority, status, created_at, updated_at, epic_num)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Old high", ActionItemPriority.HIGH.value, "pending", old_date, old_date, 1)
        )

        conn.commit()

    # Auto-complete stale items
    completed = service.auto_complete_stale_items(days_old=30)

    # Verify only LOW priority completed
    assert completed == 1

    # Verify MEDIUM and HIGH still pending
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT status FROM action_items WHERE priority = ?",
            (ActionItemPriority.MEDIUM.value,)
        )
        medium_status = cursor.fetchone()[0]
        assert medium_status == "pending"

        cursor.execute(
            "SELECT status FROM action_items WHERE priority = ?",
            (ActionItemPriority.HIGH.value,)
        )
        high_status = cursor.fetchone()[0]
        assert high_status == "pending"


def test_manual_promotion_bypasses_c8_limit(service, temp_db):
    """Test manual promotion of HIGH priority item bypasses C8 limit."""
    # Create ceremony and CRITICAL action item
    ceremony_service = CeremonyService(db_path=temp_db)
    ceremony = ceremony_service.create_summary(
        ceremony_type="retrospective",
        summary="Test retro",
        participants="team",
        epic_num=1
    )

    action_service = ActionItemService(db_path=temp_db)

    # Create and convert CRITICAL item (uses up the 1 conversion)
    critical_item = action_service.create(
        title="Critical issue",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1,
        metadata={"ceremony_id": ceremony["id"]}
    )

    service.convert_to_story(action_item_id=critical_item["id"], epic_num=1)

    # Now create HIGH priority item
    high_item = action_service.create(
        title="Important issue",
        priority=ActionItemPriority.HIGH.value,
        epic_num=1
    )

    # Manual promotion should fail without override
    with pytest.raises(MaxConversionsExceededError) as exc_info:
        service.convert_to_story(action_item_id=high_item["id"], epic_num=1)

    assert "already has 1 converted action item" in str(exc_info.value)

    # Manual promotion with override should succeed
    story_num = service.convert_to_story(
        action_item_id=high_item["id"],
        epic_num=1,
        manual_override=True
    )

    assert story_num == 2

    # Verify 2 stories now exist
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM story_state WHERE epic_num = 1")
        count = cursor.fetchone()[0]
        assert count == 2

    ceremony_service.close()
    action_service.close()


def test_get_pending_action_items_filters_correctly(service, temp_db):
    """Test get_pending_action_items filters by epic and priority."""
    action_service = ActionItemService(db_path=temp_db)

    # Create items for epic 1
    action_service.create(
        title="Epic 1 critical",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1
    )

    action_service.create(
        title="Epic 1 high",
        priority=ActionItemPriority.HIGH.value,
        epic_num=1
    )

    # Create item for epic 2
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO epic_state (epic_num, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (2, "Epic 2", datetime.now().isoformat(), datetime.now().isoformat())
        )
        conn.commit()

    action_service.create(
        title="Epic 2 critical",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=2
    )

    # Get all pending
    all_items = service.get_pending_action_items()
    assert len(all_items) == 3

    # Filter by epic 1
    epic1_items = service.get_pending_action_items(epic_num=1)
    assert len(epic1_items) == 2

    # Filter by CRITICAL priority
    critical_items = service.get_pending_action_items(priority=ActionItemPriority.CRITICAL)
    assert len(critical_items) == 2

    # Filter by epic 1 and CRITICAL
    epic1_critical = service.get_pending_action_items(
        epic_num=1,
        priority=ActionItemPriority.CRITICAL
    )
    assert len(epic1_critical) == 1
    assert epic1_critical[0]["title"] == "Epic 1 critical"

    action_service.close()


def test_mark_action_item_complete(service, temp_db):
    """Test marking action item as completed."""
    action_service = ActionItemService(db_path=temp_db)

    action_item = action_service.create(
        title="Test item",
        priority=ActionItemPriority.MEDIUM.value,
        epic_num=1
    )

    # Mark complete
    result = service.mark_action_item_complete(
        action_item_id=action_item["id"],
        completed_by="Bob",
        reason="Fixed during Story 1.2"
    )

    # Verify status updated
    assert result["status"] == "completed"
    assert result["completed_at"] is not None

    action_service.close()


def test_action_item_marked_as_converted(service, temp_db):
    """Test action item is marked as converted after story creation."""
    action_service = ActionItemService(db_path=temp_db)

    action_item = action_service.create(
        title="Test item",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1
    )

    # Convert to story
    story_num = service.convert_to_story(action_item_id=action_item["id"], epic_num=1)

    # Verify action item marked as converted
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, metadata FROM action_items WHERE id = ?", (action_item["id"],))
        row = cursor.fetchone()

        assert row[0] == "converted"

        metadata = json.loads(row[1]) if row[1] else {}
        assert metadata.get("converted_to_story") == story_num

    action_service.close()


def test_conversion_tracking_table_created(service, temp_db):
    """Test conversion tracking table is created automatically."""
    # Ensure table creation
    service._ensure_conversion_table()

    # Verify table exists
    with sqlite3.connect(str(temp_db)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='action_item_conversions'"
        )
        table = cursor.fetchone()
        assert table is not None


def test_git_commit_called_on_conversion(service, temp_db):
    """Test git commit is called when converting action item."""
    action_service = ActionItemService(db_path=temp_db)

    action_item = action_service.create(
        title="Test item",
        priority=ActionItemPriority.CRITICAL.value,
        epic_num=1
    )

    # Convert to story
    service.convert_to_story(action_item_id=action_item["id"], epic_num=1)

    # Verify git manager called
    assert service.git_manager.add.called
    assert service.git_manager.commit.called

    # Verify commit message
    commit_message = service.git_manager.commit.call_args[0][0]
    assert "feat(epic-1):" in commit_message
    assert "Story 1.1" in commit_message

    action_service.close()
