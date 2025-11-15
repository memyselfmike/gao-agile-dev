# Story 37.0: deepseek-r1 Quality Validation POC

**Story ID**: 37.0
**Epic**: 37 - UX Quality Analysis
**Feature**: e2e-testing-ux-quality
**Status**: Complete
**Story Points**: 5
**Priority**: CRITICAL - MANDATORY GATE

---

## User Story

**As a** product manager
**I want** to validate that deepseek-r1 can achieve >80% agreement with Claude on conversation quality analysis
**So that** I can make an informed decision about whether to proceed with local model-based analysis

---

## Business Value

The entire Epic 387 (UX Quality Analysis) depends on the assumption that deepseek-r1 can perform quality analysis with sufficient accuracy. If this assumption is wrong, we risk building a system that produces unreliable results, wasting 3-4 weeks of development effort.

This POC provides:
- **Risk Mitigation**: Validates critical assumption before full implementation
- **Go/No-Go Decision**: Data-driven decision on implementation approach
- **Cost-Quality Tradeoff Analysis**: Quantifies cost savings vs quality degradation
- **Implementation Strategy**: Determines whether to use local model, Claude, or hybrid approach

**Decision Impact**: Affects 20 story points (Stories 37.1-37.4) and $0-200 in monthly costs

---

## Acceptance Criteria

- [x] **AC1**: 10 diverse sample conversations created (greenfield, brownfield, vague, detailed, errors)
- [x] **AC2**: Each conversation analyzed by Claude to establish "ground truth" quality assessment
- [x] **AC3**: Same conversations analyzed by deepseek-r1 for comparison
- [x] **AC4**: Agreement measured on quality scores (within 15 points = agreement)
- [x] **AC5**: Agreement measured on issue detection (same issue type detected = agreement)
- [x] **AC6**: Validation report documents: agreement %, quality differences, limitations
- [x] **AC7**: Go/No-Go recommendation provided with rationale
- [x] **AC8**: If FAIL, alternative approach specified (Claude API, hybrid, or scope reduction)

---

## Validation Criteria

### PASS: >80% Agreement
- **Quality Score Agreement**: 8+ of 10 conversations within 15 points
- **Issue Detection Agreement**: Detects 70%+ of same issues as Claude
- **Recommendation Quality**: Recommendations are specific and actionable
- **Decision**: **Proceed** with Stories 37.1-37.4 using deepseek-r1

### PARTIAL PASS: 60-80% Agreement
- **Quality Score Agreement**: 6-7 of 10 conversations within 15 points
- **Issue Detection Agreement**: Detects 50-70% of same issues
- **Recommendation Quality**: Recommendations are generic but useful
- **Decision**: **Hybrid approach** - Use Claude for analysis, deepseek-r1 for regression tests only

### FAIL: <60% Agreement
- **Quality Score Agreement**: <6 of 10 conversations within 15 points
- **Issue Detection Agreement**: Detects <50% of same issues
- **Recommendation Quality**: Recommendations are unhelpful or incorrect
- **Decision**: **Reconsider feature** - Use Claude API (accept costs) or reduce scope

---

## Technical Context

### Sample Conversations to Validate

Create 10 diverse conversation scenarios covering:

1. **Greenfield Vague**: "build a app" → Should probe for details
2. **Greenfield Detailed**: "build a todo app with React and Firebase" → Should confirm understanding
3. **Brownfield Analysis**: "analyze this existing Python project" → Should use context
4. **Error Recovery**: Empty input or invalid command → Should handle gracefully
5. **Multi-Turn Clarification**: Vague → Probe → Clarify → Proceed flow
6. **Context Switching**: User changes topic mid-conversation
7. **Complex Requirements**: Multiple features, constraints, tech stack
8. **Ambiguous Intent**: Could be interpreted multiple ways
9. **Help Request**: "help me get started"
10. **Exit Flow**: "exit" or "quit"

### Analysis Dimensions

For each conversation, measure agreement on:

**1. Quality Score (0-100)**
- Overall conversation quality
- Agreement threshold: Within 15 points

**2. Issue Detection**
- Intent understanding issues
- Missed probing opportunities
- Unused context
- Poor response relevance

**3. Recommendation Quality**
- Specific vs generic
- Actionable vs vague
- Correct vs incorrect

### Implementation Approach

**Step 1: Create Sample Conversations**
```python
# tests/e2e/validation/sample_conversations.py

SAMPLE_CONVERSATIONS = [
    {
        "id": 1,
        "name": "greenfield_vague",
        "description": "User provides minimal information",
        "transcript": [
            {"user": "build a app", "brian": "I'd be happy to help..."},
            {"user": "a todo app", "brian": "Great! A todo app..."}
        ]
    },
    # ... 9 more conversations
]
```

**Step 2: Analyze with Claude**
```python
async def analyze_with_claude(conversation: dict) -> QualityReport:
    """Analyze conversation using Claude API (ground truth)."""
    provider = ProcessExecutor(
        project_root=Path.cwd(),
        provider_name="claude-code",
        provider_config={}
    )

    analyzer = ConversationAnalyzer(ai_service=AIAnalysisService(provider))
    return analyzer.analyze_conversation(conversation)
```

**Step 3: Analyze with deepseek-r1**
```python
async def analyze_with_deepseek(conversation: dict) -> QualityReport:
    """Analyze conversation using deepseek-r1 (local model)."""
    provider = ProcessExecutor(
        project_root=Path.cwd(),
        provider_name="opencode",
        provider_config={
            "ai_provider": "ollama",
            "use_local": True,
            "model": "deepseek-r1"
        }
    )

    analyzer = ConversationAnalyzer(ai_service=AIAnalysisService(provider))
    return analyzer.analyze_conversation(conversation)
```

**Step 4: Calculate Agreement**
```python
def calculate_agreement(
    claude_reports: List[QualityReport],
    deepseek_reports: List[QualityReport]
) -> ValidationResult:
    """Calculate agreement metrics."""

    score_agreement = 0
    issue_agreement = []

    for c_report, d_report in zip(claude_reports, deepseek_reports):
        # Score agreement (within 15 points)
        score_diff = abs(c_report.quality_score - d_report.quality_score)
        if score_diff <= 15:
            score_agreement += 1

        # Issue detection agreement
        c_issues = set(i.issue_type for i in c_report.issues)
        d_issues = set(i.issue_type for i in d_report.issues)

        if c_issues:
            overlap = len(c_issues & d_issues)
            recall = overlap / len(c_issues)
            issue_agreement.append(recall)

    return ValidationResult(
        score_agreement_pct=score_agreement / len(claude_reports) * 100,
        issue_detection_recall=sum(issue_agreement) / len(issue_agreement) * 100,
        conversations_analyzed=len(claude_reports)
    )
```

**Step 5: Generate Validation Report**
```python
def generate_validation_report(result: ValidationResult) -> str:
    """Generate validation report with Go/No-Go recommendation."""

    report = [
        "=" * 60,
        "deepseek-r1 QUALITY VALIDATION REPORT",
        "=" * 60,
        "",
        f"Conversations Analyzed: {result.conversations_analyzed}",
        f"Score Agreement: {result.score_agreement_pct:.1f}%",
        f"Issue Detection Recall: {result.issue_detection_recall:.1f}%",
        "",
        "-" * 60,
        "RECOMMENDATION",
        "-" * 60,
        ""
    ]

    if result.score_agreement_pct >= 80 and result.issue_detection_recall >= 70:
        report.extend([
            "STATUS: PASS",
            "",
            "deepseek-r1 demonstrates sufficient quality for conversation analysis.",
            "",
            "DECISION: PROCEED with Stories 37.1-37.4 using deepseek-r1",
            "",
            "Rationale:",
            f"- Score agreement ({result.score_agreement_pct:.1f}%) meets threshold (>80%)",
            f"- Issue detection ({result.issue_detection_recall:.1f}%) meets threshold (>70%)",
            "- Cost savings: $40-200/month by using local model",
            "- No degradation in analysis quality detected"
        ])
    elif result.score_agreement_pct >= 60:
        report.extend([
            "STATUS: PARTIAL PASS",
            "",
            "deepseek-r1 shows acceptable but imperfect quality.",
            "",
            "DECISION: HYBRID APPROACH",
            "",
            "Recommendation:",
            "- Use Claude API for conversation analysis (Mode 2) - $5-10/month",
            "- Use deepseek-r1 for regression tests (Mode 3) - $0/month",
            "",
            "Rationale:",
            f"- Score agreement ({result.score_agreement_pct:.1f}%) below ideal threshold",
            "- Quality matters more than cost for UX analysis",
            "- Regression tests can use local model (determinism > quality)"
        ])
    else:
        report.extend([
            "STATUS: FAIL",
            "",
            "deepseek-r1 quality insufficient for reliable analysis.",
            "",
            "DECISION: RECONSIDER FEATURE SCOPE",
            "",
            "Options:",
            "1. Use Claude API for all analysis (accept $10-50/month cost)",
            "2. Reduce Epic 387 scope (pattern-only detection, no AI analysis)",
            "3. Defer Epic 387 until better local models available",
            "",
            "Rationale:",
            f"- Score agreement ({result.score_agreement_pct:.1f}%) too low for trust",
            "- Poor analysis worse than no analysis (misleading recommendations)",
            "- Cost savings not worth unreliable quality insights"
        ])

    report.append("")
    report.append("=" * 60)

    return "\n".join(report)
```

### Dependencies

- Epic 3871: AIAnalysisService (for Claude API access)
- ollama with deepseek-r1 model
- Claude API key (for ground truth analysis)
- ConversationAnalyzer prototype (minimal implementation for POC)

---

## Test Scenarios

### Test 1: Create Sample Conversations
```python
def test_sample_conversations_cover_diversity():
    """Test sample conversations cover diverse scenarios."""
    from tests.e2e.validation.sample_conversations import SAMPLE_CONVERSATIONS

    assert len(SAMPLE_CONVERSATIONS) >= 10

    # Check diversity
    types = [conv["name"] for conv in SAMPLE_CONVERSATIONS]
    assert "greenfield" in str(types)
    assert "brownfield" in str(types)
    assert "error" in str(types)
    assert "vague" in str(types)
```

### Test 2: Agreement Calculation
```python
def test_agreement_calculation():
    """Test agreement metrics calculation."""
    claude_reports = [
        QualityReport(quality_score=85, issues=[
            QualityIssue(issue_type="intent_misunderstanding")
        ]),
        QualityReport(quality_score=70, issues=[
            QualityIssue(issue_type="missed_probing")
        ])
    ]

    deepseek_reports = [
        QualityReport(quality_score=80, issues=[  # Within 15 points
            QualityIssue(issue_type="intent_misunderstanding")
        ]),
        QualityReport(quality_score=90, issues=[  # >15 points difference
            QualityIssue(issue_type="unused_context")  # Different issue
        ])
    ]

    result = calculate_agreement(claude_reports, deepseek_reports)

    assert result.score_agreement_pct == 50.0  # 1 of 2 within threshold
    assert result.issue_detection_recall == 50.0  # 50% avg recall
```

---

## Definition of Done

- [ ] 10 sample conversations created and documented
- [ ] Claude analysis completed for all 10 conversations
- [ ] deepseek-r1 analysis completed for all 10 conversations
- [ ] Agreement metrics calculated and documented
- [ ] Validation report generated with recommendation
- [ ] Go/No-Go decision made by product team
- [ ] Alternative approach specified if FAIL or PARTIAL PASS
- [ ] Results documented in feature directory
- [ ] Decision communicated to development team

---

## Implementation Notes

### Files to Create

**New Files**:
- `tests/e2e/validation/__init__.py`
- `tests/e2e/validation/sample_conversations.py` - 10 sample conversations
- `tests/e2e/validation/poc_validator.py` - Validation logic
- `tests/e2e/validation/run_validation.py` - Execution script
- `docs/features/e2e-testing-ux-quality/POC_VALIDATION_REPORT.md` - Results

### Execution Steps

1. **Prepare**: Ensure ollama running with deepseek-r1, Claude API key set
2. **Run**: `python tests/e2e/validation/run_validation.py`
3. **Review**: Read generated validation report
4. **Decide**: Product team reviews and makes Go/No-Go decision
5. **Document**: Save report to `POC_VALIDATION_REPORT.md`
6. **Communicate**: Share decision with team

### Sample Validation Report Output

```
============================================================
deepseek-r1 QUALITY VALIDATION REPORT
============================================================

Conversations Analyzed: 10
Score Agreement: 85.0%
Issue Detection Recall: 72.0%

------------------------------------------------------------
RECOMMENDATION
------------------------------------------------------------

STATUS: PASS

deepseek-r1 demonstrates sufficient quality for conversation analysis.

DECISION: PROCEED with Stories 37.1-37.4 using deepseek-r1

Rationale:
- Score agreement (85.0%) meets threshold (>80%)
- Issue detection (72.0%) meets threshold (>70%)
- Cost savings: $40-200/month by using local model
- No degradation in analysis quality detected

============================================================
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| deepseek-r1 fails validation | Medium | Critical | Hybrid approach or Claude API fallback |
| Sample conversations not representative | Medium | High | Diverse scenarios, expert review |
| Agreement threshold too strict | Low | Medium | Adjust threshold if PARTIAL PASS reasonable |
| Claude API costs for POC | Low | Low | 10 conversations ~$0.50-1.00 (acceptable) |

---

## Estimated Costs

### POC Validation Costs
- Claude API: 10 conversations × ~$0.05-0.10 = **$0.50-1.00** (one-time)
- ollama/deepseek-r1: **$0** (local)
- **Total**: <$1

### Ongoing Costs (if PASS)
- deepseek-r1 for all analysis: **$0/month**
- Spot-checking with Claude (10% of analyses): **$2-5/month**
- **Total**: **$2-5/month** vs **$40-200/month** (Claude API only)

### Ongoing Costs (if PARTIAL PASS - Hybrid)
- Claude API for Mode 2 analysis: **$5-10/month**
- deepseek-r1 for Mode 3 regression: **$0/month**
- **Total**: **$5-10/month**

---

## Related Stories

- **Blocks**: ALL Epic 387 stories (2.1, 2.2, 2.3, 2.4)
- **Enables**: Go/No-Go decision for Epic 387 implementation
- **Related**: CRAAP Review Priority Issue #1 (Validate Local Model Quality)

---

## References

- PRD Section: Risk Assessment (HIGH RISK: Local Model Quality)
- CRAAP Review: Critical Finding (deepseek-r1 quality risk)
- CRAAP Review: Priority Issue #1 (Add Story 2.6: Quality Analyzer Validation Suite)
- Architecture Section: 3.1 ConversationAnalyzer
