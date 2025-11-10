"""Tests for RequirementsAnalyzer.

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.3 - Advanced Requirements Analysis
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from gao_dev.orchestrator.requirements_analyzer import RequirementsAnalyzer
from gao_dev.core.models.requirements_analysis import (
    MoSCoWCategory,
    KanoCategory,
    Risk,
    Constraint,
    RequirementsAnalysis,
)
from gao_dev.core.services.ai_analysis_service import AIAnalysisService, AnalysisResult


@pytest.fixture
def mock_analysis_service():
    """Create mock AIAnalysisService."""
    service = Mock(spec=AIAnalysisService)
    service.analyze = AsyncMock()
    return service


@pytest.fixture
def requirements_analyzer(mock_analysis_service):
    """Create RequirementsAnalyzer with mocked dependencies."""
    analyzer = RequirementsAnalyzer(analysis_service=mock_analysis_service)
    return analyzer


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return [
        "User authentication with email and password",
        "Dashboard with real-time metrics",
        "Export reports to PDF format",
        "Mobile responsive design",
    ]


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return {
        "product_vision": "Build a project management tool for small teams",
        "timeline": "3 months",
        "team_size": "2 developers",
        "budget": "$50,000",
        "technical_stack": "Python, React, PostgreSQL",
    }


class TestMoSCoWPrioritization:
    """Tests for MoSCoW prioritization."""

    @pytest.mark.asyncio
    async def test_moscow_prioritization_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements, sample_context
    ):
        """Test successful MoSCoW prioritization."""
        # Mock AI response
        moscow_data = [
            {
                "requirement": "User authentication with email and password",
                "category": "must",
                "rationale": "Critical for security and user management",
            },
            {
                "requirement": "Dashboard with real-time metrics",
                "category": "should",
                "rationale": "Important for user value but can start with basic version",
            },
            {
                "requirement": "Export reports to PDF format",
                "category": "could",
                "rationale": "Nice to have, not critical for MVP",
            },
            {
                "requirement": "Mobile responsive design",
                "category": "must",
                "rationale": "Essential for modern applications",
            },
        ]

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response=json.dumps(moscow_data),
            model_used="haiku",
            tokens_used=500,
            duration_ms=1500,
        )

        # Execute
        categories = await requirements_analyzer.moscow_prioritize(
            sample_requirements, sample_context
        )

        # Verify
        assert len(categories) == 4
        assert all(isinstance(c, MoSCoWCategory) for c in categories)

        must_items = [c for c in categories if c.category == "must"]
        should_items = [c for c in categories if c.category == "should"]
        could_items = [c for c in categories if c.category == "could"]

        assert len(must_items) == 2
        assert len(should_items) == 1
        assert len(could_items) == 1

        # Verify analysis service was called
        mock_analysis_service.analyze.assert_called_once()
        call_args = mock_analysis_service.analyze.call_args
        assert "MoSCoW" in call_args[0][0]
        assert call_args[1]["model"] == "haiku"
        assert call_args[1]["response_format"] == "json"

    @pytest.mark.asyncio
    async def test_moscow_prioritization_empty_requirements(
        self, requirements_analyzer, sample_context
    ):
        """Test MoSCoW prioritization with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.moscow_prioritize([], sample_context)

    @pytest.mark.asyncio
    async def test_moscow_prioritization_json_parse_failure(
        self, requirements_analyzer, mock_analysis_service, sample_requirements, sample_context
    ):
        """Test graceful handling of JSON parse failure."""
        # Mock invalid JSON response
        mock_analysis_service.analyze.return_value = AnalysisResult(
            response="Not valid JSON",
            model_used="haiku",
            tokens_used=100,
            duration_ms=500,
        )

        # Execute - should not raise, should return fallback
        categories = await requirements_analyzer.moscow_prioritize(
            sample_requirements, sample_context
        )

        # Verify fallback behavior
        assert len(categories) == len(sample_requirements)
        assert all(c.category == "should" for c in categories)
        assert all("Unable to analyze" in c.rationale for c in categories)


class TestKanoCategorization:
    """Tests for Kano model categorization."""

    @pytest.mark.asyncio
    async def test_kano_categorization_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements
    ):
        """Test successful Kano model categorization."""
        # Mock AI response
        kano_data = [
            {
                "requirement": "User authentication with email and password",
                "category": "basic",
                "rationale": "Users expect this in any modern application",
            },
            {
                "requirement": "Dashboard with real-time metrics",
                "category": "performance",
                "rationale": "Quality of implementation affects satisfaction",
            },
            {
                "requirement": "Export reports to PDF format",
                "category": "excitement",
                "rationale": "Unexpected feature that delights users",
            },
            {
                "requirement": "Mobile responsive design",
                "category": "basic",
                "rationale": "Expected in modern web applications",
            },
        ]

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response=json.dumps(kano_data),
            model_used="haiku",
            tokens_used=500,
            duration_ms=1500,
        )

        # Execute
        categories = await requirements_analyzer.kano_categorize(sample_requirements)

        # Verify
        assert len(categories) == 4
        assert all(isinstance(c, KanoCategory) for c in categories)

        basic_items = [c for c in categories if c.category == "basic"]
        performance_items = [c for c in categories if c.category == "performance"]
        excitement_items = [c for c in categories if c.category == "excitement"]

        assert len(basic_items) == 2
        assert len(performance_items) == 1
        assert len(excitement_items) == 1

    @pytest.mark.asyncio
    async def test_kano_categorization_empty_requirements(self, requirements_analyzer):
        """Test Kano categorization with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.kano_categorize([])


class TestDependencyMapping:
    """Tests for dependency mapping."""

    @pytest.mark.asyncio
    async def test_dependency_mapping_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements
    ):
        """Test successful dependency mapping."""
        # Mock AI response
        dependencies_data = {
            "User authentication with email and password": [],
            "Dashboard with real-time metrics": ["User authentication with email and password"],
            "Export reports to PDF format": ["Dashboard with real-time metrics"],
            "Mobile responsive design": [],
        }

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response=json.dumps(dependencies_data),
            model_used="haiku",
            tokens_used=400,
            duration_ms=1200,
        )

        # Execute
        dependencies = await requirements_analyzer.map_dependencies(sample_requirements)

        # Verify
        assert isinstance(dependencies, dict)
        assert len(dependencies) == 4
        assert dependencies["User authentication with email and password"] == []
        assert len(dependencies["Dashboard with real-time metrics"]) == 1
        assert len(dependencies["Export reports to PDF format"]) == 1
        assert dependencies["Mobile responsive design"] == []

    @pytest.mark.asyncio
    async def test_dependency_mapping_empty_requirements(self, requirements_analyzer):
        """Test dependency mapping with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.map_dependencies([])


class TestRiskIdentification:
    """Tests for risk identification."""

    @pytest.mark.asyncio
    async def test_risk_identification_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements, sample_context
    ):
        """Test successful risk identification."""
        # Mock AI response
        risks_data = [
            {
                "description": "Real-time metrics may require complex infrastructure",
                "category": "technical",
                "severity": "high",
                "likelihood": "medium",
                "mitigation": "Use proven real-time data libraries and services",
            },
            {
                "description": "Limited team size may cause delays",
                "category": "resource",
                "severity": "medium",
                "likelihood": "high",
                "mitigation": "Prioritize MVP features and use agile development",
            },
            {
                "description": "PDF generation may have browser compatibility issues",
                "category": "technical",
                "severity": "low",
                "likelihood": "low",
                "mitigation": "Use established PDF generation library",
            },
        ]

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response=json.dumps(risks_data),
            model_used="sonnet",
            tokens_used=800,
            duration_ms=2500,
        )

        # Execute
        risks = await requirements_analyzer.identify_risks(sample_requirements, sample_context)

        # Verify
        assert len(risks) == 3
        assert all(isinstance(r, Risk) for r in risks)

        high_risks = [r for r in risks if r.severity == "high"]
        medium_risks = [r for r in risks if r.severity == "medium"]
        low_risks = [r for r in risks if r.severity == "low"]

        assert len(high_risks) == 1
        assert len(medium_risks) == 1
        assert len(low_risks) == 1

        # Verify sonnet model was used (more intelligent for risk analysis)
        call_args = mock_analysis_service.analyze.call_args
        assert call_args[1]["model"] == "sonnet"

    @pytest.mark.asyncio
    async def test_risk_identification_empty_requirements(
        self, requirements_analyzer, sample_context
    ):
        """Test risk identification with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.identify_risks([], sample_context)


class TestConstraintAnalysis:
    """Tests for constraint analysis."""

    @pytest.mark.asyncio
    async def test_constraint_analysis_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements, sample_context
    ):
        """Test successful constraint analysis."""
        # Mock AI response
        constraints_data = {
            "time": ["Must launch by Q2 2025", "3-month development window"],
            "budget": ["Limited to $50,000", "No additional funding available"],
            "technical": ["Must use Python and React", "PostgreSQL database required"],
            "compliance": ["GDPR compliance required for EU users"],
            "resource": ["Only 2 developers available", "No dedicated designer"],
        }

        mock_analysis_service.analyze.return_value = AnalysisResult(
            response=json.dumps(constraints_data),
            model_used="haiku",
            tokens_used=600,
            duration_ms=1800,
        )

        # Execute
        constraints = await requirements_analyzer.analyze_constraints(
            sample_requirements, sample_context
        )

        # Verify
        assert isinstance(constraints, dict)
        assert len(constraints) == 5
        assert len(constraints["time"]) == 2
        assert len(constraints["budget"]) == 2
        assert len(constraints["technical"]) == 2
        assert len(constraints["compliance"]) == 1
        assert len(constraints["resource"]) == 2

    @pytest.mark.asyncio
    async def test_constraint_analysis_empty_requirements(
        self, requirements_analyzer, sample_context
    ):
        """Test constraint analysis with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.analyze_constraints([], sample_context)


class TestFullAnalysis:
    """Tests for complete requirements analysis."""

    @pytest.mark.asyncio
    async def test_analyze_all_success(
        self, requirements_analyzer, mock_analysis_service, sample_requirements, sample_context
    ):
        """Test complete requirements analysis."""
        # Setup mock responses for all methods
        mock_analysis_service.analyze.side_effect = [
            # MoSCoW response
            AnalysisResult(
                response=json.dumps(
                    [
                        {
                            "requirement": sample_requirements[0],
                            "category": "must",
                            "rationale": "Critical",
                        }
                    ]
                    * len(sample_requirements)
                ),
                model_used="haiku",
                tokens_used=500,
                duration_ms=1500,
            ),
            # Kano response
            AnalysisResult(
                response=json.dumps(
                    [
                        {
                            "requirement": sample_requirements[0],
                            "category": "basic",
                            "rationale": "Expected",
                        }
                    ]
                    * len(sample_requirements)
                ),
                model_used="haiku",
                tokens_used=500,
                duration_ms=1500,
            ),
            # Dependencies response
            AnalysisResult(
                response=json.dumps({req: [] for req in sample_requirements}),
                model_used="haiku",
                tokens_used=400,
                duration_ms=1200,
            ),
            # Risks response
            AnalysisResult(
                response=json.dumps(
                    [
                        {
                            "description": "Sample risk",
                            "category": "technical",
                            "severity": "medium",
                            "likelihood": "low",
                            "mitigation": "Monitor closely",
                        }
                    ]
                ),
                model_used="sonnet",
                tokens_used=800,
                duration_ms=2500,
            ),
            # Constraints response
            AnalysisResult(
                response=json.dumps(
                    {
                        "time": ["3 months"],
                        "budget": ["$50K"],
                        "technical": ["Python"],
                        "compliance": [],
                        "resource": ["2 devs"],
                    }
                ),
                model_used="haiku",
                tokens_used=600,
                duration_ms=1800,
            ),
        ]

        # Execute
        analysis = await requirements_analyzer.analyze_all(sample_requirements, sample_context)

        # Verify
        assert isinstance(analysis, RequirementsAnalysis)
        assert analysis.original_requirements == sample_requirements
        assert len(analysis.moscow) == len(sample_requirements)
        assert len(analysis.kano) == len(sample_requirements)
        assert len(analysis.dependencies) == len(sample_requirements)
        assert len(analysis.risks) >= 1
        assert len(analysis.constraints) == 5

        # Verify all 5 analysis methods were called
        assert mock_analysis_service.analyze.call_count == 5

    @pytest.mark.asyncio
    async def test_analyze_all_empty_requirements(self, requirements_analyzer, sample_context):
        """Test complete analysis with empty requirements list."""
        with pytest.raises(ValueError, match="Requirements list cannot be empty"):
            await requirements_analyzer.analyze_all([], sample_context)


class TestRequirementsAnalysisModel:
    """Tests for RequirementsAnalysis data model."""

    def test_to_markdown(self, sample_requirements):
        """Test markdown generation."""
        analysis = RequirementsAnalysis(
            original_requirements=sample_requirements,
            moscow=[
                MoSCoWCategory(
                    requirement=sample_requirements[0], category="must", rationale="Critical"
                )
            ],
            kano=[
                KanoCategory(
                    requirement=sample_requirements[0], category="basic", rationale="Expected"
                )
            ],
            dependencies={sample_requirements[0]: []},
            risks=[
                Risk(
                    description="Sample risk",
                    category="technical",
                    severity="high",
                    likelihood="medium",
                    mitigation="Test thoroughly",
                )
            ],
            constraints={"time": ["3 months"], "budget": ["$50K"]},
        )

        markdown = analysis.to_markdown()

        # Verify markdown content
        assert "# Requirements Analysis Report" in markdown
        assert "## MoSCoW Prioritization" in markdown
        assert "## Kano Model Analysis" in markdown
        assert "## Dependency Map" in markdown
        assert "## Risk Analysis" in markdown
        assert "## Constraint Analysis" in markdown
        assert "Generated by**: Mary (Business Analyst)" in markdown

    def test_get_must_have_requirements(self, sample_requirements):
        """Test getting MUST requirements."""
        analysis = RequirementsAnalysis(
            original_requirements=sample_requirements,
            moscow=[
                MoSCoWCategory(requirement=sample_requirements[0], category="must", rationale=""),
                MoSCoWCategory(requirement=sample_requirements[1], category="should", rationale=""),
                MoSCoWCategory(requirement=sample_requirements[2], category="must", rationale=""),
            ],
        )

        must_reqs = analysis.get_must_have_requirements()

        assert len(must_reqs) == 2
        assert sample_requirements[0] in must_reqs
        assert sample_requirements[2] in must_reqs

    def test_get_high_priority_risks(self):
        """Test getting high priority risks."""
        analysis = RequirementsAnalysis(
            original_requirements=["req1"],
            risks=[
                Risk(
                    description="High severity",
                    category="technical",
                    severity="high",
                    likelihood="low",
                    mitigation="",
                ),
                Risk(
                    description="High likelihood",
                    category="resource",
                    severity="low",
                    likelihood="high",
                    mitigation="",
                ),
                Risk(
                    description="Low priority",
                    category="scope",
                    severity="low",
                    likelihood="low",
                    mitigation="",
                ),
            ],
        )

        high_risks = analysis.get_high_priority_risks()

        assert len(high_risks) == 2
        assert high_risks[0].description == "High severity"
        assert high_risks[1].description == "High likelihood"

    def test_get_dependency_order(self, sample_requirements):
        """Test getting requirements in dependency order."""
        analysis = RequirementsAnalysis(
            original_requirements=sample_requirements,
            dependencies={
                sample_requirements[0]: [],  # No dependencies
                sample_requirements[1]: [sample_requirements[0]],  # Depends on first
                sample_requirements[2]: [],  # No dependencies
                sample_requirements[3]: [sample_requirements[1]],  # Depends on second
            },
        )

        ordered = analysis.get_dependency_order()

        # Requirements with no dependencies should come first
        assert sample_requirements[0] in ordered[:2]
        assert sample_requirements[2] in ordered[:2]
        # Requirements with dependencies should come later
        assert sample_requirements[1] in ordered[2:]
        assert sample_requirements[3] in ordered[2:]
