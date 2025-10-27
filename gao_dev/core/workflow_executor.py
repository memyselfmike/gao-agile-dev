"""Workflow execution engine."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re

from .models import WorkflowInfo
from .config_loader import ConfigLoader


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
        Resolve workflow variables from params, config, and defaults.

        Args:
            workflow: Workflow info
            params: User-provided parameters

        Returns:
            Resolved variables dictionary
        """
        variables = {}

        # Process each variable defined in workflow
        for var_name, var_config in workflow.variables.items():
            # Priority 1: Explicit parameters
            if var_name in params:
                variables[var_name] = params[var_name]
            # Priority 2: Project config
            elif var_name in self.config_loader.user_config:
                variables[var_name] = self.config_loader.user_config[var_name]
            # Priority 3: Default value
            elif "default" in var_config:
                variables[var_name] = var_config["default"]
            # Required but missing
            elif var_config.get("required", False):
                raise ValueError(f"Required variable '{var_name}' not provided")

        # Add common variables
        variables["date"] = datetime.now().strftime("%Y-%m-%d")
        variables["timestamp"] = datetime.now().isoformat()

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
