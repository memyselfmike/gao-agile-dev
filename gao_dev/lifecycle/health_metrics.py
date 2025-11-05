"""
Document Health Metrics Module.

This module provides document health KPI tracking and reporting functionality.
Implements the 5S Sustain principle - measure and maintain quality over time.

The DocumentHealthMetrics class collects comprehensive metrics about document
quality, compliance, and lifecycle state, and generates actionable health reports.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.governance import DocumentGovernance
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.models import DocumentState, Document


class DocumentHealthMetrics:
    """
    Track document health KPIs.

    Implements 5S Sustain principle - measure and maintain quality.
    Collects comprehensive metrics and generates actionable health reports.

    Attributes:
        registry: Document registry for querying documents
        governance: Governance manager for review tracking
        naming: Naming convention validator
        metrics_db_path: Optional path to metrics database
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        governance: DocumentGovernance,
        naming_convention: DocumentNamingConvention,
        metrics_db_path: Optional[Path] = None,
    ):
        """
        Initialize health metrics.

        Args:
            registry: Document registry
            governance: Governance manager
            naming_convention: Naming convention validator
            metrics_db_path: Optional path to metrics database
        """
        self.registry = registry
        self.governance = governance
        self.naming = naming_convention
        self.metrics_db_path = metrics_db_path

    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect all document health metrics.

        Returns:
            Dictionary of metrics including:
                - total_documents: Total number of documents
                - documents_by_state: Count by state (draft, active, etc.)
                - documents_by_type: Count by type (prd, architecture, etc.)
                - stale_documents: Documents not updated within review cadence
                - documents_needing_review: Documents past review due date
                - orphaned_documents: Documents with no relationships
                - documents_without_owners: Documents missing owner field
                - avg_document_age_days: Average age in days
                - oldest_document_days: Age of oldest document
                - newest_document_days: Age of newest document
                - naming_compliance_rate: Percentage following naming convention
                - frontmatter_compliance_rate: Percentage with complete frontmatter
                - cache_hit_rate: Cache hit rate (placeholder)
                - avg_query_time_ms: Average query time (placeholder)
                - context_injection_rate: Context injection rate (Epic 13 placeholder)
        """
        all_docs = self.registry.query_documents()

        return {
            # Overall counts
            "total_documents": len(all_docs),
            "documents_by_state": self._count_by_state(all_docs),
            "documents_by_type": self._count_by_type(all_docs),
            # Health indicators
            "stale_documents": self._count_stale_documents(),
            "documents_needing_review": len(
                self.governance.check_review_due(include_overdue_only=True)
            ),
            "orphaned_documents": self._count_orphaned(),
            "documents_without_owners": self._count_without_owners(all_docs),
            # Age metrics
            "avg_document_age_days": self._calculate_avg_age(all_docs),
            "oldest_document_days": self._get_oldest_document_age(all_docs),
            "newest_document_days": self._get_newest_document_age(all_docs),
            # Compliance metrics
            "naming_compliance_rate": self._calculate_naming_compliance(all_docs),
            "frontmatter_compliance_rate": self._calculate_frontmatter_compliance(
                all_docs
            ),
            # Performance metrics (placeholders)
            "cache_hit_rate": self._get_cache_hit_rate(),
            "avg_query_time_ms": self._get_avg_query_time(),
            # Context injection rate (requires Epic 13)
            "context_injection_rate": 0.0,  # Placeholder
        }

    def _count_by_state(self, documents: List[Document]) -> Dict[str, int]:
        """
        Count documents by state.

        Args:
            documents: List of documents to count

        Returns:
            Dictionary mapping state to count
        """
        states = Counter(doc.state.value for doc in documents)
        return dict(states)

    def _count_by_type(self, documents: List[Document]) -> Dict[str, int]:
        """
        Count documents by type.

        Args:
            documents: List of documents to count

        Returns:
            Dictionary mapping type to count
        """
        types = Counter(doc.type.value for doc in documents)
        return dict(types)

    def _count_stale_documents(self) -> int:
        """
        Count stale documents (not updated in >review_cadence days).

        A document is stale if:
        - It's ACTIVE
        - Last modified > review_cadence days ago

        Returns:
            Count of stale documents
        """
        active_docs = self.registry.query_documents(state=DocumentState.ACTIVE)
        stale_count = 0

        for doc in active_docs:
            # Get review cadence for doc type
            cadence = self.governance.config["document_governance"][
                "review_cadence"
            ].get(doc.type.value, 90)

            if cadence == -1:
                continue  # Never stale

            # Calculate age since last modification
            modified_date = datetime.fromisoformat(doc.modified_at)
            age_days = (datetime.now() - modified_date).days

            if age_days > cadence:
                stale_count += 1

        return stale_count

    def _count_orphaned(self) -> int:
        """
        Count orphaned documents (no relationships to other documents).

        Excludes temp/draft documents as they are expected to be orphaned.

        Returns:
            Count of orphaned documents
        """
        all_docs = self.registry.query_documents()
        orphaned = 0

        for doc in all_docs:
            # Skip temp/draft
            classification = doc.metadata.get("5s_classification", "permanent")
            if classification == "temp" or doc.state == DocumentState.DRAFT:
                continue

            # Check for relationships
            parents = self.registry.get_parent_documents(doc.id)
            children = self.registry.get_child_documents(doc.id)

            if not parents and not children:
                orphaned += 1

        return orphaned

    def _count_without_owners(self, documents: List[Document]) -> int:
        """
        Count documents without owners.

        Args:
            documents: List of documents to check

        Returns:
            Count of documents without owners
        """
        return sum(1 for doc in documents if not doc.metadata.get("owner"))

    def _calculate_avg_age(self, documents: List[Document]) -> float:
        """
        Calculate average document age in days.

        Args:
            documents: List of documents

        Returns:
            Average age in days (0.0 if no documents)
        """
        if not documents:
            return 0.0

        total_age = 0
        now = datetime.now()

        for doc in documents:
            created = datetime.fromisoformat(doc.created_at)
            age = (now - created).days
            total_age += age

        return total_age / len(documents)

    def _get_oldest_document_age(self, documents: List[Document]) -> int:
        """
        Get age of oldest document in days.

        Args:
            documents: List of documents

        Returns:
            Age of oldest document in days (0 if no documents)
        """
        if not documents:
            return 0

        oldest = min(documents, key=lambda d: d.created_at)
        created = datetime.fromisoformat(oldest.created_at)
        return (datetime.now() - created).days

    def _get_newest_document_age(self, documents: List[Document]) -> int:
        """
        Get age of newest document in days.

        Args:
            documents: List of documents

        Returns:
            Age of newest document in days (0 if no documents)
        """
        if not documents:
            return 0

        newest = max(documents, key=lambda d: d.created_at)
        created = datetime.fromisoformat(newest.created_at)
        return (datetime.now() - created).days

    def _calculate_naming_compliance(self, documents: List[Document]) -> float:
        """
        Calculate percentage of documents following naming convention.

        Args:
            documents: List of documents to check

        Returns:
            Percentage (0-100) of compliant documents
        """
        if not documents:
            return 100.0

        compliant = 0

        for doc in documents:
            filename = Path(doc.path).name
            is_valid, _ = self.naming.validate_filename(filename)

            if is_valid:
                compliant += 1

        return (compliant / len(documents)) * 100

    def _calculate_frontmatter_compliance(self, documents: List[Document]) -> float:
        """
        Calculate percentage of documents with complete frontmatter.

        Args:
            documents: List of documents to check

        Returns:
            Percentage (0-100) of documents with all required fields
        """
        if not documents:
            return 100.0

        required_fields = ["title", "doc_type", "status", "owner"]
        compliant = 0

        for doc in documents:
            metadata = doc.metadata
            has_all_fields = all(field in metadata for field in required_fields)

            if has_all_fields:
                compliant += 1

        return (compliant / len(documents)) * 100

    def _get_cache_hit_rate(self) -> float:
        """
        Get cache hit rate (placeholder - requires cache metrics).

        Returns:
            Cache hit rate (0.0 placeholder)
        """
        # Would integrate with ContextCache from Epic 15
        return 0.0

    def _get_avg_query_time(self) -> float:
        """
        Get average query time in ms (placeholder - requires metrics).

        Returns:
            Average query time in ms (0.0 placeholder)
        """
        # Would integrate with metrics database
        return 0.0

    def generate_health_report(self) -> str:
        """
        Generate markdown health report.

        Produces a comprehensive health report with:
        - Summary metrics table
        - Documents by state breakdown
        - Documents by type breakdown
        - Action items (what needs attention)

        Returns:
            Markdown formatted health report
        """
        metrics = self.collect_metrics()

        # Build report header
        report = f"""# Document Lifecycle Health Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| **Total Documents** | {metrics['total_documents']} |
| **Stale Documents** | {metrics['stale_documents']} ({metrics['stale_documents']/max(metrics['total_documents'],1)*100:.1f}%) |
| **Needs Review** | {metrics['documents_needing_review']} |
| **Orphaned Documents** | {metrics['orphaned_documents']} |
| **Without Owners** | {metrics['documents_without_owners']} |
| **Avg Document Age** | {metrics['avg_document_age_days']:.1f} days |
| **Naming Compliance** | {metrics['naming_compliance_rate']:.1f}% |
| **Frontmatter Compliance** | {metrics['frontmatter_compliance_rate']:.1f}% |

---

## Documents by State

| State | Count |
|-------|-------|
"""

        # Add state breakdown
        for state, count in metrics["documents_by_state"].items():
            report += f"| {state} | {count} |\n"

        # Add type breakdown
        report += "\n---\n\n## Documents by Type\n\n| Type | Count |\n|------|-------|\n"

        for doc_type, count in metrics["documents_by_type"].items():
            report += f"| {doc_type} | {count} |\n"

        # Generate action items
        report += "\n---\n\n## Action Items\n\n"
        action_items = self._generate_action_items(metrics)

        if action_items:
            report += "\n".join(action_items) + "\n"
        else:
            report += "✓ No action items - system is healthy!\n"

        # Add footer
        report += "\n---\n\n*Report generated by Document Health Metrics*\n"

        return report

    def _generate_action_items(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate list of action items from metrics.

        Args:
            metrics: Collected metrics dictionary

        Returns:
            List of action item strings
        """
        action_items = []

        if metrics["stale_documents"] > 0:
            action_items.append(
                f"- [ ] **Review {metrics['stale_documents']} stale documents** "
                f"(not updated within review cadence)"
            )

        if metrics["documents_needing_review"] > 0:
            action_items.append(
                f"- [ ] **Review {metrics['documents_needing_review']} documents past due date**"
            )

        if metrics["orphaned_documents"] > 0:
            action_items.append(
                f"- [ ] **Verify {metrics['orphaned_documents']} orphaned documents** "
                f"(no relationships)"
            )

        if metrics["documents_without_owners"] > 0:
            action_items.append(
                f"- [ ] **Assign owners to {metrics['documents_without_owners']} documents**"
            )

        if metrics["naming_compliance_rate"] < 100:
            non_compliant = int(
                metrics["total_documents"]
                * (100 - metrics["naming_compliance_rate"])
                / 100
            )
            action_items.append(
                f"- [ ] **Rename {non_compliant} non-compliant documents** "
                f"to follow naming convention"
            )

        if metrics["frontmatter_compliance_rate"] < 100:
            incomplete = int(
                metrics["total_documents"]
                * (100 - metrics["frontmatter_compliance_rate"])
                / 100
            )
            action_items.append(
                f"- [ ] **Complete frontmatter for {incomplete} documents** "
                f"(missing required fields)"
            )

        return action_items

    def get_action_items_only(self) -> List[Dict[str, Any]]:
        """
        Get structured action items for programmatic use.

        Returns:
            List of action item dictionaries with:
                - type: Action type (review, assign, rename, etc.)
                - count: Number of items
                - severity: Severity level (high, medium, low)
                - description: Human-readable description
                - resolution_steps: List of steps to resolve
        """
        metrics = self.collect_metrics()
        action_items = []

        if metrics["stale_documents"] > 0:
            action_items.append(
                {
                    "type": "stale_documents",
                    "count": metrics["stale_documents"],
                    "severity": "medium",
                    "description": "Documents not updated within review cadence",
                    "resolution_steps": [
                        "Identify stale documents using governance system",
                        "Review and update documents",
                        "Mark as reviewed or mark as obsolete if no longer needed",
                    ],
                }
            )

        if metrics["documents_needing_review"] > 0:
            action_items.append(
                {
                    "type": "overdue_reviews",
                    "count": metrics["documents_needing_review"],
                    "severity": "high",
                    "description": "Documents past their review due date",
                    "resolution_steps": [
                        "Run 'gao-dev lifecycle review-due --overdue-only'",
                        "Review each document",
                        "Mark as reviewed using 'gao-dev lifecycle mark-reviewed <id>'",
                    ],
                }
            )

        if metrics["orphaned_documents"] > 0:
            action_items.append(
                {
                    "type": "orphaned_documents",
                    "count": metrics["orphaned_documents"],
                    "severity": "low",
                    "description": "Documents with no relationships to other documents",
                    "resolution_steps": [
                        "Identify orphaned documents",
                        "Add relationships to parent/child documents",
                        "Or mark as obsolete if no longer relevant",
                    ],
                }
            )

        if metrics["documents_without_owners"] > 0:
            action_items.append(
                {
                    "type": "missing_owners",
                    "count": metrics["documents_without_owners"],
                    "severity": "medium",
                    "description": "Documents without assigned owners",
                    "resolution_steps": [
                        "Review governance configuration",
                        "Assign owners based on RACI matrix",
                        "Update document frontmatter",
                    ],
                }
            )

        if metrics["naming_compliance_rate"] < 100:
            non_compliant = int(
                metrics["total_documents"]
                * (100 - metrics["naming_compliance_rate"])
                / 100
            )
            action_items.append(
                {
                    "type": "naming_non_compliance",
                    "count": non_compliant,
                    "severity": "low",
                    "description": "Documents not following naming convention",
                    "resolution_steps": [
                        "Identify non-compliant filenames",
                        "Rename to follow convention: <type>-<subject>-<version>.md",
                        "Update references in other documents",
                    ],
                }
            )

        if metrics["frontmatter_compliance_rate"] < 100:
            incomplete = int(
                metrics["total_documents"]
                * (100 - metrics["frontmatter_compliance_rate"])
                / 100
            )
            action_items.append(
                {
                    "type": "frontmatter_incomplete",
                    "count": incomplete,
                    "severity": "medium",
                    "description": "Documents missing required frontmatter fields",
                    "resolution_steps": [
                        "Identify documents with incomplete frontmatter",
                        "Add missing fields: title, doc_type, status, owner",
                        "Validate using naming convention tools",
                    ],
                }
            )

        return action_items
