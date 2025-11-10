# Story 31.4: Domain-Specific Question Libraries

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.4
**Priority**: P1 (Important - Context Awareness)
**Estimate**: 4 story points
**Duration**: 1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation), Story 30.8 (Minimal Mary)

---

## Story Description

Implement domain-specific question libraries that adapt Mary's questions to the project type. When users describe a web app, Mary asks web-specific questions (responsive design? SEO? hosting?). For mobile apps, she asks about iOS/Android, offline mode, push notifications. This makes requirements gathering contextually relevant and comprehensive.

---

## User Story

**As a** user building a project in a specific domain
**I want** Mary to ask domain-relevant questions
**So that** requirements capture domain-specific concerns

---

## Acceptance Criteria

- [ ] DomainQuestionLibrary class implemented
- [ ] 5 domain question libraries created (web_app, mobile_app, api_service, cli_tool, data_pipeline)
- [ ] Domain detection algorithm (keyword matching + LLM classification)
- [ ] Each library has 15-20 questions organized by focus area
- [ ] Question selection based on domain and context
- [ ] Confidence threshold: >0.7 for domain classification (else generic)
- [ ] Libraries stored as YAML files in `gao_dev/config/domains/`
- [ ] Mary integrates domain detection in clarification workflow
- [ ] 6+ unit tests passing
- [ ] Performance: Domain detection <200ms

---

## Files to Create/Modify

### New Files

- `gao_dev/orchestrator/domain_question_library.py` (~200 LOC)
- `gao_dev/config/domains/web_app_questions.yaml` (~80 LOC)
- `gao_dev/config/domains/mobile_app_questions.yaml` (~80 LOC)
- `gao_dev/config/domains/api_service_questions.yaml` (~80 LOC)
- `gao_dev/config/domains/cli_tool_questions.yaml` (~80 LOC)
- `gao_dev/config/domains/data_pipeline_questions.yaml` (~80 LOC)
- `tests/orchestrator/test_domain_question_library.py` (~150 LOC)

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~40 LOC added)

---

## Technical Design

### DomainQuestionLibrary

**Location**: `gao_dev/orchestrator/domain_question_library.py`

```python
"""Domain-specific question libraries for requirements clarification."""

from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path
import yaml
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
    """Domain-specific question libraries for requirements clarification."""

    def __init__(self, analysis_service: AIAnalysisService):
        self.analysis_service = analysis_service
        self.logger = logger.bind(component="domain_question_library")
        self.libraries = self._load_libraries()

    def _load_libraries(self) -> Dict[DomainType, Dict[str, List[str]]]:
        """Load all domain question libraries from YAML files."""
        config_dir = Path(__file__).parent.parent / "config" / "domains"

        libraries = {}
        for domain in DomainType:
            if domain == DomainType.GENERIC:
                continue

            yaml_file = config_dir / f"{domain.value}_questions.yaml"
            if yaml_file.exists():
                with open(yaml_file, 'r') as f:
                    libraries[domain] = yaml.safe_load(f)

        self.logger.info("libraries_loaded", count=len(libraries))
        return libraries

    async def detect_domain(
        self,
        user_request: str,
        project_context: Optional[Dict] = None
    ) -> tuple[DomainType, float]:
        """
        Detect domain from user request and context.

        Uses hybrid approach:
        1. Keyword matching (fast, 90% accuracy)
        2. LLM classification (if uncertain)

        Returns:
            (domain, confidence_score)
        """
        self.logger.info("detecting_domain", request=user_request[:50])

        # Phase 1: Keyword matching
        keyword_domain, keyword_confidence = self._keyword_matching(user_request)

        if keyword_confidence > 0.7:
            self.logger.info("domain_detected_by_keywords", domain=keyword_domain.value, confidence=keyword_confidence)
            return keyword_domain, keyword_confidence

        # Phase 2: LLM classification
        llm_domain, llm_confidence = await self._llm_classification(user_request, project_context)

        if llm_confidence > 0.7:
            self.logger.info("domain_detected_by_llm", domain=llm_domain.value, confidence=llm_confidence)
            return llm_domain, llm_confidence

        # Uncertain - use generic
        self.logger.info("domain_uncertain_using_generic")
        return DomainType.GENERIC, 0.5

    def _keyword_matching(self, user_request: str) -> tuple[DomainType, float]:
        """Fast keyword-based domain detection."""
        request_lower = user_request.lower()

        # Web app keywords
        web_keywords = ["web app", "website", "frontend", "backend", "responsive", "html", "css", "react", "vue"]
        if any(kw in request_lower for kw in web_keywords):
            return DomainType.WEB_APP, 0.8

        # Mobile app keywords
        mobile_keywords = ["mobile app", "ios", "android", "app store", "play store", "react native", "flutter"]
        if any(kw in request_lower for kw in mobile_keywords):
            return DomainType.MOBILE_APP, 0.8

        # API keywords
        api_keywords = ["api", "rest", "graphql", "endpoint", "microservice", "backend service"]
        if any(kw in request_lower for kw in api_keywords):
            return DomainType.API_SERVICE, 0.8

        # CLI keywords
        cli_keywords = ["cli", "command line", "terminal", "console", "script"]
        if any(kw in request_lower for kw in cli_keywords):
            return DomainType.CLI_TOOL, 0.8

        # Data pipeline keywords
        data_keywords = ["etl", "pipeline", "data processing", "batch job", "data warehouse", "kafka"]
        if any(kw in request_lower for kw in data_keywords):
            return DomainType.DATA_PIPELINE, 0.8

        return DomainType.GENERIC, 0.3

    async def _llm_classification(
        self,
        user_request: str,
        project_context: Optional[Dict]
    ) -> tuple[DomainType, float]:
        """LLM-based domain classification."""
        prompt = f"""
Classify this project request into one domain:

Request: "{user_request}"
Context: {project_context or 'None'}

Domains:
- web_app: Web applications, websites, frontends
- mobile_app: iOS, Android, mobile apps
- api_service: REST APIs, GraphQL, backend services
- cli_tool: Command line tools, terminal apps
- data_pipeline: ETL, data processing, batch jobs
- generic: Unclear or doesn't fit above

Return JSON:
{{
  "domain": "web_app",
  "confidence": 0.85,
  "reasoning": "Request mentions web interface and responsive design"
}}
"""

        response = await self.analysis_service.analyze(
            prompt,
            model="haiku",
            response_format="json"
        )

        result = json.loads(response)
        domain = DomainType(result["domain"])
        confidence = result["confidence"]

        return domain, confidence

    def get_questions(
        self,
        domain: DomainType,
        focus_area: Optional[str] = None
    ) -> List[str]:
        """
        Get domain-specific questions.

        Args:
            domain: Detected domain
            focus_area: Optional focus (e.g., "authentication", "data_model")

        Returns:
            10-15 contextually relevant questions
        """
        if domain == DomainType.GENERIC or domain not in self.libraries:
            return self._get_generic_questions()

        library = self.libraries[domain]

        if focus_area and focus_area in library:
            # Return focused questions
            questions = library[focus_area]
            self.logger.info("questions_selected", domain=domain.value, focus=focus_area, count=len(questions))
            return questions

        # Return general questions + focus discovery
        questions = library.get("general", [])
        questions.extend(library.get("focus_discovery", []))

        self.logger.info("questions_selected", domain=domain.value, count=len(questions))
        return questions[:15]  # Limit to 15

    def _get_generic_questions(self) -> List[str]:
        """Generic questions when domain is unclear."""
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
            "What's your timeline for launch?"
        ]
```

### Domain Question Libraries (YAML)

**Example**: `gao_dev/config/domains/web_app_questions.yaml`

```yaml
general:
  - "Who are your target users? (end users, admins, etc.)"
  - "Will this be a public or internal web application?"
  - "Do you need user authentication and authorization?"
  - "What's the expected user volume? (concurrent users, daily visits)"
  - "Does it need to be mobile-responsive?"
  - "Any specific browsers you need to support?"
  - "Will you have a backend API or server-side rendering?"

authentication:
  - "Email/password or social login (Google, GitHub, etc.)?"
  - "Multi-factor authentication required?"
  - "Session timeout requirements?"
  - "Password reset flow needed?"
  - "Role-based access control (RBAC)?"

data_model:
  - "What entities will the application manage?"
  - "Relationships between entities?"
  - "Expected data volume?"
  - "Real-time updates needed (WebSockets)?"
  - "Data export/import features?"

ui_ux:
  - "Any design system or branding guidelines?"
  - "Accessibility requirements (WCAG compliance)?"
  - "Internationalization (multiple languages)?"
  - "Dark mode support?"

technical:
  - "Preferred frontend framework? (React, Vue, Angular, vanilla JS)"
  - "Preferred backend? (Node.js, Python, Go, etc.)"
  - "Database preference? (PostgreSQL, MySQL, MongoDB, etc.)"
  - "Hosting platform? (AWS, Azure, Vercel, self-hosted)"
  - "SEO requirements?"
  - "Analytics integration?"

performance:
  - "Page load time requirements?"
  - "Offline functionality needed (PWA)?"
  - "Caching strategy?"
  - "CDN usage?"

security:
  - "Sensitive data handling? (PII, payment info)"
  - "Compliance requirements? (GDPR, HIPAA, PCI-DSS)"
  - "SSL/TLS requirements?"

focus_discovery:
  - "Which area needs most clarity: authentication, data model, UI/UX, technical, or security?"
```

**Mobile App Questions**: `mobile_app_questions.yaml`

```yaml
general:
  - "iOS, Android, or both?"
  - "Native or cross-platform? (React Native, Flutter, or native Swift/Kotlin)"
  - "Offline functionality required?"
  - "Push notifications needed?"
  - "Device sensors usage? (camera, GPS, accelerometer, etc.)"
  - "Biometric authentication? (Face ID, Touch ID)"

# ... similar structure with mobile-specific focus areas
```

---

## Testing Strategy

### Unit Tests (6+ tests)

1. **test_keyword_matching_web_app** - "web app" → WEB_APP
2. **test_keyword_matching_mobile_app** - "iOS app" → MOBILE_APP
3. **test_llm_classification_fallback** - Keywords fail → LLM classifies
4. **test_get_questions_web_app** - Web app questions returned
5. **test_get_questions_with_focus** - Focus area returns specific questions
6. **test_domain_confidence_threshold** - <0.7 confidence → generic questions

---

## Definition of Done

- [ ] DomainQuestionLibrary implemented
- [ ] 5 domain YAML files created
- [ ] Keyword + LLM hybrid detection working
- [ ] Mary integrates domain detection
- [ ] 6+ tests passing
- [ ] Performance: <200ms detection
- [ ] Manual testing with each domain
- [ ] Code review complete
- [ ] Git commit: `feat(epic-31): Story 31.4 - Domain-Specific Question Libraries (4 pts)`

---

**Created**: 2025-11-10
**Status**: Ready to Implement
