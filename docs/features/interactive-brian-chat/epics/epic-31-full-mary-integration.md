# Epic 31: Full Mary (Business Analyst) Integration

**Epic ID**: Epic-31
**Feature**: Interactive Brian Chat Interface
**Duration**: 2 weeks (25 story points)
**Owner**: Amelia (Developer)
**Status**: Planning
**Previous Epic**: Epic 30 (Interactive Brian Chat with Minimal Mary)
**Story Points**: 25

---

## Epic Goal

Complete the 8th agent (Mary - Business Analyst) with full BMAD methodology integration for requirements clarification, brainstorming, vision elicitation, and problem framing. This makes GAO-Dev's agent team complete and ensures Interactive Brian Chat has proper requirements analysis before creating PRDs.

**Success Criteria**:
- Mary agent with full BMAD business analysis workflows
- Brainstorming and mind mapping capabilities
- Vision elicitation techniques
- Problem framing workshops
- Multiple clarification strategies based on request type
- Domain-specific question libraries
- 15+ tests passing
- Complete integration with Brian's workflow selection

---

## Overview

Epic 30 added **minimal Mary** - basic requirements clarification with 4-5 questions. Epic 31 completes Mary with:

**Full BMAD Business Analysis Capabilities**:
- Requirements clarification (expanded)
- Vision elicitation and articulation
- Problem statement framing
- Brainstorming facilitation
- Mind mapping
- Use case analysis
- Stakeholder analysis
- Success criteria definition

**Why Essential**: Interactive chat without proper requirements analysis leads to irrelevant PRDs and wasted implementation effort. Mary ensures we build the right thing.

---

## User Stories (5 stories, 25 points)

### Story 31.1: Vision Elicitation Workflows (5 points)
- **As a** user with a vague idea
- **I want** Mary to help me articulate my vision
- **So that** we can create a clear product vision

**Deliverables**:
- Vision canvas workflow
- Problem-solution fit workflow
- Outcome mapping workflow
- 5W1H (Who, What, When, Where, Why, How) analysis

---

### Story 31.2: Brainstorming & Mind Mapping (8 points)
- **As a** user exploring solutions
- **I want** Mary to facilitate brainstorming sessions
- **So that** we can explore multiple approaches

**Deliverables**:
- Brainstorming facilitation workflows
- Mind mapping generation
- SCAMPER technique (Substitute, Combine, Adapt, Modify, etc.)
- "How Might We" framing
- Affinity mapping

---

### Story 31.3: Advanced Requirements Analysis (5 points)
- **As a** product team
- **I want** Mary to perform deep requirements analysis
- **So that** we capture all edge cases and constraints

**Deliverables**:
- MoSCoW prioritization (Must, Should, Could, Won't)
- Kano model analysis (Basic, Performance, Excitement features)
- Dependency mapping
- Risk identification
- Constraint analysis

---

### Story 31.4: Domain-Specific Question Libraries (4 points)
- **As a** user in a specific domain
- **I want** Mary to ask domain-relevant questions
- **So that** requirements are contextually appropriate

**Deliverables**:
- Web application question library
- Mobile app question library
- API/Backend service question library
- CLI tool question library
- Data pipeline question library

---

### Story 31.5: Integration & Documentation (3 points)
- **As a** developer
- **I want** comprehensive tests and documentation
- **So that** Mary's capabilities are reliable and discoverable

**Deliverables**:
- 15+ integration tests
- User guide for Mary's workflows
- Examples and demos
- Performance validation

---

## Technical Architecture

### Mary's Expanded Capabilities

```
Mary (Business Analyst)
├── Requirements Clarification (Epic 30 - ✅)
│   └── Basic 4-5 questions
│
├── Vision Elicitation (Story 31.1)
│   ├── Vision canvas
│   ├── Problem-solution fit
│   ├── Outcome mapping
│   └── 5W1H analysis
│
├── Brainstorming (Story 31.2)
│   ├── Facilitated brainstorming
│   ├── Mind mapping
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

---

## Integration with Brian

Brian's workflow selection now includes Mary's expanded capabilities:

```python
class BrianOrchestrator:
    async def assess_and_select_workflows(self, initial_prompt: str):
        # 1. Check vagueness
        vagueness = await self._assess_vagueness(initial_prompt)

        if vagueness > 0.6:
            # 2. Delegate to Mary - she chooses the right technique
            mary_strategy = await self.mary.select_clarification_strategy(
                initial_prompt,
                vagueness
            )

            if mary_strategy == "vision_elicitation":
                # Very vague - need vision work
                requirements = await self.mary.elicit_vision(initial_prompt)

            elif mary_strategy == "brainstorming":
                # Multiple approaches possible
                requirements = await self.mary.facilitate_brainstorming(initial_prompt)

            elif mary_strategy == "basic_clarification":
                # Just need some details
                requirements = await self.mary.clarify_requirements(initial_prompt)

            # 3. Proceed with clarified requirements
            return await self._analyze_with_clear_requirements(requirements)
```

---

## Dependencies

**Upstream (Complete)**:
- ✅ Epic 30 - Interactive Brian Chat with Minimal Mary
- ✅ Epic 21 - AIAnalysisService (for Mary's LLM calls)
- ✅ Epic 26 - ConversationManager (for multi-turn dialogues)

**No Blockers**: Ready to implement after Epic 30

---

## Timeline

**Week 1**:
- **Mon-Tue**: Story 31.1 - Vision Elicitation (5 pts)
- **Wed-Fri**: Story 31.2 - Brainstorming & Mind Mapping (8 pts) start

**Week 2**:
- **Mon**: Story 31.2 finish
- **Tue-Wed**: Story 31.3 - Advanced Requirements (5 pts)
- **Thu**: Story 31.4 - Domain-Specific Libraries (4 pts)
- **Fri**: Story 31.5 - Integration & Testing (3 pts)

**Total**: 2 weeks (25 story points)

---

## Success Metrics

- [ ] All 8 agents now operational (Mary completes the team)
- [ ] Mary can handle 5+ different clarification strategies
- [ ] 90% of vague requests successfully clarified
- [ ] PRDs created after Mary's analysis are 95% relevant
- [ ] User satisfaction: "Mary helped me understand what I really needed"
- [ ] 15+ tests passing (>90% coverage)

---

## Story Files

- [Story 31.1 - Vision Elicitation](../stories/epic-31/story-31.1.md)
- [Story 31.2 - Brainstorming & Mind Mapping](../stories/epic-31/story-31.2.md)
- [Story 31.3 - Advanced Requirements Analysis](../stories/epic-31/story-31.3.md)
- [Story 31.4 - Domain-Specific Question Libraries](../stories/epic-31/story-31.4.md)
- [Story 31.5 - Integration & Documentation](../stories/epic-31/story-31.5.md)

---

**Status**: Planning Complete
**Next Step**: Begin after Epic 30 complete
**Created**: 2025-11-10
