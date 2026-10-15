using HarmonyLib;
using PixelCrushers.DialogueSystem;
using TMPro;

namespace BlackBookTcFont
{
    /// <summary>
    /// Forces our Traditional font onto every text element, however it gets its
    /// font.
    ///
    /// Two mechanisms are needed, because no single hook covers all cases:
    ///
    /// 1. TextFontChanger calls Singleton&lt;FontService&gt;.Instance.GetFont(type),
    ///    so patching FontService covers that path (TextFontChanger is used by
    ///    only a handful of elements - the log showed "switched 1 text element").
    ///
    /// 2. Everything else carries its font as a *serialized* value on the TMP
    ///    component, which never calls GetFont and never goes through a property
    ///    setter, so no hook can see it. Those are handled by the periodic sweep
    ///    in TcFontPlugin, plus the set_font prefix below for runtime changes.
    /// </summary>
    [HarmonyPatch]
    internal static class FontPatches
    {
        // ---- 1. FontService ------------------------------------------------

        [HarmonyPostfix]
        [HarmonyPatch(typeof(FontService), "GetFont", new[] { typeof(FontType) })]
        private static void GetFontByType(ref TMP_FontAsset __result) => Replace(ref __result);

        [HarmonyPostfix]
        [HarmonyPatch(typeof(FontService), "GetFont", new[] { typeof(FontName) })]
        private static void GetFontByName(ref TMP_FontAsset __result) => Replace(ref __result);

        private static void Replace(ref TMP_FontAsset result)
        {
            TMP_FontAsset tc = TcFontPlugin.TcFont;
            if (tc == null || result == null || result == tc) return;

            TcFontPlugin.KeepReachable(result);
            result = tc;
        }

        // ---- 2. DatabaseManager.Add ----------------------------------------
        //
        // DialogueLua snapshots every asset field into its Lua tables when a
        // database is registered (DialogueLua.AddToTable), and the speaker-name
        // UI reads the name from that snapshot, not from the live Field. So we
        // must convert the database BEFORE registration, or the cached copy
        // stays Simplified - the cause of "Old Egor" showing as 老叶戈尔.
        //
        // Re-initialising the tables afterwards would fix it too but resets
        // conversation sim-status, so converting first is both safer and
        // simpler.
        [HarmonyPrefix]
        [HarmonyPatch(typeof(DatabaseManager), "Add", new[] { typeof(DialogueDatabase) })]
        private static void DatabaseAddPrefix(DialogueDatabase database)
        {
            ScTcConverter converter = TcFontPlugin.Converter;
            if (converter == null || database == null || converter.IsEmpty) return;

            int converted = TextLocalizer.ConvertDatabase(database, converter);
            if (converted > 0)
                TcFontPlugin.Log.LogInfo($"[DatabaseManager.Add] converted {converted} "
                                         + "localised field(s) before the game cached them.");
        }

        // ---- 3. TMP_Text.font = ... ----------------------------------------
        //
        // A prefix rather than a postfix: a postfix on a setter would have to
        // assign the property again and recurse forever.
        [HarmonyPrefix]
        [HarmonyPatch(typeof(TMP_Text), "set_font")]
        private static void SetFontPrefix(ref TMP_FontAsset value)
        {
            TMP_FontAsset tc = TcFontPlugin.TcFont;
            if (tc == null || value == null || value == tc) return;

            TcFontPlugin.KeepReachable(value);
            value = tc;
        }
    }
}