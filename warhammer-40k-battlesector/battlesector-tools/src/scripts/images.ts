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
