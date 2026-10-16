# Translation decisions

Judgement calls that were made deliberately, so they are not re-raised by every
future audit.

---

## `讎特` for "chort" — **KEEP**

The Slavic household spirit *chort* (Russian чорт) is rendered `讎特` throughout.
An audit flagged this twice: `讎` means "feud / enmity", so the word is not
etymologically right, and both `楚特` and `喬特` were proposed as alternatives.

**Decision: keep `讎特`.** Do not raise it again.

Affects ~112 config strings across 90 files, ~665 dialogue fields and ~31 UI
labels. Changing it is a ~700-occurrence sweep that is not wanted.

---

## Mainland colloquial register — **KEEP the tone**

The game's own Simplified Chinese uses an earthy, rustic register: `俺`, `啥`,
`孬`, and `兒化` forms (`事兒`, `這兒`, `玩意兒`). A polish pass normalised these
to neutral Taiwan Mandarin, which is what Taiwanese readers would normally
expect.

**Decision: keep the warm, colloquial voice.** These are an intentional part of
how the game sounds and were reverted. A Taiwan localisation does not have to
flatten the register.

Affected ~140 proposed changes; all reverted.

---

## `咋` → `怎麼` — **CHANGE**

The single exception. `咋` is not current in Taiwan Mandarin at all, so it is
normalised. Implemented as a rule in `reference/terms.tsv` rather than a config
override, because the bulk of the occurrences are in the runtime dialogue text
(~371 fields in `data.unity3d` object 71459) that config overrides cannot reach.

---

## Terminology that IS normalised

`reference/terms.tsv`, applied to every converted string:

| Mainland | Taiwan | Note |
|---|---|---|
| 質量 | 品質 | |
| 反饋 | 回饋 | |
| 公交車 | 公車 | |
| 咋 | 怎麼 | see above |

Anything OpenCC's `s2twp` dictionary already handles never reaches this list —
it only carries terms that survive the conversion.
