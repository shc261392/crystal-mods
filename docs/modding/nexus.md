# Nexus Mods publishing (stub)

> Status: **stub**.

## References

- Nexus Mods help — <https://help.nexusmods.com/>
- Mod page best practices — <https://help.nexusmods.com/article/82-mod-page-guidelines>
- Nexus API (v1) — <https://app.swaggerhub.com/apis-docs/NexusMods/nexus-mods_public_api_params_in_form_data/1.0>
- Vortex publishing integration — <https://github.com/Nexus-Mods/Vortex/wiki>

## Publishing checklist

1. Archive naming: `<mod-id>-v<semver>.zip`, plus
   `vortex-ext-<game-id>-v<semver>.zip` if shipping an extension.
2. Mod page sections: Description, Requirements, Installation (Vortex /
   Manual / Script), Uninstall, Changelog, Credits.
3. Pair every mod release with a GitHub Release of the same version. The
   repo URL goes in the Source tab on Nexus.
4. Add the Nexus mod ID + URL to the mod's `modinfo.json`.

## TODO

- Document API key handling for automated uploads (CI).
- Document `nxm://` link handling for one-click install via Vortex.
- Endorsement / version / changelog API endpoints.
