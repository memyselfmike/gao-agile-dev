# State Database Schema - Entity Relationship Diagram

## Overview

This ERD shows the complete database schema for GAO-Dev's state tracking system, including all tables, relationships, constraints, and indexes.

## Tables and Relationships

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    EPICS                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PK  id                INTEGER (AUTOINCREMENT)                                   │
│ UK  epic_num          INTEGER (UNIQUE, NOT NULL)                                │
│     name              TEXT (NOT NULL)                                           │
│     feature           TEXT                                                      │
│     goal              TEXT                                                      │
│     description       TEXT                                                      │
│     status            TEXT (CHECK: planned|active|completed|cancelled)          │
│     total_points      INTEGER (DEFAULT 0)                                       │
│     completed_points  INTEGER (DEFAULT 0) [Auto-updated by trigger]             │
│     owner             TEXT                                                      │
│     created_by        TEXT                                                      │
│     created_at        TEXT (DEFAULT NOW)                                        │
│     started_at        TEXT                                                      │
│     completed_at      TEXT                                                      │
│     updated_at        TEXT (DEFAULT NOW) [Auto-updated by trigger]              │
│     file_path         TEXT                                                      │
│     content_hash      TEXT (SHA256 for conflict detection)                      │
│     metadata          JSON                                                      │
│                                                                                 │
│ Indexes:                                                                        │
│   - idx_epics_status (status)                                                   │
│   - idx_epics_feature (feature)                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 1:N (epic_num)
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   STORIES                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PK  id                INTEGER (AUTOINCREMENT)                                   │
│ FK  epic_num          INTEGER (NOT NULL) → epics.epic_num                       │
│     story_num         INTEGER (NOT NULL)                                        │
│     title             TEXT (NOT NULL)                                           │
│     description       TEXT                                                      │
│     status            TEXT (CHECK: pending|in_progress|done|blocked|cancelled)  │
│     priority          TEXT (CHECK: P0|P1|P2|P3, DEFAULT P1)                     │
│     points            INTEGER (DEFAULT 0)                                       │
│     owner             TEXT                                                      │
│     created_by        TEXT                                                      │
│     created_at        TEXT (DEFAULT NOW)                                        │
│     started_at        TEXT                                                      │
│     completed_at      TEXT                                                      │
│     updated_at        TEXT (DEFAULT NOW) [Auto-updated by trigger]              │
│     due_date          TEXT                                                      │
│     file_path         TEXT                                                      │
│     content_hash      TEXT (SHA256 for conflict detection)                      │
│     metadata          JSON                                                      │
│     tags              JSON (Array of strings)                                   │
│                                                                                 │
│ Constraints:                                                                    │
│   - UNIQUE (epic_num, story_num)                                                │
│   - ON UPDATE CASCADE, ON DELETE CASCADE (epic_num FK)                          │
│                                                                                 │
│ Indexes:                                                                        │
│   - idx_stories_status (status)                                                 │
│   - idx_stories_epic (epic_num)                                                 │
│   - idx_stories_priority (priority)                                             │
│   - idx_stories_owner (owner)                                                   │
│   - idx_stories_epic_status (epic_num, status) [Composite]                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                │                                    │
                │ 1:N (epic_num, story_num)          │ N:M via story_assignments
                │                                    │
                ▼                                    ▼
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│    WORKFLOW_EXECUTIONS              │  │      STORY_ASSIGNMENTS              │
├─────────────────────────────────────┤  ├─────────────────────────────────────┤
│ PK  id           INTEGER (AI)       │  │ PK  sprint_num    INTEGER (FK) ──┐  │
│     workflow_name TEXT (NOT NULL)   │  │ PK  epic_num      INTEGER (FK)   │  │
│     phase        TEXT               │  │ PK  story_num     INTEGER (FK)   │  │
│ FK  epic_num     INTEGER             │  │     assigned_at   TEXT           │  │
│ FK  story_num    INTEGER             │  │                                  │  │
│     status       TEXT (CHECK)       │  │ Foreign Keys:                    │  │
│     executor     TEXT (NOT NULL)    │  │ - (sprint_num) → sprints         │  │
│     started_at   TEXT (DEFAULT NOW) │  │ - (epic_num, story_num)          │  │
│     completed_at TEXT               │  │   → stories ON DELETE CASCADE    │  │
│     duration_ms  INTEGER            │  │                                  │  │
│     output       TEXT               │  │ Indexes:                         │  │
│     error_msg    TEXT               │  │ - idx_assignments_sprint         │  │
│     exit_code    INTEGER            │  │ - idx_assignments_story          │  │
│     metadata     JSON               │  └──────────────────────────────────┘  │
│     context_snap JSON               │                │                       │
│                                     │                │                       │
│ Indexes:                            │                │ N:1 (sprint_num)      │
│ - idx_workflow_story                │                │                       │
│ - idx_workflow_status               │                ▼                       │
│ - idx_workflow_name                 │  ┌─────────────────────────────────┐  │
└─────────────────────────────────────┘  │         SPRINTS                 │  │
                                         ├─────────────────────────────────┤  │
                                         │ PK  id              INTEGER (AI)│  │
                                         │ UK  sprint_num      INTEGER     │  │
                                         │     name            TEXT        │  │
                                         │     goal            TEXT        │  │
                                         │     status          TEXT (CHECK)│  │
                                         │     start_date      TEXT        │  │
                                         │     end_date        TEXT        │  │
                                         │     created_at      TEXT        │  │
                                         │     updated_at      TEXT [Auto] │  │
                                         │     planned_points  INTEGER     │  │
                                         │     completed_pts   INTEGER     │  │
                                         │     velocity        REAL        │  │
                                         │     metadata        JSON        │  │
                                         │                                 │  │
                                         │ Constraints:                    │  │
                                         │ - CHECK (end_date > start_date) │  │
                                         │                                 │  │
                                         │ Indexes:                        │  │
                                         │ - idx_sprints_status            │  │
                                         │ - idx_sprints_dates             │  │
                                         └─────────────────────────────────┘  │
                                                                               │
                                                                               │
        ┌──────────────────────────────────────────────────────────────────────┘
        │
        │ Referenced by all tables (audit trail)
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STATE_CHANGES                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ PK  id           INTEGER (AUTOINCREMENT)                                        │
│     table_name   TEXT (NOT NULL) [epics|stories|sprints]                        │
│     record_id    INTEGER (NOT NULL) [id of the changed record]                  │
│     field_name   TEXT (NOT NULL) [e.g., 'status']                               │
│     old_value    TEXT                                                           │
│     new_value    TEXT                                                           │
│     changed_by   TEXT [Agent name or 'system']                                  │
│     changed_at   TEXT (DEFAULT NOW)                                             │
│     reason       TEXT [Optional reason for change]                              │
│                                                                                 │
│ Indexes:                                                                        │
│   - idx_changes_record (table_name, record_id) [Composite]                      │
│                                                                                 │
│ Purpose: Complete audit trail of all status changes and field modifications     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Relationship Summary

### One-to-Many (1:N)
- **epics → stories**: One epic has many stories (via epic_num)
  - CASCADE on UPDATE and DELETE

- **stories → workflow_executions**: One story has many workflow executions
  - CASCADE on DELETE

- **sprints → story_assignments**: One sprint has many story assignments
  - CASCADE on DELETE

### Many-to-Many (N:M)
- **stories ↔ sprints**: Stories assigned to sprints (via story_assignments)
  - Junction table: story_assignments
  - Composite primary key: (sprint_num, epic_num, story_num)
  - CASCADE on DELETE from both sides

### Audit Trail
- **All tables → state_changes**: All status changes logged for audit trail
  - Triggered automatically by UPDATE triggers
  - No formal FK constraint (flexible audit log)

## Key Constraints

### Primary Keys (PK)
- All tables use INTEGER AUTOINCREMENT for internal id
- Business keys (epic_num, story_num, sprint_num) are UNIQUE but not PK

### Foreign Keys (FK)
- **stories.epic_num** → epics.epic_num (CASCADE)
- **story_assignments.sprint_num** → sprints.sprint_num (CASCADE)
- **story_assignments.(epic_num, story_num)** → stories.(epic_num, story_num) (CASCADE)
- **workflow_executions.(epic_num, story_num)** → stories.(epic_num, story_num) (CASCADE)

### Unique Constraints (UK)
- epics.epic_num
- stories.(epic_num, story_num) - Composite unique constraint
- sprints.sprint_num

### Check Constraints
- **epics.status**: IN ('planned', 'active', 'completed', 'cancelled')
- **stories.status**: IN ('pending', 'in_progress', 'done', 'blocked', 'cancelled')
- **stories.priority**: IN ('P0', 'P1', 'P2', 'P3')
- **sprints.status**: IN ('planned', 'active', 'completed', 'cancelled')
- **sprints dates**: end_date > start_date
- **workflow_executions.status**: IN ('started', 'running', 'completed', 'failed', 'cancelled')

## Indexes Strategy

### Single-Column Indexes
Used for direct lookups and simple filtering:
- Status fields (most common filter)
- Owner fields (assignment queries)
- Epic/story number lookups
- Workflow names

### Composite Indexes
Optimized for common query patterns:
- **idx_stories_epic_status** (epic_num, status): Get all stories in epic by status
- **idx_sprints_dates** (start_date, end_date): Date range queries
- **idx_changes_record** (table_name, record_id): Audit trail lookup

## Auto-Updated Fields

### Timestamps (via triggers)
- **updated_at**: Automatically set to NOW on any UPDATE
  - Applies to: epics, stories, sprints

### Calculated Fields (via triggers)
- **epics.completed_points**: Sum of points from all 'done' stories
  - Auto-updated when story status changes to/from 'done'
  - Ensures epic progress is always accurate

### Audit Trail (via triggers)
- **state_changes**: Automatic INSERT on status changes
  - Applies to: epics.status, stories.status, sprints.status
  - changed_by set to 'system' by default

## Data Integrity Features

1. **Referential Integrity**: PRAGMA foreign_keys = ON
2. **Cascade Deletions**: Prevent orphaned records
3. **Cascade Updates**: Keep relationships consistent
4. **Check Constraints**: Validate enum values and business rules
5. **Unique Constraints**: Prevent duplicate business identifiers
6. **Triggers**: Maintain calculated fields and audit trail
7. **JSON Validation**: SQLite 3.38+ validates JSON fields

## Notes

- **AI** = AUTOINCREMENT
- **FK** = Foreign Key
- **PK** = Primary Key
- **UK** = Unique Key
- **[Auto]** = Auto-updated by trigger
- All TEXT timestamps use ISO 8601 format: 'YYYY-MM-DD HH:MM:SS'
- All JSON fields support extensibility without schema changes
