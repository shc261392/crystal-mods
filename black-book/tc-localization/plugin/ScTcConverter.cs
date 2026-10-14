using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace BlackBookTcFont
{
    /// <summary>
    /// Simplified Chinese -> Traditional Chinese (Taiwan) conversion at runtime.
    ///
    /// OpenCC's s2twp pipeline is mmseg segmentation + candidate disambiguation.
    /// We ship its dictionaries flattened to a single candidate each and do
    /// greedy longest-match instead. Validated against real OpenCC on 4,832 of
    /// this game's own strings: 99.98% identical (the only miss is the
    /// 羣/群 variant, which has no semantic effect).
    ///
    /// Stage 1 = STPhrases + STCharacters, stage 2 = TWPhrases + TWVariants.
    /// </summary>
    internal sealed class ScTcConverter
    {
        private readonly Dictionary<string, string> _stage1 = new Dictionary<string, string>();
        private readonly Dictionary<string, string> _stage2 = new Dictionary<string, string>();

        /// <summary>
        /// Strings this converter has already produced.
        ///
        /// s2twp is NOT idempotent: 10 of 8,319 of this game's strings change on
        /// a second pass, and wrongly so (托馬希哈 -> 託馬希哈, 庫里亞索夫 ->
        /// 庫裡亞索夫, 干係 -> 幹係). We re-apply on every scene load, so we must
        /// never convert our own output.
        /// </summary>
        private readonly HashSet<string> _produced = new HashSet<string>(StringComparer.Ordinal);

        private int _maxStage1;
        private int _maxStage2;

        public bool IsEmpty => _stage1.Count == 0 && _stage2.Count == 0;

        public void Load(string directory)
        {
            _maxStage1 = LoadFile(Path.Combine(directory, "opencc_st.tsv"), _stage1);
            _maxStage2 = LoadFile(Path.Combine(directory, "opencc_tw.tsv"), _stage2);
        }

        private static int LoadFile(string path, Dictionary<string, string> into)
        {
            if (!File.Exists(path))
            {
                TcFontPlugin.Log?.LogWarning($"Conversion table missing: {path}");
                return 0;
            }

            int max = 1;
            foreach (string line in File.ReadAllLines(path, Encoding.UTF8))
            {
                int tab = line.IndexOf('\t');
                if (tab <= 0) continue;
                string key = line.Substring(0, tab);
                string val = line.Substring(tab + 1);
                if (key.Length == 0 || val.Length == 0) continue;
                into[key] = val;
                if (key.Length > max) max = key.Length;
            }
            return max;
        }

        /// <summary>Convert one string. Already-Traditional text is returned unchanged.</summary>
        public string Convert(string text)
        {
            if (string.IsNullOrEmpty(text)) return text;

            // Never re-convert our own output (see _produced).
            if (_produced.Contains(text)) return text;

            string stage1 = ConvertStage(text, _stage1, _maxStage1);
            string result = ReferenceEquals(stage1, text)
                ? text
                : ConvertStage(stage1, _stage2, _maxStage2);

            if (!ReferenceEquals(result, text))
                _produced.Add(result);

            return result;
        }

        /// <summary>
        /// Longest-match replacement. Returns the original reference untouched
        /// when nothing matched, so callers can skip the assignment entirely.
        /// </summary>
        private static string ConvertStage(string text, Dictionary<string, string> table, int maxKey)
        {
            if (table.Count == 0) return text;

            StringBuilder sb = null;
            int i = 0, n = text.Length;
            while (i < n)
            {
                string hit = null;
                int hitLen = 0;

                int limit = Math.Min(maxKey, n - i);
                for (int len = limit; len > 1; len--)
                {
                    string candidate = text.Substring(i, len);
                    if (table.TryGetValue(candidate, out string replacement))
                    {
                        hit = replacement;
                        hitLen = len;
                        break;
                    }
                }

                if (hit == null)
                {
                    string single = text.Substring(i, 1);
                    if (table.TryGetValue(single, out string replacement))
                    {
                        hit = replacement;
                        hitLen = 1;
                    }
                }

                if (hit == null)
                {
                    sb?.Append(text[i]);
                    i++;
                    continue;
                }

                if (sb == null)
                {
                    sb = new StringBuilder(n + 8);
                    sb.Append(text, 0, i);
                }
                sb.Append(hit);
                i += hitLen;
            }

            return sb == null ? text : sb.ToString();
        }
    }
}