---
description: Create detailed story files using Bob agent
---

Use the Task tool to spawn Bob (Scrum Master) to create detailed story files from epic breakdown.

**Prerequisites**:
- epics.md exists at `docs/features/{{FEATURE_NAME}}/epics.md`

**Process**:

1. **Ask which epic to create stories for**:
   ```
   Which epic would you like to create stories for? (epic number)
   ```

2. **Verify epics.md exists and read it**:
   ```bash
   cat docs/features/{{FEATURE_NAME}}/epics.md
   ```

3. **Create stories directory**:
   ```bash
   mkdir -p docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC_NUMBER}}
   ```

4. **Spawn Bob agent** using the Task tool:
   ```python
   Task(
       subagent_type="general-purpose",
       description="Create story files for Epic {{EPIC_NUMBER}}",
       prompt="""
   Use Bob agent to create detailed story files for Epic {{EPIC_NUMBER}} of '{{FEATURE_NAME}}'.

   Bob should:
   1. Read epics.md at docs/features/{{FEATURE_NAME}}/epics.md
   2. Extract all stories for Epic {{EPIC_NUMBER}}
   3. For each story, create a detailed story file
   4. Save each story to docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC_NUMBER}}/story-{{EPIC}}.{{STORY}}.md
   5. Update sprint-status.yaml with new stories

   Each story file MUST include:
   - Story header with metadata:
     - Epic number
     - Status (Not Started)
     - Priority (P0, P1, P2)
     - Estimated Effort (story points)
     - Owner (usually Amelia)
     - Created date
     - Dependencies
   - User Story ("As a... I want... So that...")
   - Acceptance Criteria (detailed, testable):
     - AC1, AC2, AC3, etc.
     - Each with checkbox format: - [ ] Description
   - Technical Details:
     - Implementation approach
     - File structure
     - Code examples
     - Design patterns to use
   - Testing Strategy:
     - Unit tests required
     - Integration tests required
     - Coverage targets
     - Test scenarios
   - Definition of Done checklist
   - Dependencies (upstream/downstream stories)
   - Notes and considerations

   Follow the format used in existing story files in docs/features/.

   Update sprint-status.yaml:
   - Add epic if not present
   - Add all stories for this epic
   - Set status: not_started
   - Include file paths

   🤖 Generated with Claude Code
   """
   )
   ```

5. **After Bob completes**:
   - Review story files in `docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC_NUMBER}}/`
   - Verify sprint-status.yaml is updated
   - Check that acceptance criteria are clear and testable
   - Ask user if they'd like to start implementing Story 1

**Example**:
```
User: "Create stories for Epic 1 of user authentication"

You:
1. Read epics.md
2. Create stories/epic-1/ directory
3. Spawn Bob to create story files
4. Bob creates:
   - story-1.1.md (User Registration Form)
   - story-1.2.md (Email Validation)
   - story-1.3.md (Password Strength Validation)
   - story-1.4.md (User Account Creation)
   - story-1.5.md (Registration Confirmation Email)
5. Bob updates sprint-status.yaml
6. Report: "Created 5 story files for Epic 1. All stories have comprehensive acceptance criteria and testing strategies. Ready to implement Story 1.1?"
```

**What Bob Creates**:
- `docs/features/{{FEATURE_NAME}}/stories/epic-N/story-N.M.md` (one per story)
- Updates to `docs/sprint-status.yaml`

**Next Step**:
After stories created, use `/implement-story` to implement stories one at a time.
