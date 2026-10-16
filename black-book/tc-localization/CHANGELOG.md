# Changelog — Black Book Traditional Chinese Localization

All notable changes to this mod. Versions follow the `modinfo.json` `version`
field and the `MOD_VERSION` in the `Makefile`; `make build` writes
`dist/tc-localization-v<version>.zip`.

The mod ships as a Vortex ZIP that contains the converted `config_zh.yaml`
files **and** the `BlackBookTcFont` BepInEx plugin. The plugin needs the
separate **BepInEx Framework** mod (BepInEx 5.4.23.5 x64) installed once.

## 1.3.0 — 2026-10-16

Full-translation polish pass, plus final register decisions recorded so they are
not re-litigated.

### Added

- `reference/DECISIONS.md` — the standing decisions for future audits:
  - `讎特` (chort) is **kept** (~112 config strings, ~665 dialogue fields,
    ~31 UI labels).
  - The Mainland colloquial register is **kept**: `俺` (29), `啥` (39), `孬` (3)
    and `兒化` forms are intentional.
- `reference/terms.tsv` now also carries `咋`, `質量`, `反饋`, `公交車`.

### Changed

- **204 reviewed polish corrections** applied on top of the conversion;
  `reference/overrides.tsv` held 245 unique overrides at the polish pass and
  105 after the register revert below.
- Real mistranslations inherited from the game's own EN → SC pass fixed, e.g.
  `Status/Waste` `悴败` → `衰敗`, `Abilities/FIRE` `开火！` → `烈焰！`,
  `Abilities/RIZI` `不朽权杖` → `不朽祭披`, `Units/CheranLeg*` `切兰的腿` →
  `切蘭的爪`, `Inventory/BirdUrok` `鉴戒之鸟` → `衰敗之鳥`.
- `咋` → `怎麼` (the single register exception, because `咋` is not current in
  Taiwan Mandarin). Implemented in `reference/terms.tsv`, not as config
  overrides, because most occurrences are in runtime dialogue text
  (object `71459`) that config overrides cannot reach.
- The 140 register proposals from the polish pass were reverted (`overrides`
  245 → 105); `俺`/`啥`/`孬` counts are unchanged and `咋` is 11 → 0.

### Fixed

- The overrides gate caught five polish proposals as regressions (duplicated
  keys where the earlier value was better); `overrides.tsv` is now
  deduplicated, keeping the first occurrence.
- `review/triples.jsonl` was stale (its `tc` column predated the overrides) and
  has been regenerated from the live payload.

## 1.2.1 — 2026-10-16

Translation-audit fixes, and the audit material moved into the repo.

### Added

- `reference/terms.tsv` — Taiwan term rules (`質量` → `品質`, `反饋` → `回饋`,
  `公交車` → `公車`) merged into the conversion stage so the build-time payload
  and the runtime converter stay identical.
- `review/TRANSLATION_REVIEW.tsv` — 30 editable rows
  (`file / key / english / current / suggested / issue`).
- `review/AUDIT_TC_TRANSLATION.md`, `review/triples.jsonl` (all 3,479 EN/SC/TC
  triples), `review/DIALOGUE_71459_REVIEW.json`,
  `review/TEXTTABLE_71461_REVIEW.json`, and the audit scripts.

### Fixed

- 10 name corruptions caused by OpenCC itself: `s2twp`'s single-character rule
  `里` → `裡` also fired inside transliterated Slavic names (`葉戈裡`, `基裡安`,
  `蘇佩裡克`, `聖葉戈裡日`). Fixed via `reference/overrides.tsv`; the 7
  surviving `裡` in Name fields are genuine Taiwan usage and were left alone.
- The English column in `review/TRANSLATION_REVIEW.tsv` was built from the
  wrong file (it re-read the Chinese `config_zh.yaml`), so it duplicated
  `current`; it now maps to the sibling `config_en.yaml`.
- 30 accepted review corrections applied to `reference/overrides.tsv`, e.g.
  `Units/Satan1`/`Satan2` `死神` → `撒旦`,
  `Abilities/MARY_EGYPT` `開火！` → `埃及的瑪利亞`,
  `Status/Cunning` `赤腳醫生` → `狡詐`, `Skills/KeysKnowledge` `鑰識` →
  `鑰之學識`, `Units/WolfDeadly`/`WolfFedka` `狼` → `換生狼`.
- A stray header row contributed by the review file was removed from
  `overrides.tsv`.

### Notes

- `make build` verified reproducible
  (sha256 `ec3c4a8425c9da7b18011c580563f9b2bd0646024227fed8918594a514f7da0b`).

## 1.2.0 — 2026-10-16

One consistent Traditional typeface for all on-screen text, and a deterministic
build.

### Added

- `plugin/bundles/tcserif` — a Unity-built static TMP font asset of **Iansui**
  (芫荽, SIL OFL, zh-TW), 4,330 characters, built at the game's own atlas
  settings (24 pt, padding 5, SDFAA).
- `tools/unity-font/` — documents the font rebuild and its traps (TMP 1.5.0
  required; one codepoint per glyph; pre-sized atlas).
- Runtime text conversion of the `DialogueDatabase "BlackBook"` and
  `TextTable "UILocalization"` assets in memory (12,720 strings), because their
  type trees are stripped and cannot be patched on disk.

### Changed

- The font is built with **Unity 2018.4.31f1** (changeset `212ea663d844`) —
  byte-identical to the engine that built the game, so the TMP asset format is
  compatible. TMP font assets cannot be produced offline; `UnityPy` cannot
  create Font bundles.
- **Iansui** replaces the previous Arial Unicode MS dependency (Monotype-
  licensed) with an OFL font, and avoids the SC/TC mismatch of using two cuts
  of one family.
- Three mechanisms apply the font to all text: a `FontService.GetFont`
  postfix, a `TMP_Text.set_font` prefix, and a periodic sweep for serialized
  fonts and later-created text.
- `make build` = generate → build-plugin → validate → package, producing one
  zip with the config payload, the plugin and its runtime data. Release zip
  grows to 1,453 entries / 3.2 MB.

### Fixed

- Names still showing Simplified (e.g. "Old Egor" as `老叶戈尔` instead of
  `老葉戈爾`): `DialogueLua.AddToTable` snapshots every asset field when a
  database is registered, and the speaker-name UI reads from that snapshot. The
  plugin now converts the database **before** the snapshot via a Harmony prefix
  on `DatabaseManager.Add(DialogueDatabase)`. 356 Lua-cached values were
  affected (Display Name `zh` 90, Name `zh` 109, Description `zh` 157).

## 1.1.0 — 2026-10-15

Rebuilt pipeline, plus a BepInEx plugin for the text and glyphs that cannot be
reached from the config files.

### Added

- `source/sc/` — the game's own Simplified Chinese source, checked in so
  `make build` no longer reads the installed game (and `uninstall.sh`/`ps1`
  restores from it).
- `reference/overrides.tsv` — reviewed corrections as reviewable text.
- Five real quality gates (coverage, structure, simplified, overrides,
  terminology), each proven to fail on a deliberate regression.
- BepInEx plugin (`plugin/`) with committed OpenCC tables
  (`plugin/tables/`), flattened to one candidate per key with greedy longest
  match (99.97% identical to real OpenCC on the game's own strings, guarded
  against double conversion because `s2twp` is not idempotent).
- Traditional-capable font registered as a TMP fallback, so Traditional-only
  characters no longer render as tofu (`口口口`).

### Fixed

- Nested-YAML converter bug that silently dropped `Service/Credits`
  (870 strings), `Demons`, `Izba` and `Abilities/BAD_KNIFE`:
  1,444 → 1,448 files, 2,362 → 3,479 strings.
- `uninstall.sh`/`ps1` were a no-op (they restored a stale backup that already
  held the converted files); they now restore from `source/sc`.
- Deleted 7,674 junk files committed by the old broken `deploy.sh`, which
  redirected its own log output into directory names.
- `deploy`/`uninstall` now honour `--dry-run` (they previously still wrote).

### Notes

- Only fields tagged `" zh"` are converted; the database also holds Japanese
  and Korean, whose shared codepoints (`国`/`学`/`会`) would otherwise be
  corrupted.

## 1.0.0 — 2026-06-12

Initial release.

- Extracted and converted 2,362 text strings (SC → TC via OpenCC).
- Text fields: Name (1,440), Description (562), Flavour (190), Quest descs (167).
- 1,444 Traditional Chinese YAML config files for direct game deployment.
- Reversible deployment with a backup system; `deploy.sh` / `uninstall.sh`.
