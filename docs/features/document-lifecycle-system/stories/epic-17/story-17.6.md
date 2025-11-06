# Story 17.6: Migration System

**Epic:** 17 - Context System Integration
**Story Points:** 3
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement database migration runner for schema upgrades and version tracking. This provides a robust system for managing database schema evolution, ensuring existing databases can be upgraded safely, and tracking which migrations have been applied. The system supports both SQL and Python migrations, with rollback capabilities and automatic execution on startup.

---

## Business Value

This story enables safe database evolution and deployment:

- **Safe Upgrades**: Controlled schema changes prevent data loss
- **Version Tracking**: Know exactly which migrations are applied
- **Automatic Migration**: Migrations run on startup (no manual intervention)
- **Rollback Support**: Can undo migrations if issues occur
- **Production Ready**: Enterprise-grade migration system
- **Developer Experience**: Easy to add new migrations
- **Testing**: Migrations tested before deployment
- **Observability**: Migration logs show history
- **Continuous Deployment**: Safe schema evolution in CI/CD
- **Foundation for Growth**: Schema can evolve with features

---

## Acceptance Criteria

### Schema Version Tracking
- [ ] `schema_version` table tracks applied migrations with timestamps
- [ ] Table includes: version, migration_name, applied_at, status
- [ ] Table created automatically on first run
- [ ] Version numbers sequential (001, 002, 003, ...)

### Migration Detection
- [ ] MigrationRunner detects pending migrations automatically
- [ ] Pending = migrations not in schema_version table
- [ ] Migrations discovered from migrations directory
- [ ] Both .sql and .py migration files supported

### Migration Application
- [ ] Migrations applied in order on startup
- [ ] Each migration wrapped in transaction (rollback on error)
- [ ] Migration success recorded in schema_version
- [ ] Migration failure logged with error details
- [ ] Applied migrations skipped on subsequent runs

### Rollback Support
- [ ] Rollback support for last N migrations
- [ ] Each migration can optionally have down() method
- [ ] Rollback removes entry from schema_version
- [ ] Rollback logs changes

### CLI Commands
- [ ] `gao-dev db migrate` CLI command applies pending migrations
- [ ] `gao-dev db rollback [N]` CLI command rolls back migrations
- [ ] `gao-dev db status` shows migration status and version
- [ ] `gao-dev db history` shows all applied migrations

### Logging
- [ ] Migration logs show applied migrations with timestamps
- [ ] Logs include duration for each migration
- [ ] Errors logged with full stack traces
- [ ] Logs written to console and file

### Testing
- [ ] Integration tests verify migration up/down
- [ ] Test pending migration detection
- [ ] Test migration failure handling
- [ ] Test existing databases migrated successfully

### Data Safety
- [ ] Existing databases migrated successfully without data loss
- [ ] Migrations tested with real data
- [ ] Backup recommendation in documentation

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/core/context/migrations/runner.py`

Create migration runner:

```python
from pathlib import Path
from typing import List, Optional
import sqlite3
from datetime import datetime
import structlog

logger = structlog.get_logger()

class Migration:
    """Represents a database migration."""

    def __init__(self, version: str, name: str, path: Path):
        self.version = version
        self.name = name
        self.path = path

    def apply(self, conn: sqlite3.Connection):
        """Apply migration."""
        if self.path.suffix == '.sql':
            # Execute SQL file
            sql = self.path.read_text(encoding='utf-8')
            conn.executescript(sql)
        elif self.path.suffix == '.py':
            # Execute Python migration
            # Import and call up() function
            import importlib.util
            spec = importlib.util.spec_from_file_location(self.name, self.path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.up(conn)

    def rollback(self, conn: sqlite3.Connection):
        """Rollback migration (if supported)."""
        if self.path.suffix == '.py':
            import importlib.util
            spec = importlib.util.spec_from_file_location(self.name, self.path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'down'):
                module.down(conn)
            else:
                raise ValueError(f"Migration {self.name} does not support rollback")
        else:
            raise ValueError(f"SQL migrations do not support rollback")

class MigrationRunner:
    """
    Database migration runner with version tracking.

    Discovers and applies migrations in order, tracking which have been applied.
    Supports both SQL and Python migrations with rollback capabilities.
    """

    def __init__(self, db_path: Path, migrations_dir: Optional[Path] = None):
        """
        Initialize MigrationRunner.

        Args:
            db_path: Path to SQLite database
            migrations_dir: Path to migrations directory (default: auto-detect)
        """
        self.db_path = db_path
        self.migrations_dir = migrations_dir or Path(__file__).parent / "sql"
        self._ensure_version_table()

    def _ensure_version_table(self):
        """Create schema_version table if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version TEXT PRIMARY KEY,
                    migration_name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    duration_ms INTEGER,
                    error_message TEXT
                )
            """)
            conn.commit()

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT version FROM schema_version WHERE status = 'success' ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]

    def discover_migrations(self) -> List[Migration]:
        """Discover all migration files."""
        migrations = []

        # Find .sql files
        for sql_file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., "001_initial.sql" -> "001")
            version = sql_file.stem.split('_')[0]
            name = sql_file.stem
            migrations.append(Migration(version, name, sql_file))

        # Find .py files
        for py_file in sorted(self.migrations_dir.glob("*.py")):
            if py_file.stem == '__init__':
                continue
            version = py_file.stem.split('_')[0]
            name = py_file.stem
            migrations.append(Migration(version, name, py_file))

        return sorted(migrations, key=lambda m: m.version)

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been applied yet."""
        applied = set(self.get_applied_migrations())
        all_migrations = self.discover_migrations()
        return [m for m in all_migrations if m.version not in applied]

    def apply_migration(self, migration: Migration):
        """Apply a single migration."""
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        start_time = datetime.now()

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Apply migration in transaction
                migration.apply(conn)

                # Record success
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                conn.execute(
                    """
                    INSERT INTO schema_version (version, migration_name, status, duration_ms)
                    VALUES (?, ?, 'success', ?)
                    """,
                    (migration.version, migration.name, duration_ms)
                )
                conn.commit()

            logger.info(f"Migration {migration.version} applied successfully ({duration_ms}ms)")

        except Exception as e:
            # Record failure
            logger.error(f"Migration {migration.version} failed: {e}")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO schema_version (version, migration_name, status, error_message)
                    VALUES (?, ?, 'failed', ?)
                    """,
                    (migration.version, migration.name, str(e))
                )
                conn.commit()

            raise

    def apply_pending_migrations(self):
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migrations")

        for migration in pending:
            self.apply_migration(migration)

        logger.info("All migrations applied successfully")

    def rollback_migration(self, migration: Migration):
        """Rollback a single migration."""
        logger.info(f"Rolling back migration {migration.version}: {migration.name}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Rollback migration
                migration.rollback(conn)

                # Remove from schema_version
                conn.execute("DELETE FROM schema_version WHERE version = ?", (migration.version,))
                conn.commit()

            logger.info(f"Migration {migration.version} rolled back successfully")

        except Exception as e:
            logger.error(f"Rollback failed for {migration.version}: {e}")
            raise

    def rollback_last_n(self, n: int = 1):
        """Rollback last N migrations."""
        applied = self.get_applied_migrations()
        to_rollback = applied[-n:]

        logger.info(f"Rolling back {len(to_rollback)} migrations")

        for version in reversed(to_rollback):
            all_migrations = self.discover_migrations()
            migration = next(m for m in all_migrations if m.version == version)
            self.rollback_migration(migration)

        logger.info(f"Rolled back {len(to_rollback)} migrations")

    def get_status(self) -> dict:
        """Get migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "current_version": applied[-1] if applied else None,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": [m.version for m in pending]
        }
```

**File:** `gao_dev/cli/db_commands.py`

Create database management CLI commands:

```python
import click
from rich.console import Console
from rich.table import Table
from gao_dev.core.context.migrations.runner import MigrationRunner
from gao_dev.core.config import get_gao_db_path

console = Console()

@click.group()
def db():
    """Database management commands."""
    pass

@db.command()
def migrate():
    """Apply pending migrations.

    Example:
        gao-dev db migrate
    """
    db_path = get_gao_db_path()
    runner = MigrationRunner(db_path)

    pending = runner.get_pending_migrations()

    if not pending:
        console.print("[green]No pending migrations[/green]")
        return

    console.print(f"[cyan]Applying {len(pending)} migrations...[/cyan]")

    try:
        runner.apply_pending_migrations()
        console.print("[green]All migrations applied successfully[/green]")
    except Exception as e:
        console.print(f"[red]Migration failed: {e}[/red]")
        raise

@db.command()
@click.argument('n', type=int, default=1)
def rollback(n: int):
    """Rollback last N migrations.

    Example:
        gao-dev db rollback
        gao-dev db rollback 3
    """
    db_path = get_gao_db_path()
    runner = MigrationRunner(db_path)

    try:
        runner.rollback_last_n(n)
        console.print(f"[green]Rolled back {n} migrations[/green]")
    except Exception as e:
        console.print(f"[red]Rollback failed: {e}[/red]")
        raise

@db.command()
def status():
    """Show migration status.

    Example:
        gao-dev db status
    """
    db_path = get_gao_db_path()
    runner = MigrationRunner(db_path)

    status = runner.get_status()

    console.print(f"[bold cyan]Database Migration Status[/bold cyan]")
    console.print(f"Current Version: {status['current_version']}")
    console.print(f"Applied Migrations: {status['applied_count']}")
    console.print(f"Pending Migrations: {status['pending_count']}")

    if status['pending_migrations']:
        console.print("\n[yellow]Pending:[/yellow]")
        for version in status['pending_migrations']:
            console.print(f"  - {version}")

@db.command()
def history():
    """Show all applied migrations.

    Example:
        gao-dev db history
    """
    db_path = get_gao_db_path()

    import sqlite3
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT version, migration_name, applied_at, status, duration_ms
            FROM schema_version
            ORDER BY version
        """)

        table = Table(title="Migration History")
        table.add_column("Version", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Applied", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Duration", style="blue")

        for row in cursor:
            version, name, applied_at, status, duration_ms = row
            duration = f"{duration_ms}ms" if duration_ms else "N/A"
            table.add_row(version, name, applied_at, status, duration)

        console.print(table)
```

**Files to Create:**
- `gao_dev/core/context/migrations/__init__.py`
- `gao_dev/core/context/migrations/runner.py` - Migration runner
- `gao_dev/core/context/migrations/sql/003_unify_database.sql` - Migration from Story 17.2
- `gao_dev/cli/db_commands.py` - CLI commands
- `tests/core/context/test_migration_runner.py` - Unit tests

**Files to Modify:**
- `gao_dev/cli/commands.py` - Register db command group
- `gao_dev/core/context/persistence.py` - Auto-run migrations on startup

**Dependencies:**
- Story 17.2 (Database Unification - provides migration 003)

---

## Testing Requirements

### Unit Tests

**Migration Discovery:**
- [ ] Test discover_migrations finds .sql files
- [ ] Test discover_migrations finds .py files
- [ ] Test migrations sorted by version
- [ ] Test ignores __init__.py

**Migration Application:**
- [ ] Test apply_migration executes SQL
- [ ] Test apply_migration records success in schema_version
- [ ] Test apply_migration records failure
- [ ] Test applied migration skipped on second run

**Pending Detection:**
- [ ] Test get_pending_migrations detects unapplied
- [ ] Test get_pending_migrations returns empty when all applied
- [ ] Test pending migrations sorted correctly

**Rollback:**
- [ ] Test rollback_migration executes down()
- [ ] Test rollback removes from schema_version
- [ ] Test rollback_last_n rolls back multiple
- [ ] Test rollback fails gracefully for SQL migrations

**Status:**
- [ ] Test get_status returns correct counts
- [ ] Test get_status returns current version
- [ ] Test get_status lists pending migrations

### Integration Tests
- [ ] Test full migration cycle (apply + rollback)
- [ ] Test migration with real database
- [ ] Test concurrent migration attempts (locking)
- [ ] Test migration failure recovery
- [ ] Test existing database migration (no data loss)

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Migration system documentation
- [ ] How to create new migrations guide
- [ ] Migration naming conventions
- [ ] SQL vs Python migration comparison
- [ ] Rollback best practices
- [ ] Backup recommendations
- [ ] Troubleshooting guide
- [ ] CLI command reference

---

## Implementation Details

### Development Approach

**Phase 1: Core Runner**
1. Create Migration and MigrationRunner classes
2. Implement schema_version table
3. Implement migration discovery
4. Implement apply_migration

**Phase 2: CLI Commands**
1. Create db command group
2. Implement migrate, rollback, status commands
3. Add Rich formatting

**Phase 3: Testing**
1. Write unit tests for runner
2. Write integration tests with real DB
3. Test with migration 003 from Story 17.2

**Phase 4: Auto-Migration**
1. Add auto-run on startup
2. Test with existing databases
3. Verify no data loss

### Quality Gates
- [ ] All unit tests pass
- [ ] Migration 003 applies successfully
- [ ] Rollback works correctly
- [ ] Existing databases migrate without data loss
- [ ] CLI commands work correctly
- [ ] Documentation complete

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] `schema_version` table tracks applied migrations
- [ ] MigrationRunner detects pending migrations
- [ ] Migrations applied in order on startup
- [ ] Rollback support for last N migrations
- [ ] `gao-dev db migrate` applies pending migrations
- [ ] `gao-dev db rollback [N]` rolls back migrations
- [ ] `gao-dev db status` shows migration status
- [ ] `gao-dev db history` shows all applied migrations
- [ ] Migration logs show applied migrations
- [ ] Integration tests pass (>80% coverage)
- [ ] Existing databases migrated successfully
- [ ] Code reviewed and approved
- [ ] Documentation complete with guide
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.6 - Migration System

  - Create MigrationRunner for database schema evolution
  - Implement schema_version table for version tracking
  - Support both SQL and Python migration files
  - Implement migration discovery and application
  - Add rollback support for last N migrations
  - Create gao-dev db CLI commands (migrate, rollback, status, history)
  - Auto-run migrations on database startup
  - Add transaction wrapping for safe migrations
  - Implement migration logging and error handling
  - Add integration tests for full migration cycle

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
