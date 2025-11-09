# Scientific Method for GAO-Dev Benchmarking

**Version**: 1.0.0
**Last Updated**: 2025-10-27
**Purpose**: Apply rigorous scientific methodology to measuring GAO-Dev's capabilities

---

## The Scientific Method

### Traditional Science

```
1. Question: Can GAO-Dev build apps autonomously?
2. Hypothesis: Yes, with iterative improvement
3. Experiment: Run standardized benchmarks
4. Observe: Measure time, interventions, quality
5. Analyze: Compare results across runs
6. Conclude: Autonomy improving/regressing
7. Iterate: Make improvements, repeat
```

### Applied to GAO-Dev

```
HYPOTHESIS: GAO-Dev can autonomously build a production-ready todo app

CONTROL VARIABLES (must remain constant):
- Initial prompt (never changes)
- Success criteria (same every time)
- Tech stack (consistent requirements)
- Benchmark version (v1.0 throughout)

INDEPENDENT VARIABLES (what we change):
- Agent prompts/capabilities
- Tool implementations
- Workflow optimizations
- Error handling

DEPENDENT VARIABLES (what we measure):
- Time to completion
- Manual interventions required
- Code quality score
- Test coverage
- Success criteria met

EXPERIMENT PROTOCOL:
- Run standardized benchmark
- Record all metrics
- Auto-generate run ID (no human naming!)
- Link run to benchmark version
- Store complete metadata
- Compare to previous runs with SAME benchmark

ANALYSIS:
- Plot trends over time
- Statistical significance testing
- Identify regressions
- Validate improvements
```

---

## Why Auto-Generated Run IDs?

### The Problem with Manual Naming

❌ **Human Error**:
```bash
gao-dev sandbox init test-run-1      # User types "1"
gao-dev sandbox init test-run-02     # User types "02"
gao-dev sandbox init test-run-3      # User types "3"
```
→ Inconsistent numbering, hard to sort, error-prone

❌ **Lost Context**:
```bash
gao-dev sandbox init my-test         # Which benchmark?
gao-dev sandbox init todo-attempt    # Which version?
gao-dev sandbox init experiment-001  # What's the baseline?
```
→ No link to benchmark, can't compare

❌ **Ambiguity**:
```
run-001 with todo-app-baseline v1.0?
run-001 with todo-app-baseline v2.0?
run-001 with simple-api-baseline v1.0?
```
→ Can't tell what's being tested

### The Solution: Scientific Run IDs

✅ **Auto-Generated**:
```
Format: [benchmark-name]-run-[NNN]

Examples:
- simple-api-baseline-run-001
- simple-api-baseline-run-002
- todo-app-baseline-run-001
- todo-app-baseline-run-002
```

✅ **Contains Critical Info**:
- Which benchmark (simple-api-baseline)
- Sequential number (run-001, run-002)
- Automatically linked to benchmark file
- Version tracked in metadata

✅ **Prevents Errors**:
- System auto-increments (no human error)
- Guarantees uniqueness
- Impossible to mix up benchmarks
- Clear sorting/ordering

---

## Run Management System

### Automatic Run Creation

```bash
# OLD WAY (manual, error-prone)
gao-dev sandbox init my-test-project

# NEW WAY (scientific, automatic)
gao-dev sandbox run benchmarks/simple-api-baseline.yaml
```

What happens:
1. System reads benchmark file
2. Finds last run number for this benchmark (e.g., run-003)
3. Auto-generates next ID: `simple-api-baseline-run-004`
4. Creates project with generated ID
5. Stores complete metadata:
   - Benchmark name & version
   - Prompt hash (verify it never changed)
   - Start timestamp
   - Expected outcomes
   - Success criteria
6. Ready to execute with full traceability

### Run Metadata

Every run automatically tracks:

```yaml
# .sandbox.yaml (auto-generated)
run_metadata:
  run_id: "simple-api-baseline-run-004"
  benchmark_file: "benchmarks/simple-api-baseline.yaml"
  benchmark_version: "1.0.0"
  prompt_hash: "sha256:abc123..."
  created_at: "2025-10-27T14:30:00"
  started_at: "2025-10-27T14:31:00"
  completed_at: null  # Filled when done

  expected_outcomes:
    time_minutes: 45
    manual_interventions: 3
    completion_percentage: 85

  actual_outcomes:
    time_minutes: null      # Filled during/after run
    manual_interventions: null
    completion_percentage: null

  environment:
    python_version: "3.11.5"
    node_version: "18.17.0"
    gao_dev_version: "1.0.0"
```

### Comparison Rules

The system **enforces scientific rigor**:

✅ **Valid Comparison**:
```
simple-api-baseline-run-001 vs simple-api-baseline-run-002
(same benchmark, same version)
```

❌ **Invalid Comparison** (blocked by system):
```
simple-api-baseline-run-001 vs todo-app-baseline-run-001
(different benchmarks - NOT comparable!)
```

❌ **Invalid Comparison** (blocked by system):
```
todo-app-baseline-v1-run-001 vs todo-app-baseline-v2-run-001
(different versions - variables changed!)
```

---

## Commands

### Run a Benchmark

```bash
# Automatic run ID generation
gao-dev sandbox run benchmarks/simple-api-baseline.yaml

# Output:
# >> Reading benchmark: simple-api-baseline v1.0
# >> Last run: simple-api-baseline-run-003
# >> Creating: simple-api-baseline-run-004
# >> Project: sandbox/projects/simple-api-baseline-run-004
# >> Ready to execute!
```

### List Runs (by Benchmark)

```bash
# Show all runs for a specific benchmark
gao-dev sandbox runs simple-api-baseline

# Output:
# Runs for: simple-api-baseline (v1.0)
# ----------------------------------------
# Run 001 | 2025-10-20 | 48 min | 5 interventions | COMPLETED
# Run 002 | 2025-10-23 | 42 min | 3 interventions | COMPLETED
# Run 003 | 2025-10-25 | 38 min | 2 interventions | COMPLETED
# Run 004 | 2025-10-27 | IN PROGRESS
#
# Trend: Time decreasing ↓ | Interventions decreasing ↓
```

### Compare Runs

```bash
# Compare two runs (same benchmark only!)
gao-dev sandbox compare simple-api-baseline-run-003 simple-api-baseline-run-004

# System validates they're comparable
# Shows delta in all metrics
# Highlights improvements/regressions
```

### Show Run Details

```bash
# Get all metadata for a run
gao-dev sandbox show simple-api-baseline-run-004

# Output:
# Run ID: simple-api-baseline-run-004
# Benchmark: simple-api-baseline v1.0
# Prompt Hash: sha256:abc123... (verified)
# Status: COMPLETED
#
# Timeline:
#   Created: 2025-10-27 14:30:00
#   Started: 2025-10-27 14:31:00
#   Completed: 2025-10-27 15:16:00
#   Duration: 45 minutes
#
# Outcomes:
#   Manual Interventions: 2 (expected: 3) ✓ BETTER
#   Completion: 95% (expected: 85%) ✓ BETTER
#   Success Criteria: 5/5 met ✓
```

---

## Experimental Design

### Baseline Run

The **first run** establishes the baseline:

```bash
# Run 001 is your baseline
gao-dev sandbox run benchmarks/simple-api-baseline.yaml

# Results become the reference point
# All future runs compare to this
```

### Improvement Cycle

Scientific iteration:

```
1. Run baseline (Run 001)
   → Time: 50 min, Interventions: 5

2. Analyze results
   → Identified 3 gaps

3. Form hypothesis
   → "Improving error handling will reduce interventions"

4. Make changes
   → Implement Story 7.1: Better error handling

5. Re-run experiment (Run 002)
   → Time: 45 min, Interventions: 3

6. Validate hypothesis
   → Interventions reduced by 40% ✓ VALIDATED

7. Repeat
   → Continue until full autonomy
```

### Control Group

For major changes, maintain a control:

```bash
# Control: No changes, re-run same configuration
gao-dev sandbox run benchmarks/simple-api-baseline.yaml
# simple-api-baseline-run-005

# Experimental: With new feature
gao-dev sandbox run benchmarks/simple-api-baseline.yaml
# simple-api-baseline-run-006 (after deploying change)

# Compare to isolate the impact of the change
```

---

## Statistical Rigor

### Multiple Runs for Confidence

Don't trust a single data point:

```bash
# Run same benchmark 3 times
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 001
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 002
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 003

# Get average and standard deviation
gao-dev sandbox stats simple-api-baseline --runs 001-003

# Output:
# Time: 46 ± 3 minutes (mean ± std dev)
# Interventions: 3.2 ± 0.8
# Completion: 87 ± 5%
```

### Trend Analysis

```bash
# Show improvement trend
gao-dev sandbox trends simple-api-baseline

# Output: (ASCII chart)
# Manual Interventions Over Time
#  6 |●
#  5 |  ●
#  4 |    ●
#  3 |      ●  ●
#  2 |           ●  ●
#  1 |                ●
#  0 |____________________
#     001 002 003 004 005 006 007 008
#
# Trend: Linear decrease, R² = 0.92
# Projected: Zero interventions by Run 012
```

---

## Best Practices

### DO

✅ **Use auto-generated run IDs**
- Let the system name runs
- Guarantees consistency

✅ **Run multiple iterations**
- 3+ runs for each configuration
- Calculate averages and variance

✅ **Compare apples-to-apples**
- Same benchmark version only
- Same success criteria

✅ **Track everything**
- All metrics, all runs
- Environment details

✅ **Analyze trends**
- Not just absolute values
- Look at rate of improvement

### DON'T

❌ **Manually name runs**
- Introduces human error
- Breaks traceability

❌ **Compare different benchmarks**
- simple-api vs todo-app: NOT COMPARABLE
- Different variables, different complexity

❌ **Modify prompts mid-experiment**
- Invalidates all previous data
- Start new benchmark version instead

❌ **Cherry-pick results**
- Report all runs, not just good ones
- Include failures in analysis

❌ **Trust single data points**
- Run multiple times
- Calculate statistics

---

## Example: Complete Experiment

### Hypothesis
"Improving Amelia's code generation will reduce manual interventions by 50%"

### Baseline (Before Change)
```bash
# Run benchmark 3 times for baseline
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 001
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 002
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 003

# Results:
# Run 001: 5 interventions, 50 min
# Run 002: 4 interventions, 48 min
# Run 003: 6 interventions, 52 min
# Average: 5.0 ± 1.0 interventions, 50 ± 2 min
```

### Intervention
```bash
# Implement improvement
git checkout -b improve-amelia-codegen
# ... make changes to Amelia's prompt/tools ...
git commit -m "feat: improve Amelia code generation"
```

### Experiment (After Change)
```bash
# Run benchmark 3 times with change
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 004
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 005
gao-dev sandbox run benchmarks/simple-api-baseline.yaml  # Run 006

# Results:
# Run 004: 3 interventions, 45 min
# Run 005: 2 interventions, 43 min
# Run 006: 2 interventions, 44 min
# Average: 2.3 ± 0.6 interventions, 44 ± 1 min
```

### Analysis
```bash
gao-dev sandbox compare-groups \
  --baseline 001-003 \
  --experiment 004-006 \
  --benchmark simple-api-baseline

# Output:
# Metric              | Baseline   | Experiment | Delta    | Significance
# --------------------|------------|------------|----------|-------------
# Interventions       | 5.0 ± 1.0  | 2.3 ± 0.6  | -54%     | p < 0.05 ✓
# Time (minutes)      | 50 ± 2     | 44 ± 1     | -12%     | p < 0.05 ✓
#
# CONCLUSION: Hypothesis VALIDATED
# Improvement is statistically significant
# 54% reduction in interventions (exceeded 50% target!)
```

---

## Conclusion

Scientific rigor requires:

1. **Automated, consistent naming** - No human error
2. **Complete metadata tracking** - Full traceability
3. **Controlled experiments** - Same prompt every time
4. **Statistical analysis** - Multiple runs, averages, trends
5. **Apples-to-apples comparison** - Same benchmark version
6. **Reproducible results** - Anyone can verify

By auto-generating run IDs and enforcing comparison rules, GAO-Dev ensures **true scientific measurement** of autonomous capability improvement.

---

*This methodology enables data-driven decision making and proves improvement objectively.*
