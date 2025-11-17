/**
 * Utility functions for metrics dashboard
 *
 * Story 39.23: Workflow Metrics Dashboard
 */

/**
 * Format duration in seconds to human-readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.round(seconds % 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  return `${minutes}m ${secs}s`;
}

/**
 * Format large numbers with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Get color for success rate
 */
export function getSuccessRateColor(rate: number): string {
  if (rate >= 90) return 'text-green-600';
  if (rate >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

/**
 * Get background color for success rate
 */
export function getSuccessRateBgColor(rate: number): string {
  if (rate >= 90) return 'bg-green-100';
  if (rate >= 70) return 'bg-yellow-100';
  return 'bg-red-100';
}
