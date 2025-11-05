"""
Comprehensive tests for ChecklistSchemaValidator.

Tests cover:
- Valid checklist validation
- Invalid checklist validation
- Pattern validation (version, item IDs)
- Array constraints
- YAML parsing
- Directory validation
- Integration with example checklists
- Performance benchmarks
"""

import time
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from gao_dev.core.checklists.schema_validator import ChecklistSchemaValidator


@pytest.fixture
def schema_path() -> Path:
    """Return path to checklist schema."""
    return Path(__file__).parent.parent.parent.parent / "gao_dev" / "config" / "schemas" / "checklist_schema.json"


@pytest.fixture
def validator(schema_path: Path) -> ChecklistSchemaValidator:
    """Create schema validator instance."""
    return ChecklistSchemaValidator(schema_path)


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def example_checklists_dir() -> Path:
    """Return path to example checklists directory."""
    return Path(__file__).parent.parent.parent.parent / "gao_dev" / "config" / "checklists"


class TestChecklistSchemaValidator:
    """Tests for ChecklistSchemaValidator class."""

    def test_validator_initialization(self, schema_path: Path) -> None:
        """Test validator can be initialized with valid schema."""
        validator = ChecklistSchemaValidator(schema_path)
        assert validator.schema is not None
        assert validator.validator is not None

    def test_validator_initialization_missing_file(self) -> None:
        """Test validator raises error with missing schema file."""
        with pytest.raises(FileNotFoundError):
            ChecklistSchemaValidator(Path("nonexistent.json"))


class TestValidChecklists:
    """Tests for validating well-formed checklists."""

    def test_minimal_valid_checklist(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test minimal valid checklist with required fields only."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_minimal.yaml")
        assert is_valid, f"Minimal checklist should be valid. Errors: {errors}"
        assert len(errors) == 0

    def test_complete_valid_checklist(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test complete valid checklist with all fields populated."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_complete.yaml")
        assert is_valid, f"Complete checklist should be valid. Errors: {errors}"
        assert len(errors) == 0

    def test_checklist_with_inheritance(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with extends field."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_complete.yaml")
        assert is_valid, f"Checklist with extends should be valid. Errors: {errors}"

    def test_checklist_with_all_severity_levels(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist with all severity levels."""
        checklist_data = {
            "checklist": {
                "name": "All Severities",
                "category": "testing",
                "version": "1.0.0",
                "items": [
                    {"id": "critical-item", "text": "Critical severity item", "severity": "critical"},
                    {"id": "high-item", "text": "High severity item", "severity": "high"},
                    {"id": "medium-item", "text": "Medium severity item", "severity": "medium"},
                    {"id": "low-item", "text": "Low severity item", "severity": "low"},
                ]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"All severity levels should be valid. Errors: {errors}"

    def test_checklist_with_references(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist with references array."""
        checklist_data = {
            "checklist": {
                "name": "With References",
                "category": "security",
                "version": "1.0.0",
                "items": [
                    {
                        "id": "item-with-refs",
                        "text": "Item with references to documentation",
                        "severity": "high",
                        "references": [
                            "https://example.com/doc1",
                            "https://example.com/doc2"
                        ]
                    }
                ]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"Checklist with references should be valid. Errors: {errors}"

    def test_checklist_with_metadata(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with metadata object."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_complete.yaml")
        assert is_valid, f"Checklist with metadata should be valid. Errors: {errors}"


class TestInvalidChecklists:
    """Tests for validating malformed checklists."""

    def test_missing_required_field_name(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist missing required name field."""
        checklist_data = {
            "checklist": {
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Test item", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_missing_required_field_category(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist missing required category field."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_missing_required.yaml")
        assert not is_valid
        assert len(errors) > 0
        assert any("category" in error.lower() for error in errors)

    def test_missing_required_field_version(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist missing required version field."""
        checklist_data = {
            "checklist": {
                "name": "Missing Version",
                "category": "testing",
                "items": [{"id": "item1", "text": "Test item", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("version" in error.lower() for error in errors)

    def test_missing_required_field_items(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist missing required items field."""
        checklist_data = {
            "checklist": {
                "name": "Missing Items",
                "category": "testing",
                "version": "1.0.0"
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("items" in error.lower() for error in errors)

    def test_invalid_category_enum(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with invalid category enum value."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_enum_value.yaml")
        assert not is_valid
        assert len(errors) > 0

    def test_invalid_severity_enum(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with invalid severity enum value."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_enum_value.yaml")
        assert not is_valid
        assert len(errors) > 0

    def test_invalid_version_pattern(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with invalid version pattern (not semver)."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_version_pattern.yaml")
        assert not is_valid
        assert any("version" in error.lower() or "pattern" in error.lower() for error in errors)

    def test_invalid_item_id_pattern(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with invalid item ID pattern (uppercase, spaces)."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_item_id_pattern.yaml")
        assert not is_valid
        assert len(errors) > 0

    def test_empty_items_array(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test checklist with empty items array (minItems violation)."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_empty_items.yaml")
        assert not is_valid
        assert any("items" in error.lower() for error in errors)

    def test_item_text_too_short(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist with item text too short (<10 chars)."""
        checklist_data = {
            "checklist": {
                "name": "Short Text",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Short", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("text" in error.lower() or "minlength" in error.lower() for error in errors)

    def test_name_too_short(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist with name too short (<3 chars)."""
        checklist_data = {
            "checklist": {
                "name": "AB",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Test item text", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("name" in error.lower() for error in errors)

    def test_name_too_long(self, validator: ChecklistSchemaValidator) -> None:
        """Test checklist with name too long (>100 chars)."""
        checklist_data = {
            "checklist": {
                "name": "A" * 101,
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Test item text", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("name" in error.lower() for error in errors)


class TestPatternValidation:
    """Tests for regex pattern validations."""

    def test_valid_version_patterns(self, validator: ChecklistSchemaValidator) -> None:
        """Test version pattern accepts valid semver strings."""
        valid_versions = ["1.0.0", "2.1.3", "10.20.30", "0.0.1", "99.99.99"]
        for version in valid_versions:
            checklist_data = {
                "checklist": {
                    "name": "Version Test",
                    "category": "testing",
                    "version": version,
                    "items": [{"id": "item1", "text": "Test item text", "severity": "low"}]
                }
            }
            is_valid, errors = validator.validate(checklist_data)
            assert is_valid, f"Version '{version}' should be valid. Errors: {errors}"

    def test_invalid_version_patterns(self, validator: ChecklistSchemaValidator) -> None:
        """Test version pattern rejects invalid semver strings."""
        invalid_versions = ["1.0", "v1.0.0", "1.0.0-beta", "1.0.0.0", "1", "1.0.x"]
        for version in invalid_versions:
            checklist_data = {
                "checklist": {
                    "name": "Version Test",
                    "category": "testing",
                    "version": version,
                    "items": [{"id": "item1", "text": "Test item text", "severity": "low"}]
                }
            }
            is_valid, errors = validator.validate(checklist_data)
            assert not is_valid, f"Version '{version}' should be invalid"

    def test_valid_item_id_patterns(self, validator: ChecklistSchemaValidator) -> None:
        """Test item ID pattern accepts valid kebab-case strings."""
        valid_ids = ["test-coverage", "sql-injection", "item1", "a", "test-123"]
        for item_id in valid_ids:
            checklist_data = {
                "checklist": {
                    "name": "ID Test",
                    "category": "testing",
                    "version": "1.0.0",
                    "items": [{"id": item_id, "text": "Test item text", "severity": "low"}]
                }
            }
            is_valid, errors = validator.validate(checklist_data)
            assert is_valid, f"Item ID '{item_id}' should be valid. Errors: {errors}"

    def test_invalid_item_id_patterns(self, validator: ChecklistSchemaValidator) -> None:
        """Test item ID pattern rejects invalid strings."""
        invalid_ids = ["Test Coverage", "SQL_INJECTION", "item 1", "Item-1", "item.1", "item@1"]
        for item_id in invalid_ids:
            checklist_data = {
                "checklist": {
                    "name": "ID Test",
                    "category": "testing",
                    "version": "1.0.0",
                    "items": [{"id": item_id, "text": "Test item text", "severity": "low"}]
                }
            }
            is_valid, errors = validator.validate(checklist_data)
            assert not is_valid, f"Item ID '{item_id}' should be invalid"


class TestArrayConstraints:
    """Tests for array validations."""

    def test_items_array_requires_at_least_one_item(self, validator: ChecklistSchemaValidator) -> None:
        """Test items array requires at least 1 item."""
        checklist_data = {
            "checklist": {
                "name": "Empty Items",
                "category": "testing",
                "version": "1.0.0",
                "items": []
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert not is_valid
        assert any("items" in error.lower() for error in errors)

    def test_items_array_can_contain_multiple_items(self, validator: ChecklistSchemaValidator) -> None:
        """Test items array can contain multiple items."""
        checklist_data = {
            "checklist": {
                "name": "Multiple Items",
                "category": "testing",
                "version": "1.0.0",
                "items": [
                    {"id": "item1", "text": "First test item", "severity": "low"},
                    {"id": "item2", "text": "Second test item", "severity": "medium"},
                    {"id": "item3", "text": "Third test item", "severity": "high"}
                ]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"Multiple items should be valid. Errors: {errors}"

    def test_references_array_is_optional(self, validator: ChecklistSchemaValidator) -> None:
        """Test references array is optional."""
        checklist_data = {
            "checklist": {
                "name": "No References",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Item without references", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"References should be optional. Errors: {errors}"

    def test_tags_array_is_optional(self, validator: ChecklistSchemaValidator) -> None:
        """Test tags array is optional."""
        checklist_data = {
            "checklist": {
                "name": "No Tags",
                "category": "testing",
                "version": "1.0.0",
                "items": [{"id": "item1", "text": "Item without tags", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"Tags should be optional. Errors: {errors}"


class TestYAMLParsing:
    """Tests for YAML file loading."""

    def test_valid_yaml_file_loads_successfully(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test valid YAML file loads successfully."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_minimal.yaml")
        assert is_valid, f"Valid YAML should load. Errors: {errors}"

    def test_invalid_yaml_file_raises_error(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test invalid YAML file raises YAMLError."""
        is_valid, errors = validator.validate_file(fixtures_dir / "invalid_yaml_syntax.yaml")
        assert not is_valid
        assert any("yaml" in error.lower() for error in errors)

    def test_missing_file_returns_error(self, validator: ChecklistSchemaValidator) -> None:
        """Test missing file returns appropriate error."""
        is_valid, errors = validator.validate_file(Path("nonexistent.yaml"))
        assert not is_valid
        assert any("not found" in error.lower() for error in errors)

    def test_utf8_encoding_handled_correctly(self, validator: ChecklistSchemaValidator, tmp_path: Path) -> None:
        """Test UTF-8 encoding handled correctly."""
        checklist_file = tmp_path / "utf8_checklist.yaml"
        checklist_file.write_text(
            """checklist:
  name: "UTF-8 Checklist"
  category: "testing"
  version: "1.0.0"
  items:
    - id: "item1"
      text: "Item with UTF-8 characters: café, naïve, résumé"
      severity: "low"
""",
            encoding="utf-8"
        )
        is_valid, errors = validator.validate_file(checklist_file)
        assert is_valid, f"UTF-8 encoding should work. Errors: {errors}"


class TestExampleChecklists:
    """Integration tests for example checklists."""

    def test_unit_test_standards_is_valid(self, validator: ChecklistSchemaValidator, example_checklists_dir: Path) -> None:
        """Test unit-test-standards.yaml is valid."""
        checklist_path = example_checklists_dir / "testing" / "unit-test-standards.yaml"
        is_valid, errors = validator.validate_file(checklist_path)
        assert is_valid, f"unit-test-standards.yaml should be valid. Errors: {errors}"

    def test_owasp_top_10_is_valid(self, validator: ChecklistSchemaValidator, example_checklists_dir: Path) -> None:
        """Test owasp-top-10.yaml is valid."""
        checklist_path = example_checklists_dir / "security" / "owasp-top-10.yaml"
        is_valid, errors = validator.validate_file(checklist_path)
        assert is_valid, f"owasp-top-10.yaml should be valid. Errors: {errors}"

    def test_production_readiness_is_valid(self, validator: ChecklistSchemaValidator, example_checklists_dir: Path) -> None:
        """Test production-readiness.yaml is valid."""
        checklist_path = example_checklists_dir / "deployment" / "production-readiness.yaml"
        is_valid, errors = validator.validate_file(checklist_path)
        assert is_valid, f"production-readiness.yaml should be valid. Errors: {errors}"

    def test_all_example_checklists_are_valid(self, validator: ChecklistSchemaValidator, example_checklists_dir: Path) -> None:
        """Test all example checklists validate against schema."""
        if not example_checklists_dir.exists():
            pytest.skip("Example checklists directory not found")

        results = validator.validate_directory(example_checklists_dir)
        assert len(results) > 0, "Should find at least one checklist"

        invalid_checklists = {path: errors for path, (is_valid, errors) in results.items() if not is_valid}
        assert len(invalid_checklists) == 0, f"All example checklists should be valid. Invalid: {invalid_checklists}"


class TestDirectoryValidation:
    """Tests for directory validation."""

    def test_validate_directory_finds_all_yaml_files(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test validate_directory() finds all YAML files recursively."""
        results = validator.validate_directory(fixtures_dir)
        assert len(results) > 0, "Should find at least one YAML file"

        # Check that at least some expected files were found
        file_names = [Path(path).name for path in results.keys()]
        assert "valid_minimal.yaml" in file_names
        assert "valid_complete.yaml" in file_names

    def test_validate_directory_reports_valid_and_invalid_correctly(
        self, validator: ChecklistSchemaValidator, fixtures_dir: Path
    ) -> None:
        """Test validate_directory() reports valid and invalid files correctly."""
        results = validator.validate_directory(fixtures_dir)

        # Find valid and invalid results
        valid_files = [path for path, (is_valid, _) in results.items() if is_valid]
        invalid_files = [path for path, (is_valid, _) in results.items() if not is_valid]

        assert len(valid_files) > 0, "Should find at least one valid file"
        assert len(invalid_files) > 0, "Should find at least one invalid file"

    def test_validate_directory_handles_empty_directory(self, validator: ChecklistSchemaValidator, tmp_path: Path) -> None:
        """Test validate_directory() handles empty directory gracefully."""
        results = validator.validate_directory(tmp_path)
        assert len(results) == 0, "Empty directory should return empty results"


class TestPerformance:
    """Performance tests for schema validation."""

    def test_single_checklist_validation_performance(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test single checklist validation completes in <10ms."""
        start_time = time.perf_counter()
        validator.validate_file(fixtures_dir / "valid_minimal.yaml")
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        assert duration_ms < 10, f"Validation took {duration_ms:.2f}ms, should be <10ms"

    def test_multiple_checklists_validation_performance(
        self, validator: ChecklistSchemaValidator, tmp_path: Path
    ) -> None:
        """Test validation of 100 checklists completes in <1 second."""
        # Create 100 test checklists
        for i in range(100):
            checklist_file = tmp_path / f"checklist_{i}.yaml"
            checklist_file.write_text(
                f"""checklist:
  name: "Test Checklist {i}"
  category: "testing"
  version: "1.0.0"
  items:
    - id: "item-{i}"
      text: "Test item for checklist {i}"
      severity: "low"
"""
            )

        start_time = time.perf_counter()
        results = validator.validate_directory(tmp_path)
        end_time = time.perf_counter()

        duration_seconds = end_time - start_time
        assert len(results) == 100, "Should validate all 100 checklists"
        assert duration_seconds < 1.0, f"Validation took {duration_seconds:.2f}s, should be <1s"

    def test_schema_loading_performance(self, schema_path: Path) -> None:
        """Test schema loading from file completes in <50ms."""
        start_time = time.perf_counter()
        ChecklistSchemaValidator(schema_path)
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000
        assert duration_ms < 50, f"Schema loading took {duration_ms:.2f}ms, should be <50ms"


class TestInheritanceValidation:
    """Tests for checklist inheritance (prepares for Story 14.2)."""

    def test_extends_field_is_syntactically_valid(self, validator: ChecklistSchemaValidator, fixtures_dir: Path) -> None:
        """Test extends field references are syntactically valid."""
        is_valid, errors = validator.validate_file(fixtures_dir / "valid_complete.yaml")
        assert is_valid, f"Checklist with extends field should be valid. Errors: {errors}"

    def test_extends_field_format(self, validator: ChecklistSchemaValidator) -> None:
        """Test extends field format is 'category/checklist-name'."""
        checklist_data = {
            "checklist": {
                "name": "Child Checklist",
                "category": "testing",
                "version": "1.0.0",
                "extends": "testing/base-checklist",
                "items": [{"id": "item1", "text": "Test item text", "severity": "low"}]
            }
        }
        is_valid, errors = validator.validate(checklist_data)
        assert is_valid, f"Extends field with category/name format should be valid. Errors: {errors}"
