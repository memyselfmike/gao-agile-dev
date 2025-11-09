# Story 27.2: Update CLI Commands

**Epic**: Epic 27 - Integration & Migration
**Story ID**: 27.2
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Update CLI commands to use GitIntegratedStateManager for atomic commits. All commands (create_prd, create_story, implement_story) now create git commits bundling file + DB changes.

---

## Acceptance Criteria

- [ ] create_prd uses state_manager.create_epic()
- [ ] create_story uses state_manager.create_story()
- [ ] implement_story uses state_manager.transition_story()
- [ ] All commands create atomic git commits
- [ ] CLI help updated with git transaction info
- [ ] CLI tests updated
- [ ] 8 CLI tests (one per command)

---

## Files to Modify

- `gao_dev/cli/commands.py` (~50 LOC changes to use state_manager)
- `tests/cli/test_lifecycle_commands_integration.py` (+~100 LOC)

---

## Key Changes

```python
# OLD (direct file writes)
def create_story_cmd(epic: int, story: int):
    file_path.write_text(content)
    registry.register_document(...)

# NEW (atomic commits)
def create_story_cmd(epic: int, story: int):
    story_obj = orchestrator.state_manager.create_story(
        epic, story, content, metadata
    )
    # File + DB + git commit done atomically
    print(f"Story created with commit {story_obj.commit_sha}")
```

---

## Testing Strategy

- test_create_prd_creates_commit()
- test_create_story_creates_commit()
- test_implement_story_transitions_state()
- test_cli_rollback_on_error()
- test_commit_message_format()
- test_git_sha_in_output()
- test_dirty_tree_prevents_operation()
- test_cli_help_updated()

---

## Definition of Done

- [ ] 8 tests passing
- [ ] All CLI commands use atomic commits
- [ ] Git commit: "feat(epic-27): update CLI commands for git transactions"

---

**Created**: 2025-11-09
