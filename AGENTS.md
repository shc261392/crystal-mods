# Agent operating manual — Crystal Mods

These rules apply to every AI coding agent (GitHub Copilot, Claude, etc.)
operating in this repository. They are short on purpose; deeper context is
linked under "Progressive disclosure" below.

## Hard rules

1. **Scratch space**: use `./.copilot_workspace/` for any temporary content
   (downloads, intermediate extracts, generated artifacts you're inspecting).
   **Never use `/tmp`.** The directory is gitignored and safe to write to.
2. **Iterate with the user**: after completing any non-trivial task, call the
   `vscode_askQuestions` tool to request review / approval, or to clarify the
   next step. Do not assume "continue".
3. **No silent guessing**: if your confidence in a fact (file path, API shape,
   command flag, game identifier, mod compatibility) is **below 90%**, stop and
   verify — read the source, fetch the doc, or ask the user.
4. **Reversibility first**: prefer non-destructive operations. For anything
   irreversible (force push, public repo flip, deleting backups, dropping
   `.sga`/`.pak` originals) confirm with the user.
5. **Respect platform priorities**: Windows 11 is primary, WSL2 is the dev
   environment, Linux/Proton is secondary. Every deploy script must ship a
   `.ps1` and a `.sh` variant.
6. **Locale preservation (DoW DE TC mod)**: For `dawn-of-war-de/unofficial-tc-patch/`,
   only access paths within this project directory and `Engine/Locale/Chinese/`
   in the game installation. **`Engine/Locale/English/` is forbidden.** The game
   ships with Chinese locale; all deployments must preserve this. For other
   projects, apply locale preservation rules as appropriate to that game.
7. **CRITICAL: Credential safety**: **NEVER read `.env` files or credentials
   into agent context.** Access secrets only via scripts/environment variables.
   If a task requires credentials, instruct the user to run the script directly
   or pass values via environment variables. Reading credentials into LLM context
   risks exposure through conversation logs, debug output, or model training.
8. **CRITICAL: Unrecoverable actions require dual verification**:
   - **Research FIRST**: before running ANY tool that modifies git history,
     deletes files, or performs system-wide changes, research the tool's behavior
     thoroughly (read docs, check man pages, verify examples).
   - **Test on dummy files**: create a test directory with sample files and run
     the command with a dry-run flag or on test data first.
   - **Human approval AFTER showing consequences**: present the test results,
     explain exactly what will happen (including side effects like local file
     deletion), and get explicit user approval before proceeding.
   - **Examples requiring this process**: `git-filter-repo`, `git push --force`,
     `rm -rf`, database migrations, production deployments, batch file operations.
9. **CRITICAL: UI verification mandate**: For any change to `src/pages/`,
   `src/components/`, `src/layouts/`, or stylesheets:
   - **MUST use browser tools** (`open_browser_page`, `screenshot_page`) to verify
     changes visually before claiming completion
   - **MUST take screenshot** showing the working feature as proof
   - **MUST include verification evidence** in commit message: `[verified]`,
     `screenshot:`, `tested in browser:`, `dev server:`, or `visual test:`
   - **Claiming "done" without browser verification is a critical error**
   - The commit-msg hook enforces this - commits without evidence will be blocked

## Repository contract

- Mods live at `<normalized-game-name>/<mod-name>/`. Game names are
  lowercase-hyphenated, abbreviated where standard (`dawn-of-war-de`).
- Game-level metadata (engine, graphics API, store IDs) lives in
  `<game>/metadata.jsonc`. Source of truth: PCGamingWiki — fetch with
  `tools/python/pcgw-fetch/`.
- Shared Python tools: `tools/python/<pkg>/` (uv workspace member, Ruff-linted).
- Shared Node/TS tools: `tools/node/<pkg>/` (pnpm workspace member, Biome).

## Progressive disclosure

Read these only when relevant to your current task:

- General conventions and `metadata.jsonc` schema → [docs/conventions.md](docs/conventions.md)
- PCGW fetcher tool and rate-limit etiquette → [tools/python/pcgw-fetch/README.md](tools/python/pcgw-fetch/README.md)
- Vortex extension authoring → [docs/modding/vortex.md](docs/modding/vortex.md)
- Nexus Mods publishing → [docs/modding/nexus.md](docs/modding/nexus.md)
- Unity / BepInEx modding → [docs/modding/unity-bepinex.md](docs/modding/unity-bepinex.md)
- Unreal Engine modding → [docs/modding/unreal.md](docs/modding/unreal.md)
- Roadmap: Crystal Mod Manager → [docs/roadmap/crystal-mod-manager.md](docs/roadmap/crystal-mod-manager.md)
- Per-game deploy patterns → each mod's own `README.md` and `deploy.{sh,ps1}`
