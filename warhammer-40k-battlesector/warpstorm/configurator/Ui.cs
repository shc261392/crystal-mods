using System;
using System.Collections.Generic;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform;

namespace Warpstorm.Configurator;

/// <summary>Small control factory so the views read like the HTML they mirror.</summary>
public static class Ui
{
    private static readonly Dictionary<string, Bitmap> Images = new();

    public static IBrush Brush(string key)
        => Application.Current!.TryGetResource(key, null, out var r) && r is IBrush b ? b : Brushes.Gray;

    public static IBrush Parse(string hex)
    {
        try { return new SolidColorBrush(Color.Parse(hex.StartsWith("#") ? hex : "#" + hex)); }
        catch { return Brushes.Transparent; }
    }

    /// <summary>Loads (and caches) an embedded image, e.g. "units/Foo", "ui/stat-health".</summary>
    public static Bitmap Image(string path)
    {
        if (string.IsNullOrWhiteSpace(path)) return null;
        if (Images.TryGetValue(path, out var hit)) return hit;
        Bitmap bmp = null;
        try
        {
            using var stream = AssetLoader.Open(new Uri($"avares://Warpstorm.Configurator/assets/{path}.png"));
            bmp = new Bitmap(stream);
        }
        catch
        {
            // not bundled for this entry
        }
        Images[path] = bmp;
        return bmp;
    }

    public static Bitmap Portrait(CatalogItem item)
        => item == null ? null
         : item.IsWeapon ? Image("weapons/" + item.Image) ?? Image(item.IsMelee ? "ui/type-melee" : "ui/type-ranged")
         : Image("units/" + item.Image) ?? Image("ui/faction-" + item.FactionId);

    public static TextBlock Text(string text, string classes = null, double size = 0, FontWeight? weight = null)
    {
        var tb = new TextBlock { Text = text, VerticalAlignment = VerticalAlignment.Center };
        if (!string.IsNullOrEmpty(classes)) tb.Classes.AddRange(classes.Split(' ', StringSplitOptions.RemoveEmptyEntries));
        if (size > 0) tb.FontSize = size;
        if (weight.HasValue) tb.FontWeight = weight.Value;
        return tb;
    }

    public static Border Chip(string text, string classes = null)
    {
        var b = new Border { Child = new TextBlock { Text = text }, VerticalAlignment = VerticalAlignment.Center };
        b.Classes.Add("chip");
        if (!string.IsNullOrEmpty(classes)) b.Classes.AddRange(classes.Split(' ', StringSplitOptions.RemoveEmptyEntries));
        return b;
    }

    /// <summary>A white HUD icon tinted with <paramref name="color"/> (like the site's SVG mask).</summary>
    public static Control TintedIcon(string path, string color, double size)
    {
        var bmp = Image(path);
        if (bmp == null) return new Border { Width = 0 };
        return new Border
        {
            Width = size,
            Height = size,
            Background = Parse(color),
            OpacityMask = new ImageBrush(bmp) { Stretch = Stretch.Uniform },
            VerticalAlignment = VerticalAlignment.Center,
        };
    }

    /// <summary>Square portrait on the unit's role colour, like UnitListRow.astro.</summary>
    public static Border PortraitBox(CatalogItem item, double size)
    {
        var bmp = Portrait(item);
        Control content = bmp != null
            ? new Image { Source = bmp, Stretch = Stretch.UniformToFill, VerticalAlignment = VerticalAlignment.Top }
            : new TextBlock
            {
                Text = item == null || item.Name.Length == 0 ? "?" : item.Name[..1],
                FontWeight = FontWeight.Black,
                FontSize = size / 2.4,
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Center,
            };
        return new Border
        {
            Width = size,
            Height = size,
            CornerRadius = new CornerRadius(size > 60 ? 8 : 6),
            ClipToBounds = true,
            BorderBrush = Parse("#40000000"),
            BorderThickness = new Thickness(1),
            Background = item == null ? Brush("ElevatedBrush")
                       : item.IsWeapon ? Parse("#4D000000")
                       : Parse(TierColor(item.Role, item.RoleColor)),
            Padding = item != null && item.IsWeapon ? new Thickness(size / 10) : new Thickness(0),
            Child = content,
        };
    }

    /// <summary>Tier colours used by BattleSector Tools for the portrait plate.</summary>
    public static string TierColor(string role, string fallback) => role switch
    {
        "HQ" => "#d4af37",
        "Elite" => "#7e57c2",
        "Heavy Support" => "#3b82f6",
        "Fast Attack" or "Flyer" => "#22c55e",
        "Troop" => "#dc2626",
        _ => string.IsNullOrEmpty(fallback) ? "#5c5c5c" : fallback,
    };

    public static Border Gilded(Control child, Thickness? padding = null)
    {
        var grid = new Panel();
        var top = new Border();
        top.Classes.Add("gildedTop");
        grid.Children.Add(new Border { Padding = padding ?? new Thickness(16), Child = child });
        grid.Children.Add(top);
        var b = new Border { Child = grid };
        b.Classes.Add("gilded");
        return b;
    }

    public static Border Surface(Control child, Thickness? padding = null)
    {
        var b = new Border { Child = child, Padding = padding ?? new Thickness(14) };
        b.Classes.Add("surface");
        return b;
    }

    public static Button Button(string text, Action onClick, string classes = null, string tip = null)
    {
        var b = new Button { Content = text, VerticalAlignment = VerticalAlignment.Center };
        if (!string.IsNullOrEmpty(classes)) b.Classes.AddRange(classes.Split(' ', StringSplitOptions.RemoveEmptyEntries));
        if (tip != null) ToolTip.SetTip(b, tip);
        b.Click += (_, _) => onClick();
        return b;
    }

    public static StackPanel Row(double spacing, params Control[] children)
    {
        var p = new StackPanel { Orientation = Orientation.Horizontal, Spacing = spacing };
        foreach (var c in children) if (c != null) p.Children.Add(c);
        return p;
    }

    public static StackPanel Column(double spacing, params Control[] children)
    {
        var p = new StackPanel { Spacing = spacing };
        foreach (var c in children) if (c != null) p.Children.Add(c);
        return p;
    }

    /// <summary>Square icon-only button with a tooltip.</summary>
    public static Button IconButton(string icon, string tip, Action onClick, double size = 14)
    {
        var b = new Button { Content = Icons.Make(icon, size), Classes = { "icon" } };
        if (tip != null) ToolTip.SetTip(b, tip);
        b.Click += (_, _) => onClick();
        return b;
    }

    /// <summary>Button with a leading icon.</summary>
    public static Button IconTextButton(string icon, string text, Action onClick, string classes = null, string tip = null)
    {
        var b = new Button { Content = Row(6, Icons.Make(icon, 15), new TextBlock { Text = text, VerticalAlignment = VerticalAlignment.Center }) };
        if (!string.IsNullOrEmpty(classes)) b.Classes.AddRange(classes.Split(' ', StringSplitOptions.RemoveEmptyEntries));
        if (tip != null) ToolTip.SetTip(b, tip);
        b.Click += (_, _) => onClick();
        return b;
    }

    /// <summary>Small filled circle marking an unsaved change.</summary>
    public static Control Dot(bool on) => new Avalonia.Controls.Shapes.Ellipse
    {
        Width = 7, Height = 7, Fill = on ? Brush("GoldBrush") : Brushes.Transparent,
        VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 4, 0),
    };

    public static Border Swatch(string hex, double w, double h)
        => new()
        {
            Width = w,
            Height = h,
            CornerRadius = new CornerRadius(4),
            BorderBrush = Parse("#80000000"),
            BorderThickness = new Thickness(1),
            Background = Parse(hex),
            VerticalAlignment = VerticalAlignment.Center,
        };
}
