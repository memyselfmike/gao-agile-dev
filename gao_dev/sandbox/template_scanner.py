"""Template variable detection in boilerplate projects."""

import re
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# Variable patterns
DOUBLE_BRACE_PATTERN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")
DOUBLE_UNDERSCORE_PATTERN = re.compile(r"__([A-Z_][A-Z0-9_]*)__")

# File extensions to scan
TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".sh",
    ".bash",
    ".toml",
    ".ini",
    ".cfg",
    ".xml",
}

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".coverage",
    "htmlcov",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
}

# Files to ignore
IGNORE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
}


@dataclass
class TemplateVariable:
    """Represents a detected template variable."""

    name: str
    format: str  # 'double_brace' or 'double_underscore'
    locations: List[str] = field(default_factory=list)
    required: bool = True

    def __post_init__(self):
        """Ensure locations is a list."""
        if not isinstance(self.locations, list):
            self.locations = list(self.locations)


class TemplateScanner:
    """
    Scans boilerplate projects for template variables.

    Detects variables in two formats:
    - {{variable_name}} - double brace format
    - __VARIABLE_NAME__ - double underscore format

    Efficiently scans text files while ignoring binary files,
    dependencies, and common build artifacts.
    """

    def __init__(self):
        """Initialize template scanner."""
        self.text_extensions = TEXT_EXTENSIONS
        self.ignore_dirs = IGNORE_DIRS
        self.ignore_files = IGNORE_FILES

    def scan_project(self, project_path: Path) -> List[TemplateVariable]:
        """
        Scan project for template variables.

        Walks the project directory tree, scans text files for
        template variables, and returns deduplicated results with
        file location metadata.

        Args:
            project_path: Root directory of boilerplate project

        Returns:
            List of detected template variables with metadata
        """
        project_path = Path(project_path).resolve()

        if not project_path.exists():
            logger.warning("project_path_not_found", path=str(project_path))
            return []

        logger.info("scanning_project", path=str(project_path))

        # Track variables and their locations
        variables_dict: Dict[tuple, TemplateVariable] = {}

        # Walk directory tree
        file_count = 0
        for file_path in self._walk_project(project_path):
            if not self.is_text_file(file_path):
                continue

            try:
                # Scan file for variables
                found_vars = self.scan_file(file_path)

                if found_vars:
                    file_count += 1
                    # Get relative path for cleaner reporting
                    rel_path = str(file_path.relative_to(project_path))

                    # Add to variables dict
                    for var_name, var_format in found_vars:
                        key = (var_name, var_format)
                        if key not in variables_dict:
                            variables_dict[key] = TemplateVariable(
                                name=var_name,
                                format=var_format,
                                locations=[rel_path],
                            )
                        else:
                            if rel_path not in variables_dict[key].locations:
                                variables_dict[key].locations.append(rel_path)

            except Exception as e:
                logger.warning(
                    "file_scan_error",
                    file=str(file_path),
                    error=str(e),
                )
                continue

        # Convert to list and sort by name
        result = sorted(variables_dict.values(), key=lambda v: v.name)

        logger.info(
            "scan_complete",
            variables_found=len(result),
            files_scanned=file_count,
        )

        return result

    def scan_file(self, file_path: Path) -> Set[tuple]:
        """
        Scan single file for template variables.

        Args:
            file_path: Path to file to scan

        Returns:
            Set of (variable_name, format) tuples found in file
        """
        variables = set()

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find double brace variables {{VAR}}
            for match in DOUBLE_BRACE_PATTERN.finditer(content):
                var_name = match.group(1)
                variables.add((var_name, "double_brace"))

            # Find double underscore variables __VAR__
            for match in DOUBLE_UNDERSCORE_PATTERN.finditer(content):
                var_name = match.group(1)
                variables.add((var_name, "double_underscore"))

        except Exception as e:
            logger.debug(
                "file_read_error",
                file=str(file_path),
                error=str(e),
            )
            return set()

        return variables

    def is_text_file(self, file_path: Path) -> bool:
        """
        Check if file should be scanned for variables.

        Checks file extension against whitelist of text file types.
        Also checks file size to skip very large files.

        Args:
            file_path: Path to check

        Returns:
            True if file should be scanned, False otherwise
        """
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return False

        # Check if in ignore list
        if file_path.name in self.ignore_files:
            return False

        # Check extension
        if file_path.suffix.lower() not in self.text_extensions:
            return False

        # Check file size (skip files > 1MB)
        try:
            if file_path.stat().st_size > 1_000_000:
                logger.debug("skipping_large_file", file=str(file_path))
                return False
        except Exception:
            return False

        return True

    def _walk_project(self, project_path: Path):
        """
        Walk project directory tree, yielding file paths.

        Skips ignored directories for efficiency.

        Args:
            project_path: Root directory to walk

        Yields:
            Path objects for each file
        """
        try:
            for item in project_path.rglob("*"):
                # Skip if any parent directory is in ignore list
                if any(part in self.ignore_dirs for part in item.parts):
                    continue

                if item.is_file():
                    yield item

        except Exception as e:
            logger.error(
                "walk_error",
                path=str(project_path),
                error=str(e),
            )

    def get_variables_by_format(
        self, variables: List[TemplateVariable], format: str
    ) -> List[TemplateVariable]:
        """
        Filter variables by format.

        Args:
            variables: List of template variables
            format: Format to filter by ('double_brace' or 'double_underscore')

        Returns:
            Filtered list of variables
        """
        return [v for v in variables if v.format == format]

    def get_common_variables(self, variables: List[TemplateVariable]) -> List[str]:
        """
        Get list of common variable names that should typically be provided.

        Args:
            variables: List of detected variables

        Returns:
            List of common variable names found
        """
        common_names = {
            "PROJECT_NAME",
            "project_name",
            "PROJECT_DESCRIPTION",
            "project_description",
            "AUTHOR",
            "author",
            "LICENSE",
            "license",
            "YEAR",
            "year",
            "VERSION",
            "version",
        }

        return [v.name for v in variables if v.name in common_names]
