# Story 31.1: Vision Elicitation Workflows & Prompts

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.1
**Priority**: P0 (Critical - Vision Elicitation Foundation)
**Estimate**: 5 story points
**Duration**: 1-2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 30.8 (Minimal Mary Integration), Epic 10 (Prompt Management System)

---

## Story Description

Implement vision elicitation workflows and prompts that help users articulate vague ideas into clear product visions. This enhances Mary beyond basic clarification (Epic 30) by adding structured techniques for vision discovery: vision canvas, problem-solution fit, outcome mapping, and 5W1H analysis.

**Epic 10 Integration**: Following GAO-Dev's established pattern, we separate:
- **Workflow** (metadata only) → `gao_dev/workflows/1-analysis/vision-elicitation/workflow.yaml`
- **Prompts** (LLM instructions) → `gao_dev/prompts/agents/mary_vision_*.yaml` (4 files)

Users with very vague requests ("I want to build something for teams") will receive guided vision elicitation that uncovers their true intent, target users, problem being solved, and success criteria.

---

## User Story

**As a** user with a vague idea
**I want** Mary to help me articulate my vision clearly using structured techniques
**So that** we create a well-defined product vision before building anything

---

## Acceptance Criteria

### Workflows & Prompts
- [ ] Workflow file created: `gao_dev/workflows/1-analysis/vision-elicitation/workflow.yaml` (metadata only)
- [ ] 4 prompt files created in `gao_dev/prompts/agents/`:
  - [ ] `mary_vision_canvas.yaml` (vision canvas LLM instructions)
  - [ ] `mary_vision_problem_solution_fit.yaml` (problem-solution fit)
  - [ ] `mary_vision_outcome_mapping.yaml` (outcome mapping)
  - [ ] `mary_vision_5w1h.yaml` (5W1H analysis)
- [ ] All prompts follow Epic 10 format (system_prompt, user_prompt, variables, response, metadata)
- [ ] All prompts use `@file:gao_dev/agents/mary.md` for persona injection
- [ ] All prompts use `{{variable}}` syntax for substitution

### Code Implementation
- [ ] MaryOrchestrator enhanced with `elicit_vision()` method
- [ ] MaryOrchestrator uses PromptLoader (Epic 10) to load prompts
- [ ] Strategy selection logic: vagueness > 0.8 triggers vision elicitation
- [ ] VisionSummary data model implemented
- [ ] Vision documents saved to `.gao-dev/mary/vision-documents/`
- [ ] Vision summary indexed in documents.db

### Integration
- [ ] Brian successfully delegates to Mary for vision elicitation
- [ ] Mary selects appropriate vision workflow based on context
- [ ] Vision summary handed back to Brian for workflow selection

### Testing
- [ ] 14+ unit tests passing (4 prompts × 3 tests + 2 orchestrator tests)
- [ ] Integration test: vague request → vision elicitation → clear vision summary
- [ ] Performance: Full vision elicitation completes in <20 minutes (reduced scope)

---

## Files to Create/Modify

### New Files

**Workflow (Metadata)**:
- `gao_dev/workflows/1-analysis/vision-elicitation/workflow.yaml` (~50 LOC)
  - Metadata for all 4 vision techniques
  - Variable definitions
  - Prompt references (not embedded instructions!)

**Prompts (LLM Instructions)**:
- `gao_dev/prompts/agents/mary_vision_canvas.yaml` (~90 LOC)
  - System prompt with Mary's persona and vision canvas framework
  - User prompt with 6-step facilitation (target users, user needs, vision, features, metrics, differentiators)
  - Variables: `mary_persona`, `user_request`, `project_context`
  - Response config: max_tokens, temperature

- `gao_dev/prompts/agents/mary_vision_problem_solution_fit.yaml` (~80 LOC)
  - System prompt with problem-solution fit framework
  - User prompt with 5-step facilitation (problem, current solutions, gaps, proposed solution, value proposition)

- `gao_dev/prompts/agents/mary_vision_outcome_mapping.yaml` (~80 LOC)
  - System prompt with outcome mapping framework
  - User prompt with 4-step facilitation (desired outcomes, leading indicators, lagging indicators, stakeholders)

- `gao_dev/prompts/agents/mary_vision_5w1h.yaml` (~80 LOC)
  - System prompt with 5W1H framework
  - User prompt with 6 questions (Who, What, When, Where, Why, How)

**Data Models**:
- `gao_dev/core/models/vision_summary.py` (~120 LOC)
  - VisionSummary dataclass
  - VisionCanvas, ProblemSolutionFit, OutcomeMap, FiveWOneH dataclasses
  - to_prompt() method for handing to Brian
  - to_markdown() method for file output

**Tests**:
- `tests/orchestrator/test_mary_vision_elicitation.py` (~200 LOC)
  - Test each of 4 prompts (prompt rendering, variable resolution)
  - Test VisionSummary generation
  - Test strategy selection (when to use vision elicitation)
  - Integration test: end-to-end vision elicitation flow

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~100 LOC modified/added)
  - Add `elicit_vision()` method
  - Use PromptLoader to load vision prompts
  - Use ConversationManager for multi-turn dialogue
  - Generate VisionSummary from conversation
  - Save to `.gao-dev/mary/vision-documents/`

- `gao_dev/orchestrator/brian_orchestrator.py` (~20 LOC modified)
  - Update delegation logic to handle vision elicitation strategy
  - Pass VisionSummary back to workflow selection

---

## Technical Design

### Architecture Overview

```
User: "I want to build something for teams"
  ↓
BrianOrchestrator.assess_vagueness() → 0.85 (very vague!)
  ↓
BrianOrchestrator delegates to Mary
  ↓
MaryOrchestrator.select_clarification_strategy() → VISION_ELICITATION
  ↓
MaryOrchestrator.elicit_vision()
  ├─ Load workflow: "vision-elicitation/workflow.yaml"
  ├─ Select technique: "vision_canvas" (default for greenfield)
  ├─ Load prompt: "mary_vision_canvas" (via PromptLoader)
  ├─ Render prompt with variables
  ├─ Create ConversationSession
  ├─ Multi-turn facilitation (~15-20 turns)
  ├─ Generate VisionSummary
  └─ Save to .gao-dev/mary/vision-documents/vision-{timestamp}.md
  ↓
Return VisionSummary to Brian
  ↓
Brian uses clarified vision for workflow selection
```

### Workflow File (Metadata Only)

**File**: `gao_dev/workflows/1-analysis/vision-elicitation/workflow.yaml`

```yaml
name: vision-elicitation
description: Elicit product vision through structured discovery
phase: 1
author: Mary (Business Analyst)
non_interactive: false
autonomous: false
iterative: true

variables:
  user_request:
    description: Original vague request
    type: string
    required: true

  technique:
    description: Vision elicitation technique to use
    type: string
    required: true
    allowed_values:
      - vision_canvas
      - problem_solution_fit
      - outcome_mapping
      - 5w1h

  project_context:
    description: Optional project context
    type: string
    default: ""

required_tools:
  - conversation_manager
  - analysis_service

output_file: ".gao-dev/mary/vision-documents/vision-{{technique}}-{{timestamp}}.md"

# Reference prompts by name (Epic 10 pattern)
prompts:
  vision_canvas: "mary_vision_canvas"
  problem_solution_fit: "mary_vision_problem_solution_fit"
  outcome_mapping: "mary_vision_outcome_mapping"
  5w1h: "mary_vision_5w1h"

metadata:
  category: vision_elicitation
  domain: business_analysis
  techniques_available: 4
  typical_duration: 15-20  # minutes
```

### Prompt File Example: Vision Canvas

**File**: `gao_dev/prompts/agents/mary_vision_canvas.yaml`

```yaml
name: mary_vision_canvas
description: "Mary facilitates vision canvas elicitation"
version: 1.0.0

system_prompt: |
  You are Mary, a Business Analyst helping users articulate their product vision through the Vision Canvas framework.

  {{mary_persona}}

  **Vision Canvas Framework**:
  The Vision Canvas is a structured approach to defining product vision across 6 dimensions:

  1. **Target Users**: Who will use this product?
  2. **User Needs**: What problems or needs do users have?
  3. **Product Vision**: What is your vision for solving these needs?
  4. **Key Features**: What are the 3-5 most important capabilities?
  5. **Success Metrics**: How will you measure success?
  6. **Differentiators**: What makes this better than alternatives?

  **Your Facilitation Style**:
  - Start broad, get progressively more specific
  - Ask open-ended questions to encourage elaboration
  - Build on user's answers with follow-up questions
  - Help them see connections between their answers
  - Be encouraging and curious, not interrogative
  - Use "Yes, and..." to validate and expand
  - Make it feel like a collaborative conversation

user_prompt: |
  Let's create a vision canvas for: {{user_request}}

  **Session Structure** (15-20 turns, ~15-20 minutes):

  1. **Introduction** (1 turn):
     - Welcome and explain the Vision Canvas briefly
     - Set expectations: 6 areas, takes 15-20 minutes
     - Start with the first area

  2. **Target Users** (2-3 turns):
     - Ask: "Who are your target users for {{user_request}}?"
     - Follow-up: "What's their role and context?"
     - Follow-up: "What's their technical level or expertise?"
     - Capture their answers

  3. **User Needs** (2-3 turns):
     - Ask: "What problems or needs do these users have?"
     - Follow-up: "What are their current pain points?"
     - Follow-up: "What jobs are they trying to get done?"
     - Capture their answers

  4. **Product Vision** (2-3 turns):
     - Ask: "What's your vision for solving these needs?"
     - Follow-up: "Can you give me a one-sentence vision statement?"
     - Follow-up: "What makes this unique? Why now?"
     - Capture their answers

  5. **Key Features** (2-3 turns):
     - Ask: "What are the 3-5 most important features?"
     - Follow-up: "What must it do? What's core vs nice-to-have?"
     - Follow-up: "What differentiates these features?"
     - Capture their answers

  6. **Success Metrics** (2-3 turns):
     - Ask: "How will you measure success?"
     - Follow-up: "What user adoption metrics matter?"
     - Follow-up: "What business or quality metrics?"
     - Capture their answers

  7. **Differentiators** (2-3 turns):
     - Ask: "What makes this better than existing alternatives?"
     - Follow-up: "What's your unique value proposition?"
     - Capture their answers

  8. **Synthesis** (2 turns):
     - Summarize all 6 areas
     - Ask: "Does this capture your vision? Anything to adjust?"
     - Generate final vision canvas summary

  **Important**:
  - Adapt pacing to user's responses (don't rush if they're thinking deeply)
  - If an area isn't generating ideas, ask from different angle or move on
  - Keep it conversational - you're a colleague, not following a script
  - Use their language and examples

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"  # Epic 10 reference resolution
  user_request: ""
  project_context: ""

response:
  max_tokens: 1024
  temperature: 0.7
  format: text

metadata:
  category: vision_elicitation
  agent: mary
  phase: 1
  technique: vision_canvas
  technique_type: structured
  typical_duration: 15-20
  best_for: "Greenfield projects needing comprehensive vision"
  original_source: "BMAD vision canvas (adapted for GAO-Dev)"
```

### MaryOrchestrator Implementation

**File**: `gao_dev/orchestrator/mary_orchestrator.py`

```python
class MaryOrchestrator:
    def __init__(
        self,
        prompt_loader: PromptLoader,  # Epic 10
        conversation_manager: ConversationManager,
        analysis_service: AIAnalysisService,
        workflow_registry: WorkflowRegistry
    ):
        self.prompt_loader = prompt_loader
        self.conversation_manager = conversation_manager
        self.analysis_service = analysis_service
        self.workflow_registry = workflow_registry

    async def elicit_vision(
        self,
        user_request: str,
        technique: str = "vision_canvas"
    ) -> VisionSummary:
        """
        Elicit product vision through guided discovery.

        Args:
            user_request: Original vague request
            technique: Vision technique to use (vision_canvas, problem_solution_fit, etc.)

        Returns:
            VisionSummary with clarified vision
        """

        # Load workflow metadata
        workflow = self.workflow_registry.load_workflow(
            "1-analysis/vision-elicitation/workflow.yaml"
        )

        # Get prompt name for selected technique
        prompt_name = workflow.prompts[technique]

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
            workflow="vision-elicitation",
            context={"technique": technique}
        )

        # Multi-turn facilitation (~15-20 turns)
        async for turn in range(20):
            # Generate next facilitation message
            mary_message = await self.analysis_service.analyze(
                rendered,
                conversation_history=session.messages,
                max_tokens=template.response.max_tokens,
                temperature=template.response.temperature
            )

            await session.add_message("mary", mary_message)

            # Get user response
            user_response = await session.get_user_response()
            await session.add_message("user", user_response)

        # Generate VisionSummary from conversation
        vision_summary = await self._synthesize_vision(session, technique)

        # Save to .gao-dev/mary/vision-documents/
        output_path = workflow.output_file.format(
            technique=technique,
            timestamp=datetime.now().isoformat()
        )
        await self._save_vision(vision_summary, output_path)

        return vision_summary
```

---

## Testing Strategy

### Unit Tests (14+ tests)

**Test Prompt Rendering** (4 tests):
```python
def test_vision_canvas_prompt_rendering():
    """Test vision canvas prompt loads and renders correctly."""
    loader = PromptLoader(prompts_dir=Path("gao_dev/prompts"))
    template = loader.load_prompt("mary_vision_canvas")

    assert template.name == "mary_vision_canvas"
    assert "Vision Canvas" in template.system_prompt

    rendered = loader.render_prompt(template, {
        "user_request": "Build a todo app",
        "mary_persona": "You are Mary"
    })

    assert "Build a todo app" in rendered
    assert "You are Mary" in rendered
```

(Similar tests for: problem_solution_fit, outcome_mapping, 5w1h)

**Test Strategy Selection** (2 tests):
```python
async def test_select_vision_elicitation_strategy():
    """Test that high vagueness triggers vision elicitation."""
    orchestrator = MaryOrchestrator(...)

    strategy = await orchestrator.select_clarification_strategy(
        "I want to build something",
        vagueness_score=0.9
    )

    assert strategy == ClarificationStrategy.VISION_ELICITATION
```

**Test VisionSummary Generation** (4 tests):
```python
async def test_generate_vision_canvas_summary():
    """Test vision canvas summary generation."""
    session = create_mock_session_with_vision_canvas_responses()

    summary = await orchestrator._synthesize_vision(session, "vision_canvas")

    assert isinstance(summary, VisionSummary)
    assert summary.vision_canvas.target_users
    assert summary.vision_canvas.product_vision
```

### Integration Tests (2 tests)

```python
async def test_end_to_end_vision_elicitation():
    """Test complete vision elicitation flow."""
    brian = BrianOrchestrator(...)

    # Vague request
    result = await brian.assess_and_select_workflows(
        "I want to build something for teams"
    )

    # Should delegate to Mary
    assert result.delegated_to == "Mary"
    assert result.mary_strategy == "vision_elicitation"

    # Mary completes vision elicitation
    vision_summary = result.mary_output

    assert vision_summary.vision_canvas.target_users
    assert vision_summary.file_path.exists()
```

---

## Implementation Checklist

- [ ] Create workflow file: `workflows/1-analysis/vision-elicitation/workflow.yaml`
- [ ] Create prompt: `prompts/agents/mary_vision_canvas.yaml`
- [ ] Create prompt: `prompts/agents/mary_vision_problem_solution_fit.yaml`
- [ ] Create prompt: `prompts/agents/mary_vision_outcome_mapping.yaml`
- [ ] Create prompt: `prompts/agents/mary_vision_5w1h.yaml`
- [ ] Create data model: `core/models/vision_summary.py`
- [ ] Enhance MaryOrchestrator with `elicit_vision()` method
- [ ] Update BrianOrchestrator delegation logic
- [ ] Create tests: `tests/orchestrator/test_mary_vision_elicitation.py`
- [ ] Run tests (14+ tests passing)
- [ ] Integration test: End-to-end vision elicitation
- [ ] Performance validation: <20 minutes per session

---

## Definition of Done

- [ ] All 5 files created (1 workflow + 4 prompts)
- [ ] All prompts follow Epic 10 format
- [ ] MaryOrchestrator uses PromptLoader
- [ ] 14+ tests passing (>90% coverage)
- [ ] Integration test passes
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No regressions in existing tests

---

**Status**: Todo
**Next Story**: Story 31.2 (Brainstorming & Mind Mapping)
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Epic 10 integration)
