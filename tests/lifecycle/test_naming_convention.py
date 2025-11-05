"""
Unit tests for DocumentNamingConvention.

Tests cover:
- Filename generation for all document types
- Special cases (ADR, Postmortem, Runbook)
- Filename parsing and validation
- Edge cases and error handling
"""

import pytest
from datetime import datetime
from gao_dev.lifecycle.naming_convention import DocumentNamingConvention


class TestGenerateFilename:
    """Tests for generate_filename method."""

    def test_generate_standard_filename_default_params(self):
        """Test standard filename generation with default parameters."""
        result = DocumentNamingConvention.generate_filename("PRD", "user authentication")
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"PRD_user-authentication_{today}_v1.0.md"
        assert result == expected

    def test_generate_standard_filename_custom_version(self):
        """Test standard filename with custom version."""
        result = DocumentNamingConvention.generate_filename(
            "ARCHITECTURE", "system design", version="2.5"
        )
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"ARCHITECTURE_system-design_{today}_v2.5.md"
        assert result == expected

    def test_generate_standard_filename_custom_extension(self):
        """Test standard filename with custom file extension."""
        result = DocumentNamingConvention.generate_filename(
            "EPIC", "feature rollout", ext="txt"
        )
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"EPIC_feature-rollout_{today}_v1.0.txt"
        assert result == expected

    def test_generate_filename_custom_date(self):
        """Test filename generation with custom date."""
        result = DocumentNamingConvention.generate_filename(
            "PRD", "api gateway", date="2024-01-15"
        )
        expected = "PRD_api-gateway_2024-01-15_v1.0.md"
        assert result == expected

    def test_generate_filename_subject_normalization(self):
        """Test subject normalization (spaces, underscores, special chars)."""
        result = DocumentNamingConvention.generate_filename(
            "STORY", "User_Profile / Settings", date="2024-11-05"
        )
        expected = "STORY_user-profile-settings_2024-11-05_v1.0.md"
        assert result == expected

    def test_generate_filename_removes_special_characters(self):
        """Test that special characters are removed from subject."""
        result = DocumentNamingConvention.generate_filename(
            "PRD", "user@auth#feature!", date="2024-11-05"
        )
        expected = "PRD_userauthfeature_2024-11-05_v1.0.md"
        assert result == expected

    def test_generate_adr_filename(self):
        """Test ADR filename generation."""
        result = DocumentNamingConvention.generate_filename(
            "ADR", "database choice", adr_number=1, date="2024-09-01"
        )
        expected = "ADR-001_database-choice_2024-09-01.md"
        assert result == expected

    def test_generate_adr_filename_high_number(self):
        """Test ADR with high number (padding to 3 digits)."""
        result = DocumentNamingConvention.generate_filename(
            "ADR", "logging framework", adr_number=42, date="2024-10-15"
        )
        expected = "ADR-042_logging-framework_2024-10-15.md"
        assert result == expected

    def test_generate_adr_without_number_raises_error(self):
        """Test that ADR without number raises ValueError."""
        with pytest.raises(ValueError, match="ADR requires adr_number parameter"):
            DocumentNamingConvention.generate_filename("ADR", "test")

    def test_generate_postmortem_filename(self):
        """Test Postmortem filename generation."""
        result = DocumentNamingConvention.generate_filename(
            "POSTMORTEM", "api outage", date="2024-11-15"
        )
        expected = "Postmortem_2024-11-15_api-outage.md"
        assert result == expected

    def test_generate_runbook_filename(self):
        """Test Runbook filename generation."""
        result = DocumentNamingConvention.generate_filename(
            "RUNBOOK", "kafka cluster restart", version="1.3", date="2024-08-01"
        )
        expected = "Runbook_kafka-cluster-restart_2024-08-01_v1.3.md"
        assert result == expected

    def test_generate_filename_lowercase_doctype(self):
        """Test that lowercase doc_type is converted to uppercase."""
        result = DocumentNamingConvention.generate_filename(
            "prd", "feature", date="2024-11-05"
        )
        expected = "PRD_feature_2024-11-05_v1.0.md"
        assert result == expected


class TestParseFilename:
    """Tests for parse_filename method."""

    def test_parse_standard_filename(self):
        """Test parsing standard filename."""
        filename = "PRD_user-authentication_2024-11-05_v1.0.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["doctype"] == "PRD"
        assert result["subject"] == "user-authentication"
        assert result["date"] == "2024-11-05"
        assert result["version"] == "1.0"
        assert result["ext"] == "md"

    def test_parse_architecture_filename(self):
        """Test parsing architecture document filename."""
        filename = "ARCHITECTURE_system-design_2024-09-20_v2.1.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["doctype"] == "ARCHITECTURE"
        assert result["subject"] == "system-design"
        assert result["version"] == "2.1"

    def test_parse_adr_filename(self):
        """Test parsing ADR filename."""
        filename = "ADR-001_database-choice_2024-09-01.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["doctype"] == "ADR"
        assert result["number"] == "001"
        assert result["subject"] == "database-choice"
        assert result["date"] == "2024-09-01"
        assert result["ext"] == "md"

    def test_parse_adr_high_number(self):
        """Test parsing ADR with high number."""
        filename = "ADR-042_logging-framework_2024-10-15.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["number"] == "042"
        assert result["subject"] == "logging-framework"

    def test_parse_postmortem_filename(self):
        """Test parsing Postmortem filename."""
        filename = "Postmortem_2024-11-15_api-outage.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["doctype"] == "POSTMORTEM"
        assert result["date"] == "2024-11-15"
        assert result["subject"] == "api-outage"

    def test_parse_runbook_filename(self):
        """Test parsing Runbook filename."""
        filename = "Runbook_kafka-cluster-restart_2024-08-01_v1.3.md"
        result = DocumentNamingConvention.parse_filename(filename)

        assert result["doctype"] == "RUNBOOK"
        assert result["subject"] == "kafka-cluster-restart"
        assert result["date"] == "2024-08-01"
        assert result["version"] == "1.3"

    def test_parse_invalid_filename_raises_error(self):
        """Test that invalid filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename does not match convention"):
            DocumentNamingConvention.parse_filename("invalid-filename.md")

    def test_parse_filename_missing_version(self):
        """Test that filename missing version raises error."""
        with pytest.raises(ValueError, match="Filename does not match convention"):
            DocumentNamingConvention.parse_filename("PRD_subject_2024-11-05.md")

    def test_parse_filename_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValueError, match="Filename does not match convention"):
            DocumentNamingConvention.parse_filename("PRD_subject_11-05-2024_v1.0.md")

    def test_parse_filename_uppercase_subject(self):
        """Test that uppercase subject is rejected."""
        with pytest.raises(ValueError, match="Filename does not match convention"):
            DocumentNamingConvention.parse_filename("PRD_User-Auth_2024-11-05_v1.0.md")

    def test_parse_filename_spaces(self):
        """Test that spaces in filename are rejected."""
        with pytest.raises(ValueError, match="Filename does not match convention"):
            DocumentNamingConvention.parse_filename("PRD user auth 2024-11-05 v1.0.md")


class TestValidateFilename:
    """Tests for validate_filename method."""

    def test_validate_valid_filename(self):
        """Test validation of valid filename."""
        filename = "PRD_user-authentication_2024-11-05_v1.0.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is True
        assert error is None

    def test_validate_valid_adr(self):
        """Test validation of valid ADR filename."""
        filename = "ADR-001_database-choice_2024-09-01.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is True
        assert error is None

    def test_validate_valid_postmortem(self):
        """Test validation of valid Postmortem filename."""
        filename = "Postmortem_2024-11-15_api-outage.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is True
        assert error is None

    def test_validate_valid_runbook(self):
        """Test validation of valid Runbook filename."""
        filename = "Runbook_kafka-cluster-restart_2024-08-01_v1.3.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is True
        assert error is None

    def test_validate_invalid_filename(self):
        """Test validation of invalid filename."""
        filename = "random-file.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is False
        assert error is not None
        assert "Filename does not match convention" in error

    def test_validate_missing_version(self):
        """Test validation of filename missing version."""
        filename = "PRD_subject_2024-11-05.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is False
        assert error is not None

    def test_validate_invalid_date(self):
        """Test validation of filename with invalid date format."""
        filename = "PRD_subject_11-05-2024_v1.0.md"
        is_valid, error = DocumentNamingConvention.validate_filename(filename)

        assert is_valid is False
        assert error is not None


class TestSpecialCaseMethods:
    """Tests for special case helper methods."""

    def test_is_special_case_adr(self):
        """Test that ADR is identified as special case."""
        assert DocumentNamingConvention.is_special_case("ADR") is True
        assert DocumentNamingConvention.is_special_case("adr") is True

    def test_is_special_case_postmortem(self):
        """Test that POSTMORTEM is identified as special case."""
        assert DocumentNamingConvention.is_special_case("POSTMORTEM") is True
        assert DocumentNamingConvention.is_special_case("postmortem") is True

    def test_is_special_case_runbook(self):
        """Test that RUNBOOK is identified as special case."""
        assert DocumentNamingConvention.is_special_case("RUNBOOK") is True
        assert DocumentNamingConvention.is_special_case("runbook") is True

    def test_is_special_case_prd(self):
        """Test that PRD is not a special case."""
        assert DocumentNamingConvention.is_special_case("PRD") is False

    def test_is_special_case_architecture(self):
        """Test that ARCHITECTURE is not a special case."""
        assert DocumentNamingConvention.is_special_case("ARCHITECTURE") is False


class TestSuggestFilename:
    """Tests for suggest_filename method."""

    def test_suggest_filename_simple(self):
        """Test suggesting filename from simple input."""
        result = DocumentNamingConvention.suggest_filename("prd.md", "PRD", "User Auth")
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"PRD_user-auth_{today}_v1.0.md"
        assert result == expected

    def test_suggest_filename_extracts_version(self):
        """Test suggesting filename extracts version from current name."""
        result = DocumentNamingConvention.suggest_filename(
            "prd_v2.3.md", "PRD", "User Auth"
        )
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"PRD_user-auth_{today}_v2.3.md"
        assert result == expected

    def test_suggest_filename_adr_extracts_number(self):
        """Test suggesting ADR filename extracts number."""
        result = DocumentNamingConvention.suggest_filename(
            "adr-005.md", "ADR", "Database Choice"
        )
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"ADR-005_database-choice_{today}.md"
        assert result == expected

    def test_suggest_filename_preserves_extension(self):
        """Test suggesting filename preserves extension from current name."""
        result = DocumentNamingConvention.suggest_filename(
            "document.txt", "STORY", "Feature Work"
        )
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"STORY_feature-work_{today}_v1.0.txt"
        assert result == expected

    def test_suggest_filename_no_extension(self):
        """Test suggesting filename when current name has no extension."""
        result = DocumentNamingConvention.suggest_filename("document", "EPIC", "Project")
        today = datetime.now().strftime("%Y-%m-%d")
        expected = f"EPIC_project_{today}_v1.0.md"
        assert result == expected


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_generate_filename_empty_subject(self):
        """Test filename generation with empty subject."""
        result = DocumentNamingConvention.generate_filename("PRD", "", date="2024-11-05")
        expected = "PRD__2024-11-05_v1.0.md"
        assert result == expected

    def test_generate_filename_long_subject(self):
        """Test filename generation with very long subject."""
        long_subject = "a" * 200
        result = DocumentNamingConvention.generate_filename(
            "PRD", long_subject, date="2024-11-05"
        )
        assert result.startswith("PRD_")
        assert "_2024-11-05_v1.0.md" in result

    def test_generate_filename_special_chars_only(self):
        """Test filename generation with only special characters."""
        result = DocumentNamingConvention.generate_filename(
            "PRD", "!@#$%^", date="2024-11-05"
        )
        expected = "PRD__2024-11-05_v1.0.md"
        assert result == expected

    def test_parse_filename_different_extensions(self):
        """Test parsing filenames with different extensions."""
        filenames = [
            "PRD_subject_2024-11-05_v1.0.txt",
            "PRD_subject_2024-11-05_v1.0.rst",
            "PRD_subject_2024-11-05_v1.0.html",
        ]

        for filename in filenames:
            result = DocumentNamingConvention.parse_filename(filename)
            assert result["ext"] in ["txt", "rst", "html"]

    def test_validate_filename_empty_string(self):
        """Test validation of empty string."""
        is_valid, error = DocumentNamingConvention.validate_filename("")
        assert is_valid is False
        assert error is not None

    def test_generate_adr_zero_number(self):
        """Test ADR generation with number 0."""
        result = DocumentNamingConvention.generate_filename(
            "ADR", "test", adr_number=0, date="2024-11-05"
        )
        expected = "ADR-000_test_2024-11-05.md"
        assert result == expected

    def test_generate_adr_large_number(self):
        """Test ADR generation with large number (>999)."""
        result = DocumentNamingConvention.generate_filename(
            "ADR", "test", adr_number=1234, date="2024-11-05"
        )
        expected = "ADR-1234_test_2024-11-05.md"
        assert result == expected
