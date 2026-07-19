# Copilot instructions — Crystal Mods

The canonical agent rules live in [`AGENTS.md`](../AGENTS.md) at the repo root.
This file mirrors them for GitHub Copilot's auto-loading convention. **Read
`AGENTS.md` first.**

## TL;DR for any task

1. **Scratch space rules**:
   - Temp files and scratch work MUST go in `./.copilot_workspace/`
   - `/tmp` is forbidden
   - **Distribution packages MUST use the project's `dist/` folder**, not temp folders
2. After finishing a task, ask the user for review via `vscode_askQuestions`.
3. If confidence < 90% on anything (path, flag, identifier), stop and verify.
4. **Validate before implementing**: during debugging/investigation, gather data
   and validate hypotheses BEFORE implementing fixes. If you find yourself
   creating automated fix scripts during root cause analysis, STOP and ask the
   user. Debugging requires patience; "done" must mean "correct," not just "fast."
5. **Data modifications require approval**: NEVER modify game data files
   (Engine.ucs, .sga, fonts, save files, configs) without explicit user approval,
   especially during debugging. Always maintain backups, document changes, and
   test manually before automating.
6. Confirm before irreversible actions (force-push, public-flip, delete backups).
7. Mods live at `<game>/<mod>/`; game metadata at `<game>/metadata.jsonc`
   (PCGW-sourced via `tools/python/pcgw-fetch/`).
8. Windows 11 is primary, WSL2 is dev, Linux/Proton secondary — ship both
   `.ps1` and `.sh` deploy scripts.
9. **Locale preservation (DoW DE TC mod)**: For `dawn-of-war-de/unofficial-tc-patch/`,
   only access paths within this project directory and `Engine/Locale/Chinese/`
   in the game installation. **`Engine/Locale/English/` is forbidden.** The game
   ships with Chinese locale; all deployments must preserve this. For other
   projects, apply locale preservation rules as appropriate to that game.
10. **DOWDE deployment is FORBIDDEN**: For ALL `dawn-of-war-de/` projects, agent
   deployment to game folder is **FORBIDDEN**. Only build the Vortex-installable
   ZIP deliverable in `dist/`. User handles deployment manually. **NEVER ask for
   deployment approval or offer to deploy.**
11. **CRITICAL: Engine.ucs contains mixed content**: `Engine.ucs` has BOTH Chinese
   localization AND English game mode keys (e.g., "Dark Crusade", "Soulstorm").
   **English keys are internal identifiers - translating them BREAKS THE GAME.**
   **NEVER edit Engine.ucs without explicit user approval.** See
   `dawn-of-war-de/unofficial-tc-patch/docs/ENGINE_UCS_STRUCTURE.md` for details.
12. **UI changes require browser verification**: Changes to pages/components/layouts
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
