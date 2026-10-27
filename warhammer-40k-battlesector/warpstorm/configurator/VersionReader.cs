using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace Warpstorm.Configurator;

/// <summary>
/// Reads the game version out of Unity's <c>globalgamemanagers</c>.
///
/// That file stores <c>PlayerSettings</c> as plain serialized strings; the
/// product name is immediately followed by the bundle version (verified on
/// 1.7.7). We extract printable runs and pick the version-looking string that
/// follows the product name, with a sane fallback.
/// </summary>
public static class VersionReader
{
    private static readonly Regex VersionLike = new(@"^\d+\.\d+(\.\d+)?$", RegexOptions.Compiled);

    public static string Detect(string gameDir)
    {
        try
        {
            var path = Path.Combine(GameLocator.DataDir(gameDir), "globalgamemanagers");
            if (!File.Exists(path)) return "unknown";

            var strings = ExtractStrings(File.ReadAllBytes(path));
            int at = strings.FindIndex(s => s == "Warhammer 40,000 Battlesector");
            if (at >= 0)
            {
                for (int i = at + 1; i < Math.Min(at + 8, strings.Count); i++)
                    if (VersionLike.IsMatch(strings[i])) return strings[i];
            }

            foreach (var s in strings)
                if (VersionLike.IsMatch(s)) return s; // last-resort fallback
        }
        catch { /* version is informational only */ }
        return "unknown";
    }

    private static List<string> ExtractStrings(byte[] bytes)
    {
        var result = new List<string>();
        var sb = new StringBuilder();
        foreach (var b in bytes)
        {
            if (b >= 0x20 && b < 0x7f)
            {
                sb.Append((char)b);
            }
            else
            {
                if (sb.Length >= 4) result.Add(sb.ToString());
                sb.Clear();
            }
        }
        if (sb.Length >= 4) result.Add(sb.ToString());
        return result;
    }
}
