using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Warpstorm.Configurator;

/// <summary>
/// Headless verification of the non-UI pipeline (game detect → version → catalog
/// → bundle read → config write). Run: Warpstorm.Configurator --selftest
/// </summary>
public static class SelfTest
{
    public static int Run()
    {
        var game = GameLocator.Find();
        Console.WriteLine($"game folder : {(game.Length > 0 ? game : "(not found)")}");
        Console.WriteLine($"version     : {(game.Length > 0 ? VersionReader.Detect(game) : "n/a")}");

        var catalog = CatalogLoader.Load();
        var fields = catalog.Fields;
        Console.WriteLine($"fields      : unit={fields.Unit.Count} weapon={fields.Weapon.Count}");

        var asm = typeof(CatalogLoader).Assembly;
        var avRes = asm.GetManifestResourceNames()
            .FirstOrDefault(n => n.Contains("AvaloniaResources", StringComparison.OrdinalIgnoreCase));
        if (avRes != null)
        {
            using var st = asm.GetManifestResourceStream(avRes);
            Console.WriteLine($"image bundle: {avRes} ({(st == null ? 0 : st.Length / 1048576.0):F1} MB)");
        }

        var units = catalog.Units;
        var weapons = catalog.Weapons;
        Console.WriteLine($"names       : units with zh-TW={units.Count(u => u.Names.ContainsKey("zh-TW"))} locales={units.SelectMany(u => u.Names.Keys).Distinct().Count()}");
        Console.WriteLine($"used-by     : weapons with units={weapons.Count(w => w.UsedBy.Count > 0)}");
        Console.WriteLine($"catalog     : units={units.Count} weapons={weapons.Count}");
        if (units.Count > 0) Console.WriteLine($"  first unit   : {units[0].Name} ({units[0].Id}) {units[0].Subtitle}");
        if (weapons.Count > 0) Console.WriteLine($"  first weapon : {weapons[0].Name} ({weapons[0].Id}) {weapons[0].Subtitle}");

        if (game.Length == 0)
        {
            Console.WriteLine("No game folder found — set WARPSTORM_GAME_DIR to test bundle reading.");
            return 1;
        }

        var snap = BundleReader.Read(game, s => Console.WriteLine("  " + s));
        Console.WriteLine($"bundle      : units={snap.Units.Count} weapons={snap.Weapons.Count} source={snap.Source}");

        if (snap.Units.TryGetValue("7003", out var u))
            Console.WriteLine($"  unit 7003  : MaxHealth={V(u, "MaxHealth")} PointCost={V(u, "PointCost")} " +
                              $"AP={V(u, "MaxActionPoints")} MP={V(u, "MaxMovementPoints")} MeleeAcc={V(u, "MeleeAccuracy")}");
        if (snap.Weapons.TryGetValue("7010", out var w))
            Console.WriteLine($"  weapon 7010: Damage={V(w, "Damage")} Attacks={V(w, "Attacks")} AP={V(w, "ArmourPenetration")}");

        var outDir = Path.Combine(Environment.CurrentDirectory, ".copilot_workspace", "warpstorm-selftest");
        Directory.CreateDirectory(outDir);
        var outPath = Path.Combine(outDir, "config.json");

        var unitEdits = new Dictionary<string, Dictionary<string, object>>
        {
            ["7003"] = new() { ["MaxHealth"] = 60, ["PointCost"] = 1, ["MaxActionPoints"] = 2 },
        };
        var weaponEdits = new Dictionary<string, Dictionary<string, object>>
        {
            ["7010"] = new() { ["Attacks"] = 50, ["Damage"] = 8.0, ["ArmourPenetration"] = 2 },
        };

        ConfigStore.Save(outPath, VersionReader.Detect(game), true, unitEdits, weaponEdits);
        Console.WriteLine($"\nwrote sample config: {outPath}\n");
        Console.WriteLine(File.ReadAllText(outPath));

        // Army Painter cfg round-trip (written to the scratch dir, never the game).
        var apPath = Path.Combine(outDir, "armypainter.cfg");
        File.WriteAllText(apPath, "## sample\n[Faction.BloodAngels]\n\n## Primary armour colour (RRGGBB).\nPrimary = 900F0F\n");
        BepInExCfg.Update(apPath, new Dictionary<string, string>
        {
            [BepInExCfg.Key("Faction.BloodAngels", "Primary")] = "2F6B2F",
            [BepInExCfg.Key("Faction.BloodAngels", "Secondary")] = "E0C15A",
            [BepInExCfg.Key("Paint", "HueWindow")] = "0.2",
        });
        var back = BepInExCfg.Read(apPath);
        Console.WriteLine($"cfg test    : pri={back.GetValueOrDefault("Faction.BloodAngels/Primary")} sec={back.GetValueOrDefault("Faction.BloodAngels/Secondary")} hue={back.GetValueOrDefault("Paint/HueWindow")}");
        Console.WriteLine($"factions    : {catalog.Factions.Count} game, {catalog.PaintDefaults.Count} army painter");

        var imported = ConfigStore.Import(outPath);
        Console.WriteLine($"import test : enabled={imported.Enabled} fields={imported.Fields}");
        return 0;
    }

    private static string V(Dictionary<string, string> d, string key)
        => d.TryGetValue(key, out var v) ? v : "(missing)";
}
