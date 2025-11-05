---
description: Check current sprint status and next story
---

Show current sprint status, what's done, and what's next.

**Process**:

1. **Read bmm-workflow-status.md** (ALWAYS START HERE):
   ```bash
   cat docs/bmm-workflow-status.md
   ```

2. **Read sprint-status.yaml** for detailed story tracking:
   ```bash
   cat docs/sprint-status.yaml
   ```

3. **Analyze and report**:

   **Show**:
   - Current phase and scale level
   - Current epic name and status
   - Total epics (completed vs remaining)
   - Current sprint stories:
     - How many stories total in current epic
     - How many completed
     - How many in progress
     - How many blocked
     - How many not started
   - Next story to implement (if current epic in progress)
   - Overall progress percentage

   **Format output as**:
   ```
   === SPRINT STATUS ===

   Phase: 4-implementation
   Scale Level: 3 (Medium Feature)
   Project: {{PROJECT_NAME}}

   Current Epic: Epic {{N}} - {{EPIC_NAME}}
   Status: {{in_progress|completed}}

   Progress:
   - Epic {{N}}: {{completed_stories}}/{{total_stories}} stories complete ({{percentage}}%)
     ✅ Story {{N}}.1 - {{NAME}} (done)
     ✅ Story {{N}}.2 - {{NAME}} (done)
     🔄 Story {{N}}.3 - {{NAME}} (in_progress) ← YOU ARE HERE
     ⏳ Story {{N}}.4 - {{NAME}} (not_started)
     ⏳ Story {{N}}.5 - {{NAME}} (not_started)

   Completed Epics:
   ✅ Epic 1 - {{NAME}} ({{story_count}} stories)
   ✅ Epic 2 - {{NAME}} ({{story_count}} stories)

   Next Action:
   → Continue implementing Story {{N}}.3
   → File: docs/features/{{FEATURE}}/stories/epic-{{N}}/story-{{N}}.3.md
   → Use: /implement-story --epic {{N}} --story 3

   Overall Progress: {{completed_epics}}/{{total_epics}} epics, {{completed_stories}}/{{total_stories}} stories
   ```

4. **Offer next steps**:
   ```
   Would you like to:
   1. Implement the next story (/implement-story)
   2. View a specific story file (Read {{file_path}})
   3. Update workflow status (Edit bmm-workflow-status.md)
   4. Review completed work (git log --oneline)
   ```

**Example Output**:
```
=== SPRINT STATUS ===

Phase: 4-implementation
Scale Level: 3 (Medium Feature)
Project: Sandbox & Benchmarking System

Current Epic: Epic 5 - Reporting & Visualization
Status: in_progress

Progress:
- Epic 5: 3/6 stories complete (50%)
  ✅ Story 5.1 - Report Templates (done)
  ✅ Story 5.2 - HTML Report Generator (done)
  ✅ Story 5.3 - Chart Generation (done)
  🔄 Story 5.4 - Comparison Report (in_progress) ← YOU ARE HERE
  ⏳ Story 5.5 - Trend Analysis (not_started)
  ⏳ Story 5.6 - Report CLI Commands (not_started)

Completed Epics:
✅ Epic 1 - Sandbox Infrastructure (6 stories)
✅ Epic 2 - Boilerplate Integration (5 stories)
✅ Epic 3 - Metrics Collection (9 stories)
✅ Epic 4 - Benchmark Runner (7 stories)

Next Action:
→ Continue implementing Story 5.4 - Comparison Report
→ File: docs/features/sandbox-system/stories/epic-5/story-5.4.md
→ Use: /implement-story --epic 5 --story 4

Overall Progress: 4/8 epics, 27/46 stories (59% complete)

Would you like to:
1. Implement Story 5.4 (/implement-story --epic 5 --story 4)
2. View story file (Read docs/features/sandbox-system/stories/epic-5/story-5.4.md)
3. Review recent commits (git log --oneline -5)
```

**Use Cases**:
- ✅ Check what to work on next
- ✅ See overall progress
- ✅ Understand current context
- ✅ Verify story completion
- ✅ Plan next sprint

**Always check status before starting new work!**
