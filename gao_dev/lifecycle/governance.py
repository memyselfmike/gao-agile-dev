"""
Document Governance Module.

This module provides document governance functionality including:
- Ownership management (RACI matrix)
- Review cycle tracking
- Governance rules enforcement
- Review history and reporting

Implements the 5S Sustain principle by maintaining document quality over time.
"""

import csv
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import Document
from gao_dev.lifecycle.exceptions import ValidationError, DocumentNotFoundError


@dataclass
class DocumentReview:
    """
    Record of a document review.

    Tracks who reviewed a document, when, and when the next review is due.
    """

    id: Optional[int]
    document_id: int
    reviewer: str
    reviewed_at: str
    notes: Optional[str]
    next_review_due: Optional[str]


class DocumentGovernance:
    """
    Document governance with ownership and review cycles.

    This class implements the governance framework for document management,
    including:
    - RACI matrix (Responsible, Accountable, Consulted, Informed)
    - Automatic owner/reviewer assignment
    - Review cycle tracking and reminders
    - Governance rules enforcement
    - Review history and reporting

    Implements 5S Sustain principle to maintain document quality over time.
    """

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        governance_config_path: Path,
    ):
        """
        Initialize governance manager.

        Args:
            document_manager: Document lifecycle manager
            governance_config_path: Path to governance.yaml configuration

        Raises:
            FileNotFoundError: If governance config file not found
            ValidationError: If config format is invalid
        """
        self.doc_mgr = document_manager
        self.config = self._load_config(governance_config_path)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        """
        Load governance configuration from YAML file.

        Args:
            path: Path to governance.yaml

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If config file not found
            ValidationError: If YAML is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Governance config not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if not config or "document_governance" not in config:
                    raise ValidationError("Invalid governance config: missing 'document_governance' key")
                return config
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in governance config: {e}")

    def assign_owner(self, doc_id: int, owner: str) -> None:
        """
        Assign document owner.

        Args:
            doc_id: Document ID
            owner: Owner name

        Raises:
            DocumentNotFoundError: If document not found
        """
        self.doc_mgr.registry.update_document(doc_id, owner=owner)

    def assign_reviewer(self, doc_id: int, reviewer: str) -> None:
        """
        Assign document reviewer.

        Args:
            doc_id: Document ID
            reviewer: Reviewer name

        Raises:
            DocumentNotFoundError: If document not found
        """
        self.doc_mgr.registry.update_document(doc_id, reviewer=reviewer)

    def auto_assign_ownership(self, document: Document) -> None:
        """
        Auto-assign owner and reviewer based on RACI matrix.

        This is called when a document is created to automatically assign
        ownership based on the governance configuration.

        Args:
            document: Document to assign ownership to

        Raises:
            ValidationError: If document type not in RACI matrix
        """
        doc_type = document.type.value
        ownership_config = self.config["document_governance"]["ownership"].get(doc_type)

        if not ownership_config:
            # No RACI configuration for this document type
            return

        owner = ownership_config.get("approved_by")
        reviewer = ownership_config.get("reviewed_by")

        if owner and document.id:
            self.assign_owner(document.id, owner)

        if reviewer and document.id:
            self.assign_reviewer(document.id, reviewer)

        # Set initial review due date
        if document.id:
            self._set_review_due_date(document)

    def _set_review_due_date(self, document: Document) -> None:
        """
        Calculate and set review due date based on review cadence.

        Args:
            document: Document to set review due date for
        """
        doc_type = document.type.value
        cadence_days = self.config["document_governance"]["review_cadence"].get(doc_type, 90)

        if cadence_days == -1:
            # Never review (immutable docs like ADRs, test reports)
            return

        due_date = datetime.now() + timedelta(days=cadence_days)
        self.doc_mgr.registry.update_document(
            document.id, review_due_date=due_date.strftime("%Y-%m-%d")
        )

    def get_owned_documents(self, owner: str) -> List[Document]:
        """
        Get all documents owned by a specific person.

        Args:
            owner: Owner name

        Returns:
            List of documents owned by this person
        """
        return self.doc_mgr.registry.query_documents(owner=owner)

    def get_review_queue(self, reviewer: str) -> List[Document]:
        """
        Get documents needing review by a specific reviewer.

        Returns documents where:
        - reviewer field matches the specified reviewer
        - review_due_date is set and in the past or near future (within 7 days)

        Args:
            reviewer: Reviewer name

        Returns:
            List of documents needing review
        """
        # Get all documents assigned to this reviewer
        all_docs = self.doc_mgr.registry.query_documents()
        review_queue = []

        today = datetime.now().date()
        review_window = today + timedelta(days=7)

        for doc in all_docs:
            if doc.reviewer != reviewer:
                continue

            review_due_str = doc.review_due_date
            if not review_due_str:
                continue

            try:
                review_due = datetime.strptime(review_due_str, "%Y-%m-%d").date()
                if review_due <= review_window:
                    review_queue.append(doc)
            except ValueError:
                continue

        return review_queue

    def check_review_due(
        self, owner: Optional[str] = None, include_overdue_only: bool = False
    ) -> List[Document]:
        """
        Get documents needing review.

        Args:
            owner: Optional filter by owner
            include_overdue_only: If True, only return overdue documents;
                                 if False, return documents due within 7 days

        Returns:
            List of documents needing review, sorted by due date
        """
        all_docs = self.doc_mgr.registry.query_documents(owner=owner)

        review_due = []
        today = datetime.now().date()

        for doc in all_docs:
            review_due_date_str = doc.review_due_date

            if not review_due_date_str:
                continue

            try:
                review_due_date = datetime.strptime(review_due_date_str, "%Y-%m-%d").date()

                if include_overdue_only:
                    if review_due_date < today:
                        review_due.append(doc)
                else:
                    # Due within 7 days
                    if review_due_date <= today + timedelta(days=7):
                        review_due.append(doc)

            except ValueError:
                continue

        # Sort by due date (earliest first)
        review_due.sort(key=lambda d: d.review_due_date or "9999-99-99")

        return review_due

    def mark_reviewed(
        self, doc_id: int, reviewer: str, notes: Optional[str] = None
    ) -> DocumentReview:
        """
        Mark document as reviewed.

        This:
        1. Records the review in document_reviews table
        2. Calculates and sets next review due date
        3. Returns the review record

        Args:
            doc_id: Document ID
            reviewer: Who performed the review
            notes: Optional review notes

        Returns:
            DocumentReview record

        Raises:
            DocumentNotFoundError: If document not found
        """
        document = self.doc_mgr.registry.get_document(doc_id)

        # Calculate next review due date
        doc_type = document.type.value
        cadence_days = self.config["document_governance"]["review_cadence"].get(doc_type, 90)

        if cadence_days != -1:
            next_due = datetime.now() + timedelta(days=cadence_days)
            next_due_str = next_due.strftime("%Y-%m-%d")

            # Update review_due_date in document
            self.doc_mgr.registry.update_document(doc_id, review_due_date=next_due_str)
        else:
            next_due_str = None

        # Record review in history
        reviewed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.doc_mgr.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO document_reviews (
                    document_id, reviewer, reviewed_at, notes, next_review_due
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id, reviewer, reviewed_at, notes, next_due_str),
            )

            review_id = cursor.lastrowid

        return DocumentReview(
            id=review_id,
            document_id=doc_id,
            reviewer=reviewer,
            reviewed_at=reviewed_at,
            notes=notes,
            next_review_due=next_due_str,
        )

    def get_review_history(self, doc_id: int) -> List[DocumentReview]:
        """
        Get review history for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of DocumentReview records, most recent first

        Raises:
            DocumentNotFoundError: If document not found
        """
        # Verify document exists
        self.doc_mgr.registry.get_document(doc_id)

        with self.doc_mgr.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM document_reviews
                WHERE document_id = ?
                ORDER BY reviewed_at DESC, id DESC
                """,
                (doc_id,),
            )

            return [
                DocumentReview(
                    id=row["id"],
                    document_id=row["document_id"],
                    reviewer=row["reviewer"],
                    reviewed_at=row["reviewed_at"],
                    notes=row["notes"],
                    next_review_due=row["next_review_due"],
                )
                for row in cursor.fetchall()
            ]

    def generate_governance_report(self, format: str = "markdown") -> str:
        """
        Generate governance compliance report.

        The report includes:
        - Documents needing review (overdue and upcoming)
        - Documents without owners
        - Review statistics by document type

        Args:
            format: Output format ('markdown' or 'csv')

        Returns:
            Formatted report string

        Raises:
            ValueError: If format is invalid
        """
        if format not in ["markdown", "csv"]:
            raise ValueError(f"Invalid format: {format}. Must be 'markdown' or 'csv'.")

        if format == "markdown":
            return self._generate_markdown_report()
        else:
            return self._generate_csv_report()

    def _generate_markdown_report(self) -> str:
        """Generate governance report in Markdown format."""
        report = "# Document Governance Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Documents needing review
        review_due = self.check_review_due(include_overdue_only=False)
        overdue = [d for d in review_due if self._is_overdue(d)]

        report += "## Review Status\n\n"
        report += f"- **Overdue Reviews**: {len(overdue)}\n"
        report += f"- **Due Within 7 Days**: {len(review_due) - len(overdue)}\n"
        report += f"- **Total Needing Review**: {len(review_due)}\n\n"

        if overdue:
            report += "### Overdue Reviews\n\n"
            report += "| Document | Type | Owner | Due Date | Days Overdue | Priority |\n"
            report += "|----------|------|-------|----------|--------------|----------|\n"

            # Sort by priority and days overdue
            sorted_overdue = sorted(
                overdue,
                key=lambda d: (
                    self._get_priority_value(d),
                    -self._days_overdue(d),
                ),
            )

            for doc in sorted_overdue:
                priority = doc.metadata.get("priority", "N/A")
                report += f"| {doc.path} | {doc.type.value} | "
                report += f"{doc.owner or 'N/A'} | "
                report += f"{doc.review_due_date or 'N/A'} | "
                report += f"{self._days_overdue(doc)} | {priority} |\n"

            report += "\n"

        # Documents without owners
        all_docs = self.doc_mgr.registry.query_documents()
        no_owner = [d for d in all_docs if not d.owner]

        if no_owner:
            report += f"### Documents Without Owners ({len(no_owner)})\n\n"
            for doc in no_owner:
                report += f"- {doc.path} ({doc.type.value})\n"
            report += "\n"

        # Review statistics by document type
        report += "## Review Statistics by Document Type\n\n"
        report += "| Document Type | Total | With Owner | Reviewed | Due Soon |\n"
        report += "|---------------|-------|------------|----------|----------|\n"

        from collections import defaultdict

        stats = defaultdict(lambda: {"total": 0, "with_owner": 0, "reviewed": 0, "due_soon": 0})

        for doc in all_docs:
            doc_type = doc.type.value
            stats[doc_type]["total"] += 1
            if doc.owner:
                stats[doc_type]["with_owner"] += 1
            if doc in review_due:
                stats[doc_type]["due_soon"] += 1

            # Check if document has been reviewed
            reviews = self.get_review_history(doc.id)
            if reviews:
                stats[doc_type]["reviewed"] += 1

        for doc_type in sorted(stats.keys()):
            s = stats[doc_type]
            report += f"| {doc_type} | {s['total']} | {s['with_owner']} | "
            report += f"{s['reviewed']} | {s['due_soon']} |\n"

        report += "\n"

        return report

    def _generate_csv_report(self) -> str:
        """Generate governance report in CSV format for compliance audits."""
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Document Path",
            "Type",
            "State",
            "Owner",
            "Reviewer",
            "Review Due Date",
            "Days Overdue",
            "Priority",
            "Last Reviewed",
            "Review Count",
        ])

        # Get all documents needing review
        review_due = self.check_review_due(include_overdue_only=False)

        for doc in review_due:
            reviews = self.get_review_history(doc.id)
            last_reviewed = reviews[0].reviewed_at if reviews else "Never"
            review_count = len(reviews)
            days_overdue = self._days_overdue(doc) if self._is_overdue(doc) else 0
            priority = doc.metadata.get("priority", "N/A")

            writer.writerow([
                doc.path,
                doc.type.value,
                doc.state.value,
                doc.owner or "N/A",
                doc.reviewer or "N/A",
                doc.review_due_date or "N/A",
                days_overdue,
                priority,
                last_reviewed,
                review_count,
            ])

        return output.getvalue()

    def _is_overdue(self, doc: Document) -> bool:
        """
        Check if document review is overdue.

        Args:
            doc: Document to check

        Returns:
            True if review is overdue, False otherwise
        """
        review_due_str = doc.review_due_date
        if not review_due_str:
            return False

        try:
            due_date = datetime.strptime(review_due_str, "%Y-%m-%d").date()
            return due_date < datetime.now().date()
        except ValueError:
            return False

    def _days_overdue(self, doc: Document) -> int:
        """
        Calculate days overdue for a document.

        Args:
            doc: Document to check

        Returns:
            Number of days overdue (0 if not overdue)
        """
        review_due_str = doc.review_due_date
        if not review_due_str:
            return 0

        try:
            due_date = datetime.strptime(review_due_str, "%Y-%m-%d").date()
            delta = datetime.now().date() - due_date
            return max(0, delta.days)
        except ValueError:
            return 0

    def _get_priority_value(self, doc: Document) -> int:
        """
        Get numeric priority value for sorting.

        Args:
            doc: Document to get priority for

        Returns:
            Numeric priority (lower is higher priority)
        """
        priority = doc.metadata.get("priority", "default")
        priority_mapping = self.config["document_governance"].get(
            "priority_mapping", {"P0": 1, "P1": 2, "P2": 3, "P3": 4, "default": 5}
        )
        return priority_mapping.get(priority, 5)

    def can_archive(self, doc_id: int, user_role: str) -> bool:
        """
        Check if user can archive a document.

        Args:
            doc_id: Document ID
            user_role: User's role (e.g., 'owner', 'engineering_manager')

        Returns:
            True if user can archive, False otherwise
        """
        allowed_roles = self.config["document_governance"]["permissions"]["archive"][
            "allowed_roles"
        ]
        return user_role in allowed_roles

    def can_delete(self, doc_id: int, user_role: str) -> bool:
        """
        Check if user can delete a document.

        Args:
            doc_id: Document ID
            user_role: User's role

        Returns:
            True if user can delete, False otherwise
        """
        allowed_roles = self.config["document_governance"]["permissions"]["delete"][
            "allowed_roles"
        ]
        return user_role in allowed_roles

    def get_unowned_documents(self) -> List[Document]:
        """
        Get all documents without an assigned owner.

        Returns:
            List of documents without owner
        """
        all_docs = self.doc_mgr.registry.query_documents()
        return [d for d in all_docs if not d.owner]
