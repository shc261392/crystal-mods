# TCFix — runtime description-font fix (plugin source)

`TCFix` 是本繁體中文化模組隨附的開源 BepInEx 6（IL2CPP）外掛。它在遊戲執行期把
用來算繪**單位／戰役描述**的字型 `futura medium condensed bt SDF - No Underlay`
（沒有中文字符、會把繁體字算繪成亂碼）換成完整含繁體字的
`futura medium condensed bt SDF`。此為修正描述亂碼的關鍵，無法只靠修改遊戲檔案達成。

`TCFix` is the open-source BepInEx 6 (IL2CPP) plugin bundled with this Traditional
Chinese localization. At runtime it swaps the CJK-less description font
`futura medium condensed bt SDF - No Underlay` (which garbles Traditional-Chinese
glyphs) for the full-TC `futura medium condensed bt SDF` on all affected
`TMP_Text` components.

## 檔案 / Files

- `Plugin.cs` — 完整外掛原始碼 / full plugin source.
- `TCFix.csproj` — 建置專案（`net6.0`）/ build project.

## 建置 / Build

需要 .NET 6 SDK 與遊戲已產生的 BepInEx `interop/` 組件（首次啟動遊戲後生成）。
Requires the .NET 6 SDK and the game's generated BepInEx `interop/` assemblies
(created after launching the game once with BepInEx installed).

```sh
dotnet build -c Release -p:GameDir="<game root>"
# 輸出 / output: bin/Release/net6.0/TCFix.dll  ->  BepInEx/plugins/TCFix.dll
```

`TCFix.csproj` 透過 `GameDir` 屬性以 `HintPath` 參照遊戲的 `BepInEx/core` 與
`BepInEx/interop` 組件。`TCFix.csproj` references the game's `BepInEx/core` and
`BepInEx/interop` assemblies via the `GameDir` MSBuild property.

## 執行環境框架 / Runtime framework

本外掛需要 **BepInEx 6（IL2CPP, Bleeding Edge）** —— 於本模組頁面以
**「Core (BepInEx6)」** 檔案提供。官方來源 / official source:

- BepInEx（LGPL-2.1）: <https://github.com/BepInEx/BepInEx>
- Bleeding Edge builds: <https://builds.bepinex.dev/projects/bepinex_be>
- 使用版本 / build used: **#785**, commit `6abdba4`

授權 / License: 外掛原始碼可自由審閱與重建。BepInEx 本身為 LGPL-2.1。
