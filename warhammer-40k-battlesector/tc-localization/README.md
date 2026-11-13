# WH40K Battlesector — Traditional Chinese Localization

Community **Traditional Chinese (zh-TW)** localization for **Warhammer 40,000:
Battlesector** (Black Lab Games / Slitherine), game version **1.8.0**.

The game ships with Simplified Chinese only. This mod converts it to Traditional
Chinese — menus, factions, units, campaign, mission text, unit **descriptions**,
and the launcher. In-game, select **Chinese (Simplified)**; it displays as
Traditional.

> Version **0.3.0** (Battlesector 1.8.0). See [CHANGELOG.md](CHANGELOG.md) for changes and
> [docs/DEVELOPER.md](docs/DEVELOPER.md) for the full technical record.

## How it works

Battlesector's fonts cover only the Simplified glyphs the vanilla text uses, and
several of them are dynamic: Traditional-only characters come out missing or
garbled. Pure asset edits can't fix this alone. So the mod combines:

- **Asset localization** — SC→TC text in `resources.assets`, plus the 1.8.0
  TextMesh Pro fonts (`sharedassets2.assets` and the startup/mapbuilder bundles)
  re-baked to full Traditional coverage (Noto Sans CJK TC).
- **`TCFix`** — a small open-source **BepInEx 6 (IL2CPP)** plugin that, at runtime,
  swaps any on-screen text whose font lacks the CJK glyphs to the full-Traditional
  font. This is what fixes descriptions, modals and other partial fonts.

Because of the runtime component, the mod requires the **BepInEx Framework**
mod (a one-time shared dependency, installed separately — see its own mod page).

## Install (Vortex — recommended)

1. Install the **Warhammer 40,000: Battlesector** Vortex extension (Games → search).
2. Install the **BepInEx Framework** mod, then **Deploy**.
3. Install this **Traditional Chinese Localization** file, then **Deploy**.
4. Launch once to the main menu (first launch is slower — BepInEx initializes), then
   set language to **Chinese (Simplified)** in Options. It displays as Traditional.

**Uninstall:** purge/remove both mods in Vortex — the originals restore
automatically. Manual: delete `winhttp.dll` from the game root and restore the
backed-up `*.assets` / bundle files.

## Requirements

- Warhammer 40,000: Battlesector **1.8.0** (Steam / GOG). Windows primary;
  Linux/Proton less tested.
- **BepInEx Framework** mod (separate file on the mod page).

## Building from source

```bash
make build        # rebuild text from the glossary, auto-bake glyphs, package the ZIP
```

`make build` runs [`build.sh`](build.sh): OpenCC `s2tw` → glossary → punctuation →
inject → bake missing glyphs → package. To correct a translation term, edit
[`translation/zh-TW/glossary.tsv`](translation/zh-TW/glossary.tsv) and re-run
`make build`.

Prerequisites: Python with `UnityPy opencc freetype-py numpy scipy Pillow`, the
.NET SDK (for `TCFix`), a pristine game install, and Noto Sans CJK TC at
`MOD_TC_OTF` (see `build.sh`). Every step starts from the live vanilla files, so
`make build` is reproducible.
See [docs/DEVELOPER.md](docs/DEVELOPER.md) for the font pipeline, `TCFix` build, and
environment variables.

## Layout

| Path | What |
|---|---|
| `bepinex/TCFix/` | Runtime font-swap plugin (source) |
| `bepinex/TCDiag/` | Diagnostic plugin (developer only) |
| `tools/scripts/` | Build/font tooling (`build_text.py`, `bake_font_generic.py`, …) |
| `translation/zh-TW/glossary.tsv` | Editable term corrections |
| `build.sh`, `Makefile` | Build entry points |
| `docs/` | Developer guide, Nexus text, BepInEx setup |

## License / credits

- Text via OpenCC (`s2tw`). Fonts based on **Noto Sans CJK TC**.
- `TCFix` is open source (this repo, `bepinex/TCFix/`). BepInEx is LGPL-2.1.
