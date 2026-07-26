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
    // BepInEx 6 (IL2CPP) diagnostic v3: log EVERY distinct on-screen TMP text that
    // contains CJK, with its font's full properties, so garbling screens can be
    // identified even when the font *passes* HasCharacter (dynamic-font garble or
    // wrong atlas/material). Does NOT swap fonts. Deduped by (font|GameObject) and
    // capped so it stays light over a long session.
    //
    // Grep the log for "[TCTEXT]" — one line per distinct (font, object) pair:
    //   [TCTEXT] go='..' font='..' pop=N chars=M atlas=WxH mat='..' firstCjk=U+XXXX
    //            has=T/F anyMiss=T/F text='..'
    // pop: 0 = static (uses pre-baked atlas), 1 = dynamic (runtime glyph gen — the
    //      usual garble source). anyMiss=T means the font's own table lacks a CJK char.
    [BepInPlugin(GUID, "TC Gibberish Scanner", "3.0.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.tcdiag";
        internal static new ManualLogSource Log;

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("TCDiag 3.0 loaded. Logging every on-screen CJK text + its font props every 1s. Grep '[TCTEXT]'.");
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
        private const int MaxDistinct = 1500;   // hard cap so we never flood
        private readonly HashSet<string> _seen = new HashSet<string>();

        private void Update()
        {
            _timer += Time.deltaTime;
            _hbTimer += Time.deltaTime;
            if (_hbTimer >= 30f)
            {
                _hbTimer = 0f;
                Plugin.Log.LogInfo("[TCHB] distinct CJK text objects so far: " + _distinct);
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

                bool active;
                try { active = t.isActiveAndEnabled && t.gameObject.activeInHierarchy; }
                catch { continue; }
                if (!active) continue;

                string text;
                try { text = t.text; } catch { continue; }
                if (string.IsNullOrEmpty(text)) continue;

                // First CJK char + whether ANY CJK char is missing from the font's own table.
                TMP_FontAsset f;
                try { f = t.font; } catch { continue; }

                int firstCjk = -1;
                bool anyMiss = false;
                int checkedCount = 0;
                for (int k = 0; k < text.Length; k++)
                {
                    int c = text[k];
                    if (!IsCjk(c)) continue;
                    if (firstCjk < 0) firstCjk = c;
                    bool has = false;
                    if (f != null) { try { has = f.HasCharacter(c); } catch { has = false; } }
                    if (!has) { anyMiss = true; break; }
                    if (++checkedCount >= 24) break;
                }
                if (firstCjk < 0) continue; // no CJK in this text

                string fontName = f != null ? SafeName(f) : "<NULL>";
                string goName;
                try { goName = t.gameObject.name; } catch { goName = "?"; }

                string key = fontName + "|" + goName;
                if (!_seen.Add(key)) continue;
                _distinct++;

                int pop = -1, chars = -1;
                bool hasFirst = false;
                if (f != null)
                {
                    try { pop = (int)f.atlasPopulationMode; } catch { }
                    try { chars = f.characterTable.Count; } catch { }
                    try { hasFirst = f.HasCharacter(firstCjk); } catch { }
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
                    "[TCTEXT] go='" + goName + "' font='" + fontName + "' pop=" + pop +
                    " chars=" + chars + " atlas=" + tw + "x" + th + " mat='" + matName +
                    "' firstCjk=U+" + firstCjk.ToString("X4") + " '" + (char)firstCjk +
                    "' has=" + hasFirst + " anyMiss=" + anyMiss + " text='" + preview + "'");
            }
        }

        private static string SafeName(UnityEngine.Object o)
        {
            try { return o.name; } catch { return "?"; }
        }
    }
}
