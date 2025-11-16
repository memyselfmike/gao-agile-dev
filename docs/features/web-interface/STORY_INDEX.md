# Epic 39: Web Interface - Story Index with Test Tracking

**Last Updated**: 2025-01-16
**Total Stories**: 18 (including 4 testing infrastructure stories)
**Total Story Points**: 53 (Sprint 0 + MVP)
**Status**: Ready for Implementation

---

## Quick Navigation

### Sprint 0: Testing Infrastructure (8 points) - NEW

| Story | Title | Points | Tests | Status | File |
|-------|-------|--------|-------|--------|------|
| 39.0.1 | Frontend Testing Infrastructure Setup | 2 | 10 ACs | TODO | [story-39.0.1.md](epics/39.0-testing-infrastructure/stories/story-39.0.1.md) |
| 39.0.2 | Backend Testing Infrastructure Setup | 2 | 10 ACs | TODO | [story-39.0.2.md](epics/39.0-testing-infrastructure/stories/story-39.0.2.md) |
| 39.0.3 | Linting and Code Quality Setup | 1 | 10 ACs | TODO | [story-39.0.3.md](epics/39.0-testing-infrastructure/stories/story-39.0.3.md) |
| 39.0.4 | CI/CD Pipeline Setup | 3 | 12 ACs | TODO | [story-39.0.4.md](epics/39.0-testing-infrastructure/stories/story-39.0.4.md) |

**Sprint 0 Total**: 8 points, 42 acceptance criteria

---

### Epic 39.1: Backend Foundation (9 points, adjusted)

| Story | Title | Points | Tests Written | Tests Passing | Coverage | Status | File |
|-------|-------|--------|---------------|---------------|----------|--------|------|
| 39.1 | FastAPI Web Server Setup | 2 | 0/8 | 0/8 | 0% | TODO | [story-39.1.md](epics/39.1-backend-foundation/stories/story-39.1.md) |
| 39.2 | WebSocket Manager and Event Bus | **4** | 0/50 | 0/50 | 0% | TODO | [story-39.2.md](epics/39.1-backend-foundation/stories/story-39.2.md) |
| 39.3 | Session Lock and Read-Only Mode | 3 | 0/15 | 0/15 | 0% | TODO | [story-39.3.md](epics/39.1-backend-foundation/stories/story-39.3.md) |

**Epic Total**: 9 points, 73 tests (adjusted from 8 points, Story 39.2: 3→4)

---

### Epic 39.2: Frontend Foundation (7 points)

| Story | Title | Points | Tests Written | Tests Passing | Coverage | Status | File |
|-------|-------|--------|---------------|---------------|----------|--------|------|
| 39.4 | React + Vite + Zustand Setup | 2 | 0/10 | 0/10 | 0% | TODO | [story-39.4.md](epics/39.2-frontend-foundation/stories/story-39.4.md) |
| 39.5 | Basic Layout with shadcn/ui | 3 | 0/12 | 0/12 | 0% | TODO | [story-39.5.md](epics/39.2-frontend-foundation/stories/story-39.5.md) |
| 39.6 | Dark/Light Theme Support | 2 | 0/8 | 0/8 | 0% | TODO | [story-39.6.md](epics/39.2-frontend-foundation/stories/story-39.6.md) |

**Epic Total**: 7 points, 30 tests

---

### Epic 39.3: Core Observability (16 points)

| Story | Title | Points | Tests Written | Tests Passing | Coverage | Status | File |
|-------|-------|--------|---------------|---------------|----------|--------|------|
| 39.7 | Brian Chat Component (ChatREPL Integration) | 5 | 0/40 | 0/40 | 0% | TODO | [story-39.7.md](epics/39.3-core-observability/stories/story-39.7.md) |
| 39.8 | Multi-Agent Chat Switching | 2 | 0/12 | 0/12 | 0% | TODO | [story-39.8.md](epics/39.3-core-observability/stories/story-39.8.md) |
| 39.9 | Real-Time Activity Stream | 5 | 0/25 | 0/25 | 0% | TODO | [story-39.9.md](epics/39.3-core-observability/stories/story-39.9.md) |
| 39.10 | Activity Stream Filters and Search | 4 | 0/15 | 0/15 | 0% | TODO | [story-39.10.md](epics/39.3-core-observability/stories/story-39.10.md) |

**Epic Total**: 16 points, 92 tests

---

### Epic 39.4: File Management (15 points, adjusted)

| Story | Title | Points | Tests Written | Tests Passing | Coverage | Status | File |
|-------|-------|--------|---------------|---------------|----------|--------|------|
| 39.11 | File Tree Navigation Component | 3 | 0/20 | 0/20 | 0% | TODO | [story-39.11.md](epics/39.4-file-management/stories/story-39.11.md) |
| 39.12 | Monaco Editor Integration (Read-Only) | 4 | 0/18 | 0/18 | 0% | TODO | [story-39.12.md](epics/39.4-file-management/stories/story-39.12.md) |
| 39.13 | Real-Time File Updates from Agents | 3 | 0/12 | 0/12 | 0% | TODO | [story-39.13.md](epics/39.4-file-management/stories/story-39.13.md) |
| 39.14 | Monaco Edit Mode with Commit Enforcement | **5** | 0/39 | 0/39 | 0% | TODO | [story-39.14.md](epics/39.4-file-management/stories/story-39.14.md) |

**Epic Total**: 15 points, 89 tests (adjusted from 14 points, Story 39.14: 4→5)

---

## Test Count Summary

### By Epic

| Epic | Stories | Points | Tests | Status |
|------|---------|--------|-------|--------|
| **Sprint 0: Testing Infrastructure** | 4 | 8 | 42 ACs | TODO |
| **39.1: Backend Foundation** | 3 | 9 | 73 | TODO |
| **39.2: Frontend Foundation** | 3 | 7 | 30 | TODO |
| **39.3: Core Observability** | 4 | 16 | 92 | TODO |
| **39.4: File Management** | 4 | 15 | 89 | TODO |
| **TOTAL (MVP)** | **18** | **53** | **326** | TODO |

### By Test Type

| Test Level | Test Count | Coverage Target |
|-----------|------------|-----------------|
| **Unit Tests** | 200+ | >85% |
| **Integration Tests** | 77 | >80% |
| **E2E Tests** | 6 scenarios (MVP) | All critical paths |
| **Performance Tests** | 8 metrics | P95 <targets |
| **Accessibility Tests** | WCAG 2.1 AA | 100% compliance |
| **Security Tests** | 18 | 0 high/medium vulns |

---

## Implementation Order (Updated with Sprint 0)

### Sprint 0: Testing Infrastructure (Week 0, 1 week)
1. Story 39.0.1 - Frontend Testing Infrastructure Setup
2. Story 39.0.2 - Backend Testing Infrastructure Setup
3. Story 39.0.3 - Linting and Code Quality Setup
4. Story 39.0.4 - CI/CD Pipeline Setup

**Deliverable**: Testing infrastructure operational, example tests passing

---

### Sprint 1: Backend Core (Week 1-2, 2 weeks)
5. Story 39.1 - FastAPI Web Server Setup (8 tests)
6. Story 39.2 - WebSocket Manager and Event Bus (50 tests, high-risk)
7. Story 39.3 - Session Lock and Read-Only Mode (15 tests)

**Deliverable**: Backend infrastructure complete, WebSocket operational

---

### Sprint 2: Frontend Scaffolding (Week 3-4, 2 weeks)
8. Story 39.4 - React + Vite + Zustand Setup (10 tests)
9. Story 39.5 - Basic Layout with shadcn/ui (12 tests)
10. Story 39.6 - Dark/Light Theme Support (8 tests)

**Deliverable**: Professional UI layout ready, E2E Scenario 1 passing

---

### Sprint 3: Chat Component (Week 5-6, 2 weeks)
11. Story 39.7 - Brian Chat Component (40 tests, high-risk)
12. Story 39.8 - Multi-Agent Chat Switching (12 tests)

**Deliverable**: Users can chat with all 8 agents, E2E Scenario 2 passing

---

### Sprint 4: Activity Stream (Week 7, 2 weeks)
13. Story 39.9 - Real-Time Activity Stream (25 tests)
14. Story 39.10 - Activity Stream Filters and Search (15 tests)

**Deliverable**: Real-time observability complete, E2E Scenario 3 passing

---

### Sprint 5: File Tree & Read-Only Editor (Week 8-9, 2 weeks)
15. Story 39.11 - File Tree Navigation Component (20 tests, medium-risk)
16. Story 39.12 - Monaco Editor Integration (Read-Only) (18 tests)
17. Story 39.13 - Real-Time File Updates from Agents (12 tests)

**Deliverable**: File browsing and viewing, E2E Scenario 4 passing

---

### Sprint 6: Edit Mode with Commit Enforcement (Week 10, 1 week)
18. Story 39.14 - Monaco Edit Mode with Commit Enforcement (39 tests, high-risk, security critical)

**Deliverable**: **MVP Complete** - Full web interface with all core features tested

---

## Story Dependencies

```
Sprint 0 (Testing Infrastructure)
  └─> 39.1 (FastAPI)
       └─> 39.2 (WebSocket)
            └─> 39.3 (Session Lock)
       └─> 39.4 (React + Vite)
            └─> 39.5 (Layout)
                 ├─> 39.6 (Theme)
                 ├─> 39.7 (Chat) + 39.2
                 │    └─> 39.8 (Multi-Agent)
                 ├─> 39.9 (Activity) + 39.2
                 │    └─> 39.10 (Filters)
                 └─> 39.11 (File Tree)
                      └─> 39.12 (Monaco Read-Only)
                           └─> 39.13 (Real-Time Updates) + 39.2
                                └─> 39.14 (Monaco Edit) + 39.3
```

---

## Story Points by Type (Updated)

| Size | Points Each | Count | Total |
|------|-------------|-------|-------|
| XS (Extra Small) | 1 | 1 | 1 |
| Small (S) | 2 | 5 | 10 |
| Medium (M) | 3-4 | 9 | 29 |
| Large (L) | 5 | 3 | 15 |
| **TOTAL** | - | **18** | **53** |

**Changes from Original**:
- +4 stories (Sprint 0: Testing Infrastructure)
- +8 points (Sprint 0)
- Story 39.2: 3→4 points (+1 for 50 tests, high-risk)
- Story 39.14: 4→5 points (+1 for 39 tests, security critical)

---

## Epic Progress Tracking

### Sprint 0: Testing Infrastructure
- [ ] Story 39.0.1 - Frontend Testing Infrastructure Setup (2 pts, 10 ACs)
- [ ] Story 39.0.2 - Backend Testing Infrastructure Setup (2 pts, 10 ACs)
- [ ] Story 39.0.3 - Linting and Code Quality Setup (1 pt, 10 ACs)
- [ ] Story 39.0.4 - CI/CD Pipeline Setup (3 pts, 12 ACs)

**Progress**: 0/4 stories, 0/8 points

---

### Epic 39.1: Backend Foundation
- [ ] Story 39.1 - FastAPI Web Server Setup (2 pts, 8 tests)
- [ ] Story 39.2 - WebSocket Manager and Event Bus (4 pts, 50 tests)
- [ ] Story 39.3 - Session Lock and Read-Only Mode (3 pts, 15 tests)

**Progress**: 0/3 stories, 0/9 points, 0/73 tests

---

### Epic 39.2: Frontend Foundation
- [ ] Story 39.4 - React + Vite + Zustand Setup (2 pts, 10 tests)
- [ ] Story 39.5 - Basic Layout with shadcn/ui (3 pts, 12 tests)
- [ ] Story 39.6 - Dark/Light Theme Support (2 pts, 8 tests)

**Progress**: 0/3 stories, 0/7 points, 0/30 tests

---

### Epic 39.3: Core Observability
- [ ] Story 39.7 - Brian Chat Component (5 pts, 40 tests)
- [ ] Story 39.8 - Multi-Agent Chat Switching (2 pts, 12 tests)
- [ ] Story 39.9 - Real-Time Activity Stream (5 pts, 25 tests)
- [ ] Story 39.10 - Activity Stream Filters and Search (4 pts, 15 tests)

**Progress**: 0/4 stories, 0/16 points, 0/92 tests

---

### Epic 39.4: File Management
- [ ] Story 39.11 - File Tree Navigation Component (3 pts, 20 tests)
- [ ] Story 39.12 - Monaco Editor Integration (4 pts, 18 tests)
- [ ] Story 39.13 - Real-Time File Updates (3 pts, 12 tests)
- [ ] Story 39.14 - Monaco Edit Mode with Commit Enforcement (5 pts, 39 tests)

**Progress**: 0/4 stories, 0/15 points, 0/89 tests

---

## Overall Progress
**Stories**: 0/18 completed (0%)
**Points**: 0/53 completed (0%)
**Tests**: 0/326 passing (0%)
**Status**: Planning Complete, Ready for Implementation

---

## Testing Milestones

### Week 0 (Sprint 0 End)
- [ ] Testing infrastructure complete
- [ ] CI/CD pipeline operational
- [ ] Pre-commit hooks active
- [ ] Example tests passing

### Week 2 (Sprint 1 End)
- [ ] Backend unit tests: >85% coverage
- [ ] First integration tests passing
- [ ] WebSocket tests complete (50 tests for Story 39.2)

### Week 4 (Sprint 2 End)
- [ ] Frontend unit tests: >85% coverage
- [ ] E2E Scenario 1 passing (Server startup)

### Week 6 (Sprint 3 End)
- [ ] Chat component tests complete (40 tests for Story 39.7)
- [ ] E2E Scenario 2 passing (Chat flow)

### Week 8 (Sprint 4 End)
- [ ] Activity stream tests complete
- [ ] E2E Scenario 3 passing (Activity stream)

### Week 10 (MVP COMPLETE)
- [ ] All 6 E2E scenarios passing (Scenarios 1-6)
- [ ] Performance benchmarks met (all 8 metrics)
- [ ] Accessibility: WCAG 2.1 AA (100%)
- [ ] Security: 0 high/medium vulnerabilities
- [ ] Zero CLI regressions
- [ ] File management tests complete (39 tests for Story 39.14)

---

## Related Documents

- [EPIC_BREAKDOWN.md](EPIC_BREAKDOWN.md) - Detailed epic breakdown with roadmap
- [COMPLETE_ROADMAP.md](COMPLETE_ROADMAP.md) - Complete implementation roadmap (all 3 phases)
- [TESTING_INTEGRATION_REPORT.md](TESTING_INTEGRATION_REPORT.md) - Testing strategy integration report
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Comprehensive testing checklist
- [QA/TEST_STRATEGY.md](QA/TEST_STRATEGY.md) - 8-level testing strategy (21,000+ lines)
- [QA/E2E_TEST_PLAN.md](QA/E2E_TEST_PLAN.md) - Playwright E2E test plan (14 scenarios)
- [PRD.md](PRD.md) - Product requirements (v1.2, approved)
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture (v2.1)
- [VISION.md](VISION.md) - Vision document from Mary's elicitation

---

**Document Maintainer**: Bob (Scrum Master)
**Last Updated**: 2025-01-16
**Version**: 2.0 (Updated with testing integration)
