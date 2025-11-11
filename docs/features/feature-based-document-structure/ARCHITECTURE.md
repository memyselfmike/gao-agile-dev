---
document:
  type: "architecture"
  state: "draft"
  created: "2025-11-11"
  last_modified: "2025-11-11"
  author: "Winston (Technical Architect)"
  feature: "feature-based-document-structure"
  epic: null
  story: null
  related_documents:
    - "PRD.md"
    - "README.md"
    - "FIXES_SUMMARY.md"
    - "CRITICAL_ANALYSIS.md"
  replaces: null
  replaced_by: null
---

# System Architecture
## Feature-Based Document Structure Enhancement

**Version:** 3.0.0
**Date:** 2025-11-11
**Author:** Winston (Technical Architect)
**Status:** Draft (Post-State Management Integration Review)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-11 | Initial draft |
| 2.0.0 | 2025-11-11 | Critical fixes applied: Extension approach, co-located structure, stateless validator, per-project registry, WorkflowContext integration |
| 3.0.0 | 2025-11-11 | State management integration: FeatureStateService (6th service), GitIntegratedStateManager pattern, atomic operations, Epic 32-34 numbering |

---

## Table of Contents

1. [System Context](#system-context)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Data Models](#data-models)
5. [Integration Points](#integration-points)
6. [Technology Stack](#technology-stack)
7. [Directory Structure](#directory-structure)
8. [Implementation Details](#implementation-details)
9. [Migration Strategy](#migration-strategy)
10. [Performance Considerations](#performance-considerations)
11. [Security & Validation](#security--validation)

---

## System Context

### Purpose

The Feature-Based Document Structure Enhancement **integrates** with GAO-Dev's state management system (Epics 24-27) to provide atomic feature creation, comprehensive tracking, validation, and variable resolution. It transforms document organization from inconsistent patterns to a rigorously enforced, feature-centric hierarchy.

**Key Insight:** This feature follows the proven state service pattern (Epics 24-27), creating FeatureStateService as the 6th state service and using GitIntegratedStateManager for atomic file + DB + git operations. The `epics.feature` column already exists in the schema (line 13 of `schema.sql`), confirming this integration was designed from the start.

### Key Goals

1. **FeatureStateService**: Create 6th state service following proven Epic 24-27 pattern
2. **Atomic Operations**: Use GitIntegratedStateManager for file + DB + git atomicity
3. **Extend DocumentStructureManager**: Add missing pieces (QA/, README.md, auto_commit parameter)
4. **Structure Validation**: Programmatic validation with clear violation reporting
5. **Variable Resolution**: Resolve `{{feature_name}}` with intelligent auto-detection
6. **Co-Located Organization**: Epics contain their stories (intuitive navigation)

### What Already Exists

**Epics 24-27: State Management System**
- ✅ EpicStateService, StoryStateService, ActionItemService, CeremonyService, LearningIndexService (5 services)
- ✅ StateCoordinator (facade pattern for all services)
- ✅ GitIntegratedStateManager (atomic file + DB + git operations)
- ✅ Database schema with `epics.feature TEXT` column (line 13 of schema.sql)
- ✅ Thread-safe connections, <5ms queries, auto-rollback on errors

**Epic 28: DocumentStructureManager**
- ✅ Feature folder creation (`docs/features/{name}/`)
- ✅ Scale-level based structure (Level 2-4 support)
- ✅ Git integration via GitManager
- ✅ DocumentLifecycleManager integration
- ✅ Template generation for PRD.md, ARCHITECTURE.md
- ✅ Folder creation: stories/, epics/, retrospectives/, ceremonies/

**What's Missing (This Feature Adds):**
- ❌ FeatureStateService (6th state service)
- ❌ features table in database
- ❌ GitIntegratedStateManager.create_feature() method
- ❌ QA/ folder (not created by Epic 28)
- ❌ README.md (not generated)
- ❌ auto_commit parameter on DocumentStructureManager
- ❌ MVP concept (no distinction from features)
- ❌ Structure validation (no compliance checking)
- ❌ Variable resolution (no `{{feature_name}}` support)
- ❌ Co-located epic-story structure (epics/ contains folders, stories/ is separate)

### System Boundaries

**In Scope:**
- Create FeatureStateService (6th state service following Epic 24 pattern)
- Extend StateCoordinator with feature_service facade
- Extend GitIntegratedStateManager with create_feature() method
- Extend DocumentStructureManager with QA/, README.md, auto_commit parameter
- Create FeaturePathValidator for structure validation (stateless)
- Create FeaturePathResolver for variable resolution (WorkflowContext integration)
- CLI commands wrapping GitIntegratedStateManager
- Update variable defaults for co-located structure
- Schema migration for features table

**Out of Scope:**
- Modifying core logic of existing services (reuse patterns as-is)
- Content generation (AI writes docs, not this system)
- Visual UI (CLI only)
- Real-time collaboration

---

## Architecture Overview

### High-Level Architecture (v3.0 - State Management Integration)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Application Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐          │
│  │Orchestrators │  │   Agents     │  │ Workflow Engine  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘          │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│                   CLI Commands Layer (NEW)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐         │
│  │create-feature│  │validate-     │  │list-features     │         │
│  │              │  │structure     │  │                  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│     GitIntegratedStateManager (ATOMIC ORCHESTRATOR - EXTENDED)      │
│                                                                      │
│  Existing Methods:                  NEW Method:                     │
│  • create_epic()                    • create_feature() ← NEW!       │
│  • create_story()                   ├─ Pre-check git clean          │
│  • transition_story()               ├─ Call DocumentStructure       │
│                                     │   Manager (helper)             │
│  Pattern (ALL ATOMIC):              ├─ Insert via StateCoordinator  │
│  1. Pre-check git clean             ├─ Git commit                   │
│  2. Write files                     └─ Rollback on error            │
│  3. Update database                                                 │
│  4. Git commit                                                      │
│  5. Rollback on error                                               │
└──────────────────┬───────────────────────┬──────────────────────────┘
                   │                       │
      ┌────────────▼────────────┐  ┌───────▼────────────────────────┐
      │ StateCoordinator (FACADE)│  │ DocumentStructureManager      │
      │                          │  │ (HELPER - EXTENDED)           │
      │ Existing 5 services:     │  │                               │
      │ • EpicStateService       │  │ • Creates folders             │
      │ • StoryStateService      │  │ • Generates templates         │
      │ • ActionItemService      │  │ • + QA/ folder [NEW]          │
      │ • CeremonyService        │  │ • + README.md [NEW]           │
      │ • LearningIndexService   │  │ • + auto_commit param [NEW]   │
      │                          │  │   (default: true, set false   │
      │ NEW: 6th service         │  │    when called by GISM)       │
      │ • FeatureStateService    │  │                               │
      │   (DB CRUD only)         │  └───────────────────────────────┘
      └──────────┬───────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│               Per-Project Database (.gao-dev/documents.db)          │
│                                                                      │
│  Existing Tables:           NEW Table:                              │
│  • epics (has feature col!) • features ← NEW!                       │
│  • stories                    ├─ name (unique)                      │
│  • action_items               ├─ scope (mvp/feature)                │
│  • ceremonies                 ├─ scale_level (0-4)                  │
│  • learning_index             ├─ status, owner, dates               │
│                               └─ metadata (JSON)                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│         Supporting Components (NEW - STATELESS/RESOLVERS)           │
│                                                                      │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐ │
│  │ FeaturePathValidator        │  │ FeaturePathResolver         │ │
│  │ (STATELESS)                 │  │ (WorkflowContext aware)     │ │
│  │ • validate_feature_path()   │  │ • resolve_feature_name()    │ │
│  │ • extract_feature_from_path│  │   (6-level priority)        │ │
│  │ • validate_structure()      │  │ • generate_feature_path()   │ │
│  │ • Pure functions (no DB)    │  │ • Co-located paths          │ │
│  └─────────────────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

**1. Follow State Service Pattern (Epics 24-27)**
- FeatureStateService follows exact same pattern as Epic/Story/ActionItem/Ceremony/Learning services
- StateCoordinator becomes complete facade (6 services)
- GitIntegratedStateManager provides atomic operations
- Thread-safe, <5ms queries, auto-rollback on errors

**2. Atomic Operations (GitIntegratedStateManager)**
- All operations are ATOMIC: file + DB + git happen together or roll back completely
- DocumentStructureManager becomes helper (auto_commit=false when called by GISM)
- Pre-flight checks ensure git working tree is clean
- Checkpoint-based rollback (git reset --hard + DB rollback)

**3. Stateless Validation**
- FeaturePathValidator uses pure functions (no database queries)
- Breaks circular dependencies
- Easy to test and reason about

**4. Per-Project Isolation**
- Features table in each project's `.gao-dev/documents.db` (same DB as epics, stories, etc.)
- Follows Epic 20 architecture (project-scoped tracking)
- Portable project directories

**5. Co-Located Organization**
- Epics contain their stories: `epics/1-epic-name/stories/`
- Intuitive navigation (all Epic 1 materials in one subtree)
- Better querying (find all Epic 1 docs easily)

**6. Context Persistence**
- feature_name stored in WorkflowContext.metadata
- Persists across workflow steps (no need to re-specify)

**7. Integration with Existing Schema**
- `epics.feature` column already exists (line 13 of schema.sql)
- Foreign key relationship will link epics to features
- When creating epic, populate `epics.feature = feature_name`

---

## Component Design

### Component 1: FeatureStateService

**Purpose:** 6th state service for feature metadata management

**NEW COMPONENT** (Follows Epic 24 Service Pattern)

**Current Functionality (Keep As-Is):**
```python
class DocumentStructureManager:
    """Epic 28 implementation - already exists."""

    def __init__(
        self,
        project_root: Path,
        git_manager: GitManager,
        lifecycle_manager: DocumentLifecycleManager
    ):
        self.project_root = project_root
        self.git = git_manager
        self.lifecycle = lifecycle_manager

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel,
        description: Optional[str] = None
    ) -> Path:
        """
        EXISTING: Creates feature folder with scale-level based structure.

        Already creates:
        - docs/features/{feature_name}/
        - PRD.md (template)
        - ARCHITECTURE.md (template)
        - stories/ (folder)
        - epics/ (folder)
        - retrospectives/ (folder, Level 3+)
        - ceremonies/ (folder, Level 4)
        - CHANGELOG.md
        - Git commit
        """
        feature_path = self.project_root / "docs" / "features" / feature_name
        feature_path.mkdir(parents=True, exist_ok=False)

        # Create files and folders (existing logic)
        self._create_file(feature_path / "PRD.md", self._prd_template(...))
        self._create_file(feature_path / "ARCHITECTURE.md", self._arch_template(...))
        (feature_path / "stories").mkdir()
        (feature_path / "epics").mkdir()

        if scale_level >= ScaleLevel.LEVEL_3:
            (feature_path / "retrospectives").mkdir()

        if scale_level == ScaleLevel.LEVEL_4:
            (feature_path / "ceremonies").mkdir()

        # Register with lifecycle manager
        self.lifecycle.register_document(...)

        # Atomic git commit
        self.git.add_all()
        self.git.commit(f"docs({feature_name}): initialize feature folder")

        return feature_path
```

**NEW: Extensions to Add (Story 1.1)**

Add to DocumentStructureManager:

```python
# In initialize_feature_folder(), ADD:

# NEW: QA/ folder (always create)
(feature_path / "QA").mkdir()

# NEW: README.md (generate from template)
readme_content = self._readme_template(feature_name, description)
self._create_file(feature_path / "README.md", readme_content)

# That's it! Git commit already handles new files.
```

**NEW: MVP Support (Story 1.1)**

```python
def initialize_mvp_folder(
    self,
    scale_level: ScaleLevel,
    description: Optional[str] = None
) -> Path:
    """
    NEW: Create MVP folder (greenfield initial scope).

    Wraps initialize_feature_folder() with feature_name="mvp".
    """
    return self.initialize_feature_folder(
        feature_name="mvp",
        scale_level=scale_level,
        description=description
    )
```

**Rationale:** Minimal changes to proven system. QA/ and README.md are simple additions that don't change core logic.

---

### Component 2: FeatureRegistry

**Purpose:** Track feature metadata in per-project database

**NEW COMPONENT**

**Responsibilities:**
- Register features in `.gao-dev/documents.db` (per-project!)
- Query features by scope, status
- Update feature status
- Track feature metadata (owner, dates, description)

**Interface:**
```python
class FeatureRegistry:
    """
    Track feature metadata in per-project database.

    Database location: {project_root}/.gao-dev/documents.db
    Table: features (see Data Models section)
    """

    def __init__(
        self,
        project_root: Path,
        lifecycle_manager: DocumentLifecycleManager
    ):
        """
        Initialize feature registry.

        Args:
            project_root: Project root directory
            lifecycle_manager: Document lifecycle manager (one-way dependency)
        """
        self.project_root = project_root
        self.lifecycle = lifecycle_manager
        self.db_path = project_root / ".gao-dev" / "documents.db"
        self._ensure_features_table()

    def register_feature(
        self,
        name: str,
        scope: FeatureScope,
        scale_level: int,
        description: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Feature:
        """
        Register feature in database.

        Args:
            name: Feature name (e.g., "user-auth", "mvp")
            scope: mvp or feature
            scale_level: 0-4
            description: Optional description
            owner: Optional owner

        Returns:
            Feature object with metadata

        Note: Does NOT create folders (DocumentStructureManager does that)
        """
        feature = Feature(
            name=name,
            scope=scope,
            scale_level=scale_level,
            status=FeatureStatus.PLANNING,
            description=description,
            owner=owner,
            created_at=datetime.now().isoformat()
        )

        # Insert into database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO features (name, scope, scale_level, status,
                                    description, owner, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, scope.value, scale_level, feature.status.value,
                 description, owner, feature.created_at, json.dumps({}))
            )
            feature.id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        return feature

    def get_feature(self, name: str) -> Optional[Feature]:
        """Get feature by name."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM features WHERE name = ?", (name,)
            ).fetchone()

            if row:
                return Feature(
                    id=row[0],
                    name=row[1],
                    scope=FeatureScope(row[2]),
                    status=FeatureStatus(row[3]),
                    scale_level=row[4],
                    description=row[5],
                    owner=row[6],
                    created_at=row[7],
                    completed_at=row[8],
                    metadata=json.loads(row[9] or "{}")
                )
        return None

    def list_features(
        self,
        scope: Optional[FeatureScope] = None,
        status: Optional[FeatureStatus] = None
    ) -> List[Feature]:
        """List features with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM features WHERE 1=1"
            params = []

            if scope:
                query += " AND scope = ?"
                params.append(scope.value)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY created_at DESC"

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_feature(row) for row in rows]

    def update_feature_status(
        self,
        name: str,
        status: FeatureStatus
    ) -> bool:
        """Update feature status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE features SET status = ? WHERE name = ?",
                (status.value, name)
            )
            return conn.total_changes > 0

    def feature_exists(self, name: str) -> bool:
        """Check if feature exists in registry."""
        return self.get_feature(name) is not None
```

**Key Design Decisions:**
1. **Per-project database**: Each project has its own features table (Epic 20 pattern)
2. **One-way dependency**: FeatureRegistry depends on DocumentLifecycleManager (not circular)
3. **Separation of concerns**: Registry tracks metadata, doesn't create folders
4. **scale_level stored**: Allows querying by project scale

---

### Component 3: FeaturePathValidator

**Purpose:** Stateless path validation (breaks circular dependencies)

**NEW COMPONENT**

**Responsibilities:**
- Validate paths match feature structure (pure functions)
- Extract feature name from paths
- No database queries (stateless!)
- No dependencies on FeatureRegistry or DocumentLifecycleManager

**Interface:**
```python
class FeaturePathValidator:
    """
    Stateless validator for feature paths.

    Uses pure functions - no database queries, no dependencies.
    Breaks circular dependency between FeatureRegistry and DocumentLifecycleManager.
    """

    @staticmethod
    def validate_feature_path(path: Path, feature_name: str) -> bool:
        """
        Validate path matches feature pattern.

        Args:
            path: Path to validate
            feature_name: Expected feature name

        Returns:
            True if path matches feature structure

        Example:
            validate_feature_path(
                Path("docs/features/user-auth/PRD.md"),
                "user-auth"
            ) -> True

            validate_feature_path(
                Path("docs/PRD.md"),
                "user-auth"
            ) -> False
        """
        expected_prefix = f"docs/features/{feature_name}/"
        return str(path).replace("\\", "/").startswith(expected_prefix)

    @staticmethod
    def extract_feature_from_path(path: Path) -> Optional[str]:
        """
        Extract feature name from path.

        Args:
            path: Path to extract from

        Returns:
            Feature name or None if not feature-scoped

        Example:
            extract_feature_from_path(
                Path("docs/features/user-auth/PRD.md")
            ) -> "user-auth"

            extract_feature_from_path(
                Path("docs/PRD.md")
            ) -> None
        """
        parts = path.parts
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "features":
            return parts[2]
        return None

    @staticmethod
    def validate_structure(feature_path: Path) -> List[str]:
        """
        Validate feature folder structure.

        Args:
            feature_path: Path to feature folder (e.g., docs/features/user-auth)

        Returns:
            List of violation messages (empty if compliant)

        Checks:
        - Required files exist: PRD.md, ARCHITECTURE.md, README.md
        - Required folders exist: epics/, QA/
        - epics/ is a folder (not epics.md file)
        """
        violations = []

        # Check required files
        for required_file in ["PRD.md", "ARCHITECTURE.md", "README.md"]:
            if not (feature_path / required_file).exists():
                violations.append(f"Missing required file: {required_file}")

        # Check required folders
        for required_folder in ["epics", "QA"]:
            folder_path = feature_path / required_folder
            if not folder_path.exists():
                violations.append(f"Missing required folder: {required_folder}/")
            elif not folder_path.is_dir():
                violations.append(
                    f"{required_folder} is a file, should be a folder"
                )

        # Check for old patterns
        if (feature_path / "epics.md").exists():
            violations.append(
                "Using old epics.md format (should be epics/ folder)"
            )

        return violations
```

**Key Design Decision:** Stateless validator uses pure functions. DocumentLifecycleManager can use it without creating circular dependency.

---

### Component 4: FeaturePathResolver

**Purpose:** Resolve `{{feature_name}}` variable with intelligent auto-detection

**NEW COMPONENT**

**Responsibilities:**
- Resolve feature_name from multiple sources (6-level priority)
- Integrate with WorkflowContext (use metadata.feature_name)
- Generate feature-scoped paths for all document types
- Support cross-feature references

**Interface:**
```python
class FeaturePathResolver:
    """
    Resolve feature names and generate feature-scoped paths.

    Integrates with WorkflowExecutor to provide feature_name
    variable resolution.
    """

    def __init__(
        self,
        project_root: Path,
        feature_registry: FeatureRegistry
    ):
        self.project_root = project_root
        self.features_dir = project_root / "docs" / "features"
        self.registry = feature_registry

    def resolve_feature_name(
        self,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None
    ) -> str:
        """
        Resolve feature name from multiple sources.

        Priority (highest to lowest):
        1. Explicit parameter: params["feature_name"]
        2. WorkflowContext: context.feature_name (NEW!)
        3. Current working directory (if in feature folder)
        4. Single feature detection (if only one besides mvp)
        5. MVP detection (if mvp/ exists and no other features)
        6. Error (if ambiguous)

        Args:
            params: Workflow parameters
            context: Optional WorkflowContext

        Returns:
            Feature name (e.g., "mvp", "user-auth")

        Raises:
            ValueError: If feature_name cannot be resolved
        """
        # 1. Explicit parameter (highest priority)
        if "feature_name" in params:
            name = params["feature_name"]
            if not self.registry.feature_exists(name):
                raise ValueError(
                    f"Feature '{name}' does not exist. "
                    f"Available: {self._list_feature_names()}"
                )
            return name

        # 2. WorkflowContext (NEW!)
        if context and context.feature_name:
            return context.feature_name

        # 3. Current working directory
        cwd = Path.cwd()
        if cwd.is_relative_to(self.features_dir):
            relative = cwd.relative_to(self.features_dir)
            feature_name = relative.parts[0] if relative.parts else None
            if feature_name and self.registry.feature_exists(feature_name):
                return feature_name

        # 4. Single feature detection
        features = self._list_feature_names(exclude_mvp=True)
        if len(features) == 1:
            return features[0]

        # 5. MVP detection
        if self.registry.feature_exists("mvp") and len(features) == 0:
            return "mvp"

        # 6. Error (ambiguous)
        raise ValueError(
            "Cannot resolve feature_name. Multiple features exist:\n"
            f"{', '.join(features)}\n\n"
            "Please specify explicitly:\n"
            "  --feature-name <name>\n"
            "Or run from feature directory:\n"
            "  cd docs/features/<name> && gao-dev <command>"
        )

    def generate_feature_path(
        self,
        feature_name: str,
        path_type: str,
        epic: Optional[str] = None,
        epic_name: Optional[str] = None,
        story: Optional[str] = None
    ) -> Path:
        """
        Generate feature-scoped path using co-located structure.

        Args:
            feature_name: Feature name (e.g., "user-auth")
            path_type: Path type (prd, epic_location, story_location, etc.)
            epic: Epic number (e.g., "1")
            epic_name: Epic name (e.g., "foundation")
            story: Story number (e.g., "1")

        Returns:
            Path relative to project root

        Examples:
            generate_feature_path("user-auth", "prd")
            -> Path("docs/features/user-auth/PRD.md")

            generate_feature_path("user-auth", "epic_location",
                                epic="1", epic_name="foundation")
            -> Path("docs/features/user-auth/epics/1-foundation/README.md")

            generate_feature_path("user-auth", "story_location",
                                epic="1", epic_name="foundation", story="2")
            -> Path("docs/features/user-auth/epics/1-foundation/stories/story-1.2.md")
        """
        # Co-located path templates (v2.0)
        templates = {
            # Feature-level documents
            "prd": "docs/features/{feature_name}/PRD.md",
            "architecture": "docs/features/{feature_name}/ARCHITECTURE.md",
            "readme": "docs/features/{feature_name}/README.md",
            "epics_overview": "docs/features/{feature_name}/EPICS.md",

            # Feature-level folders
            "qa_folder": "docs/features/{feature_name}/QA",
            "retrospectives_folder": "docs/features/{feature_name}/retrospectives",

            # Epic-level (co-located with stories!)
            "epic_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}",
            "epic_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/README.md",

            # Story-level (inside epic folder!)
            "story_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories",
            "story_location": "docs/features/{feature_name}/epics/{epic}-{epic_name}/stories/story-{epic}.{story}.md",
            "context_xml_folder": "docs/features/{feature_name}/epics/{epic}-{epic_name}/context",

            # Ceremony artifacts
            "retrospective_location": "docs/features/{feature_name}/retrospectives/epic-{epic}-retro.md",
            "standup_location": "docs/features/{feature_name}/standups/standup-{date}.md",

            # Legacy
            "feature_dir": "docs/features/{feature_name}"
        }

        template = templates.get(path_type)
        if not template:
            raise ValueError(f"Unknown path_type: {path_type}")

        return Path(template.format(
            feature_name=feature_name,
            epic=epic or "",
            epic_name=epic_name or "",
            story=story or "",
            date=datetime.now().strftime("%Y-%m-%d")
        ))
```

**Key Design Decisions:**
1. **WorkflowContext integration**: Checks context.feature_name (priority 2)
2. **Co-located paths**: Epics contain their stories (improved from v1.0)
3. **Comprehensive templates**: All path types defined in one place
4. **Clear error messages**: Helpful guidance when resolution fails

---

## Data Models

### Feature Model

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

class FeatureScope(Enum):
    """Feature scope: MVP or subsequent feature."""
    MVP = "mvp"
    FEATURE = "feature"

class FeatureStatus(Enum):
    """Feature lifecycle status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETE = "complete"
    ARCHIVED = "archived"

@dataclass
class Feature:
    """
    Feature metadata model.

    Stored in per-project database: .gao-dev/documents.db
    """
    id: Optional[int] = None
    name: str = ""
    scope: FeatureScope = FeatureScope.FEATURE
    status: FeatureStatus = FeatureStatus.PLANNING
    scale_level: int = 0  # NEW: 0-4 scale level
    description: Optional[str] = None
    owner: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Database Schema (Per-Project!)

```sql
-- Location: {project_root}/.gao-dev/documents.db
-- Each project has its own features table

CREATE TABLE features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
    scale_level INTEGER NOT NULL,  -- 0-4
    description TEXT,
    owner TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    metadata JSON
);

CREATE INDEX idx_features_scope ON features(scope);
CREATE INDEX idx_features_status ON features(status);
CREATE INDEX idx_features_scale_level ON features(scale_level);
```

**Example:**
```
sandbox/projects/todo-app/.gao-dev/documents.db
  └── features table (contains todo-app features)

sandbox/projects/blog-app/.gao-dev/documents.db
  └── features table (contains blog-app features)
```

---

## Integration Points

### Integration 1: WorkflowContext (Epic 18)

**Purpose:** Persist feature_name across workflow steps

**Changes Required:**

**Add Property to WorkflowContext:**
```python
@dataclass
class WorkflowContext:
    initial_prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def feature_name(self) -> Optional[str]:
        """
        Get feature name from metadata.

        Allows feature_name to persist across workflow steps.
        """
        return self.metadata.get("feature_name")
```

**Usage:**
```python
# Create context once with feature_name
context = WorkflowContext(
    initial_prompt="Create user auth",
    metadata={"feature_name": "user-auth"}
)

# Feature persists across all steps!
execute_workflow("prd", params={}, context=context)
execute_workflow("architecture", params={}, context=context)
execute_workflow("create-stories", params={}, context=context)
# No need to re-specify feature_name in each step!
```

---

### Integration 2: WorkflowExecutor (Epic 18)

**Purpose:** Integrate FeaturePathResolver into variable resolution

**Changes Required:**

**Extend WorkflowExecutor.resolve_variables():**
```python
class WorkflowExecutor:
    def __init__(self, ...):
        # ... existing init ...
        self.feature_resolver = FeaturePathResolver(project_root, feature_registry)

    def resolve_variables(
        self,
        workflow: Workflow,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None  # NEW parameter
    ) -> Dict[str, Any]:
        """
        Resolve variables with feature_name support.

        Priority:
        1. params (explicit parameters)
        2. workflow.variables (workflow defaults)
        3. config defaults (global defaults.yaml)
        4. common variables (date, timestamp, etc.)
        5. feature_name resolution (auto-detect) <- NEW!
        """
        resolved = {}

        # ... existing resolution logic ...

        # NEW: Resolve feature_name if not provided
        if "feature_name" not in resolved:
            try:
                resolved["feature_name"] = self.feature_resolver.resolve_feature_name(
                    params=resolved,
                    context=context  # Pass context!
                )
            except ValueError as e:
                # feature_name required but can't resolve
                if self._workflow_requires_feature_name(workflow):
                    raise ValueError(
                        f"Workflow '{workflow.name}' requires feature_name but cannot resolve.\n"
                        f"{str(e)}"
                    )
                # Otherwise, use legacy paths (backward compatibility)
                logger.warning("feature_name not resolved, using legacy paths")

        return resolved
```

---

### Integration 3: DocumentLifecycleManager (Epic 20)

**Purpose:** Use FeaturePathValidator for path validation

**Changes Required:**

**Extend DocumentLifecycleManager:**
```python
class DocumentLifecycleManager:
    def __init__(self, ...):
        # ... existing init ...
        self.validator = FeaturePathValidator()  # NEW: Stateless validator

    def register_document(
        self,
        path: Path,
        doc_type: str,
        author: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Register document with feature metadata.

        Now extracts feature_name and validates structure.
        """
        # Extract feature_name using stateless validator
        feature_name = self.validator.extract_feature_from_path(path)

        # Validate path if feature-scoped
        if feature_name:
            is_valid = self.validator.validate_feature_path(path, feature_name)
            if not is_valid:
                logger.warning(
                    f"Document path does not match feature structure: {path}"
                )

        # Add feature_name to metadata
        metadata = metadata or {}
        metadata["feature_name"] = feature_name
        metadata["scope"] = "mvp" if feature_name == "mvp" else "feature"

        # Register document (existing logic)
        return super().register_document(path, doc_type, author, metadata)
```

**Key Insight:** One-way dependency. DocumentLifecycleManager uses stateless validator, no circular dependency.

---

### Integration 4: Variable Defaults (Epic 18)

**Purpose:** Update defaults.yaml with co-located paths

**Changes Required:**

**Update gao_dev/config/defaults.yaml:**
```yaml
workflow_defaults:
  # Feature-level documents
  prd_location: "docs/features/{{feature_name}}/PRD.md"
  architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
  readme_location: "docs/features/{{feature_name}}/README.md"
  epics_overview: "docs/features/{{feature_name}}/EPICS.md"

  # Feature-level folders
  qa_folder: "docs/features/{{feature_name}}/QA"
  retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"

  # Epic-level (CO-LOCATED with stories!)
  epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
  epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"

  # Story-level (INSIDE epic folder!)
  story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"
  story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"
  context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"

  # Ceremony artifacts
  retrospective_location: "docs/features/{{feature_name}}/retrospectives/epic-{{epic}}-retro.md"
  standup_location: "docs/features/{{feature_name}}/standups/standup-{{date}}.md"

  # LEGACY: Backward compatibility (remove after migration)
  legacy_prd_location: "docs/PRD.md"
  legacy_architecture_location: "docs/ARCHITECTURE.md"
  legacy_epic_location: "docs/epics.md"
```

**Breaking Change:** OK per user ("this project is still in early developmental phase")

---

## Directory Structure

### Co-Located Epic-Story Structure (v2.0)

```
docs/features/
  ├── mvp/                              ← Greenfield initial scope
  │   ├── PRD.md
  │   ├── ARCHITECTURE.md
  │   ├── README.md
  │   ├── EPICS.md                      ← Master epic overview
  │   │
  │   ├── epics/                        ← Epic containers (CO-LOCATED!)
  │   │   ├── 1-foundation/            ← Epic 1 (number + name)
  │   │   │   ├── README.md            ← Epic definition
  │   │   │   ├── stories/             ← Stories for Epic 1
  │   │   │   │   ├── story-1.1.md
  │   │   │   │   └── story-1.2.md
  │   │   │   └── context/             ← Context XML for Epic 1
  │   │   │       └── story-1.1.xml
  │   │   │
  │   │   └── 2-advanced-features/     ← Epic 2
  │   │       ├── README.md
  │   │       └── stories/
  │   │           ├── story-2.1.md
  │   │           └── story-2.2.md
  │   │
  │   ├── QA/                          ← QA artifacts
  │   └── retrospectives/              ← Retrospectives
  │
  └── user-auth/                       ← Feature example
      ├── PRD.md
      ├── ARCHITECTURE.md
      ├── README.md
      ├── EPICS.md
      │
      ├── epics/                       ← Co-located structure
      │   └── 1-oauth-integration/
      │       ├── README.md
      │       └── stories/
      │           └── story-1.1.md
      │
      ├── QA/
      └── retrospectives/
```

**Key Benefits:**
1. **Intuitive Navigation**: All Epic 1 materials in `epics/1-foundation/`
2. **Logical Grouping**: Epic definition + stories together
3. **Better Querying**: Find all Epic 1 docs easily (single subtree)
4. **Consistent Pattern**: Same structure for MVP and features

---

## Implementation Details

### Revised Epic Breakdown (v3.0 - State Management Integration)

**Total: 3 epics, 11 stories, 25 points, 2 weeks**
**Epic Numbers: 32-34** (after Epic 31: Mary Integration)

**See:** `ARCHITECTURE_V3_STATE_INTEGRATION.md` for complete component specifications and rationale.

### Epic 32: State Service Integration (Week 1) - 10 points

**Story 32.1: Create FeatureStateService (3 pts)**
- Implement FeatureStateService following Epic 24 pattern
- Thread-safe connections, <5ms queries
- CRUD operations: create, get, list, update_status, delete
- Unit tests (30+ assertions)

**Story 32.2: Extend StateCoordinator (2 pts)**
- Add feature_service to StateCoordinator.__init__()
- Add facade methods: create_feature, get_feature, list_features
- Add get_feature_state() comprehensive query
- Unit tests (15+ assertions)

**Story 32.3: Create FeaturePathValidator (2 pts)**
- Implement stateless validator (pure functions)
- validate_feature_path(), extract_feature_from_path(), validate_structure()
- Unit tests (25+ assertions)

**Story 32.4: Create FeaturePathResolver (3 pts)**
- Implement resolver with 6-level priority
- WorkflowContext integration (metadata.feature_name)
- Co-located path generation
- Unit tests (40+ assertions)

### Epic 33: Atomic Feature Operations (Week 1.5) - 8 points

**Story 33.1: Extend DocumentStructureManager (2 pts)**
- Add QA/ folder creation
- Add README.md generation with template
- Add auto_commit parameter (default: true, backward compatible)
- Unit tests (20+ assertions)

**Story 33.2: Extend GitIntegratedStateManager (4 pts)**
- Add create_feature() method following atomic pattern
- Pre-flight checks, checkpoint, rollback logic
- Integrate DocumentStructureManager (auto_commit=false) + StateCoordinator
- Unit tests (50+ assertions)
- Integration tests (15+ scenarios)

**Story 33.3: CLI Commands (2 pts)**
- create-feature command (wraps GitIntegratedStateManager)
- list-features command (wraps StateCoordinator)
- validate-structure command (wraps FeaturePathValidator)
- CLI tests (20+ scenarios)

### Epic 34: Integration & Variables (Week 2) - 7 points

**Story 34.1: Schema Migration (2 pts)**
- Create migration script for features table
- Add triggers for timestamps and audit trail
- Migration tests (validate existing DB schemas)
- Documentation

**Story 34.2: Update defaults.yaml (2 pts)**
- Replace all paths with co-located structure
- Update variable defaults (feature_name, epic_folder, story_location, etc.)
- Validation tests

**Story 34.3: WorkflowExecutor Integration (2 pts)**
- Extend resolve_variables() to use FeaturePathResolver
- Pass WorkflowContext to resolver
- Fallback logic for legacy paths
- Integration tests (15+ cases)

**Story 34.4: Testing & Documentation (1 pt)**
- End-to-end tests (greenfield, feature creation, validation)
- Update CLAUDE.md with new commands
- Migration guide for existing features
- CLI help text updates

---

## Migration Strategy

### Gradual Adoption (Recommended)

**Phase 1: Implementation (Week 1-2)**
- Build all components
- Test thoroughly
- Ready for production use

**Phase 2: New Features (Immediate)**
- All new features use `gao-dev create-feature`
- Automatic compliance enforcement
- Co-located structure by default

**Phase 3: Existing Features (Gradual)**
- Optional migration via `gao-dev migrate-feature` (future story)
- No deadline, no breaking changes
- Existing features continue working (legacy paths)

**Backward Compatibility:**
```python
# Variable resolution with fallback
if "feature_name" in resolved:
    # Use feature-scoped path
    prd_location = f"docs/features/{resolved['feature_name']}/PRD.md"
else:
    # Fallback to legacy path (existing features still work!)
    prd_location = "docs/PRD.md"
```

---

## Performance Considerations

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| `create-feature` | <1s | Wraps DocumentStructureManager (already fast) |
| `validate-structure` (single) | <100ms | Stateless validation (file system checks only) |
| `list-features` | <50ms | Database query with indexes |
| `feature_name` resolution | <10ms | Priority logic with caching |

### Optimization Strategies

**1. Stateless Validation**
- FeaturePathValidator uses pure functions (no DB queries)
- Fast file system checks only

**2. Database Indexes**
- Index on features.name (unique)
- Index on features.scope, features.status, features.scale_level

**3. Caching**
- Cache feature list (TTL: 5 minutes)
- Cache resolved paths during workflow execution

---

## Security & Validation

### Input Validation

**Feature Name Validation:**
```python
# Must be kebab-case
pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'

# Examples:
# ✓ user-auth
# ✓ payment-processing
# ✓ analytics-dashboard
# ✗ UserAuth (uppercase)
# ✗ user_auth (underscores)
# ✗ user auth (spaces)
```

**Path Traversal Prevention:**
```python
def validate_path(path: Path) -> None:
    """Prevent path traversal attacks."""
    resolved = path.resolve()
    if not resolved.is_relative_to(project_root):
        raise ValueError(f"Path outside project root: {path}")
```

**SQL Injection Prevention:**
- Use parameterized queries (sqlite3 placeholders)
- Never concatenate user input into SQL

---

## Open Questions & Decisions

### Decision 1: Breaking Changes

**Question:** Should we replace existing variable paths or grandfather?

**Decision:** Replace (user approved: "OK it's fine for this to be a breaking change")

**Rationale:** Early development phase, cleaner long-term

---

### Decision 2: Epic Folder Naming

**Question:** `epics/1/` or `epics/1-epic-name/`?

**Decision:** `epics/1-epic-name/` (number + name for readability)

**Rationale:** More intuitive, GitHub displays folder names clearly

---

### Decision 3: Epic Definition File

**Question:** `epics/1-epic-name/epic.md` or `README.md`?

**Decision:** `README.md`

**Rationale:** Auto-displays on GitHub when browsing folder

---

## Summary of Changes: v1.0 → v2.0 → v3.0

| Aspect | v1.0 (REJECTED) | v2.0 (SUPERSEDED) | v3.0 (APPROVED) |
|--------|-----------------|-------------------|-----------------|
| **Approach** | Create new FeatureManager | Extend DocumentStructureManager | FeatureStateService (6th service) |
| **Atomicity** | Not specified | DocumentStructureManager + FeatureRegistry (non-atomic) | GitIntegratedStateManager (atomic) |
| **Pattern** | New standalone | Extension pattern | Epic 24-27 service pattern |
| **Scope** | 5 epics, 40 points, 4 weeks | 3 epics, 25 points, 2 weeks | 3 epics, 25 points, 2 weeks |
| **Epic Numbers** | 1-5 | 1-3 | 32-34 (correct sequencing) |
| **Epic-Story** | Separated (epics/, stories/) | Co-located (epics/1-name/stories/) | Co-located (epics/1-name/stories/) |
| **Validator** | FeatureManager (stateful) | FeaturePathValidator (stateless) | FeaturePathValidator (stateless) |
| **Database** | Ambiguous (global?) | Per-project (.gao-dev/documents.db) | Per-project (.gao-dev/documents.db) |
| **StateCoordinator** | Not integrated | Not integrated | Add feature_service facade |
| **WorkflowContext** | Not integrated | feature_name in metadata | feature_name in metadata |
| **Variables** | epic_location (ambiguous) | Clear naming (_overview, _folder, _location) | Clear naming (_overview, _folder, _location) |
| **Git Integration** | Not specified | Reuses Epic 28's GitManager | GitIntegratedStateManager (atomic) |
| **DocumentStructureManager** | Create new | Extend (standalone) | Helper with auto_commit parameter |

### Key Decision: v2.0 → v3.0

**Critical Discovery:** The `epics.feature` column already exists in `gao_dev/core/state/schema.sql` (line 13), and the state management system (Epics 24-27) provides atomic operations via GitIntegratedStateManager.

**Decision:** Follow the proven state service pattern rather than creating standalone components.

**Benefits of v3.0:**
1. ✅ **Consistency**: Follows exact same pattern as 5 existing services
2. ✅ **Atomicity**: Guaranteed file + DB + git atomic or rollback
3. ✅ **Integration**: Leverages existing StateCoordinator and GitIntegratedStateManager
4. ✅ **Performance**: <5ms queries, thread-safe, indexed
5. ✅ **Single Responsibility**: Each component has clear, focused role

**See:** `ARCHITECTURE_V3_STATE_INTEGRATION.md` for complete specifications.

---

*End of Architecture Document v3.0*
