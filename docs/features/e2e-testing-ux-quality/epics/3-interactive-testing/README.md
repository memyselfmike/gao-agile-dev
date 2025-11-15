# Epic 3: Interactive Testing Tools

**Epic ID**: 3
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Total Story Points**: 18

---

## Epic Definition

Build interactive testing tools and comprehensive regression test suite that enable developers (especially AI like Claude Code) to programmatically test Brian, and establish CI/CD integration for automated E2E testing.

This epic delivers:
- **Mode 1**: ClaudeTester framework for interactive debugging
- **Mode 3**: Comprehensive regression test suite with 20+ scenarios
- CI/CD integration for automated testing
- Fixture conversion tools for capturing real conversations

**Note**: This epic is considered OPTIONAL or PHASE 2. Based on CRAAP review recommendations, the core value (UX quality improvement) is delivered by Epic 2. Epic 3 provides developer tooling and automation but may be split into a separate feature.

---

## Business Value

While Epic 2 delivers UX quality analysis, Epic 3 provides:
- **Developer Productivity**: Tools for testing Brian programmatically
- **Regression Prevention**: Automated tests prevent quality degradation
- **CI/CD Integration**: Tests run on every PR with zero cost
- **Documentation**: Real conversation examples captured as fixtures

**However**, CRAAP review suggests this may be over-engineering for initial MVP. Consider deferring to Phase 2 or separate feature.

---

## Goals

1. **Interactive Debugging**: Enable Claude Code to test Brian programmatically
2. **Regression Testing**: 20+ automated E2E test scenarios
3. **CI/CD Integration**: Tests run in GitHub Actions with ollama
4. **Fixture Library**: Capture real conversations as reusable test fixtures

---

## Acceptance Criteria

- [ ] **AC1**: ClaudeTester framework enables interactive Brian testing
- [ ] **AC2**: 20+ E2E test scenarios covering greenfield, brownfield, errors, edge cases
- [ ] **AC3**: Tests run in CI/CD with ollama/deepseek-r1 (zero cost)
- [ ] **AC4**: Test suite completes in <8 minutes
- [ ] **AC5**: Parallel test execution working (pytest-xdist)
- [ ] **AC6**: Fixture conversion tool captures real conversations
- [ ] **AC7**: All tests passing consistently (100% pass rate on clean build)
- [ ] **AC8**: Documentation complete (user guide, developer guide)

---

## Dependencies

### Internal Dependencies
- Epic 1: Test Infrastructure (ChatHarness, FixtureLoader)
- Epic 2: UX Quality Analysis (ConversationAnalyzer for reports)

### External Dependencies
- CI/CD environment with ollama support
- pytest-xdist for parallel execution
- GitHub Actions configuration

### Blocked By
- Epic 1 must be complete
- Optionally Epic 2 (for quality reports)

---

## Stories

1. **Story 3.1**: ClaudeTester Framework (5 points)
2. **Story 3.2**: E2E Test Suite (8 points)
3. **Story 3.3**: CI/CD Integration (3 points)
4. **Story 3.4**: Fixture Conversion Tool (2 points)

**Total**: 18 story points

---

## Recommendation: Consider Splitting or Deferring

Based on CRAAP review (Perspective section #3):

**Analysis**:
- Mode 1 (ClaudeTester): Useful for AI developers, but niche use case
- Mode 3 (Regression Tests): Standard testing practice, not unique value
- Epic 2 (Quality Analysis): Delivers core UX improvement value

**Options**:
1. **Defer to Phase 2**: Ship Epic 1 + Epic 2 first (faster value delivery)
2. **Split Feature**: Make Epic 3 a separate feature "E2E Test Automation"
3. **Proceed as Planned**: All 3 epics in one feature (comprehensive but slower)

**Recommendation**: **Discuss with product team** before starting Epic 3 implementation

---

## Technical Notes

### ClaudeTester Architecture

**Purpose**: Framework for Claude Code to interact with Brian programmatically

**Key Features**:
- Spawn Brian subprocess
- Send messages programmatically
- Analyze conversation quality
- Generate improvement reports

**Use Case**: AI-driven debugging and quality validation

### Regression Test Suite

**Coverage**:
- Greenfield initialization (vague → detailed)
- Brownfield analysis (existing project)
- Error handling and recovery
- Multi-turn conversations
- Edge cases (empty input, Ctrl+C, long responses)

**Execution**: pytest with pytest-xdist for parallelization

### CI/CD Challenges

**Risks**:
- Ollama installation time in CI (5-10 minutes)
- Model download time (may be large)
- Disk space limitations on CI runners

**Mitigations**:
- Pre-build Docker image with ollama + deepseek-r1
- Cache model downloads
- Fallback to mock mode if ollama unavailable

---

## Success Metrics

- **Test Coverage**: 20+ E2E scenarios implemented
- **Test Execution Time**: <8 minutes full suite
- **Test Reliability**: 100% pass rate on clean build
- **CI/CD Cost**: $0 (ollama local model)
- **Developer Adoption**: 3+ developers use ClaudeTester for debugging

---

## Out of Scope

- A/B testing framework for prompt variations
- Performance benchmarking of response times
- Multi-user concurrent chat testing
- Real-time quality monitoring in production
- Automated fixing of detected issues

---

## References

- PRD: User Stories - Epic 3 (Interactive Testing Tools)
- Architecture: Section 1.1 ClaudeTester, Section 1.2 RegressionTestRunner
- CRAAP Review: Perspective #3 (Challenging three-mode assumption)
