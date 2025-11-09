# Product Requirements Document: Ceremony Integration & Self-Learning System

**Feature ID**: ceremony-integration-and-self-learning
**Version**: 1.0
**Created**: 2025-11-09
**Status**: Planning
**Owner**: Product Team (John)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Goals & Success Criteria](#goals--success-criteria)
4. [User Stories](#user-stories)
5. [Epic Breakdown](#epic-breakdown)
6. [Dependencies](#dependencies)
7. [Timeline](#timeline)
8. [Risks & Mitigations](#risks--mitigations)

---

## Executive Summary

GAO-Dev has built exceptional infrastructure for multi-agent ceremonies, learning tracking, and state management (Epics 22-27), but **lacks the connective tissue** to make it truly autonomous and self-improving. This feature adds:

1. **Ceremony Integration**: Automatic ceremony triggers in workflow orchestration
2. **Self-Learning Loop**: Learnings from retrospectives feed back into workflow selection
3. **Document Structure**: Systematic patterns for chores/bugs/features
4. **Course Correction**: System learns from mistakes and improves over time

**Vision**: Transform GAO-Dev from "workflow executor" to "learning, self-improving autonomous developer"

**Impact**:
- Ceremonies triggered automatically at epic milestones, story intervals, and quality gates
- Brian uses past learnings to improve workflow selection
- Action items from standups become stories automatically
- System gets smarter with every project

---

## Problem Statement

### Current State

**Infrastructure Built (Epics 22-27)**:
- ✅ CeremonyOrchestrator with hold_ceremony(), hold_standup(), hold_retrospective()
- ✅ Action item and learning tracking in database
- ✅ FastContextLoader for <5ms context queries
- ✅ GitIntegratedStateManager for atomic operations
- ✅ All services integrated into orchestrator

**Critical Gaps**:
- ❌ **No ceremony triggers**: Ceremonies exist but are never invoked automatically
- ❌ **No self-learning loop**: Learnings captured but never fed back into workflow selection
- ❌ **Document structure ad-hoc**: No systematic approach to feature folders, global docs
- ❌ **No work type taxonomy**: Confusion between chores vs bugs vs features

### Pain Points

1. **Manual Ceremony Invocation**: User must manually call ceremonies - not autonomous
2. **Learnings Lost**: Retrospectives generate insights that sit unused in database
3. **Repeated Mistakes**: Same architectural errors made across projects
4. **Inconsistent Docs**: Feature folders created differently each time
5. **No Course Correction**: System doesn't learn from quality gate failures

### User Impact

**For Autonomous Development**:
- Projects run without ceremonies → no team coordination
- No daily standups → blockers go unnoticed
- No retrospectives → wisdom lost after epic completion
- No learning feedback → same mistakes repeated

**For Users**:
- Must manually coordinate agent activities
- No visibility into project health
- No continuous improvement
- Inconsistent project structure

---

## Goals & Success Criteria

### Primary Goals

1. **Automated Ceremonies**: Ceremonies trigger automatically based on workflow state
2. **Self-Learning**: Past learnings influence future workflow selection
3. **Systematic Structure**: Clear patterns for all work types (chore/bug/feature)
4. **Continuous Improvement**: System improves with every completed project

### Success Criteria

**Ceremony Integration**:
- [ ] 100% of Level 3+ workflows include planning ceremony
- [ ] 100% of Level 2+ workflows include retrospective ceremony
- [ ] Standups trigger every N stories (configurable by scale level)
- [ ] Quality gate failures trigger emergency standups
- [ ] <2% ceremony overhead (time cost)
- [ ] >80% of ceremonies produce actionable items

**Self-Learning Loop**:
- [ ] >50% of learnings applied in subsequent projects
- [ ] >70% success rate for applied learnings
- [ ] Brian's context includes top 5 relevant learnings
- [ ] Workflow adjustments based on past quality issues
- [ ] Learning confidence scores correlate with outcomes

**Document Structure**:
- [ ] 100% of features have correct folder structure (by scale level)
- [ ] Global docs (PRD, ARCHITECTURE) updated within 1 day of feature completion
- [ ] Zero orphaned documents
- [ ] <5% document inconsistency rate

**Course Correction**:
- [ ] High-priority action items auto-converted to stories
- [ ] Repeated failures trigger retrospectives
- [ ] Architectural learnings influence Winston's decisions
- [ ] Quality learnings add extra testing workflows

---

## User Stories

### Epic 28: Ceremony-Driven Workflow Integration

**Story 28.1**: Ceremony Workflow Types (5 points)
- **As a** workflow orchestrator
- **I want** ceremony workflows defined and loadable
- **So that** Brian can include them in workflow sequences

**Story 28.2**: Enhanced Workflow Selector (8 points)
- **As a** Brian (workflow selector)
- **I want** to inject ceremonies into Level 2-4 workflows
- **So that** team coordination happens automatically

**Story 28.3**: CeremonyTriggerEngine (8 points)
- **As a** workflow coordinator
- **I want** intelligent ceremony trigger evaluation
- **So that** ceremonies run at the right moments

**Story 28.4**: Orchestrator Integration (5 points)
- **As a** GAODevOrchestrator
- **I want** seamless ceremony execution in workflows
- **So that** ceremony outcomes feed into next steps

**Story 28.5**: CLI Commands & Testing (4 points)
- **As a** developer
- **I want** CLI commands to test ceremonies
- **So that** I can validate the system works

### Epic 29: Self-Learning Feedback Loop

**Story 29.1**: Learning Schema Enhancement (3 points)
- **As a** learning tracking system
- **I want** enhanced schema with application metrics
- **So that** I can track learning effectiveness

**Story 29.2**: LearningApplicationService (8 points)
- **As a** Brian
- **I want** relevant learnings with confidence scores
- **So that** I can select workflows informed by past experience

**Story 29.3**: Brian Context Augmentation (8 points)
- **As a** Brian
- **I want** my analysis context enriched with learnings
- **So that** I make better workflow decisions

**Story 29.4**: Workflow Adjustment Logic (8 points)
- **As a** workflow selector
- **I want** to adjust workflows based on learnings
- **So that** past mistakes don't repeat

**Story 29.5**: Action Item Integration (5 points)
- **As a** Bob (scrum master)
- **I want** action items to flow into next sprint
- **So that** improvements actually happen

**Story 29.6**: Learning Decay & Confidence (3 points)
- **As a** learning system
- **I want** learnings to decay over time and update confidence
- **So that** old/obsolete learnings don't pollute decisions

**Story 29.7**: Testing & Validation (3 points)
- **As a** developer
- **I want** comprehensive tests for self-learning
- **So that** I trust the system's decisions

---

## Epic Breakdown

### Epic 28: Ceremony-Driven Workflow Integration

**Duration**: 1.5 weeks (30 story points)
**Owner**: Amelia (Developer)
**Dependencies**: Epics 22-27 (ceremony infrastructure)

**Deliverables**:
- Ceremony workflow definitions (planning, standup, retrospective)
- Enhanced WorkflowSelector with ceremony injection
- CeremonyTriggerEngine for intelligent triggering
- Full orchestrator integration
- CLI commands and 25+ tests

**Key Components**:
1. `gao_dev/workflows/5-ceremonies/` - Workflow definitions
2. `gao_dev/methodologies/adaptive_agile/workflow_selector.py` - Enhanced selector
3. `gao_dev/core/services/ceremony_trigger_engine.py` - Trigger evaluation
4. `gao_dev/orchestrator/` - Integration updates
5. `gao_dev/cli/ceremony_commands.py` - CLI commands

### Epic 29: Self-Learning Feedback Loop

**Duration**: 2 weeks (38 story points)
**Owner**: Amelia (Developer)
**Dependencies**: Epic 28, Epics 22-27

**Deliverables**:
- Enhanced learning schema with application tracking
- LearningApplicationService with relevance scoring
- Brian context augmentation with learnings
- Workflow adjustment based on past learnings
- Action item → story conversion
- 45+ tests

**Key Components**:
1. Database schema updates (Migration 006)
2. `gao_dev/core/services/learning_application_service.py` - Learning application
3. `gao_dev/orchestrator/brian_orchestrator.py` - Enhanced with learnings
4. `gao_dev/methodologies/adaptive_agile/workflow_adjuster.py` - Adjustment logic
5. `gao_dev/core/services/action_item_integration_service.py` - Action item flow

---

## Dependencies

### Technical Dependencies

**Required (Completed)**:
- ✅ Epic 22: Orchestrator decomposition
- ✅ Epic 23: GitManager enhancement
- ✅ Epic 24: State tables & tracker
- ✅ Epic 25: Git-integrated state manager
- ✅ Epic 26: Multi-agent ceremonies
- ✅ Epic 27: Integration & migration

**New Dependencies**:
- Epic 28 must complete before Epic 29 (ceremonies must work before learning from them)
- Python 3.11+ with SQLite support
- Git installed and configured

### Feature Dependencies

**Ceremony Integration (Epic 28) depends on**:
- WorkflowRegistry (existing)
- WorkflowCoordinator (existing)
- CeremonyOrchestrator (Epic 26)
- StateCoordinator (Epic 24)

**Self-Learning (Epic 29) depends on**:
- LearningIndexService (Epic 24)
- ActionItemService (Epic 24)
- FastContextLoader (Epic 25)
- BrianOrchestrator (existing)
- Ceremony integration (Epic 28)

---

## Timeline

### Phase 1: Ceremony Integration (Weeks 1-2)

**Week 1**:
- Story 28.1: Ceremony workflow types (Mon-Tue)
- Story 28.2: Enhanced workflow selector (Wed-Fri)

**Week 2**:
- Story 28.3: CeremonyTriggerEngine (Mon-Wed)
- Story 28.4: Orchestrator integration (Thu)
- Story 28.5: CLI & testing (Fri)

**Milestone**: Ceremonies auto-trigger in workflows

### Phase 2: Self-Learning Loop (Weeks 3-4)

**Week 3**:
- Story 29.1: Learning schema enhancement (Mon)
- Story 29.2: LearningApplicationService (Tue-Thu)
- Story 29.3: Brian context augmentation (Fri)

**Week 4**:
- Story 29.4: Workflow adjustment logic (Mon-Wed)
- Story 29.5: Action item integration (Thu)
- Story 29.6: Learning decay & confidence (Fri)
- Story 29.7: Testing & validation (Fri)

**Milestone**: Self-learning loop operational

### Total Duration

**4 weeks** (68 story points total)
- Epic 28: 1.5 weeks (30 points)
- Epic 29: 2 weeks (38 points)
- Testing & validation: 0.5 weeks (included in epics)

---

## Work Type Taxonomy

This feature establishes clear patterns for all work types:

### Level 0: Chore
- **No PRD**: Direct implementation
- **No Epic**: Single commit
- **No Ceremonies**: Too small
- **Example**: Update dependencies, fix typo

### Level 1: Bug Fix
- **Optional Bug Report**: Simple markdown file
- **No Epic**: Unless part of bug-fix epic
- **Retrospective on Failure**: If bug fails 2x
- **Example**: Fix failing test, resolve crash

### Level 2: Small Feature
- **Lightweight PRD**: 1-2 pages
- **Single Epic**: 3-8 stories
- **Feature Folder**: `docs/features/<name>/`
- **Ceremonies**: Planning (optional), Standup (if >3 stories), Retro (required)
- **Example**: Add authentication, new UI component

### Level 3: Medium Feature
- **Full PRD**: 3-5 pages
- **Multiple Epics**: 2-5 epics
- **Rich Feature Folder**: PRD + ARCHITECTURE + epics/ + stories/ + retrospectives/
- **Ceremonies**: Planning (required), Standup (every 2 stories), Retro (mid + final)
- **Example**: Complete module, integration system

### Level 4: Greenfield Application
- **Comprehensive PRD**: 10+ pages
- **Many Epics**: 5-20+ epics
- **Root Docs + Features**: Global docs + feature folders
- **Ceremonies**: Planning (required), Daily standup, Retro (per phase + final)
- **Example**: New product, complete rewrite

---

## Risks & Mitigations

### Risk 1: Ceremony Overhead Slows Development

**Impact**: Medium
**Probability**: Medium

**Mitigation**:
- Make most ceremonies optional for Level 2
- Track ceremony time cost in metrics
- Adjust thresholds if >2% overhead
- Skip ceremonies for chores/simple bugs

### Risk 2: Learning Relevance Scoring Inaccurate

**Impact**: High (bad decisions)
**Probability**: Medium

**Mitigation**:
- Start with simple scoring algorithm
- Iterate based on feedback
- Manual review of top learnings
- Confidence threshold (>0.3) before application
- Decay obsolete learnings

### Risk 3: Document Structure Inconsistency

**Impact**: Medium
**Probability**: Low (automated)

**Mitigation**:
- Automated folder initialization
- DocumentStructureManager service
- Consistency checker (like GitAwareConsistencyChecker)
- Repair tools for mismatches

### Risk 4: Too Many Action Items Created

**Impact**: Medium (noise)
**Probability**: Medium

**Mitigation**:
- Priority filtering (high/medium/low)
- Auto-complete low-priority items after 30 days
- Consolidate similar action items
- Limit auto-story conversion to high-priority only

### Risk 5: Performance Degradation from Context Loading

**Impact**: Medium
**Probability**: Low (FastContextLoader)

**Mitigation**:
- FastContextLoader already <5ms
- Cache learning queries
- Limit to top 5 learnings
- Async loading where possible

---

## Success Metrics

### Quantitative Metrics

**Ceremony Adoption**:
- Ceremony trigger rate by scale level
- Average ceremony duration
- Action items per ceremony
- Learnings per retrospective

**Self-Learning Effectiveness**:
- Learning application rate (% applied)
- Learning success rate (% successful outcomes)
- Confidence score accuracy
- Workflow adjustment frequency

**Document Structure**:
- Feature folder compliance rate
- Global doc update latency
- Document consistency score
- Orphaned document count

### Qualitative Metrics

**User Satisfaction**:
- Autonomous operation feedback
- Ceremony value perception
- Learning quality feedback
- Document structure clarity

**System Intelligence**:
- Workflow selection appropriateness
- Learning relevance accuracy
- Action item actionability
- Course correction effectiveness

---

## Acceptance Criteria (Feature-Level)

This feature is **COMPLETE** when:

1. **Ceremony Integration**:
   - [ ] Ceremonies trigger automatically in Level 2-4 workflows
   - [ ] Trigger logic handles all trigger types (epic_start, story_interval, quality_gate, etc.)
   - [ ] Ceremony outcomes (transcripts, action items, learnings) tracked in git
   - [ ] CLI command `gao-dev ceremony hold <type>` works
   - [ ] 25+ tests passing for ceremony integration

2. **Self-Learning Loop**:
   - [ ] Learnings scored by relevance, success rate, confidence
   - [ ] Brian's context includes top 5 relevant learnings
   - [ ] Workflows adjusted based on past learnings
   - [ ] Action items flow into next sprint planning
   - [ ] Learning confidence updates based on outcomes
   - [ ] 45+ tests passing for self-learning

3. **Document Structure**:
   - [ ] DocumentStructureManager auto-initializes feature folders
   - [ ] Global docs updated on feature planning/completion
   - [ ] Work type taxonomy documented and enforced
   - [ ] Consistency checker detects structure issues

4. **Validation**:
   - [ ] End-to-end test: Small feature (Level 2) with ceremonies
   - [ ] End-to-end test: Self-learning across 2+ projects
   - [ ] Benchmark run showing ceremony integration
   - [ ] Zero regressions in existing functionality

---

## Future Enhancements (Out of Scope)

These are **NOT** included in Epics 28-29 but could be future work:

1. **Advanced Ceremony Types**:
   - Design reviews
   - Code review ceremonies
   - Architecture decision records (ADRs)

2. **ML-Based Learning**:
   - Use ML models to improve relevance scoring
   - Cluster similar learnings
   - Predict optimal workflow sequences

3. **Cross-Project Learning**:
   - Learn from other GAO-Dev installations (federated)
   - Benchmark suite learning database
   - Community-contributed learnings

4. **Interactive Ceremonies**:
   - Real-time multi-agent participation
   - User participation in ceremonies
   - Voice/video ceremony recording

5. **Advanced Analytics**:
   - Learning effectiveness dashboards
   - Ceremony outcome trends
   - Workflow optimization recommendations

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical specification
- [Epic 28](./epics/epic-28-ceremony-workflow-integration.md) - Ceremony integration
- [Epic 29](./epics/epic-29-self-learning-feedback-loop.md) - Self-learning loop
- [Git-Integrated Hybrid Wisdom](../git-integrated-hybrid-wisdom/) - Foundation (Epics 22-27)
- [BMAD Method](../../bmm-workflow-status.md) - Methodology overview

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-09 | 1.0 | Initial PRD created | John (Product) |

---

**Status**: Ready for Epic Planning and Story Breakdown
**Next Steps**: Create Epic 28 and Epic 29 detailed specifications
