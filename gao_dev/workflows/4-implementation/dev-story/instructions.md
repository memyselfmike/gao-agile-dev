# Implement Story Workflow

## Objective
Implement a user story by writing code that meets all acceptance criteria.

## Instructions

1. **Load Story**
   - Use `read_file` to load the story file
   - Path: {{dev_story_location}}/epic-{{epic_num}}/story-{{epic_num}}.{{story_num}}.md
   - Parse acceptance criteria and requirements

2. **Create Feature Branch**
   - Use `git_create_branch` to create a new branch
   - Branch name: feature/epic-{{epic_num}}-story-{{story_num}}

3. **Implement Acceptance Criteria**
   - For each acceptance criterion:
     - Write implementation code
     - Write comprehensive unit tests
     - Ensure tests pass
   - Follow coding standards (type hints, documentation, etc.)

4. **Update Story Status**
   - Change status from "Ready" to "In Progress"
   - Use `write_file` to update the story file

5. **Commit Changes**
   - Use `git_commit` with a conventional commit message
   - Format: feat(story-{{epic_num}}.{{story_num}}): [description]
   - Include GAO-Dev footer

6. **Verify**
   - All acceptance criteria implemented
   - Tests passing
   - Code committed to feature branch

## Success Criteria
- Feature branch created
- All acceptance criteria implemented
- Tests written and passing
- Code committed with proper message
- Story status updated to "In Progress"
