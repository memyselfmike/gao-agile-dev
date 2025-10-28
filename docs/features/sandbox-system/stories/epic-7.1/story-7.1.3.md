# Story 7.1.3: Test Story-Based Workflow End-to-End

**Epic**: 7.1 - Integration & Architecture Fix
**Story Points**: 3
**Priority**: P0
**Status**: Ready
**Owner**: Amelia (Developer)

## User Story

As a QA engineer
I want to verify story-based benchmarks work with QA-as-you-go
So that we can trust the incremental development workflow

## Goal

Prove that story-based workflow works end-to-end with QA validation per story.

## Acceptance Criteria

- [ ] simple-story-test.yaml completes successfully
- [ ] Both stories execute: "Create Hello World Function" and "Create Greeting Function"
- [ ] Murat validates each story before commit (QA-as-you-go confirmed)
- [ ] 2 atomic git commits created (one per story)
- [ ] Story metrics collected (duration, tests, artifacts)
- [ ] All acceptance criteria met for both stories

## Testing

```bash
python -m gao_dev.cli.commands sandbox run \
  sandbox/benchmarks/simple-story-test.yaml
```

**Expected Output**:
```
Story 1.1: Create Hello World Function
  → Bob: Create story spec
  → Amelia: Implement hello_world()
  → Murat: Validate tests passing ✓
  → Git: Commit feat(story-1.1)

Story 1.2: Create Greeting Function
  → Bob: Create story spec
  → Amelia: Implement greet(name)
  → Murat: Validate tests passing ✓
  → Git: Commit feat(story-1.2)

Benchmark: SUCCESS ✓
```

## Definition of Done

- [ ] Benchmark runs successfully
- [ ] QA validation confirmed per story
- [ ] Commits verified
- [ ] Story updated to Done
