# Autonomous Benchmark Execution Guide

## Overview

The GAO-Dev sandbox system now supports fully autonomous benchmark execution with comprehensive metrics tracking and verbose logging. This guide shows how to run complete end-to-end benchmarks that execute all work, not just foundation setup.

## Key Features

### 1. Full Autonomous Execution
- Spawns specialized agents using Anthropic API
- Agents work independently to complete entire phases
- NO manual orchestration - truly autonomous

### 2. Complete End-to-End Projects
- Benchmarks execute ALL epics and stories (e.g., 103 story points)
- Agents create production-ready, fully functional applications
- Quality gates ensure completion criteria are met

### 3. Comprehensive Metrics Tracking
- **Token usage**: Input tokens, output tokens, total tokens
- **Cost tracking**: Real-time cost estimation ($3/MTok input, $15/MTok output)
- **Time tracking**: Precise duration for each phase and agent
- **Tool calls**: Count of all tool invocations
- **Agent activity**: Detailed logs of all agent actions

### 4. Verbose Logging
- **Event log**: Timestamped log of all events (`{run_id}_verbose.log`)
- **Metrics report**: Complete JSON metrics (`{run_id}_metrics.json`)
- **Console summary**: Human-readable summary at completion

## System Architecture

```
BenchmarkRunner
    |
    +-- MetricsAggregator (tracks all metrics)
    |
    +-- WorkflowOrchestrator
            |
            +-- AgentSpawner (spawns agents with API)
                    |
                    +-- Anthropic Claude API
                            |
                            +-- Specialized Agents (Mary, John, Winston, Sally, Bob, Amelia, Murat)
```

## Agent Execution Flow

1. **BenchmarkRunner** initializes sandbox and metrics
2. **MetricsAggregator** starts logging all events
3. **WorkflowOrchestrator** manages phase execution
4. **AgentSpawner** spawns agent for each phase:
   - Loads agent persona from `gao_dev/agents/{agent}.md`
   - Constructs full prompt with task context
   - Calls Anthropic API with Claude Sonnet 4
   - Tracks tokens, cost, duration, tool calls
5. **MetricsAggregator** records all metrics
6. Final report generated with complete statistics

## Running a Benchmark

### Prerequisites

1. **Anthropic API Key**: Required for autonomous execution
   ```bash
   # Set environment variable
   export ANTHROPIC_API_KEY="sk-ant-..."  # Linux/Mac
   set ANTHROPIC_API_KEY=sk-ant-...       # Windows CMD
   $env:ANTHROPIC_API_KEY="sk-ant-..."   # Windows PowerShell
   ```

2. **Benchmark Configuration**: YAML file in `sandbox/benchmarks/`
   - Example: `todo-app-baseline.yaml`
   - Defines phases, agents, expected duration, success criteria

### Command

```bash
# Run benchmark with API key
gao-dev sandbox run todo-app-baseline --api-key $ANTHROPIC_API_KEY

# Or with environment variable
gao-dev sandbox run todo-app-baseline
```

### What Happens

The system will:

1. **Initialize**: Create sandbox project and metrics tracker
2. **Execute Phases**: Run each phase sequentially with specialized agent
   - Phase 1: Analysis (Mary) - Research and requirements
   - Phase 2: Planning (John) - PRD, epics, stories
   - Phase 3: Architecture (Winston) - Technical design
   - Phase 4: UX Design (Sally) - User flows, wireframes
   - Phase 5: Story Creation (Bob) - Detailed user stories
   - Phase 6: Implementation (Amelia) - ALL code, ALL tests
   - Phase 7: Quality Validation (Murat) - Full test suite, audits
3. **Track Metrics**: Log every tool call, token, and second
4. **Generate Report**: Create comprehensive metrics report

### Output Files

After benchmark completes:

```
sandbox/
├── metrics/
│   ├── {run_id}_verbose.log      # Timestamped event log
│   └── {run_id}_metrics.json     # Complete metrics report
└── projects/
    └── {project_name}/            # Completed project
        ├── docs/                   # All documentation
        ├── src/                    # All source code
        ├── tests/                  # All tests
        └── README.md               # Project README
```

## Metrics Report Format

The metrics report (`{run_id}_metrics.json`) contains:

```json
{
  "run_id": "todo-app-baseline-20250127-143522-abc123",
  "benchmark_name": "Todo App Baseline",
  "start_time": "2025-01-27T14:35:22.123Z",
  "end_time": "2025-01-27T16:45:33.456Z",
  "total_duration_seconds": 7811.333,
  "total_cost_usd": 15.4567,
  "total_tokens": 1234567,
  "total_input_tokens": 234567,
  "total_output_tokens": 1000000,
  "agent_count": 7,
  "phase_count": 7,
  "success": true,
  "agent_metrics": [
    {
      "agent_name": "Mary",
      "start_time": "2025-01-27T14:35:22.123Z",
      "end_time": "2025-01-27T14:50:33.456Z",
      "duration_seconds": 911.333,
      "input_tokens": 12345,
      "output_tokens": 23456,
      "total_tokens": 35801,
      "estimated_cost_usd": 0.3888,
      "tool_calls": 45,
      "model_used": "claude-sonnet-4-20250514"
    },
    // ... more agents
  ],
  "phase_summary": [
    {
      "phase_name": "Analysis Phase",
      "agent_name": "Mary",
      "success": true,
      "duration_seconds": 911.333,
      "details": {
        "output_length": 12345,
        "metadata": { /* ... */ }
      }
    },
    // ... more phases
  ]
}
```

## Console Summary

At completion, you'll see:

```
================================================================================
BENCHMARK METRICS SUMMARY
================================================================================
Run ID: todo-app-baseline-20250127-143522-abc123
Benchmark: Todo App Baseline

Total Duration: 7811.33 seconds (130.2 minutes)
Total Cost: $15.4567
Total Tokens: 1,234,567 (1234.6K)

Agent Breakdown:
Agent           Duration     Tokens       Cost
--------------------------------------------------------------------------------
Mary              911.3s ( 15.2m)      35,801  $  0.3888
John             1234.5s ( 20.6m)      67,890  $  1.2345
Winston          1456.7s ( 24.3m)      89,012  $  1.5678
Sally             987.6s ( 16.5m)      45,678  $  0.7890
Bob               765.4s ( 12.8m)      34,567  $  0.5678
Amelia           2145.6s ( 35.8m)     789,012  $  9.1234
Murat            310.2s (  5.2m)      172,607  $  1.8854
================================================================================

Verbose log: D:\GAO Agile Dev\sandbox\metrics\{run_id}_verbose.log
Metrics JSON: D:\GAO Agile Dev\sandbox\metrics\{run_id}_metrics.json
```

## Completion Criteria

The system ensures agents complete ALL work by:

1. **Explicit Instructions**: Agent prompts state:
   - "COMPLETE END-TO-END BENCHMARK"
   - "DO NOT stop at foundation or setup"
   - "Deliver COMPLETE, PRODUCTION-READY result"

2. **Completion Criteria**: Each phase has specific criteria:
   - Implementation: Complete ALL stories with tests
   - Planning: COMPLETE and DETAILED documentation
   - Quality: Run ALL tests, fix ALL issues

3. **Success Validation**: Quality gates check:
   - All tests passing
   - Code coverage >80%
   - Type checking passes
   - Security audit clean
   - Performance benchmarks met

## Example Benchmark: Todo App

The `todo-app-baseline.yaml` benchmark creates a complete Next.js todo application:

- **103 story points** across **5 epics**
- **7 phases** with **7 specialized agents**
- **Expected duration**: ~130 minutes
- **Expected cost**: ~$15-20 (depends on actual token usage)

### Epics Included

1. **Epic 1**: Authentication & Security (18 pts)
2. **Epic 2**: Core Todo Management (21 pts)
3. **Epic 3**: Categories & Organization (15 pts)
4. **Epic 4**: Testing & Quality (39 pts)
5. **Epic 5**: Documentation & Deployment (10 pts)

### Technical Stack

- **Frontend**: Next.js 14+, React 18+, TypeScript strict mode
- **Backend**: Next.js API routes, Prisma ORM
- **Database**: PostgreSQL
- **Testing**: Jest, React Testing Library, Playwright
- **Quality**: ESLint, Prettier, TypeScript strict, >80% coverage
- **Security**: OWASP Top 10 compliance
- **Accessibility**: WCAG 2.1 AA compliance

## Troubleshooting

### No API Key Error

```
ValueError: API key not found. Set ANTHROPIC_API_KEY environment variable
or pass api_key parameter
```

**Solution**: Set the `ANTHROPIC_API_KEY` environment variable or pass `--api-key` flag.

### Agent Spawner Not Initialized

```
Agent spawner not initialized (API key required)
```

**Solution**: Ensure `execution_mode="agent"` and API key is provided to BenchmarkRunner.

### Import Errors

```
ImportError: cannot import name 'MetricsAggregator' from 'gao_dev.sandbox.benchmark'
```

**Solution**: The module exports were updated. Make sure you have the latest code.

### Incomplete Execution

If agents stop at "foundation" instead of completing all work:

1. Check agent prompts in `runner.py` - they should emphasize COMPLETE work
2. Verify timeout is sufficient (todo-app needs ~130 minutes)
3. Check metrics logs to see where agent stopped

## Advanced Usage

### Custom Benchmarks

Create your own benchmark YAML file:

```yaml
name: "my-custom-benchmark"
description: "Description of what to build"
version: "1.0.0"
timeout_seconds: 14400  # 4 hours

initial_prompt: |
  Build a complete [your project description here].

  Requirements:
  - [Requirement 1]
  - [Requirement 2]

phases:
  - name: "Analysis Phase"
    agent: "Mary"
    expected_duration_minutes: 15

  - name: "Planning Phase"
    agent: "John"
    expected_duration_minutes: 30

  # ... more phases

success_criteria:
  required_files:
    - "README.md"
    - "package.json"
  test_coverage_threshold: 80
  # ... more criteria
```

### Programmatic Usage

```python
from pathlib import Path
from gao_dev.sandbox.benchmark import BenchmarkRunner
from gao_dev.sandbox.manager import SandboxManager
from gao_dev.sandbox.metrics.collector import MetricsCollector
from gao_dev.sandbox.benchmark_loader import load_benchmark

# Load benchmark config
config = load_benchmark(Path("sandbox/benchmarks/my-benchmark.yaml"))

# Initialize components
sandbox_manager = SandboxManager(Path("sandbox"))
metrics_collector = MetricsCollector()
sandbox_root = Path("sandbox")

# Run benchmark with API key
runner = BenchmarkRunner(
    config=config,
    sandbox_manager=sandbox_manager,
    metrics_collector=metrics_collector,
    sandbox_root=sandbox_root,
    api_key="sk-ant-...",  # Your API key
)

result = runner.run()

# Check results
print(f"Success: {result.status}")
print(f"Duration: {result.duration_seconds}s")
print(f"Metrics: {result.metadata['metrics_report']}")
```

## Cost Estimation

### Claude Sonnet 4 Pricing

- **Input**: $3.00 per million tokens
- **Output**: $15.00 per million tokens

### Typical Costs

- **Simple app** (20-30 stories): $5-10
- **Medium app** (50-80 stories): $10-20
- **Complex app** (100+ stories): $20-40

### Optimization Tips

1. **Reuse boilerplate**: Use `boilerplate_url` or `boilerplate_path` to reduce initial setup tokens
2. **Clear prompts**: Specific prompts reduce iteration and token waste
3. **Reasonable timeouts**: Don't over-allocate time per phase
4. **Quality gates**: Catch issues early to avoid expensive rework

## Next Steps

1. **Run your first benchmark**: Start with `todo-app-baseline` to see the system in action
2. **Review metrics**: Examine the verbose logs and metrics JSON
3. **Create custom benchmarks**: Define your own projects to build
4. **Optimize costs**: Refine prompts and timeouts based on metrics
5. **Scale up**: Run multiple benchmarks in parallel for comparison

## Support

For issues or questions:
- Check verbose logs: `sandbox/metrics/{run_id}_verbose.log`
- Review metrics report: `sandbox/metrics/{run_id}_metrics.json`
- Check agent personas: `gao_dev/agents/*.md`
- Review code: `gao_dev/sandbox/benchmark/`

---

**Last Updated**: 2025-01-27
**Version**: 1.0.0
