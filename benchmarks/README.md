# GAO-Dev Benchmark Configurations

This directory contains standardized benchmark configurations for testing and measuring GAO-Dev's autonomous capabilities.

## Purpose

Benchmark configurations ensure **consistent, reproducible testing** by:
- Using the same initial prompt every time
- Defining clear success criteria
- Tracking metrics consistently
- Enabling meaningful comparison across runs

## Structure

```
benchmarks/
├── README.md                    # This file
├── todo-app-baseline.yaml       # Standard todo app benchmark
├── todo-app-minimal.yaml        # Simplified version for quick tests
├── simple-api-baseline.yaml     # Simpler benchmark for initial testing
└── templates/
    └── benchmark-template.yaml  # Template for creating new benchmarks
```

## Benchmark Levels

### Level 1: Simple API (30-60 min)
- **Complexity**: Low
- **Features**: Basic REST API with 2-3 endpoints
- **Purpose**: Quick validation, initial testing
- **Example**: `simple-api-baseline.yaml`

### Level 2: Todo App Minimal (1-2 hours)
- **Complexity**: Medium
- **Features**: Basic todo CRUD, no auth
- **Purpose**: Core functionality testing
- **Example**: `todo-app-minimal.yaml`

### Level 3: Todo App Baseline (2-4 hours)
- **Complexity**: High
- **Features**: Full-stack with auth, tests, deployment
- **Purpose**: Complete capability validation
- **Example**: `todo-app-baseline.yaml`

## Using Benchmarks

### Run a Benchmark
```bash
gao-dev sandbox init my-test-project
gao-dev sandbox run benchmarks/todo-app-baseline.yaml
```

### Create New Benchmark
1. Copy `templates/benchmark-template.yaml`
2. Fill in all required fields
3. Define standardized initial prompt
4. Set success criteria
5. Test the benchmark
6. Add to version control

## Standard Fields

Every benchmark must include:
- `name`: Unique identifier
- `description`: What this tests
- `version`: Semantic version
- `initial_prompt`: **Standardized prompt** (DO NOT MODIFY)
- `tech_stack`: Technologies to use
- `success_criteria`: Measurable goals
- `metrics_enabled`: What to track
- `timeout`: Maximum execution time

## Important: Initial Prompts

**DO NOT MODIFY** initial prompts in existing benchmarks without versioning!

If you need to change a prompt:
1. Create a new version (e.g., `todo-app-baseline-v2.yaml`)
2. Document the change in version history
3. Keep old version for comparison

This ensures historical runs remain comparable.

---

See individual benchmark files for specific configurations.
