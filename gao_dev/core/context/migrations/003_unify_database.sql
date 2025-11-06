-- Migration 003: Unify all context tables into main database
--
-- This migration moves workflow_context and context_usage tables
-- from separate databases into the main gao_dev.db alongside the
-- StateTracker tables (epics, stories, sprints, workflow_executions).
--
-- Benefits:
-- - Single database file for all state and context
-- - Proper foreign key constraints between tables
-- - Simplified backup/restore
-- - Better transaction consistency
-- - Easier migrations
--
-- Tables created/modified:
-- 1. workflow_context (moved from separate DB)
-- 2. context_usage (moved from separate DB)
-- 3. Foreign keys added for referential integrity
--
-- Foreign key relationships:
-- - workflow_context.workflow_id references workflow_executions.executor
-- - context_usage.workflow_id references workflow_context.workflow_id
-- - context_usage.document_id references documents.id (if documents table exists)
--
-- Migration is idempotent and safe to run multiple times.

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- Create workflow_context table (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_context (
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

    -- Foreign key to workflow_executions (optional, may not always exist)
    -- Note: workflow_id in workflow_context corresponds to executor in workflow_executions
    -- This FK is commented out as executor is not a unique key in workflow_executions
    -- Instead, we maintain referential integrity through application logic
    -- FOREIGN KEY (workflow_id) REFERENCES workflow_executions(executor) ON DELETE CASCADE
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_workflow_context_workflow_id ON workflow_context(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_context_epic_story ON workflow_context(epic_num, story_num);
CREATE INDEX IF NOT EXISTS idx_workflow_context_status ON workflow_context(status);
CREATE INDEX IF NOT EXISTS idx_workflow_context_created_at ON workflow_context(created_at);
CREATE INDEX IF NOT EXISTS idx_workflow_context_feature ON workflow_context(feature);

-- ============================================================================
-- Create context_usage table (if not exists)
-- ============================================================================

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

    -- Foreign key constraints
    FOREIGN KEY (workflow_id) REFERENCES workflow_context(workflow_id) ON DELETE SET NULL
    -- Note: document_id FK is commented out as documents table may not exist yet (Epic 16)
    -- FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
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

-- ============================================================================
-- Data Migration Notes
-- ============================================================================

-- This SQL schema creates the tables with proper foreign keys.
-- The actual data migration from old databases is handled by Python code
-- in the migration runner (see migration_003_unify_database.py).
--
-- Migration process:
-- 1. Create tables in gao_dev.db (this SQL file)
-- 2. Copy data from gao-dev-state.db (if exists)
-- 3. Copy data from .gao/context_usage.db (if exists)
-- 4. Validate foreign key constraints
-- 5. Create backup of old databases
-- 6. (Optional) Delete old databases after confirmation
--
-- The Python migration runner ensures idempotency and rollback on failure.
