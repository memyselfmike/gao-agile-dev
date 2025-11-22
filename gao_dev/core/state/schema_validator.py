"""Schema validator for state tracking database.

Validates that the database schema matches the expected structure,
including tables, indexes, triggers, and foreign key constraints.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Set

import structlog

logger = structlog.get_logger()


class SchemaValidator:
    """Validates database schema matches expected structure."""

    EXPECTED_TABLES: Set[str] = {
        "epics",
        "stories",
        "sprints",
        "story_assignments",
        "workflow_executions",
        "state_changes",
        "schema_version",
        "features",
        "features_audit",
    }

    EXPECTED_INDEXES: Set[str] = {
        "idx_stories_status",
        "idx_stories_epic",
        "idx_stories_priority",
        "idx_stories_owner",
        "idx_stories_epic_status",
        "idx_epics_status",
        "idx_epics_feature",
        "idx_sprints_status",
        "idx_sprints_dates",
        "idx_assignments_sprint",
        "idx_assignments_story",
        "idx_workflow_story",
        "idx_workflow_status",
        "idx_workflow_name",
        "idx_changes_record",
        "idx_features_scope",
        "idx_features_status",
        "idx_features_scale_level",
        "idx_features_audit_feature_id",
    }

    EXPECTED_TRIGGERS: Set[str] = {
        "update_epic_timestamp",
        "update_story_timestamp",
        "update_sprint_timestamp",
        "update_epic_points_on_story_status",
        "update_epic_points_on_story_status_revert",
        "log_story_status_change",
        "log_epic_status_change",
        "log_sprint_status_change",
        "features_completed_at_update",
        "features_audit_insert",
        "features_audit_update",
        "features_audit_delete",
    }

    # Expected columns for each table
    EXPECTED_COLUMNS: Dict[str, Set[str]] = {
        "epics": {
            "id",
            "epic_num",
            "name",
            "feature",
            "goal",
            "description",
            "status",
            "total_points",
            "completed_points",
            "owner",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
            "file_path",
            "content_hash",
            "metadata",
        },
        "stories": {
            "id",
            "epic_num",
            "story_num",
            "title",
            "description",
            "status",
            "priority",
            "points",
            "owner",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
            "due_date",
            "file_path",
            "content_hash",
            "metadata",
            "tags",
        },
        "sprints": {
            "id",
            "sprint_num",
            "name",
            "goal",
            "status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
            "planned_points",
            "completed_points",
            "velocity",
            "metadata",
        },
        "story_assignments": {
            "sprint_num",
            "epic_num",
            "story_num",
            "assigned_at",
        },
        "workflow_executions": {
            "id",
            "workflow_name",
            "phase",
            "epic_num",
            "story_num",
            "status",
            "executor",
            "started_at",
            "completed_at",
            "duration_ms",
            "output",
            "error_message",
            "exit_code",
            "metadata",
            "context_snapshot",
        },
        "state_changes": {
            "id",
            "table_name",
            "record_id",
            "field_name",
            "old_value",
            "new_value",
            "changed_by",
            "changed_at",
            "reason",
        },
        "features": {
            "id",
            "name",
            "scope",
            "status",
            "scale_level",
            "description",
            "owner",
            "created_at",
            "completed_at",
            "metadata",
        },
        "features_audit": {
            "id",
            "feature_id",
            "operation",
            "old_value",
            "new_value",
            "changed_at",
            "changed_by",
        },
    }

    @staticmethod
    def validate_schema(db_path: Path) -> Dict[str, any]:
        """Validate database schema.

        Args:
            db_path: Path to database

        Returns:
            Dict with validation results including:
            - tables_valid: bool
            - indexes_valid: bool
            - triggers_valid: bool
            - columns_valid: bool
            - foreign_keys_enabled: bool
            - errors: List[str]
            - warnings: List[str]
        """
        results = {
            "tables_valid": False,
            "indexes_valid": False,
            "triggers_valid": False,
            "columns_valid": False,
            "foreign_keys_enabled": False,
            "errors": [],
            "warnings": [],
        }

        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Check foreign keys enabled
                cursor = conn.execute("PRAGMA foreign_keys")
                results["foreign_keys_enabled"] = cursor.fetchone()[0] == 1

                if not results["foreign_keys_enabled"]:
                    results["warnings"].append(
                        "Foreign keys not enabled. Run PRAGMA foreign_keys = ON"
                    )

                # Check tables exist
                cursor = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                """
                )
                tables = {row[0] for row in cursor.fetchall()}
                missing_tables = SchemaValidator.EXPECTED_TABLES - tables
                extra_tables = tables - SchemaValidator.EXPECTED_TABLES - {
                    "sqlite_sequence"
                }

                if missing_tables:
                    results["errors"].append(f"Missing tables: {missing_tables}")
                elif extra_tables:
                    results["warnings"].append(f"Unexpected tables: {extra_tables}")
                else:
                    results["tables_valid"] = True

                # Check columns for each table
                columns_valid = True
                for table_name, expected_cols in SchemaValidator.EXPECTED_COLUMNS.items():
                    if table_name not in tables:
                        continue

                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    actual_cols = {row[1] for row in cursor.fetchall()}
                    missing_cols = expected_cols - actual_cols
                    extra_cols = actual_cols - expected_cols

                    if missing_cols:
                        results["errors"].append(
                            f"Table {table_name} missing columns: {missing_cols}"
                        )
                        columns_valid = False
                    if extra_cols:
                        results["warnings"].append(
                            f"Table {table_name} has extra columns: {extra_cols}"
                        )

                results["columns_valid"] = columns_valid

                # Check indexes exist
                cursor = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """
                )
                indexes = {row[0] for row in cursor.fetchall()}
                missing_indexes = SchemaValidator.EXPECTED_INDEXES - indexes
                extra_indexes = indexes - SchemaValidator.EXPECTED_INDEXES

                if missing_indexes:
                    results["errors"].append(f"Missing indexes: {missing_indexes}")
                elif extra_indexes:
                    results["warnings"].append(f"Unexpected indexes: {extra_indexes}")
                else:
                    results["indexes_valid"] = True

                # Check triggers exist
                cursor = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='trigger'
                """
                )
                triggers = {row[0] for row in cursor.fetchall()}
                missing_triggers = SchemaValidator.EXPECTED_TRIGGERS - triggers
                extra_triggers = triggers - SchemaValidator.EXPECTED_TRIGGERS

                if missing_triggers:
                    results["errors"].append(f"Missing triggers: {missing_triggers}")
                elif extra_triggers:
                    results["warnings"].append(f"Unexpected triggers: {extra_triggers}")
                else:
                    results["triggers_valid"] = True

                # Log validation summary
                if results["errors"]:
                    logger.error("schema_validation_failed", errors=results["errors"])
                elif results["warnings"]:
                    logger.warning(
                        "schema_validation_warnings", warnings=results["warnings"]
                    )
                else:
                    logger.info("schema_validation_passed")

        except Exception as e:
            results["errors"].append(f"Validation error: {str(e)}")
            logger.error("schema_validation_error", error=str(e))

        return results

    @staticmethod
    def is_valid(validation_results: Dict[str, any]) -> bool:
        """Check if validation results indicate a valid schema.

        Args:
            validation_results: Results from validate_schema()

        Returns:
            True if schema is valid (no errors)
        """
        return (
            validation_results["tables_valid"]
            and validation_results["indexes_valid"]
            and validation_results["triggers_valid"]
            and validation_results["columns_valid"]
            and len(validation_results["errors"]) == 0
        )

    @staticmethod
    def get_schema_info(db_path: Path) -> Dict[str, any]:
        """Get detailed schema information.

        Args:
            db_path: Path to database

        Returns:
            Dict with schema details
        """
        info = {
            "tables": {},
            "indexes": {},
            "triggers": {},
            "version": None,
        }

        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Get schema version
                try:
                    cursor = conn.execute(
                        "SELECT version, applied_at, description FROM schema_version ORDER BY version DESC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    if row:
                        info["version"] = {
                            "version": row[0],
                            "applied_at": row[1],
                            "description": row[2],
                        }
                except sqlite3.OperationalError:
                    pass  # schema_version table doesn't exist

                # Get table info
                cursor = conn.execute(
                    """
                    SELECT name, sql FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
                )
                for name, sql in cursor.fetchall():
                    info["tables"][name] = sql

                # Get index info
                cursor = conn.execute(
                    """
                    SELECT name, tbl_name, sql FROM sqlite_master
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """
                )
                for name, tbl_name, sql in cursor.fetchall():
                    info["indexes"][name] = {"table": tbl_name, "sql": sql}

                # Get trigger info
                cursor = conn.execute(
                    """
                    SELECT name, tbl_name, sql FROM sqlite_master
                    WHERE type='trigger'
                """
                )
                for name, tbl_name, sql in cursor.fetchall():
                    info["triggers"][name] = {"table": tbl_name, "sql": sql}

        except Exception as e:
            logger.error("get_schema_info_error", error=str(e))

        return info
