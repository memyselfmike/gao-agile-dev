"""Benchmark configuration data models."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json


@dataclass
class SuccessCriteria:
    """
    Success criteria for benchmark run.

    Defines the thresholds and requirements that a benchmark run
    must meet to be considered successful.
    """

    min_test_coverage: float = 80.0
    max_manual_interventions: int = 0
    max_errors: int = 0
    required_features: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate success criteria.

        Returns:
            bool: True if all criteria are valid
        """
        return (
            0 <= self.min_test_coverage <= 100
            and self.max_manual_interventions >= 0
            and self.max_errors >= 0
        )


@dataclass
class WorkflowPhaseConfig:
    """
    Configuration for a workflow phase.

    Defines how a single phase of the workflow should be executed,
    including timeouts, expected artifacts, and quality gates.
    """

    phase_name: str
    command: Optional[str] = None
    timeout_seconds: int = 3600
    continue_on_failure: bool = False
    expected_artifacts: List[str] = field(default_factory=list)
    quality_gates: Dict[str, Any] = field(default_factory=dict)
    skip_if_failed: bool = False

    def validate(self) -> bool:
        """
        Validate phase configuration.

        Returns:
            bool: True if configuration is valid
        """
        return bool(self.phase_name) and self.timeout_seconds > 0


@dataclass
class BenchmarkConfig:
    """
    Complete benchmark configuration.

    Defines all parameters for running a benchmark, including project
    setup, success criteria, workflow phases, and timeouts.
    """

    name: str
    description: str
    version: str = "1.0.0"
    project_name: str = ""
    boilerplate_url: Optional[str] = None
    boilerplate_path: Optional[Path] = None
    timeout_seconds: int = 7200  # 2 hours default
    success_criteria: SuccessCriteria = field(default_factory=SuccessCriteria)
    workflow_phases: List[WorkflowPhaseConfig] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """
        Validate entire configuration.

        Returns:
            bool: True if all configuration is valid
        """
        return (
            bool(self.name)
            and bool(self.description)
            and self.timeout_seconds > 0
            and self.success_criteria.validate()
            and all(phase.validate() for phase in self.workflow_phases)
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchmarkConfig":
        """
        Load config from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            BenchmarkConfig: Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Convert nested dicts to dataclasses
        if "success_criteria" in data and isinstance(data["success_criteria"], dict):
            data["success_criteria"] = SuccessCriteria(**data["success_criteria"])

        if "workflow_phases" in data and isinstance(data["workflow_phases"], list):
            data["workflow_phases"] = [
                WorkflowPhaseConfig(**phase) if isinstance(phase, dict) else phase
                for phase in data["workflow_phases"]
            ]

        # Convert boilerplate_path string to Path if present
        if "boilerplate_path" in data and data["boilerplate_path"] is not None:
            data["boilerplate_path"] = Path(data["boilerplate_path"])

        return cls(**data)

    @classmethod
    def from_json(cls, path: Path) -> "BenchmarkConfig":
        """
        Load config from JSON file.

        Args:
            path: Path to JSON configuration file

        Returns:
            BenchmarkConfig: Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        with open(path, "r") as f:
            data = json.load(f)

        # Convert nested dicts to dataclasses
        if "success_criteria" in data and isinstance(data["success_criteria"], dict):
            data["success_criteria"] = SuccessCriteria(**data["success_criteria"])

        if "workflow_phases" in data and isinstance(data["workflow_phases"], list):
            data["workflow_phases"] = [
                WorkflowPhaseConfig(**phase) if isinstance(phase, dict) else phase
                for phase in data["workflow_phases"]
            ]

        # Convert boilerplate_path string to Path if present
        if "boilerplate_path" in data and data["boilerplate_path"] is not None:
            data["boilerplate_path"] = Path(data["boilerplate_path"])

        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dict[str, Any]: Configuration as dictionary

        Note:
            Path objects are converted to strings for serialization.
        """
        data = asdict(self)

        # Convert Path to string for serialization
        if data.get("boilerplate_path"):
            data["boilerplate_path"] = str(data["boilerplate_path"])

        return data

    def to_yaml(self, path: Path) -> None:
        """
        Save config to YAML file.

        Args:
            path: Path where to save the configuration
        """
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

    def to_json(self, path: Path) -> None:
        """
        Save config to JSON file.

        Args:
            path: Path where to save the configuration
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
