using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text.Json;
using BlackLab.Foundation;
using Units;

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
        // 1.8.0 moved the data into per-faction source tables merged by
        // CompositeDataTableBase. The raw `keys`/`values` fields are empty now;
        // the `Keys`/`Values` properties trigger the lazy merge and return the
        // full set in both 1.7.7 (plain table) and 1.8.0 (composite).
        var keys = table.Keys;
        var values = table.Values;
        if (keys == null || values == null) return 0;

        // DataTableBase exposes Count directly; the IL2CPP IReadOnlyList returned
        // by Keys/Values does not surface a usable Count property.
        int count = table.Count;
        for (int i = 0; i < count; i++)
        {
            string id;
            try { id = Convert.ToInt32(keys[i]).ToString(); }
            catch { continue; }

            if (!edits.TryGetValue(id, out var fields)) continue;
            var data = values[i];
            foreach (var kv in fields)
            {
                // The one list-valued edit: AddAbilities: [20024] (Self Repair).
                if (kv.Key == "AddAbilities" && data is UnitData unit)
                {
                    ApplyAbilities(unit, kv.Value, applied);
                    continue;
                }
                ApplyField(data, kv.Key, kv.Value, applied);
            }
        }
        return count;
    }

    /// <summary>
    /// Adds ability slots to a unit. Self Repair is a shared ability
    /// (<c>AbilityType.SelfRepair = 20024</c>) and can be granted to any unit.
    /// The list is cloned so the original reference stays intact for revert.
    /// </summary>
    private static void ApplyAbilities(UnitData unit, JsonElement value, List<AppliedEdit> applied)
    {
        if (value.ValueKind != JsonValueKind.Array)
        {
            Plugin.Log.LogWarning("Warpstorm: AddAbilities must be an array of ability ids, e.g. [20024]");
            return;
        }

        var original = unit.AbilityList;
        var list = new Il2CppSystem.Collections.Generic.List<UnitAbilitySlot>();
        if (original != null)
            foreach (var slot in original)
                list.Add(slot);

        int added = 0;
        foreach (var item in value.EnumerateArray())
        {
            if (!item.TryGetInt32(out int id))
            {
                Plugin.Log.LogWarning($"Warpstorm: AddAbilities entry is not an integer: {item}");
                continue;
            }
            if (!AbilityExists(id))
            {
                Plugin.Log.LogWarning($"Warpstorm: ability {id} is not in AbilityDataTable; skipping");
                continue;
            }

            bool present = false;
            for (int i = 0; i < list.Count; i++)
            {
                if ((int)list[i].Ability == id)
                {
                    present = true;
                    break;
                }
            }
            if (present) continue;

            list.Add(new UnitAbilitySlot { Ability = (AbilityType)id, StartsLocked = false });
            added++;
            Plugin.Log.LogInfo($"Warpstorm: UnitData.AbilityList += {id} ({(AbilityType)id})");
        }

        if (added == 0) return;

        unit.AbilityList = list;
        applied.Add(new AppliedEdit
        {
            Target = unit,
            Property = typeof(UnitData).GetProperty("AbilityList")!,
            Original = original,
            Label = $"UnitData.AbilityList (+{added})",
        });
    }

    private static bool AbilityExists(int id)
        => Enum.IsDefined(typeof(AbilityType), id);

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
