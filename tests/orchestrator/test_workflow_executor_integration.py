"""Tests for WorkflowExecutor integration in orchestrator (Story 18.1)."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, MagicMock
from typing import Dict, Any

from gao_dev.orchestrator.orchestrator import GAODevOrchestrator
from gao_dev.core.workflow_executor import WorkflowExecutor
from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.models.workflow import WorkflowInfo


class TestOrchestratorWorkflowExecutorIntegration:
    """Test WorkflowExecutor integration in GAODevOrchestrator."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def orchestrator(self, temp_project_dir: Path) -> GAODevOrchestrator:
        """Create orchestrator instance with WorkflowExecutor."""
        orchestrator = GAODevOrchestrator(
            project_root=temp_project_dir,
            mode="benchmark"
        )
        return orchestrator

    def test_orchestrator_has_workflow_executor(self, orchestrator: GAODevOrchestrator):
        """Test that orchestrator has WorkflowExecutor instance initialized."""
        assert hasattr(orchestrator, 'workflow_executor')
        assert isinstance(orchestrator.workflow_executor, WorkflowExecutor)
        assert orchestrator.workflow_executor.config_loader is not None

    def test_workflow_executor_passed_to_coordinator(self, orchestrator: GAODevOrchestrator):
        """Test that WorkflowExecutor is passed to WorkflowCoordinator."""
        assert hasattr(orchestrator, 'workflow_coordinator')
        assert orchestrator.workflow_coordinator is not None
        assert hasattr(orchestrator.workflow_coordinator, 'workflow_executor')
        assert orchestrator.workflow_coordinator.workflow_executor is not None

    @pytest.mark.asyncio
    async def test_execute_agent_task_resolves_variables(
        self,
        orchestrator: GAODevOrchestrator,
        tmp_path: Path
    ):
        """Test that _execute_agent_task_static resolves variables before execution."""
        # Create a test workflow with variables
        workflow_dir = tmp_path / "test_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create instructions.md with variable placeholders
        instructions_file = workflow_dir / "instructions.md"
        instructions_file.write_text(
            "Create a file at {{prd_location}} for project {{project_name}}.",
            encoding="utf-8"
        )

        workflow = WorkflowInfo(
            name="test_prd",
            description="Test PRD workflow",
            phase=1,
            variables={
                "prd_location": {
                    "description": "PRD location",
                    "default": "docs/PRD.md"
                },
                "project_name": {
                    "description": "Project name",
                    "required": True
                }
            },
            required_tools=["Read", "Write"],
            templates={},
            installed_path=workflow_dir
        )

        # Mock ProcessExecutor to capture the rendered task prompt
        captured_task = None

        async def mock_execute_agent_task(task: str, tools=None, timeout=None):
            nonlocal captured_task
            captured_task = task
            yield "Task executed successfully"

        orchestrator.process_executor.execute_agent_task = mock_execute_agent_task

        # Execute the workflow
        outputs = []
        async for output in orchestrator._execute_agent_task_static(workflow, epic=1, story=1):
            outputs.append(output)

        # Verify that variables were resolved
        assert captured_task is not None
        assert "{{prd_location}}" not in captured_task  # Should be resolved
        assert "{{project_name}}" not in captured_task  # Should be resolved
        assert "docs/PRD.md" in captured_task  # Default value resolved
        assert orchestrator.project_root.name in captured_task  # project_name resolved

    @pytest.mark.asyncio
    async def test_variable_resolution_with_parameters(
        self,
        orchestrator: GAODevOrchestrator,
        tmp_path: Path
    ):
        """Test variable resolution includes epic, story, project_name parameters."""
        workflow_dir = tmp_path / "story_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        instructions_file = workflow_dir / "instructions.md"
        instructions_file.write_text(
            "Working on Epic {{epic_num}}, Story {{story_num}} for {{project_name}}",
            encoding="utf-8"
        )

        workflow = WorkflowInfo(
            name="test_story",
            description="Test story workflow",
            phase=4,
            variables={
                "epic_num": {"description": "Epic number"},
                "story_num": {"description": "Story number"},
                "project_name": {"description": "Project name"}
            },
            required_tools=["Read", "Write"],
            templates={},
            installed_path=workflow_dir
        )

        captured_task = None

        async def mock_execute_agent_task(task: str, tools=None, timeout=None):
            nonlocal captured_task
            captured_task = task
            yield "Done"

        orchestrator.process_executor.execute_agent_task = mock_execute_agent_task

        # Execute with specific epic and story
        async for _ in orchestrator._execute_agent_task_static(workflow, epic=5, story=3):
            pass

        # Verify parameters were passed correctly
        assert captured_task is not None
        assert "Epic 5" in captured_task
        assert "Story 3" in captured_task
        assert orchestrator.project_root.name in captured_task


class TestVariableResolutionPublicAPI:
    """Test public API methods of WorkflowExecutor."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def config_loader(self, temp_project_dir: Path) -> ConfigLoader:
        """Create ConfigLoader instance."""
        return ConfigLoader(temp_project_dir)

    @pytest.fixture
    def workflow_executor(self, config_loader: ConfigLoader) -> WorkflowExecutor:
        """Create WorkflowExecutor instance."""
        return WorkflowExecutor(config_loader)

    def test_resolve_variables_public_method(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test that resolve_variables public method works correctly."""
        workflow_dir = tmp_path / "test_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="test",
            description="Test",
            phase=1,
            variables={
                "output_folder": {
                    "description": "Output folder",
                    "default": "custom_output"
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {"custom_param": "custom_value"}

        # Call public method
        variables = workflow_executor.resolve_variables(workflow, params)

        # Verify variables resolved
        assert isinstance(variables, dict)
        assert "output_folder" in variables
        assert variables["output_folder"] == "custom_output"
        assert "custom_param" in variables
        assert variables["custom_param"] == "custom_value"
        assert "date" in variables
        assert "timestamp" in variables

    def test_render_template_public_method(self, workflow_executor: WorkflowExecutor):
        """Test that render_template public method works correctly."""
        template = "Hello {{name}}, welcome to {{project}}!"
        variables = {"name": "Alice", "project": "GAO-Dev"}

        # Call public method
        rendered = workflow_executor.render_template(template, variables)

        # Verify template rendered
        assert rendered == "Hello Alice, welcome to GAO-Dev!"
        assert "{{" not in rendered
        assert "}}" not in rendered

    def test_render_template_preserves_formatting(self, workflow_executor: WorkflowExecutor):
        """Test that render_template preserves markdown formatting."""
        template = """# Project: {{project_name}}

## Overview
This is the PRD for {{project_name}}.

### Location
File will be created at: {{prd_location}}

- Item 1
- Item 2
"""
        variables = {
            "project_name": "MyApp",
            "prd_location": "docs/PRD.md"
        }

        rendered = workflow_executor.render_template(template, variables)

        # Verify formatting preserved
        assert "# Project: MyApp" in rendered
        assert "## Overview" in rendered
        assert "This is the PRD for MyApp" in rendered
        assert "docs/PRD.md" in rendered
        assert "- Item 1" in rendered
        assert "- Item 2" in rendered

    def test_resolve_variables_priority_order(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test variable resolution priority: params > workflow defaults > config defaults."""
        workflow_dir = tmp_path / "priority_test"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="priority",
            description="Priority test",
            phase=1,
            variables={
                "var1": {
                    "description": "Variable 1",
                    "default": "workflow_default"
                },
                "var2": {
                    "description": "Variable 2"
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {
            "var1": "param_value",  # Should override workflow default
            "var3": "another_param"
        }

        variables = workflow_executor.resolve_variables(workflow, params)

        # var1: params win
        assert variables["var1"] == "param_value"

        # var2: should use config default (if exists)
        assert "var2" in variables

        # var3: from params
        assert variables["var3"] == "another_param"


class TestVariableResolutionErrorHandling:
    """Test error handling in variable resolution."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def workflow_executor(self, temp_project_dir: Path) -> WorkflowExecutor:
        """Create WorkflowExecutor instance."""
        config_loader = ConfigLoader(temp_project_dir)
        return WorkflowExecutor(config_loader)

    def test_required_variable_missing_raises_error(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test that missing required variable raises ValueError."""
        workflow_dir = tmp_path / "required_test"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="required",
            description="Required test",
            phase=1,
            variables={
                "required_var": {
                    "description": "Required variable",
                    "required": True
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Don't provide required variable
        with pytest.raises(ValueError, match="Required variable 'required_var' not provided"):
            workflow_executor.resolve_variables(workflow, {})

    def test_required_variable_in_params_succeeds(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test that providing required variable in params succeeds."""
        workflow_dir = tmp_path / "required_success"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="required_success",
            description="Required success test",
            phase=1,
            variables={
                "required_var": {
                    "description": "Required variable",
                    "required": True
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {"required_var": "provided_value"}

        # Should not raise
        variables = workflow_executor.resolve_variables(workflow, params)
        assert variables["required_var"] == "provided_value"


class TestTemplateRenderingEdgeCases:
    """Test edge cases in template rendering."""

    @pytest.fixture
    def workflow_executor(self, tmp_path: Path) -> WorkflowExecutor:
        """Create WorkflowExecutor instance."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        config_loader = ConfigLoader(project_dir)
        return WorkflowExecutor(config_loader)

    def test_render_template_with_missing_variable(self, workflow_executor: WorkflowExecutor):
        """Test rendering template with missing variable (should leave placeholder)."""
        template = "Hello {{name}}, welcome to {{project}}!"
        variables = {"name": "Alice"}  # Missing 'project'

        rendered = workflow_executor.render_template(template, variables)

        # Should replace what it can
        assert "Hello Alice" in rendered
        # Missing variable remains as placeholder
        assert "{{project}}" in rendered

    def test_render_template_with_special_characters(self, workflow_executor: WorkflowExecutor):
        """Test rendering with special characters in variable values."""
        template = "Path: {{file_path}}"
        variables = {"file_path": "C:\\Users\\test\\docs\\file.md"}

        rendered = workflow_executor.render_template(template, variables)

        assert "C:\\Users\\test\\docs\\file.md" in rendered

    def test_render_template_with_numeric_values(self, workflow_executor: WorkflowExecutor):
        """Test rendering with numeric values."""
        template = "Epic {{epic}}, Story {{story}}"
        variables = {"epic": 5, "story": 3}

        rendered = workflow_executor.render_template(template, variables)

        assert "Epic 5, Story 3" in rendered

    def test_render_template_empty_variables(self, workflow_executor: WorkflowExecutor):
        """Test rendering with empty variables dict."""
        template = "Hello World"
        variables = {}

        rendered = workflow_executor.render_template(template, variables)

        assert rendered == "Hello World"
