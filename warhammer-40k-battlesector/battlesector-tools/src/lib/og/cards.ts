import { getFactionEmblem, getUnitPortrait, getWeaponPortrait } from '../../scripts/images';
/**
 * OG card layouts for units, weapons and the site default. Each builder returns
 * a Satori virtual DOM (see ./render). Card art is embedded best-effort; text
 * content (stats, weapons, abilities) always renders.
 */
import { factionColor, units } from '../data';
import type { Unit, Weapon } from '../types';
import { getAbilities } from '../unit-abilities';
import { weaponClass } from '../weapon-display';
import { imageDataUri } from './images';
import { type OGNode, h } from './render';

const BG = '#14161d';
const INK = '#e9e7e0';
const FAINT = '#9a948a';
const GOLD = '#c8a04a';
const SITE = 'wh40k-battlesector.crystalgametools.org';

/** Convert a #rrggbb hex to rgba() with the given alpha. */
function alpha(hex: string, a: number): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m || !m[1]) return hex;
  const n = Number.parseInt(m[1], 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

function titleSize(name: string): number {
  const n = name.length;
  if (n <= 13) return 66;
  if (n <= 20) return 56;
  if (n <= 30) return 46;
  return 38;
}

function eyebrow(accent: string, primary: string, secondary?: string): OGNode {
  return h(
    'div',
    { style: { alignItems: 'center', gap: 12, fontSize: 25, fontWeight: 700 } },
    h('span', { style: { color: accent, letterSpacing: 0.5 } }, primary),
    secondary && h('span', { style: { color: FAINT } }, '•'),
    secondary && h('span', { style: { color: FAINT, fontWeight: 600 } }, secondary),
  );
}

function statChip(label: string, value: string | number, accent: string): OGNode {
  return h(
    'div',
    {
      style: {
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 2,
        padding: '10px 16px',
        borderRadius: 12,
        background: alpha(accent, 0.14),
        border: `1px solid ${alpha(accent, 0.4)}`,
      },
    },
    h('span', { style: { fontSize: 32, fontWeight: 700, color: INK } }, String(value)),
    h(
      'span',
      { style: { fontSize: 14, fontWeight: 600, color: FAINT, letterSpacing: 1 } },
      label.toUpperCase(),
    ),
  );
}

function pillRow(label: string, items: string[], accent: string): OGNode | false {
  if (items.length === 0) return false;
  return h(
    'div',
    { style: { flexDirection: 'column', gap: 8 } },
    h(
      'span',
      { style: { fontSize: 15, fontWeight: 700, color: FAINT, letterSpacing: 1.5 } },
      label,
    ),
    h(
      'div',
      { style: { flexWrap: 'wrap', gap: 8 } },
      ...items.map((t) =>
        h(
          'div',
          {
            style: {
              fontSize: 20,
              fontWeight: 600,
              color: INK,
              padding: '5px 14px',
              borderRadius: 999,
              background: 'rgba(255,255,255,0.06)',
              border: `1px solid ${alpha(accent, 0.35)}`,
            },
          },
          t,
        ),
      ),
    ),
  );
}

function artPanel(accent: string, art: string | null, fallbackLabel: string): OGNode {
  return h(
    'div',
    {
      style: {
        width: 430,
        flexShrink: 0,
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(150deg, ${alpha(accent, 0.42)} 0%, ${alpha(accent, 0.08)} 55%, ${BG} 100%)`,
        borderRight: '1px solid rgba(255,255,255,0.08)',
      },
    },
    art
      ? h('img', { src: art, width: 340, height: 340, style: { objectFit: 'contain' } })
      : h(
          'div',
          {
            style: {
              width: 220,
              height: 220,
              borderRadius: 20,
              alignItems: 'center',
              justifyContent: 'center',
              background: alpha(accent, 0.3),
              border: `2px solid ${alpha(accent, 0.6)}`,
              fontSize: 90,
              fontWeight: 700,
              color: INK,
            },
          },
          fallbackLabel,
        ),
  );
}

function footer(rightBadge: OGNode | false): OGNode {
  return h(
    'div',
    { style: { alignItems: 'center', justifyContent: 'space-between', marginTop: 8 } },
    h('span', { style: { fontSize: 20, fontWeight: 600, color: FAINT } }, SITE),
    rightBadge,
  );
}

function frame(accent: string, ...columns: OGNode[]): OGNode {
  return h(
    'div',
    {
      style: {
        width: '100%',
        height: '100%',
        position: 'relative',
        background: BG,
        fontFamily: 'Inter',
        color: INK,
      },
    },
    h('div', {
      style: { position: 'absolute', left: 0, top: 0, bottom: 0, width: 14, background: accent },
    }),
    h('div', { style: { flex: 1, flexDirection: 'row' } }, ...columns),
  );
}

export async function unitCard(unit: Unit): Promise<OGNode> {
  const accent = factionColor(unit.factionName);
  const art = await imageDataUri(
    getUnitPortrait(unit.name, unit.portrait) ?? getFactionEmblem(unit.faction),
  );
  const initials = unit.factionName
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const weaponNames = [
    ...new Set(unit.weaponSlots.flatMap((s) => s.options.map((o) => o.name))),
  ].slice(0, 5);
  const abilityNames = getAbilities(unit.abilityIds ?? [])
    .map((a) => a.title)
    .slice(0, 3);

  const armorValue = unit.armorProfile === 1 ? `${unit.armorFront}◆` : unit.armor;

  const content = h(
    'div',
    {
      style: {
        flex: 1,
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '52px 56px',
      },
    },
    h(
      'div',
      { style: { flexDirection: 'column', gap: 18 } },
      eyebrow(accent, unit.factionName, unit.roleName),
      h(
        'span',
        { style: { fontSize: titleSize(unit.name), fontWeight: 700, lineHeight: 1.05 } },
        unit.name,
      ),
      h(
        'div',
        { style: { gap: 12, marginTop: 4 } },
        statChip('HP', unit.totalHealth, '#39904b'),
        statChip('AP', unit.maxActionPoints, '#8f5b36'),
        statChip('MP', unit.maxMovementPoints, '#2662aa'),
        statChip('Armor', armorValue, '#6299b8'),
        statChip('Dodge', unit.evasion, GOLD),
      ),
      pillRow('WEAPONS', weaponNames, accent),
      pillRow('ABILITIES', abilityNames, accent),
    ),
    footer(
      h(
        'div',
        {
          style: {
            fontSize: 24,
            fontWeight: 700,
            color: GOLD,
            padding: '6px 18px',
            borderRadius: 10,
            border: `1px solid ${alpha(GOLD, 0.5)}`,
            background: alpha(GOLD, 0.12),
          },
        },
        `${unit.pointCost} PTS`,
      ),
    ),
  );

  return frame(accent, artPanel(accent, art, initials), content);
}

export async function weaponCard(weapon: Weapon): Promise<OGNode> {
  const accent = GOLD;
  const art = await imageDataUri(getWeaponPortrait(weapon.icon));
  const cls = weaponClass(weapon);
  const typeLabel = weapon.isMelee ? 'Melee' : 'Ranged';
  const initials = weapon.name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const chips: OGNode[] = [
    statChip('Damage', weapon.damage, '#b0472e'),
    statChip('Accuracy', `${weapon.accuracy}%`, '#2662aa'),
    statChip('Attacks', weapon.numAttacks, '#39904b'),
    statChip('AP', weapon.armorPiercing, '#8f5b36'),
  ];
  if (!weapon.isMelee && weapon.rangeMax > 0) {
    chips.push(statChip('Range', weapon.rangeMax, '#6299b8'));
  }

  const carriers = [
    ...new Set(
      units
        .filter((u) => u.weaponSlots.some((s) => s.options.some((o) => o.weaponId === weapon.id)))
        .map((u) => u.name),
    ),
  ];
  const carrierNames = carriers.slice(0, 6);
  if (carriers.length > carrierNames.length) {
    carrierNames.push(`+${carriers.length - carrierNames.length} more`);
  }

  const content = h(
    'div',
    {
      style: {
        flex: 1,
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '52px 56px',
      },
    },
    h(
      'div',
      { style: { flexDirection: 'column', gap: 20 } },
      eyebrow(
        accent,
        `${typeLabel} weapon`,
        cls !== 'melee' && cls !== 'ballistic' ? cls : undefined,
      ),
      h(
        'span',
        { style: { fontSize: titleSize(weapon.name), fontWeight: 700, lineHeight: 1.05 } },
        weapon.name,
      ),
      h('div', { style: { gap: 12, marginTop: 4, flexWrap: 'wrap' } }, ...chips),
      pillRow('CARRIED BY', carrierNames, accent),
    ),
    footer(false),
  );

  return frame(accent, artPanel(accent, art, initials), content);
}

export function defaultCard(title: string, description: string): OGNode {
  const accent = GOLD;
  return frame(
    accent,
    h(
      'div',
      {
        style: {
          flex: 1,
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 22,
          padding: '0 90px',
        },
      },
      h(
        'span',
        { style: { fontSize: 22, fontWeight: 700, color: accent, letterSpacing: 3 } },
        'WARHAMMER 40,000: BATTLESECTOR',
      ),
      h('span', { style: { fontSize: 72, fontWeight: 700, lineHeight: 1.05 } }, title),
      h(
        'span',
        { style: { fontSize: 27, color: FAINT, lineHeight: 1.35, maxWidth: 900 } },
        description,
      ),
      footer(false),
    ),
  );
}
