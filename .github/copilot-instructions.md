# Copilot instructions — Crystal Mods

The canonical agent rules live in [`AGENTS.md`](../AGENTS.md) at the repo root.
This file mirrors them for GitHub Copilot's auto-loading convention. **Read
`AGENTS.md` first.**

## TL;DR for any task

1. Temp files → `./.copilot_workspace/` (never `/tmp`).
2. After finishing a task, ask the user for review via `vscode_askQuestions`.
3. If confidence < 90% on anything (path, flag, identifier), stop and verify.
4. Confirm before irreversible actions (force-push, public-flip, delete backups).
5. Mods live at `<game>/<mod>/`; game metadata at `<game>/metadata.jsonc`
   (PCGW-sourced via `tools/python/pcgw-fetch/`).
6. Windows 11 is primary, WSL2 is dev, Linux/Proton secondary — ship both
   `.ps1` and `.sh` deploy scripts.

## Progressive disclosure index

- Conventions / schema → [`docs/conventions.md`](../docs/conventions.md)
- Vortex → [`docs/modding/vortex.md`](../docs/modding/vortex.md)
- Nexus → [`docs/modding/nexus.md`](../docs/modding/nexus.md)
- Unity / BepInEx → [`docs/modding/unity-bepinex.md`](../docs/modding/unity-bepinex.md)
- Unreal → [`docs/modding/unreal.md`](../docs/modding/unreal.md)
- Roadmap → [`docs/roadmap/crystal-mod-manager.md`](../docs/roadmap/crystal-mod-manager.md)
