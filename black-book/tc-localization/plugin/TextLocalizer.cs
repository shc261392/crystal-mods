using System.Collections.Generic;
using System.Text;
using BepInEx.Logging;
using PixelCrushers;
using PixelCrushers.DialogueSystem;
using UnityEngine;

namespace BlackBookTcFont
{
    /// <summary>
    /// Converts the game's Simplified Chinese localisation to Traditional,
    /// in memory, using the game's own Dialogue System data structures.
    ///
    /// All of the game's text lives in two ScriptableObjects:
    ///   * DialogueDatabase "BlackBook"   - 14,032 dialogue entries + actors/items/quests
    ///   * TextTable        "UILocalization" - the UI labels
    ///
    /// They cannot be patched on disk: both are MonoBehaviours whose type trees
    /// were stripped from the player build, so UnityPy cannot rewrite them.
    /// But every field is public, so we can convert them at runtime.
    ///
    /// IMPORTANT: the database is genuinely multi-language (it also holds
    /// Japanese and Korean). Only fields tagged with the Chinese language code
    /// are touched, so kana and hangul are never converted.
    /// </summary>
    internal static class TextLocalizer
    {
        /// <summary>Dialogue System stores localised values as "&lt;Field&gt; &lt;lang&gt;".</summary>
        private const string LanguageCode = "zh";

        public static int ConvertAll(ScTcConverter converter, ManualLogSource log)
        {
            if (converter.IsEmpty)
            {
                log.LogError("Conversion tables are empty; no text was converted.");
                return 0;
            }

            int dialogue = ConvertDialogueDatabases(converter, log);
            int tables = ConvertTextTables(converter, log);
            return dialogue + tables;
        }

        // ------------------------------------------------------------------ //
        // DialogueDatabase
        // ------------------------------------------------------------------ //

        /// <summary>
        /// Convert one database. Called before the game registers it, because
        /// DialogueLua snapshots every asset field into its Lua tables at that
        /// point (DialogueLua.AddToTable) and the speaker-name UI reads the name
        /// from that snapshot rather than from the live Field. Converting after
        /// registration leaves the cached copy Simplified - which is exactly why
        /// "Old Egor" kept showing as 老叶戈尔.
        /// </summary>
        public static int ConvertDatabase(DialogueDatabase db, ScTcConverter converter)
        {
            if (db == null) return 0;

            int count = 0;
            count += ConvertAssets(db.actors, converter);
            count += ConvertAssets(db.items, converter);
            count += ConvertAssets(db.locations, converter);
            count += ConvertAssets(db.variables, converter);

            foreach (Conversation conversation in db.conversations)
            {
                if (conversation == null) continue;
                count += ConvertFields(conversation.fields, converter);
                foreach (DialogueEntry entry in conversation.dialogueEntries)
                {
                    if (entry == null) continue;
                    count += ConvertFields(entry.fields, converter);
                }
            }
            return count;
        }

        private static int ConvertDialogueDatabases(ScTcConverter converter, ManualLogSource log)
        {
            DialogueDatabase[] databases;
            try
            {
                databases = Resources.FindObjectsOfTypeAll<DialogueDatabase>();
            }
            catch (System.Exception e)
            {
                log.LogWarning($"Could not enumerate DialogueDatabase objects: {e.Message}");
                return 0;
            }

            if (databases == null || databases.Length == 0)
            {
                log.LogWarning("No DialogueDatabase found yet.");
                return 0;
            }

            int count = 0;
            foreach (DialogueDatabase db in databases)
            {
                if (db == null) continue;

                count += ConvertDatabase(db, converter);
            }

            log.LogInfo($"DialogueDatabase: converted {count} field(s) across {databases.Length} database(s).");
            return count;
        }

        private static int ConvertAssets<T>(List<T> assets, ScTcConverter converter) where T : Asset
        {
            int count = 0;
            if (assets == null) return 0;
            foreach (T asset in assets)
            {
                if (asset == null) continue;
                count += ConvertFields(asset.fields, converter);
            }
            return count;
        }

        private static int ConvertFields(List<Field> fields, ScTcConverter converter)
        {
            if (fields == null) return 0;

            int count = 0;
            foreach (Field field in fields)
            {
                if (field == null || string.IsNullOrEmpty(field.value)) continue;
                if (!IsChineseField(field.title)) continue;

                string converted = converter.Convert(field.value);
                if (!ReferenceEquals(converted, field.value))
                {
                    field.value = converted;
                    count++;
                }
            }
            return count;
        }

        /// <summary>
        /// True for localised Chinese fields: "Menu Text zh", "Name zh", or a
        /// bare "zh". Titles without a language suffix (the default language)
        /// are left alone.
        /// </summary>
        private static bool IsChineseField(string title)
        {
            if (string.IsNullOrEmpty(title)) return false;

            string trimmed = title.TrimEnd();
            if (trimmed.Equals(LanguageCode, System.StringComparison.OrdinalIgnoreCase))
                return true;

            return trimmed.EndsWith(" " + LanguageCode, System.StringComparison.OrdinalIgnoreCase);
        }

        // ------------------------------------------------------------------ //
        // TextTable (UI labels)
        // ------------------------------------------------------------------ //

        private static int ConvertTextTables(ScTcConverter converter, ManualLogSource log)
        {
            TextTable[] tables;
            try
            {
                tables = Resources.FindObjectsOfTypeAll<TextTable>();
            }
            catch (System.Exception e)
            {
                log.LogWarning($"Could not enumerate TextTable objects: {e.Message}");
                return 0;
            }

            if (tables == null || tables.Length == 0)
            {
                log.LogWarning("No TextTable found yet.");
                return 0;
            }

            int count = 0;
            foreach (TextTable table in tables)
            {
                if (table == null) continue;

                int languageId = ResolveChineseLanguageId(table, log);
                if (languageId < 0)
                {
                    log.LogWarning("TextTable has no Chinese column; skipped.");
                    continue;
                }

                foreach (KeyValuePair<int, TextTableField> entry in table.fields)
                {
                    TextTableField field = entry.Value;
                    if (field == null || field.texts == null) continue;
                    if (!field.texts.TryGetValue(languageId, out string value)) continue;
                    if (string.IsNullOrEmpty(value)) continue;

                    string converted = converter.Convert(value);
                    if (!ReferenceEquals(converted, value))
                    {
                        field.texts[languageId] = converted;
                        count++;
                    }
                }
            }

            log.LogInfo($"TextTable: converted {count} label(s) across {tables.Length} table(s).");
            return count;
        }

        /// <summary>Find the column id for Chinese, logging the available languages.</summary>
        private static int ResolveChineseLanguageId(TextTable table, ManualLogSource log)
        {
            if (table.languages == null) return -1;

            StringBuilder names = new StringBuilder();
            foreach (KeyValuePair<string, int> pair in table.languages)
            {
                if (names.Length > 0) names.Append(", ");
                names.Append(pair.Key).Append('=').Append(pair.Value);
            }
            log.LogInfo($"TextTable languages: {names}");

            // Exact "Chinese", then anything starting with it (ChineseSimplified etc.).
            foreach (KeyValuePair<string, int> pair in table.languages)
            {
                if (pair.Key.Equals("Chinese", System.StringComparison.OrdinalIgnoreCase))
                    return pair.Value;
            }
            foreach (KeyValuePair<string, int> pair in table.languages)
            {
                if (pair.Key.StartsWith("Chinese", System.StringComparison.OrdinalIgnoreCase)
                    || pair.Key.Equals(LanguageCode, System.StringComparison.OrdinalIgnoreCase))
                    return pair.Value;
            }
            return -1;
        }
    }
}