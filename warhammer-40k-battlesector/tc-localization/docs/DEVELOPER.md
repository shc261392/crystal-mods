# Developer Guide & Technical Record

Everything a new developer needs to understand, rebuild, and extend the WH40K
Battlesector Traditional-Chinese localization. This is the durable record of the
research that produced the current design — read it before changing fonts or the
build.

- Game: **Warhammer 40,000: Battlesector 1.7.7**, Unity **6000.0.62f1**, **IL2CPP**.
- Delivery: **Vortex ZIP only.** Never deploy from tooling; the user installs via
  Vortex. All game-folder access during development is read-only (hash/log checks).

---

## 1. What the mod is made of

The localization ships these files (game-root relative), plus the separate **Core
(BepInEx6)** framework ZIP:

| File | Purpose |
|---|---|
| `BepInEx/plugins/TCFix.dll` | Runtime font-swap plugin (the description/modal fix) |
| `Warhammer 40K Battlesector_Data/resources.assets` | SC→TC text (7 TextAssets) + `TMP_Settings` global fallback |
| `…_Data/sharedassets0.assets` | Fonts 782/783/**785** (description font) + their materials |
| `…_Data/sharedassets1.assets` (+ `.resS`) | Font **3644** (main UI) + `.resS` atlas |
| `…_Data/StreamingAssets/{startup,mapbuilder}…bundle` | Boot/editor bundles (static CJK fonts) |
| `Launcher/Localization/stringsChinese.resx` | Launcher UI strings |

In-game the player selects **Chinese (Simplified)**; the mod's converted text is in
the Chinese slot, so it displays as Traditional.

---

## 2. The description-font saga (the core research)

**Symptom:** menus/units/factions rendered perfect TC, but campaign/army/unit
**descriptions** and several modals garbled the Traditional-specific characters
(將領隊遠眾…) — not tofu, *wrong* glyphs.

**~15 asset-level font builds failed.** We made every CJK font full + static, added
a global fallback, patched `sharedassets0/1` and both bundles — zero effect on the
descriptions. The decisive lesson:

> When Simplified renders perfectly but Traditional garbles, and asset edits have
> **zero** effect, the render font is chosen/handled at **runtime**. Stop guessing at
> assets; use a BepInEx diagnostic to read the *actual* runtime `TMP_Text.font`.

**Root cause (confirmed by a BepInEx diagnostic):** the description text is drawn by
TMP font **`futura medium condensed bt SDF - No Underlay`** (`sharedassets1` pid
**3646**) which has only **124 Latin glyphs and no CJK**. It renders CJK through a
fallback chain that produces correct common characters but garbles Traditional-only
forms. Editing the fallback fonts did not help — the runtime resolution is the
problem.

**The fix — `TCFix` (BepInEx 6 IL2CPP plugin).** At runtime, swap any `TMP_Text`
that contains CJK but whose font lacks the glyphs to the full-Traditional font
**`futura medium condensed bt SDF`** (`sharedassets0` pid **785**, ~3600+ glyphs,
which renders TC correctly). See §5.

**Two more font variants matter** (found via the generalized diagnostic):

| Font | pid / location | pop | glyphs | Used by |
|---|---|---|---|---|
| `futura … bt SDF` | sa0 **785** | static | ~3640 | *(target — renders TC correctly)* |
| `futura … - No Underlay` | sa1 **3646** | static | 124 | descriptions, most modals |
| `futura … - with shadow` | (dynamic) | dynamic | ~91 | Crusade zone modifiers, rewards |

**Critical API gotcha:** `TMP_FontAsset.HasCharacter(cp)` **searches fallbacks**, so
it returns `true` even for these broken fonts. Do **not** use it to detect the
problem. The reliable signal is `characterTable.Count` — real CJK fonts have
thousands of glyphs; the broken ones have ~100.

---

## 3. Font facts (verified)

- **Atlas orientation is top-down**: a glyph's pixels live at
  `atlas[m_GlyphRect.m_Y : m_Y+h, m_X : m_X+w]` with the SDF stored `flipud`'d.
  Both bake scripts and the game agree on this.
- `sharedassets0` **atlas 295** is **inline** (Alpha8, 2048×4096), **shared by fonts
  782 and 785**. Editing it affects both; keep their glyph layout consistent.
- `sharedassets1` **atlas 21** is in **`sharedassets1.assets.resS`** (Alpha8,
  2048×2048, offset 0, 4 MB).
- 785 uses material `NotoSansCJKjp-Regular SDF Material` (pids **2/8**); 782/783 use
  **9**. All three carry `_WeightBold` (bold dilation) and `_WeightNormal`.
- `resources.assets` `TMP_Settings` (pid 223) holds the global
  `m_fallbackFontAssets`; the shotgun build added `(fileID 2 → sa0 782)`.

---

## 4. Build pipeline (`make build`)

```
make build        # = bash build.sh
```

Steps (see [`build.sh`](../build.sh)):

1. **`build_text.py`** — from *vanilla* `resources.assets`: OpenCC **`s2tw`** →
   **glossary** (`translation/zh-TW/glossary.tsv`) → **punctuation**
   (`convert_punctuation.py`) → serialized TextAsset bins. Idempotent (always from
   vanilla). Requires `MOD_VANILLA_RES` (a pristine `resources.assets`).
2. **FontTool `replace`** injects the 7 TextAssets into `resources.assets`
   (base = current dist, so the `TMP_Settings` fallback is preserved).
3. **`bake_font_generic.py`** scans the new text and **adds any missing glyphs** to
   fonts 785 (sa0) and 3644 (sa1), rendered from **Noto Sans CJK TC**.
4. Package the Vortex ZIP.

To add a translation correction: edit `glossary.tsv` (`search<TAB>replace`), run
`make build`, ship the new ZIP. New glyphs are baked automatically.

> `make build` **preserves** the fonts' existing TC re-render, bold weight, and
> static conversions (already in the dist sharedassets) and only *adds* glyphs. For
> a full font rebuild use the scripts in §6.

### Environment

`MOD_VANILLA_RES`, `MOD_PY` (venv python), `MOD_FT` (fonttool.dll), `MOD_TC_OTF`
(NotoSansCJKtc), `MOD_ZIP_OUT`. Python deps: `UnityPy`, `opencc`, `freetype`,
`numpy`, `scipy`, `Pillow`. `FontTool` is a small AssetsTools.NET (C#/dotnet) helper
under `.copilot_workspace/csharp/FontTool` (scratch; not tracked).

---

## 5. `TCFix` plugin (`bepinex/TCFix/`)

BepInEx 6 (IL2CPP) `BasePlugin` that injects a `MonoBehaviour`. Every ~0.2s it
enumerates `Resources.FindObjectsOfTypeAll<TMP_Text>()` (the *proven* enumerator —
`FindObjectsOfType` returned nothing in this Il2CppInterop build), and for each
**active** text containing CJK whose font's `characterTable.Count < 3000`, sets
`t.font` to the full-TC 785 font, then `SetAllDirty()` + `ForceMeshUpdate()`.

Build: `dotnet build -c Release` (references the game's `BepInEx/core` + `interop`
via `GameDir`; interop is generated after the first BepInEx run). Output →
`bin/Release/TCFix.dll`.

Design notes / pitfalls:
- Use `characterTable.Count`, not `HasCharacter` (searches fallbacks — see §2).
- Use `FindObjectsOfTypeAll` (active-only `FindObjectsOfType` regressed to no-op).
- Swapping to 785 loses the "with shadow" font's shadow on zone modifiers — an
  accepted cosmetic trade for correct Traditional rendering.
- `Il2CppInterop` here does **not** prefix namespaces: use `TMPro.TMP_Text`.

**`TCDiag`** (`bepinex/TCDiag/`) is the diagnostic sibling: it logs every on-screen
CJK text with its font's properties (`[TCTEXT]` lines) so culprit fonts can be
identified. Not shipped to users.

---

## 6. Font tooling (full rebuilds)

- **`rebuild_font_tc.py`** — in-place re-render of a static font's CJK glyphs from
  NotoSansCJKtc into their existing atlas rects (no repack, no atlas growth, no
  material change). Blits **only the exact `m_GlyphRect`** — writing the padded box
  corrupts tightly-packed neighbours (proven at pointSize 17).
- **`bake_font_generic.py`** — *adds* missing glyphs to a font's free rects (used by
  `make build`). `is_relevant` covers CJK, CJK punctuation, full-width forms, general
  punctuation (bullet/em-dash/quotes/ellipsis) and `∞`.
- **`edit_material_weight.py`** — sets `_WeightBold` on the Noto SDF materials
  (pids 2/8/9). `MOD_WEIGHT_BOLD` (default 0.4).
- **`FontTool replace <in> <out> <pid> <bin>`** — the C# raw-object swap used to
  write UnityPy-serialized bins back into Unity 6 `.assets` (UnityPy cannot
  reliably reserialize whole Unity 6 `.assets`; full `env.file.save()` **corrupts**
  them — only ever raw-replace individual objects).

---

## 7. Hard-won lessons

1. SC-perfect + TC-garble + asset edits do nothing ⇒ **runtime** font handling ⇒
   diagnose with BepInEx, don't guess at assets.
2. `HasCharacter` lies (fallbacks). Discriminate with `characterTable.Count` /
   `atlasPopulationMode`.
3. Never `env.file.save()` a Unity 6 `.assets` — corrupts it. Raw-replace objects
   via FontTool only.
4. Blit glyphs into the **exact rect**, never the padded box (neighbour corruption).
5. Introducing new codepoints (punctuation) requires the render font to have those
   glyphs, or they tofu — `make build` bakes them automatically.
6. Use OpenCC **`s2tw`** (char-level), not `s2twp` (phrase) which mistranslates
   terms like `重装 → 重灌`.
