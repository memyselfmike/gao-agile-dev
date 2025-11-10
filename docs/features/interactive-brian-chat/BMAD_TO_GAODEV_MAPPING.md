# BMAD to GAO-Dev Architecture Mapping

**Date**: 2025-11-10
**Purpose**: Map BMAD Method assets to GAO-Dev architectural patterns for Epic 31 (Mary Integration)
**Problem**: Epic 31 proposes using BMAD CSV files directly, which violates GAO-Dev's established YAML-based patterns

---

## Executive Summary

Epic 31's current architecture proposes loading BMAD CSV files (`brain-methods.csv`, `adv-elicit-methods.csv`) directly into Mary. This is **architecturally inconsistent** with how GAO-Dev implements agents, workflows, and configurations.

**Key Finding**: We should **extract concepts from BMAD** and **implement them in GAO-Dev patterns**, not load BMAD files directly.

**Recommendation**: Transform BMAD assets into:
1. Mary workflows (YAML files in `gao_dev/workflows/1-analysis/`)
2. Mary checklists (YAML files in `gao_dev/config/checklists/requirements/`)
3. Prompt templates (embedded in workflow YAML or agent markdown)
4. No CSV dependencies

---

## Current GAO-Dev Architecture

### 1. Agents

**Location**: `gao_dev/agents/*.md`

**Format**: Simple markdown with persona/responsibilities
```markdown
# Mary - Business Analyst Agent

## Role
Business Analyst for GAO-Dev

## Responsibilities
- Conduct business analysis and requirements gathering
- Document current state and pain points
...

## Persona
You are Mary, an experienced Business Analyst...

## Workflow Expertise
- product-brief: Creating product briefs
- research: Market and technical research
```

**Key Insight**: Agents are lightweight personas, NOT full YAML config files

---

### 2. Workflows

**Location**: `gao_dev/workflows/{phase}/{workflow-name}/workflow.yaml`

**Structure**:
```
gao_dev/workflows/
├── 2-plan/
│   ├── prd/
│   │   ├── workflow.yaml
│   │   └── template.md
│   └── tech-spec/
│       └── workflow.yaml
├── 3-solutioning/
│   └── architecture/
│       ├── workflow.yaml
│       ├── architecture-patterns.yaml
│       └── decision-catalog.yaml
└── 4-implementation/
    ├── create-story/
    ├── dev-story/
    └── story-done/
```

**Format**: YAML with variables, templates, metadata
```yaml
name: prd
description: Create Product Requirements Document
phase: 2
author: John (Product Manager)
autonomous: true

variables:
  project_name:
    description: Project name
    type: string
    required: true
  prd_location:
    description: Path to PRD file
    type: string
    default: "docs/PRD.md"

required_tools:
  - write_file

output_file: "{{prd_location}}"

templates:
  main: template.md
```

**Key Insight**: Workflows are self-contained YAML files with variable resolution, not CSV data

---

### 3. Checklists

**Location**: `gao_dev/config/checklists/{category}/*.yaml`

**Categories**:
- `code-quality/` - Clean code, SOLID, refactoring, type safety
- `testing/` - Unit, integration, e2e test standards
- `security/` - OWASP, API security, secrets management
- `deployment/` - Production readiness, rollout, configuration
- `operations/` - Monitoring, incident response, disaster recovery
- `general/` - Code review, PR review, documentation

**Format**: YAML with structured checklist items
```yaml
checklist:
  name: "Documentation Standards"
  category: "code-quality"
  version: "1.0.0"
  description: "Documentation completeness and quality checklist"

  items:
    - id: "readme-exists"
      text: "README.md exists with project overview"
      severity: "high"
      help_text: "Include project description, installation steps..."

    - id: "api-docs"
      text: "API documentation complete and up-to-date"
      severity: "high"
      help_text: "Document all public APIs..."

  metadata:
    domain: "software-engineering"
    applicable_to: ["documentation", "story-implementation"]
    author: "John"
    tags: ["documentation", "readme", "api-docs"]
```

**Key Insight**: Reusable quality gates in YAML format with JSON Schema validation (Epic 14)

---

### 4. Configuration Files

**Location**: `gao_dev/config/*.yaml`

**Files**:
- `defaults.yaml` - Default settings
- `scale_levels.yaml` - Scale-adaptive routing
- `governance.yaml` - Governance policies
- `ceremony_limits.yaml` - Ceremony configurations
- `auto_injection.yaml` - Context injection rules

**Key Insight**: All system configuration in YAML, no CSV files

---

## BMAD Structure (Source Material)

### 1. Agent Definitions

**Location**: `bmad/bmm/agents/*.agent.yaml`

**Format**: YAML with menu system and workflow references
```yaml
agent:
  metadata:
    id: bmad/bmm/agents/analyst.md
    name: Mary
    title: Business Analyst
    icon: 📊
    module: bmm

  persona:
    role: Strategic Business Analyst + Requirements Expert
    identity: Senior analyst with deep expertise...
    communication_style: Analytical and systematic...
    principles:
      - I believe that every business challenge has root causes...

  menu:
    - trigger: brainstorm-project
      workflow: "{project-root}/bmad/bmm/workflows/1-analysis/brainstorm-project/workflow.yaml"
      description: Guide me through Brainstorming

    - trigger: product-brief
      workflow: "{project-root}/bmad/bmm/workflows/1-analysis/product-brief/workflow.yaml"
      description: Produce Project Brief
```

**Observation**: Much richer than GAO-Dev agents, but we don't need all this complexity

---

### 2. CSV Data Files

**Location**: `bmad/core/workflows/brainstorming/brain-methods.csv`

**Content**: 36 brainstorming techniques across 7 categories

```csv
category,technique_name,description,facilitation_prompts,best_for,energy_level,typical_duration
collaborative,Yes And Building,Build momentum through positive additions...,Yes and we could also...|Building on that idea...,team-building,high,15-20
collaborative,Brain Writing Round Robin,Silent idea generation...,Write your idea silently|Pass to the next person...,quiet-voices,moderate,20-25
...
structured,SCAMPER Method,Systematic creativity through seven lenses...,S-What could you substitute?|C-What could you combine?...,methodical-improvement,moderate,20-25
...
wild,Zombie Apocalypse Planning,Design solutions for extreme survival...,Society collapsed - now what?|Only basics work...,extreme-thinking,high,15-20
```

**Location**: `bmad/core/tasks/adv-elicit-methods.csv`

**Content**: 39 advanced elicitation methods across 11 categories

```csv
category,method_name,description,output_pattern
advanced,Tree of Thoughts,Explore multiple reasoning paths...,paths → evaluation → selection
collaboration,Stakeholder Round Table,Convene multiple personas...,perspectives → synthesis → alignment
core,First Principles Analysis,Strip away assumptions...,assumptions → truths → new approach
creative,Reverse Engineering,Work backwards from desired outcome...,end state → steps backward → path forward
...
```

---

## The Architectural Problem

### Epic 31's Proposed Approach (WRONG)

**From Architecture Document**:
```python
def _load_techniques(self) -> List[BrainstormingTechnique]:
    """
    Load techniques from BMAD CSV.

    Returns:
        List of 36 brainstorming techniques across 7 categories...
    """
    # Loads: bmad/core/workflows/brainstorming/brain-methods.csv
    # Loads: bmad/core/tasks/adv-elicit-methods.csv
```

**Problems**:
1. **CSV Dependency**: GAO-Dev uses YAML, not CSV
2. **External Coupling**: Depends on BMAD structure staying stable
3. **Pattern Violation**: Contradicts Epic 10 (prompt/config abstraction)
4. **Validation Gap**: CSV has no JSON Schema validation (unlike checklists)
5. **Inconsistency**: Other agents don't load CSV files
6. **Migration Risk**: What if BMAD CSV format changes?
7. **Complexity**: Parsing CSV + schema validation + error handling

### Why This Happened

Epic 31 was designed by looking at BMAD as source material and assuming we should use it directly. This is a **conceptual error** - BMAD is inspiration, not dependency.

**The user is right**: We're "leaving BMAD behind" like we did with other agents.

---

## Correct Mapping: BMAD → GAO-Dev

### Principle: Extract Concepts, Not Files

**Don't**: Load BMAD CSV files directly
**Do**: Extract valuable techniques and implement as GAO-Dev patterns

### Mapping Table

| BMAD Asset | BMAD Format | GAO-Dev Pattern | Location |
|------------|-------------|-----------------|----------|
| **Brainstorming Techniques** | CSV (36 techniques) | Workflows | `gao_dev/workflows/1-analysis/brainstorming/{technique}.yaml` |
| **Elicitation Methods** | CSV (39 methods) | Workflows | `gao_dev/workflows/1-analysis/requirements/{method}.yaml` |
| **Domain Questions** | (Proposed) | Prompt Templates | Embedded in workflow YAML |
| **Facilitation Prompts** | CSV column | Workflow Instructions | `workflow.yaml` instructions field |
| **Technique Metadata** | CSV columns | Workflow Variables | `workflow.yaml` variables field |
| **Mary's Persona** | YAML agent | Markdown Agent | `gao_dev/agents/mary.md` (already exists) |

---

## Implementation Strategy

### Phase 1: Extract Core Techniques

**Goal**: Identify the 10-15 most valuable techniques from BMAD's 36+39 assets

**Brainstorming Techniques** (Select 10 from 36):
1. **SCAMPER Method** (structured) - Systematic creativity
2. **Mind Mapping** (structured) - Visual organization
3. **What If Scenarios** (creative) - Explore possibilities
4. **First Principles Thinking** (creative) - Strip assumptions
5. **Five Whys** (deep) - Root cause analysis
6. **Yes And Building** (collaborative) - Team momentum
7. **Resource Constraints** (structured) - Force prioritization
8. **Assumption Reversal** (deep) - Challenge beliefs
9. **Stakeholder Round Table** (collaboration) - Multiple perspectives
10. **Reverse Engineering** (creative) - Work backwards

**Elicitation Methods** (Select 5 from 39):
1. **5 Whys Deep Dive** (core) - Root cause discovery
2. **Stakeholder Round Table** (collaboration) - Diverse perspectives
3. **First Principles Analysis** (core) - Fundamental truths
4. **What If Scenarios** (creative) - Alternative realities
5. **SCAMPER Method** (creative) - Systematic ideation

**Rationale**: Start with proven, widely-applicable techniques. Defer specialized/theatrical/wild techniques to future.

---

### Phase 2: Create Mary Workflows + Prompts

**IMPORTANT**: Following Epic 10's architecture, we separate:
- **Workflows** (metadata) → `gao_dev/workflows/`
- **Prompts** (LLM instructions) → `gao_dev/prompts/agents/`

**Workflow Structure** (metadata only):
```
gao_dev/workflows/1-analysis/
├── vision-elicitation/
│   └── workflow.yaml              # ← 1 workflow for all 4 techniques
│
├── brainstorming/
│   └── workflow.yaml              # ← 1 workflow for all 10 techniques
│
├── requirements-analysis/
│   └── workflow.yaml              # ← 1 workflow for all 5 methods
│
└── domain-requirements/
    └── workflow.yaml              # ← 1 workflow for all 5 domains
```

**Prompt Structure** (LLM instructions):
```
gao_dev/prompts/agents/
├── mary_brainstorming_scamper.yaml
├── mary_brainstorming_mindmap.yaml
├── mary_brainstorming_whatif.yaml
├── mary_brainstorming_first_principles.yaml
├── mary_brainstorming_five_whys.yaml
├── mary_brainstorming_yes_and.yaml
├── mary_brainstorming_constraints.yaml
├── mary_brainstorming_reversal.yaml
├── mary_brainstorming_stakeholders.yaml
├── mary_brainstorming_reverse.yaml
│
├── mary_vision_canvas.yaml
├── mary_vision_problem_solution_fit.yaml
├── mary_vision_outcome_mapping.yaml
├── mary_vision_5w1h.yaml
│
├── mary_requirements_moscow.yaml
├── mary_requirements_kano.yaml
├── mary_requirements_dependency.yaml
├── mary_requirements_risk.yaml
├── mary_requirements_constraint.yaml
│
├── mary_domain_web_app.yaml
├── mary_domain_mobile_app.yaml
├── mary_domain_api_service.yaml
├── mary_domain_cli_tool.yaml
└── mary_domain_data_pipeline.yaml
```

**Total Files**: 4 workflows + 24 prompts = 28 files

**Workflow File** (Metadata Only): `gao_dev/workflows/1-analysis/brainstorming/workflow.yaml`
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

# Reference prompts by name (Epic 10 pattern)
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

**Prompt File** (LLM Instructions): `gao_dev/prompts/agents/mary_brainstorming_scamper.yaml`
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

     **Substitute**: "What could you substitute in {{brainstorming_topic}}?"
     **Combine**: "What could you combine with {{brainstorming_topic}}?"
     **Adapt**: "How could you adapt {{brainstorming_topic}}?"
     **Modify**: "What could you modify about {{brainstorming_topic}}?"
     **Put to Other Uses**: "What other uses could {{brainstorming_topic}} have?"
     **Eliminate**: "What could you eliminate from {{brainstorming_topic}}?"
     **Reverse**: "What if you reversed {{brainstorming_topic}}?"

  3. **Synthesis** (2-3 turns):
     - Summarize all ideas by SCAMPER step
     - Identify top 3-5 ideas to explore further
     - Suggest next steps

  **Important**: Adapt pacing to user's responses, keep it conversational

variables:
  mary_persona: "@file:gao_dev/agents/mary.md"  # Epic 10 reference resolution
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

**Benefits**:
- ✅ Self-contained workflow (no CSV dependency)
- ✅ Consistent with GAO-Dev patterns
- ✅ Variable resolution support
- ✅ Clear facilitation steps
- ✅ Metadata tracking (source attribution)
- ✅ Can add/modify/remove techniques independently

---

### Phase 3: Create Mary Checklists (Optional)

**Structure**:
```
gao_dev/config/checklists/requirements/
├── vision-elicitation.yaml
├── requirements-clarity.yaml
├── stakeholder-coverage.yaml
├── success-metrics.yaml
└── risk-assessment.yaml
```

**Example**: Vision Elicitation Checklist
```yaml
checklist:
  name: "Vision Elicitation Quality"
  category: "requirements"
  version: "1.0.0"
  description: "Ensure comprehensive vision elicitation"

  items:
    - id: "target-users-defined"
      text: "Target users/personas clearly identified"
      severity: "high"
      help_text: "Identify who will use this. Be specific: roles, demographics, needs."

    - id: "problem-articulated"
      text: "Problem statement clearly articulated"
      severity: "high"
      help_text: "What problem are we solving? What's the current pain?"

    - id: "value-proposition"
      text: "Value proposition defined"
      severity: "high"
      help_text: "Why would users choose this? What's unique?"

    - id: "success-metrics"
      text: "Success metrics identified"
      severity: "medium"
      help_text: "How will we measure success? What are the KPIs?"

    - id: "constraints-identified"
      text: "Constraints and limitations documented"
      severity: "medium"
      help_text: "Time, budget, technical, regulatory constraints?"

    - id: "stakeholders-mapped"
      text: "All stakeholders identified and mapped"
      severity: "medium"
      help_text: "Who has a stake? What do they care about?"

  metadata:
    domain: "business-analysis"
    applicable_to: ["vision-elicitation", "requirements-gathering"]
    author: "Mary"
    tags: ["vision", "requirements", "clarity"]
```

**Benefits**:
- ✅ Quality gates for Mary's workflows
- ✅ Consistent with Epic 14 checklist system
- ✅ JSON Schema validation
- ✅ Reusable across workflows

---

### Phase 4: Update Mary Agent

**File**: `gao_dev/agents/mary.md`

**Additions**:
```markdown
## Workflow Expertise
- vision-elicitation: Vision canvas, problem-solution fit, 5W1H
- brainstorming: SCAMPER, mind mapping, what-if scenarios, five whys
- requirements-analysis: MoSCoW, Kano, dependency mapping, risk identification

## Brainstorming Techniques Available
1. **SCAMPER** (structured) - Systematic creativity through 7 lenses
2. **Mind Mapping** (structured) - Visual organization and connections
3. **What If Scenarios** (creative) - Explore radical possibilities
4. **First Principles** (creative) - Strip assumptions, rebuild from truths
5. **Five Whys** (deep) - Drill to root causes
6. **Yes And Building** (collaborative) - Momentum through additions
7. **Resource Constraints** (structured) - Force prioritization
8. **Assumption Reversal** (deep) - Challenge and flip beliefs
9. **Stakeholder Round Table** (collaborative) - Multiple perspectives
10. **Reverse Engineering** (creative) - Work backwards from outcome

## Vision Elicitation Methods
1. **Vision Canvas** - Complete vision framework
2. **Problem-Solution Fit** - Problem → gap → solution
3. **Outcome Mapping** - Desired outcomes and indicators
4. **5W1H Analysis** - Who, What, When, Where, Why, How

## Requirements Analysis Methods
1. **MoSCoW Prioritization** - Must, Should, Could, Won't
2. **Kano Model** - Basic, Performance, Excitement features
3. **Dependency Mapping** - Requirement relationships
4. **Risk Identification** - Potential risks and mitigations
5. **Constraint Analysis** - Time, budget, technical, compliance
```

**Benefits**:
- ✅ Documents Mary's capabilities
- ✅ Aligns with workflow structure
- ✅ Maintains simple markdown format

---

### Phase 5: Domain-Specific Questions (Simplified)

**Approach**: Embed domain questions in workflow YAML, not separate CSV or library

**Example**: Web App Requirements Workflow
```yaml
name: web-app-requirements
description: Web application requirements elicitation
phase: 1
author: Mary (Business Analyst)
domain: web_application

questions:
  general:
    - "Who are your target users?"
    - "Will this be a public or internal app?"
    - "Do you need user authentication?"
    - "What's the expected user volume?"
    - "Mobile-responsive required?"

  authentication:
    - "Email/password or social login?"
    - "Multi-factor authentication required?"
    - "Session timeout requirements?"

  data_model:
    - "What entities will the app manage?"
    - "Relationships between entities?"
    - "Data volume expectations?"
    - "Real-time updates needed?"

  deployment:
    - "Cloud hosting or on-premise?"
    - "Performance requirements (response time)?"
    - "Availability requirements (uptime SLA)?"

instructions: |
  You are Mary, gathering requirements for a web application.

  **Process**:
  1. Start with general questions to understand scope
  2. Based on user's answers, dive deeper into relevant areas:
     - If they mention auth → Ask authentication questions
     - If they discuss data → Ask data model questions
     - If they mention scale → Ask deployment questions
  3. Adapt your questions based on their responses
  4. Don't ask all questions - be selective and conversational

  **Output**: Requirements summary with priorities
```

**Benefits**:
- ✅ No separate question library to maintain
- ✅ Questions embedded with workflow context
- ✅ Easy to add new domain workflows
- ✅ Flexible - Mary adapts questions based on conversation

---

## Comparison: BMAD CSV vs GAO-Dev YAML

### BMAD Approach (CSV)

```csv
category,technique_name,description,facilitation_prompts,best_for,energy_level,typical_duration
structured,SCAMPER Method,Systematic creativity through seven lenses,S-What could you substitute?|C-What could you combine?|A-How could you adapt?|M-What could you modify?|P-Put to other uses?|E-What could you eliminate?|R-What if reversed?,methodical-improvement,moderate,20-25
```

**Pros**:
- Compact data format
- Easy to see all techniques at once
- Spreadsheet-friendly

**Cons**:
- ❌ No validation (unlike JSON Schema for YAML)
- ❌ Pipe-delimited prompts (fragile parsing)
- ❌ Hard to add complex metadata
- ❌ No variable resolution
- ❌ External dependency on BMAD structure
- ❌ Inconsistent with GAO-Dev patterns

### GAO-Dev Approach (YAML Workflows)

```yaml
name: scamper-brainstorming
description: SCAMPER Method - Systematic creativity
category: brainstorming
technique_type: structured
energy_level: moderate

facilitation_steps:
  - step: "substitute"
    prompt: "What could you substitute?"
    examples: ["What if we replaced X?"]

  - step: "combine"
    prompt: "What could you combine?"
    examples: ["What if we merged X and Y?"]

instructions: |
  You are Mary, facilitating SCAMPER...
```

**Pros**:
- ✅ Consistent with GAO-Dev patterns
- ✅ Self-contained workflows
- ✅ Variable resolution support
- ✅ Rich metadata and instructions
- ✅ No external dependencies
- ✅ Easy to add/modify/remove techniques
- ✅ Git-friendly diffs

**Cons**:
- More verbose (but clearer)
- Need to create multiple files (but more modular)

---

## Implementation Roadmap

### Epic 31 Revised Scope

**REMOVE**:
- ❌ Story 31.2 complexity: Loading 36 techniques from CSV
- ❌ BrainstormingEngine._load_techniques() CSV parsing
- ❌ CSV schema validation logic
- ❌ Dependency on BMAD CSV files
- ❌ DomainQuestionLibrary as separate class

**ADD**:
- ✅ 10 brainstorming technique workflows (YAML)
- ✅ 4 vision elicitation workflows (YAML)
- ✅ 5 requirements analysis workflows (YAML)
- ✅ Domain questions embedded in workflows
- ✅ Mary agent documentation updated

**Story Point Impact**:
- Old Story 31.2 (Brainstorming): 8 pts (load 36 CSV techniques)
- New Story 31.2 (Brainstorming): 5 pts (create 10 YAML workflows)
- **Reduction**: -3 pts (simpler, no CSV parsing)

---

### Story 31.2 Revised: Brainstorming Workflows (5 pts)

**Old Approach**:
1. Load brain-methods.csv (36 techniques)
2. Parse CSV with schema validation
3. BrainstormingEngine with technique library
4. Recommendation algorithm
5. Mind map generation

**New Approach**:
1. Create 10 brainstorming workflow YAML files
2. Each workflow is self-contained with facilitation steps
3. MaryOrchestrator selects workflows based on user needs
4. Mind map generation (same as before)

**Files to Create**:
```
gao_dev/workflows/1-analysis/brainstorming/
├── scamper.yaml
├── mind-mapping.yaml
├── what-if-scenarios.yaml
├── first-principles.yaml
├── five-whys.yaml
├── yes-and-building.yaml
├── resource-constraints.yaml
├── assumption-reversal.yaml
├── stakeholder-roundtable.yaml
└── reverse-engineering.yaml
```

**Implementation** (Epic 10 Integration):
```python
class MaryOrchestrator:
    def __init__(
        self,
        prompt_loader: PromptLoader,  # ← Epic 10 infrastructure
        conversation_manager: ConversationManager,
        analysis_service: AIAnalysisService
    ):
        self.prompt_loader = prompt_loader
        self.conversation_manager = conversation_manager
        self.analysis_service = analysis_service

    async def facilitate_brainstorming(
        self,
        user_request: str,
        technique: str = "scamper"
    ) -> BrainstormingSummary:
        """
        Facilitate brainstorming session using Epic 10 prompt system.
        """

        # Load workflow metadata
        workflow = self.workflow_registry.load_workflow(
            "1-analysis/brainstorming/workflow.yaml"
        )

        # Get prompt name for selected technique
        prompt_name = workflow.prompts[technique]  # e.g., "mary_brainstorming_scamper"

        # Load prompt template (Epic 10 PromptLoader)
        template = self.prompt_loader.load_prompt(prompt_name)

        # Render prompt with variables (Epic 10 reference resolution)
        rendered = self.prompt_loader.render_prompt(template, {
            "brainstorming_topic": user_request,
            "mary_persona": "@file:gao_dev/agents/mary.md"  # Auto-resolved!
        })

        # Create conversation session
        session = await self.conversation_manager.create_session(
            agent="Mary",
            workflow="brainstorming",
            context={"technique": technique}
        )

        # Multi-turn facilitation (~20 turns)
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

        # Generate mind map and insights
        mind_map = await self._generate_mind_map(session.extract_ideas())
        summary = await self._synthesize_session(session)

        return BrainstormingSummary(
            technique=technique,
            ideas=session.extract_ideas(),
            mind_map=mind_map,
            summary=summary
        )
```

**Benefits**:
- ✅ No CSV parsing complexity
- ✅ Uses Epic 10 PromptLoader (already implemented!)
- ✅ Reference resolution built-in (`@file:`, `{{variable}}`)
- ✅ Consistent with Brian, John, Winston patterns
- ✅ Easy to add new techniques (just add prompt YAML file)
- ✅ Plugin-friendly (can override prompts)

---

### Story 31.4 Revised: Domain-Specific Requirements (3 pts)

**Old Approach**:
1. Create DomainQuestionLibrary class
2. 5 domain question sets (web, mobile, API, CLI, data)
3. Hybrid detection (keyword + LLM)
4. Question selection algorithm

**New Approach**:
1. Create 5 domain-specific requirement workflows
2. Domain detection in BrianOrchestrator (already does scale detection)
3. Questions embedded in workflow YAML
4. No separate question library class

**Files to Create**:
```
gao_dev/workflows/1-analysis/requirements/
├── web-app-requirements.yaml
├── mobile-app-requirements.yaml
├── api-service-requirements.yaml
├── cli-tool-requirements.yaml
└── data-pipeline-requirements.yaml
```

**Implementation**:
```python
class BrianOrchestrator:
    async def _detect_domain(self, user_request: str) -> str:
        """
        Detect domain from user request.

        Uses LLM (already available via AIAnalysisService).
        """
        analysis = await self.analysis_service.analyze(
            f"Classify this request into domain: {user_request}

            Domains: web_app, mobile_app, api_service, cli_tool, data_pipeline, generic

            Return just the domain name."
        )
        return analysis.strip()

    async def assess_and_select_workflows(self, user_request: str):
        vagueness = await self._assess_vagueness(user_request)

        if vagueness > 0.6:
            # Detect domain
            domain = await self._detect_domain(user_request)

            # Select domain-specific requirements workflow
            if domain != "generic":
                workflow_path = f"gao_dev/workflows/1-analysis/requirements/{domain}-requirements.yaml"
                requirements = await self.mary.execute_workflow(workflow_path, user_request)
            else:
                # Generic requirements clarification
                requirements = await self.mary.clarify_requirements(user_request)

            return await self._analyze_with_clear_requirements(requirements)
```

**Benefits**:
- ✅ No separate question library class
- ✅ Questions embedded with context
- ✅ Domain detection in Brian (centralized)
- ✅ Easier to extend (add new domain = add YAML file)

**Reduction**: Story 31.4: 4 pts → 3 pts (-1 pt, simpler implementation)

---

## Final Recommendations

### 1. Abandon CSV Dependency ✅

**Do NOT**:
- Load `bmad/core/workflows/brainstorming/brain-methods.csv`
- Load `bmad/core/tasks/adv-elicit-methods.csv`
- Create CSV parsing logic
- Create CSV schema validation

**Instead**: Extract concepts, implement as workflows

---

### 2. Create 4 Workflows + 24 Prompts ✅

**Workflows** (4 files - metadata only):
1. `workflows/1-analysis/brainstorming/workflow.yaml`
2. `workflows/1-analysis/vision-elicitation/workflow.yaml`
3. `workflows/1-analysis/requirements-analysis/workflow.yaml`
4. `workflows/1-analysis/domain-requirements/workflow.yaml`

**Prompts** (24 files - LLM instructions):

**Brainstorming** (10 prompts):
1. `prompts/agents/mary_brainstorming_scamper.yaml`
2. `prompts/agents/mary_brainstorming_mindmap.yaml`
3. `prompts/agents/mary_brainstorming_whatif.yaml`
4. `prompts/agents/mary_brainstorming_first_principles.yaml`
5. `prompts/agents/mary_brainstorming_five_whys.yaml`
6. `prompts/agents/mary_brainstorming_yes_and.yaml`
7. `prompts/agents/mary_brainstorming_constraints.yaml`
8. `prompts/agents/mary_brainstorming_reversal.yaml`
9. `prompts/agents/mary_brainstorming_stakeholders.yaml`
10. `prompts/agents/mary_brainstorming_reverse.yaml`

**Vision Elicitation** (4 prompts):
1. `prompts/agents/mary_vision_canvas.yaml`
2. `prompts/agents/mary_vision_problem_solution_fit.yaml`
3. `prompts/agents/mary_vision_outcome_mapping.yaml`
4. `prompts/agents/mary_vision_5w1h.yaml`

**Requirements Analysis** (5 prompts):
1. `prompts/agents/mary_requirements_moscow.yaml`
2. `prompts/agents/mary_requirements_kano.yaml`
3. `prompts/agents/mary_requirements_dependency.yaml`
4. `prompts/agents/mary_requirements_risk.yaml`
5. `prompts/agents/mary_requirements_constraint.yaml`

**Domain-Specific** (5 prompts):
1. `prompts/agents/mary_domain_web_app.yaml`
2. `prompts/agents/mary_domain_mobile_app.yaml`
3. `prompts/agents/mary_domain_api_service.yaml`
4. `prompts/agents/mary_domain_cli_tool.yaml`
5. `prompts/agents/mary_domain_data_pipeline.yaml`

---

### 3. Simplify Story 31.2 and 31.4 ✅

**Story 31.2**: 8 pts → 5 pts
- Remove CSV parsing complexity
- Create 10 workflow YAML files instead
- MaryOrchestrator uses WorkflowExecutor (already exists)

**Story 31.4**: 4 pts → 3 pts
- Remove DomainQuestionLibrary class
- Embed questions in workflow YAML
- Domain detection in BrianOrchestrator

**Total Reduction**: -4 story points

---

### 4. Optional: Add Mary Checklists (Epic 32) ⏳

**Defer to Epic 32**:
- Vision elicitation quality checklist
- Requirements clarity checklist
- Stakeholder coverage checklist
- Success metrics checklist
- Risk assessment checklist

**Benefit**: Quality gates for Mary's workflows
**Cost**: 2-3 story points
**Priority**: Low (nice to have)

---

## Revised Epic 31 Total (With Epic 10 Integration)

**Original**: 32 pts (with CRITICAL fixes from risk assessment)
**With BMAD Mapping + Epic 10 Integration**: 28 pts

**Breakdown**:
- Story 31.0: BMAD CSV Validation → **REMOVED** (no CSV dependency!)
- Story 31.1: Vision Elicitation: 5 pts (1 workflow + 4 prompts)
- Story 31.2: Brainstorming: 5 pts (1 workflow + 10 prompts)
- Story 31.3: Requirements Analysis: 5 pts (1 workflow + 5 prompts)
- Story 31.4: Domain Requirements: 3 pts (1 workflow + 5 prompts)
- Story 31.5: Integration & Docs: 5 pts
- Story 31.6: Mary → John Handoff: 3 pts
- **Total**: **28 pts** (2 weeks, realistic)

**File Deliverables**:
- **4 Workflow Files** (metadata) in `gao_dev/workflows/1-analysis/`
- **24 Prompt Files** (LLM instructions) in `gao_dev/prompts/agents/`
- **28 Total Files**

---

## Success Criteria

**Epic 31 Complete When**:
- ✅ 4 workflow files created (metadata only) in `gao_dev/workflows/1-analysis/`
- ✅ 24 prompt files created (LLM instructions) in `gao_dev/prompts/agents/`
- ✅ All workflows/prompts follow Epic 10 patterns
- ✅ No CSV dependencies
- ✅ Mary agent documentation updated
- ✅ MaryOrchestrator uses PromptLoader (Epic 10)
- ✅ Prompts use `@file:` and `{{variable}}` syntax
- ✅ Domain detection in BrianOrchestrator
- ✅ 60+ tests passing (per CRITICAL 4 from risk assessment)
- ✅ Mary → John handoff working
- ✅ User guide with examples
- ✅ All workflows tested end-to-end
- ✅ Consistent with Brian, John, Winston, Bob, Amelia, Murat patterns

**NOT Required**:
- ❌ CSV parsing logic
- ❌ CSV schema validation
- ❌ BrainstormingEngine._load_techniques() from CSV
- ❌ DomainQuestionLibrary class (questions embedded in prompts)
- ❌ Dependency on BMAD CSV files
- ❌ Loading all 36+39 techniques (just 10+4+5+5=24 prompts)
- ❌ Separate workflow file per technique (1 workflow references many prompts)

---

## Conclusion

Epic 31's original CSV-based approach violated GAO-Dev's established architectural patterns. By properly mapping BMAD concepts to GAO-Dev's workflow + prompt system (Epic 10), we achieve:

1. **Epic 10 Integration**: Use existing PromptLoader, reference resolution, variable substitution
2. **Architectural Consistency**: Workflows (metadata) + Prompts (LLM instructions) separation
3. **Simplicity**: No CSV parsing, validation, or error handling
4. **Modularity**: 4 workflows reference 24 prompts (clean separation of concerns)
5. **Extensibility**: Easy to add techniques (drop in new prompt YAML file)
6. **Reduced Scope**: 28 pts instead of 32 pts (-4 pts from original)
7. **Maintainability**: Self-documenting prompts with metadata
8. **Independence**: No external BMAD dependency
9. **Plugin-Friendly**: Override prompts without code changes
10. **Consistency**: Same pattern as Brian, John, Winston, Bob, Amelia, Murat

**The user is right**: Extract BMAD's valuable concepts and implement them in GAO-Dev's way (Epic 10 patterns), not copy BMAD's structure directly.

---

**Next Steps**:
1. Review and approve this mapping
2. Update Epic 31 PRD and Architecture documents
3. Revise Story 31.2 and 31.4 acceptance criteria
4. Remove Story 31.0 (no CSV validation needed)
5. Begin implementation with workflow creation

**Status**: ✅ **READY FOR REVIEW**

