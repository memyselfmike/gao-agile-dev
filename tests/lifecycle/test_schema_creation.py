"""
Unit tests for database schema creation and migrations.

Tests cover:
- Schema creation (tables, indexes, constraints)
- Migration execution (up/down)
- Foreign key constraints
- CHECK constraints
- JSON metadata storage
- Performance requirements
"""

import pytest
import sqlite3
import tempfile
import time
import importlib
from pathlib import Path
from datetime import datetime

# Import migration module using importlib to handle numeric prefix
migration_001 = importlib.import_module("gao_dev.lifecycle.migrations.001_create_schema")
Migration001 = migration_001.Migration001
run_migration = migration_001.run_migration

from gao_dev.lifecycle.models import (
    Document,
    DocumentRelationship,
    DocumentType,
    DocumentState,
    RelationshipType,
)


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
def db_connection(temp_db):
    """Create database connection for testing."""
    conn = sqlite3.connect(str(temp_db))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestSchemaCreation:
    """Tests for schema creation."""

    def test_create_documents_table(self, db_connection):
        """Test documents table is created with all fields."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        assert cursor.fetchone() is not None

        # Check table structure
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # Core fields
        assert "id" in columns
        assert "path" in columns
        assert "type" in columns
        assert "state" in columns
        assert "created_at" in columns
        assert "modified_at" in columns

        # Author tracking
        assert "author" in columns

        # Feature linking
        assert "feature" in columns
        assert "epic" in columns
        assert "story" in columns

        # Content hash
        assert "content_hash" in columns

        # Governance fields
        assert "owner" in columns
        assert "reviewer" in columns
        assert "review_due_date" in columns

        # Metadata
        assert "metadata" in columns

    def test_create_relationships_table(self, db_connection):
        """Test document_relationships table is created."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_relationships'"
        )
        assert cursor.fetchone() is not None

        # Check table structure
        cursor.execute("PRAGMA table_info(document_relationships)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "parent_id" in columns
        assert "child_id" in columns
        assert "relationship_type" in columns

    def test_create_fts_table(self, db_connection):
        """Test FTS5 virtual table is created."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents_fts'"
        )
        assert cursor.fetchone() is not None

    def test_create_schema_version_table(self, db_connection):
        """Test schema_version table is created and populated."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute("SELECT version, description FROM schema_version")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "001"
        assert "initial" in row[1].lower()

    def test_schema_creation_performance(self, temp_db):
        """Test schema creation completes in <100ms."""
        conn = sqlite3.connect(str(temp_db))

        start_time = time.time()
        Migration001.up(conn)
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        conn.close()

        assert duration < 100, f"Schema creation took {duration}ms (expected <100ms)"


class TestIndexes:
    """Tests for index creation."""

    def test_all_indexes_created(self, db_connection):
        """Test all required indexes are created."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='documents'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        # Required indexes
        expected_indexes = [
            "idx_documents_type",
            "idx_documents_state",
            "idx_documents_feature",
            "idx_documents_epic",
            "idx_documents_owner",
            "idx_documents_type_state",
            "idx_documents_feature_type",
            "idx_documents_modified_at",
            "idx_documents_review_due_date",
        ]

        for index_name in expected_indexes:
            assert index_name in indexes, f"Index {index_name} not created"

    def test_relationship_index_created(self, db_connection):
        """Test relationship type index is created."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='document_relationships'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        assert "idx_relationships_type" in indexes


class TestConstraints:
    """Tests for database constraints."""

    def test_unique_path_constraint(self, db_connection):
        """Test path uniqueness constraint."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Insert first document
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/test.md", "prd", "draft", "2024-11-05", "2024-11-05"),
        )

        # Try to insert duplicate path
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
            cursor.execute(
                """
                INSERT INTO documents (path, type, state, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("/docs/test.md", "epic", "active", "2024-11-05", "2024-11-05"),
            )

    def test_type_check_constraint(self, db_connection):
        """Test type CHECK constraint."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Try to insert invalid type
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute(
                """
                INSERT INTO documents (path, type, state, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("/docs/test.md", "invalid_type", "draft", "2024-11-05", "2024-11-05"),
            )

    def test_state_check_constraint(self, db_connection):
        """Test state CHECK constraint."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Try to insert invalid state
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute(
                """
                INSERT INTO documents (path, type, state, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("/docs/test.md", "prd", "invalid_state", "2024-11-05", "2024-11-05"),
            )

    def test_relationship_type_check_constraint(self, db_connection):
        """Test relationship_type CHECK constraint."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Create two documents first
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/parent.md", "prd", "active", "2024-11-05", "2024-11-05"),
        )
        parent_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/child.md", "architecture", "draft", "2024-11-05", "2024-11-05"),
        )
        child_id = cursor.lastrowid

        # Try to insert invalid relationship type
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            cursor.execute(
                """
                INSERT INTO document_relationships (parent_id, child_id, relationship_type)
                VALUES (?, ?, ?)
                """,
                (parent_id, child_id, "invalid_relationship"),
            )

    def test_foreign_key_constraint(self, db_connection):
        """Test foreign key constraints are enforced."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Try to insert relationship with non-existent parent
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
            cursor.execute(
                """
                INSERT INTO document_relationships (parent_id, child_id, relationship_type)
                VALUES (?, ?, ?)
                """,
                (9999, 9998, "derived_from"),
            )


class TestDocumentCRUD:
    """Tests for document CRUD operations."""

    def test_insert_document_minimal(self, db_connection):
        """Test inserting document with minimal fields."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/test.md", "prd", "draft", "2024-11-05", "2024-11-05"),
        )

        doc_id = cursor.lastrowid
        assert doc_id > 0

        # Verify inserted
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row["path"] == "/docs/test.md"
        assert row["type"] == "prd"
        assert row["state"] == "draft"

    def test_insert_document_with_governance(self, db_connection):
        """Test inserting document with governance fields."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                path, type, state, created_at, modified_at,
                owner, reviewer, review_due_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "/docs/test.md",
                "prd",
                "active",
                "2024-11-05",
                "2024-11-05",
                "John",
                "Winston",
                "2024-12-05",
            ),
        )

        doc_id = cursor.lastrowid

        # Verify governance fields
        cursor.execute("SELECT owner, reviewer, review_due_date FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row["owner"] == "John"
        assert row["reviewer"] == "Winston"
        assert row["review_due_date"] == "2024-12-05"

    def test_insert_document_with_metadata(self, db_connection):
        """Test inserting document with JSON metadata."""
        Migration001.up(db_connection)

        import json

        metadata = {"tags": ["authentication", "security"], "retention_policy": "archive_after_1_year"}

        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                path, type, state, created_at, modified_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("/docs/test.md", "prd", "draft", "2024-11-05", "2024-11-05", json.dumps(metadata)),
        )

        doc_id = cursor.lastrowid

        # Verify metadata
        cursor.execute("SELECT metadata FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        retrieved_metadata = json.loads(row["metadata"])
        assert retrieved_metadata == metadata

    def test_update_document(self, db_connection):
        """Test updating document."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/test.md", "prd", "draft", "2024-11-05", "2024-11-05"),
        )
        doc_id = cursor.lastrowid

        # Update state
        cursor.execute(
            "UPDATE documents SET state = ?, modified_at = ? WHERE id = ?",
            ("active", "2024-11-06", doc_id),
        )

        # Verify update
        cursor.execute("SELECT state, modified_at FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        assert row["state"] == "active"
        assert row["modified_at"] == "2024-11-06"

    def test_delete_document(self, db_connection):
        """Test deleting document."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/test.md", "prd", "draft", "2024-11-05", "2024-11-05"),
        )
        doc_id = cursor.lastrowid

        # Delete
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        # Verify deleted
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        assert cursor.fetchone() is None


class TestDocumentRelationships:
    """Tests for document relationships."""

    def test_insert_relationship(self, db_connection):
        """Test inserting document relationship."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Create parent and child documents
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/prd.md", "prd", "active", "2024-11-05", "2024-11-05"),
        )
        parent_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/architecture.md", "architecture", "draft", "2024-11-05", "2024-11-05"),
        )
        child_id = cursor.lastrowid

        # Create relationship
        cursor.execute(
            """
            INSERT INTO document_relationships (parent_id, child_id, relationship_type)
            VALUES (?, ?, ?)
            """,
            (parent_id, child_id, "derived_from"),
        )

        # Verify relationship
        cursor.execute(
            "SELECT * FROM document_relationships WHERE parent_id = ? AND child_id = ?",
            (parent_id, child_id),
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["relationship_type"] == "derived_from"

    def test_cascade_delete_relationships(self, db_connection):
        """Test CASCADE DELETE removes relationships when document is deleted."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Create documents and relationship
        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/prd.md", "prd", "active", "2024-11-05", "2024-11-05"),
        )
        parent_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO documents (path, type, state, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("/docs/architecture.md", "architecture", "draft", "2024-11-05", "2024-11-05"),
        )
        child_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO document_relationships (parent_id, child_id, relationship_type)
            VALUES (?, ?, ?)
            """,
            (parent_id, child_id, "derived_from"),
        )

        # Delete parent document
        cursor.execute("DELETE FROM documents WHERE id = ?", (parent_id,))

        # Verify relationship was also deleted (CASCADE)
        cursor.execute(
            "SELECT * FROM document_relationships WHERE parent_id = ?", (parent_id,)
        )
        assert cursor.fetchone() is None


class TestMigrationSystem:
    """Tests for migration system."""

    def test_migration_is_applied(self, db_connection):
        """Test is_applied method."""
        # Before migration
        assert Migration001.is_applied(db_connection) is False

        # Apply migration
        Migration001.up(db_connection)

        # After migration
        assert Migration001.is_applied(db_connection) is True

    def test_migration_up(self, db_connection):
        """Test migration up creates all tables."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Check all tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "documents" in tables
        assert "document_relationships" in tables
        assert "documents_fts" in tables
        assert "schema_version" in tables

    def test_migration_down(self, db_connection):
        """Test migration down removes all tables."""
        Migration001.up(db_connection)
        Migration001.down(db_connection)

        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('documents', 'document_relationships', 'documents_fts')"
        )
        assert len(cursor.fetchall()) == 0

    def test_run_migration_up(self, temp_db):
        """Test run_migration function with 'up' direction."""
        run_migration(temp_db, "up")

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_run_migration_down(self, temp_db):
        """Test run_migration function with 'down' direction."""
        run_migration(temp_db, "up")
        run_migration(temp_db, "down")

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        assert cursor.fetchone() is None
        conn.close()

    def test_run_migration_invalid_direction(self, temp_db):
        """Test run_migration with invalid direction raises error."""
        with pytest.raises(ValueError, match="Invalid direction"):
            run_migration(temp_db, "sideways")


class TestPerformance:
    """Performance tests."""

    def test_bulk_insert_performance(self, db_connection):
        """Test bulk insert of 1000 documents completes in <1 second."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        start_time = time.time()

        # Insert 1000 documents
        for i in range(1000):
            cursor.execute(
                """
                INSERT INTO documents (path, type, state, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (f"/docs/test-{i}.md", "prd", "draft", "2024-11-05", "2024-11-05"),
            )

        db_connection.commit()
        duration = time.time() - start_time

        assert duration < 1.0, f"Bulk insert took {duration}s (expected <1s)"

    def test_indexed_query_performance(self, db_connection):
        """Test query with index completes in <50ms."""
        Migration001.up(db_connection)

        cursor = db_connection.cursor()

        # Insert test data
        for i in range(100):
            cursor.execute(
                """
                INSERT INTO documents (path, type, state, created_at, modified_at, feature)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"/docs/test-{i}.md", "prd", "draft", "2024-11-05", "2024-11-05", "test-feature"),
            )
        db_connection.commit()

        # Query using index
        start_time = time.time()
        cursor.execute(
            "SELECT * FROM documents WHERE type = ? AND state = ?", ("prd", "draft")
        )
        results = cursor.fetchall()
        duration = (time.time() - start_time) * 1000  # Convert to ms

        assert len(results) == 100
        assert duration < 50, f"Indexed query took {duration}ms (expected <50ms)"
