"""Script to automatically fix tests by adding proper fixtures."""

import re

# Read the test file
with open("tests/core/state/test_state_tracker.py", "r") as f:
    content = f.read()

# Define replacement patterns
replacements = [
    # Story tests - need epic
    (r"def (test_\w+)\(tracker\):\s*\n(\s*)\"\"\"Test.*story.*\"\"\"",
     r"def \1(tracker_with_epic):\n\2\"\"\"Test story operations (epic pre-created).\"\"\"\n\2tracker = tracker_with_epic"),

    # Sprint-related tests - need sprint
    (r"def (test_\w+sprint\w*)\(tracker\):",
     r"def \1(tracker_with_epic_and_sprint):"),

    # Workflow tests - need epic and story
    (r"def (test_\w+workflow\w*)\(tracker\):",
     r"def \1(tracker_with_epic_and_story):"),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

# Write back
with open("tests/core/state/test_state_tracker.py", "w") as f:
    f.write(content)

print("Tests fixed!")
