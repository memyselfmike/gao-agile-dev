# Ceremony System User Guide

**Epic**: 28 - Ceremony-Driven Workflow Integration
**Story**: 28.5 - CLI Commands & Testing (AC8)
**Last Updated**: 2025-11-09
**Version**: 1.0

---

## Table of Contents

1. [What Are Ceremonies?](#what-are-ceremonies)
2. [When Ceremonies Trigger](#when-ceremonies-trigger)
3. [Viewing Ceremony Results](#viewing-ceremony-results)
4. [Manually Holding Ceremonies](#manually-holding-ceremonies)
5. [Safety Mechanisms](#safety-mechanisms)
6. [CLI Commands Reference](#cli-commands-reference)
7. [Troubleshooting](#troubleshooting)

---

## What Are Ceremonies?

Ceremonies are structured team meetings that enable collaborative learning, continuous improvement, and coordination across GAO-Dev's autonomous agents. They serve as synchronization points in the development workflow.

### Ceremony Types

GAO-Dev supports three ceremony types:

#### 1. Planning Ceremony
- **Purpose**: Epic kickoff, story breakdown, capacity planning
- **Participants**: John (PM), Winston (Architect), Bob (Scrum Master), Amelia (Developer)
- **Outcomes**:
  - Story prioritization
  - Effort estimates
  - Sprint commitment
  - Risk identification
- **Duration**: ~30-60 minutes

#### 2. Standup Ceremony
- **Purpose**: Progress sync, blocker identification, quick decisions
- **Participants**: Bob (facilitator), Amelia (developer), others as needed
- **Outcomes**:
  - Progress updates
  - Blocker resolution plans
  - Action items for immediate work
- **Duration**: ~15 minutes

#### 3. Retrospective Ceremony
- **Purpose**: Learning capture, process improvement, team health
- **Participants**: Entire team (all agents)
- **Outcomes**:
  - Learnings (what worked, what didn't)
  - Process improvements
  - Action items for next sprint/epic
  - Team health assessment
- **Duration**: ~45-90 minutes

---

## When Ceremonies Trigger

Ceremonies trigger automatically based on **Scale Level** and **workflow state**.

### Scale Level 0: Chore
- **No ceremonies** (work too small to warrant coordination overhead)

### Scale Level 1: Bug Fix
- **Retrospective**: Only on repeated failure (2+ attempts)
- Use case: Learn from difficult bugs

### Scale Level 2: Small Feature (3-8 stories)
- **Planning**: Optional (not enforced)
- **Standup**: Every 3 stories (if >3 total stories)
- **Retrospective**: At epic completion
- Example: 5-story feature → 1 standup (after story 3) + 1 retro = 2 ceremonies

### Scale Level 3: Medium Feature (12-40 stories)
- **Planning**: Required at epic start
- **Standup**: Every 2 stories OR quality gate failure
- **Retrospective**: Mid-epic (50% checkpoint) + epic completion
- Example: 8-story feature → 1 planning + 4 standups + 2 retros = 7 ceremonies

### Scale Level 4: Greenfield App (40+ stories)
- **Planning**: Required at epic start + phase boundaries
- **Standup**: Every story OR daily (whichever comes first)
- **Retrospective**: Phase completion + epic completion
- Example: 40-story app → Multiple planning + ~40 standups + multiple retros

### Trigger Summary Table

| Scale Level | Planning | Standup | Retrospective |
|-------------|----------|---------|---------------|
| **0 (Chore)** | Never | Never | Never |
| **1 (Bug)** | Never | Never | On failure (2+) |
| **2 (Small)** | Optional | Every 3 stories | Epic completion |
| **3 (Medium)** | Required | Every 2 stories | Mid + completion |
| **4 (Large)** | Required | Every story/daily | Phase + completion |

---

## Viewing Ceremony Results

### List All Ceremonies for an Epic

```bash
gao-dev ceremony list --epic 1
```

Output:
```
+----+---------------+------------+-------------+--------------------------------------------------+
| ID | Type          | Date       | Participants| Summary                                          |
+----+---------------+------------+-------------+--------------------------------------------------+
| 1  | planning      | 2025-11-09 | team        | Epic 1 planning session                          |
| 2  | standup       | 2025-11-09 | team        | Progress check at story 2                        |
| 3  | retrospective | 2025-11-09 | team        | Epic 1 completed successfully                    |
+----+---------------+------------+-------------+--------------------------------------------------+
```

### Filter by Ceremony Type

```bash
gao-dev ceremony list --epic 1 --type retrospective
```

### Export to JSON

```bash
gao-dev ceremony list --epic 1 --format json > ceremonies.json
```

### View Ceremony Details

```bash
gao-dev ceremony show 1
```

Output:
```
Ceremony #1
  Type: planning
  Epic: 1
  Date: 2025-11-09T10:30:00
  Participants: team

  Summary:
    Epic 1 planning session
    Prioritized stories 1-4
    Identified technical risks

  Decisions:
    - Use TypeScript for frontend
    - PostgreSQL for database
    - Deploy to AWS

  Action Items:
    - Set up CI/CD pipeline
    - Create database schema
    - Schedule architecture review
```

### View Full Transcript

```bash
gao-dev ceremony show 1 --full
```

---

## Manually Holding Ceremonies

Sometimes you need to hold a ceremony outside the automatic triggers (e.g., ad-hoc planning, emergency standup).

### Hold Planning Ceremony

```bash
gao-dev ceremony hold planning --epic 1
```

### Hold Standup for Specific Story

```bash
gao-dev ceremony hold standup --epic 1 --story 3
```

### Hold Retrospective with Custom Participants

```bash
gao-dev ceremony hold retrospective --epic 1 --participants "Bob,Amelia,John"
```

### Dry-Run Mode (Test Without Saving)

```bash
gao-dev ceremony hold planning --epic 1 --dry-run
```

Output:
```
[DRY RUN] Would hold planning ceremony for epic 1
```

---

## Safety Mechanisms

GAO-Dev includes robust safety mechanisms to prevent infinite loops, resource exhaustion, and ceremony overload.

### 1. Max Ceremonies Per Epic (Hard Limit)

**Limit**: 10 ceremonies per epic
**Reason**: Prevents infinite loops and excessive overhead

```bash
gao-dev ceremony safety --epic 1
```

Output:
```
Ceremony Safety Status for Epic 1

Total Ceremonies: 7/10
  OK

By Type:
  Planning: 1
  Standup: 4
  Retrospective: 2
```

If limit approached:
```
Total Ceremonies: 9/10
  WARNING: Approaching limit
```

### 2. Cooldown Periods

**Purpose**: Prevent rapid re-triggering of same ceremony type

**Cooldown Durations**:
- Planning: 24 hours
- Standup: 12 hours
- Retrospective: 24 hours

Check cooldown status:
```bash
gao-dev ceremony safety --epic 1
```

Output:
```
Cooldown Status:
  Planning: Elapsed
  Standup: Active (3.5h remaining)
  Retrospective: Never held
```

### 3. Circuit Breaker Pattern

**Purpose**: Disable ceremonies after repeated failures (3 consecutive failures)

**Behavior**:
- After 3 consecutive failures → circuit opens (ceremonies disabled)
- Manual override required to close circuit
- Automatically resets after successful execution

Check circuit breaker status:
```bash
gao-dev ceremony safety --epic 1
```

Output:
```
Circuit Breaker:
  Planning: Closed (active)
  Standup: Closed (active)
  Retrospective: OPEN (disabled)
```

If circuit open for retrospective, ceremonies will NOT trigger until reset.

### 4. Timeout Management

**Timeout**: 10 minutes per ceremony
**Reason**: Prevent hanging/infinite execution

Ceremonies exceeding 10 minutes are automatically terminated with error status.

---

## CLI Commands Reference

### `gao-dev ceremony hold`

Hold a ceremony manually.

**Syntax**:
```bash
gao-dev ceremony hold <type> --epic <num> [OPTIONS]
```

**Arguments**:
- `<type>`: Ceremony type (planning | standup | retrospective)

**Options**:
- `--epic <num>`: Epic number (required)
- `--story <num>`: Story number (for standup)
- `--participants <list>`: Comma-separated participant list (default: team)
- `--dry-run`: Simulate without saving

**Examples**:
```bash
gao-dev ceremony hold planning --epic 1
gao-dev ceremony hold standup --epic 1 --story 3
gao-dev ceremony hold retrospective --epic 1 --participants "Bob,Amelia,John"
gao-dev ceremony hold planning --epic 1 --dry-run
```

---

### `gao-dev ceremony list`

List ceremonies for an epic.

**Syntax**:
```bash
gao-dev ceremony list --epic <num> [OPTIONS]
```

**Options**:
- `--epic <num>`: Epic number (required)
- `--type <type>`: Filter by ceremony type (planning | standup | retrospective)
- `--format <format>`: Output format (table | json | yaml, default: table)

**Examples**:
```bash
gao-dev ceremony list --epic 1
gao-dev ceremony list --epic 1 --type retrospective
gao-dev ceremony list --epic 1 --format json
```

---

### `gao-dev ceremony show`

Show ceremony details.

**Syntax**:
```bash
gao-dev ceremony show <ceremony-id> [OPTIONS]
```

**Arguments**:
- `<ceremony-id>`: Ceremony ID from list command

**Options**:
- `--full`: Show full transcript (not just excerpt)
- `--format <format>`: Output format (table | json | yaml, default: table)

**Examples**:
```bash
gao-dev ceremony show 1
gao-dev ceremony show 1 --full
gao-dev ceremony show 1 --format json
```

---

### `gao-dev ceremony evaluate`

Evaluate which ceremonies would trigger (dry-run).

**Syntax**:
```bash
gao-dev ceremony evaluate --epic <num> --level <level> [OPTIONS]
```

**Options**:
- `--epic <num>`: Epic number (required)
- `--level <level>`: Scale level 0-4 (required)
- `--stories-completed <n>`: Stories completed (default: 0)
- `--total-stories <n>`: Total stories (default: 1)
- `--quality-gates-passed`: Quality gates passed (default: true)
- `--quality-gates-failed`: Quality gates failed

**Examples**:
```bash
gao-dev ceremony evaluate --epic 1 --level 3 --stories-completed 4 --total-stories 8
gao-dev ceremony evaluate --epic 1 --level 2 --stories-completed 3 --total-stories 5 --quality-gates-failed
```

---

### `gao-dev ceremony safety`

Check ceremony safety status for an epic.

**Syntax**:
```bash
gao-dev ceremony safety --epic <num>
```

**Options**:
- `--epic <num>`: Epic number (required)

**Examples**:
```bash
gao-dev ceremony safety --epic 1
```

---

## Troubleshooting

### Problem: Ceremony not triggering when expected

**Possible Causes**:
1. **Cooldown period active**: Check `gao-dev ceremony safety --epic <num>`
2. **Max ceremonies reached**: Check `gao-dev ceremony safety --epic <num>`
3. **Circuit breaker open**: Check `gao-dev ceremony safety --epic <num>`
4. **Wrong scale level**: Verify scale level matches trigger rules

**Solution**:
```bash
# Check safety status
gao-dev ceremony safety --epic 1

# Evaluate trigger logic
gao-dev ceremony evaluate --epic 1 --level 3 --stories-completed <n> --total-stories <n>

# Manually hold if needed
gao-dev ceremony hold <type> --epic 1
```

---

### Problem: Too many ceremonies triggering

**Possible Causes**:
1. **Scale level too high**: Level 4 triggers many ceremonies
2. **Quality gate failures**: Each failure triggers standup

**Solution**:
```bash
# Check ceremony count
gao-dev ceremony safety --epic 1

# Review trigger evaluation
gao-dev ceremony evaluate --epic 1 --level <your-level> --stories-completed <n> --total-stories <n>

# Consider adjusting scale level if work is smaller than expected
```

---

### Problem: "Not in a GAO-Dev project" error

**Cause**: Not in a directory with `.gao-dev/documents.db`

**Solution**:
```bash
# Check if .gao-dev exists
ls -la .gao-dev

# If not, initialize project
gao-dev sandbox init <project-name>

# Or navigate to correct directory
cd /path/to/project
```

---

### Problem: Ceremony execution failed

**Possible Causes**:
1. **Timeout exceeded**: Ceremony took >10 minutes
2. **Database error**: Database locked or corrupted
3. **Git error**: Git repository in bad state

**Solution**:
```bash
# Check circuit breaker status
gao-dev ceremony safety --epic 1

# If circuit open, investigate last failures in logs
cat .gao-dev/logs/ceremony.log

# Verify database integrity
gao-dev consistency-check

# Verify git status
git status
```

---

### Problem: Cooldown preventing necessary ceremony

**Cause**: Cooldown period hasn't elapsed

**Solution**:
```bash
# Check cooldown status
gao-dev ceremony safety --epic 1

# Option 1: Wait for cooldown to elapse
# Cooldowns: Planning/Retro = 24h, Standup = 12h

# Option 2: Manually hold (bypasses trigger evaluation, but still respects safety limits)
gao-dev ceremony hold <type> --epic 1
```

---

### Problem: Circuit breaker blocking ceremonies

**Cause**: 3 consecutive ceremony failures triggered circuit breaker

**Solution**:
```bash
# Check circuit breaker status
gao-dev ceremony safety --epic 1

# Investigate failures
cat .gao-dev/logs/ceremony.log

# Fix root cause, then attempt successful execution
gao-dev ceremony hold <type> --epic 1

# Success will automatically reset circuit breaker
```

---

## Best Practices

### 1. Let Ceremonies Trigger Automatically

Trust the system's trigger logic. Manual ceremonies should be exception, not rule.

### 2. Monitor Safety Status

Check safety status periodically to ensure system health:
```bash
gao-dev ceremony safety --epic 1
```

### 3. Review Ceremony Results

After each ceremony, review outcomes:
```bash
gao-dev ceremony show <id>
```

### 4. Use Dry-Run for Testing

Test ceremony triggers without saving:
```bash
gao-dev ceremony hold planning --epic 1 --dry-run
gao-dev ceremony evaluate --epic 1 --level 3 --stories-completed 4 --total-stories 8
```

### 5. Respect Cooldowns

If cooldown prevents ceremony, consider if ceremony is truly needed or if cooldown is protecting you from over-coordination.

---

## Additional Resources

- **Architecture**: `docs/features/ceremony-integration-and-self-learning/ARCHITECTURE.md`
- **PRD**: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- **API Reference**: `docs/features/ceremony-integration-and-self-learning/API_REFERENCE.md` (coming soon)
- **Epic 28 Stories**: `docs/features/ceremony-integration-and-self-learning/stories/epic-28/`

---

## Feedback and Support

Found an issue? Have a suggestion?

1. Check troubleshooting section above
2. Search existing issues: [GitHub Issues](https://github.com/your-org/gao-agile-dev/issues)
3. Create new issue with:
   - Ceremony type and epic number
   - Output of `gao-dev ceremony safety --epic <num>`
   - Error messages or unexpected behavior
   - Steps to reproduce

---

**Version**: 1.0
**Last Updated**: 2025-11-09
**Epic**: 28 - Ceremony-Driven Workflow Integration
**Story**: 28.5 - CLI Commands & Testing
