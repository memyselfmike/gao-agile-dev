"""Integration test configuration and fixtures.

This module provides fixtures for integration testing, including:
- Real workflow registry
- Provider setup (Claude Code, OpenCode, Mock)
- Environment configuration helpers
- Cleanup utilities

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
Story: 21.4 - Integration Testing
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock


# =============================================================================
# Workflow Registry Fixtures
# =============================================================================

@pytest.fixture
def real_workflow_registry():
    """
    Real workflow registry for integration tests.

    Loads workflows from the actual gao_dev/workflows directory.
    """
    from gao_dev.core.workflow_registry import WorkflowRegistry
    from gao_dev.core.config_loader import ConfigLoader

    # Create ConfigLoader with project root
    project_root = Path(__file__).parent.parent.parent
    config_loader = ConfigLoader(project_root)

    # Create WorkflowRegistry with ConfigLoader
    return WorkflowRegistry(config_loader)


# =============================================================================
# Provider Fixtures
# =============================================================================

@pytest.fixture
def mock_anthropic_provider():
    """
    Mock Anthropic provider for fast testing.

    Returns:
        Mock: Mocked provider with predefined responses
    """
    from unittest.mock import patch

    with patch("gao_dev.core.services.ai_analysis_service.anthropic") as mock_anthropic:
        # Create mock client
        mock_client = Mock()
        mock_message = Mock()
        mock_message.content = [Mock(
            text='{"scale_level": 2, "project_type": "greenfield", "workflows": ["prd", "architecture"]}'
        )]
        mock_message.model = "claude-sonnet-4-5-20250929"
        mock_message.usage = Mock(input_tokens=100, output_tokens=50)

        # Setup async methods
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        mock_anthropic.Anthropic.return_value = mock_client

        yield mock_anthropic


@pytest.fixture
def claude_code_analysis_service():
    """
    Real Claude Code AIAnalysisService.

    NOTE: Requires ANTHROPIC_API_KEY environment variable.
    Tests using this fixture will be skipped if API key not available.

    Returns:
        AIAnalysisService: Configured for Claude Code
    """
    from gao_dev.core.services.ai_analysis_service import AIAnalysisService

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping Claude Code test")

    return AIAnalysisService(
        api_key=api_key,
        default_model="claude-sonnet-4-5-20250929"
    )


@pytest.fixture
def opencode_analysis_service():
    """
    OpenCode AIAnalysisService with deepseek-r1.

    NOTE: Requires Ollama running with deepseek-r1 model.
    Tests using this fixture will be skipped if Ollama not available.

    Returns:
        AIAnalysisService: Configured for OpenCode + Ollama
    """
    # Check Ollama availability
    pytest.importorskip("ollama", reason="Ollama not installed")

    # TODO: Implement OpenCode SDK integration
    pytest.skip("OpenCode SDK integration pending - Story 21.5")


@pytest.fixture
def mock_analysis_service():
    """
    Fully mocked AIAnalysisService for fast testing.

    Returns predefined responses without external calls.

    Returns:
        Mock: Mocked AIAnalysisService
    """
    import json
    from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult

    service = Mock(spec=AIAnalysisService)

    # Mock analyze method with complete response structure
    async def mock_analyze(prompt: str, model=None, **kwargs) -> AnalysisResult:
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
# Environment Configuration Fixtures
# =============================================================================

@pytest.fixture
def clean_environment(monkeypatch):
    """
    Clean environment for model selection tests.

    Removes all GAO-Dev related environment variables to ensure
    clean state for testing priority order.

    Usage:
        def test_model_selection(clean_environment, monkeypatch):
            monkeypatch.setenv("GAO_DEV_MODEL", "test-model")
            # Test with clean environment
    """
    # Remove GAO-Dev environment variables
    monkeypatch.delenv("GAO_DEV_MODEL", raising=False)
    monkeypatch.delenv("AGENT_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    yield monkeypatch


@pytest.fixture
def test_environment_with_api_key(monkeypatch):
    """
    Test environment with ANTHROPIC_API_KEY set.

    Sets up environment for tests that require API access.
    Uses real API key from environment if available, otherwise skips.

    Usage:
        def test_real_api(test_environment_with_api_key):
            # Test will have API key available
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Preserve API key in test environment
    monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)

    yield monkeypatch


# =============================================================================
# Brian Orchestrator Fixtures
# =============================================================================

@pytest.fixture
def brian_with_mock_service(real_workflow_registry, mock_analysis_service):
    """
    Brian orchestrator with mocked analysis service.

    Fast fixture for testing Brian's logic without external dependencies.

    Returns:
        BrianOrchestrator: Configured with mocked service
    """
    from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator

    return BrianOrchestrator(
        workflow_registry=real_workflow_registry,
        analysis_service=mock_analysis_service
    )


@pytest.fixture
def brian_with_claude_code(real_workflow_registry, claude_code_analysis_service):
    """
    Brian orchestrator with real Claude Code service.

    NOTE: Requires ANTHROPIC_API_KEY. Will skip if not available.

    Returns:
        BrianOrchestrator: Configured with Claude Code
    """
    from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator

    return BrianOrchestrator(
        workflow_registry=real_workflow_registry,
        analysis_service=claude_code_analysis_service
    )


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def sample_prompts():
    """
    Collection of sample prompts for testing.

    Returns:
        dict: Prompts categorized by scale level
    """
    return {
        "level_0": "Fix typo in README.md",
        "level_1": "Fix authentication bug in login endpoint",
        "level_2": "Add todo app with auth, CRUD, and filtering",
        "level_3": "Build complete CRM system with reporting",
        "level_4": "Create new e-commerce platform from scratch"
    }


@pytest.fixture
def cleanup_test_artifacts():
    """
    Cleanup test artifacts after test run.

    Yields control to test, then cleans up any created files.
    """
    artifacts = []

    def register_artifact(path: Path):
        """Register artifact for cleanup."""
        artifacts.append(path)

    yield register_artifact

    # Cleanup after test
    for artifact in artifacts:
        if artifact.exists():
            if artifact.is_dir():
                import shutil
                shutil.rmtree(artifact, ignore_errors=True)
            else:
                artifact.unlink(missing_ok=True)


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """
    Configure custom pytest markers.

    Markers:
    - integration: Integration tests (may be slow)
    - requires_api_key: Requires ANTHROPIC_API_KEY
    - requires_ollama: Requires Ollama + deepseek-r1
    - performance: Performance benchmarks
    """
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (may be slow)"
    )
    config.addinivalue_line(
        "markers",
        "requires_api_key: mark test as requiring ANTHROPIC_API_KEY"
    )
    config.addinivalue_line(
        "markers",
        "requires_ollama: mark test as requiring Ollama + deepseek-r1"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as performance benchmark"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle markers.

    Automatically skips tests based on environment:
    - Skip requires_api_key tests if ANTHROPIC_API_KEY not set
    - Skip requires_ollama tests if Ollama not available
    """
    # Check environment
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_ollama = False  # TODO: Add Ollama health check

    for item in items:
        # Skip API key tests if key not available
        if "requires_api_key" in item.keywords and not has_api_key:
            item.add_marker(
                pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
            )

        # Skip Ollama tests if not available
        if "requires_ollama" in item.keywords and not has_ollama:
            item.add_marker(
                pytest.mark.skip(reason="Ollama not available")
            )
