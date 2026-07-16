# Copilot instructions — Crystal Mods

The canonical agent rules live in [`AGENTS.md`](../AGENTS.md) at the repo root.
This file mirrors them for GitHub Copilot's auto-loading convention. **Read
`AGENTS.md` first.**

## TL;DR for any task

1. Temp files and scratch work MUST go in `./.copilot_workspace/`.
   `/tmp` is forbidden.
2. After finishing a task, ask the user for review via `vscode_askQuestions`.
3. If confidence < 90% on anything (path, flag, identifier), stop and verify.
4. Confirm before irreversible actions (force-push, public-flip, delete backups).
5. Mods live at `<game>/<mod>/`; game metadata at `<game>/metadata.jsonc`
   (PCGW-sourced via `tools/python/pcgw-fetch/`).
6. Windows 11 is primary, WSL2 is dev, Linux/Proton secondary — ship both
   `.ps1` and `.sh` deploy scripts.
7. **Locale preservation (DoW DE TC mod)**: For `dawn-of-war-de/unofficial-tc-patch/`,
   only access paths within this project directory and `Engine/Locale/Chinese/`
   in the game installation. **`Engine/Locale/English/` is forbidden.** The game
   ships with Chinese locale; all deployments must preserve this. For other
   projects, apply locale preservation rules as appropriate to that game.
8. **UI changes require browser verification**: Changes to pages/components/layouts
   MUST be verified visually using browser tools, screenshot shown to user for
   approval, then include `[verified]` in commit message. Human approval required.

## Progressive disclosure index

- Conventions / schema → [`docs/conventions.md`](../docs/conventions.md)
- Vortex → [`docs/modding/vortex.md`](../docs/modding/vortex.md)
- Nexus → [`docs/modding/nexus.md`](../docs/modding/nexus.md)
- Unity / BepInEx → [`docs/modding/unity-bepinex.md`](../docs/modding/unity-bepinex.md)
- Unreal → [`docs/modding/unreal.md`](../docs/modding/unreal.md)
- Roadmap → [`docs/roadmap/crystal-mod-manager.md`](../docs/roadmap/crystal-mod-manager.md)

For the Intent-First Agentic Workflow, see `.intent-first/rules.md`.
