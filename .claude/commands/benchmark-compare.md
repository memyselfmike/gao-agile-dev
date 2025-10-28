---
description: Compare two benchmark runs
---

Compare metrics between two benchmark runs to see improvements or regressions.

**List available runs:**

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox runs {{BENCHMARK_NAME}}
```

Ask the user for two run IDs to compare, then execute:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox compare {{RUN_ID_1}} {{RUN_ID_2}}
```

After comparison, summarize:
1. Performance differences (time, token usage)
2. Quality differences (test coverage, type safety)
3. Autonomy differences (manual interventions)
4. Overall recommendation (which run performed better)

Where:
- {{BENCHMARK_NAME}} is the benchmark name to list runs for
- {{RUN_ID_1}} and {{RUN_ID_2}} are the run IDs to compare
