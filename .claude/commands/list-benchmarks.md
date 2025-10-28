---
description: List available benchmark configurations
---

List all available benchmark configuration files.

Run these commands:

```bash
cd "D:\GAO Agile Dev"
echo "=== Available Benchmark Configs ==="
ls -lh sandbox/benchmarks/*.yaml 2>/dev/null || echo "No benchmark configs found"
echo ""
echo "=== Benchmark Details ==="
```

Then read and summarize each benchmark config file found in `sandbox/benchmarks/`, showing:
- Benchmark name
- Project type (e.g., todo-app, simple-api)
- Workflow mode (story-based or phase-based)
- Number of epics/phases
- Total story points (if story-based)
- Estimated duration

Provide recommendations on which benchmark to run based on complexity.
