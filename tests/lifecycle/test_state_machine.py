"""
Unit Tests for DocumentStateMachine.

This module provides comprehensive unit tests for the DocumentStateMachine class,
covering state transitions, validation, business rules, audit trail, and hooks system.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from gao_dev.lifecycle.state_machine import DocumentStateMachine, StateTransition
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType
from gao_dev.lifecycle.exceptions import InvalidStateTransition


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def registry(temp_db):
    """Create DocumentRegistry instance for testing."""
    reg = DocumentRegistry(temp_db)
    yield reg
    reg.close()


@pytest.fixture
def state_machine(registry):
    """Create DocumentStateMachine instance for testing."""
    machine = DocumentStateMachine(registry)
    yield machine
    # Clean up hooks after each test
    machine.clear_hooks()


@pytest.fixture
def draft_document(registry):
    """Create a draft document for testing."""
    return registry.register_document(
        path="docs/test/PRD.md",
        doc_type="prd",
        author="John",
        feature="test-feature",
        epic=1,
        state=DocumentState.DRAFT,
    )


@pytest.fixture
def active_document(registry):
    """Create an active document for testing."""
    return registry.register_document(
        path="docs/test/active-PRD.md",
        doc_type="prd",
        author="John",
        feature="test-feature",
        epic=1,
        state=DocumentState.ACTIVE,
    )


# Test: State Machine Definition


class TestStateMachineDefinition:
    """Tests for state machine definition and structure."""

    def test_transitions_defined(self, state_machine):
        """Test that all valid transitions are defined."""
        assert DocumentState.DRAFT in state_machine.TRANSITIONS
        assert DocumentState.ACTIVE in state_machine.TRANSITIONS
        assert DocumentState.OBSOLETE in state_machine.TRANSITIONS
        assert DocumentState.ARCHIVED in state_machine.TRANSITIONS

    def test_draft_transitions(self, state_machine):
        """Test DRAFT valid transitions."""
        valid = state_machine.TRANSITIONS[DocumentState.DRAFT]
        assert DocumentState.ACTIVE in valid
        assert DocumentState.ARCHIVED in valid
        assert len(valid) == 2

    def test_active_transitions(self, state_machine):
        """Test ACTIVE valid transitions."""
        valid = state_machine.TRANSITIONS[DocumentState.ACTIVE]
        assert DocumentState.OBSOLETE in valid
        assert DocumentState.ARCHIVED in valid
        assert len(valid) == 2

    def test_obsolete_transitions(self, state_machine):
        """Test OBSOLETE valid transitions."""
        valid = state_machine.TRANSITIONS[DocumentState.OBSOLETE]
        assert DocumentState.ARCHIVED in valid
        assert len(valid) == 1

    def test_archived_terminal_state(self, state_machine):
        """Test ARCHIVED is terminal state."""
        valid = state_machine.TRANSITIONS[DocumentState.ARCHIVED]
        assert len(valid) == 0


# Test: Transition Validation


class TestCanTransition:
    """Tests for can_transition() method."""

    def test_draft_to_active_allowed(self, state_machine):
        """Test DRAFT -> ACTIVE is allowed."""
        assert state_machine.can_transition(DocumentState.DRAFT, DocumentState.ACTIVE)

    def test_draft_to_archived_allowed(self, state_machine):
        """Test DRAFT -> ARCHIVED is allowed."""
        assert state_machine.can_transition(DocumentState.DRAFT, DocumentState.ARCHIVED)

    def test_draft_to_obsolete_not_allowed(self, state_machine):
        """Test DRAFT -> OBSOLETE is not allowed."""
        assert not state_machine.can_transition(DocumentState.DRAFT, DocumentState.OBSOLETE)

    def test_active_to_obsolete_allowed(self, state_machine):
        """Test ACTIVE -> OBSOLETE is allowed."""
        assert state_machine.can_transition(DocumentState.ACTIVE, DocumentState.OBSOLETE)

    def test_active_to_archived_allowed(self, state_machine):
        """Test ACTIVE -> ARCHIVED is allowed."""
        assert state_machine.can_transition(DocumentState.ACTIVE, DocumentState.ARCHIVED)

    def test_active_to_draft_not_allowed(self, state_machine):
        """Test ACTIVE -> DRAFT is not allowed."""
        assert not state_machine.can_transition(DocumentState.ACTIVE, DocumentState.DRAFT)

    def test_obsolete_to_archived_allowed(self, state_machine):
        """Test OBSOLETE -> ARCHIVED is allowed."""
        assert state_machine.can_transition(DocumentState.OBSOLETE, DocumentState.ARCHIVED)

    def test_obsolete_to_active_not_allowed(self, state_machine):
        """Test OBSOLETE -> ACTIVE is not allowed."""
        assert not state_machine.can_transition(DocumentState.OBSOLETE, DocumentState.ACTIVE)

    def test_archived_to_anything_not_allowed(self, state_machine):
        """Test ARCHIVED -> anything is not allowed."""
        assert not state_machine.can_transition(DocumentState.ARCHIVED, DocumentState.DRAFT)
        assert not state_machine.can_transition(DocumentState.ARCHIVED, DocumentState.ACTIVE)
        assert not state_machine.can_transition(
            DocumentState.ARCHIVED, DocumentState.OBSOLETE
        )
        assert not state_machine.can_transition(
            DocumentState.ARCHIVED, DocumentState.ARCHIVED
        )


# Test: Transition Execution


class TestTransition:
    """Tests for transition() method."""

    def test_transition_updates_document_state(
        self, state_machine, registry, draft_document
    ):
        """Test transition updates document state."""
        updated_doc = state_machine.transition(
            draft_document, DocumentState.ACTIVE, reason="Approved"
        )

        assert updated_doc.state == DocumentState.ACTIVE
        assert updated_doc.id == draft_document.id

        # Verify in database
        doc_from_db = registry.get_document(draft_document.id)
        assert doc_from_db.state == DocumentState.ACTIVE

    def test_transition_with_invalid_transition_raises_error(
        self, state_machine, draft_document
    ):
        """Test invalid transition raises InvalidStateTransition."""
        with pytest.raises(InvalidStateTransition) as exc_info:
            state_machine.transition(
                draft_document, DocumentState.OBSOLETE, reason="Invalid"
            )

        assert "draft" in str(exc_info.value).lower()
        assert "obsolete" in str(exc_info.value).lower()
        assert exc_info.value.from_state == "draft"
        assert exc_info.value.to_state == "obsolete"
        assert exc_info.value.doc_id == draft_document.id

    def test_transition_to_obsolete_requires_reason(
        self, state_machine, active_document
    ):
        """Test transition to OBSOLETE requires reason."""
        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(active_document, DocumentState.OBSOLETE)

        assert "reason required" in str(exc_info.value).lower()

    def test_transition_to_archived_requires_reason(self, state_machine, active_document):
        """Test transition to ARCHIVED requires reason."""
        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(active_document, DocumentState.ARCHIVED)

        assert "reason required" in str(exc_info.value).lower()

    def test_transition_to_active_does_not_require_reason(
        self, state_machine, draft_document
    ):
        """Test transition to ACTIVE doesn't require reason."""
        updated_doc = state_machine.transition(draft_document, DocumentState.ACTIVE)
        assert updated_doc.state == DocumentState.ACTIVE

    def test_transition_with_empty_reason_rejected(self, state_machine, active_document):
        """Test transition with empty string reason is rejected."""
        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(active_document, DocumentState.OBSOLETE, reason="")

        assert "reason required" in str(exc_info.value).lower()

    def test_transition_with_whitespace_reason_rejected(
        self, state_machine, active_document
    ):
        """Test transition with whitespace-only reason is rejected."""
        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(active_document, DocumentState.OBSOLETE, reason="   ")

        assert "reason required" in str(exc_info.value).lower()


# Test: Business Rules


class TestBusinessRules:
    """Tests for business rule enforcement."""

    def test_activating_document_marks_previous_active_obsolete(
        self, state_machine, registry, active_document
    ):
        """Test activating document marks previous ACTIVE as OBSOLETE."""
        # Create new draft document
        new_doc = registry.register_document(
            path="docs/test/new-PRD.md",
            doc_type="prd",
            author="Sally",
            feature="test-feature",
            epic=1,
            state=DocumentState.DRAFT,
        )

        # Activate new document
        state_machine.transition(new_doc, DocumentState.ACTIVE, reason="New version")

        # Check old document is now obsolete
        old_doc = registry.get_document(active_document.id)
        assert old_doc.state == DocumentState.OBSOLETE

        # Check new document is active
        new_doc_updated = registry.get_document(new_doc.id)
        assert new_doc_updated.state == DocumentState.ACTIVE

    def test_only_one_active_per_type_feature(self, state_machine, registry):
        """Test only one ACTIVE document per type+feature enforced."""
        # Create and activate first document
        doc1 = registry.register_document(
            path="docs/test/PRD-v1.md",
            doc_type="prd",
            author="John",
            feature="feature-a",
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc1, DocumentState.ACTIVE)

        # Create and activate second document (same type+feature)
        doc2 = registry.register_document(
            path="docs/test/PRD-v2.md",
            doc_type="prd",
            author="John",
            feature="feature-a",
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc2, DocumentState.ACTIVE)

        # Query active documents for this type+feature
        active_docs = registry.query_documents(
            doc_type="prd", state=DocumentState.ACTIVE, feature="feature-a"
        )

        # Only one should be active
        assert len(active_docs) == 1
        assert active_docs[0].id == doc2.id

        # First document should be obsolete
        doc1_updated = registry.get_document(doc1.id)
        assert doc1_updated.state == DocumentState.OBSOLETE

    def test_multiple_draft_documents_allowed(self, state_machine, registry):
        """Test multiple DRAFT documents allowed."""
        doc1 = registry.register_document(
            path="docs/test/PRD-draft1.md",
            doc_type="prd",
            author="John",
            feature="feature-a",
            state=DocumentState.DRAFT,
        )

        doc2 = registry.register_document(
            path="docs/test/PRD-draft2.md",
            doc_type="prd",
            author="Sally",
            feature="feature-a",
            state=DocumentState.DRAFT,
        )

        # Both should remain draft
        assert doc1.state == DocumentState.DRAFT
        assert doc2.state == DocumentState.DRAFT

        # Query should find both
        draft_docs = registry.query_documents(
            doc_type="prd", state=DocumentState.DRAFT, feature="feature-a"
        )
        assert len(draft_docs) == 2

    def test_multiple_obsolete_documents_allowed(self, state_machine, registry):
        """Test multiple OBSOLETE documents allowed."""
        doc1 = registry.register_document(
            path="docs/test/PRD-old1.md",
            doc_type="prd",
            author="John",
            feature="feature-a",
            state=DocumentState.ACTIVE,
        )

        doc2 = registry.register_document(
            path="docs/test/PRD-old2.md",
            doc_type="prd",
            author="Sally",
            feature="feature-a",
            state=DocumentState.ACTIVE,
        )

        # Transition both to obsolete
        state_machine.transition(doc1, DocumentState.OBSOLETE, reason="Replaced")
        state_machine.transition(doc2, DocumentState.OBSOLETE, reason="Replaced")

        # Query should find both
        obsolete_docs = registry.query_documents(
            doc_type="prd", state=DocumentState.OBSOLETE, feature="feature-a"
        )
        assert len(obsolete_docs) == 2

    def test_active_enforcement_scoped_to_feature(self, state_machine, registry):
        """Test ACTIVE enforcement is scoped to feature."""
        # Create active document in feature-a
        doc1 = registry.register_document(
            path="docs/test/feature-a-PRD.md",
            doc_type="prd",
            author="John",
            feature="feature-a",
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc1, DocumentState.ACTIVE)

        # Create active document in feature-b (different feature)
        doc2 = registry.register_document(
            path="docs/test/feature-b-PRD.md",
            doc_type="prd",
            author="Sally",
            feature="feature-b",
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc2, DocumentState.ACTIVE)

        # Both should remain active (different features)
        doc1_updated = registry.get_document(doc1.id)
        doc2_updated = registry.get_document(doc2.id)

        assert doc1_updated.state == DocumentState.ACTIVE
        assert doc2_updated.state == DocumentState.ACTIVE

    def test_active_enforcement_without_feature(self, state_machine, registry):
        """Test ACTIVE enforcement skipped if no feature."""
        doc1 = registry.register_document(
            path="docs/test/PRD-no-feature-1.md",
            doc_type="prd",
            author="John",
            feature=None,
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc1, DocumentState.ACTIVE)

        doc2 = registry.register_document(
            path="docs/test/PRD-no-feature-2.md",
            doc_type="prd",
            author="Sally",
            feature=None,
            state=DocumentState.DRAFT,
        )
        state_machine.transition(doc2, DocumentState.ACTIVE)

        # Both should remain active (no feature context)
        doc1_updated = registry.get_document(doc1.id)
        doc2_updated = registry.get_document(doc2.id)

        assert doc1_updated.state == DocumentState.ACTIVE
        assert doc2_updated.state == DocumentState.ACTIVE


# Test: Audit Trail


class TestAuditTrail:
    """Tests for audit trail functionality."""

    def test_transition_recorded_in_audit_trail(
        self, state_machine, registry, draft_document
    ):
        """Test transition is recorded in audit trail."""
        state_machine.transition(
            draft_document,
            DocumentState.ACTIVE,
            reason="Approved by team",
            changed_by="john",
        )

        history = state_machine.get_transition_history(draft_document.id)

        assert len(history) == 1
        assert history[0].document_id == draft_document.id
        assert history[0].from_state == DocumentState.DRAFT
        assert history[0].to_state == DocumentState.ACTIVE
        assert history[0].reason == "Approved by team"
        assert history[0].changed_by == "john"
        assert history[0].changed_at is not None

    def test_multiple_transitions_tracked(self, state_machine, registry, draft_document):
        """Test multiple transitions are tracked correctly."""
        # DRAFT -> ACTIVE
        state_machine.transition(
            draft_document, DocumentState.ACTIVE, reason="Approved", changed_by="john"
        )

        # ACTIVE -> OBSOLETE
        state_machine.transition(
            registry.get_document(draft_document.id),
            DocumentState.OBSOLETE,
            reason="Replaced",
            changed_by="sally",
        )

        # OBSOLETE -> ARCHIVED
        state_machine.transition(
            registry.get_document(draft_document.id),
            DocumentState.ARCHIVED,
            reason="Cleanup",
            changed_by="system",
        )

        history = state_machine.get_transition_history(draft_document.id)

        assert len(history) == 3

        # Most recent first (DESC order) - so index [0] is the last transition
        assert history[0].from_state == DocumentState.OBSOLETE
        assert history[0].to_state == DocumentState.ARCHIVED
        assert history[0].changed_by == "system"

        assert history[1].from_state == DocumentState.ACTIVE
        assert history[1].to_state == DocumentState.OBSOLETE
        assert history[1].changed_by == "sally"

        assert history[2].from_state == DocumentState.DRAFT
        assert history[2].to_state == DocumentState.ACTIVE
        assert history[2].changed_by == "john"

    def test_transition_history_ordered_by_date(
        self, state_machine, registry, draft_document
    ):
        """Test transition history ordered by date (newest first)."""
        state_machine.transition(draft_document, DocumentState.ACTIVE)

        doc = registry.get_document(draft_document.id)
        state_machine.transition(doc, DocumentState.OBSOLETE, reason="Replaced")

        history = state_machine.get_transition_history(draft_document.id)

        # Should be ordered newest first
        assert len(history) == 2
        # Parse timestamps to verify order
        time1 = datetime.fromisoformat(history[0].changed_at)
        time2 = datetime.fromisoformat(history[1].changed_at)
        assert time1 >= time2

    def test_transition_without_changed_by_defaults_to_system(
        self, state_machine, draft_document
    ):
        """Test transition without changed_by defaults to 'system'."""
        state_machine.transition(draft_document, DocumentState.ACTIVE)

        history = state_machine.get_transition_history(draft_document.id)

        assert len(history) == 1
        assert history[0].changed_by == "system"

    def test_automatic_obsolete_transition_tracked(
        self, state_machine, registry, active_document
    ):
        """Test automatic OBSOLETE transition is tracked."""
        # Create new document and activate (should obsolete the existing one)
        new_doc = registry.register_document(
            path="docs/test/new-PRD.md",
            doc_type="prd",
            author="Sally",
            feature="test-feature",
            epic=1,
            state=DocumentState.DRAFT,
        )

        state_machine.transition(new_doc, DocumentState.ACTIVE)

        # Check old document's transition history
        history = state_machine.get_transition_history(active_document.id)

        assert len(history) == 1
        assert history[0].from_state == DocumentState.ACTIVE
        assert history[0].to_state == DocumentState.OBSOLETE
        assert f"Replaced by document {new_doc.id}" in history[0].reason
        assert history[0].changed_by == "system"

    def test_empty_history_for_new_document(self, state_machine, draft_document):
        """Test empty history for document with no transitions."""
        history = state_machine.get_transition_history(draft_document.id)
        assert len(history) == 0


# Test: Hooks System


class TestHooksSystem:
    """Tests for before/after hooks system."""

    def test_before_hook_called_before_transition(self, state_machine, draft_document):
        """Test before hook is called before transition."""
        hook_called = []

        def before_hook(doc, to_state):
            hook_called.append((doc.id, doc.state, to_state))

        state_machine.register_before_hook(before_hook)
        state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert len(hook_called) == 1
        assert hook_called[0] == (
            draft_document.id,
            DocumentState.DRAFT,
            DocumentState.ACTIVE,
        )

    def test_after_hook_called_after_transition(
        self, state_machine, registry, draft_document
    ):
        """Test after hook is called after transition."""
        hook_called = []

        def after_hook(doc, from_state, to_state):
            hook_called.append((doc.id, from_state, to_state, doc.state))

        state_machine.register_after_hook(after_hook)
        state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert len(hook_called) == 1
        assert hook_called[0] == (
            draft_document.id,
            DocumentState.DRAFT,
            DocumentState.ACTIVE,
            DocumentState.ACTIVE,
        )

    def test_before_hook_can_prevent_transition(self, state_machine, draft_document):
        """Test before hook can prevent transition by raising exception."""

        def blocking_hook(doc, to_state):
            raise ValueError("Not approved yet!")

        state_machine.register_before_hook(blocking_hook)

        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert "Not approved yet!" in str(exc_info.value)

        # Document should still be DRAFT
        assert draft_document.state == DocumentState.DRAFT

    def test_multiple_before_hooks_called_in_order(self, state_machine, draft_document):
        """Test multiple before hooks called in registration order."""
        call_order = []

        def hook1(doc, to_state):
            call_order.append(1)

        def hook2(doc, to_state):
            call_order.append(2)

        def hook3(doc, to_state):
            call_order.append(3)

        state_machine.register_before_hook(hook1)
        state_machine.register_before_hook(hook2)
        state_machine.register_before_hook(hook3)

        state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert call_order == [1, 2, 3]

    def test_multiple_after_hooks_called_in_order(
        self, state_machine, registry, draft_document
    ):
        """Test multiple after hooks called in registration order."""
        call_order = []

        def hook1(doc, from_state, to_state):
            call_order.append(1)

        def hook2(doc, from_state, to_state):
            call_order.append(2)

        def hook3(doc, from_state, to_state):
            call_order.append(3)

        state_machine.register_after_hook(hook1)
        state_machine.register_after_hook(hook2)
        state_machine.register_after_hook(hook3)

        state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert call_order == [1, 2, 3]

    def test_hooks_with_complex_validation(self, state_machine, draft_document):
        """Test hook with complex validation logic."""

        def validate_approval(doc, to_state):
            if to_state == DocumentState.ACTIVE:
                if not doc.metadata.get("approved"):
                    raise ValueError("Document must be approved before activation")

        state_machine.register_before_hook(validate_approval)

        # Should fail without approval
        with pytest.raises(ValueError) as exc_info:
            state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert "approved" in str(exc_info.value).lower()

    def test_clear_hooks(self, state_machine, draft_document):
        """Test clear_hooks removes all hooks."""
        before_called = []
        after_called = []

        state_machine.register_before_hook(lambda d, t: before_called.append(1))
        state_machine.register_after_hook(lambda d, f, t: after_called.append(1))

        state_machine.clear_hooks()

        state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert len(before_called) == 0
        assert len(after_called) == 0


# Test: Utility Methods


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_get_valid_transitions(self, state_machine):
        """Test get_valid_transitions returns correct states."""
        transitions = state_machine.get_valid_transitions(DocumentState.DRAFT)
        assert DocumentState.ACTIVE in transitions
        assert DocumentState.ARCHIVED in transitions
        assert len(transitions) == 2

    def test_is_terminal_state(self, state_machine):
        """Test is_terminal_state correctly identifies terminal states."""
        assert state_machine.is_terminal_state(DocumentState.ARCHIVED)
        assert not state_machine.is_terminal_state(DocumentState.DRAFT)
        assert not state_machine.is_terminal_state(DocumentState.ACTIVE)
        assert not state_machine.is_terminal_state(DocumentState.OBSOLETE)


# Test: Integration Scenarios


class TestIntegrationScenarios:
    """Integration tests for complete lifecycle scenarios."""

    def test_complete_document_lifecycle(self, state_machine, registry):
        """Test complete document lifecycle: DRAFT -> ACTIVE -> OBSOLETE -> ARCHIVED."""
        # Create document
        doc = registry.register_document(
            path="docs/test/lifecycle-test.md",
            doc_type="prd",
            author="John",
            feature="test-feature",
            state=DocumentState.DRAFT,
        )

        # DRAFT -> ACTIVE
        doc = state_machine.transition(
            doc, DocumentState.ACTIVE, reason="Approved", changed_by="john"
        )
        assert doc.state == DocumentState.ACTIVE

        # ACTIVE -> OBSOLETE
        doc = state_machine.transition(
            doc, DocumentState.OBSOLETE, reason="Replaced", changed_by="sally"
        )
        assert doc.state == DocumentState.OBSOLETE

        # OBSOLETE -> ARCHIVED
        doc = state_machine.transition(
            doc, DocumentState.ARCHIVED, reason="Cleanup", changed_by="system"
        )
        assert doc.state == DocumentState.ARCHIVED

        # Verify complete audit trail
        history = state_machine.get_transition_history(doc.id)
        assert len(history) == 3

    def test_create_two_documents_activate_second_verify_first_obsolete(
        self, state_machine, registry
    ):
        """Test activating second document marks first as obsolete."""
        # Create and activate first document
        doc1 = registry.register_document(
            path="docs/test/PRD-v1.md",
            doc_type="prd",
            author="John",
            feature="feature-x",
            state=DocumentState.DRAFT,
        )
        doc1 = state_machine.transition(doc1, DocumentState.ACTIVE)

        # Create and activate second document
        doc2 = registry.register_document(
            path="docs/test/PRD-v2.md",
            doc_type="prd",
            author="Sally",
            feature="feature-x",
            state=DocumentState.DRAFT,
        )
        doc2 = state_machine.transition(doc2, DocumentState.ACTIVE)

        # Verify first is obsolete
        doc1_updated = registry.get_document(doc1.id)
        assert doc1_updated.state == DocumentState.OBSOLETE

        # Verify second is active
        assert doc2.state == DocumentState.ACTIVE

        # Verify both have audit trails
        history1 = state_machine.get_transition_history(doc1.id)
        history2 = state_machine.get_transition_history(doc2.id)

        assert len(history1) == 2  # DRAFT->ACTIVE, ACTIVE->OBSOLETE
        assert len(history2) == 1  # DRAFT->ACTIVE

    def test_verify_audit_trail_complete_after_multiple_transitions(
        self, state_machine, registry
    ):
        """Test audit trail is complete after multiple transitions."""
        doc = registry.register_document(
            path="docs/test/audit-test.md",
            doc_type="prd",
            author="John",
            feature="test-feature",
            state=DocumentState.DRAFT,
        )

        # Perform multiple transitions
        state_machine.transition(doc, DocumentState.ACTIVE, changed_by="john")
        doc = registry.get_document(doc.id)
        state_machine.transition(
            doc, DocumentState.OBSOLETE, reason="Replaced", changed_by="sally"
        )
        doc = registry.get_document(doc.id)
        state_machine.transition(
            doc, DocumentState.ARCHIVED, reason="Cleanup", changed_by="system"
        )

        # Verify complete audit trail
        history = state_machine.get_transition_history(doc.id)

        assert len(history) == 3

        # Verify each transition
        assert history[2].from_state == DocumentState.DRAFT
        assert history[2].to_state == DocumentState.ACTIVE

        assert history[1].from_state == DocumentState.ACTIVE
        assert history[1].to_state == DocumentState.OBSOLETE

        assert history[0].from_state == DocumentState.OBSOLETE
        assert history[0].to_state == DocumentState.ARCHIVED


# Test: Edge Cases


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_transition_same_state_to_same_state(self, state_machine, draft_document):
        """Test transitioning to same state (should fail)."""
        with pytest.raises(InvalidStateTransition):
            state_machine.transition(draft_document, DocumentState.DRAFT)

    def test_transition_with_very_long_reason(self, state_machine, active_document):
        """Test transition with very long reason string."""
        long_reason = "A" * 10000  # 10KB reason
        doc = state_machine.transition(
            active_document, DocumentState.OBSOLETE, reason=long_reason
        )

        history = state_machine.get_transition_history(doc.id)
        assert history[0].reason == long_reason

    def test_hook_exception_propagates(self, state_machine, draft_document):
        """Test exception in hook propagates correctly."""

        def failing_hook(doc, to_state):
            raise RuntimeError("Hook failure")

        state_machine.register_before_hook(failing_hook)

        with pytest.raises(RuntimeError) as exc_info:
            state_machine.transition(draft_document, DocumentState.ACTIVE)

        assert "Hook failure" in str(exc_info.value)
