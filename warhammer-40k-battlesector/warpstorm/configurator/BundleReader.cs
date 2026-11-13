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
        progress($"bundle directory entries: {bun.file.BlockAndDirInfo.DirectoryInfos.Count}");

        for (int i = 0; i < bun.file.BlockAndDirInfo.DirectoryInfos.Count; i++)
        {
            AssetsFileInstance af;
            try { af = am.LoadAssetsFileFromBundle(bun, i); }
            catch (Exception ex) { progress($"  entry {i}: load failed ({ex.GetType().Name})"); continue; } // non-serialized entries
            // 1.8.0 bundles can carry resource-only directory entries whose
            // AssetsFile has no metadata; skip them instead of NRE-ing.
            if (af?.file?.Metadata == null) continue;

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
        // Locate the named table first (1.7.7: the real data table; 1.8.0: the
        // composite that only holds `sources`).
        AssetTypeValueField tableBf = null;
        foreach (var info in af.file.AssetInfos)
        {
            if (info.TypeId != (int)AssetClassID.MonoBehaviour) continue;

            AssetTypeValueField bf;
            try { bf = am.GetBaseField(af, info); }
            catch { continue; }

            string name;
            try { name = bf["m_Name"]?.AsString ?? ""; }
            catch { continue; }
            if (name == tableName) { tableBf = bf; break; }
        }
        if (tableBf == null)
        {
            progress($"  {tableName}: not found in this entry");
            return;
        }
        progress($"  {tableName}: found");

        // 1.8.0 moved every unit/weapon into per-faction tables referenced by the
        // composite's `sources` PPtr array. Follow those references (same file
        // only) and read each faction table's inline keys/values.
        var sources = tableBf["sources"];
        if (sources != null) UnwrapArray(ref sources);
        int read = 0;
        if (sources != null && sources.Children.Count > 0)
        {
            var byPathId = new Dictionary<long, AssetFileInfo>();
            foreach (var info in af.file.AssetInfos)
                byPathId[info.PathId] = info;

            foreach (var src in sources.Children)
            {
                long pid;
                try { pid = src["m_PathID"].AsLong; }
                catch { continue; }
                int fid;
                try { fid = src["m_FileID"].AsInt; }
                catch { fid = 0; }
                if (fid != 0 || !byPathId.TryGetValue(pid, out var srcInfo)) continue;

                AssetTypeValueField srcBf;
                try { srcBf = am.GetBaseField(af, srcInfo); }
                catch { continue; }
                read += ReadEntries(srcBf, sink);
            }
            if (read > 0) progress($"Reading {tableName} ({read} entries from {sources.Children.Count} sources)…");
        }

        // 1.7.7 layout (or any table that still stores its data inline).
        if (read == 0)
        {
            int inline = ReadEntries(tableBf, sink);
            if (inline > 0) progress($"Reading {tableName} ({inline} entries)…");
        }
    }

    private static int ReadEntries(
        AssetTypeValueField bf,
        Dictionary<string, Dictionary<string, string>> sink)
    {
        var keys = bf["keys"];
        var values = bf["values"];
        if (keys == null || values == null) return 0;

        UnwrapArray(ref keys);
        UnwrapArray(ref values);

        int count = Math.Min(keys.Children.Count, values.Children.Count);
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
        return count;
    }

    private static void UnwrapArray(ref AssetTypeValueField field)
    {
        while (field.Children.Count == 1 && field.Children[0].TypeName == "Array")
            field = field.Children[0];
    }
}
