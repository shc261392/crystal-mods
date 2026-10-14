using System;
using System.Collections.Generic;
using System.IO;
using BepInEx;
using BepInEx.Logging;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.LowLevel;

namespace BlackBookTcFont
{
    /// <summary>
    /// Traditional Chinese support for Black Book, in two parts:
    ///
    /// 1. GLYPHS. The game renders Chinese from static SDF atlases baked from
    ///    its own Simplified text, so characters that only exist in Traditional
    ///    Chinese (說, 們, 沒, 裡, 讎 ...) have no glyph and draw as 口口口.
    ///    We build a DYNAMIC TMP font asset from the game's own font source, so
    ///    the glyphs appear and they match the game's existing serif style.
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

        /// <summary>XUnity.AutoTranslator's font bundle; covers all 20,902 CJK ideographs.</summary>
        private const string FallbackFontFile = "arialuni_sdf_u2018";
        private const string FallbackFontAsset = "ARIALUNI SDF";

        internal static ManualLogSource Log;

        private static readonly List<TMP_FontAsset> Fallbacks = new List<TMP_FontAsset>();
        private static TMP_FontAsset _gameSerif;
        private static TMP_FontAsset _wideCoverage;

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

            LoadFonts();

            SceneManager.sceneLoaded += OnSceneLoaded;
            Apply("startup");
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode) => Apply(scene.name);

        private void Apply(string where)
        {
            int converted = TextLocalizer.ConvertAll(_converter, Log);
            if (converted > 0)
                Log.LogInfo($"[{where}] converted {converted} localised string(s) to Traditional.");

            ApplyFontFallback(where);
        }

        // ------------------------------------------------------------------ //
        // Fonts
        // ------------------------------------------------------------------ //

        private void LoadFonts()
        {
            _gameSerif = BuildDynamicFromGameSource();
            if (_gameSerif != null)
                Log.LogInfo($"Built dynamic font from game source '{_gameSerif.sourceFontFile?.name}'.");

            _wideCoverage = LoadBundleFont();
            if (_wideCoverage != null)
                Log.LogInfo($"Loaded fallback font '{_wideCoverage.name}'.");

            Fallbacks.Clear();
            // Order matters: TMP searches fallbacks in sequence, so the serif
            // (correct style) is tried first and the wide font catches the few
            // characters it lacks.
            if (_gameSerif != null) Fallbacks.Add(_gameSerif);
            if (_wideCoverage != null) Fallbacks.Add(_wideCoverage);

            if (Fallbacks.Count == 0)
                Log.LogError("No usable font found; Traditional glyphs will still show as tofu.");
        }

        /// <summary>
        /// Create a dynamic font asset from one of the game's own fonts. A
        /// dynamic asset rasterises glyphs on demand from the source Font, so it
        /// covers far more characters than the game's static atlases - in the
        /// game's own face.
        /// </summary>
        private static TMP_FontAsset BuildDynamicFromGameSource()
        {
            TMP_FontAsset[] fonts;
            try
            {
                fonts = Resources.FindObjectsOfTypeAll<TMP_FontAsset>();
            }
            catch (Exception e)
            {
                Log.LogWarning($"Could not enumerate TMP fonts: {e.Message}");
                return null;
            }

            foreach (TMP_FontAsset font in fonts)
            {
                if (font == null) continue;

                Font source;
                try
                {
                    source = font.sourceFontFile;
                }
                catch
                {
                    continue;
                }
                if (source == null) continue;

                try
                {
                    TMP_FontAsset dynamicAsset = TMP_FontAsset.CreateFontAsset(
                        source, 90, 9, GlyphRenderMode.SDFAA, 1024, 1024,
                        AtlasPopulationMode.Dynamic, true);

                    if (dynamicAsset == null) continue;

                    // Only accept it if it can actually draw Traditional text.
                    if (dynamicAsset.HasCharacter('說') && dynamicAsset.HasCharacter('裡'))
                    {
                        Log.LogInfo($"  candidate '{font.name}' (source '{source.name}') covers Traditional.");
                        return dynamicAsset;
                    }

                    Destroy(dynamicAsset);
                }
                catch (Exception e)
                {
                    Log.LogWarning($"  font '{font.name}' could not be rebuilt dynamically: {e.Message}");
                }
            }
            return null;
        }

        private static TMP_FontAsset LoadBundleFont()
        {
            string path = Path.Combine(Paths.GameRootPath, FallbackFontFile);
            if (!File.Exists(path)) return null;

            try
            {
                AssetBundle bundle = AssetBundle.LoadFromFile(path);
                if (bundle == null) return null;

                TMP_FontAsset asset = bundle.LoadAsset<TMP_FontAsset>(FallbackFontAsset);
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
                Log.LogWarning($"Could not load {FallbackFontFile}: {e.Message}");
                return null;
            }
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
        }
    }
}