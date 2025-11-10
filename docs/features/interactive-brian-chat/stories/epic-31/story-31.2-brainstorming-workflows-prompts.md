# Story 31.2: Brainstorming Workflows & Prompts

**Epic**: Epic 31 - Full Mary (Business Analyst) Integration
**Story ID**: 31.2
**Priority**: P0 (Critical - Brainstorming Core Capability)
**Estimate**: 5 story points
**Duration**: 2 days
**Owner**: Amelia (Developer)
**Status**: Todo
**Dependencies**: Story 31.1 (Vision Elicitation Workflows)

---

## Story Description

Implement brainstorming facilitation workflows and prompts that help users explore solutions creatively using 10 proven techniques from BMAD library. This enhances Mary beyond vision elicitation by adding structured brainstorming capabilities: SCAMPER, mind mapping, what-if scenarios, first principles thinking, and more.

**Epic 10 Integration**: Following GAO-Dev's established pattern, we separate:
- **Workflow** (metadata only) → `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml`
- **Prompts** (LLM instructions) → `gao_dev/prompts/agents/mary_brainstorming_*.yaml` (10 files)

Users exploring solutions will receive guided brainstorming facilitation that generates ideas, creates mind maps, and synthesizes insights into actionable recommendations.

---

## User Story

**As a** user exploring solutions
**I want** Mary to facilitate brainstorming sessions with multiple structured techniques
**So that** we explore creative approaches and identify the best solutions

---

## Acceptance Criteria

### Workflows & Prompts
- [ ] Workflow file created: `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml` (metadata only)
- [ ] 10 prompt files created in `gao_dev/prompts/agents/`:
  - [ ] `mary_brainstorming_scamper.yaml` (SCAMPER technique)
  - [ ] `mary_brainstorming_mindmap.yaml` (Mind mapping)
  - [ ] `mary_brainstorming_whatif.yaml` (What-if scenarios)
  - [ ] `mary_brainstorming_first_principles.yaml` (First principles thinking)
  - [ ] `mary_brainstorming_five_whys.yaml` (Five whys)
  - [ ] `mary_brainstorming_yes_and.yaml` (Yes and building)
  - [ ] `mary_brainstorming_constraints.yaml` (Resource constraints)
  - [ ] `mary_brainstorming_reversal.yaml` (Assumption reversal)
  - [ ] `mary_brainstorming_stakeholders.yaml` (Stakeholder round table)
  - [ ] `mary_brainstorming_reverse.yaml` (Reverse engineering)
- [ ] All prompts follow Epic 10 format (system_prompt, user_prompt, variables, response, metadata)
- [ ] All prompts use `@file:gao_dev/agents/mary.md` for persona injection
- [ ] All prompts use `{{variable}}` syntax for substitution

### Code Implementation
- [ ] MaryOrchestrator enhanced with `facilitate_brainstorming()` method
- [ ] MaryOrchestrator uses PromptLoader (Epic 10) to load prompts
- [ ] Technique recommendation logic: goal + context → 2-3 recommended techniques
- [ ] BrainstormingSummary data model implemented
- [ ] Mind map generation (mermaid syntax)
- [ ] Insights synthesis (themes, quick wins, long-term opportunities)
- [ ] Brainstorming outputs saved to `.gao-dev/mary/brainstorming-sessions/`
- [ ] Session summary indexed in documents.db

### Integration
- [ ] Brian successfully delegates to Mary for brainstorming
- [ ] Mary selects appropriate brainstorming technique based on goal
- [ ] Brainstorming summary handed back to Brian for workflow selection

### Testing
- [ ] 16+ unit tests passing (10 prompts × 1.5 tests + 1 orchestrator test)
- [ ] Integration test: brainstorming request → technique selection → session → summary
- [ ] Performance: Technique recommendation <500ms, Mind map generation <5 sec

---

## Files to Create/Modify

### New Files

**Workflow (Metadata)**:
- `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml` (~70 LOC)
  - Metadata for all 10 brainstorming techniques
  - Variable definitions
  - Prompt references (not embedded instructions!)

**Prompts (LLM Instructions)**:
- `gao_dev/prompts/agents/mary_brainstorming_scamper.yaml` (~120 LOC)
  - System prompt with Mary's persona and SCAMPER framework
  - User prompt with 7-step facilitation (Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse)
  - Variables: `mary_persona`, `brainstorming_topic`, `session_duration`
  - Response config: max_tokens, temperature

- `gao_dev/prompts/agents/mary_brainstorming_mindmap.yaml` (~90 LOC)
  - System prompt with mind mapping framework
  - User prompt with visual organization facilitation

- `gao_dev/prompts/agents/mary_brainstorming_whatif.yaml` (~90 LOC)
  - System prompt with what-if scenario framework
  - User prompt for exploring radical possibilities

- `gao_dev/prompts/agents/mary_brainstorming_first_principles.yaml` (~90 LOC)
  - System prompt with first principles thinking framework
  - User prompt for stripping assumptions and rebuilding from truths

- `gao_dev/prompts/agents/mary_brainstorming_five_whys.yaml` (~90 LOC)
  - System prompt with five whys framework
  - User prompt for drilling to root causes

- `gao_dev/prompts/agents/mary_brainstorming_yes_and.yaml` (~90 LOC)
  - System prompt with yes-and building framework
  - User prompt for team momentum through positive additions

- `gao_dev/prompts/agents/mary_brainstorming_constraints.yaml` (~90 LOC)
  - System prompt with resource constraints framework
  - User prompt for forcing prioritization through limitations

- `gao_dev/prompts/agents/mary_brainstorming_reversal.yaml` (~90 LOC)
  - System prompt with assumption reversal framework
  - User prompt for challenging and flipping beliefs

- `gao_dev/prompts/agents/mary_brainstorming_stakeholders.yaml` (~90 LOC)
  - System prompt with stakeholder round table framework
  - User prompt for gathering multiple perspectives

- `gao_dev/prompts/agents/mary_brainstorming_reverse.yaml` (~90 LOC)
  - System prompt with reverse engineering framework
  - User prompt for working backwards from desired outcome

**Data Models**:
- `gao_dev/core/models/brainstorming_summary.py` (~150 LOC)
  - BrainstormingSummary dataclass
  - Idea dataclass
  - to_markdown() method for file output
  - to_prompt() method for handing to Brian

**Tests**:
- `tests/orchestrator/test_mary_brainstorming.py` (~250 LOC)
  - Test each of 10 prompts (prompt rendering, variable resolution)
  - Test technique recommendation logic
  - Test mind map generation
  - Test insights synthesis
  - Integration test: end-to-end brainstorming flow

### Modified Files

- `gao_dev/orchestrator/mary_orchestrator.py` (~120 LOC modified/added)
  - Add `facilitate_brainstorming()` method
  - Add `recommend_techniques()` method
  - Use PromptLoader to load brainstorming prompts
  - Use ConversationManager for multi-turn dialogue
  - Generate BrainstormingSummary from conversation
  - Generate mind map (mermaid syntax)
  - Synthesize insights (themes, quick wins, long-term)
  - Save to `.gao-dev/mary/brainstorming-sessions/`

- `gao_dev/orchestrator/brian_orchestrator.py` (~20 LOC modified)
  - Update delegation logic to handle brainstorming strategy
  - Pass BrainstormingSummary back to workflow selection

---

## Technical Design

### Architecture Overview

```
User: "I need ideas for improving authentication"
  ↓
BrianOrchestrator.assess_vagueness() → 0.75 (moderately vague)
  ↓
BrianOrchestrator delegates to Mary
  ↓
MaryOrchestrator.select_clarification_strategy() → BRAINSTORMING
  ↓
MaryOrchestrator.recommend_techniques(goal="innovation") → ["scamper", "whatif", "first_principles"]
  ↓
User selects: "scamper"
  ↓
MaryOrchestrator.facilitate_brainstorming()
  ├─ Load workflow: "brainstorming/workflow.yaml"
  ├─ Load prompt: "mary_brainstorming_scamper" (via PromptLoader)
  ├─ Render prompt with variables
  ├─ Create ConversationSession
  ├─ Multi-turn facilitation (~15-20 turns)
  ├─ Generate mind map (mermaid syntax)
  ├─ Synthesize insights (themes, quick wins, long-term)
  └─ Save to .gao-dev/mary/brainstorming-sessions/scamper-{timestamp}.md
  ↓
Return BrainstormingSummary to Brian
  ↓
Brian uses insights for workflow selection
```

### Workflow File (Metadata Only)

**File**: `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml`

```yaml
name: brainstorming
description: Facilitate brainstorming sessions with multiple techniques
phase: 1
author: Mary (Business Analyst)
non_interactive: false
autonomous: false
iterative: true

variables:
  brainstorming_topic:
    description: Topic to brainstorm about
    type: string
    required: true

  technique:
    description: Brainstorming technique to use
    type: string
    required: true
    allowed_values:
      - scamper
      - mindmap
      - whatif
      - first_principles
      - five_whys
      - yes_and
      - constraints
      - reversal
      - stakeholders
      - reverse

  goal:
    description: Brainstorming goal
    type: string
    default: "exploration"
    allowed_values:
      - innovation
      - problem_solving
      - strategic_planning
      - exploration

  session_duration:
    description: Target session duration in minutes
    type: integer
    default: 20

required_tools:
  - conversation_manager
  - analysis_service

output_file: ".gao-dev/mary/brainstorming-sessions/{{technique}}-{{timestamp}}.md"

# Reference prompts by name (Epic 10 pattern)
prompts:
  scamper: "mary_brainstorming_scamper"
  mindmap: "mary_brainstorming_mindmap"
  whatif: "mary_brainstorming_whatif"
  first_principles: "mary_brainstorming_first_principles"
  five_whys: "mary_brainstorming_five_whys"
  yes_and: "mary_brainstorming_yes_and"
  constraints: "mary_brainstorming_constraints"
  reversal: "mary_brainstorming_reversal"
  stakeholders: "mary_brainstorming_stakeholders"
  reverse: "mary_brainstorming_reverse"

metadata:
  category: brainstorming
  domain: business_analysis
  techniques_available: 10
  typical_duration: 15-25  # minutes
```

### Prompt File Example: SCAMPER

**File**: `gao_dev/prompts/agents/mary_brainstorming_scamper.yaml`

```yaml
name: mary_brainstorming_scamper
description: "Mary facilitates SCAMPER brainstorming technique"
version: 1.0.0

system_prompt: |
  You are Mary, a Business Analyst facilitating a brainstorming session using the SCAMPER technique.

  {{mary_persona}}

  **SCAMPER Framework**:
  SCAMPER is a systematic creativity technique with 7 lenses for generating ideas:

  1. **Substitute**: What could you replace? (components, materials, approaches, people)
  2. **Combine**: What could you merge? (features, ideas, teams, technologies)
  3. **Adapt**: What could you adjust to fit another purpose? (from other domains)
  4. **Modify**: What could you change? (size, shape, color, attributes, frequency)
  5. **Put to Other Uses**: What else could this do? (new contexts, users, purposes)
  6. **Eliminate**: What could you remove? (complexity, steps, features, assumptions)
  7. **Reverse**: What if you flipped it? (order, roles, assumptions, perspectives)

  **Your Facilitation Style**:
  - Encouraging and curious, never judgmental
  - Ask open-ended questions that spark thinking
  - Use "Yes, and..." to build on user's ideas
  - Provide examples when users are stuck
  - Celebrate creative thinking ("That's interesting!", "I like that!")
  - Keep energy high but allow thinking time
  - Make it feel conversational, not like following a script
  - If one lens isn't generating ideas, move to the next

user_prompt: |
  Let's brainstorm: {{brainstorming_topic}}

  **Session Structure** (15-20 turns, ~20 minutes):

  1. **Introduction** (1 turn):
     - Welcome the user warmly
     - Briefly explain SCAMPER (2 sentences max)
     - Example: "SCAMPER helps us look at {{brainstorming_topic}} from 7 different angles to spark creative ideas. Ready to begin?"

  2. **SCAMPER Steps** (2-3 turns per step):

     **S - SUBSTITUTE** (2-3 turns):
     - Ask: "What could you SUBSTITUTE in {{brainstorming_topic}}?"
     - Follow-up: "What if we replaced [current approach] with [alternative]?"
     - Build on their answer with "Yes, and..."
     - Capture all ideas

     **C - COMBINE** (2-3 turns):
     - Ask: "What could you COMBINE with {{brainstorming_topic}}?"
     - Follow-up: "What if we merged [X] and [Y]?"
     - Build on their answer
     - Capture all ideas

     **A - ADAPT** (2-3 turns):
     - Ask: "How could you ADAPT {{brainstorming_topic}} from another context?"
     - Follow-up: "What works in [other domain] that we could apply here?"
     - Build on their answer
     - Capture all ideas

     **M - MODIFY** (2-3 turns):
     - Ask: "What could you MODIFY about {{brainstorming_topic}}?"
     - Follow-up: "What if we changed [size/shape/frequency]?"
     - Build on their answer
     - Capture all ideas

     **P - PUT TO OTHER USES** (2-3 turns):
     - Ask: "What other uses could {{brainstorming_topic}} have?"
     - Follow-up: "Who else could benefit from this?"
     - Build on their answer
     - Capture all ideas

     **E - ELIMINATE** (2-3 turns):
     - Ask: "What could you ELIMINATE from {{brainstorming_topic}}?"
     - Follow-up: "What complexity could we remove?"
     - Build on their answer
     - Capture all ideas

     **R - REVERSE** (2-3 turns):
     - Ask: "What if you REVERSED {{brainstorming_topic}}?"
     - Follow-up: "What if we flipped [assumption/order/perspective]?"
     - Build on their answer
     - Capture all ideas

  3. **Synthesis** (2-3 turns):
     - Review all ideas generated (count them!)
     - Group into themes if patterns emerge
     - Ask: "Which ideas excite you most?"
     - Identify quick wins vs long-term opportunities
     - Generate final summary

  **Important Guidelines**:
  - Adapt pacing to user's responses (don't rush if they're thinking deeply)
  - If a step isn't generating ideas, provide an example or move on
  - Keep it conversational - you're a colleague brainstorming together
  - Use their language and build on their examples
  - Encourage wild ideas - no idea is too crazy in brainstorming!

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"  # Epic 10 reference resolution
  brainstorming_topic: ""
  session_duration: 20

response:
  max_tokens: 1024
  temperature: 0.8  # Higher for creative facilitation
  format: text

metadata:
  category: brainstorming
  agent: mary
  phase: 1
  technique: scamper
  technique_type: structured
  energy_level: moderate
  typical_duration: 20-25
  best_for: "Methodical product improvement and systematic innovation"
  original_source: "BMAD brain-methods.csv (adapted for GAO-Dev)"
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

    async def recommend_techniques(
        self,
        topic: str,
        goal: str = "exploration"
    ) -> List[str]:
        """
        Recommend 2-3 brainstorming techniques based on goal.

        Args:
            topic: Topic to brainstorm about
            goal: Brainstorming goal (innovation, problem_solving, strategic_planning, exploration)

        Returns:
            List of 2-3 recommended technique names
        """

        # Simple rule-based recommendation
        if goal == "innovation":
            # Creative + wild techniques
            recommendations = ["scamper", "whatif", "first_principles"]
        elif goal == "problem_solving":
            # Deep + structured techniques
            recommendations = ["five_whys", "reversal", "scamper"]
        elif goal == "strategic_planning":
            # Structured + collaborative techniques
            recommendations = ["stakeholders", "constraints", "reverse"]
        else:  # exploration
            # Diverse mix
            recommendations = ["scamper", "mindmap", "yes_and"]

        self.logger.info(
            "techniques_recommended",
            goal=goal,
            recommendations=recommendations
        )
        return recommendations

    async def facilitate_brainstorming(
        self,
        user_request: str,
        technique: str = "scamper"
    ) -> BrainstormingSummary:
        """
        Facilitate brainstorming session using Epic 10 prompt system.

        Args:
            user_request: Original request or topic to brainstorm
            technique: Brainstorming technique to use

        Returns:
            BrainstormingSummary with ideas, mind map, and insights
        """

        # Load workflow metadata
        workflow = self.workflow_registry.load_workflow(
            "1-analysis/brainstorming/workflow.yaml"
        )

        # Get prompt name for selected technique
        prompt_name = workflow.prompts[technique]

        # Load prompt template (Epic 10 PromptLoader)
        template = self.prompt_loader.load_prompt(prompt_name)

        # Render prompt with variables (Epic 10 reference resolution)
        rendered = self.prompt_loader.render_prompt(template, {
            "brainstorming_topic": user_request,
            "mary_persona": "@file:gao_dev/agents/mary.md",  # Auto-resolved
            "session_duration": 20
        })

        # Create conversation session
        session = await self.conversation_manager.create_session(
            agent="Mary",
            workflow="brainstorming",
            context={"technique": technique, "topic": user_request}
        )

        # Multi-turn facilitation (~15-20 turns)
        ideas = []
        for turn in range(20):
            # Generate next facilitation message
            mary_message = await self.analysis_service.analyze(
                rendered,
                conversation_history=session.messages,
                max_tokens=template.response.max_tokens,
                temperature=template.response.temperature
            )

            await session.add_message("mary", mary_message)

            # Check if session is complete
            if "synthesis" in mary_message.lower() or turn >= 19:
                break

            # Get user response
            user_response = await session.get_user_response()
            await session.add_message("user", user_response)

            # Extract ideas from user response
            if user_response and len(user_response) > 10:
                ideas.append(Idea(
                    content=user_response,
                    technique=technique
                ))

        # Generate mind map
        mind_map = await self._generate_mind_map(ideas, user_request)

        # Synthesize insights
        insights = await self._synthesize_insights(ideas, technique)

        # Create summary
        summary = BrainstormingSummary(
            topic=user_request,
            technique=technique,
            ideas_generated=ideas,
            mind_map=mind_map,
            key_themes=insights["key_themes"],
            quick_wins=insights["quick_wins"],
            long_term_opportunities=insights["long_term_opportunities"],
            session_duration=session.duration,
            created_at=datetime.now()
        )

        # Save to .gao-dev/mary/brainstorming-sessions/
        output_path = workflow.output_file.format(
            technique=technique,
            timestamp=datetime.now().isoformat()
        )
        await self._save_summary(summary, output_path)

        return summary

    async def _generate_mind_map(
        self,
        ideas: List[Idea],
        central_topic: str
    ) -> str:
        """
        Generate text-based mind map in mermaid syntax.

        Uses LLM to cluster ideas into themes and create hierarchy.
        """
        self.logger.info("generating_mind_map", idea_count=len(ideas))

        clustering_prompt = f"""
Cluster these {len(ideas)} brainstorming ideas into 3-5 themes.

Topic: {central_topic}

Ideas:
{chr(10).join(f"- {idea.content}" for idea in ideas)}

Return JSON:
{{
  "themes": [
    {{
      "name": "Theme Name",
      "ideas": ["idea1", "idea2"]
    }}
  ]
}}
"""

        response = await self.analysis_service.analyze(
            clustering_prompt,
            model="haiku",
            response_format="json"
        )

        themes = json.loads(response)["themes"]

        # Generate mermaid syntax
        mermaid = ["graph TD"]
        mermaid.append(f"    A[{central_topic}]")

        for i, theme in enumerate(themes):
            theme_id = chr(66 + i)  # B, C, D, ...
            mermaid.append(f"    A --> {theme_id}[{theme['name']}]")

            for j, idea in enumerate(theme['ideas'][:5]):  # Limit 5 per theme
                idea_id = f"{theme_id}{j+1}"
                idea_text = idea[:40] + "..." if len(idea) > 40 else idea
                mermaid.append(f"    {theme_id} --> {idea_id}[{idea_text}]")

        return "\n".join(mermaid)

    async def _synthesize_insights(
        self,
        ideas: List[Idea],
        technique: str
    ) -> Dict[str, Any]:
        """Synthesize insights from brainstorming session."""
        self.logger.info("synthesizing_insights", idea_count=len(ideas))

        synthesis_prompt = f"""
Analyze this brainstorming session and extract insights.

Technique: {technique}
Ideas: {len(ideas)}

{chr(10).join(f"- {idea.content}" for idea in ideas)}

Extract:
1. Key themes (recurring concepts)
2. Quick wins (implementable in <1 month)
3. Long-term opportunities (need >3 months)

Return JSON:
{{
  "key_themes": ["theme1", "theme2"],
  "quick_wins": ["idea1", "idea2"],
  "long_term_opportunities": ["idea3", "idea4"]
}}
"""

        response = await self.analysis_service.analyze(
            synthesis_prompt,
            model="sonnet",
            response_format="json"
        )

        return json.loads(response)
```

---

## Testing Strategy

### Unit Tests (16+ tests)

**Test Prompt Rendering** (10 tests):
```python
def test_scamper_prompt_rendering():
    """Test SCAMPER prompt loads and renders correctly."""
    loader = PromptLoader(prompts_dir=Path("gao_dev/prompts"))
    template = loader.load_prompt("mary_brainstorming_scamper")

    assert template.name == "mary_brainstorming_scamper"
    assert "SCAMPER" in template.system_prompt

    rendered = loader.render_prompt(template, {
        "brainstorming_topic": "authentication",
        "mary_persona": "You are Mary"
    })

    assert "authentication" in rendered
    assert "You are Mary" in rendered
```

(Similar tests for: mindmap, whatif, first_principles, five_whys, yes_and, constraints, reversal, stakeholders, reverse)

**Test Technique Recommendation** (3 tests):
```python
async def test_recommend_techniques_for_innovation():
    """Test technique recommendation for innovation goal."""
    orchestrator = MaryOrchestrator(...)

    techniques = await orchestrator.recommend_techniques(
        topic="Better authentication",
        goal="innovation"
    )

    assert len(techniques) == 3
    assert "scamper" in techniques or "whatif" in techniques
```

**Test Mind Map Generation** (1 test):
```python
async def test_generate_mind_map():
    """Test mind map generation from ideas."""
    ideas = [
        Idea(content="Social login", technique="scamper"),
        Idea(content="Biometrics", technique="scamper"),
        Idea(content="2FA", technique="scamper")
    ]

    mind_map = await orchestrator._generate_mind_map(ideas, "Authentication")

    assert "graph TD" in mind_map
    assert "Authentication" in mind_map
```

**Test Insights Synthesis** (1 test):
```python
async def test_synthesize_insights():
    """Test insights synthesis from ideas."""
    ideas = [
        Idea(content="Add password manager integration", technique="scamper"),
        Idea(content="Implement blockchain auth", technique="scamper")
    ]

    insights = await orchestrator._synthesize_insights(ideas, "scamper")

    assert "key_themes" in insights
    assert "quick_wins" in insights
    assert "long_term_opportunities" in insights
```

**Test Orchestrator Integration** (1 test):
```python
async def test_facilitate_brainstorming_full_flow():
    """Test complete brainstorming facilitation."""
    result = await orchestrator.facilitate_brainstorming(
        user_request="Ideas for better authentication",
        technique="scamper"
    )

    assert isinstance(result, BrainstormingSummary)
    assert len(result.ideas_generated) > 0
    assert result.mind_map
    assert result.key_themes
```

### Integration Tests (2 tests)

```python
async def test_brian_delegates_to_mary_for_brainstorming():
    """Test Brian delegates brainstorming to Mary."""
    brian = BrianOrchestrator(...)

    result = await brian.assess_and_select_workflows(
        "I need ideas for improving our authentication system"
    )

    assert result.delegated_to == "Mary"
    assert result.mary_strategy == "brainstorming"
```

---

## Implementation Checklist

- [ ] Create workflow file: `workflows/1-analysis/brainstorming/workflow.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_scamper.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_mindmap.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_whatif.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_first_principles.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_five_whys.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_yes_and.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_constraints.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_reversal.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_stakeholders.yaml`
- [ ] Create prompt: `prompts/agents/mary_brainstorming_reverse.yaml`
- [ ] Create data model: `core/models/brainstorming_summary.py`
- [ ] Enhance MaryOrchestrator with `facilitate_brainstorming()` method
- [ ] Add `recommend_techniques()` method to MaryOrchestrator
- [ ] Add `_generate_mind_map()` helper method
- [ ] Add `_synthesize_insights()` helper method
- [ ] Update BrianOrchestrator delegation logic
- [ ] Create tests: `tests/orchestrator/test_mary_brainstorming.py`
- [ ] Run tests (16+ tests passing)
- [ ] Integration test: Brian → Mary brainstorming flow
- [ ] Performance validation: <500ms recommendation, <5s mind map

---

## Definition of Done

- [ ] All 11 files created (1 workflow + 10 prompts)
- [ ] All prompts follow Epic 10 format
- [ ] MaryOrchestrator uses PromptLoader
- [ ] 16+ tests passing (>90% coverage)
- [ ] Integration test passes
- [ ] Mind map generation working (mermaid syntax)
- [ ] Insights synthesis working (themes, quick wins, long-term)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No regressions in existing tests

---

**Status**: Todo
**Next Story**: Story 31.3 (Requirements Analysis Workflows & Prompts)
**Created**: 2025-11-10
**Updated**: 2025-11-10 (Epic 10 integration)
