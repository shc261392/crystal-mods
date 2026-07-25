using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using TMPro;

namespace TCFix
{
    // BepInEx 6 (IL2CPP) runtime fix: swap the CJK-less description font
    // "futura medium condensed bt SDF - No Underlay" (renders TC garbled via a
    // broken fallback chain) to the working full-TC font
    // "futura medium condensed bt SDF" on all affected TMP_Text components.
    [BepInPlugin(GUID, "TC Description Font Fix", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcfix";
        internal static new ManualLogSource Log;

        // Source (broken) and target (working) font asset names.
        internal const string BrokenFontName = "futura medium condensed bt SDF - No Underlay";
        internal const string GoodFontName = "futura medium condensed bt SDF";

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCFix loaded. Swapping '" + BrokenFontName + "' -> '" + GoodFontName + "' on TMP text.");
            ClassInjector.RegisterTypeInIl2Cpp<FixBehaviour>();
            AddComponent<FixBehaviour>();
        }
    }

    public class FixBehaviour : MonoBehaviour
    {
        public FixBehaviour(IntPtr ptr) : base(ptr) { }

        private TMP_FontAsset _good;
        private float _timer;
        private int _swaps;

        private void Update()
        {
            _timer += Time.deltaTime;
            if (_timer < 1.0f) return;
            _timer = 0f;

            if (_good == null)
            {
                _good = FindGoodFont();
                if (_good == null) return;
                Plugin.Log.LogInfo("Found target font '" + _good.name + "' chars=" + SafeChars(_good));
            }

            TMP_Text[] all;
            try { all = Resources.FindObjectsOfTypeAll<TMP_Text>(); }
            catch { return; }
            if (all == null) return;

            for (int i = 0; i < all.Length; i++)
            {
                TMP_Text t = all[i];
                if (t == null) continue;
                TMP_FontAsset f;
                try { f = t.font; } catch { continue; }
                if (f == null) continue;
                string fn;
                try { fn = f.name; } catch { continue; }
                if (fn != Plugin.BrokenFontName) continue;

                try
                {
                    t.font = _good;
                    // Force a re-layout/re-render with the new font.
                    t.SetAllDirty();
                    t.ForceMeshUpdate(false, false);
                    _swaps++;
                    if (_swaps <= 20 || _swaps % 50 == 0)
                        Plugin.Log.LogInfo("Swapped font on GO='" + SafeName(t) + "' (total " + _swaps + ")");
                }
                catch (Exception e) { Plugin.Log.LogWarning("swap err: " + e.Message); }
            }
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
                if (SafeChars(f) > 3000) return f; // the full-TC instance
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
