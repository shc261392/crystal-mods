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
import { applyI18n, factionName, roleName, t, tf, unitName, weaponName } from './i18n';

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
  const factionBar = document.getElementById('army-faction-bar');
  const unitGrid = document.getElementById('unit-grid');
  const unitSearch = document.getElementById('unit-search') as HTMLInputElement | null;
  const unitSort = document.getElementById('unit-sort') as HTMLSelectElement | null;
  const unitRole = document.getElementById('unit-role') as HTMLSelectElement | null;
  const showCampaignUnits = document.getElementById('show-campaign-units') as HTMLInputElement | null;
  const tagFilter = document.getElementById('army-unit-tag-filter');
  const loadoutBox = document.getElementById('loadout-config');
  const loadoutTotal = document.getElementById('loadout-total');
  const selectedUnitChip = document.getElementById('selected-unit-chip');
  const addBtn = document.getElementById('add-btn');
  const list = document.getElementById('army-list');
  const empty = document.getElementById('empty');
  if (!factionBar || !unitGrid || !list) return;
  const listEl = list;
  const gridEl = unitGrid;
  const barEl = factionBar;
  let selectedFactionId: number | null = null;
  let selectedUnitId: number | null = null;
  const selectedLoadouts = new Map<number, number[]>();
  const PILL_ACTIVE = [
    '!border-[var(--color-gold)]',
    '!text-[var(--color-gold)]',
    'bg-[color-mix(in_oklab,var(--color-gold)_12%,transparent)]',
  ];
  const selectedTags = new Set<string>();

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
    if (locked !== null) selectedFactionId = locked;
    else if (selectedFactionId === null) selectedFactionId = factions[0]?.id ?? null;
    for (const b of barEl.querySelectorAll<HTMLButtonElement>('button[data-faction-id]')) {
      const id = Number(b.getAttribute('data-faction-id'));
      const isActive = id === selectedFactionId;
      for (const c of PILL_ACTIVE) b.classList.toggle(c, isActive);
      const disabled = locked !== null && id !== locked;
      b.disabled = disabled;
      b.classList.toggle('opacity-40', disabled);
      b.classList.toggle('cursor-not-allowed', disabled);
    }
  }

  function populateUnits(): void {
    const fid = selectedFactionId ?? -1;
    const query = unitSearch?.value.trim().toLowerCase() ?? '';
    const role = unitRole?.value ?? '';
    const campaignVisible = showCampaignUnits?.checked ?? false;
    const cards = [...gridEl.querySelectorAll<HTMLElement>('[data-unit-id][data-faction-id]')];
    const sortMode = unitSort?.value ?? 'tier-name';
    let firstVisibleUnit: number | null = null;
    for (const card of cards) {
      const cardFactionId = Number(card.getAttribute('data-faction-id'));
      const cardUnitId = Number(card.getAttribute('data-unit-id'));
      const cardName = card.getAttribute('data-unit-name') ?? '';
      const cardRole = card.getAttribute('data-role') ?? '';
      const cardTags = new Set(
        (card.getAttribute('data-tags') ?? '')
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      );
      const visible =
        cardFactionId === fid &&
        (!query || cardName.includes(query)) &&
        (!role || cardRole === role) &&
        (campaignVisible || !cardTags.has('campaign')) &&
        [...selectedTags].every((tag) => cardTags.has(tag));
      card.classList.toggle('hidden', !visible);
      if (visible && firstVisibleUnit === null) firstVisibleUnit = cardUnitId;
    }

    cards.sort((a, b) => {
      const aName = a.getAttribute('data-unit-name') ?? '';
      const bName = b.getAttribute('data-unit-name') ?? '';
      const aPoints = Number(a.getAttribute('data-unit-points'));
      const bPoints = Number(b.getAttribute('data-unit-points'));
      const aTier = Number(a.getAttribute('data-tier-rank') ?? 99);
      const bTier = Number(b.getAttribute('data-tier-rank') ?? 99);
      const aHp = Number(a.getAttribute('data-hp') ?? 0);
      const bHp = Number(b.getAttribute('data-hp') ?? 0);
      const aArmor = Number(a.getAttribute('data-armor') ?? 0);
      const bArmor = Number(b.getAttribute('data-armor') ?? 0);
      const aMove = Number(a.getAttribute('data-move') ?? 0);
      const bMove = Number(b.getAttribute('data-move') ?? 0);
      if (sortMode === 'points-desc') return bPoints - aPoints || aName.localeCompare(bName);
      if (sortMode === 'points-asc') return aPoints - bPoints || aName.localeCompare(bName);
      if (sortMode === 'name-desc') return bName.localeCompare(aName);
      if (sortMode === 'hp-desc') return bHp - aHp || aName.localeCompare(bName);
      if (sortMode === 'hp-asc') return aHp - bHp || aName.localeCompare(bName);
      if (sortMode === 'armor-desc') return bArmor - aArmor || aName.localeCompare(bName);
      if (sortMode === 'armor-asc') return aArmor - bArmor || aName.localeCompare(bName);
      if (sortMode === 'move-desc') return bMove - aMove || aName.localeCompare(bName);
      if (sortMode === 'move-asc') return aMove - bMove || aName.localeCompare(bName);
      if (sortMode === 'tier-name') return aTier - bTier || aName.localeCompare(bName);
      return aName.localeCompare(bName) || aPoints - bPoints;
    });
    for (const card of cards) gridEl.appendChild(card);

    const stillVisible = cards.some(
      (card) =>
        !card.classList.contains('hidden') &&
        Number(card.getAttribute('data-unit-id')) === selectedUnitId,
    );
    if (!stillVisible) selectedUnitId = firstVisibleUnit;
    renderSelectedUnitCards();
    renderLoadoutConfig();
  }

  function renderSelectedUnitCards(): void {
    for (const card of gridEl.querySelectorAll<HTMLElement>('[data-unit-id]')) {
      const id = Number(card.getAttribute('data-unit-id'));
      const selected = id === selectedUnitId;
      card.classList.toggle('!border-[var(--color-gold)]', selected);
      card.classList.toggle('bg-[color-mix(in_oklab,var(--color-gold)_10%,transparent)]', selected);
      card.setAttribute('aria-pressed', selected ? 'true' : 'false');
    }
    const u = selectedUnitId !== null ? unitById.get(selectedUnitId) : undefined;
    if (!selectedUnitChip) return;
    if (!u) {
      selectedUnitChip.classList.add('hidden');
      selectedUnitChip.textContent = '';
      return;
    }
    const pts = loadoutCost(u, currentLoadout(u));
    selectedUnitChip.classList.remove('hidden');
    selectedUnitChip.textContent = `${t('common.unit')}: ${unitName(u.id, u.name)} · ${pts} ${t('common.pointsShort')}`;
  }

  function paintTagButtons(): void {
    if (!tagFilter) return;
    for (const b of tagFilter.querySelectorAll<HTMLButtonElement>('button[data-tag]')) {
      const tag = b.getAttribute('data-tag') ?? '';
      const on = selectedTags.has(tag);
      b.classList.toggle('!text-[var(--color-gold)]', on);
      b.classList.toggle('!border-[var(--color-gold-dim)]', on);
      b.classList.toggle('bg-[color-mix(in_oklab,var(--color-gold)_14%,transparent)]', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
  }

  function localizeRoleOptions(): void {
    if (!unitRole) return;
    for (const opt of Array.from(unitRole.options)) {
      const id = Number(opt.getAttribute('data-role-id'));
      if (!Number.isFinite(id)) continue;
      opt.textContent = roleName(id, opt.value);
    }
  }

  function renderLoadoutConfig(): void {
    if (!loadoutBox) return;
    const u = selectedUnitId !== null ? unitById.get(selectedUnitId) : undefined;
    if (!u) {
      loadoutBox.innerHTML = '';
      if (loadoutTotal) loadoutTotal.textContent = '';
      return;
    }
    const def = [...(selectedLoadouts.get(u.id) ?? defaultLoadout(u))];
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
      sel.addEventListener('change', updateLoadoutTotal);
    }
    selectedLoadouts.set(u.id, def);
    updateLoadoutTotal();
  }

  function updateLoadoutTotal(): void {
    if (!loadoutTotal) return;
    const u = selectedUnitId !== null ? unitById.get(selectedUnitId) : undefined;
    if (!u) {
      loadoutTotal.textContent = '';
      return;
    }
    const pts = loadoutCost(u, currentLoadout(u));
    const delta = pts - u.pointCost;
    loadoutTotal.textContent =
      delta > 0
        ? `${pts} ${t('common.pointsShort')} (base ${u.pointCost} +${delta})`
        : `${pts} ${t('common.pointsShort')}`;
  }

  function currentLoadout(u: Unit): number[] {
    const def = [...(selectedLoadouts.get(u.id) ?? defaultLoadout(u))];
    if (!loadoutBox) return def;
    for (const sel of loadoutBox.querySelectorAll<HTMLSelectElement>('select[data-slot]')) {
      const i = Number(sel.getAttribute('data-slot'));
      def[i] = Number(sel.value);
    }
    selectedLoadouts.set(u.id, def);
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

  function entryKey(e: ArmyEntry): string {
    return `${e.id}:${(e.loadout ?? []).join('-')}`;
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
        return `<li class="flex items-center gap-3 rounded-lg bg-[var(--color-base)] border border-[var(--color-border)] px-3 py-2.5" data-key="${entryKey(e)}">
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
    populateUnits();
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
    const u = selectedUnitId !== null ? unitById.get(selectedUnitId) : undefined;
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

  barEl.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest(
      'button[data-faction-id]',
    ) as HTMLButtonElement | null;
    if (!btn || btn.disabled) return;
    selectedFactionId = Number(btn.getAttribute('data-faction-id'));
    populateFactions();
    populateUnits();
  });
  gridEl.addEventListener('click', (e) => {
    const card = (e.target as HTMLElement).closest('[data-unit-id]') as HTMLElement | null;
    if (!card || card.classList.contains('hidden')) return;
    selectedUnitId = Number(card.getAttribute('data-unit-id'));
    renderSelectedUnitCards();
    renderLoadoutConfig();
  });
  gridEl.addEventListener('keydown', (e) => {
    const ke = e as KeyboardEvent;
    if (ke.key !== 'Enter' && ke.key !== ' ') return;
    const card = (e.target as HTMLElement).closest('[data-unit-id]') as HTMLElement | null;
    if (!card || card.classList.contains('hidden')) return;
    ke.preventDefault();
    selectedUnitId = Number(card.getAttribute('data-unit-id'));
    renderSelectedUnitCards();
    renderLoadoutConfig();
  });
  unitSearch?.addEventListener('input', populateUnits);
  unitSort?.addEventListener('change', populateUnits);
  unitRole?.addEventListener('change', populateUnits);
  showCampaignUnits?.addEventListener('change', populateUnits);
  tagFilter?.addEventListener('click', (event) => {
    const btn = (event.target as HTMLElement).closest(
      'button[data-tag]',
    ) as HTMLButtonElement | null;
    if (!btn) return;
    const tag = btn.getAttribute('data-tag');
    if (!tag) return;
    if (selectedTags.has(tag)) selectedTags.delete(tag);
    else selectedTags.add(tag);
    paintTagButtons();
    populateUnits();
  });
  addBtn?.addEventListener('click', add);

  list.addEventListener('click', (ev) => {
    const btn = (ev.target as HTMLElement).closest('button[data-act]');
    if (!btn) return;
    const li = btn.closest('li');
    const key = li?.getAttribute('data-key');
    const entry = army.find((e) => entryKey(e) === key);
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

  window.addEventListener('bs:locale-changed', () => {
    applyI18n();
    localizeRoleOptions();
    render();
    paintTagButtons();
  });

  function toast(message: string): void {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('hidden');
    window.setTimeout(() => el.classList.add('hidden'), 1600);
  }

  applyI18n();
  localizeRoleOptions();
  paintTagButtons();
  populateFactions();
  populateUnits();
  render();
}
