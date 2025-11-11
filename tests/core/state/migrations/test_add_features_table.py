"""Tests for features table migration.

Epic: 34 - Integration & Variables
Story: 34.1 - Schema Migration
"""

import gc
import json
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

from gao_dev.core.state.migrations.add_features_table import (
    AddFeaturesTableMigration,
    Migration002,
)


class TestAddFeaturesTableMigration:
    """Test features table migration."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
            db_path = Path(f.name)
        yield db_path
        # Force garbage collection to close any lingering connections
        gc.collect()
        time.sleep(0.1)  # Small delay for Windows file locking
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                # Windows sometimes keeps file locked, ignore
                pass

    @pytest.fixture
    def fresh_db(self, temp_db: Path) -> Path:
        """Create fresh database with migrations table."""
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                CREATE TABLE migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()
        return temp_db

    @pytest.fixture
    def existing_db(self, temp_db: Path) -> Path:
        """Create database with existing epics and stories."""
        with sqlite3.connect(temp_db) as conn:
            # Create migrations table
            conn.execute("""
                CREATE TABLE migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

            # Create epics table
            conn.execute("""
                CREATE TABLE epics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    epic_num INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'planned',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

            # Create stories table
            conn.execute("""
                CREATE TABLE stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    epic_num INTEGER NOT NULL,
                    story_num INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    UNIQUE(epic_num, story_num)
                )
            """)

            # Insert test data
            conn.execute("INSERT INTO epics (epic_num, name) VALUES (1, 'Test Epic')")
            conn.execute(
                "INSERT INTO stories (epic_num, story_num, title) VALUES (1, 1, 'Test Story')"
            )

            conn.commit()
        return temp_db

    # =====================================================================
    # Test 1: Fresh Database (3 assertions)
    # =====================================================================

    def test_apply_on_fresh_database(self, fresh_db: Path):
        """Test applying migration to fresh database."""
        migration = AddFeaturesTableMigration(fresh_db)

        # Apply migration
        result = migration.apply()

        # Assertion 1: Migration applied successfully
        assert result is True

        # Assertion 2: features table created
        with sqlite3.connect(fresh_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
            )
            assert cursor.fetchone() is not None

        # Assertion 3: All triggers and indexes created
        with sqlite3.connect(fresh_db) as conn:
            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_features%'"
            )
            indexes = cursor.fetchall()
            assert len(indexes) >= 3  # scope, status, scale_level

            # Check triggers
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'features_%'"
            )
            triggers = cursor.fetchall()
            assert len(triggers) >= 4  # completed_at, 3 audit triggers (INSERT, UPDATE, DELETE)

    # =====================================================================
    # Test 2: Existing Database (4 assertions)
    # =====================================================================

    def test_apply_on_existing_database(self, existing_db: Path):
        """Test applying migration to database with existing data."""
        migration = AddFeaturesTableMigration(existing_db)

        # Apply migration
        result = migration.apply()

        # Assertion 1: Migration applied successfully
        assert result is True

        # Assertion 2: features table added
        with sqlite3.connect(existing_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
            )
            assert cursor.fetchone() is not None

        # Assertion 3: Existing epics data preserved
        with sqlite3.connect(existing_db) as conn:
            cursor = conn.execute("SELECT epic_num, name FROM epics")
            epic = cursor.fetchone()
            assert epic is not None
            assert epic[0] == 1
            assert epic[1] == 'Test Epic'

        # Assertion 4: Existing stories data preserved
        with sqlite3.connect(existing_db) as conn:
            cursor = conn.execute("SELECT epic_num, story_num, title FROM stories")
            story = cursor.fetchone()
            assert story is not None
            assert story[0] == 1
            assert story[1] == 1
            assert story[2] == 'Test Story'

    # =====================================================================
    # Test 3: Idempotency (2 assertions)
    # =====================================================================

    def test_idempotency(self, fresh_db: Path):
        """Test running migration twice."""
        migration = AddFeaturesTableMigration(fresh_db)

        # First run
        result1 = migration.apply()

        # Assertion 1: First run applied successfully
        assert result1 is True

        # Second run
        result2 = migration.apply()

        # Assertion 2: Second run detects already applied
        assert result2 is False

    # =====================================================================
    # Test 4: Rollback (3 assertions)
    # =====================================================================

    def test_rollback(self, fresh_db: Path):
        """Test rollback migration."""
        migration = AddFeaturesTableMigration(fresh_db)

        # Apply migration
        migration.apply()

        # Rollback migration
        result = migration.rollback()

        # Assertion 1: Rollback successful
        assert result is True

        # Assertion 2: features table removed
        with sqlite3.connect(fresh_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
            )
            assert cursor.fetchone() is None

        # Assertion 3: Migration record removed
        with sqlite3.connect(fresh_db) as conn:
            cursor = conn.execute(
                "SELECT version FROM migrations WHERE version = ?",
                (AddFeaturesTableMigration.VERSION,)
            )
            assert cursor.fetchone() is None

    # =====================================================================
    # Test 5: Triggers (5 assertions)
    # =====================================================================

    def test_created_at_default(self, fresh_db: Path):
        """Test created_at auto-populated on INSERT via DEFAULT."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level)
                VALUES ('test-feature', 'feature', 'planning', 2)
            """)
            conn.commit()

            cursor = conn.execute("SELECT created_at FROM features WHERE name = 'test-feature'")
            created_at = cursor.fetchone()[0]

            # Assertion 1: created_at is auto-populated by DEFAULT
            assert created_at is not None
            assert len(created_at) > 0

    def test_completed_at_trigger(self, fresh_db: Path):
        """Test completed_at auto-populated when status='complete'."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            # Insert feature
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level)
                VALUES ('test-feature', 'feature', 'planning', 2)
            """)
            conn.commit()

            # Initially completed_at should be NULL
            cursor = conn.execute("SELECT completed_at FROM features WHERE name = 'test-feature'")
            completed_at = cursor.fetchone()[0]
            assert completed_at is None

            # Update status to 'complete'
            conn.execute("UPDATE features SET status = 'complete' WHERE name = 'test-feature'")
            conn.commit()

            # Assertion 2: completed_at is auto-populated
            cursor = conn.execute("SELECT completed_at FROM features WHERE name = 'test-feature'")
            completed_at = cursor.fetchone()[0]
            assert completed_at is not None
            assert len(completed_at) > 0

    def test_audit_insert_trigger(self, fresh_db: Path):
        """Test audit record created on INSERT."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level, description, owner)
                VALUES ('test-feature', 'mvp', 'planning', 3, 'Test description', 'John')
            """)
            conn.commit()

            # Get feature ID
            cursor = conn.execute("SELECT id FROM features WHERE name = 'test-feature'")
            feature_id = cursor.fetchone()[0]

            # Assertion 3: Audit record created
            cursor = conn.execute(
                "SELECT operation, new_value FROM features_audit WHERE feature_id = ?",
                (feature_id,)
            )
            audit = cursor.fetchone()
            assert audit is not None
            assert audit[0] == 'INSERT'

            # Verify new_value contains correct data
            new_value = json.loads(audit[1])
            assert new_value['name'] == 'test-feature'
            assert new_value['scope'] == 'mvp'
            assert new_value['status'] == 'planning'
            assert new_value['scale_level'] == 3
            assert new_value['description'] == 'Test description'
            assert new_value['owner'] == 'John'

    def test_audit_update_trigger(self, fresh_db: Path):
        """Test audit record created on UPDATE."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            # Insert feature
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level, owner)
                VALUES ('test-feature', 'feature', 'planning', 2, 'John')
            """)
            conn.commit()

            # Get feature ID
            cursor = conn.execute("SELECT id FROM features WHERE name = 'test-feature'")
            feature_id = cursor.fetchone()[0]

            # Update feature
            conn.execute(
                "UPDATE features SET status = 'active', owner = 'Winston' WHERE id = ?",
                (feature_id,)
            )
            conn.commit()

            # Assertion 4: Audit record created for UPDATE
            cursor = conn.execute(
                "SELECT operation, old_value, new_value FROM features_audit WHERE feature_id = ? AND operation = 'UPDATE'",
                (feature_id,)
            )
            audit = cursor.fetchone()
            assert audit is not None
            assert audit[0] == 'UPDATE'

            # Verify old and new values
            old_value = json.loads(audit[1])
            new_value = json.loads(audit[2])

            assert old_value['status'] == 'planning'
            assert old_value['owner'] == 'John'
            assert new_value['status'] == 'active'
            assert new_value['owner'] == 'Winston'

    def test_audit_delete_trigger(self, fresh_db: Path):
        """Test audit record created on DELETE."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            # Insert feature
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level, owner)
                VALUES ('test-feature', 'feature', 'planning', 2, 'John')
            """)
            conn.commit()

            # Get feature ID
            cursor = conn.execute("SELECT id FROM features WHERE name = 'test-feature'")
            feature_id = cursor.fetchone()[0]

            # Delete feature
            conn.execute("DELETE FROM features WHERE id = ?", (feature_id,))
            conn.commit()

            # Assertion 5: Audit record created for DELETE
            cursor = conn.execute(
                "SELECT operation, old_value FROM features_audit WHERE feature_id = ? AND operation = 'DELETE'",
                (feature_id,)
            )
            audit = cursor.fetchone()
            assert audit is not None
            assert audit[0] == 'DELETE'

            # Verify old value
            old_value = json.loads(audit[1])
            assert old_value['name'] == 'test-feature'
            assert old_value['status'] == 'planning'
            assert old_value['owner'] == 'John'

    # =====================================================================
    # Additional Tests
    # =====================================================================

    def test_check_constraints(self, fresh_db: Path):
        """Test CHECK constraints on features table."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            # Test invalid scope
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO features (name, scope, status, scale_level)
                    VALUES ('test', 'invalid', 'planning', 2)
                """)

            # Test invalid status
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO features (name, scope, status, scale_level)
                    VALUES ('test', 'feature', 'invalid', 2)
                """)

            # Test invalid scale_level (negative)
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO features (name, scope, status, scale_level)
                    VALUES ('test', 'feature', 'planning', -1)
                """)

            # Test invalid scale_level (too high)
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO features (name, scope, status, scale_level)
                    VALUES ('test', 'feature', 'planning', 5)
                """)

    def test_unique_name_constraint(self, fresh_db: Path):
        """Test UNIQUE constraint on name."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            # Insert first feature
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level)
                VALUES ('test-feature', 'feature', 'planning', 2)
            """)
            conn.commit()

            # Try to insert duplicate name
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO features (name, scope, status, scale_level)
                    VALUES ('test-feature', 'mvp', 'active', 3)
                """)

    def test_migration_version_tracking(self, fresh_db: Path):
        """Test migration version is tracked correctly."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            cursor = conn.execute(
                "SELECT version, applied_at FROM migrations WHERE version = ?",
                (AddFeaturesTableMigration.VERSION,)
            )
            record = cursor.fetchone()

            assert record is not None
            assert record[0] == AddFeaturesTableMigration.VERSION
            assert record[1] is not None  # applied_at timestamp exists

    def test_rollback_not_applied(self, fresh_db: Path):
        """Test rollback when migration not applied."""
        migration = AddFeaturesTableMigration(fresh_db)

        # Try to rollback without applying
        result = migration.rollback()

        # Should return False (nothing to rollback)
        assert result is False

    def test_features_audit_table_created(self, fresh_db: Path):
        """Test features_audit table is created."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        with sqlite3.connect(fresh_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features_audit'"
            )
            assert cursor.fetchone() is not None

    def test_metadata_json_column(self, fresh_db: Path):
        """Test metadata JSON column functionality."""
        migration = AddFeaturesTableMigration(fresh_db)
        migration.apply()

        metadata = {"tags": ["epic-34", "features"], "priority": "high"}

        with sqlite3.connect(fresh_db) as conn:
            conn.execute("""
                INSERT INTO features (name, scope, status, scale_level, metadata)
                VALUES ('test-feature', 'feature', 'planning', 2, ?)
            """, (json.dumps(metadata),))
            conn.commit()

            cursor = conn.execute("SELECT metadata FROM features WHERE name = 'test-feature'")
            stored_metadata = cursor.fetchone()[0]

            assert stored_metadata is not None
            parsed_metadata = json.loads(stored_metadata)
            assert parsed_metadata == metadata


class TestMigration002Wrapper:
    """Test Migration002 wrapper for registry compatibility."""

    @pytest.fixture
    def temp_db(self) -> Path:
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
            db_path = Path(f.name)
        yield db_path
        # Force garbage collection to close any lingering connections
        gc.collect()
        time.sleep(0.1)  # Small delay for Windows file locking
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                # Windows sometimes keeps file locked, ignore
                pass

    def test_migration002_upgrade(self, temp_db: Path):
        """Test Migration002 upgrade method."""
        # Create migrations table
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                CREATE TABLE migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

        # Apply migration
        result = Migration002.upgrade(temp_db)

        assert result is True

        # Verify table created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
            )
            assert cursor.fetchone() is not None

    def test_migration002_downgrade(self, temp_db: Path):
        """Test Migration002 downgrade method."""
        # Create migrations table
        with sqlite3.connect(temp_db) as conn:
            conn.execute("""
                CREATE TABLE migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

        # Apply then rollback
        Migration002.upgrade(temp_db)
        result = Migration002.downgrade(temp_db)

        assert result is True

        # Verify table removed
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='features'"
            )
            assert cursor.fetchone() is None

    def test_migration002_version(self):
        """Test Migration002 version number."""
        assert Migration002.version == 2
        assert Migration002.description == "Add features table with triggers and audit trail"
