"""Benchmark configuration data models."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json


@dataclass
class StoryConfig:
    """
    Configuration for a single user story in incremental workflow.

    Defines a story to be implemented as part of an epic, including
    the responsible agent and acceptance criteria.
    """

    name: str
    agent: str
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    story_points: int = 3
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 3600  # 1 hour default per story

    def validate(self) -> bool:
        """
        Validate story configuration.

        Returns:
            bool: True if configuration is valid
        """
        return (
            bool(self.name)
            and bool(self.agent)
            and self.story_points > 0
            and self.timeout_seconds > 0
        )


@dataclass
class EpicConfig:
    """
    Configuration for an epic containing multiple stories.

    Defines a collection of related stories that together deliver
    a major feature or capability.
    """

    name: str
    description: str
    stories: List[StoryConfig] = field(default_factory=list)
    priority: str = "P1"  # P0, P1, P2, P3

    def validate(self) -> bool:
        """
        Validate epic configuration.

        Returns:
            bool: True if configuration is valid
        """
        return (
            bool(self.name)
            and bool(self.description)
            and all(story.validate() for story in self.stories)
        )

    def total_story_points(self) -> int:
        """Calculate total story points in epic."""
        return sum(story.story_points for story in self.stories)


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

    # Additional fields for documentation and planning
    description: str = ""
    agent: str = ""
    expected_duration_minutes: int = 60

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

    Supports two modes:
    1. Phase-based (legacy): Uses workflow_phases for waterfall execution
    2. Story-based (new): Uses epics for incremental agile execution
    """

    name: str
    description: str
    version: str = "1.0.0"
    project_name: str = ""
    boilerplate_url: Optional[str] = None
    boilerplate_path: Optional[Path] = None
    timeout_seconds: int = 7200  # 2 hours default
    success_criteria: SuccessCriteria = field(default_factory=SuccessCriteria)
    workflow_phases: List[WorkflowPhaseConfig] = field(default_factory=list)  # Legacy mode
    epics: List[EpicConfig] = field(default_factory=list)  # New story-based mode
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Additional fields for CLI display and tracking
    initial_prompt: str = ""
    complexity_level: int = 2
    estimated_duration_minutes: int = 120
    prompt_hash: str = ""

    def validate(self) -> bool:
        """
        Validate entire configuration.

        Supports three modes:
        1. Autonomous (Story 7.2.3): Has initial_prompt, no phases/epics
        2. Phase-based (legacy): Has workflow_phases
        3. Story-based (new): Has epics

        Returns:
            bool: True if all configuration is valid
        """
        has_initial_prompt = bool(self.initial_prompt)
        has_phases = bool(self.workflow_phases)
        has_epics = bool(self.epics)

        # Autonomous mode: initial_prompt without phases or epics
        if has_initial_prompt and not has_phases and not has_epics:
            return (
                bool(self.name)
                and bool(self.description)
                and self.timeout_seconds > 0
                and self.success_criteria.validate()
            )

        # Legacy/story modes: Must have either phases or epics, but not both
        if has_phases == has_epics:
            return False  # Either both empty or both filled

        return (
            bool(self.name)
            and bool(self.description)
            and self.timeout_seconds > 0
            and self.success_criteria.validate()
            and all(phase.validate() for phase in self.workflow_phases)
            and all(epic.validate() for epic in self.epics)
        )

    def is_story_based(self) -> bool:
        """
        Check if configuration uses story-based mode.

        Returns:
            bool: True if using epics/stories, False if using phases
        """
        return bool(self.epics)

    def is_phase_based(self) -> bool:
        """
        Check if configuration uses phase-based mode (legacy).

        Returns:
            bool: True if using workflow phases
        """
        return bool(self.workflow_phases)

    def total_stories(self) -> int:
        """
        Get total number of stories across all epics.

        Returns:
            int: Total story count (0 if phase-based)
        """
        return sum(len(epic.stories) for epic in self.epics)

    def total_story_points(self) -> int:
        """
        Get total story points across all epics.

        Returns:
            int: Total story points (0 if phase-based)
        """
        return sum(epic.total_story_points() for epic in self.epics)

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchmarkConfig":
        """
        Load config from YAML file.

        Supports both phase-based and story-based configurations.

        Args:
            path: Path to YAML configuration file

        Returns:
            BenchmarkConfig: Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        import hashlib

        with open(path, "r") as f:
            yaml_data = yaml.safe_load(f)

        # Handle both wrapped (with "benchmark:" key) and unwrapped formats
        if "benchmark" in yaml_data and isinstance(yaml_data["benchmark"], dict):
            data = yaml_data["benchmark"]
        else:
            data = yaml_data

        # Calculate prompt hash if initial_prompt exists
        if "initial_prompt" in data and data["initial_prompt"]:
            normalized = " ".join(data["initial_prompt"].split())
            hash_bytes = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            data["prompt_hash"] = f"sha256:{hash_bytes}"

        # Convert nested dicts to dataclasses
        if "success_criteria" in data and isinstance(data["success_criteria"], dict):
            data["success_criteria"] = SuccessCriteria(**data["success_criteria"])

        # Support both "phases" and "workflow_phases" keys (phases is alias)
        if "phases" in data and "workflow_phases" not in data:
            data["workflow_phases"] = data.pop("phases")

        # Convert workflow_phases (legacy/phase-based mode)
        if "workflow_phases" in data and isinstance(data["workflow_phases"], list):
            data["workflow_phases"] = [
                WorkflowPhaseConfig(**phase) if isinstance(phase, dict) else phase
                for phase in data["workflow_phases"]
            ]

        # Convert epics and stories (new story-based mode)
        if "epics" in data and isinstance(data["epics"], list):
            epics = []
            for epic_data in data["epics"]:
                if isinstance(epic_data, dict):
                    # Convert stories within epic
                    if "stories" in epic_data and isinstance(epic_data["stories"], list):
                        epic_data["stories"] = [
                            StoryConfig(**story) if isinstance(story, dict) else story
                            for story in epic_data["stories"]
                        ]
                    epics.append(EpicConfig(**epic_data))
                else:
                    epics.append(epic_data)
            data["epics"] = epics

        # Convert boilerplate_path string to Path if present
        if "boilerplate_path" in data and data["boilerplate_path"] is not None:
            data["boilerplate_path"] = Path(data["boilerplate_path"])

        # Filter out fields that aren't in the dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    @classmethod
    def from_json(cls, path: Path) -> "BenchmarkConfig":
        """
        Load config from JSON file.

        Supports both phase-based and story-based configurations.

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

        # Support both "phases" and "workflow_phases" keys (phases is alias)
        if "phases" in data and "workflow_phases" not in data:
            data["workflow_phases"] = data.pop("phases")

        # Convert workflow_phases (legacy/phase-based mode)
        if "workflow_phases" in data and isinstance(data["workflow_phases"], list):
            data["workflow_phases"] = [
                WorkflowPhaseConfig(**phase) if isinstance(phase, dict) else phase
                for phase in data["workflow_phases"]
            ]

        # Convert epics and stories (new story-based mode)
        if "epics" in data and isinstance(data["epics"], list):
            epics = []
            for epic_data in data["epics"]:
                if isinstance(epic_data, dict):
                    # Convert stories within epic
                    if "stories" in epic_data and isinstance(epic_data["stories"], list):
                        epic_data["stories"] = [
                            StoryConfig(**story) if isinstance(story, dict) else story
                            for story in epic_data["stories"]
                        ]
                    epics.append(EpicConfig(**epic_data))
                else:
                    epics.append(epic_data)
            data["epics"] = epics

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
