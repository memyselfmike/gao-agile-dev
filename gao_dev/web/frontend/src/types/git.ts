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
 * Commit list API response
 */
export interface CommitListResponse {
  commits: Commit[];
  total: number;
  has_more: boolean;
}

/**
 * Git timeline filters
 */
export interface GitTimelineFilters {
  author?: string;
  since?: string; // ISO 8601 date
  until?: string; // ISO 8601 date
}
