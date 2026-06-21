// Typed data access layer. JSON is imported at build time and prerendered into
// pages, so there is no runtime data fetching for static content.

import factionsData from '../data/factions.json';
import rolesData from '../data/roles.json';
import summaryData from '../data/summary.json';
import unitsData from '../data/units.json';
import weaponsData from '../data/weapons.json';
import type { Faction, Role, Summary, Unit, Weapon } from './types';

export const units = unitsData as Unit[];
export const weapons = weaponsData as Weapon[];
export const factions = factionsData as Faction[];
export const roles = rolesData as Role[];
export const summary = summaryData as Summary;

const unitById = new Map(units.map((u) => [u.id, u]));
const weaponById = new Map(weapons.map((w) => [w.id, w]));

export function getUnit(id: number): Unit | undefined {
  return unitById.get(id);
}

export function getWeapon(id: number): Weapon | undefined {
  return weaponById.get(id);
}

/** Stable, URL-safe slug combining id + name for readable links. */
export function unitSlug(unit: Unit): string {
  return `${unit.id}-${slugify(unit.name)}`;
}

export function weaponSlug(weapon: Weapon): string {
  return `${weapon.id}-${slugify(weapon.name)}`;
}

/** Parse the leading numeric id out of a slug like "1006-tyranid-termagant". */
export function idFromSlug(slug: string): number {
  const n = Number.parseInt(slug, 10);
  return Number.isNaN(n) ? -1 : n;
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

/** Faction accent colors for visual coding across the UI. */
export const FACTION_COLORS: Record<string, string> = {
  'Blood Angels': '#c0392b',
  Ultramarines: '#2e5cb8',
  Tyranid: '#7d3cc4',
  Necrons: '#2fae62',
  'Mephrit Necrons': '#1f8f4e',
  'Adepta Sororitas': '#b03050',
  'Daemons of Khorne': '#8b1a1a',
  'Black Legion': '#5a5a66',
  Orks: '#5a7d2e',
  "T'au": '#c97b1e',
  'Astra Militarum': '#5c6b3a',
};

export function factionColor(name: string): string {
  return FACTION_COLORS[name] ?? '#c8a04a';
}

/** Dataset maxima used to scale stat bars in the UI. */
export const STAT_MAX = {
  health: Math.max(...units.map((u) => u.totalHealth)),
  armor: 9,
  evasion: 30,
  movement: Math.max(...units.map((u) => u.maxMovementPoints)),
  actionPoints: Math.max(...units.map((u) => u.maxActionPoints)),
};
