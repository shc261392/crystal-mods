using System;
using System.Collections.Generic;

namespace Warpstorm.Shared
{
    /// <summary>
    /// Army Painter's recolour algorithm, free of Unity types so the plugin and
    /// the configurator's preview run the exact same code (compiled into both).
    ///
    /// Pixels are RGBA bytes (4 per pixel). Per texture we detect the two dominant
    /// saturated hue clusters (primary / secondary paint) and move pixels near
    /// those hues toward the chosen colours. Hue is replaced; saturation and value
    /// are scaled by target/cluster ratios so baked shading survives while dark,
    /// light and near-grey targets (black, white, bone, gunmetal) also work.
    /// </summary>
    public static class PaintMath
    {
        public struct Cluster
        {
            public float Hue;   // 0..1
            public float Sat;   // mean saturation of the cluster's pixels
            public float Val;   // mean value of the cluster's pixels
            public int Count;
        }

        public static void RgbToHsv(float r, float g, float b, out float h, out float s, out float v)
        {
            float max = Math.Max(r, Math.Max(g, b));
            float min = Math.Min(r, Math.Min(g, b));
            float d = max - min;
            v = max;
            s = max <= 0f ? 0f : d / max;
            if (d <= 0f) { h = 0f; return; }
            if (max == r) h = (g - b) / d + (g < b ? 6f : 0f);
            else if (max == g) h = (b - r) / d + 2f;
            else h = (r - g) / d + 4f;
            h /= 6f;
        }

        public static void HsvToRgb(float h, float s, float v, out float r, out float g, out float b)
        {
            h = (h % 1f + 1f) % 1f * 6f;
            int i = (int)Math.Floor(h);
            float f = h - i;
            float p = v * (1f - s);
            float q = v * (1f - s * f);
            float t = v * (1f - s * (1f - f));
            switch (i % 6)
            {
                case 0: r = v; g = t; b = p; break;
                case 1: r = q; g = v; b = p; break;
                case 2: r = p; g = v; b = t; break;
                case 3: r = p; g = q; b = v; break;
                case 4: r = t; g = p; b = v; break;
                default: r = v; g = p; b = q; break;
            }
        }

        public static float HueDist(float a, float b)
        {
            float d = Math.Abs(a - b);
            return Math.Min(d, 1f - d);
        }

        private static float LerpHue(float a, float b, float t)
        {
            float d = b - a;
            if (d > 0.5f) d -= 1f;
            if (d < -0.5f) d += 1f;
            return ((a + d * t) % 1f + 1f) % 1f;
        }

        private static float Clamp01(float x) => x < 0f ? 0f : (x > 1f ? 1f : x);

        /// <summary>Finds the primary and (optional) secondary paint clusters.</summary>
        public static void Detect(byte[] rgba, float satThreshold, out Cluster pri, out Cluster sec, out bool hasSec)
        {
            const int Bins = 60;
            var hist = new int[Bins];
            var sumS = new float[Bins];
            var sumV = new float[Bins];
            int pixels = rgba.Length / 4;
            int stride = Math.Max(1, pixels / 20000);
            int n = 0;
            for (int p = 0; p < pixels; p += stride)
            {
                int i = p * 4;
                if (rgba[i + 3] < 16) continue;
                RgbToHsv(rgba[i] / 255f, rgba[i + 1] / 255f, rgba[i + 2] / 255f, out float h, out float s, out float v);
                if (s < satThreshold) continue;
                int bin = (int)(h * Bins) % Bins;
                hist[bin]++;
                sumS[bin] += s;
                sumV[bin] += v;
                n++;
            }

            pri = default; sec = default; hasSec = false;
            if (n == 0) return;

            int peak = 0;
            for (int i = 1; i < Bins; i++) if (hist[i] > hist[peak]) peak = i;
            pri = MakeCluster(peak, hist, sumS, sumV, Bins);

            int guard = Math.Max(2, (int)Math.Round(Bins * 0.08f));
            int secBin = -1, secCount = 0;
            for (int i = 0; i < Bins; i++)
            {
                int d = Math.Min(Math.Abs(i - peak), Bins - Math.Abs(i - peak));
                if (d <= guard) continue;
                if (hist[i] > secCount) { secCount = hist[i]; secBin = i; }
            }
            if (secBin >= 0 && secCount >= Math.Max(3, n / 40))
            {
                sec = MakeCluster(secBin, hist, sumS, sumV, Bins);
                hasSec = true;
            }
        }

        private static Cluster MakeCluster(int bin, int[] hist, float[] sumS, float[] sumV, int bins)
        {
            // Average the neighbourhood so S/V reflect the whole paint area.
            int count = 0; float s = 0f, v = 0f;
            for (int o = -2; o <= 2; o++)
            {
                int b = ((bin + o) % bins + bins) % bins;
                count += hist[b]; s += sumS[b]; v += sumV[b];
            }
            return new Cluster
            {
                Hue = (bin + 0.5f) / bins,
                Sat = count > 0 ? s / count : 0.5f,
                Val = count > 0 ? v / count : 0.5f,
                Count = hist[bin],
            };
        }

        /// <summary>
        /// One recolour rule: pixels whose hue is within <see cref="HueWidth"/> of
        /// <see cref="Hue"/> (feathered) and saturation >= <see cref="SatMin"/> get
        /// the target colour's hue, with saturation/value scaled by target/source
        /// means so the baked shading survives.
        /// </summary>
        public sealed class Rule
        {
            public float Hue;               // 0..1 source hue centre
            public float HueWidth = 0.08f;  // half-width of the band
            public float Feather = 0.04f;   // soft edge outside the band
            public float SatMin = 0.10f;    // greys below are left alone
            public float ValMin = 0f, ValMax = 1f;
            public byte R, G, B;            // target colour
            public float SatScale = 1f, ValScale = 1f;
            // Source means; computed from the image when <= 0.
            public float SrcSat = -1f, SrcVal = -1f;
        }

        /// <summary>Weight (0..1) of a pixel for a rule.</summary>
        private static float Weight(Rule r, float h, float s, float v)
        {
            if (s < r.SatMin || v < r.ValMin || v > r.ValMax) return 0f;
            float d = HueDist(h, r.Hue);
            if (d <= r.HueWidth) return 1f;
            if (r.Feather <= 0f || d >= r.HueWidth + r.Feather) return 0f;
            return 1f - (d - r.HueWidth) / r.Feather;
        }

        /// <summary>Applies <paramref name="rules"/> (first strongest wins) into a new buffer.</summary>
        public static byte[] ApplyRules(byte[] rgba, IList<Rule> rules)
        {
            var outp = new byte[rgba.Length];
            Buffer.BlockCopy(rgba, 0, outp, 0, rgba.Length);
            if (rules == null || rules.Count == 0) return outp;

            // Source means per rule (sampled) for rules that do not fix them.
            int n = rules.Count;
            var sumS = new float[n]; var sumV = new float[n]; var cnt = new int[n];
            int pixels = rgba.Length / 4;
            int stride = Math.Max(1, pixels / 40000);
            for (int p = 0; p < pixels; p += stride)
            {
                int i = p * 4;
                if (rgba[i + 3] < 16) continue;
                RgbToHsv(rgba[i] / 255f, rgba[i + 1] / 255f, rgba[i + 2] / 255f, out float h, out float s, out float v);
                for (int k = 0; k < n; k++)
                    if (Weight(rules[k], h, s, v) >= 0.5f) { sumS[k] += s; sumV[k] += v; cnt[k]++; break; }
            }
            var tH = new float[n]; var sR = new float[n]; var vR = new float[n];
            for (int k = 0; k < n; k++)
            {
                var r = rules[k];
                RgbToHsv(r.R / 255f, r.G / 255f, r.B / 255f, out tH[k], out float ts, out float tv);
                float ms = r.SrcSat > 0 ? r.SrcSat : (cnt[k] > 0 ? sumS[k] / cnt[k] : 0.5f);
                float mv = r.SrcVal > 0 ? r.SrcVal : (cnt[k] > 0 ? sumV[k] / cnt[k] : 0.5f);
                sR[k] = ts / Math.Max(0.05f, ms) * r.SatScale;
                vR[k] = tv / Math.Max(0.05f, mv) * r.ValScale;
            }

            for (int i = 0; i < rgba.Length; i += 4)
            {
                if (rgba[i + 3] < 16) continue;
                RgbToHsv(rgba[i] / 255f, rgba[i + 1] / 255f, rgba[i + 2] / 255f, out float h, out float s, out float v);
                int best = -1; float bw = 0f;
                for (int k = 0; k < n; k++)
                {
                    float w = Weight(rules[k], h, s, v);
                    if (w > bw) { bw = w; best = k; if (w >= 1f) break; }
                }
                if (best < 0) continue;

                float nS = Clamp01(s * sR[best]);
                float nV = Clamp01(v * vR[best]);
                float newH = LerpHue(h, tH[best], bw);
                float newS = s + (nS - s) * bw;
                float newV = v + (nV - v) * bw;
                HsvToRgb(newH, newS, newV, out float rr, out float gg, out float bb);
                outp[i] = (byte)Math.Round(Clamp01(rr) * 255f);
                outp[i + 1] = (byte)Math.Round(Clamp01(gg) * 255f);
                outp[i + 2] = (byte)Math.Round(Clamp01(bb) * 255f);
            }
            return outp;
        }

        /// <summary>Automatic mode: two rules from the detected primary/secondary clusters.</summary>
        public static List<Rule> AutoRules(byte[] rgba,
                                           byte priR, byte priG, byte priB,
                                           byte secR, byte secG, byte secB,
                                           float hueWindow, float satThreshold, float feather)
        {
            Detect(rgba, satThreshold, out var pc, out var sc, out bool hasSec);
            var rules = new List<Rule>();
            if (pc.Count == 0) return rules;
            float win = Math.Max(0.03f, Math.Min(0.5f, hueWindow));
            float fe = Math.Max(0f, Math.Min(win, feather));
            rules.Add(new Rule { Hue = pc.Hue, HueWidth = win - fe, Feather = fe, SatMin = satThreshold, R = priR, G = priG, B = priB, SrcSat = pc.Sat, SrcVal = pc.Val });
            if (hasSec)
                rules.Add(new Rule { Hue = sc.Hue, HueWidth = win - fe, Feather = fe, SatMin = satThreshold, R = secR, G = secG, B = secB, SrcSat = sc.Sat, SrcVal = sc.Val });
            return rules;
        }

        /// <summary>Recolours <paramref name="rgba"/> into a new buffer (automatic mode). Targets are 0..255 RGB.</summary>
        public static byte[] Remap(byte[] rgba,
                                   byte priR, byte priG, byte priB,
                                   byte secR, byte secG, byte secB,
                                   float hueWindow, float satThreshold, float feather)
            => ApplyRules(rgba, AutoRules(rgba, priR, priG, priB, secR, secG, secB, hueWindow, satThreshold, feather));

        /// <summary>
        /// Replaces the symbol inside a UV rect of a decal atlas with a stencil.
        /// Both buffers are RGBA with rows BOTTOM-UP (Unity order). The stencil's
        /// alpha (x its luminance) is the shape; the atlas' own symbol colour and
        /// opacity are reused so the new badge blends exactly like the old one.
        /// </summary>
        public static void StampBadge(byte[] atlas, int w, int h, float u0, float v0, float u1, float v1,
                                      byte[] stencil, int sw, int sh, float scale)
        {
            int x0 = Math.Max(0, (int)(u0 * w)), x1 = Math.Min(w, (int)Math.Ceiling(u1 * w));
            int y0 = Math.Max(0, (int)(v0 * h)), y1 = Math.Min(h, (int)Math.Ceiling(v1 * h));
            if (x1 <= x0 || y1 <= y0) return;

            // Old symbol's look: foreground = strongly covered pixels, background = empty ones.
            double fr = 0, fg = 0, fb = 0, fa = 0, br = 0, bg = 0, bb = 0; int nf = 0, nb = 0;
            for (int y = y0; y < y1; y++)
                for (int x = x0; x < x1; x++)
                {
                    int i = (y * w + x) * 4;
                    if (atlas[i + 3] > 100) { fr += atlas[i]; fg += atlas[i + 1]; fb += atlas[i + 2]; fa += atlas[i + 3]; nf++; }
                    else if (atlas[i + 3] < 10) { br += atlas[i]; bg += atlas[i + 1]; bb += atlas[i + 2]; nb++; }
                }
            byte FR = (byte)(nf > 0 ? fr / nf : 255), FG = (byte)(nf > 0 ? fg / nf : 255), FB = (byte)(nf > 0 ? fb / nf : 255);
            float FA = nf > 0 ? (float)(fa / nf) : 190f;
            byte BR = (byte)(nb > 0 ? br / nb : 0), BG = (byte)(nb > 0 ? bg / nb : 0), BB = (byte)(nb > 0 ? bb / nb : 0);

            // Fit the stencil (keep aspect) centred in the rect.
            int rw = x1 - x0, rh = y1 - y0;
            float fit = Math.Min((float)rw / sw, (float)rh / sh) * Math.Max(0.1f, Math.Min(1f, scale));
            float ox = x0 + (rw - sw * fit) / 2f, oy = y0 + (rh - sh * fit) / 2f;

            for (int y = y0; y < y1; y++)
                for (int x = x0; x < x1; x++)
                {
                    float sx = (x + 0.5f - ox) / fit, sy = (y + 0.5f - oy) / fit;
                    float cover = 0f;
                    if (sx >= 0 && sy >= 0 && sx < sw && sy < sh)
                    {
                        int si = ((int)sy * sw + (int)sx) * 4;
                        float lum = (stencil[si] + stencil[si + 1] + stencil[si + 2]) / (3f * 255f);
                        cover = stencil[si + 3] / 255f * lum;
                    }
                    int i = (y * w + x) * 4;
                    atlas[i] = (byte)(BR + (FR - BR) * cover);
                    atlas[i + 1] = (byte)(BG + (FG - BG) * cover);
                    atlas[i + 2] = (byte)(BB + (FB - BB) * cover);
                    atlas[i + 3] = (byte)(FA * cover);
                }
        }
    }
}
