# Changelog — WH40K Battlesector Traditional Chinese Localization

All notable changes to this mod. Versions follow the `modinfo.json` `version`
field. The mod ships as a Vortex ZIP; a separate **Core (BepInEx6)** framework ZIP
is a one-time dependency (see the mod page).

## 0.2.2

Refinement release focused on glyph quality, punctuation, and broader runtime
coverage, plus a reproducible glossary-driven build.

### Added

- **Traditional-Chinese letterforms.** Fonts `785` (description font) and `3644`
  (main UI) now render CJK glyphs re-rendered from **Noto Sans CJK TC** instead of
  the Japanese Noto forms used previously (e.g. 眾 now uses the 罒-top TC form).
- **Full-width CJK punctuation.** Sentence punctuation is converted to full-width
  where adjacent to CJK: `, . ! ? : ;` → `，。！？：；`, parentheses `( )` → `（）`
  with balanced matching, and `...` → `……`. Numbers, decimals, version strings and
  markup tags are left untouched.
- **Glossary-driven build pipeline.** A new editable
  [`translation/zh-TW/glossary.tsv`](translation/zh-TW/glossary.tsv) applies term
  corrections after OpenCC. `make build` rebuilds the text, injects it, **auto-bakes
  any newly-needed glyphs**, and repackages the ZIP. Seeded with `重灌仲裁者 →
  重裝仲裁者` and `腥紅 → 猩紅`.
- Baked the previously-missing punctuation/symbol glyphs into the fonts:
  `！ ？ ）` plus `•` (bullet) and `∞`.

### Changed

- **`TCFix` runtime plugin → 1.2.0 (generalized).** Instead of swapping only one
  hard-coded font, it now swaps **any** on-screen text that contains CJK but is
  drawn with a font that lacks the glyphs (character table &lt; 3000). This fixes
  the **exit-game modal**, **Crusade zone modifiers/rewards**, save/name dialogs,
  and other screens that used a third font variant
  (`futura … - with shadow`, dynamic) the previous plugin never touched.
- **Faster correction.** The plugin scans every ~0.2s (was 1s), so the brief
  "gibberish then fix" flash on newly-shown modals is effectively gone.
- Reduced `<b>` bold weight (`_WeightBold` 0.75 → 0.4) on the CJK SDF materials so
  bold emphasis (e.g. `<b>遠征</b>`) is less heavy.
- Text conversion uses OpenCC **`s2tw`** (character-level), avoiding `s2twp`
  phrase-conversion errors such as `重装 → 重灌` ("reinstall").

### Fixed

- Sentence-ending `？`/`！` and bullet `•` rendering as tofu (□) after punctuation
  conversion — the required glyphs are now present in the render font.

### Notes

- The **source is no longer bundled** in the mod ZIP. The `TCFix` plugin is
  open-source in this repository:
  `.../tc-localization/bepinex/TCFix/`.
- Requires the **Core (BepInEx6)** framework (install once).

## 0.2.1

- **Runtime description fix (`TCFix`).** After exhausting asset-level font edits,
  the campaign/army/unit **description** garble was solved with a BepInEx 6 (IL2CPP)
  plugin that, at runtime, swaps the CJK-less description font
  (`futura … - No Underlay`) to the full-Traditional font. Descriptions render
  correct Traditional Chinese.
- **Two-ZIP split.** The BepInEx framework and the localization are separate files
  so updates to the localization don't re-download the framework.
- Vortex extension updated to 1.1.0 to deploy BepInEx + plugin + assets to the game
  root.

## 0.2.0

- Asset-level Traditional-Chinese baseline for game **1.7.7** (Unity 6, IL2CPP):
  SC→TC text in `resources.assets`, main-UI font (`sharedassets1` pid 3644) baked to
  full TC coverage, launcher strings (`stringsChinese.resx`). Main menus, factions,
  units, missions and buttons render correct Traditional Chinese.
- In-game: select **Chinese (Simplified)** to display Traditional Chinese.
