/**
 * Best-effort image loader for OG cards.
 *
 * Unit/weapon/faction art lives on Cloudflare R2. During `astro build` we fetch
 * each asset once, cache the bytes on disk (so repeat builds are fast and don't
 * hammer R2) and return a base64 data URI that Satori can embed. Every failure
 * mode is swallowed and returns `null` — a missing portrait must never break the
 * build; the card simply falls back to a solid faction-coloured panel.
 */
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CACHE_DIR = join(tmpdir(), 'bs-og-image-cache');
let cacheReady: Promise<void> | null = null;
const memo = new Map<string, Promise<string | null>>();

function ensureCacheDir() {
  if (!cacheReady) cacheReady = mkdir(CACHE_DIR, { recursive: true }).then(() => undefined);
  return cacheReady;
}

function mimeFor(url: string): string {
  if (/\.png(\?|$)/i.test(url)) return 'image/png';
  if (/\.jpe?g(\?|$)/i.test(url)) return 'image/jpeg';
  if (/\.webp(\?|$)/i.test(url)) return 'image/webp';
  if (/\.gif(\?|$)/i.test(url)) return 'image/gif';
  return 'image/png';
}

async function load(url: string): Promise<string | null> {
  await ensureCacheDir();
  const key = createHash('sha1').update(url).digest('hex');
  const file = join(CACHE_DIR, key);
  const mime = mimeFor(url);
  try {
    const cached = await readFile(file);
    return `data:${mime};base64,${cached.toString('base64')}`;
  } catch {
    // not cached yet
  }
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const bytes = Buffer.from(await res.arrayBuffer());
    await writeFile(file, bytes).catch(() => {});
    return `data:${mime};base64,${bytes.toString('base64')}`;
  } catch {
    return null;
  }
}

/** Returns a data URI for the remote image, or null on any failure. Memoised. */
export function imageDataUri(url: string | null | undefined): Promise<string | null> {
  if (!url) return Promise.resolve(null);
  let p = memo.get(url);
  if (!p) {
    p = load(url);
    memo.set(url, p);
  }
  return p;
}
