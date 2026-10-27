using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text.Json;
using BlackLab.Foundation;

namespace Warpstorm;

/// <summary>One field we changed, with the value it had before (for revert).</summary>
internal sealed class AppliedEdit
{
    public object Target = null!;
    public PropertyInfo Property = null!;
    public object Original;
    public string Label = "";
}

/// <summary>
/// Applies the JSON config to the game's live data tables.
///
/// We do NOT patch methods or edit asset bundles: the game keeps every unit and
/// weapon as a <c>UnitData</c> / <c>WeaponData</c> object in
/// <c>RuntimeDataTables</c>, and each stat is a public get/set property. Writing
/// those properties changes the data for every mode, and keeping the old value
/// lets us revert cleanly when the user toggles Warpstorm off.
/// </summary>
internal static class TableApplier
{
    public static List<AppliedEdit> Apply(WarpstormConfig cfg)
    {
        var applied = new List<AppliedEdit>();
        var rdt = RuntimeDataTables.Instance;

        int units = Scan(rdt.UnitDataTable, cfg.Units, applied);
        int weapons = Scan(rdt.WeaponDataTable, cfg.Weapons, applied);

        Plugin.Log.LogInfo($"Warpstorm: scanned {units} units / {weapons} weapons; applied {applied.Count} field edit(s).");
        return applied;
    }

    private static int Scan<TKey, TData>(
        DataTableBase<TKey, TData> table,
        Dictionary<string, Dictionary<string, JsonElement>> edits,
        List<AppliedEdit> applied)
        where TData : class
    {
        if (table == null) return 0;
        var keys = table.keys;
        var values = table.values;
        if (keys == null || values == null) return 0;

        int count = Math.Min(keys.Count, values.Count);
        for (int i = 0; i < count; i++)
        {
            string id;
            try { id = Convert.ToInt32(keys[i]).ToString(); }
            catch { continue; }

            if (!edits.TryGetValue(id, out var fields)) continue;
            var data = values[i];
            foreach (var kv in fields)
                ApplyField(data, kv.Key, kv.Value, applied);
        }
        return count;
    }

    public static void Revert(List<AppliedEdit> applied)
    {
        for (int i = applied.Count - 1; i >= 0; i--)
        {
            var e = applied[i];
            try { e.Property.SetValue(e.Target, e.Original); }
            catch (Exception ex) { Plugin.Log.LogWarning($"Warpstorm revert failed for {e.Label}: {ex.Message}"); }
        }
        applied.Clear();
    }

    private static void ApplyField(object data, string name, JsonElement value, List<AppliedEdit> applied)
    {
        var prop = data.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.Instance);
        if (prop == null || !prop.CanRead || !prop.CanWrite)
        {
            Plugin.Log.LogWarning($"Warpstorm: no writable property '{name}' on {data.GetType().Name}");
            return;
        }

        object converted;
        try { converted = ConvertValue(value, prop.PropertyType); }
        catch (Exception ex)
        {
            Plugin.Log.LogWarning($"Warpstorm: bad value for {data.GetType().Name}.{name}: {ex.Message}");
            return;
        }
        if (converted == null) return;

        object original = null;
        try { original = prop.GetValue(data); } catch { /* some computed props */ }

        try
        {
            prop.SetValue(data, converted);
            applied.Add(new AppliedEdit
            {
                Target = data,
                Property = prop,
                Original = original,
                Label = $"{data.GetType().Name}.{name}",
            });
            Plugin.Log.LogInfo($"Warpstorm: {data.GetType().Name}.{name} = {converted} (was {original})");
        }
        catch (Exception ex)
        {
            Plugin.Log.LogWarning($"Warpstorm: failed to set {data.GetType().Name}.{name}: {ex.Message}");
        }
    }

    private static object ConvertValue(JsonElement value, Type type)
    {
        if (type == typeof(bool)) return value.GetBoolean();

        if (type.IsEnum)
            return Enum.ToObject(type, (int)Math.Round(value.GetDouble()));

        if (type == typeof(int)) return (int)Math.Round(value.GetDouble());
        if (type == typeof(uint)) return (uint)Math.Round(value.GetDouble());
        if (type == typeof(long)) return (long)Math.Round(value.GetDouble());
        if (type == typeof(float)) return (float)value.GetDouble();
        if (type == typeof(double)) return value.GetDouble();

        // Fall back to the value's natural CLR type.
        return value.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Number => value.GetDouble(),
            JsonValueKind.String => value.GetString(),
            _ => null,
        };
    }
}
