---
description: Create atomic git commit following B-MAD standards
---

Guide through creating an atomic commit following B-MAD methodology standards.

**CRITICAL RULES**:
1. ONE story = ONE commit
2. Commit immediately after story completion
3. Follow conventional commit format
4. Include acceptance criteria checklist
5. Never batch multiple stories

**Process**:

1. **Verify this is for ONE story only**:
   ```
   Is this commit for a single story? (Which story: Epic.Story format)
   ```

2. **Check git status**:
   ```bash
   git status
   git diff --staged  # If changes staged
   git diff           # If changes unstaged
   ```

3. **Review changes** to ensure they're all for this ONE story.

4. **Read story file** to get acceptance criteria:
   ```bash
   cat docs/features/{{FEATURE}}/stories/epic-{{EPIC}}/story-{{EPIC}}.{{STORY}}.md
   ```

5. **Determine commit type and scope**:
   - **Type**: feat, fix, docs, refactor, test, chore, perf
   - **Scope**: Component/module affected (e.g., auth, api, sandbox, metrics)

6. **Create commit message** following this format:
   ```
   <type>(<scope>): implement Story <Epic>.<Story> - <Brief Description>

   <Detailed explanation of what changed and WHY>
   <Include implementation details>
   <Explain key decisions>

   Acceptance Criteria Met:
   - [x] AC1: <Description from story file>
   - [x] AC2: <Description from story file>
   - [x] AC3: <Description from story file>
   - [x] AC4: <Description from story file>

   <Optional: Technical notes, performance impact, breaking changes>

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

7. **Execute commit**:
   ```bash
   git add -A
   git commit -m "{{MESSAGE}}"
   ```

8. **Verify commit**:
   ```bash
   git log -1 --stat  # Show last commit with changes
   git status         # Verify clean working tree
   ```

9. **Update tracking**:
   - Update story status in sprint-status.yaml: `status: done`
   - If epic complete, update bmm-workflow-status.md

**Example**:
```bash
git add -A
git commit -m "feat(auth): implement Story 3.1 - JWT Token Validation

Implement JWT token validation middleware with comprehensive error handling.
Uses jsonwebtoken library to validate signature, expiration, and required claims.
Returns 401 for invalid tokens, 403 for expired tokens.

Added TokenValidator class with validate() method that:
- Verifies JWT signature using secret key
- Checks token expiration timestamp
- Validates required claims (user_id, email, roles)
- Handles malformed tokens gracefully

Includes comprehensive unit tests with 95% coverage covering:
- Valid token success case
- Invalid signature rejection
- Expired token rejection
- Missing claims rejection
- Malformed token handling

Acceptance Criteria Met:
- [x] Token signature validated using secret key
- [x] Expiration timestamp checked
- [x] Required claims (user_id, email, roles) validated
- [x] Invalid tokens return 401 error
- [x] Expired tokens return 403 error
- [x] Unit tests achieve >90% coverage
- [x] Integration test validates end-to-end flow

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Pre-Commit Checklist**:
- [ ] Changes are for ONE story only (not multiple stories)
- [ ] All tests pass (pytest)
- [ ] Test coverage >80% (pytest --cov)
- [ ] Type checking passes (mypy --strict)
- [ ] No linting errors (ruff)
- [ ] Documentation updated (docstrings, README)
- [ ] Commit message follows format
- [ ] Acceptance criteria listed in message

**Post-Commit Actions**:
- [ ] Verify commit created: `git log -1`
- [ ] Update sprint-status.yaml (mark story done)
- [ ] Update bmm-workflow-status.md (if epic/phase complete)
- [ ] Inform user of completion

**Common Commit Types**:
- `feat`: New feature (most stories)
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring (no functional change)
- `test`: Adding/updating tests
- `chore`: Maintenance (dependencies, config)
- `perf`: Performance improvement

**Scope Examples**:
- `auth`: Authentication/authorization
- `api`: API endpoints
- `db`: Database
- `ui`: User interface
- `sandbox`: Sandbox system
- `metrics`: Metrics collection
- `benchmark`: Benchmarking

**Remember**:
- ONE story = ONE commit (sacred rule)
- Commit immediately after story complete
- Never batch stories together
- Include ALL acceptance criteria in message
- Update tracking after commit
