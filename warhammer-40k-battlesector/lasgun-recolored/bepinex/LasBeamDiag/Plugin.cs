using System;
using System.Collections.Generic;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using WeaponEffects;

namespace LasBeamDiag
{
    // BepInEx 6 (IL2CPP) diagnostic. Does NOT change visuals. Each frame it scans
    // all loaded ProjectileEffect instances and logs one line the first time each
    // becomes active (i.e. fires), with its name + start (transform.position) and
    // end (FinalPosition) — the exact data a red-beam plugin would draw between.
    // It also logs a one-time inventory of every distinct projectile-effect name
    // it ever sees (active or pooled) so we can confirm the lasgun effect loads.
    //
    // Grep BepInEx/LogOutput.log for:
    //   [LASBEAM-INV] name='..'                       (distinct effect prefabs present)
    //   [LASBEAM] FIRED name='..' start=(..) end=(..) traj=N lasgun=T/F
    [BepInPlugin(GUID, "Lasgun Beam Diagnostic", "0.1.0")]
    public class Plugin : BasePlugin
    {
        public const string GUID = "com.crystalmods.lasbeamdiag";
        internal static new ManualLogSource Log;

        public override void Load()
        {
            Log = base.Log;
            Log.LogInfo("LasBeamDiag 0.1 loaded. Logging ProjectileEffect fires. Grep '[LASBEAM]'.");
            ClassInjector.RegisterTypeInIl2Cpp<DiagBehaviour>();
            AddComponent<DiagBehaviour>();
        }
    }

    public class DiagBehaviour : MonoBehaviour
    {
        public DiagBehaviour(IntPtr ptr) : base(ptr) { }

        // instances currently counted as active (so each new activation logs once)
        private readonly HashSet<int> _active = new HashSet<int>();
        private readonly HashSet<string> _names = new HashSet<string>();
        private float _hbTimer;
        private int _fires;

        private void Update()
        {
            _hbTimer += Time.deltaTime;
            bool heartbeat = _hbTimer >= 30f;
            if (heartbeat) { _hbTimer = 0f; Plugin.Log.LogInfo("[LASBEAM-HB] fires so far: " + _fires + " distinctNames=" + _names.Count); }

            Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppArrayBase<ProjectileEffect> all;
            try { all = Resources.FindObjectsOfTypeAll<ProjectileEffect>(); }
            catch (Exception e) { if (heartbeat) Plugin.Log.LogError("scan failed: " + e.Message); return; }
            if (all == null) return;

            for (int i = 0; i < all.Count; i++)
            {
                ProjectileEffect p = all[i];
                if (p == null) continue;

                string name;
                try { name = p.gameObject.name; } catch { continue; }

                // one-time inventory of every distinct effect name we ever see
                if (_names.Add(name))
                    Plugin.Log.LogInfo("[LASBEAM-INV] name='" + name + "'");

                bool active;
                try { active = p.isActiveAndEnabled && p.gameObject.activeInHierarchy; } catch { continue; }

                int id;
                try { id = p.GetInstanceID(); } catch { continue; }

                if (!active) { _active.Remove(id); continue; }
                if (!_active.Add(id)) continue; // already logged this activation

                Vector3 start, end; int traj = -1;
                try { start = p.transform.position; } catch { start = Vector3.zero; }
                try { end = p.FinalPosition; } catch { end = Vector3.zero; }
                try { traj = (int)p.TrajectoryType; } catch { }

                bool lasgun = name.IndexOf("LasGun", StringComparison.OrdinalIgnoreCase) >= 0
                              || name.IndexOf("Lasgun", StringComparison.OrdinalIgnoreCase) >= 0;
                _fires++;
                Plugin.Log.LogInfo(
                    "[LASBEAM] FIRED name='" + name + "' start=" + Fmt(start) + " end=" + Fmt(end) +
                    " traj=" + traj + " lasgun=" + lasgun);
            }
        }

        private static string Fmt(Vector3 v)
        {
            return "(" + v.x.ToString("F2") + "," + v.y.ToString("F2") + "," + v.z.ToString("F2") + ")";
        }
    }
}
