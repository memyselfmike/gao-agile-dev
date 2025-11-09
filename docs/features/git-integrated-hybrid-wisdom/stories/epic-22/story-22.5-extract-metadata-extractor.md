# Story 22.5: Extract MetadataExtractor Utility

**Epic**: Epic 22 - Orchestrator Decomposition & Architectural Refactoring
**Story ID**: 22.5
**Priority**: P2
**Estimate**: 3 hours
**Owner**: Amelia
**Status**: Done

---

## Story Description

Extract metadata extraction logic from the ArtifactManager (and orchestrator) into a dedicated MetadataExtractor utility service. This utility will handle extraction of feature names, epic numbers, story numbers, and other metadata from file paths and content.

This extraction further refines the separation of concerns, keeping ArtifactManager focused on detection/registration while MetadataExtractor handles parsing logic.

---

## Acceptance Criteria

- [x] Create `MetadataExtractor` utility (~80 LOC)
- [x] Move feature name extraction logic (~27 LOC)
- [x] Move epic/story number extraction logic (~30 LOC)
- [x] Add metadata parsing helpers (~23 LOC)
- [x] ArtifactManager uses MetadataExtractor
- [x] 8 unit tests for extractor (29 tests created)
- [x] All metadata extraction works correctly

---

## Technical Approach

### Implementation Details

The MetadataExtractor provides utility methods for parsing metadata from file paths, content, and context. It uses regex patterns and path analysis to extract structured metadata.

**Key Responsibilities**:
1. Extract feature names from paths
2. Extract epic/story numbers from paths
3. Parse document titles and descriptions
4. Infer metadata from file structure
5. Provide parsing utilities

**Design Pattern**: Utility service with static/class methods

### Files to Modify

- `gao_dev/orchestrator/metadata_extractor.py` (+80 LOC / NEW)
  - Add: MetadataExtractor class
  - Add: extract_feature_name() method
  - Add: extract_epic_number() method
  - Add: extract_story_number() method
  - Add: extract_title() method
  - Add: Helper regex patterns

- `gao_dev/orchestrator/artifact_manager.py` (refactor to use MetadataExtractor)
  - Remove: _extract_feature_name() (~27 LOC)
  - Add: Use MetadataExtractor.extract_feature_name()
  - Add: MetadataExtractor dependency

- `gao_dev/orchestrator/orchestrator.py` (if needed)
  - Update: Use MetadataExtractor where appropriate

### New Files to Create

- `gao_dev/orchestrator/metadata_extractor.py` (~80 LOC)
  - Purpose: Extract metadata from paths and content
  - Key components:
    - MetadataExtractor class
    - extract_feature_name(path) -> Optional[str]
    - extract_epic_number(path) -> Optional[int]
    - extract_story_number(path) -> Optional[Tuple[int, int]]
    - extract_title(content) -> Optional[str]
    - Regex patterns for parsing

- `tests/orchestrator/test_metadata_extractor.py` (~100 LOC)
  - Purpose: Unit tests for metadata extractor
  - Key components:
    - 8 unit tests
    - Test feature name extraction
    - Test epic number extraction
    - Test story number extraction
    - Test edge cases and invalid inputs

---

## Testing Strategy

### Unit Tests (8 tests)

- test_extract_feature_name_from_path() - Extract feature from typical path
- test_extract_feature_name_missing() - Handle paths without features
- test_extract_epic_number_from_path() - Extract epic number
- test_extract_story_number_from_path() - Extract story ID (epic.story)
- test_extract_title_from_markdown() - Parse title from markdown
- test_extract_title_missing() - Handle content without title
- test_metadata_extractor_edge_cases() - Test edge cases
- test_metadata_patterns() - Test regex pattern accuracy

**Total Tests**: 8 tests
**Test File**: `tests/orchestrator/test_metadata_extractor.py`

---

## Dependencies

**Upstream**: Story 22.2 (ArtifactManager - this refactors it)

**Downstream**: None (utility service)

---

## Implementation Notes

### Current Method to Extract

```python
# From gao_dev/orchestrator/orchestrator.py

def _extract_feature_name(self, file_path: Path) -> Optional[str]:
    """Extract feature name from path."""
    # ~27 LOC
    # Parse path
    # Look for "features" directory
    # Extract feature name
    # Return name or None
```

### New Utility Structure

```python
# gao_dev/orchestrator/metadata_extractor.py

import re
from pathlib import Path
from typing import Optional, Tuple

class MetadataExtractor:
    """Utility for extracting metadata from paths and content."""

    # Regex patterns
    FEATURE_PATTERN = re.compile(r'/features/([^/]+)/')
    EPIC_PATTERN = re.compile(r'epic-(\d+)')
    STORY_PATTERN = re.compile(r'story-(\d+)\.(\d+)')
    TITLE_PATTERN = re.compile(r'^#\s+(.+)$', re.MULTILINE)

    @classmethod
    def extract_feature_name(cls, path: Path) -> Optional[str]:
        """
        Extract feature name from file path.

        Examples:
            docs/features/sandbox-system/PRD.md → "sandbox-system"
            docs/features/git-wisdom/epics/epic-1.md → "git-wisdom"

        Returns:
            Feature name or None if not found
        """
        match = cls.FEATURE_PATTERN.search(str(path))
        return match.group(1) if match else None

    @classmethod
    def extract_epic_number(cls, path: Path) -> Optional[int]:
        """
        Extract epic number from file path.

        Examples:
            docs/epics/epic-5.md → 5
            docs/features/x/epics/epic-22.md → 22

        Returns:
            Epic number or None if not found
        """
        match = cls.EPIC_PATTERN.search(str(path))
        return int(match.group(1)) if match else None

    @classmethod
    def extract_story_number(cls, path: Path) -> Optional[Tuple[int, int]]:
        """
        Extract story number (epic, story) from file path.

        Examples:
            docs/stories/epic-5/story-5.3.md → (5, 3)

        Returns:
            (epic_num, story_num) or None if not found
        """
        match = cls.STORY_PATTERN.search(str(path))
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None

    @classmethod
    def extract_title(cls, content: str) -> Optional[str]:
        """
        Extract document title from markdown content.

        Looks for first H1 heading (# Title).

        Returns:
            Title string or None if not found
        """
        match = cls.TITLE_PATTERN.search(content)
        return match.group(1).strip() if match else None
```

### Extraction Patterns

**Feature Name**:
- Pattern: `/features/{feature-name}/`
- Examples:
  - `docs/features/sandbox-system/PRD.md` → "sandbox-system"
  - `docs/features/git-integrated-hybrid-wisdom/epics/epic-22.md` → "git-integrated-hybrid-wisdom"

**Epic Number**:
- Pattern: `epic-{number}`
- Examples:
  - `docs/epics/epic-5.md` → 5
  - `docs/features/x/epics/epic-22.md` → 22

**Story Number**:
- Pattern: `story-{epic}.{story}`
- Examples:
  - `docs/stories/epic-5/story-5.3.md` → (5, 3)
  - `docs/features/x/stories/epic-22/story-22.1.md` → (22, 1)

**Title**:
- Pattern: First `# Title` in markdown
- Examples:
  - `# Epic 22: Orchestrator Decomposition` → "Epic 22: Orchestrator Decomposition"

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (8/8 unit tests)
- [ ] Code coverage >80% for utility
- [ ] Code review completed
- [ ] Documentation updated (docstrings with examples)
- [ ] ArtifactManager refactored to use extractor
- [ ] Git commit created
- [ ] Utility <100 LOC (target: ~80 LOC)
- [ ] MyPy strict mode passes

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
