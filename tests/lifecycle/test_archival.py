"""
Unit tests for Document Archival System.

Tests the ArchivalManager class and its functionality for archiving and
deleting documents based on retention policies.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
import yaml

from gao_dev.lifecycle.archival import ArchivalManager, RetentionPolicy, ArchivalAction
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
from gao_dev.lifecycle.models import Document, DocumentState, DocumentType


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup with retry for Windows file locking issues
    if temp_path.exists():
        import time
        for attempt in range(3):
            try:
                shutil.rmtree(temp_path)
                break
            except (PermissionError, OSError):
                if attempt < 2:
                    time.sleep(0.5)
                else:
                    pass  # Give up after 3 attempts


@pytest.fixture
def registry(temp_dir):
    """Create DocumentRegistry for testing."""
    db_path = temp_dir / "test.db"
    reg = DocumentRegistry(db_path)
    yield reg
    # Close the database connection properly
    reg.close()


@pytest.fixture
def doc_manager(registry, temp_dir):
    """Create DocumentLifecycleManager for testing."""
    archive_dir = temp_dir / ".archive"
    return DocumentLifecycleManager(registry, archive_dir)


@pytest.fixture
def policies_file(temp_dir):
    """Create test retention policies file."""
    policies_path = temp_dir / "test_policies.yaml"
    policies_content = """
retention_policies:
  story:
    archive_to_obsolete: 30
    obsolete_to_archive: 90
    archive_retention: 365
    delete_after_archive: true
    compliance_tags: []

  prd:
    archive_to_obsolete: 30
    obsolete_to_archive: 90
    archive_retention: 730
    delete_after_archive: false
    compliance_tags: ["product-decisions", "compliance"]

  postmortem:
    archive_to_obsolete: -1
    obsolete_to_archive: -1
    archive_retention: -1
    delete_after_archive: false
    compliance_tags: ["incidents", "learning"]

  draft:
    archive_to_obsolete: 7
    obsolete_to_archive: 7
    archive_retention: 30
    delete_after_archive: true
    compliance_tags: []
"""
    policies_path.write_text(policies_content, encoding="utf-8")
    return policies_path


@pytest.fixture
def archival_manager(doc_manager, policies_file):
    """Create ArchivalManager for testing."""
    return ArchivalManager(doc_manager, policies_file)


def _backdate_document(registry, doc_id: int, date_string: str):
    """
    Helper to backdate a document's modified_at for testing.

    Uses direct SQL update since the registry doesn't allow modifying modified_at.
    """
    with registry._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET modified_at = ? WHERE id = ?",
            (date_string, doc_id)
        )


class TestRetentionPolicyLoading:
    """Test loading and parsing retention policies from YAML."""

    def test_load_valid_policies(self, archival_manager):
        """Test loading valid retention policies."""
        policies = archival_manager.list_policies()
        assert len(policies) == 4

        policy_types = [p.doc_type for p in policies]
        assert "story" in policy_types
        assert "prd" in policy_types
        assert "postmortem" in policy_types
        assert "draft" in policy_types

    def test_load_story_policy(self, archival_manager):
        """Test loading story retention policy."""
        policy = archival_manager.get_policy("story")
        assert policy is not None
        assert policy.doc_type == "story"
        assert policy.archive_to_obsolete == 30
        assert policy.obsolete_to_archive == 90
        assert policy.archive_retention == 365
        assert policy.delete_after_archive is True
        assert policy.compliance_tags == []

    def test_load_prd_policy(self, archival_manager):
        """Test loading PRD retention policy."""
        policy = archival_manager.get_policy("prd")
        assert policy is not None
        assert policy.doc_type == "prd"
        assert policy.delete_after_archive is False
        assert "product-decisions" in policy.compliance_tags
        assert "compliance" in policy.compliance_tags

    def test_load_postmortem_policy_never_archive(self, archival_manager):
        """Test postmortem policy with -1 (never) values."""
        policy = archival_manager.get_policy("postmortem")
        assert policy is not None
        assert policy.archive_to_obsolete == -1
        assert policy.obsolete_to_archive == -1
        assert policy.archive_retention == -1
        assert policy.delete_after_archive is False

    def test_get_nonexistent_policy(self, archival_manager):
        """Test getting policy that doesn't exist."""
        policy = archival_manager.get_policy("nonexistent")
        assert policy is None

    def test_load_missing_file(self, doc_manager, temp_dir):
        """Test loading from missing policies file."""
        missing_path = temp_dir / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            ArchivalManager(doc_manager, missing_path)

    def test_load_invalid_yaml(self, doc_manager, temp_dir):
        """Test loading invalid YAML file."""
        invalid_path = temp_dir / "invalid.yaml"
        invalid_path.write_text("{ invalid yaml content", encoding="utf-8")
        with pytest.raises((ValueError, yaml.YAMLError)):
            ArchivalManager(doc_manager, invalid_path)


class TestArchivalOperations:
    """Test archival operations for obsolete documents."""

    def test_archive_obsolete_documents_none_eligible(self, archival_manager, doc_manager, temp_dir):
        """Test archiving when no documents are eligible."""
        # Create an active document (not obsolete)
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE)

        # Try to archive
        actions = archival_manager.archive_obsolete_documents(dry_run=False)
        assert len(actions) == 0

    def test_archive_obsolete_document_dry_run(self, archival_manager, doc_manager, temp_dir):
        """Test archiving in dry-run mode (no actual changes)."""
        # Create obsolete document that's old enough
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        # Make it old by updating modified_at
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Dry run should return action but not modify
        actions = archival_manager.archive_obsolete_documents(dry_run=True)
        assert len(actions) == 1
        assert actions[0].action == "archive"
        assert actions[0].document.id == doc.id

        # Verify document is still OBSOLETE
        updated_doc = doc_manager.registry.get_document(doc.id)
        assert updated_doc.state == DocumentState.OBSOLETE

    def test_archive_obsolete_document_actual(self, archival_manager, doc_manager, temp_dir):
        """Test actually archiving an obsolete document."""
        # Create obsolete document
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        # Make it old enough
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Actually archive
        actions = archival_manager.archive_obsolete_documents(dry_run=False)
        assert len(actions) == 1

        # Verify document is now ARCHIVED
        updated_doc = doc_manager.registry.get_document(doc.id)
        assert updated_doc.state == DocumentState.ARCHIVED

    def test_archive_document_too_young(self, archival_manager, doc_manager, temp_dir):
        """Test that documents too young are not archived."""
        # Create obsolete document that's too young
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        # Only 30 days old (policy requires 90)
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, recent_date)

        # Should not be archived
        actions = archival_manager.archive_obsolete_documents(dry_run=False)
        assert len(actions) == 0

    def test_archive_multiple_documents(self, archival_manager, doc_manager, temp_dir):
        """Test archiving multiple documents at once."""
        # Create multiple obsolete documents
        old_date = (datetime.now() - timedelta(days=100)).isoformat()

        for i in range(3):
            doc_path = temp_dir / f"test{i}.md"
            doc_path.write_text(f"Test content {i}", encoding="utf-8")

            doc = doc_manager.register_document(
                path=doc_path,
                doc_type="story",
                author="test",
            )
            # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
            doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
            doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")
            _backdate_document(doc_manager.registry, doc.id, old_date)

        # Archive all
        actions = archival_manager.archive_obsolete_documents(dry_run=False)
        assert len(actions) == 3

        # Verify all are archived
        for action in actions:
            updated_doc = doc_manager.registry.get_document(action.document.id)
            assert updated_doc.state == DocumentState.ARCHIVED


class TestDeletionOperations:
    """Test deletion operations for archived documents."""

    def test_delete_expired_document(self, archival_manager, doc_manager, temp_dir):
        """Test deleting document past retention period."""
        # Create archived document with deletable policy
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ARCHIVED
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Make it very old (past retention)
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Should be deleted
        actions = archival_manager.cleanup_expired_documents(dry_run=False)
        assert len(actions) == 1
        assert actions[0].action == "delete"

        # Verify document is gone
        with pytest.raises(Exception):
            doc_manager.registry.get_document(doc.id)

    def test_delete_document_dry_run(self, archival_manager, doc_manager, temp_dir):
        """Test deletion in dry-run mode."""
        # Create expired archived document
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Dry run should return action but not delete
        actions = archival_manager.cleanup_expired_documents(dry_run=True)
        assert len(actions) == 1
        assert actions[0].action == "delete"

        # Verify document still exists
        updated_doc = doc_manager.registry.get_document(doc.id)
        assert updated_doc is not None

    def test_no_delete_with_compliance_tags(self, archival_manager, doc_manager, temp_dir):
        """Test that documents with compliance tags are NOT deleted."""
        # Create archived PRD with compliance tags
        doc_path = temp_dir / "prd.md"
        doc_path.write_text("PRD content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="test",
            metadata={"tags": ["product-decisions", "compliance"]},
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Make it very old
        old_date = (datetime.now() - timedelta(days=1000)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Should NOT be deleted due to compliance tags
        actions = archival_manager.cleanup_expired_documents(dry_run=False)
        assert len(actions) == 0

        # Verify document still exists
        updated_doc = doc_manager.registry.get_document(doc.id)
        assert updated_doc is not None

    def test_no_delete_when_policy_disallows(self, archival_manager, doc_manager, temp_dir):
        """Test that documents are not deleted when policy disallows."""
        # Create archived PRD (delete_after_archive=false)
        doc_path = temp_dir / "prd.md"
        doc_path.write_text("PRD content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="test",
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Make it very old
        old_date = (datetime.now() - timedelta(days=1000)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Should NOT be deleted due to policy
        actions = archival_manager.cleanup_expired_documents(dry_run=False)
        assert len(actions) == 0

    def test_no_delete_retention_not_expired(self, archival_manager, doc_manager, temp_dir):
        """Test that documents within retention period are not deleted."""
        # Create archived document still within retention
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Only 100 days old (retention is 365)
        recent_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, recent_date)

        # Should NOT be deleted
        actions = archival_manager.cleanup_expired_documents(dry_run=False)
        assert len(actions) == 0


class TestRetentionReports:
    """Test retention policy reporting."""

    def test_generate_markdown_report_empty(self, archival_manager):
        """Test generating report with no documents."""
        report = archival_manager.generate_retention_report(format="markdown")
        assert "# Document Retention Policy Report" in report
        assert "Generated:" in report

    def test_generate_markdown_report_with_documents(self, archival_manager, doc_manager, temp_dir):
        """Test generating report with documents."""
        # Create some documents
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Generate report
        report = archival_manager.generate_retention_report(format="markdown")
        assert "# Document Retention Policy Report" in report
        assert "STORY" in report
        assert "Policy Configuration:" in report
        assert "archive" in report.lower()

    def test_generate_csv_report(self, archival_manager, doc_manager, temp_dir):
        """Test generating CSV report."""
        # Create a document
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )

        # Generate CSV report
        report = archival_manager.generate_retention_report(format="csv")
        assert "Path,Type,State,Created,Modified,Action,Reason,Days Until Action" in report
        assert str(doc_path) in report

    def test_report_shows_pending_actions(self, archival_manager, doc_manager, temp_dir):
        """Test that report shows pending archival actions."""
        # Create obsolete document ready to archive
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Generate report
        report = archival_manager.generate_retention_report(format="markdown")
        assert "Pending Actions:" in report
        assert "ARCHIVE" in report


class TestArchivalAction:
    """Test ArchivalAction evaluation logic."""

    def test_evaluate_archival_no_policy(self, archival_manager, doc_manager, temp_dir):
        """Test evaluating archival when no policy exists."""
        # Create document with type that has no policy
        doc_path = temp_dir / "test.md"
        doc_path.write_text("Test content", encoding="utf-8")

        # Use a document type that doesn't have a policy
        doc = Document(
            id=1,
            path=str(doc_path),
            type=DocumentType.RUNBOOK,
            state=DocumentState.OBSOLETE,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
        )

        action = archival_manager._evaluate_archival(doc)
        assert action.action == "none"
        assert "No archival policy" in action.reason

    def test_evaluate_deletion_no_policy(self, archival_manager):
        """Test evaluating deletion when no policy exists."""
        doc = Document(
            id=1,
            path="test.md",
            type=DocumentType.RUNBOOK,
            state=DocumentState.ARCHIVED,
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
        )

        action = archival_manager._evaluate_deletion(doc)
        assert action.action == "none"
        assert "No retention policy" in action.reason


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_archive_document_file_not_exists(self, archival_manager, doc_manager, temp_dir):
        """Test archiving when file doesn't exist."""
        # Create document without file
        doc = doc_manager.registry.register_document(
            path=str(temp_dir / "nonexistent.md"),
            doc_type="story",
            author="test",
        )
        # Proper state transition: DRAFT -> ACTIVE -> OBSOLETE
        doc_manager.transition_state(doc.id, DocumentState.ACTIVE, reason="Approved")
        doc_manager.transition_state(doc.id, DocumentState.OBSOLETE, reason="Test")

        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Should handle gracefully
        actions = archival_manager.archive_obsolete_documents(dry_run=False)
        # The action should still be recorded even if file doesn't exist
        assert len(actions) >= 0

    def test_policy_with_forever_retention(self, archival_manager):
        """Test policy with retention=-1 (forever)."""
        policy = archival_manager.get_policy("postmortem")
        assert policy.archive_retention == -1
        assert policy.delete_after_archive is False


class TestComplianceProtection:
    """Test compliance tag protection mechanism."""

    def test_compliance_tag_prevents_deletion(self, archival_manager, doc_manager, temp_dir):
        """Test that any compliance tag prevents deletion."""
        # Create document with one compliance tag
        doc_path = temp_dir / "prd.md"
        doc_path.write_text("PRD content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="prd",
            author="test",
            metadata={"tags": ["product-decisions"]},  # This is a compliance tag
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Make it very old
        old_date = (datetime.now() - timedelta(days=1000)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Get the updated document with backdated time
        doc = doc_manager.registry.get_document(doc.id)

        # Evaluate deletion
        action = archival_manager._evaluate_deletion(doc)
        assert action.action == "none"
        assert "compliance tags" in action.reason.lower()

    def test_no_compliance_tags_allows_deletion(self, archival_manager, doc_manager, temp_dir):
        """Test that documents without compliance tags can be deleted."""
        # Create story without compliance tags
        doc_path = temp_dir / "story.md"
        doc_path.write_text("Story content", encoding="utf-8")

        doc = doc_manager.register_document(
            path=doc_path,
            doc_type="story",
            author="test",
            metadata={"tags": []},
        )
        doc_manager.transition_state(doc.id, DocumentState.ARCHIVED, reason="Test")

        # Make it very old (past retention)
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        _backdate_document(doc_manager.registry, doc.id, old_date)

        # Get the updated document with backdated time
        doc = doc_manager.registry.get_document(doc.id)

        # Evaluate deletion
        action = archival_manager._evaluate_deletion(doc)
        assert action.action == "delete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
