// Army builder: localStorage-backed list with live totals, faction breakdown
// and URL sharing. Single-faction only: pick a faction, then add its units with
// a chosen weapon loadout (which affects the point cost).

import unitsData from '../data/units.json';
import type { Unit } from '../lib/types';
import {
  type ArmyEntry,
  decodeArmy,
  encodeArmy,
  getArmy,
  saveArmy,
  totalModels,
  totalPoints,
} from './army-store';
import { factionName, t, tf, unitName, weaponName } from './i18n';

const units = (unitsData as Unit[]).filter((u) => u.faction !== 4);
const unitById = new Map(units.map((u) => [u.id, u]));

// Factions that actually have units, for the faction picker.
const factions = [...new Map(units.map((u) => [u.faction, u.factionName])).entries()]
  .map(([id, name]) => ({ id, name }))
  .sort((a, b) => factionName(a.id, a.name).localeCompare(factionName(b.id, b.name)));

function unitSlug(u: Unit): string {
  const s = u.name
    .toLowerCase()
    .replace(/['’]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${u.id}-${s}`;
}

/** The default loadout: the zero-cost option in each weapon slot. */
function defaultLoadout(u: Unit): number[] {
  return u.weaponSlots.map((slot) => {
    const free = slot.options.find((o) => (o.pointCost ?? 0) === 0) ?? slot.options[0];
    return free?.weaponId ?? -1;
  });
}

/** Total points for a unit with a given loadout = base + selected upgrade costs. */
function loadoutCost(u: Unit, loadout: number[]): number {
  let pts = u.pointCost;
  u.weaponSlots.forEach((slot, i) => {
    const opt = slot.options.find((o) => o.weaponId === loadout[i]);
    if (opt) pts += opt.pointCost ?? 0;
  });
  return pts;
}

export function initArmyBuilder(): void {
  const factionSel = document.getElementById('army-faction') as HTMLSelectElement | null;
  const select = document.getElementById('add-unit') as HTMLSelectElement | null;
  const loadoutBox = document.getElementById('loadout-config');
  const addBtn = document.getElementById('add-btn');
  const list = document.getElementById('army-list');
  const empty = document.getElementById('empty');
  if (!factionSel || !select || !list) return;
  const listEl = list;
  const facSel = factionSel;
  const unitSel = select;

  let army: ArmyEntry[] = getArmy();

  // A shared list in the URL takes precedence.
  const shared = new URLSearchParams(location.search).get('ids');
  if (shared) {
    army = decodeArmy(shared)
      .map(([id, qty, loadout]): ArmyEntry | null => {
        const u = unitById.get(id);
        if (!u) return null;
        const lo = loadout.length ? loadout : defaultLoadout(u);
        return {
          id: u.id,
          name: u.name,
          points: loadoutCost(u, lo),
          faction: u.factionName,
          qty,
          loadout: lo,
        };
      })
      .filter((e): e is ArmyEntry => e !== null);
    saveArmy(army);
    history.replaceState(null, '', location.pathname);
  }

  // Single-faction: the army's faction is fixed once it has units.
  function armyFaction(): number | null {
    const first = army[0] ? unitById.get(army[0].id) : undefined;
    return first ? first.faction : null;
  }

  function populateFactions(): void {
    const locked = armyFaction();
    const cur = facSel.value;
    facSel.innerHTML = factions
      .map((f) => `<option value="${f.id}">${factionName(f.id, f.name)}</option>`)
      .join('');
    facSel.value = locked !== null ? String(locked) : cur || String(factions[0]?.id ?? '');
    facSel.disabled = locked !== null;
  }

  function populateUnits(): void {
    const fid = Number(facSel.value);
    const inFaction = units
      .filter((u) => u.faction === fid)
      .sort((a, b) => unitName(a.id, a.name).localeCompare(unitName(b.id, b.name)));
    unitSel.innerHTML = inFaction
      .map(
        (u) =>
          `<option value="${u.id}">${unitName(u.id, u.name)} — ${u.pointCost} ${t('common.pointsShort')}</option>`,
      )
      .join('');
    renderLoadoutConfig();
  }

  function renderLoadoutConfig(): void {
    if (!loadoutBox) return;
    const u = unitById.get(Number(unitSel.value));
    if (!u) {
      loadoutBox.innerHTML = '';
      return;
    }
    const def = defaultLoadout(u);
    const slots = u.weaponSlots
      .map((slot, i) => {
        if (slot.options.length <= 1) return '';
        const opts = slot.options
          .map(
            (o) =>
              `<option value="${o.weaponId}">${weaponName(o.weaponId, o.name)}${o.pointCost ? ` (+${o.pointCost})` : ''}</option>`,
          )
          .join('');
        return `<div><span class="label block mb-1">${t('unitDetail.slotPrefix')} ${i + 1}</span><select data-slot="${i}" class="select text-sm">${opts}</select></div>`;
      })
      .join('');
    loadoutBox.innerHTML = slots ? `<p class="label">${t('army.loadout')}</p>${slots}` : '';
    for (const sel of loadoutBox.querySelectorAll<HTMLSelectElement>('select[data-slot]')) {
      const i = Number(sel.getAttribute('data-slot'));
      sel.value = String(def[i]);
    }
  }

  function currentLoadout(u: Unit): number[] {
    const def = defaultLoadout(u);
    if (!loadoutBox) return def;
    for (const sel of loadoutBox.querySelectorAll<HTMLSelectElement>('select[data-slot]')) {
      const i = Number(sel.getAttribute('data-slot'));
      def[i] = Number(sel.value);
    }
    return def;
  }

  function loadoutSummary(u: Unit, loadout: number[]): string {
    return u.weaponSlots
      .map((slot, i) => {
        const opt = slot.options.find((o) => o.weaponId === loadout[i]);
        return opt ? weaponName(opt.weaponId, opt.name) : '';
      })
      .filter(Boolean)
      .join(', ');
  }

  function persist(): void {
    saveArmy(army);
  }

  function render(): void {
    if (empty) empty.style.display = army.length ? 'none' : '';
    listEl.innerHTML = army
      .map((e) => {
        const u = unitById.get(e.id);
        const href = u ? `/units/${unitSlug(u)}` : '#';
        const displayName = u ? unitName(u.id, u.name) : unitName(e.id, e.name);
        const lo = u && e.loadout ? loadoutSummary(u, e.loadout) : '';
        return `<li class="flex items-center gap-3 rounded-lg bg-[var(--color-base)] border border-[var(--color-border)] px-3 py-2.5" data-id="${e.id}">
          <span class="flex-1 min-w-0">
            <a href="${href}" class="font-semibold text-sm truncate block hover:text-[var(--color-gold)]">${displayName}</a>
            <span class="text-xs text-[var(--color-faint)]">${lo ? `${lo} · ` : ''}${tf('army.item.pointsEach', { points: e.points })}</span>
          </span>
          <span class="flex items-center gap-1.5 shrink-0">
            <button type="button" data-act="dec" class="btn btn-ghost !px-2 !py-1 text-base leading-none" aria-label="${t('common.decrease')}">−</button>
            <span class="w-7 text-center font-bold tabular-nums">${e.qty}</span>
            <button type="button" data-act="inc" class="btn btn-ghost !px-2 !py-1 text-base leading-none" aria-label="${t('common.increase')}">+</button>
          </span>
          <span class="w-16 text-right font-bold text-[var(--color-gold-dim)] tabular-nums shrink-0">${e.points * e.qty}</span>
          <button type="button" data-act="del" class="text-[var(--color-faint)] hover:text-[var(--color-blood)] shrink-0" aria-label="${t('common.remove')}">✕</button>
        </li>`;
      })
      .join('');

    setText('sum-points', String(totalPoints(army)));
    setText('sum-units', String(army.length));
    setText('sum-models', String(totalModels(army)));
    renderFactions();
    populateFactions();
    if (!facSel.disabled) populateUnits();
  }

  function renderFactions(): void {
    const box = document.getElementById('faction-breakdown');
    if (!box) return;
    const first = army[0];
    if (!first) {
      box.innerHTML = `<p class="text-sm text-[var(--color-faint)]">${t('army.factions.none')}</p>`;
      return;
    }
    const u0 = unitById.get(first.id);
    const label = u0 ? factionName(u0.faction, u0.factionName) : first.faction;
    box.innerHTML = `<p class="label mb-1">${t('common.byFaction')}</p><div class="flex justify-between text-sm"><span class="text-[var(--color-muted)] truncate">${label}</span><span class="font-semibold tabular-nums">${totalPoints(army)}</span></div>`;
  }

  function setText(id: string, value: string): void {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function add(): void {
    const u = unitById.get(Number(unitSel.value));
    if (!u) return;
    const loadout = currentLoadout(u);
    const existing = army.find(
      (e) => e.id === u.id && (e.loadout ?? []).join('-') === loadout.join('-'),
    );
    if (existing) existing.qty += 1;
    else
      army.push({
        id: u.id,
        name: u.name,
        points: loadoutCost(u, loadout),
        faction: u.factionName,
        qty: 1,
        loadout,
      });
    persist();
    render();
  }

  facSel.addEventListener('change', populateUnits);
  unitSel.addEventListener('change', renderLoadoutConfig);
  addBtn?.addEventListener('click', add);

  list.addEventListener('click', (ev) => {
    const btn = (ev.target as HTMLElement).closest('button[data-act]');
    if (!btn) return;
    const li = btn.closest('li');
    const id = Number(li?.getAttribute('data-id'));
    const entry = army.find((e) => e.id === id);
    if (!entry) return;
    const act = btn.getAttribute('data-act');
    if (act === 'inc') entry.qty += 1;
    else if (act === 'dec') entry.qty = Math.max(1, entry.qty - 1);
    else if (act === 'del') army = army.filter((e) => e !== entry);
    persist();
    render();
  });

  document.getElementById('share-btn')?.addEventListener('click', async () => {
    if (army.length === 0) {
      toast(t('toast.addUnitsFirst'));
      return;
    }
    const url = `${location.origin}/army-builder?ids=${encodeArmy(army)}`;
    try {
      await navigator.clipboard.writeText(url);
      toast(t('toast.shareLinkCopied'));
    } catch {
      toast(url);
    }
  });

  document.getElementById('clear-btn')?.addEventListener('click', () => {
    army = [];
    persist();
    render();
  });

  window.addEventListener('bs:locale-changed', render);

  function toast(message: string): void {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('hidden');
    window.setTimeout(() => el.classList.add('hidden'), 1600);
  }

  populateFactions();
  populateUnits();
  render();
}
