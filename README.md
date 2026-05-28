# Crystal Mods

Monorepo of PC game mods, patches, deploy tooling, and (future) the **Crystal Mod
Manager** — a Vortex-like cross-platform mod manager focused on patching, asset
backup, save editing, and cheat injection.

> Status: **early — bottom-up**. The repository starts as a curated collection of
> per-game mods and a shared tooling layer. The mod manager itself is on the
> roadmap and not implemented yet.

## Layout

```
crystal-mods/
├── <normalized-game-name>/        Per-game folder (one per game)
│   ├── metadata.jsonc             Engine / API / store IDs (sourced from PCGW)
│   └── <mod-name>/                One folder per mod
│       ├── README.md
│       ├── deploy.{sh,ps1}        Cross-platform deploy/uninstall scripts
│       └── …mod source files…
├── tools/                         Shared, language-organised tooling
│   ├── python/                    uv-managed Python packages (Ruff)
│   └── node/                      pnpm-workspace TypeScript packages (Biome)
├── docs/                          Authoring guides + modding research
│   └── modding/                   Vortex / Nexus / Unity / UE / BepInEx notes
├── .github/
└── .copilot_workspace/            Agent scratch (gitignored)
```

### Platform targets

- **Primary**: Windows 11 — `.bat` / `.ps1` scripts, Vortex deploy support.
- **Dev**: WSL2 with `bash` deploy parity.
- **Secondary**: Linux / Proton where the game supports it.

### Storefront targets

- **Primary**: Steam (App ID auto-detect).
- **Optional**: GOG, Epic, Ubisoft Connect — per mod.

## Toolchains

| Stack | Manager | Version | Lint / Format |
| --- | --- | --- | --- |
| Python | [uv](https://docs.astral.sh/uv/) | `>=3.11` | [Ruff](https://docs.astral.sh/ruff/) |
| Node   | [Volta](https://volta.sh/) | `24.x` | — |
| TypeScript | [pnpm](https://pnpm.io/) workspace | `pnpm 10.x` | [Biome](https://biomejs.dev/) |

Bootstrap:

```bash
# Python (uv installs the toolchain + creates .venv per package)
uv sync

# Node (Volta auto-pins node 24 + pnpm 10 via package.json `volta`)
pnpm install
```

## Currently shipped mods

| Game | Mod | Status |
| --- | --- | --- |
| [Dawn of War – Definitive Edition](dawn-of-war-de/) | [Unofficial TC Patch](dawn-of-war-de/unofficial-tc-patch/) | Released |

## Conventions

See [docs/conventions.md](docs/conventions.md) for naming rules, the
`metadata.jsonc` schema, and per-mod layout.

## License

Per-mod licenses live next to each mod. Tools and docs default to **MIT**.
