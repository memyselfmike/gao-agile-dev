# Product Requirements Document: Epic 31 - Full Mary Integration

**Epic ID**: Epic 31
**Feature**: Interactive Brian Chat - Full Mary (Business Analyst) Integration
**Version**: 1.0
**Created**: 2025-11-10
**Owner**: Bob (Scrum Master)
**Status**: Planning

---

## Executive Summary

Epic 31 completes the Mary agent (8th agent in GAO-Dev) by implementing full BMAD (Business Management and Development) business analyst capabilities. While Epic 30 provided minimal Mary with basic requirements clarification, Epic 31 adds comprehensive business analysis workflows including vision elicitation, brainstorming facilitation, mind mapping, advanced requirements analysis, and domain-specific question libraries.

**Key Value**: Transforms vague user ideas into well-defined product visions through intelligent, LLM-powered conversational discovery. This ensures GAO-Dev builds the right thing by deeply understanding user needs before creating PRDs and starting implementation.

**Scope**: 25 story points over 2 weeks (5 stories)
**Dependencies**: Epic 30 (Interactive Brian Chat), Epic 21 (AIAnalysisService), Epic 26 (ConversationManager)

---

## Problem Statement

### Current Limitations

After Epic 30, Mary has minimal capabilities:
- Basic requirements clarification only (4-5 questions)
- No brainstorming facilitation
- No vision elicitation techniques
- No problem framing workshops
- No domain-specific intelligence
- Limited to reactive question-asking

### Problems This Creates

1. **Insufficient Vision Clarity**: Users with vague ideas get basic questions but no help articulating their vision
2. **Missed Innovation Opportunities**: No brainstorming means fewer creative solutions explored
3. **Generic Requirements**: Domain-agnostic questions miss context-specific details
4. **Shallow Analysis**: No MoSCoW, Kano, or dependency analysis means weak prioritization
5. **Incomplete BMAD Methodology**: GAO-Dev lacks full business analysis capabilities promised by BMAD framework

### Why Full Mary Matters

Interactive Brian Chat is only as good as the requirements Mary elicits. Without full business analyst capabilities:
- PRDs built on shallow understanding lead to wasted implementation effort
- Users struggle to articulate what they really want
- GAO-Dev misses opportunities to guide users toward better solutions
- The BMAD methodology remains incomplete (Mary is the 8th and final agent)

---

## Goals & Success Criteria

### Primary Goals

1. **Complete Mary Agent**: Implement all 8 GAO-Dev agents with full BMAD business analyst workflows
2. **Vision Elicitation**: Help users articulate vague ideas into clear product visions
3. **Brainstorming Excellence**: Facilitate creative exploration using multiple brainstorming techniques
4. **Advanced Analysis**: Perform MoSCoW, Kano, dependency mapping, risk identification
5. **Domain Intelligence**: Ask contextually relevant questions based on project type

### Success Metrics

- All 8 GAO-Dev agents operational (Mary completes the team)
- Mary can apply 5+ different clarification strategies intelligently
- 90% of vague requests successfully clarified and enriched
- PRDs created after Mary's analysis are 95% relevant (vs 70% baseline)
- User satisfaction: "Mary helped me understand what I really needed"
- 15+ integration tests passing (>90% coverage)
- Response time: Vision elicitation <3 minutes, brainstorming session 10-30 minutes

### Non-Goals (Out of Scope)

- Visual mind mapping tools (text-based diagrams only)
- Multi-user brainstorming sessions (single user only)
- Integration with external BA tools (JIRA, Miro, etc.)
- Automated PRD generation from Mary's output (handed to John manually)

---

## User Stories

### Story 31.1: Vision Elicitation Workflows (5 points)

**As a** user with a vague idea
**I want** Mary to help me articulate my vision clearly
**So that** we can create a well-defined product vision before building anything

**Acceptance Criteria**:
- Vision canvas workflow implemented
- Problem-solution fit analysis
- Outcome mapping workflow
- 5W1H (Who, What, When, Where, Why, How) analysis
- MaryOrchestrator enhanced with vision elicitation strategy selection
- 8+ tests passing

### Story 31.2: Brainstorming & Mind Mapping (8 points)

**As a** user exploring solutions
**I want** Mary to facilitate brainstorming sessions with multiple techniques
**So that** we can explore creative approaches and find the best solution

**Acceptance Criteria**:
- Brainstorming facilitation with 10+ techniques from BMAD library
- Text-based mind map generation (mermaid diagrams)
- SCAMPER technique (Substitute, Combine, Adapt, Modify, Put, Eliminate, Reverse)
- "How Might We" framing
- Affinity mapping and grouping
- 12+ tests passing

### Story 31.3: Advanced Requirements Analysis (5 points)

**As a** product team
**I want** Mary to perform deep requirements analysis
**So that** we capture all edge cases, constraints, and priorities

**Acceptance Criteria**:
- MoSCoW prioritization (Must, Should, Could, Won't)
- Kano model analysis (Basic, Performance, Excitement features)
- Dependency mapping between requirements
- Risk identification and analysis
- Constraint analysis (time, budget, technical, compliance)
- 8+ tests passing

### Story 31.4: Domain-Specific Question Libraries (4 points)

**As a** user in a specific domain (web app, mobile, API, CLI, data pipeline)
**I want** Mary to ask domain-relevant questions
**So that** requirements are contextually appropriate and comprehensive

**Acceptance Criteria**:
- Web application question library
- Mobile app question library
- API/Backend service question library
- CLI tool question library
- Data pipeline question library
- Domain detection from user input
- 6+ tests passing

### Story 31.5: Integration & Documentation (3 points)

**As a** developer and user
**I want** comprehensive tests, documentation, and examples
**So that** Mary's capabilities are reliable, discoverable, and easy to use

**Acceptance Criteria**:
- 15+ integration tests covering all workflows
- User guide: "Working with Mary - Business Analyst"
- 5+ examples: vision elicitation, brainstorming, requirements analysis
- Performance validation (<3 min vision elicitation, <500ms question selection)
- Updated agent documentation

---

## Epic Breakdown

### Week 1

**Monday-Tuesday (5 points)**
- Story 31.1: Vision Elicitation Workflows
- Implement vision canvas, problem-solution fit, outcome mapping, 5W1H
- Enhance MaryOrchestrator with strategy selection

**Wednesday-Friday (8 points start)**
- Story 31.2: Brainstorming & Mind Mapping
- Build brainstorming engine with 10+ techniques
- Implement mind map generation
- Add SCAMPER, HMW framing, affinity mapping

### Week 2

**Monday (8 points finish)**
- Complete Story 31.2

**Tuesday-Wednesday (5 points)**
- Story 31.3: Advanced Requirements Analysis
- Implement MoSCoW, Kano, dependency mapping, risk analysis

**Thursday (4 points)**
- Story 31.4: Domain-Specific Question Libraries
- Build libraries for 5 domains with detection logic

**Friday (3 points)**
- Story 31.5: Integration & Documentation
- Write 15+ integration tests
- Create user guide and examples

---

## Technical Architecture Overview

### Mary's Expanded Capabilities

```
Mary (Business Analyst)
├── Requirements Clarification (Epic 30 - Complete)
│   └── Basic 4-5 questions
│
├── Vision Elicitation (Story 31.1)
│   ├── Vision canvas
│   ├── Problem-solution fit
│   ├── Outcome mapping
│   └── 5W1H analysis
│
├── Brainstorming (Story 31.2)
│   ├── Facilitated brainstorming (10+ techniques)
│   ├── Mind mapping (text/mermaid)
│   ├── SCAMPER technique
│   ├── "How Might We" framing
│   └── Affinity mapping
│
├── Advanced Requirements (Story 31.3)
│   ├── MoSCoW prioritization
│   ├── Kano model analysis
│   ├── Dependency mapping
│   ├── Risk identification
│   └── Constraint analysis
│
└── Domain-Specific Analysis (Story 31.4)
    ├── Web app questions
    ├── Mobile app questions
    ├── API service questions
    ├── CLI tool questions
    └── Data pipeline questions
```

### Integration with Brian

Brian's workflow selection delegates to Mary based on request vagueness:

```python
class BrianOrchestrator:
    async def assess_and_select_workflows(self, initial_prompt: str):
        vagueness = await self._assess_vagueness(initial_prompt)

        if vagueness > 0.6:
            # Very vague - Mary selects best strategy
            mary_strategy = await self.mary.select_clarification_strategy(
                initial_prompt,
                vagueness
            )

            if mary_strategy == "vision_elicitation":
                requirements = await self.mary.elicit_vision(initial_prompt)
            elif mary_strategy == "brainstorming":
                requirements = await self.mary.facilitate_brainstorming(initial_prompt)
            elif mary_strategy == "advanced_requirements":
                requirements = await self.mary.analyze_requirements(initial_prompt)
            else:  # basic_clarification
                requirements = await self.mary.clarify_requirements(initial_prompt)

            return await self._analyze_with_clear_requirements(requirements)
```

### Key Components

1. **MaryOrchestrator** (enhanced from Epic 30)
   - Strategy selection logic
   - Vision elicitation workflows
   - Brainstorming facilitation
   - Advanced requirements analysis
   - Domain detection

2. **BrainstormingEngine** (new)
   - Technique library (BMAD methods)
   - Facilitation prompt generation
   - Idea capture and organization
   - Mind map generation

3. **RequirementsAnalyzer** (new)
   - MoSCoW prioritization
   - Kano model analysis
   - Dependency mapping
   - Risk assessment

4. **DomainQuestionLibrary** (new)
   - 5 domain-specific libraries
   - Context-aware question selection
   - Domain detection from user input

### Technology Stack

- **LLM Integration**: AIAnalysisService (Epic 21) for all conversational AI
- **Conversation Management**: ConversationManager (Epic 26) for multi-turn dialogues
- **Workflow Execution**: WorkflowRegistry and WorkflowExecutor
- **Diagram Generation**: Mermaid syntax for text-based mind maps
- **Storage**: Requirements summaries and brainstorming outputs to `.gao-dev/mary/`

---

## Dependencies

### Upstream Dependencies (Complete)

- Epic 30 Story 30.8: Minimal Mary Integration (basic clarification)
- Epic 21: AIAnalysisService (LLM calls for conversational discovery)
- Epic 26: ConversationManager (multi-turn dialogue management)
- Epic 25: FastContextLoader (project context awareness)

### Downstream Dependencies (Consuming Epic 31)

- Epic 30 Story 30.3: Conversational Brian (delegates to Mary)
- Future: John (Product Manager) receives Mary's requirements for PRD creation

### No Blockers

All dependencies are complete. Epic 31 is ready to implement after Epic 30.

---

## User Experience Flow

### Example 1: Vision Elicitation

```
User: "I want to build something for managing projects"

Brian: "This request needs clarification. Bringing in Mary..."

Mary: "I'd love to help you clarify your vision! Let's explore this together."
      "First, who would use this project management tool?"

User: "Small development teams, maybe 5-10 people"

Mary: "Got it. What specific pain points are they experiencing with current tools?"

User: "Tools like JIRA are too complex, and simple tools lack features"

Mary: [Continues 5W1H and problem-solution fit analysis...]

Mary: "Here's what I'm hearing: [Requirements Summary]
       - Target: Small dev teams (5-10 people)
       - Problem: Complexity vs simplicity trade-off
       - Key requirement: Simple UI with essential features only
       Would you like to brainstorm specific features, or should I hand this to John for PRD?"

User: "Let's brainstorm features"

Mary: [Launches brainstorming workflow with SCAMPER technique...]
```

### Example 2: Brainstorming Session

```
User: "I need ideas for making authentication better"

Brian: "Let me bring in Mary for brainstorming..."

Mary: "Let's explore authentication improvements! I can facilitate this with several techniques:
       1. SCAMPER (systematic innovation)
       2. What If Scenarios (explore possibilities)
       3. Problem Reversal (flip assumptions)
       4. Mind Mapping (organize ideas visually)

       Which approach interests you?"

User: "SCAMPER sounds good"

Mary: "Great! SCAMPER helps us innovate systematically. Let's start:

       S - SUBSTITUTE: What if we substituted passwords with something else?
       What comes to mind?"

User: "Biometrics? Hardware keys?"

Mary: "Excellent! Building on that...
       C - COMBINE: Could we combine biometrics with something for better security?
       What would make sense?"

User: "Biometrics + device recognition?"

Mary: [Continues through SCAMPER, generates mind map, summarizes ideas...]
```

---

## Risks & Mitigations

### Risk 1: Brainstorming Sessions Too Long

**Impact**: High
**Probability**: Medium
**Mitigation**:
- Set time limits per technique (15-20 min default)
- Allow user to skip/switch techniques
- Provide "quick brainstorm" mode (5-10 min)

### Risk 2: LLM Costs for Long Sessions

**Impact**: Medium
**Probability**: Medium
**Mitigation**:
- Use Haiku model for most Mary interactions (Epic 30 pattern)
- Only use Sonnet for complex synthesis
- Cache conversation context to reduce token usage
- Estimate: $0.05-0.15 per vision elicitation session

### Risk 3: Domain Detection Accuracy

**Impact**: Medium
**Probability**: Low
**Mitigation**:
- Use keyword matching + LLM classification (hybrid approach)
- Allow user to explicitly specify domain
- Fall back to generic questions if uncertain
- Log misclassifications for improvement

### Risk 4: Integration Complexity with Brian

**Impact**: Medium
**Probability**: Low
**Mitigation**:
- Build on proven Epic 30 delegation pattern
- Clear state machine for Mary strategy selection
- Comprehensive integration tests (Story 31.5)

### Risk 5: User Fatigue in Long Workflows

**Impact**: High
**Probability**: Medium
**Mitigation**:
- Checkpoint questions: "Want to continue or move forward?"
- Save session state for resumption later
- Provide summaries at each milestone
- Allow skip/fast-forward options

---

## References

### BMAD Methodology

- Brainstorming techniques: `bmad/core/workflows/brainstorming/brain-methods.csv` (36 techniques)
- Advanced elicitation: `bmad/core/tasks/adv-elicit-methods.csv` (39 methods)
- Vision elicitation: Problem-solution fit, outcome mapping, 5W1H analysis
- Requirements analysis: MoSCoW, Kano model, dependency mapping

### Existing Implementation

- Epic 30 Story 30.8: Minimal Mary (`docs/features/interactive-brian-chat/stories/epic-30/story-30.8-minimal-mary-integration.md`)
- Epic 31 Overview: `docs/features/interactive-brian-chat/epics/epic-31-full-mary-integration.md`
- Mary agent config: `gao_dev/config/agents/mary.yaml`
- Mary persona: `gao_dev/agents/mary.md`

### Related Epics

- Epic 30: Interactive Brian Chat Interface
- Epic 21: AI Analysis Service Integration
- Epic 26: Multi-Agent Ceremony Infrastructure

---

## Timeline

**Start Date**: After Epic 30 complete
**Duration**: 2 weeks (10 working days)
**Total Points**: 25 story points
**Velocity**: ~12.5 points/week

### Milestones

- **Day 2**: Vision elicitation complete (Story 31.1)
- **Day 5**: Brainstorming complete (Story 31.2)
- **Day 7**: Advanced requirements complete (Story 31.3)
- **Day 8**: Domain libraries complete (Story 31.4)
- **Day 10**: Integration & docs complete (Story 31.5), Epic 31 done

---

## Acceptance Criteria (Epic Level)

- [ ] All 5 stories complete and merged
- [ ] 15+ integration tests passing
- [ ] All 8 GAO-Dev agents operational (Mary completes the team)
- [ ] Mary can intelligently select from 5+ clarification strategies
- [ ] Vision elicitation workflows functional (canvas, problem-solution fit, outcome mapping, 5W1H)
- [ ] Brainstorming with 10+ techniques from BMAD library
- [ ] Mind map generation (mermaid diagrams)
- [ ] Advanced requirements analysis (MoSCoW, Kano, dependencies, risks)
- [ ] Domain-specific question libraries (5 domains)
- [ ] User guide published with examples
- [ ] Performance: Vision elicitation <3 min, question selection <500ms
- [ ] Manual testing: Full vision-to-PRD flow validated
- [ ] Git commit: `feat(epic-31): Full Mary Integration - Complete (25 pts)`

---

## Open Questions

1. **Should Mary suggest workflows proactively?** (e.g., "I notice you're unsure - want to try brainstorming?")
   - Decision: Yes, Mary suggests workflows when detecting uncertainty (Story 31.1)

2. **How much automation in mind mapping?** (fully automated vs user-guided)
   - Decision: Hybrid - Mary generates initial map, user can refine (Story 31.2)

3. **Should requirements be stored in DB or markdown?**
   - Decision: Markdown in `.gao-dev/mary/` for transparency, lightweight storage

4. **Integration with John for PRD creation?**
   - Decision: Deferred to Epic 32 (Mary → John handoff). Epic 31: Mary outputs requirements, user manually proceeds

---

## Appendix: Story Point Breakdown

| Story | Points | Complexity | Risk | Duration |
|-------|--------|------------|------|----------|
| 31.1 Vision Elicitation | 5 | Medium | Low | 1-2 days |
| 31.2 Brainstorming & Mind Mapping | 8 | High | Medium | 3-4 days |
| 31.3 Advanced Requirements | 5 | Medium | Low | 2 days |
| 31.4 Domain Libraries | 4 | Low | Low | 1 day |
| 31.5 Integration & Docs | 3 | Low | Low | 1 day |
| **Total** | **25** | - | - | **10 days** |

---

**Document Status**: Complete
**Next Steps**: Review PRD, approve, create story files
**Author**: Bob (Scrum Master)
**Reviewers**: Brian (Workflow Coordinator), John (Product Manager), Mary (Business Analyst)

**Version History**:
- v1.0 (2025-11-10): Initial PRD created
