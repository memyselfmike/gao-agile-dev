# SimpleMethodology

A minimal alternative methodology demonstrating IMethodology implementation.

## Overview

SimpleMethodology is intentionally simple to show how custom methodologies can be created. It uses:
- 3 complexity levels (SMALL, MEDIUM, LARGE)
- Keyword-based analysis (no AI)
- Linear workflows
- Simple agent recommendations

## When to Use

- Small projects that don't need AdaptiveAgile complexity
- Learning how to create custom methodologies
- Template for your own methodology
- Fast, deterministic complexity assessment

## Complexity Levels

| Level | Duration | Description | Workflow |
|-------|----------|-------------|----------|
| TRIVIAL/SMALL | Hours | Quick tasks, bug fixes | Implement only |
| MEDIUM | Days | Features with planning | Plan → Implement → Test |
| LARGE/XLARGE | Weeks | Projects with design | Design → Plan → Implement → Test |

## Usage

```python
from gao_dev.methodologies.registry import MethodologyRegistry
from gao_dev.methodologies.simple import SimpleMethodology

# Register SimpleMethodology
registry = MethodologyRegistry.get_instance()
registry.register_methodology(SimpleMethodology())

# Get SimpleMethodology
simple = registry.get_methodology("simple")

# Use it
assessment = await simple.assess_complexity("Build a todo app")
# Returns MEDIUM complexity

workflows = simple.build_workflow_sequence(assessment)
# Returns: Plan → Implement → Test
```

## Keyword-Based Assessment

SimpleMethodology uses simple keyword matching to determine complexity:

**LARGE indicators** (maps to XLARGE):
- application, system, platform, full stack
- greenfield, from scratch, entire, complete

**SMALL indicators** (maps to TRIVIAL):
- fix, bug, typo, update, change, quick
- simple, minor, small

**Default**: MEDIUM (for features)

## Agent Recommendations

SimpleMethodology provides simple phase-based agent recommendations:

- **Design phase**: Architect
- **Planning phase**: Planner
- **Implementation phase**: Developer
- **Testing phase**: Tester
- **Default**: Developer

## Creating Your Own Methodology

Use SimpleMethodology as a template:

1. Copy `simple/` directory to `methodologies/your_methodology/`
2. Implement IMethodology interface methods:
   - `assess_complexity()` - Your assessment logic
   - `build_workflow_sequence()` - Your workflow structure
   - `get_recommended_agents()` - Your agent selection
   - `validate_config()` - Your config validation
3. Set methodology properties (name, description, version)
4. Write tests
5. Register in MethodologyRegistry

## Comparison with AdaptiveAgileMethodology

| Feature | SimpleMethodology | AdaptiveAgileMethodology |
|---------|-------------------|-------------------------|
| Complexity Levels | 3 (SMALL, MEDIUM, LARGE) | 5 (0-4 scale levels) |
| Assessment | Keyword matching | Keyword matching |
| Workflows | Linear, 1-4 steps | Scale-adaptive, complex |
| Agent Recommendations | Simple phase-based | Specialized 7-agent team |
| Scale Levels | Not supported | Full support |
| Use Case | Simple projects | Full project lifecycle |
| Code Size | ~200 lines | ~500+ lines |

## Example Assessments

```python
# SMALL/TRIVIAL
await simple.assess_complexity("Fix login bug")
# → TRIVIAL complexity, 1 workflow (implement)

# MEDIUM
await simple.assess_complexity("Add user profile page")
# → MEDIUM complexity, 3 workflows (plan, implement, test)

# LARGE
await simple.assess_complexity("Build a complete e-commerce platform")
# → XLARGE complexity, 4 workflows (design, plan, implement, test)
```

## Benefits

- **Fast**: No AI calls, instant assessment
- **Deterministic**: Same input = same output
- **Lightweight**: Minimal code, easy to understand
- **Template**: Perfect starting point for custom methodologies
- **No Dependencies**: No external API requirements

## Limitations

- Less sophisticated than AdaptiveAgile
- No AI-based analysis
- Simpler workflow structures
- Generic agent recommendations

## See Also

- `docs/methodology-development-guide.md` - Full guide to creating methodologies
- `gao_dev/core/interfaces/methodology.py` - IMethodology interface
- `gao_dev/methodologies/adaptive_agile/` - Full-featured methodology example
