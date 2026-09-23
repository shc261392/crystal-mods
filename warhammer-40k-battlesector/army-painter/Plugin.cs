using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using UnityEngine.Rendering;
using Units;

namespace ArmyPainter
{
    // BepInEx 6 (IL2CPP) runtime plugin. "Army Painter": recolors the local
    // player's army paint scheme (primary + secondary colours) at runtime and
    // provides an in-game colour-changing UI (IMGUI).
    //
    // Rendering facts (verified from game assets + decompiled Assembly-CSharp):
    //   * Unit models use the "BlackLab/Standard" shader. Faction paint is BAKED
    //     into the albedo (_MainTex); _Color is white on units. _EmissionMap /
    //     _EmissionColor (HDR) drive glowing bits and are left untouched.
    //   * The game itself does per-renderer overrides with MaterialPropertyBlock
    //     (RendererMaterialModifier), so we use MPB too: no shared game asset is
    //     ever mutated and the whole paint job is reversible.
    //   * Player ownership: TeamManager -> ContestantBase (ContestantType ==
    //     LocalPlayer) -> UnitList. Unit models are spawned per faction bundle;
    //     renderers are found under the Unit's transform / AnimatedCharacter.
    //
    // Recolor: per unique albedo texture, auto-detect the top-2 saturated colour
    // clusters (primary/secondary), then remap pixels near those hues toward the
    // chosen colours while preserving luminance (baked shading) and leaving
    // near-neutral metal/grime pixels untouched. Results are cached per
    // (texture, target colours).
    [BepInPlugin(GUID, "Army Painter", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.armypainter";
        public const string Version = "1.0.0";
        internal static new ManualLogSource Log;

        // ---- UI toggles -----------------------------------------------------
        internal static ConfigEntry<int> ToggleKey;          // F10
        internal static ConfigEntry<bool> ShowButton;        // always-visible toggle button
        // ---- Paint behaviour -------------------------------------------------
        internal static ConfigEntry<bool> AutoApply;         // repaint new units automatically
        internal static ConfigEntry<float> HueWindow;        // hue distance accepted for remap
        internal static ConfigEntry<float> SatThreshold;     // pixels below this sat are "neutral"
        internal static ConfigEntry<float> BlendFeather;     // edge feather around the window
        // ---- Diagnostics -----------------------------------------------------
        internal static ConfigEntry<bool> DiagMode;          // verbose ownership/renderer logging

        // Per-faction primary/secondary colours (hex RRGGBB), bound lazily.
        private static readonly Dictionary<string, ConfigEntry<string>> PriEntries = new Dictionary<string, ConfigEntry<string>>();
        private static readonly Dictionary<string, ConfigEntry<string>> SecEntries = new Dictionary<string, ConfigEntry<string>>();

        public void BindFactionColors()
        {
            if (PriEntries.Count > 0) return;
            var presets = FactionPresets.All;
            for (int i = 0; i < presets.Length; i++)
            {
                var p = presets[i];
                string section = "Faction." + p.Key;
                PriEntries[p.Key] = Config.Bind(section, "Primary", ColorUtil.ToHex(p.Primary), "Primary armour colour (RRGGBB).");
                SecEntries[p.Key] = Config.Bind(section, "Secondary", ColorUtil.ToHex(p.Secondary), "Secondary / trim colour (RRGGBB).");
            }
        }

        public static bool TryGetFactionColor(string key, out Color32 pri, out Color32 sec)
        {
            pri = default; sec = default;
            if (key == null || !PriEntries.TryGetValue(key, out var pe)) return false;
            if (!ColorUtil.TryParseHex(pe.Value, out pri)) return false;
            if (!SecEntries.TryGetValue(key, out var se)) return false;
            return ColorUtil.TryParseHex(se.Value, out sec);
        }

        public static void SaveFactionColor(string key, Color32 pri, Color32 sec)
        {
            if (key == null) return;
            if (PriEntries.TryGetValue(key, out var pe)) pe.Value = ColorUtil.ToHex(pri);
            if (SecEntries.TryGetValue(key, out var se)) se.Value = ColorUtil.ToHex(sec);
        }

        public override void Load()
        {
            Log = base.Log;

            ToggleKey = Config.Bind("UI", "ToggleKey", 282, "IMGUI window toggle key (KeyCode int; 282 = F10).");
            ShowButton = Config.Bind("UI", "ShowButton", true, "Draw an always-visible toggle button (reliable fallback if the legacy Input module is stripped).");
            AutoApply = Config.Bind("Paint", "AutoApply", true, "Automatically repaint new/revived player units while a scheme is active.");
            HueWindow = Config.Bind("Paint", "HueWindow", 0.16f, "Hue distance (0..0.5) around each detected paint colour that gets recolored.");
            SatThreshold = Config.Bind("Paint", "SatThreshold", 0.08f, "Pixels with saturation below this are treated as neutral (metal/grime) and left alone.");
            BlendFeather = Config.Bind("Paint", "BlendFeather", 0.08f, "Hue feather around the remap window for smooth edges.");

            DiagMode = Config.Bind("Diagnostics", "DiagMode", false, "Verbose logging of contestants, units, renderers, materials and textures.");

            FactionPresets.RegisterDefaults();
            BindFactionColors();

            Log.LogInfo("Army Painter " + Version + " loaded.");
            ClassInjector.RegisterTypeInIl2Cpp<ArmyPainterBehaviour>();
            AddComponent<ArmyPainterBehaviour>();
        }
    }

    public class ArmyPainterBehaviour : MonoBehaviour
    {
        public ArmyPainterBehaviour(IntPtr ptr) : base(ptr) { }

        // ------------------------------------------------------------- state
        private bool _showUI;
        private readonly RecolorEngine _engine = new RecolorEngine();

        private string _factionKey = "";          // config section key for the current faction
        private Color32 _pri = new Color32(144, 15, 15, 255);
        private Color32 _sec = new Color32(224, 193, 90, 255);
        private string _priHex = "900F0F";
        private string _secHex = "E0C15A";

        private bool _previewTint;
        private bool _schemeDirty = true;         // a new scheme is waiting to be applied
        private bool _schemeActive;               // a scheme has been applied (Reset clears it)
        private HashSet<int> _painted = new HashSet<int>();

        private float _scanTimer;
        private const float ScanInterval = 0.4f;

        private bool _legacyInputWorks = true;

        // ---- IMGUI window -----------------------------------------------------
        private Rect _winRect = new Rect(20, 80, 340, 460);

        // ---- cached scan results (for status line) ----------------------------
        private int _lastUnitCount;
        private int _lastRendererCount;

        private void Awake()
        {
            // Probe legacy Input once; if it throws, fall back to the button only.
            try { _ = UnityEngine.Input.anyKeyDown; }
            catch { _legacyInputWorks = false; }
            Plugin.Log.LogInfo("ArmyPainterBehaviour awake. legacyInput=" + _legacyInputWorks);
        }

        private void Update()
        {
            if (_legacyInputWorks)
            {
                try
                {
                    if (UnityEngine.Input.GetKeyDown((KeyCode)Plugin.ToggleKey.Value))
                        _showUI = !_showUI;
                }
                catch { _legacyInputWorks = false; }
            }

            _scanTimer += Time.deltaTime;
            if (_scanTimer < ScanInterval) return;
            _scanTimer = 0f;

            AutoDetectFaction();

            // While a scheme is active (dirty or already painted), repaint on a
            // rolling basis so newly spawned / revived player units pick it up.
            if (Plugin.AutoApply.Value && _schemeActive && (_schemeDirty || _painted.Count > 0))
                ApplyScheme(false);

            if (Plugin.DiagMode.Value)
                DiagRun();
        }

        // Adopt the local player's faction once found so the saved scheme loads.
        private void AutoDetectFaction()
        {
            if (!string.IsNullOrEmpty(_factionKey)) return;
            string key = DetectFactionKey();
            if (key == null) return;
            ApplyFactionKey(key, log: true);
        }

        private string DetectFactionKey()
        {
            try
            {
                var all = Resources.FindObjectsOfTypeAll<Unit>();
                if (all == null) return null;
                for (int i = 0; i < all.Count; i++)
                {
                    var u = all[i];
                    if (u == null) continue;
                    ContestantBase owner = null;
                    try { owner = u.Team.Contestant; } catch { }
                    if (owner == null) continue;
                    ContestantType ct = ContestantType.AI;
                    try { ct = owner.ContestantType; } catch { }
                    if (ct != ContestantType.LocalPlayer) continue;
                    Faction fac = Faction.None;
                    try { fac = owner.Faction; } catch { }
                    return fac.ToString();
                }
            }
            catch { }
            return null;
        }

        private void OnGUI()
        {
            GUI.depth = 1;
            if (!_showUI)
            {
                if (Plugin.ShowButton.Value &&
                    GUI.Button(new Rect(Screen.width - 108, 4, 104, 26), "Army Painter"))
                    _showUI = true;
                return;
            }

            // Drag title bar.
            Event e = Event.current;
            if (e.type == EventType.MouseDown && e.button == 0 &&
                new Rect(_winRect.x, _winRect.y, _winRect.width, 22).Contains(e.mousePosition))
            {
                _dragOffset = e.mousePosition - new Vector2(_winRect.x, _winRect.y);
                _dragging = true;
                e.Use();
            }
            if (e.type == EventType.MouseDrag && _dragging)
            {
                _winRect.position = e.mousePosition - _dragOffset;
                e.Use();
            }
            if (e.type == EventType.MouseUp && _dragging)
            {
                _dragging = false;
                e.Use();
            }

            GUI.Box(_winRect, "Army Painter  v" + Plugin.Version);
            GUILayout.BeginArea(new Rect(_winRect.x + 6, _winRect.y + 24, _winRect.width - 12, _winRect.height - 30));
            DrawContents();
            GUILayout.EndArea();
        }

        private Vector2 _dragOffset = new Vector2(-1f, -1f);
        private bool _dragging;

        // ============================================================= UI ===
        private void DrawContents()
        {
            GUILayout.BeginVertical();

            string factionLine = string.IsNullOrEmpty(_factionKey)
                ? "No local-player faction detected (preview mode paints any model)"
                : "Faction: " + _factionKey + "   (primary / secondary)";
            GUILayout.Label(factionLine);

            // Presets ----------------------------------------------------
            GUILayout.Label("Presets");
            DrawPresetRow(0);
            DrawPresetRow(1);

            // Primary / secondary colour rows ------------------------------
            ColorRow("Primary", ref _pri, ref _priHex);
            ColorRow("Secondary", ref _sec, ref _secHex);

            GUILayout.Space(6);

            // Actions -----------------------------------------------------
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Apply paint")) ApplyScheme(true);
            if (GUILayout.Button("Preview tint")) { _previewTint = true; ApplyTintPreview(); }
            if (GUILayout.Button("Reset")) ResetPaint();
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            _previewTint = GUILayout.Toggle(_previewTint, "Live tint preview on slider drag");
            GUILayout.EndHorizontal();

            GUILayout.Label(_lastUnitCount + " player units / " + _lastRendererCount +
                            " renderers  ·  cache " + _engine.CacheSize);
            if (GUILayout.Button("Close")) _showUI = false;

            GUILayout.EndVertical();
        }

        private void DrawPresetRow(int idx)
        {
            GUILayout.BeginHorizontal();
            for (int i = idx * 6; i < Mathf.Min(FactionPresets.All.Length, idx * 6 + 6); i++)
            {
                var p = FactionPresets.All[i];
                bool active = p.Key == _factionKey;
                var prev = GUI.backgroundColor;
                GUI.backgroundColor = active ? new Color(0.6f, 0.8f, 1f) : prev;
                if (GUILayout.Button(p.Name, GUILayout.Height(22)))
                    ApplyFactionKey(p.Key, log: true);
                GUI.backgroundColor = prev;
            }
            GUILayout.EndHorizontal();
        }

        private void ApplyFactionKey(string key, bool log)
        {
            _factionKey = key;
            if (!Plugin.TryGetFactionColor(key, out _pri, out _sec))
            {
                var p = FactionPresets.Find(key);
                if (p.HasValue) { _pri = p.Value.Primary; _sec = p.Value.Secondary; }
            }
            _priHex = ColorUtil.ToHex(_pri);
            _secHex = ColorUtil.ToHex(_sec);
            _schemeDirty = true;
            _schemeActive = true;
            _painted.Clear();
            if (log) Plugin.Log.LogInfo("Army Painter scheme: " + key + "  pri=" + _priHex + " sec=" + _secHex);
        }

        private void ColorRow(string label, ref Color32 c, ref string hex)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, GUILayout.Width(86));

            GUI.color = new Color(c.r / 255f, c.g / 255f, c.b / 255f, 1f);
            GUILayout.Box("", GUILayout.Width(26), GUILayout.Height(20));
            GUI.color = Color.white;

            Color32 before = c;
            int r = (int)Mathf.Round(GUILayout.HorizontalSlider(c.r, 0f, 255f, GUILayout.Width(52)));
            GUILayout.Label("R", GUILayout.Width(12));
            int g = (int)Mathf.Round(GUILayout.HorizontalSlider(c.g, 0f, 255f, GUILayout.Width(52)));
            GUILayout.Label("G", GUILayout.Width(12));
            int b = (int)Mathf.Round(GUILayout.HorizontalSlider(c.b, 0f, 255f, GUILayout.Width(52)));
            GUILayout.Label("B", GUILayout.Width(12));

            c = new Color32((byte)Mathf.Clamp(r, 0, 255), (byte)Mathf.Clamp(g, 0, 255), (byte)Mathf.Clamp(b, 0, 255), 255);

            string newHex = GUILayout.TextField(hex, 6, GUILayout.Width(52));
            if (newHex != hex)
            {
                hex = newHex;
                if (ColorUtil.TryParseHex(hex, out Color32 parsed))
                    c = parsed;
            }

            if (!c.Equals(before))
            {
                hex = ColorUtil.ToHex(c);
                _schemeDirty = true;
                _schemeActive = true;
                if (_previewTint) ApplyTintPreview();
            }
            GUILayout.EndHorizontal();
        }

        // ========================================================= engine ===
        // Scans all live units and keeps those owned by the local player
        // (Unit.Team.Contestant.ContestantType == LocalPlayer). With no local
        // player present (army-builder / model podium) every unit is kept so the
        // painter works in preview scenes too.
        private List<Unit> FindPlayerUnits()
        {
            List<Unit> units = new List<Unit>();
            bool anyContestant = false;
            string diagLine = null;

            var all = SafeFindUnits();
            if (all == null) return units;

            for (int i = 0; i < all.Count; i++)
            {
                var u = all[i];
                if (u == null) continue;
                ContestantBase owner = null;
                try { owner = u.Team.Contestant; } catch { }
                if (owner != null)
                {
                    anyContestant = true;
                    int cid = 0; ContestantType ct = ContestantType.AI; Faction fac = Faction.None; int team = 0;
                    try { cid = owner.ContestantId; } catch { }
                    try { team = owner.TeamId; } catch { }
                    try { ct = owner.ContestantType; } catch { }
                    try { fac = owner.Faction; } catch { }
                    if (diagLine == null)
                        diagLine = "[ArmyPainter] contestant '" + SafeDisplayName(owner) + "' id=" + cid + " team=" + team + " type=" + ct + " faction=" + fac;
                    if (ct == ContestantType.LocalPlayer) units.Add(u);
                }
            }

            // Preview / army-builder scenes have no TeamManager (no battle), so
            // ownership is unset: paint every visible model so colours can be
            // tested. In a battle we ONLY ever touch LocalPlayer-confirmed units.
            if (!anyContestant && !BattleActive())
                units = new List<Unit>(all);

            if (Plugin.DiagMode.Value)
            {
                Plugin.Log.LogInfo(diagLine ?? "[ArmyPainter] no contestant ownership found.");
                Plugin.Log.LogInfo("[ArmyPainter] player units after ownership filter: " + units.Count + " / " + all.Count);
            }
            return units;
        }

        private static bool BattleActive()
        {
            try
            {
                var tms = Resources.FindObjectsOfTypeAll<TeamManager>();
                return tms != null && tms.Count > 0;
            }
            catch { return false; }
        }

        private static Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<Unit> SafeFindUnits()
        {
            try { return Resources.FindObjectsOfTypeAll<Unit>(); } catch { return null; }
        }

        private static Unit FindOwnerUnit(Transform t, HashSet<int> playerUnitIds)
        {
            Transform cur = t;
            while (cur != null)
            {
                Unit u = null;
                try { u = cur.GetComponent<Unit>(); } catch { }
                if (u != null)
                {
                    int id = 0; try { id = u.GetInstanceID(); } catch { }
                    if (id != 0 && playerUnitIds.Contains(id)) return u;
                }
                try { cur = cur.parent; } catch { break; }
            }
            return null;
        }

        private void CollectRenderers(List<Unit> units, out List<Renderer> renderers)
        {
            renderers = new List<Renderer>();
            HashSet<int> seen = new HashSet<int>();
            HashSet<int> unitIds = new HashSet<int>();
            for (int i = 0; i < units.Count; i++)
            {
                int id = 0; try { id = units[i].GetInstanceID(); } catch { }
                if (id != 0) unitIds.Add(id);
            }

            List<Renderer> target = renderers;

            void Add(Renderer r)
            {
                if (r == null) return;
                int rid = 0; try { rid = r.GetInstanceID(); } catch { }
                if (rid == 0 || !seen.Add(rid)) return;
                target.Add(r);
            }

            // Path A: renderers under each unit's transform.
            for (int i = 0; i < units.Count; i++)
            {
                var rs = SafeGetRs(units[i]);
                if (rs != null) for (int j = 0; j < rs.Count; j++) Add(rs[j]);
            }

            // Path B: every AnimatedCharacter whose hierarchy belongs to a player unit.
            try
            {
                var chars = Resources.FindObjectsOfTypeAll<AnimatedCharacter>();
                if (chars != null)
                {
                    for (int i = 0; i < chars.Count; i++)
                    {
                        var ac = chars[i];
                        if (ac == null) continue;
                        Unit owner = FindOwnerUnit(ac.transform, unitIds);
                        if (owner == null) continue;
                        Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<Renderer> rs = null;
                        try { rs = ac.AllModelRenderers; } catch { }
                        if (rs == null) try { rs = ac.GetComponentsInChildren<Renderer>(true); } catch { }
                        if (rs != null) for (int j = 0; j < rs.Count; j++) Add(rs[j]);
                    }
                }
            }
            catch { }

            _lastRendererCount = renderers.Count;
        }

        private static Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<Renderer> SafeGetRs(Unit u)
        {
            try { return u.GetComponentsInChildren<Renderer>(true); } catch { return null; }
        }

        private void ApplyScheme(bool forceReapply)
        {
            List<Unit> units = FindPlayerUnits();
            _lastUnitCount = units.Count;

            if (units.Count == 0)
            {
                if (Plugin.DiagMode.Value) Plugin.Log.LogWarning("[ArmyPainter] no player units to paint.");
                return;
            }

            CollectRenderers(units, out List<Renderer> renderers);

            Color32 pri = _pri;
            Color32 sec = _sec;

            int painted = 0;
            foreach (var r in renderers)
            {
                if (r == null) continue;
                int rid = 0; try { rid = r.GetInstanceID(); } catch { continue; }
                if (!forceReapply && _painted.Contains(rid)) continue;

                Material m = null;
                try { m = r.sharedMaterial; } catch { }
                if (m == null) continue;
                if (!RecolorFilter.ShouldPaint(m)) continue;

                Texture2D src = null;
                try { src = m.GetTexture("_MainTex") as Texture2D; } catch { }
                if (src == null) continue;

                Texture2D repl = _engine.GetRemap(src, pri, sec, Plugin.HueWindow.Value, Plugin.SatThreshold.Value, Plugin.BlendFeather.Value);
                if (repl == null) continue;

                var mpb = new MaterialPropertyBlock();
                try { r.GetPropertyBlock(mpb); } catch { }
                try { mpb.SetTexture("_MainTex", repl); } catch { continue; }
                try { mpb.SetColor("_Color", Color.white); } catch { }
                try { r.SetPropertyBlock(mpb); } catch { }
                _painted.Add(rid);
                painted++;
            }

            _previewTint = false;
            _schemeDirty = false;
            _schemeActive = true;
            Plugin.SaveFactionColor(_factionKey, _pri, _sec);
            Plugin.Log.LogInfo($"[ArmyPainter] applied to {painted}/{renderers.Count} renderers (units {units.Count}).");
        }

        private void ApplyTintPreview()
        {
            List<Unit> units = FindPlayerUnits();
            CollectRenderers(units, out List<Renderer> renderers);

            Color tint = Color.Lerp(Color.white, new Color(_pri.r / 255f, _pri.g / 255f, _pri.b / 255f, 1f), 0.55f);
            foreach (var r in renderers)
            {
                if (r == null) continue;
                var m = r.sharedMaterial; if (m == null) continue;
                if (!RecolorFilter.ShouldPaint(m)) continue;
                var mpb = new MaterialPropertyBlock();
                try { r.GetPropertyBlock(mpb); } catch { }
                try { mpb.SetColor("_Color", tint); } catch { continue; }
                try { r.SetPropertyBlock(mpb); } catch { }
            }
        }

        private void ResetPaint()
        {
            List<Unit> units = FindPlayerUnits();
            CollectRenderers(units, out List<Renderer> renderers);
            int reset = 0;
            foreach (var r in renderers)
            {
                if (r == null) continue;
                var m = r.sharedMaterial; if (m == null) continue;
                if (!RecolorFilter.ShouldPaint(m)) continue;
                var mpb = new MaterialPropertyBlock();
                try { r.GetPropertyBlock(mpb); } catch { }
                try
                {
                    Texture2D original = m.GetTexture("_MainTex") as Texture2D;
                    if (original != null) mpb.SetTexture("_MainTex", original);
                    mpb.SetColor("_Color", Color.white);
                }
                catch { }
                try { r.SetPropertyBlock(mpb); } catch { }
                reset++;
            }
            _painted.Clear();
            _engine.ClearCache();
            _schemeDirty = false;
            _schemeActive = false;
            Plugin.Log.LogInfo("[ArmyPainter] reset " + reset + " renderers to original paint.");
        }

        // ====================================================== diagnostics ===
        private void DiagRun()
        {
            List<Unit> units = FindPlayerUnits();
            Plugin.Log.LogInfo($"[ArmyPainter] DIAG playerUnits={units.Count}");
            for (int i = 0; i < units.Count && i < 5; i++)
            {
                var u = units[i];
                string n = SafeName(u);
                int unitId = 0; try { unitId = u.GetInstanceID(); } catch { }
                try
                {
                    var owner = u.Team.Contestant;
                    string ownerDesc = owner != null ? SafeDisplayName(owner) + "/" + owner.Faction : "?";
                    Plugin.Log.LogInfo("  unit '" + n + "' id=" + unitId + " faction=" + ownerDesc);
                }
                catch { Plugin.Log.LogInfo("  unit '" + n + "' id=" + unitId + " (Team not readable)"); }
            }
            CollectRenderers(units, out List<Renderer> renderers);
            Plugin.Log.LogInfo($"[ArmyPainter] DIAG renderers={renderers.Count}");
            for (int i = 0; i < renderers.Count && i < 8; i++)
            {
                var r = renderers[i];
                var m = r.sharedMaterial;
                if (m == null) continue;
                string tex = "?";
                bool readable = false;
                try
                {
                    var t = m.GetTexture("_MainTex");
                    var t2 = t as Texture2D;
                    if (t2 != null)
                    {
                        tex = SafeName(t2) + "  " + t2.width + "x" + t2.height;
                        try { readable = t2.isReadable; } catch { }
                    }
                    else
                    {
                        tex = SafeName(t);
                    }
                }
                catch { }
                Plugin.Log.LogInfo($"  renderer '{SafeName(r)}' mat='{SafeName(m)}' mode={MatMode(m)} queue={m.renderQueue} maintex={tex} readable={readable}");
            }
            Plugin.Log.LogInfo("[ArmyPainter] DIAG done");
        }

        private static float MatMode(Material m)
        {
            try { if (m.HasProperty("_Mode")) return m.GetFloat("_Mode"); } catch { }
            return -1f;
        }

        private static string SafeName(UnityEngine.Object o)
        {
            try { return o != null ? o.name : "<NULL>"; } catch { return "?"; }
        }

        private static string SafeDisplayName(ContestantBase c)
        {
            try
            {
                var d = c.DisplayName;
                return !string.IsNullOrEmpty(d) ? d : "contestant#" + c.ContestantId;
            }
            catch { return "?"; }
        }
    }

    // ============================================================== engine ===
    public static class RecolorFilter
    {
        public static bool ShouldPaint(Material m)
        {
            try
            {
                if (!m.HasProperty("_MainTex")) return false;
                if (m.HasProperty("_Mode") && Mathf.Abs(m.GetFloat("_Mode")) > 0.01f) return false; // transparent FX
                if (m.renderQueue >= 3000) return false;                                         // transparent/overlay
                var t = m.GetTexture("_MainTex") as Texture2D;
                if (t == null) return false;
                return t.width > 0 && t.height > 0;
            }
            catch { return false; }
        }
    }

    public class RecolorEngine
    {
        private readonly Dictionary<int, Texture2D> _cache = new Dictionary<int, Texture2D>();
        private readonly Queue<int> _lru = new Queue<int>();
        private const int CacheBudget = 24;

        public int CacheSize => _cache.Count;

        public void ClearCache()
        {
            _cache.Clear();
            _lru.Clear();
        }

        public Texture2D GetRemap(Texture2D src, Color32 pri, Color32 sec,
                                  float hueWindow, float satThreshold, float feather)
        {
            int key = Hash(src.GetInstanceID(), pri, sec);
            if (_cache.TryGetValue(key, out Texture2D hit)) return hit;
            if (_cache.Count >= CacheBudget && _lru.Count > 0)
            {
                // Drop from cache only - never Destroy here: renderers may still
                // reference this texture through MaterialPropertyBlocks, and
                // destroying it would flash them black. The IL2CPP GC frees it
                // once the last referencing renderer goes away.
                while (_lru.Count > 0)
                {
                    int evict = _lru.Dequeue();
                    if (_cache.Remove(evict)) break;
                }
            }

            Color32[] px = ReadPixels(src);
            if (px == null)
            {
                Plugin.Log.LogWarning("[ArmyPainter] could not read texture '" + src.name + "'.");
                return null;
            }
            int w = src.width, h = src.height;

            // Auto-detect the primary + secondary paint hues from the texture.
            GetPaintHues(px, w, h, satThreshold, out float priHue, out float secHue, out bool hasSec);

            Color32[] outp = Remap(px, priHue, secHue, hasSec, pri, sec, hueWindow, satThreshold, feather);

            Texture2D tex = null;
            try
            {
                tex = new Texture2D(w, h, TextureFormat.RGBA32, true, false);   // mip chain + sRGB (matches albedo)
                tex.SetPixels32(outp);
                tex.Apply(true, false);
                tex.name = "ArmyPainter_" + src.name;
            }
            catch (Exception e) { Plugin.Log.LogWarning("[ArmyPainter] texture build failed: " + e.Message); return null; }

            _cache[key] = tex;
            _lru.Enqueue(key);
            return tex;
        }

        // ---- pixel readback (works on non-readable textures) -----------------
        private static Color32[] ReadPixels(Texture2D src)
        {
            int w = src.width, h = src.height;
            if (w <= 0 || h <= 0) return null;
            try
            {
                if (src.isReadable) return src.GetPixels32();
            }
            catch { }

            try
            {
                RenderTexture rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
                var prev = RenderTexture.active;
                try
                {
                    Graphics.Blit(src, rt);
                    RenderTexture.active = rt;
                    var tmp = new Texture2D(w, h, TextureFormat.RGBA32, false, false);
                    tmp.ReadPixels(new Rect(0, 0, w, h), 0, 0);
                    tmp.Apply(false, false);
                    Color32[] px = tmp.GetPixels32();
                    UnityEngine.Object.Destroy(tmp);
                    return px;
                }
                finally
                {
                    RenderTexture.active = prev;
                    RenderTexture.ReleaseTemporary(rt);
                }
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("[ArmyPainter] ReadPixels failed: " + e.Message);
                return null;
            }
        }

        // ---- dominant-hue detection -------------------------------------------
        private static void GetPaintHues(Color32[] px, int w, int h, float satThreshold,
                                         out float priHue, out float secHue, out bool hasSec)
        {
            const int Bins = 60;
            int[] hist = new int[Bins];
            int stride = Mathf.Max(1, (int)((long)px.Length / 20000L));
            int n = 0;
            for (int i = 0; i < px.Length; i += stride)
            {
                Color c = new Color(px[i].r / 255f, px[i].g / 255f, px[i].b / 255f, 1f);
                Color.RGBToHSV(c, out float hh, out float ss, out float vv);
                if (ss < satThreshold) continue;
                int bin = (int)(hh * Bins) % Bins;
                hist[bin]++;
                n++;
            }
            priHue = 0f; secHue = 0f; hasSec = false;
            if (n == 0) return;

            int peak = 0;
            for (int i = 1; i < Bins; i++) if (hist[i] > hist[peak]) peak = i;
            priHue = (peak + 0.5f) / Bins;

            // second peak outside a guard band around the first
            int guard = Mathf.Max(2, Mathf.RoundToInt(Bins * 0.08f));
            int secBin = -1, secCount = 0;
            for (int i = 0; i < Bins; i++)
            {
                int d = Mathf.Min(Mathf.Abs(i - peak), Bins - Mathf.Abs(i - peak));
                if (d <= guard) continue;
                if (hist[i] > secCount) { secCount = hist[i]; secBin = i; }
            }
            if (secBin >= 0 && secCount >= Mathf.Max(3, n / 40))
            {
                secHue = (secBin + 0.5f) / Bins;
                hasSec = true;
            }
        }

        private static Color32[] Remap(Color32[] px, float priHue, float secHue, bool hasSec,
                                       Color32 pri, Color32 sec,
                                       float hueWindow, float satThreshold, float feather)
        {
            float win = Mathf.Clamp(hueWindow, 0.03f, 0.5f);
            float featherLen = Mathf.Clamp(feather, 0f, win);
            Color.RGBToHSV(new Color(pri.r / 255f, pri.g / 255f, pri.b / 255f, 1f), out float priTargetH, out float priTargetS, out float priTargetV);
            Color.RGBToHSV(new Color(sec.r / 255f, sec.g / 255f, sec.b / 255f, 1f), out float secTargetH, out float secTargetS, out float secTargetV);

            Color32[] outp = new Color32[px.Length];
            for (int i = 0; i < px.Length; i++)
            {
                Color32 p = px[i];
                if (p.a < 16) { outp[i] = p; continue; }
                Color c = new Color(p.r / 255f, p.g / 255f, p.b / 255f, p.a / 255f);
                Color.RGBToHSV(c, out float h, out float s, out float v);
                if (s < satThreshold) { outp[i] = p; continue; }

                float dp = HueDist(h, priHue);
                float ds = hasSec ? HueDist(h, secHue) : 1f;
                float dm = Mathf.Min(dp, ds);
                if (dm > win) { outp[i] = p; continue; }          // off-scheme accent kept

                bool usePri = dp < ds;
                float targetH = usePri ? priTargetH : secTargetH;
                float k = 1f - Mathf.Max(0f, dm - (win - featherLen)) / Mathf.Max(0.001f, featherLen);
                k = Mathf.Clamp01(k);
                float newH = usePri ? Mathf.LerpAngle(h * 360f, priTargetH * 360f, k) / 360f
                                    : Mathf.LerpAngle(h * 360f, secTargetH * 360f, k) / 360f;

                Color outpC = Color.HSVToRGB(newH, s, v);
                outp[i] = new Color32(
                    (byte)Mathf.Clamp(Mathf.RoundToInt(outpC.r * 255f), 0, 255),
                    (byte)Mathf.Clamp(Mathf.RoundToInt(outpC.g * 255f), 0, 255),
                    (byte)Mathf.Clamp(Mathf.RoundToInt(outpC.b * 255f), 0, 255),
                    p.a);
            }
            return outp;
        }

        private static float HueDist(float a, float b)
        {
            float d = Mathf.Abs(a - b);
            return Mathf.Min(d, 1f - d);
        }

        private static int Hash(int texId, Color32 a, Color32 b)
        {
            unchecked
            {
                int h = texId;
                h = h * 31 + a.r + (a.g << 8) + (a.b << 16);
                h = h * 31 + b.r + (b.g << 8) + (b.b << 16);
                return h;
            }
        }
    }

    // ============================================================= colours ===
    public static class ColorUtil
    {
        public static string ToHex(Color32 c)
        {
            return c.r.ToString("X2") + c.g.ToString("X2") + c.b.ToString("X2");
        }

        public static bool TryParseHex(string s, out Color32 c)
        {
            c = default;
            if (string.IsNullOrEmpty(s)) return false;
            s = s.Trim().TrimStart('#');
            if (s.Length != 6) return false;
            if (!byte.TryParse(s.Substring(0, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out byte r)) return false;
            if (!byte.TryParse(s.Substring(2, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out byte g)) return false;
            if (!byte.TryParse(s.Substring(4, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out byte b)) return false;
            c = new Color32(r, g, b, 255);
            return true;
        }
    }

    public struct FactionPreset
    {
        public string Key;
        public string Name;
        public Color32 Primary;
        public Color32 Secondary;
    }

    public static class FactionPresets
    {
        private static readonly List<FactionPreset> _all = new List<FactionPreset>();
        public static FactionPreset[] All => _all.ToArray();

        public static FactionPreset? Find(string key)
        {
            for (int i = 0; i < _all.Count; i++)
                if (_all[i].Key == key) return _all[i];
            return null;
        }

        public static void RegisterDefaults()
        {
            if (_all.Count > 0) return;
            Add("BloodAngels", "Blood Angels", "900F0F", "E0C15A");
            Add("Ultramarines", "Ultramarines", "10468F", "E8E4DA");
            Add("AstraMilitarum", "Astra Militarum", "5F6B3F", "9A8F6A");
            Add("AdeptaSororitas", "Adepta Sororitas", "8F1010", "E8E4DA");
            Add("Ork", "Orks", "2F6B2F", "7A4A1E");
            Add("Tyranid", "Tyranids", "7A2F6B", "B0566B");
            Add("Necron", "Necrons", "2F5A4A", "63C89C");
            Add("MephritNecron", "Mephrit Necrons", "C06828", "48A8A0");
            Add("Tau", "T'au", "B08A4A", "D0C8B8");
            Add("KhorneChaos", "Daemons of Khorne", "6B0F0F", "C9A227");
            Add("BlackLegion", "Black Legion", "22242A", "B01212");
            Add("GenestealerCult", "Genestealer Cult", "4A5A6B", "8FB0C8");
        }

        private static void Add(string key, string name, string priHex, string secHex)
        {
            ColorUtil.TryParseHex(priHex, out Color32 pri);
            ColorUtil.TryParseHex(secHex, out Color32 sec);
            _all.Add(new FactionPreset { Key = key, Name = name, Primary = pri, Secondary = sec });
        }
    }
}
