using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Logging;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;

namespace BlackBookTcFont
{
    /// <summary>
    /// Traditional Chinese support for Black Book, in two parts:
    ///
    /// 1. GLYPHS. The game renders Chinese from static SDF atlases baked from
    ///    its own Simplified text, so characters that only exist in Traditional
    ///    Chinese (說, 們, 沒, 裡, 讎 ...) have no glyph and draw as 口口口.
    ///    The game's fonts are static and expose no source Font, so we cannot
    ///    rebuild them; instead we ship Noto Serif TC - the same family as the
    ///    game's own "Noto Serif SC" CJK atlases - and register a dynamic TMP
    ///    asset built from it as a fallback.
    ///
    /// 2. TEXT. Everything the game displays comes from two Dialogue System
    ///    ScriptableObjects (DialogueDatabase "BlackBook", TextTable
    ///    "UILocalization"). Their Simplified Chinese fields are converted to
    ///    Traditional in memory, on startup and after every scene load.
    ///
    /// No network access, no on-demand translation: the conversion is a pure
    /// lookup against OpenCC tables shipped with the mod.
    /// </summary>
    [BepInPlugin(Guid, "Black Book TC Font", "2.0.0")]
    public class TcFontPlugin : BaseUnityPlugin
    {
        public const string Guid = "crystaldmods.blackbook.tcfont";

        private const string DataFolder = "BlackBookTcFont";

        /// <summary>Our Unity-built Noto Serif TC font asset (see tools/unity-font).</summary>
        private const string TcBundleFile = "tcserif";
        private const string TcFontAssetName = "Iansui SDF";

        /// <summary>XUnity.AutoTranslator's font bundle; last-resort coverage.</summary>
        private const string FallbackFontFile = "arialuni_sdf_u2018";
        private const string FallbackFontAsset = "ARIALUNI SDF";

        /// <summary>Characters used to prove a candidate font is usable.</summary>
        private const string Probe = "說裡們沒這";

        internal static ManualLogSource Log;

        /// <summary>The Traditional font every Chinese text element is switched to.</summary>
        internal static TMP_FontAsset TcFont => _tcFont;

        private static readonly List<TMP_FontAsset> Fallbacks = new List<TMP_FontAsset>();
        private static TMP_FontAsset _tcFont;
        private static TMP_FontAsset _gameSourceFallback;
        private static TMP_FontAsset _wideCoverage;

        private static bool _fontsBuilt;
        private static bool _inventoryLogged;
        private static int _fontAttempts;

        /// <summary>TMP's shader is not ready during Awake, so give it a few scenes.</summary>
        private const int MaxFontAttempts = 6;

        /// <summary>How often to re-force the font on text the hooks cannot see.</summary>
        private const float SweepInterval = 2f;

        private static float _sweepAccumulator;

        private ScTcConverter _converter;

        private void Awake()
        {
            Log = Logger;

            string dataPath = Path.Combine(Paths.PluginPath, DataFolder);
            _converter = new ScTcConverter();
            _converter.Load(dataPath);
            Log.LogInfo(_converter.IsEmpty
                ? "Conversion tables did not load - text will stay Simplified."
                : "Conversion tables loaded.");

            // Route every font assignment through our font, however late the
            // game creates the text element.
            try
            {
                var harmony = new HarmonyLib.Harmony(Guid);
                harmony.PatchAll(typeof(FontPatches));
                Log.LogInfo("Patched FontService.GetFont.");
            }
            catch (Exception e)
            {
                Log.LogWarning($"Could not patch FontService ({e.Message}); "
                               + "falling back to a per-scene sweep.");
            }

            SceneManager.sceneLoaded += OnSceneLoaded;
            Apply("startup");
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode) => Apply(scene.name);

        private void Apply(string where)
        {
            int converted = TextLocalizer.ConvertAll(_converter, Log);
            if (converted > 0)
                Log.LogInfo($"[{where}] converted {converted} localised string(s) to Traditional.");

            // Fonts are built lazily: TMP's shader is not loaded during Awake,
            // so building then fails with "Parameter name: shader". Retry for a
            // few scenes, then stop rather than rebuilding on every load.
            if (!_fontsBuilt && _fontAttempts < MaxFontAttempts)
            {
                _fontAttempts++;
                if (BuildFallbackFonts(where))
                    _fontsBuilt = true;
                else if (_fontAttempts == MaxFontAttempts)
                    Log.LogError("Giving up on the Traditional font; glyphs will show as tofu.");
            }

            ApplyFontFallback(where);
        }

        // ------------------------------------------------------------------ //
        // Fonts
        // ------------------------------------------------------------------ //

        private static bool BuildFallbackFonts(string where)
        {
            if (!_inventoryLogged)
            {
                LogFontInventory();
                _inventoryLogged = true;
            }

            // The game's own fonts are static atlases baked from its Simplified
            // text: they contain no glyphs for the characters that differ in
            // Traditional Chinese, which is why a second font is unavoidable.
            // We ship one built by Unity itself (tools/unity-font) - Noto Serif
            // TC, the same family as the game's Noto Serif SC CJK atlases - and
            // make it the PRIMARY font for Chinese, so no text mixes two faces.
            _tcFont = LoadBundleFont(TcBundleFile, TcFontAssetName, DataFolder);
            if (_tcFont != null)
                Log.LogInfo($"Loaded Traditional font '{_tcFont.name}' "
                            + $"({GlyphCount(_tcFont)} characters, "
                            + $"family '{_tcFont.faceInfo.familyName}').");

            // Wider fallback for anything our subset lacks (kana, rare symbols).
            _wideCoverage = LoadBundleFont(FallbackFontFile, FallbackFontAsset, null);
            if (_wideCoverage != null)
                Log.LogInfo($"Loaded fallback font '{_wideCoverage.name}'.");

            // The game's own Noto Serif, used to fill any remaining gaps.
            _gameSourceFallback = BuildFromGameFonts();

            Fallbacks.Clear();
            if (_tcFont != null) Fallbacks.Add(_tcFont);
            if (_gameSourceFallback != null) Fallbacks.Add(_gameSourceFallback);
            if (_wideCoverage != null) Fallbacks.Add(_wideCoverage);

            if (Fallbacks.Count == 0)
            {
                Log.LogWarning($"[{where}] no usable font yet; will retry.");
                return false;
            }

            Log.LogInfo($"[{where}] font ready: "
                        + $"{(_gameSourceFallback != null ? "'" + _gameSourceFallback.sourceFontFile?.name + "'" : "<none>")} "
                        + $"+ wide-coverage '{_wideCoverage?.name}'.");
            return true;
        }

        /// <summary>
        /// Create a TMP font asset from a Font and prove it can actually render
        /// Traditional Chinese.
        ///
        /// HasCharacter(char) will NOT do: its tryAddCharacter argument defaults
        /// to false, so a dynamic asset with an empty atlas always reports false.
        /// TryAddCharacters is what actually rasterises the glyphs.
        ///
        /// The atlas settings mirror the game's own NotoSerif CJK asset
        /// (24 pt, 2048x2048, padding 5, SDFAA) so the rebuilt glyphs carry the
        /// same stroke weight as the static atlas they sit next to.
        /// </summary>
        private static TMP_FontAsset TryCreateFontAsset(Font font, int pointSize)
        {
            TMP_FontAsset asset;
            try
            {
                asset = TMP_FontAsset.CreateFontAsset(
                    font, pointSize, 5, GlyphRenderMode.SDFAA, 2048, 2048,
                    AtlasPopulationMode.Dynamic, true);
            }
            catch (Exception e)
            {
                Log.LogWarning($"  CreateFontAsset({pointSize}) failed: {e.Message}");
                return null;
            }

            if (asset == null)
            {
                // CreateFontAsset returns null when FontEngine.LoadFontFace
                // fails, which happens for Fonts with no embedded font data.
                Log.LogWarning($"  CreateFontAsset({pointSize}) returned null for '{font.name}'.");
                return null;
            }

            try
            {
                asset.TryAddCharacters(Probe, out string missing);
                if (string.IsNullOrEmpty(missing))
                    return asset;

                Log.LogWarning($"  '{font.name}' at {pointSize} is missing '{missing}'.");
            }
            catch (Exception e)
            {
                Log.LogWarning($"  coverage check failed: {e.Message}");
            }

            Destroy(asset);
            return null;
        }

        /// <summary>
        /// Build from whatever Font the game loaded itself. Same family as the
        /// game's atlas, so the style matches even if coverage is narrower.
        /// </summary>
        private static TMP_FontAsset BuildFromGameFonts()
        {
            foreach (Font source in LoadedFonts())
            {
                TMP_FontAsset asset = TryCreateFontAsset(source, 24);
                if (asset != null)
                {
                    Log.LogInfo($"Built TMP font from game Font '{source.name}'.");
                    return asset;
                }
            }
            return null;
        }

        private static IEnumerable<Font> LoadedFonts()
        {
            Font[] fonts;
            try
            {
                fonts = Resources.FindObjectsOfTypeAll<Font>();
            }
            catch
            {
                yield break;
            }

            foreach (Font f in fonts)
                if (f != null) yield return f;
        }

        private static TMP_FontAsset LoadBundleFont(string file, string assetName, string subfolder)
        {
            string path = subfolder == null
                ? Path.Combine(Paths.GameRootPath, file)
                : Path.Combine(Paths.PluginPath, subfolder, file);
            if (!File.Exists(path))
            {
                Log.LogWarning($"Font bundle not found: {path}");
                return null;
            }

            try
            {
                AssetBundle bundle = AssetBundle.LoadFromFile(path);
                if (bundle == null)
                {
                    Log.LogWarning($"{path} is not a loadable AssetBundle");
                    return null;
                }

                TMP_FontAsset asset = bundle.LoadAsset<TMP_FontAsset>(assetName);
                if (asset == null)
                {
                    TMP_FontAsset[] all = bundle.LoadAllAssets<TMP_FontAsset>();
                    if (all != null && all.Length > 0) asset = all[0];
                }
                bundle.LoadAllAssets();
                return asset;
            }
            catch (Exception e)
            {
                Log.LogWarning($"Could not load {file}: {e.Message}");
                return null;
            }
        }

        // ------------------------------------------------------------------ //
        // Diagnostics
        // ------------------------------------------------------------------ //

        private static void LogFontInventory()
        {
            try
            {
                TMP_FontAsset[] assets = Resources.FindObjectsOfTypeAll<TMP_FontAsset>();
                Log.LogInfo($"TMP font assets in memory: {assets.Length}");
                foreach (TMP_FontAsset a in assets)
                {
                    if (a == null) continue;
                    FaceInfo face = a.faceInfo;
                    Log.LogInfo(
                        $"  '{a.name}' family='{face.familyName}' style='{face.styleName}' "
                        + $"pointSize={face.pointSize} atlas={a.atlasWidth}x{a.atlasHeight} "
                        + $"padding={a.atlasPadding} render={a.atlasRenderMode} "
                        + $"glyphs={GlyphCount(a)} "
                        + $"source={(a.sourceFontFile == null ? "<none>" : a.sourceFontFile.name)}");
                }
            }
            catch (Exception e)
            {
                Log.LogWarning($"TMP font inventory failed: {e.Message}");
            }

            try
            {
                Font[] fonts = Resources.FindObjectsOfTypeAll<Font>();
                Log.LogInfo($"Font objects in memory: {fonts.Length}");
                foreach (Font f in fonts)
                {
                    if (f == null) continue;
                    Log.LogInfo($"  '{f.name}' dynamic={f.dynamic}");
                }
            }
            catch (Exception e)
            {
                Log.LogWarning($"Font inventory failed: {e.Message}");
            }
        }

        /// <summary>
        /// Glyph count for logging only. Modern TMP keeps characters in
        /// m_CharacterTable; m_glyphInfoList is the legacy field and is often
        /// present but empty, so it must not be checked first.
        /// </summary>
        private static int GlyphCount(TMP_FontAsset asset)
        {
            try
            {
                Type type = asset.GetType();
                const System.Reflection.BindingFlags Flags =
                    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;

                System.Reflection.FieldInfo modern = type.GetField("m_CharacterTable", Flags);
                if (modern?.GetValue(asset) is System.Collections.ICollection table)
                    return table.Count;

                System.Reflection.FieldInfo legacy = type.GetField("m_glyphInfoList", Flags);
                if (legacy?.GetValue(asset) is System.Collections.ICollection list)
                    return list.Count;
            }
            catch
            {
                // Informational only.
            }
            return 0;
        }

        private static void ApplyFontFallback(string where)
        {
            if (Fallbacks.Count == 0) return;

            TMP_FontAsset[] fonts;
            try
            {
                fonts = Resources.FindObjectsOfTypeAll<TMP_FontAsset>();
            }
            catch
            {
                return;
            }

            int patched = 0;
            foreach (TMP_FontAsset font in fonts)
            {
                if (font == null) continue;
                if (Fallbacks.Contains(font)) continue;

                if (font.fallbackFontAssetTable == null)
                    font.fallbackFontAssetTable = new List<TMP_FontAsset>();

                foreach (TMP_FontAsset fallback in Fallbacks)
                {
                    if (font == fallback) continue;
                    if (!font.fallbackFontAssetTable.Contains(fallback))
                    {
                        font.fallbackFontAssetTable.Add(fallback);
                        patched++;
                    }
                }
            }

            if (patched > 0)
                Log.LogInfo($"[{where}] added Traditional fallback to {patched} font asset(s).");

            // Serialized fonts cannot be reached by any hook, so sweep
            // periodically rather than only on scene load.
            ScheduleSweep();
        }

        /// <summary>Keep <paramref name="original"/> reachable from our font.</summary>
        internal static void KeepReachable(TMP_FontAsset original)
        {
            if (_tcFont == null || original == null || original == _tcFont) return;
            try
            {
                if (_tcFont.fallbackFontAssetTable == null)
                    _tcFont.fallbackFontAssetTable = new List<TMP_FontAsset>();
                if (!_tcFont.fallbackFontAssetTable.Contains(original))
                    _tcFont.fallbackFontAssetTable.Add(original);
            }
            catch
            {
                // Purely a safety net; never let it break font assignment.
            }
        }

        private static bool _sweepQueued;

        /// <summary>Re-run the sweep from Update() while the game is running.</summary>
        private static void ScheduleSweep() => _sweepQueued = true;

        private void Update()
        {
            if (!_sweepQueued || _tcFont == null) return;
            _sweepQueued = false;
            _sweepAccumulator += Time.unscaledDeltaTime;
            if (_sweepAccumulator < SweepInterval) { _sweepQueued = true; return; }
            _sweepAccumulator = 0f;
            ForceFontOnAllText();
            _sweepQueued = true;
        }

        /// <summary>
        /// Point every text element at our font.
        ///
        /// A fallback is not enough: TMP only consults fallbacks for characters
        /// the primary font is missing, so the game's own glyphs win and the
        /// screen mixes two faces. Making ours primary means one face everywhere.
        /// </summary>
        private static void ForceFontOnAllText()
        {
            TMP_Text[] texts;
            try
            {
                texts = Resources.FindObjectsOfTypeAll<TMP_Text>();
            }
            catch
            {
                return;
            }

            int forced = 0;
            foreach (TMP_Text text in texts)
            {
                if (text == null) continue;
                TMP_FontAsset current = text.font;
                if (current == null || current == _tcFont) continue;

                KeepReachable(current);
                text.font = _tcFont;
                forced++;
            }

            // Log the first sweep so the log shows the mechanism working, then
            // stay quiet to avoid flooding it twice a second.
            if (!_sweepLogged)
            {
                _sweepLogged = true;
                Log.LogInfo($"[sweep] found {texts.Length} text element(s), "
                            + $"forced '{_tcFont.name}' onto {forced}.");
            }
        }

        private static bool _sweepLogged;

        /// <summary>Does this font contain any CJK, i.e. is it a Chinese face?</summary>
        private static bool HasCjkCoverage(TMP_FontAsset font)
        {
            try
            {
                // Static assets answer from their lookup table with no side effect.
                return font.HasCharacter('一') && font.HasCharacter('口');
            }
            catch
            {
                return false;
            }
        }
    }
}