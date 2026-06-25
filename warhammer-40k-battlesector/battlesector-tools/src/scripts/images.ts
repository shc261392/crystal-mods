/**
 * Image URL resolution for game assets hosted on Cloudflare R2
 */

import imageUrls from '../data/image-urls.json';

export type ImageCategory = 'units' | 'weapons' | 'factions';

export interface ImageInfo {
  url: string;
  r2_key: string;
  source: string;
}

/**
 * Get image URL for a specific asset by name and category
 */
export function getImageUrl(category: ImageCategory, name: string): string | null {
  const categoryData = imageUrls[category];
  if (!categoryData) return null;

  const imageInfo = categoryData[name as keyof typeof categoryData];
  return imageInfo ? (imageInfo as ImageInfo).url : null;
}

/**
 * Get all image URLs for a category
 */
export function getCategoryImages(category: ImageCategory): Record<string, ImageInfo> {
  return (imageUrls[category] || {}) as Record<string, ImageInfo>;
}

/**
 * Find image URL by partial name match (case-insensitive)
 */
export function findImageByName(category: ImageCategory, partialName: string): ImageInfo | null {
  const categoryData = imageUrls[category];
  if (!categoryData) return null;

  const lowerSearch = partialName.toLowerCase();
  const entry = Object.entries(categoryData).find(([name]) =>
    name.toLowerCase().includes(lowerSearch),
  );

  return entry ? (entry[1] as ImageInfo) : null;
}

/**
 * Get unit icon URL
 */
export function getUnitIcon(unitName: string): string | null {
  return getImageUrl('units', unitName);
}

/**
 * Get weapon icon URL
 */
export function getWeaponIcon(weaponName: string): string | null {
  return getImageUrl('weapons', weaponName);
}

/**
 * Get faction banner/asset URL
 */
export function getFactionAsset(assetName: string): string | null {
  return getImageUrl('factions', assetName);
}

/**
 * Check if an image exists for a given name/category
 */
export function hasImage(category: ImageCategory, name: string): boolean {
  return getImageUrl(category, name) !== null;
}

/**
 * Faction emblem artwork keyed by faction id. Only factions whose crest was
 * shipped as a standalone texture are mapped; the rest fall back to a styled
 * monogram badge rendered in the faction accent color.
 */
const FACTION_EMBLEMS: Record<number, { category: ImageCategory; key: string }> = {
  0: { category: 'factions', key: '3CCUI_side_column_factionSelect-BloodAngels' },
  1: { category: 'factions', key: '3CCUI_side_column_factionSelect-Tyranids' },
  2: { category: 'factions', key: '3CCUI_side_column_factionSelect-BattleSisters' },
  3: { category: 'factions', key: '3CCUI_side_column_factionSelect-Necrons' },
  4: { category: 'factions', key: '3CCUI_side_column_factionSelect-Necrons' },
  5: { category: 'factions', key: '3CCUI_side_column_factionSelect-KhorneDaemons' },
  7: { category: 'factions', key: '3CCUI_side_column_factionSelect-AstraMilitarum' },
  8: { category: 'factions', key: '3CCUI_side_column_factionSelect-Orks' },
  9: { category: 'factions', key: '3CCUI_side_column_factionSelect-Tau' },
  10: { category: 'factions', key: '3CCUI_side_column_factionSelect-BlackLegion' },
  11: { category: 'factions', key: '3CCUI_side_column_factionSelect-Ultramarines' },
};

/** Resolve a faction's emblem URL, or null when no crest texture exists. */
export function getFactionEmblem(factionId: number): string | null {
  const ref = FACTION_EMBLEMS[factionId];
  if (!ref) return null;
  return getImageUrl(ref.category, ref.key);
}

/**
 * Unit portrait rules. Battlesector renders most units as 3D models with no
 * standalone portrait texture, so only a handful of units have real artwork.
 * Rules are evaluated in order; the first matching pattern wins.
 */
const PORTRAIT_RULES: Array<[RegExp, string]> = [
  [/intercessor/i, 'IntercessorIcon'],
  [/assault (squad|terminators?|marines?)/i, 'AssualtMarineIcon'],
  [/librarian dreadnought/i, 'LibrarianDreadnoughtIcon-small'],
  [/inceptor/i, 'InceptorIcon-small'],
  [/techmarine/i, 'TechmarineIcon'],
  [/hormagaunt/i, 'HormagauntIcon'],
  [/gladiator lancer/i, 'GladiatorLancerIcon'],
];

/** Resolve a unit's portrait URL. Prefers the unit's own portrait key (from the
 * Selection-portraits set), falling back to name-pattern rules. */
export function getUnitPortrait(unitName: string, portraitKey?: string): string | null {
  if (portraitKey) {
    const url = getImageUrl('units', portraitKey);
    if (url) return url;
  }
  for (const [pattern, key] of PORTRAIT_RULES) {
    if (pattern.test(unitName)) return getImageUrl('units', key);
  }
  return null;
}

/** Icon used to denote a weapon's attack type (melee vs ranged/ballistic). */
export function getWeaponTypeIcon(isMelee: boolean): string | null {
  return getImageUrl('units', isMelee ? 'MeleeDamageIcon' : 'BalisticDamageIcon');
}
