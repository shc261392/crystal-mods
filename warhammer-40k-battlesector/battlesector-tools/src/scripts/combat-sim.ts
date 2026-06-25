// Combat simulator: two squads of dots fight an auto-resolved, dice-rolled
// exchange using the shared combat formulas. Each model is a dot with an HP bar
// (red = health, blue = bonus/overshield HP); a dimmed dot is a casualty.

import unitsData from '../data/units.json';
import weaponsData from '../data/weapons.json';
import { damageRange, grazeChance, hitChance } from '../lib/combat';
import type { Unit, Weapon } from '../lib/types';
import { t, unitName, weaponName } from './i18n';

const units = (unitsData as Unit[]).filter((u) => u.faction !== 4);
const weapons = weaponsData as Weapon[];
const weaponById = new Map(weapons.map((w) => [w.id, w]));

const MAX_TURNS = 25;
const TICK_MS = 750;

interface Model {
  maxHp: number;
  hp: number;
  bonusMax: number;
  bonus: number;
}

interface Squad {
  label: string;
  unitName: string;
  weaponName: string;
  armor: number;
  evasion: number;
  weaponDamage: number;
  weaponAccuracy: number;
  armorPiercing: number;
  shots: number;
  models: Model[];
}

interface Side {
  unitSel: HTMLSelectElement;
  weaponSel: HTMLSelectElement;
  bonusInput: HTMLInputElement;
  field: HTMLElement;
  count: HTMLElement;
  squad: Squad | null;
}

function weaponShots(w: Weapon): number {
  return Math.max(1, w.numAttacks) * Math.max(1, w.shotsPerAttack) * Math.max(1, w.burstSize);
}

function unitArmor(u: Unit): number {
  return u.armorProfile === 1 ? u.armorFront : u.armor;
}

/** Weapon ids a unit can field, taken from its loadout slots (deduped). */
function loadoutWeaponIds(u: Unit): number[] {
  const ids: number[] = [];
  for (const slot of u.weaponSlots) {
    for (const opt of slot.options) {
      if (!ids.includes(opt.weaponId) && weaponById.has(opt.weaponId)) ids.push(opt.weaponId);
    }
  }
  return ids;
}

export function initCombatSim(): void {
  const playBtn = document.getElementById('sim-play') as HTMLButtonElement | null;
  const revertBtn = document.getElementById('sim-revert') as HTMLButtonElement | null;
  const playLabel = document.getElementById('sim-play-label');
  const turnEl = document.getElementById('sim-turn');
  const outcomeEl = document.getElementById('sim-outcome');
  const logEl = document.getElementById('sim-log');
  if (!playBtn || !revertBtn || !turnEl || !outcomeEl || !logEl) return;

  const sideARaw = makeSide('simA');
  const sideBRaw = makeSide('simB');
  if (!sideARaw || !sideBRaw) return;
  const sideA: Side = sideARaw;
  const sideB: Side = sideBRaw;

  let timer: number | null = null;
  let turn = 0;
  let running = false;

  function makeSide(prefix: string): Side | null {
    const unitSel = document.getElementById(`${prefix}-unit`) as HTMLSelectElement | null;
    const weaponSel = document.getElementById(`${prefix}-weapon`) as HTMLSelectElement | null;
    const bonusInput = document.getElementById(`${prefix}-bonus`) as HTMLInputElement | null;
    const field = document.getElementById(`${prefix}-field`);
    const count = document.getElementById(`${prefix}-count`);
    if (!unitSel || !weaponSel || !bonusInput || !field || !count) return null;
    return { unitSel, weaponSel, bonusInput, field, count, squad: null };
  }

  function populateUnits(side: Side): void {
    const current = side.unitSel.value;
    side.unitSel.innerHTML = [...units]
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
      .map((u) => `<option value="${u.id}">${unitName(u.id, u.name)}</option>`)
      .join('');
    if (current) side.unitSel.value = current;
  }

  function populateWeapons(side: Side): void {
    const u = units.find((x) => x.id === Number(side.unitSel.value));
    const ids = u ? loadoutWeaponIds(u) : [];
    const list = ids.length ? ids : weapons.slice(0, 1).map((w) => w.id);
    side.weaponSel.innerHTML = list
      .map((id) => {
        const w = weaponById.get(id);
        if (!w) return '';
        return `<option value="${id}">${weaponName(w.id, w.name)} (${w.damage} dmg)</option>`;
      })
      .join('');
  }

  function buildSquad(side: Side, label: string): Squad | null {
    const u = units.find((x) => x.id === Number(side.unitSel.value));
    const w = weaponById.get(Number(side.weaponSel.value));
    if (!u || !w) return null;
    const bonus = Math.max(0, Number(side.bonusInput.value) || 0);
    const models: Model[] = Array.from({ length: Math.max(1, u.members) }, () => ({
      maxHp: Math.max(1, u.maxHealth),
      hp: Math.max(1, u.maxHealth),
      bonusMax: bonus,
      bonus,
    }));
    return {
      label,
      unitName: unitName(u.id, u.name),
      weaponName: weaponName(w.id, w.name),
      armor: unitArmor(u),
      evasion: u.evasion,
      weaponDamage: w.damage,
      weaponAccuracy: w.accuracy,
      armorPiercing: w.armorPiercing,
      shots: weaponShots(w),
      models,
    };
  }

  function modelAlive(m: Model): boolean {
    return m.hp > 0 || m.bonus > 0;
  }

  function aliveCount(sq: Squad): number {
    return sq.models.filter(modelAlive).length;
  }

  function renderField(side: Side): void {
    const sq = side.squad;
    if (!sq) {
      side.field.innerHTML = '';
      side.count.textContent = '';
      return;
    }
    side.field.innerHTML = sq.models
      .map((m) => {
        const dead = !modelAlive(m);
        const hpPct = Math.max(0, Math.min(100, (m.hp / m.maxHp) * 100));
        const bonusPct = m.bonusMax > 0 ? Math.max(0, Math.min(100, (m.bonus / m.maxHp) * 100)) : 0;
        const title = dead
          ? `${sq.unitName} — ✕`
          : `${sq.unitName} — ${m.hp}/${m.maxHp} HP${m.bonus > 0 ? ` (+${m.bonus})` : ''}`;
        return `<div class="sim-dot${dead ? ' dead' : ''}" title="${title}"><div class="hp" style="height:${hpPct}%"></div><div class="bonus" style="height:${bonusPct}%"></div></div>`;
      })
      .join('');
    side.count.textContent = `${aliveCount(sq)} / ${sq.models.length}`;
  }

  /** Apply one successful hit's damage to the front living model (no overflow). */
  function applyHit(sq: Squad, dmg: number): boolean {
    const target = sq.models.find(modelAlive);
    if (!target) return false;
    let remaining = dmg;
    if (target.bonus > 0) {
      const absorbed = Math.min(target.bonus, remaining);
      target.bonus -= absorbed;
      remaining -= absorbed;
    }
    if (remaining > 0) target.hp = Math.max(0, target.hp - remaining);
    return !modelAlive(target);
  }

  /** One squad fires at the other using pre-turn living shooter count. */
  function fire(attacker: Squad, defender: Squad): { hits: number; kills: number } {
    const shooters = aliveCount(attacker);
    const chance = hitChance(attacker.weaponAccuracy, 0, defender.evasion);
    let hits = 0;
    let kills = 0;
    for (let s = 0; s < shooters; s++) {
      for (let shot = 0; shot < attacker.shots; shot++) {
        if (!defender.models.some(modelAlive)) break;
        if (Math.random() * 100 < chance) {
          hits++;
          // Damage is a range [0.75x, x]; a graze (3% per point of armour over
          // penetration) deals NO damage, otherwise roll uniformly in range.
          const { min, max } = damageRange(attacker.weaponDamage);
          const grazed = Math.random() * 100 < grazeChance(attacker.armorPiercing, defender.armor);
          const dmg = grazed ? 0 : Math.round(min + Math.random() * (max - min));
          if (dmg > 0 && applyHit(defender, dmg)) kills++;
        }
      }
    }
    return { hits, kills };
  }

  function log(msg: string): void {
    if (!logEl) return;
    const li = document.createElement('li');
    li.textContent = msg;
    logEl.prepend(li);
  }

  function setOutcome(): boolean {
    const a = sideA.squad;
    const b = sideB.squad;
    if (!a || !b || !outcomeEl) return false;
    const aAlive = aliveCount(a) > 0;
    const bAlive = aliveCount(b) > 0;
    if (aAlive && bAlive && turn < MAX_TURNS) return false;
    stop();
    if (!aAlive && !bAlive) {
      outcomeEl.textContent = t('combatSim.outcome.mutual');
      outcomeEl.style.color = 'var(--color-muted)';
    } else if (aAlive && !bAlive) {
      outcomeEl.textContent = `${a.label} ${t('combatSim.outcome.wins')}`;
      outcomeEl.style.color = 'var(--color-plasma)';
    } else if (bAlive && !aAlive) {
      outcomeEl.textContent = `${b.label} ${t('combatSim.outcome.wins')}`;
      outcomeEl.style.color = 'var(--color-blood)';
    } else {
      outcomeEl.textContent = t('combatSim.outcome.stalemate');
      outcomeEl.style.color = 'var(--color-muted)';
    }
    return true;
  }

  function step(): void {
    const a = sideA.squad;
    const b = sideB.squad;
    if (!a || !b) return;
    turn++;
    if (turnEl) turnEl.textContent = String(turn);
    // Simultaneous exchange: both fire using pre-turn living counts.
    const ra = fire(a, b);
    const rb = fire(b, a);
    renderField(sideA);
    renderField(sideB);
    log(
      `${t('combatSim.turn')} ${turn}: ${a.label} → ${ra.hits} ${t('combatSim.log.hits')}, ${ra.kills} ${t('combatSim.log.kills')} · ${b.label} → ${rb.hits} ${t('combatSim.log.hits')}, ${rb.kills} ${t('combatSim.log.kills')}`,
    );
    setOutcome();
  }

  function stop(): void {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
    running = false;
    if (playLabel) playLabel.textContent = t('combatSim.play');
  }

  function play(): void {
    if (running) {
      stop();
      return;
    }
    // If a finished fight is on screen, reset before replaying.
    if (turn >= MAX_TURNS || !sideA.squad || !sideB.squad || setOutcomeFinished()) {
      reset();
    }
    running = true;
    if (playLabel) playLabel.textContent = t('combatSim.pause');
    timer = window.setInterval(() => {
      step();
      if (!running) return;
    }, TICK_MS);
  }

  function setOutcomeFinished(): boolean {
    const a = sideA.squad;
    const b = sideB.squad;
    if (!a || !b) return true;
    return aliveCount(a) === 0 || aliveCount(b) === 0;
  }

  function reset(): void {
    stop();
    turn = 0;
    if (turnEl) turnEl.textContent = '0';
    if (outcomeEl) outcomeEl.textContent = '';
    if (logEl) logEl.innerHTML = '';
    sideA.squad = buildSquad(sideA, t('combatSim.squadA'));
    sideB.squad = buildSquad(sideB, t('combatSim.squadB'));
    renderField(sideA);
    renderField(sideB);
  }

  function onSelectionChange(side: Side): void {
    populateWeapons(side);
    reset();
  }

  // Wire events
  sideA.unitSel.addEventListener('change', () => onSelectionChange(sideA));
  sideB.unitSel.addEventListener('change', () => onSelectionChange(sideB));
  sideA.weaponSel.addEventListener('change', reset);
  sideB.weaponSel.addEventListener('change', reset);
  sideA.bonusInput.addEventListener('input', reset);
  sideB.bonusInput.addEventListener('input', reset);
  playBtn.addEventListener('click', play);
  revertBtn.addEventListener('click', reset);
  window.addEventListener('bs:locale-changed', () => {
    populateUnits(sideA);
    populateUnits(sideB);
    populateWeapons(sideA);
    populateWeapons(sideB);
    reset();
  });

  // Initial population: default to two different units for an interesting fight.
  populateUnits(sideA);
  populateUnits(sideB);
  if (sideA.unitSel.options.length > 1) sideA.unitSel.selectedIndex = 0;
  if (sideB.unitSel.options.length > 1) {
    sideB.unitSel.selectedIndex = Math.min(1, sideB.unitSel.options.length - 1);
  }
  populateWeapons(sideA);
  populateWeapons(sideB);
  reset();
}
