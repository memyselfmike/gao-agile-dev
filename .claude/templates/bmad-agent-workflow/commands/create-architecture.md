---
description: Create system architecture using Winston agent
---

Use the Task tool to spawn the Winston agent (Technical Architect) to create comprehensive system architecture.

**Prerequisites**:
- PRD must exist at `docs/features/{{FEATURE_NAME}}/PRD.md`

**Process**:

1. **Verify PRD exists**:
   ```bash
   ls docs/features/{{FEATURE_NAME}}/PRD.md
   ```

2. **Spawn Winston agent** using the Task tool:
   ```python
   Task(
       subagent_type="general-purpose",
       description="Create architecture for {{FEATURE_NAME}}",
       prompt="""
   Use the Winston agent to create system architecture for '{{FEATURE_NAME}}'.

   Winston should:
   1. Read the PRD at docs/features/{{FEATURE_NAME}}/PRD.md
   2. Use the 'system-architecture' workflow for guidance
   3. Analyze requirements and design appropriate architecture
   4. Research best practices for similar systems
   5. Create comprehensive ARCHITECTURE.md
   6. Save to docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md

   The Architecture MUST include:
   - Architecture Overview (high-level design)
   - System Components (each component detailed):
     - Component name and purpose
     - Responsibilities
     - Interfaces (inputs/outputs)
     - Dependencies
   - Data Models (database schema, data structures)
   - API Design (endpoints, request/response formats)
   - Technology Stack (languages, frameworks, libraries)
   - Design Patterns (which patterns used and why)
   - Security Architecture (authentication, authorization, data protection)
   - Scalability & Performance Considerations
   - Error Handling Strategy
   - Testing Strategy
   - Deployment Architecture

   Follow the format used in existing architectures in docs/features/.

   🤖 Generated with Claude Code
   """
   )
   ```

3. **After Winston completes**:
   - Review ARCHITECTURE.md at `docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md`
   - Ensure all components are well-defined
   - Verify design patterns are appropriate
   - Check that architecture satisfies all PRD requirements
   - Ask user if they'd like to proceed to epic breakdown

**Example**:
```
User: "Create architecture for user authentication"

You:
1. Verify PRD exists
2. Spawn Winston with task to create architecture
3. Winston designs authentication system architecture
4. Report: "Winston has created a comprehensive architecture with 5 core components, JWT-based authentication, and PostgreSQL for user storage. Ready to break down into epics?"
```

**What Winston Creates**:
- `docs/features/{{FEATURE_NAME}}/ARCHITECTURE.md` (comprehensive technical architecture)

**Next Step**:
After architecture complete, use `/create-epic` to break down into implementable epics.
