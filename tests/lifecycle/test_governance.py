"""
Unit Tests for DocumentGovernance.

This module provides comprehensive unit tests for the DocumentGovernance class,
covering ownership management, review cycle tracking, governance rules, and reporting.
"""

import tempfile
import yaml
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.governance import DocumentGovernance, DocumentReview
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType
from gao_dev.lifecycle.exceptions import (
    DocumentNotFoundError,
    ValidationError,
)


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
def temp_archive_dir():
    """Create temporary archive directory."""
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir

    # Cleanup
    import shutil

    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_governance_config():
    """Create temporary governance configuration file."""
    config = {
        "document_governance": {
            "ownership": {
                "prd": {
                    "created_by": "John",
                    "approved_by": "Mary",
                    "reviewed_by": "Winston",
                    "informed": ["Team"],
                },
                "architecture": {
                    "created_by": "Winston",
                    "approved_by": "Mary",
                    "reviewed_by": "John",
                    "informed": ["Team"],
                },
                "story": {
                    "created_by": "Bob",
                    "approved_by": "John",
                    "reviewed_by": "Amelia",
                    "informed": ["Team"],
                },
                "adr": {
                    "created_by": "Winston",
                    "approved_by": "Mary",
                    "reviewed_by": "Amelia",
                    "informed": ["Team", "Stakeholders"],
                },
            },
            "review_cadence": {
                "prd": 90,
                "architecture": 60,
                "story": 30,
                "epic": 60,
                "adr": -1,  # Never review (immutable)
                "postmortem": 365,
            },
            "permissions": {
                "archive": {"allowed_roles": ["owner", "engineering_manager"]},
                "delete": {
                    "allowed_roles": ["engineering_manager"],
                    "requires_confirmation": True,
                },
                "transition_to_active": {"allowed_roles": ["owner", "approver"]},
                "mark_reviewed": {"allowed_roles": ["owner", "reviewer", "engineering_manager"]},
            },
            "rules": {
                "require_owner_on_creation": True,
                "flag_unowned_documents": True,
                "auto_assign_ownership": True,
                "enable_review_notifications": False,
                "review_reminder_days": 7,
                "escalate_overdue_after_days": 14,
            },
            "priority_mapping": {
                "P0": 1,
                "P1": 2,
                "P2": 3,
                "P3": 4,
                "default": 5,
            },
        }
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.dump(config, f)
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def registry(temp_db):
    """Create DocumentRegistry instance for testing."""
    reg = DocumentRegistry(temp_db)
    yield reg
    reg.close()


@pytest.fixture
def doc_manager(registry, temp_archive_dir):
    """Create DocumentLifecycleManager instance for testing."""
    return DocumentLifecycleManager(registry, temp_archive_dir)


@pytest.fixture
def governance(doc_manager, temp_governance_config):
    """Create DocumentGovernance instance for testing."""
    return DocumentGovernance(doc_manager, temp_governance_config)


@pytest.fixture
def sample_doc(registry):
    """Create a sample document for testing."""
    return registry.register_document(
        path="docs/features/test/PRD.md",
        doc_type="prd",
        author="John",
        feature="test-feature",
        epic=1,
        metadata={"tags": ["test"], "priority": "P1"},
    )


# Config Loading Tests


class TestConfigLoading:
    """Tests for governance configuration loading."""

    def test_load_valid_config(self, governance):
        """Test loading valid governance configuration."""
        assert "document_governance" in governance.config
        assert "ownership" in governance.config["document_governance"]
        assert "review_cadence" in governance.config["document_governance"]

    def test_load_missing_config_raises_error(self, doc_manager):
        """Test loading non-existent config file raises error."""
        with pytest.raises(FileNotFoundError):
            DocumentGovernance(doc_manager, Path("/nonexistent/governance.yaml"))

    def test_load_invalid_yaml_raises_error(self, doc_manager):
        """Test loading invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("invalid: yaml: content: [[[")
            invalid_path = Path(f.name)

        try:
            with pytest.raises(ValidationError):
                DocumentGovernance(doc_manager, invalid_path)
        finally:
            invalid_path.unlink()


# Ownership Management Tests


class TestOwnershipManagement:
    """Tests for ownership assignment and management."""

    def test_assign_owner(self, governance, sample_doc):
        """Test assigning document owner."""
        governance.assign_owner(sample_doc.id, "Mary")

        doc = governance.doc_mgr.registry.get_document(sample_doc.id)
        assert doc.owner == "Mary"

    def test_assign_reviewer(self, governance, sample_doc):
        """Test assigning document reviewer."""
        governance.assign_reviewer(sample_doc.id, "Winston")

        doc = governance.doc_mgr.registry.get_document(sample_doc.id)
        assert doc.reviewer == "Winston"

    def test_assign_owner_to_nonexistent_doc_raises_error(self, governance):
        """Test assigning owner to non-existent document raises error."""
        with pytest.raises(DocumentNotFoundError):
            governance.assign_owner(99999, "Mary")

    def test_auto_assign_ownership_for_prd(self, governance, registry):
        """Test auto-assignment of ownership based on RACI matrix for PRD."""
        doc = registry.register_document(
            path="docs/test/PRD.md",
            doc_type="prd",
            author="John",
            feature="test",
        )

        governance.auto_assign_ownership(doc)

        updated_doc = registry.get_document(doc.id)
        assert updated_doc.owner == "Mary"  # approved_by in RACI
        assert updated_doc.reviewer == "Winston"  # reviewed_by in RACI
        assert updated_doc.review_due_date is not None

    def test_auto_assign_ownership_for_adr_no_review_date(self, governance, registry):
        """Test auto-assignment for ADR (immutable) does not set review date."""
        doc = registry.register_document(
            path="docs/test/ADR.md",
            doc_type="adr",
            author="Winston",
            feature="test",
        )

        governance.auto_assign_ownership(doc)

        updated_doc = registry.get_document(doc.id)
        assert updated_doc.owner == "Mary"
        assert updated_doc.reviewer == "Amelia"
        assert updated_doc.review_due_date is None  # No review for ADRs

    def test_get_owned_documents(self, governance, registry):
        """Test retrieving documents owned by a specific person."""
        # Create multiple documents with different owners
        doc1 = registry.register_document(
            path="docs/test1.md", doc_type="prd", author="John", owner="Mary"
        )
        doc2 = registry.register_document(
            path="docs/test2.md", doc_type="story", author="Bob", owner="Mary"
        )
        doc3 = registry.register_document(
            path="docs/test3.md", doc_type="epic", author="Bob", owner="John"
        )

        mary_docs = governance.get_owned_documents("Mary")
        assert len(mary_docs) == 2
        assert all(d.owner == "Mary" for d in mary_docs)

    def test_get_review_queue(self, governance, registry):
        """Test retrieving review queue for a specific reviewer."""
        # Create document with review due soon
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John", reviewer="Winston"
        )

        # Set review due date to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=yesterday)

        queue = governance.get_review_queue("Winston")
        assert len(queue) == 1
        assert queue[0].id == doc.id

    def test_get_unowned_documents(self, governance, registry):
        """Test retrieving documents without owners."""
        doc1 = registry.register_document(
            path="docs/test1.md", doc_type="prd", author="John", owner="Mary"
        )
        doc2 = registry.register_document(
            path="docs/test2.md", doc_type="story", author="Bob"
        )

        unowned = governance.get_unowned_documents()
        assert len(unowned) == 1
        assert unowned[0].id == doc2.id


# Review Cycle Tests


class TestReviewCycle:
    """Tests for review cycle tracking."""

    def test_check_review_due_returns_overdue_docs(self, governance, registry):
        """Test checking for overdue reviews."""
        # Create document with overdue review
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John", owner="Mary"
        )

        # Set review due date to last week
        last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=last_week)

        overdue = governance.check_review_due(include_overdue_only=True)
        assert len(overdue) == 1
        assert overdue[0].id == doc.id

    def test_check_review_due_with_owner_filter(self, governance, registry):
        """Test checking reviews due with owner filter."""
        doc1 = registry.register_document(
            path="docs/test1.md", doc_type="prd", author="John", owner="Mary"
        )
        doc2 = registry.register_document(
            path="docs/test2.md", doc_type="story", author="Bob", owner="John"
        )

        # Set both to overdue
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc1.id, review_due_date=yesterday)
        registry.update_document(doc2.id, review_due_date=yesterday)

        mary_overdue = governance.check_review_due(owner="Mary", include_overdue_only=True)
        assert len(mary_overdue) == 1
        assert mary_overdue[0].id == doc1.id

    def test_mark_reviewed_creates_review_record(self, governance, sample_doc):
        """Test marking document as reviewed creates review record."""
        review = governance.mark_reviewed(sample_doc.id, "Winston", "Looks good!")

        assert review.id is not None
        assert review.document_id == sample_doc.id
        assert review.reviewer == "Winston"
        assert review.notes == "Looks good!"
        assert review.next_review_due is not None

    def test_mark_reviewed_updates_review_due_date(self, governance, sample_doc):
        """Test marking as reviewed updates next review due date."""
        # Set initial review due date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        governance.doc_mgr.registry.update_document(
            sample_doc.id, review_due_date=yesterday
        )

        governance.mark_reviewed(sample_doc.id, "Winston")

        # Check that review due date is updated to 90 days from now (PRD cadence)
        updated_doc = governance.doc_mgr.registry.get_document(sample_doc.id)
        assert updated_doc.review_due_date is not None

        due_date = datetime.strptime(updated_doc.review_due_date, "%Y-%m-%d").date()
        expected_date = (datetime.now() + timedelta(days=90)).date()

        # Allow 1 day difference for timing
        assert abs((due_date - expected_date).days) <= 1

    def test_mark_reviewed_for_immutable_doc_no_next_review(self, governance, registry):
        """Test marking immutable document (ADR) as reviewed has no next review."""
        doc = registry.register_document(
            path="docs/test-adr.md", doc_type="adr", author="Winston"
        )

        review = governance.mark_reviewed(doc.id, "Mary", "Approved")

        assert review.next_review_due is None

    def test_get_review_history(self, governance, sample_doc):
        """Test retrieving review history for a document."""
        import time

        # Add multiple reviews with small delay to ensure different timestamps
        governance.mark_reviewed(sample_doc.id, "Winston", "First review")
        time.sleep(0.1)  # Ensure different timestamp
        governance.mark_reviewed(sample_doc.id, "Mary", "Second review")

        history = governance.get_review_history(sample_doc.id)

        assert len(history) == 2
        assert history[0].notes == "Second review"  # Most recent first
        assert history[1].notes == "First review"

    def test_get_review_history_for_nonexistent_doc_raises_error(self, governance):
        """Test getting review history for non-existent document raises error."""
        with pytest.raises(DocumentNotFoundError):
            governance.get_review_history(99999)


# Governance Report Tests


class TestGovernanceReporting:
    """Tests for governance report generation."""

    def test_generate_markdown_report(self, governance, registry):
        """Test generating governance report in markdown format."""
        # Create documents with various states
        doc1 = registry.register_document(
            path="docs/test1.md", doc_type="prd", author="John", owner="Mary"
        )
        doc2 = registry.register_document(
            path="docs/test2.md", doc_type="story", author="Bob"
        )

        # Set one overdue
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc1.id, review_due_date=yesterday)

        report = governance.generate_governance_report(format="markdown")

        assert "# Document Governance Report" in report
        assert "## Review Status" in report
        assert "### Overdue Reviews" in report
        assert "### Documents Without Owners" in report
        assert doc2.path in report  # Unowned document

    def test_generate_csv_report(self, governance, registry):
        """Test generating governance report in CSV format."""
        doc = registry.register_document(
            path="docs/test.md",
            doc_type="prd",
            author="John",
            owner="Mary",
            reviewer="Winston",
        )

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=yesterday)

        report = governance.generate_governance_report(format="csv")

        # Check CSV headers
        assert "Document Path" in report
        assert "Type" in report
        assert "Owner" in report
        assert "Days Overdue" in report

        # Check document data
        assert "docs/test.md" in report
        assert "Mary" in report
        assert "Winston" in report

    def test_generate_report_invalid_format_raises_error(self, governance):
        """Test generating report with invalid format raises error."""
        with pytest.raises(ValueError):
            governance.generate_governance_report(format="json")


# Permission Tests


class TestPermissions:
    """Tests for governance permission checks."""

    def test_can_archive_owner_allowed(self, governance, sample_doc):
        """Test that owner can archive documents."""
        assert governance.can_archive(sample_doc.id, "owner") is True

    def test_can_archive_engineering_manager_allowed(self, governance, sample_doc):
        """Test that engineering manager can archive documents."""
        assert governance.can_archive(sample_doc.id, "engineering_manager") is True

    def test_can_archive_other_roles_not_allowed(self, governance, sample_doc):
        """Test that other roles cannot archive documents."""
        assert governance.can_archive(sample_doc.id, "developer") is False

    def test_can_delete_engineering_manager_only(self, governance, sample_doc):
        """Test that only engineering manager can delete documents."""
        assert governance.can_delete(sample_doc.id, "engineering_manager") is True
        assert governance.can_delete(sample_doc.id, "owner") is False
        assert governance.can_delete(sample_doc.id, "developer") is False


# Helper Method Tests


class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_is_overdue_with_past_date(self, governance, registry):
        """Test _is_overdue returns True for past dates."""
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=yesterday)

        updated_doc = registry.get_document(doc.id)
        assert governance._is_overdue(updated_doc) is True

    def test_is_overdue_with_future_date(self, governance, registry):
        """Test _is_overdue returns False for future dates."""
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=tomorrow)

        updated_doc = registry.get_document(doc.id)
        assert governance._is_overdue(updated_doc) is False

    def test_days_overdue_calculation(self, governance, registry):
        """Test _days_overdue calculates correctly."""
        doc = registry.register_document(
            path="docs/test.md", doc_type="prd", author="John"
        )

        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        registry.update_document(doc.id, review_due_date=week_ago)

        updated_doc = registry.get_document(doc.id)
        days = governance._days_overdue(updated_doc)

        assert days == 7

    def test_get_priority_value(self, governance, registry):
        """Test _get_priority_value returns correct numeric priority."""
        doc1 = registry.register_document(
            path="docs/test1.md",
            doc_type="prd",
            author="John",
            metadata={"priority": "P0"},
        )
        doc2 = registry.register_document(
            path="docs/test2.md",
            doc_type="story",
            author="Bob",
            metadata={"priority": "P3"},
        )

        assert governance._get_priority_value(doc1) == 1
        assert governance._get_priority_value(doc2) == 4


# Integration Tests


class TestGovernanceIntegration:
    """Integration tests for complete governance workflows."""

    def test_complete_document_lifecycle_with_governance(self, governance, registry):
        """Test complete document lifecycle with governance tracking."""
        # 1. Register document
        doc = registry.register_document(
            path="docs/integration/PRD.md", doc_type="prd", author="John", feature="test"
        )

        # 2. Auto-assign ownership
        governance.auto_assign_ownership(doc)

        updated_doc = registry.get_document(doc.id)
        assert updated_doc.owner == "Mary"
        assert updated_doc.reviewer == "Winston"
        assert updated_doc.review_due_date is not None

        # 3. Mark as reviewed
        review1 = governance.mark_reviewed(doc.id, "Winston", "Initial review complete")
        assert review1.id is not None

        # 4. Check review history
        history = governance.get_review_history(doc.id)
        assert len(history) == 1

        # 5. Check not in overdue list
        overdue = governance.check_review_due(include_overdue_only=True)
        assert doc.id not in [d.id for d in overdue]

    def test_governance_report_with_multiple_documents(self, governance, registry):
        """Test governance report with multiple documents in various states."""
        # Create documents
        doc1 = registry.register_document(
            path="docs/test1.md",
            doc_type="prd",
            author="John",
            owner="Mary",
            metadata={"priority": "P0"},
        )
        doc2 = registry.register_document(
            path="docs/test2.md", doc_type="story", author="Bob"
        )
        doc3 = registry.register_document(
            path="docs/test3.md",
            doc_type="architecture",
            author="Winston",
            owner="Mary",
            reviewer="John",
        )

        # Set review dates
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        registry.update_document(doc1.id, review_due_date=yesterday)  # Overdue
        registry.update_document(doc3.id, review_due_date=next_week)  # Due soon

        # Mark one as reviewed
        governance.mark_reviewed(doc3.id, "John", "Architecture looks good")

        # Generate report
        report = governance.generate_governance_report(format="markdown")

        assert "1" in report  # 1 overdue
        assert "Documents Without Owners" in report
        assert doc2.path in report  # Unowned document listed
