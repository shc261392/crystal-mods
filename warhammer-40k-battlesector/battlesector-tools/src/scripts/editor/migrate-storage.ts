/**
 * Storage migration utility to clean up obsolete draft keys.
 *
 * Old pattern (before 2026-07-07):
 *   bs-editor-draft:weapon:9005:name = "..."
 *   bs-editor-draft:weapon:9005:damage = "5"
 *
 * New pattern:
 *   bs-editor-data:weapon = { "9005": { name: "...", damage: 5 }, ... }
 *
 * This runs automatically on editor page load to clean up old keys.
 */

const DRAFT_PREFIX = 'bs-editor-draft:';

export function migrateStorage(): void {
  try {
    const keysToRemove: string[] = [];

    // Scan for old draft keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith(DRAFT_PREFIX)) {
        keysToRemove.push(key);
      }
    }

    if (keysToRemove.length > 0) {
      console.log(`[storage-migration] Removing ${keysToRemove.length} obsolete draft keys`);
      for (const key of keysToRemove) {
        localStorage.removeItem(key);
      }
      console.log('[storage-migration] Migration complete');
    }
  } catch (err) {
    console.warn('[storage-migration] Failed to migrate storage:', err);
    // Non-critical, don't show error to user
  }
}
