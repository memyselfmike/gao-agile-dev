# Story 37.2: Pattern-Based Quality Detection

**Story ID**: 2.2
**Epic**: 2 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 8
**Priority**: High

---

## User Story

**As a** developer
**I want** automated analysis of conversation transcripts that identifies specific UX deficiencies
**So that** I can improve Brian's conversation quality with actionable recommendations

---

## Acceptance Criteria

- [ ] **AC1**: ConversationAnalyzer.analyze_conversation() method implemented
- [ ] **AC2**: Detects 4+ issue types: intent_misunderstanding, missed_probing_opportunity, unused_context, poor_response_relevance
- [ ] **AC3**: Each detected issue includes: turn_num, issue_type, severity, description, suggestion
- [ ] **AC4**: Pattern library includes 10+ detection patterns per issue type
- [ ] **AC5**: False positive rate <20% on sample conversations
- [ ] **AC6**: Analysis completes in <10s per conversation
- [ ] **AC7**: Uses deepseek-r1 for AI-powered analysis (validated in Story 37.0)
- [ ] **AC8**: 10+ sample conversations analyzed with documented results

---

## Technical Context

From Architecture section 3.1 (ConversationAnalyzer), implements pattern-based detection and AI-powered deep analysis.

**Key Methods**:
- `_detect_intent_issues()`: Check for understanding signals
- `_detect_probing_issues()`: Find missed probing opportunities
- `_detect_context_issues()`: Identify unused context
- `_ai_analyze_turn()`: Deep AI analysis (optional)

---

## Dependencies

- **Depends On**: Story 37.0 (POC validation), Story 37.1 (transcripts)
- **Blocks**: Story 37.3 (scoring needs issue detection)

---

## References

- PRD Section: FR4 (Quality Analysis)
- Architecture Section: 3.1 ConversationAnalyzer
