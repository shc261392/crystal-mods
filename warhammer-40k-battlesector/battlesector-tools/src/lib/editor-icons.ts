/**
 * Builds the merged icon catalog used by the editor icon pickers: unit
 * portraits + weapon icons (from image-urls.json, served via R2) plus local
 * ability icons under public/ability-icons/. Runs at build/SSR time only.
 */
import { readdir } from 'node:fs/promises';
import { join } from 'node:path';
import imageUrls from '../data/image-urls.json';

export interface IconOption {
  key: string;
  url: string;
  source?: string;
}

type UrlMap = Record<string, { url: string; source?: string }>;

export async function buildIconCatalog(): Promise<IconOption[]> {
  let abilityIconFiles: string[] = [];
  try {
    abilityIconFiles = await readdir(join(process.cwd(), 'public', 'ability-icons'));
  } catch {
    // ability-icons dir may not exist locally; ignore.
  }

  const units = (imageUrls.units ?? {}) as UrlMap;
  const weapons = (imageUrls.weapons ?? {}) as UrlMap;

  return [
    ...Object.entries(units).map(([key, value]) => ({
      key,
      url: value.url,
      source: value.source || 'unit',
    })),
    ...Object.entries(weapons).map(([key, value]) => ({
      key,
      url: value.url,
      source: value.source || 'weapon',
    })),
    ...abilityIconFiles
      .filter((file) => file.endsWith('.png'))
      .map((file) => ({
        key: file.replace('.png', '').replace('Icon', ''),
        url: `/ability-icons/${file}`,
        source: file.toLowerCase().includes('icon') ? 'ability' : 'ability-passive',
      })),
  ]
    .filter((item) => typeof item.url === 'string' && item.url.length > 0)
    .sort((a, b) => a.key.localeCompare(b.key));
}

/**
 * Resolve a stored icon reference to a preview URL. Accepts either an
 * image-urls.json key (unit portrait / weapon icon) or an already-resolved
 * path/URL. Returns undefined when nothing usable is found.
 */
export function resolveIconUrl(
  value: string | undefined,
  kind: 'units' | 'weapons',
): string | undefined {
  if (!value) return undefined;
  if (value.startsWith('/') || value.startsWith('http')) return value;
  const map = (imageUrls[kind] ?? {}) as UrlMap;
  return map[value]?.url;
}
