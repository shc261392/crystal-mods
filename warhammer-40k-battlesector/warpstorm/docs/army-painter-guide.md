# Army Painter guide — paint your own army

Army Painter repaints a faction everywhere it appears. That means the 3D models
in battle (both sides), army management, menus, and the unit portraits. You can
do it in three ways:

| Way | Effort | Result |
|---|---|---|
| **Custom colours**: pick Primary / Secondary | 10 s | Automatic recolour; fine for quick looks |
| **Scheme pack**: pick one, e.g. *Salamanders* | 10 s | Hand-tuned colours + chapter badge |
| **Scheme Creator**: make your own pack | 5–15 min | Exactly your scheme, shareable as a .zip |

## Turn it on first (opt-in)

Army Painter does no work in game by default. Open *Army Painter*, switch
**Army Painter in game** to **On**, then Save. That is the one-time opt-in.

Even after that, the plugin only paints factions whose colours differ from the
game's defaults or that use a scheme pack. Until then it does not scan the scene,
read textures or touch portraits. If you only edit unit stats, leave Army
Painter off: no paint work happens at all.

## Built-in chapter packs (Ultramarines models)

| Pack | Armour | Badge |
|---|---|---|
| Salamanders | deep green | drake head |
| Space Wolves | Fenrisian blue-grey | wolf head |
| Imperial Fists | yellow | clenched fist |
| White Scars | bone white | lightning bolt |
| Dark Angels | Caliban dark green | winged sword |
| Raven Guard | black | raven |
| Iron Hands | gunmetal black | hand in a cog |
| Black Templars | pitch black | cross pattée |
| Crimson Fists | deep navy | clenched fist |
| Blood Ravens | blood red | winged blood drop |

All of them keep the brass, metal, red eyes and plasma glow.

**To use one:** open *Army Painter*, make sure **Army Painter in game** is
**On**, select *Ultramarines*, choose the pack under *Scheme*, then press
**Save**. The configurator bakes the textures, which takes about 30 s. Start the
game, or carry on playing: a running game reloads the pack by itself.

## Make your own (Scheme Creator)

1. **Open it.** Army Painter → **Create your own scheme…**. To start from an
   existing pack, select it under *Scheme* and click **Edit a copy**.
2. **Basics.** Choose the **base faction**: the game faction whose models get
   repainted. Then give the scheme a name, for example *Iron Lords* on
   Ultramarines models.
3. **Rule 1: main armour.** Click **Pick colour**. Then click the armour on one
   of the **original** portraits on the left of the preview. Rule 1 now matches
   that paint colour. Choose the new colour in the colour box next to it, and
   the preview on the right updates live.
4. **Rule 2: highlights.** The bright, washed-out edges of the armour have low
   saturation. Point rule 2 at them the same way. Its *Ignore darker than* is
   preset to 0.45, so it only touches the highlights.
5. **More rules.** Click **Add rule** for trim, cloth or anything else. When
   several rules match a pixel, the strongest match wins.
   - Parts stay unchanged? Raise **Colour match width**.
   - Metal, skin or glow change too? Raise **Ignore greys below**, or lower the
     width.
   - Too bright or too flat? Use **Brightness** and **Saturation**.
6. **Check the 3D result.** Click **Load model textures from the game**. You see
   your rules on the real model textures, which the game files supply read-only.
7. **Badge (optional, Ultramarines models).** Pick a built-in badge or **My own
   PNG…**. The PNG should be a **white shape on a transparent background**,
   square, about 512 px. It replaces the chapter symbol on the armour; the squad
   markings stay.
8. **Save & use** installs the pack and selects it. Press **Save** at the top to
   apply it to the game and bake its textures.
9. **Share.** **Export .zip…** gives you a small file with `scheme.json` and,
   if you set one, `badge.png`. Others install it with **Import scheme pack…**.

## What a pack is

```
my-scheme/
  scheme.json     the recipe: base faction, colour rules, optional badge
  badge.png       optional chapter badge (white on transparent)
  portraits/*.png optional pre-rendered portraits (built-in packs only)
```

Without `portraits/`, the game applies the pack's rules to its own portrait
images, at their native resolution. See [`../schemes/README.md`](../schemes/README.md)
for every `scheme.json` field.

### How a rule works

A rule selects pixels whose **hue** lies within *hue ± width* degrees,
softened by a further *edge softness*. It skips pixels below *Ignore greys*
saturation and outside the brightness range. Selected pixels get the **target
colour's hue**. Their saturation and brightness are scaled by
*target ÷ original average*, so the baked shading, scratches and weathering
survive. That is also why black, white and grey targets work.

## Limits

- The badge swap needs a separate symbol atlas. Only the **Ultramarines** models
  have one (`ULT_Logo_D`). Other factions paint their symbol into the armour,
  so only their colours change.
- A few Ultramarines textures also carry the symbol painted into the armour
  itself (for example a shoulder pad), and the portraits show it too. Those keep
  the original symbol.
- Army Painter paints by **faction**: every Ultramarines model on the field,
  yours or the enemy's, gets the scheme.

## Advanced: command line

For pack authors, the same tools as the built-in packs:

```bash
dotnet build tools/SchemeBuilder -c Release
B=tools/SchemeBuilder/bin/Release/net10.0/SchemeBuilder.dll
dotnet $B sheet    schemes/my-scheme review.png        # original vs scheme, all portraits
dotnet $B overview review.png schemes/a schemes/b       # one row per pack
dotnet $B build    schemes/my-scheme out/my-scheme      # pre-render portraits into a pack
uv run --no-project --with pillow python schemes/make-badges.py --sheet badges.png
```
