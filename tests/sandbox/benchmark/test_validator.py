"""Tests for benchmark configuration validator."""

import pytest
from pathlib import Path
import tempfile

from gao_dev.sandbox.benchmark.validator import (
    ConfigValidator,
    ValidationResult,
    ValidationMessage,
)
from gao_dev.sandbox.benchmark.config import (
    BenchmarkConfig,
    SuccessCriteria,
    WorkflowPhaseConfig,
)


class TestValidationMessage:
    """Tests for ValidationMessage."""

    def test_error_message_format(self):
        """Test error message formatting."""
        msg = ValidationMessage(
            level="error",
            field="test_field",
            message="Test error",
            current_value=10,
            expected_value=20,
            suggestion="Fix it",
        )

        result = str(msg)
        assert "[ERROR]" in result
        assert "test_field:" in result
        assert "Test error" in result
        assert "(current: 10)" in result
        assert "(expected: 20)" in result
        assert "-> Fix it" in result

    def test_warning_message_format(self):
        """Test warning message formatting."""
        msg = ValidationMessage(
            level="warning", field="field", message="Warning message"
        )

        result = str(msg)
        assert "[WARNING]" in result
        assert "field:" in result
        assert "Warning message" in result

    def test_info_message_format(self):
        """Test info message formatting."""
        msg = ValidationMessage(level="info", field="", message="Info message")

        result = str(msg)
        assert "[INFO]" in result
        assert "Info message" in result


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_default_valid(self):
        """Test that default result is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.info == []

    def test_add_error(self):
        """Test adding error message."""
        result = ValidationResult()
        result.add_error("field", "Error message", current_value=5)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].level == "error"
        assert result.errors[0].field == "field"
        assert result.errors[0].message == "Error message"
        assert result.errors[0].current_value == 5

    def test_add_warning(self):
        """Test adding warning message."""
        result = ValidationResult()
        result.add_warning("field", "Warning message")

        assert result.is_valid is True  # Warnings don't invalidate
        assert len(result.warnings) == 1
        assert result.warnings[0].level == "warning"

    def test_add_info(self):
        """Test adding info message."""
        result = ValidationResult()
        result.add_info("field", "Info message")

        assert result.is_valid is True
        assert len(result.info) == 1
        assert result.info[0].level == "info"

    def test_string_format_with_errors(self):
        """Test string formatting with errors."""
        result = ValidationResult()
        result.add_error("field1", "Error 1")
        result.add_error("field2", "Error 2")

        output = str(result)
        assert "ERRORS:" in output
        assert "Error 1" in output
        assert "Error 2" in output

    def test_string_format_with_warnings(self):
        """Test string formatting with warnings."""
        result = ValidationResult()
        result.add_warning("field", "Warning message")

        output = str(result)
        assert "WARNINGS:" in output
        assert "Warning message" in output

    def test_string_format_valid(self):
        """Test string formatting when valid."""
        result = ValidationResult()

        output = str(result)
        assert output == "Configuration is valid."


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_validator_creation(self):
        """Test creating validator."""
        validator = ConfigValidator()
        assert validator.MAX_TIMEOUT_SECONDS == 86400
        assert validator.RECOMMENDED_MAX_TIMEOUT == 14400

    def test_valid_config_passes(self):
        """Test that a valid config passes validation."""
        config = BenchmarkConfig(
            name="test",
            description="Test benchmark",
            boilerplate_url="https://github.com/user/template",
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_name_fails(self):
        """Test that missing name causes error."""
        config = BenchmarkConfig(
            name="", description="Test", boilerplate_url="https://github.com/user/repo"
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("name" in e.field for e in result.errors)

    def test_missing_description_fails(self):
        """Test that missing description causes error."""
        config = BenchmarkConfig(
            name="test", description="", boilerplate_url="https://github.com/user/repo"
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("description" in e.field for e in result.errors)

    def test_missing_boilerplate_fails(self):
        """Test that missing boilerplate causes error."""
        config = BenchmarkConfig(name="test", description="Test")

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("boilerplate" in e.field for e in result.errors)

    def test_invalid_timeout_fails(self):
        """Test that invalid timeout causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            timeout_seconds=0,
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("timeout_seconds" in e.field for e in result.errors)

    def test_timeout_exceeds_maximum_fails(self):
        """Test that timeout exceeding max causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            timeout_seconds=100000,  # > 86400
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("timeout_seconds" in e.field for e in result.errors)

    def test_invalid_url_format_fails(self):
        """Test that invalid URL format causes error."""
        config = BenchmarkConfig(
            name="test", description="Test", boilerplate_url="not-a-valid-url"
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("boilerplate_url" in e.field for e in result.errors)

    def test_nonexistent_path_warns(self):
        """Test that nonexistent path generates warning."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_path=Path("/nonexistent/path"),
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        # Should be valid but with warning
        assert result.is_valid is True
        assert any("boilerplate_path" in w.field for w in result.warnings)

    def test_invalid_test_coverage_fails(self):
        """Test that invalid test coverage causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            success_criteria=SuccessCriteria(min_test_coverage=101.0),
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("min_test_coverage" in e.field for e in result.errors)

    def test_negative_interventions_fails(self):
        """Test that negative interventions causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            success_criteria=SuccessCriteria(max_manual_interventions=-1),
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("max_manual_interventions" in e.field for e in result.errors)

    def test_negative_errors_fails(self):
        """Test that negative errors causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            success_criteria=SuccessCriteria(max_errors=-1),
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("max_errors" in e.field for e in result.errors)

    def test_invalid_phase_name_fails(self):
        """Test that invalid phase name causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            workflow_phases=[WorkflowPhaseConfig(phase_name="")],
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("workflow_phases" in e.field for e in result.errors)

    def test_invalid_phase_timeout_fails(self):
        """Test that invalid phase timeout causes error."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            workflow_phases=[WorkflowPhaseConfig(phase_name="test", timeout_seconds=0)],
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert any("workflow_phases" in e.field for e in result.errors)

    def test_long_timeout_warns(self):
        """Test that long timeout generates warning."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
            timeout_seconds=20000,  # > 14400 but < 86400
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True
        assert any("timeout_seconds" in w.field for w in result.warnings)

    def test_no_phases_informs(self):
        """Test that no phases generates info message."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True
        assert any("workflow_phases" in i.field for i in result.info)

    def test_multiple_errors_reported(self):
        """Test that multiple errors are all reported."""
        config = BenchmarkConfig(
            name="",  # Missing name
            description="",  # Missing description
            timeout_seconds=-1,  # Invalid timeout
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is False
        assert len(result.errors) >= 3  # At least these 3 errors

    def test_https_url_valid(self):
        """Test that https:// URL is valid."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="https://github.com/user/repo",
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True

    def test_http_url_valid(self):
        """Test that http:// URL is valid."""
        config = BenchmarkConfig(
            name="test", description="Test", boilerplate_url="http://example.com/repo"
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True

    def test_git_ssh_url_valid(self):
        """Test that git@ SSH URL is valid."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="git@github.com:user/repo.git",
        )

        validator = ConfigValidator()
        result = validator.validate_config(config)

        assert result.is_valid is True
