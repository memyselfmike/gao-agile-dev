"""Template variable substitution engine."""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import structlog

from .exceptions import SandboxError
from .template_scanner import TemplateScanner, TEXT_EXTENSIONS, IGNORE_DIRS

logger = structlog.get_logger(__name__)

# Variable patterns for substitution
DOUBLE_BRACE_PATTERN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")
DOUBLE_UNDERSCORE_PATTERN = re.compile(r"__([A-Z_][A-Z0-9_]*)__")

# Value validation pattern (alphanumeric, hyphens, underscores, spaces, dots)
VALUE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-\s_.]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$")


class SubstitutionError(SandboxError):
    """Raised when substitution fails."""

    pass


@dataclass
class SubstitutionResult:
    """Result of variable substitution operation."""

    files_modified: int = 0
    variables_substituted: int = 0
    unsubstituted_variables: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    success: bool = True


class TemplateSubstitutor:
    """
    Performs template variable substitution in boilerplate projects.

    Substitutes template variables in two formats:
    - {{variable_name}} - double brace format
    - __VARIABLE_NAME__ - double underscore format

    Validates values, preserves file encodings, and provides
    comprehensive error reporting.
    """

    # Common default variables
    DEFAULT_VARIABLES = {
        "PROJECT_DESCRIPTION": "A GAO-Dev sandbox project",
        "AUTHOR": "GAO-Dev",
        "LICENSE": "MIT",
        "YEAR": str(datetime.now().year),
    }

    def __init__(self):
        """Initialize template substitutor."""
        self.scanner = TemplateScanner()

    def substitute_variables(
        self,
        project_path: Path,
        variables: Dict[str, str],
        create_backup: bool = False,
    ) -> SubstitutionResult:
        """
        Substitute template variables in project files.

        Args:
            project_path: Root directory of project
            variables: Dictionary mapping variable names to values
            create_backup: Whether to backup files before substitution

        Returns:
            SubstitutionResult with operation details

        Raises:
            SubstitutionError: If substitution fails critically
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            raise SubstitutionError(f"Project path does not exist: {project_path}")

        logger.info("starting_substitution", project_path=str(project_path))

        # Merge with defaults
        all_variables = {**self.DEFAULT_VARIABLES, **variables}

        # Validate all values
        validation_errors = []
        for name, value in all_variables.items():
            if not self.validate_value(value):
                validation_errors.append(
                    f"Invalid value for '{name}': '{value}' "
                    f"(must contain only alphanumeric, hyphens, underscores, spaces, dots)"
                )

        if validation_errors:
            return SubstitutionResult(
                errors=validation_errors,
                success=False,
            )

        # Scan for template variables
        detected_vars = self.scanner.scan_project(project_path)

        # Check for required variables
        detected_names = {v.name for v in detected_vars}
        provided_names = set(all_variables.keys())
        missing_vars = detected_names - provided_names

        if missing_vars:
            logger.warning(
                "missing_variables",
                missing=list(missing_vars),
            )

        # Perform substitution
        result = SubstitutionResult()
        files_to_process = list(self._get_text_files(project_path))

        for file_path in files_to_process:
            try:
                # Create backup if requested
                if create_backup:
                    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
                    shutil.copy2(file_path, backup_path)

                # Substitute in file
                subs_made = self.substitute_in_file(file_path, all_variables)

                if subs_made > 0:
                    result.files_modified += 1
                    result.variables_substituted += subs_made

            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                result.errors.append(error_msg)
                logger.error("substitution_error", file=str(file_path), error=str(e))

        # Check for unsubstituted variables
        unsubstituted = self._find_unsubstituted_variables(project_path)
        result.unsubstituted_variables = unsubstituted

        # Determine success
        result.success = len(result.errors) == 0

        logger.info(
            "substitution_complete",
            files_modified=result.files_modified,
            variables_substituted=result.variables_substituted,
            unsubstituted=len(result.unsubstituted_variables),
            errors=len(result.errors),
        )

        return result

    def substitute_in_file(
        self,
        file_path: Path,
        variables: Dict[str, str],
    ) -> int:
        """
        Substitute variables in a single file.

        Args:
            file_path: Path to file
            variables: Variable name -> value mapping

        Returns:
            Number of substitutions made
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            original_content = content
            total_subs = 0

            # Substitute double brace variables {{VAR}}
            def replace_brace(match):
                nonlocal total_subs
                var_name = match.group(1)
                if var_name in variables:
                    total_subs += 1
                    return variables[var_name]
                return match.group(0)  # Leave unchanged

            content = DOUBLE_BRACE_PATTERN.sub(replace_brace, content)

            # Substitute double underscore variables __VAR__
            def replace_underscore(match):
                nonlocal total_subs
                var_name = match.group(1)
                if var_name in variables:
                    total_subs += 1
                    return variables[var_name]
                return match.group(0)  # Leave unchanged

            content = DOUBLE_UNDERSCORE_PATTERN.sub(replace_underscore, content)

            # Write back only if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return total_subs

        except Exception as e:
            logger.debug(
                "file_substitution_error",
                file=str(file_path),
                error=str(e),
            )
            raise

    def validate_value(self, value: str) -> bool:
        """
        Validate substitution value format.

        Values must:
        - Not be empty
        - Start and end with alphanumeric
        - Contain only: alphanumeric, hyphens, underscores, spaces, dots

        Args:
            value: Value to validate

        Returns:
            True if valid, False otherwise
        """
        if not value or not isinstance(value, str):
            return False

        # Allow empty string as a special case
        if value == "":
            return False

        # Check pattern
        return VALUE_PATTERN.match(value) is not None

    def rollback_substitution(self, project_path: Path) -> bool:
        """
        Rollback substitution using backup files.

        Restores all .bak files and removes them after restoration.

        Args:
            project_path: Project root directory

        Returns:
            True if rollback successful, False otherwise
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            return False

        logger.info("rolling_back_substitution", project_path=str(project_path))

        restored_count = 0
        try:
            for backup_file in project_path.rglob("*.bak"):
                # Get original file path
                original_file = backup_file.with_suffix("")

                # Restore from backup
                shutil.copy2(backup_file, original_file)
                backup_file.unlink()  # Remove backup
                restored_count += 1

            logger.info("rollback_complete", files_restored=restored_count)
            return True

        except Exception as e:
            logger.error("rollback_failed", error=str(e))
            return False

    def _get_text_files(self, project_path: Path):
        """
        Get all text files to process for substitution.

        Args:
            project_path: Root directory

        Yields:
            Path objects for text files
        """
        for file_path in project_path.rglob("*"):
            # Skip ignored directories
            if any(part in IGNORE_DIRS for part in file_path.parts):
                continue

            # Skip backup files
            if file_path.suffix == ".bak":
                continue

            # Check if text file
            if file_path.is_file() and file_path.suffix.lower() in TEXT_EXTENSIONS:
                # Skip large files
                try:
                    if file_path.stat().st_size < 1_000_000:
                        yield file_path
                except Exception:
                    continue

    def _find_unsubstituted_variables(self, project_path: Path) -> List[str]:
        """
        Find any remaining unsubstituted variables.

        Args:
            project_path: Project root directory

        Returns:
            List of unsubstituted variable names
        """
        remaining_vars = self.scanner.scan_project(project_path)
        return [v.name for v in remaining_vars]
