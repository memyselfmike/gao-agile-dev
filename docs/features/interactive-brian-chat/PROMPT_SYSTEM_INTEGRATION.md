# Epic 31: Prompt Management System Integration Analysis

**Date**: 2025-11-10
**Purpose**: Verify Epic 31 integrates properly with Epic 10's prompt management system
**Status**: Integration Analysis Complete

---

## Executive Summary

✅ **GOOD NEWS**: Epic 31's BMAD mapping document is on the right track, BUT it needs to integrate with Epic 10's prompt system more explicitly.

**Finding**: The BMAD mapping correctly avoids CSV dependencies and uses YAML workflows, BUT it doesn't fully leverage the established `gao_dev/prompts/` infrastructure from Epic 10.

**Recommendation**: Use BOTH workflow YAML files AND prompt template YAML files for proper separation of concerns.

---

## Epic 10's Prompt Management System (Implemented)

### Directory Structure

```
gao_dev/
├── prompts/                          # ← Epic 10 prompt system
│   ├── agents/                       # Agent-specific prompts
│   │   ├── brian_analysis.yaml
│   │   └── brian_context_with_learnings.yaml
│   ├── tasks/                        # Task prompts
│   │   ├── create_prd.yaml
│   │   ├── create_story.yaml
│   │   ├── create_architecture.yaml
│   │   ├── implement_story.yaml
│   │   └── validate_story.yaml
│   ├── story_phases/                 # Story lifecycle prompts
│   │   ├── story_creation.yaml
│   │   ├── story_implementation.yaml
│   │   └── story_validation.yaml
│   └── common/                       # Shared content
│       ├── outputs/
│       └── responsibilities/
│
└── workflows/                        # Workflow metadata
    ├── 2-plan/prd/workflow.yaml
    ├── 3-solutioning/architecture/workflow.yaml
    └── 4-implementation/dev-story/workflow.yaml
```

### Prompt Template Format (Epic 10 Standard)

```yaml
name: brian_complexity_analysis
description: "Analyze project complexity and recommend scale level"
version: 2.0.0

system_prompt: |
  You are Brian Thompson, a Senior Engineering Manager...

  {{brian_persona}}

user_prompt: |
  Analyze this software development request...

  User Request:
  {{user_request}}

  Scale Level Definitions:
  {{scale_level_definitions}}

variables:
  brian_persona: ""
  user_request: ""
  scale_level_definitions: "@file:gao_dev/config/scale_levels.yaml"
  json_schema: "@file:gao_dev/schemas/analysis_response.json"

response:
  max_tokens: 2048
  temperature: 0.7
  format: json

metadata:
  category: analysis
  agent: brian
  phase: 0
```

**Key Features**:
- **Reference Resolution**: `@file:path` injects file content
- **Variable Substitution**: `{{variable}}` with defaults
- **System + User Prompts**: Separate persona from instructions
- **Response Configuration**: Model settings per prompt
- **Metadata**: Categorization and tagging

### How Prompts Are Used

**Example: Brian's Complexity Analysis**
```python
# Load prompt template
template = prompt_loader.load_prompt("brian_complexity_analysis")

# Render with variables
rendered = prompt_loader.render_prompt(template, {
    "user_request": "Build a todo app",
    "brian_persona": agent_persona_text
})

# Use in AIAnalysisService
result = await analysis_service.analyze(
    rendered,
    max_tokens=template.response.max_tokens,
    temperature=template.response.temperature
)
```

---

## Epic 31's Current Approach (From BMAD Mapping)

### Proposed Structure (From BMAD_TO_GAODEV_MAPPING.md)

```
gao_dev/workflows/1-analysis/
├── vision-elicitation/
│   ├── vision-canvas.yaml
│   ├── problem-solution-fit.yaml
│   ├── outcome-mapping.yaml
│   └── 5w1h-analysis.yaml
│
├── brainstorming/
│   ├── scamper.yaml
│   ├── mind-mapping.yaml
│   ├── what-if-scenarios.yaml
│   ├── first-principles.yaml
│   ├── five-whys.yaml
│   └── ... (10 total)
│
└── requirements-analysis/
    ├── moscow-prioritization.yaml
    ├── kano-model.yaml
    ├── dependency-mapping.yaml
    ├── risk-identification.yaml
    └── constraint-analysis.yaml
```

### Proposed Workflow Format

```yaml
name: scamper-brainstorming
description: SCAMPER Method - Systematic creativity
phase: 1
author: Mary (Business Analyst)
category: brainstorming
technique_type: structured

facilitation_steps:
  - step: "substitute"
    prompt: "What could you substitute?"
    examples: ["What if we replaced X?"]
  - step: "combine"
    prompt: "What could you combine?"

instructions: |
  You are Mary, facilitating SCAMPER...
```

### The Issue

**Problem**: Mixing workflow metadata with prompt content!

The proposed approach combines:
1. **Workflow metadata** (name, phase, author, category)
2. **Facilitation prompts** (what Mary says to the user)
3. **Instructions** (how Mary should behave)

This violates Epic 10's separation of concerns:
- **Workflows** = metadata + structure
- **Prompts** = actual LLM instructions

---

## Correct Integration: Workflows + Prompts

### Principle: Separation of Concerns

**Workflows** (`gao_dev/workflows/`):
- Define WHAT to execute
- Specify variables, outputs, metadata
- Reference prompts and templates
- No LLM instructions embedded

**Prompts** (`gao_dev/prompts/`):
- Define HOW to execute (LLM instructions)
- System and user prompts
- Variable substitution
- Response configuration

### Revised Structure for Epic 31

```
gao_dev/
├── prompts/
│   └── agents/
│       ├── mary_vision_elicitation.yaml     # ← NEW
│       ├── mary_brainstorming_scamper.yaml  # ← NEW
│       ├── mary_brainstorming_mindmap.yaml  # ← NEW
│       ├── mary_requirements_moscow.yaml    # ← NEW
│       ├── mary_requirements_kano.yaml      # ← NEW
│       └── ... (19 total prompt files)
│
└── workflows/
    └── 1-analysis/
        ├── vision-elicitation/
        │   └── workflow.yaml               # Metadata only, references prompts
        ├── brainstorming/
        │   └── workflow.yaml               # Metadata only, references prompts
        └── requirements-analysis/
            └── workflow.yaml               # Metadata only, references prompts
```

### Example: SCAMPER Brainstorming

**Workflow File**: `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml`

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
      - mind_mapping
      - what_if_scenarios
      - first_principles
      - five_whys
      - yes_and_building
      - resource_constraints
      - assumption_reversal
      - stakeholder_roundtable
      - reverse_engineering

  session_duration:
    description: Target duration in minutes
    type: integer
    default: 20

required_tools:
  - conversation_manager
  - analysis_service

output_file: ".gao-dev/mary/brainstorming-sessions/{{technique}}-{{timestamp}}.md"

# Workflow references prompts
prompts:
  scamper: "mary_brainstorming_scamper"
  mind_mapping: "mary_brainstorming_mindmap"
  what_if_scenarios: "mary_brainstorming_whatif"
  first_principles: "mary_brainstorming_first_principles"
  five_whys: "mary_brainstorming_five_whys"
  yes_and_building: "mary_brainstorming_yes_and"
  resource_constraints: "mary_brainstorming_constraints"
  assumption_reversal: "mary_brainstorming_reversal"
  stakeholder_roundtable: "mary_brainstorming_stakeholders"
  reverse_engineering: "mary_brainstorming_reverse"

metadata:
  category: brainstorming
  domain: business_analysis
  techniques_available: 10
```

**Prompt File**: `gao_dev/prompts/agents/mary_brainstorming_scamper.yaml`

```yaml
name: mary_brainstorming_scamper
description: "Mary facilitates SCAMPER brainstorming technique"
version: 1.0.0

system_prompt: |
  You are Mary, a Business Analyst facilitating a brainstorming session using the SCAMPER technique.

  {{mary_persona}}

  **SCAMPER Framework**:
  SCAMPER is a systematic creativity technique with 7 lenses:
  - **S**ubstitute: What can we replace?
  - **C**ombine: What can we merge?
  - **A**dapt: What can we adjust?
  - **M**odify: What can we change?
  - **P**ut to other uses: What else can this do?
  - **E**liminate: What can we remove?
  - **R**everse: What if we flip it?

  **Your Facilitation Style**:
  - Encouraging and curious
  - Ask open-ended questions
  - Use "Yes, and..." to build on ideas
  - No judgment - all ideas welcome
  - Keep the energy high
  - Make it feel conversational, not robotic

user_prompt: |
  Facilitate a SCAMPER brainstorming session on: {{brainstorming_topic}}

  **Session Structure**:

  1. **Introduction** (1 turn):
     - Welcome the user
     - Briefly explain SCAMPER (2 sentences max)
     - Set expectations: 7 steps, ~20 minutes

  2. **SCAMPER Steps** (2-3 turns per step, 14-21 turns total):

     **Substitute Step**:
     - Ask: "What could you substitute in {{brainstorming_topic}}?"
     - Follow-up examples: "What if we replaced X with Y?", "What alternatives exist?"
     - Capture ideas

     **Combine Step**:
     - Ask: "What could you combine with {{brainstorming_topic}}?"
     - Follow-up examples: "What if we merged X and Y?", "How could we integrate features?"
     - Capture ideas

     **Adapt Step**:
     - Ask: "How could you adapt {{brainstorming_topic}}?"
     - Follow-up examples: "What could we adjust for a different context?", "How do similar solutions work elsewhere?"
     - Capture ideas

     **Modify Step**:
     - Ask: "What could you modify about {{brainstorming_topic}}?"
     - Follow-up examples: "What if we changed the scale, color, form?", "How could we alter attributes?"
     - Capture ideas

     **Put to Other Uses Step**:
     - Ask: "What other uses could {{brainstorming_topic}} have?"
     - Follow-up examples: "Who else could use this?", "What other problems could this solve?"
     - Capture ideas

     **Eliminate Step**:
     - Ask: "What could you eliminate from {{brainstorming_topic}}?"
     - Follow-up examples: "What if we removed this feature?", "Can we simplify by subtracting?"
     - Capture ideas

     **Reverse Step**:
     - Ask: "What if you reversed {{brainstorming_topic}}?"
     - Follow-up examples: "What's the opposite approach?", "Can we flip the process?"
     - Capture ideas

  3. **Synthesis** (2-3 turns):
     - Thank the user for their ideas
     - Summarize all ideas generated (grouped by SCAMPER step)
     - Ask: "Which of these ideas excites you most?"
     - Identify top 3-5 ideas to explore further
     - Suggest next steps (e.g., "Want to do mind mapping on the top idea?")

  **Important**:
  - Adapt pacing to user's responses (don't rush if they're generating lots of ideas)
  - If a step isn't generating ideas, move on (don't force it)
  - Keep it conversational - you're a colleague, not a script
  - Use their language and build on their examples

  **Output**: Generate your first facilitation message (introduction + start of Substitute step)

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"
  brainstorming_topic: ""

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
  best_for: "Methodical product improvement and innovation"
  original_source: "BMAD brain-methods.csv (adapted for GAO-Dev)"
```

### How It Works Together

**Step 1: User Invokes Workflow**
```python
# MaryOrchestrator
async def facilitate_brainstorming(
    self,
    user_request: str,
    technique: str = "scamper"
) -> BrainstormingSummary:
    # Load workflow
    workflow = self.workflow_registry.load_workflow("1-analysis/brainstorming/workflow.yaml")

    # Get prompt name for selected technique
    prompt_name = workflow.prompts[technique]  # "mary_brainstorming_scamper"
```

**Step 2: Load Prompt Template**
```python
    # Load prompt template (uses Epic 10 infrastructure)
    template = self.prompt_loader.load_prompt(prompt_name)
```

**Step 3: Render Prompt with Variables**
```python
    # Render prompt (resolves @file: references, {{variables}})
    rendered = self.prompt_loader.render_prompt(template, {
        "brainstorming_topic": user_request,
        "mary_persona": "@file:gao_dev/agents/mary.md"  # Auto-resolved
    })
```

**Step 4: Execute Conversation**
```python
    # Use ConversationManager + AIAnalysisService
    session = await self.conversation_manager.create_session(
        agent="Mary",
        workflow="brainstorming",
        context={"technique": technique}
    )

    # Multi-turn facilitation
    async for turn in range(20):  # ~20 turns for SCAMPER
        # Generate next facilitation prompt
        mary_message = await self.analysis_service.analyze(
            rendered,  # Uses prompt template
            conversation_history=session.messages,
            max_tokens=template.response.max_tokens,
            temperature=template.response.temperature
        )

        await session.add_message("mary", mary_message)

        # Get user response
        user_response = await session.get_user_response()
        await session.add_message("user", user_response)
```

**Step 5: Generate Output**
```python
    # Synthesize and save
    summary = await self._synthesize_session(session)
    output_path = workflow.output_file.format(
        technique=technique,
        timestamp=datetime.now().isoformat()
    )
    await self._save_summary(summary, output_path)

    return summary
```

---

## Benefits of Proper Integration

### 1. Separation of Concerns ✅

**Workflows** = Metadata + orchestration
**Prompts** = LLM instructions + facilitation

This allows:
- Update prompts without changing workflows
- A/B test prompt variations
- Reuse prompts across workflows
- Version prompts independently

### 2. Leverage Epic 10 Infrastructure ✅

**Already implemented**:
- `PromptLoader` - Load and cache prompts
- `PromptRegistry` - Discover all prompts
- Reference resolution (`@file:`, `@config:`)
- Variable substitution (`{{variable}}`)
- JSON Schema validation

**No need to rebuild this for Epic 31!**

### 3. Consistent with Other Agents ✅

**Existing agents** (Brian, John, Winston, Bob, Amelia, Murat):
- Prompts in `gao_dev/prompts/agents/`
- Workflows in `gao_dev/workflows/`
- Clear separation

**Mary should follow same pattern**

### 4. Plugin-Friendly ✅

Plugins can:
- Override Mary's prompts (custom facilitation style)
- Add new brainstorming techniques (drop in new prompt YAML)
- Register custom workflows
- All without code changes

### 5. Testable ✅

Easy to test:
- Prompt rendering (unit tests)
- Variable resolution (unit tests)
- Workflow execution (integration tests)
- End-to-end facilitation (E2E tests)

---

## Revised Epic 31 Deliverables

### Remove from BMAD Mapping Document

**Old Approach** (from BMAD mapping):
```yaml
# WRONG: Mixing workflow + prompt in one file
name: scamper-brainstorming
facilitation_steps:
  - step: "substitute"
    prompt: "What could you substitute?"
instructions: |
  You are Mary, facilitating SCAMPER...
```

### Add to Epic 31 Scope

**Story 31.2 Revised: Brainstorming Workflows & Prompts (5 pts)**

**Deliverables**:
1. **1 Workflow File**: `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml`
   - Metadata for all 10 techniques
   - Variable definitions
   - Prompt references

2. **10 Prompt Files**: `gao_dev/prompts/agents/mary_brainstorming_*.yaml`
   - `mary_brainstorming_scamper.yaml`
   - `mary_brainstorming_mindmap.yaml`
   - `mary_brainstorming_whatif.yaml`
   - `mary_brainstorming_first_principles.yaml`
   - `mary_brainstorming_five_whys.yaml`
   - `mary_brainstorming_yes_and.yaml`
   - `mary_brainstorming_constraints.yaml`
   - `mary_brainstorming_reversal.yaml`
   - `mary_brainstorming_stakeholders.yaml`
   - `mary_brainstorming_reverse.yaml`

3. **MaryOrchestrator Integration**: Use `PromptLoader` (Epic 10) to load prompts

**Story 31.1 Revised: Vision Elicitation Workflows & Prompts (5 pts)**

**Deliverables**:
1. **1 Workflow File**: `gao_dev/workflows/1-analysis/vision-elicitation/workflow.yaml`
2. **4 Prompt Files**: `gao_dev/prompts/agents/mary_vision_*.yaml`
   - `mary_vision_canvas.yaml`
   - `mary_vision_problem_solution_fit.yaml`
   - `mary_vision_outcome_mapping.yaml`
   - `mary_vision_5w1h.yaml`

**Story 31.3 Revised: Requirements Analysis Workflows & Prompts (5 pts)**

**Deliverables**:
1. **1 Workflow File**: `gao_dev/workflows/1-analysis/requirements-analysis/workflow.yaml`
2. **5 Prompt Files**: `gao_dev/prompts/agents/mary_requirements_*.yaml`
   - `mary_requirements_moscow.yaml`
   - `mary_requirements_kano.yaml`
   - `mary_requirements_dependency.yaml`
   - `mary_requirements_risk.yaml`
   - `mary_requirements_constraint.yaml`

**Story 31.4 Revised: Domain-Specific Workflows & Prompts (3 pts)**

**Deliverables**:
1. **1 Workflow File**: `gao_dev/workflows/1-analysis/domain-requirements/workflow.yaml`
2. **5 Prompt Files**: `gao_dev/prompts/agents/mary_domain_*.yaml`
   - `mary_domain_web_app.yaml`
   - `mary_domain_mobile_app.yaml`
   - `mary_domain_api_service.yaml`
   - `mary_domain_cli_tool.yaml`
   - `mary_domain_data_pipeline.yaml`

---

## Total File Count

**Workflows**: 4 files
- `brainstorming/workflow.yaml`
- `vision-elicitation/workflow.yaml`
- `requirements-analysis/workflow.yaml`
- `domain-requirements/workflow.yaml`

**Prompts**: 24 files
- 10 brainstorming prompts
- 4 vision elicitation prompts
- 5 requirements analysis prompts
- 5 domain-specific prompts

**Total**: 28 files (4 workflows + 24 prompts)

**Comparison**:
- **BMAD Mapping Proposed**: 19 workflow files (mixed workflow+prompt)
- **Correct Approach**: 4 workflow + 24 prompt = 28 files (proper separation)

---

## Implementation Checklist

### Epic 31 Integration Requirements

- [ ] **Use PromptLoader** (Epic 10)
  - Load prompts from `gao_dev/prompts/agents/mary_*.yaml`
  - Use `prompt_loader.load_prompt(name)`
  - Use `prompt_loader.render_prompt(template, variables)`

- [ ] **Use PromptRegistry** (Epic 10)
  - Register Mary's prompts on startup
  - Allow discovery: `registry.list_prompts(agent="mary")`

- [ ] **Reference Resolution**
  - Use `@file:` for including agent persona
  - Use `@config:` for system settings
  - Example: `mary_persona: "@file:gao_dev/agents/mary.md"`

- [ ] **Workflow Files**
  - Keep minimal (metadata only)
  - Reference prompts by name
  - No LLM instructions embedded

- [ ] **Prompt Files**
  - Follow Epic 10 format exactly
  - Include `system_prompt` and `user_prompt`
  - Define `variables`, `response`, `metadata`
  - Keep LLM instructions here, not in workflows

- [ ] **Testing**
  - Test prompt rendering (unit)
  - Test reference resolution (unit)
  - Test workflow execution (integration)
  - Test end-to-end facilitation (E2E)

- [ ] **Documentation**
  - Update Mary agent docs with prompt references
  - Document prompt customization
  - Provide examples in user guide

---

## Revised Story Point Estimate

**No change to total**, but better clarity on deliverables:

- Story 31.1: 5 pts (1 workflow + 4 prompts)
- Story 31.2: 5 pts (1 workflow + 10 prompts)
- Story 31.3: 5 pts (1 workflow + 5 prompts)
- Story 31.4: 3 pts (1 workflow + 5 prompts)
- Story 31.5: 5 pts (integration + docs)
- Story 31.6: 3 pts (Mary → John handoff)

**Total**: 28 pts (unchanged, but now properly integrated with Epic 10)

---

## Success Criteria

Epic 31 properly integrates with Epic 10's prompt system when:

✅ All Mary prompts in `gao_dev/prompts/agents/mary_*.yaml`
✅ All workflows in `gao_dev/workflows/1-analysis/*/workflow.yaml`
✅ MaryOrchestrator uses `PromptLoader` to load prompts
✅ Prompts use `@file:` and `{{variable}}` syntax
✅ No LLM instructions in workflow files
✅ Consistent with Brian, John, Winston, Bob, Amelia, Murat patterns
✅ Plugin-friendly (can override Mary's prompts)
✅ Testable (unit + integration + E2E)

---

## Conclusion

**The BMAD mapping document is 90% correct** - it properly avoids CSV dependencies and uses YAML. **The 10% fix** is to properly separate workflows (metadata) from prompts (LLM instructions) using Epic 10's established infrastructure.

**Action Items**:
1. ✅ Update BMAD_TO_GAODEV_MAPPING.md with workflow/prompt separation
2. ✅ Create 4 workflow YAML files (metadata only)
3. ✅ Create 24 prompt YAML files (LLM instructions)
4. ✅ Use PromptLoader in MaryOrchestrator
5. ✅ Follow Epic 10 patterns exactly

**Result**: Epic 31 integrates seamlessly with GAO-Dev's established architecture while avoiding BMAD CSV dependencies.

---

**Status**: ✅ **INTEGRATION APPROACH DEFINED**
**Next Step**: Update BMAD mapping document with prompt/workflow separation
**Created**: 2025-11-10

