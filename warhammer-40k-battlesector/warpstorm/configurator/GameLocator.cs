using System;
using System.Collections.Generic;
using System.IO;

namespace Warpstorm.Configurator;

public static class GameLocator
{
    public const string ExeName = "Warhammer 40K Battlesector.exe";

    public static string Find()
    {
        // 1) If the configurator was shipped inside the game (BepInEx/plugins/
        //    Warpstorm), walk up from the executable to the game root.
        var dir = AppContext.BaseDirectory
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        for (int i = 0; i < 8 && !string.IsNullOrEmpty(dir); i++)
        {
            if (IsGameDir(dir)) return dir;
            var parent = Path.GetDirectoryName(dir);
            if (string.IsNullOrEmpty(parent) || parent == dir) break;
            dir = parent;
        }

        // 2) Environment overrides.
        foreach (var env in new[] { "WARPSTORM_GAME_DIR", "BS_GAME_DIR" })
        {
            var v = Environment.GetEnvironmentVariable(env);
            if (IsGameDir(v)) return v!;
        }

        var candidates = new List<string>
        {
            @"C:\Program Files (x86)\Steam\steamapps\common\Warhammer 40000 Battlesector",
            @"C:\Program Files\Steam\steamapps\common\Warhammer 40000 Battlesector",
            @"D:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector",
            @"E:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector",
            @"F:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector",
            @"G:\SteamLibrary\steamapps\common\Warhammer 40000 Battlesector",
            "/mnt/c/Program Files (x86)/Steam/steamapps/common/Warhammer 40000 Battlesector",
            "/mnt/d/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector",
            "/mnt/e/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector",
            "/mnt/g/SteamLibrary/steamapps/common/Warhammer 40000 Battlesector",
        };

        try
        {
            foreach (var drive in DriveInfo.GetDrives())
            {
                foreach (var lib in new[] { "SteamLibrary", "Steam", "Games", "Games/Steam" })
                    candidates.Add(Path.Combine(drive.Name, lib, "steamapps", "common", "Warhammer 40000 Battlesector"));
            }
        }
        catch { /* drives can throw on odd mounts */ }

        foreach (var c in candidates)
            if (IsGameDir(c)) return c;

        return "";
    }

    public static bool IsGameDir(string path)
        => !string.IsNullOrWhiteSpace(path) && File.Exists(Path.Combine(path!, ExeName));

    public static string DataDir(string gameDir)
        => Path.Combine(gameDir, "Warhammer 40K Battlesector_Data");

    public static string DefaultConfigPath(string gameDir)
        => Path.Combine(gameDir, "BepInEx", "config", "warpstorm", "config.json");
}
