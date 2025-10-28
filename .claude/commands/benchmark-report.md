---
description: Generate or view benchmark reports
---

Generate HTML reports from benchmark runs or view existing reports.

**List available reports:**

```bash
cd "D:\GAO Agile Dev"
ls -lh sandbox/reports/*.html 2>/dev/null || echo "No reports found"
```

**Generate a new report:**

First list recent benchmark runs:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox runs {{BENCHMARK_NAME}}
```

Then generate report:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox report generate {{RUN_ID}} --output sandbox/reports/
```

**View report details:**

Ask the user which report they want to view, then:
1. Show the report file location
2. Offer to open it in a browser
3. Summarize key metrics from the report

Where:
- {{BENCHMARK_NAME}} is the benchmark name (e.g., "todo-app-baseline")
- {{RUN_ID}} is the specific run ID to generate a report for
