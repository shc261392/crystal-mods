#!/usr/bin/env python3
"""Scan the TC payload for Mainland-only wording that OpenCC s2twp leaves alone.

For each term we report whether it appears, how many times, and where.
Terms OpenCC already rewrites never appear in the payload, which is why the
list only matters for terms s2twp misses.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path("/home/shado/crystal-mods/.copilot_workspace/bb-tc-audit")
rows = [json.loads(line) for line in (HERE / "triples.jsonl").read_text(encoding="utf-8").splitlines()]

# term -> (Taiwan equivalent, note). Broad list; only hits matter.
TERMS = {
    "信息": "資訊", "信息量": "資訊量", "質量": "品質", "質量控制": "品質管制",
    "默認": "預設", "缺省": "預設", "打印": "列印", "打印機": "印表機",
    "鼠標": "滑鼠", "屏幕": "螢幕", "分辨率": "解析度", "服務器": "伺服器",
    "內存": "記憶體", "內存條": "記憶體", "硬盤": "硬碟", "優盤": "隨身碟",
    "文件": "檔案", "文件夾": "資料夾", "菜單": "選單", "界面": "介面",
    "設置": "設定", "程序": "程式", "程序員": "程式設計師",
    "數據": "資料", "數據庫": "資料庫", "存儲": "儲存", "加載": "載入",
    "保存": "儲存", "登錄": "登入", "註銷": "登出", "在線": "線上",
    "離線": "離線", "支持": "支援", "反饋": "回饋", "創建": "建立",
    "添加": "新增", "粘貼": "貼上", "視頻": "影片", "音頻": "音訊",
    "網絡": "網路", "軟件": "軟體", "硬件": "硬體", "芯片": "晶片",
    "激光": "雷射", "光盤": "光碟", "博客": "部落格", "社區": "社群",
    "項目": "專案", "通過": "透過", "渠道": "管道", "用戶": "使用者",
    "客戶端": "用戶端", "服務端": "伺服器端", "本地化": "在地化",
    "字地化": "在地化", "智能": "智慧", "移動": "行動", "遊戲機": "主機",
    "土豆": "馬鈴薯", "西紅柿": "番茄", "空調": "冷氣", "冰箱": "冰箱",
    "計算機": "電腦", "筆記本": "筆電", "手機": "手機", "短信": "簡訊",
    "出租車": "計程車", "自行車": "腳踏車", "摩托車": "機車", "公交車": "公車",
    "地鐵": "捷運", "蓋章": "蓋章", "複印": "影印", "打印店": "影印店",
    "視頻遊戲": "電玩", "集裝箱": "貨櫃", "洗面奶": "洗面乳", "方便麵": "泡麵",
    "盒飯": "便當", "酸奶": "優格", "奶昔": "奶昔", "彌猴桃": "奇異果",
    "菠蘿": "鳳梨", "巧克力": "巧克力", "沙發": "沙發", "公車": "公車",
    "裁員": "資遣", "招聘": "招募", "簡歷": "履歷", "面試": "面試",
    "儲蓄": "儲蓄", "工資": "薪水", "薪水": "薪水", "房貸": "房貸",
    "悔棋": "悔棋", "選項": "選項", "設置選項": "設定選項",
    "顏色": "顏色", "顏料": "顏料", "酒精": "酒精",
    "質量檢測": "品質檢測", "信息技術": "資訊科技", "項目管理": "專案管理",
    "程序設計": "程式設計", "程序计": "程式設計",
    "型別": "型別",  # Taiwan term, control
}

hits = collections.Counter()
examples: dict[str, list[str]] = collections.defaultdict(list)

# Search both the TC payload values AND the full raw byte text (to catch values
# with punctuation). Here we scroll every string value.
for r in rows:
    tc = r["tc"] or ""
    for term in TERMS:
        if term in tc:
            hits[term] += 1
            if len(examples[term]) < 6:
                examples[term].append(f"{r['file']}::{r['key']}  TC={tc}")

print(f"strings scanned: {len(rows)}")
print(f"distinct Mainland terms hit: {len(hits)}\n")
for term, n in hits.most_common():
    print(f"{term} (x{n})  -> Taiwan {TERMS[term]}")
    for ex in examples[term]:
        print(f"      {ex}")
