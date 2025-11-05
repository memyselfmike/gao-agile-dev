---
description: Break down feature into epics using John/Bob agents
---

Use the Task tool to spawn John or Bob to break down a feature into implementable epics with story estimates.

**Prerequisites**:
- PRD exists at `docs/features/{{FEATURE_NAME}}/PRD.md`
- Architecture exists at `docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md`

**Process**:

1. **Verify prerequisites**:
   ```bash
   ls docs/features/{{FEATURE_NAME}}/PRD.md
   ls docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md
   ```

2. **Spawn John/Bob agent** using the Task tool:
   ```python
   Task(
       subagent_type="general-purpose",
       description="Create epic breakdown for {{FEATURE_NAME}}",
       prompt="""
   Use John or Bob agent to create epic breakdown for '{{FEATURE_NAME}}'.

   The agent should:
   1. Read PRD at docs/features/{{FEATURE_NAME}}/PRD.md
   2. Read Architecture at docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md
   3. Break down feature into 2-6 implementable epics
   4. For each epic, break down into stories (3-8 stories per epic)
   5. Estimate story points for each story (1, 2, 3, 5, 8, 13 points)
   6. Define success criteria for each epic
   7. Identify dependencies between epics
   8. Create comprehensive epics.md
   9. Save to docs/features/{{FEATURE_NAME}}/epics.md

   The epics.md MUST include:
   - Epic Breakdown section with all epics
   - For each epic:
     - Epic name and number
     - Goal (what this epic achieves)
     - Owner (which agent implements - usually Amelia)
     - Priority (P0, P1, P2)
     - Estimated Duration (in weeks)
     - Story Points (total for epic)
     - Success Criteria (measurable outcomes)
     - Stories breakdown:
       - Story number (Epic.Story format: 1.1, 1.2, etc.)
       - Story points
       - Priority
       - Description
       - Acceptance criteria (high-level)
       - Technical notes
       - Dependencies
   - Epic Sequencing & Dependencies (which epics must be done first)
   - Total Effort Summary (total story points, duration estimate)

   Follow the format used in existing epics.md files in docs/features/.

   🤖 Generated with Claude Code
   """
   )
   ```

3. **After agent completes**:
   - Review epics.md at `docs/features/{{FEATURE_NAME}}/epics.md`
   - Verify story estimates are reasonable
   - Check dependencies make sense
   - Ensure success criteria are measurable
   - Ask user if they'd like to create story files for first epic

**Example**:
```
User: "Create epic breakdown for user authentication"

You:
1. Verify PRD and Architecture exist
2. Spawn John/Bob to create epic breakdown
3. Agent creates epics.md with 4 epics, 22 stories, 89 story points
4. Report: "Created epic breakdown with 4 epics:
   - Epic 1: User Registration (5 stories, 21 points)
   - Epic 2: Login & Session Management (6 stories, 26 points)
   - Epic 3: Password Reset (4 stories, 18 points)
   - Epic 4: OAuth Integration (7 stories, 24 points)
   Total: 22 stories, 89 points, estimated 4-5 weeks.
   Ready to create story files for Epic 1?"
```

**What's Created**:
- `docs/features/{{FEATURE_NAME}}/epics.md` (epic and story breakdown)

**Next Step**:
After epics defined, use `/create-stories` to create detailed story files.
