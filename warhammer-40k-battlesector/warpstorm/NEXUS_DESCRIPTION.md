# Warpstorm — stat editor & Army Painter for Battlesector

Change any unit or weapon stat. Repaint whole armies, including models and
portraits, in your own colours or one of ten chapter schemes. Everything is done
in one Windows app, in ten languages, and nothing in the game files is changed.

> **Please read first**
>
> - **Single-player only.** Changing stats in multiplayer is cheating and can get
>   you banned. Don't.
> - **Requires the BepInEx Framework mod.** Install it first and start the game
>   once.
> - **Game updates** can rename internal fields. Warpstorm skips anything it can't
>   find and writes a warning to the log, and the rest keeps working. Check for an
>   update after big patches.

---

## What you get

**Stat editor**
- Every unit and weapon, with its portrait, the in-game stat tiles (HP, AP, MP,
  Armor, Dodge) and its loadout.
- Edit any stat, including points costs, AP, movement, health, armour, accuracy,
  range, ammo and traits. The original value is always shown next to yours.
- **Bulk edit:** change one stat on every entry in a filtered list, for example
  "all Ork units: Max Health × 150 %".
- Works in every game mode. **F10** toggles all edits on and off in game; **F9**
  reloads them.

**Army Painter** (opt-in)
- Repaints a faction **everywhere it appears**: battle (yours and the enemy's),
  army management and menus. Covers the 3D models and the unit portraits.
- **Off by default.** Enable *Army Painter in game* and Save. It only starts
  painting when a faction actually has custom colours or a scheme; a stat-only
  setup triggers no paint work at all.
- **Custom colours:** pick Primary (armour) and Secondary (trim). There's a
  colour picker, a paint palette and a live preview.
- **Ten chapter schemes for the Ultramarines models, each with its own badge.**
  They keep the brass, metal, eyes and plasma glow.

  | Scheme | Armour | Badge |
  |---|---|---|
  | Salamanders | deep green | drake head |
  | Space Wolves | blue-grey | wolf head |
  | Imperial Fists | yellow | fist |
  | White Scars | bone white | lightning bolt |
  | Dark Angels | dark green | winged sword |
  | Raven Guard | black | raven |
  | Iron Hands | gunmetal black | hand in a cog |
  | Black Templars | black | cross |
  | Crimson Fists | deep navy | fist |
  | Blood Ravens | blood red | winged blood drop |

- **Scheme Creator:** design your own scheme for any faction and share it as a
  small `.zip`.
- **Bake:** paint is prepared ahead of time, so armies appear painted instantly
  in game.

**Configurator app**
- Opens from the game, from Vortex, or from the Start menu. See below.
- Languages: English, Deutsch, Español, Français, 한국어, Polski,
  Português (Brasil), Русский, 简体中文 and 繁體中文. The language you pick also
  sets the unit and weapon names.
- Save while the game runs and the game reloads. The app confirms it has.

---

## Requirements

- Warhammer 40,000: Battlesector (Steam), version 1.7.7.
- **BepInEx Framework** (BepInEx 6, IL2CPP) mod.
- Windows 10 or 11. The configurator needs no .NET install.

## Installation

**Vortex (recommended)**
1. Install and enable **BepInEx Framework**, then start the game once.
2. Install **Warpstorm** and deploy.
3. Optional: update the *Warhammer 40,000: Battlesector* Vortex game extension to
   1.2.0. Warpstorm Configurator then appears under Dashboard → **Tools**.

**Manual**
1. Install BepInEx Framework and start the game once.
2. Extract the Warpstorm zip into the game folder, the one that contains
   `Warhammer 40K Battlesector.exe`. It only adds `BepInEx\plugins\Warpstorm\`.

> Don't also install the old standalone **Army Painter** mod. Warpstorm already
> contains it.

## Opening the configurator

Use any of these:
- **In game:** the small Warpstorm box in the top-left corner → **Open
  Configurator**, then Alt+Tab to it.
- **Vortex:** Dashboard → Tools → *Warpstorm Configurator*.
- **Start menu:** in the configurator, *Settings → Add to Start menu* (one time).
- **The file:** `<game folder>\BepInEx\plugins\Warpstorm\Warpstorm.Configurator.exe`

It finds the game folder by itself. If it doesn't, go to Settings → Browse….

---

## How to use

### Change stats
1. Open **Units** or **Weapons**. Search by name, or filter by faction, role, or
   ranged / melee.
2. Click an entry and type a new value next to any stat, or use **− / +**. An
   empty box means the game's own value. Use the reset buttons to undo one stat,
   one group or the whole entry.
3. A unit shows its **loadout**: click a weapon to edit it. A weapon shows the
   units it is **used by**. A weapon edit changes it for all of them.
4. **Bulk edit…** (above the list) applies set, multiply %, add or reset to
   every entry in the current list.
5. Press **Save** (Ctrl+S).

### Paint an army
1. Open **Army Painter**, switch **Army Painter in game** to **On**, then pick a
   faction.
2. Choose one of these:
   - **Custom colours:** click *Primary* or *Secondary* and pick a colour. The
     preview shows the result on that faction's units.
   - **A scheme pack:** select it under *Scheme*. The chapter schemes are listed
     under Ultramarines.
3. Press **Save**. The app pre-paints (bakes) the textures, which takes about 30
   seconds per faction. Then play: the army is painted as soon as it appears.

To go back to the original look, set *Scheme* to *Custom colours*, click *Reset
to default*, then Save.

### Make your own scheme
1. Army Painter → **Create your own scheme…**. To start from a pack, select it
   and click **Edit a copy**.
2. **Base faction:** the game faction whose models you repaint. Then give your
   scheme a name.
3. **Rule 1 (armour):** click **Pick colour**, then click the armour on an
   original portrait on the left. Choose the new colour, and the preview updates
   live.
4. **Rule 2 (highlights):** catches the bright armour edges. Add rules for trim
   or other parts. If parts don't change, raise *Colour match width*. If metal or
   skin changes too, raise *Ignore greys below*.
5. **Load model textures from the game** shows the result on the real 3D
   textures.
6. **Badge** (Ultramarines models): choose a built-in badge or your own PNG, a
   white shape on transparent, about 512 px.
7. **Save & use** applies it. **Export .zip…** lets you share it, and others
   install it with **Import scheme pack…**.

### Review and settings
- **Changes** lists everything that differs from the game, with unsaved items
  marked. You can remove single edits there.
- **Settings:** in-game hotkeys, toggles (stat edits on or off, the in-game box,
  Army Painter opt-in, auto-paint, approximate portrait recolour), painted
  texture size, and file locations.
- **Export / Import** (the ⋯ menu) shares your stat edits as JSON.

### In-game controls (changeable in Settings)

| Key | Action |
|---|---|
| **F10** | stat edits on / off |
| **F9** | reload config |
| **F1** | Army Painter window (adjust colours live, apply, show original paint) |

---

## Compatibility

- **No file conflicts.** Warpstorm only adds files under
  `BepInEx\plugins\Warpstorm\` and writes its settings under `BepInEx\config\`
  and `BepInEx\cache\`.
- Works with **The Great Crusade**, **Traditional Chinese Localization** and other
  data mods. If another mod changes a stat, Warpstorm's value wins for the stats
  you set.
- Army Painter paints by faction. Every Ultramarines model on the field gets the
  Ultramarines scheme, enemies included.
- The badge swap works on the Ultramarines models only. Other factions paint
  their symbol into the armour itself, so only their colours change. A few
  textures and the portraits keep the original symbol.

## Performance: what to expect from Army Painter

Army Painter is opt-in and lazy. Off by default, and with no custom colours it
does no scanning, texture work, portrait work or rendering — editing unit stats
alone triggers no paint work. When enabled, it paints the models while the game
is running. It does not replace
the game's files, so the game always loads its original textures first and
Army Painter swaps in the painted ones afterwards. Because of this:

- **Units can briefly show their original colours** when they first appear,
  for example at the start of a battle or when the army screen opens. They then
  switch to your scheme. This is normal.
- **You may see a short FPS drop** while a faction is painted for the first time
  in a session. Army Painter spreads the work over several frames to avoid a
  freeze, so with many units on screen the switch can take a few seconds.

Baking keeps this short. It runs automatically after every Save, so the textures
are already painted and only need to be loaded. Factions or textures the bake
can't reach are painted live the first time and then cached for later sessions.
If it still bothers you, a lower *Painted texture size* (Army Painter → Bake
textures) makes the switch faster.

There is no perfect fix for this yet. Removing the flash completely would mean
replacing the game's texture files, which brings back the file conflicts and
update breakage this mod avoids. If you have ideas or want to improve it,
you're welcome to. Comments and contributions are appreciated.

## Troubleshooting

- **Army Painter does nothing.** It is opt-in: switch *Army Painter in game* on,
  give a faction a non-default colour or a scheme, then Save.
- **Nothing changes.** Open `BepInEx\LogOutput.log`:
  - `Warpstorm ON … N edit(s) applied` means the stat edits are active.
  - `[ArmyPainter] scene: …` reports per faction how many model parts were
    painted.
  - No `[Warpstorm]` lines at all means the mod isn't deployed. Redeploy it in
    Vortex.
- **Stats don't change in the current battle.** New values apply to units
  created after the reload. Restart the battle.
- **The configurator doesn't open.** See `warpstorm-configurator.log` next to the
  EXE.
- **Windows SmartScreen / antivirus warning.** The app is not code-signed. Choose
  *More info → Run anyway*. You can compare the file with the hashes below.
- **Start over with paint:** Army Painter → *Clear baked textures*. Deleting the
  folder `BepInEx\cache\warpstorm` is also safe.

## Uninstall

Remove the mod in Vortex, or delete `BepInEx\plugins\Warpstorm\`. To also remove
your settings, delete these:
- `BepInEx\config\warpstorm\`
- `BepInEx\config\com.crystalmods.warpstorm.cfg`
- `BepInEx\config\com.crystalmods.armypainter.cfg`
- `BepInEx\cache\warpstorm\`

---

## Files and hashes (1.1.0)

| File | SHA-256 |
|---|---|
| `warpstorm-v1.1.0.zip` | `b4578c21fa0cfa316bc49e28010676f59e655ec4add1c69b1b03b96817a34373` |
| `Warpstorm.dll` | `293015c2093fd9d4bc1ca4bb4fc94cfc5a4dd8423e36fcf50c8222b5476dc10b` |
| `Warpstorm.Configurator.exe` | `65bd6f0a712f27a979076e42731511fdf3eb849b265eead1a7fbcc83b8edc6d1` |

The chapter schemes are already inside the main zip. They are also available as
separate `scheme-<chapter>-v<version>.zip` files for sharing.

## Credits

- Unit and weapon data, names in ten languages and portraits come from
  BattleSector Tools.
- Barlow typeface (SIL OFL 1.1) and Material Design Icons (Apache 2.0).
- Built with Avalonia, AssetsTools.NET and BCnEncoder.Net.

Fan-made. Not affiliated with Black Lab Games or Games Workshop. Warhammer 40,000
and the chapter names are trademarks of Games Workshop. The badges are original
stencil drawings.

## Changelog

**1.1.0:** Army Painter is now opt-in and lazy; stat-only setups do no paint work
in game. **1.0.0:** first public release. The full list is on the Changelog tab.
