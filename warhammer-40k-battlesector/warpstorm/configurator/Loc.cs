using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace Warpstorm.Configurator;

/// <summary>
/// UI localisation. Same languages as BattleSector Tools; English is the
/// default and the fallback for any missing string. Tables are embedded
/// (i18n/&lt;code&gt;.json); the chosen language is remembered per user.
/// </summary>
public static class Loc
{
    public static readonly (string code, string native)[] Languages =
    {
        ("en", "English"), ("de", "Deutsch"), ("es", "Español"), ("fr", "Français"),
        ("ko", "한국어"), ("pl", "Polski"), ("pt-BR", "Português (Brasil)"), ("ru", "Русский"),
        ("zh-CN", "简体中文"), ("zh-TW", "繁體中文"),
    };

    private static readonly Dictionary<string, Dictionary<string, string>> Tables = new();

    public static string Code { get; private set; } = "en";
    public static bool IsEnglish => Code == "en";

    public static event Action Changed;

    public static void Set(string code, bool persist = true)
    {
        if (Languages.All(l => l.code != code)) code = "en";
        Code = code;
        if (persist) SavePreference(code);
        Changed?.Invoke();
    }

    public static string T(string key) => Lookup(Code, key) ?? Lookup("en", key) ?? key;

    /// <summary>Looks up <paramref name="key"/>; falls back to <paramref name="english"/> (e.g. fields.json labels).</summary>
    public static string T(string key, string english) => Lookup(Code, key) ?? english ?? Lookup("en", key) ?? key;

    public static string F(string key, params object[] args)
    {
        try { return string.Format(CultureInfo.InvariantCulture, T(key), args); }
        catch (FormatException) { return string.Format(CultureInfo.InvariantCulture, Lookup("en", key) ?? key, args); }
    }

    /// <summary>Joins short facts with the locale's list separator (no decorative middle dots).</summary>
    public static string List(params string[] parts)
        => string.Join(Code.StartsWith("zh") ? "，" : Code == "ko" ? ", " : ", ", parts.Where(p => !string.IsNullOrEmpty(p)));

    public static string Field(FieldDef f, bool weapon) => T((weapon ? "field.weapon." : "field.unit.") + f.Key, f.Label);
    public static string FieldHint(FieldDef f, bool weapon)
        => Lookup(Code, (weapon ? "field.weapon." : "field.unit.") + f.Key + ".hint") ?? f.Hint;
    public static string Group(string group) => T("group." + group, group);
    public static string Option(FieldDef f, EnumOption o) => T($"option.{f.Key}.{o.Value}", o.Label);

    private static string Lookup(string code, string key)
    {
        if (!Tables.TryGetValue(code, out var table))
            Tables[code] = table = LoadTable(code);
        return table.TryGetValue(key, out var v) && !string.IsNullOrEmpty(v) ? v : null;
    }

    public static IReadOnlyDictionary<string, string> Table(string code)
    {
        Lookup(code, "");
        return Tables[code];
    }

    private static Dictionary<string, string> LoadTable(string code)
    {
        var result = new Dictionary<string, string>();
        try
        {
            var asm = typeof(Loc).Assembly;
            using var stream = asm.GetManifestResourceStream($"i18n/{code}.json");
            if (stream == null) return result;
            using var doc = JsonDocument.Parse(stream, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            foreach (var p in doc.RootElement.EnumerateObject())
                if (p.Value.ValueKind == JsonValueKind.String) result[p.Name] = p.Value.GetString() ?? "";
        }
        catch
        {
            // a broken table falls back to English
        }
        return result;
    }

    // ------------------------------------------------------- preference

    private static string PreferencePath =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Warpstorm", "configurator.json");

    /// <summary>The saved language, or English. The OS language is deliberately not used.</summary>
    public static string LoadPreference()
    {
        try
        {
            if (!File.Exists(PreferencePath)) return "en";
            using var doc = JsonDocument.Parse(File.ReadAllText(PreferencePath));
            return doc.RootElement.TryGetProperty("language", out var l) ? l.GetString() ?? "en" : "en";
        }
        catch
        {
            return "en";
        }
    }

    private static void SavePreference(string code)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(PreferencePath)!);
            File.WriteAllText(PreferencePath, JsonSerializer.Serialize(new Dictionary<string, string> { ["language"] = code }));
        }
        catch
        {
            // preference is a convenience only
        }
    }
}
