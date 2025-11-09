"""Workflow discovery and registry."""

from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .models.workflow import WorkflowInfo
from .config_loader import ConfigLoader


class WorkflowRegistry:
    """Discover and manage GAO-Dev workflows."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize workflow registry.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader
        self._workflows: Dict[str, WorkflowInfo] = {}
        self._indexed = False

    def index_workflows(self) -> None:
        """
        Scan and index all workflows from both embedded and BMAD locations.

        Story 7.2.6: Load complete workflow catalog from bmad/bmm/workflows
        (34+ workflows) in addition to embedded workflows.
        """
        self._workflows = {}

        # Load from both locations
        paths_to_scan = [
            self.config_loader.get_workflows_path(),  # Embedded: gao_dev/workflows
            self.config_loader.get_bmad_workflows_path()  # BMAD: bmad/bmm/workflows
        ]

        for workflows_path in paths_to_scan:
            if not workflows_path.exists():
                continue

            # Recursively find all workflow.yaml files
            for workflow_file in workflows_path.rglob("workflow.yaml"):
                workflow_info = self._load_workflow(workflow_file)
                if workflow_info:
                    # Use workflow name as key (later paths override earlier ones)
                    self._workflows[workflow_info.name] = workflow_info

        self._indexed = True

    def _load_workflow(self, workflow_file: Path) -> Optional[WorkflowInfo]:
        """
        Load workflow from workflow.yaml file.

        Args:
            workflow_file: Path to workflow.yaml

        Returns:
            WorkflowInfo if valid, None otherwise
        """
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "name" not in data:
                return None

            # Determine phase from directory path or YAML
            phase = data.get("phase", self._determine_phase(workflow_file.parent))

            # Load category and metadata
            category = data.get("category")
            metadata = data.get("metadata", {})

            # Validate ceremony workflows
            if category == "ceremonies":
                if not self._validate_ceremony_metadata(metadata, data["name"]):
                    return None

            workflow_info = WorkflowInfo(
                name=data["name"],
                description=data.get("description", ""),
                phase=phase,
                installed_path=workflow_file.parent,
                author=data.get("agent") or data.get("author"),  # Ceremony workflows use 'agent'
                tags=data.get("tags", []),
                variables=data.get("variables", {}),
                required_tools=data.get("required_tools", []),
                interactive=not data.get("non_interactive", False),
                autonomous=data.get("autonomous", True),
                iterative=data.get("iterative", False),
                web_bundle=data.get("web_bundle", False),
                output_file=data.get("output_file"),
                templates=data.get("templates", {}),
                category=category,
                metadata=metadata,
            )
            return workflow_info
        except Exception as e:
            print(f"Error loading workflow {workflow_file}: {e}")
            return None

    def _validate_ceremony_metadata(self, metadata: dict, workflow_name: str) -> bool:
        """
        Validate ceremony-specific metadata.

        Args:
            metadata: Ceremony metadata dictionary
            workflow_name: Name of the workflow (for error messages)

        Returns:
            True if valid, False otherwise
        """
        if not metadata:
            print(f"Ceremony workflow '{workflow_name}' missing metadata field")
            return False

        # Check required fields
        if "ceremony_type" not in metadata:
            print(f"Ceremony workflow '{workflow_name}' missing ceremony_type in metadata")
            return False

        if "participants" not in metadata:
            print(f"Ceremony workflow '{workflow_name}' missing participants in metadata")
            return False

        if "trigger" not in metadata:
            print(f"Ceremony workflow '{workflow_name}' missing trigger in metadata")
            return False

        # Validate ceremony_type
        valid_ceremony_types = ["planning", "standup", "retrospective"]
        if metadata["ceremony_type"] not in valid_ceremony_types:
            print(
                f"Ceremony workflow '{workflow_name}' has invalid ceremony_type: "
                f"{metadata['ceremony_type']}"
            )
            return False

        # Validate participants is a list
        if not isinstance(metadata["participants"], list):
            print(f"Ceremony workflow '{workflow_name}' participants must be a list")
            return False

        # Validate participants are non-empty
        if not metadata["participants"]:
            print(f"Ceremony workflow '{workflow_name}' participants cannot be empty")
            return False

        # Validate trigger
        valid_triggers = [
            "epic_start",
            "epic_completion",
            "mid_epic_checkpoint",
            "story_interval",
            "story_count_threshold",
            "quality_gate_failure",
            "repeated_failure",
            "timeout_exceeded",
            "daily",
            "phase_end",
        ]
        if metadata["trigger"] not in valid_triggers:
            print(f"Ceremony workflow '{workflow_name}' has invalid trigger: {metadata['trigger']}")
            return False

        return True

    def _determine_phase(self, workflow_path: Path) -> int:
        """
        Determine phase from workflow path.

        Args:
            workflow_path: Path to workflow directory

        Returns:
            Phase number (0-5, 5 is for ceremonies)
        """
        # Look for phase number in parent directories
        for parent in workflow_path.parents:
            if parent.name.startswith("0-"):
                return 0
            elif parent.name.startswith("1-"):
                return 1
            elif parent.name.startswith("2-"):
                return 2
            elif parent.name.startswith("3-"):
                return 3
            elif parent.name.startswith("4-"):
                return 4
            elif parent.name.startswith("5-"):
                return 5
        return 0

    def get_workflow(self, name: str) -> Optional[WorkflowInfo]:
        """
        Get workflow by name.

        Args:
            name: Workflow name

        Returns:
            WorkflowInfo if found, None otherwise
        """
        if not self._indexed:
            self.index_workflows()
        return self._workflows.get(name)

    def list_workflows(
        self,
        phase: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[WorkflowInfo]:
        """
        List workflows, optionally filtered by phase and/or category.

        Args:
            phase: Phase number to filter by (0-5), None for all
            category: Category to filter by (e.g., "ceremonies"), None for all

        Returns:
            List of WorkflowInfo objects
        """
        if not self._indexed:
            self.index_workflows()

        workflows = list(self._workflows.values())

        if phase is not None:
            workflows = [w for w in workflows if w.phase == phase]

        if category is not None:
            workflows = [w for w in workflows if w.category == category]

        # Sort by phase, then by name
        workflows.sort(key=lambda w: (w.phase, w.name))
        return workflows

    def get_all_workflows(self) -> Dict[str, WorkflowInfo]:
        """
        Get all workflows as dictionary.

        Returns:
            Dictionary mapping workflow name to WorkflowInfo
        """
        if not self._indexed:
            self.index_workflows()
        return self._workflows.copy()

    def workflow_exists(self, name: str) -> bool:
        """
        Check if workflow exists.

        Args:
            name: Workflow name

        Returns:
            True if workflow exists
        """
        if not self._indexed:
            self.index_workflows()
        return name in self._workflows
