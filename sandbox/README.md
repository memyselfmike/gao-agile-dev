# GAO-Dev Sandbox Workspace

This directory is the **testing workspace** for GAO-Dev autonomous capabilities.

## Purpose

The sandbox is where we:
- Run benchmark tests
- Create test projects autonomously
- Measure GAO-Dev's performance
- Validate autonomous workflows

**Important**: This directory does NOT contain documentation about the sandbox system itself.
For sandbox system documentation, see `docs/features/sandbox-system/`

## Structure

```
sandbox/
├── README.md              # This file
├── gao-dev.yaml           # Sandbox workspace config
├── benchmarks/            # Benchmark configuration files
│   └── todo-baseline.yaml # Example: Todo app benchmark
└── projects/              # Test projects (created by benchmarks)
    └── todo-app-run-001/  # Example: Autonomous project creation
        ├── docs/          # Agents create these autonomously
        │   ├── PRD.md
        │   ├── architecture.md
        │   └── stories/
        ├── src/           # Implementation
        └── tests/         # Tests
```

## How It Works

### 1. Define Benchmark
Create a benchmark config in `benchmarks/`:

```yaml
# benchmarks/todo-baseline.yaml
benchmark:
  name: "todo-app-baseline"
  initial_prompt: "Build a todo application with auth..."
  tech_stack:
    frontend: "nextjs"
    backend: "nextjs-api-routes"
```

### 2. Run Benchmark
```bash
gao-dev sandbox run benchmarks/todo-baseline.yaml
```

### 3. Agents Work Autonomously
The system will:
- Initialize project in `projects/todo-app-run-001/`
- Spawn agents (Mary, John, Winston, Sally, Bob, Amelia, Murat)
- Agents create docs/, write code, run tests
- Metrics collected throughout

### 4. Review Results
```bash
gao-dev sandbox report <run-id>
```

## What Gets Created by Agents

When a benchmark runs, agents autonomously create:
- `docs/PRD.md` - Product requirements (John)
- `docs/architecture.md` - System design (Winston)
- `docs/stories/` - User stories (Bob)
- `src/` - Implementation (Amelia)
- `tests/` - Test suite (Murat)
- All commits and branches (via Git tools)

**This validates that GAO-Dev can build complete applications autonomously!**

## Benchmark Metrics

Each run tracks:
- **Performance**: Time, tokens, cost
- **Autonomy**: Interventions, one-shot success rate
- **Quality**: Coverage, errors, completeness
- **Workflow**: Story cycle time, handoffs

## Important Notes

### This is NOT for:
- ❌ Documenting the sandbox system (use `docs/features/sandbox-system/`)
- ❌ Developing GAO-Dev features (use main project structure)
- ❌ Permanent projects (these are test runs)

### This IS for:
- ✅ Testing autonomous workflows
- ✅ Benchmarking performance
- ✅ Validating end-to-end capabilities
- ✅ Measuring improvement over time

## Cleanup

Projects in `sandbox/projects/` can be deleted after benchmarks complete.
Metrics are stored separately and persist.

```bash
# Clean up old test projects
gao-dev sandbox clean todo-app-run-001
```

---

**For sandbox system documentation, see**: `docs/features/sandbox-system/`
**For benchmark configs, see**: `benchmarks/`
**For test project outputs, see**: `projects/`
