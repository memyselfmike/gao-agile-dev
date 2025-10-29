# Context Tracking & Artifact Passing Roadmap

**Created**: 2025-10-29
**Author**: Analysis of BMAD Method + GAO-Dev Gap Analysis
**Status**: Proposal - For Review & Discussion

This document outlines a comprehensive roadmap for implementing BMAD-style context tracking and artifact passing in GAO-Dev. Based on deep analysis of BMAD Method workflows and identification of current gaps in GAO-Dev.

---

## Executive Summary

**Problem**: GAO-Dev currently relies on hardcoded file paths for artifact passing between workflow stages. Agents must manually search for files, and there's no centralized state tracking or validation.

**Solution**: Implement BMAD-style context tracking with centralized state files, artifact registry, helper workflows, and dynamic context assembly.

**Impact**:
- 100% context visibility across workflows
- Zero search failures
- Reliable state tracking
- Production-ready autonomous development

**Timeline**: ~11-13 weeks (5 epics, 96 story points)

---

## Table of Contents

1. [Analysis: BMAD's Context Tracking Mechanisms](#analysis-bmads-context-tracking-mechanisms)
2. [Gap Analysis: BMAD vs GAO-Dev](#gap-analysis-bmad-vs-gao-dev)
3. [Proposed Solution: 5-Phase Implementation](#proposed-solution-5-phase-implementation)
4. [Phase 1: Foundation](#phase-1-foundation)
5. [Phase 2: Context Assembly](#phase-2-context-assembly)
6. [Phase 3: Helper Workflows](#phase-3-helper-workflows)
7. [Phase 4: Advanced Features](#phase-4-advanced-features)
8. [Phase 5: Developer Experience](#phase-5-developer-experience)
9. [Implementation Timeline](#implementation-timeline)
10. [Success Metrics](#success-metrics)
11. [Code Examples: Before vs After](#code-examples-before-vs-after)

---

## Analysis: BMAD's Context Tracking Mechanisms

### What BMAD Does Right

After analyzing `bmad/bmm/workflows/`, here are the key mechanisms BMAD uses:

#### 1. Centralized State Files

**bmm-workflow-status.md**:
- Tracks current phase, workflow, project level
- Provides next action recommendations
- Universal entry point for all workflows
- Versioned tracking of progress

**sprint-status.yaml**:
```yaml
metadata:
  generated: "2025-10-29"
  project: "GAO-Dev Sandbox"
  project_key: "sandbox"
  tracking_system: "bmad-v6"
  story_location: "docs/features/sandbox-system/stories"

development_status:
  epic-1: "completed"
  1-1-user-authentication: "done"
  1-2-navigation: "in-progress"
  1-3-dashboard: "backlog"
```

**4-State Lifecycle**:
- BACKLOG → TODO → IN PROGRESS → DONE
- Single source of truth for story progression
- Validates legal state transitions

#### 2. Helper Workflow Pattern

BMAD uses **helper workflows** as services that other workflows invoke:

```xml
<invoke-workflow path="{project-root}/bmad/bmm/workflows/helpers/sprint-status">
  <param>action: get_next_story</param>
  <param>filter_status: backlog</param>
</invoke-workflow>
```

**Helper Actions Available**:
- `get_next_story` - Find next story to work on (NO SEARCHING!)
- `update_story_status` - Transition story states with validation
- `check_epic_complete` - Verify epic completion
- `list_stories` - Get filtered story lists
- `validate_transition` - Check if status transition is legal
- `get_metadata` - Extract project metadata
- `complete_retrospective` - Mark retrospective done

#### 3. Explicit Document Discovery

From `create-story/instructions.md`:

```xml
<step n="2" goal="Discover and load source documents">
  <action>Build a prioritized document set for this epic:
    1) tech_spec_file (epic-scoped)
    2) epics_file (acceptance criteria and breakdown)
    3) prd_file (business requirements and constraints)
    4) architecture_file (architecture constraints)
    5) Architecture docs: tech-stack.md, coding-standards.md, etc.
  </action>
  <action>READ COMPLETE FILES for all items found. Store content and paths for citation.</action>
</step>
```

**Key Principles**:
- Prioritized search with fallbacks
- Reads complete files (not just paths)
- Stores for citation
- Handles missing files gracefully

#### 4. Story Context Assembly

The `story-context` workflow creates **XML context files** with:

```xml
<story-context>
  <story id="1.2" title="User Authentication">
    <user-story>
      <as-a>user</as-a>
      <i-want>to log in securely</i-want>
      <so-that>I can access my account</so-that>
    </user-story>

    <artifacts>
      <docs>
        <doc path="docs/PRD.md" section="Authentication" />
        <doc path="docs/architecture.md" section="Security" />
      </docs>

      <code>
        <file path="src/auth/auth.service.ts" reason="Existing auth service to extend" />
        <file path="src/models/user.model.ts" reason="User model definition" />
      </code>

      <interfaces>
        <interface name="AuthService" kind="class" path="src/auth/auth.service.ts" />
      </interfaces>

      <dependencies>
        <node>
          <package name="bcrypt" version="^5.0.0" />
          <package name="jsonwebtoken" version="^9.0.0" />
        </node>
      </dependencies>
    </artifacts>

    <constraints>
      <constraint>Use JWT tokens for session management</constraint>
      <constraint>Hash passwords with bcrypt (min 10 rounds)</constraint>
    </constraints>

    <tests>
      <standards>Use Jest for unit tests, place in __tests__ directories</standards>
      <ideas>
        <idea ac="AC1">Test login with valid credentials</idea>
        <idea ac="AC1">Test login with invalid credentials</idea>
        <idea ac="AC2">Test token expiration</idea>
      </ideas>
    </tests>
  </story-context>
</story-context>
```

**Critical Features**:
- All paths are **project-relative** (not absolute)
- Includes artifact content snippets
- Testing ideas mapped to acceptance criteria
- Constraints from architecture docs

#### 5. No Agent Searching

**Critical Design Principle**: Agents NEVER search for "what to do next".

**Instead**:
1. Agent reads sprint-status.yaml
2. Gets exact story from TODO or IN PROGRESS section
3. Works on that specific story
4. Updates status when done

**Code Example from create-story workflow**:

```xml
<step n="3" goal="Determine target story from sprint status">
  <action>Query sprint-status for next backlog story:</action>

  <invoke-workflow path="{project-root}/bmad/bmm/workflows/helpers/sprint-status">
    <param>action: get_next_story</param>
    <param>filter_status: backlog</param>
  </invoke-workflow>

  <check if="{{result_found}} == false">
    <output>No backlog stories found. Run sprint-planning to refresh.</output>
    <action>HALT</action>
  </check>

  <action>Parse {{result_story_key}} to extract epic_num, story_num, title</action>
</step>
```

#### 6. State Transition Validation

BMAD validates all state transitions before execution:

```xml
<action>Define legal transitions:
  - backlog → drafted ✓
  - drafted → ready-for-dev ✓
  - drafted → drafted ✓ (re-edit)
  - ready-for-dev → in-progress ✓
  - ready-for-dev → drafted ✓ (corrections)
  - in-progress → review ✓
  - review → done ✓
  - review → in-progress ✓ (corrections needed)
  - All other transitions: ✗
</action>
```

---

## Gap Analysis: BMAD vs GAO-Dev

### Current GAO-Dev Implementation

```python
# orchestrator.py lines 366-377
async def create_story(self, epic: int, story: int, story_title: Optional[str] = None):
    title_part = f" with title '{story_title}'" if story_title else ""
    task = f"""Use the Bob agent to create Story {epic}.{story}{title_part}.

Bob should:
1. Ensure the story directory exists for epic {epic}
2. Use the 'create-story' workflow
3. Read the epic definition from docs/epics.md  # HARDCODED!
4. Create story file at docs/stories/epic-{epic}/story-{epic}.{story}.md  # HARDCODED!
5. Include clear acceptance criteria
6. Set status to 'Draft'
7. Commit the story file
"""
```

**Problems**:
1. ❌ Hardcoded file path: `docs/epics.md`
2. ❌ No validation that epics.md exists
3. ❌ No context passed to agent
4. ❌ Agent must manually search
5. ❌ No state tracking
6. ❌ No validation that story doesn't already exist

### Complete Gap Matrix

| Feature | BMAD | GAO-Dev | Gap Severity | Impact |
|---------|------|---------|--------------|--------|
| **State Tracking** | bmm-workflow-status.md + sprint-status.yaml | None | **CRITICAL** | Agents don't know project state |
| **Story Queue** | 4-section BACKLOG/TODO/IN PROGRESS/DONE | None | **CRITICAL** | No story progression tracking |
| **Helper Workflows** | sprint-status helper service | None | **HIGH** | Duplicated status logic everywhere |
| **Context Assembly** | story-context XML with discovery | Hardcoded paths | **HIGH** | Fragile artifact passing |
| **Artifact Registry** | Implicit via paths + context | None | **HIGH** | No tracking of created artifacts |
| **Workflow Invocation** | Can call other workflows | Cannot | **MEDIUM** | Cannot reuse workflow logic |
| **Status Validation** | Validates legal transitions | None | **MEDIUM** | Invalid states possible |
| **Path Normalization** | Project-relative everywhere | Absolute paths | **MEDIUM** | Portability issues |
| **Document Discovery** | Prioritized search with fallbacks | Hardcoded | **MEDIUM** | Breaks when paths change |
| **Pre-flight Validation** | Checks artifacts exist first | None | **MEDIUM** | Fails mid-execution |

---

## Proposed Solution: 5-Phase Implementation

### Overview

Implement BMAD-style context tracking in 5 phases over ~11-13 weeks:

1. **Phase 1: Foundation** (18 points, 2-3 weeks) - State management infrastructure
2. **Phase 2: Context Assembly** (23 points, 2-3 weeks) - Artifact discovery and passing
3. **Phase 3: Helper Workflows** (18 points, 1-2 weeks) - Reusable workflow services
4. **Phase 4: Advanced Features** (23 points, 2-3 weeks) - Validation, resumability
5. **Phase 5: Developer Experience** (14 points, 1-2 weeks) - Observability, debugging

**Total**: 96 story points across 5 epics

---

## Phase 1: Foundation

**Duration**: 2-3 weeks | **Points**: 18 | **Priority**: CRITICAL

### Epic 10: Centralized State Management

#### Story 10.1: Implement sprint-status.yaml State File (5 points)

**Objective**: Create the core state model for tracking projects, epics, and stories.

**Technical Design**:

```python
# gao_dev/core/models/state.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

class StoryStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"

class EpicStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"

@dataclass
class Story:
    epic_id: int
    story_id: int
    key: str  # e.g., "1-2-user-authentication"
    title: str
    status: StoryStatus
    file_path: str
    story_points: Optional[int] = None
    assigned_to: Optional[str] = None
    completed_date: Optional[datetime] = None

@dataclass
class Epic:
    epic_id: int
    key: str  # e.g., "epic-1"
    title: str
    status: EpicStatus
    stories: List[Story]
    total_story_points: int = 0
    completed_story_points: int = 0

@dataclass
class SprintStatus:
    metadata: Dict[str, str]
    epics: List[Epic]

    def get_next_story(self, filter_status: StoryStatus = StoryStatus.BACKLOG) -> Optional[Story]:
        """Get first story matching status."""
        for epic in self.epics:
            for story in epic.stories:
                if story.status == filter_status:
                    return story
        return None

    def update_story_status(self, story_key: str, new_status: StoryStatus) -> bool:
        """Update story status with validation."""
        for epic in self.epics:
            for story in epic.stories:
                if story.key == story_key:
                    # Validate transition
                    if not self._is_valid_transition(story.status, new_status):
                        raise ValueError(f"Invalid transition: {story.status} → {new_status}")
                    story.status = new_status
                    if new_status == StoryStatus.DONE:
                        story.completed_date = datetime.now()
                    return True
        return False

    def _is_valid_transition(self, old: StoryStatus, new: StoryStatus) -> bool:
        """Check if status transition is legal."""
        valid_transitions = {
            StoryStatus.BACKLOG: [StoryStatus.TODO],
            StoryStatus.TODO: [StoryStatus.IN_PROGRESS, StoryStatus.BACKLOG],
            StoryStatus.IN_PROGRESS: [StoryStatus.REVIEW, StoryStatus.TODO],
            StoryStatus.REVIEW: [StoryStatus.DONE, StoryStatus.IN_PROGRESS],
            StoryStatus.DONE: [StoryStatus.DONE],  # Idempotent
        }
        return new in valid_transitions.get(old, [])
```

**YAML Serialization**:

```python
# gao_dev/core/serializers/sprint_status_yaml.py

import yaml
from pathlib import Path
from typing import Dict, Any
from ..models.state import SprintStatus, Epic, Story, StoryStatus, EpicStatus

class SprintStatusSerializer:
    def to_yaml(self, status: SprintStatus) -> str:
        """Serialize SprintStatus to YAML."""
        data = {
            "metadata": status.metadata,
            "development_status": {}
        }

        for epic in status.epics:
            # Add epic status
            data["development_status"][epic.key] = epic.status.value

            # Add story statuses
            for story in epic.stories:
                data["development_status"][story.key] = story.status.value

        return yaml.dump(data, sort_keys=False, allow_unicode=True)

    def from_yaml(self, yaml_content: str) -> SprintStatus:
        """Deserialize YAML to SprintStatus."""
        data = yaml.safe_load(yaml_content)

        # Parse metadata
        metadata = data.get("metadata", {})

        # Parse development_status
        dev_status = data.get("development_status", {})

        # Group stories by epic
        epics_dict = {}
        for key, status_str in dev_status.items():
            if key.startswith("epic-"):
                epic_id = int(key.split("-")[1])
                epics_dict[epic_id] = {
                    "key": key,
                    "status": EpicStatus(status_str),
                    "stories": []
                }
            else:
                # Parse story key: "1-2-user-authentication"
                parts = key.split("-")
                epic_id = int(parts[0])
                story_id = int(parts[1])
                title = "-".join(parts[2:])

                story = Story(
                    epic_id=epic_id,
                    story_id=story_id,
                    key=key,
                    title=title,
                    status=StoryStatus(status_str),
                    file_path=f"docs/stories/epic-{epic_id}/story-{epic_id}.{story_id}.md"
                )

                if epic_id in epics_dict:
                    epics_dict[epic_id]["stories"].append(story)

        # Convert to Epic objects
        epics = [
            Epic(
                epic_id=epic_id,
                key=epic_data["key"],
                title=f"Epic {epic_id}",  # Load from epics.md later
                status=epic_data["status"],
                stories=epic_data["stories"]
            )
            for epic_id, epic_data in sorted(epics_dict.items())
        ]

        return SprintStatus(metadata=metadata, epics=epics)

    def save(self, status: SprintStatus, file_path: Path) -> None:
        """Save SprintStatus to YAML file."""
        yaml_content = self.to_yaml(status)
        file_path.write_text(yaml_content, encoding="utf-8")

    def load(self, file_path: Path) -> SprintStatus:
        """Load SprintStatus from YAML file."""
        yaml_content = file_path.read_text(encoding="utf-8")
        return self.from_yaml(yaml_content)
```

**Deliverables**:
- ✅ State data models (Story, Epic, SprintStatus)
- ✅ Status enums with validation
- ✅ YAML serialization/deserialization
- ✅ File I/O with atomic writes
- ✅ State transition validation
- ✅ Comprehensive tests (>90% coverage)

**Tests**:
```python
# tests/core/models/test_state.py

def test_get_next_story():
    """Test finding next story by status."""
    status = create_test_sprint_status()

    # Get next backlog story
    next_story = status.get_next_story(StoryStatus.BACKLOG)
    assert next_story is not None
    assert next_story.status == StoryStatus.BACKLOG
    assert next_story.key == "1-3-dashboard"

def test_update_story_status():
    """Test updating story status."""
    status = create_test_sprint_status()

    # Valid transition
    result = status.update_story_status("1-1-auth", StoryStatus.TODO)
    assert result == True

    # Invalid transition
    with pytest.raises(ValueError):
        status.update_story_status("1-1-auth", StoryStatus.DONE)  # Can't skip states

def test_yaml_round_trip():
    """Test serialization and deserialization."""
    status = create_test_sprint_status()
    serializer = SprintStatusSerializer()

    # Serialize
    yaml_content = serializer.to_yaml(status)

    # Deserialize
    restored = serializer.from_yaml(yaml_content)

    # Verify
    assert len(restored.epics) == len(status.epics)
    assert restored.epics[0].stories[0].key == status.epics[0].stories[0].key
```

---

#### Story 10.2: Implement workflow-status.md Tracker (3 points)

**Objective**: Track current phase, epic, story, and provide next action recommendations.

**Technical Design**:

```python
# gao_dev/core/models/workflow_status.py

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class WorkflowStatus:
    project_name: str
    project_type: str  # "software", "game"
    project_level: int  # 0-4
    field_type: str  # "greenfield", "brownfield"

    current_phase: int  # 1-4
    current_epic: Optional[int]
    current_story: Optional[str]  # Story key

    next_action: str
    next_command: str
    next_agent: str

    status_history: List[dict]  # Log of status changes

    last_updated: datetime

    def to_markdown(self) -> str:
        """Generate markdown representation."""
        md = f"""---
last_updated: {self.last_updated.strftime("%Y-%m-%d")}
phase: {self.current_phase}-implementation
scale_level: {self.project_level}
project_type: {self.project_type}
project_name: {self.project_name}
---

# Workflow Status

## Current State

**Phase**: {self.current_phase} - Implementation
**Scale Level**: {self.project_level}
**Project Type**: {self.project_type}
**Current Epic**: Epic {self.current_epic}
**Current Story**: {self.current_story}

## Next Actions

**Next Action**: {self.next_action}
**Command**: `{self.next_command}`
**Agent**: {self.next_agent}

## Status History

"""
        for entry in self.status_history[-10:]:  # Last 10 entries
            md += f"- {entry['date']}: {entry['action']}\n"

        return md
```

**Deliverables**:
- ✅ WorkflowStatus data model
- ✅ Current phase/epic/story tracking
- ✅ Next action recommendations
- ✅ Status history log
- ✅ Markdown generation

---

#### Story 10.3: Create StateManager Service (5 points)

**Objective**: Centralized API for all state operations.

**Technical Design**:

```python
# gao_dev/core/state_manager.py

from pathlib import Path
from typing import Optional, List
from .models.state import SprintStatus, Story, StoryStatus, EpicStatus
from .models.workflow_status import WorkflowStatus
from .serializers.sprint_status_yaml import SprintStatusSerializer

class StateManager:
    """Centralized state management service."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.sprint_status_path = project_root / "sprint-status.yaml"
        self.workflow_status_path = project_root / "bmm-workflow-status.md"
        self.serializer = SprintStatusSerializer()

        self._sprint_status: Optional[SprintStatus] = None
        self._workflow_status: Optional[WorkflowStatus] = None

    # ========== Sprint Status Operations ==========

    def load_sprint_status(self) -> SprintStatus:
        """Load sprint status from file."""
        if not self.sprint_status_path.exists():
            raise FileNotFoundError(f"Sprint status not found: {self.sprint_status_path}")

        self._sprint_status = self.serializer.load(self.sprint_status_path)
        return self._sprint_status

    def save_sprint_status(self, status: Optional[SprintStatus] = None) -> None:
        """Save sprint status to file."""
        if status is None:
            if self._sprint_status is None:
                raise ValueError("No sprint status to save")
            status = self._sprint_status

        self.serializer.save(status, self.sprint_status_path)

    def get_next_story(self, filter_status: StoryStatus = StoryStatus.BACKLOG) -> Optional[Story]:
        """Get next story matching status."""
        if self._sprint_status is None:
            self.load_sprint_status()

        return self._sprint_status.get_next_story(filter_status)

    def update_story_status(
        self,
        story_key: str,
        new_status: StoryStatus,
        validate: bool = True
    ) -> bool:
        """Update story status with optional validation."""
        if self._sprint_status is None:
            self.load_sprint_status()

        result = self._sprint_status.update_story_status(story_key, new_status)

        if result:
            self.save_sprint_status()

        return result

    def check_epic_complete(self, epic_id: int) -> bool:
        """Check if all stories in epic are done."""
        if self._sprint_status is None:
            self.load_sprint_status()

        for epic in self._sprint_status.epics:
            if epic.epic_id == epic_id:
                return all(s.status == StoryStatus.DONE for s in epic.stories)

        return False

    def list_stories(
        self,
        filter_status: Optional[StoryStatus] = None,
        epic_id: Optional[int] = None
    ) -> List[Story]:
        """List stories with optional filters."""
        if self._sprint_status is None:
            self.load_sprint_status()

        stories = []
        for epic in self._sprint_status.epics:
            if epic_id is not None and epic.epic_id != epic_id:
                continue

            for story in epic.stories:
                if filter_status is None or story.status == filter_status:
                    stories.append(story)

        return stories

    # ========== Workflow Status Operations ==========

    def load_workflow_status(self) -> WorkflowStatus:
        """Load workflow status from markdown."""
        # Implementation: Parse markdown frontmatter and content
        pass

    def save_workflow_status(self, status: WorkflowStatus) -> None:
        """Save workflow status to markdown."""
        md_content = status.to_markdown()
        self.workflow_status_path.write_text(md_content, encoding="utf-8")

    def update_workflow_status(
        self,
        current_epic: Optional[int] = None,
        current_story: Optional[str] = None,
        next_action: Optional[str] = None
    ) -> None:
        """Update workflow status fields."""
        if self._workflow_status is None:
            self.load_workflow_status()

        if current_epic is not None:
            self._workflow_status.current_epic = current_epic
        if current_story is not None:
            self._workflow_status.current_story = current_story
        if next_action is not None:
            self._workflow_status.next_action = next_action

        self.save_workflow_status(self._workflow_status)
```

**Deliverables**:
- ✅ StateManager service class
- ✅ get_next_story() API
- ✅ update_story_status() with validation
- ✅ check_epic_complete() API
- ✅ list_stories() with filters
- ✅ Workflow status operations
- ✅ Comprehensive tests (>90% coverage)

---

#### Story 10.4: Integrate State into Orchestrator (5 points)

**Objective**: Make GAODevOrchestrator use state management throughout.

**Technical Design**:

```python
# gao_dev/orchestrator/orchestrator.py

class GAODevOrchestrator:
    def __init__(self, project_root: Path, api_key: Optional[str] = None, mode: str = "cli"):
        # ... existing initialization ...

        # NEW: Initialize state manager
        self.state_manager = StateManager(project_root)

        # Try to load existing state
        try:
            self.state_manager.load_sprint_status()
            self.state_manager.load_workflow_status()
        except FileNotFoundError:
            logger.info("state_not_found", message="No existing state files found")

    async def create_story(
        self,
        epic: Optional[int] = None,
        story: Optional[int] = None,
        story_title: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Create a user story using Bob (Scrum Master).

        NEW: If epic/story not provided, gets next from state.
        """
        # NEW: Get next story from state if not specified
        if epic is None or story is None:
            next_story = self.state_manager.get_next_story(StoryStatus.BACKLOG)
            if next_story is None:
                yield "No stories in BACKLOG. Run sprint-planning first."
                return

            epic = next_story.epic_id
            story = next_story.story_id
            story_title = story_title or next_story.title

        # NEW: Load context from state
        sprint_status = self.state_manager.load_sprint_status()

        # Find epic in state
        epic_obj = next((e for e in sprint_status.epics if e.epic_id == epic), None)
        if epic_obj is None:
            yield f"Epic {epic} not found in sprint-status.yaml"
            return

        # NEW: Build task with context
        task = f"""Use the Bob agent to create Story {epic}.{story}: {story_title}

**Context from State**:
- Epic: {epic_obj.title}
- Status: Creating story (will move to TODO after creation)
- Story file: {next_story.file_path if next_story else f'docs/stories/epic-{epic}/story-{epic}.{story}.md'}

**Your Tasks**:
1. Read epic definition from docs/epics.md (Epic {epic})
2. Create story file with:
   - Clear user story statement
   - Acceptance criteria from epic
   - Technical notes
3. Use story template from create-story workflow
4. Set initial status to 'Draft'

After creation, the story will be updated in sprint-status.yaml.
"""

        # Execute agent task
        async for message in self.execute_task(task):
            yield message

        # NEW: Update state after completion
        story_key = f"{epic}-{story}-{story_title.lower().replace(' ', '-')}"
        self.state_manager.update_story_status(story_key, StoryStatus.TODO)

        # NEW: Update workflow status
        self.state_manager.update_workflow_status(
            current_epic=epic,
            current_story=story_key,
            next_action=f"Review Story {epic}.{story}, then run story-ready to approve"
        )

        yield f"\nStory {epic}.{story} created and added to TODO queue."
```

**Deliverables**:
- ✅ StateManager integration in orchestrator
- ✅ Update create_story() to use state
- ✅ Update implement_story() to use state
- ✅ Update all agent methods
- ✅ Auto-load state on orchestrator init
- ✅ Auto-update state after workflows
- ✅ Integration tests with real workflows

---

## Phase 2: Context Assembly

**Duration**: 2-3 weeks | **Points**: 23 | **Priority**: HIGH

### Epic 11: Artifact Discovery & Context Passing

#### Story 11.1: Implement Artifact Registry (5 points)

**Objective**: Track all artifacts created by workflows.

**Technical Design**:

```python
# gao_dev/core/models/artifact.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class ArtifactType(Enum):
    PRD = "prd"
    ARCHITECTURE = "architecture"
    EPICS = "epics"
    STORY = "story"
    CODE = "code"
    TEST = "test"
    DOCS = "docs"
    CONFIG = "config"

@dataclass
class Artifact:
    id: str  # Unique identifier
    path: str  # Project-relative path
    type: ArtifactType
    creator: str  # Workflow or agent that created it
    created_at: datetime
    workflow_name: Optional[str] = None
    epic_id: Optional[int] = None
    story_id: Optional[int] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "type": self.type.value,
            "creator": self.creator,
            "created_at": self.created_at.isoformat(),
            "workflow_name": self.workflow_name,
            "epic_id": self.epic_id,
            "story_id": self.story_id,
            "metadata": self.metadata or {}
        }
```

```python
# gao_dev/core/artifact_registry.py

from pathlib import Path
from typing import List, Optional
import sqlite3
from .models.artifact import Artifact, ArtifactType

class ArtifactRegistry:
    """Registry for tracking all artifacts created by workflows."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / ".gao" / "artifacts.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                type TEXT NOT NULL,
                creator TEXT NOT NULL,
                created_at TEXT NOT NULL,
                workflow_name TEXT,
                epic_id INTEGER,
                story_id INTEGER,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def register(self, artifact: Artifact) -> None:
        """Register a new artifact."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO artifacts
            (id, path, type, creator, created_at, workflow_name, epic_id, story_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artifact.id,
            artifact.path,
            artifact.type.value,
            artifact.creator,
            artifact.created_at.isoformat(),
            artifact.workflow_name,
            artifact.epic_id,
            artifact.story_id,
            json.dumps(artifact.metadata) if artifact.metadata else None
        ))
        conn.commit()
        conn.close()

    def find_by_type(self, artifact_type: ArtifactType) -> List[Artifact]:
        """Find all artifacts of a given type."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM artifacts WHERE type = ? ORDER BY created_at DESC",
            (artifact_type.value,)
        )
        artifacts = [self._row_to_artifact(row) for row in cursor.fetchall()]
        conn.close()
        return artifacts

    def find_by_workflow(self, workflow_name: str) -> List[Artifact]:
        """Find all artifacts created by a workflow."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM artifacts WHERE workflow_name = ? ORDER BY created_at DESC",
            (workflow_name,)
        )
        artifacts = [self._row_to_artifact(row) for row in cursor.fetchall()]
        conn.close()
        return artifacts

    def find_latest(self, artifact_type: ArtifactType) -> Optional[Artifact]:
        """Find most recently created artifact of type."""
        artifacts = self.find_by_type(artifact_type)
        return artifacts[0] if artifacts else None
```

**Deliverables**:
- ✅ Artifact data model
- ✅ ArtifactRegistry with SQLite storage
- ✅ register(), find_by_type(), find_by_workflow() APIs
- ✅ Integration with WorkflowExecutor
- ✅ Tests

---

#### Story 11.2: Document Discovery Service (5 points)

**Objective**: Automatically discover context documents with prioritized search.

**Technical Design**:

```python
# gao_dev/core/document_discovery.py

from pathlib import Path
from typing import List, Optional, Dict
from .artifact_registry import ArtifactRegistry
from .models.artifact import ArtifactType

class DocumentDiscovery:
    """Discover context documents with prioritized search."""

    def __init__(self, project_root: Path, artifact_registry: ArtifactRegistry):
        self.project_root = project_root
        self.artifact_registry = artifact_registry
        self._cache: Dict[str, Path] = {}

    def find_epic_context(self, epic_id: int) -> Dict[str, Optional[Path]]:
        """
        Find all context documents for an epic.

        Returns prioritized document set:
        1. tech_spec (epic-scoped)
        2. epics file
        3. prd
        4. architecture
        5. Additional architecture docs
        """
        context = {}

        # 1. Tech spec (epic-scoped) - highest priority
        tech_spec = self._find_tech_spec(epic_id)
        if tech_spec:
            context["tech_spec"] = tech_spec

        # 2. Epics file
        epics_file = self._find_document("epics.md", ["docs", "docs/features/*"])
        if epics_file:
            context["epics"] = epics_file

        # 3. PRD
        prd_file = self._find_document("PRD.md", ["docs", "docs/features/*"])
        if prd_file:
            context["prd"] = prd_file

        # 4. Architecture
        arch_file = self._find_document("ARCHITECTURE.md", ["docs", "docs/features/*"])
        if arch_file:
            context["architecture"] = arch_file

        # 5. Additional architecture docs
        arch_docs = self._find_architecture_docs()
        context["architecture_docs"] = arch_docs

        return context

    def _find_tech_spec(self, epic_id: int) -> Optional[Path]:
        """Find tech spec for epic."""
        # Try artifact registry first
        artifacts = self.artifact_registry.find_by_type(ArtifactType.ARCHITECTURE)
        for artifact in artifacts:
            if artifact.epic_id == epic_id and "tech-spec" in artifact.path:
                path = self.project_root / artifact.path
                if path.exists():
                    return path

        # Fallback: Search filesystem
        search_patterns = [
            f"docs/tech-spec-epic-{epic_id}.md",
            f"docs/features/*/tech-spec-epic-{epic_id}.md",
            f"docs/architecture/tech-spec-epic-{epic_id}.md",
        ]

        for pattern in search_patterns:
            matches = list(self.project_root.glob(pattern))
            if matches:
                return matches[0]

        return None

    def _find_document(
        self,
        filename: str,
        search_paths: List[str]
    ) -> Optional[Path]:
        """Find document with fallback search paths."""
        # Check cache
        cache_key = f"{filename}:{':'.join(search_paths)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Search paths in order
        for search_path in search_paths:
            matches = list(self.project_root.glob(f"{search_path}/{filename}"))
            if matches:
                # Return most recently modified
                result = max(matches, key=lambda p: p.stat().st_mtime)
                self._cache[cache_key] = result
                return result

        return None

    def _find_architecture_docs(self) -> List[Path]:
        """Find additional architecture documents."""
        doc_patterns = [
            "tech-stack.md",
            "coding-standards.md",
            "testing-strategy.md",
            "backend-architecture.md",
            "frontend-architecture.md",
            "data-models.md",
            "database-schema.md",
            "rest-api-spec.md",
        ]

        found_docs = []
        for pattern in doc_patterns:
            doc = self._find_document(pattern, ["docs", "docs/features/*", "docs/architecture"])
            if doc:
                found_docs.append(doc)

        return found_docs
```

**Deliverables**:
- ✅ DocumentDiscovery service
- ✅ Prioritized search (tech-spec > epics > prd > architecture)
- ✅ Glob pattern matching
- ✅ Fallback strategies
- ✅ Caching for performance
- ✅ Tests with various project structures

---

#### Story 11.3: Add Artifact Outputs to Workflow Definitions (3 points)

**Objective**: Extend workflow.yaml to declare expected outputs.

**Schema Extension**:

```yaml
# gao_dev/workflows/2-plan/prd/workflow.yaml

name: prd
description: Create Product Requirements Document
phase: 2
author: John (Product Manager)

# ... existing fields ...

# NEW: Declare outputs
outputs:
  artifacts:
    - name: "prd_document"
      path: "{{prd_location}}"  # Supports variables
      type: "prd"
      required: true
      description: "Product Requirements Document"
      validation:
        min_size: 1000  # bytes
        max_size: 1000000
        format: "markdown"
```

**Deliverables**:
- ✅ Update workflow schema
- ✅ Output artifact specifications
- ✅ Workflow parser reads outputs
- ✅ Validation after execution
- ✅ Dynamic artifact registration
- ✅ Update existing workflow.yaml files

---

(Continued in next sections...)

---

## Implementation Timeline

### Week 1: Bug Fixes & Setup
- Fix logs and metrics
- Standardize sandbox folder naming
- Git commit improvements
- Setup for Phase 1

### Weeks 2-4: Phase 1 - Foundation (CRITICAL)
- Week 2: Story 10.1 (sprint-status.yaml)
- Week 3: Story 10.2 + 10.3 (workflow-status + StateManager)
- Week 4: Story 10.4 (Orchestrator integration)

### Weeks 5-7: Phase 2 - Context Assembly (HIGH PRIORITY)
- Week 5: Story 11.1 (Artifact Registry)
- Week 6: Story 11.2 + 11.3 (Document Discovery + Workflow Outputs)
- Week 7: Story 11.4 + 11.5 (Context Assembly + Dynamic Passing)

### Weeks 8-9: Phase 3 - Helper Workflows (MEDIUM)
- Week 8: Story 12.1 + 12.2 (Infrastructure + sprint-status helper)
- Week 9: Story 12.3 + 12.4 (workflow-status helper + Refactoring)

### Weeks 10-12: Phase 4 - Advanced Features (MEDIUM)
- Week 10: Story 13.1 + 13.2 (Path Normalization + Dependency Graph)
- Week 11: Story 13.3 + 13.4 (Validation + Quality Gates)
- Week 12: Story 13.5 (Resumability)

### Weeks 13+: Phase 5 - Developer Experience (LOW)
- As time permits or based on feedback

---

## Success Metrics

After full implementation:

### Reliability
- ✅ 100% context visibility across workflows
- ✅ Zero artifact search failures
- ✅ Reliable state tracking for all stories
- ✅ Workflow resumability on failures

### Quality
- ✅ >90% test coverage for all new code
- ✅ Zero hardcoded file paths
- ✅ Validated state transitions
- ✅ Pre-flight validation before execution

### Integration
- ✅ BMAD-compatible state files
- ✅ Helper workflow support
- ✅ Full artifact dependency tracking

### Production Readiness
- ✅ Autonomous development at scale
- ✅ Observable execution
- ✅ Debuggable workflows

---

## Code Examples: Before vs After

### Before (Current GAO-Dev)

```python
# PROBLEM: Hardcoded paths, no validation, no context

async def create_story(self, epic: int, story: int):
    task = f"""Use the Bob agent to create Story {epic}.{story}.

Bob should:
3. Read the epic definition from docs/epics.md  # HARDCODED!
4. Create story file at docs/stories/epic-{epic}/story-{epic}.{story}.md  # HARDCODED!
"""
    async for message in self.execute_task(task):
        yield message
```

**Problems**:
- ❌ Hardcoded file paths
- ❌ No validation that epics.md exists
- ❌ No context passed to agent
- ❌ Agent must manually search
- ❌ No state tracking

### After (With Full Implementation)

```python
# SOLUTION: Dynamic discovery, validation, full context

async def create_story(self, epic: Optional[int] = None, story: Optional[int] = None):
    # 1. Get next story from state (if not specified)
    if epic is None or story is None:
        next_story = self.state_manager.get_next_story(StoryStatus.BACKLOG)
        if next_story is None:
            yield "No stories in BACKLOG. Run sprint-planning first."
            return
        epic = next_story.epic_id
        story = next_story.story_id

    # 2. Discover context documents
    context = self.document_discovery.find_epic_context(epic)
    if not context.get("epics"):
        yield f"ERROR: epics.md not found. Cannot create story."
        return

    # 3. Load context content
    context_content = {}
    for doc_type, doc_path in context.items():
        if doc_path and doc_path.exists():
            context_content[doc_type] = doc_path.read_text()

    # 4. Build task with full context
    task = f"""Use the Bob agent to create Story {epic}.{story}.

**Context Documents** (already loaded for you):

**Epic Definition** (from {context['epics']}):
{self._extract_epic_section(context_content['epics'], epic)}

**PRD Reference** (from {context.get('prd', 'N/A')}):
{self._extract_relevant_section(context_content.get('prd', ''), epic)}

**Architecture Constraints** (from {context.get('architecture', 'N/A')}):
{self._extract_relevant_section(context_content.get('architecture', ''), epic)}

**Your Tasks**:
1. Create story file at: {next_story.file_path}
2. Use acceptance criteria from epic definition above
3. Include technical notes from architecture
4. Set initial status to 'Draft'

Story will be automatically registered in sprint-status.yaml after creation.
"""

    # 5. Execute with full context
    async for message in self.execute_task(task):
        yield message

    # 6. Register artifact
    story_artifact = Artifact(
        id=f"story-{epic}-{story}",
        path=next_story.file_path,
        type=ArtifactType.STORY,
        creator="Bob",
        created_at=datetime.now(),
        workflow_name="create-story",
        epic_id=epic,
        story_id=story
    )
    self.artifact_registry.register(story_artifact)

    # 7. Update state
    story_key = f"{epic}-{story}-{next_story.title}"
    self.state_manager.update_story_status(story_key, StoryStatus.TODO)

    # 8. Update workflow status
    self.state_manager.update_workflow_status(
        current_epic=epic,
        current_story=story_key,
        next_action=f"Review Story {epic}.{story}, then run story-ready"
    )

    yield f"\n✅ Story {epic}.{story} created successfully!"
    yield f"📁 File: {next_story.file_path}"
    yield f"📊 Status: BACKLOG → TODO"
    yield f"🎯 Next: Review story and run 'story-ready' to approve"
```

**Benefits**:
- ✅ Dynamic artifact discovery with validation
- ✅ Full context passed to agent (not just paths)
- ✅ Automatic state tracking
- ✅ Artifact registration
- ✅ Clear next actions
- ✅ Error handling with actionable messages

---

## Appendix: BMAD Workflow Analysis

### Helper Workflow Pattern

**Key Files Analyzed**:
- `bmad/bmm/workflows/helpers/sprint-status/instructions.md` (543 lines)
- `bmad/bmm/workflows/helpers/sprint-status/workflow.yaml`
- `bmad/bmm/workflows/4-implementation/create-story/instructions.md` (138 lines)
- `bmad/bmm/workflows/4-implementation/story-context/instructions.md` (114 lines)

**Key Insights**:
1. Helper workflows are invoked with parameters
2. They return results via variables
3. No output to user (unless show_output=true)
4. Validate inputs and transitions
5. Handle errors gracefully

### State File Format

**sprint-status.yaml Example**:
```yaml
metadata:
  generated: "2025-10-29"
  project: "GAO-Dev Sandbox & Benchmarking System"
  project_key: "sandbox"
  tracking_system: "bmad-v6"
  story_location: "docs/features/sandbox-system/stories"

development_status:
  epic-1: "completed"
  1-1-sandbox-cli: "done"
  1-2-sandbox-manager: "done"
  1-3-project-state: "done"

  epic-2: "in-progress"
  2-1-git-cloning: "done"
  2-2-template-detection: "in-progress"
  2-3-substitution-engine: "backlog"
  2-4-dependency-install: "backlog"
  2-5-validation: "backlog"
```

---

*End of Roadmap Document*
