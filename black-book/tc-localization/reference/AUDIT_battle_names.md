# Audit: historical manual overrides for `LevelConfig.Battle.Name`

> Generated during the v1.1.0 cleanup. Evidence for deciding whether to keep,
> discard, or redo these 183 edits.

## What happened

The game's own Simplified Chinese localisation machine-translated the
English → SC step badly for battle scene names. **chort**, a Slavic household
spirit, became `雠特` — but 雠 means "feud / enmity", so the name is garbled.

A previous session replaced those 183 values by hand. The audit question was:
*were those replacements an improvement?*

## Result: they are not

All **183** edits follow the same rule: `LevelConfig.Battle.Name` was set to
**the location's own `Name`**. The enemy identity was deleted entirely.

| | English source | Game's SC | Plain `s2twp` | The hand-edit |
|---|---|---|---|---|
| `Week1Day1Kusheva` | Samovar Chort | 茶炊雠特 | 茶炊讎特 | **庫舍瓦村** (the village) |
| `Week1Day3EastBridge` | Demon and Sinner | 魔鬼和罪人 | 魔鬼和罪人 | **東橋** (the bridge) |
| `Week1Day3IkotaChurch` | Proshka-Ikota | 伊廓卡普罗什卡 | 伊廓卡普羅什卡 | **主顯聖容教堂** (the church) |
| `Week1Day1ChudForest` | Chud' chorts | 楚德的雠特 | 楚德的讎特 | **楚德森林** (the forest) |
| `TestBattle` | Test Battle | 测试对战 | 測試對戰 | **對抗魔鬼** ("fight the demon") |
| `Week1Day1Kachevo` | Demons at the Ridge | 山梁上的魔鬼 | 山樑上的魔鬼 | **卡切沃湖** (the lake) |

The `s2twp` column is a faithful conversion of the game's own translation and
already reads correctly. The hand-edits are not translations of the English at
all — they replace one noun phrase with an unrelated one. In several cases
(`TestBattle` → 對抗魔鬼) the new value is *less* accurate than what it
replaced.

**Recommendation: discard all 183.** The plain OpenCC output is better in every
case examined. Nothing from this batch was carried into `overrides.tsv`.

## The 8 remaining historical edits

These were separate from the battle-name batch.

| File | Key | Hand-edit | `s2twp` | Verdict |
|---|---|---|---|---|
| `Abilities/TOMASHIHA` | `Name` | 託馬希哈 | 托馬希哈 | **Hand-edit is wrong.** 托 is a surname particle; s2twp is correct. |
| `Week1Day2BathInterior` | `Name` | 班尼亞裡面 | 班尼亞里面 | Stylistic only; `裡面` is more Taiwan-idiomatic. |
| `Week1Day6Kulyash` | `Name` | 庫裡亞索夫農莊 | 庫里亞索夫農莊 | Inconsistent with the transliteration used elsewhere. |
| `Week1Day6Kulyash` | `Description` | …幹得風生水起… | …干得風生水起… | **Hand-edit is better.** `干` here means "do/work" → `幹`. |
| `Week1Day7BrideHouse` | `LongQuestDescr` | 為瞭解 | 為了解 | Stylistic; both acceptable in TC. |
| `Week1Day7OldChapel` | `Description` | 方圓幾裡 | 方圓几里 | **Hand-edit is wrong.** 里程 uses 里. |
| `Week5Day1OldBaths` | `Description` | 科裡亞 | 科里亞 | Same transliteration as `Week1Day6Kulyash`; inconsistent. |
| `Week1Day2KrivoyLog` | `Description` | — | — | Identical; listed because it appeared in the diff. |

Four of the eight were **double-conversion damage**: a second `s2twp` pass.
`s2twp` is not idempotent, and `scripts/gate_simplified.py` now exists
specifically to catch that class of error.

**Recommendation:** discard all eight except the `幹得風生水起` fix, which is a
genuine Mainland/Taiwan difference that OpenCC's dictionary misses.

## Open issue: `雠特` / `讎特`

Both forms are wrong for the spirit name. 讎 literally means "hatred /
enmity"; the demon is transliterated from Russian *чорт*. `楚特` is the
better transliteration.

This affects **113 strings across 91 files** — every mention of a chort. It is
a single global substitution, so it is a candidate for a scripted rule rather
than 113 manual overrides. Recorded in the README roadmap; not yet done.