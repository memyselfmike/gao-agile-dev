# Epic 39: Testing Checklist

**Feature**: Browser-Based Web Interface for GAO-Dev
**Epic Number**: 39
**Test Architect**: Murat
**Version**: 1.0
**Last Updated**: 2025-01-16

---

## Purpose

This checklist ensures comprehensive testing throughout the development lifecycle for Epic 39. Use this checklist for every story to maintain consistent quality standards.

---

## Pre-Development Checklist

Before starting any story:

- [ ] Testing infrastructure setup complete (Sprint 0 stories 39.0.1-39.0.4 done)
- [ ] Story's test plan reviewed in TEST_STRATEGY.md
- [ ] Test coverage targets understood (>85% unit, >80% integration)
- [ ] Semantic HTML requirements reviewed (data-testid naming conventions from E2E_TEST_PLAN.md)
- [ ] Accessibility requirements understood (WCAG 2.1 AA)
- [ ] Security requirements reviewed (if story touches auth, file ops, or user input)

---

## Per-Story Testing Checklist

Use this checklist for each story during development.

### 1. Before Writing Code (ATDD Approach)

- [ ] Read story's detailed test plan in TEST_STRATEGY.md
- [ ] Identify test count and coverage target from test plan
- [ ] Create test file(s) with skeleton tests
- [ ] Write failing acceptance tests first (Acceptance Test-Driven Development)
- [ ] Review semantic HTML requirements (if UI story)
- [ ] Review data-testid naming conventions (if UI story)

### 2. Linting (Level 1)

**Frontend**:
- [ ] ESLint configured and passing (0 errors, <10 warnings)
- [ ] Prettier formatting applied (line length 100, single quotes)
- [ ] TypeScript strict mode enabled (no `any` types)
- [ ] All imports properly ordered and no unused imports

**Backend**:
- [ ] Ruff linting passing (0 errors)
- [ ] Black formatting applied (line length 100)
- [ ] MyPy type checking passing (strict mode, no `# type: ignore`)
- [ ] Bandit security linting passing (if story has security implications)

**Pre-Commit Hooks**:
- [ ] Pre-commit hooks installed and configured
- [ ] All hooks passing before commit

### 3. Unit Tests (Level 2)

**General**:
- [ ] All unit tests written (match test count in TEST_STRATEGY.md)
- [ ] All unit tests passing
- [ ] Coverage >85% (lines, branches, functions, statements)
- [ ] No skipped or commented-out tests
- [ ] No flaky tests (run tests 10 times, all pass)

**Frontend (Vitest + React Testing Library)**:
- [ ] Component rendering tests written
- [ ] User interaction tests written (click, type, submit)
- [ ] State management tests written (Zustand store)
- [ ] Hook tests written (custom React hooks)
- [ ] Mock WebSocket and API calls appropriately
- [ ] Snapshot tests avoided (prefer explicit assertions)

**Backend (pytest + pytest-asyncio)**:
- [ ] API endpoint tests written
- [ ] WebSocket handler tests written
- [ ] Event bus tests written
- [ ] Service layer tests written
- [ ] Mock external dependencies (ChatREPL, GitIntegratedStateManager)
- [ ] Async tests properly configured (pytest-asyncio)

**Coverage Reports**:
- [ ] Frontend coverage report generated (npm run test:coverage)
- [ ] Backend coverage report generated (pytest --cov=gao_dev/web)
- [ ] Uncovered lines reviewed and justified

### 4. Integration Tests (Level 3)

**Scope**:
- [ ] All integration tests written (if applicable to story)
- [ ] All integration tests passing
- [ ] Coverage >80% of critical integration paths

**Frontend Integration**:
- [ ] Component integration tests written (multiple components working together)
- [ ] WebSocket message flow tested
- [ ] API integration tested (mocked backend responses)
- [ ] State synchronization tested (Zustand + WebSocket)

**Backend Integration**:
- [ ] ChatREPL integration tested (if story uses Brian/agents)
- [ ] GitIntegratedStateManager integration tested (if story modifies state)
- [ ] WebSocket event flow tested (publish → broadcast → receive)
- [ ] Session lock integration tested (if story has write operations)

**Integration Test Files**:
- [ ] Frontend: `src/**/*.integration.test.tsx`
- [ ] Backend: `tests/web/integration/**/*.py`

### 5. E2E Tests (Level 5)

**Playwright E2E Tests** (if story has user-facing functionality):
- [ ] E2E scenario(s) identified from E2E_TEST_PLAN.md
- [ ] Semantic HTML implemented (button, nav, main, NOT div with onClick)
- [ ] data-testid attributes added to all interactive elements
- [ ] data-state attributes added for state indicators (loading, error, success)
- [ ] ARIA labels added to icon-only buttons and form inputs
- [ ] E2E test(s) written in TypeScript (tests/e2e/**/*.spec.ts)
- [ ] E2E test(s) passing locally
- [ ] Screenshots match baseline (visual regression)
- [ ] Test helper functions used (tests/e2e/utils/helpers.ts)

**E2E Best Practices**:
- [ ] Wait for elements explicitly (avoid hardcoded timeouts)
- [ ] Use data-testid selectors (stable, human-readable)
- [ ] Check for data-state before assertions (wait for loading to complete)
- [ ] Take screenshots at stable states only (no animations mid-flight)
- [ ] Use deterministic test data (no random UUIDs or timestamps)

### 6. Performance Tests (Level 6)

**If story has performance targets** (see TEST_STRATEGY.md):
- [ ] Performance benchmarks identified (P95 metrics)
- [ ] Performance tests written (Lighthouse, k6, or Performance API)
- [ ] All performance targets met:
  - [ ] Page load <2 seconds (Lighthouse TTI)
  - [ ] Event latency <100ms
  - [ ] Activity stream render <200ms (1,000 events)
  - [ ] File tree render <300ms (500+ files)
  - [ ] Monaco load <500ms (10,000-line files)
- [ ] Memory profiling shows no leaks (Chrome DevTools)
- [ ] CPU usage <5% during idle

**Performance Test Files**:
- [ ] Frontend: tests/performance/**/*.ts
- [ ] Backend: tests/load/**/*.js (k6 load tests)

### 7. Accessibility Tests (Level 7)

**WCAG 2.1 AA Compliance** (if story has UI components):
- [ ] axe-core tests written (tests/e2e/accessibility/**/*.spec.ts)
- [ ] axe-core: 0 violations
- [ ] Keyboard navigation verified:
  - [ ] All interactive elements reachable via Tab
  - [ ] Enter/Space activates buttons
  - [ ] Esc closes modals/dialogs
  - [ ] Arrow keys navigate lists (if applicable)
- [ ] Screen reader tested (VoiceOver on macOS or NVDA on Windows):
  - [ ] All text content read correctly
  - [ ] Form labels announced
  - [ ] Button purposes clear
  - [ ] Error messages announced
- [ ] Color contrast verified:
  - [ ] Normal text: 4.5:1 minimum
  - [ ] Large text (18pt+ or 14pt+ bold): 3:1 minimum
  - [ ] Both light and dark themes compliant
- [ ] Focus indicators visible (outline or custom style)
- [ ] ARIA attributes correct (aria-label, aria-labelledby, aria-describedby)
- [ ] Landmark regions defined (nav, main, aside, footer)
- [ ] Lighthouse accessibility score >95/100

### 8. Security Tests (Level 8)

**If story has security implications** (auth, file ops, user input):
- [ ] Security tests written (tests/web/security/**/*.py)
- [ ] All security tests passing
- [ ] npm audit: 0 high/medium vulnerabilities
- [ ] Bandit: 0 high/medium issues
- [ ] Safety (Python dependencies): 0 known vulnerabilities

**Security Attack Vectors** (test if applicable):
- [ ] WebSocket session hijacking prevented (token validation)
- [ ] CORS bypass prevented (localhost only)
- [ ] Path traversal prevented (validate file paths)
- [ ] Command injection prevented (sanitize commit messages)
- [ ] XSS prevented (sanitize user input, CSP headers)
- [ ] CSRF prevented (CSRF tokens or SameSite cookies)
- [ ] Session lock bypass prevented (middleware enforces read-only)

**Security Test Files**:
- [ ] tests/web/security/**/*.py

### 9. Regression Tests (Level 4)

**CLI Regression**:
- [ ] 100% existing CLI tests pass (zero regressions)
- [ ] Run: `pytest tests/ --ignore=tests/web`
- [ ] All tests green

**Performance Regression**:
- [ ] Performance benchmarks maintained (no degradation)
- [ ] Compare against baseline metrics

**Cross-Browser Testing** (if UI story):
- [ ] Chrome: All features work
- [ ] Firefox: All features work
- [ ] Safari: All features work
- [ ] Edge: All features work

**Responsive Design** (if UI story):
- [ ] 1024px (tablet): Layout correct
- [ ] 1440px (laptop): Layout correct
- [ ] 1920px (desktop): Layout correct

---

## Pre-PR Checklist

Before creating pull request:

### Code Quality
- [ ] No `any` types in TypeScript (strict mode enforced)
- [ ] No `# type: ignore` in Python (MyPy strict)
- [ ] DRY principles followed (no code duplication)
- [ ] SOLID principles followed (clean architecture)
- [ ] Documentation updated:
  - [ ] Inline comments for complex logic
  - [ ] README.md updated (if new feature)
  - [ ] API documentation updated (if new endpoints)

### Linting (All Green)
- [ ] ESLint: 0 errors, <10 warnings
- [ ] Ruff: 0 errors
- [ ] Prettier: All files formatted
- [ ] Black: All files formatted
- [ ] TypeScript: 0 type errors
- [ ] MyPy: 0 type errors

### Testing (All Green)
- [ ] All unit tests pass (npm test && pytest tests/web/unit)
- [ ] Coverage >85% (frontend + backend)
- [ ] All integration tests pass (pytest tests/web/integration)
- [ ] All E2E tests pass (npx playwright test)
- [ ] All performance tests pass (if applicable)
- [ ] All accessibility tests pass (axe-core 0 violations)
- [ ] All security tests pass (npm audit, Bandit)
- [ ] All regression tests pass (100% CLI tests pass)

### CI/CD Pipeline
- [ ] Pre-commit hooks pass (all linters + formatters)
- [ ] Push to feature branch triggers CI/CD
- [ ] CI/CD pipeline green (all 7 stages pass):
  - [ ] Stage 1: Linting (frontend + backend)
  - [ ] Stage 2: Unit tests (frontend + backend)
  - [ ] Stage 3: Integration tests
  - [ ] Stage 4: E2E tests (Playwright)
  - [ ] Stage 5: Performance tests (Lighthouse CI)
  - [ ] Stage 6: Accessibility tests (axe-core)
  - [ ] Stage 7: Security tests (npm audit, Bandit)
- [ ] Coverage reports uploaded to Codecov
- [ ] Playwright reports uploaded as artifacts (if E2E tests ran)
- [ ] No failing tests in CI

### Code Review Preparation
- [ ] Self-review completed (read your own diff)
- [ ] No debug statements or console.log calls
- [ ] No commented-out code
- [ ] Commit message follows format: `type(scope): description`
- [ ] PR description includes:
  - [ ] Story number and title
  - [ ] Summary of changes
  - [ ] Test coverage highlights
  - [ ] Screenshots (if UI change)
  - [ ] Breaking changes (if any)

---

## Pre-Release Checklist

Before MVP/V1.1/V1.2 release:

### Functional Completeness
- [ ] All stories in phase complete
- [ ] All acceptance criteria met
- [ ] No P0 or P1 bugs
- [ ] All known issues documented in GitHub Issues

### Performance (All P95 Metrics <Targets)
- [ ] Page load <2 seconds (Lighthouse TTI)
- [ ] Event latency <100ms
- [ ] Activity stream render <200ms (1,000 events)
- [ ] File tree render <300ms (500+ files)
- [ ] Monaco load <500ms (10,000-line files)
- [ ] WebSocket connection <100ms
- [ ] Event delivery <10ms
- [ ] Memory usage <500MB after 8 hours
- [ ] CPU usage <5% during idle

### Security (Zero High/Medium Vulnerabilities)
- [ ] npm audit: 0 high/medium vulnerabilities
- [ ] Bandit: 0 high/medium issues
- [ ] Safety: 0 known vulnerabilities
- [ ] OWASP ZAP scan: 0 high/medium (optional for MVP)
- [ ] Session token validation verified
- [ ] CORS restricted to localhost
- [ ] Path validation prevents directory traversal
- [ ] Input sanitization prevents injection

### Accessibility (100% WCAG 2.1 AA Compliance)
- [ ] axe-core: 0 violations across all pages
- [ ] Keyboard navigation: 100% features accessible
- [ ] Screen reader: All features usable (VoiceOver or NVDA)
- [ ] Color contrast: 4.5:1 (normal), 3:1 (large)
- [ ] Focus indicators visible on all interactive elements
- [ ] Lighthouse accessibility score >95/100

### Regression (Zero Regressions)
- [ ] 100% existing CLI tests pass
- [ ] Performance benchmarks maintained (no degradation)
- [ ] Cross-browser: Chrome, Firefox, Safari, Edge
- [ ] Responsive: 1024px, 1440px, 1920px

### E2E Testing (All Scenarios Pass)
- [ ] **MVP**: 6 scenarios passing (Scenarios 1-6)
  - [ ] Scenario 1: Server startup and accessibility
  - [ ] Scenario 2: Chat flow
  - [ ] Scenario 3: Activity stream
  - [ ] Scenario 4: File tree and Monaco editor
  - [ ] Scenario 5: Read-only mode
  - [ ] Scenario 6: Theme toggle
- [ ] **V1.1**: 10 scenarios passing (Scenarios 1-10)
  - [ ] Scenarios 1-6 (MVP)
  - [ ] Scenario 7: Kanban drag-drop
  - [ ] Scenario 8: Workflow controls
  - [ ] Scenario 9: Git history and diff
  - [ ] Scenario 10: Provider configuration
- [ ] **V1.2**: 14 scenarios passing (all scenarios)
  - [ ] Scenarios 1-10 (V1.1)
  - [ ] Scenario 11: Ceremony channel
  - [ ] Scenario 12: Layout resize
  - [ ] Scenario 13: Metrics dashboard
  - [ ] Scenario 14: Export metrics

### Beta Testing (Claude Code as AI Tester)
- [ ] Claude Code setup with Playwright MCP
- [ ] Claude Code ran all E2E scenarios
- [ ] User satisfaction: >80% (survey or feedback)
- [ ] AI-discovered UX issues: ≥5 real issues found
- [ ] All critical issues resolved before release

### Documentation
- [ ] User guide complete (docs/USER_GUIDE.md)
- [ ] API documentation complete (OpenAPI/Swagger)
- [ ] Troubleshooting guide complete (docs/TROUBLESHOOTING.md)
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md updated with setup instructions

---

## Post-Release Checklist

After release:

### Monitoring
- [ ] Error tracking configured (Sentry or similar)
- [ ] Performance monitoring active (Lighthouse CI continuous)
- [ ] User analytics configured (optional, privacy-compliant)
- [ ] WebSocket connection metrics tracked
- [ ] API latency metrics tracked

### Documentation
- [ ] User guide published and accessible
- [ ] API documentation published (OpenAPI docs)
- [ ] Troubleshooting guide published
- [ ] CHANGELOG.md updated with final release notes
- [ ] Release announcement prepared (if applicable)

### Retrospective
- [ ] Retrospective meeting scheduled within 1 week
- [ ] Action items documented in retrospective notes
- [ ] Learnings documented:
  - [ ] What went well
  - [ ] What could be improved
  - [ ] Action items for next phase
- [ ] Action items assigned owners and due dates
- [ ] Retrospective notes added to docs/features/web-interface/retrospectives/

### Maintenance Plan
- [ ] Bug tracking process defined
- [ ] Patch release cadence defined
- [ ] Deprecation policy defined (for future API changes)
- [ ] Security update process defined

---

## Quality Gate Summary

**Pull Request Quality Gate** (all PRs must pass):
1. Linting: 0 errors, <10 warnings
2. Unit Tests: All pass, >85% coverage
3. Integration Tests: All pass
4. Type Checking: 0 errors (strict mode)
5. Security Scan: 0 high/medium issues

**Release Quality Gate** (MVP/V1.1/V1.2):
1. Functional Completeness: All stories complete
2. Performance: All P95 metrics <targets
3. Accessibility: WCAG 2.1 AA (100%)
4. Security: 0 high/medium vulnerabilities
5. E2E Tests: All scenarios passing
6. Zero Regressions: 100% CLI tests pass
7. Beta Testing: >80% satisfaction, ≥5 UX issues found

---

## Quick Reference

### Test Commands

**Frontend**:
```bash
# Unit tests
npm test

# Unit tests with coverage
npm run test:coverage

# E2E tests
npx playwright test

# E2E tests in headed mode
npx playwright test --headed

# E2E tests for specific scenario
npx playwright test --grep "MVP-1"

# Linting
npm run lint

# Formatting
npm run format
```

**Backend**:
```bash
# Unit tests
pytest tests/web/unit

# Unit tests with coverage
pytest tests/web/unit --cov=gao_dev/web

# Integration tests
pytest tests/web/integration

# Security tests
pytest tests/web/security

# All tests with coverage
pytest tests/web --cov=gao_dev/web --cov-report=html

# Linting
ruff check gao_dev/web
black --check gao_dev/web
mypy gao_dev/web

# Security linting
bandit -r gao_dev/web -ll
```

**CI/CD**:
```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks
pre-commit install
```

---

## Support

**Questions or Issues?**
- Test Architect: Murat
- Scrum Master: Bob
- Create GitHub issue with label `testing` or `qa`

**Testing Resources**:
- TEST_STRATEGY.md - Comprehensive testing strategy (8 levels)
- E2E_TEST_PLAN.md - Playwright E2E scenarios and setup
- QA/README.md - QA documentation overview

---

**Document Status**: Complete - Ready for Use
**Version**: 1.0
**Last Updated**: 2025-01-16
**Author**: Bob (Scrum Master)
**Reviewer**: Murat (Test Architect)
