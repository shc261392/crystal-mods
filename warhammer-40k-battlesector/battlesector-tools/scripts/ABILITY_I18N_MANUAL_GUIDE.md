# Manual Ability Translation Guide

If you have translations from community sources, official game localization, or manual translation work, you can create or update `ability-i18n.json` manually.

## File Structure

See `ability-i18n.example.json` for a complete example. The file has three main sections:

### 1. Metadata

```json
{
  "generatedAt": "2026-07-04T03:00:00.000Z",
  "source": "Manual translation from community contributors",
  "stats": { ... }
}
```

### 2. Stats (Summary)

```json
"stats": {
  "totalAbilities": 62,
  "matched": 40,
  "exact": 40,
  "fuzzy": 0,
  "manual": 0,
  "needsReview": 22
}
```

Update these to reflect your progress.

### 3. Abilities Array

Each ability entry:

```json
{
  "abilityId": 1,
  "textId": null,  // Can be null if unknown
  "locales": {
    "en": {
      "title": "Jump Pack",
      "description": "Affects casting unit\n\n+2 Movement\n..."
    },
    "zh-CN": {
      "title": "跳跃背包",
      "description": "影响施法单位\n\n+2 移动\n..."
    }
  },
  "confidence": "manual",
  "notes": "Translated by community contributor"
}
```

## Step-by-Step Manual Creation

### Step 1: Start with English Source

Copy ability data from `ability-overrides.source.json`:

```bash
node -e "
  const source = require('./src/data/ability-overrides.source.json');
  const abilities = Object.entries(source.entries).map(([id, a]) => ({
    abilityId: parseInt(id),
    textId: null,
    locales: {
      en: {
        title: a.title,
        description: a.description
      }
    },
    confidence: 'manual',
    notes: 'Awaiting translation'
  }));
  console.log(JSON.stringify({ abilities }, null, 2));
" > .copilot_workspace/ability-i18n-template.json
```

### Step 2: Add Your Translations

Open `.copilot_workspace/ability-i18n-template.json` and add translations:

```json
{
  "abilityId": 1,
  "textId": null,
  "locales": {
    "en": {
      "title": "Jump Pack",
      "description": "Affects casting unit\n\n+2 Movement\n-20% Ranged Accuracy\nIgnores movement penalties from terrain\nExpires in 1 Turn\nWill not provoke pistol reactions when charging"
    },
    "zh-TW": {
      "title": "跳躍背包",
      "description": "影響施法單位\n\n+2 移動\n-20% 遠程精度\n忽略地形移動懲罰\n1回合後失效\n衝鋒時不會引發手槍反應"
    },
    "de": {
      "title": "Sprungpaket",
      "description": "Betrifft die wirkende Einheit\n\n+2 Bewegung\n-20% Fernkampfgenauigkeit\nIgnoriert Bewegungsstrafen durch Gelände\nLäuft nach 1 Runde ab\nProvoziert keine Pistolenreaktionen beim Angriff"
    }
  },
  "confidence": "manual",
  "notes": "Community translation - verified"
}
```

### Step 3: Add Metadata

Wrap the abilities array with metadata:

```json
{
  "generatedAt": "2026-07-04T03:00:00.000Z",
  "source": "Manual translation",
  "stats": {
    "totalAbilities": 62,
    "matched": 10,
    "exact": 0,
    "fuzzy": 0,
    "manual": 10,
    "needsReview": 52
  },
  "abilities": [ ... ]
}
```

### Step 4: Validate

Check the file against the schema:

```bash
# Using Node.js (if Ajv installed)
node -e "
  const Ajv = require('ajv');
  const schema = require('./src/data/ability-i18n.schema.json');
  const data = require('./src/data/ability-i18n.json');
  const ajv = new Ajv();
  const valid = ajv.validate(schema, data);
  console.log(valid ? 'Valid!' : JSON.stringify(ajv.errors, null, 2));
"
```

Or use an online JSON Schema validator.

### Step 5: Move to Production

```bash
cp .copilot_workspace/ability-i18n-template.json src/data/ability-i18n.json
```

## Translation Guidelines

### Formatting Rules

1. **Preserve line breaks**: Use `\n\n` for paragraph breaks
2. **Keep structure**: Match English formatting (headings, lists, etc.)
3. **Stat notation**: Keep format like `+20%`, `-15`, `+2 Movement`
4. **Duration**: Translate "Expires in X Turn(s)" consistently

### Example Translations

#### Active Ability (Multi-paragraph)

```
Affects casting unit

+2 Movement
-20% Ranged Accuracy
Ignores movement penalties from terrain
Expires in 1 Turn
Will not provoke pistol reactions when charging
```

Structure:
- **Line 1**: Target (Affects ...)
- **Line 2**: Empty (paragraph break)
- **Lines 3-7**: Effects list
- **Line 8**: Duration
- **Line 9+**: Special rules

#### Passive Ability (Single block)

```
+10% Melee Accuracy
+10% Ranged Accuracy
```

No target line, just effects.

### Common Phrases

| English | Chinese (Simplified) | Chinese (Traditional) | German | French |
|---------|---------------------|----------------------|--------|---------|
| Affects casting unit | 影响施法单位 | 影響施法單位 | Betrifft die wirkende Einheit | Affecte l'unité de lancement |
| Affects all allies within | 影响范围内所有盟友 | 影響範圍內所有盟友 | Betrifft alle Verbündeten innerhalb | Affecte tous les alliés dans |
| Expires in X Turn | X回合后失效 | X回合後失效 | Läuft nach X Runde ab | Expire après X tour |
| Ignores | 忽略 | 忽略 | Ignoriert | Ignore |

## Merging with Auto-Generated Data

If you have manual translations AND auto-generated data:

```bash
node -e "
  const manual = require('./path/to/manual.json');
  const auto = require('./src/data/ability-i18n.json');
  
  const merged = { ...auto };
  merged.abilities = auto.abilities.map(autoAbility => {
    const manualAbility = manual.abilities.find(m => m.abilityId === autoAbility.abilityId);
    if (!manualAbility) return autoAbility;
    
    return {
      ...autoAbility,
      locales: {
        ...autoAbility.locales,
        ...manualAbility.locales
      },
      notes: [autoAbility.notes, manualAbility.notes].filter(Boolean).join('; ')
    };
  });
  
  console.log(JSON.stringify(merged, null, 2));
" > src/data/ability-i18n.merged.json
```

## Quality Checklist

Before finalizing translations:

- [ ] All abilities have at least English text
- [ ] Line breaks preserved (`\n\n` for paragraphs)
- [ ] Stat notation consistent (`+X%`, `+X`, `-X`)
- [ ] Duration phrases translated consistently
- [ ] Special rules (like pistol reactions) translated accurately
- [ ] No missing or placeholder text (e.g., `{0}`, `{1}`)
- [ ] File validates against schema
- [ ] Stats object reflects actual counts

## Testing Translations

1. **Copy to dev environment**:
   ```bash
   cp src/data/ability-i18n.json src/data/ability-i18n.backup.json
   # Make changes
   ```

2. **Update i18n loader** (if not done yet):
   ```typescript
   // src/scripts/i18n.ts
   import abilityI18n from '../data/ability-i18n.json';
   ```

3. **Build and test**:
   ```bash
   pnpm build
   pnpm preview
   ```

4. **Verify in browser**:
   - Switch languages
   - Check ability cards
   - Look for missing translations (should fallback to English)

## Contributing Translations

If you create quality translations:

1. Document your sources
2. Add notes in the JSON about verification
3. Submit a PR with your translations
4. Include locale stats in the commit message

Example commit:
```
feat(i18n): add German ability translations

- 45 abilities translated
- All exact matches verified against game text
- Community reviewed by native speakers
```

## Support

- **Schema validation errors**: Check `ability-i18n.schema.json` for required fields
- **Formatting questions**: See `ability-i18n.example.json` for reference
- **Translation quality**: Compare with in-game text or official localizations
- **Technical issues**: Check main README or open an issue
