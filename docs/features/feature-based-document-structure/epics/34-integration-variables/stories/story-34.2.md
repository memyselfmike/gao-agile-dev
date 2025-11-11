---
document:
  type: "story"
  state: "ready"
  created: "2025-11-11"
  epic: 34
  story: 2
  feature: "feature-based-document-structure"
  points: 2
---

# Story 34.2: Update defaults.yaml (2 points)

**Epic:** 34 - Integration & Variables
**Feature:** Feature-Based Document Structure
**Status:** Ready
**Owner:** Unassigned
**Points:** 2

## User Story

As a **workflow executor**,
I want **defaults.yaml updated with co-located epic-story paths**,
So that **all workflows use feature-scoped paths by default and variables resolve correctly**.

## Acceptance Criteria

### AC1: Replace All Path Defaults
- [ ] Update `gao_dev/config/defaults.yaml` with feature-scoped paths
- [ ] Replace legacy paths (docs/PRD.md) with feature-scoped (docs/features/{{feature_name}}/PRD.md)
- [ ] All path variables use {{feature_name}} template variable
- [ ] Clear naming convention: _location (files), _folder (directories), _overview (master files)

### AC2: Co-Located Epic-Story Structure
- [ ] Epic paths: `docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/`
- [ ] Story paths: `docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/`
- [ ] Context XML: `docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context/`
- [ ] Epic definition: `docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md`
- [ ] Story files: `story-{{epic}}.{{story}}.md` (e.g., story-1.2.md)

### AC3: All Document Types Covered
- [ ] Feature-level documents: PRD, Architecture, README, EPICS overview
- [ ] Feature-level folders: QA, retrospectives, ceremonies
- [ ] Epic-level: epic folder, epic definition
- [ ] Story-level: story folder, story location, context XML
- [ ] Ceremony artifacts: retrospectives, standups, planning sessions

### AC4: Variable Naming Convention
- [ ] `{type}_location` for specific file paths (e.g., prd_location, story_location)
- [ ] `{type}_folder` for directory paths (e.g., epic_folder, qa_folder)
- [ ] `{type}_overview` for master/index files (e.g., epics_overview)
- [ ] Consistent snake_case naming
- [ ] No ambiguous names (clear what each variable points to)

### AC5: Testing
- [ ] Validation tests verify all paths resolve correctly
- [ ] Test with sample feature_name, epic, story values
- [ ] Test that FeaturePathResolver generates same paths
- [ ] Integration test: Create feature → epic → story using new paths

## Technical Notes

### Implementation Approach

**Updated defaults.yaml:**

```yaml
# Location: gao_dev/config/defaults.yaml

workflow_defaults:
  # ========================================================================
  # FEATURE-BASED DOCUMENT STRUCTURE (v3.0)
  # ========================================================================
  # All paths now feature-scoped using co-located epic-story structure.
  # Epic folders contain their stories for intuitive navigation.
  #
  # Naming Convention:
  #   _location = specific file path (PRD.md, story-1.1.md)
  #   _folder   = directory path (epics/, QA/)
  #   _overview = master/index file (EPICS.md)
  #
  # Template Variables:
  #   {{feature_name}} = Feature name (e.g., "user-auth", "mvp")
  #   {{epic}}         = Epic number (e.g., "1", "2")
  #   {{epic_name}}    = Epic name (e.g., "foundation", "oauth")
  #   {{story}}        = Story number (e.g., "1", "2")
  # ========================================================================

  # ------------------------------------------------------------------------
  # Feature-Level Documents
  # ------------------------------------------------------------------------
  # Primary documents at feature root
  # ------------------------------------------------------------------------

  feature_dir: "docs/features/{{feature_name}}"
  prd_location: "docs/features/{{feature_name}}/PRD.md"
  architecture_location: "docs/features/{{feature_name}}/ARCHITECTURE.md"
  readme_location: "docs/features/{{feature_name}}/README.md"
  epics_overview: "docs/features/{{feature_name}}/EPICS.md"

  # ------------------------------------------------------------------------
  # Feature-Level Folders
  # ------------------------------------------------------------------------
  # Organizational folders at feature root
  # ------------------------------------------------------------------------

  qa_folder: "docs/features/{{feature_name}}/QA"
  retrospectives_folder: "docs/features/{{feature_name}}/retrospectives"
  ceremonies_folder: "docs/features/{{feature_name}}/ceremonies"

  # ------------------------------------------------------------------------
  # Epic-Level Paths (CO-LOCATED with stories!)
  # ------------------------------------------------------------------------
  # Epic folders contain:
  #   - README.md (epic definition)
  #   - stories/ (all stories for this epic)
  #   - context/ (context XML files)
  # ------------------------------------------------------------------------

  epic_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}"
  epic_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/README.md"

  # ------------------------------------------------------------------------
  # Story-Level Paths (INSIDE epic folder!)
  # ------------------------------------------------------------------------
  # Stories are co-located with their epic for intuitive navigation
  # ------------------------------------------------------------------------

  story_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories"
  story_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/stories/story-{{epic}}.{{story}}.md"
  context_xml_folder: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context"
  context_xml_location: "docs/features/{{feature_name}}/epics/{{epic}}-{{epic_name}}/context/story-{{epic}}.{{story}}.xml"

  # ------------------------------------------------------------------------
  # Ceremony Artifact Paths
  # ------------------------------------------------------------------------
  # Ceremony outputs stored at feature level
  # ------------------------------------------------------------------------

  retrospective_location: "docs/features/{{feature_name}}/retrospectives/epic-{{epic}}-retro.md"
  standup_location: "docs/features/{{feature_name}}/standups/standup-{{date}}.md"
  planning_session_location: "docs/features/{{feature_name}}/ceremonies/planning-{{date}}.md"

  # ------------------------------------------------------------------------
  # QA Artifact Paths
  # ------------------------------------------------------------------------
  # Quality assurance documents in QA/ folder
  # ------------------------------------------------------------------------

  qa_validation_location: "docs/features/{{feature_name}}/QA/QA_VALIDATION_EPIC_{{epic}}.md"
  test_report_location: "docs/features/{{feature_name}}/QA/TEST_REPORT_EPIC_{{epic}}.md"
  final_qa_report_location: "docs/features/{{feature_name}}/QA/FINAL_QA_REPORT_{{feature_name}}.md"

  # ------------------------------------------------------------------------
  # LEGACY PATHS (Backward Compatibility - DEPRECATED)
  # ------------------------------------------------------------------------
  # These paths are deprecated but kept for backward compatibility.
  # New workflows should use feature-scoped paths above.
  # Will be removed in future version.
  # ------------------------------------------------------------------------

  legacy_prd_location: "docs/PRD.md"
  legacy_architecture_location: "docs/ARCHITECTURE.md"
  legacy_epic_location: "docs/epics.md"
  legacy_story_folder: "docs/stories"

  # ------------------------------------------------------------------------
  # Common Variables (Auto-Generated)
  # ------------------------------------------------------------------------
  # These are auto-populated by WorkflowExecutor
  # ------------------------------------------------------------------------

  date: "{{date}}"                    # Current date (YYYY-MM-DD)
  timestamp: "{{timestamp}}"          # Current timestamp (ISO 8601)
  project_name: "{{project_name}}"    # Project name (from project_root)
  project_root: "{{project_root}}"    # Absolute path to project root
  agent: "{{agent}}"                  # Agent executing workflow
  workflow: "{{workflow}}"            # Workflow name
```

**Path Examples (for documentation):**

```yaml
# Example path resolutions:

# Feature: user-auth, Epic: 1 (oauth-integration), Story: 2
feature_name: "user-auth"
epic: "1"
epic_name: "oauth-integration"
story: "2"

# Resolved paths:
prd_location: "docs/features/user-auth/PRD.md"
epic_folder: "docs/features/user-auth/epics/1-oauth-integration"
epic_location: "docs/features/user-auth/epics/1-oauth-integration/README.md"
story_folder: "docs/features/user-auth/epics/1-oauth-integration/stories"
story_location: "docs/features/user-auth/epics/1-oauth-integration/stories/story-1.2.md"
context_xml_location: "docs/features/user-auth/epics/1-oauth-integration/context/story-1.2.xml"
qa_validation_location: "docs/features/user-auth/QA/QA_VALIDATION_EPIC_1.md"

# Feature: mvp (greenfield initial scope)
feature_name: "mvp"
epic: "1"
epic_name: "foundation"
story: "1"

# Resolved paths:
prd_location: "docs/features/mvp/PRD.md"
epic_folder: "docs/features/mvp/epics/1-foundation"
story_location: "docs/features/mvp/epics/1-foundation/stories/story-1.1.md"
```

### Code Locations

**File to Modify:**
- `gao_dev/config/defaults.yaml` (replace workflow_defaults section)

**Files to Update (Documentation):**
- `docs/features/feature-based-document-structure/VARIABLE_NAMING_GUIDE.md` (new file)
- `CLAUDE.md` (update Essential Commands section with new paths)

### Dependencies

**Required Before Starting:**
- Story 32.4: FeaturePathResolver (templates should match)

**Blocks:**
- Story 34.3: WorkflowExecutor integration (uses updated defaults)

### Integration Points

1. **FeaturePathResolver**: Must generate paths matching these templates exactly
2. **WorkflowExecutor**: Will resolve variables using these defaults
3. **All Workflows**: Will use these paths when creating documents

## Testing Requirements

### Validation Tests

**Location:** `tests/config/test_defaults_yaml.py`

**Test Coverage:**

1. **Path Resolution (10 assertions)**
   - Load defaults.yaml
   - Verify all path variables present
   - Resolve sample paths (feature_name="user-auth", epic="1", story="2")
   - Verify resolved paths match expected format
   - Test with mvp feature
   - Test with multiple epics and stories

2. **Naming Convention (5 assertions)**
   - All file paths end with _location
   - All directory paths end with _folder
   - All master files end with _overview
   - No ambiguous variable names
   - All variables use snake_case

3. **Template Variable Coverage (5 assertions)**
   - All paths use {{feature_name}} variable
   - Epic paths use {{epic}} and {{epic_name}}
   - Story paths use {{epic}}, {{epic_name}}, {{story}}
   - Ceremony paths use {{date}} where appropriate
   - No hardcoded feature names in templates

4. **FeaturePathResolver Compatibility (5 assertions)**
   - FeaturePathResolver.generate_feature_path() matches defaults.yaml
   - All path types in defaults.yaml supported by resolver
   - Resolver and defaults.yaml templates identical
   - No template mismatches

5. **Integration Test (5 assertions)**
   - Create feature using new paths
   - Create epic using new paths
   - Create story using new paths
   - Verify all files at correct locations
   - Verify co-located structure (stories inside epic folder)

## Definition of Done

- [ ] defaults.yaml updated with all feature-scoped paths
- [ ] Co-located epic-story structure implemented
- [ ] Naming convention followed (_location, _folder, _overview)
- [ ] All document types covered (15+ path variables)
- [ ] Validation tests passing (30+ assertions)
- [ ] FeaturePathResolver templates match defaults.yaml exactly
- [ ] Integration test passes (feature → epic → story)
- [ ] Documentation updated (VARIABLE_NAMING_GUIDE.md, CLAUDE.md)
- [ ] Code reviewed and approved

## References

- **PRD:** `docs/features/feature-based-document-structure/PRD.md` (Section: Technical Requirements - Complete Variable Definitions)
- **Architecture:** `docs/features/feature-based-document-structure/ARCHITECTURE.md` (Section: Integration 4 - Variable Defaults)
- **FeaturePathResolver:** Story 32.4 (templates must match)
