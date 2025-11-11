---
document:
  type: "prd"
  state: "draft"
  created: "2025-11-11"
  last_modified: "2025-11-11"
  author: "John (Product Manager)"
  feature: "feature-based-document-structure"
  epic: null
  story: null
  related_documents:
    - "ARCHITECTURE.md"
    - "FIXES_SUMMARY.md"
    - "CRITICAL_ANALYSIS.md"
    - "README.md"
  replaces: null
  replaced_by: null
  version: "2.0.0"
---

# Product Requirements Document
## Feature-Based Document Structure Enhancement

**Version:** 2.0.0 (Post-Critical Review)
**Date:** 2025-11-11
**Status:** Draft
**Author:** John (Product Manager)
**Feature:** Feature-Based Document Structure

**Changes from v1.0:**
- Extends Epic 28's DocumentStructureManager (not replacement)
- Co-located epic-story structure (epics contain their stories)
- Per-project features registry (follows Epic 20)
- Reduced scope: 3 epics (25 points, 2 weeks) vs. 5 epics (40 points, 4 weeks)
- Clear variable naming conventions
- WorkflowContext integration for feature persistence

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [Goals & Success Criteria](#goals--success-criteria)
5. [User Stories](#user-stories)
6. [Epic Breakdown](#epic-breakdown)
7. [Technical Requirements](#technical-requirements)
8. [Dependencies](#dependencies)
9. [Timeline](#timeline)
10. [Risks & Mitigations](#risks--mitigations)

---

## Executive Summary

### Vision

**Extend Epic 28's DocumentStructureManager** to provide complete feature-based document organization with co-located epics and stories, making it trivial to find, reference, and integrate documentation for any feature.

### The Problem

**Current State (Epic 28 provides 70% of what we need):**

✅ **What Works:**
- DocumentStructureManager creates `docs/features/{name}/` folders
- Scale-level based structure (Level 2-4)
- Git integration with atomic commits
- PRD and ARCHITECTURE templates
- DocumentLifecycleManager integration

❌ **What's Missing:**
1. **No QA/ folder** - Quality artifacts scattered
2. **No README.md** - No feature index/overview
3. **No features table** - Can't track feature metadata
4. **Separated epics/stories** - Epic definitions in `epics/`, stories in `stories/` (should be co-located)
5. **No validation** - Can't check if structure compliant
6. **No CLI commands** - Must call DocumentStructureManager programmatically
7. **Incomplete variables** - Missing story-level paths

**Impact:**
- 🔻 Developer confusion when navigating documentation
- 🔻 Hard to query "show me everything for Epic 1" (scattered across folders)
- 🔻 No way to validate structure compliance
- 🔻 No metadata tracking for features

### The Solution

**Extend and enhance Epic 28's DocumentStructureManager** with:

1. **Add Missing Pieces:** QA/, README.md to existing folder creation
2. **FeatureRegistry:** Track feature metadata in per-project `.gao-dev/documents.db`
3. **Co-Located Structure:** Epics contain their stories (intuitive navigation)
4. **CLI Commands:** create-feature, validate-structure, list-features
5. **Complete Variables:** All paths defined for workflow resolution
6. **Integration:** WorkflowContext, Brian, Ceremonies

### Goals

1. **Extend (Not Replace):** Build on Epic 28's proven foundation
2. **Co-Located Organization:** Epics and their stories together
3. **Complete Variable Coverage:** All workflow paths defined
4. **Per-Project Isolation:** Features tracked in each project's database
5. **Backward Compatible:** Existing code continues working

### Success Criteria

- ✅ DocumentStructureManager enhanced (not replaced)
- ✅ All new features use co-located epic-story structure
- ✅ FeatureRegistry tracks metadata per-project
- ✅ CLI commands (`create-feature`, `validate-structure`, `list-features`)
- ✅ Complete variable definitions in defaults.yaml
- ✅ WorkflowContext integration for feature persistence
- ✅ Zero breaking changes to Epic 28 functionality
- ✅ 2-week implementation timeline

---

## Problem Statement

### Current State Analysis

Epic 28 (Ceremony Integration & Self-Learning) introduced **DocumentStructureManager** which creates feature folders based on scale level. This was a great start, but has gaps.

#### What Epic 28 Provides ✅

```python
# gao_dev/core/services/document_structure_manager.py (lines 69-172)

class DocumentStructureManager:
    def initialize_feature_folder(
        self, feature_name: str, scale_level: ScaleLevel
    ) -> Optional[Path]:
        """Creates docs/features/{name}/ with:

        Level 2: PRD.md, stories/, CHANGELOG.md
        Level 3: + ARCHITECTURE.md, epics/, retrospectives/
        Level 4: + ceremonies/, MIGRATION_GUIDE.md

        - Registers with DocumentLifecycleManager
        - Commits to git via GitManager
        - Uses conventional commit format
        """
```

**This is 70% of what we need!** It handles:
- ✅ Folder creation (`docs/features/{name}/`)
- ✅ Template generation (PRD, ARCHITECTURE)
- ✅ Git commits (atomic, conventional format)
- ✅ Document registration
- ✅ Scale-based complexity

#### What's Missing ❌

1. **No QA/ folder**
   ```
   Current: docs/features/user-auth/
     ├── PRD.md
     └── stories/

   Needed: + QA/ folder for quality artifacts
   ```

2. **No README.md**
   - No feature index/overview
   - Hard to discover what docs exist

3. **Separated epics/stories** (Bad UX)
   ```
   Current (Epic 28):
   docs/features/user-auth/
     ├── epics/
     │   └── epic-1.md        ← Epic definition here
     └── stories/
         └── epic-1/          ← Stories over here!
             └── story-1.1.md

   Problem: Have to look in TWO places for Epic 1 work!
   ```

4. **No features metadata table**
   - Can't track: feature status, owner, dependencies
   - Can't query: "What features are active?"

5. **No validation**
   - Can't check if structure compliant
   - No CI/CD integration

6. **No CLI commands**
   - Must import DocumentStructureManager and call programmatically
   - Not user-friendly

7. **Incomplete variable paths**
   - Missing: story_location, epic_location, context_xml_folder
   - Current defaults.yaml points to top-level paths

### User Impact

**For Developers:**
- "Where's the Epic 1 definition?" → Look in `epics/epic-1.md`
- "Where are the Epic 1 stories?" → Look in `stories/epic-1/`
- "This is confusing..." → Epic and stories should be together!

**For QA:**
- "Where do I put validation reports?" → No standard location
- "Where are the test reports?" → Scattered across features

**For System Integration:**
- "What features does this project have?" → Can't query
- "Which features are complete?" → No metadata

---

## Solution Overview

### Approach: Extend Epic 28

We **extend** DocumentStructureManager (not replace) and add:

1. **FeatureRegistry** - Metadata tracking
2. **FeaturePathValidator** - Structure validation
3. **FeaturePathResolver** - Variable resolution
4. **CLI Commands** - User-friendly interface
5. **Co-Located Structure** - Epics contain stories

### Final Structure (Co-Located Design)

```
docs/features/{feature-name}/
  ├── PRD.md                          # Feature requirements
  ├── ARCHITECTURE.md                 # Technical architecture
  ├── README.md                       # Feature index (NEW!)
  ├── EPICS.md                        # Master epic overview (NEW!)
  │
  ├── epics/                          # Epic containers
  │   ├── 1-epic-name/                # Epic 1 (number + name)
  │   │   ├── README.md               # Epic definition
  │   │   ├── stories/                # Stories for THIS epic (CO-LOCATED!)
  │   │   │   ├── story-1.1.md
  │   │   │   ├── story-1.2.md
  │   │   │   └── story-1.3.md
  │   │   └── context/                # Context XML for epic stories
  │   │       ├── story-1.1.xml
  │   │       └── story-1.2.xml
  │   │
  │   └── 2-another-epic/             # Epic 2
  │       ├── README.md
  │       └── stories/
  │           └── story-2.1.md
  │
  ├── QA/                             # Quality artifacts (NEW!)
  │   ├── QA_VALIDATION_*.md
  │   ├── TEST_REPORT_*.md
  │   └── FINAL_QA_REPORT_*.md
  │
  └── retrospectives/                 # Ceremony artifacts
      └── epic-1-retro.md
```

**Key Benefits of Co-Located Structure:**
- ✅ **Logical grouping:** Epic and its stories together
- ✅ **Intuitive navigation:** "I'm working on Epic 1" → go to `epics/1-epic-name/`
- ✅ **Better querying:** All Epic 1 docs in one subtree
- ✅ **Consistent pattern:** Same at feature and epic level

### Components Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Epic 28: DocumentStructureManager             │
│  (EXISTING - We enhance this, not replace)                  │
│                                                              │
│  initialize_feature_folder(name, scale_level)               │
│    - Creates docs/features/{name}/                          │
│    - Generates PRD, ARCHITECTURE templates                  │
│    - Commits to git                                         │
│    - Registers with DocumentLifecycleManager                │
│                                                              │
│  ENHANCEMENTS:                                              │
│    + Create QA/ folder                                      │
│    + Create README.md                                       │
│    + Create EPICS.md                                        │
│    + Use co-located epic/story structure                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ uses
┌─────────────────────────────────────────────────────────────┐
│                    NEW: FeatureRegistry                      │
│  (Track metadata in per-project .gao-dev/documents.db)      │
│                                                              │
│  register_feature(name, scope, scale_level)                 │
│  list_features(scope=None, status=None)                     │
│  get_feature(name)                                          │
│  update_feature_status(name, status)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              NEW: FeaturePathValidator                       │
│  (Stateless - validates paths match structure)              │
│                                                              │
│  validate_feature_path(path, feature_name) → bool           │
│  extract_feature_from_path(path) → Optional[str]            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              NEW: FeaturePathResolver                        │
│  (Resolve {{feature_name}} variable)                        │
│                                                              │
│  resolve_feature_name(params, context) → str                │
│  generate_feature_path(feature_name, path_type) → Path      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  NEW: CLI Commands                           │
│  (User-friendly wrappers)                                    │
│                                                              │
│  gao-dev create-feature <name> --scale-level 3              │
│  gao-dev validate-structure [--feature <name>]              │
│  gao-dev list-features                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Goals & Success Criteria

### Primary Goals

1. **Extend Epic 28:** Enhance DocumentStructureManager (not replace)
2. **Co-Located Structure:** Epics contain their stories
3. **Complete Variables:** All workflow paths defined
4. **Per-Project Isolation:** Features tracked per-project
5. **User-Friendly:** CLI commands for common operations

### Success Criteria

**Epic 28 Enhancement:**
- ✅ QA/ folder added to initialize_feature_folder()
- ✅ README.md added to initialize_feature_folder()
- ✅ EPICS.md added for master epic overview
- ✅ Co-located epic-story structure implemented
- ✅ All existing Epic 28 functionality preserved

**Feature Registry:**
- ✅ `features` table in per-project `.gao-dev/documents.db`
- ✅ Track: name, scope (mvp/feature), status, scale_level, dates
- ✅ Query: list_features(), get_feature(), filter by scope/status

**Variable Resolution:**
- ✅ All paths defined in defaults.yaml
- ✅ FeaturePathResolver integrated with WorkflowExecutor
- ✅ WorkflowContext.feature_name property added
- ✅ Feature name persists across multi-step workflows

**CLI Commands:**
- ✅ `create-feature` wraps DocumentStructureManager
- ✅ `validate-structure` checks compliance
- ✅ `list-features` queries registry

**Integration:**
- ✅ Ceremony artifacts respect feature structure
- ✅ Brian lists/selects features conversationally
- ✅ Artifact detection tags with feature_name
- ✅ FastContextLoader caches feature context

### Key Performance Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| Implementation time | 2 weeks | Sprint velocity |
| Code reuse | 70%+ | Lines of existing code used |
| Test coverage | 90%+ | pytest --cov |
| create-feature time | <1s | Performance test |
| validate-structure time | <2s (50 features) | Performance test |

---

## User Stories

### Epic 1: DocumentStructureManager Enhancement

**US-1.1: As a developer, I want QA/ folder auto-created so quality artifacts have a consistent location**
- DocumentStructureManager.initialize_feature_folder() creates QA/
- All scale levels (2+) get QA/ folder
- Git commit includes QA/ folder

**US-1.2: As a developer, I want README.md auto-generated so I have a feature index**
- README.md template with sections: Overview, Documents, Epics, Stories, QA
- Auto-generated from Jinja2 template
- Links to all key documents

**US-1.3: As a developer, I want epics and stories co-located so navigation is intuitive**
- Structure: `epics/1-epic-name/stories/`
- Epic definition in `epics/1-epic-name/README.md`
- All Epic 1 work in one subtree

**US-1.4: As a developer, I want EPICS.md master overview so I can see all epics at a glance**
- EPICS.md lists all epics with status
- Generated at feature creation time
- Updated as epics are added

### Epic 2: Feature Registry & Metadata

**US-2.1: As a developer, I want feature metadata tracked so I can query project state**
- `features` table in per-project `.gao-dev/documents.db`
- Fields: name, scope, status, scale_level, dates, owner, description
- Isolated per project (not global)

**US-2.2: As a developer, I want to query features so I know what's in the project**
- list_features() returns all features
- Filter by scope (mvp, feature)
- Filter by status (planning, active, complete, archived)

**US-2.3: As a system, I want feature status tracked so workflow can adapt**
- Update status: planning → active → complete
- Completed_at timestamp when marked complete
- Queryable for dashboards/reports

### Epic 3: CLI Commands & Variable Integration

**US-3.1: As a developer, I want `create-feature` command so I don't need to code**
- CLI: `gao-dev create-feature user-auth --scale-level 3`
- Wraps DocumentStructureManager.initialize_feature_folder()
- Wraps FeatureRegistry.register_feature()
- Returns success message with next steps

**US-3.2: As a developer, I want `validate-structure` command so I can check compliance**
- CLI: `gao-dev validate-structure --feature user-auth`
- Uses FeaturePathValidator
- Reports violations with suggested fixes
- Exit code 0 (pass) or 1 (fail) for CI/CD

**US-3.3: As a developer, I want `list-features` command so I can see all features**
- CLI: `gao-dev list-features`
- Queries FeatureRegistry
- Outputs table: name, scope, status, scale_level

**US-3.4: As a workflow, I want feature-scoped paths so files are created correctly**
- defaults.yaml updated with all paths
- WorkflowExecutor uses FeaturePathResolver
- Variables resolve from params → context → cwd → auto-detect

---

## Epic Breakdown

### Epic 1: DocumentStructureManager Enhancement (10 points, Week 1)

**Goal:** Add missing pieces to Epic 28's DocumentStructureManager

**Stories:**
1. **Story 1.1:** Add QA/ and README.md to DocumentStructureManager (3 pts)
   - Modify `initialize_feature_folder()` to create QA/
   - Generate README.md from Jinja2 template
   - Update git commit message
   - Tests: QA/ exists, README.md exists, git commit works

2. **Story 1.2:** Add EPICS.md and update templates (2 pts)
   - Generate EPICS.md master epic list
   - Update PRD/ARCHITECTURE templates to mention EPICS.md
   - Tests: EPICS.md created, templates updated

3. **Story 1.3:** Implement co-located epic-story structure (3 pts)
   - Modify folder creation to use `epics/N-name/stories/`
   - Update templates to reflect new structure
   - Tests: Epic folders created correctly, stories nested properly

4. **Story 1.4:** Create FeatureRegistry with database schema (2 pts)
   - Create `features` table in per-project DB
   - Implement register_feature(), list_features(), get_feature()
   - Tests: CRUD operations, per-project isolation

**Acceptance Criteria:**
- ✅ DocumentStructureManager creates QA/, README.md, EPICS.md
- ✅ Co-located epic-story structure working
- ✅ FeatureRegistry tracks metadata per-project
- ✅ All tests passing (30+ tests)

---

### Epic 2: Validation & Path Resolution (8 points, Week 1.5)

**Goal:** Add stateless validation and variable resolution

**Stories:**
1. **Story 2.1:** Create FeaturePathValidator (stateless) (2 pts)
   - Implement validate_feature_path() - pure function
   - Implement extract_feature_from_path() - pure function
   - Tests: Path validation, feature extraction, edge cases

2. **Story 2.2:** Create FeaturePathResolver with context integration (3 pts)
   - Implement resolve_feature_name() with 6-level priority
   - Integrate with WorkflowContext.feature_name property
   - Implement generate_feature_path() for all path types
   - Tests: Resolution priority, context integration, auto-detection

3. **Story 2.3:** Add WorkflowContext.feature_name property (1 pt)
   - Add property to WorkflowContext.metadata
   - Update usage examples in docs
   - Tests: Property access, persistence across steps

4. **Story 2.4:** Integrate validator with DocumentLifecycleManager (2 pts)
   - Use FeaturePathValidator.extract_feature_from_path()
   - Auto-tag documents with feature_name
   - Tests: Documents tagged correctly, validation works

**Acceptance Criteria:**
- ✅ Stateless validator (no dependencies)
- ✅ Path resolution with 6-level priority
- ✅ WorkflowContext integration working
- ✅ DocumentLifecycleManager auto-tags features
- ✅ All tests passing (25+ tests)

---

### Epic 3: CLI Commands & Variable Updates (7 points, Week 2)

**Goal:** User-friendly CLI and complete variable coverage

**Stories:**
1. **Story 3.1:** Create `create-feature` command (3 pts)
   - Implement CLI command with Click
   - Wrap DocumentStructureManager + FeatureRegistry
   - Add --scale-level option
   - Interactive prompts for description
   - Tests: CLI execution, options, error handling

2. **Story 3.2:** Create `validate-structure` command (2 pts)
   - Implement CLI command
   - Use FeaturePathValidator
   - Output violations with Rich formatting
   - Exit code for CI/CD
   - Tests: Validation, reporting, CI integration

3. **Story 3.3:** Create `list-features` command (1 pt)
   - Implement CLI command
   - Query FeatureRegistry
   - Output table with Rich
   - Tests: Query, formatting

4. **Story 3.4:** Update defaults.yaml with all variable paths (1 pt)
   - Add all feature-scoped paths
   - Add co-located epic-story paths
   - Add ceremony artifact paths
   - Tests: Variable resolution works with all paths

**Acceptance Criteria:**
- ✅ 3 CLI commands working (`create-feature`, `validate-structure`, `list-features`)
- ✅ Complete variable coverage in defaults.yaml
- ✅ Rich formatting for CLI output
- ✅ All tests passing (20+ tests)

---

## Technical Requirements

### Complete Variable Definitions

```yaml
# gao_dev/config/defaults.yaml (UPDATED)

workflow_defaults:
  # Feature-level documents
  feature_dir: "docs/features/{{feature_name}}"
  prd_location: "docs/features/{{feature_name}}/PRD.md"
  architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
  readme_location: "docs/features/{{feature_name}}/README.md"
  epics_overview: "docs/features/{{feature_name}}/EPICS.md"

  # Feature-level folders
  qa_folder: "docs/features/{{feature_name}}/QA"
  retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"

  # Epic-level paths (CO-LOCATED with stories!)
  epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
  epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"

  # Story-level paths (INSIDE epic folder!)
  story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"
  story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"
  context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"

  # Ceremony artifacts (feature-level)
  retrospective_location: "docs/features/{{feature_name}}/retrospectives/epic-{{epic}}-retro.md"
  standup_location: "docs/features/{{feature_name}}/standups/standup-{{date}}.md"
```

**Naming Conventions:**
- `_overview` = master/index file (e.g., `epics_overview`)
- `_folder` = directory path (e.g., `epic_folder`)
- `_location` = specific file path (e.g., `epic_location`)

### Database Schema (Per-Project)

```sql
-- Added to EACH project's .gao-dev/documents.db
-- NOT a global database!

CREATE TABLE features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,          -- Unique per project
    scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
    scale_level INTEGER,                -- 0-4 (from ScaleLevel enum)
    created_at TEXT NOT NULL,
    completed_at TEXT,
    description TEXT,
    owner TEXT,
    metadata JSON
);

CREATE INDEX idx_features_scope ON features(scope);
CREATE INDEX idx_features_status ON features(status);
```

### Integration Points

**Epic 10 (Prompt Abstraction):**
- Use YAML templates for README.md, EPICS.md

**Epic 18 (Variable Resolution):**
- FeaturePathResolver extends WorkflowExecutor.resolve_variables()
- All new variables resolved with priority: params → context → cwd → auto-detect

**Epic 20 (Project-Scoped Lifecycle):**
- Features table in per-project `.gao-dev/documents.db`
- Isolated per project, not global

**Epic 27 (Git Integration):**
- DocumentStructureManager already commits via GitManager
- No additional work needed

**Epic 28 (Ceremony Integration):**
- Ceremony artifacts respect feature structure
- retrospectives/, standups/ folders in feature directory

**Epic 30 (Interactive Brian):**
- Brian lists available features
- Brian auto-detects current feature from cwd
- Conversational feature selection

**Epic 31 (Mary Integration):**
- Mary helps create feature PRDs
- Natural flow: Mary vision elicitation → create-feature → PRD template

---

## Dependencies

### Internal Dependencies (GAO-Dev)

**Required (Must Exist):**
- ✅ Epic 10: Prompt Abstraction (COMPLETE)
- ✅ Epic 18: Variable Resolution (COMPLETE)
- ✅ Epic 20: Project-Scoped Lifecycle (COMPLETE)
- ✅ Epic 27: Git Integration (COMPLETE)
- ✅ Epic 28: DocumentStructureManager (COMPLETE)

**Optional (Integration Enhances):**
- Epic 30: Interactive Brian (add feature selection)
- Epic 31: Mary (generate feature PRDs)

### External Dependencies

- None (uses existing GAO-Dev stack)

---

## Timeline

### Revised Timeline (2 Weeks)

**Week 1 (Days 1-5):**
- Days 1-3: Epic 1 (DocumentStructureManager Enhancement)
- Days 4-5: Epic 2 start (Validation & Resolution)

**Week 2 (Days 6-10):**
- Days 6-7: Epic 2 completion
- Days 8-10: Epic 3 (CLI Commands & Variables)

**Total: 10 days, 3 epics, 25 story points**

**Comparison to v1.0:**
- v1.0: 5 epics, 40 points, 4 weeks (proposed duplication)
- v2.0: 3 epics, 25 points, 2 weeks (extends existing)
- **Efficiency gain:** 50% faster, 70% code reuse

---

## Risks & Mitigations

### Risk 1: Breaking Epic 28

**Severity:** High
**Likelihood:** Low

**Mitigation:**
- ✅ Extend DocumentStructureManager, don't replace
- ✅ All changes are additive (add QA/, README.md)
- ✅ No modifications to existing behavior
- ✅ Comprehensive tests before merge

### Risk 2: Co-Located Structure Too Different

**Severity:** Medium
**Likelihood:** Low

**Mitigation:**
- ✅ User validated design (intuitive for navigation)
- ✅ Consistent with existing patterns (features/{name}/)
- ✅ Clear documentation and examples
- ✅ Migration guide for any existing projects

### Risk 3: Variable Resolution Complexity

**Severity:** Medium
**Likelihood:** Medium

**Mitigation:**
- ✅ Clear 6-level priority documented
- ✅ Comprehensive tests for all scenarios
- ✅ Fallback to sensible defaults
- ✅ Validation errors guide user

### Risk 4: Per-Project Registry Confusion

**Severity:** Low
**Likelihood:** Low

**Mitigation:**
- ✅ Follows Epic 20 architecture (established pattern)
- ✅ Clear documentation
- ✅ CLI auto-detects project root

---

## Success Metrics

### Quantitative

- ✅ Implementation time: 2 weeks (vs. 4 weeks v1.0)
- ✅ Code reuse: 70%+ (Epic 28 foundation)
- ✅ Test coverage: 90%+
- ✅ Tests passing: 75+ tests
- ✅ create-feature performance: <1s
- ✅ validate-structure performance: <2s for 50 features

### Qualitative

- ✅ Developer feedback: "Structure is intuitive"
- ✅ User feedback: "CLI commands are easy to use"
- ✅ Code review: "Clean integration with Epic 28"
- ✅ Documentation: "Complete and clear"

---

## Appendix A: Example Structure

### Greenfield MVP Example

```
docs/features/mvp/
  ├── PRD.md
  ├── ARCHITECTURE.md
  ├── README.md
  ├── EPICS.md
  ├── epics/
  │   ├── 1-core-task-management/
  │   │   ├── README.md
  │   │   ├── stories/
  │   │   │   ├── story-1.1.md  # Create tasks
  │   │   │   ├── story-1.2.md  # Update tasks
  │   │   │   └── story-1.3.md  # Delete tasks
  │   │   └── context/
  │   ├── 2-user-interface/
  │   │   ├── README.md
  │   │   └── stories/
  │   └── 3-data-persistence/
  │       ├── README.md
  │       └── stories/
  ├── QA/
  │   ├── QA_VALIDATION_EPIC_1.md
  │   └── TEST_REPORT_EPIC_1.md
  └── retrospectives/
      └── epic-1-retro.md
```

### Subsequent Feature Example

```
docs/features/user-authentication/
  ├── PRD.md
  ├── ARCHITECTURE.md
  ├── README.md
  ├── EPICS.md
  ├── epics/
  │   └── 4-user-registration/
  │       ├── README.md
  │       ├── stories/
  │       │   ├── story-4.1.md  # Registration form
  │       │   └── story-4.2.md  # Email verification
  │       └── context/
  ├── QA/
  │   └── QA_VALIDATION_EPIC_4.md
  └── retrospectives/
      └── epic-4-retro.md
```

---

## Appendix B: Migration from v1.0

### Key Changes

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| Approach | Create FeatureManager (new) | Extend DocumentStructureManager |
| Epic/Story | Separated (`epics/`, `stories/`) | Co-located (`epics/1-name/stories/`) |
| Registry | Ambiguous (global?) | Per-project (Epic 20) |
| Timeline | 4 weeks, 5 epics | 2 weeks, 3 epics |
| Code Reuse | 30% | 70% |

### Decision Rationale

1. **Extend vs. Replace:** Epic 28 already provides 70% functionality - build on it
2. **Co-Located:** User insight - epics should contain their stories (intuitive)
3. **Per-Project:** Follows Epic 20 architecture (consistency)
4. **Reduced Scope:** Focus on essentials, defer nice-to-haves

---

*End of PRD v2.0*
