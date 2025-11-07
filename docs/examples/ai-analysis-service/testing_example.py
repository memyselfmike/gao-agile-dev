"""
Testing example for components using AIAnalysisService.

This example demonstrates:
- Mocking AIAnalysisService for unit tests
- Testing components that use the service
- Best practices for testable code

Epic: 21 - AI Analysis Service & Brian Provider Abstraction
"""
import pytest
from unittest.mock import Mock, AsyncMock
from gao_dev.core.services import AIAnalysisService, AnalysisResult
from gao_dev.core.providers.exceptions import (
    AnalysisError,
    AnalysisTimeoutError,
    InvalidModelError
)
import json


# ============================================================================
# EXAMPLE COMPONENT TO TEST
# ============================================================================


class ComplexityAnalyzer:
    """
    Example component that uses AIAnalysisService.

    This is what you'd write in your application.
    Notice: Service is injected via constructor (dependency injection).
    """

    def __init__(self, analysis_service: AIAnalysisService):
        """Initialize with analysis service."""
        self.analysis_service = analysis_service

    async def analyze_code_complexity(self, code: str) -> dict:
        """
        Analyze code complexity using AI.

        Args:
            code: Python code to analyze

        Returns:
            dict with complexity score and rationale

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            result = await self.analysis_service.analyze(
                prompt=f"""
                Rate this code's complexity from 1-10:

                ```python
                {code}
                ```

                Return JSON: {{"complexity": 1-10, "rationale": "explanation"}}
                """,
                response_format="json",
                max_tokens=500
            )

            data = json.loads(result.response)
            return {
                "complexity": data["complexity"],
                "rationale": data["rationale"],
                "tokens_used": result.tokens_used
            }

        except json.JSONDecodeError as e:
            raise AnalysisError(f"Invalid JSON response: {e}")


# ============================================================================
# UNIT TESTS
# ============================================================================


@pytest.fixture
def mock_analysis_service():
    """
    Mock AIAnalysisService for testing.

    This is the key to testing components that use AIAnalysisService
    without making real API calls.
    """
    service = Mock(spec=AIAnalysisService)

    # Mock the analyze method to return a predefined result
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='{"complexity": 5, "rationale": "Moderate complexity due to recursion"}',
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=120,
        duration_ms=450.0
    ))

    return service


@pytest.mark.asyncio
async def test_complexity_analyzer_success(mock_analysis_service):
    """Test ComplexityAnalyzer with successful analysis."""
    # Arrange
    analyzer = ComplexityAnalyzer(analysis_service=mock_analysis_service)
    code = "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"

    # Act
    result = await analyzer.analyze_code_complexity(code)

    # Assert
    assert result["complexity"] == 5
    assert "recursion" in result["rationale"].lower()
    assert result["tokens_used"] == 120

    # Verify service was called correctly
    mock_analysis_service.analyze.assert_called_once()
    call_args = mock_analysis_service.analyze.call_args
    assert "factorial" in call_args.kwargs["prompt"]
    assert call_args.kwargs["response_format"] == "json"


@pytest.mark.asyncio
async def test_complexity_analyzer_invalid_json():
    """Test handling of invalid JSON response."""
    # Arrange
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(return_value=AnalysisResult(
        response='Not valid JSON',  # Invalid JSON
        model_used="claude-sonnet-4-5-20250929",
        tokens_used=50,
        duration_ms=200.0
    ))

    analyzer = ComplexityAnalyzer(analysis_service=service)

    # Act & Assert
    with pytest.raises(AnalysisError, match="Invalid JSON response"):
        await analyzer.analyze_code_complexity("def add(a, b): return a + b")


@pytest.mark.asyncio
async def test_complexity_analyzer_timeout():
    """Test handling of timeout errors."""
    # Arrange
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(side_effect=AnalysisTimeoutError("Request timed out"))

    analyzer = ComplexityAnalyzer(analysis_service=service)

    # Act & Assert
    with pytest.raises(AnalysisTimeoutError):
        await analyzer.analyze_code_complexity("def test(): pass")


@pytest.mark.asyncio
async def test_complexity_analyzer_multiple_calls():
    """Test multiple analysis calls."""
    # Arrange
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(side_effect=[
        # First call returns complexity 3
        AnalysisResult(
            response='{"complexity": 3, "rationale": "Simple function"}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=80,
            duration_ms=300.0
        ),
        # Second call returns complexity 8
        AnalysisResult(
            response='{"complexity": 8, "rationale": "Complex algorithm"}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=150,
            duration_ms=500.0
        ),
    ])

    analyzer = ComplexityAnalyzer(analysis_service=service)

    # Act
    result1 = await analyzer.analyze_code_complexity("def simple(): pass")
    result2 = await analyzer.analyze_code_complexity("def complex(): ...")

    # Assert
    assert result1["complexity"] == 3
    assert result2["complexity"] == 8
    assert service.analyze.call_count == 2


# ============================================================================
# INTEGRATION TESTS (require real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_analysis_service():
    """
    Integration test with real AIAnalysisService.

    Requires ANTHROPIC_API_KEY environment variable.
    Mark as @pytest.mark.integration to skip in CI.
    """
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    # Create real service
    service = AIAnalysisService()
    analyzer = ComplexityAnalyzer(analysis_service=service)

    # Simple code example
    code = "def add(a, b): return a + b"

    # Analyze
    result = await analyzer.analyze_code_complexity(code)

    # Verify
    assert isinstance(result["complexity"], int)
    assert 1 <= result["complexity"] <= 10
    assert isinstance(result["rationale"], str)
    assert len(result["rationale"]) > 0
    assert result["tokens_used"] > 0


# ============================================================================
# ADVANCED TESTING PATTERNS
# ============================================================================


class SmartAnalyzer:
    """
    More complex component with retry logic and fallback.

    This demonstrates testing more sophisticated error handling.
    """

    def __init__(self, analysis_service: AIAnalysisService):
        self.analysis_service = analysis_service

    async def analyze_with_retry(self, prompt: str, max_retries: int = 3):
        """Analyze with retry logic on timeout."""
        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.analysis_service.analyze(
                    prompt=prompt,
                    response_format="json"
                )
                return json.loads(result.response)

            except AnalysisTimeoutError as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue  # Retry
                else:
                    raise  # Max retries exceeded

        raise last_error


@pytest.mark.asyncio
async def test_smart_analyzer_retry_logic():
    """Test retry logic with multiple failures then success."""
    # Arrange
    service = Mock(spec=AIAnalysisService)

    # First 2 calls fail with timeout, 3rd succeeds
    service.analyze = AsyncMock(side_effect=[
        AnalysisTimeoutError("Timeout 1"),
        AnalysisTimeoutError("Timeout 2"),
        AnalysisResult(
            response='{"result": "success"}',
            model_used="claude-sonnet-4-5-20250929",
            tokens_used=100,
            duration_ms=400.0
        ),
    ])

    analyzer = SmartAnalyzer(analysis_service=service)

    # Act
    result = await analyzer.analyze_with_retry("test prompt", max_retries=3)

    # Assert
    assert result["result"] == "success"
    assert service.analyze.call_count == 3


@pytest.mark.asyncio
async def test_smart_analyzer_max_retries_exceeded():
    """Test that max retries is respected."""
    # Arrange
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock(side_effect=AnalysisTimeoutError("Always timeout"))

    analyzer = SmartAnalyzer(analysis_service=service)

    # Act & Assert
    with pytest.raises(AnalysisTimeoutError):
        await analyzer.analyze_with_retry("test prompt", max_retries=3)

    # Verify it tried exactly 3 times
    assert service.analyze.call_count == 3


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""


@pytest.fixture
def complex_code():
    """Complex code for testing."""
    return """
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = {}

    async def process(self, data):
        if data in self.cache:
            return self.cache[data]

        result = await self._complex_processing(data)
        self.cache[data] = result
        return result

    async def _complex_processing(self, data):
        # Complex processing logic
        pass
"""


# ============================================================================
# EXAMPLE: Running Tests
# ============================================================================


def example_run_tests():
    """
    Example of how to run these tests.

    Run in terminal:
    ```bash
    # Run all tests
    pytest docs/examples/ai-analysis-service/testing_example.py

    # Run only unit tests (skip integration)
    pytest docs/examples/ai-analysis-service/testing_example.py -m "not integration"

    # Run with verbose output
    pytest docs/examples/ai-analysis-service/testing_example.py -v

    # Run with coverage
    pytest docs/examples/ai-analysis-service/testing_example.py --cov

    # Run specific test
    pytest docs/examples/ai-analysis-service/testing_example.py::test_complexity_analyzer_success
    ```
    """
    pass


# ============================================================================
# MAIN (for running examples)
# ============================================================================


if __name__ == "__main__":
    print("=" * 70)
    print("AIAnalysisService - Testing Examples")
    print("=" * 70)
    print("\nThis file contains pytest test examples.")
    print("\nTo run tests:")
    print("  pytest", __file__)
    print("\nTo run without integration tests:")
    print("  pytest", __file__, '-m "not integration"')
    print("\nTo run with verbose output:")
    print("  pytest", __file__, "-v")
    print("\n" + "=" * 70)
    print("\nKey Testing Patterns Demonstrated:")
    print("  1. Mocking AIAnalysisService with Mock + AsyncMock")
    print("  2. Testing successful analysis")
    print("  3. Testing error handling (timeout, invalid JSON)")
    print("  4. Testing retry logic")
    print("  5. Integration testing with real API")
    print("  6. Using fixtures for test data")
    print("=" * 70)
