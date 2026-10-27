using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using static Warpstorm.Configurator.Loc;

namespace Warpstorm.Configurator;

public enum AppPage { Units, Weapons, Paint, Changes, Settings, Help }

public partial class MainWindow : Window
{
    private Catalog _catalog = new();
    private EditSession _session;
    private AppPage _page = AppPage.Units;
    private bool _closingConfirmed;
    private bool _syncingLang;
    private string _gameLinkChip = "";
    private readonly Dictionary<AppPage, ToggleButton> _nav = new();
    private readonly Dictionary<AppPage, TextBlock> _navBadges = new();
    private readonly Dictionary<AppPage, TextBlock> _navLabels = new();
    private readonly DispatcherTimer _changeDebounce = new() { Interval = TimeSpan.FromMilliseconds(120) };
    private readonly DispatcherTimer _reloadWatch = new() { Interval = TimeSpan.FromMilliseconds(500) };
    private DateTime _reloadWatchStarted;
    private string _savedStatsStamp = "", _savedPaintStamp = "";

    /// <summary>Current UI/name language code.</summary>
    private static string Lang => Code;

    public static string AppVersion =>
        typeof(MainWindow).Assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion?.Split('+')[0]
        ?? "0.0.0";

    public MainWindow()
    {
        InitializeComponent();
        Title = $"Warpstorm Configurator {AppVersion}";
        Set(LoadPreference(), persist: false);

        SaveButton.Click += (_, _) => Save();
        RevertButton.Click += (_, _) => Revert();
        ImportButton.Click += async (_, _) => await Import();
        ExportButton.Click += async (_, _) => await Export();
        KeyDown += OnKeyDown;
        Closing += OnClosing;
        _changeDebounce.Tick += (_, _) => { _changeDebounce.Stop(); RefreshChrome(); };
        _reloadWatch.Tick += (_, _) => WatchGameReload();

        LangBox.ItemsSource = Languages.Select(l => l.native).ToList();
        LangBox.SelectionChanged += (_, _) =>
        {
            if (_syncingLang || LangBox.SelectedIndex < 0) return;
            SetLanguage(Languages[LangBox.SelectedIndex].code);
        };

        BuildNav();
        ApplyChromeText();
        Opened += (_, _) => Initialize();
    }

    private void Initialize(string gameDirOverride = null)
    {
        if (_session != null) return;
        _catalog = CatalogLoader.Load();
        _session = new EditSession(_catalog);
        _session.Changed += () => _changeDebounce.Start();

        var gameDir = gameDirOverride ?? GameLocator.Find();
        if (gameDir.Length > 0) OpenGame(gameDir);
        else
        {
            SetStatus(T("status.gameNotFound"));
            ShowPage(AppPage.Settings);
        }
        if (gameDir.Length > 0) ShowPage(AppPage.Units);
        RefreshChrome();
    }

    private void OpenGame(string gameDir)
    {
        var notes = _session.Open(gameDir);
        SetStatus(notes.Count > 0 ? string.Join(" · ", notes) : T("status.noSavedConfig"));
        _unitRows = null;
        _weaponRows = null;
        StartVerify();
    }

    // ------------------------------------------------------------- chrome

    private void BuildNav()
    {
        void Gap() => NavPanel.Children.Add(new Border { Height = 14 });

        void Add(AppPage page, string icon)
        {
            var badge = new TextBlock { FontSize = 12, FontWeight = FontWeight.SemiBold, Foreground = Ui.Brush("GoldBrush"), VerticalAlignment = VerticalAlignment.Center };
            var content = new Grid { ColumnDefinitions = new ColumnDefinitions("26,*,Auto") };
            content.Children.Add(Icons.Make(icon, 16));
            var l = new TextBlock { VerticalAlignment = VerticalAlignment.Center, TextTrimming = TextTrimming.CharacterEllipsis };
            Grid.SetColumn(l, 1);
            content.Children.Add(l);
            Grid.SetColumn(badge, 2);
            content.Children.Add(badge);

            var b = new ToggleButton { Content = content, HorizontalContentAlignment = HorizontalAlignment.Stretch };
            b.Classes.Add("nav");
            b.Click += (_, _) => ShowPage(page);
            NavPanel.Children.Add(b);
            _nav[page] = b;
            _navBadges[page] = badge;
            _navLabels[page] = l;
        }

        Add(AppPage.Units, Icons.Units);
        Add(AppPage.Weapons, Icons.Weapons);
        Add(AppPage.Paint, Icons.Paint);
        Gap();
        Add(AppPage.Changes, Icons.Changes);
        Add(AppPage.Settings, Icons.Settings);
        Add(AppPage.Help, Icons.Help);
    }

    /// <summary>Static chrome text; re-run when the language changes.</summary>
    private void ApplyChromeText()
    {
        AppTitle.Text = T("app.title");
        LangLabel.Data = Avalonia.Media.Geometry.Parse(Icons.Language);
        MoreButton.Content = Icons.Make(Icons.More, 16);
        ToolTip.SetTip(MoreButton, T("header.import") + " / " + T("header.export"));
        ToolTip.SetTip(LangLabel, T("header.language"));
        ToolTip.SetTip(LangBox, T("header.language"));
        ImportButton.Header = T("header.import");
        ExportButton.Header = T("header.export");
        ImportButton.Icon = Icons.Make(Icons.Import, 16);
        ExportButton.Icon = Icons.Make(Icons.Export, 16);
        RevertButton.Content = T("header.discard");
        ToolTip.SetTip(ImportButton, T("header.import.tip"));
        ToolTip.SetTip(ExportButton, T("header.export.tip"));
        ToolTip.SetTip(RevertButton, T("header.discard.tip"));
        ToolTip.SetTip(SaveButton, T("header.save.tip"));
        _navLabels[AppPage.Units].Text = T("nav.units");
        _navLabels[AppPage.Weapons].Text = T("nav.weapons");
        _navLabels[AppPage.Paint].Text = T("nav.paint");
        _navLabels[AppPage.Changes].Text = T("nav.changes");
        _navLabels[AppPage.Settings].Text = T("nav.settings");
        _navLabels[AppPage.Help].Text = T("nav.help");
        if (_session == null) SaveButton.Content = T("header.save");

        _syncingLang = true;
        LangBox.SelectedIndex = Array.FindIndex(Languages, l => l.code == Code);
        _syncingLang = false;
    }

    private void ShowPage(AppPage page)
    {
        _page = page;
        foreach (var (p, b) in _nav) b.IsChecked = p == page;
        if (_session == null) return;
        ContentHost.Content = page switch
        {
            AppPage.Units => BuildCatalogPage(false),
            AppPage.Weapons => BuildCatalogPage(true),
            AppPage.Paint => BuildPaintPage(),
            AppPage.Changes => BuildChangesPage(),
            AppPage.Settings => BuildSettingsPage(),
            _ => BuildHelpPage(),
        };
    }

    private void RefreshChrome()
    {
        if (_session == null) return;
        int unsaved = _session.UnsavedCount;
        SaveButton.Content = unsaved > 0 ? F("header.saveCount", unsaved) : T("header.saved");
        SaveButton.IsEnabled = _session.HasGame && unsaved > 0;
        RevertButton.IsVisible = unsaved > 0;

        _navBadges[AppPage.Units].Text = _session.UnitEdits.Count > 0 ? _session.UnitEdits.Count.ToString() : "";
        _navBadges[AppPage.Weapons].Text = _session.WeaponEdits.Count > 0 ? _session.WeaponEdits.Count.ToString() : "";
        _navBadges[AppPage.Paint].Text = _session.PaintCustomCount > 0 ? _session.PaintCustomCount.ToString() : "";
        _navBadges[AppPage.Changes].Text = unsaved > 0 ? unsaved.ToString() : "";

        // Only a state that needs attention earns a chip in the header.
        HeaderChips.Children.Clear();
        if (!_session.HasGame) HeaderChips.Children.Add(Ui.Chip(T("chip.noGame"), "bad"));

        // Game facts and hotkeys live in the status bar.
        string game = !_session.HasGame ? "" : F("chip.game", _session.GameVersion) + (_session.Verified ? "" : ", " + T("chip.reading"));
        HotkeyText.Text = (game.Length > 0 ? game + "    " : "") + HotkeySummary();
        if (_session.Verified) ToolTip.SetTip(HotkeyText, T("chip.verified"));
        NavFootnote.Text = "Warpstorm " + AppVersion;

        RefreshRowBadges();
        if (_page == AppPage.Changes) ShowPage(AppPage.Changes);
    }

    private string HotkeySummary()
    {
        string K(string id) => KeyNames.Name(_session.SettingValues.GetValueOrDefault(id));
        return F("status.hotkeys", K("warpstorm:General/ToggleKey"), K("warpstorm:General/ReloadKey"), K("armypainter:UI/ToggleKey"));
    }

    private void SetStatus(string text) => StatusText.Text = text;

    private void SetLanguage(string code)
    {
        Set(code);
        ApplyChromeText();
        if (_session == null) return;
        _unitRows = null;
        _weaponRows = null;
        RefreshChrome();
        ShowPage(_page);
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.S && e.KeyModifiers.HasFlag(KeyModifiers.Control))
        {
            Save();
            e.Handled = true;
        }
        else if (e.Key == Key.F && e.KeyModifiers.HasFlag(KeyModifiers.Control))
        {
            _searchBox?.Focus();
            e.Handled = true;
        }
    }

    // ---------------------------------------------------------- save etc.

    private bool Save()
    {
        if (_session == null) return false;
        if (!_session.HasGame)
        {
            SetStatus(T("status.pickFolderFirst"));
            ShowPage(AppPage.Settings);
            return false;
        }
        try
        {
            _session.Save();
            _savedStatsStamp = GameLink.Stamp(_session.StatsConfigPath);
            _savedPaintStamp = GameLink.Stamp(_session.PaintConfigPath);
            _gameLinkChip = "";
            if (GameLink.Running(_session.GameDir))
            {
                SetStatus(F("status.savedWaiting", _session.StatEditCount, _session.PaintCustomCount));
                _reloadWatchStarted = DateTime.UtcNow;
                _reloadWatch.Start();
            }
            else
            {
                SetStatus(F("status.savedNotRunning", _session.StatEditCount, _session.PaintCustomCount));
            }
            if (_session.BakeJobs().Count > 0) StartBake(true);   // pre-paint textures for the game
            return true;
        }
        catch (Exception ex)
        {
            SetStatus(F("status.saveFailed", ex.Message));
            return false;
        }
    }

    /// <summary>After a Save while the game runs: wait for the plugin to confirm it reloaded.</summary>
    private void WatchGameReload()
    {
        if (_session == null || !_session.HasGame) { _reloadWatch.Stop(); return; }
        var stats = GameLink.Read(GameLink.StatusPath(_session.GameDir));
        var paint = GameLink.Read(GameLink.PaintStatusPath(_session.GameDir));
        bool statsOk = stats != null && stats.ConfigStamp == _savedStatsStamp;
        bool paintOk = paint != null && paint.ConfigStamp == _savedPaintStamp;

        if (statsOk && paintOk)
        {
            _reloadWatch.Stop();
            string paintLine = paint.Active && paint.Faction.Length > 0
                ? F("status.reloaded.paint", paint.Faction, paint.Renderers, paint.Portraits)
                : T("status.reloaded.paintIdle");
            SetStatus(F("status.reloaded", stats.Edits) + "  " + paintLine + "  " + T("status.reloaded.battleNote"));
            _gameLinkChip = T("chip.gameReloaded");
            RefreshChrome();
            return;
        }

        if ((DateTime.UtcNow - _reloadWatchStarted).TotalSeconds > 8)
        {
            _reloadWatch.Stop();
            string key = KeyNames.Name(_session.SettingValues.GetValueOrDefault("warpstorm:General/ReloadKey"));
            SetStatus(GameLink.AnyStatusFileExists(_session.GameDir)
                ? F("status.reloadNoAck", key)
                : F("status.reloadNoAck.old", key));
        }
    }

    private void Revert()
    {
        _session?.Revert();
        _unitRows = null;
        _weaponRows = null;
        ShowPage(_page);
        SetStatus(T("status.discarded"));
    }

    private async Task Export()
    {
        try
        {
            var file = await StorageProvider.SaveFilePickerAsync(new FilePickerSaveOptions
            {
                Title = T("export.title"),
                SuggestedFileName = "warpstorm-export.json",
                FileTypeChoices = new[] { new FilePickerFileType("JSON") { Patterns = new[] { "*.json" } } },
            });
            var path = file?.TryGetLocalPath();
            if (string.IsNullOrEmpty(path)) return;
            var (units, weapons) = _session.CleanEdits();
            ConfigStore.Save(path, _session.GameVersion, _session.Enabled, units, weapons);
            SetStatus(F("status.exported", path));
        }
        catch (Exception ex)
        {
            SetStatus(F("status.exportFailed", ex.Message));
        }
    }

    private async Task Import()
    {
        try
        {
            var files = await StorageProvider.OpenFilePickerAsync(new FilePickerOpenOptions
            {
                Title = T("import.title"),
                AllowMultiple = false,
                FileTypeFilter = new[] { new FilePickerFileType("JSON") { Patterns = new[] { "*.json" } } },
            });
            var path = files.FirstOrDefault()?.TryGetLocalPath();
            if (string.IsNullOrEmpty(path)) return;
            var imported = ConfigStore.Import(path);
            _session.ApplyImport(imported);
            ShowPage(_page);
            SetStatus(F("status.imported", imported.Fields));
        }
        catch (Exception ex)
        {
            SetStatus(F("status.importFailed", ex.Message));
        }
    }

    private async void OnClosing(object sender, WindowClosingEventArgs e)
    {
        if (_closingConfirmed || _session == null || _session.UnsavedCount == 0) return;
        e.Cancel = true;
        var choice = await Dialog.Ask(this, T("dialog.unsaved.title"),
            F("dialog.unsaved.body", _session.UnsavedCount),
            T("dialog.unsaved.save"), T("dialog.unsaved.discard"), T("common.cancel"));
        if (choice == 2) return;
        if (choice == 0 && !Save()) return;
        _closingConfirmed = true;
        Close();
    }

    // ------------------------------------------------------------- verify

    private void StartVerify()
    {
        if (!_session.HasGame) return;
        VerifyBar.IsVisible = true;
        var gameDir = _session.GameDir;
        SetStatus(T("status.verifying"));

        Task.Run(() => BundleReader.Read(gameDir, _ => { }))
            .ContinueWith(t => Dispatcher.UIThread.Post(() =>
            {
                VerifyBar.IsVisible = false;
                if (_session.GameDir != gameDir) return; // folder changed meanwhile
                if (t.IsFaulted)
                {
                    SetStatus(F("status.verifyFailed", t.Exception?.GetBaseException().Message));
                    return;
                }
                _session.UnitOriginals = t.Result.Units;
                _session.WeaponOriginals = t.Result.Weapons;
                _session.Verified = true;
                SetStatus(F("status.verified", t.Result.Units.Count, t.Result.Weapons.Count, t.Result.Source));
                if (_page is AppPage.Units or AppPage.Weapons) RenderDetail();
                RefreshChrome();
            }));
    }

    internal async void BrowseGameFolder()
    {
        var folders = await StorageProvider.OpenFolderPickerAsync(new FolderPickerOpenOptions
        {
            Title = T("browse.title"),
            AllowMultiple = false,
        });
        var path = folders.FirstOrDefault()?.TryGetLocalPath();
        if (string.IsNullOrEmpty(path)) return;
        if (!GameLocator.IsGameDir(path))
        {
            SetStatus(F("status.notGameFolder", GameLocator.ExeName));
            return;
        }
        if (_session.UnsavedCount > 0)
        {
            var choice = await Dialog.Ask(this, T("dialog.switch.title"), T("dialog.switch.body"), T("dialog.switch.ok"), T("common.cancel"));
            if (choice != 0) return;
        }
        OpenGame(path);
        ShowPage(AppPage.Units);
        RefreshChrome();
    }
}
