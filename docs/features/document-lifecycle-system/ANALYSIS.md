# GAO-Dev Document Lifecycle & Context Management System
## Comprehensive Deep-Dive Analysis

**Version:** 1.0.0
**Date:** 2025-11-04
**Author:** John (Product Manager)
**Status:** Analysis Complete

---

## Executive Summary

This analysis addresses critical architectural gaps discovered during Epic 10 benchmark testing: **agents execute workflows but lack project context**. This revealed five interconnected issues that prevent GAO-Dev from scaling beyond software development and limit its effectiveness as an autonomous system.

### Key Findings

1. **Document Lifecycle Management is Non-Existent** - 20+ document types with no organization, versioning, or cleanup strategy
2. **Missing Meta-Prompt System** - Prompts lack dynamic context injection from related documents and artifacts
3. **No Checklist Management System** - Quality gates and validation checklists hardcoded or scattered
4. **Context Persistence & Workflow Tracking** - Pure markdown approach fails for structured queries and state management
5. **System Too Software-Development Specific** - Domain assumptions hardcoded throughout, blocking gao-ops, gao-legal, gao-research

### Impact

**Current State:** GAO-Dev creates dozens of documents per project with no lifecycle management. Agents receive generic instructions like "Create Story 1.1" without knowing the epic context, architectural constraints, or related dependencies. The system cannot answer simple questions like "Which stories are in progress?" without parsing multiple markdown files.

**Recommended Solution:** Hybrid architecture using SQLite for structured tracking/state and markdown for human-readable content, plus meta-prompt system for dynamic context injection and declarative checklist management.

**Expected Outcome:** GAO-Dev becomes truly methodology-agnostic, supports multiple domains, and provides full context to agents for higher-quality autonomous execution.

---

## Table of Contents

1. [Problem Area 1: Document Lifecycle Management](#problem-area-1-document-lifecycle-management)
2. [Problem Area 2: Meta-Prompt System](#problem-area-2-meta-prompt-system)
3. [Problem Area 3: Checklist Management System](#problem-area-3-checklist-management-system)
4. [Problem Area 4: Context Persistence & Workflow Tracking](#problem-area-4-context-persistence--workflow-tracking)
5. [Problem Area 5: Domain Agnosticism](#problem-area-5-domain-agnosticism)
6. [Cross-Cutting Concerns](#cross-cutting-concerns)
7. [Strategic Recommendations](#strategic-recommendations)

---

## Problem Area 1: Document Lifecycle Management

### Current State Assessment

#### Document Inventory (20+ Document Types)

**Pre-Development Documents:**
- `PROJECT_BRIEF.md` - Initial project vision and goals
- `RESEARCH.md` - Market research, competitive analysis
- `BRAINSTORMING.md` - Early ideation notes

**Planning Documents:**
- `PRD.md` - Product Requirements Document (persistent, versioned)
- `GAME_DESIGN_DOC.md` - For game projects
- `TECH_SPEC.md` - Technical specifications
- `epics.md` - Epic breakdown and planning

**Architecture Documents:**
- `ARCHITECTURE.md` - System architecture (persistent, versioned)
- `API.md` - API design and documentation
- `DATA_MODEL.md` - Database schemas and relationships
- `SYSTEM_DESIGN.md` - Low-level design details

**Development Documents:**
- `stories/epic-N/story-N.M.md` - Individual story files (100+ per project)
- `IMPLEMENTATION_GUIDE.md` - Development guidelines
- `STORY_ASSIGNMENTS.md` - Story ownership tracking
- `MIGRATION_GUIDE.md` - Migration instructions

**Quality Gate Documents:**
- `QA_VALIDATION_STORY_X.Y.md` - Per-story QA reports (ephemeral)
- `TEST_REPORT_X.Y.md` - Test execution results (ephemeral)
- `CODE_REVIEW_REPORT.md` - Code review findings
- `FINAL_QA_REPORT_EPIC_X.md` - Epic-level QA summary

**Post-Development Documents:**
- `COMPLETION_SUMMARY.md` - Epic completion reports
- `LESSONS_LEARNED.md` - Retrospective findings
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `README.md` - Project overview and setup (persistent)

**Status Tracking Documents:**
- `bmm-workflow-status.md` - Current epic/story status
- `sprint-status.yaml` - YAML-based sprint tracking
- `NEXT_STEPS.md` - Future work planning

#### Current Document Storage Approach

**What Exists:**
```
docs/
  features/
    {feature-name}/
      PRD.md
      ARCHITECTURE.md
      epics.md
      stories/
        epic-1/
          story-1.1.md
          story-1.2.md
        epic-2/
          story-2.1.md
      QA_VALIDATION_STORY_X.Y.md
      TEST_REPORT_X.Y.md
      COMPLETION_SUMMARY.md
  bmm-workflow-status.md
  sprint-status.yaml
```

**Problems:**
1. **No Organization Strategy** - Documents flat in feature directory, hard to find
2. **No Versioning** - PRD.md and ARCHITECTURE.md change over time, no version history
3. **No Archival** - Old QA reports and test results pile up indefinitely
4. **No Cleanup** - Ephemeral documents (test reports, temp files) never deleted
5. **No Metadata** - Can't query "Show all documents created this sprint"
6. **Duplicate Tracking** - Both `bmm-workflow-status.md` and `sprint-status.yaml` track same info

### Gap Analysis

#### What's Missing

1. **Document Metadata System**
   - Creation timestamp
   - Last updated timestamp
   - Document type (persistent, ephemeral, versioned)
   - Lifecycle stage (draft, approved, archived, deleted)
   - Related documents (epic -> stories, PRD -> architecture)
   - Owner/creator
   - Version number

2. **Lifecycle Automation**
   - Automatic archival of completed epic documents
   - Cleanup of ephemeral QA reports after epic completion
   - Versioning of PRD/Architecture when major changes occur
   - Document state transitions (draft -> review -> approved)

3. **Document Relationships**
   - Epic -> Stories (1:many)
   - PRD -> Architecture (1:1)
   - Story -> QA Reports (1:many)
   - Architecture -> Tech Specs (1:many)
   - No formal relationship tracking

4. **Search & Discovery**
   - Can't find "All QA reports from Epic 6"
   - Can't list "All pending stories"
   - Can't show "Documents modified in last week"
   - No document index

5. **Storage Strategy**
   - Which docs persist indefinitely? (PRD, Architecture, README)
   - Which docs archive after epic? (stories, QA reports)
   - Which docs delete after sprint? (temp files, drafts)
   - No formal policy

### Recommendations

#### Document Classification System

**Persistent Documents** (Keep forever, version control):
- PRD.md
- ARCHITECTURE.md
- API.md
- DATA_MODEL.md
- README.md
- epics.md

**Versioned Documents** (Keep versions, archive old):
- PRD.md (v1.0, v2.0)
- ARCHITECTURE.md (v1.0, v2.0)
- When to version: Major feature additions, architectural changes

**Ephemeral Documents** (Delete after N days/sprint):
- QA_VALIDATION_STORY_X.Y.md (delete after epic complete, 30 days)
- TEST_REPORT_X.Y.md (delete after epic complete, 30 days)
- IMPLEMENTATION_GUIDE.md (archive after epic, delete after 90 days)

**Archived Documents** (Move to archive after epic complete):
- stories/epic-N/*.md (archive entire epic directory after completion)
- COMPLETION_SUMMARY.md (move to archive/epic-N/)
- Epic-specific guides and plans

#### Proposed Document Lifecycle

```
Document Creation
  ↓
[Draft] - Document being written
  ↓
[Review] - Under review (optional, for critical docs)
  ↓
[Active] - Current working document
  ↓
[Completed] - Work finished (for stories, epics)
  ↓
[Archived] - Moved to archive (90 days after completion)
  ↓
[Deleted] - Permanently removed (ephemeral only, after 180 days)
```

#### Storage Structure Proposal

```
docs/
  features/
    {feature-name}/
      current/
        PRD.md (v3.0 - latest)
        ARCHITECTURE.md (v2.0 - latest)
        epics.md
      versions/
        PRD.v1.0.md (archived)
        PRD.v2.0.md (archived)
        ARCHITECTURE.v1.0.md (archived)
      active-stories/
        epic-1/
          story-1.1.md
        epic-2/
          story-2.1.md
      archive/
        epic-1/
          stories/
            story-1.1.md
            story-1.2.md
          COMPLETION_SUMMARY.md
          QA_VALIDATION_*.md (kept for 90 days)
      deleted/  (hidden, for recovery only)
        TEST_REPORT_*.md (deleted after 180 days)
```

#### Lifecycle Management Implementation

**Option 1: Metadata in SQLite**
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL,
    type TEXT NOT NULL,  -- persistent, ephemeral, versioned
    status TEXT NOT NULL,  -- draft, active, completed, archived, deleted
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    archived_at TIMESTAMP,
    deleted_at TIMESTAMP,
    version TEXT,
    parent_id INTEGER,  -- For versioned docs
    epic_id INTEGER,
    story_id INTEGER,
    metadata JSON
);
```

**Option 2: YAML Frontmatter in Documents**
```yaml
---
document_type: story
lifecycle: active
created: 2025-11-04T10:00:00Z
updated: 2025-11-04T15:30:00Z
version: 1.0
epic: 6
story: 1.1
owner: Amelia
auto_archive_after_epic: true
retention_days: 90
---
# Story 6.1: Git Repository Integration
```

**Recommendation: Hybrid Approach**
- SQLite for querying and tracking
- YAML frontmatter for document metadata
- Keep markdown human-readable

---

## Problem Area 2: Meta-Prompt System

### Current State Assessment

#### How Prompts Currently Work

From Epic 10, prompts are YAML templates with variable substitution:

```yaml
# gao_dev/prompts/tasks/implement_story.yaml
name: implement_story
user_prompt: |
  Use the Bob and Amelia agents to implement Story {{epic}}.{{story}}.

  Bob should:
  1. Read the story file from docs/features/.../story-{{epic}}.{{story}}.md
  2. Break down the work

  Amelia should:
  1. Implement the functionality
  2. Write tests
  3. Commit with message: "feat(epic-{{epic}}): implement Story {{epic}}.{{story}}"

variables:
  epic: ""
  story: ""
```

**Problems:**
1. **No Epic Context** - Agent doesn't know which epic they're in, what the epic goals are
2. **No Architecture Reference** - Agent doesn't know architectural constraints or patterns
3. **No Related Stories** - Agent doesn't know about dependent or related stories
4. **No Checklist Integration** - QA checklists mentioned but not included
5. **No Dynamic Content** - Can't include "current sprint goals" or "recent decisions"

#### What Agents Actually Need

When implementing Story 6.1, Amelia needs:
- **Epic Context**: Epic 6 is about "Incremental Story-Based Workflow"
- **Architecture Guidelines**: From ARCHITECTURE.md - use GitManager service pattern
- **Related Stories**: Story 6.4 will use GitManager (dependency)
- **QA Checklist**: Code quality standards, git commit format requirements
- **Project Standards**: Conventional commits, type hints, test coverage >80%

**Current Reality:** Amelia gets "Implement Story 6.1" with no context.

### Gap Analysis

#### What's Missing

1. **Reference Resolution Syntax**
   - Can't include content from other prompts: `@prompt:story_phases/story_creation`
   - Can't include document sections: `@doc:ARCHITECTURE.md#git-integration`
   - Can't include checklist: `@checklist:code_review`

2. **Dynamic Context Injection**
   - Can't inject "current epic goals" from epics.md
   - Can't inject "recent architectural decisions" from ARCHITECTURE.md
   - Can't inject "related story dependencies" from story files

3. **Conditional Content**
   - Can't include sections based on project type (web app vs CLI vs library)
   - Can't include language-specific guidelines (Python vs TypeScript)
   - Can't include domain-specific checklists (security for auth stories)

4. **Prompt Composition**
   - Can't build complex prompts from smaller reusable pieces
   - Can't share common sections across prompts
   - Can't override sections for customization

5. **Context Awareness**
   - Prompts don't know: current sprint, current epic, completed stories
   - Prompts don't know: project scale level, estimated remaining work
   - Prompts don't know: team composition, available agents

### Recommendations

#### Meta-Prompt Syntax Design

**1. Document References** - Include content from documents
```yaml
user_prompt: |
  Implement Story {{epic}}.{{story}}.

  Epic Context:
  @doc:docs/features/{{feature_name}}/epics.md#epic-{{epic}}

  Architecture Guidelines:
  @doc:docs/features/{{feature_name}}/ARCHITECTURE.md#services

  Story Details:
  @doc:docs/features/{{feature_name}}/stories/epic-{{epic}}/story-{{epic}}.{{story}}.md
```

**2. Prompt References** - Include other prompts
```yaml
system_prompt: |
  @prompt:common/developer_persona

  @prompt:common/project_standards
```

**3. Checklist References** - Include quality checklists
```yaml
user_prompt: |
  Implement the feature following these quality standards:

  @checklist:code_quality
  @checklist:testing
  @checklist:git_commits
```

**4. Config References** - Already exists from Epic 10
```yaml
variables:
  model: "@config:claude_model"
  project_name: "@config:project_name"
```

**5. Query References** - Dynamic database queries
```yaml
user_prompt: |
  Recent completed stories for context:
  @query:SELECT title FROM stories WHERE status='completed' ORDER BY completed_at DESC LIMIT 5

  Current sprint goals:
  @query:SELECT goal FROM sprints WHERE status='active'
```

**6. Conditional Sections** - Based on metadata
```yaml
user_prompt: |
  {{#if project_type == "web_app"}}
  Frontend Guidelines:
  - Use React with TypeScript
  - Follow accessibility standards
  {{/if}}

  {{#if story.tags.includes("authentication")}}
  Security Checklist:
  @checklist:security_auth
  {{/if}}
```

#### Meta-Prompt Architecture

**PromptExpander Service:**
```python
class PromptExpander:
    """Expands meta-prompt references to full content."""

    def __init__(
        self,
        prompt_loader: PromptLoader,
        document_manager: DocumentManager,
        checklist_manager: ChecklistManager,
        context_provider: ContextProvider
    ):
        pass

    def expand(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        context: ExecutionContext
    ) -> str:
        """
        Expand all references in prompt template.

        Process order:
        1. Resolve @config: references (from Epic 10)
        2. Resolve @file: references (from Epic 10)
        3. Resolve @doc: references (NEW - document sections)
        4. Resolve @prompt: references (NEW - other prompts)
        5. Resolve @checklist: references (NEW - checklists)
        6. Resolve @query: references (NEW - database queries)
        7. Apply conditional logic (NEW - {{#if}})
        8. Substitute {{variables}}

        Returns:
            Fully expanded prompt string
        """
```

**Example Expansion:**

**Input Template:**
```yaml
user_prompt: |
  Implement Story {{epic}}.{{story}}: {{story_title}}

  Epic Context:
  @doc:epics.md#epic-{{epic}}

  Quality Standards:
  @checklist:code_quality
```

**Expanded Output:**
```
Implement Story 6.1: Git Repository Integration

Epic Context:
## Epic 6: Incremental Story-Based Workflow
Goal: Transform benchmark execution from waterfall to true agile story-based
development. Each story should be created, implemented, and committed
incrementally with full git integration.

Key Requirements:
- Git repo initialized for each sandbox project
- Atomic commits after each story
- Conventional commit format

Quality Standards:
## Code Quality Checklist
- [ ] Type hints on all functions
- [ ] Docstrings on all public methods
- [ ] Test coverage >80%
- [ ] No code duplication (DRY)
- [ ] Follows SOLID principles
...
```

#### Implementation Phases

**Phase 1: Basic References (Epic 12.1)**
- @doc: references for document sections
- @prompt: references for prompt composition
- @checklist: references for checklist inclusion

**Phase 2: Dynamic Context (Epic 12.2)**
- @query: references for database queries
- Context injection from ExecutionContext
- Related document discovery

**Phase 3: Advanced Features (Epic 12.3)**
- Conditional sections ({{#if}})
- Loops ({{#for}})
- Filters and transformations

**Phase 4: Optimization (Epic 12.4)**
- Caching of expanded prompts
- Incremental expansion
- Performance profiling

---

## Problem Area 3: Checklist Management System

### Current State Assessment

#### Existing Checklists

**Current Location:** `gao_dev/checklists/qa-comprehensive.md`

**Contents:**
```markdown
# GAO-Dev Quality Assurance Checklist

## Code Quality
- [ ] Clear separation of concerns
- [ ] Type hints on all functions
- [ ] 80%+ test coverage

## Testing
- [ ] Unit tests for business logic
- [ ] Integration tests for services

## Documentation
- [ ] All public functions have docstrings
- [ ] README up-to-date
```

**Problems:**
1. **Single Monolithic File** - One 66-line checklist for everything
2. **Not Domain-Specific** - Software engineering only, no ops/legal/research
3. **Not Referenced** - Prompts mention checklists but don't include them
4. **Not Versioned** - Changes to checklist affect all projects
5. **Not Customizable** - Can't add project-specific items
6. **No Validation** - Can't track which items completed

#### What We Need

**Multiple Specialized Checklists:**
- `code_quality.yaml` - General code quality standards
- `testing.yaml` - Testing requirements
- `security.yaml` - Security checklist
- `security_auth.yaml` - Authentication-specific security
- `accessibility.yaml` - Accessibility standards (for web apps)
- `performance.yaml` - Performance requirements
- `deployment.yaml` - Deployment readiness
- `documentation.yaml` - Documentation standards
- `git_workflow.yaml` - Git commit and branch standards
- `api_design.yaml` - API design principles
- `database.yaml` - Database schema and migration standards

**Domain-Specific Checklists:**
- `ops/monitoring.yaml` - Monitoring and alerting
- `ops/incident_response.yaml` - Incident response procedures
- `legal/contract_review.yaml` - Contract review checklist
- `legal/compliance.yaml` - Compliance verification
- `research/methodology.yaml` - Research methodology standards

### Gap Analysis

#### What's Missing

1. **Checklist Format**
   - No structured format (YAML vs markdown)
   - No metadata (version, domain, category)
   - No severity/priority levels (critical, recommended, optional)

2. **Checklist Discovery**
   - No registry of available checklists
   - No search/filtering (find all "security" checklists)
   - No recommendations (suggest checklists for story type)

3. **Checklist Application**
   - No way to select which checklists apply to a story
   - No conditional inclusion (auth stories -> security_auth.yaml)
   - No project-level defaults

4. **Checklist Tracking**
   - No way to mark items complete
   - No partial completion status
   - No failure tracking (which items failed)

5. **Plugin Support**
   - No way for plugins to add custom checklists
   - No domain-specific checklist packages

### Recommendations

#### Checklist Format Standard

```yaml
# gao_dev/checklists/code_quality.yaml
checklist:
  metadata:
    name: code_quality
    title: "Code Quality Standards"
    description: "General code quality requirements for all stories"
    version: 1.0.0
    domain: software_engineering
    category: quality
    applies_to:
      - story
      - epic
    tags:
      - code
      - quality
      - testing

  items:
    - id: cq-001
      title: "Type Safety"
      description: "All functions have type hints"
      severity: critical  # critical, high, medium, low, optional
      automated: true  # Can be checked automatically
      check_command: "mypy --strict ."

    - id: cq-002
      title: "Test Coverage"
      description: "Code coverage >80%"
      severity: critical
      automated: true
      check_command: "pytest --cov --cov-fail-under=80"

    - id: cq-003
      title: "No Code Duplication"
      description: "Follow DRY principle"
      severity: high
      automated: false  # Manual review required

    - id: cq-004
      title: "SOLID Principles"
      description: "Code follows SOLID design principles"
      severity: high
      automated: false
```

#### Checklist Manager Service

```python
class ChecklistManager:
    """Manages quality checklists and validation."""

    def __init__(
        self,
        checklists_dir: Path,
        plugin_manager: PluginManager
    ):
        self.checklists_dir = checklists_dir
        self.plugin_manager = plugin_manager
        self._registry: Dict[str, Checklist] = {}

    def load_checklist(self, name: str) -> Checklist:
        """Load checklist by name."""

    def find_checklists(
        self,
        domain: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Checklist]:
        """Find checklists matching criteria."""

    def recommend_checklists(
        self,
        story: Story,
        context: ExecutionContext
    ) -> List[Checklist]:
        """Recommend checklists for a story based on metadata."""
        # If story has tag "authentication" -> include security_auth
        # If story has tag "api" -> include api_design
        # If project type "web_app" -> include accessibility

    def validate_story(
        self,
        story: Story,
        checklists: List[Checklist]
    ) -> ChecklistValidationResult:
        """
        Validate story against checklists.

        Runs automated checks, reports manual items.
        """

    def export_checklist(
        self,
        checklists: List[Checklist],
        format: str = "markdown"
    ) -> str:
        """Export checklists to markdown for inclusion in prompts."""
```

#### Checklist Integration with Prompts

**Automatic Inclusion:**
```yaml
# Story prompt template
user_prompt: |
  Implement Story {{epic}}.{{story}}: {{story_title}}

  Quality Standards (auto-selected based on story metadata):
  @checklists:auto
```

**Manual Inclusion:**
```yaml
# Custom prompt
user_prompt: |
  Review authentication implementation.

  Security Checklist:
  @checklist:security_auth

  Code Quality:
  @checklist:code_quality
```

**Conditional Inclusion:**
```yaml
user_prompt: |
  {{#if story.tags.includes("api")}}
  API Design Standards:
  @checklist:api_design
  {{/if}}
```

#### Plugin Support

Plugins can add custom checklists:

```python
# Plugin: gao-legal
class LegalTeamPlugin(BasePlugin):
    def get_checklists(self) -> List[Path]:
        return [
            Path("checklists/contract_review.yaml"),
            Path("checklists/compliance_gdpr.yaml"),
            Path("checklists/compliance_hipaa.yaml")
        ]
```

---

## Problem Area 4: Context Persistence & Workflow Tracking

### Current State Assessment

#### How State is Currently Tracked

**Markdown Files:**
- `docs/bmm-workflow-status.md` - Human-readable status narrative
- `docs/sprint-status.yaml` - YAML structure with epic/story status

**Example: sprint-status.yaml**
```yaml
epics:
  - epic_number: 6
    name: "Incremental Story-Based Workflow"
    status: completed
    stories:
      - number: 1
        status: done
        name: "Git Repository Integration"
      - number: 2
        status: in_progress
        name: "Story-Based Config Format"
```

**Problems:**
1. **No Querying** - Can't run "SELECT * FROM stories WHERE status='in_progress'"
2. **Manual Updates** - Agent must parse and update YAML correctly
3. **No Relationships** - Can't join stories to epics to metrics
4. **No History** - When did story status change? Who changed it?
5. **No Indexing** - Finding stories is O(n) file parsing

#### What Needs Tracking

**Epics:**
- Epic ID, name, description
- Status (planned, active, completed, cancelled)
- Start date, end date, estimated end date
- Total story points, completed story points
- Owner, methodology

**Stories:**
- Story ID (epic.story), title, description
- Status (draft, ready, in_progress, in_review, completed, blocked)
- Story points, priority
- Owner (agent), dependencies
- Created date, started date, completed date
- Related documents (story file path)
- Acceptance criteria (list)
- Acceptance criteria status (which ones pass/fail)

**Sprints:**
- Sprint ID, name, goal
- Start date, end date
- Status (planned, active, completed)
- Stories included
- Velocity (planned vs actual)

**Workflow Execution:**
- Workflow ID, name, status
- Start time, end time
- Step results (workflow sequence)
- Artifacts created
- Metrics (tokens, cost, duration)

**Documents:**
- Document ID, path, type
- Status, version
- Created, updated, archived dates
- Related to (epic_id, story_id)

### Gap Analysis

#### Markdown Limitations

**Current Approach - Pure Markdown:**

Advantages:
- Human-readable
- Git-friendly (version control, diffs, merges)
- Easy to write and edit
- No database dependencies

Disadvantages:
- Can't query ("Show stories in progress")
- Hard to maintain relationships
- No indexing (slow for large projects)
- Prone to formatting errors
- No schema validation
- No atomic updates (race conditions)

#### What's Missing

1. **Structured Data Store**
   - No database for tracking state
   - No indexed queries
   - No relationship management

2. **State Management**
   - No state machine for story lifecycle
   - No validation of state transitions (can't go draft -> completed, must go through in_progress)
   - No transition history

3. **Query Interface**
   - Can't answer: "Show all blocked stories"
   - Can't answer: "What's the burn-down rate for Epic 6?"
   - Can't answer: "Which stories touch the authentication module?"

4. **Relationship Tracking**
   - Story -> Epic (tracked manually in filename)
   - Story -> Documents (not tracked)
   - Story -> Dependencies (mentioned in text, not tracked)
   - Story -> Commits (not tracked)
   - Epic -> Metrics (not tracked)

5. **Audit Trail**
   - No history of status changes
   - No record of who made changes
   - No timestamp of transitions

### Recommendations

#### Hybrid Architecture: SQLite + Markdown

**Principle:** Use the right tool for the job
- **SQLite:** For structured data, queries, relationships, state tracking
- **Markdown:** For human-readable content, documentation, git-friendly diffs

**What Goes in SQLite:**
- Epic and story metadata (id, status, dates, owner)
- Story relationships and dependencies
- Document metadata and relationships
- Workflow execution state
- Metrics and analytics
- Audit log (state changes)

**What Stays in Markdown:**
- Story content (user story, acceptance criteria, description)
- PRD content (goals, features, requirements)
- Architecture content (diagrams, design decisions)
- Epic descriptions and narratives

**How They Connect:**
```python
# SQLite record
{
  "id": 61,
  "epic_id": 6,
  "story_id": 1,
  "title": "Git Repository Integration",
  "status": "completed",
  "document_path": "docs/features/sandbox-system/stories/epic-6/story-6.1.md"
}

# Markdown file at path has full content
```

#### Database Schema Design

```sql
-- Epics
CREATE TABLE epics (
    id INTEGER PRIMARY KEY,
    epic_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,  -- planned, active, completed, cancelled
    start_date DATE,
    end_date DATE,
    estimated_end_date DATE,
    total_story_points INTEGER,
    completed_story_points INTEGER,
    owner TEXT,
    methodology TEXT,  -- agile, waterfall, kanban
    project_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Stories
CREATE TABLE stories (
    id INTEGER PRIMARY KEY,
    epic_id INTEGER NOT NULL,
    story_number INTEGER NOT NULL,  -- Story number within epic
    full_id TEXT NOT NULL,  -- "6.1", "6.2", etc.
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,  -- draft, ready, in_progress, in_review, completed, blocked, skipped
    story_points INTEGER,
    priority TEXT,  -- P0, P1, P2, P3
    owner TEXT,  -- Agent name
    document_path TEXT,  -- Path to story.md file
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    UNIQUE(epic_id, story_number)
);

-- Story Dependencies
CREATE TABLE story_dependencies (
    story_id INTEGER NOT NULL,
    depends_on_story_id INTEGER NOT NULL,
    dependency_type TEXT,  -- blocks, requires, related
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (depends_on_story_id) REFERENCES stories(id),
    PRIMARY KEY (story_id, depends_on_story_id)
);

-- Acceptance Criteria
CREATE TABLE acceptance_criteria (
    id INTEGER PRIMARY KEY,
    story_id INTEGER NOT NULL,
    criteria_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, passed, failed
    automated BOOLEAN DEFAULT FALSE,
    test_command TEXT,
    FOREIGN KEY (story_id) REFERENCES stories(id)
);

-- Documents
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    document_type TEXT NOT NULL,  -- story, epic, prd, architecture, qa_report
    lifecycle_status TEXT NOT NULL,  -- draft, active, completed, archived, deleted
    version TEXT,
    epic_id INTEGER,
    story_id INTEGER,
    parent_document_id INTEGER,  -- For versioned documents
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    archived_at TIMESTAMP,
    retention_days INTEGER,
    metadata JSON,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (parent_document_id) REFERENCES documents(id)
);

-- Workflow Executions
CREATE TABLE workflow_executions (
    id INTEGER PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    epic_id INTEGER,
    story_id INTEGER,
    status TEXT NOT NULL,  -- in_progress, completed, failed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    artifacts_created JSON,  -- List of file paths
    error_message TEXT,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    FOREIGN KEY (story_id) REFERENCES stories(id)
);

-- State Change Audit Log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL,  -- epic, story, document
    entity_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,  -- status, owner, etc.
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,  -- Agent name or "system"
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSON  -- Additional context about the change
);

-- Projects (for multi-project support)
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    project_type TEXT,  -- software, operations, research, legal
    methodology TEXT,
    created_at TIMESTAMP,
    status TEXT  -- active, completed, archived
);
```

#### Story Lifecycle State Machine

```python
class StoryStatus(Enum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class StoryStateMachine:
    """Enforces valid story status transitions."""

    VALID_TRANSITIONS = {
        StoryStatus.DRAFT: [StoryStatus.READY, StoryStatus.SKIPPED],
        StoryStatus.READY: [StoryStatus.IN_PROGRESS, StoryStatus.SKIPPED],
        StoryStatus.IN_PROGRESS: [StoryStatus.IN_REVIEW, StoryStatus.BLOCKED, StoryStatus.COMPLETED],
        StoryStatus.IN_REVIEW: [StoryStatus.COMPLETED, StoryStatus.IN_PROGRESS],
        StoryStatus.BLOCKED: [StoryStatus.IN_PROGRESS, StoryStatus.SKIPPED],
        StoryStatus.COMPLETED: [],  # Terminal state
        StoryStatus.SKIPPED: []  # Terminal state
    }

    def can_transition(self, from_status: StoryStatus, to_status: StoryStatus) -> bool:
        """Check if transition is valid."""
        return to_status in self.VALID_TRANSITIONS.get(from_status, [])

    def transition(self, story: Story, to_status: StoryStatus, changed_by: str) -> bool:
        """
        Attempt to transition story status.

        Validates transition, updates database, logs audit trail.
        """
```

#### Service Layer

```python
class StoryRepository:
    """Data access for stories."""

    def create_story(self, story_data: Dict) -> Story:
        """Create new story record."""

    def get_story(self, epic_id: int, story_number: int) -> Story:
        """Get story by epic and number."""

    def update_story_status(self, story_id: int, status: StoryStatus, changed_by: str) -> Story:
        """Update story status with audit trail."""

    def find_stories(
        self,
        status: Optional[StoryStatus] = None,
        epic_id: Optional[int] = None,
        owner: Optional[str] = None
    ) -> List[Story]:
        """Find stories matching criteria."""

    def get_blocked_stories(self) -> List[Story]:
        """Get all blocked stories."""

    def get_in_progress_stories(self) -> List[Story]:
        """Get all stories currently in progress."""

class DocumentManager:
    """Manages document lifecycle and relationships."""

    def create_document(
        self,
        path: Path,
        document_type: str,
        epic_id: Optional[int] = None,
        story_id: Optional[int] = None
    ) -> Document:
        """Register new document."""

    def get_documents_for_story(self, story_id: int) -> List[Document]:
        """Get all documents related to a story."""

    def archive_epic_documents(self, epic_id: int) -> int:
        """Archive all documents for a completed epic."""

    def cleanup_ephemeral_documents(self, days: int = 30) -> int:
        """Delete ephemeral documents older than N days."""
```

#### Migration Path

**Phase 1: Add SQLite tracking (parallel with markdown)**
- Create database schema
- Populate from existing sprint-status.yaml
- Keep both markdown and SQLite in sync

**Phase 2: Services use SQLite as source of truth**
- StoryRepository becomes primary data source
- Markdown generated from SQLite for human readability
- sprint-status.yaml becomes read-only view

**Phase 3: Remove redundant markdown tracking**
- Keep story content in markdown
- Remove status tracking from markdown
- Use database for all queries

---

## Problem Area 5: Domain Agnosticism

### Current State Assessment

#### Software Engineering Assumptions Hardcoded

**1. Agent Definitions**
All agents are software engineering roles:
- John (Product Manager)
- Winston (Technical Architect)
- Sally (UX Designer)
- Bob (Scrum Master)
- Amelia (Software Developer)
- Murat (Test Architect)
- Brian (Engineering Manager)
- Mary (Engineering Manager)

**2. Workflows**
All 55+ workflows are software-focused:
- `2-plan/prd` - Product Requirements Document
- `3-solutioning/architecture` - System Architecture
- `3-solutioning/api-design` - API Design
- `4-implementation/dev-story` - Story Development
- `4-implementation/code-review` - Code Review

**3. Documents**
Document types assume software development:
- PRD.md
- ARCHITECTURE.md
- API.md
- DATA_MODEL.md
- TEST_REPORT.md

**4. Checklists**
Single checklist for software quality:
- Code quality standards
- Test coverage requirements
- Git workflow rules

**5. Metrics**
Metrics assume code development:
- Lines of code
- Test coverage percentage
- Build/test pass rate
- Code quality scores

**6. Boilerplates**
Only software boilerplates integrated:
- Python/FastAPI
- React/TypeScript
- Generic web app

### Gap Analysis

#### What Other Domains Need

**gao-ops (Operations Team):**

Agents:
- Olivia (SRE Lead)
- Oliver (DevOps Engineer)
- Ophelia (Monitoring Specialist)
- Oscar (Incident Commander)

Workflows:
- `1-analysis/infrastructure-audit`
- `2-plan/runbook`
- `3-solutioning/monitoring-design`
- `4-implementation/deploy-automation`
- `4-implementation/incident-response`

Documents:
- RUNBOOK.md
- INCIDENT_REPORT.md
- POSTMORTEM.md
- MONITORING_PLAN.md
- SLA_DEFINITION.md

Checklists:
- Deployment readiness
- Incident response procedures
- Security hardening
- Monitoring coverage

**gao-legal (Legal Team):**

Agents:
- Laura (Senior Legal Counsel)
- Leonard (Contract Specialist)
- Linda (Compliance Officer)
- Lewis (Legal Researcher)

Workflows:
- `1-analysis/legal-risk-assessment`
- `2-plan/contract-outline`
- `3-solutioning/contract-drafting`
- `4-implementation/compliance-review`

Documents:
- CONTRACT_DRAFT.md
- LEGAL_MEMO.md
- COMPLIANCE_CHECKLIST.md
- RISK_ASSESSMENT.md

Checklists:
- Contract review checklist
- GDPR compliance
- HIPAA compliance
- Intellectual property review

**gao-research (Research Team):**

Agents:
- Rachel (Lead Researcher)
- Robert (Data Analyst)
- Rebecca (Literature Review Specialist)
- Ryan (Statistical Analyst)

Workflows:
- `1-analysis/literature-review`
- `2-plan/research-methodology`
- `3-solutioning/data-collection-plan`
- `4-implementation/data-analysis`
- `5-reporting/research-paper`

Documents:
- RESEARCH_PROPOSAL.md
- METHODOLOGY.md
- DATA_ANALYSIS.md
- FINDINGS.md
- RESEARCH_PAPER.md

Checklists:
- Research methodology standards
- Data quality checklist
- Statistical validity
- Peer review criteria

#### What's Hardcoded

**Locations of Hardcoding:**

1. **Agent Factory** - `gao_dev/core/factories/agent_factory.py`
   - Hardcoded list of 8 agents
   - Agent tool assignments hardcoded

2. **Workflow Registry** - `gao_dev/core/workflow_registry.py`
   - Looks for workflows in `gao_dev/workflows/`
   - No plugin workflow loading

3. **Document Types** - No formal enum, scattered strings
   - "prd", "architecture", "story", "epic"
   - Assumed throughout codebase

4. **Checklist Path** - `gao_dev/checklists/`
   - Single directory, no domain separation

5. **Boilerplate Templates** - `gao_dev/sandbox/boilerplates/`
   - Only software templates

6. **Brian's Scale Levels** - `gao_dev/methodologies/adaptive_agile/scale_levels.py`
   - Scale definitions assume software projects
   - Level 0-4 descriptions mention "stories", "code", "tests"

### Recommendations

#### Domain Configuration Architecture

**1. Domain Definition Files**

```yaml
# gao_dev/domains/software_engineering.yaml
domain:
  name: software_engineering
  title: "Software Engineering"
  description: "Build software applications"

  agents:
    - name: John
      role: Product Manager
      config_file: agents/john.yaml
    - name: Amelia
      role: Developer
      config_file: agents/amelia.yaml
    # ... 6 more

  workflows:
    - 1-analysis/product-brief
    - 2-plan/prd
    - 3-solutioning/architecture
    - 4-implementation/dev-story

  document_types:
    - prd
    - architecture
    - api
    - story
    - test_report

  checklists:
    - code_quality
    - testing
    - security
    - api_design

  boilerplates:
    - python-fastapi
    - react-typescript

  scale_levels:
    config_file: scale_levels/software_engineering.yaml
```

```yaml
# gao_dev/domains/operations.yaml
domain:
  name: operations
  title: "Operations & DevOps"
  description: "Manage infrastructure and deployments"

  agents:
    - name: Olivia
      role: SRE Lead
      config_file: agents/olivia.yaml
    - name: Oliver
      role: DevOps Engineer
      config_file: agents/oliver.yaml

  workflows:
    - 1-analysis/infrastructure-audit
    - 2-plan/runbook
    - 3-solutioning/monitoring-design
    - 4-implementation/deploy-automation

  document_types:
    - runbook
    - incident_report
    - postmortem
    - monitoring_plan

  checklists:
    - deployment_readiness
    - incident_response
    - security_hardening

  boilerplates:
    - terraform-aws
    - kubernetes-base
```

**2. Domain Manager Service**

```python
class DomainManager:
    """Manages domain configurations and switching."""

    def __init__(self, domains_dir: Path, plugin_manager: PluginManager):
        self.domains_dir = domains_dir
        self.plugin_manager = plugin_manager
        self._domains: Dict[str, DomainConfig] = {}

    def load_domain(self, domain_name: str) -> DomainConfig:
        """Load domain configuration."""

    def get_available_domains(self) -> List[str]:
        """List all available domains."""

    def set_active_domain(self, domain_name: str) -> None:
        """Set the active domain for current project."""

    def get_agents_for_domain(self, domain_name: str) -> List[AgentConfig]:
        """Get all agents configured for a domain."""

    def get_workflows_for_domain(self, domain_name: str) -> List[str]:
        """Get workflow paths for a domain."""
```

**3. Project-Level Domain Selection**

```yaml
# Project configuration: .gaodev/config.yaml
project:
  name: "Infrastructure Monitoring System"
  domain: operations  # <-- Select domain here
  methodology: agile

  # Override or add domain-specific settings
  agents:
    - Olivia
    - Oliver
    - Ophelia

  workflows:
    custom_workflows_dir: .gaodev/workflows

  checklists:
    custom_checklists_dir: .gaodev/checklists
```

**4. Multi-Domain Projects**

Some projects need multiple domains:

```yaml
# Example: Building a SaaS application
project:
  name: "SaaS Todo App"
  primary_domain: software_engineering

  additional_domains:
    - operations  # For deployment and monitoring
    - legal  # For privacy policy and terms of service

  agents:
    # Software Engineering
    - John
    - Amelia
    - Winston
    # Operations
    - Olivia
    # Legal
    - Laura
```

**5. Domain Plugin System**

```python
# Plugin: gao-domain-legal
class LegalDomainPlugin(BasePlugin):
    """Adds legal domain to GAO-Dev."""

    def get_domain_config(self) -> DomainConfig:
        return DomainConfig.from_yaml(
            Path(__file__).parent / "domain.yaml"
        )

    def get_agents(self) -> List[AgentConfig]:
        return [
            AgentConfig.from_yaml(Path("agents/laura.yaml")),
            AgentConfig.from_yaml(Path("agents/leonard.yaml")),
            AgentConfig.from_yaml(Path("agents/linda.yaml")),
            AgentConfig.from_yaml(Path("agents/lewis.yaml"))
        ]

    def get_workflows(self) -> List[Path]:
        return [
            Path("workflows/1-analysis/legal-risk-assessment"),
            Path("workflows/2-plan/contract-outline"),
            Path("workflows/3-solutioning/contract-drafting")
        ]
```

#### Implementation Strategy

**Phase 1: Extract Software Engineering Domain (Epic 12.5)**
- Create `domains/software_engineering.yaml`
- Move agent configs to domain
- Move workflow references to domain
- Make system load from domain config
- **Goal:** No breaking changes, everything works as before

**Phase 2: Domain Abstraction Layer (Epic 12.6)**
- Create DomainManager service
- Update services to use DomainManager
- Support domain switching
- **Goal:** Can load different domains, but only one at a time

**Phase 3: Multi-Domain Support (Epic 12.7)**
- Support projects with multiple domains
- Agent collaboration across domains
- Workflow sequencing across domains
- **Goal:** SaaS project can use both software and operations agents

**Phase 4: Domain Plugin Ecosystem (Epic 12.8)**
- Plugin API for domain definitions
- Create example plugins: gao-ops, gao-legal, gao-research
- Documentation for creating custom domains
- **Goal:** Community can create domain-specific extensions

---

## Cross-Cutting Concerns

### Performance & Scalability

**Concerns:**
1. **Database Size** - SQLite with 1000+ stories, 100+ epics, 10000+ documents
2. **Prompt Expansion** - Meta-prompts with many @doc: references could be slow
3. **Checklist Validation** - Running 50+ automated checks per story
4. **Document Archival** - Moving thousands of files to archive

**Recommendations:**
- SQLite indexes on commonly queried fields (status, epic_id, created_at)
- Prompt expansion caching (cache expanded prompts, invalidate on document change)
- Parallel checklist execution (run automated checks in parallel)
- Async archival (background job for document archival)
- Pagination for large queries (limit 100 results, use offset)

### Testing Strategy

**Comprehensive Testing Required:**

1. **Unit Tests**
   - DocumentManager, StoryRepository, ChecklistManager
   - Meta-prompt expansion logic
   - State machine transitions
   - Domain loading

2. **Integration Tests**
   - SQLite + Markdown synchronization
   - Prompt expansion with real documents
   - Checklist validation end-to-end
   - Domain switching

3. **Migration Tests**
   - Test migration from current sprint-status.yaml to SQLite
   - Test backward compatibility
   - Test rollback scenarios

4. **Performance Tests**
   - Query performance with 1000+ stories
   - Prompt expansion with large documents
   - Parallel checklist validation

### Migration & Backward Compatibility

**Critical Requirement:** No breaking changes to existing projects

**Strategy:**
1. **Phase 1:** Add new systems alongside existing (dual write)
2. **Phase 2:** Migrate existing data to new systems
3. **Phase 3:** Switch to new systems as primary
4. **Phase 4:** Deprecate old systems (keep for 2 releases)

**Example Migration:**
```python
# Phase 1: Dual write
story_repository.create_story(story_data)  # Write to SQLite
update_sprint_status_yaml(story_data)  # Also write to YAML

# Phase 2: SQLite primary, YAML generated
story = story_repository.create_story(story_data)
generate_sprint_status_from_db()  # Read-only YAML

# Phase 3: SQLite only
story = story_repository.create_story(story_data)
# YAML removed or deprecated
```

### Documentation Requirements

**Must Document:**
1. **Architecture Decisions**
   - Why hybrid SQLite + Markdown?
   - Why meta-prompts over hardcoded?
   - Why domain abstraction?

2. **Migration Guides**
   - How to upgrade existing projects
   - How to migrate sprint-status.yaml to SQLite
   - How to convert hardcoded prompts to meta-prompts

3. **Developer Guides**
   - How to create custom checklists
   - How to create domain plugins
   - How to write meta-prompts with references

4. **User Guides**
   - How to query story status
   - How to manage document lifecycle
   - How to switch domains

---

## Strategic Recommendations

### Priority Order for Implementation

**Epic 12.1: Document Lifecycle Management (8 weeks)**
- Document classification and metadata
- Lifecycle automation (draft → active → archived → deleted)
- DocumentManager service
- SQLite schema for documents
- Archival and cleanup automation

**Epic 12.2: Meta-Prompt System (6 weeks)**
- PromptExpander service
- @doc: reference resolution
- @prompt: reference resolution
- @checklist: reference resolution
- Context injection

**Epic 12.3: Checklist Management System (4 weeks)**
- Structured checklist format (YAML)
- ChecklistManager service
- Checklist validation and tracking
- Plugin support for custom checklists

**Epic 12.4: Context Persistence & Workflow Tracking (8 weeks)**
- SQLite schema for epics, stories, sprints
- StoryRepository service
- State machine for story lifecycle
- Migration from sprint-status.yaml
- Audit logging

**Epic 12.5: Domain Abstraction - Foundation (6 weeks)**
- Extract software_engineering domain
- DomainManager service
- Domain configuration loading
- Backward compatibility

**Total Estimated Duration:** 32 weeks (8 months)

### Success Metrics

**After Implementation:**

1. **Context Quality**
   - Agents receive full context (epic goals, architecture, related stories)
   - 90% reduction in "missing context" errors
   - Agents can answer "What are we building?" without user input

2. **Document Management**
   - Zero orphaned documents
   - 100% of ephemeral documents cleaned up automatically
   - Can query "All QA reports from last sprint" in <1 second

3. **Query Performance**
   - "Show in-progress stories" query in <100ms
   - "Show blocked stories with dependencies" query in <500ms
   - Support 1000+ stories without performance degradation

4. **Domain Flexibility**
   - Create gao-ops team in <1 week (vs 2+ months)
   - Create gao-legal team in <1 week
   - Support multi-domain projects (e.g., SaaS = software + ops + legal)

5. **Checklist Effectiveness**
   - 80%+ of quality checks automated
   - Zero missed checklist items
   - Custom checklists for specialized domains

### Risk Assessment

**High Risks:**

1. **Database Migration Complexity**
   - **Risk:** Migrating existing sprint-status.yaml data to SQLite could fail
   - **Mitigation:** Comprehensive migration scripts with rollback, extensive testing

2. **Performance Degradation**
   - **Risk:** Meta-prompt expansion could slow down execution
   - **Mitigation:** Caching, lazy loading, performance testing

3. **Breaking Changes**
   - **Risk:** New architecture could break existing projects
   - **Mitigation:** Backward compatibility layer, deprecation warnings, dual-mode operation

4. **Learning Curve**
   - **Risk:** Developers struggle with new meta-prompt syntax
   - **Mitigation:** Comprehensive documentation, examples, IDE support

**Medium Risks:**

1. **Over-Engineering**
   - **Risk:** System becomes too complex for actual needs
   - **Mitigation:** Incremental implementation, validate at each epic

2. **Plugin Ecosystem Adoption**
   - **Risk:** Community doesn't create domain plugins
   - **Mitigation:** Create 3 reference implementations (ops, legal, research)

### Next Steps

**Immediate (Next Sprint):**
1. Create PRD for Epic 12 (Document Lifecycle System)
2. Create Architecture Proposal for hybrid SQLite + Markdown approach
3. Create Roadmap with detailed epic breakdown and story outlines
4. Get stakeholder approval for strategic direction

**Near-Term (1-2 Sprints):**
1. Begin Epic 12.1 implementation (Document Lifecycle Management)
2. Create proof-of-concept for meta-prompt system
3. Design SQLite schema with DBA review
4. Create migration strategy document

**Long-Term (6-12 Months):**
1. Complete all 5 epics (12.1 through 12.5)
2. Create 3 reference domain plugins (gao-ops, gao-legal, gao-research)
3. Migrate existing projects to new architecture
4. Launch domain plugin ecosystem

---

## Appendix A: Reference Architecture Patterns

### Similar Systems

1. **Terraform** - Declarative infrastructure, modular providers
   - Lesson: Plugin system for domain extensions
   - Lesson: State management (tfstate file + backend)

2. **Kubernetes** - Declarative configuration, CRDs
   - Lesson: YAML-based resource definitions
   - Lesson: Controllers reconcile desired vs actual state

3. **Ansible** - Playbooks with includes, roles
   - Lesson: Composition of smaller reusable units
   - Lesson: Variable substitution and templating

4. **Jira** - Issue tracking with workflows
   - Lesson: State machines for issue lifecycle
   - Lesson: Custom fields and workflows per project

### Proven Design Patterns

1. **Repository Pattern** - StoryRepository, DocumentRepository
2. **State Machine Pattern** - Story status transitions
3. **Strategy Pattern** - Domain-specific strategies
4. **Factory Pattern** - AgentFactory, ChecklistFactory
5. **Facade Pattern** - Simplified interfaces to complex subsystems
6. **Observer Pattern** - Event bus for lifecycle events

---

## Appendix B: Glossary

**Terms:**

- **Document Lifecycle** - The stages a document goes through (draft → active → archived → deleted)
- **Meta-Prompt** - A prompt template with references to other content (@doc:, @prompt:, @checklist:)
- **Domain** - A specialized area of work (software engineering, operations, legal, research)
- **Ephemeral Document** - A temporary document that should be deleted after N days
- **Persistent Document** - A document that should be kept indefinitely
- **Checklist** - A structured list of quality gates and validation items
- **Story State Machine** - The valid transitions between story statuses
- **Hybrid Architecture** - Using both SQLite (structured data) and Markdown (content)

---

**End of Analysis Document**
