# Story 12.10 (NEW): Document Health KPIs

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 3
**Priority:** P2
**Status:** Pending
**Owner:** TBD
**Sprint:** 3

---

## Story Description

Implement KPI tracking and health monitoring for document lifecycle system. Measures effectiveness of the system, identifies stale/orphaned documents, and enables continuous improvement (5S: Sustain - measure and maintain quality).

---

## Business Value

Health KPIs provide:
- **Visibility**: Dashboard showing system health at a glance
- **Action Items**: Identifies problems (stale docs, missing owners, non-compliance)
- **Continuous Improvement**: Data-driven decisions to improve document management
- **Compliance**: Audit-ready reports for governance reviews
- **5S Sustain**: Metrics ensure standards are maintained over time

---

## Acceptance Criteria

### KPI Collection
- [ ] `DocumentHealthMetrics` class for metrics collection
- [ ] `collect_metrics()` returns comprehensive metrics dict
- [ ] KPIs tracked:
  - Total documents (by state, by type)
  - Stale documents (not updated in >review_cadence days)
  - Documents needing review (review_due_date in past)
  - Orphaned documents (no relationships to other docs)
  - Average document age (days)
  - Most/least accessed documents
  - Cache hit rate
  - Average query time
  - Context injection rate (from Epic 13)
  - Naming compliance rate
  - Frontmatter compliance rate

### Health Report Generation
- [ ] `generate_health_report()` produces markdown health report
- [ ] Report sections:
  - Summary metrics table
  - Documents by state breakdown
  - Documents by type breakdown
  - Action items (what needs attention)
  - Trends (if historical data available)
- [ ] Report includes charts/visualizations (ASCII or mermaid)

### CLI Commands
- [ ] `gao-dev lifecycle health` - Display health dashboard
- [ ] `gao-dev lifecycle health --json` - JSON output for automation
- [ ] `gao-dev lifecycle health --export report.md` - Save to file
- [ ] `gao-dev lifecycle health --action-items-only` - Just show what needs fixing

### Action Items Identification
- [ ] Documents needing review (overdue)
- [ ] Stale documents (not updated in >review_cadence)
- [ ] Orphaned documents (no relationships)
- [ ] Documents without owners
- [ ] Documents with non-standard naming
- [ ] Documents missing frontmatter fields
- [ ] Each action item includes: count, severity, resolution steps

### Metrics Storage
- [ ] Metrics stored in existing metrics database (reuse sandbox metrics DB)
- [ ] Historical tracking (daily/weekly snapshots)
- [ ] Trend analysis (improvement over time)
- [ ] Integration with existing logging/observability

**Test Coverage:** >80%

---

## Technical Notes

### Implementation

```python
# gao_dev/lifecycle/health_metrics.py
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.governance import DocumentGovernance
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention
from gao_dev.lifecycle.models import DocumentState

class DocumentHealthMetrics:
    """
    Track document health KPIs.

    Implements 5S Sustain principle - measure and maintain quality.
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        governance: DocumentGovernance,
        naming_convention: DocumentNamingConvention,
        metrics_db_path: Optional[Path] = None
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
            Dictionary of metrics
        """
        all_docs = self.registry.query_documents()

        return {
            # Overall counts
            "total_documents": len(all_docs),
            "documents_by_state": self.count_by_state(all_docs),
            "documents_by_type": self.count_by_type(all_docs),

            # Health indicators
            "stale_documents": self.count_stale_documents(),
            "documents_needing_review": len(self.governance.check_review_due(include_overdue_only=True)),
            "orphaned_documents": self.count_orphaned(),
            "documents_without_owners": self.count_without_owners(all_docs),

            # Age metrics
            "avg_document_age_days": self.calculate_avg_age(all_docs),
            "oldest_document_days": self.get_oldest_document_age(all_docs),
            "newest_document_days": self.get_newest_document_age(all_docs),

            # Compliance metrics
            "naming_compliance_rate": self.calculate_naming_compliance(all_docs),
            "frontmatter_compliance_rate": self.calculate_frontmatter_compliance(all_docs),

            # Performance metrics (if available)
            "cache_hit_rate": self.get_cache_hit_rate(),
            "avg_query_time_ms": self.get_avg_query_time(),

            # Context injection rate (requires Epic 13)
            "context_injection_rate": 0.0,  # Placeholder
        }

    def count_by_state(self, documents: List) -> Dict[str, int]:
        """Count documents by state."""
        states = Counter(doc.state.value for doc in documents)
        return dict(states)

    def count_by_type(self, documents: List) -> Dict[str, int]:
        """Count documents by type."""
        types = Counter(doc.doc_type.value for doc in documents)
        return dict(types)

    def count_stale_documents(self) -> int:
        """
        Count stale documents (not updated in >review_cadence days).

        A document is stale if:
        - It's ACTIVE
        - Last modified > review_cadence days ago
        """
        sql = """
            SELECT COUNT(*) FROM documents d
            WHERE d.state = 'active'
              AND julianday('now') - julianday(d.modified_at) >
                  COALESCE(
                      (SELECT review_cadence FROM governance WHERE doc_type = d.type),
                      90
                  )
        """

        # Simplified version
        active_docs = self.registry.query_documents(state=DocumentState.ACTIVE)
        stale_count = 0

        for doc in active_docs:
            # Get review cadence for doc type
            cadence = self.governance.config['document_governance']['review_cadence'].get(
                doc.doc_type.value, 90
            )

            if cadence == -1:
                continue  # Never stale

            # Calculate age
            modified_date = datetime.fromisoformat(doc.modified_at)
            age_days = (datetime.now() - modified_date).days

            if age_days > cadence:
                stale_count += 1

        return stale_count

    def count_orphaned(self) -> int:
        """
        Count orphaned documents (no relationships to other documents).

        Excludes temp/draft documents.
        """
        all_docs = self.registry.query_documents()
        orphaned = 0

        for doc in all_docs:
            # Skip temp/draft
            classification = doc.metadata.get('5s_classification', 'permanent')
            if classification == 'temp' or doc.state == DocumentState.DRAFT:
                continue

            # Check for relationships
            parents = self.registry.get_parent_documents(doc.id)
            children = self.registry.get_child_documents(doc.id)

            if not parents and not children:
                orphaned += 1

        return orphaned

    def count_without_owners(self, documents: List) -> int:
        """Count documents without owners."""
        return sum(1 for doc in documents if not doc.metadata.get('owner'))

    def calculate_avg_age(self, documents: List) -> float:
        """Calculate average document age in days."""
        if not documents:
            return 0.0

        total_age = 0
        now = datetime.now()

        for doc in documents:
            created = datetime.fromisoformat(doc.created_at)
            age = (now - created).days
            total_age += age

        return total_age / len(documents)

    def get_oldest_document_age(self, documents: List) -> int:
        """Get age of oldest document in days."""
        if not documents:
            return 0

        oldest = min(documents, key=lambda d: d.created_at)
        created = datetime.fromisoformat(oldest.created_at)
        return (datetime.now() - created).days

    def get_newest_document_age(self, documents: List) -> int:
        """Get age of newest document in days."""
        if not documents:
            return 0

        newest = max(documents, key=lambda d: d.created_at)
        created = datetime.fromisoformat(newest.created_at)
        return (datetime.now() - created).days

    def calculate_naming_compliance(self, documents: List) -> float:
        """Calculate percentage of documents following naming convention."""
        if not documents:
            return 100.0

        compliant = 0

        for doc in documents:
            filename = Path(doc.path).name
            is_valid, _ = self.naming.validate_filename(filename)

            if is_valid:
                compliant += 1

        return (compliant / len(documents)) * 100

    def calculate_frontmatter_compliance(self, documents: List) -> float:
        """Calculate percentage of documents with complete frontmatter."""
        if not documents:
            return 100.0

        required_fields = ['title', 'doc_type', 'status', 'owner']
        compliant = 0

        for doc in documents:
            metadata = doc.metadata
            has_all_fields = all(field in metadata for field in required_fields)

            if has_all_fields:
                compliant += 1

        return (compliant / len(documents)) * 100

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate (placeholder - requires cache metrics)."""
        # Would integrate with ContextCache from Epic 15
        return 0.0

    def get_avg_query_time(self) -> float:
        """Get average query time in ms (placeholder - requires metrics)."""
        # Would integrate with metrics database
        return 0.0

    def generate_health_report(self) -> str:
        """
        Generate markdown health report.

        Returns:
            Markdown formatted report
        """
        metrics = self.collect_metrics()

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

        for state, count in metrics['documents_by_state'].items():
            report += f"| {state} | {count} |\n"

        report += "\n---\n\n## Documents by Type\n\n| Type | Count |\n|------|-------|\n"

        for doc_type, count in metrics['documents_by_type'].items():
            report += f"| {doc_type} | {count} |\n"

        report += "\n---\n\n## Action Items\n\n"

        # Generate action items
        action_items = []

        if metrics['stale_documents'] > 0:
            action_items.append(
                f"- [ ] **Review {metrics['stale_documents']} stale documents** (not updated within review cadence)"
            )

        if metrics['documents_needing_review'] > 0:
            action_items.append(
                f"- [ ] **Review {metrics['documents_needing_review']} documents past due date**"
            )

        if metrics['orphaned_documents'] > 0:
            action_items.append(
                f"- [ ] **Verify {metrics['orphaned_documents']} orphaned documents** (no relationships)"
            )

        if metrics['documents_without_owners'] > 0:
            action_items.append(
                f"- [ ] **Assign owners to {metrics['documents_without_owners']} documents**"
            )

        if metrics['naming_compliance_rate'] < 100:
            non_compliant = int(metrics['total_documents'] * (100 - metrics['naming_compliance_rate']) / 100)
            action_items.append(
                f"- [ ] **Rename {non_compliant} non-compliant documents** to follow naming convention"
            )

        if metrics['frontmatter_compliance_rate'] < 100:
            incomplete = int(metrics['total_documents'] * (100 - metrics['frontmatter_compliance_rate']) / 100)
            action_items.append(
                f"- [ ] **Complete frontmatter for {incomplete} documents** (missing required fields)"
            )

        if action_items:
            report += "\n".join(action_items) + "\n"
        else:
            report += "✓ No action items - system is healthy!\n"

        report += "\n---\n\n*Report generated by Document Health Metrics*\n"

        return report
```

**Files to Create:**
- `gao_dev/lifecycle/health_metrics.py`
- `gao_dev/cli/lifecycle_commands.py` (enhanced with health command)
- `tests/lifecycle/test_health_metrics.py`

**Dependencies:**
- Story 12.2 (DocumentRegistry)
- Story 12.7 (DocumentGovernance)
- Story 12.1 (DocumentNamingConvention)

---

## Testing Requirements

### Unit Tests
- [ ] Test collect_metrics() returns all KPIs
- [ ] Test count_stale_documents() logic
- [ ] Test count_orphaned() excludes temp/draft
- [ ] Test naming compliance calculation
- [ ] Test frontmatter compliance calculation
- [ ] Test generate_health_report() format

### Integration Tests
- [ ] Create documents, verify metrics accurate
- [ ] Simulate stale documents, verify detection
- [ ] Generate real health report

### Performance Tests
- [ ] Collect metrics for 1000 documents in <1 second

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] KPI definitions and calculations
- [ ] Health report interpretation guide
- [ ] Action item resolution steps
- [ ] CLI command examples
- [ ] Integration with monitoring systems

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance targets met
- [ ] Health reports validated
- [ ] CLI commands working
- [ ] Committed with atomic commit message
