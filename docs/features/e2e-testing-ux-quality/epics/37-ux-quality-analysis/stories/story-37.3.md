# Story 37.3: Quality Scoring Algorithm

**Story ID**: 2.3
**Epic**: 2 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 5
**Priority**: High

---

## User Story

**As a** product manager
**I want** objective quality scores (0-100%) for conversations
**So that** I can measure improvement in Brian's UX over time

---

## Acceptance Criteria

- [ ] **AC1**: ConversationAnalyzer._calculate_score() method implemented
- [ ] **AC2**: Score range is 0-100% (normalized)
- [ ] **AC3**: Severity weights defined and justified: high=3.0, medium=2.0, low=1.0
- [ ] **AC4**: Score correlates with manual expert ratings (r > 0.7)
- [ ] **AC5**: Algorithm documented with examples
- [ ] **AC6**: Edge cases handled (0 turns, all issues, no issues)
- [ ] **AC7**: Validated against 10+ sample conversations
- [ ] **AC8**: Baseline quality score established for Brian

---

## Technical Context

From Architecture section 3.1 (ConversationAnalyzer._calculate_score):

**Scoring Formula**:
```
total_penalty = sum(severity_weights[issue.severity] for issue in issues)
max_total_penalty = total_turns * max_penalty_per_turn (10.0)
score = 100 * (1 - (total_penalty / max_total_penalty))
```

**Validation**: Must correlate with expert manual assessment

---

## Dependencies

- **Depends On**: Story 37.2 (issue detection)
- **Blocks**: Story 37.4 (reporting needs scores)

---

## References

- PRD Section: Success Metrics (Brian Quality Score)
- Architecture Section: 3.1 ConversationAnalyzer._calculate_score
- CRAAP Review: Critique #1 (Ambiguous Quality Scoring Algorithm)
