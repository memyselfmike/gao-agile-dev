---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 34
  story: 1
  feature: "feature-based-document-structure"
  points: 2
---

# Story 34.1: Schema Migration (2 points)

**Epic:** 34 - Integration & Variables
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **database administrator**,
I want **a migration script for the features table with triggers and audit trail**,
So that **existing projects can adopt the features table safely and new projects get it automatically**.

## Acceptance Criteria

### AC1: Create Migration Script
- [ ] Create `gao_dev/core/state/migrations/add_features_table.py`
- [ ] Migration adds features table to existing databases
- [ ] Migration is idempotent (safe to run multiple times)
- [ ] Migration validates existing schema before applying changes
- [ ] Migration provides rollback capability

### AC2: Features Table Schema
- [ ] Table: `features` with all required columns
- [ ] Columns: id, name, scope, status, scale_level, description, owner, created_at, completed_at, metadata
- [ ] Constraints: name UNIQUE, scope/status CHECK constraints
- [ ] Indexes: scope, status, scale_level
- [ ] JSON metadata column for extensibility

### AC3: Database Triggers
- [ ] Trigger: Auto-update created_at on INSERT (default to current timestamp)
- [ ] Trigger: Auto-update completed_at when status transitions to 'complete'
- [ ] Trigger: Validate scope and status values
- [ ] Trigger: Audit trail (log changes to features_audit table)

### AC4: Audit Trail
- [ ] Create `features_audit` table for change history
- [ ] Columns: id, feature_id, operation, old_value, new_value, changed_at, changed_by
- [ ] Trigger records all INSERT, UPDATE, DELETE operations
- [ ] Queryable audit history

### AC5: Migration Testing
- [ ] Test migration on fresh database (no features table)
- [ ] Test migration on existing database (with epics, stories tables)
- [ ] Test idempotency (run migration twice, no errors)
- [ ] Test rollback (undo migration)
- [ ] Validate all existing data preserved

## Technical Notes

### Implementation Approach

**Migration Script:**

```python
# Location: gao_dev/core/state/migrations/add_features_table.py

import sqlite3
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class AddFeaturesTableMigration:
    """
    Migration to add features table and related infrastructure.

    Features:
    - Creates features table
    - Creates indexes
    - Creates triggers (auto-timestamps, audit trail)
    - Creates features_audit table
    - Idempotent (safe to run multiple times)
    """

    VERSION = "001_add_features_table"

    def __init__(self, db_path: Path):
        """
        Initialize migration.

        Args:
            db_path: Path to documents.db
        """
        self.db_path = db_path

    def apply(self) -> bool:
        """
        Apply migration.

        Returns:
            True if migration applied, False if already applied

        Raises:
            RuntimeError: If migration fails
        """
        logger.info("Applying features table migration", db_path=str(self.db_path))

        # Check if migration already applied
        if self._is_applied():
            logger.info("Migration already applied, skipping")
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create features table
                self._create_features_table(conn)

                # Create indexes
                self._create_indexes(conn)

                # Create audit table
                self._create_audit_table(conn)

                # Create triggers
                self._create_triggers(conn)

                # Record migration
                self._record_migration(conn)

                conn.commit()

            logger.info("Migration applied successfully")
            return True

        except Exception as e:
            logger.error("Migration failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Migration failed: {str(e)}") from e

    def rollback(self) -> bool:
        """
        Rollback migration.

        Returns:
            True if rolled back, False if not applied

        Raises:
            RuntimeError: If rollback fails
        """
        logger.info("Rolling back features table migration", db_path=str(self.db_path))

        if not self._is_applied():
            logger.info("Migration not applied, nothing to rollback")
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Drop triggers
                conn.execute("DROP TRIGGER IF EXISTS features_created_at_default")
                conn.execute("DROP TRIGGER IF EXISTS features_completed_at_update")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_insert")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_update")
                conn.execute("DROP TRIGGER IF EXISTS features_audit_delete")

                # Drop tables
                conn.execute("DROP TABLE IF EXISTS features_audit")
                conn.execute("DROP TABLE IF EXISTS features")

                # Remove migration record
                conn.execute(
                    "DELETE FROM migrations WHERE version = ?",
                    (self.VERSION,)
                )

                conn.commit()

            logger.info("Migration rolled back successfully")
            return True

        except Exception as e:
            logger.error("Rollback failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Rollback failed: {str(e)}") from e

    def _is_applied(self) -> bool:
        """Check if migration already applied."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if migrations table exists
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"
            ).fetchone()

            if not result:
                # Create migrations table
                conn.execute("""
                    CREATE TABLE migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT UNIQUE NOT NULL,
                        applied_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                return False

            # Check if this migration applied
            result = conn.execute(
                "SELECT version FROM migrations WHERE version = ?",
                (self.VERSION,)
            ).fetchone()

            return result is not None

    def _create_features_table(self, conn: sqlite3.Connection) -> None:
        """Create features table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
                status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
                scale_level INTEGER NOT NULL CHECK(scale_level >= 0 AND scale_level <= 4),
                description TEXT,
                owner TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                metadata JSON
            )
        """)
        logger.info("Created features table")

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for performance."""
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scope ON features(scope)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_status ON features(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scale_level ON features(scale_level)")
        logger.info("Created indexes")

    def _create_audit_table(self, conn: sqlite3.Connection) -> None:
        """Create audit trail table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id INTEGER NOT NULL,
                operation TEXT NOT NULL CHECK(operation IN ('INSERT', 'UPDATE', 'DELETE')),
                old_value JSON,
                new_value JSON,
                changed_at TEXT NOT NULL,
                changed_by TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_features_audit_feature_id ON features_audit(feature_id)")
        logger.info("Created audit table")

    def _create_triggers(self, conn: sqlite3.Connection) -> None:
        """Create database triggers."""

        # Trigger 1: Auto-set created_at on INSERT
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_created_at_default
            AFTER INSERT ON features
            FOR EACH ROW
            WHEN NEW.created_at IS NULL
            BEGIN
                UPDATE features SET created_at = datetime('now') WHERE id = NEW.id;
            END
        """)

        # Trigger 2: Auto-set completed_at when status becomes 'complete'
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_completed_at_update
            AFTER UPDATE OF status ON features
            FOR EACH ROW
            WHEN NEW.status = 'complete' AND OLD.status != 'complete'
            BEGIN
                UPDATE features SET completed_at = datetime('now') WHERE id = NEW.id;
            END
        """)

        # Trigger 3: Audit INSERT
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_insert
            AFTER INSERT ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, new_value, changed_at)
                VALUES (
                    NEW.id,
                    'INSERT',
                    json_object(
                        'name', NEW.name,
                        'scope', NEW.scope,
                        'status', NEW.status,
                        'scale_level', NEW.scale_level
                    ),
                    datetime('now')
                );
            END
        """)

        # Trigger 4: Audit UPDATE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_update
            AFTER UPDATE ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, old_value, new_value, changed_at)
                VALUES (
                    NEW.id,
                    'UPDATE',
                    json_object(
                        'name', OLD.name,
                        'scope', OLD.scope,
                        'status', OLD.status,
                        'scale_level', OLD.scale_level
                    ),
                    json_object(
                        'name', NEW.name,
                        'scope', NEW.scope,
                        'status', NEW.status,
                        'scale_level', NEW.scale_level
                    ),
                    datetime('now')
                );
            END
        """)

        # Trigger 5: Audit DELETE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS features_audit_delete
            AFTER DELETE ON features
            FOR EACH ROW
            BEGIN
                INSERT INTO features_audit (feature_id, operation, old_value, changed_at)
                VALUES (
                    OLD.id,
                    'DELETE',
                    json_object(
                        'name', OLD.name,
                        'scope', OLD.scope,
                        'status', OLD.status,
                        'scale_level', OLD.scale_level
                    ),
                    datetime('now')
                );
            END
        """)

        logger.info("Created triggers")

    def _record_migration(self, conn: sqlite3.Connection) -> None:
        """Record migration as applied."""
        conn.execute(
            "INSERT INTO migrations (version, applied_at) VALUES (?, datetime('now'))",
            (self.VERSION,)
        )
        logger.info("Recorded migration", version=self.VERSION)
```

**CLI Command for Migration:**

```python
# Add to gao_dev/cli/commands/migrate.py

@click.command("migrate")
@click.option("--rollback", is_flag=True, help="Rollback migration")
def migrate(rollback: bool):
    """
    Run database migrations.

    Applies pending migrations to bring database schema up to date.

    Examples:

        # Apply migrations
        gao-dev migrate

        # Rollback last migration
        gao-dev migrate --rollback
    """
    project_root = _find_project_root()
    db_path = project_root / ".gao-dev" / "documents.db"

    migration = AddFeaturesTableMigration(db_path)

    if rollback:
        success = migration.rollback()
        if success:
            console.print("[green]Migration rolled back successfully[/green]")
        else:
            console.print("[yellow]No migration to rollback[/yellow]")
    else:
        success = migration.apply()
        if success:
            console.print("[green]Migration applied successfully[/green]")
        else:
            console.print("[yellow]Migration already applied[/yellow]")
```

### Code Locations

**New Files:**
- `gao_dev/core/state/migrations/add_features_table.py` (migration script)
- `gao_dev/core/state/migrations/__init__.py` (migration registry)

**Files to Update:**
- `gao_dev/cli/commands/migrate.py` (add migrate command)
- `gao_dev/core/state/schema.sql` (update with features table for new projects)

### Dependencies

**Required Before Starting:**
- None (can be done in parallel with other stories)

**Blocks:**
- Story 32.1: FeatureStateService (needs features table to exist)

### Integration Points

1. **Existing Database**: Migration preserves all existing data (epics, stories, etc.)
2. **FeatureStateService**: Will use features table created by migration
3. **Audit Trail**: Provides change history for compliance and debugging

## Testing Requirements

### Migration Tests (Validation scenarios)

**Location:** `tests/core/state/migrations/test_add_features_table.py`

**Test Coverage:**

1. **Fresh Database (3 assertions)**
   - Apply migration to empty database
   - features table created
   - All triggers and indexes created

2. **Existing Database (4 assertions)**
   - Apply migration to database with epics, stories
   - features table added
   - Existing data preserved (epics, stories intact)
   - No data loss

3. **Idempotency (2 assertions)**
   - Run migration twice
   - Second run detects already applied (returns False)

4. **Rollback (3 assertions)**
   - Apply migration
   - Rollback migration
   - features table removed, migrations record removed

5. **Triggers (5 assertions)**
   - created_at auto-populated on INSERT
   - completed_at auto-populated when status='complete'
   - Audit record created on INSERT
   - Audit record created on UPDATE
   - Audit record created on DELETE

## Definition of Done

- [ ] Migration script implemented (add_features_table.py)
- [ ] features table schema correct
- [ ] Indexes created for performance
- [ ] Triggers working (auto-timestamps, audit trail)
- [ ] features_audit table created
- [ ] Migration is idempotent
- [ ] Rollback capability verified
- [ ] All migration tests passing
- [ ] Documentation updated (migration guide)
- [ ] Code reviewed and approved

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Database Schema)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Data Models - Database Schema)
- **Schema Reference:** `gao_dev/core/state/schema.sql`
