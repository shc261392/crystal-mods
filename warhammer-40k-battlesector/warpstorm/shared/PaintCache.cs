using System;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Warpstorm.Shared
{
    /// <summary>
    /// Pre-painted textures on disk, shared by the configurator ("Bake") and the
    /// plugin (load instantly; also fills the cache itself on a miss).
    ///
    ///   BepInEx/cache/warpstorm/paint/&lt;hash(scheme key)&gt;/key.txt
    ///   BepInEx/cache/warpstorm/paint/&lt;hash(scheme key)&gt;/&lt;texture name&gt;.wpt
    ///
    /// .wpt = "WPT1", int width, int height, int mipCount, int format (12 = DXT5),
    ///        int sourceWidth, int sourceHeight, then the raw Unity texture data
    ///        (mip 0 first, rows bottom-up as Texture2D.LoadRawTextureData wants).
    /// </summary>
    public static class PaintCache
    {
        /// <summary>Bump when PaintMath / the bake pipeline changes output.</summary>
        public const int Version = 1;
        public const int FormatDxt5 = 12;
        private static readonly byte[] Magic = { (byte)'W', (byte)'P', (byte)'T', (byte)'1' };

        private static string F(float v) => v.ToString("0.####", CultureInfo.InvariantCulture);

        /// <summary>Identity of a faction's paint job. Must be built identically everywhere.</summary>
        public static string SchemeKey(string faction, SchemePack pack, string priHex, string secHex,
                                       float hueWindow, float satThreshold, float feather, int maxSize)
            => pack != null
                ? $"v{Version}|{faction}|pack:{pack.Id}@{pack.Version}|max{maxSize}"
                : $"v{Version}|{faction}|{priHex.ToUpperInvariant()}{secHex.ToUpperInvariant()}|{F(hueWindow)}|{F(satThreshold)}|{F(feather)}|max{maxSize}";

        public static string Folder(string root, string schemeKey)
        {
            using var sha = SHA1.Create();
            var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(schemeKey));
            var sb = new StringBuilder();
            for (int i = 0; i < 8; i++) sb.Append(hash[i].ToString("x2"));
            return Path.Combine(root, sb.ToString());
        }

        public static string FilePath(string root, string schemeKey, string textureName)
            => Path.Combine(Folder(root, schemeKey), Safe(textureName) + ".wpt");

        private static string Safe(string name)
        {
            var chars = name.ToCharArray();
            var bad = Path.GetInvalidFileNameChars();
            for (int i = 0; i < chars.Length; i++) if (Array.IndexOf(bad, chars[i]) >= 0) chars[i] = '_';
            return new string(chars);
        }

        /// <summary>Writes atomically (temp file + rename) so a running game never reads half a file.</summary>
        public static void Write(string root, string schemeKey, string textureName,
                                 int width, int height, int mips, int format, int srcW, int srcH, byte[] data)
        {
            var dir = Folder(root, schemeKey);
            Directory.CreateDirectory(dir);
            var keyFile = Path.Combine(dir, "key.txt");
            if (!File.Exists(keyFile)) File.WriteAllText(keyFile, schemeKey);
            var path = FilePath(root, schemeKey, textureName);
            var tmp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            using (var fs = File.Create(tmp))
            using (var w = new BinaryWriter(fs))
            {
                w.Write(Magic);
                w.Write(width); w.Write(height); w.Write(mips); w.Write(format); w.Write(srcW); w.Write(srcH);
                w.Write(data);
            }
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmp, path);
        }

        public static bool TryRead(string root, string schemeKey, string textureName,
                                   out int width, out int height, out int mips, out int format,
                                   out int srcW, out int srcH, out byte[] data)
        {
            width = height = mips = format = srcW = srcH = 0;
            data = null;
            var path = FilePath(root, schemeKey, textureName);
            if (!File.Exists(path)) return false;
            try
            {
                var bytes = File.ReadAllBytes(path);
                if (bytes.Length < 28 || bytes[0] != Magic[0] || bytes[1] != Magic[1] || bytes[2] != Magic[2] || bytes[3] != Magic[3]) return false;
                width = BitConverter.ToInt32(bytes, 4);
                height = BitConverter.ToInt32(bytes, 8);
                mips = BitConverter.ToInt32(bytes, 12);
                format = BitConverter.ToInt32(bytes, 16);
                srcW = BitConverter.ToInt32(bytes, 20);
                srcH = BitConverter.ToInt32(bytes, 24);
                data = new byte[bytes.Length - 28];
                Buffer.BlockCopy(bytes, 28, data, 0, data.Length);
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>Target size for a source texture (same rule in bake and game).</summary>
        public static void TargetSize(int srcW, int srcH, int maxSize, out int w, out int h)
        {
            float scale = Math.Min(1f, (float)maxSize / Math.Max(srcW, srcH));
            w = Math.Max(4, (int)Math.Round(srcW * scale) & ~3);
            h = Math.Max(4, (int)Math.Round(srcH * scale) & ~3);
        }

        public static long SizeOnDisk(string root)
        {
            if (!Directory.Exists(root)) return 0;
            long total = 0;
            foreach (var f in Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)) total += new FileInfo(f).Length;
            return total;
        }
    }
}
