using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;

namespace Warpstorm;

/// <summary>
/// Warpstorm — runtime unit/weapon stat editor for Warhammer 40,000: Battlesector.
///
/// The configurator EXE writes <c>BepInEx/config/warpstorm/config.json</c>; this
/// plugin applies it to the live <c>RuntimeDataTables</c> when the game loads, in
/// every mode, and can be toggled on/off or reloaded without restarting.
/// </summary>
[BepInPlugin(Guid, "Warpstorm", Version)]
public class Plugin : BasePlugin
{
    public const string Guid = "com.crystalmods.warpstorm";
    public const string Version = "1.1.0";

    internal static new ManualLogSource Log = null!;
    internal static ConfigFile Cfg = null!;
    internal static ConfigEntry<bool> Enabled = null!;
    internal static ConfigEntry<int> ToggleKey = null!;
    internal static ConfigEntry<int> ReloadKey = null!;
    internal static ConfigEntry<bool> ShowStatus = null!;

    internal static string ConfigDir => Path.Combine(Paths.ConfigPath, "warpstorm");
    internal static string ConfigFile => Path.Combine(ConfigDir, "config.json");

    /// <summary>The configurator ships next to this DLL (BepInEx/plugins/Warpstorm/).</summary>
    internal static string ConfiguratorExe =>
        Path.Combine(Path.GetDirectoryName(typeof(Plugin).Assembly.Location) ?? Paths.PluginPath,
                     "Warpstorm.Configurator.exe");

    /// <summary>Starts the configurator; returns a status line for the overlay.</summary>
    internal static string LaunchConfigurator()
    {
        var exe = ConfiguratorExe;
        if (!File.Exists(exe))
        {
            Log.LogWarning($"Warpstorm Configurator not found at {exe} (reinstall the mod, or check your antivirus quarantine).");
            return "configurator not found";
        }
        try
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = exe,
                WorkingDirectory = Path.GetDirectoryName(exe),
                UseShellExecute = true,
            });
            Log.LogInfo("Warpstorm Configurator launched — Alt+Tab to it; Save there and the game reloads automatically.");
            return "configurator opened (Alt+Tab)";
        }
        catch (Exception ex)
        {
            Log.LogWarning($"Warpstorm could not start {exe}: {ex.Message}");
            return "could not open configurator";
        }
    }

    public override void Load()
    {
        Log = base.Log;
        Cfg = Config;
        Enabled = Config.Bind("General", "Enabled", true, "Master switch (also toggled live by ToggleKey).");
        ToggleKey = Config.Bind("General", "ToggleKey", 291, "KeyCode int to toggle Warpstorm on/off (291 = F10).");
        ReloadKey = Config.Bind("General", "ReloadKey", 290, "KeyCode int to reload config.json and re-apply (290 = F9).");
        ShowStatus = Config.Bind("General", "ShowStatus", true, "Draw the on-screen Warpstorm box.");

        Directory.CreateDirectory(ConfigDir);
        if (!File.Exists(ConfigFile))
            File.WriteAllText(ConfigFile, DefaultConfigJson);

        Log.LogInfo($"Warpstorm {Version} loaded. Config: {ConfigFile}");
        ClassInjector.RegisterTypeInIl2Cpp<WarpstormBehaviour>();
        AddComponent<WarpstormBehaviour>();
    }

    private const string DefaultConfigJson = """
{
  "schemaVersion": 1,
  "enabled": true,
  "units": {},
  "weapons": {}
}
""";
}

/// <summary>Waits for the game's data tables, applies the config, and watches for changes.</summary>
public class WarpstormBehaviour : MonoBehaviour
{
    public WarpstormBehaviour(IntPtr ptr) : base(ptr) { }

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    private WarpstormConfig _config;
    private List<AppliedEdit> _applied = new();
    private DateTime _lastWriteUtc = DateTime.MinValue;
    private object _lastTableRoot;
    private float _poll;
    private bool _pending = true;          // apply as soon as tables are ready
    private bool _legacyInput = true;
    private string _status = "starting";
    private int _editCount;

    private bool Active => Plugin.Enabled.Value && _config is { Enabled: true };

    private void Awake() => LoadConfig();

    private void Update()
    {
        try
        {
            if (_legacyInput)
            {
                if (Input.GetKeyDown((KeyCode)Plugin.ToggleKey.Value))
                {
                    Plugin.Enabled.Value = !Plugin.Enabled.Value;
                    ApplyNow("hotkey");
                }
                else if (Input.GetKeyDown((KeyCode)Plugin.ReloadKey.Value))
                {
                    LoadConfig();
                    ApplyNow("hotkey-reload");
                }
            }

            _poll += Time.deltaTime;
            if (_poll >= 1f)
            {
                _poll = 0f;
                Poll();
            }

            if (_pending && TablesReady())
                ApplyNow("tables-ready");
        }
        catch (Exception ex)
        {
            _legacyInput = false;
            Plugin.Log.LogDebug($"Warpstorm Update: {ex.Message}");
        }
    }

    private DateTime _settingsWriteUtc = DateTime.MinValue;
    private float _heartbeat;

    private void Poll()
    {
        // The configurator also edits com.crystalmods.warpstorm.cfg (hotkeys,
        // Enabled, ShowStatus); BepInEx only reads it at startup, so reload it.
        try
        {
            var path = Plugin.Cfg.ConfigFilePath;
            if (File.Exists(path))
            {
                var write = File.GetLastWriteTimeUtc(path);
                if (_settingsWriteUtc == DateTime.MinValue) _settingsWriteUtc = write;
                else if (write != _settingsWriteUtc)
                {
                    _settingsWriteUtc = write;
                    bool wasEnabled = Plugin.Enabled.Value;
                    Plugin.Cfg.Reload();
                    Plugin.Log.LogInfo("Warpstorm settings reloaded from disk.");
                    if (wasEnabled != Plugin.Enabled.Value) ApplyNow("settings-changed");
                }
            }
        }
        catch (Exception ex)
        {
            Plugin.Log.LogWarning($"Warpstorm settings reload failed: {ex.Message}");
        }

        _heartbeat += 1f;
        if (_heartbeat >= 5f) { _heartbeat = 0f; WriteStatus(); }

        try
        {
            if (File.Exists(Plugin.ConfigFile))
            {
                var write = File.GetLastWriteTimeUtc(Plugin.ConfigFile);
                if (write != _lastWriteUtc)
                {
                    _lastWriteUtc = write;
                    LoadConfig();
                    ApplyNow("config-changed");
                }
            }
        }
        catch (Exception ex)
        {
            Plugin.Log.LogWarning($"Warpstorm config poll failed: {ex.Message}");
        }

        // Re-apply if the game recreated its data tables (new battle / mode).
        if (TablesReady())
        {
            var root = RuntimeDataTables.Instance;
            if (!ReferenceEquals(root, _lastTableRoot))
            {
                _lastTableRoot = root;
                if (Active) ApplyNow("tables-changed");
            }
        }
    }

    private void LoadConfig()
    {
        try
        {
            if (!File.Exists(Plugin.ConfigFile))
            {
                _status = "no config file";
                return;
            }
            var text = File.ReadAllText(Plugin.ConfigFile);
            _config = JsonSerializer.Deserialize<WarpstormConfig>(text, JsonOptions);
            _lastWriteUtc = File.GetLastWriteTimeUtc(Plugin.ConfigFile);
            _status = _config == null ? "config parse failed" : "config loaded";
            Plugin.Log.LogInfo(
                $"Warpstorm config: {(_config == null ? 0 : _config.Units.Count)} units, " +
                $"{(_config == null ? 0 : _config.Weapons.Count)} weapons.");
            if (_config == null || _config.IsEmpty)
                Plugin.Log.LogWarning(
                    "Warpstorm config has 0 edits — nothing to apply. Open the Warpstorm Configurator, " +
                    "edit some values and Save, or edit " + Plugin.ConfigFile + " by hand.");
        }
        catch (Exception ex)
        {
            _status = "config error";
            Plugin.Log.LogError($"Warpstorm could not read {Plugin.ConfigFile}: {ex}");
        }
    }

    private void ApplyNow(string reason)
    {
        try { ApplyNowCore(reason); }
        finally { WriteStatus(); }
    }

    /// <summary>
    /// BepInEx/config/warpstorm/status.json — lets the configurator confirm
    /// that a running game picked up a save (configStamp = config.json mtime).
    /// </summary>
    private void WriteStatus()
    {
        try
        {
            string stamp = File.Exists(Plugin.ConfigFile) ? File.GetLastWriteTimeUtc(Plugin.ConfigFile).Ticks.ToString() : "";
            string settings = File.Exists(Plugin.Cfg.ConfigFilePath) ? File.GetLastWriteTimeUtc(Plugin.Cfg.ConfigFilePath).Ticks.ToString() : "";
            string json = "{\n" +
                $"  \"time\": \"{DateTime.UtcNow:O}\",\n" +
                $"  \"version\": \"{Plugin.Version}\",\n" +
                $"  \"configStamp\": \"{stamp}\",\n" +
                $"  \"settingsStamp\": \"{settings}\",\n" +
                $"  \"active\": {(Active ? "true" : "false")},\n" +
                $"  \"edits\": {_editCount},\n" +
                $"  \"status\": \"{_status.Replace("\"", "'")}\"\n" +
                "}\n";
            File.WriteAllText(Path.Combine(Plugin.ConfigDir, "status.json"), json);
        }
        catch
        {
            // best effort
        }
    }

    private void ApplyNowCore(string reason)
    {
        TableApplier.Revert(_applied);
        _applied = new List<AppliedEdit>();
        _pending = false;

        if (!Active)
        {
            _editCount = 0;
            _status = "OFF";
            Plugin.Log.LogInfo($"Warpstorm OFF ({reason}).");
            return;
        }

        if (!TablesReady())
        {
            _pending = true; // try again once the tables exist
            _status = "waiting for game data";
            Plugin.Log.LogInfo("Warpstorm: data tables not ready yet — will apply when the game loads them.");
            return;
        }

        if (_config == null || _config.IsEmpty)
        {
            _editCount = 0;
            _status = "no stat edits";
            Plugin.Log.LogWarning("Warpstorm: config has 0 stat edits — nothing to apply (Army Painter colours are separate).");
            return;
        }

        try
        {
            _applied = TableApplier.Apply(_config);
            _editCount = _applied.Count;
            _status = $"ON — {_editCount} edit(s)";
            Plugin.Log.LogInfo($"Warpstorm ON ({reason}), {_editCount} edit(s) applied.");
        }
        catch (Exception ex)
        {
            _editCount = 0;
            _status = "apply failed";
            Plugin.Log.LogError($"Warpstorm apply failed: {ex}");
        }
    }

    private static bool TablesReady()
    {
        try
        {
            if (!RuntimeDataTables.HasInstance) return false;
            var rdt = RuntimeDataTables.Instance;
            return rdt != null && rdt.UnitDataTable != null && rdt.WeaponDataTable != null;
        }
        catch
        {
            return false;
        }
    }

    private void OnGUI()
    {
        if (!Plugin.ShowStatus.Value) return;
        try
        {
            GUI.depth = 1;
            GUI.Box(new Rect(10, 10, 620, 76), "");
            GUI.Label(new Rect(20, 16, 450, 18),
                $"Warpstorm {Plugin.Version}  [{(Active ? "ON" : "OFF")}]  {_status}");

            if (GUI.Button(new Rect(20, 42, 140, 24), $"Toggle ({KeyName(Plugin.ToggleKey.Value)})"))
            {
                Plugin.Enabled.Value = !Plugin.Enabled.Value;
                ApplyNow("ui");
            }
            if (GUI.Button(new Rect(168, 42, 140, 24), $"Reload ({KeyName(Plugin.ReloadKey.Value)})"))
            {
                LoadConfig();
                ApplyNow("ui-reload");
            }
            if (GUI.Button(new Rect(316, 42, 150, 24), "Open Configurator"))
                _status = Plugin.LaunchConfigurator();
            GUI.Label(new Rect(476, 46, 150, 18), $"{_editCount} edit(s) applied");
        }
        catch
        {
            // IMGUI is best-effort only.
        }
    }

    private static string KeyName(int code)
    {
        try { return ((KeyCode)code).ToString(); }
        catch { return code.ToString(); }
    }
}
