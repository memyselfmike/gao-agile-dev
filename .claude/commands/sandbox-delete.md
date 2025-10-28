---
description: Delete a sandbox project
---

Delete a sandbox project and all its files.

**WARNING**: This action is irreversible. All project files will be permanently deleted.

First, list available projects:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox list
```

Show the user the list and ask which project to delete.

Before deleting, show project details:

```bash
cd "D:\GAO Agile Dev"
ls -lh "sandbox/projects/{{PROJECT_NAME}}"
du -sh "sandbox/projects/{{PROJECT_NAME}}"
```

Ask for confirmation, then execute:

```bash
cd "D:\GAO Agile Dev"
python -m gao_dev.cli.commands sandbox delete {{PROJECT_NAME}}
```

After deletion:
1. Confirm the project was deleted
2. Show updated project list
3. Show disk space freed

Where {{PROJECT_NAME}} is the name of the project to delete.
