using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.InteropServices;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using Warpstorm.Shared;

namespace Warpstorm.Configurator;

public partial class MainWindow
{
    private string _paintKey = "";
    private int _paintTarget; // 0 = primary, 1 = secondary
    private bool _syncingColor;
    private ColorView _colorView;
    private TextBox _hexBox;
    private Border _priSwatch, _secSwatch;
    private TextBlock _priHex, _secHex;
    private ToggleButton _priButton, _secButton;
    private WrapPanel _previewPanel;
    private StackPanel _factionList;
    private StackPanel _paintHeader;
    private StackPanel _colourEditor;
    private TextBlock _previewHint;
    private ToggleSwitch _paintEnableToggle;
    private TextBlock _paintEnableStatus;

    private const string PaintEnabledId = "armypainter:Paint/Enabled";
    private ComboBox _schemeBox;
    private TextBlock _packInfo;
    private bool _syncingScheme;
    private List<Warpstorm.Shared.SchemePack> _schemeChoices = new();
    private readonly DispatcherTimer _previewDebounce = new() { Interval = TimeSpan.FromMilliseconds(90) };

    // Generic paint names (not trademarked paint ranges).
    private static readonly (string name, string hex)[] PaintPalette =
    {
        ("Blood Red", "900F0F"), ("Crimson", "B01212"), ("Scarlet", "D43A1E"), ("Rust", "8A3B1A"),
        ("Burnt Orange", "C06828"), ("Gold", "C9A227"), ("Yellow", "E3C33A"), ("Bone", "D9CBA3"),
        ("Ivory", "E8E4DA"), ("White", "F2F2F2"), ("Ash Grey", "8C8C8C"), ("Gunmetal", "4A4F57"),
        ("Black", "1C1D21"), ("Brown", "5A3A22"), ("Khaki", "9A8F6A"), ("Olive", "5F6B3F"),
        ("Forest Green", "2F6B2F"), ("Emerald", "1F8F5A"), ("Teal", "2F8F8F"), ("Turquoise", "48A8A0"),
        ("Sky Blue", "4A90D0"), ("Royal Blue", "1F4FB0"), ("Navy", "10305F"), ("Purple", "5A2F8F"),
        ("Magenta", "9A2F7A"), ("Pink", "D06A9A"),
    };

    private Control BuildPaintPage()
    {
        _previewDebounce.Tick -= OnPreviewTick;
        _previewDebounce.Tick += OnPreviewTick;
        if (_paintKey.Length == 0) _paintKey = _catalog.PaintDefaults.FirstOrDefault()?.Key ?? "";

        var grid = new Grid { ColumnDefinitions = new ColumnDefinitions("300,*"), ColumnSpacing = 14 };

        _factionList = new StackPanel { Spacing = 4 };
        RebuildFactionList();
        var left = new DockPanel();
        var intro = Ui.Column(8,
            Wrap(Ui.Text(Loc.T("paint.intro"), "muted", 13)));
        var import = Ui.IconTextButton(Icons.Import, Loc.T("paint.importPack"), async () => await ImportPack(), "ghost", Loc.T("paint.importPack.tip"));
        import.HorizontalAlignment = HorizontalAlignment.Stretch;
        intro.Children.Add(import);
        var create = Ui.IconTextButton(Icons.Edit, Loc.T("creator.open"), () => OpenCreator(), "ghost", Loc.T("creator.open.tip"));
        create.HorizontalAlignment = HorizontalAlignment.Stretch;
        intro.Children.Add(create);
        intro.Margin = new Thickness(0, 0, 0, 10);
        DockPanel.SetDock(intro, Dock.Top);
        left.Children.Add(intro);
        left.Children.Add(new ScrollViewer { Content = _factionList });
        grid.Children.Add(left);

        var right = new ScrollViewer { Content = BuildPaintEditor() };
        Grid.SetColumn(right, 1);
        grid.Children.Add(right);
        SyncPaintEditor();
        return grid;
    }

    private static string SettingLabel(SettingDef s) => Loc.T($"setting.{s.File}.{s.Name}");
    private static string SettingHint(SettingDef s)
    {
        var h = Loc.T($"setting.{s.File}.{s.Name}.hint");
        return h == $"setting.{s.File}.{s.Name}.hint" ? "" : h;
    }

    private static TextBlock Wrap(TextBlock t)
    {
        t.TextWrapping = TextWrapping.Wrap;
        return t;
    }

    private void RebuildFactionList()
    {
        if (_factionList == null) return;
        _factionList.Children.Clear();
        foreach (var f in _catalog.PaintDefaults)
        {
            var (pri, sec) = _session.Paint[f.Key];
            if (_session.Pack(_session.PaintScheme.GetValueOrDefault(f.Key)) is { } rowPack &&
                Hex.Normalize(rowPack.Primary) is { } pp && Hex.Normalize(rowPack.Secondary) is { } ps)
                (pri, sec) = (pp, ps);
            var faction = _catalog.Factions.FirstOrDefault(x => x.Id == f.FactionId);
            string name = faction?.DisplayName(Lang) ?? f.Name;

            var emblem = Ui.Image("ui/faction-" + f.FactionId);
            Control icon = emblem != null
                ? new Image { Source = emblem, Width = 34, Height = 34 }
                : new Border { Width = 34, Height = 34, CornerRadius = new CornerRadius(6), Background = Ui.Parse(pri),
                               Child = Ui.Text(f.Name[..1], null, 15, FontWeight.Black) };

            var text = Ui.Column(3,
                Ui.Text(name, null, 13, FontWeight.SemiBold),
                Ui.Row(4, Ui.Swatch(pri, 26, 12), Ui.Swatch(sec, 26, 12),
                    _session.Pack(_session.PaintScheme.GetValueOrDefault(f.Key)) is { } pk
                        ? Ui.Chip(pk.Name, "gold")
                        : _session.IsPaintCustom(f.Key) ? Ui.Chip(Loc.T("paint.custom"), "gold") : Ui.Text(Loc.T("paint.default"), "faint", 10)));

            var row = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*"), ColumnSpacing = 10 };
            row.Children.Add(icon);
            Grid.SetColumn(text, 1);
            row.Children.Add(text);

            var button = new ToggleButton
            {
                Content = row,
                IsChecked = f.Key == _paintKey,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                HorizontalContentAlignment = HorizontalAlignment.Stretch,
                Padding = new Thickness(8, 6),
                Classes = { "nav" },
            };
            var key = f.Key;
            button.Click += (_, _) =>
            {
                _paintKey = key;
                RebuildFactionList();
                SyncPaintEditor();
            };
            _factionList.Children.Add(button);
        }
    }

    private bool PaintEnabledSetting
        => _session.SettingValues.GetValueOrDefault(PaintEnabledId, "false")
            .Equals("true", StringComparison.OrdinalIgnoreCase);

    /// <summary>Opt-in switch: the plugin does no paint work until this is on and a colour differs.</summary>
    private Control BuildPaintEnableCard()
    {
        _paintEnableToggle = new ToggleSwitch
        {
            IsChecked = PaintEnabledSetting,
            OnContent = Loc.T("common.on"),
            OffContent = Loc.T("common.off"),
            VerticalAlignment = VerticalAlignment.Center,
        };
        _paintEnableToggle.IsCheckedChanged += (_, _) =>
        {
            _session.SetSetting(PaintEnabledId, _paintEnableToggle.IsChecked == true ? "true" : "false");
            RefreshPaintEnableStatus();
        };

        _paintEnableStatus = Wrap(Ui.Text("", "faint", 12));
        var row = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), ColumnSpacing = 16 };
        row.Children.Add(Ui.Column(2,
            Ui.Text(Loc.T("paint.enable"), null, 14, FontWeight.SemiBold),
            Wrap(Ui.Text(Loc.T("paint.enable.hint"), "faint", 12))));
        Grid.SetColumn(_paintEnableToggle, 1);
        row.Children.Add(_paintEnableToggle);

        RefreshPaintEnableStatus();
        return Ui.Gilded(Ui.Column(8, row, _paintEnableStatus));
    }

    private void RefreshPaintEnableStatus()
    {
        if (_paintEnableStatus == null) return;
        bool on = PaintEnabledSetting;
        int custom = _session.PaintCustomCount;
        _paintEnableStatus.Text = !on
            ? Loc.T("paint.enable.off")
            : custom == 0 ? Loc.T("paint.enable.idle")
            : Loc.F("paint.enable.on", custom);
    }

    private Control BuildPaintEditor()
    {
        // Primary / secondary target buttons.
        (ToggleButton b, Border sw, TextBlock hex) Target(string label, int index, string hint)
        {
            var sw = Ui.Swatch("000000", 46, 30);
            var hex = Ui.Text("", "mono muted", 12);
            var b = new ToggleButton
            {
                Content = Ui.Row(10, sw, Ui.Column(0, Ui.Text(label, null, 14, FontWeight.SemiBold), hex)),
                Classes = { "pill" },
                Padding = new Thickness(8, 6, 14, 6),
                CornerRadius = new CornerRadius(8),
            };
            ToolTip.SetTip(b, hint);
            b.Click += (_, _) =>
            {
                _paintTarget = index;
                SyncPaintEditor();
            };
            return (b, sw, hex);
        }
        (_priButton, _priSwatch, _priHex) = Target(Loc.T("paint.primary"), 0, Loc.T("paint.primary.hint"));
        (_secButton, _secSwatch, _secHex) = Target(Loc.T("paint.secondary"), 1, Loc.T("paint.secondary.hint"));

        var swap = Ui.IconTextButton(Icons.Swap, Loc.T("paint.swap"), () =>
        {
            var (p, s) = _session.Paint[_paintKey];
            _session.SetPaint(_paintKey, s, p);
            AfterPaintChange();
        }, "ghost", Loc.T("paint.swap.tip"));
        var reset = Ui.IconTextButton(Icons.Reset, Loc.T("paint.reset"), () =>
        {
            var d = _session.PaintDefault(_paintKey);
            if (d != null) _session.SetPaint(_paintKey, d.Primary, d.Secondary);
            AfterPaintChange();
        }, "ghost", Loc.T("paint.reset.tip"));

        var copyFrom = new ComboBox { PlaceholderText = Loc.T("paint.copyFrom"), MinWidth = 180 };
        copyFrom.ItemsSource = _catalog.PaintDefaults.Select(f => _catalog.Factions.FirstOrDefault(x => x.Id == f.FactionId)?.DisplayName(Lang) ?? f.Name).ToList();
        copyFrom.SelectionChanged += (_, _) =>
        {
            if (copyFrom.SelectedIndex < 0) return;
            var src = _catalog.PaintDefaults[copyFrom.SelectedIndex];
            var (p, s) = _session.Paint[src.Key];
            _session.SetPaint(_paintKey, p, s);
            copyFrom.SelectedIndex = -1;
            AfterPaintChange();
        };

        var targets = Ui.Row(10, _priButton, _secButton);
        var actions = Ui.Row(6, swap, reset, copyFrom);

        _schemeBox = new ComboBox { MinWidth = 280 };
        _schemeBox.SelectionChanged += (_, _) =>
        {
            if (_syncingScheme || _schemeBox.SelectedIndex < 0) return;
            var id = _schemeBox.SelectedIndex == 0 ? "" : _schemeChoices[_schemeBox.SelectedIndex - 1].Id;
            _session.SetScheme(_paintKey, id);
            AfterPaintChange();
        };
        _packInfo = Wrap(Ui.Text("", "muted", 12));
        var copyPack = Ui.IconTextButton(Icons.Edit, Loc.T("creator.editCopy"), () =>
        {
            var p = _session.Pack(_session.PaintScheme.GetValueOrDefault(_paintKey));
            OpenCreator(p);
        }, "ghost", Loc.T("creator.editCopy.tip"));
        var schemeRow = Ui.Column(6, Ui.Row(10, Ui.Text(Loc.T("paint.scheme"), "label"), _schemeBox, copyPack), _packInfo);

        // Colour picker + hex + palette.
        _colorView = new ColorView
        {
            IsAlphaEnabled = false,
            IsAlphaVisible = false,
            IsColorPaletteVisible = false,
            Width = 360,
            HorizontalAlignment = HorizontalAlignment.Left,
        };
        _colorView.ColorChanged += (_, e) =>
        {
            if (_syncingColor) return;
            SetTargetColor($"{e.NewColor.R:X2}{e.NewColor.G:X2}{e.NewColor.B:X2}");
        };

        _hexBox = new TextBox { Classes = { "value" }, Width = 110, PlaceholderText = "RRGGBB" };
        _hexBox.TextChanged += (_, _) =>
        {
            if (_syncingColor) return;
            var hex = Hex.Normalize(_hexBox.Text);
            if (hex != null) SetTargetColor(hex);
        };

        var palette = new WrapPanel { MaxWidth = 380 };
        foreach (var (name, hex) in PaintPalette)
        {
            var sw = new Button
            {
                Width = 30,
                Height = 30,
                Padding = new Thickness(0),
                Margin = new Thickness(0, 0, 5, 5),
                Background = Ui.Parse(hex),
                BorderBrush = Ui.Parse("#80000000"),
                CornerRadius = new CornerRadius(6),
            };
            ToolTip.SetTip(sw, $"{Loc.T("palette." + name.Replace(" ", ""), name)}  #{hex}");
            sw.Click += (_, _) => SetTargetColor(hex);
            palette.Children.Add(sw);
        }

        var pickerColumn = Ui.Column(10,
            Ui.Text(Loc.T("paint.palette"), "label"), palette,
            Ui.Row(8, Ui.Text(Loc.T("paint.hex"), "label"), _hexBox));

        var pickers = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*"), ColumnSpacing = 18 };
        pickers.Children.Add(_colorView);
        Grid.SetColumn(pickerColumn, 1);
        pickers.Children.Add(pickerColumn);

        _colourEditor = Ui.Column(14, targets, actions, pickers);
        var editorCard = Ui.Gilded(Ui.Column(14,
            BuildPaintHeader(),
            schemeRow,
            _colourEditor));

        // Preview.
        _previewPanel = new WrapPanel();
        var previewCard = Ui.Surface(Ui.Column(8,
            Ui.Text(Loc.T("paint.preview"), "groupTitle"),
            (_previewHint = Wrap(Ui.Text(Loc.T("paint.previewHint"), "faint", 12))),
            _previewPanel));

        // Fine tuning (shared with the plugin's [Paint] settings).
        var tuning = new StackPanel { Spacing = 8 };
        foreach (var s in EditSession.Settings.Where(s => s.File == "armypainter" && s.Section == "Paint" && s.Type == "float"))
            tuning.Children.Add(BuildSlider(s));
        // Rarely needed: tucked away.
        var tuneCard = new Expander
        {
            Header = Ui.Text(Loc.T("paint.tune") + " (" + Loc.T("paint.tune.hint") + ")", null, 13.5),
            Content = Ui.Column(8, Wrap(Ui.Text(Loc.T("paint.tuneHint"), "faint", 12)), tuning),
            HorizontalAlignment = HorizontalAlignment.Stretch,
        };


        return Ui.Column(16, BuildPaintEnableCard(), editorCard, previewCard, BuildBakeCard(), tuneCard);
    }

    private Control BuildPaintHeader()
    {
        _paintHeader = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 12 };
        return _paintHeader;
    }

    private void SyncPaintEditor()
    {
        if (_colorView == null || !_session.Paint.ContainsKey(_paintKey)) return;
        var (pri, sec) = _session.Paint[_paintKey];
        var def = _session.PaintDefault(_paintKey);

        _schemeChoices = _session.Packs.Where(p => p.Faction == _paintKey).ToList();
        var activePack = _session.Pack(_session.PaintScheme.GetValueOrDefault(_paintKey));
        _syncingScheme = true;
        _schemeBox.ItemsSource = new[] { Loc.T("paint.schemeColours") }
            .Concat(_schemeChoices.Select(p => $"{p.Name} {p.Version}" + (p.Author.Length > 0 ? " — " + p.Author : ""))).ToList();
        _schemeBox.SelectedIndex = activePack == null ? 0 : 1 + _schemeChoices.FindIndex(p => p.Id == activePack.Id);
        _syncingScheme = false;
        _colourEditor.IsVisible = activePack == null;
        if (_previewHint != null) _previewHint.IsVisible = activePack == null; // only the automatic recolour is approximate
        _packInfo.Text = activePack != null
            ? activePack.Description + "  " + Loc.T("paint.packNote")
            : _schemeChoices.Count == 0 ? Loc.T("paint.noPacks") : "";
        _packInfo.IsVisible = _packInfo.Text.Length > 0;

        _priButton.IsChecked = _paintTarget == 0;
        _secButton.IsChecked = _paintTarget == 1;
        _priSwatch.Background = Ui.Parse(pri);
        _secSwatch.Background = Ui.Parse(sec);
        _priHex.Text = "#" + pri;
        _secHex.Text = "#" + sec;

        var current = _paintTarget == 0 ? pri : sec;
        _syncingColor = true;
        try
        {
            _colorView.Color = Color.Parse("#" + current);
            if (Hex.Normalize(_hexBox.Text) != current) _hexBox.Text = current;
        }
        finally
        {
            _syncingColor = false;
        }

        // Header: emblem + name + default swatches.
        if (_paintHeader is { } header)
        {
            header.Children.Clear();
            var faction = _catalog.Factions.FirstOrDefault(x => x.Id == def?.FactionId);
            var emblem = Ui.Image("ui/faction-" + (def?.FactionId ?? -1));
            if (emblem != null) header.Children.Add(new Image { Source = emblem, Width = 56, Height = 56 });
            header.Children.Add(Ui.Column(2,
                Ui.Text(faction?.DisplayName(Lang) ?? def?.Name ?? _paintKey, null, 22, FontWeight.ExtraBold),
                Ui.Row(6, Ui.Text(Loc.T("paint.defaultLabel"), "faint", 11), Ui.Swatch(def?.Primary ?? "000000", 22, 12), Ui.Swatch(def?.Secondary ?? "000000", 22, 12),
                    _session.IsPaintCustom(_paintKey) ? Ui.Chip(Loc.T("paint.customScheme"), "gold") : Ui.Chip(Loc.T("paint.defaultScheme")))));
        }

        _previewDebounce.Stop();
        _previewDebounce.Start();
    }

    private async System.Threading.Tasks.Task ImportPack()
    {
        if (!_session.HasGame) { SetStatus(Loc.T("status.pickFolderFirst")); return; }
        try
        {
            var files = await StorageProvider.OpenFilePickerAsync(new Avalonia.Platform.Storage.FilePickerOpenOptions
            {
                Title = Loc.T("paint.importPack"),
                AllowMultiple = false,
                FileTypeFilter = new[] { new Avalonia.Platform.Storage.FilePickerFileType("Scheme pack") { Patterns = new[] { "*.zip" } } },
            });
            var path = files.FirstOrDefault()?.TryGetLocalPath();
            if (string.IsNullOrEmpty(path)) return;
            var pack = _session.ImportPack(path);
            if (pack != null) _paintKey = pack.Faction;
            ShowPage(AppPage.Paint);
            SetStatus(Loc.F("paint.imported", pack?.Name ?? "?", pack?.Faction ?? "?"));
        }
        catch (Exception ex)
        {
            SetStatus(Loc.F("paint.importFailed", ex.Message));
        }
    }

    private void SetTargetColor(string hex)
    {
        if (!_session.Paint.ContainsKey(_paintKey)) return;
        var (pri, sec) = _session.Paint[_paintKey];
        if (_paintTarget == 0) pri = hex; else sec = hex;
        _session.SetPaint(_paintKey, pri, sec);
        AfterPaintChange();
    }

    private void AfterPaintChange()
    {
        SyncPaintEditor();
        RebuildFactionList();
        RefreshPaintEnableStatus();
    }

    private Control BuildSlider(SettingDef s)
    {
        float value = _session.SettingFloat(s.Id, float.Parse(s.Default, CultureInfo.InvariantCulture));
        var slider = new Slider { Minimum = s.Min, Maximum = s.Max, Value = value, Width = 260, SmallChange = 0.01, LargeChange = 0.05 };
        var readout = Ui.Text(value.ToString("0.00", CultureInfo.InvariantCulture), "mono", 12);
        var reset = new Button { Content = Icons.Make(Icons.Reset, 14), Classes = { "icon" } };
        ToolTip.SetTip(reset, Loc.F("settings.default", s.Default));
        slider.PropertyChanged += (_, e) =>
        {
            if (e.Property != RangeBase.ValueProperty) return;
            var v = Math.Round(slider.Value, 2);
            readout.Text = v.ToString("0.00", CultureInfo.InvariantCulture);
            _session.SetSetting(s.Id, v.ToString(CultureInfo.InvariantCulture));
            _previewDebounce.Stop();
            _previewDebounce.Start();
        };
        reset.Click += (_, _) => slider.Value = double.Parse(s.Default, CultureInfo.InvariantCulture);

        var label = Ui.Text(SettingLabel(s), null, 12.5);
        ToolTip.SetTip(label, SettingHint(s));
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("200,Auto,50,Auto"), ColumnSpacing = 8 };
        g.Children.Add(label);
        Grid.SetColumn(slider, 1); g.Children.Add(slider);
        Grid.SetColumn(readout, 2); g.Children.Add(readout);
        Grid.SetColumn(reset, 3); g.Children.Add(reset);
        return g;
    }

    // ------------------------------------------------------------ preview

    private void OnPreviewTick(object sender, EventArgs e)
    {
        _previewDebounce.Stop();
        RenderPreview();
    }

    private void RenderPreview()
    {
        if (_previewPanel == null || !_session.Paint.ContainsKey(_paintKey)) return;
        _previewPanel.Children.Clear();
        var def = _session.PaintDefault(_paintKey);
        var (pri, sec) = _session.Paint[_paintKey];

        var samples = _catalog.Units
            .Where(u => u.FactionId == def?.FactionId && Ui.Image("units/" + u.Image) != null)
            .OrderBy(u => u.Role == "HQ" ? 1 : 0).ThenBy(u => u.Name)
            .Take(6)
            .ToList();
        if (samples.Count == 0)
        {
            _previewPanel.Children.Add(Ui.Text(Loc.T("paint.noPortraits"), "faint", 11));
            return;
        }

        var pack = _session.Pack(_session.PaintScheme.GetValueOrDefault(_paintKey));
        float hw = _session.SettingFloat("armypainter:Paint/HueWindow", 0.16f);
        float st = _session.SettingFloat("armypainter:Paint/SatThreshold", 0.08f);
        float fe = _session.SettingFloat("armypainter:Paint/BlendFeather", 0.08f);
        var p = Color.Parse("#" + pri);
        var s = Color.Parse("#" + sec);

        foreach (var unit in samples)
        {
            var src = Ui.Image("units/" + unit.Image);
            Bitmap after = null;
            if (pack != null)
            {
                var file = pack.PortraitFile(unit.Image);
                if (file != null) try { after = new Bitmap(file); } catch { }
            }
            if (after == null)
            {
                var rgba = ToRgba(src, out int w, out int h);
                if (rgba == null) continue;
                var mapped = pack != null
                    ? PaintMath.ApplyRules(rgba, pack.RulesForPortrait(unit.Image))
                    : PaintMath.Remap(rgba, p.R, p.G, p.B, s.R, s.G, s.B, hw, st, fe);
                after = FromRgba(mapped, w, h);
            }

            Control Pic(Bitmap b) => new Border
            {
                Width = 88, Height = 88, CornerRadius = new CornerRadius(6), ClipToBounds = true,
                Background = Ui.Parse("#33000000"),
                Child = new Image { Source = b, Stretch = Stretch.UniformToFill },
            };
            var pair = Ui.Row(4, Pic(src), Icons.Make(Icons.ArrowRight, 14, Ui.Brush("FaintBrush")), Pic(after));
            var label = Ui.Text(unit.DisplayName(Lang), "muted", 11);
            label.TextTrimming = TextTrimming.CharacterEllipsis;
            label.MaxWidth = 190;
            var cell = Ui.Column(4, pair, label);
            cell.Margin = new Thickness(0, 0, 18, 12);
            _previewPanel.Children.Add(cell);
        }
    }

    /// <summary>Reads a bitmap into straight-alpha RGBA bytes.</summary>
    private static byte[] ToRgba(Bitmap bmp, out int w, out int h)
    {
        w = bmp.PixelSize.Width;
        h = bmp.PixelSize.Height;
        var format = bmp.Format ?? PixelFormat.Bgra8888;
        if (format != PixelFormat.Bgra8888 && format != PixelFormat.Rgba8888) return null;
        int stride = w * 4;
        var buf = new byte[stride * h];
        var handle = GCHandle.Alloc(buf, GCHandleType.Pinned);
        try { bmp.CopyPixels(new PixelRect(0, 0, w, h), handle.AddrOfPinnedObject(), buf.Length, stride); }
        finally { handle.Free(); }

        bool premul = bmp.AlphaFormat == AlphaFormat.Premul;
        bool bgra = format == PixelFormat.Bgra8888;
        for (int i = 0; i < buf.Length; i += 4)
        {
            if (bgra) (buf[i], buf[i + 2]) = (buf[i + 2], buf[i]);
            byte a = buf[i + 3];
            if (premul && a > 0 && a < 255)
                for (int c = 0; c < 3; c++) buf[i + c] = (byte)Math.Min(255, buf[i + c] * 255 / a);
        }
        return buf;
    }

    private static Bitmap FromRgba(byte[] rgba, int w, int h)
    {
        var wb = new WriteableBitmap(new PixelSize(w, h), new Vector(96, 96), PixelFormat.Rgba8888, AlphaFormat.Unpremul);
        using var fb = wb.Lock();
        for (int y = 0; y < h; y++)
            Marshal.Copy(rgba, y * w * 4, fb.Address + y * fb.RowBytes, w * 4);
        return wb;
    }
}
