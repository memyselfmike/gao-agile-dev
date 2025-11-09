"""Tests for Brian Context Augmentation (Story 29.3).

This test suite validates:
- Context extraction from user prompts (AC4)
- Learning context building with 0-5 learnings (AC3)
- Template rendering correctness (AC2)
- Performance target met (<500ms) (AC1)
- Cache hit/miss scenarios (AC6)
- Fallback error handling (AC7)
- Integration with workflow selection (AC5)
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

import pytest

from gao_dev.core.services.learning_application_service import (
    LearningApplicationService,
    ScoredLearning,
)
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.services.ai_analysis_service import AIAnalysisService
from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.orchestrator.models import ScaleLevel


@pytest.fixture
def mock_workflow_registry():
    """Mock workflow registry."""
    registry = Mock(spec=WorkflowRegistry)
    # Mock some workflows
    mock_workflow = Mock()
    mock_workflow.name = "test-workflow"
    registry.get_workflow.return_value = mock_workflow
    return registry


@pytest.fixture
def mock_analysis_service():
    """Mock AI analysis service."""
    return Mock(spec=AIAnalysisService)


@pytest.fixture
def mock_learning_service(tmp_path):
    """Mock learning application service."""
    db_path = tmp_path / "test_documents.db"
    service = Mock(spec=LearningApplicationService)
    service.db_path = db_path
    return service


@pytest.fixture
def brian_orchestrator(
    mock_workflow_registry, mock_analysis_service, mock_learning_service, tmp_path
):
    """Create BrianOrchestrator instance with mocked dependencies."""
    return BrianOrchestrator(
        workflow_registry=mock_workflow_registry,
        analysis_service=mock_analysis_service,
        project_root=tmp_path,
        learning_service=mock_learning_service,
    )


def create_mock_learning(
    learning_id: int,
    category: str = "technical",
    relevance_score: float = 0.8,
    success_rate: float = 0.9,
    confidence: float = 0.85,
    application_count: int = 3,
) -> ScoredLearning:
    """Helper to create mock ScoredLearning."""
    return ScoredLearning(
        learning_id=learning_id,
        topic=f"Topic {learning_id}",
        category=category,
        learning=f"Learning content {learning_id}: Always validate inputs before processing",
        relevance_score=relevance_score,
        success_rate=success_rate,
        confidence_score=confidence,
        application_count=application_count,
        indexed_at=datetime.now().isoformat(),
        metadata={
            "context": f"Applied in past projects for {category} improvements",
            "recommendation": f"Consider applying to similar {category} scenarios",
            "scale_level": 3,
            "project_type": "web_app",
        },
        tags=["validation", "security", "best-practices"],
    )


class TestContextExtraction:
    """Test context extraction from user prompts (AC4)."""

    def test_extract_tags_from_prompt(self, brian_orchestrator):
        """Test extraction of feature tags from prompt."""
        prompt = "Build a todo app with authentication and API endpoints"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert "authentication" in context["tags"] or "auth" in context["tags"]
        assert "api" in context["tags"]

    def test_extract_requirements_from_prompt(self, brian_orchestrator):
        """Test extraction of requirements from prompt."""
        prompt = "Build a secure API with fast performance and encryption"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert "security" in context["requirements"]
        assert "performance" in context["requirements"]

    def test_extract_technologies_from_prompt(self, brian_orchestrator):
        """Test extraction of technologies from prompt."""
        prompt = "Build a React app with PostgreSQL and Redis caching"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert "react" in context["technologies"]
        assert "postgres" in context["technologies"]
        assert "redis" in context["technologies"]

    def test_detect_greenfield_phase(self, brian_orchestrator):
        """Test detection of greenfield phase."""
        prompt = "Build a new application from scratch"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert context["phase"] == "greenfield"

    def test_detect_enhancement_phase(self, brian_orchestrator):
        """Test detection of enhancement phase."""
        prompt = "Add JWT authentication to the existing API"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert context["phase"] == "enhancement"

    def test_detect_bugfix_phase(self, brian_orchestrator):
        """Test detection of bugfix phase."""
        prompt = "Fix the authentication bug in the login flow"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert context["phase"] == "bugfix"

    def test_empty_prompt_handling(self, brian_orchestrator):
        """Test handling of empty prompts."""
        prompt = "Do something"
        context = brian_orchestrator._extract_context_from_prompt(prompt)

        assert context["tags"] == []
        assert context["requirements"] == []
        assert context["technologies"] == []
        assert context["phase"] == "unknown"


class TestLearningContextBuilding:
    """Test learning context building with various scenarios (AC3)."""

    def test_build_context_with_no_learning_service(self, brian_orchestrator):
        """Test graceful handling when no learning service configured."""
        # Remove learning service
        brian_orchestrator.learning_service = None

        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        assert context == ""

    def test_build_context_with_no_learnings_found(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test graceful handling when no learnings found."""
        mock_learning_service.get_relevant_learnings.return_value = []

        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        assert context == ""

    def test_build_context_with_one_learning(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test context building with one learning."""
        mock_learning_service.get_relevant_learnings.return_value = [
            create_mock_learning(1, category="quality")
        ]

        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API with authentication",
        )

        assert "Learning 1" in context
        assert "quality" in context.lower()

    def test_build_context_with_five_learnings(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test context building with maximum 5 learnings."""
        learnings = [
            create_mock_learning(i, category=f"category_{i}") for i in range(1, 6)
        ]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Verify all 5 learnings included
        for i in range(1, 6):
            assert f"Learning {i}" in context

    def test_build_context_error_fallback(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test graceful fallback on errors (AC7)."""
        mock_learning_service.get_relevant_learnings.side_effect = Exception(
            "Database error"
        )

        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Should return empty string on error (graceful degradation)
        assert context == ""


class TestLearningCaching:
    """Test learning context caching (AC6)."""

    def test_cache_miss_on_first_call(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test cache miss on first call."""
        learnings = [create_mock_learning(1)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # First call - cache miss
        context1 = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Verify learning service was called
        assert mock_learning_service.get_relevant_learnings.call_count == 1
        assert "Learning 1" in context1

    def test_cache_hit_on_second_call(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test cache hit on second call with same parameters."""
        learnings = [create_mock_learning(1)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # First call - cache miss
        context1 = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Second call - cache hit
        context2 = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Verify learning service only called once (cache hit)
        assert mock_learning_service.get_relevant_learnings.call_count == 1
        assert context1 == context2

    def test_cache_miss_on_different_scale_level(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test cache miss when scale level changes."""
        learnings = [create_mock_learning(1)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # First call - Level 3
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Second call - Level 2 (different cache key)
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_2,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Verify learning service called twice (cache miss)
        assert mock_learning_service.get_relevant_learnings.call_count == 2

    def test_cache_expiration_after_ttl(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test cache expiration after TTL (1 hour)."""
        learnings = [create_mock_learning(1)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # First call - cache miss
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Manually expire cache by setting old timestamp
        for key in brian_orchestrator._learning_cache:
            old_context, _ = brian_orchestrator._learning_cache[key]
            expired_time = datetime.now() - timedelta(hours=2)
            brian_orchestrator._learning_cache[key] = (old_context, expired_time)

        # Second call - cache expired, should fetch again
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Verify learning service called twice (cache expired)
        assert mock_learning_service.get_relevant_learnings.call_count == 2


class TestPerformance:
    """Test performance targets (AC1 - <500ms)."""

    def test_context_building_performance(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test context building meets <500ms target (C5 fix)."""
        learnings = [create_mock_learning(i) for i in range(1, 6)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        start = time.time()
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API with authentication",
        )
        duration_ms = (time.time() - start) * 1000

        # Performance target: <500ms (C5 fix - revised from <100ms)
        assert duration_ms < 500, f"Context building took {duration_ms:.2f}ms (target: <500ms)"

    def test_cached_context_performance(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test cached context retrieval is fast (<50ms)."""
        learnings = [create_mock_learning(i) for i in range(1, 6)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # First call to populate cache
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Second call should hit cache
        start = time.time()
        brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )
        duration_ms = (time.time() - start) * 1000

        # Cache hit should be very fast (<50ms)
        assert duration_ms < 50, (
            f"Cached context retrieval took {duration_ms:.2f}ms (target: <50ms)"
        )


class TestIntegration:
    """Test integration with workflow selection (AC5)."""

    @pytest.mark.asyncio
    async def test_select_workflows_with_learning_integration(
        self, brian_orchestrator, mock_learning_service, mock_analysis_service
    ):
        """Test full integration of learning context in workflow selection."""
        # Mock analysis response
        mock_analysis_service.analyze.return_value = MagicMock(
            response=json.dumps({
                "scale_level": 3,
                "project_type": "software",
                "is_greenfield": True,
                "is_brownfield": False,
                "is_game_project": False,
                "estimated_stories": 20,
                "estimated_epics": 3,
                "technical_complexity": "high",
                "domain_complexity": "medium",
                "timeline_hint": "weeks",
                "confidence": 0.85,
                "reasoning": "Medium-sized web application",
                "needs_clarification": False,
                "clarifying_questions": [],
            }),
            model_used="test-model",
            tokens_used=100,
            duration_ms=50,
        )

        # Mock learnings
        learnings = [create_mock_learning(i) for i in range(1, 3)]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # Call select_workflows_with_learning
        result = await brian_orchestrator.select_workflows_with_learning(
            user_prompt="Build a web API with authentication"
        )

        # Verify workflow sequence returned
        assert result is not None
        assert result.scale_level == ScaleLevel.LEVEL_3

        # Verify learning service was called
        assert mock_learning_service.get_relevant_learnings.called

    @pytest.mark.asyncio
    async def test_select_workflows_without_learning_service(
        self, brian_orchestrator, mock_analysis_service
    ):
        """Test workflow selection works without learning service (backward compatible)."""
        # Remove learning service
        brian_orchestrator.learning_service = None

        # Mock analysis response
        mock_analysis_service.analyze.return_value = MagicMock(
            response=json.dumps({
                "scale_level": 2,
                "project_type": "software",
                "is_greenfield": True,
                "is_brownfield": False,
                "is_game_project": False,
                "estimated_stories": 10,
                "estimated_epics": 2,
                "technical_complexity": "medium",
                "domain_complexity": "low",
                "timeline_hint": "days",
                "confidence": 0.9,
                "reasoning": "Small web application",
                "needs_clarification": False,
                "clarifying_questions": [],
            }),
            model_used="test-model",
            tokens_used=100,
            duration_ms=50,
        )

        # Call select_workflows_with_learning (should work without learning service)
        result = await brian_orchestrator.select_workflows_with_learning(
            user_prompt="Build a simple todo app"
        )

        # Verify workflow sequence returned
        assert result is not None
        assert result.scale_level == ScaleLevel.LEVEL_2


class TestTemplateRendering:
    """Test template rendering correctness (AC2)."""

    def test_fallback_template_formatting(self, brian_orchestrator):
        """Test fallback template formatting when template loading fails."""
        formatted_learnings = [
            {
                "rank": 1,
                "category": "Quality",
                "confidence": "0.85",
                "success_rate": "0.90",
                "success_rate_percent": "90",
                "content": "Always write tests first",
                "context": "TDD approach",
                "application_count": 5,
                "recommendation": "Apply TDD to new features",
            }
        ]

        result = brian_orchestrator._format_learnings_fallback(formatted_learnings)

        assert "## Relevant Past Learnings" in result
        assert "Learning 1" in result
        assert "Quality" in result
        assert "Always write tests first" in result
        assert "90%" in result

    def test_fallback_template_empty_list(self, brian_orchestrator):
        """Test fallback template with empty learnings list."""
        result = brian_orchestrator._format_learnings_fallback([])
        assert result == ""

    def test_fallback_template_multiple_learnings(self, brian_orchestrator):
        """Test fallback template with multiple learnings."""
        formatted_learnings = [
            {
                "rank": i,
                "category": f"Category{i}",
                "confidence": "0.80",
                "success_rate": "0.85",
                "success_rate_percent": "85",
                "content": f"Learning content {i}",
                "context": f"Context {i}",
                "application_count": i * 2,
                "recommendation": f"Recommendation {i}",
            }
            for i in range(1, 4)
        ]

        result = brian_orchestrator._format_learnings_fallback(formatted_learnings)

        for i in range(1, 4):
            assert f"Learning {i}" in result
            assert f"Category{i}" in result
            assert f"Learning content {i}" in result

    def test_template_loading_with_real_template(
        self, brian_orchestrator, mock_learning_service
    ):
        """Test template loading with actual YAML template file."""
        # Create real learnings to trigger template loading path
        learnings = [create_mock_learning(1, category="quality")]
        mock_learning_service.get_relevant_learnings.return_value = learnings

        # This will attempt to load the real template
        context = brian_orchestrator._build_context_with_learnings(
            scale_level=ScaleLevel.LEVEL_3,
            project_type="web_app",
            user_prompt="Build an API",
        )

        # Should contain learning content (either from template or fallback)
        assert "Learning 1" in context or "Quality" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
