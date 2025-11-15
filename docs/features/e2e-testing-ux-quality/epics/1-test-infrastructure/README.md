# Epic 1: Test Infrastructure

**Epic ID**: 1
**Feature**: e2e-testing-ux-quality
**Status**: Not Started
**Total Story Points**: 20

---

## Epic Definition

Build the core testing infrastructure that enables cost-free E2E testing of the interactive Brian chat interface using subprocess spawning, local AI models (opencode/ollama/deepseek-r1), and fixture-based test scenarios.

This epic establishes the foundation for all three testing modes (Interactive Debug, Quality Analysis, Regression Tests) by providing the critical infrastructure components: ChatHarness for subprocess interaction, FixtureLoader for scenario management, OutputMatcher for validation, and test mode flags in ChatREPL.

**Critical Constraint**: ALL tests must use opencode/ollama/deepseek-r1 by default to ensure zero API costs.

---

## Business Value

Without this infrastructure, we cannot:
- Validate Brian's behavior in real terminal execution (current tests use mocks)
- Test Rich formatting, ANSI codes, prompt-toolkit interaction
- Run comprehensive E2E tests without expensive API costs
- Programmatically interact with Brian for quality analysis

This epic enables cost-free development and testing, removing the financial barrier that limits test coverage.

---

## Goals

1. **Cost-Free Testing**: Enable developers to run comprehensive E2E tests with zero API costs
2. **Real E2E Validation**: Test actual subprocess execution, not mocked components
3. **Cross-Platform Support**: Work on Windows, macOS, Linux
4. **Fixture-Based Testing**: Enable deterministic, repeatable test scenarios
5. **Foundation for Modes 1-3**: Provide reusable infrastructure for all testing modes

---

## Acceptance Criteria

- [ ] ChatHarness can spawn `gao-dev start` subprocess and interact programmatically
- [ ] ChatHarness works on Windows (wexpect), macOS (pexpect), and Linux (pexpect)
- [ ] ANSI code stripping and pattern matching working correctly
- [ ] FixtureLoader loads and validates YAML test scenarios
- [ ] ChatREPL supports `--test-mode` and `--capture-mode` flags
- [ ] All tests default to opencode/ollama/deepseek-r1 provider
- [ ] Provider can be overridden via `E2E_TEST_PROVIDER` environment variable
- [ ] 5+ basic E2E tests passing using the infrastructure
- [ ] Test execution time <5s per test (subprocess + AI inference)
- [ ] Zero API costs for test execution

---

## Dependencies

### Internal Dependencies
- Epic 21: AI Analysis Service & Provider Abstraction (provides provider system)
- Epic 30: Interactive Brian Chat Interface (provides `gao-dev start` command)
- Epic 35: Interactive Provider Selection (provides provider configuration)

### External Dependencies
- ollama installed and running locally
- deepseek-r1 model downloaded to ollama
- opencode CLI installed and on PATH
- pexpect library (Unix/macOS)
- wexpect library (Windows)

### Blocked By
None - this is the foundation epic

### Blocks
- Epic 2: UX Quality Analysis (depends on test infrastructure)
- Epic 3: Interactive Testing Tools (depends on test infrastructure)

---

## Stories

1. **Story 1.1**: Cost-Free Test Execution (3 points)
2. **Story 1.2**: Test Mode Support in ChatREPL (5 points)
3. **Story 1.3**: ChatHarness Implementation (8 points)
4. **Story 1.4**: Fixture System (4 points)

**Total**: 20 story points

---

## Technical Notes

### Architecture Highlights

**ChatHarness**: Cross-platform subprocess wrapper using pexpect (Unix) or wexpect (Windows)
- Spawns `gao-dev start` subprocess
- Sends input via stdin
- Captures output from stdout/stderr
- Strips ANSI codes for pattern matching
- Handles timeouts and cleanup

**FixtureLoader**: YAML-based test scenario management
- Loads test scenarios from YAML files
- Validates fixture schema
- Provides scripted AI responses for test mode
- Enables deterministic testing

**Provider Configuration**: Three-tier precedence
1. `E2E_TEST_PROVIDER` environment variable (highest)
2. `AGENT_PROVIDER` environment variable (global preference)
3. Default: opencode/ollama/deepseek-r1 (cost-free)

### Risk Mitigation

**Risk**: pexpect/wexpect platform inconsistencies
**Mitigation**: Comprehensive cross-platform testing, path normalization utilities

**Risk**: Subprocess timing flakiness
**Mitigation**: Generous timeouts (5s per test), retry logic, heartbeat signals

**Risk**: Ollama not installed on developer machine
**Mitigation**: Clear setup documentation, validation in test setup, graceful error messages

---

## Testing Strategy

### Unit Tests
- ChatHarness: Process spawning, ANSI stripping, pattern matching
- FixtureLoader: YAML parsing, schema validation
- OutputMatcher: Regex matching, diff generation

### Integration Tests
- ChatHarness + gao-dev start: Full subprocess interaction
- Fixture-based tests: End-to-end scenario execution

### Cross-Platform Tests
- Windows 10+ with wexpect
- macOS with pexpect
- Ubuntu 20.04+ with pexpect

---

## Success Metrics

- [ ] 5+ E2E tests passing consistently (100% pass rate)
- [ ] Test execution time <5s per test
- [ ] Zero API costs ($0) for test execution
- [ ] Cross-platform compatibility (Windows, macOS, Linux)
- [ ] Developer setup time <10 minutes
- [ ] 85%+ test coverage for new infrastructure code

---

## Out of Scope

- Quality analysis implementation (Epic 2)
- Interactive debugging tools (Epic 3)
- CI/CD integration (deferred to Epic 3)
- Performance benchmarking
- AI-powered deep analysis

---

## References

- PRD: `docs/features/e2e-testing-ux-quality/PRD.md`
- Architecture: `docs/features/e2e-testing-ux-quality/ARCHITECTURE.md`
- CRAAP Review: `docs/features/e2e-testing-ux-quality/CRAAP_Review_E2E_Testing_UX_Quality_Analysis.md`
