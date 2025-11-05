# Story 12.7 (NEW): Document Governance Framework

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 3
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** 2

---

## Story Description

Implement document governance framework with ownership tracking, review cycles, and RACI matrix for document management. Prevents document rot by ensuring all documents have clear ownership and regular review cadences (5S: Sustain - maintain standards over time).

---

## Business Value

The governance framework provides:
- **Accountability**: Every document has a clear owner (RACI: Accountable)
- **Quality**: Regular reviews prevent stale/outdated documents
- **Compliance**: Audit trail of review cycles for regulatory requirements
- **Automation**: Auto-assignment of review due dates based on document type
- **Visibility**: Easily identify documents needing review

---

## Acceptance Criteria

### Governance Configuration
- [ ] YAML configuration file: `gao_dev/config/governance.yaml`
- [ ] RACI matrix defined per document type:
  - Responsible: Who creates the document
  - Accountable: Who owns the document
  - Consulted: Who reviews the document
  - Informed: Who is notified of changes
- [ ] Review cadence configured per document type (in days):
  - PRD: 90 days
  - Architecture: 60 days
  - Story: 30 days
  - ADR: Never (immutable once approved)
  - Postmortem: 365 days (annual review)

### Ownership Management
- [ ] `assign_owner(doc_id, owner)` assigns document owner
- [ ] `assign_reviewer(doc_id, reviewer)` assigns reviewer
- [ ] `get_owned_documents(owner)` returns documents owned by person
- [ ] `get_review_queue(reviewer)` returns documents needing review
- [ ] Auto-assignment of owner/reviewer on document creation based on RACI

### Review Cycle Tracking
- [ ] `check_review_due()` identifies documents needing review
- [ ] Review due date calculated automatically:
  - On document creation: created_date + review_cadence
  - On review: review_date + review_cadence
- [ ] `mark_reviewed(doc_id, reviewer, notes)` records review
- [ ] Review history tracked in `document_reviews` table

### Governance Rules
- [ ] Who can create each document type (RACI: Responsible)
- [ ] Who must approve (RACI: Accountable)
- [ ] Who can archive/delete (RACI: Accountable only)
- [ ] Documents without owner flagged in health KPIs

### CLI Commands
- [ ] `gao-dev lifecycle review-due` - Show documents needing review
- [ ] `gao-dev lifecycle review-due --owner John` - Filter by owner
- [ ] `gao-dev lifecycle mark-reviewed <doc-id>` - Mark as reviewed
- [ ] `gao-dev lifecycle governance-report` - Full governance report

### Review Reminders
- [ ] Generate list of overdue reviews
- [ ] Format: Document, Owner, Due Date, Days Overdue
- [ ] Sort by priority (P0 documents first, then by days overdue)
- [ ] Export to CSV for email notifications (integration point)

**Test Coverage:** >80%

---

## Technical Notes

### Governance Configuration

```yaml
# gao_dev/config/governance.yaml
document_governance:
  ownership:
    prd:
      created_by: "John"      # Product Manager
      approved_by: "Mary"     # Engineering Manager
      reviewed_by: "Winston"  # Technical Architect
      informed: ["Team"]

    architecture:
      created_by: "Winston"   # Technical Architect
      approved_by: "Mary"     # Engineering Manager
      reviewed_by: "John"     # Product Manager (business alignment)
      informed: ["Team"]

    story:
      created_by: "Bob"       # Scrum Master
      approved_by: "John"     # Product Manager
      reviewed_by: "Amelia"   # Developer (technical review)
      informed: ["Team"]

    adr:
      created_by: "Winston"   # Technical Architect
      approved_by: "Mary"     # Engineering Manager
      reviewed_by: "Amelia"   # Developer
      informed: ["Team", "Stakeholders"]

    postmortem:
      created_by: "Incident Owner"
      approved_by: "Mary"     # Engineering Manager
      reviewed_by: "Team"
      informed: ["Leadership", "Stakeholders"]

  review_cadence:  # Days between reviews
    prd: 90
    architecture: 60
    story: 30
    epic: 60
    adr: -1  # Never (immutable)
    postmortem: 365  # Annual review
    qa_report: -1  # Never (point-in-time snapshot)
    test_report: -1

  permissions:
    archive:
      allowed_roles: ["owner", "engineering_manager"]
    delete:
      allowed_roles: ["owner", "engineering_manager"]  # With confirmation
    transition_to_active:
      allowed_roles: ["owner", "approver"]
```

### Implementation

```python
# gao_dev/lifecycle/governance.py
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import Document

@dataclass
class DocumentReview:
    """Record of a document review."""
    id: Optional[int]
    document_id: int
    reviewer: str
    reviewed_at: str
    notes: Optional[str]
    next_review_due: str

class DocumentGovernance:
    """
    Document governance with ownership and review cycles.

    Implements 5S Sustain principle.
    """

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        governance_config_path: Path
    ):
        """
        Initialize governance manager.

        Args:
            document_manager: Document lifecycle manager
            governance_config_path: Path to governance.yaml
        """
        self.doc_mgr = document_manager
        self.config = self._load_config(governance_config_path)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        """Load governance configuration."""
        with open(path) as f:
            return yaml.safe_load(f)

    def assign_owner(self, doc_id: int, owner: str) -> None:
        """Assign document owner."""
        self.doc_mgr.registry.update_document(doc_id, owner=owner)

    def assign_reviewer(self, doc_id: int, reviewer: str) -> None:
        """Assign document reviewer."""
        self.doc_mgr.registry.update_document(doc_id, reviewer=reviewer)

    def auto_assign_ownership(
        self,
        document: Document
    ) -> None:
        """
        Auto-assign owner and reviewer based on RACI matrix.

        Called when document is created.
        """
        doc_type = document.doc_type.value
        ownership = self.config['document_governance']['ownership'].get(doc_type, {})

        owner = ownership.get('approved_by')
        reviewer = ownership.get('reviewed_by')

        if owner:
            self.assign_owner(document.id, owner)

        if reviewer:
            self.assign_reviewer(document.id, reviewer)

        # Set initial review due date
        self._set_review_due_date(document)

    def _set_review_due_date(self, document: Document) -> None:
        """Calculate and set review due date."""
        doc_type = document.doc_type.value
        cadence_days = self.config['document_governance']['review_cadence'].get(doc_type, 90)

        if cadence_days == -1:
            # Never review (immutable docs like ADRs)
            return

        due_date = datetime.now() + timedelta(days=cadence_days)
        self.doc_mgr.registry.update_document(
            document.id,
            review_due_date=due_date.strftime('%Y-%m-%d')
        )

    def check_review_due(
        self,
        owner: Optional[str] = None,
        include_overdue_only: bool = False
    ) -> List[Document]:
        """
        Get documents needing review.

        Args:
            owner: Filter by owner
            include_overdue_only: Only include overdue documents

        Returns:
            List of documents needing review
        """
        all_docs = self.doc_mgr.registry.query_documents(owner=owner)

        review_due = []
        today = datetime.now().date()

        for doc in all_docs:
            review_due_date_str = doc.metadata.get('review_due_date')

            if not review_due_date_str:
                continue

            try:
                review_due_date = datetime.strptime(review_due_date_str, '%Y-%m-%d').date()

                if include_overdue_only:
                    if review_due_date < today:
                        review_due.append(doc)
                else:
                    if review_due_date <= today + timedelta(days=7):  # Due within 7 days
                        review_due.append(doc)

            except ValueError:
                continue

        return review_due

    def mark_reviewed(
        self,
        doc_id: int,
        reviewer: str,
        notes: Optional[str] = None
    ) -> DocumentReview:
        """
        Mark document as reviewed.

        Args:
            doc_id: Document ID
            reviewer: Who performed the review
            notes: Optional review notes

        Returns:
            Review record
        """
        document = self.doc_mgr.registry.get_document(doc_id)

        # Calculate next review due date
        doc_type = document.doc_type.value
        cadence_days = self.config['document_governance']['review_cadence'].get(doc_type, 90)

        if cadence_days != -1:
            next_due = datetime.now() + timedelta(days=cadence_days)
            next_due_str = next_due.strftime('%Y-%m-%d')

            # Update review_due_date in document
            self.doc_mgr.registry.update_document(
                doc_id,
                review_due_date=next_due_str
            )
        else:
            next_due_str = None

        # Record review in history
        with self.doc_mgr.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO document_reviews (
                    document_id, reviewer, reviewed_at, notes, next_review_due
                ) VALUES (?, ?, datetime('now'), ?, ?)
            """, (doc_id, reviewer, notes, next_due_str))

            review_id = cursor.lastrowid

        return DocumentReview(
            id=review_id,
            document_id=doc_id,
            reviewer=reviewer,
            reviewed_at=datetime.now().isoformat(),
            notes=notes,
            next_review_due=next_due_str
        )

    def get_review_history(self, doc_id: int) -> List[DocumentReview]:
        """Get review history for document."""
        with self.doc_mgr.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM document_reviews
                WHERE document_id = ?
                ORDER BY reviewed_at DESC
            """, (doc_id,))

            return [
                DocumentReview(
                    id=row['id'],
                    document_id=row['document_id'],
                    reviewer=row['reviewer'],
                    reviewed_at=row['reviewed_at'],
                    notes=row['notes'],
                    next_review_due=row['next_review_due']
                )
                for row in cursor.fetchall()
            ]

    def generate_governance_report(self) -> str:
        """Generate governance compliance report."""
        report = "# Document Governance Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Documents needing review
        review_due = self.check_review_due(include_overdue_only=False)
        overdue = [d for d in review_due if self._is_overdue(d)]

        report += f"## Review Status\n\n"
        report += f"- **Overdue Reviews**: {len(overdue)}\n"
        report += f"- **Due Within 7 Days**: {len(review_due)}\n\n"

        if overdue:
            report += "### Overdue Reviews\n\n"
            report += "| Document | Owner | Due Date | Days Overdue |\n"
            report += "|----------|-------|----------|-------------|\n"

            for doc in sorted(overdue, key=lambda d: self._days_overdue(d), reverse=True):
                report += f"| {doc.path} | {doc.metadata.get('owner', 'N/A')} | "
                report += f"{doc.metadata.get('review_due_date', 'N/A')} | "
                report += f"{self._days_overdue(doc)} |\n"

            report += "\n"

        # Documents without owners
        all_docs = self.doc_mgr.registry.query_documents()
        no_owner = [d for d in all_docs if not d.metadata.get('owner')]

        if no_owner:
            report += f"### Documents Without Owners ({len(no_owner)})\n\n"
            for doc in no_owner:
                report += f"- {doc.path} ({doc.doc_type.value})\n"
            report += "\n"

        return report

    def _is_overdue(self, doc: Document) -> bool:
        """Check if document review is overdue."""
        review_due_str = doc.metadata.get('review_due_date')
        if not review_due_str:
            return False

        try:
            due_date = datetime.strptime(review_due_str, '%Y-%m-%d').date()
            return due_date < datetime.now().date()
        except ValueError:
            return False

    def _days_overdue(self, doc: Document) -> int:
        """Calculate days overdue."""
        review_due_str = doc.metadata.get('review_due_date')
        if not review_due_str:
            return 0

        try:
            due_date = datetime.strptime(review_due_str, '%Y-%m-%d').date()
            delta = datetime.now().date() - due_date
            return max(0, delta.days)
        except ValueError:
            return 0
```

### Database Schema Addition

```sql
-- Add to migration
CREATE TABLE document_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    reviewer TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    notes TEXT,
    next_review_due TEXT
);

CREATE INDEX idx_reviews_document ON document_reviews(document_id);
CREATE INDEX idx_reviews_date ON document_reviews(reviewed_at);
```

**Files to Create:**
- `gao_dev/lifecycle/governance.py`
- `gao_dev/config/governance.yaml`
- `gao_dev/lifecycle/migrations/003_add_reviews_table.py`
- `tests/lifecycle/test_governance.py`

**Dependencies:**
- Story 12.2 (DocumentRegistry)

---

## Testing Requirements

### Unit Tests
- [ ] Test governance config loading
- [ ] Test auto-assignment of owner/reviewer
- [ ] Test review due date calculation
- [ ] Test check_review_due() with filters
- [ ] Test mark_reviewed() updates due date
- [ ] Test review history tracking

### Integration Tests
- [ ] Create document, verify auto-assignment
- [ ] Mark as reviewed, verify next due date set
- [ ] Generate governance report

### Performance Tests
- [ ] Check review due for 1000 documents in <1 second

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Governance configuration guide
- [ ] RACI matrix documentation
- [ ] Review cycle best practices
- [ ] CLI command examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Governance configuration validated
- [ ] Review cycles tested
- [ ] Committed with atomic commit message
