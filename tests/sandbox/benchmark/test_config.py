"""Tests for benchmark configuration models."""

import pytest
from pathlib import Path
import tempfile
import yaml
import json

from gao_dev.sandbox.benchmark.config import (
    BenchmarkConfig,
    SuccessCriteria,
    WorkflowPhaseConfig,
)


class TestSuccessCriteria:
    """Tests for SuccessCriteria dataclass."""

    def test_default_values(self):
        """Test default success criteria values."""
        criteria = SuccessCriteria()

        assert criteria.min_test_coverage == 80.0
        assert criteria.max_manual_interventions == 0
        assert criteria.max_errors == 0
        assert criteria.required_features == []
        assert criteria.quality_gates == {}

    def test_custom_values(self):
        """Test creating success criteria with custom values."""
        criteria = SuccessCriteria(
            min_test_coverage=90.0,
            max_manual_interventions=3,
            max_errors=5,
            required_features=["auth", "crud"],
            quality_gates={"linting": 100},
        )

        assert criteria.min_test_coverage == 90.0
        assert criteria.max_manual_interventions == 3
        assert criteria.max_errors == 5
        assert criteria.required_features == ["auth", "crud"]
        assert criteria.quality_gates == {"linting": 100}

    def test_validate_valid_criteria(self):
        """Test validation of valid success criteria."""
        criteria = SuccessCriteria(
            min_test_coverage=85.0, max_manual_interventions=2, max_errors=3
        )

        assert criteria.validate() is True

    def test_validate_invalid_coverage_too_low(self):
        """Test validation fails for coverage < 0."""
        criteria = SuccessCriteria(min_test_coverage=-1.0)

        assert criteria.validate() is False

    def test_validate_invalid_coverage_too_high(self):
        """Test validation fails for coverage > 100."""
        criteria = SuccessCriteria(min_test_coverage=101.0)

        assert criteria.validate() is False

    def test_validate_invalid_negative_interventions(self):
        """Test validation fails for negative interventions."""
        criteria = SuccessCriteria(max_manual_interventions=-1)

        assert criteria.validate() is False

    def test_validate_invalid_negative_errors(self):
        """Test validation fails for negative errors."""
        criteria = SuccessCriteria(max_errors=-1)

        assert criteria.validate() is False


class TestWorkflowPhaseConfig:
    """Tests for WorkflowPhaseConfig dataclass."""

    def test_default_values(self):
        """Test default workflow phase values."""
        phase = WorkflowPhaseConfig(phase_name="test-phase")

        assert phase.phase_name == "test-phase"
        assert phase.timeout_seconds == 3600
        assert phase.expected_artifacts == []
        assert phase.quality_gates == {}
        assert phase.skip_if_failed is False

    def test_custom_values(self):
        """Test creating phase with custom values."""
        phase = WorkflowPhaseConfig(
            phase_name="implementation",
            timeout_seconds=7200,
            expected_artifacts=["src/main.py", "tests/test_main.py"],
            quality_gates={"coverage": 80},
            skip_if_failed=True,
        )

        assert phase.phase_name == "implementation"
        assert phase.timeout_seconds == 7200
        assert phase.expected_artifacts == ["src/main.py", "tests/test_main.py"]
        assert phase.quality_gates == {"coverage": 80}
        assert phase.skip_if_failed is True

    def test_validate_valid_phase(self):
        """Test validation of valid phase config."""
        phase = WorkflowPhaseConfig(phase_name="test", timeout_seconds=3600)

        assert phase.validate() is True

    def test_validate_invalid_empty_name(self):
        """Test validation fails for empty phase name."""
        phase = WorkflowPhaseConfig(phase_name="")

        assert phase.validate() is False

    def test_validate_invalid_zero_timeout(self):
        """Test validation fails for zero timeout."""
        phase = WorkflowPhaseConfig(phase_name="test", timeout_seconds=0)

        assert phase.validate() is False

    def test_validate_invalid_negative_timeout(self):
        """Test validation fails for negative timeout."""
        phase = WorkflowPhaseConfig(phase_name="test", timeout_seconds=-100)

        assert phase.validate() is False


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig dataclass."""

    def test_minimal_config(self):
        """Test creating minimal valid config."""
        config = BenchmarkConfig(
            name="test-benchmark",
            description="A test benchmark",
            boilerplate_url="https://github.com/user/template",
        )

        assert config.name == "test-benchmark"
        assert config.description == "A test benchmark"
        assert config.version == "1.0.0"
        assert config.project_name == ""
        assert config.boilerplate_url == "https://github.com/user/template"
        assert config.timeout_seconds == 7200
        assert isinstance(config.success_criteria, SuccessCriteria)
        assert config.workflow_phases == []
        assert config.metadata == {}

    def test_full_config(self):
        """Test creating full config with all options."""
        config = BenchmarkConfig(
            name="full-benchmark",
            description="Full featured benchmark",
            version="2.0.0",
            project_name="my-project",
            boilerplate_url="https://github.com/user/template",
            timeout_seconds=14400,
            success_criteria=SuccessCriteria(min_test_coverage=90.0),
            workflow_phases=[
                WorkflowPhaseConfig(phase_name="planning"),
                WorkflowPhaseConfig(phase_name="implementation"),
            ],
            metadata={"category": "test"},
        )

        assert config.name == "full-benchmark"
        assert config.description == "Full featured benchmark"
        assert config.version == "2.0.0"
        assert config.project_name == "my-project"
        assert config.timeout_seconds == 14400
        assert config.success_criteria.min_test_coverage == 90.0
        assert len(config.workflow_phases) == 2
        assert config.metadata == {"category": "test"}

    def test_validate_valid_config(self):
        """Test validation of valid config."""
        config = BenchmarkConfig(
            name="valid",
            description="Valid config",
            boilerplate_url="https://github.com/user/template",
            workflow_phases=[
                WorkflowPhaseConfig(phase_name="test_phase", timeout_seconds=60)
            ],
        )

        assert config.validate() is True

    def test_validate_invalid_empty_name(self):
        """Test validation fails for empty name."""
        config = BenchmarkConfig(name="", description="Test", boilerplate_url="url")

        assert config.validate() is False

    def test_validate_invalid_empty_description(self):
        """Test validation fails for empty description."""
        config = BenchmarkConfig(
            name="test", description="", boilerplate_url="url"
        )

        assert config.validate() is False

    def test_validate_invalid_zero_timeout(self):
        """Test validation fails for zero timeout."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="url",
            timeout_seconds=0,
        )

        assert config.validate() is False

    def test_validate_invalid_success_criteria(self):
        """Test validation fails for invalid success criteria."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="url",
            success_criteria=SuccessCriteria(min_test_coverage=101.0),
        )

        assert config.validate() is False

    def test_validate_invalid_workflow_phase(self):
        """Test validation fails for invalid workflow phase."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_url="url",
            workflow_phases=[WorkflowPhaseConfig(phase_name="", timeout_seconds=0)],
        )

        assert config.validate() is False

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = BenchmarkConfig(
            name="test",
            description="Test config",
            boilerplate_url="https://github.com/user/template",
        )

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["name"] == "test"
        assert data["description"] == "Test config"
        assert "success_criteria" in data
        assert "workflow_phases" in data

    def test_to_dict_with_path(self):
        """Test that Path objects are converted to strings in to_dict."""
        config = BenchmarkConfig(
            name="test",
            description="Test",
            boilerplate_path=Path("/some/path"),
        )

        data = config.to_dict()

        assert isinstance(data["boilerplate_path"], str)
        assert data["boilerplate_path"] == str(Path("/some/path"))

    def test_from_yaml(self):
        """Test loading config from YAML file."""
        yaml_content = """
name: test-benchmark
description: A test benchmark
version: 1.0.0
boilerplate_url: https://github.com/user/template
timeout_seconds: 3600
success_criteria:
  min_test_coverage: 85.0
  max_manual_interventions: 2
workflow_phases:
  - phase_name: planning
    timeout_seconds: 1800
  - phase_name: implementation
    timeout_seconds: 3600
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = BenchmarkConfig.from_yaml(temp_path)

            assert config.name == "test-benchmark"
            assert config.description == "A test benchmark"
            assert config.timeout_seconds == 3600
            assert config.success_criteria.min_test_coverage == 85.0
            assert len(config.workflow_phases) == 2
            assert config.workflow_phases[0].phase_name == "planning"
        finally:
            temp_path.unlink()

    def test_from_json(self):
        """Test loading config from JSON file."""
        json_content = {
            "name": "test-benchmark",
            "description": "A test benchmark",
            "boilerplate_url": "https://github.com/user/template",
            "success_criteria": {"min_test_coverage": 90.0},
            "workflow_phases": [{"phase_name": "implementation"}],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(json_content, f)
            temp_path = Path(f.name)

        try:
            config = BenchmarkConfig.from_json(temp_path)

            assert config.name == "test-benchmark"
            assert config.description == "A test benchmark"
            assert config.success_criteria.min_test_coverage == 90.0
            assert len(config.workflow_phases) == 1
        finally:
            temp_path.unlink()

    def test_to_yaml(self):
        """Test saving config to YAML file."""
        config = BenchmarkConfig(
            name="test",
            description="Test config",
            boilerplate_url="https://github.com/user/template",
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            config.to_yaml(temp_path)

            # Load it back
            loaded_config = BenchmarkConfig.from_yaml(temp_path)
            assert loaded_config.name == "test"
            assert loaded_config.description == "Test config"
        finally:
            temp_path.unlink()

    def test_to_json(self):
        """Test saving config to JSON file."""
        config = BenchmarkConfig(
            name="test",
            description="Test config",
            boilerplate_url="https://github.com/user/template",
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = Path(f.name)

        try:
            config.to_json(temp_path)

            # Load it back
            loaded_config = BenchmarkConfig.from_json(temp_path)
            assert loaded_config.name == "test"
            assert loaded_config.description == "Test config"
        finally:
            temp_path.unlink()


class TestExampleConfigs:
    """Tests for example benchmark configurations."""

    def test_todo_app_config_valid(self):
        """Test that todo-app.yaml is valid."""
        config_path = Path("sandbox/benchmarks/todo-app.yaml")

        if not config_path.exists():
            pytest.skip("Example config not found")

        config = BenchmarkConfig.from_yaml(config_path)

        assert config.validate() is True
        assert config.name == "todo-app"
        assert len(config.workflow_phases) > 0

    def test_minimal_config_valid(self):
        """Test that minimal.yaml is valid."""
        config_path = Path("sandbox/benchmarks/minimal.yaml")

        if not config_path.exists():
            pytest.skip("Example config not found")

        config = BenchmarkConfig.from_yaml(config_path)

        assert config.validate() is True
        assert config.name == "minimal"

    def test_full_featured_config_valid(self):
        """Test that full-featured.yaml is valid."""
        config_path = Path("sandbox/benchmarks/full-featured.yaml")

        if not config_path.exists():
            pytest.skip("Example config not found")

        config = BenchmarkConfig.from_yaml(config_path)

        assert config.validate() is True
        assert config.name == "full-featured-ecommerce"
        assert len(config.workflow_phases) > 0


class TestStoryBasedConfig:
    """Tests for story-based configuration (Epic 6)."""

    def test_story_config_creation(self):
        """Test creating StoryConfig."""
        from gao_dev.sandbox.benchmark.config import StoryConfig

        story = StoryConfig(
            name="Implement login feature",
            agent="Amelia",
            description="User authentication",
            acceptance_criteria=["Users can log in", "Sessions persist"],
            story_points=5,
        )

        assert story.name == "Implement login feature"
        assert story.agent == "Amelia"
        assert story.story_points == 5
        assert len(story.acceptance_criteria) == 2
        assert story.validate() is True

    def test_epic_config_creation(self):
        """Test creating EpicConfig with stories."""
        from gao_dev.sandbox.benchmark.config import EpicConfig, StoryConfig

        stories = [
            StoryConfig(name="Story 1", agent="Amelia", story_points=3),
            StoryConfig(name="Story 2", agent="Bob", story_points=5),
        ]

        epic = EpicConfig(
            name="User Authentication",
            description="Complete auth system",
            stories=stories,
        )

        assert epic.name == "User Authentication"
        assert len(epic.stories) == 2
        assert epic.total_story_points() == 8
        assert epic.validate() is True

    def test_benchmark_config_story_based(self):
        """Test BenchmarkConfig with epics (story-based mode)."""
        from gao_dev.sandbox.benchmark.config import (
            BenchmarkConfig,
            EpicConfig,
            StoryConfig,
        )

        epic = EpicConfig(
            name="Test Epic",
            description="Test epic description",
            stories=[
                StoryConfig(name="Story 1", agent="Amelia", story_points=3),
            ],
        )

        config = BenchmarkConfig(
            name="story-based-test",
            description="Test story-based config",
            epics=[epic],
        )

        assert config.is_story_based() is True
        assert config.is_phase_based() is False
        assert config.total_stories() == 1
        assert config.total_story_points() == 3
        assert config.validate() is True

    def test_backward_compatibility_phase_based(self):
        """Test that phase-based configs still work."""
        from gao_dev.sandbox.benchmark.config import (
            BenchmarkConfig,
            WorkflowPhaseConfig,
        )

        config = BenchmarkConfig(
            name="phase-based-test",
            description="Test phase-based config",
            workflow_phases=[
                WorkflowPhaseConfig(phase_name="Planning", timeout_seconds=600),
            ],
        )

        assert config.is_phase_based() is True
        assert config.is_story_based() is False
        assert config.total_stories() == 0
        assert config.validate() is True

    def test_validation_rejects_both_modes(self):
        """Test that config with both phases and epics is invalid."""
        from gao_dev.sandbox.benchmark.config import (
            BenchmarkConfig,
            EpicConfig,
            StoryConfig,
            WorkflowPhaseConfig,
        )

        config = BenchmarkConfig(
            name="mixed-test",
            description="Invalid mixed config",
            workflow_phases=[WorkflowPhaseConfig(phase_name="Test", timeout_seconds=60)],
            epics=[
                EpicConfig(
                    name="Test",
                    description="Test",
                    stories=[StoryConfig(name="Test", agent="Amelia")],
                )
            ],
        )

        # Should be invalid - can't have both
        assert config.validate() is False

    def test_validation_rejects_neither_mode(self):
        """Test that config with neither phases nor epics is invalid."""
        from gao_dev.sandbox.benchmark.config import BenchmarkConfig

        config = BenchmarkConfig(
            name="empty-test",
            description="Invalid empty config",
        )

        # Should be invalid - must have one or the other
        assert config.validate() is False
