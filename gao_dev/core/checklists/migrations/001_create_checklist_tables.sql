-- Checklist Execution Tracking Schema
-- Creates tables for tracking checklist executions and item results

-- Checklist executions table
CREATE TABLE IF NOT EXISTS checklist_executions (
    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_name TEXT NOT NULL,
    checklist_version TEXT NOT NULL,  -- Version of checklist executed
    artifact_type TEXT NOT NULL CHECK(artifact_type IN ('story', 'epic', 'prd', 'architecture', 'code')),
    artifact_id TEXT NOT NULL,  -- Story path, epic number, file path, etc.

    -- Story/Epic linkage
    epic_num INTEGER,
    story_num INTEGER,
    workflow_execution_id INTEGER,  -- Link to workflow that triggered this

    -- Execution metadata
    executed_by TEXT NOT NULL,  -- Agent or user who executed
    executed_at TEXT NOT NULL,  -- ISO timestamp
    completed_at TEXT,  -- ISO timestamp when completed
    duration_ms INTEGER,  -- Total execution time

    -- Status
    overall_status TEXT NOT NULL CHECK(overall_status IN ('in_progress', 'pass', 'fail', 'partial')),

    -- Additional metadata
    notes TEXT,  -- Overall execution notes
    metadata TEXT  -- JSON metadata (environment, context, etc.)
);

-- Checklist item results table
CREATE TABLE IF NOT EXISTS checklist_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL REFERENCES checklist_executions(execution_id) ON DELETE CASCADE,

    -- Item identification
    item_id TEXT NOT NULL,  -- Item ID from checklist definition
    item_category TEXT,  -- Category for grouping

    -- Result
    status TEXT NOT NULL CHECK(status IN ('pass', 'fail', 'skip', 'na')),
    notes TEXT,  -- Notes for this specific item (reason for fail/skip)

    -- Tracking
    checked_at TEXT NOT NULL,  -- ISO timestamp
    checked_by TEXT,  -- Could differ from overall executed_by

    -- Evidence (optional)
    evidence_path TEXT,  -- Path to evidence file/screenshot
    evidence_metadata TEXT  -- JSON evidence metadata
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_executions_checklist ON checklist_executions(checklist_name);
CREATE INDEX IF NOT EXISTS idx_executions_artifact ON checklist_executions(artifact_type, artifact_id);
CREATE INDEX IF NOT EXISTS idx_executions_story ON checklist_executions(epic_num, story_num);
CREATE INDEX IF NOT EXISTS idx_executions_status ON checklist_executions(overall_status);
CREATE INDEX IF NOT EXISTS idx_executions_date ON checklist_executions(executed_at);
CREATE INDEX IF NOT EXISTS idx_results_execution ON checklist_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_results_status ON checklist_results(status);
