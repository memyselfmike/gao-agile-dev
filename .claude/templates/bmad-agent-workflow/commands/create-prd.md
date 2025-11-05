---
description: Create Product Requirements Document using John agent
---

Use the Task tool to spawn the John agent (Product Manager) to create a comprehensive Product Requirements Document.

**Process**:

1. **Ask for feature name if not provided**:
   ```
   What feature would you like to create a PRD for?
   ```

2. **Create feature directory**:
   ```bash
   mkdir -p docs/features/{{FEATURE_NAME}}
   ```

3. **Spawn John agent** using the Task tool:
   ```python
   Task(
       subagent_type="general-purpose",
       description="Create PRD for {{FEATURE_NAME}}",
       prompt="""
   Use the John agent to create a Product Requirements Document for '{{FEATURE_NAME}}'.

   John should:
   1. Use the 'prd' workflow to understand the PRD structure
   2. Research similar features for best practices
   3. Read existing project documentation for context (if any)
   4. Create a comprehensive PRD.md file
   5. Save to docs/features/{{FEATURE_NAME}}/PRD.md

   The PRD MUST include:
   - Executive Summary (Vision, Goals, Strategic Importance)
   - Problem Statement (Current State, Pain Points, Impact)
   - Target State (Desired End State, Key Capabilities)
   - Requirements:
     - Functional Requirements (numbered, testable)
     - Non-Functional Requirements (performance, security, etc.)
   - Success Criteria (measurable)
   - User Stories (high-level)
   - Dependencies and Risks
   - Out of Scope (what we're NOT doing)
   - Timeline and Milestones

   Follow the format used in existing PRDs in docs/features/.

   🤖 Generated with Claude Code
   """
   )
   ```

4. **After John completes**:
   - Review the PRD at `docs/features/{{FEATURE_NAME}}/PRD.md`
   - Ensure all sections are comprehensive
   - Ask user if they'd like to proceed to architecture

**Example**:
```
User: "Create PRD for user authentication"

You:
1. Create docs/features/user-authentication/
2. Spawn John with task to create PRD
3. John creates comprehensive PRD.md
4. Report: "John has created a comprehensive PRD with 12 functional requirements and 6 non-functional requirements. Ready to proceed with architecture design?"
```

**What John Creates**:
- `docs/features/{{FEATURE_NAME}}/PRD.md` (comprehensive product requirements)

**Next Step**:
After PRD complete, use `/create-architecture` to create technical architecture.
