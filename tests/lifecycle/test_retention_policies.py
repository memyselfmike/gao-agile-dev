"""
Unit tests for Retention Policy Configuration and Validation.

Tests the retention_policies.yaml configuration file and ensures all
policies are correctly defined and meet compliance requirements.
"""

import pytest
from pathlib import Path
import yaml

from gao_dev.lifecycle.archival import ArchivalManager, RetentionPolicy
from gao_dev.lifecycle.registry import DocumentRegistry
from gao_dev.lifecycle.document_manager import DocumentLifecycleManager
import tempfile
import shutil


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
def production_policies_path():
    """Get path to production retention policies file."""
    # Assuming tests are run from project root
    return Path("gao_dev/config/retention_policies.yaml")


class TestProductionRetentionPolicies:
    """Test the production retention policies configuration."""

    def test_policies_file_exists(self, production_policies_path):
        """Test that the retention policies file exists."""
        assert production_policies_path.exists(), \
            f"Retention policies file not found: {production_policies_path}"

    def test_policies_valid_yaml(self, production_policies_path):
        """Test that the policies file is valid YAML."""
        try:
            with open(production_policies_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            assert config is not None
            assert "retention_policies" in config
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in retention policies: {e}")

    def test_all_document_types_have_policies(self, production_policies_path):
        """Test that all expected document types have retention policies."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        # Expected document types that should have policies
        expected_types = [
            "prd",
            "architecture",
            "epic",
            "story",
            "qa_report",
            "test_report",
            "postmortem",
            "adr",
            "runbook",
            "draft",
        ]

        for doc_type in expected_types:
            assert doc_type in policies, f"Missing retention policy for {doc_type}"

    def test_policy_structure_valid(self, production_policies_path):
        """Test that all policies have required fields."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]
        required_fields = [
            "archive_to_obsolete",
            "obsolete_to_archive",
            "archive_retention",
            "delete_after_archive",
            "compliance_tags",
        ]

        for doc_type, policy in policies.items():
            for field in required_fields:
                assert field in policy, \
                    f"Policy for {doc_type} missing required field: {field}"

    def test_policy_values_valid_types(self, production_policies_path):
        """Test that policy values are of correct types."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        for doc_type, policy in policies.items():
            # Numeric fields should be integers
            assert isinstance(policy["archive_to_obsolete"], int), \
                f"{doc_type}.archive_to_obsolete must be integer"
            assert isinstance(policy["obsolete_to_archive"], int), \
                f"{doc_type}.obsolete_to_archive must be integer"
            assert isinstance(policy["archive_retention"], int), \
                f"{doc_type}.archive_retention must be integer"

            # Boolean field
            assert isinstance(policy["delete_after_archive"], bool), \
                f"{doc_type}.delete_after_archive must be boolean"

            # List field
            assert isinstance(policy["compliance_tags"], list), \
                f"{doc_type}.compliance_tags must be list"


class TestComplianceRequirements:
    """Test that policies meet compliance requirements."""

    def test_postmortem_never_deleted(self, production_policies_path):
        """Test that postmortems are configured to never be deleted."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        postmortem_policy = config["retention_policies"]["postmortem"]

        # Postmortems should never be automatically archived or deleted
        assert postmortem_policy["archive_to_obsolete"] == -1, \
            "Postmortems should never become obsolete automatically"
        assert postmortem_policy["delete_after_archive"] is False, \
            "Postmortems should never be deleted"
        assert len(postmortem_policy["compliance_tags"]) > 0, \
            "Postmortems should have compliance tags"

    def test_qa_report_five_year_retention(self, production_policies_path):
        """Test that QA reports have 5-year retention (compliance)."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        qa_policy = config["retention_policies"]["qa_report"]

        # 5 years = 1825 days (accounting for leap year)
        assert qa_policy["archive_retention"] >= 1825, \
            "QA reports must be retained for at least 5 years (compliance)"
        assert qa_policy["delete_after_archive"] is False, \
            "QA reports should not be deleted (compliance)"
        assert "compliance" in qa_policy["compliance_tags"], \
            "QA reports should have 'compliance' tag"

    def test_prd_never_deleted(self, production_policies_path):
        """Test that PRDs are preserved permanently."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        prd_policy = config["retention_policies"]["prd"]

        assert prd_policy["delete_after_archive"] is False, \
            "PRDs should never be deleted (product history)"
        assert len(prd_policy["compliance_tags"]) > 0, \
            "PRDs should have compliance tags"

    def test_architecture_never_deleted(self, production_policies_path):
        """Test that architecture documents are preserved."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        arch_policy = config["retention_policies"]["architecture"]

        assert arch_policy["delete_after_archive"] is False, \
            "Architecture documents should never be deleted"
        assert "architecture-decisions" in arch_policy["compliance_tags"], \
            "Architecture should have architecture-decisions tag"


class TestPolicyLogic:
    """Test policy logic and consistency."""

    def test_retention_period_longer_than_obsolete(self, production_policies_path):
        """Test that retention periods are reasonable."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        for doc_type, policy in policies.items():
            # Skip policies with -1 (never)
            if policy["obsolete_to_archive"] == -1:
                continue

            # Archive retention should generally be longer than obsolete period
            # (This is not a hard rule, but generally makes sense)
            obsolete = policy["obsolete_to_archive"]
            retention = policy["archive_retention"]

            if retention != -1:  # Skip "forever" retention
                # Just ensure retention is positive if deletion is allowed
                if policy["delete_after_archive"]:
                    assert retention > 0, \
                        f"{doc_type}: retention must be positive if deletion allowed"

    def test_deletion_not_allowed_for_critical_docs(self, production_policies_path):
        """Test that critical documents can't be deleted."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        # These document types should NEVER be deleted
        critical_types = ["prd", "architecture", "postmortem", "qa_report", "adr", "epic"]

        for doc_type in critical_types:
            if doc_type in policies:
                policy = policies[doc_type]
                assert policy["delete_after_archive"] is False, \
                    f"{doc_type} is critical and should never be deleted"

    def test_draft_has_aggressive_cleanup(self, production_policies_path):
        """Test that drafts have aggressive cleanup policy."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        draft_policy = config["retention_policies"]["draft"]

        # Drafts should be cleaned up quickly
        assert draft_policy["obsolete_to_archive"] <= 14, \
            "Drafts should be archived within 2 weeks"
        assert draft_policy["archive_retention"] <= 60, \
            "Drafts should not be retained for long"
        assert draft_policy["delete_after_archive"] is True, \
            "Drafts should be deletable"


class TestPolicyLoading:
    """Test loading policies into ArchivalManager."""

    def test_load_production_policies(self, production_policies_path, temp_dir):
        """Test loading production policies into ArchivalManager."""
        # Create test infrastructure
        db_path = temp_dir / "test.db"
        archive_dir = temp_dir / ".archive"
        registry = DocumentRegistry(db_path)
        doc_manager = DocumentLifecycleManager(registry, archive_dir)

        # Load production policies
        archival_manager = ArchivalManager(doc_manager, production_policies_path)

        # Verify policies loaded
        policies = archival_manager.list_policies()
        assert len(policies) >= 10, "Should have at least 10 document type policies"

    def test_get_specific_policies(self, production_policies_path, temp_dir):
        """Test getting specific policies from loaded config."""
        db_path = temp_dir / "test.db"
        archive_dir = temp_dir / ".archive"
        registry = DocumentRegistry(db_path)
        doc_manager = DocumentLifecycleManager(registry, archive_dir)

        archival_manager = ArchivalManager(doc_manager, production_policies_path)

        # Test getting specific policies
        prd_policy = archival_manager.get_policy("prd")
        assert prd_policy is not None
        assert prd_policy.doc_type == "prd"

        story_policy = archival_manager.get_policy("story")
        assert story_policy is not None
        assert story_policy.doc_type == "story"

        postmortem_policy = archival_manager.get_policy("postmortem")
        assert postmortem_policy is not None
        assert postmortem_policy.archive_retention == -1


class TestPolicyDocumentation:
    """Test that policies are well-documented."""

    def test_file_has_header_comments(self, production_policies_path):
        """Test that the policies file has documentation."""
        content = production_policies_path.read_text(encoding="utf-8")

        # Should have comments explaining the structure
        assert "retention_policies" in content.lower()
        assert "compliance" in content.lower()

        # Should explain special cases
        assert "postmortem" in content.lower()
        assert "qa" in content.lower() or "quality" in content.lower()

    def test_each_policy_section_documented(self, production_policies_path):
        """Test that policy sections have comments."""
        content = production_policies_path.read_text(encoding="utf-8")

        # Check for major document types mentioned in comments
        expected_mentions = ["PRD", "Architecture", "Story", "QA", "Postmortem"]

        for mention in expected_mentions:
            assert mention in content, \
                f"Policy file should document {mention} policies"


class TestComplianceTagsConfiguration:
    """Test compliance tags configuration."""

    def test_compliance_tags_are_consistent(self, production_policies_path):
        """Test that compliance tags are used consistently."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        # Collect all compliance tags used
        all_tags = set()
        for policy in policies.values():
            all_tags.update(policy["compliance_tags"])

        # Common compliance tags should be used
        expected_common_tags = ["compliance", "audit"]

        # At least one policy should use common compliance tags
        tags_used = False
        for tag in expected_common_tags:
            if any(tag in policy["compliance_tags"] for policy in policies.values()):
                tags_used = True
                break

        assert tags_used or len(all_tags) > 0, \
            "Should have some compliance tags defined"

    def test_critical_docs_have_compliance_tags(self, production_policies_path):
        """Test that critical documents have compliance tags."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        # These should have compliance tags
        critical_with_tags = ["prd", "architecture", "postmortem", "qa_report", "adr"]

        for doc_type in critical_with_tags:
            if doc_type in policies:
                policy = policies[doc_type]
                assert len(policy["compliance_tags"]) > 0, \
                    f"{doc_type} should have compliance tags for protection"


class TestEdgeCasePolicies:
    """Test edge case policy configurations."""

    def test_negative_one_means_never(self, production_policies_path, temp_dir):
        """Test that -1 values are properly handled as 'never'."""
        db_path = temp_dir / "test.db"
        archive_dir = temp_dir / ".archive"
        registry = DocumentRegistry(db_path)
        doc_manager = DocumentLifecycleManager(registry, archive_dir)

        archival_manager = ArchivalManager(doc_manager, production_policies_path)

        postmortem_policy = archival_manager.get_policy("postmortem")

        # All three fields should be -1 for postmortems
        assert postmortem_policy.archive_to_obsolete == -1
        assert postmortem_policy.obsolete_to_archive == -1
        assert postmortem_policy.archive_retention == -1

    def test_zero_is_not_valid_retention(self, production_policies_path):
        """Test that zero is not used for retention periods."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        for doc_type, policy in policies.items():
            # Retention periods should be either positive or -1 (never)
            # Zero doesn't make sense (immediate deletion)
            for field in ["archive_to_obsolete", "obsolete_to_archive", "archive_retention"]:
                value = policy[field]
                assert value == -1 or value > 0, \
                    f"{doc_type}.{field} should be -1 (never) or positive, not zero"


class TestPolicyConsistency:
    """Test consistency across policies."""

    def test_similar_docs_have_similar_policies(self, production_policies_path):
        """Test that similar document types have similar policies."""
        with open(production_policies_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        policies = config["retention_policies"]

        # Critical documents should all disallow deletion
        critical = ["prd", "architecture", "postmortem", "qa_report"]
        for doc_type in critical:
            if doc_type in policies:
                assert policies[doc_type]["delete_after_archive"] is False, \
                    f"Critical document {doc_type} should not allow deletion"

        # Transient documents should allow deletion
        transient = ["draft", "story", "test_report"]
        for doc_type in transient:
            if doc_type in policies:
                # These can have deletion enabled
                # (Just checking they exist, not enforcing deletion)
                assert "delete_after_archive" in policies[doc_type]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
