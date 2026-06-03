# Gameplay Screenshot Analysis — Remaining English Text

**Analysis Date:** 2026-06-03  
**Source:** 8 gameplay screenshots from post-deployment testing  
**Goal:** Identify remaining untranslated text for incremental deployment

---

## Screenshot 1: Main Menu — Campaign Selection

| English Text | Type | Priority | Notes |
|---|---|---|---|
| Campaign: new | UI Label | HIGH | Game state indicator |
| Current story: Sordland | UI Label | HIGH | Campaign name display |
| Date: Jun 3, 2026, 10:58 PM | UI Label | MEDIUM | Date format (may need localization) |

**Category:** Menu/Campaign Selection

---

## Screenshot 2-3: Options Menu

| English Text | Type | Count | Priority | Notes |
|---|---|---|---|---|
| OPTIONS | Menu Title | 1 | HIGH | Top-level menu label |
| Borderless | Setting Option | 1 | HIGH | Graphics mode option |
| High | Setting Value | 5 | HIGH | Graphics quality level |
| On | Setting Value | 3 | HIGH | Toggle on/off state |
| SSAO | Graphics Option | 2 | MEDIUM | Screen Space Ambient Occlusion (technical term, could stay English) |
| Default | Setting Value | 1 | MEDIUM | Default preset |

**Category:** Settings/Options Menu

---

## Screenshot 4: Collections (Story Packs)

| English Text | Type | Count | Priority | Notes |
|---|---|---|---|---|
| COLLECTIONS | Menu Title | 1 | HIGH | Top-level menu label |
| All Story Packs | Section Header | 1 | HIGH | Category label |
| UNKNOWN | Pack Name | 5 | MEDIUM | Unknown/Locked pack names |
| Locked | Status Label | 5 | HIGH | Pack lock status |
| Unlocked | Status Label | 1 | HIGH | Pack unlock status |
| Visit the store to purchase this item. | Instruction Text | 1 | MEDIUM | Store prompt |

**Category:** Collections/Store Menu

---

## Screenshot 5: Campaign Gameplay — Character Profile

| English Text | Type | Priority | Notes |
|---|---|---|---|
| UNSTABLE | Status Label | HIGH | Stability status indicator |
| Ciara Walda | Character Name | MEDIUM | Proper name (could stay English or transliterate) |
| [Character Biography Paragraph] | Game Content | HIGH | Long character description paragraph |

**Character Biography Text (Full):**
```
"is an academician and politician who serves as the Minister of Education, 
Technology & Research of Sordland. She became a member of the United Sordland 
Party before the 1952 elections. Prior to becoming a minister, she was elected 
and served as an independent MP."
```

**Category:** Campaign Game Content / Character Data

---

## Screenshot 6: Cabinet Screen

| English Text | Type | Priority | Notes |
|---|---|---|---|
| Cabinet | Screen Title | HIGH | Government cabinet interface label |
| PETR VECTERN | Character Name | MEDIUM | Cabinet member name (proper noun) |
| Vice President | Government Title | HIGH | Cabinet position |
| LUCIAN GALADE | Character Name | MEDIUM | Cabinet member name |
| Chief of Staff | Government Title | HIGH | Cabinet position |
| JOSEF LANCEA | Character Name | MEDIUM | Cabinet member name |
| Defense Minister | Government Title | HIGH | Cabinet position |
| SYMON HOLL | Character Name | MEDIUM | Cabinet member name |
| Economy Minister | Government Title | HIGH | Cabinet position |
| GUS MANGER | Character Name | MEDIUM | Cabinet member name |
| Agriculture & Rural Dev. Minister | Government Title | HIGH | Cabinet position |
| DEIVID WISCI | Character Name | MEDIUM | Cabinet member name |
| Foreign Affairs & Trade Minister | Government Title | HIGH | Cabinet position |

**Category:** Government/Cabinet System

---

## Screenshot 7: Military Policy Screen

| English Text | Type | Priority | Notes |
|---|---|---|---|
| Compulsory Military Service | Law/Policy Title | HIGH | Policy name (appears 2x) |
| Sordish General Staff | Organization Name | HIGH | Military organization |
| Gendarmerie under Defense | Organization Name | HIGH | Government organization |
| [Policy Description Paragraph] | Game Content | HIGH | Policy details paragraph |

**Policy Description Text (Full):**
```
"In Sordland, the military operates as a conscripted force, where the duty of 
military service falls upon males upon reaching the age of 18. This mandatory 
conscription ensures a consistent and capable pool of personnel to uphold the 
nation's defense and security, strengthening the overall resilience and 
readiness of the military."
```

**Category:** Campaign Game Content / Policy System

---

## Screenshot 8: Diary/Journal Screen

| English Text | Type | Priority | Notes |
|---|---|---|---|
| TURN 1 | Metadata Label | MEDIUM | Turn counter |
| [Journal Entry 1] | Game Content | HIGH | Campaign diary text |
| [Journal Entry 2] | Game Content | HIGH | Campaign diary text |

**Journal Entry Text (Full):**
```
Entry 1: "I declared my intention to work with the reformists for the 
constitutional reform."

Entry 2: "We have won the 1953 election. A new chapter begins for Sordland."
```

**Category:** Campaign Game Content / Diary

---

## Summary by Category

### HIGH Priority (Campaign-Critical Content)

1. **UI Labels & Status** (8 items)
   - Campaign: new
   - Current story: Sordland
   - OPTIONS
   - UNSTABLE
   - Cabinet
   - Compulsory Military Service (x2)

2. **Government/Policy Titles** (7 items)
   - Vice President
   - Chief of Staff
   - Defense Minister
   - Economy Minister
   - Agriculture & Rural Dev. Minister
   - Foreign Affairs & Trade Minister
   - Sordish General Staff
   - Gendarmerie under Defense

3. **Game Content Paragraphs** (4 items)
   - Character biography (Ciara Walda)
   - Military policy description
   - Journal entries (x2)

4. **Collection/Store Labels** (4 items)
   - All Story Packs
   - Locked (x5)
   - Unlocked
   - Visit the store to purchase this item.

### MEDIUM Priority (Non-Critical UI)

1. **Settings & Graphics** (9 items)
   - Borderless
   - High (x5)
   - On (x3)
   - Default
   - SSAO (x2)

2. **Character/Organization Names** (6 items)
   - Ciara Walda
   - PETR VECTERN
   - LUCIAN GALADE
   - JOSEF LANCEA
   - SYMON HOLL
   - GUS MANGER
   - DEIVID WISCI

3. **Metadata** (2 items)
   - Date format
   - TURN 1

---

## Translation Strategy

### Phase 1: High-Priority Campaign Content (Immediate)

Focus on game content that affects player experience:
- Character/policy descriptions (paragraphs)
- Government titles and positions
- Campaign UI labels

**Estimated entries:** ~30-40

### Phase 2: UI/UX Translations (Secondary)

Focus on menus and system UI:
- Options menu labels
- Collections/store interface
- Status indicators

**Estimated entries:** ~20-30

### Phase 3: Character/Organization Names (Optional)

Decide on naming convention:
- Keep English (faster)
- Transliterate to Traditional Chinese (authentic but time-consuming)
- Hybrid approach (character names in English, titles translated)

---

## Implementation Notes

1. **Paragraph Content:** Long narrative paragraphs may not be in source.jsonl; they may require:
   - Direct JSON string extraction from entity bundle
   - Additional translation project creation
   - Manual insertion via override files

2. **Date/Format Localization:** "Date: Jun 3, 2026, 10:58 PM" may need:
   - Month name localization (六月 for June)
   - Time format adjustment (24-hour vs. 12-hour)

3. **Character Names:** Determine policy:
   - Save time: Keep all names in English
   - Authentic: Transliterate to Chinese (e.g., "Ciara Walda" → "琪亞拉·瓦爾達")

4. **Ministry/Government Titles:** High priority for game immersion:
   - "Defense Minister" → "國防部長"
   - "Economy Minister" → "經濟部長"
   - etc.

---

## Next Steps

1. Cross-reference remaining English text with source.jsonl / state.jsonl
2. Identify which entries are already in translation project vs. missing
3. Create targeted translation batch for missing entries (avoid duplicate API calls)
4. Deploy incrementally with testing
5. Iterate based on gameplay feedback
