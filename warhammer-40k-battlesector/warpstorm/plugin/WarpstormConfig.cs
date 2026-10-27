using System.Collections.Generic;
using System.Text.Json;

namespace Warpstorm;

/// <summary>
/// The JSON document shared by the Warpstorm configurator and plugin.
///
/// <code>
/// {
///   "schemaVersion": 1,
///   "gameVersion": "1.7.7",
///   "enabled": true,
///   "units":   { "7003": { "MaxHealth": 60, "PointCost": 1 } },
///   "weapons": { "7010": { "Attacks": 50, "Damage": 8.0, "ArmourPenetration": 2 } }
/// }
/// </code>
///
/// Keys are the in-game ids (stringified enums). Field names are the exact
/// <c>Units.UnitData</c> / <c>Units.WeaponData</c> property names.
/// </summary>
public sealed class WarpstormConfig
{
    public int SchemaVersion { get; set; } = 1;
    public string GameVersion { get; set; } = "";
    public bool Enabled { get; set; } = true;

    public Dictionary<string, Dictionary<string, JsonElement>> Units { get; set; } = new();
    public Dictionary<string, Dictionary<string, JsonElement>> Weapons { get; set; } = new();

    public bool IsEmpty => Units.Count == 0 && Weapons.Count == 0;
}
