# BepInEx 6 (IL2CPP) — Setup & Verification Guide

> Experimental runtime-modding phase for the Warhammer 40,000: Battlesector
> Traditional Chinese localization. This is required because the description-text
> garble is controlled by the **game's runtime code**, not the moddable font
> assets (proven exhaustively — see `DESCRIPTION_FONT_INVESTIGATION.md`).
>
> Branch: `feat/wh40k-bs-bepinex`

---

## 1. What this is and why

BepInEx is an open-source modding framework that lets a `.NET` plugin run inside
the game process. We will use it to:

1. **Diagnose** — hook the description text at runtime and log the *actual* font,
   material, and atlas the game uses (the prefab says font `785`, but the runtime
   overrides it — this is the mystery we must observe directly).
2. **Fix** — once the true runtime font is known, force it to render full
   Traditional Chinese.

The game is **Unity 6000.0.62f1, IL2CPP**, which requires **BepInEx 6
Bleeding-Edge (pre-release)**. Your game folder already contains a matching
UnityDoorstop (`winhttp.dll`, `doorstop_config.ini`) from a prior attempt; this
package completes it.

---

## 2. Provenance & integrity (verify before trusting binaries)

**Source (official BepInEx build server):**

- Project: BepInEx Bleeding Edge — <https://builds.bepinex.dev/projects/bepinex_be>
- Build: **#785**, commit **`6abdba4`**
  (<https://github.com/BepInEx/BepInEx/commit/6abdba47eeebe08552282e7a58ef0f4a9ab60b62>)
- Direct artifact URL:
  `https://builds.bepinex.dev/projects/bepinex_be/785/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.785+6abdba4.zip`
- BepInEx is open source (LGPL-2.1): <https://github.com/BepInEx/BepInEx>

**SHA-256 integrity hashes:**

| File | SHA-256 |
|------|---------|
| Original artifact `BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.785+6abdba4.zip` | `2a7cbf74d26abe4765c3e662db1721b923bac39849ebfef2ca5dc7de7e2d9b7f` |
| Repackaged mod `wh40k-battlesector-bepinex6-il2cpp-be785.zip` | `272142b59450db8fedfb0951097a21afab069745eec4c2bd9b3400821bf6109a` |
| `winhttp.dll` (doorstop proxy) | `8c6cdbc38836dee87e3368f5de1994d7c0ccebf29e4ce7aba3c0981f9375412c` |
| `BepInEx/core/BepInEx.Core.dll` | `352aacc2d5356489a00891f76db28b6463c81d25bcb02f90035171a669b7e35b` |

> The repackaged mod ZIP contains the **byte-identical** files from the official
> artifact (only re-zipped so the files land at the archive root for deployment).
> You can re-download the original from the URL above and compare hashes.

**Verify on Windows (PowerShell):**

```powershell
Get-FileHash .\wh40k-battlesector-bepinex6-il2cpp-be785.zip -Algorithm SHA256
```

**Verify on Linux/WSL:**

```bash
sha256sum wh40k-battlesector-bepinex6-il2cpp-be785.zip
```

The repackaged ZIP is **not** signed by BepInEx (only the original artifact comes
from their server). If you prefer maximum trust, download the original artifact
directly from the URL above and use that instead — the file layout is the same
(everything at the archive root).

---

## 3. Package contents

The ZIP deploys these to the **game root**
(`.../steamapps/common/Warhammer 40000 Battlesector/`):

```
winhttp.dll               ← doorstop proxy (loads BepInEx at startup)
.doorstop_version
doorstop_config.ini       ← target = BepInEx\core\BepInEx.Unity.IL2CPP.dll
changelog.txt
BepInEx/
  core/                   ← BepInEx runtime (Harmony, preloader, IL2CPP loader)
  patchers/
  plugins/                ← (empty; our plugin .dll will go here later)
dotnet/                   ← bundled .NET (CoreCLR) runtime for IL2CPP
```

BepInEx generates these **itself at runtime** (they are NOT part of the mod and
should not be tracked/deployed by Vortex):

```
BepInEx/interop/          ← the game's classes as .NET assemblies (WE NEED THESE)
BepInEx/config/
BepInEx/cache/
BepInEx/LogOutput.log
```

---

## 4. Install (choose ONE method)

### Option A — Manual (simplest, recommended for this experimental step)

1. Close the game and Vortex.
2. Extract the ZIP contents **directly into the game root folder**
   (where `Warhammer40kBattlesector.exe` / the game `.exe` lives).
   When prompted, **allow overwrite** of the existing `winhttp.dll` /
   `doorstop_config.ini` (they are replaced with the matching BepInEx 6 build).
3. Confirm `winhttp.dll` and the `BepInEx/` and `dotnet/` folders are in the game
   root.

### Option B — Vortex

1. In Vortex, drag the ZIP into the Mods drop area (or Install From File).
2. Install and **Deploy**.
3. If Vortex asks about a mod type / deployment target, choose the option that
   deploys to the **game root** (not a subfolder).

> Note: because BepInEx writes files into `BepInEx/` at runtime, Vortex's
> hardlink deployment can occasionally conflict. If you hit deployment issues,
> use **Option A (manual)** for this experimental phase.

---

## 5. First run — generate the interop assemblies

1. **Launch the game normally** (Steam or the exe).
2. The **first launch will be slower than usual** — BepInEx is decompiling the
   game's IL2CPP metadata into .NET assemblies. A console window may appear.
3. Once you reach the **main menu**, you can quit.
4. Verify these were created in the game folder:
   - `BepInEx/interop/`  ← should contain many `Il2Cpp*.dll` files, incl.
     `Il2CppTMPro.dll` and `Assembly-CSharp.dll`
   - `BepInEx/LogOutput.log`

If the game **fails to launch** or crashes:
- Do **not** panic — just delete `winhttp.dll` from the game root to fully
  disable BepInEx (the game runs vanilla again).
- Share `BepInEx/LogOutput.log` so I can diagnose.

---

## 6. What I need back from you

After a successful first run, I need to read the generated **`BepInEx/interop/`**
folder (specifically `Il2CppTMPro.dll`, `Assembly-CSharp.dll`, and the
`Il2CppInterop.*` / `Il2Cppmscorlib.dll` support assemblies) to compile the
diagnostic plugin against the game's real types.

These are on your disk under the game folder; I can read them directly via WSL —
**just confirm the first run succeeded and `BepInEx/interop/` exists.**

---

## 7. Roadmap after this

| Step | Who | Output |
|------|-----|--------|
| 1. Install BepInEx + first run | You | `BepInEx/interop/` |
| 2. Compile **diagnostic** plugin | Me | `plugins/TCDiag.dll` |
| 3. Run game, open a garbled description | You | `LogOutput.log` naming the true runtime font |
| 4. Compile **fix** plugin | Me | `plugins/TCFix.dll` |
| 5. Verify TC descriptions render | You | screenshot |
| 6. Package as Vortex mod + update extension | Me | final ZIP |

---

## 8. Safety notes

- BepInEx is a widely-used, open-source (LGPL-2.1) modding framework. The binaries
  here are the official BepInEx build server artifacts (hashes above).
- Disabling is trivial: delete `winhttp.dll` from the game root.
- This does **not** modify `GameAssembly.dll` or any game file permanently — it
  loads a plugin into memory at runtime.
- The plugins I write will be **provided as source** in this repo so you can audit
  and build them yourself if you prefer.
