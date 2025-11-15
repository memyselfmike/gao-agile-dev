# Story 3.1: ClaudeTester Framework

**Story ID**: 3.1
**Epic**: 3 - Interactive Testing Tools
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Story Points**: 5
**Priority**: Medium (Optional/Phase 2)

---

## User Story

**As** Claude Code (AI assistant)
**I want** to spawn Brian and interact with it programmatically
**So that** I can test conversation scenarios and identify UX issues

---

## Acceptance Criteria

- [ ] **AC1**: ClaudeTester.start_session() spawns `gao-dev start --capture-mode`
- [ ] **AC2**: ClaudeTester.send(message) sends input and returns Brian response
- [ ] **AC3**: ClaudeTester.end_session_and_analyze() generates QualityReport
- [ ] **AC4**: Framework uses ChatHarness for subprocess management
- [ ] **AC5**: Framework uses ConversationAnalyzer for quality analysis
- [ ] **AC6**: Example interactive test session documented
- [ ] **AC7**: API is simple and intuitive for AI usage
- [ ] **AC8**: Works from Python scripts and notebooks

---

## Technical Context

From Architecture section 1.1 (ClaudeTester), provides interactive testing framework for AI-driven debugging.

**Usage Example**:
```python
tester = ClaudeTester(scenario="greenfield_vague_request")
tester.start_session()

response = tester.send("build a app")
response = tester.send("a todo app")

report = tester.end_session_and_analyze()
print(f"Quality Score: {report.quality_score}%")
```

---

## Dependencies

- **Depends On**: Epic 1 (ChatHarness), Epic 2 (ConversationAnalyzer)
- **Blocks**: None (optional tooling)

---

## References

- PRD Section: Solution Overview - Mode 1
- Architecture Section: 1.1 ClaudeTester
