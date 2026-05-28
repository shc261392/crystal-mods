# Roadmap — Crystal Mod Manager

> Status: **not started**. This doc captures intent so we can grow the repo
> structure with the eventual manager in mind.

## Goal

A cross-platform, Vortex-class mod manager focused on:

- **Mod install / deploy** — read mods from this monorepo (or external
  archives), resolve install paths from `<game>/metadata.jsonc` + per-mod
  `modinfo.json`.
- **Patch / backup / restore** — every mutation goes through a backup
  manifest; uninstall always restores.
- **Save editing & cheats** — per-game adapters for save formats and runtime
  cheat injection.
- **Vortex compatibility** — read Vortex extensions where they exist; export
  mods to Vortex-compatible archives.

## Tentative layout (when work starts)

```
tools/node/crystal-mod-manager/
├── apps/
│   ├── desktop/        Tauri or Electron shell
│   └── cli/            Node CLI front-end
├── packages/
│   ├── core/           Mod resolution, manifest schema, deploy engine
│   ├── adapters/       Per-game adapters (DoW, Skyrim, Unity/BepInEx, UE)
│   └── vortex-bridge/  Import/export Vortex extensions
```

The current monorepo is intentionally structured so this can land later
without churn:

- `<game>/metadata.jsonc` is the manager's primary game registry.
- `<game>/<mod>/modinfo.json` is the manager's primary mod registry.
- `deploy.{sh,ps1}` are the fallback when no first-class adapter exists.

## Non-goals (for now)

- Nexus account integration / one-click install — defer until v0.2.
- Plugin marketplace.
- Mobile / console.
