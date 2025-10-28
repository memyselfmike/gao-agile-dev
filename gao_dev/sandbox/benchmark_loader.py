"""
Benchmark configuration loading and validation.

This module handles parsing benchmark YAML files and extracting
the information needed for auto-generated run IDs and scientific tracking.
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import SandboxError


class BenchmarkError(SandboxError):
    """Raised when benchmark configuration is invalid."""


class BenchmarkConfig:
    """
    Represents a parsed benchmark configuration.

    Attributes:
        name: Unique benchmark identifier (e.g., 'todo-app-baseline')
        version: Semantic version (e.g., '1.0.0')
        description: Human-readable description
        initial_prompt: The standardized prompt (IMMUTABLE)
        prompt_hash: SHA256 hash of initial_prompt for verification
        complexity_level: 1 (Simple), 2 (Medium), or 3 (High)
        estimated_duration_minutes: Expected time to complete
        tech_stack: Dictionary of technology choices
        success_criteria: List of success criteria
        expected_outcomes: Expected metrics (interventions, time, etc.)
        phases: Optional list of expected phase durations
        raw_config: Complete parsed YAML
    """

    def __init__(self, config: Dict[str, Any], file_path: Path):
        """
        Initialize benchmark config from parsed YAML.

        Args:
            config: Parsed YAML dictionary
            file_path: Path to the benchmark file

        Raises:
            BenchmarkError: If required fields missing or invalid
        """
        self.file_path = file_path
        self.raw_config = config

        # Validate structure
        if "benchmark" not in config:
            raise BenchmarkError(f"Missing 'benchmark' section in {file_path}")

        benchmark = config["benchmark"]

        # Extract required fields
        self.name = self._get_required_field(benchmark, "name", str)
        self.version = self._get_required_field(benchmark, "version", str)
        self.description = self._get_required_field(benchmark, "description", str)
        self.initial_prompt = self._get_required_field(benchmark, "initial_prompt", str)
        self.complexity_level = self._get_required_field(benchmark, "complexity_level", int)
        self.estimated_duration_minutes = self._get_required_field(
            benchmark, "estimated_duration_minutes", int
        )

        # Validate name format (must be valid for use in project names)
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", self.name):
            raise BenchmarkError(
                f"Benchmark name '{self.name}' must be lowercase alphanumeric with hyphens"
            )

        # Validate complexity level
        if self.complexity_level not in [1, 2, 3]:
            raise BenchmarkError(
                f"Complexity level must be 1, 2, or 3, got: {self.complexity_level}"
            )

        # Calculate prompt hash for verification
        self.prompt_hash = self._calculate_prompt_hash(self.initial_prompt)

        # Extract optional fields
        self.tech_stack = benchmark.get("tech_stack", {})
        self.success_criteria = benchmark.get("success_criteria", [])
        self.expected_outcomes = benchmark.get("expected_outcomes", {})
        self.phases = benchmark.get("phases", [])
        self.constraints = benchmark.get("constraints", {})
        self.boilerplate = benchmark.get("boilerplate", {})

    def _get_required_field(self, data: dict, field: str, expected_type: type) -> Any:
        """
        Extract and validate required field from dictionary.

        Args:
            data: Dictionary to extract from
            field: Field name
            expected_type: Expected Python type

        Returns:
            The field value

        Raises:
            BenchmarkError: If field missing or wrong type
        """
        if field not in data:
            raise BenchmarkError(
                f"Missing required field '{field}' in benchmark configuration"
            )

        value = data[field]
        if not isinstance(value, expected_type):
            raise BenchmarkError(
                f"Field '{field}' must be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

        return value

    def _calculate_prompt_hash(self, prompt: str) -> str:
        """
        Calculate SHA256 hash of the initial prompt.

        This hash is used to verify that the prompt hasn't changed
        between runs, ensuring scientific reproducibility.

        Args:
            prompt: The initial prompt text

        Returns:
            SHA256 hash as hex string (e.g., 'sha256:abc123...')
        """
        # Normalize whitespace to handle minor formatting differences
        normalized = " ".join(prompt.split())
        hash_bytes = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256:{hash_bytes}"

    def get_run_id_prefix(self) -> str:
        """
        Get the prefix for auto-generated run IDs.

        Returns:
            String like 'todo-app-baseline' (the benchmark name)
        """
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for storage in project metadata.

        Returns:
            Dictionary with key benchmark information
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "prompt_hash": self.prompt_hash,
            "complexity_level": self.complexity_level,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "file_path": str(self.file_path),
        }


def load_benchmark(file_path: Path) -> BenchmarkConfig:
    """
    Load and parse a benchmark YAML file.

    Args:
        file_path: Path to benchmark YAML file

    Returns:
        BenchmarkConfig object

    Raises:
        BenchmarkError: If file doesn't exist, can't be parsed, or is invalid
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise BenchmarkError(f"Benchmark file not found: {file_path}")

    if not file_path.is_file():
        raise BenchmarkError(f"Not a file: {file_path}")

    if file_path.suffix not in [".yaml", ".yml"]:
        raise BenchmarkError(
            f"Benchmark file must have .yaml or .yml extension: {file_path}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise BenchmarkError(f"Failed to parse YAML: {e}") from e
    except Exception as e:
        raise BenchmarkError(f"Failed to read file: {e}") from e

    if not isinstance(config, dict):
        raise BenchmarkError("Benchmark file must contain a YAML dictionary")

    return BenchmarkConfig(config, file_path)


def validate_benchmark_file(file_path: Path) -> bool:
    """
    Validate a benchmark file without raising exceptions.

    Args:
        file_path: Path to benchmark YAML file

    Returns:
        True if valid, False otherwise
    """
    try:
        load_benchmark(file_path)
        return True
    except BenchmarkError:
        return False
