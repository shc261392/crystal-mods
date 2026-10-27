using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Warpstorm.Configurator;

public sealed class ImportedConfig
{
    public bool Enabled = true;
    public Dictionary<string, Dictionary<string, object>> Units = new();
    public Dictionary<string, Dictionary<string, object>> Weapons = new();
    public int Fields => Units.Values.Sum(d => d.Count) + Weapons.Values.Sum(d => d.Count);
}

public static class ConfigStore
{
    public static string DefaultPath(string gameDir)
        => GameLocator.DefaultConfigPath(gameDir);

    public static string ArmyPainterConfigPath(string gameDir)
        => Path.Combine(gameDir, "BepInEx", "config", "com.crystalmods.armypainter.cfg");

    public static string PluginConfigPath(string gameDir)
        => Path.Combine(gameDir, "BepInEx", "config", "com.crystalmods.warpstorm.cfg");

    public static void Save(
        string path,
        string gameVersion,
        bool enabled,
        Dictionary<string, Dictionary<string, object>> units,
        Dictionary<string, Dictionary<string, object>> weapons)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

        var doc = new Dictionary<string, object>
        {
            ["schemaVersion"] = 1,
            ["gameVersion"] = gameVersion,
            ["enabled"] = enabled,
            ["units"] = units,
            ["weapons"] = weapons,
        };

        File.WriteAllText(path, JsonSerializer.Serialize(doc, new JsonSerializerOptions { WriteIndented = true }));
    }

    /// <summary>Reads a Warpstorm (or exported) config into editable dictionaries.</summary>
    public static ImportedConfig Import(string path)
    {
        var result = new ImportedConfig();
        using var doc = JsonDocument.Parse(File.ReadAllText(path), new JsonDocumentOptions
        {
            CommentHandling = JsonCommentHandling.Skip,
            AllowTrailingCommas = true,
        });

        var root = doc.RootElement;
        if (root.TryGetProperty("enabled", out var en) &&
            (en.ValueKind == JsonValueKind.True || en.ValueKind == JsonValueKind.False))
            result.Enabled = en.GetBoolean();

        if (root.TryGetProperty("units", out var units)) ReadSection(units, result.Units);
        if (root.TryGetProperty("weapons", out var weapons)) ReadSection(weapons, result.Weapons);
        return result;
    }

    private static void ReadSection(JsonElement section, Dictionary<string, Dictionary<string, object>> sink)
    {
        if (section.ValueKind != JsonValueKind.Object) return;
        foreach (var entry in section.EnumerateObject())
        {
            if (entry.Value.ValueKind != JsonValueKind.Object) continue;
            var fields = new Dictionary<string, object>();
            foreach (var field in entry.Value.EnumerateObject())
            {
                var value = ToClr(field.Value);
                if (value != null) fields[field.Name] = value;
            }
            if (fields.Count > 0) sink[entry.Name] = fields;
        }
    }

    private static object ToClr(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.True => true,
        JsonValueKind.False => false,
        JsonValueKind.Number => value.TryGetInt64(out var l) && l >= int.MinValue && l <= int.MaxValue
            ? (int)l
            : value.GetDouble(),
        JsonValueKind.String => value.GetString(),
        _ => null,
    };
}
