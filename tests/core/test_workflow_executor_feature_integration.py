"""Tests for WorkflowExecutor feature integration (Story 34.3).

Tests the integration of FeaturePathResolver into WorkflowExecutor for intelligent
feature_name resolution and feature-scoped path generation.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from gao_dev.core.workflow_executor import WorkflowExecutor
from gao_dev.core.config_loader import ConfigLoader
from gao_dev.core.models.workflow import WorkflowInfo
from gao_dev.core.models.workflow_context import WorkflowContext
from gao_dev.core.services.feature_state_service import FeatureStateService, FeatureScope


class TestFeatureNameResolution:
    """Test feature_name resolution with 6-level priority."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project directory with .gao-dev structure."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create .gao-dev directory
        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        # Create features directory
        features_dir = project_dir / "docs" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)

        return project_dir

    @pytest.fixture
    def feature_service(self, temp_project: Path) -> FeatureStateService:
        """Create FeatureStateService with test features."""
        service = FeatureStateService(temp_project)

        # Create test features
        service.create_feature("mvp", FeatureScope.MVP, scale_level=2)
        service.create_feature("user-auth", FeatureScope.FEATURE, scale_level=3)
        service.create_feature("payment", FeatureScope.FEATURE, scale_level=3)

        return service

    @pytest.fixture
    def config_loader(self, temp_project: Path) -> ConfigLoader:
        """Create ConfigLoader."""
        return ConfigLoader(temp_project)

    @pytest.fixture
    def workflow_executor(
        self,
        config_loader: ConfigLoader,
        temp_project: Path,
        feature_service: FeatureStateService
    ) -> WorkflowExecutor:
        """Create WorkflowExecutor with feature integration."""
        return WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=feature_service
        )

    @pytest.fixture
    def sample_workflow(self, tmp_path: Path) -> WorkflowInfo:
        """Create sample workflow."""
        workflow_dir = tmp_path / "workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        return WorkflowInfo(
            name="test_workflow",
            description="Test workflow",
            phase=1,
            variables={
                "feature_name": {
                    "description": "Feature name",
                    "required": False
                }
            },
            required_tools=["Read", "Write"],
            templates={},
            installed_path=workflow_dir
        )

    def test_priority_1_explicit_parameter(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test Priority 1: Explicit parameter resolves correctly."""
        params = {"feature_name": "user-auth"}

        resolved = workflow_executor.resolve_variables(sample_workflow, params)

        assert resolved["feature_name"] == "user-auth"

    def test_priority_2_workflow_context_metadata(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test Priority 2: WorkflowContext.metadata['feature_name'] resolves."""
        context = WorkflowContext(
            initial_prompt="test",
            metadata={"feature_name": "payment"}
        )

        resolved = workflow_executor.resolve_variables(sample_workflow, {}, context=context)

        assert resolved["feature_name"] == "payment"

    def test_priority_3_cwd_in_feature_folder(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo,
        temp_project: Path,
        monkeypatch
    ):
        """Test Priority 3: CWD in feature folder resolves."""
        # Create feature directory and change to it
        feature_dir = temp_project / "docs" / "features" / "user-auth"
        feature_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.chdir(feature_dir)

        resolved = workflow_executor.resolve_variables(sample_workflow, {})

        assert resolved["feature_name"] == "user-auth"

    def test_priority_4_single_feature_auto_detect(
        self,
        temp_project: Path,
        config_loader: ConfigLoader,
        sample_workflow: WorkflowInfo
    ):
        """Test Priority 4: Single feature (besides MVP) auto-detects."""
        # Create service with only MVP and one feature
        service = FeatureStateService(temp_project)
        service.create_feature("mvp", FeatureScope.MVP, scale_level=2)
        service.create_feature("user-auth", FeatureScope.FEATURE, scale_level=3)

        executor = WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=service
        )

        resolved = executor.resolve_variables(sample_workflow, {})

        assert resolved["feature_name"] == "user-auth"

    def test_priority_5_mvp_auto_detect(
        self,
        temp_project: Path,
        config_loader: ConfigLoader,
        sample_workflow: WorkflowInfo
    ):
        """Test Priority 5: MVP auto-detects when only feature."""
        # Create service with only MVP
        service = FeatureStateService(temp_project)
        service.create_feature("mvp", FeatureScope.MVP, scale_level=2)

        executor = WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=service
        )

        resolved = executor.resolve_variables(sample_workflow, {})

        assert resolved["feature_name"] == "mvp"

    def test_priority_6_ambiguous_raises_error_for_required_workflow(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test Priority 6: Ambiguous (multiple features) raises error for required workflow."""
        # Create workflow that requires feature_name
        workflow_dir = tmp_path / "feature_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_prd",  # This is in feature_workflows list
            description="Create PRD",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Multiple features exist (mvp, user-auth, payment from fixture)
        with pytest.raises(ValueError, match="Cannot resolve feature_name"):
            workflow_executor.resolve_variables(workflow, {})

    def test_priority_6_ambiguous_fallback_for_optional_workflow(
        self,
        workflow_executor: WorkflowExecutor,
        sample_workflow: WorkflowInfo
    ):
        """Test Priority 6: Ambiguous uses legacy paths for optional workflow."""
        # Multiple features exist (mvp, user-auth, payment from fixture)
        # sample_workflow doesn't require feature_name

        resolved = workflow_executor.resolve_variables(sample_workflow, {})

        # Should not have feature_name (will use legacy paths)
        assert "feature_name" not in resolved


class TestWorkflowContextPersistence:
    """Test WorkflowContext persistence across workflow executions."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project."""
        project_dir = tmp_path / "context_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        return project_dir

    @pytest.fixture
    def feature_service(self, temp_project: Path) -> FeatureStateService:
        """Create FeatureStateService."""
        service = FeatureStateService(temp_project)
        service.create_feature("mvp", FeatureScope.MVP, scale_level=2)
        service.create_feature("user-auth", FeatureScope.FEATURE, scale_level=3)
        return service

    @pytest.fixture
    def workflow_executor(
        self,
        temp_project: Path,
        feature_service: FeatureStateService
    ) -> WorkflowExecutor:
        """Create WorkflowExecutor."""
        config_loader = ConfigLoader(temp_project)
        return WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=feature_service
        )

    def test_context_persists_across_multiple_workflows(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test feature_name persists in context across multiple workflow executions."""
        # Create context with feature_name
        context = WorkflowContext(
            initial_prompt="Build user auth",
            metadata={"feature_name": "user-auth"}
        )

        # Execute multiple workflows with same context
        workflow_dir = tmp_path / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflows = []
        for i in range(3):
            workflow = WorkflowInfo(
                name=f"workflow_{i}",
                description=f"Workflow {i}",
                phase=1,
                variables={},
                required_tools=[],
                templates={},
                installed_path=workflow_dir
            )
            workflows.append(workflow)

        # Resolve variables for all workflows
        results = []
        for workflow in workflows:
            resolved = workflow_executor.resolve_variables(workflow, {}, context=context)
            results.append(resolved)

        # All should have same feature_name from context
        for resolved in results:
            assert resolved["feature_name"] == "user-auth"


class TestFeatureScopedPathGeneration:
    """Test feature-scoped path generation."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project."""
        project_dir = tmp_path / "path_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        return project_dir

    @pytest.fixture
    def feature_service(self, temp_project: Path) -> FeatureStateService:
        """Create FeatureStateService."""
        service = FeatureStateService(temp_project)
        service.create_feature("user-auth", FeatureScope.FEATURE, scale_level=3)
        return service

    @pytest.fixture
    def workflow_executor(
        self,
        temp_project: Path,
        feature_service: FeatureStateService
    ) -> WorkflowExecutor:
        """Create WorkflowExecutor."""
        config_loader = ConfigLoader(temp_project)
        return WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=feature_service
        )

    def test_generates_prd_path(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test PRD path generation with resolved feature_name."""
        workflow_dir = tmp_path / "prd_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_prd",
            description="Create PRD",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {"feature_name": "user-auth"}

        resolved = workflow_executor.resolve_variables(workflow, params)

        assert "prd_location" in resolved
        assert resolved["prd_location"] == "docs\\features\\user-auth\\PRD.md"

    def test_generates_epic_path(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test epic path generation with epic and epic_name."""
        workflow_dir = tmp_path / "epic_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_epic",
            description="Create epic",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {
            "feature_name": "user-auth",
            "epic": "1",
            "epic_name": "foundation"
        }

        resolved = workflow_executor.resolve_variables(workflow, params)

        assert "epic_location" in resolved
        assert resolved["epic_location"] == "docs\\features\\user-auth\\epics\\1-foundation\\README.md"
        assert "epic_folder" in resolved
        assert resolved["epic_folder"] == "docs\\features\\user-auth\\epics\\1-foundation"

    def test_generates_story_path(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test story path generation with epic, epic_name, and story."""
        workflow_dir = tmp_path / "story_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_story",
            description="Create story",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {
            "feature_name": "user-auth",
            "epic": "2",
            "epic_name": "oauth",
            "story": "3"
        }

        resolved = workflow_executor.resolve_variables(workflow, params)

        assert "story_location" in resolved
        assert resolved["story_location"] == "docs\\features\\user-auth\\epics\\2-oauth\\stories\\story-2.3.md"
        assert "story_folder" in resolved
        assert resolved["story_folder"] == "docs\\features\\user-auth\\epics\\2-oauth\\stories"


class TestFallbackToLegacyPaths:
    """Test fallback to legacy paths when feature_name can't be resolved."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project."""
        project_dir = tmp_path / "fallback_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        return project_dir

    @pytest.fixture
    def feature_service(self, temp_project: Path) -> FeatureStateService:
        """Create FeatureStateService with multiple features."""
        service = FeatureStateService(temp_project)
        service.create_feature("feature1", FeatureScope.FEATURE, scale_level=3)
        service.create_feature("feature2", FeatureScope.FEATURE, scale_level=3)
        return service

    @pytest.fixture
    def workflow_executor(
        self,
        temp_project: Path,
        feature_service: FeatureStateService
    ) -> WorkflowExecutor:
        """Create WorkflowExecutor."""
        config_loader = ConfigLoader(temp_project)
        return WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=feature_service
        )

    def test_uses_legacy_paths_when_not_required(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test workflow uses legacy paths when feature_name not required."""
        workflow_dir = tmp_path / "optional_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="optional_feature_workflow",
            description="Optional feature workflow",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Multiple features exist, ambiguous
        resolved = workflow_executor.resolve_variables(workflow, {})

        # Should not resolve feature_name
        assert "feature_name" not in resolved

        # Will have feature-scoped paths with {{feature_name}} placeholder
        # (not legacy paths, since we don't actively substitute to legacy)
        assert "prd_location" in resolved
        assert "{{feature_name}}" in resolved["prd_location"]

    def test_raises_error_when_required(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test raises error when feature_name required but can't resolve."""
        workflow_dir = tmp_path / "required_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_prd",  # Requires feature_name
            description="Create PRD",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Multiple features exist, ambiguous, and workflow requires feature_name
        with pytest.raises(ValueError) as exc_info:
            workflow_executor.resolve_variables(workflow, {})

        assert "requires feature_name but cannot resolve" in str(exc_info.value)
        assert "Specify feature_name explicitly" in str(exc_info.value)


class TestErrorHandling:
    """Test error handling for feature resolution."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project."""
        project_dir = tmp_path / "error_project"
        project_dir.mkdir(parents=True, exist_ok=True)

        gao_dev_dir = project_dir / ".gao-dev"
        gao_dev_dir.mkdir(parents=True, exist_ok=True)

        return project_dir

    @pytest.fixture
    def feature_service(self, temp_project: Path) -> FeatureStateService:
        """Create FeatureStateService with multiple features."""
        service = FeatureStateService(temp_project)
        service.create_feature("feature-a", FeatureScope.FEATURE, scale_level=3)
        service.create_feature("feature-b", FeatureScope.FEATURE, scale_level=3)
        service.create_feature("feature-c", FeatureScope.FEATURE, scale_level=3)
        return service

    @pytest.fixture
    def workflow_executor(
        self,
        temp_project: Path,
        feature_service: FeatureStateService
    ) -> WorkflowExecutor:
        """Create WorkflowExecutor."""
        config_loader = ConfigLoader(temp_project)
        return WorkflowExecutor(
            config_loader=config_loader,
            project_root=temp_project,
            feature_service=feature_service
        )

    def test_error_lists_all_features(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test error message lists all available features."""
        workflow_dir = tmp_path / "error_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="create_architecture",  # Requires feature_name
            description="Create architecture",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        with pytest.raises(ValueError) as exc_info:
            workflow_executor.resolve_variables(workflow, {})

        error_msg = str(exc_info.value)
        assert "feature-a" in error_msg
        assert "feature-b" in error_msg
        assert "feature-c" in error_msg


class TestBackwardCompatibility:
    """Test backward compatibility when feature_resolver not provided."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create temporary project."""
        project_dir = tmp_path / "compat_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    @pytest.fixture
    def workflow_executor(self, temp_project: Path) -> WorkflowExecutor:
        """Create WorkflowExecutor WITHOUT feature_service (old style)."""
        config_loader = ConfigLoader(temp_project)
        return WorkflowExecutor(config_loader=config_loader)

    def test_works_without_feature_service(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test executor works without feature_service (backward compatible)."""
        workflow_dir = tmp_path / "compat_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="test_workflow",
            description="Test workflow",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        # Should work fine, just won't have feature_name resolution
        resolved = workflow_executor.resolve_variables(workflow, {})

        assert "feature_name" not in resolved
        assert "date" in resolved
        assert "timestamp" in resolved

    def test_explicit_feature_name_still_works(
        self,
        workflow_executor: WorkflowExecutor,
        tmp_path: Path
    ):
        """Test explicit feature_name parameter works without feature_service."""
        workflow_dir = tmp_path / "compat_explicit_workflow"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow = WorkflowInfo(
            name="test_workflow",
            description="Test workflow",
            phase=1,
            variables={},
            required_tools=[],
            templates={},
            installed_path=workflow_dir
        )

        params = {"feature_name": "my-feature"}

        resolved = workflow_executor.resolve_variables(workflow, params)

        # Explicit parameter should still work
        assert resolved["feature_name"] == "my-feature"
