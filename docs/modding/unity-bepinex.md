# Unity modding & BepInEx (stub)

> Status: **stub** — fill out as we ship Unity-based mods.

## References

- BepInEx docs — <https://docs.bepinex.dev/>
- BepInEx releases — <https://github.com/BepInEx/BepInEx/releases>
- BepInEx IL2CPP (BepInEx 6) — <https://docs.bepinex.dev/articles/advanced/il2cpp.html>
- HarmonyX (patching) — <https://github.com/BepInEx/HarmonyX>
- Unity Mono runtime overview — <https://docs.unity3d.com/Manual/Mono.html>
- Unity IL2CPP overview — <https://docs.unity3d.com/Manual/IL2CPP.html>
- AssetRipper (asset extraction) — <https://github.com/AssetRipper/AssetRipper>
- UABEA / AssetsTools.NET — <https://github.com/nesrak1/UABEA>
- UnityExplorer (runtime inspector) — <https://github.com/sinai-dev/UnityExplorer>

## Detect the Unity runtime first

| Indicator | Runtime |
| --- | --- |
| `GameDir/<Game>_Data/Managed/*.dll` present | **Mono** (pre-IL2CPP) |
| `GameDir/<Game>_Data/il2cpp_data/` present | **IL2CPP** |
| `UnityPlayer.dll` version string | Unity major version |

`il2cpp_data` + `GameAssembly.dll` ⇒ use **BepInEx 6 IL2CPP** (with
`Il2CppInterop`). Otherwise use **BepInEx 5 (Mono)**.

## BepInEx install (manual)

1. Match the bitness (x64 today is universal) and runtime (Mono vs IL2CPP).
2. Unzip into the game root next to the main executable.
3. Run the game once — BepInEx generates `BepInEx/config/BepInEx.cfg` and
   `BepInEx/plugins/` (or `interop/` for IL2CPP).
4. Drop plugin `.dll`s into `BepInEx/plugins/`.

## Plugin skeleton (BepInEx 5, Mono)

```csharp
[BepInPlugin("crystal.<game>.<mod>", "Crystal <Mod>", "1.0.0")]
public class Plugin : BaseUnityPlugin {
    void Awake() {
        Logger.LogInfo("Crystal <Mod> loaded.");
        Harmony.CreateAndPatchAll(typeof(Patches));
    }
}

static class Patches {
    [HarmonyPatch(typeof(SomeGameClass), nameof(SomeGameClass.SomeMethod))]
    [HarmonyPrefix]
    static bool Prefix(/*…*/) { /*…*/ return true; }
}
```

## IL2CPP specifics (BepInEx 6 + Il2CppInterop)

- First launch dumps interop assemblies under `BepInEx/interop/`.
- Reference those interop DLLs from your plugin project, **not** the
  game's `il2cpp_data`.
- Hooks via `Il2CppInterop.Runtime.Injection.ClassInjector` or HarmonyX.

## Unity version & Unity 6 notes

- Unity 5 / 2017–2021 → Mono, BepInEx 5 path.
- Unity 2022+ → mostly IL2CPP for shipped games; BepInEx 6.
- Unity 6 (2024+) — same IL2CPP toolchain; verify BepInEx 6 IL2CPP support
  per-game and watch for `il2cpp_data/Metadata/global-metadata.dat` format
  changes. Use the latest BepInEx 6 prerelease and Il2CppInterop.

## Asset extraction toolbox

| Tool | Use for |
| --- | --- |
| AssetRipper | Bulk extract scenes, prefabs, scripts back to a Unity project |
| UABEA | Surgical edit of single assets in `.assets` / bundles |
| AssetStudio (fork) | Read-only inspection, texture / model export |
| UnityExplorer | Live runtime inspection inside the game |

## TODO

- ConfigEntry / ConfigFile examples.
- HarmonyX vs Harmony 2 quirks.
- Plugin project template (csproj targeting `netstandard2.1`).
- Distribution: r2modman / Thunderstore for community managers.
