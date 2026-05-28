# game-discover

Read-only inspector that reports an installed PC game's engine, scripting
backend, asset layout, and likely mod entry points. Used to draft a `PLAN.md`
per mod target.

```bash
uv run game-discover "/mnt/d/SteamLibrary/steamapps/common/Suzerain" \
  --out suzerain/DISCOVERY.md --json suzerain/DISCOVERY.json
```

Supports Unity (Mono / IL2CPP) and Unreal. Files in the game install are
never modified.
