// Batch-mode font asset builder for the Black Book Traditional Chinese mod.
//
// Run (from tools/unity-font, with the editor installed):
//   "D:\Unity\2018.4.31f1\Editor\Unity.exe" -batchmode -quit -nographics \
//       -projectPath "<abs path to tools/unity-font>" \
//       -executeMethod BuildTcFont.Build -logFile -
//
// Why Unity: TMP font assets cannot be produced offline. The game's own fonts
// are static atlases with no source Font, so a replacement has to be generated
// by the same engine that built the game - Unity 2018.4.31f1 (changeset
// 212ea663d844), which is exactly Black Book's build, so the asset format
// matches TMP 1.4.1 as shipped in the game.
//
// Font: Iansui (芫荽), a zh-TW face under SIL OFL.
// Output: a single AssetBundle containing a STATIC TMP font asset (plus its
// atlas textures, material and the TMP shaders), so no source Font is needed at
// runtime and the plugin can simply load and register it.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;

public static class BuildTcFont
{
    private const string FontPath = "Assets/Fonts/Iansui-Regular.ttf";
    private const string CharsetPath = "Assets/Fonts/charset.txt";
    private const string AssetDir = "Assets/Generated";
    private const string AssetPath = AssetDir + "/Iansui SDF.asset";
    private const string BundleName = "tcserif";

    // Point size and padding match the game's own NotoSerif CJK asset, so
    // stroke weight is identical to the static atlas the new glyphs sit beside.
    // The atlas is larger than the game's 2048 because TMP 1.4.1 has no
    // multi-atlas support and ~4,300 glyphs do not fit in a single 2048 tile.
    private const int PointSize = 24;
    private const int Padding = 5;
    private const int AtlasWidth = 4096;
    private const int AtlasHeight = 4096;

    [MenuItem("Black Book/Build TC Font Asset")]
    public static void BuildMenu() => Build();

    public static void Build()
    {
        EnsureTmpResources();

        try
        {
            AssetDatabase.StartAssetEditing();
            ImportFont();
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
            AssetDatabase.Refresh();
        }

        Font font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
        if (font == null)
        {
            Fail($"Could not load {FontPath}");
            return;
        }

        Debug.Log($"[BuildTcFont] source font '{font.name}' dynamic={font.dynamic}");

        // CreateFontAsset only succeeds when the Font carries embedded data
        // ("Include Font Data"); a Font with none makes FontEngine.LoadFontFace
        // fail and this returns null.
        TMP_FontAsset tmp = TMP_FontAsset.CreateFontAsset(
            font, PointSize, Padding, GlyphRenderMode.SDFAA,
            AtlasWidth, AtlasHeight, AtlasPopulationMode.Dynamic);

        if (tmp == null)
        {
            Fail("CreateFontAsset returned null - is \"Include Font Data\" enabled on the TTF?");
            return;
        }

        tmp.name = "Iansui SDF";

        string charset = File.ReadAllText(CharsetPath);
        Debug.Log($"[BuildTcFont] font settings: pointSize={tmp.faceInfo.pointSize} "
                  + $"padding={tmp.atlasPadding} atlas={tmp.atlasWidth}x{tmp.atlasHeight} "
                  + $"render={tmp.atlasRenderMode} mode={tmp.atlasPopulationMode}");

        // Populate in chunks. TMP 1.4.1's TryAddCharacters is all-or-nothing: the
        // AtlasPopulationMode of a failed native pack leaves `glyphs` null and it
        // dereferences it unguarded (TMP_FontAsset.cs:1242), so one bad batch
        // aborts the whole build. Chunking localises any failure, and a chunk
        // that throws is retried one character at a time so a single bad glyph
        // cannot cost us the rest.
        // TMP creates the atlas as a 0x0 texture and resizes it lazily inside
        // TryAddCharacters. When that lazy resize does not take, native packing
        // returns an array of NULL Glyph objects and TMP crashes dereferencing
        // them - which is what produced "added 0 characters". Force the atlas to
        // full size up front instead of relying on the lazy path.
        if (tmp.atlasTextures != null && tmp.atlasTextures.Length > 0)
        {
            Texture2D atlas = tmp.atlasTextures[0];
            if (atlas == null)
            {
                atlas = new Texture2D(tmp.atlasWidth, tmp.atlasHeight,
                                      TextureFormat.Alpha8, false);
                tmp.atlasTextures[0] = atlas;
            }
            if (atlas.width != tmp.atlasWidth || atlas.height != tmp.atlasHeight)
                atlas.Resize(tmp.atlasWidth, tmp.atlasHeight);
            atlas.Apply(false, false);
            Debug.Log($"[BuildTcFont] atlas texture forced to {atlas.width}x{atlas.height}");
        }

        const int ChunkSize = 512;
        List<char> distinct = charset.Distinct().ToList();
        Debug.Log($"[BuildTcFont] populating {distinct.Count} distinct characters in "
                  + $"chunks of {ChunkSize}...");

        var missing = new System.Text.StringBuilder();
        int added = 0;

        for (int offset = 0; offset < distinct.Count; offset += ChunkSize)
        {
            string part = new string(distinct.Skip(offset).Take(ChunkSize).ToArray());
            if (TryAddChunk(tmp, part, missing, offset / ChunkSize))
                added += part.Length;
        }

        Debug.Log($"[BuildTcFont] added {added} character(s); "
                  + $"{missing.Length} could not be added"
                  + (missing.Length > 0 ? $": {Trim(missing.ToString())}" : "."));

        // Bake: a static asset needs no source Font at runtime.
        tmp.atlasPopulationMode = AtlasPopulationMode.Static;

        Directory.CreateDirectory(AssetDir);
        AssetDatabase.DeleteAsset(AssetPath);

        AssetDatabase.CreateAsset(tmp, AssetPath);
        foreach (Texture2D atlas in tmp.atlasTextures)
        {
            if (atlas != null && !AssetDatabase.Contains(atlas))
                AssetDatabase.AddObjectToAsset(atlas, tmp);
        }
        if (tmp.material != null && !AssetDatabase.Contains(tmp.material))
            AssetDatabase.AddObjectToAsset(tmp.material, tmp);

        AssetDatabase.SaveAssets();
        AssetDatabase.ImportAsset(AssetPath, ImportAssetOptions.ForceUpdate);

        int atlasCount = tmp.atlasTextures == null ? 0 : tmp.atlasTextures.Length;
        Debug.Log($"[BuildTcFont] wrote {AssetPath} ({atlasCount} atlas texture(s))");

        AssignBundleAndBuild();
    }

    /// <summary>
    /// TMP's shaders live in its "Essential Resources", not in the package
    /// itself, so a fresh project has none and CreateFontAsset dies with
    /// "ArgumentNullException: shader" while building the atlas material.
    /// TMP's own importer calls ImportPackage(path, interactive: true), which
    /// would block a batch build, so import non-interactively instead.
    /// </summary>
    private static void EnsureTmpResources()
    {
        if (Shader.Find("TextMeshPro/Mobile/Distance Field") != null)
        {
            Debug.Log("[BuildTcFont] TMP shaders present");
            return;
        }

        string packageRoot = Path.GetFullPath(
            Path.Combine(Application.dataPath, "..", "Library", "PackageCache"));
        string[] found = Directory.Exists(packageRoot)
            ? Directory.GetFiles(packageRoot, "TMP Essential Resources.unitypackage",
                                 SearchOption.AllDirectories)
            : new string[0];

        if (found.Length == 0)
        {
            Fail("TMP Essential Resources.unitypackage not found under Library/PackageCache");
            return;
        }

        Debug.Log($"[BuildTcFont] importing TMP Essential Resources: {found[0]}");
        AssetDatabase.ImportPackage(found[0], false);
        AssetDatabase.Refresh();

        if (Shader.Find("TextMeshPro/Mobile/Distance Field") == null)
            Fail("TMP shaders still missing after importing Essential Resources");
        else
            Debug.Log("[BuildTcFont] TMP shaders imported");
    }

    private static string Trim(string value) =>
        value.Length <= 120 ? value : value.Substring(0, 120) + "...";

    private static bool TryAddChunk(TMP_FontAsset tmp, string part,
                                    System.Text.StringBuilder missing, int index)
    {
        try
        {
            tmp.TryAddCharacters(part, out string miss);
            if (!string.IsNullOrEmpty(miss))
                missing.Append(miss);
            return true;
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[BuildTcFont] chunk {index} ({part.Length} chars) failed: "
                             + $"{e.GetType().Name}: {e.Message} - retrying individually");

            foreach (char c in part)
            {
                try
                {
                    tmp.TryAddCharacters(c.ToString(), out string miss);
                    if (!string.IsNullOrEmpty(miss))
                        missing.Append(miss);
                }
                catch
                {
                    missing.Append(c);
                }
            }
            return true;
        }
    }

    private static void ImportFont()
    {
        AssetDatabase.ImportAsset(FontPath, ImportAssetOptions.ForceUpdate);

        var importer = AssetImporter.GetAtPath(FontPath) as TrueTypeFontImporter;
        if (importer == null)
        {
            Fail($"{FontPath} is not a TrueType font import");
            return;
        }

        importer.fontTextureCase = FontTextureCase.Dynamic;
        importer.SaveAndReimport();
        Debug.Log("[BuildTcFont] font reimported as Dynamic (Include Font Data)");
    }

    private static void AssignBundleAndBuild()
    {
        string outDir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "out"));
        Directory.CreateDirectory(outDir);

        var bundles = new Dictionary<string, string[]>
        {
            { BundleName, new[] { AssetPath } },
        };

        // The material references TMP's SDF shader, so ship it inside the bundle
        // rather than relying on the game resolving it by GUID.
        var extras = new List<string>();
        foreach (string shaderName in new[]
                 {
                     "TextMeshPro/Distance Field",
                     "TextMeshPro/Mobile/Distance Field",
                     "TextMeshPro/Distance Field (Surface)",
                 })
        {
            Shader shader = Shader.Find(shaderName);
            if (shader == null) continue;
            string path = AssetDatabase.GetAssetPath(shader);
            if (!string.IsNullOrEmpty(path) && path.StartsWith("Assets/"))
                extras.Add(path);
        }
        if (extras.Count > 0)
            bundles[BundleName] = bundles[BundleName].Concat(extras).Distinct().ToArray();

        AssetBundleBuild[] buildMap = bundles
            .Select(kv => new AssetBundleBuild
            {
                assetBundleName = kv.Key,
                assetNames = kv.Value,
            })
            .ToArray();

        BuildPipeline.BuildAssetBundles(
            outDir, buildMap, BuildAssetBundleOptions.None,
            BuildTarget.StandaloneWindows64);

        string produced = Path.Combine(outDir, BundleName);
        if (File.Exists(produced))
            Debug.Log($"[BuildTcFont] bundle -> {produced} ({new FileInfo(produced).Length:N0} bytes)");
        else
            Fail($"bundle not produced at {produced}");
    }

    private static void Fail(string message)
    {
        Debug.LogError($"[BuildTcFont] {message}");
        if (Application.isBatchMode) EditorApplication.Exit(1);
    }
}