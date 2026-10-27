using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using AssetsTools.NET;
using AssetsTools.NET.Extra;

namespace Warpstorm.Configurator;

public sealed class BundleSnapshot
{
    public Dictionary<string, Dictionary<string, string>> Units { get; } = new();
    public Dictionary<string, Dictionary<string, string>> Weapons { get; } = new();
    public string Source { get; set; } = "";
}

/// <summary>
/// Reads the game's startup bundle with AssetsTools.NET and returns every unit /
/// weapon entry's scalar fields as strings. This is the read-only "Original"
/// column, and it is what "verifying game data" means.
///
/// The MonoBehaviour type trees are embedded in the bundle (verified: both
/// <c>UnitDataTable</c> and <c>WeaponDataTable</c> deserialize with full field
/// names), so no class database is needed.
/// </summary>
public static class BundleReader
{
    public static BundleSnapshot Read(string gameDir, Action<string> progress)
    {
        var snap = new BundleSnapshot();
        var live = Path.Combine(GameLocator.DataDir(gameDir), "StreamingAssets", "startup_assets_all.bundle");
        var backup = live + ".vortex_backup";
        var path = File.Exists(live) ? live : backup;

        if (!File.Exists(path))
            throw new FileNotFoundException("startup_assets_all.bundle not found", path);

        snap.Source = Path.GetFileName(path);
        progress($"Opening {snap.Source}…");

        var am = new AssetsManager();
        var bun = am.LoadBundleFile(path);

        for (int i = 0; i < bun.file.BlockAndDirInfo.DirectoryInfos.Count; i++)
        {
            AssetsFileInstance af;
            try { af = am.LoadAssetsFileFromBundle(bun, i); }
            catch { continue; } // non-serialized entries

            ReadTable(af, am, "UnitDataTable", snap.Units, progress);
            ReadTable(af, am, "WeaponDataTable", snap.Weapons, progress);
        }

        return snap;
    }

    private static void ReadTable(
        AssetsFileInstance af,
        AssetsManager am,
        string tableName,
        Dictionary<string, Dictionary<string, string>> sink,
        Action<string> progress)
    {
        foreach (var info in af.file.AssetInfos)
        {
            if (info.TypeId != (int)AssetClassID.MonoBehaviour) continue;

            AssetTypeValueField bf;
            try { bf = am.GetBaseField(af, info); }
            catch { continue; }

            string name;
            try { name = bf["m_Name"]?.AsString ?? ""; }
            catch { continue; }
            if (name != tableName) continue;

            var keys = bf["keys"];
            var values = bf["values"];
            if (keys == null || values == null) return;

            UnwrapArray(ref keys);
            UnwrapArray(ref values);

            int count = Math.Min(keys.Children.Count, values.Children.Count);
            progress($"Reading {tableName} ({count} entries)…");

            for (int i = 0; i < count; i++)
            {
                string id;
                try { id = keys.Children[i].AsObject?.ToString() ?? ""; }
                catch { continue; }
                if (id.Length == 0) continue;

                var fields = new Dictionary<string, string>();
                var elem = values.Children[i];
                foreach (var child in elem.Children)
                {
                    if (child.Children.Count != 0) continue; // arrays / nested structs
                    try
                    {
                        var v = child.AsObject;
                        if (v != null) fields[child.FieldName] = Convert.ToString(v, CultureInfo.InvariantCulture) ?? "";
                    }
                    catch { /* field absent on this type */ }
                }
                sink[id] = fields;
            }
            return;
        }
    }

    private static void UnwrapArray(ref AssetTypeValueField field)
    {
        while (field.Children.Count == 1 && field.Children[0].TypeName == "Array")
            field = field.Children[0];
    }
}
