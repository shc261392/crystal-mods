using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using Warpstorm.Shared;
using static Warpstorm.Configurator.Loc;

namespace Warpstorm.Configurator;

/// <summary>
/// Scheme Creator: build your own Army Painter scheme pack for any faction —
/// colour rules with an eyedropper, a live preview on portraits and real model
/// textures, an optional chapter badge, then save (installs it) or export (.zip).
/// </summary>
public partial class MainWindow
{
    private sealed class RuleVm
    {
        public float Hue = 222, Width = 20, Feather = 10, SatMin = 0.2f, ValMin = 0f, ValMax = 1f, SatScale = 1f, ValScale = 0.9f;
        public string To = "24572B";

        public PaintMath.Rule ToRule() => new()
        {
            Hue = Hue / 360f, HueWidth = Width / 360f, Feather = Feather / 360f, SatMin = SatMin, ValMin = ValMin, ValMax = ValMax,
            SatScale = SatScale, ValScale = ValScale,
            R = Convert.ToByte(To[..2], 16), G = Convert.ToByte(To.Substring(2, 2), 16), B = Convert.ToByte(To.Substring(4, 2), 16),
        };
    }

    private sealed class CreatorState
    {
        public string Faction = "Ultramarines";
        public string Name = "My Chapter", Author = "", Version = "1.0.0", Description = "";
        public List<RuleVm> Rules = new();
        public string BadgePath = "";   // PNG on disk ("" = keep the faction's own symbol)
    }

    /// <summary>Decal atlases holding the chapter symbol, per faction (verified from the game bundles).</summary>
    private static readonly Dictionary<string, (string[] textures, float[] rect)> BadgeAtlases = new()
    {
        ["Ultramarines"] = (new[] { "ULT_Logo_D", "ULT_Logo_edit_D", "ULT_Logo_damaged_D" }, new[] { 0.290f, 0.015f, 0.437f, 0.160f }),
    };

    private CreatorState _cs;
    private int _activeRule;
    private StackPanel _rulesPanel;
    private WrapPanel _creatorPreview;
    private StackPanel _modelPreview;
    private Image _badgePreview;
    private readonly DispatcherTimer _creatorDebounce = new() { Interval = TimeSpan.FromMilliseconds(150) };
    private readonly Dictionary<string, (byte[] rgba, int w, int h)> _modelTextures = new();
    private (byte[] rgba, int w, int h)? _logoAtlas;

    private void OpenCreator(SchemePack from = null)
    {
        _cs = new CreatorState { Faction = from?.Faction ?? (_paintKey.Length > 0 ? _paintKey : "Ultramarines") };
        if (from != null)
        {
            _cs.Name = from.Name + " (copy)";
            _cs.Author = from.Author;
            _cs.Description = from.Description;
            _cs.Rules = from.Rules.Select(r => new RuleVm
            {
                Hue = r.Hue * 360f, Width = r.HueWidth * 360f, Feather = r.Feather * 360f, SatMin = r.SatMin, ValMin = r.ValMin, ValMax = r.ValMax,
                SatScale = r.SatScale, ValScale = r.ValScale, To = $"{r.R:X2}{r.G:X2}{r.B:X2}",
            }).ToList();
            if (from.BadgeFile != null && File.Exists(from.BadgeFile)) _cs.BadgePath = from.BadgeFile;
        }
        else _cs.Rules = SuggestRules(_cs.Faction);
        _activeRule = 0;
        _modelTextures.Clear();
        _creatorDebounce.Tick -= OnCreatorTick;
        _creatorDebounce.Tick += OnCreatorTick;
        ContentHost.Content = BuildCreator();
        RenderCreatorPreview();
    }

    /// <summary>Two starter rules from the faction's dominant paint colour: armour + highlights.</summary>
    private List<RuleVm> SuggestRules(string faction)
    {
        var def = _session.PaintDefault(faction);
        float hue = 222;
        var samples = FactionUnitsWithPortraits(faction).Take(6).ToList();
        var hist = new float[36];
        foreach (var u in samples)
        {
            var rgba = ToRgba(Ui.Image("units/" + u.Image), out _, out _);
            if (rgba == null) continue;
            PaintMath.Detect(rgba, 0.15f, out var pc, out _, out _);
            if (pc.Count > 0) hist[(int)(pc.Hue * 36) % 36] += pc.Count;
        }
        int best = Array.IndexOf(hist, hist.Max());
        if (hist[best] > 0) hue = (best + 0.5f) * 10f;
        // Start from a clearly different example colour so the preview changes right away.
        string target = def?.Key == "Ork" ? "8F1010" : "1F5B2C";
        return new List<RuleVm>
        {
            new() { Hue = hue, Width = 20, Feather = 10, SatMin = 0.22f, To = target, SatScale = 0.95f, ValScale = 0.85f },
            new() { Hue = hue, Width = 18, Feather = 8, SatMin = 0.07f, ValMin = 0.45f, To = Lighten(target), SatScale = 0.9f, ValScale = 0.95f },
        };
    }

    private static string Lighten(string hex)
    {
        var c = Color.Parse("#" + hex);
        byte L(byte v) => (byte)Math.Min(255, v + (255 - v) * 0.45);
        return $"{L(c.R):X2}{L(c.G):X2}{L(c.B):X2}";
    }

    private IEnumerable<CatalogItem> FactionUnitsWithPortraits(string faction)
    {
        var def = _session.PaintDefault(faction);
        return _catalog.Units.Where(u => u.FactionId == def?.FactionId && Ui.Image("units/" + u.Image) != null)
                             .OrderBy(u => u.Role == "HQ" ? 1 : 0).ThenBy(u => u.Name);
    }

    // ================================================================ UI

    private Control BuildCreator()
    {
        var back = Ui.IconTextButton(Icons.Back, T("creator.back"), () => ShowPage(AppPage.Paint), "ghost");
        var header = Ui.Row(14, back, Ui.Text(T("creator.title"), "heading", 24));

        // Basics
        var factions = _catalog.PaintDefaults;
        var factionBox = new ComboBox
        {
            ItemsSource = factions.Select(f => _catalog.Factions.FirstOrDefault(x => x.Id == f.FactionId)?.DisplayName(Lang) ?? f.Name).ToList(),
            SelectedIndex = Math.Max(0, factions.FindIndex(f => f.Key == _cs.Faction)),
            MinWidth = 220,
        };
        factionBox.SelectionChanged += (_, _) =>
        {
            if (factionBox.SelectedIndex < 0) return;
            _cs.Faction = factions[factionBox.SelectedIndex].Key;
            _cs.Rules = SuggestRules(_cs.Faction);
            _activeRule = 0;
            _modelTextures.Clear();
            _logoAtlas = null;
            ContentHost.Content = BuildCreator();
            RenderCreatorPreview();
        };
        TextBox Field(string value, Action<string> set, string placeholder = null)
        {
            var tb = new TextBox { Text = value, PlaceholderText = placeholder, MinWidth = 220 };
            tb.TextChanged += (_, _) => set(tb.Text ?? "");
            return tb;
        }
        var basics = Ui.Surface(Ui.Column(8,
            Ui.Text(T("creator.step1"), "groupTitle"),
            Wrap(Ui.Text(T("creator.step1.hint"), "faint", 11)),
            LabeledRow(T("creator.baseFaction"), factionBox),
            LabeledRow(T("creator.name"), Field(_cs.Name, v => _cs.Name = v)),
            LabeledRow(T("creator.author"), Field(_cs.Author, v => _cs.Author = v, T("creator.authorPlaceholder"))),
            LabeledRow(T("creator.description"), Field(_cs.Description, v => _cs.Description = v))));

        // Rules
        _rulesPanel = new StackPanel { Spacing = 8 };
        RebuildRules();
        var addRule = Ui.IconTextButton(Icons.Plus, T("creator.addRule"), () =>
        {
            _cs.Rules.Add(new RuleVm { Hue = 40, Width = 15, Feather = 8, SatMin = 0.25f, To = "C9A227" });
            _activeRule = _cs.Rules.Count - 1;
            RebuildRules();
            QueueCreatorPreview();
        }, "ghost");
        var rulesCard = Ui.Surface(Ui.Column(8,
            Ui.Text(T("creator.step2"), "groupTitle"),
            Wrap(Ui.Text(T("creator.step2.hint"), "faint", 11)),
            _rulesPanel, addRule));

        // Badge
        Control badgeCard;
        if (BadgeAtlases.ContainsKey(_cs.Faction))
        {
            var builtIns = _session.Packs.Where(p => p.BadgeFile != null && File.Exists(p.BadgeFile)).ToList();
            var badgeBox = new ComboBox
            {
                ItemsSource = new[] { T("creator.badgeNone") }.Concat(builtIns.Select(p => p.Name)).Concat(new[] { T("creator.badgeCustom") }).ToList(),
                MinWidth = 220,
            };
            int idx = builtIns.FindIndex(p => p.BadgeFile == _cs.BadgePath);
            badgeBox.SelectedIndex = _cs.BadgePath.Length == 0 ? 0 : idx >= 0 ? idx + 1 : builtIns.Count + 1;
            badgeBox.SelectionChanged += async (_, _) =>
            {
                if (badgeBox.SelectedIndex == 0) _cs.BadgePath = "";
                else if (badgeBox.SelectedIndex <= builtIns.Count) _cs.BadgePath = builtIns[badgeBox.SelectedIndex - 1].BadgeFile;
                else
                {
                    var files = await StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
                    {
                        Title = T("creator.badgeCustom"),
                        FileTypeFilter = new[] { new FilePickerFileType("PNG") { Patterns = new[] { "*.png" } } },
                    });
                    var path = files.FirstOrDefault()?.TryGetLocalPath();
                    if (!string.IsNullOrEmpty(path)) _cs.BadgePath = path;
                }
                QueueCreatorPreview();
            };
            _badgePreview = new Image { Width = 120, Height = 120 };
            badgeCard = Ui.Surface(Ui.Column(8,
                Ui.Text(T("creator.step3"), "groupTitle"),
                Wrap(Ui.Text(T("creator.step3.hint"), "faint", 11)),
                Ui.Row(12, badgeBox, _badgePreview)));
        }
        else
        {
            _badgePreview = null;
            badgeCard = Ui.Surface(Ui.Column(6,
                Ui.Text(T("creator.step3"), "groupTitle"),
                Wrap(Ui.Text(F("creator.badgeUnavailable", _cs.Faction), "faint", 11))));
        }

        // Save / export
        var save = Ui.Button(T("creator.save"), () => SaveCreatedPack(), "primary", T("creator.save.tip"));
        var export = Ui.Button(T("creator.export"), async () => await ExportCreatedPack(), "ghost", T("creator.export.tip"));
        var saveCard = Ui.Surface(Ui.Column(8,
            Ui.Text(T("creator.step4"), "groupTitle"),
            Wrap(Ui.Text(T("creator.step4.hint"), "faint", 11)),
            Ui.Row(8, save, export)));

        var left = new ScrollViewer { Content = Ui.Column(12, basics, rulesCard, badgeCard, saveCard) };

        // Preview
        _creatorPreview = new WrapPanel();
        _modelPreview = new StackPanel { Spacing = 6 };
        var loadModels = Ui.Button(T("creator.loadModels"), async () => await LoadModelTextures(), "ghost", T("creator.loadModels.tip"));
        var previewCard = Ui.Gilded(Ui.Column(10,
            Ui.Text(T("paint.preview"), "groupTitle"),
            Wrap(Ui.Text(T("creator.previewHint"), "faint", 11)),
            _creatorPreview,
            Ui.Text(T("creator.models"), "label"),
            loadModels,
            _modelPreview));
        var right = new ScrollViewer { Content = previewCard };

        var grid = new Grid { ColumnDefinitions = new ColumnDefinitions("460,*"), ColumnSpacing = 14 };
        grid.Children.Add(left);
        Grid.SetColumn(right, 1);
        grid.Children.Add(right);

        var dock = new DockPanel();
        header.Margin = new Thickness(0, 0, 0, 12);
        DockPanel.SetDock(header, Dock.Top);
        dock.Children.Add(header);
        dock.Children.Add(grid);
        return dock;
    }

    private static Control LabeledRow(string label, Control editor)
    {
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("130,*"), ColumnSpacing = 8 };
        g.Children.Add(Ui.Text(label, null, 12.5));
        Grid.SetColumn(editor, 1);
        g.Children.Add(editor);
        return g;
    }

    private void RebuildRules()
    {
        _rulesPanel.Children.Clear();
        for (int i = 0; i < _cs.Rules.Count; i++)
        {
            int index = i;
            var r = _cs.Rules[i];
            bool active = i == _activeRule;

            var sourceSwatch = Ui.Swatch(HueHex(r.Hue), 34, 22);
            ToolTip.SetTip(sourceSwatch, T("creator.sourceTip"));
            var picker = new ColorPicker { Color = Color.Parse("#" + r.To), IsAlphaEnabled = false, IsAlphaVisible = false };
            picker.ColorChanged += (_, e) =>
            {
                r.To = $"{e.NewColor.R:X2}{e.NewColor.G:X2}{e.NewColor.B:X2}";
                QueueCreatorPreview();
            };
            var select = Ui.IconTextButton(Icons.Eyedropper, T("creator.eyedropper"), () =>
            {
                _activeRule = index;
                RebuildRules();
            }, active ? "primary" : "ghost", T("creator.eyedropper.tip"));
            var remove = new Button { Content = Icons.Make(Icons.Close, 13), Classes = { "icon" } };
            ToolTip.SetTip(remove, T("creator.removeRule"));
            remove.IsEnabled = _cs.Rules.Count > 1;
            remove.Click += (_, _) =>
            {
                _cs.Rules.RemoveAt(index);
                _activeRule = Math.Min(_activeRule, _cs.Rules.Count - 1);
                RebuildRules();
                QueueCreatorPreview();
            };

            var head = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,Auto,Auto,Auto,*,Auto"), ColumnSpacing = 8 };
            head.Children.Add(Ui.Text(F("creator.rule", i + 1), "statLabel", 12.5));
            Grid.SetColumn(sourceSwatch, 1); head.Children.Add(sourceSwatch);
            var arrow = Icons.Make(Icons.ArrowRight, 14, Ui.Brush("FaintBrush")); Grid.SetColumn(arrow, 2); head.Children.Add(arrow);
            Grid.SetColumn(picker, 3); head.Children.Add(picker);
            Grid.SetColumn(select, 4); select.HorizontalAlignment = HorizontalAlignment.Right; head.Children.Add(select);
            Grid.SetColumn(remove, 5); head.Children.Add(remove);

            var body = Ui.Column(4,
                RuleSlider(T("creator.hue"), r.Hue, 0, 360, "0", v => { r.Hue = v; sourceSwatch.Background = Ui.Parse(HueHex(v)); }),
                RuleSlider(T("creator.width"), r.Width, 3, 60, "0", v => r.Width = v),
                RuleSlider(T("creator.feather"), r.Feather, 0, 30, "0", v => r.Feather = v),
                RuleSlider(T("creator.satMin"), r.SatMin, 0, 0.6f, "0.00", v => r.SatMin = v),
                RuleSlider(T("creator.valMin"), r.ValMin, 0, 1, "0.00", v => r.ValMin = v),
                RuleSlider(T("creator.valScale"), r.ValScale, 0.3f, 1.7f, "0.00", v => r.ValScale = v),
                RuleSlider(T("creator.satScale"), r.SatScale, 0.3f, 1.7f, "0.00", v => r.SatScale = v));

            body.IsVisible = active; // only the selected rule shows its sliders
            var card = new Border
            {
                Child = Ui.Column(6, head, body),
                Padding = new Thickness(10),
                CornerRadius = new CornerRadius(8),
                BorderThickness = new Thickness(1),
                BorderBrush = active ? Ui.Brush("GoldBrush") : Ui.Brush("BorderBrush"),
                Background = active ? Ui.Parse("#1FEFB656") : Brushes.Transparent,
            };
            if (!active)
            {
                card.Cursor = new Cursor(StandardCursorType.Hand);
                card.PointerPressed += (_, _) => { _activeRule = index; RebuildRules(); };
            }
            _rulesPanel.Children.Add(card);
        }
    }

    private Control RuleSlider(string label, float value, float min, float max, string fmt, Action<float> set)
    {
        var slider = new Slider { Minimum = min, Maximum = max, Value = value, Width = 210 };
        var readout = Ui.Text(value.ToString(fmt, CultureInfo.InvariantCulture), "mono faint", 11);
        slider.PropertyChanged += (_, e) =>
        {
            if (e.Property != RangeBase.ValueProperty) return;
            set((float)slider.Value);
            readout.Text = slider.Value.ToString(fmt, CultureInfo.InvariantCulture);
            QueueCreatorPreview();
        };
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("150,Auto,50"), ColumnSpacing = 8 };
        g.Children.Add(Ui.Text(label, "muted", 11.5));
        Grid.SetColumn(slider, 1); g.Children.Add(slider);
        Grid.SetColumn(readout, 2); g.Children.Add(readout);
        return g;
    }

    private static string HueHex(float hueDeg)
    {
        PaintMath.HsvToRgb(hueDeg / 360f, 0.75f, 0.85f, out float r, out float g, out float b);
        return $"{(int)(r * 255):X2}{(int)(g * 255):X2}{(int)(b * 255):X2}";
    }

    // =========================================================== preview

    private void QueueCreatorPreview()
    {
        _creatorDebounce.Stop();
        _creatorDebounce.Start();
    }

    private void OnCreatorTick(object sender, EventArgs e)
    {
        _creatorDebounce.Stop();
        RenderCreatorPreview();
    }

    private List<PaintMath.Rule> CreatorRules() => _cs.Rules.Select(r => r.ToRule()).ToList();

    private void RenderCreatorPreview()
    {
        if (_creatorPreview == null || _cs == null) return;
        _creatorPreview.Children.Clear();
        var rules = CreatorRules();
        foreach (var unit in FactionUnitsWithPortraits(_cs.Faction).Take(8))
        {
            var src = Ui.Image("units/" + unit.Image);
            var rgba = ToRgba(src, out int w, out int h);
            if (rgba == null) continue;
            var after = FromRgba(PaintMath.ApplyRules(rgba, rules), w, h);

            var before = new Image { Source = src, Width = 92, Height = 92, Stretch = Stretch.UniformToFill, Cursor = new Cursor(StandardCursorType.Cross) };
            ToolTip.SetTip(before, T("creator.pickTip"));
            before.PointerPressed += (_, e) =>
            {
                var p = e.GetPosition(before);
                int px = Math.Clamp((int)(p.X / before.Bounds.Width * w), 0, w - 1);
                int py = Math.Clamp((int)(p.Y / before.Bounds.Height * h), 0, h - 1);
                int i = (py * w + px) * 4;
                if (rgba[i + 3] < 16 || _activeRule < 0 || _activeRule >= _cs.Rules.Count) return;
                PaintMath.RgbToHsv(rgba[i] / 255f, rgba[i + 1] / 255f, rgba[i + 2] / 255f, out float hh, out float ss, out float vv);
                var r = _cs.Rules[_activeRule];
                r.Hue = (float)Math.Round(hh * 360f);
                r.SatMin = (float)Math.Round(Math.Max(0.05, ss * 0.5), 2);
                SetStatus(F("creator.picked", r.Hue, (int)(ss * 100), (int)(vv * 100), _activeRule + 1));
                RebuildRules();
                QueueCreatorPreview();
            };
            var pair = Ui.Row(3, Frame(before), Icons.Make(Icons.ArrowRight, 13, Ui.Brush("FaintBrush")), Frame(new Image { Source = after, Width = 92, Height = 92, Stretch = Stretch.UniformToFill }));
            var label = Ui.Text(unit.DisplayName(Lang), "muted", 10.5);
            label.MaxWidth = 200;
            label.TextTrimming = TextTrimming.CharacterEllipsis;
            var cell = Ui.Column(3, pair, label);
            cell.Margin = new Thickness(0, 0, 14, 10);
            _creatorPreview.Children.Add(cell);
        }

        _modelPreview.Children.Clear();
        foreach (var (name, (mr, mw, mh)) in _modelTextures)
        {
            var before = FromRgba(FlipRows(mr, mw, mh), mw, mh);
            var after = FromRgba(FlipRows(PaintMath.ApplyRules(mr, rules), mw, mh), mw, mh);
            _modelPreview.Children.Add(Ui.Column(3,
                Ui.Row(4, Frame(new Image { Source = before, Width = 230, Height = 230 }), Icons.Make(Icons.ArrowRight, 13, Ui.Brush("FaintBrush")),
                          Frame(new Image { Source = after, Width = 230, Height = 230 })),
                Ui.Text(name, "faint", 10.5)));
        }

        if (_badgePreview != null) _badgePreview.Source = RenderBadgePreview();
    }

    private static Border Frame(Control c) => new()
    {
        Child = c, CornerRadius = new CornerRadius(6), ClipToBounds = true, Background = Ui.Parse("#33000000"),
    };

    private static byte[] FlipRows(byte[] px, int w, int h)
    {
        var o = new byte[px.Length];
        int row = w * 4;
        for (int y = 0; y < h; y++) Buffer.BlockCopy(px, y * row, o, (h - 1 - y) * row, row);
        return o;
    }

    private Bitmap RenderBadgePreview()
    {
        if (_cs.BadgePath.Length == 0 || !File.Exists(_cs.BadgePath) || !BadgeAtlases.TryGetValue(_cs.Faction, out var atlas)) return null;
        try
        {
            _logoAtlas ??= Baker.DecodeTexture(_session.GameDir, _cs.Faction, atlas.textures[0], 1024);
            if (_logoAtlas == null) return null;
            var (lr, lw, lh) = _logoAtlas.Value;
            var copy = (byte[])lr.Clone();
            using var badge = new Bitmap(_cs.BadgePath);
            var stencil = FlipRows(ToRgba(badge, out int bw, out int bh), bw, bh);
            var r = atlas.rect;
            PaintMath.StampBadge(copy, lw, lh, r[0], r[1], r[2], r[3], stencil, bw, bh, 0.92f);

            // crop the badge area onto the primary armour colour, top-down for display
            int x0 = (int)(r[0] * lw), x1 = (int)(r[2] * lw), y0 = (int)(r[1] * lh), y1 = (int)(r[3] * lh);
            int cw = x1 - x0, ch = y1 - y0;
            var plate = Color.Parse("#" + (_cs.Rules.FirstOrDefault()?.To ?? "333333"));
            var outp = new byte[cw * ch * 4];
            for (int y = 0; y < ch; y++)
                for (int x = 0; x < cw; x++)
                {
                    int si = ((y0 + y) * lw + x0 + x) * 4, di = ((ch - 1 - y) * cw + x) * 4;
                    float a = copy[si + 3] / 255f;
                    outp[di] = (byte)(plate.R + (255 - plate.R) * a);
                    outp[di + 1] = (byte)(plate.G + (255 - plate.G) * a);
                    outp[di + 2] = (byte)(plate.B + (255 - plate.B) * a);
                    outp[di + 3] = 255;
                }
            return FromRgba(outp, cw, ch);
        }
        catch
        {
            return null;
        }
    }

    private async Task LoadModelTextures()
    {
        if (!_session.HasGame) { SetStatus(T("status.pickFolderFirst")); return; }
        var faction = _cs.Faction;
        var gameDir = _session.GameDir;
        SetStatus(T("creator.loadingModels"));
        var loaded = await Task.Run(() => Baker.SampleTextures(gameDir, faction, 3, 512));
        if (_cs.Faction != faction) return;
        _modelTextures.Clear();
        foreach (var (name, tex) in loaded) _modelTextures[name] = tex;
        SetStatus(loaded.Count > 0 ? F("creator.loadedModels", loaded.Count) : F("bake.noBundle", faction));
        RenderCreatorPreview();
    }

    // =========================================================== save

    private static string Slug(string name)
    {
        var chars = name.Trim().ToLowerInvariant().Select(c => char.IsLetterOrDigit(c) ? c : '-').ToArray();
        var s = string.Join("-", new string(chars).Split('-', StringSplitOptions.RemoveEmptyEntries));
        return s.Length == 0 ? "my-scheme" : s;
    }

    private string CreatorJson(bool withBadge)
    {
        var doc = new Dictionary<string, object>
        {
            ["id"] = Slug(_cs.Name),
            ["name"] = _cs.Name.Trim(),
            ["version"] = _cs.Version,
            ["author"] = _cs.Author.Trim(),
            ["description"] = _cs.Description.Trim(),
            ["faction"] = _cs.Faction,
            ["primary"] = _cs.Rules.FirstOrDefault()?.To ?? "FFFFFF",
            ["secondary"] = _cs.Rules.Skip(1).FirstOrDefault()?.To ?? "FFFFFF",
            ["rules"] = _cs.Rules.Select(r => new Dictionary<string, object>
            {
                ["hue"] = Math.Round(r.Hue, 1), ["width"] = Math.Round(r.Width, 1), ["feather"] = Math.Round(r.Feather, 1),
                ["satMin"] = Math.Round(r.SatMin, 3), ["valMin"] = Math.Round(r.ValMin, 3), ["valMax"] = Math.Round(r.ValMax, 3),
                ["to"] = r.To, ["satScale"] = Math.Round(r.SatScale, 3), ["valScale"] = Math.Round(r.ValScale, 3),
            }).ToList(),
        };
        if (withBadge && BadgeAtlases.TryGetValue(_cs.Faction, out var atlas))
            doc["badge"] = new Dictionary<string, object> { ["textures"] = atlas.textures, ["rect"] = atlas.rect, ["image"] = "badge.png" };
        return JsonSerializer.Serialize(doc, new JsonSerializerOptions { WriteIndented = true });
    }

    private bool HasBadge => _cs.BadgePath.Length > 0 && File.Exists(_cs.BadgePath) && BadgeAtlases.ContainsKey(_cs.Faction);

    private void SaveCreatedPack()
    {
        if (!_session.HasGame) { SetStatus(T("status.pickFolderFirst")); return; }
        try
        {
            var id = Slug(_cs.Name);
            var dir = Path.Combine(_session.UserPackRoot, id);
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "scheme.json"), CreatorJson(HasBadge));
            if (HasBadge && Path.GetFullPath(_cs.BadgePath) != Path.GetFullPath(Path.Combine(dir, "badge.png")))
                File.Copy(_cs.BadgePath, Path.Combine(dir, "badge.png"), true);
            SchemePack.Load(dir); // validate
            _session.RefreshPacks();
            _paintKey = _cs.Faction;
            _session.SetScheme(_cs.Faction, id);
            ShowPage(AppPage.Paint);
            SetStatus(F("creator.saved", _cs.Name, _cs.Faction));
        }
        catch (Exception ex)
        {
            SetStatus(F("creator.saveFailed", ex.Message));
        }
    }

    private async Task ExportCreatedPack()
    {
        try
        {
            var id = Slug(_cs.Name);
            var file = await StorageProvider.SaveFilePickerAsync(new FilePickerSaveOptions
            {
                Title = T("creator.export"),
                SuggestedFileName = $"scheme-{id}-v{_cs.Version}.zip",
                FileTypeChoices = new[] { new FilePickerFileType("Scheme pack") { Patterns = new[] { "*.zip" } } },
            });
            var path = file?.TryGetLocalPath();
            if (string.IsNullOrEmpty(path)) return;
            if (File.Exists(path)) File.Delete(path);
            using (var zip = ZipFile.Open(path, ZipArchiveMode.Create))
            {
                var e = zip.CreateEntry("scheme.json");
                using (var w = new StreamWriter(e.Open())) w.Write(CreatorJson(HasBadge));
                if (HasBadge) zip.CreateEntryFromFile(_cs.BadgePath, "badge.png");
            }
            SetStatus(F("creator.exported", path));
        }
        catch (Exception ex)
        {
            SetStatus(F("creator.saveFailed", ex.Message));
        }
    }
}
