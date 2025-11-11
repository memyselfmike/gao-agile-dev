"""Workflow execution engine."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re
import structlog

from .models.workflow import WorkflowInfo
from .models.workflow_context import WorkflowContext
from .config_loader import ConfigLoader
from .services.feature_path_resolver import FeaturePathResolver
from .services.feature_state_service import FeatureStateService

logger = structlog.get_logger(__name__)


class WorkflowExecutor:
    """
    Execute GAO-Dev workflows with variable resolution and template rendering.

    EXISTING FUNCTIONALITY (Epic 18):
    - Load workflows from YAML
    - Resolve variables with priority: params → workflow → config → common
    - Render templates with resolved variables
    - Track workflow execution

    NEW ENHANCEMENTS (Story 34.3):
    - Integrate FeaturePathResolver for feature_name resolution
    - Pass WorkflowContext to resolvers
    - Support feature-scoped paths
    - Fallback to legacy paths when needed
    """

    def __init__(
        self,
        config_loader: ConfigLoader,
        project_root: Optional[Path] = None,
        feature_service: Optional[FeatureStateService] = None
    ):
        """
        Initialize workflow executor.

        Args:
            config_loader: Configuration loader instance
            project_root: Project root directory (optional, for feature resolution)
            feature_service: FeatureStateService (optional, for feature resolution)
        """
        self.config_loader = config_loader
        self.project_root = project_root or Path.cwd()

        # Initialize FeaturePathResolver if feature_service provided
        self.feature_resolver: Optional[FeaturePathResolver] = None
        if feature_service:
            self.feature_resolver = FeaturePathResolver(
                project_root=self.project_root,
                feature_service=feature_service
            )

    def execute(self, workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow to execute
            params: Parameters for the workflow

        Returns:
            Execution result dictionary
        """
        # Resolve variables
        variables = self._resolve_variables(workflow, params)

        # Load instructions
        instructions = self._load_instructions(workflow)

        # Load template if exists
        template = None
        if workflow.templates.get("main"):
            template = self._load_template(workflow, "main")

        # Render template if exists
        rendered_output = None
        if template:
            rendered_output = self._render_template(template, variables)

        # Determine output file path
        output_file = None
        if workflow.output_file:
            output_file = self._render_template(workflow.output_file, variables)

        return {
            "success": True,
            "workflow_name": workflow.name,
            "variables": variables,
            "instructions": instructions,
            "template": rendered_output,
            "output_file": output_file,
            "required_tools": workflow.required_tools,
        }

    def _resolve_variables(
        self,
        workflow: WorkflowInfo,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None
    ) -> Dict[str, Any]:
        """
        Resolve workflow variables from multiple sources.

        EXISTING PRIORITY (Epic 18):
        1. Explicit params (runtime parameters)
        2. Workflow defaults (workflow.variables)
        3. Config defaults (defaults.yaml)
        4. Common variables (auto-generated: date, timestamp, etc.)

        NEW ENHANCEMENT (Story 34.3):
        5. Feature name resolution (FeaturePathResolver with 6-level priority)
        6. Feature-scoped path generation (using resolved feature_name)

        Args:
            workflow: Workflow info
            params: User-provided parameters
            context: Optional WorkflowContext (for feature_name persistence)

        Returns:
            Resolved variables dictionary

        Raises:
            ValueError: If required variables are missing or feature_name cannot be resolved
        """
        variables = {}

        # Layer 1: Config defaults (lowest priority)
        config_defaults = self.config_loader.get_workflow_defaults()
        variables.update(config_defaults)

        logger.debug(
            "variables_from_config_defaults",
            variables_count=len(config_defaults),
            variables=list(config_defaults.keys())
        )

        # Layer 2: Workflow.yaml defaults
        workflow_defaults = {}
        for var_name, var_config in workflow.variables.items():
            if "default" in var_config:
                workflow_defaults[var_name] = var_config["default"]

        variables.update(workflow_defaults)

        logger.debug(
            "variables_from_workflow_yaml",
            variables_count=len(workflow_defaults),
            variables=list(workflow_defaults.keys())
        )

        # Layer 3: Parameters (highest priority)
        variables.update(params)

        logger.debug(
            "variables_from_params",
            variables_count=len(params),
            variables=list(params.keys())
        )

        # Layer 4: Add common variables (always available)
        variables["date"] = datetime.now().strftime("%Y-%m-%d")
        variables["timestamp"] = datetime.now().isoformat()

        # NEW: Layer 5 - Feature name resolution
        if self.feature_resolver and "feature_name" not in variables:
            try:
                feature_name = self.feature_resolver.resolve_feature_name(
                    params=variables,
                    context=context  # Pass context for priority 2!
                )
                variables["feature_name"] = feature_name

                logger.info(
                    "Resolved feature_name",
                    feature_name=feature_name,
                    source="FeaturePathResolver"
                )

            except ValueError as e:
                # Feature name required but can't resolve
                if self._workflow_requires_feature_name(workflow):
                    raise ValueError(
                        f"Workflow '{workflow.name}' requires feature_name but cannot resolve.\n"
                        f"{str(e)}\n\n"
                        f"Specify feature_name explicitly:\n"
                        f"  --feature-name <name>\n"
                        f"Or run from feature directory:\n"
                        f"  cd docs/features/<name> && gao-dev {workflow.name}"
                    ) from e

                # Otherwise, use legacy paths (backward compatibility)
                logger.warning(
                    "feature_name not resolved, using legacy paths",
                    workflow=workflow.name,
                    reason=str(e)
                )
                # Don't add feature_name to variables (will use legacy paths)

        # NEW: Layer 6 - Feature-scoped path generation
        if "feature_name" in variables and self.feature_resolver:
            feature_paths = self._generate_feature_scoped_paths(variables)
            variables.update(feature_paths)

            logger.debug(
                "Generated feature-scoped paths",
                feature_name=variables["feature_name"],
                path_count=len(feature_paths),
                paths=list(feature_paths.keys())
            )

        # Validate required variables
        for var_name, var_config in workflow.variables.items():
            if var_config.get("required", False) and var_name not in variables:
                raise ValueError(f"Required variable '{var_name}' not provided")

        logger.debug(
            "variables_resolved",
            total_count=len(variables),
            variables=list(variables.keys())
        )

        return variables

    def _workflow_requires_feature_name(self, workflow: WorkflowInfo) -> bool:
        """
        Check if workflow requires feature_name.

        A workflow requires feature_name if:
        - It uses {{feature_name}} in any template
        - It has output paths that are feature-scoped
        - It's a feature-related workflow (prd, architecture, etc.)

        Args:
            workflow: Workflow definition

        Returns:
            True if workflow requires feature_name
        """
        # Check if workflow has output_file with {{feature_name}}
        output_file = workflow.output_file or ""
        if "{{feature_name}}" in str(output_file):
            return True

        # Check if workflow variables have feature-scoped defaults
        for var_name, var_config in workflow.variables.items():
            default_value = var_config.get("default", "")
            if "{{feature_name}}" in str(default_value):
                return True

        # Check if workflow is feature-related by name
        feature_workflows = [
            "create_prd", "create_architecture", "create_epic",
            "create_story", "implement_story", "qa_validation"
        ]
        if workflow.name in feature_workflows:
            return True

        return False

    def _generate_feature_scoped_paths(self, resolved: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate feature-scoped paths using FeaturePathResolver.

        Uses resolved feature_name, epic, epic_name, story to generate
        all feature-scoped paths (PRD, epic location, story location, etc.)

        Args:
            resolved: Already resolved variables (must contain feature_name)

        Returns:
            Dict with generated paths

        Raises:
            ValueError: If feature_resolver is not initialized
        """
        if not self.feature_resolver:
            return {}

        paths = {}
        feature_name = resolved["feature_name"]

        # Generate all path types
        path_types = [
            "prd", "architecture", "readme", "epics_overview",
            "qa_folder", "retrospectives_folder",
            "epic_folder", "epic_location",
            "story_folder", "story_location", "context_xml_folder",
            "retrospective_location"
        ]

        for path_type in path_types:
            try:
                path = self.feature_resolver.generate_feature_path(
                    feature_name=feature_name,
                    path_type=path_type,
                    epic=resolved.get("epic"),
                    epic_name=resolved.get("epic_name"),
                    story=resolved.get("story")
                )
                # Convert path_type to variable name (e.g., "prd" → "prd_location")
                if path_type.endswith(("_folder", "_location", "_overview")):
                    var_name = path_type
                else:
                    var_name = f"{path_type}_location"

                paths[var_name] = str(path)

            except ValueError:
                # Path type may require epic/story that aren't available
                # (e.g., story_location requires epic and story)
                pass

        return paths

    def _load_instructions(self, workflow: WorkflowInfo) -> str:
        """
        Load workflow instructions.

        Args:
            workflow: Workflow info

        Returns:
            Instructions content
        """
        instructions_file = workflow.installed_path / "instructions.md"
        if instructions_file.exists():
            return instructions_file.read_text(encoding="utf-8")
        return ""

    def _load_template(self, workflow: WorkflowInfo, template_name: str) -> Optional[str]:
        """
        Load workflow template.

        Args:
            workflow: Workflow info
            template_name: Template name

        Returns:
            Template content or None
        """
        template_filename = workflow.templates.get(template_name)
        if not template_filename:
            return None

        template_file = workflow.installed_path / template_filename
        if template_file.exists():
            return template_file.read_text(encoding="utf-8")
        return None

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render template with variables using Mustache-style syntax.

        Args:
            template: Template string
            variables: Variables dictionary

        Returns:
            Rendered template
        """
        rendered = template

        # Replace {{variable}} with value
        for key, value in variables.items():
            pattern = r"\{\{" + re.escape(str(key)) + r"\}\}"
            # Escape backslashes in replacement string to avoid regex escape sequence issues
            # This is critical for Windows paths (C:\Users\... becomes C:\\Users\\...)
            replacement = str(value).replace("\\", "\\\\")
            rendered = re.sub(pattern, replacement, rendered)

        return rendered

    # ========================================================================
    # Public API Methods
    # ========================================================================

    def resolve_variables(
        self,
        workflow: WorkflowInfo,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None
    ) -> Dict[str, Any]:
        """
        Resolve workflow variables from params, config, and defaults.

        PUBLIC API for orchestrator to resolve variables before execution.

        Priority order:
        1. Parameters (passed to this method) - highest priority
        2. Workflow.yaml variables section
        3. Config defaults (from defaults.yaml)
        4. Common variables (date, timestamp)
        5. Feature name resolution (if feature_resolver available)
        6. Feature-scoped path generation (if feature_name resolved)

        Args:
            workflow: Workflow info
            params: User-provided parameters
            context: Optional WorkflowContext (for feature_name persistence)

        Returns:
            Resolved variables dictionary

        Raises:
            ValueError: If required variables are missing or feature_name cannot be resolved
        """
        return self._resolve_variables(workflow, params, context)

    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render template with variables using Mustache-style syntax.

        PUBLIC API for orchestrator to render instructions with resolved variables.

        Args:
            template: Template string with {{variable}} placeholders
            variables: Variables dictionary

        Returns:
            Rendered template with all placeholders replaced
        """
        return self._render_template(template, variables)
