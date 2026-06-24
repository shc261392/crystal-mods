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
  damagePerHit,
  damageRange,
  expectedDamage,
  grazeChance,
  hitChance,
  modelsKilled,
} from '../lib/combat';
import type { Unit, Weapon } from '../lib/types';
import { t, unitName, weaponName } from './i18n';

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
  baseCritNote: string;
  factions: Record<string, MomFaction>;
};
const factionNames = factionsData as { id: number; name: string }[];

const buffs = buffsData as { attacker: Buff[]; target: Buff[] };
const atkBuffById = new Map(buffs.attacker.map((b) => [String(b.id), b]));
const tgtBuffById = new Map(buffs.target.map((b) => [String(b.id), b]));

const weapons = weaponsData as Weapon[];
// Mephrit Necrons (faction 4) is a hidden duplicate of Necrons.
const units = (unitsData as Unit[]).filter((u) => u.faction !== 4);

function $(id: string): HTMLInputElement {
  return document.getElementById(id) as HTMLInputElement;
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
  const coverSel = document.getElementById('cover') as HTMLSelectElement | null;
  const atkBuffSel = document.getElementById('atk-buff') as HTMLSelectElement | null;
  const tgtBuffSel = document.getElementById('tgt-buff') as HTMLSelectElement | null;
  const distance = $('distance');
  const rangeInfo = document.getElementById('range-info');
  const momFactionName = document.getElementById('mom-faction-name');
  const momentumInput = $('momentum');
  const momPassive = document.getElementById('mom-passive');
  const momEffects = document.getElementById('mom-effects');
  const momNotes = document.getElementById('mom-notes');

  function describeBuff(e: BuffEffect): string {
    const parts: string[] = [];
    if (e.accuracy) parts.push(`${e.accuracy > 0 ? '+' : ''}${e.accuracy} acc`);
    if (e.damage) parts.push(`${e.damage > 0 ? '+' : ''}${e.damage} dmg`);
    if (e.ap) parts.push(`${e.ap > 0 ? '+' : ''}${e.ap} AP`);
    if (e.armor) parts.push(`${e.armor > 0 ? '+' : ''}${e.armor} armor`);
    if (e.evasion) parts.push(`${e.evasion > 0 ? '+' : ''}${e.evasion} eva`);
    return parts.join(', ');
  }

  function populateBuffs(): void {
    const none = `<option value="">${t('calculator.buff.none')}</option>`;
    if (atkBuffSel) {
      const cur = atkBuffSel.value;
      atkBuffSel.innerHTML =
        none +
        buffs.attacker
          .map((b) => `<option value="${b.id}">${b.name} (${describeBuff(b.effects)})</option>`)
          .join('');
      atkBuffSel.value = cur;
    }
    if (tgtBuffSel) {
      const cur = tgtBuffSel.value;
      tgtBuffSel.innerHTML =
        none +
        buffs.target
          .map((b) => `<option value="${b.id}">${b.name} (${describeBuff(b.effects)})</option>`)
          .join('');
      tgtBuffSel.value = cur;
    }
  }

  function populateMomFactions(): void {
    // Faction is derived from the attacker unit; nothing to populate.
  }

  // The momentum passive is taken from the attacker unit's faction. Units never
  // belong to more than one faction, so the faction is unambiguous.
  function attackerFactionId(): string {
    const u = units.find((x) => x.id === Number(attackerUnitSel.value));
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
    notes.push(factionMomentum.baseCritNote);
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
    return [...units]
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
      .map((u) => `<option value="${u.id}">${unitName(u.id, u.name)}</option>`)
      .join('');
  }

  // Weapon list is the selected attacker unit's loadout; with no unit chosen
  // ('Custom values') it falls back to the full weapon list.
  function populateWeapons(): void {
    const u = units.find((x) => x.id === Number(attackerUnitSel.value));
    const current = weaponSel.value;
    if (u) {
      weaponSel.innerHTML = loadoutWeaponIds(u)
        .map((id) => {
          const w = weaponById.get(id);
          return w
            ? `<option value="${id}">${weaponName(w.id, w.name)} (${w.damage} dmg)</option>`
            : '';
        })
        .join('');
    } else {
      weaponSel.innerHTML = `<option value="">${t('common.customValues')}</option>${[...weapons]
        .sort((a, b) => weaponName(a.id, a.name).localeCompare(weaponName(b.id, b.name)))
        .map(
          (w) => `<option value="${w.id}">${weaponName(w.id, w.name)} (${w.damage} dmg)</option>`,
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
    accuracy.value = String(w.accuracy);
    ap.value = String(w.armorPiercing);
    shots.value = String(
      Math.max(1, w.numAttacks) * Math.max(1, w.shotsPerAttack) * Math.max(1, w.burstSize),
    );
  }

  function applyUnit(id: number): void {
    const u = units.find((x) => x.id === id);
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
    const cover = Number(coverSel?.value) || 0;
    const ab = atkBuffSel ? atkBuffById.get(atkBuffSel.value)?.effects : undefined;
    const tb = tgtBuffSel ? tgtBuffById.get(tgtBuffSel.value)?.effects : undefined;
    const selWeapon = weaponById.get(Number(weaponSel.value));
    const isRangedW = !!selWeapon && selWeapon.isRanged && !selWeapon.isMelee;
    const mm = momentumMods(isRangedW);
    const finalDamage = Math.max(0, (effDamage + (ab?.damage ?? 0)) * mm.dmgFactor);
    const finalAp = pierce + (ab?.ap ?? 0) + mm.apAdd;
    const finalArmor = Math.max(0, arm + cover + (tb?.armor ?? 0));
    const finalEva = eva + (tb?.evasion ?? 0);
    const finalAcc = acc + (ab?.accuracy ?? 0) + mm.accAdd;
    const perHit = damagePerHit(finalDamage);
    const dr = damageRange(finalDamage);
    const hit = hitChance(finalAcc, mod, finalEva);
    const graze = grazeChance(finalAp, finalArmor);
    const crit = critChance(0, finalAp, finalArmor);
    const perAttack = perHit * shotCount;
    const expected = expectedDamage(perAttack, hit);
    const killed = Math.min(modelsKilled(perAttack, hp), aliveModels);
    const totalHp = hp * mem;
    // Remaining HP accounts for already-lost models and a wounded front model.
    const remainingHp = Math.max(0, aliveModels * hp - (hp - frontHp));

    setText('r-perhit', `${dr.min}\u2013${dr.max}`);
    setText('r-hit', `${Math.round(hit)}%`);
    setText('r-crit', `${Math.round(crit)}%`);
    setText('r-graze', `${Math.round(graze)}%`);
    setText('r-attack', `${dr.min * shotCount}\u2013${dr.max * shotCount}`);
    setText('r-expected', String(expected));
    setText('r-killed', `${killed} / ${aliveModels}`);
    setText('r-totalhp', String(totalHp));
    setText('r-remaining', String(remainingHp));
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
  atkBuffSel?.addEventListener('change', compute);
  tgtBuffSel?.addEventListener('change', compute);
  momentumInput.addEventListener('input', compute);

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
  const params = new URLSearchParams(location.search);
  const wParam = params.get('weapon');
  const uParam = params.get('unit');
  const aParam = params.get('attacker');
  if (aParam && units.some((u) => u.id === Number(aParam))) {
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

  window.addEventListener('bs:locale-changed', () => {
    renderOptions();
    populateBuffs();
    populateMomFactions();
    compute();
  });
}
