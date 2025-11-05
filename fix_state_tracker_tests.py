"""Comprehensive script to fix state tracker tests with proper fixtures and setup."""

import re

# Read the test file
with open("tests/core/state/test_state_tracker.py", "r") as f:
    content = f.read()

# Pattern 1: Story tests that use tracker but need tracker_with_epic
story_tests = [
    "test_update_story_status",
    "test_update_story_status_invalid",
    "test_update_story_owner",
    "test_update_story_points",
    "test_get_stories_by_status",
    "test_get_stories_by_status_pagination",
    "test_get_stories_by_epic",
    "test_get_stories_by_sprint",
    "test_get_stories_in_progress",
    "test_get_blocked_stories",
    "test_story_full_id_property",
    "test_transaction_rollback_on_error",
    "test_concurrent_operations",
    "test_automatic_timestamp_updates",
    "test_prepared_statements_prevent_injection",
]

for test_name in story_tests:
    # Replace function signature
    content = re.sub(
        rf"def {test_name}\(tracker\):",
        rf"def {test_name}(tracker_with_epic):",
        content
    )
    # Add epic creation in test body if needed
    pattern = rf"(def {test_name}\(tracker_with_epic\):.*?\"\"\".*?\"\"\"\s*)"
    replacement = r"\1# Use tracker_with_epic (epic 1 already created)\n    tracker = tracker_with_epic\n    "
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Pattern 2: Sprint tests
sprint_tests = [
    "test_assign_story_to_sprint",
    "test_assign_story_to_nonexistent_sprint",
    "test_unassign_story_from_sprint",
    "test_get_sprint_stories",
    "test_get_sprint_velocity",
    "test_get_sprint_velocity_no_completed",
    "test_get_sprint_completion_rate",
    "test_get_sprint_completion_rate_no_stories",
    "test_get_current_sprint",
    "test_get_sprint_burndown_data",
]

# Add combined fixture to imports
combined_fixture = """
@pytest.fixture
def tracker_with_epic_and_sprint(tracker_with_epic):
    \"\"\"Create StateTracker with epic and sprint already created.\"\"\"
    tracker_with_epic.create_sprint(sprint_num=1, start_date="2025-01-01", end_date="2025-01-14")
    return tracker_with_epic
"""

# Insert after tracker_with_epic_and_story fixture
content = re.sub(
    r"(@pytest\.fixture\s+def tracker_with_epic_and_story.*?return tracker_with_epic)",
    r"\1\n\n" + combined_fixture,
    content,
    flags=re.DOTALL
)

for test_name in sprint_tests:
    content = re.sub(
        rf"def {test_name}\(tracker\):",
        rf"def {test_name}(tracker_with_epic_and_sprint):",
        content
    )
    # Replace tracker. with tracker_with_epic_and_sprint.
    # This is a bit risky, so we'll be careful

# Pattern 3: Workflow tests
workflow_tests = [
    "test_track_workflow_execution",
    "test_update_workflow_status",
    "test_update_workflow_status_invalid",
    "test_get_story_workflow_history",
    "test_get_workflow_execution",
    "test_get_failed_workflows",
    "test_get_workflow_metrics",
]

for test_name in workflow_tests:
    content = re.sub(
        rf"def {test_name}\(tracker\):",
        rf"def {test_name}(tracker_with_epic_and_story):",
        content
    )

# Write back
with open("tests/core/state/test_state_tracker.py", "w") as f:
    f.write(content)

print("[OK] Tests fixed with proper fixtures!")
print("  - Story tests now use tracker_with_epic")
print("  - Sprint tests now use tracker_with_epic_and_sprint")
print("  - Workflow tests now use tracker_with_epic_and_story")
