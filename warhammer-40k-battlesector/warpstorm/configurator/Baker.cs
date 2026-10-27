using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using AssetsTools.NET;
using AssetsTools.NET.Extra;
using AssetsTools.NET.Texture;
using BCnEncoder.Encoder;
using BCnEncoder.Shared;
using Warpstorm.Shared;

namespace Warpstorm.Configurator;

/// <summary>
/// "Bake": paints a faction's model textures ahead of time so the game only has
/// to upload them (see shared/PaintCache.cs). Reads the game's faction bundle
/// read-only, decodes each unit albedo (Crunch/DXT), applies the same
/// PaintMath recolour as the plugin, BC3-encodes it with mips and writes the cache.
/// </summary>
public static class Baker
{
    public sealed class Job
    {
        public string Faction = "";
        public SchemePack Pack;
        public string Primary = "", Secondary = "";
        public float HueWindow, SatThreshold, Feather;
        public int MaxSize = 2048;

        public string Key => PaintCache.SchemeKey(Faction, Pack, Primary, Secondary, HueWindow, SatThreshold, Feather, MaxSize);
    }

    public sealed class Result
    {
        public int Baked, Skipped, Failed, Total;
        public string Note = "";
    }

    public static string CacheRoot(string gameDir) => Path.Combine(gameDir, "BepInEx", "cache", "warpstorm", "paint");

    public static string BundlePath(string gameDir, string faction)
        => Path.Combine(GameLocator.DataDir(gameDir), "StreamingAssets", $"faction-{faction.ToLowerInvariant()}_assets_all.bundle");

    /// <summary>Unit-shader materials' own albedo textures in the faction bundle.</summary>
    private static List<(AssetsFileInstance file, AssetFileInfo info, string name)> UnitTextures(AssetsManager am, BundleFileInstance bun, string slot = "_MainTex")
    {
        var result = new List<(AssetsFileInstance, AssetFileInfo, string)>();
        for (int d = 0; d < bun.file.BlockAndDirInfo.DirectoryInfos.Count; d++)
        {
            AssetsFileInstance af;
            try { af = am.LoadAssetsFileFromBundle(bun, d); } catch { continue; }
            if (af == null) continue; // .resS / non-serialized entries
            var wanted = new HashSet<long>();
            foreach (var info in af.file.GetAssetsOfType(AssetClassID.Material))
            {
                AssetTypeValueField bf;
                try { bf = am.GetBaseField(af, info); } catch { continue; }
                var envs = bf["m_SavedProperties"]["m_TexEnvs"]["Array"].Children;
                bool unitShader = envs.Any(e => e["first"].AsString == "_ProjectionAlbedoMap"); // the game's unit shader
                if (!unitShader) continue;
                var queue = bf["m_CustomRenderQueue"];
                if (queue != null && !queue.IsDummy && queue.AsInt >= 3000) continue;
                var kwField = bf["m_ValidKeywords"];
                var kw = kwField == null || kwField.IsDummy ? new List<string>() : kwField["Array"].Children.Select(c => c.AsString).ToList();
                if (kw.Contains("_ALPHABLEND_ON") || kw.Contains("_ALPHAPREMULTIPLY_ON")) continue;
                var main = envs.FirstOrDefault(e => e["first"].AsString == slot);
                if (main == null) continue;
                var tex = main["second"]["m_Texture"];
                if (tex["m_FileID"].AsInt != 0 || tex["m_PathID"].AsLong == 0) continue; // other bundle: painted live
                wanted.Add(tex["m_PathID"].AsLong);
            }
            foreach (var pid in wanted)
            {
                var info = af.file.GetAssetInfo(pid);
                if (info == null) continue;
                try { result.Add((af, info, am.GetBaseField(af, info)["m_Name"].AsString)); } catch { }
            }
        }
        return result;
    }

    public static Result Bake(string gameDir, Job job, Action<string> progress, CancellationToken cancel, string rootOverride = null)
    {
        var res = new Result();
        var bundle = BundlePath(gameDir, job.Faction);
        if (!File.Exists(bundle))
        {
            res.Note = Loc.F("bake.noBundle", job.Faction);
            return res;
        }

        var root = rootOverride ?? CacheRoot(gameDir);
        string key = job.Key;
        var am = new AssetsManager();
        var bun = am.LoadBundleFile(bundle);
        var textures = UnitTextures(am, bun);
        // Chapter badge: stamp the decal atlases too (cached as "badge-<name>").
        byte[] stencil = null; int stw = 0, sth = 0;
        if (job.Pack?.Badge != null && job.Pack.BadgeFile != null && File.Exists(job.Pack.BadgeFile))
        {
            stencil = LoadStencilBottomUp(job.Pack.BadgeFile, out stw, out sth);
            textures.AddRange(UnitTextures(am, bun, "_DetailAlbedoMap")
                .Where(t => job.Pack.IsBadgeTexture(t.name))
                .Select(t => (t.file, t.info, "badge-" + t.name)));
        }
        res.Total = textures.Count;

        int workers = Math.Clamp(Environment.ProcessorCount / 2, 1, 4);
        using var gate = new SemaphoreSlim(workers);
        var running = new List<Task>();
        int done = 0;

        foreach (var (file, info, name) in textures)
        {
            cancel.ThrowIfCancellationRequested();
            byte[] bgra;
            int sw, sh;
            try
            {
                var bf = am.GetBaseField(file, info);
                var tf = TextureFile.ReadTextureFile(bf);
                sw = tf.m_Width; sh = tf.m_Height;
                if (PaintCache.TryRead(root, key, name, out _, out _, out _, out _, out int cw, out int ch, out _) && cw == sw && ch == sh)
                {
                    Interlocked.Increment(ref res.Skipped);
                    progress(Loc.F("bake.progress", job.Faction, Interlocked.Increment(ref done), res.Total, name));
                    continue;
                }
                bgra = tf.DecodeTextureRaw(tf.FillPictureData(file));   // single-threaded: AssetsManager is not thread-safe
                if (bgra == null) throw new InvalidDataException("unsupported texture format " + tf.m_TextureFormat);
            }
            catch (Exception ex)
            {
                Interlocked.Increment(ref res.Failed);
                progress(Loc.F("bake.failedOne", name, ex.Message));
                continue;
            }

            gate.Wait(cancel);
            running.Add(Task.Run(() =>
            {
                try
                {
                    if (name.StartsWith("badge-")) BakeBadge(root, key, job, name, bgra, sw, sh, stencil, stw, sth);
                    else BakeOne(root, key, job, name, bgra, sw, sh);
                    Interlocked.Increment(ref res.Baked);
                }
                catch (Exception ex)
                {
                    Interlocked.Increment(ref res.Failed);
                    progress(Loc.F("bake.failedOne", name, ex.Message));
                }
                finally
                {
                    gate.Release();
                    progress(Loc.F("bake.progress", job.Faction, Interlocked.Increment(ref done), res.Total, name));
                }
            }, cancel));
            running.RemoveAll(t => t.IsCompleted);
        }
        Task.WaitAll(running.ToArray());
        return res;
    }

    private static void BakeBadge(string root, string key, Job job, string name, byte[] bgra, int sw, int sh,
                                  byte[] stencil, int stw, int sth)
    {
        PaintCache.TargetSize(sw, sh, job.MaxSize, out int w, out int h);
        var rgba = Downscale(bgra, sw, sh, w, h);
        var b = job.Pack.Badge;
        PaintMath.StampBadge(rgba, w, h, b.U0, b.V0, b.U1, b.V1, stencil, stw, sth, b.Scale);
        EncodeAndWrite(root, key, name, rgba, w, h, sw, sh);
    }

    /// <summary>PNG -> straight RGBA with rows bottom-up (Unity order).</summary>
    private static byte[] LoadStencilBottomUp(string png, out int w, out int h)
    {
        using var src = SkiaSharp.SKBitmap.Decode(png);
        var info = new SkiaSharp.SKImageInfo(src.Width, src.Height, SkiaSharp.SKColorType.Rgba8888, SkiaSharp.SKAlphaType.Unpremul);
        using var bmp = new SkiaSharp.SKBitmap(info);
        src.CopyTo(bmp, SkiaSharp.SKColorType.Rgba8888);
        w = bmp.Width; h = bmp.Height;
        var top = bmp.Bytes;
        var o = new byte[top.Length];
        int row = w * 4;
        for (int y = 0; y < h; y++) Buffer.BlockCopy(top, y * row, o, (h - 1 - y) * row, row);
        return o;
    }

    private static void BakeOne(string root, string key, Job job, string name, byte[] bgra, int sw, int sh)
    {
        PaintCache.TargetSize(sw, sh, job.MaxSize, out int w, out int h);
        var rgba = Downscale(bgra, sw, sh, w, h);   // also BGRA -> RGBA; rows stay bottom-up (Unity order)

        var mapped = job.Pack != null
            ? PaintMath.ApplyRules(rgba, job.Pack.RulesForTexture(name))
            : PaintMath.Remap(rgba, Hex(job.Primary, 0), Hex(job.Primary, 2), Hex(job.Primary, 4),
                              Hex(job.Secondary, 0), Hex(job.Secondary, 2), Hex(job.Secondary, 4),
                              job.HueWindow, job.SatThreshold, job.Feather);
        EncodeAndWrite(root, key, name, mapped, w, h, sw, sh);
    }

    private static void EncodeAndWrite(string root, string key, string name, byte[] mapped, int w, int h, int sw, int sh)
    {
        var encoder = new BcEncoder(CompressionFormat.Bc3);
        encoder.OutputOptions.GenerateMipMaps = true;
        encoder.OutputOptions.MaxMipMapLevel = -1;
        encoder.OutputOptions.Quality = CompressionQuality.Fast;
        byte[][] mips = encoder.EncodeToRawBytes(mapped, w, h, PixelFormat.Rgba32);

        int expected = 1 + (int)Math.Floor(Math.Log2(Math.Max(w, h)));
        if (mips.Length != expected) throw new InvalidDataException($"mip count {mips.Length}, Unity expects {expected}");
        var data = new byte[mips.Sum(m => m.Length)];
        int o = 0;
        foreach (var m in mips) { Buffer.BlockCopy(m, 0, data, o, m.Length); o += m.Length; }
        PaintCache.Write(root, key, name, w, h, mips.Length, PaintCache.FormatDxt5, sw, sh, data);
    }

    /// <summary>Box-filter downscale (BGRA in, RGBA out).</summary>
    private static byte[] Downscale(byte[] bgra, int sw, int sh, int w, int h)
    {
        var o = new byte[w * h * 4];
        double fx = (double)sw / w, fy = (double)sh / h;
        Parallel.For(0, h, y =>
        {
            int y0 = (int)(y * fy), y1 = Math.Max(y0 + 1, (int)((y + 1) * fy));
            for (int x = 0; x < w; x++)
            {
                int x0 = (int)(x * fx), x1 = Math.Max(x0 + 1, (int)((x + 1) * fx));
                int b = 0, g = 0, r = 0, a = 0, n = 0;
                for (int yy = y0; yy < y1 && yy < sh; yy++)
                    for (int xx = x0; xx < x1 && xx < sw; xx++)
                    {
                        int i = (yy * sw + xx) * 4;
                        b += bgra[i]; g += bgra[i + 1]; r += bgra[i + 2]; a += bgra[i + 3]; n++;
                    }
                int j = (y * w + x) * 4;
                o[j] = (byte)(r / n); o[j + 1] = (byte)(g / n); o[j + 2] = (byte)(b / n); o[j + 3] = (byte)(a / n);
            }
        });
        return o;
    }

    private static byte Hex(string hex, int at) => Convert.ToByte(hex.Substring(at, 2), 16);

    /// <summary>Decodes one texture of the faction bundle, downscaled; RGBA rows bottom-up. Null if absent.</summary>
    public static (byte[] rgba, int w, int h)? DecodeTexture(string gameDir, string faction, string textureName, int max)
    {
        var bundle = BundlePath(gameDir, faction);
        if (!File.Exists(bundle)) return null;
        var am = new AssetsManager();
        var bun = am.LoadBundleFile(bundle);
        for (int d = 0; d < bun.file.BlockAndDirInfo.DirectoryInfos.Count; d++)
        {
            AssetsFileInstance af;
            try { af = am.LoadAssetsFileFromBundle(bun, d); } catch { continue; }
            if (af == null) continue;
            foreach (var info in af.file.GetAssetsOfType(AssetClassID.Texture2D))
            {
                AssetTypeValueField bf;
                try { bf = am.GetBaseField(af, info); } catch { continue; }
                if (bf["m_Name"].AsString != textureName) continue;
                var tf = TextureFile.ReadTextureFile(bf);
                var bgra = tf.DecodeTextureRaw(tf.FillPictureData(af));
                if (bgra == null) return null;
                PaintCache.TargetSize(tf.m_Width, tf.m_Height, max, out int w, out int h);
                return (Downscale(bgra, tf.m_Width, tf.m_Height, w, h), w, h);
            }
        }
        return null;
    }

    /// <summary>A few of the faction's unit albedos for the Scheme Creator preview (largest first).</summary>
    public static List<(string name, (byte[] rgba, int w, int h) tex)> SampleTextures(string gameDir, string faction, int count, int max)
    {
        var result = new List<(string, (byte[], int, int))>();
        var bundle = BundlePath(gameDir, faction);
        if (!File.Exists(bundle)) return result;
        var am = new AssetsManager();
        var bun = am.LoadBundleFile(bundle);
        var textures = UnitTextures(am, bun)
            .Select(t => (t.file, t.info, t.name, size: (long)t.info.ByteSize))
            .OrderByDescending(t => t.name.Contains("_INT_") || t.name.Contains("_TER_") || t.name.Contains("_CAP_"))
            .ThenByDescending(t => t.size)
            .Take(count);
        foreach (var (file, info, name, _) in textures)
        {
            try
            {
                var tf = TextureFile.ReadTextureFile(am.GetBaseField(file, info));
                var bgra = tf.DecodeTextureRaw(tf.FillPictureData(file));
                if (bgra == null) continue;
                PaintCache.TargetSize(tf.m_Width, tf.m_Height, max, out int w, out int h);
                result.Add((name, (Downscale(bgra, tf.m_Width, tf.m_Height, w, h), w, h)));
            }
            catch { }
        }
        return result;
    }

    /// <summary>Folders in the cache that no current scheme uses (old colours).</summary>
    public static int Prune(string gameDir, IEnumerable<string> keepKeys)
    {
        var root = CacheRoot(gameDir);
        if (!Directory.Exists(root)) return 0;
        var keep = new HashSet<string>(keepKeys.Select(k => Path.GetFileName(PaintCache.Folder(root, k))));
        int removed = 0;
        foreach (var dir in Directory.GetDirectories(root))
        {
            if (keep.Contains(Path.GetFileName(dir))) continue;
            try { Directory.Delete(dir, true); removed++; } catch { }
        }
        return removed;
    }
}
