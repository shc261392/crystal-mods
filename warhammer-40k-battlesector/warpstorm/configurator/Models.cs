using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Warpstorm.Configurator;

public sealed class EnumOption
{
    [JsonPropertyName("value")] public int Value { get; set; }
    [JsonPropertyName("label")] public string Label { get; set; } = "";
}

public sealed class FieldDef
{
    [JsonPropertyName("key")] public string Key { get; set; } = "";
    [JsonPropertyName("label")] public string Label { get; set; } = "";
    [JsonPropertyName("type")] public string Type { get; set; } = "int";
    [JsonPropertyName("group")] public string Group { get; set; } = "General";
    [JsonPropertyName("hint")] public string Hint { get; set; } = "";
    [JsonPropertyName("options")] public List<EnumOption> Options { get; set; } = new();

    public bool IsNumeric => Type == "int" || Type == "float";
}

public sealed class FieldsFile
{
    [JsonPropertyName("unit")] public List<FieldDef> Unit { get; set; } = new();
    [JsonPropertyName("weapon")] public List<FieldDef> Weapon { get; set; } = new();
}

public sealed class WeaponSlotOption
{
    public string WeaponId { get; init; } = "";
    public string Name { get; init; } = "";
    public int PointCost { get; init; }
}

/// <summary>A unit or weapon as shown in the list (from BattleSector Tools data).</summary>
public sealed class CatalogItem
{
    public string Id { get; init; } = "";
    public string Name { get; init; } = "";
    /// <summary>Localised names by locale code (from BattleSector Tools i18n.json).</summary>
    public Dictionary<string, string> Names { get; init; } = new();
    public string Subtitle { get; set; } = "";
    public string Faction { get; init; } = "";
    public int FactionId { get; init; } = -1;
    public string Role { get; init; } = "";
    public int RoleId { get; init; } = -1;
    public string RoleColor { get; init; } = "#5c5c5c";
    public int PointCost { get; init; }
    public int Members { get; init; } = 1;
    public string Image { get; init; } = "";
    public bool IsWeapon { get; init; }
    public bool IsMelee { get; init; }

    /// <summary>Catalog stats used for the header tiles when the bundle is not read yet.</summary>
    public Dictionary<string, string> CatalogStats { get; init; } = new();

    /// <summary>Units: weapon slots (each slot = choose-one options).</summary>
    public List<List<WeaponSlotOption>> WeaponSlots { get; init; } = new();

    /// <summary>Weapons: the units that can carry this weapon.</summary>
    public List<CatalogItem> UsedBy { get; } = new();

    public string DisplayName(string code) => code != "en" && Names.TryGetValue(code, out var n) && n.Length > 0 ? n : Name;

    /// <summary>The English name under a localised one (so guides/wikis still match).</summary>
    public string SecondaryName(string code) => DisplayName(code) != Name ? Name : "";

    public bool NameMatches(string query)
        => Name.Contains(query, System.StringComparison.OrdinalIgnoreCase) ||
           Names.Values.Any(n => n.Contains(query, System.StringComparison.OrdinalIgnoreCase));
}

public sealed class FactionOption
{
    public int Id { get; init; }
    public string Name { get; init; } = "";
    public Dictionary<string, string> Names { get; init; } = new();
    public string DisplayName(string code) => code != "en" && Names.TryGetValue(code, out var n) && n.Length > 0 ? n : Name;
    public override string ToString() => Name;
}

public sealed class ArmyPainterFaction
{
    [JsonPropertyName("key")] public string Key { get; set; } = "";
    [JsonPropertyName("name")] public string Name { get; set; } = "";
    [JsonPropertyName("factionId")] public int FactionId { get; set; } = -1;
    [JsonPropertyName("primary")] public string Primary { get; set; } = "FFFFFF";
    [JsonPropertyName("secondary")] public string Secondary { get; set; } = "FFFFFF";
}

public sealed class ArmyPainterFactionsFile
{
    [JsonPropertyName("factions")] public List<ArmyPainterFaction> Factions { get; set; } = new();
}
