using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using TMPro;

namespace TCFix
{
    // BepInEx 6 (IL2CPP) runtime fix. Several screens render Traditional-Chinese
    // text through fonts that lack the Traditional-specific glyphs (the built-in
    // "futura ... No Underlay" description font, plus modal/zone-modifier fonts),
    // producing garbled output. This plugin scans on-screen TMP text and, for any
    // text whose current font cannot render one of its CJK characters, swaps that
    // text to the full-Traditional font "futura medium condensed bt SDF" (785).
    [BepInPlugin(GUID, "TC Font Fix", "1.1.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcfix";
        internal static new ManualLogSource Log;

        // Target (working, full-Traditional) font asset name.
        internal const string GoodFontName = "futura medium condensed bt SDF";

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCFix 1.1.0 loaded. Swapping any CJK text whose font lacks the glyphs -> '" + GoodFontName + "'.");
            ClassInjector.RegisterTypeInIl2Cpp<FixBehaviour>();
            AddComponent<FixBehaviour>();
        }
    }

    public class FixBehaviour : MonoBehaviour
    {
        public FixBehaviour(IntPtr ptr) : base(ptr) { }

        // Scan active text ~20x/second so a newly-shown modal is corrected within
        // a frame or two (no visible 1-second gibberish flash) while keeping cost low.
        private const float ScanInterval = 0.05f;

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

            // Active scene text only (cheaper than FindObjectsOfTypeAll and exactly
            // what is on screen).
            TMP_Text[] all;
            try { all = UnityEngine.Object.FindObjectsOfType<TMP_Text>(); }
            catch { return; }
            if (all == null) return;

            for (int i = 0; i < all.Length; i++)
            {
                TMP_Text t = all[i];
                if (t == null) continue;
                TMP_FontAsset f;
                try { f = t.font; } catch { continue; }
                if (f == null || ReferenceEquals(f, _good)) continue;

                string text;
                try { text = t.text; } catch { continue; }
                if (!FontMissesCjk(f, text)) continue;

                try
                {
                    string oldName = SafeName(f);
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

        // True if the text contains at least one CJK character that the font's own
        // character table cannot render (so it would garble / fall back badly).
        private static bool FontMissesCjk(TMP_FontAsset f, string text)
        {
            if (string.IsNullOrEmpty(text)) return false;
            int checkedCount = 0;
            for (int i = 0; i < text.Length; i++)
            {
                int c = text[i];
                bool cjk = (c >= 0x3400 && c <= 0x9FFF) || (c >= 0xF900 && c <= 0xFAFF);
                if (!cjk) continue;
                bool has;
                try { has = f.HasCharacter(c); } catch { return false; }
                if (!has) return true;
                if (++checkedCount >= 32) break; // cap work per text object
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
