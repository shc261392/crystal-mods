using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace Warpstorm.Configurator;

/// <summary>A BepInEx setting the configurator exposes (plugin hotkeys, paint tuning).</summary>
public sealed class SettingDef
{
    public string File = "";        // "warpstorm" | "armypainter"
    public string Section = "";
    public string Name = "";
    public string Type = "bool";    // bool | key | float
    public string Default = "";
    public double Min, Max;
    public string Id => File + ":" + Section + "/" + Name;
}

/// <summary>
/// All editable state, loaded from and saved to the game's BepInEx config:
///  * stat edits     -> BepInEx/config/warpstorm/config.json
///  * paint colours  -> BepInEx/config/com.crystalmods.armypainter.cfg
///  * settings       -> both .cfg files
/// Tracks what is unsaved by comparing against the last load/save.
/// </summary>
public sealed class EditSession
{
    // Labels/hints live in the string tables: setting.<File>.<Name>[.hint]
    public static readonly SettingDef[] Settings =
    {
        new() { File = "warpstorm", Section = "General", Name = "Enabled", Type = "bool", Default = "true" },
        new() { File = "warpstorm", Section = "General", Name = "ToggleKey", Type = "key", Default = "291" },
        new() { File = "warpstorm", Section = "General", Name = "ReloadKey", Type = "key", Default = "290" },
        new() { File = "warpstorm", Section = "General", Name = "ShowStatus", Type = "bool", Default = "true" },
        new() { File = "armypainter", Section = "UI", Name = "ToggleKey", Type = "key", Default = "282" },
        new() { File = "armypainter", Section = "UI", Name = "ShowButton", Type = "bool", Default = "true" },
        new() { File = "armypainter", Section = "Paint", Name = "Enabled", Type = "bool", Default = "false" },
        new() { File = "armypainter", Section = "Paint", Name = "AutoApply", Type = "bool", Default = "true" },
        new() { File = "armypainter", Section = "Paint", Name = "ApproxPortraits", Type = "bool", Default = "false" },
        new() { File = "armypainter", Section = "Paint", Name = "MaxTextureSize", Type = "size", Default = "2048" },
        new() { File = "armypainter", Section = "Paint", Name = "HueWindow", Type = "float", Default = "0.16", Min = 0.03, Max = 0.5 },
        new() { File = "armypainter", Section = "Paint", Name = "SatThreshold", Type = "float", Default = "0.08", Min = 0, Max = 0.5 },
        new() { File = "armypainter", Section = "Paint", Name = "BlendFeather", Type = "float", Default = "0.08", Min = 0, Max = 0.5 },
        new() { File = "armypainter", Section = "Diagnostics", Name = "DiagMode", Type = "bool", Default = "false" },
    };

    public Catalog Catalog { get; }
    public string GameDir { get; private set; } = "";
    public string GameVersion { get; private set; } = "unknown";

    public Dictionary<string, Dictionary<string, string>> UnitOriginals { get; set; } = new();
    public Dictionary<string, Dictionary<string, string>> WeaponOriginals { get; set; } = new();
    public bool Verified { get; set; }

    public readonly Dictionary<string, Dictionary<string, object>> UnitEdits = new();
    public readonly Dictionary<string, Dictionary<string, object>> WeaponEdits = new();
    public bool Enabled { get; set; } = true;

    /// <summary>Faction key -> (primary, secondary) hex RRGGBB.</summary>
    public readonly Dictionary<string, (string pri, string sec)> Paint = new();
    /// <summary>Faction key -> curated scheme pack id ("" = use the colours).</summary>
    public readonly Dictionary<string, string> PaintScheme = new();
    public List<Warpstorm.Shared.SchemePack> Packs { get; private set; } = new();
    public readonly Dictionary<string, string> SettingValues = new();

    private Dictionary<string, string> _baseline = new();

    public event Action Changed;

    public EditSession(Catalog catalog)
    {
        Catalog = catalog;
        ResetPaintToDefaults();
        foreach (var s in Settings) SettingValues[s.Id] = s.Default;
        _baseline = Snapshot();
    }

    public bool HasGame => GameDir.Length > 0;
    public string StatsConfigPath => ConfigStore.DefaultPath(GameDir);
    public string PaintConfigPath => ConfigStore.ArmyPainterConfigPath(GameDir);
    public string PluginConfigPath => ConfigStore.PluginConfigPath(GameDir);

    public void NotifyChanged() => Changed?.Invoke();

    // ------------------------------------------------------------- load/save

    /// <summary>Points the session at a game folder and loads whatever is saved there.</summary>
    public List<string> Open(string gameDir)
    {
        var notes = new List<string>();
        GameDir = gameDir;
        GameVersion = VersionReader.Detect(gameDir);
        Verified = false;
        UnitOriginals = new();
        WeaponOriginals = new();
        UnitEdits.Clear();
        WeaponEdits.Clear();
        Enabled = true;
        ResetPaintToDefaults();
        foreach (var s in Settings) SettingValues[s.Id] = s.Default;

        if (File.Exists(StatsConfigPath))
        {
            try
            {
                var cfg = ConfigStore.Import(StatsConfigPath);
                Merge(UnitEdits, cfg.Units);
                Merge(WeaponEdits, cfg.Weapons);
                Enabled = cfg.Enabled;
                notes.Add(Loc.F("status.loadedEdits", cfg.Fields));
            }
            catch (Exception ex)
            {
                notes.Add(Loc.F("status.configUnreadable", ex.Message));
            }
        }

        var paint = BepInExCfg.Read(PaintConfigPath);
        foreach (var f in Catalog.PaintDefaults)
        {
            var pri = Hex.Normalize(paint.GetValueOrDefault(BepInExCfg.Key("Faction." + f.Key, "Primary"))) ?? f.Primary;
            var sec = Hex.Normalize(paint.GetValueOrDefault(BepInExCfg.Key("Faction." + f.Key, "Secondary"))) ?? f.Secondary;
            Paint[f.Key] = (pri, sec);
            PaintScheme[f.Key] = (paint.GetValueOrDefault(BepInExCfg.Key("Faction." + f.Key, "Scheme")) ?? "").Trim();
        }
        RefreshPacks();
        var plugin = BepInExCfg.Read(PluginConfigPath);
        foreach (var s in Settings)
        {
            var source = s.File == "warpstorm" ? plugin : paint;
            if (source.TryGetValue(BepInExCfg.Key(s.Section, s.Name), out var v) && v.Length > 0)
                SettingValues[s.Id] = v;
        }

        _baseline = Snapshot();
        Changed?.Invoke();
        return notes;
    }

    public void Save()
    {
        if (!HasGame) throw new InvalidOperationException(Loc.T("status.pickFolderFirst"));

        ConfigStore.Save(StatsConfigPath, GameVersion, Enabled, CleanUnits(), CleanWeapons());

        var paint = new Dictionary<string, string>();
        foreach (var (key, (pri, sec)) in Paint)
        {
            paint[BepInExCfg.Key("Faction." + key, "Primary")] = pri;
            paint[BepInExCfg.Key("Faction." + key, "Secondary")] = sec;
            paint[BepInExCfg.Key("Faction." + key, "Scheme")] = PaintScheme.GetValueOrDefault(key, "");
        }
        var plugin = new Dictionary<string, string>();
        foreach (var s in Settings)
            (s.File == "warpstorm" ? plugin : paint)[BepInExCfg.Key(s.Section, s.Name)] = SettingValues[s.Id];

        BepInExCfg.Update(PaintConfigPath, paint);
        BepInExCfg.Update(PluginConfigPath, plugin);

        _baseline = Snapshot();
        Changed?.Invoke();
    }

    public void ApplyImport(ImportedConfig imported)
    {
        Merge(UnitEdits, imported.Units);
        Merge(WeaponEdits, imported.Weapons);
        Enabled = imported.Enabled;
        Changed?.Invoke();
    }

    /// <summary>Drops every unsaved change by re-reading the files.</summary>
    public void Revert()
    {
        var originals = (UnitOriginals, WeaponOriginals, Verified);
        if (HasGame) Open(GameDir);
        (UnitOriginals, WeaponOriginals, Verified) = originals;
        Changed?.Invoke();
    }

    private static void Merge(Dictionary<string, Dictionary<string, object>> target,
                              Dictionary<string, Dictionary<string, object>> source)
    {
        foreach (var (id, fields) in source)
        {
            if (!target.TryGetValue(id, out var dest)) target[id] = dest = new Dictionary<string, object>();
            foreach (var (k, v) in fields) dest[k] = v;
        }
    }

    // ------------------------------------------------------------ stat edits

    public Dictionary<string, Dictionary<string, object>> Edits(bool weapon) => weapon ? WeaponEdits : UnitEdits;
    public Dictionary<string, Dictionary<string, string>> Originals(bool weapon) => weapon ? WeaponOriginals : UnitOriginals;

    /// <summary>Original value: from the game bundle, else the catalog, else null.</summary>
    public string Original(CatalogItem item, string field)
    {
        if (Originals(item.IsWeapon).TryGetValue(item.Id, out var o) && o.TryGetValue(field, out var v)) return v;
        return item.CatalogStats.TryGetValue(field, out var c) ? c : null;
    }

    public object Edit(CatalogItem item, string field)
        => Edits(item.IsWeapon).TryGetValue(item.Id, out var e) && e.TryGetValue(field, out var v) ? v : null;

    public bool IsEdited(CatalogItem item) => Edits(item.IsWeapon).TryGetValue(item.Id, out var e) && e.Count > 0;

    public int EditCount(CatalogItem item) => Edits(item.IsWeapon).TryGetValue(item.Id, out var e) ? e.Count : 0;

    /// <summary>Sets (or with null clears) an edit. A value equal to the original clears it too.</summary>
    public void SetEdit(CatalogItem item, string field, object value)
    {
        var edits = Edits(item.IsWeapon);
        if (!edits.TryGetValue(item.Id, out var e)) edits[item.Id] = e = new Dictionary<string, object>();

        var original = Original(item, field);
        if (value == null || (original != null && ValueEquals(value, original))) e.Remove(field);
        else e[field] = value;
        if (e.Count == 0) edits.Remove(item.Id);
        Changed?.Invoke();
    }

    public void ClearEdits(CatalogItem item)
    {
        Edits(item.IsWeapon).Remove(item.Id);
        Changed?.Invoke();
    }

    /// <summary>The value the game will use: the edit if any, else the original.</summary>
    public string Effective(CatalogItem item, string field)
    {
        var e = Edit(item, field);
        return e != null ? Format(e) : Original(item, field);
    }

    public int StatEditCount => UnitEdits.Values.Sum(d => d.Count) + WeaponEdits.Values.Sum(d => d.Count);

    private Dictionary<string, Dictionary<string, object>> CleanUnits() => Clean(UnitEdits, UnitOriginals);
    private Dictionary<string, Dictionary<string, object>> CleanWeapons() => Clean(WeaponEdits, WeaponOriginals);

    public (Dictionary<string, Dictionary<string, object>> units, Dictionary<string, Dictionary<string, object>> weapons) CleanEdits()
        => (CleanUnits(), CleanWeapons());

    private static Dictionary<string, Dictionary<string, object>> Clean(
        Dictionary<string, Dictionary<string, object>> edits,
        Dictionary<string, Dictionary<string, string>> originals)
    {
        var result = new Dictionary<string, Dictionary<string, object>>();
        foreach (var (id, fields) in edits)
        {
            originals.TryGetValue(id, out var orig);
            var keep = new Dictionary<string, object>();
            foreach (var (key, value) in fields)
            {
                if (orig != null && orig.TryGetValue(key, out var os) && ValueEquals(value, os)) continue;
                keep[key] = value;
            }
            if (keep.Count > 0) result[id] = keep;
        }
        return result;
    }

    public static bool ValueEquals(object value, string original)
    {
        switch (value)
        {
            case bool b:
                return TryParseBool(original, out var ob) && b == ob;
            case int i:
                return double.TryParse(original, NumberStyles.Float, CultureInfo.InvariantCulture, out var oi) && Math.Abs(i - oi) < 1e-9;
            case double d:
                return double.TryParse(original, NumberStyles.Float, CultureInfo.InvariantCulture, out var od) && Math.Abs(d - od) < 1e-4;
            default:
                return false;
        }
    }

    public static string Format(object value) => value switch
    {
        bool b => b ? "True" : "False",
        double d => d.ToString("0.####", CultureInfo.InvariantCulture),
        float f => f.ToString("0.####", CultureInfo.InvariantCulture),
        IFormattable f => f.ToString(null, CultureInfo.InvariantCulture),
        _ => value?.ToString() ?? "",
    };

    /// <summary>The bundle stores bools as 0/1; configs use true/false.</summary>
    public static bool TryParseBool(string text, out bool value)
    {
        var t = (text ?? "").Trim();
        if (bool.TryParse(t, out value)) return true;
        if (t == "1") { value = true; return true; }
        if (t == "0") { value = false; return true; }
        return false;
    }

    public static bool TryParseNumber(string text, out double value)
        => double.TryParse((text ?? "").Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out value);

    // --------------------------------------------------------------- paint

    public ArmyPainterFaction PaintDefault(string key) => Catalog.PaintDefaults.FirstOrDefault(f => f.Key == key);

    public void SetPaint(string key, string pri, string sec)
    {
        Paint[key] = (Hex.Normalize(pri) ?? Paint[key].pri, Hex.Normalize(sec) ?? Paint[key].sec);
        Changed?.Invoke();
    }

    public bool IsPaintCustom(string key)
    {
        if (PaintScheme.GetValueOrDefault(key, "").Length > 0) return true;
        var d = PaintDefault(key);
        return d != null && Paint.TryGetValue(key, out var p) && (p.pri != d.Primary || p.sec != d.Secondary);
    }

    public int PaintCustomCount => Catalog.PaintDefaults.Count(f => IsPaintCustom(f.Key));

    private void ResetPaintToDefaults()
    {
        Paint.Clear();
        PaintScheme.Clear();
        foreach (var f in Catalog.PaintDefaults) { Paint[f.Key] = (f.Primary, f.Secondary); PaintScheme[f.Key] = ""; }
    }

    /// <summary>One bake job per faction with a custom scheme (colours or pack), from the current values.</summary>
    public List<Baker.Job> BakeJobs()
    {
        var jobs = new List<Baker.Job>();
        int max = int.TryParse(SettingValues.GetValueOrDefault("armypainter:Paint/MaxTextureSize"), out var m) ? Math.Clamp(m, 256, 4096) : 2048;
        foreach (var f in Catalog.PaintDefaults)
        {
            if (!IsPaintCustom(f.Key)) continue;
            var (pri, sec) = Paint[f.Key];
            jobs.Add(new Baker.Job
            {
                Faction = f.Key,
                Pack = Pack(PaintScheme.GetValueOrDefault(f.Key)),
                Primary = pri,
                Secondary = sec,
                HueWindow = SettingFloat("armypainter:Paint/HueWindow", 0.16f),
                SatThreshold = SettingFloat("armypainter:Paint/SatThreshold", 0.08f),
                Feather = SettingFloat("armypainter:Paint/BlendFeather", 0.08f),
                MaxSize = max,
            });
        }
        return jobs;
    }

    public void SetScheme(string key, string packId)
    {
        PaintScheme[key] = packId ?? "";
        Changed?.Invoke();
    }

    // -------------------------------------------------------------- packs

    /// <summary>User imports (config) first, then packs shipped with the mod (plugins).</summary>
    public IEnumerable<string> PackRoots => !HasGame ? Array.Empty<string>() : new[]
    {
        Path.Combine(GameDir, "BepInEx", "config", "warpstorm", "schemes"),
        Path.Combine(GameDir, "BepInEx", "plugins", "Warpstorm", "schemes"),
    };

    public string UserPackRoot => Path.Combine(GameDir, "BepInEx", "config", "warpstorm", "schemes");

    public List<string> RefreshPacks()
    {
        var errors = new List<string>();
        Packs = Warpstorm.Shared.SchemePack.Discover(PackRoots, errors.Add);
        return errors;
    }

    public Warpstorm.Shared.SchemePack Pack(string id)
        => string.IsNullOrEmpty(id) ? null : Packs.FirstOrDefault(p => string.Equals(p.Id, id, StringComparison.OrdinalIgnoreCase));

    /// <summary>Validates a pack .zip and installs it under config/warpstorm/schemes/&lt;id&gt;/. Returns the pack.</summary>
    public Warpstorm.Shared.SchemePack ImportPack(string zipPath)
    {
        using var zip = System.IO.Compression.ZipFile.OpenRead(zipPath);
        var entry = zip.Entries.FirstOrDefault(e => e.FullName.Replace('\\', '/').EndsWith("scheme.json", StringComparison.OrdinalIgnoreCase))
                    ?? throw new InvalidDataException(Loc.T("paint.import.noScheme"));
        string prefix = entry.FullName[..^"scheme.json".Length];
        Warpstorm.Shared.SchemePack parsed;
        using (var r = new StreamReader(entry.Open())) parsed = Warpstorm.Shared.SchemePack.Parse(r.ReadToEnd());
        var id = string.IsNullOrWhiteSpace(parsed.Id) ? Path.GetFileNameWithoutExtension(zipPath) : parsed.Id;
        if (id.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || id.Contains("..")) throw new InvalidDataException("bad pack id");

        var dest = Path.Combine(UserPackRoot, id);
        if (Directory.Exists(dest)) Directory.Delete(dest, true);
        Directory.CreateDirectory(dest);
        var root = Path.GetFullPath(dest) + Path.DirectorySeparatorChar;
        foreach (var e in zip.Entries)
        {
            var name = e.FullName.Replace('\\', '/');
            if (!name.StartsWith(prefix) || name.EndsWith("/")) continue;
            var rel = name[prefix.Length..];
            bool isBadge = parsed.Badge != null && rel == parsed.Badge.Image;
            if (!(rel == "scheme.json" || isBadge || (rel.StartsWith("portraits/") && rel.EndsWith(".png", StringComparison.OrdinalIgnoreCase)))) continue;
            var target = Path.GetFullPath(Path.Combine(dest, rel));
            if (!target.StartsWith(root)) continue; // zip-slip guard
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            e.ExtractToFile(target, true);
        }
        RefreshPacks();
        return Pack(id);
    }

    public float SettingFloat(string id, float fallback)
        => float.TryParse(SettingValues.GetValueOrDefault(id), NumberStyles.Float, CultureInfo.InvariantCulture, out var f) ? f : fallback;

    public void SetSetting(string id, string value)
    {
        SettingValues[id] = value;
        Changed?.Invoke();
    }

    // --------------------------------------------------------------- dirty

    private Dictionary<string, string> Snapshot()
    {
        var s = new Dictionary<string, string> { ["enabled"] = Enabled.ToString() };
        foreach (var (id, f) in UnitEdits) foreach (var (k, v) in f) s[$"unit:{id}:{k}"] = Format(v);
        foreach (var (id, f) in WeaponEdits) foreach (var (k, v) in f) s[$"weapon:{id}:{k}"] = Format(v);
        foreach (var (k, (p, q)) in Paint) s[$"paint:{k}"] = p + "/" + q + "/" + PaintScheme.GetValueOrDefault(k, "");
        foreach (var (k, v) in SettingValues) s[$"setting:{k}"] = v;
        return s;
    }

    /// <summary>Keys that differ from what is on disk.</summary>
    public HashSet<string> UnsavedKeys()
    {
        var now = Snapshot();
        var keys = new HashSet<string>();
        foreach (var (k, v) in now)
            if (!_baseline.TryGetValue(k, out var b) || b != v) keys.Add(k);
        foreach (var k in _baseline.Keys)
            if (!now.ContainsKey(k)) keys.Add(k);
        return keys;
    }

    public int UnsavedCount => UnsavedKeys().Count;
}

public static class Hex
{
    public static string Normalize(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return null;
        var hex = text.Trim().TrimStart('#').ToUpperInvariant();
        if (hex.Length == 8) hex = hex[2..]; // AARRGGBB from a colour picker
        if (hex.Length != 6 || !hex.All(Uri.IsHexDigit)) return null;
        return hex;
    }
}
