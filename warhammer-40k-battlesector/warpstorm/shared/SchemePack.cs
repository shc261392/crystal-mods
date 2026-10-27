using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace Warpstorm.Shared
{
    /// <summary>
    /// A curated Army Painter scheme ("Salamanders"): repaints one game faction.
    ///
    /// Folder layout (also the layout inside a pack .zip):
    ///   scheme.json            this file's model (see below)
    ///   portraits/&lt;sprite&gt;.png pre-rendered, curated unit portraits (by in-game sprite name)
    ///
    /// scheme.json:
    /// {
    ///   "id": "salamanders", "name": "Salamanders", "version": "1.0.0", "author": "...",
    ///   "faction": "Ultramarines",                    // game Faction enum name it repaints
    ///   "primary": "1F5B2C", "secondary": "1C1D21",  // swatches shown in the UI
    ///   "rules":    [ { "hue": 222, "width": 26, "feather": 14, "satMin": 0.12, "to": "1F5B2C" } ],
    ///   "textures": { "ULT_INT_D": [ ...rules... ] }, // optional per-texture overrides (3D)
    ///   "portraits": { "CaptainIcon": [ ...rules... ] } // optional per-portrait overrides (build time)
    /// }
    /// Hue / width / feather are in degrees; satScale / valScale tweak the result.
    /// </summary>
    public sealed class SchemePack
    {
        public string Id = "";
        public string Name = "";
        public string Version = "";
        public string Author = "";
        public string Description = "";
        public string Faction = "";
        public string Primary = "", Secondary = "";
        public List<PaintMath.Rule> Rules = new List<PaintMath.Rule>();
        public Dictionary<string, List<PaintMath.Rule>> Textures = new Dictionary<string, List<PaintMath.Rule>>(StringComparer.OrdinalIgnoreCase);
        public Dictionary<string, List<PaintMath.Rule>> Portraits = new Dictionary<string, List<PaintMath.Rule>>(StringComparer.OrdinalIgnoreCase);
        public string Dir = "";

        /// <summary>
        /// Optional chapter badge: replaces the chapter symbol in the faction's
        /// decal atlases ("textures", e.g. ULT_Logo_D) inside "rect" (UV, origin
        /// bottom-left: u0, v0, u1, v1) with "image" (white stencil on transparent).
        /// </summary>
        public sealed class BadgeDef
        {
            public List<string> Textures = new List<string>();
            public float U0, V0, U1, V1;
            public string Image = "";
            public float Scale = 0.92f;
        }

        public BadgeDef Badge;

        public bool IsBadgeTexture(string name)
            => Badge != null && name != null && Badge.Textures.Exists(t => string.Equals(t, name, StringComparison.OrdinalIgnoreCase));

        public string BadgeFile => Badge == null || Dir.Length == 0 ? null : Path.Combine(Dir, Badge.Image);

        public List<PaintMath.Rule> RulesForTexture(string name)
            => name != null && Textures.TryGetValue(name, out var r) ? r : Rules;

        public List<PaintMath.Rule> RulesForPortrait(string name)
            => name != null && Portraits.TryGetValue(name, out var r) ? r : Rules;

        /// <summary>The curated portrait PNG for a sprite, or null.</summary>
        public string PortraitFile(string spriteName)
        {
            if (string.IsNullOrEmpty(spriteName) || Dir.Length == 0) return null;
            var p = Path.Combine(Dir, "portraits", spriteName + ".png");
            if (File.Exists(p)) return p;
            int dash = spriteName.LastIndexOf('-');   // "FooIcon-small" -> FooIcon.png
            if (dash > 0)
            {
                p = Path.Combine(Dir, "portraits", spriteName.Substring(0, dash) + ".png");
                if (File.Exists(p)) return p;
            }
            return null;
        }

        public static SchemePack Load(string dir)
        {
            var file = Path.Combine(dir, "scheme.json");
            var pack = Parse(File.ReadAllText(file));
            pack.Dir = dir;
            if (pack.Id.Length == 0) pack.Id = Path.GetFileName(dir.TrimEnd('/', '\\'));
            return pack;
        }

        public static SchemePack Parse(string json)
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            var root = doc.RootElement;
            var p = new SchemePack
            {
                Id = Str(root, "id"),
                Name = Str(root, "name"),
                Version = Str(root, "version"),
                Author = Str(root, "author"),
                Description = Str(root, "description"),
                Faction = Str(root, "faction"),
                Primary = Str(root, "primary"),
                Secondary = Str(root, "secondary"),
            };
            if (p.Faction.Length == 0) throw new FormatException("scheme.json: \"faction\" is required");
            if (root.TryGetProperty("rules", out var rules)) p.Rules = ParseRules(rules);
            if (root.TryGetProperty("textures", out var tex) && tex.ValueKind == JsonValueKind.Object)
                foreach (var t in tex.EnumerateObject()) p.Textures[t.Name] = ParseRules(t.Value);
            if (root.TryGetProperty("portraits", out var por) && por.ValueKind == JsonValueKind.Object)
                foreach (var t in por.EnumerateObject()) p.Portraits[t.Name] = ParseRules(t.Value);
            if (root.TryGetProperty("badge", out var b) && b.ValueKind == JsonValueKind.Object)
            {
                var badge = new BadgeDef { Image = Str(b, "image"), Scale = Num(b, "scale", 0.92f) };
                if (b.TryGetProperty("textures", out var bt) && bt.ValueKind == JsonValueKind.Array)
                    foreach (var t in bt.EnumerateArray()) if (t.ValueKind == JsonValueKind.String) badge.Textures.Add(t.GetString());
                if (b.TryGetProperty("rect", out var r) && r.ValueKind == JsonValueKind.Array && r.GetArrayLength() == 4)
                {
                    badge.U0 = (float)r[0].GetDouble(); badge.V0 = (float)r[1].GetDouble();
                    badge.U1 = (float)r[2].GetDouble(); badge.V1 = (float)r[3].GetDouble();
                }
                if (badge.Image.Length == 0 || badge.Textures.Count == 0 || badge.U1 <= badge.U0 || badge.V1 <= badge.V0)
                    throw new FormatException("scheme.json: badge needs image, textures and rect [u0, v0, u1, v1]");
                if (badge.Image.Contains("..")) throw new FormatException("scheme.json: badge image must be inside the pack");
                p.Badge = badge;
            }
            if (p.Rules.Count == 0) throw new FormatException("scheme.json: \"rules\" must contain at least one rule");
            return p;
        }

        private static List<PaintMath.Rule> ParseRules(JsonElement arr)
        {
            var list = new List<PaintMath.Rule>();
            if (arr.ValueKind != JsonValueKind.Array) return list;
            foreach (var e in arr.EnumerateArray())
            {
                var to = Str(e, "to").TrimStart('#');
                if (to.Length != 6) throw new FormatException("rule \"to\" must be RRGGBB");
                list.Add(new PaintMath.Rule
                {
                    Hue = Num(e, "hue", 0) / 360f,
                    HueWidth = Num(e, "width", 25) / 360f,
                    Feather = Num(e, "feather", 12) / 360f,
                    SatMin = Num(e, "satMin", 0.1f),
                    ValMin = Num(e, "valMin", 0f),
                    ValMax = Num(e, "valMax", 1f),
                    SatScale = Num(e, "satScale", 1f),
                    ValScale = Num(e, "valScale", 1f),
                    R = Convert.ToByte(to.Substring(0, 2), 16),
                    G = Convert.ToByte(to.Substring(2, 2), 16),
                    B = Convert.ToByte(to.Substring(4, 2), 16),
                });
            }
            return list;
        }

        /// <summary>Finds every pack folder (containing scheme.json) under the given roots.</summary>
        public static List<SchemePack> Discover(IEnumerable<string> roots, Action<string> onError = null)
        {
            var result = new List<SchemePack>();
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var root in roots)
            {
                if (string.IsNullOrEmpty(root) || !Directory.Exists(root)) continue;
                foreach (var dir in Directory.GetDirectories(root))
                {
                    if (!File.Exists(Path.Combine(dir, "scheme.json"))) continue;
                    try
                    {
                        var pack = Load(dir);
                        if (seen.Add(pack.Id)) result.Add(pack); // first root wins (user packs override built-ins)
                    }
                    catch (Exception ex)
                    {
                        onError?.Invoke(dir + ": " + ex.Message);
                    }
                }
            }
            return result;
        }

        private static string Str(JsonElement e, string k)
            => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";

        private static float Num(JsonElement e, string k, float d)
            => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? (float)v.GetDouble() : d;
    }
}
