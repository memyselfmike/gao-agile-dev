"""Workflow execution engine."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re
import structlog

from .models.workflow import WorkflowInfo
from .config_loader import ConfigLoader

logger = structlog.get_logger(__name__)


class WorkflowExecutor:
    """Execute GAO-Dev workflows with variable resolution and template rendering."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize workflow executor.

        Args:
            config_loader: Configuration loader instance
        """
        self.config_loader = config_loader

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

    def _resolve_variables(self, workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve workflow variables from multiple sources.

        Priority order:
        1. Parameters (passed to execute method) - highest priority
        2. Workflow.yaml variables section
        3. Config defaults (from defaults.yaml)
        4. Common variables (date, timestamp)

        Args:
            workflow: Workflow info
            params: User-provided parameters

        Returns:
            Resolved variables dictionary
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
            rendered = re.sub(pattern, str(value), rendered)

        return rendered
