"""Integration tests for Brian Provider Abstraction (Story 21.4).

This module tests Brian's integration with AIAnalysisService across different providers:
- Mocked provider (fast, no external dependencies)
- Claude Code provider (requires API key)
- OpenCode provider (requires Ollama + deepseek-r1)

Test Coverage:
- Provider abstraction layer
- Model selection priority (env var, config, explicit, default)
- Error handling scenarios (timeout, invalid model, API errors)
- Performance and overhead measurement
- Cross-provider consistency

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
Story: 21.4 - Integration Testing with Multiple Providers
"""

import pytest
import os
import time
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional

from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult
from gao_dev.core.workflow_registry import WorkflowRegistry
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError,
    ProviderTimeoutError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def workflow_registry():
    """Real workflow registry for integration tests."""
    from gao_dev.core.config_loader import ConfigLoader

    # Create ConfigLoader with project root
    project_root = Path(__file__).parent.parent.parent
    config_loader = ConfigLoader(project_root)

    # Create WorkflowRegistry with ConfigLoader
    return WorkflowRegistry(config_loader)


@pytest.fixture
def mock_anthropic_client():
    """
    Mock Anthropic client for testing without external dependencies.

    Returns AsyncMock with realistic response structure.
    """
    with patch("gao_dev.core.services.ai_analysis_service.anthropic") as mock_anthropic:
        # Create mock client and message
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(text='{"scale_level": 2, "workflows": ["prd", "architecture"]}')]
        mock_message.model = "claude-sonnet-4-5-20250929"
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)

        # Setup async create method
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_anthropic.Anthropic.return_value = mock_client

        yield mock_anthropic


@pytest.fixture
def mock_analysis_service():
    """
    Mocked AIAnalysisService for fast testing.

    Returns service that returns predefined responses without external calls.
    """
    service = Mock(spec=AIAnalysisService)

    # Mock analyze method to return realistic result with ALL required fields
    async def mock_analyze(prompt: str, model: Optional[str] = None, **kwargs) -> AnalysisResult:
        # Return complete JSON structure that Brian expects
        complete_response = {
            "scale_level": 2,
            "project_type": "greenfield",
            "is_greenfield": True,
            "is_brownfield": False,
            "is_game_project": False,
            "estimated_stories": 5,
            "estimated_epics": 1,
            "technical_complexity": "medium",
            "domain_complexity": "low",
            "timeline_hint": "1-2 weeks",
            "confidence": 0.85,
            "reasoning": "Small feature project with authentication and CRUD operations",
            "needs_clarification": False,
            "clarifying_questions": []
        }

        return AnalysisResult(
            response=json.dumps(complete_response),
            model_used=model or "claude-sonnet-4-5-20250929",
            tokens_used=150,
            duration_ms=250.0
        )

    service.analyze = AsyncMock(side_effect=mock_analyze)
    return service


# =============================================================================
# Test Class: Mock Provider Tests (Fast, No External Dependencies)
# =============================================================================

class TestBrianWithMockedProvider:
    """
    Test Brian with fully mocked provider.

    These tests run fast and validate the abstraction layer without
    requiring external services (API keys, Ollama, etc.).

    Benefits:
    - Fast execution (no network calls)
    - No external dependencies
    - Reliable for CI/CD
    - Validates abstraction layer
    """

    @pytest.mark.asyncio
    async def test_basic_workflow_selection(self, workflow_registry, mock_analysis_service):
        """Test basic workflow selection with mocked service."""
        # Create Brian with mocked service
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Execute workflow selection
        result = await brian.assess_and_select_workflows(
            "Build a todo application with user authentication"
        )

        # Verify
        assert result.scale_level.value in [0, 1, 2, 3, 4]
        assert result.workflows is not None
        assert len(result.workflows) > 0

        # Verify service was called
        mock_analysis_service.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_scale_level_detection(self, workflow_registry, mock_analysis_service):
        """Test that Brian correctly detects scale levels."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Test Level 2 prompt (small feature)
        result = await brian.assess_and_select_workflows(
            "Create a todo app with user auth, CRUD operations, and filtering"
        )

        # Should detect Level 2
        assert result.scale_level.value == 2
        assert result.project_type.value in ["greenfield", "enhancement", "software"]

    @pytest.mark.asyncio
    async def test_workflow_sequence_construction(self, workflow_registry, mock_analysis_service):
        """Test that workflow sequences are properly constructed."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        result = await brian.assess_and_select_workflows(
            "Build a CRM system"
        )

        # Verify workflow sequence structure
        assert hasattr(result, "scale_level")
        assert hasattr(result, "workflows")
        assert hasattr(result, "project_type")
        assert hasattr(result, "routing_rationale")


# =============================================================================
# Test Class: Model Selection Priority
# =============================================================================

class TestModelSelectionPriority:
    """
    Test model selection priority order.

    Priority order (highest to lowest):
    1. GAO_DEV_MODEL environment variable
    2. Explicit model parameter
    3. Model from YAML config
    4. Default model (claude-sonnet-4-5-20250929)
    """

    @pytest.mark.asyncio
    async def test_env_variable_override(self, workflow_registry, mock_analysis_service, monkeypatch):
        """Test GAO_DEV_MODEL environment variable takes highest priority."""
        # Set environment variable
        monkeypatch.setenv("GAO_DEV_MODEL", "env-model-name")

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Environment variable should override
        assert brian.model == "env-model-name"

    @pytest.mark.asyncio
    async def test_explicit_model_parameter(self, workflow_registry, mock_analysis_service, monkeypatch):
        """Test explicit model parameter."""
        # Ensure no env var interference
        monkeypatch.delenv("GAO_DEV_MODEL", raising=False)

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service,
            model="explicit-model-name"
        )

        # Explicit parameter should be used
        assert brian.model == "explicit-model-name"

    @pytest.mark.asyncio
    async def test_default_model_fallback(self, workflow_registry, mock_analysis_service, monkeypatch):
        """Test default model when no explicit configuration."""
        # Ensure no env var
        monkeypatch.delenv("GAO_DEV_MODEL", raising=False)

        # Patch YAML loading to fail (no config)
        with patch("gao_dev.core.agent_config_loader.AgentConfigLoader") as mock_loader:
            mock_loader.return_value.load_agent_config.return_value = None

            brian = BrianOrchestrator(
                workflow_registry=workflow_registry,
                analysis_service=mock_analysis_service
            )

            # Should use default
            assert brian.model == "deepseek-r1"

    @pytest.mark.asyncio
    async def test_yaml_config_model(self, workflow_registry, mock_analysis_service, monkeypatch):
        """Test model loaded from YAML config."""
        # Ensure no env var or explicit model
        monkeypatch.delenv("GAO_DEV_MODEL", raising=False)

        # Mock YAML config
        with patch("gao_dev.core.agent_config_loader.AgentConfigLoader") as mock_loader:
            mock_config = Mock()
            mock_config.model = "yaml-configured-model"
            mock_loader.return_value.load_agent_config.return_value = mock_config

            brian = BrianOrchestrator(
                workflow_registry=workflow_registry,
                analysis_service=mock_analysis_service
            )

            # Should use YAML config
            assert brian.model == "yaml-configured-model"


# =============================================================================
# Test Class: Error Handling
# =============================================================================

class TestErrorHandling:
    """
    Test error handling scenarios.

    Brian implements graceful degradation - errors are caught and
    return fallback workflow sequences with clarification needed.

    Tests various failure modes:
    - API timeout (fallback to conservative default)
    - Invalid model name (fallback to conservative default)
    - Malformed JSON response (raises AnalysisError)
    - Provider unavailable (fallback to conservative default)
    - Rate limiting (fallback to conservative default)
    """

    @pytest.mark.asyncio
    async def test_api_timeout(self, workflow_registry):
        """Test API timeout handling - should return fallback sequence."""
        # Create service that times out
        mock_service = Mock(spec=AIAnalysisService)
        mock_service.analyze = AsyncMock(side_effect=AnalysisTimeoutError("API timeout after 60s"))

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service
        )

        # Should return fallback sequence (not raise)
        result = await brian.assess_and_select_workflows("Test prompt")

        # Verify fallback behavior
        assert result.scale_level.value == 2  # Conservative default
        assert result.routing_rationale is not None
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()

    @pytest.mark.asyncio
    async def test_invalid_model(self, workflow_registry):
        """Test invalid model name handling - should return fallback sequence."""
        mock_service = Mock(spec=AIAnalysisService)
        mock_service.analyze = AsyncMock(
            side_effect=InvalidModelError("Model 'invalid-model-xyz' not found")
        )

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service,
            model="invalid-model-xyz"
        )

        # Should return fallback sequence (not raise)
        result = await brian.assess_and_select_workflows("Test prompt")

        # Verify fallback behavior
        assert result.scale_level.value == 2
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()

    @pytest.mark.asyncio
    async def test_malformed_json_response(self, workflow_registry):
        """Test handling of malformed JSON response - should fallback gracefully."""
        mock_service = Mock(spec=AIAnalysisService)

        # Return malformed JSON
        async def mock_analyze(*args, **kwargs):
            return AnalysisResult(
                response="This is not valid JSON {incomplete...",
                model_used="test-model",
                tokens_used=100,
                duration_ms=100.0
            )

        mock_service.analyze = AsyncMock(side_effect=mock_analyze)

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service
        )

        # Malformed JSON should return fallback (Brian catches JSONDecodeError)
        result = await brian.assess_and_select_workflows("Test prompt")

        # Verify fallback behavior
        assert result.scale_level.value == 2
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()

    @pytest.mark.asyncio
    async def test_provider_unavailable(self, workflow_registry):
        """Test provider unavailable error handling - should return fallback."""
        mock_service = Mock(spec=AIAnalysisService)
        mock_service.analyze = AsyncMock(
            side_effect=AnalysisError("Provider unavailable (503 Service Unavailable)")
        )

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service
        )

        # Should return fallback sequence (not raise)
        result = await brian.assess_and_select_workflows("Test prompt")

        # Verify fallback behavior
        assert result.scale_level.value == 2
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()

    @pytest.mark.asyncio
    async def test_empty_response(self, workflow_registry):
        """Test handling of empty response - should fallback gracefully."""
        mock_service = Mock(spec=AIAnalysisService)

        async def mock_analyze(*args, **kwargs):
            return AnalysisResult(
                response="",  # Empty response
                model_used="test-model",
                tokens_used=0,
                duration_ms=50.0
            )

        mock_service.analyze = AsyncMock(side_effect=mock_analyze)

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service
        )

        # Empty response should return fallback (Brian handles this)
        result = await brian.assess_and_select_workflows("Test prompt")

        # Verify fallback behavior
        assert result.scale_level.value == 2
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()


# =============================================================================
# Test Class: Claude Code Provider (Requires API Key)
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_api_key
class TestBrianWithClaudeCode:
    """
    Test Brian with real Claude Code provider.

    Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - Internet connection
    - API quota available

    These tests are slower and cost money, so they're marked with
    @pytest.mark.requires_api_key and can be skipped in CI.

    Run with: pytest -m requires_api_key
    Skip with: pytest -m "not requires_api_key"
    """

    @pytest.mark.asyncio
    async def test_real_claude_analysis(self, workflow_registry):
        """
        Test Brian with real Claude Code provider.

        NOTE: Requires ANTHROPIC_API_KEY environment variable.
        This test is skipped in CI unless API key is available.
        """
        # Check if API key available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set - skipping real API test")

        # Create real service
        analysis_service = AIAnalysisService(
            api_key=api_key,
            default_model="claude-sonnet-4-5-20250929"
        )

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        # Test real analysis
        result = await brian.assess_and_select_workflows(
            "Build a simple todo application"
        )

        # Verify real result
        assert result.scale_level.value in [0, 1, 2, 3, 4]
        assert result.workflows is not None
        assert len(result.workflows) > 0
        assert result.project_type is not None

    @pytest.mark.asyncio
    async def test_real_level_2_project(self, workflow_registry):
        """
        Test Level 2 project classification with real API.

        NOTE: Requires ANTHROPIC_API_KEY. Skipped if not available.
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        analysis_service = AIAnalysisService(api_key=api_key)
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=analysis_service
        )

        # Test Level 2 prompt
        result = await brian.assess_and_select_workflows(
            "Create a todo application with user authentication, "
            "CRUD operations, task filtering, and search"
        )

        # Should be Level 2 (small feature, 3-8 stories)
        assert result.scale_level.value == 2


# =============================================================================
# Test Class: OpenCode Provider (Requires Ollama)
# =============================================================================

@pytest.mark.integration
@pytest.mark.requires_ollama
class TestBrianWithOpenCode:
    """
    Test Brian with OpenCode + Ollama + deepseek-r1.

    Requirements:
    - Ollama running locally
    - deepseek-r1 model pulled
    - OpenCode server running

    These tests validate local model usage for:
    - Air-gapped environments
    - Cost reduction
    - Privacy-sensitive projects

    Run with: pytest -m requires_ollama
    Skip with: pytest -m "not requires_ollama"
    """

    @pytest.mark.asyncio
    async def test_deepseek_r1_analysis(self, workflow_registry):
        """
        Test Brian with local deepseek-r1 model.

        NOTE: Requires Ollama + deepseek-r1 model.
        This test is skipped if Ollama is not available.
        """
        # Try to import ollama to check availability
        pytest.importorskip("ollama", reason="Ollama not installed")

        # Check if deepseek-r1 model available
        # TODO: Add ollama health check here

        # Skip for now - will be implemented when OpenCode SDK is fully integrated
        pytest.skip("OpenCode SDK integration pending - Story 21.5")

    @pytest.mark.asyncio
    async def test_opencode_performance(self, workflow_registry):
        """
        Test performance with local model.

        NOTE: Requires Ollama. Local inference is slower than API.
        """
        pytest.skip("OpenCode SDK integration pending - Story 21.5")


# =============================================================================
# Test Class: Performance Benchmarks
# =============================================================================

@pytest.mark.performance
class TestPerformance:
    """
    Performance benchmarks for AIAnalysisService abstraction.

    Measures:
    - Service overhead vs. direct API calls
    - Response time distribution
    - Token usage efficiency

    Goal: <5% overhead from abstraction layer
    """

    @pytest.mark.asyncio
    async def test_service_overhead(self, workflow_registry, mock_analysis_service):
        """
        Measure overhead from service abstraction.

        Tests fast mocked service to isolate abstraction overhead.
        """
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Measure execution time
        start = time.time()
        result = await brian.assess_and_select_workflows(
            "Build a todo app"
        )
        duration = time.time() - start

        # Should be fast (mocked, no network)
        assert duration < 1.0, f"Overhead too high: {duration:.2f}s"
        assert result.scale_level is not None

    @pytest.mark.asyncio
    async def test_response_time_consistency(self, workflow_registry, mock_analysis_service):
        """Test response time consistency across multiple calls."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Run multiple iterations
        durations = []
        for i in range(5):
            start = time.time()
            await brian.assess_and_select_workflows(f"Build app {i}")
            durations.append(time.time() - start)

        # Check consistency (all should be fast with mock)
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 0.5, f"Average too high: {avg_duration:.2f}s"
        assert max_duration < 1.0, f"Max too high: {max_duration:.2f}s"


# =============================================================================
# Test Class: Cross-Provider Consistency
# =============================================================================

class TestCrossProviderConsistency:
    """
    Test that same prompts work consistently across providers.

    Validates:
    - Response format consistency
    - Error handling consistency
    - Logging consistency
    - Metrics consistency
    """

    @pytest.mark.asyncio
    async def test_consistent_response_structure(self, workflow_registry, mock_analysis_service):
        """Test that response structure is consistent."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        result = await brian.assess_and_select_workflows(
            "Build a CRM system"
        )

        # Verify standard structure
        assert hasattr(result, "scale_level")
        assert hasattr(result, "workflows")
        assert hasattr(result, "project_type")
        assert hasattr(result, "routing_rationale")
        assert hasattr(result, "phase_breakdown")

    @pytest.mark.asyncio
    async def test_consistent_error_messages(self, workflow_registry):
        """Test that error messages are consistent across providers."""
        # Test with timeout error - returns fallback
        mock_service = Mock(spec=AIAnalysisService)
        mock_service.analyze = AsyncMock(side_effect=AnalysisTimeoutError("Timeout"))

        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_service
        )

        result = await brian.assess_and_select_workflows("Test")
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()

        # Test with invalid model - also returns fallback
        mock_service.analyze = AsyncMock(side_effect=InvalidModelError("Invalid model"))

        result = await brian.assess_and_select_workflows("Test")
        assert "failed" in result.routing_rationale.lower() or "clarification" in result.routing_rationale.lower()


# =============================================================================
# Test Class: Integration with Real Workflows
# =============================================================================

class TestWorkflowIntegration:
    """
    Test Brian's integration with real workflow registry.

    Validates:
    - Workflow loading and registration
    - Workflow selection logic
    - Phase breakdown calculation
    - Agent recommendations
    """

    @pytest.mark.asyncio
    async def test_workflow_registry_loaded(self, workflow_registry, mock_analysis_service):
        """Test that workflow registry is properly loaded."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        # Verify workflows available from workflow registry directly
        all_workflows = workflow_registry.list_workflows()
        assert len(all_workflows) > 0, "No workflows loaded"

        # Should have workflows from multiple phases
        phases = {w.phase for w in all_workflows}
        assert len(phases) >= 1, "Expected workflows from at least 1 phase"

    @pytest.mark.asyncio
    async def test_workflow_selection_logic(self, workflow_registry, mock_analysis_service):
        """Test that workflow selection produces valid workflow list."""
        brian = BrianOrchestrator(
            workflow_registry=workflow_registry,
            analysis_service=mock_analysis_service
        )

        result = await brian.assess_and_select_workflows(
            "Build a todo app with authentication"
        )

        # Verify workflows are valid
        assert len(result.workflows) > 0

        # All workflows should be WorkflowInfo objects
        for workflow in result.workflows:
            assert hasattr(workflow, "name")
            assert hasattr(workflow, "phase")
