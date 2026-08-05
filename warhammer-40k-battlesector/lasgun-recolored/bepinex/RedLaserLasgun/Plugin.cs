using System;
using System.Collections.Generic;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using UnityEngine.Rendering;
using WeaponEffects;

namespace RedLaserLasgun
{
    // BepInEx 6 (IL2CPP) runtime plugin. Renders the Astra Militarum lasgun as a
    // glowing RED laser beam with ZERO side effects on other weapons.
    //
    // Detection & positions: a per-frame scan of active ProjectileEffect instances
    // named "LasGun". When one first becomes active it exposes transform.position
    // (muzzle) and FinalPosition (target) — both validated in-game. (A Harmony hook
    // on set_EndPoint was tried but fires before the projectile is placed at the
    // muzzle, so beams drew from the world origin — the scan is the reliable path.)
    //
    // Rendering: two additive, camera-facing LineRenderers per shot (a bright thin
    // core + a wide dim halo) using the built-in "Hidden/Internal-Colored" shader,
    // which is always present in a player build (Shader.Find for particle shaders
    // returns null there — stripped — which showed as magenta). Colour is HDR red
    // via the material and per-LineRenderer vertex colours; the material is created
    // by this plugin, so no shared game asset is touched.
    //
    // Scope: effects whose name contains "LasGun" (all AM las weapons). Optionally
    // hides the flying bolt (HideBolt) each frame while it is active.
    //
    // Tunable live via BepInEx/config/com.crystalmods.redlaserlasgun.cfg.
    [BepInPlugin(GUID, "Red Laser Lasgun", "1.1.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.redlaserlasgun";
        internal static new ManualLogSource Log;

        internal static ConfigEntry<float> Width;
        internal static ConfigEntry<float> GlowWidthMul;
        internal static ConfigEntry<float> Duration;
        internal static ConfigEntry<float> ColR, ColG, ColB;
        internal static ConfigEntry<float> Glow;
        internal static ConfigEntry<bool> HideBolt;

        public override void Load()
        {
            Log = base.Log;
            Width = Config.Bind("Beam", "Width", 0.35f, "Bright core width (world units).");
            GlowWidthMul = Config.Bind("Beam", "GlowWidthMul", 3.5f, "Outer glow halo width as a multiple of the core width.");
            Duration = Config.Bind("Beam", "Duration", 0.13f, "Seconds the beam stays before fading out.");
            HideBolt = Config.Bind("Beam", "HideBolt", true, "Hide the original flying las-bolt so only the beam shows.");
            ColR = Config.Bind("Color", "R", 1.00f, "Beam red   (0..1).");
            ColG = Config.Bind("Color", "G", 0.10f, "Beam green (0..1).");
            ColB = Config.Bind("Color", "B", 0.10f, "Beam blue  (0..1).");
            Glow = Config.Bind("Color", "Glow", 3.0f, "Intensity multiplier (additive brightness / bloom).");

            Log.LogInfo("RedLaserLasgun 1.1 loaded (scan + Internal-Colored additive beam).");
            ClassInjector.RegisterTypeInIl2Cpp<LaserBehaviour>();
            AddComponent<LaserBehaviour>();
        }
    }

    public class LaserBehaviour : MonoBehaviour
    {
        public LaserBehaviour(IntPtr ptr) : base(ptr) { }

        internal static LaserBehaviour Instance;

        private class Beam { public GameObject go; public LineRenderer core; public LineRenderer glow; public float born; }
        private readonly List<Beam> _beams = new List<Beam>();

        private readonly HashSet<int> _drawn = new HashSet<int>();   // drew a beam for this activation
        private Material _mat;
        private bool _matReady;

        private void Awake() { Instance = this; }

        private void Update()
        {
            FadeBeams();
            Scan();
        }

        private void Scan()
        {
            Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<ProjectileEffect> all;
            try { all = Resources.FindObjectsOfTypeAll<ProjectileEffect>(); }
            catch { return; }
            if (all == null) return;

            for (int i = 0; i < all.Count; i++)
            {
                ProjectileEffect p = all[i];
                if (p == null) continue;
                string name;
                try { name = p.gameObject.name; } catch { continue; }
                if (name.IndexOf("LasGun", StringComparison.OrdinalIgnoreCase) < 0) continue;

                bool active;
                try { active = p.isActiveAndEnabled && p.gameObject.activeInHierarchy; } catch { continue; }
                int id;
                try { id = p.GetInstanceID(); } catch { continue; }

                if (!active) { _drawn.Remove(id); continue; }

                if (Plugin.HideBolt.Value) HideBoltRenderers(p);   // keep hidden every active frame

                if (_drawn.Contains(id)) continue;                 // one beam per activation
                Vector3 a, b;
                try { a = p.transform.position; } catch { continue; }
                try { b = p.FinalPosition; } catch { continue; }
                if (b == Vector3.zero) continue;                   // target not ready — retry (don't mark)
                EnsureMaterial();
                SpawnBeam(a, b);
                _drawn.Add(id);
            }
        }

        private void FadeBeams()
        {
            float dur = Mathf.Max(0.02f, Plugin.Duration.Value);
            for (int i = _beams.Count - 1; i >= 0; i--)
            {
                Beam bm = _beams[i];
                float age = Time.time - bm.born;
                if (bm.go == null || age >= dur)
                {
                    if (bm.go != null) Destroy(bm.go);
                    _beams.RemoveAt(i);
                    continue;
                }
                float a = 1f - age / dur;
                Color core = Rgb(a);
                Color glow = Rgb(a * 0.45f);
                try { bm.core.startColor = core; bm.core.endColor = core; } catch { }
                try { bm.glow.startColor = glow; bm.glow.endColor = glow; } catch { }
            }
        }

        private Color Rgb(float alpha)
        {
            float g = Mathf.Max(1f, Plugin.Glow.Value);
            return new Color(Plugin.ColR.Value * g, Plugin.ColG.Value * g, Plugin.ColB.Value * g, alpha);
        }

        private void SpawnBeam(Vector3 a, Vector3 b)
        {
            GameObject parent;
            try { parent = new GameObject("RedLaserLasgunBeam"); } catch { return; }
            float w = Mathf.Max(0.02f, Plugin.Width.Value);
            LineRenderer glow = MakeLine(parent, a, b, w * Mathf.Max(1f, Plugin.GlowWidthMul.Value), Rgb(0.45f));
            LineRenderer core = MakeLine(parent, a, b, w, Rgb(1f));
            if (core == null && glow == null) { Destroy(parent); return; }
            _beams.Add(new Beam { go = parent, core = core, glow = glow, born = Time.time });
        }

        private LineRenderer MakeLine(GameObject parent, Vector3 a, Vector3 b, float width, Color col)
        {
            GameObject g;
            try { g = new GameObject("line"); g.transform.SetParent(parent.transform, false); } catch { return null; }
            LineRenderer lr;
            try { lr = g.AddComponent<LineRenderer>(); } catch { Destroy(g); return null; }
            try
            {
                if (_mat != null) lr.material = _mat;
                lr.useWorldSpace = true;
                lr.alignment = LineAlignment.View;
                lr.positionCount = 2;
                lr.SetPosition(0, a);
                lr.SetPosition(1, b);
                lr.widthCurve = TipTaper(width);
                lr.numCapVertices = 8;
                lr.numCornerVertices = 4;
                lr.shadowCastingMode = ShadowCastingMode.Off;
                lr.receiveShadows = false;
                lr.allowOcclusionWhenDynamic = false;
                lr.startColor = col; lr.endColor = col;
            }
            catch { Destroy(g); return null; }
            return lr;
        }

        private void HideBoltRenderers(ProjectileEffect p)
        {
            try
            {
                var rs = p.gameObject.GetComponentsInChildren<Renderer>(true);
                if (rs == null) return;
                for (int i = 0; i < rs.Count; i++)
                {
                    Renderer r = rs[i];
                    if (r == null) continue;
                    try { r.enabled = false; } catch { }
                }
            }
            catch { }
        }

        private static AnimationCurve TipTaper(float w)
        {
            AnimationCurve ac = new AnimationCurve();
            ac.AddKey(0.00f, w * 0.20f);
            ac.AddKey(0.06f, w);
            ac.AddKey(0.94f, w);
            ac.AddKey(1.00f, w * 0.20f);
            return ac;
        }

        // Built-in "Hidden/Internal-Colored" is always present in a player build and
        // renders material colour * vertex colour. Configure it for additive glow.
        // Plugin-owned material -> zero side effects.
        private void EnsureMaterial()
        {
            if (_matReady) return;
            _matReady = true;
            try
            {
                Shader sh = null;
                try { sh = Shader.Find("Hidden/Internal-Colored"); } catch { }
                if (sh == null) try { sh = Shader.Find("Sprites/Default"); } catch { }
                if (sh == null) try { sh = Shader.Find("Unlit/Color"); } catch { }
                if (sh != null)
                {
                    _mat = new Material(sh);
                    try { _mat.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha); } catch { }
                    try { _mat.SetInt("_DstBlend", (int)BlendMode.One); } catch { }   // additive
                    try { _mat.SetInt("_ZWrite", 0); } catch { }
                    try { _mat.SetInt("_Cull", (int)CullMode.Off); } catch { }
                    try { _mat.SetInt("_ZTest", (int)CompareFunction.LessEqual); } catch { }
                    try { _mat.color = Rgb(1f); } catch { }
                    _mat.renderQueue = 3000;                       // draw with transparents
                }
                Plugin.Log.LogInfo("Beam shader = " + (sh != null ? sh.name : "<none>"));
            }
            catch (Exception e) { Plugin.Log.LogWarning("material build failed: " + e.Message); }
        }
    }
}
