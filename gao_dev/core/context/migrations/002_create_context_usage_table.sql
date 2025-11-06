-- Migration 002: Create context_usage table for context lineage tracking
--
-- This migration creates the context_usage table for tracking which context
-- (document versions) was used for which artifacts during workflow execution.
-- This provides a compliance audit trail showing what architecture/PRD version
-- was used for each implementation.
--
-- Features:
-- - Track document usage by artifact (epic, story, etc.)
-- - Link to documents table via document_id
-- - Link to workflow_executions table via workflow_id
-- - Record document version (content hash) at time of use
-- - Detect stale context usage (using obsolete documents)
-- - Support lineage queries ("What architecture was used for Story 3.1?")
--
-- Performance targets:
-- - Record usage: <50ms
-- - Query lineage: <100ms

CREATE TABLE IF NOT EXISTS context_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Artifact identification
    artifact_type TEXT NOT NULL CHECK(artifact_type IN (
        'epic', 'story', 'task', 'code', 'test', 'doc', 'other'
    )),
    artifact_id TEXT NOT NULL,  -- e.g., "3.1", "epic-5", "story-3.2"

    -- Document reference
    document_id INTEGER,  -- Foreign key to documents table (nullable for non-doc context)
    document_path TEXT,  -- Document path for reference
    document_type TEXT,  -- Document type (prd, architecture, epic, story, etc.)
    document_version TEXT NOT NULL,  -- Content hash at time of use

    -- Workflow context
    workflow_id TEXT,  -- Foreign key to workflow_context table (nullable)
    workflow_name TEXT,  -- Workflow name for reference

    -- Epic/Story context
    epic INTEGER,
    story TEXT,

    -- Timestamps
    accessed_at TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraints (non-strict to allow for missing documents)
    FOREIGN KEY (workflow_id) REFERENCES workflow_context(workflow_id) ON DELETE SET NULL
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_context_usage_artifact
    ON context_usage(artifact_type, artifact_id);

CREATE INDEX IF NOT EXISTS idx_context_usage_document_id
    ON context_usage(document_id);

CREATE INDEX IF NOT EXISTS idx_context_usage_document_version
    ON context_usage(document_version);

CREATE INDEX IF NOT EXISTS idx_context_usage_workflow_id
    ON context_usage(workflow_id);

CREATE INDEX IF NOT EXISTS idx_context_usage_epic_story
    ON context_usage(epic, story);

CREATE INDEX IF NOT EXISTS idx_context_usage_accessed_at
    ON context_usage(accessed_at);

-- Composite index for common query: "What context was used for this artifact?"
CREATE INDEX IF NOT EXISTS idx_context_usage_artifact_lookup
    ON context_usage(artifact_type, artifact_id, accessed_at DESC);
