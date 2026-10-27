using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using UnityEngine.Rendering;
using Units;
using Warpstorm.Shared;

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
    [BepInPlugin(GUID, "Army Painter", "1.1.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.armypainter";
        public const string Version = "1.1.0";
        internal static new ManualLogSource Log;
        internal static ConfigFile Cfg;

        // ---- UI toggles -----------------------------------------------------
        internal static ConfigEntry<int> ToggleKey;          // F10
        internal static ConfigEntry<bool> ShowButton;        // always-visible toggle button
        // ---- Paint behaviour -------------------------------------------------
        internal static ConfigEntry<bool> PaintEnabled;      // opt-in: do any paint work at all
        internal static ConfigEntry<bool> AutoApply;         // repaint new units automatically
        internal static ConfigEntry<float> HueWindow;        // hue distance accepted for remap
        internal static ConfigEntry<float> SatThreshold;     // pixels below this sat are "neutral"
        internal static ConfigEntry<float> BlendFeather;     // edge feather around the window
        internal static ConfigEntry<bool> ApproxPortraits;   // approximate 2D portrait recolour
        // ---- Diagnostics -----------------------------------------------------
        internal static ConfigEntry<bool> DiagMode;          // verbose ownership/renderer logging

        // Per-faction primary/secondary colours (hex RRGGBB), bound lazily.
        private static readonly Dictionary<string, ConfigEntry<string>> PriEntries = new Dictionary<string, ConfigEntry<string>>();
        private static readonly Dictionary<string, ConfigEntry<string>> SecEntries = new Dictionary<string, ConfigEntry<string>>();
        private static readonly Dictionary<string, ConfigEntry<string>> SchemeEntries = new Dictionary<string, ConfigEntry<string>>();
        internal static ConfigEntry<int> MaxTextureSize;

        public static string FactionSchemeId(string key)
            => key != null && SchemeEntries.TryGetValue(key, out var e) ? (e.Value ?? "").Trim() : "";

        // ---- scheme packs: user imports (config/warpstorm/schemes) override built-ins (plugins/Warpstorm/schemes)
        private static List<SchemePack> _packs;
        private static DateTime _packsScanned = DateTime.MinValue;

        public static SchemePack FindPack(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            if (_packs == null || (DateTime.UtcNow - _packsScanned).TotalSeconds > 5)
            {
                _packsScanned = DateTime.UtcNow;
                string pluginDir = System.IO.Path.GetDirectoryName(typeof(Plugin).Assembly.Location) ?? Paths.PluginPath;
                _packs = SchemePack.Discover(new[]
                {
                    System.IO.Path.Combine(Paths.ConfigPath, "warpstorm", "schemes"),
                    System.IO.Path.Combine(pluginDir, "schemes"),
                }, err => Log.LogWarning("[ArmyPainter] scheme pack skipped: " + err));
            }
            foreach (var p in _packs) if (string.Equals(p.Id, id, StringComparison.OrdinalIgnoreCase)) return p;
            return null;
        }

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
                SchemeEntries[p.Key] = Config.Bind(section, "Scheme", "", "Curated scheme pack id (e.g. salamanders); empty = use the Primary/Secondary colours.");
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

        /// <summary>
        /// True as soon as one faction has a non-default colour or a scheme pack.
        /// Cheap on purpose: no Unity objects, no scene scan, no pack discovery.
        /// While this is false the plugin must not touch renderers or textures.
        /// </summary>
        public static bool HasCustomPaint()
        {
            if (PriEntries.Count == 0) return false;
            var presets = FactionPresets.All;
            for (int i = 0; i < presets.Length; i++)
            {
                var p = presets[i];
                if (SchemeEntries.TryGetValue(p.Key, out var se) && !string.IsNullOrWhiteSpace(se.Value)) return true;
                if (!TryGetFactionColor(p.Key, out var pri, out var sec)) continue;
                if (pri.r != p.Primary.r || pri.g != p.Primary.g || pri.b != p.Primary.b ||
                    sec.r != p.Secondary.r || sec.g != p.Secondary.g || sec.b != p.Secondary.b) return true;
            }
            return false;
        }

        /// <summary>Whether any custom faction needs the 2D portrait pass.</summary>
        public static bool AnyPortraitScheme()
        {
            if (ApproxPortraits.Value) return true;
            var presets = FactionPresets.All;
            for (int i = 0; i < presets.Length; i++)
            {
                string id = FactionSchemeId(presets[i].Key);
                if (id.Length > 0 && FindPack(id) != null) return true;
            }
            return false;
        }

        public override void Load()
        {
            Log = base.Log;
            Cfg = Config;

            ToggleKey = Config.Bind("UI", "ToggleKey", 282, "IMGUI window toggle key (KeyCode int; 282 = F1, 291 = F10).");
            ShowButton = Config.Bind("UI", "ShowButton", true, "Draw an always-visible toggle button (reliable fallback if the legacy Input module is stripped).");
            PaintEnabled = Config.Bind("Paint", "Enabled", false,
                "Opt-in: enable Army Painter in game. Off by default. While off (or while every faction is still at its default colour) the plugin does no paint work at all: no scene scan, no renderer/texture access, no portraits, no overlay.");
            AutoApply = Config.Bind("Paint", "AutoApply", true, "Automatically paint every unit model of a faction with a custom scheme (battle, army management, menus).");
            HueWindow = Config.Bind("Paint", "HueWindow", 0.16f, "Hue distance (0..0.5) around each detected paint colour that gets recolored.");
            SatThreshold = Config.Bind("Paint", "SatThreshold", 0.08f, "Pixels with saturation below this are treated as neutral (metal/grime) and left alone.");
            BlendFeather = Config.Bind("Paint", "BlendFeather", 0.08f, "Hue feather around the remap window for smooth edges.");
            MaxTextureSize = Config.Bind("Paint", "MaxTextureSize", 2048, "Largest size (px) of a repainted model texture. The game's are 4096; 2048 keeps memory low.");
            ApproxPortraits = Config.Bind("Paint", "ApproxPortraits", false, "Also recolour 2D unit portraits automatically (approximate hue shift; off by default).");

            DiagMode = Config.Bind("Diagnostics", "DiagMode", false, "Verbose logging of contestants, units, renderers, materials and textures.");

            FactionPresets.RegisterDefaults();
            BindFactionColors();

            Log.LogInfo("Army Painter " + Version + " loaded (opt-in " + (PaintEnabled.Value ? "ON" : "OFF") + "). " +
                        "Painting only runs when [Paint] Enabled = true and at least one faction has a custom colour or scheme.");
            ClassInjector.RegisterTypeInIl2Cpp<ArmyPainterBehaviour>();
            AddComponent<ArmyPainterBehaviour>();
        }
    }

    // Paints every unit model in the scene — battle, army management, menus —
    // with ITS OWN faction's scheme (enemies included). Factions left at their
    // default colours are not touched.
    //
    // Opt-in and lazy: the behaviour is a no-op unless [Paint] Enabled is true
    // AND at least one faction has a non-default colour or a scheme pack. In
    // particular, a stat-only setup never scans the scene or reads a texture.
    //
    // Verified from the game's bundles (faction-*_assets_all.bundle): unit
    // materials use the game's own standard shader with the albedo in _MainTex;
    // _Mode is 0/2/4 on opaque armour, so it is NOT a transparency flag here
    // (only the _ALPHABLEND/_ALPHAPREMULTIPLY keywords and queue >= 3000 are).
    // The game drives its own MaterialPropertyBlocks on unit renderers, so the
    // recoloured albedo goes into per-renderer material copies instead.
    public class ArmyPainterBehaviour : MonoBehaviour
    {
        public ArmyPainterBehaviour(IntPtr ptr) : base(ptr) { }

        private readonly RecolorEngine _engine = new RecolorEngine();
        private const float ScanInterval = 0.5f;
        private const float DormantPollInterval = 2f;
        private float _scanTimer, _cfgTimer, _statusTimer, _portraitTimer;
        private DateTime _cfgStamp = DateTime.MinValue;
        private bool _legacyInputWorks = true;
        private bool _wasActive;
        private int _tickErrors;

        // ---- IMGUI window (edits one faction at a time) ----------------------
        private bool _showUI;
        private Rect _winRect = new Rect(20, 80, 400, 470);
        private Vector2 _dragOffset;
        private bool _dragging;
        private string _editKey = "";
        private Color32 _pri, _sec;
        private string _priHex = "", _secHex = "";
        private bool _editDirty;

        // ---- painted state ---------------------------------------------------
        private sealed class PaintedRenderer
        {
            public Renderer R;
            public Material[] Originals;
            public Material[] Instances;
            public string Scheme;
        }

        private readonly struct Scheme
        {
            public readonly string Faction;
            public readonly Color32 Pri, Sec;
            public readonly SchemePack Pack;   // curated pack, or null = Primary/Secondary colours
            public readonly string Key;
            public Scheme(string faction, Color32 pri, Color32 sec, SchemePack pack)
            {
                Faction = faction; Pri = pri; Sec = sec; Pack = pack;
                Key = PaintCache.SchemeKey(faction, pack, ColorUtil.ToHex(pri), ColorUtil.ToHex(sec),
                    Plugin.HueWindow.Value, Plugin.SatThreshold.Value, Plugin.BlendFeather.Value,
                    Mathf.Clamp(Plugin.MaxTextureSize.Value, 256, 4096));
            }

            public string Label => Pack != null ? "scheme '" + Pack.Name + "'" : "#" + ColorUtil.ToHex(Pri) + "/#" + ColorUtil.ToHex(Sec);

            public byte[] Remap(byte[] rgba, string textureName)
                => Pack != null
                    ? PaintMath.ApplyRules(rgba, Pack.RulesForTexture(textureName))
                    : PaintMath.Remap(rgba, Pri.r, Pri.g, Pri.b, Sec.r, Sec.g, Sec.b,
                                      Plugin.HueWindow.Value, Plugin.SatThreshold.Value, Plugin.BlendFeather.Value);
        }

        private readonly Dictionary<int, PaintedRenderer> _painted = new Dictionary<int, PaintedRenderer>();
        private string _lastSummary = "";
        private int _lastModels, _lastPaintedCount, _lastPortraits;
        private string _activeFactions = "";

        private void Awake()
        {
            try { _ = UnityEngine.Input.anyKeyDown; }
            catch { _legacyInputWorks = false; }
            Plugin.Log.LogInfo("ArmyPainterBehaviour awake. legacyInput=" + _legacyInputWorks);
        }

        private void Update()
        {
            try { Tick(); }
            catch (Exception ex)
            {
                if (_tickErrors++ < 5) Plugin.Log.LogError("[ArmyPainter] update failed: " + ex);
            }
        }

        private void Tick()
        {
            // Opt-in gate. Until the player enables Army Painter, it must cost
            // nothing in game: no scene scan, no renderer/material access, no
            // portraits, no UI. Only the settings file is checked every couple
            // of seconds, so a Save in the configurator can switch it on.
            if (!Plugin.PaintEnabled.Value)
            {
                _cfgTimer += Time.deltaTime;
                if (_cfgTimer < DormantPollInterval) return;
                _cfgTimer = 0f;
                ReloadIfConfigChanged();
                if (Plugin.PaintEnabled.Value) return;   // enabled now; start next frame
                if (_wasActive) Deactivate();
                return;
            }

            if (_legacyInputWorks)
            {
                try { if (UnityEngine.Input.GetKeyDown((KeyCode)Plugin.ToggleKey.Value)) _showUI = !_showUI; }
                catch { _legacyInputWorks = false; }
            }

            _cfgTimer += Time.deltaTime;
            if (_cfgTimer >= 1f) { _cfgTimer = 0f; ReloadIfConfigChanged(); }

            _scanTimer += Time.deltaTime;
            if (_scanTimer < ScanInterval) return;
            _scanTimer = 0f;

            // Opted in, but every faction still uses its preset paint: the
            // game's own colours are already correct, so stay idle.
            if (!Plugin.HasCustomPaint())
            {
                if (_wasActive) Deactivate();
                return;
            }

            if (!_wasActive)
            {
                _wasActive = true;
                Plugin.Log.LogInfo("[ArmyPainter] custom paint detected — painting is active.");
            }

            if (Plugin.AutoApply.Value) PaintScene(false);

            // Colour-only repaints do not need the portrait pass (it is off by
            // default and would scan the whole UI for nothing).
            if (Plugin.AnyPortraitScheme() || _lastPortraits > 0)
            {
                _portraitTimer += ScanInterval;
                if (_portraitTimer >= 1f) { _portraitTimer = 0f; PaintPortraits(); }
            }

            _statusTimer += ScanInterval;
            if (_statusTimer >= 5f) { _statusTimer = 0f; WriteStatus(); }
        }

        /// <summary>Restores the game's own paint and goes fully dormant.</summary>
        private void Deactivate()
        {
            _wasActive = false;
            _scanTimer = _cfgTimer = _statusTimer = _portraitTimer = 0f;
            _showUI = false;

            int restored = 0;
            foreach (var pr in _painted.Values) { Restore(pr); restored++; }
            _painted.Clear();
            if (_lastPortraits > 0 || _spriteCache.Count > 0 || _curated.Count > 0) ClearPortraits();
            _engine.ClearCache();

            _lastSummary = "";
            _lastModels = _lastPaintedCount = 0;
            _activeFactions = "";
            if (restored > 0)
                Plugin.Log.LogInfo("[ArmyPainter] inactive — restored " + restored + " renderer(s) to the game's own paint.");
            else
                Plugin.Log.LogInfo("[ArmyPainter] inactive — no paint work is running.");
            WriteStatus();
        }

        // ------------------------------------------------------------ schemes

        /// <summary>The faction's scheme, or null when it is at its default colours (= leave the game's paint).</summary>
        private static Scheme? SchemeFor(string faction)
        {
            if (string.IsNullOrEmpty(faction) || faction == "None") return null;
            if (!Plugin.TryGetFactionColor(faction, out var pri, out var sec)) return null;
            string packId = Plugin.FactionSchemeId(faction);
            if (packId.Length > 0)
            {
                var pack = Plugin.FindPack(packId);
                if (pack != null) return new Scheme(faction, pri, sec, pack);
                MissingPack(faction, packId);
            }
            var preset = FactionPresets.Find(faction);
            if (preset.HasValue &&
                ColorUtil.ToHex(preset.Value.Primary) == ColorUtil.ToHex(pri) &&
                ColorUtil.ToHex(preset.Value.Secondary) == ColorUtil.ToHex(sec)) return null;
            return new Scheme(faction, pri, sec, null);
        }

        private static readonly HashSet<string> _missingPacks = new HashSet<string>();

        private static void MissingPack(string faction, string id)
        {
            if (_missingPacks.Add(faction + id))
                Plugin.Log.LogWarning($"[ArmyPainter] {faction}: scheme pack '{id}' not found (looked in BepInEx/config/warpstorm/schemes and plugins/Warpstorm/schemes); using colours.");
        }

        private void ReloadIfConfigChanged()
        {
            try
            {
                string path = Plugin.Cfg.ConfigFilePath;
                if (!System.IO.File.Exists(path)) return;
                DateTime stamp = System.IO.File.GetLastWriteTimeUtc(path);
                if (_cfgStamp == DateTime.MinValue) { _cfgStamp = stamp; WriteStatus(); return; }
                if (stamp == _cfgStamp) return;
                _cfgStamp = stamp;
                Plugin.Cfg.Reload();
                Plugin.Log.LogInfo("[ArmyPainter] config changed on disk; reloaded (repaint follows).");
                if (_editKey.Length > 0 && !_editDirty) LoadEditColours(_editKey);
                WriteStatus();
            }
            catch (Exception ex)
            {
                Plugin.Log.LogWarning("[ArmyPainter] config reload failed: " + ex.Message);
            }
        }

        // -------------------------------------------------------------- scene

        private static bool InScene(Component c)
        {
            try { return c != null && c.gameObject.activeInHierarchy && c.gameObject.scene.IsValid(); }
            catch { return false; }
        }

        /// <summary>Every unit renderer in the scene with the faction it belongs to.</summary>
        private List<KeyValuePair<Renderer, string>> CollectScene(out int units, out int characters)
        {
            var result = new List<KeyValuePair<Renderer, string>>();
            var seen = new HashSet<int>();
            units = 0; characters = 0;

            void Add(Renderer r, string faction)
            {
                if (r == null) return;
                int id;
                try { id = r.GetInstanceID(); } catch { return; }
                if (seen.Add(id)) result.Add(new KeyValuePair<Renderer, string>(r, faction));
            }

            void AddArray(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<Renderer> rs, string faction)
            {
                for (int j = 0; rs != null && j < rs.Count; j++) Add(rs[j], faction);
            }

            try
            {
                var all = Resources.FindObjectsOfTypeAll<Unit>();
                for (int i = 0; all != null && i < all.Count; i++)
                {
                    var u = all[i];
                    if (!InScene(u)) continue;
                    units++;
                    string faction;
                    try { faction = u.Faction.ToString(); } catch { continue; }
                    try { AddArray(u.GetComponentsInChildren<Renderer>(true), faction); } catch { }
                    try
                    {
                        var members = u.aliveAndDeadMembers;
                        for (int m = 0; members != null && m < members.Count; m++)
                        {
                            var ch = members[m]?.Character;
                            if (ch != null) AddArray(ch.allModelRenderers, faction);
                        }
                    }
                    catch { }
                }
            }
            catch (Exception ex) { Once("unit scan", ex); }

            // Models without a Unit (army management, unit screens, previews).
            try
            {
                var all = Resources.FindObjectsOfTypeAll<AnimatedCharacter>();
                for (int i = 0; all != null && i < all.Count; i++)
                {
                    var ac = all[i];
                    if (!InScene(ac)) continue;
                    characters++;
                    string faction = null;
                    try { if (ac.unitData != null) faction = ac.unitData.Faction.ToString(); } catch { }
                    if (faction == null)
                        try { var u = ac.GetComponentInParent<Unit>(); if (u != null) faction = u.Faction.ToString(); } catch { }
                    if (faction == null) continue;
                    Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<Renderer> rs = null;
                    try { rs = ac.allModelRenderers; } catch { }
                    if (rs == null || rs.Count == 0) try { rs = ac.GetComponentsInChildren<Renderer>(true); } catch { }
                    AddArray(rs, faction);
                }
            }
            catch (Exception ex) { Once("character scan", ex); }

            return result;
        }

        private readonly HashSet<string> _onceErrors = new HashSet<string>();

        private void Once(string where, Exception ex)
        {
            if (_onceErrors.Add(where + ex.GetType().Name))
                Plugin.Log.LogWarning("[ArmyPainter] " + where + " failed: " + ex.GetType().Name + ": " + ex.Message);
        }

        private void PaintScene(bool force)
        {
            PruneDead();
            _engine.BeginFrame();
            int deferred = 0;
            var scene = CollectScene(out int units, out int characters);
            var schemes = new Dictionary<string, Scheme?>();
            var perFaction = new Dictionary<string, int[]>(); // painted, unchanged, nothing, readFailed, restored
            int errors = 0; string firstError = null;

            foreach (var kv in scene)
            {
                var r = kv.Key;
                string faction = kv.Value;
                if (!schemes.TryGetValue(faction, out var scheme)) schemes[faction] = scheme = SchemeFor(faction);
                if (!perFaction.TryGetValue(faction, out var c)) perFaction[faction] = c = new int[5];
                try
                {
                    int rid = r.GetInstanceID();
                    _painted.TryGetValue(rid, out var pr);
                    Material[] current = ToArray(r.sharedMaterials);
                    bool ours = pr != null && SameMaterials(current, pr.Instances);

                    if (scheme == null)
                    {
                        if (ours) { Restore(pr); _painted.Remove(rid); c[4]++; }
                        continue;
                    }
                    if (ours && !force && pr.Scheme == scheme.Value.Key) { c[1]++; continue; }
                    if (pr == null || !ours)
                    {
                        if (pr != null) DestroyInstances(pr, current); // game swapped materials since
                        pr = new PaintedRenderer { R = r, Originals = current };
                    }

                    var inst = new Material[pr.Originals.Length];
                    bool any = false, readFail = false, pending = false, badgePending = false;
                    for (int i = 0; i < inst.Length; i++)
                    {
                        var orig = pr.Originals[i];
                        inst[i] = orig;
                        if (orig == null || !RecolorFilter.ShouldPaint(orig, out string prop, out Texture2D src)) continue;
                        var sch = scheme.Value;
                        Texture2D repl = _engine.GetRemap(src, sch.Key, sch.Remap);
                        if (repl == null)
                        {
                            if (_engine.Deferred) { pending = true; break; }
                            readFail = true;
                            continue;
                        }
                        Material m = pr.Instances != null && i < pr.Instances.Length && pr.Instances[i] != null &&
                                     pr.Instances[i].GetInstanceID() != orig.GetInstanceID()
                            ? pr.Instances[i]
                            : new Material(orig) { name = orig.name + " (ArmyPainter)" };
                        m.SetTexture(prop, repl);
                        // Chapter badge: the decal atlas (e.g. ULT_Logo_D) rides on _DetailAlbedoMap.
                        if (sch.Pack?.Badge != null && orig.HasProperty("_DetailAlbedoMap"))
                        {
                            var decal = orig.GetTexture("_DetailAlbedoMap")?.TryCast<Texture2D>();
                            if (decal != null && sch.Pack.IsBadgeTexture(decal.name))
                            {
                                var stamped = _engine.GetBadge(decal, sch.Key, sch.Pack);
                                if (stamped != null) m.SetTexture("_DetailAlbedoMap", stamped);
                                else if (_engine.Deferred) badgePending = true;   // finish on a later scan
                            }
                        }
                        inst[i] = m;
                        any = true;
                    }
                    if (pending) { deferred++; continue; }  // finish next scan (frame budget)
                    if (!any) { if (readFail) c[3]++; else c[2]++; continue; }
                    r.sharedMaterials = inst;
                    pr.Instances = inst;
                    pr.Scheme = badgePending ? scheme.Value.Key + "|badge-pending" : scheme.Value.Key;
                    _painted[rid] = pr;
                    c[0]++;
                }
                catch (Exception ex)
                {
                    errors++;
                    if (firstError == null) firstError = ex.GetType().Name + ": " + ex.Message;
                }
            }

            _lastModels = scene.Count;
            _lastPaintedCount = _painted.Count;
            var active = new List<string>();
            var sb = new StringBuilder();
            sb.Append($"scene: {units} units, {characters} models, {scene.Count} renderers;");
            foreach (var f in perFaction)
            {
                var s = schemes[f.Key];
                if (s != null) active.Add(f.Key);
                sb.Append($" {f.Key}{(s == null ? "(default, untouched)" : " " + s.Value.Label)}");
                if (s != null || f.Value[4] > 0)
                    sb.Append($" painted {f.Value[0]}, kept {f.Value[1]}, nothing paintable {f.Value[2]}, texture read failed {f.Value[3]}" +
                              (f.Value[4] > 0 ? $", restored {f.Value[4]}" : "") + ";");
                else sb.Append(";");
            }
            if (deferred > 0) sb.Append($" still working on {deferred} renderer(s);");
            sb.Append($" textures: {_engine.CacheHits} from bake cache, {_engine.CacheMisses} painted live;");
            if (errors > 0) sb.Append($" errors {errors} (first: {firstError})");
            _activeFactions = string.Join(", ", active);

            // Log when something was (re)painted or the scene composition changed.
            string compact = System.Text.RegularExpressions.Regex.Replace(sb.ToString(), @"kept \d+, ", "");
            bool changed = (deferred == 0 && perFaction.Values.Any(v => v[0] > 0 || v[4] > 0)) || errors > 0;
            if (changed || compact != _lastSummary)
            {
                _lastSummary = compact;
                Plugin.Log.LogInfo("[ArmyPainter] " + sb);
                if (Plugin.DiagMode.Value) DiagMaterials(scene);
                WriteStatus();
            }
        }

        private static Material[] ToArray(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppReferenceArray<Material> arr)
        {
            if (arr == null) return new Material[0];
            var result = new Material[arr.Count];
            for (int i = 0; i < result.Length; i++) result[i] = arr[i];
            return result;
        }

        private static bool SameMaterials(Material[] a, Material[] b)
        {
            if (a == null || b == null || a.Length != b.Length) return false;
            for (int i = 0; i < a.Length; i++)
            {
                int ia = a[i] == null ? 0 : a[i].GetInstanceID();
                int ib = b[i] == null ? 0 : b[i].GetInstanceID();
                if (ia != ib) return false;
            }
            return true;
        }

        private static void Restore(PaintedRenderer pr)
        {
            try { if (pr.R != null) pr.R.sharedMaterials = pr.Originals; } catch { }
            DestroyInstances(pr, null);
        }

        private static void DestroyInstances(PaintedRenderer pr, Material[] keep)
        {
            if (pr.Instances == null) return;
            var keepIds = new HashSet<int>();
            if (keep != null) foreach (var k in keep) if (k != null) keepIds.Add(k.GetInstanceID());
            if (pr.Originals != null) foreach (var o in pr.Originals) if (o != null) keepIds.Add(o.GetInstanceID());
            foreach (var m in pr.Instances)
            {
                if (m == null || keepIds.Contains(m.GetInstanceID())) continue;
                try { UnityEngine.Object.Destroy(m); } catch { }
            }
        }

        private void PruneDead()
        {
            List<int> dead = null;
            foreach (var kv in _painted)
            {
                bool alive;
                try { alive = kv.Value.R != null; } catch { alive = false; }
                if (!alive) (dead ??= new List<int>()).Add(kv.Key);
            }
            if (dead == null) return;
            foreach (var id in dead)
            {
                DestroyInstances(_painted[id], null);
                _painted.Remove(id);
            }
        }

        private void ResetAll()
        {
            int n = 0;
            foreach (var pr in _painted.Values) { Restore(pr); n++; }
            _painted.Clear();
            ClearPortraits();
            _engine.ClearCache();
            _lastSummary = "";
            Plugin.Log.LogInfo("[ArmyPainter] restored " + n + " renderers and all portraits (until the next repaint).");
            WriteStatus();
        }

        private void DiagMaterials(List<KeyValuePair<Renderer, string>> scene)
        {
            int shown = 0;
            foreach (var kv in scene)
            {
                if (shown >= 8) break;
                try
                {
                    var m = kv.Key.sharedMaterial;
                    if (m == null) continue;
                    bool ok = RecolorFilter.ShouldPaint(m, out string prop, out Texture2D tex);
                    string shader = "?"; try { shader = m.shader.name; } catch { }
                    Plugin.Log.LogInfo($"[ArmyPainter] DIAG {kv.Value} renderer '{kv.Key.name}' mat='{m.name}' shader='{shader}' " +
                                       $"queue={m.renderQueue} paintable={ok} prop={prop} tex={(tex == null ? "-" : tex.name + " " + tex.width + "x" + tex.height + " readable=" + tex.isReadable)}");
                    shown++;
                }
                catch { }
            }
        }

        // ---- 2D portraits ----------------------------------------------------
        // Approximate hue-shift of UI portraits. Off by default (quality); the
        // game's sprite reference is never changed: Image.overrideSprite shows a
        // copy and null restores the original.
        private readonly Dictionary<long, Sprite> _spriteCache = new Dictionary<long, Sprite>();
        private Dictionary<string, string> _portraitFaction = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private float _portraitNamesAge = 999f;

        private void PaintPortraits()
        {

            _portraitNamesAge += 1f;
            if (_portraitNamesAge > 10f)
            {
                _portraitNamesAge = 0f;
                _portraitFaction = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                foreach (var p in FactionPresets.All)
                    foreach (var name in PortraitNames.For(p.Key))
                        _portraitFaction[name] = p.Key;
            }

            Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<UnityEngine.UI.Image> images;
            try { images = Resources.FindObjectsOfTypeAll<UnityEngine.UI.Image>(); } catch { return; }
            int shown = 0;
            for (int i = 0; images != null && i < images.Count; i++)
            {
                try
                {
                    var img = images[i];
                    if (img == null || !img.isActiveAndEnabled) continue;
                    Sprite s = img.sprite;
                    Sprite active = img.overrideSprite;
                    bool oursActive = active != null && active.name.StartsWith("ArmyPainter_", StringComparison.Ordinal);
                    string faction = s == null ? null : PortraitFaction(s.name);
                    var scheme = faction == null ? null : SchemeFor(faction);
                    Sprite repl = null;
                    if (scheme?.Pack != null) repl = CuratedSprite(s, scheme.Value.Pack) ?? GetSpriteRemap(s, scheme.Value); // no PNG: apply the pack's rules
                    else if (scheme != null && Plugin.ApproxPortraits.Value) repl = GetSpriteRemap(s, scheme.Value);
                    if (repl != null)
                    {
                        if (!oursActive || active.GetInstanceID() != repl.GetInstanceID()) img.overrideSprite = repl;
                        shown++;
                    }
                    else if (oursActive) img.overrideSprite = null;
                }
                catch { }
            }
            if (shown != _lastPortraits)
            {
                _lastPortraits = shown;
                Plugin.Log.LogInfo($"[ArmyPainter] portraits: {shown} on screen replaced (curated pack art, or approximate if enabled).");
                WriteStatus();
            }
        }

        private readonly Dictionary<string, Sprite> _curated = new Dictionary<string, Sprite>(StringComparer.OrdinalIgnoreCase);

        /// <summary>The pack's pre-rendered portrait for this sprite (loaded once), or null.</summary>
        private Sprite CuratedSprite(Sprite s, SchemePack pack)
        {
            string key = pack.Id + "@" + pack.Version + "/" + s.name;
            if (_curated.TryGetValue(key, out var hit)) return hit;
            Sprite result = null;
            var file = pack.PortraitFile(s.name);
            if (file != null)
            {
                try
                {
                    var tex = new Texture2D(2, 2, TextureFormat.RGBA32, true, false) { name = "ArmyPainter_" + s.name };
                    if (ImageConversion.LoadImage(tex, System.IO.File.ReadAllBytes(file), false))
                    {
                        var pivot = new Vector2(s.pivot.x / Mathf.Max(1f, s.rect.width), s.pivot.y / Mathf.Max(1f, s.rect.height));
                        // Keep the original's on-screen size: scale pixels-per-unit with the resolution change.
                        float ppu = s.pixelsPerUnit * tex.width / Mathf.Max(1f, s.rect.width);
                        result = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, ppu, 0, SpriteMeshType.FullRect);
                        result.name = "ArmyPainter_" + s.name;
                    }
                }
                catch (Exception ex) { Once("curated portrait " + s.name, ex); }
            }
            _curated[key] = result;
            return result;
        }

        private string PortraitFaction(string spriteName)
        {
            if (string.IsNullOrEmpty(spriteName)) return null;
            if (_portraitFaction.TryGetValue(spriteName, out var f)) return f;
            int dash = spriteName.LastIndexOf('-');
            return dash > 0 && _portraitFaction.TryGetValue(spriteName.Substring(0, dash), out f) ? f : null;
        }

        private Sprite GetSpriteRemap(Sprite s, Scheme scheme)
        {
            long key = ((long)s.GetInstanceID() << 32) ^ (uint)scheme.Key.GetHashCode();
            if (_spriteCache.TryGetValue(key, out var hit) && hit != null) return hit;
            Texture2D tex = s.texture;
            if (tex == null) return null;
            Rect r;
            try { r = s.textureRect; } catch { r = s.rect; }
            int x = Mathf.RoundToInt(r.x), y = Mathf.RoundToInt(r.y), w = Mathf.RoundToInt(r.width), h = Mathf.RoundToInt(r.height);
            if (w <= 0 || h <= 0) return null;
            Color32[] px = RecolorEngine.ReadRegion(tex, x, y, w, h);
            if (px == null) return null;
            Color32[] outp;
            if (scheme.Pack != null)
            {
                var rgba = new byte[px.Length * 4];
                for (int i = 0, j = 0; i < px.Length; i++, j += 4) { rgba[j] = px[i].r; rgba[j + 1] = px[i].g; rgba[j + 2] = px[i].b; rgba[j + 3] = px[i].a; }
                var mapped = PaintMath.ApplyRules(rgba, scheme.Pack.RulesForPortrait(s.name));
                outp = new Color32[px.Length];
                for (int i = 0, j = 0; i < outp.Length; i++, j += 4) outp[i] = new Color32(mapped[j], mapped[j + 1], mapped[j + 2], mapped[j + 3]);
            }
            else outp = RecolorEngine.RemapPixels(px, scheme.Pri, scheme.Sec, Plugin.HueWindow.Value, Plugin.SatThreshold.Value, Plugin.BlendFeather.Value);
            var t = new Texture2D(w, h, TextureFormat.RGBA32, false, false) { name = "ArmyPainter_" + s.name };
            t.SetPixels32(outp);
            t.Apply(false, false);
            var pivot = new Vector2(s.pivot.x / Mathf.Max(1f, s.rect.width), s.pivot.y / Mathf.Max(1f, s.rect.height));
            var sprite = Sprite.Create(t, new Rect(0, 0, w, h), pivot, s.pixelsPerUnit, 0, SpriteMeshType.FullRect, s.border);
            sprite.name = "ArmyPainter_" + s.name;
            _spriteCache[key] = sprite;
            return sprite;
        }

        private void ClearPortraits()
        {
            try
            {
                var images = Resources.FindObjectsOfTypeAll<UnityEngine.UI.Image>();
                for (int i = 0; images != null && i < images.Count; i++)
                {
                    var img = images[i];
                    if (img == null) continue;
                    var active = img.overrideSprite;
                    if (active != null && active.name.StartsWith("ArmyPainter_", StringComparison.Ordinal)) img.overrideSprite = null;
                }
            }
            catch { }
            _spriteCache.Clear();
            _curated.Clear();
            _lastPortraits = 0;
        }

        // ---- status file for the configurator ---------------------------------
        private void WriteStatus()
        {
            try
            {
                string dir = System.IO.Path.Combine(BepInEx.Paths.ConfigPath, "warpstorm");
                System.IO.Directory.CreateDirectory(dir);
                string cfgStamp = _cfgStamp == DateTime.MinValue ? "" : _cfgStamp.Ticks.ToString();
                string json = "{\n" +
                    $"  \"time\": \"{DateTime.UtcNow:O}\",\n" +
                    $"  \"configStamp\": \"{cfgStamp}\",\n" +
                    $"  \"faction\": \"{_activeFactions}\",\n" +
                    $"  \"active\": {(_activeFactions.Length > 0 ? "true" : "false")},\n" +
                    $"  \"units\": {_lastModels},\n" +
                    $"  \"renderersPainted\": {_lastPaintedCount},\n" +
                    $"  \"portraitsPainted\": {_lastPortraits},\n" +
                    $"  \"summary\": \"{_lastSummary.Replace("\\", "\\\\").Replace("\"", "'")}\"\n" +
                    "}\n";
                System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "paint-status.json"), json);
            }
            catch { }
        }

        // ============================================================= UI ===
        private void OnGUI()
        {
            // Opt-in only: no Army Painter UI (not even a button) until
            // [Paint] Enabled is on. Stat-only games see nothing from this.
            if (!Plugin.PaintEnabled.Value) return;
            GUI.depth = 1;
            if (!_showUI)
            {
                if (Plugin.ShowButton.Value && GUI.Button(new Rect(Screen.width - 108, 4, 104, 26), "Army Painter"))
                    _showUI = true;
                return;
            }

            Event e = Event.current;
            if (e.type == EventType.MouseDown && e.button == 0 &&
                new Rect(_winRect.x, _winRect.y, _winRect.width, 22).Contains(e.mousePosition))
            {
                _dragOffset = e.mousePosition - new Vector2(_winRect.x, _winRect.y);
                _dragging = true;
                e.Use();
            }
            if (e.type == EventType.MouseDrag && _dragging) { _winRect.position = e.mousePosition - _dragOffset; e.Use(); }
            if (e.type == EventType.MouseUp && _dragging) { _dragging = false; e.Use(); }

            GUI.Box(_winRect, "Army Painter  v" + Plugin.Version);
            GUILayout.BeginArea(new Rect(_winRect.x + 6, _winRect.y + 24, _winRect.width - 12, _winRect.height - 30));
            DrawContents();
            GUILayout.EndArea();
        }

        private void DrawContents()
        {
            GUILayout.BeginVertical();
            GUILayout.Label("Each faction is painted everywhere it appears (yours and enemies).");
            GUILayout.Label(_lastModels + " unit renderers in scene · " + _lastPaintedCount + " painted · " + _lastPortraits + " portraits");
            GUILayout.Label("Custom schemes active: " + (_activeFactions.Length > 0 ? _activeFactions : "none"));
            if (_editKey.Length > 0 && Plugin.FactionSchemeId(_editKey).Length > 0)
                GUILayout.Label(_editKey + " uses scheme pack '" + Plugin.FactionSchemeId(_editKey) + "' (change it in the configurator).");

            GUILayout.Label("Edit faction");
            var presets = FactionPresets.All;
            for (int row = 0; row * 4 < presets.Length; row++)
            {
                GUILayout.BeginHorizontal();
                for (int i = row * 4; i < Mathf.Min(presets.Length, row * 4 + 4); i++)
                {
                    var p = presets[i];
                    var prev = GUI.backgroundColor;
                    if (p.Key == _editKey) GUI.backgroundColor = new Color(0.6f, 0.8f, 1f);
                    if (GUILayout.Button(p.Name, GUILayout.Height(22))) LoadEditColours(p.Key);
                    GUI.backgroundColor = prev;
                }
                GUILayout.EndHorizontal();
            }

            if (_editKey.Length > 0)
            {
                ColorRow("Primary", ref _pri, ref _priHex);
                ColorRow("Secondary", ref _sec, ref _secHex);
                GUILayout.BeginHorizontal();
                if (GUILayout.Button("Apply")) { Plugin.SaveFactionColor(_editKey, _pri, _sec); _editDirty = false; PaintScene(false); }
                if (GUILayout.Button("Default colours"))
                {
                    var d = FactionPresets.Find(_editKey);
                    if (d.HasValue) { Plugin.SaveFactionColor(_editKey, d.Value.Primary, d.Value.Secondary); LoadEditColours(_editKey); PaintScene(false); }
                }
                GUILayout.EndHorizontal();
            }

            GUILayout.Space(6);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Repaint now")) PaintScene(true);
            if (GUILayout.Button("Show original paint")) ResetAll();
            if (GUILayout.Button("Close")) _showUI = false;
            GUILayout.EndHorizontal();
            GUILayout.EndVertical();
        }

        private void LoadEditColours(string key)
        {
            _editKey = key;
            if (!Plugin.TryGetFactionColor(key, out _pri, out _sec))
            {
                var p = FactionPresets.Find(key);
                if (p.HasValue) { _pri = p.Value.Primary; _sec = p.Value.Secondary; }
            }
            _priHex = ColorUtil.ToHex(_pri);
            _secHex = ColorUtil.ToHex(_sec);
            _editDirty = false;
        }

        private void ColorRow(string label, ref Color32 c, ref string hex)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, GUILayout.Width(70));
            GUI.color = new Color(c.r / 255f, c.g / 255f, c.b / 255f, 1f);
            GUILayout.Box("", GUILayout.Width(26), GUILayout.Height(20));
            GUI.color = Color.white;
            Color32 before = c;
            int r = (int)Mathf.Round(GUILayout.HorizontalSlider(c.r, 0f, 255f, GUILayout.Width(56)));
            int g = (int)Mathf.Round(GUILayout.HorizontalSlider(c.g, 0f, 255f, GUILayout.Width(56)));
            int b = (int)Mathf.Round(GUILayout.HorizontalSlider(c.b, 0f, 255f, GUILayout.Width(56)));
            c = new Color32((byte)Mathf.Clamp(r, 0, 255), (byte)Mathf.Clamp(g, 0, 255), (byte)Mathf.Clamp(b, 0, 255), 255);
            string newHex = GUILayout.TextField(hex, 6, GUILayout.Width(60));
            if (newHex != hex) { hex = newHex; if (ColorUtil.TryParseHex(hex, out Color32 parsed)) c = parsed; }
            if (!c.Equals(before)) { hex = ColorUtil.ToHex(c); _editDirty = true; }
            GUILayout.EndHorizontal();
        }
    }

    // ============================================================== engine ===
    public static class RecolorFilter
    {
        // Albedo slot names, most likely first (the game's unit shader uses _MainTex).
        private static readonly string[] AlbedoProps = { "_MainTex", "_BaseMap", "_BaseColorMap", "_Albedo" };

        /// <summary>
        /// Opaque material with an albedo texture. NOTE: Il2CppInterop wraps
        /// GetTexture()'s result as Texture, so a C# "as Texture2D" is always null;
        /// TryCast is required.
        /// </summary>
        public static bool ShouldPaint(Material m, out string prop, out Texture2D tex)
        {
            prop = null; tex = null;
            try
            {
                if (m.renderQueue >= 3000) return false;                        // transparent / overlay FX
                if (m.IsKeywordEnabled("_ALPHABLEND_ON") || m.IsKeywordEnabled("_ALPHAPREMULTIPLY_ON")) return false;
                foreach (var p in AlbedoProps)
                {
                    if (!m.HasProperty(p)) continue;
                    var t = m.GetTexture(p)?.TryCast<Texture2D>();
                    if (t == null || t.width <= 0 || t.height <= 0) continue;
                    prop = p; tex = t;
                    return true;
                }
                return false;
            }
            catch { return false; }
        }
    }

    /// <summary>
    /// Portrait sprite names per faction: from the game's own UnitData icon
    /// references (once loaded) plus the BattleSector Tools catalog (embedded).
    /// </summary>
    public static class PortraitNames
    {
        private static Dictionary<int, HashSet<string>> _catalog;

        public static HashSet<string> For(string factionKey)
        {
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            if (!Enum.TryParse(factionKey, out Faction faction)) return names;

            LoadCatalog();
            if (_catalog.TryGetValue((int)faction, out var fromCatalog)) names.UnionWith(fromCatalog);

            try
            {
                if (RuntimeDataTables.HasInstance)
                {
                    var values = RuntimeDataTables.Instance.UnitDataTable?.values;
                    for (int i = 0; values != null && i < values.Count; i++)
                    {
                        var d = values[i];
                        if (d == null || d.Faction != faction) continue;
                        Add(names, d.IconRef);
                        Add(names, d.SmallIconRef);
                    }
                }
            }
            catch { }
            return names;
        }

        public static bool Matches(HashSet<string> names, string spriteName)
        {
            if (string.IsNullOrEmpty(spriteName)) return false;
            if (names.Contains(spriteName)) return true;
            int dash = spriteName.LastIndexOf('-');               // "FooIcon-small"
            return dash > 0 && names.Contains(spriteName.Substring(0, dash));
        }

        private static void Add(HashSet<string> names, UnityEngine.AddressableAssets.AssetReferenceSprite r)
        {
            if (r == null) return;
            try
            {
                var sub = r.SubObjectName;
                if (!string.IsNullOrEmpty(sub)) names.Add(sub);
                var asset = r.Asset;
                var sprite = asset == null ? null : asset.TryCast<Sprite>();
                if (sprite != null) names.Add(sprite.name);
            }
            catch { }
        }

        private static void LoadCatalog()
        {
            if (_catalog != null) return;
            _catalog = new Dictionary<int, HashSet<string>>();
            try
            {
                using var stream = typeof(PortraitNames).Assembly.GetManifestResourceStream("units.json");
                if (stream == null) return;
                using var doc = System.Text.Json.JsonDocument.Parse(stream);
                foreach (var u in doc.RootElement.EnumerateArray())
                {
                    if (!u.TryGetProperty("faction", out var f) || !u.TryGetProperty("portrait", out var p)) continue;
                    var name = p.GetString();
                    if (string.IsNullOrEmpty(name)) continue;
                    int id = f.GetInt32();
                    if (!_catalog.TryGetValue(id, out var set)) _catalog[id] = set = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                    set.Add(name);
                }
            }
            catch (Exception ex)
            {
                Plugin.Log.LogWarning("[ArmyPainter] portrait catalog unreadable: " + ex.Message);
            }
        }
    }

    public class RecolorEngine
    {
        private readonly Dictionary<int, Texture2D> _cache = new Dictionary<int, Texture2D>();
        private readonly Queue<int> _lru = new Queue<int>();
        private const int CacheBudget = 96;

        public int CacheSize => _cache.Count;

        public void ClearCache()
        {
            _cache.Clear();
            _lru.Clear();
        }

        /// <summary>Set when this frame's time budget ran out; the caller retries next scan.</summary>
        public bool Deferred;
        private readonly System.Diagnostics.Stopwatch _budget = new System.Diagnostics.Stopwatch();
        private const double BudgetMs = 60;

        public void BeginFrame() { Deferred = false; _budget.Restart(); }

        /// <summary>
        /// Recoloured copy of <paramref name="src"/>. Unit albedos are 4096² here, so
        /// the copy is made at most MaxTextureSize and DXT-compressed (≈5 MB instead
        /// of ≈85 MB each); new textures are only built while the frame budget lasts.
        /// </summary>
        public Texture2D GetRemap(Texture2D src, string schemeKey, Func<byte[], string, byte[]> remap)
        {
            int key = Hash(src.GetInstanceID(), schemeKey);
            if (_cache.TryGetValue(key, out Texture2D hit) && hit != null) return hit;
            if (_budget.Elapsed.TotalMilliseconds > BudgetMs) { Deferred = true; return null; }

            // Baked by the configurator (or by an earlier session): just upload it.
            var baked = LoadBaked(src, schemeKey);
            if (baked != null)
            {
                CacheHits++;
                _cache[key] = baked;
                _lru.Enqueue(key);
                return baked;
            }
            CacheMisses++;
            if (_cache.Count >= CacheBudget && _lru.Count > 0)
            {
                // Drop from cache only - never Destroy here: renderers may still use it.
                while (_lru.Count > 0)
                {
                    int evict = _lru.Dequeue();
                    if (_cache.Remove(evict)) break;
                }
            }

            int max = Mathf.Clamp(Plugin.MaxTextureSize.Value, 256, 4096);
            PaintCache.TargetSize(src.width, src.height, max, out int w, out int h);

            Color32[] px = ReadScaled(src, w, h);
            if (px == null)
            {
                Plugin.Log.LogWarning("[ArmyPainter] could not read texture '" + src.name + "'.");
                return null;
            }

            byte[] rgba = new byte[px.Length * 4];
            for (int i = 0, j = 0; i < px.Length; i++, j += 4)
            {
                rgba[j] = px[i].r; rgba[j + 1] = px[i].g; rgba[j + 2] = px[i].b; rgba[j + 3] = px[i].a;
            }
            byte[] mapped = remap(rgba, src.name);
            var outp = new Color32[px.Length];
            for (int i = 0, j = 0; i < outp.Length; i++, j += 4)
                outp[i] = new Color32(mapped[j], mapped[j + 1], mapped[j + 2], mapped[j + 3]);

            Texture2D tex;
            try
            {
                tex = new Texture2D(w, h, TextureFormat.RGBA32, true, false) { name = "ArmyPainter_" + src.name };
                tex.SetPixels32(outp);
                tex.Apply(true, false);
                try { tex.Compress(false); } catch { /* keep RGBA32 */ }
                SaveBaked(tex, src, schemeKey);
                tex.Apply(false, true); // upload and drop the CPU copy
            }
            catch (Exception e) { Plugin.Log.LogWarning("[ArmyPainter] texture build failed: " + e.Message); return null; }

            _cache[key] = tex;
            _lru.Enqueue(key);
            return tex;
        }

        public int CacheHits, CacheMisses;
        private readonly Dictionary<string, byte[]> _stencils = new Dictionary<string, byte[]>();
        private readonly Dictionary<string, int[]> _stencilSize = new Dictionary<string, int[]>();

        /// <summary>The decal atlas with the pack's badge stamped over the chapter symbol (cached like albedos).</summary>
        public Texture2D GetBadge(Texture2D src, string schemeKey, SchemePack pack)
        {
            string cacheName = "badge-" + src.name;
            int key = Hash(src.GetInstanceID(), "badge|" + schemeKey);
            if (_cache.TryGetValue(key, out Texture2D hit) && hit != null) return hit;
            if (_budget.Elapsed.TotalMilliseconds > BudgetMs) { Deferred = true; return null; }

            var baked = LoadBaked(src, schemeKey, cacheName);
            if (baked == null)
            {
                if (!LoadStencil(pack, out var stencil, out int sw, out int sh)) return null;
                int max = Mathf.Clamp(Plugin.MaxTextureSize.Value, 256, 4096);
                PaintCache.TargetSize(src.width, src.height, max, out int w, out int h);
                Color32[] px = ReadScaled(src, w, h);
                if (px == null) return null;
                var rgba = new byte[px.Length * 4];
                for (int i = 0, j = 0; i < px.Length; i++, j += 4) { rgba[j] = px[i].r; rgba[j + 1] = px[i].g; rgba[j + 2] = px[i].b; rgba[j + 3] = px[i].a; }
                var b = pack.Badge;
                PaintMath.StampBadge(rgba, w, h, b.U0, b.V0, b.U1, b.V1, stencil, sw, sh, b.Scale);
                var outp = new Color32[px.Length];
                for (int i = 0, j = 0; i < outp.Length; i++, j += 4) outp[i] = new Color32(rgba[j], rgba[j + 1], rgba[j + 2], rgba[j + 3]);
                try
                {
                    baked = new Texture2D(w, h, TextureFormat.RGBA32, true, false) { name = "ArmyPainter_" + src.name };
                    baked.SetPixels32(outp);
                    baked.Apply(true, false);
                    try { baked.Compress(false); } catch { }
                    SaveBaked(baked, src, schemeKey, cacheName);
                    baked.Apply(false, true);
                }
                catch (Exception e) { Plugin.Log.LogWarning("[ArmyPainter] badge build failed: " + e.Message); return null; }
            }
            _cache[key] = baked;
            _lru.Enqueue(key);
            return baked;
        }

        private bool LoadStencil(SchemePack pack, out byte[] rgba, out int w, out int h)
        {
            string file = pack.BadgeFile;
            rgba = null; w = h = 0;
            if (file == null) return false;
            if (_stencils.TryGetValue(file, out rgba)) { w = _stencilSize[file][0]; h = _stencilSize[file][1]; return rgba != null; }
            try
            {
                var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false, false);
                if (ImageConversion.LoadImage(tex, System.IO.File.ReadAllBytes(file), false))
                {
                    var px = tex.GetPixels32();                   // rows bottom-up, like the atlas
                    rgba = new byte[px.Length * 4];
                    for (int i = 0, j = 0; i < px.Length; i++, j += 4) { rgba[j] = px[i].r; rgba[j + 1] = px[i].g; rgba[j + 2] = px[i].b; rgba[j + 3] = px[i].a; }
                    w = tex.width; h = tex.height;
                }
                UnityEngine.Object.Destroy(tex);
            }
            catch (Exception e) { Plugin.Log.LogWarning("[ArmyPainter] badge image unreadable: " + e.Message); }
            _stencils[file] = rgba;
            _stencilSize[file] = new[] { w, h };
            return rgba != null;
        }
        public static string CacheRoot => System.IO.Path.Combine(Paths.CachePath, "warpstorm", "paint");

        private static Texture2D LoadBaked(Texture2D src, string schemeKey, string cacheName = null)
        {
            if (!PaintCache.TryRead(CacheRoot, schemeKey, cacheName ?? src.name, out int w, out int h, out int mips, out int format,
                                    out int srcW, out int srcH, out byte[] data)) return null;
            if (format != PaintCache.FormatDxt5 || srcW != src.width || srcH != src.height) return null;
            try
            {
                var tex = new Texture2D(w, h, TextureFormat.DXT5, mips > 1, false) { name = "ArmyPainter_" + src.name };
                if (tex.mipmapCount != mips) { UnityEngine.Object.Destroy(tex); return null; }
                tex.LoadRawTextureData((Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<byte>)data);
                tex.Apply(false, true);
                return tex;
            }
            catch (Exception e)
            {
                Plugin.Log.LogWarning("[ArmyPainter] baked texture '" + src.name + "' unusable (" + e.Message + "); repainting.");
                return null;
            }
        }

        private static void SaveBaked(Texture2D tex, Texture2D src, string schemeKey, string cacheName = null)
        {
            try
            {
                if (tex.format != TextureFormat.DXT5) return;
                byte[] data = tex.GetRawTextureData();
                int w = tex.width, h = tex.height, mips = tex.mipmapCount, sw = src.width, sh = src.height;
                string name = cacheName ?? src.name;
                System.Threading.Tasks.Task.Run(() =>
                {
                    try { PaintCache.Write(CacheRoot, schemeKey, name, w, h, mips, PaintCache.FormatDxt5, sw, sh, data); }
                    catch { /* cache is best effort */ }
                });
            }
            catch { }
        }

        private static Color32[] ReadScaled(Texture2D src, int w, int h)
        {
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
                Plugin.Log.LogWarning("[ArmyPainter] read failed for '" + src.name + "': " + e.Message);
                return null;
            }
        }

        /// <summary>Shared with the configurator preview (shared/PaintMath.cs).</summary>
        public static Color32[] RemapPixels(Color32[] px, Color32 pri, Color32 sec, float hueWindow, float satThreshold, float feather)
        {
            byte[] rgba = new byte[px.Length * 4];
            for (int i = 0, j = 0; i < px.Length; i++, j += 4)
            {
                rgba[j] = px[i].r; rgba[j + 1] = px[i].g; rgba[j + 2] = px[i].b; rgba[j + 3] = px[i].a;
            }
            byte[] mapped = PaintMath.Remap(rgba, pri.r, pri.g, pri.b, sec.r, sec.g, sec.b, hueWindow, satThreshold, feather);
            Color32[] outp = new Color32[px.Length];
            for (int i = 0, j = 0; i < outp.Length; i++, j += 4)
                outp[i] = new Color32(mapped[j], mapped[j + 1], mapped[j + 2], mapped[j + 3]);
            return outp;
        }

        /// <summary>Reads a sub-rectangle (e.g. a sprite inside an atlas) of any texture.</summary>
        public static Color32[] ReadRegion(Texture2D src, int x, int y, int w, int h)
        {
            if (w <= 0 || h <= 0) return null;
            try
            {
                RenderTexture rt = RenderTexture.GetTemporary(src.width, src.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
                var prev = RenderTexture.active;
                try
                {
                    Graphics.Blit(src, rt);
                    RenderTexture.active = rt;
                    var tmp = new Texture2D(w, h, TextureFormat.RGBA32, false, false);
                    tmp.ReadPixels(new Rect(x, y, w, h), 0, 0);
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
                Plugin.Log.LogWarning("[ArmyPainter] ReadRegion failed for '" + src.name + "': " + e.Message);
                return null;
            }
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

        private static int Hash(int texId, string scheme)
        {
            unchecked { return texId * 397 ^ scheme.GetHashCode(); }
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
