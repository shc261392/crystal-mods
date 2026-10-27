using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Warpstorm.Configurator;

/// <summary>
/// Talks to a running game through the status files the plugin writes:
///   BepInEx/config/warpstorm/status.json        (Warpstorm, every 5 s + after each apply)
///   BepInEx/config/warpstorm/paint-status.json  (Army Painter)
/// Each carries the mtime ("configStamp") of the config it has loaded, so after
/// a Save we can tell "the game picked it up" from "the game is not running".
/// </summary>
public static class GameLink
{
    public sealed class Status
    {
        public DateTime Time;
        public string ConfigStamp = "";
        public int Edits;
        public string Text = "";
        public string Faction = "";
        public int Units, Renderers, Portraits;
        public bool Active;
        public string Summary = "";
    }

    public static bool IsGameProcessRunning()
    {
        try
        {
            var name = Path.GetFileNameWithoutExtension(GameLocator.ExeName);
            return Process.GetProcessesByName(name).Length > 0;
        }
        catch
        {
            return false;
        }
    }

    public static Status Read(string path)
    {
        try
        {
            if (!File.Exists(path)) return null;
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var r = doc.RootElement;
            string S(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
            int I(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetInt32() : 0;
            DateTime.TryParse(S("time"), null, System.Globalization.DateTimeStyles.RoundtripKind, out var time);
            return new Status
            {
                Time = time.ToUniversalTime(),
                ConfigStamp = S("configStamp"),
                Edits = I("edits"),
                Text = S("status"),
                Faction = S("faction"),
                Units = I("units"),
                Renderers = I("renderersPainted"),
                Portraits = I("portraitsPainted"),
                Active = r.TryGetProperty("active", out var a) && a.ValueKind == JsonValueKind.True,
                Summary = S("summary"),
            };
        }
        catch
        {
            return null; // being written right now; try again next poll
        }
    }

    public static string Stamp(string file)
        => File.Exists(file) ? File.GetLastWriteTimeUtc(file).Ticks.ToString() : "";

    /// <summary>A heartbeat younger than this means the game is running.</summary>
    public static bool IsFresh(Status s) => s != null && (DateTime.UtcNow - s.Time).TotalSeconds < 12;

    public static string StatusPath(string gameDir) => Path.Combine(gameDir, "BepInEx", "config", "warpstorm", "status.json");
    public static string PaintStatusPath(string gameDir) => Path.Combine(gameDir, "BepInEx", "config", "warpstorm", "paint-status.json");

    public static bool Running(string gameDir)
        => IsGameProcessRunning() || IsFresh(Read(StatusPath(gameDir))) || IsFresh(Read(PaintStatusPath(gameDir)));

    public static bool AnyStatusFileExists(string gameDir)
        => new[] { StatusPath(gameDir), PaintStatusPath(gameDir) }.Any(File.Exists);
}
