"""Boilerplate integration validation."""

import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from enum import Enum

import structlog
import yaml

from .template_scanner import TemplateScanner

logger = structlog.get_logger(__name__)


class ValidationLevel(Enum):
    """Severity of validation issue."""

    ERROR = "error"  # Critical issue, project won't work
    WARNING = "warning"  # Non-critical issue
    INFO = "info"  # Informational message


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    level: ValidationLevel
    category: str  # 'structure', 'dependencies', 'config', 'health'
    message: str
    fix_suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report."""

    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0

    def __post_init__(self):
        """Calculate counts."""
        self.warnings_count = sum(
            1 for i in self.issues if i.level == ValidationLevel.WARNING
        )
        self.errors_count = sum(
            1 for i in self.issues if i.level == ValidationLevel.ERROR
        )
        self.passed = self.errors_count == 0


class BoilerplateValidator:
    """
    Validates boilerplate integration completeness and correctness.

    Checks project structure, dependencies, configuration,
    and performs basic health checks.
    """

    def __init__(self):
        """Initialize validator."""
        self.scanner = TemplateScanner()

    def validate_project(self, project_path: Path) -> ValidationReport:
        """
        Run complete validation on sandbox project.

        Args:
            project_path: Root directory of sandbox project

        Returns:
            ValidationReport with all issues found
        """
        project_path = Path(project_path).resolve()

        logger.info("validating_project", project_path=str(project_path))

        issues = []

        # Run all validation checks
        issues.extend(self.validate_structure(project_path))
        issues.extend(self.validate_dependencies(project_path))
        issues.extend(self.validate_configuration(project_path))
        issues.extend(self.run_health_check(project_path))

        # Create report
        report = ValidationReport(
            passed=True,  # Will be recalculated in __post_init__
            issues=issues,
        )

        logger.info(
            "validation_complete",
            passed=report.passed,
            warnings=report.warnings_count,
            errors=report.errors_count,
        )

        return report

    def validate_structure(self, project_path: Path) -> List[ValidationIssue]:
        """
        Validate directory structure and key files.

        Args:
            project_path: Project directory

        Returns:
            List of validation issues
        """
        issues = []

        # Check for common project files
        expected_files = {
            "README.md": "README file missing",
            ".gitignore": ".gitignore file missing",
        }

        for file, message in expected_files.items():
            if not (project_path / file).exists():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="structure",
                        message=message,
                        fix_suggestion=f"Create {file} file",
                    )
                )

        # Check for project configuration
        has_config = any(
            (project_path / f).exists()
            for f in ["package.json", "pyproject.toml", "Cargo.toml", "go.mod"]
        )

        if not has_config:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message="No project configuration file found",
                    fix_suggestion="Create package.json, pyproject.toml, or similar",
                )
            )

        # Check for .git directory conflicts
        if (project_path / ".git").exists():
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="structure",
                    message=".git directory found (should be removed after cloning)",
                    fix_suggestion="Remove .git directory from boilerplate",
                )
            )

        # Check for unsubstituted template variables
        unsubstituted = self.check_for_template_residue(project_path)
        if unsubstituted:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message=f"Unsubstituted template variables found: {', '.join(unsubstituted[:5])}",
                    fix_suggestion="Run variable substitution before validation",
                )
            )

        return issues

    def validate_dependencies(self, project_path: Path) -> List[ValidationIssue]:
        """
        Validate dependencies installed correctly.

        Args:
            project_path: Project directory

        Returns:
            List of validation issues
        """
        issues = []

        # Check Node.js dependencies
        if (project_path / "package.json").exists():
            if not (project_path / "node_modules").exists():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="dependencies",
                        message="node_modules directory not found",
                        fix_suggestion="Run npm/yarn/pnpm install",
                    )
                )

            # Check for lockfile
            has_lockfile = any(
                (project_path / f).exists()
                for f in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"]
            )

            if not has_lockfile:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        category="dependencies",
                        message="No package lockfile found",
                        fix_suggestion="Generate lockfile with package manager",
                    )
                )

        # Check Python dependencies
        if (project_path / "requirements.txt").exists() or (
            project_path / "pyproject.toml"
        ).exists():
            has_venv = any(
                (project_path / d).exists() for d in [".venv", "venv", "env"]
            )

            if not has_venv:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        category="dependencies",
                        message="No virtual environment directory found",
                        fix_suggestion="Create virtual environment and install dependencies",
                    )
                )

        return issues

    def validate_configuration(self, project_path: Path) -> List[ValidationIssue]:
        """
        Validate configuration files.

        Args:
            project_path: Project directory

        Returns:
            List of validation issues
        """
        issues = []

        # Validate JSON files
        for json_file in project_path.rglob("*.json"):
            # Skip node_modules and hidden directories
            if any(part.startswith(".") for part in json_file.parts):
                continue
            if "node_modules" in json_file.parts:
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="config",
                        message=f"Invalid JSON in {json_file.name}: {str(e)}",
                        fix_suggestion="Fix JSON syntax errors",
                    )
                )

        # Validate YAML files
        for yaml_file in project_path.rglob("*.yaml"):
            if any(part.startswith(".") for part in yaml_file.parts):
                continue
            if "node_modules" in yaml_file.parts:
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="config",
                        message=f"Invalid YAML in {yaml_file.name}: {str(e)}",
                        fix_suggestion="Fix YAML syntax errors",
                    )
                )

        # Check for .env.example but no .env
        if (project_path / ".env.example").exists():
            if not (project_path / ".env").exists():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="config",
                        message=".env.example present but .env missing",
                        fix_suggestion="Copy .env.example to .env and configure",
                    )
                )

        return issues

    def run_health_check(self, project_path: Path) -> List[ValidationIssue]:
        """
        Run project-specific health checks.

        Args:
            project_path: Project directory

        Returns:
            List of validation issues
        """
        issues = []

        # Basic readiness check
        has_source = any(
            (project_path / d).exists() for d in ["src", "lib", "app", "components"]
        )

        if not has_source:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="health",
                    message="No source code directory found (src/, lib/, app/)",
                    fix_suggestion="Verify project structure",
                )
            )

        return issues

    def check_for_template_residue(self, project_path: Path) -> List[str]:
        """
        Find any unsubstituted template variables.

        Args:
            project_path: Project directory

        Returns:
            List of unsubstituted variable names
        """
        try:
            variables = self.scanner.scan_project(project_path)
            return [v.name for v in variables]
        except Exception as e:
            logger.warning("template_scan_failed", error=str(e))
            return []

    def format_report(self, report: ValidationReport) -> str:
        """
        Format validation report as readable text.

        Args:
            report: ValidationReport

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(" Boilerplate Validation Report")
        lines.append("=" * 80)
        lines.append("")

        # Group issues by category
        categories = {}
        for issue in report.issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)

        # Print each category
        for category in ["structure", "dependencies", "config", "health"]:
            if category not in categories:
                lines.append(f"{category.title()}: OK")
                lines.append("")
                continue

            lines.append(f"{category.title()}:")
            for issue in categories[category]:
                symbol = "ERROR" if issue.level == ValidationLevel.ERROR else "WARN"
                lines.append(f"  [{symbol}] {issue.message}")
                if issue.fix_suggestion:
                    lines.append(f"         Fix: {issue.fix_suggestion}")
            lines.append("")

        # Summary
        lines.append("=" * 80)
        lines.append(
            f"Summary: {report.warnings_count} warnings, {report.errors_count} errors"
        )
        status = "READY" if report.passed else "NOT READY"
        lines.append(f"Status: {status}")
        lines.append("=" * 80)

        return "\n".join(lines)
