"""Feature State Service - Fast feature metadata queries.

This service provides CRUD operations for feature state management with
optimized queries for <5ms performance.

Epic: 32 - State Service Integration
Story: 32.1 - Create FeatureStateService

Design Pattern: Service Layer (following Epic 24 pattern)
Dependencies: sqlite3, structlog
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

import structlog

logger = structlog.get_logger()


class FeatureScope(Enum):
    """Feature scope: MVP or subsequent feature."""
    MVP = "mvp"
    FEATURE = "feature"


class FeatureStatus(Enum):
    """Feature lifecycle status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"


@dataclass
class Feature:
    """Feature metadata model."""
    name: str
    scope: FeatureScope
    status: FeatureStatus
    scale_level: int  # 0-4
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum values as strings."""
        return {
            "id": self.id,
            "name": self.name,
            "scope": self.scope.value if isinstance(self.scope, FeatureScope) else self.scope,
            "status": self.status.value if isinstance(self.status, FeatureStatus) else self.status,
            "scale_level": self.scale_level,
            "description": self.description,
            "owner": self.owner,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": json.dumps(self.metadata) if self.metadata else None,
        }


class FeatureStateService:
    """
    Service for managing feature state in per-project database.

    Follows Epic 24-27 state service pattern:
    - Thread-safe (one connection per method call)
    - <5ms queries (indexed lookups)
    - Per-project isolation (.gao-dev/documents.db)
    - Consistent with other state services

    Thread Safety:
        - Uses thread-local storage for database connections
        - Each thread gets its own connection
        - All operations are transaction-safe

    Performance:
        - Connection reuse within threads
        - Parameterized queries
        - Indexed queries for <5ms lookups

    Example:
        ```python
        service = FeatureStateService(db_path=Path(".gao-dev/documents.db"))

        # Create feature
        feature = service.create_feature(
            name="user-authentication",
            scope=FeatureScope.FEATURE,
            scale_level=3,
            description="User login and registration",
            owner="john"
        )

        # Update status
        service.update_status(
            name="user-authentication",
            status=FeatureStatus.ACTIVE
        )

        # List features
        features = service.list_features(scope=FeatureScope.MVP)

        # Delete feature
        service.delete_feature(name="user-authentication")
        ```
    """

    def __init__(self, project_root: Path):
        """
        Initialize feature state service.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".gao-dev" / "documents.db"
        self._local = threading.local()
        self.logger = logger.bind(service="feature_state")
        self._ensure_table()

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

    def _ensure_table(self) -> None:
        """Create features table if not exists.

        Note: Migration script (Story 34.1) will handle this properly.
        This is just for safety during development.
        """
        with self._get_connection() as conn:
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
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scope ON features(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_status ON features(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_features_scale_level ON features(scale_level)")

    def create_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> Feature:
        """
        Create feature record.

        Args:
            name: Feature name (e.g., "user-auth", "mvp")
            scope: MVP or FEATURE
            scale_level: 0-4
            description: Optional description
            owner: Optional owner

        Returns:
            Feature object with assigned ID

        Raises:
            ValueError: If feature already exists or invalid parameters

        Example:
            ```python
            feature = service.create_feature(
                name="user-auth",
                scope=FeatureScope.FEATURE,
                scale_level=3,
                description="User authentication system",
                owner="john"
            )
            ```
        """
        # Validate scale_level
        if not (0 <= scale_level <= 4):
            raise ValueError(f"scale_level must be between 0 and 4, got {scale_level}")

        now = datetime.utcnow().isoformat()

        # Convert enum to string value
        scope_value = scope.value if isinstance(scope, FeatureScope) else scope

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO features (
                        name, scope, status, scale_level, description, owner,
                        created_at, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        scope_value,
                        FeatureStatus.PLANNING.value,
                        scale_level,
                        description,
                        owner,
                        now,
                        None,  # metadata initially empty
                    ),
                )

                feature_id = cursor.lastrowid

                self.logger.info(
                    "feature_created",
                    name=name,
                    scope=scope_value,
                    scale_level=scale_level,
                    owner=owner,
                )

                # Return the created feature
                fetched = self.get_feature(name)
                return Feature(
                    id=fetched["id"],
                    name=fetched["name"],
                    scope=FeatureScope(fetched["scope"]),
                    status=FeatureStatus(fetched["status"]),
                    scale_level=fetched["scale_level"],
                    description=fetched["description"],
                    owner=fetched["owner"],
                    created_at=fetched["created_at"],
                    completed_at=fetched["completed_at"],
                    metadata=json.loads(fetched["metadata"]) if fetched["metadata"] else {},
                )

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Feature '{name}' already exists") from e
                elif "CHECK constraint failed" in str(e):
                    raise ValueError(f"Invalid parameter value") from e
                raise

    def get_feature(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get feature by name.

        Args:
            name: Feature name

        Returns:
            Feature record as dictionary, or None if not found

        Example:
            ```python
            feature = service.get_feature("user-auth")
            if feature:
                print(feature["status"])
            ```
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM features WHERE name = ?", (name,))

            row = cursor.fetchone()
            if not row:
                return None

            return dict(row)

    def list_features(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[FeatureStatus] = None,
    ) -> List[Feature]:
        """
        List features with optional filters.

        Args:
            scope: Filter by scope (MVP or FEATURE), None for all
            status: Filter by status, None for all

        Returns:
            List of Feature objects

        Example:
            ```python
            # Get all MVP features
            mvp_features = service.list_features(scope=FeatureScope.MVP)

            # Get all active features
            active = service.list_features(status=FeatureStatus.ACTIVE)

            # Get active MVPs
            active_mvps = service.list_features(
                scope=FeatureScope.MVP,
                status=FeatureStatus.ACTIVE
            )
            ```
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query dynamically based on filters
            query = "SELECT * FROM features WHERE 1=1"
            params = []

            if scope is not None:
                scope_value = scope.value if isinstance(scope, FeatureScope) else scope
                query += " AND scope = ?"
                params.append(scope_value)

            if status is not None:
                status_value = status.value if isinstance(status, FeatureStatus) else status
                query += " AND status = ?"
                params.append(status_value)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)

            features = []
            for row in cursor.fetchall():
                features.append(
                    Feature(
                        id=row["id"],
                        name=row["name"],
                        scope=FeatureScope(row["scope"]),
                        status=FeatureStatus(row["status"]),
                        scale_level=row["scale_level"],
                        description=row["description"],
                        owner=row["owner"],
                        created_at=row["created_at"],
                        completed_at=row["completed_at"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                )

            return features

    def update_status(self, name: str, status: FeatureStatus) -> bool:
        """
        Update feature status.

        Args:
            name: Feature name
            status: New status

        Returns:
            True if updated, False if feature not found

        Example:
            ```python
            service.update_status("user-auth", FeatureStatus.ACTIVE)
            ```
        """
        status_value = status.value if isinstance(status, FeatureStatus) else status
        now = datetime.utcnow().isoformat()

        # Set completed_at if transitioning to complete
        completed_at = None
        if status == FeatureStatus.COMPLETE:
            completed_at = now

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if completed_at:
                cursor.execute(
                    """
                    UPDATE features
                    SET status = ?, completed_at = ?
                    WHERE name = ?
                    """,
                    (status_value, completed_at, name),
                )
            else:
                cursor.execute(
                    """
                    UPDATE features
                    SET status = ?
                    WHERE name = ?
                    """,
                    (status_value, name),
                )

            if cursor.rowcount == 0:
                return False

            self.logger.info(
                "feature_status_updated",
                name=name,
                new_status=status_value,
            )

            return True

    def delete_feature(self, name: str) -> bool:
        """
        Delete feature record.

        Args:
            name: Feature name to delete

        Returns:
            True if deleted, False if feature not found

        Example:
            ```python
            if service.delete_feature("user-auth"):
                print("Feature deleted")
            else:
                print("Feature not found")
            ```
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM features WHERE name = ?", (name,))

            if cursor.rowcount == 0:
                return False

            self.logger.info("feature_deleted", name=name)

            return True

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
