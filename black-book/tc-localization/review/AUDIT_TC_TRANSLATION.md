# Black Book — Traditional Chinese translation audit (EN vs TC)

**READ-ONLY audit.** No mod/game file was modified. All scratch artefacts live in
`/home/shado/crystal-mods/.copilot_workspace/bb-tc-audit/`.

## 0. What was audited and how

| source | count | how paired |
|---|---|---|
| Config EN (`Config/**/config_en.yaml`) | 1499 files | file + dotted YAML key |
| Config TC (mod payload `config_zh.yaml`) | 1448 files / **3479 strings** | same keys |
| Config SC (game's own `${source}`) | 1448 files | same keys (for attribution) |
| Dialogue DB (obj **71459**) `en`/`zh` fields | 14032 +1530 +139 pairs | order of appearance |
| UI TextTable (obj **71461**) `en`/`zh` columns | 1085 fields | language column id 2 vs 5 |

Method: (1) paired every string with its EN counterpart and read **all 3479 config
pairs** and **all 286 credit strings** by hand; (2) ran automated detectors
(placeholder / `{...}` / sprite-tag mismatches, digit mismatches, same-EN→different-TC
inconsistency, length-ratio outliers); (3) compared SC→TC to separate *game* faults
from *OpenCC* faults; (4) scanned a curated Mainland→Taiwan term list over the static
config **and** over the OpenCC-converted dialogue/UI text.

Because the mod is `TC = s2twp(SC) + 6 overrides`, a semantic error in TC that is also
in SC is inherited from the game's own EN→SC pass, **not** introduced by the mod.
Every "wrong match" below was confirmed present in `source/sc` as well (SC quoted).

---

## A. Wrong matches (config)

### A1. Inherited from the game's Simplified Chinese — semantic mistranslations

**High severity** (player-visible named entity / UI label that says something else):

| file | key | EN | TC (=s2twp of SC) | fault |
|---|---|---|---|---|
| `Abilities/MARY_EGYPT` | `Name` | Mary of Egypt | 開火！ | SC `开火！` = "Fire!" — completely different string |
| `Abilities/CLEANSING_FIRE_ROGUELIKE` | `Name` | Cleansing Fire | 地獄之火 | = "Hellfire"; should be 淨化之火 (cf. `CLEANSING_FIRE`=Hellfire uses same) |
| `Status/Cunning` | `Name` | Cunning | 赤腳醫生 | = "barefoot doctor" |
| `Status/Cunning` | `Description` | Hides unit intentions | 若敵方密咒詞語全為白，則不受傷害 | copied verbatim from `BlackBooker`; unrelated to "hides intentions" |
| `Units/Satan1` / `Units/Satan2` | `Name` | Satan | 死神 | = "Death"; `Satan1Roguelike` correctly uses 撒旦 |
| `Units/MermaidSalt` | `Name` | Saltwater Mermaid | 奧捷莉哈 | = "Obderikha" (the bath spirit) |
| `Units/SnakeSorcerer` | `Name` | Snake Koldun | 奧捷莉哈 | = "Obderikha" (`FoolGamePlayers/Zmeevik` = 弄蛇科爾敦) |
| `Inventory/ChurchKnife` | `Name` | Church Knife | 聖矛 | = "holy spear" |
| `Inventory/BirdCurse` | `Name` | Bird of Curses | 看守之鳥 | = "guardian bird" |
| `Inventory/DogMushroom` | `Name` | Dog Mushroom | 蛇頭菌 | = "snake-head fungus" |
| `Locations/Week3Day7Blood` | `Name` | Blood Trail | 血 | only "blood"; SC `血` |
| `Units/WolfDeadly` / `Units/WolfFedka` | `Name` | Changeling Wolf | 狼 | only "wolf" |
| `Locations/RoguelikeVictory` | `Name` | Endless Battles | 對抗魔鬼 | = "fight the demons" |
| `Locations/Week1Day7Vyatkino` | `Name` | Village Cemetery | 扎布羅汀村墓地 | names **Zabolotnaya** village, not Vyatkino |
| `Locations/Week1Day6BathUnderground1` | `LevelConfig.Battle.Name` | Unholy Coals | 煤塊讎特 | = "coal chort" |
| `Locations/Week2Day5CemeteryBackers` | `Name` | Cave Cemetery | 贊助玩家墓地 | = "backers' cemetery" |
| `Skills/RoguelikeSduVarahailNikola` | `Description` | Changes {Ability1} for {Ability2} in a starting deck | 物品可用欄位數量增加{CalculatedEffect} | text belongs to Big Bag; **`{Ability1}/{Ability2}` placeholders lost**, `{CalculatedEffect}` inserted |
| `Abilities/Wind_Luka_Up` | `Description` | {MinValue} damage / Draws a random page | 防禦增加{MinValue}點 / 隨機抽取一頁 | says **defence**, EN says **damage** (cf. `Wind_Moses_Up` = defence) |
| `Locations/Week4Day2FlockField` | `Description` | …Nemzya is blocked off by **chorts**… | 雖然**列希**把涅姆津亞村給封起來了… | chorts → leshiy |
| `Locations/Week2Day1NigneeMoshevo` | `Description` | The telegraph line **stops** in this village. | 這個村的電報線**斷了**。 | "stops (ends)" → "is broken" |

**Medium severity** (wrong word, less central):

| file | key | EN | TC | fault |
|---|---|---|---|---|
| `Units/SinnerHorse` | `Name` | Sinner-horse | 罪人 | drops "-horse" |
| `Units/SnakeCopper` | `Name` | Copper Snake | 蛇蜥 | 蛇蜥 = "legless lizard" |
| `Inventory/ThunderArrow` | `Name` | Thunder Arrow | 雷石 | 石 = "stone"; flavour still says arrowhead |
| `Inventory/BurstingBone` | `Name` | Bursting Bone | 貓頭骨 | "cat skull" |
| `Inventory/ChurchTowel` | `Name` | Church Towel | 建堂節毛巾 | 建堂節 = "patronal feast", not "church" |
| `Abilities/ERETNIK_STRIKE` | `Name` | Bony Hand | 瘦骨嶙峋 | "scrawny/emaciated" |
| `Abilities/FILIMON_OLD_VIEW` | `Name` | Ancient Gaze | 老態龍鍾 | "decrepit old age" |
| `Abilities/HELP_NIKOLA` | `Name` | Lend Help, Nicholas | 上帝保佑尼古拉 | "God bless Nicholas" |
| `Abilities/IN_LOOSE` | `Name` | Scatter! | 翻天覆地！ | "earth-shattering!" |
| `Abilities/FIRE_TIME` | `Name` | Time of Fire | 點火 | "light a fire" |
| `Abilities/RIZI` / `RIZI_SMALL` | `Name` | Imperishable Phelonion | 不朽權杖 | phelonion (vestment) → 權杖 "sceptre" |
| `Abilities/SHUKA_BELUGA_ROGUELIKE` | `Name` | Shuka-Beluga | 白斑狗魚 | name → "pike" (fish) |
| `Abilities/DEMON_BRANDER_BLESS` | `Name` | Hellish Motivation | 地獄禍心 | "hellish evil intent" |
| `Status/DefenceGive` (+`OberegOnHealthLoss`) | `Name` | Ward / Reinforce Ward | 招架 / 招架增強 | 招架 = "parry"; obereg = ward |
| `Status/MissChance` | `Name` | Blind Eye | 偏斜 | "deflection" |
| `Status/DoubleDamageOnCursed` | `Name` | Righteousness | 正直 | "integrity" |
| `Status/Untouchable` | `Name` | Untouchable | 賤民 | "pariah caste" |
| `Skills/ConfusedDirections` | `Name` | Confusing Directives | 含糊其辭 | "speak evasively" |
| `Inventory/Godmode` | `Flavour` | Rip and Tear | 隨心所欲 | joke string lost |
| `Inventory/KonekGorbunok` | `Flavour` | EXTREMA hardcore in 1986 on TIA-MC-1 | EXTEMA 1986年開發的TIA-MC-1遊戲 | "EXTREMA hardcore" dropped |
| `Abilities/GEORGY_*_ROGUELIKE`, `GEORGY_SHEPARD_SMALL`, `GEORGY_WINNER_ROGUELIKE` | `Name` | George … | 喬治… | 喬治 = English "George"; the same character is 葉戈裡 elsewhere (Рус. Егор/Георгий) |
| `Service/Credits` | `Developers.People[0].Titles[2].Title` | Programming | 程式計 | truncated; SC `程序计`; other slot uses 程式設計 |

**Text truncation / text mismatch (long strings):**

| file | key | EN | TC | note |
|---|---|---|---|---|
| `Inventory/Sivulist` | `Flavour` | Protects from any disease | 這種草生長在草甸和平坦之處… | TC is the **Peter's Cross** botanical note (`PetrovHerb`), not a cure text |
| `Inventory/CryingHerb` | `Flavour` | Crying Herb, crying herb! You've cried for so long but shed so few tears. | 千屈菜啊…（long incantation） | EN is a 2-line verse, TC is a long spell. **Cannot determine which side is intended** — flagging the divergence, not asserting a fix. |

### A2. OpenCC `s2twp` artefacts

OpenCC's single-char rule `里 → 裡` fires **inside transliterated personal names**,
where 里 is a syllable, not the word "inside". Verified by running the exact converter:

```
烈火叶戈里 => 烈火葉戈裡    神父叶戈里 => 神父葉戈裡
智天使基里安 => 智天使基裡安   苏佩里克 => 蘇佩裡克
圣叶戈里日 => 聖葉戈裡日
(control) 阿里莫夫树林 => 阿里莫夫樹林 ; 圣格里高利日 => 聖格里高利日  ← OpenCC leaves these alone
```

Affected config strings (7 + 3):

| file | key | EN | TC | correct |
|---|---|---|---|---|
| `Abilities/GEORGY_FIRE` | `Name` | George the Fiery | 烈火葉戈裡 | 烈火葉戈里 |
| `Abilities/Georgy_Batushka` | `Name` | George the Father | 神父葉戈裡 | 神父葉戈里 |
| `Abilities/Georgy_Brave` | `Name` | George the Brave | 勇者葉戈裡 | 勇者葉戈里 |
| `Abilities/Georgy_Prayer` | `Name` | George the Pious | 虔信者葉戈裡 | 虔信者葉戈里 |
| `Abilities/Georgy_Shepard` | `Name` | George the Shepherd | 牧者葉戈裡 | 牧者葉戈里 |
| `Abilities/Georgy_Winner` | `Name` | Saint George | 聖徒葉戈裡 | 聖徒葉戈里 |
| `Abilities/NIKOLA_GEORGY` | `Name` | Nicholas and George | 尼古拉與葉戈裡 | 尼古拉與葉戈里 |
| `Inventory/Dedovniki` | `Flavour` | …St. George's Day… | 聖葉戈裡日 | 聖葉戈里日 (or 聖葉戈爾日) |
| `Inventory/Kiryan` | `Name` | Kiryan Cherub | 智天使基裡安 | 智天使基里安 |
| `Inventory/Superik` | `Name`,`Flavour` | Superik | 蘇佩裡克 | 蘇佩里克 |

This is the only class of *content-changing* OpenCC artefact found. A sample of the
725 distinct SC→TC single-char substitutions contained no other semantic confusions
(干→乾/幹, 只→隻, 系→係/繫, 谷→穀, 面→麵, 咸→鹹, 制→製, 里→裡 in ordinary words are all correct).

### A3. Override / build-side checks

* The 6 reviewed overrides are correctly present and applied:
  `Service/Credits/config_zh.yaml` → `ChineseLocalization.Header`=簡體中文在地化,
  `People[0..3].Titles[0].Title`=在地化管理/在地化, `Developers.People[5].Titles[0].Title`=品質管制.
  Minor: EN `Localization Lead` → 在地化**管理** ("management"); "Lead" would be 在地化**負責人/主管**.
* **Non-string defect inherited from EN into the payload** — malformed sprite/tag names:
  * `Status/Martyrdom::Description` contains `<sprite name = "Health ">` (trailing space in the
    sprite name) — matches EN but will not resolve to the `Health` sprite.
  * Object 71461 `DEFENCE_ON_MONEY` uses `<sprite name="Defense">` (US spelling) while every
    other string uses `"Defence"` — icon will not resolve. (bundle data, not config)

---

## B. Non-Taiwan terminology

**Config: essentially none.** A broad Mainland→Taiwan term list (140+ entries: 信息/質量/默認/
打印/鼠標/屏幕/分辨率/服務器/內存/文件/界面/設置/程序/數據/存儲/加載/視頻/音頻/網絡/軟件/
硬件/激光/光盤/社區/項目/通過/用戶/… ) produced **zero hits** in the 3479 TC config strings
beyond 顏色 and 型別, both of which are also correct Taiwan usage. s2twp is doing its job.

**Dialogue / UI (OpenCC-converted on the fly):** a few genuine misses survive s2twp:

| term | count | meaning | Taiwan | examples (obj 71459 `zh` unless noted) |
|---|---|---|---|---|
| 質量 | 2 | "quality" | 品質 | 「…想告訴其他人質量有多好」; 「樣式有點兒舊，不過質量好！」 |
| 反饋 | 1 | "feedback" | 回饋 | 71461 `BackerWarning`: 「…請勿在直…」（feedback 语境） |
| 公交車 | 1 | "city bus" | 公車/巴士 | 「…往公路上的公交車站那邊走」 (modern-frame story) |
| 工資 | 2 | "wage" | 薪水 | 「他今天的工資給你了」; 「給我漲工資呢！」 (borderline; understood in TW) |

(者 `酸奶`/`酸奶油` are correct Taiwan usage — excluded. `移動` is standard Taiwan — excluded.)

**Register/dialect note (not terminology):** the whole corpus carries a Northern/Mainland
rustic voice that OpenCC cannot and should not change — 俺 ×27, 咋 ×11, 孬 ×3, 犄角旮旯,
玩意兒 ×7 in config alone, and far more in dialogue. This is a *voice* choice inherited
from the game's SC, not a Taiwan-vs-Mainland vocabulary bug; it is worth a decision but
it is not something an `overrides.tsv` term list fixes.

---

## C. Dialogue / UI text (objects 71459, 71461) — best effort

**Coverage:** 14032 dialogue-text pairs + 1530 `Name` + 1530 `Description` + 139
`Display Name` + 14032 `Menu Text` pairs in 71459, plus all 1085 TextTable field records
in 71461. These were screened with automated detectors plus targeted reading; I did **not**
read all ~31k dialogue pairs semantically (see §E).

### C1. `chort` → 讎特 — systematic

The Slavic demon "chort" is machine-translated as **雠特** (Simplified) → **讎特** (TC).
`讎` means "feud/hatred", so the term is meaningless.

* **Config:** 113 strings across 91 files contain 讎 (e.g. `Units/SamovarDemon`=茶炊讎特,
  `Locations/Week1Day1Kusheva[LevelConfig.Battle.Name]`=茶炊讎特, `Skills/CroockedDemons`,
  `Skills/SkilledDemons`, `Skills/DemonGift1/2`, `Inventory/DevilsBag`, plus ~60 battle names).
* **Dialogue 71459:** 620 `zh` texts contain 雠, plus `Menu Text zh` ×29, `Description zh` ×10,
  `Display Name zh` ×4, `Name zh` ×2. Example: 「雠特抓了一张牌……」, 「瓦西娅，有没有雠特其实无所谓！」
* Recommended correct term: 惡魔/魔鬼 is already used for "demon", so a distinct rendering
  such as **喬特** (transliteration) or **小鬼** is needed. This is a **term-level** fix,
  best done in the converter/plugin pipeline, not as ~130 per-string overrides.

### C2. Markup loss inherited from SC

19 / 14032 dialogue entries have EN markup (`[em2]<link=NN>…[/em2]`) that is **absent** from
the ZH; e.g. #7736, #7920, #7932, #7935, #7942, #9171, #10506, #10983 — the Chinese lost the
`[em2]…[/em2]` emphasis/hyperlink around terms such as "leshiy", "Ivan Kupala", "Voipel".
Formatting-only, but it affects the glossary-linking feature. Inherited from SC.

### C3. Confirmed semantic dialogue mismatches (examples)

* **#7296** EN "…**Saint George's** Day, the 6th of May…" → ZH 「…**圣格里高利**日…」 — George
  rendered as **Gregory**. (Config `Dedovniki` gets the same day right as 聖葉戈里日.)
* **#1200** EN "What demon is necessary for the Book to open the aspen seal?" → ZH
  「怎么才能要想破开黑书的杨之印？」 — "what demon is necessary" dropped.
* `71461 Library`: EN "Library" → ZH 「书」 ("book"); should be 書房/圖書館.
* `71461 StatusInvPrefix`: EN "Strengthens status" → ZH 「令」 (isolated particle).
* `71461 BackerRoguelike`: EN "New Game (Endless Battles)" → ZH 「无休对战」 (drops "New Game").

The remaining flagged pairs (placeholder/digit set, `dialogue_71459_flags.json`,
`texttable_71461_flags.json`) are dominated by legitimate expansion/contraction and the
padding spaces the game uses for fixed-width UI (`疯      狂` for "Insane", etc.); these are
**not** mismatches.

---

## D. Suggested corrections (proposals only — NOT applied)

Machine-verified against the live payload; written to
`.copilot_workspace/bb-tc-audit/proposed_overrides.tsv`, format `file<TAB>key<TAB>replacement`.
`file` is relative to `StreamingAssets/Config` (matching `reference/overrides.tsv`).

```
file	key	replacement
Locations/Week3Day7Blood/config_zh.yaml	Name	血跡
Units/WolfDeadly/config_zh.yaml	Name	換生狼
Units/WolfFedka/config_zh.yaml	Name	換生狼
Skills/KeysKnowledge/config_zh.yaml	Name	鑰之學識
Skills/OrdersKnowledge/config_zh.yaml	Name	令之學識
Locations/RoguelikeVictory/config_zh.yaml	Name	無休對戰
Units/Satan1/config_zh.yaml	Name	撒旦
Units/Satan2/config_zh.yaml	Name	撒旦
Abilities/CLEANSING_FIRE_ROGUELIKE/config_zh.yaml	Name	淨化之火
Abilities/MARY_EGYPT/config_zh.yaml	Name	埃及的瑪利亞
Status/Cunning/config_zh.yaml	Name	狡詐
Status/Cunning/config_zh.yaml	Description	隱藏敵方單位的行動意圖
Inventory/ChurchKnife/config_zh.yaml	Name	教堂刀
Inventory/BirdCurse/config_zh.yaml	Name	詛咒之鳥
Inventory/DogMushroom/config_zh.yaml	Name	狗菇
Units/MermaidSalt/config_zh.yaml	Name	鹹水露莎卡
Units/SnakeSorcerer/config_zh.yaml	Name	弄蛇科爾敦
Locations/Week1Day7Vyatkino/config_zh.yaml	Name	維亞特基諾村墓地
Locations/Week1Day6BathUnderground1/config_zh.yaml	LevelConfig.Battle.Name	邪煤
Inventory/Sivulist/config_zh.yaml	Flavour	可治百病
Abilities/ERETNIK_STRIKE/config_zh.yaml	Name	骨手
Abilities/HELP_NIKOLA/config_zh.yaml	Name	出手相助吧，尼古拉
Abilities/IN_LOOSE/config_zh.yaml	Name	散開！
Status/DefenceGive/config_zh.yaml	Name	護佑
Status/Untouchable/config_zh.yaml	Name	不可觸
Locations/Week2Day5CemeteryBackers/config_zh.yaml	Name	洞穴墓地
Units/SinnerHorse/config_zh.yaml	Name	罪人之馬
Units/SnakeCopper/config_zh.yaml	Name	銅蛇
Locations/Week2Day1NigneeMoshevo/config_zh.yaml	Description	這條電報線到這個村就終止了。
Inventory/Kiryan/config_zh.yaml	Name	智天使基里安
Inventory/Superik/config_zh.yaml	Name	蘇佩里克
Inventory/Superik/config_zh.yaml	Flavour	你的蘇佩里克可真漂亮！
Abilities/Georgy_Batushka/config_zh.yaml	Name	神父葉戈里
Abilities/Georgy_Brave/config_zh.yaml	Name	勇者葉戈里
Abilities/Georgy_Prayer/config_zh.yaml	Name	虔信者葉戈里
Abilities/Georgy_Shepard/config_zh.yaml	Name	牧者葉戈里
Abilities/Georgy_Winner/config_zh.yaml	Name	聖徒葉戈里
Abilities/GEORGY_FIRE/config_zh.yaml	Name	烈火葉戈里
Abilities/NIKOLA_GEORGY/config_zh.yaml	Name	尼古拉與葉戈里
Service/Credits/config_zh.yaml	Developers.People[0].Titles[2].Title	程式設計
```

> Note on the last line: `Developers.People[0].Titles[2].Title` = 程式設計 collides with the
> existing correct `StartingElements[3].Title`; that is fine (they are different keys).

**Not expressible as single-string overrides (needs a decision / pipeline change):**

* `Abilities/Wind_Luka_Up::Description` — the correct value contains a newline, and
  `scripts/gate_overrides.py` splits each line on TAB with no multi-line support, so it
  cannot go in `overrides.tsv`. Fix via the payload generator or a multi-line rule.
* **讎特 → correct "chort" term** across ~113 config strings and ~665 dialogue fields.
* **The 里→裡 name artefact** broadly — the 10 overrides above fix the instances that exist
  today, but the converter rule needs a name whitelist (e.g. exempt 葉戈里/基里安/蘇佩里克)
  or it will reappear for any future string.
* `Inventory/CryingHerb::Flavour` — EN verse vs TC incantation; **which is intended is unknown**.
* `Locations/Week4Day2FlockField::Description`, `Service/Credits::Thanks` and other long
  CJK strings — need a translator, not a replace.

---

## E. Honest coverage & limitations

* **Config: exhaustive.** All 1448 TC files / **3479 strings** were paired and read;
  all 286 differing credit strings reviewed; 0 strings had no EN counterpart.
* **Automated detectors** (all config + dialogue + UI): placeholder/sprite set, digit set,
  same-EN→multiple-TC, same-TC→multiple-EN, length ratio. Machine-generated flag files are
  in this directory.
* **Dialogue/UI: best effort, not exhaustive.** I screened all ~31k 71459 pairs and all 1085
  71461 records with detectors and read a targeted sample, but I did **not** semantically read
  every one of the ~14k dialogue lines. A residual number of inherited mistranslations in
  dialogue surely remain unreported.
* **Attribution.** For the static config I confirmed each fault exists in `source/sc`
  (SC quoted) ⇒ inherited from the game, and separately ran the exact `s2twp` converter to
  isolate OpenCC artefacts. For dialogue I only have the raw Simplified bundle; I infer
  (do not prove) that a mismatch there is inherited, because the plugin's only transformation
  is `s2twp`, which is content-preserving apart from the 里-class artefact.
* **Not determined:** the correct intended Chinese for `CryingHerb::Flavour`; the canonical
  Chinese name for "chort"; whether `George` should be normalised to the game's dominant
  Егор → 葉戈爾 form; and the total number of semantic dialogue errors (sample-based only).
