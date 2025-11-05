# Story 15.6: CLI Commands for State Management

**Epic:** 15 - State Tracking Database
**Story Points:** 3 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Create CLI commands for querying and managing state. Provide user-friendly interface to the state database.

---

## Acceptance Criteria

### CLI Commands
- [ ] `gao-dev state story <epic> <story>` - Show story details
- [ ] `gao-dev state epic <epic>` - Show epic progress
- [ ] `gao-dev state sprint [sprint_num]` - Show sprint (current if no num)
- [ ] `gao-dev state sync` - Manual sync trigger
- [ ] `gao-dev state query "<query>"` - Custom SQL queries (read-only)
- [ ] `gao-dev state import` - Import from markdown/YAML (Story 15.5)

### Output Formatting
- [ ] Rich tables for tabular data
- [ ] Colors for status (green=done, yellow=in_progress, red=blocked)
- [ ] JSON output option (--format json) for scripting
- [ ] CSV output option (--format csv)

### Interactive Features
- [ ] `gao-dev state dashboard` - Interactive dashboard (optional)
- [ ] Progress bars for epic/sprint progress
- [ ] Charts for velocity trends (optional)

**Files to Create:**
- `gao_dev/cli/state_commands.py`
- `tests/cli/test_state_commands.py`

**Dependencies:** Story 15.4 (Query Builder)

---

## Definition of Done

- [ ] All CLI commands working
- [ ] Rich formatting implemented
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Committed with atomic commit
