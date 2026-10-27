using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Controls.Templates;
using Avalonia.Data;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;

namespace Warpstorm.Configurator;

/// <summary>One row in the unit/weapon list (bindable so recycled rows update).</summary>
public sealed class RowVm : INotifyPropertyChanged
{
    public CatalogItem Item { get; init; }
    public string Title { get; init; } = "";
    public string Secondary { get; init; } = "";
    public string Meta { get; init; } = "";
    public string PointsLabel { get; init; } = "";
    public Bitmap Thumb { get; init; }
    public IBrush Tier { get; init; }
    public Thickness ThumbPadding { get; init; }
    public bool HasSecondary => Secondary.Length > 0;

    private string _points = "";
    public string Points { get => _points; set => Set(ref _points, value, nameof(Points)); }

    private string _badge = "";
    public string Badge { get => _badge; set { Set(ref _badge, value, nameof(Badge)); Raise(nameof(HasBadge)); } }
    public bool HasBadge => _badge.Length > 0;

    public event PropertyChangedEventHandler PropertyChanged;
    private void Raise(string name) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    private void Set(ref string field, string value, string name)
    {
        if (field == value) return;
        field = value;
        Raise(name);
    }
}

public partial class MainWindow
{
    private List<RowVm> _unitRows;
    private List<RowVm> _weaponRows;
    private ListBox _list;
    private TextBox _searchBox;
    private TextBlock _countText;
    private StackPanel _detail;
    private Border _bulkPanel;
    private CatalogItem _selectedUnit;
    private CatalogItem _selectedWeapon;
    private readonly List<Action> _detailRefreshers = new();

    private string _query = "";
    private int _factionFilter = -1;
    private string _roleFilter = "";
    private int _typeFilter; // weapons: 0 all, 1 ranged, 2 melee
    private bool _editedOnly;
    private string _fieldQuery = "";
    private bool _changedFieldsOnly;

    private bool CurrentIsWeapon => _page == AppPage.Weapons;
    private CatalogItem Selected => CurrentIsWeapon ? _selectedWeapon : _selectedUnit;

    // =============================================================== page

    private Control BuildCatalogPage(bool weapon)
    {
        var grid = new Grid { ColumnDefinitions = new ColumnDefinitions("380,*"), ColumnSpacing = 14 };
        grid.Children.Add(BuildListPane(weapon));
        var right = BuildDetailPane();
        Grid.SetColumn(right, 1);
        grid.Children.Add(right);
        ApplyFilter();
        RenderDetail();
        return grid;
    }

    private Control BuildListPane(bool weapon)
    {
        _searchBox = new TextBox
        {
            Text = _query,
            PlaceholderText = weapon ? Loc.T("list.searchWeapons") : Loc.T("list.searchUnits"),
        };
        _searchBox.TextChanged += (_, _) => { _query = _searchBox.Text ?? ""; ApplyFilter(); };

        var filters = new StackPanel { Spacing = 6 };
        if (!weapon)
        {
            var factions = new List<FactionOption> { new() { Id = -1, Name = Loc.T("list.allFactions") } };
            factions.AddRange(_catalog.Factions);
            var factionBox = new ComboBox
            {
                ItemsSource = factions.Select(f => f.Id < 0 ? f.Name : f.DisplayName(Lang)).ToList(),
                SelectedIndex = Math.Max(0, factions.FindIndex(f => f.Id == _factionFilter)),
                HorizontalAlignment = HorizontalAlignment.Stretch,
            };
            factionBox.SelectionChanged += (_, _) =>
            {
                _factionFilter = factionBox.SelectedIndex <= 0 ? -1 : factions[factionBox.SelectedIndex].Id;
                ApplyFilter();
            };

            var roles = new List<string> { "" };
            roles.AddRange(_catalog.Roles);
            var roleBox = new ComboBox
            {
                ItemsSource = roles.Select(r => r.Length == 0 ? Loc.T("list.allRoles") : _catalog.RoleName(r, Lang)).ToList(),
                SelectedIndex = Math.Max(0, roles.IndexOf(_roleFilter)),
                HorizontalAlignment = HorizontalAlignment.Stretch,
            };
            roleBox.SelectionChanged += (_, _) =>
            {
                _roleFilter = roleBox.SelectedIndex <= 0 ? "" : roles[roleBox.SelectedIndex];
                ApplyFilter();
            };

            var g = new Grid { ColumnDefinitions = new ColumnDefinitions("3*,2*"), ColumnSpacing = 6 };
            g.Children.Add(factionBox);
            Grid.SetColumn(roleBox, 1);
            g.Children.Add(roleBox);
            filters.Children.Add(g);
        }

        var pills = new WrapPanel();
        if (weapon)
        {
            string[] types = { Loc.T("list.typeAll"), Loc.T("common.ranged"), Loc.T("common.melee") };
            var buttons = new List<ToggleButton>();
            for (int i = 0; i < types.Length; i++)
            {
                int index = i;
                var b = new ToggleButton { Content = types[i], IsChecked = _typeFilter == i, Margin = new Thickness(0, 0, 6, 0) };
                b.Classes.Add("pill");
                b.Click += (_, _) =>
                {
                    _typeFilter = index;
                    foreach (var other in buttons) other.IsChecked = other == b;
                    ApplyFilter();
                };
                buttons.Add(b);
                pills.Children.Add(b);
            }
        }
        var edited = new ToggleButton { Content = Ui.Row(5, Icons.Make(Icons.Edit, 12), new TextBlock { Text = Loc.T("list.editedOnly") }), IsChecked = _editedOnly };
        edited.Classes.Add("pill");
        edited.Click += (_, _) => { _editedOnly = edited.IsChecked == true; ApplyFilter(); };
        pills.Children.Add(edited);
        filters.Children.Add(pills);

        _countText = new TextBlock { Classes = { "faint" }, FontSize = 11, VerticalAlignment = VerticalAlignment.Center };
        var bulkButton = new Button { Content = Loc.T("bulk.open"), Classes = { "ghost" }, Padding = new Thickness(10, 3), FontSize = 12 };
        ToolTip.SetTip(bulkButton, Loc.T("bulk.open.tip"));
        var countRow = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto") };
        countRow.Children.Add(_countText);
        Grid.SetColumn(bulkButton, 1);
        countRow.Children.Add(bulkButton);

        _bulkPanel = BuildBulkPanel(weapon);
        _bulkPanel.IsVisible = false;
        bulkButton.Click += (_, _) => _bulkPanel.IsVisible = !_bulkPanel.IsVisible;

        _list = new ListBox
        {
            Classes = { "catalog" },
            SelectionMode = SelectionMode.Single,
            ItemTemplate = new FuncDataTemplate<RowVm>((_, _) => BuildRowTemplate(), true),
            Margin = new Thickness(0, 8, 0, 0),
        };
        _list.SelectionChanged += (_, _) =>
        {
            if (_list.SelectedItem is not RowVm vm) return;
            if (vm.Item.IsWeapon) _selectedWeapon = vm.Item; else _selectedUnit = vm.Item;
            RenderDetail();
        };

        var top = Ui.Column(6, _searchBox, filters, countRow, _bulkPanel);
        var dock = new DockPanel();
        DockPanel.SetDock(top, Dock.Top);
        dock.Children.Add(top);
        dock.Children.Add(_list);
        return dock;
    }

    private static Control BuildRowTemplate()
    {
        var thumbImage = new Image { Stretch = Stretch.UniformToFill, VerticalAlignment = VerticalAlignment.Top };
        thumbImage[!Image.SourceProperty] = new Binding(nameof(RowVm.Thumb));
        var thumb = new Border
        {
            Width = 40,
            Height = 40,
            CornerRadius = new CornerRadius(6),
            ClipToBounds = true,
            BorderBrush = Ui.Parse("#40000000"),
            BorderThickness = new Thickness(1),
            Child = thumbImage,
        };
        thumb[!Border.BackgroundProperty] = new Binding(nameof(RowVm.Tier));
        thumb[!Border.PaddingProperty] = new Binding(nameof(RowVm.ThumbPadding));

        var title = new TextBlock { FontSize = 12.5, FontWeight = FontWeight.SemiBold, TextTrimming = TextTrimming.CharacterEllipsis };
        title[!TextBlock.TextProperty] = new Binding(nameof(RowVm.Title));
        var secondary = new TextBlock { FontSize = 10.5, Classes = { "muted" }, TextTrimming = TextTrimming.CharacterEllipsis };
        secondary[!TextBlock.TextProperty] = new Binding(nameof(RowVm.Secondary));
        secondary[!Visual.IsVisibleProperty] = new Binding(nameof(RowVm.HasSecondary));
        var meta = new TextBlock { FontSize = 10, Classes = { "faint" }, TextTrimming = TextTrimming.CharacterEllipsis };
        meta[!TextBlock.TextProperty] = new Binding(nameof(RowVm.Meta));

        var badgeText = new TextBlock { FontSize = 11, FontWeight = FontWeight.SemiBold, Foreground = Ui.Parse("#1B1206") };
        badgeText[!TextBlock.TextProperty] = new Binding(nameof(RowVm.Badge));
        var badge = new Border
        {
            Background = Ui.Brush("GoldBrush"),
            CornerRadius = new CornerRadius(999),
            Padding = new Thickness(6, 0),
            VerticalAlignment = VerticalAlignment.Center,
            Child = Ui.Row(3, Icons.Make(Icons.Edit, 10, Ui.Parse("#1B1206")), badgeText),
        };
        badge[!Visual.IsVisibleProperty] = new Binding(nameof(RowVm.HasBadge));
        ToolTip.SetTip(badge, Loc.T("list.editedFields"));

        var ptsLabel = new TextBlock { FontSize = 8, Classes = { "faint" }, HorizontalAlignment = HorizontalAlignment.Right };
        ptsLabel[!TextBlock.TextProperty] = new Binding(nameof(RowVm.PointsLabel));
        var pts = new TextBlock { FontSize = 13, FontWeight = FontWeight.Black, Foreground = Ui.Brush("GoldBrush"), HorizontalAlignment = HorizontalAlignment.Right };
        pts[!TextBlock.TextProperty] = new Binding(nameof(RowVm.Points));

        var grid = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*,Auto,Auto"), ColumnSpacing = 10, Margin = new Thickness(8, 6) };
        grid.Children.Add(thumb);
        var text = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Spacing = 1, Children = { title, secondary, meta } };
        Grid.SetColumn(text, 1);
        grid.Children.Add(text);
        Grid.SetColumn(badge, 2);
        grid.Children.Add(badge);
        var right = new StackPanel { VerticalAlignment = VerticalAlignment.Center, Children = { ptsLabel, pts } };
        Grid.SetColumn(right, 3);
        grid.Children.Add(right);
        return grid;
    }

    private List<RowVm> Rows(bool weapon)
    {
        if (weapon) return _weaponRows ??= _catalog.Weapons.Select(MakeRow).ToList();
        return _unitRows ??= _catalog.Units.Select(MakeRow).ToList();
    }

    private RowVm MakeRow(CatalogItem item)
    {
        var faction = _catalog.Factions.FirstOrDefault(f => f.Id == item.FactionId);
        string factionName = faction?.DisplayName(Lang) ?? item.Faction;
        var vm = new RowVm
        {
            Item = item,
            Title = item.DisplayName(Lang),
            Secondary = item.SecondaryName(Lang),
            Meta = item.IsWeapon
                ? Loc.List(Loc.T(item.IsMelee ? "common.melee" : "common.ranged"), Loc.F("detail.usedBy", item.UsedBy.Count))
                : Loc.List(factionName, _catalog.RoleName(item.Role, Lang)),
            PointsLabel = Loc.T(item.IsWeapon ? "tile.dmg" : "list.pts").ToUpperInvariant(),
            Thumb = Ui.Portrait(item),
            Tier = item.IsWeapon ? Ui.Parse("#4D000000") : Ui.Parse(Ui.TierColor(item.Role, item.RoleColor)),
            ThumbPadding = item.IsWeapon ? new Thickness(4) : new Thickness(0),
        };
        UpdateRow(vm);
        return vm;
    }

    private void UpdateRow(RowVm vm)
    {
        int n = _session.EditCount(vm.Item);
        vm.Badge = n > 0 ? n.ToString() : "";
        vm.Points = _session.Effective(vm.Item, vm.Item.IsWeapon ? "Damage" : "PointCost") ?? "";
    }

    private void RefreshRowBadges()
    {
        if (_unitRows != null) foreach (var r in _unitRows) UpdateRow(r);
        if (_weaponRows != null) foreach (var r in _weaponRows) UpdateRow(r);
    }

    private void ApplyFilter()
    {
        if (_list == null) return;
        bool weapon = CurrentIsWeapon;
        var q = _query.Trim();
        IEnumerable<RowVm> rows = Rows(weapon);
        if (!weapon && _factionFilter >= 0) rows = rows.Where(r => r.Item.FactionId == _factionFilter);
        if (!weapon && _roleFilter.Length > 0) rows = rows.Where(r => r.Item.Role == _roleFilter);
        if (weapon && _typeFilter == 1) rows = rows.Where(r => !r.Item.IsMelee);
        if (weapon && _typeFilter == 2) rows = rows.Where(r => r.Item.IsMelee);
        if (_editedOnly) rows = rows.Where(r => _session.IsEdited(r.Item));
        if (q.Length > 0)
            rows = rows.Where(r =>
                r.Item.NameMatches(q) || r.Item.Id == q);

        var list = rows.ToList();
        _list.ItemsSource = list;
        var sel = list.FirstOrDefault(r => r.Item == Selected);
        if (sel != null) _list.SelectedItem = sel;
        int total = Rows(weapon).Count;
        int edited = Rows(weapon).Count(r => _session.IsEdited(r.Item));
        _countText.Text = Loc.F(weapon ? "list.countWeapons" : "list.countUnits", list.Count, total, edited);
    }

    private List<CatalogItem> FilteredItems()
        => (_list?.ItemsSource as IEnumerable<RowVm>)?.Select(r => r.Item).ToList() ?? new List<CatalogItem>();

    /// <summary>Jumps to a unit or weapon (from a loadout / used-by link or the Changes page).</summary>
    private void Navigate(CatalogItem item)
    {
        if (item == null) return;
        if (item.IsWeapon) _selectedWeapon = item; else _selectedUnit = item;
        _query = "";
        _editedOnly = false;
        _factionFilter = -1;
        _roleFilter = "";
        _typeFilter = 0;
        ShowPage(item.IsWeapon ? AppPage.Weapons : AppPage.Units);
        var row = (_list.ItemsSource as IEnumerable<RowVm>)?.FirstOrDefault(r => r.Item == item);
        if (row != null)
        {
            _list.SelectedItem = row;
            _list.ScrollIntoView(row);
        }
    }

    // ============================================================= detail

    private Control BuildDetailPane()
    {
        var fieldSearch = new TextBox { Text = _fieldQuery, PlaceholderText = Loc.T("detail.findStat"), Width = 240 };
        fieldSearch.TextChanged += (_, _) => { _fieldQuery = fieldSearch.Text ?? ""; RenderDetail(); };
        var changedOnly = new ToggleButton { Content = Loc.T("detail.changedOnly"), IsChecked = _changedFieldsOnly };
        changedOnly.Classes.Add("pill");
        changedOnly.Click += (_, _) => { _changedFieldsOnly = changedOnly.IsChecked == true; RenderDetail(); };

        var bar = Ui.Row(8, fieldSearch, changedOnly);
        bar.Margin = new Thickness(0, 0, 0, 10);

        _detail = new StackPanel { Spacing = 12, Margin = new Thickness(0, 0, 12, 12) };
        var dock = new DockPanel();
        DockPanel.SetDock(bar, Dock.Top);
        dock.Children.Add(bar);
        dock.Children.Add(new ScrollViewer { Content = _detail });
        return dock;
    }

    private void RenderDetail()
    {
        if (_detail == null) return;
        _detail.Children.Clear();
        _detailRefreshers.Clear();

        var item = Selected;
        if (item == null)
        {
            _detail.Children.Add(Ui.Surface(Ui.Column(6,
                Ui.Text(Loc.T(CurrentIsWeapon ? "detail.pickWeapon" : "detail.pickUnit"), null, 16, FontWeight.Bold),
                Ui.Text(Loc.T("detail.pickHint"), "muted"))));
            return;
        }

        _detail.Children.Add(BuildDetailHeader(item));

        var fields = item.IsWeapon ? _catalog.Fields.Weapon : _catalog.Fields.Unit;
        var q = _fieldQuery.Trim();
        var visible = fields.Where(f =>
                (q.Length == 0 || f.Label.Contains(q, StringComparison.OrdinalIgnoreCase) ||
                 Loc.Field(f, item.IsWeapon).Contains(q, StringComparison.OrdinalIgnoreCase) ||
                 f.Key.Contains(q, StringComparison.OrdinalIgnoreCase) || f.Group.Contains(q, StringComparison.OrdinalIgnoreCase)) &&
                (!_changedFieldsOnly || _session.Edit(item, f.Key) != null))
            .ToList();

        if (visible.Count == 0)
            _detail.Children.Add(Ui.Text(Loc.T(_changedFieldsOnly ? "detail.noChanged" : "detail.noMatch"), "muted"));

        foreach (var g in visible.GroupBy(f => f.Group))
            _detail.Children.Add(BuildGroupCard(item, g.Key, g.ToList()));
    }

    private Control BuildDetailHeader(CatalogItem item)
    {
        var portrait = Ui.PortraitBox(item, 112);

        var name = Ui.Text(item.DisplayName(Lang), "heading", 26);
        name.TextWrapping = TextWrapping.Wrap;
        var faction = _catalog.Factions.FirstOrDefault(f => f.Id == item.FactionId);
        var chips = new WrapPanel();
        void ChipAdd(Control c) { c.Margin = new Thickness(0, 0, 6, 4); chips.Children.Add(c); }
        if (item.IsWeapon)
        {
            ChipAdd(Ui.Chip(Loc.T(item.IsMelee ? "common.melee" : "common.ranged")));
        }
        else
        {
            ChipAdd(Ui.Chip(faction?.DisplayName(Lang) ?? item.Faction));
            var role = Ui.Chip(_catalog.RoleName(item.Role, Lang));
            role.BorderBrush = Ui.Parse(Ui.TierColor(item.Role, item.RoleColor));
            ChipAdd(role);
        }
        var facts = Ui.Text(Loc.List(item.Members > 1 ? Loc.F("detail.models", item.Members) : "", Loc.F("detail.id", item.Id),
                                     _session.Verified ? "" : Loc.T("detail.catalogOriginals")), "faint", 12);

        var titleBlock = Ui.Column(4, name,
            item.SecondaryName(Lang).Length > 0 ? Ui.Text(item.SecondaryName(Lang), "muted", 13) : null,
            chips, facts);

        // Points (units) / damage (weapons), with the original struck through when edited.
        string key = item.IsWeapon ? "Damage" : "PointCost";
        var bigLabel = Ui.Text(Loc.T(item.IsWeapon ? "detail.bigDamage" : "detail.bigPoints"), "label");
        bigLabel.HorizontalAlignment = HorizontalAlignment.Right;
        var big = Ui.Text("", "heading", 36);
        big.Foreground = Ui.Brush("GoldBrush");
        big.HorizontalAlignment = HorizontalAlignment.Right;
        var was = Ui.Text("", "faint", 11);
        was.HorizontalAlignment = HorizontalAlignment.Right;
        was.TextDecorations = TextDecorations.Strikethrough;
        var reset = Ui.IconTextButton(Icons.Reset, Loc.T("detail.resetAll"), () =>
        {
            _session.ClearEdits(item);
            RenderDetail();
        }, "ghost", Loc.T("detail.resetAll.tip"));
        reset.HorizontalAlignment = HorizontalAlignment.Right;
        reset.Margin = new Thickness(0, 6, 0, 0);
        var bigBlock = Ui.Column(0, bigLabel, big, was, reset);

        void RefreshBig()
        {
            big.Text = _session.Effective(item, key) ?? "—";
            var e = _session.Edit(item, key);
            was.Text = e != null ? Loc.F("detail.was", _session.Original(item, key) ?? "?") : "";
            reset.IsVisible = _session.IsEdited(item);
        }
        RefreshBig();
        _detailRefreshers.Add(RefreshBig);

        var top = new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*,Auto"), ColumnSpacing = 16 };
        top.Children.Add(portrait);
        Grid.SetColumn(titleBlock, 1);
        top.Children.Add(titleBlock);
        Grid.SetColumn(bigBlock, 2);
        top.Children.Add(bigBlock);

        var body = Ui.Column(14, top, BuildStatTiles(item), item.IsWeapon ? BuildUsedBy(item) : BuildLoadout(item));
        return Ui.Gilded(body);
    }

    private Control BuildStatTiles(CatalogItem item)
    {
        var specs = item.IsWeapon
            ? new (string label, string color, string icon, Func<string> value, string[] keys)[]
            {
                (Loc.T("tile.dmg"), "#C9A227", "", () => V(item, "Damage"), new[] { "Damage" }),
                (Loc.T("tile.attacks"), "#B6ACA1", "", () => V(item, "Attacks"), new[] { "Attacks" }),
                (Loc.T("tile.accuracy"), "#6299B8", "", () => V(item, "Accuracy") + "%", new[] { "Accuracy" }),
                (Loc.T("tile.armourPen"), "#CC6161", "", () => V(item, "ArmourPenetration"), new[] { "ArmourPenetration" }),
                (Loc.T("tile.range"), "#9F895A", "", () => $"{V(item, "MinimumRange")}–{V(item, "MaximumRange")}", new[] { "MinimumRange", "MaximumRange" }),
                (Loc.T("tile.apCost"), "#8F5B36", "ui/stat-ap", () => V(item, "APCost"), new[] { "APCost" }),
            }
            : new (string label, string color, string icon, Func<string> value, string[] keys)[]
            {
                (Loc.T("tile.hp"), "#39904B", "ui/stat-health", () => item.Members > 1 ? $"{V(item, "MaxHealth")}×{item.Members}" : V(item, "MaxHealth"), new[] { "MaxHealth" }),
                (Loc.T("tile.ap"), "#8F5B36", "ui/stat-ap", () => V(item, "MaxActionPoints"), new[] { "MaxActionPoints" }),
                (Loc.T("tile.mp"), "#2662AA", "ui/stat-movement", () => V(item, "MaxMovementPoints"), new[] { "MaxMovementPoints" }),
                (Loc.T("tile.armor"), "#6299B8", "ui/stat-armor", () => V(item, "ArmorProfile") == "1" ? V(item, "ArmorFront") : V(item, "SingularArmor"),
                    new[] { "SingularArmor", "ArmorFront", "ArmorProfile" }),
                (Loc.T("tile.dodge"), "#9F895A", "ui/stat-evasion", () => V(item, "Evasion"), new[] { "Evasion" }),
                (Loc.T("tile.meleeAcc"), "#B6ACA1", "", () => V(item, "MeleeAccuracy") + "%", new[] { "MeleeAccuracy" }),
            };

        var grid = new UniformGrid { Columns = specs.Length };
        foreach (var s in specs)
        {
            var label = Ui.Row(3,
                s.icon.Length > 0 ? Ui.TintedIcon(s.icon, s.color, 12) : null,
                new TextBlock { Text = s.label.ToUpperInvariant(), FontSize = 9.5, FontWeight = FontWeight.Bold, Foreground = Ui.Parse(s.color), LetterSpacing = 0.6 });
            label.HorizontalAlignment = HorizontalAlignment.Center;
            var value = new TextBlock { FontSize = 17, FontWeight = FontWeight.Bold, HorizontalAlignment = HorizontalAlignment.Center };
            var tile = new Border { Child = Ui.Column(2, label, value), Margin = new Thickness(0, 0, 6, 0) };
            tile.Classes.Add("tile");
            var keys = s.keys;
            var valueFn = s.value;
            void Refresh()
            {
                value.Text = valueFn();
                bool modified = keys.Any(k => _session.Edit(item, k) != null);
                tile.Classes.Set("modified", modified);
                ToolTip.SetTip(tile, modified ? Loc.F("tile.editedTip", string.Join(", ", keys.Select(k => $"{k} {_session.Original(item, k) ?? "?"}"))) : null);
            }
            Refresh();
            _detailRefreshers.Add(Refresh);
            grid.Children.Add(tile);
        }
        return grid;
    }

    private string V(CatalogItem item, string key) => _session.Effective(item, key) ?? "—";

    private Control BuildLoadout(CatalogItem unit)
    {
        if (unit.WeaponSlots.Count == 0) return null;
        var wrap = new WrapPanel();
        foreach (var slot in unit.WeaponSlots)
        {
            var group = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 4 };
            for (int i = 0; i < slot.Count; i++)
            {
                if (i > 0) group.Children.Add(Ui.Text("/", "faint", 13, FontWeight.Bold));
                group.Children.Add(WeaponLink(slot[i]));
            }
            var box = new Border
            {
                Child = group,
                Padding = new Thickness(4),
                Margin = new Thickness(0, 0, 8, 6),
                CornerRadius = new CornerRadius(6),
                BorderThickness = new Thickness(slot.Count > 1 ? 1 : 0),
                BorderBrush = Ui.Brush("GoldDimBrush"),
                Background = slot.Count > 1 ? Ui.Parse("#40000000") : Brushes.Transparent,
            };
            if (slot.Count > 1) ToolTip.SetTip(box, Loc.T("detail.chooseOne"));
            wrap.Children.Add(box);
        }
        var title = Ui.Text(Loc.T("detail.loadout"), "label");
        ToolTip.SetTip(title, Loc.T("detail.loadout.hint"));
        return Ui.Column(4, title, wrap);
    }

    private Control WeaponLink(WeaponSlotOption option)
    {
        _catalog.WeaponById.TryGetValue(option.WeaponId, out var weapon);
        var name = weapon?.DisplayName(Lang) ?? option.Name;
        var content = Ui.Row(6,
            Ui.PortraitBox(weapon, 30),
            Ui.Column(0,
                Ui.Text(name, null, 12, FontWeight.SemiBold),
                option.PointCost > 0 ? Ui.Text(Loc.F("detail.plusPts", option.PointCost), "faint", 10) : null));
        var b = new Button { Content = content, Classes = { "ghost" }, Padding = new Thickness(4, 3, 10, 3), IsEnabled = weapon != null };
        if (weapon != null && _session.IsEdited(weapon))
            b.BorderBrush = Ui.Brush("GoldBrush");
        b.Click += (_, _) => Navigate(weapon);
        return b;
    }

    private Control BuildUsedBy(CatalogItem weapon)
    {
        if (weapon.UsedBy.Count == 0)
            return Ui.Text(Loc.T("detail.usedByNone"), "faint", 11);
        var wrap = new WrapPanel();
        foreach (var unit in weapon.UsedBy.OrderBy(u => u.Name))
        {
            var b = new Button
            {
                Content = Ui.Row(6, Ui.PortraitBox(unit, 26), Ui.Text(unit.DisplayName(Lang), null, 12)),
                Classes = { "ghost" },
                Padding = new Thickness(3, 2, 10, 2),
                Margin = new Thickness(0, 0, 6, 6),
            };
            b.Click += (_, _) => Navigate(unit);
            wrap.Children.Add(b);
        }
        return Ui.Column(4,
            Ui.Text(Loc.F("detail.usedBy", weapon.UsedBy.Count) + ". " + Loc.T("detail.usedBy.hint"), "label"),
            wrap);
    }

    // ============================================================ fields

    private Control BuildGroupCard(CatalogItem item, string group, List<FieldDef> fields)
    {
        var rows = new StackPanel { Spacing = 2 };
        var resetGroup = Ui.IconTextButton(Icons.Reset, Loc.T("detail.resetGroup"), () =>
        {
            foreach (var f in fields) _session.SetEdit(item, f.Key, null);
            RenderDetail();
        }, "ghost");
        resetGroup.Padding = new Thickness(8, 1);
        resetGroup.FontSize = 11;
        void RefreshReset() => resetGroup.IsVisible = fields.Any(f => _session.Edit(item, f.Key) != null);
        RefreshReset();
        _detailRefreshers.Add(RefreshReset);

        var title = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(0, 0, 0, 6) };
        title.Children.Add(Ui.Text(Loc.Group(group), "groupTitle"));
        Grid.SetColumn(resetGroup, 1);
        title.Children.Add(resetGroup);

        var header = new Grid { ColumnDefinitions = new ColumnDefinitions("*,110,220,70,28"), ColumnSpacing = 6, Margin = new Thickness(11, 0, 6, 2) };
        var o = Ui.Text(Loc.T("detail.colOriginal"), "label"); Grid.SetColumn(o, 1); header.Children.Add(o);
        var n = Ui.Text(Loc.T("detail.colNew"), "label"); Grid.SetColumn(n, 2); header.Children.Add(n);

        rows.Children.Add(title);
        rows.Children.Add(header);
        foreach (var f in fields) rows.Children.Add(BuildFieldRow(item, f));
        return Ui.Surface(rows, new Thickness(0, 14, 0, 4));
    }

    private Control BuildFieldRow(CatalogItem item, FieldDef field)
    {
        var row = new Border();
        row.Classes.Add("fieldRow");
        var grid = new Grid { ColumnDefinitions = new ColumnDefinitions("*,110,220,70,28"), ColumnSpacing = 6 };
        row.Child = grid;

        var label = Ui.Text(Loc.Field(field, item.IsWeapon), null, 12.5);
        label.TextWrapping = TextWrapping.Wrap;
        var hint = Loc.FieldHint(field, item.IsWeapon);
        ToolTip.SetTip(label, (hint.Length > 0 ? hint + "\n" : "") + Loc.F("detail.gameField", field.Key));
        grid.Children.Add(label);

        string original = _session.Original(item, field.Key);
        string originalShown = original == null ? (_session.Verified ? "—" : "…") : DisplayValue(field, original);
        var orig = Ui.Text(originalShown, "mono faint", 12);
        ToolTip.SetTip(orig, Loc.T(_session.Verified ? "detail.origGame" : "detail.origCatalog"));
        Grid.SetColumn(orig, 1);
        grid.Children.Add(orig);

        var delta = Ui.Text("", null, 11, FontWeight.Bold);
        Grid.SetColumn(delta, 3);
        grid.Children.Add(delta);

        var reset = new Button { Content = Icons.Make(Icons.Reset, 14), Classes = { "icon" } };
        ToolTip.SetTip(reset, Loc.T("detail.resetStat"));
        Grid.SetColumn(reset, 4);
        grid.Children.Add(reset);

        void RefreshState()
        {
            var e = _session.Edit(item, field.Key);
            row.Classes.Set("modified", e != null);
            reset.IsVisible = e != null;
            delta.Text = "";
            if (e == null) return;
            if (field.IsNumeric && original != null &&
                EditSession.TryParseNumber(original, out var ov) && EditSession.TryParseNumber(EditSession.Format(e), out var nv))
            {
                double diff = nv - ov;
                delta.Text = ov != 0 ? $"{(diff >= 0 ? "+" : "")}{diff / Math.Abs(ov) * 100:0}%" : $"{(diff >= 0 ? "+" : "")}{EditSession.Format(diff)}";
                delta.Foreground = diff >= 0 ? Ui.Brush("HpBrush") : Ui.Parse("#F07A6E");
            }
            else
            {
                delta.Text = Loc.T("detail.changed");
                delta.Foreground = Ui.Brush("GoldBrush");
            }
        }

        void Changed()
        {
            RefreshState();
            foreach (var r in _detailRefreshers) r();
        }

        Control editor;
        switch (field.Type)
        {
            case "bool":
            {
                bool initial = _session.Edit(item, field.Key) is bool eb ? eb : EditSession.TryParseBool(original, out var ob) && ob;
                var toggle = new ToggleSwitch { IsChecked = initial, OnContent = Loc.T("common.yes"), OffContent = Loc.T("common.no"), MinWidth = 0 };
                toggle.IsCheckedChanged += (_, _) =>
                {
                    _session.SetEdit(item, field.Key, toggle.IsChecked == true);
                    Changed();
                };
                reset.Click += (_, _) =>
                {
                    _session.SetEdit(item, field.Key, null);
                    toggle.IsChecked = EditSession.TryParseBool(original, out var b) && b;
                    _session.SetEdit(item, field.Key, null);
                    Changed();
                };
                editor = toggle;
                break;
            }
            case "enum":
            {
                var combo = new ComboBox
                {
                    ItemsSource = field.Options.Select(x => Loc.Option(field, x)).ToList(),
                    HorizontalAlignment = HorizontalAlignment.Stretch,
                };
                int current = _session.Edit(item, field.Key) is { } ev ? Convert.ToInt32(ev, CultureInfo.InvariantCulture) : ParseInt(original);
                combo.SelectedIndex = field.Options.FindIndex(x => x.Value == current);
                combo.SelectionChanged += (_, _) =>
                {
                    if (combo.SelectedIndex < 0) return;
                    _session.SetEdit(item, field.Key, field.Options[combo.SelectedIndex].Value);
                    Changed();
                };
                reset.Click += (_, _) =>
                {
                    _session.SetEdit(item, field.Key, null);
                    combo.SelectedIndex = field.Options.FindIndex(x => x.Value == ParseInt(original));
                    _session.SetEdit(item, field.Key, null);
                    Changed();
                };
                editor = combo;
                break;
            }
            default:
                editor = BuildNumberEditor(item, field, original, reset, Changed);
                break;
        }
        Grid.SetColumn(editor, 2);
        grid.Children.Add(editor);
        RefreshState();
        return row;
    }

    private Control BuildNumberEditor(CatalogItem item, FieldDef field, string original, Button reset, Action changed)
    {
        bool isInt = field.Type == "int";
        var existing = _session.Edit(item, field.Key);
        var box = new TextBox
        {
            Classes = { "value" },
            Text = existing != null ? EditSession.Format(existing) : "",
            PlaceholderText = original ?? "",
            HorizontalAlignment = HorizontalAlignment.Stretch,
        };

        box.TextChanged += (_, _) =>
        {
            var text = (box.Text ?? "").Trim();
            if (text.Length == 0)
            {
                box.BorderBrush = null;
                _session.SetEdit(item, field.Key, null);
                changed();
                return;
            }
            if (!EditSession.TryParseNumber(text, out var v) || (isInt && Math.Abs(v - Math.Round(v)) > 1e-9))
            {
                box.BorderBrush = Ui.Parse("#F07A6E");
                ToolTip.SetTip(box, Loc.T(isInt ? "detail.needInt" : "detail.needNumber"));
                return;
            }
            box.BorderBrush = null;
            ToolTip.SetTip(box, null);
            _session.SetEdit(item, field.Key, isInt ? (int)Math.Round(v) : v);
            changed();
        };

        double Step()
        {
            if (isInt) return 1;
            EditSession.TryParseNumber(box.Text is { Length: > 0 } t ? t : original, out var cur);
            return Math.Abs(cur) >= 10 ? 1 : 0.1;
        }
        void Bump(int sign)
        {
            EditSession.TryParseNumber(box.Text is { Length: > 0 } t ? t : original, out var cur);
            var next = Math.Round(cur + sign * Step(), 4);
            box.Text = EditSession.Format(isInt ? (int)Math.Round(next) : next);
        }
        reset.Click += (_, _) => box.Text = "";

        var minus = new Button { Content = Icons.Make(Icons.Minus, 14), Classes = { "icon" } };
        minus.Click += (_, _) => Bump(-1);
        var plus = new Button { Content = Icons.Make(Icons.Plus, 14), Classes = { "icon" } };
        plus.Click += (_, _) => Bump(+1);

        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto,Auto"), ColumnSpacing = 3 };
        g.Children.Add(box);
        Grid.SetColumn(minus, 1);
        g.Children.Add(minus);
        Grid.SetColumn(plus, 2);
        g.Children.Add(plus);
        return g;
    }

    private static string DisplayValue(FieldDef field, string raw)
    {
        if (field.Type == "enum")
        {
            int v = ParseInt(raw);
            var opt = field.Options.FirstOrDefault(o => o.Value == v);
            return opt != null ? Loc.Option(field, opt) : raw;
        }
        if (field.Type == "bool") return EditSession.TryParseBool(raw, out var b) ? Loc.T(b ? "common.yes" : "common.no") : raw;
        return EditSession.TryParseNumber(raw, out var d) ? EditSession.Format(d) : raw;
    }

    private static int ParseInt(string s)
        => EditSession.TryParseNumber(s, out var d) ? (int)Math.Round(d) : 0;

    // ============================================================== bulk

    private Border BuildBulkPanel(bool weapon)
    {
        var fields = (weapon ? _catalog.Fields.Weapon : _catalog.Fields.Unit).Where(f => f.Type != "enum").ToList();
        var fieldBox = new ComboBox
        {
            ItemsSource = fields.Select(f => $"{Loc.Group(f.Group)} · {Loc.Field(f, weapon)}").ToList(),
            SelectedIndex = 0,
            HorizontalAlignment = HorizontalAlignment.Stretch,
        };
        string[] ops = { Loc.T("bulk.opSet"), Loc.T("bulk.opMultiply"), Loc.T("bulk.opAdd"), Loc.T("bulk.opReset") };
        var opBox = new ComboBox { ItemsSource = ops, SelectedIndex = 1, HorizontalAlignment = HorizontalAlignment.Stretch };
        var value = new TextBox { Text = "150", PlaceholderText = Loc.T("bulk.value"), Classes = { "value" } };
        var hint = Ui.Text("", "faint", 11);
        hint.TextWrapping = TextWrapping.Wrap;

        void UpdateHint()
        {
            var f = fieldBox.SelectedIndex >= 0 ? fields[fieldBox.SelectedIndex] : null;
            bool isBool = f?.Type == "bool";
            value.IsVisible = opBox.SelectedIndex != 3;
            hint.Text = isBool
                ? Loc.T("bulk.hintBool")
                : opBox.SelectedIndex switch
                {
                    1 => Loc.T("bulk.hintMultiply"),
                    2 => Loc.T("bulk.hintAdd"),
                    3 => Loc.T("bulk.hintReset"),
                    _ => Loc.T("bulk.hintSet"),
                };
        }
        fieldBox.SelectionChanged += (_, _) => UpdateHint();
        opBox.SelectionChanged += (_, _) => UpdateHint();
        UpdateHint();

        var apply = Ui.Button(Loc.T("bulk.apply"), () =>
        {
            var f = fields[Math.Max(0, fieldBox.SelectedIndex)];
            var items = FilteredItems();
            int changedCount = BulkApply(items, f, opBox.SelectedIndex, value.Text ?? "");
            ApplyFilter();
            RenderDetail();
            SetStatus(changedCount < 0
                ? Loc.T("bulk.invalid")
                : Loc.F("bulk.done", Loc.Field(f, weapon), changedCount, items.Count));
        }, "primary");

        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,*"), RowDefinitions = new RowDefinitions("Auto,Auto"), ColumnSpacing = 6, RowSpacing = 6 };
        Grid.SetColumnSpan(fieldBox, 2);
        g.Children.Add(fieldBox);
        Grid.SetRow(opBox, 1);
        g.Children.Add(opBox);
        Grid.SetRow(value, 1);
        Grid.SetColumn(value, 1);
        g.Children.Add(value);

        var panel = new Border
        {
            Child = Ui.Column(6, Ui.Text(Loc.T("bulk.title"), "groupTitle"), Ui.Text(Loc.T("bulk.title.hint"), "faint", 12), g, hint, apply),
            Padding = new Thickness(10),
            CornerRadius = new CornerRadius(8),
            BorderBrush = Ui.Brush("GoldDimBrush"),
            BorderThickness = new Thickness(1),
            Background = Ui.Parse("#1FEFB656"),
        };
        return panel;
    }

    /// <summary>Returns how many entries changed, or -1 for an invalid value.</summary>
    private int BulkApply(List<CatalogItem> items, FieldDef field, int op, string text)
    {
        int count = 0;
        if (op == 3)
        {
            foreach (var it in items)
                if (_session.Edit(it, field.Key) != null) { _session.SetEdit(it, field.Key, null); count++; }
            return count;
        }

        if (field.Type == "bool")
        {
            if (!EditSession.TryParseBool(text, out var b)) return -1;
            foreach (var it in items) { _session.SetEdit(it, field.Key, b); count++; }
            return count;
        }

        if (!EditSession.TryParseNumber(text, out var v)) return -1;
        foreach (var it in items)
        {
            double result;
            if (op == 0) result = v;
            else
            {
                if (!EditSession.TryParseNumber(_session.Original(it, field.Key), out var o)) continue;
                result = op == 1 ? o * v / 100.0 : o + v;
            }
            object value = field.Type == "int" ? (int)Math.Round(result) : Math.Round(result, 4);
            _session.SetEdit(it, field.Key, value);
            count++;
        }
        return count;
    }
}
