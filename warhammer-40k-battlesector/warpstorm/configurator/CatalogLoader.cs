using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Warpstorm.Configurator;

/// <summary>Everything the UI lists, "absorbed" from the BattleSector Tools data.</summary>
public sealed class Catalog
{
    public FieldsFile Fields = new();
    public List<CatalogItem> Units = new();
    public List<CatalogItem> Weapons = new();
    public List<FactionOption> Factions = new();
    public List<string> Roles = new();
    /// <summary>English role name -> localised names by locale.</summary>
    public Dictionary<string, Dictionary<string, string>> RoleNames = new();

    public string RoleName(string role, string code)
        => code != "en" && RoleNames.TryGetValue(role, out var n) && n.TryGetValue(code, out var v) && v.Length > 0 ? v : role;
    public List<ArmyPainterFaction> PaintDefaults = new();
    public Dictionary<string, CatalogItem> WeaponById = new();
}

public static class CatalogLoader
{
    private static readonly JsonDocumentOptions DocOptions = new()
    {
        CommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public static string DataDir => Path.Combine(AppContext.BaseDirectory, "data");

    // Catalog JSON key -> UnitData/WeaponData property, for the header tiles
    // shown before the game bundle has been read.
    private static readonly (string json, string field)[] UnitStatMap =
    {
        ("pointCost", "PointCost"), ("maxHealth", "MaxHealth"), ("evasion", "Evasion"),
        ("armor", "SingularArmor"), ("armorFront", "ArmorFront"), ("armorLeft", "ArmorLeft"),
        ("armorRight", "ArmorRight"), ("armorRear", "ArmorRear"), ("armorProfile", "ArmorProfile"),
        ("meleeAccuracy", "MeleeAccuracy"), ("rangedAccuracyModifier", "RangedAccuracyModifier"),
        ("maxActionPoints", "MaxActionPoints"), ("maxMovementPoints", "MaxMovementPoints"),
        ("momentumPerModelDeath", "MomentumPerModelDeath"), ("unitHeight", "UnitHeight"),
        ("activationRange", "ActivationRange"), ("awarenessRange", "AwarenessRange"),
    };

    private static readonly (string json, string field)[] WeaponStatMap =
    {
        ("damage", "Damage"), ("accuracy", "Accuracy"), ("numAttacks", "Attacks"),
        ("armorPiercing", "ArmourPenetration"), ("rangeMin", "MinimumRange"),
        ("rangeOptimal", "OptimalRange"), ("rangeMax", "MaximumRange"),
        ("accuracyFalloff", "AccuracyFalloff"),
    };

    public static Catalog Load()
    {
        var catalog = new Catalog
        {
            Fields = LoadFields(),
            PaintDefaults = LoadArmyPainterFactions(),
        };

        var names = LoadNames();
        catalog.Factions = LoadFactions(names.factions);
        catalog.Weapons = LoadWeapons(names.weapons);
        catalog.WeaponById = catalog.Weapons.GroupBy(w => w.Id).ToDictionary(g => g.Key, g => g.First());
        catalog.Units = LoadUnits(names.units, catalog.WeaponById);
        catalog.Roles = catalog.Units.Select(u => u.Role).Where(r => r.Length > 0).Distinct().OrderBy(r => r).ToList();
        foreach (var u in catalog.Units)
            if (u.RoleId >= 0 && !catalog.RoleNames.ContainsKey(u.Role))
                catalog.RoleNames[u.Role] = Pick(names.roles, u.RoleId.ToString());
        return catalog;
    }

    public static FieldsFile LoadFields()
    {
        var text = ReadTextAsset("fields.json");
        if (text.Length == 0) return new FieldsFile();
        return JsonSerializer.Deserialize<FieldsFile>(text, JsonOptions) ?? new FieldsFile();
    }

    private static Dictionary<string, string> Pick(Dictionary<string, Dictionary<string, string>> byLocale, string id)
    {
        var result = new Dictionary<string, string>();
        foreach (var (code, table) in byLocale)
            if (table.TryGetValue(id, out var v) && v.Length > 0) result[code] = v;
        return result;
    }

    private static List<CatalogItem> LoadUnits(Dictionary<string, Dictionary<string, string>> names, Dictionary<string, CatalogItem> weapons)
    {
        var items = new List<CatalogItem>();
        foreach (var e in ReadArray("units.json"))
        {
            var id = IntText(e, "id").ToString();
            var faction = Str(e, "factionName");
            var role = Str(e, "roleName");

            var slots = new List<List<WeaponSlotOption>>();
            if (e.TryGetProperty("weaponSlots", out var ws) && ws.ValueKind == JsonValueKind.Array)
            {
                foreach (var slot in ws.EnumerateArray())
                {
                    var options = new List<WeaponSlotOption>();
                    if (slot.TryGetProperty("options", out var opts) && opts.ValueKind == JsonValueKind.Array)
                        foreach (var o in opts.EnumerateArray())
                            options.Add(new WeaponSlotOption
                            {
                                WeaponId = IntText(o, "weaponId").ToString(),
                                Name = Str(o, "name"),
                                PointCost = IntText(o, "pointCost"),
                            });
                    if (options.Count > 0) slots.Add(options);
                }
            }

            var unit = new CatalogItem
            {
                Id = id,
                Name = Str(e, "name"),
                Names = Pick(names, id),
                Subtitle = $"{faction} · {role}",
                Faction = faction,
                FactionId = IntText(e, "faction", -1),
                Role = role,
                RoleId = IntText(e, "role", -1),
                RoleColor = Str(e, "roleColor") is { Length: > 0 } c ? c : "#5c5c5c",
                PointCost = IntText(e, "pointCost"),
                Members = Math.Max(1, IntText(e, "members", 1)),
                Image = Str(e, "portrait"),
                CatalogStats = Stats(e, UnitStatMap),
                WeaponSlots = slots,
            };
            items.Add(unit);

            foreach (var opt in slots.SelectMany(s => s))
                if (weapons.TryGetValue(opt.WeaponId, out var w) && !w.UsedBy.Contains(unit))
                    w.UsedBy.Add(unit);
        }
        return items.OrderBy(i => i.Name).ToList();
    }

    private static List<CatalogItem> LoadWeapons(Dictionary<string, Dictionary<string, string>> names)
    {
        var items = new List<CatalogItem>();
        foreach (var e in ReadArray("weapons.json"))
        {
            var id = IntText(e, "id").ToString();
            bool melee = Bool(e, "isMelee");
            var type = Str(e, "weaponType");
            if (type.Length == 0) type = melee ? "Melee" : "Ranged";
            items.Add(new CatalogItem
            {
                Id = id,
                Name = Str(e, "name"),
                Names = Pick(names, id),
                Subtitle = type,
                Image = Str(e, "icon"),
                IsWeapon = true,
                IsMelee = melee,
                CatalogStats = Stats(e, WeaponStatMap),
            });
        }
        return items.OrderBy(i => i.Name).ToList();
    }

    private static List<FactionOption> LoadFactions(Dictionary<string, Dictionary<string, string>> names)
    {
        var items = new List<FactionOption>();
        foreach (var e in ReadArray("factions.json"))
        {
            int id = IntText(e, "id", -1);
            items.Add(new FactionOption { Id = id, Name = Str(e, "name"), Names = Pick(names, id.ToString()) });
        }
        return items.Where(f => f.Id >= 0 && f.Name.Length > 0).OrderBy(f => f.Name).ToList();
    }

    public static List<ArmyPainterFaction> LoadArmyPainterFactions()
    {
        var text = ReadTextAsset("armypainter-factions.json");
        if (text.Length == 0) return new List<ArmyPainterFaction>();
        var doc = JsonSerializer.Deserialize<ArmyPainterFactionsFile>(text, JsonOptions);
        return doc?.Factions ?? new List<ArmyPainterFaction>();
    }

    private sealed class NameTables
    {
        public Dictionary<string, Dictionary<string, string>> units = new(), weapons = new(), factions = new(), roles = new();
    }

    /// <summary>All localised names: section -> locale -> id -> name.</summary>
    private static NameTables LoadNames()
    {
        var t = new NameTables();
        var text = ReadTextAsset("i18n.json");
        if (text.Length == 0) return t;
        try
        {
            using var doc = JsonDocument.Parse(text, DocOptions);
            Dictionary<string, Dictionary<string, string>> Section(string name)
            {
                var result = new Dictionary<string, Dictionary<string, string>>();
                if (!doc.RootElement.TryGetProperty(name, out var s)) return result;
                foreach (var locale in s.EnumerateObject())
                {
                    var table = new Dictionary<string, string>();
                    foreach (var p in locale.Value.EnumerateObject())
                        if (p.Value.ValueKind == JsonValueKind.String) table[p.Name] = p.Value.GetString() ?? "";
                    result[locale.Name] = table;
                }
                return result;
            }
            t.units = Section("unitNames");
            t.weapons = Section("weaponNames");
            t.factions = Section("factionNames");
            t.roles = Section("roleNames");
        }
        catch
        {
            // names fall back to English
        }
        return t;
    }

    private static Dictionary<string, string> Stats(JsonElement e, (string json, string field)[] map)
    {
        var result = new Dictionary<string, string>();
        foreach (var (json, field) in map)
        {
            if (!e.TryGetProperty(json, out var v)) continue;
            switch (v.ValueKind)
            {
                case JsonValueKind.Number: result[field] = v.GetRawText(); break;
                case JsonValueKind.True: result[field] = "True"; break;
                case JsonValueKind.False: result[field] = "False"; break;
            }
        }
        return result;
    }

    private static IEnumerable<JsonElement> ReadArray(string file)
    {
        var text = ReadTextAsset(file);
        if (text.Length == 0) return Array.Empty<JsonElement>();
        var doc = JsonDocument.Parse(text, DocOptions);
        return doc.RootElement.EnumerateArray().ToList(); // materialize before doc disposal
    }

    /// <summary>Reads a data file from disk if present, otherwise from the embedded resources.</summary>
    private static string ReadTextAsset(string file)
    {
        var disk = Path.Combine(DataDir, file);
        if (File.Exists(disk)) return File.ReadAllText(disk);

        var asm = typeof(CatalogLoader).Assembly;
        var names = asm.GetManifestResourceNames();
        var desired = "data/" + file;
        var name = names.FirstOrDefault(n => string.Equals(n, desired, StringComparison.OrdinalIgnoreCase))
                   ?? names.FirstOrDefault(n => n.EndsWith("/" + file, StringComparison.OrdinalIgnoreCase));
        if (name == null) return "";

        using var stream = asm.GetManifestResourceStream(name);
        if (stream == null) return "";
        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    private static string Str(JsonElement e, string key)
        => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? (v.GetString() ?? "") : "";

    private static int IntText(JsonElement e, string key, int fallback = 0)
        => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var i) ? i : fallback;

    private static bool Bool(JsonElement e, string key)
        => e.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.True;
}
