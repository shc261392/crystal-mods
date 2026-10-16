#!/usr/bin/env python3
"""Verify proposed override targets and emit an overrides.tsv-style proposal."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path("/home/shado/crystal-mods/.copilot_workspace/bb-tc-audit")
rows = {(r["file"], r["key"]): r for r in
        (json.loads(l) for l in (HERE / "triples.jsonl").read_text(encoding="utf-8").splitlines())}

# (dir, key, proposed replacement, rationale)
PROPOSALS = [
    ("Locations/Week3Day7Blood", "Name", "血跡", "EN 'Blood Trail'; SC 血 = 'blood' only"),
    ("Units/WolfDeadly", "Name", "換生狼", "EN 'Changeling Wolf'; SC 狼 = 'wolf' only"),
    ("Units/WolfFedka", "Name", "換生狼", "EN 'Changeling Wolf'; SC 狼 = 'wolf' only"),
    ("Skills/KeysKnowledge", "Name", "鑰之學識", "EN 'Knowledge of Keys'; SC 鑰識 is a non-word; sister file uses 鑰之學識"),
    ("Skills/OrdersKnowledge", "Name", "令之學識", "EN 'Knowledge of Orders'; SC 令識 is a non-word; sister file uses 令之學識"),
    ("Locations/RoguelikeVictory", "Name", "無休對戰", "EN 'Endless Battles'; SC 對抗魔鬼 = 'fight demons'; other Endless Battles files use 無休對戰"),
    ("Units/Satan1", "Name", "撒旦", "EN 'Satan'; SC 死神 = 'Death'; Satan1Roguelike already uses 撒旦"),
    ("Units/Satan2", "Name", "撒旦", "EN 'Satan'; SC 死神 = 'Death'"),
    ("Abilities/CLEANSING_FIRE_ROGUELIKE", "Name", "淨化之火", "EN 'Cleansing Fire'; SC 地獄之火 = 'Hellfire'"),
    ("Abilities/MARY_EGYPT", "Name", "埃及的瑪利亞", "EN 'Mary of Egypt'; SC 開火！ = 'Fire!'"),
    ("Status/Cunning", "Name", "狡詐", "EN 'Cunning'; SC 赤腳醫生 = 'barefoot doctor'"),
    ("Status/Cunning", "Description", "隱藏敵方單位的行動意圖", "EN 'Hides unit intentions'; SC text is copied from BlackBooker (all-white-zagovor immunity)"),
    ("Inventory/ChurchKnife", "Name", "教堂刀", "EN 'Church Knife'; SC 聖矛 = 'holy spear'"),
    ("Inventory/BirdCurse", "Name", "詛咒之鳥", "EN 'Bird of Curses'; SC 看守之鳥 = 'guardian bird'"),
    ("Inventory/DogMushroom", "Name", "狗菇", "EN 'Dog Mushroom'; SC 蛇頭菌 = 'snake-head fungus'"),
    ("Units/MermaidSalt", "Name", "鹹水露莎卡", "EN 'Saltwater Mermaid'; SC 奧捷莉哈 = 'Obderikha' (copy of Unit/Obderiha)"),
    ("Units/SnakeSorcerer", "Name", "弄蛇科爾敦", "EN 'Snake Koldun'; SC 奧捷莉哈 = 'Obderikha'"),
    ("Locations/Week1Day7Vyatkino", "Name", "維亞特基諾村墓地", "EN 'Village Cemetery'; SC 扎布羅汀村墓地 = Zabolotnaya village cemetery (wrong village)"),
    ("Locations/Week1Day6BathUnderground1", "LevelConfig.Battle.Name", "邪煤", "EN 'Unholy Coals'; SC 煤塊讎特 = 'coal chort'"),
    ("Abilities/Wind_Luka_Up", "Description", "{MinValue}點傷害\n隨機抽取一頁", "EN says damage; SC says 'defence +{MinValue}'"),
    ("Inventory/Sivulist", "Flavour", "可治百病", "EN 'Protects from any disease'; SC text is the Peter's Cross botanical note"),
    ("Abilities/ERETNIK_STRIKE", "Name", "骨手", "EN 'Bony Hand'; SC 瘦骨嶙峋 = 'skinny/scrawny'"),
    ("Abilities/HELP_NIKOLA", "Name", "出手相助吧，尼古拉", "EN 'Lend Help, Nicholas'; SC 上帝保佑尼古拉 = 'God bless Nicholas'"),
    ("Abilities/IN_LOOSE", "Name", "散開！", "EN 'Scatter!'; SC 翻天覆地！ = 'earth-shattering!'"),
    ("Status/DefenceGive", "Name", "護佑", "EN 'Ward' (obereg); SC 招架 = 'parry'"),
    ("Status/Untouchable", "Name", "不可觸", "EN 'Untouchable'; SC 賤民 = 'pariah caste'"),
    ("Locations/Week2Day5CemeteryBackers", "Name", "洞穴墓地", "EN 'Cave Cemetery'; SC 贊助玩家墓地 = 'backers' cemetery'"),
    ("Units/SinnerHorse", "Name", "罪人之馬", "EN 'Sinner-horse'; SC 罪人 = 'sinner' (drops '-horse')"),
    ("Units/SnakeCopper", "Name", "銅蛇", "EN 'Copper Snake'; SC 蛇蜥 = 'legless lizard'"),
    ("Locations/Week2Day1NigneeMoshevo", "Description", "這條電報線到這個村就終止了。", "EN 'The telegraph line stops in this village'; SC 斷了 = 'is broken'"),
    ("Inventory/Kiryan", "Name", "智天使基里安", "OpenCC artefact: 基里安 -> 基裡安 (里 is part of the name Kiryan, not 'inside')"),
    ("Inventory/Superik", "Name", "蘇佩里克", "OpenCC artefact: 蘇佩里克 -> 蘇佩裡克"),
    ("Inventory/Superik", "Flavour", "你的蘇佩里克可真漂亮！", "OpenCC artefact: 蘇佩裡克"),
    ("Abilities/Georgy_Batushka", "Name", "神父葉戈里", "OpenCC artefact: 葉戈里 -> 葉戈裡 (Egor); SC uses 叶戈里"),
    ("Abilities/Georgy_Brave", "Name", "勇者葉戈里", "OpenCC artefact 葉戈裡"),
    ("Abilities/Georgy_Prayer", "Name", "虔信者葉戈里", "OpenCC artefact 葉戈裡"),
    ("Abilities/Georgy_Shepard", "Name", "牧者葉戈里", "OpenCC artefact 葉戈裡"),
    ("Abilities/Georgy_Winner", "Name", "聖徒葉戈里", "OpenCC artefact 葉戈裡"),
    ("Abilities/GEORGY_FIRE", "Name", "烈火葉戈里", "OpenCC artefact 葉戈裡"),
    ("Abilities/NIKOLA_GEORGY", "Name", "尼古拉與葉戈里", "OpenCC artefact 葉戈裡"),
    ("Service/Credits", "Developers.People[0].Titles[2].Title", "程式設計", "EN 'Programming'; SC 程序计 truncated -> 程式計"),
]

ok = bad = 0
lines = []
for d, k, repl, why in PROPOSALS:
    row = rows.get((d, k))
    if row is None:
        print(f"!! NO ROW for {d} :: {k}")
        bad += 1
        continue
    if (row["tc"] or "").strip() == repl.strip():
        print(f"== {d} :: {k} already equals proposal")
        continue
    ok += 1
    lines.append((d, k, repl, why, row["en"], row["tc"], row["sc"]))

print(f"verified {ok} (of {len(PROPOSALS)}), missing {bad}\n")
with (HERE / "proposed_overrides.tsv").open("w", encoding="utf-8") as fh:
    fh.write("# file\tkey\treplacement\n")
    fh.write("# PROPOSALS ONLY - not applied. Review before use.\n")
    for d, k, repl, why, en, tc, sc in lines:
        fh.write(f"{d}/config_zh.yaml\t{k}\t{repl}\n")
print("wrote proposed_overrides.tsv\n")
for d, k, repl, why, en, tc, sc in lines:
    print(f"{d} :: {k}")
    print(f"   EN: {en}")
    print(f"   SC: {sc}")
    print(f"   TC: {tc}")
    print(f"   -> {repl}    ({why})")
