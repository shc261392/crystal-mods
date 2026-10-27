using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Warpstorm.Configurator;

/// <summary>
/// Minimal reader/writer for BepInEx <c>.cfg</c> files (INI-like). Updates keep
/// every comment, unknown key and section order, so the plugin's own file stays
/// intact; missing keys are appended to their section.
/// </summary>
public static class BepInExCfg
{
    public static Dictionary<string, string> Read(string path)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (!File.Exists(path)) return result;

        string section = "";
        foreach (var raw in File.ReadAllLines(path))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith("#")) continue;
            if (line.StartsWith("[") && line.EndsWith("]"))
            {
                section = line[1..^1].Trim();
                continue;
            }
            int eq = line.IndexOf('=');
            if (eq <= 0) continue;
            result[Key(section, line[..eq].Trim())] = line[(eq + 1)..].Trim();
        }
        return result;
    }

    public static string Key(string section, string name) => section + "/" + name;

    /// <summary>Writes <paramref name="values"/> (keys from <see cref="Key"/>) into the file.</summary>
    public static void Update(string path, IReadOnlyDictionary<string, string> values)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        var lines = File.Exists(path) ? File.ReadAllLines(path).ToList() : new List<string>();

        foreach (var group in values.GroupBy(kv => kv.Key[..kv.Key.IndexOf('/')]))
        {
            string section = group.Key;
            int start = lines.FindIndex(l => l.Trim().Equals($"[{section}]", StringComparison.OrdinalIgnoreCase));
            if (start < 0)
            {
                if (lines.Count > 0 && lines[^1].Trim().Length != 0) lines.Add("");
                lines.Add($"[{section}]");
                lines.Add("");
                start = lines.Count - 2;
            }

            foreach (var (fullKey, value) in group)
            {
                string name = fullKey[(fullKey.IndexOf('/') + 1)..];
                int end = SectionEnd(lines, start);
                bool found = false;
                for (int i = start + 1; i < end; i++)
                {
                    var t = lines[i].Trim();
                    if (t.StartsWith("#")) continue;
                    int eq = t.IndexOf('=');
                    if (eq <= 0 || !t[..eq].Trim().Equals(name, StringComparison.OrdinalIgnoreCase)) continue;
                    lines[i] = $"{name} = {value}";
                    found = true;
                    break;
                }
                if (!found)
                {
                    int insert = end;
                    while (insert > start + 1 && lines[insert - 1].Trim().Length == 0) insert--;
                    lines.Insert(insert, $"{name} = {value}");
                }
            }
        }

        File.WriteAllLines(path, lines);
    }

    private static int SectionEnd(List<string> lines, int start)
    {
        for (int i = start + 1; i < lines.Count; i++)
            if (lines[i].TrimStart().StartsWith("[")) return i;
        return lines.Count;
    }
}
