# Nexus Mods description — TC Localization (mod page)

> Paste into the Nexus mod page description. BBCode-friendly headings included as
> plain markdown; adapt to Nexus's editor as needed.

---

## Warhammer 40,000: Battlesector — 繁體中文化 (Traditional Chinese Localization)

Full **Traditional Chinese** localization for **Warhammer 40,000: Battlesector**
(patch **1.7.7**). Converts the in-game Simplified Chinese to Traditional Chinese —
menus, factions, units, campaign, mission text, unit descriptions, and the launcher.

The game ships with Simplified Chinese only. This mod delivers a proper Traditional
Chinese experience.

### ⚠️ Requirements (read first)

This mod has **two parts**. Install both once, then only ever update this mod:

1. **BepInEx 6 Framework (IL2CPP)** — a one-time runtime dependency
   (separate download on this page / in Files). You rarely need to update it.
2. **This TC Localization mod** — the fonts, text, and the runtime fix plugin.
   This is the part that gets updated over time.

> Why a framework? The game renders unit/campaign **descriptions** through a font
> that has no Chinese glyphs and garbles Traditional-specific characters at runtime.
> No amount of file editing fixes it — so a tiny BepInEx plugin (`TCFix`) corrects
> the font at runtime. It's open source and included with this mod.

### Installation (Vortex — recommended)

1. Install the **Warhammer 40,000: Battlesector Vortex extension** (Games → search)
   so Vortex can manage this game.
2. Install the **BepInEx 6 Framework** ZIP, then **Deploy**.
3. Install **this TC Localization** ZIP, then **Deploy**.
4. Launch the game **once** and reach the main menu (first launch is slower —
   BepInEx is initializing), then set the language to **Chinese (Simplified)** in
   Options. It will display as **Traditional Chinese**.

### Installation (manual)

Extract the **BepInEx Framework** ZIP into the game root, then extract **this mod's**
ZIP into the same game root (allow overwrite). Launch once.

### Uninstall

Vortex: purge/remove both mods — original game files are restored automatically.
Manual: delete `winhttp.dll` from the game root to disable BepInEx; restore the
backed-up `*.assets` / bundle files.

### Compatibility & notes

- Game version **1.7.7** (Unity 6, IL2CPP). Other versions untested.
- Windows (primary). Linux/Proton should work but is less tested.
- BepInEx 6 is a pre-release (Bleeding Edge) build; it's widely used for IL2CPP games.
- Safe to remove at any time.

### Known limitations (being refined)

- Some characters (e.g. 眾) currently use Japanese/Simplified glyph shapes rather
  than Traditional forms — a font re-bake from a Traditional-Chinese Noto is planned.
- Punctuation is currently half-width in places; full-width CJK punctuation is planned.
- The bold weight on some emphasized words is a little heavy.

### Credits

- Text conversion via OpenCC (s2tw). Fonts based on Noto Sans CJK.
- BepInEx by the BepInEx team (LGPL-2.1). `TCFix`/`TCDiag` plugin source is included
  and MIT-friendly for auditing.
