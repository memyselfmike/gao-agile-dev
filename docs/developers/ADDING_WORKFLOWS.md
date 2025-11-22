# Developer Guide: Adding Workflows to GAO-Dev

## TL;DR

**What**: Step-by-step guide to creating new workflows in the GAO-Dev system

**When**: Adding new autonomous agent capabilities, new development processes, or new ceremonies

**Key Steps**:
1. Create workflow directory under appropriate phase (1-5)
2. Write `workflow.yaml` with metadata and variables
3. Create `template.md` with agent instructions
4. Test with `gao-dev list-workflows` and execution
5. Document in workflow catalog

**Time**: 30-60 minutes for simple workflow, 2-4 hours for complex

---

## Table of Contents

- [Overview](#overview)
- [Workflow Structure](#workflow-structure)
- [Step-by-Step Guide](#step-by-step-guide)
- [Workflow YAML Schema](#workflow-yaml-schema)
- [Template Creation](#template-creation)
- [Variable Resolution](#variable-resolution)
- [Testing Your Workflow](#testing-your-workflow)
- [Common Patterns](#common-patterns)
- [Examples](#examples)

---

## Overview

### What is a Workflow?

A **workflow** in GAO-Dev is a reusable, autonomous agent task definition. Workflows:
- Define what an agent should do
- Specify required variables and tools
- Include prompt templates with variable substitution
- Auto-register when placed in `gao_dev/workflows/`
- Support both CLI and Web UI execution

### Workflow Phases

Workflows are organized by **SDLC phase**:

| Phase | Directory | Purpose | Example Workflows |
|-------|-----------|---------|-------------------|
| **1** | `1-analysis/` | Requirements, vision, brainstorming | vision-elicitation, requirements-analysis |
| **2** | `2-plan/` | PRDs, specifications | prd, tech-spec |
| **3** | `3-solutioning/` | Architecture, design | architecture, design-patterns |
| **4** | `4-implementation/` | Story creation, development | create-story, dev-story, story-done |
| **5** | `5-ceremonies/` | Agile ceremonies | planning-ceremony, retrospective, standup |

---

## Workflow Structure

### Directory Layout

```
gao_dev/workflows/
└── {phase}-{phase-name}/
    └── {workflow-name}/
        ├── workflow.yaml          # Required: Workflow metadata
        ├── template.md            # Required: Agent prompt template
        ├── additional-context.md  # Optional: Extra context
        └── examples/              # Optional: Example outputs
            └── example-1.md
```

### Minimal Workflow

A minimal workflow requires **two files**:

1. **workflow.yaml** - Metadata and configuration
2. **template.md** - Agent instructions

---

## Step-by-Step Guide

### Step 1: Create Workflow Directory

```bash
# Choose appropriate phase directory
cd gao_dev/workflows/

# Create workflow directory
mkdir -p 2-plan/my-new-workflow
cd 2-plan/my-new-workflow
```

### Step 2: Create workflow.yaml

```yaml
name: my-new-workflow
description: Brief description of what this workflow does
phase: 2
author: AgentName (Agent Role)
non_interactive: false
autonomous: true
iterative: false
web_bundle: false

variables:
  project_name:
    description: Project name
    type: string
    required: true
  output_location:
    description: Path to output file
    type: string
    default: "docs/output.md"

required_tools:
  - write_file
  - read_file

output_file: "{{output_location}}"

templates:
  main: template.md
```

### Step 3: Create template.md

```markdown
# Task: {{workflow_description}}

## Context

You are {{agent}} working on {{project_name}}.

## Objective

Create a comprehensive document that achieves [specific goal].

## Requirements

1. Requirement 1
2. Requirement 2
3. Requirement 3

## Output Format

Create a markdown document with the following structure:

### Section 1
[Content guidelines]

### Section 2
[Content guidelines]

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Output Location

Write the final document to: `{{output_location}}`
```

### Step 4: Test Your Workflow

```bash
# Verify workflow is discovered
gao-dev list-workflows | grep my-new-workflow

# Test execution (dry run)
gao-dev execute-workflow my-new-workflow --dry-run

# Execute workflow
gao-dev execute-workflow my-new-workflow \
  --var project_name="Test Project" \
  --var output_location="docs/test-output.md"
```

### Step 5: Verify Output

```bash
# Check that output file was created
ls -la docs/test-output.md

# Review content
cat docs/test-output.md
```

---

## Workflow YAML Schema

### Complete Schema

```yaml
# Required fields
name: string                    # Workflow identifier (kebab-case)
description: string             # Brief description (1-2 sentences)
phase: integer                  # SDLC phase (1-5)

# Agent assignment
author: string                  # Agent name (e.g., "John (Product Manager)")
agent: string                   # Alternative to 'author' for ceremonies

# Execution mode
non_interactive: boolean        # If true, no user prompts (default: false)
autonomous: boolean             # If true, agent works autonomously (default: true)
iterative: boolean              # If true, supports multiple iterations (default: false)
web_bundle: boolean            # If true, designed for web UI execution (default: false)

# Variables
variables:                      # Input variables with validation
  variable_name:
    description: string         # Variable description
    type: string               # Data type: string, integer, boolean, array
    required: boolean          # If true, must be provided
    default: any               # Default value if not provided
    validation:                # Optional validation rules
      pattern: string          # Regex pattern
      min_length: integer      # Minimum string length
      max_length: integer      # Maximum string length

# Tool requirements
required_tools:                 # List of tools agent needs
  - tool_name                  # e.g., write_file, read_file, search

# Output configuration
output_file: string            # Path template for output (with variables)
output_files:                  # Multiple output files
  - path: string
    description: string

# Template configuration
templates:
  main: string                 # Main template file (required)
  additional: string           # Optional additional templates
  context: string             # Optional context file

# Categorization (optional)
tags:                          # List of tags for filtering
  - tag1
  - tag2
category: string               # Workflow category (e.g., "ceremonies")

# Metadata (for ceremonies)
metadata:
  ceremony_type: string        # Type of ceremony
  participants: array          # Required participant roles
  duration: string            # Expected duration
  artifacts: array            # Artifacts produced
```

### Field Descriptions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | ✅ | string | Unique workflow identifier (use kebab-case) |
| `description` | ✅ | string | What the workflow does (1-2 sentences) |
| `phase` | ✅ | integer | SDLC phase (1=Analysis, 2=Plan, 3=Solution, 4=Implementation, 5=Ceremonies) |
| `author` / `agent` | ✅ | string | Agent responsible (use `agent` for ceremonies) |
| `non_interactive` | ❌ | boolean | Default: false. Set true for fully autonomous workflows |
| `autonomous` | ❌ | boolean | Default: true. If false, requires human intervention |
| `iterative` | ❌ | boolean | Default: false. Set true for workflows that can iterate |
| `web_bundle` | ❌ | boolean | Default: false. Set true for web UI optimized workflows |
| `variables` | ❌ | object | Input variables with validation |
| `required_tools` | ❌ | array | Tools the agent needs (e.g., write_file, search) |
| `output_file` | ❌ | string | Single output file path with variable substitution |
| `templates` | ✅ | object | Template files (must have `main`) |
| `tags` | ❌ | array | Tags for workflow filtering |
| `category` | ❌ | string | Workflow category (e.g., "ceremonies") |

---

## Template Creation

### Template Basics

Templates are **markdown files** with **variable substitution**:

```markdown
# {{project_name}} - {{workflow_description}}

Created by {{agent}} on {{date}}.

## Task

Complete the following for {{project_name}}:
- Step 1
- Step 2
- Step 3

Output to: {{output_location}}
```

### Available Variables

**Common variables** (auto-provided):

| Variable | Description | Example |
|----------|-------------|---------|
| `{{date}}` | Current date | "2025-01-16" |
| `{{timestamp}}` | Current timestamp | "2025-01-16T10:30:00Z" |
| `{{project_name}}` | Project name | "my-app" |
| `{{project_root}}` | Project root path | "/path/to/project" |
| `{{agent}}` | Current agent name | "John (Product Manager)" |
| `{{workflow}}` | Workflow name | "create-prd" |

**Custom variables** (defined in workflow.yaml):

```yaml
variables:
  feature_name:
    description: Name of the feature
    type: string
    required: true
```

Usage in template:
```markdown
# {{feature_name}} Implementation Plan
```

### Template Best Practices

1. **Be Specific**: Provide clear, actionable instructions
2. **Use Examples**: Show agent what good output looks like
3. **Include Success Criteria**: Define what "done" means
4. **Specify Format**: Tell agent exact output structure
5. **Reference Context**: Link to relevant docs or examples

**Good template**:
```markdown
## Objective

Create a Product Requirements Document for {{feature_name}}.

## Output Structure

Use this exact structure:

### 1. Executive Summary
[2-3 sentences describing the feature]

### 2. User Stories
As a [user type], I want [goal] so that [benefit].

### 3. Success Metrics
- Metric 1: [Measurable outcome]
- Metric 2: [Measurable outcome]

## Examples

See docs/examples/prd-example.md for a complete example.

## Output

Write the PRD to {{output_location}}.
```

**Bad template**:
```markdown
Create a document about {{feature_name}}.
```

---

## Variable Resolution

### Resolution Priority

Variables are resolved in this order (highest to lowest):

1. **Runtime parameters** (passed via CLI or API)
2. **Workflow YAML defaults** (defined in workflow.yaml)
3. **Config defaults** (from gao_dev/config/defaults.yaml)
4. **Common variables** (auto-generated: date, timestamp, etc.)

### Example

```yaml
# workflow.yaml
variables:
  output_location:
    default: "docs/PRD.md"
```

```bash
# CLI execution - runtime parameter overrides default
gao-dev execute-workflow my-workflow \
  --var output_location="custom/path/document.md"

# Result: output_location = "custom/path/document.md"
```

---

## Testing Your Workflow

### 1. List Workflows

```bash
# Verify workflow is discovered
gao-dev list-workflows

# Filter by phase
gao-dev list-workflows --phase 2

# Search by name
gao-dev list-workflows | grep my-workflow
```

### 2. Dry Run

```bash
# Test without executing
gao-dev execute-workflow my-workflow --dry-run \
  --var project_name="Test"
```

### 3. Execute with Test Data

```bash
# Run with minimal test data
gao-dev execute-workflow my-workflow \
  --var project_name="Test Project" \
  --var output_location="/tmp/test-output.md"
```

### 4. Validate Output

```bash
# Check file was created
test -f /tmp/test-output.md && echo "Success" || echo "Failed"

# Review content
cat /tmp/test-output.md

# Check variable substitution
grep "Test Project" /tmp/test-output.md
```

### 5. Integration Test

```python
# tests/workflows/test_my_workflow.py
import pytest
from pathlib import Path
from gao_dev.core.workflow_executor import WorkflowExecutor

def test_my_workflow_execution(tmp_path):
    """Test my-workflow produces expected output."""
    output_file = tmp_path / "output.md"

    executor = WorkflowExecutor()
    result = executor.execute(
        workflow_name="my-workflow",
        variables={
            "project_name": "Test",
            "output_location": str(output_file)
        }
    )

    assert result.success
    assert output_file.exists()
    content = output_file.read_text()
    assert "Test" in content
```

---

## Common Patterns

### Pattern 1: Simple Document Generation

```yaml
name: generate-document
description: Generate a simple document
phase: 2
author: AgentName
autonomous: true

variables:
  document_type:
    description: Type of document
    type: string
    required: true
  output_path:
    description: Output path
    type: string
    default: "docs/{{document_type}}.md"

required_tools:
  - write_file

output_file: "{{output_path}}"

templates:
  main: template.md
```

### Pattern 2: Multi-File Workflow

```yaml
name: create-feature-suite
description: Create complete feature with tests
phase: 4
author: Amelia (Developer)
autonomous: true

variables:
  feature_name:
    description: Feature name
    type: string
    required: true

required_tools:
  - write_file
  - read_file

output_files:
  - path: "src/features/{{feature_name}}.py"
    description: Feature implementation
  - path: "tests/features/test_{{feature_name}}.py"
    description: Feature tests
  - path: "docs/features/{{feature_name}}.md"
    description: Feature documentation

templates:
  main: implementation-template.md
  test: test-template.md
  docs: docs-template.md
```

### Pattern 3: Iterative Workflow

```yaml
name: refine-architecture
description: Iteratively refine architecture document
phase: 3
author: Winston (Architect)
autonomous: true
iterative: true

variables:
  architecture_doc:
    description: Path to architecture document
    type: string
    default: "docs/ARCHITECTURE.md"
  iteration:
    description: Iteration number
    type: integer
    default: 1

required_tools:
  - read_file
  - write_file

output_file: "{{architecture_doc}}"

templates:
  main: refine-template.md
```

### Pattern 4: Ceremony Workflow

```yaml
name: sprint-planning
description: Facilitate sprint planning ceremony
phase: 5
agent: Bob (Scrum Master)
autonomous: true
category: ceremonies

variables:
  epic_number:
    description: Epic number for sprint
    type: integer
    required: true

metadata:
  ceremony_type: sprint-planning
  participants:
    - Bob (Scrum Master)
    - Brian (Workflow Coordinator)
    - Amelia (Developer)
  duration: "2 hours"
  artifacts:
    - Sprint backlog
    - Sprint goals

templates:
  main: ceremony-template.md
```

---

## Examples

### Example 1: Simple Workflow

**Directory**: `gao_dev/workflows/2-plan/user-story/`

**workflow.yaml**:
```yaml
name: user-story
description: Create user story from requirement
phase: 2
author: Bob (Scrum Master)
autonomous: true

variables:
  requirement:
    description: Requirement description
    type: string
    required: true
  story_location:
    description: Path to story file
    type: string
    default: "docs/stories/story-{{epic}}.{{story}}.md"

required_tools:
  - write_file

output_file: "{{story_location}}"

templates:
  main: template.md
```

**template.md**:
```markdown
# User Story: {{requirement}}

## Story Details

**As a** [user type]
**I want** [capability]
**So that** [benefit]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes

[Implementation guidance]

## Testing

[Test scenarios]

---

**Created**: {{date}}
**Author**: {{agent}}
```

### Example 2: Complex Workflow with Context

**Directory**: `gao_dev/workflows/3-solutioning/api-design/`

**workflow.yaml**:
```yaml
name: api-design
description: Design RESTful API for feature
phase: 3
author: Winston (Architect)
autonomous: true

variables:
  feature_name:
    description: Feature name
    type: string
    required: true
  api_version:
    description: API version
    type: string
    default: "v1"

required_tools:
  - write_file
  - read_file

output_file: "docs/api/{{feature_name}}-api.md"

templates:
  main: api-template.md
  context: api-design-patterns.md
```

**api-template.md**:
```markdown
# API Design: {{feature_name}}

**Version**: {{api_version}}
**Date**: {{date}}
**Architect**: {{agent}}

---

## Endpoints

### 1. Create {{feature_name}}

**Endpoint**: `POST /api/{{api_version}}/{{feature_name}}`

**Request**:
```json
{
  "field1": "value",
  "field2": "value"
}
```

**Response**:
```json
{
  "id": "uuid",
  "status": "created"
}
```

[Continue with more endpoints...]

---

## See Also

For API design patterns, see: api-design-patterns.md
```

---

## See Also

- [Quick Start Guide](../QUICK_START.md) - Integration patterns
- [API Reference](../API_REFERENCE.md) - Complete API catalog
- [Variable Resolution Guide](../features/document-lifecycle-system/VARIABLE_RESOLUTION.md) - Detailed variable resolution
- [Testing Guide](TESTING_GUIDE.md) - Testing patterns for GAO-Dev

**Estimated tokens**: ~2,400
