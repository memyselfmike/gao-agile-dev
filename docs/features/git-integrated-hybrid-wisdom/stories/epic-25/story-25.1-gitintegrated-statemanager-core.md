# Story 25.1: Implement GitIntegratedStateManager (Core)

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.1
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement core GitIntegratedStateManager that bundles file + database changes into atomic git commits. Every operation (create_epic, create_story, transition_story) creates exactly one git commit containing both file and DB changes.

---

## Acceptance Criteria

- [ ] Service ~600 LOC
- [ ] Methods: create_epic(), create_story(), transition_story(), complete_story()
- [ ] All operations atomic (file + DB + git commit bundled)
- [ ] Rollback on error (DB rollback + git reset --hard)
- [ ] Pre-checks: working tree must be clean
- [ ] Structured logging at every step
- [ ] 20 unit tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/git_integrated_state_manager.py` (~600 LOC)
- `tests/core/services/test_git_integrated_state_manager.py` (~300 LOC)

### Key Pattern

```python
class GitIntegratedStateManager:
    def __init__(self, git: GitManager, registry: DocumentRegistry, state: StateCoordinator):
        self.git = git
        self.registry = registry
        self.state = state

    def create_story(self, epic_num: int, story_num: int, content: str, metadata: Dict) -> Story:
        # 1. Pre-check: clean working tree
        if not self.git.is_working_tree_clean():
            raise StateError("Uncommitted changes")

        # 2. Begin DB transaction
        self.registry.begin()

        try:
            # 3. Write file
            file_path.write_text(content)

            # 4. Register document + create state
            self.registry.register_document(...)
            self.state.create_story(...)

            # 5. Commit DB
            self.registry.commit()

            # 6. ATOMIC GIT COMMIT
            self.git.add_all()
            sha = self.git.commit(f"feat(story-{epic_num}.{story_num}): create story")

            return Story(...)
        except Exception:
            # 7. ROLLBACK both
            self.registry.rollback()
            self.git.reset_hard()
            raise
```

---

## Testing Strategy

- test_create_epic_atomic()
- test_create_story_atomic()
- test_transition_story_atomic()
- test_rollback_on_file_error()
- test_rollback_on_db_error()
- test_pre_check_fails_dirty_tree()
- test_commit_message_format()
- test_git_sha_returned()
- + 12 more tests (20 total)

---

## Dependencies

**Upstream**: Stories 23.1, 24.7 (GitManager + StateCoordinator)
**Downstream**: Epic 26, 27 (all use this for atomic operations)

---

## Definition of Done

- [ ] All criteria met
- [ ] 20 tests passing
- [ ] Service ~600 LOC
- [ ] Git commit: "feat(epic-25): implement GitIntegratedStateManager core"

---

**Created**: 2025-11-09
