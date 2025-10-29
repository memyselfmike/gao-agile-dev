# Epic 7.2 Enhancement Analysis: Scale-Adaptive Workflow Architecture

**Date**: 2025-10-29
**Context**: Deep dive into BMAD workflows to inform Epic 7.2 architecture

---

## Executive Summary

After exploring the BMAD workflow directory, we've identified critical enhancements needed for Epic 7.2:

1. **55+ Workflows Available**: BMAD contains comprehensive workflows across 4 phases (not just PRD/Story workflows)
2. **Scale-Adaptive Approach**: Workflows route based on project complexity (Level 0-4) - MISSING from Epic 7.2
3. **Workflow Orchestrator Agent**: Need "Brian" agent (Workflow Orchestrator) to implement scale-adaptive routing
4. **Terminology**: Reference as "workflows in GAO-Dev" not "bmm workflows"

---

## BMAD Workflow Inventory (55+ Workflows)

### Phase 1: Analysis (Optional)
**7 workflows** for discovery and requirements gathering:

- `brainstorm-game` - Game concept ideation using 5 methodologies
- `brainstorm-project` - Software solution exploration
- `document-project` - Brownfield codebase documentation
  - Sub-workflows: `deep-dive`, `full-scan`
- `game-brief` - Structured game design foundation
- `product-brief` - Strategic product planning
- `research` - Multi-mode research (market/technical/deep prompt)

### Phase 2: Planning (Required)
**5 workflows** for scale-adaptive planning:

- `prd` - Product Requirements Document (Level 2-4 software)
- `gdd` - Game Design Document (all game projects)
- `tech-spec` - Technical specification (Level 0-2 software)
- `create-ux-design` - UX/UI design workflows
- `narrative` - Narrative design for games

### Phase 3: Solutioning (Levels 3-4)
**2 workflows** for architecture:

- `architecture` - Overall system architecture with ADRs
- `solutioning-gate-check` - Architecture validation checkpoint

### Phase 4: Implementation (Iterative)
**10 workflows** for story-based development:

- `create-story` - Draft story from TODO section
- `story-ready` - Approve drafted story for development
- `story-context` - Generate expertise injection XML
- `story-done` - Mark story complete after DoD
- `dev-story` - Implement story
- `review-story` - Quality validation
- `correct-course` - Handle issues/changes
- `retrospective` - Epic learnings capture
- `sprint-planning` - Sprint planning workflow
- `epic-tech-context` - Epic-specific technical context

### Test Architecture Workflows
**9 workflows** for test strategy:

- `atdd` - Acceptance Test-Driven Development
- `automate` - Test automation strategy
- `ci` - Continuous Integration setup
- `framework` - Test framework selection
- `nfr-assess` - Non-functional requirements assessment
- `test-design` - Test design patterns
- `test-review` - Test quality review
- `trace` - Requirements traceability

### Helper Workflows
**3 workflows** for coordination:

- `workflow-status` - **CRITICAL**: Universal entry point, determines scale level and routes workflows
- `sprint-status` - Sprint progress tracking
- Initialization workflows

---

## Scale-Adaptive Approach (Core BMAD Innovation)

### Scale Levels (Level 0-4)

BMAD routes workflows based on project complexity:

| Level | Scope | Stories | Epics | Workflows |
|-------|-------|---------|-------|-----------|
| **Level 0** | Single atomic change | 1 story | 0 | tech-spec only → Implementation |
| **Level 1** | Small feature | 2-10 stories | 1 epic | tech-spec → Implementation |
| **Level 2** | Medium project | 5-15 stories | 1-2 epics | PRD + Epics → tech-spec → Implementation |
| **Level 3** | Large project | 12-40 stories | 2-5 epics | PRD + Epics → Architecture → Implementation |
| **Level 4** | Enterprise | 40+ stories | 5+ epics | PRD + Epics → Architecture → Implementation |

### Scale-Adaptive Routing Logic

```
User Prompt → Brian (Workflow Orchestrator)
    ↓
Analyze:
  - Project type (game/software)
  - Context (greenfield/brownfield)
  - Complexity assessment → Assign Level 0-4
  - Domain/technology hints
    ↓
Route to appropriate workflow sequence:
  - Level 0-1: tech-spec → stories → implementation
  - Level 2: PRD → epics → tech-spec → implementation
  - Level 3-4: PRD → epics → architecture → implementation
    ↓
Execute workflows in sequence
```

### Key Routing Decisions

1. **Brownfield vs Greenfield**
   - Brownfield: Must run `document-project` workflow first
   - Greenfield: Can skip directly to planning

2. **Project Type**
   - Game projects: Always use `gdd` workflow
   - Software projects: Use `prd` or `tech-spec` based on scale

3. **Complexity Assessment**
   - Analyze prompt for scope indicators
   - Ask clarifying questions if scope unclear
   - Assign scale level (0-4)
   - Determine required workflow sequence

---

## The "Brian" Agent - Workflow Orchestrator

### Agent Definition

**Name**: Brian
**Role**: Workflow Orchestrator & Scale Analyst
**Persona**: Strategic thinker who sees the big picture and optimizes workflow paths

**Responsibilities**:
1. Analyze initial prompt to assess project complexity
2. Determine scale level (0-4) using AI analysis
3. Identify project type (game/software) and context (greenfield/brownfield)
4. Select appropriate workflow sequence based on scale
5. Orchestrate workflow execution across phases
6. Ask clarifying questions when scope is ambiguous
7. Monitor workflow progress and adapt as needed

### Brian vs WorkflowSelector (Story 7.2.1)

**Current Epic 7.2.1**: WorkflowSelector class (non-agent code)
**Enhancement**: Make Brian a full agent with decision-making authority

### Brian's Decision Framework

```python
class Brian:
    """
    Workflow Orchestrator Agent

    Brian analyzes prompts and orchestrates workflow sequences
    based on scale-adaptive principles.
    """

    def analyze_project_complexity(self, prompt: str) -> ScaleLevel:
        """
        Analyze prompt to determine scale level (0-4).

        Considers:
        - Explicit scope indicators ("simple", "enterprise-scale")
        - Feature count estimates
        - Technical complexity hints
        - Team size implications
        - Timeline indicators
        """
        pass

    def determine_workflow_sequence(
        self,
        scale_level: ScaleLevel,
        project_type: ProjectType,
        context: ProjectContext
    ) -> List[Workflow]:
        """
        Build complete workflow sequence based on scale.

        Level 0: [tech-spec, create-story, dev-story]
        Level 1: [tech-spec, create-story (x3), dev-story (x3)]
        Level 2: [prd, tech-spec, create-story loop, dev-story loop]
        Level 3-4: [prd, architecture, tech-spec, create-story loop, dev-story loop]
        """
        pass

    def orchestrate_workflow_execution(
        self,
        workflow_sequence: List[Workflow]
    ) -> WorkflowResult:
        """
        Execute workflow sequence, coordinating agents.

        Calls Mary, John, Winston, Sally, Bob, Amelia, Murat
        as needed per workflow step.
        """
        pass
```

---

## What's Missing from Epic 7.2

### Critical Gaps

1. **Scale-Adaptive Architecture**
   - Epic 7.2.1 (WorkflowSelector) doesn't mention scale levels
   - No Level 0-4 assessment
   - No routing logic based on complexity
   - Missing: Scale level determination algorithm

2. **Brian Agent**
   - Epic 7.2.1 creates a `WorkflowSelector` class, not an agent
   - Should be "Brian the Workflow Orchestrator" agent
   - Needs: Agent definition file, persona, full autonomy

3. **Comprehensive Workflow Registry**
   - Epic assumes only PRD/Story workflows exist
   - Need to load ALL 55+ workflows from BMAD
   - Missing: Phase 1 (Analysis), Phase 3 (Solutioning), Test Architecture

4. **Workflow Sequencing**
   - Epic 7.2.2 (Workflow Executor) executes single workflow
   - Missing: Multi-workflow sequences (PRD → Architecture → Stories)
   - Missing: Phase transitions

5. **Just-In-Time Design**
   - BMAD creates tech-specs one epic at a time (JIT approach)
   - Epic 7.2 doesn't capture this progressive elaboration
   - Missing: Epic-level workflow injection during implementation

6. **Terminology**
   - Stories reference "bmm workflows" or "BMAD workflows"
   - Should be: "workflows in GAO-Dev" (as BMAD is implementation detail)

---

## Recommended Epic 7.2 Enhancements

### Option A: Extend Existing Stories

**Story 7.2.1 Enhancement**: Create Brian Agent & Scale-Adaptive Selector
- Change from `WorkflowSelector` class to `Brian` agent
- Add scale level assessment (Level 0-4)
- Implement complexity analysis using AI
- Build workflow sequence based on scale
- **Impact**: +2 story points (5 pts total)

**Story 7.2.2 Enhancement**: Add Multi-Workflow Sequencing
- Execute workflow sequences, not single workflows
- Handle phase transitions (Phase 2 → Phase 3 → Phase 4)
- Support JIT tech-spec generation per epic
- **Impact**: +2 story points (7 pts total)

**Story 7.2.3 Enhancement**: Update for Scale-Adaptive Benchmarks
- Benchmark config specifies scale level OR lets Brian decide
- Support workflow sequences in benchmarks
- **Impact**: +1 story point (4 pts total)

**New Story 7.2.6**: Load Complete Workflow Registry (2 pts)
- Load all 55+ workflows from bmad/bmm/workflows/
- Parse workflow.yaml files
- Build workflow dependency graph
- Enable discovery of all available workflows
- Update terminology: "workflows in GAO-Dev"

**Updated Epic Total**: 20 story points (was 15)

### Option B: Create Epic 7.2.1 (Sub-Epic)

Create **Epic 7.2.1**: Scale-Adaptive Workflow Architecture (5 pts)
- Story 7.2.1.1: Create Brian Agent (3 pts)
- Story 7.2.1.2: Implement Scale Level Assessment (2 pts)

Keep main Epic 7.2 focused on execution, add 7.2.1 for intelligence layer.

**Total**: Epic 7.2 (15 pts) + Epic 7.2.1 (5 pts) = 20 pts

---

## Implementation Recommendation

### Recommended Approach: Option A (Extend Existing Stories)

**Why**:
- Maintains Epic 7.2 cohesion
- Adds missing scale-adaptive logic to existing stories
- Avoids complexity of sub-epics
- Clear story progression

### Updated Story Breakdown

1. **Story 7.2.1: Create Brian Agent & Scale-Adaptive Workflow Selection** (5 pts, was 3)
   - Create Brian agent persona and definition file
   - Implement scale level assessment (Level 0-4)
   - AI-powered complexity analysis
   - Workflow sequence building based on scale
   - Clarifying questions for ambiguous scope

2. **Story 7.2.2: Add Multi-Workflow Sequence Executor** (7 pts, was 5)
   - Execute workflow sequences (multi-workflow)
   - Phase transition handling
   - JIT tech-spec generation per epic
   - State management across workflows
   - Artifact collection from multiple workflows

3. **Story 7.2.3: Refactor Benchmark for Scale-Adaptive Testing** (4 pts, was 3)
   - Support scale level in benchmark config
   - Test workflow sequences
   - Metrics for multi-workflow execution

4. **Story 7.2.4: Add Clarification Dialog** (2 pts, unchanged)
   - As originally planned

5. **Story 7.2.5: Integration Testing** (2 pts, unchanged)
   - Test scale-adaptive routing
   - Test workflow sequences
   - Test all scale levels (0-4)

6. **Story 7.2.6: Load Complete Workflow Registry** (2 pts, NEW)
   - Load all 55+ BMAD workflows
   - Parse workflow definitions
   - Build workflow graph
   - Enable workflow discovery
   - Update terminology throughout

**New Epic Total**: 22 story points

---

## Brian Agent Specification

### Agent Profile

```markdown
# Brian - Workflow Orchestrator

**Full Name**: Brian Thompson
**Role**: Workflow Orchestrator & Project Strategist
**Age**: 42
**Background**: 15 years in software project management, certified PMP

## Personality
- Strategic thinker who sees the big picture
- Excellent at assessing project complexity
- Optimizes for appropriate process overhead (not too heavy, not too light)
- Patient and thoughtful, never rushes to conclusions
- Asks clarifying questions when scope is unclear

## Expertise
- Project complexity assessment
- Scale-adaptive methodology (BMAD/Agile/Waterfall)
- Workflow optimization and sequencing
- Risk assessment and mitigation
- Team capacity planning

## Working Style
- Analyzes before acting
- Considers multiple workflow paths
- Optimizes for team success, not methodology perfection
- Adapts process to project, not project to process
- Clear communicator of workflow rationale

## Responsibilities
1. Analyze initial prompts to assess complexity
2. Determine appropriate scale level (0-4)
3. Select optimal workflow sequence
4. Orchestrate multi-phase workflows
5. Monitor progress and adapt workflows as needed
6. Ask clarifying questions when scope is ambiguous
7. Explain workflow decisions to users

## Tools
- Workflow registry access
- AI-powered complexity analysis
- Project context analyzer
- Scale level determination algorithms
- Clarification question generator
```

### Agent File Location

`gao_dev/agents/brian.md` - Following existing agent pattern

---

## Terminology Updates

### Current (Inconsistent)
- "bmm workflows"
- "BMAD workflows"
- "workflows from bmad/bmm/workflows/"

### Updated (Consistent)
- "workflows in GAO-Dev"
- "GAO-Dev workflows"
- "available workflows"

**Rationale**: BMAD is an implementation detail. From the user perspective, these are "workflows that GAO-Dev uses" not "BMAD's workflows."

---

## Next Steps

1. **Review this analysis** with team/user
2. **Decide**: Option A (extend stories) vs Option B (sub-epic)
3. **Update Epic 7.2 stories** with scale-adaptive enhancements
4. **Create brian.md** agent definition
5. **Update sprint-status.yaml** with new story points
6. **Begin implementation** starting with Story 7.2.1

---

## Appendix: Complete Workflow List

### Phase 1: Analysis
1. brainstorm-game
2. brainstorm-project
3. document-project (with deep-dive, full-scan sub-workflows)
4. game-brief
5. product-brief
6. research

### Phase 2: Planning
7. prd
8. gdd
9. tech-spec
10. create-ux-design
11. narrative

### Phase 3: Solutioning
12. architecture
13. solutioning-gate-check

### Phase 4: Implementation
14. create-story
15. story-ready
16. story-context
17. story-done
18. dev-story
19. review-story
20. correct-course
21. retrospective
22. sprint-planning
23. epic-tech-context

### Test Architecture
24. atdd
25. automate
26. ci
27. framework
28. nfr-assess
29. test-design
30. test-review
31. trace

### Helpers
32. workflow-status (UNIVERSAL ENTRY POINT)
33. sprint-status
34. workflow-status/init

**Total**: 34+ major workflows (55+ including sub-workflows and variations)
