# Story 12.6 (ENHANCED): Archival System + Retention Policies

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 6
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** 2

---

## Story Description

Implement comprehensive archival system with retention policy framework for compliance. Moves obsolete documents based on configurable rules, with distinction between archive vs delete, retention periods per document type, and compliance tag protection (5S: Shine - regular cleanup).

---

## Business Value

The archival system provides:
- **Compliance**: Retention policies ensure regulatory compliance (e.g., QA reports retained 5 years)
- **Organization**: Prevents accumulation of stale documents (5S: Shine)
- **Safety**: Archive vs delete distinction prevents accidental data loss
- **Flexibility**: Configurable policies per document type
- **Auditability**: Complete audit trail of archival decisions

---

## Acceptance Criteria

### Archival Rules Configuration
- [ ] YAML configuration file: `gao_dev/config/retention_policies.yaml`
- [ ] Rules support:
  - Document type (prd, architecture, story, etc.)
  - State filter (obsolete, active, draft)
  - Age in days threshold
  - Compliance tags (prevent deletion)
  - Archive retention period (how long to keep in archive)
  - Delete after archive flag (whether to permanently delete)
- [ ] Multiple rules per document type supported
- [ ] Rules evaluated in order (first match wins)

### Retention Policy Framework
- [ ] `archive_to_obsolete`: Days before ACTIVE→OBSOLETE (e.g., 30 days)
- [ ] `obsolete_to_archive`: Days before OBSOLETE→ARCHIVED (e.g., 90 days)
- [ ] `archive_retention`: Days to retain in archive before eligible for deletion (e.g., 730 = 2 years)
- [ ] `delete_after_archive`: Boolean - whether document can be deleted after retention expires
- [ ] `compliance_tags`: List of tags that prevent deletion (e.g., ["audit", "compliance", "legal"])

### Archive vs Delete Distinction
- [ ] Archive: Move to `.archive/`, state=ARCHIVED, metadata preserved
- [ ] Delete: Permanently remove file and database record (only if retention expired)
- [ ] Documents with compliance tags NEVER deleted (only archived)
- [ ] Postmortems NEVER deleted (retention = -1)
- [ ] QA reports retained 5 years minimum (compliance)

### Archival Operations
- [ ] `archive_obsolete_documents()` applies rules and archives matching documents
- [ ] Moves files to `.archive/` with preserved structure
- [ ] Updates state to ARCHIVED
- [ ] Metadata preserved in database with archive timestamp
- [ ] Dry-run mode for testing (shows what would be archived without doing it)

### CLI Commands
- [ ] `gao-dev lifecycle archive` - Archive obsolete documents based on rules
- [ ] `gao-dev lifecycle archive --dry-run` - Preview what would be archived
- [ ] `gao-dev lifecycle cleanup` - Delete documents past retention period
- [ ] `gao-dev lifecycle cleanup --dry-run` - Preview what would be deleted
- [ ] `gao-dev lifecycle retention-report` - Show retention policy compliance

### Retention Policy Report
- [ ] Shows all documents and their retention status
- [ ] Groups by document type
- [ ] Indicates:
  - Documents eligible for archival
  - Documents eligible for deletion
  - Days until next action
  - Compliance tags protecting documents
- [ ] Export to CSV for compliance audits

### Safety Features
- [ ] Atomic file operations (copy then delete)
- [ ] Backup before deletion (optional)
- [ ] Confirmation required for destructive operations
- [ ] Undo capability (restore from archive)
- [ ] Audit trail of all archival/deletion operations

**Test Coverage:** >80%

---

## Technical Notes

### Retention Policies Configuration

```yaml
# gao_dev/config/retention_policies.yaml
retention_policies:
  prd:
    archive_to_obsolete: 30  # Days before marking obsolete
    obsolete_to_archive: 90  # Days before archiving
    archive_retention: 730   # 2 years in archive
    delete_after_archive: false  # NEVER delete PRDs
    compliance_tags: ["product-decisions", "requirements"]

  architecture:
    obsolete_to_archive: 60
    archive_retention: 730  # 2 years
    delete_after_archive: false
    compliance_tags: ["architecture-decisions"]

  story:
    obsolete_to_archive: 90
    archive_retention: 365  # 1 year
    delete_after_archive: true  # Can delete after 1 year
    compliance_tags: []

  qa_report:
    obsolete_to_archive: 30
    archive_retention: 1825  # 5 years (compliance requirement)
    delete_after_archive: false
    compliance_tags: ["quality-audit", "compliance"]

  test_report:
    obsolete_to_archive: 30
    archive_retention: 365  # 1 year
    delete_after_archive: true
    compliance_tags: []

  postmortem:
    obsolete_to_archive: -1  # Never becomes obsolete
    archive_retention: -1    # Keep forever
    delete_after_archive: false
    compliance_tags: ["incidents", "learning", "compliance"]

  draft:
    obsolete_to_archive: 7   # Archive drafts after 7 days
    archive_retention: 30    # Keep 30 days
    delete_after_archive: true  # Can delete
    compliance_tags: []
```

### Implementation

```python
# gao_dev/lifecycle/archival.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml

from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import Document, DocumentState

@dataclass
class RetentionPolicy:
    """Retention policy for document type."""
    doc_type: str
    archive_to_obsolete: int  # Days, -1 = never
    obsolete_to_archive: int  # Days, -1 = never
    archive_retention: int    # Days, -1 = forever
    delete_after_archive: bool
    compliance_tags: List[str]

@dataclass
class ArchivalAction:
    """Proposed archival action."""
    document: Document
    action: str  # 'archive', 'delete', 'none'
    reason: str
    days_until_action: int

class ArchivalManager:
    """
    Manage document archival with retention policies.

    Implements 5S Shine principle (regular cleanup).
    """

    def __init__(
        self,
        document_manager: DocumentLifecycleManager,
        policies_path: Path
    ):
        """
        Initialize archival manager.

        Args:
            document_manager: Document lifecycle manager
            policies_path: Path to retention_policies.yaml
        """
        self.doc_mgr = document_manager
        self.policies = self._load_policies(policies_path)

    def _load_policies(self, path: Path) -> Dict[str, RetentionPolicy]:
        """Load retention policies from YAML."""
        with open(path) as f:
            config = yaml.safe_load(f)

        policies = {}
        for doc_type, policy_config in config['retention_policies'].items():
            policies[doc_type] = RetentionPolicy(
                doc_type=doc_type,
                **policy_config
            )

        return policies

    def archive_obsolete_documents(
        self,
        dry_run: bool = False
    ) -> List[ArchivalAction]:
        """
        Archive documents based on retention policies.

        Args:
            dry_run: If True, only show what would be archived

        Returns:
            List of archival actions performed
        """
        actions = []

        # Get all obsolete documents
        obsolete_docs = self.doc_mgr.registry.query_documents(
            state=DocumentState.OBSOLETE
        )

        for doc in obsolete_docs:
            action = self._evaluate_archival(doc)

            if action.action == 'archive':
                actions.append(action)

                if not dry_run:
                    self.doc_mgr.archive_document(doc.id)

        return actions

    def cleanup_expired_documents(
        self,
        dry_run: bool = False
    ) -> List[ArchivalAction]:
        """
        Delete documents past retention period.

        Args:
            dry_run: If True, only show what would be deleted

        Returns:
            List of deletion actions performed
        """
        actions = []

        # Get all archived documents
        archived_docs = self.doc_mgr.registry.query_documents(
            state=DocumentState.ARCHIVED
        )

        for doc in archived_docs:
            action = self._evaluate_deletion(doc)

            if action.action == 'delete':
                actions.append(action)

                if not dry_run:
                    self._delete_document(doc)

        return actions

    def _evaluate_archival(self, doc: Document) -> ArchivalAction:
        """Evaluate if document should be archived."""
        policy = self.policies.get(doc.doc_type.value)

        if not policy or policy.obsolete_to_archive == -1:
            return ArchivalAction(
                document=doc,
                action='none',
                reason='No archival policy or never archive',
                days_until_action=-1
            )

        # Calculate age since becoming obsolete
        # (This would need transition history from state machine)
        modified_date = datetime.fromisoformat(doc.modified_at)
        age_days = (datetime.now() - modified_date).days

        if age_days >= policy.obsolete_to_archive:
            return ArchivalAction(
                document=doc,
                action='archive',
                reason=f'Obsolete for {age_days} days (policy: {policy.obsolete_to_archive})',
                days_until_action=0
            )
        else:
            return ArchivalAction(
                document=doc,
                action='none',
                reason=f'Not old enough ({age_days}/{policy.obsolete_to_archive} days)',
                days_until_action=policy.obsolete_to_archive - age_days
            )

    def _evaluate_deletion(self, doc: Document) -> ArchivalAction:
        """Evaluate if archived document should be deleted."""
        policy = self.policies.get(doc.doc_type.value)

        if not policy:
            return ArchivalAction(
                document=doc,
                action='none',
                reason='No retention policy',
                days_until_action=-1
            )

        # Check compliance tags
        doc_tags = doc.metadata.get('tags', [])
        has_compliance_tags = any(
            tag in policy.compliance_tags
            for tag in doc_tags
        )

        if has_compliance_tags:
            return ArchivalAction(
                document=doc,
                action='none',
                reason=f'Protected by compliance tags: {doc_tags}',
                days_until_action=-1
            )

        # Check if deletion allowed
        if not policy.delete_after_archive:
            return ArchivalAction(
                document=doc,
                action='none',
                reason='Deletion not allowed by policy',
                days_until_action=-1
            )

        # Check if retention period expired
        if policy.archive_retention == -1:
            return ArchivalAction(
                document=doc,
                action='none',
                reason='Retention period is forever',
                days_until_action=-1
            )

        # Calculate archive age
        archived_date = datetime.fromisoformat(doc.modified_at)
        age_days = (datetime.now() - archived_date).days

        if age_days >= policy.archive_retention:
            return ArchivalAction(
                document=doc,
                action='delete',
                reason=f'Archived for {age_days} days (retention: {policy.archive_retention})',
                days_until_action=0
            )
        else:
            return ArchivalAction(
                document=doc,
                action='none',
                reason=f'Retention not expired ({age_days}/{policy.archive_retention} days)',
                days_until_action=policy.archive_retention - age_days
            )

    def _delete_document(self, doc: Document) -> None:
        """Permanently delete document."""
        # Delete file
        file_path = Path(doc.path)
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        self.doc_mgr.registry.delete_document(doc.id)

    def generate_retention_report(self) -> str:
        """Generate retention policy compliance report."""
        all_docs = self.doc_mgr.registry.query_documents()

        report = "# Document Retention Policy Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group by document type
        by_type = {}
        for doc in all_docs:
            doc_type = doc.doc_type.value
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)

        for doc_type, docs in by_type.items():
            report += f"## {doc_type.upper()} ({len(docs)} documents)\n\n"

            policy = self.policies.get(doc_type)
            if policy:
                report += f"**Policy:** Archive after {policy.obsolete_to_archive} days obsolete, "
                report += f"Retain {policy.archive_retention} days, "
                report += f"Delete: {'Yes' if policy.delete_after_archive else 'No'}\n\n"

            # Analyze each document
            for doc in docs:
                if doc.state == DocumentState.OBSOLETE:
                    action = self._evaluate_archival(doc)
                elif doc.state == DocumentState.ARCHIVED:
                    action = self._evaluate_deletion(doc)
                else:
                    action = ArchivalAction(doc, 'none', 'Not obsolete or archived', -1)

                if action.action != 'none':
                    report += f"- **{doc.path}**: {action.action.upper()} - {action.reason}\n"

            report += "\n"

        return report
```

**Files to Create:**
- `gao_dev/lifecycle/archival.py`
- `gao_dev/config/retention_policies.yaml`
- `gao_dev/cli/lifecycle_commands.py` (enhanced with archive commands)
- `tests/lifecycle/test_archival.py`
- `tests/lifecycle/test_retention_policies.py`

**Dependencies:**
- Story 12.4 (DocumentLifecycleManager)

---

## Testing Requirements

### Unit Tests
- [ ] Test retention policy loading from YAML
- [ ] Test archival evaluation for each policy
- [ ] Test deletion evaluation with compliance tags
- [ ] Test dry-run mode (no actual changes)
- [ ] Test report generation

### Integration Tests
- [ ] Archive documents based on real policies
- [ ] Verify compliance tags prevent deletion
- [ ] Verify retention periods enforced

### Performance Tests
- [ ] Evaluate 1000 documents in <5 seconds

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Retention policy configuration guide
- [ ] Compliance requirements documentation
- [ ] CLI command examples
- [ ] Audit trail documentation

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Retention policies validated
- [ ] Compliance requirements met
- [ ] Committed with atomic commit message
