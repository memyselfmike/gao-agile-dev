# E2E Testing & UX Quality Analysis System - Product Requirements Document

**Feature**: e2e-testing-ux-quality
**Epic Number**: TBD
**Owner**: Engineering Team
**Status**: Planning
**Created**: 2025-11-15
**Updated**: 2025-11-15

---

## Executive Summary

GAO-Dev's interactive Brian chat interface (Epic 30) and provider selection system (Epic 35) are production-ready and deployed as beta. However, we lack comprehensive E2E testing that validates the actual user experience. Current tests use mocks and don't exercise the real subprocess execution, Rich formatting, or conversational quality.

This feature adds a **three-mode testing system** that enables:
1. **Interactive debugging** where developers (including AI like Claude Code) can programmatically interact with Brian to identify UX issues
2. **Conversation quality analysis** that generates actionable UX improvement reports
3. **Automated regression tests** with fixture-based scenarios for CI/CD

**Critical constraint**: ALL tests must use **opencode provider with ollama/deepseek-r1** by default to enable cost-free development and testing (no Claude API costs).

---

## Problem Statement

### Current Gaps

1. **No Real E2E Testing**
   - Existing tests mock ProcessExecutor, ProviderSelector, ConversationalBrian
   - Never spawn actual `gao-dev start` subprocess
   - Don't test Rich formatting, ANSI codes, prompt-toolkit interaction
   - Miss bugs that only appear in real terminal execution

2. **No UX Quality Validation**
   - Tests verify "does it work?" but not "is the response good?"
   - Can't detect: poor intent understanding, missed probing opportunities, weak context usage
   - No framework to analyze conversation quality
   - No actionable recommendations for improving Brian's intelligence

3. **No Programmatic Testing Interface**
   - Developers can't interact with Brian programmatically to debug issues
   - Claude Code can't spawn Brian and test conversation scenarios
   - No way to capture and analyze real conversation flows

4. **API Cost Barrier**
   - Testing with Claude API is expensive ($0.003/1K tokens input, $0.015/1K tokens output)
   - Prevents frequent testing during development
   - CI/CD runs would incur significant costs
   - Developers hesitant to run comprehensive test suites

### Impact

- **User-reported bugs** slip through testing (poor UX not caught)
- **Slow iteration** on conversation quality improvements
- **Expensive testing** limits coverage and frequency
- **Limited observability** into Brian's decision-making

---

## Solution Overview

Build a **cost-free, three-mode E2E testing and UX quality analysis system** with these components:

### 1. Test Infrastructure (Cost-Free by Default)

**Provider Strategy:**
- **Default**: opencode + ollama/deepseek-r1 (zero API cost)
- **Override**: Environment variable `E2E_TEST_PROVIDER=claude-code` for occasional real API testing
- **Performance**: <2s per test with local model

**Instrumentation:**
- Add `--capture-mode` flag to `gao-dev start`
- Instrument ChatSession to log full conversations with context
- Persist transcripts to `.gao-dev/test_transcripts/` for analysis

### 2. Three Testing Modes

#### Mode 1: Interactive Debug (Claude ↔ Brian)

Framework allowing developers (especially AI like Claude Code) to:
- Spawn `gao-dev start --test-mode --capture-mode`
- Send inputs and receive outputs programmatically
- Analyze conversation quality in real-time
- Generate UX improvement reports

**Components:**
- `ClaudeTester` - Interactive testing harness
- `ChatHarness` - pexpect/wexpect wrapper for subprocess interaction
- `ConversationAnalyzer` - AI-powered quality analysis

**Workflow:**
```
Claude spawns gao-dev start
  ↓
Claude interacts with Brian (various scenarios)
  ↓
Conversation captured with full instrumentation
  ↓
Claude analyzes transcript for UX issues
  ↓
Report generated with specific recommendations
  ↓
Implement fixes
  ↓
Claude retests to verify improvements
```

#### Mode 2: Conversation Quality Analysis

Automated analysis of conversation transcripts to identify:
- **Intent Understanding**: Does Brian demonstrate understanding of user goals?
- **Probing Quality**: Does Brian ask clarifying questions when input is vague?
- **Context Usage**: Does Brian reference available context (project state, history)?
- **Response Relevance**: Are responses helpful and actionable?

**Analysis Output:**
- Turn-by-turn quality assessment
- Issue categorization (intent_misunderstanding, missed_probing_opportunity, etc.)
- Quality score (0-100%)
- Actionable recommendations with examples

#### Mode 3: Automated Regression Tests

Fixture-based tests for CI/CD:
- YAML scenarios with user input + expected output patterns
- Subprocess execution with pattern matching
- ANSI-aware output verification
- Headless, deterministic, parallelizable

**Test Coverage:**
- Greenfield initialization (vague → detailed requirements gathering)
- Brownfield analysis (existing project understanding)
- Error handling and recovery
- Multi-turn conversations
- Edge cases (empty input, Ctrl+C, long responses)

### 3. Key Components

#### ChatHarness
- Spawn `gao-dev start` subprocess via pexpect/wexpect
- Send input, capture output
- ANSI code stripping and pattern matching
- Windows/macOS/Linux compatible

#### FixtureLoader
- Load YAML test scenarios
- Provide scripted AI responses (for Mode 3)
- Validate scenario structure

#### ConversationAnalyzer
- Parse conversation transcripts
- Detect quality issues using pattern matching and AI analysis
- Generate quality scores and recommendations
- Support both automated and manual analysis

#### AI Response Injector
- Inject pre-scripted responses in test mode
- Load from YAML fixtures
- Enable deterministic testing

---

## User Stories

### Epic: E2E Testing Infrastructure

**Story 1: Cost-Free Test Execution**
- As a developer, I want ALL tests to use opencode/ollama/deepseek-r1 by default so that I can run comprehensive test suites without API costs

**Story 2: Test Mode Support**
- As a test framework, I want `gao-dev start` to support `--test-mode` and `--capture-mode` flags so that I can control Brian's behavior and capture conversations

**Story 3: ChatHarness Implementation**
- As a test developer, I want a ChatHarness class that spawns `gao-dev start` as subprocess and allows programmatic interaction

**Story 4: Fixture System**
- As a test developer, I want to define test scenarios in YAML files with user inputs and expected outputs

### Epic: Interactive Testing & Quality Analysis

**Story 5: ClaudeTester Framework**
- As Claude Code, I want to spawn Brian and interact with it programmatically so that I can test conversation scenarios and identify UX issues

**Story 6: Conversation Instrumentation**
- As a quality analyst, I want full conversation capture with context, timestamps, and internal reasoning so that I can analyze decision-making

**Story 7: Quality Analyzer**
- As a developer, I want automated analysis of conversation transcripts that identifies specific UX deficiencies with actionable recommendations

**Story 8: Quality Reporting**
- As a developer, I want detailed quality reports showing turn-by-turn analysis, quality scores, and improvement suggestions

### Epic: Regression Testing & CI/CD

**Story 9: ANSI-Aware Output Verification**
- As a test framework, I want pattern matching that strips ANSI codes and matches against expected output patterns

**Story 10: E2E Test Suite**
- As a QA engineer, I want 20+ E2E test scenarios covering greenfield, brownfield, errors, and edge cases

**Story 11: CI/CD Integration**
- As a DevOps engineer, I want tests to run in CI/CD with headless execution, parallel runs, and fast feedback

**Story 12: Fixture Conversion Tool**
- As a developer, I want to convert real user conversation transcripts into regression test fixtures

---

## Functional Requirements

### FR1: Provider Configuration

**FR1.1** - System MUST default to opencode provider with ollama/deepseek-r1 model for all tests
**FR1.2** - System MUST support `E2E_TEST_PROVIDER` environment variable to override provider
**FR1.3** - System MUST validate ollama is running before test execution
**FR1.4** - System MUST provide clear error messages if local model unavailable

### FR2: Test Modes

**FR2.1** - `gao-dev start` MUST support `--test-mode` flag for fixture-based testing
**FR2.2** - `gao-dev start` MUST support `--capture-mode` flag for conversation logging
**FR2.3** - Test mode MUST load responses from fixture files instead of calling AI
**FR2.4** - Capture mode MUST log full conversation with metadata to `.gao-dev/test_transcripts/`

### FR3: Interactive Testing

**FR3.1** - ClaudeTester MUST spawn `gao-dev start` as subprocess
**FR3.2** - ChatHarness MUST support send/receive operations with timeout
**FR3.3** - System MUST capture full output including ANSI codes
**FR3.4** - System MUST strip ANSI for pattern matching
**FR3.5** - System MUST support Windows (wexpect), macOS, Linux (pexpect)

### FR4: Quality Analysis

**FR4.1** - ConversationAnalyzer MUST identify intent understanding issues
**FR4.2** - ConversationAnalyzer MUST detect missed probing opportunities
**FR4.3** - ConversationAnalyzer MUST detect unused context
**FR4.4** - ConversationAnalyzer MUST generate quality score (0-100%)
**FR4.5** - Reports MUST include turn-by-turn analysis with examples
**FR4.6** - Reports MUST provide actionable recommendations

### FR5: Regression Testing

**FR5.1** - System MUST support YAML fixture format for test scenarios
**FR5.2** - Fixtures MUST specify user inputs and expected output patterns
**FR5.3** - System MUST validate outputs match expected patterns
**FR5.4** - System MUST fail tests on pattern mismatch with clear diff
**FR5.5** - System MUST support parallel test execution

---

## Non-Functional Requirements

### NFR1: Performance

- Test execution time <2s per test with local model
- Conversation capture overhead <5% vs normal execution
- Quality analysis <10s per conversation
- CI/CD test suite completes <5 minutes

### NFR2: Cost

- **Zero API costs** for default test execution
- Optional Claude API testing for high-stakes scenarios only
- Estimated savings: $10-50/month per developer

### NFR3: Reliability

- 100% test pass rate on clean build
- No flaky tests (deterministic with fixtures)
- Timeout handling prevents hung tests
- Proper cleanup of subprocess resources

### NFR4: Compatibility

- Windows, macOS, Linux support
- Python 3.10+ compatibility
- Works with existing provider architecture (Epic 21, 35)
- Zero regressions in 400+ existing tests

### NFR5: Maintainability

- YAML fixtures easy to read and edit
- Clear error messages for test failures
- Conversation logs human-readable
- Quality reports actionable and specific

---

## Technical Requirements

### TR1: Dependencies

**New Dependencies:**
- `pexpect` (Unix) / `wexpect` (Windows) - subprocess interaction
- `pyyaml` - fixture loading (already installed)
- `pytest-timeout` - test timeout management

**Provider Requirements:**
- ollama running locally with deepseek-r1 model
- opencode CLI installed and on PATH

### TR2: Architecture

**Test Infrastructure:**
```
tests/e2e/
├── chat/                          # E2E chat tests
│   ├── test_chat_subprocess.py    # Subprocess-based tests
│   ├── test_chat_workflows.py     # Full workflow tests
│   └── test_chat_error_handling.py
│
├── fixtures/                       # Test scenarios
│   ├── greenfield_init.yaml
│   ├── brownfield_analysis.yaml
│   └── error_recovery.yaml
│
├── harness/                        # Test infrastructure
│   ├── chat_harness.py             # pexpect wrapper
│   ├── fixture_loader.py
│   ├── output_matcher.py
│   └── ai_response_injector.py
│
└── analysis/                       # Quality analysis
    ├── conversation_analyzer.py
    ├── quality_scorer.py
    └── report_generator.py
```

**Integration Points:**
- ChatREPL: Add `--test-mode`, `--capture-mode` flags
- ChatSession: Add conversation logging
- ConversationalBrian: Support fixture response injection
- ProviderSelector: Respect E2E_TEST_PROVIDER env var

### TR3: Data Models

```python
@dataclass
class TestScenario:
    name: str
    description: str
    steps: List[TestStep]

@dataclass
class TestStep:
    user_input: str
    expect_output: List[str]  # Regex patterns
    brian_response: Optional[str]  # For test mode
    timeout_ms: int = 5000

@dataclass
class ConversationTurn:
    timestamp: str
    user_input: str
    brian_response: str
    context_used: dict
    internal_reasoning: Optional[str]

@dataclass
class QualityIssue:
    turn_num: int
    issue_type: str
    severity: str
    description: str
    suggestion: str

@dataclass
class QualityReport:
    transcript_path: Path
    total_turns: int
    quality_score: float
    issues: List[QualityIssue]
    recommendations: List[str]
```

---

## Acceptance Criteria

### Phase 1: Infrastructure (Week 1)
- [ ] ChatHarness can spawn `gao-dev start` and interact
- [ ] ANSI stripping and pattern matching working
- [ ] FixtureLoader loads YAML scenarios
- [ ] ChatREPL supports `--test-mode` flag
- [ ] All tests use opencode/deepseek-r1 by default
- [ ] 5 basic E2E tests passing

### Phase 2: Quality Analysis (Week 2)
- [ ] ChatSession captures conversations to disk
- [ ] ConversationAnalyzer detects 3+ issue types
- [ ] Quality scoring algorithm implemented
- [ ] ClaudeTester framework operational
- [ ] Quality reports generate with examples
- [ ] 1 full interactive test session documented

### Phase 3: Regression Testing (Week 3)
- [ ] 20+ E2E test scenarios implemented
- [ ] CI/CD integration complete
- [ ] Parallel test execution working
- [ ] Test suite completes <5 minutes
- [ ] Fixture conversion tool created
- [ ] All tests passing in CI

### Phase 4: Polish & Documentation (Week 4)
- [ ] User guide for writing E2E tests
- [ ] Developer guide for using ClaudeTester
- [ ] Quality analysis interpretation guide
- [ ] Example conversation analyses
- [ ] Zero regressions in existing tests
- [ ] Performance benchmarks documented

---

## Dependencies

### Internal Dependencies
- Epic 21: AI Analysis Service & Provider Abstraction
- Epic 30: Interactive Brian Chat Interface
- Epic 35: Interactive Provider Selection
- Existing provider architecture (ProcessExecutor, ProviderFactory)

### External Dependencies
- ollama installed and running
- deepseek-r1 model downloaded
- opencode CLI on PATH
- pexpect/wexpect libraries

### Risks & Mitigations

**Risk**: ollama not installed on developer machine
**Mitigation**: Clear setup documentation, validation in test setup, fallback to mock mode

**Risk**: pexpect incompatibility on Windows
**Mitigation**: Use wexpect for Windows, comprehensive cross-platform testing

**Risk**: ANSI code variations across terminals
**Mitigation**: Robust ANSI stripping regex, pattern matching vs exact matching

**Risk**: Test flakiness with subprocess timing
**Mitigation**: Generous timeouts, retry logic, clear timeout errors

---

## Timeline

**Total Duration**: 4 weeks
**Story Points**: ~60 points

### Week 1: Infrastructure (15 points)
- ChatHarness implementation
- Fixture system
- Test mode support in ChatREPL
- Basic E2E tests

### Week 2: Quality Analysis (20 points)
- Conversation instrumentation
- ConversationAnalyzer
- Quality scoring
- ClaudeTester framework
- Report generation

### Week 3: Regression Testing (15 points)
- Comprehensive test scenarios
- CI/CD integration
- Parallel execution
- Fixture conversion tool

### Week 4: Polish & Documentation (10 points)
- User guides
- Example analyses
- Performance optimization
- Final QA

---

## Success Metrics

### Development Metrics
- **Test Cost**: $0 (100% local model usage)
- **Test Execution Time**: <2s per test, <5min full suite
- **Test Coverage**: 20+ E2E scenarios
- **Code Coverage**: >85% for new code

### Quality Metrics
- **UX Issues Detected**: 5+ specific issues identified in first analysis
- **Quality Score Accuracy**: Manual review validates 90%+ of detected issues
- **Recommendation Quality**: 80%+ of recommendations actionable

### Adoption Metrics
- **CI/CD Integration**: Tests run on every PR
- **Developer Usage**: 3+ developers use ClaudeTester for debugging
- **Fixture Growth**: 10+ new fixtures added per month

### Business Metrics
- **Cost Savings**: $40-200/month in API costs avoided
- **Bug Prevention**: 50% reduction in UX bugs reaching production
- **Iteration Speed**: 2x faster UX improvement cycles

---

## Out of Scope

### Future Work (Not in MVP)
- Performance benchmarking of response times
- Multi-user concurrent chat testing
- Voice/audio interface testing
- Mobile app testing
- A/B testing framework for prompt variations
- Automated prompt optimization based on quality scores

### Explicitly Not Included
- Testing of non-chat CLI commands (existing tests cover this)
- Integration with external bug tracking systems
- Automated fixing of detected issues (only analysis + recommendations)
- Real-time quality monitoring in production

---

## Risk Assessment

### Technical Risks

**HIGH RISK: Local Model Quality**
- deepseek-r1 may produce lower quality responses than Claude
- **Mitigation**: Comprehensive fixture coverage, occasional Claude API validation
- **Acceptance**: Some quality degradation acceptable for cost savings

**MEDIUM RISK: Cross-Platform Compatibility**
- pexpect/wexpect behavior may differ across OS
- **Mitigation**: CI/CD testing on Windows, macOS, Linux
- **Acceptance**: OS-specific test fixtures if needed

**LOW RISK: Performance**
- Subprocess overhead may slow tests
- **Mitigation**: Parallel execution, caching, timeout optimization
- **Acceptance**: 5min CI time acceptable

### Process Risks

**MEDIUM RISK: Fixture Maintenance**
- Fixtures may become stale as Brian's prompts evolve
- **Mitigation**: Automated fixture validation, version tracking
- **Acceptance**: Monthly fixture review process

**LOW RISK: Team Adoption**
- Developers may not use ClaudeTester for debugging
- **Mitigation**: Clear documentation, demo sessions, success stories
- **Acceptance**: Even 1 developer using it provides value

---

## Appendix

### Related Documents
- Epic 21: AI Analysis Service & Provider Abstraction
- Epic 30: Interactive Brian Chat Interface
- Epic 35: Interactive Provider Selection
- CLAUDE.md: GAO-Dev Project Guide

### References
- pexpect documentation: https://pexpect.readthedocs.io/
- wexpect (Windows): https://pypi.org/project/wexpect/
- ollama: https://ollama.ai/
- deepseek-r1 model: https://ollama.ai/library/deepseek-r1

### Glossary
- **E2E**: End-to-end (testing from user perspective)
- **UX**: User experience
- **ANSI codes**: Terminal formatting escape sequences
- **Fixture**: Pre-defined test scenario with inputs/outputs
- **Capture mode**: Instrumented execution that logs conversations
- **Test mode**: Execution using scripted responses instead of AI
