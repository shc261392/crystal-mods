using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using SkiaSharp;
using Warpstorm.Shared;

// Warpstorm SchemeBuilder
//
//   build <schemeDir> <outDir> [--src <portraitCache>] [--size 512]
//       Renders curated portraits for every unit of the pack's faction into
//       <outDir>/portraits/ and copies scheme.json. Source portraits are the
//       game's "Selection portraits" (as published by BattleSector Tools); they
//       are downloaded once into the cache.
//   sheet <schemeDir> <out.png> [--src <portraitCache>] [--tex <albedoDir>]
//       Before/after review sheet (portraits, plus 3D albedo textures if given).
internal static class Program
{
    private static readonly string Repo = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../../.."));
    private static string Data => Path.Combine(Repo, "battlesector-tools", "src", "data");

    private static int Main(string[] args)
    {
        if (args.Length < 3) { Console.Error.WriteLine("usage: build <schemeDir> <outDir> | sheet <schemeDir> <out.png> | overview <out.png> <schemeDir>..."); return 2; }
        string Opt(string name, string def) { int i = Array.IndexOf(args, name); return i >= 0 && i + 1 < args.Length ? args[i + 1] : def; }
        if (args[0] == "overview") return Overview(args, Opt);
        var pack = SchemePack.Load(Path.GetFullPath(args[1]));
        string cache = Opt("--src", Path.Combine(Repo, "warpstorm", ".copilot_workspace", "scheme-src", "portraits"));
        var portraits = FactionPortraits(pack.Faction);
        Fetch(portraits, cache);

        if (args[0] == "build") return Build(pack, args[2], cache, portraits, int.Parse(Opt("--size", "512")));
        if (args[0] == "sheet") return Sheet(pack, args[2], cache, portraits, Opt("--tex", null));
        Console.Error.WriteLine("unknown command " + args[0]);
        return 2;
    }

    /// <summary>Portrait sprite names of the faction's units (BattleSector Tools catalog).</summary>
    private static List<string> FactionPortraits(string faction)
    {
        using var fdoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(Repo, "warpstorm", "shared", "armypainter-factions.json")));
        int fid = fdoc.RootElement.GetProperty("factions").EnumerateArray()
            .First(f => f.GetProperty("key").GetString() == faction).GetProperty("factionId").GetInt32();
        using var udoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(Data, "units.json")));
        return udoc.RootElement.EnumerateArray()
            .Where(u => u.GetProperty("faction").GetInt32() == fid && u.TryGetProperty("portrait", out var p) && p.GetString()?.Length > 0)
            .Select(u => u.GetProperty("portrait").GetString())
            .Distinct().OrderBy(n => n, StringComparer.Ordinal).ToList();
    }

    private static void Fetch(List<string> names, string cache)
    {
        Directory.CreateDirectory(cache);
        using var udoc = JsonDocument.Parse(File.ReadAllText(Path.Combine(Data, "image-urls.json")));
        var urls = udoc.RootElement.GetProperty("units");
        using var http = new HttpClient();
        http.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Warpstorm SchemeBuilder)");
        foreach (var n in names)
        {
            var dest = Path.Combine(cache, n + ".png");
            if (File.Exists(dest) || !urls.TryGetProperty(n, out var u)) continue;
            Console.WriteLine("fetch " + n);
            File.WriteAllBytes(dest, http.GetByteArrayAsync(u.GetProperty("url").GetString()).Result);
        }
    }

    private static int Build(SchemePack pack, string outDir, string cache, List<string> names, int size)
    {
        var dir = Path.Combine(outDir, "portraits");
        Directory.CreateDirectory(dir);
        File.Copy(Path.Combine(pack.Dir, "scheme.json"), Path.Combine(outDir, "scheme.json"), true);
        if (pack.BadgeFile != null)
        {
            if (!File.Exists(pack.BadgeFile)) { Console.Error.WriteLine("missing badge " + pack.BadgeFile); return 1; }
            File.Copy(pack.BadgeFile, Path.Combine(outDir, pack.Badge.Image), true);
        }
        int n = 0;
        foreach (var name in names)
        {
            var src = Path.Combine(cache, name + ".png");
            if (!File.Exists(src)) { Console.WriteLine("  skip (no source) " + name); continue; }
            if (IsPlaceholder(src)) { Console.WriteLine("  skip (placeholder art) " + name); continue; }
            using var bmp = Load(src, size);
            var recoloured = Recolour(bmp, pack.RulesForPortrait(name));
            Save(recoloured, Path.Combine(dir, name + ".png"));
            recoloured.Dispose();
            n++;
        }
        Console.WriteLine($"{pack.Id}: {n} portraits -> {dir}");
        return 0;
    }

    private static int Sheet(SchemePack pack, string outPng, string cache, List<string> names, string texDir)
    {
        const int cell = 220;
        var pics = names.Where(n => File.Exists(Path.Combine(cache, n + ".png")) && !IsPlaceholder(Path.Combine(cache, n + ".png"))).ToList();
        var texs = texDir != null && Directory.Exists(texDir) ? Directory.GetFiles(texDir, "*.png").OrderBy(f => f, StringComparer.Ordinal).ToList() : new List<string>();
        int cols = 4; // pairs per row
        int rows = (pics.Count + cols - 1) / cols + (texs.Count + cols - 1) / cols;
        var info = new SKImageInfo(cols * cell * 2 + 20, rows * (cell + 26) + 60);
        using var surface = SKSurface.Create(info);
        var c = surface.Canvas;
        c.Clear(new SKColor(0x16, 0x10, 0x0B));
        using var font = new SKFont(SKTypeface.Default, 15);
        using var title = new SKFont(SKTypeface.Default, 22);
        using var ink = new SKPaint { Color = new SKColor(0xF2, 0xEE, 0xE6), IsAntialias = true };
        c.DrawText($"{pack.Name} {pack.Version} -> {pack.Faction}   (left: original, right: scheme)", 10, 32, title, ink);

        int y = 50, x = 0, k = 0;
        void Pair(string label, SKBitmap before, SKBitmap after)
        {
            var px = 10 + x * cell * 2;
            c.DrawBitmap(before, new SKRect(px, y, px + cell - 4, y + cell - 4));
            c.DrawBitmap(after, new SKRect(px + cell, y, px + cell * 2 - 4, y + cell - 4));
            c.DrawText(label, px, y + cell + 14, font, ink);
            if (++x == cols) { x = 0; y += cell + 26; }
            k++;
        }
        foreach (var n in pics)
        {
            using var b = Load(Path.Combine(cache, n + ".png"), cell);
            using var a = Recolour(b, pack.RulesForPortrait(n));
            Pair(n, b, a);
        }
        if (x != 0) { x = 0; y += cell + 26; }
        foreach (var f in texs)
        {
            var name = Path.GetFileNameWithoutExtension(f);
            using var b = Load(f, 512);
            using var a = Recolour(b, pack.RulesForTexture(name));
            Pair("3D " + name, b, a);
        }
        using var img = surface.Snapshot();
        using var data = img.Encode(SKEncodedImageFormat.Png, 90);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPng)));
        File.WriteAllBytes(outPng, data.ToArray());
        Console.WriteLine("sheet -> " + outPng);
        return 0;
    }

    /// <summary>The game ships some portraits as black text on white ("REIVERS"); skip those.</summary>
    private static bool IsPlaceholder(string path)
    {
        using var b = Load(path, 64);
        int white = 0, n = 0;
        for (int y = 0; y < b.Height; y++)
            for (int x = 0; x < b.Width; x++)
            {
                var c = b.GetPixel(x, y);
                n++;
                if (c.Alpha > 200 && c.Red > 235 && c.Green > 235 && c.Blue > 235) white++;
            }
        return white > n * 0.45;
    }

    /// <summary>One row per scheme: badge, portraits, a 3D albedo and the stamped decal atlas.</summary>
    private static int Overview(string[] args, Func<string, string, string> opt)
    {
        string outPng = args[1];
        string cache = opt("--src", Path.Combine(Repo, "warpstorm", ".copilot_workspace", "scheme-src", "portraits"));
        string texDir = opt("--tex", null);
        string logo = opt("--logo", null);
        var dirs = args.Skip(2).TakeWhile(a => !a.StartsWith("--")).ToList();
        string[] sample = { "UltramarinesIntercessorsIcon", "CaptainIcon", "UltramarinesTerminatorsStormBolterIcon", "UltramarinesAggressorsIcon", "RedemptorDreadnoughtIcon" };
        const int cell = 170;
        int cols = 1 + sample.Length + 2;
        var info = new SKImageInfo(cols * cell + 20, dirs.Count * (cell + 30) + 50);
        using var surface = SKSurface.Create(info);
        var c = surface.Canvas;
        c.Clear(new SKColor(0x16, 0x10, 0x0B));
        using var font = new SKFont(SKTypeface.Default, 14);
        using var ink = new SKPaint { Color = new SKColor(0xF2, 0xEE, 0xE6), IsAntialias = true };
        c.DrawText("Scheme overview (Ultramarines base): badge · portraits · 3D albedo ULT_INT_D · decal atlas with badge", 10, 28, new SKFont(SKTypeface.Default, 18), ink);
        int y = 44;
        foreach (var dir in dirs)
        {
            var pack = SchemePack.Load(Path.GetFullPath(dir));
            Fetch(sample.ToList(), cache);
            int x = 10;
            using (var badgeBg = new SKPaint { Color = new SKColor(0x24, 0x24, 0x2A) })
                c.DrawRect(new SKRect(x, y, x + cell - 6, y + cell - 6), badgeBg);
            if (pack.BadgeFile != null && File.Exists(pack.BadgeFile))
            {
                using var badge = Load(pack.BadgeFile, cell - 30);
                c.DrawBitmap(badge, new SKRect(x + 12, y + 12, x + cell - 18, y + cell - 18));
            }
            using (var sw = new SKPaint { Color = SKColor.Parse("#" + pack.Primary) }) c.DrawRect(new SKRect(x, y + cell - 18, x + 60, y + cell - 6), sw);
            c.DrawText($"{pack.Name} {pack.Version}", x, y + cell + 12, font, ink);
            x += cell;
            foreach (var n in sample)
            {
                var src = Path.Combine(cache, n + ".png");
                if (!File.Exists(src)) { x += cell; continue; }
                using var b = Load(src, cell);
                using var a = Recolour(b, pack.RulesForPortrait(n));
                c.DrawBitmap(a, new SKRect(x, y, x + cell - 6, y + cell - 6));
                x += cell;
            }
            if (texDir != null && File.Exists(Path.Combine(texDir, "ULT_INT_D.png")))
            {
                using var b = Load(Path.Combine(texDir, "ULT_INT_D.png"), 512);
                using var a = Recolour(b, pack.RulesForTexture("ULT_INT_D"));
                c.DrawBitmap(a, new SKRect(x, y, x + cell - 6, y + cell - 6));
            }
            x += cell;
            if (logo != null && File.Exists(logo) && pack.Badge != null)
            {
                using var atlas = StampedAtlas(logo, pack);
                // show the badge area on a dark plate, like it would sit on armour
                using var plate = new SKPaint { Color = SKColor.Parse("#" + pack.Primary) };
                c.DrawRect(new SKRect(x, y, x + cell - 6, y + cell - 6), plate);
                var srcRect = new SKRect(pack.Badge.U0 * atlas.Width, (1 - pack.Badge.V1) * atlas.Height, pack.Badge.U1 * atlas.Width, (1 - pack.Badge.V0) * atlas.Height);
                c.DrawBitmap(atlas, srcRect, new SKRect(x + 8, y + 8, x + cell - 14, y + cell - 14));
            }
            y += cell + 30;
        }
        using var img = surface.Snapshot();
        using var data = img.Encode(SKEncodedImageFormat.Png, 90);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPng)));
        File.WriteAllBytes(outPng, data.ToArray());
        Console.WriteLine("overview -> " + outPng);
        return 0;
    }

    /// <summary>Atlas PNG (top-down) -> stamp badge in Unity (bottom-up) space -> back to top-down. Alpha shown as white.</summary>
    private static SKBitmap StampedAtlas(string atlasPng, SchemePack pack)
    {
        using var atlas = Load(atlasPng, 1024);
        using var badge = Load(pack.BadgeFile, 512);
        byte[] a = FlipRows(Straight(atlas), atlas.Width, atlas.Height);
        byte[] b = FlipRows(Straight(badge), badge.Width, badge.Height);
        PaintMath.StampBadge(a, atlas.Width, atlas.Height, pack.Badge.U0, pack.Badge.V0, pack.Badge.U1, pack.Badge.V1, b, badge.Width, badge.Height, pack.Badge.Scale);
        a = FlipRows(a, atlas.Width, atlas.Height);
        for (int i = 0; i < a.Length; i += 4) { byte al = a[i + 3]; a[i] = a[i + 1] = a[i + 2] = 255; a[i + 3] = al; }
        var info = new SKImageInfo(atlas.Width, atlas.Height, SKColorType.Rgba8888, SKAlphaType.Unpremul);
        var result = new SKBitmap(info);
        System.Runtime.InteropServices.Marshal.Copy(a, 0, result.GetPixels(), a.Length);
        return result;
    }

    private static byte[] Straight(SKBitmap src)
    {
        var info = new SKImageInfo(src.Width, src.Height, SKColorType.Rgba8888, SKAlphaType.Unpremul);
        using var straight = new SKBitmap(info);
        src.CopyTo(straight, SKColorType.Rgba8888);
        return (byte[])straight.Bytes.Clone();
    }

    private static byte[] FlipRows(byte[] px, int w, int h)
    {
        var o = new byte[px.Length];
        int row = w * 4;
        for (int y = 0; y < h; y++) Buffer.BlockCopy(px, y * row, o, (h - 1 - y) * row, row);
        return o;
    }

    private static SKBitmap Load(string path, int max)
    {
        using var src = SKBitmap.Decode(path);
        var bmp = src.Copy(SKColorType.Rgba8888);
        if (max > 0 && Math.Max(bmp.Width, bmp.Height) > max)
        {
            float s = (float)max / Math.Max(bmp.Width, bmp.Height);
            var resized = bmp.Resize(new SKImageInfo((int)(bmp.Width * s), (int)(bmp.Height * s), SKColorType.Rgba8888, SKAlphaType.Unpremul),
                                     new SKSamplingOptions(SKCubicResampler.Mitchell));
            bmp.Dispose();
            bmp = resized;
        }
        return bmp;
    }

    private static SKBitmap Recolour(SKBitmap src, List<PaintMath.Rule> rules)
    {
        var info = new SKImageInfo(src.Width, src.Height, SKColorType.Rgba8888, SKAlphaType.Unpremul);
        using var straight = new SKBitmap(info);
        src.CopyTo(straight, SKColorType.Rgba8888);
        var bytes = straight.Bytes;
        var outBytes = PaintMath.ApplyRules(bytes, rules);
        var result = new SKBitmap(info);
        System.Runtime.InteropServices.Marshal.Copy(outBytes, 0, result.GetPixels(), outBytes.Length);
        return result;
    }

    private static void Save(SKBitmap bmp, string path)
    {
        using var img = SKImage.FromBitmap(bmp);
        using var data = img.Encode(SKEncodedImageFormat.Png, 100);
        File.WriteAllBytes(path, data.ToArray());
    }
}
