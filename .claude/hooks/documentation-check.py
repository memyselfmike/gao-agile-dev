#!/usr/bin/env python3
"""Documentation Check Hook - Ensures docs stay synchronized.

Triggers on: PostToolUse (after Edit/Write)
"""
import json
import re
import sys

# Read input from stdin
try:
    input_data = json.load(sys.stdin)
    file_path = input_data.get("tool_input", {}).get("file_path", "")
except (json.JSONDecodeError, ValueError):
    # If input parsing fails, exit silently (no blocking)
    sys.exit(0)

# Check if file is in implementation directories and has relevant extension
pattern = r"(gao_dev|src)[/\\].*\.(py|ts|tsx|js|jsx|yaml|json)$"
if re.search(pattern, file_path):
    print("""<system-reminder priority="high">

DOCUMENTATION UPDATE CHECK

You modified code. Evaluate documentation impact:

DOCUMENTATION IMPACT:
- API endpoints: [YES/NO]
- User workflows: [YES/NO]
- Feature docs: [YES/NO]
- Development patterns: [YES/NO]
- Architecture: [YES/NO]
- Examples: [YES/NO]

If ANY are YES: Invoke Skill(skill="documentation") and update affected docs.

</system-reminder>""")

sys.exit(0)
