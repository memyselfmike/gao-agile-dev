"""Debug script to test update behavior."""
import sqlite3
import tempfile
from pathlib import Path

# Create temp DB
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = Path(f.name)

# Create schema
conn = sqlite3.connect(str(db_path))
schema_path = Path("gao_dev/core/state/schema.sql")
with open(schema_path, "r") as schema_file:
    conn.executescript(schema_file.read())
conn.close()

# Test operations
from gao_dev.core.state.state_tracker import StateTracker

tracker = StateTracker(db_path)

# Create epic and story
print("Creating epic...")
epic = tracker.create_epic(epic_num=1, title="Test Epic", feature="test")
print(f"Epic created: {epic.epic_num}")

print("\nCreating story...")
story = tracker.create_story(epic_num=1, story_num=1, title="Test Story")
print(f"Story created: {story.epic}.{story.story_num}, status={story.status}")

print("\nUpdating story status...")
updated = tracker.update_story_status(1, 1, "in_progress")
print(f"After update: status={updated.status}")

print("\nGetting story again...")
retrieved = tracker.get_story(1, 1)
print(f"Retrieved: status={retrieved.status}")

# Clean up
db_path.unlink()

print("\n" + ("="*50))
if retrieved.status == "in_progress":
    print("SUCCESS: Update worked correctly!")
else:
    print(f"FAILURE: Expected 'in_progress', got '{retrieved.status}'")
