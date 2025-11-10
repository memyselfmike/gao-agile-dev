"""Domain-specific question libraries for requirements clarification.

This module provides domain detection and contextually relevant questions
for different project types (web apps, mobile apps, APIs, etc.).

Epic: 31 - Full Mary (Business Analyst) Integration
Story: 31.4 - Domain-Specific Question Libraries
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from pathlib import Path
import yaml
import json
import structlog

from ..core.services.ai_analysis_service import AIAnalysisService

logger = structlog.get_logger()


class DomainType(Enum):
    """Project domain types."""

    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API_SERVICE = "api_service"
    CLI_TOOL = "cli_tool"
    DATA_PIPELINE = "data_pipeline"
    GENERIC = "generic"


class DomainQuestionLibrary:
    """Domain-specific question libraries for requirements clarification.

    Uses hybrid approach for domain detection:
    1. Keyword matching (fast, 90% accuracy)
    2. LLM classification (if uncertain)

    Performance: Domain detection <200ms
    Confidence threshold: >0.7 for domain classification (else generic)
    """

    def __init__(self, analysis_service: AIAnalysisService):
        """
        Initialize domain question library.

        Args:
            analysis_service: AI analysis service for LLM classification
        """
        self.analysis_service = analysis_service
        self.logger = logger.bind(component="domain_question_library")
        self.libraries = self._load_libraries()

    def _load_libraries(self) -> Dict[DomainType, Dict[str, List[str]]]:
        """Load all domain question libraries from YAML files.

        Returns:
            Dictionary mapping DomainType to question library structure

        Raises:
            IOError: If library files cannot be loaded
        """
        config_dir = Path(__file__).parent.parent / "config" / "domains"

        libraries = {}
        for domain in DomainType:
            if domain == DomainType.GENERIC:
                continue

            yaml_file = config_dir / f"{domain.value}_questions.yaml"
            if yaml_file.exists():
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        libraries[domain] = yaml.safe_load(f)
                    self.logger.debug("library_loaded", domain=domain.value, file=str(yaml_file))
                except Exception as e:
                    self.logger.error(
                        "library_load_failed", domain=domain.value, file=str(yaml_file), error=str(e)
                    )
            else:
                self.logger.warning("library_file_not_found", domain=domain.value, file=str(yaml_file))

        self.logger.info("libraries_loaded", count=len(libraries))
        return libraries

    async def detect_domain(
        self, user_request: str, project_context: Optional[Dict] = None
    ) -> Tuple[DomainType, float]:
        """
        Detect domain from user request and context.

        Uses hybrid approach:
        1. Keyword matching (fast, 90% accuracy)
        2. LLM classification (if uncertain)

        Args:
            user_request: User's project description or request
            project_context: Optional project context dict

        Returns:
            Tuple of (domain, confidence_score)
            - domain: Detected DomainType
            - confidence_score: 0.0-1.0 confidence level
        """
        self.logger.info("detecting_domain", request=user_request[:50])

        # Phase 1: Keyword matching
        keyword_domain, keyword_confidence = self._keyword_matching(user_request)

        if keyword_confidence > 0.7:
            self.logger.info(
                "domain_detected_by_keywords",
                domain=keyword_domain.value,
                confidence=keyword_confidence,
            )
            return keyword_domain, keyword_confidence

        # Phase 2: LLM classification
        llm_domain, llm_confidence = await self._llm_classification(user_request, project_context)

        if llm_confidence > 0.7:
            self.logger.info(
                "domain_detected_by_llm", domain=llm_domain.value, confidence=llm_confidence
            )
            return llm_domain, llm_confidence

        # Uncertain - use generic
        self.logger.info("domain_uncertain_using_generic")
        return DomainType.GENERIC, 0.5

    def _keyword_matching(self, user_request: str) -> Tuple[DomainType, float]:
        """Fast keyword-based domain detection.

        Args:
            user_request: User's project description

        Returns:
            Tuple of (domain, confidence_score)
        """
        request_lower = user_request.lower()

        # Define keyword patterns with weights
        patterns = [
            # Web app keywords (check first - most common)
            (
                DomainType.WEB_APP,
                [
                    "web app",
                    "website",
                    "web application",
                    "frontend",
                    "backend",
                    "responsive",
                    "html",
                    "css",
                    "react",
                    "vue",
                    "angular",
                    "next.js",
                    "django",
                    "flask",
                ],
                0.85,
            ),
            # Mobile app keywords
            (
                DomainType.MOBILE_APP,
                [
                    "mobile app",
                    "ios",
                    "android",
                    "app store",
                    "play store",
                    "react native",
                    "flutter",
                    "swift",
                    "kotlin",
                    "mobile application",
                ],
                0.85,
            ),
            # API keywords
            (
                DomainType.API_SERVICE,
                [
                    "api",
                    "rest",
                    "restful",
                    "graphql",
                    "endpoint",
                    "microservice",
                    "backend service",
                    "web service",
                    "grpc",
                ],
                0.85,
            ),
            # CLI keywords
            (
                DomainType.CLI_TOOL,
                [
                    "cli",
                    "command line",
                    "terminal",
                    "console",
                    "script",
                    "command-line tool",
                    "cli tool",
                ],
                0.85,
            ),
            # Data pipeline keywords
            (
                DomainType.DATA_PIPELINE,
                [
                    "etl",
                    "pipeline",
                    "data processing",
                    "batch job",
                    "data warehouse",
                    "kafka",
                    "airflow",
                    "data pipeline",
                    "stream processing",
                ],
                0.85,
            ),
        ]

        # Check each pattern
        for domain, keywords, base_confidence in patterns:
            matches = sum(1 for kw in keywords if kw in request_lower)
            if matches > 0:
                # Adjust confidence based on number of matches
                # 1 match = base, 2+ matches = higher confidence
                confidence = min(base_confidence + (matches - 1) * 0.05, 0.95)
                self.logger.debug(
                    "keyword_match_found",
                    domain=domain.value,
                    matches=matches,
                    confidence=confidence,
                )
                return domain, confidence

        # No strong keywords found
        return DomainType.GENERIC, 0.3

    async def _llm_classification(
        self, user_request: str, project_context: Optional[Dict]
    ) -> Tuple[DomainType, float]:
        """LLM-based domain classification.

        Used as fallback when keyword matching is uncertain.

        Args:
            user_request: User's project description
            project_context: Optional project context

        Returns:
            Tuple of (domain, confidence_score)
        """
        prompt = f"""Classify this project request into one domain:

Request: "{user_request}"
Context: {project_context or 'None'}

Domains:
- web_app: Web applications, websites, frontends, full-stack apps
- mobile_app: iOS, Android, mobile apps (native or cross-platform)
- api_service: REST APIs, GraphQL, backend services, microservices
- cli_tool: Command line tools, terminal apps, scripts
- data_pipeline: ETL, data processing, batch jobs, streaming
- generic: Unclear or doesn't fit above categories

Return JSON:
{{
  "domain": "web_app",
  "confidence": 0.85,
  "reasoning": "Request mentions web interface and responsive design"
}}
"""

        try:
            response = await self.analysis_service.analyze(
                prompt, model="haiku", response_format="json"
            )

            result = json.loads(response.response)
            domain = DomainType(result["domain"])
            confidence = float(result["confidence"])

            self.logger.debug(
                "llm_classification_result",
                domain=domain.value,
                confidence=confidence,
                reasoning=result.get("reasoning", ""),
            )

            return domain, confidence

        except Exception as e:
            self.logger.error("llm_classification_failed", error=str(e))
            # Fallback to generic on error
            return DomainType.GENERIC, 0.4

    def get_questions(
        self, domain: DomainType, focus_area: Optional[str] = None
    ) -> List[str]:
        """
        Get domain-specific questions.

        Args:
            domain: Detected domain
            focus_area: Optional focus area (e.g., "authentication", "data_model")

        Returns:
            List of 10-15 contextually relevant questions
        """
        if domain == DomainType.GENERIC or domain not in self.libraries:
            questions = self._get_generic_questions()
            self.logger.info("generic_questions_selected", count=len(questions))
            return questions

        library = self.libraries[domain]

        if focus_area and focus_area in library:
            # Return focused questions
            questions = library[focus_area]
            self.logger.info(
                "questions_selected",
                domain=domain.value,
                focus=focus_area,
                count=len(questions),
            )
            return questions[:15]  # Limit to 15

        # Return general questions + focus discovery
        questions = []
        questions.extend(library.get("general", []))

        # Add focus discovery questions if available
        if "focus_discovery" in library:
            questions.extend(library["focus_discovery"])

        self.logger.info("questions_selected", domain=domain.value, count=len(questions))
        return questions[:15]  # Limit to 15

    def _get_generic_questions(self) -> List[str]:
        """Generic questions when domain is unclear.

        Returns:
            List of 10 general-purpose questions
        """
        return [
            "Who are the primary users of this system?",
            "What problem are you trying to solve?",
            "What are the key features or capabilities needed?",
            "Are there any specific constraints (time, budget, technical)?",
            "How will success be measured?",
            "Are there similar existing solutions?",
            "What makes this solution unique or better?",
            "What are the expected user volumes?",
            "Any compliance or regulatory requirements?",
            "What's your timeline for launch?",
        ]

    def get_available_focus_areas(self, domain: DomainType) -> List[str]:
        """
        Get available focus areas for a domain.

        Args:
            domain: Domain type

        Returns:
            List of focus area names (e.g., ["authentication", "data_model", "ui_ux"])
        """
        if domain == DomainType.GENERIC or domain not in self.libraries:
            return []

        library = self.libraries[domain]
        # Exclude special sections
        excluded = {"general", "focus_discovery"}
        focus_areas = [key for key in library.keys() if key not in excluded]

        self.logger.debug("focus_areas_retrieved", domain=domain.value, areas=focus_areas)
        return focus_areas
