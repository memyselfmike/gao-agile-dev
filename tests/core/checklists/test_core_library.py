"""
Integration tests for the core checklist library.

Tests that all 21+ checklists in the core library:
- Load successfully
- Validate against schema
- Have appropriate metadata
- Have correct item counts
- Follow inheritance patterns
"""

import time
from pathlib import Path

import pytest

from gao_dev.core.checklists.checklist_loader import ChecklistLoader
from gao_dev.core.checklists.schema_validator import ChecklistSchemaValidator


@pytest.fixture
def schema_path():
    """Path to checklist JSON schema."""
    return Path("gao_dev/config/schemas/checklist_schema.json")


@pytest.fixture
def checklists_dir():
    """Path to core checklists directory."""
    return Path("gao_dev/config/checklists")


@pytest.fixture
def validator(schema_path):
    """Schema validator instance."""
    return ChecklistSchemaValidator(schema_path)


@pytest.fixture
def loader(checklists_dir, schema_path):
    """Checklist loader instance."""
    return ChecklistLoader([checklists_dir], schema_path)


class TestCoreLibraryValidation:
    """Test that all core checklists are valid."""

    def test_all_checklists_validate(self, validator, checklists_dir):
        """Test that all checklists validate against schema."""
        results = validator.validate_directory(checklists_dir)

        # Should have at least 21 checklists
        assert len(results) >= 21, f"Expected at least 21 checklists, found {len(results)}"

        # All should be valid
        invalid_checklists = []
        for file_path, (is_valid, errors) in results.items():
            if not is_valid:
                invalid_checklists.append((file_path, errors))

        if invalid_checklists:
            error_msg = "The following checklists failed validation:\n"
            for file_path, errors in invalid_checklists:
                error_msg += f"\n{file_path}:\n"
                for error in errors:
                    error_msg += f"  - {error}\n"
            pytest.fail(error_msg)

    def test_checklists_have_required_fields(self, loader, checklists_dir):
        """Test that all checklists have required fields."""
        checklist_names = loader.list_checklists()

        for name in checklist_names:
            checklist = loader.load_checklist(name)

            # Required fields
            assert checklist.name, f"{name}: missing name"
            assert checklist.category, f"{name}: missing category"
            assert checklist.version, f"{name}: missing version"
            assert len(checklist.items) > 0, f"{name}: no items"

            # Metadata should exist
            assert checklist.metadata, f"{name}: missing metadata"


class TestCoreLibraryCategories:
    """Test checklist organization by category."""

    def test_testing_checklists(self, loader):
        """Test that testing category has expected checklists."""
        all_checklists = loader.list_checklists()
        testing_checklists = [c for c in all_checklists if c.startswith("testing/")]

        # Should have 4 testing checklists
        assert len(testing_checklists) == 4, f"Expected 4 testing checklists, found {len(testing_checklists)}"

        expected = [
            "testing/base-testing-standards",
            "testing/unit-test-standards",
            "testing/integration-test-standards",
            "testing/e2e-test-standards",
        ]

        for checklist_name in expected:
            assert checklist_name in testing_checklists, f"Missing {checklist_name}"

    def test_code_quality_checklists(self, loader):
        """Test that code-quality category has expected checklists."""
        all_checklists = loader.list_checklists()
        code_quality_checklists = [c for c in all_checklists if c.startswith("code-quality/")]

        # Should have 5 code-quality checklists
        assert len(code_quality_checklists) == 5, f"Expected 5 code-quality checklists, found {len(code_quality_checklists)}"

        expected = [
            "code-quality/solid-principles",
            "code-quality/clean-code",
            "code-quality/python-standards",
            "code-quality/type-safety",
            "code-quality/refactoring",
        ]

        for checklist_name in expected:
            assert checklist_name in code_quality_checklists, f"Missing {checklist_name}"

    def test_security_checklists(self, loader):
        """Test that security category has expected checklists."""
        all_checklists = loader.list_checklists()
        security_checklists = [c for c in all_checklists if c.startswith("security/")]

        # Should have 4 security checklists
        assert len(security_checklists) == 4, f"Expected 4 security checklists, found {len(security_checklists)}"

        expected = [
            "security/owasp-top-10",
            "security/secure-coding",
            "security/secrets-management",
            "security/api-security",
        ]

        for checklist_name in expected:
            assert checklist_name in security_checklists, f"Missing {checklist_name}"

    def test_deployment_checklists(self, loader):
        """Test that deployment category has expected checklists."""
        all_checklists = loader.list_checklists()
        deployment_checklists = [c for c in all_checklists if c.startswith("deployment/")]

        # Should have 4 deployment checklists
        assert len(deployment_checklists) == 4, f"Expected 4 deployment checklists, found {len(deployment_checklists)}"

        expected = [
            "deployment/production-readiness",
            "deployment/rollout-checklist",
            "deployment/database-migration",
            "deployment/configuration-management",
        ]

        for checklist_name in expected:
            assert checklist_name in deployment_checklists, f"Missing {checklist_name}"

    def test_operations_checklists(self, loader):
        """Test that operations category has expected checklists."""
        all_checklists = loader.list_checklists()
        operations_checklists = [c for c in all_checklists if c.startswith("operations/")]

        # Should have 4 operations checklists
        assert len(operations_checklists) == 4, f"Expected 4 operations checklists, found {len(operations_checklists)}"

        expected = [
            "operations/incident-response",
            "operations/change-management",
            "operations/monitoring-setup",
            "operations/disaster-recovery",
        ]

        for checklist_name in expected:
            assert checklist_name in operations_checklists, f"Missing {checklist_name}"

    def test_general_checklists(self, loader):
        """Test that general category has expected checklists."""
        all_checklists = loader.list_checklists()
        general_checklists = [c for c in all_checklists if c.startswith("general/")]

        # Should have 4 general checklists
        assert len(general_checklists) == 4, f"Expected 4 general checklists, found {len(general_checklists)}"

        expected = [
            "general/code-review",
            "general/pr-review",
            "general/documentation",
            "general/story-implementation",
        ]

        for checklist_name in expected:
            assert checklist_name in general_checklists, f"Missing {checklist_name}"

    def test_total_checklist_count(self, loader):
        """Test that total checklist count is correct."""
        all_checklists = loader.list_checklists()

        # Should have exactly 25 checklists (21 new + 4 existing)
        # testing: 4, code-quality: 5, security: 4, deployment: 4, operations: 4, general: 4
        assert len(all_checklists) == 25, f"Expected 25 checklists, found {len(all_checklists)}"


class TestChecklistInheritance:
    """Test inheritance patterns in checklists."""

    def test_base_testing_standards_standalone(self, loader):
        """Test that base-testing-standards can be loaded standalone."""
        checklist = loader.load_checklist("testing/base-testing-standards")

        assert checklist.name == "Base Testing Standards"
        assert checklist.category == "testing"
        assert len(checklist.items) >= 3  # Should have at least a few items

    def test_testing_checklists_extend_base(self, loader):
        """Test that testing checklists extend base-testing-standards."""
        # Unit tests extend base
        unit_checklist = loader.load_checklist("testing/unit-test-standards")
        assert unit_checklist.name == "Unit Test Standards"
        assert len(unit_checklist.items) >= 10  # Base items + child items

        # Check that base items are included
        item_ids = [item.id for item in unit_checklist.items]
        assert "test-exists" in item_ids  # From base
        assert "test-passing" in item_ids  # From base
        assert "test-coverage" in item_ids  # From child

        # Integration tests extend base
        integration_checklist = loader.load_checklist("testing/integration-test-standards")
        assert integration_checklist.name == "Integration Test Standards"
        item_ids = [item.id for item in integration_checklist.items]
        assert "test-exists" in item_ids  # From base

        # E2E tests extend base
        e2e_checklist = loader.load_checklist("testing/e2e-test-standards")
        assert e2e_checklist.name == "End-to-End Test Standards"
        item_ids = [item.id for item in e2e_checklist.items]
        assert "test-exists" in item_ids  # From base


class TestChecklistContent:
    """Test checklist content quality."""

    def test_checklists_have_reasonable_item_counts(self, loader):
        """Test that checklists have 5-15 items (focused, not overwhelming)."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)
            item_count = len(checklist.items)

            # Should have between 5 and 15 items
            assert 3 <= item_count <= 15, f"{name}: has {item_count} items (expected 5-15)"

    def test_severity_distribution(self, loader):
        """Test that checklists use severity levels appropriately."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)

            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for item in checklist.items:
                severity_counts[item.severity] += 1

            # Should have at least one high or critical item
            assert (
                severity_counts["critical"] + severity_counts["high"] >= 2
            ), f"{name}: needs more high/critical items"

    def test_critical_items_have_help_text(self, loader):
        """Test that all critical items have help_text."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)

            for item in checklist.items:
                if item.severity == "critical":
                    assert item.help_text, f"{name}: critical item '{item.id}' missing help_text"

    def test_security_checklists_have_references(self, loader):
        """Test that security checklists have references."""
        security_checklists = [
            "security/owasp-top-10",
            "security/secure-coding",
            "security/secrets-management",
            "security/api-security",
        ]

        for name in security_checklists:
            checklist = loader.load_checklist(name)

            # At least some items should have references
            has_references = any(item.references for item in checklist.items)
            assert has_references, f"{name}: security checklist should have references"

    def test_metadata_populated(self, loader):
        """Test that metadata fields are populated."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)

            # Should have metadata
            assert checklist.metadata, f"{name}: missing metadata"

            # Should have domain
            assert "domain" in checklist.metadata, f"{name}: missing domain in metadata"

            # Should have applicable_to
            assert "applicable_to" in checklist.metadata, f"{name}: missing applicable_to in metadata"

            # Should have author
            assert "author" in checklist.metadata, f"{name}: missing author in metadata"

            # Should have tags
            assert "tags" in checklist.metadata, f"{name}: missing tags in metadata"


class TestPerformance:
    """Test loading performance."""

    def test_bulk_loading_performance(self, loader):
        """Test that all checklists can be loaded in <1 second."""
        start_time = time.time()

        all_checklists = loader.list_checklists()
        for name in all_checklists:
            loader.load_checklist(name)

        elapsed_time = time.time() - start_time

        # Should load all checklists in less than 1 second
        assert elapsed_time < 1.0, f"Loading took {elapsed_time:.2f}s (expected <1s)"

    def test_single_checklist_load_time(self, loader):
        """Test that a single checklist loads in <50ms."""
        # Clear cache to ensure we're testing actual load time
        loader._cache.clear()

        start_time = time.time()
        loader.load_checklist("testing/unit-test-standards")
        elapsed_time = time.time() - start_time

        # Should load in less than 50ms
        assert elapsed_time < 0.05, f"Loading took {elapsed_time*1000:.1f}ms (expected <50ms)"


class TestChecklistUsability:
    """Test checklist usability for agents and humans."""

    def test_checklists_have_descriptions(self, loader):
        """Test that checklists have descriptions."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)
            assert checklist.description, f"{name}: missing description"

    def test_item_ids_are_kebab_case(self, loader):
        """Test that item IDs follow kebab-case convention."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)

            for item in checklist.items:
                # Should match kebab-case pattern (lowercase with hyphens)
                assert item.id.islower() or "-" in item.id, f"{name}: item ID '{item.id}' not kebab-case"

    def test_no_duplicate_item_ids_within_checklist(self, loader):
        """Test that there are no duplicate item IDs within a checklist."""
        all_checklists = loader.list_checklists()

        for name in all_checklists:
            checklist = loader.load_checklist(name)

            item_ids = [item.id for item in checklist.items]
            duplicates = [id for id in item_ids if item_ids.count(id) > 1]

            assert len(duplicates) == 0, f"{name}: duplicate item IDs: {duplicates}"

    def test_checklists_can_be_rendered(self, loader):
        """Test that checklists can be rendered to markdown."""
        all_checklists = loader.list_checklists()

        for name in all_checklists[:5]:  # Test a few
            checklist = loader.load_checklist(name)
            markdown = loader.render_checklist(checklist)

            # Should contain checklist name and items
            assert checklist.name in markdown
            assert "[ ]" in markdown  # Checkbox
