// Damage calculator: wires the form to the shared combat formulas. Weapon and
// unit datasets are imported (bundled by Vite) so selecting one auto-fills the
// inputs. State is reflected in the URL for sharing.

import unitsData from '../data/units.json';
import weaponsData from '../data/weapons.json';
import { damagePerHit, expectedDamage, hitChance, modelsKilled } from '../lib/combat';
import type { Unit, Weapon } from '../lib/types';
import { t, unitName, weaponName } from './i18n';

const weapons = weaponsData as Weapon[];
const units = unitsData as Unit[];

function $(id: string): HTMLInputElement {
  return document.getElementById(id) as HTMLInputElement;
}

export function initCalculator(): void {
  const weaponSel = document.getElementById('weapon') as HTMLSelectElement;
  const unitSel = document.getElementById('unit') as HTMLSelectElement;
  if (!weaponSel || !unitSel) return;

  const damage = $('damage');
  const accuracy = $('accuracy');
  const ap = $('ap');
  const accmod = $('accmod');
  const shots = $('shots');
  const armor = $('armor');
  const evasion = $('evasion');
  const hpmodel = $('hpmodel');
  const members = $('members');

  function renderOptions(): void {
    const currentW = weaponSel.value;
    const currentU = unitSel.value;
    weaponSel.innerHTML = `<option value="">${t('common.customValues')}</option>${[...weapons]
      .sort((a, b) => weaponName(a.id, a.name).localeCompare(weaponName(b.id, b.name)))
      .map((w) => `<option value="${w.id}">${weaponName(w.id, w.name)} (${w.damage} dmg)</option>`)
      .join('')}`;
    unitSel.innerHTML = `<option value="">${t('common.customValues')}</option>${[...units]
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)))
      .map((u) => `<option value="${u.id}">${unitName(u.id, u.name)}</option>`)
      .join('')}`;
    if (currentW) weaponSel.value = currentW;
    if (currentU) unitSel.value = currentU;
  }

  renderOptions();

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
  }

  function compute(): void {
    const dmg = Number(damage.value) || 0;
    const acc = Number(accuracy.value) || 0;
    const pierce = Number(ap.value) || 0;
    const mod = Number(accmod.value) || 0;
    const shotCount = Math.max(1, Number(shots.value) || 1);
    const arm = Number(armor.value) || 0;
    const eva = Number(evasion.value) || 0;
    const hp = Math.max(1, Number(hpmodel.value) || 1);
    const mem = Math.max(1, Number(members.value) || 1);

    const perHit = damagePerHit(dmg, arm, pierce);
    const hit = hitChance(acc, mod, eva);
    const perAttack = perHit * shotCount;
    const expected = expectedDamage(perAttack, hit);
    const killed = modelsKilled(perAttack, hp);
    const totalHp = hp * mem;

    setText('r-perhit', String(perHit));
    setText('r-hit', `${Math.round(hit)}%`);
    setText('r-attack', String(perAttack));
    setText('r-expected', String(expected));
    setText('r-killed', `${Math.min(killed, mem)} / ${mem}`);
    setText('r-totalhp', String(totalHp));
    syncUrl();
  }

  function setText(id: string, value: string): void {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function syncUrl(): void {
    const p = new URLSearchParams();
    if (weaponSel.value) p.set('weapon', weaponSel.value);
    if (unitSel.value) p.set('unit', unitSel.value);
    const qs = p.toString();
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
    const copy = document.getElementById('copy-link');
    copy?.setAttribute('data-url', `${location.pathname}${qs ? `?${qs}` : ''}`);
  }

  weaponSel.addEventListener('change', () => {
    if (weaponSel.value) applyWeapon(Number(weaponSel.value));
    compute();
  });
  unitSel.addEventListener('change', () => {
    if (unitSel.value) applyUnit(Number(unitSel.value));
    compute();
  });
  for (const el of [damage, accuracy, ap, accmod, shots, armor, evasion, hpmodel, members]) {
    el.addEventListener('input', () => {
      // Manual edits detach from the preset selection.
      compute();
    });
  }

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
  if (wParam) {
    weaponSel.value = wParam;
    applyWeapon(Number(wParam));
  } else {
    applyWeapon(weapons[0]?.id ?? -1);
  }
  if (uParam) {
    unitSel.value = uParam;
    applyUnit(Number(uParam));
  }
  compute();

  window.addEventListener('bs:locale-changed', () => {
    renderOptions();
  });
}
