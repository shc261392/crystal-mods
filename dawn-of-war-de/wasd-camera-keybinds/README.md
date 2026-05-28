# Keybinding Overhaul — DoW:DE

A drop-in replacement for `Engine/defprofile/keydefaults.lua`, the file that
defines the default key layout used by **Warhammer 40,000: Dawn of War –
Definitive Edition** the first time a profile is created (and reset to from
the in-game *Options → Hotkeys → Reset Defaults* button).

## Why this exists

DoW:DE ships five stock layouts in `Engine.sga`:

| Stock layout | What it is |
|---|---|
| `keydefaults.lua` | QWERTY default |
| `keydefaults_grid.lua` | Grid (positional ability) layout |
| `keydefaults_grid_azerty.lua` | Grid for AZERTY keyboards |
| `keydefaults_grid_qwertz.lua` | Grid for QWERTZ keyboards |
| `keydefaults_modern.lua` | "Modern RTS" variant |

**None of them pans the camera with bare `W` `A` `S` `D`** — all five require
`Shift+` to use WASD for camera pan, because the bare letters are claimed by
race-specific building / ability bindings. The community workaround has been
to manually edit `keydefaults.lua` to swap the modifier between camera and
action bindings. This mod automates and standardises that fix.

## Presets

Three presets ship, covering two different installation strategies:

| Preset | Deploys | Strategy |
|---|---|---|
| [`vanilla`](presets/vanilla/HOTKEYS.md) | `Engine/defprofile/keydefaults.lua` | Byte-identical to the stock DoW:DE QWERTY layout (v15.2). Ship this to undo another preset without verifying game files. |
| [`wasd-camera`](presets/wasd-camera/HOTKEYS.md) | `Engine/defprofile/keydefaults.lua` | **Replaces the Classic preset.** Plain `W`/`A`/`S`/`D` pan the camera; bare-letter action bindings move to `Shift+<letter>`. The in-game *Classic Hotkeys* option becomes WSAD. |
| [`wasd-camera-ingame`](presets/wasd-camera-ingame/HOTKEYS.md) | `Engine/defprofile/keydefaults_modern.lua` | **Replaces the Modern preset slot.** In-game *Options → Hotkey Preset → "Modern Hotkeys"* now loads the WSAD layout. Classic stays untouched so you can switch back at any time. |

### Which one should I install?

- **"I want WSAD permanently as Classic"** → `wasd-camera`.
- **"I want to keep Classic intact and pick WSAD from the in-game dropdown"** → `wasd-camera-ingame` (then in-game: *Options → Hotkeys → Preset → "Modern Hotkeys"*).
- **"I broke my hotkeys and want stock back"** → `vanilla`.

The two WSAD presets are functionally identical in bindings — they differ only
in **which slot they occupy**.

## Why two slots? The engine's hardcoded preset list

During development we discovered that `W40k.exe`, `W40kMod.dll`, and
`DXP3Mod.dll` all hardcode a fixed list of three preset filenames:

- `keydefaults.lua` — Classic
- `keydefaults_grid.lua` — Grid
- `keydefaults_modern.lua` — Modern

Any other filename (e.g. `keydefaults_wasd.lua`) is silently ignored by the
engine — the Options dropdown will not show it. So the in-game variant
overwrites the **Modern** slot, which has the lowest installed base (it was
introduced in the 2025 Definitive Edition redesign and most returning players
stick with Classic).

The Grid slot is left untouched because competitive multiplayer players who
learned positional hotkeys depend on it.

## Stock preset main bindings (for reference)

Quick at-a-glance comparison of the three stock presets so you can pick which
slot to claim:

| Action | Classic (default) | Grid (positional) | Modern (2025 redesign) |
|---|---|---|---|
| Stop | `Q` | `W` | `S` |
| Move | `V` | `Q` | `M` |
| Attack-move | `A` | `E` | `A` |
| Attack (melee) | `Z` | `R` | `Z` |
| Attack ground | `G` | `S` | `G` |
| Melee stance toggle | `Ctrl+F6` | `F` | `W` |
| Repair | `E` | `S` | `H` |
| Reinforce | `R` | `Ctrl+Q` | `R` |
| Stances 1–5 | `F1`–`F5` | `F2`–`F6` | `Numpad 1`–5 |
| Camera pan | `Shift+WASD` + arrows | `Shift+WASD` + arrows | `Shift+WASD` + arrows |

All three stock presets require `Shift+WASD` for camera pan — the very issue
this mod fixes. Per-faction tables are in each preset's `HOTKEYS.md`.

## How it works

`W40k.module` registers `Data` (the unpacked loose-file folder) **before**
`Engine.sga` in its archive priority list. Placing patched lua files at
`<game-root>/Engine/defprofile/` therefore wins over the packed copies
without any SGA rebuilding.

This is the same loose-file-override pattern the game already uses internally
to layer Definitive-Edition assets on top of the 2004 base archives.

### How presets are discovered

The engine does **not** glob `Engine/defprofile/keydefaults*.lua`. The three
preset filenames (`keydefaults.lua`, `keydefaults_grid.lua`,
`keydefaults_modern.lua`) are hardcoded inside `W40k.exe`, `W40kMod.dll`, and
`DXP3Mod.dll`. Adding a new filename does nothing.

Each loaded file declares its dropdown display label via `bindings_locstring`,
a reference to an entry in `Engine.ucs`:

```lua
bindings_version  = 15.2
bindings_locstring = "$11271750"   -- $11271750 = "Classic Hotkeys"
                                   -- $11271751 = "Grid Hotkeys (QWERTY)"
                                   -- $11271752 = "Modern Hotkeys"
```

The `wasd-camera-ingame` preset overwrites `keydefaults_modern.lua` and keeps
its locstring as `$11271752`, so the in-game dropdown entry still reads
"Modern Hotkeys" — but selecting it now loads the WSAD layout.

## Installation

### Vortex Mod Manager

1. Install the **Dawn of War – Definitive Edition** Vortex extension (one-time
   setup; ships separately as `vortex-ext-game-warhammer40kdawnofwar-v*.zip`).
2. Drag your chosen preset zip onto Vortex
   (`wh40k-dow-de-keybinds-<preset>-v*.zip`).
3. Click *Deploy Mods*. Vortex routes the archive to the game root because
   its paths begin with `Engine/` — the existing root-mod installer handles
   it; no keybind-specific extension changes are required.

### Manual install

1. Open the game folder: in Steam, right-click *Dawn of War – Definitive
   Edition* → *Manage* → *Browse local files*.
2. Make a backup of `Engine/defprofile/keydefaults.lua` if you have one (the
   stock copy lives inside `Engine/Engine.sga`, so you can always recover it
   from there).
3. Extract the preset zip directly into the game folder. The archive
   structure mirrors the game's layout, so the file lands at
   `Engine/defprofile/keydefaults.lua`.
4. Start the game. If a profile already exists, open *Options → Hotkeys →
   Reset Defaults* to adopt the new layout (existing custom bindings live in
   `%APPDATA%\Relic Entertainment\Dawn of War\Profiles\<profile>\` and are
   not touched).

### Uninstall

- `vanilla` / `wasd-camera`: delete `Engine/defprofile/keydefaults.lua`. The
  packed copy in `Engine.sga` resumes service automatically.
- `wasd-camera-ingame`: delete `Engine/defprofile/keydefaults_modern.lua`.
  The Modern dropdown entry returns to Relic's stock Modern bindings. Profiles
  that were saved while WSAD-Modern was selected keep those bindings until you
  pick another preset in *Options → Hotkeys* and click *Reset Defaults*.

## How the WSAD preset is generated

`scripts/build_keybind_presets.py` reads
[`stock/keydefaults.lua`](stock/keydefaults.lua) (a verbatim copy of the file
unpacked from `Engine.sga` with `relic sga unpack`) and applies two rules:

1. **`camera_bindings` block** — every `Shift+W`, `Shift+A`, `Shift+S`,
   `Shift+D` token is replaced with the bare letter.
2. **All other bindings** — every value that is exactly the bare letter `W`,
   `A`, `S`, or `D` (as a standalone token in a comma list) is prefixed with
   `Shift+`. Tokens that already carry a modifier (`Control+`, `Shift+`,
   `Alt+`, multi-key combos) are left untouched.

This produces 177 transformed lines from the v15.2 source. Re-running the
script against a future stock release (v15.3+) regenerates the preset
deterministically.

```bash
make keybinds-build              # regenerate presets from mod/keybinds/stock/
make package-keybinds            # build zip per preset under dist/
```

## Adding the stock source after a game update

If Relic ships a new `keydefaults.lua` version:

```bash
# 1. Unpack the current Engine.sga from your install
uv run relic sga unpack \
    "<game-root>/Engine/Engine.sga" \
    .copilot_workspace/engine_unpack

# 2. Refresh the committed stock copy
cp .copilot_workspace/engine_unpack/defprofile/keydefaults.lua \
   mod/keybinds/stock/keydefaults.lua

# 3. Regenerate presets
make keybinds-build
```

The diff against `mod/keybinds/stock/keydefaults.lua` in git tells you
exactly what Relic changed and which new bindings the transform may need to
account for.
