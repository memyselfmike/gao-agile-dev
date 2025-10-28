---
description: Initialize a new sandbox project
---

Initialize a new sandbox project for testing.

Run this command to create a fresh sandbox project:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox init {{PROJECT_NAME}} --description "{{DESCRIPTION}}"
```

After running, show:
1. The project location
2. The initial git status
3. Suggest next steps (adding files, running benchmarks)

Ask the user for:
- PROJECT_NAME: The name for the new sandbox project
- DESCRIPTION: Brief description of what this project tests
