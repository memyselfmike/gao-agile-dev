# Web Interface QA Documentation

**Feature**: Browser-Based Web Interface for GAO-Dev
**Epic Number**: 39
**Test Architect**: Murat
**Version**: 1.0
**Last Updated**: 2025-01-16

---

## Overview

This directory contains the complete test strategy and quality assurance documentation for Epic 39 (Web Interface). The strategy covers **8 testing levels** with comprehensive plans for linting, unit testing, integration testing, regression testing, E2E testing (AI-powered via Playwright MCP), performance testing, accessibility testing, and security testing.

## Documents in This Directory

### 1. TEST_STRATEGY.md (Primary Document)

**Purpose**: Comprehensive testing strategy covering all 8 testing levels

**Contents**:
- Level 1: Linting and Code Quality (ESLint, Ruff, Black, MyPy)
- Level 2: Unit Testing (Vitest, pytest, 85% coverage target)
- Level 3: Integration Testing (API + WebSocket + Frontend)
- Level 4: Regression Testing (Zero CLI regressions, performance benchmarks)
- Level 5: E2E Testing (Playwright MCP, 14 scenarios)
- Level 6: Performance Testing (Lighthouse, k6, P95 metrics)
- Level 7: Accessibility Testing (WCAG 2.1 AA, axe-core)
- Level 8: Security Testing (Bandit, OWASP ZAP, attack vectors)
- CI/CD Pipeline Integration (GitHub Actions)
- Story-Level Test Plans (39 stories)
- Quality Gates (Definition of Done, Release Criteria)
- Tools and Frameworks
- Metrics and Reporting

**Length**: ~21,000 lines
**Coverage**: All 3 phases (MVP, V1.1, V1.2)

### 2. E2E_TEST_PLAN.md (E2E Focused)

**Purpose**: Detailed E2E test plan for Claude Code using Playwright MCP

**Contents**:
- Playwright MCP Setup Instructions
- Semantic HTML Requirements (AI-testable by design)
- data-testid Naming Conventions (stable selectors)
- 14 E2E Scenarios (6 MVP, 4 V1.1, 4 V1.2)
- Complete Given/When/Then specifications
- Test implementations (TypeScript)
- Screenshot Comparison Strategy (visual regression)
- Test Execution Guide
- Troubleshooting

**Length**: ~9,500 lines
**Coverage**: All 14 E2E scenarios across 3 phases

### 3. README.md (This File)

**Purpose**: Navigation guide for QA documentation

---

## Quick Start

### For Developers

**Before starting implementation**:

1. **Read TEST_STRATEGY.md** - Understand testing levels and targets
2. **Review E2E_TEST_PLAN.md** - Understand semantic HTML requirements and data-testid conventions
3. **Set up linting** - Install ESLint, Prettier, Ruff, Black, MyPy
4. **Configure pre-commit hooks** - Use `.pre-commit-config.yaml` from TEST_STRATEGY.md
5. **Write tests first** (ATDD approach) - Acceptance tests define "done" before implementation

### For Claude Code (AI Tester)

**To test GAO-Dev via Playwright MCP**:

1. **Read E2E_TEST_PLAN.md** - Complete test scenarios and setup
2. **Install Playwright** - `npx playwright install chromium`
3. **Start server** - `gao-dev start --web --test-mode`
4. **Run tests** - `npx playwright test`
5. **Review results** - `npx playwright show-report`

### For Test Reviewers

**To review test strategy**:

1. **TEST_STRATEGY.md** - Comprehensive testing approach
   - Verify all 8 levels covered
   - Check coverage targets (85% unit, 80% integration)
   - Review quality gates (Definition of Done, Release Criteria)
   - Validate CI/CD pipeline design

2. **E2E_TEST_PLAN.md** - E2E scenarios and AI testability
   - Verify 14 scenarios cover critical paths
   - Check semantic HTML requirements are clear
   - Validate data-testid naming conventions
   - Review screenshot comparison strategy

---

## Testing Levels Summary

### Level 1: Linting and Code Quality

**Tools**:
- Frontend: ESLint, Prettier, TypeScript (strict mode)
- Backend: Ruff, Black, MyPy (strict mode), Bandit

**Quality Gate**: 0 errors, <10 warnings

**Pre-Commit Hooks**: All linters run before commit

### Level 2: Unit Testing

**Tools**:
- Frontend: Vitest, React Testing Library
- Backend: pytest, pytest-asyncio

**Coverage Target**: >85% business logic

**Test Organization**:
- Frontend: `src/**/*.test.tsx`
- Backend: `tests/web/unit/**/*.py`

### Level 3: Integration Testing

**Scope**:
- Frontend: Component integration, WebSocket message flow, API integration
- Backend: ChatREPL integration, GitIntegratedStateManager integration, WebSocket event flow

**Coverage Target**: >80% critical paths

**Test Organization**:
- Frontend: `src/**/*.integration.test.tsx`
- Backend: `tests/web/integration/**/*.py`

### Level 4: Regression Testing

**Scope**:
- CLI functionality (zero regressions)
- Performance benchmarks (P95 metrics)
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Responsive design (1024px, 1440px, 1920px)

**Test Organization**: `tests/regression/**/*.py`, `tests/e2e/regression/**/*.ts`

### Level 5: E2E Testing (Playwright MCP)

**Tool**: Playwright (AI-driven via MCP)

**Scenarios**: 14 total
- Phase 1 (MVP): 6 scenarios
- Phase 2 (V1.1): 4 scenarios
- Phase 3 (V1.2): 4 scenarios

**Coverage Target**: All critical user journeys

**Test Organization**: `tests/e2e/**/*.spec.ts`

**Key Feature**: Claude Code acts as automated beta tester

### Level 6: Performance Testing

**Tools**: Lighthouse, k6, Performance API

**Metrics** (P95):
- Page load: <2s
- Event latency: <100ms
- Activity stream render: <200ms (1,000 events)
- File tree render: <300ms (500 files)
- Monaco load: <500ms

**Test Organization**: `tests/performance/**/*.ts`, `tests/load/**/*.js`

### Level 7: Accessibility Testing

**Standard**: WCAG 2.1 AA (100% compliance)

**Tools**: axe-core, Lighthouse, VoiceOver, NVDA

**Requirements**:
- Color contrast: 4.5:1 (normal text), 3:1 (large text)
- 100% keyboard accessible
- Screen reader compatible
- Semantic HTML throughout
- ARIA labels for all interactive elements

**Test Organization**: `tests/e2e/accessibility/**/*.spec.ts`

### Level 8: Security Testing

**Tools**: Bandit, npm audit, Safety, OWASP ZAP

**Attack Vectors**:
- WebSocket session hijacking
- CORS bypass
- Path traversal
- Command injection
- XSS
- CSRF
- Session lock bypass

**Quality Gate**: 0 high/medium vulnerabilities

**Test Organization**: `tests/security/**/*.py`

---

## Coverage Targets

| Test Level | Target | Measurement |
|-----------|--------|-------------|
| **Unit Tests (Frontend)** | >85% | Vitest coverage report |
| **Unit Tests (Backend)** | >85% | pytest --cov report |
| **Integration Tests** | >80% | Combined coverage |
| **E2E Tests** | 14 scenarios | Playwright test results |
| **Performance Tests** | All P95 metrics | Lighthouse, k6 |
| **Accessibility** | 100% WCAG 2.1 AA | axe-core, manual audit |
| **Security** | 0 high/medium | Bandit, npm audit, OWASP ZAP |

---

## Quality Gates

### Pull Request Quality Gate

**All PRs must pass**:

1. **Linting** - 0 errors, <10 warnings
2. **Unit Tests** - All pass, >85% coverage
3. **Integration Tests** - All pass
4. **Type Checking** - 0 errors (strict mode)
5. **Security Scan** - 0 high/medium issues

**If any gate fails**: PR cannot merge

### Release Quality Gate (MVP)

**MVP Release requires**:

1. **Functional Completeness** - All 14 stories complete (39.1-39.14)
2. **Performance** - All P95 metrics <targets
3. **Accessibility** - WCAG 2.1 AA (100% compliance)
4. **Security** - 0 high/medium vulnerabilities
5. **E2E Tests** - 6 MVP scenarios passing
6. **Zero Regressions** - 100% existing CLI tests pass
7. **Beta Testing** - >80% satisfaction, ≥5 AI-discovered UX issues

---

## CI/CD Pipeline

### GitHub Actions Workflow

**Stages** (all must pass):

1. **Linting** - ESLint, Ruff, Black, MyPy, Bandit
2. **Unit Tests** - Frontend (Vitest) + Backend (pytest)
3. **Integration Tests** - API + WebSocket + Frontend integration
4. **E2E Tests** - Playwright (all scenarios)
5. **Performance Tests** - Lighthouse CI, k6 load tests
6. **Accessibility Tests** - axe-core (0 violations)
7. **Security Tests** - npm audit, Safety, OWASP ZAP

**Matrix Testing**:
- Python: 3.11, 3.12
- Node.js: 18, 20
- OS: Ubuntu, macOS, Windows
- Browsers: Chrome, Firefox, Safari, Edge

**Artifacts**:
- Test results (JSON, HTML)
- Coverage reports (HTML, XML)
- Playwright videos (failures only)
- Lighthouse reports
- Accessibility reports
- Security scan results

---

## Story-Level Test Breakdown

### High-Risk Stories (Comprehensive Testing)

**Story 39.2: WebSocket Manager and Event Bus**
- Unit tests: 28 tests
- Integration tests: 15 tests
- Performance tests: 3 tests
- Security tests: 4 tests
- **Total: 50 tests**

**Story 39.7: Brian Chat Component**
- Unit tests: 20 tests
- Integration tests: 13 tests
- E2E tests: 3 tests
- Accessibility tests: 4 tests
- **Total: 40 tests**

**Story 39.14: Monaco Edit Mode with Commit Enforcement**
- Unit tests: 13 tests
- Integration tests: 17 tests
- E2E tests: 4 tests
- Security tests: 5 tests
- **Total: 39 tests**

### Medium-Risk Stories (Standard Testing)

**Story 39.11: File Tree Navigation Component**
- Unit tests: 12 tests
- Integration tests: 5 tests
- E2E tests: 1 test
- Performance tests: 2 tests
- **Total: 20 tests**

### Low-Risk Stories (Basic Testing)

**Story 39.6: Dark/Light Theme Support**
- Unit tests: 6 tests
- E2E tests: 1 test
- Accessibility tests: 1 test
- **Total: 8 tests**

**See TEST_STRATEGY.md for all 39 stories**

---

## Test Execution

### Local Development

**Run all unit tests**:
```bash
# Frontend
npm test

# Backend
pytest tests/web/unit
```

**Run integration tests**:
```bash
pytest tests/web/integration
```

**Run E2E tests**:
```bash
npx playwright test
```

**Run performance tests**:
```bash
npm run test:performance
```

**Run accessibility tests**:
```bash
npx playwright test --grep "@accessibility"
```

**Run security tests**:
```bash
pytest tests/web/security
```

### CI/CD

**Trigger full pipeline**:
- Push to main branch
- Create pull request
- Manual workflow dispatch

**View results**:
- GitHub Actions summary
- Codecov dashboard (coverage)
- Playwright HTML report
- Lighthouse reports

---

## Tools and Frameworks

### Frontend Testing

| Tool | Version | Purpose |
|------|---------|---------|
| Vitest | 1.1+ | Unit testing |
| React Testing Library | 14+ | Component testing |
| Playwright | 1.40+ | E2E testing |
| axe-core | 4.8+ | Accessibility testing |
| Lighthouse | 11+ | Performance auditing |
| ESLint | 8.56+ | Linting |
| Prettier | 3.1+ | Formatting |
| TypeScript | 5.3+ | Type checking |

### Backend Testing

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 7.4+ | Unit/integration testing |
| pytest-asyncio | 0.21+ | Async test support |
| pytest-cov | 4.1+ | Coverage reporting |
| Ruff | 0.1+ | Linting |
| Black | 23.10+ | Formatting |
| MyPy | 1.6+ | Type checking (strict) |
| Bandit | 1.7+ | Security linting |
| Safety | 2.3+ | Dependency scanning |
| k6 | 0.47+ | Load testing |

---

## Metrics and Reporting

### Test Execution Metrics

**Track per PR**:
- Total tests run
- Tests passed/failed/skipped
- Test duration
- Coverage percentage
- Flaky test rate

**Example Report**:
```
Test Execution Summary
─────────────────────────────────────────
Frontend Tests:
  Unit: 287 passed, 0 failed (85.4% coverage)
  Integration: 45 passed, 0 failed
  E2E: 6 passed, 0 failed
  Total: 338 tests, 12m 34s

Backend Tests:
  Unit: 156 passed, 0 failed (87.2% coverage)
  Integration: 32 passed, 0 failed
  Security: 18 passed, 0 failed
  Total: 206 tests, 8m 12s

Performance Metrics (P95):
  Page Load: 1.8s ✓ (<2s target)
  Event Latency: 8ms ✓ (<100ms target)

Overall: PASS ✓
```

### Coverage Trends

**Visualization**: Codecov dashboard
**Track**:
- Overall coverage percentage
- Coverage by component
- Uncovered lines

### Flaky Test Tracking

**Action**:
- Mark as flaky: `@pytest.mark.flaky`
- Investigate within 24 hours
- Fix or delete within 1 week

---

## Next Steps

### For Developers

1. **Review TEST_STRATEGY.md** - Understand testing approach
2. **Set up linting** - Configure ESLint, Ruff, Black, MyPy
3. **Configure pre-commit hooks** - Install `.pre-commit-config.yaml`
4. **Begin Story 39.1** - Backend Foundation (first story)
5. **Write tests first** - ATDD approach (tests define "done")

### For Claude Code

1. **Review E2E_TEST_PLAN.md** - Understand test scenarios
2. **Install Playwright** - `npx playwright install chromium`
3. **Familiarize with data-testid conventions** - Stable selectors for testing
4. **Ready to test** - Once MVP deployed, run E2E tests
5. **Report UX issues** - Find ≥5 real issues during beta

### For Product Owner

1. **Review Quality Gates** - Approve DoD and release criteria
2. **Confirm Coverage Targets** - 85% unit, 80% integration, 100% accessibility
3. **Approve CI/CD Pipeline** - GitHub Actions workflow
4. **Sign off on strategy** - Approve TEST_STRATEGY.md

---

## Document Status

**Status**: Complete - Ready for Review

**Authors**:
- Murat (Test Architect) - Primary author

**Reviewers**:
- Winston (Technical Architect) - Architecture alignment
- Bob (Scrum Master) - Story-level test plans
- Amelia (Developer) - Implementation feasibility
- Sally (UX Designer) - Accessibility requirements

**Version**: 1.0
**Last Updated**: 2025-01-16

---

## Questions or Feedback?

**Contact**: Murat (Test Architect)

**Issues**: Create GitHub issue with label `testing` or `qa`

**Suggestions**: PRs welcome to improve test strategy

---

**END OF QA DOCUMENTATION**
