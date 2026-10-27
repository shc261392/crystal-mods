using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using static Warpstorm.Configurator.Loc;

namespace Warpstorm.Configurator;

public partial class MainWindow
{
    // =========================================================== changes

    private Control BuildChangesPage()
    {
        var unsaved = _session.UnsavedKeys();
        var page = new StackPanel { Spacing = 12, Margin = new Thickness(0, 0, 12, 12) };

        int stats = _session.StatEditCount, paint = _session.PaintCustomCount;
        int settings = EditSession.Settings.Count(s => _session.SettingValues[s.Id] != s.Default);
        page.Children.Add(Ui.Gilded(Ui.Column(8,
            Ui.Text(F("changes.summary", stats, paint, settings), "heading", 22),
            Ui.Text(unsaved.Count > 0 ? F("changes.unsaved", unsaved.Count) : T("changes.allSaved"),
                unsaved.Count > 0 ? "muted" : "faint", 12),
            Ui.Row(8,
                Ui.IconTextButton(Icons.Save, T("header.save"), () => Save(), "primary"),
                Ui.IconTextButton(Icons.Undo, T("changes.discard"), Revert, "ghost"),
                Ui.IconTextButton(Icons.Delete, T("changes.removeAll"), async () =>
                {
                    var c = await Dialog.Ask(this, T("changes.removeAll.title"), F("changes.removeAll.body", stats),
                        T("common.remove"), T("common.cancel"));
                    if (c != 0) return;
                    _session.UnitEdits.Clear();
                    _session.WeaponEdits.Clear();
                    _session.NotifyChanged();
                    _unitRows = null;
                    _weaponRows = null;
                    ShowPage(AppPage.Changes);
                }, "ghost")))));

        page.Children.Add(StatChanges(T("nav.units"), false, unsaved));
        page.Children.Add(StatChanges(T("nav.weapons"), true, unsaved));

        // Army Painter.
        var paintRows = new StackPanel { Spacing = 4 };
        foreach (var f in _catalog.PaintDefaults)
        {
            bool custom = _session.IsPaintCustom(f.Key);
            bool dirty = unsaved.Contains("paint:" + f.Key);
            if (!custom && !dirty) continue;
            var (pri, sec) = _session.Paint[f.Key];
            var key = f.Key;
            var name = _catalog.Factions.FirstOrDefault(x => x.Id == f.FactionId)?.DisplayName(Lang) ?? f.Name;
            var open = Ui.Button(name, () => { _paintKey = key; ShowPage(AppPage.Paint); }, "ghost");
            var reset = Ui.Button(T("common.reset"), () => { _session.SetPaint(key, f.Primary, f.Secondary); }, "ghost");
            paintRows.Children.Add(Ui.Row(10,
                Dot(dirty), open,
                Ui.Swatch(f.Primary, 22, 14), Ui.Swatch(f.Secondary, 22, 14), Icons.Make(Icons.ArrowRight, 14, Ui.Brush("FaintBrush")),
                Ui.Swatch(pri, 22, 14), Ui.Swatch(sec, 22, 14),
                Ui.Text($"#{pri} / #{sec}", "mono muted", 12), reset));
        }
        if (paintRows.Children.Count == 0) paintRows.Children.Add(Ui.Text(T("changes.paintDefault"), "faint", 12));
        page.Children.Add(Ui.Surface(Ui.Column(8, Ui.Text(T("nav.paint"), "groupTitle"), paintRows), new Thickness(0, 14, 0, 4)));

        // Settings.
        var settingRows = new StackPanel { Spacing = 4 };
        foreach (var s in EditSession.Settings)
        {
            var v = _session.SettingValues[s.Id];
            bool dirty = unsaved.Contains("setting:" + s.Id);
            if (v == s.Default && !dirty) continue;
            settingRows.Children.Add(Ui.Row(10, Dot(dirty), Ui.Text(SettingLabel(s), null, 12.5),
                Ui.Text($"{SettingDisplay(s, s.Default)} → {SettingDisplay(s, v)}", "mono muted", 12),
                Ui.Button(T("common.reset"), () => _session.SetSetting(s.Id, s.Default), "ghost")));
        }
        if (settingRows.Children.Count == 0) settingRows.Children.Add(Ui.Text(T("changes.settingsDefault"), "faint", 12));
        page.Children.Add(Ui.Surface(Ui.Column(8, Ui.Text(T("nav.settings"), "groupTitle"), settingRows), new Thickness(0, 14, 0, 4)));

        return new ScrollViewer { Content = page };
    }

    private Control StatChanges(string title, bool weapon, HashSet<string> unsaved)
    {
        var rows = new StackPanel { Spacing = 2 };
        var fields = weapon ? _catalog.Fields.Weapon : _catalog.Fields.Unit;
        var items = weapon ? _catalog.Weapons : _catalog.Units;
        var edits = _session.Edits(weapon);
        string prefix = weapon ? "weapon:" : "unit:";

        foreach (var (id, fieldEdits) in edits.OrderBy(e => items.FirstOrDefault(i => i.Id == e.Key)?.Name ?? e.Key))
        {
            var item = items.FirstOrDefault(i => i.Id == id)
                       ?? new CatalogItem { Id = id, Name = F("changes.unknownId", id), IsWeapon = weapon };
            var head = Ui.Row(8, Ui.PortraitBox(item, 28), Ui.Button(item.DisplayName(Lang), () => Navigate(item), "ghost"),
                Ui.Button(T("changes.resetEntry"), () => _session.ClearEdits(item), "ghost"));
            head.Margin = new Thickness(0, 6, 0, 2);
            rows.Children.Add(head);

            foreach (var (key, value) in fieldEdits)
            {
                var f = fields.FirstOrDefault(x => x.Key == key);
                var original = _session.Original(item, key);
                var line = new Grid { ColumnDefinitions = new ColumnDefinitions("16,260,*,Auto"), ColumnSpacing = 8, Margin = new Thickness(36, 0, 0, 0) };
                line.Children.Add(Dot(unsaved.Contains($"{prefix}{id}:{key}")));
                var l = Ui.Text(f != null ? Field(f, weapon) : key, null, 12.5);
                Grid.SetColumn(l, 1);
                line.Children.Add(l);
                string before = original == null ? "?" : f != null ? DisplayValue(f, original) : original;
                string after = f != null ? DisplayValue(f, EditSession.Format(value)) : EditSession.Format(value);
                var v = Ui.Text($"{before}  →  {after}", "mono", 12);
                v.Foreground = Ui.Brush("GoldBrush");
                Grid.SetColumn(v, 2);
                line.Children.Add(v);
                var k = key;
                var x = new Button { Content = Icons.Make(Icons.Close, 13), Classes = { "icon" } };
                ToolTip.SetTip(x, T("changes.removeEdit"));
                x.Click += (_, _) => _session.SetEdit(item, k, null);
                Grid.SetColumn(x, 3);
                line.Children.Add(x);
                rows.Children.Add(line);
            }
        }

        // Entries removed since the last save still show up as unsaved.
        int removed = unsaved.Where(k => k.StartsWith(prefix)).Count(k =>
        {
            var parts = k.Split(':');
            return !(edits.TryGetValue(parts[1], out var e2) && e2.ContainsKey(parts[2]));
        });
        if (edits.Count == 0)
            rows.Children.Add(Ui.Text(T(weapon ? "changes.noWeaponEdits" : "changes.noUnitEdits"), "faint", 12));
        if (removed > 0)
            rows.Children.Add(Ui.Row(4, Ui.Dot(true), Ui.Text(F("changes.removed", removed), "muted", 12)));

        return Ui.Surface(Ui.Column(4, Ui.Text($"{title} ({edits.Count})", "groupTitle"), rows), new Thickness(0, 14, 0, 4));
    }

    private static Control Dot(bool on) => Ui.Dot(on);

    private static string SettingDisplay(SettingDef s, string v) => s.Type switch
    {
        "key" => KeyNames.Name(v),
        "bool" => T(v.Equals("true", StringComparison.OrdinalIgnoreCase) ? "common.on" : "common.off"),
        _ => v,
    };

    // ========================================================== settings

    private Control BuildSettingsPage()
    {
        var page = new StackPanel { Spacing = 12, Margin = new Thickness(0, 0, 12, 12) };

        // Game folder.
        var path = new TextBox { Text = _session.GameDir, IsReadOnly = true, PlaceholderText = T("settings.folderPlaceholder") };
        var folderGrid = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto,Auto"), ColumnSpacing = 6 };
        folderGrid.Children.Add(path);
        var browse = Ui.IconTextButton(Icons.Folder, T("settings.browse"), BrowseGameFolder, _session.HasGame ? "ghost" : "primary");
        Grid.SetColumn(browse, 1);
        folderGrid.Children.Add(browse);
        var openFolder = Ui.Button(T("settings.open"), () => OpenPath(_session.GameDir), "ghost");
        openFolder.IsEnabled = _session.HasGame;
        Grid.SetColumn(openFolder, 2);
        folderGrid.Children.Add(openFolder);
        page.Children.Add(Ui.Gilded(Ui.Column(8,
            Ui.Text(T("settings.folder"), "groupTitle"),
            Wrap(Ui.Text(F("settings.folderHint", GameLocator.ExeName), "muted", 12)),
            folderGrid,
            _session.HasGame ? Ui.Text(F("settings.gameVersion", _session.GameVersion), "faint", 11) : null)));

        page.Children.Add(SettingsCard(T("settings.controls"), s => s.Type == "key" || s.Name is "ShowStatus" or "ShowButton"));
        page.Children.Add(SettingsCard(T("settings.behaviour"), s => s.Name is "Enabled" or "AutoApply" or "ApproxPortraits" or "DiagMode"));

        // Files.
        var files = new StackPanel { Spacing = 6 };
        void FileRow(string label, string file)
        {
            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("200,*,Auto"), ColumnSpacing = 8 };
            g.Children.Add(Ui.Text(label, null, 12.5));
            var p = Ui.Text(file, "mono faint", 11);
            p.TextTrimming = TextTrimming.CharacterEllipsis;
            ToolTip.SetTip(p, file);
            Grid.SetColumn(p, 1);
            g.Children.Add(p);
            var b = Ui.Button(T("settings.show"), () => OpenPath(File.Exists(file) ? Path.GetDirectoryName(file) : file), "ghost");
            b.IsEnabled = File.Exists(file) || Directory.Exists(file);
            Grid.SetColumn(b, 2);
            g.Children.Add(b);
            files.Children.Add(g);
        }
        if (_session.HasGame)
        {
            FileRow(T("settings.fileStats"), _session.StatsConfigPath);
            FileRow(T("settings.filePaint"), _session.PaintConfigPath);
            FileRow(T("settings.fileSettings"), _session.PluginConfigPath);
            FileRow(T("settings.fileLog"), Path.Combine(_session.GameDir, "BepInEx", "LogOutput.log"));
        }
        else files.Children.Add(Ui.Text(T("status.pickFolderFirst"), "faint", 12));
        page.Children.Add(Ui.Surface(Ui.Column(8, Ui.Text(T("settings.files"), "groupTitle"), files), new Thickness(0, 14, 0, 4)));

        // Shortcut (Windows only, opt-in).
        if (OperatingSystem.IsWindows())
        {
            var lnk = StartMenuShortcutPath();
            bool exists = File.Exists(lnk);
            var status = Ui.Text(T(exists ? "settings.shortcutPresent" : "settings.shortcutNone"), "faint", 11);
            var add = Ui.Button(T(exists ? "settings.shortcutUpdate" : "settings.shortcutAdd"), () =>
            {
                try
                {
                    CreateShortcut(lnk);
                    status.Text = T("settings.shortcutAdded");
                }
                catch (Exception ex) { status.Text = F("settings.shortcutFailed", ex.Message); }
            }, "ghost");
            var remove = Ui.Button(T("common.remove"), () =>
            {
                try { File.Delete(lnk); status.Text = T("settings.shortcutRemoved"); }
                catch (Exception ex) { status.Text = F("settings.shortcutRemoveFailed", ex.Message); }
            }, "ghost");
            page.Children.Add(Ui.Surface(Ui.Column(8,
                Ui.Text(T("settings.startMenu"), "groupTitle"),
                Wrap(Ui.Text(T("settings.startMenuHint"), "muted", 12)),
                Ui.Row(6, add, remove), status)));
        }

        return new ScrollViewer { Content = page };
    }

    private Control SettingsCard(string title, Func<SettingDef, bool> filter)
    {
        var rows = new StackPanel { Spacing = 8 };
        foreach (var s in EditSession.Settings.Where(filter))
        {
            var hint = SettingHint(s);
            var label = Ui.Column(2, Ui.Text(SettingLabel(s), null, 14),
                hint.Length > 0 ? Wrap(Ui.Text(hint, "faint", 12)) : null);
            ToolTip.SetTip(label, (s.File == "warpstorm" ? "com.crystalmods.warpstorm.cfg" : "com.crystalmods.armypainter.cfg") + $"  [{s.Section}] {s.Name}");
            Control editor;
            var value = _session.SettingValues[s.Id];
            if (s.Type == "bool")
            {
                var t = new ToggleSwitch
                {
                    IsChecked = value.Equals("true", StringComparison.OrdinalIgnoreCase),
                    OnContent = T("common.on"),
                    OffContent = T("common.off"),
                };
                t.IsCheckedChanged += (_, _) => _session.SetSetting(s.Id, t.IsChecked == true ? "true" : "false");
                editor = t;
            }
            else if (s.Type == "key")
            {
                var choices = KeyNames.Choices.ToList();
                int.TryParse(value, out var code);
                if (choices.All(c => c.code != code)) choices.Add((code, KeyNames.Name(code)));
                var combo = new ComboBox { ItemsSource = choices.Select(c => c.name).ToList(), Width = 170 };
                combo.SelectedIndex = choices.FindIndex(c => c.code == code);
                combo.SelectionChanged += (_, _) =>
                {
                    if (combo.SelectedIndex < 0) return;
                    _session.SetSetting(s.Id, choices[combo.SelectedIndex].code.ToString(CultureInfo.InvariantCulture));
                    HotkeyText.Text = HotkeySummary();
                };
                editor = combo;
            }
            else editor = BuildSlider(s);

            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), ColumnSpacing = 16 };
            g.Children.Add(label);
            editor.VerticalAlignment = VerticalAlignment.Center;
            Grid.SetColumn(editor, 1);
            g.Children.Add(editor);
            rows.Children.Add(g);
        }
        return Ui.Surface(Ui.Column(10, Ui.Text(title, "groupTitle"), rows), new Thickness(0, 14, 0, 4));
    }

    private static string StartMenuShortcutPath()
        => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Warpstorm Configurator.lnk");

    private static void CreateShortcut(string lnk)
    {
        var exe = Environment.ProcessPath ?? throw new InvalidOperationException("unknown program path");
        var shellType = Type.GetTypeFromProgID("WScript.Shell") ?? throw new InvalidOperationException("WScript.Shell unavailable");
        dynamic shell = Activator.CreateInstance(shellType)!;
        dynamic shortcut = shell.CreateShortcut(lnk);
        shortcut.TargetPath = exe;
        shortcut.WorkingDirectory = Path.GetDirectoryName(exe);
        shortcut.IconLocation = exe + ",0";
        shortcut.Description = "Warpstorm Configurator";
        shortcut.Save();
    }

    private void OpenPath(string path)
    {
        if (string.IsNullOrEmpty(path)) return;
        try { Process.Start(new ProcessStartInfo { FileName = path, UseShellExecute = true }); }
        catch (Exception ex) { SetStatus(F("status.openFailed", path, ex.Message)); }
    }

    // ============================================================== help

    private Control BuildHelpPage()
    {
        TextBlock P(string t) => Wrap(Ui.Text(t, "muted", 13));
        string keys = F("help.keys",
            KeyNames.Name(_session.SettingValues.GetValueOrDefault("warpstorm:General/ToggleKey")),
            KeyNames.Name(_session.SettingValues.GetValueOrDefault("warpstorm:General/ReloadKey")),
            KeyNames.Name(_session.SettingValues.GetValueOrDefault("armypainter:UI/ToggleKey")));
        var page = Ui.Column(12,
            Ui.Gilded(Ui.Column(8,
                Ui.Text(T("help.headline"), "heading", 24),
                P("1. " + T("help.step1")),
                P("2. " + T("help.step2")),
                P("3. " + T("help.step3")),
                P("4. " + keys))),
            Ui.Surface(Ui.Column(8,
                Ui.Text(T("help.tutorial"), "groupTitle"),
                P("1. " + T("help.tut1")), P("2. " + T("help.tut2")), P("3. " + T("help.tut3")), P("4. " + T("help.tut4")),
                P("5. " + T("help.tut5")), P("6. " + T("help.tut6")), P("7. " + T("help.tut7")),
                Ui.Button(T("creator.open"), () => { ShowPage(AppPage.Paint); OpenCreator(); }, "primary"))),
            Ui.Surface(Ui.Column(8,
                Ui.Text(T("help.where"), "groupTitle"),
                P(T("help.whereBody")),
                P(T("help.whereEasier")),
                Ui.Text(Environment.ProcessPath ?? "", "mono faint", 11))),
            Ui.Surface(Ui.Column(8,
                Ui.Text(T("help.good"), "groupTitle"),
                P("• " + T("help.good1")),
                P("• " + T("help.good2")),
                P("• " + T("help.good3")),
                P("• " + T("help.good4")))),
            Ui.Surface(Ui.Column(4,
                Ui.Text(T("help.about"), "groupTitle"),
                Ui.Text(F("help.aboutLine", AppVersion), "faint", 12),
                Ui.Text(T("help.disclaimer"), "faint", 12))));
        page.Margin = new Thickness(0, 0, 12, 12);
        return new ScrollViewer { Content = page };
    }
}
