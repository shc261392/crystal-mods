// Damage calculator: wires the form to the shared combat formulas. Weapon and
// unit datasets are imported (bundled by Vite) so selecting one auto-fills the
// inputs. State is reflected in the URL for sharing.

import buffsData from '../data/buffs.json';
import factionMomentumData from '../data/faction-momentum.json';
import factionsData from '../data/factions.json';
import unitsData from '../data/units.json';
import weaponsData from '../data/weapons.json';
import {
  critChance,
  damagePerHitAfterArmor,
  damageRange,
  damageRangeAfterArmor,
  expectedDamage,
  grazeChance,
  hitChance,
  modelsKilled,
} from '../lib/combat';
import type { Unit, Weapon } from '../lib/types';
import { t, unitName, weaponName } from './i18n';
import { pageSignal } from './reinit';

interface BuffEffect {
  accuracy?: number;
  damage?: number;
  ap?: number;
  armor?: number;
  evasion?: number;
}
interface Buff {
  id: number;
  name: string;
  effects: BuffEffect;
}

interface MomEffect {
  stat: string;
  perMomentum: number | null;
  unit: string;
  affectsCalc: boolean;
}
interface MomFaction {
  passive: string;
  statusEffectId: number | null;
  effects: MomEffect[];
  note?: string;
  noCalcEffect?: boolean;
  tooltipDiscrepancy?: boolean;
  special?: string;
  conditional?: { name: string; note: string };
}
const factionMomentum = factionMomentumData as {
  factions: Record<string, MomFaction>;
};
const factionNames = factionsData as { id: number; name: string }[];

const buffs = buffsData as { attacker: Buff[]; target: Buff[] };
const atkBuffById = new Map(buffs.attacker.map((b) => [String(b.id), b]));
const tgtBuffById = new Map(buffs.target.map((b) => [String(b.id), b]));

// Mephrit Necrons (faction 4) is a hidden duplicate of Necrons.
const allUnits = (unitsData as Unit[]).filter((u) => u.faction !== 4);
const usedWeaponIds = new Set<number>();
for (const u of allUnits) {
  for (const slot of u.weaponSlots) {
    for (const opt of slot.options) usedWeaponIds.add(opt.weaponId);
  }
}
const weapons = (weaponsData as Weapon[]).filter((w) => usedWeaponIds.has(w.id));

const CRIT_DAMAGE_MULT = 1.5;
const GRAZE_DAMAGE_MULT = 0.25;

type FormulaModelId = 'floor-first' | 'post-armor-swing' | 'graze-null';

interface FormulaModelResult {
  id: FormulaModelId;
  label: string;
  note: string;
  steps: string[];
  expected: number;
}

function $(id: string): HTMLInputElement {
  return document.getElementById(id) as HTMLInputElement;
}

/** Dropdown label: in-game damage range and shot count. */
function weaponLabel(w: Weapon): string {
  const dr = damageRange(w.damage);
  const shots = Math.max(1, w.numAttacks);
  return `${dr.min}\u2013${dr.max} dmg${shots > 1 ? ` \u00d7${shots}` : ''}`;
}

export function initCalculator(): void {
  const weaponSel = document.getElementById('weapon') as HTMLSelectElement;
  const unitSel = document.getElementById('unit') as HTMLSelectElement;
  const attackerUnitSel = document.getElementById('attacker-unit') as HTMLSelectElement;
  if (!weaponSel || !unitSel || !attackerUnitSel) return;

  const weaponById = new Map(weapons.map((w) => [w.id, w]));
  function loadoutWeaponIds(u: Unit): number[] {
    const ids: number[] = [];
    for (const slot of u.weaponSlots) {
      for (const opt of slot.options) {
        if (!ids.includes(opt.weaponId) && weaponById.has(opt.weaponId)) ids.push(opt.weaponId);
      }
    }
    return ids;
  }

  const damage = $('damage');
  const accuracy = $('accuracy');
  const ap = $('ap');
  const accmod = $('accmod');
  const shots = $('shots');
  const armor = $('armor');
  const evasion = $('evasion');
  const hpmodel = $('hpmodel');
  const members = $('members');
  const dmgmod = $('dmgmod');
  const curhp = $('curhp');
  const lost = $('lost');
  const coverSel = document.getElementById('cover') as HTMLInputElement | null;
  const atkBuffSel = document.getElementById('atk-buff') as HTMLSelectElement | null;
  const tgtBuffSel = document.getElementById('tgt-buff') as HTMLSelectElement | null;
  const distance = $('distance');
  const rangeInfo = document.getElementById('range-info');
  const formulaModelSel = document.getElementById('formula-model') as HTMLSelectElement | null;
  const showCampaignUnits = document.getElementById(
    'show-campaign-units-calculator',
  ) as HTMLInputElement | null;
  const formulaModelNote = document.getElementById('formula-model-note');
  const formulaSteps = document.getElementById('formula-steps');
  const formulaCopyReport = document.getElementById('formula-copy-report');
  const momFactionName = document.getElementById('mom-faction-name');
  const momentumInput = $('momentum');
  const momPassive = document.getElementById('mom-passive');
  const momEffects = document.getElementById('mom-effects');
  const momNotes = document.getElementById('mom-notes');
  const atkBuffList = document.getElementById('atk-buff-list');
  const tgtBuffList = document.getElementById('tgt-buff-list');
  const params = new URLSearchParams(location.search);
  if (showCampaignUnits) {
    showCampaignUnits.checked = params.get('campaign') === '1';
    const attFromUrl = allUnits.find((u) => u.id === Number(params.get('attacker')));
    const tgtFromUrl = allUnits.find((u) => u.id === Number(params.get('unit')));
    if ((attFromUrl?.campaignOnly || tgtFromUrl?.campaignOnly) && !showCampaignUnits.checked) {
      showCampaignUnits.checked = true;
    }
  }

  function listedUnits(): Unit[] {
    return showCampaignUnits?.checked ? allUnits : allUnits.filter((u) => !u.campaignOnly);
  }
  // Stacking buffs/debuffs: multiple can be active on each side.
  const atkBuffIds: string[] = [];
  const tgtBuffIds: string[] = [];

  function describeBuff(e: BuffEffect): string {
    const parts: string[] = [];
    if (e.accuracy) parts.push(`${e.accuracy > 0 ? '+' : ''}${e.accuracy} acc`);
    if (e.damage) parts.push(`${e.damage > 0 ? '+' : ''}${e.damage} dmg`);
    if (e.ap) parts.push(`${e.ap > 0 ? '+' : ''}${e.ap} AP`);
    if (e.armor) parts.push(`${e.armor > 0 ? '+' : ''}${e.armor} armor`);
    if (e.evasion) parts.push(`${e.evasion > 0 ? '+' : ''}${e.evasion} eva`);
    return parts.join(', ');
  }

  const BUFF_KEYS: (keyof BuffEffect)[] = ['accuracy', 'damage', 'ap', 'armor', 'evasion'];

  /** Combined effect of every active buff/debuff on one side. */
  function sumBuffs(ids: string[], map: Map<string, Buff>): BuffEffect {
    const e: BuffEffect = {};
    for (const id of ids) {
      const b = map.get(id);
      if (!b) continue;
      for (const k of BUFF_KEYS) {
        const v = b.effects[k];
        if (v) e[k] = (e[k] ?? 0) + v;
      }
    }
    return e;
  }

  function renderBuffChips(ids: string[], map: Map<string, Buff>, el: HTMLElement | null): void {
    if (!el) return;
    el.innerHTML = ids
      .map((id) => {
        const b = map.get(id);
        if (!b) return '';
        return `<span class="chip">${b.name} (${describeBuff(b.effects)}) <button type="button" class="ml-0.5 text-[var(--color-blood)] font-bold" data-remove-buff="${id}" aria-label="remove">×</button></span>`;
      })
      .join('');
  }

  function addBuff(
    ids: string[],
    id: string,
    map: Map<string, Buff>,
    el: HTMLElement | null,
  ): void {
    if (!id || ids.includes(id)) return;
    ids.push(id);
    renderBuffChips(ids, map, el);
  }

  function removeBuff(
    ids: string[],
    id: string,
    map: Map<string, Buff>,
    el: HTMLElement | null,
  ): void {
    const i = ids.indexOf(id);
    if (i >= 0) ids.splice(i, 1);
    renderBuffChips(ids, map, el);
  }

  function populateBuffs(): void {
    const add = `<option value="">${t('calculator.buff.add')}</option>`;
    const sorted = (list: Buff[]) => [...list].sort((a, b) => a.name.localeCompare(b.name));
    if (atkBuffSel) {
      atkBuffSel.innerHTML =
        add +
        sorted(buffs.attacker)
          .map((b) => `<option value="${b.id}">${b.name} (${describeBuff(b.effects)})</option>`)
          .join('');
      atkBuffSel.value = '';
      renderBuffChips(atkBuffIds, atkBuffById, atkBuffList);
    }
    if (tgtBuffSel) {
      tgtBuffSel.innerHTML =
        add +
        sorted(buffs.target)
          .map((b) => `<option value="${b.id}">${b.name} (${describeBuff(b.effects)})</option>`)
          .join('');
      tgtBuffSel.value = '';
      renderBuffChips(tgtBuffIds, tgtBuffById, tgtBuffList);
    }
  }

  function populateMomFactions(): void {
    // Faction is derived from the attacker unit; nothing to populate.
  }

  // The momentum passive is taken from the attacker unit's faction. Units never
  // belong to more than one faction, so the faction is unambiguous.
  function attackerFactionId(): string {
    const u = allUnits.find((x) => x.id === Number(attackerUnitSel.value));
    if (!u) return '';
    const fid = String(u.faction);
    return factionMomentum.factions[fid] ? fid : '';
  }

  // Per-momentum effects that map to the damage maths (the rest are info only).
  function momentumMods(isRanged: boolean): { accAdd: number; apAdd: number; dmgFactor: number } {
    let accAdd = 0;
    let apAdd = 0;
    let dmgMul = 0;
    const fid = attackerFactionId();
    const mom = Math.max(0, Number(momentumInput.value) || 0);
    const f = fid ? factionMomentum.factions[fid] : undefined;
    if (f && mom > 0) {
      for (const e of f.effects) {
        if (!e.affectsCalc || e.perMomentum == null) continue;
        if (e.stat === 'accuracy') accAdd += e.perMomentum * mom;
        else if (e.stat === 'armorPiercing') apAdd += e.perMomentum * mom;
        else if (e.stat === 'damageMul') dmgMul += e.perMomentum * mom;
        else if (e.stat === 'rangedDamageMul' && isRanged) dmgMul += e.perMomentum * mom;
      }
    }
    return { accAdd, apAdd, dmgFactor: 1 + dmgMul };
  }

  function fmt(n: number): string {
    return Number(n.toFixed(2)).toString();
  }

  function pickFormulaModel(): FormulaModelId {
    const v = formulaModelSel?.value as FormulaModelId | undefined;
    if (v === 'floor-first' || v === 'post-armor-swing' || v === 'graze-null') return v;
    return 'floor-first';
  }

  function resolveSpecialBuckets(
    critPercent: number,
    grazePercent: number,
  ): { crit: number; graze: number; normal: number } {
    const c = Math.max(0, Math.min(1, critPercent / 100));
    const g = Math.max(0, Math.min(1, grazePercent / 100));
    if (c + g <= 1) return { crit: c, graze: g, normal: 1 - c - g };
    const sum = c + g;
    const scale = sum > 0 ? 1 / sum : 0;
    const crit = c * scale;
    const graze = g * scale;
    return { crit, graze, normal: 0 };
  }

  function reconstructionExpected(
    model: FormulaModelId,
    dr: { min: number; max: number },
    shots: number,
    hit: number,
    crit: number,
    graze: number,
  ): FormulaModelResult {
    const hitFactor = Math.max(0, Math.min(1, hit / 100));
    const buckets = resolveSpecialBuckets(crit, graze);
    const baseAvg = (dr.min + dr.max) / 2;
    const critAvg = (Math.round(dr.min + 1) + Math.round(dr.max * CRIT_DAMAGE_MULT)) / 2;
    const grazeAvg = (dr.min * GRAZE_DAMAGE_MULT + dr.max * GRAZE_DAMAGE_MULT) / 2;

    if (model === 'floor-first') {
      const onHit = Math.floor(
        baseAvg * buckets.normal +
          baseAvg * CRIT_DAMAGE_MULT * buckets.crit +
          baseAvg * GRAZE_DAMAGE_MULT * buckets.graze,
      );
      const perAttack = Math.floor(onHit * shots);
      const expected = Math.floor(perAttack * hitFactor);
      return {
        id: model,
        label: 'A · Floor-first chain',
        note: 'Applies crit=1.5x and graze=0.25x on a floored base average, with floor rounding at each major stage.',
        steps: [
          'Take max damage as base, derive min as 75% of max (floor).',
          'Apply attacker-side stacking mods first; then flat bonuses.',
          'Apply armor shaping to get post-armor range.',
          'Apply crit/graze weighted multiplier (crit 1.5x, graze 0.25x).',
          'Apply hit chance to get final expected damage.',
        ],
        expected,
      };
    }

    if (model === 'post-armor-swing') {
      const onHit = baseAvg * buckets.normal + critAvg * buckets.crit + grazeAvg * buckets.graze;
      const perAttack = Math.round(onHit * shots);
      const expected = Math.round(perAttack * hitFactor);
      return {
        id: model,
        label: 'B · Post-armor swing',
        note: 'Treats crit/graze as separate post-armor outcome bands, then blends by their probabilities.',
        steps: [
          'Compute post-armor normal damage range.',
          'Compute crit band: min+1, max×1.5.',
          'Compute graze band: range×0.25.',
          'Blend normal/crit/graze bands by chance weights.',
          'Apply hit chance at the end.',
        ],
        expected,
      };
    }

    const onHitNoGraze = baseAvg * (1 - buckets.crit) + critAvg * buckets.crit;
    const expected = Math.round(onHitNoGraze * shots * hitFactor * (1 - buckets.graze));
    return {
      id: model,
      label: 'C · Graze-null branch',
      note: 'Assumes many grazes collapse to 0 final damage; crit bonus is still 1.5x when non-graze hits crit.',
      steps: [
        'Build post-armor base range (normal hit).',
        'Apply crit uplift only on non-graze branch (1.5x max, +1 min).',
        'Treat graze as a null branch (0 damage) at probability level.',
        'Apply hit chance and graze-null branch factor.',
      ],
      expected,
    };
  }

  let lastFormulaResult: FormulaModelResult | null = null;

  function renderMomentum(): void {
    const mom = Math.max(0, Number(momentumInput.value) || 0);
    const barFill = document.getElementById('mom-bar-fill');
    const barLabel = document.getElementById('mom-bar-label');
    if (barFill) barFill.style.width = `${Math.min(100, mom)}%`;
    if (barLabel) barLabel.textContent = `${mom}/100`;
    if (!momPassive || !momEffects || !momNotes) return;
    const fid = attackerFactionId();
    const f = fid ? factionMomentum.factions[fid] : undefined;
    if (momFactionName) {
      momFactionName.textContent = fid
        ? (factionNames.find((x) => x.id === Number(fid))?.name ?? '—')
        : t('calculator.momentum.selectUnit');
    }
    if (!f) {
      momPassive.textContent = '';
      momEffects.innerHTML = '';
      momNotes.textContent = '';
      return;
    }
    momPassive.textContent = `${t('calculator.momentum.passive')}: ${f.passive}`;
    momEffects.innerHTML = f.effects
      .map((e) => {
        const label = t(`calculator.momentum.stat.${e.stat}`);
        const badge = e.affectsCalc
          ? `<span class="text-[var(--color-toxin)]">(${t('calculator.momentum.applied')})</span>`
          : `<span class="text-[var(--color-faint)]">(${t('calculator.momentum.info')})</span>`;
        const tip =
          e.stat === 'rangeStability'
            ? ` title="${t('calculator.momentum.rangeStabilityTip')}"`
            : '';
        if (e.perMomentum == null) {
          return `<li${tip}><span class="underline decoration-dotted">${label}</span> — ${f.special === 'favouredOfChaos' ? 'threshold' : 'special'} ${badge}</li>`;
        }
        const per = e.unit === 'percentMul' ? e.perMomentum * 100 : e.perMomentum;
        const total = per * mom;
        const sign = per >= 0 ? '+' : '';
        const suffix = e.unit === 'percent' || e.unit === 'percentMul' ? '%' : '';
        const atTxt = t('calculator.momentum.at').replace('{n}', String(mom));
        return `<li${tip}><span class="underline decoration-dotted">${label}</span>: ${sign}${fmt(per)}${suffix} / mom = <strong>${sign}${fmt(total)}${suffix}</strong> ${atTxt} ${badge}</li>`;
      })
      .join('');
    const notes: string[] = [];
    if (f.note) notes.push(f.note);
    if (f.tooltipDiscrepancy) notes.push(t('calculator.momentum.tauDiscrepancy'));
    if (f.conditional) notes.push(`${f.conditional.name}: ${f.conditional.note}`);
    momNotes.innerHTML = notes.map((n) => `<span class="block">• ${n}</span>`).join('');
  }

  function updateRangeInfo(): void {
    if (!rangeInfo) return;
    const w = weaponById.get(Number(weaponSel.value));
    if (!w || !w.isRanged || w.isMelee || !w.rangeMax) {
      rangeInfo.textContent = '';
      return;
    }
    const parts = [
      `${t('calculator.range.optimal')} ${w.rangeOptimal}, ${t('calculator.range.max')} ${w.rangeMax} ${t('calculator.range.tiles')}`,
    ];
    if (w.accuracyFalloff) parts.push(`${t('weaponDetail.range.accFalloff')} ${w.accuracyFalloff}`);
    const d = distance.value === '' ? null : Number(distance.value);
    if (d !== null && d > w.rangeMax) parts.push(t('calculator.range.outOfRange'));
    else if (d !== null && d > w.rangeOptimal)
      parts.push(`${d - w.rangeOptimal} ${t('calculator.range.beyondOptimal')}`);
    rangeInfo.textContent = parts.join(' · ');
  }

  function unitOptionsHtml(): string {
    return [...listedUnits()]
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
      .map((u) => `<option value="${u.id}">${unitName(u.id, u.name)}</option>`)
      .join('');
  }

  // Weapon list is the selected attacker unit's loadout; with no unit chosen
  // ('Custom values') it falls back to the full weapon list.
  function populateWeapons(): void {
    const u = allUnits.find((x) => x.id === Number(attackerUnitSel.value));
    const current = weaponSel.value;
    if (u) {
      weaponSel.innerHTML = loadoutWeaponIds(u)
        .map((id) => {
          const w = weaponById.get(id);
          return w
            ? `<option value="${id}">${weaponName(w.id, w.name)} (${weaponLabel(w)})</option>`
            : '';
        })
        .join('');
    } else {
      weaponSel.innerHTML = `<option value="">${t('common.customValues')}</option>${[...weapons]
        .sort((a, b) => weaponName(a.id, a.name).localeCompare(weaponName(b.id, b.name)))
        .map(
          (w) => `<option value="${w.id}">${weaponName(w.id, w.name)} (${weaponLabel(w)})</option>`,
        )
        .join('')}`;
    }
    if (current && weaponSel.querySelector(`option[value="${current}"]`)) {
      weaponSel.value = current;
    }
  }

  function renderOptions(): void {
    const currentA = attackerUnitSel.value;
    const currentU = unitSel.value;
    attackerUnitSel.innerHTML = `<option value="">${t('common.customValues')}</option>${unitOptionsHtml()}`;
    unitSel.innerHTML = `<option value="">${t('common.customValues')}</option>${unitOptionsHtml()}`;
    if (currentA) attackerUnitSel.value = currentA;
    if (currentU) unitSel.value = currentU;
    populateWeapons();
  }

  renderOptions();
  populateBuffs();
  populateMomFactions();

  function applyWeapon(id: number): void {
    const w = weapons.find((x) => x.id === id);
    if (!w) return;
    damage.value = String(w.damage);
    // Total shots = the weapon's Attacks x every model in the attacking squad.
    const au = allUnits.find((x) => x.id === Number(attackerUnitSel.value));
    // Melee weapons carry no own accuracy (they hit with the wielder's
    // MeleeAccuracy). Use the weapon's accuracy when it has one, otherwise fall
    // back to the attacker's melee accuracy so the hit chance is never 0%.
    const meleeAcc = au && au.meleeAccuracy > 0 ? au.meleeAccuracy : 85;
    accuracy.value = String(w.isMelee && w.accuracy <= 0 ? meleeAcc : w.accuracy);
    ap.value = String(w.armorPiercing);
    const models = au ? Math.max(1, au.members) : 1;
    shots.value = String(Math.max(1, w.numAttacks) * models);
  }

  function applyUnit(id: number): void {
    const u = allUnits.find((x) => x.id === id);
    if (!u) return;
    armor.value = String(u.armorProfile === 1 ? u.armorFront : u.armor);
    evasion.value = String(u.evasion);
    hpmodel.value = String(u.maxHealth);
    members.value = String(u.members);
    curhp.value = '';
    lost.value = '0';
  }

  function compute(): void {
    const dmg = Number(damage.value) || 0;
    const acc = Number(accuracy.value) || 0;
    const pierce = Number(ap.value) || 0;
    const mod = Number(accmod.value) || 0;
    const shotCount = Math.max(1, Number(shots.value) || 1);
    const dmgModifier = Number(dmgmod.value) || 0;
    const arm = Number(armor.value) || 0;
    const eva = Number(evasion.value) || 0;
    const hp = Math.max(1, Number(hpmodel.value) || 1);
    const mem = Math.max(1, Number(members.value) || 1);
    const lostModels = Math.min(mem, Math.max(0, Number(lost.value) || 0));
    const aliveModels = Math.max(0, mem - lostModels);
    const frontHp = curhp.value === '' ? hp : Math.max(0, Math.min(hp, Number(curhp.value) || 0));

    const effDamage = Math.max(0, dmg + dmgModifier);
    // Cover level 0..4 (none, 1/4, 1/2, 3/4, full). Cover reduces the attacker's
    // accuracy; full cover (4) blocks the attack entirely.
    const cover = Number(coverSel?.value) || 0;
    const coverAccPenalty = [0, 15, 30, 45, 0][cover] ?? 0;
    const blocked = cover >= 4;
    const ab = sumBuffs(atkBuffIds, atkBuffById);
    const tb = sumBuffs(tgtBuffIds, tgtBuffById);
    const selWeapon = weaponById.get(Number(weaponSel.value));
    const isRangedW = !!selWeapon && selWeapon.isRanged && !selWeapon.isMelee;
    const mm = momentumMods(isRangedW);
    const finalDamage = Math.max(0, (effDamage + (ab?.damage ?? 0)) * mm.dmgFactor);
    const finalAp = pierce + (ab?.ap ?? 0) + mm.apAdd;
    const finalArmor = Math.max(0, arm + (tb?.armor ?? 0));
    const finalEva = eva + (tb?.evasion ?? 0);
    const finalAcc = acc + (ab?.accuracy ?? 0) + mm.accAdd - coverAccPenalty;
    const perHit = damagePerHitAfterArmor(finalDamage, finalArmor, finalAp);
    const dr = damageRangeAfterArmor(finalDamage, finalArmor, finalAp);
    const hit = blocked ? 0 : hitChance(finalAcc, mod, finalEva);
    const graze = grazeChance(finalAp, finalArmor);
    const crit = critChance(0, finalAp, finalArmor);
    const perAttackAvg = perHit * shotCount;
    // Expected one-round damage = average post-armor damage × hit chance × non-graze share.
    const expected = Math.round(expectedDamage(perAttackAvg, hit) * (1 - graze / 100));
    const formulaResult = reconstructionExpected(
      pickFormulaModel(),
      dr,
      shotCount,
      hit,
      crit,
      graze,
    );
    lastFormulaResult = formulaResult;
    const killed = Math.min(modelsKilled(perAttackAvg, hp), aliveModels);
    const totalHp = hp * mem;
    // HP left in the unit after this attack: pre-existing damage (lost models +
    // a wounded front model) minus the expected damage this attack deals.
    const currentHp = Math.max(0, aliveModels * hp - (hp - frontHp));
    const remainingHp = Math.max(0, currentHp - expected);

    setText('r-perhit', `${dr.min}\u2013${dr.max}`);
    setText('r-hit', blocked ? t('calculator.cover.blocked') : `${Math.round(hit)}%`);
    setText('r-crit', `${Math.round(crit)}%`);
    setText('r-graze', `${Math.round(graze)}%`);
    setText('r-attack', `${dr.min * shotCount}\u2013${dr.max * shotCount}`);
    setText('r-expected', String(expected));
    const formulaLabel = (formulaResult.label ?? '').split('·')[0]?.trim() ?? '';
    setText(
      'r-expected-model',
      `${formulaResult.expected}${formulaLabel ? ` (${formulaLabel})` : ''}`,
    );
    setText('r-killed', `${killed} / ${aliveModels}`);
    setText('r-totalhp', String(totalHp));
    setText('r-remaining', String(remainingHp));
    if (formulaModelNote) formulaModelNote.textContent = formulaResult.note;
    if (formulaSteps) {
      formulaSteps.innerHTML = formulaResult.steps.map((s) => `<li>${s}</li>`).join('');
    }
    updateRangeInfo();
    renderMomentum();
    syncUrl();
  }

  function setText(id: string, value: string): void {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (attackerUnitSel.value) p.set('attacker', attackerUnitSel.value);
    if (weaponSel.value) p.set('weapon', weaponSel.value);
    if (unitSel.value) p.set('unit', unitSel.value);
    if (showCampaignUnits?.checked) p.set('campaign', '1');
    const qs = p.toString();
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
    const copy = document.getElementById('copy-link');
    copy?.setAttribute('data-url', `${location.pathname}${qs ? `?${qs}` : ''}`);
  }

  attackerUnitSel.addEventListener('change', () => {
    populateWeapons();
    if (weaponSel.value) applyWeapon(Number(weaponSel.value));
    compute();
  });
  weaponSel.addEventListener('change', () => {
    if (weaponSel.value) applyWeapon(Number(weaponSel.value));
    compute();
  });
  unitSel.addEventListener('change', () => {
    if (unitSel.value) applyUnit(Number(unitSel.value));
    compute();
  });
  for (const el of [
    damage,
    accuracy,
    ap,
    accmod,
    shots,
    dmgmod,
    armor,
    evasion,
    hpmodel,
    members,
    curhp,
    lost,
    distance,
  ]) {
    el.addEventListener('input', () => {
      // Manual edits detach from the preset selection.
      compute();
    });
  }
  coverSel?.addEventListener('change', compute);
  // Cover is chosen via a segmented-shield button group backed by the hidden
  // #cover input.
  const coverGroup = document.getElementById('cover-group');
  const coverButtons = coverGroup?.querySelectorAll<HTMLButtonElement>('.cover-btn');
  if (coverButtons) {
    for (const btn of coverButtons) {
      btn.addEventListener('click', () => {
        if (coverSel) coverSel.value = btn.getAttribute('data-cover') ?? '0';
        for (const b of coverButtons) {
          b.setAttribute('aria-checked', b === btn ? 'true' : 'false');
        }
        compute();
      });
    }
  }
  atkBuffSel?.addEventListener('change', () => {
    addBuff(atkBuffIds, atkBuffSel.value, atkBuffById, atkBuffList);
    atkBuffSel.value = '';
    compute();
  });
  tgtBuffSel?.addEventListener('change', () => {
    addBuff(tgtBuffIds, tgtBuffSel.value, tgtBuffById, tgtBuffList);
    tgtBuffSel.value = '';
    compute();
  });
  atkBuffList?.addEventListener('click', (e) => {
    const id = (e.target as HTMLElement)
      .closest('[data-remove-buff]')
      ?.getAttribute('data-remove-buff');
    if (id) {
      removeBuff(atkBuffIds, id, atkBuffById, atkBuffList);
      compute();
    }
  });
  tgtBuffList?.addEventListener('click', (e) => {
    const id = (e.target as HTMLElement)
      .closest('[data-remove-buff]')
      ?.getAttribute('data-remove-buff');
    if (id) {
      removeBuff(tgtBuffIds, id, tgtBuffById, tgtBuffList);
      compute();
    }
  });
  momentumInput.addEventListener('input', compute);
  showCampaignUnits?.addEventListener('change', () => {
    const oldA = attackerUnitSel.value;
    const oldU = unitSel.value;
    renderOptions();
    if (oldA && attackerUnitSel.querySelector(`option[value="${oldA}"]`)) {
      attackerUnitSel.value = oldA;
    }
    if (oldU && unitSel.querySelector(`option[value="${oldU}"]`)) {
      unitSel.value = oldU;
      applyUnit(Number(oldU));
    }
    populateWeapons();
    compute();
  });
  formulaModelSel?.addEventListener('change', compute);
  formulaCopyReport?.addEventListener('click', async () => {
    const model = lastFormulaResult;
    if (!model) return;
    const lines = [
      `Model: ${model.label}`,
      `Expected damage (reconstruction): ${model.expected}`,
      `Crit multiplier: ${CRIT_DAMAGE_MULT}x`,
      `Graze multiplier: ${GRAZE_DAMAGE_MULT}x`,
      `Inputs -> dmg:${damage.value || '0'}, acc:${accuracy.value || '0'}, ap:${ap.value || '0'}, shots:${shots.value || '1'}, armor:${armor.value || '0'}, evasion:${evasion.value || '0'}`,
      'Order assumptions:',
      ...model.steps.map((s, i) => `${i + 1}. ${s}`),
    ];
    const payload = lines.join('\n');
    try {
      await navigator.clipboard.writeText(payload);
      showToast('Reconstruction report copied');
    } catch {
      showToast(payload);
    }
  });

  document.getElementById('copy-link')?.addEventListener('click', async () => {
    const url = `${location.origin}${location.pathname}${location.search}`;
    try {
      await navigator.clipboard.writeText(url);
      showToast(t('toast.linkCopied'));
    } catch {
      showToast(url);
    }
  });

  function showToast(message: string): void {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('hidden');
    window.setTimeout(() => el.classList.add('hidden'), 1600);
  }

  // Hydrate from URL
  const wParam = params.get('weapon');
  const uParam = params.get('unit');
  const aParam = params.get('attacker');
  if (aParam && allUnits.some((u) => u.id === Number(aParam))) {
    attackerUnitSel.value = aParam;
  } else if (!wParam && attackerUnitSel.options.length > 1) {
    // Default the attacker to the first unit's loadout.
    attackerUnitSel.selectedIndex = 1;
  }
  populateWeapons();
  if (wParam && weaponSel.querySelector(`option[value="${wParam}"]`) === null) {
    // A deep-linked weapon that isn't in the chosen loadout: use the full list.
    attackerUnitSel.value = '';
    populateWeapons();
  }
  if (wParam) {
    weaponSel.value = wParam;
    applyWeapon(Number(wParam));
  } else if (weaponSel.value) {
    applyWeapon(Number(weaponSel.value));
  }
  if (uParam) {
    unitSel.value = uParam;
    applyUnit(Number(uParam));
  }
  compute();

  // Mode toggle: one-round attack test (default) vs battle simulation.
  const oneRoundBtn = document.getElementById('mode-oneround-btn');
  const battleBtn = document.getElementById('mode-battle-btn');
  const oneRoundPane = document.getElementById('mode-oneround');
  const battlePane = document.getElementById('mode-battle');
  const MODE_ACTIVE = ['bg-[var(--color-gold)]', '!text-[var(--color-void)]', 'shadow'];
  function setMode(battle: boolean): void {
    oneRoundPane?.classList.toggle('hidden', battle);
    battlePane?.classList.toggle('hidden', !battle);
    for (const c of MODE_ACTIVE) {
      oneRoundBtn?.classList.toggle(c, !battle);
      battleBtn?.classList.toggle(c, battle);
    }
    oneRoundBtn?.classList.toggle('text-[var(--color-muted)]', battle);
    battleBtn?.classList.toggle('text-[var(--color-muted)]', !battle);
    oneRoundBtn?.setAttribute('aria-selected', battle ? 'false' : 'true');
    battleBtn?.setAttribute('aria-selected', battle ? 'true' : 'false');
  }
  oneRoundBtn?.addEventListener('click', () => setMode(false));
  battleBtn?.addEventListener('click', () => setMode(true));
  setMode(false);

  window.addEventListener(
    'bs:locale-changed',
    () => {
      renderOptions();
      populateBuffs();
      populateMomFactions();
      compute();
    },
    { signal: pageSignal('calculator') },
  );
}
