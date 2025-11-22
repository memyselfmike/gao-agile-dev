"""Artifact verification for benchmark runs."""

import ast
import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
import structlog

logger = structlog.get_logger()


@dataclass
class ArtifactCheck:
    """Result of checking a single artifact."""

    path: str
    exists: bool = False
    size: int = 0
    valid: bool = False
    error: str = ""


@dataclass
class VerificationResult:
    """Result of verifying artifacts for a phase."""

    phase: str
    expected_count: int
    found_count: int
    valid_count: int
    results: List[ArtifactCheck] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if verification succeeded."""
        return self.found_count > 0 and self.valid_count == self.found_count


class ArtifactVerifier:
    """
    Verifies that expected artifacts were created correctly.

    Checks:
    - File existence
    - File is not empty
    - Content is valid (basic syntax checks)
    """

    def __init__(self, project_root: Path):
        """
        Initialize artifact verifier.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.logger = logger.bind(component="ArtifactVerifier")

    def verify_artifacts(
        self, artifact_paths: List[str], phase: str
    ) -> VerificationResult:
        """
        Verify a list of artifacts.

        Args:
            artifact_paths: List of file paths to verify
            phase: Phase name for context

        Returns:
            VerificationResult with check details
        """
        results = []

        for path in artifact_paths:
            check = self._verify_artifact(path)
            results.append(check)

        found_count = sum(1 for r in results if r.exists)
        valid_count = sum(1 for r in results if r.valid)

        result = VerificationResult(
            phase=phase,
            expected_count=len(artifact_paths),
            found_count=found_count,
            valid_count=valid_count,
            results=results,
        )

        self.logger.info(
            "artifacts_verified",
            phase=phase,
            expected=result.expected_count,
            found=result.found_count,
            valid=result.valid_count,
            success=result.success,
        )

        return result

    def _verify_artifact(self, path: str) -> ArtifactCheck:
        """
        Verify a single artifact.

        Args:
            path: File path relative to project root

        Returns:
            ArtifactCheck with verification details
        """
        check = ArtifactCheck(path=path)
        full_path = self.project_root / path

        # Check if file exists
        if not full_path.exists():
            check.error = "File does not exist"
            return check

        check.exists = True

        # Check file size
        try:
            check.size = full_path.stat().st_size
        except Exception as e:
            check.error = f"Cannot read file stats: {e}"
            return check

        # Check if file is empty
        if check.size == 0:
            check.error = "File is empty"
            return check

        # Validate content based on file type
        try:
            content = full_path.read_text(encoding="utf-8")
            check.valid = self._validate_content(path, content)

            if not check.valid:
                check.error = "Content validation failed"

        except UnicodeDecodeError:
            # Binary file or encoding issue
            check.valid = True  # Accept binary files
            check.error = ""
        except Exception as e:
            check.error = f"Failed to read content: {e}"
            return check

        return check

    def _validate_content(self, path: str, content: str) -> bool:
        """
        Validate file content based on file type.

        Args:
            path: File path (for extension detection)
            content: File content

        Returns:
            True if content is valid
        """
        suffix = Path(path).suffix.lower()

        # Python files
        if suffix == ".py":
            return self._validate_python(content)

        # Markdown files
        elif suffix in [".md", ".markdown"]:
            return self._validate_markdown(content)

        # JSON files
        elif suffix == ".json":
            return self._validate_json(content)

        # YAML files
        elif suffix in [".yaml", ".yml"]:
            return self._validate_yaml(content)

        # For other files, just check non-empty
        return len(content.strip()) > 0

    def _validate_python(self, content: str) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def _validate_markdown(self, content: str) -> bool:
        """Validate Markdown (basic check)."""
        # Just check it's not empty and has some structure
        return len(content.strip()) > 0 and len(content.split("\n")) > 1

    def _validate_json(self, content: str) -> bool:
        """Validate JSON syntax."""
        try:
            json.loads(content)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def _validate_yaml(self, content: str) -> bool:
        """Validate YAML syntax."""
        try:
            yaml.safe_load(content)
            return True
        except yaml.YAMLError:
            return False
