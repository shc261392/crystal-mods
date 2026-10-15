using HarmonyLib;
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

        // ---- 2. TMP_Text.font = ... ----------------------------------------
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