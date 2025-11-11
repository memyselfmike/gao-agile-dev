# GAO-Dev Folder Structure & Naming Convention Directive

**Version:** 1.0.0
**Last Updated:** 2025-11-11
**Purpose:** Single source of truth for folder structure and naming conventions across GAO-Dev
**Audience:** All AI agents, developers, and contributors

---

## Table of Contents

1. [Overview](#overview)
2. [Core Principles](#core-principles)
3. [Project Root Structure](#project-root-structure)
4. [Feature-Based Document Structure](#feature-based-document-structure)
5. [Variable Naming Conventions](#variable-naming-conventions)
6. [Document Frontmatter Standards](#document-frontmatter-standards)
7. [Epic and Story Organization](#epic-and-story-organization)
8. [Git Commit Conventions](#git-commit-conventions)
9. [File Naming Rules](#file-naming-rules)
10. [Best Practices Checklist](#best-practices-checklist)

---

## Overview

GAO-Dev uses a **feature-based document structure** that organizes all project artifacts by feature, with co-located epics and stories for intuitive navigation. This directive documents all conventions that agents and developers must follow.

**Key Goals:**
- **Consistency**: All features follow the same structure
- **Discoverability**: Easy to find any document
- **Automation**: Variables resolve predictably
- **Git Integration**: Atomic commits with clear traceability

---

## Core Principles

### 1. Feature-Centric Organization

All documentation lives under `docs/features/{feature_name}/`:
- **Greenfield projects** (new apps): Use `mvp` as feature name
- **Brownfield projects** (existing apps): Use descriptive feature names (`user-auth`, `payment-system`)

### 2. Co-Located Epic-Story Structure

Stories live **inside** their epic folders for intuitive navigation:
```
epics/1-oauth-integration/
├── README.md           # Epic definition
├── stories/            # All stories for this epic
│   ├── story-1.1.md
│   └── story-1.2.md
└── context/            # Context XML files
    ├── story-1.1.xml
    └── story-1.2.xml
```

### 3. Hybrid File + Database Architecture

- **Files**: Live documentation (docs/, src/, tests/)
- **Database**: State tracking, metadata (.gao-dev/documents.db)
- **Git**: Atomic commits with rollback safety

### 4. ASCII-Only, Windows-Compatible

- No emojis in filenames or code
- Use forward slashes in path variables (converted automatically)
- Black formatting (line length 100)

---

## Project Root Structure

### Top-Level Directories

```
gao-agile-dev/
├── .claude/                     # Claude Code agents, skills, commands
│   ├── agents/                  # Specialized sub-agents
│   ├── skills/                  # Modular capabilities
│   ├── commands/                # Custom slash commands
│   └── templates/               # Document templates
│
├── .gao-dev/                    # Global tracking (multi-project)
│   └── documents.db             # Document lifecycle database
│
├── docs/                        # Project documentation
│   ├── features/                # Feature-based docs (PRIMARY LOCATION)
│   │   ├── mvp/                 # Greenfield "MVP" feature
│   │   ├── user-auth/           # Brownfield feature example
│   │   └── payment-system/      # Another feature
│   │
│   ├── bmm-workflow-status.md   # Current project status (START HERE)
│   ├── sprint-status.yaml       # All story statuses
│   └── MIGRATION_GUIDE_*.md     # Migration guides
│
├── gao_dev/                     # Source code
│   ├── agents/                  # Agent implementations
│   ├── cli/                     # CLI commands
│   ├── core/                    # Core services
│   │   ├── services/            # Business services
│   │   ├── models/              # Domain models
│   │   └── workflow_executor.py
│   ├── orchestrator/            # GAODevOrchestrator
│   ├── workflows/               # 55+ embedded workflows
│   └── config/                  # YAML configurations
│       ├── agents/              # Agent configs
│       ├── prompts/             # Prompt templates
│       └── defaults.yaml        # Default variables
│
├── sandbox/                     # Sandbox workspace
│   ├── benchmarks/              # Benchmark configs
│   └── projects/                # Test projects
│       └── my-app/
│           ├── .gao-dev/        # Per-project tracking
│           │   ├── documents.db # Project-specific DB
│           │   └── context.json # Execution context
│           ├── docs/            # Live docs
│           ├── src/             # App code
│           └── tests/           # Test suite
│
└── tests/                       # 400+ tests
```

---

## Feature-Based Document Structure

### Complete Feature Structure

```
docs/features/{feature_name}/
├── PRD.md                       # Product Requirements Document
├── ARCHITECTURE.md              # System Architecture
├── README.md                    # Feature overview & index
├── EPICS.md                     # Epic master list
│
├── epics/                       # Epic definitions (co-located with stories)
│   ├── {epic}-{epic_name}/      # e.g., 1-oauth-integration
│   │   ├── README.md            # Epic definition
│   │   ├── stories/             # All stories for this epic
│   │   │   ├── story-{epic}.{story}.md  # e.g., story-1.1.md
│   │   │   └── story-{epic}.{story}.md  # e.g., story-1.2.md
│   │   └── context/             # Context XML files
│   │       ├── story-{epic}.{story}.xml # e.g., story-1.1.xml
│   │       └── story-{epic}.{story}.xml # e.g., story-1.2.xml
│   │
│   └── {epic}-{epic_name}/      # Another epic
│       └── ...
│
├── QA/                          # Quality assurance artifacts
│   ├── QA_VALIDATION_EPIC_{epic}.md
│   ├── TEST_REPORT_EPIC_{epic}.md
│   └── FINAL_QA_REPORT_{feature_name}.md
│
├── retrospectives/              # Ceremony outputs
│   └── epic-{epic}-retro.md
│
├── ceremonies/                  # Planning sessions, etc.
│   └── planning-{date}.md
│
└── standups/                    # Daily standup notes
    └── standup-{date}.md
```

### Folder Creation Order

When creating a new feature structure, create folders in this order:

1. **Feature root**: `docs/features/{feature_name}/`
2. **Primary documents**: PRD.md, ARCHITECTURE.md, README.md, EPICS.md
3. **Organizational folders**: epics/, QA/, retrospectives/, ceremonies/, standups/
4. **Epic folders** (as needed): `epics/{epic}-{epic_name}/`
5. **Epic subfolders**: `stories/`, `context/`

---

## Variable Naming Conventions

### Naming Rules

1. **Use snake_case**: All lowercase with underscores
2. **Use clear suffixes**: `_location`, `_folder`, `_overview`
3. **No ambiguity**: Name should clearly indicate what it points to
4. **Consistent pattern**: `{type}_{suffix}`

### Variable Suffixes

| Suffix | Meaning | Example | Resolves To |
|--------|---------|---------|-------------|
| `_location` | Specific file path | `prd_location` | `docs/features/mvp/PRD.md` |
| `_folder` | Directory path | `qa_folder` | `docs/features/mvp/QA` |
| `_overview` | Master/index file | `epics_overview` | `docs/features/mvp/EPICS.md` |

### Core Template Variables

#### Feature Identifiers

```yaml
{{feature_name}}    # Feature identifier: "mvp", "user-auth", "payment-system"
{{epic}}            # Epic number: "1", "2", "34"
{{epic_name}}       # Epic identifier: "foundation", "oauth-integration"
{{story}}           # Story number: "1", "2", "5"
```

#### Auto-Generated Variables

```yaml
{{date}}            # Current date: "2025-11-11"
{{timestamp}}       # ISO 8601: "2025-11-11T14:30:00Z"
{{project_name}}    # Project name: "gao-agile-dev"
{{project_root}}    # Project root path: "/path/to/project"
{{agent}}           # Executing agent: "john", "winston", "amelia"
{{workflow}}        # Workflow name: "create-prd", "implement-story"
```

### Feature-Level Path Variables

```yaml
# Feature directory
feature_dir: "docs/features/{{feature_name}}"

# Primary documents
prd_location: "docs/features/{{feature_name}}/PRD.md"
architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
readme_location: "docs/features/{{feature_name}}/README.md"
epics_overview: "docs/features/{{feature_name}}/EPICS.md"

# Organizational folders
qa_folder: "docs/features/{{feature_name}}/QA"
retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"
ceremonies_folder: "docs/features/{{feature_name}}/ceremonies"
standups_folder: "docs/features/{{feature_name}}/standups"
```

### Epic-Level Path Variables

```yaml
# Epic folder (contains README.md, stories/, context/)
epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"

# Epic definition file
epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"
```

### Story-Level Path Variables

```yaml
# Story folder (inside epic folder)
story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"

# Individual story file
story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"

# Context XML folder
context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"

# Context XML file
context_xml_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context/story-{{epic}}.{{story}}.xml"
```

### QA Artifact Variables

```yaml
qa_validation_location: "docs/features/{{feature_name}}/QA/QA_VALIDATION_EPIC_{{epic}}.md"
test_report_location: "docs/features/{{feature_name}}/QA/TEST_REPORT_EPIC_{{epic}}.md"
final_qa_report_location: "docs/features/{{feature_name}}/QA/FINAL_QA_REPORT_{{feature_name}}.md"
```

### Ceremony Artifact Variables

```yaml
retrospective_location: "docs/features/{{feature_name}}/retrospectives/epic-{{epic}}-retro.md"
standup_location: "docs/features/{{feature_name}}/standups/standup-{{date}}.md"
planning_session_location: "docs/features/{{feature_name}}/ceremonies/planning-{{date}}.md"
```

---

## Document Frontmatter Standards

All markdown documents must include YAML frontmatter for metadata tracking.

### Standard Frontmatter Template

```yaml
---
document:
  type: "{type}"                    # prd, architecture, epic, story, qa, retrospective
  state: "{state}"                  # draft, review, approved, complete
  created: "{date}"                 # ISO date: 2025-11-11
  last_modified: "{date}"           # ISO date: 2025-11-11
  author: "{author}"                # Agent name: "John (Product Manager)"
  feature: "{feature_name}"         # Feature identifier
  epic: {epic_num}                  # Epic number (null for feature-level docs)
  story: {story_num}                # Story number (null for non-story docs)
  related_documents:                # List of related docs
    - "ARCHITECTURE.md"
    - "epics/1-foundation/README.md"
  replaces: "{path}"                # Previous version (null if first)
  replaced_by: "{path}"             # Newer version (null if current)
  version: "{version}"              # Semantic version: 1.0.0
---
```

### Document Types

| Type | Description | Example Files |
|------|-------------|---------------|
| `prd` | Product Requirements Document | PRD.md |
| `architecture` | System Architecture | ARCHITECTURE.md |
| `epic` | Epic definition | epics/1-foundation/README.md |
| `story` | User story | stories/story-1.1.md |
| `qa` | Quality assurance | QA/QA_VALIDATION_EPIC_1.md |
| `retrospective` | Retrospective ceremony | retrospectives/epic-1-retro.md |
| `planning` | Planning ceremony | ceremonies/planning-2025-11-11.md |
| `standup` | Daily standup notes | standups/standup-2025-11-11.md |
| `guide` | Reference guide | VARIABLE_NAMING_GUIDE.md |

### Document States

| State | Description | Used For |
|-------|-------------|----------|
| `draft` | Work in progress | Initial creation |
| `review` | Ready for review | Completed, awaiting feedback |
| `approved` | Reviewed and approved | Final version |
| `complete` | Implementation done | Stories, epics after completion |
| `archived` | No longer active | Replaced documents |

---

## Epic and Story Organization

### Epic Naming Convention

Format: `{epic_number}-{epic_name}`

**Rules:**
- Epic number: Sequential integer (1, 2, 3, ...)
- Epic name: Lowercase, hyphen-separated, descriptive
- Must be unique within feature

**Good Examples:**
```
1-foundation
2-oauth-integration
3-session-management
34-integration-variables
```

**Bad Examples:**
```
epic-1              # Redundant with number
1_foundation        # Use hyphens, not underscores
Foundation          # Use lowercase
1                   # Missing name
```

### Story Naming Convention

Format: `story-{epic}.{story}.md`

**Rules:**
- Epic number: Matches parent epic
- Story number: Sequential within epic (1, 2, 3, ...)
- Always use `.md` extension

**Good Examples:**
```
story-1.1.md        # Epic 1, Story 1
story-1.2.md        # Epic 1, Story 2
story-34.5.md       # Epic 34, Story 5
```

**Bad Examples:**
```
story-1-1.md        # Use dot separator
story_1.1.md        # Use hyphen prefix
1.1.md              # Missing "story-" prefix
story-1.1           # Missing .md extension
```

### Context XML Naming Convention

Format: `story-{epic}.{story}.xml`

Mirrors story naming but with `.xml` extension.

**Examples:**
```
story-1.1.xml       # Context for Story 1.1
story-1.2.xml       # Context for Story 1.2
story-34.5.xml      # Context for Story 34.5
```

---

## Git Commit Conventions

### Commit Message Format

```
<type>(<scope>): <description>

<optional body>

🤖 Generated with GAO-Dev
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(epic-1): Story 1.1 - User registration` |
| `fix` | Bug fix | `fix(auth): Resolve token expiration issue` |
| `docs` | Documentation only | `docs: Update PRD with new requirements` |
| `refactor` | Code refactoring | `refactor(core): Extract service layer` |
| `test` | Add/update tests | `test(api): Add integration tests` |
| `chore` | Maintenance | `chore: Update dependencies` |

### Commit Scopes

Common scopes:
- `epic-N`: Epic-level work (e.g., `epic-1`, `epic-34`)
- `story-N.M`: Story-level work (e.g., `story-1.1`)
- Component names: `cli`, `core`, `orchestrator`, `agents`
- Feature names: `user-auth`, `payment-system`

### Commit Rules

1. **One commit per story**: Each story gets exactly ONE atomic commit
2. **Atomic commits**: All changes for a feature together (file + DB + git)
3. **Clear descriptions**: Focus on "why" not "what"
4. **Use present tense**: "Add feature" not "Added feature"

**Good Commit Messages:**
```
feat(epic-1): Story 1.1 - User registration (3 pts)
fix(auth): Resolve session timeout edge case
docs(feature-auth): Update PRD with OAuth requirements
refactor(core): Extract workflow variable resolver
```

**Bad Commit Messages:**
```
Update files                    # Too vague
feat: stuff                     # No scope, unclear
WIP                             # Never commit WIP
Fixed it                        # What did you fix?
```

---

## File Naming Rules

### General Rules

1. **Use lowercase**: All filenames lowercase
2. **Hyphens for multi-word**: Use hyphens, not underscores or spaces
3. **Descriptive names**: Name should indicate content
4. **Proper extensions**: `.md` for markdown, `.yaml` for YAML, `.py` for Python

### Document Files

| Document Type | Filename | Location |
|---------------|----------|----------|
| Product Requirements | `PRD.md` | `docs/features/{feature}/` |
| Architecture | `ARCHITECTURE.md` | `docs/features/{feature}/` |
| Feature README | `README.md` | `docs/features/{feature}/` |
| Epics Overview | `EPICS.md` | `docs/features/{feature}/` |
| Epic Definition | `README.md` | `epics/{epic}-{name}/` |
| Story | `story-{epic}.{story}.md` | `epics/{epic}-{name}/stories/` |
| Context XML | `story-{epic}.{story}.xml` | `epics/{epic}-{name}/context/` |
| QA Validation | `QA_VALIDATION_EPIC_{epic}.md` | `QA/` |
| Test Report | `TEST_REPORT_EPIC_{epic}.md` | `QA/` |
| Final QA | `FINAL_QA_REPORT_{feature}.md` | `QA/` |
| Retrospective | `epic-{epic}-retro.md` | `retrospectives/` |
| Planning | `planning-{date}.md` | `ceremonies/` |
| Standup | `standup-{date}.md` | `standups/` |

### Code Files

```python
# Good
user_service.py
authentication_manager.py
workflow_executor.py

# Bad
UserService.py          # Use lowercase
user-service.py         # Use underscores for Python
userservice.py          # Missing separator
```

### Test Files

```python
# Good
test_user_service.py
test_workflow_executor.py

# Bad
user_service_test.py    # Prefix with "test_"
testUserService.py      # Use snake_case
```

---

## Best Practices Checklist

### When Creating New Features

- [ ] Create feature folder: `docs/features/{feature_name}/`
- [ ] Add primary documents with frontmatter: PRD.md, ARCHITECTURE.md, README.md, EPICS.md
- [ ] Create organizational folders: epics/, QA/, retrospectives/, ceremonies/, standups/
- [ ] Register feature in `.gao-dev/documents.db` (via FeatureRegistry)
- [ ] Update `gao_dev/config/defaults.yaml` with feature-specific variables (if needed)

### When Creating New Epics

- [ ] Create epic folder: `epics/{epic}-{epic_name}/`
- [ ] Add epic README.md with frontmatter
- [ ] Create subfolders: `stories/`, `context/`
- [ ] Update EPICS.md master list
- [ ] Register epic in `.gao-dev/documents.db`

### When Creating New Stories

- [ ] Create story file: `stories/story-{epic}.{story}.md` (inside epic folder)
- [ ] Add story frontmatter with all required fields
- [ ] Create context XML: `context/story-{epic}.{story}.xml`
- [ ] Update epic README.md to reference story
- [ ] Register story in `.gao-dev/documents.db`

### When Implementing Stories

- [ ] Create feature branch: `feature/epic-{epic}-{name}`
- [ ] Use TodoWrite to track tasks (ONE in_progress at a time)
- [ ] Write tests first (TDD approach)
- [ ] Implement functionality
- [ ] Run tests and validate
- [ ] **ONE atomic commit** per story with proper format
- [ ] Update story state to "complete"
- [ ] Update frontmatter `last_modified` date

### When Reviewing Code

- [ ] Check file naming conventions
- [ ] Verify folder structure compliance
- [ ] Validate frontmatter completeness
- [ ] Confirm commit message format
- [ ] Ensure variable names follow conventions
- [ ] Check for ASCII-only content (no emojis)

### When Writing Documentation

- [ ] Include YAML frontmatter
- [ ] Use proper document type and state
- [ ] List related documents
- [ ] Update last_modified date
- [ ] Follow markdown formatting standards
- [ ] Use relative paths for links

---

## Common Mistakes to Avoid

### ❌ DON'T

1. **Hardcode paths**: Never use `docs/features/mvp/PRD.md`
   - ✅ **DO**: Use `docs/features/{{feature_name}}/PRD.md`

2. **Separate epics and stories**: Don't put stories in a separate folder
   - ❌ **BAD**: `docs/features/mvp/epics/` and `docs/features/mvp/stories/`
   - ✅ **GOOD**: `docs/features/mvp/epics/1-foundation/stories/`

3. **Use ambiguous suffixes**: Don't use `_path`, `_file`, `_dir`
   - ❌ **BAD**: `epic_path`, `epic_file`, `epic_dir`
   - ✅ **GOOD**: `epic_location`, `epic_folder`

4. **Skip frontmatter**: Never create documents without YAML frontmatter
   - ✅ **DO**: Always include complete frontmatter

5. **Batch commits**: Don't commit multiple stories at once
   - ✅ **DO**: One atomic commit per story

6. **Use emojis**: Don't use emojis in filenames or code
   - ✅ **DO**: ASCII-only (Windows compatibility)

7. **Forget to update state**: Don't leave stale document states
   - ✅ **DO**: Update `state` and `last_modified` when documents change

---

## Quick Reference

### Starting a Session

1. Read `docs/bmm-workflow-status.md` - Current status
2. Read relevant feature PRD and ARCHITECTURE
3. Check `git log --oneline -10` - Recent commits
4. Read current story file - Acceptance criteria

### Creating a New Feature

```bash
# CLI command (when implemented)
gao-dev create-feature --name user-auth

# Or programmatically
from gao_dev.core.services import DocumentStructureManager
manager = DocumentStructureManager(...)
manager.create_feature_structure("user-auth", scale_level=3)
```

### Checking Compliance

```bash
# Validate feature structure
gao-dev validate-structure --feature user-auth

# List all features
gao-dev list-features
```

### Variable Resolution Priority

1. **Runtime parameters** (highest priority)
2. **Workflow YAML defaults** (`workflow.yaml`)
3. **Config defaults** (`config/defaults.yaml`)
4. **Auto-generated** (date, timestamp, project_name, etc.)

---

## Related Documentation

- **Variable Naming Guide**: `docs/features/feature-based-document-structure/VARIABLE_NAMING_GUIDE.md`
- **Feature-Based PRD**: `docs/features/feature-based-document-structure/PRD.md`
- **Feature-Based Architecture**: `docs/features/feature-based-document-structure/ARCHITECTURE.md`
- **CLAUDE.md**: `CLAUDE.md` - Project guide for Claude agents
- **defaults.yaml**: `gao_dev/config/defaults.yaml` - Complete variable definitions

---

## Version History

- **v1.0.0** (2025-11-11): Initial directive
  - Complete folder structure documentation
  - Variable naming conventions
  - Document frontmatter standards
  - Epic/story organization rules
  - Git commit conventions
  - Best practices checklist

---

**Remember**: These conventions exist to ensure consistency, discoverability, and automation. When in doubt, follow the patterns in existing features and refer to this directive.
