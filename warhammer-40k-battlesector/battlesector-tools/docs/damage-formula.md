# Damage & armour formula

Reference for the combat maths used across Battlesector Tools (weapon detail
tables, the damage calculator, and the "damage vs Armor 3/6/9" sort). All logic
lives in [`src/lib/combat.ts`](../src/lib/combat.ts); this document is the
human-readable specification and source of truth.

> Rounding matters. Read the [Rounding conventions](#rounding-conventions) table
> — some steps floor, one rounds normally.

## 1. Base damage range

A weapon's `damage` stat is its **maximum** damage. The minimum is 75% of it,
floored:

$$
d_{\max} = \text{weapon.damage}, \qquad
d_{\min} = \left\lfloor 0.75 \times d_{\max} \right\rfloor
$$

Example: `damage = 20` → range **15–20** (`floor(0.75 × 20) = 15`).

Constants: `MIN_DAMAGE_MULT = 0.75`.

## 2. Armour reduction (multiplicative)

Armour is reduced by the weapon's armour piercing first; the result cannot be
negative:

$$
a_{\text{eff}} = \max(0,\; \text{armour} - \text{AP})
$$

Each point of effective armour removes **10% of the weapon's max damage**. The
reduced max is **floored**, then the min is 75% of that reduced max, **floored**:

$$
d_{\max}' = \left\lfloor d_{\max} \times \frac{10 - a_{\text{eff}}}{10} \right\rfloor,
\qquad
d_{\min}' = \left\lfloor 0.75 \times d_{\max}' \right\rfloor
$$

We compute `floor(d_max × (10 − a_eff) / 10)` with integer arithmetic (not
`1 − a_eff/10`) to avoid floating-point error — e.g. `1 − 9/10 = 0.0999…`, which
would wrongly floor `20 × 0.0999… = 1` instead of `2`.

At `a_eff = 0` this reduces to the base range `[floor(0.75 × max), max]`.

Implemented by `effectiveArmor()` and `damageRangeAfterArmor()`.

### Worked example — Baal Predator

Assault cannon: base **3–4** damage (`d_max = 4`), **AP 4**.

| Target armour | `a_eff` | `d_max' = floor(4 × (10−a_eff)/10)` | Range |
| ---: | ---: | ---: | :--- |
| 0–4 | 0 | `floor(4 × 1.0) = 4` | **3–4** |
| 5 | 1 | `floor(4 × 0.9) = 3` | **2–3** |
| 6 | 2 | `floor(4 × 0.8) = 3` | **2–3** |
| 7 | 3 | `floor(4 × 0.7) = 2` | **1–2** |
| 8 | 4 | `floor(4 × 0.6) = 2` | **1–2** |
| 9 | 5 | `floor(4 × 0.5) = 2` | **1–2** |
| 10 | 6 | `floor(4 × 0.4) = 1` | **0–1** |

Matches the in-game values: 5–6 armour → 2–3, 7–9 armour → 1–2, 10 armour → 0–1.

## 3. Critical hits

**Chance** — base weapon crit (0 unless specified) plus 5% for every point of AP
**above** the target's armour:

$$
P_{\text{crit}} = \text{baseCrit} + 5\% \times \max(0,\; \text{AP} - \text{armour})
$$

**Damage** — the crit band derives from the **post-armour max** `d_max'`. The min
is `+1`; the max uses **normal rounding** (not floor) of `1.5 ×`:

$$
\text{crit}_{\min} = d_{\max}' + 1, \qquad
\text{crit}_{\max} = \operatorname{round}(1.5 \times d_{\max}')
$$

The band is clamped so `crit_max ≥ crit_min` (prevents inversion when `d_max'` is
tiny, e.g. `d_max' = 1 → round(1.5) = 2 = min`).

| `d_max'` | crit band |
| ---: | :--- |
| 6 | 7–9 |
| 5 | 6–8 (`round(7.5) = 8`) |
| 4 | 5–6 |
| 3 | 4–5 (`round(4.5) = 5`) |
| 2 | 3–3 |
| 1 | 2–2 |
| 0 | 1–1 (clamped) |

Constants: `CRIT_FACTOR = 5`, `CRIT_DAMAGE_MULT = 1.5`. Implemented by
`critChance()` and `critDamageRange()`.

## 4. Grazes

**Chance** — 3% for every point of target armour **above** the weapon's AP:

$$
P_{\text{graze}} = 3\% \times \max(0,\; \text{armour} - \text{AP})
$$

**Damage** — 25% of the normal average damage.

Constants: `GRAZE_FACTOR = 3`, `GRAZE_DAMAGE_MULT = 0.25`. Implemented by
`grazeChance()`.

## 5. Expected damage per hit

The three outcome bands, weighted by their probabilities:

$$
\text{E}[d] = P_{\text{normal}} \cdot \overline{d} + P_{\text{crit}} \cdot \overline{\text{crit}} + P_{\text{graze}} \cdot 0.25\,\overline{d}
$$

where $\overline{d} = \tfrac{d_{\min}' + d_{\max}'}{2}$,
$\overline{\text{crit}} = \tfrac{\text{crit}_{\min} + \text{crit}_{\max}}{2}$, and
$P_{\text{normal}} = 1 - P_{\text{crit}} - P_{\text{graze}}$.

Implemented by `expectedDamagePerHit(range, critPercent, grazePercent)`.

## 6. Total damage throughput

A full attack fires `shots` projectiles:

$$
\text{shots} = n_{\text{attacks}} \times n_{\text{shots}} \times n_{\text{burst}}
$$

For melee weapons with no listed accuracy, accuracy defaults to **80%**.

$$
D_{\text{total}} = \text{shots} \times \frac{\text{accuracy}}{100} \times \text{E}[d]
$$

`totalDamageVsArmor(weapon, armour)` in
[`src/lib/weapon-display.ts`](../src/lib/weapon-display.ts) computes this; it
backs the **damage vs Armor 3 / 6 / 9** sort on the weapons page.

The weapon detail tables also surface the raw pre-probability figure as
`DMG: dmin'–dmax' (×shots)` so you can see the hit before crit/graze/accuracy are
applied.

## Rounding conventions

| Step | Operation | Rounding |
| :--- | :--- | :--- |
| Base min damage | `0.75 × max` | **floor** |
| Armour-reduced max | `max × (10 − a_eff) / 10` | **floor** |
| Armour-reduced min | `0.75 × reducedMax` | **floor** |
| Crit min | `reducedMax + 1` | exact (integer) |
| Crit max | `1.5 × reducedMax` | **round** (half up) |
| Graze damage | `0.25 × normalAvg` | none (probabilistic average) |
| Hit / crit / graze chance | clamped to 0–100% | — |

## Related

- Hit chance, models killed, momentum and cover: see
  [`game-mechanics.md`](game-mechanics.md).
- Tag/stat explanations surfaced in the UI: `src/lib/tag-tooltips.ts`.
