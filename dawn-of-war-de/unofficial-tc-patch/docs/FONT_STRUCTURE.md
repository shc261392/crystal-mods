# Dawn of War DE Font Structure Documentation

## Overview
Dawn of War DE uses `.fnt` files to define font rendering properties. Each file specifies different font sizes for various screen resolutions.

## Font File Structure

### Resolution Breakpoints
The game adjusts font sizes based on horizontal resolution:

| Property | Resolution Range | Notes |
|----------|-----------------|-------|
| `size640` | ≤ 640×480 | Lowest supported resolution |
| `size800` | 800×600 | Optional, not all fonts define this |
| `size1024` | 1024×768 | Standard definition |
| `size1280` | 1280×1024 | HD resolution |
| `size1600` | ≥ 1600×1200 | Full HD and above |
| `sizeDefault` | Fallback | Used if no matching resolution found |

### FNT File Format
```lua
font = {
    type = "FreeType2";
    name = "Display Name";
    file = "FontFile.ttf";
    
    sizeDefault = 14;  -- Fallback size
    size640 = 14;      -- 640×480
    size800 = 16;      -- 800×600 (optional)
    size1024 = 18;     -- 1024×768
    size1280 = 20;     -- 1280×1024
    size1600 = 24;     -- 1600×1200+
    
    spaceChar = " ";
    missingChar = "?";
}
```

## Vanilla Chinese Locale Font Sizes

### albertus extra bold12.fnt
- **Font**: NotoSansTC-Medium.ttf
- **Sizes**: 11 → 11 → 11 → 12 → 14 → 16

### albertus extra bold14.fnt
- **Font**: NotoSansTC-Medium.ttf
- **Sizes**: 12 → 12 → 12 → 14 → 16 → 18

### albertus extra bold16.fnt
- **Font**: NotoSansTC-Regular.ttf
- **Sizes**: 14 → 14 → (no 800) → 18 → 20 → 24

### albertus extra bold20.fnt
- **Font**: NotoSansTC-Bold.TTF
- **Sizes**: 20 → 20 → (no 800) → 24 → 28 → 34

### engravers old english mt30.fnt
- **Font**: NotoSerifTC-Bold.ttf (decorative title font)
- **Sizes**: 20 → 20 → 24 → 28 → 36 → 48

### gillsans_11.fnt
- **Font**: NotoSansTC-Regular.ttf
- **Sizes**: 10 → 10 → 11 → 12 → 14 → 16

### gillsans_11b.fnt
- **Font**: NotoSansTC-Bold.ttf
- **Sizes**: 10 → 10 → 10 → 12 → 14 → 16

### gillsans_16.fnt
- **Font**: NotoSansTC-Regular.ttf
- **Sizes**: 14 → 14 → 14 → 18 → 20 → 28

### gillsans_bold_16.fnt
- **Font**: NotoSansTC-Regular.ttf
- **Sizes**: 11 → 11 → 12 → 14 → 16 → 18

### notosans medium 16.fnt
- **Font**: NotoSans-Medium-English.TTF (Latin characters)
- **Sizes**: 16 → 16 → (no 800) → 20 → 24 → 30

### notosans_m_16_xc.fnt
- **Font**: NotoSans_ExtraCondensed-Medium.TTF
- **Sizes**: 14 → 14 → 16 → 18 → 20 → 24

### quorum medium bold13.fnt
- **Font**: NotoSansTC-Bold.ttf
- **Sizes**: 9 → 9 → 11 → 12 → 14 → 16

### quorum medium bold16.fnt
- **Font**: NotoSansTC-Bold.ttf
- **Sizes**: 16 → 16 → 18 → 20 → 24 → 28

## Size Adjustment Pattern

When increasing font sizes by N points:
- Apply +N to ALL resolution sizes (sizeDefault, size640, size800, size1024, size1280, size1600)
- Preserve resolution entries that exist (some files omit size800)
- Do NOT modify files without size* entries

## Font Usage Notes

### Primary UI Fonts
- **gillsans_16.fnt**: Main UI text, menus
- **notosans medium 16.fnt**: Latin character fallback
- **albertus extra bold series**: Headers, buttons

### Decorative Fonts
- **engravers old english mt30.fnt**: Campaign titles, dramatic text
- Uses Noto Serif TC Bold (serif font)

### Compact Fonts
- **notosans_m_16_xc.fnt**: Extra condensed for space-constrained UI
- **quorum medium bold13.fnt**: Small labels

## Line Height

**Note**: The game does NOT expose line-height configuration in .fnt files. Line spacing is calculated automatically by the FreeType2 renderer based on the font metrics embedded in the TTF file itself.

If line spacing adjustment is needed, it would require:
1. Modifying the TTF font files (advanced)
2. Engine-level changes (impossible without source)

## Related Files

- **Font textures**: `art/ui/swf/font*.gfx` — Pre-rendered glyph atlases
- **Font files**: `font/*.ttf` — TrueType font files (Noto Sans TC, Noto Serif TC)
- **SGA packing**: See `SGA_REPACKING_GUIDE.md` for compression settings

## Script Usage

To adjust all font sizes by +6:
```bash
python3 scripts/adjust_font_sizes.py --root data/ --increase 6
```

To preview changes without modifying files:
```bash
python3 scripts/adjust_font_sizes.py --root data/ --increase 6 --dry-run
```
