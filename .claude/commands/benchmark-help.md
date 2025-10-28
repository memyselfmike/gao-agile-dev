---
description: Show benchmark command quick reference
---

# GAO-Dev Benchmarking Quick Reference

## Available Slash Commands

**Project Management:**
- `/sandbox-init` - Initialize a new sandbox project
- `/sandbox-list` - List all sandbox projects
- `/sandbox-clean` - Clean/reset a sandbox project
- `/sandbox-status` - Check sandbox system status

**Benchmark Operations:**
- `/list-benchmarks` - List available benchmark configs
- `/run-benchmark` - Execute a benchmark run
- `/benchmark-report` - Generate or view benchmark reports
- `/benchmark-compare` - Compare two benchmark runs

## Quick Start

1. **Create a test project:**
   ```bash
   /sandbox-init
   ```

2. **See available benchmarks:**
   ```bash
   /list-benchmarks
   ```

3. **Run a benchmark:**
   ```bash
   /run-benchmark
   ```

4. **View results:**
   ```bash
   /benchmark-report
   ```

## Important Notes

- **API Key Required**: Benchmarks need `ANTHROPIC_API_KEY` environment variable
- **Story-Based Mode**: Fully autonomous, spawns agents (Epic 6+ feature)
- **Phase-Based Mode**: Legacy waterfall workflow
- **Git Integration**: All projects have automatic git commits per story
- **Reports**: HTML reports with charts available in `sandbox/reports/`

## Benchmark Configs Location

All benchmark YAML files are in: `sandbox/benchmarks/`

## Example Benchmarks

- `todo-app-incremental.yaml` - Full story-based todo app (4 epics, 13 stories)
- `todo-app-baseline.yaml` - Phase-based todo app (legacy mode)
- `simple-api-baseline.yaml` - Simple REST API benchmark

## Metrics Tracked

- **Performance**: Time, tokens, API calls
- **Quality**: Test coverage, type safety, code quality
- **Autonomy**: Manual interventions, error recovery
- **Workflow**: Story completion, commit history

For detailed help on any command, just run it and follow the prompts!
