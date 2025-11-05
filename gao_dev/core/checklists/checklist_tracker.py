"""
Checklist execution tracking and persistence.

Provides ChecklistTracker for tracking checklist executions in a SQLite database,
recording item-level results, and querying execution history for compliance and
quality gate enforcement.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import ExecutionResult, ItemResult


class ChecklistTracker:
    """
    Tracks checklist execution and results in database.

    Provides methods to:
    - Start tracking a checklist execution
    - Record individual item results
    - Complete execution with overall status calculation
    - Query execution history and results
    - Generate compliance reports

    The tracker uses SQLite for persistence and enforces data integrity
    through foreign key constraints and CHECK constraints.
    """

    def __init__(self, db_path: Path):
        """
        Initialize tracker with database path.

        Args:
            db_path: Path to SQLite database file

        The database schema will be created automatically if it doesn't exist.
        """
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self):
        """Create database schema if it doesn't exist."""
        schema_path = Path(__file__).parent / "migrations" / "001_create_checklist_tables.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        try:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    def track_execution(
        self,
        checklist_name: str,
        checklist_version: str,
        artifact_type: str,
        artifact_id: str,
        executed_by: str,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        workflow_execution_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Start tracking a checklist execution.

        Args:
            checklist_name: Name of checklist being executed
            checklist_version: Version of checklist
            artifact_type: Type of artifact (story, epic, prd, architecture, code)
            artifact_id: ID of artifact
            executed_by: Who is executing (agent or user name)
            epic_num: Epic number if applicable
            story_num: Story number if applicable
            workflow_execution_id: Link to workflow execution
            metadata: Additional metadata

        Returns:
            execution_id for recording item results

        Raises:
            ValueError: If artifact_type is invalid

        Example:
            execution_id = tracker.track_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                epic_num=12,
                story_num=1
            )
        """
        # Validate artifact_type
        valid_types = {"story", "epic", "prd", "architecture", "code"}
        if artifact_type not in valid_types:
            raise ValueError(
                f"Invalid artifact_type: {artifact_type}. Must be one of {valid_types}"
            )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO checklist_executions (
                    checklist_name, checklist_version, artifact_type, artifact_id,
                    epic_num, story_num, workflow_execution_id,
                    executed_by, executed_at, overall_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
            """,
                (
                    checklist_name,
                    checklist_version,
                    artifact_type,
                    artifact_id,
                    epic_num,
                    story_num,
                    workflow_execution_id,
                    executed_by,
                    datetime.now().isoformat(),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def record_item_result(
        self,
        execution_id: int,
        item_id: str,
        status: str,
        item_category: Optional[str] = None,
        notes: Optional[str] = None,
        checked_by: Optional[str] = None,
        evidence_path: Optional[str] = None,
        evidence_metadata: Optional[Dict] = None,
    ):
        """
        Record result for a single checklist item.

        Args:
            execution_id: ID from track_execution()
            item_id: Item ID from checklist definition
            status: pass, fail, skip, or na
            item_category: Category for grouping
            notes: Notes for this item (required for fail/skip)
            checked_by: Who checked this item
            evidence_path: Path to evidence file
            evidence_metadata: Additional evidence metadata

        Raises:
            ValueError: If status is invalid or notes missing for fail/skip
        """
        # Validate status
        valid_statuses = {"pass", "fail", "skip", "na"}
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {status}. Must be one of {valid_statuses}"
            )

        # Require notes for fail/skip
        if status in {"fail", "skip"} and not notes:
            raise ValueError(f"Notes required for status '{status}'")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO checklist_results (
                    execution_id, item_id, item_category, status, notes,
                    checked_at, checked_by, evidence_path, evidence_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    execution_id,
                    item_id,
                    item_category,
                    status,
                    notes,
                    datetime.now().isoformat(),
                    checked_by,
                    evidence_path,
                    json.dumps(evidence_metadata) if evidence_metadata else None,
                ),
            )
            conn.commit()

    def complete_execution(self, execution_id: int, notes: Optional[str] = None) -> str:
        """
        Complete checklist execution and calculate overall status.

        Args:
            execution_id: ID from track_execution()
            notes: Overall execution notes

        Returns:
            overall_status (pass, fail, partial)

        The overall status is calculated as follows:
        - fail: Any required item failed
        - pass: All required items passed (skip/na ignored)
        - partial: Mix of pass/skip/na, no failures

        Example:
            status = tracker.complete_execution(
                execution_id=123,
                notes="All security checks passed"
            )
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Get all item results
            cursor.execute(
                """
                SELECT status FROM checklist_results
                WHERE execution_id = ?
            """,
                (execution_id,),
            )
            statuses = [row[0] for row in cursor.fetchall()]

            if not statuses:
                raise ValueError(
                    f"No item results found for execution {execution_id}"
                )

            # Calculate overall status
            if "fail" in statuses:
                overall_status = "fail"
            elif all(s in {"pass", "skip", "na"} for s in statuses):
                if "pass" in statuses:
                    overall_status = "pass"
                else:
                    overall_status = "partial"
            else:
                overall_status = "partial"

            # Get execution start time to calculate duration
            cursor.execute(
                """
                SELECT executed_at FROM checklist_executions
                WHERE execution_id = ?
            """,
                (execution_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Execution {execution_id} not found")

            executed_at = datetime.fromisoformat(row[0])
            duration_ms = int((datetime.now() - executed_at).total_seconds() * 1000)

            # Update execution record
            cursor.execute(
                """
                UPDATE checklist_executions
                SET overall_status = ?, completed_at = ?, duration_ms = ?, notes = ?
                WHERE execution_id = ?
            """,
                (
                    overall_status,
                    datetime.now().isoformat(),
                    duration_ms,
                    notes,
                    execution_id,
                ),
            )
            conn.commit()

            return overall_status

    def get_execution_results(self, execution_id: int) -> ExecutionResult:
        """
        Get complete execution results including all item results.

        Args:
            execution_id: ID from track_execution()

        Returns:
            ExecutionResult with all item results

        Raises:
            ValueError: If execution not found

        Example:
            result = tracker.get_execution_results(123)
            print(f"Status: {result.overall_status}")
            for item in result.item_results:
                print(f"  {item.item_id}: {item.status}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get execution record
            cursor.execute(
                """
                SELECT checklist_name, checklist_version, artifact_type, artifact_id,
                       epic_num, story_num, executed_by, executed_at, completed_at,
                       overall_status, notes, duration_ms, workflow_execution_id, metadata
                FROM checklist_executions
                WHERE execution_id = ?
            """,
                (execution_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Execution {execution_id} not found")

            # Get item results
            cursor.execute(
                """
                SELECT item_id, item_category, status, notes, checked_at,
                       checked_by, evidence_path, evidence_metadata
                FROM checklist_results
                WHERE execution_id = ?
                ORDER BY checked_at
            """,
                (execution_id,),
            )

            item_results = [
                ItemResult(
                    item_id=r[0],
                    item_category=r[1],
                    status=r[2],
                    notes=r[3],
                    checked_at=datetime.fromisoformat(r[4]) if r[4] else None,
                    checked_by=r[5],
                    evidence_path=r[6],
                    evidence_metadata=json.loads(r[7]) if r[7] else None,
                )
                for r in cursor.fetchall()
            ]

            return ExecutionResult(
                execution_id=execution_id,
                checklist_name=row[0],
                checklist_version=row[1],
                artifact_type=row[2],
                artifact_id=row[3],
                epic_num=row[4],
                story_num=row[5],
                executed_by=row[6],
                executed_at=datetime.fromisoformat(row[7]),
                completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
                overall_status=row[9],
                notes=row[10],
                duration_ms=row[11],
                workflow_execution_id=row[12],
                metadata=json.loads(row[13]) if row[13] else None,
                item_results=item_results,
            )

    def get_story_checklists(
        self, epic_num: int, story_num: int
    ) -> List[ExecutionResult]:
        """
        Get all checklist executions for a story.

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            List of ExecutionResult sorted by execution time (most recent first)

        Example:
            executions = tracker.get_story_checklists(epic=12, story=1)
            for exec in executions:
                print(f"{exec.checklist_name}: {exec.overall_status}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT execution_id
                FROM checklist_executions
                WHERE epic_num = ? AND story_num = ?
                ORDER BY executed_at DESC
            """,
                (epic_num, story_num),
            )

            execution_ids = [row[0] for row in cursor.fetchall()]
            return [self.get_execution_results(eid) for eid in execution_ids]

    def get_failed_items(self, execution_id: int) -> List[ItemResult]:
        """
        Get only failed items with notes.

        Useful for quality gate reporting and identifying issues.

        Args:
            execution_id: ID from track_execution()

        Returns:
            List of ItemResult for failed items only

        Example:
            failed = tracker.get_failed_items(123)
            if failed:
                print("Failed items:")
                for item in failed:
                    print(f"  {item.item_id}: {item.notes}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT item_id, item_category, status, notes, checked_at,
                       checked_by, evidence_path, evidence_metadata
                FROM checklist_results
                WHERE execution_id = ? AND status = 'fail'
                ORDER BY checked_at
            """,
                (execution_id,),
            )

            return [
                ItemResult(
                    item_id=r[0],
                    item_category=r[1],
                    status=r[2],
                    notes=r[3],
                    checked_at=datetime.fromisoformat(r[4]) if r[4] else None,
                    checked_by=r[5],
                    evidence_path=r[6],
                    evidence_metadata=json.loads(r[7]) if r[7] else None,
                )
                for r in cursor.fetchall()
            ]

    def get_checklist_history(
        self, checklist_name: str
    ) -> Tuple[List[ExecutionResult], Dict]:
        """
        Get all executions of a specific checklist with aggregate statistics.

        Args:
            checklist_name: Name of checklist

        Returns:
            Tuple of (executions list, statistics dict)
            Statistics include: total_executions, pass_rate, avg_duration_ms,
            most_failed_items

        Example:
            executions, stats = tracker.get_checklist_history("qa-comprehensive")
            print(f"Pass rate: {stats['pass_rate']:.1%}")
            print(f"Most failed items: {stats['most_failed_items']}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all executions
            cursor.execute(
                """
                SELECT execution_id
                FROM checklist_executions
                WHERE checklist_name = ?
                ORDER BY executed_at DESC
            """,
                (checklist_name,),
            )
            execution_ids = [row[0] for row in cursor.fetchall()]
            executions = [self.get_execution_results(eid) for eid in execution_ids]

            # Calculate statistics
            total_executions = len(executions)
            if total_executions == 0:
                return executions, {
                    "total_executions": 0,
                    "pass_rate": 0.0,
                    "avg_duration_ms": 0,
                    "most_failed_items": [],
                }

            passed = sum(1 for e in executions if e.overall_status == "pass")
            pass_rate = passed / total_executions

            durations = [e.duration_ms for e in executions if e.duration_ms]
            avg_duration_ms = sum(durations) // len(durations) if durations else 0

            # Find most failed items
            cursor.execute(
                """
                SELECT item_id, COUNT(*) as fail_count
                FROM checklist_results
                WHERE execution_id IN (
                    SELECT execution_id FROM checklist_executions
                    WHERE checklist_name = ?
                ) AND status = 'fail'
                GROUP BY item_id
                ORDER BY fail_count DESC
                LIMIT 5
            """,
                (checklist_name,),
            )
            most_failed_items = [(row[0], row[1]) for row in cursor.fetchall()]

            return executions, {
                "total_executions": total_executions,
                "pass_rate": pass_rate,
                "avg_duration_ms": avg_duration_ms,
                "most_failed_items": most_failed_items,
            }

    def get_compliance_report(
        self,
        artifact_type: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict:
        """
        Generate aggregate compliance metrics.

        Args:
            artifact_type: Filter by artifact type (story, epic, etc.)
            date_range: Optional (start_date, end_date) tuple

        Returns:
            Dictionary with compliance metrics including:
            - pass_rate_by_checklist: Pass rates for each checklist
            - trend_data: Time series data for trend analysis
            - quality_bottlenecks: Checklists with lowest pass rates

        Example:
            report = tracker.get_compliance_report(
                artifact_type="story",
                date_range=(start_date, end_date)
            )
            print(f"Overall pass rate: {report['overall_pass_rate']:.1%}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query with filters
            where_clauses = []
            params = []

            if artifact_type:
                where_clauses.append("artifact_type = ?")
                params.append(artifact_type)

            if date_range:
                where_clauses.append("executed_at BETWEEN ? AND ?")
                params.extend([date_range[0].isoformat(), date_range[1].isoformat()])

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Get pass rates by checklist
            cursor.execute(
                f"""
                SELECT checklist_name,
                       COUNT(*) as total,
                       SUM(CASE WHEN overall_status = 'pass' THEN 1 ELSE 0 END) as passed
                FROM checklist_executions
                {where_sql}
                GROUP BY checklist_name
            """,
                params,
            )

            pass_rate_by_checklist = {
                row[0]: {"total": row[1], "passed": row[2], "pass_rate": row[2] / row[1]}
                for row in cursor.fetchall()
            }

            # Get overall metrics
            total_executions = sum(d["total"] for d in pass_rate_by_checklist.values())
            total_passed = sum(d["passed"] for d in pass_rate_by_checklist.values())
            overall_pass_rate = total_passed / total_executions if total_executions > 0 else 0.0

            # Identify quality bottlenecks (lowest pass rates)
            quality_bottlenecks = sorted(
                [
                    (name, data["pass_rate"])
                    for name, data in pass_rate_by_checklist.items()
                ],
                key=lambda x: x[1],
            )[:5]

            return {
                "overall_pass_rate": overall_pass_rate,
                "total_executions": total_executions,
                "total_passed": total_passed,
                "pass_rate_by_checklist": pass_rate_by_checklist,
                "quality_bottlenecks": quality_bottlenecks,
            }

    def get_pending_checklists(
        self, epic_num: int, story_num: int, required_checklists: List[str]
    ) -> List[str]:
        """
        Get required checklists not yet executed for a story.

        Args:
            epic_num: Epic number
            story_num: Story number
            required_checklists: List of required checklist names

        Returns:
            List of checklist names not yet executed

        Example:
            pending = tracker.get_pending_checklists(
                epic_num=12,
                story_num=1,
                required_checklists=["qa-comprehensive", "security-checklist"]
            )
            if pending:
                print(f"Missing checklists: {', '.join(pending)}")
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get completed checklists for this story
            cursor.execute(
                """
                SELECT DISTINCT checklist_name
                FROM checklist_executions
                WHERE epic_num = ? AND story_num = ? AND overall_status != 'in_progress'
            """,
                (epic_num, story_num),
            )

            completed = {row[0] for row in cursor.fetchall()}
            return [c for c in required_checklists if c not in completed]

    def track_batch_execution(
        self,
        checklist_name: str,
        checklist_version: str,
        artifact_type: str,
        artifact_id: str,
        executed_by: str,
        item_results: List[Dict],
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        workflow_execution_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        notes: Optional[str] = None,
    ) -> int:
        """
        Record multiple item results atomically in a single transaction.

        Args:
            checklist_name: Name of checklist being executed
            checklist_version: Version of checklist
            artifact_type: Type of artifact
            artifact_id: ID of artifact
            executed_by: Who is executing
            item_results: List of dicts with item_id, status, notes, etc.
            epic_num: Epic number if applicable
            story_num: Story number if applicable
            workflow_execution_id: Link to workflow execution
            metadata: Additional metadata
            notes: Overall execution notes

        Returns:
            execution_id

        Raises:
            ValueError: If any validation fails (rolls back entire transaction)

        Example:
            execution_id = tracker.track_batch_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                item_results=[
                    {"item_id": "qa-1", "status": "pass"},
                    {"item_id": "qa-2", "status": "fail", "notes": "Missing tests"}
                ]
            )
        """
        # Validate artifact_type
        valid_types = {"story", "epic", "prd", "architecture", "code"}
        if artifact_type not in valid_types:
            raise ValueError(
                f"Invalid artifact_type: {artifact_type}. Must be one of {valid_types}"
            )

        # Validate all item statuses before starting transaction
        valid_statuses = {"pass", "fail", "skip", "na"}
        for item in item_results:
            status = item.get("status")
            if status not in valid_statuses:
                raise ValueError(
                    f"Invalid status: {status}. Must be one of {valid_statuses}"
                )
            if status in {"fail", "skip"} and not item.get("notes"):
                raise ValueError(f"Notes required for status '{status}'")

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.isolation_level = None  # Use autocommit mode, we'll manage transactions
            conn.execute("BEGIN")

            cursor = conn.cursor()

            # Create execution record
            execution_start = datetime.now()
            cursor.execute(
                """
                INSERT INTO checklist_executions (
                    checklist_name, checklist_version, artifact_type, artifact_id,
                    epic_num, story_num, workflow_execution_id,
                    executed_by, executed_at, overall_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
            """,
                (
                    checklist_name,
                    checklist_version,
                    artifact_type,
                    artifact_id,
                    epic_num,
                    story_num,
                    workflow_execution_id,
                    executed_by,
                    execution_start.isoformat(),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            execution_id = cursor.lastrowid

            # Record all item results
            for item in item_results:
                cursor.execute(
                    """
                    INSERT INTO checklist_results (
                        execution_id, item_id, item_category, status, notes,
                        checked_at, checked_by, evidence_path, evidence_metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        execution_id,
                        item["item_id"],
                        item.get("item_category"),
                        item["status"],
                        item.get("notes"),
                        datetime.now().isoformat(),
                        item.get("checked_by"),
                        item.get("evidence_path"),
                        json.dumps(item.get("evidence_metadata")) if item.get("evidence_metadata") else None,
                    ),
                )

            # Calculate overall status
            statuses = [item["status"] for item in item_results]
            if "fail" in statuses:
                overall_status = "fail"
            elif all(s in {"pass", "skip", "na"} for s in statuses):
                if "pass" in statuses:
                    overall_status = "pass"
                else:
                    overall_status = "partial"
            else:
                overall_status = "partial"

            # Complete execution
            duration_ms = int((datetime.now() - execution_start).total_seconds() * 1000)
            cursor.execute(
                """
                UPDATE checklist_executions
                SET overall_status = ?, completed_at = ?, duration_ms = ?, notes = ?
                WHERE execution_id = ?
            """,
                (
                    overall_status,
                    datetime.now().isoformat(),
                    duration_ms,
                    notes,
                    execution_id,
                ),
            )

            conn.execute("COMMIT")
            return execution_id

        except Exception as e:
            conn.execute("ROLLBACK")
            raise ValueError(f"Batch execution failed: {e}") from e
        finally:
            conn.close()

    def import_execution_results(self, data: Dict) -> int:
        """
        Import execution results from JSON/YAML format.

        Useful for CLI-based checklist execution where results are
        captured in a file and then imported.

        Args:
            data: Dictionary with execution data including:
                - checklist_name, checklist_version, artifact_type, artifact_id
                - executed_by, epic_num, story_num
                - item_results: list of item result dicts
                - notes, metadata

        Returns:
            execution_id

        Raises:
            ValueError: If data validation fails

        Example:
            data = {
                "checklist_name": "qa-comprehensive",
                "checklist_version": "1.0",
                "artifact_type": "story",
                "artifact_id": "12.1",
                "executed_by": "Amelia",
                "item_results": [
                    {"item_id": "qa-1", "status": "pass"},
                    {"item_id": "qa-2", "status": "fail", "notes": "Missing tests"}
                ]
            }
            execution_id = tracker.import_execution_results(data)
        """
        # Validate required fields
        required_fields = [
            "checklist_name",
            "checklist_version",
            "artifact_type",
            "artifact_id",
            "executed_by",
            "item_results",
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Use batch execution
        return self.track_batch_execution(
            checklist_name=data["checklist_name"],
            checklist_version=data["checklist_version"],
            artifact_type=data["artifact_type"],
            artifact_id=data["artifact_id"],
            executed_by=data["executed_by"],
            item_results=data["item_results"],
            epic_num=data.get("epic_num"),
            story_num=data.get("story_num"),
            workflow_execution_id=data.get("workflow_execution_id"),
            metadata=data.get("metadata"),
            notes=data.get("notes"),
        )
