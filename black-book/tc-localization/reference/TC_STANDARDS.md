# Traditional Chinese Localization Standards

Guidelines for Black Book TC translation.

---

## Character Encoding & Text Processing

- **Encoding**: UTF-8 (no BOM)
- **Line endings**: LF (`\n`), not CRLF
- **Character set**: CJK Unified Ideographs (U+4E00–U+9FFF)
- **Normalization**: NFKC (Compatibility Composition)

---

## Punctuation

### Chinese Punctuation (Preferred)

| Mark | Unicode | Name | Usage |
|------|---------|------|-------|
| 。 | U+3002 | Ideographic Full Stop | End of sentence |
| ， | U+FF0C | Fullwidth Comma | List items, clause separation |
| 、 | U+3001 | Ideographic Comma | Enumeration within lists |
| ； | U+FF1B | Fullwidth Semicolon | Clause separation |
| ： | U+FF1A | Fullwidth Colon | Explanation, list intro |
| ？ | U+FF1F | Fullwidth Question Mark | Questions |
| ！ | U+FF01 | Fullwidth Exclamation Mark | Exclamation |
| 「」 | U+300C / U+300D | Corner Brackets | Dialog, quotes |
| 『』 | U+300E / U+300F | White Corner Brackets | Nested quotes |
| （） | U+FF08 / U+FF09 | Fullwidth Parentheses | Parenthetical remarks |

### Spacing

- **No spaces** between Chinese characters and punctuation: `說話。` (not `說話 。`)
- **Space before English**: `中文 English 中文`
- **Space after punctuation in enumerations**: `一、 Item one 二、 Item two`

---

## Capitalization & Typography

- **Game titles, brand names**: Keep original English
  - Example: ✓ "Black Book" (not "黑冊" unless officially)
  - Example: ✓ "OpenCC" (not "開放轉換")
- **Proper nouns (character/place names)**: Keep original unless official TC version exists
- **Acronyms**: Keep as-is
  - Example: ✓ "NPC" (not "非玩家角色")

---

## Grammar & Syntax

### Verb Tenses
- Chinese has no tense inflection; use context words instead
- Past: `已經...` / `曾經...` / verb + `了`
- Future: `將會...` / `即將...` / verb + `會`
- Progressive: verb + `中` / `著`

**Examples**:
- "has defeated" → `已經擊敗`
- "will appear" → `將會出現`
- "is attacking" → `正在攻擊`

### Formality
- **Neutral/Polite** (preferred for UI/dialog): -您 (formal you), verb + `了` (completed action)
- **Casual**: -你, present tense
- Keep consistency within the same context (e.g., all NPC dialog in same register)

### Negation
- `不` (negative fact/logic) vs. `沒` (negative past action)
  - "Do not attack" → `不要攻擊` (imperative)
  - "Did not attack" → `沒有攻擊` (past)

---

## Common Issues & Fixes

| ❌ Wrong | ✓ Correct | Reason |
|---------|----------|--------|
| 選擇 角色 | 選擇角色 | No space between Chinese words |
| 使用 Spell | 使用Spell | No space before English |
| 法術。 | 法術。 | Fullwidth period, not ASCII `.` |
| 菜单 | 菜單 | 菜单 is Simplified; 菜單 is Traditional |
| 獲得+50 Gold | 獲得+50黃金 or 獲得+50 Gold | Either translate "Gold" or keep English + space |
| 角色名: Bob | 角色名：Bob | Use fullwidth colon `:` → `：` |

---

## Translation Quality Checklist

Before submitting translations, verify:

- [ ] All text is Traditional Chinese (no Simplified characters)
- [ ] Punctuation is fullwidth Chinese (not ASCII)
- [ ] Line endings are LF only
- [ ] No trailing whitespace
- [ ] Terminology is consistent with `TERMINOLOGY.md`
- [ ] Grammar and tone match the original context
- [ ] No untranslated English (unless intentional brand names)
- [ ] Character count reasonable (Chinese is ~30% more compact than English)

---

## Resources

- **Unicode Character Reference**: https://unicode-table.com
- **OpenCC**: https://github.com/BYVoid/OpenCC
- **Google Noto Fonts CJK**: https://fonts.google.com/noto/specimen/Noto+Sans+TC
- **TC Standards (Taiwan)**: https://www.cns11643.gov.tw/ (Official CNS standard)

---

*Last updated: 2026-06-10*
