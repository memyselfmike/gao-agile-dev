"""Tests for domain question library.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.4 - Domain-Specific Question Libraries
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import json
import time

from gao_dev.orchestrator.domain_question_library import (
    DomainQuestionLibrary,
    DomainType,
)
from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult


@pytest.fixture
def mock_analysis_service():
    """Create mock analysis service."""
    service = MagicMock(spec=AIAnalysisService)
    return service


@pytest.fixture
def domain_library(mock_analysis_service):
    """Create domain question library with mock service."""
    return DomainQuestionLibrary(analysis_service=mock_analysis_service)


class TestDomainDetection:
    """Test domain detection (keyword matching + LLM classification)."""

    @pytest.mark.asyncio
    async def test_keyword_matching_web_app(self, domain_library):
        """Test keyword matching detects web app domain."""
        user_request = "I want to build a responsive web app with React frontend"

        domain, confidence = await domain_library.detect_domain(user_request)

        assert domain == DomainType.WEB_APP
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_keyword_matching_mobile_app(self, domain_library):
        """Test keyword matching detects mobile app domain."""
        user_request = "Need to create an iOS and Android mobile app with Flutter"

        domain, confidence = await domain_library.detect_domain(user_request)

        assert domain == DomainType.MOBILE_APP
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_keyword_matching_api_service(self, domain_library):
        """Test keyword matching detects API service domain."""
        user_request = "I need a REST API service with GraphQL endpoints"

        domain, confidence = await domain_library.detect_domain(user_request)

        assert domain == DomainType.API_SERVICE
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_keyword_matching_cli_tool(self, domain_library):
        """Test keyword matching detects CLI tool domain."""
        user_request = "Build a command line tool for managing projects via terminal"

        domain, confidence = await domain_library.detect_domain(user_request)

        assert domain == DomainType.CLI_TOOL
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_keyword_matching_data_pipeline(self, domain_library):
        """Test keyword matching detects data pipeline domain."""
        user_request = "Need ETL pipeline to process data from Kafka to data warehouse"

        domain, confidence = await domain_library.detect_domain(user_request)

        assert domain == DomainType.DATA_PIPELINE
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_llm_classification_fallback(self, domain_library, mock_analysis_service):
        """Test LLM classification when keywords are uncertain."""
        # Request without clear keywords
        user_request = "I need something to manage tasks"

        # Mock LLM response
        mock_result = AnalysisResult(
            response=json.dumps({
                "domain": "web_app",
                "confidence": 0.75,
                "reasoning": "Task management typically implies web application",
            }),
            model_used="haiku",
            tokens_used=100,
            duration_ms=150,
        )
        mock_analysis_service.analyze = AsyncMock(return_value=mock_result)

        domain, confidence = await domain_library.detect_domain(user_request)

        # Should use LLM classification
        assert mock_analysis_service.analyze.called
        assert domain == DomainType.WEB_APP
        assert confidence == 0.75

    @pytest.mark.asyncio
    async def test_domain_confidence_threshold_generic(self, domain_library, mock_analysis_service):
        """Test that low confidence results in generic domain."""
        user_request = "I need something"

        # Mock LLM response with low confidence
        mock_result = AnalysisResult(
            response=json.dumps({
                "domain": "generic",
                "confidence": 0.4,
                "reasoning": "Request is too vague",
            }),
            model_used="haiku",
            tokens_used=100,
            duration_ms=150,
        )
        mock_analysis_service.analyze = AsyncMock(return_value=mock_result)

        domain, confidence = await domain_library.detect_domain(user_request)

        # Low confidence should result in GENERIC
        assert domain == DomainType.GENERIC
        assert confidence <= 0.7

    @pytest.mark.asyncio
    async def test_domain_detection_performance(self, domain_library):
        """Test that domain detection is fast (<200ms)."""
        user_request = "Build a web application with user authentication"

        start_time = time.time()
        domain, confidence = await domain_library.detect_domain(user_request)
        duration_ms = (time.time() - start_time) * 1000

        # Should be fast with keyword matching
        assert duration_ms < 200
        assert domain == DomainType.WEB_APP


class TestQuestionRetrieval:
    """Test question retrieval for different domains."""

    def test_get_questions_web_app(self, domain_library):
        """Test getting web app questions."""
        questions = domain_library.get_questions(DomainType.WEB_APP)

        assert len(questions) > 0
        assert len(questions) <= 15
        # Should contain web-specific questions
        assert any("authentication" in q.lower() or "user" in q.lower() for q in questions)

    def test_get_questions_mobile_app(self, domain_library):
        """Test getting mobile app questions."""
        questions = domain_library.get_questions(DomainType.MOBILE_APP)

        assert len(questions) > 0
        assert len(questions) <= 15
        # Should contain mobile-specific questions
        assert any("ios" in q.lower() or "android" in q.lower() for q in questions)

    def test_get_questions_api_service(self, domain_library):
        """Test getting API service questions."""
        questions = domain_library.get_questions(DomainType.API_SERVICE)

        assert len(questions) > 0
        assert len(questions) <= 15
        # Should contain API-specific questions
        assert any("api" in q.lower() or "endpoint" in q.lower() for q in questions)

    def test_get_questions_with_focus(self, domain_library):
        """Test getting questions with specific focus area."""
        # Get available focus areas
        focus_areas = domain_library.get_available_focus_areas(DomainType.WEB_APP)
        assert len(focus_areas) > 0

        # Get focused questions
        if "authentication" in focus_areas:
            questions = domain_library.get_questions(DomainType.WEB_APP, "authentication")
            assert len(questions) > 0
            # Should be authentication-specific
            assert any("auth" in q.lower() or "login" in q.lower() for q in questions)

    def test_get_questions_generic(self, domain_library):
        """Test getting generic questions for uncertain domain."""
        questions = domain_library.get_questions(DomainType.GENERIC)

        assert len(questions) == 10  # Generic questions are hardcoded to 10
        # Should contain general questions
        assert any("users" in q.lower() for q in questions)
        assert any("problem" in q.lower() for q in questions)

    def test_get_available_focus_areas(self, domain_library):
        """Test getting available focus areas for a domain."""
        focus_areas = domain_library.get_available_focus_areas(DomainType.WEB_APP)

        assert len(focus_areas) > 0
        # Should not include special sections
        assert "general" not in focus_areas
        assert "focus_discovery" not in focus_areas
        # Should include actual focus areas
        assert any(
            area in ["authentication", "data_model", "ui_ux", "technical", "security"]
            for area in focus_areas
        )


class TestLibraryLoading:
    """Test library file loading."""

    def test_libraries_loaded(self, domain_library):
        """Test that libraries are loaded on initialization."""
        # Should load all 5 domain libraries
        assert len(domain_library.libraries) == 5
        assert DomainType.WEB_APP in domain_library.libraries
        assert DomainType.MOBILE_APP in domain_library.libraries
        assert DomainType.API_SERVICE in domain_library.libraries
        assert DomainType.CLI_TOOL in domain_library.libraries
        assert DomainType.DATA_PIPELINE in domain_library.libraries
        # GENERIC should not be in libraries (uses hardcoded questions)
        assert DomainType.GENERIC not in domain_library.libraries

    def test_library_structure(self, domain_library):
        """Test that loaded libraries have expected structure."""
        web_library = domain_library.libraries[DomainType.WEB_APP]

        # Should have general questions
        assert "general" in web_library
        assert isinstance(web_library["general"], list)
        assert len(web_library["general"]) > 0

        # Should have focus discovery
        assert "focus_discovery" in web_library

        # Should have multiple focus areas
        assert len(web_library.keys()) > 2  # At least general + focus_discovery + 1 area


class TestMultipleKeywords:
    """Test keyword matching with multiple matches."""

    @pytest.mark.asyncio
    async def test_multiple_keyword_matches_increase_confidence(self, domain_library):
        """Test that multiple keyword matches increase confidence."""
        # Single keyword
        request_single = "Build a web app"
        domain1, confidence1 = await domain_library.detect_domain(request_single)

        # Multiple keywords
        request_multiple = "Build a responsive web app with React frontend and backend API"
        domain2, confidence2 = await domain_library.detect_domain(request_multiple)

        assert domain1 == domain2 == DomainType.WEB_APP
        # Multiple matches should have higher confidence
        assert confidence2 >= confidence1


class TestLLMClassificationErrors:
    """Test LLM classification error handling."""

    @pytest.mark.asyncio
    async def test_llm_classification_error_fallback(
        self, domain_library, mock_analysis_service
    ):
        """Test that LLM errors fall back to generic domain."""
        user_request = "I need something"

        # Mock LLM error
        mock_analysis_service.analyze = AsyncMock(side_effect=Exception("API error"))

        domain, confidence = await domain_library.detect_domain(user_request)

        # Should fall back to GENERIC on error
        assert domain == DomainType.GENERIC
        assert confidence < 0.7

    @pytest.mark.asyncio
    async def test_llm_classification_invalid_json(
        self, domain_library, mock_analysis_service
    ):
        """Test handling of invalid JSON from LLM."""
        user_request = "I need something"

        # Mock invalid JSON response
        mock_result = AnalysisResult(
            response="This is not JSON",
            model_used="haiku",
            tokens_used=100,
            duration_ms=150,
        )
        mock_analysis_service.analyze = AsyncMock(return_value=mock_result)

        domain, confidence = await domain_library.detect_domain(user_request)

        # Should fall back to GENERIC on parse error
        assert domain == DomainType.GENERIC
