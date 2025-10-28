---
description: Clean/reset a sandbox project
---

Reset a sandbox project to a clean state (removes all generated files).

First, list available projects:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox list
```

Ask the user which project to clean, then run:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox clean {{PROJECT_NAME}}
```

After cleaning:
1. Confirm the project was reset
2. Show the current git status
3. Ask if they want to initialize with a new boilerplate
