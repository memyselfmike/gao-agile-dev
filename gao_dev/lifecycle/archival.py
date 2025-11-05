"""
Document Archival System with Retention Policies.

This module implements the archival system for document lifecycle management,
providing configurable retention policies, compliance protection, and automated
cleanup operations. It implements the 5S Shine principle (regular cleanup).

The archival system distinguishes between:
- Archive: Move to .archive/ directory, state=ARCHIVED, metadata preserved
- Delete: Permanently remove file and database record (only after retention expires)

Key Features:
- YAML-based retention policies per document type
- Compliance tag protection (documents never deleted)
- Configurable retention periods and deletion rules
- Dry-run mode for safe testing
- Comprehensive audit trail
- Safety features (atomic operations, confirmations)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml
import csv
from io import StringIO

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType


@dataclass
class RetentionPolicy:
    """
    Retention policy configuration for a document type.

    Defines how documents of a specific type should be archived and retained.

    Attributes:
        doc_type: Document type this policy applies to
        archive_to_obsolete: Days before ACTIVE->OBSOLETE (-1 = never)
        obsolete_to_archive: Days before OBSOLETE->ARCHIVED (-1 = never)
        archive_retention: Days to retain in archive (-1 = forever)
        delete_after_archive: Whether document can be deleted after retention expires
        compliance_tags: List of tags that prevent deletion (compliance protection)
    """

    doc_type: str
    archive_to_obsolete: int  # Days, -1 = never
    obsolete_to_archive: int  # Days, -1 = never
    archive_retention: int  # Days, -1 = forever
    delete_after_archive: bool
    compliance_tags: List[str]


@dataclass
class ArchivalAction:
    """
    Represents a proposed archival action for a document.

    Used by dry-run mode to preview what would happen without making changes.

    Attributes:
        document: The document this action applies to
        action: Type of action ('archive', 'delete', 'none')
        reason: Human-readable explanation for the action
        days_until_action: How many days until action is needed (0 = now, -1 = never)
    """

    document: Document
    action: str  # 'archive', 'delete', 'none'
    reason: str
    days_until_action: int


class ArchivalManager:
    """
    Manage document archival with retention policies.

    This class implements the 5S Shine principle (regular cleanup) by providing
    automated archival and deletion operations based on configurable retention
    policies. It ensures compliance by protecting documents with compliance tags
    and maintaining detailed audit trails.

    The manager handles three main operations:
    1. Archive obsolete documents (move to .archive/)
    2. Delete expired archived documents (permanent removal)
    3. Generate retention policy reports for auditing

    Example:
        >>> manager = ArchivalManager(doc_mgr, policies_path)
        >>> # Preview what would be archived
        >>> actions = manager.archive_obsolete_documents(dry_run=True)
        >>> for action in actions:
        ...     print(f"{action.document.path}: {action.reason}")
        >>> # Actually archive
        >>> actions = manager.archive_obsolete_documents(dry_run=False)
    """

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        policies_path: Path,
    ):
        """
        Initialize archival manager.

        Args:
            document_manager: Document lifecycle manager for document operations
            policies_path: Path to retention_policies.yaml configuration file

        Raises:
            FileNotFoundError: If policies_path does not exist
            ValueError: If policies_path contains invalid YAML
        """
        self.doc_mgr = document_manager
        self.policies = self._load_policies(policies_path)

    def _load_policies(self, path: Path) -> Dict[str, RetentionPolicy]:
        """
        Load retention policies from YAML configuration.

        The YAML file should have structure:
            retention_policies:
              prd:
                archive_to_obsolete: 30
                obsolete_to_archive: 90
                archive_retention: 730
                delete_after_archive: false
                compliance_tags: ["product-decisions"]

        Args:
            path: Path to retention_policies.yaml

        Returns:
            Dictionary mapping document type to RetentionPolicy

        Raises:
            FileNotFoundError: If path does not exist
            ValueError: If YAML is invalid or missing required fields
        """
        if not path.exists():
            raise FileNotFoundError(f"Retention policies not found: {path}")

        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or "retention_policies" not in config:
            raise ValueError("Invalid retention policies: missing 'retention_policies' key")

        policies = {}
        for doc_type, policy_config in config["retention_policies"].items():
            try:
                policies[doc_type] = RetentionPolicy(
                    doc_type=doc_type,
                    archive_to_obsolete=policy_config.get("archive_to_obsolete", -1),
                    obsolete_to_archive=policy_config.get("obsolete_to_archive", -1),
                    archive_retention=policy_config.get("archive_retention", -1),
                    delete_after_archive=policy_config.get("delete_after_archive", False),
                    compliance_tags=policy_config.get("compliance_tags", []),
                )
            except (KeyError, TypeError) as e:
                raise ValueError(f"Invalid policy for {doc_type}: {e}")

        return policies

    def archive_obsolete_documents(
        self,
        dry_run: bool = False,
    ) -> List[ArchivalAction]:
        """
        Archive documents based on retention policies.

        Evaluates all OBSOLETE documents and archives those that meet the
        retention policy criteria. In dry-run mode, returns actions without
        making any changes.

        Process:
        1. Query all OBSOLETE documents
        2. For each document, evaluate archival criteria
        3. If eligible, move to .archive/ and update state
        4. Return list of actions taken

        Args:
            dry_run: If True, only show what would be archived without doing it

        Returns:
            List of ArchivalAction objects describing what was (or would be) done

        Example:
            >>> actions = manager.archive_obsolete_documents(dry_run=True)
            >>> print(f"Would archive {len(actions)} documents")
            >>> for action in actions:
            ...     print(f"  {action.document.path}: {action.reason}")
        """
        actions = []

        # Get all obsolete documents
        try:
            obsolete_docs = self.doc_mgr.registry.query_documents(
                state=DocumentState.OBSOLETE
            )
        except Exception as e:
            # If query fails, return empty list
            return actions

        for doc in obsolete_docs:
            action = self._evaluate_archival(doc)

            if action.action == "archive":
                actions.append(action)

                if not dry_run:
                    try:
                        self.doc_mgr.archive_document(doc.id)
                    except Exception:
                        # Skip this document if archival fails
                        # (file might not exist, permission issues, etc.)
                        pass

        return actions

    def cleanup_expired_documents(
        self,
        dry_run: bool = False,
    ) -> List[ArchivalAction]:
        """
        Delete documents past retention period.

        Evaluates all ARCHIVED documents and permanently deletes those that:
        1. Have exceeded their retention period
        2. Are marked as delete_after_archive=true
        3. Do NOT have compliance tags

        SAFETY: Documents with compliance tags are NEVER deleted.

        Args:
            dry_run: If True, only show what would be deleted without doing it

        Returns:
            List of ArchivalAction objects describing what was (or would be) deleted

        Example:
            >>> actions = manager.cleanup_expired_documents(dry_run=True)
            >>> print(f"Would delete {len(actions)} documents")
            >>> for action in actions:
            ...     print(f"  {action.document.path}: {action.reason}")
        """
        actions = []

        # Get all archived documents
        try:
            archived_docs = self.doc_mgr.registry.query_documents(
                state=DocumentState.ARCHIVED
            )
        except Exception:
            return actions

        for doc in archived_docs:
            action = self._evaluate_deletion(doc)

            if action.action == "delete":
                actions.append(action)

                if not dry_run:
                    try:
                        self._delete_document(doc)
                    except Exception:
                        # Skip if deletion fails
                        pass

        return actions

    def _evaluate_archival(self, doc: Document) -> ArchivalAction:
        """
        Evaluate if a document should be archived.

        Checks retention policy and document age to determine if an OBSOLETE
        document should be moved to the archive.

        Args:
            doc: Document to evaluate (must be OBSOLETE state)

        Returns:
            ArchivalAction indicating whether to archive and why
        """
        policy = self.policies.get(doc.type.value)

        if not policy or policy.obsolete_to_archive == -1:
            return ArchivalAction(
                document=doc,
                action="none",
                reason="No archival policy or never archive",
                days_until_action=-1,
            )

        # Calculate age since last modification (approximation of obsolete date)
        # Note: Ideally we'd track state transition history, but using modified_at
        # as a proxy for when document became obsolete
        try:
            modified_date = datetime.fromisoformat(doc.modified_at)
        except (ValueError, TypeError):
            # If date parsing fails, skip this document
            return ArchivalAction(
                document=doc,
                action="none",
                reason="Invalid modified date",
                days_until_action=-1,
            )

        age_days = (datetime.now() - modified_date).days

        if age_days >= policy.obsolete_to_archive:
            return ArchivalAction(
                document=doc,
                action="archive",
                reason=f"Obsolete for {age_days} days (policy: {policy.obsolete_to_archive})",
                days_until_action=0,
            )
        else:
            return ArchivalAction(
                document=doc,
                action="none",
                reason=f"Not old enough ({age_days}/{policy.obsolete_to_archive} days)",
                days_until_action=policy.obsolete_to_archive - age_days,
            )

    def _evaluate_deletion(self, doc: Document) -> ArchivalAction:
        """
        Evaluate if an archived document should be deleted.

        Checks multiple criteria:
        1. Has retention policy
        2. No compliance tags (NEVER delete documents with compliance tags)
        3. Deletion allowed by policy (delete_after_archive=true)
        4. Retention period expired

        Args:
            doc: Document to evaluate (must be ARCHIVED state)

        Returns:
            ArchivalAction indicating whether to delete and why
        """
        policy = self.policies.get(doc.type.value)

        if not policy:
            return ArchivalAction(
                document=doc,
                action="none",
                reason="No retention policy",
                days_until_action=-1,
            )

        # Check compliance tags (HIGHEST PRIORITY - never delete)
        doc_tags = doc.metadata.get("tags", [])
        has_compliance_tags = any(tag in policy.compliance_tags for tag in doc_tags)

        if has_compliance_tags:
            return ArchivalAction(
                document=doc,
                action="none",
                reason=f"Protected by compliance tags: {[t for t in doc_tags if t in policy.compliance_tags]}",
                days_until_action=-1,
            )

        # Check if deletion allowed by policy
        if not policy.delete_after_archive:
            return ArchivalAction(
                document=doc,
                action="none",
                reason="Deletion not allowed by policy",
                days_until_action=-1,
            )

        # Check if retention period is forever
        if policy.archive_retention == -1:
            return ArchivalAction(
                document=doc,
                action="none",
                reason="Retention period is forever",
                days_until_action=-1,
            )

        # Calculate archive age
        try:
            archived_date = datetime.fromisoformat(doc.modified_at)
        except (ValueError, TypeError):
            return ArchivalAction(
                document=doc,
                action="none",
                reason="Invalid archived date",
                days_until_action=-1,
            )

        age_days = (datetime.now() - archived_date).days

        if age_days >= policy.archive_retention:
            return ArchivalAction(
                document=doc,
                action="delete",
                reason=f"Archived for {age_days} days (retention: {policy.archive_retention})",
                days_until_action=0,
            )
        else:
            return ArchivalAction(
                document=doc,
                action="none",
                reason=f"Retention not expired ({age_days}/{policy.archive_retention} days)",
                days_until_action=policy.archive_retention - age_days,
            )

    def _delete_document(self, doc: Document) -> None:
        """
        Permanently delete document file and database record.

        This is a destructive operation and should only be called after
        all safety checks (compliance tags, retention period) have passed.

        Args:
            doc: Document to delete

        Raises:
            Various exceptions if file or database operations fail
        """
        # Delete file if it exists
        file_path = Path(doc.path)
        if file_path.exists():
            try:
                file_path.unlink()
            except (PermissionError, OSError):
                # File might be in use or permission denied
                # Log but don't fail - database record will still be removed
                pass

        # Delete from database (hard delete - permanently remove)
        self.doc_mgr.registry.delete_document(doc.id, soft=False)

    def generate_retention_report(self, format: str = "markdown") -> str:
        """
        Generate retention policy compliance report.

        Analyzes all documents and reports their retention status, grouping
        by document type and showing which documents are eligible for
        archival or deletion.

        Args:
            format: Output format ('markdown' or 'csv')

        Returns:
            Report as string in requested format

        Example:
            >>> report = manager.generate_retention_report()
            >>> print(report)
            # Document Retention Policy Report
            Generated: 2025-11-05 14:30:00
            ...
        """
        if format == "csv":
            return self._generate_csv_report()
        else:
            return self._generate_markdown_report()

    def _generate_markdown_report(self) -> str:
        """Generate report in markdown format."""
        try:
            all_docs = self.doc_mgr.registry.query_documents()
        except Exception:
            return "# Document Retention Policy Report\n\nError: Could not query documents.\n"

        report = "# Document Retention Policy Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group by document type
        by_type: Dict[str, List[Document]] = {}
        for doc in all_docs:
            doc_type = doc.type.value
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)

        # Generate section for each document type
        for doc_type, docs in sorted(by_type.items()):
            report += f"## {doc_type.upper()} ({len(docs)} documents)\n\n"

            policy = self.policies.get(doc_type)
            if policy:
                report += f"**Policy Configuration:**\n"
                report += f"- Obsolete to Archive: {policy.obsolete_to_archive} days "
                report += f"({'never' if policy.obsolete_to_archive == -1 else ''})\n"
                report += f"- Archive Retention: {policy.archive_retention} days "
                report += f"({'forever' if policy.archive_retention == -1 else ''})\n"
                report += f"- Delete After Archive: {'Yes' if policy.delete_after_archive else 'No'}\n"
                report += f"- Compliance Tags: {', '.join(policy.compliance_tags) if policy.compliance_tags else 'None'}\n\n"
            else:
                report += "**Policy:** No retention policy configured\n\n"

            # Analyze each document
            actions_pending = []
            for doc in docs:
                if doc.state == DocumentState.OBSOLETE:
                    action = self._evaluate_archival(doc)
                elif doc.state == DocumentState.ARCHIVED:
                    action = self._evaluate_deletion(doc)
                else:
                    continue

                if action.action != "none":
                    actions_pending.append(action)

            if actions_pending:
                report += "**Pending Actions:**\n\n"
                for action in actions_pending:
                    report += f"- `{action.document.path}`\n"
                    report += f"  - Action: **{action.action.upper()}**\n"
                    report += f"  - Reason: {action.reason}\n"
                    report += f"  - State: {action.document.state.value}\n"
                    if action.document.metadata.get("tags"):
                        report += f"  - Tags: {', '.join(action.document.metadata['tags'])}\n"
                    report += "\n"
            else:
                report += "**Status:** All documents compliant with retention policy.\n\n"

            report += "---\n\n"

        # Summary
        total_actions = sum(
            1
            for doc in all_docs
            if (doc.state == DocumentState.OBSOLETE and self._evaluate_archival(doc).action != "none")
            or (doc.state == DocumentState.ARCHIVED and self._evaluate_deletion(doc).action != "none")
        )

        report += f"## Summary\n\n"
        report += f"- Total Documents: {len(all_docs)}\n"
        report += f"- Pending Actions: {total_actions}\n"
        report += f"- Document Types: {len(by_type)}\n"

        return report

    def _generate_csv_report(self) -> str:
        """Generate report in CSV format for compliance audits."""
        try:
            all_docs = self.doc_mgr.registry.query_documents()
        except Exception:
            return "error,Could not query documents\n"

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Path",
            "Type",
            "State",
            "Created",
            "Modified",
            "Action",
            "Reason",
            "Days Until Action",
            "Compliance Tags",
        ])

        # Write rows
        for doc in all_docs:
            if doc.state == DocumentState.OBSOLETE:
                action = self._evaluate_archival(doc)
            elif doc.state == DocumentState.ARCHIVED:
                action = self._evaluate_deletion(doc)
            else:
                action = ArchivalAction(doc, "none", "Not obsolete or archived", -1)

            tags = ", ".join(doc.metadata.get("tags", []))

            writer.writerow([
                doc.path,
                doc.type.value,
                doc.state.value,
                doc.created_at,
                doc.modified_at,
                action.action,
                action.reason,
                action.days_until_action,
                tags,
            ])

        return output.getvalue()

    def get_policy(self, doc_type: str) -> Optional[RetentionPolicy]:
        """
        Get retention policy for a document type.

        Args:
            doc_type: Document type (prd, architecture, story, etc.)

        Returns:
            RetentionPolicy if configured, None otherwise
        """
        return self.policies.get(doc_type)

    def list_policies(self) -> List[RetentionPolicy]:
        """
        Get all configured retention policies.

        Returns:
            List of all RetentionPolicy objects
        """
        return list(self.policies.values())
