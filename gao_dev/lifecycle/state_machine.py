"""
Document State Machine Implementation.

This module provides the DocumentStateMachine class for managing document lifecycle
state transitions with validation, business rules, and audit trail.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List, TYPE_CHECKING

from gao_dev.lifecycle.models import Document, DocumentState
from gao_dev.lifecycle.exceptions import InvalidStateTransition

if TYPE_CHECKING:
    from gao_dev.lifecycle.registry import DocumentRegistry


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

    This class enforces valid state transitions and business rules for documents.
    It maintains an audit trail of all state changes and supports custom hooks
    for validation and side effects.

    Valid Transitions:
        - DRAFT -> ACTIVE (on approval/completion)
        - DRAFT -> ARCHIVED (if never activated)
        - ACTIVE -> OBSOLETE (when replaced by newer version)
        - ACTIVE -> ARCHIVED (if no longer needed)
        - OBSOLETE -> ARCHIVED (cleanup)
        - ARCHIVED -> (terminal state, no transitions out)

    Business Rules:
        - Only one ACTIVE document per (type, feature) combination
        - When document transitions to ACTIVE, previous ACTIVE becomes OBSOLETE
        - DRAFT documents can be deleted without becoming ARCHIVED
        - ARCHIVED documents are read-only

    Thread Safety:
        Uses registry's connection management (thread-safe via thread-local connections)
    """

    # Valid state transitions
    TRANSITIONS = {
        DocumentState.DRAFT: [DocumentState.ACTIVE, DocumentState.ARCHIVED],
        DocumentState.ACTIVE: [DocumentState.OBSOLETE, DocumentState.ARCHIVED],
        DocumentState.OBSOLETE: [DocumentState.ARCHIVED],
        DocumentState.ARCHIVED: [],  # Terminal state
    }

    def __init__(self, registry: "DocumentRegistry"):
        """
        Initialize state machine.

        Args:
            registry: Document registry for querying/updating documents
        """
        self.registry = registry
        self._before_hooks: List[Callable] = []
        self._after_hooks: List[Callable] = []

        # Apply migration 002 if not already applied
        self._ensure_transitions_table()

    def _ensure_transitions_table(self) -> None:
        """Ensure document_transitions table exists."""
        import importlib.util
        from pathlib import Path as ImportPath

        # Import migration module dynamically
        migration_path = (
            ImportPath(__file__).parent / "migrations" / "002_add_transitions_table.py"
        )
        spec = importlib.util.spec_from_file_location("migration_002", migration_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        Migration002 = migration_module.Migration002

        with self.registry._get_connection() as conn:
            if not Migration002.is_applied(conn):
                Migration002.up(conn)

    def can_transition(self, from_state: DocumentState, to_state: DocumentState) -> bool:
        """
        Check if transition is allowed.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid, False otherwise

        Example:
            >>> machine.can_transition(DocumentState.DRAFT, DocumentState.ACTIVE)
            True
            >>> machine.can_transition(DocumentState.ARCHIVED, DocumentState.ACTIVE)
            False
        """
        return to_state in self.TRANSITIONS.get(from_state, [])

    def transition(
        self,
        document: Document,
        to_state: DocumentState,
        reason: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> Document:
        """
        Execute state transition with validation and business rules.

        This method:
        1. Validates the transition is allowed
        2. Requires reason for certain transitions
        3. Executes before hooks (for custom validation)
        4. Enforces business rules (e.g., one active per type+feature)
        5. Updates document state
        6. Records transition in audit trail
        7. Executes after hooks (for side effects)

        Args:
            document: Document to transition
            to_state: Target state
            reason: Reason for transition (required for OBSOLETE and ARCHIVED)
            changed_by: Who initiated the change (defaults to "system")

        Returns:
            Updated document with new state

        Raises:
            InvalidStateTransition: If transition not allowed
            ValueError: If reason required but not provided

        Example:
            >>> doc = registry.get_document(1)
            >>> updated_doc = machine.transition(
            ...     doc,
            ...     DocumentState.ACTIVE,
            ...     reason="Approved by team",
            ...     changed_by="john"
            ... )
        """
        from_state = document.state

        # Validate transition
        if not self.can_transition(from_state, to_state):
            raise InvalidStateTransition(
                f"Cannot transition from {from_state.value} to {to_state.value}",
                from_state=from_state.value,
                to_state=to_state.value,
                doc_id=document.id,
            )

        # Require reason for critical transitions
        if to_state in [DocumentState.OBSOLETE, DocumentState.ARCHIVED]:
            if not reason or reason.strip() == "":
                raise ValueError(
                    f"Reason required for transition to {to_state.value}"
                )

        # Execute before hooks
        for hook in self._before_hooks:
            hook(document, to_state)

        # Business rule: Only one ACTIVE document per type+feature
        if to_state == DocumentState.ACTIVE:
            self._enforce_single_active(document)

        # Update document state
        updated_doc = self.registry.update_document(document.id, state=to_state)

        # Record transition in audit trail
        self._record_transition(
            document_id=document.id,
            from_state=from_state,
            to_state=to_state,
            reason=reason or "No reason provided",
            changed_by=changed_by,
        )

        # Execute after hooks
        for hook in self._after_hooks:
            hook(updated_doc, from_state, to_state)

        return updated_doc

    def _enforce_single_active(self, document: Document) -> None:
        """
        Ensure only one ACTIVE document per type+feature.

        When activating a document, mark previous ACTIVE as OBSOLETE.

        Args:
            document: Document being activated
        """
        if not document.feature:
            return  # No feature context, skip check

        # Find current active document of same type+feature
        active_docs = self.registry.query_documents(
            doc_type=document.type.value,
            state=DocumentState.ACTIVE,
            feature=document.feature,
        )

        for active_doc in active_docs:
            if active_doc.id != document.id:
                # Mark as obsolete
                self.registry.update_document(active_doc.id, state=DocumentState.OBSOLETE)
                self._record_transition(
                    document_id=active_doc.id,
                    from_state=DocumentState.ACTIVE,
                    to_state=DocumentState.OBSOLETE,
                    reason=f"Replaced by document {document.id}",
                    changed_by="system",
                )

    def _record_transition(
        self,
        document_id: int,
        from_state: DocumentState,
        to_state: DocumentState,
        reason: str,
        changed_by: Optional[str],
    ) -> None:
        """
        Record state transition in audit trail.

        Args:
            document_id: Document ID
            from_state: Previous state
            to_state: New state
            reason: Transition reason
            changed_by: Who made the change
        """
        from datetime import datetime

        with self.registry._get_connection() as conn:
            # Use Python datetime for microsecond precision instead of SQL datetime('now')
            timestamp = datetime.now().isoformat()
            conn.execute(
                """
                INSERT INTO document_transitions (
                    document_id, from_state, to_state, reason, changed_by, changed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    from_state.value,
                    to_state.value,
                    reason,
                    changed_by or "system",
                    timestamp,
                ),
            )

    def get_transition_history(self, document_id: int) -> List[StateTransition]:
        """
        Get transition history for a document.

        Returns all state transitions ordered by date (most recent first).

        Args:
            document_id: Document ID

        Returns:
            List of StateTransition objects

        Example:
            >>> history = machine.get_transition_history(1)
            >>> for transition in history:
            ...     print(f"{transition.from_state} -> {transition.to_state}: {transition.reason}")
        """
        with self.registry._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM document_transitions
                WHERE document_id = ?
                ORDER BY changed_at DESC
                """,
                (document_id,),
            )

            return [
                StateTransition(
                    document_id=row["document_id"],
                    from_state=DocumentState(row["from_state"]),
                    to_state=DocumentState(row["to_state"]),
                    reason=row["reason"],
                    changed_by=row["changed_by"],
                    changed_at=row["changed_at"],
                )
                for row in cursor.fetchall()
            ]

    def register_before_hook(self, hook: Callable[[Document, DocumentState], None]) -> None:
        """
        Register hook to run before transition.

        The hook should accept (document, to_state) and can raise an exception
        to prevent the transition.

        Args:
            hook: Callable that takes (document, to_state)

        Example:
            >>> def validate_approval(doc, to_state):
            ...     if to_state == DocumentState.ACTIVE:
            ...         if not doc.metadata.get("approved"):
            ...             raise ValueError("Document must be approved first")
            >>> machine.register_before_hook(validate_approval)
        """
        self._before_hooks.append(hook)

    def register_after_hook(
        self, hook: Callable[[Document, DocumentState, DocumentState], None]
    ) -> None:
        """
        Register hook to run after transition.

        The hook should accept (document, from_state, to_state) and can perform
        side effects like sending notifications or updating related documents.

        Args:
            hook: Callable that takes (document, from_state, to_state)

        Example:
            >>> def notify_on_active(doc, from_state, to_state):
            ...     if to_state == DocumentState.ACTIVE:
            ...         print(f"Document {doc.id} is now active!")
            >>> machine.register_after_hook(notify_on_active)
        """
        self._after_hooks.append(hook)

    def clear_hooks(self) -> None:
        """Clear all registered hooks (useful for testing)."""
        self._before_hooks.clear()
        self._after_hooks.clear()

    def get_valid_transitions(self, from_state: DocumentState) -> List[DocumentState]:
        """
        Get list of valid target states from a given state.

        Args:
            from_state: Current state

        Returns:
            List of valid target states

        Example:
            >>> machine.get_valid_transitions(DocumentState.DRAFT)
            [<DocumentState.ACTIVE: 'active'>, <DocumentState.ARCHIVED: 'archived'>]
        """
        return self.TRANSITIONS.get(from_state, [])

    def is_terminal_state(self, state: DocumentState) -> bool:
        """
        Check if a state is terminal (no transitions out).

        Args:
            state: State to check

        Returns:
            True if state is terminal, False otherwise

        Example:
            >>> machine.is_terminal_state(DocumentState.ARCHIVED)
            True
            >>> machine.is_terminal_state(DocumentState.DRAFT)
            False
        """
        return len(self.TRANSITIONS.get(state, [])) == 0
