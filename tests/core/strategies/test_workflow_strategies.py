"""
Unit tests for workflow build strategies.

Tests the Strategy Pattern implementation for workflow selection,
including ScaleLevelStrategy, ProjectTypeStrategy, CustomWorkflowStrategy,
and WorkflowStrategyRegistry.

Story 5.4: Updated to use orchestrator.models instead of brian_orchestrator.
"""

import pytest
from unittest.mock import Mock, MagicMock

from gao_dev.core.strategies.workflow_strategies import (
    WorkflowStrategyRegistry,
    ScaleLevelStrategy,
    ProjectTypeStrategy,
    CustomWorkflowStrategy
)
from gao_dev.core.models.workflow_context import WorkflowContext
from gao_dev.orchestrator.models import ScaleLevel, ProjectType


class TestWorkflowStrategyRegistry:
    """Test suite for WorkflowStrategyRegistry."""

    @pytest.fixture
    def registry(self):
        """Create WorkflowStrategyRegistry instance."""
        return WorkflowStrategyRegistry()

    @pytest.fixture
    def mock_workflow_registry(self):
        """Create mock workflow registry."""
        return Mock()

    def test_registry_initialization(self, registry):
        """Test that registry initializes correctly."""
        assert registry._strategies == []

    def test_register_strategy(self, registry, mock_workflow_registry):
        """Test registering a strategy."""
        strategy = ScaleLevelStrategy(mock_workflow_registry)
        registry.register_strategy(strategy)

        assert len(registry._strategies) == 1
        assert registry._strategies[0] == strategy

    def test_register_multiple_strategies_sorted_by_priority(self, registry, mock_workflow_registry):
        """Test that strategies are sorted by priority (highest first)."""
        scale_strategy = ScaleLevelStrategy(mock_workflow_registry)  # priority 50
        custom_strategy = CustomWorkflowStrategy(mock_workflow_registry)  # priority 100
        project_strategy = ProjectTypeStrategy(mock_workflow_registry)  # priority 75

        registry.register_strategy(scale_strategy)
        registry.register_strategy(custom_strategy)
        registry.register_strategy(project_strategy)

        # Should be sorted: custom (100), project (75), scale (50)
        assert len(registry._strategies) == 3
        assert isinstance(registry._strategies[0], CustomWorkflowStrategy)
        assert isinstance(registry._strategies[1], ProjectTypeStrategy)
        assert isinstance(registry._strategies[2], ScaleLevelStrategy)

    def test_register_invalid_strategy_raises_error(self, registry):
        """Test that registering non-strategy raises TypeError."""
        with pytest.raises(TypeError):
            registry.register_strategy("not a strategy")

    def test_get_strategy_returns_highest_priority_match(self, registry, mock_workflow_registry):
        """Test that get_strategy returns highest priority matching strategy."""
        scale_strategy = ScaleLevelStrategy(mock_workflow_registry)
        custom_strategy = CustomWorkflowStrategy(mock_workflow_registry)

        registry.register_strategy(scale_strategy)
        registry.register_strategy(custom_strategy)

        # Context with custom workflows should match CustomStrategy (higher priority)
        context = WorkflowContext(
            initial_prompt="test",
            custom_workflows=["workflow1", "workflow2"],
            metadata={"scale_level": ScaleLevel.LEVEL_2.value}
        )

        strategy = registry.get_strategy(context)
        assert isinstance(strategy, CustomWorkflowStrategy)

    def test_get_strategy_returns_none_if_no_match(self, registry):
        """Test that get_strategy returns None if no strategy matches."""
        context = WorkflowContext(initial_prompt="test")
        strategy = registry.get_strategy(context)
        assert strategy is None

    def test_list_strategies(self, registry, mock_workflow_registry):
        """Test listing all registered strategies."""
        registry.register_strategy(ScaleLevelStrategy(mock_workflow_registry))
        registry.register_strategy(CustomWorkflowStrategy(mock_workflow_registry))

        strategies = registry.list_strategies()
        assert len(strategies) == 2
        assert "CustomWorkflowStrategy" in strategies
        assert "ScaleLevelStrategy" in strategies


class TestCustomWorkflowStrategy:
    """Test suite for CustomWorkflowStrategy."""

    @pytest.fixture
    def mock_workflow_registry(self):
        """Create mock workflow registry."""
        mock_reg = Mock()
        mock_reg.get_workflow.return_value = Mock(name="test_workflow")
        return mock_reg

    @pytest.fixture
    def strategy(self, mock_workflow_registry):
        """Create CustomWorkflowStrategy instance."""
        return CustomWorkflowStrategy(mock_workflow_registry)

    def test_can_handle_with_custom_workflows(self, strategy):
        """Test that strategy can handle contexts with custom workflows."""
        context = WorkflowContext(
            initial_prompt="test",
            custom_workflows=["workflow1", "workflow2"]
        )
        assert strategy.can_handle(context) is True

    def test_cannot_handle_without_custom_workflows(self, strategy):
        """Test that strategy cannot handle contexts without custom workflows."""
        context = WorkflowContext(initial_prompt="test")
        assert strategy.can_handle(context) is False

    def test_cannot_handle_empty_custom_workflows(self, strategy):
        """Test that strategy cannot handle empty custom workflows list."""
        context = WorkflowContext(initial_prompt="test", custom_workflows=[])
        assert strategy.can_handle(context) is False

    def test_build_workflow_sequence(self, strategy, mock_workflow_registry):
        """Test building workflow sequence from custom workflows."""
        context = WorkflowContext(
            initial_prompt="test",
            custom_workflows=["workflow1", "workflow2"]
        )

        sequence = strategy.build_workflow_sequence(context)

        assert len(sequence.workflows) == 2
        assert mock_workflow_registry.get_workflow.call_count == 2

    def test_get_priority(self, strategy):
        """Test that custom strategy has highest priority."""
        assert strategy.get_priority() == 100


class TestProjectTypeStrategy:
    """Test suite for ProjectTypeStrategy."""

    @pytest.fixture
    def mock_workflow_registry(self):
        """Create mock workflow registry with all needed workflows."""
        mock_reg = Mock()
        mock_reg.get_workflow.return_value = Mock(name="test_workflow")
        return mock_reg

    @pytest.fixture
    def strategy(self, mock_workflow_registry):
        """Create ProjectTypeStrategy instance."""
        return ProjectTypeStrategy(mock_workflow_registry)

    def test_can_handle_brownfield_project(self, strategy):
        """Test that strategy handles brownfield projects."""
        context = WorkflowContext(
            initial_prompt="test",
            project_type=ProjectType.BROWNFIELD
        )
        # Need to mock analysis for is_brownfield property
        from gao_dev.orchestrator.brian_orchestrator import PromptAnalysis
        context.analysis = Mock(is_brownfield=True, is_game_project=False)

        assert strategy.can_handle(context) is True

    def test_can_handle_game_project(self, strategy):
        """Test that strategy handles game projects."""
        context = WorkflowContext(
            initial_prompt="test",
            project_type=ProjectType.GAME
        )
        context.analysis = Mock(is_brownfield=False, is_game_project=True)

        assert strategy.can_handle(context) is True

    def test_can_handle_bug_fix(self, strategy):
        """Test that strategy handles bug fixes."""
        context = WorkflowContext(
            initial_prompt="test",
            project_type=ProjectType.BUG_FIX
        )
        assert strategy.can_handle(context) is True

    def test_cannot_handle_regular_software(self, strategy):
        """Test that strategy doesn't handle regular software projects."""
        context = WorkflowContext(
            initial_prompt="test",
            project_type=ProjectType.SOFTWARE
        )
        context.analysis = Mock(is_brownfield=False, is_game_project=False)

        assert strategy.can_handle(context) is False

    def test_get_priority(self, strategy):
        """Test project type strategy priority."""
        assert strategy.get_priority() == 75


class TestScaleLevelStrategy:
    """Test suite for ScaleLevelStrategy."""

    @pytest.fixture
    def mock_workflow_registry(self):
        """Create mock workflow registry."""
        mock_reg = Mock()
        mock_reg.get_workflow.return_value = Mock(name="test_workflow")
        return mock_reg

    @pytest.fixture
    def strategy(self, mock_workflow_registry):
        """Create ScaleLevelStrategy instance."""
        return ScaleLevelStrategy(mock_workflow_registry)

    def test_can_handle_with_scale_level(self, strategy):
        """Test that strategy handles contexts with scale level."""
        context = WorkflowContext(
            initial_prompt="test",
            scale_level=ScaleLevel.LEVEL_2
        )
        assert strategy.can_handle(context) is True

    def test_cannot_handle_without_scale_level(self, strategy):
        """Test that strategy doesn't handle contexts without scale level."""
        context = WorkflowContext(initial_prompt="test")
        assert strategy.can_handle(context) is False

    @pytest.mark.parametrize("scale_level,expected_workflows", [
        (ScaleLevel.LEVEL_0, 2),  # tech-spec, dev-story
        (ScaleLevel.LEVEL_1, 3),  # tech-spec, create-story, dev-story
        (ScaleLevel.LEVEL_2, 4),  # PRD, tech-spec, create-story, dev-story
        (ScaleLevel.LEVEL_3, 4),  # PRD, architecture, create-story, dev-story
        (ScaleLevel.LEVEL_4, 5),  # PRD, architecture, epic, create-story, dev-story
    ])
    def test_build_sequence_for_different_scale_levels(
        self,
        strategy,
        mock_workflow_registry,
        scale_level,
        expected_workflows
    ):
        """Test that correct number of workflows built for each scale level."""
        context = WorkflowContext(
            initial_prompt="test",
            scale_level=scale_level,
            project_type=ProjectType.SOFTWARE
        )

        sequence = strategy.build_workflow_sequence(context)

        assert len(sequence.workflows) == expected_workflows
        assert sequence.scale_level == scale_level

    def test_level_3_and_4_use_jit_tech_specs(self, strategy, mock_workflow_registry):
        """Test that Level 3 and 4 set jit_tech_specs flag."""
        context_l3 = WorkflowContext(
            initial_prompt="test",
            scale_level=ScaleLevel.LEVEL_3
        )
        context_l4 = WorkflowContext(
            initial_prompt="test",
            scale_level=ScaleLevel.LEVEL_4
        )

        sequence_l3 = strategy.build_workflow_sequence(context_l3)
        sequence_l4 = strategy.build_workflow_sequence(context_l4)

        assert sequence_l3.jit_tech_specs is True
        assert sequence_l4.jit_tech_specs is True

    def test_level_0_1_2_do_not_use_jit_tech_specs(self, strategy, mock_workflow_registry):
        """Test that Level 0, 1, 2 don't set jit_tech_specs flag."""
        for level in [ScaleLevel.LEVEL_0, ScaleLevel.LEVEL_1, ScaleLevel.LEVEL_2]:
            context = WorkflowContext(
                initial_prompt="test",
                scale_level=level
            )
            sequence = strategy.build_workflow_sequence(context)
            assert sequence.jit_tech_specs is False

    def test_get_priority(self, strategy):
        """Test scale level strategy priority."""
        assert strategy.get_priority() == 50
