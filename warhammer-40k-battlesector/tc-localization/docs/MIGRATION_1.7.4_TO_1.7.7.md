# Migration: WH40K Battlesector TC Localization — 1.7.4 → 1.7.7

**Date:** 2026-07-23
**Author:** Crystal Mods maintainer (agent-assisted analysis)
**Status:** Stable baseline **built** (v0.2.0) — text + main UI font + launcher. Bundle fonts deferred pending baseline test.
**Game version:** 1.7.7 (Unity `6000.0.62f1`, build-guid `233ee0a952e84e97b2e5c5d62fdf0dc3`, patched 2026-07-22)

---

## 1. Executive summary

The game updated from **1.7.4 → 1.7.7**. The previously-built mod (v0.1.0, targeting
1.7.4) **no longer launches** when deployed on 1.7.7 because the 1.7.7 patch
re-serialised and re-authored every asset file the mod ships, so the old pre-built
binaries collide with the new game data.

A **full rebuild from the clean vanilla 1.7.7 assets is required.** The good news:
the **localization architecture is unchanged** (same TextRepository system, same 7
Chinese `TextAsset`s, same TMP font object, same Unity 6 engine), so the existing
1.7.4-era tooling design still applies — it just needs to be re-run against the new
vanilla files and re-packaged.

Two important discoveries shaped this migration:

1. **The in-game "backup" was contaminated.** `<game>/.zh-tw-mod-backup/` did *not*
   contain pristine vanilla files — it held the **old mod's Traditional-Chinese
   output**. It has been discarded; the rebuild sources exclusively from the
   proven-clean vanilla 1.7.7 game files.
2. **Font baking is still required.** Vanilla 1.7.7 bakes 3295 glyphs, but the TC
   text needs 2204 CJK codepoints of which **939 are missing** from the atlas —
   i.e. a text-only patch would show ~939 tofu (□) boxes.

---

## 2. Version facts

| Fact | 1.7.4 (old mod base) | 1.7.7 (current) |
|---|---|---|
| Unity | `6000.0.62f1` | `6000.0.62f1` (unchanged) |
| Loc system | TextRepository (`resources.assets` TextAssets) | Same |
| Chinese slot | Simplified only (`*_chinese`) | Same |
| Languages | 8 (BR-PT, ZH, FR, DE, KO, PL, RU, ES) | Same |
| TMP font | `sharedassets1.assets` `pid 3644` (NotoSansCJK) | Same object present |
| Patched 2026 | — | 07-22 18:52 (exe, levels, bundles, catalog) |

**Conclusion:** No engine or architecture migration is needed — only a data rebuild.

---

## 3. What the 1.7.7 patch changed (evidence-based)

Hashes computed on the live install (first 16 hex shown). "Backup" = the
(contaminated) 1.7.4-era `.zh-tw-mod-backup`; "Vanilla 1.7.7" = current game files.

| File | Changed by 1.7.7? | Notes |
|---|---|---|
| `Warhammer 40K Battlesector_Data/resources.assets` | **Yes** | TC text lives here — rebuild |
| `…/sharedassets1.assets` (+`.resS`) | **Yes** (`.assets`); `.resS` unchanged | TMP font `pid 3644` — re-bake |
| `…/StreamingAssets/startup_assets_all.bundle` | **Yes** | Early-boot font fallback — re-patch |
| `…/StreamingAssets/mapbuilder-tools_assets_all.bundle` | **Yes** | Map-builder font — re-patch |
| `…/StreamingAssets/ui-shared_assets_all.bundle` | **Yes** | 684 MB; font references |
| `…/StreamingAssets/aa/catalog.bin` + `.hash` | **Yes** | Addressables catalog |
| `…/StreamingAssets/catalog.bin` + `.hash` | **No** (identical) | Root catalog untouched |
| `Launcher/Localization/stringsChinese.resx` | No (still 1.7.4 vanilla) | Launcher UI — re-patch anyway |

**Current game files are clean vanilla 1.7.7** — the mod is *not* currently deployed
(verified: live `resources.assets` / `sharedassets1.assets` hashes match neither the
old mod dist nor the old backup).

---

## 4. Critical discovery — the contaminated backup

The mod's build tooling keeps a "pristine backup" at `<game>/.zh-tw-mod-backup/`
with a `MANIFEST` of SHA-256 hashes. **A byte-level diff proved this backup is not
vanilla** — it holds the *old mod's Traditional-Chinese output*:

| Line id | `.zh-tw-mod-backup` (labelled "vanilla") | Real vanilla 1.7.7 |
|---|---|---|
| campaign 0 | 聲響投遞者已激活 (**Traditional**) | 声响投递者已激活 (**Simplified**) |
| campaign 1 | 已**經**安全 (Trad) | 已**经**安全 (Simp) |
| campaign 5 | 消**滅**所有**敵**人 (Trad) | 消**灭**所有**敌**人 (Simp) |

A vanilla game ships **Simplified** in the `chinese` slot; a TC mod produces
**Traditional**. The backup contains Traditional → it was captured *after* the mod
was deployed. This also explains an apparent "788 added / 825 removed codepoint
churn" between the two files: it was simply Simplified↔Traditional variance, **not**
a re-translation.

**Consequences & action taken**
- The backup's `MANIFEST` hashes and its bundle copies are **modded, not pristine**.
- The backup was **deleted**; the rebuild sources from a fresh read-only snapshot of
  the clean vanilla 1.7.7 game (`.copilot_workspace/vanilla-1.7.7/`).
- Going forward, a pristine snapshot must be taken **only** immediately after a Steam
  update / verify, **before** any deploy.

---

## 5. Content delta (what genuinely changed in 1.7.7)

Comparing the mod's captured text against vanilla 1.7.7 SC, after accounting for the
Simplified/Traditional axis, the **only genuinely new strings** are:

| Repository | New ids | Content |
|---|---|---|
| `campaign_chinese` | 479–482 (+4) | Empty placeholders (`\|\|\|\|1\|0\|1`) — ship empty |
| `units_chinese` | 1667–1668 (+2) | Blood Angels **"Path of Glory – Confirmed Kill"** mechanic (荣耀之路 – 确认击杀 …); +202 CJK chars |

Everything else is byte-length-preserved and re-converts automatically via OpenCC.

**Glyph coverage** (vanilla 1.7.7 `pid 3644`):

| Metric | Value |
|---|---|
| Baked characters | 3295 |
| TC CJK codepoints needed | 2204 |
| **Missing (tofu risk)** | **939** (all CJK ideographs) |
| Font free glyph rects | 369 (< 939 → atlas extension required) |

---

## 6. Why the old mod fails on 1.7.7

The 1.7.7 patch re-serialised `resources.assets`, `sharedassets1.assets`, and the
`startup` / `mapbuilder` / `ui-shared` bundles with new object layouts, new content,
and new addressables catalog CRCs. The old mod ships **pre-built 1.7.4 binaries**;
dropping them onto a 1.7.7 install produces serialization/offset mismatches and
catalog CRC conflicts → the game fails to launch. A rebuild against 1.7.7 vanilla is
the only correct fix.

---

## 7. Rebuild pipeline (full)

All steps read the **clean vanilla 1.7.7** files and write to
`translation/zh-TW/dist/`. **No step writes to the game folder.**

| Phase | Step | Tool | Output |
|---|---|---|---|
| 0 | Clean source snapshot | copy vanilla 1.7.7 → `.copilot_workspace/vanilla-1.7.7/` | source of truth |
| 1 | TC text (byte-identical `s2tw`) | `patch_resources_174.py` | `dist/resources.assets` |
| 1 | Launcher TC (`s2twp`) | `patch_launcher.py` | `dist/stringsChinese.resx` |
| 2 | Bake 939 missing TC glyphs into `pid 3644` | `bake_fonts_174.py` | `pid3644.bin` + edited `.resS` |
| 2 | Inject font bytes into `sharedassets1` | C# `FontTool replace` (AssetsTools.NET) | `dist/sharedassets1.assets` |
| 2 | Map-builder bundle font | `patch_mapbuilder_font.py` | `dist/mapbuilder-tools_assets_all.bundle` |
| 2 | Startup/ui-shared bundle font | `patch_font.py` | `dist/startup_assets_all.bundle` |
| 3 | New-string terminology review | manual | verify units 1667–1668 |
| 4 | Catalog safety | validate "skip catalog" still holds for 1.7.7 | — |
| 5 | Package | Vortex-installable zip | `dist/…-v0.2.0.zip` |

### Baseline build actually shipped (v0.2.0)

Per maintainer decision, the **stable baseline** ships only the components proven
to fully resolve their target text; the historically-fragile bundle fonts (which
"previously do not fully solve the issue") are **deferred** until the baseline is
confirmed to launch. Completed and verified:

| Step | Result |
|---|---|
| `patch_resources_174.py` | ✅ 7/7 TextAssets, byte-identical (8,369,508 B) |
| `patch_launcher.py` | ✅ launcher resx → TC |
| `bake_fonts_174.py` | ✅ **939/939 glyphs placed, 0 unplaced** |
| `FontTool replace` | ✅ `pid 3644` 6,271,524 → 6,352,544 B; CharacterTable 3295 → **4234** |
| edited `.resS` | ✅ differs from vanilla only in the 4 MB atlas region (offset 0) |
| **Deferred** | ⏸ `patch_font.py` (startup) + `patch_mapbuilder_font.py` (map-builder) |

**Deliverable:** `warhammer-40k-battlesector/dist/wh40k-battlesector-tc-localization-v0.2.0.zip`
(101 MB). May show residual tofu only in long campaign-description fallback text and
the map-builder tool UI — to be addressed after the baseline is validated.

**Key technical facts**
- `patch_resources_174.py` uses OpenCC **`s2tw`** (strict 1:1 char map) so every
  TextAsset keeps its exact byte length → no serialized-offset corruption.
- UnityPy 1.25 cannot re-serialize Unity 6 `.assets`; the C# **`FontTool`**
  (`AssetsTools.NET`, prebuilt `net10.0`) performs the raw `pid 3644` byte swap.
- Atlas has 369 free rects but 939 glyphs are needed → the bake must **extend the
  atlas** (as the map-builder path already does, 2048→4096) or spill to a second
  atlas; capacity must be validated during the bake.

---

## 8. Packaging & deployment policy (MANDATORY)

- **Deliverable = a Vortex-installable ZIP in `dist/`.** The user installs it via
  Vortex, which makes its own backups.
- **The agent must NOT deploy to the game folder** and must **NOT** run the
  `deploy.sh` / `deploy.ps1` deploy phase. Those scripts are for reference/manual use
  only.
- Zip layout is game-relative so Vortex maps files correctly:
  ```
  Warhammer 40K Battlesector_Data/resources.assets
  Warhammer 40K Battlesector_Data/sharedassets1.assets
  Warhammer 40K Battlesector_Data/sharedassets1.assets.resS
  Warhammer 40K Battlesector_Data/StreamingAssets/startup_assets_all.bundle
  Warhammer 40K Battlesector_Data/StreamingAssets/mapbuilder-tools_assets_all.bundle
  Launcher/Localization/stringsChinese.resx
  modinfo.json
  README.md
  ```
- `modinfo.json`: bump `version` and set `supportedVersions: ["1.7.7"]`.

---

## 9. Validation checklist (post-install, user-performed)

1. Launcher shows Traditional Chinese.
2. Game launches (no crash) with Chinese selected.
3. Main menu / settings render TC, no tofu.
4. Unit roster incl. Blood Angels **"榮耀之路 – 確認擊殺"** (Path of Glory) renders.
5. Mission briefings + campaign text render (watch the historically-fragile
   description text for residual tofu).
6. Map-builder UI (if used) renders TC.
7. Screenshot the above for the release page.

---

## 10. Risks & open items

- **Atlas capacity** — 939 glyphs vs 369 free rects; must confirm the atlas
  extension packs all glyphs (track `bake_report.json` `unplaced`).
- **Addressables catalog** — the 1.7.4 build deliberately *skipped* deploying
  `catalog.*`; confirm the 1.7.7 `startup`/`ui-shared` bundles we patch are not
  CRC-verified against `aa/catalog.bin`, or handle the CRC.
- **Stale orchestrator** — `tools/scripts/deploy.sh` still calls the pre-1.7.4
  scripts; the real build path is the `_174` scripts + `FontTool`. Consolidate into a
  committed, reproducible **build-only** script (no deploy) as part of this update.
- **Provenance** — keep the clean vanilla 1.7.7 snapshot hashes recorded so future
  updates can diff cleanly and avoid another contaminated backup.
