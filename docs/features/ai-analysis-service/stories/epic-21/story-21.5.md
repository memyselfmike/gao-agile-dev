# Story 21.5: Benchmark Validation with DeepSeek-R1

**Epic**: 21 - AI Analysis Service & Brian Provider Abstraction
**Story Points**: 3
**Status**: Blocked (depends on Stories 21.1-21.4)
**Priority**: High
**Assignee**: TBD

---

## User Story

As a **user**, I want **to run benchmarks with local deepseek-r1 model**, so that **I can validate GAO-Dev works with free local models and save on API costs during development**.

---

## Context

This is the **original user request** that sparked Epic 21:
> "we now have opencode working as an option for running gao-dev - one of the benefits of opencode is the ability to utilise local models. we have ollama installed with the deepseek-r1 model and I would like to test a benchmark of our simple todo app using opencode + deepseek-r1"

After implementing Stories 21.1-21.4, we can now test the complete flow:
1. Brian uses AIAnalysisService (provider-abstracted)
2. AIAnalysisService uses ProcessExecutor
3. ProcessExecutor uses OpenCode provider
4. OpenCode connects to Ollama
5. Ollama runs deepseek-r1 locally

**Success = Benchmark runs end-to-end with local model**

---

## Acceptance Criteria

### AC1: Environment Setup
- [ ] Ollama installed and running
- [ ] deepseek-r1 model pulled (ollama pull deepseek-r1:8b)
- [ ] OpenCode server configured (opencode.json exists)
- [ ] OpenCode server running

### AC2: Benchmark Configuration
- [ ] `sandbox/benchmarks/simple-todo-deepseek.yaml` exists
- [ ] Configured for deepseek-r1 model
- [ ] Simplified success criteria (local model limitations)
- [ ] Scale level set appropriately

### AC3: Benchmark Execution
- [ ] Run `python run_deepseek_benchmark.py`
- [ ] Brian uses deepseek-r1 for analysis
- [ ] Workflow selection works correctly
- [ ] No "404 - model not found" errors
- [ ] Benchmark completes successfully

### AC4: Workflow Selection Validation
- [ ] Brian analyzes prompt using deepseek-r1
- [ ] Returns appropriate scale level
- [ ] Selects correct workflow sequence
- [ ] Logging shows model=deepseek-r1
- [ ] No fallback to Claude

### AC5: Metrics Collection
- [ ] Performance metrics captured:
  - Brian analysis duration
  - Token usage
  - Cost (should be $0 for local)
  - Workflow execution time
- [ ] Autonomy metrics captured
- [ ] Quality metrics captured (if applicable)

### AC6: Report Generation
- [ ] HTML report generated successfully
- [ ] Report shows deepseek-r1 usage
- [ ] Performance metrics displayed
- [ ] Charts render correctly
- [ ] Can open report in browser

### AC7: Performance Comparison
- [ ] Document deepseek-r1 performance vs. Claude
- [ ] Compare analysis quality
- [ ] Note any differences in workflow selection
- [ ] Document limitations/issues

### AC8: Troubleshooting Guide
- [ ] Document common issues
- [ ] Setup instructions clear
- [ ] Error messages documented
- [ ] Workarounds provided

---

## Technical Details

### Benchmark Configuration

```yaml
# sandbox/benchmarks/simple-todo-deepseek.yaml
benchmark:
  name: "simple-todo-deepseek"
  description: "Simple todo app with OpenCode + deepseek-r1 local model"
  version: "1.0.0"

  initial_prompt: |
    Create a minimal but functional todo application.

    Requirements:
    - Backend: Python with FastAPI
    - Simple in-memory storage (no database required)
    - REST API endpoints (CRUD operations)
    - Basic error handling
    - Unit tests with pytest

  # Relaxed criteria for local model
  success_criteria:
    - Application runs without errors
    - Core API endpoints work
    - At least basic tests exist

  # Level 2 project (small feature)
  scale_level: 2

  # Use deepseek-r1 explicitly
  model_override: "deepseek-r1"

  timeout_seconds: 1800  # 30 minutes
```

### Execution Script

```python
# run_deepseek_benchmark.py
#!/usr/bin/env python
"""
Run GAO-Dev benchmark with OpenCode + Ollama + deepseek-r1.

This script sets the required environment variables and runs the benchmark.
"""

import os
import sys
import subprocess

# Set environment variables
os.environ["AGENT_PROVIDER"] = "opencode-sdk"
os.environ["GAO_DEV_MODEL"] = "deepseek-r1"

print("=" * 80)
print("GAO-Dev Benchmark: OpenCode + Ollama + DeepSeek-R1")
print("=" * 80)
print(f"Provider: {os.environ['AGENT_PROVIDER']}")
print(f"Model: {os.environ['GAO_DEV_MODEL']}")
print("=" * 80)
print()

# Run the benchmark
cmd = [
    sys.executable, "-m", "gao_dev.cli.commands",
    "sandbox", "run",
    "sandbox/benchmarks/simple-todo-deepseek.yaml"
]

try:
    result = subprocess.run(cmd, check=True)
    sys.exit(result.returncode)
except subprocess.CalledProcessError as e:
    print(f"\nBenchmark failed with exit code: {e.returncode}")
    sys.exit(e.returncode)
except KeyboardInterrupt:
    print("\n\nBenchmark interrupted by user")
    sys.exit(1)
```

### Expected Logs

```
================================================================================
GAO-Dev Benchmark: OpenCode + Ollama + DeepSeek-R1
================================================================================
Provider: opencode-sdk
Model: deepseek-r1
================================================================================

2025-11-07 10:00:00 [info] benchmark_starting name=simple-todo-deepseek
2025-11-07 10:00:01 [info] brian_analysis_started model=deepseek-r1
2025-11-07 10:00:03 [info] analysis_started model=deepseek-r1 prompt_length=150
2025-11-07 10:00:08 [info] analysis_complete model=deepseek-r1 tokens=120 duration_ms=5200
2025-11-07 10:00:08 [info] brian_analysis_complete scale_level=2 model=deepseek-r1
2025-11-07 10:00:08 [info] workflow_sequence_selected workflows=3 scale_level=2
...
```

---

## Testing Checklist

### Pre-Flight Checks
- [ ] Ollama installed: `ollama --version`
- [ ] deepseek-r1 available: `ollama list | grep deepseek`
- [ ] OpenCode configured: `cat opencode.json`
- [ ] OpenCode running: `opencode status`

### Benchmark Execution
- [ ] Run: `python run_deepseek_benchmark.py`
- [ ] Observe logs in real-time
- [ ] Check for errors
- [ ] Wait for completion

### Verification
- [ ] Check Brian used deepseek-r1: `grep "model=deepseek-r1" logs/`
- [ ] Check workflow selected: `grep "workflow_sequence" logs/`
- [ ] Check no Anthropic API calls: `grep "anthropic" logs/`
- [ ] Check artifacts created: `ls sandbox/projects/*/`

### Report Review
- [ ] Open HTML report
- [ ] Verify model shown as deepseek-r1
- [ ] Check metrics make sense
- [ ] Review performance data

---

## Performance Expectations

### DeepSeek-R1 vs Claude Sonnet 4.5

| Metric | DeepSeek-R1 (8B) | Claude Sonnet 4.5 | Notes |
|--------|------------------|-------------------|-------|
| Analysis Time | 5-15 seconds | 2-5 seconds | Local inference slower |
| Cost | $0 | $0.01-0.05 | Free local model |
| Quality | Good | Excellent | Claude more consistent |
| Context Length | 8K tokens | 200K tokens | Claude handles larger prompts |
| Availability | Offline | Internet required | Local advantage |

### Known Limitations
- DeepSeek-R1 may be less consistent in JSON formatting
- Slower inference time on local hardware
- Limited context window compared to Claude
- May need prompt adjustments for optimal results

---

## Troubleshooting Guide

### Issue: "404 - model: deepseek-r1"
**Cause**: Brian still using Anthropic API
**Solution**: Verify Stories 21.1-21.3 complete, check environment variables

### Issue: Ollama connection refused
**Cause**: Ollama not running
**Solution**:
```bash
ollama serve  # Start Ollama
ollama list   # Verify models
```

### Issue: "Model not found"
**Cause**: deepseek-r1 not pulled
**Solution**:
```bash
ollama pull deepseek-r1:8b
ollama list  # Verify
```

### Issue: OpenCode not configured
**Cause**: opencode.json missing or incorrect
**Solution**:
```bash
# Verify opencode.json exists
cat opencode.json

# Should contain Ollama configuration
{
  "provider": {
    "ollama": {
      "baseURL": "http://localhost:11434/v1",
      "models": {
        "deepseek-r1:8b": {...}
      }
    }
  }
}
```

### Issue: Slow performance
**Cause**: Local inference on CPU
**Solution**:
- Expected behavior (local models slower)
- Consider GPU acceleration for better performance
- Increase timeout in benchmark config

---

## Definition of Done

- [ ] Benchmark runs successfully with deepseek-r1
- [ ] Brian uses local model (no Anthropic API calls)
- [ ] Workflow selection works correctly
- [ ] Metrics captured and report generated
- [ ] Performance documented and compared
- [ ] Troubleshooting guide complete
- [ ] Success validated by user

---

## Dependencies

- **Story 21.1** (required): AIAnalysisService
- **Story 21.2** (required): Brian refactored
- **Story 21.3** (required): Initialization updated
- **Story 21.4** (optional): Integration tests help validate
- **Ollama** (external): Must be installed and running
- **deepseek-r1** (external): Must be pulled in Ollama
- **OpenCode** (optional): For OpenCode provider

---

## Success Metrics

- [ ] Benchmark completes without errors
- [ ] Brian analysis duration < 30 seconds
- [ ] Cost = $0 (local model)
- [ ] Workflow selection same as with Claude (or close)
- [ ] Report generated successfully
- [ ] User satisfied with local model functionality

---

## Documentation Updates

After successful benchmark:
- [ ] Update README.md with local model instructions
- [ ] Document performance comparison
- [ ] Add troubleshooting section
- [ ] Link to benchmark config example
- [ ] Note any limitations discovered

---

## Related Documents

- **Story 21.1**: Create AI Analysis Service (prerequisite)
- **Story 21.2**: Refactor Brian (prerequisite)
- **Story 21.3**: Update Initialization (prerequisite)
- **Story 21.4**: Integration Testing (validation)
- **Epic 21 Plan**: `docs/features/ai-analysis-service/EPIC-21-PLAN.md`
- **Architecture Analysis**: `docs/analysis/brian-architecture-analysis.md`
- **Benchmark Config**: `sandbox/benchmarks/simple-todo-deepseek.yaml`
- **Execution Script**: `run_deepseek_benchmark.py`
