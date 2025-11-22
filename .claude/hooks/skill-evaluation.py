#!/usr/bin/env python3
"""Skill Evaluation Hook - Forces evaluation of skills before work begins.

Triggers on: UserPromptSubmit
"""
import sys

# Output the system reminder
print("""<system-reminder priority="critical">

MANDATORY SKILL EVALUATION PROTOCOL

Before proceeding, evaluate which skills are needed:

SKILL EVALUATION:
- story-writing: [YES/NO] - [reasoning]
- prd-creation: [YES/NO] - [reasoning]
- architecture-design: [YES/NO] - [reasoning]
- code-review: [YES/NO] - [reasoning]
- ui-testing: [YES/NO] - [reasoning]
- bug-verification: [YES/NO] - [reasoning]
- documentation: [YES/NO] - [reasoning]

For each YES, invoke: Skill(skill="skill-name")

</system-reminder>""")

sys.exit(0)
