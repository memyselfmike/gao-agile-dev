#!/usr/bin/env python3
"""Pre-Push Validation Hook - Validates before git push.

Triggers on: PreToolUse (before Bash commands)
"""
import json
import sys

# Read input from stdin
try:
    input_data = json.load(sys.stdin)
    command = input_data.get("tool_input", {}).get("command", "")
except (json.JSONDecodeError, ValueError):
    # If input parsing fails, exit silently (no blocking)
    sys.exit(0)

# Check if command contains "git push"
if "git push" in command:
    print("""<system-reminder priority="critical">

PRE-PUSH VALIDATION REQUIRED

Before git push, validate:

PRE-PUSH CHECKLIST:
1. Installation: python verify_install.py (all PASS)
2. Tests: pytest --cov=gao_dev tests/ (0 failures, >=80% coverage)
3. Types: mypy gao_dev/ --strict (0 errors)
4. Format: black gao_dev/ --check (all formatted)
5. Docs: Are affected docs updated?
6. Workflow: bmm-workflow-status.md current?
7. Commit: git log -1 --pretty=%B (format: <type>(<scope>): <desc>)
8. Issues: No critical TODOs?

OUTPUT FORMAT:
PRE-PUSH VALIDATION:
- Installation: [PASS/FAIL]
- Tests: [PASS/FAIL] - [details]
- Types: [PASS/FAIL]
- Format: [PASS/FAIL]
- Docs: [PASS/FAIL]
- Workflow: [PASS/FAIL]
- Commit: [PASS/FAIL]
- Issues: [PASS/FAIL]

OVERALL: [READY TO PUSH / NOT READY]

Only push if READY TO PUSH.

</system-reminder>""")

sys.exit(0)
