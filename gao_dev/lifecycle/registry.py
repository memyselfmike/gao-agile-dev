"""
Document Registry Implementation.

This module provides the DocumentRegistry class, which is the core data access layer
for document lifecycle operations. It provides thread-safe CRUD operations, query
interface, and relationship management using SQLite.
"""

import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from gao_dev.lifecycle.models import (
    Document,
    DocumentState,
    DocumentType,
    DocumentRelationship,
    RelationshipType,
)
from gao_dev.lifecycle.exceptions import (
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    ValidationError,
    RelationshipError,
    DatabaseError,
)


class DocumentRegistry:
    """
    SQLite-based document registry with CRUD operations.

    This class provides thread-safe document management using a connection-per-thread
    pattern. All database operations are protected by thread-local connections and
    proper transaction handling.

    Thread Safety:
        - Uses thread-local storage for database connections
        - Each thread gets its own connection
        - All operations are transaction-safe

    Performance:
        - Connection reuse within threads
        - Parameterized queries for SQL injection prevention
        - Indexed queries for fast lookups (<50ms)
    """

    def __init__(self, db_path: Path):
        """
        Initialize document registry.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._init_database()

    def close(self) -> None:
        """
        Close all database connections.

        Should be called when done with the registry to release resources.
        Note: This only closes the connection for the current thread.
        For full cleanup across all threads, ensure all threads have completed
        and call close() from each thread, or use the close_all() method with caution.
        """
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

    def _init_database(self) -> None:
        """
        Initialize database schema if not exists.

        Creates all tables and indexes using the migration scripts.
        Applies migrations in order: 001, 002, 003.
        """
        import importlib.util
        import sys
        from pathlib import Path as ImportPath

        migrations = [
            ("001_create_schema.py", "migration_001"),
            ("002_add_transitions_table.py", "migration_002"),
            ("003_add_reviews_table.py", "migration_003"),
        ]

        with self._get_connection() as conn:
            for migration_file, module_name in migrations:
                migration_path = (
                    ImportPath(__file__).parent / "migrations" / migration_file
                )
                spec = importlib.util.spec_from_file_location(module_name, migration_path)
                migration_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(migration_module)

                # Get the Migration class (e.g., Migration001, Migration002)
                migration_num = module_name.split("_")[1]
                migration_class = getattr(migration_module, f"Migration{migration_num}")

                if not migration_class.is_applied(conn):
                    migration_class.up(conn)

    @contextmanager
    def _get_connection(self):
        """
        Get thread-local database connection.

        This context manager ensures:
        - Each thread has its own connection
        - Transactions are committed on success
        - Transactions are rolled back on error
        - Foreign keys are enforced

        Yields:
            sqlite3.Connection: Thread-local database connection
        """
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

    def _validate_doc_type(self, doc_type: str) -> None:
        """
        Validate document type.

        Args:
            doc_type: Document type string

        Raises:
            ValidationError: If document type is invalid
        """
        try:
            DocumentType(doc_type)
        except ValueError:
            valid_types = [t.value for t in DocumentType]
            raise ValidationError(
                f"Invalid document type: {doc_type}. "
                f"Valid types: {', '.join(valid_types)}",
                field="doc_type",
                value=doc_type,
            )

    def _validate_state(self, state: DocumentState) -> None:
        """
        Validate document state.

        Args:
            state: Document state

        Raises:
            ValidationError: If state is invalid
        """
        if not isinstance(state, DocumentState):
            try:
                DocumentState(state)
            except ValueError:
                valid_states = [s.value for s in DocumentState]
                raise ValidationError(
                    f"Invalid document state: {state}. "
                    f"Valid states: {', '.join(valid_states)}",
                    field="state",
                    value=state,
                )

    def _calculate_content_hash(self, path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of file content.

        Args:
            path: File path

        Returns:
            SHA256 hash string, or None if file doesn't exist
        """
        file_path = Path(path)
        if not file_path.exists():
            return None

        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def _row_to_document(self, row: sqlite3.Row) -> Document:
        """
        Convert database row to Document object.

        Args:
            row: SQLite row

        Returns:
            Document instance
        """
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        return Document(
            id=row["id"],
            path=row["path"],
            type=DocumentType(row["type"]),
            state=DocumentState(row["state"]),
            created_at=row["created_at"],
            modified_at=row["modified_at"],
            author=row["author"],
            feature=row["feature"],
            epic=row["epic"],
            story=row["story"],
            content_hash=row["content_hash"],
            owner=row["owner"],
            reviewer=row["reviewer"],
            review_due_date=row["review_due_date"],
            metadata=metadata,
        )

    # CRUD Operations

    def register_document(
        self,
        path: str,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None,
        state: DocumentState = DocumentState.DRAFT,
        owner: Optional[str] = None,
        reviewer: Optional[str] = None,
        feature: Optional[str] = None,
        epic: Optional[int] = None,
        story: Optional[str] = None,
    ) -> Document:
        """
        Register a new document in the registry.

        Args:
            path: Document file path (must be unique)
            doc_type: Document type (prd, architecture, etc.)
            author: Document author
            metadata: Optional metadata dict
            state: Initial state (default: DRAFT)
            owner: Document owner (governance)
            reviewer: Document reviewer (governance)
            feature: Feature name
            epic: Epic number
            story: Story identifier

        Returns:
            Document object with assigned ID

        Raises:
            DocumentAlreadyExistsError: If path already registered
            ValidationError: If invalid data provided
            DatabaseError: If database operation fails
        """
        # Validate inputs
        self._validate_doc_type(doc_type)
        self._validate_state(state)

        # Calculate content hash if file exists
        content_hash = self._calculate_content_hash(path)

        # Extract feature/epic from metadata if not provided
        if metadata:
            feature = feature or metadata.get("feature")
            epic = epic or metadata.get("epic")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO documents (
                        path, type, state, created_at, modified_at,
                        author, feature, epic, story, owner, reviewer,
                        content_hash, metadata
                    ) VALUES (?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        path,
                        doc_type,
                        state.value,
                        author,
                        feature,
                        epic,
                        story,
                        owner,
                        reviewer,
                        content_hash,
                        json.dumps(metadata or {}),
                    ),
                )

                doc_id = cursor.lastrowid

                # Retrieve and return full document
                return self.get_document(doc_id)

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                raise DocumentAlreadyExistsError(
                    f"Document already registered: {path}", path=path
                )
            raise DatabaseError(f"Database integrity error: {e}", original_error=e)
        except Exception as e:
            raise DatabaseError(
                f"Failed to register document: {e}", original_error=e
            )

    def get_document(self, doc_id: int) -> Document:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document object

        Raises:
            DocumentNotFoundError: If document not found
            DatabaseError: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()

                if not row:
                    raise DocumentNotFoundError(
                        f"Document not found: {doc_id}", doc_id=doc_id
                    )

                return self._row_to_document(row)
        except DocumentNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get document: {e}", original_error=e)

    def get_document_by_path(self, path: str) -> Optional[Document]:
        """
        Get document by file path.

        Args:
            path: Document file path

        Returns:
            Document object, or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE path = ?", (path,))
                row = cursor.fetchone()

                return self._row_to_document(row) if row else None
        except Exception as e:
            raise DatabaseError(
                f"Failed to get document by path: {e}", original_error=e
            )

    def update_document(self, doc_id: int, **updates) -> Document:
        """
        Update document metadata.

        Args:
            doc_id: Document ID
            **updates: Fields to update (path, state, author, feature, epic, story,
                      owner, reviewer, review_due_date, content_hash, metadata)

        Returns:
            Updated document

        Raises:
            DocumentNotFoundError: If document not found
            ValidationError: If no valid fields to update or invalid values
            DatabaseError: If database operation fails
        """
        # Verify document exists
        self.get_document(doc_id)

        # Validate state if being updated
        if "state" in updates:
            self._validate_state(updates["state"])
            if isinstance(updates["state"], DocumentState):
                updates["state"] = updates["state"].value

        # Build UPDATE query
        allowed_fields = {
            "path",
            "state",
            "author",
            "feature",
            "epic",
            "story",
            "owner",
            "reviewer",
            "review_due_date",
            "content_hash",
            "metadata",
        }

        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            raise ValidationError("No valid fields to update")

        # Convert metadata to JSON if present
        if "metadata" in update_fields and isinstance(update_fields["metadata"], dict):
            update_fields["metadata"] = json.dumps(update_fields["metadata"])

        # Build SQL
        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        set_clause += ", modified_at = datetime('now')"
        values = list(update_fields.values())
        values.append(doc_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE documents SET {set_clause} WHERE id = ?", values
                )

            return self.get_document(doc_id)
        except Exception as e:
            raise DatabaseError(f"Failed to update document: {e}", original_error=e)

    def delete_document(self, doc_id: int, soft: bool = True) -> None:
        """
        Delete document (soft delete by default).

        Args:
            doc_id: Document ID
            soft: If True, mark as archived; if False, hard delete

        Raises:
            DocumentNotFoundError: If document not found
            DatabaseError: If database operation fails
        """
        # Verify document exists
        self.get_document(doc_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if soft:
                    # Soft delete: mark as archived
                    cursor.execute(
                        """
                        UPDATE documents
                        SET state = ?, modified_at = datetime('now')
                        WHERE id = ?
                        """,
                        (DocumentState.ARCHIVED.value, doc_id),
                    )
                else:
                    # Hard delete: remove from database
                    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        except Exception as e:
            raise DatabaseError(f"Failed to delete document: {e}", original_error=e)

    # Query Interface

    def query_documents(
        self,
        doc_type: Optional[str] = None,
        state: Optional[DocumentState] = None,
        feature: Optional[str] = None,
        epic: Optional[int] = None,
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Query documents with filters.

        All filters are combined with AND logic.

        Args:
            doc_type: Filter by document type
            state: Filter by state
            feature: Filter by feature
            epic: Filter by epic number
            owner: Filter by owner
            tags: Filter by tags (any match)

        Returns:
            List of matching documents

        Raises:
            DatabaseError: If database operation fails
        """
        where_clauses = []
        params = []

        if doc_type:
            self._validate_doc_type(doc_type)
            where_clauses.append("type = ?")
            params.append(doc_type)

        if state:
            self._validate_state(state)
            where_clauses.append("state = ?")
            params.append(state.value)

        if feature:
            where_clauses.append("feature = ?")
            params.append(feature)

        if epic:
            where_clauses.append("epic = ?")
            params.append(epic)

        if owner:
            where_clauses.append("owner = ?")
            params.append(owner)

        if tags:
            # Query JSON array for tags - match any tag
            tag_conditions = " OR ".join(
                "EXISTS (SELECT 1 FROM json_each(metadata, '$.tags') WHERE value = ?)"
                for _ in tags
            )
            where_clauses.append(f"({tag_conditions})")
            params.extend(tags)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM documents WHERE {where_sql}", params)

                return [self._row_to_document(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to query documents: {e}", original_error=e)

    def get_active_document(
        self, doc_type: str, feature: Optional[str] = None
    ) -> Optional[Document]:
        """
        Get current active document of given type.

        Args:
            doc_type: Document type
            feature: Optional feature filter

        Returns:
            Active document, or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        filters = {"doc_type": doc_type, "state": DocumentState.ACTIVE}
        if feature:
            filters["feature"] = feature

        documents = self.query_documents(**filters)
        return documents[0] if documents else None

    def get_documents_by_state(self, state: DocumentState) -> List[Document]:
        """
        Get all documents in given state.

        Args:
            state: Document state

        Returns:
            List of documents in that state

        Raises:
            DatabaseError: If database operation fails
        """
        return self.query_documents(state=state)

    def get_feature_documents(self, feature: str) -> List[Document]:
        """
        Get all documents for a feature.

        Args:
            feature: Feature name

        Returns:
            List of documents for that feature

        Raises:
            DatabaseError: If database operation fails
        """
        return self.query_documents(feature=feature)

    def get_epic_documents(self, epic_num: int) -> List[Document]:
        """
        Get all documents for an epic.

        Args:
            epic_num: Epic number

        Returns:
            List of documents for that epic

        Raises:
            DatabaseError: If database operation fails
        """
        return self.query_documents(epic=epic_num)

    # Relationship Management

    def add_relationship(
        self, parent_id: int, child_id: int, rel_type: RelationshipType
    ) -> DocumentRelationship:
        """
        Create a relationship between two documents.

        Args:
            parent_id: Parent document ID
            child_id: Child document ID
            rel_type: Relationship type

        Returns:
            DocumentRelationship object

        Raises:
            DocumentNotFoundError: If either document not found
            RelationshipError: If relationship already exists
            DatabaseError: If database operation fails
        """
        # Verify both documents exist
        self.get_document(parent_id)
        self.get_document(child_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO document_relationships (parent_id, child_id, relationship_type)
                    VALUES (?, ?, ?)
                    """,
                    (parent_id, child_id, rel_type.value),
                )

                return DocumentRelationship(
                    parent_id=parent_id, child_id=child_id, relationship_type=rel_type
                )
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                raise RelationshipError(
                    f"Relationship already exists: {parent_id} -> {child_id} ({rel_type.value})",
                    parent_id=parent_id,
                    child_id=child_id,
                    relationship_type=rel_type.value,
                )
            raise DatabaseError(f"Database integrity error: {e}", original_error=e)
        except Exception as e:
            raise DatabaseError(
                f"Failed to add relationship: {e}", original_error=e
            )

    def get_relationships(self, doc_id: int) -> List[DocumentRelationship]:
        """
        Get all relationships for a document (both as parent and child).

        Args:
            doc_id: Document ID

        Returns:
            List of DocumentRelationship objects

        Raises:
            DocumentNotFoundError: If document not found
            DatabaseError: If database operation fails
        """
        # Verify document exists
        self.get_document(doc_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM document_relationships
                    WHERE parent_id = ? OR child_id = ?
                    """,
                    (doc_id, doc_id),
                )

                relationships = []
                for row in cursor.fetchall():
                    relationships.append(
                        DocumentRelationship(
                            parent_id=row["parent_id"],
                            child_id=row["child_id"],
                            relationship_type=RelationshipType(row["relationship_type"]),
                        )
                    )

                return relationships
        except Exception as e:
            raise DatabaseError(
                f"Failed to get relationships: {e}", original_error=e
            )

    def get_parent_documents(
        self, doc_id: int, rel_type: Optional[RelationshipType] = None
    ) -> List[Document]:
        """
        Get parent documents for a given document.

        Args:
            doc_id: Child document ID
            rel_type: Optional relationship type filter

        Returns:
            List of parent documents

        Raises:
            DocumentNotFoundError: If document not found
            DatabaseError: If database operation fails
        """
        # Verify document exists
        self.get_document(doc_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if rel_type:
                    cursor.execute(
                        """
                        SELECT d.* FROM documents d
                        INNER JOIN document_relationships r ON d.id = r.parent_id
                        WHERE r.child_id = ? AND r.relationship_type = ?
                        """,
                        (doc_id, rel_type.value),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT d.* FROM documents d
                        INNER JOIN document_relationships r ON d.id = r.parent_id
                        WHERE r.child_id = ?
                        """,
                        (doc_id,),
                    )

                return [self._row_to_document(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(
                f"Failed to get parent documents: {e}", original_error=e
            )

    def get_child_documents(
        self, doc_id: int, rel_type: Optional[RelationshipType] = None
    ) -> List[Document]:
        """
        Get child documents for a given document.

        Args:
            doc_id: Parent document ID
            rel_type: Optional relationship type filter

        Returns:
            List of child documents

        Raises:
            DocumentNotFoundError: If document not found
            DatabaseError: If database operation fails
        """
        # Verify document exists
        self.get_document(doc_id)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if rel_type:
                    cursor.execute(
                        """
                        SELECT d.* FROM documents d
                        INNER JOIN document_relationships r ON d.id = r.child_id
                        WHERE r.parent_id = ? AND r.relationship_type = ?
                        """,
                        (doc_id, rel_type.value),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT d.* FROM documents d
                        INNER JOIN document_relationships r ON d.id = r.child_id
                        WHERE r.parent_id = ?
                        """,
                        (doc_id,),
                    )

                return [self._row_to_document(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(
                f"Failed to get child documents: {e}", original_error=e
            )
