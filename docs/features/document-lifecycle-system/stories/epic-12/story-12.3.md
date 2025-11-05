# Story 12.3: Document State Machine

**Epic:** 12 - Document Lifecycle Management (Enhanced)
**Story Points:** 3
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** 1

---

## Story Description

Implement a state machine for document lifecycle with validation and transition logic. Enforces valid state transitions (draft→active→obsolete→archived) with business rules like "only one active document per type+feature."

---

## Business Value

The state machine provides:
- **Consistency**: Enforces valid state transitions across all documents
- **Business Rules**: Only one active PRD/Architecture per feature
- **Auditability**: Tracks all state changes with reasons and timestamps
- **Extensibility**: Hooks for custom transition logic (e.g., notifications)
- **Safety**: Prevents invalid state changes that could corrupt the system

---

## Acceptance Criteria

### State Machine Definition
- [ ] `DocumentStateMachine` class implemented
- [ ] Four states supported: DRAFT, ACTIVE, OBSOLETE, ARCHIVED
- [ ] Valid transitions defined:
  - DRAFT → ACTIVE (on approval/completion)
  - DRAFT → ARCHIVED (if never activated)
  - ACTIVE → OBSOLETE (when replaced by newer version)
  - ACTIVE → ARCHIVED (if no longer needed)
  - OBSOLETE → ARCHIVED (automatic or manual cleanup)
- [ ] Terminal state: ARCHIVED (no transitions out)

### Transition Validation
- [ ] `can_transition(from_state, to_state)` validates if transition allowed
- [ ] `transition(document, to_state, reason)` executes state change
- [ ] Invalid transitions raise `InvalidStateTransition` exception
- [ ] Transition reason required for ACTIVE→OBSOLETE and ACTIVE→ARCHIVED
- [ ] Transition history logged to audit table

### Business Rules
- [ ] Only one ACTIVE document per (type, feature) combination enforced
- [ ] When document transitions to ACTIVE, previous ACTIVE becomes OBSOLETE
- [ ] DRAFT documents can be deleted without becoming ARCHIVED
- [ ] ARCHIVED documents cannot be modified (read-only)
- [ ] Transition hooks system implemented for custom logic

### Audit Trail
- [ ] `document_transitions` table tracks all state changes
- [ ] Records: document_id, from_state, to_state, reason, changed_by, changed_at
- [ ] Query interface: get_transition_history(doc_id)
- [ ] Audit trail preserved even if document deleted

### Hooks System
- [ ] `before_transition(document, to_state)` hook for validation
- [ ] `after_transition(document, from_state, to_state)` hook for side effects
- [ ] Default hooks can be overridden
- [ ] Example hooks: send notification, trigger archival, update relationships

### Unit Tests
- [ ] All valid transitions tested
- [ ] All invalid transitions tested (should raise exception)
- [ ] Business rule "one active per type+feature" tested
- [ ] Transition history tracked correctly
- [ ] Hook system tested
- [ ] Test coverage >80%

---

## Technical Notes

### State Machine Implementation

```python
# gao_dev/lifecycle/state_machine.py
from enum import Enum
from typing import Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime

from gao_dev.lifecycle.models import Document, DocumentState
from gao_dev.lifecycle.exceptions import InvalidStateTransition

@dataclass
class StateTransition:
    """Record of a state transition."""
    document_id: int
    from_state: DocumentState
    to_state: DocumentState
    reason: str
    changed_by: Optional[str]
    changed_at: str

class DocumentStateMachine:
    """
    State machine for document lifecycle.

    Enforces valid transitions and business rules.
    """

    # Valid state transitions
    TRANSITIONS = {
        DocumentState.DRAFT: [DocumentState.ACTIVE, DocumentState.ARCHIVED],
        DocumentState.ACTIVE: [DocumentState.OBSOLETE, DocumentState.ARCHIVED],
        DocumentState.OBSOLETE: [DocumentState.ARCHIVED],
        DocumentState.ARCHIVED: []  # Terminal state
    }

    def __init__(self, registry: 'DocumentRegistry'):
        """
        Initialize state machine.

        Args:
            registry: Document registry for querying/updating documents
        """
        self.registry = registry
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []

    def can_transition(
        self,
        from_state: DocumentState,
        to_state: DocumentState
    ) -> bool:
        """
        Check if transition is allowed.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        return to_state in self.TRANSITIONS.get(from_state, [])

    def transition(
        self,
        document: Document,
        to_state: DocumentState,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None
    ) -> Document:
        """
        Execute state transition with validation.

        Args:
            document: Document to transition
            to_state: Target state
            reason: Reason for transition (required for some transitions)
            changed_by: Who initiated the change

        Returns:
            Updated document

        Raises:
            InvalidStateTransition: If transition not allowed
        """
        from_state = document.state

        # Validate transition
        if not self.can_transition(from_state, to_state):
            raise InvalidStateTransition(
                f"Cannot transition from {from_state.value} to {to_state.value}"
            )

        # Require reason for critical transitions
        if to_state in [DocumentState.OBSOLETE, DocumentState.ARCHIVED] and not reason:
            raise ValueError(f"Reason required for transition to {to_state.value}")

        # Execute before hooks
        for hook in self._before_hooks:
            hook(document, to_state)

        # Business rule: Only one ACTIVE document per type+feature
        if to_state == DocumentState.ACTIVE:
            self._enforce_single_active(document)

        # Update document state
        updated_doc = self.registry.update_document(
            document.id,
            state=to_state
        )

        # Record transition in audit trail
        self._record_transition(
            document_id=document.id,
            from_state=from_state,
            to_state=to_state,
            reason=reason or "No reason provided",
            changed_by=changed_by
        )

        # Execute after hooks
        for hook in self._after_hooks:
            hook(updated_doc, from_state, to_state)

        return updated_doc

    def _enforce_single_active(self, document: Document) -> None:
        """
        Ensure only one ACTIVE document per type+feature.

        When activating a document, mark previous ACTIVE as OBSOLETE.
        """
        if not document.feature:
            return  # No feature context, skip check

        # Find current active document of same type+feature
        active_docs = self.registry.query_documents(
            doc_type=document.doc_type.value,
            state=DocumentState.ACTIVE,
            feature=document.feature
        )

        for active_doc in active_docs:
            if active_doc.id != document.id:
                # Mark as obsolete
                self.registry.update_document(
                    active_doc.id,
                    state=DocumentState.OBSOLETE
                )
                self._record_transition(
                    document_id=active_doc.id,
                    from_state=DocumentState.ACTIVE,
                    to_state=DocumentState.OBSOLETE,
                    reason=f"Replaced by document {document.id}",
                    changed_by="system"
                )

    def _record_transition(
        self,
        document_id: int,
        from_state: DocumentState,
        to_state: DocumentState,
        reason: str,
        changed_by: Optional[str]
    ) -> None:
        """Record state transition in audit trail."""
        with self.registry._get_connection() as conn:
            conn.execute("""
                INSERT INTO document_transitions (
                    document_id, from_state, to_state, reason, changed_by, changed_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                document_id,
                from_state.value,
                to_state.value,
                reason,
                changed_by or "system"
            ))

    def get_transition_history(self, document_id: int) -> List[StateTransition]:
        """Get transition history for a document."""
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM document_transitions
                WHERE document_id = ?
                ORDER BY changed_at DESC
            """, (document_id,))

            return [
                StateTransition(
                    document_id=row['document_id'],
                    from_state=DocumentState(row['from_state']),
                    to_state=DocumentState(row['to_state']),
                    reason=row['reason'],
                    changed_by=row['changed_by'],
                    changed_at=row['changed_at']
                )
                for row in cursor.fetchall()
            ]

    def register_before_hook(self, hook: Callable) -> None:
        """Register hook to run before transition."""
        self._before_hooks.append(hook)

    def register_after_hook(self, hook: Callable) -> None:
        """Register hook to run after transition."""
        self._after_hooks.append(hook)
```

### Audit Trail Schema

```sql
-- Add to migration
CREATE TABLE document_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    from_state TEXT NOT NULL CHECK(from_state IN ('draft', 'active', 'obsolete', 'archived')),
    to_state TEXT NOT NULL CHECK(to_state IN ('draft', 'active', 'obsolete', 'archived')),
    reason TEXT NOT NULL,
    changed_by TEXT,
    changed_at TEXT NOT NULL
);

CREATE INDEX idx_transitions_document ON document_transitions(document_id);
CREATE INDEX idx_transitions_date ON document_transitions(changed_at);
```

**Files to Create:**
- `gao_dev/lifecycle/state_machine.py`
- `gao_dev/lifecycle/migrations/002_add_transitions_table.py`
- `tests/lifecycle/test_state_machine.py`
- `tests/lifecycle/test_state_transitions.py`

**Dependencies:**
- Story 12.2 (DocumentRegistry)

---

## Testing Requirements

### Unit Tests

**Transition Validation Tests:**
- [ ] Test can_transition() for all valid transitions returns True
- [ ] Test can_transition() for all invalid transitions returns False
- [ ] Test DRAFT → ACTIVE allowed
- [ ] Test DRAFT → OBSOLETE not allowed (should raise exception)
- [ ] Test ARCHIVED → anything not allowed

**Transition Execution Tests:**
- [ ] Test transition() updates document state
- [ ] Test transition() records audit trail
- [ ] Test transition() without reason for OBSOLETE raises error
- [ ] Test transition() with reason succeeds

**Business Rule Tests:**
- [ ] Test activating document marks previous ACTIVE as OBSOLETE
- [ ] Test multiple DRAFT documents allowed
- [ ] Test multiple OBSOLETE documents allowed
- [ ] Test only one ACTIVE per type+feature enforced

**Audit Trail Tests:**
- [ ] Test get_transition_history() returns all transitions
- [ ] Test transitions ordered by date (newest first)
- [ ] Test transition history includes reason and changed_by

**Hooks Tests:**
- [ ] Test before_hook called before transition
- [ ] Test after_hook called after transition
- [ ] Test hook can prevent transition (raise exception)

### Integration Tests
- [ ] Register document, transition through full lifecycle
- [ ] Create two documents, activate second, verify first becomes OBSOLETE
- [ ] Verify audit trail complete after multiple transitions

### Performance Tests
- [ ] Transition completes in <50ms
- [ ] Audit trail query completes in <50ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] State diagram showing all transitions
- [ ] Business rules documented clearly
- [ ] Hook system documentation with examples
- [ ] Audit trail query examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] State transition diagram created
- [ ] Business rules verified
- [ ] Committed with atomic commit message
