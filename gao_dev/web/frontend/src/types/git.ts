/**
 * Git-related type definitions for GAO-Dev web interface
 */

/**
 * Commit author information
 */
export interface CommitAuthor {
  name: string;
  email: string;
  is_agent: boolean;
}

/**
 * Git commit information
 */
export interface Commit {
  hash: string;
  short_hash: string;
  message: string;
  author: CommitAuthor;
  timestamp: string; // ISO 8601 format
  files_changed: number;
  insertions: number;
  deletions: number;
}

/**
 * Commit filters
 */
export interface CommitFilters {
  author?: string | null;
  since?: string | null;
  until?: string | null;
  search?: string | null;
}

/**
 * Commit list API response
 */
export interface CommitListResponse {
  commits: Commit[];
  total: number;
  total_unfiltered: number;
  has_more: boolean;
  filters_applied: CommitFilters;
}

/**
 * Git timeline filters
 */
export interface GitTimelineFilters {
  author?: string;
  since?: string; // ISO 8601 date
  until?: string; // ISO 8601 date
  search?: string;
}

/**
 * File change information in a commit diff
 */
export interface FileChange {
  path: string;
  change_type: 'added' | 'modified' | 'deleted';
  insertions: number;
  deletions: number;
  is_binary: boolean;
  diff?: string;
  original_content?: string;
  modified_content?: string;
}

/**
 * Commit diff API response
 */
export interface CommitDiffResponse {
  files: FileChange[];
}
