# Critical Issues - Fixes Summary

**Date:** 2025-11-11
**Status:** All 7 Criticals Resolved ✅
**Next Step:** Update PRD v2.0 and ARCHITECTURE v2.0

---

## Executive Summary

All **7 CRITICAL issues** identified in the critical analysis have been resolved through collaborative review. The key insight: this feature **extends** Epic 28's DocumentStructureManager rather than replacing it.

**Scope Reduction:** From 5 epics (40 points, 4 weeks) → **3 epics (25 points, 2 weeks)**

---

## CRITICAL-1: DocumentStructureManager Already Exists ✅ FIXED

### Problem
PRD/ARCHITECTURE proposed creating FeatureManager, StructureValidator, and template system - but DocumentStructureManager (Epic 28) already does 70% of this!

### Solution: EXTEND, Don't Replace

**Keep Existing:**
- `DocumentStructureManager.initialize_feature_folder()` - Creates folders/templates
- Git integration via GitManager
- DocumentLifecycleManager integration
- Scale-level based structure

**Add New:**
- `FeatureRegistry` - Track feature metadata in database
- `FeatureValidator` - Validate structure compliance
- CLI commands - Wrap existing DocumentStructureManager
- Missing pieces: QA/, README.md, MVP concept integration

### Impact
- ✅ Reuses 70% existing code
- ✅ Lower risk (proven system)
- ✅ Faster implementation (2 weeks vs 4 weeks)
- ✅ Maintains Epic 28 compatibility

---

## CRITICAL-2: Missing Git Integration ✅ FIXED

### Problem
PRD didn't specify git commits for create-feature, migrate-feature commands.

### Solution: Already Solved!

DocumentStructureManager **already has** full git integration:
```python
def __init__(self, ..., git_manager: GitManager):
    self.git = git_manager

def initialize_feature_folder(self, ...):
    # ... creates files ...
    self.git.add_all()
    self.git.commit(f"docs({feature_name}): initialize feature folder")
```

**What we need:**
- Ensure CLI commands use DocumentStructureManager (inherits git)
- Ensure FeatureValidator is read-only (no git needed)
- Ensure FeatureRegistry updates included in commits

### Impact
- ✅ Atomic commits already implemented
- ✅ Conventional commit format already used
- ✅ Auto-rollback via Epic 27 transaction model

---

## CRITICAL-3: Missing Story-Level Path Variables ✅ FIXED

### Problem
PRD defined feature-level paths but missing:
- Individual story file paths
- Individual epic file paths
- Context XML folder paths
- Separated epics from stories (bad design)

### Solution: Co-Located Epic-Story Structure

**Key Insight (from user):** Epics and stories should be **co-located** - an epic contains its stories!

**New Structure:**
```
docs/features/{feature-name}/
  ├── PRD.md
  ├── ARCHITECTURE.md
  ├── README.md
  ├── EPICS.md                           # Master epic overview
  │
  ├── epics/                             # Epic containers
  │   ├── 1-epic-name/                   # Epic 1 (number + name)
  │   │   ├── README.md                  # Epic definition
  │   │   ├── stories/                   # Stories for this epic
  │   │   │   ├── story-1.1.md
  │   │   │   └── story-1.2.md
  │   │   └── context/                   # Context XML
  │   │       └── story-1.1.xml
  │   └── 2-another-epic/
  │       ├── README.md
  │       └── stories/
  │
  ├── QA/
  └── retrospectives/
```

**Complete Variable Paths:**
```yaml
workflow_defaults:
  # Feature-level
  prd_location: "docs/features/{{feature_name}}/PRD.md"
  architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
  readme_location: "docs/features/{{feature_name}}/README.md"
  epics_overview: "docs/features/{{feature_name}}/EPICS.md"
  qa_folder: "docs/features/{{feature_name}}/QA"
  retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"

  # Epic-level (co-located!)
  epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
  epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"

  # Story-level (inside epic!)
  story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"
  story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"
  context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"
```

### Design Decisions
1. **Epic folder naming:** `epics/1-epic-name/` (number + name for readability)
2. **Epic definition:** `README.md` (auto-displays on GitHub)
3. **Stories location:** `stories/` subfolder (cleaner with many stories)

### Impact
- ✅ Logical grouping (epic + stories together)
- ✅ Intuitive navigation
- ✅ Better querying (all Epic 1 docs in one subtree)
- ✅ Complete variable coverage

---

## CRITICAL-4: Per-Project vs. Global Registry ✅ FIXED

### Problem
Ambiguous whether `features` table goes in:
- Per-project `.gao-dev/documents.db` (correct)
- Global GAO-Dev database (wrong)

### Solution: Per-Project (Epic 20 Architecture)

Epic 20 already established: **Each project has its own `.gao-dev/documents.db`**

```
sandbox/projects/todo-app/.gao-dev/
  └── documents.db
      ├── documents table
      └── features table       ← Features for todo-app

sandbox/projects/blog-app/.gao-dev/
  └── documents.db
      ├── documents table
      └── features table       ← Features for blog-app
```

**Database Schema (per-project):**
```sql
-- In EACH project's .gao-dev/documents.db

CREATE TABLE features (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,      -- Unique PER PROJECT
    scope TEXT NOT NULL CHECK(scope IN ('mvp', 'feature')),
    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'complete', 'archived')),
    scale_level INTEGER,            -- 0-4
    created_at TEXT NOT NULL,
    completed_at TEXT,
    description TEXT,
    owner TEXT,
    metadata JSON
);
```

**FeatureRegistry Implementation:**
```python
class FeatureRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / ".gao-dev" / "documents.db"  # ← Per-project!
```

### Impact
- ✅ Multi-project isolation
- ✅ Portable project directories
- ✅ Consistent with Epic 20 architecture

---

## CRITICAL-5: Circular Dependency ✅ FIXED

### Problem
Circular dependency between components:
```
FeatureManager needs DocumentLifecycleManager
  → to register documents

DocumentLifecycleManager needs FeatureManager
  → to validate feature paths
```

### Solution: Stateless FeaturePathValidator

Break cycle by making path validation **stateless** (no database queries):

```python
class FeaturePathValidator:
    """Stateless validator - no dependencies."""

    @staticmethod
    def validate_feature_path(path: Path, feature_name: str) -> bool:
        """Pure function - validates path matches pattern."""
        expected = f"docs/features/{feature_name}/"
        return str(path).startswith(expected)

    @staticmethod
    def extract_feature_from_path(path: Path) -> Optional[str]:
        """Extract feature name from path."""
        parts = path.parts
        if len(parts) >= 3 and parts[0] == "docs" and parts[1] == "features":
            return parts[2]
        return None

class DocumentLifecycleManager:
    def __init__(self):
        self.validator = FeaturePathValidator()  # ← No circular dependency!

    def register_document(self, path: Path, ...):
        feature_name = self.validator.extract_feature_from_path(path)
        if feature_name:
            self.validator.validate_feature_path(path, feature_name)

class FeatureRegistry:
    def __init__(self, project_root: Path, lifecycle: DocumentLifecycleManager):
        self.lifecycle = lifecycle  # ← One-way dependency only!
```

**Key Insight:** Path validation doesn't need database - it just validates the **pattern**.

### Impact
- ✅ No circular dependencies
- ✅ Easy to initialize both classes
- ✅ Stateless validator = easy to test

---

## CRITICAL-6: Variable Naming Inconsistency ✅ FIXED

### Problem
Confusion between `epic_location` (file or folder?) and `epic_folder`

### Solution: Clear Naming Convention

**Rules:**
- `_overview` = master/index file
- `_folder` = directory path
- `_location` = specific file path

**Applied:**
```yaml
# CLEAR NAMING:
epics_overview: "docs/features/{{feature_name}}/EPICS.md"           # Master list (file)
epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"  # Directory
epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"  # Epic file
```

**REMOVED (ambiguous):**
```yaml
epic_location: "docs/epics.md"  # Single file? Folder? Unclear!
```

### Impact
- ✅ Clear, consistent naming
- ✅ No ambiguity
- ✅ Easy to understand variable purpose

---

## CRITICAL-7: WorkflowContext Integration ✅ FIXED

### Problem
Multi-step workflows lose feature context:
```python
# Step 1: Create PRD
execute_workflow("prd", {"feature_name": "user-auth"})

# Step 2: Create Architecture
# Problem: feature_name lost! Must re-specify
execute_workflow("architecture", {"feature_name": "user-auth"})  # ← Redundant!
```

### Solution: Store feature_name in WorkflowContext

WorkflowContext already has flexible `metadata` dict - use it!

**Add Property:**
```python
@dataclass
class WorkflowContext:
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def feature_name(self) -> Optional[str]:
        """Get feature name from metadata."""
        return self.metadata.get("feature_name")
```

**Updated Resolution Priority:**
```python
class FeaturePathResolver:
    def resolve_feature_name(
        self,
        params: Dict[str, Any],
        context: Optional[WorkflowContext] = None  # ← Add parameter
    ) -> str:
        """
        Priority:
        1. Explicit parameter: params["feature_name"]
        2. WorkflowContext: context.feature_name  ← NEW!
        3. Current working directory
        4. Single feature detection
        5. MVP detection
        6. Error
        """
        if "feature_name" in params:
            return params["feature_name"]

        if context and context.feature_name:  # ← NEW!
            return context.feature_name

        # ... rest of logic ...
```

**Usage:**
```python
# Create context once
context = WorkflowContext(
    initial_prompt="Create user auth",
    metadata={"feature_name": "user-auth"}
)

# Feature persists across all steps!
execute_workflow("prd", params={}, context=context)
execute_workflow("architecture", params={}, context=context)
execute_workflow("create-stories", params={}, context=context)
```

### Impact
- ✅ Feature name persists across workflow steps
- ✅ No need to re-specify in each step
- ✅ Cleaner API

---

## Updated Architecture Summary

### What We're Building (Revised)

**Extend Existing (Epic 28):**
```python
class DocumentStructureManager:
    # Already exists - ADD TO IT:
    def initialize_feature_folder(self, ...):
        # ADD: (feature_path / "QA").mkdir()
        # ADD: self._create_file(feature_path / "README.md", template)
```

**Add New:**
```python
class FeatureRegistry:
    """Track feature metadata in per-project database."""
    def register_feature(self, name, scope, scale_level): pass
    def list_features(self): pass
    def get_feature(self, name): pass

class FeaturePathValidator:
    """Stateless path validation."""
    @staticmethod
    def validate_feature_path(path, feature_name): pass
    @staticmethod
    def extract_feature_from_path(path): pass

class FeaturePathResolver:
    """Resolve feature_name variable."""
    def resolve_feature_name(self, params, context): pass
    def generate_feature_path(self, feature_name, path_type): pass
```

**Add CLI Commands:**
```bash
gao-dev create-feature <name> --scale-level 3
  → Wraps DocumentStructureManager.initialize_feature_folder()
  → Wraps FeatureRegistry.register_feature()

gao-dev validate-structure [--feature <name>]
  → Uses FeaturePathValidator

gao-dev list-features
  → Uses FeatureRegistry.list_features()
```

---

## Revised Epic Breakdown

### Epic 1: Foundation (Week 1) - 10 points
1. Story 1.1: Add QA/ and README.md to DocumentStructureManager (3 pts)
2. Story 1.2: Create FeatureRegistry with database schema (3 pts)
3. Story 1.3: Create FeaturePathValidator (stateless) (2 pts)
4. Story 1.4: Create FeaturePathResolver with WorkflowContext integration (2 pts)

### Epic 2: CLI Commands (Week 1.5) - 8 points
1. Story 2.1: create-feature command (wraps existing) (3 pts)
2. Story 2.2: validate-structure command (2 pts)
3. Story 2.3: list-features command (1 pt)
4. Story 2.4: Update init command for MVP (2 pts)

### Epic 3: Integration & Variable Updates (Week 2) - 7 points
1. Story 3.1: Update defaults.yaml with co-located paths (2 pts)
2. Story 3.2: Integrate with WorkflowExecutor (2 pts)
3. Story 3.3: Update DocumentLifecycleManager integration (1 pt)
4. Story 3.4: Testing & Documentation (2 pts)

**Total: 3 epics, 11 stories, 25 points, 2 weeks**

---

## Key Decisions Made

1. ✅ **Extend, don't replace** DocumentStructureManager
2. ✅ **Co-located epic-story structure** (epics contain their stories)
3. ✅ **Per-project features table** (follows Epic 20)
4. ✅ **Stateless validator** (breaks circular dependency)
5. ✅ **Clear variable naming** (_overview, _folder, _location)
6. ✅ **WorkflowContext for persistence** (use metadata dict)
7. ✅ **Breaking change acceptable** (early development phase)

---

## Next Steps

1. ✅ All criticals resolved
2. ⏳ Update PRD.md v2.0 (reflect extension approach, co-located structure)
3. ⏳ Update ARCHITECTURE.md v2.0 (reflect new components, simplified scope)
4. ⏳ Create epic files (3 epics in epics/ folder)
5. ⏳ Create story files (11 stories across 3 epics)
6. ⏳ Begin implementation

---

*End of Fixes Summary*
