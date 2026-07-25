using System;
using System.Collections.Generic;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using TMPro;

namespace TCDiag
{
    // BepInEx 6 (IL2CPP) diagnostic plugin.
    [BepInPlugin(GUID, "TC Description Font Diagnostic", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcdiag";
        internal static new ManualLogSource Log;

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCDiag loaded. Auto-scans TMP CJK text every 3s; also press F8 to force a dump.");
            ClassInjector.RegisterTypeInIl2Cpp<DiagBehaviour>();
            AddComponent<DiagBehaviour>();
        }
    }

    public class DiagBehaviour : MonoBehaviour
    {
        public DiagBehaviour(IntPtr ptr) : base(ptr) { }

        private float _timer;
        private readonly HashSet<string> _seen = new HashSet<string>();
        private readonly HashSet<string> _fbLogged = new HashSet<string>();
        private static readonly int[] SampleCps = { 0x5C07 /*將*/, 0x9818 /*領*/, 0x9060 /*遠*/, 0x773E /*眾*/, 0x5728 /*在*/ };

        private void Update()
        {
            // Manual trigger (legacy input may be disabled; wrapped in try/catch).
            try
            {
                if (Input.GetKeyDown(KeyCode.F8))
                {
                    _seen.Clear();
                    Scan(true);
                    return;
                }
            }
            catch { /* new input system — ignore */ }

            _timer += Time.deltaTime;
            if (_timer >= 3f)
            {
                _timer = 0f;
                Scan(false);
            }
        }

        private static bool HasCjk(string s)
        {
            if (string.IsNullOrEmpty(s)) return false;
            foreach (char c in s)
                if (c >= 0x3400 && c <= 0x9FFF) return true;
            return false;
        }

        private void Scan(bool force)
        {
            TMP_Text[] all;
            try { all = Resources.FindObjectsOfTypeAll<TMP_Text>(); }
            catch (Exception e) { Plugin.Log.LogError("FindObjectsOfTypeAll<TMP_Text> failed: " + e.Message); return; }
            if (all == null) return;

            for (int i = 0; i < all.Length; i++)
            {
                TMP_Text t = all[i];
                if (t == null) continue;
                string text;
                try { text = t.text; } catch { continue; }
                if (!HasCjk(text)) continue;

                string goName;
                try { goName = t.gameObject.name; } catch { goName = "?"; }

                // dedup by (object name + first 12 chars of text)
                string key = goName + "|" + (text.Length > 12 ? text.Substring(0, 12) : text);
                if (!force && !_seen.Add(key)) continue;
                if (force) _seen.Add(key);

                DumpOne(t, goName, text);
            }
        }

        private void DumpOne(TMP_Text t, string goName, string text)
        {
            var log = Plugin.Log;
            try
            {
                string preview = text.Length > 40 ? text.Substring(0, 40) : text;
                log.LogInfo("==== TMP CJK text ==== GO='" + goName + "' text='" + preview + "'");

                TMP_FontAsset f = t.font;
                if (f == null) { log.LogInfo("   font = NULL (uses default)"); }
                else
                {
                    string fn = SafeName(f);
                    int pop = -1; try { pop = (int)f.atlasPopulationMode; } catch { }
                    int chars = -1; try { chars = f.characterTable.Count; } catch { }
                    log.LogInfo("   font='" + fn + "' pop=" + pop + " chars=" + chars);

                    // Sample TC-specific glyphs (the exact garbled ones) — does the runtime font resolve them?
                    foreach (int cp in SampleCps)
                    {
                        bool has = false;
                        try { has = f.HasCharacter(cp); } catch { }
                        log.LogInfo("      U+" + cp.ToString("X4") + " HasCharacter=" + has);
                    }

                    // Fallback chain — log once per font name to reveal what provides CJK.
                    if (_fbLogged.Add(fn))
                    {
                        try
                        {
                            var fb = f.fallbackFontAssetTable;
                            if (fb != null && fb.Count > 0)
                                for (int k = 0; k < fb.Count; k++)
                                    LogCoverage("   [" + fn + "] fallback[" + k + "]", fb[k]);
                            else
                                log.LogInfo("   [" + fn + "] no local fallback table");
                        }
                        catch (Exception e) { log.LogInfo("   fallback read err: " + e.Message); }
                        try
                        {
                            var g = TMP_Settings.fallbackFontAssets;
                            if (g != null && g.Count > 0)
                                for (int k = 0; k < g.Count; k++)
                                    LogCoverage("   GLOBAL fallback[" + k + "]", g[k]);
                            else
                                log.LogInfo("   GLOBAL fallback: (empty)");
                        }
                        catch (Exception e) { log.LogInfo("   global fallback read err: " + e.Message); }
                    }
                }

                // Material + main texture actually sampled
                try
                {
                    Material m = t.fontSharedMaterial;
                    if (m == null) log.LogInfo("   sharedMaterial = NULL");
                    else
                    {
                        Texture tex = m.mainTexture;
                        string tn = tex != null ? tex.name : "null";
                        int tw = tex != null ? tex.width : -1, th = tex != null ? tex.height : -1;
                        log.LogInfo("   material='" + SafeName(m) + "' mainTex='" + tn + "' " + tw + "x" + th);
                    }
                }
                catch (Exception e) { log.LogInfo("   material read err: " + e.Message); }
            }
            catch (Exception e) { log.LogError("DumpOne err: " + e.Message); }
        }

        private static string SafeName(UnityEngine.Object o)
        {
            try { return o.name; } catch { return "?"; }
        }

        private static void LogCoverage(string label, TMP_FontAsset f)
        {
            var log = Plugin.Log;
            if (f == null) { log.LogInfo(label + " = null"); return; }
            string nm = SafeName(f);
            int pop = -1; try { pop = (int)f.atlasPopulationMode; } catch { }
            int chars = -1; try { chars = f.characterTable.Count; } catch { }
            bool has5C07 = false, has5728 = false;
            try { has5C07 = f.HasCharacter(0x5C07); } catch { }
            try { has5728 = f.HasCharacter(0x5728); } catch { }
            log.LogInfo(label + " '" + nm + "' pop=" + pop + " chars=" + chars +
                        " 將=" + has5C07 + " 在=" + has5728);
        }
    }
}
