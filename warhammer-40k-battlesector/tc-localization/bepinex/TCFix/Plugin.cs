using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using TMPro;

namespace TCFix
{
    // BepInEx 6 (IL2CPP) runtime fix. Several fonts render Traditional-Chinese text
    // incorrectly: the built-in futura variants "... - No Underlay" (static, 124
    // Latin glyphs) and "... - with shadow" (dynamic, ~91 glyphs) have no real CJK
    // coverage and produce garbled output via broken fallback / dynamic generation.
    // This plugin finds on-screen TMP text that contains CJK but is drawn with a
    // font that has only a small character table (i.e. not a full-CJK font) and
    // swaps it to the full-Traditional font "futura medium condensed bt SDF" (785,
    // ~3636 glyphs), which renders correct Traditional Chinese.
    //
    // Note: HasCharacter() searches fallbacks and returns true even for these broken
    // fonts, so it CANNOT be used to detect the problem. The reliable signal is the
    // font's own characterTable size (full-CJK fonts have thousands of glyphs).
    [BepInPlugin(GUID, "TC Font Fix", "1.2.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcfix";
        internal static new ManualLogSource Log;

        // Target (working, full-Traditional) font asset name.
        internal const string GoodFontName = "futura medium condensed bt SDF";
        // A font with at least this many glyphs is treated as a real CJK font and
        // left alone; anything smaller that draws CJK is swapped.
        internal const int FullCjkMinChars = 3000;

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCFix 1.2.0 loaded. Swapping CJK text on partial fonts (<" + FullCjkMinChars + " glyphs) -> '" + GoodFontName + "'.");
            ClassInjector.RegisterTypeInIl2Cpp<FixBehaviour>();
            AddComponent<FixBehaviour>();
        }
    }

    public class FixBehaviour : MonoBehaviour
    {
        public FixBehaviour(IntPtr ptr) : base(ptr) { }

        // Scan ~10x/second so a newly-shown modal is corrected within ~0.1s (no
        // visible 1-second gibberish flash) while keeping cost reasonable.
        private const float ScanInterval = 0.1f;

        private TMP_FontAsset _good;
        private float _timer;
        private int _swaps;

        private void Update()
        {
            if (_good == null)
            {
                _good = FindGoodFont();
                if (_good == null) return;
                Plugin.Log.LogInfo("Found target font '" + _good.name + "' chars=" + SafeChars(_good));
            }

            _timer += Time.deltaTime;
            if (_timer < ScanInterval) return;
            _timer = 0f;

            // Use FindObjectsOfTypeAll (proven reliable in this Il2CppInterop build);
            // filter to on-screen components ourselves.
            TMP_Text[] all;
            try { all = Resources.FindObjectsOfTypeAll<TMP_Text>(); }
            catch { return; }
            if (all == null) return;

            for (int i = 0; i < all.Length; i++)
            {
                TMP_Text t = all[i];
                if (t == null) continue;

                bool active;
                try { active = t.isActiveAndEnabled && t.gameObject.activeInHierarchy; }
                catch { continue; }
                if (!active) continue;

                TMP_FontAsset f;
                try { f = t.font; } catch { continue; }
                if (f != null && ReferenceEquals(f, _good)) continue;      // already good
                if (f != null && SafeChars(f) >= Plugin.FullCjkMinChars) continue; // real CJK font

                string text;
                try { text = t.text; } catch { continue; }
                if (!HasCjk(text)) continue;                                // only CJK text

                try
                {
                    string oldName = f != null ? SafeName(f) : "<NULL>";
                    t.font = _good;
                    t.SetAllDirty();
                    t.ForceMeshUpdate(false, false);
                    _swaps++;
                    if (_swaps <= 40 || _swaps % 100 == 0)
                        Plugin.Log.LogInfo("Swapped GO='" + SafeName(t) + "' (was font '" + oldName + "') total=" + _swaps);
                }
                catch (Exception e) { Plugin.Log.LogWarning("swap err: " + e.Message); }
            }
        }

        private static bool HasCjk(string s)
        {
            if (string.IsNullOrEmpty(s)) return false;
            for (int i = 0; i < s.Length; i++)
            {
                int c = s[i];
                if ((c >= 0x3400 && c <= 0x9FFF) || (c >= 0xF900 && c <= 0xFAFF)) return true;
            }
            return false;
        }

        private static TMP_FontAsset FindGoodFont()
        {
            TMP_FontAsset[] fonts;
            try { fonts = Resources.FindObjectsOfTypeAll<TMP_FontAsset>(); }
            catch { return null; }
            if (fonts == null) return null;
            for (int i = 0; i < fonts.Length; i++)
            {
                TMP_FontAsset f = fonts[i];
                if (f == null) continue;
                string n; try { n = f.name; } catch { continue; }
                if (n != Plugin.GoodFontName) continue;
                if (SafeChars(f) >= Plugin.FullCjkMinChars) return f; // the full-TC instance
            }
            return null;
        }

        private static int SafeChars(TMP_FontAsset f)
        {
            try { return f.characterTable.Count; } catch { return -1; }
        }

        private static string SafeName(UnityEngine.Object o)
        {
            try { return o.name; } catch { return "?"; }
        }
    }
}
