---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 33
  story: 1
  feature: "feature-based-document-structure"
  points: 2
---

# Story 33.1: Extend DocumentStructureManager (2 points)

**Epic:** 33 - Atomic Feature Operations
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **DocumentStructureManager (Epic 28 component)**,
I want **to create QA/ folder, generate README.md, and support auto_commit parameter**,
So that **feature folders have complete structure and can be called by GitIntegratedStateManager without double-committing**.

## Acceptance Criteria

### AC1: Add QA/ Folder Creation
- [ ] Modify `initialize_feature_folder()` to create QA/ folder
- [ ] QA/ folder created for all scale levels (Level 2+)
- [ ] QA/ folder included in git commit
- [ ] Backward compatible (existing functionality preserved)

### AC2: Add README.md Generation
- [ ] Create Jinja2 template for README.md at `gao_dev/config/prompts/feature/README.md.j2`
- [ ] Template includes sections: Overview, Documents, Epics, Stories, QA, Retrospectives
- [ ] Generate README.md with feature metadata (name, description, scale_level)
- [ ] README.md committed with other files

### AC3: Add auto_commit Parameter
- [ ] Add `auto_commit: bool = True` parameter to `initialize_feature_folder()`
- [ ] When `auto_commit=True`: Commit to git (default, backward compatible)
- [ ] When `auto_commit=False`: Skip git commit (for GitIntegratedStateManager)
- [ ] Return feature_path in both cases

### AC4: Maintain Backward Compatibility
- [ ] All existing callers continue working (auto_commit defaults to True)
- [ ] Git commit message format unchanged
- [ ] DocumentLifecycleManager integration unchanged
- [ ] No breaking changes to Epic 28 functionality

### AC5: Testing
- [ ] 20+ unit test assertions covering:
  - QA/ folder created
  - README.md generated with correct content
  - auto_commit=True commits to git
  - auto_commit=False skips commit
  - Backward compatibility (existing tests pass)

## Technical Notes

### Implementation Approach

**Extend DocumentStructureManager (gao_dev/core/services/document_structure_manager.py):**

```python
# Location: gao_dev/core/services/document_structure_manager.py (lines ~69-200)

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class DocumentStructureManager:
    """
    Manage feature folder initialization (Epic 28).

    ENHANCEMENTS (Story 33.1):
    - Create QA/ folder
    - Generate README.md from template
    - Support auto_commit parameter for GitIntegratedStateManager integration
    """

    def __init__(
        self,
        project_root: Path,
        git_manager: GitManager,
        lifecycle_manager: DocumentLifecycleManager
    ):
        self.project_root = project_root
        self.git = git_manager
        self.lifecycle = lifecycle_manager

        # NEW: Jinja2 environment for templates
        template_dir = Path(__file__).parent.parent / "config" / "prompts" / "feature"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def initialize_feature_folder(
        self,
        feature_name: str,
        scale_level: ScaleLevel,
        description: Optional[str] = None,
        auto_commit: bool = True  # NEW: Default True (backward compatible)
    ) -> Path:
        """
        Initialize feature folder with scale-level based structure.

        EXISTING FUNCTIONALITY (Epic 28):
        - Creates docs/features/{feature_name}/
        - Generates PRD.md, ARCHITECTURE.md templates
        - Creates epics/, stories/, retrospectives/ (scale-dependent)
        - Registers with DocumentLifecycleManager
        - Commits to git

        NEW ENHANCEMENTS (Story 33.1):
        - Creates QA/ folder (all scale levels)
        - Generates README.md from Jinja2 template
        - Supports auto_commit parameter:
          - True (default): Commits to git (backward compatible)
          - False: Skips commit (for GitIntegratedStateManager)

        Args:
            feature_name: Feature name (e.g., "user-auth", "mvp")
            scale_level: Project scale (0-4)
            description: Optional feature description
            auto_commit: Whether to commit to git (default: True)

        Returns:
            Path to created feature folder

        Raises:
            ValueError: If feature folder already exists
        """
        logger.info(
            "Initializing feature folder",
            feature_name=feature_name,
            scale_level=scale_level.value,
            auto_commit=auto_commit
        )

        feature_path = self.project_root / "docs" / "features" / feature_name

        # Check if already exists
        if feature_path.exists():
            raise ValueError(f"Feature folder already exists: {feature_path}")

        # Create feature directory
        feature_path.mkdir(parents=True, exist_ok=False)

        # EXISTING: Generate PRD.md and ARCHITECTURE.md
        self._create_prd(feature_path, feature_name, description, scale_level)
        self._create_architecture(feature_path, feature_name, description, scale_level)

        # NEW: Generate README.md
        self._create_readme(feature_path, feature_name, description, scale_level)

        # EXISTING: Create folders based on scale level
        (feature_path / "epics").mkdir()

        if scale_level >= ScaleLevel.LEVEL_2:
            (feature_path / "stories").mkdir()  # Will be deprecated for co-located structure

        # NEW: Create QA/ folder (all scale levels)
        (feature_path / "QA").mkdir()

        if scale_level >= ScaleLevel.LEVEL_3:
            (feature_path / "retrospectives").mkdir()

        if scale_level == ScaleLevel.LEVEL_4:
            (feature_path / "ceremonies").mkdir()

        # EXISTING: Create CHANGELOG.md
        self._create_changelog(feature_path, feature_name)

        # EXISTING: Register with DocumentLifecycleManager
        self.lifecycle.register_document(
            path=feature_path / "PRD.md",
            doc_type="prd",
            author="system",
            metadata={"feature_name": feature_name, "scale_level": scale_level.value}
        )

        # NEW: Conditional git commit
        if auto_commit:
            self.git.add_all()
            self.git.commit(
                f"docs({feature_name}): initialize feature folder\n\n"
                f"Created feature structure with scale level {scale_level.value}.\n"
                f"Includes: PRD, Architecture, README, QA, and folder structure."
            )
            logger.info("Feature folder committed to git", feature_name=feature_name)
        else:
            logger.info(
                "Feature folder created (no git commit - delegated to caller)",
                feature_name=feature_name
            )

        return feature_path

    def _create_readme(
        self,
        feature_path: Path,
        feature_name: str,
        description: Optional[str],
        scale_level: ScaleLevel
    ) -> None:
        """
        Create README.md from Jinja2 template.

        Template location: gao_dev/config/prompts/feature/README.md.j2
        """
        template = self.jinja_env.get_template("README.md.j2")

        content = template.render(
            feature_name=feature_name,
            description=description or f"Feature: {feature_name}",
            scale_level=scale_level.value,
            created_date=datetime.now().strftime("%Y-%m-%d"),
            has_ceremonies=scale_level == ScaleLevel.LEVEL_4,
            has_retrospectives=scale_level >= ScaleLevel.LEVEL_3
        )

        readme_path = feature_path / "README.md"
        readme_path.write_text(content, encoding="utf-8")

        logger.info("Created README.md", path=str(readme_path))
```

**README.md.j2 Template:**

```markdown
# {{ feature_name }}

**Description:** {{ description }}

**Scale Level:** {{ scale_level }}

**Created:** {{ created_date }}

---

## Overview

This feature follows GAO-Dev's feature-based document structure with co-located epic and story organization.

## Documents

- **[PRD.md](./PRD.md)** - Product Requirements Document
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical Architecture
- **[EPICS.md](./EPICS.md)** - Master Epic Overview

## Structure

```
{{ feature_name }}/
├── PRD.md                    # Requirements
├── ARCHITECTURE.md           # Architecture
├── README.md                 # This file
├── EPICS.md                  # Epic overview
├── epics/                    # Epic containers (co-located with stories)
│   └── {N}-{epic-name}/
│       ├── README.md         # Epic definition
│       ├── stories/          # Stories for this epic
│       └── context/          # Context XML files
├── QA/                       # Quality artifacts
│   ├── QA_VALIDATION_*.md
│   └── TEST_REPORT_*.md
{% if has_retrospectives %}
├── retrospectives/           # Retrospectives
│   └── epic-{N}-retro.md
{% endif %}
{% if has_ceremonies %}
└── ceremonies/               # Ceremony artifacts
    └── planning-session-*.md
{% endif %}
```

## Epics

See [EPICS.md](./EPICS.md) for complete epic list and status.

## Contributing

All work should follow the co-located epic-story structure:
1. Epic definition in `epics/{N}-{name}/README.md`
2. Stories in `epics/{N}-{name}/stories/story-{N}.{M}.md`
3. Context XML in `epics/{N}-{name}/context/`

## Quality Assurance

All QA artifacts go in the `QA/` folder. See QA validation and test reports for quality metrics.

---

*This feature was created with GAO-Dev's DocumentStructureManager (Epic 28 + Story 33.1)*
```

### Code Locations

**File to Modify:**
- `gao_dev/core/services/document_structure_manager.py` (lines ~69-200)
  - Add auto_commit parameter to initialize_feature_folder()
  - Add _create_readme() method
  - Create QA/ folder

**New File:**
- `gao_dev/config/prompts/feature/README.md.j2` (Jinja2 template)

**Reference:**
- Epic 28 DocumentStructureManager implementation

### Dependencies

**Required Before Starting:**
- Epic 28: DocumentStructureManager (COMPLETE)

**Blocks:**
- Story 33.2: GitIntegratedStateManager.create_feature() (needs auto_commit=False)

### Integration Points

1. **GitManager**: Conditional commit based on auto_commit parameter
2. **DocumentLifecycleManager**: Register README.md as new document
3. **Jinja2**: Template rendering for README.md

## Testing Requirements

### Unit Tests (20+ assertions)

**Location:** `tests/core/services/test_document_structure_manager.py` (extend existing)

**Test Coverage:**

1. **QA/ Folder Creation (4 assertions)**
   - QA/ folder exists after initialization
   - QA/ folder is a directory
   - QA/ folder included in git commit
   - All scale levels get QA/ folder

2. **README.md Generation (6 assertions)**
   - README.md exists after initialization
   - README.md contains feature name
   - README.md contains description
   - README.md contains scale level
   - README.md contains structure diagram
   - README.md sections match template

3. **auto_commit Parameter (6 assertions)**
   - auto_commit=True commits to git (default)
   - auto_commit=False skips git commit
   - Feature path returned in both cases
   - Files still created when auto_commit=False
   - Git status clean after auto_commit=True
   - Git status has changes after auto_commit=False

4. **Backward Compatibility (4 assertions)**
   - Existing tests pass without modifications
   - Default behavior unchanged (auto_commit=True)
   - PRD.md and ARCHITECTURE.md still created
   - DocumentLifecycleManager integration works

## Definition of Done

- [ ] QA/ folder created for all features
- [ ] README.md generated from Jinja2 template
- [ ] auto_commit parameter working (True/False)
- [ ] 20+ unit test assertions passing
- [ ] Backward compatible (existing tests pass)
- [ ] Code reviewed and approved
- [ ] No regressions in Epic 28 functionality
- [ ] Type hints throughout (mypy passes)
- [ ] Structlog logging updated

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Epic 1 - DocumentStructureManager Enhancement)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Component 1 - DocumentStructureManager Extensions)
- **Epic 28:** DocumentStructureManager original implementation
