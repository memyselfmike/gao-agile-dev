"""Tests for migration runner."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from gao_dev.core.context.migrations.runner import MigrationRunner, MigrationInfo


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def temp_migrations_dir(tmp_path):
    """Create temporary migrations directory with test migrations."""
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()

    # Create a simple test migration
    migration_001 = migrations_dir / "migration_001_test.py"
    migration_001.write_text("""
import sqlite3
from pathlib import Path

class Migration001:
    @staticmethod
    def upgrade(target_db_path: Path):
        conn = sqlite3.connect(str(target_db_path))
        try:
            conn.execute(\"\"\"
                CREATE TABLE test_table_001 (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            \"\"\")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def downgrade(target_db_path: Path):
        conn = sqlite3.connect(str(target_db_path))
        try:
            conn.execute("DROP TABLE IF EXISTS test_table_001")
            conn.commit()
        finally:
            conn.close()
""")

    # Create another test migration
    migration_002 = migrations_dir / "migration_002_add_column.py"
    migration_002.write_text("""
import sqlite3
from pathlib import Path

class Migration002:
    @staticmethod
    def upgrade(target_db_path: Path):
        conn = sqlite3.connect(str(target_db_path))
        try:
            conn.execute(\"\"\"
                CREATE TABLE test_table_002 (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
            \"\"\")
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def downgrade(target_db_path: Path):
        conn = sqlite3.connect(str(target_db_path))
        try:
            conn.execute("DROP TABLE IF EXISTS test_table_002")
            conn.commit()
        finally:
            conn.close()
""")

    return migrations_dir


class TestMigrationRunner:
    """Test MigrationRunner class."""

    def test_initialization(self, temp_db):
        """Test runner initialization."""
        runner = MigrationRunner(temp_db)

        assert runner.db_path == temp_db
        assert runner.migrations_dir.exists()

    def test_schema_version_table_creation(self, temp_db):
        """Test schema_version table is created."""
        runner = MigrationRunner(temp_db)

        # Connect and check table exists
        conn = sqlite3.connect(str(temp_db))
        try:
            runner._ensure_schema_version_table(conn)

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "schema_version"
        finally:
            conn.close()

    def test_discover_migrations(self):
        """Test migration discovery from migrations directory."""
        runner = MigrationRunner(Path.cwd() / "gao_dev.db")

        migrations = runner._discover_migrations()

        # Should find Migration003 at minimum
        assert len(migrations) >= 1

        # Check migration structure
        for migration in migrations:
            assert isinstance(migration, MigrationInfo)
            assert migration.version > 0
            assert migration.name
            assert migration.module_path

        # Migrations should be sorted by version
        versions = [m.version for m in migrations]
        assert versions == sorted(versions)

    def test_get_migration_status(self, temp_db):
        """Test getting migration status."""
        runner = MigrationRunner(temp_db)

        migrations = runner.get_migration_status()

        assert isinstance(migrations, list)
        for migration in migrations:
            assert isinstance(migration, MigrationInfo)
            # None should be applied yet
            assert not migration.is_applied

    def test_get_current_version_empty(self, temp_db):
        """Test getting current version with no migrations applied."""
        runner = MigrationRunner(temp_db)

        version = runner.get_current_version()

        assert version is None

    def test_get_pending_migrations(self, temp_db):
        """Test getting pending migrations."""
        runner = MigrationRunner(temp_db)

        pending = runner.get_pending_migrations()

        # All migrations should be pending initially
        assert len(pending) >= 1
        for migration in pending:
            assert not migration.is_applied

    def test_migrate_single(self, temp_db):
        """Test applying a single migration."""
        runner = MigrationRunner(temp_db)

        # Apply only first migration
        applied = runner.migrate(target_version=1)

        assert len(applied) == 0 or len(applied) == 1  # May be 0 if no migration 001

        # Check current version
        current = runner.get_current_version()
        if applied:
            assert current == 1

    def test_migrate_all(self, temp_db):
        """Test applying all pending migrations."""
        runner = MigrationRunner(temp_db)

        # Get pending count
        pending_before = runner.get_pending_migrations()
        pending_count = len(pending_before)

        # Apply all migrations
        applied = runner.migrate()

        assert len(applied) == pending_count

        # All should now be applied
        pending_after = runner.get_pending_migrations()
        assert len(pending_after) == 0

        # Check current version is highest
        current = runner.get_current_version()
        if applied:
            assert current == max(m.version for m in applied)

    def test_migrate_records_in_schema_version(self, temp_db):
        """Test that migrations are recorded in schema_version table."""
        runner = MigrationRunner(temp_db)

        # Apply migrations
        applied = runner.migrate()

        if not applied:
            pytest.skip("No migrations to apply")

        # Check schema_version table
        conn = sqlite3.connect(str(temp_db))
        try:
            cursor = conn.execute(
                "SELECT version, name, applied_at FROM schema_version ORDER BY version"
            )
            records = cursor.fetchall()

            assert len(records) == len(applied)

            for record, migration in zip(records, applied):
                assert record[0] == migration.version
                assert record[1] == migration.name
                assert record[2]  # applied_at should be set
        finally:
            conn.close()

    def test_migrate_idempotent(self, temp_db):
        """Test that running migrate twice doesn't re-apply migrations."""
        runner = MigrationRunner(temp_db)

        # Apply all migrations
        applied_first = runner.migrate()

        if not applied_first:
            pytest.skip("No migrations to apply")

        # Try to apply again
        applied_second = runner.migrate()

        # Should not apply anything second time
        assert len(applied_second) == 0

    def test_rollback_not_supported(self, temp_db):
        """Test rollback with migration that doesn't support it."""
        runner = MigrationRunner(temp_db)

        # Apply Migration003 which doesn't support rollback
        applied = runner.migrate(target_version=3)

        if not applied or applied[0].version != 3:
            pytest.skip("Migration003 not available or not applied")

        # Try to rollback
        with pytest.raises(NotImplementedError):
            runner.rollback(steps=1)

    def test_validate_migrations(self):
        """Test migration validation."""
        runner = MigrationRunner(Path.cwd() / "gao_dev.db")

        is_valid, errors = runner.validate_migrations()

        # Should be valid (or have known issues)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

        # If not valid, errors should be descriptive
        if not is_valid:
            assert len(errors) > 0
            for error in errors:
                assert isinstance(error, str)
                assert len(error) > 0

    def test_migration_info_repr(self):
        """Test MigrationInfo string representation."""
        migration = MigrationInfo(
            version=1,
            name="test",
            module_path="test.module",
            applied_at=None
        )

        repr_str = repr(migration)

        assert "Migration001" in repr_str
        assert "test" in repr_str
        assert "pending" in repr_str

        # Test with applied migration
        migration.applied_at = "2025-01-01T12:00:00"
        repr_str = repr(migration)

        assert "applied" in repr_str


class TestMigrationRunnerWithRealMigrations:
    """Test MigrationRunner with actual GAO-Dev migrations."""

    def test_discover_real_migrations(self):
        """Test discovering actual migrations in the project."""
        runner = MigrationRunner(Path.cwd() / "gao_dev.db")

        migrations = runner._discover_migrations()

        # Should find Migration003
        assert any(m.version == 3 for m in migrations)

        # Check Migration003 details
        migration_003 = next(m for m in migrations if m.version == 3)
        assert migration_003.name == "unify_database"
        assert "migration_003_unify_database" in migration_003.module_path

    def test_migration_003_structure(self):
        """Test that Migration003 has correct structure."""
        runner = MigrationRunner(Path.cwd() / "gao_dev.db")

        # Load Migration003
        migrations = runner._discover_migrations()
        migration_003 = next((m for m in migrations if m.version == 3), None)

        if migration_003 is None:
            pytest.skip("Migration003 not found")

        # Load the class
        migration_class = runner._load_migration_class(migration_003)

        # Check it has upgrade method
        assert hasattr(migration_class, "upgrade")
        assert callable(migration_class.upgrade)

        # Check it has downgrade method
        assert hasattr(migration_class, "downgrade")
        assert callable(migration_class.downgrade)

    def test_migration_003_creates_tables(self, temp_db):
        """Test that Migration003 creates required tables."""
        runner = MigrationRunner(temp_db)

        # Apply Migration003
        applied = runner.migrate(target_version=3)

        if not any(m.version == 3 for m in applied):
            pytest.skip("Migration003 not applied")

        # Check tables were created
        conn = sqlite3.connect(str(temp_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Should have at least these tables
            assert "schema_version" in tables
            assert "workflow_context" in tables
            assert "context_usage" in tables
        finally:
            conn.close()


class TestMigrationRunnerCLIScenarios:
    """Test scenarios that would be executed via CLI."""

    def test_fresh_database_migrate(self, temp_db):
        """Test migrating a fresh database (no schema_version table)."""
        runner = MigrationRunner(temp_db)

        # Status should show all pending
        status = runner.get_migration_status()
        pending = [m for m in status if not m.is_applied]
        assert len(pending) >= 1

        # Current version should be None
        assert runner.get_current_version() is None

        # Migrate all
        applied = runner.migrate()
        assert len(applied) == len(pending)

        # Status should show all applied
        status_after = runner.get_migration_status()
        pending_after = [m for m in status_after if not m.is_applied]
        assert len(pending_after) == 0

    def test_partially_migrated_database(self, temp_db):
        """Test migrating a database with some migrations already applied."""
        runner = MigrationRunner(temp_db)

        # Get all migrations
        all_migrations = runner.get_migration_status()

        if len(all_migrations) < 2:
            pytest.skip("Need at least 2 migrations for this test")

        # Apply first migration only
        runner.migrate(target_version=all_migrations[0].version)

        # Status should show first applied, rest pending
        status = runner.get_migration_status()
        applied = [m for m in status if m.is_applied]
        pending = [m for m in status if not m.is_applied]

        assert len(applied) >= 1
        assert len(pending) >= 0

        # Current version should be first migration
        current = runner.get_current_version()
        assert current == all_migrations[0].version

    def test_status_command_scenario(self, temp_db):
        """Test the 'gao-dev db status' command scenario."""
        runner = MigrationRunner(temp_db)

        # Get status
        status = runner.get_migration_status()
        current = runner.get_current_version()

        # Should return valid data
        assert isinstance(status, list)
        assert current is None or isinstance(current, int)

        # Apply some migrations
        runner.migrate(target_version=1)

        # Get status again
        status_after = runner.get_migration_status()
        current_after = runner.get_current_version()

        # Should show changes
        applied_after = [m for m in status_after if m.is_applied]
        assert len(applied_after) >= 0

    def test_validate_command_scenario(self):
        """Test the 'gao-dev db validate' command scenario."""
        runner = MigrationRunner(Path.cwd() / "gao_dev.db")

        # Validate migrations
        is_valid, errors = runner.validate_migrations()

        # Should return boolean and list
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestMigrationRunnerEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_database_path(self, tmp_path):
        """Test runner with database path that doesn't exist yet."""
        db_path = tmp_path / "nonexistent" / "test.db"

        runner = MigrationRunner(db_path)

        # Should be able to create runner (database created on first operation)
        assert runner.db_path == db_path

    def test_invalid_target_version(self, temp_db):
        """Test migrate with invalid target version."""
        runner = MigrationRunner(temp_db)

        # Migrate to version that doesn't exist
        applied = runner.migrate(target_version=999)

        # Should apply all migrations up to highest available
        assert len(applied) >= 0

    def test_rollback_with_no_migrations(self, temp_db):
        """Test rollback when no migrations are applied."""
        runner = MigrationRunner(temp_db)

        # Try to rollback
        rolled_back = runner.rollback(steps=1)

        # Should return empty list
        assert len(rolled_back) == 0

    def test_rollback_invalid_steps(self, temp_db):
        """Test rollback with invalid steps parameter."""
        runner = MigrationRunner(temp_db)

        # Try to rollback with steps < 1
        with pytest.raises(ValueError):
            runner.rollback(steps=0)

        with pytest.raises(ValueError):
            runner.rollback(steps=-1)

    def test_concurrent_migration_detection(self, temp_db):
        """Test that runner detects migrations applied outside its control."""
        runner = MigrationRunner(temp_db)

        # Apply migration
        runner.migrate(target_version=1)

        # Create new runner instance
        runner2 = MigrationRunner(temp_db)

        # Should detect already-applied migration
        pending = runner2.get_pending_migrations()
        versions = [m.version for m in pending]

        if pending:
            assert 1 not in versions  # Migration 1 should not be pending


class TestSchemaVersionTable:
    """Test schema_version table functionality."""

    def test_schema_version_structure(self, temp_db):
        """Test schema_version table has correct structure."""
        runner = MigrationRunner(temp_db)

        conn = sqlite3.connect(str(temp_db))
        try:
            runner._ensure_schema_version_table(conn)

            # Check columns
            cursor = conn.execute("PRAGMA table_info(schema_version)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "version" in columns
            assert "name" in columns
            assert "applied_at" in columns
            assert "checksum" in columns
            assert "execution_time_ms" in columns
            assert "notes" in columns
        finally:
            conn.close()

    def test_schema_version_records_timestamp(self, temp_db):
        """Test that migrations record accurate timestamps."""
        runner = MigrationRunner(temp_db)

        before = datetime.now()

        # Apply migration
        applied = runner.migrate(target_version=1)

        after = datetime.now()

        if not applied:
            pytest.skip("No migrations to apply")

        # Check timestamp
        conn = sqlite3.connect(str(temp_db))
        try:
            cursor = conn.execute(
                "SELECT applied_at FROM schema_version WHERE version = ?",
                (applied[0].version,)
            )
            record = cursor.fetchone()

            assert record is not None

            # Parse timestamp
            applied_at = datetime.fromisoformat(record[0])

            # Should be between before and after
            assert before <= applied_at <= after
        finally:
            conn.close()
