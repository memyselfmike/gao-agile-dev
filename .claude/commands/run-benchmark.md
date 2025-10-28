---
description: Run a benchmark with a config file
---

Execute a benchmark run using a configuration file.

**IMPORTANT**: Running benchmarks requires an Anthropic API key. Before running, ensure:
1. You have set the ANTHROPIC_API_KEY environment variable, OR
2. You have a .env file with ANTHROPIC_API_KEY

First, show available benchmarks:

```bash
cd "D:\GAO Agile Dev"
ls -1 sandbox/benchmarks/*.yaml
```

Ask the user which benchmark config to run, or use the one they specified.

Then execute:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox run {{BENCHMARK_CONFIG}}
```

Where {{BENCHMARK_CONFIG}} is the path to the YAML file (e.g., `sandbox/benchmarks/todo-app-incremental.yaml`)

After the run:
1. Show the run summary
2. Display any errors or warnings
3. Show the project location
4. Offer to show detailed results or generate a report

**Note**: Story-based benchmarks will execute autonomously with agent spawning. This may take significant time and API credits.
