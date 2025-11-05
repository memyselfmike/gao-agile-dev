-- GAO-Dev State Tracking Database Schema
-- Version: 1.0.0
-- Description: Complete SQLite schema for epics, stories, sprints, workflow executions, and state changes

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Epics table
CREATE TABLE IF NOT EXISTS epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    feature TEXT,
    goal TEXT,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'completed', 'cancelled')) DEFAULT 'planned',

    -- Points tracking
    total_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0,

    -- Ownership
    owner TEXT,
    created_by TEXT,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- File sync
    file_path TEXT,
    content_hash TEXT,  -- SHA256 for conflict detection

    -- Extensible metadata
    metadata JSON
);

-- Stories table
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_num INTEGER NOT NULL REFERENCES epics(epic_num) ON UPDATE CASCADE ON DELETE CASCADE,
    story_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,

    -- Status and priority
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'done', 'blocked', 'cancelled')) DEFAULT 'pending',
    priority TEXT CHECK(priority IN ('P0', 'P1', 'P2', 'P3')) DEFAULT 'P1',

    -- Story points
    points INTEGER DEFAULT 0,

    -- Ownership
    owner TEXT,
    created_by TEXT,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    due_date TEXT,

    -- File sync
    file_path TEXT,
    content_hash TEXT,

    -- Extensible metadata
    metadata JSON,
    tags JSON,  -- JSON array of tag strings

    -- Unique constraint
    UNIQUE(epic_num, story_num)
);

-- Sprints table
CREATE TABLE IF NOT EXISTS sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    goal TEXT,

    -- Status
    status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'completed', 'cancelled')) DEFAULT 'planned',

    -- Dates
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Metrics
    planned_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0,
    velocity REAL DEFAULT 0.0,  -- Calculated: completed_points / planned duration

    -- Extensible metadata
    metadata JSON,

    -- Date validation
    CHECK(end_date > start_date)
);

-- Story assignments (many-to-many: stories <-> sprints)
CREATE TABLE IF NOT EXISTS story_assignments (
    sprint_num INTEGER NOT NULL REFERENCES sprints(sprint_num) ON DELETE CASCADE,
    epic_num INTEGER NOT NULL,
    story_num INTEGER NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (sprint_num, epic_num, story_num),
    FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num) ON DELETE CASCADE
);

-- Workflow executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    phase TEXT,  -- analysis, planning, implementation, etc.

    -- Story linkage
    epic_num INTEGER,
    story_num INTEGER,

    -- Execution details
    status TEXT NOT NULL CHECK(status IN ('started', 'running', 'completed', 'failed', 'cancelled')) DEFAULT 'started',
    executor TEXT NOT NULL,  -- Agent name (John, Amelia, etc.)

    -- Timing
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    duration_ms INTEGER,

    -- Results
    output TEXT,
    error_message TEXT,
    exit_code INTEGER,

    -- Extensible metadata
    metadata JSON,
    context_snapshot JSON,  -- Snapshot of WorkflowContext at execution

    FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num) ON DELETE CASCADE
);

-- State change history (audit trail)
CREATE TABLE IF NOT EXISTS state_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,  -- Agent or user
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    reason TEXT  -- Optional reason for change
);

-- Indexes for performance

-- Stories indexes
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_epic ON stories(epic_num);
CREATE INDEX IF NOT EXISTS idx_stories_priority ON stories(priority);
CREATE INDEX IF NOT EXISTS idx_stories_owner ON stories(owner);
CREATE INDEX IF NOT EXISTS idx_stories_epic_status ON stories(epic_num, status);  -- Composite for common query

-- Epics indexes
CREATE INDEX IF NOT EXISTS idx_epics_status ON epics(status);
CREATE INDEX IF NOT EXISTS idx_epics_feature ON epics(feature);

-- Sprints indexes
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);
CREATE INDEX IF NOT EXISTS idx_sprints_dates ON sprints(start_date, end_date);

-- Story assignments indexes
CREATE INDEX IF NOT EXISTS idx_assignments_sprint ON story_assignments(sprint_num);
CREATE INDEX IF NOT EXISTS idx_assignments_story ON story_assignments(epic_num, story_num);

-- Workflow executions indexes
CREATE INDEX IF NOT EXISTS idx_workflow_story ON workflow_executions(epic_num, story_num);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_name ON workflow_executions(workflow_name);

-- State changes index
CREATE INDEX IF NOT EXISTS idx_changes_record ON state_changes(table_name, record_id);

-- Triggers for auto-updating timestamps

CREATE TRIGGER IF NOT EXISTS update_epic_timestamp
AFTER UPDATE ON epics
FOR EACH ROW
BEGIN
    UPDATE epics SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_story_timestamp
AFTER UPDATE ON stories
FOR EACH ROW
BEGIN
    UPDATE stories SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sprint_timestamp
AFTER UPDATE ON sprints
FOR EACH ROW
BEGIN
    UPDATE sprints SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger for updating epic completed_points when story status changes
CREATE TRIGGER IF NOT EXISTS update_epic_points_on_story_status
AFTER UPDATE OF status ON stories
FOR EACH ROW
WHEN NEW.status = 'done' AND OLD.status != 'done'
BEGIN
    UPDATE epics
    SET completed_points = (
        SELECT COALESCE(SUM(points), 0)
        FROM stories
        WHERE epic_num = NEW.epic_num AND status = 'done'
    )
    WHERE epic_num = NEW.epic_num;
END;

-- Trigger for recalculating epic completed_points when story changes from done to other status
CREATE TRIGGER IF NOT EXISTS update_epic_points_on_story_status_revert
AFTER UPDATE OF status ON stories
FOR EACH ROW
WHEN OLD.status = 'done' AND NEW.status != 'done'
BEGIN
    UPDATE epics
    SET completed_points = (
        SELECT COALESCE(SUM(points), 0)
        FROM stories
        WHERE epic_num = NEW.epic_num AND status = 'done'
    )
    WHERE epic_num = NEW.epic_num;
END;

-- Trigger for logging story status changes (audit trail)
CREATE TRIGGER IF NOT EXISTS log_story_status_change
AFTER UPDATE OF status ON stories
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('stories', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;

-- Trigger for logging epic status changes (audit trail)
CREATE TRIGGER IF NOT EXISTS log_epic_status_change
AFTER UPDATE OF status ON epics
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('epics', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;

-- Trigger for logging sprint status changes (audit trail)
CREATE TRIGGER IF NOT EXISTS log_sprint_status_change
AFTER UPDATE OF status ON sprints
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('sprints', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;
