# Epic 387: UX Quality Analysis

**Epic ID**: 37
**Feature**: e2e-testing-ux-quality
**Status**: Complete
**Total Story Points**: 25
**Completed Points**: 25/25 (100%) ✅

---

## Epic Definition

Build a conversation quality analysis system that automatically identifies UX deficiencies in Brian's conversational behavior and generates actionable improvement recommendations.

This epic delivers the **core value proposition** of the feature: improving Brian's conversation quality through systematic analysis. It includes conversation capture, pattern-based and AI-powered quality detection, scoring algorithms, and formatted reporting.

**CRITICAL DEPENDENCY**: Must validate deepseek-r1 model quality (Story 37.0) before proceeding with full implementation.

---

## Business Value

Brian's conversation quality directly impacts user satisfaction. Poor UX issues include:
- Misunderstanding user intent
- Failing to probe for details when input is vague
- Not using available context
- Irrelevant or unhelpful responses

This epic enables:
- **Systematic detection** of conversation quality issues
- **Actionable recommendations** for improving Brian's prompts
- **Measurable improvement** in conversation quality over time
- **Continuous monitoring** of Brian's UX performance

**Target Impact**: Improve Brian's quality score from baseline to 80%+ within 2 months

---

## Goals

1. **Quality Measurement**: Establish objective quality scoring for conversations (0-100%)
2. **Issue Detection**: Identify specific UX problems (intent, probing, context, relevance)
3. **Actionable Recommendations**: Provide concrete suggestions for improvement
4. **Validation**: Ensure local model (deepseek-r1) quality is sufficient for analysis
5. **Foundation for Improvement**: Enable data-driven UX enhancements to Brian

---

## Acceptance Criteria

- [ ] **AC1**: deepseek-r1 quality validated with >80% agreement vs Claude on conversation analysis
- [ ] **AC2**: Conversation capture working in ChatSession with full metadata
- [ ] **AC3**: ConversationAnalyzer detects 4+ issue types (intent, probing, context, relevance)
- [ ] **AC4**: Quality scoring algorithm implemented and validated
- [ ] **AC5**: Quality reports generated with turn-by-turn analysis
- [ ] **AC6**: Recommendations are specific and actionable (not generic)
- [ ] **AC7**: 10+ sample conversations analyzed with documented results
- [ ] **AC8**: Quality scores correlate with manual expert ratings (r > 0.7)
- [ ] **AC9**: Analysis completes in <10s per conversation
- [ ] **AC10**: Zero API costs for analysis (uses deepseek-r1)

---

## Dependencies

### Internal Dependencies
- **CRITICAL**: Epic 386 - Test Infrastructure (provides ChatHarness, capture mode)
- Epic 380: ChatSession implementation (modified for conversation capture)
- Epic 21: AIAnalysisService (for AI-powered analysis)

### External Dependencies
- ollama running with deepseek-r1 model
- Conversation transcripts from capture mode
- Sample conversations for validation

### Blocked By
- Epic 386 must be complete (especially Story 1.2 - capture mode)
- **GATE DECISION**: Story 37.0 (POC validation) must pass before Stories 37.1-37.4 proceed

### Blocks
- Epic 38: Interactive Testing Tools (depends on quality analysis for reports)

---

## Stories

0. **Story 37.0**: deepseek-r1 Quality Validation POC (5 points) **[MANDATORY GATE]** ✅ COMPLETE
1. **Story 37.1**: Conversation Instrumentation (3 points) ✅ COMPLETE
2. **Story 37.2**: Pattern-Based Quality Detection (8 points) ✅ COMPLETE
3. **Story 37.3**: Quality Scoring Algorithm (5 points) ✅ COMPLETE
4. **Story 37.4**: Quality Reporting (4 points) ✅ COMPLETE

**Total**: 25 story points

---

## Critical Risk: Local Model Quality

### Problem

The CRAAP review identified a CRITICAL risk:

> "deepseek-r1 may produce significantly lower quality conversation analysis than Claude, making quality scores and recommendations unreliable. If analysis quality is poor, the entire Mode 2 (Quality Analysis) becomes useless; defeats purpose of the feature."

### Gate Decision

**Story 37.0 is MANDATORY** before proceeding with Stories 37.1-37.4.

**Validation Criteria**:
- Compare deepseek-r1 vs Claude on 10 sample conversations
- Measure agreement on quality scoring (must achieve >80% agreement)
- Measure agreement on issue detection (must detect 70%+ of same issues)
- Document quality differences and limitations

**Decision Rule**:
- **PASS** (>80% agreement): Proceed with Stories 37.1-37.4 using deepseek-r1
- **PARTIAL PASS** (60-80% agreement): Use Claude for analysis, deepseek-r1 for tests only
- **FAIL** (<60% agreement): Reconsider feature scope or use Claude API (accept costs)

**Owner**: Technical Lead + Product Manager

---

## Technical Notes

### Architecture Highlights

**ConversationAnalyzer**: Core analysis engine
- Pattern-based detection (fast, deterministic)
- AI-powered deep analysis (optional, higher quality)
- Issue categorization and severity scoring
- Recommendation generation

**Quality Scoring**: 0-100% score based on:
- Issue count and severity
- Turn count normalization
- Weighted penalty system

**Report Generation**: Structured reports with:
- Overall quality score
- Turn-by-turn analysis
- Issue details with examples
- Actionable recommendations

### Two-Tier Analysis Strategy

**Tier 1: Pattern-Based Detection** (Fast, cost-free)
- Regex patterns for common issues
- Context availability checking
- Question detection
- Understanding signal detection

**Tier 2: AI-Powered Analysis** (Slower, optional)
- Deep semantic analysis
- Nuanced quality assessment
- Context relevance evaluation
- Only used when patterns are ambiguous

### Risk Mitigation

**Risk**: Analysis quality insufficient for actionable recommendations
**Mitigation**: Story 37.0 validates quality BEFORE implementation

**Risk**: Local model produces inconsistent results
**Mitigation**: Multiple runs, statistical validation, Claude spot-checking

**Risk**: Scoring algorithm doesn't correlate with actual UX quality
**Mitigation**: Expert validation, user feedback integration, continuous tuning

---

## Testing Strategy

### Validation Tests
- deepseek-r1 vs Claude agreement (Story 37.0)
- Quality scores vs expert manual ratings
- Issue detection recall and precision
- Recommendation actionability assessment

### Unit Tests
- Pattern matching accuracy
- Scoring algorithm correctness
- Report formatting
- Edge case handling

### Integration Tests
- Full conversation analysis end-to-end
- Multiple conversation types (greenfield, brownfield, errors)
- Performance testing (<10s per conversation)

---

## Success Metrics

### PRIMARY: UX Quality Improvement (Core Value)

- **Brian Quality Score**: Increase from baseline to 80%+ within 2 months
  - Baseline established by first 10 conversation analyses
  - Target: 80%+ quality score across diverse test conversations

- **Intent Understanding**: 90%+ of user intents correctly identified
  - Measured by explicit confirmation signals in Brian responses

- **Probing Quality**: Brian asks clarifying questions for 80%+ of vague inputs
  - Vague inputs detected via pattern matching

- **Context Usage**: Brian uses available context in 70%+ of responses
  - Usage detected via response analysis

- **Actionable Improvements**: 5+ specific UX improvements implemented and validated
  - Each improvement linked to detected quality issue
  - Validation via before/after comparison
  - Quality score increase >10 points per improvement

### SECONDARY: Analysis Infrastructure

- **Analysis Accuracy**: 80%+ agreement with manual expert assessment
- **Analysis Speed**: <10s per conversation
- **Cost**: $0 for standard analysis (local model)
- **Issue Detection**: 70%+ of known issues detected automatically

---

## Out of Scope

- Real-time quality monitoring in production (future work)
- Automated prompt optimization based on quality scores (future work)
- A/B testing framework for prompt variations (future work)
- Performance benchmarking of response times (future work)
- Multi-user conversation analysis (future work)

---

## Implementation Sequence

### Phase 1: Validation (Week 1)
**Story 37.0**: Validate deepseek-r1 quality
- **GATE DECISION**: Go/No-Go for Epic 2

### Phase 2: Foundation (Week 1-2)
**Story 37.1**: Conversation instrumentation
- Enable conversation capture
- Persist transcripts with metadata

### Phase 3: Analysis (Week 2-3)
**Story 37.2**: Pattern-based detection
**Story 37.3**: Quality scoring
- Implement detection algorithms
- Develop scoring system
- Validate with sample conversations

### Phase 4: Reporting (Week 3)
**Story 37.4**: Quality reporting
- Generate formatted reports
- Document findings
- Create improvement recommendations

---

## References

- PRD: `docs/features/e2e-testing-ux-quality/PRD.md` (Section: User Stories - Epic 2)
- Architecture: `docs/features/e2e-testing-ux-quality/ARCHITECTURE.md` (Section: 3. Conversation Analysis Layer)
- CRAAP Review: Priority Issue #1 (Validate Local Model Quality)
- CRAAP Review: Alignment Section (UX Quality Improvement focus)
