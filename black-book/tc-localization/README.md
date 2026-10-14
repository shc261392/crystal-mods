# Black Book — Traditional Chinese Localization Mod

**繁體中文本地化模組**

> **English** · [中文](#繁體中文)

Unofficial Traditional Chinese (繁體中文 / 正體中文) localisation for
**Black Book** (Steam App ID 1138660).

The game already ships a complete Simplified Chinese localisation. This mod
converts it to Traditional Chinese using
[OpenCC](https://github.com/BYVoid/OpenCC) `s2twp` (Simplified → Traditional,
Taiwan, with phrase substitution) plus a small set of reviewed terminology
corrections.

---

## Coverage — read this first

Black Book stores its Chinese text in **two different places**, and this mod
only converts one of them:

| Where the text lives | What it is | Covered? |
|---|---|---|
| `Black Book_Data/StreamingAssets/Config/**/config_zh.yaml` | Item names and descriptions, ability names, quest and chapter text, demon list, credits screen — **3,479 strings in 1,448 files** | ✅ **Yes** |
| `Black Book_Data/data.unity3d` | Menus, settings labels, tooltips, dialogue and story text baked into Unity assets — **~5,100 distinct strings** | ❌ **No** |

Measured against the runtime string dump captured by XUnity AutoTranslator
before it was removed: of **5,881** distinct strings the game actually displays,
**766** come from the YAML configs and **5,115** (≈87%) come from Unity assets.

**Consequence:** with this mod installed and no other translation layer, roughly
87% of the game's text — menus, settings, tooltips, dialogue — is still
Simplified Chinese. Item names, ability names, chapter titles and the credits
screen are Traditional. **The two languages appear side by side.**

Closing that gap means patching `data.unity3d` in place, which is a separate
(and much riskier) piece of work. See [Roadmap](#roadmap).

The game does **not** need a CJK font installed: it already ships
`arialuni_sdf_u2018`, which covers Traditional characters.

---

## Installation

### Option A — Script (recommended)

**Linux / WSL2 / Git Bash**

```bash
cd tc-localization
bash deploy.sh              # add --dry-run to preview
```

**Windows PowerShell**

```powershell
cd C:\path\to\tc-localization
.\deploy.ps1                # add -DryRun to preview
```

Both scripts auto-detect the Steam install, write only the
`config_zh.yaml` files, and leave every other game file alone. Pass
`--game-path` / `-GamePath` if the game is somewhere unusual.

### Option B — Manual

1. Download `tc-localization-v*.zip` from Releases.
2. Find your game folder (Steam → right-click **Black Book** → **Manage** →
   **Browse local files**).
3. Extract the zip over the game folder, merging into
   `Black Book_Data/StreamingAssets/Config/`.

### Uninstall

```bash
bash uninstall.sh           # Linux / WSL2 / Git Bash
.\uninstall.ps1             # Windows PowerShell
```

The game's own Simplified Chinese files are restored from `source/sc/`, which
holds them byte-for-byte. **No backup is created or needed** — the same files
are the build input.

If anything still looks wrong, verify the install through Steam:
*right-click Black Book → Properties → Installed Files → Verify integrity of
game files*.

---

## Building from source

```bash
make build
```

That is the **only** command that produces a release zip. It:

1. **generates** — converts `source/sc/**` (the game's own Simplified Chinese)
   into `payload/**` via OpenCC `s2twp`, then applies
   `reference/overrides.tsv`;
2. **validates** — runs five quality gates;
3. **packages** — writes `dist/tc-localization-v<version>.zip`.

The build never reads the installed game, so it works on any machine and
always produces a byte-identical archive. Verify with:

```bash
make check-package
```

### Quality gates

| Gate | Catches |
|---|---|
| `gate_coverage.py` | A source file with no payload counterpart, or a string key that disappeared. *(This is what caught `Service/Credits`, `Demons` and `Izba` being silently dropped.)* |
| `gate_structure.py` | Key reordering, lost numbers/booleans, or encoding drift — the UTF-8 BOM and CRLF line endings the game itself ships must survive. |
| `gate_simplified.py` | Any string that is not exactly `s2twp(source)`. Note `s2twp` is **not** idempotent: running it twice turns `托马希哈` into the wrong `託馬希哈`. |
| `gate_overrides.py` | A manual correction in `overrides.tsv` that no longer matches anything. |
| `gate_terminology.py` | Mainland-only wording that survives conversion (see `reference/terminology_banned.tsv`). |

### Manual corrections

`reference/overrides.tsv` holds reviewed corrections applied after conversion,
one TAB-separated `file / key / text` row per line. It is plain text, so
corrections are reviewable in a pull request rather than hidden in a script.

---

## Project layout

```
tc-localization/
├── Makefile                  # the one canonical build
├── pyproject.toml            # pinned build dependencies
├── source/sc/                # the game's own Simplified Chinese config
│                             #   (build input AND uninstall restoration source)
├── payload/                  # generated, not committed
├── reference/
│   ├── overrides.tsv         # reviewed manual corrections
│   ├── terminology_banned.tsv# Mainland-only terms to reject
│   ├── TERMINOLOGY.md        # human glossary
│   └── TC_STANDARDS.md       # writing conventions
└── scripts/                  # builder, gates, packager
```

---

## Troubleshooting

**Text is still Simplified in menus and dialogue.**
Expected — see [Coverage](#coverage-read-this-first). Item names, ability
names, chapter titles and the credits screen should be Traditional.

**Text shows as empty boxes (tofu).**
The game ships its own CJK font (`arialuni_sdf_u2018`); this mod does not
replace it. If text is missing there too, the Simplified Chinese original was
likely damaged — run `bash uninstall.sh` to restore it, or verify through Steam.

**`make build` fails with a missing dependency.**

```bash
uv venv && uv pip install -e .
```

---

## Roadmap

- [ ] Convert the Unity asset text in `data.unity3d` so the mod covers ~100%
      of the game instead of ~13%. Requires an asset-rewrite step and careful
      regression testing.
- [ ] Resolve `雠特` / `讎特` ("chort", a Slavic household spirit) — currently
      transliterated to `讎特`, whose literal meaning is "feud". `楚特` is
      probably the right transliteration. Affects 113 strings.
- [ ] Review the 189 game directories that ship no Simplified Chinese at all.

---

## Credits

- **Game**: Black Book © HypeTrain Digital / Morteshka
- **Simplified Chinese localisation**: the original developers and community
- **Conversion**: [OpenCC](https://github.com/BYVoid/OpenCC) `s2twp`
- **Mod**: Community

This is an unofficial fan project. Not affiliated with or endorsed by
HypeTrain Digital or Morteshka.

---

## 繁體中文

非官方 **Black Book**（Steam App ID 1138660）繁體中文本地化模組。

遊戲本身已內建完整的簡體中文，本模組使用 OpenCC `s2twp` 加上人工校訂的
術語修正，將其轉換為繁體中文。

### 覆蓋範圍（請先閱讀）

| 文字所在位置 | 內容 | 有沒有轉換 |
|---|---|---|
| `StreamingAssets/Config/**/config_zh.yaml` | 物品名稱與說明、能力名稱、任務與章節標題、惡魔列表、製作人員名單 — **1,448 個檔案、3,479 條字串** | ✅ 有 |
| `Black Book_Data/data.unity3d` | 選單、設定、提示、對話與劇情文字 — **約 5,100 條字串** | ❌ 沒有 |

實測資料：在移除自動翻譯工具前擷取到的 5,881 條實際顯示字串中，只有 766 條
來自 YAML 設定檔，其餘 5,115 條（約 87%）來自 Unity 資源檔。

**因此，安裝本模組後，物品名稱、能力名稱、章節標題與製作人員名單會是繁體，
但選單、設定、提示與對話仍會是簡體，兩種文字會並存。**

補足這個缺口需要直接改寫 `data.unity3d`，屬於另一項風險較高的工作，詳見
「Roadmap」。

遊戲已內建支援中日韓的字型（`arialuni_sdf_u2018`），無須另外安裝字型。

### 安裝／移除

```bash
bash deploy.sh        # 安裝（加上 --dry-run 可先預覽）
bash uninstall.sh     # 還原遊戲原本的簡體中文
```

Windows PowerShell 請改用 `.\deploy.ps1` 與 `.\uninstall.ps1`。

不需要備份：模組中的 `source/sc/` 存放了遊戲原本的簡體中文設定檔，
移除時會直接複製回去。

### 自行建置

```bash
make build
```

這是唯一會產生發行版壓縮檔的指令，流程為「產生 → 檢查 → 封裝」，
且完全不讀取遊戲安裝目錄，因此可在任何機器上重現相同的封裝檔。

### 致謝

- **遊戲**：Black Book © HypeTrain Digital / Morteshka
- **簡體中文在地化**：原開發者與社群
- **轉換工具**：[OpenCC](https://github.com/BYVoid/OpenCC) `s2twp`
- **模組**：社群

本為非官方同人專案，與 HypeTrain Digital、Morteshka 無任何關聯。