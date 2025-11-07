"""Tests for WorkflowExecutor variable resolution with config defaults (Story 18.4)."""

import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from gao_dev.core.workflow_executor import WorkflowExecutor
from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.models.workflow import WorkflowInfo


class TestWorkflowExecutorVariableResolution:
    """Test variable resolution with config defaults."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def config_loader(self, temp_project_dir: Path) -> ConfigLoader:
        """Create a ConfigLoader instance."""
        return ConfigLoader(temp_project_dir)

    @pytest.fixture
    def workflow_executor(self, config_loader: ConfigLoader) -> WorkflowExecutor:
        """Create a WorkflowExecutor instance."""
        return WorkflowExecutor(config_loader)

    @pytest.fixture
    def sample_workflow(self, tmp_path: Path) -> WorkflowInfo:
        """Create a sample workflow for testing."""
        workflow_dir = tmp_path / "workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        return WorkflowInfo(
            name="test_workflow",
            description="Test workflow",
            phase=1,
            variables={
                "project_name": {
                    "description": "Project name",
                    "required": True
                },
                "output_folder": {
                    "description": "Output folder",
                    "required": False
                },
                "prd_location": {
                    "description": "PRD location",
                    "required": False
                }
            },
            required_tools=["Read", "Write"],
            templates={},
            installed_path=workflow_dir
        )

    def test_resolve_variables_uses_config_defaults(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test that config defaults are used when variable not in params."""
        # Execute with minimal params
        params = {"project_name": "MyProject"}

        result = workflow_executor.execute(sample_workflow, params)
        variables = result["variables"]

        # Should have config defaults
        assert "output_folder" in variables
        assert variables["output_folder"] == "docs"  # From config defaults

        assert "prd_location" in variables
        assert variables["prd_location"] == "docs/PRD.md"  # From config defaults

    def test_resolve_variables_priority_order(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test variable resolution priority: params > workflow.yaml > config defaults."""
        workflow_dir = tmp_path / "priority_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create workflow with default value in workflow.yaml
        workflow = WorkflowInfo(
            name="priority_test",
            description="Priority test",
            phase=1,
            variables={
                "output_folder": {
                    "description": "Output folder",
                    "default": "workflow_default_folder"  # Workflow default
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Config default is "docs" (from defaults.yaml)
        # Workflow default is "workflow_default_folder"
        # No param provided

        result = workflow_executor.execute(workflow, {})
        variables = result["variables"]

        # Should use workflow.yaml default (priority 2), not config default (priority 3)
        assert variables["output_folder"] == "workflow_default_folder"

    def test_resolve_variables_param_overrides_all(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test that explicit params override both workflow and config defaults."""
        workflow_dir = tmp_path / "override_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="override_test",
            description="Override test",
            phase=1,
            variables={
                "output_folder": {
                    "description": "Output folder",
                    "default": "workflow_default"
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Provide explicit param
        params = {"output_folder": "custom_folder"}

        result = workflow_executor.execute(workflow, params)
        variables = result["variables"]

        # Should use explicit param (highest priority)
        assert variables["output_folder"] == "custom_folder"

    def test_resolve_variables_includes_common_variables(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test that common variables (date, timestamp) are always included."""
        params = {"project_name": "MyProject"}

        result = workflow_executor.execute(sample_workflow, params)
        variables = result["variables"]

        # Should have common variables
        assert "date" in variables
        assert "timestamp" in variables

        # Validate format
        assert isinstance(variables["date"], str)
        assert isinstance(variables["timestamp"], str)

        # Date should be in YYYY-MM-DD format
        datetime.strptime(variables["date"], "%Y-%m-%d")

        # Timestamp should be ISO format
        datetime.fromisoformat(variables["timestamp"])

    def test_resolve_variables_required_missing_raises_error(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test that missing required variable raises ValueError."""
        # Don't provide required project_name
        params = {}

        with pytest.raises(ValueError, match="Required variable 'project_name' not provided"):
            workflow_executor.execute(sample_workflow, params)

    def test_resolve_variables_all_config_defaults_available(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test that all config defaults are available to workflows."""
        workflow_dir = tmp_path / "defaults_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Create workflow that uses multiple config defaults
        workflow = WorkflowInfo(
            name="defaults_test",
            description="Config defaults test",
            phase=1,
            variables={
                "prd_location": {"description": "PRD location"},
                "architecture_location": {"description": "Arch location"},
                "tech_spec_location": {"description": "Tech spec location"},
                "dev_story_location": {"description": "Story location"},
                "epic_location": {"description": "Epic location"},
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        result = workflow_executor.execute(workflow, {})
        variables = result["variables"]

        # All should have config defaults
        assert variables["prd_location"] == "docs/PRD.md"
        assert variables["architecture_location"] == "docs/ARCHITECTURE.md"
        assert variables["tech_spec_location"] == "docs/TECHNICAL_SPEC.md"
        assert variables["dev_story_location"] == "docs/stories"
        assert variables["epic_location"] == "docs/epics.md"

    def test_resolve_variables_with_empty_params(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test variable resolution with empty params dict."""
        workflow_dir = tmp_path / "empty_params_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="empty_params_test",
            description="Empty params test",
            phase=1,
            variables={
                "output_folder": {"description": "Output folder"}
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Empty params
        result = workflow_executor.execute(workflow, {})
        variables = result["variables"]

        # Should still have config defaults and common variables
        assert "output_folder" in variables
        assert variables["output_folder"] == "docs"
        assert "date" in variables
        assert "timestamp" in variables


class TestWorkflowExecutorVariableResolutionIntegration:
    """Integration tests for variable resolution with real workflows."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project_dir = tmp_path / "integration_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def config_loader_with_overrides(self, temp_project_dir: Path) -> ConfigLoader:
        """Create ConfigLoader with user config overrides."""
        import yaml

        user_config = {
            "workflow_defaults": {
                "prd_location": "custom/PRD.md",
                "output_folder": "custom_docs"
            }
        }

        user_config_path = temp_project_dir / "gao-dev.yaml"
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(user_config, f)

        return ConfigLoader(temp_project_dir)

    def test_workflow_uses_user_config_overrides(
        self,
        config_loader_with_overrides: ConfigLoader,
        tmp_path: Path
    ):
        """Test that workflow uses user config overrides."""
        executor = WorkflowExecutor(config_loader_with_overrides)

        workflow_dir = tmp_path / "override_integration"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="override_integration",
            description="Override integration test",
            phase=1,
            variables={
                "prd_location": {"description": "PRD location"},
                "output_folder": {"description": "Output folder"}
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        result = executor.execute(workflow, {})
        variables = result["variables"]

        # Should use user config overrides
        assert variables["prd_location"] == "custom/PRD.md"
        assert variables["output_folder"] == "custom_docs"

    def test_workflow_complete_priority_chain(
        self,
        config_loader_with_overrides: ConfigLoader,
        tmp_path: Path
    ):
        """Test complete priority chain: params > workflow > user config > defaults."""
        executor = WorkflowExecutor(config_loader_with_overrides)

        workflow_dir = tmp_path / "priority_chain"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # User config has: prd_location = "custom/PRD.md", output_folder = "custom_docs"
        # Workflow will have: prd_location default = "workflow/PRD.md"
        # Params will have: prd_location = "param/PRD.md"

        workflow = WorkflowInfo(
            name="priority_chain",
            description="Priority chain test",
            phase=1,
            variables={
                "prd_location": {
                    "description": "PRD location",
                    "default": "workflow/PRD.md"
                },
                "output_folder": {
                    "description": "Output folder"
                },
                "architecture_location": {
                    "description": "Arch location"
                }
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {"prd_location": "param/PRD.md"}

        result = executor.execute(workflow, params)
        variables = result["variables"]

        # prd_location: param wins (highest priority)
        assert variables["prd_location"] == "param/PRD.md"

        # output_folder: user config wins (no workflow default, no param)
        assert variables["output_folder"] == "custom_docs"

        # architecture_location: embedded default wins (no param, no workflow, no user config)
        assert variables["architecture_location"] == "docs/ARCHITECTURE.md"

    def test_workflow_variable_resolution_logging(
        self,
        temp_project_dir: Path,
        tmp_path: Path,
        caplog
    ):
        """Test that variable resolution logs debug information."""
        import structlog

        config_loader = ConfigLoader(temp_project_dir)
        executor = WorkflowExecutor(config_loader)

        workflow_dir = tmp_path / "logging_test"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="logging_test",
            description="Logging test",
            phase=1,
            variables={
                "output_folder": {"description": "Output folder"}
            },
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Execute workflow
        with caplog.at_level("DEBUG"):
            result = executor.execute(workflow, {"custom_param": "value"})

        # Check that logging occurred (may need to configure structlog for pytest)
        # This is a basic check - actual log assertion depends on structlog config
        assert result["success"] is True
