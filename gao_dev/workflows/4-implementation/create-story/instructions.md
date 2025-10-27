# Create Story Workflow

## Objective
Create a new user story from an epic definition.

## Instructions

1. **Read Epic Definition**
   - Use `read_file` to load the epic definition from `docs/epics.md`
   - Locate Epic {{epic_num}} in the document
   - Extract epic description, goals, and acceptance criteria

2. **Analyze Requirements**
   - Review the epic's scope
   - Identify the specific piece of functionality for Story {{story_num}}
   - Determine acceptance criteria for this story

3. **Create Story File**
   - Use the template provided
   - Fill in all sections with relevant information
   - Ensure acceptance criteria are specific and testable
   - Set initial status to "Draft"

4. **Write Story**
   - Use `write_file` to create the story at the output location
   - Path: {{dev_story_location}}/epic-{{epic_num}}/story-{{epic_num}}.{{story_num}}.md

5. **Verify**
   - Confirm file was created successfully
   - Report story title and location

## Success Criteria
- Story file created at correct location
- All required sections populated
- Acceptance criteria are clear and testable
- Status set to "Draft"
