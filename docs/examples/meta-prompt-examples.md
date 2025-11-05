# Meta-Prompt Examples

**Version:** 1.0.0
**Date:** 2025-11-05
**Epic:** 13 - Meta-Prompt System & Context Injection

---

## Overview

This document provides practical examples of using the meta-prompt system introduced in Epic 13. Each example demonstrates a specific reference type and common use cases.

---

## Table of Contents

1. [Document References (@doc:)](#document-references-doc)
2. [Context References (@context:)](#context-references-context)
3. [Checklist References (@checklist:)](#checklist-references-checklist)
4. [Query References (@query:)](#query-references-query)
5. [Config References (@config:)](#config-references-config)
6. [File References (@file:)](#file-references-file)
7. [Nested References](#nested-references)
8. [Automatic Context Injection](#automatic-context-injection)
9. [Advanced Patterns](#advanced-patterns)
10. [Real-World Examples](#real-world-examples)

---

## Document References (@doc:)

### Basic Document Reference

```yaml
name: read_story
version: 2.0.0

user_prompt: |
  Read and summarize this story:

  @doc:stories/epic-1/story-1.1.md

variables:
  # No content variable needed!

meta_prompts:
  enabled: true
```

**What Happens:**
- Document resolver loads `stories/epic-1/story-1.1.md`
- Full content injected into prompt
- Always fresh from source

### Document with Variables

```yaml
name: read_story_dynamic
version: 2.0.0

user_prompt: |
  Read and summarize this story:

  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

variables:
  epic: "1"
  story: "1"

meta_prompts:
  enabled: true
```

**What Happens:**
- Variables `{{epic}}` and `{{story}}` substituted first
- Becomes: `@doc:stories/epic-1/story-1.1.md`
- Then document resolver loads the file

### Document Section Reference

```yaml
name: read_acceptance_criteria
version: 2.0.0

user_prompt: |
  Verify these acceptance criteria are met:

  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md#acceptance-criteria

variables:
  epic: "1"
  story: "1"

meta_prompts:
  enabled: true
```

**What Happens:**
- Document resolver loads the file
- Extracts only the "Acceptance Criteria" section
- Section determined by markdown heading: `## Acceptance Criteria`

### Multiple Document References

```yaml
name: review_feature
version: 2.0.0

user_prompt: |
  Review this feature implementation:

  PRD:
  @doc:features/{{feature}}/PRD.md

  Architecture:
  @doc:features/{{feature}}/ARCHITECTURE.md

  Story:
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

variables:
  feature: "sandbox-system"
  epic: "1"
  story: "1"

meta_prompts:
  enabled: true
```

**Benefits:**
- Single prompt with all context
- No need to pass large content strings
- Always current content

---

## Context References (@context:)

### Basic Context Reference

```yaml
name: use_epic_context
version: 2.0.0

user_prompt: |
  Create a story for this epic:

  Epic Definition:
  @context:epic_definition

variables:
  feature: "sandbox-system"

meta_prompts:
  enabled: true
```

**What Happens:**
- Context resolver queries context registry
- Finds epic_definition for current feature
- Injects content into prompt

### Multiple Context References

```yaml
name: implement_with_standards
version: 2.0.0

user_prompt: |
  Implement this feature following our standards:

  PRD Context:
  @context:prd

  Architecture Context:
  @context:architecture

  Coding Standards:
  @context:coding_standards

variables:
  feature: "sandbox-system"

meta_prompts:
  enabled: true
```

**Benefits:**
- Context automatically scoped to feature
- No need to know file paths
- Centrally managed

### Context with Fallback

```yaml
name: use_optional_context
version: 2.0.0

user_prompt: |
  Implement Story {{epic}}.{{story}}.

  Architecture Guidelines:
  @context:architecture

  If no architecture exists above, create one first.

variables:
  epic: "1"
  story: "1"
  feature: ""

meta_prompts:
  enabled: true
```

**Graceful Degradation:**
- If context not found, reference removed
- Prompt continues with fallback instruction
- Agent knows what to do

---

## Checklist References (@checklist:)

### Basic Checklist Reference

```yaml
name: validate_with_checklist
version: 2.0.0

user_prompt: |
  Validate code quality:

  @checklist:code-quality/solid-principles

  Verify all items above are satisfied.

variables:
  feature: ""

meta_prompts:
  enabled: true
```

**What Happens:**
- Checklist resolver loads checklist file
- Checklist formatted as markdown list
- Agent has clear validation criteria

### Multiple Checklists

```yaml
name: comprehensive_validation
version: 2.0.0

user_prompt: |
  Perform comprehensive validation:

  Unit Test Standards:
  @checklist:testing/unit-test-standards

  Code Quality:
  @checklist:code-quality/solid-principles

  Code Review Checklist:
  @checklist:code-quality/code-review-checklist

  Report results for each checklist.

variables:
  feature: ""

meta_prompts:
  enabled: true
```

**Benefits:**
- All quality standards in one place
- Consistent validation across stories
- Easy to update standards globally

### Checklist for Specific Phase

```yaml
name: story_validation
version: 2.0.0

user_prompt: |
  Validate Story {{epic}}.{{story}}:

  Story Requirements:
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

  QA Comprehensive Checklist:
  @checklist:testing/qa-comprehensive

  For each checklist item, indicate PASS or FAIL.

variables:
  epic: "1"
  story: "1"
  feature: ""

meta_prompts:
  enabled: true
```

---

## Query References (@query:)

### Basic Query

```yaml
name: list_stories
version: 2.0.0

user_prompt: |
  Review existing stories:

  @query:stories.where(epic={{epic}}).format('list')

variables:
  epic: "1"

meta_prompts:
  enabled: true
```

**What Happens:**
- Query resolver executes query on document database
- Filters stories by epic
- Formats results as bulleted list
- Injects into prompt

### Query with Status Filter

```yaml
name: list_completed_stories
version: 2.0.0

user_prompt: |
  Completed stories in this epic:

  @query:stories.where(epic={{epic}}, status='done').format('list')

  Review for consistency and patterns.

variables:
  epic: "1"

meta_prompts:
  enabled: true
```

### Query for Related Documents

```yaml
name: find_related_docs
version: 2.0.0

user_prompt: |
  Related documentation:

  PRDs:
  @query:documents.where(type='prd', feature={{feature}}).format('list')

  ADRs:
  @query:documents.where(type='adr', feature={{feature}}).format('list')

variables:
  feature: "sandbox-system"

meta_prompts:
  enabled: true
```

**Benefits:**
- Dynamic content based on current state
- Always up-to-date
- Prevents duplicate work

### Query with Custom Format

```yaml
name: detailed_story_list
version: 2.0.0

user_prompt: |
  Existing stories:

  @query:stories.where(epic={{epic}}).format('detailed')

  Avoid overlapping these stories.

variables:
  epic: "1"

meta_prompts:
  enabled: true
```

**Format Options:**
- `list`: Bulleted list with titles
- `detailed`: Includes summaries
- `table`: Markdown table format
- `json`: JSON array (for structured processing)

---

## Config References (@config:)

### Basic Config Reference

```yaml
name: brian_analysis
version: 2.0.0

user_prompt: |
  Analyze project scale:

  Scale Level Definitions:
  @config:scale_levels

  Assess which level applies.

variables:
  user_request: ""

meta_prompts:
  enabled: true
```

**What Happens:**
- Config resolver loads configuration value
- Formatted as YAML or JSON
- Injected into prompt

### Schema Reference

```yaml
name: return_json
version: 2.0.0

user_prompt: |
  Analyze and return JSON:

  Expected Schema:
  @config:analysis_response_schema

  Return ONLY JSON matching schema above.

variables:
  request: ""

meta_prompts:
  enabled: true
```

### Multiple Config References

```yaml
name: workflow_config
version: 2.0.0

user_prompt: |
  Execute workflow:

  Scale Levels:
  @config:scale_levels

  Workflow Definitions:
  @config:workflow_registry

  Auto-Injection Config:
  @config:auto_injection

variables:
  workflow: ""

meta_prompts:
  enabled: true
```

---

## File References (@file:)

### Basic File Reference (Epic 10 syntax)

```yaml
name: load_responsibilities
version: 2.0.0

user_prompt: |
  Your responsibilities:

  @file:common/responsibilities/developer.md

variables:
  # None needed

meta_prompts:
  enabled: true
```

**Note:** `@file:` is from Epic 10 and still supported. Use `@doc:` for documents in lifecycle management system.

### File vs Document

**Use @file: for:**
- Static reference files (responsibilities, templates)
- Files outside document lifecycle system
- Common content shared across prompts

**Use @doc: for:**
- Managed documents (stories, PRDs, architecture)
- Documents with metadata and versioning
- Documents in lifecycle system

---

## Nested References

### Level 1: Simple Nesting

```yaml
# prompt.yaml
user_prompt: |
  Story Requirements:
  @doc:stories/epic-1/story-1.1.md

# stories/epic-1/story-1.1.md contains:
Epic Context:
@context:epic_definition
```

**What Happens:**
1. Document resolver loads story file
2. Story content contains `@context:epic_definition`
3. Context resolver resolves epic context
4. Both injected into final prompt

### Level 2: Deeper Nesting

```yaml
# prompt.yaml
user_prompt: |
  Epic Definition:
  @context:epic_definition

# Epic definition contains:
Related PRD:
@doc:features/sandbox-system/PRD.md

# PRD.md contains:
Architecture Reference:
@doc:features/sandbox-system/ARCHITECTURE.md
```

**What Happens:**
1. Context resolver loads epic definition
2. Epic contains `@doc:PRD.md`
3. Document resolver loads PRD
4. PRD contains `@doc:ARCHITECTURE.md`
5. Document resolver loads architecture
6. All three levels injected

### Max Depth Protection

```yaml
# Prevents infinite loops
max_depth: 3  # Default in MetaPromptEngine
```

If nesting exceeds max depth:
```
CircularReferenceError: Maximum nesting depth (3) exceeded.
Possible circular reference.
```

---

## Automatic Context Injection

### Configuration

```yaml
# gao_dev/config/auto_injection.yaml

implement_story:
  story_definition: "@doc:stories/epic-{{epic}}/story-{{story}}.md"
  epic_definition: "@context:epic_definition"
  architecture: "@context:architecture"
  testing_standards: "@checklist:testing/unit-test-standards"

create_story:
  epic_definition: "@context:epic_definition"
  prd: "@context:prd"
  related_stories: "@query:stories.where(epic={{epic}}, status='done').format('list')"
```

### Usage in Prompt

```yaml
name: implement_story_auto
version: 2.0.0

user_prompt: |
  Implement Story {{epic}}.{{story}}.

  # No references needed here!
  # All context auto-injected based on workflow_name

  Follow these steps:
  1. Read story requirements (auto-injected above)
  2. Review architecture (auto-injected above)
  3. Implement following standards (auto-injected above)
  4. Write tests

variables:
  epic: "1"
  story: "1"
  feature: ""

meta_prompts:
  enabled: true
```

### Code Usage

```python
engine = MetaPromptEngine(
    prompt_loader=prompt_loader,
    resolver_registry=resolver_registry,
    auto_injection_config=Path("gao_dev/config/auto_injection.yaml")
)

rendered = engine.render_prompt(
    template,
    variables={"epic": 1, "story": 1, "feature": "sandbox"},
    workflow_name="implement_story"  # Triggers auto-injection!
)
```

**Result:**
- `story_definition` auto-injected
- `epic_definition` auto-injected
- `architecture` auto-injected
- `testing_standards` auto-injected
- All without explicit references in prompt

---

## Advanced Patterns

### Pattern 1: Conditional Context

```yaml
user_prompt: |
  Implement {{feature_type}} feature.

  {% if feature_type == 'api' %}
  API Standards:
  @context:api_standards
  {% endif %}

  {% if feature_type == 'ui' %}
  UI Guidelines:
  @context:ui_guidelines
  {% endif %}

variables:
  feature_type: "api"

meta_prompts:
  enabled: true
```

### Pattern 2: Reference Composition

```yaml
user_prompt: |
  Complete feature development:

  Requirements:
  @doc:features/{{feature}}/PRD.md#requirements

  Architecture:
  @doc:features/{{feature}}/ARCHITECTURE.md#overview

  Stories:
  @query:stories.where(feature={{feature}}, status='todo').format('list')

  Standards:
  @checklist:code-quality/solid-principles

variables:
  feature: "sandbox-system"

meta_prompts:
  enabled: true
```

### Pattern 3: Reference in Variables

```yaml
user_prompt: |
  {{instructions}}

variables:
  instructions: "@doc:instructions/{{task_type}}.md"
  task_type: "implementation"

meta_prompts:
  enabled: true
```

**Note:** Variables are resolved before references, so references in variables work!

### Pattern 4: Dynamic Reference Selection

```yaml
user_prompt: |
  Use appropriate checklist:

  {% if story_type == 'feature' %}
  @checklist:testing/feature-checklist
  {% elif story_type == 'bugfix' %}
  @checklist:testing/bugfix-checklist
  {% else %}
  @checklist:testing/default-checklist
  {% endif %}

variables:
  story_type: "feature"

meta_prompts:
  enabled: true
```

---

## Real-World Examples

### Example 1: Story Implementation Prompt

```yaml
name: implement_story_complete
version: 2.0.0
description: "Complete story implementation with all context"

user_prompt: |
  Implement Story {{epic}}.{{story}} for feature '{{feature}}'.

  ## Story Requirements
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

  ## Acceptance Criteria
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md#acceptance-criteria

  ## Epic Context
  @context:epic_definition

  ## Architecture Guidelines
  @context:architecture

  ## Coding Standards
  @context:coding_standards

  ## Quality Checklists

  Unit Testing:
  @checklist:testing/unit-test-standards

  SOLID Principles:
  @checklist:code-quality/solid-principles

  Code Review:
  @checklist:code-quality/code-review-checklist

  ## Related Work

  Completed Stories:
  @query:stories.where(epic={{epic}}, status='done').format('list')

  ## Implementation Steps

  1. Review all context above
  2. Create feature branch: feature/epic-{{epic}}-story-{{story}}
  3. Write tests first (TDD approach)
  4. Implement functionality
  5. Run tests and verify all acceptance criteria met
  6. Self-review against checklists
  7. Commit with conventional commit message

  Report progress at each step.

variables:
  epic: "1"
  story: "1"
  feature: "sandbox-system"

response:
  max_tokens: 8000
  temperature: 0.7

metadata:
  category: implementation
  phase: development

meta_prompts:
  enabled: true
```

**Benefits:**
- Complete context in one prompt
- No hardcoded content
- Always up-to-date
- Comprehensive quality standards
- Awareness of related work

### Example 2: Code Review Prompt

```yaml
name: code_review_comprehensive
version: 2.0.0
description: "Comprehensive code review with standards"

user_prompt: |
  Review code for Story {{epic}}.{{story}}.

  ## Story Requirements
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md

  ## Acceptance Criteria (Must All Be Met)
  @doc:stories/epic-{{epic}}/story-{{epic}}.{{story}}.md#acceptance-criteria

  ## Code Quality Standards

  SOLID Principles:
  @checklist:code-quality/solid-principles

  DRY Principle:
  @checklist:code-quality/dry-principle

  Type Safety:
  @checklist:code-quality/type-safety

  Error Handling:
  @checklist:code-quality/error-handling

  ## Testing Standards

  Unit Tests:
  @checklist:testing/unit-test-standards

  Integration Tests:
  @checklist:testing/integration-test-standards

  ## Architecture Compliance
  @context:architecture

  ## Review Checklist
  @checklist:code-quality/code-review-checklist

  ## Instructions

  For each checklist item:
  - Indicate PASS or FAIL
  - If FAIL, provide specific examples and recommendations
  - Reference architecture where relevant
  - Verify acceptance criteria met

  Provide summary: APPROVED / CHANGES REQUESTED

variables:
  epic: "1"
  story: "1"
  feature: "sandbox-system"

response:
  max_tokens: 6000
  temperature: 0.7

metadata:
  category: review
  phase: validation

meta_prompts:
  enabled: true
```

### Example 3: Epic Planning Prompt

```yaml
name: plan_epic
version: 2.0.0
description: "Plan epic with context and analysis"

user_prompt: |
  Plan Epic {{epic}} for feature '{{feature}}'.

  ## PRD Context
  @context:prd

  ## Architecture Context
  @context:architecture

  ## Existing Epics (For Context)
  @query:documents.where(type='epic', feature={{feature}}).format('list')

  ## Completed Stories (Learn From)
  @query:stories.where(feature={{feature}}, status='done').format('detailed')

  ## Story Template
  @doc:templates/story.md.j2

  ## Planning Instructions

  1. Review PRD and architecture above
  2. Review existing epics and completed stories
  3. Break epic into 5-15 stories
  4. Use story template for structure
  5. Estimate story points (1, 2, 3, 5, 8, 13)
  6. Identify dependencies
  7. Create epic document

  ## Epic Document Should Include

  - Epic overview and goals
  - Success criteria
  - Story breakdown with estimates
  - Dependency graph
  - Risk assessment
  - Timeline estimate

variables:
  epic: "1"
  feature: "sandbox-system"

response:
  max_tokens: 8000
  temperature: 0.7

metadata:
  category: planning
  phase: epic-planning

meta_prompts:
  enabled: true
```

---

## Performance Tips

### 1. Use Caching

```python
# Resolvers cache automatically
resolver_registry = ReferenceResolverRegistry(cache_enabled=True)
```

### 2. Batch Common References

```yaml
# Define once, reference multiple times
common_context: |
  @context:architecture
  @context:coding_standards

user_prompt: |
  {{common_context}}

  Implement feature...
```

### 3. Avoid Redundant References

**Bad:**
```yaml
@doc:stories/epic-1/story-1.1.md
@doc:stories/epic-1/story-1.1.md#acceptance-criteria
@doc:stories/epic-1/story-1.1.md#technical-notes
```

**Good:**
```yaml
@doc:stories/epic-1/story-1.1.md
# File loaded once, sections extracted efficiently
```

### 4. Use Auto-Injection for Common Patterns

Instead of repeating references:
```yaml
# Every story implementation needs these
@context:epic_definition
@context:architecture
@checklist:testing/unit-test-standards
```

Configure auto-injection:
```yaml
# auto_injection.yaml
implement_story:
  epic_definition: "@context:epic_definition"
  architecture: "@context:architecture"
  testing_standards: "@checklist:testing/unit-test-standards"
```

---

## Common Pitfalls

### Pitfall 1: Forgetting meta_prompts.enabled

**Problem:**
```yaml
user_prompt: |
  @doc:file.md  # Appears literally in output

# Missing:
meta_prompts:
  enabled: true
```

### Pitfall 2: Circular References

**Problem:**
```yaml
# File A:
@doc:fileB.md

# File B:
@doc:fileA.md

# Result: CircularReferenceError
```

### Pitfall 3: Invalid Reference Syntax

**Wrong:**
```yaml
@ doc:file.md           # Space after @
@doc :file.md           # Space before :
@doc: file.md           # Space after :
@doc:file with spaces.md  # Spaces in path
```

**Correct:**
```yaml
@doc:file.md
@doc:path/to/file.md
@doc:stories/epic-{{epic}}/story.md
```

### Pitfall 4: Missing Feature Variable

**Problem:**
```yaml
@context:epic_definition  # Needs feature to resolve

variables:
  # Missing: feature: ""
```

**Solution:**
```yaml
variables:
  feature: "sandbox-system"  # Required for context resolution
```

---

## Quick Reference

### Reference Type Summary

| Type | Purpose | Example | Resolver |
|------|---------|---------|----------|
| @doc: | Load managed document | `@doc:stories/epic-1/story-1.1.md` | DocumentReferenceResolver |
| @context: | Load from context registry | `@context:epic_definition` | ContextReferenceResolver |
| @checklist: | Load quality checklist | `@checklist:testing/unit-test-standards` | ChecklistReferenceResolver |
| @query: | Query document database | `@query:stories.where(epic=1).format('list')` | QueryReferenceResolver |
| @config: | Load configuration value | `@config:scale_levels` | ConfigReferenceResolver |
| @file: | Load static file (Epic 10) | `@file:common/responsibilities.md` | FileReferenceResolver |

### Syntax Rules

- No spaces around `:` in reference
- Variables work: `{{epic}}`, `{{story}}`
- Section syntax: `#section-name`
- Query methods: `.where()`, `.format()`
- Nesting supported (max depth: 3)

---

## Resources

- **Migration Guide**: `docs/MIGRATION_GUIDE_EPIC_13.md`
- **Story Spec**: `docs/features/document-lifecycle-system/stories/epic-13/story-13.6.md`
- **Code**: `gao_dev/core/meta_prompts/`
- **Tests**: `tests/core/meta_prompts/`
- **Updated Prompts**: `gao_dev/prompts/`

---

**Last Updated:** 2025-11-05
**Epic:** 13 - Meta-Prompt System & Context Injection
**Story:** 13.6 - Update Core Prompts to Use Meta-Prompts
