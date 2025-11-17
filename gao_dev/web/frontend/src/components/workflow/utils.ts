/**
 * Workflow utility functions
 *
 * Story 39.21: Workflow Detail Panel
 */

/**
 * Format duration from seconds to human-readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '0s';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<void> {
  await navigator.clipboard.writeText(text);
}

/**
 * Get file icon by extension
 */
export function getFileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';

  const iconMap: Record<string, string> = {
    ts: '📘',
    tsx: '⚛️',
    js: '📜',
    jsx: '⚛️',
    py: '🐍',
    md: '📝',
    json: '📋',
    yaml: '⚙️',
    yml: '⚙️',
    html: '🌐',
    css: '🎨',
    sh: '🔧',
    xml: '📄',
    sql: '🗄️',
    txt: '📃',
  };

  return iconMap[ext] || '📄';
}

/**
 * Format file size in bytes to human-readable string
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}
