---
description: Implement ONE story using Amelia agent (TDD approach)
---

Use the Task tool to spawn Amelia (Developer) to implement ONE story following TDD and quality standards.

**Prerequisites**:
- Story file exists at `docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC}}/story-{{EPIC}}.{{STORY}}.md`

**Process**:

1. **Ask which story to implement** (if not provided):
   ```
   Which story would you like to implement? (format: epic.story, e.g., 1.1)
   ```

2. **Verify story file exists**:
   ```bash
   cat docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC}}/story-{{EPIC}}.{{STORY}}.md
   ```

3. **Spawn Amelia agent** using the Task tool:
   ```python
   Task(
       subagent_type="general-purpose",
       description="Implement Story {{EPIC}}.{{STORY}} - {{STORY_NAME}}",
       prompt="""
   Use Amelia agent to implement Story {{EPIC}}.{{STORY}} following TDD and quality standards.

   Amelia should follow this EXACT process:

   1. READ STORY COMPLETELY
      - Read story file at docs/features/{{FEATURE_NAME}}/stories/epic-{{EPIC}}/story-{{EPIC}}.{{STORY}}.md
      - Understand all acceptance criteria
      - Review PRD and Architecture for context
      - Check dependencies (blocked by other stories?)

   2. PLAN WORK (use TodoWrite)
      - Break story into implementation tasks
      - Plan test strategy
      - Identify files to create/modify

   3. WRITE TESTS FIRST (TDD - RED phase)
      - Write FAILING tests for each acceptance criterion
      - Ensure tests fail for the right reason
      - Cover edge cases and error conditions
      - Run tests to verify they fail: pytest

   4. IMPLEMENT (TDD - GREEN phase)
      - Write MINIMAL code to pass tests
      - Follow SOLID principles
      - Keep functions <50 lines
      - Use type hints on ALL functions (no Any types)
      - Handle errors explicitly
      - Use structured logging (no print statements)

   5. REFACTOR (TDD - REFACTOR phase)
      - Remove duplication (DRY)
      - Improve names for clarity
      - Extract complex logic to functions
      - Run tests to ensure still passing

   6. VALIDATE QUALITY
      - Run all tests: pytest
      - Check coverage: pytest --cov={{MODULE}} --cov-report=term-missing
      - Type checking: mypy {{MODULE}} --strict
      - Linting: ruff check .
      - Coverage MUST be >80%
      - All checks MUST pass

   7. CREATE ATOMIC COMMIT (ONE STORY = ONE COMMIT)
      ```bash
      git add -A
      git commit -m "feat({{SCOPE}}): implement Story {{EPIC}}.{{STORY}} - {{STORY_NAME}}

      {{DETAILED_EXPLANATION}}

      Acceptance Criteria Met:
      - [x] AC1: {{DESCRIPTION}}
      - [x] AC2: {{DESCRIPTION}}
      - [x] AC3: {{DESCRIPTION}}

      🤖 Generated with Claude Code
      Co-Authored-By: Claude <noreply@anthropic.com>"
      ```

   8. UPDATE TRACKING
      - Update story status in sprint-status.yaml (status: done)
      - Mark TodoWrite items as completed

   QUALITY STANDARDS (NON-NEGOTIABLE):
   - ✅ TDD: Tests written FIRST
   - ✅ 80%+ test coverage
   - ✅ Type hints on all functions
   - ✅ No `Any` types
   - ✅ SOLID principles
   - ✅ DRY (no duplication)
   - ✅ Functions <50 lines
   - ✅ MyPy strict mode passes
   - ✅ Ruff passes (no linting errors)
   - ✅ ONE atomic commit per story

   🤖 Generated with Claude Code
   """
   )
   ```

4. **After Amelia completes**:
   - Verify commit was created
   - Check that sprint-status.yaml was updated
   - Review test coverage
   - Confirm all quality checks passed
   - Ask user if they'd like to implement next story

**Example**:
```
User: "Implement story 1.1"

You:
1. Read story-1.1.md (User Registration Form)
2. Spawn Amelia to implement
3. Amelia:
   - Writes tests first (7 test cases)
   - Implements registration form component
   - Refactors for clarity
   - All tests pass, 92% coverage
   - MyPy and Ruff pass
   - Creates atomic commit
   - Updates sprint-status.yaml
4. Report: "Story 1.1 complete! Created registration form with comprehensive validation. 7 tests passing, 92% coverage, all quality checks passed. Committed with message 'feat(auth): implement Story 1.1 - User Registration Form'. Ready to implement Story 1.2?"
```

**What Amelia Does**:
- Implements feature with TDD
- Creates comprehensive tests
- Creates ONE atomic commit
- Updates sprint-status.yaml

**Critical Rules**:
- ✅ ONE story at a time
- ✅ ONE commit per story
- ✅ Tests FIRST (TDD)
- ✅ 80%+ coverage required
- ✅ All quality checks must pass

**Next Step**:
Continue implementing remaining stories one at a time until epic complete.
