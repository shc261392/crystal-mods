using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;

namespace Warpstorm.Configurator;

/// <summary>Small themed modal: returns the index of the clicked button (last = cancel / close).</summary>
public static class Dialog
{
    public static async Task<int> Ask(Window owner, string title, string message, params string[] buttons)
    {
        int result = buttons.Length - 1;
        var win = new Window
        {
            Title = title,
            Width = 460,
            SizeToContent = SizeToContent.Height,
            CanResize = false,
            WindowStartupLocation = WindowStartupLocation.CenterOwner,
            Icon = owner.Icon,
        };

        var row = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, HorizontalAlignment = HorizontalAlignment.Right };
        for (int i = 0; i < buttons.Length; i++)
        {
            int index = i;
            var b = new Button { Content = buttons[i] };
            b.Classes.Add(i == 0 ? "primary" : "ghost");
            b.Click += (_, _) => { result = index; win.Close(); };
            row.Children.Add(b);
        }

        win.Content = new StackPanel
        {
            Margin = new Thickness(20),
            Spacing = 16,
            Children =
            {
                new TextBlock { Text = title, FontSize = 16, FontWeight = FontWeight.Bold },
                new TextBlock { Text = message, TextWrapping = TextWrapping.Wrap, Classes = { "muted" } },
                row,
            },
        };
        await win.ShowDialog(owner);
        return result;
    }
}

/// <summary>Unity KeyCode ints the BepInEx configs use, with readable names.</summary>
public static class KeyNames
{
    public static readonly (int code, string name)[] Choices =
        Enumerable.Range(0, 15).Select(i => (282 + i, "F" + (i + 1)))
            .Concat(new[]
            {
                (277, "Insert"), (278, "Home"), (279, "End"), (280, "Page Up"), (281, "Page Down"),
                (19, "Pause"), (302, "Scroll Lock"), (96, "` (back quote)"),
            })
            .ToArray();

    private static readonly Dictionary<int, string> ByCode = Choices.ToDictionary(c => c.code, c => c.name);

    public static string Name(string code)
        => int.TryParse(code, out var c) ? Name(c) : (code ?? "?");

    public static string Name(int code) => ByCode.TryGetValue(code, out var n) ? n : $"KeyCode {code}";
}
