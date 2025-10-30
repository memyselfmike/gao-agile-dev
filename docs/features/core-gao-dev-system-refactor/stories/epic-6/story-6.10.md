# Story 6.10: Update Documentation & Architecture

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 2
**Priority**: P1 (High)
**Type**: Documentation
**Status**: Blocked (Requires 6.1-6.9)

---

## Overview

Update all documentation to reflect the completed refactoring, including architecture diagrams, getting started guides, and migration notes.

---

## User Story

**As a** GAO-Dev developer
**I want** documentation that matches the actual codebase
**So that** I can understand and contribute to the project

---

## Acceptance Criteria

1. **Architecture Documentation**
   - [ ] Update `ARCHITECTURE.md` with actual structure
   - [ ] Add component diagrams showing services
   - [ ] Document dependency injection patterns
   - [ ] Update from "target architecture" to "current architecture"

2. **API Documentation**
   - [ ] Document new service APIs
   - [ ] Update orchestrator API docs
   - [ ] Update sandbox manager API docs
   - [ ] Add usage examples

3. **Getting Started Guide**
   - [ ] Update code examples with new patterns
   - [ ] Update import statements
   - [ ] Add service usage examples
   - [ ] Remove references to legacy code

4. **Migration Notes**
   - [ ] Create MIGRATION.md if needed
   - [ ] Document breaking changes (if any)
   - [ ] Provide migration examples
   - [ ] Note legacy_models removal

5. **README Updates**
   - [ ] Update project structure diagram
   - [ ] Update feature list
   - [ ] Update architecture overview
   - [ ] Update success metrics (show completed)

6. **CLAUDE.md Updates**
   - [ ] Update project structure section
   - [ ] Update service layer documentation
   - [ ] Remove references to God Classes
   - [ ] Update "When in Doubt" section

---

## Documentation Updates Required

### 1. ARCHITECTURE.md

**Sections to Update**:

- **Current Architecture** (was "Target Architecture")
  - Update to reflect actual implementation
  - Add "IMPLEMENTED" markers
  - Remove "PLANNED" markers

- **Component Design**
  - Add service layer documentation
  - Document `WorkflowCoordinator`
  - Document `StoryLifecycleManager`
  - Document `ProcessExecutor`
  - Document `QualityGateManager`
  - Document sandbox services

- **Data Flow**
  - Update diagrams to show service delegation
  - Show event bus integration
  - Show dependency injection

### 2. Epic Documentation

Update `docs/features/core-gao-dev-system-refactor/`:

- **epics.md**
  - Mark Epic 6 as COMPLETE
  - Update success metrics
  - Update timeline

- **README.md**
  - Update status to "COMPLETE"
  - Update implementation checklist
  - Update change log

- **PRD.md**
  - Mark success criteria as met
  - Update current state metrics
  - Add completion date

### 3. Component Diagrams

Create/update diagrams showing:

```
┌─────────────────────────────────────────────┐
│         GAODevOrchestrator (Facade)         │
│                 < 200 lines                 │
└─────────────────┬───────────────────────────┘
                  │ delegates to
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐      ┌────▼─────┐
    │ Workflow│      │  Story   │
    │Coordina-│      │Lifecycle │
    │  tor    │      │ Manager  │
    └─────────┘      └──────────┘

    ┌─────────┐      ┌──────────┐
    │ Process │      │ Quality  │
    │Executor │      │   Gate   │
    └─────────┘      └──────────┘
```

### 4. Usage Examples

Add examples to docs:

```python
# Example: Using new architecture
from gao_dev.orchestrator import GAODevOrchestrator

# Use factory for default config
orchestrator = GAODevOrchestrator.create_default(
    project_root=Path("."),
    api_key="your-key"
)

# Or customize with DI
from gao_dev.core.services import (
    WorkflowCoordinator,
    StoryLifecycleManager
)

orchestrator = GAODevOrchestrator(
    workflow_coordinator=WorkflowCoordinator(...),
    story_lifecycle=StoryLifecycleManager(...),
    # ... other services
)
```

---

## Implementation Steps

1. **Update Architecture Docs**
   - Read through ARCHITECTURE.md
   - Update each section to match implementation
   - Add diagrams
   - Add code examples

2. **Update Epic Docs**
   - Mark Epic 6 complete in epics.md
   - Update README status
   - Update PRD metrics
   - Update timeline

3. **Update Getting Started**
   - Update code examples
   - Add service usage patterns
   - Update import statements

4. **Create Migration Notes** (if needed)
   - Document breaking changes
   - Provide migration examples
   - Note deprecated patterns

5. **Update .claude/CLAUDE.md**
   - Update project structure
   - Update best practices
   - Remove God Class warnings
   - Add service layer documentation

6. **Review & Verify**
   - Check all links work
   - Verify code examples compile
   - Ensure consistency across docs
   - Spell check

---

## Documentation Checklist

### Files to Update

- [ ] `docs/features/core-gao-dev-system-refactor/ARCHITECTURE.md`
- [ ] `docs/features/core-gao-dev-system-refactor/epics.md`
- [ ] `docs/features/core-gao-dev-system-refactor/README.md`
- [ ] `docs/features/core-gao-dev-system-refactor/PRD.md`
- [ ] `.claude/CLAUDE.md`
- [ ] `README.md` (project root)
- [ ] Create `MIGRATION.md` (if needed)

### Diagrams to Create/Update

- [ ] Component architecture diagram
- [ ] Service dependency diagram
- [ ] Data flow diagram
- [ ] Sequence diagram for workflow execution

### Code Examples to Add

- [ ] Creating orchestrator with factory
- [ ] Creating orchestrator with custom services
- [ ] Using individual services
- [ ] Event bus subscription
- [ ] Plugin integration

---

## Definition of Done

- [ ] All documentation files updated
- [ ] All diagrams created/updated
- [ ] All code examples working
- [ ] No broken links
- [ ] Consistent terminology throughout
- [ ] Spell checked
- [ ] Reviewed by at least one other developer
- [ ] Epic 6 marked as COMPLETE in all docs

---

## Success Criteria

Documentation is complete when:
- A new developer can understand the architecture from docs
- All code examples compile and run
- No references to "God Classes" remain
- Architecture section says "IMPLEMENTED" not "PLANNED"
- Success metrics show goals achieved

---

**Related Stories**: All Epic 6 stories
**Estimated Time**: Half day
**Deliverable**: Complete, accurate, up-to-date documentation
