# Story 13.5: MetaPromptEngine Implementation

**Epic:** 13 - Meta-Prompt System & Context Injection
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement MetaPromptEngine that extends PromptLoader with meta-prompt capabilities. This is the orchestrating component that brings together all resolvers, handles automatic context injection, supports nested references, and detects cycles.

---

## Business Value

This story completes the meta-prompt system:

- **Unified Interface**: Single entry point for prompt rendering with meta-prompts
- **Automatic Context**: Workflow-based automatic context injection
- **Nested References**: Handle complex prompt compositions
- **Safety**: Cycle detection prevents infinite loops
- **Performance**: Caching and optimization for fast rendering
- **Backward Compatibility**: Works seamlessly with Epic 10's PromptLoader

---

## Acceptance Criteria

### Core Functionality
- [ ] Extends Epic 10's PromptLoader (composition, not inheritance)
- [ ] `render_with_meta_prompts()` resolves all reference types
- [ ] Supports @doc:, @checklist:, @query:, @context:, @config:, @file: references
- [ ] Variable substitution happens BEFORE reference resolution
- [ ] References in rendered content recursively resolved

### Automatic Context Injection
- [ ] Configuration for per-workflow auto-injection
- [ ] Auto-inject epic context for story workflows
- [ ] Auto-inject architecture for implementation workflows
- [ ] Auto-inject checklists for validation workflows
- [ ] Auto-injection configurable in YAML

### Nested References
- [ ] Support nested references up to 3 levels deep
- [ ] Depth tracking prevents infinite recursion
- [ ] Cycle detection with clear error messages
- [ ] Referenced documents can contain references

### Performance
- [ ] Render typical prompt in <200ms
- [ ] Cache resolved references
- [ ] Batch document loading when possible
- [ ] Performance metrics tracked

### Integration
- [ ] Works with all existing prompt templates
- [ ] No breaking changes to PromptLoader API
- [ ] Feature flag for gradual rollout
- [ ] Fallback to standard rendering if meta-prompt fails

---

## Technical Notes

### Implementation

```python
# gao_dev/core/meta_prompts/meta_prompt_engine.py

from pathlib import Path
from typing import Dict, Any, Optional
from gao_dev.core.prompt_loader import PromptLoader, PromptTemplate
from gao_dev.core.meta_prompts.resolver_registry import ReferenceResolverRegistry

class MetaPromptEngine:
    """
    Meta-prompt engine that extends PromptLoader with reference resolution.

    Composition over inheritance - wraps PromptLoader rather than extending it.
    """

    def __init__(
        self,
        prompt_loader: PromptLoader,
        resolver_registry: ReferenceResolverRegistry,
        auto_injection_config: Optional[Path] = None
    ):
        self.prompt_loader = prompt_loader
        self.resolver_registry = resolver_registry
        self.auto_injection = self._load_auto_injection_config(auto_injection_config)
        self.max_depth = 3

    def load_prompt(self, name: str) -> PromptTemplate:
        """Load prompt template (delegates to PromptLoader)."""
        return self.prompt_loader.load_prompt(name)

    def render_prompt(
        self,
        template: PromptTemplate,
        variables: Dict[str, Any],
        workflow_name: Optional[str] = None
    ) -> str:
        """
        Render prompt with meta-prompt support.

        Process:
        1. Add automatic context for workflow
        2. Render template with variables (Epic 10 logic)
        3. Resolve all meta-prompt references
        4. Return final rendered prompt
        """
        # Step 1: Add automatic context injection
        if workflow_name and workflow_name in self.auto_injection:
            auto_vars = self._get_auto_injection_variables(workflow_name, variables)
            variables = {**variables, **auto_vars}

        # Step 2: Standard template rendering (Epic 10)
        rendered = self.prompt_loader.render_prompt(template, variables)

        # Step 3: Resolve meta-prompt references
        final = self._resolve_references(rendered, variables, depth=0)

        return final

    def _resolve_references(
        self,
        content: str,
        context: Dict[str, Any],
        depth: int = 0
    ) -> str:
        """
        Resolve all references in content.

        Supports nested references up to max_depth.
        """
        if depth > self.max_depth:
            raise CircularReferenceError(
                f"Maximum nesting depth ({self.max_depth}) exceeded. "
                "Possible circular reference."
            )

        # Find all references in content
        references = self._find_references(content)

        if not references:
            return content  # Base case: no references

        # Resolve each reference
        for ref_str in references:
            try:
                resolved = self.resolver_registry.resolve(ref_str, context)

                # Replace reference with resolved content
                content = content.replace(ref_str, resolved)

            except Exception as e:
                logger.warning(f"Failed to resolve reference {ref_str}: {e}")
                # Replace with empty string and continue
                content = content.replace(ref_str, "")

        # Recursively resolve references in resolved content
        if self._has_references(content):
            content = self._resolve_references(content, context, depth + 1)

        return content

    def _find_references(self, content: str) -> List[str]:
        """
        Find all @{type}:{value} references in content.

        Returns list of reference strings (e.g., ["@doc:path/file.md", "@context:epic"])
        """
        import re
        pattern = r'@(\w+):([^\s\n]+)'
        matches = re.findall(pattern, content)
        return [f"@{type_}:{value}" for type_, value in matches]

    def _has_references(self, content: str) -> bool:
        """Check if content contains any references."""
        return '@' in content and ':' in content

    def _get_auto_injection_variables(
        self,
        workflow_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get automatic injection variables for workflow.

        Example:
            workflow_name = "implement_story"
            -> Returns variables with auto-injected context
        """
        auto_vars = {}
        config = self.auto_injection[workflow_name]

        for key, reference in config.items():
            # Render reference with current variables
            rendered_ref = self._render_template_string(reference, variables)
            # Resolve the reference
            resolved = self.resolver_registry.resolve(rendered_ref, variables)
            auto_vars[key] = resolved

        return auto_vars

    def _render_template_string(self, template_str: str, variables: Dict) -> str:
        """Render a template string with variables."""
        from jinja2 import Template
        template = Template(template_str)
        return template.render(**variables)

    def _load_auto_injection_config(self, config_path: Optional[Path]) -> Dict:
        """
        Load automatic context injection configuration.

        Format (YAML):
            implement_story:
              story_context: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
              epic_context: "@context:epic_definition"
              architecture: "@context:architecture"
              testing_checklist: "@checklist:testing/unit-test-standards"

            create_story:
              epic_context: "@context:epic_definition"
              prd: "@context:prd"
        """
        if not config_path or not config_path.exists():
            return {}

        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
```

### Auto-Injection Configuration

```yaml
# gao_dev/config/auto_injection.yaml

# Automatic context injection per workflow

implement_story:
  # Story context
  story_definition: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
  acceptance_criteria: "@doc:stories/epic-{{epic}}/story-{{story}}.md#acceptance-criteria"

  # Epic and architecture context
  epic_definition: "@context:epic_definition"
  architecture: "@context:architecture"

  # Quality standards
  testing_standards: "@checklist:testing/unit-test-standards"
  code_quality: "@checklist:code-quality/solid-principles"

create_story:
  # Epic context for story creation
  epic_definition: "@context:epic_definition"
  prd: "@context:prd"

  # Related stories
  related_stories: "@query:stories.where(epic={{epic}}, status='done').format('list')"

validate_story:
  # Story and acceptance criteria
  story_definition: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
  acceptance_criteria: "@doc:stories/epic-{{epic}}/story-{{story}}.md#acceptance-criteria"

  # Quality checklists
  qa_checklist: "@checklist:testing/qa-comprehensive"
```

### Usage Example

```python
# Example: Render prompt with meta-prompts

from gao_dev.core.meta_prompts import MetaPromptEngine

# Initialize
engine = MetaPromptEngine(
    prompt_loader=PromptLoader(prompts_dir=Path("gao_dev/config/prompts")),
    resolver_registry=resolver_registry,
    auto_injection_config=Path("gao_dev/config/auto_injection.yaml")
)

# Load and render prompt
template = engine.load_prompt("tasks/implement_story")
rendered = engine.render_prompt(
    template,
    variables={"epic": 3, "story": 1, "feature": "sandbox-system"},
    workflow_name="implement_story"
)

# Result: All @doc:, @context:, @checklist: references resolved
# Automatic context injected based on workflow
```

**Files to Create:**
- `gao_dev/core/meta_prompts/meta_prompt_engine.py`
- `gao_dev/config/auto_injection.yaml`
- `tests/core/meta_prompts/test_meta_prompt_engine.py`
- `tests/core/meta_prompts/test_auto_injection.py`

**Dependencies:**
- Story 13.1, 13.2, 13.3, 13.4 (All resolvers)
- Epic 10 (PromptLoader)

---

## Testing Requirements

### Unit Tests

**Core Rendering:**
- [ ] Test render_prompt() with no references
- [ ] Test render_prompt() with single reference
- [ ] Test render_prompt() with multiple references
- [ ] Test variable substitution before reference resolution
- [ ] Test nested references (1, 2, 3 levels)
- [ ] Test max depth enforcement
- [ ] Test circular reference detection

**Auto-Injection:**
- [ ] Test auto-injection for each workflow
- [ ] Test auto-injection disabled when no workflow specified
- [ ] Test auto-injection with template variables ({{epic}}, {{story}})
- [ ] Test auto-injection config loading

**Error Handling:**
- [ ] Test missing reference handled gracefully
- [ ] Test invalid reference syntax handled
- [ ] Test resolver not found handled
- [ ] Test partial rendering on error

### Integration Tests
- [ ] Test with all resolver types
- [ ] Test with real prompt templates
- [ ] Test end-to-end workflow execution
- [ ] Test backward compatibility with Epic 10 prompts

### Performance Tests
- [ ] Typical prompt renders in <200ms
- [ ] Complex prompt (10+ references) renders in <500ms
- [ ] Auto-injection overhead <50ms
- [ ] Reference caching reduces repeated resolution

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] MetaPromptEngine API documentation
- [ ] Auto-injection configuration guide
- [ ] Nested reference resolution algorithm documented
- [ ] Examples for each reference type
- [ ] Migration guide from PromptLoader
- [ ] Performance optimization tips

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No breaking changes to PromptLoader
- [ ] Performance benchmarks met
- [ ] Auto-injection working for all workflows
- [ ] Integration tests with all resolvers passing
- [ ] Committed with atomic commit message:
  ```
  feat(epic-13): implement Story 13.5 - MetaPromptEngine Implementation

  - Implement MetaPromptEngine wrapping PromptLoader
  - Add automatic context injection per workflow
  - Support nested references with cycle detection
  - Add auto_injection.yaml configuration
  - Comprehensive error handling and fallbacks
  - Add unit and integration tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
