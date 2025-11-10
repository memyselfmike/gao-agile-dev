# Story 31.5: Integration & Documentation

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.5
**Priority**: P0 (Critical - Final Integration)
**Estimate**: 5 story points
**Duration**: 2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Stories 31.1, 31.2, 31.3, 31.4, 31.6 (All previous stories)

---

## Story Description

Final integration, comprehensive testing, and documentation for Epic 31. Create 20+ integration tests covering all Mary workflows, write user guide, provide examples and demos, validate performance, and ensure all components work together seamlessly following Epic 10 prompt system integration.

This story confirms that Full Mary is production-ready, all workflows use Epic 10's PromptLoader pattern, and all 8 GAO-Dev agents are operational.

---

## User Story

**As a** developer and user
**I want** comprehensive tests, documentation, and examples
**So that** Mary's capabilities are reliable, discoverable, and easy to use

---

## Acceptance Criteria

### Testing
- [ ] 20+ integration tests covering all Mary workflows
- [ ] All tests verify Epic 10 prompt loading and rendering
- [ ] End-to-end test: Brian → Mary (all strategies) → PRD creation
- [ ] Performance validation (all targets met)
- [ ] Total test count: 60+ (14 from 31.1 + 16 from 31.2 + 13 from 31.3 + 11 from 31.4 + 6 from 31.6)

### Documentation
- [ ] User guide: "Working with Mary - Business Analyst" created
- [ ] 5+ examples demonstrating Mary's capabilities
- [ ] Demo script for showing Mary in action
- [ ] Epic 10 integration documented
- [ ] Prompt system usage explained

### Integration
- [ ] All 8 GAO-Dev agents confirmed operational
- [ ] All Mary workflows use PromptLoader
- [ ] All prompts use `@file:` and `{{variable}}` syntax
- [ ] Document lifecycle integration for Mary's outputs
- [ ] Epic 31 documentation updated (README, links)
- [ ] All story documentation reviewed and finalized

### Completion
- [ ] Git commit for Epic 31 merge
- [ ] No CSV dependencies (BMAD independence confirmed)
- [ ] All 24 prompts following Epic 10 format
- [ ] All 4 workflows following GAO-Dev patterns

---

## Files to Create/Modify

### New Files

- `tests/integration/test_mary_integration.py` (~400 LOC)
  - 20+ integration tests
  - Full workflow testing
  - Epic 10 prompt system validation
  - Performance validation

- `docs/features/interactive-brian-chat/USER_GUIDE_MARY.md` (~250 LOC)
  - How to use Mary
  - Workflow explanations
  - Epic 10 prompt system overview
  - Examples

- `docs/features/interactive-brian-chat/examples/mary-examples.md` (~200 LOC)
  - 5 complete examples
  - Vision elicitation example
  - Brainstorming example (SCAMPER)
  - Requirements analysis example
  - Domain-specific example (web app)
  - Full flow example

- `docs/features/interactive-brian-chat/DEMO_SCRIPT.md` (~100 LOC)
  - Demo walkthrough
  - Key talking points
  - Epic 10 highlights

### Modified Files

- `docs/features/interactive-brian-chat/README.md` (~60 LOC updated)
  - Add Epic 31 summary
  - Document Epic 10 integration
  - Update agent status (all 8 operational)
  - Add links to documentation

- `docs/bmm-workflow-status.md` (~30 LOC updated)
  - Mark Epic 31 complete
  - Update agent count
  - Add Epic 10 prompt system reference

---

## Integration Tests

**Location**: `tests/integration/test_mary_integration.py`

### Test Suite (20+ tests)

```python
"""Integration tests for Mary (Business Analyst) - Epic 31 with Epic 10."""

import pytest
from pathlib import Path

from gao_dev.orchestrator.brian_orchestrator import BrianOrchestrator
from gao_dev.orchestrator.mary_orchestrator import MaryOrchestrator, ClarificationStrategy
from gao_dev.core.prompt_loader import PromptLoader


class TestMaryVisionElicitation:
    """Test vision elicitation workflows (Story 31.1)."""

    @pytest.mark.asyncio
    async def test_vision_elicitation_full_flow(self, mary_orchestrator):
        """Test complete vision elicitation from vague request to vision summary."""
        result = await mary_orchestrator.elicit_vision(
            user_request="I want to build something for small teams"
        )

        assert result.vision_canvas is not None
        assert len(result.vision_canvas.key_features) >= 3
        assert result.file_path.exists()

    @pytest.mark.asyncio
    async def test_vision_canvas_prompt_loading(self, prompt_loader):
        """Test vision canvas prompt loads via Epic 10 PromptLoader."""
        template = prompt_loader.load_prompt("mary_vision_canvas")

        assert template.name == "mary_vision_canvas"
        assert "Vision Canvas" in template.system_prompt
        assert "mary_persona" in template.variables
        assert template.variables["mary_persona"] == "@file:gao_dev/agents/mary.md"

    @pytest.mark.asyncio
    async def test_vision_canvas_workflow(self, mary_orchestrator):
        """Test vision canvas workflow specifically."""
        result = await mary_orchestrator.elicit_vision(
            user_request="Team collaboration tool",
            technique="vision_canvas"
        )

        assert result.vision_canvas is not None
        assert result.vision_canvas.target_users
        assert result.vision_canvas.product_vision

    @pytest.mark.asyncio
    async def test_problem_solution_fit_workflow(self, mary_orchestrator):
        """Test problem-solution fit workflow."""
        result = await mary_orchestrator.elicit_vision(
            user_request="Better project management",
            technique="problem_solution_fit"
        )

        assert result.problem_solution_fit is not None

    @pytest.mark.asyncio
    async def test_vision_summary_to_prompt(self, mary_orchestrator):
        """Test vision summary converts to Brian-compatible prompt."""
        result = await mary_orchestrator.elicit_vision(
            user_request="Task management for developers"
        )

        prompt = result.to_prompt()
        assert "CLARIFIED VISION" in prompt
        assert len(prompt) > 100


class TestMaryBrainstorming:
    """Test brainstorming workflows (Story 31.2)."""

    @pytest.mark.asyncio
    async def test_brainstorming_technique_recommendation(self, mary_orchestrator):
        """Test technique recommendation based on goal."""
        techniques = await mary_orchestrator.recommend_techniques(
            topic="Authentication improvements",
            goal="innovation"
        )

        assert len(techniques) >= 2
        assert "scamper" in techniques or "whatif" in techniques

    @pytest.mark.asyncio
    async def test_scamper_prompt_loading(self, prompt_loader):
        """Test SCAMPER prompt loads via Epic 10 PromptLoader."""
        template = prompt_loader.load_prompt("mary_brainstorming_scamper")

        assert template.name == "mary_brainstorming_scamper"
        assert "SCAMPER" in template.system_prompt
        assert template.response.temperature == 0.8  # Creative facilitation

    @pytest.mark.asyncio
    async def test_scamper_facilitation(self, mary_orchestrator):
        """Test SCAMPER technique facilitation."""
        result = await mary_orchestrator.facilitate_brainstorming(
            user_request="User authentication",
            technique="scamper"
        )

        assert len(result.ideas_generated) > 0
        assert result.technique == "scamper"

    @pytest.mark.asyncio
    async def test_mind_map_generation(self, mary_orchestrator):
        """Test mind map generation from ideas."""
        result = await mary_orchestrator.facilitate_brainstorming(
            user_request="Authentication improvements",
            technique="scamper"
        )

        assert result.mind_map
        assert "graph TD" in result.mind_map
        assert "Authentication" in result.mind_map or "authentication" in result.mind_map

    @pytest.mark.asyncio
    async def test_brainstorming_insights_synthesis(self, mary_orchestrator):
        """Test insights synthesis from brainstorming."""
        result = await mary_orchestrator.facilitate_brainstorming(
            user_request="Better authentication"
        )

        assert result.key_themes
        assert result.quick_wins or result.long_term_opportunities


class TestMaryRequirementsAnalysis:
    """Test advanced requirements analysis (Story 31.3)."""

    @pytest.mark.asyncio
    async def test_moscow_prioritization(self, mary_orchestrator):
        """Test MoSCoW prioritization."""
        requirements = [
            "User login",
            "Dashboard",
            "Dark mode",
            "Export to PDF"
        ]

        result = await mary_orchestrator.analyze_requirements(
            requirements=requirements,
            timeline="3 months"
        )

        assert len(result.moscow) == 4
        assert any(r.category == "must" for r in result.moscow)

    @pytest.mark.asyncio
    async def test_moscow_prompt_loading(self, prompt_loader):
        """Test MoSCoW prompt loads via Epic 10 PromptLoader."""
        template = prompt_loader.load_prompt("mary_requirements_moscow")

        assert template.name == "mary_requirements_moscow"
        assert "MoSCoW" in template.system_prompt
        assert template.response.format == "json"

    @pytest.mark.asyncio
    async def test_kano_categorization(self, mary_orchestrator):
        """Test Kano model categorization."""
        requirements = [
            "Password reset",
            "Fast performance",
            "AI suggestions"
        ]

        result = await mary_orchestrator.analyze_requirements(requirements)

        assert len(result.kano) == 3

    @pytest.mark.asyncio
    async def test_dependency_mapping(self, mary_orchestrator):
        """Test dependency mapping."""
        requirements = [
            "User profile",
            "User login",
            "Password reset"
        ]

        result = await mary_orchestrator.analyze_requirements(requirements)

        assert result.dependencies
        # Profile likely depends on login
        if "User profile" in result.dependencies:
            assert len(result.dependencies["User profile"]) > 0

    @pytest.mark.asyncio
    async def test_risk_identification(self, mary_orchestrator):
        """Test risk identification."""
        requirements = [
            "Real-time collaboration",
            "Video conferencing",
            "AI-powered recommendations"
        ]

        result = await mary_orchestrator.analyze_requirements(
            requirements=requirements,
            timeline="2 months",
            team_size=2
        )

        assert len(result.risks) > 0
        assert any(r.category == "technical" for r in result.risks)

    @pytest.mark.asyncio
    async def test_complete_requirements_analysis(self, mary_orchestrator):
        """Test complete requirements analysis flow."""
        requirements = [
            "User authentication",
            "Dashboard with metrics",
            "Export to PDF",
            "Dark mode"
        ]

        result = await mary_orchestrator.analyze_requirements(
            requirements=requirements,
            project_context="SaaS web app",
            timeline="3 months",
            team_size=3
        )

        # All 5 analyses complete
        assert result.moscow
        assert result.kano
        assert result.dependencies
        assert result.risks
        assert result.constraints


class TestMaryDomainIntelligence:
    """Test domain-specific question libraries (Story 31.4)."""

    @pytest.mark.asyncio
    async def test_detect_web_app_domain(self, brian_orchestrator):
        """Test web app domain detection."""
        domain, confidence = await brian_orchestrator.detect_domain(
            "I want to build a web application for team collaboration"
        )

        assert domain == "web_app"
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_detect_mobile_app_domain(self, brian_orchestrator):
        """Test mobile app domain detection."""
        domain, confidence = await brian_orchestrator.detect_domain(
            "I need an iOS and Android app for fitness tracking"
        )

        assert domain == "mobile_app"
        assert confidence > 0.7

    @pytest.mark.asyncio
    async def test_web_app_prompt_loading(self, prompt_loader):
        """Test web app domain prompt loads via Epic 10 PromptLoader."""
        template = prompt_loader.load_prompt("mary_domain_web_app")

        assert template.name == "mary_domain_web_app"
        assert "web application" in template.system_prompt.lower()
        # Questions embedded in prompt
        assert "authentication" in template.user_prompt.lower()
        assert "responsive" in template.user_prompt.lower()

    @pytest.mark.asyncio
    async def test_gather_domain_requirements(self, mary_orchestrator):
        """Test domain-specific requirements gathering."""
        result = await mary_orchestrator.gather_domain_requirements(
            user_request="Build a fitness tracking mobile app",
            domain="mobile_app"
        )

        assert isinstance(result, DomainRequirements)
        assert result.domain == "mobile_app"
        assert result.requirements


class TestBrianMaryIntegration:
    """Test Brian → Mary delegation and integration."""

    @pytest.mark.asyncio
    async def test_brian_delegates_vague_request_to_mary(
        self,
        brian_orchestrator
    ):
        """Test Brian detects vagueness and delegates to Mary."""
        workflows = await brian_orchestrator.assess_and_select_workflows(
            "I want to build something"
        )

        assert workflows.mary_clarification_performed

    @pytest.mark.asyncio
    async def test_strategy_selection_based_on_vagueness(self, mary_orchestrator):
        """Test strategy selection for different vagueness levels."""
        # Very vague → vision elicitation
        strategy1 = await mary_orchestrator.select_clarification_strategy(
            "I want something",
            vagueness_score=0.9
        )
        assert strategy1 == ClarificationStrategy.VISION_ELICITATION

        # Moderately vague → brainstorming
        strategy2 = await mary_orchestrator.select_clarification_strategy(
            "I need better authentication",
            vagueness_score=0.75
        )
        assert strategy2 == ClarificationStrategy.BRAINSTORMING

        # Clear direction → advanced requirements
        strategy3 = await mary_orchestrator.select_clarification_strategy(
            "Build user login with email/password and 2FA",
            vagueness_score=0.65
        )
        assert strategy3 == ClarificationStrategy.ADVANCED_REQUIREMENTS

    @pytest.mark.asyncio
    async def test_brian_detects_domain_and_delegates(self, brian_orchestrator):
        """Test Brian detects domain and delegates to Mary."""
        result = await brian_orchestrator.assess_and_select_workflows(
            "Build a REST API for user management"
        )

        assert result.detected_domain in ["api_service", "web_app"]
        assert result.delegated_to == "Mary"


class TestEpic10Integration:
    """Test Epic 10 prompt system integration."""

    def test_all_mary_prompts_follow_epic10_format(self, prompt_loader):
        """Test all Mary prompts follow Epic 10 format."""
        mary_prompts = [
            # Vision (4)
            "mary_vision_canvas",
            "mary_vision_problem_solution_fit",
            "mary_vision_outcome_mapping",
            "mary_vision_5w1h",
            # Brainstorming (10)
            "mary_brainstorming_scamper",
            "mary_brainstorming_mindmap",
            "mary_brainstorming_whatif",
            "mary_brainstorming_first_principles",
            "mary_brainstorming_five_whys",
            "mary_brainstorming_yes_and",
            "mary_brainstorming_constraints",
            "mary_brainstorming_reversal",
            "mary_brainstorming_stakeholders",
            "mary_brainstorming_reverse",
            # Requirements (5)
            "mary_requirements_moscow",
            "mary_requirements_kano",
            "mary_requirements_dependency",
            "mary_requirements_risk",
            "mary_requirements_constraint",
            # Domain (5)
            "mary_domain_web_app",
            "mary_domain_mobile_app",
            "mary_domain_api_service",
            "mary_domain_cli_tool",
            "mary_domain_data_pipeline",
        ]

        for prompt_name in mary_prompts:
            template = prompt_loader.load_prompt(prompt_name)

            # Epic 10 format requirements
            assert template.name == prompt_name
            assert template.system_prompt
            assert template.user_prompt
            assert template.variables
            assert template.response
            assert template.metadata

            # Mary persona injection
            assert "mary_persona" in template.variables
            assert template.variables["mary_persona"] == "@file:gao_dev/agents/mary.md"

    def test_no_csv_dependencies(self):
        """Test that no CSV files are used for BMAD techniques."""
        import os
        from pathlib import Path

        # Check that orchestrator doesn't load CSV files
        mary_orchestrator_path = Path("gao_dev/orchestrator/mary_orchestrator.py")
        content = mary_orchestrator_path.read_text()

        assert ".csv" not in content
        assert "brain-methods.csv" not in content
        assert "adv-elicit-methods.csv" not in content


class TestPerformance:
    """Performance validation tests."""

    @pytest.mark.asyncio
    async def test_vision_elicitation_performance(self, mary_orchestrator):
        """Test vision elicitation completes in <3 minutes."""
        import time

        start = time.time()
        result = await mary_orchestrator.elicit_vision(
            "Project management tool"
        )
        duration = time.time() - start

        assert duration < 180  # 3 minutes

    @pytest.mark.asyncio
    async def test_domain_detection_performance(self, brian_orchestrator):
        """Test domain detection completes in <200ms."""
        import time

        start = time.time()
        domain, confidence = await brian_orchestrator.detect_domain(
            "Build a web app"
        )
        duration = time.time() - start

        assert duration < 0.2  # 200ms

    @pytest.mark.asyncio
    async def test_requirements_analysis_performance(self, mary_orchestrator):
        """Test requirements analysis completes in <2 minutes."""
        import time

        requirements = ["Login", "Dashboard", "Reports", "Admin panel"]

        start = time.time()
        result = await mary_orchestrator.analyze_requirements(requirements)
        duration = time.time() - start

        assert duration < 120  # 2 minutes

    @pytest.mark.asyncio
    async def test_prompt_loading_performance(self, prompt_loader):
        """Test prompt loading is fast (<10ms per prompt)."""
        import time

        prompt_names = [
            "mary_vision_canvas",
            "mary_brainstorming_scamper",
            "mary_requirements_moscow"
        ]

        for prompt_name in prompt_names:
            start = time.time()
            template = prompt_loader.load_prompt(prompt_name)
            duration = time.time() - start

            assert duration < 0.01  # 10ms
```

---

## User Guide

**Location**: `docs/features/interactive-brian-chat/USER_GUIDE_MARY.md`

```markdown
# User Guide: Working with Mary (Business Analyst)

**Version**: 1.0 (Epic 31 with Epic 10 Integration)
**Last Updated**: 2025-11-10

---

## Introduction

Mary is GAO-Dev's Business Analyst agent. She helps you clarify vague ideas, facilitate brainstorming sessions, analyze requirements, and ensure you build the right thing before writing code.

Mary uses conversational AI (not hardcoded scripts) to adapt to your needs, ask relevant questions, and guide you through proven business analysis techniques.

**Epic 10 Integration**: All Mary workflows use GAO-Dev's prompt system with `@file:` reference resolution and `{{variable}}` substitution. This means:
- Prompts are externalized to YAML files
- Easy to customize without code changes
- Plugin-friendly for domain-specific extensions

---

## When Mary Gets Involved

Mary automatically joins the conversation when Brian detects your request needs exploration:

- **Vagueness > 0.8**: Vision elicitation (20-30 min)
- **Vagueness 0.7-0.8**: Brainstorming (15-25 min)
- **Vagueness 0.6-0.7**: Advanced requirements analysis (1-2 min)
- **Vagueness < 0.6**: Basic clarification (5-10 min)

You can also explicitly request Mary:
```
> "Mary, can you help me brainstorm authentication ideas?"
> "I need help clarifying my vision"
> "Can we do a requirements analysis?"
```

---

## Mary's Capabilities

### 1. Vision Elicitation (Story 31.1)

**When to use**: You have a vague idea and need to articulate your vision.

**Techniques** (4 prompts):
- **Vision Canvas**: Target users, needs, vision, features, metrics, differentiators
- **Problem-Solution Fit**: Problem statement, current solutions, gaps, value prop
- **Outcome Mapping**: Desired outcomes, leading/lagging indicators, stakeholders
- **5W1H Analysis**: Who, What, When, Where, Why, How

**Example**:
```
You: "I want to build something for teams"
Brian: "This is quite vague. Let me bring in Mary..."
Mary: "Let's clarify your vision! First, who would use this?"
You: "Small development teams, 5-10 people"
Mary: "What problems are they experiencing?"
[... continues through vision canvas ...]
Mary: "Here's your vision summary: [summary]"
```

**Output**: Vision document saved to `.gao-dev/mary/vision-documents/`

### 2. Brainstorming Facilitation (Story 31.2)

**When to use**: You want to explore creative solutions and generate ideas.

**Techniques** (10 prompts):
- **SCAMPER**: Substitute, Combine, Adapt, Modify, Put, Eliminate, Reverse
- **Mind Mapping**: Visual organization and connections
- **What If Scenarios**: Explore radical possibilities
- **First Principles**: Strip assumptions, rebuild from truths
- **Five Whys**: Drill to root causes
- **Yes And Building**: Momentum through positive additions
- **Resource Constraints**: Force prioritization through limitations
- **Assumption Reversal**: Challenge and flip beliefs
- **Stakeholder Round Table**: Multiple perspectives
- **Reverse Engineering**: Work backwards from desired outcome

**Example**:
```
You: "I need ideas for better authentication"
Mary: "Let's brainstorm! I recommend SCAMPER technique. Ready?"
Mary: "S - SUBSTITUTE: What could you substitute passwords with?"
You: "Biometrics? Hardware keys?"
Mary: "Great! C - COMBINE: What if we combined biometrics with..."
[... continues through SCAMPER ...]
Mary: "You generated 12 ideas! Here's your mind map: [diagram]"
```

**Output**: Brainstorming summary with ideas, mind maps, insights saved to `.gao-dev/mary/brainstorming-sessions/`

### 3. Advanced Requirements Analysis (Story 31.3)

**When to use**: You have requirements but need prioritization and risk analysis.

**Analyses** (5 prompts):
- **MoSCoW Prioritization**: Must, Should, Could, Won't
- **Kano Model**: Basic, Performance, Excitement features
- **Dependency Mapping**: What depends on what
- **Risk Identification**: Technical, resource, timeline risks
- **Constraint Analysis**: Time, budget, technical, compliance

**Example**:
```
You: "Analyze these requirements: [list]"
Mary: "Let's prioritize using MoSCoW method..."
Mary: "MUST: User login, Dashboard"
Mary: "SHOULD: Dark mode, Export"
Mary: "COULD: AI suggestions"
[... continues with Kano, dependencies, risks ...]
```

**Output**: Requirements analysis report saved to `.gao-dev/mary/requirements-analysis/`

### 4. Domain-Specific Questions (Story 31.4)

**When to use**: Automatic - Mary asks domain-relevant questions.

**Domains** (5 prompts):
- **Web App**: Responsive design, SEO, hosting, authentication (20 questions)
- **Mobile App**: iOS/Android, offline mode, push notifications (18 questions)
- **API Service**: REST/GraphQL, authentication, rate limiting (17 questions)
- **CLI Tool**: Commands, configuration, output formats (15 questions)
- **Data Pipeline**: ETL, scheduling, error handling, monitoring (19 questions)

**Example**:
```
You: "Build a mobile fitness app"
Mary: [Detects mobile_app domain]
Mary: "iOS, Android, or both?"
Mary: "Will users need offline access to workouts?"
Mary: "Push notifications for workout reminders?"
[... domain-specific questions embedded in prompt ...]
```

---

## Epic 10 Prompt System

All Mary workflows use GAO-Dev's Epic 10 prompt system:

**Workflow Files** (metadata only):
- `workflows/1-analysis/vision-elicitation/workflow.yaml`
- `workflows/1-analysis/brainstorming/workflow.yaml`
- `workflows/1-analysis/requirements-analysis/workflow.yaml`
- `workflows/1-analysis/domain-requirements/workflow.yaml`

**Prompt Files** (LLM instructions):
- 24 total prompts in `prompts/agents/mary_*.yaml`
- All use `@file:gao_dev/agents/mary.md` for persona injection
- All use `{{variable}}` syntax for variable substitution
- All follow Epic 10 format: system_prompt, user_prompt, variables, response, metadata

**Benefits**:
- Prompts externalized (no code changes needed)
- Easy to customize per project
- Plugin-friendly for domain-specific extensions

---

## Tips for Working with Mary

1. **Be open and exploratory**: Mary thrives in open-ended conversations
2. **Build on ideas**: Mary uses "Yes, and..." - you can too
3. **Ask for technique changes**: "Can we try a different brainstorming technique?"
4. **Save checkpoints**: Long sessions auto-save, you can resume later
5. **Review outputs**: Mary saves everything to `.gao-dev/mary/` - review and refine

---

## Performance & Limits

- **Vision Elicitation**: 20-30 minutes (user-paced)
- **Brainstorming Session**: 15-25 minutes (user-paced)
- **Requirements Analysis**: 1-2 minutes (automated)
- **Domain Detection**: <200ms (keyword + LLM)
- **Prompt Loading**: <10ms per prompt (Epic 10 caching)
- **Session Timeout**: 1 hour (auto-checkpoint)

---

## Troubleshooting

**Issue**: Mary asks questions I already answered
**Solution**: Mary builds on conversation history - review and clarify if needed

**Issue**: Wrong domain detected
**Solution**: Explicitly state domain: "This is a CLI tool..."

**Issue**: Too many questions
**Solution**: "Mary, I have enough clarity now" or "Skip to summary"

**Issue**: Want to customize prompts
**Solution**: Edit YAML files in `gao_dev/prompts/agents/mary_*.yaml`

---

## Next Steps After Mary

After Mary completes clarification:
1. **Vision Summary** → John creates PRD
2. **Brainstorming Output** → Inform feature prioritization
3. **Requirements Analysis** → Winston creates architecture
4. **All outputs** → Stored in `.gao-dev/mary/` for reference

---

**Questions?** Type `help mary` in the chat or see examples in `examples/mary-examples.md`
```

---

## Definition of Done

- [ ] 20+ integration tests passing
- [ ] All tests verify Epic 10 prompt system integration
- [ ] User guide created and comprehensive
- [ ] 5+ examples documented
- [ ] Demo script created
- [ ] All performance targets validated
- [ ] All 8 GAO-Dev agents confirmed operational
- [ ] End-to-end test successful
- [ ] All Mary workflows use PromptLoader
- [ ] All prompts use `@file:` and `{{variable}}` syntax
- [ ] No CSV dependencies (BMAD independence confirmed)
- [ ] Document lifecycle integration verified
- [ ] Documentation updated (README, bmm-workflow-status.md)
- [ ] Code review complete
- [ ] Total test count: 60+ tests
- [ ] Git commit: `feat(epic-31): Story 31.5 - Integration & Documentation (5 pts)`
- [ ] Epic 31 merge commit: `feat(epic-31): Full Mary Integration with Epic 10 - Complete (28 pts)`

---

## Manual Testing Checklist

- [ ] Vision elicitation: Complete flow, summary saved, Epic 10 prompts loaded
- [ ] Brainstorming: SCAMPER technique, mind map generated, Epic 10 prompts loaded
- [ ] Requirements analysis: MoSCoW + Kano + risks, Epic 10 prompts loaded
- [ ] Domain detection: Test all 5 domains with keyword + LLM
- [ ] Brian → Mary delegation: Vague request triggers Mary
- [ ] Full flow: Vague idea → Mary → clarified → Brian → PRD
- [ ] Performance: All operations within target times
- [ ] All 8 agents: Verify complete agent roster
- [ ] Prompt system: Verify `@file:` resolution and `{{variable}}` substitution
- [ ] No CSV loading: Confirm no BMAD CSV dependencies

---

## Test Count Summary

**Total: 60+ tests across Epic 31**

- Story 31.1 (Vision Elicitation): 14 tests
- Story 31.2 (Brainstorming): 16 tests
- Story 31.3 (Requirements Analysis): 13 tests
- Story 31.4 (Domain Requirements): 11 tests
- Story 31.5 (Integration): 20+ tests
- Story 31.6 (Mary → John Handoff): 6 tests

**Coverage**:
- All 24 Mary prompts tested
- All 4 Mary workflows tested
- Epic 10 integration validated
- Performance validated
- End-to-end flows validated

---

## Next Steps

After Epic 31 complete:
- **Epic 32**: Mary → John handoff automation enhancements (optional)
- **Epic 33**: Additional brainstorming techniques (optional)
- **Production**: Full Mary deployed and operational with all 8 agents

---

**Status**: Todo
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Epic 10 integration, 60+ test count)
