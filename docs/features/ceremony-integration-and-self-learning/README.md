# Ceremony Integration & Self-Learning System

**Feature Status**: Planning Complete - Ready for Implementation
**Created**: 2025-11-09
**Owner**: Product Team

---

## Overview

This feature adds the missing connective tissue to make GAO-Dev truly autonomous and self-improving:

1. **Ceremony Integration**: Automatic ceremony triggers in workflow orchestration
2. **Self-Learning Loop**: Learnings from retrospectives feed back into workflow selection
3. **Document Structure**: Systematic patterns for chores/bugs/features
4. **Course Correction**: System learns from mistakes and improves over time

**Vision**: Transform GAO-Dev from "workflow executor" to "learning, self-improving autonomous developer"

---

## Documentation Structure

```
ceremony-integration-and-self-learning/
├── README.md                          # ← START HERE (this file)
├── PRD.md                             # Product Requirements Document ⭐
├── ARCHITECTURE.md                    # Technical Specification ⭐
│
├── epics/
│   ├── epic-28-ceremony-workflow-integration.md    # Week 1-2 (30 points) ⭐
│   └── epic-29-self-learning-feedback-loop.md      # Week 3-4 (38 points) ⭐
│
└── stories/
    ├── epic-28/                       # 5 stories (ceremony integration)
    └── epic-29/                       # 7 stories (self-learning)
```

**Start Reading**: [PRD.md](./PRD.md) for requirements, then [ARCHITECTURE.md](./ARCHITECTURE.md) for technical design.

---

## Quick Links

**Epic Documents**:
- [Epic 28: Ceremony-Driven Workflow Integration](./epics/epic-28-ceremony-workflow-integration.md) - Automatic ceremony triggers
- [Epic 29: Self-Learning Feedback Loop](./epics/epic-29-self-learning-feedback-loop.md) - Learnings influence workflow selection

**Key Documents**:
- [PRD.md](./PRD.md) - Product requirements, success criteria, timeline
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design, APIs, data models

---

## Epic Summaries

### Epic 28: Ceremony-Driven Workflow Integration (30 points)

**Goal**: Ceremonies trigger automatically in workflows

**Stories**:
1. **Story 28.1** (5pts): Ceremony Workflow Types - Create ceremony-*.yaml workflows
2. **Story 28.2** (8pts): Enhanced Workflow Selector - Inject ceremonies into Level 2-4
3. **Story 28.3** (8pts): CeremonyTriggerEngine - Intelligent trigger evaluation
4. **Story 28.4** (5pts): Orchestrator Integration - Full workflow integration
5. **Story 28.5** (4pts): CLI Commands & Testing - `gao-dev ceremony hold`

**Deliverables**:
- 3 ceremony workflows (planning, standup, retrospective)
- CeremonyTriggerEngine service (~350 LOC)
- Enhanced WorkflowSelector with injection logic
- CLI commands for manual invocation
- 54+ tests

---

### Epic 29: Self-Learning Feedback Loop (38 points)

**Goal**: System learns from past work and improves

**Stories**:
1. **Story 29.1** (3pts): Learning Schema Enhancement - Add application tracking
2. **Story 29.2** (8pts): LearningApplicationService - Relevance scoring algorithm
3. **Story 29.3** (8pts): Brian Context Augmentation - Enrich with top 5 learnings
4. **Story 29.4** (8pts): Workflow Adjustment Logic - Adjust based on learnings
5. **Story 29.5** (5pts): Action Item Integration - Action items → stories
6. **Story 29.6** (3pts): Learning Decay & Confidence - Recency and confidence updates
7. **Story 29.7** (3pts): Testing & Validation - Comprehensive test suite

**Deliverables**:
- LearningApplicationService (~400 LOC)
- Enhanced BrianOrchestrator with learning integration
- WorkflowAdjuster service (~250 LOC)
- ActionItemIntegrationService (~200 LOC)
- 57+ tests

---

## Story Details

### Epic 28 Stories

**Story 28.1**: Ceremony Workflow Types (5 points)
- Create `gao_dev/workflows/5-ceremonies/` directory
- 3 ceremony workflows (planning, standup, retrospective)
- WorkflowRegistry integration
- 5 unit tests

**Story 28.2**: Enhanced Workflow Selector (8 points)
- Inject ceremonies into Level 2-4 workflow sequences
- Different patterns per scale level
- Ceremony creation methods
- 10 unit tests

**Story 28.3**: CeremonyTriggerEngine (8 points)
- Service to evaluate trigger conditions (~350 LOC)
- 10 trigger types supported
- Integration with StateCoordinator
- 15 unit tests

**Story 28.4**: Orchestrator Integration (5 points)
- WorkflowCoordinator uses CeremonyTriggerEngine
- Ceremony execution in workflow flow
- Atomic git commits for ceremony artifacts
- 8 integration tests

**Story 28.5**: CLI Commands & Testing (4 points)
- `gao-dev ceremony hold <type>` command
- 3 E2E tests (Level 2, 3, quality gate)
- CLI output and help text
- 5 CLI tests

### Epic 29 Stories

**Story 29.1**: Learning Schema Enhancement (3 points)
- Migration 006: Add application tracking columns
- Create learning_applications table
- Indexes for performance
- 5 migration tests

**Story 29.2**: LearningApplicationService (8 points)
- Relevance scoring algorithm (~400 LOC)
- get_relevant_learnings() with scoring
- record_application() with stat updates
- 15 unit tests

**Story 29.3**: Brian Context Augmentation (8 points)
- Enhance BrianOrchestrator with learnings
- Build enriched context with top 5 learnings
- Learning recommendations
- 10 unit tests

**Story 29.4**: Workflow Adjustment Logic (8 points)
- WorkflowAdjuster service (~250 LOC)
- Adjust workflows based on learning categories
- Quality → extra testing, Process → more ceremonies
- 12 unit tests

**Story 29.5**: Action Item Integration (5 points)
- ActionItemIntegrationService (~200 LOC)
- Inject action items into planning
- Auto-convert high-priority to stories
- 8 unit tests

**Story 29.6**: Learning Decay & Confidence (3 points)
- Recency decay algorithm
- Confidence score updates
- Learning supersession
- 5 unit tests

**Story 29.7**: Testing & Validation (3 points)
- 45 unit tests across all services
- 10 integration tests
- 2 E2E scenarios (two-project learning loops)
- Performance benchmarks

---

## Key Innovations

### 1. Ceremony Trigger Matrix

Ceremonies trigger automatically based on scale level:

```
┌─────────────┬──────────────┬──────────────────┬─────────────────┐
│ Scale Level │ Planning     │ Standup          │ Retrospective   │
├─────────────┼──────────────┼──────────────────┼─────────────────┤
│ Level 0-1   │ None         │ None             │ On error only   │
│ Level 2     │ Optional     │ Every 3 stories  │ Epic completion │
│ Level 3     │ Required     │ Every 2 stories  │ Mid + completion│
│ Level 4     │ Required     │ Daily/per story  │ Per phase + end │
└─────────────┴──────────────┴──────────────────┴─────────────────┘
```

### 2. Self-Learning Loop

```
Retrospective → Learnings Indexed (confidence: 0.5)
    ↓
New Project → Brian Analyzes
    ↓
LearningApplicationService.get_relevant_learnings()
    ↓
Score by: relevance × success_rate × confidence × recency × similarity
    ↓
Top 5 Learnings → Brian's Context
    ↓
WorkflowAdjuster.apply_adjustments()
    ↓
Workflows Executed
    ↓
Outcome Evaluated → record_application()
    ↓
Confidence Updated → Learning Stronger/Weaker
    ↓
LOOP CONTINUES
```

### 3. Document Structure Taxonomy

Clear patterns for all work types:
- **Level 0 (Chore)**: No docs, just commit
- **Level 1 (Bug)**: Optional bug report
- **Level 2 (Small Feature)**: Feature folder with PRD, stories, changelog
- **Level 3 (Medium Feature)**: Full structure with epics, retrospectives
- **Level 4 (Greenfield)**: Root docs + feature folders + comprehensive structure

---

## Implementation Timeline

**Total Duration**: 4 weeks (68 story points)

**Phase 1: Ceremony Integration** (Weeks 1-2, 30 points)
- Week 1: Stories 28.1-28.2 (workflow types + selector)
- Week 2: Stories 28.3-28.5 (trigger engine + integration + CLI)
- **Milestone**: Ceremonies auto-trigger in workflows

**Phase 2: Self-Learning Loop** (Weeks 3-4, 38 points)
- Week 3: Stories 29.1-29.3 (schema + learning service + Brian)
- Week 4: Stories 29.4-29.7 (adjustment + action items + decay + tests)
- **Milestone**: Self-learning loop operational

---

## Success Criteria

**Ceremony Integration**:
- ✓ 100% of Level 3+ workflows include planning ceremony
- ✓ 100% of Level 2+ workflows include retrospective
- ✓ Standups trigger every N stories (configurable)
- ✓ <2% ceremony overhead

**Self-Learning**:
- ✓ >50% of learnings applied in subsequent projects
- ✓ >70% success rate for applied learnings
- ✓ Brian's context includes top 5 relevant learnings
- ✓ Workflow adjustments based on past issues

**Document Structure**:
- ✓ 100% of features have correct folder structure
- ✓ Global docs updated within 1 day
- ✓ Zero orphaned documents

---

## Dependencies

**Required (Completed)**:
- ✅ Epic 22: Orchestrator decomposition
- ✅ Epic 23: GitManager enhancement
- ✅ Epic 24: State tables & tracker
- ✅ Epic 25: Git-integrated state manager
- ✅ Epic 26: Multi-agent ceremonies
- ✅ Epic 27: Integration & migration

**Sequential Dependencies**:
- Epic 28 must complete before Epic 29 (need ceremonies to learn from them)

---

## Risks & Mitigations

**Risk 1**: Ceremony overhead slows development
- **Mitigation**: Optional for Level 2, track cost, <2% target

**Risk 2**: Learning relevance scoring inaccurate
- **Mitigation**: Simple algorithm, iterate, manual review option

**Risk 3**: Too many action items
- **Mitigation**: Priority filtering, auto-complete after 30 days

---

## Future Enhancements (Out of Scope)

- ML-based learning scoring
- Cross-project learning (federated)
- Interactive ceremonies with user participation
- Advanced ceremony types (design reviews, ADRs)

---

## References

- [Git-Integrated Hybrid Wisdom Feature](../git-integrated-hybrid-wisdom/) - Foundation (Epics 22-27)
- [BMAD Method](../../bmm-workflow-status.md) - Methodology overview
- [Adaptive Agile Methodology](../../../gao_dev/methodologies/adaptive_agile/) - Scale-adaptive routing

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-09 | 1.0 | Feature planning complete | Product Team |

---

**Status**: Ready for Implementation
**Next Steps**: Begin Epic 28.1 (Ceremony Workflow Types)
