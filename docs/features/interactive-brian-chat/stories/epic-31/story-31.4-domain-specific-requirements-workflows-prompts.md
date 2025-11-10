# Story 31.4: Domain-Specific Requirements Workflows & Prompts

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.4
**Priority**: P1 (Important - Context Awareness)
**Estimate**: 3 story points
**Duration**: 1 day
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation Workflows), Story 30.8 (Minimal Mary)

---

## Story Description

Implement domain-specific requirements workflows and prompts that adapt Mary's questions to the project type. When users describe a web app, Mary asks web-specific questions (responsive design, SEO, hosting). For mobile apps, she asks about iOS/Android, offline mode, push notifications. This makes requirements gathering contextually relevant and comprehensive.

**Epic 10 Integration**: Following GAO-Dev's established pattern, we separate:
- **Workflow** (metadata only) → `gao_dev/workflows/1-analysis/domain-requirements/workflow.yaml`
- **Prompts** (LLM instructions with embedded questions) → `gao_dev/prompts/agents/mary_domain_*.yaml` (5 files)

Domain-specific questions are EMBEDDED in prompts, not stored in separate library classes. This keeps prompts self-contained and easier to maintain.

---

## User Story

**As a** user building a project in a specific domain
**I want** Mary to ask domain-relevant questions
**So that** requirements capture domain-specific concerns

---

## Acceptance Criteria

### Workflows & Prompts
- [ ] Workflow file created: `gao_dev/workflows/1-analysis/domain-requirements/workflow.yaml` (metadata only)
- [ ] 5 prompt files created in `gao_dev/prompts/agents/`:
  - [ ] `mary_domain_web_app.yaml` (Web app requirements)
  - [ ] `mary_domain_mobile_app.yaml` (Mobile app requirements)
  - [ ] `mary_domain_api_service.yaml` (API service requirements)
  - [ ] `mary_domain_cli_tool.yaml` (CLI tool requirements)
  - [ ] `mary_domain_data_pipeline.yaml` (Data pipeline requirements)
- [ ] All prompts follow Epic 10 format (system_prompt, user_prompt, variables, response, metadata)
- [ ] All prompts use `@file:gao_dev/agents/mary.md` for persona injection
- [ ] All prompts use `{{variable}}` syntax for substitution
- [ ] Domain-specific questions EMBEDDED in prompts (15-20 questions per domain)

### Code Implementation
- [ ] MaryOrchestrator enhanced with `gather_domain_requirements()` method
- [ ] BrianOrchestrator enhanced with `detect_domain()` method
- [ ] MaryOrchestrator uses PromptLoader (Epic 10) to load domain prompts
- [ ] Domain detection: keyword matching + LLM fallback
- [ ] Confidence threshold: >0.7 for domain classification (else generic)
- [ ] DomainRequirements data model implemented
- [ ] Requirements outputs saved to `.gao-dev/mary/domain-requirements/`

### Integration
- [ ] Brian detects domain from user request
- [ ] Brian delegates to Mary with detected domain
- [ ] Mary selects appropriate domain-specific prompt
- [ ] Domain requirements handed back to Brian

### Testing
- [ ] 11+ unit tests passing (5 prompts × 2 tests + 1 orchestrator test)
- [ ] Integration test: domain detection → domain-specific questions → requirements
- [ ] Performance: Domain detection <200ms

---

## Files to Create/Modify

### New Files

**Workflow (Metadata)**:
- `gao_dev/workflows/1-analysis/domain-requirements/workflow.yaml` (~60 LOC)
  - Metadata for all 5 domains
  - Variable definitions
  - Prompt references (not embedded instructions!)

**Prompts (LLM Instructions with Embedded Questions)**:
- `gao_dev/prompts/agents/mary_domain_web_app.yaml` (~150 LOC)
  - System prompt with Mary's persona and web app context
  - User prompt with 20 domain-specific questions organized by focus area
  - Questions embedded in prompt (authentication, data model, UI/UX, technical, performance, security)
  - Variables: `mary_persona`, `user_request`, `project_context`
  - Response config: max_tokens, temperature

- `gao_dev/prompts/agents/mary_domain_mobile_app.yaml` (~150 LOC)
  - Mobile-specific questions (iOS/Android, offline, push notifications, sensors, biometrics)

- `gao_dev/prompts/agents/mary_domain_api_service.yaml` (~140 LOC)
  - API-specific questions (REST/GraphQL, authentication, rate limiting, versioning)

- `gao_dev/prompts/agents/mary_domain_cli_tool.yaml` (~130 LOC)
  - CLI-specific questions (commands, configuration, output formats, interactive/non-interactive)

- `gao_dev/prompts/agents/mary_domain_data_pipeline.yaml` (~140 LOC)
  - Data pipeline-specific questions (ETL, scheduling, error handling, monitoring, data quality)

**Data Models**:
- `gao_dev/core/models/domain_requirements.py` (~100 LOC)
  - DomainRequirements dataclass
  - to_markdown() method for file output
  - to_prompt() method for handing to Brian

**Tests**:
- `tests/orchestrator/test_mary_domain_requirements.py` (~180 LOC)
  - Test each of 5 prompts (prompt rendering, variable resolution)
  - Test domain detection (keyword + LLM)
  - Test domain requirements gathering
  - Integration test: end-to-end domain-specific flow

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~60 LOC modified/added)
  - Add `gather_domain_requirements()` method
  - Use PromptLoader to load domain prompts
  - Generate DomainRequirements from conversation
  - Save to `.gao-dev/mary/domain-requirements/`

- `gao_dev/orchestrator/brian_orchestrator.py` (~40 LOC modified/added)
  - Add `detect_domain()` method
  - Keyword matching + LLM classification
  - Update delegation logic to pass detected domain to Mary

---

## Technical Design

### Architecture Overview

```
User: "Build a mobile fitness tracking app"
  ↓
BrianOrchestrator.detect_domain()
  ├─ Keyword matching: "mobile" → DomainType.MOBILE_APP (confidence: 0.85)
  └─ (LLM classification only if keyword confidence < 0.7)
  ↓
BrianOrchestrator delegates to Mary with domain=mobile_app
  ↓
MaryOrchestrator.gather_domain_requirements(domain="mobile_app")
  ├─ Load workflow: "domain-requirements/workflow.yaml"
  ├─ Load prompt: "mary_domain_mobile_app" (via PromptLoader)
  ├─ Render prompt with variables
  ├─ Execute LLM with domain-specific questions embedded in prompt
  ├─ LLM adapts questions conversationally based on user responses
  ├─ Generate DomainRequirements
  └─ Save to .gao-dev/mary/domain-requirements/mobile-app-{timestamp}.md
  ↓
Return DomainRequirements to Brian
  ↓
Brian uses requirements for workflow selection
```

### Workflow File (Metadata Only)

**File**: `gao_dev/workflows/1-analysis/domain-requirements/workflow.yaml`

```yaml
name: domain-requirements
description: Domain-specific requirements gathering
phase: 1
author: Mary (Business Analyst)
non_interactive: false
autonomous: false
iterative: true

variables:
  user_request:
    description: Original user request
    type: string
    required: true

  domain:
    description: Detected domain type
    type: string
    required: true
    allowed_values:
      - web_app
      - mobile_app
      - api_service
      - cli_tool
      - data_pipeline
      - generic

  project_context:
    description: Optional project context
    type: string
    default: ""

required_tools:
  - conversation_manager
  - analysis_service

output_file: ".gao-dev/mary/domain-requirements/{{domain}}-{{timestamp}}.md"

# Reference prompts by name (Epic 10 pattern)
prompts:
  web_app: "mary_domain_web_app"
  mobile_app: "mary_domain_mobile_app"
  api_service: "mary_domain_api_service"
  cli_tool: "mary_domain_cli_tool"
  data_pipeline: "mary_domain_data_pipeline"

metadata:
  category: domain_requirements
  domain: business_analysis
  domains_available: 5
  typical_duration: 10-15  # minutes
```

### Prompt File Example: Web App

**File**: `gao_dev/prompts/agents/mary_domain_web_app.yaml`

```yaml
name: mary_domain_web_app
description: "Mary gathers web application requirements"
version: 1.0.0

system_prompt: |
  You are Mary, a Business Analyst gathering requirements for a web application.

  {{mary_persona}}

  **Web Application Context**:
  Web applications have specific considerations:
  - Frontend (browser-based UI)
  - Backend (server-side logic)
  - Database (data persistence)
  - Hosting/deployment
  - Responsive design (mobile, tablet, desktop)
  - SEO and discoverability
  - Performance and loading times
  - Security (authentication, authorization, data protection)

  **Your Approach**:
  - Start with general questions about the web app
  - Based on user's answers, dive deeper into relevant areas
  - Don't ask all questions - be selective and conversational
  - Adapt based on what the user tells you
  - If they mention authentication, ask authentication questions
  - If they discuss scale, ask performance questions
  - Keep it natural - you're having a conversation, not filling a form

user_prompt: |
  Let's gather requirements for your web application: {{user_request}}

  **Domain-Specific Questions** (Adapt based on conversation):

  **General**:
  - Who are your target users? (end users, admins, etc.)
  - Will this be a public or internal web application?
  - Do you need user authentication and authorization?
  - What's the expected user volume? (concurrent users, daily visits)
  - Does it need to be mobile-responsive?
  - Any specific browsers you need to support?
  - Will you have a backend API or server-side rendering?

  **Authentication** (if relevant):
  - Email/password or social login (Google, GitHub, etc.)?
  - Multi-factor authentication required?
  - Session timeout requirements?
  - Password reset flow needed?
  - Role-based access control (RBAC)?

  **Data Model** (if relevant):
  - What entities will the application manage?
  - Relationships between entities?
  - Expected data volume?
  - Real-time updates needed (WebSockets)?
  - Data export/import features?

  **UI/UX** (if relevant):
  - Any design system or branding guidelines?
  - Accessibility requirements (WCAG compliance)?
  - Internationalization (multiple languages)?
  - Dark mode support?

  **Technical** (if relevant):
  - Preferred frontend framework? (React, Vue, Angular, vanilla JS)
  - Preferred backend? (Node.js, Python, Go, etc.)
  - Database preference? (PostgreSQL, MySQL, MongoDB, etc.)
  - Hosting platform? (AWS, Azure, Vercel, self-hosted)
  - SEO requirements?
  - Analytics integration?

  **Performance** (if relevant):
  - Page load time requirements?
  - Offline functionality needed (PWA)?
  - Caching strategy?
  - CDN usage?

  **Security** (if relevant):
  - Sensitive data handling? (PII, payment info)
  - Compliance requirements? (GDPR, HIPAA, PCI-DSS)
  - SSL/TLS requirements?

  **Session Structure** (10-15 turns):
  1. Start with general questions
  2. Listen to user's responses
  3. Identify focus areas from their answers
  4. Ask targeted follow-up questions in those areas
  5. Don't ask questions about areas they haven't mentioned
  6. Keep it conversational and adaptive
  7. Synthesize requirements at the end

  **Important**:
  - You don't need to ask ALL questions
  - Pick the most relevant 8-12 based on their responses
  - If they give a detailed answer, build on it instead of asking next question
  - Use "Yes, and..." to validate and expand
  - Make it feel natural, not like an interrogation

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"  # Epic 10 reference resolution
  user_request: ""
  project_context: ""

response:
  max_tokens: 1024
  temperature: 0.7
  format: text

metadata:
  category: domain_requirements
  agent: mary
  phase: 1
  domain: web_app
  questions_available: 20
  typical_duration: 10-15
  best_for: "Web applications, SaaS products, internal tools"
  original_source: "Professional BA practice (adapted for GAO-Dev)"
```

### BrianOrchestrator Domain Detection

**File**: `gao_dev/orchestrator/brian_orchestrator.py`

```python
class BrianOrchestrator:
    async def detect_domain(self, user_request: str) -> tuple[str, float]:
        """
        Detect domain from user request.

        Uses hybrid approach:
        1. Keyword matching (fast, 90% accuracy)
        2. LLM classification (if uncertain)

        Returns:
            (domain, confidence_score)
        """
        self.logger.info("detecting_domain", request=user_request[:50])

        # Phase 1: Keyword matching
        domain, confidence = self._keyword_matching(user_request)

        if confidence > 0.7:
            self.logger.info("domain_detected_by_keywords", domain=domain, confidence=confidence)
            return domain, confidence

        # Phase 2: LLM classification
        domain, confidence = await self._llm_classification(user_request)

        if confidence > 0.7:
            self.logger.info("domain_detected_by_llm", domain=domain, confidence=confidence)
            return domain, confidence

        # Uncertain - use generic
        self.logger.info("domain_uncertain_using_generic")
        return "generic", 0.5

    def _keyword_matching(self, user_request: str) -> tuple[str, float]:
        """Fast keyword-based domain detection."""
        request_lower = user_request.lower()

        # Web app keywords
        web_keywords = ["web app", "website", "frontend", "backend", "responsive", "html", "css", "react", "vue"]
        if any(kw in request_lower for kw in web_keywords):
            return "web_app", 0.8

        # Mobile app keywords
        mobile_keywords = ["mobile app", "ios", "android", "app store", "play store", "react native", "flutter"]
        if any(kw in request_lower for kw in mobile_keywords):
            return "mobile_app", 0.8

        # API keywords
        api_keywords = ["api", "rest", "graphql", "endpoint", "microservice", "backend service"]
        if any(kw in request_lower for kw in api_keywords):
            return "api_service", 0.8

        # CLI keywords
        cli_keywords = ["cli", "command line", "terminal", "console", "script"]
        if any(kw in request_lower for kw in cli_keywords):
            return "cli_tool", 0.8

        # Data pipeline keywords
        data_keywords = ["etl", "pipeline", "data processing", "batch job", "data warehouse", "kafka"]
        if any(kw in request_lower for kw in data_keywords):
            return "data_pipeline", 0.8

        return "generic", 0.3

    async def _llm_classification(self, user_request: str) -> tuple[str, float]:
        """LLM-based domain classification."""
        prompt = f"""
Classify this project request into one domain:

Request: "{user_request}"

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
        return result["domain"], result["confidence"]
```

### MaryOrchestrator Domain Requirements

**File**: `gao_dev/orchestrator/mary_orchestrator.py`

```python
class MaryOrchestrator:
    async def gather_domain_requirements(
        self,
        user_request: str,
        domain: str = "generic"
    ) -> DomainRequirements:
        """
        Gather domain-specific requirements using Epic 10 prompt system.

        Args:
            user_request: Original user request
            domain: Detected domain type

        Returns:
            DomainRequirements with domain-specific answers
        """

        # Load workflow metadata
        workflow = self.workflow_registry.load_workflow(
            "1-analysis/domain-requirements/workflow.yaml"
        )

        # Get prompt name for detected domain
        if domain in workflow.prompts:
            prompt_name = workflow.prompts[domain]
        else:
            # Fallback to generic clarification
            return await self.clarify_requirements(user_request)

        # Load prompt template (Epic 10 PromptLoader)
        template = self.prompt_loader.load_prompt(prompt_name)

        # Render prompt with variables (Epic 10 reference resolution)
        rendered = self.prompt_loader.render_prompt(template, {
            "user_request": user_request,
            "mary_persona": "@file:gao_dev/agents/mary.md",  # Auto-resolved
            "project_context": ""
        })

        # Create conversation session
        session = await self.conversation_manager.create_session(
            agent="Mary",
            workflow="domain-requirements",
            context={"domain": domain}
        )

        # Multi-turn conversation (~10-15 turns)
        requirements = {}
        for turn in range(15):
            # Generate next question
            mary_message = await self.analysis_service.analyze(
                rendered,
                conversation_history=session.messages,
                max_tokens=template.response.max_tokens,
                temperature=template.response.temperature
            )

            await session.add_message("mary", mary_message)

            # Check if gathering is complete
            if "synthesis" in mary_message.lower() or "summary" in mary_message.lower():
                break

            # Get user response
            user_response = await session.get_user_response()
            await session.add_message("user", user_response)

        # Extract requirements from conversation
        requirements_summary = await self._extract_requirements(session, domain)

        # Create domain requirements
        domain_reqs = DomainRequirements(
            domain=domain,
            user_request=user_request,
            requirements=requirements_summary,
            created_at=datetime.now()
        )

        # Save to .gao-dev/mary/domain-requirements/
        output_path = workflow.output_file.format(
            domain=domain,
            timestamp=datetime.now().isoformat()
        )
        await self._save_requirements(domain_reqs, output_path)

        return domain_reqs
```

---

## Testing Strategy

### Unit Tests (11+ tests)

**Test Prompt Rendering** (5 tests):
```python
def test_web_app_prompt_rendering():
    """Test web app domain prompt loads and renders correctly."""
    loader = PromptLoader(prompts_dir=Path("gao_dev/prompts"))
    template = loader.load_prompt("mary_domain_web_app")

    assert template.name == "mary_domain_web_app"
    assert "web application" in template.system_prompt.lower()

    rendered = loader.render_prompt(template, {
        "user_request": "Build a todo app",
        "mary_persona": "You are Mary"
    })

    assert "todo app" in rendered
    assert "You are Mary" in rendered
```

(Similar tests for: mobile_app, api_service, cli_tool, data_pipeline)

**Test Domain Detection** (4 tests):
```python
async def test_keyword_matching_web_app():
    """Test web app keyword detection."""
    brian = BrianOrchestrator(...)

    domain, confidence = await brian.detect_domain(
        "Build a web application with React"
    )

    assert domain == "web_app"
    assert confidence > 0.7

async def test_llm_classification_fallback():
    """Test LLM classification when keywords uncertain."""
    brian = BrianOrchestrator(...)

    domain, confidence = await brian.detect_domain(
        "I want to build something for users to track their habits"
    )

    # Should trigger LLM classification
    assert confidence > 0 or domain == "generic"
```

**Test Requirements Gathering** (2 tests):
```python
async def test_gather_domain_requirements():
    """Test domain-specific requirements gathering."""
    result = await orchestrator.gather_domain_requirements(
        user_request="Build a fitness tracking mobile app",
        domain="mobile_app"
    )

    assert isinstance(result, DomainRequirements)
    assert result.domain == "mobile_app"
    assert result.requirements
```

### Integration Tests (2 tests)

```python
async def test_brian_detects_domain_and_delegates_to_mary():
    """Test Brian detects domain and delegates to Mary."""
    brian = BrianOrchestrator(...)

    result = await brian.assess_and_select_workflows(
        "Build a REST API for user management"
    )

    assert result.detected_domain == "api_service"
    assert result.delegated_to == "Mary"
```

---

## Implementation Checklist

- [ ] Create workflow file: `workflows/1-analysis/domain-requirements/workflow.yaml`
- [ ] Create prompt: `prompts/agents/mary_domain_web_app.yaml`
- [ ] Create prompt: `prompts/agents/mary_domain_mobile_app.yaml`
- [ ] Create prompt: `prompts/agents/mary_domain_api_service.yaml`
- [ ] Create prompt: `prompts/agents/mary_domain_cli_tool.yaml`
- [ ] Create prompt: `prompts/agents/mary_domain_data_pipeline.yaml`
- [ ] Create data model: `core/models/domain_requirements.py`
- [ ] Add `detect_domain()` to BrianOrchestrator
- [ ] Add `_keyword_matching()` helper to BrianOrchestrator
- [ ] Add `_llm_classification()` helper to BrianOrchestrator
- [ ] Add `gather_domain_requirements()` to MaryOrchestrator
- [ ] Create tests: `tests/orchestrator/test_mary_domain_requirements.py`
- [ ] Run tests (11+ tests passing)
- [ ] Integration test: Domain detection → requirements gathering
- [ ] Performance validation: <200ms domain detection

---

## Definition of Done

- [ ] All 6 files created (1 workflow + 5 prompts)
- [ ] All prompts follow Epic 10 format
- [ ] Domain-specific questions embedded in prompts (15-20 per domain)
- [ ] BrianOrchestrator has domain detection (keyword + LLM)
- [ ] MaryOrchestrator uses PromptLoader
- [ ] 11+ tests passing (>90% coverage)
- [ ] Integration test passes
- [ ] Performance validated (<200ms detection)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No regressions in existing tests

---

**Status**: Todo
**Next Story**: Story 31.5 (Integration & Documentation)
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Epic 10 integration with embedded questions)
