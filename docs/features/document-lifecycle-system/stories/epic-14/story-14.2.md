# Story 14.2: ChecklistLoader Implementation

**Epic:** 14 - Checklist Plugin System
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement ChecklistLoader that loads, validates, and resolves checklist inheritance from YAML files. Similar to PromptLoader from Epic 10, this provides the core infrastructure for the checklist system with support for inheritance resolution, plugin integration, and performance-optimized caching.

---

## Business Value

This story provides the loading infrastructure that makes checklists reusable and extensible:

- **Centralized Loading**: Single interface for loading all checklists simplifies usage across the system
- **Validation**: Automatic schema validation prevents invalid checklists from breaking workflows
- **Inheritance**: Reuse common checklist items via extends mechanism reduces duplication by 60%
- **Performance**: Caching reduces repeated file reads from ~10ms to <1ms per load
- **Discovery**: Automatic discovery of available checklists enables dynamic checklist selection
- **Plugin Support**: Load checklists from plugins without code changes, enabling domain-specific extensions
- **Quality Gates**: Foundation for automated quality checks in CI/CD pipelines

---

## Acceptance Criteria

### Core Loading
- [ ] `load_checklist(name)` loads checklist from YAML file
- [ ] Validates against JSON schema (Story 14.1)
- [ ] Resolves `extends` inheritance recursively
- [ ] Caches loaded checklists for performance
- [ ] `list_checklists()` discovers all available checklists
- [ ] `render_checklist()` outputs markdown format

### Inheritance Resolution
- [ ] Child checklist items override parent items with same ID
- [ ] Child items appended to parent items
- [ ] Recursive inheritance supported (grandparent → parent → child)
- [ ] Circular inheritance detected and prevented
- [ ] Metadata merged (child overrides parent)

### Plugin Integration
- [ ] Plugin checklists discovered from plugin directories
- [ ] Plugin checklists override core checklists (same name)
- [ ] Multiple checklist directories supported
- [ ] Search order: plugin → project → core

### Performance
- [ ] Load <10ms (cached)
- [ ] Discovery (list_checklists) <100ms
- [ ] Inheritance resolution <50ms

---

## Technical Notes

```python
# gao_dev/core/checklists/checklist_loader.py

from pathlib import Path
from typing import Dict, List, Optional
import yaml
import jsonschema
from dataclasses import dataclass

@dataclass
class ChecklistItem:
    id: str
    text: str
    severity: str
    category: Optional[str] = None
    help_text: Optional[str] = None
    references: List[str] = None

@dataclass
class Checklist:
    name: str
    category: str
    version: str
    description: Optional[str]
    items: List[ChecklistItem]
    metadata: Dict

class ChecklistLoader:
    """Load and validate checklists from YAML files."""

    def __init__(self, checklist_dirs: List[Path], schema_path: Path):
        self.checklist_dirs = checklist_dirs
        self.schema = self._load_schema(schema_path)
        self._cache: Dict[str, Checklist] = {}

    def load_checklist(self, name: str) -> Checklist:
        """Load checklist by name (e.g., 'testing/unit-test-standards')."""
        if name in self._cache:
            return self._cache[name]

        # Find checklist file
        checklist_path = self._find_checklist(name)
        if not checklist_path:
            raise ChecklistNotFoundError(f"Checklist not found: {name}")

        # Load and validate
        with open(checklist_path) as f:
            data = yaml.safe_load(f)

        self._validate(data)

        # Resolve inheritance
        checklist = self._resolve_inheritance(data, name)

        # Cache and return
        self._cache[name] = checklist
        return checklist

    def _resolve_inheritance(self, data: dict, name: str) -> Checklist:
        """Resolve extends inheritance."""
        checklist_data = data['checklist']

        # Base case: no inheritance
        if 'extends' not in checklist_data:
            return self._parse_checklist(checklist_data)

        # Load parent
        parent_name = checklist_data['extends']
        parent = self.load_checklist(parent_name)

        # Merge: parent items + child items (child overrides same ID)
        merged_items = self._merge_items(parent.items, checklist_data.get('items', []))

        # Merge metadata
        merged_metadata = {**parent.metadata, **checklist_data.get('metadata', {})}

        return Checklist(
            name=checklist_data['name'],
            category=checklist_data['category'],
            version=checklist_data['version'],
            description=checklist_data.get('description'),
            items=merged_items,
            metadata=merged_metadata
        )

    def render_checklist(self, checklist: Checklist) -> str:
        """Render checklist as markdown."""
        lines = [f"# {checklist.name}\n"]
        if checklist.description:
            lines.append(f"{checklist.description}\n")

        for item in checklist.items:
            lines.append(f"- [ ] **[{item.severity.upper()}]** {item.text}")
            if item.help_text:
                lines.append(f"  - {item.help_text}")

        return "\n".join(lines)

    def list_checklists(self) -> List[str]:
        """Discover all available checklists."""
        checklists = []
        for dir in self.checklist_dirs:
            for yaml_file in dir.rglob("*.yaml"):
                rel_path = yaml_file.relative_to(dir)
                name = str(rel_path.with_suffix('')).replace('\\', '/')
                checklists.append(name)
        return sorted(set(checklists))
```

**Files to Create:**
- `gao_dev/core/checklists/__init__.py`
- `gao_dev/core/checklists/checklist_loader.py`
- `gao_dev/core/checklists/models.py`
- `gao_dev/core/checklists/exceptions.py`
- `tests/core/checklists/test_checklist_loader.py`

**Dependencies:**
- Story 14.1 (Checklist YAML Schema)

---

## Testing Requirements

- [ ] Load simple checklist
- [ ] Load checklist with inheritance
- [ ] Load checklist with multi-level inheritance
- [ ] Circular inheritance detected
- [ ] Invalid checklist rejected
- [ ] Missing checklist raises error
- [ ] Cache hit returns cached value
- [ ] list_checklists() finds all checklists
- [ ] Plugin checklists override core
- [ ] Render markdown format

**Test Coverage:** >80%

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Committed with atomic commit

  ```
  feat(epic-14): implement Story 14.2 - ChecklistLoader Implementation

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
