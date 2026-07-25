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
    // BepInEx 6 (IL2CPP) diagnostic: capture every ON-SCREEN TMP text whose font
    // cannot render one of its CJK characters (i.e. every gibberish instance), so
    // the culprit fonts can be identified. Does NOT swap fonts (so the true runtime
    // font is observed). Deduplicated + capped to stay light over a long session.
    //
    // Grep the log for "[TCGIB]" to get one line per distinct gibberish instance.
    [BepInPlugin(GUID, "TC Gibberish Scanner", "2.0.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcdiag";
        internal static new ManualLogSource Log;

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCDiag 2.0 loaded. Scanning on-screen CJK text for missing-glyph gibberish every 1s. Grep '[TCGIB]'.");
            ClassInjector.RegisterTypeInIl2Cpp<DiagBehaviour>();
            AddComponent<DiagBehaviour>();
        }
    }

    public class DiagBehaviour : MonoBehaviour
    {
        public DiagBehaviour(IntPtr ptr) : base(ptr) { }

        private float _timer;
        private float _hbTimer;
        private int _distinct;
        private const int MaxDistinct = 1200;    // hard cap so we never flood
        private readonly HashSet<string> _seen = new HashSet<string>();

        private void Update()
        {
            _timer += Time.deltaTime;
            _hbTimer += Time.deltaTime;
            if (_hbTimer >= 30f)
            {
                _hbTimer = 0f;
                Plugin.Log.LogInfo("[TCHB] distinct gibberish instances so far: " + _distinct);
            }
            if (_timer < 1f) return;
            _timer = 0f;
            if (_distinct >= MaxDistinct) return;
            Scan();
        }

        private static bool IsCjk(int c)
        {
            return (c >= 0x3400 && c <= 0x9FFF) || (c >= 0xF900 && c <= 0xFAFF);
        }

        private void Scan()
        {
            TMP_Text[] all;
            try { all = Resources.FindObjectsOfTypeAll<TMP_Text>(); }
            catch (Exception e) { Plugin.Log.LogError("scan failed: " + e.Message); return; }
            if (all == null) return;

            for (int i = 0; i < all.Length && _distinct < MaxDistinct; i++)
            {
                TMP_Text t = all[i];
                if (t == null) continue;

                // Only text actually shown on screen.
                bool active;
                try { active = t.isActiveAndEnabled && t.gameObject.activeInHierarchy; }
                catch { continue; }
                if (!active) continue;

                string text;
                try { text = t.text; } catch { continue; }
                if (string.IsNullOrEmpty(text)) continue;

                // Find the first CJK char the font cannot render (own table).
                TMP_FontAsset f;
                try { f = t.font; } catch { continue; }

                int missCp = -1;
                for (int k = 0; k < text.Length; k++)
                {
                    int c = text[k];
                    if (!IsCjk(c)) continue;
                    bool has = false;
                    if (f != null)
                    {
                        try { has = f.HasCharacter(c); } catch { has = false; }
                    }
                    if (!has) { missCp = c; break; }
                }
                if (missCp < 0) continue; // renders fine (or no CJK) — not gibberish

                string fontName = f != null ? SafeName(f) : "<NULL>";
                string goName;
                try { goName = t.gameObject.name; } catch { goName = "?"; }

                string key = fontName + "|" + goName + "|" + missCp;
                if (!_seen.Add(key)) continue; // already logged this instance
                _distinct++;

                int pop = -1, chars = -1;
                if (f != null)
                {
                    try { pop = (int)f.atlasPopulationMode; } catch { }
                    try { chars = f.characterTable.Count; } catch { }
                }
                string matName = "?"; int tw = -1, th = -1;
                try
                {
                    Material m = t.fontSharedMaterial;
                    if (m != null)
                    {
                        matName = SafeName(m);
                        Texture tex = m.mainTexture;
                        if (tex != null) { tw = tex.width; th = tex.height; }
                    }
                }
                catch { }

                string preview = text.Length > 24 ? text.Substring(0, 24) : text;
                preview = preview.Replace("\n", " ").Replace("\r", " ");
                Plugin.Log.LogInfo(
                    "[TCGIB] go='" + goName + "' font='" + fontName + "' pop=" + pop +
                    " ownChars=" + chars + " miss=U+" + missCp.ToString("X4") + " '" + (char)missCp +
                    "' mat='" + matName + "' tex=" + tw + "x" + th + " text='" + preview + "'");
            }
        }

        private static string SafeName(UnityEngine.Object o)
        {
            try { return o.name; } catch { return "?"; }
        }
    }
}
