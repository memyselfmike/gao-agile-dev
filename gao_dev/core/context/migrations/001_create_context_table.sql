-- Migration 001: Create workflow_context table
--
-- This migration creates the workflow_context table for storing serialized
-- WorkflowContext instances with versioning, indexing, and efficient queries.
--
-- Features:
-- - Unique workflow_id for each execution
-- - Epic and story number tracking
-- - JSON blob for serialized context data
-- - Auto-incrementing version field for versioning
-- - Status tracking (running, completed, failed, paused)
-- - Comprehensive indexes for fast lookups
-- - Timestamp tracking for audit trail

CREATE TABLE workflow_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT UNIQUE NOT NULL,
    epic_num INTEGER NOT NULL,
    story_num INTEGER,
    feature TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    current_phase TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'paused')),
    context_data TEXT NOT NULL,  -- JSON blob
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for fast lookups
CREATE INDEX idx_workflow_context_workflow_id ON workflow_context(workflow_id);
CREATE INDEX idx_workflow_context_epic_story ON workflow_context(epic_num, story_num);
CREATE INDEX idx_workflow_context_status ON workflow_context(status);
CREATE INDEX idx_workflow_context_created_at ON workflow_context(created_at);
CREATE INDEX idx_workflow_context_feature ON workflow_context(feature);
