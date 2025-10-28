"""Benchmark configuration validation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import BenchmarkConfig, SuccessCriteria, WorkflowPhaseConfig


@dataclass
class ValidationMessage:
    """A single validation message."""

    level: str  # "error", "warning", "info"
    field: str
    message: str
    current_value: Any = None
    expected_value: Any = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format message for display."""
        parts = [f"[{self.level.upper()}]"]
        if self.field:
            parts.append(f"{self.field}:")
        parts.append(self.message)
        if self.current_value is not None:
            parts.append(f"(current: {self.current_value})")
        if self.expected_value is not None:
            parts.append(f"(expected: {self.expected_value})")
        if self.suggestion:
            parts.append(f"-> {self.suggestion}")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool = True
    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    info: List[ValidationMessage] = field(default_factory=list)

    def add_error(self, field: str, message: str, **kwargs) -> None:
        """Add an error message."""
        self.errors.append(
            ValidationMessage(level="error", field=field, message=message, **kwargs)
        )
        self.is_valid = False

    def add_warning(self, field: str, message: str, **kwargs) -> None:
        """Add a warning message."""
        self.warnings.append(
            ValidationMessage(level="warning", field=field, message=message, **kwargs)
        )

    def add_info(self, field: str, message: str, **kwargs) -> None:
        """Add an info message."""
        self.info.append(
            ValidationMessage(level="info", field=field, message=message, **kwargs)
        )

    def __str__(self) -> str:
        """Format for display."""
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            lines.extend([f"  {e}" for e in self.errors])
        if self.warnings:
            lines.append("WARNINGS:")
            lines.extend([f"  {w}" for w in self.warnings])
        if self.info:
            lines.append("INFO:")
            lines.extend([f"  {i}" for i in self.info])
        return "\n".join(lines) if lines else "Configuration is valid."


class ConfigValidator:
    """Validates benchmark configurations."""

    MAX_TIMEOUT_SECONDS = 86400  # 24 hours
    RECOMMENDED_MAX_TIMEOUT = 14400  # 4 hours

    def validate_config(self, config: BenchmarkConfig) -> ValidationResult:
        """
        Validate complete benchmark configuration.

        Args:
            config: Benchmark configuration to validate

        Returns:
            ValidationResult with errors, warnings, and info
        """
        result = ValidationResult()

        # Validate required fields
        self._validate_required_fields(config, result)

        # Validate field types and ranges
        self._validate_field_types(config, result)

        # Validate semantic constraints
        self._validate_semantic_constraints(config, result)

        # Validate success criteria
        self._validate_success_criteria(config.success_criteria, result)

        # Validate workflow phases
        self._validate_workflow_phases(config.workflow_phases, result)

        # Add warnings for best practices
        self._add_warnings(config, result)

        return result

    def _validate_required_fields(
        self, config: BenchmarkConfig, result: ValidationResult
    ) -> None:
        """Validate that required fields are present."""
        if not config.name:
            result.add_error("name", "Benchmark name is required")
        if not config.description:
            result.add_error("description", "Benchmark description is required")
        # Boilerplate is optional for greenfield benchmarks
        if not config.boilerplate_url and not config.boilerplate_path:
            result.add_info(
                "boilerplate",
                "No boilerplate specified - will start from empty project (greenfield)",
                suggestion="For faster setup, consider providing a boilerplate template",
            )

    def _validate_field_types(
        self, config: BenchmarkConfig, result: ValidationResult
    ) -> None:
        """Validate field types and ranges."""
        if config.timeout_seconds <= 0:
            result.add_error(
                "timeout_seconds",
                "Timeout must be positive",
                current_value=config.timeout_seconds,
                expected_value="> 0",
            )
        elif config.timeout_seconds > self.MAX_TIMEOUT_SECONDS:
            result.add_error(
                "timeout_seconds",
                f"Timeout exceeds maximum of {self.MAX_TIMEOUT_SECONDS}s (24 hours)",
                current_value=config.timeout_seconds,
            )

    def _validate_semantic_constraints(
        self, config: BenchmarkConfig, result: ValidationResult
    ) -> None:
        """Validate semantic constraints."""
        # Validate boilerplate URL if provided
        if config.boilerplate_url:
            # Basic URL validation - check if it looks like a URL
            url = config.boilerplate_url
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("git@")):
                result.add_error(
                    "boilerplate_url",
                    "Invalid URL format",
                    current_value=config.boilerplate_url,
                    suggestion="URL should start with http://, https://, or git@",
                )

        # Validate boilerplate path if provided
        if config.boilerplate_path:
            if not Path(config.boilerplate_path).exists():
                result.add_warning(
                    "boilerplate_path",
                    "Boilerplate path does not exist",
                    current_value=config.boilerplate_path,
                    suggestion="Path will be created during initialization",
                )

    def _validate_success_criteria(
        self, criteria: SuccessCriteria, result: ValidationResult
    ) -> None:
        """Validate success criteria."""
        if not (0 <= criteria.min_test_coverage <= 100):
            result.add_error(
                "success_criteria.min_test_coverage",
                "Test coverage must be between 0 and 100",
                current_value=criteria.min_test_coverage,
            )

        if criteria.max_manual_interventions < 0:
            result.add_error(
                "success_criteria.max_manual_interventions",
                "Cannot be negative",
                current_value=criteria.max_manual_interventions,
            )

        if criteria.max_errors < 0:
            result.add_error(
                "success_criteria.max_errors",
                "Cannot be negative",
                current_value=criteria.max_errors,
            )

    def _validate_workflow_phases(
        self, phases: List[WorkflowPhaseConfig], result: ValidationResult
    ) -> None:
        """Validate workflow phase configurations."""
        for i, phase in enumerate(phases):
            prefix = f"workflow_phases[{i}]"

            if not phase.phase_name:
                result.add_error(f"{prefix}.phase_name", "Phase name is required")

            if phase.timeout_seconds <= 0:
                result.add_error(
                    f"{prefix}.timeout_seconds",
                    "Phase timeout must be positive",
                    current_value=phase.timeout_seconds,
                )

    def _add_warnings(self, config: BenchmarkConfig, result: ValidationResult) -> None:
        """Add warnings for best practices."""
        # Warn if timeout is very long
        if config.timeout_seconds > self.RECOMMENDED_MAX_TIMEOUT:
            result.add_warning(
                "timeout_seconds",
                f"Timeout is longer than recommended maximum of {self.RECOMMENDED_MAX_TIMEOUT}s (4 hours)",
                current_value=config.timeout_seconds,
                suggestion="Consider breaking into smaller benchmarks",
            )

        # Warn if no workflow phases defined
        if not config.workflow_phases:
            result.add_info(
                "workflow_phases",
                "No workflow phases defined - will run entire workflow",
                suggestion="Consider defining phases for better progress tracking",
            )
